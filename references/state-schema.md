# State Tracking Schema for SaaS Builder

The state file (`.nextjs-builder-state.json`) lives in the project root and tracks all progress.
It is the single source of truth for what has been done and what remains. Always read it at the
start of a session and update it after every meaningful action.

## Complete Schema

```json
{
  "version": "1.0.0",
  "project_name": "my-saas-app",
  "source_documents": [
    {
      "path": "requirements.md",
      "type": "markdown",
      "extracted_at": "2026-02-28T10:00:00Z"
    }
  ],
  "created_at": "2026-02-28T10:00:00Z",
  "last_updated": "2026-02-28T14:30:00Z",
  "current_phase": "build",
  "design_inputs": {
    "accent_color": "#2563eb",
    "accent_color_source": "user",
    "font_preference": "modern",
    "font_preference_source": "user",
    "layout_preference": "sidebar-layout",
    "layout_preference_source": "user",
    "openapi_spec_path": "spec/api.yaml",
    "gemini_api_key": "AIza...",
    "gemini_api_key_source": "user"
  },
  "plan": {
    "app_name": "Acme Dashboard",
    "app_description": "Team collaboration and analytics platform",
    "target_audience": "Product managers and team leads",
    "api_spec": {
      "path": "spec/api.yaml",
      "title": "Acme API",
      "version": "v1",
      "base_url": "http://localhost:3001/api"
    },
    "design_system": {
      "primary": "#2563eb",
      "primary_foreground": "#ffffff",
      "secondary": "#93a3d1",
      "background": "#ffffff",
      "foreground": "#0a0a0a",
      "muted": "#6b7280",
      "muted_background": "#f3f4f6",
      "border": "#e5e7eb",
      "destructive": "#ef4444",
      "font_heading": "Inter",
      "font_body": "Inter",
      "border_radius": "0.5rem",
      "derived_from": "accent_color=#2563eb, font_preference=modern"
    },
    "build_order": ["layout", "dashboard", "users", "settings", "analytics"]
  },
  "pages": [
    {
      "id": "dashboard",
      "route": "/dashboard",
      "title": "Dashboard — Acme",
      "page_type": "dashboard",
      "resource": "dashboard",
      "endpoints": [
        "GET /api/stats",
        "GET /api/recent-activity",
        "GET /api/chart-data"
      ],
      "components": ["DashboardHeader", "StatCards", "RecentActivity", "ChartWidget"],
      "content_source": "requirements.md#dashboard",
      "status": "verified",
      "priority": "high",
      "iteration": 2,
      "screenshots": [
        "screenshots/dashboard-v1.png",
        "screenshots/dashboard-v2.png"
      ],
      "verification_log": [
        {
          "timestamp": "2026-02-28T11:30:00Z",
          "iteration": 1,
          "result": "fail",
          "screenshot": "screenshots/dashboard-v1.png",
          "notes": "Stat cards misaligned. Chart not rendering. Sidebar collapse button missing."
        },
        {
          "timestamp": "2026-02-28T12:00:00Z",
          "iteration": 2,
          "result": "pass",
          "screenshot": "screenshots/dashboard-v2.png",
          "notes": "All components properly aligned. Chart visible. Sidebar functional."
        }
      ]
    },
    {
      "id": "users",
      "route": "/users",
      "title": "Users — Acme",
      "page_type": "list",
      "resource": "users",
      "endpoints": [
        "GET /api/users",
        "DELETE /api/users/{id}"
      ],
      "components": ["UsersTable", "SearchBar", "FilterBar", "Pagination"],
      "content_source": "requirements.md#users",
      "status": "in-progress",
      "priority": "high",
      "iteration": 0,
      "screenshots": [],
      "verification_log": []
    },
    {
      "id": "user-detail",
      "route": "/users/:id",
      "title": "User Details — Acme",
      "page_type": "detail",
      "resource": "user",
      "endpoints": [
        "GET /api/users/{id}",
        "PUT /api/users/{id}"
      ],
      "components": ["UserForm", "ActivityLog", "RelatedData"],
      "content_source": "requirements.md#user-detail",
      "status": "pending",
      "priority": "high",
      "iteration": 0,
      "screenshots": [],
      "verification_log": []
    },
    {
      "id": "settings",
      "route": "/settings",
      "title": "Settings — Acme",
      "page_type": "settings",
      "resource": "settings",
      "endpoints": [
        "GET /api/settings",
        "PUT /api/settings"
      ],
      "components": ["SettingsForm", "DangerZone"],
      "content_source": "requirements.md#settings",
      "status": "pending",
      "priority": "medium",
      "iteration": 0,
      "screenshots": [],
      "verification_log": []
    }
  ],
  "shared_components": [
    {
      "name": "Header",
      "status": "verified",
      "file": "components/header.tsx"
    },
    {
      "name": "Sidebar",
      "status": "verified",
      "file": "components/sidebar.tsx"
    },
    {
      "name": "Layout",
      "status": "verified",
      "file": "components/layout.tsx"
    }
  ],
  "session_log": [
    {
      "session_id": "abc123",
      "started_at": "2026-02-28T10:00:00Z",
      "ended_at": "2026-02-28T12:30:00Z",
      "actions": [
        "Parsed requirements.md",
        "Generated plan with API spec",
        "Scaffolded Next.js project with sidebar layout",
        "Implemented and verified dashboard page"
      ]
    },
    {
      "session_id": "def456",
      "started_at": "2026-02-28T14:00:00Z",
      "ended_at": null,
      "actions": [
        "Resumed from state file",
        "Started implementing users list page"
      ]
    }
  ],
  "issues": [
    {
      "page_id": "dashboard",
      "severity": "minor",
      "description": "Chart tooltip positioning off-screen on small devices",
      "resolved": false
    }
  ],
  "image_manifest": {
    "path": "image-manifest.json",
    "total_images": 8,
    "generated": 5,
    "placeholders": 3,
    "failed": 0,
    "last_generated_at": "2026-02-28T15:30:00Z"
  },
  "audit": {
    "interactions_passed": false,
    "accessibility_passed": false,
    "responsive_passed": false,
    "performance_passed": false,
    "completed_at": null
  }
}
```

