# REVENUE PROTECTION (OVERDUE, Act I climax, mission 6 TICKETS, PLEASE): the boss that fills a 9.2 m bore rail tunnel.
# An original design: the fallen station sign of Hill Central (a ☺ CORP smiley in white vitreous enamel, 8.7 m across,
# twelve plates bolted to a steel lattice inside a riveted hoop like a tunnelling machine's shield) on the front of the
# 17:32, four hundred burned commuters regrown as one piece. Real references: enamel station signs, bulkhead lamps,
# TBM shields, charred timber, conductor's punches, lanyards. Built from code, no downloaded assets.
#
# Root space = game metres: x right, y up, +z toward the train (the mask FACES +z). The origin is the middle of the
# bore on the plane of the plates' backs. "L" is the mask's own left = +x = on your right when you face it.
#
#   mask                 empty: turn / drop this and the whole sign goes (it hangs off `hang_bolt` in the last phase)
#     plate_00..11       the enamel plates, each its own mesh with its bolts. 00-03 inner (quadrants from +x,
#                        counter-clockwise), 04-11 outer (45 degrees each from +x). 02 03 08 09 10 11 are the lower ones
#     plate_NN_crazed    the same plate broken into shards that still hang together (hidden until the game wants it)
#     plate_NN_up/_low   02 03 08 11 split along the smile crack: _low drops in stage 3, _up stays (hidden until then)
#     frame, frame_low   the back lattice, hoop and hub; frame_low is everything under the smile crack (drops in stage 3)
#     eye_R, eye_L       the lamp housings (bezel + can), origin on the hinge pin: swing about y to open them
#     eye_L_blown        stage 2: the left housing burst from inside (hidden until then)
#     eye_cluster        stage 2: the real eyes behind it (hidden); eyeball_00.. are their own nodes (origin = centre)
#     anchors, anchor_hang   ☺ CORP's clamps and straps that bolt the sign on; anchor_hang is the last one to go
#   mass                 empty: the 17:32
#     mass_ne, mass_nw, mass_sw, mass_se   the plug in four pieces (it comes apart along a cross at the end)
#     mass_lod           the whole plug as one far mesh with the near one baked into its texture (hidden)
#   inspector            empty at his waist: insp_body, insp_head, insp_armR > insp_foreR > insp_punch_lever,
#                        insp_armL > insp_foreL, insp_base (the mound he is fused into)
# rp_arm.glb (its own root): arm_seg (1.5 m, tiles along +z), arm_knot (the lit wrist), arm_hand > palm + f0..f4 >
#   f?_a > f?_b > f?_c (curl each about its local x), arm_stump.
# Everything the fight needs to know (boxes, stages, markers, sockets) is written to revenue_protection.parts.json.
#
# run: blender52 -b -P tools/blender/make_revenue_protection.py
#      flags after '--': --no-export --no-sheet --no-ao --qa --stats --only=mask,mass,inspector,arm
#      --preview=<dir> [--views=front,q,...] [--stage=0..3] (quick looks while iterating)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rpkit import *
from lib import _link, _image, _obj
import rpkit

FID = 'revenue_protection'
OUT = os.path.join(MODELS, 'story')
ONLY = set(arg('only').split(',')) if isinstance(arg('only'), str) else None
def want(k): return ONLY is None or k in ONLY

# ------------------------------------------------------------ the numbers
R_BORE = 4.6          # the tunnel
FLOOR_Y = -3.13       # the top of the track bed in that tunnel (the concept's): the disc sinks into it
RM = 4.35             # the sign: nominal radius of the enamel
R_IN = 2.30           # the seam between the 4 inner and the 8 outer plates
R_HUB = 0.22          # the inner plates stop here, under the hub cap
GAP = 0.028           # half a seam
PT = 0.14             # plate thickness: back at z = 0, face at z = PT
EYE_C = (1.25, 0.70)  # the left eye's centre (the right one is mirrored)
EYE_A, EYE_B = 0.60, 1.08  # the hole's half width and half height
HOOP_R = 4.41
MASS_R = 4.52
MASS_Z0, MASS_Z1 = -0.62, -6.6   # the plug: front face (under the lattice) and where its back starts to round off
HANG_A = math.radians(100)       # the last anchor
SOCKETS = [14, 46, 76, 104, 134, 166, 194, 226, 256, 284, 314, 346]  # where arms root, degrees round the rim
SMILE_C, SMILE_R, SMILE_X = (0.0, 2.53), 4.03, 2.6


def crack_y(x):
    """the smile crack, rim to rim: the painted smile's arc in the middle, then a shallow run out to the hoop"""
    ax = abs(x)
    if ax <= SMILE_X: return SMILE_C[1] - math.sqrt(SMILE_R ** 2 - ax * ax)
    y0 = SMILE_C[1] - math.sqrt(SMILE_R ** 2 - SMILE_X ** 2)
    return y0 + (ax - SMILE_X) * 0.2


def below_crack(x, y): return y < crack_y(x)


def plate_spec(i):
    """(r0, r1, a0, a1) of plate i"""
    if i < 4: return R_HUB, R_IN, i * math.pi / 2, (i + 1) * math.pi / 2
    return R_IN, RM, (i - 4) * math.pi / 4, (i - 3) * math.pi / 4


def plate_at(x, y):
    r = math.hypot(x, y); a = math.atan2(y, x) % (2 * math.pi)
    return int(a / (math.pi / 2)) if r < R_IN else 4 + int(a / (math.pi / 4))


def plate_pt(i, u, v, inset=0.0):
    """a point on plate i: u across (angle), v out (radius), both 0..1, the outline moved in by inset"""
    r0, r1, a0, a1 = plate_spec(i)
    r = lerp(r0 + GAP + inset, r1 - GAP - inset, v)
    da = math.asin(min(0.99, (GAP + inset) / r))
    a = lerp(a0 + da, a1 - da, u)
    return r * math.cos(a), r * math.sin(a)


def bolts_of(i):
    """where plate i's bolts go (x, y, missing): along its edges, over the lattice"""
    r0, r1, a0, a1 = plate_spec(i); rn = Rnd(900 + i); out = []; e = 0.15
    def at(r, a): out.append((r * math.cos(a), r * math.sin(a)))
    da = lambda r: math.asin((GAP + e) / r)
    if i < 4:
        for t in (0.2, 0.5, 0.8): at(r1 - e, lerp(a0 + da(r1), a1 - da(r1), t))
        for rr in (0.75, 1.5): at(rr, a0 + da(rr)); at(rr, a1 - da(rr))
    else:
        for t in (0.11, 0.37, 0.63, 0.89): at(r1 - e - 0.03, lerp(a0, a1, t))
        for t in (0.25, 0.75): at(r0 + e, lerp(a0 + da(r0), a1 - da(r0), t))
        for rr in (2.95, 3.65): at(rr, a0 + da(rr)); at(rr, a1 - da(rr))
    gone = {0: [2], 5: [1], 6: [7], 7: [0, 3], 8: [5], 10: [2], 11: [8], 3: [4]}.get(i, [])
    return [(x, y, k in gone) for k, (x, y) in enumerate(out) if not eye_hit(x, y, 0.22)]


def eye_hit(x, y, grow=0.0):
    return ((abs(x) - EYE_C[0]) / (EYE_A + grow)) ** 2 + ((y - EYE_C[1]) / (EYE_B + grow)) ** 2 < 1.0


# ------------------------------------------------------------ textures
EN = 512          # the enamel map: the whole face seen straight on, plus swatches in the corners
EN_M = 9.2        # metres across it
def en_uv(p): return (0.5 + p.x / EN_M, 0.5 + p.y / EN_M)
def en_px(x, y): return (0.5 + x / EN_M) * EN, (0.5 - y / EN_M) * EN


def blocky(r, size, cell):
    n = r.random((size // cell + 1, size // cell + 1))
    return np.kron(n, np.ones((cell, cell)))[:size, :size]


def paint_enamel(name, crazed=False):
    """white vitreous enamel after sixty years on a station front and a while in a tunnel: per-plate tone, grime in
    the seams, rust blooming from every bolt and running down, chips to the black ground coat and the steel, soot above
    the lamp holes and rust tears under them, the ghost of the painted smile and its outline, stencilled plate numbers.
    crazed = the same with a net of cracks and flaked edges (the plates that are about to fall)."""
    S = EN; A = Atlas(name, S, S, rough=0.2, metal=0.0); px = A.px; orm = A.orm
    r = np.random.default_rng(17)
    yy, xx = np.mgrid[0:S, 0:S]
    X = (xx + 0.5) / S * EN_M - EN_M / 2; Y = EN_M / 2 - (yy + 0.5) / S * EN_M
    Rr = np.hypot(X, Y); Aa = np.arctan2(Y, X) % (2 * math.pi)
    pid = np.where(Rr < R_IN, (Aa / (math.pi / 2)).astype(int), 4 + (Aa / (math.pi / 4)).astype(int))
    tones = [0xece8dc, 0xe4dfd0, 0xeeebe2, 0xdcd6c6, 0xe8e4d8, 0xd8d2c0, 0xeeeadf, 0xe2ddd0, 0xdad4c4, 0xece8dc, 0xe0dacb, 0xe9e5da]
    col = np.stack([hexrgb(c) for c in tones])[pid]
    n1 = blocky(r, S, 32); n2 = blocky(r, S, 8); n3 = blocky(r, S, 2)
    col = col * (0.93 + 0.07 * n1[:, :, None]) * (0.965 + 0.035 * n2[:, :, None]) * (0.985 + 0.015 * n3[:, :, None])
    rough = np.full((S, S), 0.3) + 0.14 * n2; metal = np.zeros((S, S))
    def lay(mask, c, a=1.0, ro=None, me=None):
        nonlocal col, rough, metal
        m = (mask * a)[:, :, None] if mask.dtype != bool else (mask[:, :, None] * a)
        col = col * (1 - m) + hexrgb(c)[None, None] * m
        if ro is not None: rough = rough * (1 - m[:, :, 0]) + ro * m[:, :, 0]
        if me is not None: metal = metal * (1 - m[:, :, 0]) + me * m[:, :, 0]
    # yellowing and tunnel grime: heavier low down (it drags on the track bed) and round the rim (it scrapes the bore)
    lay(np.clip((n1 - 0.55) * 2.2, 0, 1) * 0.5, 0xc9b98e, 0.5)
    low = np.clip((-Y - 2.2) / 2.2, 0, 1) ** 1.5
    lay(low * (0.5 + 0.5 * n2), 0x3a2e28, 0.75, ro=0.8)
    rim = np.clip((Rr - (RM - 0.3)) / 0.3, 0, 1) ** 2
    lay(rim * (0.4 + 0.6 * n3), 0x2c2622, 0.8, ro=0.75)
    # grime and rust creeping in from the seams
    sa_in = np.abs(((Aa + math.pi / 4) % (math.pi / 2)) - math.pi / 4); sa_out = np.abs(((Aa + math.pi / 8) % (math.pi / 4)) - math.pi / 8)
    d_seam = np.where(Rr < R_IN, Rr * np.sin(np.minimum(sa_in, math.pi / 2)), Rr * np.sin(sa_out))
    d_seam = np.minimum(d_seam, np.abs(Rr - R_IN)); d_seam = np.minimum(d_seam, np.abs(Rr - R_HUB - 0.08))
    seam = np.exp(-np.clip(d_seam - GAP, 0, 9) / 0.07)
    lay(seam * (0.35 + 0.65 * n2), 0x6a5238, 0.55, ro=0.7)
    lay((seam > 0.6) & (n3 > 0.5), 0x5e3418, 0.75, ro=0.9)
    # the ghost of the paint: the smile and the outline ring. paler where the paint kept the weather off, a few flecks left
    ysm = SMILE_C[1] - np.sqrt(np.clip(SMILE_R ** 2 - X ** 2, 0, None))
    dsm = np.where(np.abs(X) <= SMILE_X, np.abs(Y - ysm) * np.sqrt(np.clip(1 - (X / SMILE_R) ** 2, 0.2, 1)),
                   np.hypot(np.abs(X) - SMILE_X, Y - (SMILE_C[1] - math.sqrt(SMILE_R ** 2 - SMILE_X ** 2))))
    ghost = (dsm < 0.17) | (np.abs(Rr - 4.02) < 0.06)
    gn = blocky(r, S, 2); gn4 = blocky(r, S, 6)
    lay(ghost * (0.45 + 0.55 * gn4), 0x9c978c, 0.42, ro=0.34)
    lay(ghost & (gn > 0.84) & (gn4 > 0.35), 0x1a1614, 0.9, ro=0.5)
    # soot over the lamp holes (they burned), rust tears under them
    for sx in (-1, 1):
        ex, ey = sx * EYE_C[0], EYE_C[1]
        up = np.clip((Y - ey) / 2.3, 0, 1); wdt = EYE_A * (1.25 + 0.5 * up)
        soot = np.clip(1 - np.abs(X - ex - 0.12 * sx * up) / wdt, 0, 1) ** 0.8 * np.clip(1.15 - up * 1.15, 0, 1) * (Y > ey - 0.2) * (0.5 + 0.5 * n2) * (0.75 + 0.25 * n3)
        lay(np.clip(soot * 1.25, 0, 1), 0x1c181c, 0.8, ro=0.9)
        halo = np.clip(1.6 - np.sqrt(((X - ex) / (EYE_A + 0.28)) ** 2 + ((Y - ey) / (EYE_B + 0.28)) ** 2) * 1.6, 0, 1)
        lay(halo * (0.5 + 0.5 * n3), 0x2a2220, 0.7, ro=0.85)
        for k, (ox, ln, w) in enumerate(((-0.34, 1.9, 0.07), (-0.06, 2.6, 0.1), (0.22, 1.5, 0.06), (0.4, 0.9, 0.05))):
            x0 = ex + ox; y0 = ey - EYE_B * math.sqrt(max(0.05, 1 - (ox / EYE_A) ** 2)) - 0.1
            t = np.clip((y0 - Y) / ln, 0, 1); wob = 0.04 * np.sin(Y * 5 + k)
            tear = (np.abs(X - x0 - wob) < w * (1 - 0.6 * t)) & (Y < y0) & (Y > y0 - ln)
            lay(tear * (1 - t) ** 0.7 * (0.6 + 0.4 * n3), 0x5a2e16 if k % 2 else 0x34140e, 0.8, ro=0.85)
    # dried dark runs out of the seams (what is behind it leaks)
    for k in range(34):
        a = r.uniform(0, 2 * math.pi); rr_ = r.choice([R_IN, R_IN, RM - 0.05, r.uniform(0.6, 4.2)])
        x0, y0 = rr_ * math.cos(a), rr_ * math.sin(a) - 0.03
        if rr_ not in (R_IN, RM - 0.05): a2 = round(a / (math.pi / 4)) * (math.pi / 4); x0, y0 = rr_ * math.cos(a2), rr_ * math.sin(a2)
        ln = r.uniform(0.25, 1.1); w = r.uniform(0.025, 0.06)
        t = np.clip((y0 - Y) / ln, 0, 1)
        run = (np.abs(X - x0 - 0.02 * np.sin(Y * 9 + k)) < w * (1 - 0.7 * t)) & (Y < y0) & (Y > y0 - ln)
        lay(run * (1 - t) ** 0.5, 0x2a0c0c, 0.8, ro=0.35)
    # bolts: a rust bloom and a run down the face from each (the missing ones worst)
    bolt_list = [(x, y, g, i) for i in range(12) for x, y, g in bolts_of(i)]
    for k, (bx, by, gone, i) in enumerate(bolt_list):
        d = np.hypot(X - bx, Y - by)
        bloom = np.clip(1 - d / (0.17 if gone else 0.115), 0, 1) ** 0.7 * (0.55 + 0.45 * n3)
        lay(bloom, 0x5e3a20, 0.8, ro=0.9)
        ln = r.uniform(0.35, 1.5) * (1.4 if gone else 1.0); w = r.uniform(0.03, 0.055)
        t = np.clip((by - Y) / ln, 0, 1)
        run = (np.abs(X - bx - 0.015 * np.sin(Y * 11 + k)) < w * (1 - 0.65 * t)) & (Y < by) & (Y > by - ln)
        lay(run * (1 - t) ** 0.8 * (0.6 + 0.4 * n3), 0x8a5a30 if k % 3 else 0x5a3018, 0.55, ro=0.8)
        if gone: lay(d < 0.045, 0x0a0808, 1.0, ro=0.9)
    # chips: the glass flaked off to the blue-black ground coat, rusted steel in the middle of the big ones, a thin
    # rust edge and a stain running down from it. many specks, a few big wounds, most of them at an edge
    n_chip = 900 if crazed else 560
    for k in range(n_chip):
        a = r.uniform(0, 2 * math.pi); rr_ = math.sqrt(r.uniform(0.01, 1)) * RM
        if r.random() < 0.6:
            i = int(r.integers(0, 12)); u, v = r.random(), r.random()
            e = int(r.integers(0, 4)); u, v = [(u, 0.0), (u, 1.0), (0.0, v), (1.0, v)][e]
            cx, cy = plate_pt(i, u, v, abs(r.normal(0, 0.07)))
        else: cx, cy = rr_ * math.cos(a), rr_ * math.sin(a)
        q_ = r.random()
        rad = r.uniform(0.012, 0.035) if q_ < 0.68 else (r.uniform(0.04, 0.085) if q_ < 0.95 else r.uniform(0.1, 0.2))
        if crazed: rad *= 1.25
        pxc, pyc = en_px(cx, cy); rp = rad / EN_M * S; q = int(rp * 2.2) + 3; ext = int(rp * 5) + 2
        x0, x1, y0, y1 = max(0, int(pxc) - q), min(S, int(pxc) + q), max(0, int(pyc) - q), min(S, int(pyc) + q + ext)
        if x1 <= x0 or y1 <= y0: continue
        sl = (slice(y0, y1), slice(x0, x1)); sy, sxx = np.mgrid[y0:y1, x0:x1]
        ring_ = blob_mask(0, 0, pxc, pyc, rp + 1.0, 1000 + k, 0.4, sy, sxx); core = blob_mask(0, 0, pxc, pyc, rp, 1000 + k, 0.4, sy, sxx)
        steel = blob_mask(0, 0, pxc + rp * 0.1, pyc + rp * 0.1, rp * 0.55, 2000 + k, 0.5, sy, sxx) & (rp > 2.0)
        if rp > 1.6:  # the stain under it
            tt = np.clip((sy - pyc) / (rp * 4.5), 0, 1); st_ = (np.abs(sxx + 0.5 - pxc) < rp * 0.8 * (1 - 0.7 * tt)) & (sy > pyc) & (sy < pyc + rp * 4.5)
            al = (st_ * (1 - tt) * 0.4)[:, :, None]; col[sl] = col[sl] * (1 - al) + hexrgb(0x7a4a26)[None, None] * al; rough[sl] = np.where(st_, 0.6, rough[sl])
        sh_ = 0.85 + 0.3 * r.random()
        for msk, c, ro, me in ((ring_ & ~core, 0x6a4024, 0.85, 0.0), (core, 0x22212a, 0.55, 0.0), (steel, 0x4e2c1a if k % 3 else 0x5a5450, 0.7, 0.0 if k % 3 else 0.5)):
            col[sl][msk] = hexrgb(c) * sh_; rough[sl][msk] = ro; metal[sl][msk] = me
    # scrapes: bright steel arcs where the rim meets the bore, and a ground-off band at the bottom
    for k in range(70):
        a0_ = r.uniform(0, 2 * math.pi); rr_ = RM - r.uniform(0.0, 0.22); ln = r.uniform(0.05, 0.3)
        m = (np.abs(Rr - rr_) < 0.012) & (np.abs(((Aa - a0_ + math.pi) % (2 * math.pi)) - math.pi) < ln / 2)
        lay(m, 0x8a8a8c, 0.9, ro=0.4, me=0.7)
    if crazed:  # a net of cracks: cells of 15 to 40 cm, the lines dark, flakes missing along them
        pts = r.uniform(-RM, RM, (460, 2))
        d1 = np.full((S, S), 9.0); d2 = np.full((S, S), 9.0)
        for (cx, cy) in pts:
            d = np.hypot(X - cx, Y - cy); sw = d < d1
            d2 = np.where(sw, d1, np.minimum(d2, d)); d1 = np.where(sw, d, d1)
        edge = (d2 - d1)
        lay(edge < 0.0095, 0x2a2422, 0.8, ro=0.8)
        lay((edge < 0.04) & (n3 > 0.8) & (n1 > 0.4), 0x24201e, 0.9, ro=0.7)
        lay((edge < 0.03) & (n2 > 0.86), 0x6a3c1e, 0.6, ro=0.9)
    # stencilled plate numbers (the fitters') and the fabricator's mark
    px[:] = np.clip(col, 0, 1)
    for i in range(12):
        cx, cy = plate_pt(i, 0.5, 0.2 if i >= 4 else 0.62, 0.0)
        x, y = en_px(cx, cy)
        text_px(px, 'P%02d' % i, int(x) - 9, int(y) - 3, 1, 0x4a4640)
    out = np.hypot(X, Y) > RM + 0.02
    px[out] = hexrgb(0x2a2420); rough[out] = 0.8
    orm[:, :, 1] = np.clip(rough, 0.05, 1); orm[:, :, 2] = np.clip(metal, 0, 1)
    # corner swatches (outside the disc): the plates' backs and flanges, a broken edge, bolt heads, washers, holes
    A.cell('back', 2, 2, 48, 48, 0x2e2a2c, rough=0.75, metal=0.1, var=0.16, seed=3, speck=0x7a3c1a, speck_p=0.14)
    A.cell('flange', 52, 2, 24, 48, 0xcfc8b6, rough=0.4, var=0.1, seed=4, speck=0x7a3c1a, speck_p=0.22)
    e = A.cell('edge', 2, 52, 24, 24, 0x3a3432, rough=0.7, metal=0.4, var=0.2, seed=5, speck=0x8a4a22, speck_p=0.2)
    e[:, 21:] = hexrgb(0xe8e4d8); e[:, 19:21] = hexrgb(0x141214); e[:, :2] = hexrgb(0x141214)   # the glass coat, the ground coat, the steel between
    A.cell('bolt', 28, 52, 24, 24, 0x3e3430, rough=0.65, metal=0.55, var=0.22, seed=6, speck=0x6a4026, speck_p=0.22)
    A.cell('washer', 54, 52, 22, 22, 0x33292a, rough=0.8, metal=0.3, var=0.22, seed=7, speck=0x5e3a22, speck_p=0.3)
    return A


TRIM_CELLS = [  # name, colour, roughness, metal, variation, speck colour, speck share
    ('steel', 0x4a4844, 0.55, 0.7, 0.14, 0x6a4a34, 0.1), ('rust', 0x5c3622, 0.9, 0.1, 0.22, 0x3a2012, 0.25), ('rustdark', 0x33221c, 0.9, 0.15, 0.2, 0x5c3622, 0.18),
    ('cast', 0x24232a, 0.55, 0.5, 0.12, 0x4a3024, 0.08), ('bright', 0xa8a8aa, 0.32, 0.9, 0.2, 0x3a3432, 0.25), ('soot', 0x0c0a0c, 0.95, 0.0, 0.3, 0x1c1618, 0.2),
    ('brass', 0xc89a3a, 0.3, 1.0, 0.1, 0x6a4a1a, 0.1), ('chrome', 0xc8ccd4, 0.14, 1.0, 0.05, None, 0.0), ('glass', 0x4c6468, 0.06, 0.3, 0.12, 0x9ab8bc, 0.08),
    ('white', 0xf2f4f2, 0.25, 0.0, 0.03, None, 0.0), ('cyan', 0x4fd8ff, 0.3, 0.0, 0.04, None, 0.0), ('yellow', 0xffe14d, 0.35, 0.0, 0.04, None, 0.0),
    ('black', 0x141216, 0.4, 0.0, 0.1, None, 0.0), ('chain', 0x3a3a3e, 0.45, 0.8, 0.2, 0x7a4020, 0.15), ('navy', 0x121a3a, 0.7, 0.0, 0.1, 0x0a0e20, 0.2),
    ('peak', 0x06070c, 0.12, 0.0, 0.05, None, 0.0),
]


def trim_atlas():
    A = Atlas('rp_trim', 128, 128, rough=0.6)
    for k, (nm, c, ro, me, var, sp, spp) in enumerate(TRIM_CELLS):
        A.cell(nm, (k % 8) * 16, (k // 8) * 16, 16, 16, c, rough=ro, metal=me, var=var, seed=40 + k, speck=sp, speck_p=spp)
    b = A.sub('bright')  # scraped: streaks along v, scorched between
    b[:] = b * 0.62
    for x in (2, 6, 11): b[:, x] = hexrgb(0xb8b8bc)
    for x in (0, 8, 9, 14): b[:, x] = hexrgb(0x2a2422)
    hz = A.cell('hazard', 0, 32, 32, 16, 0xffd21a, rough=0.45); yy, xx = np.mgrid[0:16, 0:32]; hz[((xx + yy) // 4) % 2 == 0] = hexrgb(0x141414)
    st = A.cell('strap', 32, 32, 64, 16, 0x4fd8ff, rough=0.7)   # ☺ CORP ratchet strap: woven cyan, the logo printed along it
    st[::2, :] = st[::2, :] * 0.9; st[0, :] = st[-1, :] = hexrgb(0x2a90b8)
    for x0 in (4, 36): px_disc(st, x0 + 4, 8, 4.5, 0xffe14d); px_disc(st, x0 + 4, 8, 4.5, 0x111111, r_in=3.6); st[6, x0 + 2] = st[6, x0 + 5] = hexrgb(0x111111); st[9, x0 + 2:x0 + 6] = hexrgb(0x111111); text_px(st, 'CORP', x0 + 10, 5, 1, 0x0a3a50)
    tg = A.cell('tag', 0, 48, 96, 40, 0xffe14d, rough=0.4)     # the asset tag ☺ CORP riveted to its face
    tg[:2] = tg[-2:] = hexrgb(0x141414); tg[:, :2] = tg[:, -2:] = hexrgb(0x141414)
    px_disc(tg, 12, 12, 8, 0x141414); px_disc(tg, 12, 12, 6.6, 0xffe14d); tg[9:11, 9:11] = tg[9:11, 14:16] = hexrgb(0x141414)
    for xk in range(8, 17): tg[14 + (1 if 9 < xk < 15 else 0), xk] = hexrgb(0x141414)
    text_px(tg, 'CORP ASSET', 26, 4, 1, 0x141414); text_px(tg, '17-32', 26, 13, 1, 0xc02020)
    text_px(tg, 'REVENUE', 6, 23, 1, 0x141414); text_px(tg, 'PROTECTION', 6, 31, 1, 0x141414)
    text_px(tg, 'DO NOT', 56, 23, 1, 0xc02020); text_px(tg, 'FEED', 62, 31, 1, 0xc02020)
    return A


M = {}; AT = {}
def materials():
    AT['en'] = paint_enamel('rp_enamel'); M['en'] = AT['en'].material('rp_enamel', use_orm=True, metal_map=False)
    AT['cz'] = paint_enamel('rp_enamel_crazed', crazed=True); M['cz'] = AT['cz'].material('rp_enamel_crazed', use_orm=True, metal_map=False)
    AT['tr'] = trim_atlas(); M['tr'] = AT['tr'].material('rp_steel', use_orm=True)
    M['void'] = mat('rp_void', 0x060506, rough=1.0)   # the inside of the lamp cans: no shine at all, so the eyes stay holes
    M['void'].node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.0
    mass_materials(); glow_materials()
    return M


def TR(k, m=0.5): return AT['tr'].quad(k, m)
def TRF(k, m=0.5): return AT['tr'].fit(k, m)


# ------------------------------------------------------------ the mask: plates
def warp(x, y):
    """the enamel isn't flat any more: long ripples and a few dents (metres out of plane)"""
    z = 0.006 * fbm(x * 0.8, y * 0.8, 3.1) + 0.004 * fbm(x * 2.3, y * 2.3, 9.4, 2)
    for dx, dy, rad, dep in DENTS:
        d = math.hypot(x - dx, y - dy)
        if d < rad: z -= dep * (0.5 + 0.5 * math.cos(math.pi * d / rad))
    return z


DENTS = [(-2.9, 1.1, 0.5, 0.045), (3.2, -1.7, 0.42, 0.04), (0.9, -0.9, 0.36, 0.03), (-1.0, 3.3, 0.4, 0.035), (-3.4, -1.9, 0.5, 0.05), (2.5, 3.0, 0.3, 0.03), (-0.5, -3.6, 0.45, 0.04)]
BENT = {7: (0.0, 1.0, 0.11), 10: (1.0, 1.0, 0.09), 4: (1.0, 1.0, 0.06), 1: (0.0, 1.0, 0.04)}  # plate: corner (u, v) curled forward by this much


def plate_mesh(i, mat_en):
    """one plate as a closed pan: a gridded face (so it can ripple and dent), a chamfer, flanged sides, a flat back"""
    r0, r1, a0, a1 = plate_spec(i)
    na, nr = (10, 4) if i < 4 else (8, 4)
    bi = bz = 0.024; cc = 0.05
    arc = (a1 - a0) * (r0 + r1) / 2; rad = r1 - r0
    us = [0.0, cc / arc] + [k / na for k in range(1, na)] + [1 - cc / arc, 1.0]
    vs = [0.0, cc / rad] + [k / nr for k in range(1, nr)] + [1 - cc / rad, 1.0]
    nu, nv = len(us), len(vs)
    def P(u, v, inset, z):
        # the four corners are cut at 45 degrees
        cu = min(u, 1 - u) < 1e-9; cv = min(v, 1 - v) < 1e-9
        if cu and cv: u = cc / arc if u < 0.5 else 1 - cc / arc; v = cc / rad * 0.0 if False else v
        x, y = plate_pt(i, u, v, inset)
        if cu and cv:  # pull the corner in along its diagonal
            x2, y2 = plate_pt(i, 0.0 if u < 0.5 else 1.0, cc / rad if v < 0.5 else 1 - cc / rad, inset)
            x, y = (x + x2) / 2, (y + y2) / 2
        return x, y, z
    bm = bmesh.new(); top = {}
    bent = BENT.get(i)
    for iu, u in enumerate(us):
        for iv, v in enumerate(vs):
            x, y, z = P(u, v, bi, PT)
            edge = min(u, 1 - u) * arc; edge = min(edge, min(v, 1 - v) * rad)
            z += warp(x, y) * min(1.0, edge / 0.3)
            if bent:
                d = math.hypot((u - bent[0]) * arc, (v - bent[1]) * rad)
                if d < 0.9: z += bent[2] * (1 - d / 0.9) ** 2
            top[iu, iv] = bm.verts.new((x, y, z))
    for iu in range(nu - 1):
        for iv in range(nv - 1):
            bm.faces.new((top[iu, iv], top[iu + 1, iv], top[iu + 1, iv + 1], top[iu, iv + 1]))
    loop = [(iu, 0) for iu in range(nu)] + [(nu - 1, iv) for iv in range(1, nv)] + [(iu, nv - 1) for iu in range(nu - 2, -1, -1)] + [(0, iv) for iv in range(nv - 2, 0, -1)]
    def ringv(inset, z, lift=True):
        out = []
        for iu, iv in loop:
            x, y, zz = P(us[iu], vs[iv], inset, z)
            if lift and bent:
                d = math.hypot((us[iu] - bent[0]) * arc, (vs[iv] - bent[1]) * rad)
                if d < 0.9: zz += bent[2] * (1 - d / 0.9) ** 2
            out.append(bm.verts.new((x, y, zz)))
        return out
    r_top = [top[k] for k in loop]; r_ch = ringv(0.0, PT - bz); r_bot = ringv(0.0, 0.0)
    n = len(loop)
    for a, b in ((r_top, r_ch), (r_ch, r_bot)):
        for k in range(n): bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    cx, cy = plate_pt(i, 0.5, 0.5, 0.0); cen = bm.verts.new((cx, cy, 0.0))
    for k in range(n): bm.faces.new((r_bot[k], r_bot[(k + 1) % n], cen))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for v in bm.verts: v.co = gv(v.co.x, v.co.y, v.co.z)
    me = bpy.data.meshes.new('plate_%02d' % i); bm.to_mesh(me); bm.free()
    me.materials.append(mat_en)
    o = _link(bpy.data.objects.new('plate_%02d' % i, me))
    return o


def prism_cutter(poly, z0=-0.6, z1=0.8, name='cut', m=None):
    """a prism over a 2D outline (game x, y) from z0 to z1, with a UV layer so booleans can hand its faces over"""
    bm = bmesh.new()
    a = [bm.verts.new(gv(x, y, z0)) for x, y in poly]; b = [bm.verts.new(gv(x, y, z1)) for x, y in poly]
    n = len(poly)
    bm.faces.new(a); bm.faces.new(b)
    for k in range(n): bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.loops.layers.uv.new('UVMap')
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if m is not None: me.materials.append(m)
    return _link(bpy.data.objects.new(name, me))


def boolean(o, cutter, op='DIFFERENCE', keep=False):
    md = o.modifiers.new('bool', 'BOOLEAN'); md.object = cutter; md.operation = op; md.solver = 'EXACT'
    try: md.material_mode = 'TRANSFER'
    except Exception: pass
    bpy.context.view_layer.objects.active = o
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    o.select_set(True)
    bpy.ops.object.modifier_apply(modifier=md.name)
    if not keep: bpy.data.objects.remove(cutter, do_unlink=True)
    return o


def plate_uv(o, atlas, cut_mat=None):
    """the face and its chamfer seen straight on in the enamel map; flanges, the back and broken edges on swatches.
    Faces that came from a boolean cutter (cut_mat's slot) are the broken edges."""
    me = o.data
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=2e-4)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_area() < 1e-9], context='FACES')
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=2e-5)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_area() < 1e-9], context='FACES')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.normal_update()
    uvl = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    cut_i = next((k for k, m in enumerate(me.materials) if m is cut_mat), -1) if cut_mat else -1
    tex = atlas.tex
    for f in bm.faces:
        n = g_of(f.normal)
        if f.material_index == cut_i and cut_i >= 0: key = 'edge'
        elif n.z > 0.3: key = None
        elif n.z < -0.3: key = 'back'
        else: key = 'flange'
        if key is None:
            for l in f.loops: l[uvl].uv = en_uv(g_of(l.vert.co))
        else:
            P = [g_of(l.vert.co) for l in f.loops]
            if key == 'back': st = [(p.x * 1.7 % 1.0, p.y * 1.7 % 1.0) for p in P]; c = sum(P, V3()) / len(P); st = [((p.x - c.x) * 1.2 + 0.5, (p.y - c.y) * 1.2 + 0.5) for p in P]
            else:
                t = V3((-n.y, n.x, 0)); t = t.normalized() if t.length > 1e-6 else V3((1, 0, 0)); c = sum(P, V3()) / len(P)
                st = [((p - c).dot(t) * 1.6 + 0.5, p.z / PT * 0.9 + 0.05) for p in P]
            for l, (s_, t_) in zip(f.loops, st): l[uvl].uv = px_uv(atlas.R[key], tex, min(1, max(0, s_)), min(1, max(0, t_)), 1.0)
        f.material_index = 0; f.smooth = True
    bm.to_mesh(me); bm.free()
    while len(me.materials) > 1: me.materials.pop(index=len(me.materials) - 1)
    fix_uv(o)
    me.set_sharp_from_angle(angle=math.radians(50))   # (the 45 degree chamfer shades as a rolled edge, and shares its vertices)
    if 'tint' not in me.color_attributes:  # (joined to its bolts later: their tint layer must find one here)
        ca = me.color_attributes.new('tint', 'BYTE_COLOR', 'CORNER'); ca.data.foreach_set('color', [1.0] * (4 * len(me.loops)))
    return o


