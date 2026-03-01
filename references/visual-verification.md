# Visual Verification Guide

Every page and significant UI change must be visually verified before marking complete.
This ensures the implementation matches the requirements and catches rendering issues early.

## The Verification Loop

```
Implement → Full-page screenshot → Chunk → Analyze all chunks → Fix (if needed) → Re-screenshot → Done
```

Maximum 3 fix-and-verify iterations per page. If still failing after 3 attempts,
log the issues in the state file and move on — the user can review and decide.

## Step 1: Prepare the Page

Ensure the dev server is running:

```bash
# Start if not already running
lsof -i :3000 || (cd <project-dir> && npm run dev &)
sleep 3
```

## Step 2: Take a Full-Page Screenshot

Always use `--full` to capture the entire page, not just the viewport. SaaS pages
can be complex with interactive components — sidebar, multiple sections, footer — and
viewport-only screenshots miss critical content.

```bash
# Navigate to the page
agent-browser open http://localhost:3000/<route>

# Wait for the page to fully load (critical for dynamic content)
agent-browser wait --load networkidle

# Take FULL PAGE screenshot (not viewport)
agent-browser screenshot --full screenshots/<page-id>-v<iteration>-full.png
```

### Screenshot Naming Convention

```
screenshots/<page-id>-v<iteration>-full.png        # Full page (source, complete)
screenshots/<page-id>-v<iteration>-001.jpg          # Chunk 1 (sidebar/top area)
screenshots/<page-id>-v<iteration>-002.jpg          # Chunk 2 (main content)
screenshots/<page-id>-v<iteration>-003.jpg          # Chunk 3 (etc.)
screenshots/<page-id>-mobile-v<iteration>-full.png  # Mobile full page
screenshots/<page-id>-tablet-v<iteration>-full.png  # Tablet full page
```

## Step 3: Chunk for Vision Analysis

A full-page SaaS screenshot with sidebar and content can be 1280x2000-4000px —
far too tall for Claude's vision to analyze effectively in one image. The resize script's
`chunk` mode slices it into viewport-sized pieces (default 900px tall) with overlap
between chunks so no element gets cut off at a boundary.

```bash
python <skill-path>/scripts/resize_screenshot.py \
  screenshots/<page-id>-v<iteration>-full.png \
  screenshots/<page-id>-v<iteration> \
  --mode chunk
```

This produces numbered files:
```
screenshots/<page-id>-v<iteration>-001.jpg   # Top of page (sidebar + header)
screenshots/<page-id>-v<iteration>-002.jpg   # Next section
screenshots/<page-id>-v<iteration>-003.jpg   # Next section
...
```

Each chunk is:
- 900px tall from the source (configurable via `--chunk-height`)
- 100px overlap with adjacent chunks (configurable via `--overlap`)
- Resized to fit within 1568px on the longest edge
- Saved as JPEG under 5MB

For very long pages, use a larger chunk height to reduce the number of images:
```bash
python <skill-path>/scripts/resize_screenshot.py \
  screenshots/<page-id>-v<iteration>-full.png \
  screenshots/<page-id>-v<iteration> \
  --mode chunk --chunk-height 1200
```

### Fallback: Single Image Resize

For short pages that fit in ~2 viewport heights, a single resized image is fine:
```bash
python <skill-path>/scripts/resize_screenshot.py \
  screenshots/<page-id>-v<iteration>-full.png \
  screenshots/<page-id>-v<iteration>-resized.jpg
```

## Step 4: Analyze Every Chunk with Vision

Read each chunk image sequentially using Claude's built-in vision (the Read tool
processes images). Analyze them in order — they represent the page from top to bottom.

```
Read screenshots/<page-id>-v<iteration>-001.jpg   # Sidebar / header
Read screenshots/<page-id>-v<iteration>-002.jpg   # Main content / tables
Read screenshots/<page-id>-v<iteration>-003.jpg   # More content / footer
...
```

For each chunk, evaluate against these criteria:

### Layout & Structure
- Does the section match what the plan describes for this part of the page?
- Are elements properly aligned and spaced?
- Does content flow logically from the previous chunk?
- No unexpected gaps or overlapping elements?
- Sidebar present and properly styled (if this is a dashboard)?

### Visual Design
- Correct colors from the design system (accent color, text colors, backgrounds)?
- Typography consistent (headings, body, captions)?
- Visual hierarchy clear (headings stand out, CTAs are prominent)?
- Images/icons rendered correctly?

### Content
- Is the right content displayed (from the source document)?
- Any missing sections that should be here?
- Text readable (not too small, not clipped, not overflowing)?

