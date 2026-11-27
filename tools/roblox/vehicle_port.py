# The web game's own vehicles (public/models/p_*.glb) brought into the Roblox kits (27 Nov 2026; the owner: "Can the
# vehicles on all maps be made a bit better?", main: the web models are the bar). A web vehicle is a modelled mesh with
# pixel-art texture atlases (liveries, plates, slogans) multiplied by vertex colours (baked AO, paint). Roblox gets none
# of that well (uploads drop material colours; the owner's look is flat colours; NO lettering may go up:
# roblox-upload-content-rules), so each face is given ONE flat colour:
#   1. the face's colour is sampled from its texture (an average over the face, not one texel, so a plate or a slogan
#      averages to its panel colour and no letter survives) or read from its vertex colours;
#   2. it is snapped to a small hand-picked muted palette per vehicle (`rules`, per web material), or set outright;
#   3. the faces are piled by (kind, colour) and handed to arenakit.put, so the map's own flush() names them
#      "<model><n>__<kind>_<hex>" and WebArena paints them from their names, like every other kit piece.
# The vehicle's own frame (Roblox studs): length along Z, FRONT +Z, up +Y, the footprint's middle at x = z = 0, the
# lowest point at y = 0. port() returns pieces in that frame; place() scales and turns them onto a spot.
# Use (inside a map's headless Blender script, after `from arenakit import *`):
#   import vehicle_port as VP
#   car = VP.port('p_car_sedan', VP.SEDAN_RULES(body='8a5b45'))
#   VP.place('fo_road', car, VP.fit(car, (x0, y0, z0, x1, y1, z1), yaw=math.pi / 2))
import bpy, bmesh, math, os, sys
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import arenakit as K

MODELS = os.path.normpath(os.path.join(HERE, '..', '..', 'public', 'models'))
S = 3.0                                                     # studs per metre
# Blender (x, y, z) after the glTF import -> the vehicle frame. The web's three.js models face +z (front) with y up,
# which the importer turns into Blender (x, -z, y): so Blender -Y is the front. Vehicle frame = Roblox axes:
# x right... (x, y, z)_veh = (x_b, z_b, -y_b) * S  (front at +Z)
TO_VEH = Matrix(((S, 0, 0, 0), (0, 0, S, 0), (0, -S, 0, 0), (0, 0, 0, 1)))


def _hex_rgb(h): return tuple(int(h[j:j + 2], 16) / 255 for j in (0, 2, 4))
def _rgb_hex(c): return ''.join('%02x' % max(0, min(255, round(v * 255))) for v in c)
def lum(c): return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


class Tex:
    """an image's pixels as rows of sRGB floats, sampled with wrap"""
    def __init__(self, im):
        self.w, self.h = im.size
        px = list(im.pixels)
        ch = im.channels
        self.px = [(px[i], px[i + 1], px[i + 2]) for i in range(0, len(px), ch)]
    def at(self, u, v):
        x = int((u % 1.0) * self.w) % self.w
        y = int((v % 1.0) * self.h) % self.h
        return self.px[y * self.w + x]


def _mat_tex(m):
    """the image feeding the material's base colour (through its MULTIPLY mix), and whether vertex colours multiply in"""
    if not m or not m.use_nodes: return None, False
    tex, vc = None, False
    for l in m.node_tree.links:
        n = l.from_node
        if l.to_node.type == 'MIX' or l.to_node.type == 'BSDF_PRINCIPLED':
            if n.type == 'TEX_IMAGE' and n.image and l.to_socket.name in ('A', 'B', 'Base Color', 'Color1', 'Color2'):
                if tex is None: tex = n.image
            if n.type in ('ATTRIBUTE', 'VERTEX_COLOR'): vc = True
    return tex, vc


# barycentric sample points over a triangle (an even spread: the corners pulled in, the middle)
BARY = [(1 / 3, 1 / 3, 1 / 3)] + [(a, b, 1 - a - b) for (a, b) in
        ((0.7, 0.15), (0.15, 0.7), (0.15, 0.15), (0.45, 0.45), (0.45, 0.1), (0.1, 0.45), (0.55, 0.3), (0.3, 0.55), (0.3, 0.15), (0.15, 0.3))]


