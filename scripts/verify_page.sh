#!/usr/bin/env bash
# verify_page.sh — One-command visual verification for a single page.
#
# Handles the entire screenshot → chunk pipeline. After running this,
# Claude only needs to analyze the output chunk images with vision.
#
# Usage:
#   bash verify_page.sh <route> <page-id> [options]
#
# Examples:
#   bash verify_page.sh / home
#   bash verify_page.sh /features features --viewport mobile
#   bash verify_page.sh /pricing pricing --iteration 2
#
# Output:
#   screenshots/<page-id>-<viewport>-v<iteration>-full.png   (full page)
#   screenshots/<page-id>-<viewport>-v<iteration>-001.jpg    (chunk 1)
#   screenshots/<page-id>-<viewport>-v<iteration>-002.jpg    (chunk 2)
#   ...
#
# Exit codes:
#   0 = screenshots captured and chunked successfully
#   1 = error (server not running, page failed to load, etc.)

set -euo pipefail

ROUTE="${1:?Usage: bash verify_page.sh <route> <page-id> [options]}"
PAGE_ID="${2:?Usage: bash verify_page.sh <route> <page-id> [options]}"

# Defaults
PROJECT_DIR="."
VIEWPORT="desktop"
ITERATION=""
SKILL_PATH="$(dirname "$(realpath "$0")")/.."
PORT=3000

# Parse optional args
shift 2
while [[ $# -gt 0 ]]; do
  case $1 in
    --project-dir) PROJECT_DIR="$2"; shift 2 ;;
    --viewport) VIEWPORT="$2"; shift 2 ;;
    --iteration) ITERATION="$2"; shift 2 ;;
    --skill-path) SKILL_PATH="$2"; shift 2 ;;
    --port) PORT="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# Resolve viewport dimensions
case "$VIEWPORT" in
  desktop) VP_WIDTH=1280; VP_HEIGHT=720 ;;
  tablet)  VP_WIDTH=768;  VP_HEIGHT=1024 ;;
  mobile)  VP_WIDTH=375;  VP_HEIGHT=812 ;;
  *) echo "Unknown viewport: $VIEWPORT (use desktop, tablet, or mobile)" >&2; exit 1 ;;
esac

# Viewport suffix (omit for desktop since it's the default)
VP_SUFFIX=""
if [ "$VIEWPORT" != "desktop" ]; then
  VP_SUFFIX="-${VIEWPORT}"
fi

# Auto-detect iteration number if not specified
SCREENSHOTS_DIR="${PROJECT_DIR}/screenshots"
mkdir -p "$SCREENSHOTS_DIR"

if [ -z "$ITERATION" ]; then
  # Find the highest existing iteration number for this page+viewport
  EXISTING=$(ls "$SCREENSHOTS_DIR"/${PAGE_ID}${VP_SUFFIX}-v*-full.png 2>/dev/null | \
    sed -n "s/.*-v\([0-9]*\)-full\.png/\1/p" | sort -n | tail -1)
  ITERATION=$(( ${EXISTING:-0} + 1 ))
fi

BASE_NAME="${PAGE_ID}${VP_SUFFIX}-v${ITERATION}"
FULL_PATH="${SCREENSHOTS_DIR}/${BASE_NAME}-full.png"
CHUNK_BASE="${SCREENSHOTS_DIR}/${BASE_NAME}"

echo "=== Visual Verification: ${PAGE_ID} (${VIEWPORT}) ==="
echo "  Route:      ${ROUTE}"
echo "  Viewport:   ${VP_WIDTH}x${VP_HEIGHT}"
echo "  Iteration:  ${ITERATION}"
echo "  Output:     ${FULL_PATH}"
echo ""

# Step 1: Ensure dev server is running
echo "── Step 1: Check dev server ──"
if lsof -i ":${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "  Dev server already running on port ${PORT}"
else
  echo "  Starting dev server..."
  (cd "$PROJECT_DIR" && npm run dev &) 2>/dev/null
  sleep 5
  if ! lsof -i ":${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "  ERROR: Dev server failed to start on port ${PORT}" >&2
    exit 1
  fi
  echo "  Dev server started"
fi

# Step 2: Set viewport and navigate
echo "── Step 2: Navigate to page ──"
if [ "$VIEWPORT" != "desktop" ]; then
  # Close and reopen with specific viewport for non-desktop
  agent-browser close 2>/dev/null || true
  agent-browser --viewport "${VP_WIDTH}x${VP_HEIGHT}" open "http://localhost:${PORT}${ROUTE}"
else
  agent-browser open "http://localhost:${PORT}${ROUTE}"
fi

# Step 3: Wait for full load
echo "── Step 3: Wait for page load ──"
agent-browser wait --load networkidle

# Step 4: Full-page screenshot
echo "── Step 4: Full-page screenshot ──"
agent-browser screenshot --full "$FULL_PATH"

if [ ! -f "$FULL_PATH" ]; then
  echo "  ERROR: Screenshot not saved at ${FULL_PATH}" >&2
  exit 1
fi

FILE_SIZE=$(du -h "$FULL_PATH" | cut -f1)
echo "  Saved: ${FULL_PATH} (${FILE_SIZE})"

# Step 5: Chunk for vision analysis
echo "── Step 5: Chunk for vision ──"
RESIZE_SCRIPT="${SKILL_PATH}/scripts/resize_screenshot.py"
if [ -f "$RESIZE_SCRIPT" ]; then
  python3 "$RESIZE_SCRIPT" "$FULL_PATH" "$CHUNK_BASE" --mode chunk
else
  echo "  WARNING: resize_screenshot.py not found at ${RESIZE_SCRIPT}" >&2
  echo "  Could not chunk. Analyze the full screenshot directly."
fi

# List output files
echo ""
echo "── Chunks ready for vision analysis ──"
CHUNKS=$(ls "${CHUNK_BASE}"-*.jpg 2>/dev/null | sort)
CHUNK_COUNT=$(echo "$CHUNKS" | grep -c . 2>/dev/null || echo 0)

if [ "$CHUNK_COUNT" -gt 0 ]; then
  echo "  ${CHUNK_COUNT} chunks generated:"
  echo "$CHUNKS" | while read -r chunk; do
    echo "    → Read $chunk"
  done
else
  echo "  No chunks generated. Analyze the full screenshot:"
  echo "    → Read ${FULL_PATH}"
fi

echo ""
echo "══════════════════════════════════════════════════════"
echo "  ACTION REQUIRED: Read and analyze each chunk above."
echo "  Check: layout, content, colors, CTAs, visual hierarchy."
echo "  Then update state:"
echo "    python state_manager.py --action add-verification \\"
echo "      --page-id ${PAGE_ID} --result pass|fail \\"
echo "      --screenshot ${FULL_PATH} \\"
echo "      --notes 'Your analysis here'"
echo "══════════════════════════════════════════════════════"
