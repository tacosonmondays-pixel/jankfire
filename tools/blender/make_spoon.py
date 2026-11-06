# Spoon + the Ladle skin.
# Spoon: a stainless tablespoon (200 mm: an egg-shaped bowl 45 x 70 mm, 12 mm deep; a narrow neck that dips into the
# bowl; a flat handle that widens to a rounded 23 mm end and lifts a little) x1.15 into the code spoon's 0.23 m.
# Mirror polished. Made fun: PROPERTY OF THE CAFETERIA stamped along the handle.
# Ladle: a stainless soup ladle (a 90 mm hemisphere bowl with a rolled rim, a flat handle rising out of it, a hook on
# the end) at the code ladle's size. Made fun: SOUP stamped on it, with a dent.
# run: blender -b --python tools/blender/make_spoon.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj


def smooth01(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)


def shell(centre, rx, ry, rz, m, egg=0.0, seg=24, rings=16, thick=0.0015, name='bowl', dent=None):
    """the lower half of an ellipsoid as a thin metal shell (a spoon or ladle bowl). egg > 0 widens it toward -z."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 1e-5], context='VERTS')
    for v in bm.verts:
        x, y, z = v.co.x, v.co.z, -v.co.y  # unit sphere, game axes
        k = 1 + egg * (-z)
        gx, gy, gz = x * rx * k, y * ry, z * rz
        if dent:  # a dent: push the shell in round a point
            dx, dy, dz, r, d = dent
            q = math.exp(-((gx - dx) ** 2 + (gy - dy) ** 2 + (gz - dz) ** 2) / (r * r))
            gx, gy, gz = gx * (1 - d * q), gy * (1 - d * q), gz
        v.co = gv(centre[0] + gx, centre[1] + gy, centre[2] + gz)
    o = _obj(name, bm, m)
    for p in o.data.polygons: p.use_smooth = True
    md = o.modifiers.new('solid', 'SOLIDIFY'); md.thickness = thick; md.offset = -1.0; md.use_even_offset = True
    apply_mods(o)
    return o


def stamp_px(text, w, h, base, ink):
    def draw(px):
        px[:] = hexrgb(base)
        r = np.random.default_rng(len(text))
        px[:] *= (0.97 + 0.05 * r.random((h, w, 1)))
        text_px(px, text, 2, (h - 7) // 2, 1, ink)
    return draw


def stamp_faces(o, mat_index, z0, z1, axis_len, x_half):
    """give the handle's top faces between z0..z1 the stamp material, uvs along -z (letters' up = +x)"""
    me = o.data
    uvl = (me.uv_layers.active or me.uv_layers.new()).data
    for f in me.polygons:
        c = f.center; n = f.normal
        gz, gny = -c.y, n.z
        if gny > 0.6 and z0 <= gz <= z1:
            f.material_index = mat_index
            for li in f.loop_indices:
                v = me.vertices[me.loops[li].vertex_index].co
                uvl[li].uv = ((z1 - (-v.y)) / axis_len, (v.x + x_half) / (2 * x_half))


def spoon():
    steel = mat('sp_steel', 0xdfe3ea, rough=0.1, metal=1.0)
    stamp = mat('sp_stamp', 0xffffff, rough=0.2, metal=1.0, tex=tex_canvas('sp_stamp_t', 116, 11, stamp_px('PROPERTY OF THE CAFETERIA', 116, 11, 0xdfe3ea, 0x6a7078)))
    Z_END, Z_NECK, Z_BOWL = 0.058, -0.078, -0.128
    N, K = 40, 16
    zs = [Z_END + (Z_NECK - Z_END) * i / (N - 1) for i in range(N)]
    def width(z):
        if z > 0.034: return 0.026 * math.sqrt(max(0.0, 1 - ((z - 0.034) / 0.024) ** 2))
        return 0.0085 + (0.026 - 0.0085) * smooth01(-0.07, 0.03, z)
    def thick(z): return 0.0026 + 0.0008 * smooth01(0.0, -0.07, z)
    def yc(z): return 0.006 * ((z - Z_NECK) / (Z_END - Z_NECK)) ** 2 - 0.006 * smooth01(-0.045, Z_NECK, z)
    def ring(i, t):
        z = zs[i]; w = max(width(z), 0.0006); th = thick(z); out = []
        for j in range(K):
            a = 2 * math.pi * j / K; c, s = math.cos(a), math.sin(a)
            out.append((th / 2 * math.copysign(abs(s) ** 0.4, s), w / 2 * math.copysign(abs(c) ** 0.4, c)))
        return out
    handle = loft([(0, yc(z), z) for z in zs], ring, m=steel, name='handle', close=(True, False), smooth_angle=50)
    handle.data.materials.append(stamp)
    stamp_faces(handle, 1, -0.052, 0.046, 0.098, 0.013)
    bowl = shell((0, -0.0055, Z_BOWL), 0.0255, 0.0125, 0.049, steel, egg=0.1, name='bowl')
    WZ = {'sp_steel': 'b'}
    meta = {'kind': 'weapon', 'id': 'spoon', 'paint': [], 'muzzle': [0, 0, -0.17], 'hatAt': [[0, 0.004, 0.02], 0.04]}
    return finish('w_spoon', zone_join([handle], 'spoon_handle', {'sp_steel': 'a'}) + zone_join([bowl], 'spoon_bowl', WZ), meta)


def ladle():
    steel = mat('ld_steel', 0xd2d7de, rough=0.16, metal=1.0)
    stamp = mat('ld_stamp', 0xffffff, rough=0.25, metal=1.0, tex=tex_canvas('ld_stamp_t', 40, 11, stamp_px('SOUP', 40, 11, 0xd2d7de, 0x5a6068)))
    C = (0, -0.034, -0.168); R = 0.047
    bowl = shell(C, R, 0.042, R, steel, seg=28, rings=16, thick=0.0016, name='ladle_bowl', dent=(0.03, -0.03, -0.02, 0.014, 0.12))
    rim = lathe([(R + 0.0012, -0.0016), (R + 0.0024, 0.0), (R + 0.0012, 0.0016), (R - 0.0004, 0.0)], (C[0], C[1], C[2]), steel, seg=28, axis='y', name='rim')
    # the handle: leaves the back of the rim, climbs, runs back flat, hooks down at the end
    path = [(0, C[1] + 0.002, C[2] + R - 0.002), (0, -0.018, -0.105), (0, -0.004, -0.07), (0, 0.004, -0.03), (0, 0.009, 0.02),
            (0, 0.012, 0.07), (0, 0.012, 0.098), (0, 0.007, 0.11), (0, -0.002, 0.116), (0, -0.011, 0.117)]
    pts = []
    for a, b in zip(path, path[1:]):
        for k in range(6): t = k / 6; pts.append(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))
    pts.append(path[-1])
    W = [0.011 + 0.006 * smooth01(-0.1, 0.06, p[2]) - 0.007 * smooth01(0.09, 0.112, p[2]) * (1 if p[1] < 0.011 else 0.5) for p in pts]
    K = 12
    def ring(i, t):
        w = W[i]; th = 0.0028; out = []
        for j in range(K):
            a = 2 * math.pi * j / K; c, s = math.cos(a), math.sin(a)
            out.append((th / 2 * math.copysign(abs(s) ** 0.4, s), w / 2 * math.copysign(abs(c) ** 0.4, c)))
        return out
    hd = loft(pts, ring, m=steel, name='ladle_handle', smooth_angle=50)
    hd.data.materials.append(stamp)
    stamp_faces(hd, 1, 0.0, 0.06, 0.06, 0.0085)
    meta = {'kind': 'weapon', 'id': 'spoon', 'skin': 'spoon_ladle', 'paint': [], 'muzzle': [0, 0, -0.17], 'hatAt': [[0, 0.016, 0.04], 0.045]}
    return finish('w_spoon_ladle', zone_join([hd], 'ladle_handle', {'ld_steel': 'a'}) + zone_join([bowl, rim], 'ladle_bowl', {'ld_steel': 'b'}), meta)


main_multi(lambda: [(spoon(), 'w_spoon'), (ladle(), 'w_spoon_ladle')], exposure=-0.4)
