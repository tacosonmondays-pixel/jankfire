# THE SCYTHE IN TWO FORMS, v3 (18 Nov 2026). The Scythe "is a sniper too" (the owner): one weapon, two kit models from
# this one builder, the same scale and the same grip origin (0, 0, 0):
#   - SCYTHE  w_scythe (melee, `scythe`): a reaper scythe whose haft is a vented barrel shroud and whose middle is a gun
#             action, so it reads as a weapon both ways.
#   - RIFLE   w_scythe_rifle (`scythe_rifle`): the same model with two nodes moved (the weapons session's design,
#             Weapons.luau scythe mdl.parts.form): the BLADE slides down the haft to behind the grip and turns on its
#             edge to become the STOCK, nesting in the heel; a short SCOPE comes up out of the receiver; the teal COLLAR,
#             between the head socket and the brake, is the muzzle ring.
# v3 (the main session's review of v831: "a long bare stick with a box and a blade" / "a stick with a scope"): a thicker
# haft that is a vented shroud with steel ferrules, a receiver that reads as an action (ejection port with the bolt in
# it, a bolt handle, a trigger in a guard), a chunky head socket with a ported brake, a blade with a spine ridge, a wide
# ground band and a heavy tang, a heel shaped as the stock's wrist that the blade nests into. Every join is a flare, a
# fillet ring or a rounded transition (lathe profiles; unions bevelled after), never two primitives butted together.
# Original: no red and black, no gun under the blade, no blade folding forward along a barrel. Quiet kit style (look B):
# dark haft, charcoal parts, steel blade with a lighter ground edge, steel ferrules, the teal collar the ONE accent.
#   blender -b --factory-startup -P tools/roblox/gun_set.py -- <out> scythe scythe_rifle
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- scythe scythe_rifle
#   JF_NOZFIX=1 blender -b --factory-startup -P tools/roblox/gun_zfix.py -- scythe scythe_rifle      (0 pairs)
# STATIC (identical in both models), front to back along the haft (z):
#   brake (-1.38 .. -1.338, charcoal, two ports a side, the dark bore: the rifle's muzzle at its face z -1.38), the teal
#   collar (-1.336 .. -1.313), the head socket (-1.31 .. -1.19, charcoal, r 0.037: the blade's mouth on its upper left),
#   a steel ferrule, the vented shroud (r 0.0265, 4 rows of 6 slots), a steel ferrule, the ribbed fore band round -0.45,
#   a flare into the RECEIVER (-0.402 .. -0.052: the scope's channel along its top with light rims, the ejection port
#   with the bolt on the left side (the side first person sees), the bolt handle behind it, a dark inset on the right,
#   the trigger guard and trigger under its back), a flare out of it, the ribbed grip wrap round (0, 0, 0), a steel
#   ferrule, a flare into the HEEL (0.086 .. 0.214: the stock's wrist, a slot along it the blade's root nests in, its
#   flat top the hat seat).
# MOVING (only two nodes, the same names and the same meshes in both models; only their placement differs):
#   - blade  (blade_wzB__steel, blade_wzB__tang, blade_wzN__edge): scythe: out to the left (-x) from the socket, edge
#            forward (-z), on its flat. rifle: on its edge (spine up, edge down), its tang in the heel's slot, the tip at
#            z 0.826: the stock. x_rifle = TURN_R x_scythe + (BLADE_T - TURN_R BLADE_C): CFrame (0.02, 1.23, 0.126,
#            0,-1,0, 0,0,1, -1,0,0) about its root BLADE_C (0.012, 0.02, -1.218) -> BLADE_T (0, 0.012, 0.114).
#   - scope  (scope_wzB__frame, scope_wzB__dark, scope_wzN__glass, scope_wzN__deck): a short scope on two ring mounts
#            that slide in the receiver's channel. scythe: sunk in the channel, its top under the rim. rifle: up 0.0645
#            (about (0, 0.013, -0.24) -> (0, 0.0775, -0.24)), the mounts' feet still 8 mm in the channel.
#   (the same numbers as v831: the weapons session's rows hold them)
# CONTRACT: spots grip (0, 0, 0) and fore (0, 0, -0.45) in both (the hands never move); scythe: mid (-0.3, 0.02, -1.25),
# muzzle (-0.7, 0.02, -1.16) at the blade tip; rifle: mid (0, 0, -0.6), muzzle (0, 0, -1.38) at the brake's face, sight
# (0, 0.0775, -0.072) at the eyepiece (the aim line). The notes carry `pivots` (each moving node's origin in that model),
# `hatAt` (the same in both: the heel's top) and `form` (the other model's key, the moving nodes and each one's move).
# Zones: the haft _wzA; the blade, the scope, the head, the receiver and the heel _wzB; the collar, the wraps, the
# ferrules, the bore, the vents, the insets, the port, the action, the trigger, the edge, the lenses and the light
# rings _wzN. Flat kit colours (Batch export, no bake). Flicker: no flat faces of two looks facing one way within the
# rack's 0.02 studs (round parts have no face square to a flat one: their facets sit half a step off the axes).
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import gunkit
from gunkit import P
from artist_kit import outline, rrect, prism, xprism, cyl, soft, cut, union, oprism, capsule, to_mesh, _obj
from gun_melee import split, lathe, loft, catmull, interp, ball
from gun_batch_a import Batch