### Per-Section Checks for SaaS Pages

**Sidebar chunk**:
- Navigation items present and readable?
- Active state visually distinct (background or border)?
- Collapse/expand button visible?
- Icons paired with labels?

**Data table chunk**:
- Table headers properly aligned?
- Column headers bold and distinct from data?
- Data rows populated with content?
- Zebra striping (alternating row colors) present?
- Pagination or load more control visible?

**Form chunk**:
- All form fields present?
- Labels aligned and associated with inputs?
- Placeholder text visible but not confusing?
- Validation messages clear and positioned correctly?
- Submit button prominent and accessible?

**Dashboard chunk**:
- Stat cards rendered with icon, label, and value?
- Cards aligned in grid layout?
- Gap spacing consistent between cards?
- No horizontal scrolling?
- Charts/visualizations visible and not distorted?

**Recent activity / list chunk**:
- Items rendered and populated with data?
- Timestamps or metadata visible?
- Empty state shown appropriately (if no data)?

**Empty state chunk**:
- Illustration or icon visible?
- Message text clear and helpful?
- CTA button prominent and labeled?

### Obvious Issues (any chunk)
- Blank/white areas where content should be
- Broken images (alt text showing instead of image)
- Overlapping or clipped elements
- Horizontal scrollbar or overflow
- Console errors visible in the UI
- Text that appears cut off or truncated

After analyzing all chunks, form a single verdict: pass or fail with specific notes.

## Step 5: Record Results

After analysis, update the state:

```bash
# If verification passed
python <skill-path>/scripts/state_manager.py \
  --action add-verification \
  --page-id <page-id> \
  --result pass \
  --screenshot screenshots/<page-id>-v<iteration>-full.png \
  --notes "All sections verified across N chunks. Layout, content, and design correct."

# If issues found
python <skill-path>/scripts/state_manager.py \
  --action add-verification \
  --page-id <page-id> \
  --result fail \
  --screenshot screenshots/<page-id>-v<iteration>-full.png \
  --notes "Chunk 2: table headers misaligned. Chunk 3: empty state button missing."
```

## Step 6: Fix and Re-verify (if needed)

If issues were found:

1. Fix the identified problems in the code
2. Refresh the page (agent-browser will show the updated version)
3. Take a new full-page screenshot with incremented version number
4. Chunk and analyze again
5. Repeat up to 3 times total

If after 3 iterations the page still has issues, log them and move on:

```bash
python <skill-path>/scripts/state_manager.py \
  --action update-page \
  --page-id <page-id> \
  --status needs-review \
  --notes "After 3 iterations: sidebar collapse button positioning needs refinement"
```

## Regression Testing with Diff

After modifying any shared component (nav, sidebar, layout), use agent-browser's diff
capability to check for visual regressions on previously verified pages:

```bash
# Save baseline before changes
agent-browser open http://localhost:3000/dashboard
agent-browser wait --load networkidle
agent-browser screenshot --full screenshots/dashboard-baseline.png

# Make your changes...

# Compare after changes
agent-browser open http://localhost:3000/dashboard
agent-browser wait --load networkidle
agent-browser diff screenshot --baseline screenshots/dashboard-baseline.png
```

The diff output highlights changed pixels in red and reports a mismatch percentage.
A mismatch > 5% warrants investigation (unless the change was intentional).

## Annotated Screenshots

For debugging complex layouts, use annotated screenshots that label interactive elements:

```bash
agent-browser screenshot --annotate screenshots/<page-id>-annotated.png
```

This overlays numbered boxes on interactive elements, making it easier to reference
specific parts of the page when describing issues.

## Multi-Viewport Verification

For important pages (dashboards, main flows), verify at three viewports. Use `--full` at each viewport:

```bash
# Desktop (default, usually 1280x720)
agent-browser open http://localhost:3000/<route>
agent-browser wait --load networkidle
agent-browser screenshot --full screenshots/<page-id>-desktop-full.png

# Tablet
agent-browser close && agent-browser --viewport 768x1024 open http://localhost:3000/<route>
agent-browser wait --load networkidle
agent-browser screenshot --full screenshots/<page-id>-tablet-full.png

# Mobile
agent-browser close && agent-browser --viewport 375x812 open http://localhost:3000/<route>
agent-browser wait --load networkidle
agent-browser screenshot --full screenshots/<page-id>-mobile-full.png
```

Chunk and analyze each viewport's full-page screenshot separately. Mobile often
reveals layout issues that desktop hides, especially for sidebars and data tables.
