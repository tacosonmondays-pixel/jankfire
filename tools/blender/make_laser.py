# Big Laser Pointer: an office laser pointer pen (anodized aluminium body, chrome tail cap with a pocket clip and a
# split-ring lanyard, a chrome switch collar with a rubber push button, a flared head with a knurled grip band and a
# recessed lens) scaled about x4.7 to the size of a leg, exactly where the code model (gearmodels.js laserBuild) has it:
# body 84 mm across, lens at z -0.408, muzzle z -0.42. Then the hack: the grip and trigger guard of a lime toy pistol
# (clamshell halves, screws, a stippled panel) duct-taped underneath, two D-cells taped end to end under the front and
# wired in with hot glue, a 5-LED bar-graph module (the PEW-O-METER) zip-tied to the side you see, a cat charm on the
# lanyard (cats love these). The yellow warning sticker says CLASS 9000, the aperture label says the beam comes out
# this end, the body print says MAX OUTPUT: YES.
# own nodes (meta.laser names them, public/js/laserglb.js binds them): lz_button_wzN (origin (0, 0.047, -0.07): the game presses it to y 0.042), lz_led0_wzN ..
# lz_led4_wzN (z 0.16 .. 0.064, the game lights them), lz_emit_wzN (the emitter in the lens, the game brightens it),
# lz_charm_wzN (origin (0, -0.006, 0.338) on the split ring, hangs down -y, the game swings it). The charge orb in
# front of the lens is the game's. run: blender -b --python tools/blender/make_laser.py  (-- --qa: the asset-QA gate)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib

R_BODY = 0.042
BTN = (0, 0.047, -0.07)
CHARM = (0, -0.006, 0.338)
LED_Z = [0.16 - 0.024 * i for i in range(5)]
LED_TH = math.radians(155)  # the meter faces up-left, toward the first-person camera (it sees the top and the -x side)
CELL_Y, CELL_R = -0.0645, 0.0222
FONT.setdefault('(', ['00010', '00100', '01000', '01000', '01000', '00100', '00010'])
FONT.setdefault(')', ['01000', '00100', '00010', '00010', '00010', '00100', '01000'])


# ------------------------------------------------------------ small kit additions (local to this script)
def weld(o, dist=1e-6, sliver=1e-7):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=sliver)
    bm.to_mesh(o.data); bm.free()
    return o


def dcut(o, cutter):
    """boolean the cutter out of o; the new faces take the cutter's material (holes, recesses)"""
    apply_mods(cutter)
    md = o.modifiers.new('bool', 'BOOLEAN'); md.object = cutter; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'
    md.material_mode = 'TRANSFER'
    bpy.context.view_layer.objects.active = o
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    o.select_set(True)
    bpy.ops.object.modifier_move_to_index(modifier=md.name, index=0)
    bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    return weld(o)


def fix_zero_uv(o, spread=0.002):
    """faces whose UVs collapsed (decal sides, edges seen side on) get a tiny box projection round their own mean UV:
    the same texel colour, but a real area (the QA gate and bakes want that)"""
    me = o.data
    if not me.uv_layers: return o
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        ls = list(poly.loop_indices)
        pts = [uv[i].uv.copy() for i in ls]
        a2 = sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))
        if abs(a2) > 1e-9: continue
        c = sum(pts, Vector((0, 0))) / len(pts)
        n = poly.normal; ax = max(range(3), key=lambda i: abs(n[i])); a, b = [(1, 2), (0, 2), (0, 1)][ax]
        co = [me.vertices[me.loops[i].vertex_index].co for i in ls]
        lo_a, hi_a = min(p[a] for p in co), max(p[a] for p in co); lo_b, hi_b = min(p[b] for p in co), max(p[b] for p in co)
        for i, p in zip(ls, co):
            uv[i].uv = (c.x + ((p[a] - lo_a) / max(hi_a - lo_a, 1e-9) - 0.5) * spread, c.y + ((p[b] - lo_b) / max(hi_b - lo_b, 1e-9) - 0.5) * spread)
    return o


def drop_loose(bm):
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')