FRAME, DARK, BLACK, DECK = '444851', '353840', '16171b', '676d78'
HAFT, WRAP, TEAL, STEEL, EDGE, TANG, GLASS = '3c3734', '232429', '3ee6c8', '98a0aa', 'c8ced6', '6b727c', '2a343c'

# ---- the motion (kept from v831: Weapons.luau scythe / scythe_rifle mdl.parts.form)
TURN_R = Matrix(((0, -1, 0), (0, 0, 1), (-1, 0, 0)))   # (x, y, z) -> (-y, z, -x): flat -> on its edge, along +z
BLADE_C = Vector((0.012, 0.02, -1.218))   # the blade's root: its spine corner on the root face, on the centre plane
BLADE_T = Vector((0.0, 0.012, 0.114))     # ... in the rifle
AXIS_S, SCOPE_UP, SCOPE_Z = 0.013, 0.0645, -0.24       # the scope's axis (scythe), its rise, its middle
AXIS_R = AXIS_S + SCOPE_UP

# ---- the haft and the head (metres, weapon frame)
SR = 0.0265                     # the shroud's radius
BF = -1.38                      # the brake's face (the rifle's muzzle)
# ---- the receiver and the scope's channel
ZF, ZB = -0.402, -0.052         # the receiver's front and back faces
RIM, XS, CH = 0.036, 0.034, 0.0235    # its top, its half width, the channel's half width
R_OBJ, R_TUBE, R_EYE = 0.022, 0.0135, 0.0185
FOOT_S = -0.0365                # the mounts' feet in the scythe (rifle: RIM - 0.008)
FLOOR = FOOT_S - 0.002          # the channel's floor
SF, SE = -0.383, -0.072         # the scope's objective face and eyepiece face
# ---- the heel
HZ0, HTOP, HX = 0.086, 0.03, 0.031
HAT = ((0.0, HTOP, 0.122), 0.09)   # on the heel's flat top (s = 0.09 / 0.12 = 0.75)

B = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))    # weapon frame -> Blender (gunkit.P)

# the blade's outline (scythe pose, the x-z plane at y 0.02): its ground edge (forward, -z) and its spine (back, +z)
EDGE_C = catmull([(0.012, -1.262), (-0.06, -1.318), (-0.2, -1.366), (-0.35, -1.378), (-0.5, -1.348), (-0.62, -1.272), (-0.70, -1.16)], n=10)[::-1]
SPINE_C = catmull([(0.012, -1.218), (-0.15, -1.234), (-0.3, -1.2455), (-0.45, -1.236), (-0.6, -1.203), (-0.70, -1.16)], n=10)[::-1]
Y0 = 0.02
TANG_X = -0.062                  # the tang's colour line (the thick root: from x -0.09 the blade thickens to it)


def wmat(R, t):
    """a weapon-frame move x' = R x + t as a 4x4 matrix in Blender's frame"""
    M = (B @ R @ B.transposed()).to_4x4()
    M.translation = B @ Vector(t)
    return M


