# THE SECONDARIES' LOOT SKINS (18 Nov 2026), batch 3 of the loot skins that had no model (LootTable.SKINS; GunSkins.valid
# hid them): Bug Zapper (taser), Squirt Flower and Hose Nozzle (water pistol), Business Cards (card deck), Game Pad (TV
# remote), Walkie Talkies (Lefty & Righty), Ice Cube (snowball), Garden Hose (lasso). Like batch 2
# (gun_primary_skins.reskin) each is its base weapon's own build (every spot, moving node and origin kept), recoloured
# to its theme, off-theme pieces off, one signature piece on; organic shapes are moulded in one piece (sdf_kit):
#   taser_zapper     an electric fly-swatter racket head on the cartridge, three lit wires across it (lines, not a grid),
#                    a pale body and UV-violet glow
#   water_flower     a clown's squirt flower round the nozzle: white petals and a yellow heart moulded in one piece, the
#                    bore left open; soft green body, pink fittings
#   water_hose       a garden spray gun: green body, brass fittings, a length of hose out of the grip's foot on a brass
#                    coupling
#   cards_business   plain white cards (no text), slate backs, a slim chrome case round the deck
#   remote_pad       a game pad's rounded face on the remote's front half: a d-pad, two thumbsticks, four plain buttons
#                    (no brand shapes or symbols); the remote's own keys off
#   akimbo_walkie    a walkie-talkie: an antenna with a knob off the back, speaker ribs on the left, an orange talk button
#   snowball_ice     a rounded ice cube (one moulded skin), its edges frosted white, the snowball's centre kept
#   lasso_hose       the rope a green garden hose, the leather a brass collar, a brass spray nozzle at the loop's eye
# Loaded by gun_set.py (no JF_EXTRA).
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
import numpy as np
from mathutils import Vector
from gunkit import P
from artist_kit import outline, rrect, prism, xprism, cyl, tube, capsule, cut, union, soft
from gun_melee import split, ball
from gun_primary_skins import reskin
import gun_batch_a as A, gun_batch_b as Bb, gun_batch_c as C, gun_batch_d as D, gun_batch_e2 as E2


def oval_ring(c, rz, ry, r, plane='zy', keep=None):
    """a smooth oval ring (a torus stretched to an ellipse) as an sdf field: centre c, radii rz / ry in the side plane
       (plane 'zy') or rx / ry in the front plane ('xy'), tube radius r. keep(p) -> field: intersect with it (half rings)"""
    import sdf_kit as S
    c = np.asarray(c, float)
    def f(p):
        q = p - c
        if plane == 'zy':
            a, b, t = q[:, 2] / rz, q[:, 1] / ry, q[:, 0]
            m = min(rz, ry)
        else:
            a, b, t = q[:, 0] / rz, q[:, 1] / ry, q[:, 2]
            m = min(rz, ry)
        rad = (np.sqrt(a * a + b * b) - 1.0) * m
        return np.sqrt(rad * rad + t * t) - r
    return S.intersect(f, keep) if keep is not None else f


# ------------------------------------------------------------------------------------------------ Bug Zapper (taser)
def taser_zapper():
    g = reskin(Bb.BUILD['taser'], 'taser@taser_zapper',
               {'body': 'd8d6cf', 'glow': ('8a7dff', 'n'), 'lit': ('9a8cff', 'n'), 'ring': '3a3d44'})
    c = (0.0, 0.012, -0.262)
    import sdf_kit as S
    g.pieces[('racket_wzB', 'ring')] = S.mesh(oval_ring(c, 0.07, 0.052, 0.0062), (-0.01, c[1] - 0.064, c[2] - 0.082), (0.01, c[1] + 0.064, c[2] + 0.082),
                                             h=0.0012, tris=900, name='zapring')
    for dy in (-0.022, 0.022):                      # the neck: two struts from the cartridge into the ring
        g.put('racket_wzB__ring', capsule(0.005, (0.0, c[1] + dy * 0.5, -0.16), (0.0, c[1] + dy, c[2] + 0.064), seg=10, rings=4))
    for dy in (-0.026, 0.0, 0.026):                 # three lit wires across, along the barrel
        half = 0.07 * math.sqrt(max(0.0, 1 - (dy / 0.052) ** 2))
        g.put('wire_wzN__lit', capsule(0.0013, (0.0, c[1] + dy, c[2] - half + 0.002), (0.0, c[1] + dy, c[2] + half - 0.002), seg=8, rings=3))
    return g.done()


