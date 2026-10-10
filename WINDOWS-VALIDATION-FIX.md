# Windows validation follow-up (SQLite lock and Claude Code CLI)

This document accompanies the October 10 plugin validation patch. It **does not** change the policy or event authorization logic.

## 1. Apply the small patch to the existing candidate

From the directory that contains `scripts/`, `tests/`, and `.claude-plugin/`:

```powershell
Expand-Archive -LiteralPath "$HOME\Downloads\loopgrid-claude-code-plugin-v0.1.0-WINDOWS-FIX-PATCH.zip" -DestinationPath . -Force
python -m unittest discover -s tests -v
python -m compileall -q scripts examples
```

Expected: `Ran 40 tests` and `OK`. The correction closes SQLite connections even when database initialization raises in a concurrent thread, preventing a leaked handle from blocking Windows temporary-directory cleanup. Confirmed on Windows: 40/40 tests passed on October 10, 2026.

## 2. Install the standalone Claude Code CLI

The `claude-agent-sdk` pip package does not install the separate Claude Code CLI. Official Windows install choice:

```powershell
winget install Anthropic.ClaudeCode
```

Close and reopen PowerShell so PATH refreshes, then, from the plugin root:

```powershell
claude --version
claude plugin validate .
```

Plugin validation checks the local manifest, skills/hooks wiring and requires **no model/API credits**. Actual interactive Claude sessions, MCP discovery and hook lifecycle remain separate tests that require Claude Code account access.

## 3. Real Core without an Anthropic model request

With the local LoopGrid Core running:

```powershell
python examples\core_sandbox_e2e.py
```

This validates deterministic inputs and Core evidence only, not real Claude Code dispatch. Do not submit the plugin to Anthropic until native CLI validation and runtime behavior are tested.

## 4. Isolated Core verification and older-workspace diagnosis

The original Core test used the shared `default` workspace. Core's decision verification checks **every** event in that decision's workspace chain, so unrelated older or invalid records can make a newly completed decision fail verification.

The corrected example creates a new development test workspace with its own active sandbox policy, rather than modifying the existing workspace. With local Core running, execute:

```powershell
python examples\core_sandbox_e2e.py
```

For the previously reported failing decision, first inspect its **existing** workspace in read-only mode:

```powershell
python examples\inspect_workspace_integrity.py dec_2a379ca7daac40f2a7771e9d
```

The diagnostic prints Core's failure reasons. It does not delete or repair events. If the new isolated workspace passes but the original does not, investigate the historical chain/key problem separately; do **not** declare the original chain verified. If the new workspace fails too, share the `verificationFailures` list.

The example requires permission to create a development workspace and a policy. It refuses remote Core hosts and does not call Anthropic or payment APIs.
