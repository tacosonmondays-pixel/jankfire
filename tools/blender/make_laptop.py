# The Laptop (item): a 14 inch office laptop at life size (320 x 220 mm deck, 12 mm thick; 208 mm lid), held BACKWARDS:
# the hinge is at your end (z = 0), the deck sticks out forward like a tray and the screen faces whoever you point it at.
# You get the back of the lid, so that is where the fun goes: an AD SUPPORTED sticker, an IT asset tag, a round
# "I <heart> POP-UPS" badge. The screen is a desktop buried in pop-ups (it glows). Keyboard: 5 rows of chiclet keys with a
# few wrong-coloured ones and a space bar, a trackpad with a sticky note next to it (PASSWORD: PASSWORD), ports on both
# sides, a webcam with its light on, rubber feet, a brass hinge barrel.
# The lid is its own node (`lid_wzB`, origin on the hinge) leaning 15 degrees back at you, so the game could shut it.
# run: blender -b --python tools/blender/make_laptop.py      (or: /opt/bpy52/bin/python tools/blender/make_laptop.py)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

def M_(v): return v / 1000  # millimetres -> game metres (life size)
W, D, T = 320, 220, 12      # deck: width (x), depth (forward, -z), thickness (y)
LID_H, LID_T = 208, 7
OPEN = 0.26                 # how far past upright the lid leans back at you (rad)
FONT.setdefault('%', ['11000', '11001', '00010', '00100', '01000', '10011', '00011'])
FONT.setdefault('$', ['00100', '01111', '10100', '01110', '00101', '11110', '00100'])


def quad(corners, m, name='decal'):
    """a flat sticker through 4 game points (mm), given bottom-left, bottom-right, top-right, top-left as you read it:
    it faces you when those go anticlockwise. UVs are the whole texture"""
    bm = bmesh.new()
    vs = [bm.verts.new(gv(*[M_(c) for c in p])) for p in corners]
    f = bm.faces.new(vs)
    uvl = bm.loops.layers.uv.new('UVMap')  # the same layer name cube_project gives the other parts, or the join drops these
    for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
    o = bpy.data.objects.new(name, bpy.data.meshes.new(name)); bm.to_mesh(o.data); bm.free()
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(m)
    return o


