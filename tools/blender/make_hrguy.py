# THE TALL GUY FROM HR (Scary Forest, public/js/hrguy.js): 3.6 m of cheap grey suit and no face, in Blender.
# A too-thin man in a single-breasted two-button suit (notch lapels with a soft roll, squared shoulders, flap pockets, a
# breast pocket with a red square, a back vent), a red four-in-hand tie with a dimple and a tie bar, a belt, a blue
# lanyard from round his collar down to the ☺ CORP badge (the game paints its own canvas on the card: `hr_badge`), a
# hardboard clipboard with a steel clip and a form about you, pressed trousers with a break and turn-ups, shiny cap-toe
# oxfords, long pale fingers, a smooth egg for a head with a faint brow ridge and nothing else, and a bluetooth
# earpiece whose LED the game blinks (`hr_led`).
# Built on the code model's rig (buildHR()): one empty per joint at the same spot, the same parents, nothing rotated,
# so the game's pose() (a new, worse pose every blink) turns the same nodes it always did:
#   hr_body (0, 0, 0) > hr_legL / hr_legR (+-0.11, 1.86, 0), hr_head (0, 3.08, 0) > hr_led,
#   hr_armL / hr_armR (+-0.33, 2.9, 0) > hr_foreL / hr_foreR (0, -0.78, 0) > (right only) hr_clip (0, -0.92, -0.05)
# each joint's look is one mesh hr_<joint>_m under it. the mannequin jank: his left shoulder sits higher, his left
# knee bends back the wrong way, one finger on his left hand doesn't curl like the others.
# blender52 -b --python tools/blender/make_hrguy.py [-- --no-sheet] [--no-export] [--qa] [--poses] [--night] [--quick]
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cast'))
from castlib import *  # noqa (blob, limb, lerp3 + everything in lib.py)
from sidekit import rrect, text_c, smiley

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
FILE = 'x_hrguy'
# the code rig's joints (world rest spots, game axes) and parents
J = {'body': (0, 0, 0), 'legL': (-0.11, 1.86, 0), 'legR': (0.11, 1.86, 0), 'head': (0, 3.08, 0),
     'armL': (-0.33, 2.9, 0), 'armR': (0.33, 2.9, 0), 'foreL': (-0.33, 2.12, 0), 'foreR': (0.33, 2.12, 0), 'clip': (0.33, 1.2, -0.05)}
PARENT = {'body': None, 'legL': 'body', 'legR': 'body', 'head': 'body', 'armL': 'body', 'armR': 'body', 'foreL': 'armL', 'foreR': 'armR', 'clip': 'foreR'}
CLIP_TILT = -0.15  # the code clipboard's tilt (rotation.x), baked into the mesh: the node itself isn't turned


# ------------------------------------------------------------ materials
class Mats:
    def __init__(self):
        S = 0x5a606e
        self.suit = cloth('hr_suit', S, tex_noise('hr_suitT', S, 0.035, 32, speck=0x646a78, speck_p=0.025, seed=31))
        b = self.suit.node_tree.nodes['Principled BSDF']; b.inputs['Roughness'].default_value = 0.5; b.inputs['Coat Weight'].default_value = 0.12  # the cheap sheen
        self.shirt = mat('hr_shirt', 0xe8e8ea, rough=0.62, emit=0x1a1a1c, strength=1.0, tex=tex_noise('hr_shirtT', 0xe8e8ea, 0.025, 16, seed=32))
        self.skin = mat('hr_skin', 0xe6e0d6, rough=0.34, clearcoat=0.25, emit=0x56524c, strength=1.0)  # pale, lit from nowhere
        self.tie = mat('hr_tie', 0xb81a26, rough=0.3, clearcoat=0.35, tex=tex_stripes('hr_tieT', 0xb81a26, 0x9a121c, 16, 2))
        self.strap = mat('hr_strap', 0x2a6cff, rough=0.55, emit=0x081840, strength=1.0)
        self.black = mat('hr_black', 0x0c0c0e, rough=0.14, clearcoat=1.0)  # shoes, buttons, the belt, the earpiece, the badge holder
        self.chrome = mat('hr_chrome', 0xc8ccd4, rough=0.2, metal=1.0)
        self.led = mat('hr_led', 0x19a8ff, emit=0x19a8ff, strength=4.0)
        self.board = mat('hr_board', 0x6a4a2a, rough=0.5, clearcoat=0.3, tex=tex_noise('hr_boardT', 0x6a4a2a, 0.1, 32, speck=0x4a3018, speck_p=0.12, seed=33))
        self.paper = mat('hr_paper', 0xf4f2ec, rough=0.7, emit=0x1a1a1a, strength=1.0, tex=tex_canvas('hr_paperT', 64, 88, paper_px))
        self.badge = mat('hr_badge', 0xffffff, rough=0.4, tex=tex_canvas('hr_badgeT', 64, 88, badge_px))
        for m in (self.skin, self.black, self.chrome, self.led, self.board): m.use_backface_culling = True


def badge_px(px):
    """the code badge (hrguy.js badgeTex): ☺ CORP, the egg photo, HR, hi! i'm from HR. only for the sheets: the game puts
    its own canvas on hr_badge. painted upside down because the card's V runs top to bottom (the README's gotcha)"""
    px[:] = hexrgb(0xf4f2ec)
    px[0:16] = hexrgb(0x2a6cff)
    text_c(px, 'CORP', 38, 5, 1, 0xffffff)
    smiley(px, 14, 8.5, 5, face=0xffffff, ink=0x2a6cff)
    px[22:54, 14:50] = hexrgb(0xcfcac0)
    px_disc(px, 32, 39, 9.5, 0xece8e0)
    px[50:54, 18:46] = hexrgb(0x4a5060)
    text_c(px, 'HR', 32, 59, 2, 0x120818)
    text_c(px, 'HI! IM HR', 32, 77, 1, 0x120818)
    px[:] = px[::-1].copy()


def paper_px(px):
    """the form on his clipboard. it's about you"""
    px[:] = hexrgb(0xf4f2ec)
    px[13:23, 2:62] = hexrgb(0x2a6cff)  # (below the clip's jaw)
    text_c(px, 'RE: YOU', 32, 15, 1, 0xffffff)
    for i in range(6):  # the questions, a box each
        y = 27 + i * 8
        px[y:y + 4, 4:8] = hexrgb(0x55506a); px[y + 1:y + 3, 5:7] = hexrgb(0xf4f2ec)
        px[y + 1:y + 3, 11:58 - (i * 7) % 19] = hexrgb(0x8a86a0)
    for k in range(3): px[44 + k, 4 + k] = hexrgb(0xff3030); px[46 - k * 2, 6 + k] = hexrgb(0xff3030)  # one ticked. in red
    px_disc(px, 46, 45, 9, 0xff3030, r_in=7.6)  # and circled
    px[82:83, 28:60] = hexrgb(0x120818)
    text_px(px, 'SIGN', 2, 77, 1, 0xff3030)


# ------------------------------------------------------------ mesh helpers (game coordinates)
def mk(name, verts, faces, m, smooth_ang=40):
    bm = bmesh.new()
    vs = [bm.verts.new(gv(*p)) for p in verts]
    for f in faces:
        try: bm.faces.new([vs[i] for i in f])
        except ValueError: pass
    o = lib_obj(name, bm, m)
    for p in o.data.polygons: p.use_smooth = True
    if smooth_ang: o.data.set_sharp_from_angle(angle=math.radians(smooth_ang))
    return o


def grid(name, rows, m, ring=True, caps=(False, False), smooth_ang=48, out=None):
    """a surface through rows of game points (every row the same length). ring: each row closes on itself. caps: fan
    the first / last row to its middle. out(p) -> the way the surface should face at p (the winding is fixed to match)"""
    n = len(rows[0]); V = [p for r in rows for p in r]; F = []
    for i in range(len(rows) - 1):
        for j in range(n if ring else n - 1):
            k = (j + 1) % n
            F.append((i * n + j, i * n + k, (i + 1) * n + k, (i + 1) * n + j))
    for e, (c, r) in enumerate(zip(caps, (rows[0], rows[-1]))):
        if not c: continue
        ci = len(V); V.append(tuple(sum(p[t] for p in r) / n for t in range(3)) if c is True else c)
        base = 0 if e == 0 else (len(rows) - 1) * n
        for j in range(n if ring else n - 1): F.append((base + j, ci, base + (j + 1) % n) if e == 0 else (base + (j + 1) % n, ci, base + j))
    o = mk(name, V, F, m, smooth_ang)
    face_out(o, out)
    return o


