"""Generates frames for a YouTube Shorts promo for Shakti Winding Wires."""
import math
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FPS = 30
OVERLAY_MODE = os.environ.get("OVERLAY_MODE", "0") == "1"
OUT_DIR = os.path.join(
    os.path.dirname(__file__),
    "overlay_frames" if OVERLAY_MODE else "frames",
)
os.makedirs(OUT_DIR, exist_ok=True)

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

COPPER = (184, 115, 51)
COPPER_LIGHT = (224, 158, 89)
COPPER_BRIGHT = (255, 165, 60)
GOLD = (255, 200, 80)
DARK = (12, 10, 8)
DARK2 = (28, 20, 14)
WHITE = (245, 240, 232)
SHADOW = (0, 0, 0)


def font(size, bold=True, serif=False):
    path = FONT_SERIF if serif else (FONT_BOLD if bold else FONT_REG)
    return ImageFont.truetype(path, size)


def ease_out(t):
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, t)))


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


def make_background(frame_idx, total_frames):
    """Dark gradient background with a slow-moving warm glow."""
    img = Image.new("RGB", (W, H), DARK)
    px = img.load()
    for y in range(H):
        t = y / H
        c = lerp_color(DARK2, DARK, t)
        for x in range(W):
            px[x, y] = c
    # Moving warm glow
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx = int(W * (0.3 + 0.4 * math.sin(frame_idx / 90)))
    cy = int(H * (0.3 + 0.3 * math.cos(frame_idx / 110)))
    for r in range(700, 0, -40):
        alpha = 1 - r / 700
        c = tuple(int(COPPER[i] * alpha * 0.35) for i in range(3))
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    img = Image.blend(img, glow, 0.55)
    return img


def draw_coil(img, frame_idx, cx, cy, radius=320, turns=8, thickness=14, rotation=0.0, alpha=1.0):
    """Draws a stylised copper coil/spring as a series of arcs."""
    if radius < 6 or alpha <= 0.001:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    spacing = (radius * 1.6) / turns
    start_y = cy - (turns - 1) * spacing / 2
    for i in range(turns):
        y = start_y + i * spacing
        # Wire ellipse (top arc lit, bottom shadowed)
        rx = radius
        ry = spacing * 0.85
        # shadow
        d.ellipse(
            [cx - rx + 6, y - ry + 6, cx + rx + 6, y + ry + 6],
            outline=(0, 0, 0, int(180 * alpha)),
            width=thickness + 2,
        )
        # copper body
        d.ellipse(
            [cx - rx, y - ry, cx + rx, y + ry],
            outline=COPPER + (int(255 * alpha),),
            width=thickness,
        )
        # highlight (top half) — draw arc
        d.arc(
            [cx - rx + 2, y - ry + 2, cx + rx - 2, y + ry - 2],
            start=200, end=340,
            fill=COPPER_BRIGHT + (int(255 * alpha),),
            width=max(3, thickness // 3),
        )
        # specular dot
        sx = cx + int(math.cos(math.radians(260 + rotation * 360 + i * 25)) * rx * 0.85)
        sy = y + int(math.sin(math.radians(260)) * ry * 0.85)
        d.ellipse([sx - 6, sy - 6, sx + 6, sy + 6], fill=GOLD + (int(255 * alpha),))
    img.paste(layer, (0, 0), layer)


def draw_text(img, text, y, size, color=WHITE, bold=True, serif=False, alpha=1.0, x_offset=0, letter_spacing=0):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(size, bold=bold, serif=serif)
    if letter_spacing == 0:
        bbox = d.textbbox((0, 0), text, font=f)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2 + x_offset - bbox[0]
        # shadow
        d.text((x + 4, y + 5), text, font=f, fill=(0, 0, 0, int(180 * alpha)))
        d.text((x, y), text, font=f, fill=color + (int(255 * alpha),))
    else:
        # compute total width with spacing
        widths = []
        for ch in text:
            bb = d.textbbox((0, 0), ch, font=f)
            widths.append(bb[2] - bb[0])
        tw = sum(widths) + letter_spacing * (len(text) - 1)
        x = (W - tw) // 2 + x_offset
        for i, ch in enumerate(text):
            d.text((x + 4, y + 5), ch, font=f, fill=(0, 0, 0, int(180 * alpha)))
            d.text((x, y), ch, font=f, fill=color + (int(255 * alpha),))
            x += widths[i] + letter_spacing
    img.paste(layer, (0, 0), layer)


def draw_pill(img, text, cy, size=44, pad_x=44, pad_y=18, fill=COPPER, txt=WHITE, alpha=1.0):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(size, bold=True)
    bbox = d.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    w = tw + pad_x * 2
    h = th + pad_y * 2
    x = (W - w) // 2
    y = cy - h // 2
    d.rounded_rectangle(
        [x, y, x + w, y + h],
        radius=h // 2,
        fill=fill + (int(255 * alpha),),
    )
    d.text((x + pad_x - bbox[0], y + pad_y - bbox[1]), text, font=f, fill=txt + (int(255 * alpha),))
    img.paste(layer, (0, 0), layer)


def draw_check(img, cx, cy, r, alpha=1.0, color=COPPER_BRIGHT):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color + (int(255 * alpha),), width=8)
    d.line(
        [(cx - r * 0.45, cy + r * 0.05), (cx - r * 0.05, cy + r * 0.45), (cx + r * 0.5, cy - r * 0.4)],
        fill=color + (int(255 * alpha),),
        width=10,
    )
    img.paste(layer, (0, 0), layer)