def load(name, part='lod0'):
    """import public/models/<name>.glb and return its mesh objects (LOD0: anything not under a 'lod1' empty;
       part='lod1': only those). The scene keeps them until free() is called."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, name + '.glb'))
    new = [o for o in bpy.data.objects if o not in before]
    def under_lod1(o):
        p = o.parent
        while p:
            if p.name.startswith('lod1'): return True
            p = p.parent
        return o.name.endswith('_lod1') or o.name.startswith('lod1')
    meshes = [o for o in new if o.type == 'MESH' and (under_lod1(o) == (part == 'lod1'))]
    return new, meshes


def free(objs):
    for o in objs:
        try: bpy.data.objects.remove(o, do_unlink=True)
        except Exception: pass


def faces(meshes):
    """every triangle of the meshes in the vehicle frame: (verts[3] as Vector, material name, sampled sRGB colour,
       vertex colour sRGB, object name, normal)"""
    out = []
    texes = {}
    for o in meshes:
        dg = bpy.context.evaluated_depsgraph_get()
        me = o.evaluated_get(dg).to_mesh()
        M = TO_VEH @ o.matrix_world
        me.calc_loop_triangles()
        uv = me.uv_layers.active.data if me.uv_layers.active else None
        vcl = me.color_attributes.get('Color')
        vdom = vcl.domain if vcl else None
        for t in me.loop_triangles:
            m = me.materials[t.material_index] if me.materials else None
            mname = m.name if m else ''
            if m not in texes:
                im, vc = _mat_tex(m)
                texes[m] = (Tex(im) if im else None, vc)
            tex, use_vc = texes[m]
            vs = [M @ me.vertices[i].co for i in t.vertices]
            col = None
            if tex and uv:
                uvs = [uv[l].uv for l in t.loops]
                acc = [0.0, 0.0, 0.0]
                for (a, b, c) in BARY:
                    u = a * uvs[0][0] + b * uvs[1][0] + c * uvs[2][0]
                    v = a * uvs[0][1] + b * uvs[1][1] + c * uvs[2][1]
                    p = tex.at(u, v)
                    acc[0] += p[0]; acc[1] += p[1]; acc[2] += p[2]
                col = tuple(x / len(BARY) for x in acc)
            vcol = None
            if vcl:
                acc = [0.0, 0.0, 0.0]
                if vdom == 'CORNER':
                    for l in t.loops:
                        c = vcl.data[l].color_srgb; acc[0] += c[0]; acc[1] += c[1]; acc[2] += c[2]
                else:
                    for i in t.vertices:
                        c = vcl.data[i].color_srgb; acc[0] += c[0]; acc[1] += c[1]; acc[2] += c[2]
                vcol = tuple(x / 3 for x in acc)
            n = (vs[1] - vs[0]).cross(vs[2] - vs[0])
            n = n.normalized() if n.length > 1e-12 else Vector((0, 1, 0))
            out.append({'v': vs, 'mat': mname, 'tex': col, 'vc': vcol, 'obj': o.name, 'n': n})
        o.evaluated_get(dg).to_mesh_clear()
    return out


def ground(tris):
    """move the triangles so the footprint's middle is at x = z = 0 and the lowest point at y = 0"""
    lo = [min(v[i] for t in tris for v in t['v']) for i in range(3)]
    hi = [max(v[i] for t in tris for v in t['v']) for i in range(3)]
    d = Vector(((lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2))
    for t in tris: t['v'] = [v - d for v in t['v']]
    return tris


def bounds(tris):
    lo = [min(v[i] for t in tris for v in t['v']) for i in range(3)]
    hi = [max(v[i] for t in tris for v in t['v']) for i in range(3)]
    return lo, hi


def snap(c, palette):
    """the palette entry (src_hex, kind, out_hex) whose source colour is nearest c (a weighted RGB distance)"""
    best, bd = None, 1e9
    for e in palette:
        s = _hex_rgb(e[0])
        rm = (c[0] + s[0]) / 2
        d = (2 + rm) * (c[0] - s[0]) ** 2 + 4 * (c[1] - s[1]) ** 2 + (3 - rm) * (c[2] - s[2]) ** 2
        if d < bd: bd, best = d, e
    return best


def colour(tris, rules, default=('plastic', '9a9a9a')):
    """give every triangle t['look'] = (kind, hex). rules: {material name: rule}; a rule is
         ('kind', 'hex')                         one colour for the whole material
         [(src_hex, kind, out_hex), ...]         snap the sampled colour (texture, else vertex colour) to the nearest src
         callable(t) -> (kind, hex) | None       anything else (None falls through to the material's next rule)
       a rule may also be a list of rules tried in order (callables first, then a palette)."""
    def steps(r):
        if r is None: return []
        if isinstance(r, tuple) and len(r) == 2: return [r]                       # a fixed look
        if callable(r): return [r]
        if isinstance(r, list) and r and isinstance(r[0], tuple) and len(r[0]) == 3: return [r]   # one palette
        if isinstance(r, list): return [s for x in r for s in steps(x)]           # several, in order
        return []
    plan = {}
    for t in tris:
        key = t['mat'] if t['mat'] in rules else '*'
        if key not in plan: plan[key] = steps(rules.get(key))
        look = None
        for st in plan[key]:
            if isinstance(st, tuple): look = st; break
            if callable(st):
                look = st(t)
                if look: break
                continue
            c = t['tex'] or t['vc'] or (0.6, 0.6, 0.6)
            e = snap(c, st)
            look = (e[1], e[2]); break
        t['look'] = look or default
    return tris


def report(tris):
    """area per final look, and per material the sampled colours seen (to tune a palette)"""
    area = {}
    for t in tris:
        a = (t['v'][1] - t['v'][0]).cross(t['v'][2] - t['v'][0]).length / 2
        area[t['look']] = area.get(t['look'], 0) + a
    for k, a in sorted(area.items(), key=lambda kv: -kv[1]): print('   LOOK %-8s %s  %.2f sq studs' % (k[0], k[1], a))


def sampled(tris, mat):
    """a histogram of the sampled colours of one material, rounded to 1/8 steps: [(hex, area)]"""
    h = {}
    for t in tris:
        if t['mat'] != mat: continue
        c = t['tex'] or t['vc']
        if not c: continue
        k = _rgb_hex(tuple(round(x * 8) / 8 for x in c))
        a = (t['v'][1] - t['v'][0]).cross(t['v'][2] - t['v'][0]).length / 2
        h[k] = h.get(k, 0) + a
    return sorted(h.items(), key=lambda kv: -kv[1])


def port(name, rules, part='lod0', keep=None, report_=False):
    """a web vehicle as triangles with looks, in the vehicle frame (grounded). keep(obj_name) -> bool filters objects"""
    objs, meshes = load(name, part)
    if keep: meshes = [o for o in meshes if keep(o.name)]
    tris = ground(faces(meshes))
    free(objs)
    colour(tris, rules)
    if report_:
        print('PORT', name, len(tris), 'triangles; bounds', bounds(tris)); report(tris)
    return tris


def split(tris, pred):
    """(those where pred(t), the rest)"""
    a, b = [], []
    for t in tris: (a if pred(t) else b).append(t)
    return a, b


def transform(tris, M):
    """new triangles moved by M (a 4x4 in the vehicle frame)"""
    out = []
    for t in tris:
        u = dict(t); u['v'] = [M @ v for v in t['v']]
        out.append(u)
    return out


def turn(tris, yaw):
    """turned about +Y by yaw and grounded again (a web model built along X: turn(tris, -pi / 2) puts its +X at +Z)"""
    return ground(transform(tris, Matrix.Rotation(yaw, 4, 'Y')))


def hinge(tris, p, axis, angle):
    """turn triangles about the line through p along axis (vehicle frame) by angle radians"""
    R = Matrix.Translation(p) @ Matrix.Rotation(angle, 4, Vector(axis).normalized()) @ Matrix.Translation(-Vector(p))
    return transform(tris, R)


def clip(tris, p, n):
    """cut every triangle crossing the plane through p with normal n into pieces on either side (so a later split by
       centroid follows the plane exactly: a bonnet or a door cut out of one shell)"""
    p, n = Vector(p), Vector(n).normalized()
    out = []
    for t in tris:
        d = [(v - p).dot(n) for v in t['v']]
        if all(x >= -1e-6 for x in d) or all(x <= 1e-6 for x in d):
            out.append(t); continue
        for side in (1, -1):
            poly = []
            for i in range(3):
                a, b = t['v'][i], t['v'][(i + 1) % 3]
                da, db = d[i] * side, d[(i + 1) % 3] * side
                if da >= 0: poly.append(a)
                if (da >= 0) != (db >= 0):
                    poly.append(a.lerp(b, da / (da - db)))
            for k in range(1, len(poly) - 1):
                u = dict(t); u['v'] = [poly[0].copy(), poly[k].copy(), poly[k + 1].copy()]
                out.append(u)
    return out


def centre(t): return (t['v'][0] + t['v'][1] + t['v'][2]) / 3


def _key(v): return (round(v.x, 4), round(v.y, 4), round(v.z, 4))


def thicken(tris, d, look=None):
    """a shell piece (a cut-out bonnet or door) made solid: an inner skin d inward (along -normal, from the averaged
       vertex normals) facing the other way, and a rim along its open edges. look: the inner skin's look (default: same)"""
    vn = {}
    for t in tris:
        for v in t['v']: vn.setdefault(_key(v), Vector()); vn[_key(v)] += t['n']
    for k in vn: vn[k] = vn[k].normalized() if vn[k].length > 1e-9 else Vector((0, 1, 0))
    inner, rim, edges = [], [], {}
    for t in tris:
        u = dict(t)
        vs = [v - vn[_key(v)] * d for v in t['v']]
        u['v'] = [vs[0], vs[2], vs[1]]; u['n'] = -t['n']
        if look: u['look'] = look
        inner.append(u)
        for i in range(3):
            a, b = _key(t['v'][i]), _key(t['v'][(i + 1) % 3])
            edges[(a, b)] = (t, t['v'][i], t['v'][(i + 1) % 3])
    for (a, b), (t, va, vb) in edges.items():
        if (b, a) in edges: continue                     # an inner edge (shared the other way round)
        ia, ib = va - vn[a] * d, vb - vn[b] * d
        for q in ((va, ia, ib), (va, ib, vb)):
            u = dict(t); u['v'] = [q[0], q[1], q[2]]
            if look: u['look'] = look
            rim.append(u)
    return tris + inner + rim


def box(x0, y0, z0, x1, y1, z1, look, inward=False, skip=()):
    """a plain box as triangles (inward: its faces look inside, a room seen through an opening). skip: faces left
       out, by name ('-x', '+x', '-y', '+y', '-z', '+z')"""
    c = [Vector((x, y, z)) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    # (index = ix * 4 + iy * 2 + iz)
    quads = {'-x': (0, 1, 3, 2), '+x': (4, 6, 7, 5), '-y': (0, 2, 6, 4), '+y': (1, 5, 7, 3), '-z': (0, 4, 5, 1), '+z': (2, 3, 7, 6)}
    out = []
    for name, q in quads.items():
        if name in skip: continue
        a, b, cc, dd = (c[i] for i in q)
        for tri in ((a, b, cc), (a, cc, dd)):
            vs = list(tri) if not inward else [tri[0], tri[2], tri[1]]
            n = (vs[1] - vs[0]).cross(vs[2] - vs[0]).normalized()
            out.append({'v': vs, 'mat': 'box', 'tex': None, 'vc': None, 'obj': 'box', 'n': n, 'look': look})
    return out


def fit(tris, box, yaw=0.0, keep_aspect=False, pad=(0, 0, 0), y0=None):
    """the matrix that puts the vehicle's footprint on box (x0, y0, z0, x1, y1, z1, Roblox studs, map frame) turned by
       yaw about +Y (yaw 0: front +Z; pi/2: front +X): scaled to fill the box (or uniformly, keep_aspect) less pad"""
    lo, hi = bounds(tris)
    L = (hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])
    x0, y0_, z0, x1, y1, z1 = box
    bx, by, bz = x1 - x0, y1 - y0_, z1 - z0
    turned = abs(math.sin(yaw)) > 0.5
    w, l = (bz, bx) if turned else (bx, bz)
    sx, sy, sz = (w - 2 * pad[0]) / L[0], (by - pad[1]) / L[1], (l - 2 * pad[2]) / L[2]
    if keep_aspect: sx = sy = sz = min(sx, sy, sz)
    base = y0_ if y0 is None else y0
    return (Matrix.Translation(((x0 + x1) / 2, base, (z0 + z1) / 2)) @ Matrix.Rotation(yaw, 4, 'Y')
            @ Matrix.Diagonal((sx, sy, sz, 1)))


def place(model, tris, M=None, weld=1e-4):
    """hand the triangles to arenakit, one bmesh per look (welded so smooth shading holds across a colour patch)"""
    by = {}
    for t in tris: by.setdefault(t['look'], []).append(t)
    for (kind, h), ts in by.items():
        bm = bmesh.new()
        for t in ts:
            vs = [bm.verts.new(M @ v if M else v) for v in t['v']]
            try: bm.faces.new(vs)
            except ValueError: pass
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=weld)
        K.put(model, kind, h, bm)
    return len(tris)


