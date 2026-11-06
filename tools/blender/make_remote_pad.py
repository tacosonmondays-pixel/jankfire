# Game Pad (TV Remote skin): an original chunky wired game controller, ~x1.35 a real pad (a 200 mm body with two
# drooping handles), held by its right handle where the remote is held and pointed like a remote. Our own layout:
# a chunky plus pad on the left, two sticks, a glowing CORP home button, and on the right the remote's two moves as
# the big face buttons (a blue II PAUSE and a pink << REWIND) with a yellow smiley and a green ? key; bumpers and
# triggers on the front edge, a 4-dot player light. The cable comes out of the front and has been cut ("now
# wireless"): its frayed copper end is the muzzle at the remote's (0, 0, -0.18) and the IR node the game flashes.
# Node: ir_wzN (the frayed end: one mesh, one material, the game swaps it blue / pink when you click).
# run: blender -b --python tools/blender/make_remote_pad.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sidekit import rrect, plate_xz, quad, uv_face, smiley, text_c, one_mat, bake_normals

PX, PZ = -0.06, -0.04   # pad centre (its right handle lands in your hand at x ~0)
TOPY = 0.012            # top of the face
HX = 0.062              # handles at PX +- HX


def L(x, y, z): return (PX + x, y, PZ + z)  # pad-local -> game


def handle_ring(i, t):  # a handle's cross-section: rounder and fatter toward the end
    r = 0.0175 + 0.0035 * math.sin(math.pi * min(1, t * 1.2))
    return [(r * 0.85 * math.sin(2 * math.pi * k / 18), r * math.cos(2 * math.pi * k / 18)) for k in range(18)]


