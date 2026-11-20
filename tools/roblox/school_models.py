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
        if lv == 'R' or not r['floor'] or look in ('court', 'landing') or r['tower']: continue
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
    txt = txt[:-1] + extra + '}\n'
    with open(LAYOUT, 'w', newline='\n') as f: f.write(txt)
    print('LAYOUT %s: %d chars' % (LAYOUT, len(txt)))

lights()
write_layout()
if '--layout-only' in K.FLAGS:
    print('layout only: no kit')
