"""Render 1080x1920 slides that look like TikTok's own in-app text tool.

White style = hook slide, yellow style = lyrics slide. For each slide the text
is tried at a few heights and drawn plain if it reads well there, otherwise it
gets TikTok's rounded per-line background box. The photo itself is never edited.
"""
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
import sys, os

W, H = 1080, 1920
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "fonts", "TikTokSans-VF.ttf")
AXES = [36, 100, 550, 0]   # opsz, wdth, wght, slnt -- fitted to TikTok's own text

# (plain text colour, box colour, text colour on box) -- sampled from TikTok's own text tool
WHITE = ((255, 255, 255), (255, 255, 255), (0, 0, 0))
YELLOW = ((242, 203, 71), (243, 205, 70), (130, 74, 15))

SIZE = 76
LH = round(SIZE * 1.513)          # TikTok line pitch
PAD_L, PAD_R = 0.62, 1.07         # box padding (x size), TikTok leaves a trailing space on the right
RADIUS = 0.17                     # corner radius (x size)
ASC_GAP = 0.22                    # box top to top of tall letters (x size)
POSITIONS = (0.42, 0.30, 0.56, 0.20, 0.68)   # tried in this order, first readable one wins


def wrap(draw, text, font, max_w):
    lines = []
    for para in text.split("\n"):
        start = len(lines)
        cur = ""
        for word in para.split():
            test = (cur + " " + word).strip()
            if draw.textlength(test, font=font) <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = word
        lines.append(cur)
        if len(lines) - start >= 2 and len(lines[-1].split()) == 1 and len(lines[-2].split()) > 2:
            prev = lines[-2].split()
            lines[-2] = " ".join(prev[:-1])
            lines[-1] = prev[-1] + " " + lines[-1]
    return lines


def lum(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = c
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def readability(im, d, font, lines, y0, color):
    """worst line: (fraction of low-contrast pixels around the letters, fraction of busy pixels)"""
    import numpy as np
    small = np.asarray(im.resize((W // 4, H // 4))).astype(float) / 255
    lin = np.where(small <= 0.03928, small / 12.92, ((small + 0.055) / 1.055) ** 2.4)
    lb = lin[..., 0] * 0.2126 + lin[..., 1] * 0.7152 + lin[..., 2] * 0.0722
    lt = lum(color)
    ratio = (np.maximum(lt, lb) + 0.05) / (np.minimum(lt, lb) + 0.05)
    edges = np.asarray(im.resize((W // 4, H // 4)).convert("L").filter(ImageFilter.FIND_EDGES))
    worst_bad = worst_busy = 0
    for i, ln in enumerate(lines):
        mask = Image.new("L", (W, H), 0)
        tw = d.textlength(ln, font=font)
        ImageDraw.Draw(mask).text(((W - tw) / 2, y0 + i * LH), ln, font=font, fill=255)
        ring = np.asarray(mask.resize((W // 4, H // 4)).filter(ImageFilter.GaussianBlur(3))) > 8
        if not ring.any():
            continue
        # split the line into chunks so one unreadable word can't hide in the average
        xs = np.where(ring.any(0))[0]
        for chunk in np.array_split(xs, 4):
            sub = ring.copy(); sub[:, :chunk.min()] = False; sub[:, chunk.max() + 1:] = False
            if sub.sum() < 5:
                continue
            worst_bad = max(worst_bad, (ratio[sub] < 3.6).mean())
            worst_busy = max(worst_busy, (edges[sub] > 70).mean())
    return worst_bad, worst_busy


def slide(img_path, text, style, out, force=None):
    im = ImageOps.fit(Image.open(img_path).convert("RGB"), (W, H), Image.LANCZOS)
    font = ImageFont.truetype(FONT, SIZE)
    font.set_variation_by_axes(AXES)
    d = ImageDraw.Draw(im)
    max_text = int(W * 0.93 - (PAD_L + PAD_R) * SIZE)
    lines = wrap(d, text, font, max_text)
    plain, box, on_box = style

    block = LH * len(lines)
    best, best_score, boxed, tried = None, 9, True, set()
    for p in POSITIONS:
        y0 = max(int(H * 0.09), min(int(H * p) - block // 2, H - int(H * 0.12) - block))
        if y0 in tried:
            continue
        tried.add(y0)
        bad, busy = readability(im, d, font, lines, y0, plain)
        if bad < 0.04 and busy < 0.16:
            best, boxed = y0, False
            break
        if bad + busy < best_score:
            best, best_score = y0, bad + busy
    if force is not None:
        boxed = force
    y0 = best

    asc_top = font.getbbox("d")[1]
    shift = int((PAD_R - PAD_L) * SIZE / 2)   # text sits a bit left of centre, like TikTok

    if boxed:
        k = 3  # draw big then shrink so corners are smooth
        m = Image.new("L", (W * k, H * k), 0)
        md = ImageDraw.Draw(m)
        for i, ln in enumerate(lines):
            bw = d.textlength(ln, font=font) + (PAD_L + PAD_R) * SIZE
            x0 = (W - bw) / 2
            top = y0 + i * LH
            md.rounded_rectangle([x0 * k, top * k, (x0 + bw) * k, (top + LH + 1) * k],
                                 radius=RADIUS * SIZE * k, fill=255)
        m = m.resize((W, H), Image.LANCZOS)
        im.paste(Image.new("RGB", (W, H), box), (0, 0), m)
        d = ImageDraw.Draw(im)

    for i, ln in enumerate(lines):
        tw = d.textlength(ln, font=font)
        ty = y0 + i * LH + ASC_GAP * SIZE - asc_top
        d.text(((W - tw) / 2 - shift, ty), ln, font=font, fill=on_box if boxed else plain)
    im.save(out, quality=95, subsampling=0)
    return boxed


if __name__ == "__main__":
    # quick test: python src/slides.py photo.jpg "hook text" "lyrics text" out/prefix
    img, hook, lyric, prefix = sys.argv[1:5]
    slide(img, hook, WHITE, prefix + "_1.jpg")
    slide(img, lyric, YELLOW, prefix + "_2.jpg")
