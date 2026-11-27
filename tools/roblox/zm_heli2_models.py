# ZOMBIES: the extraction helicopter, rebuilt from the web game's own (27 Nov 2026; the owner: "Can the helicopter be
# modeled a bit better? Like the jankfire helicopter?"). Runs tools/blender/make_heli.py's build (the JANK NEWS 7: the
# lofted pod-and-boom, the bubble with a real cabin, gasketed windows, the 3-blade rotor on its hub, mast and pitch
# links, the 2-blade tail rotor, the swept fin, skids, the belly searchlight on its yoke, beacon and nav lights) with
# its livery swapped for one with NO writing, digits or symbols (Roblox: roblox-upload-content-rules), in two schemes:
#   A  the JANK scheme toned down for night: dusty pink body, mustard boom, teal skids
#   B  a darker rescue scheme with one jank accent stripe
# then splits it for Roblox: the parts that turn are their own pieces (zh_rotor, zh_tail, zh_search), the rest one piece
# per kind (zh_body, zh_glass, zh_cabin, zh_lamps, zh_beacon, zh_cam), x3 to studs (the web models are metres), nose
# along Blender +Y (Roblox -Z after rbxglb's turn), skids at z 0. Marker cubes (zh_hubmark, zh_tailmark, zh_nosemark)
# tell Studio's ZmKit.importHeli where the hubs and the nose are (LoadAsset centres a model, so positions are relative).
#   blender.exe -b --factory-startup -P tools/roblox/zm_heli2_models.py -- <outDir> [--livery=A|B|both] [--ao]
# -> <outDir>/zm_heli_A.glb, zm_heli_B.glb, livery_A.png, livery_B.png (look at both at full size before uploading)
import os, sys, math
import bpy, bmesh
from mathutils import Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
MH = os.path.normpath(os.path.join(HERE, '..', 'blender', 'make_heli.py'))
mine = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = next((a for a in mine if not a.startswith('--')), '.')
WHICH = next((a.split('=', 1)[1] for a in mine if a.startswith('--livery=')), 'both')
AO = '--ao' in mine
os.makedirs(OUT, exist_ok=True)
SCALE = 3.0

# make_heli reads its flags from sys.argv at import: build only, no pictures, no export of its own
sys.argv = [sys.argv[0], '--', '--no-sheet', '--no-hero', '--no-export'] + ([] if AO else ['--no-ao'])
src = open(MH, encoding='utf8').read().rstrip()
assert src.endswith('main()'), 'make_heli.py no longer ends with main()'
src = src[:-len('main()')]

