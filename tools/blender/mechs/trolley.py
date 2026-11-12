# TROLLEY: the speed hero (docs/mechs/ROSTER.md). An original JANKFIRE hero: a 4 m shopping trolley mech. A chrome
# wire basket on a low steel chassis with team-colour side covers, a team-colour push handle with a pound-coin lock,
# a rubber bumper and headlights for ramming, four caster wheels (the front-left one is wonky), a fold-down child seat
# for a rider, a rear deck where the pilot stands at the handle, a tall safety flag, and two little boosters under the
# deck for CLEAN UP AISLE 5. Clean look (the owner's references): glossy paint, chrome, few strong glows. The detail
# pass (2026-11-12): coil-over springs and brake pedals on the casters, lug bolts and deep tread on the wheels, a drive
# motor with cooling fins under the deck, fuel lines to the boosters, headlight visors, a number plate, a chained coin
# lock and a wing mirror; details and dt() parts drop out of the far LOD.
# Game space: faces -z (the basket's nose), the handle at the back (+z), its right is +x, wheels on y = 0.
from mechkit import *
import herokit
from detailkit import *

FID = 'mech_trolley'
WR = 0.32  # wheel radius
PAL_A = {  # "BIG SHOP": red handle / bumper / covers, chrome wire, yellow coin lock and seat, white headlights
    'paint': 0xe8202a, 'paint2': 0xffd23a, 'white': 0xf4f2ee, 'dark': 0x1a1a22, 'accent': 0xffd23a, 'frame': 0x40464f,
    'chrome': 0xd8dee6, 'rubber': 0x18181c, 'glass': 0x0c1222, 'glow': 0xfff6d8, 'thrust': 0x7df9ff, 'flag': 0xff7a1c,
    'hazard': 0xffd23a,
}
PAL_B = {  # "MIDNIGHT RUN": cyan, pink seat, green boosters
    'paint': 0x27c6e6, 'paint2': 0xff4fbf, 'white': 0xf4f0ec, 'dark': 0x1c1420, 'thrust': 0x9dff6a, 'flag': 0xff4fbf,
}
ROLE_LOOK.setdefault('flag', (0.5, 0.0, 0.3)); ROLE_LOOK.setdefault('hazard', (0.30, 0.0, 1.0))
NUMBER = 'A5'  # (aisle 5)
CASTER = {'FL': (-0.92, 0.72, -1.52), 'FR': (0.92, 0.72, -1.52), 'BL': (-1.06, 0.72, 1.40), 'BR': (1.06, 0.72, 1.40)}  # (on top of the rails: the tyres clear the mounts)
HINGE = (0.0, 0.92, -1.70)  # the basket tips about its front-bottom edge
BASKET = {'y0': 0.92, 'y1': 1.86, 'zf0': -1.70, 'zf1': -1.84, 'zb0': 1.20, 'zb1': 1.30, 'wf0': 0.84, 'wf1': 0.96, 'wb0': 1.00, 'wb1': 1.12}


def wheel_c(k): c = CASTER[k]; return (c[0], WR, c[2] + 0.10)


# ------------------------------------------------------------ build
def build():
    mk = Mech(FID, 'tr', PAL_A); M = mk.M
    mk.joint('root', (0, 0, 0)); mk.joint('chassis', (0, 0.55, 0), 'root')
    mk.joint('basket', HINGE, 'chassis'); mk.joint('seat', (0, 1.82, 1.20), 'basket')
    mk.joint('handle', (0, 1.78, 1.70), 'chassis'); mk.joint('bumper', (0, 0.52, -1.80), 'chassis'); mk.joint('flag', (-1.02, 1.80, 1.62), 'chassis')
    for k, c in CASTER.items():
        mk.joint('caster_' + k, c, 'chassis'); mk.joint('wheel_' + k, wheel_c(k), 'caster_' + k)
    T = {}
    chassis(mk, M, T); basket(mk, M, T); handle(mk, M, T); bumper(mk, M, T); flag(mk, M, T)
    for k in CASTER: caster(mk, M, T, k)
    stickers(mk, M, T)
    mk.meta.update({'name': 'TROLLEY', 'height': 2.6, 'wheel_radius': WR, 'phase': 'concept',
                    'palettes': {'A': {k: PAL_A[k] for k in ('paint', 'paint2', 'white', 'dark', 'glow', 'thrust')},
                                 'B': {k: PAL_B[k] for k in ('paint', 'paint2', 'white', 'dark', 'thrust')}}})
    return mk


def box(x0, x1, y0, y1, z0, z1, m, bev=0.02, name='box'):
    return hull([(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)], m, bev, 2, name)


def bar(a, b, r, m, name='bar', seg=8):
    return cyl(a, b, r, m, seg, name=name)


