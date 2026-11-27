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
# (20 Nov 2026, the owner: "can you do school v2? I like the layout is great jhust need to be rebuilt, try school v2A
#  and v2B couple different looks ... make it a little darker, maybe the ceiling lights flicker". --variant=v2A | v2B:
#  the same layout, its own arena (name, site, look, kit). v1 is the default and builds exactly as before)
VARIANT = ([f.split('=', 1)[1] for f in K.FLAGS if f.startswith('--variant=')] or ['v1'])[0]
V2 = VARIANT in ('v2A', 'v2B')
_VNAME = {'v1': 'JankfieldHigh', 'v2A': 'JankfieldHighV2A', 'v2B': 'JankfieldHighV2B'}[VARIANT]
LAYOUT = os.path.normpath(os.path.join(K.HERE, '..', '..', 'roblox', 'studio-tools', _VNAME + 'Layout.luau'))
INFO = dict(name=_VNAME, title={'v1': 'JANKFIELD HIGH', 'v2A': 'JANKFIELD HIGH (OLD)', 'v2B': 'JANKFIELD HIGH'}[VARIANT],   # (v2B: the owner's pick, 20 Nov)
            look={'v1': 'school', 'v2A': 'school_v2a', 'v2B': 'school_v2b'}[VARIANT], mapId='school',
            kit={'v1': 'school', 'v2A': 'school2a', 'v2B': 'school2b'}[VARIANT],
            origin=(0, 0, {'v1': -66000, 'v2A': -72000, 'v2B': -78000}[VARIANT]), killY=-60, centreX=0, maxTeam=0,
            about='a hand-made zombies map (tools/roblox/school_layout.py), built to roblox/docs/ZOMBIES.md'
                  + ('' if not V2 else '; look ' + VARIANT + ' (chunky rebuild, school_models.py --variant)'))

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
    'fill': ('Concrete', 'a39e93', 'stair'), 'parapet': ('Concrete', 'd8d0c0', 'plaster'), 'towerwall': ('Concrete', 'b9b5ab', 'block'), 'bleacher': ('WoodPlanks', 'b98d5c', 'bleacher'),
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
        K.light('point', x, 8.6, z, (0, -1, 0), 1.2, 30, 0, 'ffd9a8')
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
         '\tzm = {', '\t\tlabel = %s, start = %s,' % (q(Z['label'] + {'v1': '', 'v2A': ' (old)', 'v2B': ''}[VARIANT]), q(Z['start'])),
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
    if '--no-layout' in K.FLAGS:          # (card_render.py runs this builder: never append to the layout twice)
        print('layout not written (--no-layout)'); return
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
    if V2 and any(LIGHT_GROUPS):
        extra += ('\t-- the flickering lights: light index -> group (SchoolLife.client flickers each group, and the kit\'s sc_flk<group>)\n'
                  '\tlightGroups = { %s },\n' % ', '.join('[%d] = %d' % (i + 1, g) for i, g in enumerate(LIGHT_GROUPS) if g))
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

# ---------------------------------------------------------------- v2: each look's pictures, role by role
# role -> (colour key, picture). The v1 roles keep their names (the furniture and the shared code read them through
# L.TEXKEY); the new roles (stone, plaster, tile, felt, board, paint...) only the v2 kit uses. A picture is a name in
# school_textures.TEX (v1's) or TEX2 (v2's); its uploaded id comes from SURFACES (v1) or TEX2_IDS (v2)
TEX2_IDS = {       # (the v2 pictures, uploaded 20 Nov 2026 as Images, all approved)
    'a_terrazzo': 94976107123385, 'a_plaster': 93967757955287, 'a_tile': 95035963336200, 'a_brick': 128782282184054,
    'a_stone': 113102432800653, 'a_hextile': 100342179355756, 'b_polished': 92915607470710, 'b_board': 96774896908235,
    'b_felt': 91358210670842, 'b_vinyl': 84138425132700, 'b_porcelain': 91515197562193, 'b_whiteboard': 111184054506765,
    'b_ceiling': 110957618175256}
V2TEX = {
    'v2A': {
        'lino': ('cdbfa9', 'a_terrazzo'), 'terrazzo': ('cbbda6', 'a_terrazzo'), 'cafetile': ('b8ab96', 'cafetile'),
        'rtile_floor': ('dedad0', 'a_hextile'), 'rtile_wall': ('e2e3de', 'rtile_wall'), 'woodfloor': ('a07752', 'woodfloor'),
        'gymwood': ('c9a06a', 'gymwood'), 'carpet': ('7a8088', 'carpet'), 'ceiling': ('e2dbcd', 'a_plaster'),
        'concrete': ('97948d', 'concrete'), 'pavers': ('a49784', 'pavers'), 'rubber': ('343538', 'rubber'),
        'chalkboard': ('4a5a50', None), 'lockers': ('6e7c86', 'lockers'), 'brick': ('7f5446', 'a_brick'),
        'block': ('bdbab2', 'block'), 'hallwall': ('ddd5c4', 'a_plaster'), 'classwall': ('dcd4c3', 'a_plaster'),
        'stone': ('cfc6b4', 'a_stone'), 'plaster': ('ddd6c5', 'a_plaster'), 'tile': ('8e9a8a', 'a_tile'),
        'roofdeck': ('96938c', 'concrete'),
    },
    'v2B': {
        'lino': ('a7a8a6', 'b_polished'), 'terrazzo': ('a5a6a4', 'b_polished'), 'cafetile': ('cbc6be', 'b_porcelain'),
        'rtile_floor': ('cfcac2', 'b_porcelain'), 'rtile_wall': ('d2cec7', 'b_porcelain'), 'woodfloor': ('8e98a1', 'b_vinyl'),
        'gymwood': ('cca673', 'gymwood'), 'carpet': ('6f7680', 'carpet'), 'ceiling': ('c8c9c6', 'b_ceiling'),
        'concrete': ('959491', 'concrete'), 'pavers': ('a3a4a2', 'b_polished'), 'rubber': ('353638', 'rubber'),
        'chalkboard': ('bcc0bd', None), 'lockers': ('5e6670', 'lockers'), 'brick': ('b6b8b7', 'b_board'),
        'block': ('b3b5b4', 'b_board'), 'hallwall': ('b9bbba', 'b_board'), 'classwall': ('bbbdbc', 'b_board'),
        'board': ('b8bab9', 'b_board'), 'felt': ('8a8f78', 'b_felt'), 'roofdeck': ('939290', 'concrete'),
    },
}
if V2:
    _tk = V2TEX[VARIANT]
    L.TEXKEY = {k: v[0] for k, v in _tk.items()}
    L.ACCENT = '3f7f86' if VARIANT == 'v2A' else 'b07a3a'          # (one accent: muted teal / muted amber)
    _v1ids = dict(SURFACES)
    SURFACES = {}
    for _k, (_hx, _img) in _tk.items():
        if _img in _v1ids: SURFACES[_k] = _v1ids[_img]
        elif _img in TEX2_IDS: SURFACES[_k] = 'rbxassetid://%d' % TEX2_IDS[_img]

# ================================================================ THE KIT: the architecture (furniture: school_props.py)
import school_textures as ST
T = L.TEXKEY
PAINT, WOODTRIM, METAL, DARK, FRAME, GLASS = 'ddd4c2', '8f6f50', 'a7adb2', '4a4f55', '9aa1a6', 'b8d4dc'
GRASS, HEDGE, ASPHALT, WALK, COPING, PLINTH, POST, MESH = '5a7344', '4d6a3b', '3e4043', 'b5b0a6', 'a5a198', '8a857b', '6a7076', 'a9b1b6'
STEPC, NOSE = 'bdb8ad', '585d63'
if V2: NOSE = '737980'      # (round 2: the dark nosings read as black stripes)
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

_DUMP = [tuple(float(v) for v in f.split('=', 1)[1].split(',')) for f in K.FLAGS if f.startswith('--dump=')]
def bx(model, col, b, kind='plastic', bev=0.0):
    x0, y0, z0, x1, y1, z1 = b
    if x1 - x0 < 1e-3 or y1 - y0 < 1e-3 or z1 - z0 < 1e-3: return
    for d in _DUMP:     # (--dump=x0,y0,z0,x1,y1,z1: print every box touching that region, for z-fight hunts)
        if x0 <= d[3] and x1 >= d[0] and y0 <= d[4] and y1 >= d[1] and z0 <= d[5] and z1 >= d[2]:
            print('BOX', model, col, tuple(round(v, 3) for v in b))
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
            bx(M_('sc_lamp', lv), 'd8d3c6', (x - 2.0, Ly + 14.45, z - 2.0, x + 2.0, Ly + 14.55, z + 2.0), 'neon')
        elif 30 < y < 36:
            K.cyl('sc_lamp_G', METAL, x, 35.2, z, 1.6, 1.8, segs=16)
            K.cyl('sc_lamp_G', 'd8d3c6', x, 35.0, z, 1.1, 0.2, segs=16, kind='neon')

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
        elif kind == 'parapet': bx(m, PAINT, (x0, y0, z0, x1, y1, z1))
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
        if V2 and inside(cx, cz) and y0 >= 30.0 and sy > 4.0:   # (v2: a solid parapet 3 high, framed glass above it)
            m = 'sc_roofdress'
            def P3(u0, v0, w0, u1, v1, w1, col, kind='plastic'):
                if along_x: bx(m, col, (u0, v0, cz + w0, u1, v1, cz + w1), kind)
                else: bx(m, col, (cx + w0, v0, u0, cx + w1, v1, u1), kind)
            ua, ub = (x0, x1) if along_x else (z0, z1)
            P3(ua, y0, -0.45, ub, y0 + 3.0, 0.45, ST2['parapet'])
            P3(ua, y0 + 3.0, -0.6, ub, y0 + 3.5, 0.6, ST2['cap'])
            P3(ua, y0 + 3.5, -0.08, ub, y1 - 0.4, 0.08, GLASS, 'glass')
            P3(ua, y1 - 0.4, -0.3, ub, y1, 0.3, ST2['frame'])
            uu = ua + 3.0
            while uu < ub - 1.0: P3(uu - 0.3, y0 + 3.5, -0.3, uu + 0.3, y1 - 0.4, 0.3, ST2['frame']); uu += 6.0
            continue
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

