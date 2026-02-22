"""Manage isolated git worktrees for each chat session."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class WorktreeError(RuntimeError):
    """Raised when worktree operations fail."""


class WorktreeManager:
    """Create and manage a base git repository plus per-session worktrees."""

    def __init__(self, workspace_root: Path, base_repo_path: Path):
        self.workspace_root = workspace_root
        self.base_repo_path = base_repo_path

    def _run_git(self, args: List[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        cmd = ["git", *args]
        logger.debug("Running command: %s (cwd=%s)", " ".join(cmd), cwd)
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise WorktreeError(
                f"Git command failed ({' '.join(cmd)}): {result.stderr.strip() or result.stdout.strip()}"
            )
        return result

    def ensure_base_repo(self) -> None:
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        if not self.base_repo_path.exists():
            self.base_repo_path.mkdir(parents=True, exist_ok=True)
            self._run_git(["init", "-b", "main"], cwd=self.base_repo_path)
            self._run_git(["config", "user.email", "agent@example.local"], cwd=self.base_repo_path)
            self._run_git(["config", "user.name", "Personal Agent"], cwd=self.base_repo_path)
            readme = self.base_repo_path / "README.md"
            readme.write_text("# Personal Agent Workspace Base\n", encoding="utf-8")
            self._run_git(["add", "."], cwd=self.base_repo_path)
            self._run_git(["commit", "-m", "Initialize base workspace"], cwd=self.base_repo_path)
            logger.info("Initialized base repo at %s", self.base_repo_path)

    def create_worktree(self, session_id: str) -> Path:
        self.ensure_base_repo()
        worktree_path = self.workspace_root / session_id
        if worktree_path.exists():
            return worktree_path

        branch_name = f"session/{session_id}"
        self._run_git(["worktree", "add", "-b", branch_name, str(worktree_path), "main"], cwd=self.base_repo_path)
        return worktree_path

    def cleanup_worktree(self, session_id: str) -> None:
        worktree_path = self.workspace_root / session_id
        if not worktree_path.exists():
            return

        self._run_git(["worktree", "remove", "--force", str(worktree_path)], cwd=self.base_repo_path)
        branch_name = f"session/{session_id}"
        try:
            self._run_git(["branch", "-D", branch_name], cwd=self.base_repo_path)
        except WorktreeError:
            logger.warning("Unable to delete branch %s", branch_name)

        if worktree_path.exists():
            shutil.rmtree(worktree_path, ignore_errors=True)

    def list_worktrees(self) -> list[dict[str, str]]:
        self.ensure_base_repo()
        result = self._run_git(["worktree", "list", "--porcelain"], cwd=self.base_repo_path)
        items: list[dict[str, str]] = []
        current: dict[str, str] = {}
        for line in result.stdout.splitlines():
            if not line.strip():
                if current:
                    items.append(current)
                current = {}
                continue
            key, _, value = line.partition(" ")
            current[key] = value
        if current:
            items.append(current)
        return items