def chassis(mk, M, T):
    C = []
    for s in (1, -1):  # two side rails, the covers on them (team colour), cross members
        C.append(bar((s * 0.92, 0.66, -1.62), (s * 1.06, 0.66, 1.52), 0.06, M['frame'], 'rail', 16))
        C.append(hull([(s * x, y, z) for (x, z) in ((0.99, -1.40), (1.13, 1.30)) for y in (0.50, 0.80) for _ in (0,)] +
                      [(s * x, y, z) for (x, z) in ((0.93, -1.40), (1.07, 1.30)) for y in (0.50, 0.80)], M['paint'], 0.025, name='cover'))
    for z in (-1.62, -0.40, 0.70, 1.52):
        w = 0.92 + (z + 1.62) / 3.14 * 0.14
        C.append(bar((-w, 0.66, z), (w, 0.66, z), 0.045, M['frame'], 'cross', 12))
    for x in (-0.6, -0.3, 0.0, 0.3, 0.6):  # the bottom tray (wire)
        C.append(bar((x, 0.62, -1.56), (x, 0.62, 1.46), 0.025, M['chrome'], 'tray'))
    for k, c in CASTER.items():  # caster mount plates under the rails
        C.append(box(c[0] - 0.13, c[0] + 0.13, c[1] - 0.04, c[1] + 0.03, c[2] - 0.13, c[2] + 0.13, M['frame'], 0.012, 'mount'))
    for (x, z) in ((0.84, -1.20), (-0.84, -1.20), (0.98, 1.00), (-0.98, 1.00)):  # the posts the basket rests on
        C.append(bar((x, 0.66, z), (x, BASKET['y0'], z), 0.04, M['chrome'], 'rest'))
    # the rear deck the pilot stands on, a chrome edge, and two little boosters under it
    C.append(box(-0.62, 0.62, 0.58, 0.70, 1.30, 1.92, M['rubber'], 0.02, 'deck'))
    C.append(box(-0.64, 0.64, 0.56, 0.62, 1.88, 1.96, M['chrome'], 0.012, 'deckedge'))
    for x in (-0.38, 0.38):
        C.append(cyl((x, 0.44, 1.30), (x, 0.44, 1.86), 0.13, M['dark'], 28, name='booster'))
        C.append(cyl((x, 0.44, 1.36), (x, 0.44, 1.46), 0.145, M['paint'], 28, name='boosterband'))
        C += nozzle((x, 0.44, 1.86), (0, 0, 1), 0.12, 0.16, M, 'boosternoz', seg=28)
        C += ribs((x, 0.44, 1.52), (0, 0, 1), 0.138, 0.138, 3, 0.26, M['frame'], 'boosterrib')
    C.append(box(-0.52, 0.52, 0.40, 0.58, 1.27, 1.40, M['frame'], 0.012, 'boostermount'))
    mk.add('chassis', C); T['chassis'] = C
    chassis_detail(mk, M, T)


def cover_x(z, s): return s * (0.99 + (z + 1.40) / 2.70 * 0.14)  # (the cover's slanted outer face)


def chassis_detail(mk, M, T):
    D = []
    for s in (1, -1):  # the covers: bolts at the ends, a chrome strip along the top
        n = norm((s, 0, -s * 0.052))
        D += bolts([(cover_x(z, s) + s * 0.002, y, z) for z in (-1.30, 1.20) for y in (0.56, 0.74)], n, M['chrome'], 0.016, 0.009)
        D += dt([bar((cover_x(-1.36, s) - s * 0.012, 0.795, -1.36), (cover_x(1.26, s) - s * 0.012, 0.795, 1.26), 0.016, M['chrome'], 'coverstrip', 10)])
    # the drive motor under the middle: a dark box, cooling fins down its sides, a cable to each booster
    D += dt([box(-0.38, 0.38, 0.40, 0.585, -0.70, 0.30, M['dark'], 0.02, 'motor'), box(-0.30, 0.30, 0.36, 0.42, -0.60, 0.20, M['frame'], 0.012, 'motorpan')])
    for s in (1, -1):
        D += dt([box(s * 0.375 - 0.004, s * 0.425 + 0.004, 0.43, 0.555, z - 0.012, z + 0.012, M['frame'], 0.0, 'fin') for z in (-0.58, -0.46, -0.34, -0.22, -0.10, 0.02, 0.14)])
        D += hose([(s * 0.20, 0.47, 0.30), (s * 0.24, 0.47, 0.70), (s * 0.34, 0.47, 1.05), (s * 0.38, 0.47, 1.28)], 0.026, M, 'fuelline')
    # the deck: grip ribs front and back (the NO STEP sticker sits between them)
    D += dt([box(-0.55, 0.55, 0.698, 0.716, z - 0.016, z + 0.016, M['rubber'], 0.0, 'deckrib') for z in (1.37, 1.45, 1.79, 1.86)])
    D += bolts([(x, 0.40, 1.335) for x in (-0.44, 0.44)] + [(x, 0.52, 1.402) for x in (-0.44, 0.44)], (0, 0, 1), M['chrome'], 0.016, 0.009)  # (booster mount)
    for k, c in CASTER.items():  # caster mounts: four bolts underneath
        D += bolts([(c[0] + dx, c[1] - 0.04, c[2] + dz) for dx in (-0.095, 0.095) for dz in (-0.095, 0.095)], (0, -1, 0), M['chrome'], 0.015, 0.008)
    for s in (1, -1):  # the hinge brackets under the basket's nose
        D += dt([box(s * 0.70 - 0.03, s * 0.70 + 0.03, 0.62, 0.90, -1.74, -1.60, M['frame'], 0.01, 'hingebracket')])
    mk.add('chassis', D)


