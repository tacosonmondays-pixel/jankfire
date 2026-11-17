# TRIPO GUN: a whole gun the owner made in Tripo (AI image/text-to-3D, shape only) turned into a kit SKIN of a live gun
# (17 Nov 2026, the owner: "this can be cleaned right?" on a Tripo angel rifle). Headless Blender 5.3.
#   blender -b --factory-startup -P tools/roblox/tripo_gun.py -- <raw.glb> <base gun id> <skin id> <recipe.json> <out_dir>
#           [--export <dir>] [--sheet <file.jpg>] [--concept <picture>] [--no-bake] [--stage clean|sheet]
#   (--stage clean: steps 1-8 and a flat-colour preview, seconds: the loop while writing a recipe's regions;
#    --stage sheet: only the sheet again from a finished run's files)
#   blender -b --factory-startup -P tools/roblox/tripo_gun.py -- parts <raw.glb> <out_dir> [<recipe.json> <base gun id>]
# THE OWNER'S FILES STAY LOCAL: the raw glb, the recipe (it describes the owner's asset), the cleaned mesh and every
# render live in the vault next to the raw file; only this code is in git.
#
# WHAT IT DOES, in order (every choice that is the gun's own is in its recipe, below):
#   1. LOAD     the raw glb through Blender's glTF importer, transforms applied, joined (the raw file is never written)
#   2. FIT      turn (axes, then extra turns) into the kit frame (metres; x right, y up, z back, muzzle at -z) and solve
#               scale + offset so the Tripo muzzle and grip land on the base gun's muzzle and grip spots (weighted least
#               squares; the bore height counts most); prints the residual misfit and where the Tripo sights end up
#   3. CLEAN    weld, list the loose parts (connected pieces), drop the ones the recipe names (a floating halo, specks),
#               fill holes, normals out; per-part Collapse decimate (budget), flatten lumps (cut above a plane, capped)
#   4. NODES    the moving nodes: a whole part (a magazine Tripo made separate) or a BOX CUT out of a fused part (bisect
#               on the box's planes, split, both sides capped), named as the base gun's (mag, charge ...)
#   5. INLAYS   boolean unions (EXACT): Tripo parts merged (a star relief into its brake: no hidden face under it can
#               flicker) or kit-made stars let into a surface; their faces keep a tag for the colours
#   6. REGIONS  colours by face selection: ordered rules (later wins) -> node, wrap zone, slot; conditions on part, tag,
#               node, box, |x|, normal, crease-grown patches from seed points; a tidy pass takes out one-face teeth
#   7. SHADE    smooth with sharp edges by angle + a Weighted Normal pass over the WHOLE mesh, then split into pieces
#               "<node>_wz<A|B|N>__<slot>" carrying those normals (region borders shade continuously)
#   8. SAVE     <out>/<K>_clean.blend (one mesh per piece, kit Blender frame), <K>_clean.glb (to look at), <K>_clean.json
#               (the recipe, the fit, the numbers). K = w_<base>@<skin>
#   9. SKIN     SKINS below: every <K>_clean.json under ROOT (JF_TRIPO_ROOT, default the vault's Assets) is a skin for
#               gun_set.py when JF_EXTRA names this module; the builder loads the pieces by absolute path, adds the
#               recipe's kit parts (slim sights on the base gun's sight line, a halo, a charging handle, a trigger) and
#               the base gun's spots; Route S shade shells on the recipe's `shell` pieces (artist_kit.bake_gun). A
#               missing file means no skin (nothing fails)
#  10. CHECK    gun_check (loose parts, moving nodes), gun_zfix as built (JF_NOZFIX=1) and after, the flicker scan of the
#               shelled glb (pairs not involving a shade shell must be 0), triangles with shells
#  11. EXPORT   --export <dir>: the K_sh.glb copied to <dir>/src/K.glb, then export_weapons.py -- <dir> --kit (an out_dir
#               outside roblox/assets: no WeaponKit book is written; export_report.json there holds lo/hi and the paint)
#  12. SHEET    --sheet <jpg>: raw (grey) | cleaned 3/4 | left side | in hand | the base gun in hand | aim view
#               (and --concept <picture> first). The `parts` command renders the parts and crease patches to write a
#               recipe from (step 0 for a new gun)
#
# THE CONTRACT the result keeps (gunskin_kit.py): the base gun's spots (muzzle, sight, grip ...), its sight LINE (the
# recipe's `add` puts gun_sights.py's slim sights on g.spots['sight']: the Tripo's own sights are cut down or dropped),
# about its size, its moving nodes by name (gun_check's MOVING list), wrap zones in the piece names, nothing floating.
#
# A RECIPE (JSON; weapon-frame metres unless it says raw; "SY" / "BY" in an `add` argument = the sight line's / bore's
# height). The angel rifle's is vault Assets/tripo-17nov/angel-rifle/recipe.json; the fields:
# {
#   "name": "Seraph Rifle (Tripo)",
#   "turn": {"axes": ["+Y", "+Z", "+X"],        weapon x, y, z = these raw axes (Blender import frame: Z up)
#            "pre": [["Z", -34.0]]},            raw turns first (degrees about raw X / Y / Z): a gun lying diagonal
#   "fit": {"muzzle": [-0.5, 0.0053, 0.2376],   RAW points: the bore's centre at the muzzle face, the grip spot's match
#           "grip": [0.1867, 0.0053, 0.1386],   (as far up the grip, as far back in it, as the base gun's)
#           "centre": [-0.5, 0.0053, 0.24],     a raw point on the gun's middle plane (weapon x = 0; default: muzzle)
#           "weights": {"muzzle_y": 10, "muzzle_z": 3, "grip_y": 1, "grip_z": 3},  ("scale": 1.17 fixes the scale)
#           "report": {"rear sight top": [-0.02, 0.0053, 0.3071]}},   raw points printed in the kit frame
#   "weld": 0.0001, "fill": 64, "sharp": 40,    merge distance, biggest hole filled (edges), shading angle (deg)
#   "drop": [{"box": [[x0,y0,z0],[x1,y1,z1]]}, {"near": [x,y,z]}, {"tris_below": 14}, {"index": 9}],   parts out
#   "decimate": {"default": 1.0, "parts": [{"part": {"near": [..]}, "ratio": 0.6}]},   Collapse per part
#   "flatten": [{"part": {...}, "box": [lo, hi], "axis": "y", "keep": "below", "at": 0.068}],   cut + cap
#   "splits": [{"part": {...}, "co": [x, y, z], "no": [x, y, z]}],   cut along a plane (a straight colour border)
#   "nodes": [{"node": "mag", "part": {...}}, {"node": "grip", "part": {...}, "box": [lo, hi]}],  whole part / box cut
#   "unions": [{"parts": [{...base}, {...}, {...}], "tag": "bstar"}],   parts after the first get the tag
#   "inlays": [{"part": {...}, "tag": "mstar", "shape": "star", "points": 4, "R": 0.026, "r": 0.007, "c": [y, z],
#               "sides": [-1, 1], "proud": 0.0015, "turn": 0}],   a kit star let into a part's side faces (union)
#   "palette": {"pearl": "eeece6", "gold": "c9a456", "lit": ["ffd58a", "n"]},   slot -> colour or [colour, kind]
#   "default": {"node": "body", "zone": "A", "slot": "pearl"},
#   "regions": [{"where": {"part": {...}, "box": [lo, hi], "absx": [a, b], "n": {"x": [lo, hi]}, "an": {"x": [lo, hi]},
#                          "tag": "bstar", "node": "mag", "slot": "pearl", "grow": {"seeds": [[x,y,z]], "crease": 25},
#                          "side": {"co": [..], "no": [..]}, "rz": [x, y, rmin, rmax], "ellipsoid": [[c], [r]],
#                          "not": {...}, "any": [{...}, {...}]},
#                "node": "muzzle", "zone": "N", "slot": "lit"}],   conditions all hold; a later rule wins
#   "tidy": 1,  "tidy_fixed": ["lit"],          one-face teeth passes; slots never changed by it
#   "add": [{"fn": "rifle_rear", "piece": "sight_wzN__graph", "args": [0.234, "SY", 0.08], "kw": {"w": 0.037}},
#           {"fn": "box", "piece": "charge_wzB__graph", "args": [[-0.008, 0.008], [0.05, 0.06], [-0.1, -0.064]]},
#           {"fn": "halo", "piece": "halo_wzN", "kw": {"c": [0, "BY", -0.556], "ro": 0.046, "ri": 0.038, "li": 0.034,
#                                                     "L": 0.009, "tilt": 18, "spokes": 3, "r_hub": 0.012}}],
#        fn: a Gun method (box prism cyl cylz ring ball xprism yprism window), a gun_sights.py helper (rifle_rear
#        rifle_front notch blade bead), gun_models' trigger / guard, or halo (a tilted ring on spokes, below)
#   "shell": ["body_wzA__pearl", "rwing"],      Route S shells: pieces or nodes (budget: <= 15k tris with shells)
#   "ao": null                                  the bake's AO reach (metres; null = from the gun's length)
# }
# TRAPS (the angel rifle): Tripo pieces come as open shells sitting on each other (a star relief with no back, a halo as a
# zero-thickness ribbon): fill, then UNION the reliefs into what they sit on or the hidden face under them flickers;
# Tripo sights are lumps at the wrong height and place: cut them down and stand the slim kit sights on the base line;
# a part's bbox centre picks it ({"box"}), {"near"} picks the part with the nearest face centre.
import sys, os, math, json, glob, time, shutil, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import gunkit

