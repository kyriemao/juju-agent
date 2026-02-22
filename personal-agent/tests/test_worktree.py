from pathlib import Path

from agent.worktree import WorktreeManager


def test_create_and_list_worktree(tmp_path: Path) -> None:
    manager = WorktreeManager(workspace_root=tmp_path / "workspace", base_repo_path=tmp_path / "workspace/base")

    created = manager.create_worktree("session-a")

    assert created.exists()
    listed = manager.list_worktrees()
    paths = [item.get("worktree", "") for item in listed]
    assert str(created) in paths


def test_cleanup_worktree(tmp_path: Path) -> None:
    manager = WorktreeManager(workspace_root=tmp_path / "workspace", base_repo_path=tmp_path / "workspace/base")
    created = manager.create_worktree("session-clean")
    assert created.exists()

    manager.cleanup_worktree("session-clean")

    assert not created.exists()