def blade_move(s=1.0):
    """the blade's move s of the way from the scythe to the rifle, turning about its root while the root slides along
       (the picture's in-between; s = 1 is the rifle exactly): (R, t) with x' = R x + t, weapon frame"""
    ax, ang = TURN_R.to_quaternion().to_axis_angle()
    R = Matrix.Rotation(ang * s, 3, ax)
    root = BLADE_C.lerp(BLADE_T, s)
    return R, root - R @ BLADE_C


def scope_move(s=1.0):
    return Matrix.Identity(3), Vector((0.0, SCOPE_UP * s, 0.0))


class TwoForm(Batch):
    """a Batch gun whose moving nodes are exported as the SAME local mesh in both models, each under its own node
       transform (place: node -> weapon-frame (R, t) from its scythe pose), and whose notes carry the form move"""
    def __init__(self, name, form):
        super().__init__(name)
        self.form = form
        self.place = {}     # node -> (R, t): this model's placement of the node's scythe-pose mesh
        self.pivot0 = {}    # node -> the node's origin in the scythe pose (weapon frame)

    def move_nodes(self, moves):
        """apply {node: (R, t)} to the built pieces (weapon frame); remember the placement"""
        for (node, slot), bm in self.pieces.items():
            base = node.split('_wz')[0]
            if base in moves:
                R, t = moves[base]
                bm.transform(wmat(R, t))
                bm.normal_update()
        for base, (R, t) in moves.items():
            self.place[base] = (R, t)
            self.origins[base] = tuple(round(v, 5) for v in (R @ Vector(self.pivot0[base]) + t))

    def export(self, out_dir):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        objs = self.to_scene()
        for o in objs:
            base = o.name.split('.')[0].split('_wz')[0]
            if base in self.pivot0:
                R, t = self.place.get(base, (Matrix.Identity(3), Vector((0, 0, 0))))
                # the node's own mesh: its scythe pose about its scythe origin (the same numbers in both files)
                M = wmat(R, t) @ Matrix.Translation(P(*self.pivot0[base]))
                o.data.transform(M.inverted())
                o.matrix_world = M
        root = bpy.data.objects.new(self.name, None)
        bpy.context.scene.collection.objects.link(root)
        lo, hi = self.bounds()
        meta = {'kind': 'weapon', 'id': self.name[2:], 'set': 'kit', 'lo': lo, 'hi': hi, 'spots': self.spots,
                'pivots': {k: [round(v, 5) for v in at] for k, at in self.origins.items()},
                'hatAt': [[round(v, 4) for v in self.hat[0]], self.hat[1]], 'hat_size': self.hat[1],
                'form': form_notes(self.form)}
        root['jf'] = json.dumps(meta)
        for o in objs: o.parent = root
        path = os.path.join(out_dir, self.name + '.glb')
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=False, export_apply=True,
                                  export_animations=False, export_yup=True, export_extras=True,
                                  export_vertex_color='NONE')
        return path, lo, hi, self.tris(), len(self.pieces)


def form_notes(form):
    """the move of each moving node from this model's pose to the other's: p_other = pivot + rot(axis, deg)(p - pivot)
       + move, and the same as a CFrame (x, y, z, R00 .. R22) in model space (p_other = cf * p)"""
    out = {'other': 'scythe_rifle' if form == 'scythe' else 'scythe', 'nodes': ['blade', 'scope'], 'turn': {}}
    for node, (R, t), piv in (('blade', blade_move(), BLADE_C), ('scope', scope_move(), Vector((0.0, AXIS_S, SCOPE_Z)))):
        if form != 'scythe':   # (from the rifle: the inverse)
            R, t = R.transposed(), -(R.transposed() @ t)
            piv = TURN_R @ piv + blade_move()[1] if node == 'blade' else piv + scope_move()[1]
        ax, ang = R.to_quaternion().to_axis_angle()
        mv = (R @ piv + t) - piv
        out['turn'][node] = {'pivot': [round(v, 5) for v in piv], 'axis': [round(v, 5) for v in ax],
                             'deg': round(math.degrees(ang), 3), 'move': [round(v, 5) for v in mv],
                             'cf': [round(v, 5) for v in t] + [round(R[i][j], 5) for i in range(3) for j in range(3)]}
    return out


