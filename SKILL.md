---
name: ak-e2e-saas-web-app-builder
description: >-
  Build end-to-end SaaS application frontends from OpenAPI specifications using NextJS,
  shadcn/ui, and Framer Motion micro-interactions. Use when the user wants to create a
  SaaS dashboard, admin panel, CRUD application, or any data-driven web app from an
  OpenAPI spec. Also trigger when the user mentions "build a SaaS app from this spec",
  "create an admin dashboard", "turn this API into a frontend", "build a UI for this API",
  or wants to convert an OpenAPI spec into a working, interactive NextJS application.
  Supports both greenfield (new project) and brownfield (existing NextJS project) workflows.
  The skill works autonomously — it parses the OpenAPI spec, plans the app structure,
  builds every page with full interactivity and mock data, and visually verifies every
  page via browser screenshots analyzed by Claude's vision. All progress is tracked in a
  session-agnostic state file so work survives session interruptions.
---

# E2E SaaS Builder

Autonomously build production-quality SaaS application frontends from OpenAPI specifications.
Feed it an OpenAPI spec (file path or GitHub raw URL), and it will plan the app structure,
scaffold a NextJS + shadcn/ui project, implement every page with mock data and
micro-interactions, and visually verify its work.

The skill operates with minimal human intervention — it parses the OpenAPI spec,
generates an app plan, builds every page with realistic mock data, applies Framer Motion
micro-interactions to every component, takes screenshots to verify its work, and
fixes issues it finds. Progress is persisted so the build can resume across sessions.

## Preflight (Run First — Every Time)

Before doing ANY work, run the preflight script. It installs companion skills,
checks system dependencies (Node, Python, Pillow, agent-browser), and detects
whether this is a fresh start or a resume:

```bash
bash <skill-path>/scripts/preflight.sh
```

This is idempotent — safe to re-run. It will:
1. Install `shadcn-ui` (giuseppe-trisciuoglio/developer-kit), `interaction-design` (wshobson/agents), and `agent-browser` skills
2. Install Pillow for screenshot resizing and PyYAML for spec parsing
3. Verify Node.js 18+, npm, Python 3 are available
4. Check for an existing `.nextjs-builder-state.json` (resume detection)

If any companion skill fails to install (e.g., no internet), the skill falls back to
bundled patterns in [references/react-patterns.md](references/react-patterns.md),
[references/saas-patterns.md](references/saas-patterns.md), and
[references/interaction-patterns.md](references/interaction-patterns.md).

## Quick Start

### Resuming a Previous Session

After preflight, check its output. If it reports an existing state file, read it
to understand current progress and resume from the first incomplete item.
See [references/state-schema.md](references/state-schema.md).

### Starting Fresh

**STOP — Before doing anything else, you MUST ask the user for these inputs.**
Do not skip this step. Do not pick defaults silently. Always ask, even if the user's
initial prompt doesn't mention design. If they say "pick for me" or don't care, THEN
you may choose defaults based on the API's subject matter.

Ask for exactly these six inputs (nothing more — everything else is derived automatically):

1. **OpenAPI Spec** — Path to a local file OR a GitHub raw URL to an OpenAPI 3.x spec
   (YAML or JSON). The skill will fetch from URLs automatically.

2. **Backend API URL** (optional) — The base URL of a running backend API (e.g.,
   `https://api.example.com/v1`). If provided, the app will make real API calls
   instead of using mock data. If not provided or the API is not running,
   the app falls back to mock data generated from the spec schemas.

3. **App layout preference** — Ask: "What layout style do you want?"
   - `sidebar` → Collapsible sidebar nav + top bar + main content (default for most SaaS)
   - `topnav` → Horizontal nav bar + main content area
   - `minimal` → No persistent nav, tab-based navigation within pages
   - Or describe a custom layout

4. **Accent color** — A single brand/accent color (hex code, color name, or "pick for me").
   This drives the entire palette: primary buttons, links, highlights. The rest of the
   color system is generated automatically to complement this choice.

5. **Font preference** — One of: "modern" (Inter/DM Sans), "elegant" (Playfair Display + Inter),
   "bold" (Plus Jakarta Sans), "minimal" (Geist), or a specific Google Font name.

6. **Gemini API key** — Required for AI image generation (empty states, onboarding
   illustrations, avatars). Ask the user for their `GEMINI_API_KEY` (or `GOOGLE_API_KEY`).
   If they don't have one, point them to https://aistudio.google.com/apikey.
   If they want to skip, the app will use branded SVG placeholders and still look good.

