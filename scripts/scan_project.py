#!/usr/bin/env python3
"""Scan a SaaS app project to detect state and quality issues.

Analyzes app structure, component usage, form validation, animations, and images.
Detects what's been built, identifies quality gaps, and generates project state.

Usage:
    python scan_project.py --root /path/to/app [--output state.json]
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def scan_pages(root: str) -> dict:
    """Scan app/pages or src/pages directory for page files."""
    pages = {}
    page_dir = None

    # Check common locations
    for candidate in [
        os.path.join(root, 'app', 'pages'),
        os.path.join(root, 'pages'),
        os.path.join(root, 'src', 'pages'),
    ]:
        if os.path.isdir(candidate):
            page_dir = candidate
            break

    if not page_dir:
        return pages

    for root_dir, dirs, files in os.walk(page_dir):
        for file in files:
            if file.endswith(('.tsx', '.ts', '.jsx', '.js')):
                rel_path = os.path.relpath(os.path.join(root_dir, file), page_dir)
                page_id = rel_path.replace(os.sep, '/').replace('.tsx', '').replace('.ts', '').replace('.jsx', '').replace('.js', '')

                # Skip layout, error, loading files
                if any(x in page_id for x in ['layout', 'error', 'loading', '_app', '_document']):
                    continue

                file_path = os.path.join(root_dir, file)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                pages[page_id] = {
                    'path': file_path,
                    'content': content,
                    'route': '/' + page_id.replace('/page', '').replace('index', ''),
                }

    return pages


def extract_metadata(page_content: str) -> dict:
    """Extract tech usage from page content."""
    metadata = {
        'has_use_client': False,
        'has_framer_motion': False,
        'has_react_hook_form': False,
        'has_zod': False,
        'has_shadcn_components': [],
        'has_skeleton': False,
        'has_toast': False,
        'has_forms': False,
        'component_imports': [],
    }

    # Check for 'use client' directive
    if "'use client'" in page_content or '"use client"' in page_content:
        metadata['has_use_client'] = True

    # Check for framer-motion imports
    if 'framer-motion' in page_content or 'motion.' in page_content:
        metadata['has_framer_motion'] = True

    # Check for react-hook-form
    if 'react-hook-form' in page_content or 'useForm' in page_content:
        metadata['has_react_hook_form'] = True

    # Check for zod
    if 'from "zod"' in page_content or "from 'zod'" in page_content or 'z.object' in page_content:
        metadata['has_zod'] = True

    # Check for shadcn component imports
    shadcn_pattern = r'from\s+["\']@/components/ui/([a-z-]+)["\']'
    shadcn_matches = re.findall(shadcn_pattern, page_content)
    if shadcn_matches:
        metadata['has_shadcn_components'] = list(set(shadcn_matches))

    # Check for Skeleton component
    if 'Skeleton' in page_content:
        metadata['has_skeleton'] = True

    # Check for toast usage
    if 'useToast' in page_content or 'toast.' in page_content or 'Toast' in page_content:
        metadata['has_toast'] = True

    # Check for forms (form tags or form components)
    if '<form' in page_content or 'Form' in page_content or '<input' in page_content:
        metadata['has_forms'] = True

    # Extract component imports
    import_pattern = r'import\s+{([^}]+)}\s+from'
    imports = re.findall(import_pattern, page_content)
    for imp in imports:
        components = [c.strip() for c in imp.split(',')]
        metadata['component_imports'].extend(components)

    return metadata


def detect_issues(page_id: str, metadata: dict) -> list:
    """Detect quality issues based on page metadata."""
    issues = []

    # Check for missing Framer Motion animations
    if not metadata['has_framer_motion']:
        issues.append({
            'type': 'Quality: Missing animations',
            'severity': 'low',
            'message': f"{page_id}: No Framer Motion imports found. Consider adding page/component animations.",
        })

    # Check for forms without validation
    if metadata['has_forms'] and not metadata['has_zod']:
        issues.append({
            'type': 'Quality: Missing form validation',
            'severity': 'medium',
            'message': f"{page_id}: Contains forms but no Zod validation schema detected.",
        })

    # Check for missing loading states (Skeleton component)
    if not metadata['has_skeleton'] and ('fetch' in metadata['component_imports'] or 'api' in page_id.lower()):
        issues.append({
            'type': 'Quality: Missing loading states',
            'severity': 'medium',
            'message': f"{page_id}: No Skeleton component for loading states detected.",
        })

    # Check for missing toast notifications
    if 'form' in page_id.lower() and not metadata['has_toast']:
        issues.append({
            'type': 'Quality: Missing feedback',
            'severity': 'low',
            'message': f"{page_id}: No toast notifications found. Consider adding user feedback for actions.",
        })

    return issues


def scan_images(root: str) -> dict:
    """Scan for image files and their usage."""
    images = {}
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')

    # Common image directories
    image_dirs = [
        os.path.join(root, 'public'),
        os.path.join(root, 'public', 'images'),
        os.path.join(root, 'src', 'assets'),
        os.path.join(root, 'assets'),
    ]

    for img_dir in image_dirs:
        if not os.path.isdir(img_dir):
            continue

        for root_dir, dirs, files in os.walk(img_dir):
            for file in files:
                if file.lower().endswith(image_extensions):
                    file_path = os.path.join(root_dir, file)
                    rel_path = os.path.relpath(file_path, root)
                    file_size = os.path.getsize(file_path)

                    images[rel_path] = {
                        'size': file_size,
                        'type': os.path.splitext(file)[1].lower(),
                    }

    return images


def detect_existing_state(root: str, pages: dict, images: dict) -> dict:
    """Detect what's been built."""
    state = {
        'pages_built': [],
        'resources_implemented': [],
        'auth_implemented': False,
        'components_used': set(),
        'styling_framework': None,
        'animations_framework': None,
        'form_validation': False,
    }

    # Check pages
    for page_id, page_data in pages.items():
        metadata = extract_metadata(page_data['content'])

        page_info = {
            'id': page_id,
            'route': page_data['route'],
            'has_use_client': metadata['has_use_client'],
            'has_animations': metadata['has_framer_motion'],
            'has_form_validation': metadata['has_zod'],
            'has_loading_states': metadata['has_skeleton'],
            'shadcn_components': metadata['has_shadcn_components'],
        }

        state['pages_built'].append(page_info)

        # Track component usage
        for comp in metadata['has_shadcn_components']:
            state['components_used'].add(comp)

        # Detect auth
        if 'login' in page_id or 'auth' in page_id:
            state['auth_implemented'] = True

        # Track validation
        if metadata['has_zod']:
            state['form_validation'] = True

        # Detect animations framework
        if metadata['has_framer_motion']:
            state['animations_framework'] = 'framer-motion'

    # Check for styling
    if os.path.exists(os.path.join(root, 'tailwind.config.js')) or os.path.exists(os.path.join(root, 'tailwind.config.ts')):
        state['styling_framework'] = 'tailwindcss'

    state['components_used'] = list(state['components_used'])
    return state


