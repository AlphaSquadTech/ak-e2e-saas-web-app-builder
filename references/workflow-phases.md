# Workflow Phases — Detailed Instructions

**Important**: Before starting any phase, the preflight script must have been run.
The SKILL.md instructs Claude to run `bash <skill-path>/scripts/preflight.sh` before
doing any work. If preflight hasn't run yet in this session, run it now.

## Phase 0: OpenAPI Parsing & Plan Generation

### Parse the OpenAPI Spec

If the user provided a GitHub URL, fetch it first:

```bash
curl -sL "<url>" -o openapi-spec.yaml
```

Use the `parse_openapi.py` script to extract structure:

```bash
python <skill-path>/scripts/parse_openapi.py \
  --spec openapi-spec.yaml \
  --output app-plan.json \
  --accent-color "#2563eb" \
  --font "modern" \
  --layout "sidebar"
```

The parser extracts:
- API title, description, version → app name and description
- Tags → page groups (each tag becomes a section/page)
- Endpoints grouped by resource → CRUD pages for each resource
- Schemas → TypeScript interfaces, form fields, table columns, mock data generators
- Security schemes → auth type (JWT, API key, OAuth, etc.)
- Request/response bodies → form structures, detail views

### Content Mapping for SaaS

1. **Identify resources** — Each major noun in the API (users, orders, products, etc.) becomes a resource module
2. **Map CRUD operations** — List → Detail → Create → Edit → Delete flows per resource
3. **Identify relationships** — Foreign keys and nested objects determine navigation structure
4. **Extract auth requirements** — Security schemes determine the auth flow to implement
5. **Find dashboard candidates** — Aggregate endpoints (stats, counts, recent activity) feed into a dashboard page

### Generate the App Plan

Create a plan following `templates/project-plan.json`. Typical SaaS structure:

- **Dashboard** (`/dashboard`): Overview with stats cards, recent activity, charts
- **Resource List** (`/resources`): Data table with search, filter, sort, pagination, bulk actions
- **Resource Detail** (`/resources/[id]`): Tabbed detail view with related data
- **Create Resource** (`/resources/new` or dialog on list page): Form with validation
- **Settings** (`/settings`): App configuration pages
- **Auth** (`/login`, `/register`): Authentication pages following the spec's security scheme

Adjust based on what the spec actually contains. Don't create pages for resources that don't have endpoints.

### Save Plan and Initialize State

```bash
python <skill-path>/scripts/state_manager.py --action init \
  --plan app-plan.json \
  --output .nextjs-builder-state.json
```

Proceed immediately to Phase 1 — the skill operates autonomously. Only pause for user
input if the spec is too ambiguous to generate a reasonable plan.

---

## Phase 1: Project Scaffolding

### Collect Design Inputs (MANDATORY — Do Not Skip)

**You MUST ask the user for their design preferences before scaffolding.** Do not
proceed to scaffolding without these values. Do not silently pick defaults. Always
ask, wait for a response, and then proceed.

If the user already provided these values in their initial message, use them directly
without re-asking. Only pick defaults if the user explicitly says "pick for me" or
"I don't care."

Ask for exactly five inputs:

1. **OpenAPI Spec** — Path to local file or GitHub raw URL
2. **App layout** — `sidebar` (default), `topnav`, or `minimal`
3. **Accent color** — A hex code (e.g., `#2563eb`), color name, or "pick for me"
4. **Font preference** — `modern`, `elegant`, `bold`, `minimal`, or a specific Google Font
5. **Gemini API key** — Their `GEMINI_API_KEY` for AI image generation in Phase 2.5

Default mapping for colors/fonts (only used when user says "pick for me"):
- SaaS/dashboard → `#2563eb` (blue) + modern
- Developer tools → `#0f172a` (dark navy) + minimal
- CRM/business → `#7c3aed` (purple) + bold
- Analytics → `#059669` (green) + modern
- E-commerce admin → `#ea580c` (orange) + bold

### Generate Full Design System from Inputs

From the accent color and font choice, automatically derive the complete design system
using shadcn's CSS variable theming (HSL-based):

