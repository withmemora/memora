"""FastAPI server for Memora conversational memory system.

Provides REST API endpoints for:
- Memory management (add, search, retrieve)
- Branch operations (create, switch, list)
- Memory export and analytics
- WebSocket support for real-time updates
"""

from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .readable_memory import ReadableMemoryManager


# Pydantic models for API requests/responses


class AddMessageRequest(BaseModel):
    """Request to add a new message to memory."""

    message: str = Field(..., description="The message to add to memory")
    branch: Optional[str] = Field("main", description="Branch to add message to")
    source: str = Field("api", description="Source of the message")


class SearchRequest(BaseModel):
    """Request to search memories."""

    query: Optional[str] = Field(None, description="Text to search for")
    category: Optional[str] = Field(None, description="Category to filter by")
    entity: Optional[str] = Field(None, description="Entity to filter by")
    confidence_min: Optional[float] = Field(0.0, description="Minimum confidence score")
    limit: int = Field(20, description="Maximum results to return")


class MemoryResponse(BaseModel):
    """Response containing memory information."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str = ""
    count: int = 0


class SessionResponse(BaseModel):
    """Response for session operations."""

    success: bool
    session_id: str
    message: str = ""


class BranchRequest(BaseModel):
    """Request to create or switch branches."""

    branch_name: str = Field(..., description="Name of the branch")


# Global state
memory_manager: Optional[ReadableMemoryManager] = None
active_sessions: Dict[str, str] = {}  # session_id -> current_branch
websocket_connections: List[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    global memory_manager
    memory_root = Path("./memora_data")
    memory_root.mkdir(exist_ok=True)
    memory_manager = ReadableMemoryManager(memory_root)

    logging.info(f"Memora API server started with memory at {memory_root}")
    yield

    # Shutdown
    logging.info("Memora API server shutting down")


# Create FastAPI app
app = FastAPI(
    title="Memora API",
    description="Git-style versioned memory for LLMs with human-readable interface",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health and info endpoints


@app.get("/dashboard")
async def dashboard():
    """Serve the web dashboard."""
    dashboard_path = Path(__file__).parent.parent.parent.parent / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    else:
        return JSONResponse({"error": "Dashboard not found"}, status_code=404)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Memora API",
        "description": "Git-style versioned memory for LLMs",
        "version": "1.0.0",
        "docs": "/docs",
        "dashboard": "/dashboard",
        "status": "operational",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "memory_root": str(memory_manager.memory_root) if memory_manager else None,
        "active_sessions": len(active_sessions),
    }


# Session management endpoints


@app.post("/sessions", response_model=SessionResponse)
async def create_session(branch: str = "main"):
    """Create a new memory session."""
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")

    try:
        session_id = memory_manager.start_conversation(branch)
        active_sessions[session_id] = branch

        return SessionResponse(
            success=True, session_id=session_id, message=f"Session created on branch '{branch}'"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@app.get("/sessions")
async def list_sessions():
    """List all active sessions."""
    return {
        "sessions": [
            {"session_id": sid, "branch": branch} for sid, branch in active_sessions.items()
        ],
        "count": len(active_sessions),
    }


@app.delete("/sessions/{session_id}")
async def end_session(session_id: str):
    """End a session."""
    if session_id in active_sessions:
        del active_sessions[session_id]
        return {"success": True, "message": "Session ended"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


# Memory management endpoints


@app.post("/memory", response_model=MemoryResponse)
async def add_memory(request: AddMessageRequest):
    """Add a new message to memory."""
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")

    try:
        # Create session if needed
        session_id = memory_manager.start_conversation(request.branch or "main")
        if session_id not in active_sessions:
            active_sessions[session_id] = request.branch or "main"

        # Add message to memory
        result = memory_manager.add_message(
            session_id=session_id, message=request.message, source=request.source
        )

        # Notify WebSocket connections
        await notify_websocket_clients(
            {
                "type": "memory_added",
                "session_id": session_id,
                "branch": request.branch,
                "result": result,
            }
        )

        return MemoryResponse(
            success=True,
            data=result,
            message="Memory added successfully",
            count=result.get("memories_created", 0),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add memory: {str(e)}")


@app.post("/memory/search", response_model=MemoryResponse)
async def search_memories(request: SearchRequest):
    """Search memories with filters."""
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")

    try:
        # Use first available session or create one
        session_id = next(iter(active_sessions.keys()), None)
        if not session_id:
            session_id = memory_manager.start_conversation("main")
            active_sessions[session_id] = "main"

        results = memory_manager.search_memories(
            session_id=session_id,
            search_text=request.query,
            category=request.category,
            entity=request.entity,
            confidence_min=request.confidence_min,
            limit=request.limit,
        )

        return MemoryResponse(
            success=True,
            data={"memories": results},
            message=f"Found {len(results)} memories",
            count=len(results),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/memory/{memory_id}")
async def get_memory(memory_id: str):
    """Get a specific memory by ID."""
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")

    try:
        # Use first available session or create one
        session_id = next(iter(active_sessions.keys()), None)
        if not session_id:
            session_id = memory_manager.start_conversation("main")
            active_sessions[session_id] = "main"

        memory = memory_manager.get_memory_by_id(memory_id)
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")

        return MemoryResponse(success=True, data=memory, message="Memory retrieved successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memory: {str(e)}")


@app.get("/memory/categories")
async def list_categories():
    """List all available memory categories."""
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")

    try:
        # Use first available session or create one
        session_id = next(iter(active_sessions.keys()), None)
        if not session_id:
            session_id = memory_manager.start_conversation("main")
            active_sessions[session_id] = "main"

        categories = memory_manager.list_memories_by_category(session_id)

        return {"success": True, "categories": categories, "count": len(categories)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list categories: {str(e)}")


@app.get("/memory/timeline")
async def get_memory_timeline():
    """Get chronological memory timeline."""
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")

    try:
        # Use first available session or create one
        session_id = next(iter(active_sessions.keys()), None)
        if not session_id:
            session_id = memory_manager.start_conversation("main")
            active_sessions[session_id] = "main"

        timeline = memory_manager.get_memory_timeline(session_id)

        return MemoryResponse(
            success=True,
            data={"timeline": timeline},
            message=f"Timeline contains {len(timeline)} entries",
            count=len(timeline),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get timeline: {str(e)}")


# Export endpoints


@app.get("/memory/export")
async def export_memories(
    format: str = Query("json", description="Export format: json or text"),
    session_id: Optional[str] = Query(None, description="Session ID to export"),
):
    """Export memories in specified format."""
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")

    if format not in ["json", "text"]:
        raise HTTPException(status_code=400, detail="Format must be 'json' or 'text'")

    try:
        # Use provided session or first available
        if not session_id:
            session_id = next(iter(active_sessions.keys()), None)
        if not session_id:
            session_id = memory_manager.start_conversation("main")
            active_sessions[session_id] = "main"

        export_data = memory_manager.export_readable_memories(session_id, format)

        if format == "json":
            return JSONResponse(
                content={"success": True, "data": export_data},
                headers={"Content-Type": "application/json"},
            )
        else:
            return JSONResponse(
                content={"success": True, "data": export_data},
                headers={"Content-Type": "text/plain"},
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# Branch management endpoints


@app.post("/branches")
async def create_branch(request: BranchRequest):
    """Create a new branch."""
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")

    try:
        session_id = memory_manager.start_conversation(request.branch_name)
        active_sessions[session_id] = request.branch_name

        return {
            "success": True,
            "branch": request.branch_name,
            "session_id": session_id,
            "message": f"Branch '{request.branch_name}' created",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create branch: {str(e)}")


@app.get("/branches")
async def list_branches():
    """List all available branches."""
    # For now, return branches from active sessions
    # In a full implementation, this would query the underlying Git-style storage
    branches = set(active_sessions.values())

    return {"success": True, "branches": list(branches), "count": len(branches)}


# WebSocket endpoint for real-time updates


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time memory updates."""
    await websocket.accept()
    websocket_connections.append(websocket)

    try:
        while True:
            # Keep connection alive and wait for messages
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_json(
                {"type": "heartbeat", "timestamp": datetime.utcnow().isoformat()}
            )
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)


async def notify_websocket_clients(message: dict):
    """Send message to all connected WebSocket clients."""
    if not websocket_connections:
        return

    disconnected = []
    for websocket in websocket_connections:
        try:
            await websocket.send_json(message)
        except Exception:
            disconnected.append(websocket)

    # Remove disconnected clients
    for websocket in disconnected:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)


# Development server function


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Start the Memora API server."""
    uvicorn.run(
        "memora.interface.server:app", host=host, port=port, reload=reload, log_level="info"
    )


if __name__ == "__main__":
    start_server()