# (27 Nov 2026, the owner: "can we make the shrubs better looking?": the hedges round the ground floor's window bays
#  read as flat green boxes with a row of flat blobs on top.) v2: each hedge sits in a low stone planter with dark soil,
#  and is a stack of big soft lumps (three rows, staggered, each lump its own size, lean and one of three muted greens;
#  each hedge its own set of greens). The hit box (the cover) is the layout's, unchanged. The lumps are their own model,
#  sc_hedgeA (the leaf-card version, tools/roblox/school_hedgeB.py, is sc_hedgeB: the owner picks; ZmGate.hedges switches)
# (lifted a notch after the first night look: the darkest read black under the school's lamps)
HEDGE_GREENS = (('55703f', '61794a', '718a57'), ('587345', '64804c', '748f5b'), ('5c763f', '688248', '7a945c'), ('52693f', '5e7549', '6e8758'))
_hrnd = None
def hedge_v2(x0, y0, z0, x1, y1, z1):
    import random
    global _hrnd
    if _hrnd is None: _hrnd = random.Random(271127)
    rnd = _hrnd
    along_x = (x1 - x0) >= (z1 - z0)
    a0, a1 = (x0, x1) if along_x else (z0, z1)
    c = (z0 + z1) / 2 if along_x else (x0 + x1) / 2
    def at(u, w):
        return (u, c + w) if along_x else (c + w, u)
    # the planter: a stone kerb 1.1 tall round the footprint, dark soil on it
    pa0, pa1 = a0 - 0.6, a1 + 0.6
    if along_x:
        bx('sc_ground', PLINTH, (pa0, y0, c - 1.0, pa1, y0 + 1.1, c + 1.0), bev=0.12)
        bx('sc_ground', '3f362c', (pa0 + 0.2, y0 + 1.1, c - 0.8, pa1 - 0.2, y0 + 1.16, c + 0.8))
    else:
        bx('sc_ground', PLINTH, (c - 1.0, y0, pa0, c + 1.0, y0 + 1.1, pa1), bev=0.12)
        bx('sc_ground', '3f362c', (c - 0.8, y0 + 1.1, pa0 + 0.2, c + 0.8, y0 + 1.16, pa1 - 0.2))
    greens = rnd.choice(HEDGE_GREENS)
    # the body: one soft mass (hedgekit: a metaball union of three staggered rows of ellipsoids, decimated), the
    # hedge's darkest green; then a few lighter rounded lumps pushing out of it, top and faces
    import hedgekit as HK
    elems, (ax_, _a0, _a1, _c) = HK.plan(x0, y0, z0, x1, y1, z1, rnd)
    K.put('sc_hedgeA', 'plastic', greens[0], HK.body(elems, ax_, tris=int(70 * (a1 - a0) + 250)), K.I4)  # (the body: the hedge's darkest)
    for (pt, nrm) in HK.surface_points(elems, ax_, max(3, int((a1 - a0) / 1.6)), rnd):
        rr = rnd.uniform(0.85, 1.35)
        K.sphere('sc_hedgeA', greens[rnd.choice((1, 2, 2))], pt[0] - nrm[0] * rr * 0.45, pt[1] - nrm[1] * rr * 0.45, pt[2] - nrm[2] * rr * 0.45, rr, segs=12, rings_=8)

def niches_dress():
    """the hedged bays under the ground-floor windows, the fire escapes' grated decks and ladders, the roof gates'
    decks, the basement's drain pits"""
    for b in L.SOLID:
        x0, y0, z0, x1, y1, z1, mat = b
        if mat == 'hedge' and V2:
            hedge_v2(x0, y0, z0, x1, y1, z1)
        elif mat == 'hedge':
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

# (27 Nov 2026, the owner: "Finish the fence it's just the gate!!") v2: the grounds' fence in the front gate's style
#  (studio-tools/ZmGate.luau: stone pillars, iron bars): a pillar every 10 studs, a low stone plinth between them and an
#  iron section on it (three rails, round bars). v2B leaves the gate's span open (the front, x 18..38: ZmFrontGate). The
#  boundary is the layout's hit boxes, unchanged
F_STONE, F_CAP, F_IRON = 'b0aaa0', '928d84', '282b30'
def railing_fence(m):
    X0_, Z0_, X1_, Z1_ = L.YARD
    gap = (18.0, 38.0) if VARIANT == 'v2B' else None
    pillars = set()
    for (along_x, line, a0, a1) in ((True, Z1_, X0_, X1_), (True, Z0_, X0_, X1_), (False, X0_, Z0_, Z1_), (False, X1_, Z0_, Z1_)):
        n = int(round((a1 - a0) / 10.0))
        posts = [a0 + (a1 - a0) * k / n for k in range(n + 1)]
        front = along_x and line == Z1_
        def box(u0, u1, y0, y1, w, col, bev=0.0):
            if along_x: bx(m, col, (u0, y0, line - w, u1, y1, line + w), bev=bev)
            else: bx(m, col, (line - w, y0, u0, line + w, y1, u1), bev=bev)
        for i in range(n):
            spans = [(posts[i] + 0.9, posts[i + 1] - 0.9)]
            if gap and front:
                spans = [(max(s0, x), min(s1, y)) for (s0, s1) in spans for (x, y) in ((-1e9, gap[0]), (gap[1], 1e9)) if min(s1, y) - max(s0, x) > 0.5]
            for (s0, s1) in spans:
                box(s0, s1, 0.0, 1.0, 0.6, F_STONE, bev=0.08)          # the plinth
                for y in (1.6, 4.7, 7.8):
                    box(s0, s1, y - 0.16, y + 0.16, 0.16, F_IRON)        # the rails
                k = 0
                while s0 + 0.5 + k * 0.95 < s1 - 0.3:
                    u = s0 + 0.5 + k * 0.95
                    if along_x: K.cyl(m, F_IRON, u, 1.0, line, 0.13, 7.4, segs=6, bev=0.0)
                    else: K.cyl(m, F_IRON, line, 1.0, u, 0.13, 7.4, segs=6, bev=0.0)
                    k += 1
        for u in posts:
            if gap and front and gap[0] - 1.0 < u < gap[1] + 1.0: continue
            key = (round(u, 2), round(line, 2), along_x)
            pt = (u, line) if along_x else (line, u)
            if (round(pt[0], 2), round(pt[1], 2)) in pillars: continue
            pillars.add((round(pt[0], 2), round(pt[1], 2)))
            bx(m, F_STONE, (pt[0] - 0.9, 0.0, pt[1] - 0.9, pt[0] + 0.9, 9.0, pt[1] + 0.9), bev=0.12)
            bx(m, F_CAP, (pt[0] - 1.15, 9.0, pt[1] - 1.15, pt[0] + 1.15, 9.6, pt[1] + 1.15), bev=0.12)

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
    if V2:
        railing_fence(m)
    # a chain-link fence round the grounds (v1)
    for (a, b_, c, d_) in (() if V2 else ((L.YARD[0], L.YARD[1], L.YARD[2], L.YARD[1]), (L.YARD[0], L.YARD[3], L.YARD[2], L.YARD[3]),
                          (L.YARD[0], L.YARD[1], L.YARD[0], L.YARD[3]), (L.YARD[2], L.YARD[1], L.YARD[2], L.YARD[3]))):
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
        if V2: continue          # (v2: v2_facade)
        bx('sc_ext', PLINTH, (a, -0.2, b_, c, 2.0, d_))
        bx('sc_ext', COPING, (a, 30.4, b_, c, 31.4, d_))
        bx('sc_ext', COPING, (a, 14.6, b_, c, 15.2, d_))
    # the courtyard's lamp posts (their lights: lights())
    # (20 Nov, main: the first lantern was a 1.6-tall neon cylinder, blown out white on camera. Now a small lantern: a
    #  frosted shade you see the light through, a dim warm core, a cap; the point light under it lights the yard)
    for (x, z) in ((-30, -24), (30, 24), (-30, 24), (30, -24)):
        K.cyl('sc_court', DARK, x, 0.0, z, 0.3, 9.0, segs=10)
        K.cyl('sc_court', DARK, x, 8.9, z, 0.42, 0.15, segs=12)
        K.cyl('sc_court', 'e9dfc8', x, 9.05, z, 0.38, 0.7, segs=12, r2=0.3, kind='glass')
        K.cyl('sc_court', '8a7350', x, 9.15, z, 0.14, 0.45, segs=8, kind='neon')
        K.cyl('sc_court', DARK, x, 9.75, z, 0.55, 0.2, segs=12, r2=0.2)

# ================================================================ v2 (20 Nov 2026): CHUNKY first, a subtle texture on top
# The owner, about the hubs that day: "by old design I meant lke the chunker structes you know? we just add subtle
# texture to them now"; about the school: "make it a little darker, maybe the ceiling lights flicker". The layout and
# every hit box stay; only the look changes. The rule that keeps the hit boxes honest: a pier's face IS the hit wall's
# face and the wall between piers is RECESSED behind it, so nothing a player walks past stands proud of the hit box (but
# a skirting on a pier, 0.25, a cornice over head height, and the frames round an opening's edges).
CEIL = L.CEIL
def LVY(lv): return 32.0 if lv == 'R' else LV[lv]
STYLE = {
    'v2A': dict(S=12.0, PW=2.4, REC=0.35, frame='5a4434', frameW=1.3, winframe='d9d2c2', sill=None, skirt='4f3b2d',
                rail='5a4434', cornice=True, fixture='globe', light='ffcf9a', lightB=1.0, lightR=17.5, core='8c7354',
                shade='e9dfcc', beam=None, bracket='5a4434', parapet=None, cap='5a4434', exitc='2f6a46', transom=False),
    'v2B': dict(S=8.0, PW=1.4, REC=0.35, frame='4c5258', frameW=1.4, winframe='4c5258', sill=None, skirt=None,
                rail=None, cornice=False, fixture='trough', light='e2eaff', lightB=0.95, lightR=17.5, core='7f8a96',
                shade='dfe5e8', beam=None, bracket=None, parapet=None, cap='4c5258', exitc='2f6a46', transom=False),
}
ST2 = STYLE.get(VARIANT, STYLE['v2A'])
if V2:
    _A = VARIANT == 'v2A'
    ST2['sill'] = T['stone'] if _A else T['board']
    ST2['beam'] = T['plaster'] if _A else T['ceiling']
    ST2['parapet'] = T['plaster'] if _A else T['board']

HALLS = ('hall', 'lobby', 'landing', 'stairhole', 'cafe')
CLASSY = ('classroom', 'lab', 'art', 'music', 'complab', 'nurse')
SERVICE = ('storage', 'janitor', 'workshop', 'tunnel', 'boiler', 'tower')
GYMS = ('gym', 'balcony', 'gymair', 'weights')
def _fin(pier, zones, S=None, PW=None, rail=None, skirt=None, plinth=None, cornice=False, rec=None):
    d = dict(pier=pier, zones=zones, rail=rail, skirt=skirt, plinth=plinth, cornice=cornice and ST2['cornice'],
             S=S or ST2['S'], PW=PW or ST2['PW'], lo=zones[0][1], hi=zones[-1][1], proud=0.25)
    if rec is not None: d['rec'] = rec; d['proud'] = 0.0      # (outside: flush piers, a deeper recess)
    return d

