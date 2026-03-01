#!/usr/bin/env python3
"""Parse an OpenAPI 3.x specification and generate a SaaS app project plan.

Reads an OpenAPI spec (YAML or JSON), extracts resources, endpoints, and schemas,
then generates a project-plan.json suitable for the state manager.

Usage:
    python parse_openapi.py --spec openapi-spec.yaml --output app-plan.json \
        [--accent-color "#2563eb"] [--font "modern"] [--layout "sidebar"]

Dependencies: pyyaml (pip install pyyaml --break-system-packages)
"""

import argparse
import json
import os
import re
import sys


def load_spec(path: str) -> dict:
    """Load an OpenAPI spec from YAML or JSON."""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Try JSON first
    try:
        return json.loads(content)
    except (json.JSONDecodeError, ValueError):
        pass

    # Try YAML
    try:
        import yaml
        return yaml.safe_load(content)
    except ImportError:
        print("Error: PyYAML is required for YAML specs. Install: pip install pyyaml --break-system-packages", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing spec: {e}", file=sys.stderr)
        sys.exit(1)


def extract_resources(spec: dict) -> dict:
    """Group endpoints by resource (first path segment)."""
    resources = {}
    paths = spec.get('paths', {})

    for path, methods in paths.items():
        # Extract resource name from path (e.g., /users/{id} -> users)
        parts = [p for p in path.strip('/').split('/') if not p.startswith('{')]
        if not parts:
            continue
        resource_name = parts[0]

        if resource_name not in resources:
            resources[resource_name] = {
                'name': resource_name,
                'endpoints': [],
                'has_list': False,
                'has_detail': False,
                'has_create': False,
                'has_update': False,
                'has_delete': False,
                'schema': None,
            }

        res = resources[resource_name]
        is_detail = '{' in path  # Has path parameter = detail endpoint

        for method, operation in methods.items():
            if method.lower() in ('get', 'post', 'put', 'patch', 'delete'):
                endpoint_str = f"{method.upper()} {path}"
                res['endpoints'].append(endpoint_str)

                m = method.lower()
                if m == 'get' and not is_detail:
                    res['has_list'] = True
                elif m == 'get' and is_detail:
                    res['has_detail'] = True
                elif m == 'post':
                    res['has_create'] = True
                elif m in ('put', 'patch'):
                    res['has_update'] = True
                elif m == 'delete':
                    res['has_delete'] = True

                # Try to find associated schema
                if not res['schema']:
                    schema_ref = None
                    if m == 'get' and not is_detail:
                        # List endpoint - check response
                        resp = operation.get('responses', {}).get('200', {})
                        content = resp.get('content', {}).get('application/json', {})
                        schema = content.get('schema', {})
                        if schema.get('type') == 'array':
                            schema_ref = schema.get('items', {}).get('$ref', '')
                        elif '$ref' in schema:
                            schema_ref = schema['$ref']
                    elif m == 'post':
                        # Create endpoint - check request body
                        rb = operation.get('requestBody', {}).get('content', {}).get('application/json', {})
                        schema_ref = rb.get('schema', {}).get('$ref', '')

                    if schema_ref and '/' in schema_ref:
                        res['schema'] = schema_ref.split('/')[-1]

    return resources


def extract_schemas(spec: dict) -> dict:
    """Extract component schemas."""
    schemas = {}
    components = spec.get('components', {}).get('schemas', {})
    for name, schema in components.items():
        schemas[name] = {
            'name': name,
            'type': schema.get('type', 'object'),
            'properties': list(schema.get('properties', {}).keys()),
            'required': schema.get('required', []),
            'has_enums': any(
                'enum' in prop
                for prop in schema.get('properties', {}).values()
            ),
        }
    return schemas


def extract_security(spec: dict) -> str:
    """Detect authentication type from security schemes."""
    schemes = spec.get('components', {}).get('securitySchemes', {})
    if not schemes:
        return 'none'

    for name, scheme in schemes.items():
        scheme_type = scheme.get('type', '')
        if scheme_type == 'http' and scheme.get('scheme') == 'bearer':
            return 'jwt'
        elif scheme_type == 'oauth2':
            return 'oauth2'
        elif scheme_type == 'apiKey':
            return 'api-key'
        elif scheme_type == 'http':
            return 'basic'

    return 'unknown'


def generate_plan(spec: dict, resources: dict, schemas: dict,
                  auth_type: str, accent_color: str, font: str, layout: str) -> dict:
    """Generate a project plan from parsed spec data."""
    info = spec.get('info', {})
    project_name = re.sub(r'[^a-z0-9-]', '-', info.get('title', 'my-saas-app').lower()).strip('-')

    font_map = {
        'modern': ('Inter', 'Inter'),
        'elegant': ('Playfair Display', 'Inter'),
        'bold': ('Plus Jakarta Sans', 'Plus Jakarta Sans'),
        'minimal': ('Geist', 'Geist'),
    }
    heading_font, body_font = font_map.get(font, (font, font))

    plan = {
        'project_name': project_name,
        'site_name': info.get('title', 'My App'),
        'site_description': info.get('description', ''),
        'api_spec': {
            'title': info.get('title', ''),
            'version': info.get('version', '1.0.0'),
            'base_url': '',
        },
        'design_system': {
            '_note': 'Auto-generated from design_inputs',
            'primary': accent_color,
            'primary_foreground': '#ffffff',
            'secondary': '#93a3d1',
            'background': '#ffffff',
            'foreground': '#0a0a0a',
            'muted': '#6b7280',
            'muted_background': '#f3f4f6',
            'border': '#e5e7eb',
            'destructive': '#ef4444',
            'font_heading': heading_font,
            'font_body': body_font,
            'border_radius': '0.5rem',
            'layout': layout,
        },
        'resources': [],
        'pages': [],
        'build_order': ['layout'],
        'shared_components': [
            {'name': 'AppShell', 'description': 'Main layout wrapper with sidebar/topnav and content area'},
            {'name': 'DataTable', 'description': 'Reusable data table with sort, search, filter, pagination'},
            {'name': 'PageTransition', 'description': 'Framer Motion AnimatePresence wrapper'},
            {'name': 'EmptyState', 'description': 'Empty state component with illustration, message, and CTA'},
            {'name': 'LoadingSkeleton', 'description': 'Skeleton loading screens for different page types'},
        ],
    }

    # Extract base URL from servers
    servers = spec.get('servers', [])
    if servers:
        plan['api_spec']['base_url'] = servers[0].get('url', '')

    # Dashboard page (always first)
    plan['pages'].append({
        'id': 'dashboard',
        'route': '/dashboard',
        'title': 'Dashboard',
        'page_type': 'dashboard',
        'resource': None,
        'endpoints': [],
        'components': ['StatCards', 'RecentActivity', 'Charts'],
        'priority': 'high',
        'description': 'Overview dashboard with stats and recent activity',
    })
    plan['build_order'].append('dashboard')

    # Resource pages
    for res_name, res_data in resources.items():
        plan['resources'].append({
            'name': res_name,
            'endpoints': res_data['endpoints'],
            'schema': res_data['schema'],
        })

        # List page
        if res_data['has_list']:
            page_id = f"{res_name}-list"
            components = ['DataTable', 'SearchFilter', 'Pagination']
            if res_data['has_create']:
                components.append('CreateDialog')

            plan['pages'].append({
                'id': page_id,
                'route': f"/{res_name}",
                'title': res_name.replace('-', ' ').replace('_', ' ').title(),
                'page_type': 'list',
                'resource': res_name,
                'endpoints': [e for e in res_data['endpoints'] if 'GET' in e and '{' not in e],
                'components': components,
                'priority': 'high',
                'description': f"{res_name.title()} list with search, filter, and CRUD operations",
            })
            plan['build_order'].append(page_id)

        # Detail page
        if res_data['has_detail']:
            page_id = f"{res_name}-detail"
            components = ['DetailCard', 'TabbedSections']
            if res_data['has_update']:
                components.append('EditSheet')
            if res_data['has_delete']:
                components.append('DeleteDialog')

            plan['pages'].append({
                'id': page_id,
                'route': f"/{res_name}/[id]",
                'title': f"{res_name.replace('-', ' ').replace('_', ' ').title()} Detail",
                'page_type': 'detail',
                'resource': res_name,
                'endpoints': [e for e in res_data['endpoints'] if '{' in e],
                'components': components,
                'priority': 'high',
                'description': f"{res_name.title()} detail view with edit and delete",
            })
            plan['build_order'].append(page_id)

    # Auth pages
    if auth_type != 'none':
        plan['pages'].append({
            'id': 'login',
            'route': '/login',
            'title': 'Login',
            'page_type': 'auth',
            'resource': None,
            'endpoints': [],
            'components': ['LoginForm'],
            'priority': 'medium',
            'description': f"Login page ({auth_type} authentication)",
        })
        plan['build_order'].append('login')

        if auth_type in ('jwt', 'oauth2'):
            plan['pages'].append({
                'id': 'register',
                'route': '/register',
                'title': 'Register',
                'page_type': 'auth',
                'resource': None,
                'endpoints': [],
                'components': ['RegisterForm'],
                'priority': 'low',
                'description': 'Registration page',
            })
            plan['build_order'].append('register')

    # Settings page
    plan['pages'].append({
        'id': 'settings',
        'route': '/settings',
        'title': 'Settings',
        'page_type': 'settings',
        'resource': None,
        'endpoints': [],
        'components': ['SettingsForm', 'DangerZone'],
        'priority': 'low',
        'description': 'Application settings',
    })
    plan['build_order'].append('settings')

    return plan


def main():
    parser = argparse.ArgumentParser(description='Parse OpenAPI spec and generate SaaS app plan')
    parser.add_argument('--spec', required=True, help='Path to OpenAPI spec (YAML or JSON)')
    parser.add_argument('--output', default='app-plan.json', help='Output plan file path')
    parser.add_argument('--accent-color', default='#2563eb', help='Brand accent color')
    parser.add_argument('--font', default='modern', help='Font preference')
    parser.add_argument('--layout', default='sidebar', help='Layout preference (sidebar, topnav, minimal)')
    args = parser.parse_args()

    if not os.path.exists(args.spec):
        print(f"Error: Spec file not found: {args.spec}", file=sys.stderr)
        sys.exit(1)

    print(f"=== Parsing OpenAPI Spec: {args.spec} ===\n")

    spec = load_spec(args.spec)

    # Validate it looks like an OpenAPI spec
    if 'openapi' not in spec and 'swagger' not in spec:
        print("Warning: File doesn't appear to be an OpenAPI spec (no 'openapi' or 'swagger' field)")

    info = spec.get('info', {})
    print(f"API: {info.get('title', 'Unknown')} v{info.get('version', '?')}")

    resources = extract_resources(spec)
    schemas = extract_schemas(spec)
    auth_type = extract_security(spec)

    print(f"Resources: {len(resources)}")
    for name, res in resources.items():
        ops = []
        if res['has_list']: ops.append('List')
        if res['has_detail']: ops.append('Detail')
        if res['has_create']: ops.append('Create')
        if res['has_update']: ops.append('Update')
        if res['has_delete']: ops.append('Delete')
        print(f"  {name}: {', '.join(ops)} (schema: {res['schema'] or 'none'})")

    print(f"Schemas: {len(schemas)}")
    for name, schema in schemas.items():
        print(f"  {name}: {len(schema['properties'])} properties")

    print(f"Auth: {auth_type}")

    plan = generate_plan(spec, resources, schemas, auth_type,
                         args.accent_color, args.font, args.layout)

    with open(args.output, 'w') as f:
        json.dump(plan, f, indent=2)

    print(f"\nPlan written: {args.output}")
    print(f"  Pages: {len(plan['pages'])}")
    print(f"  Build order: {' -> '.join(plan['build_order'])}")


if __name__ == '__main__':
    main()