def wall(p00, p10, p01, p11, nu, nv, r, m, name, ends=True):
    """a wire panel on a bilinear quad: nu bars running along v, nv bars along u (ends = the two edge bars too: the
    panel that shares a corner leaves its own out, so no bar is doubled)"""
    L = lambda u, v: lerp(lerp(p00, p10, u), lerp(p01, p11, u), v)
    out = [bar(L(i / nu, 0), L(i / nu, 1), r, m, name, 12) for i in (range(nu + 1) if ends else range(1, nu))]
    out += [bar(L(0, j / nv), L(1, j / nv), r * 0.8, m, name, 12) for j in range(1, nv)]
    return out


def basket(mk, M, T):
    b = BASKET; y0, y1 = b['y0'], b['y1']
    FL0, FR0, BL0, BR0 = (-b['wf0'], y0, b['zf0']), (b['wf0'], y0, b['zf0']), (-b['wb0'], y0, b['zb0']), (b['wb0'], y0, b['zb0'])
    FL1, FR1, BL1, BR1 = (-b['wf1'], y1, b['zf1']), (b['wf1'], y1, b['zf1']), (-b['wb1'], y1, b['zb1']), (b['wb1'], y1, b['zb1'])
    B = []
    B += wall(FL0, BL0, FL1, BL1, 14, 4, 0.03, M['chrome'], 'side_L')
    B += wall(FR0, BR0, FR1, BR1, 14, 4, 0.03, M['chrome'], 'side_R')
    B += wall(FL0, FR0, FL1, FR1, 8, 4, 0.03, M['chrome'], 'front', ends=False)
    B += wall(BL0, BR0, BL1, BR1, 9, 4, 0.03, M['chrome'], 'back', ends=False)
    B += wall(FL0, FR0, BL0, BR0, 7, 12, 0.03, M['chrome'], 'floor', ends=False)
    rim = [FL1, FR1, BR1, BL1, FL1]
    for a, c in zip(rim, rim[1:]): B.append(bar(a, c, 0.055, M['chrome'], 'rim', 14))
    for a, c in ((FL0, FR0), (BL0, BR0), (FL0, BL0), (FR0, BR0)): B.append(bar(a, c, 0.05, M['frame'], 'floorframe'))
    B.append(cyl(add(FL1, (0.10, 0.0, 0.0)), add(FR1, (-0.10, 0.0, 0.0)), 0.085, M['paint'], 24, name='nosetrim'))  # (a team-colour bar on the nose rim)
    B.append(cyl((-0.70, y0 - 0.02, b['zf0'] + 0.02), (0.70, y0 - 0.02, b['zf0'] + 0.02), 0.07, M['frame'], 24, name='hingebar'))
    nf = norm((0, 0.14 / 0.94, -1))  # the front wall's slant: a team-colour plate wired onto it (the aisle number goes here)
    pc = (0, 1.42, lerp((0, y0, b['zf0']), (0, y1, b['zf1']), (1.42 - y0) / (y1 - y0))[2])
    B.append(skin(pc, fr(nf), 0.86, 0.36, M['paint'], 0.05, 0.05, 0.03, name='nameplate')); T['nameplate'] = B[-1]; T['np_c'] = add(pc, mul(nf, 0.05)); T['np_n'] = nf
    B += bolts([at(pc, fr(nf), x, y, 0.05) for x in (-0.37, 0.37) for y in (-0.13, 0.13)], nf, M['chrome'], 0.014, 0.008)
    B += dt([cyl((x, y0 - 0.02, b['zf0'] + 0.02), (x + (0.04 if x > 0 else -0.04), y0 - 0.02, b['zf0'] + 0.02), 0.085, M['chrome'], 20, bev=0.004, name='hingecap') for x in (-0.70, 0.70)])
    mk.add('basket', B); T['basket'] = B
    # the child seat: a yellow plastic panel hinged at the back rim, folded up against the back wall (flips down)
    S = [box(-0.42, 0.42, 1.30, 1.80, 1.12, 1.18, M['paint2'], 0.012, 'seatpanel')]
    for x in (-0.20, 0.20): S.append(box(x - 0.09, x + 0.09, 1.36, 1.50, 1.105, 1.13, M['dark'], 0.004, 'leghole'))
    S.append(bar((-0.45, 1.82, 1.18), (0.45, 1.82, 1.18), 0.04, M['chrome'], 'seathinge', 14))  # (its ends past the panel's sides: not flush on the far LOD)
    mk.add('seat', S); T['seat'] = S