## Status Values

### Page Status
| Status | Meaning |
|--------|---------|
| `pending` | Not yet started |
| `in-progress` | Currently being implemented |
| `implemented` | Code written but not yet visually verified |
| `verified` | Visually verified and passes all checks |
| `needs-review` | Failed verification after 3 attempts — needs human input |
| `failed` | Build error or critical issue preventing implementation |

### Page Type
| Type | Meaning | Example |
|------|---------|---------|
| `dashboard` | Overview/analytics page with multiple widgets | Dashboard with stats cards and charts |
| `list` | Table or list of resources | Users, Projects, Tasks list |
| `detail` | Single resource detail/edit view | User profile, Project details |
| `form` | Standalone form (create/edit) | Create new team, Invite user |
| `auth` | Authentication pages | Login, Sign up, Password reset |
| `settings` | Configuration/settings pages | Account settings, Team settings |

### Phase Values
| Phase | Meaning |
|-------|---------|
| `plan` | Analyzing documents and generating plan |
| `scaffold` | Setting up the NextJS project |
| `build` | Implementing pages iteratively |
| `images` | Generating real images from manifest via Gemini API |
| `audit` | Final site-wide checks |
| `complete` | All pages verified, audit passed |

## State Manager Commands

The `scripts/state_manager.py` script provides these operations:

```bash
# Initialize state from plan
python state_manager.py --action init --plan project-plan.json --output .nextjs-builder-state.json

# Set current phase
python state_manager.py --action set-phase --phase build

# Update page status
python state_manager.py --action update-page --page-id dashboard --status verified

# Add verification entry
python state_manager.py --action add-verification \
  --page-id dashboard \
  --result pass \
  --screenshot screenshots/dashboard-v2.png \
  --notes "All sections verified. Layout correct."

# Log a session action
python state_manager.py --action log --message "Implemented users page"

# Add an issue
python state_manager.py --action add-issue \
  --page-id dashboard \
  --severity minor \
  --description "Chart tooltip positioning off-screen on mobile"

# Get next pending page
python state_manager.py --action next-page

# Print status summary
python state_manager.py --action summary
```

## Reading State at Session Start

When resuming, follow this procedure:

1. Read `.nextjs-builder-state.json`
2. Check `current_phase` to understand where things are
3. If phase is `build`, find the first page with status `pending` or `in-progress`
4. If phase is `audit`, run the remaining audit checks
5. Check `issues` array for unresolved problems
6. Log the new session in `session_log`

```bash
python <skill-path>/scripts/state_manager.py --action summary
```

This prints a concise status overview so you can immediately understand the project state.

## Key Differences from Marketing Builder

### Page Entries
- Added `page_type` field to classify page purpose (dashboard, list, detail, form, etc.)
- Added `resource` field to identify which API resource the page serves
- Added `endpoints` field to list all API endpoints this page consumes
- Removed SEO-specific fields: `target_keyword`, `meta_description`, `h1`, `structured_data_type`

### Plan Structure
- Changed `seo_strategy` to `api_spec` containing path, title, version, and base_url
- Added `layout_preference` to design_inputs (e.g., "sidebar-layout", "top-nav")
- Added `openapi_spec_path` to design_inputs if an OpenAPI spec is provided

### Audit Fields
- Changed `audit.seo_passed` to `audit.interactions_passed` (verifying forms, buttons, interactive elements work)
- Kept accessibility, responsive, and performance checks

## Design Inputs Schema

```json
{
  "accent_color": "#2563eb",
  "accent_color_source": "user",
  "font_preference": "modern",
  "font_preference_source": "user",
  "layout_preference": "sidebar-layout",
  "layout_preference_source": "user",
  "openapi_spec_path": "spec/api.yaml",
  "openapi_spec_path_source": "user",
  "gemini_api_key": "AIza...",
  "gemini_api_key_source": "user"
}
```