def face_out(o, out=None):
    """make the winding consistent; out(p) (game axes) says which way it should face, else outward from the middle"""
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if out is not None:
        votes = 0.0
        for f in bm.faces:
            c = f.calc_center_median(); g = (c.x, c.z, -c.y); d = out(g)
            votes += f.calc_area() * (f.normal.x * d[0] + f.normal.y * -d[2] + f.normal.z * d[1])
        if votes < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(o.data); bm.free()
    return o


def rim(o, t, offset=-1.0):
    """give an open shell's edges a thickness (the shell itself stays one face thick: hems, lapels, flaps)"""
    md = o.modifiers.new('rim', 'SOLIDIFY'); md.thickness = t; md.offset = offset; md.use_rim = True; md.use_rim_only = True
    apply_mods(o)
    o.data.set_sharp_from_angle(angle=math.radians(48))
    return o


def slab(name, outline, z0, z1, m, bev=0.0):
    """an outline [(x, y)] in a front-facing plane, extruded from z0 to z1 (game z). caps triangulated"""
    bm = bmesh.new()
    a = [bm.verts.new(gv(x, y, z0)) for x, y in outline]; b = [bm.verts.new(gv(x, y, z1)) for x, y in outline]
    f0 = bm.faces.new(a); f1 = bm.faces.new(b[::-1])
    n = len(outline)
    for j in range(n): bm.faces.new((a[j], a[(j + 1) % n], b[(j + 1) % n], b[j]))
    bmesh.ops.triangulate(bm, faces=[f0, f1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib_obj(name, bm, m)
    for p in o.data.polygons: p.use_smooth = True
    o.data.set_sharp_from_angle(angle=math.radians(40))
    if bev: bevel(o, bev, 1, 40); apply_mods(o)
    return o


def plate_y(name, outline, y0, y1, m):
    """a top-view outline [(x, z)] extruded from y0 up to y1 (soles, heels). caps triangulated"""
    bm = bmesh.new()
    lo = [bm.verts.new(gv(x, y0, z)) for x, z in outline]; hi = [bm.verts.new(gv(x, y1, z)) for x, z in outline]
    n = len(outline)
    f0 = bm.faces.new(lo[::-1]); f1 = bm.faces.new(hi)
    for j in range(n): bm.faces.new((lo[j], lo[(j + 1) % n], hi[(j + 1) % n], hi[j]))
    bmesh.ops.triangulate(bm, faces=[f0, f1]); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib_obj(name, bm, m); o.data.set_sharp_from_angle(angle=math.radians(40))
    for p in o.data.polygons: p.use_smooth = True
    return o


def bake(o):
    """modifiers and the object's own transform into its mesh (so joins and ray casts see it where it is)"""
    apply_mods(o)
    o.data.transform(o.matrix_basis.copy()); o.matrix_basis = Matrix.Identity(4)
    return o


def to_world(o, M):
    """bake a game-space 4x4 (mathutils Matrix in game axes) into a mesh"""
    C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    bake(o)
    o.data.transform(C @ M @ C.inverted())
    if M.to_3x3().determinant() < 0: face_out(o)  # (a mirror turns every face inside out)
    return o


def rot_game(rx=0.0, ry=0.0, rz=0.0, at=(0, 0, 0)):
    """three's Euler XYZ (R = Rx Ry Rz) about a game point, as a game-space matrix"""
    R = Matrix.Rotation(rx, 4, 'X') @ Matrix.Rotation(ry, 4, 'Y') @ Matrix.Rotation(rz, 4, 'Z')
    T = Matrix.Translation(Vector(at))
    return T @ R @ T.inverted()


def interp(table, y):
    """Catmull-Rom through a table of (y, values...) rows sorted by y"""
    ys = [r[0] for r in table]
    if y <= ys[0]: return table[0][1:]
    if y >= ys[-1]: return table[-1][1:]
    i = max(k for k in range(len(ys) - 1) if ys[k] <= y)
    t = (y - ys[i]) / (ys[i + 1] - ys[i])
    p0, p1, p2, p3 = table[max(0, i - 1)], table[i], table[i + 1], table[min(len(table) - 1, i + 2)]
    out = []
    for k in range(1, len(p1)):
        a, b, c, d = p0[k], p1[k], p2[k], p3[k]
        out.append(0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3))
    return out


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------ the torso's shape
# (y, half width, front depth, back depth, superellipse power): a narrow man in a suit, waist suppressed, the shoulders
# padded out square past the armholes and sloping in to a thin neck. the jacket is this surface; the shirt sits inside
JK = [(1.80, 0.218, 0.122, 0.140, 2.3), (1.95, 0.214, 0.116, 0.131, 2.3), (2.10, 0.199, 0.110, 0.117, 2.3),
      (2.24, 0.189, 0.108, 0.107, 2.4), (2.40, 0.201, 0.116, 0.108, 2.5), (2.56, 0.226, 0.128, 0.112, 2.6),
      (2.70, 0.252, 0.132, 0.116, 2.7), (2.80, 0.272, 0.126, 0.116, 2.8), (2.87, 0.292, 0.114, 0.11, 3.0),
      (2.915, 0.303, 0.1, 0.1, 3.0), (2.945, 0.296, 0.088, 0.092, 2.8), (2.966, 0.232, 0.079, 0.085, 2.4),
      (2.984, 0.15, 0.071, 0.078, 2.2), (3.000, 0.088, 0.066, 0.074, 2.1)]
Y_TB, Y_BB, Y_HEM, Y_GORGE = 2.33, 2.18, 1.80, 2.97  # top button, bottom button, hem, where the V meets the collar


def sup_pt(th, a, bf, bb, p):
    """theta 0 = the front middle (-z), + toward +x (his right)"""
    s, c = math.sin(th), math.cos(th)
    x = a * math.copysign(abs(s) ** (2 / p), s)
    zz = abs(c) ** (2 / p)
    return x, (-bf * zz if c >= 0 else bb * zz)


def zfront(x, y, inset=0.0):
    a, bf, bb, p = interp(JK, y)
    a -= inset; bf -= inset
    u = min(1.0, abs(x) / a)
    return -bf * (1 - u ** p) ** (1 / p)


def zback(x, y):
    a, bf, bb, p = interp(JK, y)
    return bb * (1 - min(1.0, abs(x) / a) ** p) ** (1 / p)


def push_left(x, y):
    """his left front lies over his right where it buttons: that edge stands 8 mm proud"""
    return 0.008 * smoothstep(-0.07, -0.015, x) * (1 - smoothstep(2.4, 2.52, y))


def lift_left(x, y):
    """jank: his left shoulder (pad and all) sits 18 mm higher than his right"""
    return 0.018 * smoothstep(-0.12, -0.24, x) * smoothstep(2.74, 2.9, y)


def shirt_in(y):  # how far the shirt front sits inside the jacket: 12 mm in the V, more where the jacket buttons over it
    return 0.012 + 0.012 * (1 - smoothstep(2.36, 2.56, y))


def edge_R(y):  # where his right front's edge is (x) at height y
    if y >= Y_TB: return 0.088 * min(1.0, (y - Y_TB) / (Y_GORGE - Y_TB)) + 0.002 * max(0.0, y - Y_GORGE) / 0.03
    if y >= Y_BB: return 0.0
    return 0.078 * ((Y_BB - y) / (Y_BB - Y_HEM)) ** 1.5


def edge_L(y):  # his left front's edge: past the middle where it buttons, then the V, the cutaway below
    if y >= Y_TB: return -edge_R(y) + 0.03 * (1 - smoothstep(Y_TB, Y_TB + 0.13, y))
    if y >= Y_BB: return 0.03
    return 0.03 - 0.108 * ((Y_BB - y) / (Y_BB - Y_HEM)) ** 1.5


def c_ring(y, M, t0=None, t1=None, inset=0.0, push=True):
    """the jacket at height y: from his right front edge round the back to his left front edge, M points evenly spaced
    (or any arc t0..t1 of it)"""
    a, bf, bb, p = interp(JK, y)
    a -= inset; bf -= inset; bb -= inset
    def th(x): return math.copysign(math.asin(min(0.9999, (abs(x) / a)) ** (p / 2)), x)
    if t0 is None: t0, t1 = th(edge_R(y)), th(edge_L(y)) + 2 * math.pi
    dense = [sup_pt(t0 + (t1 - t0) * k / 400, a, bf, bb, p) for k in range(401)]
    L = [0.0]
    for k in range(1, 401): L.append(L[-1] + math.hypot(dense[k][0] - dense[k - 1][0], dense[k][1] - dense[k - 1][1]))
    out = []
    for j in range(M):
        s = L[-1] * j / (M - 1); k = min(399, max(i for i in range(400) if L[i] <= s))
        f = (s - L[k]) / max(1e-9, L[k + 1] - L[k])
        x = dense[k][0] + (dense[k + 1][0] - dense[k][0]) * f; z = dense[k][1] + (dense[k + 1][1] - dense[k][1]) * f
        if push and j > M / 2 and z < 0: z -= push_left(x, y)
        out.append((x, y + lift_left(x, y), z))
    return out


# ------------------------------------------------------------ the body: jacket, shirt, tie, lanyard, badge
def jacket(M):
    ys = [1.80, 1.86, 1.95, 2.05, 2.12, 2.18, 2.26, 2.33, 2.42, 2.52, 2.62, 2.72, 2.80, 2.87, 2.915, 2.945, 2.966, 2.984, 3.0]
    rows = [c_ring(y, 22) for y in ys]
    sh = grid('jacket', rows, M.suit, ring=False, out=lambda g: (g[0], 0, g[2]))
    rim(sh, 0.006)
    out = [sh]
    # the collar: a tab over each lapel's top (the notch is the gap between them), the band round the back of his neck
    for sx in (-1, 1):
        cz = lambda x, y: zfront(sx * x, y) - 0.0072
        inner = [(0.080, 2.905), (0.0815, 2.928), (0.083, 2.95), (0.084, 2.988)]
        outer = [(0.12, 2.886), (0.132, 2.916), (0.125, 2.952), (0.106, 2.984)]
        rows_ = [[(sx * x, y, cz(x, y)) for x, y in inner], [(sx * x, y, cz(x, y)) for x, y in outer]]
        t = grid('collartab', rows_, M.suit, ring=False, out=lambda g: (0, 0.2, -1))
        rim(t, 0.005)
        out.append(t)
    bot, top = [], []
    for k in range(13):  # the band: stands up from the jacket's neckline, hugging the shirt collar
        a = math.pi * (-0.72 + 1.44 * k / 12)  # 0 = straight back, + toward his right
        th = math.pi - a
        back = max(0.0, math.cos(a))
        A, bf, bb, p = interp(JK, 2.99); x0, z0 = sup_pt(th, A, bf, bb, p)
        x1, z1 = sup_pt(th, 0.088, 0.07, 0.081, 2.1)
        bot.append((x0 * 1.03, 2.985, z0 * 1.03)); top.append((x1, 3.002 + 0.036 * back, z1))
    cb = grid('collarband', [bot, top], M.suit, ring=False, out=lambda g: (g[0], 0.2, g[2]))
    rim(cb, 0.006)
    out.append(cb)
    return out


def lapels(M):
    """notch lapels: from the top button up to the notch, rolled (they stand off his chest most at the fold)"""
    out = []
    for sx in (-1, 1):  # sx = his side (+1 right, -1 left)
        edge = edge_R if sx > 0 else (lambda y: -edge_L(y))  # (mirrored: how far the V edge is from the middle on that side)
        y0 = 2.335 if sx < 0 else 2.38
        zf = (lambda x, y: zfront(x, y) - push_left(x, y)) if sx < 0 else zfront
        def outer(v):  # the outer edge: tip -> peak, a little belly
            tipx, tipy = edge(y0) + 0.008, y0
            return ((1 - v) ** 2 * tipx + 2 * (1 - v) * v * 0.166 + v * v * 0.155, (1 - v) ** 2 * tipy + 2 * (1 - v) * v * 2.6 + v * v * 2.894)
        NV, NU = 9, 4
        rows = []
        for i in range(NV + 1):
            v = i / NV
            yi = y0 + (2.905 - y0) * v
            ix = edge(yi) - 0.004  # (overhangs the shell's edge: the fold)
            ox, oy = outer(v)
            row = []
            for j in range(NU):
                u = j / (NU - 1)
                x = ix + (ox - ix) * u; y = yi + (oy - yi) * u
                if i == NV:  # the top: the gorge seam out to the notch, then up to the lapel's peak
                    x, y = [(edge(2.905) - 0.004, 2.905), (0.12, 2.886), (0.138, 2.889), (0.155, 2.894)][j]
                lift = 0.005 + 0.0055 * (1 - u) ** 2
                row.append((sx * x, y, zf(sx * x, y) - lift))
            rows.append(row)
        L = grid('lapel', rows, M.suit, ring=False, out=lambda g: (0, 0.1, -1))
        rim(L, 0.005)
        out.append(L)
        roll = []  # the roll: a soft round edge along the fold
        for i in range(8):
            yi = y0 + 0.006 + (2.9 - y0 - 0.006) * i / 7
            x = edge(yi) - 0.002
            roll.append((sx * x, yi, zf(sx * x, yi) - 0.0085))
        out.append(limb('roll', roll, [0.0025] + [0.0068] * 6 + [0.004], M.suit, seg=5))
    return out


def inner_body(M):
    """the shirt front (and the trousers' waistband under it) inside the jacket: all the V and the cutaway ever show"""
    ys = [1.83, 1.92, 1.97, 2.03, 2.15, 2.32, 2.46, 2.6, 2.74, 2.86, 2.93, 2.97, 3.0]
    rows = []
    for y in ys:
        r = c_ring(y, 9, -1.05, 1.05, inset=0.012, push=False)
        rows.append([(x, y, z + shirt_in(y) - 0.012) for x, yy, z in r])
    o = grid('shirtfront', rows, M.shirt, ring=False, out=lambda g: (0, 0, -1))
    o.data.materials.append(M.suit)
    for f in o.data.polygons:
        if f.center.z < 1.97: f.material_index = 1  # (blender z = game y) below the belt: trousers
    out = [o]
    belt = [[(x, y, z - 0.0035) for x, yy, z in c_ring(y, 9, -1.0, 1.0, inset=0.012 + shirt_in(y) - 0.012, push=False)] for y in (1.97, 2.0, 2.03)]
    b = grid('belt', belt, M.black, ring=False, out=lambda g: (0, 0, -1))
    rim(b, 0.004)
    out.append(b)
    zb = zfront(0, 2.0) + shirt_in(2.0) - 0.0035
    out.append(slab('buckle', rrect(0.0, 2.0, 0.05, 0.036, 0.005, 1), zb - 0.006, zb + 0.001, M.chrome))
    return out


def neck_collar_tie(M):
    out = []
    out.append(limb('neck', [(0, 2.94, 0.004), (0, 3.02, 0.006), (0, 3.075, 0.006), (0, 3.098, 0.006)], [0.058, 0.057, 0.056, 0.03], M.skin, seg=10))
    band = []  # the shirt collar: a band round the neck, its points down over the knot
    for k in range(16):
        a = 2 * math.pi * k / 16; bx, bz = math.sin(a), math.cos(a)
        front = max(0.0, -bz)
        band.append([(bx * 0.068, 2.975 - front * 0.008, bz * 0.07 + 0.004), (bx * 0.065, 3.05 - front * 0.04, bz * 0.067 + 0.004)])
    cb = grid('shirtcollar', [[b[0] for b in band], [b[1] for b in band]], M.shirt, ring=True, out=lambda g: (g[0], 0, g[2]))
    rim(cb, 0.004)
    out.append(cb)
    for sx in (-1, 1):  # the collar points
        zz = lambda x, y: zfront(x, y) + shirt_in(y) - 0.0035
        pts = [(sx * 0.016, 3.006), (sx * 0.061, 2.987), (sx * 0.056, 2.912)]
        tri = mk('collarpt', [(x, y, zz(x, y)) for x, y in pts], [(0, 1, 2)], M.shirt)
        face_out(tri, lambda g: (0, 0, -1)); rim(tri, 0.004)
        out.append(tri)
    kn = []  # the knot: four-in-hand, a bit lopsided like they are
    for i, (y, w, d) in enumerate([(3.006, 0.026, 0.016), (2.99, 0.028, 0.021), (2.968, 0.024, 0.02), (2.948, 0.019, 0.016), (2.934, 0.015, 0.011)]):
        zc = zfront(0, y) + shirt_in(y) - 0.004
        ring = []
        for k in range(10):
            a = 2 * math.pi * k / 10
            x = math.sin(a) * w * (1.12 if math.sin(a) > 0 else 1.0); z = -math.cos(a) * d
            ring.append((x + 0.002, y + 0.004 * math.sin(a) * (i in (1, 2)), zc - d * 0.6 + z * (1 if z < 0 else 0.35)))
        kn.append(ring)
    out.append(grid('knot', kn, M.tie, ring=True, caps=(True, True)))
    # the blade: widens to the tip, pinched under the knot (the dimple), a chevron at the end (it peeks out under the
    # jacket's bottom button, above the belt)
    ys = [2.938, 2.918, 2.895, 2.86, 2.76, 2.62, 2.47, 2.33, 2.2, 2.12, 2.075]
    rows = []
    for i, y in enumerate(ys):
        w = interp([(2.075, 0.068), (2.3, 0.066), (2.6, 0.058), (2.8, 0.046), (2.9, 0.036), (2.938, 0.03)], y)[0]
        front, back = [], []
        for j in range(7):
            u = j / 6; x = (u - 0.5) * w
            zb = zfront(x, y) + shirt_in(y) - 0.0028
            bulge = 0.0035 * (1 - (2 * u - 1) ** 2)
            dimple = 0.0045 * math.exp(-((u - 0.5) / 0.12) ** 2) * max(0.0, (y - 2.85) / 0.088) if i < 4 else 0.0
            yy = y - (0.045 * (1 - abs(2 * u - 1)) if i == len(ys) - 1 else 0.0)
            front.append((x, yy, zb - 0.0045 - bulge + dimple))
            if 0 < j < 6: back.append((x, yy, zb))
        rows.append(front + back[::-1])
    out.append(grid('tie', rows, M.tie, ring=True, caps=(False, True)))
    zt = zfront(0, 2.62) + shirt_in(2.62) - 0.0028 - 0.0045 - 0.0035  # the tie bar, half into the tie's front
    out.append(box((0.064, 0.006, 0.003), (0.004, 2.62, zt), M.chrome))
    return out


def pockets_buttons(M):
    out = []
    for y in (Y_TB, Y_BB):  # two buttons, on his left front where it laps over
        z = zfront(0.0, y) - push_left(0.0, y)
        out.append(lathe([(0.0, 0.002), (0.0185, 0.002), (0.019, -0.0025), (0.017, -0.0055), (0.009, -0.0048), (0.0, -0.0045)], (0.0, y, z), M.black, seg=8, axis='z'))
    for sx in (-1, 1):  # the hip pockets' flaps
        cx, y0 = sx * 0.114, 2.045
        rows = []
        for i, dy in enumerate((0.0, -0.028, -0.052)):
            row = []
            for j in range(4):
                u = j / 3; x = cx + (u - 0.5) * 0.124
                if i == 2 and j in (0, 3): x -= (u - 0.5) * 0.012  # rounded bottom corners
                y = y0 + dy + (0.004 if i == 2 and j in (0, 3) else 0.0)
                row.append((x, y, zfront(x, y) - 0.0035 - 0.002 * i / 2))
            rows.append(row)
        f = grid('flap', rows, M.suit, ring=False, out=lambda g: (0, 0, -1)); rim(f, 0.004)
        out.append(f)
    rows = []  # the breast pocket (his left), a red silk square folded flat in it
    for i, dy in enumerate((0.0, 0.022)):
        row = []
        for j in range(3):
            u = j / 2; x = -0.178 + (u - 0.5) * 0.075; y = 2.635 + dy + (0.5 - u) * 0.012
            row.append((x, y + lift_left(x, y), zfront(x, y) - 0.003))
        rows.append(row)
    w = grid('welt', rows, M.suit, ring=False, out=lambda g: (0, 0, -1)); rim(w, 0.004)
    out.append(w)
    P = [Vector(q) for q in rows[1]]
    Q = [P[0] + (P[1] - P[0]) * 0.11, P[1], P[2] + (P[1] - P[2]) * 0.11]  # (on the welt's own faces, a little narrower)
    sq = [[tuple(q + Vector((0, dy, dz))) for q in Q] for dy, dz in ((-0.006, 0.0026), (0.013, -0.0004))]
    s = grid('square', sq, M.tie, ring=False, out=lambda g: (0, 0, -1)); rim(s, 0.003)
    out.append(s)
    # the back: a seam down the middle and the vent
    seam = [(0.0, y, zback(0, y) + 0.0005) for y in (2.04, 2.4, 2.7, 2.88, 2.96)]
    out.append(limb('seam', seam, [0.0022] * len(seam), M.suit, seg=4))
    rows = []
    for y in (1.802, 1.92, 2.04):
        rows.append([(x, y, zback(x, y) + 0.005) for x in (-0.045, -0.0225, 0.0)])
    v = grid('vent', rows, M.suit, ring=False, out=lambda g: (0, 0, 1)); rim(v, 0.005)
    out.append(v)
    return out


def lanyard_badge(M, body_objs, neck_objs):
    """two straps from round the back of his collar down his front to a clip and the badge (the game paints the card)"""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    def trees(objs):
        out = []
        for o in objs:
            bake(o); out.append(BVHTree.FromObject(o, dg))
        return out
    T_body, T_neck = trees(body_objs), trees(neck_objs)
    def cast(ts, p, d):  # first hit from game point p along game direction d -> game point
        best = None
        for t in ts:
            loc, _, _, dist = t.ray_cast(gv(*p), gv(*d), 2.0)
            if loc is not None and (best is None or dist < best[0]): best = (dist, (loc.x, loc.z, -loc.y))
        return best[1] if best else None
    W, OFF = 0.024, 0.003
    pts, dirs = [], []
    def strap(sx, up):
        for i in (range(9) if up else range(8, -1, -1)):
            t = i / 8; y = 2.49 + (2.975 - 2.49) * t; x = sx * (0.0125 + (0.052 - 0.0125) * t ** 1.15)
            z = min(cast(T_body, (x + e, y, -1.0), (0, 0, 1))[2] for e in (-W / 2, 0.0, W / 2))  # (flat across: the front-most of its middle and edges)
            pts.append(Vector((x, y, z - OFF))); dirs.append(Vector((0, 0, -1)))
    strap(1, True)
    for k in range(1, 9):  # round the back of his neck, over the collars
        a = math.pi * (0.62 - 1.24 * k / 9)  # 0 = straight back, + toward his right
        y = 3.0 + 0.016 * math.cos(a)
        d = Vector((math.sin(a), 0, math.cos(a)))
        h = cast(T_neck, tuple(Vector((0, y, 0.004)) + d * 0.4), tuple(-d)); pts.append(Vector(h) + d * OFF); dirs.append(d)
    strap(-1, False)
    for _ in range(60):  # taut: it bridges hollows instead of following them
        for i in range(1, len(pts) - 1):
            m = (pts[i - 1] + pts[i + 1]) / 2
            if (m - pts[i]).dot(dirs[i]) > 0: pts[i] = m
    rows_a, rows_b = [], []
    for i, p in enumerate(pts):
        tng = (pts[min(len(pts) - 1, i + 1)] - pts[max(0, i - 1)]).normalized()
        side = tng.cross(dirs[i]).normalized()
        rows_a.append(tuple(p + side * W / 2)); rows_b.append(tuple(p - side * W / 2))
    out = []
    s = grid('strap', [rows_a, rows_b], M.strap, ring=False, smooth_ang=70, out=lambda g: (g[0], 0, g[2]) if g[1] > 2.985 else (0, 0, -1))
    rim(s, 0.002)
    out.append(s)
    bt, bb_ = 2.437, 2.222
    zfwd = min(h[2] for h in (cast(T_body, (x, y, -1.0), (0, 0, 1)) for x in (-0.07, -0.035, 0.0, 0.035, 0.07) for y in (2.23, 2.28, 2.33, 2.38, 2.43)) if h)
    zh = zfwd - 0.0025  # the holder's back
    zs = (pts[0].z + pts[-1].z) / 2  # the straps' ends
    out.append(slab('crimp', rrect(0.0, 2.486, 0.036, 0.022, 0.004, 1), zs - 0.0045, zs + 0.0055, M.chrome))
    zr = zs + (zh - 0.004 - zs) * 0.45
    ring = [(math.sin(2 * math.pi * k / 6) * 0.008, 2.466 + math.cos(2 * math.pi * k / 6) * 0.008, zr) for k in range(6)]
    out.append(tube(ring, 0.0019, M.chrome, seg=4, closed=True))
    out.append(blob('lobster', (0.0, 2.449, zr + (zh - 0.004 - zr) * 0.6), (0.0075, 0.014, 0.0045), M.chrome, seg=6, rings=5))
    out.append(slab('holder', rrect(0.0, (bt + bb_) / 2, 0.152, bt - bb_, 0.014, 2), zh - 0.005, zh, M.black))  # (black, rigid)
    cw, ch = 0.132, 0.181  # the card (the game's canvas, 64 x 88)
    cy = (bt + bb_) / 2 - 0.006
    zc_ = zh - 0.0066
    card = mk('card', [(-cw / 2, cy - ch / 2, zc_), (cw / 2, cy - ch / 2, zc_), (cw / 2, cy + ch / 2, zc_), (-cw / 2, cy + ch / 2, zc_)], [(0, 1, 2, 3)], M.badge, 0)
    face_out(card, lambda g: (0, 0, -1))
    uvl = card.data.uv_layers.new(name='UVMap')
    for li, lp in enumerate(card.data.loops):
        v = card.data.vertices[lp.vertex_index].co
        uvl.data[li].uv = (0.5 - v.x / cw, 0.5 - (v.z - cy) / ch)  # viewer's right = image right; V from top (0) to bottom (1)
    card['keep_uv'] = 1
    out.append(card)
    outer = rrect(0.0, cy, cw + 0.012, ch + 0.012, 0.01, 2)
    inner = rrect(0.0, cy, cw - 0.006, ch - 0.006, 0.006, 2)
    lip = grid('lip', [[(x, y, zh - 0.0082) for x, y in outer], [(x, y, zh - 0.0082) for x, y in inner]], M.black, ring=True, out=lambda g: (0, 0, -1))
    rim(lip, 0.0032)
    out.append(lip)
    return out


# ------------------------------------------------------------ the head
def head_parts(M):
    """head-local (the joint 3.08 up): a smooth egg, bigger end up, a faint brow ridge. the earpiece on his right"""
    cy, rx, ry, rz = 0.29, 0.165, 0.255, 0.19
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=22, v_segments=14, radius=1.0)
    for v in bm.verts:
        bx, by, bz = v.co
        sx, sy, sz = bx, bz, -by  # unit sphere in game axes
        k = 1 + 0.085 * sy
        p = Vector((rx * sx * k, ry * sy, rz * sz * k - 0.012 * (1 - sy * sy)))
        n = Vector((sx / rx, sy / ry, sz / rz)).normalized()
        front = max(0.0, -n.z)
        yb = 0.068
        ridge = 0.0085 * math.exp(-((p.y - yb) / 0.03) ** 2) * front ** 2.2 * (1 - 0.4 * math.exp(-(p.x / 0.028) ** 2)) * math.exp(-(p.x / 0.13) ** 4)
        under = -0.0028 * math.exp(-((p.y - yb + 0.045) / 0.024) ** 2) * front ** 3 * math.exp(-((abs(p.x) - 0.055) / 0.035) ** 2)
        p += n * (ridge + under)
        v.co = gv(p.x, cy + p.y, p.z)
    egg = lib_obj('egg', bm, M.skin)
    for f in egg.data.polygons: f.use_smooth = True
    out = [egg]
    out.append(limb('hneck', [(0, -0.05, 0.006), (0, 0.04, 0.008), (0, 0.11, 0.012)], [0.0535, 0.052, 0.05], M.skin, seg=10))
    def ex(y, z):  # the egg's +x surface at head-local (y, z)
        sy = (y - cy) / ry; k = 1 + 0.085 * sy
        sz = (z + 0.012 * (1 - sy * sy)) / (rz * k)
        return rx * k * math.sqrt(max(0.0, 1 - sy * sy - sz * sz))
    # the earpiece: a round pod where an ear would be (the LED in its middle), a boom down toward where a mouth would
    # be, a hook over the missing ear
    py, pz = 0.272, 0.012
    px0 = ex(py, pz) - 0.002
    pod = lathe([(0.0, 0.0), (0.021, 0.0), (0.023, 0.006), (0.021, 0.012), (0.014, 0.0155), (0.0, 0.0165)], (0, 0, 0), M.black, seg=12, axis='x', name='pod')
    to_world(pod, Matrix.Translation(Vector((px0, py, pz))) @ Matrix.Rotation(-0.12, 4, 'Y'))
    out.append(pod)
    boom = []
    for t in (0.0, 0.35, 0.7, 1.0):
        y = py - 0.07 * t; z = pz - 0.088 * t
        boom.append((ex(y, z) + 0.0105 + 0.004 * (1 - t), y, z))
    out.append(limb('boom', boom, [0.0145, 0.0135, 0.0115, 0.0085], M.black, seg=8))
    tip = boom[-1]
    out.append(blob('boomtip', (tip[0] - 0.001, tip[1] - 0.002, tip[2] - 0.004), (0.0092, 0.0092, 0.0092), M.chrome, seg=8, rings=5))
    hook = []
    for t in (0.0, 0.25, 0.5, 0.75, 1.0):
        a = math.pi * (0.15 + 1.0 * t)
        y = py + 0.012 + math.sin(a) * 0.045; z = pz + 0.035 - math.cos(a) * 0.045
        hook.append((ex(y, z) + 0.0035, y, z))
    out.append(limb('hook', hook, [0.0045, 0.0042, 0.004, 0.004, 0.0035], M.black, seg=5))
    led = blob('led', (px0 + 0.0165, py, pz), (0.0058, 0.0058, 0.0058), M.led, seg=8, rings=5)
    return out, led


