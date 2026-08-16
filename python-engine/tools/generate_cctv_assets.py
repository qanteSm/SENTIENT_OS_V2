"""Advanced Procedural CCTV Room & Transparent Monster Generator.
Generates 1920x1080 photorealistic surveillance backgrounds and transparent RGBA horror entities.
"""

import math
import os
import random
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance


OUT_DIR = Path(r"c:\Users\muham\OneDrive\Masaüstü\projeler\sentient_v2\electron-app\renderer\minigame\images\cctv")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def create_scanlines_and_noise(img: Image.Image, green_tint: bool = True) -> Image.Image:
    """Apply CCTV night vision noise, scanlines, and vignette."""
    arr = np.array(img, dtype=np.float32)
    h, w = arr.shape[:2]

    # 1. Grain Noise
    noise = np.random.normal(0, 18, (h, w, 3))
    arr = np.clip(arr + noise, 0, 255)

    # 2. Horizontal scanlines
    for y in range(0, h, 3):
        arr[y, :, :] *= 0.72

    # 3. Vignette
    y_idx, x_idx = np.ogrid[:h, :w]
    cent_y, cent_x = h / 2, w / 2
    dist_from_center = np.sqrt((x_idx - cent_x) ** 2 + (y_idx - cent_y) ** 2)
    max_dist = np.sqrt(cent_x ** 2 + cent_y ** 2)
    vignette = 1.0 - 0.45 * (dist_from_center / max_dist) ** 1.8
    arr = arr * np.expand_dims(vignette, axis=-1)

    # 4. Color Grading (Night vision green / cool security CRT)
    if green_tint:
        arr[:, :, 0] *= 0.65  # Red down
        arr[:, :, 1] *= 1.25  # Green up
        arr[:, :, 2] *= 0.75  # Blue down

    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


# ==============================================================================
# ROOM BACKGROUND GENERATION (1920 x 1080)
# ==============================================================================

def generate_cam2_server_room():
    """CAM 02: High-tech Data Center Server Room."""
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (8, 14, 20))
    draw = ImageDraw.Draw(img)

    # Vanishing Point
    vp_x, vp_y = w * 0.5, h * 0.42

    # Floor & Ceiling Grids
    draw.polygon([(0, h), (w, h), (vp_x + 180, vp_y), (vp_x - 180, vp_y)], fill=(12, 18, 26))
    draw.polygon([(0, 0), (w, 0), (vp_x + 220, vp_y - 80), (vp_x - 220, vp_y - 80)], fill=(6, 10, 16))

    # Server Racks - Left and Right Perspective
    for i in range(8):
        t0 = i / 8.0
        t1 = (i + 1) / 8.0

        # Left Rack
        lx0 = int((1 - t0) * 0 + t0 * (vp_x - 180))
        lx1 = int((1 - t1) * 0 + t1 * (vp_x - 180))
        ly_top0 = int((1 - t0) * 80 + t0 * (vp_y - 120))
        ly_top1 = int((1 - t1) * 80 + t1 * (vp_y - 120))
        ly_bot0 = int((1 - t0) * h + t0 * vp_y)
        ly_bot1 = int((1 - t1) * h + t1 * vp_y)

        draw.polygon([(lx0, ly_top0), (lx1, ly_top1), (lx1, ly_bot1), (lx0, ly_bot0)],
                     fill=(14 + i * 2, 22 + i * 3, 32 + i * 4), outline=(30, 50, 70))

        # Blinking Server LEDs on Left
        for row in range(12):
            led_y = int(ly_top0 + (ly_bot0 - ly_top0) * (row + 0.5) / 13)
            for led_c in range(6):
                led_x = int(lx0 + (lx1 - lx0) * (led_c + 0.5) / 7)
                col = random.choice([(0, 255, 136), (0, 229, 255), (0, 180, 255), (255, 60, 60), (30, 40, 50)])
                draw.rectangle([led_x - 2, led_y - 2, led_x + 2, led_y + 2], fill=col)

        # Right Rack
        rx0 = int((1 - t0) * w + t0 * (vp_x + 180))
        rx1 = int((1 - t1) * w + t1 * (vp_x + 180))
        ry_top0 = ly_top0
        ry_top1 = ly_top1
        ry_bot0 = ly_bot0
        ry_bot1 = ly_bot1

        draw.polygon([(rx0, ry_top0), (rx1, ry_top1), (rx1, ry_bot1), (rx0, ry_bot0)],
                     fill=(14 + i * 2, 22 + i * 3, 32 + i * 4), outline=(30, 50, 70))

        # Blinking LEDs Right
        for row in range(12):
            led_y = int(ry_top0 + (ry_bot0 - ry_top0) * (row + 0.5) / 13)
            for led_c in range(6):
                led_x = int(rx0 + (rx1 - rx0) * (led_c + 0.5) / 7)
                col = random.choice([(0, 255, 136), (0, 229, 255), (0, 180, 255), (255, 180, 0), (30, 40, 50)])
                draw.rectangle([led_x - 2, led_y - 2, led_x + 2, led_y + 2], fill=col)

    # Overhead Cable Trays & Cooling Ducts
    draw.rectangle([vp_x - 120, vp_y - 180, vp_x + 120, vp_y - 110], fill=(20, 30, 42), outline=(40, 60, 80))

    img = create_scanlines_and_noise(img)
    img.save(OUT_DIR / "cctv_cam2.jpg", quality=92)
    print("✓ Created cctv_cam2.jpg")


