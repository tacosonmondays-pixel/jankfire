# BATCH A (17 Nov 2026): five NEW kit models for weapons ported from the web game (not remodels): the Minigun, the
# Water Pistol, the Nail Gun, the Bread and the Hand Slapper. The web game's own models (public/models/w_<id>.glb,
# tools/blender/make_<id>.py) are the brief for size, spots and what each thing IS; these are built fresh in the kit
# style (chunky, a few fat masses, two or three flat quiet colours with one accent), modelled with artist_kit.py solids
# and gunkit pieces, exported in plain flat kit colours (no bake), as gun_melee.py does.
#   blender -b --factory-startup -P tools/roblox/gun_set.py -- roblox/assets/weapons-kit/src minigun water nailgun bread slapper
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- minigun water nailgun bread slapper
#   JF_NOZFIX=1 blender -b --factory-startup -P tools/roblox/gun_zfix.py -- minigun water nailgun bread slapper   (0 pairs)
#   blender -b --factory-startup -P tools/roblox/export_weapons.py -- roblox/assets/weapons-kit --kit roblox/assets/weapons-kit/src/w_<id>.glb
#   - MINIGUN  w_minigun (look C: one wide crisp chamfer, 8-sided tubes shaded round). Six steel barrels round a dark
#              spindle, an olive front clamp, a charcoal mid clamp and a fat rotor drum: all node `barrels`, which spins
#              about its own z through its origin (0, 0, -0.45) on the axis. Behind it a charcoal rotor housing, an
#              olive receiver (charcoal top, dark side insets), a drive motor on the right, a dark carry handle on top,
#              a fat olive ammo box with a charcoal lid lip and latch hanging under the receiver, a vertical front grip
#              (fore) under the housing and a pistol grip with a trigger at the back (grip): a two-handed hip hold.
#   - WATER    w_water (look B: round edges). A big toy squirt gun: a light grey shell with dark insets, a clear tank on
#              top with blue caps and a filler cap, the liquid inside it (node `water`: a rounded block of the tank's
#              full inside, its flat bottom face AT the node origin on the tank floor (0, 0.0545, -0.0775), so scaling y
#              0 -> 1 empties / fills it), a ribbed blue pump under the barrel (node `pump`, origin at its middle; it
#              slides along z on its tube), a blue nozzle, a dark pistol grip and guard. Toy sights on the aim line
#              (y 0.136): a chunky notch on the rear hump at z 0.08, a blade on the tank's front cap.
#   - NAILGUN  w_nailgun (look B). A framing nailer turned to fire forward: a muted orange moulded housing (a rounded
#              box section) with a dark inset each side and charcoal end caps (the rear one, under the eye, with a lighter
#              top), the charcoal nose below its front with a steel contact-safety yoke round the driver guide (the muzzle
#              at its face), an orange handle with dark rubber insets on a charcoal foot with a steel air fitting, an
#              aluminium magazine track from the nose down to the foot with a long window through it, and
#              in the track the nail strip (node `mag`: 33 steel nails, heads in the track's rail, two orange collation
#              bands; origin at the strip's middle). Iron sights (gun_sights notch + blade) on the aim line y 0.1744;
#              nothing between them rises above y 0.163.
#   - BREAD    w_bread (look B: organic lofts). A huge domed loaf, 1.79 m in all, held like a bat: five scored slashes
#              along its top (pale crumb in the cuts), a darker baked base, the tip rounded at z -1.50; its narrow heel
#              sits in a faceted paper sleeve (the grip) open at the front with a thin lip, twisted shut at the back.
#   - SLAPPER  w_slapper (look B). A cartoon toy hand in a dusty rose, palm to the left (-x, the side first person
#              sees), with an off-white glove cuff: node `hand`, origin at the wrist (0, 0, -0.45) where the stick meets
#              the cuff; a plain light grey stick, a dark ribbed grip and a rose end knob. Since 18 Nov the hand is ONE
#              fused piece (the owner: "fuse the fingers so its all one piece"): a pillow palm, four fingers pressed
#              together with a shallow round groove between them and a slight curl, a thumb up out of a fat root, all
#              smooth unions of one distance field (sdf_kit.py), meshed once; the thumb's tip keeps the hats' seat.
# CONTRACT (the weapons session's specs, roblox/docs/WEAPONS.md; the web models' spots): spots muzzle, grip (where the
# fist closes), fore (the minigun's front grip), sight (water, nailgun: the aim line), mid (melee: 45 % from grip to
# tip) and hat (the hat seat). Each gun also carries `hatAt` [[x, y, z], size] (the web's export const hatAt) and
# `pivots` (the moving nodes' origins) in its file notes; the nodes' origins also sit in the glb (export_report.json
# "nodes"). Frame: gunkit's (metres; x right, y up, z back, the muzzle at -z).
# Zones (web wrapzones): the big shells _wzA (receiver + ammo box, water shell, nail drum, bread sleeve, slapper stick
# and grip), second parts _wzB (barrels, housing, caps, crust, hand), small trims _wzN (insets, sights, nails, tank,
# liquid, crumb, cuff). Under 10k triangles each.
# Flicker rule (gun_melee / artist_kit): no faces of two looks facing one way, overlapping, within 0.02 studs on the
# rack (gun_zfix: 2.2 mm on the water pistol up to 5.4 mm on the bread); JF_NOZFIX=1 gun_zfix.py shows 0 pairs.
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import gunkit
from gunkit import Gun, P, raked
from artist_kit import outline, rrect, prism, xprism, cyl, capsule, cut, union, soft, curve_slab, finish, _obj, _link, KEEP
from gun_melee import Melee, mid_of, split, ball, lathe, loft, W, _raw
import gun_sights as SG
import sdf_kit as SDF