# ---------------------------------------------------------------- shared palettes
# the web's enclosed lifeboat (p_wreck_boat): one atlas of stripes, windows, a fender band and the roof's lettering
# panel (that averages to a pinkish white: it goes to the hull colour, so no blank plate is left on the roof)
def LIFEBOAT_RULES(hull='c07a45', hull2='a8693c', dark='3c3f44', glass='34404b', light='c9c6bf'):
    return {'*': [('ff8020', 'plastic', hull), ('806040', 'plastic', hull2), ('9f8040', 'plastic', hull2),
                  ('202020', 'plastic', dark), ('202040', 'plastic', dark), ('404040', 'plastic', dark),
                  ('dfbfbf', 'plastic', hull), ('df9f9f', 'plastic', hull), ('dfdfbf', 'plastic', hull),
                  ('406060', 'plastic', glass), ('406080', 'plastic', glass), ('bfbfbf', 'plastic', light),
                  ('ffffff', 'plastic', light), ('ffffdf', 'plastic', light)]}


# the web's farm wagon (p_wagon_open, built along +X, the tongue at +X): one wood atlas (blue sides, red wheels and
# undercarriage, a brown floor, the tongue and a crate, pale loaves) and plain iron (the tyres, the brake lever)
def WAGON_RULES(bed, floor, wheel, iron, wood, cargo, dark):
    return {'wo_wood': [('2060bf', 'plastic', bed), ('40609f', 'plastic', bed), ('806020', 'plastic', floor),
                        ('bf4020', 'plastic', wheel), ('9f4020', 'plastic', wheel), ('804020', 'plastic', wheel),
                        ('806040', 'plastic', wood), ('9f8040', 'plastic', wood), ('9f8060', 'plastic', cargo),
                        ('bf9f80', 'plastic', cargo), ('bf8060', 'plastic', cargo), ('202040', 'plastic', dark),
                        ('402040', 'plastic', dark), ('202020', 'plastic', dark)],
            'wo_iron': ('plastic', iron), '*': ('plastic', dark)}


