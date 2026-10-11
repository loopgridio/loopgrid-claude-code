#!/usr/bin/env python3
"""Offline configuration diagnostics for the LoopGrid Claude Code plugin.

This diagnostic does not read credentials or initiate network requests. To
check connectivity, the operator should explicitly test the configured Core.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core_origin import validate_core_origin
from loopgrid_hook import PROJECT_OPT_IN, project_opted_in


def main():
    print("LoopGrid for Claude Code — offline environment diagnostic")
    base = (os.getenv("CLAUDE_PLUGIN_OPTION_CORE_URL")
            or os.getenv("LOOPGRID_BASE_URL", "http://127.0.0.1:8000"))
    try:
        base = validate_core_origin(base)
    except ValueError as exc:
        print("[ERROR]", str(exc))
        return 1
    mode = os.getenv("LOOPGRID_CLAUDE_MODE", "off").strip().lower()
    if mode not in {"off", "observe", "enforce"}:
        print("[ERROR] Invalid LOOPGRID_CLAUDE_MODE")
        return 1
    project = os.getenv("CLAUDE_PROJECT_DIR") or str(Path.cwd())
    print("mode:", mode)
    print("workspace:", (os.getenv("CLAUDE_PLUGIN_OPTION_WORKSPACE_ID")
                        or os.getenv("LOOPGRID_WORKSPACE", "default")))
    print("configured Core URL:", base)
    print("project root for diagnostic:", project)
    print("project hook activation:", project_opted_in({"CLAUDE_PROJECT_DIR": project}))
    print("project activation marker:", str(Path(project) / PROJECT_OPT_IN))
    uv_available = bool(shutil.which("uv"))
    lock_present = (Path(__file__).resolve().parents[1] / "uv.lock").is_file()
    python_ok = sys.version_info >= (3, 10)
    print("uv available:", uv_available)
    print("Directory dependency uv.lock snapshot present:", lock_present)
    print("python version:", sys.version.split()[0])
    print("No network request was sent. Test Core connectivity explicitly if needed.")
    if not uv_available or not python_ok:
        print("[ERROR] Missing local prerequisite; see README Installation.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