def build():
    shell = mat('lp_shell', 0xc4c8d2, rough=0.22, metal=0.55, clearcoat=0.8, tex=tex_noise('lp_shell_t', 0xc4c8d2, var=0.05, size=16, seed=611))
    dark = mat('lp_dark', 0x18181e, rough=0.4, clearcoat=0.4)
    key = mat('lp_key', 0x2a2a34, rough=0.45, clearcoat=0.3, tex=tex_noise('lp_key_t', 0x2a2a34, var=0.1, size=8, seed=612))
    keyp = mat('lp_keyp', 0xff4fd8, rough=0.3, clearcoat=0.7)
    keyy = mat('lp_keyy', 0xffe14d, rough=0.3, clearcoat=0.7)
    pad = mat('lp_pad', 0xa9adb9, rough=0.18, metal=0.4, clearcoat=0.9)
    brass = mat('lp_brass', 0xc9a24a, rough=0.2, metal=1.0)
    chrome = mat('lp_chrome', 0xd0d4dc, rough=0.14, metal=1.0)
    rubber = mat('lp_rubber', 0x141416, rough=0.85)
    led = mat('lp_led', 0x39ff14, rough=0.2, emit=0x39ff14, strength=4.0)

    def desktop(px):  # the screen: 4 pop-ups on a purple desktop, a taskbar
        h, w = px.shape[:2]
        px[:] = hexrgb(0x2a1238)
        px[h - 8:] = hexrgb(0x12081a); px[h - 7:h - 2, 2:14] = hexrgb(0x39ff14)
        def win(x, y, ww, hh, bar, lines, btn):
            px[y + 3:y + hh + 3, x + 3:x + ww + 3] = hexrgb(0x4fd8ff)       # hard offset shadow
            px[y:y + hh, x:x + ww] = hexrgb(0xff4fd8)                          # pink border
            px[y + 2:y + hh - 2, x + 2:x + ww - 2] = hexrgb(0x12081a)
            px[y + 2:y + 12, x + 2:x + ww - 2] = hexrgb(bar)
            px[y + 3:y + 11, x + ww - 11:x + ww - 3] = hexrgb(0xff3030)
            text_px(px, 'X', x + ww - 9, y + 4, 1, 0xffffff)
            text_px(px, lines[0], x + 5, y + 4, 1, 0x000000)
            for i, ln in enumerate(lines[1:]): text_px(px, ln, x + 6, y + 17 + i * 10, 1, 0xffffff)
            bw = len(btn) * 6 + 6
            px[y + hh - 15:y + hh - 5, x + 6:x + 6 + bw] = hexrgb(0xffe14d)
            text_px(px, btn, x + 9, y + hh - 13, 1, 0x000000)
        win(8, 6, 104, 52, 0x4fd8ff, ['YOU WON A BOAT', 'SHIPPING IS', '$400'], 'PAY')
        win(120, 14, 96, 50, 0xffe14d, ['FREE AIMBOT', 'IT IS A DUCK'], 'DUCK')
        win(62, 62, 110, 52, 0x39ff14, ['HOT SINGLE BOTS', 'BEHIND YOU'], 'TURN AROUND')
        win(178, 74, 60, 40, 0xff4fd8, ['BREAD', 'BUY'], 'OK')
    screen = mat('lp_screen', 0xffffff, rough=0.75, emit=0xffffff, strength=1.0, tex=tex_canvas('lp_screen_t', 232, 140, desktop), emit_tex=True)

    def sticker(px):
        px[:] = hexrgb(0xffe14d); px[:2] = px[-2:] = hexrgb(0x000000); px[:, :2] = px[:, -2:] = hexrgb(0x000000)
        text_px(px, 'AD SUPPORTED', 6, 6, 2, 0x000000)
    stick_m = mat('lp_sticker', 0xffffff, rough=0.35, clearcoat=0.6, tex=tex_canvas('lp_sticker_t', 154, 26, sticker))
    def asset(px):
        px[:] = hexrgb(0x4fd8ff); px[:1] = px[-1:] = hexrgb(0x000000)
        text_px(px, 'PROPERTY OF IT', 3, 2, 1, 0x000000); text_px(px, 'ASSET 404', 3, 11, 1, 0x000000)
        for x in range(60, 86, 2): px[11:18, x:x + 1] = hexrgb(0x000000)  # a barcode
    asset_m = mat('lp_asset', 0xffffff, rough=0.4, tex=tex_canvas('lp_asset_t', 90, 20, asset))
    def badge(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0xc4c8d2)
        px_disc(px, w / 2, h / 2, w / 2 - 1, 0x000000); px_disc(px, w / 2, h / 2, w / 2 - 3, 0xff4fd8)
        text_px(px, 'I < ', 14, 9, 1, 0xffffff); text_px(px, 'POP-UPS', 3, 19, 1, 0xffffff)
    badge_m = mat('lp_badge', 0xffffff, rough=0.3, clearcoat=0.7, tex=tex_canvas('lp_badge_t', 46, 46, badge))
    def note(px):
        px[:] = hexrgb(0xffe14d); px[:5] = hexrgb(0xe6c93a)
        text_px(px, 'PASSWORD:', 3, 9, 1, 0x1a1a1a); text_px(px, 'PASSWORD', 3, 20, 1, 0xc02030)
    note_m = mat('lp_note', 0xffffff, rough=0.7, tex=tex_canvas('lp_note_t', 60, 36, note))

    parts, lid = [], []
    A, L = parts.append, lid.append
    # (anything laid on a surface is a part 0.7 mm proud or a decal 0.45 mm off: the asset QA calls under 0.2 mm z-fighting and a decal over 0.6 mm floating)
    # ---------------- deck: a slab with a chamfered front lip, the keyboard well sunk into it
    A(box((M_(W), M_(T), M_(D)), (0, M_(T / 2), M_(-D / 2)), shell, bev=M_(3), seg=3))
    A(box((M_(280), M_(1.2), M_(104)), (0, M_(T + 0.2), M_(-72)), dark))
    kw, kd, gap = 20.5, 16.5, 2.4
    odd = {(1, 3): keyp, (3, 9): keyy, (0, 11): keyp, (2, 6): keyy}
    for r in range(4):
        n = 12
        for c in range(n):
            x = (c - (n - 1) / 2) * (kw + gap) + (r % 2) * 3 - 1.5
            A(box((M_(kw), M_(2.2), M_(kd)), (M_(x), M_(T + 1.6), M_(-30 - r * (kd + gap))), odd.get((r, c), key), bev=M_(0.5), seg=1))
    for x, wdt, m in ((-108, 52, key), (0, 150, key), (108, 52, key)):  # bottom row: ctrl-ish, the space bar, arrows-ish
        A(box((M_(wdt), M_(2.2), M_(kd)), (M_(x), M_(T + 1.6), M_(-30 - 4 * (kd + gap))), m, bev=M_(0.5), seg=1))
    A(box((M_(104), M_(0.9), M_(62)), (0, M_(T + 0.25), M_(-172)), pad, bev=M_(0.4), seg=1))                 # trackpad
    A(box((M_(1), M_(2), M_(62)), (0, M_(T + 0.35), M_(-172)), dark))                                        # its click line
    nt = quad([(-134, T + 0.45, -146), (-86, T + 0.45, -150), (-84, T + 0.45, -196), (-132, T + 0.45, -192)][::-1], note_m, 'note'); A(nt)  # sticky note on the palm rest (reads from the screen side)
    for sx in (-1, 1):  # ports: two slots and a jack per side
        for z in (-40, -62): A(box((M_(1.8), M_(4.4), M_(13)), (sx * M_(W / 2), M_(T / 2), M_(z)), dark))
        A(cyl(M_(2.6), M_(2), (sx * M_(W / 2), M_(T / 2), M_(-84)), chrome, axis='x', seg=10))
        for z in (-22, -198): A(cyl(M_(7), M_(1.6), (sx * M_(128), M_(-0.6), M_(z)), rubber, axis='y', seg=10))  # feet
    A(cyl(M_(1.6), M_(1.6), (M_(-146), M_(T + 0.4), M_(-204)), led, axis='y', seg=8))                           # power light
    # ---------------- hinge: a brass barrel between two shell knuckles
    A(cyl(M_(6.2), M_(196), (0, M_(T + 1), M_(-1)), brass, axis='x', seg=14, bev=M_(1)))
    for sx in (-1, 1): A(cyl(M_(6.8), M_(34), (sx * M_(120), M_(T + 1), M_(-1)), shell, axis='x', seg=14, bev=M_(1)))
    # ---------------- lid (built upright on the hinge line, leant back as one node)
    y0 = T + 1
    L(box((M_(W), M_(LID_H), M_(LID_T)), (0, M_(y0 + LID_H / 2), 0), shell, bev=M_(3), seg=3))
    L(box((M_(306), M_(192), M_(1)), (0, M_(y0 + LID_H / 2 + 2), M_(-LID_T / 2 - 0.2)), dark))                # bezel, on the side facing them
    sy0, sy1 = y0 + 20, y0 + 196
    scr = quad([(146, sy0, -LID_T / 2 - 1.15), (-146, sy0, -LID_T / 2 - 1.15), (-146, sy1, -LID_T / 2 - 1.15), (146, sy1, -LID_T / 2 - 1.15)], screen, 'screen'); L(scr)
    L(cyl(M_(2.4), M_(1.6), (0, M_(y0 + 201.5), M_(-LID_T / 2 - 0.9)), chrome, axis='z', seg=10))               # webcam
    L(cyl(M_(1.1), M_(1.8), (M_(8), M_(y0 + 201.5), M_(-LID_T / 2 - 0.9)), led, axis='z', seg=8))             # its light: on. always on
    zb = LID_T / 2 + 0.45  # the back of the lid (what you look at)
    def tilt(cx, cy, w, h, a):  # a sticker stuck on at an angle
        c, s = math.cos(a), math.sin(a)
        return [(cx + dx * w / 2 * c - dy * h / 2 * s, cy + dx * w / 2 * s + dy * h / 2 * c, zb) for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    L(quad(tilt(-10, y0 + 112, 200, 34, 0.12), stick_m, 'sticker'))
    L(quad(tilt(-92, y0 + 34, 92, 20, -0.04), asset_m, 'asset'))
    L(quad(tilt(104, y0 + 46, 54, 54, 0.2), badge_m, 'badge'))

    flat = {'note', 'screen', 'sticker', 'asset', 'badge'}
    for p in parts + lid:
        apply_mods(p)
        if p.name.split('.')[0] not in flat: uv_box(p, 0.03)
    WZ = {'lp_shell': 'a', 'lp_pad': 'a', 'lp_dark': 'b', 'lp_key': 'b', 'lp_brass': 'b', 'lp_chrome': 'b', 'lp_rubber': 'b'}  # shell + trackpad = A, keys + metal = B; the screen, stickers, odd keys and lights keep their look
    deck = zone_join(parts, 'lp_deck', WZ, default='n')
    lnode = part(lid, 'lid_wzB', pivot=(0, M_(y0), 0))
    lnode.rotation_euler.x = OPEN
    top = M_(y0) + M_(LID_H) * math.cos(OPEN)
    meta = {'kind': 'weapon', 'id': 'laptop', 'paint': ['lp_sticker'], 'muzzle': [0, 0.12, -0.06], 'hatAt': [[0, top + 0.004, M_(LID_H) * math.sin(OPEN)], 0.08]}
    return finish('w_laptop', deck + [lnode], meta)


main(build, 'w_laptop')