If the user already provided these in their initial message, skip asking and use the
provided values directly. If they say "pick for me" for colors/fonts, choose sensible
defaults based on the API's subject matter:
- SaaS/dashboard → `#2563eb` (blue) + modern
- Developer tools → `#0f172a` (dark navy) + minimal
- CRM/business → `#7c3aed` (purple) + bold
- Analytics → `#059669` (green) + modern
- E-commerce admin → `#ea580c` (orange) + bold

### Existing Project (Brownfield)

To use this skill on an existing NextJS project:

1. **STOP — Ask for design inputs first** (same rule as fresh projects):
   - **Accent color**: Ask the user. If they already provided one, use it. If they say
     "pick for me", try to detect from the project's Tailwind/CSS config, or fall back
     to subject-matter defaults.
   - **Font preference**: Ask the user. Same logic — use provided, detect, or default.
   - **Layout preference**: Ask the user. Detect from existing layout if possible.
   - **Gemini API key**: Ask the user for their `GEMINI_API_KEY`. If they don't have one,
     point them to https://aistudio.google.com/apikey. If they want to skip, that's fine.

2. **Scan the project** (pass the design inputs as flags):
   ```bash
   python <skill-path>/scripts/scan_project.py --project-dir . \
     --accent-color "<user's color>" --font "<user's font>"
   ```

3. **Review the scan output.** Check `.nextjs-builder-state.json` for the list of pages
   and issues found.

4. **Generate context files** (critical for verification enforcement):
   ```bash
   bash <skill-path>/scripts/generate_context_file.sh --project-dir .
   ```

5. **Work on specific pages.** Use the state manager to find what needs work:
   ```bash
   python <skill-path>/scripts/state_manager.py --action summary
   python <skill-path>/scripts/state_manager.py --action next-page
   ```

6. **Verify after every change:**
   ```bash
   bash <skill-path>/scripts/verify_page.sh <route> <page-id>
   ```

### Build Phases

| Phase | Name | Description |
|-------|------|-------------|
| 0 | **Parse & Plan** | Parse OpenAPI spec, extract endpoints/schemas, generate app plan with page structure |
| 1 | **Scaffold** | Initialize NextJS project with shadcn/ui, Framer Motion, app layout, design system |
| 2 | **Build** | Implement pages autonomously with mock data, interactions, visual verification after each |
| 2.5 | **Images** | Generate real images via Gemini API for empty states, illustrations, avatars |
| 3 | **Audit** | Full-app visual pass, accessibility check, interaction audit, responsive verification |

For detailed instructions: [references/workflow-phases.md](references/workflow-phases.md)

## Core Principles

1. **Spec-first.** The OpenAPI spec is the source of truth. Every endpoint becomes a page
   or component. Schemas drive form fields, table columns, and mock data shapes. Don't
   invent API structures.

2. **Interactive by default.** Every component gets micro-interactions: buttons have
   hover/tap feedback, cards lift on hover, loading states use skeletons, forms validate
   in real-time, toasts confirm actions. Use Framer Motion + shadcn/ui patterns.
   See [references/interaction-patterns.md](references/interaction-patterns.md).

3. **Real API when available, mock data as fallback.** If the user provides a backend
   API URL, generate API client functions that call the real endpoints. Use the OpenAPI
   spec to type the responses. If no backend URL is given (or the API is unreachable),
   fall back to realistic mock data generated from schemas. The frontend should feel
   like a working app either way — but real data is always preferred.

4. **Verify visually, autonomously.** After implementing each page, take a screenshot and
   analyze it. Fix issues without asking the user. Only escalate if stuck after 3 attempts.
   See [references/visual-verification.md](references/visual-verification.md).

5. **Track everything.** Update `.nextjs-builder-state.json` after every meaningful action.
   This is the source of truth. Use:
   ```bash
   python <skill-path>/scripts/state_manager.py --action update-page --page-id dashboard --status verified
   ```

6. **Ship quality.** shadcn/ui components, Radix UI accessibility, proper TypeScript,
   Zod validation on all forms. The output should be production-ready.

7. **Verify or it didn't happen.** The state manager enforces that pages cannot be
   marked `verified` without a passing verification entry that includes a screenshot.
   Use `verify_page.sh` to run the full verification pipeline in one command. The
   generated `CLAUDE.md`/`GEMINI.md` file repeats this rule on every turn.

## OpenAPI Processing

