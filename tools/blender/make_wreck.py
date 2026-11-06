# Wrecking Ball killstreak (wreck.js buildWreckBall): you roll around inside a 2.2 m riveted steel demolition ball.
# Real references: riveted boiler / tank plate (butt straps, two rows of snap-head rivets), a bathysphere's bolted
# viewport, a forged pad eye with a master ring, long-link lifting chain. Origin = the ball's centre, radius exactly
# 1.1 (physics + the outline sphere). The shell: four pressed gores, the seams covered by riveted butt straps that cross
# under the chain stub and again underneath, a raised hoop round the equator (latitude +-0.17) in `wb_accent` (the
# game paints it your colour), rivets along the hoop, a few dents from past jobs, scuffed gunmetal paint with chips and
# rust. The chain stub on top: a cast boss with eight bolts and a weld bead, a hazard-yellow pad eye stencilled LIFT
# HERE, the master ring through it, two links up to the hook (meta hook = where the chain leaves the top link).
# The viewing slot: node `slot` (origin on the shell at latitude 0.42 at the front, rotation x 0.42: its -z points out),
# a bolted cast frame 0.76 x 0.29 x 0.18 round a 0.62 x 0.17 opening (kept clear: the game puts your face in it) under a
# little rain hood. Node `link`: one chain link (the game instances it for the whole chain), parked beside the ball.
# The gag: a BABY ON BOARD sign suction-cupped to the back (you're the baby).
# run: blender -b --python tools/blender/make_wreck.py   (-- --no-sheet, -- --qa = the blender-asset-qa gate)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link
import lib

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
V3 = Vector
R = 1.1
LAT_SLOT = 0.42
BAND = 0.17
LINK_W, LINK_L, WIRE = 0.26, 0.39, 0.042  # centreline width, centreline length (along y), wire radius


def sph(lat, az, r=R):
    """a point on a sphere round the centre: az 0 = +x, az 90 deg = +z (the back), az -90 = -z (the front, the slot)"""
    return V3((r * math.cos(lat) * math.cos(az), r * math.sin(lat), r * math.cos(lat) * math.sin(az)))


def G2B(q):  # a game-axes rotation matrix (3x3) -> blender 4x4
    Gm = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
    return (Gm @ q @ Gm.inverted()).to_4x4()


def frame_at(n):
    """an orthonormal frame with z along n (game axes): (x, y, z) columns as a 3x3"""
    n = V3(n).normalized()
    a = V3((0, 1, 0)) if abs(n.y) < 0.95 else V3((1, 0, 0))
    x = a.cross(n).normalized(); y = n.cross(x)
    return Matrix((x, y, n)).transposed()


def weld(o, dist=1e-6):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data); bm.free()
    return o


def uv_unzero(o, eps=2e-3):
    me = o.data
    if not me.uv_layers: return o
    uv = me.uv_layers.active.data
    for p in me.polygons:
        pts = [uv[li].uv.copy() for li in p.loop_indices]
        a2 = sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))
        if abs(a2) < 1e-9:
            for k, li in enumerate(p.loop_indices):
                a = 2 * math.pi * k / len(pts)
                uv[li].uv = (pts[0].x + eps * math.cos(a), pts[0].y + eps * math.sin(a))
    return o


# ------------------------------------------------------------ textures
def tnoise(size, cells, rng):
    lat = rng.random((cells, cells))
    t = np.arange(size) * cells / size
    i0 = np.floor(t).astype(int) % cells; i1 = (i0 + 1) % cells
    f = t - np.floor(t); f = f * f * (3 - 2 * f)
    a = lat[i0][:, i0] * (1 - f)[None, :] + lat[i0][:, i1] * f[None, :]
    b = lat[i1][:, i0] * (1 - f)[None, :] + lat[i1][:, i1] * f[None, :]
    return a * (1 - f)[:, None] + b * f[:, None]


