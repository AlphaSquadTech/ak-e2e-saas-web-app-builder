# Image Generation Guide

The skill cannot generate images itself. Instead, it uses a two-stage pipeline:

1. **Placeholders** — branded SVGs that look intentional, not broken
2. **AI generation** — Gemini API (`gemini-3.1-flash-image-preview`) fills in real images from prompts

## The Image Manifest

Every image the site needs is tracked in `image-manifest.json` in the project root.
This file is the bridge between site building and image generation.

### When to Add Manifest Entries

During Phase 2 (Build), every time you add an `<Image>` tag or reference an image path
in a page component, also add a corresponding entry to the manifest. Common image types for SaaS:

| Image Type | Typical Dimensions | Use In SaaS |
|------------|-------------------|-------------|
| Empty state illustration | 400×300 | List pages with no data |
| Onboarding graphic | 600×400 | First-time user experience |
| Avatar placeholder | 80×80 | User/team member avatars |
| Feature illustration | 400×400 | Settings or about sections |
| Dashboard background | 1200×200 | Dashboard hero/banner area |
| Error state illustration | 400×300 | Error pages (404, 500) |
| Login background | 1920×1080 | Auth page background |

### Supported Aspect Ratios

The Gemini image model supports these aspect ratios (embedded in the prompt):
`1:1`, `9:16`, `16:9`, `3:4`, `4:3`, `3:2`, `2:3`, `5:4`, `4:5`, `21:9`

If your image dimensions don't match one exactly, the script auto-selects the closest
supported ratio. Prefer using standard ratios when defining image dimensions.

### Supported Styles

These visual styles can be applied per-image (in the manifest `style` field) or
globally via the `--style` flag:

| Style | Best For |
|-------|----------|
| `photorealistic` | Hero images, product shots, lifestyle photos |
| `watercolor` | Artistic, warm illustrations |
| `oil-painting` | Premium, textured artwork |
| `sketch` | Technical diagrams, wireframes, hand-drawn feel |
| `pixel-art` | Retro, gaming, playful themes |
| `anime` | Bold, character-driven illustrations |
| `vintage` | Nostalgic, classic aesthetics |
| `modern` | Clean, contemporary design |
| `abstract` | Backgrounds, patterns, conceptual art |
| `minimalist` | Icons, subtle illustrations, clean design |

### Text Rendering in Images

Gemini can render text in generated images. The script auto-detects text requests
in prompts (keywords like "text", "says", "sign", "banner", "logo") and adds
text rendering quality hints. For best results:

- **Be explicit**: Write `with text that says "ACME Corp"` rather than vague references
- **Limit text length**: Short phrases (1-4 words) render most reliably
- **Specify prominence**: "large bold heading", "small subtle caption", etc.
- **Font matching**: The script auto-adds font hints from the `brand.font` field

### Writing Good Prompts

The `prompt` field is what gets sent to Gemini. Write it as a clear, specific
image description. Include:

- **Subject**: What is in the image ("a modern SaaS dashboard", "a team collaboration scene")
- **Composition**: How it's arranged ("centered product on white background", "isometric view")
- **Style**: Visual treatment (or rely on the `style` field for standard styles)
- **Mood**: Emotional tone ("professional and clean", "warm and friendly", "bold and energetic")
- **Constraints**: What to avoid ("no text", "no people", "minimal detail")

Do NOT include brand color, font, or aspect ratio instructions in the prompt field —
those come from the `brand` object, `style` field, and `dimensions`/`aspect_ratio`
fields and are appended automatically by `generate_images.py`.

**Good prompt:**
"A modern SaaS dashboard showing analytics charts, user metrics, and recent activity with clean interface design in isometric view"

**Bad prompt:**
"Make a nice dashboard image for the app"

### Deriving Brand Context

The `brand` object in each manifest entry is derived from the state file's `design_inputs`:

```
design_inputs.accent_color → brand.accent_color
design_inputs.font_preference → brand.font (resolved to actual font name)
Document subject matter → brand.mood
```

Mood mapping by document type:
- SaaS/tech → "professional, modern, trustworthy"
- Finance → "authoritative, precise, reliable"
- Creative/agency → "bold, expressive, dynamic"
- Luxury/premium → "sophisticated, elegant, refined"
- Health/wellness → "calm, natural, nurturing"
- Education → "approachable, clear, inspiring"

## Stage 1: Generating Placeholders

After adding entries to the manifest during page implementation:

```bash
python <skill-path>/scripts/generate_placeholders.py --manifest image-manifest.json
```

This creates branded SVGs at each entry's `placeholder` path. The site code should
reference the placeholder path initially:

