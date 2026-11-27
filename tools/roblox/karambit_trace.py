# TRACE A KARAMBIT'S SIDE OUTLINE (27 Nov 2026; main, for the owner: "make a karambit like the designs in our vault"):
# a karambit is a flat-profile object, so its side silhouette, traced and extruded, is the most faithful model. This
# traces one knife of the vault's karambit grid (our own generated art: JANKFIRE Vault/Assets/skin-refs/knife/
# karambit_grid.png), splits it into its regions (blade, guard, handle; the ring is modelled as a ring), finds the
# blade's honed edge band along the inside of its curve, turns the handle onto the knife's grip axis and scales it to
# our kit size, and writes the outlines for gun_knife_skins.karambit (no download, no Blender: numpy + PIL).
#   py -3.13 tools/roblox/karambit_trace.py <grid.png> [quadrant g1|g2|g3|g4]  -> tools/roblox/karambit_trace.json
import sys, os, json, math
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
QUAD = {'g1': (0, 0, 768, 512), 'g2': (768, 0, 1536, 512), 'g3': (0, 512, 768, 1024), 'g4': (768, 512, 1536, 1024)}
# landmarks picked on the gridded crops (px): ring centre, outer radius, tip, the blade-handle junction (the guard's
# middle), the guard's half length along the handle, the edge's heel (where the honed edge starts at the guard)
MARKS = {'g4': dict(R=(668, 262), Ro=57, Ri=38, T=(68, 398), J=(360, 185), GW=26, HEEL=(330, 232),
                   # the star bolster, by hand off a 4x zoom (outside the silhouette at its top and bottom tips: the
                   # mask trims those), seeds inside the blade / handle / panel / gem, how far the blade's spine and edge
                   # carry on under the bolster (px)
                   STAR=[(360, 78), (380, 80), (379, 118), (386, 140), (393, 160), (398, 182), (400, 210), (398, 240),
                         (395, 262), (398, 296), (366, 296), (365, 265), (355, 245), (345, 220), (330, 190), (312, 170),
                         (299, 154), (320, 131), (337, 111), (350, 96)],
                   BSEED=(150, 250), HSEED=(560, 140), PSEED=(520, 190), GSEED=(360, 165), CARRY=(22, 14)),
         'g3': dict(R=(680, 262), Ro=56, Ri=37, T=(65, 398), J=(365, 185), GW=28, HEEL=(333, 232))}
HANDLE_M = 0.110          # the handle's length (ring centre to guard middle), metres: the kit karambit's
GRIP_Z = 0.03             # the knife's grip spot: the handle's middle lands here


def mask_of(im, bg=(42, 39, 44), thr=34):
    a = np.asarray(im.convert('RGB')).astype(int)
    d = np.abs(a - np.array(bg)).sum(-1)
    m = d > thr
    # (a median clean-up: 5x5 majority)
    from PIL import ImageFilter
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(5))) > 127


def trace(m):
    """the outer boundary of the largest blob, in order (Moore neighbour tracing), as [(x, y)] pixel centres"""
    H, W = m.shape
    ys, xs = np.nonzero(m)
    i = np.lexsort((xs, ys))[0]
    start = (xs[i], ys[i])
    nb = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1)]
    inside = lambda x, y: 0 <= x < W and 0 <= y < H and m[y, x]
    out = [start]; cur = start; back = 0
    for _ in range(400000):
        found = False
        for k in range(8):
            d = (back + 1 + k) % 8
            nx, ny = cur[0] + nb[d][0], cur[1] + nb[d][1]
            if inside(nx, ny):
                back = (d + 4) % 8
                nxt = (nx, ny); found = True
                break
        if not found: break
        # (Jacob's stopping rule: done only when the walk leaves the start pixel the way it first did; a boundary can
        # pass its start pixel more than once, at a thin spur, and stopping there loses the rest of the outline)
        if cur == start and len(out) > 2 and nxt == out[1]: break
        cur = nxt
        out.append(cur)
    if len(out) > 1 and out[-1] == start: out.pop()
    return out


def simplify(pts, tol):
    """Douglas-Peucker on a closed ring"""
    def dp(seg):
        if len(seg) < 3: return seg
        a, b = np.array(seg[0], float), np.array(seg[-1], float)
        ab = b - a; L = np.linalg.norm(ab) or 1
        d = [abs(ab[0] * (p[1] - a[1]) - ab[1] * (p[0] - a[0])) / L for p in seg[1:-1]]
        k = int(np.argmax(d)) + 1
        if d[k - 1] > tol: return dp(seg[:k + 1])[:-1] + dp(seg[k:])
        return [seg[0], seg[-1]]
    n = len(pts); h = n // 2
    return dp(pts[:h + 1])[:-1] + dp(pts[h:] + [pts[0]])[:-1]