def generate_cam3_research_lab():
    """CAM 03: Biological Research & Quarantine Laboratory."""
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (10, 16, 22))
    draw = ImageDraw.Draw(img)

    vp_x, vp_y = w * 0.5, h * 0.45

    # Walls & Tile Floor
    draw.polygon([(0, h), (w, h), (w * 0.75, vp_y + 120), (w * 0.25, vp_y + 120)], fill=(16, 24, 30))
    # Tile lines
    for x in range(0, w, 80):
        draw.line([(x, h), (vp_x, vp_y + 120)], fill=(25, 38, 48), width=1)

    # Central Glass Quarantine Pod
    cx0, cy0, cx1, cy1 = w * 0.35, h * 0.2, w * 0.65, h * 0.8
    draw.rectangle([cx0, cy0, cx1, cy1], fill=(12, 35, 30), outline=(0, 255, 136), width=4)
    # Glass reflection
    draw.polygon([(cx0 + 20, cy0), (cx0 + 120, cy0), (cx0 + 40, cy1), (cx0, cy1)], fill=(0, 255, 136, 40))

    # Specimen Cylinder Inside Pod
    draw.ellipse([w * 0.45, h * 0.35, w * 0.55, h * 0.65], fill=(5, 50, 40), outline=(0, 229, 255), width=3)

    # Lab Tables Left & Right
    draw.polygon([(0, h * 0.6), (w * 0.28, h * 0.65), (w * 0.28, h), (0, h)], fill=(20, 32, 42), outline=(40, 60, 80))
    draw.polygon([(w, h * 0.6), (w * 0.72, h * 0.65), (w * 0.72, h), (w, h)], fill=(20, 32, 42), outline=(40, 60, 80))

    # Chemical beakers & computer screens on tables
    draw.rectangle([w * 0.08, h * 0.52, w * 0.22, h * 0.60], fill=(0, 200, 255), outline=(255, 255, 255))
    draw.rectangle([w * 0.78, h * 0.52, w * 0.92, h * 0.60], fill=(0, 255, 136), outline=(255, 255, 255))

    img = create_scanlines_and_noise(img)
    img.save(OUT_DIR / "cctv_cam3.jpg", quality=92)
    print("✓ Created cctv_cam3.jpg")


