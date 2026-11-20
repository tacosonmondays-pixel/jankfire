# JANKFIELD HIGH (20 Nov 2026), the zombies school: the kit (headless Blender) and the layout Studio builds it from.
# The rooms, walls, doors, windows, ramps, furniture and the zombies mode's markers all come from school_layout.py
# (plain Python); this script turns them into
#   roblox/studio-tools/JankfieldHighLayout.luau   the hit boxes (+ fences, ramps), spawns, lights, and the `zm` table
#                                                  WebArena turns into the ZM folder of markers (roblox/docs/ZOMBIES.md)
#   <out>/school.glb                               the kit (the look), when it's built (not with --layout-only)
# run: blender -b --factory-startup -P tools/roblox/school_models.py -- <out dir> [<preview dir>] [--layout-only]
#      [--blockout]  (--blockout: the layout says blockout = true: WebArena shows the hit boxes in their colours, for the
#                     mode's gameplay tests before the kit is in)
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arenakit as K
import school_layout as L

OUT_DIR = K.ARGS[0] if K.ARGS else os.path.join(K.HERE, 'out_school')
PREVIEW = K.ARGS[1] if len(K.ARGS) > 1 else None
LAYOUT = os.path.normpath(os.path.join(K.HERE, '..', '..', 'roblox', 'studio-tools', 'JankfieldHighLayout.luau'))
INFO = dict(name='JankfieldHigh', title='JANKFIELD HIGH', look='school', mapId='school', kit='school',
            origin=(0, 0, -66000), killY=-60, centreX=0, maxTeam=0,
            about='a hand-made zombies map (tools/roblox/school_layout.py), built to roblox/docs/ZOMBIES.md')

# the hit boxes' looks: layout material -> (Roblox material for impacts, colour, name). In the blockout these are what
# you see too: quiet greys and creams, colour only where a room needs it to read
MATS = {
    'plaster': ('SmoothPlastic', 'e3ddd0', 'plaster'), 'brick': ('Brick', '8c5e4e', 'brick'),
    'block': ('Concrete', 'b9b5ab', 'block'), 'glass': ('Glass', 'a9cfd8', 'glass'), 'earth': ('Concrete', '6b6359', 'earth'),
    'lino': ('SmoothPlastic', 'c4c2b8', 'lino'), 'tile': ('SmoothPlastic', 'd9d2c0', 'tile'),
    'terrazzo': ('Marble', 'd6d0c4', 'terrazzo'), 'restroomtile': ('Marble', 'd8dddc', 'restroomtile'),
    'concrete': ('Concrete', 'a39e93', 'concrete'), 'pavers': ('Pavement', 'b3a897', 'pavers'),
    'gymwood': ('WoodPlanks', 'c99c64', 'gymwood'), 'rubber': ('SmoothPlastic', '45474b', 'rubber'),
    'carpet': ('Fabric', '7c8590', 'carpet'), 'wood': ('WoodPlanks', 'a77d55', 'wood'),
    'roofdeck': ('Concrete', '9b9a93', 'roofdeck'), 'grass': ('Grass', '56703f', 'grass'), 'stair': ('Concrete', 'b1ada3', 'stair'),
    'rooflid': ('Concrete', '8d8b85', 'rooflid'), 'mainstair': ('Concrete', 'b6b1a6', 'stair'), 'landing': ('Concrete', 'b6b1a6', 'stair'),
    'fill': ('Concrete', 'a39e93', 'stair'), 'towerwall': ('Concrete', 'b9b5ab', 'block'), 'bleacher': ('WoodPlanks', 'b98d5c', 'bleacher'),
    'post': ('Metal', '7f868c', 'metal'), 'ramp': ('Concrete', 'bdb8ac', 'stair'), 'fence': ('Metal', '969da3', 'fence'),
    'hedge': ('Grass', '4b6639', 'hedge'), 'grating': ('DiamondPlate', '6c7177', 'grating'), 'roofg': ('Concrete', '7b7975', 'roof'),
    'greenglass': ('Glass', 'b9d8c2', 'glass'), 'furn': ('SmoothPlastic', 'b8b1a3', 'furniture'),
}
FURN_COL = {
    'desk': 'a98a68', 'teacherdesk': '8d6e52', 'lockers': '6f7f8f', 'bookshelf': '8a6a4c', 'lunchtable': 'c2b8a4',
    'labbench': '5d6670', 'fume': 'a8b4b8', 'servery': 'b8bcbc', 'kitchen': 'a9adad', 'fridge': 'c9cdcd', 'bench': 'a07c58',
    'reception': '8d6e52', 'pillar': 'd6d0c4', 'trophy': '8d6e52', 'boiler': '6e5a52', 'heater': '7a7f84', 'generator': '5f6b5a',
    'crate': '9a7a52', 'shelf': '7a7f84', 'workbench': '8a6a4c', 'stallwall': '9aa6a8', 'sinks': 'd8dcdc', 'bed': 'c8ccd0',
    'tree': '7a6a56', 'planter': '9a8f80', 'picnic': 'a07c58', 'hvac': '9ea3a6', 'towerleg': '7f868c', 'solar': '3d4650',
    'skylight': 'b8cdd6', 'dish': 'c9cccd', 'computers': '6a6e74', 'couch': '6d7f86', 'counter': '9a8a74', 'table': 'a98a68',
    'piano': '2f2f33', 'riser': '8a6a4c', 'rack': '5c6066', 'weightbench': '45474b', 'kiln': '8c5e4e', 'arttable': 'b0a48c',
    'easel': 'a07c58', 'drying': '9aa0a6', 'bigdesk': '6f5541', 'filing': '8e969c', 'chair': '6d7f86', 'cabinet': '9aa0a6',
    'globe': '6d8fa0', 'readtable': 'a98a68', 'desk_big': '8d6e52', 'mopsink': 'c8ccd0', 'cart': '6f7f8f', 'vault': 'a8754a',
    'mat': '5f7488', 'ballrack': '7f868c', 'showerwall': 'c8d0d0', 'cubbies': 'a98a68', 'bikerack': '7f868c', 'flagpole': 'c9cccd',
    'skeleton': 'e8e4d8', 'trash': '5f6b5a', 'plant': '5a7046', 'coffeetable': '8a6a4c',
}
def mat_of(m):
    if m in MATS: return MATS[m]
    if m.startswith('furn_'):
        k = m[5:]
        return ('SmoothPlastic', FURN_COL.get(k, 'b8b1a3'), 'furniture')
    raise KeyError(m)

# ================================================================ lights: warm ceiling panels room by room, the gym's
# high bays, lamp posts in the courtyard, floods on the roof, a light on each stairwell landing
def lights():
    for r in L.ROOMS:
        lv, look = r['lv'], r['look']
        if lv == 'R' or not r['floor'] or look in ('court', 'landing', 'gym', 'balcony', 'gymair') or r['tower']: continue
        x0, z0, x1, z1 = r['r']
        Ly = L.LV[lv]
        y = Ly + L.CEIL - 1.0
        sp = 30.0
        nx, nz = max(1, int(round((x1 - x0) / sp))), max(1, int(round((z1 - z0) / sp)))
        for i in range(nx):
            for j in range(nz):
                x, z = x0 + (i + 0.5) * (x1 - x0) / nx, z0 + (j + 0.5) * (z1 - z0) / nz
                col = 'ffe8cc' if look not in ('boiler', 'tunnel', 'storage', 'workshop') else 'ffd9a8'
                K.light('point', x, y, z, (0, -1, 0), 0.9, 26, 0, col)
    for (x, z) in ((84, -12), (84, 36), (120, -12), (120, 36), (148, 12)):          # the gym's high bays
        K.light('point', x, 34.0, z, (0, -1, 0), 1.3, 42, 0, 'fff1df')
    for (x, z) in ((-30, -24), (30, 24), (-30, 24), (30, -24)):                      # the courtyard's lamp posts
        K.light('point', x, 11.0, z, (0, -1, 0), 1.1, 30, 0, 'ffd9a8')
    for (x, z) in ((-90, -50), (-10, -50), (70, -50), (130, -60)):                   # floods on the roof
        K.light('point', x, 44.0, z, (0, -1, 0), 0.9, 40, 0, 'dfe6ff')
    for (tx, tz) in ((-110, -5), (150, -53)):                                        # each stairwell landing
        for y in (-16.0, 0.0, 16.0, 32.0):
            K.light('point', tx, y + 12.0, tz, (0, -1, 0), 0.8, 22, 0, 'ffe8cc')

