"""Session lifecycle management for websocket-connected Claude processes."""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import WebSocket

from agent.cc_process import CCProcess
from agent.worktree import WorktreeManager
from config import MAX_CONCURRENT_SESSIONS, WORKTREE_AUTO_CLEANUP

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Session:
    session_id: str
    worktree_path: Path
    cc_process: CCProcess
    websocket: WebSocket
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "active"
    message_history: list[dict[str, str]] = field(default_factory=list)


class SessionManager:
    def __init__(self, worktree_manager: WorktreeManager, claude_path: str):
        self.worktree_manager = worktree_manager
        self.claude_path = claude_path
        self.sessions: dict[str, Session] = {}
        self._lock = asyncio.Lock()

    async def create_session(self, websocket: WebSocket) -> Session:
        async with self._lock:
            if len(self.sessions) >= MAX_CONCURRENT_SESSIONS:
                raise RuntimeError("Maximum concurrent sessions reached")
            session_id = str(uuid.uuid4())
            worktree_path = self.worktree_manager.create_worktree(session_id)
            session = Session(
                session_id=session_id,
                worktree_path=worktree_path,
                cc_process=CCProcess(self.claude_path),
                websocket=websocket,
            )
            self.sessions[session_id] = session
            return session

    async def get_or_create_session(self, session_id: str | None, websocket: WebSocket) -> Session:
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]
        return await self.create_session(websocket)

    async def run_message(self, session: Session, content: str) -> None:
        session.status = "active"
        session.message_history.append({"role": "user", "summary": content[:200]})

        async def emit(event: dict[str, Any]) -> None:
            await session.websocket.send_json(event)
            if event["type"] == "chunk":
                session.message_history.append({"role": "assistant", "summary": event["content"][:200]})

        await session.cc_process.run_prompt(content, session.session_id, session.worktree_path, emit)
        session.status = "idle"
        await self.on_session_complete(session)

    async def close_session(self, session_id: str) -> None:
        session = self.sessions.pop(session_id, None)
        if not session:
            return
        session.status = "closed"
        await session.cc_process.terminate()
        if WORKTREE_AUTO_CLEANUP:
            self.worktree_manager.cleanup_worktree(session_id)

    async def close_by_websocket(self, websocket: WebSocket) -> None:
        targets = [sid for sid, s in self.sessions.items() if s.websocket == websocket]
        for sid in targets:
            await self.close_session(sid)

    async def on_session_complete(self, session: Session) -> None:
        """Extension hook for post-response processing, e.g. memory update."""
        logger.debug("Session %s completed round", session.session_id)