def plate_lift(i, x, y):
    """how far plate i's face is bent forward at (x, y) (its curled corner)"""
    bent = BENT.get(i)
    if not bent: return 0.0
    r0, r1, a0, a1 = plate_spec(i); r = math.hypot(x, y); a = math.atan2(y, x) % (2 * math.pi)
    if a < a0 - 0.5: a += 2 * math.pi
    u = (a - a0) / (a1 - a0); v = (r - r0) / (r1 - r0)
    d = math.hypot((u - bent[0]) * (a1 - a0) * (r0 + r1) / 2, (v - bent[1]) * (r1 - r0))
    return bent[2] * (1 - d / 0.9) ** 2 if d < 0.9 else 0.0


def bolt_buf(name, bolts, atlas, mat_, seed=1, T_fn=None, shank=True, plate=None):
    """hex bolts on square washers through a plate (and into the lattice behind, so nothing floats)"""
    b = Buf(name); rn = Rnd(seed)
    for k, (x, y, gone) in enumerate(bolts):
        if gone: continue
        z = PT + warp(x, y) * 0.0
        Mx = T(x, y, plate_lift(plate, x, y) if plate is not None else 0.0) @ RZ(math.atan2(y, x) + rn.u(-0.12, 0.12))
        if T_fn: Mx = T_fn(x, y) @ Mx
        tint = rn.u(0.55, 1.0)
        b.add(xf(p_box(0.135, 0.135, 0.016, bottom=False), T(0, 0, PT + 0.004)), mat_, atlas.fit('washer', 1), Mx, tint)
        b.add(xf(p_prism(6, 0.05, 0.04, r1=0.044, dome=0.01), T(0, 0, PT + 0.008)), mat_, atlas.fit('bolt', 1), Mx @ RZ(rn.u(0, 1.0)), tint)
    return b


def poly_contains(poly, x, y):
    c = False; n = len(poly)
    for k in range(n):
        x0, y0 = poly[k]; x1, y1 = poly[(k + 1) % n]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0): c = not c
    return c


def clip_half(poly, px_, py_, nx, ny):
    """keep the part of a convex polygon on the side of the line through (px_, py_) that (nx, ny) points away from"""
    out = []; n = len(poly)
    for k in range(n):
        a = poly[k]; b = poly[(k + 1) % n]
        da = (a[0] - px_) * nx + (a[1] - py_) * ny; db = (b[0] - px_) * nx + (b[1] - py_) * ny
        if da <= 0: out.append(a)
        if (da < 0) != (db < 0) and abs(da - db) > 1e-12:
            t = da / (da - db); out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def shard_cells(i, n_seed, rn, kerf=0.007):
    """voronoi cells over plate i (convex polygons, each shrunk by the kerf): how it breaks"""
    r0, r1, a0, a1 = plate_spec(i)
    hit = plate_pt(i, rn.u(0.3, 0.7), rn.u(0.3, 0.7))
    seeds = [hit] + [plate_pt(i, rn.u(0.03, 0.97), rn.u(0.03, 0.97)) for _ in range(n_seed - 1)]
    seeds = [(lerp(sx, hit[0], 0.25), lerp(sy, hit[1], 0.25)) for sx, sy in seeds[1:]] + [hit]
    cells = []
    for k, (sx, sy) in enumerate(seeds):
        poly = [(-6, -6), (6, -6), (6, 6), (-6, 6)]
        for j, (tx, ty) in enumerate(seeds):
            if j == k: continue
            nx, ny = tx - sx, ty - sy; L = math.hypot(nx, ny)
            if L < 1e-6: continue
            nx, ny = nx / L, ny / L
            poly = clip_half(poly, (sx + tx) / 2 - nx * kerf, (sy + ty) / 2 - ny * kerf, nx, ny)
            if len(poly) < 3: break
        if len(poly) >= 3: cells.append(poly)
    return cells, hit


def smile_poly(shift=0.0, jag=0.035):
    """everything under the smile crack, as an outline (the crack itself zigzags a little: it is a break)"""
    xs = [-4.7 + 9.4 * k / 46 for k in range(47)]
    top = [(x, crack_y(x) + shift + (jag * (1 if k % 2 else -1) * (0.4 + 0.6 * abs(math.sin(k * 1.7)))) * (0 < k < 46)) for k, x in enumerate(xs)]
    return top + [(5.2, -5.4), (-5.2, -5.4)]


def build_plates():
    """-> {name: object}: the 12 plates, their crazed twins, and the smile halves of 02 03 08 11"""
    P = {}
    cutm = bpy.data.materials.new('rp_cut')
    for i in range(12):
        o = plate_mesh(i, M['en'])
        if i < 4:  # the lamp holes go through the inner plates
            sx = 1 if i in (0, 3) else -1
            el = [(sx * EYE_C[0] + EYE_A * math.cos(t), EYE_C[1] + EYE_B * math.sin(t)) for t in (2 * math.pi * k / 28 for k in range(28))]
            boolean(o, prism_cutter(el, m=cutm))
        bolts = bolts_of(i)
        # crazed: broken along a web of cracks into shards, each a hair out of place, a chip or two already gone
        rn = Rnd(300 + i if i else 331)   # (plate 00's first break left a sliver the QA gate did not like)
        cells, hit = shard_cells(i, 5, rn)
        shards = []; bb = Buf('bolts_cz_%02d' % i)
        drop = rn.i(0, len(cells) - 1) if i in (5, 9, 0, 6) else -1
        for k, cell in enumerate(cells):
            sh = o.copy(); sh.data = o.data.copy(); _link(sh)
            boolean(sh, prism_cutter(cell, m=cutm), 'INTERSECT')
            if len(sh.data.polygons) < 4: bpy.data.objects.remove(sh, do_unlink=True); continue
            cxy = (sum(p[0] for p in cell) / len(cell), sum(p[1] for p in cell) / len(cell))
            small = abs(sum(cell[j][0] * cell[(j + 1) % len(cell)][1] - cell[(j + 1) % len(cell)][0] * cell[j][1] for j in range(len(cell)))) / 2
            if k == drop and small < 3.0: bpy.data.objects.remove(sh, do_unlink=True); continue
            Mx = T(cxy[0], cxy[1], rn.u(-0.004, 0.018)) @ RX(rn.u(-0.03, 0.03)) @ RY(rn.u(-0.03, 0.03)) @ RZ(rn.u(-0.0015, 0.0015)) @ T(-cxy[0], -cxy[1], 0)
            sh.data.transform(C_G2B @ Mx @ C_B2G)
            plate_uv(sh, AT['cz'], cutm); sh.data.materials.clear(); sh.data.materials.append(M['cz'])
            shards.append(sh)
            mine = [b for b in bolts if poly_contains(cell, b[0], b[1])]
            sub = bolt_buf('b', mine, AT['cz'], M['cz'], seed=500 + i * 20 + k, plate=i)
            for q in range(len(sub.F)):
                bb.F.append(tuple(len(bb.V) + v for v in sub.F[q])); bb.UV.append(sub.UV[q]); bb.MI.append(bb.mi(M['cz'])); bb.TI.append(sub.TI[q])
            bb.V.extend(Mx @ v for v in sub.V)
        cz = join(shards + ([bb.obj(sharp=40)] if bb.F else []), 'plate_%02d_crazed' % i)
        P[cz.name] = cz
        # the smile halves
        if i in (2, 3, 8, 11):
            for tag, op, sh_ in (('low', 'INTERSECT', -0.006), ('up', 'DIFFERENCE', 0.006)):
                h = o.copy(); h.data = o.data.copy(); _link(h)
                boolean(h, prism_cutter(smile_poly(sh_), m=cutm), op)
                plate_uv(h, AT['cz'], cutm); h.data.materials.clear(); h.data.materials.append(M['cz'])
                side = [b for b in bolts if below_crack(b[0], b[1]) == (tag == 'low') and abs(b[1] - crack_y(b[0])) > 0.1]
                hb = bolt_buf('b', side, AT['cz'], M['cz'], seed=700 + i, plate=i)
                h = join([h] + ([hb.obj(sharp=40)] if hb.F else []), 'plate_%02d_%s' % (i, tag))
                P[h.name] = h
        plate_uv(o, AT['en'], cutm); o.data.materials.clear(); o.data.materials.append(M['en'])
        pb = bolt_buf('b', bolts, AT['en'], M['en'], seed=100 + i, plate=i)
        extra = [pb.obj(sharp=40)]
        if i == 11:  # ☺ CORP's asset tag, riveted on
            tb = Buf('tag'); tx, ty = plate_pt(11, 0.45, 0.42)
            Mt = T(tx, ty, PT + 0.012) @ RZ(-0.06)
            tb.add(p_box(0.78, 0.33, 0.016), M['tr'], AT['tr'].face('tag', 'z', 1), Mt)
            for sx in (-1, 1):
                for sy in (-1, 1): tb.add(xf(p_prism(6, 0.016, 0.014, dome=0.006), T(sx * 0.36, sy * 0.135, 0.006)), M['tr'], TR('bright', 2), Mt, 0.8)
            extra.append(tb.obj(sharp=40))
        o = join([o] + extra, 'plate_%02d' % i)
        P[o.name] = o
    bpy.data.materials.remove(cutm)
    return P


# ------------------------------------------------------------ the mask: lattice, hoop, hub
def beam(b, p0, p1, w, d, key='steel', up=(0, 0, 1), tint=1.0, ends=True):
    """a bar from p0 to p1: w across, d along `up`"""
    p0, p1 = V3(p0), V3(p1); L = (p1 - p0).length
    if L < 1e-4: return
    Mx = frame(p1 - p0, up, (p0 + p1) / 2)
    b.add(p_box(w, d, L, top=ends, bottom=ends), M['tr'], TR(key, 1), Mx, tint)