def fmt(v): return K.fmt(v)
def vec(t): return '{%s}' % ','.join(fmt(float(x)) for x in t)

def zm_luau():
    Z = L.ZM
    q = lambda s: '"%s"' % s.replace('"', '\\"')
    o = ['\t-- the zombies mode\'s markers (roblox/docs/ZOMBIES.md): WebArena builds the ZM folder from this. Local studs.',
         '\tzm = {', '\t\tlabel = %s, start = %s,' % (q(Z['label']), q(Z['start'])),
         '\t\tnav = %s,' % vec(Z['nav']),
         '\t\t-- areas: { id, label, x0, y0, z0, x1, y1, z1 }', '\t\tareas = {']
    for a in Z['areas']:
        x0, z0, x1, z1 = a['r']
        o.append('\t\t\t{ %s, %s, %s },' % (q(a['id']), q(a['name']), ', '.join(fmt(v) for v in (x0, a['y'][0], z0, x1, a['y'][1], z1))))
    o.append('\t\t},')
    o.append('\t\t-- doors: the shutter\'s box (min, max) in the opening')
    o.append('\t\tdoors = {')
    for d in Z['doors']:
        o.append('\t\t\t{ a = %s, b = %s, price = %d, label = %s, min = %s, max = %s },' % (
            q(d['a']), q(d['b']), d['price'], q(d['name']), vec(d['box']['min']), vec(d['box']['max'])))
    o.append('\t\t},')
    o.append('\t\t-- windows: out (where a zombie appears), inn (where it lands inside), at (the boards\' middle), n (into the room), w, h')
    o.append('\t\twindows = {')
    for w in Z['windows']:
        o.append('\t\t\t{ area = %s, kind = %s, out = %s, inn = %s, at = %s, n = %s, w = %s, h = %s },' % (
            q(w['area']), q(w['kind']), vec(w['out']), vec(w['in']), vec(w['at']), vec(w['n']), fmt(w['w']), fmt(w['h'])))
    o.append('\t\t},')
    o.append('\t\tbuys = {')
    for b in Z['buys']:
        o.append('\t\t\t{ weapon = %s, price = %d, at = %s, n = %s },' % (q(b['w']), b['price'], vec(b['at']), vec(b['n'])))
    o.append('\t\t},')
    o.append('\t\tcrates = {')
    for c in Z['crates']: o.append('\t\t\t{ at = %s, n = %s },' % (vec(c['at']), vec(c['n'])))
    o.append('\t\t},')
    o.append('\t\tpower = { at = %s, n = %s },' % (vec(Z['power']['at']), vec(Z['power']['n'])))
    o.append('\t\tmach = { at = %s, n = %s },' % (vec(Z['mach']['at']), vec(Z['mach']['n'])))
    o.append('\t\tvoider = { at = %s, n = %s },' % (vec(Z['up']['at']), vec(Z['up']['n'])))
    o.append('\t\tcolas = {')
    for c in [Z['cola']] + Z['colas']: o.append('\t\t\t{ cola = %s, at = %s, n = %s },' % (q(c['id']), vec(c['at']), vec(c['n'])))
    o.append('\t\t},')
    o.append('\t\tspawns = { %s }, face = {0,0,-1},' % ', '.join(vec(p) for p in Z['spawns']))
    o.append('\t},')
    return '\n'.join(o) + '\n'

def write_layout():
    solid = [tuple(b[:6]) + mat_of(b[6]) for b in L.SOLID]
    rot = [tuple(r[:7]) + mat_of(r[7]) + (r[8],) for r in L.ROT]
    tilt = [tuple(t[:12]) + mat_of(t[12]) + (t[13], t[14]) for t in L.TILT]
    K.write_layout(LAYOUT, INFO, solid, [], [tuple(p) for p in L.SPAWNS], {'att': [], 'def': [], 'mid': []},
                   src='tools/roblox/school_models.py', rot=rot, tilt=tilt)
    with open(LAYOUT, encoding='utf-8') as f: txt = f.read().rstrip()
    assert txt.endswith('}')
    extra = ''
    if '--blockout' in K.FLAGS:
        extra += '\t-- (the blockout: WebArena shows the hit boxes in their colours until the kit is in)\n\tblockout = true,\n'
    extra += zm_luau()
    if SURFACES:
        extra += ('\t-- the kit\'s surfaces: a SurfaceAppearance picture per piece colour (WebArena; the meshes carry world UVs)\n'
                  '\tsurfaces = { %s },\n' % ', '.join('["%s"] = "%s"' % (L.TEXKEY[k], v) for k, v in sorted(SURFACES.items())))
    txt = txt[:-1] + extra + '}\n'
    with open(LAYOUT, 'w', newline='\n') as f: f.write(txt)
    print('LAYOUT %s: %d chars' % (LAYOUT, len(txt)))

# the pictures (tools/roblox/school_textures.py), uploaded as Images: name -> rbxassetid (20 Nov 2026, all approved)
SURFACES = {k: 'rbxassetid://%d' % v for k, v in {
    'lino': 140507969568773, 'cafetile': 110598245107944, 'terrazzo': 72007196220887, 'rtile_floor': 88801409286905,
    'rtile_wall': 119608007939948, 'hallwall': 128042008134468, 'classwall': 117747459921855, 'block': 121905920802081,
    'brick': 114560088115327, 'gymwood': 127686198604350, 'woodfloor': 124778878997898, 'carpet': 93910495940944,
    'ceiling': 101271808462044, 'concrete': 92719214966737, 'chalkboard': 126513689391105, 'pavers': 90576630175655,
    'rubber': 78191784089177, 'lockers': 124572738338924}.items()}

# ================================================================ THE KIT: the architecture (furniture: school_props.py)
import school_textures as ST
T = L.TEXKEY
PAINT, WOODTRIM, METAL, DARK, FRAME, GLASS = 'ddd4c2', '8f6f50', 'a7adb2', '4a4f55', '9aa1a6', 'b8d4dc'
GRASS, HEDGE, ASPHALT, WALK, COPING, PLINTH, POST, MESH = '5a7344', '4d6a3b', '3e4043', 'b5b0a6', 'a5a198', '8a857b', '6a7076', 'a9b1b6'
STEPC, NOSE = 'bdb8ad', '585d63'
LV = L.LV
def lvl_of(y):
    return 'B' if y < -8 else ('G' if y < 8 else ('U' if y < 24 else 'R'))
MODEL_BASE = {'sc_furn_' + k: (32.0 if k == 'R' else v) for k, v in L.LV.items()}
def M_(name, lv):
    """a model name carrying its level, so the UV pass can put a wall picture's floor line on that level's floor"""
    m = '%s_%s' % (name, lv)
    MODEL_BASE[m] = 32.0 if lv == 'R' else LV[lv]
    return m

FLOORTEX = {'lino': 'lino', 'tile': 'cafetile', 'terrazzo': 'terrazzo', 'restroomtile': 'rtile_floor', 'concrete': 'concrete',
            'pavers': 'pavers', 'gymwood': 'gymwood', 'rubber': 'rubber', 'carpet': 'carpet', 'wood': 'woodfloor',
            'roofdeck': 'concrete', 'stair': 'concrete', 'rooflid': 'concrete'}