def hunt_car(model, M, body='7c8790'):
    """the HOUSE HUNT garage car (offered to hunt-mode, 27 Nov 2026): the web game's hatchback (p_car_hatch) on the
    car's footprint in hunt_house_layout.FURN['car'] (x -4.5..4.5, y 0..7, z -10..10, front +Z: its hit boxes are the
    body -4.5,0.8,-10..4.5,4.4,10 and the cabin -4,4.4,-5..4,7,4). M: the prop's placement matrix (Roblox space), as
    hunt_house_props passes it to every prop. One call in place of hunt_house_props.car(M):
        import vehicle_port as VP; VP.hunt_car(M_, M)"""
    tris = port('p_car_hatch', CAR_RULES(body=body))
    return place(model, tris, M @ fit(tris, (-4.5, 0.0, -10.0, 4.5, 7.0, 10.0)))


def highnoon_wagon(x, z, wm='8c6a47', wd='5c4532', iron='4f4a45', cargo='b38f5c', model='wagon'):
    """the High Noon finisher set's street cart (offered to the finishers session, 27 Nov 2026): the web game's open
    wagon in the town's woods, on the cart's own footprint in highnoon_town.wagon(x, z) (x +-2.1, z +-3.2, 3 tall,
    along z), in the town kit's kinds (planks for the bed, wood for the rest). One call in place of wagon(8.6, 21.0):
        import vehicle_port as VP; VP.highnoon_wagon(8.6, 21.0, C['wm'], C['wd'])"""
    rules = {'wo_wood': [('2060bf', 'planks', wm), ('40609f', 'planks', wm), ('806020', 'planks', wd),
                         ('bf4020', 'wood', wd), ('9f4020', 'wood', wd), ('804020', 'wood', wd), ('806040', 'wood', wm),
                         ('9f8040', 'wood', wm), ('9f8060', 'wood', cargo), ('bf9f80', 'wood', cargo), ('bf8060', 'wood', cargo),
                         ('202040', 'metal', iron), ('402040', 'metal', iron), ('202020', 'metal', iron)],
             'wo_iron': ('metal', iron), '*': ('wood', wd)}
    body, tongue = wagon_parts(port('p_wagon_open', rules))
    return place(model, body + tongue, fit(body, (x - 2.1, 0.0, z - 3.2, x + 2.1, 3.0, z + 3.2)))