def frame_bufs():
    """the back lattice in two buffers: what stays up, and what drops with the lower third (under the smile crack)"""
    up, low = Buf('frame'), Buf('frame_low'); rn = Rnd(77)
    def which(p): return low if below_crack(p[0], p[1]) else up
    def member(p0, p1, w, d, key='steel', upv=(0, 0, 1), tint=None):
        """a bar of the lattice. It stops at the lamp housings (they stand in the lattice) and is cut at the smile
        crack, each side keeping its piece"""
        p0, p1 = V3(p0), V3(p1); tint = rn.u(0.7, 1.0) if tint is None else tint
        n_ = 40; pts = [p0.lerp(p1, k / n_) for k in range(n_ + 1)]
        ins = [eye_hit(q.x, q.y, 0.16) and q.z > -0.72 for q in pts]
        if not any(ins): return cracked(p0, p1, w, d, key, upv, tint)
        k = 0
        while k <= n_:
            if ins[k]: k += 1; continue
            j = k
            while j < n_ and not ins[j + 1]: j += 1
            if j > k and (pts[j] - pts[k]).length > 0.45 and (k == 0 or j == n_): cracked(pts[k], pts[j], w, d, key, upv, tint)   # (a piece cut off at both ends would hang in the air)
            k = j + 1
    def cracked(p0, p1, w, d, key, upv, tint):
        s0, s1 = below_crack(p0.x, p0.y), below_crack(p1.x, p1.y)
        if s0 == s1: beam(low if s0 else up, p0, p1, w, d, key, upv, tint); return
        lo_, hi_ = 0.0, 1.0
        for _ in range(24):
            m = (lo_ + hi_) / 2; q = p0.lerp(p1, m)
            if below_crack(q.x, q.y) == s0: lo_ = m
            else: hi_ = m
        g = 0.03 / max(1e-6, (p1 - p0).length)
        beam(low if s0 else up, p0, p0.lerp(p1, max(0.0, lo_ - g)), w, d, key, upv, tint)
        beam(low if s1 else up, p0.lerp(p1, min(1.0, hi_ + g)), p1, w, d, key, upv, tint)
    def pol(r, a, z): return (r * math.cos(a), r * math.sin(a), z)
    ZF, ZW, ZB = -0.014, -0.11, -0.74   # the flange's middle (its face 3 mm behind the plates' backs), the web's middle, the back chord
    # T-section spokes behind every seam, a ring behind the inner seam
    for k in range(8):
        a = k * math.pi / 4
        member(pol(R_IN, a, ZF), pol(HOOP_R - 0.03, a, ZF), 0.2, 0.022, 'steel'); member(pol(R_IN, a, ZW), pol(HOOP_R - 0.03, a, ZW), 0.024, 0.17, 'rustdark')
        if k % 2 == 0:
            member(pol(0.2, a, ZF), pol(R_IN, a, ZF), 0.2, 0.022, 'steel'); member(pol(0.2, a, ZW), pol(R_IN, a, ZW), 0.024, 0.17, 'rustdark')
    for k in range(16):
        a0, a1 = k * math.pi / 8, (k + 1) * math.pi / 8
        member(pol(R_IN, a0, ZF - 0.004), pol(R_IN, a1, ZF - 0.004), 0.2, 0.022, 'steel'); member(pol(R_IN, a0, ZW), pol(R_IN, a1, ZW), 0.024, 0.17, 'rustdark')
    # the back chords: two rings of angle iron, laced to the front with round bar (a space frame 0.75 m deep)
    RB1, RB2 = 3.4, 1.3
    for k in range(16):
        a0, a1 = (k + 0.5) * math.pi / 8, (k + 1.5) * math.pi / 8
        member(pol(RB1, a0, ZB), pol(RB1, a1, ZB), 0.07, 0.07, 'rust')
        am = (k + 1) * math.pi / 8
        for aa in (a0, a1):
            member(pol(R_IN, am, ZW - 0.06), pol(RB1, aa, ZB), 0.036, 0.036, 'rustdark', (0, 1, 0.3))
            member(pol(HOOP_R - 0.06, am, -0.3), pol(RB1, aa, ZB), 0.036, 0.036, 'rustdark', (0, 1, 0.3))
    for k in range(8):
        a0, a1 = (k + 0.5) * math.pi / 4, (k + 1.5) * math.pi / 4
        skip = lambda a: abs(math.cos(a)) < 0.75 and math.sin(a) < -0.2   # the bay in front of the inspector stays open
        if not (skip(a0) and skip(a1)): member(pol(RB2, a0, ZB), pol(RB2, a1, ZB), 0.07, 0.07, 'rust')
        if not skip(a0):
            member(pol(RB2, a0, ZB), pol(RB1, a0 - math.pi / 16, ZB), 0.05, 0.05, 'rustdark')
            member(pol(R_IN, a0 + math.pi / 8, ZW - 0.06), pol(RB2, a0, ZB), 0.036, 0.036, 'rustdark', (0, 1, 0.3))
            member(pol(0.2, a0, -0.16), pol(RB2, a0, ZB), 0.036, 0.036, 'rustdark', (0, 1, 0.3))
    # gussets where spokes meet the ring and the hoop, two bolt heads each
    for k in range(8):
        a = k * math.pi / 4
        for rr_, sz in ((R_IN, 0.46), (HOOP_R - 0.22, 0.4)):
            p = pol(rr_, a, ZF - 0.02); bb = which(p)
            Mx = T(*p) @ RZ(a)
            bb.add(p_box(sz, sz, 0.016), M['tr'], TR('rust', 1), Mx, rn.u(0.6, 0.95))
    # the hoop: a riveted steel band round the whole sign, like the skin of a tunnelling shield. 16 lengths, butt straps
    prof = [(RM - 0.012, PT + 0.03), (HOOP_R, PT + 0.03), (HOOP_R, -0.56), (HOOP_R - 0.026, -0.56), (HOOP_R - 0.026, PT - 0.02), (RM - 0.012, PT - 0.02)]
    keys = ['cast', 'bright', 'rustdark', 'rustdark', 'cast', 'cast']
    NSEG = 16; SUB = 3
    for sgi in range(NSEG):
        bb = low if (sgi >= NSEG // 2) else up
        a_lo, a_hi = sgi * 2 * math.pi / NSEG, (sgi + 1) * 2 * math.pi / NSEG
        tint = rn.u(0.75, 1.0)
        for e in range(len(prof)):
            (ra, za), (rb, zb) = prof[e], prof[(e + 1) % len(prof)]
            rows = [[pol(ra, lerp(a_lo, a_hi, s / SUB), za) for s in range(SUB + 1)], [pol(rb, lerp(a_lo, a_hi, s / SUB), zb) for s in range(SUB + 1)]]
            V_, F_, UV_ = p_grid(rows)
            if keys[e] == 'bright': UV_ = [[(v, u) for u, v in f] for f in UV_]  # the scrapes run along the tunnel
            bb.add((V_, F_, UV_), M['tr'], TRF(keys[e], 1), None, tint * (0.8 if keys[e] == 'bright' else 1.0))
        if sgi in (0, NSEG // 2):  # the cut ends of each half (they face each other, a hair apart)
            for bb2, sgn in ((up, 1), (low, -1)):
                a_c = a_lo + sgn * 0.0006 * (1 if sgi == 0 else -1)
                V_ = [V3(pol(r_, a_c, z_)) for r_, z_ in prof]; cen_ = sum(V_, V3()) / len(V_)
                away = cen_ + V3((-math.sin(a_c), math.cos(a_c), 0)) * (sgn * (1 if sgi == 0 else -1))
                bb2.add(orient_from((V_, [(0, 1, 4, 5), (1, 2, 3, 4)], [[(0, 0), (1, 0), (1, 1), (0, 1)]] * 2), away), M['tr'], TR('rustdark', 2), None, 0.8)
        # the butt strap over each joint, four rivets
        Ms = T(*pol(HOOP_R + 0.006, a_lo, -0.2)) @ RZ(a_lo)
        bs = low if below_crack(*pol(HOOP_R, a_lo + 1e-3, 0)[:2]) else up
        bs.add(p_box(0.024, 0.34, 0.5), M['tr'], TR('rust', 1), Ms, rn.u(0.7, 1.0))
        for dy in (-0.11, 0.11):
            for dz in (-0.16, 0.16): bs.add(xf(p_prism(5, 0.03, 0.02, r1=0.018, dome=0.008), T(0.012, dy, dz) @ RY(math.pi / 2)), M['tr'], TR('cast', 2), Ms, 0.9)
    # rivets along the hoop's front lip (one every 7.5 degrees), a tie rod from the hoop to the web at each spoke
    for k in range(48):
        a = (k + 0.5) * 2 * math.pi / 48; p = pol((RM - 0.012 + HOOP_R) / 2, a, PT + 0.03)
        which(p).add(xf(p_prism(5, 0.022, 0.012, r1=0.012, dome=0.006), T(*p)), M['tr'], TR('cast', 2), None, 0.9)
    # the hub: a cap over the middle where the four inner plates meet, a big nut, a ring of bolts; a tube back to the chords
    hub = [(0.0, PT + 0.085), (0.1, PT + 0.085), (0.26, PT + 0.06), (0.335, PT + 0.02), (0.335, PT - 0.03), (0.3, PT - 0.03), (0.3, -0.2), (0.0, -0.2)]
    k_ = 12
    rings_ = [[V3((r_ * math.cos(2 * math.pi * j / k_), r_ * math.sin(2 * math.pi * j / k_), z_)) for j in range(k_)] for r_, z_ in hub[1:-1]]
    up.add(p_loft(rings_[::-1], tip0=V3((0, 0, -0.2)), tip1=V3((0, 0, PT + 0.085))), M['tr'], TR('cast', 1), None, 0.95)
    up.add(xf(p_prism(6, 0.085, 0.07, r1=0.075, dome=0.012), T(0, 0, PT + 0.08)), M['tr'], TR('rust', 1), RZ(0.3), 0.9)
    for j in range(8):
        a = (j + 0.5) * math.pi / 4
        up.add(xf(p_prism(6, 0.026, 0.03, dome=0.006), T(0.2 * math.cos(a), 0.2 * math.sin(a), PT + 0.062)), M['tr'], TR('rust', 2), None, 0.8)
    up.add(xf(p_prism(8, 0.11, 0.56, top=False), T(0, 0, -0.75)), M['tr'], TR('rustdark', 1), None, 0.8)
    return up, low


# ------------------------------------------------------------ the mask: the lamp housings (the eyes)
def oval(a, b, t): return V3((a * math.cos(t), b * math.sin(t), 0))
def oval_n(a, b, t): n = V3((b * math.cos(t), a * math.sin(t), 0)); return n.normalized()


def oval_loft(a, b, prof, k=24, closed=True):
    """a section (offset out from the oval, z) swept round an a x b oval"""
    rings_ = []
    for off, z in prof:
        rings_.append([oval(a, b, 2 * math.pi * j / k) + oval_n(a, b, 2 * math.pi * j / k) * off + V3((0, 0, z)) for j in range(k)])
    return rings_


def eye_buf(name, sx, blown=False):
    """a bulkhead lamp housing: a cast bezel bolted over the hole, the can behind it (tapering, so it can swing out on
    its hinge), what is left of the lens round the lip, the dead lamp holder at the back. Built round the eye's centre."""
    b = Buf(name); rn = Rnd(40 + (sx > 0) + 2 * blown); tr = M['tr']
    a, bb = EYE_A, EYE_B; K = 24
    # the bezel: flange on the enamel, a raised rim, a lip down into the hole
    prof = [(0.17, PT - 0.004), (0.17, PT + 0.03), (0.07, PT + 0.034), (0.045, PT + 0.085), (-0.02, PT + 0.085), (-0.05, PT + 0.04), (-0.05, -0.04)]
    rings_ = oval_loft(a, bb, prof, K)
    if blown:  # the bezel is sprung: twisted and bulged where it let go
        for ring_ in rings_:
            for j, p in enumerate(ring_):
                t = 2 * math.pi * j / K
                p.z += 0.07 * max(0.0, math.sin(t * 1.5 + 0.6)) + 0.03 * math.sin(t * 4)
                p.x += 0.025 * math.sin(t * 3 + 1)
    V_, F_, UV_ = p_loft(rings_)
    b.add((V_, F_, [[(u * 0.5, v) for u, v in f] for f in UV_]), tr, TR('cast', 1), None, 0.9)
    for j in range(12):  # studs round the flange
        if blown and j in (2, 3, 4, 9): continue
        t = (j + 0.5) * 2 * math.pi / 12; p = oval(a, bb, t) + oval_n(a, bb, t) * 0.12
        lift = (0.07 * max(0.0, math.sin(t * 1.5 + 0.6)) + 0.03 * math.sin(t * 4) - 0.012) if blown else 0.0
        b.add(xf(p_prism(6, 0.032, 0.035, r1=0.028, dome=0.008), T(p.x, p.y, PT + 0.022 + lift)), tr, TR('rust', 2), None, rn.u(0.6, 1.0))
        if not blown: b.add(xf(p_prism(5, 0.014, 0.16, top=False), T(p.x, p.y, -0.07)), tr, TR('rustdark', 2), None, 0.6)
    # hinge knuckles on the outer side, a latch on the inner side
    for dy in (-0.55, 0.55):
        b.add(p_box(0.1, 0.2, 0.084), tr, TR('cast', 1), T(sx * (a + 0.2), dy, PT + 0.05), 0.85)
        b.add(xf(p_prism(6, 0.03, 0.26, bottom=True), RX(-math.pi / 2) @ T(0, 0, -0.13)), tr, TR('bright', 1), T(sx * (a + 0.255), dy, PT + 0.07), 0.7)
    b.add(p_box(0.16, 0.09, 0.062), tr, TR('rust', 1), T(-sx * (a + 0.15), 0.0, PT + 0.05), 0.85)
    b.add(p_box(0.05, 0.2, 0.035), tr, TR('bright', 1), T(-sx * (a + 0.2), 0.02, PT + 0.065) @ RZ(0.25), 0.7)
    DEPTH = 0.62; a2, b2 = 0.38, 0.86
    if not blown:
        # the can: looked into from the front (soot black), seen from outside when plates are gone (rusty steel)
        ins = [[oval(lerp(a - 0.05, a2, s), lerp(bb - 0.05, b2, s), 2 * math.pi * j / K) + V3((0, 0, lerp(-0.04, -DEPTH, s))) for j in range(K)] for s in (0.0, 0.5, 1.0)]
        b.add(p_loft(ins, tip1=V3((0, 0, -DEPTH + 0.02))), M['void'], ('tile', 0.5), None, 1.0)   # (wound to face the axis: you look into it)
        outs = [[oval(lerp(a - 0.02, a2 + 0.03, s), lerp(bb - 0.02, b2 + 0.03, s), 2 * math.pi * j / K) + V3((0, 0, lerp(-0.035, -DEPTH - 0.03, s))) for j in range(K)] for s in (0.0, 0.5, 1.0)]
        b.add(p_loft(outs, tip1=V3((0, 0, -DEPTH - 0.05))), tr, TR('rust', 1), None, 0.8, flip=True)
        for k in range(3):  # strengthening bands round the can
            z = -0.14 - k * 0.2; s = (-z - 0.04) / (DEPTH - 0.04)
            rr_ = [[oval(lerp(a - 0.02, a2 + 0.03, s) + e, lerp(bb - 0.02, b2 + 0.03, s) + e, 2 * math.pi * j / 16) + V3((0, 0, z + dz)) for j in range(16)] for e, dz in ((0.0, 0.03), (0.022, 0.03), (0.022, -0.03), (0.0, -0.03))]
            b.add(p_loft(rr_[::-1]), tr, TR('rustdark', 1), None, 0.85, flip=True)
        # the lamp holder: a cross bar, two sockets, one bulb's broken stump
        b.add(p_box(0.05, 1.5, 0.04), tr, TR('rustdark', 1), T(0, 0, -DEPTH + 0.1), 0.4)
        for dy in (-0.38, 0.38):
            b.add(xf(p_prism(8, 0.085, 0.12, r1=0.07), T(0, dy, -DEPTH + 0.1)), tr, TR('brass', 1), None, 0.22)
        b.add(xf(p_prism(5, 0.05, 0.1, r1=0.02, dome=0.03), T(0, 0.38, -DEPTH + 0.22)), tr, TR('glass', 1), None, 0.7)
        # the lens: only teeth of glass left round the lip
        for j in range(11):
            t = (3.5 + j * 0.24 + rn.u(-0.05, 0.05)) if j < 9 else (0.9, 2.3)[j - 9]; p = oval(a - 0.05, bb - 0.05, t); n = oval_n(a, bb, t)
            ln = rn.u(0.05, 0.17); w = rn.u(0.03, 0.07); dz = j * 0.0017
            tg = V3((-n.y, n.x, 0))
            base = [p + tg * w + V3((0, 0, PT + 0.03 + dz)), p - tg * w + V3((0, 0, PT + 0.03 + dz)), p + V3((0, 0, PT + 0.008 + dz))]
            tip = p - n * ln + tg * rn.u(-0.05, 0.05) + V3((0, 0, PT + 0.022 + dz))
            b.add(orient_from((base + [tip], [(0, 1, 3), (1, 2, 3), (2, 0, 3), (1, 0, 2)], [[(0, 0), (1, 0), (0.5, 1)]] * 4), sum(base + [tip], V3()) / 4), tr, TRF('glass', 2), None, rn.u(0.45, 0.9))
    else:
        # burst from behind: the can's wall split into petals, peeled out through the bezel toward you
        NP = 7
        for k in range(NP):
            t0 = 2 * math.pi * (k + rn.u(-0.08, 0.08)) / NP; t1 = 2 * math.pi * (k + 1 + rn.u(-0.08, 0.08)) / NP - 0.1
            curl = rn.u(0.5, 1.25); ln = rn.u(0.35, 0.62); rows = []
            for s in (0.0, 0.3, 0.62, 1.0):
                row = []
                for q in range(4):
                    t = lerp(t0, t1, q / 3); n = oval_n(a, bb, t)
                    ang = curl * s * 1.9; rad_out = (1 - math.cos(ang)) / max(0.3, curl * 1.9) * ln; zf = math.sin(ang) / max(0.3, curl * 1.9) * ln
                    edge = 1 - 0.92 * s ** 1.4
                    p = oval(a - 0.055, bb - 0.055, lerp((t0 + t1) / 2, t, edge)) + n * rad_out + V3((0, 0, -0.03 + zf * 1.0 + PT * 0.5 * s))
                    row.append(p)
                rows.append(row)
            b.add(p_grid(rows), tr, TR('rust', 1), None, rn.u(0.6, 0.9))
            b.add(p_grid([[p + V3((0, 0, -0.012)) + oval_n(a, bb, 0) * 0 for p in row] for row in rows], flip=True), tr, TR('soot', 1), None, 0.8)
    return b


EYE_ITEMS = []
def eye_cluster_bufs():
    """the real eyes behind the left housing: thirteen of them packed in a socket of regrown tissue, every one on you.
    -> (the socket buffer, [(eyeball buffer, centre)])"""
    rn = Rnd(1732); sock = Buf('eye_cluster'); balls = []
    cx, cy = EYE_C
    spots = []
    tries = 0
    while len(spots) < 13 and tries < 4000:
        tries += 1
        r_ = rn.u(0.11, 0.2) if len(spots) > 2 else rn.u(0.2, 0.26)
        x = rn.u(-EYE_A + 0.1, EYE_A - 0.1); y = rn.u(-EYE_B + 0.12, EYE_B - 0.12)
        if (x / (EYE_A - r_ * 0.8)) ** 2 + (y / (EYE_B - r_ * 0.8)) ** 2 > 1: continue
        if any(math.hypot(x - sx_, y - sy_) < (r_ + sr_) * 0.93 for sx_, sy_, sr_ in spots): continue
        spots.append((x, y, r_))
    # the tissue they sit in: a lumpy dark-red pad filling the hole, a lid of char round each
    K = 20
    rings_ = [[oval(EYE_A * s, EYE_B * s, 2 * math.pi * j / K) + V3((0, 0, z + 0.03 * fbm(j * 0.9, s * 4, 2.0))) for j in range(K)] for s, z in ((1.02, -0.32), (0.9, -0.2), (0.55, -0.14), (0.2, -0.12))]
    sock.add(p_loft(rings_, tip1=V3((0, 0, -0.12))), M['bits'], AT['bits'].fit('flesh', 1), T(cx, cy, 0), 0.75)
    for k, (x, y, r_) in enumerate(spots):
        z = -0.14 + r_ * 0.45
        lid = [[V3((math.cos(2 * math.pi * j / 8) * r_ * s, math.sin(2 * math.pi * j / 8) * r_ * s * (0.86 if s < 1.1 else 1.0), zz)) for j in range(8)] for s, zz in ((1.25, -0.06), (1.12, r_ * 0.35), (0.9, r_ * 0.62))]
        sock.add(p_loft(lid), M['char'], ('tile', 0.4), T(cx + x, cy + y, z), 0.5)
        eb = Buf('eyeball_%02d' % k)
        V_, F_, UV_ = p_ellipsoid(r_, r_, r_, 8, 5)
        V_ = [RX(math.pi / 2) @ v for v in V_]  # the pole (the pupil) looks along +z
        eb.add((V_, F_, UV_), M['eye'], ('fn', lambda p, r_=r_: (0.5 + p.x / (2.05 * r_), 0.5 + p.y / (2.05 * r_)) if p.z > -r_ * 0.2 else (0.06 + 0.02 * p.x / r_, 0.06 + 0.02 * p.y / r_)), None, rn.pick([(1, 1, 1), (1, 0.92, 0.85), (0.92, 0.95, 1), (1, 0.85, 0.8)]))
        balls.append((eb, (cx + x, cy + y, z)))
    return sock, balls


# ------------------------------------------------------------ the 17:32: textures
BITS = 128
def paint_char(name):
    """charred skin, the way burnt timber cracks into blocks (alligatoring): ash-grey plates, black cracks, and in some
    of the cracks the dark red of what grew back. Tiles. Light on purpose: the vertex colours darken it per body."""
    S = 64; r = np.random.default_rng(31)
    pts = r.random((46, 2)) * S; shade = 0.72 + 0.5 * r.random(46); red = r.random(46) < 0.34
    yy, xx = np.mgrid[0:S, 0:S]
    d1 = np.full((S, S), 1e9); d2 = np.full((S, S), 1e9); i1 = np.zeros((S, S), int)
    for k, (cx, cy) in enumerate(pts):
        dx = np.abs(xx + 0.5 - cx); dx = np.minimum(dx, S - dx); dy = np.abs(yy + 0.5 - cy); dy = np.minimum(dy, S - dy)
        d = np.hypot(dx, dy); sw = d < d1
        d2 = np.where(sw, d1, np.minimum(d2, d)); i1 = np.where(sw, k, i1); d1 = np.where(sw, d, d1)
    edge = d2 - d1
    px = hexrgb(0x5c5654)[None, None] * shade[i1][:, :, None] * (0.93 + 0.14 * r.random((S, S, 1)))
    hl = (edge > 1.2) & (edge < 2.6) & (np.roll(i1, 1, 0) != i1) | ((edge > 1.0) & (edge < 2.2) & (r.random((S, S)) < 0.25))
    px[hl] = px[hl] * 1.25 + 0.03
    crack = edge < 1.15
    px[crack] = hexrgb(0x120e10)
    px[crack & red[i1]] = hexrgb(0x5a1216)
    px[crack & red[i1] & (r.random((S, S)) < 0.3)] = hexrgb(0x8a1c1c)
    return _image(name, np.clip(px, 0, 1).astype(np.float32))


def paint_pack(name):
    """the plug's wall and back, where the bore has pressed everyone flat: a tiling picture of packed commuters seen
    from outside (heads, shoulders, a lanyard here and there) on char. Cheaper than modelling 300 more."""
    S = 128; r = np.random.default_rng(41); px = np.zeros((S, S, 3), np.float32)
    px[:] = hexrgb(0x17130f) * (0.8 + 0.4 * blocky(r, S, 4)[:, :, None])
    def put(x, y, c):
        px[int(y) % S, int(x) % S] = hexrgb(c) if isinstance(c, int) else c
    for k in range(34):
        cx, cy = r.uniform(0, S), r.uniform(0, S); a = r.uniform(0, 6.28); ca, sa = math.cos(a), math.sin(a); sh = r.uniform(0.75, 1.15)
        body = hexrgb([0x2e2928, 0x262224, 0x34302c, 0x1e1c22][k % 4]) * sh; skin = hexrgb([0x6e625a, 0x5c5450, 0x786a5e][k % 3]) * sh
        def at(u, v): return cx + u * ca - v * sa, cy + u * sa + v * ca      # u across the shoulders, v up to the head
        for u in np.arange(-7, 7.5, 0.5):
            for v in np.arange(-9, 1.5, 0.5):
                if abs(u) <= 7 - max(0.0, v) * 2.5 - max(0.0, -v - 4) * 0.5: put(*at(u, v), body * (0.8 + 0.2 * (v > -1)))
        for u in np.arange(-3, 3.5, 0.5):
            for v in np.arange(1.5, 8.5, 0.5):
                if (u / 3.2) ** 2 + ((v - 5) / 3.6) ** 2 <= 1: put(*at(u, v), skin)
        if k % 3 != 2:  # the face is toward you: sockets, a mouth
            for u, v in ((-1.3, 5.6), (1.3, 5.6), (0, 3.2)): put(*at(u, v), 0x080506); put(*at(u + 0.5, v), 0x080506)
        if k % 2 == 0:  # a lanyard and its card
            lc = [0x2aa8d8, 0xe8b820, 0xc8c8c0][k % 3]
            for t in np.arange(0, 1.01, 0.1): put(*at(-2.5 + 2.5 * t, 0.5 - 5 * t), lc); put(*at(2.5 - 2.5 * t, 0.5 - 5 * t), lc)
            for u in (-1, 0, 1):
                for v in (-5.5, -6.5, -7.5): put(*at(u, v), 0xd8d4c8)
    cr = blocky(r, S, 1) > 0.965; px[cr] = hexrgb(0x4a1012)
    return _image(name, np.clip(px, 0, 1))


FACES = 6
def bits_atlas():
    """the small things that make it people: faces, shirt fronts, lanyards, ID cards, leather, shoes, cut flesh, and
    the inspector's uniform"""
    A = Atlas('rp_bits', BITS, BITS, rough=0.6); r = np.random.default_rng(5)
    for f in range(FACES):  # 16 x 20 faces: ashen, the sockets and the mouth burnt black
        c = A.cell('face%d' % f, f * 16, 0, 16, 20, [0x74675f, 0x6a5e5a, 0x7c6e62, 0x625858, 0x70625a, 0x685c56][f], var=0.1, seed=60 + f)
        c[r.random((20, 16)) < 0.16] *= 0.55
        c[0:2, :] *= 0.5; c[:, 0:1] *= 0.55; c[:, 15:] *= 0.55
        for ex in (3, 10): c[6:9, ex:ex + 3] = hexrgb(0x0a0606); c[5, ex:ex + 3] = hexrgb(0x2a2020)
        if f in (0, 3): c[7, 4] = c[7, 11] = hexrgb(0xb0a898)                          # a milky eye still in there
        if f == 4: c[6:9, 3:6] = c[6:9, 10:13] = hexrgb(0x3a2e2c); c[7, 3:6] = c[7, 10:13] = hexrgb(0x0a0606)   # shut
        c[10:12, 7:9] = hexrgb(0x2a1e1e)                                                # what's left of the nose
        if f in (0, 2, 5): c[13:18, 5:11] = hexrgb(0x060404); c[13, 6:10] = hexrgb(0xb8b0a0); c[17, 6:10] = hexrgb(0x8a8474) if f != 2 else hexrgb(0x060404)   # screaming
        elif f == 1: c[14:16, 4:12] = hexrgb(0xb8b0a0); c[14:16, 4:12:2] = hexrgb(0x3a3030); c[13, 4:12] = c[16, 4:12] = hexrgb(0x120c0c)   # no lips: teeth
        elif f == 3: c[14:16, 6:10] = hexrgb(0x060404)
        else: c[15, 5:11] = hexrgb(0x120c0c)
    for k, (hd, bg) in enumerate(((0x4fd8ff, 0xf4f4f0), (0xffe14d, 0xf4f4f0), (0xf4f4f0, 0xf4f4f0), (0x4fd8ff, 0xe8f6fb))):  # ID cards, 12 x 16
        c = A.cell('card%d' % k, k * 12, 20, 12, 16, bg, rough=0.35)
        c[0:4, :] = hexrgb(hd); c[1:3, 5:7] = hexrgb(0x2a2a2a)                           # the punched slot
        c[5:10, 1:6] = hexrgb(0x8a7a70); c[5:7, 1:6] = hexrgb(0x3a3030)                  # the photo
        px_disc(c, 8.5, 7.5, 2.4, 0xffe14d); c[7, 8] = c[7, 9] = hexrgb(0x111111)        # ☺
        c[11, 1:11] = c[13, 1:8] = hexrgb(0x6a6a6a)
        c[13:, :][r.random((3, 12)) < 0.3] *= 0.4; c[:, 10:][r.random((16, 2)) < 0.3] *= 0.4   # singed at a corner
    st = A.cell('strap', 48, 20, 8, 16, 0xf0f0f0, rough=0.7); st[::2, :] *= 0.86; st[:, 0] *= 0.7; st[:, -1] *= 0.7
    sh = A.cell('shirt0', 56, 20, 16, 20, 0xd8d4c8, rough=0.7, var=0.06, seed=71)       # shirt and tie
    sh[0:3, 5:11] = hexrgb(0xf0ece0); sh[2:18, 7:9] = hexrgb(0xb02028); sh[2:5, 6:10] = hexrgb(0x8a1820); sh[r.random((20, 16)) < 0.2] *= 0.3
    for y in (7, 12): sh[y, 4] = hexrgb(0x8a8a80)
    sh = A.cell('shirt1', 72, 20, 16, 20, 0x9ab0c8, rough=0.7, var=0.06, seed=72)       # blue blouse, a hi-vis strap of a rucksack
    sh[:, 2:4] = hexrgb(0xffe14d); sh[::3, :] *= 0.9; sh[r.random((20, 16)) < 0.22] *= 0.3
    sh = A.cell('shirt2', 88, 20, 16, 20, 0x3a3e4a, rough=0.75, var=0.08, seed=73)      # suit: lapels, a pocket square
    sh[:, 7:9] = hexrgb(0xd8d4c8); sh[4:7, 11:14] = hexrgb(0xff4fd8); sh[:, 0:16:4] *= 1.2; sh[r.random((20, 16)) < 0.18] *= 0.35
    le = A.cell('leather', 0, 40, 24, 16, 0x7a4a26, rough=0.5, var=0.12, seed=74, speck=0x3a2010, speck_p=0.12)
    le[1, :] = le[-2, :] = hexrgb(0xb08a50); le[:, 1] = le[:, -2] = hexrgb(0xb08a50)   # stitching
    A.cell('leatherb', 24, 40, 16, 16, 0x1e1a1c, rough=0.4, var=0.12, seed=75, speck=0x4a4444, speck_p=0.08)
    A.cell('brass', 40, 40, 8, 8, 0xd0a040, rough=0.3, var=0.1, seed=76)
    A.cell('shoe', 48, 40, 8, 8, 0x1a1616, rough=0.3, var=0.15, seed=77)
    A.cell('shoer', 56, 40, 8, 8, 0xb01828, rough=0.25, var=0.08, seed=78)
    um = A.cell('brolly', 64, 40, 16, 16, 0x18161c, rough=0.5, var=0.1, seed=79); um[:, 3::8] = hexrgb(0x3a3642)
    A.cell('wood', 80, 40, 8, 8, 0x8a5a2b, rough=0.4, var=0.15, seed=80)
    A.cell('rib', 88, 40, 8, 8, 0x9a9aa0, rough=0.35, metal=0.0, var=0.1, seed=81)
    fl = A.cell('flesh', 0, 56, 32, 32, 0x6a1218, rough=0.3, var=0.18, seed=82, speck=0x2a0608, speck_p=0.2)   # cut through: meat, fat, bone ends
    for k in range(9):
        cx, cy = r.uniform(3, 29), r.uniform(3, 29)
        px_disc(fl, cx, cy, r.uniform(1.6, 2.6), 0xd8c8a8); px_disc(fl, cx, cy, 0.9, 0x5a1014)
    fl[r.random((32, 32)) < 0.05] = hexrgb(0xc8a070)
    te = A.cell('teeth', 32, 56, 16, 8, 0xb8b0a0, rough=0.4); te[:, ::3] = hexrgb(0x3a3030); te[0] = te[-1] = hexrgb(0x120c0c)
    A.cell('mouth', 48, 56, 8, 8, 0x0a0606, rough=0.6, var=0.2, seed=83, speck=0x4a1014, speck_p=0.2)
    A.cell('ash', 56, 56, 8, 8, 0x8a8480, rough=0.9, var=0.15, seed=84)
    # the inspector's: navy serge with brass buttons, the cap band with its lettering, the badge, tickets
    nv = A.cell('serge', 0, 88, 24, 32, 0x18203c, rough=0.75, var=0.1, seed=85); nv[r.random((32, 24)) < 0.22] *= 0.35
    for y in (4, 12, 20, 28): px_disc(nv, 12, y, 1.8, 0xd0a040); nv[y, 12] = hexrgb(0x6a4a1a)
    nv[:, 9] *= 0.6; nv[:, 15] *= 0.6
    bd = A.cell('band', 24, 88, 56, 8, 0x0c1022, rough=0.5); bd[0] = bd[-1] = hexrgb(0xd0a040)
    text_px(bd, 'REVENUE', 7, 1, 1, 0xd0a040) if False else None
    for i, ch in enumerate('REVENUE'):
        g = FONT[ch]
        for ry in range(1, 7):
            for rx in range(5):
                if g[ry][rx] == '1': bd[ry, 8 + i * 6 + rx] = hexrgb(0xd0a040)
    bg = A.cell('badge', 80, 88, 12, 12, 0xd0a040, rough=0.3); px_disc(bg, 6, 6, 4.2, 0xffe14d); px_disc(bg, 6, 6, 4.2, 0x141414, r_in=3.4); bg[4, 4] = bg[4, 7] = hexrgb(0x141414); bg[7, 4:8] = hexrgb(0x141414)
    tk = A.cell('ticket', 96, 88, 12, 16, 0xe8d8a0, rough=0.7); tk[2, 1:11] = tk[13, 1:11] = hexrgb(0xb04030); tk[5:8, 2:6] = hexrgb(0x3a3030); px_disc(tk, 8.5, 10.5, 1.3, 0x1a1414)
    A.cell('capnavy', 108, 88, 16, 16, 0x141a34, rough=0.7, var=0.1, seed=86, speck=0x06080e, speck_p=0.2)
    A.cell('white', 24, 96, 8, 8, 0xe8e4d8, rough=0.6, var=0.05, seed=87)
    return A


def eye_tex():
    S = 32
    def draw(px):
        px[:] = hexrgb(0xe8dcc8); r = np.random.default_rng(9)
        for k in range(7):
            a = r.uniform(0, 6.28); px_line(px, 16 + 15 * math.cos(a), 16 + 15 * math.sin(a), 16 + 8 * math.cos(a + 0.3), 16 + 8 * math.sin(a + 0.3), 0xb03838, 1.0)
        px_disc(px, 16, 16, 9.5, 0x3a2a20); px_disc(px, 16, 16, 8.5, 0x7a8a5a); px_disc(px, 16, 16, 6.0, 0xa8b070); px_disc(px, 16, 16, 4.2, 0x050404)
        px_disc(px, 13, 13, 1.4, 0xffffff)
        px[0:6, 0:6] = hexrgb(0x9a2a2a)   # the back of the ball
    base = tex_canvas('rp_eye_t', S, S, draw)
    return mat('rp_eye_glow', 0xffffff, rough=0.12, emit=0xffffff, strength=0.55, tex=base, emit_tex=True)


def mass_materials():
    AT['bits'] = bits_atlas(); M['bits'] = AT['bits'].material('rp_bits', rough=0.6)
    M['char'] = mat('rp_char', 0xffffff, rough=0.6, tex=paint_char('rp_char_t'))
    M['pack'] = mat('rp_pack', 0xffffff, rough=0.65, tex=paint_pack('rp_pack_t'))
    M['eye'] = eye_tex()


def BT(k, m=0.5): return AT['bits'].quad(k, m)
def BF(k, m=0.5): return AT['bits'].fit(k, m)
CHAR = ('tile', 0.42)
LAN = [(0.16, 0.72, 1.0), (1.0, 0.76, 0.1), (0.85, 0.85, 0.82), (0.16, 0.72, 1.0), (1.0, 0.76, 0.1)]   # cyan, yellow, white (linear)


# ------------------------------------------------------------ the 17:32: one commuter
KNOTS = []   # (x, y) of every knot of people: the plug's face swells under each
def core_z(x, y):
    """the front face of the plug (before bodies stand out of it)"""
    z = MASS_Z0 - 0.5 + 0.26 * fbm(x * 0.42, y * 0.42, 1.7, 3) + 0.08 * fbm(x * 1.3, y * 1.3, 5.1, 2)
    for kx, ky in KNOTS:
        d2 = (x - kx) ** 2 + (y - ky) ** 2
        if d2 < 3.2: z += 0.2 * math.exp(-d2 / 0.9)
    if abs(x) < 1.0 and -3.4 < y < -1.2: z -= 0.3 * (1 - abs(x)) * min(1.0, (y + 3.4) * 2, (-1.2 - y) * 2)   # the inspector's bay
    e = ((abs(x) - EYE_C[0]) / (EYE_A + 0.35)) ** 2 + ((y - EYE_C[1]) / (EYE_B + 0.35)) ** 2
    if e < 1.0: z = min(z, -1.02) - 0.12 * (1 - e)   # the lamp cans stand in it here
    return min(z, -0.74)


class Fig:
    """adds one fused commuter to a buffer. Mw = the figure's space in the root's (see rpkit: origin between the
    shoulders, +y to the head, +z out of the chest); everything it grows (arms to a world point, a lanyard) follows."""
    def __init__(s, b, Mw, rn, scale=1.0, body=None, hero=False, lean=None):
        s.b = b; s.M = Mw @ SC(scale); s.rn = rn; s.k = scale; s.hero = hero
        s.body = body if body is not None else rn.u(0.2, 0.42)
        s.R = s.M.to_3x3().normalized()

    def w(s, p): return s.M @ V3(p)
    def d(s, v): return (s.R @ V3(v)).normalized()

    def torso(s, wide=1.0, deep=1.0, length=0.5, k=8, shirt=None, neck=True):
        s.wide, s.deep = wide, deep
        s.b.add(torso_prim(k, wide, deep, length, neck), M['char'], CHAR, s.M, s.body, jit=0.016)
        if shirt is not None: s.b.add(chest_patch(wide, deep, off=0.007 + 0.006 * s.rn.u(0, 1)), M['bits'], AT['bits'].face('shirt%d' % shirt, 'z', 1), s.M, s.rn.u(0.55, 0.9))
        return s

    def head(s, yaw=0.0, pitch=0.0, roll=0.0, jaw=None, face=None, at=(0, 0.178, 0.012), size=1.12, bare=False):
        rn = s.rn
        face = rn.i(0, FACES - 1) if face is None else face
        jaw = (rn.u(0.5, 1.0) if face in (0, 2, 5) else rn.u(0.0, 0.25)) if jaw is None else jaw
        Mh = s.M @ T(at[0], at[1] - 0.115, at[2]) @ RY(yaw) @ RX(pitch) @ RZ(roll) @ T(0, 0.115, 0) @ SC(size * rn.u(0.94, 1.06), size * rn.u(0.94, 1.12), size)   # (it turns on the top of the neck, so it stays on it)
        fp, sk = head_prims(8 if s.hero else 6, jaw)
        s.b.add(fp, M['bits'], AT['bits'].face('face%d' % face, 'z', 0.5), Mh, rn.u(0.72, 1.0), jit=0.006)
        s.b.add(sk, M['char'], ('tile', 0.3), Mh, min(1.0, s.body * rn.u(1.0, 1.5)), jit=0.006)
        s.Mh = Mh
        return s

    def arm(s, side, target, hand='flat', fingers=None, palm=None, pole=None, k=5, hs=1.3, tint=None, l1=0.31, l2=0.27, r=1.0):
        """an arm from this side's shoulder to a point in the ROOT's space. fingers = where they point (root), palm =
        what the palm faces (root). Out of reach = it stretches as far as it goes."""
        rn = s.rn; K = s.k
        p0 = s.w((side * 0.2 * getattr(s, 'wide', 1.0), -0.03, 0.0))
        pole = V3(pole) if pole is not None else s.d((side * 0.7, -0.7, -0.25))
        p1, p2 = ik2(p0, target, l1 * K, l2 * K, pole)
        tint = tint if tint is not None else min(1.0, s.body * rn.u(1.0, 1.35))
        s.b.add(limb_prim(p0, p1, p2, 0.058 * K * r, 0.047 * K * r, 0.034 * K * r, k, fine=s.hero), M['char'], CHAR, None, tint, jit=0.008)
        fwd = (p2 - p1).normalized()
        f = V3(fingers).normalized() if fingers is not None else fwd
        pn = V3(palm) if palm is not None else s.d((0, 0, 1))
        Mh = frame(f, -pn, p2 - f * 0.012) @ SC(hs * K)
        prim = {'flat': lambda: hand_flat(rn.u(0.6, 1.5), side), 'grip': lambda: hand_grip(rn.u(0.8, 1.1), side), 'mitt': lambda: hand_mitt(side, rn.u(0.1, 0.7)),
                'claw': lambda: hand_claw(side, rn.u(0.35, 0.8))}[hand]()
        s.b.add(prim, M['char'], ('tile', 0.3), Mh, min(1.0, tint * rn.u(1.5, 2.2)))
        return p2

    def stub(s, side, direction, length=0.22):
        """an upper arm that goes back into the mass"""
        p0 = s.w((side * 0.2 * getattr(s, 'wide', 1.0), -0.03, 0.0)); dv = V3(direction).normalized()
        s.b.add(p_tube([p0, p0 + dv * length * s.k], [0.058 * s.k, 0.05 * s.k], 5), M['char'], CHAR, None, s.body)

    def lanyard(s, col=None, card=None, sway=0.0):
        rn = s.rn; col = LAN[rn.i(0, len(LAN) - 1)] if col is None else col
        card = rn.i(0, 3) if card is None else card
        dp = getattr(s, 'deep', 1.0); wd = getattr(s, 'wide', 1.0)
        cx = sway + rn.u(-0.03, 0.03); cy = -0.2 + rn.u(-0.04, 0.03); zc = 0.128 * dp
        soot = rn.u(0.4, 0.9); c2 = tuple(c * soot for c in col)
        for sd in (-1, 1):
            a = V3((sd * 0.07 * wd, 0.03, 0.05 * dp)); b_ = V3((sd * 0.085 * wd, -0.03, 0.118 * dp)); c = V3((cx + sd * 0.012, cy, zc + 0.006 + (0.005 if sd > 0 else 0.0)))
            w = V3((0.016, 0, 0))
            s.b.add(merge(p_quad(a - w, a + w, b_ + w, b_ - w), p_quad(b_ - w, b_ + w, c + w, c - w)), M['bits'], BF('strap', 1), s.M, c2)
        tilt = rn.u(-0.5, 0.5); cw, ch = 0.105, 0.14
        Mc = s.M @ T(cx, cy + 0.01, zc - 0.03) @ RZ(tilt) @ RX(-0.3 + rn.u(-0.06, 0.06)) @ RY(rn.u(-0.22, 0.22))
        s.b.add(p_quad((-cw / 2, -ch, 0), (cw / 2, -ch, 0), (cw / 2, 0, 0), (-cw / 2, 0, 0)), M['bits'], AT['bits'].face('card%d' % card, 'z', 0.5), Mc, rn.u(0.5, 0.9))
        return s

    def leg(s, side, hip, knee_dir, foot, heel=False, tint=None):
        rn = s.rn; K = s.k
        p1, p2 = ik2(hip, foot, 0.44 * K, 0.42 * K, knee_dir)
        tint = tint if tint is not None else s.body * rn.u(0.8, 1.1)
        s.b.add(limb_prim(hip, p1, p2, 0.085 * K, 0.06 * K, 0.042 * K, 5, knob=1.08), M['char'], CHAR, None, tint, jit=0.01)
        fwd = (p2 - p1).normalized(); up = fwd.orthogonal() if abs(fwd.dot(V3(knee_dir).normalized())) > 0.9 else V3(knee_dir)
        toe = (up - fwd * up.dot(fwd)).normalized()
        s.b.add(shoe_prim(heel), M['bits'], BT('shoer' if heel else 'shoe', 1), frame(toe, -fwd, p2) @ SC(K * 1.1), rn.u(0.22, 0.4) if heel else rn.u(0.6, 1.0))


def briefcase(b, Mw, rn):
    b.add(p_box(0.44, 0.31, 0.105), M['bits'], BT('leather' if rn.chance(0.6) else 'leatherb', 1), Mw, rn.u(0.3, 0.6))
    for x in (-0.08, 0.08): b.add(p_box(0.02, 0.02, 0.07, bottom=False), M['bits'], BT('leatherb', 1), Mw @ T(x, 0.17, 0) @ RX(-math.pi / 2), 0.8)
    b.add(p_box(0.2, 0.022, 0.026), M['bits'], BT('leatherb', 1), Mw @ T(0, 0.205, 0), 0.8)
    for x in (-0.13, 0.13): b.add(p_box(0.045, 0.05, 0.012, bottom=False), M['bits'], BT('brass', 1), Mw @ T(x, 0.115, 0.056), rn.u(0.6, 1.0))


def umbrella(b, Mw, rn, opened=False):
    """the tip at the origin, the shaft along +y (a furled one: 0.9 m; an open one: its bare ribs and a rag of cloth)"""
    L = 0.86
    b.add(p_tube([(0, 0, 0), (0, 0.07, 0), (0, L, 0)], [0.006, 0.012, 0.012], 4), M['bits'], BT('rib', 1), Mw, 0.7)
    hp = [(0, L, 0), (0, L + 0.1, 0), (0.03, L + 0.16, 0), (0.085, L + 0.17, 0), (0.12, L + 0.12, 0), (0.12, L + 0.07, 0)]
    b.add(p_tube(hp, 0.016, 5, cap1=True), M['bits'], BT('wood', 1), Mw, rn.u(0.6, 1.0))
    if not opened:
        b.add(p_tube([(0, 0.07, 0), (0, 0.2, 0), (0, 0.62, 0), (0, 0.72, 0)], [0.014, 0.04, 0.05, 0.02], 6, twist=0.5), M['bits'], BF('brolly', 1), Mw, rn.u(0.6, 1.0))
        b.add(p_box(0.03, 0.03, 0.02), M['bits'], BT('strap', 1), Mw @ T(0.045, 0.5, 0), LAN[rn.i(0, 2)])
    else:
        hub = V3((0, 0.2, 0)); tips = []
        for k in range(8):
            a = 2 * math.pi * k / 8; bend = rn.u(0.55, 1.0)
            tip = V3((math.cos(a) * 0.5 * bend, 0.2 - 0.12 + rn.u(-0.12, 0.2), math.sin(a) * 0.5 * bend)); tips.append(tip)
            b.add(p_tube([hub, hub.lerp(tip, 0.5) + V3((0, 0.06, 0)), tip], 0.006, 3), M['bits'], BT('rib', 1), Mw, 0.8)
        for k in (0, 1, 4, 5, 6):
            b.add(([hub, tips[k], tips[(k + 1) % 8]], [(0, 1, 2), (2, 1, 0)], [[(0, 0), (1, 0), (0.5, 1)]] * 2), M['bits'], BF('brolly', 1), Mw, rn.u(0.5, 0.9))


# ------------------------------------------------------------ the 17:32: clusters of them
class Mass:
    """routes what is built to the quadrant it stands in (the plug comes apart along a cross at the end)"""
    NAMES = ('mass_ne', 'mass_nw', 'mass_sw', 'mass_se')
    def __init__(s): s.B = [Buf(n) for n in s.NAMES]; s.figs = 0; s.spots = []; s.big = []; s.tally = {}; s._t = 0
    def mark(s, k): t = sum(b.tris() for b in s.B); s.tally[k] = s.tally.get(k, 0) + t - s._t; s._t = t
    def at(s, x, y): s.spots.append((x, y)); return s.B[(0 if y >= 0 else 3) if x >= 0 else (1 if y >= 0 else 2)]


def zdir(): return V3((0, 0, 1))
GLASS_Z = -0.05     # the back of the enamel: hands lie flat against it


def lattice_near(x, y, pad=0.16):
    """is this spot (on the plane behind the plates) under a spoke or the ring of the lattice?"""
    r = math.hypot(x, y); a = math.atan2(y, x) % (math.pi / 4)
    if abs(r - R_IN) < pad + 0.1 or r > HOOP_R - 0.12 - pad or r < 0.45: return True
    seam = min(a, math.pi / 4 - a) * r
    if r > R_IN: return seam < pad + 0.1
    a2 = math.atan2(y, x) % (math.pi / 2)
    return min(a2, math.pi / 2 - a2) * r < pad + 0.1


def blocked(x, y, grow=0.0):
    """spots that have to stay clear: the inspector's bay, the lamp cans"""
    return abs(x) < 0.85 + grow and -3.3 < y < -1.3 + grow


def presser(ms, x, y, rot, rn, z=-0.5, hero=True, both=True, look=0.0):
    """someone up against the inside of the sign: palms flat on it, the face between them (a face at a window)"""
    if eye_hit(x, y, 0.45): return bust(ms, x, y, core_z(x, y) + 0.2, rot, rn, arm='reach', pitch=0.5)   # no glass to lean on behind a lamp
    b = ms.at(x, y); ms.figs += 1; ms.big.append((x, y))
    Mw = T(x, y, z) @ RZ(rot) @ RX(rn.u(0.12, 0.3)) @ RY(rn.u(-0.2, 0.2))
    f = Fig(b, Mw, rn, rn.u(0.98, 1.1), hero=hero)
    f.torso(rn.u(0.95, 1.1), 1.0, shirt=rn.pick([0, 0, 1, 2, None]))
    f.head(yaw=look + rn.u(-0.25, 0.25), pitch=rn.u(-0.5, -0.2), roll=rn.u(-0.25, 0.25), at=(0, 0.178, 0.03))
    up = V3((-math.sin(rot), math.cos(rot), 0)); rt = V3((math.cos(rot), math.sin(rot), 0))
    for side in ((-1, 1) if both else (rn.sign(),)):
        tx = V3((x, y, 0)) + rt * side * rn.u(0.24, 0.36) + up * rn.u(0.14, 0.38)
        fd = (up + rt * side * rn.u(-0.1, 0.6)).normalized()
        if lattice_near(tx.x, tx.y):  # a bar of the lattice is in the way: hold it
            f.arm(side, (tx.x, tx.y, -0.26), 'grip', fingers=fd, palm=zdir(), hs=1.35)
        else:
            f.arm(side, (tx.x, tx.y, GLASS_Z - 0.02), 'flat', fingers=fd, palm=zdir(), hs=1.4)
    if rn.chance(0.75): f.lanyard()
    return f


def bust(ms, x, y, z, rot, rn, yaw=0.0, pitch=0.2, shirt='r', arm=None, lan=0.6, scale=None, k=6, face=None, jaw=None, body=None, neck=None):
    """head and shoulders standing out of the mass, facing roughly out. arm = None | 'reach' | 'hang' | 'grip'"""
    b = ms.at(x, y); ms.figs += 1; ms.big.append((x, y))
    Mw = T(x, y, z) @ RZ(rot + rn.u(-0.25, 0.25)) @ RX(pitch + rn.u(-0.15, 0.2)) @ RY(yaw + rn.u(-0.35, 0.35))
    f = Fig(b, Mw, rn, scale or rn.u(0.96, 1.12), body=body)
    neck = rn.chance(0.55) if neck is None else neck
    f.torso(rn.u(0.88, 1.18), rn.u(0.9, 1.08), length=rn.u(0.3, 0.46), k=6, shirt=(rn.pick([0, 1, 2, None, None]) if shirt == 'r' else shirt), neck=neck)
    f.head(yaw=rn.u(-0.6, 0.6), pitch=rn.u(-0.45, 0.25) - pitch * 0.6, roll=rn.u(-0.45, 0.45), face=face, jaw=jaw, at=(rn.u(-0.02, 0.02), 0.175 if neck else 0.13, 0.012))
    if rn.chance(lan): f.lanyard()
    if arm == 'reach':
        sd = rn.sign(); tgt = f.w((sd * rn.u(0.1, 0.45), rn.u(-0.05, 0.4), rn.u(0.42, 0.56)))
        f.arm(sd, tgt, rn.pick(['claw', 'claw', 'flat']), palm=f.d((0, -0.4, 1)), hs=1.35)
        f.stub(-sd, f.d((-sd, -0.6, -0.5)))
    elif arm == 'hang':
        for sd in (-1, 1):
            if rn.chance(0.7): f.arm(sd, f.w((sd * rn.u(0.2, 0.35), rn.u(-0.5, -0.3), rn.u(0.1, 0.3))), 'mitt', palm=f.d((0, 0, -1)), hs=1.25)
    elif arm == 'grip':
        sd = rn.sign(); tgt = f.w((sd * rn.u(0.15, 0.3), rn.u(0.05, 0.3), rn.u(0.3, 0.45)))
        f.arm(sd, tgt, 'grip', fingers=f.d((0, 1, 0.2)), palm=f.d((0, 0, 1)), hs=1.3)
    else:
        for sd in (-1, 1): f.stub(sd, f.d((sd, -0.8, -0.4)))
    return f


def slumper(ms, x, y, z, rot, rn, lite=False):
    """folded forward: you see the crown of the head, the back of a jacket, arms hanging toward you"""
    b = ms.at(x, y); ms.figs += 1; ms.big.append((x, y))
    Mw = T(x, y, z) @ RZ(rot) @ RX(rn.u(1.0, 1.45)) @ RY(rn.u(-0.3, 0.3))
    f = Fig(b, Mw, rn, rn.u(0.98, 1.12))
    f.torso(rn.u(0.95, 1.12), 1.0, length=0.42, k=6)
    f.head(pitch=rn.u(0.2, 0.7), roll=rn.u(-0.4, 0.4), yaw=rn.u(-0.6, 0.6), jaw=0.2)
    for sd in (-1, 1):
        if rn.chance(0.3 if lite else 0.8):
            tgt = f.w((sd * rn.u(0.18, 0.4), rn.u(0.25, 0.52), rn.u(-0.1, 0.2)))
            f.arm(sd, tgt, rn.pick(['mitt', 'mitt', 'claw']), palm=f.d((0, -1, 0)), hs=1.3)
    if rn.chance(0.5): f.lanyard(sway=rn.u(-0.05, 0.05))
    return f


def legs(ms, x, y, z, rot, rn, heel=False):
    """a pair of legs out of the mass, knees bent, shoes on"""
    b = ms.at(x, y); ms.figs += 1
    Mw = T(x, y, z) @ RZ(rot); f = Fig(b, Mw, rn, rn.u(0.98, 1.1)); f.body = rn.u(0.3, 0.5)
    for sd in (-1, 1):
        hip = f.w((sd * 0.1, 0, -0.1)); foot = f.w((sd * rn.u(0.08, 0.3), rn.u(0.45, 0.75), rn.u(0.1, 0.45)))
        f.leg(sd, hip, f.d((rn.u(-0.3, 0.3), 0.3, 1)), foot, heel=heel)


def loose_arm(ms, x, y, z, direction, rn, hand='claw', length=1.0):
    """an arm on its own, out of the mass"""
    b = ms.at(x, y)
    p0 = V3((x, y, z)); dv = V3(direction).normalized()
    f = Fig(b, T(x, y, z), rn, rn.u(1.0, 1.12)); f.wide = 0.0
    tgt = p0 + dv * 0.52 * length * f.k
    f.arm(1, tgt, hand, palm=(dv.orthogonal() + zdir() * 0.5), pole=dv.orthogonal(), hs=1.35)


def cluster(ms, kind, cx, cy, rot, rn):
    """a knot of fused people about 1.6 m across. kind: window | pile | choir | reach | tangle"""
    def P(lx, ly): lx *= 0.86; ly *= 0.86; c, s_ = math.cos(rot), math.sin(rot); return cx + lx * c - ly * s_, cy + lx * s_ + ly * c
    def cz(lx, ly): x, y = P(lx, ly); return core_z(x, y) - 0.04
    if kind == 'window':
        x, y = P(0, -0.1)
        if not blocked(x, y): presser(ms, x, y, rot + rn.u(-0.3, 0.3), rn)
        for lx, ly, dr in ((-0.52, 0.12, 0.5), (0.55, 0.0, -0.5)):
            x, y = P(lx, ly)
            if not blocked(x, y): bust(ms, x, y, cz(lx, ly) + 0.34, rot + dr + rn.u(-0.3, 0.3), rn, yaw=-dr, arm=rn.pick(['grip', None]), k=8)
        x, y = P(0.1, 0.75)
        if not blocked(x, y): slumper(ms, x, y, cz(0.1, 0.75) + 0.3, rot + math.pi + rn.u(-0.5, 0.5), rn)
        x, y = P(-0.3, -0.75)
        if not blocked(x, y): bust(ms, x, y, cz(-0.3, -0.75) + 0.22, rot + rn.u(-1, 1), rn, pitch=0.5, lan=0.8)
    elif kind == 'pile':
        for lx, ly, dr in ((-0.4, 0.3, 2.4), (0.45, 0.35, -2.0), (0.05, -0.5, 3.4)):
            x, y = P(lx, ly)
            if not blocked(x, y): slumper(ms, x, y, cz(lx, ly) + 0.3, rot + dr + rn.u(-0.4, 0.4), rn)
        x, y = P(0.0, 0.05)
        if not blocked(x, y): bust(ms, x, y, cz(0, 0.05) + 0.3, rot + rn.u(-0.6, 0.6), rn, arm='reach', pitch=0.35)
        x, y = P(0.6, -0.35)
        if not blocked(x, y): legs(ms, x, y, cz(0.6, -0.35) + 0.08, rot + rn.u(0, 6.28), rn, heel=rn.chance(0.3))
        x, y = P(-0.55, -0.3)
        if not blocked(x, y): briefcase(ms.at(x, y), T(x, y, cz(-0.55, -0.3) + 0.22) @ RZ(rn.u(0, 6.28)) @ RX(rn.u(0.3, 1.2)) @ RY(rn.u(-0.5, 0.5)), rn)
    elif kind == 'choir':
        for lx, ly in ((-0.5, 0.25), (0.0, 0.42), (0.5, 0.25), (-0.28, -0.22), (0.3, -0.25), (0.0, -0.62)):
            x, y = P(lx + rn.u(-0.06, 0.06), ly + rn.u(-0.06, 0.06))
            if blocked(x, y): continue
            bust(ms, x, y, cz(lx, ly) + rn.u(0.26, 0.42), rot + rn.u(-0.5, 0.5), rn, pitch=rn.u(0.25, 0.6), arm=rn.pick([None, None, 'grip', 'reach']), lan=0.7,
                 face=rn.pick([0, 2, 5, 0, 2, 1]), jaw=rn.u(0.7, 1.0), k=8)
    elif kind == 'reach':
        for lx, ly, dr in ((-0.3, 0.1, 0.4), (0.4, -0.2, -0.6)):
            x, y = P(lx, ly)
            if not blocked(x, y): bust(ms, x, y, cz(lx, ly) + 0.36, rot + dr, rn, arm='reach', pitch=0.4, k=8)
        for lx, ly in ((0.1, 0.7), (-0.6, -0.5)):
            x, y = P(lx, ly)
            if not blocked(x, y): bust(ms, x, y, cz(lx, ly) + 0.24, rot + rn.u(0, 6.28), rn, pitch=rn.u(0.2, 0.7), arm='hang')
        x, y = P(0.55, 0.5)
        if not blocked(x, y): umbrella(ms.at(x, y), T(x, y, cz(0.55, 0.5) - 0.1) @ RZ(rn.u(0, 6.28)) @ RX(rn.u(0.9, 1.35)), rn, opened=rn.chance(0.35))
        x, y = P(-0.2, -0.7)
        if not blocked(x, y): loose_arm(ms, x, y, cz(-0.2, -0.7) + 0.1, (rn.u(-0.5, 0.5), rn.u(-0.5, 0.5), 1), rn)
    else:  # tangle
        x, y = P(-0.35, 0.3)
        if not blocked(x, y): legs(ms, x, y, cz(-0.35, 0.3) + 0.1, rot + rn.u(0, 6.28), rn, heel=rn.chance(0.4))
        x, y = P(0.4, 0.2)
        if not blocked(x, y): bust(ms, x, y, cz(0.4, 0.2) + 0.3, rot + 1.5, rn, yaw=-1.2, pitch=0.2, arm='grip')
        x, y = P(0.0, -0.5)
        if not blocked(x, y): slumper(ms, x, y, cz(0, -0.5) + 0.3, rot + rn.u(0, 6.28), rn)
        for lx, ly in ((-0.6, -0.3), (0.55, -0.45), (0.1, 0.75)):
            x, y = P(lx, ly)
            if not blocked(x, y): loose_arm(ms, x, y, cz(lx, ly) + 0.1, (rn.u(-0.7, 0.7), rn.u(-0.7, 0.7), 1), rn, rn.pick(['claw', 'flat', 'mitt']))
        x, y = P(-0.1, 0.1)
        if not blocked(x, y) and rn.chance(0.6): briefcase(ms.at(x, y), T(x, y, cz(-0.1, 0.1) + 0.2) @ RZ(rn.u(0, 6.28)) @ RX(rn.u(0.2, 1.0)), rn)


def wall_r(a, z):
    """the plug's radius: squeezed to the bore in most places, sagging away from it in others (more toward the back)"""
    n = fbm(math.cos(a) * 1.6 + z * 0.35, math.sin(a) * 1.6, z * 0.3, 3); back = min(1.0, max(0.0, (-z - 1.2) / 4.5))
    return min(4.56, MASS_R + 0.04 * n) - max(0.0, n - 0.05) * (0.5 + 1.4 * back) - 0.22 * back * back


def PACK_UV(p):
    a = math.atan2(p.y, p.x)
    return (a * 4.5 / 4.2, p.z / 4.2) if p.z > -7.0 else (p.x / 4.2, p.y / 4.2)   # (4.2 m a repeat: the heads come out life size)


MASS_ZW = [MASS_Z0 - 0.12, -1.5, -2.5, -3.6, -4.7, -5.7, MASS_Z1]; MASS_NA = 12
def wall_mesh_r(a, z):
    """the radius of the plug's wall AS MESHED (between the rings and columns mass_core builds): what stands on it uses this"""
    a %= 2 * math.pi; q = int(a / (math.pi / 2)) % 4; t = (a - q * math.pi / 2) / (math.pi / 2) * MASS_NA; k = min(MASS_NA - 1, int(t)); ft = t - k
    a0, a1 = q * math.pi / 2 + k * (math.pi / 2) / MASS_NA, q * math.pi / 2 + (k + 1) * (math.pi / 2) / MASS_NA
    z = max(MASS_ZW[-1], min(MASS_ZW[0], z)); i = max(j for j in range(len(MASS_ZW) - 1) if MASS_ZW[j] >= z); fz = (MASS_ZW[i] - z) / (MASS_ZW[i] - MASS_ZW[i + 1])
    r00, r01, r10, r11 = wall_r(a0, MASS_ZW[i]), wall_r(a1, MASS_ZW[i]), wall_r(a0, MASS_ZW[i + 1]), wall_r(a1, MASS_ZW[i + 1])
    return min(lerp(lerp(r00, r01, ft), lerp(r10, r11, ft), fz), lerp(r00, r10, fz), lerp(r01, r11, fz)) * math.cos(math.pi / 4 / MASS_NA)


def mass_core(ms):
    """the plug itself: a lumpy charred cork, in four wedges with a hair between them. Each wedge is closed (the cut
    faces are meat: you see them when it comes apart)."""
    NA = MASS_NA  # per quadrant
    RS = [0.0, 0.45, 0.9, 1.35, 1.8, 2.25, 2.7, 3.15, 3.6, 4.05, 4.45]
    rn = Rnd(5)
    ZW = MASS_ZW
    BACK = [(3.75, -7.0), (2.9, -7.35), (1.6, -7.6)]
    for q in range(4):
        b = ms.B[q]; a0 = q * math.pi / 2; eps = 0.0012 / 2.0
        angs = [a0 + eps + (math.pi / 2 - 2 * eps) * k / NA for k in range(NA + 1)]
        prof = []  # per angle: the outline from the middle of the front face, over the lip, down the wall, to the middle of the back
        for a in angs:
            c, s_ = math.cos(a), math.sin(a); row = []
            for r_ in RS: row.append(V3((r_ * c, r_ * s_, core_z(r_ * c, r_ * s_) if r_ > 0 else core_z(0, 0))))
            for z in ZW: rr_ = wall_r(a, z); row.append(V3((rr_ * c, rr_ * s_, z)))
            for r_, z in BACK: rr2 = r_ * (1 + 0.22 * fbm(c * 2.2, s_ * 2.2, r_ * 0.7, 2)); row.append(V3((rr2 * c, rr2 * s_, z + 0.35 * fbm(c * 3, s_ * 3, r_))))
            row.append(V3((0, 0, -7.65)))
            prof.append(row)
        nrow = len(prof[0])
        # the axis points are shared by every angle: move each wedge's a hair off the axis so they don't touch
        mid = a0 + math.pi / 4; off = V3((math.cos(mid), math.sin(mid), 0)) * 0.003
        for row in prof: row[0] = row[0] + off; row[-1] = row[-1] + off
        V_ = [p for row in prof for p in row]; F_ = []; UV_ = []
        for k in range(NA):
            for i in range(nrow - 1):
                a_, b_, c_, d_ = k * nrow + i, (k + 1) * nrow + i, (k + 1) * nrow + i + 1, k * nrow + i + 1
                F_.append((a_, b_, c_, d_)); UV_.append([(V_[j].x + V_[j].z * 0.5, V_[j].y + V_[j].z * 0.3) for j in (a_, b_, c_, d_)])
        cuts = []
        for k_ in (0, NA):   # the two cut faces
            row = prof[k_]; cen = sum(row, V3()) / len(row)
            Vc = list(row) + [cen]; n_ = len(row)
            Fc = [(i, (i + 1) % n_, n_) for i in range(n_)]
            cuts.append((Vc, Fc, [[(0, 0), (1, 0), (0.5, 1)]] * n_))
        skin, c0, c1 = outward([(V_, F_, UV_)] + cuts)   # (the rows meet at the axis: those slivers go)
        wall = [fi for fi, f in enumerate(skin[1]) if sum((skin[0][i].z for i in f)) / len(f) < MASS_Z0 - 0.3 and (sum((math.hypot(skin[0][i].x, skin[0][i].y) for i in f)) / len(f) > 4.2 or sum((skin[0][i].z for i in f)) / len(f) < -6.0)]
        ws = set(wall)
        b.add((skin[0], [f for i, f in enumerate(skin[1]) if i not in ws], [u for i, u in enumerate(skin[2]) if i not in ws]), M['char'], ('tile', 0.5), None, 0.085)
        b.add((skin[0], [skin[1][i] for i in wall], [skin[2][i] for i in wall]), M['pack'], ('fn', PACK_UV), None, 0.8)
        for cf, k_ in ((c0, 0), (c1, NA)):
            ax = V3((math.cos(angs[k_]), math.sin(angs[k_]), 0))
            b.add(cf, M['bits'], ('fn', lambda p, ax=ax: px_uv(AT['bits'].R['flesh'], AT['bits'].tex, (p.dot(ax) * 0.37) % 1.0 * 0.999, (p.z * 0.37) % 1.0 * 0.999, 0.5)), None, 0.8)


def build_mass(N):
    ms = Mass(); rn = Rnd(1732)
    # --- where the knots of people go: set pieces first (what the first fallen plates show), then a scatter
    plan = [('window', -2.05, -2.35, 0.25, 11),     # behind plate 09 (the first to fall): a face at a window
            ('window', -1.45, 3.05, -0.3, 12),      # behind plate 06
            ('reach', 3.15, -1.2, 0.6, 13),         # behind plate 11
            ('choir', 1.75, -2.25, 0.2, 14), ('choir', -0.25, -3.75, 0.0, 15), ('choir', 2.9, -2.9, -0.4, 16), ('choir', -3.35, -1.2, 0.5, 17),   # the mouth
            ('window', 0.0, -0.45, 0.0, 18),        # dead centre, under the hub
            ('pile', 2.75, 1.9, 1.0, 19), ('window', 3.3, 0.45, -0.2, 20), ('reach', -3.0, 1.2, 0.3, 21), ('tangle', 0.2, 2.3, 0.0, 22), ('pile', -0.5, 3.9, 2.0, 23)]
    kinds = ['window', 'pile', 'choir', 'reach', 'tangle', 'pile', 'reach', 'window', 'tangle']
    tries = 0; DMIN = float(arg('dmin', 1.28))
    while tries < 9000:
        tries += 1
        a = rn.u(0, 2 * math.pi); r_ = math.sqrt(rn.u(0, 1)) * 4.05
        x, y = r_ * math.cos(a), r_ * math.sin(a)
        if any(math.hypot(x - q[1], y - q[2]) < DMIN for q in plan) or blocked(x, y, 0.3): continue
        if eye_hit(x, y, 0.3) and rn.chance(0.5): continue
        kind = 'choir' if (below_crack(x, y) and rn.chance(0.6)) else rn.pick(kinds)
        rot = rn.u(-0.9, 0.9) if rn.chance(0.6) else rn.u(0, 2 * math.pi)
        plan.append((kind, x, y, rot, 100 + len(plan)))
    KNOTS[:] = [(q[1], q[2]) for q in plan]
    mass_core(ms); ms.mark('core')
    for kind, x, y, rot, seed in plan: cluster(ms, kind, x, y, rot, Rnd(seed))
    placed = KNOTS
    # --- between the knots it is still bodies: backs, shoulders and the backs of heads, half sunk
    for k in range(int(arg('lumps', 0))):
        r2 = Rnd(3000 + k); a = r2.u(0, 2 * math.pi); r_ = math.sqrt(r2.u(0, 1)) * 4.4; x, y = r_ * math.cos(a), r_ * math.sin(a)
        if blocked(x, y, 0.0): continue
        near = min(math.hypot(x - kx, y - ky) for kx, ky in KNOTS)
        if near < 0.55: continue
        b = ms.at(x, y); zz = core_z(x, y)
        tilt = RZ(r2.u(0, 6.28)) @ RX(r2.u(-0.5, 0.5)) @ RY(r2.u(-0.5, 0.5))
        q = r2.u(0, 1)
        if q < 0.5: b.add(mound(r2.u(0.2, 0.27), r2.u(0.26, 0.4), r2.u(0.13, 0.22), 6), M['char'], CHAR, T(x, y, zz - 0.02) @ tilt, r2.u(0.2, 0.45))     # a back
        elif q < 0.8: b.add(mound(0.1, 0.125, r2.u(0.1, 0.14), 6), M['char'], ('tile', 0.3), T(x, y, zz - 0.01) @ tilt, r2.u(0.3, 0.6))                    # the back of a head
        else:
            dv = V3((r2.u(-1, 1), r2.u(-1, 1), 0)).normalized()
            p0 = V3((x, y, zz - 0.04)) - dv * 0.3; p1 = V3((x, y, zz + r2.u(0.06, 0.14))); p2 = V3((x, y, zz - 0.04)) + dv * 0.3 + V3((r2.u(-0.1, 0.1), r2.u(-0.1, 0.1), 0))
            b.add(p_tube([p0, p1, p2], [0.08, 0.07, 0.05], 5), M['char'], CHAR, None, r2.u(0.22, 0.45))                                                   # a knee, an elbow
    ms.mark('knots')
    # --- then every gap a person would fit in gets one: nothing of the plug's own face shows bigger than a head
    HX = float(arg('hex', 0.6)); row = 0; yv = -4.3; fill = 0
    while yv < 4.3:
        xv = -4.3 + (HX / 2 if row % 2 else 0.0)
        while xv < 4.3:
            r2 = Rnd(4000 + row * 97 + int((xv + 5) * 13)); x, y = xv + r2.u(-0.12, 0.12), yv + r2.u(-0.12, 0.12); xv += HX
            if math.hypot(x, y) > 4.25 or blocked(x, y, 0.08): continue
            if min(math.hypot(x - sx_, y - sy_) for sx_, sy_ in ms.big) < float(arg('fillr', 0.4)): continue
            fill += 1; q = r2.u(0, 1); zz = core_z(x, y)
            if q < 0.26: bust(ms, x, y, zz + r2.u(0.14, 0.3), r2.u(-1.2, 1.2) if r2.chance(0.6) else r2.u(0, 6.28), r2, pitch=r2.u(0.15, 0.8), lan=0.65, arm=r2.pick([None, None, None, 'hang', 'reach']))
            elif q < 0.44: slumper(ms, x, y, zz + 0.26, r2.u(0, 6.28), r2, lite=True)
            else:   # a back and the back of a head: someone face down in it
                b = ms.at(x, y); ms.big.append((x, y)); ms.figs += 1; rot = r2.u(0, 6.28); tn = r2.u(0.2, 0.42)
                Mx = T(x, y, zz - 0.03) @ RZ(rot) @ RX(r2.u(-0.3, 0.3)) @ RY(r2.u(-0.3, 0.3))
                b.add(torso_prim(6, r2.u(0.95, 1.2), 1.0, r2.u(0.36, 0.5), False), M['char'], CHAR, Mx @ T(0, 0.1, 0.02) @ RX(math.pi / 2 + r2.u(-0.25, 0.25)) @ RY(math.pi), tn, jit=0.016)
                if r2.chance(0.75): b.add(mound(0.1, 0.125, r2.u(0.1, 0.13), 6), M['char'], ('tile', 0.3), Mx @ T(r2.u(-0.05, 0.05), 0.2, -0.03) @ RX(r2.u(-0.3, 0.2)), min(1.0, tn * 1.3), jit=0.006)
                if r2.chance(0.4): loose_arm(ms, x + 0.25 * math.cos(rot), y + 0.25 * math.sin(rot), zz + 0.03, (r2.u(-0.6, 0.6), r2.u(-0.6, 0.6), 0.9), r2, r2.pick(['claw', 'flat', 'mitt']))
        yv += HX * 0.866; row += 1
    print('JF_MASS fill', fill, 'spots', len(ms.spots)); ms.mark('fill')
    # --- round the inspector: backs turned on him, a ring of arms that do not touch him
    for k, (x, y, rot) in enumerate(((-1.0, -2.2, 1.9), (1.05, -2.3, -1.9), (-1.0, -1.25, 2.6), (1.0, -1.2, -2.6))):
        slumper(ms, x, y, core_z(x, y) + 0.25, rot, Rnd(700 + k))
    # --- they have grown together: ropes of skin from one to the next
    rn3 = Rnd(77); big = list(ms.big); nb = 0
    for i, (x0, y0) in enumerate(big):
        for j in range(i + 1, len(big)):
            x1, y1 = big[j]; d = math.hypot(x1 - x0, y1 - y0)
            if not (0.38 < d < 0.8) or not rn3.chance(0.17) or blocked((x0 + x1) / 2, (y0 + y1) / 2): continue
            z0, z1 = core_z(x0, y0) + rn3.u(0.1, 0.3), core_z(x1, y1) + rn3.u(0.1, 0.3); mx, my = (x0 + x1) / 2 + rn3.u(-0.08, 0.08), (y0 + y1) / 2 + rn3.u(-0.08, 0.08)
            ms.at(mx, my).add(p_tube([(x0, y0, z0), (mx, my, (z0 + z1) / 2 - rn3.u(0.0, 0.1)), (x1, y1, z1)], [rn3.u(0.05, 0.09), rn3.u(0.025, 0.045), rn3.u(0.05, 0.09)], 4), M['char'], CHAR, None, rn3.u(0.2, 0.36), jit=0.01); nb += 1
    for k in range(9):   # behind it, what it drags: arms trailing on the track
        r2 = Rnd(9500 + k); a = r2.u(3.6, 5.8); r_ = r2.u(1.5, 3.4); x, y = r_ * math.cos(a), r_ * math.sin(a)
        f = Fig(ms.at(x, y), T(x, y, -7.2), r2, 1.1); f.wide = 0.0
        f.arm(1, (x + r2.u(-0.3, 0.3), y - r2.u(0.1, 0.4), -7.2 - 0.62), 'mitt', palm=(0, -1, 0), pole=(0, 1, 0), hs=1.3, l1=0.36, l2=0.32)
    ms.mark('bay')
    # --- hands over the rim: arms come round the outside of the hoop and lay their fingers on the enamel
    for k in range(24):
        a = (k + rn.u(0.15, 0.85)) * 2 * math.pi / 24
        if any(abs(((math.degrees(a) - sdeg + 180) % 360) - 180) < 6 for sdeg in SOCKETS) or abs(((math.degrees(a) - math.degrees(HANG_A) + 180) % 360) - 180) < 5: continue
        r2 = Rnd(5000 + k); c, s_ = math.cos(a), math.sin(a); out = V3((c, s_, 0)); b = ms.at(c, s_)
        rr_ = HOOP_R + 0.075; tint = r2.u(0.3, 0.5)
        b.add(p_tube([out * 4.4 + V3((0, 0, -0.95)), out * (rr_ + 0.02) + V3((0, 0, -0.45)), out * rr_ + V3((0, 0, PT + 0.075))], [0.07, 0.055, 0.042], 5), M['char'], CHAR, None, tint)
        tg = V3((-s_, c, 0)); fd = (-out + tg * r2.u(-0.35, 0.35)).normalized()
        Mh = frame(fd, zdir(), out * (rr_ - 0.01) + V3((0, 0, PT + 0.075))) @ SC(1.45)
        b.add(hand_flat(r2.u(0.7, 1.4), r2.sign()) if r2.chance(0.7) else hand_claw(r2.sign(), 0.3), M['char'], ('tile', 0.3), Mh, min(1.0, tint * 1.9))
    ms.mark('rim hands')
    # --- the roots of the arms: a fan of upper arms out of the lip at each socket, flat to the wall
    for k, sdeg in enumerate(SOCKETS):
        a = math.radians(sdeg); c, s_ = math.cos(a), math.sin(a); r2 = Rnd(6000 + k); b = ms.at(c, s_)
        tang = V3((-s_, c, 0)); out = V3((c, s_, 0))
        for j in range(4):
            t = (j - 1.5) * 0.14
            p0 = out * 4.3 + tang * t * 1.6 + V3((0, 0, -0.95)); p1 = out * 4.5 + tang * t * 1.1 + V3((0, 0, -0.72)); p2 = out * 4.5 + tang * t * 0.5 + V3((0, 0, -0.5))
            b.add(p_tube([p0, p1, p2], [0.075, 0.062, 0.055], 5, squash=1.0, cap1=True), M['char'], CHAR, None, r2.u(0.4, 0.62))
    ms.mark('sockets')
    # --- the wall and the back of the plug: people pressed flat by the bore (seen when you get behind it, never in the fight)
    for k in range(44):   # backs and heads in low relief all over the wall (the bore presses them flat)
        r2 = Rnd(8500 + k); a = r2.u(0, 2 * math.pi); z = -0.95 - r2.u(0, 1) * 5.6; c, s_ = math.cos(a), math.sin(a); out = V3((c, s_, 0))
        Mx = frame(out, (r2.u(-1, 1), r2.u(-1, 1), r2.u(-1, 1)), out * (wall_mesh_r(a, z) - 0.045) + V3((0, 0, z))) @ RX(r2.u(-0.12, 0.12)) @ RY(r2.u(-0.12, 0.12))
        b = ms.at(c, s_); tn = r2.u(0.2, 0.42)
        b.add(mound(r2.u(0.22, 0.3), r2.u(0.3, 0.55), r2.u(0.12, 0.14), 5), M['char'], CHAR, Mx, tn, jit=0.008)
        # (no heads on these: a flat little cap that close to the wall lay in its plane. the wall's picture has the heads)
    for k in range(int(arg('wallfigs', 0))):   # (whole figures on the wall: squashed flat their faces lay in the wall's own plane. the wall's picture does the job)
        r2 = Rnd(8000 + k); a = r2.u(0, 2 * math.pi); z = -1.1 - (r2.u(0, 1) ** 1.6) * 5.2
        c, s_ = math.cos(a), math.sin(a); out = V3((c, s_, 0))
        Mw = frame(out, (r2.u(-1, 1), r2.u(-1, 1), r2.u(-1, 1)), out * (wall_mesh_r(a, z) - 0.05) + V3((0, 0, z))) @ SC(1.08, 1.08, 0.42)
        f = Fig(ms.at(c, s_), Mw, r2, 1.0); ms.figs += 1
        f.torso(1.05, 1.0, length=0.45, k=6, shirt=None)
        f.head(yaw=r2.u(-1.3, 1.3), pitch=r2.u(-0.2, 0.2), roll=r2.u(-0.5, 0.5))
        if r2.chance(0.6): f.lanyard()
        for sd in (-1, 1):
            if r2.chance(0.6):
                tgt = f.w((sd * r2.u(0.3, 0.5), r2.u(-0.3, 0.45), 0.02)); tgt = V3((tgt.x, tgt.y, 0)).normalized() * (wall_mesh_r(math.atan2(tgt.y, tgt.x), tgt.z) + 0.02) + V3((0, 0, tgt.z))
                f.arm(sd, tgt, 'mitt', fingers=f.d((sd * 0.3, 1, 0)), palm=out, hs=1.3)
    for k in range(4):
        r2 = Rnd(9000 + k); a = r2.u(0, 2 * math.pi); r_ = r2.u(0.5, 3.6); x, y = r_ * math.cos(a), r_ * math.sin(a)
        z = -7.25 - 0.3 * (1 - r_ / 4.0)
        Mw = T(x, y, z) @ RZ(r2.u(0, 6.28)) @ RX(math.pi + r2.u(-0.5, 0.5))
        f = Fig(ms.at(x, y), Mw, r2, 1.05); ms.figs += 1
        f.torso(1.0, 1.0, length=0.4, k=6); f.head(pitch=r2.u(-0.4, 0.4), roll=r2.u(-0.5, 0.5))
        if k % 2 == 0: f.arm(1, f.w((0.4, 0.3, 0.45)), 'mitt', hs=1.3)
    ms.mark('wall and back'); print('JF_MASS tally', ms.tally, 'bridges', nb)
    mass = empty('mass'); N['mass'] = mass
    for b in ms.B:
        o = b.obj(sharp=72, weld=2e-5)
        # the core's rows meet at the axis in zero-area quads: drop them
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5); bm.to_mesh(o.data); bm.free()
        fix_uv(o); o.data.set_sharp_from_angle(angle=math.radians(72))
        N[b.name] = node(o, b.name, None, mass)
    print('JF_MASS figures', ms.figs, 'knots', len(placed), 'tris', sum(tri_count(N[n]) for n in Mass.NAMES))
    return mass


# ------------------------------------------------------------ the inspector
INFO = {}
INSP_AT = (0.0, -2.74, -0.9)   # his waist, in the root's space
INSP_S = 1.12
def glow_materials():
    def ember(px):
        r = np.random.default_rng(23); S = px.shape[0]
        px[:] = hexrgb(0x160c0a)
        pts = r.random((22, 2)) * S; yy, xx = np.mgrid[0:S, 0:S]
        d1 = np.full((S, S), 1e9); d2 = np.full((S, S), 1e9)
        for cx, cy in pts:
            d = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy); sw = d < d1
            d2 = np.where(sw, d1, np.minimum(d2, d)); d1 = np.where(sw, d, d1)
        e = d2 - d1
        px[:] = hexrgb(0x2a0a05); px[e < 1.7] = hexrgb(0x6a1c06); px[e < 0.85] = hexrgb(0xe85a12); px[(e < 0.4) & (r.random((S, S)) < 0.6)] = hexrgb(0xffc060)
    img = tex_canvas('rp_ember_t', 32, 32, ember)
    M['ember'] = mat('rp_inspector_glow', 0xffffff, rough=0.6, emit=0xffffff, strength=2.4, tex=img, emit_tex=True)
    def knot(px):
        px[:] = hexrgb(0x1a5a78); r = np.random.default_rng(29)
        px[r.random(px.shape[:2]) < 0.35] = hexrgb(0x4fd8ff); px[r.random(px.shape[:2]) < 0.08] = hexrgb(0xd8f6ff)
    M['knot'] = mat('rp_knot_glow', 0xffffff, rough=0.4, emit=0xffffff, strength=2.2, tex=tex_canvas('rp_knot_t', 16, 16, knot), emit_tex=True)


