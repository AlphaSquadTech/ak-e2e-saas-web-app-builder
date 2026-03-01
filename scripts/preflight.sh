#!/usr/bin/env bash
# Preflight check for ak-e2e-saas-web-app-builder
#
# Run this BEFORE starting any build. It ensures all companion skills
# and system dependencies are installed and ready.
#
# Usage: bash preflight.sh [--skip-skills] [--skip-deps]
#
# Exit codes:
#   0 = all checks passed
#   1 = critical failure (cannot proceed)
#   2 = non-critical warnings (can proceed with degraded capability)

set -euo pipefail

YELLOW='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

WARNINGS=0
ERRORS=0

ok()   { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; WARNINGS=$((WARNINGS + 1)); }
fail() { echo -e "${RED}✗${NC} $1"; ERRORS=$((ERRORS + 1)); }

SKIP_SKILLS=false
SKIP_DEPS=false

for arg in "$@"; do
  case $arg in
    --skip-skills) SKIP_SKILLS=true ;;
    --skip-deps)   SKIP_DEPS=true ;;
  esac
done

echo "=== Preflight Check: ak-e2e-saas-web-app-builder ==="
echo ""

# ─── 1. Companion Skills ─────────────────────────────────────────────

echo "── Companion Skills ──"

if [ "$SKIP_SKILLS" = true ]; then
  warn "Skipping skill installation (--skip-skills)"
else
  # Check if npx/skills CLI is available
  if command -v npx &>/dev/null; then
    # Install companion skills (idempotent — safe to re-run)
    for skill_spec in \
      "giuseppe-trisciuoglio/developer-kit --skill shadcn-ui" \
      "wshobson/agents --skill interaction-design" \
      "vercel-labs/agent-browser"; do

      display_name="$skill_spec"
      install_cmd="npx skills add $skill_spec"

      echo -n "  Installing $display_name ... "
      if $install_cmd 2>/dev/null; then
        ok "installed"
      else
        warn "failed to install $display_name (will use bundled fallback)"
      fi
    done
  else
    warn "npx not found — cannot install companion skills (will use bundled fallbacks)"
  fi
fi

echo ""

# ─── 2. System Dependencies ──────────────────────────────────────────

echo "── System Dependencies ──"

if [ "$SKIP_DEPS" = true ]; then
  warn "Skipping dependency checks (--skip-deps)"
else
  # Node.js (required)
  if command -v node &>/dev/null; then
    NODE_VERSION=$(node --version)
    ok "Node.js $NODE_VERSION"
    # Check minimum version (18+)
    MAJOR=$(echo "$NODE_VERSION" | sed 's/v//' | cut -d. -f1)
    if [ "$MAJOR" -lt 18 ]; then
      warn "Node.js 18+ recommended (found $NODE_VERSION)"
    fi
  else
    fail "Node.js not found (required)"
  fi

  # npm (required)
  if command -v npm &>/dev/null; then
    ok "npm $(npm --version)"
  else
    fail "npm not found (required)"
  fi

  # Python 3 (required for scripts)
  if command -v python3 &>/dev/null; then
    ok "Python $(python3 --version 2>&1 | cut -d' ' -f2)"
  else
    fail "Python 3 not found (required for state_manager.py and parse_openapi.py)"
  fi

  # Pillow (recommended for screenshot resizing)
  if python3 -c "import PIL" 2>/dev/null; then
    ok "Pillow (Python image processing)"
  else
    echo -n "  Installing Pillow ... "
    if pip install Pillow --break-system-packages -q 2>/dev/null || pip3 install Pillow --break-system-packages -q 2>/dev/null; then
      ok "Pillow installed"
    else
      warn "Pillow not installed (screenshot resizing will try ImageMagick or ffmpeg instead)"
    fi
  fi

  # PyYAML (needed for OpenAPI spec parsing)
  if python3 -c "import yaml" 2>/dev/null; then
    ok "PyYAML (OpenAPI spec parsing)"
  else
    echo -n "  Installing PyYAML ... "
    if pip install pyyaml --break-system-packages -q 2>/dev/null || pip3 install pyyaml --break-system-packages -q 2>/dev/null; then
      ok "PyYAML installed"
    else
      warn "PyYAML not installed (install manually: pip install pyyaml)"
    fi
  fi

  # google-genai SDK (needed for image generation)
  if python3 -c "import google.genai" 2>/dev/null; then
    ok "google-genai (Gemini image API)"
  else
    echo -n "  Installing google-genai ... "
    if pip install google-genai --break-system-packages -q 2>/dev/null || pip3 install google-genai --break-system-packages -q 2>/dev/null; then
      ok "google-genai installed"
    else
      warn "google-genai not installed (image generation will be unavailable — install manually: pip install google-genai)"
    fi
  fi

  # Check for Gemini API key (env var or state file)
  if [ -n "${GEMINI_API_KEY:-}" ] || [ -n "${GOOGLE_API_KEY:-}" ]; then
    ok "Gemini API key found (environment variable)"
  elif [ -f ".nextjs-builder-state.json" ] && python3 -c "
import json, sys
key = json.load(open('.nextjs-builder-state.json')).get('design_inputs',{}).get('gemini_api_key','')
sys.exit(0 if key else 1)
" 2>/dev/null; then
    ok "Gemini API key found (saved in state file)"
  else
    warn "No Gemini API key found. Ask the user for their key (or get one from https://aistudio.google.com/apikey)"
  fi

  # agent-browser CLI (required for visual verification)
  if command -v agent-browser &>/dev/null; then
    ok "agent-browser CLI"
  elif npx agent-browser --version &>/dev/null 2>&1; then
    ok "agent-browser (via npx)"
  else
    warn "agent-browser CLI not found (install globally: npm install -g agent-browser)"
  fi

  # create-next-app (needed for scaffolding)
  if npx create-next-app --version &>/dev/null 2>&1; then
    ok "create-next-app (via npx)"
  else
    warn "create-next-app not reachable via npx (may need internet for Phase 1)"
  fi

  # Note about framer-motion
  echo "Note: framer-motion will be installed during project scaffolding"
fi

echo ""

# ─── 3. Environment ──────────────────────────────────────────────────

echo "── Environment ──"

# Check if we're in a git repo (helpful but not required)
if git rev-parse --is-inside-work-tree &>/dev/null 2>&1; then
  ok "Inside a git repository"
else
  warn "Not in a git repo (commits won't be tracked)"
fi

# Check for existing state file (resume scenario)
if [ -f ".nextjs-builder-state.json" ]; then
  PHASE=$(python3 -c "import json; print(json.load(open('.nextjs-builder-state.json'))['current_phase'])" 2>/dev/null || echo "unknown")
  PAGES=$(python3 -c "import json; s=json.load(open('.nextjs-builder-state.json')); print(f\"{sum(1 for p in s['pages'] if p['status']=='verified')}/{len(s['pages'])}\")" 2>/dev/null || echo "?/?")
  ok "Existing state file found (phase: $PHASE, pages verified: $PAGES)"
else
  ok "No existing state file (fresh start)"
fi

echo ""

# ─── Summary ──────────────────────────────────────────────────────────

echo "── Summary ──"
if [ "$ERRORS" -gt 0 ]; then
  fail "$ERRORS critical issue(s) found. Fix these before proceeding."
  exit 1
elif [ "$WARNINGS" -gt 0 ]; then
  warn "$WARNINGS warning(s). Can proceed with reduced capability."
  exit 2
else
  ok "All checks passed. Ready to build!"
  exit 0
fi
