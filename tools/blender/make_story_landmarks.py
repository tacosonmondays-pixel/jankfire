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
        while len(me.uv_layers) > 1: me.uv_layers.remove(me.uv_layers[-1])
        for n in nodes + lods:
            while len(n.data.uv_layers) > 1: n.data.uv_layers.remove(n.data.uv_layers[-1])
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
    ld = S.sub(0, 34, 128, 46); crust(ld, 0x1a0a2e, 0.05, seed=3)
    write(ld, 'now loading:', 4, 6, 2, 0xffffff); write(ld, 'tuesday', 4, 24, 2, 0xff8ad8)
    ld[40:43, 4:124] = hexrgb(0x3a2a5a); ld[40:43, 4:96] = hexrgb(GREEN)
    R = {'sky': S.rect(0, 0, 128, 34), 'loading': S.rect(0, 34, 128, 46)}
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
    write(pn, 'insert', 6, at(4.98), 1, 0xffffff); write(pn, 'coin', 6, at(4.98) + 8, 1, 0xffffff)
    write(pn, 'bills', 40, at(4.98), 1, 0xffffff)
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
    write(fl, 'thank u for your loyalty', 7, 30, 1, 0xff8ad8)
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
    O.append(box((MW + 0.06, 0.07, MD + 0.06), (0, 5.985, 0), chrome, bev=0.02, seg=1))
    O.append(box((MW - 0.6, 0.32, MD - 0.6), (0, 0.16, 0), decal, bev=0.02, seg=1))
    T(O[:3]); fit(O[3], R['grille'])
    for sx in (-1, 1):
        for sz in (-1, 1):
            O.append(box((0.11, 5.66, 0.11), (sx * MW / 2, 3.16, sz * MD / 2), chrome, bev=0.025, seg=1))  # corner guards
            O.append(lathe([(0.0, 0.0), (0.22, 0.0), (0.22, 0.05), (0.14, 0.12), (0.11, 0.32), (0.0, 0.32)], (sx * (MW / 2 - 0.32), 0, sz * (MD / 2 - 0.32)), chrome, seg=10, axis='y'))
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
    for a, b in zip(shelves, shelves[1:] + [y1]):
        O.append(fit(box((x1 - x0 + 0.01, b - a, 0.04), (WCX, (a + b) / 2, -0.21), sim), R['sky'], mode='front'))
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
    sy = 2.75; Y = sy + 0.025 + 0.07
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
    # row 3: TINY ISLANDS (water, three islands, a palm, a shark) and a DESERT (dunes, cacti)
    sy = 3.75; Y = sy + 0.025 + 0.05
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
    # row 4: THE CITY BLOCK (Jankburg in a box) and THE SUBURB
    sy = 4.75; Y = sy + 0.025 + 0.06
    O.append(base(-0.95, 0.95, sy, 'road', h=0.06))
    rnd = random.Random(8)
    for k, (bx, bz) in enumerate(((-0.75, -0.65), (-0.45, -0.62), (-0.15, -0.68), (0.2, -0.6), (0.55, -0.66), (-0.6, -1.25), (0.4, -1.28))):
        h = rnd.uniform(0.25, 0.75) if bz > -1 else rnd.uniform(0.15, 0.3)
        w = rnd.uniform(0.2, 0.3)
        O.append(fit(box((w, h, 0.26), (bx, Y + h / 2, bz), sim), R[('b_teal', 'b_pink', 'b_yel', 'b_white')[k % 4]]))
    O.append(fit(cyl(0.05, 0.7, (0.82, Y + 0.35, -0.62), sim, axis='y', seg=6, r2=0.03), R['b_white']))
    O.append(fit(ball(0.06, (0.82, Y + 0.72, -0.62), sim, seg=6, rings=4), R['hazard']))
    O.append(base(1.05, 1.95, sy, 'grass', h=0.06))
    for (hx, hz) in ((1.3, -0.75), (1.72, -1.15)):
        O.append(fit(box((0.3, 0.2, 0.26), (hx, Y + 0.1, hz), sim), R['b_pink' if hx < 1.5 else 'b_yel']))
        roof = side([(-0.15, 0.0), (0.15, 0.0), (0.0, 0.13)], 0.34, (hx, Y + 0.2, hz), sim); O.append(fit(roof, R['roof']))
    for (tx, tz) in ((1.75, -0.6), (1.2, -1.25)):
        O.append(fit(cyl(0.09, 0.26, (tx, Y + 0.18, tz), sim, axis='y', seg=6, r2=0.0), R['leaf']))
        O.append(fit(cyl(0.015, 0.06, (tx, Y + 0.03, tz), sim, axis='y', seg=4), R['trunk']))
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
    for k, (cx, cy, a, L_) in enumerate(((1.95, 2.3, 0.6, 0.9), (2.2, 2.05, -0.3, 0.6), (1.75, 2.0, 1.2, 0.5))):
        O.append(fit(box((L_, 0.1, 0.006), (cx, cy, FZ - 0.003), decal, rot=(0, 0, a)), R['tape']))
    sgn = fit(box((1.15, 0.5, 0.012), (0.0 + 0.3, 5.3, FZ - 0.004), decal, rot=(0, 0, -0.07)), R['sign'], mode='front'); O.append(sgn)
    for (cx, cy) in ((-0.2, 5.55), (0.82, 5.5), (-0.2, 5.1), (0.8, 5.03)):
        O.append(fit(box((0.2, 0.07, 0.004), (cx, cy, FZ - 0.011), decal, rot=(0, 0, 0.7 if cx < 0 else -0.6)), R['tape']))
    for (rect, w, h, pos, a) in (('st_smile', 0.36, 0.36, (2.1, 4.95, FZ + 0.0), 0.2), ('st_norefund', 0.4, 0.15, (0.4, 1.6, FZ + 0.0), -0.08),
                                 ('st_1730', 0.5, 0.2, (PCX - 0.35, 3.0, FZ - 0.042), 0.1), ('st_love', 0.5, 0.2, (PCX + 0.35, 3.08, FZ - 0.042), -0.12)):
        if pos[2] == FZ + 0.0: pos = (pos[0], pos[1], FZ - 0.002)  # on the glass / the cabinet
        O.append(fit(box((w, h, 0.005), pos, decal, rot=(0, 0, a)), R[rect], mode='front'))
    O.append(fit(box((0.005, 0.5, 0.5), (-MW / 2 - 0.0, 3.8, -1.0), decal, rot=(0.3, 0, 0)), R['st_dye']))
    O.append(fit(box((0.005, 0.25, 0.62), (MW / 2 + 0.0, 5.4, -0.6), decal, rot=(-0.05, 0, 0)), R['st_1730']))
    O.append(fit(box((0.005, 0.25, 0.62), (MW / 2 + 0.0, 1.4, -0.9), decal, rot=(0.1, 0, 0)), R['st_love']))
    # power: a junction box on the right flank, three fat cables to the floor and off to the depot wall, tape bands
    jb = fit(box((0.14, 0.6, 0.5), (MW / 2 + 0.06, 3.4, 0.4), decal, bev=0.02, seg=1), R['grey']); O.append(jb)
    cabs = []
    for k, (dz, sag) in enumerate(((-0.12, 0.0), (0.02, 0.1), (0.16, 0.05))):
        pts = [(MW / 2 + 0.12, 3.2, 0.4 + dz), (MW / 2 + 0.3 + 0.04 * k, 2.9, 0.42 + dz), (MW / 2 + 0.42 + 0.05 * k, 1.6, 0.5 + dz),
               (MW / 2 + 0.5 + 0.06 * k, 0.4, 0.7 + dz), (MW / 2 + 0.6 + 0.05 * k, 0.06, 1.2 + dz), (MW / 2 + 0.75, 0.06 + 0.002 * k, 1.9 + dz * 1.5),
               (MW / 2 + 0.3 - 0.1 * k, 0.06, 2.4 + dz)]
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
    meta['_lodpick'] = [o for o in O if 'coil' not in o.name and 'jumper' not in o.name and BK._diag(o) > 0.95]
    return O, meta


BUILDERS = [('machine', build_machine)]

if __name__ == '__main__':
    run2(BUILDERS)
