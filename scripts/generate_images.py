#!/usr/bin/env python3
"""Generate real images from an image manifest using the Gemini API.

Reads image-manifest.json and calls the Gemini API via the google-genai SDK to
generate images from prompts, replacing SVG placeholders with real AI-generated images.

Dependencies: google-genai, Pillow

Usage:
    python generate_images.py [--manifest image-manifest.json] [--dry-run] [--delay 2]
                              [--only <image-id>] [--retry-failed]
                              [--model gemini-3.1-flash-image-preview]
                              [--style <style>]

Options:
    --manifest      Path to the image manifest (default: image-manifest.json)
    --dry-run       Print prompts without calling API
    --delay         Seconds between API calls (default: 2)
    --only          Generate a single image by ID
    --retry-failed  Also retry entries with status 'failed'
    --model         Model override (default: gemini-3.1-flash-image-preview)
    --style         Global style override (photorealistic, watercolor, oil-painting,
                    sketch, pixel-art, anime, vintage, modern, abstract, minimalist)

Environment Variables:
    GEMINI_API_KEY or GOOGLE_API_KEY  — Required for API access
    IMAGE_MODEL                       — Optional model name override
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

# ── Supported styles ────────────────────────────────────────────────────────
SUPPORTED_STYLES = [
    "photorealistic",
    "watercolor",
    "oil-painting",
    "sketch",
    "pixel-art",
    "anime",
    "vintage",
    "modern",
    "abstract",
    "minimalist",
]

# ── Supported aspect ratios (Gemini image model) ───────────────────────────
SUPPORTED_ASPECT_RATIOS = [
    "1:1", "9:16", "16:9", "3:4", "4:3",
    "3:2", "2:3", "5:4", "4:5", "21:9",
]


def check_api_key():
    """Check that an API key is available. Returns the key or exits."""
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        print("Error: No API key found.", file=sys.stderr)
        print("  Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable.", file=sys.stderr)
        print("  Get a key from https://aistudio.google.com/apikey", file=sys.stderr)
        sys.exit(1)
    return key


def _closest_aspect_ratio(w: int, h: int) -> str:
    """Find the closest supported aspect ratio for given dimensions."""
    target = w / h
    best_ratio = ""
    best_diff = float("inf")
    for ratio_str in SUPPORTED_ASPECT_RATIOS:
        rw, rh = map(int, ratio_str.split(":"))
        diff = abs(target - rw / rh)
        if diff < best_diff:
            best_diff = diff
            best_ratio = ratio_str
    return best_ratio


def build_prompt(entry: dict, global_style: str = None) -> str:
    """Build a complete image generation prompt from a manifest entry.

    Embeds aspect ratio, style, brand context, and text rendering hints
    directly into the prompt text (Gemini image models read these from
    the prompt rather than separate parameters).
    """
    parts = []

    # Core description
    core_prompt = entry["prompt"]
    parts.append(core_prompt)

    # Aspect ratio (embedded in prompt — Gemini reads this from text)
    dims = entry.get("dimensions", {})
    aspect_ratio = entry.get("aspect_ratio", "")
    if not aspect_ratio and dims.get("width") and dims.get("height"):
        aspect_ratio = _closest_aspect_ratio(dims["width"], dims["height"])
    if aspect_ratio:
        parts.append(f"Generate this image with an aspect ratio of {aspect_ratio}.")

    # Style directive (per-entry or global override)
    style = global_style or entry.get("style", "")
    if style:
        parts.append(f"Visual style: {style}.")

    # Brand context
    brand = entry.get("brand", {})
    if brand.get("accent_color"):
        parts.append(
            f"Use a color palette that harmonizes with the brand color {brand['accent_color']}."
        )
    if brand.get("mood"):
        parts.append(f"The overall mood should be: {brand['mood']}.")

    # Text rendering hints (auto-detect text keywords in prompt)
    prompt_lower = core_prompt.lower()
    has_text_request = any(
        kw in prompt_lower
        for kw in ["text", "says", "reads", "label", "title", "heading", "sign", "banner", "logo"]
    )
    if has_text_request:
        if brand.get("font"):
            parts.append(
                f"For any text in the image, use a {brand['font']}-like clean typeface. "
                "Ensure text is crisp, legible, and properly spelled."
            )
        else:
            parts.append(
                "Ensure any text in the image is crisp, legible, and properly spelled."
            )

    # Quality
    parts.append("High quality, professional, suitable for a marketing website.")

    return " ".join(parts)


def generate_image(entry: dict, model: str, global_style: str = None) -> str:
    """Generate an image from a manifest entry using the Gemini API. Returns output path."""
    from google import genai
    from PIL import Image as PILImage

    # The client authenticates using the GEMINI_API_KEY environment variable
    client = genai.Client()
    prompt = build_prompt(entry, global_style=global_style)

    response = client.models.generate_content(
        model=model,
        contents=[prompt],
    )

    output_path = entry["path"]
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    for part in response.parts:
        if part.inline_data is not None:
            img = part.as_image()

            # Resize if dimensions specified
            dims = entry.get("dimensions", {})
            target_w = dims.get("width")
            target_h = dims.get("height")
            if target_w and target_h:
                if img.size != (target_w, target_h):
                    img = img.resize((target_w, target_h), PILImage.LANCZOS)

            # Save in the appropriate format
            if output_path.lower().endswith(".webp"):
                img.save(output_path, "WebP", quality=90)
            elif output_path.lower().endswith((".jpg", ".jpeg")):
                if img.mode == "RGBA":
                    img = img.convert("RGB")
                img.save(output_path, "JPEG", quality=90)
            else:
                img.save(output_path)

            return output_path

        elif part.text is not None:
            # Model returned text (possibly a safety warning)
            print(f"  Model message: {part.text[:200]}")

    raise RuntimeError("No image returned by the model")


def save_manifest(manifest: dict, path: str):
    """Atomically write the manifest back to disk."""
    tmp_path = path + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(manifest, f, indent=2)
    os.replace(tmp_path, path)


def now_iso() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def main():
    parser = argparse.ArgumentParser(
        description="Generate images from manifest using the Gemini API"
    )
    parser.add_argument(
        "--manifest",
        default="image-manifest.json",
        help="Path to the image manifest (default: image-manifest.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompts without calling API",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2,
        help="Seconds between API calls (default: 2)",
    )
    parser.add_argument(
        "--only",
        metavar="IMAGE_ID",
        help="Generate a single image by ID",
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Also retry entries with status 'failed'",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("IMAGE_MODEL", "gemini-3.1-flash-image-preview"),
        help="Model name (default: gemini-3.1-flash-image-preview)",
    )
    parser.add_argument(
        "--style",
        choices=SUPPORTED_STYLES,
        default=None,
        help="Global style override applied to all images",
    )
    args = parser.parse_args()

    # Check API key (skip for dry run)
    if not args.dry_run:
        check_api_key()

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

    # Filter eligible entries
    eligible_statuses = {"placeholder"}
    if args.retry_failed:
        eligible_statuses.add("failed")

    candidates = []
    for entry in images:
        if args.only and entry.get("id") != args.only:
            continue
        if entry.get("status") in eligible_statuses:
            candidates.append(entry)

    # Sort by priority
    candidates.sort(key=lambda e: PRIORITY_ORDER.get(e.get("priority", "medium"), 1))

    if not candidates:
        print("No eligible images to generate.")
        if args.only:
            print(f"  (--only {args.only} didn't match any eligible entry)")
        return

    total = len(candidates)
    generated = 0
    failed = 0

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Generating {total} image(s) with {args.model}")
    if args.style:
        print(f"  Global style: {args.style}")
    print()

    for i, entry in enumerate(candidates, 1):
        entry_id = entry.get("id", "unknown")
        alt_text = entry.get("alt", "")[:60]
        print(f"[{i}/{total}] {entry_id}: {alt_text}")

        prompt = build_prompt(entry, global_style=args.style)

        if args.dry_run:
            print(f"  Prompt: {prompt}")
            ratio = entry.get("aspect_ratio", "auto")
            style = args.style or entry.get("style", "none")
            print(f"  Aspect ratio: {ratio} | Style: {style}")
            print()
            continue

        try:
            output_path = generate_image(entry, model=args.model, global_style=args.style)
            entry["status"] = "generated"
            entry["generated_at"] = now_iso()
            entry["error"] = None
            generated += 1
            print(f"  ✓ Saved: {output_path}")

        except Exception as e:
            error_str = str(e)

            # Check for rate limit — retry once after 30s
            if "rate" in error_str.lower() or "429" in error_str:
                print("  Rate limited. Waiting 30s and retrying...")
                time.sleep(30)
                try:
                    output_path = generate_image(entry, model=args.model, global_style=args.style)
                    entry["status"] = "generated"
                    entry["generated_at"] = now_iso()
                    entry["error"] = None
                    generated += 1
                    print(f"  ✓ Saved (retry): {output_path}")
                except Exception as retry_e:
                    entry["status"] = "failed"
                    entry["error"] = str(retry_e)
                    failed += 1
                    print(f"  ✗ Failed (after retry): {retry_e}")

            # Check for network error — retry once after 5s
            elif "network" in error_str.lower() or "connection" in error_str.lower():
                print("  Network error. Retrying in 5s...")
                time.sleep(5)
                try:
                    output_path = generate_image(entry, model=args.model, global_style=args.style)
                    entry["status"] = "generated"
                    entry["generated_at"] = now_iso()
                    entry["error"] = None
                    generated += 1
                    print(f"  ✓ Saved (retry): {output_path}")
                except Exception as retry_e:
                    entry["status"] = "failed"
                    entry["error"] = str(retry_e)
                    failed += 1
                    print(f"  ✗ Failed (after retry): {retry_e}")

            # Safety filter or other error
            else:
                if "safety" in error_str.lower() or "block" in error_str.lower():
                    entry["status"] = "failed"
                    entry["error"] = f"safety_filter: {error_str}"
                    print("  ✗ Blocked by safety filter")
                else:
                    entry["status"] = "failed"
                    entry["error"] = error_str
                    print(f"  ✗ Failed: {error_str}")
                failed += 1

        # Save manifest after each image (progress survives interruption)
        save_manifest(manifest, args.manifest)

        # Delay between calls
        if i < total and not args.dry_run:
            time.sleep(args.delay)

    # Summary
    skipped = total - generated - failed
    print(f"\nSummary: {generated} generated, {failed} failed, {skipped} skipped")


if __name__ == "__main__":
    main()