# --------------------------------------------------------------------------------------------- Squirt Flower (water)
def flower_field():
    import sdf_kit as S
    c = np.array([0.0, 0.01, -0.272])
    heart = S.ellipsoid(tuple(c), (0.026, 0.026, 0.012))
    petals = []
    for k in range(10):
        a = 2 * math.pi * k / 10
        d = np.array([math.cos(a), math.sin(a), 0.0])
        rot = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
        petals.append(S.ellipsoid(tuple(c + d * 0.047 + np.array([0, 0, 0.004])), (0.024, 0.0115, 0.005), rot))
    pet = S.union(*petals, k=0.004)
    whole = S.carve(S.union(heart, pet, k=0.006), S.capsule((0, 0.01, -0.32), (0, 0.01, -0.24), 0.0075), k=0.002)
    return ['petal', 'heart'], [pet, heart], whole


def water_flower():
    import sdf_kit as S
    g = reskin(A.BUILD['water'], 'water@water_flower',
               {'body': '9fb79a', 'accent': 'd27a95', 'petal': 'f4f1ea', 'heart': 'e8c24a'})
    labels, parts, field = flower_field()
    for lab, bm in S.mesh_paint(field, S.nearest(*parts), labels, (-0.08, -0.07, -0.30), (0.08, 0.09, -0.24),
                                h=0.0011, tris=1800, name='flower').items():
        g.pieces[('flower_wzN', lab)] = bm
    return g.done()


# ---------------------------------------------------------------------------------------------- Hose Nozzle (water)
def water_hose():
    g = reskin(A.BUILD['water'], 'water@water_hose',
               {'body': '3f6e48', 'accent': 'b8924a', 'frame': '2f3237', 'hose': '2f5a38'})
    # a brass coupling under the grip's foot and a length of hose curling back and down from it
    g.put('hose_wzN__accent', soft(cyl(0.017, (0.0, -0.15, 0.104), (0.0, -0.172, 0.112), sides=18), 0.002, seg=1))
    from gun_melee import catmull
    ctl = [(0.0, -0.165, 0.11), (0.0, -0.2, 0.125), (0.0, -0.228, 0.155), (0.008, -0.24, 0.195), (0.018, -0.236, 0.235), (0.026, -0.22, 0.27)]
    yz = catmull([(p[1], p[2]) for p in ctl], 6); xs = catmull([(p[0], 0.0) for p in ctl], 6)
    pts = [(xs[i][0], yz[i][0], yz[i][1]) for i in range(len(yz))]
    for p0, p1 in zip(pts, pts[1:]):
        g.put('hose_wzN__hose', capsule(0.0125, p0, p1, seg=14, rings=5))
    return g.done()


# ------------------------------------------------------------------------------------------- Business Cards (cards)
def cards_business():
    g = reskin(E2.BUILD['cards'], 'cards@cards_business', {'card': 'f2f0ea', 'back': '3e4b5f', 'case': 'c3c9d1'})
    # (open at the back: the fanned cards lie behind the deck, so no wall of the case lies on the front card's face)
    case = soft(xprism(outline(rrect(-0.051, 0.051, 0.036, 0.104, 0.006)), -0.0225, -0.002), 0.0015, seg=2)
    hollow = xprism(outline(rrect(-0.044, 0.044, 0.04, 0.12, 0.004)), -0.019, 0.01)   # (1 mm narrower than the deck: it grips its edges)
    g.put('case_wzN__case', cut(case, hollow))
    return g.done()


# ------------------------------------------------------------------------------------------------ Game Pad (remote)
def pad_field():
    import sdf_kit as S
    face = S.slab([(-0.197, -0.004), (-0.197, 0.0), (-0.07, 0.0), (-0.07, -0.004)], 0.064, 0.012, grow=0.014)   # (its front 3 mm behind the nose window)
    lobes = S.union(S.ellipsoid((-0.046, -0.012, -0.09), (0.026, 0.02, 0.04)), S.ellipsoid((0.046, -0.012, -0.09), (0.026, 0.02, 0.04)))
    return S.union(face, lobes, k=0.016)


