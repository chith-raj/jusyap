#!/usr/bin/env python3
from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path
from typing import Iterable, Tuple


PROJECT_DIR = Path(__file__).resolve().parents[1]
RESOURCES_DIR = PROJECT_DIR / "JusYap.app" / "Contents" / "Resources"
ICONSET_DIR = RESOURCES_DIR / "JusYap.iconset"
ICNS_PATH = RESOURCES_DIR / "JusYap.icns"


Color = Tuple[int, int, int, int]


def clamp(value: float, low: int = 0, high: int = 255) -> int:
    return max(low, min(high, int(round(value))))


def mix(a: Color, b: Color, t: float) -> Color:
    return tuple(clamp(a[i] + (b[i] - a[i]) * t) for i in range(4))  # type: ignore[return-value]


def inside_rounded_rect(x: float, y: float, size: int, radius: float) -> bool:
    left = radius
    right = size - radius
    top = radius
    bottom = size - radius

    if left <= x <= right or top <= y <= bottom:
        return True

    cx = left if x < left else right
    cy = top if y < top else bottom
    return (x - cx) ** 2 + (y - cy) ** 2 <= radius**2


def distance_to_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    dx = bx - ax
    dy = by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def draw_disc(pixels: bytearray, size: int, cx: float, cy: float, radius: float, color: Color) -> None:
    min_x = max(0, int(cx - radius - 2))
    max_x = min(size - 1, int(cx + radius + 2))
    min_y = max(0, int(cy - radius - 2))
    max_y = min(size - 1, int(cy + radius + 2))

    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            coverage = max(0.0, min(1.0, radius + 0.75 - d))
            if coverage:
                blend_pixel(pixels, size, x, y, color, coverage)


def draw_line(
    pixels: bytearray,
    size: int,
    points: Iterable[Tuple[float, float]],
    width: float,
    color: Color,
) -> None:
    pts = list(points)
    radius = width / 2.0
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        min_x = max(0, int(min(ax, bx) - radius - 2))
        max_x = min(size - 1, int(max(ax, bx) + radius + 2))
        min_y = max(0, int(min(ay, by) - radius - 2))
        max_y = min(size - 1, int(max(ay, by) + radius + 2))
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                d = distance_to_segment(x + 0.5, y + 0.5, ax, ay, bx, by)
                coverage = max(0.0, min(1.0, radius + 0.75 - d))
                if coverage:
                    blend_pixel(pixels, size, x, y, color, coverage)

    for x, y in pts:
        draw_disc(pixels, size, x, y, radius, color)


def blend_pixel(pixels: bytearray, size: int, x: int, y: int, color: Color, alpha_scale: float) -> None:
    idx = (y * size + x) * 4
    src_alpha = (color[3] / 255.0) * alpha_scale
    inv = 1.0 - src_alpha
    pixels[idx] = clamp(color[0] * src_alpha + pixels[idx] * inv)
    pixels[idx + 1] = clamp(color[1] * src_alpha + pixels[idx + 1] * inv)
    pixels[idx + 2] = clamp(color[2] * src_alpha + pixels[idx + 2] * inv)
    pixels[idx + 3] = clamp(255 * src_alpha + pixels[idx + 3] * inv)


def draw_drop(pixels: bytearray, size: int) -> None:
    center_x = size * 0.62
    center_y = size * 0.56
    scale = size / 1024.0
    fill = (20, 38, 68, 230)
    highlight = (255, 255, 255, 95)

    for y in range(int(size * 0.28), int(size * 0.84)):
        for x in range(int(size * 0.42), int(size * 0.79)):
            nx = (x + 0.5 - center_x) / (185 * scale)
            ny = (y + 0.5 - center_y) / (240 * scale)
            top_pull = max(0.0, -ny)
            shape = nx * nx * (1.0 + top_pull * 0.75) + (ny + 0.12) ** 2
            taper = abs(nx) - max(0.0, -ny - 0.12) * 0.85
            if shape <= 1.0 and taper <= 0.88:
                edge = min(1.0 - shape, 0.88 - taper)
                coverage = max(0.0, min(1.0, edge * 18.0))
                blend_pixel(pixels, size, x, y, fill, coverage)

    draw_line(
        pixels,
        size,
        [
            (size * 0.56, size * 0.41),
            (size * 0.60, size * 0.52),
            (size * 0.66, size * 0.67),
        ],
        18 * scale,
        highlight,
    )


