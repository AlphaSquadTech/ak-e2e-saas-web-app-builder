#!/usr/bin/env python3
"""Resize and chunk screenshots for Claude's Vision API.

Claude's vision works best with images between 200-1568 pixels on each edge.
Images larger than 1568px get downscaled server-side, adding latency without
improving analysis quality. Max file size is 5MB.

Two modes:
  resize (default) — Shrink a single image to fit within max dimensions.
  chunk            — Slice a tall full-page screenshot into viewport-sized
                     chunks, each resized to fit within Vision API limits.
                     Outputs numbered files: output-001.jpg, output-002.jpg, ...

Usage:
    # Resize a single image
    python resize_screenshot.py screenshot.png screenshot-resized.jpg

    # Chunk a tall full-page screenshot into viewport-sized pieces
    python resize_screenshot.py page-full.png screenshots/page --mode chunk

    # Chunk with custom height per chunk (default 900px)
    python resize_screenshot.py page-full.png screenshots/page --mode chunk --chunk-height 800

Examples:
    python resize_screenshot.py screenshot.png screenshot-resized.jpg
    python resize_screenshot.py screenshot.png screenshot-small.jpg --max-dimension 1024
    python resize_screenshot.py page-full.png screenshots/home --mode chunk
    python resize_screenshot.py page-full.png screenshots/home --mode chunk --chunk-height 1200 --overlap 100
"""

import argparse
import json
import sys
import os


def save_image(img, output_path: str, quality: int):
    """Save a PIL Image to disk with format auto-detection and size enforcement."""
    # Convert RGBA to RGB if saving as JPEG
    if output_path.lower().endswith(('.jpg', '.jpeg')) and img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    if output_path.lower().endswith(('.jpg', '.jpeg')):
        img.save(output_path, 'JPEG', quality=quality, optimize=True)
    elif output_path.lower().endswith('.webp'):
        img.save(output_path, 'WebP', quality=quality)
    else:
        img.save(output_path, optimize=True)

    file_size = os.path.getsize(output_path)

    # If file is still > 5MB, reduce quality iteratively
    if file_size > 5 * 1024 * 1024:
        for q in [70, 55, 40, 25]:
            if output_path.lower().endswith(('.jpg', '.jpeg')):
                img.save(output_path, 'JPEG', quality=q, optimize=True)
            elif output_path.lower().endswith('.webp'):
                img.save(output_path, 'WebP', quality=q)
            file_size = os.path.getsize(output_path)
            if file_size <= 5 * 1024 * 1024:
                break

    return file_size


def resize_with_pillow(input_path: str, output_path: str, max_dim: int, quality: int) -> dict:
    """Resize using Pillow (preferred)."""
    from PIL import Image

    img = Image.open(input_path)
    original_size = img.size

    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    new_size = img.size

    file_size = save_image(img, output_path, quality)

    return {
        'original_size': original_size,
        'new_size': new_size,
        'file_size_bytes': file_size,
        'quality': quality,
        'resized': original_size != new_size,
    }


def chunk_with_pillow(input_path: str, output_base: str, chunk_height: int,
                      overlap: int, max_dim: int, quality: int) -> dict:
    """Slice a tall image into chunks and resize each to Vision API limits."""
    from PIL import Image

    img = Image.open(input_path)
    width, height = img.size

    # Convert RGBA to RGB once
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    chunks = []
    y = 0
    index = 1
    step = chunk_height - overlap  # effective step with overlap

    while y < height:
        # Crop this chunk
        bottom = min(y + chunk_height, height)
        chunk = img.crop((0, y, width, bottom))

        # Resize chunk to fit within Vision API limits
        chunk.thumbnail((max_dim, max_dim), Image.LANCZOS)

        # Build output path: output_base-001.jpg, output_base-002.jpg, ...
        chunk_path = f"{output_base}-{index:03d}.jpg"
        os.makedirs(os.path.dirname(chunk_path) or '.', exist_ok=True)

        file_size = save_image(chunk, chunk_path, quality)

        chunks.append({
            'index': index,
            'path': chunk_path,
            'source_region': {'x': 0, 'y': y, 'width': width, 'height': bottom - y},
            'resized_to': chunk.size,
            'file_size_bytes': file_size,
        })

        y += step
        index += 1

        # Safety: if the remaining strip is very short (< 15% of chunk height),
        # the previous chunk already captured it via overlap. Skip it.
        if height - y < chunk_height * 0.15 and y < height:
            break

    return {
        'original_size': (width, height),
        'chunk_count': len(chunks),
        'chunk_height': chunk_height,
        'overlap': overlap,
        'chunks': chunks,
    }


