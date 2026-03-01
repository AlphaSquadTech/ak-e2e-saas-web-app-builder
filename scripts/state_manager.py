#!/usr/bin/env python3
"""Session-agnostic state manager for the NextJS SaaS App Builder skill.

Manages the .nextjs-builder-state.json file that persists build progress across sessions.
Every action reads the current state, modifies it, and writes it back atomically.

Usage:
    python state_manager.py --action <action> [options]

Actions:
    init              Initialize state from a project plan
    set-phase         Update the current phase
    update-page       Update a page's status
    add-verification  Add a verification log entry for a page
    log               Add a session log entry
    add-issue         Add an issue
    resolve-issue     Mark an issue as resolved
    next-page         Print the next pending page
    summary           Print a status summary

Examples:
    python state_manager.py --action init --plan project-plan.json --output .nextjs-builder-state.json
    python state_manager.py --action set-phase --phase build
    python state_manager.py --action update-page --page-id home --status verified
    python state_manager.py --action add-verification --page-id home --result pass --screenshot screenshots/home.png --notes "Looks good"
    python state_manager.py --action log --message "Implemented homepage hero section"
    python state_manager.py --action add-issue --page-id home --severity minor --description "Spacing issue on mobile"
    python state_manager.py --action next-page
    python state_manager.py --action summary
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone


DEFAULT_STATE_FILE = '.nextjs-builder-state.json'


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def read_state(path: str) -> dict:
    if not os.path.exists(path):
        print(f"Error: State file not found: {path}", file=sys.stderr)
        print(f"Run with --action init first.", file=sys.stderr)
        sys.exit(1)
    with open(path, 'r') as f:
        return json.load(f)


def write_state(path: str, state: dict):
    state['last_updated'] = now_iso()
    # Atomic write: write to temp file, then rename
    tmp_path = path + '.tmp'
    with open(tmp_path, 'w') as f:
        json.dump(state, f, indent=2, default=str)
    os.replace(tmp_path, path)


def action_init(args):
    """Initialize state from a project plan."""
    if not args.plan:
        print("Error: --plan is required for init action", file=sys.stderr)
        sys.exit(1)

    with open(args.plan, 'r') as f:
        plan = json.load(f)

    output = args.output or DEFAULT_STATE_FILE

    # Build pages array from plan
    pages = []
    for page_def in plan.get('pages', []):
        pages.append({
            'id': page_def.get('id', page_def.get('route', '').strip('/') or 'home'),
            'route': page_def.get('route', '/'),
            'title': page_def.get('title', ''),
            'page_type': page_def.get('page_type', 'list'),
            'resource': page_def.get('resource', None),
            'endpoints': page_def.get('endpoints', []),
            'components': page_def.get('components', []),
            'content_source': page_def.get('content_source', ''),
            'status': 'pending',
            'priority': page_def.get('priority', 'medium'),
            'iteration': 0,
            'screenshots': [],
            'verification_log': [],
        })

    state = {
        'version': '1.0.0',
        'project_name': plan.get('project_name', plan.get('app_name', 'unnamed')),
        'source_documents': plan.get('source_documents', []),
        'created_at': now_iso(),
        'last_updated': now_iso(),
        'current_phase': 'scaffold',
        'plan': plan,
        'pages': pages,
        'shared_components': [],
        'session_log': [
            {
                'session_id': str(uuid.uuid4())[:8],
                'started_at': now_iso(),
                'ended_at': None,
                'actions': ['Initialized state from plan'],
            }
        ],
        'issues': [],
        'audit': {
            'interactions_passed': False,
            'accessibility_passed': False,
            'responsive_passed': False,
            'performance_passed': False,
            'completed_at': None,
        },
    }

    write_state(output, state)
    print(f"State initialized: {output}")
    print(f"  Project: {state['project_name']}")
    print(f"  Pages: {len(pages)}")
    print(f"  Phase: {state['current_phase']}")


def action_set_phase(args):
    """Set the current phase."""
    state = read_state(args.state_file)
    old_phase = state['current_phase']
    state['current_phase'] = args.phase

    # Log the transition
    if state['session_log']:
        state['session_log'][-1]['actions'].append(f"Phase: {old_phase} -> {args.phase}")

    write_state(args.state_file, state)
    print(f"Phase updated: {old_phase} -> {args.phase}")


def action_update_page(args):
    """Update a page's status."""
    state = read_state(args.state_file)

    for page in state['pages']:
        if page['id'] == args.page_id:
            old_status = page['status']
            new_status = args.status

            # ENFORCEMENT: Cannot mark as "verified" without a verification entry
            # that includes a screenshot. This prevents skipping visual verification.
            if new_status == 'verified':
                has_valid_verification = False
                for entry in page.get('verification_log', []):
                    if entry.get('result') == 'pass' and entry.get('screenshot'):
                        has_valid_verification = True
                        break

                if not has_valid_verification:
                    print(
                        f"ERROR: Cannot mark '{args.page_id}' as verified — "
                        f"no passing verification with screenshot found.\n"
                        f"  Run visual verification first:\n"
                        f"    bash <skill-path>/scripts/verify_page.sh {page.get('route', '/')} {args.page_id}\n"
                        f"  Then record the result:\n"
                        f"    python state_manager.py --action add-verification "
                        f"--page-id {args.page_id} --result pass "
                        f"--screenshot screenshots/{args.page_id}-v1-full.png "
                        f"--notes 'description'",
                        file=sys.stderr
                    )
                    sys.exit(1)

            page['status'] = new_status
            if args.notes:
                page['verification_log'].append({
                    'timestamp': now_iso(),
                    'iteration': page['iteration'],
                    'result': 'pass' if new_status == 'verified' else 'info',
                    'notes': args.notes,
                })

            if state['session_log']:
                state['session_log'][-1]['actions'].append(
                    f"Page '{args.page_id}': {old_status} -> {new_status}"
                )

            write_state(args.state_file, state)
            print(f"Page '{args.page_id}': {old_status} -> {new_status}")
            return

    print(f"Error: Page '{args.page_id}' not found", file=sys.stderr)
    sys.exit(1)


