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


# ---------------------------------------------------------------------------------------------------------------------
# Open roofs (18 Nov 2026, the owner: "Suburb we should be able to get on roofs, gut map too!! There are weird ceiling
# blockers"). Instead of split(): every lid-high box (not the wall box's 'bound' and 'ledge') becomes the shape of the
# kit over it and nothing above, so you can land on, walk on and fight from the roofs. Rays every CELL studs straight
# down onto the kit give a height map; heights go to the nearest Q (a pitched roof or a dome becomes steps Q high, all
# within Q/2 of the mesh, low enough to walk up); runs of equal height merge into boxes (strips along a ridge). Each box
# stands from the old box's foot to its height, so the walls under the roof stay solid.
#   * a cell nothing was found over (or only the ground) stays open when it joins the footprint's rim (a round tower's
#     corners, a gap): the hit boxes follow what you see. one walled in by roof (a light well) is filled at the lowest
#     roof height round it, so nobody drops into a building that isn't there
#   * a footprint with nothing over it at all keeps its box as it was (and says so)
# returns (solid, rot, info); TOPS (module) gets the roof boxes' tops for the sight-line check (tools/roblox/roof_sight.py)
CELL = 1.0
Q = 0.5
UNDER = 8.0      # studs under a raised box's foot that still count as its roof closing it (see _grid)
TOPS = []


def _grid(tree, cx, cz, hx, hz, yaw, y0, y1, cell):
    t = math.radians(yaw)
    c, s = math.cos(t), math.sin(t)
    nx, nz = max(1, int(round(2 * hx / cell))), max(1, int(round(2 * hz / cell)))
    cw, ch = 2 * hx / nx, 2 * hz / nz
    G = [[None] * nz for _ in range(nx)]
    for i in range(nx):
        for j in range(nz):
            lx, lz = -hx + (i + 0.5) * cw, -hz + (j + 0.5) * ch
            wx, wz = cx + lx * c + lz * s, cz - lx * s + lz * c       # (local x = (c, 0, -s), local z = (s, 0, c))
            hit = tree.ray_cast(Vector((wx, y1 - 0.05, wz)), Vector((0, -1, 0)), y1 - y0)
            if hit[0] is not None and hit[0].y > y0 + 0.5:
                G[i][j] = hit[0].y
            elif y0 > 1.0:
                # (a box standing on something, not the street: the Gut's Tube roof from 18, a house's roof from 24. the kit
                # dipping just under its foot (a barrel vault's side meeting a wall: the v812 test fell through there) is
                # still a closed roof: a plate at the foot. nothing under it within UNDER: open, as over the street)
                low = tree.ray_cast(Vector((wx, y0 + 0.4, wz)), Vector((0, -1, 0)), UNDER)
                if low[0] is not None:
                    G[i][j] = y0 + 0.5
    return G, nx, nz, cw, ch


def _fill_wells(G, nx, nz):
    """cells with nothing over them that the rim can't reach through other empty cells: filled at the lowest roof round"""
    seen = [[False] * nz for _ in range(nx)]
    stack = [(i, j) for i in range(nx) for j in range(nz) if (i in (0, nx - 1) or j in (0, nz - 1)) and G[i][j] is None]
    for (i, j) in stack: seen[i][j] = True
    while stack:
        i, j = stack.pop()
        for (a, b) in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
            if 0 <= a < nx and 0 <= b < nz and not seen[a][b] and G[a][b] is None:
                seen[a][b] = True; stack.append((a, b))
    hits = [G[i][j] for i in range(nx) for j in range(nz) if G[i][j] is not None]
    low = min(hits) if hits else None
    wells = 0
    for i in range(nx):
        for j in range(nz):
            if G[i][j] is None and not seen[i][j] and low is not None:
                G[i][j] = low; wells += 1
    return wells


def _rects(G, nx, nz, tol):
    """runs of heights at most tol apart merged into rectangles: (i, j, w, h, the highest of them: you never sink into
    the mesh, you stand at most tol over it)"""
    used = [[False] * nz for _ in range(nx)]
    out = []
    for j in range(nz):
        for i in range(nx):
            v = G[i][j]
            if used[i][j] or v is None: continue
            lo = hi = v
            w = 1
            while i + w < nx and not used[i + w][j] and G[i + w][j] is not None and max(hi, G[i + w][j]) - min(lo, G[i + w][j]) <= tol + 1e-6:
                lo, hi = min(lo, G[i + w][j]), max(hi, G[i + w][j]); w += 1
            h = 1
            while j + h < nz:
                row = [G[i + k][j + h] for k in range(w)]
                if any(used[i + k][j + h] for k in range(w)) or any(x is None for x in row): break
                nlo, nhi = min(lo, min(row)), max(hi, max(row))
                if nhi - nlo > tol + 1e-6: break
                lo, hi = nlo, nhi; h += 1
            for a in range(i, i + w):
                for b in range(j, j + h): used[a][b] = True
            out.append((i, j, w, h, hi))
    return out


