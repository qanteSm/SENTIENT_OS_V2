"""Process generated CCTV room photos and create transparent PNG monster entities."""

import os
import shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

ARTIFACTS_DIR = Path(r"C:\Users\muham\.gemini\antigravity-ide\brain\ed988aaf-56ad-4fc0-90ff-bbe61dfaed27")
DEST_DIR = Path(r"c:\Users\muham\OneDrive\Masaüstü\projeler\sentient_v2\electron-app\renderer\minigame\images\cctv")
DEST_DIR.mkdir(parents=True, exist_ok=True)


def find_latest_artifact(pattern: str) -> Path:
    matches = list(ARTIFACTS_DIR.glob(f"{pattern}*"))
    if not matches:
        raise FileNotFoundError(f"No artifact found matching {pattern}")
    matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0]


def copy_room_photos():
    room_map = {
        "cctv_cam1.jpg": "cctv_cam1_normal",
        "cctv_cam2.jpg": "cctv_cam2_normal",
        "cctv_cam3.jpg": "cctv_cam3_normal",
        "cctv_cam4.jpg": "cctv_cam4_normal",
        "cctv_cam5.jpg": "cctv_cam5_normal",
        "cctv_cam6.jpg": "cctv_cam6_normal",
    }

    for target_name, prefix in room_map.items():
        src = find_latest_artifact(prefix)
        dest = DEST_DIR / target_name
        shutil.copy2(src, dest)
        print(f"[OK] Copied room photo: {src.name} -> {dest.name}")


def extract_transparent_monster(src_prefix: str, target_name: str, threshold: int = 15, feather: float = 1.2):
    src = find_latest_artifact(src_prefix)
    img = Image.open(src).convert("RGBA")
    arr = np.array(img, dtype=np.float32)

    # Compute luminance/intensity of background
    r, g, b, _ = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    brightness = np.maximum(r, np.maximum(g, b))

    # Alpha mask: 0 if pure dark black, ramping up smoothly to 255
    alpha = np.clip((brightness - threshold) * (255.0 / (80.0 - threshold)), 0, 255)

    arr[:, :, 3] = alpha
    out_img = Image.fromarray(arr.astype(np.uint8))
    if feather > 0:
        # Soft feathering on edges
        mask = out_img.split()[3].filter(ImageFilter.GaussianBlur(feather))
        out_img.putalpha(mask)

    dest = DEST_DIR / target_name
    out_img.save(dest, format="PNG")
    print(f"[OK] Created transparent monster PNG: {dest.name}")


def main():
    print("Processing CCTV room backgrounds and transparent monsters...")
    copy_room_photos()

    extract_transparent_monster("monster_shadow_lurker", "monster_shadow_lurker.png", threshold=12)
    extract_transparent_monster("monster_cyber_glitch", "monster_cyber_glitch.png", threshold=14)
    extract_transparent_monster("monster_crawler", "monster_crawler.png", threshold=10)
    extract_transparent_monster("monster_weeping_phantom", "monster_weeping_phantom.png", threshold=12)

    print("All CCTV photographic assets & transparent monster entities successfully processed!")


if __name__ == "__main__":
    main()
