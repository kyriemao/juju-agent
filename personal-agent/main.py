"""FastAPI entrypoint for Personal Agent."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from agent.session import SessionManager
from agent.worktree import WorktreeManager
from config import BASE_REPO_PATH, CLAUDE_PATH, HOST, LOG_LEVEL, PORT, WORKSPACE_ROOT

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Personal Agent")
worktree_manager = WorktreeManager(WORKSPACE_ROOT, BASE_REPO_PATH)
session_manager = SessionManager(worktree_manager, CLAUDE_PATH)


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(Path(__file__).parent / "frontend" / "index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            msg_type = payload.get("type")

            if msg_type == "new_session":
                session = await session_manager.create_session(websocket)
                await websocket.send_json(
                    {
                        "type": "session_created",
                        "session_id": session.session_id,
                        "worktree_path": str(session.worktree_path),
                    }
                )
                continue

            if msg_type == "message":
                session = await session_manager.get_or_create_session(payload.get("session_id"), websocket)
                if not payload.get("session_id"):
                    await websocket.send_json(
                        {
                            "type": "session_created",
                            "session_id": session.session_id,
                            "worktree_path": str(session.worktree_path),
                        }
                    )
                await session_manager.run_message(session, payload.get("content", ""))
                continue

            await websocket.send_json({"type": "error", "content": f"Unknown message type: {msg_type}"})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
        await session_manager.close_by_websocket(websocket)
    except Exception as exc:  # noqa: BLE001
        logger.exception("WebSocket error")
        await websocket.send_json({"type": "error", "content": str(exc)})
        await session_manager.close_by_websocket(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)