# ------------------------------------------------------------ arms and hands
def sleeve_upper(M, sx):
    x = sx * 0.33
    P = [(x, 2.958, 0.0), (x + sx * 0.002, 2.944, 0.0), (x + sx * 0.004, 2.92, 0.0), (x + sx * 0.005, 2.885, 0.0), (x + sx * 0.006, 2.7, -0.004),
         (x + sx * 0.004, 2.3, -0.004), (x + sx * 0.002, 2.16, 0.0), (x + sx * 0.001, 2.115, 0.002), (x, 2.095, 0.002), (x, 2.083, 0.002)]
    R = [0.018, 0.044, 0.057, 0.063, 0.06, 0.0545, 0.052, 0.044, 0.03, 0.012]
    return [sweep(P, R, M.suit, seg=10, name='sleeve', squash=(0.9, 1.0))]


def finger_pts(M, pts, radii, name='finger', seg=5):
    """a finger through its joints (knuckle .. tip): a bulge at each knuckle, a round tip"""
    P, R = [tuple(pts[0])], [radii[0]]
    for i in range(1, len(pts)):
        a, b = Vector(pts[i - 1]), Vector(pts[i])
        P += [tuple((a + b) / 2), tuple(b)]
        R += [radii[i - 1] * 0.9, radii[i] * (1.08 if i < len(pts) - 1 else 0.86)]
    d = (Vector(pts[-1]) - Vector(pts[-2])).normalized()
    P.append(tuple(Vector(pts[-1]) + d * radii[-1] * 0.7)); R.append(radii[-1] * 0.45)
    return limb(name, P, R, M.skin, seg=seg)