The skill maps OpenAPI spec structures to app pages:

| Spec Element | Maps To |
|--------------|---------|
| Tag groups | Page/section grouping |
| `GET /resources` | List/table page with search, filter, pagination |
| `GET /resources/{id}` | Detail page with tabbed sections |
| `POST /resources` | Create form (dialog or page) |
| `PUT/PATCH /resources/{id}` | Edit form (dialog or inline edit) |
| `DELETE /resources/{id}` | Delete confirmation dialog |
| Schema properties | Form fields, table columns, detail display |
| Enum properties | Select dropdowns, filter chips |
| Auth security schemes | Login page, auth guard pattern |

## Environment Support

**Claude Code**: Full support. Use bash, agent-browser for screenshots, Read tool for vision.

**Cowork**: Full support. Same workflow. Save screenshots to project directory for persistence.

## Image Generation

Claude cannot generate images. The skill uses a two-stage image pipeline:

1. **During Build (Phase 2)**: Every `<Image>` component gets a branded SVG placeholder
   and a corresponding entry in `image-manifest.json` with a descriptive prompt.
   Placeholders use the accent color so the app looks intentional, not broken.

2. **After Build (Phase 2.5)**: A Python script calls the Gemini API via the `google-genai`
   SDK to generate real images from the manifest prompts using the
   `gemini-3.1-flash-image-preview` model. Requires a `GEMINI_API_KEY`.
   Cost: ~$0.50–$1.50 for a typical app.

```bash
# Generate branded placeholders (run during Phase 2, after adding manifest entries)
python <skill-path>/scripts/generate_placeholders.py

# Preview what will be generated (dry run)
python <skill-path>/scripts/generate_images.py --dry-run

# Generate real images via Gemini API (key is saved in state file's design_inputs)
export GEMINI_API_KEY="$(python3 -c "import json; print(json.load(open('.nextjs-builder-state.json'))['design_inputs'].get('gemini_api_key',''))")"
python <skill-path>/scripts/generate_images.py
```

See [references/image-generation.md](references/image-generation.md) for the full guide.

## File Reference

| Path | Purpose | When to read |
|------|---------|--------------|
| [references/workflow-phases.md](references/workflow-phases.md) | Detailed phase instructions | Starting each phase |
| [references/visual-verification.md](references/visual-verification.md) | Screenshot + vision verification | Before verifying any page |
| [references/saas-patterns.md](references/saas-patterns.md) | SaaS UI patterns | During implementation |
| [references/react-patterns.md](references/react-patterns.md) | React/Next.js patterns | When implementing components |
| [references/design-guidelines.md](references/design-guidelines.md) | SaaS design + UX rules | When implementing UI |
| [references/interaction-patterns.md](references/interaction-patterns.md) | Micro-interaction catalogue | When adding animations |
| [references/state-schema.md](references/state-schema.md) | State file format | When reading/updating state |
| [references/image-generation.md](references/image-generation.md) | Image pipeline guide | Phase 2 and 2.5 |
| [scripts/preflight.sh](scripts/preflight.sh) | Install skills + check dependencies | **Always run first** |
| [scripts/parse_openapi.py](scripts/parse_openapi.py) | OpenAPI spec parser | Phase 0 only |
| [scripts/init_project.sh](scripts/init_project.sh) | NextJS project scaffolding | Phase 1 only |
| [scripts/state_manager.py](scripts/state_manager.py) | Read/update state file | Throughout all phases |
| [scripts/verify_page.sh](scripts/verify_page.sh) | One-command visual verification | After every page change |
| [scripts/resize_screenshot.py](scripts/resize_screenshot.py) | Image chunking for vision | During visual verification |
| [scripts/scan_project.py](scripts/scan_project.py) | Brownfield project scanner | Existing projects |
| [scripts/generate_context_file.sh](scripts/generate_context_file.sh) | CLAUDE.md/GEMINI.md generator | Phase 1 or brownfield |
| [scripts/generate_placeholders.py](scripts/generate_placeholders.py) | Branded SVG placeholders | Phase 2 |
| [scripts/generate_images.py](scripts/generate_images.py) | Gemini API image generation | Phase 2.5 |
| [templates/project-plan.json](templates/project-plan.json) | Plan structure template | Phase 0 only |
| [templates/state-tracker.json](templates/state-tracker.json) | Initial state template | Phase 1 only |
| [templates/image-manifest.json](templates/image-manifest.json) | Image manifest schema | Phase 2 |
