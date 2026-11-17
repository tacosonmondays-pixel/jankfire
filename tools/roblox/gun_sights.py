# THE SLIM SIGHTS (owner, 16 Nov 2026: "my issue is just the iron sights or the scopes look bulky and not like the ones
# in rivals"). One kit every gun and skin draws its sights from. Sized from the vault note Research/Rivals sights.md
# (Rivals is the teacher for method and size only; nothing of its own is copied):
#   - sights are not tiny: they read slim because they are THIN (a ring is a washer, its wall about a tenth of its
#     width), OPEN (three quarters of a ring is hole) and UNDER the aim line (bases, ears and blocks stay below it;
#     above it only thin ring walls and post tips);
#   - one sight type per gun: a ring rifle (rifle_rear + rifle_front), a notch gun (notch + blade), an optic gun
#     (red_dot / holo), a scope gun (scope_slim), a bead shotgun (bead), or none;
#   - eight-sided rings with a corner on top and a chamfer round the hole (a pale line catches the light there),
#     square ears with one chamfer on top, pointed post tips; never a tube, never a box round a ring;
#   - the gun's near-black, never its colour block (a skin may make them gold, never put ornament round the hole).
# The gun bodies stay chunky: only the sights got slim.
#
# THE RULES OF THE KIT
#   - every builder is placed from the gun's sight spot (g.spots['sight']): the aim line runs through a ring's centre,
#     along a notch's floor, through a reflex sight's dot / a holo's reticle, and a front post's tip (or a bead's
#     centre) sits on it. Nothing here moves the spot: the game's rows (Weapons.luau mdl.sight) stay as they are.
#   - no wall thinner than 3.5 mm (rings 4 mm): the guns are drawn at ~2.6 (first person) to ~5 (racks) studs a
#     metre, and thinner things shimmer or drop out in Roblox.
#   - every part stands on the top it is given (`base`: the height of the surface under it) and sinks SINK into it,
#     so tools/roblox/gun_check.py finds nothing loose.
#   - no two faces of different colours lie flat on each other: where a ring, a pane or a dot meets another part they
#     cross or one is buried in the other (no z-fighting, nothing for gun_zfix to push about).
#   - glass panes go on a glass slot (kind 'g' + an alpha: g.slot('glass', '9fb4c4', 'g', 0.3)), dots and reticles
#     on a Neon slot (kind 'n'); sights sit on _wzN zones (a wrap leaves them alone).
#   - the caller names the pieces, so a sight that rides on a moving node (a pistol's slide, a bolt) keeps that node.
# Frame and units as gunkit: metres, x right, y up, z back (the muzzle at -z). Builders that use it: gun_models.py,
# gun_models_c*.py, gun_set.py and the skin files; new skins: `import gun_sights as SG`.
import math
import bpy, bmesh
import gunkit
from gunkit import P

WALL = 0.0035   # the thinnest blade or ear
RING = 0.004    # a ring's or a hood's wall, seen face-on
SINK = 0.001    # how far a part sinks into what it stands on
CHAMFER = 0.0012  # the chamfer round a ring's hole


# --------------------------------------------------------------------------------------------- shapes
def _fold(g, piece, bm):
    """fold a finished solid (its faces and edges already carry their smooth flags) into a piece"""
    bm.normal_update()
    me = bpy.data.meshes.new('tmp')
    bm.to_mesh(me); bm.free()
    g._bm(piece).from_mesh(me)
    bpy.data.meshes.remove(me)


def _area(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts))) / 2


def _flags(bm, round_deg=40.0):
    """shade a solid: faces meeting at less than round_deg shade smooth into each other, every other edge is crisp"""
    bm.normal_update()
    lim = math.radians(round_deg)
    for f in bm.faces: f.smooth = False
    for e in bm.edges:
        fs = e.link_faces
        e.smooth = len(fs) == 2 and fs[0].normal.angle(fs[1].normal, 0.0) < lim
        if e.smooth:
            fs[0].smooth = fs[1].smooth = True


