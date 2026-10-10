#!/usr/bin/env python3
"""Read-only diagnosis for an existing LoopGrid decision's workspace chain.

Run: python examples/inspect_workspace_integrity.py dec_...
Only reads the verification endpoint; does not modify or repair ledger history.
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import loopgrid_hook as lg


def main():
    if len(sys.argv) != 2 or not sys.argv[1].startswith('dec_'):
        raise SystemExit('Usage: python examples/inspect_workspace_integrity.py dec_<id>')
    cfg = lg.config()
    report = lg._api(cfg, 'GET', f'/api/v1/decisions/{sys.argv[1]}/verify')
    print(json.dumps({
        'decisionId': sys.argv[1],
        'workspaceId': report.get('workspace_id'),
        'valid': report.get('valid'),
        'checkedEventsForDecision': report.get('checked_events'),
        'totalWorkspaceEvents': report.get('total_ledger_events'),
        'failureCount': len(report.get('failures', [])),
        'failures': report.get('failures', [])[:25],
        'keyId': report.get('key_id'),
    }, indent=2))
    if not report.get('valid'):
        raise SystemExit('INTEGRITY ALERT: Existing workspace verification failed; investigate failure reasons. Do not erase or rewrite evidence.')

if __name__ == '__main__':
    main()
