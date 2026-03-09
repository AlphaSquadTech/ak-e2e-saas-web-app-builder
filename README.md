# ak-e2e-saas-web-app-builder

A Claude skill that autonomously builds production-quality SaaS application frontends from OpenAPI specifications. Feed it an API spec and it will plan, scaffold, build, visually verify, and deliver a complete NextJS + shadcn/ui application — end to end, without manual intervention.

## What It Does

Given an OpenAPI 3.x spec (YAML or JSON), this skill:

1. **Parses** the spec to extract resources, endpoints, schemas, and security schemes
2. **Plans** the app structure — dashboard, CRUD pages, auth flows, settings
3. **Scaffolds** a NextJS project with shadcn/ui, Framer Motion, and a full design system derived from your chosen accent color
4. **Builds** every page with real or mock data, micro-interactions, form validation, data tables, and charts
5. **Verifies** each page visually via browser screenshots analyzed by Claude's vision
6. **Generates** AI images (empty states, illustrations, avatars) via the Gemini API
7. **Audits** the full app across desktop, tablet, and mobile viewports

The entire pipeline runs autonomously. You provide inputs once and get a complete app back.

## Tech Stack

- **NextJS 14+** (App Router, TypeScript, Server Components)
- **shadcn/ui** (Radix UI primitives, CSS variable theming)
- **Tailwind CSS** (utility-first styling)
- **Framer Motion** (micro-interactions on every interactive element)
- **React Hook Form + Zod** (form validation)
- **@tanstack/react-table** (sortable, filterable data tables)
- **recharts** (dashboard charts)
- **Gemini API** (AI image generation via `gemini-3-pro-image-preview`)

## Installation

### Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) or Claude Desktop (Cowork mode)
- Node.js 18+
- Python 3.8+
- A Gemini API key (optional, for AI image generation) — get one at https://aistudio.google.com/apikey

### Install the Skill

```bash
# Clone the repo
git clone https://github.com/alphasquadtech/ak-e2e-saas-web-app-builder.git

# Add to your Claude skills directory
# For Claude Code: copy to your project's .claude/skills/ directory
# For Cowork: copy to your skills folder
```

Alternatively, if using Claude Code with skill installation:

```bash
claude skill install alphasquadtech/ak-e2e-saas-web-app-builder
```

### Companion Skills (Auto-Installed)

The preflight script automatically installs these companion skills on first run:

- **shadcn-ui** (`giuseppe-trisciuoglio/developer-kit`) — shadcn/ui component patterns and best practices
- **interaction-design** (`wshobson/agents`) — Framer Motion micro-interaction catalogue
- **agent-browser** — Browser automation for visual verification screenshots

If installation fails (e.g., no internet), the skill falls back to its bundled reference docs.

## Usage

### Greenfield (New Project)

Start a Claude session and provide your OpenAPI spec. The skill will ask for 6 inputs, then build everything autonomously.

**Example prompts:**

```
Build a SaaS app from this OpenAPI spec: ./petstore-openapi.yaml
Use a sidebar layout, blue accent (#2563eb), modern font.
Backend API is running at https://api.petstore.example.com/v1
Here's my Gemini API key: <key>
```

```
Turn this API into a frontend: https://raw.githubusercontent.com/org/repo/main/openapi.json
Pick colors and fonts for me. No Gemini key, skip images.
```

```
Create an admin dashboard from this spec: ./inventory-api.yaml
I want a topnav layout with purple (#7c3aed) accent and bold font.
The backend is at http://localhost:8080/api
```

```
Build a UI for this API spec. Here's the file: ./crm-openapi.yaml
Sidebar layout, green (#059669), modern font.
Backend URL: https://crm-api.mycompany.io/v2
Gemini key: <key>
```

### Brownfield (Existing Project)

Point the skill at an existing NextJS project to add pages, fix interactions, or run a full audit.

**Example prompts:**

```
I have an existing NextJS project at ./my-saas-app.
Scan it and fix any missing micro-interactions.
My accent color is #2563eb, font is modern.
```

```
Add a new "Products" CRUD section to my existing app based on this spec: ./products-api.yaml
The project is in ./dashboard-app
```

```
Run a full visual audit on my NextJS project at ./my-app.
Check every page at desktop, tablet, and mobile. Fix spacing issues.
```

### What the Skill Asks For

On first run, the skill asks for exactly 6 inputs:

| # | Input | Required | Default |
|---|-------|----------|---------|
| 1 | OpenAPI spec (file path or URL) | Yes | — |
| 2 | Backend API URL | No | Falls back to mock data |
| 3 | Layout preference | No | `sidebar` |
| 4 | Accent color | No | Auto-picked based on API subject |
| 5 | Font preference | No | `modern` |
| 6 | Gemini API key | No | SVG placeholders used instead |

If you provide all inputs in your initial message, the skill won't ask again.

## Build Phases

| Phase | Name | What Happens |
|-------|------|-------------|
| 0 | Parse & Plan | OpenAPI spec parsed, resources extracted, app plan generated |
| 1 | Scaffold | NextJS project initialized, dependencies installed, layout and design system set up |
| 2 | Build | Every page built with data, interactions, and visual verification after each |
| 2.5 | Images | AI-generated images replace SVG placeholders (requires Gemini API key) |
| 3 | Audit | Full-app visual pass at 3 viewports, interaction audit, accessibility check, `npm run build` |

All phases run autonomously in sequence. The skill only pauses for missing inputs.