ROOT = os.environ.get('JF_TRIPO_ROOT', r'C:\Users\soup2\Documents\JANKFIRE Vault\Assets')
PY = os.environ.get('JF_PY', r'C:\Users\soup2\AppData\Local\Programs\Python\Python313\python.exe')
AX = {'X': 0, 'Y': 1, 'Z': 2}


def W(co):
    """Blender kit frame -> weapon frame (x right, y up, z back)"""
    return Vector((co[0], co[2], -co[1]))


def B(w):
    """weapon frame -> Blender kit frame (gunkit.P)"""
    return Vector((w[0], -w[2], w[1]))


def tri_count(bm):
    return sum(len(f.verts) - 2 for f in bm.faces)


# ================================================================================================ 1-2. load and fit
def load_raw(path):
    """the raw glb as one bmesh in its import frame (transforms applied); the scene is emptied again"""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    bm = bmesh.new()
    for o in [o for o in bpy.context.scene.objects if o.type == 'MESH']:
        me = o.data.copy(); me.transform(o.matrix_world)
        bm.from_mesh(me); bpy.data.meshes.remove(me)
    for o in list(bpy.context.scene.objects): bpy.data.objects.remove(o, do_unlink=True)
    for f in bm.faces: f.material_index = 0
    return bm


def turn_matrix(rec):
    """3x3: raw -> weapon axes (no scale)"""
    t = rec.get('turn', {})
    R = Matrix.Identity(3)
    for ax, deg in t.get('pre', []):
        R = Matrix.Rotation(math.radians(deg), 3, ax.upper()) @ R
    axes = t.get('axes', ['+Y', '+Z', '+X'])
    M = Matrix(((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)))
    for row, a in enumerate(axes):
        M[row][AX[a[1].upper()]] = -1.0 if a[0] == '-' else 1.0
    return M @ R


def solve_fit(rec, spots):
    """scale s and offset t with weapon = s R raw + t; returns (s, t, R, residuals)"""
    f = rec['fit']
    R = turn_matrix(rec)
    m, gp = R @ Vector(f['muzzle']), R @ Vector(f['grip'])
    M0, G0 = Vector(spots['muzzle']), Vector(spots['grip'])
    w = dict(muzzle_y=10.0, muzzle_z=3.0, grip_y=1.0, grip_z=3.0); w.update(f.get('weights', {}))
    rows = [((m.y, 1.0, 0.0), M0.y, w['muzzle_y']), ((m.z, 0.0, 1.0), M0.z, w['muzzle_z']),
            ((gp.y, 1.0, 0.0), G0.y, w['grip_y']), ((gp.z, 0.0, 1.0), G0.z, w['grip_z'])]
    fixed = f.get('scale')
    if fixed:   # (only the offsets left)
        rows = [((0.0, a[1], a[2]), b - a[0] * fixed, k) for a, b, k in rows]
    # weighted normal equations (3x3)
    A = [[0.0] * 3 for _ in range(3)]; bb = [0.0] * 3
    for a, b, k in rows:
        for i in range(3):
            bb[i] += k * a[i] * b
            for j in range(3): A[i][j] += k * a[i] * a[j]
    if fixed: A[0][0] = 1.0; bb[0] = fixed; A[0][1] = A[0][2] = A[1][0] = A[2][0] = 0.0
    sol = Matrix(A).inverted() @ Vector(bb)
    s, ty, tz = sol
    tx = -s * (R @ Vector(f.get('centre', f['muzzle']))).x   # (the raw point on the gun's middle plane: weapon x = 0)
    t = Vector((tx, ty, tz))
    def wp(p): return s * (R @ Vector(p)) + t
    res = {'scale': round(s, 5), 'offset': [round(x, 5) for x in t],
           'muzzle_at': [round(x, 4) for x in wp(f['muzzle'])], 'muzzle_spot': list(spots['muzzle']),
           'grip_at': [round(x, 4) for x in wp(f['grip'])], 'grip_spot': list(spots['grip'])}
    res['muzzle_miss_mm'] = [round((wp(f['muzzle'])[i] - spots['muzzle'][i]) * 1000, 1) for i in range(3)]
    res['grip_miss_mm'] = [round((wp(f['grip'])[i] - spots['grip'][i]) * 1000, 1) for i in range(3)]
    for name, p in f.get('report', {}).items():
        q = wp(p)
        res['at ' + name] = [round(x, 4) for x in q]
        if 'sight' in name:
            res['miss ' + name + ' (mm below the sight line, mm ahead of the sight spot)'] = [
                round((spots['sight'][1] - q.y) * 1000, 1), round((spots['sight'][2] - q.z) * 1000, 1)]
    return s, t, R, res


def fit_bmesh(bm, s, t, R):
    """raw import frame -> the kit's Blender frame"""
    Pm = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))   # weapon -> Blender
    L = Pm @ (R * s)
    M = L.to_4x4(); M.translation = Pm @ t
    bm.transform(M)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


# ================================================================================================ 3. parts and clean
def parts_of(bm):
    """{face: part id}, parts sorted biggest first; and per part: tris, lo, hi (weapon frame), centre"""
    bm.verts.index_update(); bm.faces.index_update()
    par = list(range(len(bm.verts)))
    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for e in bm.edges:
        a, b = find(e.verts[0].index), find(e.verts[1].index)
        if a != b: par[a] = b
    groups = {}
    for f in bm.faces: groups.setdefault(find(f.verts[0].index), []).append(f)
    order = sorted(groups.values(), key=lambda fs: -len(fs))
    pid, info = {}, []
    for i, fs in enumerate(order):
        pts = [W(v.co) for f in fs for v in f.verts]
        lo = Vector([min(p[k] for p in pts) for k in range(3)]); hi = Vector([max(p[k] for p in pts) for k in range(3)])
        for f in fs: pid[f] = i
        info.append({'index': i, 'tris': sum(len(f.verts) - 2 for f in fs), 'lo': lo, 'hi': hi, 'centre': (lo + hi) / 2,
                     'faces': fs, 'boundary': sum(1 for f in fs for e in f.edges if e.is_boundary)})
    return pid, info


def select_parts(sel, info, bm=None):
    """part selector -> set of part indices. near = the part whose SURFACE passes closest to the point (needs bm)"""
    if sel is None: return set(range(len(info)))
    if isinstance(sel, list): return set().union(*[select_parts(s, info, bm) for s in sel])
    out = set()
    if 'index' in sel: out.add(sel['index'])
    if 'box' in sel:
        lo, hi = sel['box']
        out |= {p['index'] for p in info if all(lo[k] <= p['centre'][k] <= hi[k] for k in range(3))}
    if 'tris_below' in sel: out |= {p['index'] for p in info if p['tris'] < sel['tris_below']}
    if 'near' in sel:
        owner = {f: p['index'] for p in info for f in p['faces']}
        bm.faces.ensure_lookup_table()
        tree = BVHTree.FromBMesh(bm)
        hit = tree.find_nearest(B(sel['near']))
        if hit[2] is not None: out.add(owner[bm.faces[hit[2]]])
    return out