```
Given accent color (e.g., #2563eb), convert to HSL and set:
  --primary: <accent HSL>
  --primary-foreground: <auto-contrast HSL>
  --secondary: <accent desaturated 30%, +15 lightness HSL>
  --background: 0 0% 100%
  --foreground: 222.2 84% 4.9%
  --muted: 210 40% 96.1%
  --muted-foreground: 215.4 16.3% 46.9%
  --accent: <accent at 10% opacity HSL>
  --border: 214.3 31.8% 91.4%
  --destructive: 0 84.2% 60.2%
  --radius: 0.5rem

Also generate .dark { } variant with inverted values.
```

Configure `tailwind.config.ts` following shadcn's pattern (see the shadcn-ui skill reference).

### Initialize NextJS

```bash
bash <skill-path>/scripts/init_project.sh <project-name>
```

### Install Dependencies

```bash
cd <project-name>

# UI framework (shadcn/ui)
npx shadcn@latest init -y
npx shadcn@latest add button card input label textarea separator badge \
  dialog sheet select table toast form tabs avatar dropdown-menu \
  menubar checkbox switch tooltip popover command accordion skeleton \
  alert alert-dialog breadcrumb navigation-menu scroll-area

# Icons
npm install lucide-react

# Animations (interaction design skill requirement)
npm install framer-motion

# Forms + validation
npm install react-hook-form zod @hookform/resolvers

# Data table (for resource list pages)
npm install @tanstack/react-table

# Date handling (common in SaaS)
npm install date-fns

# Charts (for dashboard)
npm install recharts
```

### Set Up App Layout

Based on the user's layout preference, create the shell:

**Sidebar layout (default):**
- `src/components/layout/sidebar.tsx` — Collapsible sidebar with nav items from the plan's resource list
- `src/components/layout/topbar.tsx` — Top bar with user avatar, search, notifications
- `src/components/layout/app-shell.tsx` — Wraps sidebar + topbar + main content area
- Navigation items are auto-generated from the plan's pages

**Topnav layout:**
- `src/components/layout/navbar.tsx` — Horizontal nav with dropdowns for grouped items
- `src/components/layout/app-shell.tsx` — Wraps navbar + main content

**Minimal layout:**
- `src/components/layout/app-shell.tsx` — Clean wrapper with minimal chrome

All layouts MUST include:
- Framer Motion page transitions (AnimatePresence wrapping the main content area)
- Toaster component from shadcn in the root layout
- Skeleton loading placeholder for the content area
- Responsive behavior (sidebar collapses on mobile, topnav becomes hamburger)

### Generate Mock Data Layer

Create `src/lib/mock-data.ts` with typed mock data generated from OpenAPI schemas:
- Each resource gets a typed array of mock items (10-25 items)
- Use realistic names, dates, amounts, emails, statuses
- Respect enum values from the spec
- Include relationship IDs that reference other resource mocks
- Export typed getter functions: `getUsers()`, `getUserById(id)`, `searchUsers(query)`, etc.
- Add simulated async delays: `await new Promise(r => setTimeout(r, 300+Math.random()*500))`

### Generate TypeScript Types

Create `src/lib/types.ts` from OpenAPI schemas:
- Each schema becomes a TypeScript interface
- Enum schemas become union types
- Request bodies become form input types
- Response bodies become display types

### Generate Zod Schemas

Create `src/lib/schemas.ts`:
- Each POST/PUT request body schema becomes a Zod schema
- These are used by React Hook Form for validation
- Map OpenAPI validation rules: required, minLength, maxLength, pattern, enum, format

### Configure Root Layout

`app/layout.tsx`:
- Import chosen font(s) via `next/font/google`
- Apply as CSS variables
- Add Toaster from shadcn
- Wrap with AppShell component
- Include `suppressHydrationWarning` for dark mode support

### Verify Scaffolding

```bash
npm run dev &
sleep 5
agent-browser open http://localhost:3000
agent-browser wait --load networkidle
agent-browser screenshot screenshots/scaffold.png
```

Read the screenshot. Confirm the base layout renders. Fix any issues.

### Generate Context File

```bash
bash <skill-path>/scripts/generate_context_file.sh --project-dir <project-name>
```

This creates `CLAUDE.md` and `GEMINI.md` in the project root. This step is critical.
Without the context file, the AI will gradually forget to verify its work over long sessions.

```bash
python <skill-path>/scripts/state_manager.py --action set-phase --phase build
```