def ticket_punch():
    """a conductor's hand punch, 1.5 x life (0.25 m): a fixed lower handle that becomes the C-shaped jaw, an upper
    lever on a rivet that drives the pin. -> (body, lever) buffers built round the rivet (lever closes about x)"""
    body, lever = Buf('punch'), Buf('lever'); tr = M['tr']
    ch = TR('chrome', 1); br = TR('brass', 1)
    # the lower handle, bowed, with a finger loop at its end
    body.add(p_tube([(0, -0.012, 0.01), (0, -0.03, -0.05), (0, -0.045, -0.11), (0, -0.036, -0.16)], [0.011, 0.01, 0.009, 0.009], 5, squash=1.6, cap1=True), tr, ch)
    # the jaw: a C of steel in front of the rivet, the die at its lower lip
    body.add(p_box(0.034, 0.03, 0.05), tr, ch, T(0, -0.014, 0.03))
    body.add(p_box(0.03, 0.02, 0.085), tr, ch, T(0, -0.03, 0.085))
    body.add(p_box(0.032, 0.07, 0.022), tr, ch, T(0, 0.0, 0.118))
    body.add(p_box(0.028, 0.02, 0.05), tr, ch, T(0, 0.036, 0.1))
    body.add(xf(p_prism(8, 0.012, 0.014, top=True), RX(math.pi / 2) @ T(0, 0, -0.007)), tr, br, T(0, -0.02, 0.085))     # the die
    body.add(xf(p_prism(8, 0.014, 0.04, top=True, bottom=True), RY(math.pi / 2) @ T(0, 0, -0.02)), tr, br, T(0, 0, 0))    # the rivet
    body.add(p_box(0.02, 0.012, 0.03), tr, TR('black', 1), T(0, -0.052, 0.07))                                             # the chad box
    # the lever: the upper handle and the pin
    lever.add(p_tube([(0, 0.012, 0.0), (0, 0.04, -0.05), (0, 0.062, -0.11), (0, 0.058, -0.16)], [0.011, 0.01, 0.009, 0.009], 5, squash=1.6, cap1=True), tr, ch)
    lever.add(p_box(0.024, 0.02, 0.07), tr, ch, T(0, 0.016, 0.035) @ RX(0.25))
    lever.add(xf(p_prism(6, 0.007, 0.03, top=True), RX(math.pi / 2)), tr, br, T(0, 0.03, 0.085))                           # the pin
    return body, lever


