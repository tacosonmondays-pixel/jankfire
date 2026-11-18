# Ray-blind over the roofs (18 Nov 2026, the main session for the owner: "make the invisible columns ray-blind above
# each inner building's real roof. A rope or a bullet stopping in thin air over a roof reads as a bug ... Keep them
# collide-only up to 150, so nobody walks over buildings that were walled before").
#
# A walled arena's buildings stand solid to the old lid (150, the layouts' LID) so nobody gets on their roofs. Their hit
# boxes took ropes and shots all the way up, so a rope aimed just over a roof bit thin air. Run inside <map>_models.py
# (Blender, after the kit is built, before write_layout): every hit box that reaches the lid (not the wall box's own
# 'bound' and 'ledge') is measured against the kit's real geometry over it (a grid of rays down onto the kit's meshes)
# and becomes:
#   * up to three layers that take ropes and shots, wrapping the real roof: the whole footprint up to the eaves (the
#     low 15% of the roof), the part above the eaves up to the middle of what's there, the part above that up to the top
#     (domes, lanterns, ridges). nothing you can see lets a rope through (bar a sliver of a stud at a layer's edge).
#   * one box from the eaves to the lid that stops bodies and takes nothing (flag 'c', CanQuery off): rays pass.
import math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

STEP = 2.0          # studs between the rays
SKIP = ('_far', 'heart')   # the far silhouettes (look only, far away) and the Gut's hearts (only one is installed)


def _tree(pieces):
    verts, polys = [], []
    for (model, key), items in pieces.items():
        if any(s in model for s in SKIP): continue
        for bm, M in items:
            bm.verts.index_update()
            base = len(verts)
            for v in bm.verts: verts.append(M @ v.co)
            for f in bm.faces: polys.append([base + v.index for v in f.verts])
    return BVHTree.FromPolygons(verts, polys), len(polys)


def _q(vals, f):
    s = sorted(vals)
    return s[min(len(s) - 1, max(0, int(f * (len(s) - 1) + 0.5)))]


def _layers(tree, cx, cz, hx, hz, yaw, y0, y1):
    """sample the footprint (local half sizes hx, hz about cx, cz, turned by yaw degrees as CFrame.Angles(0, yaw, 0));
    returns the eaves height and the hookable layers [(lx0, lz0, lx1, lz1, top)] in local coordinates"""
    t = math.radians(yaw)
    c, s = math.cos(t), math.sin(t)
    nx, nz = max(1, int(round(2 * hx / STEP))), max(1, int(round(2 * hz / STEP)))
    cells = []
    for i in range(nx):
        for j in range(nz):
            lx = -hx + (i + 0.5) * 2 * hx / nx
            lz = -hz + (j + 0.5) * 2 * hz / nz
            wx, wz = cx + lx * c + lz * s, cz - lx * s + lz * c       # (local x = (c, 0, -s), local z = (s, 0, c))
            hit = tree.ray_cast(Vector((wx, y1 - 0.05, wz)), Vector((0, -1, 0)), y1 - y0)
            h = hit[0].y if hit[0] is not None else y0
            cells.append((lx, lz, h))
    seen = [h for (_, _, h) in cells if h > y0 + 0.3]
    if not seen: return y0, []
    out = []
    eaves = _q([h for (_, _, h) in cells], 0.15)
    if eaves > y0 + 0.5: out.append((-hx, -hz, hx, hz, eaves))
    floor_ = eaves
    for frac in (0.5, 1.0):
        up = [(lx, lz, h) for (lx, lz, h) in cells if h > floor_ + 1.0]
        if not up: break
        top = _q([h for (_, _, h) in up], frac) if frac < 1.0 else max(h for (_, _, h) in up)
        hxs, hzs = hx / nx, hz / nz                                  # (a cell's half size)
        out.append((max(-hx, min(u[0] for u in up) - hxs), max(-hz, min(u[1] for u in up) - hzs),
                    min(hx, max(u[0] for u in up) + hxs), min(hz, max(u[1] for u in up) + hzs), top))
        floor_ = top
    return eaves, out


def split(solid, rot, lid, pieces):
    """solid: [(x0, y0, z0, x1, y1, z1, material, colour, web mat)]; rot: [(cx, cy, cz, sx, sy, sz, yaw, material, colour,
    web mat, flags)] (what write_layout takes). returns both with every lid-high box split, and what it did"""
    tree, ntri = _tree(pieces)
    s_out, r_out, n, made = [], [], 0, 0
    for b in solid:
        x0, y0, z0, x1, y1, z1 = b[:6]
        if y1 < lid - 0.01 or b[8] in ('bound', 'ledge'):
            s_out.append(b); continue
        n += 1
        cx, cz, hx, hz = (x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) / 2, (z1 - z0) / 2
        eaves, lay = _layers(tree, cx, cz, hx, hz, 0.0, y0, y1)
        for (a0, c0, a1, c1, top) in lay:
            s_out.append((cx + a0, y0, cz + c0, cx + a1, top, cz + c1) + tuple(b[6:9])); made += 1
        lo = max(eaves, y0)
        r_out.append((cx, (lo + y1) / 2, cz, x1 - x0, y1 - lo, z1 - z0, 0.0) + tuple(b[6:9]) + ('c',)); made += 1
    for r in rot:
        cx, cy, cz, sx, sy, sz, yaw = r[:7]
        y0, y1 = cy - sy / 2, cy + sy / 2
        if y1 < lid - 0.01 or r[9] in ('bound', 'ledge') or 'c' in (r[10] or ''):
            r_out.append(r); continue
        n += 1
        eaves, lay = _layers(tree, cx, cz, sx / 2, sz / 2, yaw, y0, y1)
        t = math.radians(yaw); c, s = math.cos(t), math.sin(t)
        for (a0, c0, a1, c1, top) in lay:
            lx, lz = (a0 + a1) / 2, (c0 + c1) / 2
            r_out.append((cx + lx * c + lz * s, (y0 + top) / 2, cz - lx * s + lz * c, a1 - a0, top - y0, c1 - c0, yaw) + tuple(r[7:10]) + ('',)); made += 1
        lo = max(eaves, y0)
        r_out.append((cx, (lo + y1) / 2, cz, sx, y1 - lo, sz, yaw) + tuple(r[7:10]) + ('c',)); made += 1
    info = '%d lid-high boxes over %d kit triangles -> %d boxes (layers that take ropes, and the ray-blind rest)' % (n, ntri, made)
    return s_out, r_out, info