WALLTEX = {'hall': 'hallwall', 'lobby': 'hallwall', 'landing': 'hallwall', 'cafe': 'hallwall', 'stairhole': 'hallwall',
           'classroom': 'classwall', 'lab': 'classwall', 'art': 'classwall', 'music': 'classwall', 'complab': 'classwall', 'nurse': 'classwall',
           'restroom': 'rtile_wall', 'lockerroom': 'rtile_wall',
           'storage': 'block', 'janitor': 'block', 'workshop': 'block', 'tunnel': 'block', 'boiler': 'block', 'tower': 'block',
           'gym': 'block', 'balcony': 'block', 'gymair': 'block', 'weights': 'block', 'gymtop': 'block',
           'court': 'brick', 'courtair': 'brick', 'roof': 'brick', 'roofx': 'brick'}
PANELLED = ('library', 'office', 'principal', 'lounge')     # warm paint over a wood wainscot
def wallcol(r):
    if r is None: return T['brick']
    lk = r['look']
    if lk in PANELLED: return PAINT
    return T[WALLTEX.get(lk, 'classwall')]

def bx(model, col, b, kind='plastic', bev=0.0):
    x0, y0, z0, x1, y1, z1 = b
    if x1 - x0 < 1e-3 or y1 - y0 < 1e-3 or z1 - z0 < 1e-3: return
    # (unbevelled boxes shade flat: smoothed normals on a big slab's edges drew dark seams between floor pieces)
    K.B(model, col, x0, y0, z0, x1, y1, z1, bev=bev, kind=kind, flat=bev <= 0)

def cut_rect(pieces, ax, line, a0, a1, y0, y1, tol=2.6):
    """cut a window (a0..a1 along the wall, y0..y1) out of every piece standing on that wall line"""
    out = []
    for (b, col, model, lv) in pieces:
        x0, py0, z0, x1, py1, z1 = b
        if ax == 'x': on, u0, u1 = (z1 - z0 <= tol and z0 >= line - 2.1 and z1 <= line + 2.1), x0, x1
        else: on, u0, u1 = (x1 - x0 <= tol and x0 >= line - 2.1 and x1 <= line + 2.1), z0, z1
        if not on or u1 <= a0 or u0 >= a1 or py1 <= y0 or py0 >= y1: out.append((b, col, model, lv)); continue
        parts = []
        if py0 < y0: parts.append((u0, py0, u1, y0))
        if py1 > y1: parts.append((u0, y1, u1, py1))
        my0, my1 = max(py0, y0), min(py1, y1)
        if u0 < a0: parts.append((u0, my0, a0, my1))
        if u1 > a1: parts.append((a1, my0, u1, my1))
        for (p0, q0, p1, q1) in parts:
            if p1 - p0 < 0.02 or q1 - q0 < 0.02: continue
            out.append(((p0, q0, z0, p1, q1, z1) if ax == 'x' else (x0, q0, p0, x1, q1, p1), col, model, lv))
    return out

# ---------------------------------------------------------------- the outside windows (look only: the hit wall
# stays whole). Every outside wall of a room people would want light in gets 6 x 6 windows at the zombie windows'
# height, 10 studs apart, clear of doors, the zombies' windows and the walls that meet it
WINDOWED = ('classroom', 'library', 'cafe', 'lab', 'art', 'office', 'principal', 'lounge', 'complab', 'music', 'nurse',
            'lobby', 'weights', 'restroom', 'lockerroom', 'hall', 'janitor', 'storage')
EXT_WIN = []      # (lv, axis, line, a0, a1, y0, y1, outward)
def ext_windows():
    busy = [(o['lv'], o['axis'], o['line'], o['a0'] - 5, o['a1'] + 5) for o in L.OPENINGS]
    for lv in ('G', 'U'):
        Ly = LV[lv]
        for (ax, line, s0, s1, out) in (('x', L.FZ0, L.FX0, L.FX1, -1), ('x', L.FZ1, L.FX0, L.FX1, 1),
                                        ('z', L.FX0, L.FZ0, L.FZ1, -1), ('z', L.FX1, L.FZ0, L.FZ1, 1)):
            c = s0 + 7.0
            while c < s1 - 6.0:
                probe = lambda u: L.room_at(lv, u, line - out * 1.5) if ax == 'x' else L.room_at(lv, line - out * 1.5, u)
                r, ra, rb = probe(c), probe(c - 4.5), probe(c + 4.5)
                ok = r is not None and r is ra and r is rb and r['look'] in WINDOWED
                if ok and any(b[0] == lv and b[1] == ax and abs(b[2] - line) < 0.1 and c + 3 > b[3] and c - 3 < b[4] for b in busy): ok = False
                if ok:
                    EXT_WIN.append((lv, ax, float(line), c - 3.0, c + 3.0, Ly + 3.0, Ly + 9.0, out)); c += 10.0
                else:
                    c += 2.0
        # the gym's high windows (clerestory), on its east wall, 8 wide
    for z in (-24.0, -8.0, 8.0, 24.0, 40.0):
        EXT_WIN.append(('U', 'z', float(L.FX1), z - 4.0, z + 4.0, 21.0, 29.0, 1))

def window_unit(model, ax, line, a0, a1, y0, y1, t0, t1, sill_out=None):
    """frame, mullion, glass and sills in an opening a0..a1 x y0..y1 through a wall t0..t1 thick (across the line)"""
    def B3(u0, v0, w0, u1, v1, w1, col, kind='plastic'):
        if ax == 'x': bx(model, col, (u0, v0, w0, u1, v1, w1), kind)
        else: bx(model, col, (w0, v0, u0, w1, v1, u1), kind)
    f = 0.35
    B3(a0, y0, t0 - 0.08, a0 + f, y1, t1 + 0.08, FRAME); B3(a1 - f, y0, t0 - 0.08, a1, y1, t1 + 0.08, FRAME)
    B3(a0 + f, y1 - f, t0 - 0.08, a1 - f, y1, t1 + 0.08, FRAME); B3(a0 + f, y0, t0 - 0.08, a1 - f, y0 + f, t1 + 0.08, FRAME)
    m = (a0 + a1) / 2
    B3(m - 0.15, y0 + f, (t0 + t1) / 2 - 0.15, m + 0.15, y1 - f, (t0 + t1) / 2 + 0.15, FRAME)
    B3(a0 + f, y0 + f, (t0 + t1) / 2 - 0.06, a1 - f, y1 - f, (t0 + t1) / 2 + 0.06, GLASS, 'glass')
    B3(a0 - 0.3, y0 - 0.25, t0 - 0.35, a1 + 0.3, y0, t1 + 0.35, COPING)      # the sills, in and out

