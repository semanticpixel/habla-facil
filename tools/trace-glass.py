#!/usr/bin/env python3
"""
Turn a hand-drawn glass PNG into a two-layer SVG that matches the existing set.

The source PNG is a white background, near-black ink strokes, and one flat
colour for the liquid. Ink and liquid are separated by colour, traced
independently, and stacked liquid-under-ink in a shared 124x120 viewBox so
every glass lines up on the same baseline at the same optical size.

    pip install pillow scipy numpy vtracer
    python3 trace-glass.py highball.png highball.svg --height 74

Options worth knowing:
  --height   drawn height inside the 124x120 box. The coupe is the anchor at
             104. The rocks glass is 52.8 (66 * 0.80) because it is wide and
             was reading much heavier than the coupe at full size.
  --smooth   gaussian blur radius on the liquid mask before tracing, which
             rounds off wobble and small nubs. 0 is off; 8 is a light clean-up.
  --thin     erode the ink by N px before tracing, to match pen weight across
             drawings. Leave at 0 unless a drawing was made at a different
             scale; it costs some hand-drawn character.
"""
import argparse
import re

import numpy as np
import vtracer
from PIL import Image
from scipy import ndimage

VB_W, VB_H = 124, 120
BASELINE = 113          # every glass rests its base here
CX = 62                 # and centres here
NUM = re.compile(r'-?\d*\.?\d+(?:e-?\d+)?')


def disk(radius):
    y, x = np.ogrid[-radius:radius + 1, -radius:radius + 1]
    return x * x + y * y <= radius * radius


def split_layers(path, thin=0, smooth=0):
    a = np.array(Image.open(path).convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    ink = ndimage.binary_opening((r + g + b) / 3 < 110, np.ones((3, 3)))
    liquid = ndimage.binary_opening((r > 150) & (r - g > 60) & (r - b > 60), np.ones((3, 3)))

    # Ink strokes drawn over the liquid cut it into pieces. Close across them so
    # the liquid is one solid shape that can sit underneath the ink.
    liquid = ndimage.binary_fill_holes(ndimage.binary_closing(liquid, disk(26)))
    lab, n = ndimage.label(liquid)
    if n > 1:
        sizes = ndimage.sum(liquid, lab, range(1, n + 1))
        liquid = lab == 1 + int(np.argmax(sizes))

    if thin:
        ink = ndimage.binary_opening(ndimage.binary_erosion(ink, disk(thin)), disk(2))
    if smooth:
        liquid = ndimage.gaussian_filter(liquid.astype(float), smooth) > 0.5
    return ink, liquid


def trace(mask, tmp_png, tmp_svg, **kw):
    img = np.where(mask[..., None], 0, 255).astype(np.uint8).repeat(3, axis=2)
    Image.fromarray(img).save(tmp_png)
    opts = dict(colormode="binary", mode="spline", hierarchical="stacked",
                filter_speckle=8, corner_threshold=60, length_threshold=4.0,
                splice_threshold=45, path_precision=3)
    opts.update(kw)
    vtracer.convert_image_to_svg_py(tmp_png, tmp_svg, **opts)
    return parse_paths(open(tmp_svg).read())


def parse_paths(svg_text):
    """vtracer puts a translate() on each path; bake it into the coordinates."""
    out = []
    for m in re.finditer(r'<path([^>]*)>', svg_text):
        attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', m.group(1)))
        tx = ty = 0.0
        mt = re.search(r'translate\(([^)]+)\)', attrs.get('transform', ''))
        if mt:
            v = [float(x) for x in NUM.findall(mt.group(1))]
            tx, ty = v[0], (v[1] if len(v) > 1 else 0.0)
        out.append(affine(attrs.get('d', ''), 1.0, tx, ty))
    return out


def tokens(d):
    for m in re.finditer(r'([MCZmcz])([^MCZmcz]*)', d):
        yield m.group(1), [float(x) for x in NUM.findall(m.group(2))]


def fmt(v):
    v = round(v, 2)
    return str(int(v) if v == int(v) else v)


def affine(d, s, tx, ty):
    parts = []
    for cmd, nums in tokens(d):
        if cmd.upper() == 'Z':
            parts.append('Z')
            continue
        pts = []
        for i in range(0, len(nums), 2):
            pts += [fmt(nums[i] * s + tx), fmt(nums[i + 1] * s + ty)]
        parts.append(cmd + ' '.join(pts))
    return ''.join(parts)


def bbox(ds):
    p = np.array([(n[i], n[i + 1]) for d in ds for _, n in tokens(d)
                  for i in range(0, len(n), 2)])
    return p[:, 0].min(), p[:, 1].min(), p[:, 0].max(), p[:, 1].max()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("png")
    ap.add_argument("svg")
    ap.add_argument("--height", type=float, default=66.0)
    ap.add_argument("--smooth", type=float, default=0)
    ap.add_argument("--thin", type=int, default=0)
    ap.add_argument("--label", default="Glass")
    args = ap.parse_args()

    ink, liquid = split_layers(args.png, thin=args.thin, smooth=args.smooth)
    d_ink = trace(ink, "/tmp/_ink.png", "/tmp/_ink.svg")
    d_liq = trace(liquid, "/tmp/_liq.png", "/tmp/_liq.svg", filter_speckle=40,
                  **(dict(corner_threshold=90, length_threshold=8.0) if args.smooth else {}))

    x0, y0, x1, y1 = bbox(d_ink + d_liq)
    s = args.height / (y1 - y0)
    tx, ty = CX - (x0 + x1) / 2 * s, BASELINE - y1 * s
    d_ink = [affine(d, s, tx, ty) for d in d_ink]
    d_liq = [affine(d, s, tx, ty) for d in d_liq]

    fx0, fy0, fx1, fy1 = bbox(d_ink + d_liq)
    if not (fx0 > 0 and fy0 > 0 and fx1 < VB_W and fy1 < VB_H):
        raise SystemExit(
            f"drawing overflows the {VB_W}x{VB_H} box "
            f"(x {fx0:.1f}-{fx1:.1f}, y {fy0:.1f}-{fy1:.1f}) — lower --height")

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VB_W} {VB_H}" '
           f'role="img" aria-label="{args.label}">'
           f'\n  <path class="liquid" fill="var(--glass-liquid, #EF676C)" d="{" ".join(d_liq)}"/>'
           f'\n  <path class="ink" fill="var(--glass-ink, #060405)" d="{" ".join(d_ink)}"/>'
           f'\n</svg>\n')
    open(args.svg, "w").write(svg)
    print(f"{args.svg}: {len(svg)} bytes, fits x {fx0:.1f}-{fx1:.1f}, y {fy0:.1f}-{fy1:.1f}")


if __name__ == "__main__":
    main()