def action_add_verification(args):
    """Add a verification log entry."""
    state = read_state(args.state_file)

    for page in state['pages']:
        if page['id'] == args.page_id:
            page['iteration'] += 1
            entry = {
                'timestamp': now_iso(),
                'iteration': page['iteration'],
                'result': args.result,
                'screenshot': args.screenshot or '',
                'notes': args.notes or '',
            }
            page['verification_log'].append(entry)

            if args.screenshot:
                page['screenshots'].append(args.screenshot)

            # Auto-update status based on result
            if args.result == 'pass':
                page['status'] = 'verified'
            elif args.result == 'fail' and page['iteration'] >= 3:
                page['status'] = 'needs-review'
            elif args.result == 'fail':
                page['status'] = 'in-progress'

            if state['session_log']:
                state['session_log'][-1]['actions'].append(
                    f"Verified '{args.page_id}': {args.result} (iteration {page['iteration']})"
                )

            write_state(args.state_file, state)
            print(f"Verification added for '{args.page_id}': {args.result} (iteration {page['iteration']})")
            return

    print(f"Error: Page '{args.page_id}' not found", file=sys.stderr)
    sys.exit(1)


def action_log(args):
    """Add a session log entry."""
    state = read_state(args.state_file)

    if not state['session_log'] or state['session_log'][-1].get('ended_at'):
        # Start new session
        state['session_log'].append({
            'session_id': str(uuid.uuid4())[:8],
            'started_at': now_iso(),
            'ended_at': None,
            'actions': [args.message],
        })
    else:
        state['session_log'][-1]['actions'].append(args.message)

    write_state(args.state_file, state)
    print(f"Logged: {args.message}")


def action_add_issue(args):
    """Add an issue."""
    state = read_state(args.state_file)
    state['issues'].append({
        'page_id': args.page_id or 'general',
        'severity': args.severity or 'minor',
        'description': args.description,
        'resolved': False,
        'created_at': now_iso(),
    })
    write_state(args.state_file, state)
    print(f"Issue added: [{args.severity}] {args.description}")


def action_resolve_issue(args):
    """Resolve an issue by index."""
    state = read_state(args.state_file)
    idx = int(args.issue_index)
    unresolved = [i for i, issue in enumerate(state['issues']) if not issue['resolved']]
    if idx < 0 or idx >= len(unresolved):
        print(f"Error: Issue index {idx} out of range (0-{len(unresolved)-1})", file=sys.stderr)
        sys.exit(1)
    state['issues'][unresolved[idx]]['resolved'] = True
    state['issues'][unresolved[idx]]['resolved_at'] = now_iso()
    write_state(args.state_file, state)
    print(f"Issue {idx} resolved")