LIVERIES = r'''
def _scheme(BODY, BOOM, ACC, INK_, WHITE_, NOSE, BOLT, FIN, HZ, SKID, accent_only=False):
    def livery(H):
        P = PA; SD = P.SIDES
        P.px[:] = hexrgb(BODY)
        keel = [(H.P[r][3].x, H.P[r][3].y) for r in range(RI[2.40], RI[-2.55] + 1)]
        P.poly(SD, [(2.75, keel[0][1])] + keel + [(-3.2, keel[-1][1] + 0.05), (-3.2, 0.4), (2.75, 0.4)], INK_)
        sl = lambda y, d=0.0: -1.93 - 0.342 * (y - 0.5) - d
        band = lambda d0, d1, col: P.poly(SD, [(sl(0.4, d0), 0.4), (sl(3.2, d0), 3.2), (sl(3.2, d1), 3.2), (sl(0.4, d1), 0.4)], col)
        if accent_only:
            band(0.34, 7.0, BOOM); band(0.06, 0.28, ACC)  # (B: one accent stripe where the pod meets the boom)
        else:
            band(0.34, 7.0, BOOM); band(0.0, 0.06, INK_); band(0.06, 0.28, ACC); band(0.28, 0.34, INK_)
        fe = lambda y, d=0.0: (-6.00 - 0.51 * (y - 1.84) if y >= 1.84 else -6.00 + 0.42 * (1.84 - y)) + d
        tail = lambda d0, d1, col, **kw: P.poly(SD, [(fe(0.9, d0), 0.9), (fe(1.84, d0), 1.84), (fe(3.2, d0), 3.2), (fe(3.2, d1) if d1 > -1 else -7.05, 3.2), (fe(1.84, d1) if d1 > -1 else -7.05, 1.84), (fe(0.9, d1) if d1 > -1 else -7.05, 0.9)], col, **kw)
        tail(0.02, -9, FIN)
        if not accent_only:
            tail(0.10, 0.05, ACC); tail(0.05, 0.02, INK_); tail(0.12, 0.10, INK_)
        P.poly(SD, [(-5.3, 0.9), (-5.3, 1.55), (-7.05, 1.55), (-7.05, 0.9)], INK_, hazard=HZ)  # hazard bands on the ventral fin
        P.poly(SD, [(-7.05, 2.90), (-6.2, 2.90), (-6.2, 3.2), (-7.05, 3.2)], ACC if not accent_only else FIN); P.line(SD, [(-7.05, 2.89), (-6.2, 2.89)], INK_, 1.0)
        xc = lambda y: -6.555 - 0.41 * (y - 2.40)
        bolt = [(0.03, 0.40), (-0.17, -0.02), (-0.04, -0.02), (-0.11, -0.40), (0.17, 0.06), (0.04, 0.06), (0.15, 0.40)]
        for dx, dy, col in ((0.03, -0.035, INK_), (0.0, 0.0, BOLT)): P.poly(SD, [(xc(2.40 + v) + u + dx, 2.40 + v + dy) for u, v in bolt], col)  # the bolt on the fin
        P.poly(SD, [(2.40, 0.4), (2.75, 0.4), (2.75, 3.0), (2.40, 3.0)], NOSE); P.line(SD, [(2.395, 0.4), (2.395, 3.0)], INK_, 1.0)
        for nm, xa, xb, s0, s1 in WIN:
            if nm == 'sky': continue
            ra, rb, j0, j1 = RI[xa], RI[xb], s0, s1 + 1
            out = [H.P[r][j0] for r in range(ra, rb + 1)] + [H.P[rb][j] for j in range(j0 + 1, j1 + 1)] + [H.P[r][j1] for r in range(rb - 1, ra - 1, -1)] + [H.P[ra][j] for j in range(j1 - 1, j0, -1)]
            c = sum(out, V3()) / len(out)
            pts = [(c.x + (p.x - c.x) * 0.975, c.y + (p.y - c.y) * 0.975) for p in out]
            ycut = min(p[1] for p in pts) + 0.55 * (max(p[1] for p in pts) - min(p[1] for p in pts))
            for reg in SD:
                sub = P.sub(reg); ins = P.mask(reg, pts)
                row = P.pix(reg, 0, ycut)[1] - P.R[reg][1]
                yy = np.mgrid[0:sub.shape[0], 0:sub.shape[1]][0]
                sub[ins] = hexrgb(G_DARK); sub[ins & (yy < row)] = hexrgb(G_MID)
        P.line(SD, [(0.90, 2.115), (0.90, 0.80), (0.84, 0.735), (-0.09, 0.735), (-0.15, 0.80), (-0.15, 2.115), (0.90, 2.115)], INK_)
        P.line(SD, [(-0.15, 0.80), (-0.21, 0.735), (-1.14, 0.735), (-1.20, 0.80), (-1.20, 2.03), (-0.15, 2.03)], INK_)
        P.line(SD, [(0.05, 2.30), (0.05, 2.50)], INK_); P.line(SD, [(-0.62, 2.26), (-0.62, 2.52)], INK_); P.line(SD, [(-1.62, 2.26), (-1.62, 2.50)], INK_)
        for x in (-3.02, -3.95, -4.42, -5.08):
            P.line(SD, [(x, 1.28), (x, 2.16)], INK_)
        # where the web one had its writing: plain shapes only (no letters, no digits, no symbols)
        if not accent_only:
            P.poly(SD, [(0.80, 0.93), (0.80, 1.10), (-1.10, 1.10), (-1.10, 0.93)], BOOM)   # (was JANK NEWS) a door stripe
            P.line(SD, [(0.80, 0.915), (-1.10, 0.915)], INK_, 1.0); P.line(SD, [(0.80, 1.115), (-1.10, 1.115)], INK_, 1.0)
            P.poly(SD, [(-3.30, CYL(-3.30) - 0.06), (-3.30, CYL(-3.30) + 0.06), (-4.10, CYL(-4.10) + 0.06), (-4.10, CYL(-4.10) - 0.06)], INK_)  # (was J-ANKY)
            P.poly(SD, [(-5.10, CYL(-5.10) - 0.09), (-5.10, CYL(-5.10) + 0.09), (-5.70, CYL(-5.70) + 0.09), (-5.70, CYL(-5.70) - 0.09)], INK_, hazard=BOOM)  # (was NO HUGS)
        else:
            P.poly(SD, [(0.80, 0.98), (0.80, 1.06), (-2.10, 1.06), (-2.10, 0.98)], ACC)  # B: the one accent, a thin line along the side
        P.sub('U')[:] = hexrgb(INK_)  # (was HI MOM) the belly plain
        P.sub('S')[:] = hexrgb(FIN)   # (was NO STEP / OK STEP) the stabiliser plain
        P.grain()
        for k, c in (('pink', BODY), ('yellow', BOOM), ('cyan', SKID), ('ink', INK_), ('white', WHITE_)): P.sub(k)[:] = hexrgb(c)
        P.write()
    return livery

# the instrument panel without the web one's two ring dials (stacked, they read as an "8" and a "0": no digits on
# Roblox, not even look-alikes): a plain gauge block there; the moving map, the engine bars and the annunciators stay
def mat_glow_zm(name):
    def draw(px):
        for k, c in (('white', 0xfff0c8), ('red', 0xff2030), ('green', 0x39ff14), ('strobe', 0xffffff)):
            x, y, w, h = GLOW[k]; px[y:y + h, x:x + w] = hexrgb(c)
        p = px[16:32, 0:32]; p[:] = hexrgb(0x0b0b12)
        p[2:10, 2:13] = hexrgb(0x08303c)
        for i in range(2, 13): p[2 + (i * 5 // 9) % 7, i] = hexrgb(0x4fd8ff)
        px_line(p, 3, 8, 11, 3, 0xff4fd8, 1.0); p[5:7, 7:9] = hexrgb(0xffe14d)
        p[2:10, 19:30] = hexrgb(0x0c2410)
        for k_, hgt in enumerate((5, 6, 4, 6, 3)):
            p[9 - hgt:9, 20 + k_ * 2] = hexrgb(0x39ff14 if k_ != 2 else 0xff3030)
        p[3:9, 14:18] = hexrgb(0x1c2a30)
        for k_, c in enumerate((0xff3030, 0xffa020, 0x39ff14, 0x4fd8ff, 0xff4fd8, 0xffe14d, 0xff3030, 0x39ff14)):
            p[12:14, 3 + k_ * 3:5 + k_ * 3] = hexrgb(c)
    img = tex_canvas(name + '_t', 32, 32, draw)
    return mat(name, 0xffffff, rough=0.25, emit=0xffffff, strength=2.2, tex=img, emit_tex=True)

LIVERY = {
    # A: the JANK scheme for night: dusty pink body, mustard boom and nose, teal skids and accents, the bolt mustard
    'A': _scheme(BODY=0xa8627f, BOOM=0xb38a33, ACC=0x2f8a86, INK_=0x1b1520, WHITE_=0xe6e0d4, NOSE=0xb38a33, BOLT=0xb38a33,
                 FIN=0xa8627f, HZ=0xb38a33, SKID=0x2f8a86),
    # B: a darker rescue scheme: charcoal body and boom, one jank-pink accent stripe, light grey bolt and hazards
    'B': _scheme(BODY=0x383d42, BOOM=0x383d42, ACC=0xc2508f, INK_=0x15171a, WHITE_=0xd8dbde, NOSE=0x383d42, BOLT=0xb9bec4,
                 FIN=0x383d42, HZ=0x9aa0a6, SKID=0x2a2d31, accent_only=True),
}
'''