def build():
    body_m = mat('gp_body', 0xffffff, rough=0.22, clearcoat=1.0, tex=tex_noise('gp_body_t', 0x8a5cff, var=0.04, size=16, seed=401))
    grip_m = mat('gp_grip', 0xffffff, rough=0.6, clearcoat=0.2, tex=tex_noise('gp_grip_t', 0x5ff2c2, var=0.08, size=16, speck=0x3fd2a2, speck_p=0.25, seed=402))
    face_m = mat('gp_face', 0x2a2236, rough=0.35, clearcoat=0.4)
    dark = mat('gp_dark', 0x141118, rough=0.45)
    stick_m = mat('gp_stick', 0xffffff, rough=0.7, tex=tex_noise('gp_stick_t', 0x3a3442, var=0.12, size=16, seed=403))
    cable_m = mat('gp_cable', 0x1c1a20, rough=0.5, clearcoat=0.3)
    ir_m = mat('gp_ir', 0xff3030, rough=0.2, emit=0xff3030, strength=3.0)
    led_m = mat('gp_led', 0x39ff14, rough=0.3, emit=0x39ff14, strength=3.0)
    ledoff = mat('gp_ledoff', 0x1a3a1a, rough=0.3)
    def key(sym, bg, ink):
        def d(px):
            px[:] = hexrgb(bg)
            if sym == 'II': px[4:12, 4:6] = px[4:12, 10:12] = hexrgb(ink)
            elif sym == '<<':
                for k in range(5): px[8 - k:8 + k + 1, 3 + k] = hexrgb(ink); px[8 - k:8 + k + 1, 9 + k] = hexrgb(ink)
            elif sym == ':)': smiley(px, 8, 8, 5.6, face=bg, ink=ink, ring=ink)
            else: text_px(px, sym, 6, 4, 1, ink)
        return d
    keys = [('II', 0x2e7bff, 0xffffff, (0, -0.017)), ('<<', 0xff5a8a, 0xffffff, (0, 0.017)), (':)', 0xffe14d, 0x2a2236, (-0.017, 0)), ('?', 0x39ff14, 0x2a2236, (0.017, 0))]
    km = [mat(f'gp_key{i}', 0xffffff, rough=0.25, clearcoat=0.9, tex=tex_canvas(f'gp_key{i}_t', 16, 16, key(s, b, k))) for i, (s, b, k, _) in enumerate(keys)]
    def home_draw(px):
        px[:] = hexrgb(0xff4fd8); smiley(px, 8, 8, 6.6, face=0xffe14d)
    home = mat('gp_home', 0xffffff, rough=0.2, emit=0xff4fd8, strength=0.6, tex=tex_canvas('gp_home_t', 16, 16, home_draw), emit_tex=True)
    def logo_draw(px):
        px[:] = hexrgb(0x2a2236); text_c(px, 'CORP', 20, 1, 1, 0xffe14d)
    logo = mat('gp_logo', 0xffffff, rough=0.35, tex=tex_canvas('gp_logo_t', 40, 9, logo_draw))
    def stk_draw(px):
        px[:] = hexrgb(0xffffff); px[1:-1, 1:-1] = hexrgb(0xff4fd8)
        text_c(px, 'NOW', 24, 3, 1, 0xffffff); text_c(px, 'WIRELESS', 24, 12, 1, 0xffe14d)
    stk = mat('gp_sticker', 0xffffff, rough=0.4, tex=tex_canvas('gp_sticker_t', 48, 22, stk_draw))
    parts, decals, irp = [], [], []
    A = parts.append

    # ---------------- the body: a fat rounded slab, a dark face inset, two handles drooping back and down
    A(plate_xz(rrect(PX, PZ, 0.168, 0.082, 0.03, 6), -0.016, 0.026, body_m, name='shell', bev=0.009, seg=4))
    A(plate_xz(rrect(PX, PZ - 0.002, 0.128, 0.056, 0.02, 5), TOPY - 0.004, 0.0052, face_m, name='face', bev=0.0015, seg=2))
    for sx in (-1, 1):
        cen = [Vector(L(sx * (HX + 0.004 * t), -0.004 - 0.024 * t * t, 0.006 + 0.06 * t)) for t in [i / 7 for i in range(8)]]
        A(loft(cen, handle_ring, grip_m, name='handle', close=(False, True), smooth_angle=70))
    # ---------------- top: plus pad, two sticks, home, small keys, the four face buttons
    for w, d in ((0.03, 0.0095), (0.0095, 0.03)):
        A(plate_xz(rrect(PX - 0.045, PZ - 0.004, w, d, 0.0018, 2), TOPY + 0.001, 0.004, dark, name='dpad', ch=0.0008))
    A(cyl(0.004, 0.001, L(-0.045, TOPY + 0.0055, -0.004), face_m, axis='y', seg=10, name='dpaddot'))
    for x in (-0.026, 0.026):
        A(cyl(0.0105, 0.004, L(x, TOPY + 0.002, 0.017), dark, axis='y', seg=18, name='stickwell'))
        A(cyl(0.0038, 0.009, L(x, TOPY + 0.007, 0.017), dark, axis='y', seg=10, name='stem'))
        A(lathe([(0.0, 0.006), (0.0075, 0.0058), (0.0098, 0.0035), (0.0098, 0.0), (0.006, -0.0015), (0.0, -0.0015)], L(x, TOPY + 0.011, 0.017), stick_m, seg=18, axis='y', name='stickcap'))
    hb = cyl(0.0068, 0.003, L(0, TOPY + 0.0025, -0.012), home, axis='y', seg=16, bev=0.001, name='homebtn'); A(hb)
    for x in (-0.012, 0.012): A(plate_xz(rrect(PX + x, PZ + 0.001, 0.009, 0.0045, 0.002, 2), TOPY + 0.001, 0.003, dark, name='smallkey'))
    kb = []
    for i, (s, b, k, (dx, dz)) in enumerate(keys):
        o = cyl(0.0068, 0.005, L(0.045 + dx, TOPY + 0.0025, -0.004 + dz), km[i], axis='y', seg=16, bev=0.0012, name='facekey'); kb.append((o, L(0.045 + dx, TOPY + 0.005, -0.004 + dz))); A(o)
    decals.append(quad(L(0, TOPY + 0.0014, -0.026), 0.024, 0.0054, logo, axis='y', name='logo'))
    decals.append(quad(L(-HX - 0.002, 0.0118, 0.034), 0.022, 0.01, stk, axis='y', name='sticker'))
    # ---------------- front edge: bumpers + triggers, player lights, the cable's strain relief
    for sx in (-1, 1):
        A(plate_xz(rrect(PX + sx * 0.05, PZ - 0.044, 0.042, 0.012, 0.005, 3), 0.002, 0.009, dark, name='bumper', bev=0.002))
        A(side([(PZ - 0.035, -0.012), (PZ - 0.048, -0.008), (PZ - 0.052, -0.016), (PZ - 0.044, -0.026), (PZ - 0.032, -0.022)], 0.028, (PX + sx * 0.05, 0, 0), face_m, bev=0.003, name='trigger'))
    for k in range(4):
        A(box((0.004, 0.0022, 0.003), L(-0.009 + k * 0.006, TOPY - 0.0005, -0.0405), led_m if k == 0 else ledoff, name='plight'))
    A(lathe([(0.0068, -0.0), (0.0068, -0.006), (0.0055, -0.012), (0.0045, -0.018)], (PX, -0.002, PZ - 0.04), dark, seg=14, name='relief'))
    # the cable: out of the front, a lazy curve over to the muzzle, cut, the copper fraying out
    cab = [(PX, -0.002, PZ - 0.058), (PX + 0.004, -0.004, -0.115), (PX + 0.022, -0.006, -0.145), (-0.012, -0.003, -0.165), (-0.002, -0.001, -0.172)]
    A(sweep(cab, 0.0036, cable_m, seg=10, name='cable'))
    A(cyl(0.0039, 0.002, (-0.0015, -0.001, -0.1735), mat('gp_cut', 0x5a5560, rough=0.6), axis='z', seg=10, rot=(0, 0.15, 0), name='cutend'))
    rng = random.Random(9)
    for k in range(9):  # frayed copper strands (the IR node: glows, flashes)
        a = 2 * math.pi * k / 9
        p0 = (-0.0015 + math.cos(a) * 0.0018, -0.001 + math.sin(a) * 0.0018, -0.1745)
        p1 = (p0[0] + math.cos(a) * rng.uniform(0.002, 0.005), p0[1] + math.sin(a) * rng.uniform(0.002, 0.005), -0.18 + rng.uniform(0, 0.003))
        irp.append(rod(p0, p1, 0.0006, ir_m, seg=4, name='strand'))
    irp.append(ball(0.0022, (-0.0015, -0.001, -0.1775), ir_m, seg=8, rings=5, name='spark'))

    for p in parts + irp: apply_mods(p)
    one_mat(parts + irp)
    for p in parts + irp:
        if not p.data.materials[0].name.startswith('gp_key') and p is not hb: uv_box(p, 0.03)
    for o, c in kb: uv_face(o, 'y', c, 0.0136)
    uv_face(hb, 'y', L(0, TOPY + 0.004, -0.012), 0.0136)
    bake_normals(parts + irp)
    WZ = {'gp_body': 'a', 'gp_grip': 'a', 'gp_face': 'b', 'gp_dark': 'b', 'gp_stick': 'b', 'gp_cable': 'b'}
    bodies = zone_join(parts, 'gp_body', WZ, default='n')
    dn = join(decals, 'gp_decals_wzN')
    inode = part(irp, 'ir_wzN', pivot=(0, 0, -0.176))
    meta = {'kind': 'weapon', 'id': 'remote', 'skin': 'remote_pad', 'paint': ['gp_body'], 'muzzle': [0, 0, -0.18],
            'hatAt': [[PX, round(TOPY + 0.002, 4), PZ + 0.004], 0.05]}
    return finish('w_remote_pad', bodies + [dn, inode], meta)


main(build, 'w_remote_pad')