def walls():
    pieces = []      # (box, colour, model, lv)
    for w in L.WALLS:
        lv, (x0, y0, z0, x1, y1, z1) = w['lv'], w['box']
        if w['mat'] == 'glass':          # the glass round the main stairs' hole upstairs: panes in a frame
            m = M_('sc_wall', lv)
            if x1 - x0 < z1 - z0:
                c = (x0 + x1) / 2
                bx(m, GLASS, (c - 0.15, y0 + 1.0, z0, c + 0.15, y1 - 0.4, z1), 'glass')
                bx(m, METAL, (c - 0.3, y0, z0, c + 0.3, y0 + 1.0, z1)); bx(m, METAL, (c - 0.3, y1 - 0.4, z0, c + 0.3, y1, z1))
                zz = z0
                while zz < z1 - 0.1: bx(m, METAL, (c - 0.25, y0, zz, c + 0.25, y1, min(z1, zz + 0.3))); zz += 4.0
                bx(m, DARK, (c - 0.35, y0 + 4.0, z0, c + 0.35, y0 + 4.3, z1))      # a handrail on it
            else:
                c = (z0 + z1) / 2
                bx(m, GLASS, (x0, y0 + 1.0, c - 0.15, x1, y1 - 0.4, c + 0.15), 'glass')
                bx(m, METAL, (x0, y0, c - 0.3, x1, y0 + 1.0, c + 0.3)); bx(m, METAL, (x0, y1 - 0.4, c - 0.3, x1, y1, c + 0.3))
                bx(m, DARK, (x0, y0 + 4.0, c - 0.35, x1, y0 + 4.3, c + 0.35))
            continue
        if not w['ext']:
            A, B_ = L.ROOMS[w['a']], L.ROOMS[w['b']]
            # each half in the finish of the room it faces, and no longer than that room (a run's ends reach half a
            # stud into the wall they meet; a courtyard's brick half would show its end in the hall)
            def clip(r, u0, u1, along_z):
                lo, hi = (r['r'][1], r['r'][3]) if along_z else (r['r'][0], r['r'][2])
                return max(u0, lo), min(u1, hi)     # (exactly: a half-stud overlap put two wall ends in one plane)
            c = w['line']
            if w['axis'] == 'z':
                a0, a1 = clip(A, z0, z1, True); b0, b1 = clip(B_, z0, z1, True)
                pieces.append(((x0, y0, a0, c, y1, a1), wallcol(A), M_('sc_wall', lv), lv))
                pieces.append(((c, y0, b0, x1, y1, b1), wallcol(B_), M_('sc_wall', lv), lv))
            else:
                a0, a1 = clip(A, x0, x1, False); b0, b1 = clip(B_, x0, x1, False)
                pieces.append(((a0, y0, z0, a1, y1, c), wallcol(A), M_('sc_wall', lv), lv))
                pieces.append(((b0, y0, c, b1, y1, z1), wallcol(B_), M_('sc_wall', lv), lv))
            continue
        # an outside wall (2 thick, outward from the footprint): a 0.5 skin in the room's finish, brick beyond
        thin_x = (x1 - x0) <= 2.5 and (z1 - z0) > 2.5
        thin_z = (z1 - z0) <= 2.5 and (x1 - x0) > 2.5
        lvq = lv     # (the wall's own level: a piece over a window starts above 24 and would ask the roof)
        if thin_x or thin_z:
            # the skin, room by room along the strip (one strip can run past several rooms); where no room is beside
            # it (a corner) the strip is brick right through
            a_lo, a_hi = (z0, z1) if thin_x else (x0, x1)
            def beside(u, side):
                if thin_x: return L.room_at(lvq, (x0 - 0.5) if side < 0 else (x1 + 0.5), u)
                return L.room_at(lvq, u, (z0 - 0.5) if side < 0 else (z1 + 0.5))
            n_lo = sum(1 for u in range(int(a_lo), int(a_hi)) if beside(u + 0.5, -1) is not None)
            n_hi = sum(1 for u in range(int(a_lo), int(a_hi)) if beside(u + 0.5, 1) is not None)
            side = -1 if n_lo > n_hi else 1
            segs, u = [], a_lo
            while u < a_hi - 1e-6:
                r = beside(u + 0.5, side)
                u1 = u + 1.0
                while u1 < a_hi - 1e-6 and beside(u1 + 0.5, side) is r: u1 += 1.0
                segs.append((u, min(u1, a_hi), r)); u = u1
            for (s0, s1, r) in segs:
                col = wallcol(r) if r is not None else T['brick']
                if thin_x:
                    sk = (x0, y0, s0, x0 + 0.5, y1, s1) if side < 0 else (x1 - 0.5, y0, s0, x1, y1, s1)
                else:
                    sk = (s0, y0, z0, s1, y1, z0 + 0.5) if side < 0 else (s0, y0, z1 - 0.5, s1, y1, z1)
                if r is None and lv == 'B': continue
                pieces.append((sk, col, M_('sc_wall', lv) if r is not None else 'sc_ext', lv))
            if thin_x: x0, x1 = (x0 + 0.5, x1) if side < 0 else (x0, x1 - 0.5)
            else: z0, z1 = (z0 + 0.5, z1) if side < 0 else (z0, z1 - 0.5)
        if lv == 'B': continue           # (the rest is buried)
        pieces.append(((x0, y0, z0, x1, y1, z1), T['brick'], 'sc_ext', lv))
    # the windows: the courtyard's glass and the outside windows, cut from the pieces, then their frames and glass
    for (lv, ax, line, a0, a1, y0, y1) in L.GLASS:
        pieces = cut_rect(pieces, ax, line, a0, a1, y0, y1)
        window_unit(M_('sc_win', lv), ax, line, a0, a1, y0, y1, line - 0.5, line + 0.5)
    for (lv, ax, line, a0, a1, y0, y1, out) in EXT_WIN:
        pieces = cut_rect(pieces, ax, line, a0, a1, y0, y1)
        t0, t1 = (line, line + 2.0) if out > 0 else (line - 2.0, line)
        window_unit(M_('sc_win', lv), ax, line, a0, a1, y0, y1, t0, t1)
    for (b, col, model, lv) in pieces:
        bx(model, col, b)
    # a wood wainscot and dado rail in the library and the offices
    for w in L.WALLS:
        if w['ext'] or w['mat'] == 'glass': continue
        lv = w['lv']
        for side, k in ((-1, w['a']), (1, w['b'])):
            r = L.ROOMS[k]
            if r['look'] not in PANELLED: continue
            x0, y0, z0, x1, y1, z1 = w['box']
            Ly = LV[lv]
            if y0 > Ly + 0.1 or y1 < Ly + 3.9: continue     # (only the pieces standing on the floor: a door's cut
                                                            #  leaves full-length strips under and over it)
            if w['axis'] == 'z':
                f = w['line'] + side * 0.5
                bx(M_('sc_trim', lv), WOODTRIM, (min(f, f + side * 0.12), Ly, z0, max(f, f + side * 0.12), Ly + 3.6, z1))
                bx(M_('sc_trim', lv), WOODTRIM, (min(f, f + side * 0.22), Ly + 3.6, z0, max(f, f + side * 0.22), Ly + 3.9, z1))
            else:
                f = w['line'] + side * 0.5
                bx(M_('sc_trim', lv), WOODTRIM, (x0, Ly, min(f, f + side * 0.12), x1, Ly + 3.6, max(f, f + side * 0.12)))
                bx(M_('sc_trim', lv), WOODTRIM, (x0, Ly + 3.6, min(f, f + side * 0.22), x1, Ly + 3.9, max(f, f + side * 0.22)))

def bulkhead_corners():
    """the stairwells' bulkheads on the roof: a post in the outer corner where the roof's low parapet meets them (both
    walls stop at their rooms, the corner above the parapet was open)"""
    for (x, z) in ((-100.0, 0.0), (140.0, -48.0)):
        sx = 1 if x < 0 else -1
        bx('sc_wall_R', T['block'], (min(x, x + sx * 0.5), 31.0, min(z, z + 0.5 * (1 if z == 0 else -1)), max(x, x + sx * 0.5), 47.0, max(z, z + 0.5 * (1 if z == 0 else -1))))

def copings():
    """a concrete cap on every wall that ends in the open: the roof's parapets, the gym's walls, the sheds"""
    for w in L.WALLS:
        x0, y0, z0, x1, y1, z1 = w['box']
        if w['lv'] != 'R' or w['mat'] == 'glass' or y1 > 46: continue
        thin_x = (x1 - x0) < (z1 - z0)
        if thin_x: bx('sc_roofdress', COPING, (x0 - 0.15, y1, z0, x1 + 0.15, y1 + 0.3, z1))
        else: bx('sc_roofdress', COPING, (x0, y1, z0 - 0.15, x1, y1 + 0.3, z1 + 0.15))

