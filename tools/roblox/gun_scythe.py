# THE SCYTHE IN TWO FORMS (18 Nov 2026). The Scythe "is a sniper too" (the owner): one weapon, two kit models from this
# one builder, the same scale and the same grip origin (0, 0, 0):
#   - SCYTHE  w_scythe (melee, `scythe`): the reaper scythe of Batch C (gun_batch_c.scythe: the same haft, wraps and
#             blade, its spots unchanged), now with what the rifle needs built in.
#   - RIFLE   w_scythe_rifle (`scythe_rifle`): the same model with two nodes moved (the weapons session's design,
#             WeaponModels.luau SCYTHE_TURN): the BLADE slides down the haft to behind the grip and turns on its edge to
#             become the STOCK; a short SCOPE comes up out of the haft; the teal COLLAR is the MUZZLE RING at the front.
# Original: no red and black, no gun under the blade, no blade folding forward along a barrel. Quiet kit style (look B):
# a dark haft, a steel blade with a lighter ground edge, charcoal parts, the small teal collar the one accent.
#   blender -b --factory-startup -P <script that imports gun_scythe and calls BUILD[...]()>   (gun_set does not list it yet)
# WHAT IS STATIC (identical in both models): the haft in two lengths (the front one from the collar back to the
# receiver: the long dark haft and the ribbed fore band at -0.45 where the front hand holds; the rear one: the ribbed
# grip wrap round (0, 0, 0)); the teal collar at the front (its face has the dark bore: the rifle's muzzle); between the
# hands the RECEIVER, a charcoal sleeve with a dark inset each side and a channel along its top that the scope lies in;
# at the butt the HEEL, a charcoal block with a slot in its back that the blade's root locks into (its flat top is the
# hat seat).
# WHAT MOVES (only two nodes, the same names and the same meshes in both models; only their placement differs):
#   - blade  (blade_wzB__steel, blade_wzN__edge): scythe: out to the left (-x) from the collar, edge forward (-z), on
#            its flat. rifle: on its edge (spine up, edge down, flat facing -x), its root in the heel's slot and the
#            rest running back to the tip at z 0.82: the stock. x_rifle = TURN_R x_scythe + (BLADE_T - TURN_R BLADE_C)
#            (TURN_R: 120 degrees about (-1, 1, 1)/sqrt 3; the code stand-in's own turn, the blade 1.4 cm further forward).
#   - scope  (scope_wzB__frame, scope_wzB__dark, scope_wzN__glass, scope_wzN__deck): a short scope on a mount block
#            that slides in the receiver's channel. scythe: sunk in the channel, its top just under the rim (the walls
#            hide it from the side). rifle: up SCOPE_UP (0.0645), the mount's foot still 8 mm in the channel, the aim line at
#            y AXIS_R. A pure translation along +y.
# CONTRACT: spots grip (0, 0, 0) and fore (0, 0, -0.45) in both (the hands never move); scythe: mid (-0.3, 0.02, -1.25),
# muzzle (-0.7, 0.02, -1.16) at the blade tip; rifle: mid (0, 0, -0.6), muzzle (0, 0, -1.305) at the collar's face,
# sight (0, AXIS_R, EYE_Z) = (0, 0.0775, -0.095) at the eyepiece (the aim line). The notes carry `pivots` (each moving node's origin in that
# model: the blade's root, the scope's middle), `hatAt` (the same in both) and `form` (the other model's key, the
# moving nodes, and each node's move to the other form: pivot + axis/deg + move, and the same as a CFrame).
# Zones: the haft _wzA; the blade, the scope, the receiver and the heel _wzB; the collar, the wraps, the bore, the
# insets, the edge, the lenses and the scope's light rings _wzN. Flat kit colours (Batch export, no bake).
# Checks: one connected piece each with the moving nodes touching it (the blade in the collar / the heel's slot within
# 1.5 mm, the scope's mount 1 mm off the channel walls), 0 flicker pairs in both (JF_NOZFIX gun_zfix style and the glb
# scan at rack studs), under 12k triangles.
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import gunkit
from gunkit import P
from artist_kit import outline, rrect, prism, cyl, soft, cut
from gun_melee import split, lathe, loft, catmull, interp
from gun_batch_a import Batch, pockets