def handle(mk, M, T):
    H = []
    for s in (1, -1):  # the posts from the chassis' back corners up to the handle
        H.append(bar((s * 1.06, 0.70, 1.52), (s * 1.02, 1.74, 1.68), 0.055, M['chrome'], 'post'))
        H.append(box(s * 1.02 - 0.08, s * 1.02 + 0.08, 1.70, 1.86, 1.62, 1.78, M['dark'], 0.02, 'grip_end'))
    H.append(cyl((-1.06, 1.78, 1.70), (1.06, 1.78, 1.70), 0.085, M['paint'], 28, name='handlebar'))
    H.append(box(-0.16, 0.16, 1.82, 2.02, 1.60, 1.80, M['paint2'], 0.025, 'coinlock'))  # the pound-coin lock (allies ride)
    H.append(box(-0.05, 0.05, 1.92, 1.97, 1.585, 1.60, M['dark'], 0.004, 'coinslot'))
    for i in range(6):  # the coin lock's chain: real links, hanging off the lock
        c = lerp((0.10, 1.84, 1.585), (0.30, 1.62, 1.46), i / 5); c = (c[0], c[1] - 0.04 * math.sin(math.pi * i / 5), c[2])
        ax = (0, 0, 1) if i % 2 else (1, 0, 0)
        H += dt([tube(ring_pts(c, ax, 0.026, 10, (1.0, 0.6), ref=norm((0.2, -0.22, -0.125))) + [ring_pts(c, ax, 0.026, 10, (1.0, 0.6), ref=norm((0.2, -0.22, -0.125)))[0]], 0.006, M['chrome'], 6, 'chainlink')])
    H += dt([box(0.27, 0.33, 1.56, 1.63, 1.43, 1.49, M['paint2'], 0.006, 'chaintag')])
    for s in (1, -1):  # clamps where the posts meet the bar
        H += dt([cyl((s * 0.93, 1.78, 1.70), (s * 0.97, 1.78, 1.70), 0.10, M['chrome'], 20, bev=0.004, name='clamp')])
    H += dt([tube([(-1.02, 1.86, 1.70), (-1.04, 2.02, 1.66), (-1.10, 2.14, 1.60)], 0.016, M['chrome'], 8, 'mirrorstalk'),  # (a wing mirror: it checks its blind spot)
             lathe_ax([(0.0, 0.0), (0.11, 0.0), (0.12, 0.02), (0.11, 0.045), (0.0, 0.05)], (-1.12, 2.20, 1.60), (0, 0.1, -1), M['dark'], 20, 'mirror'),  # (its back to the front)
             lathe_ax([(0.0, 0.0), (0.095, 0.0), (0.095, 0.012), (0.0, 0.012)], (-1.12, 2.2006, 1.594), (0, -0.1, 1), M['chrome'], 20, 'mirrorglass')])  # (the glass faces the pilot)
    mk.add('handle', H); T['handle'] = H


def bumper(mk, M, T):
    B = [tube([(-0.98, 0.52, -1.36), (-1.0, 0.52, -1.70), (-0.90, 0.52, -1.86), (0.90, 0.52, -1.86), (1.0, 0.52, -1.70), (0.98, 0.52, -1.36)], 0.10, M['paint'], 12, 'bumper')]
    B.append(box(-0.86, 0.86, 0.40, 0.66, -1.80, -1.68, M['dark'], 0.02, 'nose'))
    for x in (-0.55, 0.55):
        c = (x, 0.53, -1.82)
        B.append(frustum(c, add(c, (0, 0, -0.06)), 0.11, 0.10, M['chrome'], 32, bev=0.008, name='lampring'))
        B.append(lathe_ax([(0.085, 0.0), (0.084, 0.012), (0.078, 0.03), (0.05, 0.045), (0.0, 0.05)], add(c, (0, 0, -0.04)), (0, 0, -1), M['glow'], 32, 'lamp'))
        sx = 1 if x > 0 else -1  # a visor over each lamp, tilted in: a scowl
        B += dt([hull([add(c, (dx, 0.105 + 0.03 * sx * dx / 0.13 + dy, z)) for dx in (-0.13, 0.13) for dy in (0.0, 0.035) for z in (-0.02, -0.13)], M['dark'], 0.01, name='visor')])
    for sx in (-1, 1):  # corner lights
        c = (sx * 0.95, 0.60, -1.73)
        B += dt([frustum(c, add(c, (0, 0, -0.04)), 0.05, 0.045, M['chrome'], 16, bev=0.0, name='blinkring'),
                 lathe_ax([(0.04, 0.0), (0.03, 0.02), (0.0, 0.026)], add(c, (0, 0, -0.035)), (0, 0, -1), M['paint'], 16, 'blinker')])  # (roles the bumper already has: no new draw calls)
    pc = (0.0, 0.47, -1.80)  # a number plate on the nose (the serial sticker is its text)
    B.append(box(-0.22, 0.22, 0.42, 0.53, -1.83, -1.79, M['chrome'], 0.008, 'plate')); T['plate'] = B[-1]
    B += bolts([(x, 0.475, -1.83) for x in (-0.19, 0.19)], (0, 0, -1), M['chrome'], 0.012, 0.007)
    mk.add('bumper', B); T['bumper'] = B


def flag(mk, M, T):
    b = (-1.02, 1.80, 1.62)
    F = [bar(b, add(b, (0, 1.35, 0)), 0.025, M['white'], 'pole')]
    top = add(b, (0, 1.35, 0))
    F.append(hull([add(top, (dx, y, z)) for dx in (-0.012, 0.012) for (y, z) in ((0.0, 0.0), (-0.42, 0.0), (-0.21, 0.62))], M['flag'], 0.004, name='pennant'))
    F.append(ball(top, 0.045, M['paint2'], 10, 6, 'poletip'))
    F.append(box(b[0] - 0.07, b[0] + 0.07, b[1] - 0.02, b[1] + 0.13, b[2] - 0.07, b[2] + 0.07, M['dark'], 0.01, 'poleclamp'))
    F += bolts([(b[0] - 0.072, b[1] + 0.055, b[2] + dz) for dz in (-0.035, 0.035)], (-1, 0, 0), M['white'], 0.012, 0.007)
    mk.add('flag', F); T['flag'] = F


