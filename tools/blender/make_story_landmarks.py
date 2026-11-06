# OVERDUE story landmarks (the slice's hero props): THE MACHINE (the original ☺ CORP vending machine, a tiny sim world
# glowing behind its glass), the Lost & Found depot sign (every letter salvaged from something else), the returns
# counter (with its cat), a lost-property pile, the Gut border gate (a pastel Bottom archway being eaten by flesh), the
# sofa-car and the rush-hour car wreck.
# -> public/models/story/s_<id>.glb (full mesh + *_lod1 meshes at <= 25% tris) + tools/blender/sheets/story/s_<id>.jpg
# run: blender -b --python tools/blender/make_story_landmarks.py [-- --only machine,gutgate] [--no-sheet]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bottom_kit import *
import bottom_kit as BK
import gutkit as GK
from sidekit import seg7

PINK, YEL, TEAL, MINT, LILAC, PEACH = 0xffb3c7, 0xffe58a, 0x5fd3c6, 0xa8f0d0, 0xc9a8ff, 0xffc49a
HOT, MAG, CYAN, GREEN, RED, INK = 0xff4fd8, 0xff00dc, 0x4fd8ff, 0x39ff14, 0xff3030, 0x141018
DYE = [0xff6fae, 0xffe14d, 0x3fd6c6, 0xb48cff]


def plain(name, col, rough=0.5, metal=0.0, cc=0.0, var=0.08, speck=None, p=0.0, seed=1, size=16):
    return mat(name, col, rough=rough, metal=metal, clearcoat=cc, tex=tex_noise(name + '_t', col, var=var, size=size, speck=speck, speck_p=p, seed=seed))


def tiled(objs, size=0.25):
    for o in objs: uv_tile(o, size)
    return objs


def fit(o, rect, **kw):
    uv_fit(o, rect, **kw)
    return o


def helix(c0, c1, r, turns, per=4, phase=0.0):
    """points of a coil spring from game point c0 to c1 (the axis), radius r: vending-machine spirals, springs"""
    a, b = Vector(c0), Vector(c1); ax = (b - a); L = ax.length; ax.normalize()
    up = Vector((0, 1, 0)) if abs(ax.y) < 0.9 else Vector((1, 0, 0))
    u = (up - ax * ax.dot(up)).normalized(); v = ax.cross(u)
    n = int(turns * per)
    return [tuple(a + ax * (L * i / n) + (u * math.cos(phase + 2 * math.pi * i / per) + v * math.sin(phase + 2 * math.pi * i / per)) * r) for i in range(n + 1)]


def glyph(ch, x0, y0, s, depth, m, name='glyph'):
    """a chunky block letter from the 5x7 font: every lit pixel a cube, merged (counts as one part)"""
    g = FONT.get(ch.upper(), FONT[' '])
    parts = []
    for ry, row in enumerate(g):
        for rx, bit in enumerate(row):
            if bit == '1': parts.append(box((s, s, depth), (x0 + rx * s, y0 - ry * s, 0), m))
    return parts


def fix_uv(o):
    """faces whose UVs collapsed to a line (box sides under a front projection, swatch fills) get a tiny UV triangle
    round their own centre: same pixel, but no zero-area UV faces for the QA gate"""
    me = o.data
    if o.type != 'MESH' or not me.uv_layers: return o
    uv = me.uv_layers.active.data
    for pg in me.polygons:
        L_ = list(pg.loop_indices); P = [Vector(uv[i].uv) for i in L_]
        ar = sum((P[k].x * P[(k + 1) % len(P)].y - P[(k + 1) % len(P)].x * P[k].y) for k in range(len(P))) / 2
        if abs(ar) > 2e-7: continue
        c = sum(P, Vector((0, 0))) / len(P)
        for k, i in enumerate(L_):
            t = 2 * math.pi * k / len(L_); uv[i].uv = (c.x + 0.0008 * math.cos(t), c.y + 0.0008 * math.sin(t))
    return o


def pulse_normals(o):
    """faces on pulse/flesh materials get one smooth normal per position (the game breathes them along the normal: a
    split normal would tear the shell open); everything else keeps its own (auto-smooth / custom) normals"""
    me = o.data
    pm = {i for i, m in enumerate(me.materials) if m and GK.PULSE.search(m.name)}
    if not pm: return o
    if hasattr(me, 'calc_normals_split'): me.calc_normals_split()
    acc = {}
    key = lambda co: (round(co.x, 4), round(co.y, 4), round(co.z, 4))
    for p in me.polygons:
        if p.material_index not in pm: continue
        for v in p.vertices:
            k = key(me.vertices[v].co); acc[k] = acc.get(k, Vector()) + p.normal * p.area
    ln = [Vector(l.normal) for l in me.loops]
    for p in me.polygons:
        if p.material_index not in pm: continue
        for li in p.loop_indices:
            n = acc[key(me.vertices[me.loops[li].vertex_index].co)]
            if n.length > 1e-12: ln[li] = n.normalized()
    if hasattr(me, 'use_auto_smooth'): me.use_auto_smooth = True
    for p in me.polygons:
        if p.material_index in pm: p.use_smooth = True
    me.normals_split_custom_set([tuple(n) for n in ln])
    return o


# ------------------------------------------------------------ the run (bottom_kit.run, plus separate named nodes)
def run2(builders, sheet_kw=None):
    """like bottom_kit.run; a builder's extras may also carry '_sep': {name: (objs, pivot, lod objs)} for parts that
    must stay their own node (car wheels): each is joined with its origin at pivot, its lod becomes <name>_lod1."""
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    only = None; done = []
    if '--only' in argv: only = set(argv[argv.index('--only') + 1].split(','))
    for pid, fn in builders:
        if only and pid not in only: continue
        reset(); lib._mats.clear()
        objs, extra = fn()
        extra = dict(extra or {})
        lod_parts = extra.pop('_lod', None)
        lod_pick = extra.pop('_lodpick', None)
        sep = extra.pop('_sep', {})
        objs = [o for o in objs if o is not None]
        keep = set(objs) | set(lod_parts or [])
        for so, pv, sl in sep.values(): keep |= set(so) | set(sl)
        for o in list(bpy.context.scene.objects):
            if o not in keep: bpy.data.objects.remove(o, do_unlink=True)
        for o in keep:
            if o.type == 'MESH' and not o.data.uv_layers: uv_fit(o, (0.0, 0.0, 0.02, 0.02))
        full = sum(tri_count(o) for o in objs)
        lod = make_lod(objs, 's_' + pid + '_lod1', int(full * 0.245), parts=lod_parts or lod_pick)
        if lod_parts:
            for o in lod_parts:
                if o.name in bpy.data.objects and o != lod: bpy.data.objects.remove(o, do_unlink=True)
        nodes, lods = [], []
        for nm, (so, pv, sl) in sep.items():
            for o in sl: apply_mods(o)
            l = part(sl, nm + '_lod1', pv); smooth(l, 35)
            bake_normals(so); n = part(so, nm, pv)
            nodes.append(n); lods.append(l)
        bake_normals(objs)
        body = join(objs, 's_' + pid + '_mesh')
        me = body.data
        if me.validate(verbose=True): print('JF_MESH_FIXED', pid)
        while len(me.uv_layers) > 1: me.uv_layers.remove(me.uv_layers[-1])
        for n in nodes + lods:
            while len(n.data.uv_layers) > 1: n.data.uv_layers.remove(n.data.uv_layers[-1])
        for n in [body, lod] + nodes + lods: fix_uv(n); pulse_normals(n)
        root = finish('s_' + pid, [body, lod] + nodes + lods, {})
        tris = tri_count(body) + sum(tri_count(n) for n in nodes)
        lt = tri_count(lod) + sum(tri_count(n) for n in lods)
        _, lo, hi = stats(root)
        meta = {'kind': 'prop', 'id': pid, 'story': True, 'district': 'bottom'}
        meta['col'] = [round(hi[k] - lo[k], 2) for k in range(3)]
        meta['tris'] = [tris, lt]
        meta.update(extra)
        root['jf'] = json.dumps(meta)
        fid = STORY + '/s_' + pid
        if '--no-export' not in argv: export(root, fid)
        print(f'JF_TRIS s_{pid}: full {tris} lod1 {lt} ({100 * lt // max(1, tris)}%)')
        if '--no-sheet' not in argv:
            allm = list(me.materials) + [m for n in nodes for m in n.data.materials]
            preview_paint(set(allm), PREVIEW[len(done) % len(PREVIEW)] if pid not in ('sofacar',) else 0xffb3c7)
            for l in [lod] + lods: l.parent = None; l.hide_render = True
            kw = dict(exposure=-0.6); kw.update((sheet_kw or {}).get(pid, {}))
            if '--lod-only' not in argv: sheet(root, fid, **kw)
            if LOD_SHEETS:
                lr = bpy.data.objects.new('lodroot', None); bpy.context.scene.collection.objects.link(lr)
                for l in [lod] + lods: l.parent = lr; l.hide_render = False
                for n in [body] + nodes: n.hide_render = True
                for o in list(bpy.context.scene.objects):
                    if o.type in ('LIGHT', 'CAMERA'): bpy.data.objects.remove(o, do_unlink=True)
                old = lib.SHEETS; lib.SHEETS = LOD_SHEETS
                sheet(lr, 's_' + pid + '_lod1', views=('persp', 'front', 'back_persp'), res=(480, 320), **kw)
                lib.SHEETS = old
        done.append(pid)
        print(f'JF_MATS s_{pid}: ' + ', '.join(sorted({m.name for m in allm if m} if '--no-sheet' not in argv else {m.name for m in me.materials if m})))
    tmp = os.path.join(lib.SHEETS, '_tmp')
    for d in (os.path.join(tmp, STORY), tmp):
        try: os.rmdir(d)
        except OSError: pass


# ================================================================================================ THE MACHINE
# the original ☺ CORP vending machine, blown up to landmark size (a real snack machine is 0.9 x 1.83 x 0.9 m; this is
# the same layout at 5.6 x 6.8 x 3.2 m): glass on the viewer's left, the coin/keypad column on the right (= -x, the
# front is -z), the big pickup tray underneath, a lit header. Inside the glass, on spiral-coil shelves: the sims.
MW, MH, MD = 5.6, 6.8, 3.2
FZ = -MD / 2  # the front face
WIN = (-1.05, 2.55, 1.75, 5.75)  # window x0, x1, y0, y1 (game x)
WCX = (WIN[0] + WIN[1]) / 2
PCX = -1.925  # the control column's centre x
TRAY = (-0.85, 2.35, 0.45, 1.45)