def board_back_z(y):
    """the clipboard's back face (game z) at height y: the code's tilt about the clip pivot"""
    yl = (y - J['clip'][1]) / math.cos(CLIP_TILT)
    return J['clip'][2] + yl * math.sin(CLIP_TILT) + 0.004 / math.cos(CLIP_TILT)


def frame(o, U, V, W):
    o, U, V, W = Vector(o), Vector(U).normalized(), Vector(V).normalized(), Vector(W).normalized()
    return lambda u, v, w: tuple(o + U * u + V * v + W * w)


def palm(M, F, k=1.0):
    """the palm in a hand frame F(u, v, w): v runs down the hand from the wrist (0) to the knuckles, u across (index
    side +), w out of the palm. flat, a little cupped, the thumb's pad on the index side"""
    rows = []
    for v, wd, t in ((0.03, 0.048, 0.029), (0.0, 0.052, 0.029), (-0.04, 0.064, 0.03), (-0.085, 0.072, 0.027), (-0.122, 0.075, 0.024), (-0.134, 0.066, 0.016)):
        row = []
        for j in range(10):
            a = 2 * math.pi * j / 10
            c, s = math.cos(a), math.sin(a)
            u = wd / 2 * math.copysign(abs(c) ** 0.75, c); w = t / 2 * math.copysign(abs(s) ** 0.85, s)
            if w > 0 and u > 0 and -0.07 < v < 0.02: w += 0.007 * (u / (wd / 2))  # the thumb's pad
            if w > 0: w -= 0.003 * (1 - abs(u) / (wd / 2))  # cupped
            row.append(F(u * k, v * k, w * k))
        rows.append(row)
    return grid('palm', rows, M.skin, ring=True, caps=(True, True), smooth_ang=70)


