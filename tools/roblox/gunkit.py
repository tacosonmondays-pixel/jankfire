# The kit the Roblox game's own weapon models are built from (tools/roblox/gun_models.py uses it). Headless Blender.
#
# WHY: the web game's weapon models were made for another renderer (many small pieces, printed pictures); in Roblox
# they read as noisy, and repainting did not fix it (owner, 15 Nov 2026). These are new models built FOR Roblox in
# the class of finish the owner pointed at: a few big chamfered masses, eight-sided barrels, two or three flat
# colours, SmoothPlastic, no pictures. Style notes: vault "Research/Rivals weapons and skins - style notes.md".
#
# THE FRAME. Everything here is written in the game's own weapon frame, the one Weapons.luau's `mdl` spots use:
# metres, x = right, y = up, z = BACK (the muzzle is at -z), the grip near the origin. P() turns that into Blender's
# z-up frame, and the .glb comes out in the file frame again (export_yup), so the numbers in a builder are the
# numbers in the weapon's row.
#
# PIECES. A gun is a handful of pieces, one per (node, slot):
#   node  what it is / what moves:  body, barrel, mag, grip, stock, sight, trim ... (+ the names the game moves:
#         mag, charge, pump, bolt, lever, slide, hammer, cylinder ... see Weapons.luau mdl.parts and GunParts.luau).
#         a wrap zone rides on it as in the web models: _wzA = the colour block, _wzB = the dark / metal end,
#         _wzN = trims (only painted by a FULL wrap).
#   slot  which colour of the gun's little palette it wears: body, frame, dark, steel, wood, accent, glow, glass ...
# the piece arrives in Studio as a MeshPart named "<node>__<slot>", so a skin can recolour a slot or swap a node by
# name. Every solid added to the same (node, slot) is joined into one mesh.
import bpy, bmesh, math, os, json
from mathutils import Vector, Matrix


def P(x, y, z):
    """weapon frame (x right, y up, z back) -> Blender (x, -z, y)"""
    return Vector((x, -z, y))


def lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def hex_rgb(h): return [int(h[j:j + 2], 16) / 255 for j in (0, 2, 4)]


def rect(z0, z1, y0, y1):
    """a side-view rectangle as a profile [(z, y)]"""
    return [(z0, y0), (z1, y0), (z1, y1), (z0, y1)]


def raked(cz, cy, length, depth, rake, taper=0.0):
    """a handle seen from the side: a slab `length` long and `depth` deep (front to back) centred on (cz, cy), its
       top leaning forward by `rake` radians (the same sign as holds.json: negative = the usual pistol-grip rake).
       taper > 0 flares the bottom. returns a profile [(z, y)]"""
    h, d = length / 2, depth / 2
    pts = [(-d - taper, -h), (d + taper, -h), (d, h), (-d, h)]  # (along z, along the handle)
    s, c = math.sin(rake), math.cos(rake)
    # the handle's own up axis is (y, z) = (cos, sin(rake)): CFrame.Angles(rake, 0, 0) applied to +Y
    return [(cz + u * c + v * s, cy + v * c - u * s) for u, v in pts]