def openings_dress():
    """frames round every door and doorway, a sill and frame round every zombie window"""
    for o in L.OPENINGS:
        ax, line, a0, a1, y0, y1, kind = o['axis'], o['line'], o['a0'], o['a1'], o['y0'], o['y1'], o['kind']
        lv = lvl_of(y0 + 1.0)
        # the wall's thickness here: an outside wall runs outward 2 from the line
        r_lo = L.room_at(lv, line - 0.5, (a0 + a1) / 2) if ax == 'z' else L.room_at(lv, (a0 + a1) / 2, line - 0.5)
        r_hi = L.room_at(lv, line + 0.5, (a0 + a1) / 2) if ax == 'z' else L.room_at(lv, (a0 + a1) / 2, line + 0.5)
        if r_lo is not None and r_hi is not None: t0, t1 = line - 0.5, line + 0.5
        elif r_lo is None: t0, t1 = line - 2.0, line
        else: t0, t1 = line, line + 2.0
        model = M_('sc_frame', lv)
        def B3(u0, v0, w0, u1, v1, w1, col):
            if ax == 'x': bx(model, col, (u0, v0, w0, u1, v1, w1))
            else: bx(model, col, (w0, v0, u0, w1, v1, u1))
        col = METAL if kind in ('door', 'zwin') else WOODTRIM
        f = 0.4
        if kind == 'zwin' and o['y0'] > LV[lv] + 0.5 and lv != 'R':
            B3(a0 - f, y0, t0 - 0.1, a0, y1, t1 + 0.1, FRAME); B3(a1, y0, t0 - 0.1, a1 + f, y1, t1 + 0.1, FRAME)
            B3(a0 - f, y1, t0 - 0.1, a1 + f, y1 + f, t1 + 0.1, FRAME)
            B3(a0 - 0.4, y0 - 0.3, t0 - 0.4, a1 + 0.4, y0, t1 + 0.4, COPING)
            continue
        if kind == 'zwin': continue         # (the roof's gates and the basement grates: the cut is enough)
        B3(a0 - f, y0, t0 - 0.1, a0, y1, t1 + 0.1, col); B3(a1, y0, t0 - 0.1, a1 + f, y1, t1 + 0.1, col)
        B3(a0 - f, y1, t0 - 0.1, a1 + f, y1 + f, t1 + 0.1, col)

def floors_and_ceilings():
    for (x0, y0, z0, x1, y1, z1, fm, lv) in L.SLABS:
        if fm == 'grass':
            bx('sc_ground', GRASS, (x0, y0, z0, x1, y1, z1)); continue
        bx(M_('sc_floor', lv), T[FLOORTEX.get(fm, 'concrete')], (x0, y0, z0, x1, y1, z1))
    EXPOSED = ('tunnel', 'storage', 'workshop', 'boiler', 'janitor')
    for k, r in enumerate(L.ROOMS):
        lv = r['lv']
        if lv == 'R' or r['tower'] or r['look'] in ('court', 'gym', 'gymair', 'balcony', 'courtair'): continue
        x0, z0, x1, z1 = r['r']
        Ly = LV[lv]
        g = L.GRID[lv]
        def inset(side):
            # half a wall where a wall stands on that side (sampled at the side's middle), else flush
            if side == 'w': i, j = int(x0) - 1 - L.GX0, int((z0 + z1) / 2) - L.GZ0
            elif side == 'e': i, j = int(x1) - L.GX0, int((z0 + z1) / 2) - L.GZ0
            elif side == 'n': i, j = int((x0 + x1) / 2) - L.GX0, int(z0) - 1 - L.GZ0
            else: i, j = int((x0 + x1) / 2) - L.GX0, int(z1) - L.GZ0
            nb = g[i][j] if 0 <= i < L.NX and 0 <= j < L.NZ else -1
            if nb < 0: return 0.0
            return 0.5 if L.needs_wall(k, nb) else 0.0
        c = T['concrete'] if r['look'] in EXPOSED else T['ceiling']
        bx(M_('sc_ceil', lv), c, (x0 + inset('w'), Ly + 14.7, z0 + inset('n'), x1 - inset('e'), Ly + 15.0, z1 - inset('s')))
    # the light panels: a glowing white panel over every ceiling light; round high-bay lamps in the gym
    for (kind, p, d, b, rr, a, col) in K.LIGHTS:
        x, y, z = p
        lv = lvl_of(y - 10)
        if abs((y - LV.get(lv, 32.0)) - 14.0) < 0.01 and lv != 'R':
            Ly = LV[lv]
            bx(M_('sc_lamp', lv), METAL, (x - 2.3, Ly + 14.55, z - 2.3, x + 2.3, Ly + 14.7, z + 2.3))
            bx(M_('sc_lamp', lv), 'f6f4ee', (x - 2.0, Ly + 14.45, z - 2.0, x + 2.0, Ly + 14.55, z + 2.0), 'neon')
        elif 30 < y < 36:
            K.cyl('sc_lamp_G', METAL, x, 35.2, z, 1.6, 1.8, segs=16)
            K.cyl('sc_lamp_G', 'f6f4ee', x, 35.0, z, 1.3, 0.2, segs=16, kind='neon')

def stairs_dress():
    m = 'sc_stair'
    # the main stairs: 16 treads on the hit ramp's line (within half a stud of it), dark nosings, a rail on the open side
    for k in range(1, 17):
        za, zb = 22 - 2.0 * k, 22 - 2.0 * (k - 1)
        bx(m, STEPC, (54.0, 0.0, za, 64.0, k - 0.5, zb))
        bx(m, NOSE, (54.0, k - 0.62, zb - 0.35, 64.0, k - 0.44, zb + 0.06))
    for k in range(0, 9):
        z = 20.0 - 4.0 * k
        yt = (22 - z) / 2.0
        bx(m, METAL, (54.2, yt, z - 0.2, 54.6, yt + 3.6, z + 0.2))
    _rail(m, (54.4, 3.5, 22.0), (54.4, 19.5, -10.0))
    # the stairwells: each flight's treads on its ramp, the landings, the wall between the flights
    for (x0, x1, xm, zA, zB, f1, f2) in ((-120, -100, -110, (-10, 0), (-34, -26), (-120, -110), (-110, -100)),
                                        (140, 160, 150, (-58, -48), (-88, -74), (150, 160), (140, 150))):
        za_edge, zb_edge = zA[0], zB[1]
        for lv in ('B', 'G', 'U'):
            Ly = LV[lv]
            for k in range(1, 9):
                z_a, z_b = za_edge - 2.0 * (k - 1), za_edge - 2.0 * k
                bx(m, STEPC, (f1[0], Ly + k - 2.0, min(z_a, z_b), f1[1], Ly + k - 0.5, max(z_a, z_b)))
                bx(m, NOSE, (f1[0], Ly + k - 0.62, max(z_a, z_b) - 0.35, f1[1], Ly + k - 0.44, max(z_a, z_b) + 0.06))
                z_a, z_b = zb_edge + 2.0 * (k - 1), zb_edge + 2.0 * k
                bx(m, STEPC, (f2[0], Ly + 8 + k - 2.0, min(z_a, z_b), f2[1], Ly + 8 + k - 0.5, max(z_a, z_b)))
                bx(m, NOSE, (f2[0], Ly + 8 + k - 0.62, min(z_a, z_b) - 0.06, f2[1], Ly + 8 + k - 0.44, min(z_a, z_b) + 0.35))
    for (x0, y0, z0, x1, y1, z1, kind) in L.STEPS:
        if kind == 'landing': bx(m, T['concrete'], (x0, y0, z0, x1, y1, z1))
        elif kind == 'towerwall': bx(m, T['block'], (x0, y0, z0, x1, y1, z1))
        elif kind == 'fill': bx(m, STEPC, (x0, y0, z0, x1, y1, z1))
        elif kind == 'post': bx('sc_gymdress', METAL, (x0, y0, z0, x1, y1, z1), bev=0.15)
    # the bleachers: grey risers, a wooden seat board on each row, rails down both sides
    for k in range(1, 17):
        xa, xb = 108 - 2.0 * k, 108 - 2.0 * (k - 1)
        bx('sc_gymdress', '8d9196', (xa, 0.0, -4.0, xb, k - 0.5, 36.0))
        bx('sc_gymdress', 'c9a46e', (xb - 1.2, k - 0.56, -3.8, xb + 0.05, k - 0.3, 35.8), bev=0.08)
    for z in (-4.2, 36.2):
        for k in range(0, 9):
            x = 106.0 - 4.0 * k
            yt = (108 - x) / 2.0
            bx('sc_gymdress', METAL, (x - 0.2, yt, z - 0.2, x + 0.2, yt + 3.6, z + 0.2))
        _rail('sc_gymdress', (108.0, 3.5, z), (76.0, 19.5, z))

