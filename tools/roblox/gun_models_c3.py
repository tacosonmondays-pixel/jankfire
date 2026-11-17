import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunkit_c import *
import gun_sights as SG
# VERSION C, part 3: Plan B (M1911), Revolver (S&W Model 29), Redline (Thompson M1928), Katana, Shredder. The style,
# the contract and the shared pieces are in gunkit_c.py; gun_models_c.py builds and previews these with the rest:
#   blender -b --factory-startup -P tools/roblox/gun_models_c.py -- <out_dir> pistol revolver redline katana shredder
#   blender -b --factory-startup -P tools/roblox/gun_preview.py -- <out_dir> --set c pistol revolver redline katana shredder
import bmesh
from gunkit import P


# ------------------------------------------------------------------------------------------------- local pieces
def fold(g, piece, bm):
    """fold a finished solid whose faces and edges already carry their smooth flags into a piece"""
    bm.normal_update()
    me = bpy.data.meshes.new('tmp')
    bm.to_mesh(me); bm.free()
    g._bm(piece).from_mesh(me)
    bpy.data.meshes.remove(me)


def loft(g, piece, rings, group=None, caps=(True, True)):
    """a solid through rings of points [(x, y, z)] (weapon frame; every ring the same count, in order round it).
       group(i, k) -> a key for the face between ring i and i + 1 on side k (None = flat): faces with the same key
       shade smooth into each other, every other edge stays crisp (the style's faceted outline). the caps are flat"""
    bm = bmesh.new()
    V = [[bm.verts.new(P(*p)) for p in ring] for ring in rings]
    m = len(rings[0])
    key = {}
    for i in range(len(rings) - 1):
        for k in range(m):
            j = (k + 1) % m
            f = bm.faces.new([V[i][k], V[i][j], V[i + 1][j], V[i + 1][k]])
            key[f] = group(i, k) if group else k
    if caps[0]: bm.faces.new(V[0][::-1])
    if caps[1]: bm.faces.new(V[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:
        f.smooth = key.get(f) is not None
    for e in bm.edges:
        fs = e.link_faces
        e.smooth = len(fs) == 2 and key.get(fs[0]) is not None and key.get(fs[0]) == key.get(fs[1])
    fold(g, piece, bm)


def disc(cx, cy, r, z, n=8, turn=0.0):
    """a ring of n points round (cx, cy) at z, the first at angle turn + pi / n"""
    return [(cx + r * math.cos(turn + math.pi / n + 2 * math.pi * j / n), cy + r * math.sin(turn + math.pi / n + 2 * math.pi * j / n), z) for j in range(n)]


def fluted(g, piece, R, rf, cy, z0, z1, n=6, lobe=3, a1=0.245, a2=0.14, ch=0.003, run=0.011, ramp=0.007):
    """a revolver's cylinder round the axis (0, cy): round, n flutes between the chambers (one on each side at
       angle 0 and pi, so a chamber is on top), the flutes running out in a short ramp before each end, both ends
       chamfered. n-fold symmetric, so a turn of 2 pi / n looks the same"""
    sec = 2 * math.pi / n
    rm = (R + rf) / 2 + (R - rf) * 0.1
    prof = []  # (angle, radius in the fluted middle, is it a lobe point)
    for k in range(n):
        f = k * sec
        prof += [(f, rf, False), (f + a2, rm, False), (f + a1, R, True)]
        for i in range(1, lobe + 1):
            prof.append((f + a1 + (sec - 2 * a1) * i / (lobe + 1), R, True))
        prof += [(f + sec - a1, R, True), (f + sec - a2, rm, False)]
    def ring(z, mode):
        out = []
        for a, r, lob in prof:
            rr = R - ch if mode == 'chamfer' else (r if mode == 'flute' else R)
            out.append((rr * math.cos(a), cy + rr * math.sin(a), z))
        return out
    zs = [(z0, 'chamfer'), (z0 + ch, 'round'), (z0 + run, 'round'), (z0 + run + ramp, 'flute'),
          (z1 - run - ramp, 'flute'), (z1 - run, 'round'), (z1 - ch, 'round'), (z1, 'chamfer')]
    m = len(prof)
    def group(i, k):
        lobe_side = prof[k][2] and prof[(k + 1) % m][2]
        if i in (0, 6): return None
        if i in (1, 5): return 'round'
        if i in (2, 4): return 'round' if lobe_side else None
        return 'round' if lobe_side else ('flute', ((k + 2) // (len(prof) // n)) % n)
    loft(g, piece, [ring(z, mode) for z, mode in zs], group=group)


# ------------------------------------------------------------------------------------------------------- Plan B
def pistol():
    """PLAN B, after the Colt M1911: a slim tall slide with big rear grooves and a barrel bushing in its nose, the
       exposed spur hammer (cocked), the grip safety's tail over the web of the hand, a straight single-stack grip
       raked like the original with blue panels and two screws, the slide stop and thumb safety on the left, the long
       flat trigger. Light charcoal slide on a near-black frame, the blue only on the grip panels"""
    base = A.pistol()
    g = Gun('w_pistol')
    g.slot('body', '3c4c75'); g.slot('frame', DECK); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('glow', 'e8e8e0')
    g.spots = dict(base.spots)
    BY, SY = 0.03, g.spots['sight'][1]  # the bore's height, the aim line
    # the slide (node "slide": kicks back, locks back when empty): tall and slim, its nose drops in front of the frame
    g.prism('slide_wzA__frame', [(-0.248, -0.017), (-0.19, -0.017), (-0.19, 0.004), (0.054, 0.004), (0.054, 0.052),
                                  (-0.248, 0.052)], 0.044, bev=0.007)
    for z0 in (0.012, 0.0215, 0.031, 0.0405):  # the rear grooves
        g.box('slide_wzN__dark', (-0.0228, 0.0228), (0.011, 0.045), (z0, z0 + 0.0055), bev=0.0012)
    g.box('slide_wzN__black', (0.0215, 0.0229), (0.022, 0.045), (-0.096, -0.036), bev=0.001)  # ejection port (right)
    # the nose: the barrel bushing round the muzzle, the recoil spring plug under it
    g.ring('slide_wzN__dark', 0.0165, 0.0094, (0, BY, -0.2535), (0, BY, -0.245), sides=8, bev=0.002)
    g.cylz('slide_wzN__dark', 0.0092, -0.2515, -0.24, y=-0.0025, sides=8, bev=0.002)
    g.cylz('slide_wzN__black', 0.0048, -0.2522, -0.25, y=-0.0025, sides=8, bev=0)
    # sights (slim sights, 16 Nov 2026, gun_sights.py; on the slide, near-black): a pointed blade with a white dot at
    # the front, a low notch block with two square ears at the back (the aim line over both)
    SG.blade(g, 'slide_wzN__dark', -0.226, SY, 0.052, w=0.0055, depth=0.012, glow_piece='slide_wzN__glow')
    SG.notch(g, 'slide_wzN__dark', 0.044, SY, 0.052, 0.031, depth=0.008, nw=0.3, nd=0.0036)
    # the barrel (stays put: it shows out of the bushing when the slide locks back)
    tube(g, 'body_wzB__dark', 0.0092, -0.2515, -0.2, y=BY, bev=0.0015, hole=(0.0058, 0.02))
    # the frame: the rails and dust cover under the slide (a little narrower, so the nose rides over it)
    g.prism('body_wzB__dark', [(-0.19, -0.017), (0.0, -0.017), (0.03, -0.024), (0.056, -0.012), (0.056, 0.005),
                                (-0.19, 0.005)], 0.04, bev=0.006)
    # the trigger guard (a loop from the dust cover to the grip), the long flat trigger
    g.prism('body_wzB__dark', [(-0.106, -0.014), (-0.11, -0.046), (-0.101, -0.066), (-0.085, -0.0765), (0.006, -0.0765),
                                (0.002, -0.0645), (-0.081, -0.0645), (-0.094, -0.057), (-0.097, -0.042), (-0.093, -0.014)],
            0.026, bev=0.004)
    g.prism('body_wzB__dark', [(-0.05, -0.016), (-0.036, -0.016), (-0.036, -0.056), (-0.04, -0.06), (-0.048, -0.058)],
            0.014, bev=0.003)
    # slide stop (pin head at the front) and thumb safety, on the left
    g.prism('body_wzN__dark', [(-0.088, 0.002), (-0.034, 0.002), (-0.026, -0.006), (-0.032, -0.014), (-0.076, -0.012),
                                (-0.09, -0.006)], 0.004, x=-0.0215, bev=0.0015)
    g.cyl('body_wzN__dark', 0.0062, (-0.0235, -0.005, -0.08), (-0.0255, -0.005, -0.08), sides=8, bev=0.001)
    g.prism('body_wzN__dark', [(0.026, 0.003), (0.054, 0.003), (0.054, -0.009), (0.04, -0.016), (0.024, -0.008)],
            0.004, x=-0.0215, bev=0.0015)
    # the grip: the frame raked as before, the blue panels with two screws, the grip safety and its tail
    g.prism('grip_wzB__dark', raked(0.032, -0.072, 0.142, 0.06, -0.297, taper=0.003), 0.044, bev=0.008)
    g.prism('grip_wzA__body', raked(0.0325, -0.0745, 0.108, 0.043, -0.297), 0.052, bev=0.005)
    rk = -0.297
    pts = [(0.0325 + d * math.sin(rk), -0.0745 + d * math.cos(rk)) for d in (0.036, -0.036)]
    rivets(g, 'rivet_wzN__frame', 0.026, pts, r=0.0048)
    g.prism('grip_wzB__dark', [(0.038, 0.004), (0.06, 0.004), (0.077, -0.002), (0.086, -0.01), (0.082, -0.019),
                                (0.066, -0.019), (0.052, -0.032), (0.04, -0.028)], 0.034, bev=0.006)
    # the magazine (node "mag": slides out along the grip's rake), hidden but for its base
    g.prism('mag_wzB__dark', raked(0.03, -0.068, 0.13, 0.036, -0.297), 0.03, bev=0.003)
    g.prism('mag_wzN__frame', raked(0.0545, -0.1445, 0.014, 0.066, -0.297), 0.048, bev=0.004)
    # the spur hammer (node "hammer"), cocked back
    g.prism('hammer_wzN__dark', [(0.048, -0.003), (0.064, -0.005), (0.072, 0.012), (0.082, 0.026), (0.086, 0.038),
                                  (0.078, 0.045), (0.064, 0.04), (0.054, 0.024)], 0.016, bev=0.003)
    return g


# ----------------------------------------------------------------------------------------------------- Revolver
def revolver():
    """REVOLVER, after the Smith & Wesson Model 29: a long round barrel with a sight rib on top and a half underlug
       (the ejector shroud) ending well short of the muzzle, a ramp front sight, an adjustable rear sight on the top
       strap, the round fluted cylinder (six flutes, six chambers, a turn of 60 degrees looks the same), the cylinder
       latch on the left, the target hammer's wide spur, the round trigger guard, big wood target grips with the
       medallion. Charcoal frame, a lighter cylinder and rib, the wood"""
    base = A.revolver()
    g = Gun('w_revolver')
    g.slot('frame', '434751'); g.slot('body', '6c685e'); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('wood', '43352b'); g.slot('glow', 'b8bcc4'); g.slot('steel', '626772')
    g.spots = dict(base.spots)
    BY, SY, CY = 0.03, g.spots['sight'][1], 0.009  # the bore, the aim line, the cylinder's axis
    # the barrel, a touch thicker at the frame, the rib on top, the ejector shroud under its back half
    tube(g, 'body_wzA__frame', 0.0185, -0.29, -0.11, y=BY, bev=0.003, hole=(0.0092, 0.02), r2=0.0205)
    g.box('body_wzA__steel', (-0.0085, 0.0085), (0.042, 0.0575), (-0.2885, -0.11), bev=0.003)
    g.prism('body_wzA__frame', [(-0.224, 0.026), (-0.11, 0.026), (-0.11, -0.017), (-0.198, -0.017), (-0.216, -0.01),
                                 (-0.224, 0.004)], 0.03, bev=0.006)
    # the ramp front sight with a light insert facing you
    g.prism('sight_wzN__frame', [(-0.2875, 0.054), (-0.25, 0.054), (-0.25, SY + 0.001), (-0.262, SY + 0.001)], 0.012, bev=0.003)
    g.box('sight_wzN__glow', (-0.0045, 0.0045), (SY - 0.008, SY - 0.001), (-0.2505, -0.2488), bev=0.0006)
    # the frame: its front round the barrel's end, the top strap, the bottom, the rear with the hammer in it
    g.prism('body_wzA__frame', [(-0.124, -0.024), (-0.113, -0.048), (-0.103, -0.048), (-0.103, 0.067), (-0.121, 0.067),
                                 (-0.126, 0.058), (-0.126, 0.0)], 0.044, bev=0.006)
    g.box('body_wzA__frame', (-0.02, 0.02), (0.053, 0.067), (-0.115, 0.03), bev=0.005)
    g.box('body_wzA__frame', (-0.022, 0.022), (-0.048, -0.035), (-0.108, 0.03), bev=0.005)
    g.prism('body_wzA__frame', [(-0.003, -0.048), (0.04, -0.05), (0.064, -0.046), (0.088, -0.038), (0.084, -0.016),
                                 (0.07, 0.022), (0.062, 0.044), (0.048, 0.062), (0.036, 0.067), (-0.003, 0.067)],
            0.046, bev=0.008)
    g.prism('body_wzN__dark', [(0.004, 0.013), (0.03, 0.012), (0.035, 0.02), (0.03, 0.028), (0.004, 0.028)], 0.006,
            x=-0.025, bev=0.002)  # the cylinder latch
    rivets(g, 'rivet_wzN__steel', 0.023, [(0.034, -0.03)], r=0.005)
    # the cylinder (node "cylinder": a chamber a shot)
    fluted(g, 'cylinder_wzB__steel', 0.043, 0.0335, CY, -0.1, 0.0)
    for k in range(6):
        a = math.pi / 6 + k * math.pi / 3
        cx_, cy_ = 0.021 * math.cos(a), CY + 0.021 * math.sin(a)
        loft(g, 'cylinder_wzN__black', [disc(cx_, cy_, 0.0085, -0.1012, 8, a), disc(cx_, cy_, 0.0085, -0.098, 8, a)],
             group=lambda i, k: 'r')
    # the hammer (node "hammer"), down: a blade from its pin and the wide checkered spur
    g.prism('hammer_wzN__dark', [(0.042, 0.024), (0.062, 0.022), (0.07, 0.04), (0.084, 0.056), (0.072, 0.066),
                                  (0.05, 0.064), (0.04, 0.05)], 0.014, bev=0.003)
    g.prism('hammer_wzN__dark', [(0.064, 0.058), (0.09, 0.056), (0.1, 0.062), (0.097, 0.071), (0.074, 0.075),
                                  (0.062, 0.07)], 0.022, bev=0.003)
    # the adjustable rear sight: a leaf on the top strap, the blade with its notch at the back
    g.prism('sight_wzN__dark', [(-0.032, 0.066), (0.042, 0.066), (0.042, 0.075), (-0.022, 0.075)], 0.022, bev=0.003)
    for xs in ((-0.0175, -0.0058), (0.0058, 0.0175)):
        g.box('sight_wzN__dark', xs, (0.066, SY + 0.002), (0.022, 0.042), bev=0.0025)
    g.box('sight_wzN__dark', (-0.0064, 0.0064), (0.066, SY - 0.009), (0.022, 0.042), bev=0.002)
    # the round trigger guard and the target trigger
    g.prism('body_wzA__frame', [(-0.074, -0.044), (-0.08, -0.068), (-0.072, -0.088), (-0.05, -0.1), (-0.01, -0.104),
                                 (0.02, -0.098), (0.038, -0.084), (0.032, -0.07), (0.014, -0.084), (-0.012, -0.09),
                                 (-0.043, -0.087), (-0.06, -0.077), (-0.065, -0.064), (-0.061, -0.044)], 0.024, bev=0.004)
    g.prism('body_wzN__dark', [(-0.03, -0.046), (-0.012, -0.046), (-0.012, -0.06), (-0.02, -0.074), (-0.03, -0.082),
                                (-0.036, -0.079), (-0.031, -0.066)], 0.014, bev=0.003)
    # big wood target grips, the medallion
    g.prism('grip_wzA__wood', [(0.034, -0.048), (0.088, -0.036), (0.1, -0.058), (0.112, -0.092), (0.124, -0.135),
                                (0.135, -0.172), (0.138, -0.194), (0.13, -0.207), (0.114, -0.211), (0.084, -0.21),
                                (0.071, -0.2), (0.06, -0.168), (0.05, -0.135), (0.04, -0.112), (0.037, -0.098),
                                (0.026, -0.086), (0.026, -0.068)], 0.056, bev=0.01)
    rivets(g, 'grip_wzN__steel', 0.028, [(0.073, -0.07)], r=0.0075)
    return g


# ------------------------------------------------------------------------------------------------------ Redline
def redline():
    """REDLINE, after the Thompson M1928: the flat-topped receiver with the cocking knob on top and the peep sight
       with ears at its back, the finned barrel (the fins are the vents that glow hotter as your HP drops), the Cutts
       compensator with its slots on top, the vertical foregrip with finger grooves, the straight stick magazine, the
       pistol grip and the buttstock in the gun's red, the selector and safety levers on the left, and the
       tachometer on the left (the needle is your fire rate). Charcoal receiver, a lighter top, near-black frame and
       barrel, the red on the furniture"""
    base = A.redline()
    g = Gun('w_redline')
    g.slot('body', '7a2a28'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('white', 'bdbbb2'); g.slot('red', 'ff2a2a', 'n'); g.slot('vent', '7a1414', 'n'); g.slot('deck', DECK)
    g.spots = dict(base.spots)
    BY, SY = 0.01, g.spots['sight'][1]
    # the receiver (charcoal) under its flat top (a step lighter), the knob in its slot, the port on the right
    g.prism('body_wzB__frame', [(-0.205, -0.022), (0.112, -0.022), (0.126, -0.006), (0.126, 0.042), (-0.205, 0.042)],
            0.064, bev=0.008)
    g.prism('cover_wzA__deck', [(-0.205, 0.038), (0.126, 0.038), (0.126, 0.049), (0.117, 0.058), (-0.197, 0.058),
                                 (-0.205, 0.05)], 0.064, bev=0.007, wtop=0.052)
    g.box('trim_wzN__black', (-0.0045, 0.0045), (0.05, 0.0588), (-0.03, 0.078), bev=0.001)
    g.cyl('cover_wzN__dark', 0.0145, (0, 0.052, 0.046), (0, 0.068, 0.046), sides=8, bev=0.004)
    g.box('trim_wzN__black', (0.0315, 0.0332), (0.0, 0.03), (-0.1, -0.03), bev=0.001)
    # the lower frame (near-black, a little narrower), its magazine well, the selector and safety on the left
    g.prism('body_wzB__dark', [(-0.192, -0.018), (0.112, -0.018), (0.12, -0.03), (0.12, -0.05), (-0.192, -0.05)],
            0.058, bev=0.007)
    g.box('body_wzB__dark', (-0.031, 0.031), (-0.074, -0.04), (-0.165, -0.076), bev=0.006)
    for z0 in (0.03, 0.074):
        g.prism('body_wzN__dark', [(z0, -0.026), (z0 + 0.024, -0.026), (z0 + 0.028, -0.034), (z0 + 0.02, -0.042),
                                    (z0 + 0.004, -0.04)], 0.004, x=-0.031, bev=0.0015)
    # the barrel, its fins (the vents: the game recolours every piece named *vents*), the foregrip's collar
    tube(g, 'barrel_wzB__dark', 0.0155, -0.41, -0.2, y=BY, bev=0.002)
    for i in range(6):
        z0 = -0.397 + i * 0.024
        tube(g, 'redline_vents_wzN__vent', 0.029, z0, z0 + 0.012, y=BY, bev=0.003)
    tube(g, 'guard_wzB__dark', 0.03, -0.26, -0.204, y=BY, bev=0.004)
    # the Cutts compensator, its slots across the top, the front blade on its back
    tube(g, 'barrel_wzB__dark', 0.024, -0.47, -0.404, y=BY, bev=0.004, hole=(0.011, 0.025))
    for z0 in (-0.462, -0.4485, -0.435, -0.4215):
        g.box('trim_wzN__black', (-0.0155, 0.0155), (BY + 0.0135, BY + 0.0232), (z0, z0 + 0.0065), bev=0.001)
    g.box('sight_wzN__frame', (-0.0105, 0.0105), (0.028, 0.047), (-0.417, -0.397), bev=0.003)
    g.box('sight_wzN__frame', (-0.0065, 0.0065), (0.04, SY), (-0.414, -0.4), bev=0.002)
    # the vertical foregrip (red) under its mount, three finger grooves down its front
    g.box('guard_wzB__dark', (-0.022, 0.022), (-0.044, -0.012), (-0.262, -0.198), bev=0.005)
    g.prism('guard_wzA__body', [(-0.252, -0.042), (-0.259, -0.06), (-0.253, -0.077), (-0.265, -0.096), (-0.258, -0.113),
                                 (-0.27, -0.132), (-0.264, -0.15), (-0.272, -0.166), (-0.264, -0.172), (-0.218, -0.172),
                                 (-0.199, -0.042)], 0.044, bev=0.008)
    # the stick magazine (node "mag"), two ribs, its plate
    g.prism('mag_wzB__dark', [(-0.158, -0.042), (-0.083, -0.042), (-0.083, -0.256), (-0.158, -0.256)], 0.046, bev=0.007)
    for y in (-0.12, -0.19):
        g.box('mag_wzB__dark', (-0.0255, 0.0255), (y - 0.006, y + 0.006), (-0.16, -0.081), bev=0.0025)
    g.box('mag_wzN__dark', (-0.027, 0.027), (-0.27, -0.252), (-0.163, -0.078), bev=0.005)
    # the trigger guard (a loop from the well to the grip), the trigger, the grip (raked as before, red)
    g.prism('grip_wzB__dark', [(-0.074, -0.048), (-0.076, -0.088), (-0.064, -0.104), (0.05, -0.104), (0.046, -0.09),
                                (-0.054, -0.09), (-0.062, -0.082), (-0.062, -0.048)], 0.026, bev=0.004)
    trigger(g, 'grip_wzB__dark', 0.0, -0.05, -0.08)
    g.prism('grip_wzA__body', raked(0.081, -0.092, 0.15, 0.06, -0.384, taper=0.004), 0.05, bev=0.009)
    # the buttstock (red) on its dark mount, the butt plate
    g.box('stock_wzB__dark', (-0.025, 0.025), (-0.046, 0.03), (0.11, 0.152), bev=0.006)
    g.prism('stock_wzA__body', [(0.145, 0.028), (0.383, 0.013), (0.383, -0.12), (0.364, -0.12), (0.31, -0.096),
                                 (0.25, -0.074), (0.195, -0.058), (0.145, -0.046)], 0.05, bev=0.01)
    g.box('stock_wzB__dark', (-0.0275, 0.0275), (-0.122, 0.018), (0.381, 0.395), bev=0.006)
    # the rear peep with its ears
    aperture(g, 'sight_wzN__frame', 0.1058, SY, ro=0.019, ri=0.009, zt=0.018, base=0.056)
    for xs in ((-0.0325, -0.0205), (0.0205, 0.0325)):
        g.box('sight_wzN__frame', xs, (0.054, 0.089), (0.094, 0.118), bev=0.004)
    # the tachometer on the left: a fat bezel, a pale face with ticks and the red arc, the needle (it turns about x
    # through GY, GZ: WeaponModels.luau keeps that pivot)
    GZ, GY = -0.04992, 0.0277
    g.cyl('gauge_wzN__dark', 0.046, (-0.03, GY, GZ), (-0.05, GY, GZ), sides=8, bev=0.004)
    g.ring('gauge_wzN__dark', 0.051, 0.04, (-0.057, GY, GZ), (-0.046, GY, GZ), sides=8, bev=0.003)
    g.cyl('gauge_wzN__white', 0.041, (-0.051, GY, GZ), (-0.047, GY, GZ), sides=8, bev=0)
    for a in (-2.3, -1.15, 0.0, 1.15):
        cy_, cz_ = GY + 0.033 * math.cos(a), GZ + 0.033 * math.sin(a)
        g.box('gauge_wzN__dark', (-0.0522, -0.0505), (cy_ - 0.0035, cy_ + 0.0035), (cz_ - 0.0035, cz_ + 0.0035), bev=0.0008)
    for a in (1.55, 1.8, 2.05, 2.3):
        cy_, cz_ = GY + 0.033 * math.cos(a), GZ + 0.033 * math.sin(a)
        g.box('arc_wzN__body', (-0.0525, -0.0505), (cy_ - 0.0055, cy_ + 0.0055), (cz_ - 0.0055, cz_ + 0.0055), bev=0.001)
    g.box('needle_wzN__red', (-0.0548, -0.0518), (GY - 0.004, GY + 0.034), (GZ - 0.0035, GZ + 0.0035), bev=0.001)
    g.cyl('gauge_wzN__dark', 0.0075, (-0.0565, GY, GZ), (-0.05, GY, GZ), sides=8, bev=0.001)
    return g


# ------------------------------------------------------------------------------------------------------- Katana
def katana():
    """KATANA, a real one: the curved blade with its ridge line (shinogi), a wavy temper line (hamon) on the bright
       edge, and a clear tip (kissaki) whose edge sweeps up to the point past a crisp yokote; the brass habaki collar,
       the round tsuba with a raised rim between two seppa, the tsuka in indigo cord with its row of diamond windows,
       the fuchi collar and the kashira cap"""
    base = A.katana()
    g = Gun('w_katana')
    g.slot('steel', '858c96'); g.slot('edge', 'cdd2d8'); g.slot('spine', '5f666f'); g.slot('body', '283459')
    g.slot('dark', DARK); g.slot('brass', '6a675e')
    g.spots = dict(base.spots)
    Z0, L, RISE = -0.139, 0.6967, 0.066
    KIS = 0.074            # the kissaki's length
    TY = 1 - KIS / L       # where it starts (the yokote), as a fraction of the blade
    RF = 0.68              # the ridge's height on the blade, edge 0 .. back 1
    def sec(t):
        """(z, edge height, back height, half thickness at the ridge) at t (0 at the collar .. 1 at the point)"""
        z = Z0 - L * t
        ye = RISE * t * t - 0.022
        ys = ye + 0.056 - 0.013 * t
        tk = 0.0075 - 0.0015 * t
        if t > TY:
            u = (t - TY) / (1 - TY)
            ys2 = ys - 0.005 * u * u
            ye = ye + (ys2 - 0.0028 - ye) * u ** 1.7
            ys, tk = ys2, tk * (1 - 0.72 * u)
        return z, ye, ys, tk
    def thick(f):
        return 0.12 + 0.88 * f / RF if f <= RF else 1 - 0.3 * (f - RF) / (1 - RF)
    def strip(piece, ts, f0, f1):
        rings = []
        for t in ts:
            z, ye, ys, tk = sec(t)
            a, b = f0(t), f1(t)
            ya, yb = ye + (ys - ye) * a, ye + (ys - ye) * b
            xa, xb = thick(a) * tk, thick(b) * tk
            rings.append([(-xa, ya, z), (xa, ya, z), (xb, yb, z), (-xb, yb, z)])
        loft(g, piece, rings)
    N, M = 36, 7
    main = [TY * i / N for i in range(N + 1)]
    tip = [TY + (1 - TY) * i / M for i in range(M + 1)]
    hamon = lambda t: 0.33 + 0.085 * math.sin(2 * math.pi * 6 * t / TY - 0.6) * min(1, t / 0.06 + 0.3)
    # the blade (the game stretches every piece named kat_blade with every kill)
    strip('kat_blade_wzB__edge', main, lambda t: 0.0, hamon)
    strip('kat_blade_wzB__steel', main, hamon, lambda t: RF)
    strip('kat_blade_wzB__spine', main + tip[1:], lambda t: RF, lambda t: 1.0)
    strip('kat_blade_wzB__edge', tip, lambda t: 0.0, lambda t: RF)
    # the habaki (brass), the round tsuba with its raised rim, the two seppa
    g.prism('kat_guard_wzN__brass', [(-0.164, -0.024), (-0.147, -0.028), (-0.147, 0.038), (-0.164, 0.035)], 0.024, bev=0.004)
    g.box('kat_guard_wzN__brass', (-0.016, 0.016), (-0.023, 0.031), (-0.149, -0.144), bev=0.0015)
    g.cyl('kat_guard_wzN__dark', 0.046, (0, 0.004, -0.143), (0, 0.004, -0.13), sides=16, bev=0.002)
    g.ring('kat_guard_wzN__dark', 0.052, 0.044, (0, 0.004, -0.145), (0, 0.004, -0.128), sides=16, bev=0.003)
    g.box('kat_guard_wzN__brass', (-0.0195, 0.0195), (-0.024, 0.029), (-0.129, -0.124), bev=0.0015)
    # the tsuka: the fuchi collar, the indigo cord, the kashira cap
    g.box('kat_tsuka_wzN__dark', (-0.0195, 0.0195), (-0.0225, 0.0265), (-0.125, -0.107), bev=0.006)
    g.box('kat_tsuka_wzA__body', (-0.0175, 0.0175), (-0.0205, 0.0245), (-0.11, 0.107), bev=0.008)
    g.prism('kat_tsuka_wzN__dark', [(0.104, -0.0225), (0.123, -0.0225), (0.131, -0.014), (0.131, 0.018), (0.123, 0.0265),
                                     (0.104, 0.0265)], 0.039, bev=0.006)
    # the diamond windows between the crossing cord (pale, as the ray skin under it): a row down each side, a row on
    # the back and the front, half a step along
    for i in range(6):
        zc = -0.0905 + i * 0.0358
        g.prism('kat_trims_wzN__edge', [(zc - 0.0148, 0.002), (zc, -0.0105), (zc + 0.0148, 0.002), (zc, 0.0145)], 0.038, bev=0.001)
    for i in range(5):
        zc = -0.0905 + i * 0.0358 + 0.0179
        g.yprism('kat_trims_wzN__edge', [(0, zc - 0.0145), (0.0078, zc), (0, zc + 0.0145), (-0.0078, zc)], -0.022, 0.026, bev=0.001)
    return g


# ----------------------------------------------------------------------------------------------------- Shredder
def shredder():
    """SHREDDER, a garden wood chipper: the big funnel hopper (16 sides, shaded round) with a fat rim, the rotor with
       its teeth inside a cage of six chunky posts, an amber band, the motor housing with its cooling slots, an amber
       top and the recoil starter with its red T pull handle on the back, the discharge chute, the carry bar, the
       grip and trigger under the motor, the power lamps and the heat gauge. Its frame is its own (the rotor's hub
       at the origin, the mouth at -z); PolishBackup.WeaponImport's W.kitShredder finds hub_wzN__dark and
       chute_wzB__frame by name"""
    base = A.shredder()
    g = Gun('w_shredder')
    g.slot('deck', DECK); g.slot('body', '686353'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('steel', '8a8f98'); g.slot('red', '7e302c'); g.slot('lamp', 'ff281e', 'n'); g.slot('white', 'd6d6cf')
    g.spots = dict(base.spots)
    # the hopper: an amber funnel, dark inside, a fat dark rim
    A.funnel(g, 'hopper_wzA__body', 'throat_wzB__dark', 0.225, 0.098, -0.333, -0.1, 0.016, sides=16)
    g.ring('rim_wzN__dark', 0.244, 0.2, (0, 0, -0.35), (0, 0, -0.31), sides=16, bev=0.008)
    # the cage round the rotor: two rings and six posts
    for z0, z1 in ((-0.116, -0.086), (0.028, 0.058)):
        g.ring('cage_wzB__frame', 0.118, 0.09, (0, 0, z0), (0, 0, z1), sides=8, bev=0.005)
    for k in range(6):
        a = math.pi / 6 + k * math.pi / 3
        tube(g, 'cage_wzB__frame', 0.016, -0.1, 0.044, y=0.104 * math.sin(a), x=0.104 * math.cos(a), bev=0.004)
    # the rotor: the shaft (sh_hub), six steel teeth a row, their blunt tips
    g.cylz('hub_wzN__dark', 0.034, -0.13, 0.05, sides=8, bev=0.004)
    for k in range(6):
        a = k * math.pi / 3 + 0.3
        c, sn = math.cos(a), math.sin(a)
        for z in (-0.066, -0.012):
            g.cyl('teeth_wzN__steel', 0.018, (c * 0.03, sn * 0.03, z), (c * 0.076, sn * 0.076, z), sides=4, bev=0.003, smooth=False)
            g.cyl('tips_wzN__steel', 0.02, (c * 0.074, sn * 0.074, z), (c * 0.088, sn * 0.088, z), sides=4, bev=0.003, smooth=False, r2=0.014)
    # the amber band, the motor: a charcoal housing, cooling slots down its sides, an amber top and stripe
    g.ring('band_wzA__body', 0.124, 0.07, (0, 0, 0.054), (0, 0, 0.08), sides=8, bev=0.005)
    g.box('motor_wzB__frame', (-0.097, 0.097), (-0.1, 0.1), (0.07, 0.33), bev=0.022)
    panel(g, 'motor_wzN__body', 0.097, 0.1, 0.3, -0.078, -0.058)
    A.deck(g, 'motor_wzN__body', 0.08, 0.098, 0.09, 0.31)
    for z0 in (0.128, 0.164, 0.2, 0.236, 0.272):
        g.box('vents_wzN__dark', (-0.0985, 0.0985), (-0.046, 0.06), (z0, z0 + 0.018), bev=0.002)
    g.box('motor_wzN__dark', (-0.08, 0.08), (-0.082, 0.082), (0.32, 0.346), bev=0.008)
    # the recoil starter on the back: a round cover and the red T pull handle
    g.cylz('starter_wzN__frame', 0.062, 0.34, 0.358, y=0.004, sides=8, bev=0.006)
    g.box('starter_wzN__dark', (-0.008, 0.008), (-0.004, 0.012), (0.356, 0.362), bev=0.002)
    g.box('pull_wzN__red', (-0.034, 0.034), (-0.005, 0.015), (0.36, 0.378), bev=0.006)
    # the chute out of the top (sh_bell2: the Tool's "up"), its dark mouth
    g.prism('chute_wzB__frame', [(0.09, 0.08), (0.175, 0.08), (0.255, 0.168), (0.212, 0.212), (0.1, 0.122)], 0.084, bev=0.01)
    g.prism('chute_wzN__black', [(0.247, 0.163), (0.256, 0.172), (0.219, 0.209), (0.21, 0.2)], 0.062, bev=0.001)
    # the carry bar over the cage
    for z0 in (-0.112, 0.034):
        g.box('bar_wzN__dark', (-0.014, 0.014), (0.1, 0.172), (z0, z0 + 0.026), bev=0.005)
    g.box('bar_wzN__dark', (-0.017, 0.017), (0.15, 0.181), (-0.118, 0.066), bev=0.007)
    # the grip under the motor and its trigger
    g.prism('grip_wzB__dark', raked(0.103, -0.168, 0.165, 0.06, -0.2, taper=0.004), 0.048, bev=0.01, x=-0.015)
    g.box('grip_wzB__dark', (-0.04, 0.01), (-0.108, -0.09), (0.07, 0.16), bev=0.006)
    g.prism('trigger_wzN__dark', [(0.05, -0.106), (0.072, -0.106), (0.068, -0.148), (0.056, -0.148)], 0.016, bev=0.003, x=-0.015)
    # two power lamps and the heat gauge on top of the motor
    g.box('sh_lamp_a_wzN__lamp', (-0.068, -0.05), (0.097, 0.108), (0.278, 0.296), bev=0.003)
    g.box('sh_lamp_b_wzN__lamp', (0.05, 0.068), (0.097, 0.108), (0.278, 0.296), bev=0.003)
    g.cyl('gauge_wzN__dark', 0.036, (-0.04, 0.096, 0.2), (-0.04, 0.114, 0.2), sides=8, bev=0.004)
    g.cyl('gauge_wzN__white', 0.027, (-0.04, 0.1135, 0.2), (-0.04, 0.1165, 0.2), sides=8, bev=0)
    g.box('needle_wzN__dark', (-0.0435, -0.0365), (0.1165, 0.12), (0.176, 0.202), bev=0.001)
    return g


BUILD = {'pistol': pistol, 'revolver': revolver, 'redline': redline, 'katana': katana, 'shredder': shredder}