def finish(r):
    """the wall finish of the room a wall half faces: the piers' colour, the panels' zones [(height over the floor,
    colour)], a rail (height, colour), a skirting (proud on the piers, flush in the panels) or a flush plinth, a cornice;
    None: a flat wall in one colour (the restrooms: tile from floor to ceiling)"""
    lk = 'exterior' if r is None else r['look']
    A = VARIANT == 'v2A'
    if lk in ('restroom', 'lockerroom'):      # (tile between piers: the restrooms were the last flat walls)
        if A: return _fin(T['plaster'], [(0, T['rtile_wall'])], cornice=True)
        return _fin(T['board'], [(0, T['rtile_wall'])])
    if lk in HALLS and r is not None and r['id'] == 'lockers':
        return _fin(T['stone'] if A else T['board'], [(0, T['lockers']), (7.0, T['plaster'] if A else T['felt'])],
                    rail=(7.0, ST2['rail']) if A else None, skirt=ST2['skirt'] if A else None, plinth=None if A else (0.6, T['board']), cornice=True)
    if lk in HALLS:
        if A: return _fin(T['stone'], [(0, T['tile']), (4.5, T['plaster'])], rail=(4.5, ST2['rail']), skirt=ST2['skirt'], cornice=True)
        return _fin(T['board'], [(0, T['board']), (1.0, T['felt']), (9.5, T['board'])], plinth=(1.0, T['board']))
    if lk in CLASSY:
        if A: return _fin(T['plaster'], [(0, 'b9ae99'), (4.0, T['plaster'])], rail=(4.0, ST2['rail']), skirt=ST2['skirt'], cornice=True)
        return _fin(T['board'], [(0, 'aeb0ac'), (3.6, T['felt']), (10.5, 'bec0bc')], plinth=(0.8, T['board']))   # (round 2: a felt pinboard band)
    if lk in PANELLED:
        if A: return _fin('8f6b4c', [(0, '94714f'), (4.5, T['plaster'])], rail=(4.5, ST2['rail']), skirt=ST2['skirt'], cornice=True)
        return _fin('a68b66', [(0, T['felt'])], plinth=(0.8, T['board']))
    if lk in SERVICE or lk in GYMS:
        big = lk in GYMS
        zones = [(0, T['felt'])] if (not A and lk in ('gymair', 'balcony')) else [(0, T['block'])]    # (v2B: felt up top in the gym)
        return _fin(T['brick'] if A else T['board'], zones, S=16.0 if big else None, PW=3.0 if big else None,
                    skirt='5e5e5b' if A else None)
    if lk in ('court', 'courtair'):
        f_ = _fin(T['stone'] if A else T['board'], [(0, T['brick'])], skirt=T['stone'] if A else None,
                  plinth=None if A else (1.0, T['board']))
        f_['proud'] = 1.0            # (round 2: "turn the white strips into piers that stand out")
        return f_
    if lk == 'exterior':
        return _fin(T['stone'] if A else T['board'], [(0, T['brick'])], rec=0.5)
    return None           # (the roof's parapets: plain)

def vprism(model, col, pts, y0, y1, kind='plastic'):
    """a flat outline [(x, z), ...] (convex) stood up from y0 to y1, flat shaded, no bevel"""
    import bmesh
    bm = bmesh.new()
    lo = [bm.verts.new((x, y0, z)) for (x, z) in pts]
    hi = [bm.verts.new((x, y1, z)) for (x, z) in pts]
    bm.faces.new(lo); bm.faces.new(hi[::-1])
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for e in bm.edges: e.smooth = False
    K.put(model, kind, col, bm)

def articulate(model, b, ax, sign, fin, Ly, top):
    """one wall piece whose room-side face is b's +sign side across `ax` ('x': the face looks along x, the wall runs
    along z): piers on the S grid (world positions, so they line up from piece to piece and level to level) stay full,
    their face is the hit face; the panels between them step back REC"""
    x0, y0, z0, x1, y1, z1 = b
    rec = fin.get('rec', ST2['REC'])
    if ax == 'x': u0, u1, t0, t1 = z0, z1, x0, x1
    else: u0, u1, t0, t1 = x0, x1, z0, z1
    if abs(t1 - t0) < rec + 0.15: rec = max(0.0, abs(t1 - t0) - 0.15)
    tf = t1 if sign > 0 else t0                        # the face
    tb = t0 if sign > 0 else t1                        # the back
    tr = tf - sign * rec                               # the recessed face
    def B3(ua, ya, ta, ub, yb, tb_, col, bev=0.0):
        if ub - ua < 0.02 or yb - ya < 0.02: return
        lo_t, hi_t = min(ta, tb_), max(ta, tb_)
        if hi_t - lo_t < 0.02: return
        if ax == 'x': bx(model, col, (lo_t, ya, ua, hi_t, yb, ub), bev=bev)
        else: bx(model, col, (ua, ya, lo_t, ub, yb, hi_t), bev=bev)
    ya, yb = max(y0, Ly), min(y1, top)
    if y0 < ya: B3(u0, y0, tb, u1, min(y1, ya), tf, fin['lo'])                 # (in the slab)
    if y1 > yb and yb >= y0: B3(u0, max(yb, y0), tb, u1, y1, tf, fin['hi'])   # (over the ceiling)
    if yb <= ya: return
    S, PW = fin['S'], fin['PW']
    piers = []
    if u1 - u0 < 3.0: piers = [(u0, u1)]                                       # (a short piece is all pier)
    else:
        k0, k1 = int(math.floor((u0 - PW) / S)), int(math.ceil((u1 + PW) / S))
        for k in range(k0, k1 + 1):
            a, c = max(u0, k * S - PW / 2), min(u1, k * S + PW / 2)
            if c - a > 0.05: piers.append((a, c))
        merged = []
        for (a, c) in piers:
            if merged and a - merged[-1][1] < 0.6: merged[-1] = (merged[-1][0], c)
            else: merged.append((a, c))
        piers = merged
        if piers and piers[0][0] - u0 < 0.6: piers[0] = (u0, piers[0][1])
        if piers and u1 - piers[-1][1] < 0.6: piers[-1] = (piers[-1][0], u1)
    panels, u = [], u0
    for (a, c) in piers:
        if a - u > 0.05: panels.append((u, a))
        u = c
    if u1 - u > 0.05: panels.append((u, u1))
    floor = ya <= Ly + 0.01
    pr = fin.get('proud', 0.0)               # (round 2: the piers stand proud of the hit face too, for a deeper relief)
    for (a, c) in piers:
        if c - a > 1.0 and yb - ya > 2.0:      # (round 4: the piers' two front edges chamfered, as the principles ask)
            tF = tf + sign * pr                 # (a six-sided prism, no extra bevel: K.chamfer took v2B's kit past 20 MB)
            ch = min(0.35, (c - a) * 0.2)
            tu = [(tb, a), (tF - sign * ch, a), (tF, a + ch), (tF, c - ch), (tF - sign * ch, c), (tb, c)]
            vprism(model, fin['pier'], [(t_, u_) if ax == 'x' else (u_, t_) for (t_, u_) in tu], ya, yb)
        else:
            B3(a, ya, tb, c, yb, tf + sign * pr, fin['pier'])
        if fin['skirt'] and floor: B3(a, Ly, tf + sign * pr, c, min(Ly + 1.0, yb), tf + sign * (pr + 0.25), fin['skirt'])
    zs = fin['zones']
    for (a, c) in panels:
        for i, (h, col) in enumerate(zs):
            za = ya if i == 0 else max(ya, Ly + h)
            zb = yb if i == len(zs) - 1 else min(yb, Ly + zs[i + 1][0])
            if zb > za: B3(a, za, tb, c, zb, tr, col)
        if floor and fin['skirt']: B3(a, Ly, tr, c, min(Ly + 1.0, yb), tf, fin['skirt'])
        elif floor and fin['plinth']: B3(a, Ly, tr, c, min(Ly + fin['plinth'][0], yb), tf, fin['plinth'][1])
        if fin['rail']:
            h = Ly + fin['rail'][0]
            if ya <= h - 0.3 and yb >= h + 0.3: B3(a, h - 0.3, tr, c, h + 0.3, tf, fin['rail'][1])
    if fin['cornice'] and ya <= Ly + 13.6 and yb >= Ly + 14.7:
        B3(u0, Ly + 13.6, tf, u1, Ly + 14.0, tf + sign * (pr + 0.2), ST2['beam'])
        B3(u0, Ly + 14.0, tf, u1, Ly + 14.7, tf + sign * (pr + 0.5), ST2['beam'])

def cut_rect2(pieces, ax, line, a0, a1, y0, y1, tol=2.6):
    """cut_rect for v2 pieces (box, colour, model, lv, meta): the meta rides along"""
    plain = [(p[0], p[1], p[2], (p[3], p[4])) for p in pieces]
    out = cut_rect(plain, ax, line, a0, a1, y0, y1, tol)
    return [(b, col, model, lvm[0], lvm[1]) for (b, col, model, lvm) in out]

def window_unit2(model, ax, line, a0, a1, y0, y1, t0, t1, mull=None):
    """a chunky window: a 0.6 frame through the wall's depth, mullions, a transom bar at two thirds, the glass in the
    middle, deep sills in and out"""
    def B3(u0, v0, w0, u1, v1, w1, col, kind='plastic'):
        if ax == 'x': bx(model, col, (u0, v0, w0, u1, v1, w1), kind)
        else: bx(model, col, (w0, v0, u0, w1, v1, u1), kind)
    f, fc = 0.6, ST2['winframe']
    t0, t1 = t0 + 0.25, t1 - 0.25          # (round 3: the frame sits inside the opening, a reveal round it)
    B3(a0, y0, t0, a0 + f, y1, t1, fc); B3(a1 - f, y0, t0, a1, y1, t1, fc)
    B3(a0 + f, y1 - f, t0, a1 - f, y1, t1, fc); B3(a0 + f, y0, t0, a1 - f, y0 + f, t1, fc)
    tm = (t0 + t1) / 2
    n = mull if mull is not None else (2 if a1 - a0 > 9 else 1)
    for i in range(1, n + 1):
        m = a0 + (a1 - a0) * i / (n + 1)
        B3(m - 0.32, y0 + f, tm - 0.25, m + 0.32, y1 - f, tm + 0.25, fc)
    ytr = y0 + (y1 - y0) * 0.66
    B3(a0 + f, ytr - 0.25, tm - 0.2, a1 - f, ytr + 0.25, tm + 0.2, fc)
    B3(a0 + f, y0 + f, tm - 0.07, a1 - f, y1 - f, tm + 0.07, GLASS, 'glass')
    B3(a0 - 0.4, y0 - 0.5, t0 - 0.8, a1 + 0.4, y0, t1 + 0.8, ST2['sill'])

# the stair hole through the upper floor: no ceiling, beams or fittings under it on the floor below
HOLES = {}
for _r in L.ROOMS:
    if _r['look'] == 'stairhole':
        HOLES.setdefault({'U': 'G', 'G': 'B'}[_r['lv']], []).append(_r['r'])
def minus(rect, holes):
    """a rectangle (x0, z0, x1, z1) less the holes: up to four rectangles round each"""
    out = [rect]
    for (hx0, hz0, hx1, hz1) in holes:
        nxt = []
        for (x0, z0, x1, z1) in out:
            if hx1 <= x0 or hx0 >= x1 or hz1 <= z0 or hz0 >= z1: nxt.append((x0, z0, x1, z1)); continue
            if hz0 > z0: nxt.append((x0, z0, x1, hz0))
            if hz1 < z1: nxt.append((x0, hz1, x1, z1))
            if hx0 > x0: nxt.append((x0, max(z0, hz0), hx0, min(z1, hz1)))
            if hx1 < x1: nxt.append((hx1, max(z0, hz0), x1, min(z1, hz1)))
        out = nxt
    return [r for r in out if r[2] - r[0] > 0.05 and r[3] - r[1] > 0.05]
