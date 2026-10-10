#!/usr/bin/env python3
"""List local hook records requiring operator attention (no automatic retries)."""
from __future__ import annotations
from pathlib import Path
import sqlite3
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from loopgrid_hook import config


def main():
    path = config()["state"]
    if not path.exists():
        print("No local hook ledger exists yet.")
        return 0
    with sqlite3.connect(str(path)) as db:
        for decision, status, tool in db.execute("SELECT decision_id,status,tool FROM calls WHERE status IN ('needs_reconciliation','capture_failed','pending','created','authorized','observed') ORDER BY rowid DESC LIMIT 100"):
            print(f"decision={decision or '<unavailable>'}  state={status}  tool={tool}")
    print("Never retry business actions solely to repair evidence. Investigate downstream state first.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