def vignette(img, strength=0.55):
    v = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(v)
    # Draw a darkening frame around the edge by stacking rectangles
    for i in range(60):
        a = int(255 * ((60 - i) / 60) ** 2 * strength)
        vd.rectangle([i * 6, i * 10, W - i * 6, H - i * 10], outline=a, width=2)
    v = v.filter(ImageFilter.GaussianBlur(100))
    overlay = Image.new("RGB", (W, H), (0, 0, 0))
    img.paste(overlay, (0, 0), v)


def grain(img, frame_idx, amount=8):
    # simple noise: scatter pixels
    import random
    random.seed(frame_idx * 7919)
    px = img.load()
    for _ in range(W * H // 90):
        x = random.randint(0, W - 1)
        y = random.randint(0, H - 1)
        r, g, b = px[x, y]
        d = random.randint(-amount, amount)
        px[x, y] = (max(0, min(255, r + d)), max(0, min(255, g + d)), max(0, min(255, b + d)))


# ───────────────────────────── SCENES ─────────────────────────────
# Each scene: (start_sec, end_sec, render_fn)

def scene_brand(img, t, dur, idx):
    # 0-4s: Brand reveal with coil
    p = t / dur
    # coil grows in
    coil_p = ease_out(min(1, t / 1.4))
    draw_coil(img, idx, W // 2, H // 2 - 80, radius=int(300 * coil_p), turns=9, thickness=18, alpha=coil_p)
    # title slides up
    title_p = ease_out(max(0, min(1, (t - 0.6) / 1.0)))
    y_title = int(lerp(H * 0.78, H * 0.72, title_p))
    draw_text(img, "SHAKTI", y_title, 180, color=COPPER_BRIGHT, alpha=title_p, letter_spacing=8)
    sub_p = ease_out(max(0, min(1, (t - 1.2) / 1.0)))
    draw_text(img, "WINDING WIRES", int(lerp(H * 0.86, H * 0.82, sub_p)), 80, color=WHITE, alpha=sub_p, letter_spacing=12)
    # tagline fade in
    tag_p = ease_out(max(0, min(1, (t - 2.2) / 1.0)))
    draw_text(img, "— Powering India's Industry —", int(H * 0.90), 38, color=GOLD, bold=False, serif=True, alpha=tag_p)


def scene_premium(img, t, dur, idx):
    # 4-9s
    p = ease_out(min(1, t / 0.8))
    draw_coil(img, idx, W // 2, H // 2, radius=260, turns=6, thickness=14, alpha=0.35)
    draw_pill(img, "PREMIUM QUALITY", int(H * 0.30), size=46, alpha=p)
    draw_text(img, "100% PURE", int(H * 0.40), 130, color=WHITE, alpha=ease_out(min(1, (t - 0.3) / 0.9)), letter_spacing=4)
    draw_text(img, "ELECTROLYTIC", int(H * 0.50), 96, color=COPPER_BRIGHT, alpha=ease_out(min(1, (t - 0.7) / 0.9)), letter_spacing=4)
    draw_text(img, "COPPER", int(H * 0.58), 170, color=GOLD, alpha=ease_out(min(1, (t - 1.0) / 0.9)), letter_spacing=8)
    # spec line
    sp = ease_out(max(0, min(1, (t - 2.0) / 1.0)))
    draw_text(img, "99.97% Conductivity  •  Annealed Finish", int(H * 0.72), 38, color=WHITE, bold=False, alpha=sp)


def scene_gauges(img, t, dur, idx):
    # 9-14s
    p = ease_out(min(1, t / 0.7))
    draw_text(img, "ALL GAUGES", int(H * 0.18), 110, color=WHITE, alpha=p, letter_spacing=6)
    draw_text(img, "AVAILABLE", int(H * 0.26), 110, color=COPPER_BRIGHT, alpha=p, letter_spacing=6)
    # Draw wire samples of varying thickness
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    sizes = [(28, "8 SWG"), (22, "16 SWG"), (16, "24 SWG"), (10, "32 SWG"), (6, "40 SWG"), (3, "50 SWG")]
    y0 = int(H * 0.38)
    step = 110
    for i, (thk, label) in enumerate(sizes):
        ap = ease_out(max(0, min(1, (t - 0.5 - i * 0.18) / 0.6)))
        if ap <= 0:
            continue
        y = y0 + i * step
        x1, x2 = int(W * 0.20), int(W * 0.65)
        # shadow
        d.line([(x1 + 4, y + 4), (x2 + 4, y + 4)], fill=(0, 0, 0, int(180 * ap)), width=thk + 4)
        # copper wire
        d.line([(x1, y), (x2, y)], fill=COPPER + (int(255 * ap),), width=thk)
        # highlight
        d.line([(x1, y - max(1, thk // 4)), (x2, y - max(1, thk // 4))],
               fill=COPPER_BRIGHT + (int(220 * ap),), width=max(1, thk // 3))
        # label
        f = font(40, bold=True)
        d.text((int(W * 0.70) + 3, y - 25 + 3), label, font=f, fill=(0, 0, 0, int(180 * ap)))
        d.text((int(W * 0.70), y - 25), label, font=f, fill=WHITE + (int(255 * ap),))
    img.paste(layer, (0, 0), layer)
    # bottom strap
    sp = ease_out(max(0, min(1, (t - 2.5) / 1.0)))
    draw_pill(img, "CUSTOM SIZES ON REQUEST", int(H * 0.92), size=40, alpha=sp, fill=COPPER)


def scene_certified(img, t, dur, idx):
    # 14-19s
    p = ease_out(min(1, t / 0.6))
    # big check
    cp = ease_out(min(1, t / 0.9))
    draw_check(img, W // 2, int(H * 0.32), int(180 * cp), alpha=cp)
    draw_text(img, "ISI  •  BIS", int(H * 0.45), 120, color=WHITE, alpha=p, letter_spacing=10)
    draw_text(img, "CERTIFIED", int(H * 0.53), 130, color=COPPER_BRIGHT, alpha=ease_out(min(1, (t - 0.4) / 0.8)), letter_spacing=8)
    # benefits list
    benefits = ["Uniform Diameter", "Tested Insulation", "Lab-Verified Purity", "Consistent Resistance"]
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(46, bold=True)
    for i, b in enumerate(benefits):
        ap = ease_out(max(0, min(1, (t - 1.2 - i * 0.25) / 0.5)))
        if ap <= 0:
            continue
        y = int(H * 0.66) + i * 70
        x = int(W * 0.18)
        # bullet
        d.ellipse([x - 18, y + 10, x + 2, y + 30], fill=COPPER_BRIGHT + (int(255 * ap),))
        d.text((x + 30 + 3, y + 3), b, font=f, fill=(0, 0, 0, int(180 * ap)))
        d.text((x + 30, y), b, font=f, fill=WHITE + (int(255 * ap),))
    img.paste(layer, (0, 0), layer)


def scene_uses(img, t, dur, idx):
    # 19-24s — applications
    p = ease_out(min(1, t / 0.6))
    draw_text(img, "TRUSTED FOR", int(H * 0.16), 70, color=WHITE, alpha=p, letter_spacing=8)
    draw_text(img, "EVERY APPLICATION", int(H * 0.22), 70, color=COPPER_BRIGHT, alpha=p, letter_spacing=6)
    # tiles
    apps = [
        ("ELECTRIC", "MOTORS"),
        ("TRANSFORMERS", ""),
        ("SUBMERSIBLE", "PUMPS"),
        ("FANS &", "APPLIANCES"),
        ("GENERATORS", ""),
        ("CHOKES &", "BALLASTS"),
    ]
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cols, rows = 2, 3
    tile_w = int(W * 0.40)
    tile_h = int(H * 0.18)
    gap_x = int(W * 0.05)
    gap_y = int(H * 0.025)
    total_w = cols * tile_w + (cols - 1) * gap_x
    x0 = (W - total_w) // 2
    y0 = int(H * 0.32)
    for i, (l1, l2) in enumerate(apps):
        r = i // cols
        c = i % cols
        ap = ease_out(max(0, min(1, (t - 0.6 - i * 0.18) / 0.5)))
        if ap <= 0:
            continue
        x = x0 + c * (tile_w + gap_x)
        y = y0 + r * (tile_h + gap_y)
        # tile background
        d.rounded_rectangle([x, y, x + tile_w, y + tile_h], radius=24,
                            fill=(40, 28, 18, int(220 * ap)),
                            outline=COPPER + (int(255 * ap),), width=4)
        f1 = font(48, bold=True)
        f2 = font(48, bold=True)
        # center text
        if l2:
            bb1 = d.textbbox((0, 0), l1, font=f1)
            tw1 = bb1[2] - bb1[0]
            bb2 = d.textbbox((0, 0), l2, font=f2)
            tw2 = bb2[2] - bb2[0]
            d.text((x + (tile_w - tw1) // 2, y + tile_h // 2 - 55), l1, font=f1, fill=WHITE + (int(255 * ap),))
            d.text((x + (tile_w - tw2) // 2, y + tile_h // 2 + 5), l2, font=f2, fill=COPPER_BRIGHT + (int(255 * ap),))
        else:
            bb1 = d.textbbox((0, 0), l1, font=f1)
            tw1 = bb1[2] - bb1[0]
            d.text((x + (tile_w - tw1) // 2, y + tile_h // 2 - 25), l1, font=f1, fill=WHITE + (int(255 * ap),))
    img.paste(layer, (0, 0), layer)


def scene_cta(img, t, dur, idx):
    # 24-32s — contact / call to action
    p = ease_out(min(1, t / 0.7))
    # outer coil decorative
    draw_coil(img, idx, W // 2, int(H * 0.18), radius=180, turns=4, thickness=12, alpha=0.6 * p)
    draw_text(img, "ORDER TODAY", int(H * 0.38), 110, color=COPPER_BRIGHT, alpha=p, letter_spacing=6)
    sub_p = ease_out(max(0, min(1, (t - 0.3) / 0.8)))
    draw_text(img, "SHAKTI  WINDING  WIRES", int(H * 0.48), 54, color=WHITE, alpha=sub_p, letter_spacing=2)
    # divider
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    lp = ease_out(max(0, min(1, (t - 0.7) / 0.6)))
    if lp > 0:
        cx = W // 2
        w = int(W * 0.35 * lp)
        y = int(H * 0.535)
        d.rectangle([cx - w, y, cx + w, y + 4], fill=COPPER_BRIGHT + (int(255 * lp),))
    img.paste(layer, (0, 0), layer)
    # contact lines
    lines = [
        ("CALL", "+91 - XXXXX XXXXX"),
        ("WHATSAPP", "+91 - XXXXX XXXXX"),
        ("EMAIL", "sales@shaktiwires.in"),
    ]
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i, (lab, val) in enumerate(lines):
        ap = ease_out(max(0, min(1, (t - 1.2 - i * 0.25) / 0.5)))
        if ap <= 0:
            continue
        y = int(H * 0.59) + i * 130
        fl = font(34, bold=True)
        fv = font(52, bold=True)
        bbl = d.textbbox((0, 0), lab, font=fl)
        bbv = d.textbbox((0, 0), val, font=fv)
        twl = bbl[2] - bbl[0]
        twv = bbv[2] - bbv[0]
        d.text(((W - twl) // 2, y), lab, font=fl, fill=COPPER_BRIGHT + (int(255 * ap),))
        d.text(((W - twv) // 2 + 3, y + 50 + 3), val, font=fv, fill=(0, 0, 0, int(180 * ap)))
        d.text(((W - twv) // 2, y + 50), val, font=fv, fill=WHITE + (int(255 * ap),))
    img.paste(lay, (0, 0), lay)
    # final stamp
    fp = ease_out(max(0, min(1, (t - 2.5) / 0.8)))
    draw_pill(img, "★  TRUSTED SINCE YEARS  ★", int(H * 0.92), size=40, alpha=fp, fill=COPPER)


SCENES = [
    (0.0, 4.0, scene_brand),
    (4.0, 9.0, scene_premium),
    (9.0, 14.0, scene_gauges),
    (14.0, 19.0, scene_certified),
    (19.0, 24.0, scene_uses),
    (24.0, 32.0, scene_cta),
]

TOTAL = SCENES[-1][1]
TOTAL_FRAMES = int(TOTAL * FPS)


def render_frame(idx):
    t = idx / FPS
    if OVERLAY_MODE:
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    else:
        img = make_background(idx, TOTAL_FRAMES)
    for s, e, fn in SCENES:
        if s <= t < e:
            local_t = t - s
            dur = e - s
            fade_in = ease_in_out(min(1, local_t / 0.4))
            fade_out = ease_in_out(min(1, (dur - local_t) / 0.4))
            scene_img = img.copy()
            fn(scene_img, local_t, dur, idx)
            if OVERLAY_MODE:
                # blend in alpha space
                alpha_mul = min(fade_in, fade_out)
                if alpha_mul < 1.0:
                    r, g, b, a = scene_img.split()
                    from PIL import ImageEnhance
                    a = a.point(lambda v: int(v * alpha_mul))
                    scene_img = Image.merge("RGBA", (r, g, b, a))
                img = scene_img
            else:
                img = Image.blend(img, scene_img, min(fade_in, fade_out))
            break
    if not OVERLAY_MODE:
        vignette(img, 0.45)
        grain(img, idx, amount=6)
    return img


def main():
    ext = "png" if OVERLAY_MODE else "jpg"
    print(f"Rendering {TOTAL_FRAMES} frames at {FPS} fps ({TOTAL}s) overlay={OVERLAY_MODE}…")
    for i in range(TOTAL_FRAMES):
        img = render_frame(i)
        path = os.path.join(OUT_DIR, f"f_{i:05d}.{ext}")
        if OVERLAY_MODE:
            img.save(path, optimize=False)
        else:
            img.save(path, quality=88)
        if i % 30 == 0:
            print(f"  {i}/{TOTAL_FRAMES}")
    print("done.")


if __name__ == "__main__":
    main()
