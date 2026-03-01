#!/usr/bin/env python3
"""Generate branded SVG placeholder images from an image manifest.

Reads image-manifest.json and creates SVG placeholders for each entry.
Placeholders use the site's accent color and show the alt text + dimensions,
so the site looks cohesive during development and visual verification.

Usage:
    python generate_placeholders.py [--manifest image-manifest.json] [--force]

Options:
    --manifest  Path to the image manifest (default: image-manifest.json)
    --force     Regenerate even if placeholder file already exists
"""

import argparse
import json
import os
import sys


SVG_TEMPLATE = """\
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <style>
      .bg {{ fill: #f3f4f6; }}
      .accent {{ fill: {accent_color}; opacity: 0.08; }}
      .border {{ stroke: {accent_color}; stroke-width: 2; fill: none; opacity: 0.3; }}
      .icon {{ fill: {accent_color}; opacity: 0.25; }}
      .label {{ font-family: system-ui, -apple-system, sans-serif; fill: #374151; text-anchor: middle; }}
      .dims {{ font-family: system-ui, -apple-system, sans-serif; fill: #9ca3af; text-anchor: middle; font-size: 14px; }}
    </style>
  </defs>
  <rect class="bg" width="{width}" height="{height}" rx="4"/>
  <rect class="accent" width="{width}" height="{height}" rx="4"/>
  <rect class="border" x="1" y="1" width="{border_w}" height="{border_h}" rx="4"/>
  <!-- Camera/image icon centered above text -->
  <g transform="translate({cx}, {icon_y})">
    <path class="icon" d="M-20,-16 L-14,-16 L-10,-22 L10,-22 L14,-16 L20,-16 L20,14 L-20,14 Z" />
    <circle class="icon" cx="0" cy="0" r="8" style="fill:none; stroke:{accent_color}; stroke-width:2; opacity:0.25;"/>
  </g>
  <text class="label" x="{cx}" y="{label_y}" font-size="{label_font_size}">{alt_text}</text>
  <text class="dims" x="{cx}" y="{dims_y}">{width} × {height}</text>
</svg>"""


def truncate_text(text: str, max_len: int = 60) -> str:
    """Truncate text with ellipsis if too long. Also escape XML entities."""
    if len(text) > max_len:
        text = text[:max_len - 3] + "..."
    # Escape XML special characters
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace('"', "&quot;").replace("'", "&apos;")
    return text


def generate_svg(entry: dict) -> str:
    """Generate an SVG placeholder string from a manifest entry."""
    dims = entry.get("dimensions", {})
    width = dims.get("width", 800)
    height = dims.get("height", 400)

    # Get accent color from brand or fallback
    brand = entry.get("brand", {})
    accent_color = brand.get("accent_color", "#6b7280")

    # Calculate positions
    cx = width / 2
    cy = height / 2
    icon_y = cy - 40
    label_y = cy + 16
    dims_y = cy + 40

    # Scale font size based on width
    label_font_size = max(14, min(20, width / 40))

    alt_text = truncate_text(entry.get("alt", entry.get("id", "Image")))

    return SVG_TEMPLATE.format(
        width=width,
        height=height,
        border_w=width - 2,
        border_h=height - 2,
        accent_color=accent_color,
        cx=int(cx),
        icon_y=int(icon_y),
        label_y=int(label_y),
        dims_y=int(dims_y),
        label_font_size=int(label_font_size),
        alt_text=alt_text,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate branded SVG placeholder images from an image manifest"
    )
    parser.add_argument(
        "--manifest",
        default="image-manifest.json",
        help="Path to the image manifest (default: image-manifest.json)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if placeholder file already exists",
    )
    args = parser.parse_args()

    # Read manifest
    if not os.path.exists(args.manifest):
        print(f"Error: Manifest not found: {args.manifest}", file=sys.stderr)
        sys.exit(1)

    with open(args.manifest) as f:
        manifest = json.load(f)

    images = manifest.get("images", [])
    if not images:
        print("No images in manifest. Nothing to do.")
        return

    generated = 0
    skipped = 0

    for entry in images:
        status = entry.get("status", "")
        if status not in ("placeholder", "pending"):
            skipped += 1
            continue

        placeholder_path = entry.get("placeholder")
        if not placeholder_path:
            print(f"  Warning: Entry '{entry.get('id', '?')}' has no placeholder path, skipping")
            skipped += 1
            continue

        # Skip if exists and not --force
        if os.path.exists(placeholder_path) and not args.force:
            print(f"  Skip (exists): {placeholder_path}")
            skipped += 1
            continue

        # Create parent directories
        os.makedirs(os.path.dirname(placeholder_path) or ".", exist_ok=True)

        # Generate and write SVG
        svg_content = generate_svg(entry)
        with open(placeholder_path, "w") as f:
            f.write(svg_content)

        print(f"  Created: {placeholder_path}")
        generated += 1

    print(f"\nSummary: {generated} placeholders generated, {skipped} skipped")


if __name__ == "__main__":
    main()
