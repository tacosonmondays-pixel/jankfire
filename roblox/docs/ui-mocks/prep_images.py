"""Prepare the pictures the UI mocks use (run once; outputs go to img/).

- Our own Blender renders of the live guns, skins, hats and containers have a plain
  grey studio background. This keys it out (region growing from the border, so dark
  gun parts next to a dark background survive) and writes transparent PNGs.
- Studio captures (HUD hidden, place v1347 era, 21 Nov 2026) are cropped to 16:9 and
  sized to 1920x1080, plus a blurred copy for menu screens.

Sources live outside git (side-session notes) or elsewhere in the repo; paths below.
"""
import os
import sys
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "img")
NOTES = r"C:\Users\soup2\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_f6d4e505-8093-4c63-b4ec-8c76fd4df317"
GUNS = os.path.join(NOTES, "base-gun-pictures")
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CAPS = sys.argv[1] if len(sys.argv) > 1 else None  # folder with the Studio captures


def region_bg(rgb, tol=4.5, maxd=26.0, seeds=None):
    """Background mask by growing from the border: a pixel joins when it is within
    `tol` of a neighbour already in, and within `maxd` of the border's median colour."""
    a = rgb.astype(np.float32)
    h, w, _ = a.shape
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    ref = np.median(border, axis=0)
    near = np.sqrt(((a - ref) ** 2).sum(-1)) < maxd
    m = np.zeros((h, w), bool)
    m[0, :] = near[0, :]; m[-1, :] = near[-1, :]; m[:, 0] = near[:, 0]; m[:, -1] = near[:, -1]
    # neighbour differences (4-connected)
    dn = np.full((h, w), 1e9, np.float32); dn[1:] = np.abs(a[1:] - a[:-1]).max(-1)   # with the pixel above
    ds = np.full((h, w), 1e9, np.float32); ds[:-1] = np.abs(a[:-1] - a[1:]).max(-1)  # with the pixel below
    dw = np.full((h, w), 1e9, np.float32); dw[:, 1:] = np.abs(a[:, 1:] - a[:, :-1]).max(-1)
    de = np.full((h, w), 1e9, np.float32); de[:, :-1] = np.abs(a[:, :-1] - a[:, 1:]).max(-1)
    ok = near
    for _ in range(4000):
        g = m.copy()
        g[1:] |= m[:-1] & (dn[1:] < tol)
        g[:-1] |= m[1:] & (ds[:-1] < tol)
        g[:, 1:] |= m[:, :-1] & (dw[:, 1:] < tol)
        g[:, :-1] |= m[:, 1:] & (de[:, :-1] < tol)
        g &= ok
        if (g == m).all():
            break
        m = g
    return m, ref


def keyed(src, crop=None, tol=4.5, maxd=26.0, trim=True, scale=None):
    im = Image.open(src).convert("RGB")
    if crop:
        im = im.crop(crop)
    rgb = np.asarray(im)
    bg, ref = region_bg(rgb, tol, maxd)
    alpha = Image.fromarray(((~bg) * 255).astype(np.uint8))
    # close pinholes, then a soft 1 px edge
    alpha = alpha.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MinFilter(3))
    # smooth the stair-stepped outline: 4x up, blur, re-sharpen, back down
    w4, h4 = alpha.width * 4, alpha.height * 4
    a4 = alpha.resize((w4, h4), Image.BICUBIC).filter(ImageFilter.GaussianBlur(3.2))
    a4 = a4.point(lambda v: max(0, min(255, int((v - 96) * 255 / 70))))
    alpha = a4.resize((alpha.width, alpha.height), Image.LANCZOS)
    # pull the background colour out of half-covered edge pixels so no grey rim shows on new backgrounds
    a = np.asarray(alpha).astype(np.float32)[..., None] / 255.0
    c = np.asarray(im).astype(np.float32)
    fg = np.where(a > 0.02, (c - (1 - a) * ref) / np.maximum(a, 0.02), c)
    out = Image.fromarray(np.clip(fg, 0, 255).astype(np.uint8)).convert("RGBA")
    out.putalpha(alpha)
    if trim:
        bb = alpha.point(lambda v: 255 if v > 24 else 0).getbbox()
        if bb:
            pad = 6
            bb = (max(0, bb[0] - pad), max(0, bb[1] - pad), min(im.width, bb[2] + pad), min(im.height, bb[3] + pad))
            out = out.crop(bb)
    if scale:
        out = out.resize((int(out.width * scale), int(out.height * scale)), Image.LANCZOS)
    return out


def fill_rows(im, boxes):
    """Paint over small boxes by blending each row between the pixels left and right of the box."""
    a = np.asarray(im).astype(np.float32).copy()
    for x0, y0, x1, y1 in boxes:
        for y in range(y0, y1):
            l, r = a[y, x0 - 2], a[y, x1 + 1]
            for x in range(x0, x1):
                t = (x - x0) / (x1 - x0)
                a[y, x] = l * (1 - t) + r * t
    return Image.fromarray(a.astype(np.uint8))