FRAME, DARK, DECK, BLACK = '444851', '353840', '676d78', '16171b'


class Batch(Melee):
    """a Melee (ArtGun built, flat kit colours) whose moving nodes keep their own origins in the file (origins:
       node -> (x, y, z), weapon frame) and whose notes carry the hat seat (hat: ((x, y, z), size)) and the pivots"""
    def __init__(self, name):
        super().__init__(name)
        self.origins = {}
        self.hat = None

    def done(self):
        if self.hat: self.spots['hat'] = tuple(round(v, 4) for v in self.hat[0])
        return super().done()

    def export(self, out_dir):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        objs = self.to_scene()
        for o in objs:
            base = o.name.split('.')[0].split('_wz')[0]
            if base in self.origins:
                at = P(*self.origins[base])
                o.data.transform(Matrix.Translation(-at))
                o.matrix_world = Matrix.Translation(at)
        root = bpy.data.objects.new(self.name, None)
        bpy.context.scene.collection.objects.link(root)
        lo, hi = self.bounds()
        meta = {'kind': 'weapon', 'id': self.name[2:], 'set': 'kit', 'lo': lo, 'hi': hi, 'spots': self.spots}
        if self.origins: meta['pivots'] = {k: [round(v, 5) for v in at] for k, at in self.origins.items()}
        if self.hat:
            meta['hatAt'] = [[round(v, 4) for v in self.hat[0]], self.hat[1]]
            meta['hat_size'] = self.hat[1]
        root['jf'] = json.dumps(meta)
        for o in objs: o.parent = root
        path = os.path.join(out_dir, self.name + '.glb')
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=False, export_apply=True,
                                  export_animations=False, export_yup=True, export_extras=True,
                                  export_vertex_color='NONE')
        return path, lo, hi, self.tris(), len(self.pieces)


def r5(v): return tuple(round(x, 5) for x in v)


def split_v(o, test):
    """as gun_melee.split, but test(corners, centre, normal) also sees the face's corners (weapon frame): a face that
       wraps round a cut has its centre inside the cut, its corners tell the truth"""
    me = finish(o)
    out = []
    for keep in (False, True):
        bm = bmesh.new(); bm.from_mesh(me)
        bm.normal_update()
        gone = [f for f in bm.faces if bool(test([W(v.co) for v in f.verts], W(f.calc_center_median()), W(f.normal))) != keep]
        bmesh.ops.delete(bm, geom=gone, context='FACES')
        out.append(_raw(bm))
    o.hide_render = True; o.hide_set(True)
    return out


def inset_test(xface, z0, z1, y0, y1):
    """a split test: the floor of a side pocket let in from |x| = xface"""
    return lambda c, n: abs(n.x) > 0.95 and abs(c.x) < xface - 0.001 and z0 - 0.002 < c.z < z1 + 0.002 and y0 - 0.002 < c.y < y1 + 0.002


def pockets(z0, z1, y0, y1, r, xface, depth):
    """two side pocket cutters (left and right), let in `depth` from |x| = xface"""
    return [prism(outline(rrect(z0, z1, y0, y1, r)), depth + 0.02, x=sx * (xface - depth + (depth + 0.02) / 2)) for sx in (-1, 1)]