# ================================================================================================= helpers
def ribs(z0, z1, n, hi, lo):
    """a ribbed band's profile [(r, z)]: n ribs of radius hi with grooves of radius lo, each rib's edges rounded"""
    out, step = [], (z1 - z0) / n
    for k in range(n):
        a = z0 + k * step
        out += [(hi, a + 0.0015), (hi, a + step - 0.004), (lo, a + step - 0.0025), (lo, a + step - 0.0005)]
    return out


def alathe(prof, a, d, segs=16, turn=0.0):
    """a profile [(r, t)] turned about the line a + t d (weapon frame): an end with r 0 closes on the axis"""
    a = Vector(a); d = Vector(d).normalized()
    up = Vector((1, 0, 0)) if abs(d.x) < 0.9 else Vector((0, 1, 0))
    u = (up - d * d.dot(up)).normalized(); v = d.cross(u)
    bm = bmesh.new()
    rings = []
    for r, t in prof:
        c = a + d * t
        if r < 1e-7: rings.append([bm.verts.new(P(*c))])
        else: rings.append([bm.verts.new(P(*(c + (u * math.cos(turn + 2 * math.pi * i / segs) + v * math.sin(turn + 2 * math.pi * i / segs)) * r)))
                            for i in range(segs)])
    for A, Bv in zip(rings, rings[1:]):
        if len(A) == 1 and len(Bv) == 1: continue
        for i in range(segs):
            j = (i + 1) % segs
            if len(A) == 1: bm.faces.new([A[0], Bv[j], Bv[i]])
            elif len(Bv) == 1: bm.faces.new([A[i], A[j], Bv[0]])
            else: bm.faces.new([A[i], A[j], Bv[j], Bv[i]])
    if len(rings[0]) > 1: bm.faces.new(rings[0])
    if len(rings[-1]) > 1: bm.faces.new(rings[-1][::-1])
    return _obj(bm)


def side_box(z0, z1, y0, y1, r, x_face, depth):
    """a pocket cutter let in `depth` from the side face at x = x_face (its sign picks the side)"""
    s = 1 if x_face > 0 else -1
    return prism(outline(rrect(z0, z1, y0, y1, r)), depth + 0.02, x=s * (abs(x_face) - depth + (depth + 0.02) / 2))


def rad(c): return math.hypot(c.x, c.y)


