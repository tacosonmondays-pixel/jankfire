# TRIPO BAKE: a whole Tripo gun's surface (relief, soft shading, painted motifs) baked onto its game mesh as Roblox
# SurfaceAppearance maps, for ANY gun tripo_gun.py made (17 Nov 2026; first the angel rifle, the owner: "it lost a lot
# of detail especially with the texture"; then the Ducky set, "looks so simple now"). Headless Blender 5.3. Reads
# tools/roblox/tripo_gun.py (fit, clean, render helpers) and artist_kit.py (atlas UVs); never edits them.
#
#   blender -b --factory-startup -P tools/roblox/tripo_bake.py -- bake  <base@skin> [--spec <json>] [--game <glb>] [--out <dir>]
#   blender -b --factory-startup -P tools/roblox/tripo_bake.py -- sheet <base@skin> [--sheet <jpg>] [--title <text>]
#   blender -b --factory-startup -P tools/roblox/tripo_bake.py -- luau  <base@skin>      (the install Luau again)
#   blender -b --factory-startup -P tools/roblox/tripo_bake.py -- diag                   (the angel rifle's diagnosis)
# The gun is found by its vault folder (the one holding w_<key>_clean.json); its optional bake_spec.json there holds
# what is its own (the game mesh to bake on, slot finishes, painted motifs, detail relief, sheet close-ups): see BAKE.
#
# BAKE   keeps the game mesh's pieces EXACTLY (names, vertices, normals; shade shells dropped: the AO is in the
#        ColorMap now), gives the pictured pieces 1024 atlases (as many as the wanted texel density needs), then per
#        texel:
#          - NormalMap (tangent space, OpenGL +Y): the raw Tripo surface (tripo_gun's clean re-run WITHOUT decimation,
#            shaded smooth like Tripo's own file) found by a short ray along the game mesh's normal, in the game
#            mesh's MikkTSpace frame; kit parts (no raw surface: sights, rings, blades) get clean rounded-edge
#            normals; Tripo wobble (turns under a few degrees) is faded out; a 3x3 median takes out stray hits;
#            detail relief from the spec (rivet domes, piping, grooves) bends the normals on top
#          - ColorMap: the slot colours (cut-in decal pieces start from the surface they were cut into), the spec's
#            painted motifs as smooth signed-distance shapes laid in the gun's own frame (the recipe's decal outlines
#            redrawn smooth, waves, foam, clouds, drops, ducks, crowns, piping), then Cycles AO over the gun, cavity
#            and edge lines from the surface curvature, a soft top-down light, hue-kept toy shadows, gold lit like a metal
#          - MetalnessMap / RoughnessMap per slot (glossy toy plastic, gold a little metallic)
#        small UV islands are evened out (a GLYPH GUARD: no row of little islands may read as writing or a barcode)
#        and every map's empty space is filled from the islands (pull-push). Writes into the out folder:
#        K_up.glb (the upload: the game's piece names "<node>__<slot>__<look>", PRE_TURNed, atlas UVs + tangents, no
#        pictures inside), K_preview.glb (maps inside, to look at), K_<atlas>_{color,normal,metal,rough}.png,
#        K_install.luau (Edit-mode SurfaceAppearance set-up, ids to fill in), export_report.json (the kit book's row,
#        uv = false), bake.json (what went where, densities, triangles)
# SHEET  before / after at the same cameras: the owner's concept (or the raw Tripo in clay) | the game now (flat colours
#        + shade shells) | the new maps; the spec's close-ups; in hand; the aim view (the recipe's ADS hide list off)
# DIAG   (angel rifle) raw / v2 / v5 / v6 from the same cameras, clay and colour, with surface measures (diag.json)
#
# Frame: tripo_gun's (metres; weapon x right, y up, z back, muzzle at -z; B() = the kit's Blender frame). An exported
# upload file is PRE_TURNed (x and z negated, rbxglb.py): it is read and written in that frame, untouched.
# THE OWNER'S FILES STAY LOCAL: every mesh, map and render this writes goes to the vault or a scratch folder; the
# per-gun bake_spec.json lives in the vault next to the recipe.
import sys, os, math, json, time, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import tripo_gun as TG

K = 'w_ar@ar_seraph_tripo'
VAULT = os.environ.get('JF_ANGEL', r'C:\Users\soup2\Documents\JANKFIRE Vault\Assets\tripo-17nov\angel-rifle')
KIT = os.environ.get('JF_KITDIR', r'C:\Users\soup2\AppData\Local\Temp\claude\76cad3e90d004071'
                     r'\2f7beada-dc88-4870-9c10-a63ae3e562cc\scratchpad\rooftop-models\weapons-kit')
NOTES = os.environ.get('JF_NOTES', r'C:\Users\soup2\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc'
                       r'\side-session-notes\local_f6d4e505-8093-4c63-b4ec-8c76fd4df317')
SRC = {
    'raw': os.path.join(VAULT, 'angelic_rifle_raw.glb'),
    'rec': os.path.join(VAULT, 'v6', 'recipe.json'),
    'clean': os.path.join(VAULT, 'v6', K + '_clean.json'),
    'v2': os.path.join(VAULT, 'v2', K + '_sh.glb'),
    'v5': os.path.join(VAULT, 'v5', K + '_sh.glb'),
    'v6': os.path.join(KIT, 'tripo_angel', K + '_up.glb'),          # (the live upload, asset 130346853233717)
}
OUT = os.path.join(KIT, 'tripo_angel_bake')
TURN = Matrix.Rotation(math.pi, 4, 'Z')   # PRE_TURN: an upload file <-> the kit's Blender frame
PY = TG.PY


# ================================================================================================ loading
def fit_of():
    rec = json.load(open(SRC['rec']))
    meta = json.load(open(SRC['clean']))
    s, t, R, res = TG.solve_fit(rec, meta['spots'])
    return rec, meta, (s, t, R), res


def raw_bmesh(drop=False):
    """the raw Tripo mesh fitted into the kit's Blender frame (tripo_gun's load + fit + weld); drop: also the recipe's
       dropped parts out, holes filled, normals out (the bake's source). Empties the scene."""
    rec, meta, (s, t, R), _ = fit_of()
    bm = TG.load_raw(SRC['raw'])
    TG.fit_bmesh(bm, s, t, R)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=rec.get('weld', 1e-4) * s)
    if drop:
        TG.drop_parts(bm, rec)
        TG.fill_holes(bm, rec.get('fill', 64))
        TG.normals_out(bm)
    bm.normal_update()
    return bm


def raw_glb(path, drop=False):
    """the fitted raw as a glb (kit Blender frame, smooth shaded as Tripo exported it), for the render runs"""
    if os.path.exists(path): return path
    bm = raw_bmesh(drop)
    for f in bm.faces: f.smooth = True
    o = TG._bm_obj(bm, 'raw'); bm.free()
    m = bpy.data.materials.new('clay'); o.data.materials.append(m)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=False, export_yup=True)
    return path


def is_shell(o):
    m = o.data.materials[0] if o.type == 'MESH' and o.data.materials else None
    return '__shade' in o.name or (m is not None and m.name.split('.')[0] == 'shade')


def is_lit(o):
    return any(k in o.name for k in ('__lit', '__sdot'))


def slot_of(o):
    """'body_wzA__pearl__pecebee' -> 'pearl'; a kit-frame _sh.glb piece 'body_wzA' -> its material's name"""
    parts = o.name.split('.')[0].split('__')
    if len(parts) >= 2: return parts[1]
    m = o.data.materials[0] if o.data.materials else None
    return m.name.split('.')[0] if m else '?'


def node_of(o):
    return o.name.split('.')[0].split('__')[0]


def load(which, at=None):
    """import one version into the current scene in the kit's Blender frame: raw | v2 | v5 | v6 | a glb path.
       returns the mesh objects"""
    if which == 'raw':
        path, turned = raw_glb(os.path.join(OUT, 'work', '_rawfit.glb')), False
    elif which in ('v2', 'v5'):
        path, turned = SRC[which], False
    elif which == 'v6':
        path, turned = SRC['v6'], True
    else:
        path, turned = which, True
    M = (at if at is not None else Matrix.Identity(4)) @ (TURN if turned else Matrix.Identity(4))
    objs = TG._import(path, M)
    bpy.context.view_layer.update()   # (the children's matrix_world follow the root only after this)
    return [o for o in objs if o.type == 'MESH']


# ================================================================================================ rendering
CLAY = (0.62, 0.62, 0.62, 1)


def clay(objs):
    m = bpy.data.materials.new('clayR'); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = CLAY; b.inputs['Roughness'].default_value = 0.55
    for o in objs:
        if is_shell(o): o.hide_render = True; continue
        o.data.materials.clear(); o.data.materials.append(m)


def plastic(objs):
    """the imported flat colours as Roblox SmoothPlastic (roughness ~0.5, plain specular); Neon pieces glow"""
    for o in objs:
        if is_shell(o): continue
        for m in o.data.materials:
            if not m or not m.node_tree: continue
            b = m.node_tree.nodes.get('Principled BSDF')
            if not b: continue
            if is_lit(o):
                c = b.inputs['Base Color'].default_value
                b.inputs['Emission Color'].default_value = c; b.inputs['Emission Strength'].default_value = 2.0
            b.inputs['Roughness'].default_value = 0.5
            b.inputs['Metallic'].default_value = 0.0


LIGHT = dict(sun=(52, 0, -65), sun_e=2.0, fill_e=0.45, world=0.42)


def stage(Wd, Ht, samples=24, dark=False):
    sc = TG._scene(Wd, Ht, samples)
    sc.world.node_tree.nodes['Background'].inputs[1].default_value = 0.08 if dark else LIGHT['world']
    return sc


def lights(sc, key=None, fill=True):
    """one sun (the key) and a soft fill from the other side (Roblox: the sun + the ambient/fill light)"""
    a = key or LIGHT['sun']
    TG._sun(sc, (math.radians(a[0]), math.radians(a[1]), math.radians(a[2])), LIGHT['sun_e'])
    if fill:
        d = bpy.data.lights.new('fill', 'SUN'); d.energy = LIGHT['fill_e']; d.angle = 1.2
        o = bpy.data.objects.new('fill', d); o.rotation_euler = (math.radians(60), 0, math.radians(110))
        sc.collection.objects.link(o)


def bounds_of(objs):
    pts = [TG.W(o.matrix_world @ v.co) for o in objs if o.type == 'MESH' and not is_shell(o) for v in o.data.vertices]
    lo = Vector([min(p[k] for p in pts) for k in range(3)]); hi = Vector([max(p[k] for p in pts) for k in range(3)])
    return lo, hi


# the cameras every version is shot from (weapon-frame points; directions in the kit's Blender frame, as tripo_gun's
# VIEWS: -x is the gun's left, +y the muzzle, +z up)
GUN_LO, GUN_HI = Vector((-0.0918, -0.2618, -0.72)), Vector((0.092, 0.133, 0.4447))
SHOTS = [
    {'name': 'side', 'label': 'left side', 'at': None, 'dir': (-1, 0, 0), 'size': 'L'},
    {'name': 'q34', 'label': '3/4', 'q34': True},
    {'name': 'wing', 'label': 'rear wing', 'at': (-0.06, 0.045, 0.01), 'dir': (-1, 0.35, 0.45), 'size': 0.40},
    {'name': 'stock', 'label': 'stock', 'at': (-0.04, -0.075, 0.335), 'dir': (-1, -0.22, 0.28), 'size': 0.33},
    {'name': 'recv', 'label': 'receiver + handguard', 'at': (-0.03, 0.0, -0.17), 'dir': (-1, 0.3, 0.32), 'size': 0.36},
]


def shoot(sc, shot, path):
    lo, hi = GUN_LO, GUN_HI
    L = hi[2] - lo[2]
    mid = TG.B((0, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2))
    if shot.get('q34'):
        TG._cam(sc, mid + Vector((-0.75 * L, 0.80 * L, 0.42 * L)) * 0.95, mid + Vector((0, 0.04 * L, 0)), fov=40)
    else:
        at = mid if shot['at'] is None else TG.B(shot['at'])
        d = Vector(shot['dir']).normalized()
        size = L * 1.06 if shot['size'] == 'L' else shot['size']
        TG._cam(sc, at + d * 3.0, at, ortho=size)
    return TG._render(path)


# ================================================================================================ the measures
def soup(objs, keep):
    """triangles of the objects keep(o) accepts, in the WEAPON frame: points (n,3,3), corner normals (n,3,3), names"""
    P, N, names = [], [], []
    for o in objs:
        if o.type != 'MESH' or not keep(o): continue
        me = o.data; me.calc_loop_triangles()
        mw = o.matrix_world; nm = mw.to_3x3().inverted().transposed()
        cn = me.corner_normals
        for t in me.loop_triangles:
            P.append([tuple(TG.W(mw @ me.vertices[i].co)) for i in t.vertices])
            N.append([tuple(TG.W((nm @ cn[l].vector).normalized())) for l in t.loops])
            names.append(o.name.split('.')[0])
    return np.array(P), np.array(N), names