def build_inspector(N):
    """the man who was checking tickets: fused in to the thighs, the cap fused to his head, the punch still in his
    right hand, the left held out for a ticket. Lit from inside through the split in his chest, his eyes and mouth.
    Built in his own space (waist at the origin, facing +z), then stood in the mass."""
    rn = Rnd(1732); bi, ch = M['bits'], M['char']
    B = {k: Buf(k) for k in ('insp_body', 'insp_head', 'insp_armR', 'insp_foreR', 'insp_punch_lever', 'insp_armL', 'insp_foreL', 'insp_base')}
    b = B['insp_body']
    rows = [(-0.2, 0.185, 0.125), (-0.02, 0.17, 0.118), (0.16, 0.18, 0.13), (0.36, 0.205, 0.14), (0.5, 0.235, 0.115), (0.56, 0.085, 0.08), (0.635, 0.06, 0.062)]
    rings_ = [superring(y, hx, hz, 10, 2.8, 0.012 if 0.1 < y < 0.45 else 0.0) for y, hx, hz in rows]
    V_, F_, UV_ = p_loft(rings_)
    # the jacket: buttoned front seen straight on, plain serge round the back; burnt darker toward the waist
    def jk(p): 
        return px_uv(AT['bits'].R['serge'], AT['bits'].tex, min(1, max(0, 0.5 + p.x / 0.5)), min(1, max(0, (p.y + 0.22) / 0.78)), 0.5)
    front = [fi for fi, f in enumerate(F_) if sum((V_[i].z for i in f)) / len(f) > 0.03]
    fs = set(front)
    burnt = lambda c: 0.22 + 0.6 * min(1.0, max(0.0, (c.y + 0.15) / 0.5)) * (0.75 + 0.25 * math.sin(c.x * 23 + c.y * 17))   # burnt black from the waist up
    b.add((V_, [F_[i] for i in front], [UV_[i] for i in front]), bi, ('fn', jk), None, burnt, jit=0.004)
    b.add((V_, [f for i, f in enumerate(F_) if i not in fs], [u for i, u in enumerate(UV_) if i not in fs]), bi, BT('capnavy', 1), None, lambda c: burnt(c) * 0.7, jit=0.004)
    # the split in his chest: the light is in there. ribs across it
    gl = [[V3((x * (1 - 0.5 * abs(y - 0.3) / 0.16), y, 0.128 + 0.012 * (1 - abs(x) / 0.07))) for x in (-0.07, 0.0, 0.07)] for y in (0.14, 0.24, 0.36, 0.46)]
    b.add(p_grid(gl), M['ember'], ('fn', lambda p: (0.5 + p.x * 6, (p.y - 0.12) * 2.7)), None, 1.0)
    for y in (0.19, 0.26, 0.33, 0.4): b.add(p_tube([(-0.085, y - 0.01, 0.125), (0, y + 0.012, 0.152), (0.085, y - 0.01, 0.125)], 0.011, 4), ch, CHAR, None, 0.3)
    for sx in (-1, 1):  # the torn edges of the jacket curling back from it, lapels, epaulettes with a button
        b.add(p_grid([[(sx * 0.07, 0.12, 0.137), (sx * 0.1, 0.13, 0.16), (sx * 0.14, 0.12, 0.138)], [(sx * 0.075, 0.3, 0.145), (sx * 0.115, 0.3, 0.172), (sx * 0.16, 0.3, 0.145)], [(sx * 0.05, 0.47, 0.13), (sx * 0.09, 0.47, 0.15), (sx * 0.13, 0.47, 0.125)]], flip=sx < 0), bi, BT('capnavy', 1), None, 0.4)
        b.add(p_box(0.1, 0.02, 0.07), bi, BT('capnavy', 1), T(sx * 0.17, 0.515, 0.0) @ RZ(-sx * 0.25), 0.75)
        b.add(xf(p_prism(6, 0.013, 0.01, dome=0.004), RX(-math.pi / 2)), bi, BT('brass', 1), T(sx * 0.2, 0.522, 0.0), 0.9)
        b.add(p_box(0.075, 0.03, 0.02), bi, BT('white', 1), T(sx * 0.05, 0.572, 0.062) @ RZ(sx * 0.5), 0.6)            # collar points
    # his lanyard (yellow: staff), the badge big enough to read; the satchel strap across him and the satchel
    for sd in (-1, 1): b.add(p_quad((sd * 0.075 - 0.014, 0.56, 0.06), (sd * 0.075 + 0.014, 0.56, 0.06), (sd * 0.1 + 0.014, 0.45, 0.137), (sd * 0.1 - 0.014, 0.45, 0.137)), bi, BF('strap', 1), None, LAN[1])
    b.add(p_box(0.11, 0.15, 0.012), bi, AT['bits'].face('card1', 'z', 0.5), T(0.125, 0.3, 0.158) @ RZ(0.2), 0.95)
    b.add(p_quad((0.086, 0.45, 0.14), (0.114, 0.45, 0.14), (0.14, 0.36, 0.16), (0.112, 0.36, 0.16)), bi, BF('strap', 1), None, LAN[1])
    b.add(p_tube([(0.2, 0.5, 0.03), (0.08, 0.36, 0.142), (-0.08, 0.14, 0.14), (-0.19, -0.02, 0.06)], 0.02, 4, squash=0.3), bi, BT('leatherb', 1), None, 0.8)
    b.add(p_box(0.2, 0.17, 0.085), bi, BT('leather', 1), T(-0.2, -0.1, 0.07) @ RY(-0.35), 0.5)
    b.add(p_box(0.214, 0.07, 0.1), bi, BT('leatherb', 1), T(-0.2, -0.03, 0.075) @ RY(-0.35), 0.7)
    # --- the head, on its own node (he looks at you)
    h = B['insp_head']; HY = 0.76
    fp, sk = head_prims(8, 0.35)
    Mh = T(0, HY, 0.012) @ SC(1.1)
    h.add(fp, bi, AT['bits'].face('face1', 'z', 0.5), Mh, 0.85, jit=0.003); h.add(sk, ch, ('tile', 0.3), Mh, 0.42, jit=0.003)
    h.add(p_box(0.03, 0.05, 0.035, taper=0.6), ch, ('tile', 0.3), Mh @ T(0, -0.005, 0.105) @ RX(-0.35), 0.5)        # what is left of his nose
    h.add(p_box(0.16, 0.018, 0.03), ch, ('tile', 0.3), Mh @ T(0, 0.052, 0.085), 0.3)                                # the brow
    for sx in (-1, 1):
        h.add(p_quad((sx * 0.048 - 0.02, 0.014, 0.0935), (sx * 0.048 + 0.02, 0.014, 0.0935), (sx * 0.048 + 0.02, 0.042, 0.092), (sx * 0.048 - 0.02, 0.042, 0.092)), M['ember'], ('fn', lambda p: (0.42 + p.x * 1.5, 0.3 + (p.y - 0.78) * 1.5)), Mh, 1.0)   # the light, in his eyes
        h.add(p_box(0.02, 0.06, 0.04), ch, ('tile', 0.3), Mh @ T(sx * 0.092, 0.01, 0.0) @ RY(sx * 0.3), 0.4)        # ears
    h.add(p_quad((-0.03, -0.085, 0.079), (0.03, -0.085, 0.079), (0.03, -0.055, 0.087), (-0.03, -0.055, 0.087)), M['ember'], ('fn', lambda p: (0.5 + p.x * 3, 0.2 + (p.y - 0.66) * 3)), Mh, 1.0)
    # the cap, fused on: band with REVENUE round the front, the badge, a wide crown tipped up at the front, a gloss peak
    CY = 0.085
    band = [[V3((math.sin(2 * math.pi * j / 12) * rx, y, math.cos(2 * math.pi * j / 12) * rz - 0.006)) for j in range(12)] for y, rx, rz in ((CY - 0.012, 0.094, 0.104), (CY + 0.045, 0.097, 0.107))]
    V_, F_, UV_ = p_loft(band)
    def bandu(p):
        q = Mh.inverted() @ p; a = math.atan2(q.x, q.z + 0.006) / (2 * math.pi)
        return px_uv(AT['bits'].R['band'], AT['bits'].tex, min(0.998, max(0.002, 0.5 + a * 2.85)), min(1, max(0, (q.y - CY + 0.012) / 0.057)), 0.5)
    h.add((V_, F_, UV_), bi, BT('capnavy', 1), Mh, 0.5)
    fb = [[V3((math.sin(a_) * 0.099, y, math.cos(a_) * 0.109 - 0.006)) for a_ in [(-0.85 + 1.7 * j / 6) for j in range(7)]] for y in (CY - 0.01, CY + 0.043)]
    h.add(p_grid(fb, flip=True), bi, ('fn', bandu), Mh, 0.95)
    crown = [[V3((math.sin(2 * math.pi * j / 12) * rx, y + (0.02 * math.cos(2 * math.pi * j / 12) if k_ else 0), math.cos(2 * math.pi * j / 12) * rz - 0.006)) for j in range(12)] for k_, (y, rx, rz) in enumerate(((CY + 0.045, 0.097, 0.107), (CY + 0.105, 0.135, 0.15), (CY + 0.118, 0.115, 0.13)))]
    h.add(p_loft(crown, tip1=V3((0, CY + 0.122, -0.006))), bi, BT('capnavy', 1), Mh, 0.75, jit=0.004)
    pk = [[V3((math.sin(a_) * (0.1 + e * 0.9), CY - 0.012 - e * 0.35 + 0.012 * math.cos(a_ * 2), math.cos(a_) * (0.108 + e) - 0.006)) for a_ in [(-1.0 + 2.0 * j / 6) for j in range(7)]] for e in (0.0, 0.035, 0.07)]
    h.add(p_grid(pk, flip=True), M['tr'], TR('peak', 1), Mh, 1.0); h.add(p_grid([[p + V3((0, -0.008, 0)) for p in row] for row in pk]), M['tr'], TR('peak', 1), Mh, 0.6)
    h.add(p_box(0.05, 0.05, 0.012), bi, AT['bits'].face('badge', 'z', 0.5), Mh @ T(0, CY + 0.075, 0.118) @ RX(-0.3), 1.0)
    for sx in (-1, 1):  # where it has run into him
        h.add(p_tube([(sx * 0.094, CY, 0.02), (sx * 0.097, CY - 0.05, 0.03), (sx * 0.085, CY - 0.1, 0.035)], [0.022, 0.016, 0.008], 4), bi, BT('capnavy', 1), Mh, 0.5)
        h.add(p_tube([(sx * 0.06, CY, -0.09), (sx * 0.065, CY - 0.06, -0.092), (sx * 0.05, CY - 0.11, -0.08)], [0.024, 0.016, 0.008], 4), bi, BT('capnavy', 1), Mh, 0.45)
    # --- the arms. his right (-x) holds the punch up in front of his chest; his left (+x) is held out, palm up, for the ticket
    SH = {-1: V3((-0.245, 0.47, 0.0)), 1: V3((0.245, 0.47, 0.0))}
    EL = {-1: V3((-0.3, 0.2, 0.08)), 1: V3((0.31, 0.19, 0.06))}
    WR = {-1: V3((-0.13, 0.3, 0.33)), 1: V3((0.15, 0.2, 0.34))}
    for sd, an, fn_ in ((-1, 'insp_armR', 'insp_foreR'), (1, 'insp_armL', 'insp_foreL')):
        B[an].add(p_tube([SH[sd], SH[sd].lerp(EL[sd], 0.5), EL[sd]], [0.068, 0.064, 0.055], 7, cap1=True), bi, BT('capnavy', 1), None, 0.6, jit=0.004)
        B[an].add(p_tube([SH[sd] + V3((0, 0.02, 0)), SH[sd] + V3((sd * 0.01, -0.03, 0))], [0.074, 0.078], 7), bi, BT('capnavy', 1), None, 0.7)
        fd = (WR[sd] - EL[sd]).normalized()
        B[fn_].add(p_tube([EL[sd], EL[sd].lerp(WR[sd], 0.45), WR[sd] - fd * 0.06], [0.058, 0.05, 0.043], 7), bi, BT('capnavy', 1), None, 0.55, jit=0.004)
        B[fn_].add(p_tube([WR[sd] - fd * 0.075, WR[sd] - fd * 0.04], [0.049, 0.05], 7), bi, BT('white', 1), None, 0.5)                    # a burnt cuff
        B[fn_].add(p_tube([WR[sd] - fd * 0.05, WR[sd]], [0.034, 0.032], 5), ch, CHAR, None, 0.5)
    # the right hand round the punch's handles; the punch points at you
    PR = WR[-1] + V3((0.02, 0.01, 0.075))          # the rivet
    Mp = frame((0.25, 0.1, 1), (0, 1, 0.05), PR) @ SC(1.3)
    pb, pl = ticket_punch()
    for src, dst in ((pb, B['insp_foreR']), (pl, B['insp_punch_lever'])):
        o_ = len(dst.V); dst.V.extend(Mp @ v for v in src.V)
        for q in range(len(src.F)): dst.F.append(tuple(o_ + i for i in src.F[q])); dst.UV.append(src.UV[q]); dst.MI.append(dst.mi(src.mats[src.MI[q]])); dst.TI.append(src.TI[q])
    Mhand = frame(Mp.to_3x3() @ V3((0, 0.25, -1)), Mp.to_3x3() @ V3((1, 0, 0)), Mp @ V3((0.045, -0.02, -0.02))) @ SC(1.25)
    B['insp_foreR'].add(hand_grip(1.15, -1), ch, ('tile', 0.3), Mhand, 0.55)
    # the left hand: open, palm up, thumb and finger pinched on a ticket that isn't there
    Ml = frame((-0.25, 0.12, 1), (0, -1, 0.2), WR[1]) @ SC(1.25)
    B['insp_foreL'].add(hand_claw(1, 0.35), ch, ('tile', 0.3), Ml, 0.55)
    # --- what he is fused into: a mound of backs and hands that do not quite touch him
    bs = B['insp_base']
    ringb = [[V3((math.cos(2 * math.pi * j / 12) * rx * (1 + 0.12 * math.sin(j * 2.3)), y, math.sin(2 * math.pi * j / 12) * rz * (1 + 0.1 * math.cos(j * 1.7)))) for j in range(12)] for y, rx, rz in ((-0.72, 0.62, 0.5), (-0.5, 0.5, 0.42), (-0.3, 0.3, 0.26), (-0.14, 0.2, 0.15))]
    bs.add(p_loft([r_[::-1] for r_ in ringb]), ch, CHAR, None, 0.2, jit=0.012)
    for k in range(7):
        a = -0.4 + k * 0.63 + rn.u(-0.15, 0.15); c, s_ = math.cos(a), math.sin(a)
        f = Fig(bs, T(c * 0.42, -0.55, s_ * 0.34 + 0.02), rn, 1.0, body=rn.u(0.22, 0.38)); f.wide = 0.0
        tgt = V3((c * rn.u(0.24, 0.3), rn.u(-0.2, 0.05), s_ * rn.u(0.2, 0.26) + 0.02))
        f.arm(1, tgt, ('claw', 'flat', 'claw', 'mitt', 'claw', 'flat', 'claw')[k], fingers=(-c * 0.5, 1, -s_ * 0.5), palm=(-c, 0.2 + 0.05 * k, -s_), pole=(c, 0.3, s_), hs=1.2 + 0.02 * k)
    for k in range(5):
        a = 0.9 + k * 1.26 + rn.u(-0.2, 0.2); bs.add(mound(0.1, 0.125, 0.11, 6), ch, ('tile', 0.3), T(math.cos(a) * 0.45, -0.52 + rn.u(-0.1, 0.05), math.sin(a) * 0.36) @ frame((math.cos(a), 0.8 + 0.1 * k, math.sin(a))), rn.u(0.3, 0.5))
    # --- nodes
    root = empty('inspector', None, INSP_AT); root.scale = (INSP_S,) * 3; N['inspector'] = root
    piv = {'insp_body': None, 'insp_base': None, 'insp_head': (0, 0.62, 0.0), 'insp_armR': tuple(SH[-1]), 'insp_armL': tuple(SH[1]), 'insp_foreR': tuple(EL[-1]), 'insp_foreL': tuple(EL[1]), 'insp_punch_lever': tuple(PR)}
    par = {'insp_foreR': 'insp_armR', 'insp_foreL': 'insp_armL', 'insp_punch_lever': 'insp_foreR'}
    for k in ('insp_body', 'insp_base', 'insp_head', 'insp_armR', 'insp_armL', 'insp_foreR', 'insp_foreL', 'insp_punch_lever'):
        o = B[k].obj(sharp=62, weld=2e-5); pv = piv[k]
        pp = N[par[k]] if k in par else root
        if pv is not None:
            p = gv(*pv); o.data.transform(Matrix.Translation(-p))
            base = V3(piv[par[k]]) if k in par else V3((0, 0, 0))
            o.location = gv(*(V3(pv) - base))
        o.name = k; o.data.name = k; o.parent = pp; N[k] = o
    INFO['insp'] = dict(crit=(0, 0.3, 0.16), rivet=tuple(PR), head=(0, HY, 0.0))
    return root