def remote_pad():
    import sdf_kit as S
    g = reskin(D.BUILD['remote'], 'remote@remote_pad',
               {'body': '34363d', 'pad': '2c2e34', 'btn': 'aeb3bb', 'stick': '1d1f23'},
               drop=('key_wzB__key', 'key_wzB__accent', 'body_wzA__plate'))
    field = pad_field()
    g.pieces[('pad_wzA', 'pad')] = S.mesh(field, (-0.11, -0.05, -0.23), (0.11, 0.04, -0.04), h=0.0014, tris=1400, name='pad')
    top = 0.0145
    # the d-pad on the left (a rounded plus, short arms), four plain round buttons on the right, two thumbsticks between
    g.put('dpad_wzN__stick', soft(union(prism(outline(rrect(-0.168, -0.144, top - 0.002, top + 0.004, 0.002)), 0.008, x=-0.04),
                                        prism(outline(rrect(-0.16, -0.152, top - 0.002, top + 0.004, 0.002)), 0.024, x=-0.04)), 0.001, seg=1))
    for (dx, dz) in ((0.0, -0.17), (0.0, -0.142), (-0.013, -0.156), (0.013, -0.156)):   # (all one plain grey: no console's colours)
        g.put('btn_wzN__btn', soft(cyl(0.0052, (0.04 + dx, top - 0.003, dz), (0.04 + dx, top + 0.004, dz), sides=14), 0.0012, seg=1))
    for x in (-0.02, 0.02):
        g.put('stick_wzN__stick', cyl(0.0045, (x, top - 0.004, -0.112), (x, top + 0.006, -0.112), sides=12))
        g.put('stick_wzN__stick', soft(cyl(0.009, (x, top + 0.006, -0.112), (x, top + 0.011, -0.112), sides=16), 0.0015, seg=1))
    g.hat = ((0.0, top, -0.112), 0.05)
    g.spots['hat'] = (0.0, top, -0.112)
    return g.done()


# --------------------------------------------------------------------------------------- Walkie Talkies (akimbo)
def akimbo_walkie():
    g = reskin(Bb.BUILD['akimbo'], 'akimbo@akimbo_walkie',
               {'body': '3a3e45', 'frame': '2a2c31', 'dark': '24262b', 'orange': 'd67a32', 'grille': '1d1f23'})
    # the antenna off the back of the top, a knob on it; speaker ribs on the left; an orange talk button
    g.put('aerial_wzN__dark', soft(cyl(0.006, (0.012, 0.06, 0.06), (0.012, 0.2, 0.072), sides=12), 0.001, seg=1))
    g.put('aerial_wzN__orange', ball(0.009, (0.012, 0.204, 0.072)))
    for k in range(4):
        y = 0.022 + k * 0.011
        g.put('grille_wzN__grille', soft(prism(outline(rrect(-0.11, -0.03, y - 0.0028, y + 0.0028, 0.0026)), 0.004, x=-0.0295), 0.0008, seg=1))
    g.put('talk_wzN__orange', soft(prism(outline(rrect(-0.01, 0.028, 0.026, 0.05, 0.004)), 0.006, x=-0.0285), 0.0015, seg=1))
    return g.done()


# ------------------------------------------------------------------------------------------------ Ice Cube (snowball)
def ice_field():
    import sdf_kit as S
    c = np.array([0.0, 0.02, -0.079])
    a, b = math.radians(18), math.radians(12)
    Ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    R = Ry @ Rx
    hs, rr = 0.05, 0.016
    def cube(p):
        q = (p - c) @ R
        d = np.abs(q) - (hs - rr)
        out = np.sqrt((np.maximum(d, 0.0) ** 2).sum(-1))
        return out + np.minimum(d.max(-1), 0.0) - rr
    def frost(p):
        # near the cube's edges and corners (two or more axes close to the face): a white frosted rim
        q = np.abs((p - c) @ R)
        near = np.sort(q, -1)[:, -2]            # the second-largest |coordinate|
        return (hs - 0.012) - near
    return ['ice', 'frost'], [lambda p: np.full(len(p), 0.0), frost], cube


def snowball_ice():
    import sdf_kit as S
    g = reskin(C.BUILD['snowball'], 'snowball@snowball_ice', {'ice': 'b9dcea', 'frost': 'eef6f9'}, drop=('ball', 'clump', 'ice'))
    labels, parts, field = ice_field()
    for lab, bm in S.mesh_paint(field, S.nearest(*parts), labels, (-0.09, -0.07, -0.17), (0.09, 0.11, 0.01),
                                h=0.0012, tris=1600, name='icecube').items():
        g.pieces[('cube_wzA', lab)] = bm
    return g.done()


# -------------------------------------------------------------------------------------------- Garden Hose (lasso)
def lasso_hose():
    g = reskin(E2.BUILD['lasso'], 'lasso@lasso_hose', {'rope': '3f7a4a', 'leather': 'b8924a', 'brass': 'c49a4e'})
    eye = g.spots.get('eye', (0.086, -0.2355, 0.0012))
    g.put('loop_wzN__brass', soft(cyl(0.011, (eye[0] - 0.01, eye[1] - 0.004, eye[2]), (eye[0] + 0.022, eye[1] - 0.004, eye[2]), sides=16, r2=0.007), 0.0015, seg=1))
    return g.done()


SKINS = {'taser@taser_zapper': taser_zapper, 'water@water_flower': water_flower, 'water@water_hose': water_hose,
         'cards@cards_business': cards_business, 'remote@remote_pad': remote_pad, 'akimbo@akimbo_walkie': akimbo_walkie,
         'snowball@snowball_ice': snowball_ice, 'lasso@lasso_hose': lasso_hose}