FING = [(0.027, 0.215), (0.009, 0.24), (-0.009, 0.225), (-0.026, 0.18)]  # (u at the knuckle, length): index .. pinky
FR = [0.0112, 0.0104, 0.0094, 0.0078]


def hand(M, sx):
    """long pale hands. the left hangs open, palm to his thigh; the right holds the clipboard by its top edge, palm to
    its back, thumb over the clip onto the jaw, the fingers down the back of the board"""
    x = sx * 0.33
    out = []
    if sx < 0:
        F = frame((x + 0.004, 1.402, -0.012), (0, 0, -1), (0.05, 1, 0), (1, -0.05, 0))
        out.append(palm(M, F))
        for i, (u0, L) in enumerate(FING):
            curl = [0.1, 0.32, 0.26] if i != 2 else [-0.08, 0.04, 0.06]  # (his ring finger doesn't curl: wrong)
            d = Matrix.Rotation(u0 * 2.2, 3, 'Z') @ Vector((0, -1, 0))  # spread (about w)
            p = Vector((u0, -0.126, -0.002)); P = [F(*p)]
            for seg_, c in zip((0.43, 0.31, 0.26), curl):
                d = Matrix.Rotation(-c, 3, 'X') @ d  # curl toward the palm (+w)
                p = p + d * L * seg_; P.append(F(*p))
            out.append(finger_pts(M, P, FR))
        p = Vector((0.03, -0.03, 0.012)); P = [F(*p)]
        for dd, L in (((0.3, -0.8, 0.5), 0.062), ((0.15, -0.9, 0.42), 0.05), ((0.05, -0.85, 0.52), 0.042)):
            p = p + Vector(dd).normalized() * L; P.append(F(*p))
        out.append(finger_pts(M, P, [0.0135, 0.0125, 0.011, 0.0092], name='thumb'))
    else:
        zt = board_back_z(1.25)
        F = frame((x - 0.002, 1.402, -0.018), (1, 0, 0), (0, 1, 0.13), (0, 0.13, -1))
        out.append(palm(M, F))
        for i, (u0, L) in enumerate(FING):  # flat down the back of the board, a little spread
            P = [F(u0, -0.126, -0.002)]
            y = P[0][1]
            for j, seg_ in enumerate((0.43, 0.31, 0.26)):
                y -= L * seg_
                P.append((x + u0 * (1.0 + 0.35 * (j + 1)), y, board_back_z(y) + 0.0118 + 0.0015 * j))
            out.append(finger_pts(M, P, FR))
        # the thumb: from the palm, forward over the board's top edge, down onto the clip's jaw
        P = [F(0.03, -0.045, 0.012), (x + 0.036, 1.292, zt - 0.02), (x + 0.037, 1.252, zt - 0.029), (x + 0.035, 1.21, zt - 0.0255)]
        out.append(finger_pts(M, P, [0.0135, 0.0125, 0.011, 0.0092], name='thumb'))
    return out