```tsx
import Image from 'next/image'

{/* During build, this points to the placeholder SVG */}
<Image
  src="/images/placeholders/empty-state.svg"
  alt="No data available - get started by adding your first item"
  width={400}
  height={300}
  priority
/>
```

The visual verification step will see branded placeholders — gray boxes with the accent
color tint, the alt text label, and dimensions. This is enough to verify layout, spacing,
and visual hierarchy.

## Stage 2: Generating Real Images with Gemini API

After all pages are built and verified with placeholders (end of Phase 2 or start of Phase 3):

### Prerequisites

1. **google-genai SDK**:
   ```bash
   pip install google-genai --break-system-packages
   ```

2. **Pillow** (for image resizing/conversion):
   ```bash
   pip install Pillow --break-system-packages
   ```

3. **API Key** — Should already be saved in the state file from Phase 1 design inputs.
   Export it before running the script:
   ```bash
   # Load from state file (saved when user provided it during design inputs)
   export GEMINI_API_KEY="$(python3 -c "import json; print(json.load(open('.nextjs-builder-state.json'))['design_inputs'].get('gemini_api_key',''))")"
   ```
   If the key is not in the state file, ask the user for it now. They can get one from
   https://aistudio.google.com/apikey. Save it to `design_inputs.gemini_api_key` in the
   state file so it persists for future sessions.

### How It Works

The script uses the `google-genai` Python SDK to call the Gemini API directly.
For each manifest entry it:

1. Constructs a rich prompt from the entry's fields (description, aspect ratio, style,
   brand context, text rendering hints)
2. Calls `client.models.generate_content(model="gemini-3.1-flash-image-preview", ...)`
3. Extracts the inline image data from the response via `part.as_image()`
4. Resizes to target dimensions if specified, and saves in the correct format

Prompt construction is automatic — the script reads each manifest entry and builds
a rich prompt that includes the core description, aspect ratio, visual style, brand
context (accent color, mood), and text rendering hints (auto-detected from keywords).

### Dry Run First (Recommended)

```bash
python <skill-path>/scripts/generate_images.py --manifest image-manifest.json --dry-run
```

This prints every constructed prompt without calling the API. Review them for quality
before spending credits.

### Generate All Images

```bash
python <skill-path>/scripts/generate_images.py --manifest image-manifest.json
```

### Generate a Single Image

```bash
python <skill-path>/scripts/generate_images.py --manifest image-manifest.json --only empty-state
```

### Retry Failed Images

```bash
python <skill-path>/scripts/generate_images.py --manifest image-manifest.json --retry-failed
```

### Apply a Global Style

```bash
python <skill-path>/scripts/generate_images.py --manifest image-manifest.json --style minimalist
```

This overrides the `style` field on all entries. Useful for creating a cohesive visual
language across all images.

### Cost Estimate

`gemini-3.1-flash-image-preview` pricing:
- ~$0.045 per image at 512px
- ~$0.067 per image at 1024px
- ~$0.101 per image at 2048px

A typical SaaS app (5-10 images) costs $0.30–$1.00 total.

## Stage 3: Swap Placeholders for Real Images

After generation, update all `<Image>` `src` attributes to point to the real image paths
instead of the placeholder paths. This can be done with a find-and-replace:

```bash
# In the project's src/ directory, replace placeholder paths with real paths
# For each manifest entry:
#   /images/placeholders/empty-state.svg  →  /images/empty-state.webp
```

Alternatively, build a helper component that checks if the real image exists and falls
back to the placeholder:

```tsx
// components/site-image.tsx
import Image, { ImageProps } from 'next/image'
import fs from 'fs'
import path from 'path'

interface SiteImageProps extends Omit<ImageProps, 'src'> {
  imageId: string
  src: string
  placeholderSrc: string
}

export function SiteImage({ imageId, src, placeholderSrc, ...props }: SiteImageProps) {
  // In production, always use the real path (placeholder should have been replaced)
  // During dev, this lets both work
  const realPath = path.join(process.cwd(), 'public', src)
  const resolvedSrc = fs.existsSync(realPath) ? src : placeholderSrc
  return <Image src={resolvedSrc} {...props} />
}
```

## Using Alternative Image Generators

The manifest is tool-agnostic. If you want to use a different generator:

- **DALL-E / OpenAI**: Read the manifest, call the OpenAI images API with the prompt field.
- **Human designer**: Hand the manifest to a designer — it contains all the specs they need.
- **Stock photos**: Use the `alt` and `prompt` fields as search terms on stock photo sites.

The manifest is the contract. The generation tool is swappable.
