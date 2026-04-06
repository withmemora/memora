"""FastAPI server for Memora v3.0.

Provides REST API endpoints for:
- Memory management (paginated list, search, retrieve)
- Session management (list, active, details)
- Branch operations (create, switch, list, status)
- Graph endpoints (nodes, edges, profile, query)
- Timeline and export
- WebSocket support for real-time updates
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

from memora.core.engine import CoreEngine


class AddMemoryRequest(BaseModel):
    content: str = Field(..., description="Human-readable memory content")
    branch: Optional[str] = Field("main", description="Branch to add to")
    source: str = Field("manual", description="Source of the memory")


class SearchRequest(BaseModel):
    query: Optional[str] = Field(None, description="Text to search for")
    memory_type: Optional[str] = Field(None, description="Filter by type")
    limit: int = Field(100, description="Maximum results")


memory_engine: Optional[CoreEngine] = None
websocket_connections: List[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    global memory_engine
    memory_root = Path("./memora_data")
    memory_root.mkdir(exist_ok=True)

    memory_engine = CoreEngine()
    try:
        memory_engine.open_store(memory_root)
    except Exception:
        memory_engine.init_store(memory_root)
        memory_engine.open_store(memory_root)

    logging.info(f"Memora API server started with memory at {memory_root}")
    yield
    logging.info("Memora API server shutting down")


app = FastAPI(
    title="Memora API v3.0",
    description="Git-style versioned memory for LLMs with human-readable interface",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/dashboard")
async def dashboard():
    dashboard_path = Path(__file__).parent.parent.parent.parent / "dashboard_local.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    return JSONResponse({"error": "Dashboard not found"}, status_code=404)


@app.get("/")
async def root():
    return {
        "name": "Memora API",
        "version": "3.0.0",
        "docs": "/docs",
        "dashboard": "/dashboard",
        "status": "operational",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/stats")
async def get_stats():
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        stats = memory_engine.get_store_stats()
        commits = memory_engine.get_log(limit=100)
        last_commit_time = commits[0].committed_at if commits else None
        return {
            "success": True,
            "data": {
                "total_memories": stats.get("memory_count", 0),
                "total_commits": stats.get("commit_count", 0),
                "total_branches": stats.get("branch_count", 0),
                "total_sessions": stats.get("session_count", 0),
                "current_branch": memory_engine.get_current_branch() or "main",
                "open_conflicts": stats.get("open_conflict_count", 0),
                "total_objects": stats.get("object_count", 0),
                "last_commit": last_commit_time,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.post("/memory")
async def add_memory(request: AddMemoryRequest):
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        results = memory_engine.ingest_text(request.content, source=request.source)
        await notify_websocket_clients({"type": "memory_added", "count": len(results)})
        return {
            "success": True,
            "memories_created": len(results),
            "memories": [{"id": m.id, "content": m.content} for _, m in results],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add memory: {str(e)}")


@app.get("/memories")
async def list_memories(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    branch: Optional[str] = Query(None),
    memory_type: Optional[str] = Query(None),
):
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        memories = memory_engine.get_all_memories(
            branch=branch, memory_type=memory_type, skip=skip, limit=limit
        )
        return {
            "success": True,
            "memories": [m.to_dict() for m in memories],
            "count": len(memories),
            "skip": skip,
            "limit": limit,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list memories: {str(e)}")


@app.get("/memories/{memory_id}")
async def get_memory(memory_id: str):
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        memory = memory_engine.get_memory(memory_id)
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        return {"success": True, "memory": memory.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memory: {str(e)}")


@app.delete("/memories/{memory_id}")
async def forget_memory(memory_id: str):
    """Delete a memory by ID. Selective forgetting."""
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        deleted = memory_engine.forget_memory(memory_id)
        if deleted:
            return {"success": True, "message": f"Memory {memory_id} deleted"}
        raise HTTPException(status_code=404, detail="Memory not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete memory: {str(e)}")


@app.post("/memories/{memory_id}/pin")
async def toggle_pin_memory(memory_id: str):
    """Toggle pin status of a memory."""
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        success, new_state = memory_engine.toggle_pin_memory(memory_id)
        if success:
            await notify_websocket_clients(
                {
                    "type": "memory_pinned" if new_state else "memory_unpinned",
                    "memory_id": memory_id,
                }
            )
            return {"success": True, "pinned": new_state}
        raise HTTPException(status_code=404, detail="Memory not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle pin: {str(e)}")


@app.post("/memories/{memory_id}/hide")
async def toggle_hide_memory(memory_id: str):
    """Toggle hide status of a memory (hide from LLM context)."""
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        success, new_state = memory_engine.toggle_hide_memory(memory_id)
        if success:
            await notify_websocket_clients(
                {"type": "memory_hidden" if new_state else "memory_shown", "memory_id": memory_id}
            )
            return {"success": True, "hidden": new_state}
        raise HTTPException(status_code=404, detail="Memory not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle hide: {str(e)}")


@app.get("/memories/{memory_id}")
async def get_memory(memory_id: str):
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        memory = memory_engine.get_memory(memory_id)
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        return {"success": True, "memory": memory.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memory: {str(e)}")


@app.post("/memory/search")
async def search_memories(request: SearchRequest):
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        if request.query:
            memories = memory_engine.search_memories(request.query)
        else:
            memories = memory_engine.get_all_memories(
                memory_type=request.memory_type, skip=0, limit=request.limit
            )
        return {
            "success": True,
            "memories": [m.to_dict() for m in memories[: request.limit]],
            "count": len(memories),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/memory/export")
async def export_memories(
    format: str = Query("json", description="Export format: json, markdown, text"),
    branch: Optional[str] = Query(None),
):
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        exported = memory_engine.export_memories(format=format, branch=branch)
        return {"success": True, "data": exported}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@app.get("/memory/timeline")
async def get_timeline(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        memories = memory_engine.get_timeline(start_date or "", end_date or "")
        return {
            "success": True,
            "timeline": [m.to_dict() for m in memories],
            "count": len(memories),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get timeline: {str(e)}")


@app.get("/sessions")
async def list_sessions():
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        sessions = memory_engine.list_sessions()
        return {
            "success": True,
            "sessions": [s.to_dict() for s in sessions],
            "count": len(sessions),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@app.get("/sessions/active")
async def get_active_session():
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        session = memory_engine.get_active_session()
        if session:
            return {"success": True, "session": session.to_dict()}
        return {"success": True, "session": None, "message": "No active session"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active session: {str(e)}")


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        sessions = memory_engine.list_sessions()
        for s in sessions:
            if s.id == session_id:
                return {"success": True, "session": s.to_dict()}
        raise HTTPException(status_code=404, detail="Session not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


@app.get("/branches")
async def list_branches():
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        branches = memory_engine.list_branches()
        current_branch = memory_engine.get_current_branch() or "main"
        branch_list = [
            {"name": name, "commit_hash": ch, "is_current": name == current_branch}
            for name, ch in branches
        ]
        if not branch_list:
            branch_list = [{"name": "main", "commit_hash": None, "is_current": True}]
        return {"success": True, "branches": branch_list, "current_branch": current_branch}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list branches: {str(e)}")


@app.get("/branches/status")
async def get_branch_status():
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        all_status = memory_engine.get_all_branches_status()
        current = memory_engine.get_current_branch() or "main"
        return {"success": True, "current_branch": current, "branches": all_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get branch status: {str(e)}")


@app.post("/branches")
async def create_branch(name: str = Query(..., description="Branch name")):
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        memory_engine.create_branch(name)
        return {"success": True, "branch": name, "message": f"Branch '{name}' created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create branch: {str(e)}")


@app.put("/branches/{branch_name}")
async def switch_branch(branch_name: str):
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        memory_engine.switch_branch(branch_name)
        return {"success": True, "branch": branch_name, "message": f"Switched to '{branch_name}'"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to switch branch: {str(e)}")


@app.get("/commits")
async def get_commits(limit: int = Query(20, description="Number of commits")):
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        commits = memory_engine.get_log(limit=limit)
        commit_list = []
        for c in commits:
            commit_list.append(
                {
                    "hash": c.root_tree_hash[:12] if c.root_tree_hash else "unknown",
                    "author": c.author,
                    "message": c.message,
                    "committed_at": c.committed_at,
                    "parent_hash": c.parent_hash[:12] if c.parent_hash else None,
                }
            )
        return {"success": True, "commits": commit_list, "count": len(commit_list)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get commits: {str(e)}")


@app.get("/graph/nodes")
async def get_graph_nodes(node_type: Optional[str] = Query(None)):
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        nodes = memory_engine.get_graph_nodes(node_type)
        return {"success": True, "nodes": nodes, "count": len(nodes)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get nodes: {str(e)}")


@app.get("/graph/edges")
async def get_graph_edges():
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        edges = memory_engine.get_graph_edges()
        return {"success": True, "edges": edges, "count": len(edges)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get edges: {str(e)}")


@app.get("/graph/profile")
async def get_graph_profile():
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        profile = memory_engine.get_graph_profile()
        return {"success": True, "profile": profile}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")


@app.get("/graph/query")
async def graph_query(entity: str = Query(..., description="Entity to query")):
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        edges = memory_engine.graph_query(entity)
        return {"success": True, "entity": entity, "edges": edges, "count": len(edges)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query graph: {str(e)}")


@app.get("/conflicts")
async def get_conflicts():
    if not memory_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    try:
        conflicts = memory_engine.get_open_conflicts()
        return {"success": True, "conflicts": [(cid, c.to_dict()) for cid, c in conflicts]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conflicts: {str(e)}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates.

    Sends notifications for:
    - Session start/end with memory counts
    - Memory operations (add, delete, pin, hide)
    - Graph updates
    - Branch changes
    - Conflicts detected
    """
    await websocket.accept()
    websocket_connections.append(websocket)

    # Send initial connection confirmation
    await websocket.send_json(
        {
            "type": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "WebSocket connected - real-time updates enabled",
        }
    )

    try:
        while True:
            # Wait for client ping to maintain connection
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_json(
                    {"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()}
                )
    except WebSocketDisconnect:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)


async def notify_websocket_clients(message: dict):
    if not websocket_connections:
        return
    disconnected = []
    for ws in websocket_connections:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        if ws in websocket_connections:
            websocket_connections.remove(ws)


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    uvicorn.run(
        "memora.interface.server:app", host=host, port=port, reload=reload, log_level="info"
    )


if __name__ == "__main__":
    start_server()