def bary(p, a, b, c):
    v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11 = v0.dot(v0), v0.dot(v1), v1.dot(v1)
    d20, d21 = v2.dot(v0), v2.dot(v1)
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-20: return 1 / 3, 1 / 3, 1 / 3
    v = (d11 * d20 - d01 * d21) / den; w = (d00 * d21 - d01 * d20) / den
    return 1 - v - w, v, w


def compare(raw, game, region_raw):
    """raw surface sample points (triangle centres of the raw region) -> the nearest game surface: the distance (mm)
       and the angle between the raw shading normal and the game's shading normal there (deg); area-weighted stats"""
    P, N, _ = raw
    G, GN, _ = game
    if not len(G): return None
    verts = [Vector(p) for t in G for p in t]
    tree = BVHTree.FromPolygons(verts, [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(len(G))])
    ds, angs, ws = [], [], []
    for i in region_raw:
        a, b, c = (Vector(x) for x in P[i])
        area = (b - a).cross(c - a).length / 2
        if area < 1e-12: continue
        cen = (a + b + c) / 3
        nr = Vector(N[i].sum(axis=0)).normalized()
        hit = tree.find_nearest(cen)
        if hit[0] is None: continue
        j = hit[2]
        u, v, w = bary(hit[0], *(Vector(x) for x in G[j]))
        ng = (Vector(GN[j][0]) * u + Vector(GN[j][1]) * v + Vector(GN[j][2]) * w).normalized()
        ds.append(hit[3] * 1000); angs.append(math.degrees(nr.angle(ng, 0.0))); ws.append(area)
    ds, angs, ws = np.array(ds), np.array(angs), np.array(ws)
    def wq(x, q):
        o = np.argsort(x); cw = np.cumsum(ws[o]); return float(x[o][np.searchsorted(cw, q * cw[-1])])
    return {'dist_mm_p50': round(wq(ds, 0.5), 2), 'dist_mm_p90': round(wq(ds, 0.9), 2),
            'area_over_1mm': round(float(ws[ds > 1.0].sum() / ws.sum()), 3),
            'normal_deg_p50': round(wq(angs, 0.5), 1), 'normal_deg_p90': round(wq(angs, 0.9), 1),
            'area_over_15deg': round(float(ws[angs > 15].sum() / ws.sum()), 3)}


def creases(P, idx, deg=25.0):
    """total length (m) of mesh edges inside the region whose two faces turn by more than deg (the relief's lines)"""
    from collections import defaultdict
    key = lambda p: (round(p[0], 6), round(p[1], 6), round(p[2], 6))
    edges = defaultdict(list)
    for i in idx:
        t = P[i]
        n = np.cross(t[1] - t[0], t[2] - t[0]); ln = np.linalg.norm(n)
        if ln < 1e-14: continue
        n = n / ln
        for a, b in ((0, 1), (1, 2), (2, 0)):
            k = tuple(sorted((key(t[a]), key(t[b]))))
            edges[k].append(n)
    tot = 0.0
    for (a, b), ns in edges.items():
        if len(ns) == 2 and math.degrees(math.acos(max(-1, min(1, float(np.dot(ns[0], ns[1])))))) > deg:
            tot += math.dist(a, b)
    return tot


REGIONS = {   # weapon frame; raw: by its loose part (the wings are Tripo's parts 1 and 2), the game: by piece name
    'rear wings': {'raw_parts': [(-0.062, 0.042, 0.012), (0.062, 0.042, 0.012)], 'names': ('rwing_',)},
    'stock': {'raw_main': True, 'z': (0.205, 1.0), 'names': ('stock_',)},
    'receiver + handguard': {'raw_main': True, 'z': (-0.47, 0.02), 'y': (-0.035, 1.0), 'names': ('body_', 'guard_', 'rail_')},
}


def raw_parts_index(P):
    """the raw triangles' loose part ids (connected by shared corners), biggest part = 0"""
    key = lambda p: (round(p[0], 6), round(p[1], 6), round(p[2], 6))
    par = {}
    def find(x):
        while par.setdefault(x, x) != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for t in P:
        ks = [key(p) for p in t]
        for k in ks[1:]:
            a, b = find(ks[0]), find(k)
            if a != b: par[a] = b
    roots = [find(key(t[0])) for t in P]
    size = {}
    for r in roots: size[r] = size.get(r, 0) + 1
    order = {r: i for i, r in enumerate(sorted(size, key=lambda r: -size[r]))}
    return np.array([order[r] for r in roots])


def region_idx(name, P, names, part=None):
    r = REGIONS[name]
    C = P.mean(axis=1)
    out = []
    for i in range(len(P)):
        c = C[i]
        if part is not None:   # (raw)
            if 'raw_parts' in r:
                if part['wing'][i]: out.append(i)
                continue
            if part['id'][i] != 0: continue
        else:
            if not names[i].startswith(r['names']): continue
        if 'z' in r and not (r['z'][0] <= c[2] <= r['z'][1]): continue
        if 'y' in r and not (r['y'][0] <= c[1] <= r['y'][1]): continue
        out.append(i)
    return out


def measures(versions):
    """versions: {name: soup}; the raw is 'raw'"""
    raw = versions['raw']
    P = raw[0]
    pid = raw_parts_index(P)
    C = P.mean(axis=1)
    cent = {}
    for k in set(pid.tolist()):
        cent[k] = P[pid == k].reshape(-1, 3).mean(axis=0)
    wing_ids = {k for k, c in cent.items() for q in REGIONS['rear wings']['raw_parts'] if np.linalg.norm(c - np.array(q)) < 0.03}
    part = {'id': pid, 'wing': np.array([p in wing_ids for p in pid])}
    out = {}
    for reg in REGIONS:
        ri = region_idx(reg, P, raw[2], part)
        row = {'raw': {'tris': len(ri), 'crease_m': round(creases(P, ri), 3)}}
        for v, s in versions.items():
            if v == 'raw': continue
            gi = region_idx(reg, s[0], s[2])
            row[v] = {'tris': len(gi), 'crease_m': round(creases(s[0], gi), 3)}
            row[v].update(compare(raw, (s[0][gi], s[1][gi], [s[2][i] for i in gi]), ri) or {})
        out[reg] = row
    return out


# ================================================================================================ the sheet maker
GRID = r'''
import json, sys
from PIL import Image, ImageDraw, ImageFont
s = json.load(open(sys.argv[1], encoding='utf8'))
cw, ch, lw, hh = s['cw'], s['ch'], s.get('lw', 0), s.get('hh', 40)
cols, rows = len(s['cols']), len(s['rows'])
notes = s.get('notes', [])
def font(n, b=True):
    try: return ImageFont.truetype('arialbd.ttf' if b else 'arial.ttf', n)
    except Exception: return ImageFont.load_default()
FT, FH, FN = font(30), font(22), font(19, False)
nh = 34 + 25 * len(notes) if notes else 0
W, H = lw + cw * cols, 50 + nh + hh + ch * rows
out = Image.new('RGB', (W, H), (28, 30, 36))
d = ImageDraw.Draw(out)
d.text((14, 10), s['title'], fill=(242, 242, 242), font=FT)
y = 50
for ln in notes:
    d.text((18, y), ln, fill=(225, 225, 225), font=FN); y += 25
y = 50 + nh
for j, c in enumerate(s['cols']):
    d.rectangle([lw + j * cw, y, lw + (j + 1) * cw - 2, y + hh - 2], fill=(44, 47, 56))
    d.text((lw + j * cw + 10, y + 9), c, fill=(240, 240, 240), font=FH)
y += hh
for i, r in enumerate(s['rows']):
    if lw:
        d.rectangle([0, y + i * ch, lw - 2, y + (i + 1) * ch - 2], fill=(44, 47, 56))
        for k, part in enumerate(r.split('|')):
            d.text((10, y + i * ch + 12 + 26 * k), part, fill=(240, 240, 240), font=FH)
    for j in range(cols):
        p = s['cells'][i][j]
        if not p: continue
        im = Image.open(p).convert('RGB'); im.thumbnail((cw - 2, ch - 2))
        out.paste(im, (lw + j * cw + (cw - 2 - im.width) // 2, y + i * ch + (ch - 2 - im.height) // 2))
        cap = s.get('caps', {}).get('%d,%d' % (i, j))
        if cap:
            d.rectangle([lw + j * cw, y + (i + 1) * ch - 30, lw + (j + 1) * cw - 2, y + (i + 1) * ch - 2], fill=(18, 18, 22))
            d.text((lw + j * cw + 8, y + (i + 1) * ch - 27), cap, fill=(235, 235, 235), font=FN)
out.save(s['out'], quality=90)
print('SHEET', s['out'], out.size)
'''


def grid(out, title, cols, rows, cells, notes=(), caps=None, cw=640, ch=400, lw=190):
    os.makedirs(os.path.join(OUT, 'work'), exist_ok=True)
    js = os.path.join(OUT, 'work', '_grid_%d.json' % int(time.time() * 1000))
    with open(js, 'w', encoding='utf8') as fh:
        json.dump({'out': out, 'title': title, 'cols': cols, 'rows': rows, 'cells': cells, 'notes': list(notes),
                   'caps': caps or {}, 'cw': cw, 'ch': ch, 'lw': lw}, fh)
    r = subprocess.run([PY, '-c', GRID, js], capture_output=True, text=True)
    print(r.stdout.strip(), r.stderr.strip()[-600:])


# ================================================================================================ DIAG
DIAG_COLS = [('raw', 'clay'), ('v2', 'clay'), ('v5', 'clay'), ('v6', 'clay'), ('v2', 'colour'), ('v6', 'colour')]


def diag(out_dir, sheet_path):
    pdir = os.path.join(out_dir, 'work', 'diag'); os.makedirs(pdir, exist_ok=True)
    raw_glb(os.path.join(out_dir, 'work', '_rawfit.glb'))
    # ---- the measures (raw vs each version, per region)
    vers = {}
    for v in ('raw', 'v2', 'v5', 'v6'):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        objs = load(v)
        vers[v] = soup(objs, lambda o: not is_shell(o) and not is_lit(o))
    m = measures(vers)
    # shade shells: which nodes, how many triangles, texel density (the bake json of each run)
    shells = {}
    for v in ('v2', 'v5', 'v6'):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        objs = load(v)
        sh = [o for o in objs if is_shell(o)]
        shells[v] = {'nodes': sorted(node_of(o).split('_wz')[0] for o in sh),
                     'tris': sum(len(p.vertices) - 2 for o in sh for p in o.data.polygons),
                     'tris_gun': sum(len(p.vertices) - 2 for o in objs if not is_shell(o) for p in o.data.polygons),
                     'unshaded_painted': sorted({node_of(o) + '__' + slot_of(o) for o in objs if not is_shell(o) and not is_lit(o)
                                                 and slot_of(o) not in ('graph',) and node_of(o).split('_wz')[0] not in
                                                 [node_of(s).split('_wz')[0] for s in sh]})}
    for v, d in (('v2', 'v2'), ('v5', 'v5'), ('v6', 'v6')):
        bj = os.path.join(VAULT, d, K + '_bake.json')
        cj = os.path.join(VAULT, d, K + '_clean.json')
        if os.path.exists(bj):
            b = json.load(open(bj)); shells[v].update({k: b.get(k) for k in ('texels_per_m', 'atlas_used')})
        elif os.path.exists(cj):
            b = json.load(open(cj)).get('bake', {}); shells[v].update({k: b.get(k) for k in ('texels_per_m', 'atlas_used')})
    rec = json.load(open(SRC['rec']))
    info = {'measures': m, 'shells': shells, 'v6_recipe': {k: rec.get(k) for k in ('decimate', 'reshape', 'planar', 'sharp', 'palette')}}
    with open(os.path.join(out_dir, 'diag.json'), 'w') as fh: json.dump(info, fh, indent=1)
    print('DIAG MEASURES', json.dumps(info, indent=1))
    # ---- the renders
    cells = []
    for shot in SHOTS:
        row = []
        for v, mode in DIAG_COLS:
            path = os.path.join(pdir, '%s_%s_%s.png' % (shot['name'], v, mode))
            if not os.path.exists(path):
                sc = stage(800, 500, 24)
                objs = load(v)
                (clay if mode == 'clay' else plastic)(objs)
                lights(sc)
                shoot(sc, shot, path)
            row.append(path)
        cells.append(row)
    return info, cells