# ================================================================================================= the static parts
def front(g):
    """the brake, the teal collar, the head socket, the vented shroud with its ferrules and the fore band: one lathe,
       every step between them a rounded transition, split by colour; the blade's mouth, the brake's ports and the
       shroud's vents cut into it"""
    p = [(0.0, BF + 0.03), (0.0085, BF + 0.03), (0.0085, BF + 0.003), (0.0108, BF), (0.0225, BF), (0.0262, BF + 0.0015),
         (0.0285, BF + 0.005), (0.0285, -1.343), (0.027, -1.3395), (0.0262, -1.337)]                      # brake
    p += [(0.0285, -1.3355), (0.032, -1.334), (0.0335, -1.3305), (0.0335, -1.3185), (0.032, -1.315), (0.0285, -1.3135)]   # collar
    p += [(0.0272, -1.312), (0.0305, -1.3105), (0.035, -1.3075), (0.037, -1.3025), (0.037, -1.214), (0.0355, -1.2075),
          (0.0325, -1.2015), (0.0298, -1.195)]                                                              # head socket
    p += [(0.0292, -1.192), (0.0305, -1.1895), (0.031, -1.1855), (0.031, -1.1765), (0.0305, -1.1725), (0.0285, -1.1695),
          (SR, -1.166)]                                                                                      # ferrule
    p += [(SR, -0.523), (0.0285, -0.5195), (0.03, -0.516), (0.03, -0.506), (0.0285, -0.5025), (0.0272, -0.5)]  # ferrule
    p += ribs(-0.4985, -0.426, 3, 0.0292, 0.0278) + [(0.0272, -0.4245), (SR, -0.423), (SR, -0.4175)]          # fore band
    p += [(0.0268, -0.414), (0.0274, -0.4105), (0.0283, -0.4065), (0.0292, -0.4025), (0.0295, -0.401),
          (0.0295, -0.396), (0.0, -0.396)]                                                                   # flare
    hf = lathe(p, segs=20)
    # the blade's mouth on the socket's upper left: the blade's own outline 1 mm out, through 1 mm over its tang
    xs = [0.013 - (0.083) * i / 11 for i in range(12)]
    mouth = [(x, interp(SPINE_C, x) + 0.0047) for x in xs] + [(x, interp(EDGE_C, x) - 0.0012) for x in xs[::-1]]
    cutters = [oprism(mouth, (0.0, Y0, 0.0), (1, 0, 0), (0, 0, 1), -0.012, 0.012)]
    # two ports a side through the brake, into the bore
    cutters += [capsule(0.0042, (-0.045, 0.0, z), (0.045, 0.0, z), seg=12, rings=6) for z in (-1.3535, -1.3665)]
    # the shroud's vents: four rows of six slots (two each side, low and high), 3.5 mm deep
    for ang in (15.0, 65.0, 115.0, 165.0):
        a = math.radians(ang); rr = SR + 0.0042 - 0.0035
        for k in range(6):
            zc = -0.585 - 0.1 * k
            cutters.append(capsule(0.0042, (rr * math.cos(a), rr * math.sin(a), zc + 0.03), (rr * math.cos(a), rr * math.sin(a), zc - 0.03),
                                   seg=8, rings=4))
    hf = cut(hf, *cutters)
    rest, bore = split(hf, lambda c, n: BF - 0.001 < c.z < -1.347 and rad(c) < 0.0092)
    rest, collar = split(rest, lambda c, n: -1.3365 < c.z < -1.3125)
    rest, head = split(rest, lambda c, n: c.z < -1.1915)
    rest, fer = split(rest, lambda c, n: c.z < -1.167 or -0.5235 < c.z < -0.4995)
    rest, band = split(rest, lambda c, n: -0.4995 < c.z < -0.4235)
    rest, flare = split(rest, lambda c, n: c.z > -0.4175)
    shroud, vent = split(rest, lambda c, n: rad(c) < 0.0259)
    g.put('haft_wzA__haft', shroud); g.put('haft_wzN__black', vent); g.put('ferrule_wzN__steel', fer)
    g.put('wrap_wzN__wrap', band); g.put('head_wzB__frame', head); g.put('collar_wzN__teal', collar)
    g.put('muzzle_wzN__black', bore); g.put('receiver_wzB__frame', flare)


def rear(g):
    """from inside the receiver's back: a flare out of it, the ribbed grip wrap round (0, 0, 0), a steel ferrule, a
       flare into the heel"""
    p = [(0.0, ZB - 0.006), (0.0278, ZB - 0.006), (0.0278, ZB + 0.001), (0.0265, ZB + 0.0045), (0.0251, ZB + 0.0085),
         (0.0243, ZB + 0.0125), (0.024, ZB + 0.016)]
    p += ribs(-0.033, 0.054, 5, 0.0272, 0.0257) + [(0.0252, 0.0555), (0.024, 0.057)]
    p += [(0.0262, 0.0595), (0.0285, 0.0625), (0.0285, 0.0725), (0.0262, 0.0755), (0.024, 0.0778)]          # ferrule
    p += [(0.0243, 0.081), (0.025, 0.0838), (0.0257, 0.0865), (0.0257, 0.094), (0.0, 0.094)]                 # flare
    hr = lathe(p, segs=20)
    rest, rflare = split(hr, lambda c, n: c.z < ZB + 0.0128)
    rest, hflare = split(rest, lambda c, n: c.z > 0.0778)
    rest, fer = split(rest, lambda c, n: c.z > 0.0566)
    haft, wrap = split(rest, lambda c, n: -0.0335 < c.z < 0.0566)
    g.put('receiver_wzB__frame', rflare); g.put('heel_wzB__frame', hflare); g.put('ferrule_wzN__steel', fer)
    g.put('haft_wzA__haft', haft); g.put('wrap_wzN__wrap', wrap)