FRAME, DARK, BLACK, DECK = '444851', '353840', '16171b', '676d78'
HAFT, WRAP, TEAL, STEEL, EDGE, GLASS = '3c3734', '232429', '3ee6c8', '98a0aa', 'c8ced6', '2a343c'

# ---- the receiver and the scope's channel (metres, weapon frame)
ZF, ZB = -0.404, -0.076         # the receiver's front and back faces (the hands: fore band ends -0.4075, wrap -0.0925)
RIM, XS, CH = 0.036, 0.0315, 0.0235   # its top, its half width, the channel's half width
R_OBJ, R_TUBE, R_EYE = 0.022, 0.0135, 0.0185
H_M = 0.036                      # the mount block under the tube
AXIS_S = RIM - 0.001 - R_OBJ     # the scope's axis in the scythe: the objective's top 1 mm under the rim
FOOT_S = AXIS_S - R_TUBE - H_M   # the mount's foot in the scythe
FLOOR = FOOT_S - 0.002           # the channel's floor
BOT = FLOOR - 0.012              # the receiver's bottom
SCOPE_UP = (RIM - 0.008) - FOOT_S   # rifle: the foot 8 mm down in the channel
AXIS_R = AXIS_S + SCOPE_UP
SCOPE_Z = -0.24                  # the scope's middle (its node origin)
EYE_Z = -0.095                   # the eyepiece's back face

# ---- the heel at the butt (the blade's socket in the rifle)
HZ0, HZ1, HTOP, HBOT = 0.092, 0.152, 0.03, -0.046
SLOT = (0.11, -0.037, 0.017, 0.0085)    # its slot: front wall z, bottom, top, half width

# ---- the blade's move to the rifle (weapon frame): x' = TURN_R (x - BLADE_C) + BLADE_T
TURN_R = Matrix(((0, -1, 0), (0, 0, 1), (-1, 0, 0)))   # (x, y, z) -> (-y, z, -x): flat -> on its edge, along +z
BLADE_C = Vector((0.012, 0.02, -1.218))   # the blade's root: its spine corner on the root face, on the centre plane
BLADE_T = Vector((0.0, 0.012, 0.114))     # ... in the rifle: 4 mm behind the slot's front wall, the spine at y 0.012

HAT = ((0.0, HTOP, round((HZ0 + HZ1) / 2, 4)), 0.09)   # on the heel's flat top (s = 0.09 / 0.12 = 0.75)

B = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))    # weapon frame -> Blender (gunkit.P)


def wmat(R, t):
    """a weapon-frame move x' = R x + t as a 4x4 matrix in Blender's frame"""
    M = (B @ R @ B.transposed()).to_4x4()
    M.translation = B @ Vector(t)
    return M


def blade_move(s=1.0):
    """the blade's move s of the way from the scythe to the rifle, turning about its root while the root slides along
       (the picture's mid pose; s = 1 is the rifle exactly): (R, t) with x' = R x + t, weapon frame"""
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
        q = R.to_quaternion()
        ax, ang = q.to_axis_angle()
        mv = (R @ piv + t) - piv
        out['turn'][node] = {'pivot': [round(v, 5) for v in piv], 'axis': [round(v, 5) for v in ax],
                             'deg': round(math.degrees(ang), 3), 'move': [round(v, 5) for v in mv],
                             'cf': [round(v, 5) for v in t] + [round(R[i][j], 5) for i in range(3) for j in range(3)]}
    return out


# ================================================================================================= the parts
def ribs(z0, z1, n):
    out, step = [], (z1 - z0) / n
    for k in range(n):
        a = z0 + k * step
        out += [(0.0232, a + 0.0015), (0.0232, a + step - 0.004), (0.0214, a + step - 0.0025), (0.0214, a + step - 0.0005)]
    return out


