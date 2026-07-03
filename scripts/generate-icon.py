#!/usr/bin/env python3
from __future__ import annotations

import struct
import subprocess
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
ICON_SOURCE_PATH = PROJECT_DIR / "assets" / "jusyap-app-icon.png"
RESOURCES_DIR = PROJECT_DIR / "JusYap.app" / "Contents" / "Resources"
ICONSET_DIR = RESOURCES_DIR / "JusYap.iconset"
ICNS_PATH = RESOURCES_DIR / "JusYap.icns"


ICON_FILES = {
    16: ["icon_16x16.png"],
    32: ["icon_16x16@2x.png", "icon_32x32.png"],
    64: ["icon_32x32@2x.png"],
    128: ["icon_128x128.png"],
    256: ["icon_128x128@2x.png", "icon_256x256.png"],
    512: ["icon_256x256@2x.png", "icon_512x512.png"],
    1024: ["icon_512x512@2x.png"],
}

ICNS_ENTRIES = [
    ("icp4", "icon_16x16.png"),
    ("icp5", "icon_32x32.png"),
    ("icp6", "icon_32x32@2x.png"),
    ("ic07", "icon_128x128.png"),
    ("ic08", "icon_256x256.png"),
    ("ic09", "icon_512x512.png"),
    ("ic10", "icon_512x512@2x.png"),
]


def resize_logo(size: int, out_path: Path) -> None:
    subprocess.run(
        [
            "sips",
            "-z",
            str(size),
            str(size),
            str(ICON_SOURCE_PATH),
            "--out",
            str(out_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def write_icns(path: Path) -> None:
    payload = bytearray()
    for icon_type, filename in ICNS_ENTRIES:
        data = (ICONSET_DIR / filename).read_bytes()
        payload.extend(icon_type.encode("ascii"))
        payload.extend(struct.pack(">I", len(data) + 8))
        payload.extend(data)

    path.write_bytes(b"icns" + struct.pack(">I", len(payload) + 8) + payload)


def main() -> int:
    if not ICON_SOURCE_PATH.exists():
        raise FileNotFoundError(f"App icon source not found: {ICON_SOURCE_PATH}")

    RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
    ICONSET_DIR.mkdir(parents=True, exist_ok=True)

    for size, filenames in ICON_FILES.items():
        for filename in filenames:
            resize_logo(size, ICONSET_DIR / filename)

    write_icns(ICNS_PATH)
    print(f"Wrote {ICNS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