# ================================================================================================= the minigun
def minigun():
    """THE MINIGUN (see the file's header)"""
    gunkit.use_style('C')
    g = Batch('w_minigun')
    g.slot('body', '545c46'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('deck', DECK)
    g.slot('steel', '8a9099'); g.slot('black', BLACK)
    # ---- the barrels (node `barrels`): six barrels on a 42 mm circle, bores with a dark plug 6 mm in, a spindle, the
    # front clamp (the one colour), the mid clamp and the rotor drum sunk 10 mm into the housing (all round the axis)
    R = 0.042
    for k in range(6):
        a = math.pi / 6 + k * math.pi / 3
        bx, by = R * math.cos(a), R * math.sin(a)
        # (a corner up: no barrel face lies level with the clamps' flat faces)
        g.cylz('barrels_wzB__steel', 0.0135, -0.75, -0.235, x=bx, y=by, sides=8, bev=0.002, hole=(0.0072, 0.03), flat=False)
        g.cylz('barrels_wzN__black', 0.0068, -0.744, -0.72, x=bx, y=by, sides=8, bev=0, flat=False)
    g.cylz('barrels_wzA__body', 0.062, -0.728, -0.704, sides=8, bev=0.004)
    g.cylz('barrels_wzB__frame', 0.06, -0.49, -0.468, sides=8, bev=0.004)
    g.cylz('barrels_wzB__frame', 0.072, -0.262, -0.196, sides=8, bev=0.006)
    g.cylz('barrels_wzB__dark', 0.019, -0.738, -0.19, sides=8, bev=0.002)
    g.origins['barrels'] = (0.0, 0.0, -0.45)
    # ---- the rotor housing (charcoal) round the drum's back
    g.cylz('housing_wzB__frame', 0.084, -0.206, -0.0915, sides=8, bev=0.008)   # (ends at the receiver's front face)
    # ---- the receiver: olive sides with a dark inset each side, a charcoal top (split off the one solid)
    rec = soft(prism(outline([(-0.092, -0.078, 'c'), (0.168, -0.078, 'c'), (0.2, -0.05, 'c'), (0.2, 0.048, 'c'),
                              (0.182, 0.07, 'c'), (-0.092, 0.07, 'c')]), 0.144), 0.011, seg=1)
    rec = cut(rec, *pockets(-0.06, 0.165, -0.054, 0.044, 0.014, 0.072, 0.0045))
    rest, inset = split(rec, inset_test(0.072, -0.06, 0.165, -0.054, 0.044))
    olive, top = split(rest, lambda c, n: n.y > 0.95 and c.y > 0.065)
    g.put('body_wzA__body', olive); g.put('body_wzN__dark', inset); g.put('body_wzB__deck', top)
    # the drive motor on the right side (third person), its end cap
    g.cylz('motor_wzB__frame', 0.034, 0.005, 0.15, x=0.074, y=0.004, sides=8, bev=0.005)
    g.cylz('motor_wzB__dark', 0.026, 0.148, 0.162, x=0.074, y=0.004, sides=8, bev=0.003)
    # ---- the carry handle (a bridge on two legs sunk into the top): the hat's seat
    hd = soft(cut(prism(outline(rrect(-0.075, 0.148, 0.062, 0.15, 0.02)), 0.03),
                  prism(outline(rrect(-0.048, 0.121, 0.04, 0.123, 0.012)), 0.06)), 0.005, seg=1)
    g.put('handle_wzB__dark', hd)
    # ---- the ammo box: fat, olive, a dark inset each side, a charcoal lid lip and latch; it hangs under the receiver
    bx_ = soft(prism(outline(rrect(-0.09, 0.06, -0.252, -0.074, 0.014)), 0.15), 0.008, seg=1)
    bx_ = cut(bx_, *pockets(-0.07, 0.04, -0.234, -0.12, 0.012, 0.075, 0.0035))
    box_rest, box_in = split(bx_, inset_test(0.075, -0.07, 0.04, -0.234, -0.12))
    g.put('box_wzA__body', box_rest); g.put('box_wzN__dark', box_in)
    g.box('box_wzN__frame', (-0.079, 0.079), (-0.11, -0.088), (-0.094, 0.064), bev=0.004)   # (its top chamfer 4 mm off the box's)
    g.box('box_wzN__frame', (-0.017, 0.017), (-0.138, -0.1), (-0.098, -0.084), bev=0.003)
    # ---- the front grip (fore) under the housing on a clamp block; the pistol grip, guard and trigger at the back
    g.put('fore_wzB__dark', soft(prism(outline([(-0.168, -0.08, 'c'), (-0.132, -0.08, 'c'), (-0.134, -0.2, 0.012),
                                                (-0.17, -0.2, 0.012)]), 0.032), 0.006, seg=1))
    g.box('fore_wzB__frame', (-0.022, 0.022), (-0.094, -0.07), (-0.178, -0.122), bev=0.004)
    g.put('grip_wzB__dark', soft(prism(raked(0.146, -0.138, 0.15, 0.044, -0.22, taper=0.004), 0.04), 0.007, seg=1))
    g.box('guard_wzB__frame', (-0.011, 0.011), (-0.128, -0.11), (0.054, 0.13), bev=0.004)
    g.prism('trigger_wzN__steel', [(0.085, -0.074), (0.103, -0.074), (0.099, -0.108), (0.09, -0.108)], 0.012, bev=0.002)
    g.spots = {'muzzle': (0.0, 0.0, -0.75), 'grip': (0.0, -0.13, 0.143), 'fore': (0.0, -0.14, -0.15)}
    g.hat = ((0.0, 0.15, 0.036), 0.1)
    return g.done()


# ================================================================================================= the water pistol
def water():
    """THE WATER PISTOL (see the file's header)"""
    gunkit.use_style('B')
    g = Batch('w_water')
    g.slot('body', 'a7adb5'); g.slot('frame', FRAME); g.slot('accent', '3f78a3'); g.slot('black', BLACK)
    g.slot('glass', 'd3e4ee', 'g', 0.28); g.slot('water', '4a98cc')
    BY, SY, SZ = 0.01, 0.136, 0.09
    # ---- the shell: a saddle for the tank (y 0.0465, 3.5 mm under the tank's inner floor), the rear hump the notch
    # stands on, a dark inset each side, two domed screws
    sh = soft(prism(outline([(-0.125, -0.02, 0.008), (-0.125, 0.0465, 0.004), (0.04, 0.0465, 0.004), (0.05, 0.12, 0.012),
                             (0.136, 0.12, 0.02), (0.152, 0.07, 0.02), (0.125, -0.036, 0.01), (-0.03, -0.036, 0.01)]), 0.056),
              0.008, seg=3)
    sh = cut(sh, *pockets(-0.105, 0.012, -0.024, 0.032, 0.01, 0.028, 0.003), *pockets(0.064, 0.122, 0.058, 0.104, 0.01, 0.028, 0.003))
    rest, inset = split(sh, lambda c, n: abs(n.x) > 0.95 and abs(c.x) < 0.027)
    g.put('body_wzA__body', rest); g.put('body_wzN__frame', inset)
    for z, y in ((0.028, -0.017),):
        g.put('body_wzN__frame', capsule(0.0042, (-0.0302, y, z), (0.0302, y, z), seg=12, rings=8))
    # the barrel housing, the strut up to the tank's front cap, the pump's tube and its front bracket
    g.put('body_wzA__body', soft(cyl(0.026, (0, BY, -0.236), (0, BY, -0.1), sides=20), 0.004, seg=2))
    g.put('body_wzA__body', soft(prism(outline(rrect(-0.2, -0.188, 0.025, 0.05, 0.002)), 0.022), 0.002, seg=2))
    g.put('body_wzA__body', soft(cyl(0.011, (0, -0.042, -0.262), (0, -0.042, -0.12), sides=16), 0.002, seg=2))
    g.put('body_wzA__body', soft(prism(outline(rrect(-0.266, -0.25, -0.052, 0.006, 0.004)), 0.02), 0.002, seg=2))
    # the nozzle (blue): a flange on the barrel, a cone, a bore with a dark plug 4 mm in
    noz = lathe([(0.0105, -0.29), (0.012, -0.285), (0.0165, -0.262), (0.022, -0.247), (0.029, -0.245), (0.029, -0.232),
                 (0.022, -0.228)], segs=20, cy=BY)
    g.put('nozzle_wzN__accent', soft(cut(noz, cyl(0.0042, (0, BY, -0.3), (0, BY, -0.282), sides=12)), 0.0015, seg=2))
    g.put('nozzle_wzN__black', cyl(0.004, (0, BY, -0.286), (0, BY, -0.281), sides=12))
    # ---- the tank: a clear rounded shell, blue end caps, a filler cap; the liquid (node `water`) inside
    ob = xprism(outline(rrect(-0.034, 0.034, 0.047, 0.117, 0.018)), -0.19, 0.035)
    g.put('tank_wzN__glass', cut(ob, xprism(outline(rrect(-0.031, 0.031, 0.050, 0.114, 0.015)), -0.2, 0.045)))
    for z0, z1 in ((-0.205, -0.183), (0.028, 0.05)):
        g.put('tank_wzB__accent', soft(xprism(outline(rrect(-0.038, 0.038, 0.043, 0.121, 0.021)), z0, z1), 0.004, seg=2))
    g.put('tank_wzB__accent', soft(cyl(0.011, (0, 0.111, -0.008), (0, 0.127, -0.008), sides=16), 0.002, seg=2))
    WF = 0.0545
    g.put('water_wzN__water', xprism(outline(rrect(-0.0285, 0.0285, WF, 0.104, 0.0125)), -0.181, 0.026))   # (full: 1 cm of air above)
    g.origins['water'] = (0.0, WF, -0.0775)
    # ---- the pump (node `pump`): a ribbed blue sleeve round its tube
    prof = [(0.017, -0.248)]
    for z in (-0.245, -0.224, -0.203, -0.182):
        prof += [(0.021, z), (0.021, z + 0.007), (0.024, z + 0.009), (0.024, z + 0.016), (0.021, z + 0.018)]
    prof += [(0.021, -0.172), (0.017, -0.169)]
    g.put('pump_wzB__accent', soft(lathe(prof, segs=20, cy=-0.042), 0.0012, seg=2))
    g.origins['pump'] = (0.0, -0.042, -0.2085)
    # ---- the grip, the guard (a dark loop under the shell), the blue trigger
    g.put('grip_wzB__frame', soft(prism(outline([(0.052, -0.03, 'c'), (0.13, -0.03, 'c'), (0.138, -0.06, 's'), (0.152, -0.115, 's'),
                                                 (0.158, -0.148, 0.016), (0.096, -0.16, 0.02), (0.084, -0.12, 's'), (0.071, -0.098, 's'),
                                                 (0.066, -0.076, 's'), (0.054, -0.052, 's')]), 0.052), 0.012, seg=3))
    gd = cut(prism(outline(rrect(-0.036, 0.058, -0.088, -0.026, 0.018)), 0.016),
             prism(outline(rrect(-0.024, 0.046, -0.076, -0.01, 0.01)), 0.04))
    g.put('guard_wzB__frame', soft(gd, 0.003, seg=2))
    g.put('trigger_wzN__accent', soft(prism(outline([(0.004, -0.03, 'c'), (0.02, -0.03, 'c'), (0.016, -0.05, 's'),
                                                     (0.019, -0.068, 0.003), (0.009, -0.068, 0.003), (0.004, -0.05, 's')]), 0.01), 0.0015, seg=2))
    # ---- toy sights on the aim line: a chunky notch on the hump, a blade on the tank's front cap
    SG.notch(g, 'sight_wzN__frame', 0.08, SY, 0.119, 0.03, depth=0.012, nw=0.34, nd=0.0075, c=0.003)
    SG.blade(g, 'sight_wzN__frame', -0.194, SY, 0.1195, w=0.008, depth=0.012)
    g.spots = {'muzzle': (0.0, 0.01, -0.29), 'sight': (0.0, SY, SZ), 'grip': (0.0, -0.09, 0.108)}
    g.hat = ((0.0, 0.12, 0.115), 0.05)    # (behind the notch, 4 mm clear of it)
    return g.done()


# ================================================================================================= the nail gun
def nailgun():
    """THE NAIL GUN (see the file's header)"""
    gunkit.use_style('B')
    g = Batch('w_nailgun')
    g.slot('body', '86573d'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('alu', '8e949d')
    g.slot('steel', 'b5bbc4'); g.slot('black', BLACK); g.slot('deck', DECK)
    DY, SY, SZ = 0.097, 0.1744, 0.1324
    # ---- the housing (the tool's head): a rounded-box section (superellipse), muted orange with a dark inset each side;
    # charcoal end caps (the rear one, under the eye, with a lighter top: the notch stands on it)
    def ring_(a, b, z, e=4.0, n=32):
        return [(a * math.copysign(abs(math.cos(t)) ** (2 / e), math.cos(t)), DY + b * math.copysign(abs(math.sin(t)) ** (2 / e), math.sin(t)), z)
                for t in (2 * math.pi * i / n for i in range(n))]
    hs = loft([ring_(0.052, 0.058, -0.205), ring_(0.056, 0.062, -0.197), ring_(0.056, 0.062, 0.075), ring_(0.053, 0.06, 0.09)])
    hs = cut(hs, *pockets(-0.165, 0.045, DY - 0.03, DY + 0.03, 0.012, 0.056, 0.0035))
    rest, inset = split(hs, lambda c, n: abs(n.x) > 0.95 and abs(c.x) < 0.0545)
    g.put('body_wzA__body', rest); g.put('body_wzN__dark', inset)
    g.put('body_wzB__frame', loft([ring_(0.036, 0.04, -0.231), ring_(0.05, 0.056, -0.226), ring_(0.058, 0.064, -0.218),
                                   ring_(0.06, 0.066, -0.19)]))
    rc = loft([ring_(0.06, 0.066, 0.07), ring_(0.06, 0.066, 0.104), ring_(0.055, 0.061, 0.116), ring_(0.044, 0.049, 0.126),
               ring_(0.026, 0.03, 0.132)], tip=(0.0, DY, 0.134))
    rc, rtop = split(rc, lambda c, n: n.y > 0.75)
    g.put('cap_wzB__frame', rc); g.put('cap_wzB__deck', rtop)
    # ---- the nose under the drum's front, the narrower driver guide (a dark bore), the steel contact-safety yoke
    g.put('nose_wzB__frame', soft(prism(outline([(-0.16, 0.07, 'c'), (-0.29, 0.064, 0.006), (-0.333, 0.059, 0.004),
                                                 (-0.333, 0.016, 0.004), (-0.3, 0.008, 0.006), (-0.16, 0.004, 'c')]), 0.046), 0.004, seg=2))
    guide = prism(outline(rrect(-0.348, -0.326, 0.025, 0.055, 0.003)), 0.03)
    g.put('nose_wzB__frame', soft(cut(guide, cyl(0.006, (0, 0.04, -0.36), (0, 0.04, -0.338), sides=12)), 0.0015, seg=2))
    g.put('nose_wzN__black', cyl(0.0057, (0, 0.04, -0.344), (0, 0.04, -0.338), sides=12))
    ring = cut(xprism(outline(rrect(-0.02, 0.02, 0.0185, 0.0615, 0.007)), -0.358, -0.346),
               xprism(outline(rrect(-0.0128, 0.0128, 0.0258, 0.0542, 0.004)), -0.37, -0.34))
    g.put('tip_wzN__steel', soft(ring, 0.0012, seg=2))
    for sx in (-1, 1):
        g.put('tip_wzN__steel', soft(prism(outline(rrect(-0.352, -0.3335, 0.034, 0.046, 0.002)), 0.006, x=sx * 0.0185), 0.001, seg=1))
    # ---- the handle, its foot, the air fitting, the trigger
    hd = soft(prism(raked(0.048, -0.066, 0.22, 0.05, -0.2, taper=0.004), 0.05), 0.012, seg=3)
    hd = cut(hd, *[prism(raked(0.05, -0.08, 0.15, 0.024, -0.2), 0.0235, x=sx * (0.025 - 0.0035 + 0.01175)) for sx in (-1, 1)])
    hrest, hin = split(hd, lambda c, n: abs(n.x) > 0.95 and abs(c.x) < 0.024)
    g.put('grip_wzA__body', hrest); g.put('grip_wzN__dark', hin)
    g.put('foot_wzB__frame', soft(prism(outline(rrect(-0.012, 0.105, -0.205, -0.163, 0.01)), 0.058), 0.005, seg=2))
    g.put('fitting_wzN__steel', soft(cyl(0.0085, (0, -0.184, 0.1), (0, -0.184, 0.128), sides=12), 0.0015, seg=1))
    g.put('fitting_wzN__steel', cyl(0.0125, (0, -0.184, 0.1), (0, -0.184, 0.112), sides=6))
    g.prism('trigger_wzN__frame', [(-0.023, 0.04), (0.0, 0.04), (-0.006, -0.008), (-0.017, -0.008)], 0.014, bev=0.003)
    # ---- the magazine track: a slanted aluminium channel from the nose to the foot, a window through it; in it the nail
    # strip (node `mag`): nails along -z, their heads in the track's rail, two collation bands across them
    H0, H1 = Vector((-0.245, 0.028)), Vector((-0.004, -0.168))      # (z, y) the first and the last nail head
    d = (H1 - H0); L = d.length; dh = d / L
    Ln, MT, MH = 0.062, 0.008, 0.006
    def at(u, dz): q = H0 + dh * u; return (q.x + dz, q.y)
    trk = prism(outline([at(0, -Ln - MT) + (0.004,), at(0, MH) + (0.004,), at(L + 0.016, MH) + (0.006,),
                         at(L + 0.016, -Ln - MT) + (0.006,)]), 0.032)
    win = prism(outline([at(0.075, -Ln - 0.004) + (0.004,), at(0.075, -0.0005) + (0.004,), at(L - 0.022, -0.0005) + (0.004,),
                         at(L - 0.022, -Ln - 0.004) + (0.004,)]), 0.06)
    g.put('magtrack_wzB__alu', soft(cut(soft(trk, 0.003, seg=2), win), 0.0012, seg=1))
    N = int(L / 0.0095) + 1
    for i in range(N):
        hz, hy = at(L * i / (N - 1), 0.0)
        # (a corner up, so no nail face lies level with the track's flat faces)
        g.cyl('mag_wzN__steel', 0.005, (0, hy, hz + 0.0015), (0, hy, hz - 0.0015), sides=10, bev=0, flat=False)
        g.cyl('mag_wzN__steel', 0.0025, (0, hy, hz - 0.001), (0, hy, hz - Ln + 0.008), sides=6, bev=0, flat=False)
        g.cyl('mag_wzN__steel', 0.0025, (0, hy, hz - Ln + 0.008), (0, hy, hz - Ln), sides=6, bev=0, r2=0.0004, flat=False)
    for ofs in (-0.018, -0.044):
        g.put('mag_wzN__body', prism([at(0.04, ofs - 0.004), at(0.04, ofs + 0.004), at(L - 0.01, ofs + 0.004),
                                      at(L - 0.01, ofs - 0.004)], 0.012))
    mz, my = at(L / 2, -Ln / 2)
    g.origins['mag'] = (0.0, round(my, 5), round(mz, 5))
    # ---- iron sights on the aim line: the notch on the rear cap, the blade on the drum's front
    SG.notch(g, 'sight_wzN__frame', 0.093, SY, 0.162, 0.028, depth=0.012, nw=0.32, nd=0.0065)
    SG.blade(g, 'sight_wzN__frame', -0.205, SY, 0.162, w=0.006, depth=0.01)
    g.spots = {'muzzle': (0.0, 0.04, -0.358), 'sight': (0.0, SY, SZ), 'grip': (0.0, -0.06, 0.05)}
    g.hat = ((0.0, 0.159, -0.06), 0.08)
    return g.done()


# ================================================================================================= the bread
def _ellipsoid(c, along, across, depth, ang, u=20, v=10):
    """an ellipsoid cutter at c (weapon frame): `along` its long half axis, turned `ang` about y from the z axis"""
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    ca, sa = math.cos(ang), math.sin(ang)
    for vt in bm.verts:
        lx, ly, lz = vt.co.x * across, vt.co.y * depth, vt.co.z * along
        vt.co = P(c[0] + lx * ca + lz * sa, c[1] + ly, c[2] - lx * sa + lz * ca)
    return _obj(bm)


def _q(c, e):
    """where a point sits against an ellipsoid cutter: < 1 inside, 1 on it"""
    (cx, cy, cz), along, across, depth, ang = e
    dx, dy, dz = c.x - cx, c.y - cy, c.z - cz
    ca, sa = math.cos(ang), math.sin(ang)
    lx, lz = dx * ca - dz * sa, dx * sa + dz * ca
    return (lx / across) ** 2 + (dy / depth) ** 2 + (lz / along) ** 2


def bread():
    """THE BREAD (see the file's header)"""
    gunkit.use_style('B')
    g = Batch('w_bread')
    # v2 (18 Nov, the main session: "reads as a carrot or a surfboard, a smooth orange spindle"): golden-brown crust kept
    # greyer than it looks here (the hall's warm lamps push browns to orange), four deep diagonal score cuts that wrap
    # onto the sides with pale crumb and a lighter golden rim, lumps between the cuts, rounder blunt ends, a paler
    # underside. Kept: the length, the tip, grip and mid spots, and the crest at z -0.45 (the hat seat) at its height.
    g.slot('paper', 'bdb6a7'); g.slot('crust', '7a5f3e'); g.slot('side', '9a7d58'); g.slot('under', 'b49c78')
    g.slot('edge', 'c2a676'); g.slot('crumb', 'dccdab')
    HW, TOP, BOT = 0.105, 0.09, -0.07            # the loaf's full half width, top, bottom
    hh = (0.034, 0.032, -0.028)                  # the heel inside the sleeve
    CUTS = (-0.66, -0.86, -1.06, -1.245)         # the score cuts' centres (none near the hat's crest at -0.45)
    LUMPS = (-0.765, -0.96, -1.15)               # the puffed crust between them
    def lumps(z, k):
        up = sum(math.exp(-((z - c) / 0.055) ** 2) for c in LUMPS)
        dn = sum(math.exp(-((z - c) / 0.04) ** 2) for c in CUTS)
        return 1.0 + k * (up - 0.8 * dn)
    def env(z):
        if z >= -0.07: return hh
        if z >= -0.26:                           # the rounded back end of the loaf, gathered into the sleeve
            t = (-0.07 - z) / 0.19; s = math.sqrt(max(0.0, 1 - (1 - t) ** 2))
            return tuple(a + (b - a) * s for a, b in zip(hh, (HW, TOP, BOT)))
        bulge = 1.0 + 0.025 * math.sin(math.pi * min(1.0, max(0.0, (-0.43 - z) / 0.77)))
        f = 1.0
        if z < -1.3:                             # the blunt rounded nose: a quarter ellipse to the tip at -1.50
            t = min(1.0, (-1.3 - z) / 0.2); f = math.sqrt(max(0.0, 1 - t * t))
        return (HW * bulge * f * lumps(z, 0.035), TOP * bulge * f * lumps(z, 0.06), BOT * f)
    def sec(z, n=28):
        hw, top, bot = env(z)
        out = []
        for i in range(n):
            a = 2 * math.pi * i / n
            c, s = math.cos(a), math.sin(a)
            x = hw * math.copysign(abs(c) ** (2 / 2.6), c)
            y = top * abs(s) ** (2 / 2.2) if s >= 0 else -abs(bot) * abs(s) ** (2 / 4.0)   # (a dome over a flat base)
            out.append((x, y, z))
        return out
    zs = ([0.03 - 0.1 * i / 3 for i in range(4)] + [-0.07 - 0.19 * (1 - (1 - i / 10) ** 1.5) for i in range(1, 11)] +
          [-0.26 - 1.04 * i / 32 for i in range(1, 33)] + [-1.3 - 0.197 * (1 - (1 - i / 12) ** 1.6) for i in range(1, 13)])
    loaf = loft([sec(z) for z in zs], tip=(0.0, 0.0, -1.50))
    # four diagonal score cuts across the top (turned 40 degrees): each a shallow wide oval ledge (the lighter golden
    # rim where the crust opened) round a deep narrow slot (the pale crumb). Two cutters, so both outlines are clean
    # ovals of the mesh itself (choosing rim faces one by one gave a jagged staircase on the long loft faces)
    E = [((0.0, env(z)[1] + 0.006, z), 0.13, 0.034, 0.034, 0.70) for z in CUTS]
    R = [((0.0, env(z)[1] + 0.012, z), 0.165, 0.052, 0.0155, 0.70) for z in CUTS]
    loaf = cut(loaf, *[_ellipsoid(*e, u=28, v=12) for e in R])
    loaf = cut(loaf, *[_ellipsoid(*e) for e in E])
    rest, crumb = split_v(loaf, lambda vs, c, n: any(all(_q(v, e) < 1.004 for v in vs) for e in E))
    rest, edge = split_v(rest, lambda vs, c, n: any(all(_q(v, e) < 1.004 for v in vs) for e in R))
    crust, side = split(rest, lambda c, n: n.y < 0.42)
    side, under = split(side, lambda c, n: n.y < -0.3)
    g.put('bread_wzB__crust', crust); g.put('bread_wzB__side', side); g.put('bread_wzB__under', under)
    g.put('bread_wzN__edge', edge); g.put('bread_wzN__crumb', crumb)
    # the paper sleeve (the grip): a faceted twelve-sided sleeve over the heel, a thin lip at its open front, gathered and
    # twisted shut at the back
    crink = [0.0, 0.7, -0.4, 0.9, -0.8, 0.3, -0.2, 0.8, -0.6]
    def ssec(z, r, twist=0.0, n=9):   # (nine sides: 40 degree folds stay crisp)
        out = []
        for i in range(n):
            a = 2 * math.pi * i / n + twist
            k = 1.0 + 0.02 * crink[i]
            out.append((r * k * math.cos(a), 0.002 + 0.93 * r * k * math.sin(a), z))
        return out
    SL = [(0.292, 0.027, 1.1), (0.281, 0.02, 0.95), (0.268, 0.0125, 0.8), (0.256, 0.024, 0.55), (0.24, 0.039, 0.3),
          (0.22, 0.0465, 0.12), (0.19, 0.0485, 0.0), (0.12, 0.0485, 0.0), (0.04, 0.0485, 0.0), (-0.04, 0.049, 0.0),
          (-0.075, 0.051, 0.0), (-0.1, 0.0555, 0.0), (-0.106, 0.0565, 0.0)]
    sl = loft([ssec(z, r, tw) for z, r, tw in SL])
    lip = loft([ssec(z, r - 0.0042) for z, r in ((-0.112, 0.0575), (-0.1, 0.0555), (-0.075, 0.051), (-0.068, 0.0505))])
    g.put('sleeve_wzA__paper', cut(sl, lip))
    grip = (0.0, 0.002, 0.12)
    tip = (0.0, 0.0, -1.45)
    g.spots = {'grip': grip, 'muzzle': tip, 'mid': mid_of(grip, tip)}
    g.hat = ((0.0, round(env(-0.39)[1], 4), -0.39), 0.12)
    return g.done()


# ================================================================================================= the hand slapper
FK = 0.010   # the fingers' fillet into each other (bigger = a shallower groove between them)


def slapper_hand():
    """the fused hand's field (weapon frame, metres): see slapper()"""
    palm = SDF.slab([(-0.474, -0.006), (-0.520, -0.034), (-0.584, -0.031), (-0.588, 0.025), (-0.530, 0.036),
                     (-0.474, 0.006)], 0.0185, 0.0165, grow=0.018)
    back = SDF.ellipsoid((0.005, 0.0, -0.54), (0.017, 0.038, 0.05))      # the back of the hand's swell (+x)
    palm = SDF.blend(palm, back, 0.010)
    # fingers: knuckle, middle and tip centres (y high = the index, beside the thumb) and their radii
    fingers = [SDF.tube([(0.001, 0.034, -0.575), (-0.001, 0.0362, -0.630), (-0.007, 0.0395, -0.6698)], (0.0137, 0.0132, 0.0136)),
               SDF.tube([(0.001, 0.0113, -0.578), (-0.001, 0.0119, -0.640), (-0.008, 0.0128, -0.6858)], (0.0142, 0.0137, 0.0141)),
               SDF.tube([(0.001, -0.0123, -0.576), (-0.001, -0.0130, -0.632), (-0.007, -0.0142, -0.6768)], (0.0137, 0.0132, 0.0135)),
               SDF.tube([(0.001, -0.0350, -0.572), (-0.001, -0.0366, -0.615), (-0.006, -0.0392, -0.6500)], (0.0123, 0.0118, 0.0121))]
    hand = SDF.blend(palm, SDF.union(*fingers, k=FK), 0.012)
    # the thumb: up out of the palm's top edge by the wrist, its tip where the hats' seat is (x -0.008, z -0.51)
    thumb = SDF.capsule((-0.002, 0.026, -0.488), (-0.0067, 0.0799, -0.5118), 0.0185, 0.0155)
    mound = SDF.ellipsoid((-0.006, 0.026, -0.505), (0.017, 0.02, 0.03))
    hand = SDF.blend(hand, SDF.blend(thumb, mound, 0.008), 0.014)
    wrist = SDF.capsule((0.0, 0.0, -0.46), (0.0, 0.0, -0.48), 0.019)   # (its back end at z -0.441, inside the cuff)
    return SDF.blend(hand, wrist, 0.012)


def slapper():
    """THE HAND SLAPPER (see the file's header)"""
    gunkit.use_style('B')
    g = Batch('w_slapper')
    g.slot('hand', 'b98895'); g.slot('cuff', 'd3d5d9'); g.slot('stick', 'b4b8be'); g.slot('grip', '3d4048')
    # ---- the hand (node `hand`, origin at the wrist): palm to -x, fingers forward, thumb up. ONE fused piece (18 Nov,
    # the owner: "fuse the fingers so its all one piece"): a signed distance field (sdf_kit) of a pillow palm, four
    # fingers pressed together with a slight curl to the palm side, a thumb with a fat root and a wrist, every join a
    # smooth union (the fingers FK into each other, leaving a shallow round groove between them; the palm and thumb
    # 12-14 mm), meshed once and decimated: no finger primitives stuck on a block
    g.pieces[('hand_wzB', 'hand')] = SDF.mesh(slapper_hand(), (-0.03, -0.062, -0.712), (0.03, 0.106, -0.424),
                                             h=0.0011, tris=3200, name='slap_hand')
    g.put('hand_wzN__cuff', soft(lathe([(0.0, -0.436), (0.021, -0.436), (0.0285, -0.4395), (0.032, -0.446), (0.0325, -0.455),
                                        (0.031, -0.465), (0.027, -0.472), (0.0, -0.472)], segs=20), 0.0015, seg=2))
    g.origins['hand'] = (0.0, 0.0, -0.45)
    # ---- the stick, the ribbed grip, the end knob
    g.put('stick_wzA__stick', cyl(0.0135, (0, 0, -0.455), (0, 0, 0.002), sides=16))
    prof = [(0.0145, -0.016), (0.02, -0.01), (0.0215, 0.0)]
    for z in (0.0, 0.024, 0.048, 0.072):
        prof += [(0.0215, z + 0.012), (0.0195, z + 0.016), (0.0195, z + 0.024)]
    prof += [(0.0215, 0.1), (0.0225, 0.114), (0.0225, 0.12)]
    g.put('grip_wzA__grip', soft(lathe(prof, segs=20), 0.001, seg=1))
    g.put('cap_wzN__hand', ball(0.023, (0.0, 0.0, 0.13), sub=2))
    grip = (0.0, 0.0, 0.055)
    tip = (0.0, 0.0, -0.70)
    g.spots = {'grip': grip, 'muzzle': tip, 'mid': mid_of(grip, tip)}
    g.hat = ((0.0, 0.049, -0.57), 0.06)   # (on the palm's top edge, ahead of the thumb)
    return g.done()


BUILD = {'minigun': minigun, 'water': water, 'nailgun': nailgun, 'bread': bread, 'slapper': slapper}
