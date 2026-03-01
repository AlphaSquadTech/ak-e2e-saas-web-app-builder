#!/usr/bin/env bash
# Initialize a NextJS project optimized for SaaS applications.
#
# Usage: bash init_project.sh <project-name>
#
# Creates a NextJS project with:
# - App Router + TypeScript
# - Tailwind CSS
# - ESLint
# - SaaS-optimized folder structure

set -euo pipefail

PROJECT_NAME="${1:?Usage: bash init_project.sh <project-name>}"

echo "==> Creating NextJS project: $PROJECT_NAME"

# Create the project non-interactively
npx create-next-app@latest "$PROJECT_NAME" \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --src-dir \
  --import-alias "@/*" \
  --no-turbopack \
  --yes

cd "$PROJECT_NAME"

echo "==> Creating SaaS application directory structure"

# Create directory structure
mkdir -p src/components/ui
mkdir -p src/components/layout
mkdir -p src/components/shared
mkdir -p src/components/resources
mkdir -p src/lib
mkdir -p src/lib/mock-data
mkdir -p public/images/placeholders
mkdir -p public/images/empty-states
mkdir -p screenshots

echo "==> Creating not-found.tsx"
cat > src/app/not-found.tsx << 'NOTFOUND_EOF'
import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 px-4">
      <h1 className="text-6xl font-bold tracking-tight">404</h1>
      <p className="text-lg text-muted-foreground">This page could not be found.</p>
      <Link
        href="/"
        className="mt-4 inline-flex items-center rounded-md bg-primary px-6 py-3 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
      >
        Go back home
      </Link>
    </div>
  )
}
NOTFOUND_EOF

echo "==> Creating utility helpers"
cat > src/lib/utils.ts << 'UTILS_EOF'
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
UTILS_EOF

# Install clsx and tailwind-merge for the cn utility
npm install clsx tailwind-merge

echo "==> Creating .env.local template"
cat > .env.local << 'ENV_EOF'
NEXT_PUBLIC_BASE_URL=http://localhost:3000
ENV_EOF

echo "==> Creating empty image manifest"
cat > image-manifest.json << 'MANIFEST_EOF'
{
  "_schema_version": "1.0.0",
  "_description": "Image manifest for AI generation. Entries added during Phase 2 build.",
  "project_name": "",
  "accent_color": "",
  "font_preference": "",
  "images": []
}
MANIFEST_EOF

echo "==> Creating .gitignore additions"
cat >> .gitignore << 'GITIGNORE_EOF'

# Builder state
.nextjs-builder-state.json

# Screenshots (optional: remove this line if you want to track them)
screenshots/

# Image manifest (build state)
image-manifest.json
GITIGNORE_EOF

echo "==> Generating AI context files"
if [ -f "$(dirname "$0")/generate_context_file.sh" ]; then
  bash "$(dirname "$0")/generate_context_file.sh" --project-dir . --skill-path "$(dirname "$0")/.."
else
  echo "  WARNING: generate_context_file.sh not found. Create CLAUDE.md manually."
fi

echo ""
echo "==> SaaS project '$PROJECT_NAME' created successfully!"
echo "    cd $PROJECT_NAME && npm run dev"
echo ""
