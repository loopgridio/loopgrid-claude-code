#!/usr/bin/env python3
"""Check environment, optional CLI dependencies, and LoopGrid Core connectivity."""
from __future__ import annotations
import importlib.util
import os
from pathlib import Path
import shutil
import sys
from urllib.error import URLError
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loopgrid_hook import config, project_opted_in, PROJECT_OPT_IN


def main():
    try:
        c = config()
    except Exception as ex:
        print(f"[ERROR] Invalid LoopGrid environment: {ex}")
        return 1
    print("LoopGrid for Claude Code — environment diagnostic")
    print("mode:", c["mode"])
    print("workspace:", c["workspace"])
    print("base:", c["base"])
    print("configured service key:", bool(c["key"]))
    print("configured policy:", bool(c["policy"]))
    project = os.environ.get("CLAUDE_PROJECT_DIR") or str(Path.cwd())
    print("project root for diagnostic:", project)
    print("project hook activation:", project_opted_in({"CLAUDE_PROJECT_DIR": project}))
    print("project activation marker:", str(Path(project) / PROJECT_OPT_IN))
    print("uvx available:", bool(shutil.which("uvx")))
    print("python version:", sys.version.split()[0])
    try:
        with urlopen(c["base"] + "/ready", timeout=5) as r:
            print("Core /ready:", r.status)
            return 0 if r.status == 200 else 1
    except (URLError, TimeoutError, OSError) as ex:
        print("Core is not reachable:", type(ex).__name__)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