def smooth(pts, k=2):
    n = len(pts); out = []
    for i in range(n):
        xs = [pts[(i + j) % n][0] for j in range(-k, k + 1)]; ys = [pts[(i + j) % n][1] for j in range(-k, k + 1)]
        out.append((sum(xs) / len(xs), sum(ys) / len(ys)))
    return out


def circle3(a, b, c):
    ax, ay = a; bx, by = b; cx, cy = c
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    return ux, uy


def hsv(im):
    a = np.asarray(im.convert('RGB')).astype(float) / 255
    mx, mn = a.max(-1), a.min(-1)
    return np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0.0), mx


def poly_mask(poly, shape):
    from PIL import ImageDraw
    im = Image.new('L', (shape[1], shape[0]), 0)
    ImageDraw.Draw(im).polygon([tuple(p) for p in poly], fill=255)
    return np.asarray(im) > 127


def biggest(m, seed=None):
    """the connected part of a mask holding `seed` (x, y), else the largest"""
    from collections import deque
    H, W = m.shape
    lab = np.zeros(m.shape, np.int32); best, bestn, k = 0, 0, 0
    for y0, x0 in zip(*np.nonzero(m)):
        if lab[y0, x0]: continue
        k += 1; q = deque([(y0, x0)]); lab[y0, x0] = k; n = 0
        while q:
            y, x = q.popleft(); n += 1
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and m[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = k; q.append((yy, xx))
        if n > bestn: best, bestn = k, n
    if seed is not None and lab[seed[1], seed[0]]: return lab == lab[seed[1], seed[0]]
    return lab == best


def opened(m, k):
    from PIL import ImageFilter
    im = Image.fromarray((m * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.MinFilter(k)).filter(ImageFilter.MaxFilter(k))) > 127


def closed(m, k):
    from PIL import ImageFilter
    im = Image.fromarray((m * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.MaxFilter(k)).filter(ImageFilter.MinFilter(k))) > 127


def grown(m, k):
    from PIL import ImageFilter
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(k))) > 127


def fill_holes(m):
    return ~biggest(~m, seed=(0, 0))


def resample(ch, n):
    """a polyline -> n points evenly spaced along it"""
    c = np.array(ch, float); d = np.r_[0, np.cumsum(np.hypot(*np.diff(c, axis=0).T))]
    t = np.linspace(0, d[-1], n)
    return [(float(np.interp(v, d, c[:, 0])), float(np.interp(v, d, c[:, 1]))) for v in t]