def forearm(M, sx):
    x = sx * 0.33
    P = [(x, 2.168, 0.0), (x, 2.152, 0.0), (x, 2.128, 0.0), (x, 2.085, -0.002), (x, 2.0, -0.005), (x, 1.75, -0.011), (x, 1.55, -0.012), (x, 1.468, -0.012)]
    R = [0.014, 0.038, 0.049, 0.0525, 0.0505, 0.048, 0.0465, 0.0468]
    sl = sweep(P, R, M.suit, seg=10, name='forearm', squash=(0.9, 1.0), cap=False)
    rim(sl, 0.0045)
    out = [sl]
    out.append(limb('cuff', [(x, 1.478, -0.012), (x, 1.44, -0.013), (x, 1.412, -0.014), (x, 1.404, -0.014)], [0.0395, 0.0398, 0.0405, 0.037], M.shirt, seg=10, squash=(0.9, 1.0)))
    d = Vector((sx * 0.62, 0, 0.78)).normalized()  # the cuff buttons: on the outside back of the sleeve, kissing
    for k in range(4):
        y = 1.505 + k * 0.0168
        c = Vector((x, y, -0.012)) + Vector((d.x * 0.0435, 0, d.z * 0.048))
        out.append(rod(tuple(c - d * 0.002), tuple(c + d * 0.0038), 0.0081, M.black, seg=8))
    out += hand(M, sx)
    return out


def clipboard(M):
    """clip-local (the pivot at the origin, untilted): the board hangs down from just above the pivot"""
    out = []
    out.append(slab('board', rrect(0.0, -0.12, 0.24, 0.32, 0.014, 2), -0.004, 0.004, M.board, bev=0.0016))
    out.append(slab('base', rrect(0.0, 0.021, 0.112, 0.034, 0.008, 1), -0.0062, -0.0035, M.chrome))
    for xx in (-0.04, 0.04): out.append(blob('rivet', (xx, 0.026, -0.0064), (0.0045, 0.0045, 0.0022), M.chrome, seg=8, rings=4))
    out.append(cyl(0.0056, 0.104, (0.0, 0.012, -0.0122), M.chrome, axis='x', seg=10))
    jaw = slab('jaw', rrect(0.0, -0.012, 0.104, 0.04, 0.006, 1), -0.0122, -0.0098, M.chrome)
    to_world(jaw, rot_game(rx=-0.06, at=(0, 0.008, -0.011)))
    out.append(jaw)
    for k, (z, rz, dx, dy) in enumerate([(-0.0055, 0.014, 0.004, -0.001), (-0.0072, -0.011, -0.003, -0.002), (-0.0089, 0.0, 0.0, 0.0)]):
        W, H = 0.204, 0.276
        cy_ = 0.004 - H / 2
        rows = []
        for i in range(4):
            row = []
            for j in range(3):
                u, v = j / 2, i / 3
                px_, py = (u - 0.5) * W, (v - 0.5) * H
                curl = 0.006 * max(0.0, u - 0.5) * 2 * max(0.0, 0.5 - v) * 2 if k == 2 else 0.0  # the top sheet's corner lifts
                c, s_ = math.cos(rz), math.sin(rz)
                row.append((px_ * c - py * s_ + dx, cy_ + px_ * s_ + py * c + dy, z - curl))
            rows.append(row)
        sh = grid('paper%d' % k, rows, M.paper, ring=False, out=lambda g: (0, 0, -1))
        uvl = sh.data.uv_layers.new(name='UVMap')
        for li, lp in enumerate(sh.data.loops):
            vv = sh.data.vertices[lp.vertex_index].co
            gx, gy = vv.x - dx, vv.z - dy
            u, v = 0.5 - gx / W, (gy + 0.272) / H
            uvl.data[li].uv = (u, v) if k == 2 else (0.94 + 0.04 * u, 0.01 + 0.04 * v)  # (the sheets under it: a blank corner)
        sh['keep_uv'] = 1
        out.append(sh)
    for o in out: to_world(o, Matrix.Translation(Vector(J['clip'])) @ Matrix.Rotation(CLIP_TILT, 4, 'X'))
    return out


# ------------------------------------------------------------ legs
LEG = [(2.02, 0.098, 0.112), (1.86, 0.094, 0.104), (1.6, 0.085, 0.092), (1.3, 0.077, 0.082), (0.95, 0.068, 0.073),
       (0.6, 0.065, 0.068), (0.3, 0.063, 0.066), (0.2, 0.066, 0.07), (0.1, 0.066, 0.072)]


def leg(M, sx):
    """pressed trousers (a crease down the front and back), a break where they land on the shoe, turn-ups, a cap-toe
    oxford. his left knee bends back and in a bit: wrong"""
    x0 = sx * 0.11
    wrong = sx < 0
    def centre(y):  # the trouser's middle (x, z): straight down, except his left knee goes back and in
        kz = 0.045 if wrong else -0.01; kx = -sx * 0.012 if wrong else 0.0
        if y >= 0.93: t = (2.02 - y) / (2.02 - 0.93); return (x0 + kx * t, -0.006 + (kz + 0.006) * t)
        t = (0.93 - y) / 0.83; return (x0 + kx * (1 - t), kz * (1 - t))
    def hem(th): return 0.098 + 0.027 * math.cos(th)  # up on the shoe in front, down at the heel
    N = 12
    rows = []
    for y in [2.02, 1.8, 1.5, 1.2, 1.0, 0.93, 0.86, 0.6, 0.33, 0.25, 0.215, 0.18, None]:
        row = []
        for j in range(N):
            th = 2 * math.pi * j / N
            yy = y if y is not None else hem(th)
            hx, hz = interp(LEG, yy)
            cx, cz = centre(yy)
            s, c = math.sin(th), math.cos(th)
            r = 1.06 + 0.06 * max(0.0, c) if y == 0.215 else 1.0  # the break: it buckles on the shoe
            crease = 0.006 if j == 0 else -0.006 if j == N // 2 else 0.0
            row.append((cx + s * hx * r, yy, cz - c * hz * r - crease))
        rows.append(row)
    out = [grid('trouser', rows, M.suit, ring=True, smooth_ang=50)]
    cuff = []
    for k in (0, 1):
        row = []
        for j in range(N):
            th = 2 * math.pi * j / N
            yy = hem(th) + k * 0.046
            hx, hz = interp(LEG, yy); cx, cz = centre(yy)
            crease = 0.006 if j == 0 else -0.006 if j == N // 2 else 0.0
            row.append((cx + math.sin(th) * (hx + 0.006), yy - 0.002 * (1 - k), cz - math.cos(th) * (hz + 0.006) - crease))
        cuff.append(row)
    cf = grid('turnup', cuff, M.suit, ring=True, out=lambda g: (g[0] - x0, 0, g[2]))
    rim(cf, 0.0065)
    out.append(cf)
    out += shoe(M, sx, x0, toe_out=0.13 if wrong else 0.05)
    return out