def diag_sheet(info, cells, sheet_path):
    m, sh = info['measures'], info['shells']
    def f(reg, v, k): return m[reg][v].get(k, 0)
    w, s, r = 'rear wings', 'stock', 'receiver + handguard'
    notes = [
        'WHAT WAS LOST (raw Tripo vs the live v6; measured on the surfaces, weapon frame):',
        '1. Shading flattened: v6 shades smooth only up to 40 deg, then a face-area Weighted Normal pass (Tripo shades all smooth), so soft relief reads as flat facets. '
        'Shading normals turned from the raw by >15 deg on %d%% of the wings, %d%% of the stock, %d%% of the receiver.' % (
            100 * f(w, 'v6', 'area_over_15deg'), 100 * f(s, 'v6', 'area_over_15deg'), 100 * f(r, 'v6', 'area_over_15deg')),
        '2. Decimation was mild, not the cause: wings cut to 0.6, stock to 0.66 (raw wings %d tris -> v6 %d incl. cut-in borders), but the crease lines (>25 deg) '
        'survived (wings %.2f m -> %.2f m, stock %.2f m -> %.2f m) and the v6 surface sits within %.2f mm (P90) of the raw: the clay columns match.' % (
            m[w]['raw']['tris'], m[w]['v6']['tris'], m[w]['raw']['crease_m'], m[w]['v6']['crease_m'], m[s]['raw']['crease_m'], m[s]['v6']['crease_m'], f(w, 'v6', 'dist_mm_p90')),
        '3. Relief moved/flattened: v2 reshaped the wings flat onto the sides (wing surface P90 %.1f mm off the raw); v5/v6 put them back (P90 %.1f / %.1f mm); '
        'v6\'s planar pass pressed the receiver sides flat (<=1 mm).' % (f(w, 'v2', 'dist_mm_p90'), f(w, 'v5', 'dist_mm_p90'), f(w, 'v6', 'dist_mm_p90')),
        '4. THE MAIN LOSS - colours flattened to plain fills: pearl ecebee / wing f7f4ee differ ~3% in brightness, so feathers melt into the body; near-white albedo '
        'clips to white under the hall lamps (relief invisible); gold contour fills cover the feather steps; gold is flat paint, not metal; no cavity or edge lines.',
        '5. Shade shells thin and partial: v6 shells cover %s only (%d tris), at %s texels/m on %d%% of one 1024 atlas: soft AO, no cavity or edge lines; '
        'gold trims, rail, halo, brake and shroud get no shading at all.' % (
            ', '.join(sh['v6']['nodes']), sh['v6']['tris'], sh['v6'].get('texels_per_m'), round(100 * (sh['v6'].get('atlas_used') or 0))),
        'Earlier versions: v5 = v6 geometry; v2 reshaped the wings flat (78% of their area turned >15 deg) - no earlier version kept more geometric detail than v5/v6. '
        'Gone on purpose (owner picks): the halo above, the front wings, Tripo\'s sights. So the fix is the SURFACE: normals, AO/cavity/edges, paint.',
    ]
    caps = {}
    for i, shot in enumerate(SHOTS):
        reg = {'wing': w, 'stock': s, 'recv': r}.get(shot['name'])
        if not reg: continue
        for j, (v, mode) in enumerate(DIAG_COLS):
            if mode != 'clay': continue
            if v == 'raw': caps['%d,%d' % (i, j)] = '%d tris, creases %.2f m' % (m[reg]['raw']['tris'], m[reg]['raw']['crease_m'])
            else: caps['%d,%d' % (i, j)] = '%d tris, %.2f m, >15deg %d%%' % (m[reg][v]['tris'], m[reg][v]['crease_m'], 100 * m[reg][v].get('area_over_15deg', 0))
    cols = ['owner\'s raw Tripo (clay)', 'v2 (clay)', 'v5 (clay)', 'v6 LIVE (clay)', 'v2 (colour + shells)', 'v6 LIVE (colour + shells)']
    rows = [sh_['label'] for sh_ in SHOTS]
    grid(sheet_path, 'Angel rifle (ar@ar_seraph_tripo): what the detail lost, raw -> v2 -> v5 -> v6 (same cameras, same light)',
         cols, rows, cells, notes, caps, cw=560, ch=350, lw=150)


# ================================================================================================ BAKE: any tripo_gun gun
# A gun is found by its key (base@skin) through its vault folder (the one holding w_<key>_clean.json). An optional
# bake_spec.json there (or --spec) holds what is the gun's own; every key is optional:
# {
#   "recipe": "recipe.json", "clean": "w_<key>_clean.json", "raw": "<raw.glb>",   (paths relative to the folder)
#   "game": "<the game mesh .glb>",   an upload file (PRE_TURNed, pieces "<node>__<slot>__<look>") or a kit-frame
#                                     K_sh.glb / K.glb from tripo_gun (pieces "<node>_wz<X>", material = slot)
#   "now": "<glb>",                   what is in the game now, for the sheet's BEFORE column (default: game)
#   "out": "<dir>",                   (default: weapons-kit/tripo_<folder>_bake)
#   "plain": ["sight_", "fsight_"],   piece prefixes left as they are (no picture): sights, dark bits
#   "kit": ["muzzle_", "halo_"],      piece prefixes built from kit shapes (no raw surface): clean bevel normals
#   "density": 1400,                  texels per metre wanted (the number of 1024 atlases follows; "atlases": n)
#   "groups": [["stock_", "rwing_"]], pieces that share an atlas (the rest fill the others)
#   "slots": {"gold": {"metal": 0.8, "rough": 0.34, "edge": 0.4, "cav": 0.3, "tint": "8a5a20", "lift": "fff0c0",
#                      "lines": 0.0, "scale": 1.0}},   the finish per slot (defaults: by colour, below)
#   "hi_sharp": 60,                   the raw surface's shading: smooth up to this angle (Tripo's own look)
#   "wobble": [1.5, 5.0],             raw normal turns under a (deg) dropped, over b kept, in between faded
#   "paint": [...],                   painted motifs (see PAINT below), "recipe_decals": true (the recipe's cut-in
#                                     decals painted as smooth shapes over their faces, in their slots' colours)
#   "relief": [...],                  detail normals: rivets, grooves, piping (see PAINT below)
#   "shots": [{"name", "label", "at": [x, y, z], "dir": [x, y, z] (Blender frame), "size": m}],   sheet close-ups
# }
ATLAS = 1024
CAGE = 0.003          # the ray reaches this far out and in from the game surface for the raw one (metres)
BEVEL_W = 0.0012      # a kit part's rounded-edge normal reaches this far in from each hard edge
SAMPLES = 64          # Cycles samples for the AO masks


def glb_names(path):
    import struct
    b = open(path, 'rb').read()
    n = struct.unpack('<I', b[12:16])[0]
    j = json.loads(b[20:20 + n])
    return [nd.get('name', '') for nd in j.get('nodes', [])], j


def is_upload(path):
    """an upload file (PRE_TURNed, look codes in the names) or a kit-frame file"""
    names, _ = glb_names(path)
    return any(nm.count('__') >= 2 for nm in names)


def gun_cfg(key, spec_path=None, game=None, out=None):
    import glob as G
    K = 'w_' + key
    hits = G.glob(os.path.join(TG.ROOT, 'tripo-*', '*', K + '_clean.json'))
    if not hits: raise SystemExit('no vault folder holds %s_clean.json' % K)
    d = os.path.dirname(hits[0])
    sp = spec_path or os.path.join(d, 'bake_spec.json')
    spec = json.load(open(sp)) if os.path.exists(sp) else {}
    def rel(p): return p if os.path.isabs(p) else os.path.join(d, p)
    cfg = {'key': key, 'K': K, 'base': key.split('@')[0], 'skin': key.split('@')[1], 'dir': d, 'spec': spec,
           'recipe': rel(spec.get('recipe', 'recipe.json')), 'clean': rel(spec.get('clean', K + '_clean.json'))}
    cj = json.load(open(cfg['clean']))
    cfg['raw'] = rel(spec['raw']) if 'raw' in spec else cj['raw']
    cfg['game'] = game or (rel(spec['game']) if 'game' in spec else os.path.join(d, K + '_sh.glb'))
    cfg['now'] = rel(spec['now']) if 'now' in spec else cfg['game']
    cfg['out'] = out or (rel(spec['out']) if 'out' in spec else
                         os.path.join(KIT, 'tripo_' + os.path.basename(d).replace('-', '_') + '_bake'))
    cfg['spots'] = cj.get('spots')
    return cfg


def lin(h): return np.array([TG.gunkit.lin(c) for c in TG.gunkit.hex_rgb(h)], dtype=np.float32)
def srgb_np(a):
    a = np.clip(a, 0, 1)
    return np.where(a <= 0.0031308, 12.92 * a, 1.055 * np.power(a, 1 / 2.4) - 0.055)


def slot_finish(slot, colour, spec):
    """a slot's finish: metal, rough, edge (highlight amount), cav (cavity darkening), tint (shadow colour, linear
       multiplier), lift (highlight colour), lines (extra crease lines, e.g. feathers), scale (albedo multiplier)"""
    c = lin(colour)
    import colorsys
    h, l, s = colorsys.rgb_to_hls(*[float(x) for x in srgb_np(c)])
    goldish = ('gold' in slot) or (0.08 < h < 0.14 and s > 0.35 and 0.35 < l < 0.7 and 'duck' not in slot)
    f = {'metal': 0.75 if goldish else 0.0, 'rough': 0.34 if goldish else 0.45, 'edge': 0.45 if goldish else 0.32,
         'cav': 0.32, 'lines': 0.0, 'scale': 1.0, 'gold': goldish}
    # the shadow tint: the colour's own hue, deeper and a little more saturated (toy shading, never grey mud)
    t = np.power(np.maximum(c, 1e-4), 0.55); t = t / max(float(t.max()), 1e-4)
    f['tint'] = (0.42 * t + 0.08).tolist()   # (the multiplier at full shadow: shading = 1 - d + d tint)
    f['lift'] = [1.0, 0.97, 0.88] if goldish else [1.0, 1.0, 1.0]
    f.update({k: v for k, v in spec.get('slots', {}).get(slot, {}).items()})
    for k in ('tint', 'lift'):
        if isinstance(f[k], str): f[k] = (lin(f[k]) if k == 'tint' else srgb_np(lin(f[k]))).tolist()
    return f


# ---------------------------------------------------------------------------------------------- the game mesh
def load_game(path):
    """the game mesh's pieces, untouched (as the file holds them). returns (objects, turned). each object gets
       jf_piece = '<node>__<slot>' and jf_up = its upload name"""
    turned = is_upload(path)
    bpy.ops.import_scene.gltf(filepath=path)
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in objs:
        if o.parent is not None:
            mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in [o for o in bpy.context.scene.objects if o.type != 'MESH']: bpy.data.objects.remove(o, do_unlink=True)
    bpy.context.view_layer.update()
    for o in objs:
        if o.matrix_world != Matrix.Identity(4):
            o.data = o.data.copy(); o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
        base = o.name.split('.')[0]
        if base.count('__') >= 2: piece = '__'.join(base.split('__')[:2]); up = base
        else:
            m = o.data.materials[0] if o.data.materials else None
            piece = base.split('__')[0] + '__' + (m.name.split('.')[0] if m else 'none'); up = None
        o['jf_piece'] = piece
        if up: o['jf_up'] = up
    return objs, turned


def piece_roles(objs, pal, spec):
    """per object: 'shell' (dropped), 'plain' (left as it is: glow, glass, dark, sights) or 'sa' (gets the maps)"""
    plain = tuple(spec.get('plain', ['sight_', 'fsight_']))
    out = {}
    for o in objs:
        node, slot = o['jf_piece'].split('__')
        if slot == 'shade' or is_shell(o): out[o.name] = 'shell'; continue
        p = pal.get(slot, {'color': '808080', 'kind': 'p'})
        lum = float(np.dot(lin(p['color']), [0.2126, 0.7152, 0.0722]))
        if p['kind'] != 'p' or lum < spec.get('dark_lum', 0.055) or o['jf_piece'].startswith(plain) or node.startswith(plain):
            out[o.name] = 'plain'
        else:
            out[o.name] = 'sa'
    return out


def area_of(o):
    return sum(p.area for p in o.data.polygons)


def atlas_groups(sa, spec):
    """the 'sa' pieces into atlases: spec groups first, then by node along the gun, about equal area each"""
    area = {o.name: area_of(o) for o in sa}
    total = sum(area.values())
    dens = spec.get('density', 1400)
    n = spec.get('atlases') or max(1, math.ceil(total * dens * dens / (ATLAS * ATLAS * 0.58)))
    groups = [[o for o in sa if o['jf_piece'].startswith(tuple(g))] for g in spec.get('groups', [])]
    used = {o.name for g in groups for o in g}
    rest = [o for o in sa if o.name not in used]
    n_rest = max(n - len(groups), 1 if rest else 0)
    if rest:
        # (whole nodes together, the biggest first into the emptiest atlas: about the same density in every atlas)
        nodes = {}
        for o in rest: nodes.setdefault(o['jf_piece'].split('__')[0].split('_wz')[0], []).append(o)
        bins = [[] for _ in range(n_rest)]; fill = [0.0] * n_rest
        for k in sorted(nodes, key=lambda k: -sum(area[o.name] for o in nodes[k])):
            b = fill.index(min(fill)); bins[b] += nodes[k]; fill[b] += sum(area[o.name] for o in nodes[k])
        groups += bins
    return [g for g in groups if g], total