def main():
    grid = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\soup2\Documents\JANKFIRE Vault\Assets\skin-refs\knife\karambit_grid.png'
    q = sys.argv[2] if len(sys.argv) > 2 else 'g4'
    M = MARKS[q]
    im = Image.open(grid).crop(QUAD[q])
    m = mask_of(im)
    sat, val = hsv(im)
    H, W = m.shape
    yy, xx = np.mgrid[0:H, 0:W]
    R, J, T = np.array(M['R'], float), np.array(M['J'], float), np.array(M['T'], float)
    ax = (J - R) / np.linalg.norm(J - R)                     # the handle's axis, ring -> guard
    uJ = float(np.dot(J - R, ax))
    ring = ((xx - R[0]) ** 2 + (yy - R[1]) ** 2) <= (M['Ro'] * 1.06) ** 2
    # ---- the regions, as the design draws them: the guard is its four-point star bolster (traced by hand: its left
    # edges lie over the blade, its right side runs into the handle's frame); the blade is what lies beyond it; the
    # handle what lies between it and the ring; the handle's recessed panel is its non-silver inside; the bolster's gem
    # its saturated middle
    perp_px = np.array([ax[1], -ax[0]])
    star = poly_mask(M['STAR'], m.shape)
    guard = m & star
    rest = m & ~star
    blade = biggest(rest, seed=tuple(int(v) for v in M['BSEED']))
    U = (xx - R[0]) * ax[0] + (yy - R[1]) * ax[1]; V = (xx - R[0]) * perp_px[0] + (yy - R[1]) * perp_px[1]
    # (opened: no thin rim wrapped round the ring; nothing past the ring's middle: the frame's tail ends on the ring)
    handle = biggest(opened(rest & ~ring & ~blade & (U > -4), 11), seed=tuple(int(v) for v in M['HSEED']))
    panel = fill_holes(biggest(opened(handle & (sat >= 0.30), 7), seed=tuple(int(v) for v in M['PSEED'])))
    gem = fill_holes(biggest(guard & (sat >= 0.45) & (val > 0.70), seed=tuple(int(v) for v in M['GSEED'])))
    # the frame's outline to extrude: the handle, run on into the ring's outer half where they meet (the ring is its own
    # solid in the model) and 2 mm on under the bolster
    rr = (xx - R[0]) ** 2 + (yy - R[1]) ** 2
    band = (rr <= M['Ro'] ** 2) & (rr >= (0.5 * (M['Ro'] + M['Ri'])) ** 2)     # (the ring's outer half: no hole)
    frame = biggest(closed(handle | (grown(handle, 17) & band), 9) | (grown(handle, 13) & star & m),
                    seed=tuple(int(v) for v in M['HSEED']))
    # (the frame's tail sloping down onto the ring: within a radius of the ring's middle that widens away from it, so
    # the top line runs down into the ring instead of ending in a square stub over it)
    frame = biggest(opened(frame & ((np.sqrt(rr) <= M['Ro'] * 0.95 + 0.9 * np.maximum(U, 0)) | (U > 60)), 5),
                    seed=tuple(int(v) for v in M['HSEED']))
    # pixel -> our frame: the handle's axis onto +z (the ring at the front, -z), y up; the handle's middle on the grip
    s = HANDLE_M / uJ
    perp = np.array([ax[1], -ax[0]])                         # (the axis turned a quarter: toward the image's top)
    def to_m(p):
        d = np.array(p, float) - R
        return (round(float(np.dot(d, ax)) * s - uJ * s / 2 + GRIP_Z, 5), round(float(np.dot(d, perp)) * s, 5))   # (z, y)
    sgn = 1 if to_m(M['T'])[1] < 0 else -1                   # (the blade must curl toward -y)
    def zy(p): z, y = to_m(p); return (z, round(y * sgn, 5))
    out = {'source': '%s %s' % (os.path.basename(grid), q), 'scale_m_per_px': s}
    px = {}
    for name, rm, k, tol in (('guard', guard, 3, 0.8), ('handle', handle, 3, 0.9), ('frame', frame, 7, 0.9), ('panel', panel, 11, 1.2), ('gem', gem, 3, 0.7)):
        px[name] = simplify(smooth(trace(rm), k), tol)
        out[name] = [zy(p) for p in px[name]]
    # ---- the blade: its outline from the tip, split at the star into the spine (outside the curve) and the edge
    # (inside it); each chain runs tip -> root and is carried on under the bolster (hidden in its thickness)
    bl = simplify(smooth(trace(blade), 3), 1.0)
    n = len(bl)
    ti = min(range(n), key=lambda i: (bl[i][0] - T[0]) ** 2 + (bl[i][1] - T[1]) ** 2)
    bl = bl[ti:] + bl[:ti]
    def near_star(p):
        x, y = int(round(p[0])), int(round(p[1]))
        return any(star[min(H - 1, max(0, y + dy)), min(W - 1, max(0, x + dx))] for dy in (-3, 0, 3) for dx in (-3, 0, 3))
    onstar = [i for i in range(n) if near_star(bl[i])]
    c0, c1 = min(onstar), max(onstar)
    chA, chB = bl[:c0 + 1], [bl[0]] + bl[c1:][::-1]
    lowy = lambda ch: sum(p[1] for p in ch) / len(ch)
    edge_c, spine_c = (chA, chB) if lowy(chA) > lowy(chB) else (chB, chA)
    def carry(ch, L):
        (x0, y0), (x1, y1) = ch[-4], ch[-1]
        d = float(np.hypot(x1 - x0, y1 - y0)) or 1.0
        return ch + [(x1 + (x1 - x0) / d * L, y1 + (y1 - y0) / d * L)]
    spine_c = carry(spine_c, M['CARRY'][0]); edge_c = carry(edge_c, M['CARRY'][1])
    out['blade'] = [zy(p) for p in bl]
    out['spine'] = [zy(p) for p in spine_c]
    out['edge'] = [zy(p) for p in edge_c]
    # ---- the panel's centre line (the lit inlay's path): the middle of the panel across the handle's axis, smoothed
    pu, pv = U[panel], V[panel]
    slices = []
    for uc in np.arange(pu.min(), pu.max(), 3.0):
        sel = np.abs(pu - uc) < 1.5
        if sel.sum() > 2: slices.append((uc, pv[sel].min(), pv[sel].max()))
    tall = max(b - a for _, a, b in slices)
    body = [(uc, 0.5 * (a + b)) for uc, a, b in slices if b - a > 0.6 * tall]
    bu = np.array([c for c, _ in body]); cu = np.linspace(bu.min() + 6, bu.max() - 6, 12)
    cv = np.polyval(np.polyfit([c for c, _ in body], [v for _, v in body], 2), cu)
    line_px = [tuple(R + ax * a + perp * b) for a, b in zip(cu, cv)]
    out['inlay'] = [zy(p) for p in line_px]
    # ---- the ring as the design draws it: its hole (the enclosed background by R: centre and the radius of its area)
    # and its outer edge (a least-squares circle through the silhouette's edge on the ring's free side, facing away
    # from the handle): not concentric, the band thicker toward the bottom (the overlay test, 27 Nov)
    hole = biggest(fill_holes(m) & ~m & (rr <= (M['Ro'] * 0.9) ** 2), seed=tuple(int(v) for v in M['R']))
    hy, hx = np.nonzero(hole); Ch = np.array([hx.mean(), hy.mean()]); ri_px = float(np.sqrt(hole.sum() / np.pi))
    ey_, ex_ = np.nonzero(m & ~(np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(__import__('PIL.ImageFilter', fromlist=['x']).MinFilter(3))) > 127))
    dvec = np.stack([ex_ - R[0], ey_ - R[1]], -1); dist = np.hypot(dvec[:, 0], dvec[:, 1])
    free = (dist > M['Ro'] * 0.8) & (dist < M['Ro'] * 1.35) & ((dvec @ ax) < M['Ro'] * 0.2)
    px_, py_ = ex_[free].astype(float), ey_[free].astype(float)
    A_ = np.stack([px_, py_, np.ones_like(px_)], -1); b_ = -(px_ ** 2 + py_ ** 2)
    c_ = np.linalg.lstsq(A_, b_, rcond=None)[0]; Co = np.array([-c_[0] / 2, -c_[1] / 2]); ro_px = float(np.sqrt(Co @ Co - c_[2]))
    out['ring'] = {'centre': zy(Ch), 'ri': round(ri_px * s, 5), 'outer_centre': zy(Co), 'ro': round(ro_px * s, 5),
                   'px': {'hole': [round(float(v), 1) for v in Ch], 'ri': round(ri_px, 1), 'outer': [round(float(v), 1) for v in Co], 'ro': round(ro_px, 1)}}
    out['tip'] = zy(M['T'])
    out['junction'] = zy(M['J'])
    # ---- the check picture: every region drawn from these outlines, over the design at 35 %
    from PIL import ImageDraw
    chk = Image.new('RGB', (W, H))
    dr = ImageDraw.Draw(chk)
    dr.ellipse((R[0] - M['Ro'], R[1] - M['Ro'], R[0] + M['Ro'], R[1] + M['Ro']), outline=(43, 46, 51), width=int(M['Ro'] - M['Ri']))
    dr.ellipse((R[0] - M['Ro'], R[1] - M['Ro'], R[0] + M['Ro'], R[1] + M['Ro']), fill=(43, 46, 51))
    dr.ellipse((R[0] - M['Ri'], R[1] - M['Ri'], R[0] + M['Ri'], R[1] + M['Ri']), fill=(0, 0, 0))
    dr.polygon([tuple(p) for p in px['frame']], fill=(195, 202, 211))
    dr.polygon([tuple(p) for p in px['panel']], fill=(76, 106, 94))
    dr.line([tuple(p) for p in line_px], fill=(95, 214, 196), width=4)
    sp, ed = resample(spine_c, 40), resample(edge_c, 40)
    inn = [(e[0] + 0.34 * (a[0] - e[0]), e[1] + 0.34 * (a[1] - e[1])) for a, e in zip(sp, ed)]
    dr.polygon(sp + inn[::-1], fill=(43, 46, 51)); dr.polygon(ed + inn[::-1], fill=(238, 241, 245))
    dr.polygon([tuple(p) for p in px['guard']], fill=(214, 220, 228)); dr.polygon([tuple(p) for p in px['gem']], fill=(95, 214, 196))
    chk = Image.blend(chk, im.convert('RGB'), 0.35)
    chk.save(os.path.join(os.environ.get('TRACE_CHECK_DIR', HERE), 'karambit_trace_check.png'))
    json.dump(out, open(os.path.join(HERE, 'karambit_trace.json'), 'w'), indent=0)
    print({k: (len(v) if isinstance(v, list) else v) for k, v in out.items()})


if __name__ == '__main__':
    main()
