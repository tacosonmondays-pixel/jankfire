# UVs for the Roblox game's own gun models (the kit, tools/roblox/gun_models.py), so a wrap texture can follow them.
# Headless Blender; called by export_weapons.py --kit just before the pieces are turned for the upload, and by
# wrap_preview.py. Changes nothing but the UV layer: names, vertices, spots and moving nodes stay exactly as built.
#
# WHAT IT DOES. Every piece's mesh islands are unfolded in the gun's own frame (metres; x right, y up, z back) at one
# scale for the whole gun: TILE_M metres of gun per texture tile (wrap_textures.py draws at the same number).
#
#   - The LEFT side of every piece (the side the player looks at in first person) maps to (u, v) = (z, y): one flat
#     projection shared by every piece, so a pattern runs straight across the body, grip, mag and stock, upright when
#     seen from the left.
#   - Every other face is a FLAT projection chosen by the way it faces (its family): a long piece's sides on (z, y),
#     its top and bottom on (z, x); an upright piece's sides on (z, y), its front and back on (x, y), its ends on
#     (z, x). The offsets are fixed per piece and chosen so the families meet without a jump at the left side's edges
#     (round the top-left edge, the front-left edge). A face never mixes two directions, so nothing shears: checks
#     stay square and stripes stay straight on sloped faces and bevels (16 Nov, after the first judging: the first
#     version unfolded by each point's own height, and checks skewed into diamonds, stripes zig-zagged at chamfers).
#     A sloped face stretches a little (up to 1.4 times at 45 degrees); nothing is ever mirrored.
#   - Round pieces (barrels, rings) are unfolded by angle. The seams sit at the bottom-right / front-right edges and
#     where a bevel turns from one family to the next.
import bpy, bmesh, math

TILE_M = 0.25      # metres of gun per texture tile (must match wrap_textures.TILE_M)
CAP = 0.7          # a face whose normal is this much along the piece's axis is an end cap
ROUND = 0.88       # an island whose side vertices all sit within this ratio of its biggest radius is round


def wf(v): return (v.x, v.z, -v.y)  # Blender z-up -> the gun's frame (x right, y up, z back)


def islands(bm):
    parent = list(range(len(bm.faces)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    owner = {}
    for f in bm.faces:
        for v in f.verts:
            j = owner.setdefault(v.index, f.index)
            a, b = find(f.index), find(j)
            if a != b: parent[a] = b
    groups = {}
    for f in bm.faces: groups.setdefault(find(f.index), []).append(f)
    return list(groups.values())


def unwrap_island(faces, uv, D):
    P = {v.index: wf(v.co) for f in faces for v in f.verts}
    xs, ys, zs = [p[0] for p in P.values()], [p[1] for p in P.values()], [p[2] for p in P.values()]
    xl, xr, yb, yt, zf, zb = min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)
    W = xr - xl
    upright = (yt - yb) > (zb - zf) * 1.15
    # round? (barrels, rings, tubes along z): every vertex off the end caps near one radius from the middle
    xc, yc = (xl + xr) / 2, (yb + yt) / 2
    rnd = False
    if not upright and W > 1e-4 and abs(W - (yt - yb)) < 0.2 * max(W, yt - yb):
        # the outer skin only (faces looking away from the axis; a bore looks inwards), its spread round the axis
        outer = set()
        for f in faces:
            nx, ny, nz = wf(f.normal)
            if abs(nz) > CAP: continue
            cx, cy = sum(P[v.index][0] for v in f.verts) / len(f.verts) - xc, sum(P[v.index][1] for v in f.verts) / len(f.verts) - yc
            if nx * cx + ny * cy > 0: outer.update(v.index for v in f.verts)
        if len(outer) > 8:
            rs = [math.hypot(P[i][0] - xc, P[i][1] - yc) for i in outer]
            ang = sorted(math.atan2(P[i][1] - yc, P[i][0] - xc) for i in outer)
            gap = max([b - a for a, b in zip(ang, ang[1:])] + [ang[0] + math.tau - ang[-1]])
            rnd = min(rs) / max(rs) > ROUND - 0.03 and gap < math.radians(40)
    R = (W + (yt - yb)) / 4
    for f in faces:
        nx, ny, nz = wf(f.normal)
        pts = [P[l.vert.index] for l in f.loops]
        out = []
        if not upright:
            if abs(nz) > CAP:                                    # end cap of a long piece: flat on (x, y)
                zc = zb if nz > 0 else zf
                s = 1 if nz > 0 else -1
                out = [(zc + s * (x - xl), y) for x, y, z in pts]
            elif rnd:                                            # round: by angle, the seam at the bottom right
                for x, y, z in pts:
                    phi = math.pi - math.atan2(y - yc, x - xc)   # 0 at the left, growing over the top
                    phi = (phi + 0.75 * math.pi) % math.tau - 0.75 * math.pi
                    out.append([z, yc + R * phi])
                ref = out[0][1]
                for o in out[1:]:                                # a face across the seam: keep it in one piece
                    while o[1] - ref > math.pi * R: o[1] -= math.tau * R
                    while o[1] - ref < -math.pi * R: o[1] += math.tau * R
            else:                                                # flat by family: side faces on (z, y), top and
                if abs(nx) >= abs(ny):                           # bottom on (z, x); the offsets meet at the edges
                    out = [(z, y if nx < 0 else W + 2 * yt - y) for x, y, z in pts]
                elif ny > 0:
                    out = [(z, yt + (x - xl)) for x, y, z in pts]
                else:
                    out = [(z, yb - (x - xl)) for x, y, z in pts]
        else:
            if abs(ny) > CAP:                                    # top / bottom of an upright piece: flat on (z, x)
                out = [(z, (yt + (x - xl)) if ny > 0 else (yb - (x - xl))) for x, y, z in pts]
            elif abs(nx) >= abs(nz):                             # its sides: flat on (z, y), the left as every piece's
                out = [(z if nx < 0 else 2 * zb + W - z, y) for x, y, z in pts]
            elif nz < 0:                                         # front and back: flat on (x, y)
                out = [(zf - (x - xl), y) for x, y, z in pts]
            else:
                out = [(zb + (x - xl), y) for x, y, z in pts]
        for l, (u, v) in zip(f.loops, out):
            l[uv].uv = (u * D, v * D)


def unwrap(objs, scale=1.0, layer='UVMap'):
    """give every mesh object one UV layer from the gun-frame unfold. scale > 1 makes the pattern finer (sidearms)"""
    D = scale / TILE_M
    for o in objs:
        if o.type != 'MESH': continue
        me = o.data
        while len(me.uv_layers): me.uv_layers.remove(me.uv_layers[0])
        bm = bmesh.new(); bm.from_mesh(me)
        bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table(); bm.normal_update()
        uv = bm.loops.layers.uv.new(layer)
        for faces in islands(bm): unwrap_island(faces, uv, D)
        bm.to_mesh(me); bm.free()
        me.update()


# sidearms get a finer pattern (they sit closer to the eye and are smaller): the web game did the same (packMat ps)
SCALE = {'pistol': 1.25, 'revolver': 1.25, 'sawnoff': 1.25, 'marbles': 1.25}