def caster(mk, M, T, k):
    c = CASTER[k]; w = wheel_c(k)
    Cs = [cyl(add(c, (0, -0.06, 0)), add(c, (0, 0.02, 0)), 0.11, M['chrome'], 28, name='swivel')]
    Cs += dt([cyl(add(c, (0, -0.075, 0)), add(c, (0, -0.058, 0)), 0.122, M['frame'], 28, bev=0.003, name='bearing')])
    s = 1 if c[0] > 0 else -1  # a coil-over shock on the outer side: a yellow spring round a dark damper
    top, bot = add(c, (s * 0.20, -0.07, -0.02)), add(w, (s * 0.20, 0.06, 0.0))
    Cs += dt([cyl(top, bot, 0.022, M['chrome'], 12, bev=0.0, name='damper'), cyl(add(top, (0, 0.02, 0)), add(top, (0, -0.02, 0)), 0.05, M['frame'], 16, bev=0.003, name='shocktop'),
              box(c[0] + s * 0.115, c[0] + s * 0.24, c[1] - 0.075, c[1] - 0.045, c[2] - 0.06, c[2] + 0.02, M['frame'], 0.006, 'shockarm')])
    Cs += helix(add(top, mul(norm(sub(bot, top)), 0.04)), sub(bot, top), 0.042, math.dist(top, bot) - 0.08, 4.5, 0.009, M['paint2'], 14, 'spring')
    Cs += dt([cyl(add(w, (s * 0.145, 0, 0)), add(w, (s * 0.215, 0, 0)), 0.04, M['chrome'], 6, bev=0.0, name='axlenut')])
    if c[2] > 0:  # the back casters have brake pedals
        Cs += dt([hull([add(c, (dx, dy, dz)) for dx in (-0.06, 0.06) for (dy, dz) in ((-0.05, 0.10), (-0.02, 0.10), (-0.07, 0.25), (-0.045, 0.26))], M['paint2'], 0.008, name='brake')])
    for s in (-1, 1):  # the fork: two plates down to the axle, trailing back a little
        Cs.append(hull([add(c, (s * 0.12 + dx, -0.05, -0.08)) for dx in (-0.02, 0.02)] + [add(c, (s * 0.12 + dx, -0.05, 0.10)) for dx in (-0.02, 0.02)] +
                       [add(w, (s * 0.12 + dx, 0.0, dz)) for dx in (-0.02, 0.02) for dz in (-0.07, 0.07)], M['frame'], 0.01, name='fork'))
    Cs.append(bar(add(w, (-0.15, 0, 0)), add(w, (0.15, 0, 0)), 0.03, M['chrome'], 'axle'))
    mk.add('caster_' + k, Cs)
    # the wheel: a fat rubber tyre with a tread, a yellow hub (the wonky front-left one gets a red hub)
    Wh = [lathe_ax([(WR - 0.11, -0.09), (WR - 0.05, -0.098), (WR - 0.018, -0.088), (WR, -0.06), (WR, 0.06), (WR - 0.018, 0.088), (WR - 0.05, 0.098), (WR - 0.11, 0.09), (WR - 0.11, -0.09)], w, (1, 0, 0), M['rubber'], 40, 'tyre', cap=False)]
    Wh.append(lathe_ax([(0.0, -0.075), (WR - 0.10, -0.075), (WR - 0.10, 0.075), (0.0, 0.075)], w, (1, 0, 0), M['paint' if k == 'FL' else 'paint2'], 32, 'hub'))
    Wh.append(cyl(add(w, (-0.09, 0, 0)), add(w, (0.09, 0, 0)), 0.06, M['chrome'], 24, name='hubcap'))
    for sx in (-1, 1):  # a chrome dish ring and five lug bolts on each face of the hub
        Wh += dt([lathe_ax([(0.14, 0.0), (0.15, 0.006), (0.145, 0.014), (0.125, 0.016), (0.12, 0.0), (0.14, 0.0)], add(w, (sx * 0.068, 0, 0)), (sx, 0, 0), M['chrome'], 28, 'hubring', cap=False)])
        Wh += bolt_ring(add(w, (sx * 0.075, 0, 0)), (sx, 0, 0), 0.092, 5, M['chrome'], 0.014, 0.01)
    for i in range(12):  # tread blocks
        a = 2 * math.pi * i / 12
        p = add(w, (0, math.cos(a) * (WR - 0.005), math.sin(a) * (WR - 0.005)))
        Wh += dt([hull([add(p, (dx + (0.012 if i % 2 else -0.012), math.cos(a) * dr - math.sin(a) * dt_, math.sin(a) * dr + math.cos(a) * dt_)) for dx in (-0.06, 0.06) for dr in (-0.01, 0.026) for dt_ in (-0.03, 0.03)], M['rubber'], 0.006, name='tread')])
    mk.add('wheel_' + k, Wh)


