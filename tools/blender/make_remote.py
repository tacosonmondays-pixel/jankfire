# TV Remote: a fat CRT-era television remote at real size (210 x 50 x 26 mm: game metres = real ones, the code model
# is already life size). Charcoal shell with a satin grey face plate, rubber keys: a red power key, a 3 x 4 number pad
# with printed digits, CH / VOL rockers round an OK key, the four coloured teletext keys, then the two big ones the
# weapon fires: a blue PAUSE key with a raised II and a pink REWIND key with a raised <<. Grip ribs, rubber side
# grips, a sloped nose with a dark red IR window, and the IR LED poking through it (its own node, ir_wzN: the game
# flashes it blue / pink when you click). The battery door underneath says BATTERIES NOT INCLUDED (they never are).
# No sights: it's held like a pointer. run: blender -b --python tools/blender/make_remote.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

def M_(v): return v / 1000  # millimetres -> game metres (life size)
def pz(pts): return [(M_(z), M_(y)) for z, y in pts]
PLATE_Y = 13.5          # top of the face plate
PX = 1.2                # face plate print: pixels per mm
PLATE = (-18.5, 18.5, -150, 12)  # x0, x1, z0, z1 of the face plate


def plate_xz(pts, y0, thick, m, name='plate', bev=0.0):
    """a top-view outline [(x, z)] (game mm) extruded up from y0 by thick: keys, symbols, panels."""
    bm = bmesh.new()
    vs = [bm.verts.new(gv(M_(x), M_(y0), M_(z))) for x, z in pts]
    f = bm.faces.new(vs)
    bm.normal_update()
    if f.normal.z < 0: f.normal_flip()
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, vec=Vector((0, 0, M_(thick))), verts=[e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = bpy.data.objects.new(name, bpy.data.meshes.new(name)); bm.to_mesh(o.data); bm.free()
    bpy.context.scene.collection.objects.link(o)
    if m is not None: o.data.materials.append(m)
    smooth(o, 40); bevel(o, M_(bev), 2)
    return o


def key_xz(pts, y0, thick, ch, m, name='key'):
    """a rubber key: outline [(x, z)] extruded up from y0, its top edge chamfered by ch (no hidden bottom bevel, cheap)"""
    bm = bmesh.new()
    vs = [bm.verts.new(gv(M_(x), M_(y0), M_(z))) for x, z in pts]
    f = bm.faces.new(vs)
    bm.normal_update()
    if f.normal.z < 0: f.normal_flip()
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    top = [e for e in r['geom'] if isinstance(e, bmesh.types.BMFace)]
    bmesh.ops.translate(bm, vec=Vector((0, 0, M_(thick - ch))), verts=[e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)])
    bmesh.ops.inset_region(bm, faces=top, thickness=M_(ch), depth=M_(ch))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = bpy.data.objects.new(name, bpy.data.meshes.new(name)); bm.to_mesh(o.data); bm.free()
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(m)
    smooth(o, 40)
    return o


