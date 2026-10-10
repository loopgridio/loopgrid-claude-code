# Anthropic Plugin Directory — release gate

The directory scanner passed plugin structure but reported three policy holds and two warnings for the original `uvx` and machine credential setup. This patch changes the server launch to a reproducible `uv` project and declares Claude-managed `userConfig` for the service key. Its lock file **must be generated from the actual registry**, not fabricated.

## On Windows (one-time, in plugin repository root)

```powershell
uv --version
uv lock
uv lock --check
python -m unittest discover -s tests -q
claude plugin validate --strict .
```

Confirm `uv.lock` exists and has an entry for `loopgrid-mcp` version `0.1.0` plus dependency source and distribution hashes. `uv lock` resolves upstream dependencies on the connected machine. Do **not** commit/publish a release that lacks `uv.lock`. Commit `pyproject.toml` and `uv.lock` together.

Because the MCP launcher changed from `uvx` to `uv run --locked`, **repeat plugin discovery and verify all six MCP tools connect** (`claude --plugin-dir .`, then `/mcp`). Also check that the plugin's `service_key` option is offered under Claude's plugin configuration UI. If the frontend doesn't prompt automatically, configure using CLI/plugin management; never paste tokens into skills or commit them.

## Revalidate in Claude's directory portal

Use the repository's new commit and click **Re-validate**. Examine the expanded reasons for both policy holds and warnings. We cannot guarantee Anthropic removes the holds, and `userConfig` experiences vary among Claude Code/Cowork clients. Report any remaining holds before submission rather than bypassing them.

The `Local MCP server: not on claude.ai` notice is informational: this plugin targets Claude Code and Claude Cowork, not web-only claude.ai. The plugin-scoped server name is `mcp__plugin_loopgrid_loopgrid__<tool>` in Claude Code. Retain support for a manually-added `mcp__loopgrid__` server separately when appropriate.

The marketplace icon is the existing LoopGrid mark, converted to a 1024×1024 PNG from the site's unchanged SVG. The portal warns that the listing icon may be frozen when the draft is first saved/submitted; inspect its preview before finalizing.
