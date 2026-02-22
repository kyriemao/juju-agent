"""本地环境自检脚本：检查 Personal Agent 运行与 Computer Use 所需依赖。"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from typing import Iterable


def check_python_modules(modules: Iterable[str]) -> list[str]:
    missing: list[str] = []
    for name in modules:
        if importlib.util.find_spec(name) is None:
            missing.append(name)
    return missing


def check_claude() -> tuple[bool, str]:
    path = shutil.which("claude")
    if not path:
        return False, "未找到 claude CLI（请先安装 Claude Code）"

    try:
        result = subprocess.run(
            [path, "--help"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except Exception as exc:  # noqa: BLE001
        return False, f"claude 命令执行失败: {exc}"

    if result.returncode != 0:
        return False, f"claude --help 返回非 0: {result.stderr.strip() or result.stdout.strip()}"

    return True, path


def main() -> int:
    print("== Personal Agent 环境自检 ==")

    missing = check_python_modules(["fastapi", "uvicorn", "pytest"])
    if missing:
        print(f"[FAIL] 缺少 Python 依赖: {', '.join(missing)}")
    else:
        print("[OK] Python 依赖检查通过 (fastapi/uvicorn/pytest)")

    claude_ok, claude_msg = check_claude()
    if claude_ok:
        print(f"[OK] 找到 claude CLI: {claude_msg}")
    else:
        print(f"[FAIL] {claude_msg}")

    if missing or not claude_ok:
        print("\n结论：当前环境不满足完整端到端验证条件。")
        return 1

    print("\n结论：基础依赖齐全，可继续执行端到端联调。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