def open_up(solid, rot, lid, pieces, cell=CELL, q=Q, tol=0.0, slide=None):
    """cell: studs between rays; q: height steps; tol: heights this far apart share a box (fewer boxes on curved roofs).
    slide(cx, cz, y0) -> True: a roof nobody may stay on (over a spawn): its boxes go out turned (yaw 0 for a plain one)
    with the flag "s", and WebArena marks them Slide: Move.client slides you off toward the middle, like the wall box's
    ledge. you can still hook it, land on it, touch it; there's no ceiling over it"""
    tree, ntri = _tree(pieces)
    s_out, r_out = [], []
    n, made, kept, wells, twins, slid = 0, 0, 0, 0, 0, 0
    del TOPS[:]
    done = set()   # (a round building is several turned squares on one centre: the first one sampled covers it)
    for b in solid:
        x0, y0, z0, x1, y1, z1 = b[:6]
        if y1 < lid - 0.01 or b[8] in ('bound', 'ledge'):
            s_out.append(b); continue
        n += 1
        cx, cz, hx, hz = (x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) / 2, (z1 - z0) / 2
        G, nx, nz, cw, ch = _grid(tree, cx, cz, hx, hz, 0.0, y0, y1, cell)
        if all(G[i][j] is None for i in range(nx) for j in range(nz)):
            s_out.append(b); kept += 1; continue
        wells += _fill_wells(G, nx, nz)
        sl = slide is not None and slide(cx, cz, y0)
        qq, tt = (max(q, 1.0), max(tol, 3.0)) if sl else (q, tol)     # (a roof that sheds you: nobody stands on it, coarser)
        for i in range(nx):
            for j in range(nz):
                if G[i][j] is not None: G[i][j] = round(G[i][j] / qq) * qq
        for (i, j, w, h, top) in _rects(G, nx, nz, tt):
            a0, c0 = x0 + i * cw, z0 + j * ch
            if sl:
                r_out.append((a0 + w * cw / 2, (y0 + top) / 2, c0 + h * ch / 2, w * cw, top - y0, h * ch, 0.0) + tuple(b[6:9]) + ('s',)); slid += 1
            else:
                s_out.append((a0, y0, c0, a0 + w * cw, top, c0 + h * ch) + tuple(b[6:9]))
                TOPS.append(('s', a0, c0, a0 + w * cw, c0 + h * ch, 0.0, top))
            made += 1
    for r in rot:
        cx, cy, cz, sx, sy, sz, yaw = r[:7]
        y0, y1 = cy - sy / 2, cy + sy / 2
        if y1 < lid - 0.01 or r[9] in ('bound', 'ledge') or 'c' in (r[10] or ''):
            r_out.append(r); continue
        n += 1
        key = (round(cx, 2), round(cz, 2), round(sx, 2), round(sz, 2), round(y0, 2), round(y1, 2))
        if key in done: twins += 1; continue
        done.add(key)
        hx, hz = sx / 2, sz / 2
        G, nx, nz, cw, ch = _grid(tree, cx, cz, hx, hz, yaw, y0, y1, cell)
        if all(G[i][j] is None for i in range(nx) for j in range(nz)):
            r_out.append(r); kept += 1; continue
        wells += _fill_wells(G, nx, nz)
        sl = slide is not None and slide(cx, cz, y0)
        qq, tt = (max(q, 1.0), max(tol, 3.0)) if sl else (q, tol)
        for i in range(nx):
            for j in range(nz):
                if G[i][j] is not None: G[i][j] = round(G[i][j] / qq) * qq
        t = math.radians(yaw); c, s = math.cos(t), math.sin(t)
        for (i, j, w, h, top) in _rects(G, nx, nz, tt):
            lx, lz = -hx + (i + w / 2) * cw, -hz + (j + h / 2) * ch
            wx, wz = cx + lx * c + lz * s, cz - lx * s + lz * c
            r_out.append((wx, (y0 + top) / 2, wz, w * cw, top - y0, h * ch, yaw) + tuple(r[7:10]) + ('s' if sl else '',)); made += 1
            if sl: slid += 1
            else: TOPS.append(('r', wx, wz, w * cw, h * ch, yaw, top))
    info = ('%d lid-high boxes over %d kit triangles -> %d roof boxes (open roofs, cell %.1f, steps %.1f, merged within %.1f; %d of them shed you: Slide); %d turned twins of a round building skipped; %d light wells filled; %d kept whole (nothing over them)'
            % (n, ntri, made, cell, q, tol, slid, twins, wells, kept))
    return s_out, r_out, info