def rrect(cx, cz, w, d, r, n=3):
    """a rounded rectangle outline in (x, z), counter-clockwise seen from above"""
    out = []
    for ax, az, a0 in ((cx + w / 2 - r, cz + d / 2 - r, 90), (cx + w / 2 - r, cz - d / 2 + r, 0), (cx - w / 2 + r, cz - d / 2 + r, -90), (cx - w / 2 + r, cz + d / 2 - r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 - 90 * i / n)
            out.append((ax + math.cos(a) * r, az + math.sin(a) * r))
    return out


def uv_top(o, cx, cz, sx, sz, rect, plain):
    """keys + plates: faces looking up get a straight top-down map into rect (u0, v0, u1, v1) of the texture, image up =
    the remote's nose (-z); every other face gets a box map squeezed into the plain rect (no squashed zero-area UVs)."""
    bpy.context.view_layer.update()
    me = o.data
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data
    mw = o.matrix_world
    pts = [mw @ v.co for v in me.vertices]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    span = hi - lo
    for pg in me.polygons:
        n = mw.to_3x3() @ pg.normal
        top = n.z > 0.6
        ax = max(range(3), key=lambda i: abs(n[i]))
        a, b = [(1, 2), (0, 2), (0, 1)][ax]
        for li in pg.loop_indices:
            v = mw @ me.vertices[me.loops[li].vertex_index].co
            if top:
                u, w = (v.x - M_(cx)) / M_(sx) + 0.5, (v.y - (-M_(cz))) / M_(sz) + 0.5  # blender y = -game z: up the image = nose
                uv[li].uv = (rect[0] + u * (rect[2] - rect[0]), rect[1] + w * (rect[3] - rect[1]))
            else:
                u = (v[a] - lo[a]) / max(span[a], 1e-6); w = (v[b] - lo[b]) / max(span[b], 1e-6)
                uv[li].uv = (plain[0] + u * (plain[2] - plain[0]), plain[1] + w * (plain[3] - plain[1]))


# number-pad atlas: 6 x 2 cells of 14 x 11 px, white glyphs on grey rubber, a plain strip on the right
KEYS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '-', '0', 'AV']
CW, CH_, AW, AH = 14, 11, 90, 22
def keys_draw(px):
    px[:] = hexrgb(0x5e5e68)
    for i, k in enumerate(KEYS):
        c, r = i % 6, i // 6
        text_px(px, k, c * CW + (CW - (len(k) * 6 - 1)) // 2, r * CH_ + 2, 1, 0xf4f4f4)
def cell(i):  # (u0, v0, u1, v1) of key i in the atlas (v up from the bottom row of pixels)
    c, r = i % 6, i // 6
    return (c * CW / AW, 1 - (r + 1) * CH_ / AH, (c + 1) * CW / AW, 1 - r * CH_ / AH)
KEY_PLAIN = (85 / AW, 0.1, 89 / AW, 0.9)


def plate_draw(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0x80868f)
    def at(x, z): return int(round((x - PLATE[0]) * PX)), int(round((z - PLATE[2]) * PX))
    for txt, x, z in (('CH', -10.5, -55), ('VOL', 9.5, -55)):
        c, r = at(x, z); text_px(px, txt, c - (len(txt) * 6 - 1) // 2, r - 3, 1, 0x1c1c22)
    c, r = at(0, -10); text_px(px, 'CLICKER', c - 20, r - 3, 1, 0xff4fd8)
    c, r = at(-11, -147); text_px(px, 'TV', c - 5, r - 3, 1, 0x1c1c22)


def build():
    shell = mat('rm_shell', 0x232328, rough=0.42, clearcoat=0.25, tex=tex_noise('rm_shell_t', 0x232328, var=0.1, size=16, seed=401))
    pw, ph = int((PLATE[1] - PLATE[0]) * PX), int((PLATE[3] - PLATE[2]) * PX)
    plate_m = mat('rm_plate', 0xffffff, rough=0.4, clearcoat=0.3, tex=tex_canvas('rm_plate_t', pw, ph, plate_draw))
    keys_m = mat('rm_keys', 0xffffff, rough=0.65, tex=tex_canvas('rm_keys_t', AW, AH, keys_draw))
    rubber = mat('rm_rubber', 0x5e5e68, rough=0.65)
    grip_m = mat('rm_grip', 0x1c1c22, rough=0.8, tex=tex_noise('rm_grip_t', 0x1e1e24, var=0.25, size=16, speck=0x3a3a44, speck_p=0.3, seed=402))
    def pwr(px):
        px[:] = hexrgb(0xe0201c)
        px_disc(px, 8, 8, 5.2, 0xffffff, r_in=3.6, a0=0.6, a1=5.68 - 0.0)
        px[2:9, 7:9] = hexrgb(0xffffff)
    power_m = mat('rm_power', 0xffffff, rough=0.5, clearcoat=0.4, tex=tex_canvas('rm_power_t', 16, 16, pwr))
    pause_m = mat('rm_pause', 0x2e7bff, rough=0.35, clearcoat=0.8)
    rew_m = mat('rm_rewind', 0xff5a8a, rough=0.35, clearcoat=0.8)
    white = mat('rm_white', 0xf8f8f8, rough=0.35)
    window = mat('rm_window', 0x3a0808, rough=0.08, clearcoat=1.0)
    ir_m = mat('rm_ir', 0xff3030, rough=0.2, emit=0xff3030, strength=3.0)
    door = mat('rm_door', 0x232329, rough=0.4, tex=tex_noise('rm_door_t', 0x24242a, var=0.08, size=16, seed=403))
    tele = [mat('rm_tele' + c, h, rough=0.4, clearcoat=0.6) for c, h in (('r', 0xe8281e), ('g', 0x2ac84a), ('y', 0xffd21a), ('b', 0x2e7bff))]
    def stk(px):
        px[:] = hexrgb(0xf4f0e0); px[:1] = px[-1:] = hexrgb(0xff4fd8)
        text_px(px, 'BATTERIES', 2, 2, 1, 0x1c1c22); text_px(px, 'NOT', 20, 11, 1, 0xd01c1c); text_px(px, 'INCLUDED', 5, 20, 1, 0x1c1c22)
    sticker = mat('rm_sticker', 0xffffff, rough=0.5, tex=tex_canvas('rm_sticker_t', 58, 29, stk))
    parts, ir_parts, decals = [], [], []
    A = parts.append

    # ---------------- shell: a sloped nose, flat deck, battery hump underneath at the back
    A(side(pz([(-173.5, 4), (-165, 9.5), (-152, 12), (30, 12), (36, 9), (38, 2), (37, -9), (33, -16), (24, -19.5), (-28, -19.5), (-42, -14.5), (-166, -14.5), (-173, -11)]),
           M_(50), (0, 0, 0), shell, bev=M_(5.5), seg=3))  # (a 7 mm bevel would eat the 15 mm nose face whole)
    for k in range(3):  # grip ribs across the back of the deck
        A(box((M_(28), M_(2.4), M_(2.6)), (0, M_(12.6), M_(15 + k * 5)), shell, bev=M_(0.8)))
    for sx in (-1, 1):  # rubber side grips
        A(side(pz([(-40, -8), (28, -8), (31, -5), (31, 2), (28, 4.5), (-40, 4.5), (-43, 2), (-43, -5)]), M_(2), (sx * M_(25.6), 0, 0), grip_m, bev=M_(0.8), seg=2))
    # ---------------- face plate (printed) + keys
    pl = plate_xz(rrect(0, (PLATE[2] + PLATE[3]) / 2, PLATE[1] - PLATE[0], PLATE[3] - PLATE[2], 3), 11, PLATE_Y - 11, plate_m, 'plate', bev=0.6); A(pl)
    keyobjs = []
    pk = key_xz(rrect(11, -140, 11, 11, 5.4, 3), PLATE_Y - 0.5, 3.5, 0.9, power_m, 'power'); A(pk); keyobjs.append((pk, 'power'))
    tv = key_xz(rrect(-11, -140, 10, 7, 2, 2), PLATE_Y - 0.5, 2.5, 0.6, rubber, 'tvkey'); A(tv)
    for i, k in enumerate(KEYS):
        x, z = -12 + (i % 3) * 12, -124 + (i // 3) * 12
        o = key_xz(rrect(x, z, 10, 8, 2, 2), PLATE_Y - 0.5, 3, 0.8, keys_m, 'key' + k); A(o); keyobjs.append((o, i))
    for x in (-12, 12):
        A(key_xz(rrect(x, -70, 9, 22, 3.5, 2), PLATE_Y - 0.5, 3.2, 0.9, rubber, 'rocker'))
    A(key_xz(rrect(0, -70, 10, 10, 4.9, 3), PLATE_Y - 0.5, 3, 0.9, rubber, 'ok'))
    for j, m in enumerate(tele):
        A(key_xz(rrect(-13.5 + j * 9, -45, 7, 5, 1.5, 1), PLATE_Y - 0.5, 2.2, 0.6, m, 'tele'))
    # the two that matter: PAUSE (blue, raised II) and REWIND (pink, raised <<)
    A(key_xz(rrect(-9.5, -27, 17, 18, 3.5, 2), PLATE_Y - 0.5, 4.2, 1.2, pause_m, 'pause'))
    A(key_xz(rrect(9.5, -27, 17, 18, 3.5, 2), PLATE_Y - 0.5, 4.2, 1.2, rew_m, 'rewind'))
    top = PLATE_Y + 3.7
    for x in (-12.2, -6.8):
        A(plate_xz(rrect(x, -27, 3.2, 10, 0.8, 1), top - 0.4, 1.6, white, 'bar'))
    for x in (6.3, 12.7):
        A(plate_xz([(x - 3.6, -27), (x + 2.6, -32.2), (x + 2.6, -21.8)], top - 0.4, 1.6, white, 'tri'))
    # ---------------- the nose: dark red IR window, the LED poking through it
    A(box((M_(36), M_(14.4), M_(3)), (0, M_(-2.8), M_(-173.4)), window, bev=M_(1)))  # 1.4 mm proud of the nose
    ir_parts.append(lathe([(M_(3.0), M_(-170)), (M_(3.0), M_(-176.2)), (M_(2.4), M_(-178.5)), (M_(1.3), M_(-179.6)), (0, M_(-180))], (0, 0, 0), ir_m, seg=14, name='ir'))
    # ---------------- underneath: battery door with a thumb catch + the sticker
    A(plate_xz(rrect(0, -4, 36, 48, 3), -20.6, 1.6, door, 'door', bev=0.5))
    for k in range(3): A(box((M_(14), M_(2), M_(1.6)), (0, M_(-21.4), M_(12 + k * 2.6)), door))  # thumb catch, 1.8 mm proud
    d = bmesh.new()
    vs = [d.verts.new(gv(M_(x), M_(-21.8), M_(z))) for x, z in ((-15, -24), (15, -24), (15, 6), (-15, 6))]
    d.faces.new(vs)  # faces down (-y)
    so = bpy.data.objects.new('sticker', bpy.data.meshes.new('sticker')); d.to_mesh(so.data); d.free()
    bpy.context.scene.collection.objects.link(so); so.data.materials.append(sticker); A(so); decals.append(so)

    for p in parts + ir_parts:
        apply_mods(p)
        if p.name.startswith('key') or p is pl or p is pk: continue
        if p is so: continue
        uv_box(p, 0.03)
    uv_top(pl, 0, (PLATE[2] + PLATE[3]) / 2, PLATE[1] - PLATE[0], PLATE[3] - PLATE[2], (0, 0, 1, 1), (0.0, 0.0, 0.03, 0.03))
    uv_top(pk, 11, -140, 11, 11, (0, 0, 1, 1), (0.0, 0.0, 0.05, 0.05))
    for o, i in keyobjs:
        if i == 'power': continue
        x, z = -12 + (i % 3) * 12, -124 + (i // 3) * 12
        uv_top(o, x, z, 10, 8, cell(i), KEY_PLAIN)
    # the sticker is seen from below: image right = +x when you flip the remote over (nose away from you)
    bpy.context.view_layer.update()
    me = so.data; me.uv_layers.new(); uv = me.uv_layers.active.data
    for pg in me.polygons:
        for li in pg.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = ((M_(15) - v.x) / M_(30), (v.y + M_(6)) / M_(30))  # rolled over: +x is on your left, the nose is up
    WZ = {'rm_shell': 'a', 'rm_grip': 'a', 'rm_door': 'a', 'rm_plate': 'b', 'rm_rubber': 'b', 'rm_keys': 'b', 'rm_window': 'b'}  # wrap zones: shell = A, face plate + rubber keys = B, the coloured keys / symbols / stickers keep their look
    bodies = zone_join(parts, 'rm_body', WZ, default='n')
    inode = part(ir_parts, 'ir_wzN', pivot=(0, 0, M_(-176)))
    meta = {'kind': 'weapon', 'id': 'remote', 'paint': ['rm_rewind'], 'muzzle': [0, 0, -0.18], 'hatAt': [[0, M_(PLATE_Y), M_(-62)], 0.05]}
    return finish('w_remote', bodies + [inode], meta)


main(build, 'w_remote')