def in_hole(lv, x, z, pad=1.5):
    return any(hx0 - pad < x < hx1 + pad and hz0 - pad < z < hz1 + pad for (hx0, hz0, hx1, hz1) in HOLES.get(lv, []))

def v2_slabs():
    """the floors, room by room (v1's slabs are merged by the layout's floor material; v2 gives the classrooms their own
    floor): the raster's cells grouped by the room's floor role, then the gym's lid"""
    role_of = {'lino': 'lino', 'tile': 'cafetile', 'terrazzo': 'terrazzo', 'restroomtile': 'rtile_floor', 'concrete': 'concrete',
               'pavers': 'pavers', 'gymwood': 'gymwood', 'rubber': 'rubber', 'carpet': 'carpet', 'wood': 'woodfloor',
               'roofdeck': 'roofdeck', 'stair': 'concrete'}
    for lv in L.ORDER:
        Ly = LVY(lv)
        g = L.GRID[lv]
        groups = {}
        for i in range(L.NX):
            for j in range(L.NZ):
                k = g[i][j]
                if k < 0 or not L.ROOMS[k]['floor']: continue
                r = L.ROOMS[k]
                role = 'woodfloor' if r['look'] in CLASSY and r['fmat'] in ('lino', 'tile') else role_of.get(r['fmat'], 'concrete')
                groups.setdefault(role, set()).add((i, j))
        for role, cells in groups.items():
            for (i0, j0, i1, j1) in L._greedy(cells):
                # (round 3: two pieces of one floor that only touched showed a bright hairline; they overlap 0.05 now)
                ex = 0.05 if (i1, j0) in cells else 0.0
                ez = 0.05 if (i0, j1) in cells else 0.0
                bx(M_('sc_floor', lv), T[role], (L.GX0 + i0, Ly - 1.0, L.GZ0 + j0, L.GX0 + i1 + ex, Ly, L.GZ0 + j1 + ez))
    for (x0, y0, z0, x1, y1, z1, fm, lv) in L.SLABS:
        if fm == 'rooflid': bx(M_('sc_floor', lv), T['concrete'], (x0, y0, z0, x1, y1, z1))

def transoms():
    """(v2A) a glazed light over every doorway between two rooms: (lv, axis, line, a0, a1, y0, y1)"""
    out = []
    if not ST2['transom']: return out
    for o in L.OPENINGS:
        if o['kind'] != 'doorway': continue
        lv = lvl_of(o['y0'] + 1.0)
        if lv in ('B', 'R'): continue
        ax, line, c = o['axis'], o['line'], (o['a0'] + o['a1']) / 2
        r_lo = L.room_at(lv, line - 0.5, c) if ax == 'z' else L.room_at(lv, c, line - 0.5)
        r_hi = L.room_at(lv, line + 0.5, c) if ax == 'z' else L.room_at(lv, c, line + 0.5)
        if r_lo is None or r_hi is None: continue
        y0 = o['y1'] + 0.9
        if y0 + 1.6 > LVY(lv) + 13.2: continue
        out.append((lv, ax, line, o['a0'], o['a1'], y0, y0 + 1.6))
    return out
TRANSOMS = []

def v2_walls():
    """v1's walls (each half in its room's finish, the outside skins room by room, the windows cut), but every piece
    keeps which way it faces and which finish it gets, and is then articulated"""
    pieces = []      # (box, colour, model, lv, meta)  meta: (ax, sign, fin, Ly, top) or None (plain)
    for w in L.WALLS:
        lv, (x0, y0, z0, x1, y1, z1) = w['lv'], w['box']
        Ly = LVY(lv)
        if w['mat'] == 'glass':
            # the glass round the stair hole upstairs: a solid upstand 3.6 over the floor, a cap, glass over it in frames
            m = M_('sc_wall', lv)
            thin_x = x1 - x0 < z1 - z0
            c = (x0 + x1) / 2 if thin_x else (z0 + z1) / 2
            up = Ly + 3.6
            def G3(a0_, ya_, ta, a1_, yb_, tb_, col, kind='plastic', bev=0.0):
                if thin_x: bx(m, col, (c + ta, ya_, a0_, c + tb_, yb_, a1_), kind, bev=bev)
                else: bx(m, col, (a0_, ya_, c + ta, a1_, yb_, c + tb_), kind, bev=bev)
            a_lo, a_hi = (z0, z1) if thin_x else (x0, x1)
            G3(a_lo, y0, -0.45, a_hi, up, 0.45, ST2['parapet'])
            G3(a_lo, up, -0.6, a_hi, up + 0.5, 0.6, ST2['cap'], bev=0.12)
            G3(a_lo, up + 0.5, -0.1, a_hi, y1 - 0.6, 0.1, GLASS, 'glass')
            G3(a_lo, y1 - 0.6, -0.35, a_hi, y1, 0.35, ST2['frame'])
            uu = a_lo
            while uu < a_hi - 0.1:
                G3(uu, up + 0.5, -0.3, min(a_hi, uu + 0.6), y1 - 0.6, 0.3, ST2['frame']); uu += 6.0
            continue
        if not w['ext']:
            A_, B_ = L.ROOMS[w['a']], L.ROOMS[w['b']]
            def clip(r, u0, u1, along_z):
                lo, hi = (r['r'][1], r['r'][3]) if along_z else (r['r'][0], r['r'][2])
                return max(u0, lo), min(u1, hi)
            c = w['line']
            top = Ly + CEIL if lv != 'R' else y1
            for (r, sgn) in ((A_, -1), (B_, 1)):
                fin = finish(r) if lv != 'R' else None
                col = wallcol(r) if fin is None else fin['hi']
                if w['axis'] == 'z':
                    a0, a1 = clip(r, z0, z1, True)
                    b = (x0, y0, a0, c, y1, a1) if sgn < 0 else (c, y0, a0, x1, y1, a1)
                    meta = ('x', sgn, fin, Ly, top) if fin else None
                else:
                    a0, a1 = clip(r, x0, x1, False)
                    b = (a0, y0, z0, a1, y1, c) if sgn < 0 else (a0, y0, c, a1, y1, z1)
                    meta = ('z', sgn, fin, Ly, top) if fin else None
                pieces.append((b, col, M_('sc_wall', lv), lv, meta))
            continue
        # an outside wall: the 0.5 skin facing the room, room by room (as v1), then the brick beyond, its outer face
        # articulated too (stone or concrete pilasters, recessed brick or board between)
        thin_x = (x1 - x0) <= 2.5 and (z1 - z0) > 2.5
        thin_z = (z1 - z0) <= 2.5 and (x1 - x0) > 2.5
        lvq = lv
        side = None
        if thin_x or thin_z:
            a_lo, a_hi = (z0, z1) if thin_x else (x0, x1)
            def beside(u, sd):
                if thin_x: return L.room_at(lvq, (x0 - 0.5) if sd < 0 else (x1 + 0.5), u)
                return L.room_at(lvq, u, (z0 - 0.5) if sd < 0 else (z1 + 0.5))
            n_lo = sum(1 for u in range(int(a_lo), int(a_hi)) if beside(u + 0.5, -1) is not None)
            n_hi = sum(1 for u in range(int(a_lo), int(a_hi)) if beside(u + 0.5, 1) is not None)
            side = -1 if n_lo > n_hi else 1
            u = a_lo
            while u < a_hi - 1e-6:
                r = beside(u + 0.5, side)
                u1 = u + 1.0
                while u1 < a_hi - 1e-6 and beside(u1 + 0.5, side) is r: u1 += 1.0
                s0, s1 = u, min(u1, a_hi)
                if thin_x: sk = (x0, y0, s0, x0 + 0.5, y1, s1) if side < 0 else (x1 - 0.5, y0, s0, x1, y1, s1)
                else: sk = (s0, y0, z0, s1, y1, z0 + 0.5) if side < 0 else (s0, y0, z1 - 0.5, s1, y1, z1)
                if not (r is None and lv == 'B'):
                    fin = finish(r) if (r is not None and lv != 'R') else None
                    col = (fin['hi'] if fin else wallcol(r)) if r is not None else T['brick']
                    meta = (('x' if thin_x else 'z'), side, fin, Ly, Ly + CEIL) if fin else None     # (faces the room)
                    pieces.append((sk, col, M_('sc_wall', lv) if r is not None else 'sc_ext', lv, meta))
                u = u1
            if thin_x: x0, x1 = (x0 + 0.5, x1) if side < 0 else (x0, x1 - 0.5)
            else: z0, z1 = (z0 + 0.5, z1) if side < 0 else (z0, z1 - 0.5)
        if lv == 'B': continue
        ext = finish(None)
        meta = (('x' if thin_x else 'z'), -side, ext, Ly, y1) if (side is not None and lv != 'R') else None     # (faces out)
        pieces.append(((x0, y0, z0, x1, y1, z1), T['brick'], 'sc_ext', lv, meta))
    for (lv, ax, line, a0, a1, y0, y1) in L.GLASS:
        pieces = cut_rect2(pieces, ax, line, a0, a1, y0, y1)
        window_unit2(M_('sc_win', lv), ax, line, a0, a1, y0, y1, line - 0.5, line + 0.5, mull=2)
    for (lv, ax, line, a0, a1, y0, y1, out) in EXT_WIN:
        pieces = cut_rect2(pieces, ax, line, a0, a1, y0, y1)
        t0, t1 = (line, line + 2.0) if out > 0 else (line - 2.0, line)
        window_unit2(M_('sc_win', lv), ax, line, a0, a1, y0, y1, t0, t1)
    for (lv, ax, line, a0, a1, y0, y1) in TRANSOMS:
        pieces = cut_rect2(pieces, ax, line, a0, a1, y0, y1, tol=1.2)
    for (b, col, model, lv, meta) in pieces:
        if meta: articulate(model, b, meta[0], meta[1], meta[2], meta[3], meta[4])
        else: bx(model, col, b)

def v2_copings():
    for w in L.WALLS:
        x0, y0, z0, x1, y1, z1 = w['box']
        if w['lv'] != 'R' or w['mat'] == 'glass' or y1 > 46: continue
        col = T['stone'] if VARIANT == 'v2A' else T['board']
        if (x1 - x0) < (z1 - z0): bx('sc_roofdress', col, (x0 - 0.35, y1, z0, x1 + 0.35, y1 + 0.6, z1), bev=0.1)
        else: bx('sc_roofdress', col, (x0, y1, z0 - 0.35, x1, y1 + 0.6, z1 + 0.35), bev=0.1)