def body(g):
    """the static parts, the same in both models"""
    # ---- the front haft: the bore in the collar's face (the muzzle), the teal collar, the long haft, the fore band;
    # it ends 4 mm inside the receiver's front wall
    prof = [(0.0, -1.272), (0.0088, -1.272), (0.0088, -1.3015), (0.0108, -1.305), (0.026, -1.305), (0.0293, -1.3027),
            (0.031, -1.2985), (0.031, -1.2045), (0.0292, -1.2005), (0.0245, -1.1985), (0.02, -1.198), (0.02, -0.4925)]
    prof += ribs(-0.49, -0.41, 3) + [(0.0232, -0.4085), (0.02, -0.4075), (0.02, ZF + 0.004), (0.0, ZF + 0.004)]
    hf = lathe(prof, segs=24)
    rest, bore = split(hf, lambda c, n: c.z > -1.302 and c.z < -1.27 and math.hypot(c.x, c.y) < 0.0092)
    rest, collar = split(rest, lambda c, n: c.z < -1.1979)
    haft, band = split(rest, lambda c, n: -0.4915 < c.z < -0.4078)
    g.put('haft_wzA__haft', haft); g.put('collar_wzN__teal', collar); g.put('muzzle_wzN__black', bore)
    g.put('wrap_wzN__wrap', band)
    # ---- the rear haft: from inside the receiver's back wall through the grip wrap into the heel
    prof = [(0.0, ZB - 0.004), (0.02, ZB - 0.004), (0.02, -0.0925)] + ribs(-0.09, 0.09, 7) + \
           [(0.0232, 0.0905), (0.02, 0.0915), (0.02, 0.098), (0.0, 0.098)]
    hr = lathe(prof, segs=24)
    haft2, wrap = split(hr, lambda c, n: -0.0915 < c.z < 0.0912)
    g.put('haft_wzA__haft', haft2); g.put('wrap_wzN__wrap', wrap)
    # ---- the receiver: a charcoal sleeve between the hands, a dark inset each side, the scope's channel along its top
    rec = soft(prism(outline(rrect(ZF, ZB, BOT, RIM, 0.014)), 2 * XS), 0.005, seg=2)
    chan = prism(outline(rrect(ZF + 0.015, ZB - 0.015, FLOOR, RIM + 0.03, 0.008)), 2 * CH)
    rec = cut(rec, chan, *pockets(ZF + 0.035, ZB - 0.035, BOT + 0.012, RIM - 0.014, 0.008, XS, 0.003))
    rest, inset = split(rec, lambda c, n: abs(n.x) > 0.95 and CH + 0.002 < abs(c.x) < XS - 0.001)
    rest, deck = split(rest, lambda c, n: n.y > 0.95 and c.y > RIM - 0.001)
    g.put('receiver_wzB__frame', rest); g.put('receiver_wzN__dark', inset); g.put('receiver_wzN__deck', deck)
    # ---- the heel at the butt: a charcoal block, a slot in its back for the blade's root; its flat top seats the hat
    hl = soft(prism(outline(rrect(HZ0, HZ1, HBOT, HTOP, 0.011)), 0.05), 0.005, seg=2)
    sz, sb, st, sw = SLOT
    hl = cut(hl, prism(outline(rrect(sz, HZ1 + 0.05, sb, st, 0.004)), 2 * sw))
    g.put('heel_wzB__frame', hl)


def blade(g):
    """the blade, in the scythe pose (gun_batch_c.scythe's blade exactly): at y 0.02, its neck in the collar, sweeping
       out to the left (-x) in a broad crescent to the tip (-0.70, 0.02, -1.16), the spine thick and rounded, the flats
       tapering to a lighter ground edge facing forward (-z)"""
    Y0 = 0.02
    edge = catmull([(0.012, -1.262), (-0.06, -1.318), (-0.2, -1.366), (-0.35, -1.378), (-0.5, -1.348), (-0.62, -1.272), (-0.70, -1.16)], n=10)
    spine = catmull([(0.012, -1.218), (-0.15, -1.234), (-0.3, -1.2455), (-0.45, -1.236), (-0.6, -1.203), (-0.70, -1.16)], n=10)
    edge, spine = edge[::-1], spine[::-1]
    N = 30
    st, ZB_ = [], []
    for k in range(N):
        x = 0.012 + (-0.686 - 0.012) * (k / (N - 1)) ** 0.9
        u = min(1.0, -x / 0.7) if x < 0 else 0.0
        zs, ze = interp(spine, x), interp(edge, x)
        T = 0.0145 * (1 - 0.55 * u)
        bw = min(0.022 * (1 - 0.4 * u), 0.42 * (zs - ze))
        zb = ze + bw
        Tb = 0.7 * T
        ZB_.append((x, zb))
        sec = [(zs + min(0.0035, 0.3 * (zs - ze)), 0.0), (zs, T / 2), (zb, Tb / 2), (ze, 0.0008), (ze, -0.0008), (zb, -Tb / 2), (zs, -T / 2)]
        st.append([(x, Y0 + yy, zz) for zz, yy in sec])
    bl = loft(st, tip=(-0.70, Y0, -1.16))
    ZB_ = ZB_[::-1]
    steel, ground = split(bl, lambda c, n: c.x < 0.0 and c.z < interp(ZB_, c.x) + 0.0006)
    g.put('blade_wzB__steel', steel); g.put('blade_wzN__edge', ground)
    g.pivot0['blade'] = tuple(BLADE_C)


