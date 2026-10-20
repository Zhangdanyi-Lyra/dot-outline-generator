#!/usr/bin/env python3
"""Recolor an approved grayscale RGBA master and composite honest previews."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
from PIL import Image


PALETTE = {
    "blue": "#4597F8",
    "orange": "#FF5D00",
    "lime": "#D4FF3A",
    "pink": "#FF8BE8",
    "ochre": "#966400",
}


def hex_rgb(value: str) -> np.ndarray:
    value = value.removeprefix("#")
    if len(value) != 6 or any(c not in "0123456789abcdefABCDEF" for c in value):
        raise ValueError("Use a palette name or a six-digit hexadecimal color.")
    return np.array([int(value[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


def resolve_color(value: str, exclusions: list[str]) -> tuple[str, np.ndarray]:
    value = value.lower()
    if value == "random":
        excluded = {PALETTE.get(c.lower(), c).upper().removeprefix("#") for c in exclusions}
        candidates = [name for name, color in PALETTE.items() if color[1:] not in excluded]
        if not candidates:
            raise ValueError("All palette colors were excluded.")
        value = random.SystemRandom().choice(candidates)
    color = PALETTE.get(value, value)
    rgb = hex_rgb(color)
    return "#" + "".join(f"{int(v):02X}" for v in rgb), rgb


def load_rgba(path: Path) -> Image.Image:
    with Image.open(path) as source:
        if "A" not in source.getbands() and "transparency" not in source.info:
            raise ValueError("Source has no alpha channel; use the transparent grayscale master.")
        return source.convert("RGBA")


def validate_master(original: np.ndarray) -> None:
    alpha = original[..., 3]
    if not np.any(alpha > 0) or not np.any(alpha == 0):
        raise ValueError("Master must contain both visible pixels and fully transparent regions.")
    solid_enough = alpha >= 16
    if not np.any(solid_enough):
        raise ValueError("Master contains no sufficiently visible outline.")
    rgb = original[..., :3].astype(np.int16)
    chroma = rgb.max(axis=2) - rgb.min(axis=2)
    if np.mean(chroma[solid_enough] > 8) > 0.01:
        raise ValueError("Source is colored. Recolor its original grayscale master instead.")


def recolor(original: np.ndarray, color: np.ndarray) -> np.ndarray:
    result = original.copy()
    luminance = original[..., :3].astype(np.float32) @ np.array(
        [0.2126, 0.7152, 0.0722], dtype=np.float32
    )
    tinted = color + (255.0 - color) * (luminance[..., None] / 255.0)
    visible = original[..., 3] > 0
    result[..., :3][visible] = np.clip(np.rint(tinted[visible]), 0, 255).astype(np.uint8)
    if not np.array_equal(result[..., 3], original[..., 3]):
        raise RuntimeError("Alpha preservation failed.")
    if not np.array_equal(result[~visible], original[~visible]):
        raise RuntimeError("Transparent-pixel preservation failed.")
    return result


def composite_preview(image: Image.Image, background: str) -> Image.Image:
    width, height = image.size
    if background == "checker":
        yy, xx = np.indices((height, width))
        values = np.where(((xx // 28) + (yy // 28)) % 2 == 0, 245, 229).astype(np.uint8)
        rgba = np.empty((height, width, 4), dtype=np.uint8)
        rgba[..., :3] = values[..., None]
        rgba[..., 3] = 255
        base = Image.fromarray(rgba)
    else:
        values = hex_rgb({"white": "#FFFFFF", "dark": "#202020"}.get(background, background))
        base = Image.new("RGBA", image.size, tuple(int(v) for v in values) + (255,))
    return Image.alpha_composite(base, image).convert("RGB")


def check_destinations(source: Path, destinations: list[Path]) -> None:
    source = source.resolve()
    targets = [path.resolve() for path in destinations]
    if len(set(targets)) != len(targets) or source in targets:
        raise ValueError("Source, PNG output and preview must have distinct paths.")
    for target in targets:
        if target.exists():
            raise ValueError(f"Output already exists; choose a new versioned filename: {target}")
        if target.suffix.lower() != ".png":
            raise ValueError("Outputs must use the .png extension.")


def save_new(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as target:
        image.save(target, format="PNG")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    tint = commands.add_parser("recolor", help="Preserve alpha and map grayscale to one color family.")
    tint.add_argument("--source", required=True, type=Path)
    tint.add_argument("--color", required=True, help="blue, orange, lime, pink, ochre, random, or #RRGGBB")
    tint.add_argument("--exclude", action="append", default=[], help="Exclude a name/hex from random choice.")
    tint.add_argument("--output", required=True, type=Path)
    tint.add_argument("--preview", required=True, type=Path)
    preview = commands.add_parser("preview", help="Composite an RGBA image without editing its source.")
    preview.add_argument("--source", required=True, type=Path)
    preview.add_argument("--output", required=True, type=Path)
    preview.add_argument("--background", default="checker", help="checker, white, dark, or #RRGGBB")
    args = parser.parse_args()

    try:
        destinations = [args.output] + ([args.preview] if args.command == "recolor" else [])
        check_destinations(args.source, destinations)
        image = load_rgba(args.source)
        report = {"source": str(args.source.resolve()), "size": list(image.size)}
        if args.command == "recolor":
            original = np.asarray(image)
            validate_master(original)
            color_name, color = resolve_color(args.color, args.exclude)
            result = Image.fromarray(recolor(original, color))
            preview_image = composite_preview(result, "checker")
            save_new(result, args.output)
            save_new(preview_image, args.preview)
            report.update(color=color_name, alpha_preserved=True, transparent_pixels_preserved=True,
                          output=str(args.output.resolve()), preview=str(args.preview.resolve()))
        else:
            result = composite_preview(image, args.background)
            save_new(result, args.output)
            report.update(preview=str(args.output.resolve()), background=args.background)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