def steel_px(base, seed, rust=0.5, chips=1.0):
    """scuffed painted steel (tiles): mottled paint, scratches, chipped spots showing bright metal, rust blooms"""
    def draw(px):
        h, w = px.shape[:2]
        r = np.random.default_rng(seed)
        n = 0.5 * tnoise(w, 4, r) + 0.3 * tnoise(w, 8, r) + 0.2 * tnoise(w, 16, r)
        px[:] = hexrgb(base)[None, None] * (0.8 + 0.3 * n[:, :, None])
        for k in range(int(4 * chips)):  # scratches
            x0, y0 = r.random() * w, r.random() * h
            a = r.random() * math.pi; L = r.uniform(4, 14)
            for ox in (-w, 0, w):
                for oy in (-h, 0, h):
                    px_line(px, x0 + ox, y0 + oy, x0 + ox + math.cos(a) * L, y0 + oy + math.sin(a) * L, 0xa8b0ba if k % 3 else 0x2e343c, 1.0)
        for k in range(int(3 * chips)):  # paint chips: bright steel with a dark rim
            cx, cy, rr = r.random() * w, r.random() * h, r.uniform(0.8, 2.0)
            px_disc(px, cx, cy, rr + 0.9, 0x2a2e34); px_disc(px, cx, cy, rr, 0xc4ccd4)
        if rust:
            m = np.clip((0.6 * tnoise(w, 5, r) + 0.4 * tnoise(w, 10, r) - (0.84 - 0.12 * rust)) / 0.1, 0, 1)[:, :, None]
            px[:] = px * (1 - 0.7 * m) + hexrgb(0x7a4428)[None, None] * 0.7 * m
            px[(r.random((h, w)) < 0.006 * rust)] = hexrgb(0x9a5a30)
    return draw


def lug_px(px):
    """hazard-yellow paint over the pad eye, worn through to steel on the edges"""
    h, w = px.shape[:2]
    r = np.random.default_rng(31)
    px[:] = hexrgb(0xffc21a) * (0.92 + 0.1 * r.random((h, w, 1)))
    m = r.random((h, w)) < 0.05
    px[m] = hexrgb(0x6a6e74)