# ---------------------------------------------------------------------------------------------- the raw surface
def high_surface(cfg, rec, work):
    """the raw Tripo surface placed exactly as the game mesh's Tripo parts: tripo_gun's whole clean (fit, drops,
       straighten, mirror, reshape, cuts) re-run with NO decimation, joined, welded, shaded smooth up to hi_sharp
       degrees. returns (tree, V (n,3), T (m,3) vertex ids, CN (m,3,3) corner normals) in the kit's Blender frame"""
    hdir = os.path.join(work, 'high'); os.makedirs(hdir, exist_ok=True)
    src = cfg['spec'].get('high', 'nodec')   # nodec: tripo_gun's clean again without decimation | clean: the vault's
    glb = os.path.join(hdir, cfg['K'] + '_clean.glb')   # cleaned pieces as they are | rawfit | a .glb path
    if src == 'clean': glb = cfg['clean'][:-len('.json')] + '.glb'
    elif src == 'rawfit': glb = os.path.join(cfg['dir'], cfg['K'] + '_rawfit.glb')
    elif src != 'nodec': glb = src if os.path.isabs(src) else os.path.join(cfg['dir'], src)
    if src == 'nodec' and not os.path.exists(glb):
        r2 = json.loads(json.dumps(rec)); r2['decimate'] = {}
        TG.TURNED.clear()
        TG.clean(cfg['raw'], cfg['base'], cfg['skin'], r2, hdir)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
    bm = bmesh.new()
    for o in [o for o in bpy.context.scene.objects if o.type == 'MESH']:
        me = o.data.copy(); me.transform(o.matrix_world); bm.from_mesh(me); bpy.data.meshes.remove(me)
    for o in list(bpy.context.scene.objects): bpy.data.objects.remove(o, do_unlink=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=2e-6)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bm.normal_update()
    lim = math.radians(cfg['spec'].get('hi_sharp', 60))
    for f in bm.faces: f.smooth = True
    for e in bm.edges:
        fs = e.link_faces
        e.smooth = len(fs) == 2 and fs[0].normal.angle(fs[1].normal, 0.0) < lim
    me = bpy.data.meshes.new('high'); bm.to_mesh(me); bm.free()
    me.calc_loop_triangles()
    V = np.empty(len(me.vertices) * 3, np.float64); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    LT = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get('loops', LT); LT = LT.reshape(-1, 3)
    LV = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', LV)
    CN = np.empty(len(me.loops) * 3, np.float64); me.corner_normals.foreach_get('vector', CN); CN = CN.reshape(-1, 3)
    T = LV[LT]
    tree = BVHTree.FromPolygons([Vector(v) for v in V], [tuple(t) for t in T.tolist()], all_triangles=True)
    print('HIGH SURFACE', len(T), 'tris from', glb)
    return tree, V, T, CN[LT]


# ---------------------------------------------------------------------------------------------- texels
def raster(objs, turned, N=ATLAS):
    """every texel of the atlas the objects' 'UVMap' covers: piece index, position, normal, tangent, sign (kit
       Blender frame). returns dict of (N, N, ..) arrays, rows bottom-up (Blender's image order)"""
    R = np.diag([-1.0, -1.0, 1.0]) if turned else np.eye(3)
    pid = np.full((N, N), -1, np.int32); isl = np.full((N, N), -1, np.int32); nisl = 0
    P = np.zeros((N, N, 3), np.float32); Nn = np.zeros((N, N, 3), np.float32); Tn = np.zeros((N, N, 3), np.float32)
    S = np.ones((N, N), np.float32)
    for k, o in enumerate(objs):
        me = o.data
        me.calc_tangents(uvmap='UVMap')
        me.calc_loop_triangles()
        nl = len(me.loops)
        uv = np.empty(nl * 2, np.float64); me.uv_layers['UVMap'].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2) * N - 0.5
        co = np.empty(len(me.vertices) * 3, np.float64); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3) @ R.T
        lv = np.empty(nl, np.int32); me.loops.foreach_get('vertex_index', lv)
        tg = np.empty(nl * 3, np.float64); me.loops.foreach_get('tangent', tg); tg = tg.reshape(-1, 3) @ R.T
        sg = np.empty(nl, np.float64); me.loops.foreach_get('bitangent_sign', sg)
        cn = np.empty(nl * 3, np.float64); me.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3) @ R.T
        lt = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get('loops', lt); lt = lt.reshape(-1, 3)
        # (UV islands: loops joined by a triangle or sharing a vertex at the same UV; small ones get blurred later)
        par = list(range(nl))
        def find(i):
            while par[i] != i:
                par[i] = par[par[i]]; i = par[i]
            return i
        for a_, b_, c_ in lt.tolist():
            for x_ in (b_, c_):
                ra, rb = find(a_), find(x_)
                if ra != rb: par[ra] = rb
        seen = {}
        for li in range(nl):
            kk = (int(lv[li]), round(uv[li, 0], 2), round(uv[li, 1], 2))
            if kk in seen:
                ra, rb = find(li), find(seen[kk])
                if ra != rb: par[ra] = rb
            else: seen[kk] = li
        roots = {}
        tri_isl = [roots.setdefault(find(int(t_[0])), len(roots)) + nisl for t_ in lt]
        nisl += len(roots)
        for ti, t in enumerate(lt):
            q = uv[t]
            x0, y0 = np.floor(q.min(axis=0)).astype(int); x1, y1 = np.ceil(q.max(axis=0)).astype(int)
            x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, N - 1), min(y1, N - 1)
            if x1 < x0 or y1 < y0: continue
            xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
            (ax, ay), (bx, by), (cx, cy) = q
            den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(den) < 1e-12: continue
            w0 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den
            w1 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / den
            w2 = 1 - w0 - w1
            m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            if not m.any(): continue
            yy, xx = ys[m], xs[m]
            W3 = np.stack([w0[m], w1[m], w2[m]], 1)
            pid[yy, xx] = k; isl[yy, xx] = tri_isl[ti]
            P[yy, xx] = W3 @ co[lv[t]]
            Nn[yy, xx] = W3 @ cn[t]
            Tn[yy, xx] = W3 @ tg[t]
            S[yy, xx] = np.sign(W3 @ sg[t] + 1e-9)
    inside = pid >= 0
    # (two texels round every island: the nearest island texel's values, so the borders bake too)
    grow = inside.copy()
    for _ in range(2):
        for sh in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            src = np.roll(grow, sh, axis=(0, 1)) & ~grow
            if not src.any(): continue
            for arr in (P, Nn, Tn):
                arr[src] = np.roll(arr, sh, axis=(0, 1))[src]
            S[src] = np.roll(S, sh, axis=(0, 1))[src]; pid[src] = np.roll(pid, sh, axis=(0, 1))[src]
            isl[src] = np.roll(isl, sh, axis=(0, 1))[src]
            grow = grow | src
    nrm = lambda a: a / np.maximum(np.linalg.norm(a, axis=-1, keepdims=True), 1e-9)
    return {'pid': pid, 'isl': isl, 'inside': inside, 'ok': grow, 'P': P, 'N': nrm(Nn), 'T': nrm(Tn), 'S': S}


def to_tangent(n, Nl, T, S):
    """world normals n -> tangent space (OpenGL: +Y = the bitangent, MikkTSpace frame of the game mesh)"""
    T = T - Nl * np.sum(T * Nl, -1, keepdims=True)
    T = T / np.maximum(np.linalg.norm(T, axis=-1, keepdims=True), 1e-9)
    Bt = np.cross(Nl, T) * S[..., None]
    return np.stack([np.sum(n * T, -1), np.sum(n * Bt, -1), np.sum(n * Nl, -1)], -1)


def transfer(tex, hi, kit_mask, wobble=(1.5, 5.0)):
    """per texel: the raw surface's normal under the game surface (a ray from CAGE out, along -normal, 2 CAGE long;
       else the nearest raw point within CAGE / 2). returns (normal (N,N,3) world, hit mask, hit position)"""
    tree, V, T, CN = hi
    ok = tex['ok'] & ~kit_mask
    idx = np.flatnonzero(ok.ravel())
    P = tex['P'].reshape(-1, 3)[idx].astype(np.float64); Nl = tex['N'].reshape(-1, 3)[idx].astype(np.float64)
    org = P + Nl * CAGE
    loc = np.full((len(idx), 3), np.nan); fi = np.full(len(idx), -1, np.int64)
    rc, fn = tree.ray_cast, tree.find_nearest
    for i in range(len(idx)):
        h = rc(Vector(org[i]), Vector(-Nl[i]), 2 * CAGE)
        if h[0] is None:
            h = fn(Vector(P[i]), CAGE * 0.5)
            if h[0] is None: continue
        loc[i] = h[0]; fi[i] = h[2]
    got = fi >= 0
    out = tex['N'].reshape(-1, 3).astype(np.float64).copy()
    hitpos = tex['P'].reshape(-1, 3).astype(np.float64).copy()
    g = np.flatnonzero(got)
    tri = T[fi[g]]
    a, b, c = V[tri[:, 0]], V[tri[:, 1]], V[tri[:, 2]]
    p = loc[g]
    v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11 = np.sum(v0 * v0, 1), np.sum(v0 * v1, 1), np.sum(v1 * v1, 1)
    d20, d21 = np.sum(v2 * v0, 1), np.sum(v2 * v1, 1)
    den = np.where(np.abs(d00 * d11 - d01 * d01) < 1e-30, 1e-30, d00 * d11 - d01 * d01)
    wv = (d11 * d20 - d01 * d21) / den; ww = (d00 * d21 - d01 * d20) / den; wu = 1 - wv - ww
    cnf = CN[fi[g]]
    nh = cnf[:, 0] * wu[:, None] + cnf[:, 1] * wv[:, None] + cnf[:, 2] * ww[:, None]
    nh /= np.maximum(np.linalg.norm(nh, axis=1, keepdims=True), 1e-12)
    nl = Nl[g]
    good = np.sum(nh * nl, 1) > 0.2
    # Tripo wobble out: a turn under wobble[0] degrees is dropped, over wobble[1] kept whole, faded in between
    cosang = np.clip(np.sum(nh * nl, 1), -1, 1); ang = np.degrees(np.arccos(cosang))
    a0, a1 = wobble
    keep = np.clip((ang - a0) / max(a1 - a0, 1e-6), 0, 1); keep = keep * keep * (3 - 2 * keep)
    new_ang = np.radians(ang * keep)
    perp = nh - nl * cosang[:, None]
    pl = np.linalg.norm(perp, axis=1, keepdims=True)
    perp = np.where(pl > 1e-9, perp / np.maximum(pl, 1e-12), 0)
    nh2 = nl * np.cos(new_ang)[:, None] + perp * np.sin(new_ang)[:, None]
    sel = idx[g[good]]
    out[sel] = nh2[good]; hitpos[sel] = p[good]
    hit = np.zeros(out.shape[0], bool); hit[sel] = True
    Nn = tex['N'].shape[0]
    print('TRANSFER %d texels, %d on the raw surface (%.0f%%)' % (len(idx), hit.sum(), 100 * hit.sum() / max(len(idx), 1)))
    return out.reshape(Nn, Nn, 3), hit.reshape(Nn, Nn), hitpos.reshape(Nn, Nn, 3)


def hard_edges(o, turned, deg=25.0):
    """a piece's hard edges: (a (m,3), b (m,3), the two faces' mean normal (m,3), convex (m,)) kit Blender frame"""
    R = np.diag([-1.0, -1.0, 1.0]) if turned else np.eye(3)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)
    bm.normal_update()
    A, Bv, En, cv = [], [], [], []
    for e in bm.edges:
        fs = e.link_faces
        if len(fs) != 2: continue
        n0, n1 = fs[0].normal, fs[1].normal
        if n0.angle(n1, 0.0) < math.radians(deg): continue
        c1 = fs[1].calc_center_median()
        convex = (c1 - e.verts[0].co).dot(n0) < 0
        A.append(e.verts[0].co[:]); Bv.append(e.verts[1].co[:]); En.append((n0 + n1).normalized()[:]); cv.append(convex)
    bm.free()
    if not A: return None
    return (np.array(A) @ R.T, np.array(Bv) @ R.T, np.array(En) @ R.T, np.array(cv))


def bevel_normals(tex, objs, turned, sel):
    """kit parts: a rounded-edge normal within BEVEL_W of each hard edge (the face normal leaning half way to the
       edge's mean normal at the edge); returns (normals, convex-edge mask 0..1)"""
    out = tex['N'].copy(); edge = np.zeros(tex['pid'].shape, np.float32)
    for k, o in enumerate(objs):
        if not sel[k]: continue
        he = hard_edges(o, turned)
        m = tex['ok'] & (tex['pid'] == k)
        if he is None or not m.any(): continue
        A, Bv, En, cv = he
        ii = np.flatnonzero(m.ravel())
        Pk = tex['P'].reshape(-1, 3)[ii]
        best = np.full(len(ii), 1e9); bj = np.zeros(len(ii), np.int64)
        AB = Bv - A; L2 = np.maximum(np.sum(AB * AB, 1), 1e-18)
        for s0 in range(0, len(A), 64):
            a, ab, l2 = A[s0:s0 + 64], AB[s0:s0 + 64], L2[s0:s0 + 64]
            t = np.clip(np.einsum('nk,mk->nm', Pk, ab) - np.sum(a * ab, 1)[None], 0, None) / l2[None]
            t = np.clip(t, 0, 1)
            q = a[None] + t[..., None] * ab[None]
            d = np.linalg.norm(Pk[:, None] - q, axis=2)
            j = np.argmin(d, 1); dj = d[np.arange(len(ii)), j]
            upd = dj < best; best[upd] = dj[upd]; bj[upd] = j[upd] + s0
        t = np.clip(1 - best / BEVEL_W, 0, 1); t = t * t * (3 - 2 * t)
        Nl = tex['N'].reshape(-1, 3)[ii]
        n = Nl + (En[bj] - Nl) * (0.5 * t)[:, None]
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
        o2 = out.reshape(-1, 3); o2[ii] = n
        e2 = edge.reshape(-1); e2[ii] = np.maximum(e2[ii], t * cv[bj])
    return out, edge