def stickers(mk, M, T):
    m = herokit.atlas_mat(mk, NUMBER)
    covers = [o for o in T['chassis'] if o.name.startswith('cover')]
    for s in (1, -1):
        o = herokit.stamp(covers, 'number', (s * 1.12, 0.65, -0.95), (s, 0, 0), (0, 1, 0), 0.52, m)
        if o: mk.add('chassis', o)
    for cell, c, n, w in (('cola', (1.12, 0.65, 0.55), (1, 0, 0), 0.62), ('bread', (-1.12, 0.65, 0.40), (-1, 0, 0), 0.26),
                          ('tri', (-1.12, 0.65, 0.85), (-1, 0, 0), 0.20)):
        o = herokit.stamp(covers, cell, c, n, (0, 1, 0), w, m)
        if o: mk.add('chassis', o)
    o = herokit.stamp([T['nameplate']], 'number', add(T['np_c'], (0, 0, 0)), T['np_n'], (0, 1, 0), 0.40, m)
    if o: mk.add('basket', o)
    o = herokit.stamp([T['plate']], 'serial', (0.0, 0.475, -1.83), (0, 0, -1), (0, 1, 0), 0.40, m)
    if o: mk.add('bumper', o)
    o = herokit.stamp([x for x in T['chassis'] if x.name.startswith('deck')], 'nostep', (0, 0.70, 1.62), (0, 1, 0), (0, 0, -1), 0.60, m)  # (where the pilot stands)
    if o: mk.add('chassis', o)
    mk.meta['spray'] = [{'name': 'spray_0', 'joint': 'chassis', 'at': [-1.125, 0.65, -0.25], 'dir': [-1, 0, 0], 'up': [0, 1, 0], 'size': 0.42},
                        {'name': 'spray_1', 'joint': 'chassis', 'at': [1.125, 0.65, -0.25], 'dir': [1, 0, 0], 'up': [0, 1, 0], 'size': 0.42}]


# ------------------------------------------------------------ markers
def marks(mk):
    b = BASKET
    m = {
        'mk_seat': {'joint': 'chassis', 'at': (0, 0.71, 1.62), 'dir': (0, 0, -1)},  # (the pilot stands here at the handle)
        'mk_rider': {'joint': 'basket', 'at': (0, b['y0'] + 0.05, -0.10), 'dir': (0, 0, -1)},  # (an ally riding in the basket)
        'mk_scoop': {'joint': 'basket', 'at': (0, b['y1'] - 0.10, b['zf1'] + 0.10), 'dir': (0, 0, -1)},
        'mk_muzzle': {'joint': 'handle', 'at': (0.40, 2.10, 1.50), 'dir': norm((0, 0.35, -1))},  # (tin cans lobbed from the handle)
        'mk_bumper': {'joint': 'bumper', 'at': (0, 0.52, -1.98), 'dir': (0, 0, -1)},
        'mk_eject': {'joint': 'chassis', 'at': (0, 1.20, 1.66), 'dir': norm((0, 1, 0.3))},
        'mk_mark': {'joint': 'flag', 'at': (-1.02, 3.55, 1.62), 'dir': (0, 1, 0)},
    }
    for s, L in ((1, 'R'), (-1, 'L')):
        m['mk_thrust_' + L] = {'joint': 'chassis', 'at': (s * 0.38, 0.44, 2.04), 'dir': (0, 0, 1)}
    for k in CASTER:
        m['mk_wheel_' + k] = {'joint': 'caster_' + k, 'at': add(wheel_c(k), (0, -WR, 0)), 'dir': (0, -1, 0)}  # (where it touches: sparks / dust; on the caster, which doesn't spin)
    for sl in mk.meta.get('spray', []):
        m['mk_' + sl['name']] = {'joint': sl['joint'], 'at': tuple(sl['at']), 'dir': tuple(sl['dir'])}
    return m