def action_next_page(args):
    """Print the next page to work on."""
    state = read_state(args.state_file)

    # Check build order from plan
    build_order = state.get('plan', {}).get('build_order', [])
    page_map = {p['id']: p for p in state['pages']}

    # First check in-progress pages
    for page in state['pages']:
        if page['status'] == 'in-progress':
            print(json.dumps(page, indent=2))
            return

    # Then follow build order for pending pages
    if build_order:
        for page_id in build_order:
            if page_id in page_map and page_map[page_id]['status'] == 'pending':
                print(json.dumps(page_map[page_id], indent=2))
                return

    # Fallback: first pending page by priority
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    pending = [p for p in state['pages'] if p['status'] == 'pending']
    pending.sort(key=lambda p: priority_order.get(p.get('priority', 'medium'), 1))

    if pending:
        print(json.dumps(pending[0], indent=2))
    else:
        print("All pages complete!")


def action_summary(args):
    """Print a status summary."""
    state = read_state(args.state_file)

    print(f"Project: {state['project_name']}")
    print(f"Phase: {state['current_phase']}")
    print(f"Last updated: {state['last_updated']}")
    print()

    # Page status counts
    status_counts = {}
    for page in state['pages']:
        s = page['status']
        status_counts[s] = status_counts.get(s, 0) + 1

    total = len(state['pages'])
    verified = status_counts.get('verified', 0)
    print(f"Pages: {verified}/{total} verified")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")

    # Unresolved issues
    unresolved = [i for i in state['issues'] if not i['resolved']]
    if unresolved:
        print(f"\nUnresolved issues: {len(unresolved)}")
        for i, issue in enumerate(unresolved):
            print(f"  [{i}] [{issue['severity']}] {issue['page_id']}: {issue['description']}")

    # Audit status
    audit = state.get('audit', {})
    if state['current_phase'] in ('audit', 'complete'):
        print(f"\nAudit:")
        print(f"  Interactions: {'PASS' if audit.get('interactions_passed') else 'PENDING'}")
        print(f"  Accessibility: {'PASS' if audit.get('accessibility_passed') else 'PENDING'}")
        print(f"  Responsive: {'PASS' if audit.get('responsive_passed') else 'PENDING'}")
        print(f"  Performance: {'PASS' if audit.get('performance_passed') else 'PENDING'}")

    # Sessions
    print(f"\nSessions: {len(state['session_log'])}")


def action_verify_all(args):
    """List all pages that need verification."""
    state = read_state(args.state_file)

    needs_verification = []
    for page in state['pages']:
        if page['status'] in ('implemented', 'in-progress', 'pending'):
            needs_verification.append(page)
        elif page['status'] == 'needs-review':
            needs_verification.append(page)

    if not needs_verification:
        print("All pages are verified or not yet implemented!")
        return

    print(f"Pages needing verification ({len(needs_verification)}):\n")
    for page in needs_verification:
        route = page.get('route', '/')
        iterations = page.get('iteration', 0)
        print(f"  [{page['status']:14s}] {page['id']:20s} {route}")
        print(f"    bash <skill-path>/scripts/verify_page.sh {route} {page['id']}")
        if iterations > 0:
            print(f"    (previously attempted {iterations} time(s))")
        print()


def main():
    parser = argparse.ArgumentParser(description='NextJS SaaS App Builder State Manager')
    parser.add_argument('--action', required=True,
                        choices=['init', 'set-phase', 'update-page', 'add-verification',
                                 'log', 'add-issue', 'resolve-issue', 'next-page', 'summary',
                                 'verify-all'])
    parser.add_argument('--state-file', default=DEFAULT_STATE_FILE,
                        help=f'Path to state file (default: {DEFAULT_STATE_FILE})')

    # Init options
    parser.add_argument('--plan', help='Path to project plan JSON (for init)')
    parser.add_argument('--output', help='Output state file path (for init)')

    # Phase options
    parser.add_argument('--phase', help='Phase name (for set-phase)')

    # Page options
    parser.add_argument('--page-id', help='Page identifier')
    parser.add_argument('--status', help='New status for the page')

    # Verification options
    parser.add_argument('--result', choices=['pass', 'fail'], help='Verification result')
    parser.add_argument('--screenshot', help='Screenshot path')
    parser.add_argument('--notes', help='Notes or description')

    # Log options
    parser.add_argument('--message', help='Log message')

    # Issue options
    parser.add_argument('--severity', choices=['minor', 'major', 'critical'], help='Issue severity')
    parser.add_argument('--description', help='Issue description')
    parser.add_argument('--issue-index', help='Issue index to resolve')

    args = parser.parse_args()

    actions = {
        'init': action_init,
        'set-phase': action_set_phase,
        'update-page': action_update_page,
        'add-verification': action_add_verification,
        'log': action_log,
        'add-issue': action_add_issue,
        'resolve-issue': action_resolve_issue,
        'next-page': action_next_page,
        'summary': action_summary,
        'verify-all': action_verify_all,
    }

    actions[args.action](args)


if __name__ == '__main__':
    main()