def save(img, name):
    p = os.path.join(OUT, name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    img.save(p, optimize=True)
    print("wrote", name, img.size)


def main():
    os.makedirs(OUT, exist_ok=True)
    # 1. base guns (flat 128,131,138 background)
    for gid in ["ar", "revolver", "katana", "smg", "shotgun", "sniper", "shredder", "redline", "burst", "lmg",
                "dmr", "lever", "autoshot", "pistol", "sawnoff", "marbles", "knife"]:
        p = os.path.join(GUNS, f"{gid}_side.png")
        if os.path.exists(p):
            save(keyed(p, tol=6, maxd=30, scale=0.6), f"guns/{gid}_side.png")
    for gid in ["ar", "revolver"]:
        save(keyed(os.path.join(GUNS, f"{gid}_34.png"), tol=6, maxd=30), f"guns/{gid}_34.png")

    # 2. Ducky VIP set renders (as built sheet, 2400x1710): Wish Duck three-quarter and side, Bubble Bath side
    ducky = os.path.join(NOTES, "ducky_v3_built.jpg")
    save(keyed(ducky, crop=(1726, 734, 2392, 1160), tol=4.0, maxd=22), "items/wish_duck_34.png")
    save(keyed(ducky, crop=(12, 262, 1006, 528), tol=4.0, maxd=22), "items/bubble_bath_side.png")
    save(keyed(ducky, crop=(12, 1366, 1006, 1610), tol=4.0, maxd=22), "items/ribbon_duck_side.png")

    # Triangulum Sniper skin (as built sheet, 2560x956): the left-side Blender view
    tri = os.path.join(NOTES, "triangulum_v2_built.jpg")
    save(keyed(tri, crop=(12, 205, 630, 385), tol=4.0, maxd=22), "items/triangulum_side.png")

    # coin pack renders (the shop's own product art, dark studio background kept: used on dark tiles)
    import shutil
    for n in ["99", "499", "1999", "4500"]:
        shutil.copy(os.path.join(REPO, "roblox", "docs", "money", "icons", f"pack_{n}.png"), os.path.join(OUT, "items", f"packsq_{n}.png"))

    # the Frag Grenade item model (docs/items/models-v2-batch1.jpg, "after" column)
    save(keyed(os.path.join(REPO, "roblox", "docs", "items", "models-v2-batch1.jpg"), crop=(660, 60, 880, 300), tol=4.0, maxd=26), "items/frag.png")

    # 3. containers (Blender, vignetted light grey)
    shut = os.path.join(REPO, "roblox", "docs", "loot", "models-shut.png")
    save(keyed(shut, crop=(100, 330, 570, 640), tol=3.2, maxd=40), "items/duffel.png")
    save(keyed(shut, crop=(560, 270, 1060, 660), tol=3.2, maxd=40), "items/crate.png")
    spray = keyed(shut, crop=(1100, 180, 1380, 640), tol=2.6, maxd=80)
    keep = Image.new("L", spray.size, 0)  # the floor shadow touches the can: keep only the can's outline
    from PIL import ImageDraw
    ImageDraw.Draw(keep).polygon([(50, 0), (215, 0), (203, spray.height), (38, spray.height)], fill=255)
    a = np.minimum(np.asarray(spray.getchannel("A")), np.asarray(keep))
    spray.putalpha(Image.fromarray(a))
    save(spray.crop(spray.getchannel("A").getbbox()), "items/spray.png")

    # 4. hats (Blender on dark grey)
    for hid in ["star-tricorne", "royal-duck"]:
        p = os.path.join(REPO, "roblox", "docs", "gun-hats", f"{hid}.png")
        crop = (800, 150, 1160, 385) if hid == "star-tricorne" else (640, 0, 1280, 360)  # one view of the 2x2
        save(keyed(p, crop=crop, tol=4.0, maxd=22), f"items/{hid}.png")

    # 5. wraps on the bullpup (web skin renders, 6 x 320 px tiles on purple)
    sk = os.path.join(REPO, "docs", "wraps", "glb_skins_1.png")
    tiles = {"cherry_pop": 0, "hazard_stripes": 1, "kintsugi": 3, "seigaiha": 4, "sakura_storm": 5}
    for name, col in tiles.items():
        x0 = col * 320 + 2
        save(keyed(sk, crop=(x0, 34, x0 + 316, 206), tol=7, maxd=40, scale=1.6), f"items/wrap_{name}.png")

    # 6. Studio captures -> 1920x1080 (+ blurred copies)
    if CAPS:
        for name in ["hub_spawn", "hub_rotunda", "match_crate", "match_forest"]:
            src = os.path.join(CAPS, name + ".jpg")
            im = Image.open(src).convert("RGB")
            w, h = im.size
            tw = int(round(h * 16 / 9))
            x0 = (w - tw) // 2
            im = im.crop((x0, 0, x0 + tw, h)).resize((1920, 1080), Image.LANCZOS)
            im = im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=60, threshold=2))
            if name.startswith("match"):
                im = fill_rows(im, [(998, 572, 1024, 598), (946, 594, 974, 622)])
            os.makedirs(os.path.join(OUT, "bg"), exist_ok=True)
            im.save(os.path.join(OUT, "bg", name + ".jpg"), quality=90)
            im.filter(ImageFilter.GaussianBlur(22)).save(os.path.join(OUT, "bg", name + "_blur.jpg"), quality=88)
            print("wrote bg", name)


if __name__ == "__main__":
    main()
