"""Ollama HTTP Proxy - Transparent memory capture for all Ollama interfaces.

v3.0: Added session lifecycle management with auto-commit.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
import uvicorn

from memora.core.engine import CoreEngine
from memora.core.ingestion import extract_memories


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("memora.proxy")


class OllamaProxy:
    """HTTP proxy for capturing Ollama conversations with session management."""

    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        proxy_port: int = 11435,
        memory_path: str = "./memora_data",
        verbose: bool = True,
    ):
        self.ollama_host = ollama_host
        self.proxy_port = proxy_port
        self.verbose = verbose

        self.engine = CoreEngine()
        store_path = Path(memory_path)
        if (store_path / ".memora").exists():
            self.engine.open_store(store_path)
        else:
            self.engine.init_store(store_path)

        self.app = FastAPI(title="Memora Ollama Proxy")
        self.setup_routes()
        self.client = httpx.AsyncClient(timeout=300.0)

        # Session timeout is a safety net, not the primary signal.
        # Primary signal is connection close (client disconnects).
        # Default 15 minutes — users pause mid-conversation.
        self._session_timeout_minutes = 15

    def setup_routes(self):
        @self.app.api_route(
            "/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"]
        )
        async def proxy_all(request: Request, path: str):
            return await self.handle_request(request, path)

    async def handle_request(self, request: Request, path: str):
        url = f"{self.ollama_host}/{path}"
        body = await request.body()
        is_chat_endpoint = path in ["api/chat", "api/generate"]

        request_data = None
        if is_chat_endpoint and body:
            try:
                request_data = json.loads(body)
            except json.JSONDecodeError:
                pass

        if is_chat_endpoint and request_data:
            self._ensure_session_open(request_data)
            # Check timeout before processing — if the session timed out,
            # close it and the next _ensure_session_open call will open a new one
            await self._check_session_timeout()

        try:
            is_streaming = False
            if request_data:
                is_streaming = request_data.get("stream", False)

            if is_streaming:
                return await self.handle_streaming_request(url, request, body, request_data)
            else:
                response = await self.client.request(
                    method=request.method,
                    url=url,
                    content=body,
                    headers=dict(request.headers),
                )

                if is_chat_endpoint and response.status_code == 200:
                    await self.capture_memories(request_data, response.content)
                    # Touch session on successful response too
                    active = self.engine.get_active_session()
                    if active:
                        self.engine._session_manager.touch_session(active.id)

                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )

        except Exception as e:
            logger.error(f"Proxy error: {e}")
            return Response(
                content=json.dumps({"error": str(e)}),
                status_code=500,
                media_type="application/json",
            )

    async def handle_streaming_request(
        self, url: str, request: Request, body: bytes, request_data: dict
    ):
        full_response = []

        async def stream_generator():
            async with self.client.stream(
                method=request.method,
                url=url,
                content=body,
                headers=dict(request.headers),
            ) as response:
                async for chunk in response.aiter_bytes():
                    full_response.append(chunk)
                    yield chunk

            combined_response = b"".join(full_response)
            await self.capture_memories(request_data, combined_response)
            self._last_request_time = datetime.now(timezone.utc)

        return StreamingResponse(stream_generator(), media_type="application/json")

    def _ensure_session_open(self, request_data: dict):
        """Open a session if none is active. Touch existing session to reset timeout."""
        active = self.engine.get_active_session()
        if active is None:
            branch = self.engine.get_current_branch() or "main"
            model = request_data.get("model", "")
            self.engine._session_manager.open_session(branch, ollama_model=model)
            logger.info("Opened new session")
        else:
            # Reset the timeout on every request — the session stays alive
            # as long as the user keeps chatting. Timeout only fires
            # when the user stops chatting for 15+ minutes.
            self.engine._session_manager.touch_session(active.id)

    async def _check_session_timeout(self):
        """Check if the active session has timed out from inactivity."""
        if self.engine._session_manager is None:
            return
        timed_out_id = self.engine._session_manager.check_timeout()
        if timed_out_id:
            logger.info(
                f"Session {timed_out_id} timed out after {self._session_timeout_minutes}min"
            )
            self.engine.auto_commit_session(timed_out_id)

    async def capture_memories(self, request_data: Optional[dict], response_content: bytes):
        """Capture memories from request and response."""
        if not request_data:
            return

        try:
            user_message = None
            if "messages" in request_data:
                messages = request_data["messages"]
                if messages and isinstance(messages, list):
                    for msg in reversed(messages):
                        if msg.get("role") == "user":
                            user_message = msg.get("content")
                            break
            elif "prompt" in request_data:
                user_message = request_data["prompt"]

            ai_response = None
            try:
                response_lines = response_content.decode("utf-8").strip().split("\n")
                for line in response_lines:
                    if line.strip():
                        response_json = json.loads(line)
                        if "message" in response_json:
                            content = response_json["message"].get("content", "")
                            if content:
                                ai_response = (ai_response or "") + content
                        elif "response" in response_json:
                            content = response_json.get("response", "")
                            if content:
                                ai_response = (ai_response or "") + content
            except Exception as e:
                logger.debug(f"Error parsing response: {e}")

            session = self.engine.get_active_session()
            session_id = session.id if session else ""
            branch = session.branch if session else "main"

            if user_message:
                memories, ner_entities, _ = extract_memories(
                    user_message,
                    source=f"ollama_chat",
                    session_id=session_id,
                    branch=branch,
                    raw_turn=user_message,
                )
                store_path, store = self.engine._ensure()
                for memory in memories:
                    store.write(memory)
                    if self.engine._session_manager:
                        self.engine._session_manager.add_memory_to_session(session_id, memory.id)
                    if self.engine._index_manager:
                        self.engine._index_manager.add_memory(
                            memory.id,
                            memory.content,
                            memory.memory_type.value,
                            memory.session_id,
                            memory.created_at,
                        )
                    if self.engine._graph and ner_entities:
                        self.engine._graph.update_from_ner(ner_entities)

                if memories and self.verbose:
                    logger.info(f"Captured {len(memories)} memories from user")

            if ai_response:
                memories, ner_entities, _ = extract_memories(
                    ai_response,
                    source=f"ollama_chat",
                    session_id=session_id,
                    branch=branch,
                    raw_turn=ai_response,
                )
                store_path, store = self.engine._ensure()
                for memory in memories:
                    store.write(memory)
                    if self.engine._session_manager:
                        self.engine._session_manager.add_memory_to_session(session_id, memory.id)
                    if self.engine._index_manager:
                        self.engine._index_manager.add_memory(
                            memory.id,
                            memory.content,
                            memory.memory_type.value,
                            memory.session_id,
                            memory.created_at,
                        )
                    if self.engine._graph and ner_entities:
                        self.engine._graph.update_from_ner(ner_entities)

                if memories and self.verbose:
                    logger.info(f"Captured {len(memories)} memories from AI")

        except Exception as e:
            logger.error(f"Error capturing memories: {e}")

    def run(self):
        logger.info(f"Memora Proxy starting on port {self.proxy_port}")
        logger.info(f"   Forwarding to: {self.ollama_host}")
        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=self.proxy_port,
            log_level="warning",
        )


def start_proxy(
    ollama_host: str = "http://localhost:11434",
    proxy_port: int = 11435,
    memory_path: str = "./memora_data",
    verbose: bool = True,
):
    proxy = OllamaProxy(
        ollama_host=ollama_host, proxy_port=proxy_port, memory_path=memory_path, verbose=verbose
    )
    proxy.run()


if __name__ == "__main__":
    start_proxy()