def _bevel(bm, bev):
    if bev <= 0: return
    geom = [e for e in bm.edges if len(e.link_faces) == 2 and
            e.link_faces[0].normal.angle(e.link_faces[1].normal, 0.0) > math.radians(50)]
    if geom:
        bmesh.ops.bevel(bm, geom=geom, offset=bev, offset_type='OFFSET', segments=1, profile=0.5, affect='EDGES',
                        clamp_overlap=True)


def xsolid(g, piece, outline, z0, z1, bev=0.0006):
    """an outline seen from the FRONT [(x, y)] (any simple shape, concave is fine) pushed along the barrel from z0 to
       z1, its edges chamfered by bev"""
    pts = list(outline)
    if _area(pts) < 0: pts = pts[::-1]
    bm = bmesh.new()
    A = [bm.verts.new(P(x, y, z0)) for x, y in pts]
    B = [bm.verts.new(P(x, y, z1)) for x, y in pts]
    n = len(pts)
    bm.faces.new(A); bm.faces.new(B[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([A[i], B[i], B[j], A[j]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    _bevel(bm, bev)
    _flags(bm)
    _fold(g, piece, bm)


def xframe(g, piece, outer, inner, z0, z1, bev=0.0006):
    """the band between two outlines seen from the FRONT [(x, y)] with the same number of points, in step (a frame
       round a window), pushed along the barrel from z0 to z1"""
    outer, inner = list(outer), list(inner)
    if _area(outer) < 0: outer, inner = outer[::-1], inner[::-1]
    bm = bmesh.new()
    n = len(outer)
    OA = [bm.verts.new(P(x, y, z0)) for x, y in outer]
    OB = [bm.verts.new(P(x, y, z1)) for x, y in outer]
    IA = [bm.verts.new(P(x, y, z0)) for x, y in inner]
    IB = [bm.verts.new(P(x, y, z1)) for x, y in inner]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([OA[i], OB[i], OB[j], OA[j]])
        bm.faces.new([IA[i], IA[j], IB[j], IB[i]])
        bm.faces.new([OA[i], OA[j], IA[j], IA[i]])
        bm.faces.new([OB[i], IB[i], IB[j], OB[j]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    _bevel(bm, bev)
    _flags(bm)
    _fold(g, piece, bm)


def trap(x_bot, x_top, y0, y1, cx=0.0):
    """a trapezoid seen from the front: x_bot wide at y0, x_top wide at y1 (half widths) [(x, y)]"""
    return [(cx - x_bot, y0), (cx + x_bot, y0), (cx + x_top, y1), (cx - x_top, y1)]


def poly(cx, cy, r, sides=8, turn=0.0):
    """a regular polygon seen from the front [(x, y)], a corner on top (turn 0), counter-clockwise"""
    return [(cx + r * math.cos(math.pi / 2 + turn + 2 * math.pi * k / sides), cy + r * math.sin(math.pi / 2 + turn + 2 * math.pi * k / sides))
            for k in range(sides)]


def ring8(g, piece, ro, ri, c, depth, sides=8, bev=CHAMFER):
    """a thin washer across the barrel (its axis along z) centred on c (x, y, z): eight-sided with a corner on top,
       crisp facets in every look, its front and back edges chamfered (the chamfer round the hole catches the light)"""
    x, y, z = c
    xframe(g, piece, poly(x, y, ro, sides), poly(x, y, ri, sides), z - depth / 2, z + depth / 2, bev=bev)


# --------------------------------------------------------------------------------------------- iron sights
def rifle_rear(g, piece, z, sy, base, w=0.036, wall=RING, depth=0.009, ears=True, stem_w=None, stem_z=None, ear_z=None,
               ear_base=None, sides=8, stem_piece=None):
    """a ring rifle's rear sight: a thin eight-sided washer (outside width w, wall `wall`, `depth` along the barrel,
       z = its middle) round the aim line (sy), on a narrow stem (stem_w wide, about 0.45 of the ring) down to the top
       at `base`. stem_z = (z0, z1): run the stem further along the barrel (to reach the receiver when the ring stands
       behind it). ears: two small square ears either side, their tops level with the ring's bottom, standing straight
       on the top (at ear_z / ear_base when the top under the ring is not there). stem_piece: the stem in another
       colour (the body's, so a tall stem does not read as a dark stripe). Nothing lies flat on the top it stands on (a
       thin plate there would z-fight with it)"""
    ro, ri = w / 2, w / 2 - wall
    ring8(g, piece, ro, ri, (0, sy, z), depth, sides=sides)
    sw = stem_w or 0.45 * w
    za, zb = stem_z or (z - depth / 2 - 0.002, z + depth / 2 + 0.002)
    top = sy - ri - wall * 0.45  # (the stem ends inside the ring's wall, clear of its hole)
    if base < top:  # (a tall stem narrows toward the ring: a post, not a block under it)
        xsolid(g, stem_piece or piece, trap(sw / 2, sw / 2 * (0.86 if top - base < 0.35 * w else 0.6), base - SINK, top), za, zb,
               bev=0.0008)
    ex, ew = 0.55 * w, 0.17 * w
    eb = base if ear_base is None else ear_base
    ez = z if ear_z is None else ear_z
    if ears:
        ytop = sy - ro
        if ytop > eb + 0.003:
            for sx in (-1, 1):
                x0, x1 = sorted((sx * (ex - ew / 2), sx * (ex + ew / 2)))
                c = min(0.0018, (ytop - eb) * 0.3)
                if sx > 0:  # (the chamfer on the outer top corner)
                    pts = [(x0, eb - SINK), (x1, eb - SINK), (x1, ytop - c), (x1 - c, ytop), (x0, ytop)]
                else:
                    pts = [(x0, eb - SINK), (x1, eb - SINK), (x1, ytop), (x0 + c, ytop), (x0, ytop - c)]
                xsolid(g, piece, pts, ez - depth / 2, ez + depth / 2, bev=0.0006)


def rifle_front(g, piece, z, sy, base, w=0.032, wall=RING, depth=0.008, dot_piece=None, stem_w=None, sides=8):
    """a ring rifle's front sight: a thin eight-sided hood (outside width w, wall `wall`) with a narrow pointed post
       inside whose tip is the aim point (a third of the way up the hood's opening), on a narrow stem down to the top
       at `base` (the gas block / the receiver's front end). dot_piece: a small glowing bead on the tip instead"""
    ro, ri = w / 2, w / 2 - wall
    cy = sy + (2 * ri) / 6  # (the tip a third of the way up the opening)
    ring8(g, piece, ro, ri, (0, cy, z), depth, sides=sides)
    pb = 0.2 * w / 2  # the post's half width at its foot
    yb = cy - ri - wall * 0.5
    if dot_piece:
        xsolid(g, piece, trap(pb, pb * 0.55, yb, sy - 0.0012), z - depth * 0.3, z + depth * 0.3, bev=0.0005)
        g.ball(dot_piece, 0.0022, (0, sy, z), sub=1)
    else:
        xsolid(g, piece, [(-pb, yb), (pb, yb), (pb * 0.45, sy - 0.004), (0.0, sy), (-pb * 0.45, sy - 0.004)],
               z - depth * 0.3, z + depth * 0.3, bev=0.0004)
    sw = stem_w or 0.42 * w
    top = cy - ri - wall * 0.45
    if base < top:
        xsolid(g, piece, trap(sw / 2 * 1.25, sw / 2, base - SINK, top), z - depth / 2 - 0.001, z + depth / 2 + 0.001, bev=0.0008)


def notch(g, piece, z, sy, base, w, depth=0.007, nw=0.3, nd=0.0065, c=0.002, x=0.0, neck=None):
    """a low notch block (pistols, SMGs, shotguns, revolvers): `w` wide across the gun, `depth` along the barrel
       (z = its middle), standing on the top at `base`; its top edge (the two square ears' tops, one chamfer c on
       their outer corners) on the aim line (sy), a square U notch nw of its width wide and nd deep between them: the
       front post's tip shows in the notch, flush with the ears (Rivals: the aim point sits on the rear sight's top
       edge; nothing solid above the line). neck = a half width: where the aim line stands well above the top, the
       block below the notch narrows to a stem that wide (a leaf on a stem, not a tall block)"""
    top = sy
    fl = sy - nd  # the notch's floor
    hw, hn = w / 2, nw * w / 2
    yb = min(base, fl - 0.002) - SINK
    c = min(c, nd * 0.45)
    head = [(x + hw, top - c), (x + hw - c, top), (x + hn, top), (x + hn, fl), (x - hn, fl), (x - hn, top), (x - hw + c, top),
            (x - hw, top - c)]
    ys = fl - 0.003
    if neck and ys - 0.004 > yb + 0.003:
        out = [(x - neck, yb), (x + neck, yb), (x + neck, ys - 0.004), (x + hw, ys)] + head + [(x - hw, ys), (x - neck, ys - 0.004)]
    else:
        out = [(x - hw, yb), (x + hw, yb)] + head
    xsolid(g, piece, out, z - depth / 2, z + depth / 2, bev=0.0007)


def blade(g, piece, z, sy, base, w=0.005, depth=0.008, glow_piece=None):
    """a front blade (pistols, shotguns, revolvers): narrow, its pointed tip on the aim line, standing on the top at
       `base`. glow_piece: a small glowing insert on its back face just under the tip (the dot you line up)"""
    yb = base - SINK
    tip = 0.0035 if sy - yb > 0.006 else (sy - yb) * 0.5
    xsolid(g, piece, [(-w / 2, yb), (w / 2, yb), (w / 2 * 0.8, sy - tip), (0.0, sy), (-w / 2 * 0.8, sy - tip)],
           z - depth / 2, z + depth / 2, bev=0.0004)
    if glow_piece and sy - tip - 0.0045 > yb:
        gy = sy - tip - 0.0025
        xsolid(g, glow_piece, trap(w / 2 * 0.62, w / 2 * 0.62, gy - 0.0018, gy + 0.0018), z + depth / 2 - 0.0015,
               z + depth / 2 + 0.0015, bev=0)


def bead(g, piece, z, sy, base, r=0.003, stem_piece=None, stem_w=0.0056, stem_d=0.006):
    """a shotgun's bead: a small faceted ball centred on the aim line on a short narrow stem (stem_w across, stem_d
       along the barrel) down to the top at `base`"""
    if sy - r * 0.4 > base:
        xsolid(g, stem_piece or piece, trap(stem_w / 2, stem_w * 0.38, base - SINK, sy - r * 0.4), z - stem_d / 2,
               z + stem_d / 2, bev=0.0004)
    g.ball(piece, r, (0, sy, z), sub=1)


# --------------------------------------------------------------------------------------------- optics
def _hood(g, frame_piece, glass_piece, z, sy, base, bw, tw, win_w, win_h, depth, x):
    """a tapered hood standing straight on the top at `base` (no riser): bw / tw = its half widths at the foot and
       the top, a window win_w x win_h (half sizes) centred on the aim line, its sides following the taper, a faintly
       tinted pane in it. returns the pane's back face z"""
    top = sy + win_h + max(0.0045, 0.2 * tw)
    yb = base - SINK
    def half(y): return bw + (tw - bw) * (y - yb) / (top - yb)  # (the hood's half width at a height)
    k = (half(sy + win_h) - half(sy - win_h)) / 2
    O = [(x - bw, yb), (x + bw, yb), (x + tw, top), (x - tw, top)]
    I = [(x - win_w - k, sy - win_h), (x + win_w + k, sy - win_h), (x + win_w - k, sy + win_h), (x - win_w + k, sy + win_h)]
    # the band between the outside and the window: a foot-to-top hood, solid under the window
    xframe(g, frame_piece, O, I, z - depth / 2, z + depth / 2, bev=0.0008)
    e = 0.0007  # (the pane's rim buried in the frame)
    pane = [(x - win_w - k - e, sy - win_h - e), (x + win_w + k + e, sy - win_h - e), (x + win_w - k + e, sy + win_h + e),
            (x - win_w + k - e, sy + win_h + e)]
    xsolid(g, glass_piece, pane, z - 0.0015, z + 0.0015, bev=0)
    return z + 0.0015


def red_dot(g, frame_piece, glass_piece, dot_piece, z, sy, base, bw=0.017, tw=0.0105, win_w=0.0075, win_h=0.0068,
            depth=0.02, dot=0.0035, x=0.0):
    """a small reflex sight: a dark tapered hood standing straight on the top (`base`), wider at its foot (bw) than its
       top (tw) (half widths), a window (win_w x win_h, half sizes) centred on the aim line with a faintly tinted pane,
       one small glowing dot on the aim line, `depth` along the barrel (z = its middle)"""
    zb = _hood(g, frame_piece, glass_piece, z, sy, base, bw, tw, win_w, win_h, depth, x)
    g.ball(dot_piece, dot / 2, (x, sy, zb + dot * 0.1), sub=1)


def holo(g, frame_piece, glass_piece, ret_piece, z, sy, base, bw=0.021, tw=0.015, win_w=0.0115, win_h=0.0085,
         depth=0.024, ring=0.0062, x=0.0):
    """a holographic sight: the reflex sight's hood, wider, with a glowing ring (3 mm wide, outer radius `ring`) and
       a dot in the window, both centred on the aim line"""
    zb = _hood(g, frame_piece, glass_piece, z, sy, base, bw, tw, win_w, win_h, depth, x)
    g.ring(ret_piece, ring, ring - 0.003, (x, sy, zb - 0.001), (x, sy, zb + 0.002), sides=16, bev=0)
    g.ball(ret_piece, 0.0016, (x, sy, zb + 0.0002), sub=1)


# --------------------------------------------------------------------------------------------- scopes
def _arc_band(r0, r1, a0, a1, n=6):
    """a curved band between radii r0 < r1 from angle a0 to a1 (degrees) seen from the front [(x, y)] round (0, 0)"""
    out = [(r1 * math.cos(math.radians(a0 + (a1 - a0) * k / n)), r1 * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]
    out += [(r0 * math.cos(math.radians(a1 - (a1 - a0) * k / n)), r0 * math.sin(math.radians(a1 - (a1 - a0) * k / n))) for k in range(n + 1)]
    return out


def scope_slim(g, piece, z0, z1, sy, r=0.019, bell=None, eye=None, lens_piece=None, rim_piece=None, glint_piece=None,
               mounts=(), mount_piece=None, turret=True, turret_piece=None, band_piece=None, band_z=None, x=0.0,
               bell_len=0.05, eye_len=0.058, sides=8):
    """a slim scope on the aim line (its axis at (x, sy)) from the objective's front z0 to the eyepiece's back z1
       (z0 < z1): an eight-sided tube r, a bell at each end about 1.3 times it (bell, eye), a lens (lens_piece: a glass
       slot) sunk in each end inside a rim (rim_piece: a thin lip round each end; default the tube's own look),
       behind the front glass a small glowing crescent (glint_piece) that catches the eye from the front, one turret
       on top, a band (band_piece at band_z: a 12 mm section of the tube a little fatter, in another look). mounts:
       [(z, base)]: a thin ring round the tube at z on a narrow leg straight down into the top at base (mount_piece;
       default the tube's own look). A rim or a mount ring in another look than the tube would lie a few mm over it:
       gun_zfix would push it about, so keep those in the tube's look"""
    bell = bell or round(r * 1.3, 4)
    eye = eye or round(r * 1.25, 4)
    rp = rim_piece or piece  # (the tube's own look unless a skin wants a trim there)
    hb, he = bell * 0.74, eye * 0.74  # (the recesses: the rim is about 0.15 of the bell's width)
    # the objective: the rim (a 6 mm section of the bell, its lip over the recess) at the very front, the bell behind
    # it with its recess, the taper down to the tube
    zb0 = z0 + 0.006
    g.cyl(piece, bell, (x, sy, zb0), (x, sy, z0 + bell_len), sides=sides, bev=0.0012, hole=(hb, 0.02))
    g.ring(rp, bell, hb - 0.0012, (x, sy, z0), (x, sy, zb0), sides=sides, bev=0.0008)
    tz = z0 + bell_len + 0.03
    g.cyl(piece, bell, (x, sy, z0 + bell_len - 0.001), (x, sy, tz), sides=sides, bev=0.0008, r2=r)
    # the eyepiece: the rim at the back, the eyepiece with its recess, the taper
    ze1 = z1 - 0.006
    g.cyl(piece, eye, (x, sy, ze1), (x, sy, z1 - eye_len), sides=sides, bev=0.0012, hole=(he, 0.018))
    g.ring(rp, eye, he - 0.0012, (x, sy, ze1), (x, sy, z1), sides=sides, bev=0.0008)
    te = z1 - eye_len - 0.026
    g.cyl(piece, eye, (x, sy, z1 - eye_len + 0.001), (x, sy, te), sides=sides, bev=0.0008, r2=r)
    # the tube between (cut round the band, so the band is a section of it, not a sleeve over it)
    bz = None
    if band_piece:
        bz = band_z if band_z is not None else (tz + (tz + te) / 2) / 2
        g.cyl(piece, r, (x, sy, tz - 0.002), (x, sy, bz - 0.006), sides=sides, bev=0.0006)
        g.cyl(band_piece, r + 0.0018, (x, sy, bz - 0.006), (x, sy, bz + 0.006), sides=sides, bev=0.0008)
        g.cyl(piece, r, (x, sy, bz + 0.006), (x, sy, te + 0.002), sides=sides, bev=0.0006)
    else:
        g.cyl(piece, r, (x, sy, tz - 0.002), (x, sy, te + 0.002), sides=sides, bev=0.0006)
    if lens_piece:  # (each sunk 6 mm, its rim buried in the recess's wall; you see the dark recess floor through it)
        g.cyl(lens_piece, hb + 0.0006, (x, sy, zb0 + 0.0055), (x, sy, zb0 + 0.0085), sides=sides, bev=0)
        g.cyl(lens_piece, he + 0.0006, (x, sy, ze1 - 0.0055), (x, sy, ze1 - 0.0085), sides=sides, bev=0)
    if glint_piece:  # behind the front glass, standing on the recess's floor (upper left as you face the scope)
        band = [(x + px, sy + py) for px, py in _arc_band(hb * 0.42, hb * 0.42 + 0.0042, 105, 165)]
        xsolid(g, glint_piece, band, zb0 + 0.0135, zb0 + 0.0205, bev=0)
    zt = (tz + te) / 2
    if turret:
        tp = turret_piece or piece
        g.cyl(tp, 0.0095, (x, sy + r * 0.8, zt), (x, sy + r + 0.0115, zt), sides=8, bev=0.0012)
    mp = mount_piece or piece
    for zm, yb in mounts:
        g.ring(mp, r + RING, r - 0.0012, (x, sy, zm - 0.006), (x, sy, zm + 0.006), sides=sides, bev=0.0008)
        if yb < sy - r:
            xsolid(g, mp, trap(max(0.013, r * 0.6), max(0.0085, r * 0.42), yb - 0.002, sy - r + 0.0012, cx=x), zm - 0.01,
                   zm + 0.01, bev=0.0008)
    return zt


# --------------------------------------------------------------------------------------------- other names
# (the names the brief used: the same builders)
rear_aperture = rifle_rear   # a thin ring on a narrow stem
front_post = rifle_front     # a thin hood with a pointed post (rifles); blade() for pistols, shotguns, revolvers
rear_notch = notch           # a low notch block / a notch leaf on a stem