def v2_openings():
    """deep frames: jambs standing 0.35 proud of the hit face on both sides and a head; a glazed transom over v2A's
    doorways; the zombie windows get a frame and a deep sill (the mode nails its planks in the opening)"""
    for o in L.OPENINGS:
        ax, line, a0, a1, y0, y1, kind = o['axis'], o['line'], o['a0'], o['a1'], o['y0'], o['y1'], o['kind']
        lv = lvl_of(y0 + 1.0)
        r_lo = L.room_at(lv, line - 0.5, (a0 + a1) / 2) if ax == 'z' else L.room_at(lv, (a0 + a1) / 2, line - 0.5)
        r_hi = L.room_at(lv, line + 0.5, (a0 + a1) / 2) if ax == 'z' else L.room_at(lv, (a0 + a1) / 2, line + 0.5)
        if r_lo is not None and r_hi is not None: t0, t1 = line - 0.5, line + 0.5
        elif r_lo is None: t0, t1 = line - 2.0, line
        else: t0, t1 = line, line + 2.0
        model = M_('sc_frame', lv)
        def B3(u0, v0, w0, u1, v1, w1, col, kind_='plastic', bev=0.0):
            if ax == 'x': bx(model, col, (u0, v0, w0, u1, v1, w1), kind_, bev=bev)
            else: bx(model, col, (w0, v0, u0, w1, v1, u1), kind_, bev=bev)
        fw, pr, fc = ST2['frameW'], 1.1, ST2['frame']     # (round 4: portals 2 deeper than the wall, a stud each side)
        if kind == 'zwin':
            if lv == 'R': continue
            B3(a0 - 0.6, y0, t0 - 0.15, a0, y1, t1 + 0.15, fc); B3(a1, y0, t0 - 0.15, a1 + 0.6, y1, t1 + 0.15, fc)
            B3(a0 - 0.6, y1, t0 - 0.15, a1 + 0.6, y1 + 0.6, t1 + 0.15, fc)
            if o['y0'] > LVY(lv) + 0.5: B3(a0 - 0.5, y0 - 0.5, t0 - 0.55, a1 + 0.5, y0, t1 + 0.55, ST2['sill'])
            continue
        Lf = LVY(lv)
        head0 = y1 + (1.45 if kind == 'door' else 0.0)          # (a shutter's housing sits over its opening)
        tr = next((t for t in TRANSOMS if t[0] == lv and t[1] == ax and abs(t[2] - line) < 0.01 and abs(t[3] - a0) < 0.01), None)
        if tr and tr[5] < head0 + 1.3: tr = None      # (the deeper head covers where the transom was)
        jtop = (tr[6] + 0.4) if tr else head0 + 1.3
        B3(a0 - fw, Lf, t0 - pr, a0, jtop, t1 + pr, fc, bev=0.08)
        B3(a1, Lf, t0 - pr, a1 + fw, jtop, t1 + pr, fc, bev=0.08)
        B3(a0 - fw - 0.3, head0, t0 - pr - 0.15, a1 + fw + 0.3, head0 + 1.3, t1 + pr + 0.15, fc, bev=0.12)
        if tr:
            ty0, ty1 = tr[5], tr[6]
            B3(a0, ty0, (t0 + t1) / 2 - 0.06, a1, ty1, (t0 + t1) / 2 + 0.06, 'e8e2d4', 'glass')
            B3(a0 - fw - 0.2, ty1, t0 - pr - 0.1, a1 + fw + 0.2, ty1 + 0.4, t1 + pr + 0.1, fc, bev=0.08)
            for mm in (a0 + (a1 - a0) / 3, a0 + 2 * (a1 - a0) / 3):
                B3(mm - 0.2, ty0, t0 - 0.05, mm + 0.2, ty1, t1 + 0.05, fc)

# ---------------------------------------------------------------- the light fittings, planned once (v2_lights, v2_ceilings)
FIXTURES = []        # dict(x, y, z, lv, room, lit, dead, group, axis, gym)
LIGHT_GROUPS = []    # per K.LIGHTS entry: its flicker group (0: steady)
def _hash(*v):
    h = 2166136261
    for x in v:
        for ch in ('%.2f|' % x).encode():
            h = ((h ^ ch) * 16777619) & 0xffffffff
    return h / 4294967296.0

def v2_plan():
    """beams on the S grid across each room's short side, one fitting in the middle of every bay (two or three rows in a
    wide room); a light on every other fitting (pools of light and shadow), a few dead fittings, and up to two per room
    that flicker together (the room's group)"""
    S = ST2['S']
    room_n = 0
    for k, r in enumerate(L.ROOMS):
        lv = r['lv']
        if lv == 'R' or r['tower'] or not r['floor'] or r['look'] in ('court', 'gymair', 'courtair', 'balcony'): continue
        x0, z0, x1, z1 = r['r']
        Ly = LV[lv]
        gym = r['look'] == 'gym'
        top = 37.0 if gym else Ly + CEIL
        Sx = 16.0 if gym else S
        along_x = (x1 - x0) >= (z1 - z0)
        a0, a1 = (x0, x1) if along_x else (z0, z1)
        c0, c1 = (z0, z1) if along_x else (x0, x1)
        beams = [kk * Sx for kk in range(int(math.ceil((a0 + 1.5) / Sx)), int(math.floor((a1 - 1.5) / Sx)) + 1)]
        edges = [a0] + beams + [a1]
        span = c1 - c0
        rows = 1 if span <= 22 else (2 if span <= 46 else 3)
        r['_beams'] = beams
        flick_here = 0
        room_n += 1
        grp = (room_n % 22) + 1
        for bi in range(len(edges) - 1):
            ua, ub = edges[bi], edges[bi + 1]
            if ub - ua < 3.0: continue
            um = (ua + ub) / 2
            for ri in range(rows):
                cm = c0 + span * (ri + 0.5) / rows
                x, z = (um, cm) if along_x else (cm, um)
                if in_hole(lv, x, z): continue
                y = top - (2.2 if ST2['fixture'] == 'globe' else 0.6)
                if gym: y = top - 4.5
                h = _hash(x, z, Ly)
                # (a fitting about every 24 studs: every other bay in v2A's 12, every third in v2B's 8. Round 1's judges saw
                #  every fitting glowing and no pools: now each fitting has its light, and about 1 in 5 is dead)
                if not gym and (bi + ri) % max(2, int(round(24.0 / Sx))) != 0: continue
                if r['id'] == 'lobby' and 54.5 < z < 61.5: continue      # (the girder over the lobby's posts)
                # (26 Nov 2026, the owner on zombies: "not all ceiling likes should work so the ones that do give a better
                #  vibe": in v2B about 4 in 10 fittings are dead in every room but the gym, and a room never ends up with
                #  none lit (below). v2A keeps its 1 in 5 in the halls)
                dead = (not gym) and ((h < DEAD_SHARE) if VARIANT == 'v2B' else (h < 0.2 and (r['look'] in HALLS or r['look'] in SERVICE)))
                f = dict(x=x, y=y, z=z, lv=lv, room=k, lit=not dead, dead=dead, group=0, axis='x' if along_x else 'z', gym=gym)
                if not dead and not gym and flick_here < 2 and h > 0.86:
                    f['group'] = grp; flick_here += 1
                FIXTURES.append(f)
        mine = [f for f in FIXTURES if f['room'] == k]
        if mine and not any(f['lit'] for f in mine):
            keep = min(mine, key=lambda f: _hash(f['x'], f['z'], 7.0))      # (one lit fitting at least, picked the same each build)
            keep['lit'], keep['dead'] = True, False
    print('FIXTURES %d: %d lit, %d flicker, %d dead' % (len(FIXTURES), sum(f['lit'] for f in FIXTURES), sum(1 for f in FIXTURES if f['group']), sum(f['dead'] for f in FIXTURES)))
DEAD_SHARE = 0.42

def v2_lights():
    col, b, rng = ST2['light'], ST2['lightB'], ST2['lightR']
    for f in FIXTURES:
        if not f['lit']: continue
        if ST2['fixture'] == 'trough' and not f['gym']:
            # (v2B, round 3: a spot pointing down from just under the lens: a pool on the floor, the ceiling left dim, so
            #  the lens reads as the light; a point light under it lit the ceiling brighter than the lamp)
            K.light('spot', f['x'], f['y'] - 0.7, f['z'], (0, -1, 0), 1.6, 21.0, 82, col)
        else:
            y = f['y'] - (1.6 if ST2['fixture'] == 'globe' else 3.5)
            K.light('point', f['x'], y, f['z'], (0, -1, 0), b * (1.2 if f['gym'] else 1.0), rng * (1.7 if f['gym'] else 1.0), 0, col)
        LIGHT_GROUPS.append(f['group'])
    # the courtyard's lanterns, the roof's floods (cold, low), the stairwells
    for (x, z) in ((-30, -24), (30, 24), (-30, 24), (30, -24)):
        K.light('point', x, 8.6, z, (0, -1, 0), 1.1, 28, 0, 'ffd2a0'); LIGHT_GROUPS.append(0)
    # (the courtyard read black under the night look: a cold moon fill high over it, wide and faint)
    for (x, z) in ((-18, 0), (18, 0)):
        K.light('point', x, 26.0, z, (0, -1, 0), 0.35, 52, 0, 'a9b9e6'); LIGHT_GROUPS.append(0)
    for (x, y, z) in COURT_LANTERNS:
        K.light('point', x, y - 0.6, z, (0, -1, 0), 0.95, 30, 0, 'ffc98e'); LIGHT_GROUPS.append(0)
    K.light('point', 0.0, 5.5, 0.0, (0, 1, 0), 0.6, 20, 0, 'ffe2b8'); LIGHT_GROUPS.append(0)     # (the tree, from its planter)
    for (x, z) in ((-90, -50), (-10, -50), (70, -50), (130, -60)):
        K.light('point', x, 44.0, z, (0, -1, 0), 0.6, 40, 0, 'b9c8f0'); LIGHT_GROUPS.append(0)
    for i, (ax, az, bx_, bz) in enumerate(((-105.0, -5.0, -115.0, -30.0), (155.0, -53.0, 145.0, -81.0))):
        for y in (-16.0, 0.0, 16.0, 32.0):
            K.light('point', ax, y + 12.5, az, (0, -1, 0), 0.8, 20, 0, col)       # (over landing A, off the middle wall)
            LIGHT_GROUPS.append(23 + i if y == 0.0 else 0)      # (each stairwell's ground-floor landing flickers)
            if y < 32.0:
                K.light('point', bx_, y + 8.0 + 4.5, bz, (0, -1, 0), 0.7, 18, 0, col)   # (over landing B, half way up)
                LIGHT_GROUPS.append(0)
    # emergency lights: a dim green glow over every third shutter; red in the basement's tunnels
    for (x, z) in BASEMENT_RED:
        K.light('point', x, -4.0, z, (0, -1, 0), 0.45, 9, 0, 'ff5a46'); LIGHT_GROUPS.append(0)
    # a faint fill in every room, so no room seen through a doorway is a black hole (round 2: black rooms beyond doors)
    tint = 'ffe6c8' if VARIANT == 'v2A' else 'e6ecf6'
    for r in L.ROOMS:
        if r['lv'] == 'R' or r['tower'] or not r['floor'] or r['look'] in ('court', 'courtair', 'gymair', 'balcony'): continue
        x0, z0, x1, z1 = r['r']
        K.light('point', (x0 + x1) / 2, LV[r['lv']] + 9.0, (z0 + z1) / 2, (0, -1, 0), 0.15 if VARIANT == 'v2B' else 0.3,   # (26 Nov: v2B darker between its lamps)
                min(36.0, 0.55 * max(x1 - x0, z1 - z0) + 8.0), 0, tint)
        LIGHT_GROUPS.append(0)
    # a lamp over every shutter, on both faces (round 3: black shutter bays)
    for d in L.DOORS:
        if d['lv'] == 'R': continue
        mn, mx = d['box']['min'], d['box']['max']
        K.light('point', (mn[0] + mx[0]) / 2, mx[1] + 1.0, (mn[2] + mx[2]) / 2, (0, -1, 0),
                0.85 if VARIANT == 'v2B' else 0.45, 16 if VARIANT == 'v2B' else 13, 0, tint); LIGHT_GROUPS.append(0)   # (26 Nov: v2B's darker halls: a door you can buy still reads)
    # the gym: a sconce on every brick pier at 8 studs, spots under the high bays (round 3: black lower walls)
    for (px, pz) in GYM_SCONCES:
        K.light('point', px, 8.0, pz, (0, -1, 0), 0.55, 16, 0, 'ffcf9a' if VARIANT == 'v2A' else 'e2eaff'); LIGHT_GROUPS.append(0)
    for f in FIXTURES:
        if f['gym'] and f['lit']:
            K.light('spot', f['x'], f['y'] - 0.4, f['z'], (0, -1, 0), 1.2, 34, 70, col); LIGHT_GROUPS.append(0)
    # a warm sconce in the corner beside the main stairs, under the floor that carries over them (round 2: a black corner)
    K.light('point', 62.2, 8.4, 18.0, (0, -1, 0), 0.6, 14, 0, 'ffcf9a' if VARIANT == 'v2A' else 'e2eaff'); LIGHT_GROUPS.append(0)