def receiver(g):
    """the action between the hands: the body with the trigger guard and the bolt handle's boss grown out of it (one
       solid, its joins bevelled round), the scope's channel along its top, the ejection port on the left with the bolt
       in it, a dark inset on the right, the trigger in a slot inside the guard"""
    body_ = prism(outline([(ZF, -0.048, 0.012), (ZB, -0.056, 0.012), (ZB, RIM, 0.0025), (ZF, RIM, 0.0025)]), 2 * XS)
    guard = to_mesh(cut(prism(outline(rrect(-0.126, -0.06, -0.088, -0.044, 0.015)), 0.011),
                        prism(outline(rrect(-0.115, -0.071, -0.077, -0.02, 0.009)), 0.03)))
    boss = alathe([(0.0, 0.0), (0.0125, 0.0), (0.0125, 0.0045), (0.0098, 0.0085), (0.0072, 0.011), (0.0, 0.011)],
                  (-(XS - 0.0045), 0.006, -0.162), (-1, 0, 0), segs=12)
    rec = union(body_, guard, boss)
    chan = prism(outline(rrect(ZF + 0.015, ZB - 0.015, FLOOR, RIM + 0.03, 0.008)), 2 * CH)
    rec = cut(rec, chan, side_box(-0.3, -0.186, -0.014, 0.02, 0.006, -XS, 0.004),          # the ejection port (left)
              side_box(-0.37, -0.09, -0.04, 0.02, 0.008, XS, 0.003),                         # the inset (right)
              prism(outline(rrect(-0.101, -0.081, -0.075, -0.045, 0.003)), 0.009))           # the trigger's slot
    rec = soft(rec, 0.003, seg=2)
    rest, port = split(rec, lambda c, n: n.x < -0.95 and -XS + 0.001 < c.x < -CH - 0.002 and -0.302 < c.z < -0.184)
    rest, inset = split(rest, lambda c, n: n.x > 0.95 and CH + 0.002 < c.x < XS - 0.001)
    rest, deck = split(rest, lambda c, n: n.y > 0.95 and c.y > RIM - 0.0015)
    g.put('receiver_wzB__frame', rest); g.put('receiver_wzN__black', port); g.put('receiver_wzN__dark', inset)
    g.put('receiver_wzN__deck', deck)
    # the bolt in the port (its facets half a step off the side's plane), the handle: a steel stem out of the boss, a
    # dark knob
    g.put('action_wzN__steel', capsule(0.0055, (-0.0292, 0.003, -0.296), (-0.0292, 0.003, -0.19), seg=12, rings=6),
          soft(cyl(0.0046, (-(XS + 0.004), 0.006, -0.162), (-0.061, -0.013, -0.158), sides=12), 0.0012, seg=2))
    g.put('action_wzN__dark', ball(0.0105, (-0.0645, -0.0155, -0.1575), sub=2, scale=(1.0, 0.92, 0.92)))
    # the trigger, curved, out of its slot
    g.put('trigger_wzN__steel', soft(prism(outline([(-0.0855, -0.047, 'c'), (-0.096, -0.047, 'c'), (-0.0985, -0.059, 's'),
                                                     (-0.097, -0.0705, 0.002), (-0.0915, -0.0715, 0.002), (-0.0905, -0.06, 's')]),
                                           0.0066), 0.001, seg=1))


def heel(g):
    """the heel at the butt, shaped as the stock's wrist: a flat top (the hat seat) that rounds down at the back into
       the toe, a slot along its middle that follows the blade's outline in the rifle (the blade's tang nests in it)"""
    hl = prism(outline([(HZ0, HTOP, 0.0025), (0.16, HTOP, 0.02), (0.204, -0.006, 's'), (0.214, -0.058, 0.018),
                        (0.19, -0.097, 0.016), (0.128, -0.072, 's'), (HZ0, -0.042, 0.012)], step=0.013), 2 * HX)
    xs = [0.013 - 0.18 * i / 13 for i in range(14)]
    top = [(0.126 - x, interp(SPINE_C, x) + 1.23 + 0.0047) for x in xs]
    bot = [(0.126 - x, interp(EDGE_C, x) + 1.23 - 0.0012) for x in xs]
    slot = prism(top + bot[::-1], 0.024)
    # (the improvement round, from the first-person rifle view, where the heel is the nearest thing to the eye: a dark
    # rubber cheek pad let into each side, the blade's lock pin showing as a steel dome on each pad, a light top)
    pads = [side_box(0.1, 0.178, -0.05, 0.018, 0.012, sx * HX, 0.003) for sx in (-1, 1)]
    hl = soft(cut(hl, slot, *pads), 0.004, seg=2)
    rest, pad = split(hl, lambda c, n: abs(n.x) > 0.95 and 0.013 < abs(c.x) < HX - 0.001)
    rest, cap = split(rest, lambda c, n: n.y > 0.95 and c.y > HTOP - 0.0015)
    g.put('heel_wzB__frame', rest); g.put('heel_wzN__wrap', pad); g.put('heel_wzN__deck', cap)
    for sx in (-1, 1):
        g.put('pin_wzN__steel', alathe([(0.0, 0.0), (0.0088, 0.0), (0.0088, 0.002), (0.0079, 0.0036), (0.0058, 0.0049), (0.0, 0.0054)],
                                       (sx * (HX - 0.004), -0.014, 0.13), (sx, 0, 0), segs=12, turn=math.pi / 12))