def make_icon(size: int) -> bytes:
    pixels = bytearray(size * size * 4)
    bg_top = (35, 159, 221, 255)
    bg_bottom = (17, 89, 182, 255)
    radius = size * 0.22

    for y in range(size):
        t = y / max(1, size - 1)
        base = mix(bg_top, bg_bottom, t)
        for x in range(size):
            idx = (y * size + x) * 4
            if inside_rounded_rect(x + 0.5, y + 0.5, size, radius):
                shine = 1.0 - min(1.0, math.hypot((x / size) - 0.3, (y / size) - 0.18) * 1.3)
                pixels[idx : idx + 4] = bytes(mix(base, (255, 255, 255, 255), shine * 0.12))

    scale = size / 1024.0
    shadow = (0, 0, 0, 60)
    white = (245, 250, 255, 245)

    wave = [
        (size * 0.22, size * 0.52),
        (size * 0.31, size * 0.44),
        (size * 0.39, size * 0.60),
        (size * 0.48, size * 0.36),
        (size * 0.58, size * 0.68),
        (size * 0.68, size * 0.46),
        (size * 0.78, size * 0.54),
    ]
    draw_line(pixels, size, [(x + 5 * scale, y + 8 * scale) for x, y in wave], 62 * scale, shadow)
    draw_line(pixels, size, wave, 54 * scale, white)
    draw_drop(pixels, size)

    return encode_png(size, size, pixels)


def encode_png(width: int, height: int, rgba: bytearray) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    rows = bytearray()
    stride = width * 4
    for y in range(height):
        rows.append(0)
        start = y * stride
        rows.extend(rgba[start : start + stride])

    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png.extend(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)))
    png.extend(chunk(b"IDAT", zlib.compress(bytes(rows), 9)))
    png.extend(chunk(b"IEND", b""))
    return bytes(png)


def main() -> int:
    RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
    ICONSET_DIR.mkdir(parents=True, exist_ok=True)

    names = {
        16: ["icon_16x16.png"],
        32: ["icon_16x16@2x.png", "icon_32x32.png"],
        64: ["icon_32x32@2x.png"],
        128: ["icon_128x128.png"],
        256: ["icon_128x128@2x.png", "icon_256x256.png"],
        512: ["icon_256x256@2x.png", "icon_512x512.png"],
        1024: ["icon_512x512@2x.png"],
    }

    for size, filenames in names.items():
        png = make_icon(size)
        for filename in filenames:
            (ICONSET_DIR / filename).write_bytes(png)

    write_icns(ICNS_PATH)
    print(f"Wrote {ICNS_PATH}")
    return 0


def write_icns(path: Path) -> None:
    entries = [
        ("icp4", ICONSET_DIR / "icon_16x16.png"),
        ("icp5", ICONSET_DIR / "icon_32x32.png"),
        ("icp6", ICONSET_DIR / "icon_32x32@2x.png"),
        ("ic07", ICONSET_DIR / "icon_128x128.png"),
        ("ic08", ICONSET_DIR / "icon_256x256.png"),
        ("ic09", ICONSET_DIR / "icon_512x512.png"),
        ("ic10", ICONSET_DIR / "icon_512x512@2x.png"),
    ]
    payload = bytearray()
    for icon_type, icon_path in entries:
        data = icon_path.read_bytes()
        payload.extend(icon_type.encode("ascii"))
        payload.extend(struct.pack(">I", len(data) + 8))
        payload.extend(data)

    path.write_bytes(b"icns" + struct.pack(">I", len(payload) + 8) + payload)


if __name__ == "__main__":
    raise SystemExit(main())