def generate_cam4_dark_corridor():
    """CAM 04: Dark Basement Industrial Concrete Hallway."""
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (5, 7, 10))
    draw = ImageDraw.Draw(img)

    vp_x, vp_y = w * 0.5, h * 0.5

    # Perspective Concrete Hallway
    draw.polygon([(0, h), (w, h), (vp_x + 80, vp_y + 80), (vp_x - 80, vp_y + 80)], fill=(12, 14, 18))
    draw.polygon([(0, 0), (w, 0), (vp_x + 80, vp_y - 80), (vp_x - 80, vp_y - 80)], fill=(8, 10, 14))
    draw.polygon([(0, 0), (0, h), (vp_x - 80, vp_y + 80), (vp_x - 80, vp_y - 80)], fill=(15, 18, 24))
    draw.polygon([(w, 0), (w, h), (vp_x + 80, vp_y + 80), (vp_x + 80, vp_y - 80)], fill=(15, 18, 24))

    # Ceiling Pipes and Conduits
    for i in range(4):
        py = 40 + i * 25
        draw.line([(0, py), (vp_x - 80, vp_y - 70 + i * 5)], fill=(40, 48, 56), width=4)
        draw.line([(w, py), (vp_x + 80, vp_y - 70 + i * 5)], fill=(40, 48, 56), width=4)

    # Overhead Flickering Fluorescent Tube Light Cone
    draw.polygon([(vp_x - 30, vp_y - 70), (vp_x + 30, vp_y - 70), (w * 0.7, h), (w * 0.3, h)], fill=(45, 55, 45))

    # Blood Stains on Concrete Floor
    draw.ellipse([w * 0.42, h * 0.72, w * 0.58, h * 0.82], fill=(35, 10, 15))

    img = create_scanlines_and_noise(img)
    img.save(OUT_DIR / "cctv_cam4.jpg", quality=92)
    print("✓ Created cctv_cam4.jpg")


def generate_cam5_ventilation_shaft():
    """CAM 05: Ventilation Turbine & Ductwork Shaft."""
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (8, 12, 16))
    draw = ImageDraw.Draw(img)

    cx, cy = w * 0.5, h * 0.5
    outer_r = int(h * 0.46)

    # Duct tunnel concentric rings
    for r in range(outer_r, 40, -40):
        shade = int(12 + (outer_r - r) * 0.08)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(shade, shade + 4, shade + 8), outline=(30, 45, 60), width=2)

    # Industrial 8-Blade Turbine
    for b in range(8):
        angle = b * (math.pi / 4) + 0.2
        bx0 = cx + math.cos(angle - 0.15) * 80
        by0 = cy + math.sin(angle - 0.15) * 80
        bx1 = cx + math.cos(angle + 0.15) * (outer_r - 20)
        by1 = cy + math.sin(angle + 0.15) * (outer_r - 20)
        bx2 = cx + math.cos(angle - 0.15) * (outer_r - 20)
        by2 = cy + math.sin(angle - 0.15) * (outer_r - 20)
        draw.polygon([(cx, cy), (bx0, by0), (bx1, by1), (bx2, by2)], fill=(20, 28, 38), outline=(50, 70, 90))

    # Central Hub
    draw.ellipse([cx - 80, cy - 80, cx + 80, cy + 80], fill=(30, 42, 56), outline=(0, 229, 255), width=3)

    # Heavy Metal Grate Over Front
    for gx in range(int(cx - outer_r), int(cx + outer_r), 70):
        draw.line([(gx, cy - outer_r), (gx, cy + outer_r)], fill=(40, 55, 75), width=4)

    img = create_scanlines_and_noise(img)
    img.save(OUT_DIR / "cctv_cam5.jpg", quality=92)
    print("✓ Created cctv_cam5.jpg")


def generate_cam6_security_vault():
    """CAM 06: Heavy Reinforced Blast Gate & Security Airlock."""
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (10, 14, 18))
    draw = ImageDraw.Draw(img)

    # Heavy Blast Door Frame
    draw.rectangle([w * 0.18, h * 0.12, w * 0.82, h * 0.88], fill=(18, 25, 34), outline=(50, 70, 90), width=8)

    # Steel Door Panels
    draw.rectangle([w * 0.22, h * 0.16, w * 0.50, h * 0.84], fill=(24, 34, 46), outline=(60, 85, 110), width=4)
    draw.rectangle([w * 0.50, h * 0.16, w * 0.78, h * 0.84], fill=(24, 34, 46), outline=(60, 85, 110), width=4)

    # Hazard Caution Stripes (Yellow / Black)
    for s in range(16):
        x0 = int(w * 0.18 + s * (w * 0.64 / 16))
        x1 = int(x0 + (w * 0.64 / 32))
        draw.polygon([(x0, h * 0.84), (x1, h * 0.84), (x1 - 30, h * 0.88), (x0 - 30, h * 0.88)], fill=(255, 200, 0))

    # Electronic Lock Panel & Keypad
    draw.rectangle([w * 0.84, h * 0.42, w * 0.94, h * 0.58], fill=(15, 20, 28), outline=(0, 255, 136), width=2)
    draw.rectangle([w * 0.86, h * 0.45, w * 0.92, h * 0.50], fill=(255, 34, 85)) # Red locked indicator

    img = create_scanlines_and_noise(img)
    img.save(OUT_DIR / "cctv_cam6.jpg", quality=92)
    print("✓ Created cctv_cam6.jpg")