SHOE = [(0.088, 0.03, 0.098), (0.072, 0.047, 0.11), (0.03, 0.053, 0.118), (-0.03, 0.055, 0.12), (-0.09, 0.058, 0.106),
        (-0.15, 0.06, 0.085), (-0.2, 0.06, 0.069), (-0.245, 0.055, 0.06), (-0.28, 0.045, 0.05), (-0.305, 0.024, 0.037)]  # z, half width, top


def shoe(M, sx, x0, toe_out=0.05):
    def yb(z): return 0.016 + 0.019 * smoothstep(-0.07, 0.02, z)  # the heel lifts the upper
    rows = []
    for z, w, h in SHOE:
        row = []
        for k in range(9):  # the arch over the top, side to side
            a = math.pi * k / 8
            c, s = math.cos(a), math.sin(a)
            row.append((w * math.copysign(abs(c) ** 0.75, c), yb(z) + (h - yb(z)) * (abs(s) ** 0.8), z))
        row += [(-w * 0.5, yb(z) - 0.0012, z), (w * 0.5, yb(z) - 0.0012, z)]
        rows.append(row)
    out = [grid('upper', rows, M.black, ring=True, caps=(True, True), smooth_ang=60)]
    seam = []  # the cap-toe seam: a raised stitch line over the toe
    for k in range(9):
        a = math.pi * (0.06 + 0.88 * k / 8); c, s = math.cos(a), math.sin(a)
        z, w, h = -0.2, 0.06, 0.069
        seam.append((w * math.copysign(abs(c) ** 0.75, c) * 1.02, yb(z) + (h - yb(z)) * abs(s) ** 0.8 + 0.0012, z + 0.006 * s))
    out.append(limb('capseam', seam, [0.0026] * len(seam), M.black, seg=4))
    for k in range(3):  # the laces across the vamp, where the quarters meet
        z = -0.072 - k * 0.018; w, h = interp([(r[0], r[1], r[2]) for r in SHOE[::-1]], z)
        out.append(rod((-0.017, h + 0.0005, z), (0.017, h + 0.0005, z), 0.0032, M.black, seg=5))
    out.append(rod((0.0, 0.119, -0.06), (0.0, 0.101, -0.124), 0.0022, M.black, seg=4))
    fp = [(0.012, -0.313)] + [(r[1] + 0.006, r[0]) for r in SHOE if r[0] < 0.0] + [(0.061, 0.0)]  # the sole: the forefoot to the heel's front
    fp = sorted(fp, key=lambda q: q[1])
    out.append(plate_y('sole', [(w, z) for w, z in fp] + [(-w, z) for w, z in fp[::-1]], 0.0, 0.017, M.black))
    hl = [(0.058, -0.003)] + [(r[1] * 0.98, r[0]) for r in SHOE if r[0] > 0.0][::-1]  # the heel block
    hl = sorted(hl, key=lambda q: q[1])
    out.append(plate_y('heel', [(w, z) for w, z in hl] + [(-w, z) for w, z in hl[::-1]], 0.0005, 0.036, M.black))
    M4 = Matrix.Translation(Vector((x0, 0, 0))) @ Matrix.Rotation(-sx * toe_out, 4, 'Y')
    for o in out: to_world(o, M4)
    return out


# ------------------------------------------------------------ assembling the rig
def node(jn, objs, extra_name=None):
    """join a joint's pieces into hr_<joint>_m, origin on the joint"""
    objs = [o for o in objs if o is not None]
    for o in objs:
        bake(o)
        if not o.get('keep_uv'): uv_box(o, 0.14)
        if os.environ.get('JF_HR_PIECES'): o.data.calc_loop_triangles(); print('JF_PIECE', jn, o.name, len(o.data.loop_triangles))
    if os.environ.get('JF_HR_QAPIECES') == jn:  # which pieces fight (the joined mesh only says it's somewhere inside)
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.claude', 'skills', 'blender-asset-qa', 'scripts'))
        import qa_check
        bpy.context.view_layer.update()
        res = qa_check.run(objects=[o.name for o in objs], profile='game', uv=False)
        for e in res['errors']: print('JF_QAP_E', str(e)[:300])
    m = join(objs, extra_name or 'hr_%s_m' % jn)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    p = gv(*J[jn])
    m.data.transform(Matrix.Translation(-p)); m.location = (0, 0, 0)
    bm = bmesh.new(); bm.from_mesh(m.data)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
    big = [f for f in bm.faces if len(f.verts) > 4]
    if big: bmesh.ops.triangulate(bm, faces=big)
    bm.to_mesh(m.data); bm.free()
    bpy.context.view_layer.objects.active = m
    bpy.ops.object.material_slot_remove_unused()
    return m


def build():
    M = Mats()
    empties = {}
    root = bpy.data.objects.new('hrguy', None); bpy.context.scene.collection.objects.link(root)
    for jn in ('body', 'legL', 'legR', 'head', 'armL', 'armR', 'foreL', 'foreR', 'clip'):
        e = bpy.data.objects.new('hr_' + jn, None); bpy.context.scene.collection.objects.link(e)
        e.empty_display_size = 0.05
        par = PARENT[jn]
        e.parent = empties[par] if par else root
        pp = J[par] if par else (0, 0, 0)
        e.location = gv(*(J[jn][k] - pp[k] for k in range(3)))
        empties[jn] = e
    meshes = {}
    jk = jacket(M); lp = lapels(M); ib = inner_body(M); nt = neck_collar_tie(M); pb = pockets_buttons(M)
    body = jk + lp + ib + nt + pb
    neck = [o for o in body if o.name.split('.')[0] in ('collarband', 'shirtcollar', 'neck', 'collartab')]
    body += lanyard_badge(M, body, neck)
    meshes['body'] = node('body', body)
    hp, led = head_parts(M)
    for o in hp + [led]: to_world(o, Matrix.Translation(Vector(J['head'])))
    meshes['head'] = node('head', hp)
    meshes['led'] = node('head', [led], 'hr_led')
    for jn, sx in (('armL', -1), ('armR', 1)): meshes[jn] = node(jn, sleeve_upper(M, sx))
    for jn, sx in (('foreL', -1), ('foreR', 1)): meshes[jn] = node(jn, forearm(M, sx))
    meshes['clip'] = node('clip', clipboard(M))
    for jn, sx in (('legL', -1), ('legR', 1)): meshes[jn] = node(jn, leg(M, sx))
    for k, m in meshes.items():
        m.parent = empties['head' if k == 'led' else k]
        m.matrix_parent_inverse = Matrix.Identity(4)
        m.location = (0, 0, 0)
    bpy.context.view_layer.update()
    meta = {'kind': 'char', 'id': 'hrguy', 'joints': {k: list(v) for k, v in J.items()}, 'led': 'hr_led', 'badge': 'hr_badge',
            'nodes': {k: 'hr_' + k for k in J}}
    root['jf'] = json.dumps(meta)
    return root, empties, meshes


# ------------------------------------------------------------ his pose() (public/js/hrguy.js), on the empties
def pose_seed(empties, seed):
    s = seed + 1
    def r():
        nonlocal s
        s = (s * 16807) % 2147483647
        return s / 2147483647
    hx = (r() - 0.5) * 0.3; hy = (r() - 0.5) * 0.6; sg = -1 if r() < 0.5 else 1; hz = sg * (0.15 + r() * 0.45)
    bz = (r() - 0.5) * 0.08
    a0 = ((r() - 0.5) * 0.2, 0, -0.06 - r() * 0.12); f0 = -r() * 0.3
    up = r() < 0.4
    a1x = 0.5 if up else (r() - 0.5) * 0.15
    a1 = (a1x, 0, 0.06 + r() * 0.1); f1 = 1.2 if up else -r() * 0.25
    rots = {'head': (hx, hy, hz), 'body': (0, 0, bz), 'armL': a0, 'foreL': (f0, 0, 0), 'armR': a1, 'foreR': (f1, 0, 0)}
    C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
    for jn, (rx, ry, rz) in rots.items():
        Rg = Matrix.Rotation(rx, 3, 'X') @ Matrix.Rotation(ry, 3, 'Y') @ Matrix.Rotation(rz, 3, 'Z')
        Rb = C @ Rg @ C.inverted()
        e = empties[jn]; loc = e.location.copy()
        e.matrix_basis = Matrix.Translation(loc) @ Rb.to_4x4()
    bpy.context.view_layer.update()
    return up


def rest(empties):
    for e in empties.values(): e.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()


