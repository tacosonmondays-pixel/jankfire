# Speed Trap radar gun: a hand-held police traffic radar (~28 cm, the "hair dryer" kind): a flared antenna horn with a
# rubber bumper and a flat radome up front, a gunmetal body with a police-blue stripe, a pistol grip with a lock
# trigger, and the readout hump on the back with a short sun visor. Game metres = real ones (the code model is life
# size). The readout face is a dark 2 mm recess facing you: the game draws its live red LED km/h display there (root
# metadata `screen` = [x, y, z, w, h]). Made fun: the stripe says SPEED TRAP, the bezel asks HOW FAST, there's a tiny
# police beacon on top (lamp_wzN, the game blinks it; a dull red dome under it shows when it's off) and a coiled cord
# down to a car lighter plug. Held in your LEFT hand in first person.
# run: blender -b --python tools/blender/make_radar.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

def M_(v): return v / 1000  # millimetres -> game metres (life size)
def pz(pts): return [(M_(z), M_(y)) for z, y in pts]
AX_Y = 30                   # antenna axis height (= the muzzle's)
FACE_Z = 46                 # the readout face (back of the hump)
SCR = (0, 64, 45.5, 52, 23)  # the LED display the game draws: centre x, y, z + width, height (mm), 1.5 mm off the recess floor