def wagon_parts(tris):
    """the open wagon turned so it runs along Z (tongue +Z) and split: (the wagon, its tongue). The tongue is what lies
       ahead of the bed's front board, low down"""
    tris = turn(tris, -math.pi / 2)
    top = [v.z for t in tris if centre(t).y > 3.0 for v in t['v']]
    front = max(top) if top else 0.0
    tongue, body = split(tris, lambda t: centre(t).z > front + 0.15 and centre(t).y < 3.0)
    return body, tongue


# the web traffic cars (p_car, p_car_sedan, p_car_hatch, p_car_taxi ...): 'tint' is the paint (a near-white panel-line
# picture times the paint in the vertex colours), 'glass' painted windows, 'trim' an atlas of small parts (tyres,
# chrome, grilles, plates, stickers), 'lamp' headlamps, 'tail' tail lamps, 'ind' indicators
def CAR_RULES(body, glass='2f3944', tyre='34363a', rim='8e939a', dark='45484e', plate='d9d6cc', lamp='e7e2d2',
              tail='8e3b38', ind='d9873e', ind_kind='plastic', chrome='aeb3b9'):
    trim = [('111111', 'plastic', tyre), ('222222', 'plastic', tyre), ('333333', 'plastic', dark), ('555555', 'plastic', dark),
            ('888888', 'plastic', rim), ('aaaaaa', 'plastic', chrome), ('cccccc', 'plastic', chrome), ('eeeeee', 'plastic', plate),
            ('ffffff', 'plastic', plate), ('e8c040', 'plastic', ind), ('ff8000', 'plastic', ind), ('cc2020', 'plastic', tail),
            ('80ff60', 'plastic', plate), ('ff60c0', 'plastic', plate), ('3070c0', 'plastic', dark), ('60e0ff', 'plastic', plate),
            ('c09060', 'plastic', dark), ('602818', 'plastic', dark), ('ffb0c8', 'plastic', plate)]
    def paint(t):
        c = t['tex']
        if c and lum(c) < 0.3: return ('plastic', dark)          # the tint sheet's dark patch (under the bumpers)
        return ('plastic', body)
    return {'tint': [paint], 'glass': ('plastic', glass), 'trim': trim, 'lamp': ('plastic', lamp),
            'tail': ('plastic', tail), 'ind': (ind_kind, ind), '*': ('plastic', dark)}