def torus(R, r, c, axis, m, seg=24, tseg=8, name='torus'):
    """a ring of wire radius r round a game axis through c (axis x = the ring stands in the YZ plane)"""
    bm = bmesh.new(); rings = []
    for i in range(seg):
        t = 2 * math.pi * i / seg; ring = []
        for j in range(tseg):
            p = 2 * math.pi * j / tseg
            rr, h = R + r * math.cos(p), r * math.sin(p)
            a, b = rr * math.cos(t), rr * math.sin(t)
            g = {'z': (c[0] + a, c[1] + b, c[2] + h), 'x': (c[0] + h, c[1] + b, c[2] + a), 'y': (c[0] + a, c[1] + h, c[2] + b)}[axis]
            ring.append(bm.verts.new(gv(*g)))
        rings.append(ring)
    for A, B in zip(rings, rings[1:] + rings[:1]):
        for j in range(tseg):
            k = (j + 1) % tseg
            bm.faces.new((A[j], A[k], B[k], B[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); smooth(o, 70)
    return o


def uv_cylz(o, z0, z1, su=1.0, sv=1.0, turn=-math.pi / 2):
    """u along the pen (z0 -> 0, z1 -> su), v once round (angle from +x toward +y, from `turn`) x sv. per face, no seams"""
    bpy.context.view_layer.update()
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data; mw = o.matrix_world
    for poly in me.polygons:
        ls = []
        for li in poly.loop_indices:
            v = mw @ me.vertices[me.loops[li].vertex_index].co
            gx, gy, gz = v.x, v.z, -v.y
            a = math.atan2(gy, gx) if abs(gx) + abs(gy) > 1e-7 else 0.0
            ls.append([li, (gz - z0) / (z1 - z0) * su, (a - turn) / (2 * math.pi)])
        ref = ls[0][2]
        for e in ls:
            while e[2] - ref > 0.5: e[2] -= 1
            while e[2] - ref < -0.5: e[2] += 1
        for li, u, w in ls: uv[li].uv = (u, w * sv)


def uv_dir(o, origin, uax, vax, su, sv, nrm=None, rect=(0, 0, 1, 1), plain=None):
    """planar UVs along two game directions (a decal seen straight on: uax = the viewer's right, vax = up). faces that
    don't face nrm (if given) get a squeezed plain corner of the texture instead (no zero-area UVs)"""
    bpy.context.view_layer.update()
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data; mw = o.matrix_world
    O, U, V = Vector(origin), Vector(uax).normalized(), Vector(vax).normalized()
    N = Vector(nrm).normalized() if nrm else None
    for poly in me.polygons:
        n = mw.to_3x3() @ poly.normal; gn = Vector((n.x, n.z, -n.y))
        face = N is None or gn.dot(N) > 0.5
        for li in poly.loop_indices:
            v = mw @ me.vertices[me.loops[li].vertex_index].co
            g = Vector((v.x, v.z, -v.y)) - O
            u, w = g.dot(U) / su + 0.5, g.dot(V) / sv + 0.5
            r = rect if face else (plain or rect)
            if not face: u, w = 0.5 + (u - 0.5) * 0.2, 0.5 + (w - 0.5) * 0.2
            uv[li].uv = (r[0] + u * (r[2] - r[0]), r[1] + w * (r[3] - r[1]))


def hull2d(pts):
    pts = sorted(set((round(x, 7), round(y, 7)) for x, y in pts))
    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0: hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]  # counter-clockwise


def resample(poly, n, start_angle=None):
    """a closed outline resampled to n points evenly by length (optionally starting nearest start_angle)"""
    P = [Vector(p) for p in poly]
    seg = [(P[i] - P[i - 1]).length for i in range(1, len(P))] + [(P[0] - P[-1]).length]
    L = sum(seg); out = []
    k, acc = 0, 0.0
    for i in range(n):
        s = L * i / n
        while k < len(seg) - 1 and acc + seg[k] < s: acc += seg[k]; k += 1
        a, b = P[k], P[(k + 1) % len(P)]
        out.append(a + (b - a) * ((s - acc) / max(seg[k], 1e-9)))
    if start_angle is not None:
        j = min(range(n), key=lambda i: abs(math.remainder(math.atan2(out[i].y, out[i].x) - start_angle, 2 * math.pi)))
        out = out[j:] + out[:j]
    return out


def circle_pts(c, r, n=48): return [(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def band(outline, z, w, m, name='tape', turns=1.18, tt=0.0007, n=44, across=3, start=math.radians(90), seed=1, lift=0.0,
         wrinkle=0.0002, torn=True, tex_len=0.06):
    """duct tape (or a zip tie) wound round whatever the outline goes round (a closed (x, y) outline at z): a spiral of
    `turns`, each wrap lying on the one before, a torn end, optional `lift` (m) where the end peels up"""
    rnd = random.Random(seed)
    P = resample(outline, n, start)
    Nn = []
    for i in range(n):
        d = P[(i + 1) % n] - P[i - 1]
        Nn.append(Vector((d.y, -d.x)).normalized())  # outward (the outline is counter-clockwise)
    M = int(n * turns)
    tear = [rnd.uniform(-0.85, 0.4) if torn else 0.0 for _ in range(across)]  # (never back past the last station: no fold)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    lay = (tt + 0.0003)  # each wrap sits on the last
    perim = sum((P[i] - P[i - 1]).length for i in range(n))
    ph = [rnd.uniform(0, 6.28) for _ in range(4)]
    def at(sf, k):
        i0 = int(math.floor(sf)); f = sf - i0
        a, b = P[i0 % n], P[(i0 + 1) % n]; na, nb = Nn[i0 % n], Nn[(i0 + 1) % n]
        p = a + (b - a) * f; q = (na + (nb - na) * f).normalized()
        ww = w - 0.0007 * sf / n  # each wrap a hair narrower than the one under it (no coplanar edges)
        zz = z - ww / 2 + ww * k / (across - 1)
        wr = wrinkle * (math.sin(sf * 0.9 + ph[0] + k * 1.3) + 0.6 * math.sin(sf * 2.3 + ph[1] - k)) / 1.6
        up = max(0.0, (sf - (M - 9)) / 9) ** 2 * lift
        d0 = -0.00022 + sf / n * lay + wr + up
        return p, q, d0, zz
    outer, inner, us = [], [], []
    for s in range(M + 1):
        ro, ri = [], []
        for k in range(across):
            sf = s + (tear[k] if s == M else 0.0)
            p, q, d0, zz = at(sf, k)
            ro.append(bm.verts.new(gv(p.x + q.x * (d0 + tt), p.y + q.y * (d0 + tt), zz)))
            ri.append(bm.verts.new(gv(p.x + q.x * d0, p.y + q.y * d0, zz)))
        outer.append(ro); inner.append(ri); us.append(s / n * perim / tex_len)
    def quad(vs, uvs):
        try: f = bm.faces.new(vs)
        except ValueError: return
        for lp, t in zip(f.loops, uvs): lp[uvl].uv = t
    for s in range(M):
        for k in range(across - 1):
            v0, v1 = k / (across - 1), (k + 1) / (across - 1)
            quad((outer[s][k], outer[s + 1][k], outer[s + 1][k + 1], outer[s][k + 1]), [(us[s], v0), (us[s + 1], v0), (us[s + 1], v1), (us[s], v1)])
            if s >= M - 10: quad((inner[s][k + 1], inner[s + 1][k + 1], inner[s + 1][k], inner[s][k]), [(us[s], v1), (us[s + 1], v1), (us[s + 1], v0), (us[s], v0)])  # (the rest lies on the body: never seen)
        for k, (a, b) in ((0, (inner, outer)), (across - 1, (outer, inner))):
            quad((a[s][k], a[s + 1][k], b[s + 1][k], b[s][k]), [(us[s], 0.02), (us[s + 1], 0.02), (us[s + 1], 0.05), (us[s], 0.05)])
    for s, rev in ((M, False),):  # the free end (the start is under the next wrap)
        for k in range(across - 1):
            vs = (outer[s][k], outer[s][k + 1], inner[s][k + 1], inner[s][k])
            quad(vs[::-1] if rev else vs, [(us[s], 0.1), (us[s], 0.2), (us[s] + 0.01, 0.2), (us[s] + 0.01, 0.1)])
    drop_loose(bm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); smooth(o, 50)
    return o


def patch(r_out, r_in, z0, z1, th0, th1, m, uvf, name='patch', nz=4, nth=8, back=False):
    """a sticker on a round body: a curved slab from angle th0 to th1 (from +x toward +y), z0..z1, its face at r_out
    (proud of the surface: no z-fighting), its back sunk to r_in. uvf(t_z, t_th) -> (u, v) on the face, 0..1 each"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    def P(r, i, j):
        th = th0 + (th1 - th0) * j / nth; zz = z0 + (z1 - z0) * i / nz
        return bm.verts.new(gv(r * math.cos(th), r * math.sin(th), zz))
    O = [[P(r_out, i, j) for j in range(nth + 1)] for i in range(nz + 1)]
    I = [[P(r_in, i, j) for j in range(nth + 1)] for i in range(nz + 1)]
    def quad(vs, uvs):
        f = bm.faces.new(vs)
        for lp, t in zip(f.loops, uvs): lp[uvl].uv = t
    for i in range(nz):
        for j in range(nth):
            c = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            quad([O[a][b] for a, b in c], [uvf(a / nz, b / nth) for a, b in c])
            if back: quad([I[a][b] for a, b in c][::-1], [uvf(a / nz, b / nth) for a, b in c][::-1])
    def edge(cells):  # the rim: its border pixels
        for (a0, b0), (a1, b1) in zip(cells, cells[1:]):
            t0, t1 = uvf(a0 / nz, b0 / nth), uvf(a1 / nz, b1 / nth)
            try: quad([O[a0][b0], O[a1][b1], I[a1][b1], I[a0][b0]], [t0, t1, t1, t0])
            except ValueError: pass
    edge([(0, j) for j in range(nth + 1)]); edge([(nz, j) for j in range(nth + 1)][::-1])
    edge([(i, nth) for i in range(nz + 1)]); edge([(i, 0) for i in range(nz + 1)][::-1])
    drop_loose(bm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); smooth(o, 30)
    return o


def decal_mat(name, px, rough=0.4, metal=0.0, clip=False, emit=0.0):
    """a material from a painted RGBA (h x w x 4) array: alpha-clipped letters if clip"""
    h, w = px.shape[:2]
    img = bpy.data.images.new(name + '_t', w, h, alpha=True)
    img.pixels.foreach_set(np.ascontiguousarray(px[::-1]).ravel()); img.file_format = 'PNG'; img.pack()
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; t.interpolation = 'Closest'
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    if clip:
        nt.links.new(t.outputs['Alpha'], b.inputs['Alpha'])
        m.blend_method = 'CLIP'; m.alpha_threshold = 0.5; m.shadow_method = 'CLIP'
    if emit:
        nt.links.new(t.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = emit
    m['jf_color'] = 0xffffff
    return m


def rgba(px3, alpha=None):
    a = np.ones(px3.shape[:2] + (1,), np.float32) if alpha is None else alpha[:, :, None].astype(np.float32)
    return np.concatenate([px3.astype(np.float32), a], axis=2)


def text_w(s, scale=1): return (len(s) * 6 - 1) * scale


def tex_px(name, w, h, draw):  # tex_canvas, but the draw function gets numpy (h, w, 3)
    return tex_canvas(name, w, h, draw)


def laser_symbol(px, cx, cy, s, ink, bg):
    """the starburst-in-a-triangle laser symbol, s = the triangle's height in pixels"""
    h, w = px.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    def tri(sz):
        top = cy - sz * 0.62; bot = cy + sz * 0.38
        half = (yy - top) / max(bot - top, 1e-6) * sz * 0.6
        return (yy >= top) & (yy <= bot) & (np.abs(xx + 0.5 - cx) <= half)
    px[tri(s)] = hexrgb(ink); px[tri(s * 0.66)] = hexrgb(bg)
    c2 = (cx, cy + s * 0.05)
    for i in range(8):
        a = i / 8 * 2 * math.pi
        px_line(px, c2[0] + math.cos(a) * s * 0.07, c2[1] + math.sin(a) * s * 0.07, c2[0] + math.cos(a) * s * 0.17, c2[1] + math.sin(a) * s * 0.17, ink, 1.0)
    px_line(px, c2[0], c2[1], c2[0] + s * 0.32, c2[1], ink, 1.0)
    px_disc(px, c2[0], c2[1], s * 0.06, ink)


# ------------------------------------------------------------ textures
def tex_brushed(name, base, w=64, h=32, var=0.07, seed=1):
    r = np.random.default_rng(seed)
    rows = np.convolve(r.random(h + 4), np.ones(3) / 3, 'same')[2:h + 2]
    n = 0.65 * rows[:, None] + 0.35 * r.random((h, w)) * 0.6 + 0.12
    px = hexrgb(base)[None, None, :] * (1 - var + 2 * var * n[:, :, None])
    return _img(name, px)


def _img(name, px): return lib._image(name, np.clip(px, 0, 1).astype(np.float32))


def tex_knurl(name, base, dark, size=16, period=4):
    y, x = np.mgrid[0:size, 0:size]
    k = ((x + y) % period == 0) | ((x - y) % period == 0)
    px = np.where(k[:, :, None], hexrgb(dark), hexrgb(base)).astype(np.float32)
    r = np.random.default_rng(3); px *= (0.92 + 0.16 * r.random((size, size)))[:, :, None]
    return _img(name, px)


def tex_tape(name, base=0xaab0b8, size=16, seed=4):
    r = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size]
    weave = 0.84 + 0.16 * ((x % 2) ^ (y % 3 == 0))
    n = weave * (0.82 + 0.3 * r.random((size, size)))
    px = hexrgb(base)[None, None] * n[:, :, None]
    return _img(name, px)


def tex_stipple(name, base, dot, size=16, seed=5):
    r = np.random.default_rng(seed)
    px = np.tile(hexrgb(base), (size, size, 1)) * (0.9 + 0.15 * r.random((size, size, 1)))
    m = r.random((size, size)) < 0.28
    px[m] = hexrgb(dot)
    return _img(name, px)


def build():
    body_m = mat('lz_body', 0xd42a8c, rough=0.3, metal=0.55, clearcoat=0.6, tex=tex_brushed('lz_body_t', 0xd42a8c, seed=11))
    chrome = mat('lz_chrome', 0xd8dee6, rough=0.12, metal=1.0, tex=tex_noise('lz_chrome_t', 0xd8dee6, var=0.04, size=16, seed=12))
    knurl = mat('lz_knurl', 0xc4cad2, rough=0.3, metal=1.0, tex=tex_knurl('lz_knurl_t', 0xc8ced6, 0x5a6068))
    dark = mat('lz_dark', 0x0c0c10, rough=0.6)
    grip_m = mat('lz_grip', 0x55e02c, rough=0.32, clearcoat=0.4, tex=tex_noise('lz_grip_t', 0x55e02c, var=0.05, size=16, seed=13))
    panel_m = mat('lz_panel', 0x2f9a1a, rough=0.6, tex=tex_stipple('lz_panel_t', 0x35a81e, 0x1c6a10))
    trig_m = mat('lz_trig', 0xffe14d, rough=0.3, clearcoat=0.5)
    steel = mat('lz_steel', 0xb8bcc4, rough=0.25, metal=1.0)
    tape_m = mat('lz_tape', 0x8e949b, rough=0.62, metal=0.12, tex=tex_tape('lz_tape_t', 0x8e949b))
    red_m = mat('lz_red', 0xe0201c, rough=0.35, clearcoat=0.4)
    blk_m = mat('lz_wire', 0x18181c, rough=0.4)
    glue_m = mat('lz_glue', 0xe6eef0, rough=0.08, clearcoat=1.0)
    zip_m = mat('lz_zip', 0x141418, rough=0.45, tex=tex_noise('lz_zip_t', 0x18181c, var=0.15, size=8, seed=14))
    btn_m = mat('lz_button', 0xff2d4a, rough=0.42, clearcoat=0.6)
    led_m = mat('lz_led', 0x1c6a14, rough=0.15, emit=0x39ff14, strength=1.5, clearcoat=1.0)  # own: the game lights them
    emit_m = mat('lz_emit', 0x39ff14, emit=0x39ff14, strength=2.0)  # own: the game brightens it
    glint_m = mat('lz_glint', 0xffffff, emit=0xe8fff0, strength=2.0)

    def glass_draw(px):  # the lens: deep green glass with the elements' rings in it
        px[:] = hexrgb(0x08200e)
        for r_, c_ in ((15.5, 0x16402a), (12, 0x0e3020), (8.5, 0x1a4a30), (6.5, 0x061a0c)):
            px_disc(px, 16, 16, r_, c_, r_in=r_ - 1.2)
    glass_m = mat('lz_glass', 0xffffff, rough=0.05, clearcoat=1.0, tex=tex_px('lz_glass_t', 32, 32, glass_draw))

    def warn_draw(px):  # 128 x 56: CAUTION / DO NOT STARE / INTO BEAM / CLASS 9000
        px[:] = hexrgb(0xffd400)
        px[2:4, 2:-2] = px[-4:-2, 2:-2] = hexrgb(0x111111); px[2:-2, 2:4] = px[2:-2, -4:-2] = hexrgb(0x111111)
        laser_symbol(px, 22, 29, 36, 0x111111, 0xffd400)
        text_px(px, 'CAUTION', 42, 6, 2, 0x111111)
        text_px(px, 'DO NOT STARE', 42, 23, 1, 0x111111)
        text_px(px, 'INTO BEAM.', 42, 32, 1, 0x111111)
        text_px(px, 'CLASS 9000', 42, 42, 1, 0xc01010)
    warn_m = mat('lz_warn', 0xffffff, rough=0.35, clearcoat=0.5, tex=tex_px('lz_warn_t', 128, 56, warn_draw))

    def apt_draw(px):  # 128 x 56, the aperture label: AVOID EXPOSURE / BEAM COMES OUT / THIS END  ->
        px[:] = hexrgb(0xffd400)
        px[2:4, 2:-2] = px[-4:-2, 2:-2] = hexrgb(0x111111); px[2:-2, 2:4] = px[2:-2, -4:-2] = hexrgb(0x111111)
        text_px(px, 'AVOID EXPOSURE', 7, 7, 1, 0x111111)
        text_px(px, 'BEAM COMES OUT', 7, 19, 1, 0x111111)
        text_px(px, 'THIS END', 7, 31, 2, 0xc01010)
        for d in range(-3, 4): px_line(px, 104, 38 + d * 0.2, 121, 38, 0x111111, 3.0) if d == 0 else None
        px_line(px, 112, 30, 121, 38, 0x111111, 3.0); px_line(px, 112, 46, 121, 38, 0x111111, 3.0)
    apt_m = mat('lz_apt', 0xffffff, rough=0.35, clearcoat=0.5, tex=tex_px('lz_apt_t', 128, 56, apt_draw))

    # the body print (white, alpha-clipped): MAX OUTPUT: YES
    ptxt = 'MAX OUTPUT: YES'
    pw, ph = text_w(ptxt) + 4, 11
    p3 = np.zeros((ph, pw, 3), np.float32); text_px(p3, ptxt, 2, 2, 1, 0xffffff)
    print_m = decal_mat('lz_print', rgba(np.where(p3.sum(2, keepdims=True) > 0, hexrgb(0xf4f0ff), 0), (p3.sum(2) > 0)), rough=0.3, clip=True)

    def meter_draw(px):  # 96 x 32: the module's face (top 24 rows) + plain black (the rest)
        px[:] = hexrgb(0x15151b)
        px[0:24, :] = hexrgb(0x1d1d25)
        text_px(px, 'PEW-O-METER', 15, 14, 1, 0xf0f0f0)
        for i in range(5):  # a tick under each LED (led0 is at the back = the right of the face as you see it)
            x = int(round((LED_Z[i] - 0.053) / 0.126 * 96)); px[22:24, x - 1:x + 1] = hexrgb(0x39ff14 if i == 0 else 0x9a9aa8)
        px[14:21, 2:8] = hexrgb(0x39ff14); px[14:21, 3:7] = hexrgb(0x1d1d25); px[16:19, 4:6] = hexrgb(0x39ff14)  # a little battery glyph
    meter_m = mat('lz_meter', 0xffffff, rough=0.35, clearcoat=0.6, tex=tex_px('lz_meter_t', 96, 32, meter_draw))

    def cell_draw(px):  # 64 (along, - end -> + end) x 48 (round): cyan wrap, black + end band, a big D and 1.5V both sides
        px[:] = hexrgb(0x3fcfff)
        px[:, 46:] = hexrgb(0x16161c)
        px[:, 44:46] = hexrgb(0xffe14d)
        def side_art(a):
            a[:] = 0
            text_px(a, 'D', 6, 4, 2, 0x16161c)
            text_px(a, '1.5V', 20, 8, 1, 0x16161c)
            text_px(a, '+', 50, 8, 1, 0xffffff)
        art = np.zeros((24, 64, 3), np.float32); side_art(art)
        mask = art.sum(2) > 0
        lower = px[24:48]; lower[mask] = art[mask]  # +x side: upright
        art2 = art[::-1, ::-1]; mask2 = mask[::-1, ::-1]
        upper = px[0:24]; upper[mask2] = art2[mask2]  # -x side: turned 180 (the label goes on round)
    cell_m = mat('lz_cell', 0xffffff, rough=0.3, clearcoat=0.7, tex=tex_px('lz_cell_t', 64, 48, cell_draw))

    def cat_draw(px):  # 32 x 32, the face (seen from +x): big hunting eyes, a pink nose, whiskers, blush
        px[:] = hexrgb(0xfafafa)
        for ex in (9, 22):
            px_disc(px, ex + 0.5, 15, 4.6, 0x141418); px_disc(px, ex - 0.8, 13.3, 1.6, 0xffffff); px_disc(px, ex + 1.8, 17, 0.8, 0xffffff)
        px_disc(px, 16, 20.5, 1.9, 0xff6fa8)
        px_line(px, 16, 22, 14, 24, 0x141418, 1); px_line(px, 16, 22, 18, 24, 0x141418, 1)
        for sx, x0 in ((-1, 6), (1, 26)):
            for dy in (-1.5, 1.0):
                px_line(px, x0, 21 + dy, x0 + sx * 5, 20 + dy * 1.8, 0x55555e, 1)
        px_disc(px, 5, 20, 2.2, 0xffb6d2); px_disc(px, 27, 20, 2.2, 0xffb6d2)
    cat_m = mat('lz_cat', 0xffffff, rough=0.28, clearcoat=0.8, tex=tex_px('lz_cat_t', 32, 32, cat_draw))
    pink_m = mat('lz_pink', 0xff8fc0, rough=0.35, clearcoat=0.5)
    gold_m = mat('lz_gold', 0xf2c040, rough=0.15, metal=1.0)
    collar_m = mat('lz_collar', 0xff3060, rough=0.4, clearcoat=0.4)  # the bell's ribbon

    A_, B_, N_ = [], [], []  # wrap zones: body + grip / chrome, tape, cells / stickers + labels
    btn_p, charm_p, emit_p, leds = [], [], [], [[] for _ in range(5)]
    def put(lst, o, name): o.name = name; lst.append(o); return o

    # ---------------- the pen: tail cap, anodized body, chrome switch collar, flared head with a knurled band
    tail = lathe([(0.0392, 0.2558), (0.0405, 0.2575), (0.0405, 0.2700), (0.0398, 0.2706), (0.0398, 0.2994), (0.0405, 0.3),
                  (0.0385, 0.3055), (0.032, 0.3145), (0.02, 0.3200), (0.0, 0.3215)], (0, 0, 0), chrome, seg=28, name='tail')
    put(B_, tail, 'tail')
    prof = [(0.0398, 0.2706)] + [((0.0411 if i % 2 else 0.0402), 0.2712 + i * 0.007) for i in range(5)] + [(0.0398, 0.2994)]
    put(B_, lathe(prof, (0, 0, 0), knurl, seg=28, cap=False, name='tail_knurl'), 'tail_knurl')
    put(B_, box((0.0042, 0.012, 0.009), (0, 0, 0.3235), chrome, bev=0.0012, seg=1), 'eyelet')
    put(B_, lathe([(0.0405, 0.2595), (0.0418, 0.2603), (0.0418, 0.2687), (0.0405, 0.2695)], (0, 0, 0), chrome, seg=28, cap=False, name='clip_ring'), 'clip_ring')
    body = lathe([(0.0395, 0.2555), (0.042, 0.2535), (0.042, -0.2965), (0.0412, -0.2985)], (0, 0, 0), body_m, seg=28, cap=False, name='body')
    put(A_, body, 'body')
    put(B_, lathe([(0.0418, -0.0425), (0.0446, -0.0455), (0.0446, -0.0945), (0.0418, -0.0975)], (0, 0, 0), chrome, seg=28, cap=False, name='collar'), 'collar')
    for z in (-0.0525,):  # a fine ring in the collar (by the button)
        put(B_, torus(0.0447, 0.0009, (0, 0, z), 'z', steel, seg=28, tseg=3), f'collar_ring{z}')
    head = lathe([(0.0405, -0.296), (0.0445, -0.2995), (0.0478, -0.3085), (0.0512, -0.3195), (0.0529, -0.3295), (0.053, -0.3345),
                  (0.0512, -0.3347)], (0, 0, 0), chrome, seg=28, cap=False, name='head')
    put(B_, head, 'head')
    put(B_, lathe([(0.0512, -0.3856), (0.053, -0.3858), (0.053, -0.392), (0.0512, -0.3988), (0.0468, -0.4038), (0.0438, -0.4072),
                   (0.0402, -0.4086), (0.0362, -0.4078), (0.0352, -0.4032)], (0, 0, 0), chrome, seg=28, cap=False, name='bezel_front'), 'bezel_front')
    prof = [(0.0515, -0.3347)]
    for i in range(9):
        prof.append((0.0534 if i % 2 == 0 else 0.0521, -0.3358 - i * 0.0061))
    prof.append((0.0515, -0.3856))
    hk = lathe(prof, (0, 0, 0), knurl, seg=28, cap=False, name='head_knurl')
    put(B_, hk, 'head_knurl')
    gl = lathe([(0.0353, -0.4031), (0.022, -0.4037), (0.0, -0.404)], (0, 0, 0), glass_m, seg=28, name='lens', cap=False)
    put(N_, gl, 'lens')
    put(N_, cyl(0.0042, 0.0004, (0.0125, 0.0125, -0.40425), glint_m, axis='z', seg=10), 'glint')
    em = cyl(0.0128, 0.0006, (0, 0, -0.4043), emit_m, axis='z', seg=20, name='emit')  # the emitter, just in front of the glass
    emit_p.append(em)

    # ---------------- the push button: a chrome bezel on the collar, the red rubber dome is its own node
    put(B_, lathe([(0.0192, 0.039), (0.0192, 0.0445), (0.0182, 0.047), (0.0168, 0.0478), (0.0142, 0.0478), (0.0138, 0.046), (0.0138, 0.0415)],
                  (0, 0, BTN[2]), chrome, seg=20, axis='y', cap=False, name='bezel'), 'bezel')
    put(N_, cyl(0.0138, 0.0016, (0, 0.0454, BTN[2]), dark, axis='y', seg=24), 'btn_well')
    dome = lathe([(0.0133, -0.0065), (0.0133, -0.001), (0.0127, 0.0022), (0.0112, 0.0046), (0.0084, 0.0064), (0.0045, 0.0072), (0.0, 0.0074)],
                 (0, 0, 0), btn_m, seg=20, axis='y', name='dome')
    dome.location = gv(*BTN)
    btn_p.append(dome)

    # ---------------- pocket clip (a pen clip: ring round the cap, a tapered arm with a rib, the ball at its tip)
    path = [(0, 0.0414, 0.2672), (0, 0.0452, 0.2598), (0, 0.0472, 0.2488), (0, 0.0476, 0.23), (0, 0.0476, 0.17), (0, 0.0474, 0.11),
            (0, 0.0468, 0.094), (0, 0.0458, 0.088)]
    def clip_ring(i, t):
        w = 0.0142 - 0.0046 * t; h = 0.0013
        return [(h, -w / 2), (h, -w * 0.18), (h + 0.0006, 0), (h, w * 0.18), (h, w / 2), (-h, w / 2), (-h, -w / 2)]
    clip = loft(path, clip_ring, chrome, 'clip', up=(0, 1, 0), smooth_angle=40)
    put(B_, clip, 'clip')
    put(B_, ball(0.0043, (0, 0.0449, 0.0855), chrome, scale=(1.05, 0.8, 1.3), seg=10, rings=6), 'clip_ball')

    # ---------------- split ring through the eyelet (two turns of flat wire)
    RC, RR = (0.0005, 0.3295), 0.0106
    hel = []
    for i in range(33):
        t = 4 * math.pi * i / 32 + 0.3
        hel.append((-0.0011 + 0.0022 * i / 32, RC[0] + RR * math.sin(t), RC[1] + RR * math.cos(t)))
    put(B_, sweep(hel, 0.0011, steel, seg=5, squash=(1.0, 0.75)), 'split_ring')

    # ---------------- the toy pistol grip: two clamshell halves (the seam shows), stippled panels, screws, the guard + trigger
    G = [(0.044, -0.03), (0.049, -0.044), (0.054, -0.068), (0.06, -0.11), (0.066, -0.15), (0.0715, -0.182), (0.0715, -0.195), (0.066, -0.205),
         (0.048, -0.2105), (0.02, -0.2075), (0.003, -0.2015), (-0.006, -0.192), (-0.009, -0.18), (-0.004, -0.169), (-0.004, -0.161),
         (-0.011, -0.15), (-0.008, -0.138), (-0.008, -0.131), (-0.014, -0.12), (-0.012, -0.108), (-0.014, -0.098), (-0.016, -0.09),
         (-0.017, -0.06), (-0.016, -0.03)]
    halves = []
    for sx in (-1, 1):
        h = side(G, 0.0168, (sx * 0.0086, 0, 0), grip_m, bev=0.0024, seg=2, name=f'grip{sx}')
        apply_mods(h)  # (rounded first: the screw holes stay crisp and cheap)
        halves.append(h)
    # screws on the right half (Phillips heads in deep bosses), hex nut pockets on the left
    SCR = [(0.044, -0.057), (0.055, -0.181), (0.007, -0.181)]
    for z, y in SCR:
        dcut(halves[1], cyl(0.0046, 0.006, (0.0172, y, z), dark, axis='x', seg=10))
        dcut(halves[0], cyl(0.0048, 0.006, (-0.0172, y, z), dark, axis='x', seg=6))
    put(A_, halves[0], 'grip_l'); put(A_, halves[1], 'grip_r')
    def screw_draw(px):
        px[:] = hexrgb(0xc0c4cc); px[3:5, 1:7] = hexrgb(0x2a2a30); px[1:7, 3:5] = hexrgb(0x2a2a30)
    screw_m = mat('lz_screw', 0xffffff, rough=0.25, metal=1.0, tex=tex_px('lz_screw_t', 8, 8, screw_draw))
    for i, (z, y) in enumerate(SCR):
        s = lathe([(0.0034, 0.0142), (0.0034, 0.0156), (0.0028, 0.0161), (0.0, 0.0163)], (0, y, z), screw_m, seg=12, axis='x', name='screw', cap=False)
        uv_dir(s, (0.016, y, z), (0, 0, -1), (0, 1, 0), 0.0068, 0.0068)
        put(N_, s, f'screw{i}')
        put(N_, cyl(0.0034, 0.0016, (-0.015, y, z), steel, axis='x', seg=6), f'nut{i}')
    PANEL = [(0.016 + 0.024 * math.cos(a) * (1 - 0.15 * math.sin(a)), -0.128 + 0.048 * math.sin(a)) for a in [2 * math.pi * k / 20 for k in range(20)]]
    PANEL = [(z + (y + 0.128) * -0.11, y) for z, y in PANEL]  # leans back with the grip
    for sx in (-1, 1):
        p = side(PANEL, 0.0014, (sx * 0.01695, 0, 0), panel_m, bev=0.0005, seg=1, name='panel')
        put(A_, p, f'panel{sx}')
    guard = [(-0.012, -0.0975), (-0.03, -0.1005), (-0.072, -0.0985), (-0.0905, -0.091), (-0.1005, -0.077), (-0.1035, -0.058),
             (-0.103, -0.036), (-0.0915, -0.036), (-0.0915, -0.057), (-0.089, -0.071), (-0.081, -0.081), (-0.068, -0.0875),
             (-0.03, -0.0895), (-0.012, -0.0885)]
    put(A_, side(guard, 0.0096, (0, 0, 0), grip_m, bev=0.002, seg=2, name='guard'), 'guard')
    trig = [(-0.0355, -0.036), (-0.0505, -0.036), (-0.0555, -0.047), (-0.0575, -0.0605), (-0.0555, -0.0745), (-0.0495, -0.0805),
            (-0.0465, -0.078), (-0.0485, -0.068), (-0.0475, -0.056), (-0.042, -0.046)]
    put(A_, side(trig, 0.0075, (0, 0, 0), trig_m, bev=0.0016, seg=2, name='trigger'), 'trigger')

    # ---------------- two D-cells, end to end under the front (+ ends forward), wired in, taped on
    def cell(z0, tag):
        z1 = z0 - 0.08
        put(B_, lathe([(0.0, z0), (0.0158, z0), (0.0194, z0 - 0.0006), (0.0214, z0 - 0.0018), (0.0222, z0 - 0.0036)], (0, CELL_Y, 0), steel, seg=20, name='cneg', cap=False), 'cneg' + tag)
        w = lathe([(0.0222, z0 - 0.0035), (0.0222, z1 + 0.0035)], (0, CELL_Y, 0), cell_m, seg=20, cap=False, name='cwrap')
        put(B_, w, 'cwrap' + tag)
        put(B_, lathe([(0.0222, z1 + 0.0036), (0.0207, z1 + 0.0011), (0.0164, z1), (0.0084, z1), (0.0078, z1 - 0.0058), (0.0, z1 - 0.0066)],
                      (0, CELL_Y, 0), steel, seg=20, name='cpos', cap=False), 'cpos' + tag)
        return w, z0, z1
    wa = cell(-0.112, 'a'); wb = cell(-0.1995, 'b')
    for w_, z0, z1 in (wa, wb):
        bpy.context.view_layer.update()
        me = w_.data; me.uv_layers.new(name='UVMap'); uvd = me.uv_layers.active.data
        for poly in me.polygons:
            ls = []
            for li in poly.loop_indices:
                v = w_.matrix_world @ me.vertices[me.loops[li].vertex_index].co
                gx, gy, gz = v.x, v.z - CELL_Y, -v.y
                ls.append([li, (gz - z0 + 0.0035) / (z1 - z0 + 0.007), (math.atan2(gy, gx) + math.pi / 2) / (2 * math.pi)])
            ref = ls[0][2]
            for e in ls:
                while e[2] - ref > 0.5: e[2] -= 1
                while e[2] - ref < -0.5: e[2] += 1
            for li, u, vv in ls: uvd[li].uv = (u, vv)
    # wires: red from the front + terminal into the head, black from the back - end into the body, hot glue on both
    put(B_, tube([(0.0, CELL_Y, -0.2852), (0.0008, -0.061, -0.2925), (0.003, -0.0548, -0.2985), (0.0045, -0.0488, -0.3068)], 0.0026, red_m, seg=8), 'wire_red')
    put(B_, tube([(0.0, CELL_Y, -0.1115), (-0.001, -0.0628, -0.1062), (-0.004, -0.0545, -0.1018), (-0.0052, -0.0428, -0.1005)], 0.0026, blk_m, seg=8), 'wire_blk')
    for i, (p, sc) in enumerate((((0.0046, -0.0478, -0.3085), (1.4, 0.8, 1.2)), ((-0.0052, -0.0425, -0.1002), (1.3, 0.75, 1.2)), ((0.0, CELL_Y, -0.2857), (0.9, 0.9, 0.6)))):
        b = ball(0.0058, p, glue_m, scale=sc, seg=10, rings=6); jitter(b, 0.0007, seed=20 + i)
        put(B_, b, f'glue{i}')

    # ---------------- tape: round the pen + the grip's top (two bands), round the pen + the cells (two bands, one peeling)
    pen_c = circle_pts((0, 0), R_BODY, 64)
    grip_o = hull2d(pen_c + [(sx * 0.0171, y) for sx in (-1, 1) for y in (-0.03, -0.0585)])
    cell_o = hull2d(pen_c + circle_pts((0, CELL_Y), CELL_R, 40))
    put(B_, band(grip_o, 0.0005, 0.022, tape_m, 'tape_g1', n=40, across=2, start=math.radians(60), seed=2), 'tape_g1')
    put(B_, band(grip_o, 0.0345, 0.022, tape_m, 'tape_g2', n=40, across=2, start=math.radians(110), seed=3), 'tape_g2')
    put(B_, band(cell_o, -0.132, 0.024, tape_m, 'tape_c1', n=40, start=math.radians(70), seed=4), 'tape_c1')
    put(B_, band(cell_o, -0.266, 0.024, tape_m, 'tape_c2', n=40, start=math.radians(92), seed=5, lift=0.0045, turns=1.22), 'tape_c2')

    # ---------------- the PEW-O-METER: a little black bar-graph module on the side you see, zip-tied on
    th = LED_TH
    radial = Vector((math.cos(th), math.sin(th), 0)); upv = Vector((math.sin(th), -math.cos(th), 0))  # out of the pen / toward its top
    def at(rad, up, z): p = radial * rad + upv * up; return (p.x, p.y, z)
    rot = (0, 0, th - math.pi)
    mod = box((0.016, 0.031, 0.126), at(0.0435, 0, 0.116), meter_m, bev=0.0022, rot=rot, name='meter')
    apply_mods(mod)
    face_c = Vector(at(0.0515, 0, 0.116))
    uv_dir(mod, face_c, (0, 0, 1), tuple(upv), 0.126, 0.031, nrm=tuple(radial), rect=(0, 1 / 4, 1, 1), plain=(0, 0, 1, 0.2))
    put(N_, mod, 'meter')
    for i, z in enumerate(LED_Z):
        l = box((0.004, 0.0105, 0.0158), at(0.0517, 0.0042, z), led_m, bev=0.0016, seg=1, rot=rot, name=f'led{i}')
        leds[i].append(l)
        put(N_, box((0.0014, 0.0128, 0.018), at(0.0515, 0.0042, z), dark, rot=rot), f'led_bezel{i}')
    mod_o = hull2d(pen_c + [tuple(radial * r_ + upv * u_)[:2] for r_ in (0.0355, 0.0515) for u_ in (-0.0155, 0.0155)])
    put(B_, band(mod_o, 0.1745, 0.0046, zip_m, 'zip', turns=1.0, tt=0.0013, n=36, across=2, start=math.radians(205), seed=6, wrinkle=0.0, torn=False, tex_len=0.02), 'zip')
    zh = Vector((math.cos(math.radians(205)), math.sin(math.radians(205)), 0)) * 0.0445
    put(B_, box((0.0068, 0.0056, 0.0072), (zh.x, zh.y, 0.1745), zip_m, bev=0.0008, rot=(0, 0, math.radians(205) - math.pi / 2)), 'zip_head')
    tail_d = Vector((math.cos(math.radians(205)), math.sin(math.radians(205)), 0))
    put(B_, box((0.005, 0.0013, 0.0044), (zh.x + tail_d.x * 0.0046, zh.y + tail_d.y * 0.0046, 0.1745), zip_m, rot=(0, 0, math.radians(205))), 'zip_tail')  # the cut end
    rb = [at(0.046, -0.01, 0.0535), at(0.0442, -0.013, 0.047), at(0.0418, -0.016, 0.039)]  # its cable, under the grip tape
    put(B_, sweep(rb, 0.0018, blk_m, seg=6, squash=(0.45, 1.6)), 'meter_cable')

    # ---------------- stickers + print: warning (the side you see), aperture label + MAX OUTPUT: YES (the other side)
    t0, t1 = math.radians(150) - 0.55, math.radians(150) + 0.55
    put(N_, patch(0.0427, 0.0414, -0.252, -0.146, t0, t1, warn_m, lambda a, b: (a, 1 - b), 'warn'), 'warn')  # -x viewer: right = +z, up = toward the top
    t0, t1 = math.radians(12) - 0.55, math.radians(12) + 0.55
    put(N_, patch(0.0427, 0.0414, -0.252, -0.146, t0, t1, apt_m, lambda a, b: (1 - a, b), 'apt'), 'apt')  # +x viewer: right = -z
    t0, t1 = math.radians(4) - 0.19, math.radians(4) + 0.19
    put(N_, patch(0.04245, 0.0414, 0.054, 0.166, t0, t1, print_m, lambda a, b: (1 - a, b), 'bprint', nz=4, nth=3), 'bprint')

    # ---------------- the cat charm (its own node, origin on the split ring): jump ring, two links, the cat, a bell
    c0 = Vector(CHARM)
    def cp(x, y, z): return (c0.x + x, c0.y + y, c0.z + z)
    charm_p.append(torus(0.0042, 0.0011, cp(0, -0.0036, 0), 'z', steel, seg=10, tseg=4, name='jump'))
    charm_p.append(torus(0.0033, 0.0009, cp(0, -0.0098, 0), 'x', steel, seg=10, tseg=4, name='link1'))
    charm_p.append(torus(0.0033, 0.0009, cp(0, -0.0152, 0), 'z', steel, seg=10, tseg=4, name='link2'))
    charm_p.append(torus(0.003, 0.0009, cp(0, -0.0205, 0), 'x', steel, seg=10, tseg=4, name='bail'))
    hc = cp(0, -0.0395, 0)
    head = ball(0.0166, hc, cat_m, scale=(0.84, 0.94, 1.17), seg=16, rings=10, name='cathead')
    uv_dir(head, hc, (0, 0, -1), (0, 1, 0), 0.039, 0.0312, nrm=(1, 0, 0), rect=(0, 0, 1, 1), plain=(0.02, 0.9, 0.12, 0.98))
    charm_p.append(head)
    def ear(sz, inset, thick, m, nm):  # a rounded triangle standing on the head, tips leaning out; front face toward +x
        y0, zc = -0.0395 + 0.0104, sz * 0.0098
        tri = [(zc - 0.0064 * (1 - inset), y0 + inset * 0.002), (zc + 0.0064 * (1 - inset), y0 + inset * 0.002), (zc + sz * 0.0036 * (1 - inset * 0.5), y0 + 0.0128 * (1 - inset * 0.45))]
        bm = bmesh.new()
        xs = (0.0006 + thick, 0.0006) if inset else (0.0034, -0.0034)
        rings = [[bm.verts.new(gv(c0.x + x_, c0.y + y_, c0.z + z_)) for z_, y_ in tri] for x_ in xs]
        bm.faces.new(rings[0]); bm.faces.new(rings[1][::-1])
        for i in range(3):
            j = (i + 1) % 3
            bm.faces.new((rings[0][i], rings[0][j], rings[1][j], rings[1][i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        o = lib._obj(nm, bm, m); smooth(o, 30); bevel(o, 0.0011 if not inset else 0.0004, 2, 30)
        return o
    for sz in (-1, 1):
        e = ear(sz, 0.0, 0.0, cat_m, 'ear'); apply_mods(e)
        uv_dir(e, hc, (0, 0, -1), (0, 1, 0), 0.5, 0.5, rect=(0.02, 0.9, 0.06, 0.94))
        charm_p.append(e)
        charm_p.append(ear(sz, 0.3, 0.0034 + 0.0006, pink_m, 'inear'))
    charm_p.append(torus(0.0022, 0.0008, cp(0.006, -0.0535, 0), 'z', collar_m, seg=8, tseg=4, name='bell_ring'))
    charm_p.append(ball(0.0046, cp(0.0062, -0.0592, 0), gold_m, seg=10, rings=6, name='bell'))
    charm_p.append(cyl(0.0016, 0.0005, cp(0.0106, -0.0598, 0), dark, axis='x', seg=8, name='bell_slot'))

    allp = A_ + B_ + N_ + btn_p + charm_p + emit_p + [l for L in leds for l in L]
    for p in allp:
        apply_mods(p)
        if p.name.startswith('wire_'): weld(p, 1e-6)
        if p.data.uv_layers: continue
        if p in (body,): continue
        uv_box(p, 0.03)
    uv_cylz(body, 0.2555, -0.2985, su=6.0, sv=2.0)
    for k in (hk,):
        uv_cylz(k, -0.3347, -0.3856, su=4.0, sv=24.0)
    for p in allp:
        if p.name == 'tail_knurl': uv_cylz(p, 0.2706, 0.2994, su=2.2, sv=20.0)
        fix_zero_uv(p)
    if '--qa' in sys.argv: qa(allp)
    if '--parts' in sys.argv:  # where the triangles go
        cnt = []
        for p in allp:
            me = p.data; me.calc_loop_triangles(); cnt.append((len(me.loop_triangles), p.name))
        print('JF_PARTS', sorted(cnt, reverse=True)[:40])

    WZ = {'lz_body': 'a', 'lz_grip': 'a', 'lz_panel': 'a', 'lz_trig': 'a', 'lz_warn': 'n', 'lz_apt': 'n', 'lz_print': 'n', 'lz_meter': 'n',
          'lz_glass': 'n', 'lz_glint': 'n', 'lz_dark': 'n', 'lz_screw': 'n'}
    bodies = zone_join(A_ + B_ + N_, 'lz_body', WZ, default='b')
    bnode = part(btn_p, 'lz_button_wzN', pivot=BTN)
    cnode = part(charm_p, 'lz_charm_wzN', pivot=CHARM)
    enode = part(emit_p, 'lz_emit_wzN', pivot=(0, 0, -0.4043))
    lnodes = [part(leds[i], f'lz_led{i}_wzN', pivot=at(0.0517, 0.0042, z)) for i, z in enumerate(LED_Z)]
    meta = {'kind': 'weapon', 'id': 'laser', 'paint': ['lz_grip'], 'muzzle': [0, 0, -0.42],
            'hatAt': [[0, 0.0425, -0.2], 0.08],
            # the charge hooks, for public/js/laserglb.js (it binds them on any Blender laser: this one or a skin)
            'laser': {'button': 'lz_button_wzN', 'leds': [n.name for n in lnodes], 'emit': 'lz_emit_wzN', 'charm': 'lz_charm_wzN'}}
    print('JF_META', json.dumps(meta))
    return finish('w_laser', bodies + [bnode, cnode, enode] + lnodes, meta)


def qa(parts):
    """the blender-asset-qa gate on every part before the joins (so a finding names the part): z-fight eps 0.2 mm
    (stickers stand 0.7 mm proud on purpose), contact 0.6 mm"""
    sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    for p in parts: apply_mods(p)
    res = qa_check.run(objects=[p.name for p in parts], profile='game', eps=0.0002, tol=0.0006)
    print('QA_PASS', res.get('pass'))
    for k in ('errors', 'warnings'):
        for e in res.get(k, []): print('QA_' + k.upper()[:-1], e)
    for n, m in res.get('objects', {}).items():
        bad = {k: v for k, v in m.items() if k in ('degenerate_faces', 'zero_length_edges', 'nonmanifold_edges', 'inconsistent_normals_edges', 'inside_out_islands', 'duplicate_verts') and v}
        if bad: print('QA_PART', n, m.get('tris'), bad)


main(build, 'w_laser')