# ================================================================================================= the moving parts
def blade(g):
    """the blade in the scythe pose: at y 0.02, its tang in the socket's mouth, sweeping out to the left (-x) in a broad
       crescent to the tip (-0.70, 0.02, -1.16); a raised ridge along the spine on both flats, the flats running to a
       wide lighter ground band and the edge facing forward (-z); the root thickens into a heavy dark tang"""
    N = 34
    st, ZBL = [], []
    for k in range(N):
        x = 0.012 + (-0.686 - 0.012) * (k / (N - 1)) ** 0.9
        u = min(1.0, -x / 0.7) if x < 0 else 0.0
        zs, ze = interp(SPINE_C, x), interp(EDGE_C, x)
        w = zs - ze
        q = min(1.0, max(0.0, (x + 0.09) / 0.05)); tg = q * q * (3 - 2 * q)       # (0 at x -0.09 .. 1 at -0.04)
        T = 0.0145 * (1 - 0.55 * u) + 0.0075 * tg
        bw = min(0.03 * (1 - 0.35 * u), 0.45 * w)
        zb = ze + bw
        Tb = 0.62 * T
        te = 0.0008 + 0.006 * tg
        rw = min(0.0065, 0.14 * w)
        rh = 0.0011 * (1 - 0.6 * u) * (1 - tg)
        sb = min(0.0035, 0.3 * w)
        ZBL.append((x, zb))
        top = [(zs + sb, 0.0), (zs, T / 2), (zs - rw, T / 2 + rh), (zs - 2 * rw, T / 2 - 0.0003), (zb, Tb / 2), (ze, te / 2)]
        sec = top + [(z, -y) for z, y in reversed(top[1:])]
        st.append([(x, Y0 + yy, zz) for zz, yy in sec])
    bl = loft(st, tip=(-0.70, Y0, -1.16))
    ZBL = ZBL[::-1]
    rest, tang = split(bl, lambda c, n: c.x > TANG_X)
    steel, ground = split(rest, lambda c, n: c.z < interp(ZBL, c.x) + 0.0006)
    g.put('blade_wzB__steel', steel); g.put('blade_wzB__tang', tang); g.put('blade_wzN__edge', ground)
    g.pivot0['blade'] = tuple(BLADE_C)