BASEMENT_RED = ((-50, -20), (-20, -42), (30, -42), (-80, 6))
# wall sconces in the gym, on its long walls' brick piers (x every 16 on the z walls, z every 16 on the east wall)
GYM_SCONCES = ([(x, -29.6) for x in (80.0, 112.0, 144.0)] + [(x, 53.6) for x in (80.0, 112.0, 144.0)] +
               [(157.6, z) for z in (-16.0, 16.0, 48.0)])     # (the lights' spots, 2.4 off the wall lines)
# wall lanterns on the courtyard's ground-floor piers (the light's spot, 0.9 off the wall): x on the long walls, z on the ends
COURT_LANTERNS = ([(x, 8.0, -30.6) for x in (-24.0, 24.0)] + [(x, 8.0, 30.6) for x in (-24.0, 24.0)] +
                  [(-38.6, 8.0, z) for z in (-12.0, 12.0)] + [(38.6, 8.0, z) for z in (-12.0, 12.0)])

def v2_ceilings():
    """ceilings (none over the stair hole), beams on the S grid (v2B: soffits along the long walls too: a waffle), and
    the fittings"""
    EXPOSED = ('tunnel', 'storage', 'workshop', 'boiler', 'janitor')
    for k, r in enumerate(L.ROOMS):
        lv = r['lv']
        if lv == 'R' or r['tower'] or r['look'] in ('court', 'courtair', 'gymair', 'balcony'): continue
        x0, z0, x1, z1 = r['r']
        Ly = LV[lv]
        gym = r['look'] == 'gym'
        top = 37.0 if gym else Ly + 15.0
        g = L.GRID[lv]
        def inset(side):
            if side == 'w': i, j = int(x0) - 1 - L.GX0, int((z0 + z1) / 2) - L.GZ0
            elif side == 'e': i, j = int(x1) - L.GX0, int((z0 + z1) / 2) - L.GZ0
            elif side == 'n': i, j = int((x0 + x1) / 2) - L.GX0, int(z0) - 1 - L.GZ0
            else: i, j = int((x0 + x1) / 2) - L.GX0, int(z1) - L.GZ0
            nb = g[i][j] if 0 <= i < L.NX and 0 <= j < L.NZ else -1
            if nb < 0: return 0.0
            return 0.5 if L.needs_wall(k, nb) else 0.0
        ix0, ix1, iz0, iz1 = x0 + inset('w'), x1 - inset('e'), z0 + inset('n'), z1 - inset('s')
        holes = HOLES.get(lv, [])
        mc = M_('sc_ceil', lv)
        if not gym:
            c = T['concrete'] if r['look'] in EXPOSED else T['ceiling']
            for (a, b_, c_, d_) in minus((ix0, iz0, ix1, iz1), holes):
                bx(mc, c, (a, top - 0.3, b_, c_, top, d_))
        beams = r.get('_beams', [])
        along_x = (x1 - x0) >= (z1 - z0)
        bd = 3.0 if gym else (1.6 if VARIANT == 'v2A' else 1.4)
        bw = 3.0 if gym else ST2['PW']
        bcol = ('6c7176' if VARIANT == 'v2A' else T['board']) if gym else (T['concrete'] if r['look'] in EXPOSED else ST2['beam'])
        rects = []
        for p in beams:
            rects.append((p - bw / 2, iz0, p + bw / 2, iz1) if along_x else (ix0, p - bw / 2, ix1, p + bw / 2))
        if r['id'] == 'lobby':
            # a girder across the lobby on its two posts' line (z 58), deeper than the beams it carries
            for (a, b_, c_, d_) in minus((ix0, 56.0, ix1, 60.0), holes):
                bx(mc, bcol, (a, top - 0.3 - bd - 0.5, b_, c_, top - 0.3, d_))
        if VARIANT == 'v2B' and not gym:
            sw = 1.2
            rects += [(ix0, iz0, ix1, iz0 + sw), (ix0, iz1 - sw, ix1, iz1)] if along_x else [(ix0, iz0, ix0 + sw, iz1), (ix1 - sw, iz0, ix1, iz1)]
        for ri_, rc in enumerate(rects):
            dd = bd if ri_ < len(beams) else bd - 0.2          # (v2B's soffits a step shallower than the beams: no shared faces)
            for (a, b_, c_, d_) in minus(rc, holes):
                bx(mc, bcol, (a, top - 0.3 - dd, b_, c_, top - 0.3, d_))
    for f in FIXTURES:
        x, y, z, lv = f['x'], f['y'], f['z'], f['lv']
        model = ('sc_flk%dx' % f['group']) if f['group'] else M_('sc_fix', lv)     # (WebArena's import strips trailing digits)
        core = '3e3d3a' if f['dead'] else ST2['core']
        ck = 'plastic' if f['dead'] else 'neon'
        top = 37.0 if f['gym'] else LV[lv] + 15.0
        mf = M_('sc_fix', lv)
        if f['gym']:
            # a high-bay lamp: a chunky shade on a stem, a frosted bowl, a small core
            K.cyl(mf, ST2['frame'], x, y + 1.6, z, 0.25, top - 0.3 - (y + 1.6), segs=6, bev=0)
            K.cyl(mf, '5e6368', x, y + 0.4, z, 1.6, 1.3, segs=12, r2=0.7, bev=0.1)
            K.cyl(model, ST2['shade'], x, y, z, 1.4, 0.45, segs=12, kind='glass', bev=0)
            K.cyl(model, core, x, y + 0.2, z, 0.5, 0.3, segs=8, kind=ck, bev=0)
        elif ST2['fixture'] == 'globe':
            K.cyl(mf, ST2['frame'], x, top - 0.55, z, 0.65, 0.25, segs=10, bev=0)
            K.cyl(mf, ST2['frame'], x, y + 0.9, z, 0.2, top - 0.55 - (y + 0.9), segs=6, bev=0)
            K.cyl(mf, ST2['frame'], x, y + 0.75, z, 0.5, 0.3, segs=10, bev=0)
            K.sphere(model, ST2['shade'], x, y, z, 0.95, segs=12, rings_=8, kind='glass')
            K.sphere(model, core, x, y, z, 0.32, segs=6, rings_=4, kind=ck)
        else:
            al = f['axis'] == 'x'
            L2, W2 = 2.8, 0.7
            hx, hz = (L2, W2) if al else (W2, L2)
            bx(mf, '585e64', (x - hx - 0.15, y - 0.2, z - hz - 0.15, x + hx + 0.15, top - 0.3, z + hz + 0.15), bev=0.1)
            bx(model, ST2['shade'], (x - hx, y - 0.42, z - hz, x + hx, y - 0.2, z + hz), 'glass')
            cc = core if f['dead'] else 'a9b8c6'      # (round 3: a brighter lens, nearly the whole diffuser)
            bx(model, cc, (x - hx + 0.2, y - 0.46, z - hz + 0.15, x + hx - 0.2, y - 0.4, z + hz - 0.15), ck)
    # the green lamps over every third shutter (no sign, no text) and the basement's red lamps
    for i, d in enumerate(L.DOORS):
        if i % 3 or d['lv'] == 'R': continue
        mn, mx = d['box']['min'], d['box']['max']
        cx, cz = (mn[0] + mx[0]) / 2, (mn[2] + mx[2]) / 2
        y = mx[1] + 3.2       # (over the deeper heads)
        mf = M_('sc_fix', d['lv'])
        if d['axis'] == 'z':
            bx(mf, '33363a', (cx - 1.1, y - 0.4, cz - 1.2, cx + 1.1, y + 0.4, cz + 1.2), bev=0.1)
            bx(mf, ST2['exitc'], (cx - 1.2, y - 0.25, cz - 0.9, cx + 1.2, y + 0.25, cz + 0.9), 'neon')
        else:
            bx(mf, '33363a', (cx - 1.2, y - 0.4, cz - 1.1, cx + 1.2, y + 0.4, cz + 1.1), bev=0.1)
            bx(mf, ST2['exitc'], (cx - 0.9, y - 0.25, cz - 1.2, cx + 0.9, y + 0.25, cz + 1.2), 'neon')
    for (px, pz) in GYM_SCONCES:        # (the gym's sconces: a box, a frosted shade, a core)
        if pz < 0 or pz > 50:
            s_ = 1 if pz < 0 else -1
            w = -32.0 if pz < 0 else 56.0          # the wall line; its pier face is 0.75 off it
            def Z(a, b): return (min(w + s_ * a, w + s_ * b), max(w + s_ * a, w + s_ * b))
            za, zb = Z(0.6, 1.8); bx(M_('sc_fix', 'G'), ST2['frame'], (px - 0.7, 8.3, za, px + 0.7, 9.8, zb), bev=0.1)
            za, zb = Z(0.9, 1.65); bx(M_('sc_fix', 'G'), ST2['shade'], (px - 0.55, 7.0, za, px + 0.55, 8.3, zb), 'glass')
            za, zb = Z(1.1, 1.45); bx(M_('sc_fix', 'G'), ST2['core'], (px - 0.2, 7.4, za, px + 0.2, 8.0, zb), 'neon')
        else:                                       # (the east wall's skin face is x 160, its piers 0.25 proud)
            bx(M_('sc_fix', 'G'), ST2['frame'], (158.6, 8.3, pz - 0.7, 159.9, 9.8, pz + 0.7), bev=0.1)
            bx(M_('sc_fix', 'G'), ST2['shade'], (158.75, 7.0, pz - 0.55, 159.5, 8.3, pz + 0.55), 'glass')
            bx(M_('sc_fix', 'G'), ST2['core'], (158.95, 7.4, pz - 0.2, 159.3, 8.0, pz + 0.2), 'neon')
    for i, (ax_, az_) in enumerate(((-105.0, -5.0), (155.0, -53.0))):      # (the stairwells' landing lamps, boxed)
        for yy in (-16.0, 0.0, 16.0):
            bx(M_('sc_fix', lvl_of(yy + 1)), ST2['frame'], (ax_ - 0.9, yy + 13.4, az_ - 0.9, ax_ + 0.9, yy + 14.0, az_ + 0.9), bev=0.1)
            bx(M_('sc_fix', lvl_of(yy + 1)), ST2['shade'], (ax_ - 0.7, yy + 12.9, az_ - 0.7, ax_ + 0.7, yy + 13.4, az_ + 0.7), 'glass')
    bx(M_('sc_fix', 'G'), ST2['frame'], (62.65, 8.0, 17.3, 63.3, 9.6, 18.7), bev=0.1)                    # (the stair-corner sconce)
    bx(M_('sc_fix', 'G'), ST2['shade'], (62.2, 7.6, 17.45, 62.7, 8.9, 18.55), 'glass')
    bx(M_('sc_fix', 'G'), ST2['core'], (62.35, 7.9, 17.8, 62.6, 8.5, 18.2), 'neon')
    for (x, z) in BASEMENT_RED:
        bx('sc_fix_B', '33363a', (x - 0.7, -2.4, z - 0.7, x + 0.7, -1.0, z + 0.7), bev=0.1)
        bx('sc_fix_B', '6e2e2a', (x - 0.5, -2.9, z - 0.5, x + 0.5, -2.4, z + 0.5), 'neon')