# ---------------------------------------------------------------------------------------------- image helpers
def blur(a, sigma, mask=None):
    """separable Gaussian (masked: blur(a m) / blur(m), so empty texels never bleed in)"""
    if sigma <= 0: return a
    r = max(1, int(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    def conv(x):
        for ax in (0, 1):
            acc = np.zeros_like(x)
            for i, w in enumerate(k): acc += w * np.roll(x, i - r, axis=ax)
            x = acc
        return x
    if mask is None: return conv(a)
    m = mask.astype(np.float32)
    if a.ndim == 3: m = m[..., None]
    return conv(a * m) / np.maximum(conv(np.broadcast_to(m, a.shape).copy()), 1e-6)


def pushpull(a, valid):
    """fill the texels outside every island smoothly from the islands (pull-push): no hard island outline is left
       for the eye (or Roblox's mip maps) to find"""
    a = a.astype(np.float32); m = valid.astype(np.float32)
    if a.ndim == 2: a = a[..., None]; squeeze = True
    else: squeeze = False
    levels = [(a * m[..., None], m)]
    while levels[-1][1].shape[0] > 1:
        A, M = levels[-1]
        h = A.shape[0] // 2
        A2 = A.reshape(h, 2, h, 2, -1).sum(axis=(1, 3)); M2 = M.reshape(h, 2, h, 2).sum(axis=(1, 3))
        levels.append((A2, M2))
    A, M = levels[-1]
    cur = A / np.maximum(M[..., None], 1e-9)
    for A, M in reversed(levels[:-1]):
        up = np.repeat(np.repeat(cur, 2, 0), 2, 1)
        up = (up + np.roll(up, 1, 0) + np.roll(up, -1, 0) + np.roll(up, 1, 1) + np.roll(up, -1, 1)) / 5
        own = A / np.maximum(M[..., None], 1e-9)
        w = np.clip(M, 0, 1)[..., None]
        cur = own * w + up * (1 - w)
    out = np.where(valid[..., None], a, cur)
    return out[..., 0] if squeeze else out


def save_png(path, arr, mode):
    """arr: (N, N, C) floats 0..1, rows bottom-up -> 8-bit PNG (top row first) through plain Python + PIL"""
    a = np.clip(np.flipud(arr) * 255 + 0.5, 0, 255).astype(np.uint8)
    if mode == 'L' and a.ndim == 3: a = a[..., 0]
    raw = path + '.bytes'
    with open(raw, 'wb') as fh: fh.write(np.ascontiguousarray(a).tobytes())
    code = ('import sys; from PIL import Image; w, h = int(sys.argv[3]), int(sys.argv[4]); '
            'Image.frombytes(sys.argv[5], (w, h), open(sys.argv[1], "rb").read()).save(sys.argv[2], optimize=True)')
    r = subprocess.run([PY, '-c', code, raw, path, str(a.shape[1]), str(a.shape[0]), mode], capture_output=True, text=True)
    if r.returncode: print('PNG FAILED', path, r.stderr[-400:])
    os.remove(raw)
    return path


# ---------------------------------------------------------------------------------------------- the AO masks
def ao_masks(scene_objs, group, N, ao_dist, samples=SAMPLES):
    """Cycles, over the whole gun: R = AO at the gun's reach, G = AO inside the solid at a chamfer's reach (low only
       round convex edges), B = a short AO (creases, seams). returns (N, N, 3)"""
    import artist_kit as AK
    os.environ.setdefault('JF_BAKE_DEVICE', 'CPU')
    sc = bpy.context.scene
    AK._gpu(); sc.cycles.samples = samples
    img = bpy.data.images.new('masks', N, N, float_buffer=True)
    keep = {}
    for o in group:
        keep[o.name] = list(o.data.materials)
        m = bpy.data.materials.new('bk'); m.use_nodes = True
        nt = m.node_tree; nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission')
        a1 = nt.nodes.new('ShaderNodeAmbientOcclusion'); a1.samples = 16; a1.inputs['Distance'].default_value = ao_dist
        a2 = nt.nodes.new('ShaderNodeAmbientOcclusion'); a2.samples = 16; a2.inside = True; a2.only_local = True
        a2.inputs['Distance'].default_value = 0.0028
        a3 = nt.nodes.new('ShaderNodeAmbientOcclusion'); a3.samples = 16; a3.inputs['Distance'].default_value = 0.008
        c = nt.nodes.new('ShaderNodeCombineXYZ')
        nt.links.new(a1.outputs['AO'], c.inputs['X']); nt.links.new(a2.outputs['AO'], c.inputs['Y'])
        nt.links.new(a3.outputs['AO'], c.inputs['Z'])
        nt.links.new(c.outputs[0], em.inputs['Color']); nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
        tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img; tn.select = True; nt.nodes.active = tn
        o.data.materials.clear(); o.data.materials.append(m)
    bpy.ops.object.select_all(action='DESELECT')
    for o in group: o.select_set(True)
    bpy.context.view_layer.objects.active = group[0]
    t0 = time.time()
    bpy.ops.object.bake(type='EMIT', margin=3, margin_type='EXTEND', use_clear=True)
    print('AO MASKS %d pieces in %.0fs' % (len(group), time.time() - t0))
    a = np.empty(N * N * 4, np.float32); img.pixels.foreach_get(a)
    for o in group:
        bm_ = o.data.materials[0]
        o.data.materials.clear()
        for m in keep[o.name]: o.data.materials.append(m)
        bpy.data.materials.remove(bm_)
    bpy.data.images.remove(img)
    return a.reshape(N, N, 4)[..., :3]


def curvature(P, Nw, ok, texel):
    """mean curvature (1/m, convex > 0) from the normals' change between neighbouring texels of one surface"""
    k = np.zeros(ok.shape, np.float32); cnt = np.zeros(ok.shape, np.float32)
    for ax in (0, 1):
        P1, P0 = np.roll(P, -1, ax), np.roll(P, 1, ax)
        N1, N0 = np.roll(Nw, -1, ax), np.roll(Nw, 1, ax)
        o1, o0 = np.roll(ok, -1, ax), np.roll(ok, 1, ax)
        dP = P1 - P0; dN = N1 - N0
        l2 = np.sum(dP * dP, -1)
        both = ok & o1 & o0 & (l2 < (5 * texel) ** 2) & (l2 > 1e-14)
        kk = np.sum(dN * dP, -1) / np.maximum(l2, 1e-14)
        k += np.where(both, kk, 0); cnt += both
    return k / np.maximum(cnt, 1)


# ---------------------------------------------------------------------------------------------- PAINT
# Painted motifs and detail normals, placed in the gun's own frame (not the atlas): each item is a list of 2D shapes
# seen along one axis ("axis": "x" = a side view, coordinates [z, y]; "y" = from above, [z, x]; "z" = from the
# front, [x, y]) laid on the faces turned that way ("sides": [-1, 1]: the left and right faces, mirrored like the
# recipe's decals; "nmin": how square to that axis a face must be, default 0.35), clipped to "box" (weapon frame)
# and to pieces whose name starts with "nodes". Shapes are signed distance fields, so their edges are smooth
# (anti-aliased at the texel size) whatever the mesh under them:
#   {"poly": [[u, v], ...]}  {"circle": [u, v], "r": m}  {"ellipse": [u, v], "r": [ru, rv], "turn": deg}
#   {"line": [[u, v], ...], "w": m}  (a round-ended stroke)  {"box": [[u0, v0], [u1, v1]], "r": m}
#   {"drop": [u, v], "r": m}  (a water drop, tip up)  {"cloud": [u, v], "w": m, "h": m}
#   {"wave": [[u0, u1], v], "amp": m, "len": m, "depth": m, "phase": 0..1}   (a band whose top rolls in crests)
#   {"duck": [u, v], "s": m, "face": 1 | -1}   (a rubber duck: body, head, tail; its bill and eye in "bill"/"eye")
#   {"crown": [u, v], "s": m}
# A paint item: {"color": slot or hex, "shapes": [...], "outline": [hex, width m], "feather": texels} -> drawn in
# order over the slot colours. A relief item: {"kind": "dome" | "raised" | "groove", "h": m (height or depth),
# "shapes": [...], "w": m (the slope's width)} -> a height field whose slope bends the normals (rivets = small domes,
# piping = raised lines, panel lines = grooves).
def sd_poly(u, v, pts):
    pts = np.asarray(pts, np.float64)
    d = np.full(u.shape, np.inf); s = np.ones(u.shape)
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[i - 1]
        eu, ev = b[0] - a[0], b[1] - a[1]
        wu, wv = u - a[0], v - a[1]
        t = np.clip((wu * eu + wv * ev) / max(eu * eu + ev * ev, 1e-18), 0, 1)
        du, dv = wu - eu * t, wv - ev * t
        d = np.minimum(d, du * du + dv * dv)
        c1 = v >= a[1]; c2 = v < b[1]; c3 = eu * wv > ev * wu
        flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
        s = np.where(flip, -s, s)
    return s * np.sqrt(d)


def sd_line(u, v, pts, w):
    pts = np.asarray(pts, np.float64)
    d = np.full(u.shape, np.inf)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        eu, ev = b[0] - a[0], b[1] - a[1]
        wu, wv = u - a[0], v - a[1]
        t = np.clip((wu * eu + wv * ev) / max(eu * eu + ev * ev, 1e-18), 0, 1)
        d = np.minimum(d, np.hypot(wu - eu * t, wv - ev * t))
    return d - w / 2


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def shape_sd(u, v, s):
    """one shape's signed distance (metres; < 0 inside); composite shapes return the union of their parts"""
    if 'poly' in s: return sd_poly(u, v, s['poly'])
    if 'circle' in s: return np.hypot(u - s['circle'][0], v - s['circle'][1]) - s['r']
    if 'ellipse' in s:
        cu, cv = s['ellipse']; ru, rv = s['r']; a = math.radians(s.get('turn', 0))
        x, y = (u - cu) * math.cos(a) + (v - cv) * math.sin(a), -(u - cu) * math.sin(a) + (v - cv) * math.cos(a)
        k = np.hypot(x / ru, y / rv)
        return (k - 1) * min(ru, rv)
    if 'line' in s: return sd_line(u, v, s['line'], s['w'])
    if 'box' in s:
        (u0, v0), (u1, v1) = s['box']; r = s.get('r', 0.0)
        cu, cv, hu, hv = (u0 + u1) / 2, (v0 + v1) / 2, abs(u1 - u0) / 2 - r, abs(v1 - v0) / 2 - r
        qx, qy = np.abs(u - cu) - hu, np.abs(v - cv) - hv
        return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
    if 'drop' in s:
        cu, cv = s['drop']; r = s['r']
        c = np.hypot(u - cu, v - cv) - r
        tip = sd_poly(u, v, [[cu - r * 0.92, cv + r * 0.38], [cu, cv + r * 2.3], [cu + r * 0.92, cv + r * 0.38]])
        return smin(c, tip, r * 0.35)
    if 'cloud' in s:
        cu, cv = s['cloud']; w, h = s['w'], s['h']
        d = shape_sd(u, v, {'box': [[cu - w / 2, cv - h / 2], [cu + w / 2, cv - h * 0.05]], 'r': h * 0.3})
        for fu, fv, fr in ((-0.28, 0.02, 0.30), (-0.02, 0.16, 0.42), (0.27, 0.06, 0.33), (0.12, -0.05, 0.3)):
            d = smin(d, np.hypot(u - (cu + fu * w), v - (cv + fv * h)) - fr * h, h * 0.12)
        return d
    if 'wave' in s:
        (u0, u1), vb = s['wave']; amp, ln, dep = s['amp'], s['len'], s.get('depth', 1.0)
        ph = s.get('phase', 0.0)
        x = (u - u0) / ln + ph
        f = x - np.floor(x)
        # one crest: a slow rise, a rounded top, a steep curling front (a toy wave, never a zig-zag)
        crest = np.where(f < 0.62, np.sin(f / 0.62 * math.pi / 2) ** 1.6, np.cos((f - 0.62) / 0.38 * math.pi / 2) ** 0.7)
        top = vb + amp * crest
        inside_u = (u >= u0) & (u <= u1)
        d = np.maximum(v - top, (vb - dep) - v)
        d = np.maximum(d, np.maximum(u0 - u, u - u1))
        return d
    if 'duck' in s:
        cu, cv = s['duck']; k = s['s']; fc = s.get('face', 1)
        part = s.get('part', 'body')
        X = lambda a: cu + fc * a * k
        if part == 'bill':
            return shape_sd(u, v, {'ellipse': [X(0.50), cv + 0.30 * k], 'r': [0.17 * k, 0.07 * k], 'turn': -8 * fc})
        if part == 'eye':
            return np.hypot(u - X(0.30), v - (cv + 0.40 * k)) - 0.045 * k
        body = shape_sd(u, v, {'ellipse': [X(-0.05), cv - 0.10 * k], 'r': [0.48 * k, 0.27 * k]})
        head = np.hypot(u - X(0.24), v - (cv + 0.32 * k)) - 0.22 * k
        tail = sd_poly(u, v, [[X(-0.38), cv - 0.02 * k], [X(-0.62), cv + 0.22 * k], [X(-0.30), cv + 0.08 * k]])
        return smin(smin(body, head, 0.10 * k), tail, 0.06 * k)
    if 'crown' in s:
        cu, cv = s['crown']; k = s['s']
        pts = [[-0.5, -0.3], [0.5, -0.3], [0.5, 0.25], [0.28, 0.02], [0.0, 0.32], [-0.28, 0.02], [-0.5, 0.25]]
        return sd_poly(u, v, [[cu + a * k, cv + b * k] for a, b in pts]) - 0.02 * k
    raise SystemExit('unknown shape %s' % list(s))


def item_sd(u, v, item):
    d = None
    for s in item['shapes']:
        e = shape_sd(u, v, s)
        d = e if d is None else (np.maximum(d, -e) if s.get('cut') else np.minimum(d, e))
    return d


AXES = {'x': (0, (2, 1)), 'y': (1, (2, 0)), 'z': (2, (0, 1))}   # axis index, (u, v) components (weapon frame)


def item_texels(item, Pw, Nw, names, pid, ok):
    """the texels an item may paint: their (u, v) and index"""
    ax, (iu, iv) = AXES[item.get('axis', 'x')]
    nmin = item.get('nmin', 0.35)
    sides = item.get('sides', [-1, 1])
    m = ok.copy()
    nz = Nw[..., ax]
    m &= (np.abs(nz) >= nmin) & np.isin(np.sign(nz), sides)
    if 'box' in item:
        lo, hi = item['box']
        for k in range(3): m &= (Pw[..., k] >= lo[k]) & (Pw[..., k] <= hi[k])
    if 'nodes' in item:
        okp = np.array([nm.startswith(tuple(item['nodes'])) for nm in names] + [False])
        m &= okp[pid]
    ii = np.flatnonzero(m.ravel())
    return ii, Pw.reshape(-1, 3)[ii, iu], Pw.reshape(-1, 3)[ii, iv]


def recipe_decal_items(rec, pal):
    """the recipe's cut-in decals as paint items (same outlines, their tags' slot colours)"""
    tagslot = {}
    for r in rec.get('regions', []):
        t = r.get('where', {}).get('tag')
        if t and r.get('slot'): tagslot[t] = r['slot']
    items = []
    for d in rec.get('decals', []):
        slot = tagslot.get(d.get('tag'))
        if not slot: continue
        it = {'color': slot, 'shapes': [{'poly': p} for p in d['polys']], 'sides': d.get('sides', [-1, 1]),
              'nmin': d.get('nmin', 0.35)}
        if 'box' in d: it['box'] = d['box']
        items.append(it)
    return items


# ---------------------------------------------------------------------------------------------- the bake
def decal_hosts(objs, sa, decal_slots, decal_items, turned):
    """the recipe's cut-in decal pieces (most of their surface inside a decal outline) -> the slot of the surface
       they were cut into (the most common slot among the pieces sharing their border points). Their texels start
       from that colour; the smooth painted outline then gives the decal its shape (no jagged mesh edge shows)"""
    if not decal_items: return {}
    R = np.diag([-1.0, -1.0, 1.0]) if turned else np.eye(3)
    key = lambda c: (round(c[0], 5), round(c[1], 5), round(c[2], 5))
    at = {}
    for o in objs:
        slot = o['jf_piece'].split('__')[1]
        for v in o.data.vertices: at.setdefault(key(v.co), set()).add(slot)
    out = {}
    for o in sa:
        slot = o['jf_piece'].split('__')[1]
        if slot not in decal_slots: continue
        co = np.array([v.co[:] for v in o.data.vertices]) @ R.T
        wf = np.stack([co[:, 0], co[:, 2], -co[:, 1]], -1)
        inside = np.zeros(len(wf), bool)
        for it in decal_items:
            if it['color'] != slot: continue
            m = np.ones(len(wf), bool)
            if 'box' in it:
                lo, hi = it['box']
                for k in range(3): m &= (wf[:, k] >= lo[k] - 1e-3) & (wf[:, k] <= hi[k] + 1e-3)
            if not m.any(): continue
            d = item_sd(wf[m, 2], wf[m, 1], it)
            inside[np.flatnonzero(m)[d < 0.0015]] = True
        if inside.mean() < 0.6: continue
        votes = {}
        for v in o.data.vertices:
            for s_ in at.get(key(v.co), ()):
                if s_ != slot and s_ not in decal_slots: votes[s_] = votes.get(s_, 0) + 1
        if votes: out[o.name] = max(votes, key=votes.get)
    print('DECAL PIECES ->', {k: v for k, v in out.items()})
    return out


def bake(cfg):
    t0 = time.time()
    spec, out = cfg['spec'], cfg['out']
    work = os.path.join(out, 'work'); os.makedirs(work, exist_ok=True)
    rec = json.load(open(cfg['recipe']))
    pal = TG.palette_of(rec)
    hi = high_surface(cfg, rec, work)
    # ---- the game mesh, untouched
    bpy.ops.wm.read_factory_settings(use_empty=True)
    objs, turned = load_game(cfg['game'])
    roles = piece_roles(objs, pal, spec)
    shells = [o for o in objs if roles[o.name] == 'shell']
    shell_tris = sum(len(p.vertices) - 2 for o in shells for p in o.data.polygons)
    objs = [o for o in objs if roles.get(o.name) != 'shell']
    for o in shells: bpy.data.objects.remove(o, do_unlink=True)
    sa = [o for o in objs if roles[o.name] == 'sa']
    groups, area = atlas_groups(sa, spec)
    import artist_kit as AK
    L = max(v.co.y for o in objs for v in o.data.vertices) - min(v.co.y for o in objs for v in o.data.vertices)
    ao_dist = max(0.02, min(0.06, 0.02 + 0.03 * L))
    kitp = tuple(spec.get('kit', []))
    decal_items = recipe_decal_items(rec, pal) if spec.get('recipe_decals') else []
    pl = spec.get('paint', [])
    if any(it.get('decals') for it in pl):
        paint_items = []
        for it in pl: paint_items += decal_items if it.get('decals') else [it]
    else: paint_items = decal_items + pl
    relief_items = spec.get('relief', [])
    # {"poly": "<tag>"} in a shape list = every outline of the recipe's decals with that tag
    tagpolys = {}
    for d_ in rec.get('decals', []): tagpolys.setdefault(d_.get('tag'), []).extend(d_['polys'])
    def resolve(it):
        sh = []
        for s_ in it.get('shapes', []):
            if isinstance(s_.get('poly'), str): sh += [{'poly': q} for q in tagpolys.get(s_['poly'], [])]
            else: sh.append(s_)
        it = dict(it); it['shapes'] = sh
        return it
    paint_items = [resolve(it) for it in paint_items]
    relief_items = [resolve(it) for it in relief_items]
    # the light slot each decal slot sits on (the node's biggest other piece): its texels start from that colour
    decal_slots = {it['color'] for it in decal_items}
    host = decal_hosts(objs, sa, decal_slots, decal_items, turned)
    info = {'key': cfg['key'], 'game': cfg['game'], 'turned': turned, 'atlases': [], 'pieces': {}, 'shells_dropped':
            sorted(o for o in roles if roles[o] == 'shell'), 'shell_tris_saved': shell_tris}
    for ai, grp in enumerate(groups):
        tag = 'A%d' % (ai + 1)
        dens, used, over = AK.atlas_uvs(grp, margin=spec.get('margin', 0.003), rotate=True)
        tex = raster(grp, turned)
        texel = 1.0 / dens
        names = [o['jf_piece'] for o in grp]
        kit_sel = [o['jf_piece'].startswith(kitp) or o['jf_piece'].split('__')[0].startswith(kitp) for o in grp]
        kit_mask = np.array(kit_sel + [False])[tex['pid']] & tex['ok']
        Nraw, hit, Phit = transfer(tex, hi, kit_mask, tuple(spec.get('wobble', [1.5, 5.0])))
        # a piece the raw surface hardly covers is a kit part after all (flat + bevels, no stray raw bits)
        for k, o in enumerate(grp):
            m = tex['inside'] & (tex['pid'] == k)
            frac = float((hit & m).sum()) / max(int(m.sum()), 1)
            if not kit_sel[k] and frac < spec.get('kit_below', 0.45): kit_sel[k] = True
            info['pieces'][o.name] = {'atlas': tag, 'raw_cover': round(frac, 3), 'kit': kit_sel[k]}
        kit_mask = np.array(kit_sel + [False])[tex['pid']] & tex['ok']
        Nbev, edge_kit = bevel_normals(tex, grp, turned, kit_sel)
        Nw = np.where(kit_mask[..., None], Nbev, np.where(hit[..., None], Nraw, tex['N']))
        Pw_b = np.where(hit[..., None], Phit, tex['P'])
        # ---- detail relief (rivets, piping, panel lines): a height field's slope bends the normals
        Pwf = np.stack([Pw_b[..., 0], Pw_b[..., 2], -Pw_b[..., 1]], -1)          # Blender -> weapon frame
        Nwf = np.stack([Nw[..., 0], Nw[..., 2], -Nw[..., 1]], -1)
        Nlf = np.stack([tex['N'][..., 0], tex['N'][..., 2], -tex['N'][..., 1]], -1)
        relief_h = np.zeros(tex['pid'].shape, np.float32)
        for it in relief_items:
            ii, u, v = item_texels(it, Pwf, Nlf, names, tex['pid'], tex['ok'])
            if not len(ii): continue
            ax, (iu, iv) = AXES[it.get('axis', 'x')]
            e = 0.25 * texel
            def hgt(uu, vv):
                d = item_sd(uu, vv, it); w = it.get('w', 0.0015)
                if it['kind'] == 'dome': x = np.clip(-d / w, 0, 1); return it['h'] * np.sqrt(1 - (1 - x) ** 2)
                x = np.clip(0.5 - d / w, 0, 1); x = x * x * (3 - 2 * x)
                return it['h'] * x * (-1 if it['kind'] == 'groove' else 1)
            h0 = hgt(u, v); du = (hgt(u + e, v) - hgt(u - e, v)) / (2 * e); dv = (hgt(u, v + e) - hgt(u, v - e)) / (2 * e)
            g = np.zeros((len(ii), 3)); g[:, iu] = du; g[:, iv] = dv
            nf = Nwf.reshape(-1, 3)[ii]
            sgn = np.sign(nf[:, ax])[:, None]
            g = g - nf * np.sum(g * nf, 1, keepdims=True)
            nn = nf - g * 1.0
            nn /= np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-9)
            Nwf.reshape(-1, 3)[ii] = nn
            relief_h.reshape(-1)[ii] += h0
        Nw = np.stack([Nwf[..., 0], -Nwf[..., 2], Nwf[..., 1]], -1)
        # ---- the masks: Cycles AO over the gun, curvature from the final normals
        M = ao_masks(objs, grp, ATLAS, ao_dist)
        ok = tex['ok']
        aol, inside_ao, crease = (blur(M[..., i], 1.0, ok) for i in range(3))
        k = curvature(Pw_b, Nw, ok, texel)
        r0 = spec.get('curv_r', 0.0015)
        convex = np.clip(k * r0, 0, 1); concave = np.clip(-k * r0, 0, 1)
        convex = np.maximum(blur(convex, 0.8, ok), 0); concave = blur(concave, 1.2, ok)
        cav_wide = blur(np.clip(-k * r0 * 0.5, 0, 1), 4.0, ok)
        edge_low = np.clip((0.86 - inside_ao) / 0.5, 0, 1) ** 1.2
        edge = np.clip(np.maximum.reduce([edge_low, convex * 1.2, edge_kit]), 0, 1)
        cav = np.clip(0.6 * concave + 0.6 * cav_wide + 0.8 * (1 - crease), 0, 1)
        # ---- the colours: slot base (decal pieces start from their host), motifs over it
        fin = {}
        base = np.zeros(tex['P'].shape, np.float32); slot_ix = np.zeros(tex['pid'].shape, np.int32)
        slots = []
        for kk, o in enumerate(grp):
            s = host.get(o.name, o['jf_piece'].split('__')[1])
            if s not in slots: slots.append(s)
            m = ok & (tex['pid'] == kk)
            base[m] = lin(pal[s]['color']) * slot_finish(s, pal[s]['color'], spec)['scale']
            slot_ix[m] = slots.index(s)
        for s in slots: fin[s] = slot_finish(s, pal[s]['color'], spec)
        col = base.copy()
        paint_slot = slot_ix.copy()
        fw = texel * 0.9
        for it in paint_items:
            ii, u, v = item_texels(it, Pwf, Nlf, names, tex['pid'], ok)
            if not len(ii): continue
            d = item_sd(u, v, it)
            if 'ring' in it:   # (a line drawn `inset` inside the shape's edge: foam on a wave's crest, piping in a border)
                inset, wid = it['ring']
                d = np.maximum(np.abs(d + inset) - wid / 2, d)
            if 'clip' in it:
                c0, c1 = it['clip']
                d = np.maximum(d, np.maximum(c0 - v, v - c1))
            cov = np.clip(0.5 - d / (fw * it.get('feather', 1.0)), 0, 1)
            c = it['color']
            if c in pal:
                rgb = lin(pal[c]['color'])
                if c not in fin: fin[c] = slot_finish(c, pal[c]['color'], spec)
                if c not in slots: slots.append(c)
                si = slots.index(c)
            else:
                rgb = lin(c); si = None
            cf = col.reshape(-1, 3)
            cf[ii] = cf[ii] * (1 - cov[:, None]) + rgb[None] * cov[:, None]
            if si is not None: paint_slot.reshape(-1)[ii[cov > 0.5]] = si
            if 'outline' in it:
                oc, ow = it['outline']
                ring = np.clip(0.5 - (np.abs(d) - ow / 2) / fw, 0, 1)
                cf[ii] = cf[ii] * (1 - ring[:, None]) + lin(oc)[None] * ring[:, None]
        # ---- shading over the paint (linear): AO, cavity, a soft top-down light, a gun-wide height gradient
        upw = Nwf[..., 1]
        ylo, yhi = Pwf[..., 1][ok].min(), Pwf[..., 1][ok].max()
        hfrac = np.clip((Pwf[..., 1] - ylo) / max(yhi - ylo, 1e-6), 0, 1)
        tint = np.stack([np.array(fin[slots[i]]['tint'], np.float32) for i in range(len(slots))])[paint_slot]
        cavk = np.array([fin[s]['cav'] for s in slots], np.float32)[paint_slot]
        linesk = np.array([fin[s]['lines'] for s in slots], np.float32)[paint_slot]
        edgek = np.array([fin[s]['edge'] for s in slots], np.float32)[paint_slot]
        lift = np.stack([np.array(fin[slots[i]]['lift'], np.float32) for i in range(len(slots))])[paint_slot]
        metal = np.array([fin[s]['metal'] for s in slots], np.float32)[paint_slot]
        rough = np.array([fin[s]['rough'] for s in slots], np.float32)[paint_slot]
        gold = np.array([1.0 if fin[s]['gold'] else 0.0 for s in slots], np.float32)[paint_slot]
        # (a calm hand on busy little islands: brake ports, spokes, ribs packed small read as a grid of lines, so
        # islands under 8000 texels get half the cavity and edge lines)
        isl_ = tex['isl']
        cnt_ = np.bincount(isl_[tex['inside'] & (isl_ >= 0)].ravel(), minlength=isl_.max() + 2)
        calm = np.where(ok & (isl_ >= 0), np.where(cnt_[np.maximum(isl_, 0)] < 8000, 0.5, 1.0), 1.0).astype(np.float32)
        cav = cav * calm; edge = edge * calm; concave = concave * calm
        occ = (1 - 0.42 * (1 - aol)) * (1 - cavk * cav) * (1 - linesk * np.clip(concave * 1.6, 0, 1))
        light = (1.0 + 0.05 * upw - 0.03) * (1 + 0.05 * (hfrac - 0.5))
        light = light * (1 + gold * (0.10 * upw - 0.02))            # (gold: a bright top, a dark underside, like a metal)
        d = 1 - np.clip(occ, 0.45, 1.0)[..., None]
        shaded = col * (1 - d + d * tint) * light[..., None]
        srgb = srgb_np(shaded)
        e = (edge * edgek)[..., None]
        srgb = srgb + (lift - srgb) * np.clip(e, 0, 1) * 0.55
        srgb = np.clip(srgb, 0, 1)
        nt = to_tangent(Nw, tex['N'], tex['T'], tex['S'])
        nt = np.where(ok[..., None], nt, np.array([0, 0, 1.0]))
        # clean-up: a 3x3 median on the raw-surface texels (stray hits and crease speckles out), at most 55 deg of turn
        stack = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                sh_ = np.roll(nt, (dy, dx), axis=(0, 1)); okn = np.roll(hit & ok, (dy, dx), axis=(0, 1))
                stack.append(np.where(okn[..., None], sh_, np.nan))
        med = np.nanmedian(np.stack(stack), axis=0)
        use = hit & ok & ~np.isnan(med[..., 0])
        nt = np.where(use[..., None], med, nt)
        zmin = math.cos(math.radians(55))
        low = nt[..., 2] < zmin
        xy = nt[..., :2] / np.maximum(np.linalg.norm(nt[..., :2], axis=-1, keepdims=True), 1e-9) * math.sqrt(1 - zmin * zmin)
        nt = np.where(low[..., None], np.concatenate([xy, np.full(low.shape + (1,), zmin)], -1), nt)
        nt /= np.maximum(np.linalg.norm(nt, axis=-1, keepdims=True), 1e-9)
        # GLYPH GUARD: small islands (chamfer strips, little faces packed in rows) are evened out to their own mean
        # colour and a nearly flat normal, so no row of them reads like writing or a barcode in the picture
        isl = tex['isl']
        cnt = np.bincount(isl[tex['inside'] & (isl >= 0)].ravel(), minlength=isl.max() + 2)
        small = np.zeros(len(cnt) + 1, bool); small[:len(cnt)] = cnt < spec.get('small_px', 1500)
        # (and thin ones: chamfer strips packed side by side read as bars; mean thickness under 9 texels)
        ii_ = tex['inside'] & (isl >= 0)
        ys_, xs_ = np.nonzero(ii_); ids_ = isl[ii_]
        x0 = np.full(len(cnt), 10 ** 6); x1 = np.full(len(cnt), -1); y0 = np.full(len(cnt), 10 ** 6); y1 = np.full(len(cnt), -1)
        np.minimum.at(x0, ids_, xs_); np.maximum.at(x1, ids_, xs_); np.minimum.at(y0, ids_, ys_); np.maximum.at(y1, ids_, ys_)
        span = np.maximum(np.maximum(x1 - x0, y1 - y0) + 1, 1)
        small[:len(cnt)] |= (cnt > 0) & (cnt / span < spec.get('thin_px', 9))
        sm = ok & (isl >= 0) & small[np.maximum(isl, 0)]
        if sm.any():
            for ch in range(3):
                mean = np.bincount(isl[sm], weights=srgb[..., ch][sm], minlength=len(cnt)) / np.maximum(np.bincount(isl[sm], minlength=len(cnt)), 1)
                srgb[..., ch][sm] = 0.7 * mean[isl[sm]] + 0.3 * srgb[..., ch][sm]
            nt[sm] = nt[sm] * 0.35 + np.array([0, 0, 1.0]) * 0.65
            nt /= np.maximum(np.linalg.norm(nt, axis=-1, keepdims=True), 1e-9)
        rough_m = np.clip(blur(rough + 0.08 * cav_wide, 1.5, ok), 0.05, 1)   # (no line work in the roughness)
        # ---- fill the gaps, write
        enc_n = nt * 0.5 + 0.5
        maps = {'color': pushpull(srgb, ok), 'normal': pushpull(enc_n, ok), 'metal': pushpull(metal, ok),
                'rough': pushpull(rough_m, ok)}
        # (the glyph guard, second half: round the small islands, 4 texels out, every map is blurred into soft blobs,
        # so a packed row of little islands never shows outlines that could read as letters or bars)
        if sm.any():
            zone = sm.copy()
            for _ in range(4):
                zone = zone | np.roll(zone, 1, 0) | np.roll(zone, -1, 0) | np.roll(zone, 1, 1) | np.roll(zone, -1, 1)
            zone &= ~(ok & ~sm)   # (never over a big island's own texels)
            for nm in maps:
                bl = blur(maps[nm], 2.5)
                maps[nm] = np.where(zone[..., None] if maps[nm].ndim == 3 else zone, bl, maps[nm])
        paths = {}
        for nm, arr in maps.items():
            if nm == 'normal':
                n3 = arr * 2 - 1; n3 /= np.maximum(np.linalg.norm(n3, axis=-1, keepdims=True), 1e-9); arr = n3 * 0.5 + 0.5
            mode = 'RGB' if arr.ndim == 3 else 'L'
            paths[nm] = save_png(os.path.join(out, '%s_%s_%s.png' % (cfg['K'], tag, nm)), arr, mode)
        used_metal = bool(metal[ok].max() > 0.01)
        info['atlases'].append({'tag': tag, 'pieces': [o.name for o in grp], 'texels_per_m': round(dens, 1),
                                'atlas_used': round(used, 3), 'uv_overlap': round(over, 4), 'maps': paths,
                                'raw_hit': round(float(hit[tex['inside']].mean()), 3), 'metal_used': used_metal})
        for o in grp: o['jf_atlas'] = tag
        print('ATLAS %s: %d pieces, %.0f texels/m, %.0f%% used, overlap %.2f%%' % (tag, len(grp), dens, used * 100, over * 100))
    # ---- the files
    up = export_upload(cfg, objs, turned, pal, info)
    preview_glb(cfg, up, info)
    info['install_luau'] = install_luau(cfg, info)
    info['seconds'] = round(time.time() - t0)
    with open(os.path.join(out, 'bake.json'), 'w') as fh: json.dump(info, fh, indent=1)
    print('BAKE DONE %s in %ds -> %s' % (cfg['key'], info['seconds'], out))
    return info


def export_upload(cfg, objs, turned, pal, info):
    """the upload file: every piece as the game had it (names, vertices, normals), the pictured ones on their atlas
       UVs, tangents written; no picture inside (the maps go up as Images for the SurfaceAppearances). A kit-frame
       game file is turned (rbxglb.PRE_TURN) and named "<node>__<slot>__<look>" as export_weapons.py would"""
    import rbxglb
    out = cfg['out']
    for o in list(bpy.context.scene.objects):
        if o.type != 'MESH': bpy.data.objects.remove(o, do_unlink=True)
    pieces = []
    rename = {}
    for o in objs:
        node, slot = o['jf_piece'].split('__')
        old = o.name
        if 'jf_up' not in o:
            p = pal.get(slot, {'color': '808080', 'kind': 'p', 'alpha': 1.0})
            look = {'color': p['color'], 'glow': 2.0 if p['kind'] == 'n' else 0.0, 'alpha': p.get('alpha', 1.0) if p['kind'] == 'g' else 1.0,
                    'metal': 0.0, 'rough': 0.75}
            o['jf_up'] = '%s__%s__%s' % (node, slot, rbxglb.look_code(look))
        o.name = o['jf_up']; o.data.name = o['jf_up']
        rename[old] = o.name
        # (a pictured piece's only UV layer is its atlas; the others keep the game's own unfold)
    # (the piece table and the atlases by the names the upload carries)
    info['pieces'] = {rename.get(k, k): v for k, v in info['pieces'].items()}
    for a in info['atlases']: a['pieces'] = [rename.get(k, k) for k in a['pieces']]
    if not turned: rbxglb.turn_for_roblox(objs)
    path = os.path.join(out, cfg['K'] + '_up.glb')
    rbxglb.export_glb(path, tangents=True)
    lo, hi = [1e9] * 3, [-1e9] * 3
    for o in objs:
        for v in o.data.vertices:
            w = (-v.co.x, v.co.z, v.co.y)   # (the turned file's Blender frame -> the weapon file frame, un-turned)
            for i in range(3): lo[i] = min(lo[i], w[i]); hi[i] = max(hi[i], w[i])
        code = o.name.split('__')[2]
        pieces.append({'upload': o.name, 'tris': sum(len(p.vertices) - 2 for p in o.data.polygons),
                       'sa': o.get('jf_atlas'), 'paint': code})
    info['upload'] = path
    info['lo'] = [round(x, 4) for x in lo]; info['hi'] = [round(x, 4) for x in hi]
    # export_weapons.py's report row (weapon_paint.write_kit reads it: lo / hi -> FileLo / FileHi, the paint codes).
    # uv = false: W.kit then leaves WrapUV off every piece (a wrap picture must not land on the bake's atlas UVs)
    def look_of(code):
        k, hx = code[0], code[1:7]
        return {'color': hx, 'metal': 0.0, 'rough': 0.75, 'glow': 2.0 if k == 'n' else 0.0,
                'alpha': int(code[7:9], 16) / 255 if k == 'g' and len(code) >= 9 else 1.0, 'tex': False, **({'glowColor': hx} if k == 'n' else {})}
    row = {'pieces': [{'name': '__'.join(q['upload'].split('__')[:2]), 'upload': q['upload'], 'tris': q['tris'],
                       'look': look_of(q['paint']), 'paint': q['paint'], 'sa': q['sa']} for q in pieces],
           'tris': sum(q['tris'] for q in pieces), 'lo': info['lo'], 'hi': info['hi'], 'bytes': os.path.getsize(path),
           'turned': True, 'meta': {'kind': 'weapon', 'id': cfg['key'], 'set': 'kit', 'lo': info['lo'], 'hi': info['hi'],
                                    'spots': cfg.get('spots'), 'baked': 'surface_appearance'}, 'nodes': {}, 'uv': False, 'paint': 'kit'}
    with open(os.path.join(out, 'export_report.json'), 'w') as fh: json.dump({cfg['K']: row}, fh, indent=1)
    info['tris'] = sum(p['tris'] for p in pieces)
    info['upload_pieces'] = pieces
    print('UPLOAD %s: %d tris, lo %s hi %s' % (path, info['tris'], info['lo'], info['hi']))
    return path


def install_luau(cfg, info, where='game.ServerStorage.PolishBackup.WeaponSets.kit'):
    """the Edit-mode Luau that puts the maps on (Studio's execute_luau, after W.kit loaded the upload; maps are
       PluginSecurity, so Edit only): fill IDS with the uploaded Image ids first. Every pictured piece gets one
       SurfaceAppearance (Overlay, opaque maps, no tint), its TextureID cleared and WrapUV off; the rest is untouched"""
    rows = ['-- %s: SurfaceAppearances from tools/roblox/tripo_bake.py (Edit mode only; fill IDS first)' % cfg['K'],
            'local IDS = {']
    for a in info['atlases']:
        rows.append('	%s = { color = "rbxassetid://0", normal = "rbxassetid://0", metal = "rbxassetid://0", rough = "rbxassetid://0" },' % a['tag'])
    rows += ['}', 'local PIECES = { -- "<node>__<slot>" -> atlas']
    for name, v in sorted(info['pieces'].items()):
        rows.append('	["%s"] = "%s",' % ('__'.join(name.split('__')[:2]), v['atlas']))
    rows += ['}',
             'local m = %s:FindFirstChild("%s")' % (where, cfg['K']),
             'if not m then return "%s: NOT LOADED (W.kit first)" end' % cfg['K'],
             'local n, missing = 0, {}',
             'for _, d in m:GetDescendants() do',
             '	if not d:IsA("MeshPart") then continue end',
             '	local node, slot = string.match(d.Name, "^(.-)__(%w+)")',
             '	local a = node and PIECES[node .. "__" .. slot]',
             '	if not a then continue end',
             '	local id = IDS[a]',
             '	if id.color == "rbxassetid://0" then table.insert(missing, a); continue end',
             '	local sa = d:FindFirstChildOfClass("SurfaceAppearance") or Instance.new("SurfaceAppearance")',
             '	sa.ColorMap = id.color; sa.NormalMap = id.normal; sa.MetalnessMap = id.metal; sa.RoughnessMap = id.rough',
             '	sa.AlphaMode = Enum.AlphaMode.Overlay; sa.Color = Color3.new(1, 1, 1)',
             '	sa.Parent = d',
             '	d.TextureID = ""; d.Material = Enum.Material.SmoothPlastic',
             '	d:SetAttribute("WrapUV", nil) -- (its UVs are the bake atlas: a wrap picture would land 2-4x too big, seamed)',
             '	n += 1',
             'end',
             'return ("%s: %d pieces wear their maps%s"):format(m.Name, n, if #missing > 0 then " (no ids yet for " .. table.concat(missing, ", ") .. ")" else "")',
             '']
    path = os.path.join(cfg['out'], cfg['K'] + '_install.luau')
    with open(path, 'w', newline=chr(10)) as fh: fh.write(chr(10).join(rows))
    return path


def sa_material(name, maps, dark=False):
    """a Blender material wearing one atlas's maps the way Roblox's SurfaceAppearance does"""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    def img(p, cs):
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(p, check_existing=True)
        t.image.colorspace_settings.name = cs; return t
    c = img(maps['color'], 'sRGB'); nt.links.new(c.outputs['Color'], b.inputs['Base Color'])
    n = img(maps['normal'], 'Non-Color'); nm = nt.nodes.new('ShaderNodeNormalMap'); nm.uv_map = 'UVMap'
    nt.links.new(n.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    r = img(maps['rough'], 'Non-Color'); nt.links.new(r.outputs['Color'], b.inputs['Roughness'])
    mt = img(maps['metal'], 'Non-Color'); nt.links.new(mt.outputs['Color'], b.inputs['Metallic'])
    return m


def preview_glb(cfg, up, info):
    """K_preview.glb: the upload file with the maps on (to look at in any glTF viewer; never uploaded)"""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=up)
    mats = {a['tag']: sa_material('sa_' + a['tag'], a['maps']) for a in info['atlases']}
    for o in bpy.context.scene.objects:
        if o.type != 'MESH': continue
        a = info['pieces'].get(o.name.split('.')[0], {}).get('atlas')
        if a: o.data.materials.clear(); o.data.materials.append(mats[a])
    bpy.ops.export_scene.gltf(filepath=os.path.join(cfg['out'], cfg['K'] + '_preview.glb'), export_format='GLB',
                              use_selection=False, export_yup=True, export_tangents=True)


def wear_maps(objs, info):
    """in a render scene: every pictured piece of an imported upload file wears its atlas's maps; glow glows"""
    mats = {a['tag']: sa_material('sa_' + a['tag'], a['maps']) for a in info['atlases']}
    for o in objs:
        a = info['pieces'].get(o.name.split('.')[0], {}).get('atlas')
        if a: o.data.materials.clear(); o.data.materials.append(mats[a])
    plastic([o for o in objs if not info['pieces'].get(o.name.split('.')[0], {}).get('atlas')])


# ================================================================================================ SHEET: before / after
def raw_glb_cfg(cfg):
    """the gun's raw Tripo model fitted into the kit frame (whole, as the owner made it), smooth shaded"""
    path = os.path.join(cfg['out'], 'work', '_rawfit.glb')
    if os.path.exists(path): return path
    rec = json.load(open(cfg['recipe'])); cj = json.load(open(cfg['clean']))
    s, t, R, _ = TG.solve_fit(rec, cj['spots'])
    bm = TG.load_raw(cfg['raw']); TG.fit_bmesh(bm, s, t, R)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=rec.get('weld', 1e-4) * s)
    for f in bm.faces: f.smooth = True
    o = TG._bm_obj(bm, 'raw'); bm.free()
    o.data.materials.append(bpy.data.materials.new('clay'))
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=False, export_yup=True)
    return path