# ------------------------------------------------------------ the arms (rp_arm.glb): a segment, the wrist knot, the hand, a stump
SEG = 1.5
def rope_arm(b, rn, z0, a0, rad, twist, hand, tint, k=5):
    """one human arm laid along the rope's helix from z0: shoulder, elbow (kicked outward), wrist, a hand on the next"""
    def at(z, r, da=0.0): a = a0 + twist * z + da; return V3((math.cos(a) * r, math.sin(a) * r, z))
    p0 = at(z0, rad * 0.9); p1 = at(z0 + 0.34, rad + rn.u(0.04, 0.13), rn.u(-0.12, 0.12)); p2 = at(z0 + 0.64, rad * rn.u(0.92, 1.05), rn.u(-0.1, 0.1))
    b.add(limb_prim(p0, p1, p2, 0.066, 0.054, 0.04, k), M['char'], CHAR, None, tint, jit=0.006)
    fd = (at(z0 + 0.8, rad * 0.95) - p2).normalized(); out = V3((p2.x, p2.y, 0)).normalized()
    prim = {'mitt': lambda: hand_mitt(1, rn.u(0.2, 0.6)), 'flat': lambda: hand_flat(rn.u(0.8, 1.5), rn.sign()), 'claw': lambda: hand_claw(rn.sign(), rn.u(0.3, 0.7)), 'grip': lambda: hand_grip(1.0, rn.sign())}[hand]()
    b.add(prim, M['char'], ('tile', 0.3), frame(fd if hand != 'flat' else (fd + out * rn.u(0.2, 0.9)).normalized(), out, p2 - fd * 0.01) @ SC(1.35), min(1.0, tint * 1.8))