def scope(g):
    """the short scope in the scythe pose, sunk in the receiver's channel on its two ring mounts"""
    A = AXIS_S
    prof = [(0.0, SF + 0.004), (0.0158, SF + 0.004), (0.0158, SF), (0.019, SF), (R_OBJ, SF + 0.0025), (R_OBJ, SF + 0.029),
            (0.0208, SF + 0.0315), (0.0208, SF + 0.0345), (R_OBJ, SF + 0.037), (R_OBJ, -0.33), (0.0205, -0.3255),
            (R_TUBE, -0.311), (R_TUBE, -0.168), (0.0158, -0.1605), (R_EYE, -0.153), (R_EYE, SE - 0.0035),
            (0.0172, SE), (0.0138, SE), (0.0138, SE - 0.004), (0.0, SE - 0.004)]
    body_ = lathe(prof, segs=20, cy=A)
    def r(c): return math.hypot(c.x, c.y - A)
    rest, lens = split(body_, lambda c, n: abs(n.z) > 0.9 and ((r(c) < 0.0156 and c.z < SF + 0.0045) or (r(c) < 0.0136 and c.z > SE - 0.0045)))
    rest, ring = split(rest, lambda c, n: c.z > SE - 0.0025 and r(c) > 0.0136)   # (the eyepiece's light ring)
    g.put('scope_wzB__frame', rest); g.put('scope_wzN__glass', lens); g.put('scope_wzN__deck', ring)
    # the turrets: elevation on top, parallax on the left (the side first person sees), each on a flared base, a light cap
    tprof = [(0.0, 0.006), (0.0124, 0.006), (0.0124, 0.0112), (0.0103, 0.0138), (0.0095, 0.0158), (0.0095, 0.0196),
             (0.0088, 0.0212), (0.0, 0.0212)]
    for d in ((0, 1, 0), (-1, 0, 0)):
        tu = alathe(tprof, (0.0, A, SCOPE_Z), d, segs=12, turn=math.pi / 12)
        tside, tcap = split(tu, lambda c, n, d=d: Vector(n).dot(Vector(d)) > 0.9 and Vector((c.x, c.y - A, c.z - SCOPE_Z)).dot(Vector(d)) > 0.02)
        g.put('scope_wzB__frame', tside); g.put('scope_wzN__deck', tcap)
    # the two ring mounts: one front-view outline each, a block in the channel (1 mm off its walls) running up into a
    # clamp round the tube, its inside corners filleted, pushed along the scope
    yb, rc, hw = A - 0.0075, 0.0164, CH - 0.001
    xc = math.sqrt(rc * rc - (yb - A) ** 2)
    a0 = math.atan2(yb - A, xc)
    arc = [(rc * math.cos(a0 + (math.pi - 2 * a0) * i / 10), A + rc * math.sin(a0 + (math.pi - 2 * a0) * i / 10), 'c') for i in range(1, 10)]
    key = outline([(-hw, FOOT_S, 0.004), (hw, FOOT_S, 0.004), (hw, yb, 0.003), (xc, yb, 0.003)] + arc + [(-xc, yb, 0.003), (-hw, yb, 0.003)])
    for z0, z1 in ((-0.305, -0.277), (-0.201, -0.173)):
        g.put('scope_wzB__dark', soft(xprism(key, z0, z1), 0.002, seg=1))
    g.pivot0['scope'] = (0.0, A, SCOPE_Z)


def _build(form):
    gunkit.use_style('B')
    g = TwoForm('w_scythe' if form == 'scythe' else 'w_scythe_rifle', form)
    g.slot('haft', HAFT); g.slot('wrap', WRAP); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('teal', TEAL); g.slot('steel', STEEL); g.slot('edge', EDGE); g.slot('tang', TANG); g.slot('glass', GLASS)
    g.slot('deck', DECK)
    front(g); rear(g); receiver(g); heel(g); blade(g); scope(g)
    g.origins = {k: tuple(v) for k, v in g.pivot0.items()}
    g.hat = HAT
    if form == 'scythe':
        g.spots = {'grip': (0.0, 0.0, 0.0), 'fore': (0.0, 0.0, -0.45), 'mid': (-0.3, 0.02, -1.25), 'muzzle': (-0.7, 0.02, -1.16)}
    else:
        g.spots = {'grip': (0.0, 0.0, 0.0), 'fore': (0.0, 0.0, -0.45), 'mid': (0.0, 0.0, -0.6), 'muzzle': (0.0, 0.0, BF),
                   'sight': (0.0, round(AXIS_R, 4), SE)}
    g.done()
    if form != 'scythe':
        g.move_nodes({'blade': blade_move(), 'scope': scope_move()})
    return g


def scythe():
    """THE SCYTHE (melee pose; see the file's header)"""
    return _build('scythe')


def scythe_rifle():
    """THE SCYTHE'S RIFLE FORM (see the file's header)"""
    return _build('scythe_rifle')


def mid(s=0.5):
    """a picture's in-between: the scythe model with the blade s of the way down the haft and turned s of the way
       (about its root), the scope s of the way up (not a game model)"""
    g = _build('scythe')
    g.name = 'w_scythe_mid'
    g.move_nodes({'blade': blade_move(s), 'scope': scope_move(s)})
    return g


BUILD = {'scythe': scythe, 'scythe_rifle': scythe_rifle}
