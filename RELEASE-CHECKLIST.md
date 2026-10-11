# One-update Claude plugin release checkpoint

**Goal:** Keep the original GitHub Directory draft, update `loopgridio/loopgrid-claude-code` **once**, and pursue Anthropic Verified without modifying `loopgrid-mcp==0.1.0` or any other integrations.

## Current source of truth

- This directory is the **candidate plugin source**. It uses **already published** `loopgrid-claude-launcher==0.1.0` and upstream `loopgrid-mcp==0.1.0` unchanged.
- `.claude-plugin/plugin.json` has privacy, support, documentation and terms metadata.
- The repository **includes the genuine Windows-generated `uv.lock`** (38 lockfile entries: 37 registry package resolutions plus the local virtual project). Its release pins are `loopgrid-claude-launcher==0.1.0` and `loopgrid-mcp==0.1.0`. Re-run `uv lock --check` before pushing. This file is an audit snapshot and is not automatically enforced by `uvx`.
- No Python service-key credentials belong in the repository.

## Local checkpoint (PowerShell inside this directory)

```powershell
uv lock --check
python -m unittest discover -s tests -v
python -m compileall -q scripts examples
claude plugin validate --strict .
```

Inspect the included `uv.lock` and confirm `loopgrid-claude-launcher` version `0.1.0`, `loopgrid-mcp` version `0.1.0`, and registry hashes are present. If not, **stop**. Do not substitute the previous lockfile.

## Clean Claude Code MCP test

Start Claude Code from a separate temporary project folder, not the plugin source:

```powershell
$pluginDir = (Get-Location).Path
$testDir = Join-Path $env:TEMP 'loopgrid-verified-final-smoke'
New-Item -ItemType Directory -Force $testDir | Out-Null
Set-Location $testDir
$env:LOOPGRID_CLAUDE_MODE = 'off'
$env:LOOPGRID_BASE_URL = 'http://127.0.0.1:8000'
claude --plugin-dir $pluginDir
```

In `/mcp`, expect only `plugin:loopgrid:loopgrid` with **six tools**, with no project-level `CLAUDE_PLUGIN_ROOT` warning. To test a **real evidence write**, use your existing local Core in an isolated workspace and synthetic data. Do not execute refunds. Confirm Core verification is valid there; the historical `default` workspace's event 89 is known to fail verification. The offline bundle integrity check was previously validated with the older plugin; re-running after the new launcher is useful but not essential if the tool contracts are unchanged.

## Single GitHub update after checks pass

Only then copy this *complete* source tree, **including hidden `.claude-plugin` and `.github`**, into your existing cloned `loopgridio/loopgrid-claude-code` repository and commit once. Preserve the existing GitHub remote, CI, org and Directory draft; do not create a new submission. Before pushing, use `git status` and `git diff --check`; ensure no `*.pyc`, `.venv`, secrets or stale experimental files are staged.

In Anthropic's draft, click **Re-validate**; confirm the SHA changed from old `f2cb2de`. Inspect all holds; a pinned `uvx` and a lockfile **do not guarantee** automated clearance or Verified status. Keep **Claude Code** as the only listing surface. Complete Data handling accurately (current: `Reads and stores`, `Yes — listed in README`, `Longer`, `No`). Before ticking Compliance, resolve the declared lifecycle-hook wording and affirm the privacy statement applies to the real Core deployment. Keep auto-publish **off** while testing.

## Expected limitations

`uvx`'s dependency resolution and its initial inherited environment are **not controlled by the plugin's `uv.lock`**. `uv.lock` is review/audit data for this design. External network or registry supply chain must be trusted separately. Anthropic grants Verified at its discretion, not automatically when its scanner is quiet.