---

## Phase 2: Autonomous Build

For each page in the plan's build order:

### 2.1 Implement the Page

**For resource list pages (`/resources`):**
- Use shadcn Table component with @tanstack/react-table
- Implement: column sorting, search/filter input, pagination controls
- Each row has action dropdown (View, Edit, Delete)
- "Create New" button opens a Dialog with the create form
- Skeleton loading state while "fetching" mock data
- Empty state with illustration placeholder and CTA
- Bulk selection with checkbox column
- All interactions animated with Framer Motion

**For resource detail pages (`/resources/[id]`):**
- Tabbed layout using shadcn Tabs component
- Primary info displayed in a Card
- Related resources in sub-tables or card grids
- Edit button opens a Sheet (slide-over) or Dialog with pre-filled form
- Delete button triggers AlertDialog confirmation
- Breadcrumb navigation back to list

**For create/edit forms:**
- Use shadcn Form components with React Hook Form + Zod validation
- Real-time validation with error messages
- Select dropdowns for enum fields
- Date pickers for date fields
- Textarea for long text fields
- Toast notification on "successful" submission
- Loading state on submit button (spinner + disabled)

**For dashboard pages:**
- Stat cards with animated number transitions
- Charts using recharts (line, bar, or area)
- Recent activity list
- Quick action buttons
- All cards with hover lift effect

**For auth pages (if spec has security schemes):**
- Login form following the spec's auth pattern
- Registration form if applicable
- Clean centered layout (no sidebar/topbar)
- Form validation with error states
- Loading state on submit
- Toast for success/error feedback

**For settings pages:**
- Card-based sections for different setting groups
- Toggle switches for boolean settings
- Forms for profile/account details
- Destructive actions (delete account) in a separated danger zone with AlertDialog

**Micro-interactions on EVERY page (critical — reference `references/interaction-patterns.md`):**
- All buttons: `whileHover={{ scale: 1.02 }}`, `whileTap={{ scale: 0.98 }}`
- All cards: hover translateY(-4px) + shadow transition
- Page mount: fade-in from below (opacity 0→1, y 20→0)
- Data loading: skeleton screens, not spinners
- Form submission: button loading state + toast
- Delete confirmations: AlertDialog with destructive variant
- Navigation: AnimatePresence page transitions
- Tables: row hover highlight
- Sidebar: collapse/expand with spring animation
- Mobile: swipe-to-action on list items where appropriate
- Always wrap motion in `prefers-reduced-motion` check

**Image handling — every page:**

For every image the page needs (empty states, illustrations, avatars, etc.):

1. Determine the image's purpose, ideal dimensions, and aspect ratio
2. Write a descriptive prompt for AI generation
3. Add an entry to `image-manifest.json`
4. Generate the placeholder SVG:
   ```bash
   python <skill-path>/scripts/generate_placeholders.py
   ```
5. Reference the placeholder path in the component:
   ```tsx
   <Image
     src="/images/placeholders/empty-state-users.svg"
     alt="No users found"
     width={400}
     height={300}
   />
   ```

### 2.2 Visual Verification (Mandatory — One Command)

After implementing each page, verify it visually. **This is not optional.**
The state manager will reject any attempt to mark the page as `verified` without proof.

```bash
bash <skill-path>/scripts/verify_page.sh <route> <page-id>
```

Then **analyze every chunk** the script outputs. For SaaS pages, evaluate:

- **Layout**: Sidebar/topnav renders correctly? Content area sized properly?
- **Components**: shadcn components render? Tables populated? Forms have all fields?
- **Interactions**: Buttons visible and styled? Cards have proper spacing?
- **Data**: Mock data displayed correctly? Empty states shown where appropriate?
- **Design**: Accent color correct? Typography consistent? Dark/light contrast good?

Record result in state manager:
```bash
# If verification passed:
python <skill-path>/scripts/state_manager.py \
  --action add-verification --page-id <id> --result pass \
  --screenshot screenshots/<id>-v1-full.png \
  --notes "All sections verified. Layout, content, and design correct."

# If issues found:
python <skill-path>/scripts/state_manager.py \
  --action add-verification --page-id <id> --result fail \
  --screenshot screenshots/<id>-v1-full.png \
  --notes "Table columns misaligned. Empty state not showing."
```