def prism(model, col, pts, axis, c0, c1, kind='plastic'):
    """a convex outline extruded along an axis: axis 'z': pts are (x, y), from z c0 to c1; axis 'x': pts are (z, y)"""
    import bmesh
    bm = bmesh.new()
    if axis == 'z':
        a = [bm.verts.new((u, v, c0)) for (u, v) in pts]; b = [bm.verts.new((u, v, c1)) for (u, v) in pts]
    else:
        a = [bm.verts.new((c0, v, u)) for (u, v) in pts]; b = [bm.verts.new((c1, v, u)) for (u, v) in pts]
    bm.faces.new(a); bm.faces.new(b[::-1])
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], b[i], b[j], a[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for e in bm.edges: e.smooth = False
    K.put(model, kind, col, bm)

def v2_stairs():
    """the treads (as v1); the parapets from the layout (the main stairs' open side, the bleachers' sides) solid with a
    cap; the balcony's edge a solid parapet on its rail's hit box"""
    m = 'sc_stair'
    for k in range(1, 17):
        za, zb = 22 - 2.0 * k, 22 - 2.0 * (k - 1)
        bx(m, STEPC, (54.0, 0.0, za, 64.0, k - 0.5, zb))
        bx(m, NOSE, (54.0, k - 0.62, zb - 0.35, 64.0, k - 0.44, zb + 0.06))
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
        elif kind == 'post': bx('sc_gymdress', ST2['parapet'], (x0 - 0.3, y0, z0 - 0.3, x1 + 0.3, y1, z1 + 0.3), bev=0.15)
        elif kind == 'parapet': pass          # (drawn sloped below)
    # the sloped parapets over the layout's stepped ones: the main stairs' open side, both sides of the bleachers
    prism(m, ST2['parapet'], [(22.0, 0.0), (-10.0, 0.0), (-10.0, 19.4), (22.0, 3.4)], 'x', 53.65, 54.35)
    _rail(m, (54.0, 3.5, 22.0), (54.0, 19.5, -10.0), t=0.85, col=ST2['cap'])
    for (za, zb) in ((-4.7, -4.0), (36.0, 36.7)):
        prism('sc_gymdress', ST2['parapet'], [(108.0, 0.0), (108.0, 3.2), (76.0, 19.2), (76.0, 0.0)], 'z', za, zb)
        _rail('sc_gymdress', (108.0, 3.3, (za + zb) / 2), (76.0, 19.3, (za + zb) / 2), t=0.85, col=ST2['cap'])
    # the bleachers: grey risers, a seat board each
    for k in range(1, 17):
        xa, xb = 108 - 2.0 * k, 108 - 2.0 * (k - 1)
        bx('sc_gymdress', '8d9196', (xa, 0.0, -4.0, xb, k - 0.5, 36.0))
        bx('sc_gymdress', 'b7925f', (xb - 1.2, k - 0.56, -3.8, xb + 0.05, k - 0.3, 35.8), bev=0.08)
    # the balcony: a solid parapet on its rail's hit box
    for (za, zb) in ((-32.0, -4.0), (36.0, 56.0)):
        bx('sc_gymdress', ST2['parapet'], (75.4, 16.0, za, 76.1, 19.5, zb))
        bx('sc_gymdress', ST2['cap'], (75.25, 19.5, za, 76.25, 19.9, zb), bev=0.1)

def gym_hoops():
    """a basketball backboard and hoop on each end wall of the gym: a chunky bracket, a board, a ring of boxes"""
    m = 'sc_gymdress'
    for (z, s) in ((-32.0, 1), (56.0, -1)):
        x = 96.0         # (clear of the shutters at x 118..130 on both end walls)
        w = z + s * 0.5
        def Z(a, b): return (min(w + s * a, w + s * b), max(w + s * a, w + s * b))
        za, zb = Z(0.0, 3.0); bx(m, ST2['frame'], (x - 0.8, 13.0, za, x + 0.8, 14.2, zb), bev=0.1)        # the bracket
        za, zb = Z(3.0, 3.5); bx(m, 'd9dcdc' if VARIANT == 'v2A' else 'cfd3d6', (x - 3.6, 11.0, za, x + 3.6, 15.4, zb), bev=0.12)
        za, zb = Z(2.9, 3.0); bx(m, ST2['frame'], (x - 1.2, 12.2, za, x + 1.2, 13.8, zb))                  # (the square on the board)
        r_ = 1.0
        zc = w + s * (3.5 + r_ + 0.1)
        for (a0_, b0_, a1_, b1_) in ((x - r_, zc - r_, x + r_, zc - r_ + 0.3), (x - r_, zc + r_ - 0.3, x + r_, zc + r_),
                                    (x - r_, zc - r_, x - r_ + 0.3, zc + r_), (x + r_ - 0.3, zc - r_, x + r_, zc + r_)):
            bx(m, 'b0663a' if VARIANT == 'v2A' else L.ACCENT, (a0_, 11.6, min(b0_, b1_), a1_, 11.9, max(b0_, b1_)))

def tower_soffits():
    """a sloped slab under every flight of the stairwells (round 3: the steps' undersides showed separate blocks with black
    gaps)"""
    m = 'sc_stair'
    for (x0, x1, xm, zA, zB, f1, f2) in ((-120, -100, -110, (-10, 0), (-34, -26), (-120, -110), (-110, -100)),
                                        (140, 160, 150, (-58, -48), (-88, -74), (150, 160), (140, 150))):
        za_edge, zb_edge = zA[0], zB[1]
        for lv in ('B', 'G', 'U'):
            Ly = LV[lv]
            prism(m, STEPC, [(za_edge, Ly - 2.0), (za_edge, Ly - 0.5), (za_edge - 16.0, Ly + 7.5), (za_edge - 16.0, Ly + 6.0)], 'x', f1[0], f1[1])
            prism(m, STEPC, [(zb_edge, Ly + 6.0), (zb_edge, Ly + 7.5), (zb_edge + 16.0, Ly + 15.5), (zb_edge + 16.0, Ly + 14.0)], 'x', f2[0], f2[1])

def v2_court():
    """the courtyard's covered walk: a deep canopy along all four walls at first-floor height, a fascia, brackets (v2A)"""
    A = VARIANT == 'v2A'
    m = 'sc_court'
    D, y0, y1 = 5.5, 12.0, 13.6       # (round 3: deeper and thicker)
    roof = '585d61' if A else T['board']
    fas = ST2['frame'] if A else T['board']
    e = 0.5 + D
    spans = [('z', -32.0, -39.5, 39.5, 1), ('z', 32.0, -39.5, 39.5, -1), ('x', -40.0, -32.0 + e, 32.0 - e, 1), ('x', 40.0, -32.0 + e, 32.0 - e, -1)]
    for (ax, line, a0, a1, inward) in spans:
        f0 = line + inward * 0.5
        f1 = f0 + inward * D
        lo, hi = min(f0, f1), max(f0, f1)
        ff = (f1 - inward * 0.8, f1)
        if ax == 'z':
            bx(m, roof, (a0, y0, lo, a1, y1, hi))
            bx(m, fas, (a0, y0 - 1.4, min(ff), a1, y1 + 0.3, max(ff)))
        else:
            bx(m, roof, (lo, y0, a0, hi, y1, a1))
            bx(m, fas, (min(ff), y0 - 1.4, a0, max(ff), y1 + 0.3, a1))
        if True:    # brackets on the piers the lanterns don't use (round 3: "a deep bracketed canopy")
            k0, k1 = int(math.ceil((a0 + 2) / 12.0)), int(math.floor((a1 - 2) / 12.0))
            for k in range(k0, k1 + 1):
                p = k * 12.0
                if abs(abs(p) - (24.0 if ax == 'z' else 12.0)) < 0.1 or (ax == 'x' and abs(p) < 0.1): continue
                if ax == 'z': _rail(m, (p, 8.6, f0 + inward * 1.2), (p, y0 - 0.25, f0 + inward * (D - 1.2)), t=0.8, col=ST2['bracket'] or ST2['frame'])
                else: _rail(m, (f0 + inward * 1.2, 8.6, p), (f0 + inward * (D - 1.2), y0 - 0.25, p), t=0.8, col=ST2['bracket'] or ST2['frame'])

def court_lanterns():
    """a wall lantern on each of eight ground-floor piers: a chunky bracket box, a frosted shade, a small warm core"""
    m = 'sc_court'
    shade = 'e9dfcc' if VARIANT == 'v2A' else 'dfe5e8'
    core = '8a7350' if VARIANT == 'v2A' else '7f8a96'
    for (x, y, z) in COURT_LANTERNS:
        if abs(abs(z) - 30.6) < 0.1:
            sz = 1 if z < 0 else -1          # (pointing into the yard)
            w = z - sz * 0.9                 # the wall face
            def Z(a, b): return (min(w + sz * a, w + sz * b), max(w + sz * a, w + sz * b))
            za, zb = Z(0.0, 1.3); bx(m, ST2['frame'], (x - 0.6, y - 0.2, za, x + 0.6, y + 1.4, zb), bev=0.1)
            za, zb = Z(0.3, 1.2); bx(m, shade, (x - 0.5, y - 1.3, za, x + 0.5, y - 0.2, zb), 'glass')
            za, zb = Z(0.6, 0.9); bx(m, core, (x - 0.18, y - 1.0, za, x + 0.18, y - 0.5, zb), 'neon')
        else:
            sx = 1 if x < 0 else -1
            w = x - sx * 0.9
            def X(a, b): return (min(w + sx * a, w + sx * b), max(w + sx * a, w + sx * b))
            xa, xb = X(0.0, 1.3); bx(m, ST2['frame'], (xa, y - 0.2, z - 0.6, xb, y + 1.4, z + 0.6), bev=0.1)
            xa, xb = X(0.3, 1.2); bx(m, shade, (xa, y - 1.3, z - 0.5, xb, y - 0.2, z + 0.5), 'glass')
            xa, xb = X(0.6, 0.9); bx(m, core, (xa, y - 1.0, z - 0.18, xb, y - 0.5, z + 0.18), 'neon')

def v2_facade():
    """the outside: a deep plinth, a string course at the first floor, a heavy cornice under the parapet"""
    X0, X1, Z0, Z1 = L.FX0, L.FX1, L.FZ0, L.FZ1
    st = T['stone'] if VARIANT == 'v2A' else T['board']
    for (a, b_, c, d_) in ((X0 - 2.5, Z0 - 2.5, X1 + 2.5, Z0 - 2.0), (X0 - 2.5, Z1 + 2.0, X1 + 2.5, Z1 + 2.5),
                          (X0 - 2.5, Z0 - 2.0, X0 - 2.0, Z1 + 2.0), (X1 + 2.0, Z0 - 2.0, X1 + 2.5, Z1 + 2.0)):
        bx('sc_ext', st, (a, -0.2, b_, c, 2.0, d_))
        bx('sc_ext', st, (a, 14.7, b_, c, 15.7, d_))
    for (a, b_, c, d_) in ((X0 - 2.9, Z0 - 2.9, X1 + 2.9, Z0 - 2.0), (X0 - 2.9, Z1 + 2.0, X1 + 2.9, Z1 + 2.9),
                          (X0 - 2.9, Z0 - 2.0, X0 - 2.0, Z1 + 2.0), (X1 + 2.0, Z0 - 2.0, X1 + 2.9, Z1 + 2.0)):
        bx('sc_ext', st, (a, 29.9, b_, c, 31.3, d_))

def v2_build():
    TRANSOMS[:] = transoms()
    v2_slabs(); v2_walls(); bulkhead_corners(); v2_copings(); v2_openings(); v2_ceilings(); v2_stairs()
    _fences = list(L.FENCES)
    # (the balcony's rails are solid parapets now)
    L.FENCES[:] = [f for f in _fences if not (75.0 < f[0] < 76.5 and 15.5 < f[1] < 16.5)]
    fences(); L.FENCES[:] = _fences
    niches_dress(); grounds(); v2_court(); court_lanterns(); v2_facade(); gym_hoops(); tower_soffits()

# ---------------------------------------------------------------- the UVs: world-scaled box projection per textured colour
if not V2:
    TEXSIZE = {T[k]: ST.TEX[k] for k in ST.TEX}
    FLOORUP = {T[k] for k in ('hallwall', 'classwall', 'rtile_wall', 'lockers', 'chalkboard')}
else:       # (v2: each role's picture, from TEX or TEX2; only the floor-up pictures start at their floor)
    _sizes = dict(ST.TEX); _sizes.update(getattr(ST, 'TEX2', {}))
    TEXSIZE = {hx: _sizes[img] for (hx, img) in V2TEX[VARIANT].values() if img in _sizes}
    FLOORUP = {hx for (hx, img) in V2TEX[VARIANT].values() if img in ('rtile_wall', 'hallwall', 'classwall', 'lockers', 'chalkboard', 'b_whiteboard')}
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
        board = hx == T['chalkboard']        # (a chalkboard, or v2B's whiteboard: 16 x 6, its own picture)
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
        byhex = {T[k]: k for k in ST.TEX} if not V2 else {hx: img for (hx, img) in V2TEX[VARIANT].values()}
        dirs = texdir[0].split('|')
        imgs = {}
        for ob in bpy.data.objects:
            if ob.type != 'MESH': continue
            hx = ob.name.rsplit('_', 1)[-1]
            if hx not in byhex: continue
            nm = byhex[hx]
            if nm not in imgs:
                pth = next((os.path.join(d, nm + '.png') for d in dirs if os.path.exists(os.path.join(d, nm + '.png'))), None)
                if pth is None: continue
                imgs[nm] = bpy.data.images.load(pth)
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
    if '--card' in K.FLAGS:          # (a map-vote card: card_render.py's size and quality)
        sc.cycles.samples = 128; sc.render.resolution_x, sc.render.resolution_y = 1280, 720
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
    ('fence', (-20, 16, 120), (28, 4, 170), 24),
    ('hedges', (30, 8, 135), (0, 4, 100), 22),
    ('cafe', (-40, 7, 92), (-90, 4, 50), 18),
    ('zf1', (-26, 7, -8), (-40, 7, -8), 30),
    ('zf2', (-26, 7, 5), (-40, 7, 5), 30),
    ('office', (24, 22, 70), (-14, 18, 90), 18),
]

