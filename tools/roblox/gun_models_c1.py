import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunkit_c import *
# VERSION C, part 1 (rules and shared pieces: gunkit_c.py; the worked example, the Assault Rifle: gun_models_c.py): the
# SMG (MP5A2), Hat Trick (FAMAS), Belt Sander (M249), Second Opinion (SVD) and Sniper (Remington 700 / M40).
#   blender -b --factory-startup -P tools/roblox/gun_models_c.py -- <out_dir> smg burst lmg dmr sniper


# ------------------------------------------------------------------------------------------------ local pieces
def rot_rect(cx, cy, along, across, ang, r0=0.0):
    """a rectangle seen from the front [(x, y)]: `along` long in the direction ang (degrees), `across` wide, its centre
       r0 out from (cx, cy) in that direction (slots and flutes round a barrel, belt links)"""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    vx, vy = -uy, ux
    c = (cx + ux * r0, cy + uy * r0)
    return [(c[0] + ux * su * along / 2 + vx * sv * across / 2, c[1] + uy * su * along / 2 + vy * sv * across / 2)
            for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def arch(cx, cy, ro, ri, angs):
    """a half shell over a barrel seen from the front [(x, y)]: the outer arc through angs (degrees), back on the inner"""
    out = [(cx + ro * math.cos(math.radians(a)), cy + ro * math.sin(math.radians(a))) for a in angs]
    inn = [(cx + ri * math.cos(math.radians(a)), cy + ri * math.sin(math.radians(a))) for a in reversed(angs)]
    return out + inn


def wedge_w(w, wtop, y0, y1):
    """the width of a wedge-section prism (w at its lowest point y0, wtop at its highest y1) at a height"""
    return lambda y: w + (wtop - w) * (y - y0) / (y1 - y0)


def vent(g, piece, prof, wat, proud=0.0016, bev=0.0015):
    """a dark slot let into both sides of a wedge-section block: prof its side outline, wat the block's width at a height"""
    ys = [p[1] for p in prof]
    g.prism(piece, prof, wat(min(ys)) + 2 * proud, bev=bev, wtop=wat(max(ys)) + 2 * proud)


def edge_z(ctrl, y, n=24):
    """where a curved magazine's edge (3 control points [(z, y)]) is at a height"""
    pts = bez(*ctrl, n)
    for (z0, y0), (z1, y1) in zip(pts, pts[1:]):
        if (y0 - y) * (y1 - y) <= 0 and y1 != y0:
            return z0 + (z1 - z0) * (y - y0) / (y1 - y0)
    return pts[-1][0]


def mag_ribs(g, piece, front, back, ys, w, h=0.013, inset=0.004):
    """raised bands across a curved magazine at the heights ys, following its curve"""
    for y in ys:
        z0 = max(edge_z(front, y - h / 2), edge_z(front, y + h / 2)) + inset
        z1 = min(edge_z(back, y - h / 2), edge_z(back, y + h / 2)) - inset
        g.box(piece, (-w / 2, w / 2), (y - h / 2, y + h / 2), (z0, z1), bev=0.003)


# ------------------------------------------------------------------------------------------------------------ SMG
def smg():
    """SMG, after the HK MP5A2: the tall receiver with the cocking tube running on over the barrel to a HOODED front
       post, a DRUM rear sight, the slim curved magazine, the tapered handguard with its lip, the trigger pack with the
       big guard, the solid triangular A2 stock. Teal on the handguard and stock, charcoal receiver, a lighter top"""
    base = A.smg()
    g = Gun('w_smg')
    g.slot('deck', DECK); g.slot('body', '30605d'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('steel', STEEL)
    g.spots = dict(base.spots)
    BY, SY = 0.01, g.spots['sight'][1]  # the barrel's height, the aim line (0.054)
    # receiver (charcoal), narrower on top, the lighter top cover along it (node "cover")
    g.prism('body_wzB__frame', [(-0.168, -0.034), (0.128, -0.034), (0.128, 0.03), (0.116, 0.041), (-0.168, 0.041)],
            0.056, bev=0.007, wtop=0.046)
    g.box('cover_wzA__deck', (-0.02, 0.02), (0.035, 0.048), (-0.164, 0.114), bev=0.005, wtop=0.031)
    rivets(g, 'rivet_wzN__steel', 0.027, [(0.11, -0.043), (-0.032, -0.043)])
    vent(g, 'body_wzN__dark', rect(-0.15, 0.1, -0.006, 0.006), wedge_w(0.056, 0.046, -0.034, 0.041))
    # the cocking tube over the barrel, its slot on the left, the handle at its front left (node "charge")
    tube(g, 'body_wzB__frame', 0.0125, -0.304, -0.16, y=0.03, bev=0.003)
    g.box('trim_wzN__black', (-0.0128, -0.0075), (0.0262, 0.0338), (-0.262, -0.19), bev=0.001)
    g.box('charge_wzB__dark', (-0.04, -0.008), (0.023, 0.038), (-0.283, -0.265), bev=0.004)
    g.cyl('charge_wzB__dark', 0.0105, (-0.051, 0.0305, -0.274), (-0.034, 0.0305, -0.274), sides=8, bev=0.003)
    # the tapered handguard (teal, node "fore"), its lip at the front
    g.prism('fore_wzA__body', [(-0.166, 0.03), (-0.166, -0.047), (-0.27, -0.032), (-0.281, -0.039), (-0.296, -0.035),
                                (-0.296, 0.019), (-0.287, 0.028)], 0.06, bev=0.008, wtop=0.034)
    # barrel, the muzzle collar
    tube(g, 'barrel_wzB__dark', 0.0135, -0.352, -0.29, y=BY, bev=0.003)
    tube(g, 'barrel_wzB__dark', 0.0175, -0.37, -0.341, y=BY, bev=0.004, hole=(0.0082, 0.02))
    # the hooded front post: a block round barrel and tube, a ring hood, the post inside it (its top the aim line)
    FZ = -0.299
    g.box('sight_wzN__frame', (-0.017, 0.017), (BY - 0.017, 0.045), (FZ - 0.014, FZ + 0.014), bev=0.005)
    g.ring('sight_wzN__frame', 0.0195, 0.0128, (0, SY, FZ - 0.011), (0, SY, FZ + 0.011), sides=8, bev=0.003)
    g.box('sight_wzN__frame', (-0.0052, 0.0052), (0.036, SY), (FZ - 0.0055, FZ + 0.0055), bev=0.0015)
    # the drum rear sight: an aperture on the aim line between the drum's two ends, on a foot
    RZ = 0.102
    g.box('sight_wzN__frame', (-0.022, 0.022), (0.04, 0.05), (RZ - 0.02, RZ + 0.02), bev=0.004)
    aperture(g, 'sight_wzN__frame', RZ, SY, ro=0.0175, ri=0.0082, zt=0.02)
    for sx in (-1, 1):
        g.cyl('sight_wzN__frame', 0.0185, (sx * 0.0095, SY, RZ), (sx * 0.0215, SY, RZ), sides=8, bev=0.003)
    # magazine well, the slim curved magazine (node "mag"), a rib down its side, a teal base plate
    g.box('body_wzB__frame', (-0.025, 0.025), (-0.07, -0.03), (-0.158, -0.058), bev=0.005)
    MF, MB = [(-0.148, -0.05), (-0.15, -0.13), (-0.185, -0.208)], [(-0.07, -0.05), (-0.073, -0.13), (-0.11, -0.205)]
    fb, bb = curved_mag(g, 'mag_wzB__dark', MF, MB, 0.036, bev=0.006)
    curved_mag(g, 'mag_wzB__dark', [(-0.128, -0.078), (-0.13, -0.13), (-0.157, -0.188)],
               [(-0.09, -0.078), (-0.093, -0.13), (-0.12, -0.186)], 0.041, bev=0.003)
    plate(g, 'mag_wzN__body', fb, bb, 0.016, 0.044, bev=0.005)
    # the trigger pack under the back (near-black): its housing, the grip, the big guard, the trigger
    g.prism('grip_wzB__dark', [(-0.05, -0.026), (0.128, -0.026), (0.128, -0.046), (0.106, -0.062), (-0.042, -0.062),
                                (-0.05, -0.054)], 0.054, bev=0.006)
    g.prism('grip_wzB__dark', raked(0.07, -0.1, 0.15, 0.058, -0.244, taper=0.005), 0.048, bev=0.01)
    guard(g, 'grip_wzB__dark', -0.046, 0.05, -0.094, t=0.018, hw=0.014)
    g.box('grip_wzB__dark', (-0.0135, 0.0135), (-0.09, -0.055), (-0.046, -0.028), bev=0.004)
    trigger(g, 'grip_wzB__dark', 0.004, -0.058, -0.074)
    # the A2 stock: one solid teal wedge (a level top, a sloped underside), a dark butt plate, the kit's mark
    g.prism('stock_wzA__body', [(0.12, -0.056), (0.12, 0.041), (0.262, 0.036), (0.262, -0.112), (0.236, -0.112)],
            0.05, bev=0.009)
    g.box('stock_wzB__dark', (-0.028, 0.028), (-0.118, 0.042), (0.258, 0.284), bev=0.007)
    kit_mark(g, 'mark_wzN__dark', 0.162, -0.05, -0.008, 0.052, gap=0.026, t=0.013)
    # the ejection port on the right
    g.box('trim_wzN__black', (0.0232, 0.0272), (0.004, 0.026), (-0.13, -0.058), bev=0.001)
    return g


# ------------------------------------------------------------------------------------------------------ Hat Trick
def burst():
    """HAT TRICK, after the FAMAS (a bullpup): the long carry handle over the whole top with the rear sight in its back
       and a post at its front, the charging lever under it, the big trigger guard round the hand, the magazine behind
       the grip, the short barrel with the grenade rings and a slotted flash hider, the cheek rest. Blue body, charcoal
       handle with a lighter top, its three blue squares (the three-round burst)"""
    base = A.burst()
    g = Gun('w_burst')
    g.slot('deck', DECK); g.slot('body', '44577c'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('steel', STEEL)
    g.spots = dict(base.spots)
    BY, SY = 0.012, g.spots['sight'][1]  # 0.1448
    # the bullpup body (blue): from the trigger back to the butt, the cheek rest rising at its back
    BODY = [(-0.2, -0.042), (-0.2, 0.056), (0.2, 0.056), (0.245, 0.08), (0.478, 0.08), (0.5, 0.068), (0.5, -0.125),
            (0.43, -0.125), (0.17, -0.078), (0.0, -0.078), (-0.045, -0.042)]
    g.prism('body_wzA__body', BODY, 0.07, bev=0.01, wtop=0.058)
    bw = wedge_w(0.07, 0.058, -0.125, 0.08)
    g.box('deck_wzA__deck', (-0.025, 0.025), (0.052, 0.061), (-0.195, 0.205), bev=0.003)
    g.box('deck_wzA__deck', (-0.024, 0.024), (0.076, 0.085), (0.252, 0.47), bev=0.003)
    vent(g, 'body_wzN__dark', rect(0.31, 0.43, -0.03, 0.022), bw)
    rivets(g, 'rivet_wzN__steel', 0.5 * bw(-0.03), [(0.46, -0.03), (0.46, -0.09)])
    g.box('stock_wzB__dark', (-0.036, 0.036), (-0.132, 0.075), (0.495, 0.54), bev=0.008)
    # the fore-end (charcoal) with four upright vents a side
    FORE = [(-0.39, -0.016), (-0.375, -0.03), (-0.196, -0.036), (-0.196, 0.054), (-0.37, 0.05), (-0.39, 0.034)]
    g.prism('fore_wzB__frame', FORE, 0.066, bev=0.008, wtop=0.052)
    fw = wedge_w(0.066, 0.052, -0.036, 0.054)
    for z0 in (-0.355, -0.32, -0.285, -0.25):
        vent(g, 'fore_wzN__dark', rect(z0, z0 + 0.016, -0.014, 0.03), fw)
    # the barrel: the grenade sleeve and its two rings, the slotted flash hider
    tube(g, 'barrel_wzB__dark', 0.016, -0.6, -0.385, y=BY, bev=0.003)
    tube(g, 'barrel_wzB__dark', 0.021, -0.6, -0.47, y=BY, bev=0.004)
    for z0 in (-0.59, -0.5):
        tube(g, 'barrel_wzB__dark', 0.025, z0, z0 + 0.016, y=BY, bev=0.003)
    tube(g, 'barrel_wzB__dark', 0.024, -0.67, -0.598, y=BY, bev=0.004, hole=(0.011, 0.025))
    for ang in (45, 135, 225, 315):
        g.xprism('trim_wzN__black', rot_rect(0, BY, 0.012, 0.008, ang, r0=0.019), -0.655, -0.612, bev=0.001)
    # the carry handle (charcoal, a lighter top): a long bar on a front foot and a rear foot, open under its middle
    g.prism('handle_wzB__frame', [(-0.345, 0.1), (0.192, 0.1), (0.204, 0.112), (0.192, 0.132), (-0.33, 0.132),
                                  (-0.345, 0.12)], 0.04, bev=0.007)
    g.prism('handle_wzB__frame', [(-0.345, 0.045), (-0.27, 0.045), (-0.262, 0.106), (-0.345, 0.106)], 0.04, bev=0.006)
    g.prism('handle_wzB__frame', [(0.085, 0.106), (0.108, 0.052), (0.212, 0.052), (0.204, 0.106)], 0.042, bev=0.006)
    g.box('handle_wzN__deck', (-0.0155, 0.0155), (0.127, 0.1365), (-0.33, 0.188), bev=0.003)
    for z0 in (-0.215, -0.17, -0.125):  # three blue squares: the three-round burst
        g.box('handle_wzA__body', (-0.0215, 0.0215), (0.104, 0.139), (z0, z0 + 0.028), bev=0.003)
    # the sights: the post with ears at the handle's front, the aperture between two ears at its back
    post(g, 'handle_wzN__frame', -0.318, 0.106, SY, hw=0.019, ear=0.011, zt=0.028)
    aperture(g, 'handle_wzN__frame', 0.1204, SY, ro=0.0155, ri=0.0075, zt=0.018)
    for x0, x1 in ((-0.026, -0.0135), (0.0135, 0.026)):
        g.box('handle_wzN__frame', (x0, x1), (0.124, 0.159), (0.103, 0.138), bev=0.004)
    # the charging lever under the handle (node "charge")
    g.box('charge_wzB__dark', (-0.013, 0.013), (0.052, 0.092), (-0.15, -0.1), bev=0.004)
    g.box('charge_wzB__dark', (-0.026, 0.026), (0.07, 0.09), (-0.15, -0.124), bev=0.004)
    # the grip, the big guard round the hand (node "loop"), the trigger
    g.prism('grip_wzB__dark', raked(-0.105, -0.135, 0.17, 0.062, -0.07, taper=0.004), 0.05, bev=0.01)
    g.prism('loop_wzB__dark', [(-0.253, -0.034), (-0.219, -0.034), (-0.219, -0.2), (-0.206, -0.213), (-0.07, -0.213),
                                (-0.064, -0.25), (-0.228, -0.25), (-0.253, -0.226)], 0.032, bev=0.008)
    trigger(g, 'grip_wzB__dark', -0.168, -0.04, -0.07)
    # the magazine behind the grip (node "mag"), two ribs, a blue base plate
    g.prism('mag_wzB__dark', [(0.02, -0.06), (0.136, -0.06), (0.13, -0.248), (0.016, -0.248)], 0.052, bev=0.008)
    for y in (-0.13, -0.19):
        g.box('mag_wzB__dark', (-0.029, 0.029), (y - 0.007, y + 0.007), (0.022, 0.13), bev=0.003)
    plate(g, 'mag_wzN__body', (0.016, -0.248), (0.13, -0.248), 0.022, 0.06, bev=0.006)
    # the ejection port on the right, under the cheek rest
    g.box('trim_wzN__black', (0.5 * bw(0.04) - 0.002, 0.5 * bw(0.04) + 0.0025), (0.024, 0.052), (0.04, 0.14), bev=0.001)
    return g


# ---------------------------------------------------------------------------------------------------- Belt Sander
def belt_path(p0, p1, p2, n, dense=60):
    """n points evenly spaced along a quadratic curve in the front view [(x, y)], with the curve's direction there
       (degrees); index 0 at p2 (the gun's end)"""
    pts = []
    for i in range(dense + 1):
        t = i / dense
        a, b, c = (1 - t) ** 2, 2 * (1 - t) * t, t * t
        pts.append((a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]))
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(dense)]
    L = sum(seg)
    out = []
    for k in range(n):
        s = L * (1 - (k + 0.5) / n)
        acc = 0.0
        for i in range(dense):
            if acc + seg[i] >= s or i == dense - 1:
                f = (s - acc) / seg[i] if seg[i] else 0
                x = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f
                y = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f
                ang = math.degrees(math.atan2(pts[i + 1][1] - pts[i][1], pts[i + 1][0] - pts[i][0]))
                out.append((x, y, ang))
                break
            acc += seg[i]
    return out, L / n


def lmg():
    """BELT SANDER, after the M249 SAW: the boxy receiver under a big flat feed cover (it lifts), the feed tray on the
       left with the belt running up into it from the box under the left, the barrel with a slotted heat shield (it
       glows), a carry handle folded down to the right, the gas tube and block under the barrel, a tall front post and a
       birdcage; the stock. The power tool: the handguard is the sander, a grit belt round two rollers under it, a cord
       out of the stock. Orange on the sander and stock, charcoal receiver, a lighter cover"""
    base = A.lmg()
    g = Gun('w_lmg')
    g.slot('deck', DECK); g.slot('paper', '7d7262'); g.slot('body', '6a4632'); g.slot('frame', FRAME); g.slot('dark', DARK)
    g.slot('black', BLACK); g.slot('grit', '3a3632'); g.slot('link', '50545d')
    g.spots = dict(base.spots)
    BY, SY = 0.02, g.spots['sight'][1]  # 0.10379
    # receiver (charcoal), a dark panel low on each side
    g.prism('body_wzB__frame', [(-0.205, -0.066), (0.17, -0.066), (0.205, -0.03), (0.205, 0.052), (-0.205, 0.052)],
            0.078, bev=0.009)
    panel(g, 'body_wzN__dark', 0.039, 0.0, 0.16, -0.05, -0.016)
    # the feed cover (node "cover", it lifts round its back): one lighter block over the receiver's top
    g.prism('cover_wzA__deck', [(-0.146, 0.05), (0.088, 0.05), (0.088, 0.08), (0.07, 0.095), (-0.122, 0.095),
                                (-0.146, 0.076)], 0.074, bev=0.008, wtop=0.058)
    g.box('cover_wzN__frame', (-0.03, 0.03), (0.046, 0.06), (-0.15, 0.092), bev=0.003)
    # the feed tray on the left, its dark mouth, and the belt: twelve links from the box up into it, low on the side
    g.box('body_wzB__dark', (-0.048, -0.036), (-0.018, 0.034), (-0.128, -0.032), bev=0.004)
    g.box('trim_wzN__black', (-0.0495, -0.044), (-0.008, 0.024), (-0.12, -0.04), bev=0.001)
    links, pitch = belt_path((-0.072, -0.072), (-0.094, -0.03), (-0.052, 0.008), 12)
    for k, (x, y, ang) in enumerate(links):  # belt_00 at the tray, belt_11 at the box (the box end runs out first)
        z0, z1 = (-0.115, -0.05) if k % 2 == 0 else (-0.108, -0.043)
        g.xprism('belt_%02d_wzN__link' % k, rot_rect(x, y, pitch * 0.82, 0.017, ang), z0, z1, bev=0.0015)
    # the ammunition box under the left (node "mag"): an orange band, the lip the belt leaves by
    g.box('mag_wzB__dark', (-0.086, 0.022), (-0.236, -0.062), (-0.178, 0.0), bev=0.01)
    g.box('mag_wzN__body', (-0.0885, 0.0245), (-0.122, -0.1), (-0.1805, 0.0025), bev=0.004)
    g.box('mag_wzB__dark', (-0.084, -0.054), (-0.08, -0.058), (-0.124, -0.036), bev=0.004)
    # the barrel, the birdcage, the heat shield over it (piece "lmg_heat": the game warms it as you fire), its slots
    tube(g, 'barrel_wzB__dark', 0.018, -0.82, -0.2, y=BY, bev=0.003)
    brake(g, 'barrel_wzB__dark', 'trim_wzN__black', -0.87, -0.81, BY, 0.023, ports=2, hole=0.01)
    g.xprism('lmg_heat_wzN__dark', arch(0, BY, 0.027, 0.0205, (-18, 22.5, 67.5, 112.5, 157.5, 198)), -0.74, -0.33, bev=0.002)
    for z0 in (-0.7, -0.63, -0.56, -0.49, -0.42):
        g.box('trim_wzN__black', (-0.0085, 0.0085), (BY + 0.0215, BY + 0.0262), (z0, z0 + 0.034), bev=0.001)
    # the gas tube and block under the barrel
    tube(g, 'barrel_wzB__dark', 0.014, -0.69, -0.48, y=BY - 0.037, bev=0.003)
    g.box('barrel_wzB__dark', (-0.021, 0.021), (BY - 0.054, BY + 0.01), (-0.7, -0.66), bev=0.005)
    g.box('barrel_wzB__frame', (-0.024, 0.024), (BY - 0.062, BY - 0.04), (-0.652, -0.62), bev=0.005)  # the bipod's yoke
    for sx in (-1, 1):  # its legs, folded forward
        g.box('barrel_wzB__frame', sorted((sx * 0.007, sx * 0.022)), (BY - 0.07, BY - 0.054), (-0.75, -0.62), bev=0.004)
        g.box('barrel_wzB__frame', sorted((sx * 0.005, sx * 0.024)), (BY - 0.078, BY - 0.05), (-0.776, -0.745), bev=0.005)
    # the carry handle, folded down to the right: a clamp on the barrel, an arm, the bar
    g.box('barrel_wzB__frame', (-0.024, 0.024), (BY - 0.004, BY + 0.027), (-0.312, -0.276), bev=0.005)
    g.box('barrel_wzB__frame', (0.02, 0.05), (0.03, 0.046), (-0.306, -0.282), bev=0.004)
    g.box('barrel_wzB__frame', (0.039, 0.058), (0.026, 0.05), (-0.44, -0.27), bev=0.006)
    # the sander under the barrel (the handguard, orange), its grit belt round two rollers (the off hand holds it)
    g.prism('sander_wzA__body', [(-0.49, -0.03), (-0.206, -0.03), (-0.206, 0.024), (-0.47, 0.024), (-0.49, 0.008)],
            0.084, bev=0.009, wtop=0.07)
    g.prism('belt_wzN__grit', stadium(-0.505, -0.215, -0.036, 0.03), 0.072, bev=0.004)
    for z in (-0.475, -0.245):
        g.cyl('roller_wzN__frame', 0.023, (-0.046, -0.036, z), (0.046, -0.036, z), sides=8, bev=0.004)
    # sights: the rear aperture on a block behind the cover (an elevation knob on its right), the tall front post
    g.box('sight_wzN__frame', (-0.024, 0.024), (0.05, 0.074), (0.092, 0.14), bev=0.005)
    aperture(g, 'sight_wzN__frame', 0.112, SY, ro=0.018, ri=0.0088, zt=0.02, base=0.07)
    g.cyl('sight_wzN__frame', 0.012, (0.022, 0.062, 0.118), (0.037, 0.062, 0.118), sides=8, bev=0.003)
    g.box('sight_wzN__frame', (-0.022, 0.022), (BY - 0.022, 0.045), (-0.812, -0.778), bev=0.005)
    post(g, 'sight_wzN__frame', -0.795, 0.04, SY, hw=0.02, ear=0.011, zt=0.03)
    # the charging handle on the right, the link chute (port) on the right
    g.box('body_wzB__dark', (0.038, 0.056), (0.0, 0.024), (-0.182, -0.15), bev=0.004)
    g.box('trim_wzN__black', (0.0385, 0.042), (0.016, 0.044), (-0.11, -0.01), bev=0.001)
    # grip, the trigger guard (node "guard"), trigger
    g.prism('grip_wzB__dark', raked(0.142, -0.132, 0.18, 0.066, -0.297, taper=0.005), 0.052, bev=0.01)
    guard(g, 'guard_wzB__dark', 0.0, 0.12, -0.124, t=0.018, hw=0.014)
    g.box('guard_wzB__dark', (-0.014, 0.014), (-0.124, -0.06), (0.0, 0.02), bev=0.004)
    trigger(g, 'guard_wzB__dark', 0.06, -0.064, -0.1)
    # the stock (orange): a straight top, a sloped hollow underside to the toe; a dark pad, the kit's mark, the cord
    g.prism('stock_wzA__body', [(0.198, -0.058), (0.198, 0.05), (0.5, 0.058), (0.518, 0.046), (0.518, -0.155),
                                 (0.44, -0.155), (0.33, -0.078), (0.27, -0.06)], 0.062, bev=0.01)
    g.box('stock_wzB__dark', (-0.035, 0.035), (-0.162, 0.064), (0.512, 0.545), bev=0.008)
    kit_mark(g, 'mark_wzN__dark', 0.36, -0.03, 0.03, 0.064, gap=0.032, t=0.016)
    g.cyl('cord_wzN__dark', 0.016, (0, -0.15, 0.47), (0, -0.205, 0.478), sides=8, bev=0.004, r2=0.012)
    return g


# ------------------------------------------------------------------------------------------------- Second Opinion
def dmr():
    """SECOND OPINION, after the SVD Dragunov: the open skeleton stock (the steep grip, a thick comb, a bottom bar and
       the butt round the big thumbhole), the slim handguard with long oval vents, the long thin barrel with a slotted
       flash hider and a hooded front post, the side-mounted scope with its square turret block; its name: a second,
       small round optic beside the first. Purple on the stock and handguard, charcoal receiver, a lighter cover"""
    base = A.dmr()
    g = Gun('w_dmr')
    g.slot('body', '4f4b62'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('glow', '9fb6c8'); g.slot('steel', STEEL); g.slot('deck', DECK)
    g.spots = dict(base.spots)
    BY, SY = 0.02, g.spots['sight'][1]  # 0.11996
    # receiver (charcoal) and its dust cover (a lighter top), rivets, the port on the right
    g.prism('body_wzB__frame', [(-0.178, -0.04), (0.1, -0.04), (0.142, -0.006), (0.142, 0.05), (-0.178, 0.05)], 0.062, bev=0.008)
    g.prism('deck_wzB__deck', [(-0.122, 0.044), (0.146, 0.044), (0.152, 0.054), (0.14, 0.07), (-0.122, 0.07)], 0.058,
            bev=0.007, wtop=0.044)
    rivets(g, 'rivet_wzN__steel', 0.031, [(-0.145, -0.022), (0.075, -0.022)])
    g.box('trim_wzN__black', (0.029, 0.0335), (0.012, 0.042), (-0.1, -0.012), bev=0.001)
    # the charging knob on the right (node "charge")
    g.box('charge_wzB__dark', (0.028, 0.046), (0.016, 0.034), (-0.014, 0.012), bev=0.003)
    g.cyl('charge_wzB__dark', 0.0115, (0.041, 0.025, -0.001), (0.058, 0.025, -0.001), sides=8, bev=0.003)
    # the slim handguard (purple), three long oval vents a side
    HG = [(-0.17, -0.036), (-0.17, 0.056), (-0.505, 0.05), (-0.53, 0.038), (-0.53, -0.014), (-0.512, -0.026)]
    g.prism('guard_wzA__body', HG, 0.058, bev=0.008, wtop=0.046)
    hw = wedge_w(0.058, 0.046, -0.036, 0.056)
    for z0 in (-0.47, -0.39, -0.31):
        vent(g, 'guard_wzN__dark', stadium(z0, z0 + 0.062, 0.016, 0.0085), hw)
    # the gas block, the long barrel, the hooded front post, the slotted flash hider
    g.box('barrel_wzB__dark', (-0.02, 0.02), (BY - 0.019, 0.056), (-0.575, -0.528), bev=0.005)
    tube(g, 'barrel_wzB__dark', 0.019, -0.82, -0.52, y=BY, bev=0.003)
    FZ = -0.785
    g.box('barrel_wzB__dark', (-0.016, 0.016), (BY - 0.016, 0.054), (FZ - 0.016, FZ + 0.016), bev=0.004)
    g.ring('barrel_wzB__dark', 0.0165, 0.011, (0, 0.066, FZ - 0.011), (0, 0.066, FZ + 0.011), sides=8, bev=0.003)
    g.box('barrel_wzB__dark', (-0.005, 0.005), (0.05, 0.068), (FZ - 0.005, FZ + 0.005), bev=0.0015)
    tube(g, 'barrel_wzB__dark', 0.0205, -0.8915, -0.808, y=BY, bev=0.004, hole=(0.0095, 0.03))
    for ang in (45, 135, 225, 315):
        g.xprism('trim_wzN__black', rot_rect(0, BY, 0.012, 0.0075, ang, r0=0.0165), -0.874, -0.824, bev=0.001)
    # the scope over the aim line: a tube, the objective bell with pale glass, a purple band, the square turret block
    # (a knob on top and one on the right), the long eyepiece and its rubber cup
    tube(g, 'scope_wzN__frame', 0.024, -0.14, 0.05, y=SY, bev=0.004)
    tube(g, 'scope_wzN__frame', 0.032, -0.215, -0.168, y=SY, bev=0.005, hole=(0.0255, 0.012))
    tube(g, 'scope_wzN__frame', 0.031, -0.172, -0.128, y=SY, bev=0.003, r2=0.024)
    tube(g, 'lens_wzN__glow', 0.0258, -0.204, -0.2, y=SY, bev=0)
    tube(g, 'scope_wzA__body', 0.0262, -0.118, -0.098, y=SY, bev=0.002)
    g.box('scope_wzN__frame', (-0.028, 0.028), (SY - 0.022, SY + 0.025), (-0.066, -0.008), bev=0.008)
    g.cyl('scope_wzN__frame', 0.0165, (0, SY + 0.02, -0.037), (0, SY + 0.042, -0.037), sides=8, bev=0.004)
    g.cyl('scope_wzN__frame', 0.015, (0.024, SY, -0.037), (0.046, SY, -0.037), sides=8, bev=0.004)
    tube(g, 'scope_wzN__frame', 0.024, 0.045, 0.1, y=SY, bev=0.003, r2=0.028)
    tube(g, 'scope_wzN__dark', 0.03, 0.162, 0.096, y=SY, bev=0.006, hole=(0.021, 0.012))
    tube(g, 'lens_wzN__glow', 0.0212, 0.151, 0.147, y=SY, bev=0)
    # the side mount: from a rail on the receiver's left, over the cover, up under the scope; its clamp lever
    g.xprism('scope_wzN__frame', [(-0.052, 0.0), (-0.0305, 0.0), (-0.0305, 0.073), (0.014, 0.073), (0.014, 0.099),
                                  (-0.052, 0.099)], -0.086, 0.044, bev=0.004)
    g.cyl('scope_wzN__dark', 0.0095, (-0.051, 0.03, -0.03), (-0.064, 0.03, -0.03), sides=8, bev=0.003)
    # the second opinion: a small round optic on the mount's left edge, beside the first, its pale lens toward you
    OX, OY = -0.048, SY - 0.006
    tube(g, 'scope_wzN__frame', 0.0145, -0.045, 0.05, y=OY, x=OX, bev=0.004)
    tube(g, 'scope_wzN__frame', 0.0175, -0.075, -0.04, y=OY, x=OX, bev=0.004, hole=(0.0125, 0.008))
    tube(g, 'lens_wzN__glow', 0.0126, -0.068, -0.065, y=OY, x=OX, bev=0)
    tube(g, 'scope_wzA__body', 0.0155, 0.022, 0.034, y=OY, x=OX, bev=0.002)
    tube(g, 'lens_wzN__glow', 0.0105, 0.05, 0.053, y=OY, x=OX, bev=0)
    # the magazine (node "mag"): short, a little curved, two ribs, a purple base plate
    MF, MB = [(-0.088, -0.03), (-0.091, -0.1), (-0.105, -0.162)], [(0.03, -0.03), (0.028, -0.1), (0.016, -0.166)]
    fb, bb = curved_mag(g, 'mag_wzB__dark', MF, MB, 0.054, bev=0.008)
    mag_ribs(g, 'mag_wzB__dark', MF, MB, (-0.075, -0.12), 0.06)
    plate(g, 'mag_wzN__body', fb, bb, 0.02, 0.062, bev=0.006)
    # the trigger guard and trigger
    guard(g, 'body_wzB__frame', 0.035, 0.2, -0.085, t=0.018, hw=0.013)
    g.box('body_wzB__frame', (-0.013, 0.013), (-0.085, -0.038), (0.035, 0.053), bev=0.004)
    trigger(g, 'body_wzB__frame', 0.115, -0.02, -0.064)
    # the skeleton stock (purple): the comb and butt in one (an upside-down L), the grip and the bottom bar in one
    # (an L), the thumbhole open between them; a dark butt pad
    gfb, gbb, gbt, gft = raked(0.24, -0.1, 0.172, 0.064, -0.646, taper=0.004)
    dz, dy = gbb[0] - gbt[0], gbb[1] - gbt[1]
    def back_edge(y): return (gbt[0] + dz * (y - gbt[1]) / dy, y)
    g.prism('stock_wzA__body', [(0.128, 0.062), (0.26, 0.066), (0.3, 0.086), (0.47, 0.086), (0.5, 0.072), (0.586, 0.072),
                                 (0.586, -0.194), (0.508, -0.194), (0.508, 0.0), (0.22, 0.0), (0.128, 0.008)], 0.056, bev=0.01)
    g.prism('stock_wzA__body', [(0.128, -0.036), (0.128, 0.006), back_edge(0.006), back_edge(-0.142), (0.514, -0.142),
                                 (0.514, -0.19), (gfb[0] + 0.004, -0.19), gfb, gft], 0.047, bev=0.009)
    g.box('stock_wzB__dark', (-0.03, 0.03), (-0.2, 0.078), (0.582, 0.6), bev=0.007)
    return g


# ------------------------------------------------------------------------------------------------------------ Sniper
def sniper():
    """SNIPER, after the Remington 700 / M40: the round action with a rail, the bolt at its back (a bent handle and a
       fat knob on the right), the heavy fluted barrel and a big ported brake, the big tactical scope in high rings
       (three turrets, a fat bell, a long eyepiece), a detachable box magazine, and ONE solid stock: a wide flat
       fore-end, a near-vertical grip, a high comb, a straight belly to the toe. Crimson stock, charcoal action"""
    base = A.sniper()
    g = Gun('w_sniper')
    g.slot('body', '523847'); g.slot('frame', FRAME); g.slot('dark', DARK); g.slot('black', BLACK)
    g.slot('glow', '9fb6c8'); g.slot('steel', STEEL); g.slot('accent', '5c4152'); g.slot('deck', DECK)
    g.spots = dict(base.spots)
    BY, SY = 0.02, g.spots['sight'][1]  # 0.12354
    # the stock: one solid piece (fore-end, wrist, comb and butt in one outline, the grip grown out of its underside)
    g.prism('stock_wzA__body', [(-0.84, 0.004), (-0.855, -0.028), (-0.83, -0.1), (0.1, -0.1), (0.165, -0.108),
                                 (0.576, -0.245), (0.576, 0.088), (0.315, 0.088), (0.248, 0.0)],
            0.08, bev=0.012, wtop=0.066)
    g.prism('stock_wzA__body', raked(0.135, -0.15, 0.215, 0.072, -0.14, taper=0.007), 0.062, bev=0.011)
    g.prism('stock_wzB__dark', rect(0.571, 0.597, -0.245, 0.088), 0.081, bev=0.007, wtop=0.0675)
    sw = wedge_w(0.08, 0.066, -0.245, 0.088)
    vent(g, 'mark_wzN__dark', rect(-0.77, -0.75, -0.074, -0.024), sw)
    vent(g, 'mark_wzN__dark', rect(-0.73, -0.71, -0.074, -0.024), sw)
    # the round action (charcoal) and its rail (lighter), the port on the right
    tube(g, 'body_wzB__frame', 0.033, -0.36, 0.035, y=BY, bev=0.005)
    tube(g, 'body_wzB__frame', 0.04, -0.382, -0.352, y=BY, bev=0.004)
    rail(g, 'deck_wzB__deck', 'trim_wzN__black', -0.35, 0.03, BY + 0.027, hw=0.016, h=0.012)
    g.box('trim_wzN__black', (0.0275, 0.033), (0.011, 0.029), (-0.178, -0.072), bev=0.001)
    # the bolt (node "bolt": it lifts round the bore and slides back): its body in the action, the shroud at the back,
    # the bent handle down to the right, the fat knob
    tube(g, 'bolt_wzB__steel', 0.0195, -0.1, 0.04, y=BY, bev=0.003)
    tube(g, 'bolt_wzB__steel', 0.0235, 0.03, 0.085, y=BY, bev=0.004, r2=0.019)
    g.cyl('bolt_wzB__steel', 0.0095, (0.0, BY, 0.05), (0.066, BY - 0.033, 0.068), sides=8, bev=0.002)
    g.cyl('bolt_wzN__accent', 0.02, (0.058, BY - 0.029, 0.066), (0.094, BY - 0.047, 0.075), sides=8, bev=0.006)
    # the heavy barrel, four flutes along it, the big brake with two ports a side
    tube(g, 'barrel_wzB__dark', 0.033, -1.375, -0.37, y=BY, bev=0.004)
    for ang in (45, 135, 225, 315):
        g.xprism('trim_wzN__black', rot_rect(0, BY, 0.003, 0.01, ang, r0=0.0306), -1.27, -0.6, bev=0.0008)
    tube(g, 'barrel_wzB__dark', 0.037, -0.62, -0.37, y=BY, bev=0.004, r2=0.039)
    tube(g, 'barrel_wzB__dark', 0.038, -1.388, -1.352, y=BY, bev=0.003)
    brake(g, 'barrel_wzB__dark', 'trim_wzN__black', -1.48, -1.36, BY, 0.05, ports=2, hole=0.015)
    # the big scope: the fat objective bell (pale glass, a crimson band), the tube, the square turret block with three
    # turrets, the long eyepiece; two high rings down to the rail
    tube(g, 'scope_wzN__frame', 0.029, -0.33, 0.045, y=SY, bev=0.004)
    tube(g, 'scope_wzN__frame', 0.052, -0.468, -0.395, y=SY, bev=0.007, hole=(0.0435, 0.014))
    tube(g, 'scope_wzN__frame', 0.05, -0.4, -0.31, y=SY, bev=0.004, r2=0.029)
    tube(g, 'lens_wzN__glow', 0.0438, -0.455, -0.451, y=SY, bev=0)
    tube(g, 'scope_wzA__body', 0.0535, -0.442, -0.42, y=SY, bev=0.003)
    g.box('scope_wzN__frame', (-0.034, 0.034), (SY - 0.031, SY + 0.031), (-0.163, -0.093), bev=0.009)
    g.cyl('scope_wzN__frame', 0.021, (0, SY + 0.028, -0.128), (0, SY + 0.056, -0.128), sides=8, bev=0.004)
    g.cyl('scope_wzN__frame', 0.019, (0.031, SY, -0.128), (0.058, SY, -0.128), sides=8, bev=0.004)
    g.cyl('scope_wzN__frame', 0.016, (-0.031, SY, -0.128), (-0.052, SY, -0.128), sides=8, bev=0.004)
    tube(g, 'scope_wzN__frame', 0.029, 0.04, 0.092, y=SY, bev=0.003, r2=0.037)
    tube(g, 'scope_wzN__frame', 0.038, 0.186, 0.088, y=SY, bev=0.006, hole=(0.0305, 0.01))
    tube(g, 'lens_wzN__glow', 0.0306, 0.177, 0.173, y=SY, bev=0)
    for z0 in (-0.275, -0.025):
        g.ring('scope_wzN__dark', 0.0365, 0.0285, (0, SY, z0), (0, SY, z0 + 0.03), sides=8, bev=0.003)
        g.box('scope_wzN__dark', (-0.02, 0.02), (0.055, SY - 0.031), (z0, z0 + 0.03), bev=0.005)
    # the box magazine, the bottom metal, the trigger guard (node "guard") and trigger
    g.box('mag_wzB__dark', (-0.03, 0.03), (-0.16, -0.07), (-0.17, -0.066), bev=0.008)
    g.box('mag_wzB__dark', (-0.033, 0.033), (-0.17, -0.15), (-0.176, -0.06), bev=0.005)
    g.box('guard_wzB__frame', (-0.024, 0.024), (-0.107, -0.092), (-0.19, 0.1), bev=0.004)
    guard(g, 'guard_wzB__frame', -0.01, 0.1, -0.142, t=0.018, hw=0.014)
    g.box('guard_wzB__frame', (-0.0135, 0.0135), (-0.138, -0.1), (-0.01, 0.008), bev=0.004)
    trigger(g, 'guard_wzB__frame', 0.042, -0.104, -0.12)
    return g


BUILD = {'smg': smg, 'burst': burst, 'lmg': lmg, 'dmr': dmr, 'sniper': sniper}