# ==============================================================================
# TRANSPARENT FULL-BODY MONSTERS (RGBA PNG with Zero Background)
# ==============================================================================

def generate_monster_shadow_lurker():
    """Transparent Monster 1: Tall Slender Shadow Lurker with Glowing Red Eyes."""
    w, h = 600, 1000
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Silhouette Torso & Elongated Limbs
    cx = w // 2
    # Head
    draw.ellipse([cx - 45, 60, cx + 45, 170], fill=(10, 10, 14, 240))
    # Neck & Spine
    draw.polygon([(cx - 20, 160), (cx + 20, 160), (cx + 35, 450), (cx - 35, 450)], fill=(12, 12, 16, 250))
    # Shoulders & Long Claws
    draw.polygon([(cx - 35, 200), (cx - 160, 480), (cx - 180, 680), (cx - 140, 670), (cx - 130, 460), (cx - 15, 240)], fill=(8, 8, 12, 245))
    draw.polygon([(cx + 35, 200), (cx + 160, 480), (cx + 180, 680), (cx + 140, 670), (cx + 130, 460), (cx + 15, 240)], fill=(8, 8, 12, 245))
    # Long Razor Fingers
    for f in range(5):
        draw.line([(cx - 160 + f * 8, 670), (cx - 180 + f * 10, 750 + f * 8)], fill=(15, 15, 20, 250), width=5)
        draw.line([(cx + 160 - f * 8, 670), (cx + 180 - f * 10, 750 + f * 8)], fill=(15, 15, 20, 250), width=5)
    # Legs
    draw.polygon([(cx - 30, 450), (cx - 60, 700), (cx - 70, 960), (cx - 40, 960), (cx - 20, 700), (cx, 480)], fill=(10, 10, 14, 250))
    draw.polygon([(cx + 30, 450), (cx + 60, 700), (cx + 70, 960), (cx + 40, 960), (cx + 20, 700), (cx, 480)], fill=(10, 10, 14, 250))

    # Glowing Pure Red Eyes with Halo
    draw.ellipse([cx - 22, 100, cx - 8, 114], fill=(255, 30, 60, 255))
    draw.ellipse([cx + 8, 100, cx + 22, 114], fill=(255, 30, 60, 255))

    # Soft outer feathering
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    img.save(OUT_DIR / "monster_shadow_lurker.png", format="PNG")
    print("✓ Created monster_shadow_lurker.png (Transparent RGBA)")


def generate_monster_cyber_glitch():
    """Transparent Monster 2: Cybernetic Glitched Apparition with Floating Pixels."""
    w, h = 600, 1000
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx = w // 2
    # Glitched Humanoid Silhouette
    draw.ellipse([cx - 50, 70, cx + 50, 190], fill=(15, 30, 35, 220))
    draw.polygon([(cx - 40, 180), (cx + 40, 180), (cx + 60, 500), (cx - 60, 500)], fill=(12, 25, 30, 230))
    draw.polygon([(cx - 45, 500), (cx - 80, 940), (cx - 40, 940), (cx - 10, 520)], fill=(10, 22, 28, 235))
    draw.polygon([(cx + 45, 500), (cx + 80, 940), (cx + 40, 940), (cx + 10, 520)], fill=(10, 22, 28, 235))

    # Floating Digital Cyber Glitch Blocks
    for _ in range(65):
        gx = random.randint(cx - 180, cx + 180)
        gy = random.randint(50, 900)
        gw = random.randint(15, 75)
        gh = random.randint(4, 18)
        color = random.choice([
            (0, 255, 136, random.randint(140, 240)),
            (0, 229, 255, random.randint(140, 240)),
            (255, 34, 85, random.randint(140, 240)),
            (255, 255, 255, 200),
        ])
        draw.rectangle([gx, gy, gx + gw, gy + gh], fill=color)

    # Cyan Glowing Eyes
    draw.ellipse([cx - 24, 115, cx - 10, 128], fill=(0, 255, 255, 255))
    draw.ellipse([cx + 10, 115, cx + 24, 128], fill=(0, 255, 255, 255))

    img.save(OUT_DIR / "monster_cyber_glitch.png", format="PNG")
    print("✓ Created monster_cyber_glitch.png (Transparent RGBA)")