def drop_parts(bm, rec):
    pid, info = parts_of(bm)
    gone = set()
    for sel in rec.get('drop', []): gone |= select_parts(sel, info, bm)
    dropped = [{'index': i, 'tris': info[i]['tris'], 'centre': [round(x, 3) for x in info[i]['centre']]} for i in sorted(gone)]
    faces = [f for f in bm.faces if pid[f] in gone]
    if faces: bmesh.ops.delete(bm, geom=faces, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    if loose: bmesh.ops.delete(bm, geom=loose, context='VERTS')
    return dropped


def dedupe_faces(bm):
    """a face on the same corners as another (Tripo leaves a few): the copy goes (glTF calls the mesh invalid)"""
    bm.verts.index_update()
    seen, gone = set(), []
    for f in bm.faces:
        k = frozenset(v.index for v in f.verts)
        if k in seen: gone.append(f)
        else: seen.add(k)
    if gone: bmesh.ops.delete(bm, geom=gone, context='FACES_ONLY')
    return len(gone)


def fill_holes(bm, sides):
    bnd = [e for e in bm.edges if e.is_boundary]
    r = bmesh.ops.holes_fill(bm, edges=bnd, sides=sides)
    if r['faces']: bmesh.ops.triangulate(bm, faces=[f for f in r['faces'] if len(f.verts) > 3], quad_method='BEAUTY', ngon_method='BEAUTY')
    return r['faces']


def _bm_obj(bm, name='tmp'):
    me = bpy.data.meshes.new(name); bm.to_mesh(me)
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    return o


def _obj_bm(o, apply=True):
    if apply:
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    else:
        me = o.data
    bm = bmesh.new(); bm.from_mesh(me)
    if apply: bpy.data.meshes.remove(me)
    old = o.data
    bpy.data.objects.remove(o, do_unlink=True)
    if old.users == 0: bpy.data.meshes.remove(old)
    return bm


def split_off(bm, faces):
    """move faces into a new bmesh (removed from bm)"""
    bm.faces.index_update()
    keep = {f.index for f in faces}
    sub = bm.copy()   # (copies in order: the i-th face of sub is the i-th face of bm)
    bmesh.ops.delete(sub, geom=[f for i, f in enumerate(sub.faces) if i not in keep], context='FACES')
    loose = [v for v in sub.verts if not v.link_faces]
    if loose: bmesh.ops.delete(sub, geom=loose, context='VERTS')
    bmesh.ops.delete(bm, geom=list(faces), context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    if loose: bmesh.ops.delete(bm, geom=loose, context='VERTS')
    return sub


def merge_in(bm, sub):
    me = bpy.data.meshes.new('m'); sub.to_mesh(me); sub.free()
    bm.from_mesh(me); bpy.data.meshes.remove(me)


def decimate_parts(bm, rec):
    d = rec.get('decimate')
    if not d: return []
    pid, info = parts_of(bm)
    ratio = {i: d.get('default', 1.0) for i in range(len(info))}
    for r in d.get('parts', []):
        for i in select_parts(r['part'], info, bm): ratio[i] = r['ratio']
    log = []
    for i in sorted(ratio, reverse=True):
        if ratio[i] >= 0.999: continue
        before = info[i]['tris']
        sub = split_off(bm, info[i]['faces'])
        o = _bm_obj(sub); sub.free()
        m = o.modifiers.new('dec', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = ratio[i]; m.use_collapse_triangulate = True
        sub = _obj_bm(o)
        bmesh.ops.dissolve_degenerate(sub, edges=sub.edges[:], dist=1e-7)
        bmesh.ops.triangulate(sub, faces=[f for f in sub.faces if len(f.verts) > 3])
        log.append({'part': i, 'from': before, 'to': tri_count(sub)})
        merge_in(bm, sub)   # (the other parts' faces stay valid: split_off and merge_in never touch them)
    return log


def _plane(axis, at):
    """an axis-aligned plane in the weapon frame -> (co, no) in the Blender frame"""
    w = [0.0, 0.0, 0.0]; w[AX[axis.upper()]] = 1.0
    return B([at if k == AX[axis.upper()] else 0.0 for k in range(3)]), B(w)


def _inbox(c, box, pad=0.0):
    lo, hi = box
    return all(lo[k] - pad <= c[k] <= hi[k] + pad for k in range(3))


def flatten(bm, op):
    """cut away the part of the mesh beyond a plane inside a box (weapon frame) and cap the cut"""
    pid, info = parts_of(bm)
    ps = select_parts(op.get('part'), info, bm)
    lay = bm.faces.layers.int['_sel']   # (made once in clean(): a new layer would orphan every face reference)
    for f in bm.faces: f[lay] = 1 if pid[f] in ps else 0   # (bisect copies the mark onto the faces it splits)
    faces = [f for f in bm.faces if f[lay] and _inbox(W(f.calc_center_median()), op['box'])]
    co, no = _plane(op.get('axis', 'y'), op['at'])
    geom = list(set(faces) | {e for f in faces for e in f.edges} | {v for f in faces for v in f.verts})
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no, dist=1e-6)
    k = AX[op.get('axis', 'y').upper()]
    keep_below = op.get('keep', 'below') == 'below'
    def beyond(c): return (c[k] > op['at'] + 1e-6) if keep_below else (c[k] < op['at'] - 1e-6)
    gone = [f for f in bm.faces if f[lay] and _inbox(W(f.calc_center_median()), op['box'], 1e-4) and beyond(W(f.calc_center_median()))]
    bmesh.ops.delete(bm, geom=gone, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    if loose: bmesh.ops.delete(bm, geom=loose, context='VERTS')
    caps = fill_holes(bm, 100000)
    return {'faces_cut': len(gone), 'caps': len(caps)}


def box_cut(bm, part_faces, box):
    """cut a fused part along a box (weapon frame): returns the faces inside, split from the rest, both sides capped"""
    lo, hi = box
    lay = bm.faces.layers.int['_sel']
    pf = set(part_faces)
    for f in bm.faces: f[lay] = 1 if f in pf else 0   # (bisect copies the mark onto the faces it splits)
    for k, ax in enumerate('XYZ'):
        for at in (lo[k], hi[k]):
            fs = [f for f in bm.faces if f[lay]]
            pts = [W(v.co)[k] for f in fs for v in f.verts]
            if not pts or not (min(pts) < at < max(pts)): continue
            geom = list(set(fs) | {e for f in fs for e in f.edges} | {v for f in fs for v in f.verts})
            co, no = _plane(ax, at)
            bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no, dist=1e-6)
    inside = [f for f in bm.faces if f[lay] and _inbox(W(f.calc_center_median()), box, 1e-6)]
    ins = set(inside)
    seam = [e for f in inside for e in f.edges if any(g not in ins for g in e.link_faces) and len(e.link_faces) == 2]
    bmesh.ops.split_edges(bm, edges=list(set(seam)))
    return inside


# ================================================================================================ 5. unions and inlays
def union_bms(base, others):
    """EXACT boolean union of closed bmeshes; faces from `others` come back with material_index 1"""
    for f in base.faces: f.material_index = 0
    ob = _bm_obj(base, 'base'); base.free()
    m0, m1 = bpy.data.materials.new('u0'), bpy.data.materials.new('u1')
    ob.data.materials.append(m0); ob.data.materials.append(m1)
    tools = []
    for o in others:
        for f in o.faces: f.material_index = 1
        t = _bm_obj(o, 'tool'); o.free()
        t.data.materials.append(m0); t.data.materials.append(m1)
        tools.append(t)
        md = ob.modifiers.new('u', 'BOOLEAN'); md.object = t; md.operation = 'UNION'; md.solver = 'EXACT'
        md.material_mode = 'INDEX'
    out = _obj_bm(ob)
    for t in tools:
        me = t.data; bpy.data.objects.remove(t, do_unlink=True); bpy.data.meshes.remove(me)
    bpy.data.materials.remove(m0); bpy.data.materials.remove(m1)
    return out


def star_outline(cy, cz, R, r, n=4, turn=0.0, k=3):
    """a star seen from the side [(y, z)]: n points R out, r between them; each side bowed in a little (k samples)"""
    pts = []
    for i in range(n * 2):
        a = math.radians(turn) + math.pi / 2 + i * math.pi / n
        rad = R if i % 2 == 0 else r
        pts.append((cy + rad * math.sin(a), cz + rad * math.cos(a)))
    return pts


def star_prism(poly, x0, x1):
    """an outline [(y, z)] pushed along x from x0 to x1 (weapon frame) as a closed bmesh"""
    bm = bmesh.new()
    A = [bm.verts.new(B((x0, y, z))) for y, z in poly]
    C = [bm.verts.new(B((x1, y, z))) for y, z in poly]
    n = len(poly)
    bm.faces.new(A); bm.faces.new(C[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([A[i], C[i], C[j], A[j]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], ngon_method='EAR_CLIP')
    return bm


def run_unions(bm, rec, tags):
    log = []
    for u in rec.get('unions', []):
        pid, info = parts_of(bm)
        sets = [select_parts(s, info, bm) for s in u['parts']]
        base_ids = sets[0]; other_ids = set().union(*sets[1:]) - base_ids
        base_f = [f for f in bm.faces if pid[f] in base_ids]
        oth_f = [f for f in bm.faces if pid[f] in other_ids]
        oth = split_off(bm, oth_f)       # (the base's faces stay valid)
        base = split_off(bm, base_f)
        n0 = tri_count(base)
        out = union_bms(base, [oth])
        tid = tags.setdefault(u['tag'], len(tags) + 1)
        lay = out.faces.layers.int.get('tag') or out.faces.layers.int.new('tag')
        for f in out.faces:
            if f.material_index == 1: f[lay] = tid
            f.material_index = 0
        log.append({'tag': u['tag'], 'base_tris': n0, 'after': tri_count(out)})
        merge_in(bm, out)
    return log


def run_inlays(bm, rec, tags):
    log = []
    for il in rec.get('inlays', []):
        pid, info = parts_of(bm)
        ids = select_parts(il['part'], info, bm)
        base = split_off(bm, [f for f in bm.faces if pid[f] in ids])
        cy, cz = il['c']
        poly = star_outline(cy, cz, il['R'], il['r'], il.get('points', 4), il.get('turn', 0.0))
        tools = []
        for sx in il.get('sides', [-1, 1]):
            # the surface's height under the star: the farthest the part reaches out on that side inside its footprint
            ys = [p[0] for p in poly]; zs = [p[1] for p in poly]
            xs = [abs(W(v.co).x) for v in base.verts if sx * W(v.co).x > 0 and min(ys) <= W(v.co).y <= max(ys) and min(zs) <= W(v.co).z <= max(zs)]
            top = (max(xs) if xs else il.get('x', 0.03)) + il.get('proud', 0.0015)
            inner = max(0.002, top - il.get('depth', 0.012))
            tools.append(star_prism(poly, sx * inner, sx * top))
        n0 = tri_count(base)
        out = union_bms(base, tools)
        tid = tags.setdefault(il['tag'], len(tags) + 1)
        lay = out.faces.layers.int.get('tag') or out.faces.layers.int.new('tag')
        for f in out.faces:
            if f.material_index == 1: f[lay] = tid
            f.material_index = 0
        log.append({'tag': il['tag'], 'base_tris': n0, 'after': tri_count(out)})
        merge_in(bm, out)
    return log


# ================================================================================================ 6. regions
def concave(e, deg):
    fs = e.link_faces
    if len(fs) != 2: return True
    a, b = fs
    if a.normal.angle(b.normal, 0.0) < math.radians(deg): return False
    return (b.calc_center_median() - a.calc_center_median()).dot(a.normal) > 0


def grow(bm, seeds, deg, allowed=None):
    seen = set(seeds); todo = list(seeds)
    while todo:
        f = todo.pop()
        for e in f.edges:
            if concave(e, deg): continue
            for g in e.link_faces:
                if g in seen or (allowed is not None and g not in allowed): continue
                seen.add(g); todo.append(g)
    return seen


class Ctx:
    def __init__(self, bm, tags, nodes_of):
        self.bm = bm
        self.pid, self.info = parts_of(bm)
        bm.normal_update()
        self.c = {f: W(f.calc_center_median()) for f in bm.faces}
        self.n = {f: W(f.normal) for f in bm.faces}
        lay = bm.faces.layers.int.get('tag')
        inv = {v: k for k, v in tags.items()}
        self.tag = {f: inv.get(f[lay]) if lay else None for f in bm.faces}
        self.node0 = nodes_of
        self.cache = {}
        self.cur = {}

    def parts(self, sel):
        key = json.dumps(sel, sort_keys=True)
        if key not in self.cache: self.cache[key] = select_parts(sel, self.info, self.bm)
        return self.cache[key]

    def grown(self, spec):
        key = 'grow' + json.dumps(spec, sort_keys=True)
        if key not in self.cache:
            seeds = []
            self.bm.faces.ensure_lookup_table()
            tree = BVHTree.FromBMesh(self.bm)
            for p in spec['seeds']:   # (the face whose surface passes closest to the point)
                hit = tree.find_nearest(B(p))
                if hit[2] is not None: seeds.append(self.bm.faces[hit[2]])
            allowed = None
            if 'part' in spec:
                ps = self.parts(spec['part']); allowed = {f for f in self.bm.faces if self.pid[f] in ps}
            self.cache[key] = grow(self.bm, seeds, spec.get('crease', 25.0), allowed)
        return self.cache[key]


def match(cond, f, cx):
    c, n = cx.c[f], cx.n[f]
    for k, v in cond.items():
        if k == 'part':
            if cx.pid[f] not in cx.parts(v): return False
        elif k == 'box':
            if not _inbox(c, v): return False
        elif k == 'absx':
            if not (v[0] <= abs(c.x) <= v[1]): return False
        elif k == 'n':
            for a, (lo, hi) in v.items():
                if not (lo <= n[AX[a.upper()]] <= hi): return False
        elif k == 'an':
            for a, (lo, hi) in v.items():
                if not (lo <= abs(n[AX[a.upper()]]) <= hi): return False
        elif k == 'out':   # the normal points away from the gun's middle plane (x) by at least v
            if n.x * (1 if c.x >= 0 else -1) < v: return False
        elif k == 'tag':
            if cx.tag[f] not in (v if isinstance(v, list) else [v]): return False
        elif k == 'node':
            if cx.cur[f][0] not in (v if isinstance(v, list) else [v]): return False
        elif k == 'slot':
            if cx.cur[f][2] not in (v if isinstance(v, list) else [v]): return False
        elif k == 'grow':
            if f not in cx.grown(v): return False
        elif k == 'side':   # on the side of a plane its normal points to (weapon frame)
            if (c - Vector(v['co'])).dot(Vector(v['no'])) < 0: return False
        elif k == 'rz':     # [x, y, rmin, rmax]: distance from the line along z through (x, y) (a bore)
            if not (v[2] <= math.hypot(c.x - v[0], c.y - v[1]) <= v[3]): return False
        elif k == 'ellipsoid':
            q, r = Vector(v[0]), v[1]
            if sum(((c[i] - q[i]) / r[i]) ** 2 for i in range(3)) > 1: return False
        elif k == 'not':
            if match(v, f, cx): return False
        elif k == 'any':
            if not any(match(x, f, cx) for x in v): return False
        else:
            raise SystemExit('tripo_gun: unknown region condition %r' % k)
    return True


def assign_regions(bm, rec, tags, node_lay):
    d = rec.get('default', {})
    names = rec['_node_names']
    cx = Ctx(bm, tags, None)
    for f in bm.faces:
        nd = names[f[node_lay]] if f[node_lay] else d.get('node', 'body')
        cx.cur[f] = (nd, d.get('zone', 'A'), d.get('slot', 'body'))
    for r in rec.get('regions', []):
        hit = [f for f in bm.faces if match(r.get('where', {}), f, cx)]
        for f in hit:
            nd, zn, sl = cx.cur[f]
            cx.cur[f] = (r.get('node', nd), r.get('zone', zn), r.get('slot', sl))
        r['_hits'] = len(hit)
    fixed = set(rec.get('tidy_fixed', []))
    for _ in range(rec.get('tidy', 1)):
        change = {}
        for f in bm.faces:
            if cx.cur[f][2] in fixed: continue
            nb = [cx.cur[g] for e in f.edges for g in e.link_faces if g is not f and cx.pid[g] == cx.pid[f]]
            if not nb: continue
            best = max(set(nb), key=nb.count)
            if best != cx.cur[f] and nb.count(best) >= 2 and best[2] not in fixed and best[0] == cx.cur[f][0]:
                change[f] = best
        for f, k in change.items(): cx.cur[f] = k
    return {f: '%s_wz%s__%s' % v for f, v in cx.cur.items()}


# ================================================================================================ 7-8. shade, split, save
def shade_and_split(bm, piece_of, sharp):
    """smooth + sharp-by-angle + Weighted Normal over the whole mesh; split into one Mesh per piece with those normals"""
    keys = sorted(set(piece_of.values()))
    pidx = {k: i for i, k in enumerate(keys)}
    for f in bm.faces: f.material_index = pidx[piece_of[f]]
    bm.normal_update()
    lim = math.radians(sharp)
    for f in bm.faces: f.smooth = True
    for e in bm.edges:
        fs = e.link_faces
        e.smooth = len(fs) == 2 and fs[0].normal.angle(fs[1].normal, 0.0) < lim
    o = _bm_obj(bm, 'whole')
    me = o.data
    oi = me.attributes.new('oi', 'INT', 'FACE')
    for p in me.polygons: oi.data[p.index].value = p.index
    wn = o.modifiers.new('wn', 'WEIGHTED_NORMAL'); wn.mode = 'FACE_AREA'; wn.weight = 50; wn.keep_sharp = True
    dg = bpy.context.evaluated_depsgraph_get()
    ev = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    cn = [tuple(c.vector) for c in ev.corner_normals]
    full = {p.index: [cn[li] for li in p.loop_indices] for p in ev.polygons}
    out = {}
    for k in keys:
        sub = bmesh.new(); sub.from_mesh(ev)
        bmesh.ops.delete(sub, geom=[f for f in sub.faces if f.material_index != pidx[k]], context='FACES')
        loose = [v for v in sub.verts if not v.link_faces]
        if loose: bmesh.ops.delete(sub, geom=loose, context='VERTS')
        for f in sub.faces: f.material_index = 0
        pm = bpy.data.meshes.new(k); sub.to_mesh(pm); sub.free()
        a = pm.attributes['oi']
        nrm = []
        for p in pm.polygons: nrm += full[a.data[p.index].value]
        pm.attributes.remove(pm.attributes['oi'])
        pm.normals_split_custom_set(nrm)
        out[k] = pm
    bpy.data.objects.remove(o, do_unlink=True); bpy.data.meshes.remove(me); bpy.data.meshes.remove(ev)
    return out


def hexrgb(h):
    return [gunkit.lin(c) for c in gunkit.hex_rgb(h)]


def palette_of(rec):
    out = {}
    for k, v in rec.get('palette', {}).items():
        out[k] = {'color': v, 'kind': 'p', 'alpha': 1.0} if isinstance(v, str) else {'color': v[0], 'kind': v[1], 'alpha': 1.0}
    return out


def save_clean(pieces, rec, meta, out_dir, K):
    os.makedirs(out_dir, exist_ok=True)
    blend = os.path.join(out_dir, K + '_clean.blend')
    for k, me in pieces.items(): me.name = k
    bpy.data.libraries.write(blend, set(pieces.values()), compress=True)
    # the .glb to look at: one object per piece in its slot colour, the weapon file frame
    pal = palette_of(rec)
    mats = {}
    objs = []
    for k, me in pieces.items():
        slot = k.split('__')[1]
        if slot not in mats:
            m = bpy.data.materials.new(slot); m.use_nodes = True
            bs = m.node_tree.nodes['Principled BSDF']
            col = hexrgb(pal.get(slot, {'color': 'ff00ff'})['color'])
            bs.inputs['Base Color'].default_value = col + [1]; bs.inputs['Roughness'].default_value = 0.75
            mats[slot] = m
        me.materials.clear(); me.materials.append(mats[slot])
        o = bpy.data.objects.new(k, me); bpy.context.scene.collection.objects.link(o); objs.append(o)
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, K + '_clean.glb'), export_format='GLB', use_selection=False,
                              export_yup=True, export_apply=True, export_animations=False)
    for o in objs: bpy.data.objects.remove(o, do_unlink=True)
    for m in mats.values(): bpy.data.materials.remove(m)
    with open(os.path.join(out_dir, K + '_clean.json'), 'w') as fh: json.dump(meta, fh, indent=1, default=str)
    return blend


def clean(raw, base_id, skin_id, rec, out_dir):
    """steps 1-8: returns the meta written to <K>_clean.json"""
    import gun_set
    t0 = time.time()
    key = '%s@%s' % (base_id, skin_id)
    K = 'w_' + key
    spots = dict(gun_set.BUILD[base_id]().spots)
    bm = load_raw(raw)
    meta = {'key': key, 'base': base_id, 'skin': skin_id, 'raw': os.path.abspath(raw), 'name': rec.get('name', key),
            'raw_tris': tri_count(bm), 'raw_verts': len(bm.verts)}
    meta['raw_nonmanifold'] = sum(1 for e in bm.edges if not e.is_manifold)
    s, t, R, fit = solve_fit(rec, spots)
    meta['fit'] = fit
    fit_bmesh(bm, s, t, R)
    for nm in ('tag', 'node', '_sel'): bm.faces.layers.int.new(nm)   # (all working layers up front)
    v0 = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=rec.get('weld', 1e-4) * s)
    meta['welded'] = v0 - len(bm.verts)
    meta['duplicate_faces'] = dedupe_faces(bm)
    pid, info = parts_of(bm)
    meta['parts_raw'] = [{'index': p['index'], 'tris': p['tris'], 'boundary_edges': p['boundary'],
                          'centre': [round(x, 3) for x in p['centre']], 'lo': [round(x, 3) for x in p['lo']],
                          'hi': [round(x, 3) for x in p['hi']]} for p in info]
    meta['dropped'] = drop_parts(bm, rec)
    meta['holes_filled'] = len(fill_holes(bm, rec.get('fill', 64)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    meta['nonmanifold_after_fill'] = sum(1 for e in bm.edges if not e.is_manifold)
    meta['decimate'] = decimate_parts(bm, rec)
    meta['flatten'] = [flatten(bm, op) for op in rec.get('flatten', [])]
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    tags = {}
    meta['unions'] = run_unions(bm, rec, tags)
    meta['inlays'] = run_inlays(bm, rec, tags)
    # straight region borders: parts cut along planes (nothing removed), so a colour edge can follow a line
    for sp in rec.get('splits', []):
        pid, info = parts_of(bm)
        ps = select_parts(sp.get('part'), info, bm)
        fs = [f for f in bm.faces if pid[f] in ps]
        geom = list(set(fs) | {e for f in fs for e in f.edges} | {v for f in fs for v in f.verts})
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=B(sp['co']), plane_no=B(sp['no']), dist=1e-6)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method='BEAUTY', ngon_method='BEAUTY')
    # moving nodes: whole parts, or box cuts out of a part
    node_lay = bm.faces.layers.int['node']
    names = [None]
    meta['nodes'] = []
    for nd in rec.get('nodes', []):
        pid, info = parts_of(bm)
        ids = select_parts(nd['part'], info, bm)
        if nd['node'] not in names: names.append(nd['node'])
        k = names.index(nd['node'])
        faces = [f for f in bm.faces if pid[f] in ids]
        if 'box' in nd:
            inside = box_cut(bm, faces, nd['box'])
            for f in inside: f[node_lay] = k
            caps = fill_holes(bm, 100000)
            ins = set(inside)
            for f in caps:   # (a cap belongs to the side it closes)
                nb = [g for e in f.edges for g in e.link_faces if g is not f]
                f[node_lay] = k if any(g in ins for g in nb) else (nb[0][node_lay] if nb else 0)
            meta['nodes'].append({'node': nd['node'], 'cut_faces': len(inside), 'caps': len(caps)})
        else:
            for f in faces: f[node_lay] = k
            meta['nodes'].append({'node': nd['node'], 'parts': sorted(ids), 'tris': sum(len(f.verts) - 2 for f in faces)})
    rec['_node_names'] = names
    meta['duplicate_faces'] += dedupe_faces(bm)   # (a hole fill can lay a copy over a face Tripo left unwelded)
    for f in fill_holes(bm, 16):   # (and close what the copy's removal opened; the patch joins its neighbour's node)
        nb = [g for e in f.edges for g in e.link_faces if g is not f]
        f[node_lay] = nb[0][node_lay] if nb else 0
    meta['duplicate_faces'] += dedupe_faces(bm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.faces.index_update()
    piece_of = assign_regions(bm, rec, tags, node_lay)
    meta['regions'] = [{'slot': r.get('slot'), 'node': r.get('node'), 'zone': r.get('zone'), 'faces': r.get('_hits')}
                       for r in rec.get('regions', [])]
    pieces = shade_and_split(bm, piece_of, rec.get('sharp', 40.0))
    meta['pieces'] = {k: sum(len(p.vertices) - 2 for p in me.polygons) for k, me in pieces.items()}
    meta['tris'] = sum(meta['pieces'].values())
    meta['nonmanifold_final'] = {'open': sum(1 for e in bm.edges if len(e.link_faces) == 1),
                                 'three_way': sum(1 for e in bm.edges if len(e.link_faces) > 2),
                                 'wire': sum(1 for e in bm.edges if not e.link_faces)}
    bm.free()
    rec_copy = {k: v for k, v in rec.items() if not k.startswith('_')}
    for r in rec_copy.get('regions', []): r.pop('_hits', None)
    meta['recipe'] = rec_copy
    meta['seconds'] = round(time.time() - t0, 1)
    meta['blend'] = save_clean(pieces, rec, meta, out_dir, K)
    with open(os.path.join(out_dir, K + '_clean.json'), 'w') as fh: json.dump(meta, fh, indent=1, default=str)
    for me in pieces.values():
        if me.users == 0: bpy.data.meshes.remove(me)
    print('CLEANED %s: %d -> %d tris, %d pieces, %.1fs' % (key, meta['raw_tris'], meta['tris'], len(meta['pieces']), meta['seconds']))
    return meta


# ================================================================================================ 9. the skin builder
def halo(g, piece, c, ro, ri, li, L=0.009, tilt=18.0, spokes=3, r_hub=0.012, spoke_r=0.0024, a0=90.0):
    """a slim halo round a barrel, its top leaning back by `tilt` degrees: a gold ring (piece + '__gold'), a lit inner
       ring (piece + '__lit'), `spokes` gold spokes from r_hub (inside the barrel) out into the gold ring"""
    c = Vector(c)
    tl = math.radians(tilt)
    ax = Vector((0.0, -math.sin(tl), math.cos(tl)))   # the ring's axis: along the barrel, its top leaning back
    g.ring(piece + '__gold', ro, ri, tuple(c - ax * L / 2), tuple(c + ax * L / 2), sides=24, bev=0.0012)
    g.ring(piece + '__lit', ri, li, tuple(c - ax * L / 4), tuple(c + ax * L / 4), sides=24, bev=0.0, flat=False)
    up = Vector((0.0, 1.0, 0.0)); u = (up - ax * ax.dot(up)).normalized(); v = ax.cross(u)
    for k in range(spokes):
        a = math.radians(a0 + 360.0 * k / spokes)
        d = u * math.cos(a) + v * math.sin(a)
        g.cyl(piece + '__gold', spoke_r, tuple(c + d * r_hub), tuple(c + d * (ri + 0.0035)), sides=6, bev=0.0)


def _sub(v, SY, BY):
    if isinstance(v, str): return {'SY': SY, 'BY': BY}.get(v, v)
    if isinstance(v, list): return [_sub(x, SY, BY) for x in v]
    if isinstance(v, dict): return {k: _sub(x, SY, BY) for k, x in v.items()}
    return v


def add_kit(g, items, SY, BY):
    import gun_sights as SG
    import gun_models as GM
    for it in items:
        it = _sub(it, SY, BY)
        fn, piece, args, kw = it['fn'], it.get('piece'), it.get('args', []), it.get('kw', {})
        if fn == 'halo': halo(g, piece, **kw)
        elif fn in ('box', 'prism', 'cyl', 'cylz', 'ring', 'ball', 'xprism', 'yprism', 'window'):
            args = [tuple(a) if isinstance(a, list) and fn in ('box', 'cyl', 'ring', 'ball') else a for a in args]
            if fn in ('prism', 'xprism', 'yprism'): args = [[tuple(p) for p in args[0]]] + list(args[1:])
            getattr(g, fn)(piece, *args, **kw)
        elif fn in ('rifle_rear', 'rifle_front', 'notch', 'blade', 'bead'): getattr(SG, fn)(g, piece, *args, **kw)
        elif fn in ('trigger', 'guard'): getattr(GM, fn)(g, piece, *args, **kw)
        else: raise SystemExit('tripo_gun: unknown add fn %r' % fn)


def builder(meta_path):
    """a gun_set builder for one cleaned Tripo gun (its <K>_clean.json)"""
    def build():
        import gun_set
        from artist_kit import ArtGun
        with open(meta_path) as fh: meta = json.load(fh)
        rec = meta['recipe']
        base = gun_set.BUILD[meta['base']]()
        gunkit.use_style('C')
        g = ArtGun('w_' + meta['key'])
        g.spots = dict(base.spots)
        for k, v in palette_of(rec).items(): g.slot(k, v['color'], v['kind'])
        SY, BY = g.spots['sight'][1], g.spots['muzzle'][1]
        add_kit(g, rec.get('add', []), SY, BY)
        g.done()
        blend = os.path.join(os.path.dirname(meta_path), os.path.basename(meta['blend']))
        with bpy.data.libraries.load(blend) as (src, dst):
            dst.meshes = list(src.meshes)
        for me in dst.meshes:
            node, slot = me.name.split('.')[0].split('__')
            if slot not in g.slots: raise SystemExit('%s: piece %s has no slot in the palette' % (g.name, me.name))
            g.pieces.setdefault((node, slot), bmesh.new()).from_mesh(me)
            bpy.data.meshes.remove(me)
        g.shell = set(rec.get('shell', [])) or None
        g.ao = rec.get('ao')
        g.tripo = meta
        return g
    return build


def discover():
    out = {}
    for p in glob.glob(os.path.join(ROOT, 'tripo-*', '*', 'w_*@*_clean.json')):
        key = os.path.basename(p)[2:-len('_clean.json')]
        blend = p[:-len('.json')] + '.blend'
        if os.path.exists(blend): out[key] = builder(p)
    return out


SKINS = discover() if os.path.isdir(ROOT) else {}


# ================================================================================================ 10. checks
def blender_run(script, args, env_extra=None):
    env = dict(os.environ)
    env.update(env_extra or {})
    cmd = [bpy.app.binary_path, '-b', '--factory-startup', '-P', script, '--'] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, env=env, encoding='utf8', errors='replace')
    return r.stdout + r.stderr


def flicker_scan(glb, rack=None):
    """same-facing faces of different looks in one plane closer than 0.02 studs (gun_zfix's finder on the armory's
       smallest display) in an exported glb: returns (pairs not involving a shade shell, pairs with one)"""
    import gun_zfix
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    ys = [(o.matrix_world @ v.co).y for o in objs for v in o.data.vertices]
    L = max(ys) - min(ys)
    K = (rack or (6.6 if L > 0.75 else 3.9)) / L
    M = Matrix.Scale(K, 4) @ Matrix.Rotation(-math.pi / 2, 4, 'X')
    pieces = {}
    for o in objs:
        bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
        m = o.data.materials[0] if o.data.materials else None
        look = (m.name.split('.')[0] if m else 'none') + ('_A' if '_wzA' in o.name else '_x')
        pieces.setdefault((o.name, look), []).append((bm, M))
    found, hits, _ = gun_zfix._find(pieces)
    plain, shell = [], []
    for (pa, pb, nk), (ar, n, da, db, na, nb) in hits.items():
        a, b = found[pa][0], found[pb][0]
        row = (a, b, round(abs(da - db), 4), round(ar, 4))
        (shell if ('shade' in found[pa][1] or 'shade' in found[pb][1]) else plain).append(row)
    return plain, shell, K


# ================================================================================================ 12. the sheet
def _vm_pose(wid):
    import re
    src = open(os.path.join(HERE, '..', '..', 'roblox', 'src', 'shared', 'Weapons.luau'), encoding='utf8').read()
    for m in re.finditer(r'\n\t(\w+) = \{\n\t\tid = "(\w+)"(.*?)\n\t\},', src, re.S):
        if m.group(2) != wid: continue
        v = re.search(r'vm = \{ p = Vector3\.new\(([^)]*)\) \* S, r = Vector3\.new\(([^)]*)\), s = ([\d.]+)', m.group(3))
        if v: return [float(x) for x in v.group(1).split(',')], [float(x) for x in v.group(2).split(',')], float(v.group(3))
    return [0.2, -0.2, -0.38], [0, 0.04, 0], 0.7


def hold_matrix(wid):
    p, r, s = _vm_pose(wid)
    Cm = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    rot = Matrix.Rotation(r[0], 4, 'X') @ Matrix.Rotation(r[1], 4, 'Y') @ Matrix.Rotation(r[2], 4, 'Z')
    return Cm @ (Matrix.Translation(Vector(p)) @ rot @ Matrix.Scale(s, 4)) @ Cm.inverted()


def _scene(Wd=900, Ht=560, samples=32):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = samples; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = Wd, Ht
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.55, 0.58, 0.64, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.4   # (near-white guns: keep the whites off the clip)
    return sc


def _sun(sc, rot, strength=1.8):
    d = bpy.data.lights.new('sun', 'SUN'); d.energy = strength; d.angle = 0.25
    o = bpy.data.objects.new('sun', d); o.rotation_euler = rot; sc.collection.objects.link(o)


def _cam(sc, loc, look, ortho=None, fov=40.0, up=Vector((0, 0, 1))):
    cd = bpy.data.cameras.new('c'); o = bpy.data.objects.new('c', cd); sc.collection.objects.link(o)
    o.location = Vector(loc)
    f = (Vector(look) - Vector(loc)).normalized(); r = f.cross(up).normalized(); u = r.cross(f)
    o.rotation_euler = Matrix((r, u, -f)).transposed().to_euler()
    if ortho: cd.type = 'ORTHO'; cd.ortho_scale = ortho
    else: cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(fov)
    cd.clip_start = 0.005; cd.clip_end = 100
    sc.camera = o


def _render(path, crop=False):
    r = bpy.context.scene.render
    r.filepath = path
    if crop:   # gun_preview's in-hand crop: the lower right of a wide view
        Wd, Ht = r.resolution_x, r.resolution_y
        r.resolution_x, r.resolution_y = round(Wd / 0.58), round(Ht / 0.66)
        r.use_border = True; r.use_crop_to_border = True
        r.border_min_x, r.border_max_x, r.border_min_y, r.border_max_y = 0.42, 1.0, 0.0, 0.66
    bpy.ops.render.render(write_still=True)
    return path


def _import(glb, at=None):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=glb)
    new = [o for o in bpy.context.scene.objects if o not in before]
    root = bpy.data.objects.new('root', None); bpy.context.scene.collection.objects.link(root)
    for o in new:
        if o.parent is None: o.parent = root
    if at is not None: root.matrix_world = at
    return new