def sign_px(px):
    """the BABY ON BOARD diamond: yellow, a black border, bold black letters"""
    h, w = px.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.abs(xx + 0.5 - w / 2) / (w / 2) + np.abs(yy + 0.5 - h / 2) / (h / 2)
    px[:] = hexrgb(0xffd21a)
    px[(d > 0.87) & (d <= 0.94)] = hexrgb(0x141414)
    for dx in (0, 1):
        text_px(px, 'BABY', (w - 23) // 2 + dx, 19, 1, 0x141414)
        text_px(px, 'ON', (w - 11) // 2 + dx, 28, 1, 0x141414)
        text_px(px, 'BOARD', (w - 29) // 2 + dx, 37, 1, 0x141414)


def stencil_mat(name, text, color=0x141414):
    w = len(text) * 6 + 1
    img = bpy.data.images.new(name + '_t', w, 9, alpha=True)
    px = np.zeros((9, w, 4), dtype=np.float32)
    rgb = np.zeros((9, w, 3), dtype=np.float32)
    text_px(rgb, text, 1, 1, 1, 0xffffff)
    r = np.random.default_rng(4)
    mask = (rgb.sum(axis=2) > 0) & (r.random((9, w)) > 0.08)  # spray-painted: a few dropouts
    px[:, :, :3] = hexrgb(color); px[:, :, 3] = mask.astype(np.float32)
    img.pixels.foreach_set(px[::-1].ravel()); img.file_format = 'PNG'; img.pack()
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.6
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; t.interpolation = 'Closest'
    nt.links.new(t.outputs['Color'], b.inputs['Base Color']); nt.links.new(t.outputs['Alpha'], b.inputs['Alpha'])
    m.blend_method = 'CLIP'; m.alpha_threshold = 0.5; m.shadow_method = 'CLIP'
    m['jf_color'] = color
    return m, w


# ------------------------------------------------------------ parts
DENTS = [((0.58, 0.0), 0.26, 0.026), ((-0.58, math.pi), 0.24, 0.024), ((-0.66, math.pi / 2), 0.22, 0.02), ((-0.64, -math.pi / 2), 0.22, 0.022), ((0.9, math.pi * 0.75 + 0.35), 0.2, 0.018)]


def shell(m):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=R)
    for v in bm.verts:  # the dents (in game axes: blender (x, -z, y))
        g = V3((v.co.x, v.co.z, -v.co.y)).normalized()
        k = 1.0
        for (la, az), rad, depth in DENTS:
            c = sph(la, az, 1.0)
            ang = math.acos(max(-1.0, min(1.0, g.dot(c))))
            k -= depth / R * math.exp(-(ang * R / rad) ** 2)
        v.co *= k
    o = _obj('wb_shell', bm, m)
    for p in o.data.polygons: p.use_smooth = True
    return o


def band(m):
    """the hoop round the equator in your colour: slightly domed, bevelled edges, its inner edge sunk into the shell"""
    y0 = R * math.sin(BAND)
    prof = [(R - 0.006, -y0), (R + 0.009, -y0 + 0.006), (R + 0.016, -y0 + 0.022), (R + 0.019, 0.0), (R + 0.016, y0 - 0.022), (R + 0.009, y0 - 0.006), (R - 0.006, y0)]
    o = lathe(prof, (0, 0, 0), m, seg=64, axis='y', name='wb_band', cap=False)
    return o


def strap_arc(name, m, az, lat0, lat1, w=0.1, t=0.013, n=None):
    """a riveted butt strap along a meridian (az), from lat0 to lat1: flat bar with bevelled edges, sunk into the shell"""
    n = n or max(4, int(abs(lat1 - lat0) * R / 0.09))
    L = V3((-math.sin(az), 0, math.cos(az)))
    sec = [(-w / 2, -0.008), (-w / 2, 0.0), (-w / 2 + 0.008, t), (w / 2 - 0.008, t), (w / 2, 0.0), (w / 2, -0.008)]
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    rings = []
    for i in range(n + 1):
        la = lat0 + (lat1 - lat0) * i / n
        P = sph(la, az); N = P.normalized()
        rings.append([bm.verts.new(gv(*(P + L * a + N * b))) for a, b in sec])
    k = len(sec)
    for i in range(n):
        for j in range(k):
            jj = (j + 1) % k
            f = bm.faces.new((rings[i][j], rings[i][jj], rings[i + 1][jj], rings[i + 1][j]))
            for lp, q in zip(f.loops, ((i / n * 3, j / k), (i / n * 3, (j + 1) / k), ((i + 1) / n * 3, (j + 1) / k), ((i + 1) / n * 3, j / k))): lp[uvl].uv = q
    for ring, flip in ((rings[0], False), (rings[-1], True)):
        f = bm.faces.new(ring[::-1] if not flip else ring)
        for lp in f.loops: lp[uvl].uv = (0.5 + 0.1 * math.cos(ring.index(lp.vert)), 0.5 + 0.1 * math.sin(ring.index(lp.vert)))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    smooth(o, 35)
    return o


def rivet_mesh(bm, uvl, p, n, r=0.032, h=0.024, seg=6):
    """a snap-head rivet dome on the surface at p, normal n (game), into bm"""
    M3 = frame_at(n)
    prof = [(r, -0.006), (r * 0.84, h * 0.55), (0.0, h)]
    rings = []
    for rr, z in prof[:-1]:
        rings.append([bm.verts.new(gv(*(p + M3 @ V3((math.cos(2 * math.pi * i / seg) * rr, math.sin(2 * math.pi * i / seg) * rr, z))))) for i in range(seg)])
    top = bm.verts.new(gv(*(p + M3 @ V3((0, 0, prof[-1][1])))))
    for a, b in zip(rings, rings[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            f = bm.faces.new((a[i], a[j], b[j], b[i]))
            for lp in f.loops: lp[uvl].uv = (0.2 + 0.6 * (i / seg), 0.3 + 0.3 * (lp.vert in b))
    for i in range(seg):
        j = (i + 1) % seg
        f = bm.faces.new((rings[-1][i], rings[-1][j], top))
        for lp in f.loops: lp[uvl].uv = (0.5 + 0.2 * math.cos(i), 0.5 + 0.2 * math.sin(i)) if lp.vert is not top else (0.5, 0.9)


def rivets(m):
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    count = 0
    for la in (BAND - 0.045, -(BAND - 0.045)):  # along both edges of the hoop, on the hoop
        for i in range(24):
            az = 2 * math.pi * (i + 0.5) / 24
            p = sph(la, az, R + 0.012)
            rivet_mesh(bm, uvl, p, p.normalized(), r=0.03, h=0.022); count += 1
    for az in (math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4):  # two rows down every strap
        L = V3((-math.sin(az), 0, math.cos(az)))
        for la0, la1, k in ((BAND + 0.1, 1.15, 4), (-(BAND + 0.1), -1.42, 5)):
            for i in range(k):
                la = la0 + (la1 - la0) * i / (k - 1)
                for s in (-1, 1):
                    q = sph(la, az, R + 0.012) + L * (s * 0.028)
                    rivet_mesh(bm, uvl, q, sph(la, az).normalized(), r=0.022, h=0.017, seg=5); count += 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj('wb_rivets', bm, m)
    smooth(o, 60)
    print('JF_RIVETS', count)
    return o


def hexbolt(bm, uvl, p, n, r=0.026, h=0.022, spin=0.0):
    M3 = frame_at(n)
    q = Matrix.Rotation(spin, 3, 'Z')
    rings = [[bm.verts.new(gv(*(p + M3 @ (q @ V3((math.cos(2 * math.pi * i / 6) * r, math.sin(2 * math.pi * i / 6) * r, z)))))) for i in range(6)] for z in (-0.006, h)]
    for i in range(6):
        j = (i + 1) % 6
        f = bm.faces.new((rings[0][i], rings[0][j], rings[1][j], rings[1][i]))
        for lp in f.loops: lp[uvl].uv = (i / 6 + 0.1 * (lp.vert in (rings[0][j], rings[1][j])), 0.2 + 0.5 * (lp.vert in rings[1]))
    for ring, flip in ((rings[0], True), (rings[1], False)):
        f = bm.faces.new(ring[::-1] if flip else ring)
        for lp in f.loops:
            a = ring.index(lp.vert); lp[uvl].uv = (0.5 + 0.3 * math.cos(a), 0.5 + 0.3 * math.sin(a))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])


def chain_link(name, m, centre=(0, 0, 0), rot=None, n_end=5, sides=6):
    """one long chain link: a stadium centreline (LINK_W wide, LINK_L long along y) swept with a round wire"""
    rc = LINK_W / 2
    st = (LINK_L - LINK_W) / 2  # half the straight
    path = []
    for i in range(n_end + 1):  # top end
        a = math.pi * i / n_end
        path.append(V3((rc * math.cos(a), st + rc * math.sin(a), 0)))
    for i in range(n_end + 1):  # bottom end
        a = math.pi + math.pi * i / n_end
        path.append(V3((rc * math.cos(a), -st + rc * math.sin(a), 0)))
    n = len(path)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    rings = []
    Q = rot or Matrix.Identity(3)
    for i in range(n):
        T = (path[(i + 1) % n] - path[i - 1]).normalized()
        Nn = V3((0, 0, 1)); B = T.cross(Nn)
        rings.append([bm.verts.new(gv(*(V3(centre) + Q @ (path[i] + (B * math.cos(2 * math.pi * k / sides) + Nn * math.sin(2 * math.pi * k / sides)) * WIRE)))) for k in range(sides)])
    for i in range(n):
        ii = (i + 1) % n
        for k in range(sides):
            kk = (k + 1) % sides
            f = bm.faces.new((rings[i][k], rings[i][kk], rings[ii][kk], rings[ii][k]))
            for lp, q in zip(f.loops, ((i / n * 2, k / sides), (i / n * 2, (k + 1) / sides), ((i + 1) / n * 2, (k + 1) / sides), ((i + 1) / n * 2, k / sides))): lp[uvl].uv = q
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    smooth(o, 70)
    return o


def stub(m_iron, m_lug, m_bolt, m_chain, m_weld):
    """the chain stub, worked down from the hook (2.05, where the game's chain carries on): the top link, the one it
    holds, the master ring hanging in that, and the pad eye's hole hanging on the ring"""
    HOOK = R + 0.95
    l2y = HOOK - 0.146  # the game's first link sits ~0.16 above the hook: this one interlocks with it
    l1y = l2y - (LINK_L - 2 * WIRE)  # its top wire rests on the bottom wire of the one above
    R1, R2 = 0.115, 0.044
    ring_top = l1y - LINK_L / 2 + WIRE + R2  # the ring's top tube rests on the bottom of link 1
    ring_y = ring_top - R1
    HOLE_R = 0.06
    HOLE_Y = ring_y - R1 - HOLE_R + R2  # the eye's top edge hangs on the ring's bottom tube
    TOP_R = 0.13
    BOSS_TOP = R + 0.025
    parts = []
    # the cast boss, its weld bead to the shell, eight bolts round the top
    prof = [(0.0, BOSS_TOP), (0.255, BOSS_TOP), (0.275, BOSS_TOP - 0.005), (0.29, BOSS_TOP - 0.018), (0.325, R - 0.035), (0.35, R - 0.07)]
    parts.append(lathe(prof, (0, 0, 0), m_iron, seg=28, axis='y', name='wb_boss', cap=True))
    yb = math.sqrt(R * R - 0.336 ** 2)
    parts.append(rope_ring('wb_weld', m_weld, 0.338, yb + 0.004, 0.017))
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    for i in range(8):
        a = 2 * math.pi * (i + 0.5) / 8
        hexbolt(bm, uvl, V3((math.cos(a) * 0.205, BOSS_TOP, math.sin(a) * 0.205)), V3((0, 1, 0)), r=0.027, h=0.024, spin=a)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bolts = _obj('wb_bolts', bm, m_bolt); smooth(bolts, 30)
    parts.append(bolts)
    # the pad eye: a thick plate across z (thickness along x), round top, the hole; small fillet welds at its foot
    base = BOSS_TOP - 0.012
    outline = [(-TOP_R, base), (TOP_R, base), (TOP_R, HOLE_Y)] + [(TOP_R * math.cos(a), HOLE_Y + TOP_R * math.sin(a)) for a in [math.pi * i / 14 for i in range(1, 14)]] + [(-TOP_R, HOLE_Y)]
    hole = [(HOLE_R * math.cos(2 * math.pi * i / 16), HOLE_Y + HOLE_R * math.sin(2 * math.pi * i / 16)) for i in range(16)]
    lug = side(outline, 0.09, (0, 0, 0), m_lug, bev=0.01, seg=2, name='wb_lug', holes=[hole], angle=35)
    apply_mods(lug)
    for f in lug.data.polygons: f.material_index = 0  # (the boolean's new faces land on a junk slot: kit gotcha)
    while len(lug.data.materials) > 1: lug.data.materials.pop(index=len(lug.data.materials) - 1)
    parts.append(lug)
    for sx in (1, -1):
        parts.append(rope_line(f'wb_fillet{sx}', m_weld, [V3((sx * 0.046, BOSS_TOP + 0.002, z)) for z in np.linspace(-TOP_R + 0.01, TOP_R - 0.01, 9)], 0.008))
    # the master ring through the eye, then two links up to the hook
    parts.append(torus_mesh('wb_ring', m_chain, (0, ring_y, 0), R1, R2, 16, 8))
    parts.append(chain_link('wb_link1', m_chain, (0, l1y, 0), rot=Matrix.Rotation(math.pi / 2, 3, 'Y')))
    parts.append(chain_link('wb_link2', m_chain, (0, l2y, 0)))
    print('JF_STUB hole', round(HOLE_Y, 3), 'ring', round(ring_y, 3), 'links', round(l1y, 3), round(l2y, 3), 'hook', round(HOOK, 3))
    return parts, (HOLE_Y, HOLE_R, BOSS_TOP, HOOK)


def torus_mesh(name, m, c, R1, r2, seg=16, sides=8):
    """a ring in the XY plane (round z), like three's TorusGeometry"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        ca, sa = math.cos(a), math.sin(a)
        rings.append([bm.verts.new(gv(c[0] + (R1 + r2 * math.cos(2 * math.pi * k / sides)) * ca, c[1] + (R1 + r2 * math.cos(2 * math.pi * k / sides)) * sa, c[2] + r2 * math.sin(2 * math.pi * k / sides))) for k in range(sides)])
    for i in range(seg):
        ii = (i + 1) % seg
        for k in range(sides):
            kk = (k + 1) % sides
            f = bm.faces.new((rings[i][k], rings[ii][k], rings[ii][kk], rings[i][kk]))
            for lp, q in zip(f.loops, ((i / seg, k / sides), ((i + 1) / seg, k / sides), ((i + 1) / seg, (k + 1) / sides), (i / seg, (k + 1) / sides))): lp[uvl].uv = q
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    smooth(o, 70)
    return o


def rope_ring(name, m, r, y, tube, seg=40, sides=6):
    """a weld bead round y at height y"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        d = V3((math.cos(a), 0, math.sin(a)))
        rings.append([bm.verts.new(gv(*(d * (r + tube * math.cos(2 * math.pi * k / sides)) + V3((0, y + tube * math.sin(2 * math.pi * k / sides), 0))))) for k in range(sides)])
    for i in range(seg):
        ii = (i + 1) % seg
        for k in range(sides):
            kk = (k + 1) % sides
            f = bm.faces.new((rings[i][k], rings[ii][k], rings[ii][kk], rings[i][kk]))
            for lp, q in zip(f.loops, ((i / seg * 8, k / sides), ((i + 1) / seg * 8, k / sides), ((i + 1) / seg * 8, (k + 1) / sides), (i / seg * 8, (k + 1) / sides))): lp[uvl].uv = q
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    smooth(o, 70)
    return o


def rope_line(name, m, pts, r, sides=6):
    o = sweep([tuple(p) for p in pts], r, m, seg=sides, name=name)
    return o


# ------------------------------------------------------------ the slot
def slot_frame(m_frame, m_bolt):
    """the viewport frame in the slot's own space (x across, y up, -z out of the ball): outer 0.76 x 0.29, opening
    0.62 x 0.17, 0.18 deep (+ more buried in the shell), the front edge of the opening chamfered in; a rain hood"""
    OW, OH, IW, IH = 0.38, 0.145, 0.31, 0.085
    zf, zfi, zb = -0.09, -0.074, 0.16
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    def rect(hw, hh, z): return [bm.verts.new(gv(x, y, z)) for x, y in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
    of, inf, ob, ib = rect(OW, OH, zf), rect(IW, IH, zfi), rect(OW, OH, zb), rect(IW, IH, zb)
    def quad(a, b, c, d):
        f = bm.faces.new((a, b, c, d))
        for lp in f.loops:
            g = V3((lp.vert.co.x, lp.vert.co.z, -lp.vert.co.y)); lp[uvl].uv = ((g.x + g.z) * 2.5, (g.y + g.z) * 2.5)
    for i in range(4):
        j = (i + 1) % 4
        quad(of[i], of[j], inf[j], inf[i])  # the front (sloping into the opening)
        quad(ob[j], ob[i], of[i], of[j])  # outer walls
        quad(inf[i], inf[j], ib[j], ib[i])  # the opening's walls
        quad(ib[i], ib[j], ob[j], ob[i])  # back
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    fr = _obj('slot_frame', bm, m_frame)
    smooth(fr, 30); bevel(fr, 0.011, 2, 30)
    apply_mods(fr)
    # bolts round the front
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    n = V3((0, 0, -1))
    for x, y in ((-0.345, 0.115), (0.345, 0.115), (-0.345, -0.115), (0.345, -0.115), (-0.17, 0.116), (0.17, 0.116), (-0.17, -0.116), (0.17, -0.116)):
        zz = zf + (zfi - zf) * max(0.0, (abs(y) - IH) / (OH - IH) - 1) if False else zf - 0.0
        # the front slopes from zf at the outer edge to zfi at the opening: put each bolt on it
        t = min(1.0, max(0.0, (OH - abs(y)) / (OH - IH))) if abs(x) < IW else min(1.0, max(0.0, (OW - abs(x)) / (OW - IW)))
        z = zf + (zfi - zf) * t
        hexbolt(bm, uvl, V3((x, y, z + 0.004)), n, r=0.017, h=0.014, spin=0.3 * x)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bolts = _obj('slot_bolts', bm, m_bolt); smooth(bolts, 30)
    # a rain hood over the top: a bent plate out over the opening (it shades your eyes: you look grumpy)
    hood = []
    prof = [(OH - 0.01, zf + 0.03), (OH + 0.006, zf - 0.005), (OH + 0.004, zf - 0.045), (OH - 0.012, zf - 0.075)]
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    T_ = 0.012
    tops = [[bm.verts.new(gv(x, y, z)) for y, z in prof] for x in (-OW - 0.01, OW + 0.01)]
    bots = [[bm.verts.new(gv(x, y - T_, z + (0.004 if i else 0))) for i, (y, z) in enumerate(prof)] for x in (-OW - 0.01, OW + 0.01)]
    k = len(prof)
    for i in range(k - 1):
        for a, b in ((tops, None), (bots, 1)):
            f = bm.faces.new((a[0][i], a[1][i], a[1][i + 1], a[0][i + 1]))
    for s in (0, 1):
        for i in range(k - 1):
            bm.faces.new((tops[s][i], tops[s][i + 1], bots[s][i + 1], bots[s][i]))
    bm.faces.new((tops[0][0], bots[0][0], bots[1][0], tops[1][0]))
    bm.faces.new((tops[0][-1], tops[1][-1], bots[1][-1], bots[0][-1]))
    for f in bm.faces:
        for lp in f.loops:
            g = V3((lp.vert.co.x, lp.vert.co.z, -lp.vert.co.y)); lp[uvl].uv = (g.x * 2.5, (g.y + g.z) * 2.5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    hd = _obj('slot_hood', bm, m_frame)
    smooth(hd, 30); bevel(hd, 0.004, 1, 30); apply_mods(hd)
    return [fr, bolts, hd]


# ------------------------------------------------------------ the sign
def baby_sign(m_sign, m_cup, la=0.52, az=math.pi / 2, size=0.42):
    """the BABY ON BOARD diamond, bent to the ball (flexible plastic), on its suction cup at the top corner"""
    c = sph(la, az).normalized()
    M3 = frame_at(c)  # x = across, y = up-ish on the surface
    up = M3.col[1]; right = M3.col[0]
    # face the sign outward with "up" toward the ball's top
    up = (V3((0, 1, 0)) - c * c.y).normalized(); right = up.cross(c).normalized()  # as you look at it from outside
    n = 6
    h = size / 2
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    grid = {}
    for i in range(n + 1):
        for j in range(n + 1):
            u, v = i / n, j / n
            # the diamond: (u, v) over the square, rotated 45 deg
            a, b = (u - 0.5) * 2, (v - 0.5) * 2
            x, y = (a - b) * h / 2, (a + b) * h / 2
            p = (c * R + right * x + up * y)
            p = p.normalized() * (R + 0.006)
            grid[(i, j)] = (bm.verts.new(gv(*p)), (0.5 + (x / h) * 0.5 * 1.0, 0.5 + (y / h) * 0.5))
    for i in range(n):
        for j in range(n):
            vs = [grid[(i, j)], grid[(i + 1, j)], grid[(i + 1, j + 1)], grid[(i, j + 1)]]
            f = bm.faces.new([q[0] for q in vs])
            for lp, q in zip(f.loops, vs): lp[uvl].uv = q[1]
    # thickness: a back copy sunk a little (so it has edges and no back-face hole)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj('wb_sign', bm, m_sign)
    sol = o.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.006; sol.offset = -1.0
    apply_mods(o)
    for f in o.data.polygons: f.use_smooth = True
    # the suction cup at the top corner
    tip = (c * R + up * (h * 0.8)).normalized() * (R + 0.006)  # on the sign's face, its rim sunk in
    cup = lathe([(0.0, 0.026), (0.016, 0.022), (0.032, 0.008), (0.038, 0.0), (0.038, -0.004), (0.0, -0.004)], (0, 0, 0), m_cup, seg=14, axis='y', name='wb_cup')
    apply_mods(cup)
    cup.data.transform(G2B(frame_at(tip) @ Matrix.Rotation(math.pi / 2, 3, 'X')))
    cup.data.transform(Matrix.Translation(gv(*tip)))
    return [o, cup]


# ------------------------------------------------------------ build
def build():
    steel = mat('wb_steel', 0xffffff, rough=0.42, metal=0.18, clearcoat=0.45, tex=tex_canvas('wb_steel_t', 64, 64, steel_px(0x8a95a2, 11, rust=0.6)))
    strap = mat('wb_strap', 0xffffff, rough=0.45, metal=0.25, clearcoat=0.3, tex=tex_canvas('wb_strap_t', 32, 32, steel_px(0x68717c, 12, rust=0.8, chips=0.6)))
    rivm = mat('wb_rivet', 0xd0d8e0, rough=0.28, metal=0.55)
    accent = mat('wb_accent', 0xff4fd8, rough=0.35, clearcoat=0.6)
    iron = mat('wb_iron', 0xffffff, rough=0.45, metal=0.35, tex=tex_canvas('wb_iron_t', 32, 32, steel_px(0x5e6670, 13, rust=0.6, chips=0.4)))
    lugm = mat('wb_lug', 0xffffff, rough=0.35, clearcoat=0.6, tex=tex_canvas('wb_lug_t', 16, 16, lug_px))
    bolt = mat('wb_bolt', 0xaab2bc, rough=0.3, metal=0.55)
    chain = mat('wb_chain', 0xffffff, rough=0.34, metal=0.45, tex=tex_canvas('wb_chain_t', 16, 16, steel_px(0x86909a, 14, rust=0.35, chips=0.6)))
    weldm = mat('wb_weld', 0xffffff, rough=0.6, metal=0.6, tex=tex_noise('wb_weld_t', 0x4a4038, var=0.3, size=8, seed=15))
    frame_m = mat('wb_frame', 0xffffff, rough=0.4, metal=0.3, tex=tex_canvas('wb_frame_t', 32, 32, steel_px(0x5a636e, 16, rust=0.4, chips=0.6)))
    sign_m = mat('wb_sign', 0xffffff, rough=0.3, clearcoat=0.7, tex=tex_canvas('wb_sign_t', 64, 64, sign_px))
    cup_m = mat('wb_cup', 0xd8f0ff, rough=0.1, alpha=0.55, clearcoat=1.0)
    parts = [shell(steel), band(accent)]
    for az in (math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4):  # four straps over the top, under the boss
        parts.append(strap_arc(f'wb_strapT{int(math.degrees(az))}', strap, az, BAND - 0.02, 1.3))
    for k, az in enumerate((math.pi / 4, 3 * math.pi / 4)):  # two full arcs underneath, crossing at the bottom
        parts.append(strap_arc(f'wb_strapB{k}', strap, az, -(BAND - 0.02), -math.pi + (BAND - 0.02), t=0.013 + 0.004 * k))
    parts.append(rivets(rivm))
    st, (hole_y, hole_r, boss_top, hook_y) = stub(iron, lugm, bolt, chain, weldm)
    parts += st
    # LIFT HERE stencilled on both faces of the pad eye, under the hole
    sten, sw = stencil_mat('wb_stencil', 'LIFT HERE')
    for s in (1, -1):
        bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
        L = 0.19; Hh = L * 9 / sw
        yc = (boss_top + 0.012 + hole_y - hole_r) / 2
        x = s * (0.045 + 0.0015)
        quad = [(-L / 2, yc - Hh / 2), (L / 2, yc - Hh / 2), (L / 2, yc + Hh / 2), (-L / 2, yc + Hh / 2)]
        vs = [bm.verts.new(gv(x, y, z * s * -1)) for z, y in quad]
        f = bm.faces.new(vs)
        for lp, (u, v) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = (u, v)
        vb = [bm.verts.new(gv(x - s * 0.003, y, z * s * -1)) for z, y in quad]
        fb = bm.faces.new(vb[::-1])
        for lp, (u, v) in zip(fb.loops, ((0, 1), (1, 1), (1, 0), (0, 0))): lp[uvl].uv = (u, v)
        for i in range(4):
            j = (i + 1) % 4
            fs = bm.faces.new((vs[i], vb[i], vb[j], vs[j]))
            for lp in fs.loops: lp[uvl].uv = (0.003 + 0.001 * (lp.vert in vb), 0.003 + 0.001 * (lp.vert in (vs[j], vb[j])))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(_obj(f'wb_lift{s}', bm, sten))
    parts += baby_sign(sign_m, cup_m)
    # the viewport frame: its own node with the exact transform the game expects
    sp = slot_frame(frame_m, bolt)
    for p in parts + sp:
        apply_mods(p)
        if p.data.materials[0].name not in ('wb_stencil', 'wb_sign'): uv_box(p, 0.6 if p.name == 'wb_shell' else 0.25)
        uv_unzero(p); weld(p, 1e-7)
    lk = chain_link('link', chain)
    uv_unzero(lk)
    SLOT_POS, SLOT_ROT = gv(0, math.sin(LAT_SLOT) * R, -math.cos(LAT_SLOT) * R), Euler((LAT_SLOT, 0, 0))
    if '--qa' in ARGV:
        for p in sp: p.location = SLOT_POS; p.rotation_euler = SLOT_ROT
        bpy.context.view_layer.update()
        qa(parts + sp, lk)
        for p in sp: p.location = (0, 0, 0); p.rotation_euler = (0, 0, 0)
        bpy.context.view_layer.update()
    groups = {}
    for p in parts: groups.setdefault(p.data.materials[0].name, []).append(p)
    nodes = [join(objs, 'ball_' + mn[3:]) for mn, objs in sorted(groups.items())]
    slot = join(sp, 'slot')
    slot.location = SLOT_POS
    slot.rotation_euler = SLOT_ROT
    lk.location = gv(1.75, -0.8, 0.25)
    meta = {'kind': 'prop', 'id': 'wreck', 'hook': [0, round(hook_y, 4), 0], 'paint': ['wb_steel'], 'slot': 'slot', 'link': 'link', 'accent': 'wb_accent'}
    print('JF_META', json.dumps(meta))
    root = finish('x_wreck', nodes + [slot, lk], meta)
    for a_ in ARGV:
        if a_.startswith('--close='):
            sys.path.insert(0, '/tmp/claude-0/-workspace-jankfire/86957797-7d93-5698-a006-852e0a15c9f9/scratchpad/agents/misc')
            import closeup
            closeup.shots(root, [('front', (0.6, 0.9, -3.6), (0, 0.2, 0), 35), ('back', (-1.2, 1.2, 3.4), (0, 0.3, 0), 35),
                                 ('slot', (0.5, 0.7, -2.0), (0, 0.45, -1.0), 40), ('stub', (1.4, 1.9, -1.2), (0, 1.5, 0), 40),
                                 ('below', (1.5, -2.6, -1.6), (0, -0.4, 0), 35), ('sign', (-0.4, 1.0, 2.4), (0, 0.5, 1.0), 45)], a_.split('=', 1)[1], 'wreck', exposure=-0.2)
    return root


def qa(parts, lk):
    sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    for tag, objs in (('ball', parts), ('link', [lk])):
        res = qa_check.run(objects=[p.name for p in objs], profile='game', eps=0.0008, tol=0.002)
        print('QA_PASS', tag, res.get('pass'))
        for k in ('errors', 'warnings'):
            for e in res.get(k, []): print('QA_' + k.upper()[:-1], tag, e)
        for n, m in res.get('objects', {}).items():
            bad = {k: v for k, v in m.items() if k in ('degenerate_faces', 'zero_length_edges', 'nonmanifold_edges', 'boundary_edges', 'inconsistent_normals_edges', 'inside_out_islands', 'duplicate_verts', 'islands') and v}
            print('QA_PART', tag, n, m.get('tris'), bad)


main(build, 'x_wreck', exposure=-0.2)
