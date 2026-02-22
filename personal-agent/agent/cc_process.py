"""Claude Code subprocess wrapper with stream-json parsing."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Awaitable, Callable

from agent.output_filter import filter_event

logger = logging.getLogger(__name__)

EventCallback = Callable[[dict[str, Any]], Awaitable[None]]


class CCProcessError(RuntimeError):
    """Raised when Claude CLI cannot be started or managed."""


class CCProcess:
    def __init__(self, claude_path: str):
        self.claude_path = claude_path
        self.process: asyncio.subprocess.Process | None = None

    async def run_prompt(self, message: str, session_id: str, cwd: Path, on_event: EventCallback) -> None:
        if shutil.which(self.claude_path) is None:
            raise CCProcessError(
                f"Claude CLI not found: '{self.claude_path}'. Please install Claude Code and/or set CLAUDE_PATH."
            )

        cmd = [
            self.claude_path,
            "--output-format",
            "stream-json",
            "--verbose",
            "-p",
            message,
        ]
        logger.info("Starting Claude process for session %s", session_id)
        # Remove CLAUDECODE env var to allow launching Claude Code from within
        # an existing Claude Code session (e.g. during testing).
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(cwd),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        assert self.process.stdout is not None
        assert self.process.stderr is not None

        try:
            while True:
                line = await self.process.stdout.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace").strip()
                if not text:
                    continue
                try:
                    raw_event = json.loads(text)
                except json.JSONDecodeError:
                    logger.debug("Ignoring non-json line: %s", text)
                    continue

                filtered = filter_event(raw_event, session_id)
                if filtered:
                    await on_event(filtered)

            stderr_output = (await self.process.stderr.read()).decode("utf-8", errors="replace").strip()
            return_code = await self.process.wait()
            if return_code != 0:
                await on_event(
                    {
                        "type": "error",
                        "session_id": session_id,
                        "content": stderr_output or f"Claude process exited with code {return_code}",
                    }
                )
            else:
                await on_event({"type": "done", "session_id": session_id})
        finally:
            self.process = None

    async def terminate(self) -> None:
        if not self.process:
            return
        self.process.terminate()
        try:
            await asyncio.wait_for(self.process.wait(), timeout=3)
        except asyncio.TimeoutError:
            self.process.kill()
            await self.process.wait()
        finally:
            self.process = None
