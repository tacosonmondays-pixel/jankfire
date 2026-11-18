# TRIPO SKINS REBUILT ON OUR OWN BASE (18 Nov 2026). The owner: "I don't like tripo guns! I do like how it made wings
# and decorative parts but the base of the gun should be made in blender by you in the style of rivals!"
#   - The gun's BASE is ours, built here with the Blender-artist kit (tools/roblox/artist_kit.py: exact booleans, one
#     crisp wide chamfer, weighted normals) in Rivals' finish: a few fat masses, the colour as a frame round darker
#     insets, flat colours, real gun parts, panel lines, and painted motifs CUT IN as flat colour regions.
#   - Tripo is only for DECORATION: the parts the owner liked are loaded at build time from the cleaned Tripo file in
#     the vault (never copied into the repo) and attached to this base.
# Built with the live set (flat kit colours; wrap UVs at export like every kit gun; no bake):
#   JF_EXTRA=gun_sets_tripo_rebuild blender -b --factory-startup -P tools/roblox/gun_set.py -- <out_dir> pistol@pistol_ducky_tripo
#   JF_EXTRA=gun_sets_tripo_rebuild blender -b --factory-startup -P tools/roblox/gun_check.py -- pistol@pistol_ducky_tripo
#   JF_NOZFIX=1 JF_EXTRA=gun_sets_tripo_rebuild blender -b --factory-startup -P tools/roblox/gun_zfix.py -- pistol@pistol_ducky_tripo
# (tripo_gun.py also registers pistol@pistol_ducky_tripo, the whole-Tripo v709, when JF_EXTRA names it: name one only.)
#
# pistol@pistol_ducky_tripo  DUCKY PLAN B, rebuilt (the owner's concept: vault Assets/tripo-17nov/ducky-pistol/concept.png,
#   and the red-pen marks owner-marks-1/2.jpg). Plan B's contract: its spots (muzzle, sight line y 0.0585, port, grip),
#   the moving nodes slide (kicks back 0.038), mag (drops along the grip's rake), hammer (tips about x).
#   - SLIDE (node slide): a fat yellow slide under a pearl top rib; the duck's face, clouds and a curling sea cut into
#     its flanks as flat colour (the katana's crest and foam shapes, tripo_gun.CREST / FOAM); a blue-white-blue band
#     round it behind the front post (paint only: nothing rises above the slide top between the notch and the post);
#     rear serrations; the ejection port on the right with a dark chamber; the slim notch and a short front post on
#     the aim line (gun_sights; the post is short, so no dot). The striped life ring (kit hoop, even bands) hangs on
#     its left on two gold clips and kicks with it.
#   - DUCK BLOCK (node slide: it and all on it kick with the slide, as v709's head did): a yellow block on the slide's
#     nose (0.5 mm into it: a seam, not a gap), a touch narrower and lower than the slide, with a blue inset and three
#     white bubbles each side; Tripo's duck head in front of it with its open bill and eyes, made rounder (wider,
#     deeper, a little lower: from the eye its top hides behind the slide's, so the front post stands against the sky)
#     and sunk into the block; Tripo's crown upright and centred ON the head, twice its size, sat down into it and
#     fused (one moulded head-and-crown, 18 Nov; it was worn at a slant on the head's left, off the head from the
#     side). Its tips rise above the aim line, so it is its own piece slide_wzN__crown that the hold hides while
#     aiming (holds.json ads.skins). The block's flat top is the hat seat (hats ride the piece under them, hide while
#     aiming).
#     The barrel (node body) stays put: its bore is in the duck's mouth at rest and shows out of it when the slide kicks,
#     a link under it holds it to the frame.
#   - FRAME (node body): pearl, a rail line along each side, the recoil plug (gold ring, dark bore) under the head, the
#     squared gold guard and flat trigger, the gold slide stop (dark slot) and thumb safety on the left, the takedown
#     pin's head on the right, the yellow grip-safety tail.
#   - GRIP (node grip): a fat pearl grip with front-strap grooves; each side a gold bezel round a blue panel with
#     white curling waves at its foot and gold screws; Tripo's wing relief lying flat on the panel.
#   - MAG (node mag): hidden in the grip but for its chunky gold base. HAMMER (node hammer): a gold spur, cocked.
#   - Zones: the base masses _wzA (slide, rib, comp, frame, grip), metal and working parts _wzB, decoration and
#     painted motifs _wzN (a wrap leaves them alone). The painted motifs are IMPRINTED (tripo_gun.imprint: the base's
#     own faces split along the outlines, no walls, nothing laid on top); the band is slices of the slide's own body.
#     A first try let them in as 3 mm boolean inlays: their hidden walls ran closer than the flicker scan's 1.8 mm
#     wherever two outlines run near each other (a foam line, a wave's curl), and gun_zfix pushed them 7 mm out.
#     As built: 0 z-fight pairs, gun_check one piece. Tripo files stay in the vault; nothing of them is in git.
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import gunkit
from gunkit import Gun, P, raked
from artist_kit import ArtGun, SG, outline, rrect, path, prism, xprism, cyl, tube, curve_slab, curve_sweep, cut, soft, _link, KEEP