def scope(g):
    """the short scope in the scythe pose: sunk in the receiver's channel on its mount block"""
    A = AXIS_S
    prof = [(0.0, -0.381), (0.0158, -0.381), (0.0158, -0.385), (0.0198, -0.385), (R_OBJ, -0.3825), (R_OBJ, -0.33),
            (0.0205, -0.325), (R_TUBE, -0.309), (R_TUBE, -0.17), (0.0158, -0.163), (R_EYE, -0.156), (R_EYE, EYE_Z - 0.0035),
            (0.0172, EYE_Z), (0.0138, EYE_Z), (0.0138, EYE_Z - 0.004), (0.0, EYE_Z - 0.004)]
    body_ = lathe(prof, segs=24, cy=A)
    def r(c): return math.hypot(c.x, c.y - A)
    rest, lens = split(body_, lambda c, n: abs(n.z) > 0.9 and ((r(c) < 0.0156 and c.z < -0.3805) or (r(c) < 0.0136 and c.z > EYE_Z - 0.0045)))
    rest, ring = split(rest, lambda c, n: c.z > EYE_Z - 0.0025 and r(c) > 0.0136)   # (the eyepiece's light ring)
    g.put('scope_wzB__frame', rest); g.put('scope_wzN__glass', lens); g.put('scope_wzN__deck', ring)
    # the elevation turret on top (charcoal, a light cap), sunk into the tube, its cap under the objective's top
    tu = cyl(0.0095, (0.0, A + 0.01, -0.24), (0.0, A + 0.0212, -0.24), sides=16)
    tside, tcap = split(tu, lambda c, n: n.y > 0.9)
    g.put('scope_wzB__frame', tside); g.put('scope_wzN__deck', tcap)
    # the mount block under the tube: its sides 1 mm off the channel's walls (it slides in the channel)
    g.put('scope_wzB__dark', soft(prism(outline(rrect(-0.295, -0.19, FOOT_S, A - 0.004, 0.006)), 2 * (CH - 0.001)), 0.003, seg=2))
    g.pivot0['scope'] = (0.0, A, SCOPE_Z)


def _build(form):
    gunkit.use_style('B')
    g = TwoForm('w_scythe' if form == 'scythe' else 'w_scythe_rifle', form)
    g.slot('haft', HAFT); g.slot('wrap', WRAP); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('teal', TEAL); g.slot('steel', STEEL); g.slot('edge', EDGE); g.slot('glass', GLASS); g.slot('deck', DECK)
    body(g); blade(g); scope(g)
    g.origins = {k: tuple(v) for k, v in g.pivot0.items()}
    g.hat = HAT
    if form == 'scythe':
        g.spots = {'grip': (0.0, 0.0, 0.0), 'fore': (0.0, 0.0, -0.45), 'mid': (-0.3, 0.02, -1.25), 'muzzle': (-0.7, 0.02, -1.16)}
    else:
        g.spots = {'grip': (0.0, 0.0, 0.0), 'fore': (0.0, 0.0, -0.45), 'mid': (0.0, 0.0, -0.6), 'muzzle': (0.0, 0.0, -1.305),
                   'sight': (0.0, round(AXIS_R, 4), EYE_Z)}
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