def _grey(objs):
    m = bpy.data.materials.new('grey'); m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.55, 0.55, 0.56, 1)
    for o in objs:
        if o.type == 'MESH': o.data.materials.clear(); o.data.materials.append(m)


def sheet(K, base_id, out_dir, sheet_path, raw, fit, concept=None, Wd=900, Ht=560):
    """the verdict panels (PNG) in out_dir, composed with labels into sheet_path by plain Python + PIL"""
    import gun_set
    sh = os.path.join(out_dir, K + '_sh.glb')
    meta = json.load(open(os.path.join(out_dir, K + '_clean.json')))
    pdir = os.path.join(out_dir, 'sheet'); os.makedirs(pdir, exist_ok=True)   # (the panels)
    lo, hi = meta.get('bounds', ([-0.05, -0.3, -0.72], [0.05, 0.15, 0.47]))
    cy, cz = (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2
    L = hi[2] - lo[2]
    mid = B((0, cy, cz))
    side = Vector((-3.0, 0, 0))
    panels = []
    # raw, grey, fitted into the kit frame (the same camera as the cleaned side view)
    sc = _scene(Wd, Ht)
    bm = load_raw(raw)
    sc = _scene(Wd, Ht)
    s, t, R = fit
    fit_bmesh(bm, s, t, R)
    o = _bm_obj(bm, 'raw'); bm.free(); _grey([o])
    _sun(sc, (math.radians(60), 0, math.radians(-90)))
    _cam(sc, mid + side, mid, ortho=L * 1.12)
    panels.append((_render(os.path.join(pdir, '_p_raw.png')), 'Tripo raw (grey), fitted to the AR'))
    # cleaned + coloured + shells: three-quarter, left side
    sc = _scene(Wd, Ht); _import(sh)
    _sun(sc, (math.radians(50), 0, math.radians(-40)))
    _cam(sc, mid + Vector((-0.75 * L, 0.80 * L, 0.42 * L)) * 0.95, mid + Vector((0, 0.04 * L, 0)), fov=40)
    panels.append((_render(os.path.join(pdir, '_p_34.png')), 'cleaned + coloured + shade shells, 3/4'))
    sc = _scene(Wd, Ht); _import(sh)
    _sun(sc, (math.radians(60), 0, math.radians(-90)))
    _cam(sc, mid + side, mid, ortho=L * 1.12)
    panels.append((_render(os.path.join(pdir, '_p_side.png')), 'left side'))
    # in hand: the skin, then the live base gun (gun_preview's camera and pose)
    sc = _scene(Wd, Ht); _import(sh, hold_matrix(base_id))
    _sun(sc, (math.radians(35), 0, math.radians(20)))
    _cam(sc, (0, 0, 0), (0, 1, 0), fov=70)
    panels.append((_render(os.path.join(pdir, '_p_hand.png'), crop=True), 'in hand (first person, no arms)'))
    sc = _scene(Wd, Ht)
    gun_set.BUILD[base_id]().to_scene(at=hold_matrix(base_id))
    _sun(sc, (math.radians(35), 0, math.radians(20)))
    _cam(sc, (0, 0, 0), (0, 1, 0), fov=70)
    panels.append((_render(os.path.join(pdir, '_p_base.png'), crop=True), 'live base %s in hand, for scale' % base_id.upper()))
    # aim view (approximate: the eye 0.11 m behind the sight spot, zoom 1.5)
    sc = _scene(Wd, Ht); _import(sh)
    _sun(sc, (math.radians(35), 0, math.radians(20)))
    sp = meta['spots']['sight']
    eye = B((0, sp[1], sp[2] + 0.11))
    _cam(sc, eye, eye + B((0, 0, -1)), fov=70 / 1.5)
    panels.append((_render(os.path.join(pdir, '_p_aim.png')), 'aim view (approx.: eye 0.11 m behind the rear sight)'))
    if concept: panels.insert(0, (concept, "owner's concept"))
    spec = {'panels': panels, 'out': sheet_path, 'w': Wd, 'h': Ht, 'title': meta.get('name', K)}
    js = os.path.join(pdir, '_sheet.json')
    with open(js, 'w') as fh: json.dump(spec, fh)
    code = r'''
import json, sys
from PIL import Image, ImageDraw, ImageFont
s = json.load(open(sys.argv[1]))
W, H = s['w'], s['h']; n = len(s['panels']); cols = 3; rows = (n + cols - 1) // cols
try: F = ImageFont.truetype('arialbd.ttf', 22); FT = ImageFont.truetype('arialbd.ttf', 28)
except Exception: F = FT = ImageFont.load_default()
out = Image.new('RGB', (W * cols, H * rows + 44), (30, 32, 38))
d = ImageDraw.Draw(out)
d.text((14, 8), s['title'], fill=(240, 240, 240), font=FT)
for i, (p, label) in enumerate(s['panels']):
    im = Image.open(p).convert('RGB'); im.thumbnail((W, H))
    x, y = (i % cols) * W, 44 + (i // cols) * H
    out.paste(im, (x + (W - im.width) // 2, y + (H - im.height) // 2))
    d.rectangle([x, y + H - 34, x + W, y + H], fill=(20, 20, 24))
    d.text((x + 10, y + H - 30), label, fill=(235, 235, 235), font=F)
out.save(s['out'], quality=90)
print('SHEET', s['out'])
'''
    r = subprocess.run([PY, '-c', code, js], capture_output=True, text=True)   # (PIL is in the user's site-packages)
    print(r.stdout.strip(), r.stderr.strip()[-400:])
    return sheet_path


def preview(glb, out_dir):
    """the cleaned glb in its flat slot colours (workbench): preview_left / right / top / front.png"""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    objs = _import(glb)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'; sc.display.shading.show_cavity = True
    for o in objs:
        if o.type == 'MESH':
            for m in o.data.materials:
                bs = m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
                if bs: m.diffuse_color = tuple(bs.inputs['Base Color'].default_value)
    xs = [o.matrix_world @ v.co for o in objs if o.type == 'MESH' for v in o.data.vertices]
    lo = Vector([min(c[k] for c in xs) for k in range(3)]); hi = Vector([max(c[k] for c in xs) for k in range(3)])
    c = (lo + hi) / 2; L = max(hi - lo)
    sc.render.resolution_x, sc.render.resolution_y = 1600, 800
    out = []
    for name, d, up, sz in (('left', Vector((-1, 0, 0)), Vector((0, 0, 1)), 1.05), ('right', Vector((1, 0, 0)), Vector((0, 0, 1)), 1.05),
                            ('top', Vector((0, 0, 1)), Vector((0, 1, 0)), 1.05), ('q34', Vector((-0.75, 0.8, 0.42)).normalized(), Vector((0, 0, 1)), 0.9)):
        _cam(sc, c + d * 3, c, ortho=L * sz, up=up)
        out.append(_render(os.path.join(out_dir, 'preview_%s.png' % name)))
    print('PREVIEW', out)


# ================================================================================================ the parts helper
def parts_view(raw, out_dir, rec=None, base_id=None):
    """step 0 for a new gun: every loose part listed (and, with a recipe and base gun, in the kit frame after its fit)
       and rendered in its own colour from both sides and the top: parts.png, parts.json"""
    os.makedirs(out_dir, exist_ok=True)
    bm = load_raw(raw)
    info = {'raw_tris': tri_count(bm), 'nonmanifold': sum(1 for e in bm.edges if not e.is_manifold)}
    if rec and base_id:
        import gun_set
        s, t, R, fit = solve_fit(rec, dict(gun_set.BUILD[base_id]().spots))
        fit_bmesh(bm, s, t, R); info['fit'] = fit
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=rec.get('weld', 1e-4) * s)
        frame = 'weapon'
    else:
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
        frame = 'raw'
    pid, parts = parts_of(bm)
    info['frame'] = frame   # (raw: the import frame's own X, Y, Z)
    info['parts'] = [{'index': p['index'], 'tris': p['tris'], 'boundary_edges': p['boundary'],
                      'centre': [round(x, 4) for x in (p['centre'] if frame == 'weapon' else B(p['centre']))],
                      'lo': [round(x, 4) for x in (p['lo'] if frame == 'weapon' else B(p['lo']))],
                      'hi': [round(x, 4) for x in (p['hi'] if frame == 'weapon' else B(p['hi']))]} for p in parts]
    with open(os.path.join(out_dir, 'parts.json'), 'w') as fh: json.dump(info, fh, indent=1)
    for p in info['parts']: print('PART %3d %6d tris  centre %s  lo %s hi %s  open edges %d' % (p['index'], p['tris'], p['centre'], p['lo'], p['hi'], p['boundary_edges']))
    # render: each part its own colour
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'OBJECT'; sc.display.shading.show_cavity = True
    import colorsys
    for p in parts:
        sub = bmesh.new()
        tmp = bm.copy(); tmp.faces.ensure_lookup_table()
        keep = {f.index for f in p['faces']}
        bmesh.ops.delete(tmp, geom=[f for f in tmp.faces if f.index not in keep], context='FACES')
        o = _bm_obj(tmp, 'P%02d' % p['index']); tmp.free(); sub.free()
        o.color = colorsys.hsv_to_rgb((p['index'] * 0.618) % 1.0, 0.55, 0.95) + (1.0,)
    xs = [v.co for v in bm.verts]
    lo = Vector([min(c[k] for c in xs) for k in range(3)]); hi = Vector([max(c[k] for c in xs) for k in range(3)])
    c = (lo + hi) / 2; L = max(hi - lo)
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    views = (('left', Vector((-1, 0, 0)) if frame == 'weapon' else Vector((0, -1, 0)), Vector((0, 0, 1))),
             ('right', Vector((1, 0, 0)) if frame == 'weapon' else Vector((0, 1, 0)), Vector((0, 0, 1))),
             ('top', Vector((0, 0, 1)), Vector((0, 1, 0))))
    shots = []
    for name, d, up in views:
        _cam(sc, c + d * 3, c, ortho=L * 1.1, up=up)
        shots.append(_render(os.path.join(out_dir, 'parts_%s.png' % name)))
    # crease patches (what a `grow` rule reaches from a seed: faces up to concave creases sharper than 25 degrees),
    # each its own colour; patches of 12+ triangles listed with their centres (seeds for the recipe's regions)
    for o in [o for o in sc.objects if o.type == 'MESH']: bpy.data.objects.remove(o, do_unlink=True)
    bm.normal_update()
    left = set(bm.faces); patches = []
    while left:
        f0 = next(iter(left))
        p = grow(bm, [f0], 25.0, left)
        left -= p; patches.append(p)
    patches.sort(key=len, reverse=True)
    info['patches'] = []
    for i, p in enumerate(patches):
        tmp = bm.copy(); tmp.faces.ensure_lookup_table()
        bm.faces.index_update(); keep = {f.index for f in p}
        bmesh.ops.delete(tmp, geom=[f for j, f in enumerate(tmp.faces) if j not in keep], context='FACES')
        o = _bm_obj(tmp, 'S%03d' % i); tmp.free()
        o.color = colorsys.hsv_to_rgb((i * 0.618) % 1.0, 0.6, 0.95) + (1.0,)
        if len(p) >= 12:
            cc = sum((W(f.calc_center_median()) for f in p), Vector()) / len(p)
            info['patches'].append({'index': i, 'faces': len(p), 'centre': [round(x, 4) for x in (cc if frame == 'weapon' else B(cc))]})
    for name, d, up in views:
        _cam(sc, c + d * 3, c, ortho=L * 1.1, up=up)
        shots.append(_render(os.path.join(out_dir, 'patches_%s.png' % name)))
    with open(os.path.join(out_dir, 'parts.json'), 'w') as fh: json.dump(info, fh, indent=1)
    print('PARTS VIEWS', shots)