class Gun:
    def __init__(self, name):
        self.name = name            # 'w_ar'
        self.slots = {}             # slot -> { color, kind ('p' plastic, 'n' neon, 'g' glass), alpha }
        self.pieces = {}            # (node, slot) -> bmesh
        self.spots = {}             # name -> (x, y, z): muzzle, sight, grip ... (written into the file's notes)

    # ---- the palette
    def slot(self, name, color, kind='p', alpha=1.0):
        self.slots[name] = {'color': color, 'kind': kind, 'alpha': alpha}

    def _bm(self, piece):
        node, slot = piece.split('__')
        if slot not in self.slots: raise SystemExit('%s: no slot %r (piece %s)' % (self.name, slot, piece))
        return self.pieces.setdefault((node, slot), bmesh.new())

    def _add(self, piece, bm, smooth=None):
        """fold a finished solid into its piece. smooth: a test (face) -> bool for the faces that shade smooth (a
           barrel's sides); everything else is flat, so every chamfer is a crisp facet"""
        bm.normal_update()
        for f in bm.faces: f.smooth = bool(smooth and smooth(f))
        for e in bm.edges:
            fs = e.link_faces
            e.smooth = len(fs) == 2 and fs[0].smooth and fs[1].smooth
        me = bpy.data.meshes.new('tmp')
        bm.to_mesh(me); bm.free()
        self._bm(piece).from_mesh(me)
        bpy.data.meshes.remove(me)

    # ---- solids
    def prism(self, piece, prof, w, bev=0.004, x=0.0, wtop=None, shear=0.0):
        """a side-view outline [(z, y)] pushed out to a width. w = full width (at the outline's lowest point when
           wtop is given: the width then runs straight to wtop at its highest point, a wedge section). every edge is
           chamfered once by bev. shear moves the top sideways (rarely wanted)"""
        bm = bmesh.new()
        ys = [p[1] for p in prof]
        y0, y1 = min(ys), max(ys)
        def hw(y):
            if wtop is None or y1 - y0 < 1e-9: return w / 2
            return (w + (wtop - w) * (y - y0) / (y1 - y0)) / 2
        def cx(y): return x + (shear * (y - y0) / (y1 - y0) if y1 - y0 > 1e-9 else 0)
        L = [bm.verts.new(P(cx(y) - hw(y), y, z)) for z, y in prof]
        R = [bm.verts.new(P(cx(y) + hw(y), y, z)) for z, y in prof]
        n = len(prof)
        bm.faces.new(L); bm.faces.new(R[::-1])
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new([L[i], R[i], R[j], L[j]])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        if bev > 0:
            bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bev, offset_type='OFFSET', segments=1, profile=0.5, affect='EDGES', clamp_overlap=True)
        self._add(piece, bm)

    def box(self, piece, x, y, z, bev=0.004, wtop=None):
        """x, y, z = (lo, hi) each. wtop narrows (or widens) the top"""
        self.prism(piece, rect(z[0], z[1], y[0], y[1]), x[1] - x[0], bev=bev, x=(x[0] + x[1]) / 2, wtop=wtop)

    def xprism(self, piece, prof, z0, z1, bev=0.004):
        """an outline seen from the FRONT [(x, y)] pushed along the barrel from z0 to z1 (rails, tubes with flats)"""
        bm = bmesh.new()
        A = [bm.verts.new(P(px, py, z0)) for px, py in prof]
        B = [bm.verts.new(P(px, py, z1)) for px, py in prof]
        n = len(prof)
        bm.faces.new(A); bm.faces.new(B[::-1])
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new([A[i], B[i], B[j], A[j]])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        if bev > 0:
            bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bev, offset_type='OFFSET', segments=1, profile=0.5, affect='EDGES', clamp_overlap=True)
        self._add(piece, bm)

    def yprism(self, piece, prof, y0, y1, bev=0.004):
        """an outline seen from ABOVE [(x, z)] pushed up from y0 to y1"""
        bm = bmesh.new()
        A = [bm.verts.new(P(px, y0, pz)) for px, pz in prof]
        B = [bm.verts.new(P(px, y1, pz)) for px, pz in prof]
        n = len(prof)
        bm.faces.new(A); bm.faces.new(B[::-1])
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new([A[i], B[i], B[j], A[j]])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        if bev > 0:
            bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bev, offset_type='OFFSET', segments=1, profile=0.5, affect='EDGES', clamp_overlap=True)
        self._add(piece, bm)

    @staticmethod
    def _frame(a, b):
        """two unit vectors square to the line a -> b (weapon frame); the first is as near 'up' as it can be"""
        a, b = Vector(a), Vector(b)
        ax = (b - a).normalized()
        up = Vector((0, 1, 0))
        if abs(ax.dot(up)) > 0.95: up = Vector((0, 0, -1))
        u = (up - ax * ax.dot(up)).normalized()
        v = ax.cross(u).normalized()
        return a, b, u, v

    def cyl(self, piece, r, a, b, sides=8, bev=0.003, r2=None, flat=True, smooth=True, hole=None):
        """an n-sided cylinder (or cone: r at a, r2 at b) between two points (x, y, z). flat = a flat faces up (else a
           corner). its sides shade smooth, its ends and chamfers stay crisp. hole = (radius, depth): a blind hole
           sunk into the END AT a (a muzzle)"""
        a, b, u, v = self._frame(a, b)
        r2 = r if r2 is None else r2
        off = math.pi / sides if flat else 0.0
        bm = bmesh.new()
        def loop(c, rad):
            return [bm.verts.new(P(*(c + (u * math.cos(off + i * 2 * math.pi / sides) + v * math.sin(off + i * 2 * math.pi / sides)) * rad))) for i in range(sides)]
        A, B = loop(a, r), loop(b, r2)
        sides_f = []
        for i in range(sides):
            j = (i + 1) % sides
            sides_f.append(bm.faces.new([A[i], B[i], B[j], A[j]]))
        bm.faces.new(B)
        inner = []
        if hole:
            hr, hd = hole
            ax = (b - a).normalized()
            H0, H1 = loop(a, hr), loop(a + ax * hd, hr)
            for i in range(sides):
                j = (i + 1) % sides
                bm.faces.new([A[i], A[j], H0[j], H0[i]])
                inner.append(bm.faces.new([H0[i], H0[j], H1[j], H1[i]]))
            bm.faces.new(H1)
        else:
            bm.faces.new(A)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        keep = set(sides_f)
        if bev > 0:
            rim = [e for e in bm.edges if sum(1 for f in e.link_faces if f in keep) == 1 and not any(f in inner for f in e.link_faces)]
            bmesh.ops.bevel(bm, geom=rim, offset=bev, offset_type='OFFSET', segments=1, profile=0.5, affect='EDGES', clamp_overlap=True)
        axb = (P(*b) - P(*a)).normalized()  # (after the chamfer: the sides are the faces that still face straight out)
        self._add(piece, bm, smooth=(lambda f: abs(f.normal.dot(axb)) < 0.45) if smooth else None)

    def cylz(self, piece, r, z0, z1, y=0.0, x=0.0, **kw):
        """a cylinder along the barrel; z0 is the end a `hole` goes into (give the muzzle end first)"""
        self.cyl(piece, r, (x, y, z0), (x, y, z1), **kw)

    def ring(self, piece, ro, ri, a, b, sides=8, bev=0.002, flat=True, smooth=False):
        """a ring (a tube with a hole right through) between two points: sight frames, barrel bands, drum rims"""
        a, b, u, v = self._frame(a, b)
        off = math.pi / sides if flat else 0.0
        bm = bmesh.new()
        def loop(c, rad):
            return [bm.verts.new(P(*(c + (u * math.cos(off + i * 2 * math.pi / sides) + v * math.sin(off + i * 2 * math.pi / sides)) * rad))) for i in range(sides)]
        AO, BO, AI, BI = loop(a, ro), loop(b, ro), loop(a, ri), loop(b, ri)
        out = []
        for i in range(sides):
            j = (i + 1) % sides
            out.append(bm.faces.new([AO[i], BO[i], BO[j], AO[j]]))
            bm.faces.new([AI[i], AI[j], BI[j], BI[i]])
            bm.faces.new([AO[i], AO[j], AI[j], AI[i]])
            bm.faces.new([BO[i], BI[i], BI[j], BO[j]])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        if bev > 0:
            bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bev, offset_type='OFFSET', segments=1, profile=0.5, affect='EDGES', clamp_overlap=True)
        axb = (P(*b) - P(*a)).normalized()
        self._add(piece, bm, smooth=(lambda f: abs(f.normal.dot(axb)) < 0.45) if smooth else None)

    def window(self, piece, x, y, z, t, bev=0.003):
        """a square frame standing across the gun (a sight you look through): x, y = (lo, hi) of its OUTSIDE,
           z = (lo, hi) its thickness along the barrel, t = how thick the frame's bars are. the kit's own sight shape"""
        (x0, x1), (y0, y1) = x, y
        self.box(piece, (x0, x0 + t), (y0, y1), z, bev=bev)
        self.box(piece, (x1 - t, x1), (y0, y1), z, bev=bev)
        self.box(piece, (x0 + t * 0.6, x1 - t * 0.6), (y1 - t, y1), z, bev=bev)
        self.box(piece, (x0 + t * 0.6, x1 - t * 0.6), (y0, y0 + t), z, bev=bev)

    def ball(self, piece, r, at, sub=2):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
        c = P(*at)
        for vtx in bm.verts: vtx.co += c
        self._add(piece, bm, smooth=lambda f: True)

    # ---- skins: a skin is the gun with its slots recoloured and some nodes swapped (tools/roblox/gun_models.py SKINS)
    def drop(self, *nodes):
        """take every piece of these nodes off (a node is its name without the wrap zone: 'barrel' drops
           barrel_wzA / barrel_wzB / barrel_wzN ...), so a skin can build its own"""
        for key in list(self.pieces):
            base = key[0].split('_wz')[0]
            if base in nodes or key[0] in nodes:
                self.pieces.pop(key).free()

    def recolour(self, **slots):
        """slot = 'rrggbb' (or (colour, kind) / (colour, kind, alpha)): the same pieces in other colours"""
        for name, v in slots.items():
            if isinstance(v, str): v = (v,)
            s = self.slots.setdefault(name, {'color': v[0], 'kind': 'p', 'alpha': 1.0})
            s['color'] = v[0]
            if len(v) > 1: s['kind'] = v[1]
            if len(v) > 2: s['alpha'] = v[2]

    # ---- out
    def bounds(self):
        lo, hi = [1e9] * 3, [-1e9] * 3
        for bm in self.pieces.values():
            for v in bm.verts:
                g = (v.co.x, v.co.z, -v.co.y)
                for i in range(3): lo[i] = min(lo[i], g[i]); hi[i] = max(hi[i], g[i])
        return [round(x, 4) for x in lo], [round(x, 4) for x in hi]

    def tris(self):
        return sum(sum(len(f.verts) - 2 for f in bm.faces) for bm in self.pieces.values())

    def to_scene(self, at=Matrix.Identity(4), prefix=''):
        """the pieces as objects in the current scene (for a preview render or an export). returns the objects"""
        objs = []
        mats = {}
        for (node, slot), bm in self.pieces.items():
            me = bpy.data.meshes.new(node)
            bm.to_mesh(me)
            o = bpy.data.objects.new(prefix + node, me)
            bpy.context.scene.collection.objects.link(o)
            if slot not in mats:
                s = self.slots[slot]
                m = bpy.data.materials.new(slot)
                m.use_nodes = True
                b = m.node_tree.nodes['Principled BSDF']
                r, g, bl = [lin(c) for c in hex_rgb(s['color'])]
                b.inputs['Base Color'].default_value = (r, g, bl, 1)
                b.inputs['Metallic'].default_value = 0.0
                b.inputs['Roughness'].default_value = 0.75
                if s['kind'] == 'n':
                    (b.inputs.get('Emission Color') or b.inputs.get('Emission')).default_value = (r, g, bl, 1)
                    b.inputs['Emission Strength'].default_value = 2.0
                if s['kind'] == 'g':
                    b.inputs['Alpha'].default_value = s['alpha']
                    m.blend_method = 'BLEND'
                mats[slot] = m
            me.materials.append(mats[slot])
            o.matrix_world = at
            objs.append(o)
        return objs

    def export(self, out_dir):
        """<out_dir>/<name>.glb in the weapon frame, one node per piece, one material per slot (named by the slot).
           tools/roblox/export_weapons.py takes it from there (the turn for Roblox, the look in the piece names)"""
        bpy.ops.wm.read_factory_settings(use_empty=True)
        objs = self.to_scene()
        root = bpy.data.objects.new(self.name, None)
        bpy.context.scene.collection.objects.link(root)
        lo, hi = self.bounds()
        root['jf'] = json.dumps({'kind': 'weapon', 'id': self.name[2:], 'set': 'kit', 'lo': lo, 'hi': hi, 'spots': self.spots})
        for o in objs: o.parent = root
        path = os.path.join(out_dir, self.name + '.glb')
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=False, export_apply=True,
                                  export_animations=False, export_yup=True, export_extras=True,
                                  export_vertex_color='NONE')
        return path, lo, hi, self.tris(), len(self.pieces)