def generate_monster_crawler():
    """Transparent Monster 3: Pale Quadrupedal Wall/Floor Crawler."""
    w, h = 800, 600
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = w // 2, h // 2
    # Crawling Bent Spine Body
    draw.ellipse([cx - 140, cy - 60, cx + 140, cy + 60], fill=(22, 20, 25, 245))
    # Humanoid Distorted Head
    draw.ellipse([cx + 110, cy - 80, cx + 200, cy + 30], fill=(25, 22, 28, 250))

    # 4 Insectoid/Human Jointed Creepy Limbs
    # Front Right
    draw.line([(cx + 100, cy + 20), (cx + 220, cy + 120), (cx + 280, cy + 240)], fill=(18, 16, 22, 250), width=14)
    # Front Left
    draw.line([(cx + 60, cy - 20), (cx + 180, cy - 140), (cx + 260, cy - 40)], fill=(18, 16, 22, 250), width=14)
    # Back Right
    draw.line([(cx - 100, cy + 20), (cx - 200, cy + 140), (cx - 260, cy + 240)], fill=(18, 16, 22, 250), width=14)
    # Back Left
    draw.line([(cx - 120, cy - 20), (cx - 220, cy - 120), (cx - 290, cy + 50)], fill=(18, 16, 22, 250), width=14)

    # Sharp Pale Needle Teeth & Red Eyes
    draw.ellipse([cx + 160, cy - 50, cx + 172, cy - 38], fill=(255, 40, 40, 255))
    draw.ellipse([cx + 180, cy - 45, cx + 192, cy - 33], fill=(255, 40, 40, 255))

    img = img.filter(ImageFilter.GaussianBlur(1.0))
    img.save(OUT_DIR / "monster_crawler.png", format="PNG")
    print("✓ Created monster_crawler.png (Transparent RGBA)")


def generate_monster_weeping_phantom():
    """Transparent Monster 4: Weeping Ghost with Long Dripping Hair & Ectoplasm."""
    w, h = 600, 1000
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx = w // 2
    # Weeping Robe / Flowing Ectoplasm
    draw.polygon([
        (cx - 30, 120), (cx + 30, 120),
        (cx + 90, 400), (cx + 160, 920),
        (cx - 160, 920), (cx - 90, 400)
    ], fill=(18, 18, 24, 235))

    # Long Dark Draped Hair covering face
    draw.ellipse([cx - 55, 80, cx + 55, 230], fill=(5, 5, 8, 255))
    for hair_x in range(cx - 50, cx + 50, 4):
        draw.line([(hair_x, 140), (hair_x + random.randint(-15, 15), 450 + random.randint(0, 120))], fill=(3, 3, 5, 250), width=3)

    # Pale Pale Gaunt Hands clutching hair
    draw.polygon([(cx - 60, 240), (cx - 30, 200), (cx - 20, 240), (cx - 50, 280)], fill=(180, 190, 200, 230))
    draw.polygon([(cx + 60, 240), (cx + 30, 200), (cx + 20, 240), (cx + 50, 280)], fill=(180, 190, 200, 230))

    # Bleeding Black/Red Tears glowing between hair
    draw.ellipse([cx - 15, 220, cx - 5, 235], fill=(255, 0, 60, 255))
    draw.ellipse([cx + 5, 220, cx + 15, 235], fill=(255, 0, 60, 255))

    img.save(OUT_DIR / "monster_weeping_phantom.png", format="PNG")
    print("✓ Created monster_weeping_phantom.png (Transparent RGBA)")


def main():
    print("Generating CCTV room backgrounds and transparent monsters...")
    generate_cam2_server_room()
    generate_cam3_research_lab()
    generate_cam4_dark_corridor()
    generate_cam5_ventilation_shaft()
    generate_cam6_security_vault()

    generate_monster_shadow_lurker()
    generate_monster_cyber_glitch()
    generate_monster_crawler()
    generate_monster_weeping_phantom()
    print("All CCTV assets generated successfully!")


if __name__ == "__main__":
    main()