## How Visual Verification Works

After building each page, the skill:

1. Takes a full-page browser screenshot via `agent-browser`
2. Chunks the screenshot into analyzable sections (sidebar, data table, forms, etc.)
3. Analyzes each chunk with Claude's vision for layout, spacing, alignment, and component rendering
4. Records pass/fail in the state file — pages cannot be marked "verified" without a passing screenshot
5. If issues are found, fixes them and re-verifies (up to 3 iterations)

The state manager enforces this — there's no way to skip verification.

## State Management

All progress is tracked in `.nextjs-builder-state.json` in the project root. This means:

- **Sessions can be interrupted** — resume with `claude --resume <session-id>` and the skill picks up where it left off
- **Every page has a status** — `pending`, `in_progress`, `built`, `verified`, or `failed`
- **Verification is enforced** — the state manager rejects `verified` status without screenshot proof
- **Phase tracking** — the current build phase is persisted

Check progress anytime:

```bash
python scripts/state_manager.py --action summary
```

## Real API vs. Mock Data

The skill generates a transparent data provider layer:

- **`api-client.ts`** — typed fetch functions generated from the OpenAPI spec, one per endpoint
- **`mock-data.ts`** — realistic mock data generated from schemas (respects enums, relationships, types)
- **`data-provider.ts`** — switches between real API and mock data based on `NEXT_PUBLIC_API_URL`

All page components import from `data-provider`, never directly from the other two. To switch between real and mock data, just set or unset the env variable.

## Image Pipeline

The skill uses a two-stage image pipeline since Claude cannot generate images:

1. **During build** — branded SVG placeholders (using your accent color) are generated for every image slot
2. **After build** — a Python script calls the Gemini API (`gemini-3-pro-image-preview`) to generate real images from descriptive prompts stored in `image-manifest.json`

Typical cost: ~$0.50–$1.50 per app. If you skip the Gemini key, the app ships with SVG placeholders that look intentional, not broken.

## File Structure

```
ak-e2e-saas-web-app-builder/
├── SKILL.md                          # Main skill entry point
├── README.md                         # This file
├── references/
│   ├── workflow-phases.md            # Detailed phase-by-phase instructions
│   ├── visual-verification.md       # Screenshot verification guide
│   ├── saas-patterns.md             # SaaS UI patterns (lists, forms, dashboards)
│   ├── react-patterns.md            # React/NextJS patterns
│   ├── design-guidelines.md         # Design system + spacing rules
│   ├── interaction-patterns.md      # Framer Motion micro-interaction catalogue
│   ├── state-schema.md              # State file format reference
│   └── image-generation.md          # Image pipeline guide
├── scripts/
│   ├── preflight.sh                 # Dependency checker + companion skill installer
│   ├── parse_openapi.py             # OpenAPI spec parser
│   ├── init_project.sh              # NextJS project scaffolding
│   ├── state_manager.py             # Build state read/write/enforce
│   ├── verify_page.sh               # One-command visual verification
│   ├── resize_screenshot.py         # Screenshot chunking for vision analysis
│   ├── scan_project.py              # Brownfield project scanner
│   ├── generate_context_file.sh     # CLAUDE.md/GEMINI.md anti-amnesia generator
│   ├── generate_placeholders.py     # Branded SVG placeholder generator
│   └── generate_images.py           # Gemini API image generation
└── templates/
    ├── project-plan.json            # App plan structure template
    ├── state-tracker.json           # Initial state file template
    └── image-manifest.json          # Image manifest schema
```

## Caveats & Known Limitations

### Context Window

Long builds (10+ pages) may approach Claude's context window limit. The skill mitigates this with:
- **Anti-amnesia files** (`CLAUDE.md`/`GEMINI.md`) that are re-read every turn
- **State persistence** so interrupted sessions can resume
- Starting a fresh session with `claude --resume` if context runs out

### Visual Verification Accuracy

Visual verification catches most layout and spacing issues, but is not perfect. Known blind spots:
- Subtle color contrast issues (especially in dark mode)
- Animation timing (screenshots are static)
- Scroll-dependent layouts that require interaction to reveal
- Very small text alignment differences (< 2px)

After delivery, a manual review pass is recommended for production apps.

### Mock Data vs. Real API

When using mock data:
- Pagination is simulated (all data is in memory)
- Search/filter operates on the full mock dataset
- Create/update/delete operations show success feedback but don't persist across page reloads

When using a real API:
- The API must be running and accessible from the dev server
- CORS must be configured on the backend to allow requests from `localhost:3000`
- Authentication tokens are not automatically managed — you may need to add auth headers manually

### Image Generation

- Requires a Gemini API key with access to `gemini-3-pro-image-preview`
- Image generation adds ~2-5 minutes to the build depending on the number of images
- Generated images are good for prototypes and demos; consider custom illustrations for production
- The script includes retry logic and respects rate limits, but may fail on very large manifests (30+ images)

### Companion Skills

The skill works best with its companion skills installed (`shadcn-ui`, `interaction-design`, `agent-browser`). Without them, it falls back to bundled reference patterns — the output is still good, but companion skills provide richer component and interaction guidance.

### Browser Automation

Visual verification requires `agent-browser` to take screenshots. If `agent-browser` is not available:
- The skill will still build the app correctly
- Verification steps will be skipped (pages marked as "built" but not "verified")
- You can manually verify by running `npm run dev` and inspecting in a browser

## License

MIT