Same pass/fail/fix loop — maximum 3 iterations per page.

### 2.3 Regression Check

After each page, spot-check one previously verified page to catch regressions
(especially if shared components were modified).

### 2.4 Continue to Next Page

Move to the next page in the build order. Repeat until all pages are done.

---

## Phase 2.5: Image Generation

After all pages are built and verified with placeholders, generate real images.

### Prerequisites

1. **google-genai SDK**: `pip install google-genai --break-system-packages`
2. **Pillow** for image resizing: `pip install Pillow --break-system-packages`
3. **Gemini API key**: Should already be saved in the state file from Phase 1 design inputs.

Export the saved API key:

```bash
export GEMINI_API_KEY="$(python3 -c "import json; print(json.load(open('.nextjs-builder-state.json'))['design_inputs'].get('gemini_api_key',''))")"
```

If the API key is missing at this point, ask the user for it now. If they provide it,
save it to the state file. If they decline, skip this phase — the app is fully functional
without real images.

### Dry Run, Generate, Swap, Re-verify

Same process as the marketing skill — see [references/image-generation.md](references/image-generation.md).

```bash
python <skill-path>/scripts/generate_images.py --dry-run
python <skill-path>/scripts/generate_images.py
```

After swapping placeholders for real images, take new screenshots and verify.

---

## Phase 3: Final Audit

### Full-App Visual Pass

Take full-page screenshots of every page at desktop, tablet (768px), and
mobile (375px) viewports. Chunk and analyze each.

### Interaction Audit Checklist

- [ ] Every button has hover/tap micro-interaction
- [ ] Every card has hover lift effect
- [ ] All loading states use skeleton screens
- [ ] All form submissions show loading state + toast feedback
- [ ] Delete operations use AlertDialog confirmation
- [ ] Page transitions are smooth (AnimatePresence)
- [ ] Sidebar collapses/expands with animation
- [ ] `prefers-reduced-motion` is respected
- [ ] No animation blocks user interaction

### Component Quality Checklist

- [ ] All forms validate with Zod schemas
- [ ] All form inputs have associated labels (accessibility)
- [ ] All interactive elements are keyboard-focusable
- [ ] All icon-only buttons have ARIA labels
- [ ] Tables are sortable and paginated
- [ ] Empty states are handled for every list/table
- [ ] Toast notifications for all user actions
- [ ] Breadcrumb navigation on detail pages
- [ ] Responsive layout works at all breakpoints

### Performance Check

```bash
npm run build
```

- No build warnings
- No unnecessary `'use client'` on components that don't need it
- Bundle size reasonable
- Images optimized

### Deliver

Update state to complete:
```bash
python <skill-path>/scripts/state_manager.py --action set-phase --phase complete
```

Present the user with:
- Summary of all pages built (routes, titles, key functionality)
- Screenshot gallery
- Any unresolved issues
- Run instructions: `npm run dev`

---

## Brownfield Entry (Existing Projects)

When using this skill on an existing NextJS project instead of building from scratch,
the phases become modular operations rather than a linear pipeline.

### Collect Design Inputs (MANDATORY — Do Not Skip)

Same rule as fresh projects — ask for accent color, font, layout preference, and
Gemini API key. If the user already provided values, use them directly.

### Scan the Project

```bash
python <skill-path>/scripts/scan_project.py --project-dir . \
  --accent-color "<user's color>" --font "<user's font>"
```

This produces `.nextjs-builder-state.json` and `image-manifest.json`.

### Generate Context File

```bash
bash <skill-path>/scripts/generate_context_file.sh --project-dir .
```

Always do this. The context file prevents verification amnesia.

### Targeted Work

Pick what the project needs:

**Add a new page:**
1. Create `app/<route>/page.tsx`
2. Add image manifest entries
3. Run `generate_placeholders.py`
4. Run `verify_page.sh <route> <page-id>`
5. Fix → re-verify
6. Record in state manager

**Fix interaction issues flagged by scan:**
1. Read `state_manager.py --action summary`
2. Add missing animations, loading states, form validation
3. Verify each fixed page

**Run a full audit:**
1. Set phase: `state_manager.py --action set-phase --phase audit`
2. Follow Phase 3 instructions