def build_arm():
    N = {}; root = empty('rp_arm'); ch, bi = M['char'], M['bits']
    # --- the segment: 8 arms round the outside, 4 inside, a quarter turn of braid per length, so it tiles along +z
    b = Buf('arm_seg'); rn = Rnd(88); TW = (math.pi / 2) / SEG
    b.add(p_tube([(0, 0, -0.02), (0, 0, SEG / 2), (0, 0, SEG + 0.02)], [0.13, 0.135, 0.13], 6), ch, CHAR, None, 0.14)     # the middle: packed tight, in the dark
    for i in range(8):
        for j in range(2):
            z0 = j * 0.75 + (i % 2) * 0.375 + rn.u(-0.09, 0.09)
            hand = ['mitt', 'grip', 'mitt', 'claw', 'mitt', 'flat', 'grip', 'mitt'][(i + j * 3) % 8]
            rope_arm(b, rn, z0, i * math.pi / 4 + rn.u(-0.12, 0.12), 0.2 * rn.u(0.9, 1.12), TW, hand, rn.u(0.28, 0.5))
    for i in range(4):
        for j in range(2):
            z0 = j * 0.75 + 0.19
            a0 = i * math.pi / 2 + math.pi / 8
            def at(z, r=0.105): a = a0 - TW * z * 2; return V3((math.cos(a) * r, math.sin(a) * r, z))
            b.add(p_tube([at(z0), at(z0 + 0.36, 0.13), at(z0 + 0.74)], [0.07, 0.062, 0.05], 5), ch, CHAR, None, rn.u(0.2, 0.34), jit=0.006)
    for k in range(3):  # a lanyard still on one of them, a cuff of shirt
        a = rn.u(0, 6.28); z = 0.25 + k * 0.5; p = V3((math.cos(a) * 0.27, math.sin(a) * 0.27, z)); out = V3((math.cos(a), math.sin(a), 0))
        Mc = frame(out, (0, 0, 1), p) @ RZ(rn.u(-0.6, 0.6))
        b.add(p_box(0.1, 0.14, 0.008), bi, AT['bits'].face('card%d' % k, 'z', 0.5), Mc, 0.8)
        b.add(p_tube([p + V3((0, 0, 0.07)), p - out * 0.1 + V3((0, 0, 0.16)), p - out * 0.22 + V3((0, 0, 0.1))], 0.012, 4, squash=0.3), bi, BF('strap', 1), None, LAN[k])
    N['arm_seg'] = b
    # --- the wrist knot: lanyards wound into a ball round the rope, ID cards hanging off it, lit from inside
    b = Buf('arm_knot'); rn = Rnd(89)
    V_, F_, UV_ = p_ellipsoid(0.3, 0.3, 0.3, 10, 6)
    b.add((V_, F_, UV_), M['knot'], ('tile', 0.5), RX(math.pi / 2), 1.0, jit=0.02, jf=3.0)
    for k in range(9):
        ax = V3((rn.u(-1, 1), rn.u(-1, 1), rn.u(-0.5, 0.5))).normalized(); Mr = frame(ax, (rn.u(-1, 1), rn.u(-1, 1), rn.u(-1, 1)))
        rr_ = rn.u(0.315, 0.37); off = rn.u(-0.12, 0.12); n_ = 10
        pts = [Mr @ V3((math.cos(2 * math.pi * j / n_) * rr_ * (1 + 0.05 * math.sin(j * 2.1 + k)), math.sin(2 * math.pi * j / n_) * rr_, off)) for j in range(n_)]
        rings_ = []
        for j in range(n_):
            p = pts[j]; tg = (pts[(j + 1) % n_] - pts[j - 1]).normalized(); out = (p - Mr @ V3((0, 0, off))).normalized(); sd_ = tg.cross(out)
            w = 0.045; t_ = 0.007
            rings_.append([p + sd_ * w + out * t_, p - sd_ * w + out * t_, p - sd_ * w - out * t_, p + sd_ * w - out * t_])
        V2 = [v for r_ in rings_ for v in r_]; F2 = []; U2 = []
        for j in range(n_):
            jj = (j + 1) % n_
            for q in range(4): F2.append((j * 4 + q, j * 4 + (q + 1) % 4, jj * 4 + (q + 1) % 4, jj * 4 + q)); U2.append([(q, j), (q + 1, j), (q + 1, j + 1), (q, j + 1)])
        c = LAN[k % 3]; s_ = rn.u(0.6, 1.0)
        b.add((V2, F2, U2), bi, BT('strap', 1), None, tuple(x * s_ for x in c), flip=True)
    for k in range(10):
        d_ = V3((rn.u(-1, 1), rn.u(-1, 1), rn.u(-0.6, 0.6))).normalized(); p = d_ * 0.36
        Mc = frame(d_ + V3((rn.u(-0.5, 0.5), rn.u(-0.5, 0.5), rn.u(-0.5, 0.5))), (0, -1, 0), p + d_ * 0.07 + V3((0, -0.05, 0)))
        b.add(p_box(0.115, 0.155, 0.01), bi, AT['bits'].face('card%d' % (k % 4), 'z', 0.5), Mc, rn.u(0.75, 1.0))
        b.add(p_tube([p * 0.6, p + d_ * 0.05, p + d_ * 0.085 + V3((0, -0.03, 0))], 0.014, 4, squash=0.3), bi, BF('strap', 1), None, LAN[k % 3])
    N['arm_knot'] = b
    # --- the stump: what is left on the arm when the wrist is shot through. the cut faces +z
    b = Buf('arm_stump'); rn = Rnd(90)
    R0 = [[V3((math.cos(2 * math.pi * j / 12) * r_ * (1 + 0.1 * math.sin(j * 1.9)), math.sin(2 * math.pi * j / 12) * r_ * (1 + 0.1 * math.cos(j * 2.3)), z)) for j in range(12)] for z, r_ in ((-0.3, 0.27), (-0.1, 0.29), (0.0, 0.26))]
    b.add(p_loft(R0), ch, CHAR, None, 0.3, jit=0.01)
    V_ = list(R0[-1]) + [V3((0, 0, 0.03))]
    b.add((V_, [(j, (j + 1) % 12, 12) for j in range(12)], [[(V_[i].x, V_[i].y) for i in (j, (j + 1) % 12, 12)] for j in range(12)]), bi, ('fn', lambda p: px_uv(AT['bits'].R['flesh'], AT['bits'].tex, 0.5 + p.x * 1.7, 0.5 + p.y * 1.7, 0.5)), None, 1.0)
    for k in range(7):  # bone ends, and flaps of skin round the edge
        a = rn.u(0, 6.28); r_ = rn.u(0.03, 0.19)
        b.add(xf(p_prism(5, 0.022, rn.u(0.04, 0.1), r1=0.016, dome=0.004), T(math.cos(a) * r_, math.sin(a) * r_, 0.0) @ RX(rn.u(-0.3, 0.3)) @ RY(rn.u(-0.3, 0.3))), bi, BT('white', 1), None, rn.u(0.7, 1.0))
    for k in range(8):
        a = k * 0.785 + rn.u(-0.2, 0.2); c, s_ = math.cos(a), math.sin(a); tg = V3((-s_, c, 0))
        p = V3((c * 0.225, s_ * 0.225, -0.05)); tip = p + V3((c * rn.u(0.03, 0.12), s_ * rn.u(0.03, 0.12), rn.u(0.14, 0.26)))
        b.add(([p + tg * 0.07, p - tg * 0.07, tip], [(0, 1, 2), (2, 1, 0)], [[(0, 0), (1, 0), (0.5, 1)]] * 2), ch, ('tile', 0.3), None, 0.4)
    N['arm_stump'] = b
    # --- the hand made of hands. wrist at the origin, fingers along +z, the palm faces -y, the thumb on +x
    palm = Buf('palm'); rn = Rnd(91)
    pr = [[V3((x * w, y_ + 0.05 * math.cos(x * 1.4), z)) for x in (-1, -0.5, 0, 0.5, 1)] for z, w, y_ in ((-0.05, 0.2, 0.0), (0.2, 0.33, 0.02), (0.5, 0.4, 0.03), (0.74, 0.4, 0.02))]
    top = [[p + V3((0, 0.1, 0)) for p in row] for row in pr]; bot = [[p + V3((0, -0.1, 0)) for p in row] for row in pr]
    edge = [bot[0][k] for k in range(5)] + [bot[k][4] for k in range(1, 4)] + [bot[3][k] for k in range(3, -1, -1)] + [bot[k][0] for k in range(2, 0, -1)]
    edge_t = [p + V3((0, 0.2, 0)) for p in edge]
    for pr_ in outward([p_grid(top), p_grid(bot), p_loft([edge, edge_t])]): palm.add(pr_, ch, CHAR, None, 0.2)
    for k in range(9):   # the people it is made of: arms laid across the back of it, hands gripping its edges, a face in the palm
        x = rn.u(-0.3, 0.3); z = rn.u(0.0, 0.6); f = Fig(palm, T(x, 0.1, z), rn, 1.0, body=rn.u(0.28, 0.45)); f.wide = 0.0
        tgt = V3((x + rn.u(-0.3, 0.3), 0.14, z + rn.u(0.2, 0.42)))
        f.arm(1, tgt, rn.pick(['mitt', 'grip', 'flat']), palm=(0, -1, 0), pole=(0, 1, 0), hs=1.3)
    for k in range(5):
        x = rn.u(-0.28, 0.28); z = rn.u(0.05, 0.6); f = Fig(palm, T(x, -0.1, z), rn, 1.0, body=rn.u(0.28, 0.45)); f.wide = 0.0
        f.arm(1, V3((x + rn.u(-0.25, 0.25), -0.15, z + rn.u(0.15, 0.4))), rn.pick(['claw', 'flat']), palm=(0, -1, 0), pole=(0, -1, 0), hs=1.3)
    f = Fig(palm, T(0.02, -0.06, 0.36) @ RX(math.pi / 2) @ RZ(0.3), rn, 1.0); f.head(at=(0, 0, 0.0), jaw=1.0, face=0, size=1.25)
    N['palm'] = palm
    FING = [('f0', (0.37, -0.02, 0.2), 1.0, 0.3), ('f1', (0.3, 0.0, 0.72), 0.26, 0.36), ('f2', (0.1, 0.02, 0.76), 0.08, 0.4), ('f3', (-0.1, 0.02, 0.76), -0.08, 0.38), ('f4', (-0.3, 0.0, 0.72), -0.26, 0.32)]
    HN = []
    for fi, (nm, base, splay, L) in enumerate(FING):
        for pi_, ph in enumerate('abc'):
            b = Buf('%s_%s' % (nm, ph)); r2 = Rnd(920 + fi * 10 + pi_); th = 0.075 - pi_ * 0.012
            # each joint of a finger is two people's arms, side by side; a knuckle of elbows; the last one ends in a hand
            for sd in (-1, 1):
                p0 = V3((sd * th * 0.8, r2.u(-0.01, 0.01), -0.03)); p1 = V3((sd * th * (1.0 + r2.u(0, 0.5)), r2.u(0.02, 0.07), L * 0.52)); p2 = V3((sd * th * 0.7, 0.0, L + 0.02))
                b.add(limb_prim(p0, p1, p2, 0.07 - pi_ * 0.008, 0.058 - pi_ * 0.006, 0.045 - pi_ * 0.004, 5), ch, CHAR, None, r2.u(0.26, 0.45), jit=0.006)
                if ph != 'c' and r2.chance(0.7): b.add(hand_mitt(sd, 0.5), ch, ('tile', 0.3), frame((sd * 0.25, -0.15 - 0.1 * sd, 1), (sd * 0.4, 1, 0.3), p2 - V3((0, -0.03 - 0.012 * sd, 0.06 + 0.02 * sd))) @ SC(1.2), r2.u(0.5, 0.8))
            b.add(mound(th * 1.5, 0.07, 0.06, 6), ch, CHAR, T(0, 0.03, 0.0) @ RX(-math.pi / 2), 0.3, jit=0.006)
            if ph == 'c':
                b.add(hand_flat(1.3, 1 if fi % 2 else -1), ch, ('tile', 0.3), T(0, 0.004, L - 0.02) @ RX(0.12) @ RZ(0.2 * (1 if fi % 2 else -1)) @ SC(1.9), r2.u(0.55, 0.8))    # the fingertip is a hand
            HN.append((nm, ph, b, base, splay, L))
    N['_fingers'] = HN
    # --- nodes
    out = {}
    for k in ('arm_seg', 'arm_knot', 'arm_stump'):
        o = N[k].obj(sharp=72, weld=2e-5); o.name = k; o.data.name = k; o.parent = root; out[k] = o
    hand = empty('arm_hand', root); out['arm_hand'] = hand
    o = N['palm'].obj(sharp=72, weld=2e-5); o.name = 'palm'; o.data.name = 'palm'; o.parent = hand; out['palm'] = o
    prev = {}
    for nm, ph, b, base, splay, L in HN:
        if ph == 'a':
            e = empty(nm, hand); set_game_matrix(e, T(*base) @ RY(splay)); out[nm] = e; par_ = e; loc = (0, 0, 0)
        else: par_ = prev[nm]; loc = (0, 0, prevL[nm])
        o = b.obj(sharp=72, weld=2e-5); o.name = '%s_%s' % (nm, ph); o.data.name = o.name; o.parent = par_; o.location = gv(*loc)
        prev[nm] = o; prevL[nm] = L; out[o.name] = o
    # (every piece sits on the file's origin: the game clones each and puts it where it wants)
    meta = dict(kind='story', id='rp_arm', seg=dict(node='arm_seg', len=SEG, axis=[0, 0, 1], r=0.3, twist_deg=90, note='tiles along +z; arms overhang the far end by up to 0.3 m'),
                knot=dict(node='arm_knot', r=0.42, glow='rp_knot_glow'), stump=dict(node='arm_stump', cut='+z', r=0.29),
                hand=dict(node='arm_hand', palm='-y', along='+z', thumb='f0', fingers=[dict(name=nm, base=r3(base), splay=splay, len=[L, L, L]) for nm, base, splay, L in FING], curl='rotation.x of f?_a / f?_b / f?_c, + closes; open = 0, grip about 0.9 each'))
    root['jf'] = json.dumps(meta)
    return root, out, meta


prevL = {}


# ------------------------------------------------------------ assembling
def node(o, name, pivot=None, parent=None, hide=False):
    """name a mesh (built in root space), put its origin at pivot (game), parent it"""
    o.name = name; o.data.name = name
    if pivot is not None:
        p = gv(*pivot); o.data.transform(Matrix.Translation(-p)); o.location = p
    if parent is not None: o.parent = parent
    if hide: o['jf_hidden'] = 1
    return o


def empty(name, parent=None, pos=None):
    e = _link(bpy.data.objects.new(name, None))
    if pos is not None: e.location = gv(*pos)
    if parent is not None: e.parent = parent
    return e


def anchor_bufs():
    """☺ CORP's work: six clean white clamps on the hoop's back edge, each with a cyan ratchet strap run back over the
    plug and sunk into it. Five let go in stage 3; the one near the top (anchor_hang) is what the face hangs off."""
    rest, hang = Buf('anchors'), Buf('anchor_hang'); tr = M['tr']; pos = {}
    for k, deg in enumerate((30, math.degrees(HANG_A), 150, 210, 270, 330)):
        a = math.radians(deg); c, s_ = math.cos(a), math.sin(a); b = hang if k == 1 else rest
        Mx = T(c * (HOOP_R + 0.052), s_ * (HOOP_R + 0.052), -0.42) @ RZ(a)     # local x = out of the hoop, y = round it, z = along the tunnel
        b.add(p_box(0.1, 0.3, 0.3), tr, TR('white', 1), Mx)
        b.add(p_box(0.104, 0.304, 0.07), tr, TR('cyan', 1), Mx @ T(0, 0, 0.09))
        b.add(p_box(0.012, 0.2, 0.09), tr, AT['tr'].face('hazard', 'x', 1), Mx @ T(0.052, 0, -0.07))
        b.add(xf(p_prism(6, 0.05, 0.05, r1=0.044, dome=0.012), RY(math.pi / 2)), tr, TR('chrome', 1), Mx @ T(0.05, 0, 0.09))          # the bolt
        b.add(xf(p_prism(6, 0.03, 0.2, top=False), RY(-math.pi / 2)), tr, TR('chain', 1), Mx @ T(0.02, 0, 0.09))                          # through the hoop
        # the strap: off the clamp, flat along the plug, then down into it; the ratchet half way
        rr_ = 4.578
        pts = [(HOOP_R + 0.06, -0.57), (rr_, -0.8), (rr_, -1.9), (rr_ - 0.02, -2.3), (4.3, -2.75)]
        for (r0, z0), (r1, z1) in zip(pts, pts[1:]):
            p0 = V3((c * r0, s_ * r0, z0)); p1 = V3((c * r1, s_ * r1, z1))
            b.add(p_box(0.1, 0.012, (p1 - p0).length), tr, AT['tr'].fit('strap', 1), frame(p1 - p0, (c, s_, 0), (p0 + p1) / 2), 0.9)
        b.add(p_box(0.13, 0.05, 0.2), tr, TR('steel', 1), frame((0, 0, 1), (c, s_, 0), (c * (rr_ + 0.0), s_ * (rr_ + 0.0), -1.3)), 0.9)
        b.add(p_box(0.03, 0.03, 0.16), tr, TR('yellow', 1), frame((0, 0.5, 1), (c, s_, 0), (c * (rr_ + 0.01), s_ * (rr_ + 0.01), -1.2)), 0.9)
        pos[k] = (c * HOOP_R, s_ * HOOP_R, -0.33)
    INFO['hang'] = pos[1]; INFO['anchors'] = [pos[k] for k in (0, 2, 3, 4, 5)]
    return rest, hang


def build_mask(N):
    mask = empty('mask'); N['mask'] = mask
    for k, o in sorted(build_plates().items()):
        N[k] = node(o, k, None, mask, hide=('_' in k[6:]))
    up, low = frame_bufs()
    N['frame'] = node(up.obj(sharp=35), 'frame', None, mask); N['frame_low'] = node(low.obj(sharp=35), 'frame_low', None, mask)
    INFO['hinge'] = {}
    for nm, sx, bl in (('eye_R', -1, False), ('eye_L', 1, False), ('eye_L_blown', 1, True)):
        b = eye_buf(nm, sx, bl)
        b.V = [v + V3((sx * EYE_C[0], EYE_C[1], 0)) for v in b.V]
        hg = (sx * (EYE_C[0] + EYE_A + 0.255), EYE_C[1], PT + 0.07); INFO['hinge'][nm] = hg
        N[nm] = node(b.obj(sharp=38), nm, hg, mask, hide=bl)
    sock, balls = eye_cluster_bufs()
    N['eye_cluster'] = node(sock.obj(sharp=44), 'eye_cluster', None, mask, hide=True)
    for eb, c in balls:
        eb.V = [v + V3(c) for v in eb.V]
        N[eb.name] = node(eb.obj(sharp=60), eb.name, c, N['eye_cluster'], hide=True)
    rest, hang = anchor_bufs()
    N['anchors'] = node(rest.obj(sharp=35), 'anchors', None, mask); N['anchor_hang'] = node(hang.obj(sharp=35), 'anchor_hang', None, mask)
    return mask


VIEWS = {  # name: (camera, target, lens or ('o', ortho scale))
    'front': ((0, 0, 40), (0, 0, 0), ('o', 15.6)), 'q': ((13, 3.2, 17), (0, -0.2, -1.5), 50), 'side': ((40, 0, -3.2), (0, 0, -3.2), ('o', 11.5)),
    'back': ((-9, 3, -24), (0, 0, -3), 50), 'eye': ((2.6, 1.2, 4.2), (1.25, 0.7, 0), 50), 'plate': ((-2.2, 2.4, 3.2), (-2.6, 2.9, 0.1), 50),
    'low': ((2.5, -2.0, 9.0), (0, -0.6, 0), 35), 'rim': ((5.6, 3.6, 3.0), (3.2, 2.9, -0.3), 50), 'hub': ((0.6, 0.4, 2.6), (0, 0, 0.1), 50),
    'mass6': ((0.8, -1.2, 6.0), (0.2, -0.4, -0.6), 40), 'insp': ((0.9, -1.75, 2.2), (0, -2.2, -0.75), 50), 'insp2': ((-1.6, -2.0, 1.2), (0, -2.2, -0.8), 50), 'behind': ((3, 1, -14), (0, 0, -4), 40),
}


def studio(key=9000, amb=0.6):
    world(0x1a1220, amb)
    area(key, (9, 9, 16), (0, 0, 0), 9.0, (1.0, 0.97, 0.92))
    area(key / 3, (-12, 2, 10), (0, 0, -1), 10.0, (0.8, 0.88, 1.0))
    area(key / 3.4, (-4, 10, -6), (0, 0, -3), 8.0, (1.0, 0.75, 0.9))
    area(key / 6, (0, -8, 8), (0, -1, -1), 8.0, (1.0, 0.9, 0.8))


STAGE1 = (9, 6, 11)          # the plates the fight drops first (any plate can go: this is the order the pictures use)
SPLIT = (2, 3, 8)            # stage 3 swaps these for their _up / _low halves (11 is split too, for a fight that kept it)
HANG_POSE = (-0.06, -0.2)    # how the pictures hang what is left: turned in its own plane, flapped forward (radians)


def set_stage(N, st, crazed=(), hang=True):
    """show the model as it is after break stage st (0 = whole). crazed = plates shown as their cracked twin"""
    def vis(k, on):
        if k in N: N[k].hide_render = not on
    for i in range(12):
        nm = 'plate_%02d' % i
        gone = (st >= 1 and i in STAGE1) or (st >= 3 and i in (9, 10, 11))
        halves = st >= 2 and i in SPLIT
        cz = i in crazed and not gone and not halves
        vis(nm, not gone and not halves and not cz); vis(nm + '_crazed', cz)
        vis(nm + '_up', halves); vis(nm + '_low', halves and st < 3)
    vis('frame_low', st < 3); vis('anchors', st < 3)
    vis('eye_L', st < 2); vis('eye_L_blown', st >= 2); vis('eye_cluster', st >= 2)
    for k in N:
        if k.startswith('eyeball_'): vis(k, st >= 2)
    vis('mass_lod', False)
    if 'mask' in N:
        P = V3(INFO['hang'])
        Mx = T(*P) @ RZ(HANG_POSE[0]) @ RX(HANG_POSE[1]) @ T(*(-P)) if (st >= 3 and hang) else Matrix.Identity(4)
        set_game_matrix(N['mask'], Mx)
    bpy.context.view_layer.update()


def preview(N, pdir, views, st=0, res=(960, 600), exposure=0.0):
    os.makedirs(pdir, exist_ok=True)
    colour_preview(list(M.values()))
    set_stage(N, st, crazed=(5, 10) if st in (1, 2) else ()); studio(); out = []
    for v in views:
        loc, tgt, lens = VIEWS[v]
        p = os.path.join(pdir, f'rp_{v}_s{st}.png')
        if isinstance(lens, tuple): shot(p, loc, tgt, res=res, ortho=lens[1], exposure=exposure, samples=int(arg('samples', 12)))
        else: shot(p, loc, tgt, lens, res=res, exposure=exposure, samples=int(arg('samples', 12)))
        out.append(p)
    clear_studio(); set_stage(N, 0)
    print('JF_PREVIEW', ' '.join(out))


# ------------------------------------------------------------ finishing: AO, the parts file, export
def flat_ao(o, v=1.0):
    me = o.data
    if 'AO' in me.color_attributes: me.color_attributes.remove(me.color_attributes['AO'])
    ca = me.color_attributes.new('AO', 'BYTE_COLOR', 'CORNER'); ca.data.foreach_set('color', [v, v, v, 1.0] * len(me.loops))