sys.path.insert(0, HERE)
import rbxglb  # noqa: E402  (tools/roblox: the turn for Roblox)


def build_one(tag):
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for img in list(bpy.data.images): bpy.data.images.remove(img)
    for m in list(bpy.data.materials): bpy.data.materials.remove(m)
    g = {'__file__': MH, '__name__': 'make_heli_zm'}
    exec(compile(src, MH, 'exec'), g)
    exec(compile(LIVERIES, 'zm_liveries', 'exec'), g)
    g['livery'] = g['LIVERY'][tag]
    g['mat_glow'] = g['mat_glow_zm']
    # the skids, the mast cap and the trim's other cyan bits are the trim atlas's cyan, not the paint's: A teal, B dark
    x, y, w, h, col, ro, me = g['TRIM']['cyan']
    g['TRIM']['cyan'] = (x, y, w, h, 0x2f8a86 if tag == 'A' else 0x2a2d31, ro, me)
    g['lib'].reset(); g['lib']._mats.clear()
    root, N, t0, t1, res = g['finish_heli'](g['build']())
    # the livery map, for a look at full size before any upload
    pa = g['PA']
    pa.img.filepath_raw = os.path.join(OUT, 'livery_%s.png' % tag); pa.img.file_format = 'PNG'; pa.img.save()
    # the left rear door (Roblox -X, the side the squad boards; the front one is filled by the pilot's seat) out of the shell, the glass and the cabin's
    # liner as pieces of their own, so the extraction film can slide it back (27 Nov, the owner: "helicopter door opens
    # and there's a guy, he reaches out his hand"). the door's box from make_heli's shut lines: x -1.20..-0.15, y
    # 0.74..2.03 (game metres; Blender (x, -z, y))
    bpy.context.view_layer.update()
    def in_door(w, inner):  # (Blender -y: Roblox -X after the turn, measured on the 27 Nov preview)
        return -1.20 <= w.x <= -0.15 and 0.74 <= w.z <= 2.03 and w.y < -inner
    def split(obj, name, inner):
        mw = obj.matrix_world
        bm = bmesh.new(); bm.from_mesh(obj.data); bm.faces.ensure_lookup_table()
        pick = set(f.index for f in bm.faces if in_door(mw @ f.calc_center_median(), inner))
        if not pick:
            bm.free(); return None
        new = obj.copy(); new.data = obj.data.copy(); new.name = name
        bpy.context.scene.collection.objects.link(new)
        bm2 = bmesh.new(); bm2.from_mesh(new.data); bm2.faces.ensure_lookup_table()
        bmesh.ops.delete(bm2, geom=[f for f in bm2.faces if f.index not in pick], context='FACES')
        bm2.to_mesh(new.data); bm2.free()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index in pick], context='FACES')
        bm.to_mesh(obj.data); bm.free()
        return new
    N['door'] = split(N['shell'], 'door', 0.45)
    N['doorglass'] = split(N['glass'], 'doorglass', 0.45)
    N['doorliner'] = split(N['cabin'], 'doorliner', 0.58)
    dc = None
    if N['door']:
        vs = [N['door'].matrix_world @ v.co for v in N['door'].data.vertices]
        dc = sum(vs, vs[0] * 0) / len(vs)
    # the pieces Roblox gets: world transforms baked, unparented, metres -> studs, nose +X -> +Y
    turnto = Matrix.Rotation(math.pi / 2, 4, 'Z') @ Matrix.Scale(SCALE, 4)
    want = [('shell', 'zh_body'), ('glass', 'zh_glass'), ('cabin', 'zh_cabin'), ('lamps', 'zh_lamps'), ('beacon', 'zh_beacon'),
            ('rotor_main', 'zh_rotor'), ('rotor_tail', 'zh_tail'), ('camera', 'zh_cam'), ('searchlight', 'zh_search'),
            ('door', 'zh_door'), ('doorglass', 'zh_doorglass'), ('doorliner', 'zh_doorliner')]
    want = [(k, nm) for k, nm in want if N.get(k) is not None]
    bpy.context.view_layer.update()
    marks = {'zh_hubmark': N['rotor_main'].matrix_world.translation.copy(), 'zh_tailmark': N['rotor_tail'].matrix_world.translation.copy(),
             'zh_searchmark': N['searchlight'].matrix_world.translation.copy()}
    if dc is not None: marks['zh_doormark'] = dc
    lo = [1e9] * 3; hi = [-1e9] * 3
    out = []
    for key, nm in want:
        o = N[key]
        me = o.data.copy()
        me.transform(o.matrix_world)
        me.transform(turnto)
        for v in me.vertices:
            for a in range(3): lo[a] = min(lo[a], v.co[a]); hi[a] = max(hi[a], v.co[a])
        mats = [m.name for m in me.materials]
        code = 'g16364699' if key in ('glass', 'doorglass') else 't'  # (rbxglb.look_code: the glass's tint + alpha; the rest keep their pictures)
        me.name = '%s__%s' % (nm, code)  # (27 Nov test: Roblox names a MeshPart after the glTF MESH, not the node)
        ob = bpy.data.objects.new('%s__%s' % (nm, code), me)
        bpy.context.scene.collection.objects.link(ob)
        out.append(ob)
    # the nose: the front of the airframe at mid height (after the turn the nose is +Y)
    nose = (0.0, hi[1], (lo[2] + hi[2]) / 2)
    for nm, p in list(marks.items()) + [('zh_nosemark', None)]:
        q = (turnto @ p) if p is not None else nose
        bm = bpy.data.meshes.new(nm)
        s = 0.06
        verts = [(q[0] + x * s, q[1] + y * s, q[2] + z * s) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
        faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        bm.from_pydata(verts, [], faces); bm.update()
        ob = bpy.data.objects.new(nm + '__p808080', bm)
        bpy.context.scene.collection.objects.link(ob)
        out.append(ob)
    # only the Roblox pieces in the scene
    for o in list(bpy.context.scene.objects):
        if o not in out: bpy.data.objects.remove(o, do_unlink=True)
    rbxglb.turn_for_roblox(out)
    path = os.path.join(OUT, 'zm_heli_%s.glb' % tag)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=False, export_apply=True, export_animations=False,
                              export_yup=True, export_texcoords=True, export_normals=True, export_materials='EXPORT',
                              export_image_format='AUTO', export_vertex_color='ACTIVE' if AO else 'NONE')
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in out)
    print('ZMHELI2', tag, path, os.path.getsize(path), 'bytes', tris, 'tris', 'size', [round(hi[a] - lo[a], 1) for a in range(3)],
          [(o.name, len(o.data.polygons), [m.name for m in o.data.materials]) for o in out])


for tag in (['A', 'B'] if WHICH == 'both' else [WHICH]):
    build_one(tag)