def mc_atlases():
    # --- sim atlas (glows): the sky behind the shelves + swatches for the little worlds
    S = Atlas('mc_sim_t', 128)
    sky = S.sub(0, 0, 128, 34)  # one shelf's sim sky (a row panel is 3.6 x 0.95 m): sunset, a striped sun, the grid
    H0 = 20
    for y in range(34):
        t = y / H0
        sky[y] = hexrgb(0x2a1050) * (1 - t) + hexrgb(0xff5ab8) * t if y < H0 else hexrgb(0x1a0a2e)
    rr = np.random.default_rng(4)
    for k in range(26):
        x, y = rr.integers(0, 128), rr.integers(0, 11); sky[y, x] = hexrgb(0xffffff if k % 3 else 0x9ff5ff)
    sun = np.zeros((34, 128, 3), np.float32); px_disc(sun, 64, H0, 9, 0xffe14d)
    m_ = sun.sum(axis=2) > 0
    for y in (13, 16, 18): m_[y] = False
    sky[:H0][m_[:H0]] = hexrgb(0xffe14d)
    for x in range(-260, 400, 16): px_line(sky, 64 + (x - 64) * 0.12, H0, x, 33, 0x4fd8ff, 1.0)
    for y in (H0, H0 + 1, H0 + 3, H0 + 6, H0 + 10): sky[y] = sky[y] * 0.25 + hexrgb(0x4fd8ff) * 0.75
    S.px[34:68] = np.roll(sky, 38, axis=1)  # a second sky with the sun off to one side
    R = {'sky': S.rect(0, 0, 128, 34), 'sky2': S.rect(0, 34, 128, 34)}
    def blds(x, y, wall, win, name):
        b = S.sub(x, y, 16, 16); crust(b, wall, 0.06, seed=x + y)
        for yy in range(2, 15, 3):
            for xx in range(2, 15, 4): b[yy:yy + 2, xx:xx + 2] = hexrgb(win if (xx + yy) % 7 else 0x2a1a3a)
        R[name] = S.rect(x, y, 16, 16, 1)
    blds(0, 80, 0x5fd3c6, 0xffe14d, 'b_teal'); blds(16, 80, 0xff8ac8, 0xfff2c0, 'b_pink'); blds(32, 80, 0xffe58a, 0x4fd8ff, 'b_yel')
    blds(48, 80, 0xe8e4f0, 0xff4fd8, 'b_white')
    rd = S.sub(64, 80, 16, 16); rd[:] = hexrgb(0x4a4458); rd[7:9, 1::5] = hexrgb(0xffffff); rd[7:9, 2::5] = hexrgb(0xffffff); R['road'] = S.rect(64, 80, 16, 16, 1)
    wt = S.sub(80, 80, 16, 16); crust(wt, 0x2ab8e8, 0.1, seed=5, speck=0xc8f8ff, p=0.08); R['water'] = S.rect(80, 80, 16, 16, 1)
    ck = S.sub(96, 80, 16, 16); ck[:] = hexrgb(0xfff0f6); ck[0:4, 0:4] = ck[4:8, 4:8] = ck[8:12, 0:4] = ck[12:16, 4:8] = hexrgb(0xff8ac8)
    ck[0:4, 8:12] = ck[4:8, 12:16] = ck[8:12, 8:12] = ck[12:16, 12:16] = hexrgb(0xff8ac8); R['tile'] = S.rect(96, 80, 16, 16, 1)
    cr = S.sub(112, 80, 16, 16); wood(cr, 0xd8963a, 0x8a5020, seed=7, rings=3); cr[0:2] = cr[-2:] = hexrgb(0x6a3a18); cr[:, 0:2] = cr[:, -2:] = hexrgb(0x6a3a18)
    px_line(cr, 1, 1, 14, 14, 0x6a3a18, 1.5); R['crate'] = S.rect(112, 80, 16, 16, 1)
    for k, (nm, c) in enumerate((('sand', 0xffd890), ('grass', 0x7dff4f), ('mann', 0xfff2e6), ('gun', 0x2a2430), ('tracer', 0xffffa0),
                                 ('cactus', 0x39c46a), ('leaf', 0x5fe85a), ('roof', 0xff5a5a), ('loot', 0xff4fd8), ('teamA', 0xff7ad8),
                                 ('teamB', 0x5fe8ff), ('trunk', 0xb87a40), ('conc', 0xb8b0c8), ('hazard', 0xffe14d), ('fount', 0x9ff5ff), ('dark', 0x2a1a3a))):
        R[nm] = S.fill((k % 8) * 16, 96 + (k // 8) * 16, 16, 16, c)
    # --- glow atlas: the header lightbox, the LCD, LEDs, the medallion
    G = Atlas('mc_glow_t', 256, 64)
    lg = G.sub(0, 0, 256, 40); crust(lg, 0xff2fbf, 0.04, seed=8)
    lg[0:3] = lg[-3:] = hexrgb(0xffe8f8); lg[:, 0:3] = lg[:, -3:] = hexrgb(0xffe8f8)
    smiley(lg, 62, 20, 15, face=0xffe14d, ink=INK)
    text_px(lg, 'CORP', 89, 4, 5, 0x6a0050); text_px(lg, 'CORP', 88, 3, 5, 0xffffff)
    for x in range(10, 250, 9): lg[35:37, x:x + 4] = hexrgb(0xffe14d)  # a dotted rule under it
    lg[6:30, 222:224] = hexrgb(0x9a1080)  # a dead tube
    lcd = G.sub(0, 40, 64, 24); lcd[:] = hexrgb(0x061a08)
    seg7(lcd, '17:30', 4, 3, 9, 13, 2, GREEN, gap=3, ghost=0x0e3010)
    write(lcd, 'insert life', 1, 17, 1, 0x9fff7a)
    R['logo'] = G.rect(0, 0, 256, 40); R['lcd'] = G.rect(0, 40, 64, 24)
    R['led_g'] = G.fill(64, 40, 8, 8, GREEN); R['led_r'] = G.fill(72, 40, 8, 8, RED); R['led_p'] = G.fill(64, 48, 8, 8, 0xff6fd8)
    md = G.sub(80, 40, 24, 24); md[:] = hexrgb(0xffe14d); smiley(md, 12, 12, 11.5, face=0xffe14d, ink=INK); R['medal'] = G.rect(80, 40, 24, 24)
    R['warm'] = G.fill(104, 40, 8, 8, 0xfff0c0)
    # --- decal atlas: the control panel, keys, stickers, tape, signs, patches, rubber
    D = Atlas('mc_decal_t', 256)
    pn = D.sub(0, 0, 64, 200); crust(pn, 0x2e2a36, 0.05, seed=9)
    pn[:, ::3] *= 0.92
    def at(y): return int((WIN[3] + 0.0 - y) / 4.1 * 200)  # panel row for a world height
    write(pn, 'coin', 6, at(4.9), 1, 0xffffff); write(pn, 'bills', 34, at(4.9), 1, 0xffffff)
    write(pn, 'select', 14, at(4.17), 1, 0xffffff)
    write(pn, 'CHANGE', 14, at(2.25), 1, 0xffe14d)
    px_line(pn, 8, at(2.95), 16, at(2.75), 0xff4fd8, 2); px_line(pn, 16, at(2.75), 13, at(2.83), 0xff4fd8, 2)
    write(pn, 'the', 2, at(3.08), 1, 0xff4fd8, wob=1, seed=2); write(pn, 'button', 2, at(3.08) + 8, 1, 0xff4fd8, wob=1, seed=3)
    for k in range(6): px_line(pn, rr.uniform(0, 64), rr.uniform(0, 200), rr.uniform(0, 64), rr.uniform(0, 200), 0x4a4652, 1)
    R['panel'] = D.rect(0, 0, 64, 200)
    keys = '123456789*0#'
    for k, ch in enumerate(keys):
        x, y = 64 + (k % 4) * 16, (k // 4) * 16
        kb = D.sub(x, y, 16, 16); crust(kb, 0xdcdce4, 0.04, seed=k); kb[0] = kb[:, 0] = hexrgb(0xffffff); kb[-1] = kb[:, -1] = hexrgb(0x9a9aa6)
        text_px(kb, ch, 6, 4, 1, INK) if ch not in '*#' else text_px(kb, ch, 6, 4, 1, 0xff3030)
        R['key' + ch] = D.rect(x, y, 16, 16, 1)
    sg = D.sub(128, 0, 128, 56); crust(sg, 0xc89a5a, 0.08, seed=10, speck=0x8a6030, p=0.05)
    sg[0:2] = sg[-2:] = hexrgb(0xa07840)
    write(sg, 'do not', 10, 6, 2, INK, wob=1, seed=4, bold=True)
    write(sg, 'unplug.', 10, 22, 2, INK, wob=1, seed=5, bold=True)
    write(sg, 'ever.', 52, 38, 2, 0xd01830, wob=2, seed=6, bold=True)
    px_line(sg, 50, 53, 114, 51, 0xd01830, 1.6)
    R['sign'] = D.rect(128, 0, 128, 56)
    st = D.sub(64, 48, 32, 32); st[:] = hexrgb(0xffffff); smiley(st, 16, 16, 14, face=0xffe14d, ink=INK); R['st_smile'] = D.rect(64, 48, 32, 32)
    tiedye(D.sub(96, 48, 32, 32), DYE, seed=5, arms=3, twist=8); R['st_dye'] = D.rect(96, 48, 32, 32)
    nr = D.sub(128, 56, 64, 24); nr[:] = hexrgb(0xff3030); nr[2:-2, 2:-2] = hexrgb(0xffffff); write(nr, 'NO REFUNDS', 3, 9, 1, 0xff3030); R['st_norefund'] = D.rect(128, 56, 64, 24)
    tt = D.sub(192, 56, 64, 24); tt[:] = hexrgb(0x111118); seg7(tt, '17:30', 4, 4, 8, 16, 2, 0xffe14d, gap=3); R['st_1730'] = D.rect(192, 56, 64, 24)
    lv = D.sub(128, 80, 64, 24); crust(lv, 0x5fd3c6, 0.04, seed=11); write(lv, 'the bottom', 3, 3, 1, INK); heart(lv, 32, 16, 3, 0xff4fd8); R['st_love'] = D.rect(128, 80, 64, 24)
    tp = D.sub(192, 80, 16, 16); crust(tp, 0xb8bcc6, 0.08, seed=12); tp[::3] *= 0.92; R['tape'] = D.rect(192, 80, 16, 16, 1)
    R['rubber'] = D.fill(208, 80, 16, 16, 0x18161c); R['red'] = D.fill(224, 80, 16, 16, 0xff2030); R['jred'] = D.fill(240, 80, 16, 16, 0xd82020)
    bt = D.sub(64, 80, 64, 24); crust(bt, 0x1e1c22, 0.05, seed=13); bt[0:6] = hexrgb(0xffe14d); write(bt, 'MAX AMP', 6, 10, 1, 0xffe14d); R['battery'] = D.rect(64, 80, 64, 24)
    for k, (c, nm) in enumerate(((0x3fd6c6, 'patch_teal'), (0xffd84a, 'patch_yel'))):
        p = D.sub(k * 32, 200, 32, 32); crust(p, c, 0.08, seed=14 + k, speck=0x9a5a3a, p=0.03)
        for x in (2, 29):
            for y in range(2, 32, 6): px_disc(p, x + 0.5, y + 0.5, 1.2, 0xe8e8f0)
        for y in (2, 29):
            for x in range(2, 32, 6): px_disc(p, x + 0.5, y + 0.5, 1.2, 0xe8e8f0)
        R[nm] = D.rect(k * 32, 200, 32, 32)
    fl = D.sub(64, 104, 128, 48); crust(fl, 0x2a2236, 0.05, seed=16)
    for k in range(7): px_line(fl, rr.uniform(0, 128), rr.uniform(0, 48), rr.uniform(0, 128), rr.uniform(0, 48), 0x5a4e6a, 1)
    text_px(fl, 'PUSH', 52, 8, 2, 0xffffff); smiley(fl, 40, 14, 6, face=0xffe14d, ink=INK)
    write(fl, 'thanks 4 ur loyalty', 7, 30, 1, 0xff8ad8)
    fl[42:45, 10:118] = hexrgb(0x4a3e5a)
    R['flap'] = D.rect(64, 104, 128, 48)
    gr = D.sub(192, 104, 64, 16); gr[:] = hexrgb(0x1a1820); gr[3:13, 1::4] = hexrgb(0x6a6676); gr[3:13, 2::4] = hexrgb(0x4a4656); R['grille'] = D.rect(192, 104, 64, 16)
    sh = D.sub(192, 120, 64, 16); crust(sh, 0x9aa0b4, 0.06, seed=17); sh[0:2] = hexrgb(0xe8ecf4); R['shelf'] = D.rect(192, 120, 64, 16)
    ps = D.sub(64, 152, 192, 16); ps[:] = hexrgb(0xffffff)
    for k, c in enumerate((0xff4fd8, 0x3fa8ff, 0x39c46a, 0xff3030, 0xffb020, 0x3fd6c6, 0xb48cff, 0xff8a3a)):
        x = k * 24; ps[:, x] = hexrgb(0xb0b0b8); text_px(ps, 'ABCDEFGH'[k % 8] + str(k % 3 + 1), x + 3, 5, 1, INK); ps[4:12, x + 16:x + 21] = hexrgb(c)
    R['price'] = D.rect(64, 152, 192, 16)
    lab = D.sub(64, 168, 64, 16); crust(lab, 0xb8bcc6, 0.06, seed=18); write(lab, 'dale only', 4, 4, 1, 0xd01830, wob=1, seed=9); R['daleonly'] = D.rect(64, 168, 64, 16)
    mt = D.sub(128, 168, 32, 16); crust(mt, 0x4a4656, 0.06, seed=19); R['motor'] = D.rect(128, 168, 32, 16, 1)
    br = D.sub(160, 168, 32, 16); crust(br, 0xd86a4a, 0.1, seed=20, speck=0x9a3a2a, p=0.1); br[7] = hexrgb(0xe8d8c8); R['brick'] = D.rect(160, 168, 32, 16)
    rc = D.sub(192, 168, 32, 32); crust(rc, 0xfbfaf4, 0.03, seed=21)
    for y in range(4, 30, 4): rc[y, 3:29 - (y * 7) % 9] = hexrgb(0x8a8a96)
    write(rc, 'x1', 3, 22, 1, 0xff3030); R['receipt'] = D.rect(192, 168, 32, 32)
    R['grey'] = D.fill(224, 168, 16, 16, 0x6a6676); R['plug'] = D.fill(240, 168, 16, 16, 0xf0ece4)
    bs = D.sub(64, 200, 56, 56); crust(bs, 0xff4fd0, 0.05, seed=31); px_disc(bs, 28, 28, 27, 0xffe8f6); px_disc(bs, 28, 28, 24.5, 0xffc8ec)
    smiley(bs, 28, 28, 22, face=0xffe8a0, ink=0x9a1878); grime(bs, 0xff4fd0, 0.3, seed=5, blob=5)
    for k in range(5): px_line(bs, rr.uniform(0, 56), rr.uniform(0, 56), rr.uniform(0, 56), rr.uniform(0, 56), 0xff4fd0, 1.5)
    R['bigsmile'] = D.rect(64, 200, 56, 56)
    cs = D.sub(120, 200, 72, 20); crust(cs, 0xff4fd0, 0.05, seed=32); text_px(cs, 'CORP', 12, 3, 2, 0xffe8f6); grime(cs, 0xff4fd0, 0.3, seed=6, blob=3); R['sidecorp'] = D.rect(120, 200, 72, 20)
    return S, G, D, R


def mannequin(hip, rot, m, R, team, pose='aim', gun=True, s=1.0):
    """a 0.34 m sim fighter (the PvP mannequin): pelvis, torso, ball head, jointed limbs with the wrong knee, a rifle.
    built round its hip, then turned by rot (three euler) and moved to hip."""
    P = []
    sk = R['mann']; tm = R[team]
    def rodp(a, b, r=0.011): return fit(rod(a, b, r * s, m, seg=4), sk)
    sc = lambda p: tuple(v * s for v in p)
    P.append(fit(box(sc((0.07, 0.05, 0.04)), (0, 0, 0), m), tm))
    P.append(fit(box(sc((0.08, 0.11, 0.045)), sc((0, 0.08, 0)), m, rot=(0.08, 0, 0)), tm))
    P.append(fit(ball(0.03 * s, sc((0, 0.17, -0.005)), m, seg=6, rings=4), sk))
    L = {'aim': [((-0.025, -0.02, 0), (-0.04, -0.09, -0.03), (-0.035, -0.17, 0.0)), ((0.025, -0.02, 0), (0.05, -0.085, 0.02), (0.06, -0.17, 0.04))],
         'fly': [((-0.025, -0.02, 0), (-0.07, -0.07, -0.04), (-0.1, -0.12, -0.08)), ((0.025, -0.02, 0), (0.08, -0.06, 0.03), (0.07, -0.13, 0.08))],
         'crouch': [((-0.025, -0.02, 0), (-0.04, -0.04, -0.08), (-0.04, -0.12, -0.04)), ((0.025, -0.02, 0), (0.04, -0.09, 0.03), (0.04, -0.12, 0.07))]}[pose]
    A = {'aim': [((-0.05, 0.12, 0), (-0.03, 0.09, -0.06), (0.0, 0.1, -0.11)), ((0.05, 0.12, 0), (0.04, 0.08, -0.04), (0.01, 0.1, -0.09))],
         'fly': [((-0.05, 0.12, 0), (-0.11, 0.17, -0.01), (-0.15, 0.24, 0.02)), ((0.05, 0.12, 0), (0.1, 0.19, 0.0), (0.12, 0.27, 0.03))],
         'crouch': [((-0.05, 0.12, 0), (-0.04, 0.08, -0.05), (-0.01, 0.09, -0.1)), ((0.05, 0.12, 0), (0.05, 0.08, -0.04), (0.02, 0.09, -0.09))]}[pose]
    for a, b, c in L + A: P.append(rodp(sc(a), sc(b))); P.append(rodp(sc(b), sc(c)))
    if gun:
        P.append(fit(box(sc((0.018, 0.026, 0.13)), sc((0.005, 0.1, -0.12)), m), R['gun']))
    xform(P, rot=rot, move=hip)
    return P


def build_machine():
    S, G, D, R = mc_atlases()
    candy_px = np.zeros((128, 128, 3), np.float32); crust(candy_px, 0xff4fd0, 0.04, seed=31, speck=[(0xffd6f2, 0.004), (0x9a3a2a, 0.004), (0xd8309a, 0.03)], block=4)
    r_ = np.random.default_rng(3)
    for k in range(4): x, y = r_.uniform(0, 128), r_.uniform(0, 128); px_line(candy_px, x, y, x + r_.uniform(-14, 14), y + r_.uniform(-6, 6), 0xffa8e4, 1)
    for k in range(4):  # rust blooms with drips, chipped primer
        x, y = int(r_.uniform(4, 120)), int(r_.uniform(4, 110)); px_disc(candy_px, x, y, 2.6, 0xb0502a); drip(candy_px, x, y, int(r_.uniform(5, 14)), 0xb0502a)
        px_disc(candy_px, int(r_.uniform(4, 120)), int(r_.uniform(4, 120)), 1.8, 0xffe0f4)
    candy = mat('mc_candy', 0xffffff, rough=0.2, clearcoat=1.0, tex=lib._image('mc_candy_t', candy_px))
    chrome = plain('mc_chrome', 0xe4e8f2, rough=0.12, metal=1.0, var=0.05, seed=32)
    glass = mat('mc_glass', 0xbff4ff, rough=0.04, alpha=0.13, clearcoat=1.0)
    sim = mat('mc_sim', 0xffffff, rough=0.4, tex=S.image(), emit=0xffffff, strength=1.4, emit_tex=True)
    glow = mat('mc_glow', 0xffffff, rough=0.2, tex=G.image(), emit=0xffffff, strength=3.0, emit_tex=True)
    decal = mat('mc_decal', 0xffffff, rough=0.32, clearcoat=0.5, tex=D.image())
    O = []; L = []
    T = lambda objs: tiled(objs, 2.0)
    # --- the cabinet: dented, then the window and the tray cut in, then bevelled so the gloss catches
    body = box((MW, 5.72, MD), (0, 0.3 + 2.86, 0), candy, name='cabinet')
    subdiv(body, 5)
    dent(body, (-MW / 2, 1.0, -1.0), 0.55, 0.1); dent(body, (-MW / 2, 5.7, 1.1), 0.5, 0.06)
    dent(body, (MW / 2, 2.4, 0.7), 0.7, 0.1); dent(body, (1.2, 3.0, MD / 2), 0.9, 0.1)
    cut(body, box((WIN[1] - WIN[0], WIN[3] - WIN[2], 2.8), (WCX, (WIN[2] + WIN[3]) / 2, FZ), None))
    cut(body, box((TRAY[1] - TRAY[0], TRAY[3] - TRAY[2], 2.2), ((TRAY[0] + TRAY[1]) / 2, (TRAY[2] + TRAY[3]) / 2, FZ), None))
    bevel(body, 0.05, 2); O.append(body)
    hw, hr = MW / 2 + 0.06, 0.62  # the header: rounded shoulders seen from the front (the 50s machine silhouette)
    prof = [(-hw, 5.95)] + [(-hw + hr - math.cos(math.radians(a)) * hr, 6.8 - hr + math.sin(math.radians(a)) * hr) for a in range(0, 91, 15)]
    prof += [(hw - hr + math.cos(math.radians(a)) * hr, 6.8 - hr + math.sin(math.radians(a)) * hr) for a in range(90, -1, -15)] + [(hw, 5.95)]
    O.append(side_x(prof, MD + 0.12, (0, 0, 0), candy, bev=0.05, seg=2))
    O.append(box((MW + 0.06, 0.09, MD + 0.06), (0, 5.985, 0), chrome, bev=0.02, seg=1))
    O.append(box((MW - 0.6, 0.29, MD - 0.6), (0, 0.175, 0), decal, bev=0.02, seg=1))
    T(O[:3]); fit(O[3], R['grille'])
    for sx in (-1, 1):
        for sz in (-1, 1):
            O.append(box((0.11, 5.66, 0.11), (sx * MW / 2, 3.16, sz * MD / 2), chrome, bev=0.025, seg=1))  # corner guards
            O.append(lathe([(0.0, 0.0), (0.22, 0.0), (0.22, 0.05), (0.14, 0.12), (0.11, 0.345), (0.0, 0.345)], (sx * (MW / 2 - 0.32), 0, sz * (MD / 2 - 0.32)), chrome, seg=10, axis='y'))
    # the lit header: lightbox face, chrome lip, and the old ☺ medallion hanging off one bolt
    O.append(fit(box((4.9, 0.5, 0.08), (0, 6.36, FZ - 0.07), glow, bev=0.015, seg=1), R['logo'], mode='front'))
    for y in (6.09, 6.63): O.append(box((5.0, 0.04, 0.12), (0, y, FZ - 0.07), chrome, bev=0.01, seg=1))
    md = cyl(0.44, 0.12, (-2.35, 6.36, FZ - 0.18), glow, axis='z', seg=24, rot=(0, 0, 0.21))
    multi_mat(md, [glow, chrome], lambda n, c: 0 if n[2] < -0.9 else 1); uv_fit(md, R['medal'], mode='front', only={0}); uv_fit(md, (0.95, 0.95, 0.99, 0.99), only={1})
    O.append(md)
    O.append(BK.torus(0.45, 0.03, (-2.35, 6.36, FZ - 0.18), chrome, axis='z', seg=24, sides=4))
    O.append(cyl(0.05, 0.2, (-2.35, 6.36, FZ - 0.1), chrome, axis='z', seg=8))
    # --- the window: chrome frame, glass, the sim sky at the back, four shelves with price rails
    x0, x1, y0, y1 = WIN
    for (w, h, cx, cy) in ((x1 - x0 + 0.2, 0.1, WCX, y1 + 0.03), (x1 - x0 + 0.2, 0.1, WCX, y0 - 0.03), (0.1, y1 - y0, x0 - 0.03, (y0 + y1) / 2), (0.1, y1 - y0, x1 + 0.03, (y0 + y1) / 2)):
        O.append(box((w, h, 0.07), (cx, cy, FZ - 0.025), chrome, bev=0.02, seg=1))
    O.append(box((x1 - x0 + 0.02, y1 - y0 + 0.02, 0.03), (WCX, (y0 + y1) / 2, FZ + 0.015), glass, name='glass'))
    shelves = [y0, 2.75, 3.75, 4.75]
    for k, (a, b) in enumerate(zip(shelves, shelves[1:] + [y1])):
        r_s = R['sky2' if k % 2 else 'sky']
        if k >= 2: r_s = (r_s[2], r_s[1], r_s[0], r_s[3])  # mirrored: every shelf's sun sits somewhere else
        O.append(fit(box((x1 - x0 + 0.01, b - a, 0.04), (WCX, (a + b) / 2, -0.21), sim), r_s, mode='front'))
    for sy in shelves:
        if sy > y0: O.append(fit(box((x1 - x0 + 0.02, 0.05, 1.32), (WCX, sy, -0.86), decal), R['shelf']))
        O.append(fit(box((x1 - x0 - 0.02, 0.1, 0.03), (WCX, sy + 0.04, -1.52), decal), R['price'], mode='front'))
    # spiral coils (the vending part), each driven by a little motor box on the back wall
    def coil(x, sy, item=None):
        cy = sy + 0.025 + 0.17
        O.append(tube(helix((x, cy, -1.44), (x, cy, -0.3), 0.16, 5, per=5), 0.013, chrome, seg=4, name='coil'))
        O.append(fit(box((0.2, 0.2, 0.12), (x, cy, -0.26), decal), R['motor']))
    coil(-0.75, y0); coil(-0.3, y0); coil(2.3, 2.75); coil(2.3, 3.75); coil(2.3, 4.75)
    # loot capsules in the row-1 coils (what the sims pay out)
    for x, z in ((-0.75, -1.1), (-0.3, -0.75)):
        O.append(fit(ball(0.12, (x, y0 + 0.025 + 0.12, z), sim, seg=8, rings=6), R['loot']))
        O.append(fit(cyl(0.125, 0.03, (x, y0 + 0.025 + 0.12, z), sim, axis='y', seg=8), R['hazard']))
    # --- the sims on the shelves (all glowing: they're the only lit world left)
    def tilt_row(r0, sy, t, xa, xb):  # high shelves lean toward you (you look up at them from 1.7 m) on a wedge stand
        f = sy + 0.025
        xform(O[r0:], rot=(-t, 0, 0), pivot=(0, f, -1.45))
        O.append(fit(side([(-1.45, f - 0.005), (-0.44, f - 0.005), (-0.44, f + math.sin(t) * 1.0 + 0.01)], xb - xa, ((xa + xb) / 2, 0, 0), decal), R['motor']))
    def base(xa, xb, sy, sw, h=0.07):
        return fit(box((xb - xa, h, 1.0), ((xa + xb) / 2, sy + 0.025 + h / 2, -0.95), sim, bev=0.01, seg=1), R[sw])
    # row 1: DEAD MALL (checker floor, fountain, a shopfront, the escalator, Todd floating upside down)
    sy = y0; Y = sy + 0.025 + 0.07
    O.append(base(0.05, 2.45, sy, 'tile'))
    O.append(fit(lathe([(0.0, Y), (0.26, Y), (0.27, Y + 0.08), (0.22, Y + 0.08), (0.05, Y + 0.09), (0.05, Y + 0.28), (0.13, Y + 0.3), (0.12, Y + 0.33), (0.0, Y + 0.33)],
                       (0.85, 0, -0.95), sim, seg=10, axis='y'), R['conc']))
    O.append(fit(cyl(0.22, 0.02, (0.85, Y + 0.07, -0.95), sim, axis='y', seg=10), R['fount']))
    O.append(fit(box((0.7, 0.55, 0.12), (1.85, Y + 0.275, -0.6), sim), R['b_white']))
    O.append(fit(box((0.5, 0.1, 0.03), (1.85, Y + 0.45, -0.68), sim), R['roof']))
    esc = box((0.28, 0.06, 0.75), (1.45, Y + 0.22, -1.0), sim, rot=(0.55, 0, 0)); O.append(fit(esc, R['dark']))
    O += mannequin((0.85, Y + 0.62, -0.95), (math.pi, 0.4, 0.2), sim, R, 'teamB', pose='fly', gun=False)
    O.append(fit(cyl(0.035, 0.14, (0.85, Y + 0.39, -0.95), sim, axis='y', seg=6, r2=0.02), R['fount']))  # the fountain holds Todd up
    # row 2: THE FIGHT in the warehouse (crates, three fighters, a tracer, a muzzle flash)
    sy = 2.75; Y = sy + 0.025 + 0.07; r0 = len(O)
    O.append(base(-0.95, 1.95, sy, 'conc'))
    O.append(fit(box((2.9, 0.012, 0.06), (0.5, Y + 0.004, -1.42), sim), R['hazard']))
    for (cx, cy, cz, s_, a) in ((1.45, 0.14, -0.85, 0.28, 0.1), (1.45, 0.42, -0.85, 0.28, -0.15), (1.1, 0.12, -0.7, 0.24, 0.3), (-0.6, 0.12, -0.6, 0.24, 0.5)):
        O.append(fit(box((s_, s_, s_), (cx, Y + cy, cz), sim, bev=0.012, seg=1, rot=(0, a, 0)), R['crate']))
    O += mannequin((0.05, Y + 0.17, -1.05), (0, 0.5, 0), sim, R, 'teamA', pose='aim')
    O += mannequin((-0.62, Y + 0.33, -1.0), (0.3, -0.6, 0.9), sim, R, 'teamB', pose='fly')
    O += mannequin((1.05, Y + 0.12, -1.15), (0, -0.6, 0), sim, R, 'teamB', pose='crouch')
    O.append(fit(rod((-0.03, Y + 0.27, -1.18), (-0.55, Y + 0.36, -1.02), 0.008, sim, seg=4), R['tracer']))
    for a in (0.0, 1.0):
        O.append(fit(box((0.07, 0.012, 0.012), (-0.02, Y + 0.27, -1.19), sim, rot=(0, 0.5, a)), R['tracer']))
    tilt_row(r0, sy, 0.18, -0.95, 1.95)
    # row 3: TINY ISLANDS (water, three islands, a palm, a shark) and a DESERT (dunes, cacti)
    sy = 3.75; Y = sy + 0.025 + 0.05; r0 = len(O)
    O.append(base(-0.95, 0.85, sy, 'water', h=0.05))
    for (ix, iz, r_i) in ((-0.55, -1.0, 0.24), (0.2, -0.75, 0.3), (0.55, -1.25, 0.14)):
        isl = ball(r_i, (ix, Y, iz), sim, scale=(1, 0.32, 1), seg=8, rings=5); jitter(isl, 0.015, seed=int(ix * 10) + 30); O.append(fit(isl, R['sand']))
        O.append(fit(ball(r_i * 0.6, (ix, Y + r_i * 0.2, iz), sim, scale=(1, 0.35, 1), seg=6, rings=4), R['grass']))
    tr = sweep([(0.2, Y + 0.05, -0.75), (0.23, Y + 0.2, -0.78), (0.29, Y + 0.36, -0.8)], [0.022, 0.018, 0.014], sim, seg=5, name='palm')
    O.append(fit(tr, R['trunk']))
    for k in range(5):
        a = 2 * math.pi * k / 5
        O.append(fit(box((0.04, 0.008, 0.2), (0.29 + math.cos(a) * 0.08, Y + 0.34, -0.8 + math.sin(a) * 0.08), sim, rot=(0.35, -a + math.pi / 2, 0)), R['leaf']))
    O.append(fit(cyl(0.04, 0.07, (-0.3, Y + 0.02, -1.3), sim, axis='y', seg=4, r2=0.0, rot=(0, 0, 0.3)), R['dark']))
    O.append(base(0.95, 1.95, sy, 'sand', h=0.05))
    for (dx, dz, r_d) in ((1.25, -0.8, 0.3), (1.7, -1.15, 0.22)):
        O.append(fit(ball(r_d, (dx, Y, dz), sim, scale=(1.3, 0.35, 1), seg=8, rings=4), R['sand']))
    for (cx, cz, h) in ((1.45, -1.2, 0.36), (1.75, -0.7, 0.26)):
        O.append(fit(cyl(0.035, h, (cx, Y + h / 2, cz), sim, axis='y', seg=6), R['cactus']))
        O.append(fit(sweep([(cx + 0.03, Y + h * 0.5, cz), (cx + 0.09, Y + h * 0.5, cz), (cx + 0.09, Y + h * 0.78, cz)], 0.02, sim, seg=5), R['cactus']))
    tilt_row(r0, sy, 0.28, -0.95, 1.95)
    # row 4: THE CITY BLOCK (Jankburg in a box) and THE SUBURB
    sy = 4.75; Y = sy + 0.025 + 0.06; r0 = len(O)
    O.append(base(-0.95, 0.95, sy, 'road', h=0.06))
    rnd = random.Random(8)
    for k, (bx, bz) in enumerate(((-0.75, -0.65), (-0.45, -0.62), (-0.15, -0.68), (0.2, -0.6), (0.55, -0.66), (-0.6, -1.25), (0.4, -1.28))):
        h = rnd.uniform(0.28, 0.55) if bz > -1 else rnd.uniform(0.12, 0.24)
        w = rnd.uniform(0.2, 0.3)
        O.append(fit(box((w, h, 0.26), (bx, Y + h / 2, bz), sim), R[('b_teal', 'b_pink', 'b_yel', 'b_white')[k % 4]]))
    O.append(fit(cyl(0.05, 0.5, (0.82, Y + 0.25, -0.62), sim, axis='y', seg=6, r2=0.03), R['b_white']))
    O.append(fit(ball(0.06, (0.82, Y + 0.52, -0.62), sim, seg=6, rings=4), R['hazard']))
    O.append(base(1.05, 1.95, sy, 'grass', h=0.06))
    for (hx, hz) in ((1.3, -0.75), (1.72, -1.15)):
        O.append(fit(box((0.3, 0.2, 0.26), (hx, Y + 0.1, hz), sim), R['b_pink' if hx < 1.5 else 'b_yel']))
        roof = side([(-0.15, 0.0), (0.15, 0.0), (0.0, 0.13)], 0.34, (hx, Y + 0.2, hz), sim); O.append(fit(roof, R['roof']))
    for (tx, tz) in ((1.75, -0.6), (1.2, -1.25)):
        O.append(fit(cyl(0.09, 0.26, (tx, Y + 0.18, tz), sim, axis='y', seg=6, r2=0.0), R['leaf']))
        O.append(fit(cyl(0.015, 0.06, (tx, Y + 0.03, tz), sim, axis='y', seg=4), R['trunk']))
    tilt_row(r0, sy, 0.36, -0.95, 1.95)
    # --- the control column (the viewer's right): plate, LCD, coin slot, bill reader, keypad, THE button, CHANGE
    PZ = FZ - 0.02
    O.append(fit(box((1.3, 4.1, 0.05), (PCX, 3.75 - 0.05, PZ + 0.005), decal), R['panel'], mode='front'))
    PZ -= 0.02
    O.append(box((1.1, 0.52, 0.04), (PCX, 5.2, PZ - 0.01), chrome, bev=0.01, seg=1))
    O.append(fit(box((0.98, 0.42, 0.04), (PCX, 5.2, PZ - 0.03), glow), R['lcd'], mode='front'))
    O.append(box((0.32, 0.5, 0.08), (PCX + 0.3, 4.5, PZ - 0.03), chrome, bev=0.02, seg=1))
    O.append(fit(box((0.05, 0.3, 0.02), (PCX + 0.3, 4.5, PZ - 0.075), decal), R['rubber']))
    O.append(fit(box((0.55, 0.32, 0.16), (PCX - 0.3, 4.5, PZ - 0.07), decal, bev=0.02, seg=1), R['rubber']))
    O.append(fit(box((0.4, 0.035, 0.02), (PCX - 0.3, 4.45, PZ - 0.155), glow), R['led_g']))
    for k, ch in enumerate('123456789*0#'):
        cx = PCX + 0.3 - (k % 3) * 0.3; cy = 4.0 - (k // 3) * 0.26
        O.append(fit(box((0.24, 0.2, 0.07), (cx, cy, PZ - 0.025), decal, bev=0.02, seg=1), R['key' + ch], mode='front'))
    O.append(cyl(0.24, 0.06, (PCX, 2.55, PZ - 0.02), chrome, axis='z', seg=16, bev=0.01))
    O.append(fit(lathe([(0.0, -0.33), (0.1, -0.325), (0.17, -0.3), (0.2, -0.25), (0.2, -0.2), (0.14, -0.18), (0.14, -0.04)], (PCX, 2.55, PZ), decal, seg=16, axis='z'), R['red']))
    O.append(fit(box((0.5, 0.1, 0.006), (PCX + 0.05, 2.18, PZ - 0.003), decal, rot=(0, 0, -0.05)), R['daleonly'], mode='front'))
    O.append(box((0.5, 0.3, 0.2), (PCX, 1.86, PZ - 0.08), chrome, bev=0.03, seg=2))
    O.append(fit(box((0.4, 0.18, 0.02), (PCX, 1.88, PZ - 0.185), decal), R['rubber']))
    # --- the tray you get dispensed from: chrome lips, a pink-lit ceiling, the flap hanging open, a capsule inside
    tx0, tx1, ty0, ty1 = TRAY; tcx = (tx0 + tx1) / 2
    for (w, h, cx, cy) in ((tx1 - tx0 + 0.2, 0.1, tcx, ty1 + 0.03), (tx1 - tx0 + 0.2, 0.12, tcx, ty0 - 0.03), (0.1, ty1 - ty0, tx0 - 0.03, (ty0 + ty1) / 2), (0.1, ty1 - ty0, tx1 + 0.03, (ty0 + ty1) / 2)):
        O.append(box((w, h, 0.09), (cx, cy, FZ - 0.03), chrome, bev=0.025, seg=1))
    O.append(fit(box((tx1 - tx0 - 0.02, 0.04, 1.0), (tcx, ty1 - 0.005, -1.0), glow), R['led_p']))
    O.append(fit(box((tx1 - tx0 + 0.01, 0.06, 1.1), (tcx, ty0 + 0.02, -1.05), decal, rot=(-0.08, 0, 0)), R['rubber']))
    hinge = (tcx, ty1 - 0.02, FZ + 0.02)
    O.append(cyl(0.035, tx1 - tx0 - 0.05, hinge, chrome, axis='x', seg=8))
    fl = box((tx1 - tx0 - 0.08, 0.94, 0.05), (tcx, ty1 - 0.02 - 0.47, FZ + 0.02), decal, bev=0.015, seg=1, name='flap')
    subdiv(fl, 2); dent(fl, (tcx + 0.6, ty0 + 0.4, FZ), 0.35, 0.04); fit(fl, R['flap'], mode='front')
    xform([fl], rot=(0.42, 0, 0.035), pivot=hinge); O.append(fl)
    O.append(fit(ball(0.16, (tcx - 0.7, ty0 + 0.17, -1.0), sim, seg=8, rings=6), R['loot']))
    O.append(fit(box((0.3, 0.005, 0.4), (tcx + 0.4, ty0 + 0.06, -1.1), decal, rot=(0.0, 0.4, 0.05)), R['receipt']))
    # --- decades of repair: patches, tape, stickers, the sign, cables, a battery bank
    O.append(fit(box((1.3, 1.0, 0.03), (PCX + 0.05, 0.92, FZ - 0.008), decal, rot=(0, 0, 0.05)), R['patch_teal'], mode='front'))
    O.append(fit(box((0.03, 1.4, 1.2), (-MW / 2 - 0.008, 2.3, 0.9), decal, rot=(0.06, 0, 0)), R['patch_yel']))
    O.append(fit(box((0.03, 0.9, 0.8), (MW / 2 + 0.008, 4.7, 0.6), decal, rot=(-0.1, 0, 0)), R['patch_teal']))
    for a in (0.7, -0.7):  # duct-tape X over the right-side dent... and a crack in the glass
        O.append(fit(box((0.006, 0.12, 1.0), (MW / 2 + 0.003, 2.4, 0.7), decal, rot=(a, 0, 0)), R['tape']))
    for k, (cx, cy, a, L_) in enumerate(((1.95, 4.45, 0.6, 0.9), (2.2, 4.2, -0.3, 0.6), (1.75, 4.15, 1.2, 0.5))):
        O.append(fit(box((L_, 0.1, 0.006), (cx, cy, FZ - 0.003 - 0.0015 * k), decal, rot=(0, 0, a)), R['tape']))
    SX, SY = -0.45, 2.3  # the sign, taped on the glass at eye height over the loot coils
    sgn = fit(box((1.1, 0.48, 0.012), (SX, SY, FZ - 0.004), decal, rot=(0, 0, -0.07)), R['sign'], mode='front'); O.append(sgn)
    for (dx, dy) in ((-0.5, 0.25), (0.5, 0.21), (-0.52, -0.2), (0.48, -0.25)):
        O.append(fit(box((0.2, 0.07, 0.004), (SX + dx, SY + dy, FZ - 0.011), decal, rot=(0, 0, 0.7 if dx * dy < 0 else -0.6)), R['tape']))
    for (rect, w, h, pos, a) in (('st_smile', 0.36, 0.36, (2.1, 4.95, FZ + 0.0), 0.2), ('st_norefund', 0.4, 0.15, (0.4, 1.6, FZ + 0.0), -0.08),
                                 ('st_1730', 0.5, 0.2, (PCX - 0.3, 5.6, FZ - 0.042), 0.1), ('st_love', 0.5, 0.2, (PCX + 0.2, 1.1, FZ - 0.0245), -0.12)):
        if pos[2] == FZ + 0.0: pos = (pos[0], pos[1], FZ - 0.002)  # on the glass / the cabinet
        O.append(fit(box((w, h, 0.005), pos, decal, rot=(0, 0, a)), R[rect], mode='front'))
    O.append(fit(box((0.005, 0.5, 0.5), (-MW / 2 - 0.0, 2.3, -0.9), decal, rot=(0.3, 0, 0)), R['st_dye']))
    O.append(fit(cyl(1.15, 0.006, (-MW / 2, 4.35, 0.1), decal, axis='x', seg=24), R['bigsmile']))  # the faded ☺ on the flank
    O.append(fit(box((0.006, 0.42, 1.5), (-MW / 2, 2.95, 0.1), decal), R['sidecorp']))
    O.append(fit(box((2.4, 0.6, 0.03), (0.6, 5.1, MD / 2), decal), R['grille']))  # the back: vents, a service hatch, a rear sticker
    O.append(fit(box((1.6, 2.2, 0.03), (-1.1, 2.4, MD / 2 + 0.004), decal, rot=(0, 0, 0.03)), R['patch_teal']))
    O.append(fit(box((0.7, 0.28, 0.005), (1.4, 1.5, MD / 2), decal, rot=(0, 0, -0.1)), R['st_norefund']))
    O.append(fit(box((0.005, 0.25, 0.62), (MW / 2 + 0.0, 5.4, -0.6), decal, rot=(-0.05, 0, 0)), R['st_1730']))
    O.append(fit(box((0.005, 0.25, 0.62), (MW / 2 + 0.0, 1.4, -0.9), decal, rot=(0.1, 0, 0)), R['st_love']))
    # power: a junction box on the right flank, three fat cables to the floor and off to the depot wall, tape bands
    jb = fit(box((0.14, 0.6, 0.5), (MW / 2 + 0.06, 3.4, 0.4), decal, bev=0.02, seg=1), R['grey']); O.append(jb)
    cabs = []
    for k, (dz, sag) in enumerate(((-0.12, 0.0), (0.02, 0.1), (0.16, 0.05))):
        pts = [(MW / 2 + 0.12, 3.2, 0.4 + dz), (MW / 2 + 0.3 + 0.04 * k, 2.9, 0.42 + dz), (MW / 2 + 0.42 + 0.05 * k, 1.6, 0.5 + dz),
               (MW / 2 + 0.5 + 0.06 * k, 0.4, 0.7 + dz), (MW / 2 + 0.6 + 0.05 * k, 0.06 + 0.005 * k, 1.2 + dz), (MW / 2 + 0.75, 0.06 + 0.005 * k, 1.9 + dz * 1.5),
               (MW / 2 + 0.3 - 0.1 * k, 0.06 + 0.005 * k, 2.4 + dz)]
        c = tube(pts, 0.06, decal, seg=6, name='cable'); fit(c, R['rubber']); cabs.append(c); O.append(c)
        for t in (2, 3): O.append(fit(cyl(0.075, 0.16, pts[t], decal, axis='y', seg=6), R['tape']))
    O.append(fit(box((0.9, 0.12, 0.3), (MW / 2 + 0.2, 0.06, 2.45), decal, bev=0.02, seg=1, rot=(0, 0.3, 0)), R['plug']))
    # the battery bank (car batteries, jumper cables to the junction box)
    for k, (bx, by, bz, a) in enumerate(((MW / 2 + 0.45, 0.13, -0.9, 0.1), (MW / 2 + 0.45, 0.13, -0.45, -0.05), (MW / 2 + 0.47, 0.39, -0.68, 0.2))):
        O.append(fit(box((0.4, 0.26, 0.34), (bx, by, bz), decal, bev=0.015, seg=1, rot=(0, a, 0)), R['battery']))
        for s_, col in ((-1, 'jred'), (1, 'rubber')):
            tp_ = (bx + 0.08 * s_, by + 0.15, bz)
            O.append(fit(cyl(0.025, 0.05, tp_, decal, axis='y', seg=6), R['grey']))
            O.append(fit(tube(bend_path(tp_, (MW / 2 + 0.12, 3.25 + 0.05 * s_ + 0.02 * k, 0.2 + 0.04 * k), -0.6, n=6), 0.018, decal, seg=4, name='jumper'), R[col]))
    # a cable over the header to the medallion, taped down
    O.append(fit(tube([(-2.35, 6.42, FZ - 0.1), (-2.38, 6.7, FZ - 0.02), (-2.3, 6.835, -1.3), (-2.1, 6.835, 1.2), (-1.95, 6.7, MD / 2 + 0.08), (-1.85, 5.6, MD / 2 + 0.03)], 0.04, decal, seg=6), R['rubber']))
    for o in O:
        if o.data.materials and o.data.materials[0] == chrome: uv_tile(o, 1.0)
    meta = {'col': [MW, MH, MD], 'district': 'bottom', 'landmark': True,
            'lights': [[WCX, 3.75, FZ - 0.4, 0x4fd8ff], [0, 6.4, FZ - 0.5, 0xfff2c0], [(TRAY[0] + TRAY[1]) / 2, 0.95, FZ - 0.4, 0xff4fd8], [PCX, 4.6, FZ - 0.4, 0x39ff14]],
            'tray': [(TRAY[0] + TRAY[1]) / 2, TRAY[2], FZ - 0.4], 'terminal': [PCX, 1.5, FZ - 0.8], 'sign': 'do not unplug. ever.'}
    bpy.context.view_layer.update()
    meta['_lodpick'] = [o for o in O if 'coil' not in o.name and 'jumper' not in o.name and BK._diag(o) > 0.95 and (min(o.dimensions) > 0.045 or o.name.startswith('glass'))]
    return O, meta


# ================================================================================================ LOST & FOUND sign
# the depot's sign over its open front: 16 m of scaffold pipe bolted to the wall, marquee bulbs (half of them dead),
# and every letter salvaged from something else: a car door L, a tyre O, a pink neon S, a pallet T, a yellow neon &,
# a fridge-door F, a toilet-seat O, a horseshoe-magnet U, a corrugated-sheet N and a road-sign D.
# origin at the sign's centre, its back on the wall (z = 0), the front toward -z. seen from the front +x is on the
# viewer's left, so letters are laid out in viewer space (u right, v up) and placed with x = cx - u.

def cat_rom(pts, n=4):
    """smooth a polyline through its points (catmull-rom), n samples per span"""
    P = [Vector(p) for p in pts]; P = [P[0]] + P + [P[-1]]; out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t)))
    out.append(tuple(P[-2]))
    return out


def lf_atlas():
    A = Atlas('lf_salvage_t', 256)
    R = {}
    d = A.sub(0, 0, 64, 96); crust(d, 0x4fd8c8, 0.05, seed=41, speck=[(0xa0482a, 0.02), (0xd8fff4, 0.01)])  # car door teal
    d[40:42] = hexrgb(0x2a9a8a); grime(d, 0x8a4a2a, 0.08, seed=4, blob=6)
    for k in range(5): px_disc(d, 6 + k * 13, 84 + k % 2 * 6, 3.5 + k % 3, 0xb0582a); px_disc(d, 7 + k * 13, 85 + k % 2 * 6, 1.8, 0x7a3a1a)
    px_disc(d, 52, 30, 2, 0x3a3a40); d[29:31, 51:54] = hexrgb(0x8a8a90)  # keyhole
    R['door'] = A.rect(0, 0, 64, 96)
    f = A.sub(64, 0, 64, 96); crust(f, 0x8ff0c4, 0.03, seed=42, speck=0xa06a3a, p=0.01); f[0:2] = hexrgb(0xe8fff4)
    R['fridge'] = A.rect(64, 0, 64, 96)
    w = A.sub(128, 0, 64, 32); wood(w, 0xd8a868, 0x8a5a2a, seed=43, rings=4)
    for x in (6, 58): px_disc(w, x, 8, 1.2, 0x3a3a40); px_disc(w, x, 24, 1.2, 0x3a3a40)
    R['plank'] = A.rect(128, 0, 64, 32)
    c = A.sub(192, 0, 64, 64); crust(c, 0xc8ccd4, 0.06, seed=44)
    for x in range(0, 64, 8): c[:, x:x + 3] *= 0.82
    for k in range(6): xx = 4 + k * 10; c[0:20 + k * 5, xx:xx + 2] = hexrgb(0xb0602a)  # rust streaks
    c[26:36] = hexrgb(0xffb3c7)  # somebody's pink stripe
    R['corr'] = A.rect(192, 0, 64, 64)
    R['white'] = A.fill(128, 32, 16, 16, 0xfbfaf6); R['blue'] = A.fill(144, 32, 16, 16, 0x2a6ad8); R['red'] = A.fill(160, 32, 16, 16, 0xff2a3a)
    R['board'] = A.fill(176, 32, 16, 16, 0x2a1a34); R['deadbulb'] = A.fill(128, 48, 16, 16, 0x8a8698); R['seal'] = A.fill(144, 48, 16, 16, 0x1a181c)
    R['plate'] = A.fill(160, 48, 16, 16, 0xffe58a); R['string'] = A.fill(176, 48, 16, 16, 0xf0e6c8)
    t = A.sub(0, 96, 64, 32); crust(t, 0xd8b07a, 0.06, seed=45); t[:, 0:3] = hexrgb(0xb08850); px_disc(t, 7, 16, 3.5, 0xf8f0e0)
    write(t, 'returns:', 14, 5, 1, INK, wob=1, seed=2); write(t, 'never', 22, 17, 1, 0xd01830, wob=1, seed=3, bold=True)
    R['tag'] = A.rect(0, 96, 64, 32)
    sb = A.sub(64, 96, 64, 32); crust(sb, 0x2a6ad8, 0.04, seed=46); R['roadblue'] = A.rect(64, 96, 64, 32)
    return A, R


def build_lostfound_sign():
    A, R = lf_atlas()
    sal = mat('lf_salvage', 0xffffff, rough=0.3, clearcoat=0.7, tex=A.image())
    metal = plain('lf_metal', 0xc8ccd6, rough=0.28, metal=0.9, var=0.1, seed=47, speck=0x8a5a3a, p=0.03)
    rub = plain('lf_rubber', 0x2a282e, rough=0.85, var=0.12, seed=48, speck=0x5a5862, p=0.05)
    NE = Atlas('lf_neon_t', 16); pinkr = NE.fill(0, 0, 8, 16, 0xff5ad8); yelr = NE.fill(8, 0, 8, 16, 0xffe14d)
    neon = mat('lf_neon', 0xffffff, rough=0.15, tex=NE.image(), emit=0xffffff, strength=4.0, emit_tex=True)
    bulb = mat('lf_bulb', 0xfff0c0, rough=0.2, emit=0xffd27a, strength=6.0)
    O = []; rnd = random.Random(11)
    PZ, PY = -0.25, 1.15  # scaffold pipe line
    for y in (PY, -PY): O.append(cyl(0.05, 15.9, (0, y, PZ), metal, axis='x', seg=8))
    for x in (-7.6, -3.8, 0.0, 3.8, 7.6):  # uprights on wall plates
        O.append(box((0.07, 2.42, 0.07), (x, 0, PZ + 0.02), metal, bev=0.01, seg=1))
        O.append(box((0.3, 2.6, 0.02), (x, 0, -0.01), metal, bev=0.005, seg=1))
        for y in (PY, -PY): O.append(box((0.06, 0.06, 0.26), (x, y, -0.14), metal))
    # marquee bulbs along both pipes; half dead, two missing, one smashed
    xs = [-7.7 + 0.55 * k for k in range(29)]
    for row, y in enumerate((PY, -PY)):
        for k, x in enumerate(xs):
            O.append(cyl(0.035, 0.08, (x, y, PZ - 0.07), metal, axis='z', seg=5, cap=False))
            st = rnd.random()
            if (row, k) in ((0, 6), (1, 21)): continue
            if (row, k) == (0, 17):
                b = ball(0.05, (x, y, PZ - 0.14), sal, seg=6, rings=3, scale=(1, 1, 0.6)); jitter(b, 0.015, seed=3); O.append(fit(b, R['deadbulb'])); continue
            lit = st < 0.5
            b = ball(0.055, (x, y, PZ - 0.155), bulb if lit else sal, seg=6, rings=3)
            if not lit: fit(b, R['deadbulb'])
            O.append(b)
    # letters, left to right as read; x = cx - u
    widths = [1.1, 1.85, 1.15, 1.3, 1.1, 1.05, 1.45, 1.3, 1.25, 1.3]
    gaps = [0.12, 0.12, 0.12, 0.35, 0.35, 0.12, 0.12, 0.12, 0.12]
    tot = sum(widths) + sum(gaps); u = -tot / 2; C = []
    for k, w in enumerate(widths):
        C.append(-(u + w / 2)); u += w + (gaps[k] if k < len(gaps) else 0)
    LZ = -0.4  # letters' middle plane
    def poly(cx, pts, dv=0.0): return [(cx - a, b + dv) for a, b in pts]
    def hang(cx, du, top=True, dv=0.95):  # a strap from the pipe to the letter
        y0, y1 = (dv - 0.03, PY) if top else (-PY, -dv + 0.03)
        O.append(box((0.05, y1 - y0, 0.02), (cx - du, (y0 + y1) / 2, PZ - 0.06), metal))
        O.append(box((0.04, 0.045, 0.055), (cx - du, y0 + (0.015 if top else -0.015), -0.3525), metal))
    jit = lambda: (rnd.uniform(-0.05, 0.05), rnd.uniform(-0.04, 0.04))
    # L: a car door (teal, a dent, chrome handle, the wing mirror still on, a rubber seal)
    cx = C[0]; w = 1.1; h2 = w / 2
    Lp = [(-h2, -0.95), (h2, -0.95), (h2, -0.55), (-h2 + 0.44, -0.55), (-h2 + 0.44, 0.95), (-h2, 0.95)]
    door = side_x(poly(cx, Lp), 0.12, (0, 0, LZ), sal, bev=0.03, seg=2); fit(door, R['door'], mode='front')
    xform([door], rot=(0, 0, 0.04), pivot=(cx, 0, LZ)); O.append(door)
    O.append(box((0.22, 0.05, 0.05), (cx - (-h2 + 0.22), 0.3, LZ - 0.075), metal, bev=0.012, seg=1))
    O.append(box((0.18, 0.16, 0.12), (cx - (-h2 + 0.3), 0.98, LZ - 0.05), sal, bev=0.04, seg=2)); fit(O[-1], R['door'])
    O.append(box((0.03, 0.12, 0.08), (cx - (-h2 + 0.3), 0.98, LZ - 0.12), metal))
    O.append(fit(box((0.03, 1.9, 0.13), (cx + h2 - 0.01, 0, LZ), sal), R['seal']))
    hang(cx, -h2 + 0.2); hang(cx, h2 - 0.2, top=False)
    # O: a tyre
    cx = C[1]
    O.append(BK.torus(0.68, 0.27, (cx, 0, LZ), rub, axis='z', seg=20, sides=6))
    O.append(BK.torus(0.43, 0.04, (cx, 0, LZ - 0.12), metal, axis='z', seg=16, sides=3))  # a bit of rim still in it
    hang(cx, 0, dv=0.95); hang(cx, 0.0, top=False)
    # S: pink neon on a black board, clips, a transformer box
    cx = C[2]
    O.append(fit(box((1.1, 1.9, 0.03), (cx, 0, LZ + 0.05), sal, bev=0.01, seg=1), R['board']))
    sp = cat_rom([(0.45, 0.68), (0.2, 0.88), (-0.2, 0.86), (-0.42, 0.55), (-0.25, 0.15), (0.25, -0.1), (0.43, -0.5), (0.2, -0.86), (-0.2, -0.87), (-0.45, -0.65)], 5)
    O.append(fit(sweep([(cx - a, b, LZ - 0.04) for a, b in sp], 0.055, neon, seg=6), pinkr))
    for k in (4, 18, 30, 40):
        a, b = sp[k]; O.append(cyl(0.015, 0.08, (cx - a, b, LZ - 0.0), metal, axis='z', seg=4))
    O.append(fit(box((0.3, 0.14, 0.12), (cx, -0.85, LZ + 0.0), sal, bev=0.02, seg=1), R['board']))
    hang(cx, -0.4); hang(cx, 0.4); hang(cx, 0, top=False)
    # T: pallet planks (three across, two down), nailed crooked
    cx = C[3]
    for k, v in enumerate((0.86, 0.69, 0.52)):
        dv, rz = jit()
        O.append(fit(box((1.3, 0.15, 0.025), (cx + dv, v, LZ - 0.035), sal, bev=0.006, seg=1, rot=(0, 0, rz * 0.5)), R['plank']))
    for du in (-0.12, 0.12):
        dv, rz = jit()
        O.append(fit(box((0.2, 1.5, 0.025), (cx - du, -0.2, LZ - 0.005), sal, bev=0.006, seg=1, rot=(0, 0, rz * 0.4)), R['plank'], mode='front'))
    O.append(fit(box((1.2, 0.12, 0.07), (cx, 0.69, LZ + 0.04), sal, bev=0.01, seg=1), R['plank']))
    hang(cx, -0.5); hang(cx, 0.5); hang(cx, 0, top=False)
    # &: yellow neon on a board
    cx = C[4]
    O.append(fit(box((1.0, 1.9, 0.03), (cx, 0, LZ + 0.05), sal, bev=0.01, seg=1), R['board']))
    ap = cat_rom([(0.44, -0.88), (0.05, -0.35), (-0.24, 0.12), (-0.3, 0.55), (-0.08, 0.84), (0.17, 0.72), (0.19, 0.42), (-0.05, 0.18), (-0.36, -0.12),
                  (-0.42, -0.52), (-0.22, -0.84), (0.08, -0.88), (0.3, -0.66), (0.42, -0.32)], 5)
    O.append(fit(sweep([(cx - a, b, LZ - 0.04 - 0.03 * (i > 35)) for i, (a, b) in enumerate(ap)], 0.05, neon, seg=6), yelr))
    for k in (3, 22, 48, 60):
        a, b = ap[k]; O.append(cyl(0.015, 0.11, (cx - a, b, LZ - 0.01), metal, axis='z', seg=4))
    hang(cx, -0.35); hang(cx, 0.35); hang(cx, 0, top=False)
    # F: a fridge door (mint enamel, chrome bar handle, magnets, a badge)
    cx = C[5]; w = 1.05; h2 = w / 2
    Fp = [(-h2, -0.95), (-h2 + 0.42, -0.95), (-h2 + 0.42, -0.12), (h2 - 0.22, -0.12), (h2 - 0.22, 0.24), (-h2 + 0.42, 0.24), (-h2 + 0.42, 0.55), (h2, 0.55), (h2, 0.95), (-h2, 0.95)]
    fd = side_x(poly(cx, Fp), 0.13, (0, 0, LZ), sal, bev=0.05, seg=3); fit(fd, R['fridge'], mode='front')
    xform([fd], rot=(0, 0, -0.03), pivot=(cx, 0, LZ)); O.append(fd)
    O.append(rod((cx - (-h2 + 0.12), -0.7, LZ - 0.13), (cx - (-h2 + 0.12), 0.1, LZ - 0.13), 0.025, metal, seg=6))
    for v in (-0.7, 0.1): O.append(box((0.04, 0.04, 0.08), (cx - (-h2 + 0.12), v, LZ - 0.09), metal))
    for k, (du, dv, col) in enumerate(((0.0, 0.75, 'red'), (0.25, 0.8, 'blue'), (0.1, 0.06, 'plate'))):
        O.append(fit(box((0.09, 0.09, 0.03), (cx - du, dv, LZ - 0.075), sal, bev=0.01, seg=1), R[col]))
    O.append(box((0.26, 0.07, 0.02), (cx - 0.15, 0.64, LZ - 0.072), metal, bev=0.005, seg=1))
    hang(cx, -h2 + 0.2); hang(cx, h2 - 0.2); hang(cx, -h2 + 0.2, top=False)
    # O: a toilet seat (with its hinges, a taped crack)
    cx = C[6]
    ell = lambda a, b, n=24: [(a * math.cos(2 * math.pi * k / n), b * math.sin(2 * math.pi * k / n)) for k in range(n)]
    seat = side_x(poly(cx, ell(0.7, 0.93)), 0.07, (0, 0, LZ), sal, bev=0.025, seg=2, holes=[poly(cx, ell(0.4, 0.58))]); fit(seat, R['white'])
    O.append(seat)
    for du in (-0.2, 0.2): O.append(cyl(0.05, 0.14, (cx - du, 0.95, LZ + 0.02), metal, axis='x', seg=8))
    O.append(fit(box((0.06, 0.3, 0.086), (cx - 0.55, -0.35, LZ - 0.002), sal, rot=(0, 0, 0.5)), R['plate']))
    hang(cx, -0.2, dv=0.97); hang(cx, 0.2, dv=0.97); hang(cx, 0, top=False, dv=0.93)
    # U: a horseshoe magnet (red, silver tips)
    cx = C[7]
    up = [(-0.42, 0.62), (-0.42, 0.1), (-0.42, -0.3)] + [(math.cos(math.radians(a)) * 0.42, -0.3 + math.sin(math.radians(a)) * 0.42 * 1.05) for a in range(-170, -9, 20)] + [(0.42, -0.3), (0.42, 0.1), (0.42, 0.62)]
    O.append(fit(sweep([(cx - a, b, LZ) for a, b in up], 0.22, sal, seg=4, squash=(0.45, 1.0)), R['red']))
    for s_ in (-1, 1): O.append(sweep([(cx - s_ * 0.42, 0.6, LZ), (cx - s_ * 0.42, 0.95, LZ)], 0.215, metal, seg=4, squash=(0.47, 1.02)))
    hang(cx, -0.42, dv=0.95); hang(cx, 0.42, dv=0.95); hang(cx, 0, top=False, dv=0.95)
    # N: corrugated sheet strips (two posts and a diagonal)
    cx = C[8]; w = 1.25; h2 = w / 2
    def corr(cu, cv, sw, sh, rz):
        o = box((sw, sh, 0.012), (0, 0, 0), sal); subdiv(o, 8)
        for v in o.data.vertices: v.co.y += 0.0  # (local)
        for v in o.data.vertices:
            gx = v.co.x; v.co.y += -0.018 * math.sin(gx / sw * 2 * math.pi * 3)  # ridges along the strip (blender y = game -z)
        o.data.update(); fit(o, R['corr'], mode='front')
        xform([o], rot=(0, 0, rz), move=(cx - cu, cv, LZ)); return o
    O.append(corr(-h2 + 0.18, 0, 0.36, 1.9, 0.0)); O.append(corr(h2 - 0.18, 0, 0.36, 1.9, 0.0))
    dl = math.hypot(w - 0.36, 1.9); ang = math.atan2(1.9, w - 0.36)
    dg = corr(0, 0, 0.36, dl * 0.97, -(math.pi / 2 - ang)); xform([dg], move=(0, 0, -0.03)); O.append(dg)
    hang(cx, -h2 + 0.18); hang(cx, h2 - 0.18); hang(cx, h2 - 0.18, top=False)
    # D: a road sign (white border, blue face) cut into a D, still on a bent bit of its post
    cx = C[9]
    def dshape(l, r0, c0=-0.28, n=12): return [(l, -r0)] + [(c0 + math.cos(math.radians(a)) * r0, math.sin(math.radians(a)) * r0) for a in range(-90, 91, 180 // n)] + [(l, r0)]
    outer = side_x(poly(cx, dshape(-0.65, 0.95, -0.25)), 0.03, (0, 0, LZ + 0.02), sal, holes=[poly(cx, dshape(-0.31, 0.44, -0.25))]); fit(outer, R['white'])
    inner = side_x(poly(cx, dshape(-0.59, 0.89, -0.25)), 0.03, (0, 0, LZ - 0.02), sal, holes=[poly(cx, dshape(-0.37, 0.5, -0.25))]); fit(inner, R['roadblue'])
    O += [outer, inner]
    for v in (0.6, -0.6): O.append(cyl(0.03, 0.1, (cx - (-0.47), v, LZ - 0.01), metal, axis='z', seg=6))
    O.append(sweep([(cx - (-0.45), -0.7, LZ + 0.05), (cx - (-0.46), -1.05, LZ + 0.05), (cx - (-0.3), -1.32, LZ + 0.12)], 0.04, metal, seg=6))
    hang(cx, -0.4, dv=0.95); hang(cx, 0.3, dv=0.85); hang(cx, -0.4, top=False, dv=0.95)
    # the tag: returns: never (on a string off the bottom pipe, past the D)
    tx = C[9] - 0.95
    O.append(fit(tube([(tx, -PY - 0.04, PZ - 0.03), (tx - 0.02, -1.18, PZ - 0.06), (tx - 0.03, -1.2, PZ - 0.08)], 0.006, sal, seg=4), R['string']))
    O.append(fit(box((0.5, 0.25, 0.006), (tx - 0.21, -1.27, PZ - 0.08), sal, rot=(0.12, 0.2, -0.1)), R['tag'], mode='front'))
    for o in O:
        if o.data.materials and o.data.materials[0] in (metal, rub): uv_tile(o, 0.5)
    lights = [[C[2], 0, -0.7, 0xff4fd8], [C[4], 0, -0.7, 0xffe14d], [-4.0, PY, -0.6, 0xffd27a], [4.0, PY, -0.6, 0xffd27a]]
    bpy.context.view_layer.update()
    meta = {'district': 'bottom', 'landmark': True, 'lights': lights, 'mount': 'wall', 'col': [16.0, 2.8, 0.5],
            'note': 'origin at the sign centre on the wall (z = 0), sticks out toward -z', 'tag': 'returns: never'}
    meta['_lodpick'] = [o for o in O if BK._diag(o) > 0.9 and min(o.dimensions) > 0.02]
    return O, meta


# ================================================================================================ RETURNS counter
# the depot's 12 m returns desk, patched together over sixty years: an original ☺ CORP formica front, a kicked-in
# panel, three filing cabinets, an old door laid on its side. A RETURNS sign on two poles with a NOW SERVING display
# stuck at 000, a service bell, a take-a-number dispenser, piles of tagged lost property, and a cat asleep on it all.
# origin centre-bottom, the customer side (front) toward -z.

def rc_atlases():
    A = Atlas('rc_hard_t', 256)
    R = {}
    fm = A.sub(0, 0, 128, 32); crust(fm, 0xffe58a, 0.04, seed=51, speck=0xd8b860, p=0.04)  # formica front, ☺ CORP print
    smiley(fm, 14, 16, 10, face=0xffffff, ink=0xd84a9a); text_px(fm, 'RETURNS', 30, 6, 2, 0xd84a9a); write(fm, 'since forever', 31, 22, 1, 0xb85a8a)
    grime(fm, 0xb89a5a, 0.12, seed=3, blob=6); R['formica'] = A.rect(0, 0, 128, 32)
    fm2 = A.sub(0, 32, 128, 32); crust(fm2, 0xffe58a, 0.04, seed=52, speck=0xd8b860, p=0.04); grime(fm2, 0xb89a5a, 0.15, seed=4, blob=6)
    for x in range(4, 128, 18): fm2[:, x] = hexrgb(0xe8c870)
    R['formica2'] = A.rect(0, 32, 128, 32)
    tp = A.sub(128, 0, 64, 32); crust(tp, 0xffb3c7, 0.03, seed=53)
    for k in range(6): tp[(k * 11) % 32, :] = hexrgb(0xff9ab6)
    for k in range(14): px_disc(tp, (k * 37) % 64, (k * 13) % 32, 1.0, 0xe88aa6)
    R['top'] = A.rect(128, 0, 64, 32)
    cab = A.sub(192, 0, 64, 64); crust(cab, 0x5fd3c6, 0.05, seed=54, speck=0x9a5a3a, p=0.02); R['cabinet'] = A.rect(192, 0, 64, 64)
    dr = A.sub(128, 32, 64, 32); crust(dr, 0x6fe0d2, 0.04, seed=55); dr[2:6, 22:42] = hexrgb(0xf4f0e8); write(dr, 'misc', 23, 1, 1, INK)
    dr[-2:] = hexrgb(0x3a9a90); R['drawer'] = A.rect(128, 32, 64, 32)
    dd = A.sub(0, 64, 128, 48); crust(dd, 0xff9ac0, 0.05, seed=56, speck=0xffffff, p=0.01)  # the door on its side, 4 panels
    for (x0, y0) in ((8, 6), (68, 6), (8, 27), (68, 27)): dd[y0:y0 + 15, x0:x0 + 52] = hexrgb(0xf080aa); dd[y0, x0:x0 + 52] = hexrgb(0xffd0e0)
    R['door'] = A.rect(0, 64, 128, 48)
    sg = A.sub(0, 112, 256, 48); crust(sg, 0xffe14d, 0.04, seed=57, speck=0xd8a830, p=0.03)  # the RETURNS sign
    sg[0:3] = sg[-3:] = hexrgb(0xff4fd8); sg[:, 0:3] = sg[:, -3:] = hexrgb(0xff4fd8)
    text_px(sg, 'RETURNS', 68, 7, 3, 0x6a0050); text_px(sg, 'RETURNS', 66, 6, 3, 0xff00a8)
    sg[6:27, 96:99] = sg[6:27, 96:99] * 0.5 + hexrgb(0xffe14d) * 0.5  # peeled
    smiley(sg, 26, 20, 15, face=0xffffff, ink=INK); smiley(sg, 230, 20, 15, face=0xffffff, ink=INK)
    write(sg, 'all losses final.', 77, 34, 1, 0x6a0050)
    R['sign'] = A.rect(0, 112, 256, 48)
    cb = A.sub(128, 64, 64, 48); crust(cb, 0xc8955a, 0.06, seed=58, speck=0x8a6030, p=0.04)
    cb[22:26] = hexrgb(0xd8c8a0); write(cb, 'fragile', 6, 30, 1, 0xd01830); write(cb, 'lost', 40, 6, 1, INK, wob=1, seed=3)
    R['cardboard'] = A.rect(128, 64, 64, 48)
    tg = A.sub(192, 64, 32, 16); crust(tg, 0xd8b07a, 0.05, seed=59); px_disc(tg, 4, 8, 2, 0xf8f0e0); write(tg, '#', 10, 4, 1, 0xd01830); write(tg, '17', 18, 4, 1, INK)
    R['tag'] = A.rect(192, 64, 32, 16)
    for k, (nm, c) in enumerate((('suitcase', 0xb48cff), ('rubber', 0x1c1a20), ('red', 0xff2a3a), ('white', 0xfbfaf6), ('wood', 0xb87a40), ('pot', 0xd86a3a),
                                 ('leaf', 0x39c46a), ('duck', 0xffd83a), ('bag', 0x2a2a34), ('teal', 0x3fd6c6), ('paper', 0xf6f2e4), ('string', 0xf0e6c8),
                                 ('bowl', 0xff4fd8), ('guitar', 0x2a1a3a), ('mug', 0xffffff), ('beak', 0xff8a2a))):
        R[nm] = A.fill(128 + (k % 8) * 16, 192 + (k // 8) * 16, 16, 16, c)
    rcp = A.sub(0, 160, 64, 32); crust(rcp, 0xf6f2e4, 0.03, seed=60)
    for y in range(3, 30, 5): rcp[y, 4:60 - (y * 7) % 20] = hexrgb(0x9a9aa6)
    R['papers'] = A.rect(0, 160, 64, 32)
    tk = A.sub(64, 160, 64, 32); crust(tk, 0xffffff, 0.02, seed=61); tk[0:6] = hexrgb(0xff3030); text_px(tk, 'TAKE A', 8, 9, 1, 0xff3030); text_px(tk, 'NUMBER', 8, 19, 1, 0xff3030)
    R['takenum'] = A.rect(64, 160, 64, 32)
    S_ = Atlas('rc_soft_t', 64)
    tb = S_.sub(0, 0, 64, 32); crust(tb, 0xff9a3a, 0.06, seed=62)
    for x in range(0, 64, 7): tb[:, x:x + 3] = tb[:, x:x + 3] * 0.6 + hexrgb(0xb85a10) * 0.4
    R['tabby'] = S_.rect(0, 0, 64, 32)
    fc = S_.sub(0, 32, 32, 32); crust(fc, 0xff9a3a, 0.05, seed=63); fc[18:32, 6:26] = hexrgb(0xfff2e6)
    px_line(fc, 7, 15, 12, 17, INK, 1.2); px_line(fc, 12, 17, 15, 15, INK, 1.2); px_line(fc, 18, 15, 21, 17, INK, 1.2); px_line(fc, 21, 17, 25, 15, INK, 1.2)
    px_disc(fc, 16, 21, 1.6, 0xff7aa0)
    for x in range(0, 32, 8): fc[0:6, x:x + 3] = hexrgb(0xb85a10)
    R['catface'] = S_.rect(0, 32, 32, 32)
    R['fur_w'] = S_.fill(32, 32, 16, 16, 0xfff2e6); R['pinkear'] = S_.fill(48, 32, 16, 16, 0xff9ab6)
    R['cloth'] = S_.fill(32, 48, 16, 16, 0x4f7ad8); R['felt'] = S_.fill(48, 48, 16, 16, 0x3a2a34)
    G = Atlas('rc_glow_t', 128, 32)
    ns = G.sub(0, 0, 128, 32); ns[:] = hexrgb(0x140608); text_px(ns, 'NOW', 4, 4, 1, 0xff6060); text_px(ns, 'SERVING', 4, 13, 1, 0xff6060)
    seg7(ns, '000', 60, 4, 14, 24, 3, 0xff2020, gap=5, ghost=0x401010)
    write(ns, 'please wait', 2, 23, 1, 0xffa0a0)
    R['serving'] = G.rect(0, 0, 128, 32)
    return A, S_, G, R


def grd(o, y0, soft=0.0):  # gutkit.ground, after the object's placement is current
    bpy.context.view_layer.update(); return GK.ground(o, y0, soft)


def tag_on(O, p, m, R, rot=0.0, drop=0.08):
    """a luggage tag on a string hanging off the point p (game)"""
    x, y, z = p
    O.append(fit(tube([(x, y, z), (x + 0.01, y - drop * 0.6, z - 0.006), (x + 0.02, y - drop - 0.012, z - 0.012)], 0.003, m, seg=3), R['string']))
    O.append(fit(box((0.09, 0.05, 0.003), (x + 0.045, y - drop - 0.01, z - 0.012), m, rot=(0.1, rot, -0.3)), R['tag'], mode='front'))


def build_returns_counter():
    A, S_, G, R = rc_atlases()
    hard = mat('rc_hard', 0xffffff, rough=0.3, clearcoat=0.6, tex=A.image())
    soft = mat('rc_soft', 0xffffff, rough=0.85, tex=S_.image())
    chrome = plain('rc_chrome', 0xe0e4ec, rough=0.14, metal=1.0, var=0.05, seed=64)
    glow = mat('rc_glow', 0xffffff, rough=0.3, tex=G.image(), emit=0xffffff, strength=2.5, emit_tex=True)
    O = []; rnd = random.Random(21)
    TOP = 1.1
    O.append(fit(box((12.0, 1.0, 0.78), (0, 0.55, 0.03), hard), R['formica2']))  # carcass
    O.append(fit(box((11.8, 0.1, 0.7), (0, 0.05, 0.0), hard), R['rubber']))
    # the worktop in two slabs with a taped seam, a chrome nosing
    for x0, x1, rz in ((-6.1, 0.02, 0.0), (0.02, 6.1, 0.004)):
        O.append(fit(box((x1 - x0, 0.05, 0.98), ((x0 + x1) / 2, TOP - 0.025, -0.03), hard, bev=0.01, seg=1, rot=(0, 0, rz)), R['top']))
    O.append(box((12.2, 0.06, 0.03), (0, TOP - 0.03, -0.53), chrome, bev=0.01, seg=1))
    O.append(fit(box((0.12, 0.004, 0.98), (0.02, TOP + 0.0015, -0.03), hard), R['white']))
    # front, A: original formica (x 3..6), B: original with the kicked-in hole patched (x 0..3)
    O.append(fit(box((2.98, 0.94, 0.04), (4.5, 0.57, -0.37), hard), R['formica'], mode='front'))
    O.append(fit(box((2.98, 0.94, 0.04), (1.5, 0.57, -0.37), hard), R['formica2'], mode='front'))
    O.append(fit(box((0.7, 0.5, 0.03), (1.2, 0.42, -0.4), hard, rot=(0, 0, 0.12)), R['cardboard'], mode='front'))
    for a in (0.6, -0.6): O.append(fit(box((0.8, 0.07, 0.006), (1.2, 0.42, -0.418), hard, rot=(0, 0, a)), R['white']))
    # C: three filing cabinets (x -3..0), four drawers each, one drawer pulled out
    for k in range(3):
        cx = -0.5 - k * 0.98
        O.append(fit(box((0.92, 0.99, 0.7), (cx, 0.505, -0.02), hard, bev=0.015, seg=1), R['cabinet']))
        for d in range(4):
            out = 0.22 if (k, d) == (1, 1) else 0.0
            dy = 0.15 + d * 0.235
            O.append(fit(box((0.84, 0.2, 0.03), (cx, dy, -0.385 - out), hard, bev=0.01, seg=1), R['drawer'], mode='front'))
            O.append(box((0.22, 0.025, 0.04), (cx, dy + 0.04, -0.415 - out), chrome, bev=0.006, seg=1))
            if out:
                O.append(fit(box((0.8, 0.16, out), (cx, dy - 0.01, -0.37 - out / 2), hard), R['drawer']))
                O.append(fit(box((0.6, 0.012, 0.18), (cx, dy + 0.075, -0.4 - out / 2), hard, rot=(0.25, 0, 0)), R['papers']))
    # D: a door laid on its side (x -6..-3), its knob still on, propped on a crate
    O.append(fit(box((2.98, 0.9, 0.05), (-4.5, 0.6, -0.38), hard, bev=0.01, seg=1, rot=(0, 0, 0.01)), R['door'], mode='front'))
    O.append(ball(0.04, (-3.4, 0.62, -0.43), chrome, seg=8, rings=5))
    O.append(fit(box((0.5, 0.15, 0.45), (-5.2, 0.075, -0.6), hard, bev=0.01, seg=1), R['wood']))
    # the RETURNS sign on two poles, NOW SERVING stuck at 000 hanging under it
    for x in (-2.7, 2.7): O.append(cyl(0.035, 1.9, (x, TOP + 0.95 - 0.02, 0.3), chrome, axis='y', seg=8))
    O.append(fit(box((5.8, 0.9, 0.06), (0, 2.5, 0.27), hard, bev=0.015, seg=1), R['sign'], mode='front'))
    O.append(fit(box((5.7, 0.8, 0.01), (0, 2.5, 0.303), hard), R['formica2']))  # the back of the board, plain
    for x in (-2.15, -1.55):
        O.append(tube([(x, 2.05, 0.27), (x, 1.92, 0.27)], 0.008, chrome, seg=4))
    O.append(fit(box((1.2, 0.32, 0.08), (-1.85, 1.77, 0.27), glow, bev=0.01, seg=1), R['serving'], mode='front'))
    # the bell, and a cat asleep next to it
    O.append(cyl(0.07, 0.025, (1.0, TOP + 0.012, -0.28), hard, axis='y', seg=12)); fit(O[-1], R['rubber'])
    O.append(lathe([(0.065, TOP + 0.025), (0.06, TOP + 0.06), (0.04, TOP + 0.09), (0.012, TOP + 0.1), (0.0, TOP + 0.1)], (1.0, 0, -0.28), chrome, seg=12, axis='y'))
    O.append(cyl(0.008, 0.03, (1.0, TOP + 0.11, -0.28), chrome, axis='y', seg=6))
    CX, CZ = 1.55, -0.12
    body = ball(1.0, (CX, TOP + 0.08, CZ), soft, scale=(0.24, 0.1, 0.18), seg=12, rings=7); jitter(body, 0.006, seed=5)
    for v in body.data.vertices:
        if v.co.z < 0: pass
    grd(body, TOP - 0.002); fit(body, R['tabby'])
    O.append(body)
    hd = ball(0.075, (CX - 0.17, TOP + 0.075, CZ - 0.11), soft, scale=(1.05, 0.85, 0.95), seg=8, rings=6); fit(hd, R['catface'], mode='front'); O.append(hd)
    for s_ in (-1, 1):
        e = cyl(0.03, 0.05, (CX - 0.17 + s_ * 0.042, TOP + 0.14, CZ - 0.1), soft, axis='y', seg=4, r2=0.0, rot=(0, 0, -s_ * 0.3)); fit(e, R['pinkear']); O.append(e)
    tail = sweep([(CX + 0.2, TOP + 0.05, CZ + 0.05), (CX + 0.16, TOP + 0.035, CZ - 0.12), (CX - 0.0, TOP + 0.03, CZ - 0.19), (CX - 0.12, TOP + 0.03, CZ - 0.19)],
                 [0.03, 0.03, 0.028, 0.02], soft, seg=6); fit(tail, R['tabby']); O.append(tail)
    paw = ball(0.035, (CX - 0.1, TOP + 0.02, CZ - 0.17), soft, scale=(1.4, 0.7, 1), seg=6, rings=4); grd(paw, TOP - 0.002); fit(paw, R['fur_w']); O.append(paw)
    tag_on(O, (CX - 0.14, TOP + 0.04, CZ - 0.16), hard, R, rot=0.3, drop=0.02)
    # take-a-number: floor stand bolted to the counter's end, a red dispenser, tickets hanging out
    TX, TZ = 6.08, -0.3
    O.append(cyl(0.2, 0.03, (TX + 0.12, 0.015, TZ), chrome, axis='y', seg=12))
    O.append(cyl(0.025, 1.19, (TX + 0.12, 0.605, TZ), chrome, axis='y', seg=6))
    O.append(box((0.15, 0.04, 0.04), (TX + 0.05, 0.9, TZ), chrome))
    O.append(fit(cyl(0.13, 0.12, (TX + 0.12, 1.3, TZ - 0.03), hard, axis='z', seg=14, bev=0.01), R['red']))
    O.append(fit(box((0.28, 0.14, 0.01), (TX + 0.12, 1.5, TZ - 0.03), hard), R['takenum'], mode='front'))
    O.append(box((0.01, 0.07, 0.02), (TX + 0.12, 1.44, TZ - 0.03), chrome))
    O.append(fit(box((0.05, 0.16, 0.003), (TX + 0.12, 1.12, TZ - 0.1), hard, rot=(0.2, 0, 0.05)), R['white']))
    # lost property on the counter (each with its tag)
    def card(w, h, d, x, z, y0, rz):
        O.append(fit(box((w, h, d), (x, y0 + h / 2, z), hard, bev=0.006, seg=1, rot=(0, rz, 0)), R['cardboard'])); return y0 + h
    y = card(0.55, 0.36, 0.42, 4.6, -0.05, TOP, 0.1); y = card(0.45, 0.3, 0.36, 4.62, -0.02, y, -0.2); y = card(0.32, 0.24, 0.3, 4.55, 0.0, y, 0.35)
    tag_on(O, (4.4, TOP + 0.3, -0.27), hard, R); tag_on(O, (4.8, y - 0.05, -0.15), hard, R, rot=0.5)
    O.append(fit(box((0.52, 0.66, 0.22), (3.4, TOP + 0.33, 0.05), hard, bev=0.03, seg=2, rot=(0, 0.15, 0)), R['suitcase']))
    O.append(sweep([(3.27, TOP + 0.62, 0.05), (3.3, TOP + 0.72, 0.05), (3.5, TOP + 0.72, 0.05), (3.53, TOP + 0.62, 0.05)], 0.015, hard, seg=4)); fit(O[-1], R['rubber'])
    tag_on(O, (3.62, TOP + 0.5, -0.1), hard, R, drop=0.1)
    O.append(fit(lathe([(0.0, TOP), (0.17, TOP), (0.18, TOP + 0.015), (0.1, TOP + 0.02), (0.1, TOP + 0.1), (0.07, TOP + 0.14), (0.0, TOP + 0.145)], (-0.9, 0, -0.1), soft, seg=12, axis='y'), R['felt']))
    tag_on(O, (-0.8, TOP + 0.1, -0.2), hard, R, drop=0.05)
    O.append(fit(rod((-1.6, TOP + 0.03, -0.25), (-0.6, TOP + 0.035, 0.05), 0.03, soft, seg=6), R['cloth']))
    O.append(fit(sweep([(-1.6, TOP + 0.03, -0.25), (-1.68, TOP + 0.05, -0.28), (-1.68, TOP + 0.09, -0.24), (-1.62, TOP + 0.09, -0.2)], 0.012, hard, seg=4), R['wood']))
    tag_on(O, (-1.55, TOP + 0.05, -0.26), hard, R, drop=0.02)
    O.append(fit(box((0.5, 0.3, 0.38), (-2.6, TOP + 0.15, 0.0), hard, bev=0.01, seg=1, rot=(0, -0.1, 0)), R['wood']))
    for k in range(5): O.append(fit(ball(0.07, (-2.75 + k * 0.08, TOP + 0.3 + (k % 2) * 0.02, -0.05 + (k % 3) * 0.06), hard, seg=8, rings=5), R[('red', 'teal', 'duck', 'bowl', 'white')[k]]))
    tag_on(O, (-2.4, TOP + 0.25, -0.2), hard, R)
    O.append(fit(box((0.4, 0.34, 0.3), (-4.6, TOP + 0.17, 0.05), hard, rot=(0, 0.2, 0)), R['papers']))
    O.append(fit(lathe([(0.0, TOP), (0.09, TOP), (0.11, TOP + 0.16), (0.12, TOP + 0.17), (0.0, TOP + 0.17)], (-5.25, 0, -0.1), hard, seg=10, axis='y'), R['pot']))
    fol = ball(0.17, (-5.25, TOP + 0.3, -0.1), hard, seg=8, rings=6); jitter(fol, 0.03, seed=7); fit(fol, R['leaf']); O.append(fol)
    O.append(fit(cyl(0.045, 0.1, (-4.95, TOP + 0.05, -0.3), hard, axis='y', seg=10), R['mug']))
    O.append(fit(BK.torus(0.03, 0.01, (-4.9, TOP + 0.05, -0.3), hard, axis='z', seg=8, sides=3), R['mug']))
    duck = ball(0.06, (-0.2, TOP + 0.05, -0.28), hard, scale=(1.2, 0.8, 1), seg=8, rings=5); grd(duck, TOP - 0.002); fit(duck, R['duck']); O.append(duck)
    O.append(fit(ball(0.035, (-0.25, TOP + 0.11, -0.28), hard, seg=6, rings=4), R['duck']))
    O.append(fit(cyl(0.012, 0.03, (-0.28, TOP + 0.105, -0.28), hard, axis='x', seg=5, r2=0.004), R['beak']))
    # leaning on the customer side: a bicycle wheel, a guitar case, a bin bag
    O.append(BK.torus(0.32, 0.022, (2.3, 0.35, -0.48), hard, axis='z', seg=18, sides=4)); fit(O[-1], R['rubber'])
    for k in range(6):
        a = math.pi * k / 6; O.append(rod((2.3 - math.cos(a) * 0.3, 0.35 - math.sin(a) * 0.3, -0.48), (2.3 + math.cos(a) * 0.3, 0.35 + math.sin(a) * 0.3, -0.48), 0.004, chrome, seg=3))
    O.append(cyl(0.03, 0.08, (2.3, 0.35, -0.48), chrome, axis='z', seg=8))
    xform(O[-8:], rot=(-0.12, 0, 0), pivot=(2.3, 0, -0.41))
    tag_on(O, (2.3, 0.62, -0.46), hard, R)
    gc = sweep([(-1.2, 0.2, -0.7), (-1.2, 0.42, -0.64), (-1.2, 0.62, -0.58), (-1.2, 0.85, -0.5), (-1.2, 1.02, -0.45)], [0.2, 0.21, 0.15, 0.1, 0.1], hard, seg=8, squash=(1.0, 0.45))
    fit(gc, R['guitar']); O.append(gc)
    tag_on(O, (-1.2, 1.0, -0.47), hard, R)
    bag = ball(0.32, (-5.6, 0.3, -0.62), soft, scale=(1, 0.95, 0.8), seg=10, rings=6); jitter(bag, 0.04, seed=9); grd(bag, 0.0); fit(bag, R['felt']); O.append(bag)
    O.append(fit(cyl(0.06, 0.1, (-5.6, 0.62, -0.62), soft, axis='y', seg=6, r2=0.02), R['felt']))
    tag_on(O, (-5.55, 0.65, -0.66), hard, R)
    for o in O:
        if o.data.materials and o.data.materials[0] == chrome: uv_tile(o, 0.5)
    bpy.context.view_layer.update()
    meta = {'district': 'bottom', 'landmark': True, 'col': [12.0, 1.1, 0.98], 'top': TOP, 'bell': [1.0, TOP + 0.1, -0.28], 'cat': [CX, TOP, CZ],
            'lights': [[-1.85, 1.75, -0.2, 0xff3030]], 'ticket': [TX + 0.12, 1.3, TZ - 0.1]}
    meta['_lodpick'] = [o for o in O if BK._diag(o) > 0.4 and min(o.dimensions) > 0.02]
    return O, meta


# ================================================================================================ lost-property pile
# what nobody came back for: suitcases and a duffel (tinted per pile), boxes, a sack, a single shoe, a traffic cone,
# an umbrella blown inside out and a closed one, a teddy, a briefcase, a whole bicycle leaning on it all, and a luggage
# tag on everything. ~2.6 m across, origin centre-bottom, front -z.

def build_lostpile():
    A = Atlas('lp_hard_t', 64); R = {}
    cn = A.sub(0, 0, 16, 32); cn[:] = hexrgb(0xff6a1a); cn[8:12] = cn[18:22] = hexrgb(0xffffff); R['cone'] = A.rect(0, 0, 16, 32)
    cb = A.sub(16, 0, 32, 32); crust(cb, 0xc8955a, 0.06, seed=71); cb[14:17] = hexrgb(0xd8c8a0); write(cb, 'lost', 4, 20, 1, INK, wob=1, seed=2); R['cardboard'] = A.rect(16, 0, 32, 32)
    tg = A.sub(48, 0, 16, 16); crust(tg, 0xd8b07a, 0.05, seed=72); px_disc(tg, 3, 8, 1.6, 0xf8f0e0); tg[6:10, 7:14] = hexrgb(0x2a2a8a); R['tag'] = A.rect(48, 0, 16, 16)
    for k, (nm, c) in enumerate((('brief', 0x5a2a1a), ('canopy', 0xff4fd8), ('canopy2', 0x3fd6c6), ('bike', 0x4fd8ff), ('white', 0xfbfaf6), ('rubber', 0x1c1a20),
                                 ('shoe', 0xff8ac8), ('gold', 0xffd84a), ('string', 0xf0e6c8), ('saddle', 0x2a2026), ('red', 0xff3030), ('wood', 0xb87a40))):
        R[nm] = A.fill((k % 4) * 16, 32 + (k // 4) * 8, 16, 8, c)
    hard = mat('lp_hard', 0xffffff, rough=0.32, clearcoat=0.6, tex=A.image())
    S_ = Atlas('lp_soft_t', 32)
    fur = S_.sub(0, 0, 16, 16); crust(fur, 0xc8884a, 0.1, seed=73); R['fur'] = S_.rect(0, 0, 16, 16, 1)
    tf = S_.sub(16, 0, 16, 16); crust(tf, 0xc8884a, 0.08, seed=74); tf[8:16, 3:13] = hexrgb(0xf0d0a8); px_disc(tf, 5, 6, 1.6, INK); px_disc(tf, 11, 6, 1.6, INK); px_disc(tf, 8, 10, 1.4, 0x3a2020)
    R['tface'] = S_.rect(16, 0, 16, 16)
    sk = S_.sub(0, 16, 16, 16); crust(sk, 0xc8b88a, 0.08, seed=75); sk[::4] *= 0.9; R['sack'] = S_.rect(0, 16, 16, 16, 1)
    R['snout'] = S_.fill(16, 16, 8, 8, 0xf0d0a8); R['bow'] = S_.fill(24, 16, 8, 8, 0xff3a6a)
    soft = mat('lp_soft', 0xffffff, rough=0.9, tex=S_.image())
    metal = plain('lp_metal', 0xd8dce4, rough=0.18, metal=1.0, var=0.06, seed=76)
    def suit(px):
        crust(px, 0xf8f6f2, 0.04, seed=77)
        for y in (4, 27): px[y] = hexrgb(0xb8b8c0)
        for x in (3, 28): px[:, x] = hexrgb(0xc8c8d0)
        for (x, y) in ((3, 4), (28, 4), (3, 27), (28, 27)): px_disc(px, x, y, 1.5, 0x8a8a96)
    paint = mat('lp_paint', 0xffffff, rough=0.3, clearcoat=0.7, tex=tex_canvas('lp_paint_t', 32, 32, suit))
    O = []
    def tg(p, rot=0.0, drop=0.07): tag_on(O, p, hard, R, rot=rot, drop=drop)
    # the base layer
    sa = box((0.78, 0.26, 0.52), (-0.3, 0.13, 0.12), paint, bev=0.03, seg=1, rot=(0, 0.3, 0)); uv_tile(sa, 0.5); O.append(sa)
    sb = box((0.46, 0.66, 0.24), (0.62, 0.36, 0.3), paint, bev=0.03, seg=1, rot=(0, -0.4, -0.12)); uv_tile(sb, 0.5); O.append(sb)
    O.append(fit(sweep([(0.5, 0.66, 0.3), (0.55, 0.73, 0.32), (0.72, 0.72, 0.24), (0.76, 0.63, 0.22)], 0.014, hard, seg=4), R['rubber']))
    O.append(fit(box((0.46, 0.44, 0.46), (-0.95, 0.22, -0.2), hard, bev=0.008, seg=1, rot=(0, 0.5, 0)), R['cardboard']))
    O.append(fit(box((0.4, 0.32, 0.36), (-0.28, 0.42, 0.15), hard, bev=0.008, seg=1, rot=(0, -0.25, 0.04)), R['cardboard']))
    sk_ = ball(0.3, (0.22, 0.26, -0.5), soft, scale=(1.1, 0.9, 0.9), seg=8, rings=5); jitter(sk_, 0.03, seed=4); grd(sk_, 0.0); fit(sk_, R['sack']); O.append(sk_)
    O.append(fit(cyl(0.05, 0.1, (0.22, 0.55, -0.5), soft, axis='y', seg=5, r2=0.02), R['sack']))
    du = pillow((0.78, 0.3, 0.36), (0.15, 0.4 + 0.05, 0.12), paint, puff=0.18, rot=(0.06, 0.35, -0.1)); uv_tile(du, 0.5); O.append(du)
    # the cone on the boxes, a teddy on the duffel, a briefcase and a shoe out front
    O.append(fit(box((0.34, 0.03, 0.34), (-0.28, 0.595, 0.15), hard, rot=(0, 0.3, 0.04)), R['cone']))
    O.append(fit(lathe([(0.15, 0.6), (0.14, 0.68), (0.1, 0.82), (0.07, 0.94), (0.035, 1.06), (0.0, 1.08)], (-0.28, 0, 0.15), hard, seg=8, axis='y'), R['cone'], mode='front'))
    T = []
    T.append(fit(ball(1.0, (0, 0.13, 0), soft, scale=(0.13, 0.15, 0.11), seg=8, rings=5), R['fur']))
    T.append(fit(ball(0.1, (0, 0.34, -0.01), soft, seg=8, rings=5), R['tface'], mode='front'))
    for s_ in (-1, 1):
        T.append(fit(ball(0.038, (s_ * 0.075, 0.43, 0.0), soft, seg=6, rings=4, scale=(1, 1, 0.5)), R['fur']))
        T.append(fit(ball(1.0, (s_ * 0.13, 0.17, -0.04), soft, scale=(0.045, 0.09, 0.045), seg=6, rings=4, rot=(0.4, 0, s_ * 0.5)), R['fur']))
        T.append(fit(ball(1.0, (s_ * 0.07, 0.04, -0.12), soft, scale=(0.05, 0.05, 0.09), seg=6, rings=4), R['fur']))
    T.append(fit(ball(0.045, (0, 0.31, -0.095), soft, seg=6, rings=4, scale=(1, 0.8, 1)), R['snout']))
    T.append(fit(box((0.1, 0.04, 0.04), (0, 0.235, -0.09), soft), R['bow']))
    xform(T, rot=(0.05, -0.3, 0.08), move=(0.15, 0.62, -0.08)); O += T
    bc = box((0.44, 0.32, 0.11), (-0.85, 0.2, -0.52), hard, bev=0.015, seg=1, rot=(0.22, 0.4, 0)); fit(bc, R['brief']); O.append(bc)
    bh = sweep([(-0.97, 0.36, -0.6), (-0.95, 0.42, -0.62), (-0.82, 0.43, -0.57), (-0.78, 0.37, -0.54)], 0.013, hard, seg=4); fit(bh, R['rubber']); O.append(bh)
    sh = [box((0.11, 0.035, 0.3), (0.0, 0.0175, 0.0), hard, bev=0.01, seg=1), box((0.1, 0.08, 0.17), (0.0, 0.07, 0.05), hard, bev=0.03, seg=2),
          ball(1.0, (0, 0.05, -0.08), hard, scale=(0.05, 0.035, 0.07), seg=6, rings=4)]
    fit(sh[0], R['white']); fit(sh[1], R['shoe']); fit(sh[2], R['shoe'])
    xform(sh, rot=(0, 0.7, 0), move=(-0.3, 0.0, -0.85)); O += sh
    # umbrellas: one blown inside out stuck in the top, one closed lying across the front
    up = lathe([(0.0, 0.0), (0.2, 0.08), (0.42, 0.2), (0.5, 0.3), (0.48, 0.3), (0.0, 0.03)], (0, 0, 0), hard, seg=8, axis='y')
    fit(up, R['canopy'], mode='front')
    U = [up, rod((0, -0.62, 0), (0, 0.32, 0), 0.012, metal, seg=4),
         fit(sweep([(0, -0.62, 0), (0, -0.72, 0.0), (0, -0.76, 0.06), (0, -0.72, 0.1)], 0.016, hard, seg=4), R['wood'])]
    xform(U, rot=(0.3, 0, 0.25), move=(0.42, 1.18, 0.35)); O += U
    cu = [fit(cyl(0.045, 0.7, (0, 0, 0), hard, axis='x', seg=8, r2=0.012), R['canopy2']), rod((0.33, 0, 0), (0.48, 0, 0), 0.008, metal, seg=4),
          fit(sweep([(-0.35, 0, 0), (-0.45, 0.0, 0), (-0.5, 0.05, 0), (-0.46, 0.09, 0)], 0.015, hard, seg=4), R['wood'])]
    xform(cu, rot=(0.1, 0.3, 0.12), move=(0.6, 0.32, -0.52)); O += cu
    # the bicycle, leaning on the pile's left side (frame in its own plane, then tipped onto the pile)
    B = []; br = 0.31
    for z in (-0.52, 0.52):
        B.append(fit(BK.torus(br, 0.025, (0, br + 0.025, z), hard, axis='x', seg=16, sides=4), R['rubber']))
        B.append(cyl(0.035, 0.1, (0, br + 0.025, z), metal, axis='x', seg=6))
        for k in range(3):
            a = math.pi * k / 3
            B.append(rod((0, br + 0.025 - math.cos(a) * br, z - math.sin(a) * br), (0, br + 0.025 + math.cos(a) * br, z + math.sin(a) * br), 0.004, metal, seg=3))
    ra, fa, bb, st, ht, hb = (0, 0.335, 0.52), (0, 0.335, -0.52), (0, 0.3, 0.02), (0, 0.8, 0.2), (0, 0.8, -0.36), (0, 0.66, -0.4)
    for a_, b_ in ((bb, st), (st, ht), (bb, hb), (bb, ra), (st, ra), (hb, fa), (hb, ht)):
        B.append(fit(rod(a_, b_, 0.018, hard, seg=4), R['bike']))
    B.append(fit(sweep([(-0.24, 0.92, -0.3), (-0.1, 0.9, -0.36), (0, 0.88, -0.37), (0.1, 0.9, -0.36), (0.24, 0.92, -0.3)], 0.014, hard, seg=4), R['rubber']))
    B.append(rod((0, 0.8, -0.36), (0, 0.9, -0.37), 0.016, metal, seg=4))
    B.append(fit(box((0.12, 0.05, 0.24), (0, 0.85, 0.22), hard, bev=0.02, seg=1), R['saddle']))
    B.append(rod((0, 0.8, 0.2), (0, 0.84, 0.21), 0.012, metal, seg=4))
    B.append(cyl(0.08, 0.02, bb, metal, axis='x', seg=8)); B.append(rod((0.02, 0.3, 0.02), (0.02, 0.18, -0.05), 0.012, metal, seg=4))
    B.append(fit(box((0.1, 0.025, 0.06), (0.06, 0.18, -0.05), hard), R['rubber']))
    xform(B, rot=(0, -0.35, -0.42), move=(-1.25, 0.0, 0.35)); O += B
    bpy.context.view_layer.update()
    for o in B: grd(o, 0.0)
    # tags on everything
    for p_, r_ in (((-0.55, 0.27, -0.15), 0.2), ((0.42, 0.6, 0.18), -0.4), ((-1.12, 0.44, -0.4), 0.3), ((-0.45, 0.56, -0.02), 0.0), ((0.1, 0.52, -0.82), 0.5),
                   ((-0.2, 0.95, 0.06), -0.2), ((0.1, 0.72, -0.18), 0.4), ((-0.88, 0.37, -0.62), 0.1), ((-0.25, 0.14, -0.96), 0.3), ((0.55, 0.36, -0.58), -0.3)):
        tg(p_, r_)
    bpy.context.view_layer.update()
    meta = {'district': 'bottom', 'col': [2.4, 1.2, 1.8], 'note': 'scatter: a pile of lost property, tinted per pile (lp_paint)', 'paint': ['lp_paint']}
    meta['_lodpick'] = [o for o in O if BK._diag(o) > 0.3 and min(o.dimensions) > 0.02]
    return O, meta


# ================================================================================================ the Gut border gate
# the top of the Long Stairs: an old pastel Bottom archway (concrete pillars painted teal and pink, an iron truss arch
# with a hand-painted sign) that the Gut is eating. Skin has grown over the left pillar and creeps onto the iron, a
# gum with teeth hangs along the arch (the opening is turning into a mouth), veins coil round the ironwork, an eye has
# opened in the keystone and a length of intestine is draped over the top. Opening 12 x 10 m, outside 18 x 14 x 3 m;
# collision = pillars at x +-6..9 (y 0..10) and the lintel at y 10..13. origin centre-bottom, front -z.

def build_gutgate():
    M = GK.gut_mats()
    flesh, vein, enamel, eyem = M['flesh'], M['vein'], M['enamel'], M['eye']
    A = Atlas('gg_bottom_t', 256); R = {}
    def pillar_tex(x, col, seed, words):
        p = A.sub(x, 0, 64, 128); crust(p, col, 0.05, seed=seed, speck=0xffffff, p=0.005)
        rr = np.random.default_rng(seed)
        for k in range(9):  # paint peeled back to grey concrete
            cx, cy = rr.uniform(4, 60), rr.uniform(4, 124); px_disc(p, cx, cy, rr.uniform(2, 5), 0x9a948e); px_disc(p, cx + 1, cy + 1, 1.5, 0x8a847e)
        for y in (18, 21): p[y] = p[y] * 0.5 + hexrgb(0xffffff) * 0.5  # a painted band
        grime(p, 0x6a6a72, 0.12, seed=seed + 1, blob=8)
        for x0 in range(2, 64, 9): drip(p, x0, 22, int(rr.uniform(3, 12)), 0x8a8a92)
        for i, (t, c, y) in enumerate(words): write(p, t, 4, y, 1, c, wob=1, seed=seed + i, bold=True)
        R['p%d' % x] = A.rect(x, 0, 64, 128)
    pillar_tex(0, 0x5fd3c6, 81, [('gut', 0xff4fd8, 60), ('-->', 0xff4fd8, 69)])
    pillar_tex(64, 0xffb3c7, 82, [('the bottom', 0x3a2a8a, 58), ('<', 0xff00a8, 68), ('no cars', 0x3a2a8a, 96), ('no interns', 0x3a2a8a, 106)])
    cc = A.sub(128, 0, 64, 64); crust(cc, 0xb8b2ac, 0.08, seed=83, speck=[(0x8a847e, 0.08), (0xffb3c7, 0.02), (0x5fd3c6, 0.02)]); R['conc'] = A.rect(128, 0, 64, 64)
    ks = A.sub(192, 0, 64, 64); crust(ks, 0xffe58a, 0.06, seed=84, speck=0x9a948e, p=0.05)
    rr = np.random.default_rng(5)
    for k in range(6):  # cracks out from the eye
        x, y = 32.0, 30.0; a = rr.uniform(0, 6.28)
        for st in range(6): nx, ny = x + math.cos(a) * 5, y + math.sin(a) * 5; px_line(ks, x, y, nx, ny, 0x6a5a3a, 1.2); x, y = nx, ny; a += rr.uniform(-0.6, 0.6)
    R['key'] = A.rect(192, 0, 64, 64)
    sg = A.sub(0, 128, 256, 64); crust(sg, 0xfff1b0, 0.04, seed=85, speck=0xd8c890, p=0.03)  # the sign, hand painted
    sg[0:4] = sg[-4:] = hexrgb(0xff4fd8); sg[:, 0:4] = sg[:, -4:] = hexrgb(0xff4fd8)
    for x0 in range(10, 250, 22): sg[5:7, x0:x0 + 10] = hexrgb(0x5fd3c6); sg[-7:-5, x0 + 8:x0 + 18] = hexrgb(0x5fd3c6)
    l1, l2 = 'WELCOME TO THE GUT.', "DON'T PET ANYTHING."
    write(sg, l1, (256 - tw(l1, 2)) // 2 + 1, 11, 2, 0x5a1a4a, wob=1, seed=7); write(sg, l1, (256 - tw(l1, 2)) // 2, 10, 2, 0xff2a8a, wob=1, seed=7)
    write(sg, l2, (256 - tw(l2, 2)) // 2 + 1, 37, 2, 0x103a3a, wob=1, seed=8); write(sg, l2, (256 - tw(l2, 2)) // 2, 36, 2, 0x1a8a80, wob=1, seed=8)
    for k in range(4): drip(sg, int(rr.uniform(20, 236)), 26, int(rr.uniform(3, 8)), 0xff2a8a)
    R['sign'] = A.rect(0, 128, 256, 64)
    bot = mat('gg_bottom', 0xffffff, rough=0.55, clearcoat=0.3, tex=A.image())
    ir = np.zeros((32, 32, 3), np.float32); crust(ir, 0x3a3a52, 0.1, seed=86, speck=[(0xb0582a, 0.08), (0x5fd3c6, 0.03), (0x7a3a2a, 0.06)])
    iron = mat('gg_iron', 0xffffff, rough=0.35, metal=0.6, clearcoat=0.3, tex=lib._image('gg_iron_t', ir))
    O = []; F = []  # F = flesh parts (welded, smooth)
    # --- the pillars: plinth, painted shaft, capital (the viewer's left one, +x, is teal: that's the one being eaten)
    for sx, reg in ((1, 'p0'), (-1, 'p64')):
        cx = sx * 7.5
        O.append(fit(box((3.4, 0.6, 3.4), (cx, 0.3, 0), bot, bev=0.06, seg=1), R['conc']))
        O.append(fit(box((3.0, 9.0, 3.0), (cx, 5.08, 0), bot, bev=0.05, seg=1), R[reg]))
        O.append(fit(box((3.3, 0.45, 3.3), (cx, 9.79, 0), bot, bev=0.06, seg=1), R['conc']))
        O.append(fit(box((3.15, 0.25, 3.15), (cx, 9.45, 0), bot, bev=0.04, seg=1), R['conc']))
    # --- the iron arch: straight bottom chord, curved top chord, uprights, warren diagonals, scrolls, finials
    YB, YT0, YT1 = 10.17, 12.75, 13.5
    topy = lambda x: YT0 + (YT1 - YT0) * (1 - (x / 8.6) ** 2)
    O.append(box((17.4, 0.32, 0.36), (0, YB, 0), iron, bev=0.03, seg=1))
    tc = [(x, topy(x), 0) for x in [-8.6 + 17.2 * k / 24 for k in range(25)]]
    O.append(sweep(tc, 0.2, iron, seg=4, name='topchord', smooth_angle=30))
    for sx in (-1, 1):
        O.append(box((0.32, YT0 - YB + 0.2, 0.32), (sx * 8.6, (YB + YT0) / 2, 0), iron, bev=0.03, seg=1))
        O.append(ball(0.22, (sx * 8.6, YT0 + 0.3, 0), iron, seg=8, rings=5))
        sc = [(sx * (8.65 + 0.25 * math.sin(t) * (1 - t / 9)), YT0 - 0.2 - 0.25 * (1 - math.cos(t)) * (1 - t / 9) - t * 0.06, 0) for t in [k * 0.55 for k in range(14)]]
        O.append(sweep(sc, [0.08 - 0.004 * k for k in range(14)], iron, seg=4))
        sc2 = [(sx * (8.4 - t * 0.12 - 0.22 * math.sin(t) * (1 - t / 10)), YB + 0.2 + 0.22 * (1 - math.cos(t)) * (1 - t / 10), 0) for t in [k * 0.55 for k in range(13)]]
        O.append(sweep(sc2, [0.07 - 0.003 * k for k in range(13)], iron, seg=4))
    xs = [-8.6 + 17.2 * k / 12 for k in range(13)]
    for k in range(12):
        a, b = xs[k], xs[k + 1]
        if k % 2 == 0: O.append(rod((a, YB + 0.1, 0), (b, topy(b) - 0.1, 0), 0.07, iron, seg=4))
        else: O.append(rod((a, topy(a) - 0.1, 0), (b, YB + 0.1, 0), 0.07, iron, seg=4))
    # the sign board, wired onto the truss
    O.append(fit(box((10.8, 1.75, 0.12), (0, 11.37, -0.28), bot, bev=0.03, seg=1), R['sign'], mode='front'))
    O.append(fit(box((10.7, 1.65, 0.02), (0, 11.37, -0.215), bot), R['conc']))  # its back, plain
    for x in (-4.8, -1.6, 1.6, 4.8):
        for y in (10.55, 12.15): O.append(box((0.1, 0.12, 0.3), (x, y, -0.16), iron))
    # the keystone (painted yellow) on the crown, an eye opening in it
    O.append(fit(side_x([(-0.62, 12.85), (0.62, 12.85), (0.86, 14.0), (-0.86, 14.0)], 1.6, (0, 0, 0), bot, bev=0.05, seg=1), R['key'], mode='front'))
    eye = GK.eyeball(eyem, 0.42, (0, 13.42, -0.72), rot=(-math.pi / 2 - 0.28, 0, 0), n=12, polar=(25, 50, 75, 100, 120), name='eye')
    O.append(eye)
    rim = GK.torus(0.47, 0.13, flesh, pos=(0, 13.42, -0.8), rot=(-math.pi / 2 - 0.28, 0, 0), n=14, k=6, name='socket', wob=lambda a: 1 + 0.25 * math.sin(3 * a))
    F.append(rim)
    up = ball(1.0, (0, 13.68, -0.86), flesh, scale=(0.54, 0.28, 0.32), seg=12, rings=7, name='lid', rot=(0.25, 0, 0)); F.append(up)
    lo = ball(1.0, (0, 13.1, -0.84), flesh, scale=(0.46, 0.15, 0.26), seg=10, rings=6, name='lidlow'); F.append(lo)
    # --- skin over the left (+x) pillar: metaballs hugging its faces, thick at the top, drips down the front
    rnd = random.Random(31); balls = []
    def on(face, u, v, r):  # a ball on a pillar face at (u across, v = height), pushed a bit out
        x0, z0 = 7.5, 0.0
        P_ = {'out': (9.0 + r * 0.25, v, u), 'in': (6.0 - r * 0.25, v, u), 'front': (x0 + u, v, -1.5 - r * 0.25), 'back': (x0 + u, v, 1.5 + r * 0.25)}[face]
        balls.append((P_, r))
    for face in ('out', 'in', 'front', 'back'):  # a continuous sheet at the top with a ragged lower edge
        low = {'out': 5.2, 'in': 3.6, 'front': 4.4, 'back': 6.0}[face]
        for i in range(7):
            u = -1.45 + 2.9 * i / 6
            edge = low + rnd.uniform(-0.8, 1.2) + 0.6 * math.sin(i * 1.9)
            v = 10.3
            while v > edge:
                on(face, u + rnd.uniform(-0.15, 0.15), v, rnd.uniform(0.4, 0.72) * (1.0 + 0.25 * (v - edge > 2)))
                v -= rnd.uniform(0.42, 0.55)
        for k in range(5):  # swellings
            on(face, rnd.uniform(-1.2, 1.2), rnd.uniform(low + 1.5, 9.8), rnd.uniform(0.85, 1.15))
    for k in range(7):  # drips down the front and the inner face
        fx = rnd.choice(('front', 'in')); u = rnd.uniform(-1.0, 1.0); v0 = rnd.uniform(4.0, 6.5)
        for j in range(6): on(fx, u + rnd.uniform(-0.04, 0.04), v0 - j * 0.34, 0.5 - j * 0.04)
    for k in range(14):  # over the capital and onto the end of the arch
        balls.append(((rnd.uniform(6.2, 8.9), rnd.uniform(10.0, 11.4), rnd.uniform(-1.4, 1.4)), rnd.uniform(0.6, 0.95)))
    for x in (5.2, 4.2, 3.3):  # creeping along the bottom chord
        balls.append(((x + 0.8, YB, 0.0), 0.75)); balls.append(((x, YB - 0.1, rnd.uniform(-0.2, 0.2)), 0.6))
    skin = GK.meta(balls, res=0.3, m=flesh, target=2300, name='skin')
    GK.lump(skin, 0.2, 0.75, seed=4); GK.lump(skin, 0.07, 2.2, seed=5); F.append(skin)
    # --- the mouth: a gum along the underside of the arch, teeth hanging down, lips running down both pillars
    gb = []
    for k in range(36):
        x = -5.9 + 11.8 * k / 35
        gb.append(((x, 9.85 + 0.05 * math.sin(k), -0.15 + 0.2 * math.sin(k * 0.7)), 0.72 + 0.08 * math.sin(k * 1.7)))
    for sx in (-1, 1):
        for j in range(8): gb.append(((sx * (5.75 + 0.05 * j), 9.6 - j * 0.38, -0.2), 0.58 - j * 0.04))
    gum = GK.meta(gb, res=0.3, m=flesh, target=1250, name='gum'); GK.lump(gum, 0.06, 1.4, seed=6); F.append(gum)
    T = []
    for k in range(9):
        x = -4.9 + 9.8 * k / 8 + rnd.uniform(-0.1, 0.1)
        big = k in (0, 8)
        f = GK.canine if (big or k == 4) else GK.molar
        s_ = (3.2 if big else 2.5 if k == 4 else 2.3) * rnd.uniform(0.92, 1.08)
        T.append(f(enamel, pos=(x, 9.5, -0.35 + rnd.uniform(-0.1, 0.1)), rot=(math.pi + rnd.uniform(-0.1, 0.1), math.pi, rnd.uniform(-0.12, 0.12)), s=s_, seed=k))
    for sx in (-1, 1):  # two growing up from the lips at the corners
        T.append(GK.canine(enamel, pos=(sx * 5.6, 7.0, -0.45), rot=(0.1, 0, sx * 0.6), s=2.0, seed=20 + sx))
    for t_ in T: uv_tile(t_, 0.5)
    O += T
    # --- veins: crawling over the skin, coiling round the bottom chord and a couple of diagonals, across the sign
    bvh = GK.bvh_of(skin)
    for k in range(7):
        st = (rnd.uniform(6.2, 8.8), rnd.uniform(6.5, 10.5), rnd.choice((-1.6, 1.6)))
        pts = GK.crawl(bvh, st, (rnd.uniform(-0.3, 0.3), -1, 0), 14, 0.38, 0.05, seed=40 + k, wig=0.45)
        F.append(sweep(pts, [0.09 * (1 - i / len(pts) * 0.6) for i in range(len(pts))], vein, seg=5, name='vein'))
    def coil(x0, x1, y0, y1, r, turns, rad, z=0.0, ph=0.0):
        n = int(turns * 8); pts = []
        for i in range(n + 1):
            t = i / n; a = ph + t * turns * 2 * math.pi
            pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + math.sin(a) * r, z + math.cos(a) * r))
        F.append(sweep(pts, [rad * (1 - 0.5 * i / n) for i in range(n + 1)], vein, seg=5, name='coil'))
    coil(6.0, -1.5, YB, YB, 0.25, 7, 0.09); coil(6.0, 2.5, YB + 0.05, YB - 0.05, 0.27, 3, 0.07, ph=2.0)
    a, b = xs[9], xs[10]; coil(a, b, topy(a) - 0.1, YB + 0.1, 0.13, 3, 0.06)
    a, b = xs[10], xs[11]; coil(a, b, YB + 0.1, topy(b) - 0.1, 0.13, 3, 0.06, ph=1.0)
    for k, (y0, y1, x1) in enumerate(((10.9, 11.6, 1.6), (11.9, 11.2, 3.2))):  # over the sign's face (the gut is reading it)
        pts = [(5.4 - (5.4 - x1) * t, y0 + (y1 - y0) * t + 0.15 * math.sin(t * 9 + k), -0.37) for t in [i / 14 for i in range(15)]]
        F.append(sweep(pts, [0.07 - 0.003 * i for i in range(15)], vein, seg=5, name='signvein'))
    # --- intestine draped over the top (sausage bulges), hanging down front and back
    ip = cat_rom([(3.6, 11.6, 0.95), (3.0, 13.0, 0.75), (2.2, 13.45, 0.1), (1.8, 12.9, -0.62), (1.5, 12.3, -0.75), (1.1, 13.0, -0.1), (0.0, 13.55, 1.15),
                  (-1.2, 13.45, 0.7), (-2.4, 13.5, 0.0), (-3.6, 13.3, -0.6), (-5.9, 12.55, -0.75), (-6.4, 11.2, -0.8), (-7.0, 12.1, -0.75), (-7.3, 13.4, -0.2), (-7.6, 13.4, 0.6),
                  (-7.8, 12.0, 0.95), (-7.9, 11.0, 0.95)], 5)
    ir_ = [0.42 + 0.07 * math.cos(i * 1.3) for i in range(len(ip))]
    gut = sweep(ip, ir_, flesh, seg=8, name='intestine'); GK.lump(gut, 0.03, 2.0, seed=9); F.append(gut)
    for o in F:
        GK.wet(o); uv_tile(o, 0.5)
    O += F
    bpy.context.view_layer.update()
    meta = {'district': 'gut', 'landmark': True, 'col': [18.0, 14.0, 3.0], 'opening': [12.0, 10.0],
            'boxes': [[-7.5, 5.0, 0.0, 3.0, 10.0, 3.0], [7.5, 5.0, 0.0, 3.0, 10.0, 3.0], [0.0, 11.5, 0.0, 18.0, 3.0, 3.0]],
            'eye': [0, 13.42, -0.9], 'sign': "WELCOME TO THE GUT. DON'T PET ANYTHING.", 'pulse': [m.name for m in (flesh, vein)]}
    meta['_lodpick'] = [o for o in O if BK._diag(o) > 1.6 and min(o.dimensions) > 0.05]
    return O, meta


# ================================================================================================ saloons
# one pre-war four-door saloon (4.4 m, 2.55 m wheelbase, 0.6 m tyres: the proportions of a real 80s three-box saloon),
# built two ways: the Bottom's drivable SOFA-CAR and the dead rush-hour WRECK that jams the Commute. Front = -z.
WBZ, WR = (-1.33, 1.22), 0.3  # axle z (front, rear), wheel radius


def saloon_side(ar=0.37, ay=0.3, sill=0.28):
    pts = [(-2.2, 0.34), (-2.23, 0.56), (-2.19, 0.76), (-2.06, 0.82), (-0.78, 0.9), (1.38, 0.92), (2.12, 0.9), (2.2, 0.78), (2.23, 0.55), (2.2, 0.34), (2.14, sill)]
    for zc in (WBZ[1], WBZ[0]):
        pts += [(zc + ar * math.cos(math.radians(a)), ay + ar * math.sin(math.radians(a)) if 0 < a < 180 else sill) for a in range(0, 181, 30)]
    pts.append((-2.14, sill))
    return pts


def saloon_body(paint, glass, chrome, misc, R, W=1.7, bev=0.05, seg=2, pillars=True):
    O = []
    body = side(saloon_side(), W, (0, 0, 0), paint, bev=bev, seg=seg, name='body'); O.append(body)
    gh = side([(-0.78, 0.9), (-0.06, 1.4), (0.98, 1.41), (1.38, 0.92)], W - 0.24, (0, 0, 0), glass, bev=0.02, seg=1, name='greenhouse')
    apply_mods(gh)
    for v in gh.data.vertices:
        if v.co.z > 1.0: v.co.x *= 0.88
    O.append(gh)
    rf = side([(-0.08, 1.39), (1.0, 1.4), (0.96, 1.46), (-0.02, 1.46)], (W - 0.24) * 0.9, (0, 0, 0), paint, bev=0.02, seg=1, name='roof'); O.append(rf)
    if pillars:
        for sx in (-1, 1):
            hw0, hw1 = (W - 0.24) / 2 + 0.01, (W - 0.24) / 2 * 0.88 + 0.01
            O.append(rod((sx * hw0, 0.9, -0.76), (sx * hw1, 1.41, -0.07), 0.04, paint, seg=4))
            O.append(rod((sx * hw0, 0.92, 1.36), (sx * hw1, 1.41, 0.97), 0.06, paint, seg=4))
            O.append(rod((sx * hw0, 0.92, 0.42), (sx * hw1, 1.41, 0.42), 0.035, paint, seg=4))
    for z in (-2.21, 2.21): O.append(box((W + 0.06, 0.15, 0.13), (0, 0.43, z), chrome, bev=0.03, seg=1))
    return O


def tyre(c, m_t, m_h, R, r=WR, w=0.2, seg=16, flat=0.0, hubm=None):
    rr = r * 0.66
    prof = [(rr, -w / 2), (r * 0.92, -w / 2), (r, -w * 0.3), (r, w * 0.3), (r * 0.92, w / 2), (rr, w / 2)]
    t = lathe(prof, c, m_t, seg=seg, axis='x', name='tyre'); fit(t, R['rubber'])
    h = cyl(rr * 1.02, w * 1.04, c, hubm or m_h, axis='x', seg=max(8, seg // 2), bev=0.01, name='hub')
    if flat:
        for o in (t, h):
            apply_mods(o)
            for v in o.data.vertices:
                g = o.matrix_world @ v.co; y = g.z
                if y < c[1] - r * (1 - flat):
                    k = (c[1] - r * (1 - flat) - y) / (r * flat + 1e-6)
                    v.co.z += (c[1] - r * (1 - flat) - y) * 0.8; v.co.x *= 1 + 0.18 * k
            o.data.update()
    return [t, h]


def build_sofacar():
    M_ = Atlas('scar_misc_t', 128); R = {}
    tiedye(M_.sub(0, 0, 64, 64), DYE, seed=91, arms=3, twist=7); R['tiedye'] = M_.rect(0, 0, 64, 64)
    vl = M_.sub(64, 0, 64, 32); crust(vl, 0xc9a8ff, 0.07, seed=92); vl[::3] *= 0.94; grime(vl, 0x8a6aa8, 0.15, seed=3, blob=4); R['velvet'] = M_.rect(64, 0, 64, 32)
    pl = M_.sub(64, 32, 48, 16); pl[:] = hexrgb(0xf4f0e0); pl[0:2] = pl[-2:] = hexrgb(0xff4fd8); text_px(pl, 'SOFA-1', 6, 5, 1, INK); R['plate'] = M_.rect(64, 32, 48, 16)
    gr = M_.sub(64, 48, 32, 16); gr[:] = hexrgb(0x1a181e); gr[2:14, 1::3] = hexrgb(0x8a8a96); R['grille'] = M_.rect(64, 48, 32, 16)
    for k, (nm, c) in enumerate((('rubber', 0x1c1a20), ('bgreen', 0x39ff14), ('bpink', 0xff4fd8), ('byel', 0xffe14d), ('wood', 0xb87a40), ('steel', 0x4a444c),
                                 ('primer', 0x9a9aa6), ('black', 0x141418), ('wire', 0x2a2a30), ('hook', 0xc8ccd4), ('rust', 0xa0482a), ('white', 0xfbfaf6))):
        R[nm] = M_.fill((k % 8) * 16, 64 + (k // 8) * 16, 16, 16, c)
    misc = mat('scar_misc', 0xffffff, rough=0.6, clearcoat=0.3, tex=M_.image())
    def pt(px):
        crust(px, 0xfbf8f4, 0.03, seed=93, speck=[(0xb0602a, 0.01), (0xd8d0c8, 0.02)], block=2)
        rr = np.random.default_rng(4)
        for k in range(5): px_disc(px, rr.uniform(0, 64), rr.uniform(0, 64), rr.uniform(1.5, 4), 0xc0703a); px_disc(px, rr.uniform(0, 64), rr.uniform(0, 64), 1.2, 0x8a4020)
        for k in range(3): px_disc(px, rr.uniform(0, 64), rr.uniform(0, 64), rr.uniform(2, 4), 0xc8c4cc)
    paint = mat('scar_paint', 0xffffff, rough=0.2, clearcoat=1.0, metal=0.15, tex=tex_canvas('scar_paint_t', 64, 64, pt))
    chrome = plain('scar_chrome', 0xe0e4ec, rough=0.14, metal=1.0, var=0.06, seed=94, speck=0x8a5a3a, p=0.02)
    glass = mat('scar_glass', 0x1a2a3a, rough=0.06, metal=0.5, clearcoat=1.0)
    G = Atlas('scar_glow_t', 32, 16); R['head'] = G.fill(0, 0, 8, 8, 0xfff2c0); R['tail'] = G.fill(8, 0, 8, 8, 0xff2020); R['amber'] = G.fill(16, 0, 8, 8, 0xffa020)
    R['b0'] = G.fill(0, 8, 8, 8, 0xffe14d); R['b1'] = G.fill(8, 8, 8, 8, 0xff6fd8); R['b2'] = G.fill(16, 8, 8, 8, 0x4fd8ff); R['b3'] = G.fill(24, 8, 8, 8, 0x7dff4f)
    glow = mat('scar_glow', 0xffffff, rough=0.25, tex=G.image(), emit=0xffffff, strength=3.0, emit_tex=True)
    O = saloon_body(paint, glass, chrome, misc, R)
    W = 1.7
    # the nose and tail: grille, lamps, plate, mirrors, a replaced (primer grey) rear door, door seams
    O.append(fit(box((0.9, 0.2, 0.04), (0, 0.63, -2.215), misc), R['grille'], mode='front'))
    for sx in (-1, 1):
        O.append(fit(box((0.34, 0.15, 0.05), (sx * 0.6, 0.64, -2.205), glow, bev=0.01, seg=1), R['head']))
        O.append(fit(box((0.1, 0.08, 0.05), (sx * 0.76, 0.5, -2.2), glow), R['amber']))
        O.append(fit(box((0.36, 0.14, 0.05), (sx * 0.58, 0.66, 2.215), glow, bev=0.01, seg=1), R['tail']))
        O.append(box((0.07, 0.1, 0.16), (sx * (W / 2 + 0.06), 0.97, -0.68), paint, bev=0.02, seg=1))
        for z in (-0.06, 0.95): O.append(fit(box((0.01, 0.56, 0.012), (sx * (W / 2 + 0.002), 0.62, z), misc), R['black']))
        for z in (-0.5, 0.5): O.append(box((0.03, 0.03, 0.15), (sx * (W / 2 + 0.01), 0.82, z), chrome))
    O.append(fit(box((0.012, 0.56, 0.98), (W / 2 + 0.004, 0.6, 0.44), misc, rot=(0.0, 0, 0.0)), R['primer']))
    O.append(fit(box((0.42, 0.13, 0.012), (0, 0.42, -2.28), misc), R['plate'], mode='front'))
    O.append(fit(box((0.42, 0.13, 0.012), (0, 0.6, 2.235), misc), R['plate'], mode='front'))
    # roof rack, the sofa bolted on facing forward, bungee cords over it, string lights, a wok dish on a pole
    for z in (0.05, 0.9):
        O.append(box((1.5, 0.04, 0.05), (0, 1.505, z), chrome, bev=0.01, seg=1))
        for sx in (-1, 1): O.append(box((0.05, 0.05, 0.07), (sx * 0.68, 1.475, z), chrome))
    S = []; Y0 = 1.525
    S.append(fit(box((1.9, 0.22, 0.82), (0, Y0 + 0.11, 0), misc, bev=0.03, seg=1), R['velvet']))
    for sx in (-1, 1):
        S.append(fit(box((0.21, 0.41, 0.84), (sx * 0.86, Y0 + 0.215, 0), misc, bev=0.04, seg=1), R['velvet']))
        S.append(fit(cyl(0.12, 0.86, (sx * 0.86, Y0 + 0.44, 0), misc, axis='z', seg=8, bev=0.02), R['velvet']))
    S.append(fit(box((1.5, 0.44, 0.2), (0, Y0 + 0.42, 0.31), misc, bev=0.04, seg=1), R['velvet']))
    for i, x in enumerate((-0.5, 0.0, 0.5)):
        S.append(fit(pillow((0.5, 0.15, 0.6), (x, Y0 + 0.29, -0.08), misc, puff=0.2, top=1.3, rot=(0.02 * (i - 1), 0.03 * (1 - i), 0.02 * (i - 1))), R['tiedye' if i == 1 else 'velvet']))
        S.append(fit(pillow((0.48, 0.38, 0.16), (x, Y0 + 0.55, 0.12), misc, puff=0.14, pinch=0.05, rot=(0.22, 0.02 * (i - 1), 0.03 * (1 - i))), R['velvet']))
    O += S
    for sx in (-1, 1):
        for z in (0.05, 0.75): O.append(box((0.06, 0.12, 0.05), (sx * 0.7, 1.56, z), chrome))
    for k, (z, col) in enumerate(((-0.22, 'bgreen'), (0.12, 'bpink'))):
        pts = [(W / 2 + 0.01, 0.92, z), (0.98, 1.36, z), (0.98, 1.8, z), (0.6, 1.9, z), (0.0, 1.92, z), (-0.6, 1.9, z), (-0.98, 1.8, z), (-0.98, 1.36, z), (-(W / 2 + 0.01), 0.92, z)]
        O.append(fit(sweep(pts, 0.016, misc, seg=4), R[col]))
        for sx in (-1, 1): O.append(fit(box((0.03, 0.06, 0.03), (sx * (W / 2 + 0.02), 0.9, z), misc), R['hook']))
    wire = [(-0.95, 2.21, 0.36), (-0.95, 1.6, -0.6), (-0.8, 0.95, -1.4), (-0.4, 0.83, -2.05), (0.4, 0.83, -2.05), (0.8, 0.95, -1.4), (0.95, 1.6, -0.6), (0.95, 2.21, 0.36)]
    wp = cat_rom(wire, 4)
    for k in range(len(wp)):  # sag between the anchor points
        x, y, z = wp[k]; wp[k] = (x, y - 0.05 * math.sin(k * math.pi / 4) ** 2, z)
    O.append(fit(tube(wp, 0.008, misc, seg=4), R['wire']))
    for k in range(2, len(wp) - 2, 2):
        x, y, z = wp[k]; O.append(fit(ball(0.035, (x, y - 0.035, z), glow, seg=6, rings=3), R['b%d' % (k // 2 % 4)]))
    for sx in (-1, 1): O.append(rod((sx * 0.95, 1.9, 0.36), (sx * 0.95, 2.24, 0.36), 0.015, chrome, seg=4))
    O.append(rod((0.75, 1.9, 0.4), (0.75, 2.5, 0.42), 0.02, chrome, seg=5))
    wk = [lathe([(0.0, 0.0), (0.17, 0.03), (0.27, 0.1), (0.3, 0.15), (0.27, 0.12), (0.17, 0.05), (0.0, 0.01)], (0, 0, 0), misc, seg=12, axis='y', name='wok')]
    fit(wk[0], R['steel'])
    wk.append(fit(sweep([(0, 0.15, -0.3), (0, 0.2, -0.2), (0, 0.3, -0.02)], 0.005, misc, seg=4), R['hook']))
    wk.append(fit(ball(0.04, (0, 0.32, 0), misc, seg=6, rings=4, scale=(1, 0.5, 1)), R['hook']))
    xform(wk, rot=(-0.9, 0.5, 0), move=(0.75, 2.5, 0.42)); O += wk
    for o in O:
        if o.data.materials and o.data.materials[0] in (paint, chrome): uv_tile(o, 0.6)
    # wheels: their own nodes, pivots on the axles
    sep = {}; wheels = {}
    for nm, (sx, zc) in (('wheel_fl', (1, WBZ[0])), ('wheel_fr', (-1, WBZ[0])), ('wheel_rl', (1, WBZ[1])), ('wheel_rr', (-1, WBZ[1]))):
        c = (sx * 0.74, WR, zc)
        parts = tyre(c, misc, chrome, R)
        for o in parts[1:]: uv_tile(o, 0.3)
        lod = [fit(lathe([(WR * 0.7, -0.1), (WR, -0.07), (WR, 0.07), (WR * 0.7, 0.1)], c, misc, seg=8, axis='x'), R['rubber'])]
        sep[nm] = (parts, c, lod); wheels[nm[6:]] = [round(v, 3) for v in c]
    bpy.context.view_layer.update()
    meta = {'district': 'bottom', 'vehicle': True, 'col': [W, 1.45, 4.5], 'paint': ['scar_paint'], 'wheels': wheels, 'wheel_r': WR, 'wheelbase': WBZ[1] - WBZ[0],
            'seats': [[-0.5, 1.75, -0.08], [0.0, 1.75, -0.08], [0.5, 1.75, -0.08]], 'driver': [0.38, 0.9, 0.1],
            'lights': [[0, 0.65, -2.4, 0xfff2c0], [0, 1.9, -0.2, 0xffd27a]], '_sep': sep}
    meta['_lodpick'] = [o for o in O if BK._diag(o) > 0.6 and min(o.dimensions) > 0.02]
    return O, meta


def build_carwreck():
    M_ = Atlas('cw_misc_t', 64); R = {}
    for k, (nm, c) in enumerate((('rubber', 0x26242a), ('rust', 0x9a4a24), ('dull', 0x8a8a92), ('black', 0x18161a), ('paper', 0xf2ecd8), ('paper2', 0xe8e0c8),
                                 ('lamp', 0xd8d0b8), ('red', 0x9a2a2a))):
        R[nm] = M_.fill((k % 4) * 16, (k // 4) * 16, 16, 16, c)
    pp = M_.sub(0, 32, 32, 32); crust(pp, 0xf2ecd8, 0.03, seed=101)
    for y in range(3, 30, 4): pp[y, 3:28 - (y * 5) % 9] = hexrgb(0x8a8a96)
    pp[3:9, 3:9] = hexrgb(0xff4fd8); R['memo'] = M_.rect(0, 32, 32, 32)
    pl = M_.sub(32, 32, 32, 16); pl[:] = hexrgb(0xd8d4c4); text_px(pl, '17:30', 1, 5, 1, 0x3a3a44); R['plate'] = M_.rect(32, 32, 32, 16)
    misc = mat('cw_misc', 0xffffff, rough=0.75, tex=M_.image())
    def pt(px):  # faded paint, rust blooms, ash dust on top
        crust(px, 0xece8e0, 0.05, seed=102, speck=[(0xb0602a, 0.03), (0xd8d4cc, 0.06)], block=2)
        rr = np.random.default_rng(6)
        grime(px, 0xb0602a, 0.1, seed=9, blob=8); grime(px, 0x7a3a1a, 0.05, seed=10, blob=4)
        for k in range(7): x = int(rr.uniform(0, 62)); drip(px, x, int(rr.uniform(0, 40)), int(rr.uniform(6, 20)), 0x9a4a22)
        grime(px, 0xd8d0c0, 0.14, seed=7, blob=6)
    paint = mat('cw_paint', 0xffffff, rough=0.7, clearcoat=0.15, tex=tex_canvas('cw_paint_t', 64, 64, pt))
    def gl(px):  # smashed glass: dark, a white crack web, holes
        px[:] = hexrgb(0x1e2630); rr = np.random.default_rng(8)
        for c_ in ((20, 18), (44, 40)):
            for k in range(9):
                a = rr.uniform(0, 6.28); x, y = c_
                for st in range(5): nx, ny = x + math.cos(a) * 4, y + math.sin(a) * 4; px_line(px, x, y, nx, ny, 0xd8e0e8, 1); x, y = nx, ny; a += rr.uniform(-0.5, 0.5)
            px_disc(px, c_[0], c_[1], 3, 0x06080a)
    glass = mat('cw_glass', 0xffffff, rough=0.12, metal=0.3, clearcoat=0.6, tex=tex_canvas('cw_glass_t', 64, 64, gl))
    W = 1.72
    O = saloon_body(paint, glass, misc, misc, R, W=W, bev=0.04, seg=1, pillars=False)
    fit(O[-1], R['rust']); fit(O[-2], R['dull'])
    uv_tile(O[0], 0.7); uv_tile(O[2], 0.7); uv_tile(O[1], 1.0)
    for sx in (-1, 1):
        O.append(fit(box((0.07, 0.09, 0.14), (sx * (W / 2 + 0.03), 0.97, -0.68), misc), R['black']))
        O.append(fit(box((0.32, 0.14, 0.04), (sx * 0.6, 0.64, -2.2), misc), R['lamp']))
        O.append(fit(box((0.34, 0.12, 0.04), (sx * 0.58, 0.66, 2.2), misc), R['red']))
    O.append(fit(box((0.42, 0.13, 0.012), (0, 0.6, 2.225), misc), R['plate'], mode='front'))
    xform([O[3]], rot=(0, 0, 0.09), move=(0, -0.05, -0.03), pivot=(0.9, 0.43, -2.21))  # the front bumper, hanging off one bolt
    # the bonnet popped open from the shunt, papers blown onto it, the roof and the boot
    bn = side([(-2.06, 0.0), (-0.85, 0.0), (-0.85, 0.035), (-2.06, 0.035)], W - 0.1, (0, 0.84, 0), paint)
    uv_tile(bn, 0.7); xform([bn], rot=(-0.22, 0, 0.03), pivot=(0, 0.86, -0.86)); O.append(bn)
    for k, (x, y, z, a, rz) in enumerate(((0.3, 1.465, 0.3, 0.4, 0.0), (-0.25, 1.465, 0.6, -0.7, 0.0), (0.4, 0.935, 1.7, 1.2, 0.03), (-0.5, 0.925, 1.9, 0.2, 0.02))):
        O.append(fit(box((0.21, 0.003, 0.3), (x, y, z), misc, rot=(rz, a, rz)), R['memo' if k % 2 == 0 else 'paper2']))
    sep_parts = []
    for sx, zc in ((1, WBZ[0]), (-1, WBZ[0]), (1, WBZ[1]), (-1, WBZ[1])):
        sep_parts += tyre((sx * 0.75, WR, zc), misc, misc, R, seg=10, flat=0.3, hubm=misc)
    for o in sep_parts[1::2]: fit(o, R['rust'])
    O += sep_parts
    bpy.context.view_layer.update()
    for o in sep_parts: grd(o, 0.0)
    meta = {'district': 'commute', 'col': [W, 1.42, 4.46], 'paint': ['cw_paint'], 'note': 'dead pre-war saloon, the Final Quarter rush hour; scatter (tint per car)'}
    L = side(saloon_side(), W, (0, 0, 0), paint, name='lbody'); uv_tile(L, 0.7)
    L2 = side([(-0.78, 0.9), (-0.06, 1.44), (0.98, 1.45), (1.38, 0.92)], W - 0.3, (0, 0, 0), glass); uv_tile(L2, 1.0)
    LW = [fit(cyl(WR, 0.2, (sx * 0.75, WR, zc), misc, axis='x', seg=6), R['rubber']) for sx, zc in ((1, WBZ[0]), (-1, WBZ[0]), (1, WBZ[1]), (-1, WBZ[1]))]
    meta['_lod'] = [L, L2] + LW
    return O, meta


BUILDERS = [('sofacar', build_sofacar), ('carwreck', build_carwreck), ('gutgate', build_gutgate), ('lostpile', build_lostpile), ('returns_counter', build_returns_counter), ('machine', build_machine), ('lostfound_sign', build_lostfound_sign)]

if __name__ == '__main__':
    run2(BUILDERS)
