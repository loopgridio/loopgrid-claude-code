#!/usr/bin/env python3
"""Launch the locked LoopGrid MCP runtime using explicit Claude plugin options.

No shell interpolation is used for credentials. Claude-managed sensitive
userConfig is passed to plugin subprocesses as CLAUDE_PLUGIN_OPTION_SERVICE_KEY.
"""
from __future__ import annotations
import os


def prepare_environment(env=None):
    env = dict(os.environ if env is None else env)
    # Never implicitly inherit a machine-wide credential into the plugin.
    env.pop("LOOPGRID_SERVICE_KEY", None)
    key = env.get("CLAUDE_PLUGIN_OPTION_SERVICE_KEY", "").strip()
    if key:
        env["LOOPGRID_SERVICE_KEY"] = key
    core_url = env.get("CLAUDE_PLUGIN_OPTION_CORE_URL", "").strip()
    if core_url:
        env["LOOPGRID_BASE_URL"] = core_url
    workspace = env.get("CLAUDE_PLUGIN_OPTION_WORKSPACE_ID", "").strip()
    if workspace:
        env["LOOPGRID_WORKSPACE"] = workspace
    return env


def main():
    new_env = prepare_environment()
    os.environ.clear()
    os.environ.update(new_env)
    from loopgrid_mcp.server import main as mcp_main
    mcp_main()


if __name__ == "__main__":
    main()
