"""Application configuration for Personal Agent."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = BASE_DIR / "workspace"
BASE_REPO_PATH = WORKSPACE_ROOT / "base"
CLAUDE_PATH = os.getenv("CLAUDE_PATH", "claude")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Extension-ready config switches
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "cc")
MEMORY_ENABLED = os.getenv("MEMORY_ENABLED", "false").lower() == "true"
WORKTREE_AUTO_CLEANUP = os.getenv("WORKTREE_AUTO_CLEANUP", "false").lower() == "true"
MAX_CONCURRENT_SESSIONS = int(os.getenv("MAX_CONCURRENT_SESSIONS", "10"))
