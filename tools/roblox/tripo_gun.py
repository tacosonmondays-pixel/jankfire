# TRIPO GUN: a whole gun the owner made in Tripo (AI image/text-to-3D, shape only) turned into a kit SKIN of a live gun
# (17 Nov 2026, the owner: "this can be cleaned right?" on a Tripo angel rifle). Headless Blender 5.3.
#   blender -b --factory-startup -P tools/roblox/tripo_gun.py -- <raw.glb> <base gun id> <skin id> <recipe.json> <out_dir>
#           [--export <dir>] [--sheet <file.jpg>] [--concept <picture>] [--compare <folder>] [--no-bake] [--stage clean|sheet]
#   (--compare: a folder with an earlier run's sheet/_p_hand.png and _p_aim.png, shown BEFORE / NOW on the sheet)
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
#            "matrix": [[..], [..], [..]],        or rows = weapon x, y, z as raw directions (a model at any angle)
#            "pre": [["Z", -34.0]]},            raw turns first (degrees about raw X / Y / Z): a gun lying diagonal
#   "fit": {"muzzle": [-0.5, 0.0053, 0.2376],   RAW points: the bore's centre at the muzzle face, the grip spot's match
#           "grip": [0.1867, 0.0053, 0.1386],   (as far up the grip, as far back in it, as the base gun's)
#           "centre": [-0.5, 0.0053, 0.24],     a raw point on the gun's middle plane (weapon x = 0; default: muzzle)
#           "weights": {"muzzle_y": 10, "muzzle_z": 3, "grip_y": 1, "grip_z": 3},  ("scale": 1.17 fixes the scale)
#           "anchors": [[raw point, [x, y, z] target, weight y, weight z]],   more matches (weights 0 on muzzle/grip
#                                               drop those: a katana fits its guard face and blade tip)
#           "report": {"rear sight top": [-0.02, 0.0053, 0.3071]}},   raw points printed in the kit frame
#   "weld": 0.0001, "fill": 64, "sharp": 40,    merge distance, biggest hole filled (edges), shading angle (deg)
#   "drop": [{"box": [[x0,y0,z0],[x1,y1,z1]]}, {"near": [x,y,z]}, {"tris_below": 14}, {"index": 9}],   parts out
#   "decimate": {"default": 1.0, "parts": [{"part": {"near": [..]}, "ratio": 0.6}]},   Collapse per part
#   "straighten": [{"part": {...}, "centre": true}],   turn a part that drifts sideways along its length straight
#                (seen from the top), and with centre slide it onto the centre plane; "turn": false only slides;
#                "shift": [dx, dy, dz] moves every selected part the same (a head off the middle, with its eyes)
#   "mirror": {"keep": [{...}, ...]},   mirror-symmetric about x = 0 (the fit's "centre" point sets the plane): every
#                part but the kept one-sided props loses its right half and gets its left half mirrored across
#   "flatten": [{"part": {...}, "box": [lo, hi], "axis": "y", "keep": "below", "at": 0.068, "cap": true}],   cut + cap
#   "reshape": [{"part": {...}, "side_flat": true, "pivot": [x, y, z], "scale": 0.58, "thick": 0.007, "x_in": 0.044,
#                "y_top": 0.068, "z_back": 0.05, "sharpen": {"prom": 0.005, "tip": 0.004, "pinch": 0.55, "radius": 0.012,
#                "notch": 0.002}, "scale3": [1, 0.5, 1], "shift": [dx, dy, dz]}],   re-pose a part (a wing: flat on
#                the side, smaller, thinner, lower), see reshape(); scale3 per axis, shift not mirrored by side
#   "rims": [{"tag": ["rwing", "fwing"], "width": 0.0018}],   a chamfer round a fused part's outer face (trim line)
#   "splits": [{"part": {...}, "box": [lo, hi], "co": [x, y, z], "no": [x, y, z]}],   cut along a plane (a straight
#                colour border; box: only faces whose centre is in it)
#   "blend": [{"part": {...}, "box": [lo, hi], "to": 0.0425, "fade": {"axis": "y", "from": -0.03, "to": -0.012}}],
#                pull a lip that overhangs past |x| = to flush (fully below fade.from, not at all at fade.to)
#   "decals": [{"part": {...}, "box": .., "sides": [-1, 1], "tag": "wave", "polys": [[[z, y], ...]]}],   flat painted
#                shapes (a wave band, foam dots, a duck icon) CUT into the side faces along their outlines (seen
#                along x): new edges, no picture, nothing laid on top; colour them by tag
#   "planar": [{"part": {...}, "box": .., "axis": "x", "nmin": 0.9, "sides": [-1, 1], "max_move": 0.002}],   a lumpy
#                face that should be flat put on one plane per side (polish)
#   "smooth": [{"part": {...}, "box": .., "iters": 4, "factor": 0.5, "pin": 32, "max_move": 0.0015, "soft_deg": 70}],
#                a lumpy part evened (Taubin smoothing, no shrinking, each vert moved at most max_move), verts on sharp
#                creases and open borders pinned, shaded smooth across facets up to soft_deg (polish)
#   "lines": [{"part": {...}, "box": .., "absx": .., "cf_at": 0.5 | "plane": {"co", "no"}, "width": 0.0012,
#              "tag": "rwlit"}],   a thin strip along a contour border or a plane cut, tagged (glow lines)
#   "contours": [{"part": {...}, "box": .., "absx": .., "field": "ny", "smooth": 2, "at": 0.5}],   cut a soft surface
#                along an iso-line of its smoothed vertex normals ("rz" + "axis": [x, y]: the distance from a bore's
#                axis, a clean circle); colour with {"cf": [lo, hi]} (smooth borders)
#   "nodes": [{"node": "mag", "part": {...}}, {"node": "grip", "part": {...}, "box": [lo, hi]}],  whole part / box cut
#   "unions": [{"parts": [{...base}, {...}, {...}], "tag": "bstar"}],   parts after the first get the tag
#   "inlays": [{"part": {...}, "tag": "mstar", "shape": "star", "points": 4, "R": 0.026, "r": 0.007, "c": [y, z],
#               "sides": [-1, 1], "proud": 0.0015, "turn": 0}],   a kit star let into a part's side faces (union);
#               "shape": "oval" with "ry", "rz" instead: an ellipse (a face's eyes and bill); "x": the side's |x|
#               where no vertex of the part lies inside the footprint (a big flat face); "x_min": a floor for it
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
#        rifle_front notch blade bead), gun_models' trigger / guard, or halo (a tilted ring on spokes, below);
#        with "pieces": brake (a ported muzzle brake + shroud), kblade (a katana blade, one kit solid from an outline:
#        sharp edge, spine, and curling waves, foam curls and dots cut into its flat face), candy (a striped round grip),
#        hoop (a striped pommel loop with gold collars)
#   "shell": ["body_wzA__pearl", "rwing"],      Route S shells: pieces or nodes (budget: <= 15k tris with shells)
#   "sheet": {"closeup": {"at": [x, y, z], "size": 0.16, "label": "front sight"}},   an extra close side view
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
    if 'matrix' in t:   # (rows = weapon x, y, z as raw directions: a model lying at any angle, measured by PCA)
        M = Matrix(t['matrix'])
        for i in range(3): M[i].normalize()
        return M
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
    for a in f.get('anchors', []):   # [raw point, weapon target, weight y, weight z]: any pair of matches (a katana's
        q = R @ Vector(a[0])          # guard face and blade tip instead of a gun's muzzle and grip)
        rows += [((q.y, 1.0, 0.0), a[1][1], a[2]), ((q.z, 0.0, 1.0), a[1][2], a[3])]
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
    for k, a in enumerate(f.get('anchors', [])):
        res['anchor %d miss_mm' % k] = [round((wp(a[0])[i] - a[1][i]) * 1000, 1) for i in range(3)]
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
    if 'max_tris' in sel:   # (an AND filter on what the other keys picked: a box's small parts only, e.g. rivets)
        out = {i for i in out if info[i]['tris'] < sel['max_tris']}
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


def normals_out(bm):
    """recalc_face_normals, then a check per connected part: its faces must point away from its middle (signed
       volume about its centroid > 0); a part that came out inside-out is turned the right way. (The angel's rail, cut
       open at the front-sight block, came back inside-out: Roblox culls back faces, so it would have vanished)"""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    pid, info = parts_of(bm)
    flipped = 0
    for p in info:
        c = B(p['centre'])
        vol = sum((f.calc_center_median() - c).dot(f.normal) * f.calc_area() for f in p['faces'])
        if vol < 0:
            bmesh.ops.reverse_faces(bm, faces=p['faces']); flipped += 1
            TURNED.append({'centre': [round(x, 3) for x in p['centre']], 'tris': p['tris']})
    bm.normal_update()
    return flipped