def generate_state(root: str, pages: dict, images: dict, existing_state: dict) -> dict:
    """Generate comprehensive project state."""
    state = {
        'project_root': root,
        'metadata': {
            'detected_at': None,
            'total_pages': len(pages),
            'total_images': len(images),
        },
        'pages': [],
        'resources': [],
        'design_inputs': {
            'layout_preference': 'sidebar',
            'openapi_spec_path': None,
        },
        'audit': {
            'pages_complete': 0,
            'pages_in_progress': len(pages),
            'pages_pending': 0,
            'interactions_passed': False,
            'animations_present': existing_state.get('animations_framework') is not None,
            'validation_present': existing_state.get('form_validation', False),
        },
        'issues': [],
    }

    # Process pages
    for page_id, page_data in pages.items():
        metadata = extract_metadata(page_data['content'])
        page_issues = detect_issues(page_id, metadata)
        state['issues'].extend(page_issues)

        page_info = {
            'id': page_id,
            'route': page_data['route'],
            'page_type': 'list' if '-list' in page_id else ('detail' if '[id]' in page_id else 'dashboard'),
            'status': 'in_progress',
            'metadata': metadata,
        }
        state['pages'].append(page_info)

    # Check for resources from page routes
    resource_pattern = r'^/([a-z-]+)'
    resources_found = set()
    for page in state['pages']:
        match = re.match(resource_pattern, page['route'])
        if match:
            resource = match.group(1)
            if resource not in ['dashboard', 'settings', 'login', 'register']:
                resources_found.add(resource)

    for resource in sorted(resources_found):
        state['resources'].append({
            'name': resource,
            'endpoints': [],
            'schema': None,
        })

    # Determine interactions_passed based on quality checks
    total_issues = len(state['issues'])
    high_severity = sum(1 for i in state['issues'] if i.get('severity') == 'high')
    state['audit']['interactions_passed'] = high_severity == 0

    return state


def generate_manifest(state: dict, images: dict) -> dict:
    """Generate build manifest from state."""
    manifest = {
        'project': {
            'name': state['project_root'].split(os.sep)[-1],
            'pages': len(state['pages']),
            'resources': len(state['resources']),
        },
        'assets': {
            'images': len(images),
            'total_size': sum(img['size'] for img in images.values()),
        },
        'build_status': {
            'pages_complete': state['audit']['pages_complete'],
            'pages_in_progress': state['audit']['pages_in_progress'],
            'pages_pending': state['audit']['pages_pending'],
        },
        'quality': {
            'animations': state['audit']['animations_present'],
            'validation': state['audit']['validation_present'],
            'interactions_passed': state['audit']['interactions_passed'],
            'total_issues': len(state['issues']),
        },
    }

    return manifest


def main():
    parser = argparse.ArgumentParser(description='Scan SaaS app project structure and state')
    parser.add_argument('--root', required=True, help='Project root directory')
    parser.add_argument('--output', default='project-state.json', help='Output state file path')
    args = parser.parse_args()

    if not os.path.isdir(args.root):
        print(f"Error: Root directory not found: {args.root}", file=sys.stderr)
        sys.exit(1)

    print(f"=== Scanning Project: {args.root} ===\n")

    # Scan project
    pages = scan_pages(args.root)
    images = scan_images(args.root)

    print(f"Pages found: {len(pages)}")
    print(f"Images found: {len(images)}")

    # Detect existing state
    existing_state = detect_existing_state(args.root, pages, images)
    print(f"Auth implemented: {existing_state['auth_implemented']}")
    print(f"Form validation: {existing_state['form_validation']}")
    print(f"Animations: {existing_state['animations_framework']}")

    # Generate state
    state = generate_state(args.root, pages, images, existing_state)

    # Generate manifest
    manifest = generate_manifest(state, images)

    # Write output
    output_data = {
        'state': state,
        'manifest': manifest,
    }

    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\nState written: {args.output}")
    print(f"  Pages: {state['metadata']['total_pages']}")
    print(f"  Resources: {len(state['resources'])}")
    print(f"  Quality issues: {len(state['issues'])}")

    if state['issues']:
        print("\nTop issues:")
        for issue in state['issues'][:5]:
            print(f"  [{issue['severity']}] {issue['type']}: {issue['message']}")


if __name__ == '__main__':
    main()