def put(cfg, info, col, at=None):
    """one column's gun into the current scene (kit Blender frame, then `at`): raw | now | new"""
    A = at if at is not None else Matrix.Identity(4)
    if col == 'raw':
        objs = [o for o in TG._import(raw_glb_cfg(cfg), A) if o.type == 'MESH']; clay(objs)
    elif col == 'now':
        p = cfg['now']
        objs = [o for o in TG._import(p, A @ (TURN if is_upload(p) else Matrix.Identity(4))) if o.type == 'MESH']
        plastic(objs)
    else:
        objs = [o for o in TG._import(info['upload'], A @ TURN) if o.type == 'MESH']
        wear_maps(objs, info)
    bpy.context.view_layer.update()
    return objs


def gun_sheet(cfg, path, title=None):
    global GUN_LO, GUN_HI
    info = json.load(open(os.path.join(cfg['out'], 'bake.json')))
    rec = json.load(open(cfg['recipe']))
    spec = cfg['spec']
    GUN_LO, GUN_HI = Vector(info['lo']), Vector(info['hi'])
    cols = spec.get('sheet_cols', ['concept', 'now', 'new'] if os.path.exists(os.path.join(cfg['dir'], 'concept.png')) else ['raw', 'now', 'new'])
    names = {'concept': "owner's concept", 'raw': "owner's raw Tripo (clay)", 'now': 'NOW in the game (flat colours + shade shells)',
             'new': 'NEW: SurfaceAppearance maps (same mesh)'}
    pdir = os.path.join(cfg['out'], 'work', 'sheet'); os.makedirs(pdir, exist_ok=True)
    shots = [{'name': 'side', 'label': 'left side', 'at': None, 'dir': (-1, 0, 0), 'size': 'L'}, {'name': 'q34', 'label': '3/4', 'q34': True}]
    shots += spec.get('shots', [])
    rows, cells = [], []
    for sh in shots:
        row = []
        for c in cols:
            if c == 'concept':
                row.append(os.path.join(cfg['dir'], 'concept.png') if sh['name'] == 'q34' else None); continue
            out = os.path.join(pdir, '%s_%s.png' % (sh['name'], c))
            sc = stage(800, 500, 32); put(cfg, info, c); lights(sc); shoot(sc, sh, out)
            row.append(out)
        rows.append(sh['label']); cells.append(row)
    # in hand (first person, no arms) and the aim view (the ADS hide list off)
    row = []
    for c in cols:
        if c == 'concept': row.append(None); continue
        out = os.path.join(pdir, 'hand_%s.png' % c)
        sc = stage(800, 500, 32); put(cfg, info, c, TG.hold_matrix(cfg['base'])); lights(sc, (35, 0, 20))
        TG._cam(sc, (0, 0, 0), (0, 1, 0), fov=70); TG._render(out, crop=True)
        row.append(out)
    rows.append('in hand'); cells.append(row)
    sp = (cfg.get('spots') or {}).get('sight')
    if sp:
        try:
            hj = json.load(open(os.path.join(HERE, 'holds.json')))
            back = 0.17 + float(hj.get(cfg['base'], {}).get('ads', {}).get('aimZ', -0.06))
        except Exception: back = 0.11
        hide = tuple((rec.get('sheet') or {}).get('aim_hide', []))
        eye = TG.B((0, sp[1], sp[2] + back))
        row = []
        for c in cols:
            if c in ('concept', 'raw'): row.append(None); continue
            out = os.path.join(pdir, 'aim_%s.png' % c)
            sc = stage(800, 500, 32); objs = put(cfg, info, c)
            for o in objs:
                if hide and o.name.startswith(hide): o.hide_render = True
            lights(sc, (35, 0, 20)); TG._cam(sc, eye, eye + TG.B((0, 0, -1)), fov=70 / 1.5); TG._render(out)
            row.append(out)
        rows.append('aim view' + (' (%s hidden)' % ', '.join(hide) if hide else '')); cells.append(row)
    a = info['atlases']
    bpy.ops.wm.read_factory_settings(use_empty=True)
    now_tris = sum(len(p.vertices) - 2 for o in put(cfg, info, 'now') for p in o.data.polygons)
    notes = ['%d tris (the game now: %d with shade shells, %d saved), %d atlas%s of 1024: %s; bounds lo %s hi %s' % (
        info['tris'], now_tris, now_tris - info['tris'], len(a), '' if len(a) == 1 else 'es',
        ', '.join('%s %d texels/m' % (x['tag'], x['texels_per_m']) for x in a), info['lo'], info['hi'])] + spec.get('notes', [])
    grid(path, title or ('%s: surface detail baked into SurfaceAppearance maps (same mesh, same names)' % cfg['key']),
         [names[c] for c in cols], rows, cells, notes, cw=640, ch=400, lw=150)
    return path