VAULT = os.environ.get('JF_TRIPO_ROOT', r'C:\Users\soup2\Documents\JANKFIRE Vault\Assets')
DUCKY_PISTOL = os.path.join(VAULT, 'tripo-17nov', 'ducky-pistol', 'w_pistol@pistol_ducky_tripo_clean.blend')

NAMES = {'pistol@pistol_ducky_tripo': 'Ducky Plan B'}


class KitArt(ArtGun):
    """an ArtGun that exports as a plain kit gun (flat slot colours, no bake: export_weapons.py unfolds the wrap UVs
       as for any kit gun); its file notes also carry the hat seat proposal (hat = ((x, y, z), size)) as hatAt"""
    hat = None

    def export(self, out_dir):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        objs = self.to_scene()
        root = bpy.data.objects.new(self.name, None)
        bpy.context.scene.collection.objects.link(root)
        lo, hi = self.bounds()
        meta = {'kind': 'weapon', 'id': self.name[2:], 'set': 'kit', 'lo': lo, 'hi': hi, 'spots': self.spots}
        if self.hat: meta['hatAt'] = [list(self.hat[0]), self.hat[1]]
        root['jf'] = json.dumps(meta)
        for o in objs: o.parent = root
        path_ = os.path.join(out_dir, self.name + '.glb')
        bpy.ops.export_scene.gltf(filepath=path_, export_format='GLB', use_selection=False, export_apply=True,
                                  export_animations=False, export_yup=True, export_extras=True,
                                  export_vertex_color='NONE')
        return path_, lo, hi, self.tris(), len(self.pieces)


# ================================================================================================ shared helpers
def wf(co):
    """Blender kit frame -> weapon frame"""
    return Vector((co.x, co.z, -co.y))


