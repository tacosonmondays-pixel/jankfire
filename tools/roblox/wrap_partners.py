"""Each wrap's PARTNER: what the other part of the gun wears on NORMAL and REVERSE (docs/WRAP-TEXTURES.md, "Normal and
reverse").

The Rivals study (19 Nov 2026, vault Research/Rivals wraps study): a Rivals wrap is two looks, the pattern and a
designed second look, and Inverted swaps which parts of the gun wear which. The second look is chosen per wrap, and it
always CONTRASTS the pattern in lightness (a light pattern with a deep tone of itself, a dark glowing pattern with
bright or metal parts), so the gun reads as two designed tones. Ours before this was the picture tinted down by a grey
multiplier to about 0.2 luminance: on a dark picture (Galaxy, Sakura, Hex, Lava, Kintsugi) that half went near black,
and the whole gun read as one dark smear.

The rule, worked out in CIE L*a*b* from each wrap's colour map:
  - a light picture (mean L* >= LIGHT) gets DEEP: the same picture tinted to a deep tone of its own hue (L* about 40
    below, 16..30), so the pattern still shows, darker, in its own colour (a navy sea under a pale wave, a wine red
    under a red die);
  - a dark picture gets METAL: one satin anodised metal in the hue of the wrap's accent (its brightest saturated
    colour), L* 28..38 (Kintsugi's partner is a bronze gold, Lava's copper, Galaxy's a violet steel, Hex a teal steel).
    (First set at L* 44..58: in Studio the metal read as pale pastel plastic; 0.6 of that colour read as metal, 19 Nov.)
OVERRIDE sets a wrap's partner by hand.

Writes roblox/src/shared/WrapPartners.luau (read by WeaponModels.wrap; LoadoutUI's chip band shows the partner too).
Usage: py tools/roblox/wrap_partners.py <wraps dir> [<more dirs>...]   (every *_color.png found, first dir wins)
"""
import os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(REPO, 'roblox', 'src', 'shared', 'WrapPartners.luau')

LIGHT = 46.0
# by hand: id -> (kind, partner hex)  (kind 'deep' takes the tint from the partner colour)
OVERRIDE = {
}

M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
WHITE = np.array([0.95047, 1.0, 1.08883])


def srgb_to_lin(c):
    c = np.asarray(c, np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.clip(np.asarray(c, np.float64), 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def rgb_to_lab(rgb):
    xyz = srgb_to_lin(rgb) @ M.T / WHITE
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def lab_to_rgb(lab):
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    fy = (L + 16) / 116
    fx, fz = fy + a / 500, fy - b / 200
    inv = lambda f: np.where(f ** 3 > 0.008856, f ** 3, (f - 16 / 116) / 7.787)
    xyz = np.stack([inv(fx), inv(fy), inv(fz)], -1) * WHITE
    return lin_to_srgb(xyz @ np.linalg.inv(M).T)


def lch(L, C, h):
    return np.array([L, C * np.cos(h), C * np.sin(h)])


def hx(c):
    return ''.join('%02x' % int(round(float(np.clip(v, 0, 1)) * 255)) for v in c)


def tint_for(target, mean_rgb):
    """the per-channel multiplier (SurfaceAppearance.Color) that takes the picture's mean colour to target"""
    k = np.clip(srgb_to_lin(target) / np.maximum(srgb_to_lin(mean_rgb), 1e-4), 0, 1)
    return lin_to_srgb(k)


def partner_of(path, wid=None):
    """-> {'k': 'deep'|'metal', 'c': partner hex, 't': tint hex or None, 'L': face L*}"""
    a = np.asarray(Image.open(path).convert('RGB').resize((256, 256)), np.float64) / 255.0
    px = a.reshape(-1, 3)
    lab = rgb_to_lab(px)
    Lm = float(lab[:, 0].mean())
    C = np.hypot(lab[:, 1], lab[:, 2])
    w = C + 1e-6
    hue = float(np.arctan2((lab[:, 2] * w).sum() / w.sum(), (lab[:, 1] * w).sum() / w.sum()))
    Cm = float(np.median(C))
    mean_rgb = px.mean(0)
    mx, mn = px.max(1), px.min(1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    score = sat * mx if float(sat.max()) > 0.15 else mx
    top = rgb_to_lab(px[score >= np.quantile(score, 0.98)].mean(0))
    acc_c, acc_h = float(np.hypot(top[1], top[2])), float(np.arctan2(top[2], top[1]))
    if wid in OVERRIDE:
        k, c = OVERRIDE[wid]
        col = np.array([int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)])
        return {'k': k, 'c': c, 't': hx(tint_for(col, mean_rgb)) if k == 'deep' else None, 'L': round(Lm, 1)}
    chroma = float(np.clip(Cm * 0.8 + 4, 6, 30))
    if Lm >= LIGHT:
        target = lab_to_rgb(lch(max(16.0, min(30.0, Lm - 40.0)), chroma, hue))
        return {'k': 'deep', 'c': hx(target), 't': hx(tint_for(target, mean_rgb)), 'L': round(Lm, 1)}
    target = lab_to_rgb(lch(float(np.clip(Lm + 16.0, 28.0, 38.0)), float(np.clip(acc_c * 0.35, 6, 22)), acc_h))
    return {'k': 'metal', 'c': hx(target), 't': None, 'L': round(Lm, 1)}


def main():
    dirs = sys.argv[1:]
    merge = '--merge' in dirs          # (keep the file's other rows: replace or add only the wraps found in the dirs)
    dirs = [d for d in dirs if d != '--merge']
    found = {}
    for d in dirs:
        for f in sorted(os.listdir(d)):
            if f.endswith('_color.png') and not f.startswith('flow_'):
                found.setdefault(f[:-len('_color.png')], os.path.join(d, f))
    rows = []
    old = {}
    if merge and os.path.exists(OUT):
        import re
        for line in open(OUT, encoding='utf-8'):
            m = re.match(r'\t([a-z0-9_]+) = \{ k = ', line)
            if m and m.group(1) not in found:
                old[m.group(1)] = line.rstrip('\n')
    for wid in sorted(set(found) | set(old)):
        if wid in old:
            rows.append(old[wid]); continue
        p = partner_of(found[wid], wid)
        t = (', t = Color3.fromHex("%s")' % p['t']) if p['t'] else ''
        rows.append('\t%s = { k = "%s", c = Color3.fromHex("%s")%s }, -- L* %.0f' % (wid, p['k'], p['c'], t, p['L']))
    src = '\n'.join([
        '--!strict',
        '-- GENERATED by tools/roblox/wrap_partners.py from the wraps\' colour maps: do not edit by hand (OVERRIDE there).',
        '-- Each picture wrap\'s PARTNER, what the other part of the gun wears on NORMAL and REVERSE (WeaponModels.wrap;',
        '-- docs/WRAP-TEXTURES.md "Normal and reverse"): k = "deep" (the picture tinted by t to a deep tone of itself) or',
        '-- "metal" (one satin anodised metal, colour c); c is also the chip\'s band colour.',
        'export type Partner = { k: string, c: Color3, t: Color3? }',
        'local P: { [string]: Partner } = {',
    ] + rows + ['}', 'return P', ''])
    with open(OUT, 'w', newline='\n') as fh:
        fh.write(src)
    print('wrote', OUT, len(rows), 'wraps;', sum(1 for r in rows if '"deep"' in r), 'deep')


if __name__ == '__main__':
    main()