# ------------------------------------------------------------ sheets
def render_views(views, res, path, note, night=False, samples=24):
    """views: [(camera game pos, target game pos, lens)]; tiled 4 across into path"""
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'; sc.eevee.taa_render_samples = samples
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    made = []
    def light(kind, e, loc, at, sz=1.0, col=(1, 1, 1), spot=None):
        L = bpy.data.lights.new('l', kind); L.energy = e; L.color = col
        if kind == 'AREA': L.size = sz
        if kind == 'SPOT': L.spot_size = spot; L.spot_blend = 0.5; L.shadow_soft_size = 0.05
        o = bpy.data.objects.new('l', L); sc.collection.objects.link(o); o.location = gv(*loc)
        d = gv(*at) - o.location; o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); made.append(o)
        return o
    if night:
        bg.inputs['Color'].default_value = srgb(0x0c1018); bg.inputs['Strength'].default_value = 0.35
        light('SUN', 0.25, (-3, 10, -4), (0, 0, 0), col=(0.64, 0.73, 1.0))
    else:
        bg.inputs['Color'].default_value = srgb(0x3a3346); bg.inputs['Strength'].default_value = 0.6
        light('AREA', 900, (3.5, 5.5, -4.5), (0, 2, 0), 3.0); light('AREA', 300, (-5, 3, -1.5), (0, 2, 0), 4.0, (0.85, 0.9, 1.0))
        light('AREA', 650, (-1.5, 4.5, 5.5), (0, 2.2, 0), 2.0, (1.0, 0.6, 0.75))
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    made.append(cam)
    outs = []
    tmp = os.path.join(SHEETS, '_tmp'); os.makedirs(tmp, exist_ok=True)
    for i, (cp, tp, lens) in enumerate(views):
        torch = light('SPOT', 260, cp, tp, spot=0.5, col=(1.0, 0.94, 0.82)) if night else None
        cam.location = gv(*cp); d = gv(*tp) - cam.location; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        cam.data.lens = lens; cam.data.clip_start = 0.02; cam.data.clip_end = 200
        p = os.path.join(tmp, 'hr_%d.png' % i); sc.render.filepath = p
        bpy.ops.render.render(write_still=True); outs.append(p)
        if torch: made.remove(torch); bpy.data.objects.remove(torch, do_unlink=True)
    for o in made: bpy.data.objects.remove(o, do_unlink=True)
    n = len(outs); cols = min(4, n)
    lay = '|'.join('%s_%s' % ('+'.join(['w0'] * (k % cols)) or '0', '+'.join(['h0'] * (k // cols)) or '0') for k in range(n))
    flt = f'xstack=inputs={n}:layout={lay}:fill=black,' if n > 1 else ''
    os.system('ffmpeg -loglevel error -y ' + ' '.join(f'-i "{p}"' for p in outs) + f' -filter_complex "{flt}drawtext=text=\'{note}\':x=8:y=8:fontsize=18:fontcolor=0xffe14d" -q:v 3 "{path}"')
    for p in outs: os.remove(p)
    print('JF_SHEET', path)


def turnaround(tris, quick=False):
    c = (0, 1.8, 0)
    v = []
    for deg in ((0, 35, 180) if quick else (0, 35, 90, 180, 215, 300)):
        a = math.radians(deg)
        v.append(((math.sin(a) * -8.5, 2.0, -math.cos(a) * 8.5), c, 75))
    v.append(((0.55, 2.95, -1.25), (0.0, 2.72, 0.0), 50))  # the chest: tie, lapels, badge
    if not quick: v.append(((0.9, 3.4, -0.75), (0.08, 3.33, 0.0), 60))  # the head and the earpiece
    v.append(((0.95, 1.45, -0.8), (0.33, 1.2, -0.05), 50))  # the hand and the clipboard
    if not quick: v.append(((-0.45, 0.5, -0.95), (0.0, 0.12, -0.06), 45))  # the shoes
    v.append(((-0.9, 1.4, -0.9), (-0.33, 1.25, 0.0), 55))  # the left hand
    if not quick: v.append(((0.5, 2.1, 1.1), (0.0, 1.95, 0.08), 45))  # the vent
    if not quick: v += [((1.4, 3.1, -2.0), (0.0, 2.75, 0.0), 40), ((-1.6, 2.9, 1.6), (0.0, 2.8, 0.0), 40)]  # shoulders, the back of the collar
    render_views(v, (420, 560), os.path.join(SHEETS, 'c_hrguy.jpg'), f'x_hrguy  {tris} tris  3.62 m', samples=8 if quick else 24)


def closeups():
    v = [((0.75, 3.42, -0.62), (0.05, 3.35, 0.0), 55), ((-0.2, 3.36, -0.9), (0.0, 3.36, 0.0), 55),
         ((0.75, 1.32, -0.55), (0.33, 1.2, -0.04), 45), ((-0.75, 1.3, -0.45), (-0.33, 1.22, 0.0), 45),
         ((0.0, 2.75, -0.95), (0.0, 2.7, 0.0), 45), ((-0.35, 0.35, -0.7), (-0.11, 0.1, -0.08), 45)]
    render_views(v, (560, 560), os.path.join(SHEETS, 'c_hrguy_close.jpg'), 'x_hrguy close-ups', samples=12)


def night_sheet(tris):
    v = [((0.4, 1.7, -3.2), (0, 2.0, 0), 30), ((2.0, 1.7, -8.0), (0, 1.9, 0), 40), ((-1.2, 1.7, -2.4), (0, 2.6, 0), 32), ((0.6, 1.7, -1.6), (0.0, 3.0, 0.0), 35)]
    render_views(v, (420, 560), os.path.join(SHEETS, 'c_hrguy_night.jpg'), 'x_hrguy at night (a flashlight from the camera)', night=True)


def pose_sheet(empties):
    paths = []
    seeds = [7, 101, 333, 512, 777, 940]
    tmp = os.path.join(SHEETS, '_tmp'); os.makedirs(tmp, exist_ok=True)
    for k, sd in enumerate(seeds):
        up = pose_seed(empties, sd)
        p = os.path.join(tmp, 'pose_%d.jpg' % k)
        render_views([((2.4, 2.3, -7.0), (0, 1.85, 0), 55), ((-4.4, 2.2, -5.6), (0, 1.85, 0), 55)], (300, 480), p, f'pose({sd}){" UP" if up else ""}', samples=12)
        paths.append(p)
        rest(empties)
    dst = os.path.join(SHEETS, 'c_hrguy_poses.jpg')
    lay = '|'.join('%s_%s' % ('+'.join(['w0'] * (k % 3)) or '0', '+'.join(['h0'] * (k // 3)) or '0') for k in range(len(paths)))
    os.system('ffmpeg -loglevel error -y ' + ' '.join(f'-i "{p}"' for p in paths) + f' -filter_complex "xstack=inputs={len(paths)}:layout={lay}" -q:v 3 "{dst}"')
    for p in paths: os.remove(p)
    print('JF_SHEET', dst)


def qa(meshes):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    hits = []
    if os.environ.get('JF_ZF_DEBUG'):  # where the coplanar faces are (blender x, y, z), to find a z-fight by hand
        pit = qa_check._point_in_tri
        def spy(q, a, b, c, n):
            r = pit(q, a, b, c, n)
            if r and abs(n.dot((b - a).cross(c - a).normalized())) > 0.999: hits.append((round(q.x, 3), round(q.y, 3), round(q.z, 3), round(n.x, 2), round(n.y, 2), round(n.z, 2)))
            return r
        qa_check._point_in_tri = spy
    bpy.context.view_layer.update()
    res = qa_check.run(objects=[m.name for m in meshes.values()], profile='game')
    print('JF_QA', 'PASS' if res['pass'] else 'FAIL', len(res['errors']), 'errors', len(res['warnings']), 'warnings')
    for e in res['errors']: print('JF_QA_E', str(e)[:400])
    for w in res['warnings']: print('JF_QA_W', str(w)[:400])
    for h in sorted(set(hits))[:200]: print('JF_ZF', h)
    return res


def run():
    reset()
    root, empties, meshes = build()
    tris = 0
    for k, m in meshes.items():
        m.data.calc_loop_triangles(); n = len(m.data.loop_triangles); tris += n
        print('JF_PART', m.name, n, 'tris', len(m.data.materials), 'mats', [x.name for x in m.data.materials])
    print('JF_TRIS', tris)
    if '--qa' in ARGV: qa(meshes)
    if '--no-export' not in ARGV: export(root, FILE)
    if '--no-sheet' not in ARGV: turnaround(tris, '--quick' in ARGV)
    if '--close' in ARGV: closeups()
    if '--night' in ARGV: night_sheet(tris)
    if '--poses' in ARGV: pose_sheet(empties)


run()