# ================================================================================================ the command line
def main(argv):
    def opt(name, d=None):
        if name in argv:
            i = argv.index(name); return argv[i + 1]
        return d
    global OUT
    cmd = argv[0] if argv else 'diag'
    if cmd == 'diag':   # (the angel rifle's diagnosis: raw / v2 / v5 / v6)
        OUT = opt('--out', OUT); os.makedirs(os.path.join(OUT, 'work'), exist_ok=True)
        info, cells = diag(OUT, None)
        diag_sheet(info, cells, opt('--sheet', os.path.join(NOTES, 'angel-detail-diagnosis.jpg')))
        return
    cfg = gun_cfg(argv[1], opt('--spec'), opt('--game'), opt('--out'))
    OUT = cfg['out']; os.makedirs(os.path.join(OUT, 'work'), exist_ok=True)
    if cmd == 'bake':      # bake <key> [--spec <json>] [--game <glb>] [--out <dir>]
        bake(cfg)
    elif cmd == 'luau':    # luau <key>: the install Luau again from bake.json
        print('WROTE', install_luau(cfg, json.load(open(os.path.join(OUT, 'bake.json')))))
    elif cmd == 'sheet':   # sheet <key> [--sheet <jpg>] [--title <text>]
        gun_sheet(cfg, opt('--sheet', os.path.join(OUT, cfg['K'] + '_rich.jpg')), opt('--title'))


if __name__ == '__main__':
    main(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