if V2:
    VIEWS = [v if v[0] != 'court' else ('court', (-30, 6.5, 22), (24, 9, -24), 18) for v in VIEWS]
    VIEWS += [('stairtop', (44, 22, 30), (60, 12, -4), 18), ('exit', (-20, 6, 40), (30, 9, 40), 22)]

def check_walls():
    """(--check-walls) does the kit's wall cover every hit wall? at each level's mid height, every 0.25 stud of a hit
    wall's footprint (minus the openings and windows) should be under some wall piece of the kit"""
    got = []
    _B = K.B
    def grab(model, col, x0, y0, z0, x1, y1, z1, **kw):
        if kw.get('M') is None: got.append((min(x0, x1), min(y0, y1), min(z0, z1), max(x0, x1), max(y0, y1), max(z0, z1), model, col))
    K.B = grab
    if V2: TRANSOMS[:] = transoms(); v2_walls()
    else: walls()
    bulkhead_corners()
    K.B = _B
    holes = []
    for (lv, ax, line, a0, a1, y0, y1) in L.GLASS: holes.append((lv, ax, line, a0, a1, y0, y1))
    for (lv, ax, line, a0, a1, y0, y1, out) in EXT_WIN: holes.append((lv, ax, line, a0, a1, y0, y1))
    if V2: holes += list(TRANSOMS)
    bad = {}
    for w in L.WALLS:
        if w['mat'] == 'glass': continue
        x0, y0, z0, x1, y1, z1 = w['box']
        y = (y0 + y1) / 2
        n = 0
        xs = [x0 + 0.125 + 0.25 * i for i in range(int((x1 - x0) / 0.25))]
        zs = [z0 + 0.125 + 0.25 * i for i in range(int((z1 - z0) / 0.25))]
        if V2:      # (v2's panels are recessed from the faces: check the wall's middle)
            if x1 - x0 < z1 - z0: xs = [(x0 + x1) / 2]
            else: zs = [(z0 + z1) / 2]
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

if V2: v2_plan(); v2_lights()
else: lights()
ext_windows()
write_layout()
if '--check-walls' in K.FLAGS:
    check_walls()
elif '--layout-only' in K.FLAGS:
    print('layout only: no kit')
else:
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)        # (no default cube in the kit)
    if V2: v2_build()
    else: floors_and_ceilings(); walls(); bulkhead_corners(); copings(); openings_dress(); stairs_dress(); fences(); niches_dress(); grounds()
    if '--no-furniture' not in K.FLAGS:
        try:
            import school_props
            if V2:      # (each look's furniture palette: v2A old oak, walnut and sage steel; v2B pale ash and charcoal steel)
                for _k, _v in {'v2A': dict(WOOD='8c6c4e', WOOD_D='6a4c36', WOOD_L='bb9f7c', METAL='7d8a84', METAL_D='55605a', FABRIC='5e6f68',
                            LEGT=0.4, NO_FLAG=True, PILLAR_GROW=1.0,
                            TRUNK=1.9, LIMB=1.4, BARK='8a755d', LEAF='6f9058', LEAF_D='5e7c4a'),
                               'v2B': dict(WOOD='c2a986', WOOD_D='8a7559', WOOD_L='d2bf9f', METAL='6a7076', METAL_D='45494e',
                                           STEEL='a9aeb2', FABRIC='5f6a72', LEGT=0.4, NO_FLAG=True, PILLAR_GROW=1.0,
                                           LEAF='6f9058', LEAF_D='5e7c4a', TRUNK=1.9, LIMB=1.4, BARK='8a755d')}[VARIANT].items():
                    setattr(school_props, _k, _v)
            school_props.furniture(K, L)
        except Exception as e:
            print('NO FURNITURE YET', repr(e))
    # (20 Nov, v2: Roblox turns down a kit with a mesh over 20,000 triangles; v2's globes and housings put ~40k in one
    #  mesh per floor and the upload came back "Unknown Error". Any (model, look) over 18,000 is split into more models)
    #  (v2B still failed at 18,000 triangles of flat boxes, ~36,000 vertices; 10,000 passes)
    SPLIT_AT = 10000
    _big = []
    for (mname, key), items in list(K.PIECES.items()):
        tris = [sum(len(f.verts) - 2 for f in bm.faces) for bm, M in items]
        if sum(tris) <= SPLIT_AT or mname.startswith('sc_flk'): continue
        chunks, cur, n = [[]], 0, 0
        for it, t in zip(items, tris):
            if n + t > SPLIT_AT and chunks[-1]: chunks.append([]); n = 0
            chunks[-1].append(it); n += t
        del K.PIECES[(mname, key)]
        for gi, ch in enumerate(chunks):
            nm = mname if gi == 0 else mname + 'abcdefghijklmnopqrstuvwxyz'[gi]
            if nm != mname and mname in MODEL_BASE: MODEL_BASE[nm] = MODEL_BASE[mname]
            K.PIECES.setdefault((nm, key), []).extend(ch)
        _big.append((mname, key, sum(tris), len(chunks)))
    print('SPLIT (model, look, tris, parts):', _big)
    _tri = {}
    for (mname, key), items in K.PIECES.items():
        _tri[mname] = _tri.get(mname, 0) + sum(sum(len(f.verts) - 2 for f in bm.faces) for bm, M in items)
    print('TRIS BY MODEL', sorted(_tri.items(), key=lambda kv: -kv[1]), 'total', sum(_tri.values()))
    _only = [f[8:].split(',') for f in K.FLAGS if f.startswith('--views=')]
    views = [v for v in VIEWS if v[0] in _only[0]] if _only else VIEWS
    if PREVIEW and '--no-preview' not in K.FLAGS:
        K.render_previews = render_school
    K.finish('school', OUT_DIR, PREVIEW, views, prefix='school', sky=(0.16, 0.13, 0.22), sun_rot=(60, 0, -130), sun_energy=1.2)