def decal_x(x, y, z, length, height, m, facing, name='decal'):
    """a flat sticker in the y-z plane at game x (mm), facing -x (facing=-1) or +x"""
    bm = bmesh.new()
    vs = [bm.verts.new(gv(M_(x), M_(y + dy * height / 2), M_(z + dz * length / 2))) for dz, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    bm.faces.new(vs if facing < 0 else vs[::-1])
    o = bpy.data.objects.new(name, bpy.data.meshes.new(name)); bm.to_mesh(o.data); bm.free()
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(m)
    return o


def decal_z(x, y, z, w, h, m, facing=1, name='decal'):
    """a flat sticker in the x-y plane at game z (mm), facing +z (the back, toward you) or -z (the front)"""
    bm = bmesh.new()
    vs = [bm.verts.new(gv(M_(x + dx * w / 2), M_(y + dy * h / 2), M_(z))) for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    bm.faces.new(vs if facing > 0 else vs[::-1])
    o = bpy.data.objects.new(name, bpy.data.meshes.new(name)); bm.to_mesh(o.data); bm.free()
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(m)
    return o


def uv_flat(o, cu, cv, su, sv, axis):
    """straight-on UVs for a decal: axis 'z' (seen from behind, right = +x), '-z' (seen from the front, right = -x)"""
    bpy.context.view_layer.update()
    me = o.data
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data
    for pg in me.polygons:
        for li in pg.loop_indices:
            v = o.matrix_world @ me.vertices[me.loops[li].vertex_index].co
            gx, gy = v.x, v.z
            u = (gx - M_(cu)) / M_(su) if axis == 'z' else (M_(cu) - gx) / M_(su)
            uv[li].uv = (u + 0.5, (gy - M_(cv)) / M_(sv) + 0.5)


def cut1(o, cutter):
    cut(o, cutter)
    for pg in o.data.polygons: pg.material_index = 0
    return o


def build():
    body = mat('rd_body', 0x3a3f4a, rough=0.32, metal=0.35, clearcoat=0.6, tex=tex_noise('rd_body_t', 0x3a3f4a, var=0.08, size=16, seed=501))
    black = mat('rd_black', 0x141418, rough=0.38, clearcoat=0.5)
    rubber = mat('rd_rubber', 0x1a1a1e, rough=0.8, tex=tex_noise('rd_rubber_t', 0x1c1c22, var=0.22, size=16, speck=0x3a3a44, speck_p=0.3, seed=502))
    chrome = mat('rd_chrome', 0xc8ccd4, rough=0.16, metal=1.0)
    recess = mat('rd_recess', 0x0a0606, rough=0.5)
    lamp_m = mat('rd_lamp', 0xff2020, rough=0.15, emit=0xff2020, strength=4.0)
    lampoff = mat('rd_lampoff', 0x5a0c0c, rough=0.15, clearcoat=1.0)
    keyb = mat('rd_keyb', 0x2e7bff, rough=0.4, clearcoat=0.5)
    keyg = mat('rd_keyg', 0x6a6a74, rough=0.6)
    def dome(px):
        h, w = px.shape[:2]; c = w / 2
        px[:] = hexrgb(0x262c3a)
        for k, r in enumerate(range(int(c) - 2, 4, -5)): px_disc(px, c, c, r, 0x2e3546 if k % 2 == 0 else 0x262c3a)
        text_px(px, 'K-BAND', int(c) - 17, int(c) - 3, 1, 0x8a94aa)
    radome = mat('rd_radome', 0xffffff, rough=0.3, clearcoat=0.6, tex=tex_canvas('rd_radome_t', 48, 48, dome))
    def stripe(px):
        px[:] = hexrgb(0x2e7bff); px[:2] = px[-2:] = hexrgb(0xf4f4f4)
        text_px(px, 'SPEED TRAP', 4, 4, 1, 0xffffff)
    stripe_m = mat('rd_stripe', 0xffffff, rough=0.35, clearcoat=0.6, tex=tex_canvas('rd_stripe_t', 66, 15, stripe))
    def bezel(px):
        px[:] = hexrgb(0x141418)
        text_px(px, 'HOW FAST', 1, 1, 1, 0xffe14d)
    bezel_m = mat('rd_label', 0xffffff, rough=0.4, tex=tex_canvas('rd_label_t', 49, 9, bezel))
    blue = mat('rd_blue', 0x2e7bff, rough=0.35, clearcoat=0.6)
    parts, lamp_parts = [], []
    A = parts.append

    # ---------------- antenna: flared horn, rubber bumper ring, flat radome face set into it
    A(lathe([(M_(33), M_(-80)), (M_(34.5), M_(-96)), (M_(36), M_(-98)), (M_(36), M_(-103)), (M_(37), M_(-106)), (M_(47.5), M_(-184)), (M_(47.5), M_(-188))],
            (0, M_(AX_Y), 0), black, seg=28, cap=False))
    A(lathe([(M_(46), M_(-186)), (M_(51), M_(-185)), (M_(52.5), M_(-188)), (M_(52.5), M_(-199)), (M_(51), M_(-202.5)), (M_(48), M_(-203)), (M_(46.5), M_(-201.5)), (M_(46.5), M_(-196)), (M_(46), M_(-186))],
            (0, M_(AX_Y), 0), rubber, seg=28, cap=False))
    def hr(z): return 37 + 10.5 * (-106 - z) / 78  # the horn's radius at z
    A(lathe([(M_(hr(-121) + 0.3), M_(-121)), (M_(hr(-122) + 2), M_(-122)), (M_(hr(-128) + 2), M_(-128)), (M_(hr(-129) + 0.3), M_(-129)), (M_(hr(-121) + 0.3), M_(-121))],
            (0, M_(AX_Y), 0), blue, seg=28, cap=False))  # a police-blue band round the horn
    bm = bmesh.new()
    vs = [bm.verts.new(gv(M_(math.cos(2 * math.pi * k / 28) * 46.6), M_(AX_Y + math.sin(2 * math.pi * k / 28) * 46.6), M_(-198))) for k in range(28)]
    f = bm.faces.new(vs); bm.normal_update()
    if f.normal.y > 0: f.normal_flip()  # (blender -y = game forward) the radome faces forward
    rdm = bpy.data.objects.new('radome', bpy.data.meshes.new('radome')); bm.to_mesh(rdm.data); bm.free()
    bpy.context.scene.collection.objects.link(rdm); rdm.data.materials.append(radome); A(rdm)
    # ---------------- body: rounded housing; the readout head on its back is a block of its own, wider than the body
    A(side(pz([(-100, 2), (-100, 58), (-92, 63), (-24, 64), (30, 64), (36, 56), (36, 10), (30, 2), (24, -2), (-92, -2)]), M_(58), (0, 0, 0), body, bev=M_(6), seg=3))
    head = side(pz([(0, 34), (0, 82), (8, 94), (FACE_Z, 94), (FACE_Z, 34)]), M_(68), (0, 0, 0), body, bev=M_(4), seg=3)
    apply_mods(head)
    cut1(head, box((M_(SCR[3] + 4), M_(SCR[4] + 6), M_(6)), (M_(SCR[0]), M_(SCR[1]), M_(FACE_Z - 0.5)), None))  # the display recess, 3.5 mm deep
    A(head)
    A(box((M_(SCR[3] + 4.4), M_(SCR[4] + 6.4), M_(1)), (M_(SCR[0]), M_(SCR[1]), M_(FACE_Z - 2.5)), recess))  # its dark floor, 2 mm under the face
    A(box((M_(70), M_(2.6), M_(16)), (0, M_(95), M_(FACE_Z - 1)), body, bev=M_(1)))  # sun visor, 7 mm past the face
    for x, m in ((-16, keyg), (0, keyb), (16, keyg)):
        A(cyl(M_(4), M_(3), (M_(x), M_(44), M_(FACE_Z + 0.8)), m, axis='z', seg=12, bev=M_(0.8)))
    lab = decal_z(0, 85.5, FACE_Z + 1.1, 44, 8, bezel_m, 1, 'label'); A(lab)
    for sx in (-1, 1):  # police stripe: a blue trim strip down each side, the printed decal on it
        A(side(pz([(-84, 17), (28, 17), (28, 33), (-84, 33)]), M_(1.6), (sx * M_(29.6), 0, 0), blue, bev=M_(0.4)))
    st = [decal_x(sx * (29.6 + 0.8 + 1.1), 25, -28, 110, 15, stripe_m, sx, 'stripe') for sx in (-1, 1)]
    parts.extend(st)
    # beacon on top of the head: a dull red dome (off) inside the glowing one (the game blinks the glowing one)
    A(cyl(M_(9), M_(3), (M_(18), M_(95.5), M_(22)), chrome, axis='y', seg=16, bev=M_(0.8)))
    A(lathe([(M_(6.3), M_(97)), (M_(6.3), M_(99)), (M_(5.5), M_(102)), (M_(3.5), M_(104.3)), (0, M_(105.3))], (M_(18), 0, M_(22)), lampoff, seg=14, axis='y'))
    lamp_parts.append(lathe([(M_(7.9), M_(95.4)), (M_(7.9), M_(99)), (M_(7.1), M_(103)), (M_(4.8), M_(105.8)), (0, M_(107.2))], (M_(18), 0, M_(22)), lamp_m, seg=14, axis='y', name='lamp'))
    # ---------------- grip, guard, lock trigger
    A(side(pz([(-26, 0), (24, 0), (26, -14), (24, -40), (26, -64), (30, -86), (24, -96), (0, -99), (-7, -93), (-5, -81), (-10, -70), (-6, -60), (-12, -48), (-10, -36), (-18, -22)]),
           M_(32), (0, 0, 0), rubber, bev=M_(4), seg=2))
    A(side(pz([(-74, 0), (-70, -18), (-58, -34), (-36, -40), (-16, -36), (-14, 0)]), M_(12), (0, 0, 0), body, bev=M_(3), seg=2,
           holes=[pz([(-64, -4), (-22, -4), (-21, -30), (-38, -34), (-56, -28)])]))
    A(side(pz([(-48, -2), (-38, -2), (-34, -12), (-36, -24), (-42, -30), (-46, -28), (-43, -18), (-46, -10)]), M_(9), (0, 0, 0), chrome, bev=M_(2)))

    # coiled cord out of the butt down to a car lighter plug (they really have these)
    A(lathe([(M_(6), M_(-96)), (M_(4.2), M_(-104)), (M_(3.4), M_(-110))], (M_(1), 0, M_(10)), rubber, seg=10, axis='y'))  # strain relief
    pts = []
    for i in range(61):
        t = i / 60; a = t * 6 * 2 * math.pi
        cy_, cz_ = -110 - 52 * t, 10 + 22 * t * t  # the coil's axis droops back a bit
        pts.append((M_(1 + math.cos(a) * 6), M_(cy_), M_(cz_ + math.sin(a) * 6)))
    pts.append((M_(1), M_(-168), M_(36))); pts.append((M_(1), M_(-176), M_(40)))
    cord = mat('rd_cord', 0x16161a, rough=0.5, clearcoat=0.4)
    A(tube(pts, M_(1.9), cord, seg=6, name='cord'))
    A(lathe([(M_(3), M_(-174)), (M_(8.5), M_(-178)), (M_(9), M_(-182)), (M_(9), M_(-206)), (M_(8), M_(-210)), (M_(5), M_(-212))], (M_(1), 0, M_(41)), black, seg=14, axis='y'))  # plug
    A(lathe([(M_(5), M_(-211.5)), (M_(5), M_(-214)), (M_(3.5), M_(-216)), (0, M_(-216.5))], (M_(1), 0, M_(41)), chrome, seg=10, axis='y'))  # its tip
    A(cyl(M_(9.4), M_(3), (M_(1), M_(-186), M_(41)), lampoff, axis='y', seg=14))  # red ring on the plug

    flat = [rdm, lab] + st
    for p in parts + lamp_parts:
        apply_mods(p)
        if p not in flat: uv_box(p, 0.03)
    uv_flat(lab, 0, 85.5, 44, 8, 'z')
    uv_flat(rdm, 0, AX_Y, 93.2, 93.2, '-z')
    for o_, sx in zip(st, (-1, 1)):
        uv_planar(o_, (M_(sx * 31.5), M_(25), M_(-28)), (M_(110), M_(15)), 'x' if sx > 0 else '-x')
    WZ = {'rd_body': 'a', 'rd_rubber': 'a', 'rd_black': 'b', 'rd_chrome': 'b', 'rd_recess': 'b', 'rd_blue': 'n', 'rd_cord': 'b'}  # wrap zones: body + grip = A, horn + metal = B, the stripe, radome, lamp, labels keep their look
    bodies = zone_join(parts, 'rd_body', WZ, default='n')
    lnode = part(lamp_parts, 'lamp_wzN', pivot=(M_(18), M_(97), M_(22)))
    meta = {'kind': 'weapon', 'id': 'radar', 'paint': ['rd_stripe'], 'muzzle': [0, M_(AX_Y), -0.205], 'hatAt': [[M_(-8), M_(94), M_(22)], 0.06],
            'screen': [M_(SCR[0]), M_(SCR[1]), M_(SCR[2]), M_(SCR[3]), M_(SCR[4])]}
    return finish('w_radar', bodies + [lnode], meta)


main(build, 'w_radar')