def tripo_parts(blend, picks):
    """the cleaned Tripo file's pieces (one mesh per piece, kit Blender frame) -> {piece: bmesh} keeping only the
       connected parts that pass picks[piece](lo, hi) (their weapon-frame box). Read from the vault at build time"""
    if not os.path.exists(blend):
        raise SystemExit('gun_sets_tripo_rebuild: the cleaned Tripo file is not here: %s' % blend)
    with bpy.data.libraries.load(blend) as (src, dst):
        dst.meshes = [n for n in src.meshes if n.split('.')[0] in picks]
    out = {}
    for me in dst.meshes:
        name = me.name.split('.')[0]
        bm = bmesh.new(); bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        parent = list(range(len(bm.verts)))
        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]; i = parent[i]
            return i
        for e in bm.edges:
            a, b = find(e.verts[0].index), find(e.verts[1].index)
            if a != b: parent[a] = b
        groups = {}
        for f in bm.faces: groups.setdefault(find(f.verts[0].index), []).append(f)
        drop = []
        for fs in groups.values():
            ws = [wf(v.co) for f in fs for v in f.verts]
            lo = Vector([min(w[k] for w in ws) for k in range(3)]); hi = Vector([max(w[k] for w in ws) for k in range(3)])
            if not picks[name](lo, hi): drop += fs
        bmesh.ops.delete(bm, geom=drop, context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        out[name] = bm
        bpy.data.meshes.remove(me)
    return out


def plain(bm, sharp=40.0):
    """a bare copy of a bmesh (no custom data: the clean file's custom normals do not survive a move of its own),
       shaded smooth with edges sharper than `sharp` degrees hard"""
    out = bmesh.new()
    vm = {v: out.verts.new(v.co) for v in bm.verts}
    for f in bm.faces:
        try: out.faces.new([vm[v] for v in f.verts])
        except ValueError: pass
    out.normal_update()
    lim = math.radians(sharp)
    for f in out.faces: f.smooth = True
    for e in out.edges:
        fs = e.link_faces
        e.smooth = len(fs) == 2 and fs[0].normal.angle(fs[1].normal, 0.0) < lim
    return out


def add_bm(g, piece, bm):
    """fold a finished bmesh into a piece (after g.done(): it keeps its own normals)"""
    node, slot = piece.split('__')
    g.slots[slot]
    me = bpy.data.meshes.new('tp'); bm.to_mesh(me)
    g.pieces.setdefault((node, slot), bmesh.new()).from_mesh(me)
    bpy.data.meshes.remove(me)


def imprinted(g, solid, base_piece, sides, nmin=0.5):
    """FLAT COLOUR CUT INTO A SURFACE: no walls, nothing laid on top (an inlay's hidden walls lie closer than the
       flicker scan's 1.8 mm wherever two outlines run near each other: a foam line, a wave's curl). solid = an artist
       solid (its bevel and cuts set); sides = [(s, [(outline [(z, y)], piece), ...] bottom layer first), ...]:
       tripo_gun.imprint splits the faces that face side s (x) along every outline, the faces inside an outline go to
       its piece (the last one wins), the rest stay base_piece. Every part keeps the solid's own surface"""
    import tripo_gun as TG
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(solid.evaluated_get(dg)); me.transform(solid.matrix_world)
    solid.hide_render = True; solid.hide_set(True)
    bm = bmesh.new(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)
    bm.normal_update()
    bm.faces.layers.int.new('_sel')
    cls = bm.faces.layers.int.new('_cls')
    names = [base_piece]
    for s, polys in sides:
        hit = TG.imprint(bm, lambda f: True, [p for p, _ in polys], sides=(s,), nmin=nmin)
        for f, i in hit.items():
            pc = polys[i][1]
            if pc not in names: names.append(pc)
            f[cls] = names.index(pc)
    for k, pc in enumerate(names):
        sub = bm.copy()
        lay = sub.faces.layers.int['_cls']
        bmesh.ops.delete(sub, geom=[f for f in sub.faces if f[lay] != k], context='FACES')
        bmesh.ops.delete(sub, geom=[v for v in sub.verts if not v.link_faces], context='VERTS')
        m2 = bpy.data.meshes.new('imprint'); sub.to_mesh(m2); sub.free(); KEEP.append(m2)   # (no normals recalc: open)
        g.put(pc, _link(bpy.data.objects.new('imprint', m2)))
    bm.free()


def side(poly, s, face, depth, out=0.012):
    """a cutter for a side-view outline [(z, y)] on the flank at x = s * face: from `depth` inside it to `out` outside"""
    x0, x1 = face - depth, face + out
    return prism(poly, x1 - x0, x=s * (x0 + x1) / 2)


def oval(cz, cy, rz, ry, n=24, flat=None):
    """an ellipse [(z, y)]; flat = a height above cy where its top is cut level"""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        pts.append((cz + rz * math.cos(a), cy + (ry * math.sin(a) if flat is None else min(ry * math.sin(a), flat))))
    out = []
    for p in pts:   # (no repeated points where the top is cut level)
        if not out or abs(p[0] - out[-1][0]) > 1e-7 or abs(p[1] - out[-1][1]) > 1e-7: out.append(p)
    return out


def cloud(base, bumps, step=0.0006):
    """a cartoon cloud [(z, y)]: a flat foot at y = base under the upper envelope of round puffs [(cz, cy, r)] (crisp
       valleys where two puffs meet)"""
    za = min(cz - math.sqrt(max(r * r - (base - cy) ** 2, 0.0)) for cz, cy, r in bumps)
    zb = max(cz + math.sqrt(max(r * r - (base - cy) ** 2, 0.0)) for cz, cy, r in bumps)
    n = max(8, int((zb - za) / step))
    top = []
    for i in range(1, n):
        z = za + (zb - za) * i / n
        y = base
        for cz, cy, r in bumps:
            if abs(z - cz) < r: y = max(y, cy + math.sqrt(r * r - (z - cz) ** 2))
        top.append((z, y))
    return [(za, base), (zb, base)] + top[::-1]


def sea(z_rear, z_front, n, y0, H, bottom):
    """a band of n curling crests (tripo_gun.CREST: the katana's waves, each lip curling toward the muzzle) from z_rear
       to z_front, troughs at y0, crests H higher, its foot at `bottom`; and the white foam curl inside each crest
       (tripo_gun.FOAM). returns (band [(z, y)], [foam [(z, y)], ...]). Works in any 2D frame (u, v) as well"""
    from tripo_gun import CREST, FOAM
    Pd = (z_rear - z_front) / n
    top = []
    for w in range(n):
        for u, h in CREST: top.append((z_rear - (w + u) * Pd, y0 + h * H))
    top.append((z_front, y0))
    band = top + [(z_front, bottom), (z_rear, bottom)]
    foams = [[(z_rear - (w + u) * Pd, y0 + h * H) for u, h in FOAM] for w in range(n)]
    return band, foams


# ================================================================================================ Ducky Plan B
PAL = {'duck': 'f0c64a', 'pearl': 'f1e7eb', 'blue': '6d95cf', 'gold': 'c8932f', 'bill': 'd88c5c', 'wing': 'f7f4ee',
       'black': '2a2530', 'metal': '3e3b47'}
RAKE = -0.297                        # (Plan B's grip rake, radians)
GC = (0.034, -0.074)                 # the grip's centre (z, y)
SR, CR = math.sin(RAKE), math.cos(RAKE)
GD, GL, GT = 0.064, 0.142, 0.004     # the grip's depth, length, flare at its foot


def gl(u, v):
    """grip-local (u across the grip, + toward the back; v up the grip) -> side view (z, y) (gunkit.raked's turn)"""
    return (GC[0] + u * CR + v * SR, GC[1] + v * CR - u * SR)


def gpoly(pts):
    return [gl(u, v) for u, v in pts]


def g_front(v):
    """the grip's front face (its u) at v: the slab flares toward its foot"""
    return -(GD / 2 + GT * (GL / 2 - v) / GL)


def pistol_ducky_tripo():
    """DUCKY PLAN B rebuilt on our base (see the file's header)"""
    import gun_set
    import tripo_gun as TG
    g = KitArt('w_pistol@pistol_ducky_tripo')
    g.spots = dict(gun_set.BUILD['pistol']().spots)
    for k, v in PAL.items(): g.slot(k, v)
    gunkit.use_style('C')
    SY = g.spots['sight'][1]                      # 0.0585, the aim line
    TOP = 0.0525                                  # the slide's (and the comp's) top
    ZF, ZR = -0.172, 0.058                        # the slide's front and back
    XS = 0.027                                    # the slide's half width
    XR = 0.0235                                   # the rib's half width (it stands on the body's top flat)
    BY = 0.022                                    # the bore (the duck's mouth)
    one = dict(seg=1)                             # one crisp chamfer (Rivals)

    # ---------------------------------------------------------------- the slide (node "slide")
    def slide_body():
        return soft(prism([(ZF, 0.004), (ZR, 0.004), (ZR, 0.045), (ZF, 0.045)], 2 * XS), 0.0035, **one)

    def slide_rib():   # (the pearl top on the body's top flat: its flanks rise from the body's chamfer, a crisp step)
        return soft(xprism([(-XR, 0.045), (XR, 0.045), (XR, TOP - 0.0032), (XR - 0.0032, TOP), (-(XR - 0.0032), TOP),
                            (-XR, TOP - 0.0032)], ZF, ZR), 0.0008, **one)

    # the band round the slide behind the front post: blue, white, blue (slices of the slide's own body and rib)
    BAND = [(-0.160, -0.1535, 'slide_wzN__blue'), (-0.1535, -0.1465, 'slide_wzN__wing'), (-0.1465, -0.140, 'slide_wzN__blue')]
    def band_box(z0, z1): return prism([(z0, -0.01), (z1, -0.01), (z1, 0.07), (z0, 0.07)], 0.09)
    boxes = [band_box(z0, z1) for z0, z1, _ in BAND]
    # rear serrations (both flanks), the ejection port (right; it opens through the rib's right edge)
    grooves = []
    for s in (-1, 1):
        for z0 in (0.016, 0.0245, 0.033, 0.0415):
            grooves.append(side(outline(rrect(z0, z0 + 0.0034, 0.0185, 0.0395, 0.0012), step=0.002), s, XS, 0.0026))
    def port(): return prism(outline(rrect(-0.088, -0.034, 0.0255, 0.062, 0.004), step=0.002), 0.03, x=0.034)
    # the flanks, painted (imprinted): the sea along the foot (curling crests, foam curls), clouds, the duck's face
    band, foams = sea(0.064, -0.178, 7, 0.0074, 0.0124, -0.004)
    flanks = []
    for s in (-1, 1):
        fz = -0.0595 if s < 0 else -0.0105        # (the face: mid-slide on the left; behind the port on the right)
        eyes = [oval(fz - 0.0135, 0.0346, 0.0041, 0.0056), oval(fz + 0.0135, 0.0346, 0.0041, 0.0056)]
        bill = oval(fz, 0.0262, 0.0118, 0.0052, n=32, flat=0.0029)
        if s < 0:   # LEFT (first person sees it): a cloud behind the face; the life ring covers the front
            cl = cloud(0.0128, [(-0.0262, 0.0172, 0.0044), (-0.0178, 0.0228, 0.0066), (-0.0072, 0.0262, 0.0074), (0.0018, 0.0212, 0.0056), (0.0068, 0.0168, 0.0038)])
        else:       # RIGHT: a cloud ahead of the port
            cl = cloud(0.0128, [(-0.1332, 0.0168, 0.0038), (-0.1282, 0.0212, 0.0056), (-0.1192, 0.0262, 0.0074), (-0.1086, 0.0228, 0.0066), (-0.1002, 0.0172, 0.0044)])
        flanks.append((s, [(band, 'slide_wzN__blue')] + [(f, 'slide_wzN__wing') for f in foams] + [(cl, 'slide_wzN__wing'),
                           (bill, 'slide_wzN__bill')] + [(e, 'slide_wzN__black') for e in eyes]))
    imprinted(g, cut(slide_body(), *(boxes + grooves + [port()])), 'slide_wzA__duck', flanks)
    g.put('slide_wzA__pearl', cut(slide_rib(), *(boxes + [port()])))
    for (z0, z1, piece), box in zip(BAND, boxes):
        g.put(piece, cut(slide_body(), box, op='INTERSECT'), cut(slide_rib(), box, op='INTERSECT'))
    # the dark chamber in the port (its face 2.5 mm proud of the port's floor)
    g.put('slide_wzB__metal', soft(prism(outline(rrect(-0.0855, -0.0365, 0.022, 0.0405, 0.003), step=0.002), 0.0095,
                                         x=0.0215 - 0.00475), 0.0008, **one))
    # sights (gun_sights; near-black, on the rib): the notch at the back, a short front post (no dot) ahead of the band
    SG.notch(g, 'slide_wzN__metal', 0.045, SY, TOP, 0.028, depth=0.0065, nw=0.3, nd=0.0036)
    SG.blade(g, 'slide_wzN__metal', -0.1655, SY, TOP, w=0.0048, depth=0.008)
    # the life ring on the left flank (kit hoop: even pearl and blue bands), held by two gold clips; it kicks with
    # the slide
    RC, RR, Rr = (-0.0405, 0.0118, -0.1332), 0.0226, 0.0117
    TG.hoop(g, ['slide_wzN__pearl', 'slide_wzN__blue', 'slide_wzN__gold'], RC, RR, Rr, n=8, sides=12, steps=2)
    for phi in (0.0, 180.0):
        TG.clip(g, 'slide_wzN__gold', RC, RR, Rr, phi, x_in=-(XS - 0.0016), w=0.0075, t=0.0017)

    # ---------------------------------------------------------------- the frame (node "body", fixed)
    FX = 0.0235                                   # the frame's half width
    def frame():
        return soft(prism(outline([(-0.240, 0.005, 'c'), (-0.240, -0.027, 0.004), (-0.110, -0.027, 0.003), (-0.104, -0.021, 0.003),
                                   (-0.004, -0.021, 'c'), (0.058, -0.016, 'c'), (0.058, 0.005, 'c')], step=0.002), 2 * FX), 0.003, **one)
    rail = [xprism([(s * (FX + 0.006), -0.0152), (s * (FX - 0.0014), -0.0118), (s * (FX + 0.006), -0.0084)], -0.236, -0.108)
            for s in (-1, 1)]   # (the rail line along each side: a V groove)
    bore = cyl(0.0042, (0, -0.011, -0.246), (0, -0.011, -0.231), sides=16)
    g.put('body_wzA__pearl', cut(frame(), *(rail + [bore])))
    # the recoil plug: a gold ring on the frame's nose, a dark bore inside it
    g.put('body_wzN__gold', soft(tube(0.0072, 0.0042, (0, -0.011, -0.2428), (0, -0.011, -0.2392), sides=20), 0.0007, **one))
    g.put('body_wzN__black', cyl(0.0042, (0, -0.011, -0.2395), (0, -0.011, -0.2335), sides=16))
    # the squared gold guard and the flat trigger
    g.put('body_wzB__gold', curve_sweep(path([(-0.1035, -0.017, 'c'), (-0.1065, -0.0705, 0.011), (-0.020, -0.0775, 0.011),
                                              (0.0035, -0.060, 'c')], step=0.003), 0.0105, 0.017, 0.0035))
    g.put('body_wzB__gold', curve_slab(outline([(-0.0585, -0.017, 'c'), (-0.0445, -0.017, 'c'), (-0.0445, -0.0525, 0.0035),
                                                (-0.0505, -0.0585, 0.0032), (-0.0585, -0.054, 0.0032)], step=0.002), 0.012, 0.002, res=1))
    # the slide stop on the left: a gold lever (a dark slot painted in) with a round boss at its front; its pin's head
    # on the right; the thumb safety at the back on the left (all on the frame's flank, 4 mm proud)
    LX = FX + 0.004                               # (their outer face)
    stop = soft(prism(outline(rrect(-0.0885, -0.031, -0.0118, -0.0042, 0.0034), step=0.002), 0.0044, x=-(LX - 0.0022)), 0.0007, **one)
    imprinted(g, stop, 'body_wzN__gold', [(-1, [(outline(rrect(-0.071, -0.043, -0.0094, -0.0066, 0.0014), step=0.001), 'body_wzN__black')])])
    g.put('body_wzN__gold', soft(cyl(0.0064, (-(FX - 0.001), -0.008, -0.0875), (-(LX + 0.001), -0.008, -0.0875), sides=20), 0.0012, **one))
    g.put('body_wzN__gold', soft(cyl(0.0042, (FX - 0.001, -0.008, -0.0875), (FX + 0.0032, -0.008, -0.0875), sides=16), 0.0009, **one))
    g.put('body_wzN__gold', soft(prism(outline([(0.0245, -0.0035, 0.003), (0.034, 0.0022, 0.002), (0.0565, 0.0022, 'c'),
                                                (0.0565, -0.0085, 'c'), (0.032, -0.0085, 0.002)], step=0.002), 0.0044,
                                       x=-(LX - 0.0022)), 0.0007, **one))
    # the barrel (stays put: it shows out of the duck's mouth when the slide kicks), its dark bore, and the link under
    # its back down into the frame: hidden under the slide even at full kick, and behind every plane the band's hidden
    # slice faces sweep through while the slide kicks (no flicker in any pose)
    g.put('body_wzB__metal', soft(tube(0.0058, 0.0036, (0, BY, -0.2585), (0, BY, -0.088), sides=16), 0.0006, **one),
          soft(prism([(-0.098, -0.006), (-0.09, -0.006), (-0.09, BY - 0.004), (-0.098, BY - 0.004)], 0.008), 0.0008, **one))
    g.put('body_wzN__black', cyl(0.0036, (0, BY, -0.2554), (0, BY, -0.09), sides=16))

    # ---------------------------------------------------------------- the duck block (node "slide": it kicks)
    CX, CT = 0.0265, TOP - 0.002                  # (a touch narrower and lower than the slide: the head is the hero)
    def comp():   # (its back 0.5 mm into the slide's nose: the two chamfers meet in a seam line, one moving piece)
        return soft(prism([(-0.226, -0.006), (ZF + 0.0005, -0.006), (ZF + 0.0005, CT), (-0.226, CT)], 2 * CX), 0.004, **one)
    inset = outline(rrect(-0.2195, -0.1805, 0.0055, 0.0405, 0.0055), step=0.002)
    g.put('slide_wzA__duck', cut(comp(), *[side(inset, s, CX, 0.0035) for s in (-1, 1)]))
    for s in (-1, 1):   # the blue inset 1 mm under the block's face, three white bubbles rising, 2 mm proud of it
        g.put('slide_wzB__blue', soft(prism(inset, 0.0035, x=s * (CX - 0.001 - 0.00175)), 0.0006, **one))
        for cz, cy, r in ((-0.2055, 0.0165, 0.0062), (-0.1925, 0.0285, 0.0042), (-0.2055, 0.0348, 0.0029)):
            g.put('slide_wzN__wing', soft(cyl(r, (s * (CX - 0.002), cy, cz), (s * (CX + 0.001), cy, cz), sides=14), min(0.0009, r * 0.3), **one))

    # ---------------------------------------------------------------- the grip (node "grip")
    GX = 0.026
    def grip():   # (its top, inside the frame, cut level under the thumb safety)
        g0 = soft(prism(raked(GC[0], GC[1], GL, GD, RAKE, taper=GT), 2 * GX), 0.004, **one)
        return cut(g0, prism([(-0.1, -0.012), (0.2, -0.012), (0.2, 0.05), (-0.1, 0.05)], 0.1))
    PU, PV, PB = 0.0262, 0.058, 0.0034            # the panel: half widths across and up the grip, the bezel
    OUT = gpoly(outline(rrect(-PU, PU, -PV, PV, 0.009), step=0.002))
    IN = gpoly(outline(rrect(-(PU - PB), PU - PB, -(PV - PB), PV - PB, 0.006), step=0.002))
    strap = []   # the front strap's grooves (across it, square to the rake, 1.6 mm deep)
    for v in (-0.040, -0.028, -0.016, -0.004, 0.008):
        u0 = g_front(v) + 0.0016
        strap.append(prism(gpoly([(-0.05, v - 0.0013), (u0, v - 0.0013), (u0, v + 0.0013), (-0.05, v + 0.0013)]), 0.04))
    g.put('grip_wzA__pearl', cut(grip(), *([side(OUT, s, GX, 0.0065) for s in (-1, 1)] + strap)))
    crests, _f = sea(PU - PB, -(PU - PB), 2, -0.043, 0.0125, -0.075)
    PF = GX - 0.0008                              # the blue panel's face (|x|): 0.8 mm under the grip's
    PK = GX - 0.007                               # (the panel's and the bezel's backs, in the 6.5 mm pocket)
    for s in (-1, 1):   # a gold bezel 0.5 mm proud of the grip, the blue panel in it, white waves painted at its foot
        g.put('grip_wzB__gold', soft(cut(prism(OUT, GX + 0.0005 - PK, x=s * (GX + 0.0005 + PK) / 2), prism(IN, 0.03, x=s * GX)), 0.0007, **one))
        panel = soft(prism(IN, PF - PK, x=s * (PF + PK) / 2), 0.0005, **one)
        imprinted(g, panel, 'grip_wzB__blue', [(s, [(gpoly(crests), 'grip_wzN__wing')])])
        for u, v in ((-(PU - PB) + 0.005, -(PV - PB) + 0.0055), ((PU - PB) - 0.005, -(PV - PB) + 0.0055),
                     (-(PU - PB) + 0.005, (PV - PB) - 0.0055)):
            z, y = gl(u, v)
            g.put('grip_wzN__gold', soft(cyl(0.0026, (s * (PF - 0.002), y, z), (s * (PF + 0.002), y, z), sides=12), 0.0008, **one))
    # the grip safety's tail (yellow) over the web of the hand (its top 4 mm under the frame's, hidden under the slide)
    g.put('grip_wzA__duck', soft(prism(outline([(0.040, 0.001, 'c'), (0.062, 0.001, 0.004), (0.078, -0.0035, 0.006),
                                                (0.087, -0.0105, 0.004), (0.083, -0.0185, 0.003), (0.068, -0.0185, 0.004),
                                                (0.054, -0.030, 'c'), (0.041, -0.026, 'c')], step=0.002), 0.036), 0.003, **one))

    # ---------------------------------------------------------------- mag (node "mag") and hammer (node "hammer")
    g.put('mag_wzB__metal', soft(prism(gpoly([(-0.019, -0.076), (0.013, -0.076), (0.013, 0.05), (-0.019, 0.05)]), 0.03), 0.002, **one))
    g.put('mag_wzB__gold', soft(prism(gpoly([(-0.039, -0.0855), (0.038, -0.0855), (0.0365, -0.0705), (-0.0375, -0.0705)]), 0.058), 0.0035, **one))
    HP = (0.0545, 0.0048)                         # (the hammer's pivot, z y: Weapons.luau parts.hammer.at)
    g.put('hammer_wzB__gold', soft(prism([(HP[0] + (z - HP[0]) * 0.82, HP[1] + (y - HP[1]) * 0.82) for z, y in
                                          [(0.048, -0.003), (0.064, -0.005), (0.072, 0.012), (0.082, 0.026), (0.086, 0.038),
                                           (0.078, 0.045), (0.064, 0.04), (0.054, 0.024)]], 0.015), 0.0015, **one))
    g.done()

    # ---------------------------------------------------------------- Tripo's decoration (from the vault)
    T = tripo_parts(DUCKY_PISTOL, {
        'slide_wzA__duck': lambda lo, hi: hi.z < -0.20,                   # the round head
        'slide_wzN__bill': lambda lo, hi: hi.z < -0.23,                   # its open bill (upper and lower)
        'slide_wzN__gold': lambda lo, hi: hi.z < -0.23,                   # the small crown
        'slide_wzN__black': lambda lo, hi: hi.z < -0.23,                  # the eyes
        'grip_wzN__wing': lambda lo, hi: hi.x - lo.x > 0.003})            # the wing reliefs (not the flat wave decals)
    # head, bill, eyes: where Tripo had them, on the block (node slide), made rounder: 12 % wider and deeper about the
    # head's middle, 5 % lower about its chin (its crown of the head 7 mm under the aim line: from the eye it stays
    # hidden behind the slide's top, so the front post stands against the sky)
    HC = Vector((0.0, 0.0269, -0.2347))
    for src, dst, sharp in (('slide_wzA__duck', 'slide_wzN__duck', 70.0), ('slide_wzN__bill', 'slide_wzN__bill', 55.0),
                            ('slide_wzN__black', 'slide_wzN__black', 55.0)):
        for v in T[src].verts:
            w = wf(v.co) - HC
            v.co = P(HC.x + w.x * 1.12, (HC.y + w.y) * 0.95, HC.z + w.z * 1.12)
        add_bm(g, dst, plain(T[src], sharp=sharp))
    # the crown ON THE HEAD (18 Nov 2026, the owner: "ducky tripo on the pistol the crown isnt on the ducks head"):
    # upright, centred on the crown of the head, twice Tripo's size (about 15 mm across on the 40 mm head: Tripo's
    # was a 7.6 mm pip that read as a stray part), sitting down onto it (sunk 3.5 mm) and fused to it (sdf_kit.fuse, a
    # 1.5 mm fillet: one moulded head-and-crown, painted gold on the duck's yellow). Its own piece slide_wzN__crown
    # (node slide: it kicks with the slide), so the hold can hide it while aiming: it rises above the aim line (the
    # head's top is 7 mm under it). (Before: worn at a slant on the head's left, 15 mm off its middle, to keep it out
    # of the notch; seen from the side it was not on the head)
    crown = T['slide_wzN__gold']
    cw = [wf(v.co) for v in crown.verts]
    foot = Vector((sum(w.x for w in cw) / len(cw), min(w.y for w in cw), sum(w.z for w in cw) / len(cw)))
    hw = [wf(v.co) for v in T['slide_wzA__duck'].verts]   # (already placed: the rounder head)
    top = max(hw, key=lambda w: w.y)
    at = Vector((0.0, top.y - 0.0035, top.z - 0.001))
    for v, w in zip(crown.verts, cw):
        d = (w - foot) * 2.0
        v.co = P(at.x + d.x, at.y + d.y, at.z + d.z)
    g.slot('crown', PAL['gold'])
    add_bm(g, 'slide_wzN__crown', plain(crown, sharp=40.0))
    import sdf_kit as SDF
    SDF.fuse(g, [(('slide_wzN', 'duck'), 0), (('slide_wzN', 'crown'), 0.0015)], h=0.0004, tris=2600, name='duckcrown',
             smooth=1, seam_k=1.0)
    # the wings: onto this grip's panels at three quarters of Tripo's size (this grip is slimmer), on the panel's upper
    # part, lying flat: their back sunk into the panel, 2.3 mm proud of it as before
    wing = T['grip_wzN__wing']
    TP = (0.0393, -0.0802)                        # (the centre of Tripo's grip panel, z y)
    K, VC, VT = 0.75, 0.012, 0.0146               # (the scale; the wing's centre up this panel, and up Tripo's)
    for v in wing.verts:
        w = wf(v.co)
        dz, dy = w.z - TP[0], w.y - TP[1]
        u, vv = dz * CR - dy * SR, dz * SR + dy * CR
        z, y = gl(u * K, VC + (vv - VT) * K)
        sx = 1.0 if w.x > 0 else -1.0
        v.co = P(sx * (abs(w.x) - 0.026 + PF), y, z)
    add_bm(g, 'grip_wzN__wing', plain(wing, sharp=50.0))
    for bm in T.values(): bm.free()
    # the hat seat: the block's flat top (it rides the slide), 3.3 cm ahead of the front post; size on the hats' scale
    # (s = metres / 0.12): 0.62, Plan B's own hat size
    g.hat = ((0.0, round(TOP - 0.002, 4), -0.198), 0.62)
    return g


SKINS = {'pistol@pistol_ducky_tripo': pistol_ducky_tripo} if os.path.exists(DUCKY_PISTOL) else {}