def bake_all(N, A):
    """ambient occlusion per group, each seeing only what is really next to it"""
    meshes = {k: o for k, o in N.items() if o.type == 'MESH'}
    for o in meshes.values(): o.hide_render = False
    for o in A.values():
        if o.type == 'MESH': o.hide_render = True
    hid = [k for k, o in meshes.items() if o.get('jf_hidden')]
    for k in hid: meshes[k].hide_render = True
    G = lambda pre: [o for k, o in meshes.items() if k.startswith(pre) and k not in hid]
    mask_all = G('plate_') + G('frame') + G('eye_') + G('anchor')
    if 'mass_ne' in N:
        for o in mask_all: o.hide_render = True
        bake_ao(G('mass_') + G('insp_'), dist=0.45, lo=0.3, gain=1.15)
        for o in mask_all: o.hide_render = False
    if 'frame' in N:
        others = G('mass_') + G('insp_')
        for o in others: o.hide_render = True
        bake_ao(G('frame') + G('eye_') + G('anchor'), dist=0.35, lo=0.42, also=G('plate_'))
        bake_ao(G('plate_'), dist=0.25, lo=0.5, also=G('frame') + G('eye_'))
        for o in others: o.hide_render = False
    for k in hid:  # the damage pieces: each alone (it is shown when its neighbours may be gone)
        o = meshes[k]
        if k.startswith('eyeball'): flat_ao(o); continue
        for q in meshes.values(): q.hide_render = True
        o.hide_render = False; bake_ao([o], dist=0.2, lo=0.55)
    for o in meshes.values(): o.hide_render = False
    for k, o in A.items():
        if o.type != 'MESH': continue
        for q in list(meshes.values()) + [x for x in A.values() if x.type == 'MESH']: q.hide_render = True
        o.hide_render = False; bake_ao([o], dist=0.3, lo=0.3, gain=1.15)
    for q in list(meshes.values()) + [x for x in A.values() if x.type == 'MESH']: q.hide_render = False


def stage_of(k):
    """(the break stage that takes this part away, the stage it first shows at, what it stands in for)"""
    if k.startswith('plate_'):
        i = int(k[6:8]); suf = k[9:]
        if suf == 'crazed': return 0, None, k[:8]
        if suf == 'low': return 3, 2, k[:8]
        if suf == 'up': return 0, 2, k[:8]
        if i in STAGE1: return 1, None, None
        if i in SPLIT: return 2, None, None       # swapped for its halves when the smile crack runs
        return (3 if i == 10 else 0), None, None
    if k in ('frame_low', 'anchors'): return 3, None, None
    if k == 'eye_L': return 2, None, None
    if k in ('eye_L_blown', 'eye_cluster') or k.startswith('eyeball_'): return 0, 2, ('eye_L' if k == 'eye_L_blown' else None)
    return 0, None, None


def parts_json(N, A, arm_meta, tris):
    parts = []
    bpy.context.view_layer.update()
    for k in sorted(N):
        o = N[k]
        if o.type != 'MESH': continue
        lo, hi = bounds([o]); st, frm, of = stage_of(k)
        d = dict(name=k, centre=r3((lo + hi) / 2), half=r3((hi - lo) / 2), stage=st, group=o.parent.name if o.parent else None, tris=tri_count(o))
        if o.get('jf_hidden'): d['hidden'] = True
        if frm is not None: d['shown_from'] = frm
        if of: d['instead_of'] = of
        if o.location.length > 1e-6 and k != 'inspector': d['pivot'] = r3(g_of(o.matrix_world.translation))
        parts.append(d)
    ia = V3(INSP_AT); ii = INFO.get('insp', {})
    wp = lambda q: r3(ia + V3(q) * INSP_S)
    crack = [[round(x, 3), round(crack_y(x), 3)] for x in [(-4.33 + 8.66 * k / 24) for k in range(25)]]
    meta = dict(
        id=FID, name='REVENUE PROTECTION', units='metres, root space: x right, y up, +z toward the train (the mask faces +z)',
        note='L is the mask\'s own left = +x. boxes are axis-aligned, of the part as built (whole, nothing swung or dropped)',
        tunnel=dict(bore_r=R_BORE, floor_y=FLOOR_Y, mask_r=RM, hoop_r=HOOP_R, mass_r=MASS_R, mass_z=[MASS_Z0, -7.65]),
        tris=tris,
        stages={'1': dict(name='HAIRLINE', drops=['plate_%02d' % i for i in STAGE1], note='any plate may be crazed (swap to plate_NN_crazed) and then dropped; these three are the order the sheets use'),
                '2': dict(name='THE LEFT EYE', hide=['eye_L'], show=['eye_L_blown', 'eye_cluster'], crack=dict(hide=['plate_%02d' % i for i in SPLIT], show=['plate_%02d_%s' % (i, h) for i in SPLIT for h in ('up', 'low')]),
                          note='plate_11 is split too (plate_11_up / _low) for a fight that still has it'),
                '3': dict(name='THE SMILE', drops=['plate_%02d_low' % i for i in SPLIT] + ['plate_10', 'frame_low', 'anchors'], hang=dict(node='mask', pivot=r3(INFO['hang']), sheet_pose=dict(rz=HANG_POSE[0], rx=HANG_POSE[1])))},
        markers=dict(
            eye_L=dict(centre=[EYE_C[0], EYE_C[1], PT], half=[EYE_A, EYE_B], hinge=r3(INFO['hinge']['eye_L']), hinge_axis=[0, 1, 0], node='eye_L', depth=0.62),
            eye_R=dict(centre=[-EYE_C[0], EYE_C[1], PT], half=[EYE_A, EYE_B], hinge=r3(INFO['hinge']['eye_R']), hinge_axis=[0, 1, 0], node='eye_R', depth=0.62),
            inspector=dict(node='inspector', at=r3(ia), scale=INSP_S, crit=wp(ii.get('crit', (0, 0, 0))), crit_r=0.2, head=wp(ii.get('head', (0, 0, 0))), punch=wp(ii.get('rivet', (0, 0, 0))),
                           joints=dict(insp_head='turn about y / x', insp_armR='shoulder', insp_foreR='elbow', insp_punch_lever='about its local x: + closes the punch (0.3 rad shut)')),
            hang_bolt=r3(INFO['hang']), anchors=[r3(q) for q in INFO['anchors']],
            hub=[0, 0, PT + 0.09], smile_crack=crack, plate_face_z=PT, glass_z=GLASS_Z,
            sockets=[dict(deg=d, pos=r3((4.5 * math.cos(math.radians(d)), 4.5 * math.sin(math.radians(d)), -0.5)), dir=[0, 0, 1], out=r3((math.cos(math.radians(d)), math.sin(math.radians(d)), 0))) for d in SOCKETS],
            mouth_sockets=[dict(pos=[x, round(crack_y(x) - 0.75, 3), -0.7], dir=[0, 0, 1]) for x in (-2.6, -1.5, 1.5, 2.6)]),
        materials=dict(rp_inspector_glow='his light (emissive: flare it on a crit)', rp_eye_glow='the eyes behind the blown housing (emissive)', rp_knot_glow='the wrist knot (rp_arm.glb, emissive)',
                       rp_enamel='the face', rp_enamel_crazed='the cracked face', rp_void='inside the lamp cans (no specular: the eyes stay black)', rp_steel='lattice, hoop, housings, clamps', rp_char='burnt skin (tiles)', rp_pack='the wall of the plug: packed commuters (tiles)', rp_bits='faces, lanyards, cards, clothes', rp_mass_lod='the far plug: the near one photographed onto it'),
        lod=dict(node='mass_lod', instead_of=list(Mass.NAMES), note='hidden. swap it in past about 40 m, or while every plate is still on; it has the near model photographed onto its face (the inspector too: hide him with it)'),
        arm=arm_meta, parts=parts)
    return meta


def finish_all(N, A, arm):
    for k, o in list(N.items()) + list(A.items()):
        if o.type == 'MESH': o.data.validate(); o.data.update()
    bpy.context.view_layer.update()
    if not arg('no-ao'): bake_all(N, A)
    for o in list(N.values()) + list(A.values()):
        if o.type == 'MESH': final_colour(o)
    vis = sum(tri_count(o) for k, o in N.items() if o.type == 'MESH' and not o.get('jf_hidden'))   # (the lod is built after this)
    hid = sum(tri_count(o) for k, o in N.items() if o.type == 'MESH' and o.get('jf_hidden'))
    grp = lambda pre: sum(tri_count(o) for k, o in N.items() if o.type == 'MESH' and not o.get('jf_hidden') and k.startswith(pre))
    tris = dict(whole=vis, hidden_variants=hid, mask=grp('plate_') + grp('frame') + grp('eye_') + grp('anchor'), mass=grp('mass_'), inspector=grp('insp_'),
                arm={k: tri_count(o) for k, o in A.items() if o.type == 'MESH' and k[0] != 'f' and k != 'palm'})
    tris['arm']['arm_hand'] = sum(tri_count(o) for k, o in A.items() if o.type == 'MESH' and (k[0] == 'f' or k == 'palm'))
    print('JF_TRIS', json.dumps(tris))
    return tris


def build_mass_lod(N, A):
    """the plug as one cheap mesh for far away (and for while the mask still hides it): the near model's face is
    photographed straight on into a 256 px map, the wall is plain char"""
    tmp = os.path.join(SHEETS, '_tmp'); os.makedirs(tmp, exist_ok=True)
    colour_preview(list(M.values()))
    keep = ('mass_ne', 'mass_nw', 'mass_sw', 'mass_se')
    for k, o in list(N.items()) + list(A.items()): o.hide_render = not (k in keep or k.startswith('insp_'))
    world(0xffffff, 1.0)
    p = shot(os.path.join(tmp, 'lod_face.png'), (0, 0, 30), (0, 0, -1), res=(256, 256), ortho=2 * R_BORE, exposure=0.0, samples=8)
    img = bpy.data.images.load(p); img.pack(); img.name = 'rp_mass_lod_t'
    colour_preview(list(M.values()), on=False)
    for k, o in list(N.items()) + list(A.items()): o.hide_render = False
    M['lod'] = mat('rp_mass_lod', 0xffffff, rough=0.6, tex=img)
    b = Buf('mass_lod'); NA = 24; RS = [0.0, 0.8, 1.6, 2.4, 3.2, 3.9, 4.45]; ZW = [MASS_Z0 - 0.12, -2.2, -3.8, -5.4, MASS_Z1]; BK = [(3.75, -7.0), (2.6, -7.4)]
    rows = []
    for k in range(NA + 1):
        a = 2 * math.pi * k / NA; c, s_ = math.cos(a), math.sin(a)
        row = [V3((r_ * c, r_ * s_, (core_z(r_ * c, r_ * s_) if r_ else core_z(0, 0)) + 0.14)) for r_ in RS]
        row += [V3((wall_r(a, z) * c, wall_r(a, z) * s_, z)) for z in ZW] + [V3((r_ * c, r_ * s_, z)) for r_, z in BK] + [V3((0, 0, -7.6))]
        rows.append(row)
    nf = len(RS)
    front = outward([p_grid([row[:nf] for row in rows]), p_grid([row[nf - 1:] for row in rows])])
    b.add(front[0], M['lod'], ('fn', lambda q: (0.5 + q.x / (2 * R_BORE), 0.5 + q.y / (2 * R_BORE))))
    b.add(front[1], M['pack'], ('fn', lambda q: ((math.atan2(q.y, q.x) % (2 * math.pi)) * 4.5 / 4.2, q.z / 4.2)), None, 0.8)
    o = b.obj(sharp=72, weld=1e-4); flat_ao(o); final_colour(o)
    N['mass_lod'] = node(o, 'mass_lod', None, N['mass'], hide=True)
    try: os.remove(p)
    except OSError: pass
    print('JF_LOD mass_lod', tri_count(o), 'tris')
    return o


TUNNEL = []
def tunnel_set(on=True, ring_z=0.9, man=True, floor=True):
    """the pictures' scale: a ring the size of the bore, the track bed, a 1.8 m figure"""
    for o in TUNNEL:
        try: bpy.data.objects.remove(o, do_unlink=True)
        except ReferenceError: pass
    TUNNEL.clear()
    if not on: return
    m = mat('jf_set_ring', 0xff4fd8, rough=0.6, emit=0xff4fd8, strength=0.6); m2 = mat('jf_set_floor', 0x2a2228, rough=0.9); m3 = mat('jf_set_man', 0x4fd8ff, rough=0.6, emit=0x4fd8ff, strength=0.25)
    b = Buf('jf_set_ring'); k = 64
    R = [[V3((math.cos(2 * math.pi * j / k) * r_, math.sin(2 * math.pi * j / k) * r_, ring_z + z)) for j in range(k)] for r_, z in ((R_BORE, -0.06), (R_BORE + 0.12, -0.06), (R_BORE + 0.12, 0.06), (R_BORE, 0.06), (R_BORE, -0.06))]
    b.add(p_loft(R), m, ('tile', 1.0)); TUNNEL.append(b.obj())
    if floor:
        b = Buf('jf_set_floor'); hw = math.sqrt(R_BORE ** 2 - FLOOR_Y ** 2)
        b.add(p_box(hw * 2, 0.08, 9.0), m2, ('tile', 1.0), T(0, FLOOR_Y - 0.04, 5.2)); TUNNEL.append(b.obj())
    if man:
        b = Buf('jf_set_man'); Mx = T(2.3, FLOOR_Y, 3.4)
        for sz, at_ in (((0.2, 0.84, 0.2), (-0.12, 0.42, 0)), ((0.2, 0.84, 0.2), (0.12, 0.42, 0)), ((0.5, 0.62, 0.26), (0, 1.15, 0)), ((0.14, 0.62, 0.16), (-0.33, 1.15, 0)), ((0.14, 0.62, 0.16), (0.33, 1.15, 0)), ((0.24, 0.28, 0.24), (0, 1.66, 0))):
            b.add(xf(p_box(sz[0], sz[2], sz[1]), RX(-math.pi / 2)), m3, ('tile', 1.0), Mx @ T(*at_))
        TUNNEL.append(b.obj())
    for o in TUNNEL: flat_ao(o); final_colour(o)


def sheets(N, A, tris):
    colour_preview(list(M.values()))
    tmp = os.path.join(SHEETS, '_tmp'); os.makedirs(tmp, exist_ok=True)
    arm_objs = [o for o in A.values()]
    def arms(on):
        for o in arm_objs: o.hide_render = not on
    def boss(on):
        for o in N.values(): o.hide_render = not on
    S = int(arg('samples', 16))
    # (a) the whole thing in a ring the size of the bore, a 1.8 m figure on the track bed
    arms(False); set_stage(N, 0); tunnel_set(True); studio(9000, 0.6); out = []
    for nm, loc, tgt, lens in (('front', (0, 0, 40), (0, 0, 0), ('o', 10.6)), ('three-quarter', (15, 4.2, 15.5), (0, -0.2, -2.2), 50), ('side', (40, 0, -1.6), (0, 0, -1.6), ('o', 13.4)), ('back', (-10, 3.5, -24.5), (0, 0, -3.5), 50)):
        p = os.path.join(tmp, f'ta_{nm}.png'); out.append(p)
        if isinstance(lens, tuple): shot(p, loc, tgt, res=(760, 760), ortho=lens[1], exposure=-1.0, samples=S)
        else: shot(p, loc, tgt, lens, res=(760, 760), exposure=-1.0, samples=S)
    contact(out, os.path.join(SHEETS, 'rp_turnaround'), f'REVENUE PROTECTION  {tris["whole"]} TRIS  MASK {tris["mask"]}  MASS {tris["mass"]}  INSPECTOR {tris["inspector"]}  RING = THE 9.2 M BORE  FIGURE = 1.8 M', cols=4, labels=['front', 'three-quarter', 'side (the plug is 7 m deep)', 'back'])
    # (b) the three break stages, front on
    out = []
    for st in (1, 2, 3):
        set_stage(N, st, crazed=(5, 10) if st == 1 else (5,) if st == 2 else ())
        p = os.path.join(tmp, f'st_{st}.png'); out.append(p)
        shot(p, (0, 0, 40), (0, 0, 0), res=(760, 760), ortho=10.6, exposure=-0.7, samples=S)
    set_stage(N, 0)
    contact(out, os.path.join(SHEETS, 'rp_stages'), 'REVENUE PROTECTION  THE MASK BREAKS', cols=3, labels=['1 HAIRLINE: plates craze and fall (05 10 crazed here)', '2 THE LEFT EYE: blown, real eyes; the smile is a crack', '3 THE SMILE: the lower third gone, it hangs off one clamp'])
    tunnel_set(False); clear_studio()
    # (c) close-ups
    out = []; lab = []
    studio(7000, 0.6)
    def cu(nm, loc, tgt, lens=50, ex=-0.8, st=None, cz=(), label=None):
        if st is not None: set_stage(N, st, crazed=cz)
        p = os.path.join(tmp, f'cu_{nm}.png'); out.append(p); lab.append(label or nm)
        shot(p, loc, tgt, lens, res=(760, 560), exposure=ex, samples=S)
    cu('enamel', (-1.9, 2.3, 3.0), (-2.5, 2.8, 0.1), 50, -1.1, st=0, label='enamel, bolts, the hoop')
    cu('crazed', (3.3, 2.2, 3.4), (2.6, 2.5, 0.1), 50, -1.1, st=1, cz=(5, 4), label='a crazed plate (04) by a whole one')
    cu('eye_blown', (2.5, 1.0, 3.6), (1.3, 0.75, 0), 50, -0.6, st=2, label='the left eye, blown')
    for k, o in N.items():
        if k.startswith(('plate_', 'frame', 'eye', 'anchor')) and o.type == 'MESH': o.hide_render = True
    cu('mass6', (0.9, -1.2, 5.6), (0.3, -0.9, -0.8), 38, 0.5, label='the 17:32 from 6 m (mask off)')
    cu('inspector', (0.85, -1.85, 1.3), (0.0, -2.2, -0.8), 50, 0.4, label='the inspector')
    if 'mass_lod' in N:
        for k, o in N.items(): o.hide_render = k != 'mass_lod'
        cu('lod', (9, 2.5, 13), (0, -0.2, -2.5), 50, 0.5, label='mass lod (%d tris), mask off' % tri_count(N['mass_lod']))
    set_stage(N, 0); boss(False); arms(True); clear_studio()
    # the arm kit: the hand open and gripping, eight lengths along a curve with the knot and the hand
    for k in ('arm_seg', 'arm_knot', 'arm_stump'): A[k].hide_render = True
    hand = A['arm_hand']; hand.location = (0, 0, 0)
    world(0x1a1220, 0.6); area(700, (2.5, 3.0, 2.5), (0, 0, 0.7), 4.0); area(260, (-3, -1, 1.5), (0, 0, 0.7), 4.0, (0.8, 0.88, 1.0)); area(200, (0, -3, -1.5), (0, 0, 0.7), 3.0, (1.0, 0.8, 0.9))
    def curl(v):
        for k, o in A.items():
            if len(k) == 4 and k[0] == 'f' and k[2] == '_': o.rotation_euler = Euler((v * (0.75 if k[1] == '0' else 1.0), 0, 0), 'XYZ')
    for nm, v in (('hand_open', 0.08), ('hand_grip', 0.95)):
        curl(v); bpy.context.view_layer.update()
        p = os.path.join(tmp, f'cu_{nm}.png'); out.append(p); lab.append(nm.replace('_', ' ') + ' (palm side)')
        shot(p, (1.9, -2.5, 2.6), (0.0, -0.15, 0.85), 50, res=(760, 560), exposure=0.5, samples=S)
    curl(0.55)
    clear_studio()
    seg = A['arm_seg']; seg.hide_render = False; A['arm_knot'].hide_render = False
    pts = [V3((0, 0, 0))]; d = V3((0, 0.05, 1)).normalized(); copies = []
    for k in range(8):
        d = (RX(-0.12 if k < 4 else 0.16) @ RY(0.1)) @ d.to_4d(); d = V3(d[:3]).normalized()
        pts.append(pts[-1] + d * SEG)
    for k in range(8):
        o = seg if k == 0 else seg.copy()
        if k: _link(o); o.name = 'jf_set_seg%d' % k; copies.append(o)
        o.parent = None; set_game_matrix(o, frame(pts[k + 1] - pts[k], (0, 1, 0), pts[k]) @ RZ(k * 0.0))
    A['arm_knot'].parent = None; set_game_matrix(A['arm_knot'], frame(pts[8] - pts[7], (0, 1, 0), pts[8]))
    hand.parent = None; set_game_matrix(hand, frame(pts[8] - pts[7], (0, 1, 0), pts[8] + (pts[8] - pts[7]).normalized() * 0.3))
    mid = pts[4]
    world(0x1a1220, 0.6); area(6000, (9, 9, 9), tuple(mid), 9.0); area(2200, (-9, 3, 2), tuple(mid), 9.0, (0.8, 0.88, 1.0)); area(1500, (0, -6, 12), tuple(mid), 6.0, (1.0, 0.8, 0.9))
    p = os.path.join(tmp, 'cu_arm.png'); out.append(p); lab.append('8 lengths, the knot, the hand (12 m)')
    shot(p, (17.5, 4.5, 6.5), tuple(pts[5] + V3((0, -0.2, 0.9))), 36, res=(760, 560), exposure=0.3, samples=S)
    contact(out, os.path.join(SHEETS, 'rp_closeups'), 'REVENUE PROTECTION  CLOSE-UPS', cols=3, labels=lab)
    clear_studio()   # (takes the copies with it: they are named jf_set*)
    try: os.rmdir(tmp)
    except OSError: pass


def main():
    lib.reset(); lib._mats.clear()
    materials()
    N = {}; A = {}; arm_meta = {}
    root = empty(FID)
    if want('mask'): build_mask(N).parent = root
    if want('mass'): build_mass(N).parent = root
    if want('inspector'): build_inspector(N).parent = root
    if want('arm'): aroot, A, arm_meta = build_arm()
    bpy.context.view_layer.update()
    tris = finish_all(N, A, arm_meta)
    if 'mass_ne' in N and not arg('no-lod'): build_mass_lod(N, A); tris['mass_lod'] = tri_count(N['mass_lod'])
    if arg('stats'):
        for k, o in sorted(N.items()) + sorted(A.items()):
            if o.type == 'MESH': print('JF_PART', k, tri_count(o), [m.name for m in o.data.materials])
    full = ONLY is None
    if full or arg('json'):
        meta = parts_json(N, A, arm_meta, tris)
        small = {k: v for k, v in meta.items() if k not in ('parts',)}; small['parts_file'] = FID + '.parts.json'; small['kind'] = 'story'
        small['hidden'] = sorted(k for k, o in N.items() if o.type == 'MESH' and o.get('jf_hidden'))
        root['jf'] = json.dumps(small)
        if not arg('no-export'):
            os.makedirs(OUT, exist_ok=True)
            with open(os.path.join(OUT, FID + '.parts.json'), 'w') as f: json.dump(meta, f, separators=(',', ':'))
            print('JF_JSON', os.path.join(OUT, FID + '.parts.json'), len(meta['parts']), 'parts')
    if arg('qa'): run_qa(N, A)
    if not arg('no-export') and full:
        compact_glb(export_glb(root, os.path.join(OUT, FID + '.glb')))
        if A: compact_glb(export_glb(aroot, os.path.join(OUT, 'rp_arm.glb')))
    pdir = arg('preview')
    if isinstance(pdir, str):
        for o in A.values(): o.hide_render = True
        preview(N, pdir, arg('views', 'front,q').split(','), int(arg('stage', 0)), res=tuple(int(x) for x in arg('res', '960x600').split('x')), exposure=float(arg('exposure', 0)))
        return
    if not arg('no-sheet') and full: sheets(N, A, tris)


def run_qa(N, A):
    G = lambda pre, hidden=False: [o for k, o in N.items() if o.type == 'MESH' and k.startswith(pre) and bool(o.get('jf_hidden')) == hidden]
    res = {}
    if 'frame' in N: res['mask'] = qa('mask', G('plate_') + G('frame') + G('eye_') + G('anchor'), quiet=True)
    if 'mass_ne' in N: res['mass'] = qa('mass', G('mass_') + G('insp_'), tol=0.01, quiet=True)
    for o in G('plate_', True) + G('eye_', True): res[o.name] = qa(o.name, [o] + ([q for k, q in N.items() if k.startswith('eyeball')] if o.name == 'eye_cluster' else []), tol=0.03 if 'crazed' in o.name else 0.004, quiet=True)
    for k in ('arm_seg', 'arm_knot', 'arm_stump'):
        if k in A: res[k] = qa(k, [A[k]], tol=0.01, quiet=True)
    if 'palm' in A: res['arm_hand'] = qa('arm_hand', [o for k, o in A.items() if o.type == 'MESH' and (k == 'palm' or k[0] == 'f')], tol=0.02, quiet=True)
    print('QA_SUMMARY', {k: v.get('pass') for k, v in res.items()})
    return res


main()