TURNED = []   # (the parts normals_out turned the right way, for the clean json)


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
    out = list(r['faces'])
    if out:   # (every triangle of every cap: the caller colours and turns them)
        t = bmesh.ops.triangulate(bm, faces=[f for f in out if len(f.verts) > 3], quad_method='BEAUTY', ngon_method='BEAUTY')
        out = [f for f in set(out) | set(t['faces']) if f.is_valid]
    return out


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
    # (a face is cut when any corner is in the box, not only its middle: a long Tripo triangle whose middle lies
    # outside would stay whole across the plane, and the cap would then close a loop far beyond it)
    faces = [f for f in bm.faces if f[lay] and (_inbox(W(f.calc_center_median()), op['box']) or
                                                any(_inbox(W(v.co), op['box']) for v in f.verts))]
    if 'no' in op:   # (any plane, weapon frame: {"co", "no"}; the side `no` points to is cut away)
        pco, pno = Vector(op['co']), Vector(op['no']).normalized()
        co, no = B(pco), B(pno) - B(Vector((0.0, 0.0, 0.0)))
        def beyond(c): return (c - pco).dot(pno) > 1e-6
    else:
        co, no = _plane(op.get('axis', 'y'), op['at'])
        k = AX[op.get('axis', 'y').upper()]
        keep_below = op.get('keep', 'below') == 'below'
        def beyond(c): return (c[k] > op['at'] + 1e-6) if keep_below else (c[k] < op['at'] - 1e-6)
    geom = list(set(faces) | {e for f in faces for e in f.edges} | {v for f in faces for v in f.verts})
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no, dist=1e-6)
    gone = [f for f in bm.faces if f[lay] and _inbox(W(f.calc_center_median()), op['box'], 1e-4) and beyond(W(f.calc_center_median()))]
    bmesh.ops.delete(bm, geom=gone, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    if loose: bmesh.ops.delete(bm, geom=loose, context='VERTS')
    if 'no' in op and op.get('cap', True):   # (only the cut's own opening is closed: a global fill would also cap the
        # openings a Tripo part keeps on purpose, e.g. the pocket a grip panel sits in, and z-fight with it)
        on = [e for e in bm.edges if e.is_boundary and all(abs((W(v.co) - pco).dot(pno)) < 1e-5 for v in e.verts)]
        r = bmesh.ops.holes_fill(bm, edges=on, sides=100000) if on else {'faces': []}
        caps = list(r['faces'])
        if caps: bmesh.ops.triangulate(bm, faces=[f for f in caps if len(f.verts) > 3], quad_method='BEAUTY', ngon_method='BEAUTY')
        return {'faces_cut': len(gone), 'caps': len(caps)}
    caps = fill_holes(bm, 100000) if op.get('cap', True) else []   # (cap false: an end hidden inside a kit part)
    return {'faces_cut': len(gone), 'caps': len(caps)}


def carve(bm, op):
    """a stepped Tripo block taken out to make room for a clean kit one: the selected parts cut along a box (weapon
       frame), the inside deleted, the cut capped. {"part", "box"}"""
    pid, info = parts_of(bm)
    ps = select_parts(op.get('part'), info, bm)
    inside = box_cut(bm, [f for f in bm.faces if pid[f] in ps], op['box'])
    bmesh.ops.delete(bm, geom=inside, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    if loose: bmesh.ops.delete(bm, geom=loose, context='VERTS')
    # (only the cut's openings, on the box's faces, are closed: not a pocket the part keeps, e.g. a grip panel's)
    lo, hi = op['box']
    def onplane(e):
        return any(all(abs(W(v.co)[k] - at) < 1e-5 for v in e.verts) for k in range(3) for at in (lo[k], hi[k]))
    on = [e for e in bm.edges if e.is_boundary and onplane(e)]
    caps = list(bmesh.ops.holes_fill(bm, edges=on, sides=100000)['faces']) if on else []
    if caps: bmesh.ops.triangulate(bm, faces=[f for f in caps if len(f.verts) > 3], quad_method='BEAUTY', ngon_method='BEAUTY')
    return {'faces_cut': len(inside), 'caps': len(caps)}


def press(bm, op):
    """a relief that tilts and sticks out laid flat: every vertex of the selected parts inside the box (weapon frame)
       standing out past |x| = `x_max` pressed back to it (an even face parallel to the side), and the relief's open
       foot (its border edges) sunk to |x| = `x_foot` so no gap shows under it. {"part", "box", "x_max", "x_foot"}"""
    pid, info = parts_of(bm)
    ps = select_parts(op.get('part'), info, bm)
    vs = {v for f in bm.faces if pid[f] in ps for v in f.verts if _inbox(W(v.co), op['box'])}
    n = m = 0
    xb = op.get('x_base')   # (mode "scale": everything standing out past x_base squeezed toward it so the highest point
    if xb is not None:      # lands on x_max: the relief keeps its shape, only thinner; nothing folds flat onto itself)
        peak = max((abs(W(v.co).x) for v in vs), default=xb)
        k = (op['x_max'] - xb) / max(peak - xb, 1e-6)
    for v in vs:
        p = W(v.co); s = 1.0 if p.x >= 0 else -1.0
        x0 = abs(p.x)
        if xb is not None:
            if x0 > xb:
                p.x = s * (xb + (x0 - xb) * k); v.co = B(p); n += 1
        elif abs(p.x) > op['x_max']:
            p.x = s * op['x_max']; v.co = B(p); n += 1
        if 'x_foot' in op and x0 >= op.get('foot_from', op['x_foot']) and any(e.is_boundary for e in v.link_edges):
            p.x = s * op['x_foot']; v.co = B(p); m += 1   # (only the relief's own foot: `foot_from` out, not the side's seams)
    return {'pressed': n, 'feet': m}


def straighten(bm, op):
    """a part that drifts sideways along its length (seen from the top) turned about the vertical so its front and back
       ends line up along z (the middle of its front third against its back third); centre: true also slides it so
       its middle is on the gun's centre plane (x = 0)"""
    pid, info = parts_of(bm)
    out = []
    for i in sorted(select_parts(op['part'], info, bm)):
        vs = list({v for f in info[i]['faces'] for v in f.verts})
        P = [W(v.co) for v in vs]
        z0, z1 = min(p.z for p in P), max(p.z for p in P)
        L = z1 - z0
        fr = [p.x for p in P if p.z < z0 + L / 3]; bk = [p.x for p in P if p.z > z1 - L / 3]
        xf, xb = (min(fr) + max(fr)) / 2, (min(bk) + max(bk)) / 2
        zf = sum(p.z for p in P if p.z < z0 + L / 3) / len(fr); zb = sum(p.z for p in P if p.z > z1 - L / 3) / len(bk)
        ang = math.atan2(xb - xf, zb - zf) if op.get('turn', True) else 0.0   # (its drift: x per z)
        c = sum(P, Vector()) / len(P)
        R = Matrix.Rotation(ang, 3, 'Y')    # (weapon frame: about y, turning x toward z)
        P = [c + R @ (p - c) for p in P]
        dx = 0.0
        if op.get('centre'):
            dx = -(min(p.x for p in P) + max(p.x for p in P)) / 2
        sh = Vector(op.get('shift', (0.0, 0.0, 0.0)))   # (every selected part the same move: a head with its eyes)
        for v, p in zip(vs, P): v.co = B(Vector((p.x + dx + sh.x, p.y + sh.y, p.z + sh.z)))
        out.append({'part': i, 'drift_mm': round((xb - xf) * 1000, 2), 'turned_deg': round(math.degrees(ang), 3),
                    'moved_x_mm': round(dx * 1000, 2)})
    return out


def mirror(bm, op):
    """the gun made mirror-symmetric about its centre plane (x = 0, the plane the fit's centre point sets): every part
       except the `keep` ones (one-sided props: a charm, a chain, a charging handle) is cut on the plane, its right half
       (x > 0) deleted and its left half (x < 0, the side first person sees) copied across, the seam welded"""
    pid, info = parts_of(bm)
    keep = set()
    for sel in op.get('keep', []): keep |= select_parts(sel, info, bm)
    lay = bm.faces.layers.int['_sel']
    for f in bm.faces: f[lay] = 0 if pid[f] in keep else 1
    fs = [f for f in bm.faces if f[lay]]
    geom = list(set(fs) | {e for f in fs for e in f.edges} | {v for f in fs for v in f.verts})
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=Vector((0, 0, 0)), plane_no=Vector((1, 0, 0)), dist=1e-6)
    gone = [f for f in bm.faces if f[lay] and W(f.calc_center_median()).x > 1e-7]
    bmesh.ops.delete(bm, geom=gone, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    if loose: bmesh.ops.delete(bm, geom=loose, context='VERTS')
    left = [f for f in bm.faces if f[lay]]
    seam = {v for f in left for v in f.verts if abs(v.co.x) < 1e-6}
    for v in seam: v.co.x = 0.0
    dup = bmesh.ops.duplicate(bm, geom=list(set(left) | {e for f in left for e in f.edges} | {v for f in left for v in f.verts}))
    nv = [g for g in dup['geom'] if isinstance(g, bmesh.types.BMVert)]
    nf = [g for g in dup['geom'] if isinstance(g, bmesh.types.BMFace)]
    for v in nv: v.co.x = -v.co.x
    bmesh.ops.reverse_faces(bm, faces=nf)
    on = [v for v in bm.verts if abs(v.co.x) < 1e-6 and v.link_faces]
    n0 = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=on, dist=op.get('weld', 1e-5))
    return {'kept_parts': sorted(keep), 'right_faces_deleted': len(gone), 'left_faces_copied': len(nf),
            'seam_verts_welded': n0 - len(bm.verts)}


def smooth_parts(bm, op):
    """a lumpy part made an even toy shape: Laplacian smoothing (volume kept) of the selected parts' faces inside the
       box, the verts on sharp edges (> pin degrees: a bill's crease, a rim) and on open borders pinned, so outlines
       and colour creases stay where they are. {"part", "box", "iters": 4, "factor": 0.6, "pin": 32}"""
    pid, info = parts_of(bm)
    ps = select_parts(op.get('part'), info, bm)
    box = op.get('box')
    fs = [f for f in bm.faces if pid[f] in ps and (box is None or _inbox(W(f.calc_center_median()), box))]
    vs = list({v for f in fs for v in f.verts})
    pin = math.radians(op.get('pin', 32.0))
    bm.normal_update()
    def pinned(v):
        for e in v.link_edges:
            lf = e.link_faces
            if len(lf) != 2: return True
            if lf[0].normal.angle(lf[1].normal, 0.0) > pin: return True
        return any(f not in fset for f in v.link_faces)
    fset = set(fs)
    free = [v for v in vs if not pinned(v)]
    before = {v: v.co.copy() for v in free}
    lam = op.get('factor', 0.5); mu = -1.04 * lam   # (Taubin: a smoothing step, then an inflating one: no shrinking)
    for _ in range(op.get('iters', 4)):
        for k in (lam, mu):
            new = {}
            for v in free:
                nb = [e.other_vert(v) for e in v.link_edges]
                if not nb: continue
                avg = sum((u.co for u in nb), Vector()) / len(nb)
                new[v] = v.co + (avg - v.co) * k
            for v, c in new.items(): v.co = c
    cap = op.get('max_move', 0.0015)   # (never more than this from where it was: the shape stays, only the noise goes)
    for v, c in before.items():
        d = v.co - c
        if d.length > cap: v.co = c + d.normalized() * cap
    bm.normal_update()
    moved = max(((v.co - c).length for v, c in before.items()), default=0.0)
    soft = bm.faces.layers.int.get('_soft')
    if soft is not None:   # (and shaded smooth across its facets: a toy shape, no facet noise; creases stay sharp)
        for f in fs: f[soft] = int(op.get('soft_deg', 70))
    return {'faces': len(fs), 'free_verts': len(free), 'pinned': len(vs) - len(free), 'max_move_mm': round(moved * 1000, 2)}


def planar(bm, op):
    """a face that should be flat made flat: the verts of the selected faces (inside the box, facing +-axis by nmin)
       moved onto one plane per side, at the median of their coordinates along the axis (a slide's or receiver's
       side, a panel). {"part", "box", "axis": "x", "nmin": 0.9, "sides": [-1, 1], "max_move": 0.002}"""
    pid, info = parts_of(bm)
    ps = select_parts(op.get('part'), info, bm)
    box = op.get('box'); k = AX[op.get('axis', 'x').upper()]; nmin = op.get('nmin', 0.9); lim = op.get('max_move', 0.002)
    out = []
    bm.normal_update()
    for s in op.get('sides', (-1, 1)):
        fs = []
        for f in bm.faces:
            if pid.get(f) not in ps: continue
            if box is not None and not _inbox(W(f.calc_center_median()), box): continue
            n = W(f.normal) - W(Vector((0.0, 0.0, 0.0)))
            if n[k] * s >= nmin: fs.append(f)
        vs = list({v for f in fs for v in f.verts})
        if not vs: continue
        vals = sorted(W(v.co)[k] for v in vs)
        if op.get('pick', 'median') == 'outer':   # (the outermost face of that side: a panel, not the walls inside it)
            sv = sorted(vals, key=lambda x: -x * s)
            med = sv[max(0, len(sv) // 10)]
        else:
            med = vals[len(vals) // 2]
        n = 0
        for v in vs:
            w = W(v.co)
            if abs(w[k] - med) <= lim:
                w[k] = med; v.co = B(w); n += 1
        out.append({'side': s, 'faces': len(fs), 'verts_moved': n, 'plane': round(med, 5)})
    bm.normal_update()
    return out


def _taubin(bm, verts, iters, lam=0.5):
    """volume-keeping smoothing of these verts (a smoothing step, then an inflating one)"""
    for _ in range(iters):
        for k in (lam, -1.04 * lam):
            new = {}
            for v in verts:
                nb = [e.other_vert(v) for e in v.link_edges]
                if nb: new[v] = v.co + (sum((u.co for u in nb), Vector()) / len(nb) - v.co) * k
            for v, c in new.items(): v.co = c


def _relax(bm, iters, flat_deg=25.0):
    """even triangles on the same surface: near-flat edges flipped to fatter triangles, then each vertex slid along
       the surface toward its neighbours' middle and put back onto the surface it started on (decimation slivers
       shade as streaks; even triangles catch light evenly)"""
    def flip():
        bm.normal_update()
        ok = [e for e in bm.edges if len(e.link_faces) == 2 and
              e.link_faces[0].normal.angle(e.link_faces[1].normal, 0.0) < math.radians(flat_deg)]
        if ok: bmesh.ops.beautify_fill(bm, faces=list({f for e in ok for f in e.link_faces}), edges=ok)
    flip()
    ref = BVHTree.FromBMesh(bm)
    for _ in range(iters):
        bm.normal_update()
        new = {}
        for v in bm.verts:
            nb = [e.other_vert(v) for e in v.link_edges]
            if len(nb) < 3: continue
            d = sum((u.co for u in nb), Vector()) / len(nb) - v.co
            d -= v.normal * d.dot(v.normal)
            p = v.co + d * 0.5
            hit = ref.find_nearest(p)
            new[v] = hit[0] if hit[0] is not None else p
        for v, c in new.items(): v.co = c
        flip()


def _iso_cut(bm, faces, val, t):
    """cut the faces along the iso-line val = t of a field on their verts (marching triangles); the new verts get t"""
    newv = set()
    for e in list({e for f in faces for e in f.edges}):
        a, b = e.verts
        if a not in val or b not in val: continue
        sa, sb = val[a] - t, val[b] - t
        if sa * sb >= 0 or abs(sa - sb) < 1e-9: continue
        fac = sa / (sa - sb)
        if fac < 0.04 or fac > 0.96:   # (a crossing next to a vertex: that vertex goes onto the line instead)
            val[a if fac < 0.04 else b] = t; continue
        pa, pb = a.co.copy(), b.co.copy()
        ne, nv = bmesh.utils.edge_split(e, a, fac)
        nv.co = pa.lerp(pb, fac)
        val[nv] = t; newv.add(nv)
    for f in list({f for v in newv for f in v.link_faces}):
        on = [v for v in f.verts if v in newv or abs(val.get(v, t + 1) - t) < 1e-9]
        if len(on) == 2 and not any(e for e in on[0].link_edges if e.other_vert(on[0]) is on[1]):
            try:
                bmesh.utils.face_split(f, on[0], on[1])
            except ValueError: pass
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])


def remesh(bm, op, tags):
    """a lumpy Tripo toy (a duck head, a bill, a relief) rebuilt as one even surface, each selected part on its own:
       voxel remesh (`voxel` m), `smooth` Taubin passes, decimated back to `ratio` x its old triangles, then drawn back
       onto the old part's size and outline by a SMOOTHED displacement (`fit`, `fit_smooth` passes: the old lumps
       do not come back, only its silhouette). Colour patches of the old part (`zones`: [{"tag", "where": a region
       condition, read on the old faces}]) are carried over by nearest face and cut along a smoothed border, so a
       region rule {"tag": ...} colours them with a clean edge. The new faces shade smooth up to `soft_deg`.
       {"part", "voxel": 0.0006, "smooth": 4, "ratio": 1.0, "fit": 1.0, "fit_smooth": 12, "soft_deg": 80, "zones": []}"""
    pid, info = parts_of(bm)
    ids = select_parts(op['part'], info, bm)
    groups = [info[i]['faces'] for i in sorted(ids)]
    if op.get('lobes'):   # (a fan of feathers / lobes: each patch between creases sharper than `lobes` degrees rebuilt
        # on its own, so the grooves between them stay clean; patches under `lobe_min` faces join a neighbour)
        bm.normal_update()
        split = []
        for fs in groups:
            fset = set(fs); left = set(fs); pats = []
            while left:
                g_ = grow(bm, [next(iter(left))], op['lobes'], fset); pats.append(g_); left -= g_
            big = [p for p in pats if len(p) >= op.get('lobe_min', 20)] or [max(pats, key=len)]
            for p in pats:
                if any(p is b for b in big): continue
                nbrs = [b for b in big if any(g in b for f in p for e in f.edges for g in e.link_faces)]
                (max(nbrs, key=len) if nbrs else big[0]).update(p)
            split += [list(b) for b in big]
        groups = split
    log = []
    for fs in groups:
        fs = [f for f in fs if f.is_valid]
        if not fs: continue
        before = sum(len(f.verts) - 2 for f in fs)
        P0 = [W(v.co) for v in {v for f in fs for v in f.verts}]
        lo0 = [min(p[a] for p in P0) for a in range(3)]; hi0 = [max(p[a] for p in P0) for a in range(3)]
        zsets = []
        if op.get('zones'):
            cx = Ctx(bm, tags, None)
            for z in op['zones']:
                zsets.append({f for f in fs if match(z['where'], f, cx)})
        bm.faces.index_update()
        order = sorted(fs, key=lambda f: f.index)
        zone_of = [next((k for k, zs in enumerate(zsets) if f in zs), -1) for f in order]
        sub = split_off(bm, order)   # (the i-th face of sub is order[i]; the other groups' faces stay valid)
        sub.faces.ensure_lookup_table()
        tree = BVHTree.FromBMesh(sub)
        is_open = any(e.is_boundary for e in sub.edges)
        fit_tree = tree
        o = _bm_obj(sub)
        if op.get('solidify') and is_open:   # (an open Tripo shell, a relief with no back: given a back first, or the
            # voxels see only a film and come out in crumbs; the fit then aims at the thickened shell, front AND back,
            # or the new back would be pulled through onto the old front)
            sm = o.modifiers.new('so', 'SOLIDIFY'); sm.thickness = op['solidify']; sm.offset = -1.0; sm.use_even_offset = True
            o2 = _bm_obj(sub.copy())
            sm2 = o2.modifiers.new('so', 'SOLIDIFY'); sm2.thickness = op['solidify']; sm2.offset = -1.0; sm2.use_even_offset = True
            sb = _obj_bm(o2); fit_tree = BVHTree.FromBMesh(sb); sb.free()
        m = o.modifiers.new('rm', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = op.get('voxel', 0.0006); m.adaptivity = 0.0
        nb = _obj_bm(o)
        bmesh.ops.triangulate(nb, faces=nb.faces[:])
        # (crumbs: any piece under 3% of the biggest goes)
        nb.verts.index_update()
        par = list(range(len(nb.verts)))
        def fnd(i):
            while par[i] != i:
                par[i] = par[par[i]]; i = par[i]
            return i
        for e in nb.edges:
            a_, b_ = fnd(e.verts[0].index), fnd(e.verts[1].index)
            if a_ != b_: par[a_] = b_
        comp = {}
        for f in nb.faces: comp.setdefault(fnd(f.verts[0].index), []).append(f)
        big = max(len(c) for c in comp.values())
        crumbs = [f for c in comp.values() if len(c) < 0.03 * big for f in c]
        if crumbs:
            bmesh.ops.delete(nb, geom=crumbs, context='FACES')
            bmesh.ops.delete(nb, geom=[v for v in nb.verts if not v.link_faces], context='VERTS')
        voxel_tris = len(nb.faces)
        _taubin(nb, list(nb.verts), op.get('smooth', 4))
        target = max(24, int(before * op.get('ratio', 1.0)))
        if len(nb.faces) > target:
            o = _bm_obj(nb); nb.free()
            m = o.modifiers.new('dec', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = target / voxel_tris
            m.use_collapse_triangulate = True
            nb = _obj_bm(o)
            bmesh.ops.dissolve_degenerate(nb, edges=nb.edges[:], dist=1e-7)
            bmesh.ops.triangulate(nb, faces=[f for f in nb.faces if len(f.verts) > 3])
        _relax(nb, op.get('relax', 4))
        _taubin(nb, list(nb.verts), op.get('smooth_after', 1), lam=0.35)
        # back onto the old size and outline: the displacement to the old surface, low-passed over the new one
        disp = {}
        for v in nb.verts:
            hit = fit_tree.find_nearest(v.co)
            disp[v] = (hit[0] - v.co) if hit[0] is not None else Vector()
        for _ in range(op.get('fit_smooth', 12)):
            disp = {v: (disp[v] + sum((disp[e.other_vert(v)] for e in v.link_edges), Vector())) / (1 + len(v.link_edges))
                    for v in nb.verts}
        for v in nb.verts: v.co += disp[v] * op.get('fit', 1.0)
        dm = op.get('dome')   # ({"c", "r", "y0", "blend"}: a head cut flat on top made round: above y0 the surface
        if dm:                # eased onto a sphere, fully by y0 + blend)
            dc = Vector(dm['c'])
            for v in nb.verts:
                p = W(v.co)
                u = (p.y - dm['y0']) / dm['blend']
                if u <= 0: continue
                wgt = 1.0 if u >= 1 else 3 * u * u - 2 * u ** 3
                v.co = B(p.lerp(dc + (p - dc).normalized() * dm['r'], wgt))
        for cl in op.get('clamp', []):   # ({"box", "y_max"}: kept under a cap sitting on it, e.g. a crown's base)
            for v in nb.verts:
                p = W(v.co)
                if _inbox(p, cl['box']) and p.y > cl['y_max']:
                    p.y = cl['y_max']; v.co = B(p)
        for nm in ('tag', 'node', '_sel', '_soft'):
            if nm not in nb.faces.layers.int: nb.faces.layers.int.new(nm)
        if 'cf' not in nb.verts.layers.float: nb.verts.layers.float.new('cf')
        # the colour patches, carried over by nearest old face, cut along a smoothed border
        cuts = []
        for k, z in enumerate(op.get('zones', [])):
            tid = tags.setdefault(z['tag'], len(tags) + 1)
            val = {}
            for v in nb.verts:
                hit = tree.find_nearest(v.co)
                val[v] = 1.0 if hit[2] is not None and zone_of[hit[2]] == k else 0.0
            for _ in range(z.get('smooth', 2)):
                val = {v: (val[v] + sum(val[e.other_vert(v)] for e in v.link_edges)) / (1 + len(v.link_edges)) for v in nb.verts}
            n0 = len(nb.faces)
            _iso_cut(nb, list(nb.faces), val, 0.5)
            lay = nb.faces.layers.int['tag']
            hits = 0
            for f in nb.faces:
                if sum(val.get(v, 0.0) for v in f.verts) / len(f.verts) > 0.5:
                    f[lay] = tid; hits += 1
            cuts.append({'tag': z['tag'], 'old_faces': len(zsets[k]), 'faces': hits, 'cut_tris': len(nb.faces) - n0})
        soft = nb.faces.layers.int['_soft']
        for f in nb.faces: f[soft] = int(op.get('soft_deg', 80))
        P = [W(v.co) for v in nb.verts]
        lo1 = [min(p[a] for p in P) for a in range(3)]; hi1 = [max(p[a] for p in P) for a in range(3)]
        sub.free()
        log.append({'from': before, 'voxel_tris': voxel_tris, 'to': len(nb.faces), 'zones': cuts,
                    'open': sum(1 for e in nb.edges if len(e.link_faces) != 2),
                    'lo': [round(x, 4) for x in lo1], 'hi': [round(x, 4) for x in hi1],
                    'size_change_mm': [round(((hi1[a] - lo1[a]) - (hi0[a] - lo0[a])) * 1000, 2) for a in range(3)],
                    'centre_shift_mm': [round(((hi1[a] + lo1[a]) - (hi0[a] + lo0[a])) * 500, 2) for a in range(3)]})
        merge_in(bm, nb)
    return log


def relief(bm, op):
    """a flat Tripo relief (a cloud, a wing on a grip panel) rebuilt clean from its own side outline: the part seen
       along x, its outline read as a distance from its middle per angle (`bins`), that curve smoothed (`smooth`
       passes: the jags go, the lobes stay), and a new relief extruded through it from its old back to its old face
       (`face_pct` percentile of how far out it reaches: a stray spike does not count) with a rounded front edge
       (`bevel` m, `bevel_steps`); `n` points round, evenly along it. {"part", "n": 44, "bins": 240, "smooth": 4,
       "bevel": 0.001, "bevel_steps": 1, "back_pct": 0.03, "face_pct": 0.97}"""
    pid, info = parts_of(bm)
    ids = select_parts(op['part'], info, bm)
    groups = [info[i]['faces'] for i in sorted(ids)]
    log = []
    for fs in groups:
        fs = [f for f in fs if f.is_valid]
        if not fs: continue
        before = sum(len(f.verts) - 2 for f in fs)
        vs = list({v for f in fs for v in f.verts})
        P = [W(v.co) for v in vs]
        side = 1.0 if sum(p.x for p in P) > 0 else -1.0
        ax = sorted(abs(p.x) for p in P)
        x_back = op.get('back', ax[int(len(ax) * op.get('back_pct', 0.03))])
        x_face = op.get('face', ax[min(len(ax) - 1, int(len(ax) * op.get('face_pct', 0.97)))])
        # the outline seen along x: dense samples on every edge, as (y, z)
        S = []
        x_min = x_back + op.get('min_h', 0.0) * (x_face - x_back)   # (a low ramp below this height is not outline)
        for e in {e for f in fs for e in f.edges}:
            a, b = W(e.verts[0].co), W(e.verts[1].co)
            k = max(1, int((a - b).length / 0.0004))
            for j in range(k + 1):
                q = a.lerp(b, j / k)
                if abs(q.x) >= x_min: S.append((q.y, q.z))
        cy = op.get('centre', [sum(s[0] for s in S) / len(S), sum(s[1] for s in S) / len(S)])
        nb_ = op.get('bins', 240)
        rad = [0.0] * nb_
        for y, z in S:
            th = math.atan2(z - cy[1], y - cy[0]) % (2 * math.pi)
            i = int(th / (2 * math.pi) * nb_) % nb_
            rad[i] = max(rad[i], math.hypot(y - cy[0], z - cy[1]))
        for i in range(nb_):   # (an empty bin: its neighbours' mean)
            if rad[i] == 0.0:
                j0 = next(j for j in range(1, nb_) if rad[(i - j) % nb_] > 0); j1 = next(j for j in range(1, nb_) if rad[(i + j) % nb_] > 0)
                rad[i] = (rad[(i - j0) % nb_] * j1 + rad[(i + j1) % nb_] * j0) / (j0 + j1)
        for _ in range(op.get('smooth', 4)):
            rad = [(rad[i - 1] + 2 * rad[i] + rad[(i + 1) % nb_]) / 4.0 for i in range(nb_)]
        n = op.get('n', 44)
        def r_at(th):
            u = (th % (2 * math.pi)) / (2 * math.pi) * nb_ - 0.5
            i0 = int(math.floor(u)); fr = u - i0
            return rad[i0 % nb_] * (1 - fr) + rad[(i0 + 1) % nb_] * fr
        dense = [(cy[0] + r_at(2 * math.pi * j / 1440) * math.cos(2 * math.pi * j / 1440),
                  cy[1] + r_at(2 * math.pi * j / 1440) * math.sin(2 * math.pi * j / 1440)) for j in range(1440)]
        cl = op.get('clamp', {})   # ({"y": [lo, hi], "z": [lo, hi]}: kept off an edge it would lie flush with)
        ylo, yhi = cl.get('y', [-9, 9]); zlo, zhi = cl.get('z', [-9, 9])
        dense = [(min(max(y, ylo), yhi), min(max(z, zlo), zhi)) for y, z in dense]
        acc = [0.0]   # (the n points evenly spaced ALONG the outline: a long shape's far lobes get their share)
        for j in range(1, 1441): acc.append(acc[-1] + math.dist(dense[j - 1], dense[j % 1440]))
        O, j = [], 0
        for q in range(n):
            s = acc[-1] * q / n
            while acc[j + 1] < s: j += 1
            fr = (s - acc[j]) / max(acc[j + 1] - acc[j], 1e-12)
            a, b = dense[j], dense[(j + 1) % 1440]
            O.append((a[0] + (b[0] - a[0]) * fr, a[1] + (b[1] - a[1]) * fr))
        N2 = []   # (outward 2D normals of the outline)
        for j in range(n):
            a, b = Vector(O[j - 1]), Vector(O[(j + 1) % n])
            t2 = (b - a).normalized(); nn = Vector((t2.y, -t2.x))
            if nn.dot(Vector(O[j]) - Vector(cy)) < 0: nn = -nn
            N2.append(nn)
        bev = op.get('bevel', 0.001); bs = op.get('bevel_steps', 1)
        rings = []
        def ring_at(xa, inset):
            rings.append([(side * xa, O[j][0] - N2[j].x * inset, O[j][1] - N2[j].y * inset) for j in range(n)])
        ring_at(x_back, 0.0)
        ring_at(x_face - bev, 0.0)
        for s in range(1, bs + 1):
            al = math.pi / 2 * s / bs
            ring_at(x_face - bev + bev * math.sin(al), bev * (1 - math.cos(al)))
        split_off(bm, fs).free()
        # the new relief, into bm: sides smooth with the given normals, the face flat (a cap)
        new = bmesh.new()
        V = [[new.verts.new(B(Vector(p))) for p in rg] for rg in rings]
        for i in range(len(rings) - 1):
            for k in range(n):
                j = (k + 1) % n
                new.faces.new([V[i][k], V[i][j], V[i + 1][j], V[i + 1][k]])
        new.faces.new(V[0][::-1]); new.faces.new(V[-1])
        bmesh.ops.recalc_face_normals(new, faces=new.faces[:])
        bmesh.ops.triangulate(new, faces=new.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
        for nm in ('tag', 'node', '_sel', '_soft'): new.faces.layers.int.new(nm)
        new.verts.layers.float.new('cf')
        soft = new.faces.layers.int['_soft']
        new.normal_update()
        for f in new.faces:   # (walls and the rounded edge shade smooth; the flat face and the hidden back stay flat)
            if abs(W(f.normal).x - W(Vector()).x) < 0.95: f[soft] = 80
        log.append({'from': before, 'to': len(new.faces), 'side': int(side), 'x_back': round(x_back, 4), 'x_face': round(x_face, 4),
                    'centre': [round(cy[0], 4), round(cy[1], 4)], 'r': [round(min(rad), 4), round(max(rad), 4)]})
        merge_in(bm, new)
    return log


def _span(P):
    lo = Vector([min(p[k] for p in P) for k in range(3)]); hi = Vector([max(p[k] for p in P) for k in range(3)])
    return [round(x, 4) for x in lo], [round(x, 4) for x in hi]


def reshape(bm, op):
    """re-pose each selected part (a wing; its mirror twin on the other side gets the same, x mirrored), weapon frame:
       side_flat  turn it about its middle so its thinnest direction (PCA) faces straight out of its side (no flare)
       scale      uniform, about `pivot` (given for the right side, x mirrored on the left; default its middle)
       thick      squash across (x) to this thickness, about its middle
       x_in       slide across so its inner face sits at |x| = x_in (sunk into the body, then fused by a union)
       y_top / z_back / z_front   slide so its highest point / its back / its front end is there
       sharpen    {"bin": deg, "prom": m, "tip": m, "pinch": 0..1, "radius": m, "notch": m}: feather tips found as the
                  local maxima of the outline's distance from the pivot (a fan's tips), each pulled out along its own
                  direction and pinched to a point; the notches between them pulled in (deeper cuts)"""
    import numpy as np
    pid, info = parts_of(bm)
    ids = select_parts(op['part'], info, bm)
    log = []
    for i in sorted(ids):
        vs = list({v for f in info[i]['faces'] for v in f.verts})
        P = [W(v.co) for v in vs]
        before = _span(P)
        side = 1.0 if sum(p.x for p in P) > 0 else -1.0
        c = sum(P, Vector()) / len(P)
        if op.get('side_flat'):
            A = np.array([list(p - c) for p in P])
            w, V = np.linalg.eigh(A.T @ A)
            n = Vector(V[:, 0].tolist())
            if n.x * side < 0: n = -n
            q = n.rotation_difference(Vector((side, 0.0, 0.0)))
            P = [c + q @ (p - c) for p in P]
        pv = Vector(op['pivot']) if 'pivot' in op else c.copy()
        pv.x = side * abs(pv.x)
        sc = op.get('scale', 1.0)
        P = [pv + (p - pv) * sc for p in P]
        if 'scale3' in op:   # (per axis, weapon frame, about the pivot: a crown squashed under the sight line)
            k3 = op['scale3']
            P = [Vector((pv.x + (p.x - pv.x) * k3[0], pv.y + (p.y - pv.y) * k3[1], pv.z + (p.z - pv.z) * k3[2])) for p in P]
        if 'tilt' in op:   # (degrees about x through the pivot, its top leaning forward toward -z: a crown on a brow)
            ca, sa = math.cos(math.radians(op['tilt'])), math.sin(math.radians(op['tilt']))
            P = [Vector((p.x, pv.y + (p.y - pv.y) * ca + (p.z - pv.z) * sa, pv.z - (p.y - pv.y) * sa + (p.z - pv.z) * ca)) for p in P]
        if 'thick' in op:
            xs = [p.x for p in P]; cx = (max(xs) + min(xs)) / 2; k = op['thick'] / max(max(xs) - min(xs), 1e-6)
            P = [Vector((cx + (p.x - cx) * k, p.y, p.z)) for p in P]
        d = Vector((0.0, 0.0, 0.0))
        if 'x_in' in op: d.x = side * (op['x_in'] - min(abs(p.x) for p in P))
        if 'y_top' in op: d.y = op['y_top'] - max(p.y for p in P)
        if 'z_back' in op: d.z = op['z_back'] - max(p.z for p in P)
        if 'z_front' in op: d.z = op['z_front'] - min(p.z for p in P)
        mv = op.get('move', (0, 0, 0)); d += Vector((side * mv[0], mv[1], mv[2]))
        d += Vector(op.get('shift', (0, 0, 0)))   # (absolute: not mirrored by side)
        P = [p + d for p in P]
        root = pv + d
        tips = []
        sh = op.get('sharpen')
        if sh:
            P, tips = _sharpen(P, root, sh)
        for v, p in zip(vs, P): v.co = B(p)
        xs = [abs(p.x) for p in P]
        log.append({'part': i, 'side': int(side), 'before': before, 'after': _span(P), 'tips': len(tips),
                    'thick_after': round(max(xs) - min(xs), 4), 'top_y': round(max(p.y for p in P), 4),
                    'out_x': round(max(xs), 4)})
    return log


def _sharpen(P, root, sh):
    """see reshape(): in the side plane (z, y) about root"""
    q = [Vector((p.z - root.z, p.y - root.y)) for p in P]
    th = [math.degrees(math.atan2(v.y, v.x)) for v in q]
    r = [v.length for v in q]
    bw = sh.get('bin', 3.0)
    best = {}
    for k, (a, rr) in enumerate(zip(th, r)):
        b = int(math.floor(a / bw))
        if b not in best or rr > r[best[b]]: best[b] = k
    keys = sorted(best)
    rmax = [r[best[b]] for b in keys]
    w = sh.get('window', 3)
    prom = sh.get('prom', 0.006)
    tips, notches = [], []
    for j in range(len(keys)):
        lo_, hi_ = max(0, j - w), min(len(keys), j + w + 1)
        nb = rmax[lo_:hi_]
        if rmax[j] == max(nb) and rmax[j] - min(nb) >= prom and 0 < j < len(keys) - 1: tips.append(best[keys[j]])
        if rmax[j] == min(nb) and max(nb) - rmax[j] >= prom and 0 < j < len(keys) - 1: notches.append(best[keys[j]])
    rad, e, pinch, nd = sh.get('radius', 0.012), sh.get('tip', 0.004), sh.get('pinch', 0.5), sh.get('notch', 0.0)
    out = [v.copy() for v in q]
    for t in tips:
        T = q[t]; a = T.normalized()
        for k, v in enumerate(q):
            dv = v - T
            dist = dv.length
            if dist >= rad: continue
            along = dv.dot(a)
            perp = dv - a * along
            wgt = (1 - dist / rad) ** 2
            out[k] = out[k] + a * (e * wgt) - perp * (pinch * wgt)
    for t in notches:
        N = q[t]; a = N.normalized()
        for k, v in enumerate(q):
            dist = (v - N).length
            if dist >= rad * 0.7: continue
            wgt = (1 - dist / (rad * 0.7)) ** 2
            out[k] = out[k] - a * (nd * wgt)
    return [Vector((p.x, root.y + o.y, root.z + o.x)) for p, o in zip(P, out)], tips


def _faces_of(bm, op):
    """the faces an op works on: its part selector, then an optional box and |x| range on face centres"""
    pid, info = parts_of(bm)
    ps = select_parts(op.get('part'), info, bm)
    fs = [f for f in bm.faces if pid[f] in ps]
    if 'box' in op: fs = [f for f in fs if _inbox(W(f.calc_center_median()), op['box'])]
    if 'absx' in op: fs = [f for f in fs if op['absx'][0] <= abs(W(f.calc_center_median()).x) <= op['absx'][1]]
    return fs


def contour(bm, op):
    """a clean colour border on a soft Tripo surface: a field on the vertices (a component of the vertex normal,
       weapon frame: "nx" / "ny" / "nz", or "anx" for |nx|), smoothed over the surface `smooth` times, and the faces CUT
       along its iso-line at `at` (marching triangles), so a region rule {"cf": [lo, hi]} on the field gives a smooth
       border instead of one that steps along the triangles. The field is kept in the vertex layer 'cf'"""
    fs = _faces_of(bm, op)
    lay = bm.verts.layers.float['cf']
    bm.normal_update()
    verts = {v for f in fs for v in f.verts}
    fld = op.get('field', 'ny')
    if fld == 'rz':   # distance from the line along z through op['axis'] = [x, y] (a bore's rim)
        ax_ = op.get('axis', [0.0, 0.0])
        val = {v: math.hypot(W(v.co).x - ax_[0], W(v.co).y - ax_[1]) for v in verts}
    else:
        k = AX[fld[-1].upper()]
        val = {v: (abs(W(v.normal)[k]) if fld.startswith('a') else W(v.normal)[k]) for v in verts}
    for _ in range(op.get('smooth', 2)):
        nv = {}
        for v in verts:
            nb = [e.other_vert(v) for e in v.link_edges if e.other_vert(v) in verts]
            nv[v] = (val[v] + sum(val[u] for u in nb)) / (1 + len(nb))
        val = nv
    t = op['at']
    for v in verts: v[lay] = val[v]
    newv = set()
    for e in list({e for f in fs for e in f.edges}):
        a, b = e.verts
        if a not in val or b not in val: continue
        sa, sb = val[a] - t, val[b] - t
        if sa * sb >= 0 or abs(sa - sb) < 1e-9: continue
        fac = sa / (sa - sb)
        if fac < 0.02 or fac > 0.98:   # (a crossing next to a vertex: move that vertex onto the line instead)
            v = a if fac < 0.02 else b
            v[lay] = t; continue
        pa, pb = a.co.copy(), b.co.copy()
        ne, nv = bmesh.utils.edge_split(e, a, fac)
        nv.co = pa.lerp(pb, fac)
        nv[lay] = t
        newv.add(nv)
    cut = 0
    for f in list({f for v in newv for f in v.link_faces}):
        on = [v for v in f.verts if v in newv]
        if len(on) == 2 and not any(e for e in on[0].link_edges if e.other_vert(on[0]) is on[1]):
            try:
                bmesh.utils.face_split(f, on[0], on[1]); cut += 1
            except ValueError: pass
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    return {'faces': len(fs), 'cuts': cut}


def _inpoly(z, y, poly):
    """is (z, y) inside the closed polygon [(z, y), ...] (even-odd)"""
    inside = False
    n = len(poly)
    for i in range(n):
        za, ya = poly[i]; zb, yb = poly[(i + 1) % n]
        if (ya > y) != (yb > y):
            zc = za + (y - ya) * (zb - za) / (yb - ya)
            if z < zc: inside = not inside
    return inside


def imprint(bm, ok, polys, sides=(-1, 1), nmin=0.35):
    """a flat painted shape CUT INTO a surface (no picture, nothing laid on top: no flicker): every outline segment of
       each closed polygon [(z, y), ...] (weapon frame, projected along x onto the faces that face side s) bisects
       the faces near it along the plane through the segment and the x axis; then the faces whose middle falls
       inside a polygon are returned with its index (the last polygon wins: a foam curl inside a wave).
       ok(f) -> the faces that may be cut (a mark carried onto the pieces bisect splits off). returns {face: index}"""
    lay = bm.faces.layers.int['_sel']
    for f in bm.faces: f[lay] = 1 if ok(f) else 0
    orig = bm.edges.layers.int.get('_orig') or bm.edges.layers.int.new('_orig')
    for e in bm.edges: e[orig] = 1   # (the edges before the cuts: their split halves keep the mark, the cuts do not)
    def facing(f):
        return any(f.normal.x * s >= nmin for s in sides)   # (weapon x = Blender x)
    for poly in polys:
        n = len(poly)
        for i in range(n):
            (za, ya), (zb, yb) = poly[i], poly[(i + 1) % n]
            if abs(za - zb) + abs(ya - yb) < 1e-7: continue
            lz, hz = min(za, zb) - 2e-4, max(za, zb) + 2e-4
            ly, hy = min(ya, yb) - 2e-4, max(ya, yb) + 2e-4
            fs = []
            for f in bm.faces:
                if not f[lay] or not facing(f): continue
                zs = [-v.co.y for v in f.verts]; ys = [v.co.z for v in f.verts]   # (weapon z = -Blender y, y = Blender z)
                if max(zs) < lz or min(zs) > hz or max(ys) < ly or min(ys) > hy: continue
                fs.append(f)
            if not fs: continue
            geom = list(set(fs) | {e for f in fs for e in f.edges} | {v for f in fs for v in f.verts})
            nw = Vector((0.0, -(zb - za), (yb - ya))).normalized()   # (weapon frame: x cross the segment)
            bmesh.ops.bisect_plane(bm, geom=geom, plane_co=B((0.0, ya, za)), plane_no=B(nw) - B((0.0, 0.0, 0.0)), dist=1e-7)
    bm.normal_update()
    # every cut line ran right across the faces it touched: merge the slivers back (coplanar neighbours of the same
    # class: inside polygon k, or outside), so only the outlines stay as new edges
    tagl = bm.faces.layers.int.get('tag')   # (and never across an earlier decal's or inlay's border)
    for f in [f for f in bm.faces if f[lay]]:
        k = 0
        if facing(f):
            c = f.calc_center_median(); z, y = -c.y, c.z
            for i, poly in enumerate(polys):
                if _inpoly(z, y, poly): k = i + 1
        f.material_index = (f[tagl] if tagl else 0) * 64 + k
    # (a cut edge with the same class on both sides is only the rest of a cut line: dissolve it, and the corner it
    # left on an old edge with it; the outlines, between classes, stay)
    edges = [e for e in bm.edges if not e[orig] and len(e.link_faces) == 2 and all(f[lay] for f in e.link_faces)
             and e.link_faces[0].material_index == e.link_faces[1].material_index]
    if edges:
        try: bmesh.ops.dissolve_edges(bm, edges=edges, use_verts=True, use_face_split=False)
        except Exception as ex: print('imprint: dissolve skipped', ex)
    out = {}
    for f in bm.faces:
        if not f[lay]: continue
        if f.material_index % 64 > 0: out[f] = f.material_index % 64 - 1
        f.material_index = 0
    return out


def decals(bm, op, tags):
    """the recipe's painted shapes: {"part": .., "box": .., "sides": [-1, 1], "nmin": 0.35, "tag": "wave",
       "polys": [[[z, y], ...], ...]} -> the faces inside get the tag (regions colour it)"""
    pid, info = parts_of(bm)
    ps = select_parts(op.get('part'), info, bm)
    box = op.get('box')
    def ok(f):
        return pid.get(f) in ps and (box is None or _inbox(W(f.calc_center_median()), box))
    hit = imprint(bm, ok, op['polys'], op.get('sides', (-1, 1)), op.get('nmin', 0.35))
    tid = tags.setdefault(op['tag'], len(tags) + 1)
    lay = bm.faces.layers.int['tag']
    for f in hit: f[lay] = tid
    return {'tag': op['tag'], 'faces': len(hit), 'polys': len(op['polys'])}


def lines(bm, op, tags):
    """a thin crisp strip (a glow line) along a border on the op's faces: the contour iso-line of field value `cf_at`
       (the edges whose two corners carry it, see contour()) or a plane cut (`plane`: {"co", "no"}, weapon frame); those
       edges are bevelled `width` to each side and the new faces tagged `tag` (colour them with {"tag": ..})"""
    lay = bm.verts.layers.float['cf']
    tl = bm.faces.layers.int['tag']
    if 'plane' in op:
        fs = _faces_of(bm, op)
        co, no = B(op['plane']['co']), B(op['plane']['no']).normalized()
        geom = list(set(fs) | {e for f in fs for e in f.edges} | {v for f in fs for v in f.verts})
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no, dist=1e-6)
        fset = set(_faces_of(bm, op))
        on = lambda v: abs((v.co - co).dot(no)) < 1e-6
    else:
        fset = set(_faces_of(bm, op))
        t = op['cf_at']
        on = lambda v: abs(v[lay] - t) < 1e-6
    eds = [e for e in bm.edges if on(e.verts[0]) and on(e.verts[1]) and len(e.link_faces) == 2
           and all(f in fset for f in e.link_faces)]
    if not eds: return {'tag': op['tag'], 'edges': 0}
    res = bmesh.ops.bevel(bm, geom=eds, offset=op.get('width', 0.0012), offset_type='OFFSET', segments=1, profile=0.5,
                          affect='EDGES', clamp_overlap=True)
    tid = tags.setdefault(op['tag'], len(tags) + 1)
    for f in res['faces']: f[tl] = tid
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    return {'tag': op['tag'], 'edges': len(eds), 'faces': len(res['faces'])}


def blend(bm, op):
    """pull an overhanging lip flush: every vertex of the op's faces sticking out past |x| = to is drawn in toward it,
       fully below `fade.from` (along fade.axis) and not at all at `fade.to`"""
    fs = _faces_of(bm, op)
    fd = op['fade']; k = AX[fd['axis'].upper()]
    n = 0
    for v in {v for f in fs for v in f.verts}:
        w_ = W(v.co)
        if abs(w_.x) <= op['to']: continue
        u = (w_[k] - fd['from']) / (fd['to'] - fd['from'])
        wgt = 1.0 if u <= 0 else (0.0 if u >= 1 else 1 - (3 * u * u - 2 * u ** 3))   # (smoothstep)
        if wgt <= 0: continue
        sx = 1.0 if w_.x > 0 else -1.0
        w_.x = sx * (op['to'] + (abs(w_.x) - op['to']) * (1 - wgt))
        v.co = B(w_); n += 1
    return {'verts_moved': n}


def rims(bm, op, tags):
    """a chamfer `width` wide round the outer face of every tagged (fused) part: the edges between a face looking out
       of the gun's side (|n.x| > 0.6, away from the middle) and a wall (|n.x| < 0.5). Seen from the side it is the
       emblem's trim line (colour it with an `an` x rule). After the unions: a bevelled solid fed to an EXACT boolean
       lost most of itself (the angel's left rear wing)"""
    lay = bm.faces.layers.int['tag']
    want = {tags[t] for t in (op['tag'] if isinstance(op['tag'], list) else [op['tag']]) if t in tags}
    bm.normal_update()
    eds = set()
    for e in bm.edges:
        lf = e.link_faces
        if len(lf) != 2 or lf[0][lay] not in want or lf[1][lay] not in want: continue
        ca = W(lf[0].calc_center_median()); side = 1.0 if ca.x > 0 else -1.0
        na, nb = W(lf[0].normal), W(lf[1].normal)
        if (na.x * side > 0.6 and abs(nb.x) < 0.5) or (nb.x * side > 0.6 and abs(na.x) < 0.5): eds.add(e)
    if eds:
        bmesh.ops.bevel(bm, geom=list(eds), offset=op['width'], offset_type='OFFSET', segments=1, profile=0.5,
                        affect='EDGES', clamp_overlap=True)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    return {'tag': op['tag'], 'edges': len(eds)}


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
        if il.get('shape') == 'oval':   # (a painted-on face's eye or bill: an ellipse ry tall, rz long)
            ry, rz, nn = il['ry'], il['rz'], il.get('n', 20)
            poly = [(cy + ry * math.sin(2 * math.pi * i / nn), cz + rz * math.cos(2 * math.pi * i / nn)) for i in range(nn)]
        else:
            poly = star_outline(cy, cz, il['R'], il['r'], il.get('points', 4), il.get('turn', 0.0))
        tools = []
        tops = []
        for sx in il.get('sides', [-1, 1]):
            # the surface's height under the star: the farthest the part reaches out on that side inside its footprint
            ys = [p[0] for p in poly]; zs = [p[1] for p in poly]
            xs = [abs(W(v.co).x) for v in base.verts if sx * W(v.co).x > 0 and min(ys) <= W(v.co).y <= max(ys) and min(zs) <= W(v.co).z <= max(zs)]
            if 'x_min' in il: xs.append(il['x_min'])   # (a floor: the corners in a small footprint can all be inside ones)
            top = (max(xs) if xs else il.get('x', 0.03)) + il.get('proud', 0.0015)
            inner = max(0.002, top - il.get('depth', 0.012))
            tools.append(star_prism(poly, sx * inner, sx * top))
            tops.append([sx, len(xs), round(top, 4)])
        n0 = tri_count(base)
        out = union_bms(base, tools)
        tid = tags.setdefault(il['tag'], len(tags) + 1)
        lay = out.faces.layers.int.get('tag') or out.faces.layers.int.new('tag')
        for f in out.faces:
            if f.material_index == 1: f[lay] = tid
            f.material_index = 0
        log.append({'tag': il['tag'], 'base_tris': n0, 'after': tri_count(out), 'tops': tops})
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
        elif k == 'cf':     # [lo, hi]: the face's contour field (its corners' mean), see contour()
            lay = cx.bm.verts.layers.float['cf']
            m = sum(v[lay] for v in f.verts) / len(f.verts)
            if not (v[0] - 1e-6 <= m <= v[1] + 1e-6): return False
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
    soft = bm.faces.layers.int.get('_soft')
    for f in bm.faces: f.smooth = True
    for e in bm.edges:
        fs = e.link_faces
        el = lim
        if soft is not None and len(fs) == 2 and fs[0][soft] and fs[1][soft]:   # (a smoothed toy shape)
            el = max(lim, math.radians(min(fs[0][soft], fs[1][soft])))
        e.smooth = len(fs) == 2 and fs[0].normal.angle(fs[1].normal, 0.0) < el
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
        out[k] = {'color': v, 'kind': 'p', 'alpha': 1.0} if isinstance(v, str) else             {'color': v[0], 'kind': v[1], 'alpha': float(v[2]) if len(v) > 2 else 1.0}   # ([colour, 'g', 0.7]: glass)
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
    for nm in ('tag', 'node', '_sel', '_soft'): bm.faces.layers.int.new(nm)   # (all working layers up front)
    bm.verts.layers.float.new('cf')
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
    normals_out(bm)
    meta['nonmanifold_after_fill'] = sum(1 for e in bm.edges if not e.is_manifold)
    meta['parts_turned_out'] = 0
    meta['decimate'] = decimate_parts(bm, rec)
    meta['nonmanifold_after_decimate'] = sum(1 for e in bm.edges if not e.is_manifold)
    meta['straighten'] = [straighten(bm, op) for op in rec.get('straighten', [])]
    if rec.get('mirror'): meta['mirror'] = mirror(bm, rec['mirror'])
    meta['flatten'] = [flatten(bm, op) for op in rec.get('flatten', [])]
    meta['nonmanifold_after_flatten'] = sum(1 for e in bm.edges if not e.is_manifold)
    meta['reshape'] = [reshape(bm, op) for op in rec.get('reshape', [])]
    meta['blends'] = [blend(bm, op) for op in rec.get('blend', [])]
    meta['carve'] = [carve(bm, op) for op in rec.get('carve', [])]     # (polish 2: stepped blocks out, kit ones in)
    tags = {}
    meta['remesh'] = [remesh(bm, op, tags) for op in rec.get('remesh', [])]   # (polish 2: lumpy toys rebuilt even)
    meta['relief'] = [relief(bm, op) for op in rec.get('relief', [])]          # (polish 2: flat reliefs rebuilt clean)
    meta['planar'] = [planar(bm, op) for op in rec.get('planar', [])]          # (polish: true flats flat)
    meta['smooth'] = [smooth_parts(bm, op) for op in rec.get('smooth', [])]    # (polish: lumps evened, creases kept)
    meta['parts_turned_out'] += normals_out(bm)
    meta['unions'] = run_unions(bm, rec, tags)
    meta['inlays'] = run_inlays(bm, rec, tags)
    meta['press'] = [press(bm, op) for op in rec.get('press', [])]     # (polish 2: tilted reliefs laid flat, after the
    # painted face's inlays are in: a boolean against the pressed relief can fail, and the inlay then squeezes with it)
    meta['rims'] = [rims(bm, op, tags) for op in rec.get('rims', [])]
    # straight region borders: parts cut along planes (nothing removed), so a colour edge can follow a line
    for sp in rec.get('splits', []):
        fs = _faces_of(bm, sp)   # (its part, and only faces in its box when it has one)
        geom = list(set(fs) | {e for f in fs for e in f.edges} | {v for f in fs for v in f.verts})
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=B(sp['co']), plane_no=B(sp['no']), dist=1e-6)
    meta['decals'] = [decals(bm, op, tags) for op in rec.get('decals', [])]   # (painted shapes cut into the faces)
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
            # (each cap facing out of its own half: a Tripo part is often open, so the fill can come out facing in,
            # and then it lies on the other half's cap facing the same way, a flicker pair the size of the cut)
            lo, hi = nd['box']
            for f in caps:
                f.normal_update()
                c = W(f.calc_center_median()); nrm = W(f.normal) - W(Vector((0.0, 0.0, 0.0)))
                for a in range(3):
                    for at, sgn in ((lo[a], -1.0), (hi[a], 1.0)):
                        if abs(c[a] - at) < 1e-5:
                            want = sgn if f[node_lay] == k else -sgn   # (the inside's cap faces out of the box)
                            if nrm[a] * want < 0: f.normal_flip()
            meta['nodes'].append({'node': nd['node'], 'cut_faces': len(inside), 'caps': len(caps)})
        else:
            for f in faces: f[node_lay] = k
            meta['nodes'].append({'node': nd['node'], 'parts': sorted(ids), 'tris': sum(len(f.verts) - 2 for f in faces)})
    rec['_node_names'] = names
    meta['contours'] = [contour(bm, op) for op in rec.get('contours', [])]
    meta['lines'] = [lines(bm, op, tags) for op in rec.get('lines', [])]
    meta['turned_parts'] = TURNED
    meta['duplicate_faces'] += dedupe_faces(bm)   # (a hole fill can lay a copy over a face Tripo left unwelded)
    ff = rec.get('fill_final', {})   # (polish: close every crack and hole up to `sides`, except the boxes left open)
    skip = ff.get('skip', [])
    keep_open = [e for e in bm.edges if e.is_boundary and any(_inbox(W((e.verts[0].co + e.verts[1].co) / 2), b) for b in skip)]
    for e in keep_open: e.tag = True
    bnd = [e for e in bm.edges if e.is_boundary and not e.tag]
    r = bmesh.ops.holes_fill(bm, edges=bnd, sides=ff.get('sides', 16))
    fills = list(r['faces'])
    if fills:
        t = bmesh.ops.triangulate(bm, faces=[f for f in fills if len(f.verts) > 3], quad_method='BEAUTY', ngon_method='BEAUTY')
        fills = [f for f in set(fills) | set(t['faces']) if f.is_valid]
    for e in bm.edges: e.tag = False
    meta['fill_final'] = len(fills)
    for f in fills:   # (and close what the copy's removal opened; the patch joins its neighbour's node)
        nb = [g for e in f.edges for g in e.link_faces if g is not f]
        f[node_lay] = nb[0][node_lay] if nb else 0
    meta['duplicate_faces'] += dedupe_faces(bm)
    meta['parts_turned_out'] += normals_out(bm)
    bm.faces.index_update()
    piece_of = assign_regions(bm, rec, tags, node_lay)
    meta['regions'] = [{'slot': r.get('slot'), 'node': r.get('node'), 'zone': r.get('zone'), 'faces': r.get('_hits')}
                       for r in rec.get('regions', [])]
    pieces = shade_and_split(bm, piece_of, rec.get('sharp', 40.0))
    meta['pieces'] = {k: sum(len(p.vertices) - 2 for p in me.polygons) for k, me in pieces.items()}
    meta['tris'] = sum(meta['pieces'].values())
    meta['nonmanifold_final'] = {'open': sum(1 for e in bm.edges if len(e.link_faces) == 1),
                                 'three_way': sum(1 for e in bm.edges if len(e.link_faces) > 2),
                                 'wire': sum(1 for e in bm.edges if not e.link_faces),
                                 'at': sorted({tuple(round(x, 2) for x in W((e.verts[0].co + e.verts[1].co) / 2))
                                               for e in bm.edges if not e.is_manifold})}
    # each edge left open: a hairline (another face passes through its middle: a T-junction, no hole to see) or a gap
    bm.faces.ensure_lookup_table()
    tree = BVHTree.FromBMesh(bm)
    rows = []
    for e in bm.edges:
        if e.is_manifold or not e.link_faces: continue
        mid = (e.verts[0].co + e.verts[1].co) / 2
        own = set(e.link_faces)
        near = [h for h in tree.find_nearest_range(mid, 0.0003) if h[2] is not None and bm.faces[h[2]] not in own]
        rows.append({'a': [round(x, 4) for x in W(e.verts[0].co)], 'b': [round(x, 4) for x in W(e.verts[1].co)],
                     'faces': len(e.link_faces), 'piece': piece_of[e.link_faces[0]], 'hairline': bool(near)})
    meta['nonmanifold_final']['edges'] = rows
    meta['nonmanifold_final']['gaps'] = sum(1 for r in rows if not r['hairline'] and r['faces'] == 1)
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


def brake(g, pieces, y, z_tip, z_rear, r=0.033, ri=0.024, ports=3, star=0.016, shroud=None, bands=(), inner=0.0145,
          bore=0.0085, sides=12, shroud_sides=14):
    """a shaped muzzle brake on the bore line (y), built the Blender-artist way (artist_kit booleans + bevels):
       a hollow body (r / ri, a flat facet facing each side) with `ports` slots through each side showing a dark inner
       barrel, gold rims at both ends, a chamfered nose with the bore, and a lit 4-point star let into each flank in a
       moat (its face 0.8 mm under the facet, 3.7 mm over the moat's floor: nothing to flicker). shroud = (r, z_front,
       z_back): a round tube over the bare barrel behind it, cut into pearl and gold bands at `bands` [(z0, z1), ...]
       (adjacent segments, one radius: nothing laid on anything). pieces: {"body", "gold", "dark", "lit"} piece names"""
    import artist_kit as AK
    tw = math.pi / sides   # (a flat facet facing each side: the stars' seat)
    def C(z): return (0.0, y, z)
    zr0, zr1 = z_rear - 0.010, z_rear + 0.002          # the rear rim (overlaps the barrel's end)
    zf0, zf1 = z_tip + 0.020, z_tip + 0.012            # front rim .. nose
    rim_r = AK.tube(r, inner + 0.0015, C(zr1), C(zr0), sides=sides, turn=tw)
    body = AK.tube(r, ri, C(zr0), C(zf0), sides=sides, turn=tw)
    rim_f = AK.tube(r, bore + 0.002, C(zf0), C(zf1), sides=sides, turn=tw)
    nose = AK.cut(AK.cyl(r * 0.86, C(z_tip), C(zf1), sides=sides, r2=r, turn=tw), AK.cyl(bore, C(z_tip - 0.01), C(zf1 + 0.003), sides=10))
    core = AK.cyl(inner, C(zf0 - 0.004), C(zr0 + 0.002), sides=8)
    L = zr0 - zf0                                   # (negative: the body runs toward -z)
    cut = []
    star_z = zr0 - 0.22 * abs(L) if star else None
    fx = r * math.cos(tw)
    pz0 = (star_z - star - 0.004) if star else zr0 - 0.006
    span = pz0 - (zf0 + 0.005)
    plen = span / ports - 0.004
    for k in range(ports):
        z1 = pz0 - k * (plen + 0.004); z0 = z1 - plen
        for sx in (-1, 1):
            cut.append(AK.prism([(z0, y - 0.0045), (z1, y - 0.0045), (z1, y + 0.0045), (z0, y + 0.0045)], 0.022, x=sx * fx))
    stars = []
    if star:
        def st(R, rr):
            return [(R * math.sin(a) if i % 2 == 0 else rr * math.sin(a), R * math.cos(a) if i % 2 == 0 else rr * math.cos(a))
                    for i, a in enumerate(math.pi / 4 * k for k in range(8))]
        for sx in (-1, 1):
            U, V = (0.0, 0.0, -sx), (0.0, 1.0, 0.0)
            O = (sx * fx, y, star_z)
            cut.append(AK.oprism(st(star + 0.0022, star * 0.36 + 0.0016), O, U, V, -0.0045, 0.01))
            stars.append(AK.oprism(st(star, star * 0.33), O, U, V, -0.0046, -0.0008))
    g.put(pieces['body'], AK.cut(body, *cut), AK.soft(nose, 0.0015, seg=1))
    g.put(pieces['gold'], AK.soft(rim_r, 0.0012, seg=1), AK.soft(rim_f, 0.0012, seg=1))
    g.put(pieces['dark'], core)
    if stars: g.put(pieces['lit'], *stars)
    if shroud:
        sr, s0, s1 = shroud
        cuts = sorted([s0, s1] + [z for b in bands for z in b])
        segs = list(zip(cuts[:-1], cuts[1:]))
        for z0, z1 in segs:
            is_band = any(abs(z0 - b[0]) < 1e-9 and abs(z1 - b[1]) < 1e-9 for b in bands)
            g.put(pieces['gold'] if is_band else pieces['shroud'], AK.cyl(sr, C(z0), C(z1), sides=shroud_sides))


def _loft(rings, caps=(True, True)):
    """an artist_kit solid through rings of weapon-frame points (every ring the same count, in order round it)"""
    import artist_kit as AK
    bm = bmesh.new()
    V = [[bm.verts.new(B(Vector(p))) for p in ring] for ring in rings]
    m = len(rings[0])
    for i in range(len(rings) - 1):
        for k in range(m):
            j = (k + 1) % m
            bm.faces.new([V[i][k], V[i][j], V[i + 1][j], V[i + 1][k]])
    if caps[0]: bm.faces.new(V[0][::-1])
    if caps[1]: bm.faces.new(V[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return AK._obj(bm)


CREST = [(0.00, 0.00), (0.25, 0.18), (0.45, 0.50), (0.58, 0.80), (0.70, 0.97), (0.82, 0.98), (0.92, 0.88),
         (0.98, 0.70), (0.96, 0.56), (0.89, 0.50), (0.84, 0.56), (0.83, 0.64), (0.79, 0.60), (0.78, 0.45),
         (0.85, 0.25), (0.95, 0.08)]   # (one curling crest: u 0 back .. 1 front, h 0 trough .. 1 top; the lip overhangs)
FOAM = [(0.40, 0.30), (0.55, 0.58), (0.68, 0.78), (0.78, 0.86), (0.85, 0.84), (0.76, 0.75), (0.64, 0.61),
        (0.52, 0.40), (0.45, 0.26)]    # (the white curl inside a crest, under its back slope)


def kblade(g, pieces, outline, z0=-0.139, tk=(0.0056, 0.0046), ty=0.834, n=96, m=10, edge=0.24, spine=0.12,
           tip_w=0.0024, waves=4, base=0.40, height=0.36, dots=0.0032, tip_piece=None, **_old):
    """a katana blade rebuilt in kit (a Tripo blade is a soft lump): ONE closed solid lofted through sections of the
       outline [(z, y_edge, y_back)] from the root (z0) to the tip, its faces coloured: a bevel to a SHARP edge
       (pieces['edge']), the flat face (pieces['blade']), a chamfered spine (pieces['spine']), past `ty` (the yokote)
       the point in pieces['edge'] (or tip_piece). On the flat face, CUT INTO it (no picture, nothing laid on top):
       a band of `waves` curling crests (pieces['wave'], its top `height` of the face tall from `base`), a white foam
       curl inside each crest (pieces['foam']) and round dots over the troughs (pieces['wave'], radius `dots` m).
       The game stretches every kat_blade piece about z0 alike, so all of them stay in place"""
    def at(z):
        for i in range(len(outline) - 1):
            (za, ea, ba), (zb, eb, bb) = outline[i], outline[i + 1]
            if za >= z >= zb:
                u = (za - z) / (za - zb) if za != zb else 0.0
                return ea + (eb - ea) * u, ba + (bb - ba) * u
        return outline[-1][1], outline[-1][2]
    zt = outline[-1][0]
    def sec(t):
        z = z0 + (zt - z0) * t
        ye, yb = at(z)
        if yb - ye < tip_w:
            c = (ye + yb) / 2; ye, yb = c - tip_w / 2, c + tip_w / 2
        k = tk[0] + (tk[1] - tk[0]) * min(max(t, 0.0) / ty, 1.0)
        if t > ty: k *= 1.0 - 0.7 * ((t - ty) / (1 - ty)) ** 1.3
        return z, ye, yb, k
    def zy(t, f):   # (a point on the face: t along, f across) -> weapon (z, y)
        z, ye, yb, _ = sec(t)
        return (z, ye + (yb - ye) * f)
    def thick(f):
        if f <= edge: return 0.1 + 0.9 * f / edge
        if f >= 1 - spine: return 1.0 - 0.45 * (f - (1 - spine)) / spine
        return 1.0
    F = [0.0, edge, 1 - spine, 1.0]
    names = ['edge', 'blade', 'spine']
    CODE = {'edge': 0, 'blade': 1, 'spine': 2, 'tip': 3, 'wave': 4, 'foam': 5}
    ts = [ty * i / n for i in range(n + 1)] + [ty + (1 - ty) * i / m for i in range(1, m + 1)]
    bm = bmesh.new()
    kc = bm.faces.layers.int.new('kc'); bm.faces.layers.int.new('_sel')
    rings = []
    for t in ts:
        z, ye, yb, k = sec(t)
        right = [(thick(f) * k, ye + (yb - ye) * f, z) for f in F]
        left = [(-x, y, zz) for x, y, zz in reversed(right)]
        rings.append([bm.verts.new(B(Vector(p))) for p in right + left])
    nf = len(F); cnt = 2 * nf
    def code(k, tmid):   # ring edge k (right side 0..nf-2 up, top nf-1, left down, bottom 2nf-1)
        if k == nf - 1: return CODE['spine']
        if k == cnt - 1: return CODE['edge']
        nm = names[k if k < nf - 1 else cnt - 2 - k]
        if tmid > ty and nm != 'spine': return CODE['tip']
        return CODE[nm]
    for i in range(len(rings) - 1):
        tmid = (ts[i] + ts[i + 1]) / 2
        for k in range(cnt):
            j = (k + 1) % cnt
            f = bm.faces.new([rings[i][k], rings[i][j], rings[i + 1][j], rings[i + 1][k]])
            f[kc] = code(k, tmid)
    f = bm.faces.new(rings[0][::-1]); f[kc] = CODE['blade']          # (the root: inside the habaki)
    f = bm.faces.new(rings[-1]); f[kc] = CODE['tip']
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    # the painted waves, cut into the flat face on both sides
    t0, t1 = -0.01, ty - 0.012
    P = (t1 - t0) / waves
    top = []
    for w in range(waves):
        for u, h in CREST: top.append(zy(t0 + (w + u) * P, base + h * height))
    top.append(zy(t1, base))
    bottom = [zy(t1 - (t1 - t0) * i / 24, edge - 0.04) for i in range(25)]   # (along the edge line's own curve)
    band = top + bottom
    foams = [[zy(t0 + (w + u) * P, base + h * height) for u, h in FOAM] for w in range(waves)]
    dotp = []
    for w in range(1, waves):
        zc, yc = zy(t0 + (w - 0.12) * P, base + height + 0.05)
        dotp.append([(zc + dots * math.cos(2 * math.pi * i / 12), yc + dots * math.sin(2 * math.pi * i / 12)) for i in range(12)])
    polys = [band] + foams + dotp
    hit = imprint(bm, lambda f: f[kc] == CODE['blade'], polys, sides=(-1, 1), nmin=0.5)
    for f, i in hit.items():
        f[kc] = CODE['foam'] if 1 <= i <= len(foams) else CODE['wave']
    import artist_kit as AK
    piece_of = {CODE['edge']: pieces['edge'], CODE['blade']: pieces['blade'], CODE['spine']: pieces['spine'],
                CODE['tip']: tip_piece or pieces['edge'], CODE['wave']: pieces['wave'], CODE['foam']: pieces.get('foam', pieces['blade'])}
    bm.faces.ensure_lookup_table()
    for c in sorted({f[kc] for f in bm.faces}):
        sub = bm.copy(); sub.faces.ensure_lookup_table()
        lay = sub.faces.layers.int['kc']
        bmesh.ops.delete(sub, geom=[f for f in sub.faces if f[lay] != c], context='FACES')
        g.put(piece_of[c], AK._obj(sub))
    bm.free()


def candy(g, pieces, y, z0, z1, r, n=7, tilt=24.0, sides=16, x=0.0):
    """a striped round grip (a candy-cane wrap) along z on (x, y): n slabs between parallel planes tilted `tilt`
       degrees (flat ends), alternating pieces[0], pieces[1]; each slab a closed solid, neighbours share hidden caps"""
    tn = math.tan(math.radians(tilt))
    L = (z1 - z0) / n
    def ring(zc, slant):
        return [(x + r * math.cos(2 * math.pi * i / sides), y + r * math.sin(2 * math.pi * i / sides),
                 zc + (r * math.sin(2 * math.pi * i / sides) * tn if slant else 0.0)) for i in range(sides)]
    for k in range(n):
        a = ring(z0 + L * k, k > 0)
        b = ring(z0 + L * (k + 1), k < n - 1)
        g.put(pieces[k % 2], _loft([a, b]))


def hoop(g, pieces, c, R, r, n=12, sides=12, steps=3, bands=(), band_w=14.0, band_r=1.14, gap=None):
    """a striped ring standing in the y-z plane (a pommel loop) round c: tube radius r on a circle of radius R, cut
       into n segments alternating pieces[0], pieces[1]; `bands` = angles (degrees, 0 = toward -z, 90 = up) of gold
       collars (pieces[2], radius r * band_r, band_w degrees wide); gap = (from, to) degrees left open (a hook)"""
    c = Vector(c)
    def ring(phi, rad):
        d = Vector((0.0, math.sin(phi), -math.cos(phi)))   # (the loop's radial direction in the y-z plane)
        o = c + d * R
        return [tuple(o + (Vector((1.0, 0.0, 0.0)) * math.cos(2 * math.pi * i / sides) + d * math.sin(2 * math.pi * i / sides)) * rad)
                for i in range(sides)]
    marks = sorted([(b - band_w / 2, b + band_w / 2) for b in bands])
    seg = 360.0 / n
    def in_band(a):
        return any(m0 <= a + w <= m1 for m0, m1 in marks for w in (-360.0, 0.0, 360.0))
    edges = sorted({round(seg * i, 6) for i in range(n + 1)} | {round(e % 360.0, 6) for mk in marks for e in mk})
    cuts = []   # (start deg, end deg, piece, radius)
    for a0, a1 in zip(edges[:-1], edges[1:]):
        mid = (a0 + a1) / 2
        if gap and gap[0] <= mid <= gap[1]: continue
        inb = in_band(mid)
        cuts.append((a0, a1, pieces[2] if inb else pieces[int(mid // seg) % 2], r * band_r if inb else r))
    for a0, a1, piece, rad in cuts:
        st = max(1, int(round((a1 - a0) / 30.0 * steps)))
        phis = [math.radians(a0 + (a1 - a0) * j / st) for j in range(st + 1)]
        rings = [ring(ph, rad) for ph in phis]
        # (true tube normals, drawn straight into the piece: through put() the weighted-normal pass shades each
        # segment from its own faces only, so every band and segment end showed as a facet)
        norms = [[tuple((Vector(p) - (c + Vector((0.0, math.sin(ph), -math.cos(ph))) * R)).normalized()) for p in rg]
                 for ph, rg in zip(phis, rings)]
        _smooth_solid(g, piece, rings, norms)


def _smooth_solid(g, piece, rings, norms):
    """a closed solid through rings of weapon-frame points (as _loft) with its side normals given (weapon frame),
       flat caps; drawn straight into g.pieces so the normals are kept (the clean pieces' path), not re-shaded"""
    node, slot = piece.split('__')
    g.slots[slot]   # (an unknown slot fails here)
    bm = bmesh.new()
    V = [[bm.verts.new(B(Vector(p))) for p in rg] for rg in rings]
    nrm = {}
    for rg, nr in zip(V, norms):
        for v, n in zip(rg, nr): nrm[v] = Vector((n[0], -n[2], n[1]))   # (weapon -> Blender frame)
    m = len(rings[0])
    for i in range(len(rings) - 1):
        for k in range(m):
            j = (k + 1) % m
            bm.faces.new([V[i][k], V[i][j], V[i + 1][j], V[i + 1][k]])
    caps = {bm.faces.new(V[0][::-1]), bm.faces.new(V[-1])}
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces: f.smooth = True
    me = bpy.data.meshes.new('ss')
    bm.verts.index_update(); bm.faces.index_update()
    capi = {f.index for f in caps}
    vn = {v.index: nrm[v] for v in bm.verts}
    bm.to_mesh(me); bm.free()
    loops = []
    for p in me.polygons:
        for li in p.loop_indices:
            loops.append(tuple(p.normal) if p.index in capi else tuple(vn[me.loops[li].vertex_index]))
    me.normals_split_custom_set(loops)
    g.pieces.setdefault((node, slot), bmesh.new()).from_mesh(me)
    bpy.data.meshes.remove(me)


def clip(g, piece, c, R, r, phi, x_in, w=0.007, t=0.0015, rc=0.002, k=2, shape='wrap', seg=8):
    """a strap clip holding a hoop (see hoop: tube radius r on a circle of radius R round c, in the y-z plane) to the
       body beside it: a straight band `w` m wide and `t` thick wrapped round the tube at angle `phi` (degrees, 0 =
       toward -z, 90 = up), from inside the body (x = x_in) out over the tube. shape 'wrap': a U strap hugging the
       tube's outer half (`seg` steps round it) and running straight back into the body; 'box': a rounded rectangle"""
    c = Vector(c)
    side = 1.0 if x_in > c.x else -1.0          # (the body is on this side of the ring)
    prof, pn = [], []   # (the section in (x, rho), in order round it; and its outward normals)
    if shape == 'wrap':
        rr = r + t
        for j in range(seg + 1):
            b = math.radians(-90.0 + 180.0 * j / seg)
            prof.append((c.x - side * rr * math.cos(b), R + rr * math.sin(b))); pn.append((-side * math.cos(b), math.sin(b)))
        prof += [(x_in, R + rr), (x_in, R - rr)]; pn += [(0.0, 1.0), (0.0, -1.0)]
    else:
        x0, x1 = x_in, c.x - side * (r + t)          # (inner end, sunk in the body .. outer face)
        r0, r1 = R - r - t, R + r + t
        xa, xb = min(x0, x1), max(x0, x1)
        cr = min(rc, (xb - xa) / 2.01, (r1 - r0) / 2.01)
        for (cx_, cr_, a0) in ((xb - cr, r1 - cr, 0.0), (xa + cr, r1 - cr, 90.0), (xa + cr, r0 + cr, 180.0), (xb - cr, r0 + cr, 270.0)):
            for j in range(k + 1):
                a = math.radians(a0 + 90.0 * j / k)
                prof.append((cx_ + cr * math.cos(a), cr_ + cr * math.sin(a))); pn.append((math.cos(a), math.sin(a)))
    ph = math.radians(phi)
    d = Vector((0.0, math.sin(ph), -math.cos(ph))); tg = Vector((0.0, math.cos(ph), math.sin(ph)))
    rings = [[tuple(Vector((px, c.y, c.z)) + d * pr + tg * s) for px, pr in prof] for s in (-w / 2.0, w / 2.0)]
    norms = [[tuple(Vector((nx, 0.0, 0.0)) + d * nr) for nx, nr in pn]] * 2
    _smooth_solid(g, piece, rings, norms)


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
        elif fn == 'brake': brake(g, it['pieces'], **kw)
        elif fn == 'kblade': kblade(g, it['pieces'], **kw)
        elif fn == 'candy': candy(g, it['pieces'], **kw)
        elif fn == 'hoop': hoop(g, it['pieces'], **kw)
        elif fn == 'clip': clip(g, piece, **kw)
        elif fn in ('box', 'prism', 'cyl', 'cylz', 'ring', 'ball', 'xprism', 'yprism', 'window'):
            args = [tuple(a) if isinstance(a, list) and fn in ('box', 'cyl', 'ring', 'ball') else a for a in args]
            if fn in ('prism', 'xprism', 'yprism'): args = [[tuple(p) for p in args[0]]] + list(args[1:])
            getattr(g, fn)(piece, *args, **kw)
        elif fn in ('rifle_rear', 'rifle_front', 'notch', 'blade', 'bead', 'scope_slim'): getattr(SG, fn)(g, piece, *args, **kw)
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
        for k, v in palette_of(rec).items(): g.slot(k, v['color'], v['kind'], v['alpha'])
        SY, BY = g.spots.get('sight', g.spots['muzzle'])[1], g.spots['muzzle'][1]   # (a melee base has no sight)
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


COMPOSE = r'''
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


def sheet(K, base_id, out_dir, sheet_path, raw, fit, concept=None, compare=None, rec=None, Wd=900, Ht=560):
    """the verdict panels (PNG) in out_dir/sheet, composed with labels into sheet_path by plain Python + PIL.
       compare = a folder holding an earlier version's _p_hand.png and _p_aim.png: shown beside this version's"""
    import gun_set
    sh = os.path.join(out_dir, K + '_sh.glb')
    meta = json.load(open(os.path.join(out_dir, K + '_clean.json')))
    pdir = os.path.join(out_dir, 'sheet', K); os.makedirs(pdir, exist_ok=True)   # (the panels, per gun)
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
    panels.append((_render(os.path.join(pdir, '_p_raw.png')), 'Tripo raw (grey), fitted to the %s' % base_id.upper()))
    # cleaned + coloured + shells: three-quarter, left side
    sc = _scene(Wd, Ht); _import(sh)
    _sun(sc, (math.radians(50), 0, math.radians(-40)))
    _cam(sc, mid + Vector((-0.75 * L, 0.80 * L, 0.42 * L)) * 0.95, mid + Vector((0, 0.04 * L, 0)), fov=40)
    panels.append((_render(os.path.join(pdir, '_p_34.png')), 'cleaned + coloured + shade shells, 3/4'))
    sc = _scene(Wd, Ht); _import(sh)
    _sun(sc, (math.radians(60), 0, math.radians(-90)))
    _cam(sc, mid + side, mid, ortho=L * 1.12)
    panels.append((_render(os.path.join(pdir, '_p_side.png')), 'left side'))
    sc = _scene(Wd, Ht); _import(sh)
    _sun(sc, (math.radians(20), 0, math.radians(-30)))
    _cam(sc, mid + Vector((0, 0, 3.0)), mid, ortho=L * 1.12, up=Vector((1, 0, 0)))
    panels.append((_render(os.path.join(pdir, '_p_top.png')), 'top (right side up)'))
    cu = ((rec or meta.get('recipe', {})).get('sheet') or {}).get('closeup')   # {"at": [x, y, z], "size": m, "label": ".."}
    close = None
    if cu:   # a close left-side view of one detail (a slight turn toward the camera so its depth shows)
        sc = _scene(Wd, Ht); _import(sh)
        _sun(sc, (math.radians(55), 0, math.radians(-70)))
        at = B(cu['at'])
        _cam(sc, at + Vector((-3.0, 0.6, 0.5)), at, ortho=cu.get('size', 0.18))
        close = (_render(os.path.join(pdir, '_p_close.png')), cu.get('label', 'close-up'))
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
    sp = meta['spots'].get('sight')
    aim_hidden = None
    if sp is None:   # (a melee weapon has no sight: that panel shows it from the tip instead, edge on)
        sc = _scene(Wd, Ht); _import(sh)
        _sun(sc, (math.radians(35), 0, math.radians(20)))
        _cam(sc, mid + B((0, 0, -3.0)), mid, ortho=max(hi[1] - lo[1], hi[0] - lo[0]) * 1.4)
        panels.append((_render(os.path.join(pdir, '_p_aim.png')), 'from the tip, edge on'))
    else:
        # aim view (approximate: the eye 0.11 m behind the sight spot, zoom 1.5)
        sc = _scene(Wd, Ht); _import(sh)
        _sun(sc, (math.radians(35), 0, math.radians(20)))
        try:   # (the eye's distance behind the sight: 0.17 + the gun's holds.json ads aimZ; the AR's is -0.06)
            hj = json.load(open(os.path.join(HERE, 'holds.json')))
            back = 0.17 + float(hj.get(base_id, {}).get('ads', {}).get('aimZ', -0.06))
        except Exception: back = 0.11
        eye = B((0, sp[1], sp[2] + back))
        _cam(sc, eye, eye + B((0, 0, -1)), fov=70 / 1.5)
        panels.append((_render(os.path.join(pdir, '_p_aim.png')), 'aim view (approx.: eye %.2f m behind the sight)' % back))
        sc = _scene(Wd, Ht)   # (the live base gun from the same eye: what the aim picture should look like)
        gun_set.BUILD[base_id]().to_scene()
        _sun(sc, (math.radians(35), 0, math.radians(20)))
        _cam(sc, eye, eye + B((0, 0, -1)), fov=70 / 1.5)
        _render(os.path.join(pdir, '_p_base_aim.png'))
        hide = ((rec or meta.get('recipe', {})).get('sheet') or {}).get('aim_hide')   # piece-name prefixes (holds.json ads hide)
        if hide:
            sc = _scene(Wd, Ht); objs = _import(sh)
            for o in objs:
                if o.type == 'MESH' and any(o.name.startswith(h) for h in hide): bpy.data.objects.remove(o, do_unlink=True)
            _sun(sc, (math.radians(35), 0, math.radians(20)))
            _cam(sc, eye, eye + B((0, 0, -1)), fov=70 / 1.5)
            aim_hidden = (_render(os.path.join(pdir, '_p_aim_hidden.png')), 'aim view, %s hidden (ADS hide list)' % ', '.join(hide))
    P = dict(zip(('raw', '34', 'side', 'top', 'hand', 'base', 'aim'), panels))
    relabel = lambda pl, l: (pl[0], l)
    if compare and close and os.path.exists(os.path.join(compare, '_p_close.png')):
        # 3/4, side, top | the detail before and now, now in hand | aimed before and now, the base gun in hand
        panels = [P['34'], P['side'], P['top'],
                  (os.path.join(compare, '_p_close.png'), 'BEFORE: ' + close[1]), relabel(close, 'NOW: ' + close[1]),
                  relabel(P['hand'], 'NOW: in hand'),
                  (os.path.join(compare, '_p_aim.png'), 'BEFORE: aim view'), relabel(P['aim'], 'NOW: aim view'), P['base']]
    elif compare:   # raw, 3/4, side, top | before in hand, now in hand, before aimed | now aimed, base gun in hand
        panels = [P['raw'], P['34'], P['side'], P['top'],
                  (os.path.join(compare, '_p_hand.png'), 'BEFORE: in hand'), relabel(P['hand'], 'NOW: in hand'),
                  (os.path.join(compare, '_p_aim.png'), 'BEFORE: aim view'), relabel(P['aim'], 'NOW: aim view'), P['base']]
    else:
        if aim_hidden: panels.append(aim_hidden)
        if close: panels.append(close)
    if concept: panels.insert(0, (concept, "owner's concept"))
    spec = {'panels': panels, 'out': sheet_path, 'w': Wd, 'h': Ht, 'title': meta.get('name', K)}
    js = os.path.join(pdir, '_sheet.json')
    with open(js, 'w') as fh: json.dump(spec, fh)
    r = subprocess.run([PY, '-c', COMPOSE, js], capture_output=True, text=True)   # (PIL is in the user's site-packages)
    print(r.stdout.strip(), r.stderr.strip()[-400:])
    return sheet_path


VIEWS = {'left': (Vector((-1, 0, 0)), Vector((0, 0, 1))), 'right': (Vector((1, 0, 0)), Vector((0, 0, 1))),
         'top': (Vector((0, 0, 1)), Vector((1, 0, 0))), 'below': (Vector((0, 0, -1)), Vector((1, 0, 0))),
         'front': (Vector((0, 1, 0)), Vector((0, 0, 1))), 'back': (Vector((0, -1, 0)), Vector((0, 0, 1))),
         'q34': (Vector((-0.75, 0.8, 0.42)).normalized(), Vector((0, 0, 1))),
         'lq': (Vector((-1, 0.35, 0.45)).normalized(), Vector((0, 0, 1))),
         'lb': (Vector((-1, -0.35, -0.3)).normalized(), Vector((0, 0, 1)))}   # (Blender frame: -x left, +y muzzle, +z up)


def closeups(glb, spots, pdir, Wd=900, Ht=560, preturned=False):
    """close views of details: spots [{"name", "at": [x, y, z] (weapon frame), "size": m, "view": VIEWS key, "label"}]
       -> pdir/_c_<name>.png; returns [(png, label)]. preturned: the glb is an exported (PRE_TURN) one, e.g. the
       live copy, turned back half a turn so the same cameras see the same spots (the BEFORE pictures)"""
    out = []
    os.makedirs(pdir, exist_ok=True)
    for sp in spots:
        sc = _scene(Wd, Ht); objs = _import(glb, Matrix.Rotation(math.pi, 4, 'Z') if preturned else None)
        d, up = VIEWS[sp.get('view', 'left')]
        if sp.get('rake'):   # (polish sheets: plain grey clay under a low raking light, so wobble shows)
            clay = bpy.data.materials.new('clay'); clay.use_nodes = True
            bsdf = clay.node_tree.nodes.get('Principled BSDF')
            bsdf.inputs['Base Color'].default_value = (0.62, 0.62, 0.62, 1); bsdf.inputs['Roughness'].default_value = 0.45
            for o in objs:
                if o.type == 'MESH':
                    for i in range(len(o.material_slots)): o.material_slots[i].material = clay
                    if not o.material_slots: o.data.materials.append(clay)
            sc.world.node_tree.nodes['Background'].inputs[1].default_value = 0.45
            side = Vector((d.y, -d.x, 0.0)) if abs(d.z) < 0.9 else Vector((1.0, 0.0, 0.0))
            ldir = (side * 0.7 + up * 0.35 + d * 0.35).normalized()   # (light skimming across the surface, toward the camera)
            ls = bpy.data.lights.new('rake', 'SUN'); ls.energy = 4.5; ls.angle = 0.04
            lo = bpy.data.objects.new('rake', ls); sc.collection.objects.link(lo)
            lo.rotation_euler = (-ldir).to_track_quat('-Z', 'Y').to_euler()
        else:
            _sun(sc, (math.radians(50), 0, math.radians(-60)), strength=0.5 if sp.get('dark') else 1.8)
        if sp.get('dark'):   # (a dusk light: the Neon glow reads)
            sc.world.node_tree.nodes['Background'].inputs[1].default_value = 0.06
        at = B(sp['at'])
        _cam(sc, at + d * 3.0, at, ortho=sp.get('size', 0.15), up=up)
        out.append((_render(os.path.join(pdir, '_c_%s.png' % sp['name'])), sp.get('label', sp['name'])))
    return out


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
                            ('top', Vector((0, 0, 1)), Vector((1, 0, 0)), 1.05), ('q34', Vector((-0.75, 0.8, 0.42)).normalized(), Vector((0, 0, 1)), 0.9)):
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
def compose(out, title, panels, Wd=900, Ht=560):
    """panels [(png, label)] into a labelled 3-column sheet (plain Python + PIL)"""
    spec = {'panels': panels, 'out': out, 'w': Wd, 'h': Ht, 'title': title}
    js = os.path.splitext(out)[0] + '_sheet.json'
    with open(js, 'w') as fh: json.dump(spec, fh)
    r = subprocess.run([PY, '-c', COMPOSE, js], capture_output=True, text=True)
    print(r.stdout.strip(), r.stderr.strip()[-400:])
    os.remove(js)


def main(argv):
    if argv and argv[0] == 'compose':   # compose <out.jpg> <title> <png> <label> [<png> <label> ...]
        compose(argv[1], argv[2], [(argv[i], argv[i + 1]) for i in range(3, len(argv) - 1, 2)])
        return
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
    if opt('--stage') == 'closeups':   # (the recipe's sheet.closeups from out_dir's shelled glb, into --into <dir>)
        spots = (rec.get('sheet') or {}).get(opt('--set') or 'closeups', [])
        glb = opt('--glb') or os.path.join(out_dir, K + '_sh.glb')   # (--glb <exported glb> --preturned: the live one)
        into = opt('--into') or os.path.join(out_dir, 'sheet', K)
        if '--raw' in rest:   # (the same views of the RAW model, fitted into the kit frame: the BEFORE pictures)
            os.makedirs(into, exist_ok=True)
            import gun_set
            s_, t_, R_, _ = solve_fit(rec, dict(gun_set.BUILD[base_id]().spots))
            bm = load_raw(raw); fit_bmesh(bm, s_, t_, R_)
            o = _bm_obj(bm, 'raw'); bm.free(); _grey([o])
            glb = os.path.join(into, '_rawfit.glb')
            bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', use_selection=False, export_yup=True)
        for png, label in closeups(glb, spots, into, preturned='--preturned' in rest):
            print('CLOSEUP', png, label)
        return
    if opt('--stage') == 'sheet':   # (only the sheet again, from the files a full run left in out_dir)
        meta = json.load(open(os.path.join(out_dir, K + '_clean.json')))
        s, t, R, _ = solve_fit(rec, meta['spots'])
        sheet(K, base_id, out_dir, opt('--sheet'), raw, (s, t, R), concept=opt('--concept'), compare=opt('--compare'), rec=rec)
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
    SKINS[key] = builder(os.path.join(out_dir, K + '_clean.json'))   # (this run's own files, wherever out_dir is)
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
        sheet(K, base_id, out_dir, sp, raw, (s, t, R), concept=opt('--concept'), compare=opt('--compare'), rec=rec)
    print('TRIPO GUN %s done in %.0fs' % (key, time.time() - t0))
    for k in ('fit', 'tris', 'tris_gun', 'tris_shells', 'tris_total', 'zfix', 'flicker', 'gun_check', 'export', 'export_lo_hi', 'bounds', 'base_bounds'):
        if k in meta: print('  %s: %s' % (k, json.dumps(meta[k], default=str)))


if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