def resize_with_imagemagick(input_path: str, output_path: str, max_dim: int, quality: int) -> dict:
    """Fallback: resize using ImageMagick convert command."""
    import subprocess

    result = subprocess.run(
        ['identify', '-format', '%wx%h', input_path],
        capture_output=True, text=True
    )
    original_size = tuple(int(x) for x in result.stdout.strip().split('x'))

    subprocess.run([
        'convert', input_path,
        '-resize', f'{max_dim}x{max_dim}>',
        '-quality', str(quality),
        output_path
    ], check=True)

    result = subprocess.run(
        ['identify', '-format', '%wx%h', output_path],
        capture_output=True, text=True
    )
    new_size = tuple(int(x) for x in result.stdout.strip().split('x'))
    file_size = os.path.getsize(output_path)

    return {
        'original_size': original_size,
        'new_size': new_size,
        'file_size_bytes': file_size,
        'quality': quality,
        'resized': original_size != new_size,
    }


def resize_with_ffmpeg(input_path: str, output_path: str, max_dim: int, quality: int) -> dict:
    """Fallback: resize using ffmpeg."""
    import subprocess

    subprocess.run([
        'ffmpeg', '-y', '-i', input_path,
        '-vf', f"scale='min({max_dim},iw)':'min({max_dim},ih)':force_original_aspect_ratio=decrease",
        '-q:v', str(max(1, 31 - int(quality * 0.3))),
        output_path
    ], check=True, capture_output=True)

    file_size = os.path.getsize(output_path)
    return {
        'original_size': 'unknown',
        'new_size': 'check output',
        'file_size_bytes': file_size,
        'quality': quality,
        'resized': True,
    }


def main():
    parser = argparse.ArgumentParser(
        description='Resize and chunk screenshots for Claude Vision API')
    parser.add_argument('input', help='Input image path')
    parser.add_argument('output',
                        help='Output path. For resize mode: full file path (e.g., out.jpg). '
                             'For chunk mode: base name without extension (e.g., screenshots/home)')
    parser.add_argument('--mode', choices=['resize', 'chunk'], default='resize',
                        help='resize = shrink single image; chunk = slice tall image into pieces')
    parser.add_argument('--max-dimension', type=int, default=1568,
                        help='Max dimension per edge for Vision API (default: 1568)')
    parser.add_argument('--quality', type=int, default=85,
                        help='JPEG/WebP quality 1-100 (default: 85)')
    parser.add_argument('--chunk-height', type=int, default=900,
                        help='Height of each chunk in source pixels (default: 900)')
    parser.add_argument('--overlap', type=int, default=100,
                        help='Pixel overlap between adjacent chunks to avoid cutting '
                             'elements at boundaries (default: 100)')
    parser.add_argument('--json', action='store_true',
                        help='Output result as JSON (useful for scripts)')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)

    if args.mode == 'chunk':
        # Chunk mode — requires Pillow (no ImageMagick/ffmpeg fallback for cropping)
        try:
            result = chunk_with_pillow(
                args.input, args.output, args.chunk_height,
                args.overlap, args.max_dimension, args.quality)

            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"Chunked: {result['original_size'][0]}x{result['original_size'][1]} "
                      f"-> {result['chunk_count']} chunks")
                for chunk in result['chunks']:
                    region = chunk['source_region']
                    print(f"  [{chunk['index']:03d}] y={region['y']}-{region['y']+region['height']} "
                          f"-> {chunk['resized_to'][0]}x{chunk['resized_to'][1]} "
                          f"({chunk['file_size_bytes']/1024:.0f} KB) "
                          f"{chunk['path']}")

        except ImportError:
            print("Error: Chunk mode requires Pillow. Install with: pip install Pillow",
                  file=sys.stderr)
            sys.exit(1)

    else:
        # Resize mode — try Pillow, ImageMagick, ffmpeg in order
        result = None
        method = None

        try:
            result = resize_with_pillow(args.input, args.output, args.max_dimension, args.quality)
            method = 'Pillow'
        except ImportError:
            try:
                result = resize_with_imagemagick(args.input, args.output,
                                                 args.max_dimension, args.quality)
                method = 'ImageMagick'
            except (FileNotFoundError, Exception):
                try:
                    result = resize_with_ffmpeg(args.input, args.output,
                                               args.max_dimension, args.quality)
                    method = 'ffmpeg'
                except (FileNotFoundError, Exception):
                    print("Error: No image processing tool available.", file=sys.stderr)
                    print("Install one of: Pillow (pip install Pillow), ImageMagick, or ffmpeg",
                          file=sys.stderr)
                    sys.exit(1)

        if args.json:
            result['method'] = method
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"Resized using {method}")
            print(f"  Original: {result['original_size']}")
            print(f"  New: {result['new_size']}")
            print(f"  File size: {result['file_size_bytes'] / 1024:.1f} KB")
            print(f"  Quality: {result['quality']}")
            print(f"  Output: {args.output}")

            if result['file_size_bytes'] > 5 * 1024 * 1024:
                print(f"  WARNING: File still exceeds 5MB limit!", file=sys.stderr)


if __name__ == '__main__':
    main()