# ------------------------------------------------------------ clips
def clips():
    from clips import clip, ev_, M
    W4 = ('FL', 'FR', 'BL', 'BR')
    ch = lambda r=(0, 0, 0), p=(0, 0, 0): {'chassis': {'r': r, 'p': p}}
    spin = lambda a, wob=0: {**{'wheel_' + k: (a, 0, 0) for k in W4}, 'caster_FL': (0, wob, 0)}  # (a < 0: rolling forward)
    st = M(ch(), spin(0))
    out = []
    a = M(st, {'flag': (0, 0, 3), 'caster_FL': (0, 8, 0)}); b = M(st, ch((0.6, 0, 0.5), (0, -0.01, 0)), {'flag': (2, 0, -3), 'caster_FL': (0, -6, 0)})
    out.append(clip('idle', 2.0, [(0, a), (1.0, b)], loop=True, note='a jiggle; the flag waves, the wonky wheel twitches'))
    # drive: the wheels turn once (game: timeScale = speed / (2 pi x 0.32)), the chassis rattles, the wonky wheel wobbles
    keys = []
    for k in range(9):
        t = k / 8; r = ch((0.5 * math.sin(4 * math.pi * t), 0, 0.8 * math.sin(2 * math.pi * t)), (0, 0.012 * math.sin(4 * math.pi * t), 0))
        keys.append((t, M(r, spin(-45 * k, 14 * math.sin(4 * math.pi * t)), {'flag': (-28, 0, 6 * math.sin(2 * math.pi * t))})))
    dv = clip('drive', 1.0, keys, loop=True, note='one wheel turn, linear (timeScale = speed / (2 pi x 0.32)); rattle, wobble, flag streaming back')
    dv['linear'] = True; out.append(dv)
    # drift: casters swivel 35 degrees, the chassis yaws into it and leans out, wheels still spinning
    for side, sg in (('L', 1), ('R', -1)):
        keys = []
        for k in range(5):
            t = k / 4 * 0.6
            keys.append((t, M(ch((0, 12 * sg, -6 * sg), (0, 0, 0)), {**{'caster_' + c: (0, 35 * sg, 0) for c in W4}, **{'wheel_' + c: (-90 * k, 0, 0) for c in W4}},
                             {'flag': (-30, 0, 20 * sg), 'basket': (0, 0, 0)})))
        dr = clip('drift_' + side, 0.6, keys, loop=True, note=f'sliding sideways, turning {"left" if sg > 0 else "right"} (casters at 35 degrees); builds the ram charge')
        dr['linear'] = True; dr['events'] = [ev_(0.0, 'dust', 'mk_wheel_BL' if sg > 0 else 'mk_wheel_BR', 0, True, 0.6), ev_(0.3, 'spark', 'mk_wheel_FL' if sg > 0 else 'mk_wheel_FR')]
        out.append(dr)
    # push (E): rock back, then ram forward hard (hit at 0.24 s), the basket rattling
    back = M(st, ch((5, 0, 0), (0, 0.02, 0.22)), {'basket': (4, 0, 0), 'flag': (10, 0, 0)})
    ram = M(st, ch((-7, 0, 0), (0, -0.04, -0.45)), spin(-60), {'basket': (-10, 0, 0), 'flag': (-40, 0, 0)})
    pu = clip('push', 0.7, [(0, st), (0.12, back), (0.24, ram), (0.36, M(ram, ch((-3, 0, 0), (0, 0, -0.30)))), (0.7, st)], note='TROLLEY PUSH: a ram, hit at 0.24 s at mk_bumper')
    pu['snap'] = (2,); pu['events'] = [ev_(0.24, 'spark', 'mk_bumper', 0.35), ev_(0.24, 'dust', 'mk_bumper', 0, True)]; out.append(pu)
    # scoop / dump: the basket dips its nose to scoop, or tips right over to dump
    sc = clip('scoop', 0.8, [(0, st), (0.14, M(st, {'basket': (6, 0, 0)})), (0.26, M(st, ch((-3, 0, 0)), {'basket': (-38, 0, 0)})), (0.52, M(st, {'basket': (4, 0, 0)})), (0.8, st)],
              note='the basket dips its nose (people scooped in at 0.26 s go to mk_rider), comes back up')
    sc['snap'] = (2,); sc['events'] = [ev_(0.26, 'dust', 'mk_scoop', 0.1, True)]; out.append(sc)
    dp = clip('dump', 1.0, [(0, st), (0.14, M(st, {'basket': (8, 0, 0)})), (0.34, M(st, ch((-4, 0, 0)), {'basket': (-82, 0, 0)})), (0.62, M(st, {'basket': (-76, 0, 0)})), (1.0, st)],
              note='tips the basket right over (whoever is in it falls out at 0.34 s)')
    dp['snap'] = (2,); dp['events'] = [ev_(0.34, 'dust', 'mk_scoop', 0.15, True, 1.2)]; out.append(dp)
    out.append(clip('seat_down', 0.4, [(0, st), (0.25, M(st, {'seat': (96, 0, 0)})), (0.4, M(st, {'seat': (88, 0, 0)}))], hold=True, note='the child seat flips down (an ally can ride: mk_rider); held'))
    out.append(clip('seat_up', 0.4, [(0, M(st, {'seat': (88, 0, 0)})), (0.25, M(st, {'seat': (-6, 0, 0)})), (0.4, st)], hold=True, note='the child seat folds back up; held'))
    # CLEAN UP AISLE 5: a squat, the nose down, the boosters roaring, the flag flat out, the wheels a blur
    keys = []
    for k in range(5):
        t = k / 4 * 0.4
        keys.append((t, M(ch((-4 + 0.8 * math.sin(math.pi * k), 0, 0.6 * math.sin(math.pi * k)), (0, -0.05, 0)), spin(-180 * k, 20 * math.sin(math.pi * k)), {'flag': (-70, 0, 4 * math.sin(math.pi * k)), 'basket': (-4, 0, 0)})))
    bo = clip('boost', 0.4, keys, loop=True, note='CLEAN UP AISLE 5: two wheel turns a loop, boosters on (the game lights the flames)')
    bo['linear'] = True; bo['events'] = [ev_(0.0, 'burst', 'mk_thrust_L', 0.1), ev_(0.0, 'burst', 'mk_thrust_R')]; out.append(bo)
    # jump / land / hit
    crouch = M(st, ch((2, 0, 0), (0, -0.12, 0))); hop = M(st, ch((-8, 0, 0), (0, 0.10, 0)), {'caster_FL': (0, 30, 0), 'caster_BR': (0, -20, 0), 'flag': (30, 0, 0)})
    jp = clip('jump', 0.5, [(0, st), (0.12, crouch), (0.22, hop), (0.5, M(hop, {'caster_FR': (0, -25, 0), 'caster_BL': (0, 18, 0)}))], hold=True, note='crouch, hop, the casters flop (held in the air)')
    jp['snap'] = (2,); jp['events'] = [ev_(0.22, 'burst', 'mk_thrust_L'), ev_(0.22, 'burst', 'mk_thrust_R')]; out.append(jp)
    ld = clip('land', 0.6, [(0, hop), (0.07, M(st, ch((3, 0, 2), (0, -0.16, 0)), {'basket': (5, 0, 0), 'flag': (-30, 0, 0)})), (0.25, M(st, ch((-1, 0, -1), (0, 0.03, 0)))), (0.6, st)],
              note='a crash-down squash, the basket bounces, settle')
    ld['snap'] = (1,); ld['events'] = [ev_(0.07, 'dust', 'mk_wheel_FL', 0, True), ev_(0.07, 'dust', 'mk_wheel_BR', 0, True)]; out.append(ld)
    hr = clip('hit_react', 0.5, [(0, st), (0.05, M(st, ch((4, -8, 6), (0, 0.04, 0.10)), {'caster_FL': (0, 50, 0), 'basket': (6, 0, 0), 'flag': (20, 0, 20)})), (0.22, M(st, ch((-1, 2, -2)))), (0.5, st)],
              note='knocked sideways; the wonky wheel spins round')
    hr['snap'] = (1,); out.append(hr)
    # MECH DROP: falling (wheels dangling and spinning), the landing, then a cocky wheelie, held
    fa = M(st, spin(-120), {'caster_FL': (0, 40, 0), 'caster_FR': (0, -30, 0), 'caster_BL': (0, 20, 0), 'caster_BR': (0, -45, 0), 'flag': (40, 0, 10), 'basket': (-6, 0, 0)})
    fb = M(fa, spin(-240), {'caster_FL': (0, -20, 0), 'flag': (30, 0, -10)})
    out.append(clip('drop_fall', 0.5, [(0, fa), (0.25, fb)], loop=True, note='the MECH DROP fall (loop): casters flopping, wheels spinning'))
    imp = M(st, ch((0, 0, 0), (0, -0.20, 0)), {'basket': (8, 0, 0), 'flag': (-40, 0, 0), 'caster_FL': (0, 25, 0), 'caster_BR': (0, -15, 0)})
    di = clip('drop_in', 1.3, [(0, fa), (0.30, fa), (0.36, imp), (0.7, M(st, ch((0, 0, 0), (0, -0.04, 0)))), (1.3, st)], hold=True, note='impact at 0.36 s; ends standing')
    di['snap'] = (2,); di['events'] = [ev_(0.36, 'slam', 'chassis', 0.4, True, 1.4)]; out.append(di)
    wheelie = ch((18, 0, 0), (0, 0.47, 0.15))  # (up on the back wheels: rotated about the chassis, lifted so the back wheels stay on the floor)
    coil = M(st, ch((3, 0, 0), (0, -0.10, 0.10)), {'basket': (4, 0, 0)})
    pop = M(st, wheelie, spin(-200, 30), {'basket': (6, 0, 0), 'flag': (-20, 0, 15)})
    sig = M(st, ch((16, 0, 0), (0, 0.42, 0.14)), spin(-360, 22), {'flag': (-10, 0, 10)})
    keys = [(0, imp), (0.18, M(st, ch((0, 0, 0), (0, -0.10, 0)))), (0.42, M(st, {'flag': (-8, 0, 8), 'caster_FL': (0, 20, 0)})), (0.64, st), (0.82, coil), (1.0, pop), (1.2, M(sig, ch((14, 0, 0), (0, 0.37, 0.12)))), (1.7, sig)]
    hi = clip('hero_intro', 1.7, keys, hold=True, note='the MECH DROP landing shot: from the impact, a cocky wheelie by ~1.0 s, the wonky wheel spinning in the air; held')
    hi['snap'] = (5,); hi['events'] = [ev_(0, 'slam', 'chassis', 0.4, True, 1.4), ev_(1.0, 'burst', 'mk_thrust_L', 0.12), ev_(1.0, 'burst', 'mk_thrust_R'), ev_(1.0, 'dust', 'mk_wheel_BL', 0, True), ev_(1.0, 'dust', 'mk_wheel_BR', 0, True), ev_(1.02, 'glint', 'mk_bumper')]
    out.append(hi)
    dip = M(st, ch((-3, 0, 0), (0, -0.08, 0)))
    out.append(clip('pilot_in', 2.6, [(0, st), (0.5, dip), (1.6, dip), (2.0, M(st, ch((2, 0, 0)))), (2.6, st)], note='dips at the back (the pilot hops on the deck 0.5 to 1.6 s), settles'))
    ej = clip('eject', 0.7, [(0, st), (0.06, M(st, ch((8, 0, 0), (0, -0.10, 0)), {'flag': (40, 0, 0)})), (0.25, M(st, ch((-2, 0, 0)))), (0.7, st)], hold=True, note='the deck kicks the pilot off (launch at 0.06 s); held')
    ej['snap'] = (1,); ej['events'] = [ev_(0.06, 'pop', 'mk_eject', 0.2)]; out.append(ej)
    dead = M(st, ch((-6, 10, 14), (0, -0.20, 0)), {'basket': (-30, 0, 10), 'seat': (60, 0, 0), 'flag': (75, 0, 30), 'caster_FL': (0, 80, 0), 'caster_BR': (0, -50, 0),
                                                  'wheel_FL': {'r': (90, 0, 40), 'p': (-0.6, -0.12, -0.4)}})
    ds = clip('destroy', 1.6, [(0, st), (0.12, M(st, ch((6, -8, -8), (0, 0.10, 0)), {'basket': (-12, 0, 0)})), (0.6, dead), (1.6, dead)], hold=True,
              note='hit, the wonky wheel finally comes off, it slumps over, the basket tipped; held')
    ds['snap'] = (1,); ds['events'] = [ev_(0.12, 'pop', 'mk_eject', 0.3), ev_(0.6, 'spark', 'mk_wheel_FL'), ev_(0.6, 'dust', 'chassis', 0, True, 1.2)]; out.append(ds)
    for cl in out: cl['air'] = 'all'  # (wheels, no legs: the chassis moves on purpose, nothing to solve)
    return out