def _rail(model, a, b, t=0.35, col=None):
    """a straight square rail from a to b (a box turned to lie along it)"""
    from mathutils import Vector, Matrix
    A, B_ = Vector(a), Vector(b)
    d = B_ - A
    ln = d.length
    zax = d.normalized()
    up = Vector((0, 1, 0))
    xax = up.cross(zax).normalized() if abs(zax.dot(up)) < 0.99 else Vector((1, 0, 0))
    yax = zax.cross(xax).normalized()
    c = (A + B_) / 2
    Mx = Matrix(((xax.x, yax.x, zax.x, c.x), (xax.y, yax.y, zax.y, c.y), (xax.z, yax.z, zax.z, c.z), (0, 0, 0, 1)))
    K.B(model, col or DARK, -t / 2, -t / 2, -ln / 2, t / 2, t / 2, ln / 2, bev=0.08, M=Mx)

def fences():
    """the roof's chain-link (posts, rails, a see-through mesh), the balcony's and the stairwell holes' rails, the
    fire escapes' and roof gates' railings (the rest of a niche's cage is invisible: it only stops you)"""
    inside = lambda x, z: L.FX0 - 0.5 <= x <= L.FX1 + 0.5 and L.FZ0 - 0.5 <= z <= L.FZ1 + 0.5
    for (x0, y0, z0, x1, y1, z1) in L.FENCES:
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        if sy < 0.5: continue                                   # (a cage's lid)
        along_x = sx >= sz
        ln = sx if along_x else sz
        thin = min(sx, sz)
        if thin > 1.0: continue
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        if inside(cx, cz) and y0 >= 30.0 and sy > 4.0:          # the roof's fence: posts, rails, mesh
            m = 'sc_roofdress'
            n = max(1, int(round(ln / 6.0)))
            for i in range(n + 1):
                u = (x0 if along_x else z0) + ln * i / n
                b = (u - 0.2, y0, cz - 0.2, u + 0.2, y1, cz + 0.2) if along_x else (cx - 0.2, y0, u - 0.2, cx + 0.2, y1, u + 0.2)
                bx(m, POST, b)
            for yy in (y0 + 0.2, y1 - 0.2):
                bx(m, POST, (x0, yy - 0.12, cz - 0.1, x1, yy + 0.12, cz + 0.1) if along_x else (cx - 0.1, yy - 0.12, z0, cx + 0.1, yy + 0.12, z1))
            bx(m, MESH, (x0, y0 + 0.3, cz - 0.03, x1, y1 - 0.3, cz + 0.03) if along_x else (cx - 0.03, y0 + 0.3, z0, cx + 0.03, y1 - 0.3, z1), 'glass')
            continue
        # outside the building only the fire escapes' and the roof gates' railings show (the rest of a cage, and the
        # cage over a hedged bay, only stops you)
        if not inside(cx, cz) and not (abs(y0 - 16.0) < 0.1 or abs(y0 - 32.0) < 0.1): continue
        # a railing: posts every 4, a top rail at 3.5, a mid rail
        m = M_('sc_rail', lvl_of(y0 + 1.0))
        top = y0 + min(sy, 3.5)
        n = max(1, int(round(ln / 4.0)))
        for i in range(n + 1):
            u = (x0 if along_x else z0) + ln * i / n
            b = (u - 0.15, y0, cz - 0.15, u + 0.15, top, cz + 0.15) if along_x else (cx - 0.15, y0, u - 0.15, cx + 0.15, top, u + 0.15)
            bx(m, METAL, b)
        for yy in (top - 0.15, y0 + 1.6):
            bx(m, METAL if yy < top - 1 else DARK, (x0, yy - 0.12, cz - 0.12, x1, yy + 0.12, cz + 0.12) if along_x else (cx - 0.12, yy - 0.12, z0, cx + 0.12, yy + 0.12, z1))