# ================================================================================================ the command line
def main(argv):
    if argv and argv[0] == 'parts':
        rec = json.load(open(argv[3])) if len(argv) > 4 else None
        parts_view(argv[1], argv[2], rec, argv[4] if len(argv) > 4 else None)
        return
    raw, base_id, skin_id, recipe, out_dir = argv[:5]
    rest = argv[5:]
    def opt(name):
        if name in rest:
            i = rest.index(name); return rest[i + 1]
        return None
    with open(recipe) as fh: rec = json.load(fh)
    key = '%s@%s' % (base_id, skin_id)
    K = 'w_' + key
    t0 = time.time()
    if opt('--stage') == 'sheet':   # (only the sheet again, from the files a full run left in out_dir)
        meta = json.load(open(os.path.join(out_dir, K + '_clean.json')))
        s, t, R, _ = solve_fit(rec, meta['spots'])
        sheet(K, base_id, out_dir, opt('--sheet'), raw, (s, t, R), concept=opt('--concept'))
        return
    meta = clean(raw, base_id, skin_id, rec, out_dir)
    if opt('--stage') == 'clean':   # (the quick loop while writing regions: flat colours, workbench, three views)
        preview(os.path.join(out_dir, K + '_clean.glb'), out_dir)
        return
    # build through gun_set (zfix-wrapped, as every skin), bake (Route S shells)
    os.environ['JF_EXTRA'] = ','.join([x for x in os.environ.get('JF_EXTRA', '').split(',') if x] + ['tripo_gun'])
    os.environ['JF_TRIPO_ROOT'] = os.environ.get('JF_TRIPO_ROOT', ROOT)
    global SKINS
    SKINS = discover()
    if key not in SKINS:   # (an out_dir outside ROOT: build it straight from its own json)
        SKINS[key] = builder(os.path.join(out_dir, K + '_clean.json'))
    import gun_set, gun_zfix
    if key not in gun_set.SKINS: gun_set.SKINS[key] = SKINS[key]
    g = SKINS[key]()
    os.environ['JF_NOZFIX'] = ''
    K0, pairs_built = gun_zfix.report(g)
    zk, eps, moved = gun_zfix.zfix(g)
    K1, pairs_after = gun_zfix.report(g)
    lo, hi = g.bounds()
    meta['bounds'] = [lo, hi]
    meta['spots'] = g.spots
    base = gun_set.BUILD[base_id]()
    meta['base_bounds'] = list(base.bounds())
    meta['zfix'] = {'pairs_as_built': pairs_built, 'faces_moved': moved, 'pairs_after': pairs_after}
    meta['tris_gun'] = g.tris()
    meta['pieces_built'] = {'%s__%s' % k: sum(len(f.verts) - 2 for f in bm.faces) for k, bm in g.pieces.items()}
    if '--no-bake' not in rest:
        from artist_kit import bake_gun
        os.environ.setdefault('JF_BAKE_DEVICE', 'CPU')
        bake_gun(g, out_dir, ao=g.ao)
        bj = json.load(open(os.path.join(out_dir, K + '_bake.json')))
        meta['tris_shells'] = bj['shell_tris']; meta['tris_total'] = bj['tris'] + bj['shell_tris']
        meta['bake'] = {k: bj[k] for k in ('texels_per_m', 'atlas_used', 'uv_overlap', 'device', 'seconds')}
        plain, shell, Kd = flicker_scan(os.path.join(out_dir, K + '_sh.glb'))
        meta['flicker'] = {'pairs_not_shell': plain, 'shell_pairs': len(shell), 'display_studs_per_m': round(Kd, 3)}
    with open(os.path.join(out_dir, K + '_clean.json'), 'w') as fh: json.dump(meta, fh, indent=1, default=str)
    env = {'JF_EXTRA': os.environ['JF_EXTRA'], 'JF_TRIPO_ROOT': os.environ['JF_TRIPO_ROOT']}
    chk = blender_run(os.path.join(HERE, 'gun_check.py'), [key], env)
    meta['gun_check'] = [l for l in chk.splitlines() if l.startswith(('CHECK', '   LOOSE'))]
    if not meta['gun_check']: meta['gun_check'] = ['(not run: the clean json is outside JF_TRIPO_ROOT)'] + chk.splitlines()[-5:]
    exp = opt('--export')
    if exp and '--no-bake' not in rest:
        os.makedirs(os.path.join(exp, 'src'), exist_ok=True)
        src = os.path.join(exp, 'src', K + '.glb')
        shutil.copyfile(os.path.join(out_dir, K + '_sh.glb'), src)
        log = blender_run(os.path.join(HERE, 'export_weapons.py'), [exp, '--kit', src])
        meta['export'] = [l for l in log.splitlines() if l.startswith(('EXPORTED', 'KIT BOOK'))] or log.splitlines()[-8:]
        rp = json.load(open(os.path.join(exp, 'export_report.json')))
        if K in rp: meta['export_lo_hi'] = [rp[K]['lo'], rp[K]['hi']]; meta['export_tris'] = rp[K]['tris']
    with open(os.path.join(out_dir, K + '_clean.json'), 'w') as fh: json.dump(meta, fh, indent=1, default=str)
    sp = opt('--sheet')
    if sp and '--no-bake' not in rest:
        s, t, R, _ = solve_fit(rec, meta['spots'])
        sheet(K, base_id, out_dir, sp, raw, (s, t, R), concept=opt('--concept'))
    print('TRIPO GUN %s done in %.0fs' % (key, time.time() - t0))
    for k in ('fit', 'tris', 'tris_gun', 'tris_shells', 'tris_total', 'zfix', 'flicker', 'gun_check', 'export', 'export_lo_hi', 'bounds', 'base_bounds'):
        if k in meta: print('  %s: %s' % (k, json.dumps(meta[k], default=str)))


if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
