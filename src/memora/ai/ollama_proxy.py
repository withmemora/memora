"""Ollama HTTP Proxy - Transparent memory capture for all Ollama interfaces.

This proxy sits between any Ollama client (GUI, CLI, web) and the Ollama service,
automatically capturing memories from all conversations without changing user workflow.
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

from memora.interface.api import MemoraStore
from memora.core.ingestion import extract_facts


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("memora.proxy")


class OllamaProxy:
    """HTTP proxy for capturing Ollama conversations."""

    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        proxy_port: int = 11435,
        memory_path: str = "./memora_data",
        verbose: bool = True,
    ):
        """Initialize the proxy.

        Args:
            ollama_host: Ollama service URL
            proxy_port: Port for proxy to listen on
            memory_path: Path to Memora storage
            verbose: Print memory capture logs
        """
        self.ollama_host = ollama_host
        self.proxy_port = proxy_port
        self.memory_store = MemoraStore(memory_path)
        self.verbose = verbose

        # Create FastAPI app
        self.app = FastAPI(title="Memora Ollama Proxy")
        self.setup_routes()

        # HTTP client for forwarding requests
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 min timeout for LLM

    def setup_routes(self):
        """Setup proxy routes."""

        @self.app.api_route(
            "/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"]
        )
        async def proxy_all(request: Request, path: str):
            """Proxy all requests to Ollama."""
            return await self.handle_request(request, path)

    async def handle_request(self, request: Request, path: str):
        """Handle and forward request to Ollama.

        Args:
            request: Incoming FastAPI request
            path: Request path

        Returns:
            Response from Ollama
        """
        # Build target URL
        url = f"{self.ollama_host}/{path}"

        # Get request body
        body = await request.body()

        # Check if this is a chat/generate endpoint (where we capture memories)
        is_chat_endpoint = path in ["api/chat", "api/generate"]

        # Parse request data for memory capture
        request_data = None
        if is_chat_endpoint and body:
            try:
                request_data = json.loads(body)
            except json.JSONDecodeError:
                pass

        # Forward request to Ollama
        try:
            # Check if streaming response
            is_streaming = False
            if request_data:
                is_streaming = request_data.get("stream", False)

            if is_streaming:
                # Handle streaming response
                return await self.handle_streaming_request(url, request, body, request_data)
            else:
                # Handle normal request
                response = await self.client.request(
                    method=request.method,
                    url=url,
                    content=body,
                    headers=dict(request.headers),
                )

                # Capture memories from response
                if is_chat_endpoint and response.status_code == 200:
                    await self.capture_memories(request_data, response.content)

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
        """Handle streaming response from Ollama.

        Args:
            url: Target Ollama URL
            request: Original request
            body: Request body
            request_data: Parsed request data

        Returns:
            StreamingResponse
        """
        # Collect full response for memory capture
        full_response = []

        async def stream_generator():
            """Generator that streams response and collects it."""
            async with self.client.stream(
                method=request.method,
                url=url,
                content=body,
                headers=dict(request.headers),
            ) as response:
                async for chunk in response.aiter_bytes():
                    full_response.append(chunk)
                    yield chunk

            # After streaming completes, capture memories
            combined_response = b"".join(full_response)
            await self.capture_memories(request_data, combined_response)

        return StreamingResponse(stream_generator(), media_type="application/json")

    async def capture_memories(self, request_data: Optional[dict], response_content: bytes):
        """Capture memories from request and response.

        Args:
            request_data: Parsed request data
            response_content: Response from Ollama
        """
        if not request_data:
            return

        try:
            # Extract user message from request
            user_message = None

            # For /api/chat endpoint
            if "messages" in request_data:
                messages = request_data["messages"]
                if messages and isinstance(messages, list):
                    # Get last user message
                    for msg in reversed(messages):
                        if msg.get("role") == "user":
                            user_message = msg.get("content")
                            break

            # For /api/generate endpoint
            elif "prompt" in request_data:
                user_message = request_data["prompt"]

            # Extract AI response
            ai_response = None
            try:
                # Handle streaming response (multiple JSON objects)
                response_lines = response_content.decode("utf-8").strip().split("\n")
                for line in response_lines:
                    if line.strip():
                        response_json = json.loads(line)
                        if "message" in response_json:
                            content = response_json["message"].get("content", "")
                            if content:
                                if ai_response is None:
                                    ai_response = content
                                else:
                                    ai_response += content
                        elif "response" in response_json:
                            content = response_json.get("response", "")
                            if content:
                                if ai_response is None:
                                    ai_response = content
                                else:
                                    ai_response += content
            except Exception as e:
                logger.debug(f"Error parsing response: {e}")

            # Extract and store memories
            session_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

            if user_message:
                user_facts = extract_facts(user_message, source=f"ollama:user:{session_id}")

                if user_facts and self.verbose:
                    logger.info(f"Captured {len(user_facts)} memories from user")

                for fact in user_facts:
                    self.memory_store.add(fact.content, source=fact.source)

            if ai_response:
                ai_facts = extract_facts(ai_response, source=f"ollama:ai:{session_id}")

                if ai_facts and self.verbose:
                    logger.info(f"Captured {len(ai_facts)} memories from AI")

                for fact in ai_facts:
                    self.memory_store.add(fact.content, source=fact.source)

        except Exception as e:
            logger.error(f"Error capturing memories: {e}")

    def run(self):
        """Run the proxy server."""
        logger.info(f"🧠 Memora Proxy starting on port {self.proxy_port}")
        logger.info(f"   Forwarding to: {self.ollama_host}")
        logger.info(f"   Memory storage: {self.memory_store.memory_root}")
        logger.info("")
        logger.info("✓ Proxy is running!")
        logger.info(
            "  Configure Ollama clients to use: http://localhost:{}".format(self.proxy_port)
        )
        logger.info("")

        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=self.proxy_port,
            log_level="warning",  # Reduce uvicorn logs
        )


def start_proxy(
    ollama_host: str = "http://localhost:11434",
    proxy_port: int = 11435,
    memory_path: str = "./memora_data",
    verbose: bool = True,
):
    """Start the Ollama proxy server.

    Args:
        ollama_host: Ollama service URL
        proxy_port: Port for proxy
        memory_path: Path to Memora storage
        verbose: Print capture logs
    """
    proxy = OllamaProxy(
        ollama_host=ollama_host, proxy_port=proxy_port, memory_path=memory_path, verbose=verbose
    )
    proxy.run()


if __name__ == "__main__":
    start_proxy()