def niches_dress():
    """the hedged bays under the ground-floor windows, the fire escapes' grated decks and ladders, the roof gates'
    decks, the basement's drain pits"""
    for b in L.SOLID:
        x0, y0, z0, x1, y1, z1, mat = b
        if mat == 'hedge':
            bx('sc_ground', HEDGE, (x0 - 0.3, y0, z0 - 0.3, x1 + 0.3, y1 - 0.6, z1 + 0.3), bev=0.25)
            n = max(1, int(round(max(x1 - x0, z1 - z0) / 3.0)))
            for i in range(n):
                t = (i + 0.5) / n
                cx, cz = (x0 + (x1 - x0) * t, (z0 + z1) / 2) if (x1 - x0) > (z1 - z0) else ((x0 + x1) / 2, z0 + (z1 - z0) * t)
                K.blob('sc_ground', HEDGE, cx, y1 - 0.8, cz, 1.6, sy=0.6, sub=1)
        elif mat == 'grating':
            bx('sc_rail_%s' % lvl_of(y1 + 1.0), '5a6066', (x0, y0, z0, x1, y1, z1))
            for k in range(int((x1 - x0) // 1.2)):
                xx = x0 + 0.6 + 1.2 * k
                bx('sc_rail_%s' % lvl_of(y1 + 1.0), '7a8088', (xx - 0.12, y1 - 0.02, z0 + 0.2, xx + 0.12, y1 + 0.06, z1 - 0.2))
    for (kind, x0, z0, x1, z1, y, (ox, oz)) in L.NICHES:
        if kind == 'window' and y > 1:       # a ladder down the fire escape's outer edge to the ground
            if ox: lx, lz = (x1 - 0.6 if ox > 0 else x0 + 0.6), (z0 + z1) / 2
            else: lx, lz = (x0 + x1) / 2, (z1 - 0.6 if oz > 0 else z0 + 0.6)
            for s in (-0.9, 0.9):
                if ox: bx('sc_rail_U', METAL, (lx - 0.1, 0.0, lz + s - 0.1, lx + 0.1, y, lz + s + 0.1))
                else: bx('sc_rail_U', METAL, (lx + s - 0.1, 0.0, lz - 0.1, lx + s + 0.1, y, lz + 0.1))
            for k in range(1, int(y // 1.5)):
                yy = k * 1.5
                if ox: bx('sc_rail_U', METAL, (lx - 0.08, yy, lz - 0.9, lx + 0.08, yy + 0.16, lz + 0.9))
                else: bx('sc_rail_U', METAL, (lx - 0.9, yy, lz - 0.08, lx + 0.9, yy + 0.16, lz + 0.08))
        if kind == 'grate':        # (seen through the grate: a concrete pit, as its hit boxes)
            bx('sc_wall_B', T['concrete'], (x0, y - 1.0, z0, x1, y, z1))
            bx('sc_wall_B', T['concrete'], (x0, y + 12.0, z0, x1, y + 13.0, z1))
            if ox:
                far = x1 if ox > 0 else x0
                for b in ((far - 0.3 if ox > 0 else far, y, z0, far if ox > 0 else far + 0.3, y + 12.0, z1),
                          (x0, y, z0 - 0.3, x1, y + 12.0, z0), (x0, y, z1, x1, y + 12.0, z1 + 0.3)):
                    bx('sc_wall_B', T['concrete'], b)
            else:
                far = z1 if oz > 0 else z0
                for b in ((x0, y, far - 0.3 if oz > 0 else far, x1, y + 12.0, far if oz > 0 else far + 0.3),
                          (x0 - 0.3, y, z0, x0, y + 12.0, z1), (x1, y, z0, x1 + 0.3, y + 12.0, z1)):
                    bx('sc_wall_B', T['concrete'], b)

def grounds():
    """the school's grounds: a walk round the building, the front drive and car park, lawns, trees, a fence, the
    field to the east, a canopy over the front doors, the courtyard's lamp posts"""
    m = 'sc_ground'
    X0, X1, Z0, Z1 = L.FX0, L.FX1, L.FZ0, L.FZ1
    # the walk (6 wide) round the building, just outside the bays
    for b in ((X0 - 18, -0.4, Z1 + 10, X1 + 18, 0.08, Z1 + 16), (X0 - 18, -0.4, Z0 - 16, X1 + 18, 0.08, Z0 - 10),
              (X0 - 18, -0.4, Z0 - 10, X0 - 12, 0.08, Z1 + 10), (X1 + 12, -0.4, Z0 - 10, X1 + 18, 0.08, Z1 + 10)):
        bx(m, WALK, b)
    # the front: a drive and the car park south of the walk
    bx(m, ASPHALT, (-150.0, -0.4, Z1 + 16, 200.0, 0.06, Z1 + 64))
    for k in range(-14, 19):
        x = 10.0 * k
        bx(m, 'b7b3aa', (x - 0.2, 0.06, Z1 + 40, x + 0.2, 0.1, Z1 + 60))     # (pale bay lines, low contrast)
    # the field east of the gym, a low track kerb round it
    bx(m, '5f7a49', (X1 + 30, -0.4, -120.0, 220.0, 0.04, 140.0))
    # trees round the grounds: chunky trunks and canopy blobs
    import random
    rnd = random.Random(4242)
    spots = [(x, Z0 - 40) for x in range(-160, 230, 34)] + [(X0 - 40, z) for z in range(-120, 150, 34)] + [(x, Z1 + 80) for x in range(-170, 230, 44)]
    for (x, z) in spots:
        x += rnd.uniform(-6, 6); z += rnd.uniform(-6, 6)
        h = rnd.uniform(14, 22)
        K.cyl(m, '6e5c4a', x, -0.2, z, 0.9, h * 0.55, segs=10)
        for j in range(3):
            K.blob(m, rnd.choice(('4f6a3e', '56724a', '4a6239')), x + rnd.uniform(-2.5, 2.5), h * 0.55 + 3 + j * 2.4, z + rnd.uniform(-2.5, 2.5), rnd.uniform(4.2, 6.0), sy=0.8, sub=2)
    # a chain-link fence round the grounds
    for (a, b_, c, d_) in ((L.YARD[0], L.YARD[1], L.YARD[2], L.YARD[1]), (L.YARD[0], L.YARD[3], L.YARD[2], L.YARD[3]),
                          (L.YARD[0], L.YARD[1], L.YARD[0], L.YARD[3]), (L.YARD[2], L.YARD[1], L.YARD[2], L.YARD[3])):
        if a == c:
            bx(m, POST, (a - 0.2, 0.0, b_, a + 0.2, 8.0, d_)) if False else None
            zz = b_
            while zz <= d_:
                bx(m, POST, (a - 0.2, 0.0, zz - 0.2, a + 0.2, 8.0, zz + 0.2)); zz += 10.0
            bx(m, MESH, (a - 0.03, 0.3, b_, a + 0.03, 7.8, d_), 'glass')
        else:
            xx = a
            while xx <= c:
                bx(m, POST, (xx - 0.2, 0.0, b_ - 0.2, xx + 0.2, 8.0, b_ + 0.2)); xx += 10.0
            bx(m, MESH, (a, 0.3, b_ - 0.03, c, 7.8, b_ + 0.03), 'glass')
    # the canopy over the front doors, on four columns clear of the bays
    bx(m, COPING, (-26.0, 14.0, Z1 + 2.0, 26.0, 15.0, Z1 + 14.0), bev=0.2)
    for x in (-24.0, 24.0):
        for z in (Z1 + 12.5,):
            K.cyl(m, 'd8d2c6', x, 0.0, z, 0.8, 14.0, segs=16)
    # a stone plinth along the foot of the outside walls and a cornice band at the roof line
    for (a, b_, c, d_) in ((X0 - 2.3, Z0 - 2.3, X1 + 2.3, Z0 - 2.0), (X0 - 2.3, Z1 + 2.0, X1 + 2.3, Z1 + 2.3),
                          (X0 - 2.3, Z0 - 2.0, X0 - 2.0, Z1 + 2.0), (X1 + 2.0, Z0 - 2.0, X1 + 2.3, Z1 + 2.0)):
        bx('sc_ext', PLINTH, (a, -0.2, b_, c, 2.0, d_))
        bx('sc_ext', COPING, (a, 30.4, b_, c, 31.4, d_))
        bx('sc_ext', COPING, (a, 14.6, b_, c, 15.2, d_))
    # the courtyard's lamp posts (their lights: lights())
    for (x, z) in ((-30, -24), (30, 24), (-30, 24), (30, -24)):
        K.cyl('sc_court', DARK, x, 0.0, z, 0.35, 10.0, segs=10)
        K.cyl('sc_court', 'f4e2c0', x, 10.0, z, 0.8, 1.6, segs=12, kind='neon')
        K.cyl('sc_court', DARK, x, 11.6, z, 1.0, 0.4, segs=12)

# ---------------------------------------------------------------- the UVs: world-scaled box projection per textured colour
TEXSIZE = {T[k]: ST.TEX[k] for k in ST.TEX}
FLOORUP = {T[k] for k in ('hallwall', 'classwall', 'rtile_wall', 'lockers', 'chalkboard')}
def add_uvs(objs):
    n = 0
    for ob in objs:
        hx = ob.name.rsplit('_', 1)[-1]
        if hx not in TEXSIZE: continue
        tu, tv = TEXSIZE[hx]
        model = ob.name.split('__')[0].rstrip('0123456789')
        # (only the pictures drawn floor-up, a wainscot or skirting, start at their floor; tiling ones run on unbroken)
        base = MODEL_BASE.get(model, 0.0) if hx in FLOORUP else 0.0
        me = ob.data
        uvl = me.uv_layers.new(name='UVMap')
        board = hx == T['chalkboard']
        for poly in me.polygons:
            nb = poly.normal
            rn = (nb.x, nb.z, -nb.y)                         # (Blender -> Roblox axes)
            ax = max(range(3), key=lambda i: abs(rn[i]))
            for li in poly.loop_indices:
                v = me.vertices[me.loops[li].vertex_index].co
                r = (v.x, v.z, -v.y)
                if board:      # (each board is 16 x 6 studs, its own picture: z -76..-60, 3.5 over its floor)
                    uv = ((r[2] + 76.0) / tu, (r[1] - base - 3.5) / tv)
                elif ax == 1: uv = (r[0] / tu, r[2] / tv)
                elif ax == 0: uv = (r[2] / tu, (r[1] - base) / tv)
                else: uv = (r[0] / tu, (r[1] - base) / tv)
                uvl.data[li].uv = uv
        n += 1
    print('UVS on %d meshes' % n)

_flush_plain = K.flush
def _flush_uv(*a, **k):
    objs = _flush_plain(*a, **k)
    add_uvs(objs)
    return objs
K.flush = _flush_uv

def render_school(folder, views, prefix, sky=(0.16, 0.13, 0.22), sun_rot=(60, 0, -130), sun_energy=1.2):
    """the kit's previews (arenakit's render_previews, plus): the layout's lights, the pictures on the textured meshes
    as Roblox will show them (--tex=<school_textures output folder>), denoised"""
    import bpy
    from mathutils import Vector
    os.makedirs(folder, exist_ok=True)
    sc = bpy.context.scene
    for (kind, p, d, b, r, a, col) in K.LIGHTS:
        ld = bpy.data.lights.new('l', 'POINT'); ld.energy = b * r * r * 2.2; ld.shadow_soft_size = 1.5
        ld.color = [int(col[j:j + 2], 16) / 255 for j in (0, 2, 4)]
        ob = bpy.data.objects.new('l', ld); sc.collection.objects.link(ob)
        ob.location = (K.P @ Vector((p[0], p[1], p[2], 1))).xyz
    texdir = [f.split('=', 1)[1] for f in K.FLAGS if f.startswith('--tex=')]
    if texdir:
        byhex = {T[k]: k for k in ST.TEX}
        imgs = {}
        for ob in bpy.data.objects:
            if ob.type != 'MESH': continue
            hx = ob.name.rsplit('_', 1)[-1]
            if hx not in byhex: continue
            nm = byhex[hx]
            if nm not in imgs: imgs[nm] = bpy.data.images.load(os.path.join(texdir[0], nm + '.png'))
            nt = ob.data.materials[0].node_tree
            tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = imgs[nm]
            nt.links.new(tn.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    cam_data = bpy.data.cameras.new('cam'); cam_data.clip_end = 8000
    cam = bpy.data.objects.new('cam', cam_data); sc.collection.objects.link(cam)
    sc.camera = cam
    sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = sun_energy; sun.angle = 0.15; sun.color = (0.85, 0.88, 1.0)
    so = bpy.data.objects.new('sun', sun); sc.collection.objects.link(so); so.rotation_euler = tuple(math.radians(a) for a in sun_rot)
    w = bpy.data.worlds.new('w'); w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (sky[0], sky[1], sky[2], 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
    sc.world = w
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 1100, 620
    sc.view_settings.view_transform = 'Standard'
    sc.render.image_settings.file_format = 'JPEG'
    probes = [f.split('=', 1)[1].split(',') for f in K.FLAGS if f.startswith('--probe=')]
    for (name, cp, tp, lens) in views:
        c = K.P @ Vector((cp[0], cp[1], cp[2], 1)); t = K.P @ Vector((tp[0], tp[1], tp[2], 1))
        cam.location = c.xyz
        cam.rotation_euler = (t.xyz - c.xyz).to_track_quat('-Z', 'Y').to_euler()
        cam_data.lens = lens
        for pr in probes:       # (--probe=<view>,<px>,<py>: what's under that pixel of that view)
            if pr[0] != name: continue
            bpy.context.view_layer.update()
            px, py = float(pr[1]), float(pr[2])
            W_, H_ = sc.render.resolution_x, sc.render.resolution_y
            fx = cam_data.sensor_width / cam_data.lens
            u, v = (px / W_ - 0.5) * fx, -(py / H_ - 0.5) * fx * H_ / W_
            d = (cam.matrix_world.to_3x3() @ Vector((u, v, -1.0))).normalized()
            hit, loc, nrm, idx, ob, mx = sc.ray_cast(bpy.context.evaluated_depsgraph_get(), cam.location, d)
            if hit:
                r = (loc.x, loc.z, -loc.y); rn = (nrm.x, nrm.z, -nrm.y)
                print('PROBE %s (%s,%s): %s at %.2f %.2f %.2f normal %.2f %.2f %.2f' % (name, pr[1], pr[2], ob.name, r[0], r[1], r[2], rn[0], rn[1], rn[2]))
            else:
                print('PROBE %s: nothing' % name)
        sc.render.filepath = os.path.join(folder, '%s_%s.jpg' % (prefix, name))
        bpy.ops.render.render(write_still=True)
        print('RENDERED', sc.render.filepath)

# local studs: (name, camera, look at, lens mm)
VIEWS = [
    ('aerial', (300, 220, 280), (20, 0, 0), 24),
    ('lobby', (10, 7, 90), (-6, 5, 40), 18),
    ('shall', (-36, 6, 41), (36, 5, 40), 18),
    ('court', (-34, 12, 28), (20, 5, -20), 18),
    ('gym', (150, 26, 24), (80, 6, 10), 18),
    ('class', (37, 6, -52), (8, 5, -70), 18),
    ('library', (-40, 22, 92), (-100, 18, 60), 18),
    ('lockers', (47, 6, 46), (47, 6, -40), 18),
    ('roof', (130, 44, -40), (-60, 34, -70), 20),
    ('tunnel', (-40, -10, -42), (60, -12, -42), 18),
    ('restroom', (-62, 6, -2), (-96, 4, -30), 18),
    ('front', (0, 10, 150), (0, 12, 90), 22),
    ('cafe', (-40, 7, 92), (-90, 4, 50), 18),
    ('zf1', (-26, 7, -8), (-40, 7, -8), 30),
    ('zf2', (-26, 7, 5), (-40, 7, 5), 30),
    ('office', (24, 22, 70), (-14, 18, 90), 18),
]

def check_walls():
    """(--check-walls) does the kit's wall cover every hit wall? at each level's mid height, every 0.25 stud of a hit
    wall's footprint (minus the openings and windows) should be under some wall piece of the kit"""
    got = []
    _B = K.B
    def grab(model, col, x0, y0, z0, x1, y1, z1, **kw):
        if kw.get('M') is None: got.append((min(x0, x1), min(y0, y1), min(z0, z1), max(x0, x1), max(y0, y1), max(z0, z1), model, col))
    K.B = grab
    walls(); bulkhead_corners()
    K.B = _B
    holes = []
    for (lv, ax, line, a0, a1, y0, y1) in L.GLASS: holes.append((lv, ax, line, a0, a1, y0, y1))
    for (lv, ax, line, a0, a1, y0, y1, out) in EXT_WIN: holes.append((lv, ax, line, a0, a1, y0, y1))
    bad = {}
    for w in L.WALLS:
        if w['mat'] == 'glass': continue
        x0, y0, z0, x1, y1, z1 = w['box']
        y = (y0 + y1) / 2
        n = 0
        xs = [x0 + 0.125 + 0.25 * i for i in range(int((x1 - x0) / 0.25))]
        zs = [z0 + 0.125 + 0.25 * i for i in range(int((z1 - z0) / 0.25))]
        for x in xs:
            for z in zs:
                if any(h[0] == w['lv'] and h[5] <= y <= h[6] and ((h[1] == 'x' and abs(z - h[2]) < 2.2 and h[3] <= x <= h[4]) or (h[1] == 'z' and abs(x - h[2]) < 2.2 and h[3] <= z <= h[4])) for h in holes): continue
                if w['lv'] == 'B' and w['ext']: continue
                if not any(g[0] <= x <= g[3] and g[2] <= z <= g[5] and g[1] <= y <= g[4] for g in got):
                    n += 1
                    key = (w['lv'], round(x), round(z))
                    if key not in bad: print('   GAP', w['lv'], (x, y, z), 'in hit wall', w['box'], w['mat'], 'ext' if w['ext'] else (L.ROOMS[w['a']]['id'], L.ROOMS[w['b']]['id']))
                    bad[key] = bad.get(key, 0) + 1
    print('WALL GAPS: %d spots' % len(bad))
    for k in sorted(bad)[:40]: print('   ', k, bad[k])

lights()
ext_windows()
write_layout()
if '--check-walls' in K.FLAGS:
    check_walls()
elif '--layout-only' in K.FLAGS:
    print('layout only: no kit')
else:
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)        # (no default cube in the kit)
    floors_and_ceilings(); walls(); bulkhead_corners(); copings(); openings_dress(); stairs_dress(); fences(); niches_dress(); grounds()
    if '--no-furniture' not in K.FLAGS:
        try:
            import school_props
            school_props.furniture(K, L)
        except Exception as e:
            print('NO FURNITURE YET', repr(e))
    _tri = {}
    for (mname, key), items in K.PIECES.items():
        _tri[mname] = _tri.get(mname, 0) + sum(sum(len(f.verts) - 2 for f in bm.faces) for bm, M in items)
    print('TRIS BY MODEL', sorted(_tri.items(), key=lambda kv: -kv[1]), 'total', sum(_tri.values()))
    _only = [f[8:].split(',') for f in K.FLAGS if f.startswith('--views=')]
    views = [v for v in VIEWS if v[0] in _only[0]] if _only else VIEWS
    if PREVIEW and '--no-preview' not in K.FLAGS:
        K.render_previews = render_school
    K.finish('school', OUT_DIR, PREVIEW, views, prefix='school', sky=(0.16, 0.13, 0.22), sun_rot=(60, 0, -130), sun_energy=1.2)
