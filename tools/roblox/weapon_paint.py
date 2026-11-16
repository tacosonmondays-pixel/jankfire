# The factory paint of the Roblox weapon templates: which colour and material every piece of every gun gets.
# Pure Python (no bpy): export_weapons.py imports it, paint_preview.py imports it, and it runs on its own.
#
# TWO PAINTS, ONE SWITCH
#   calm  (the default) the Roblox game's own finish: a quiet body, one accent per gun, bright only where it tells the
#         player something (a sight dot, a heat glow, live shells). asked for by the owner on 2026-11-15 ("less
#         colourful", "serious ... roblox rivals touch").
#   web   the web game's paint, exactly as the model files carry it (pictures kept).
# switch:  blender ... -P tools/roblox/export_weapons.py -- <out_dir> --paint web <files>     (exports + repaints)
#          py tools/roblox/weapon_paint.py roblox/assets/weapons/export_report.json --paint web   (repaints the report
#          only, no Blender: the .glb files and the uploaded assets do NOT change with the paint)
#   both also write roblox/studio-tools/WeaponPaint.luau: BOTH paints of every gun + which one is the default. it
#   lives in the place as ServerStorage.PolishBackup.WeaponPaint (node tools/roblox/push.mjs puts it there), and
#   Studio's WeaponImport reads it:  W.use() repaints every template with the default, W.use("web") with the web
#   paint, W.load({ "smg" }) brings a model in again. nothing is typed or pasted by hand.
#
# A PAINT CODE is '<kind><rrggbb>[aa][+]':
#   kind  p plastic (SmoothPlastic) · m dark metal (Metal) · s shiny metal (Metal + a little Reflectance) · n neon (glows)
#         g glass (+ two hex digits of alpha) · w wood (Wood) · r rubber / grip (Plastic, the slightly grainy one)
#   +     keep the piece's picture (if its material has one). without it the picture is taken off: in Roblox a picture
#         ignores the part's Color, so a repainted piece cannot keep it.
# The model files themselves always carry the WEB look in their piece names ("<node>__<material>__<code>"), whatever
# the paint: the paint is applied in Studio from the report (WeaponImport, spec.paint), so no model is uploaded again
# when a colour changes.
#
# THE CALM TABLE: per gun, '<material>' or '<node>__<material>' (the more exact one wins) -> code. a piece that is
# not listed keeps its web look.
import json, sys

PAINTS = ('calm', 'web')
DEFAULT = 'calm'

# the family: dark steel and black polymer stay as the web has them (already quiet); furniture goes to ONE muted
# neutral per gun (olive, tan, walnut, slate, graphite ...) and each gun keeps ONE small accent in its web hue.
# bright chrome goes to mid steel (it washed out to white under the hall lamps), joke stickers take the colour of
# the surface under them, and nothing glows except sights, lenses and heat.
# CHOOSE DARK: the training hall's lamps show a colour far brighter than a Blender preview does (first photo round,
# 2026-11-15: 4c5639 olive came out lime, 4a3222 walnut orange). these values are what looked right IN the hall.
# after the first judge round: every gun needs TWO values (one flat grey reads as clay), pairs that looked alike are
# split by value (Plan B dark, Revolver steel), and big wood is 'r' not 'w' (Wood's grain is coarse up close).
# after the second: a body painted near black (141519) hides its second value, so the big dark pieces are lifted to
# charcoal; an accent goes on ONE clear part (the SMG's magazine, the Lawn Mower's drum), not on a slab of the body;
# 'r' (Plastic) on a big light surface reads as cork, so the Sniper's stock is smooth.
STEEL = 's767b85'      # mid steel (was bright chrome)
STEEL_D = 'm3a3d45'    # dark steel
POLY = 'p1e2024'       # black polymer
RUBBER = 'r1d1e21'     # black rubber / grip
BRASS = 's947839'      # muted brass trim (was shiny gold)
CART = 'sa58640'       # cartridge brass (the web's was a loud yellow)
TIP = 's9c5c3a'        # copper bullet tips
SHELL = 'p9a2b27'      # shotgun hulls: the one red left
WALNUT = 'w3b281c'

CALM = {
 # Assault Rifle: olive furniture on gunmetal, a smoked magazine
 'w_ar': {
  'ar_olive': 'p3e4630', 'ar_grip': 'r343b29', 'ar_tape': 'p2b3122', 'ar_neon': 'p1b1c20', 'ar_sticker': 'm2c3036',
  'ar_charm': STEEL_D, 'ar_mag': 'g2b2e34b8', 'ar_magbase': POLY, 'ar_white': 'pc8c8c8', 'ar_brass': CART, 'ar_copper': TIP,
  'ar_dark': 'p24262b',
 },
 # SMG: black and charcoal, the whole magazine is its teal accent (the handguard's teal slab goes charcoal)
 'w_smg': {
  'smg_body_wzA__smg_teal': 'p2b2e33', 'mag_wzA__smg_teal': 'p1f857c', 'mag_wzB__smg_dark': 'p1f857c',
  'smg_freshener': 'p1c1d21', 'smg_string': 'p1c1d21',
 },
 # Plan B: the dark handgun. black frame, gunmetal slide, a blue rib along the top and blue controls
 'w_pistol': {
  'pb_frame': POLY, 'pb_pearl': 'r2a2c31', 'pb_satin': 'm3f434c', 'pb_polish': 's5f646e', 'pb_rib': 's4a67b8',
  'pb_roll_r': 'm3f434c', 'pb_roll_l': 'm3f434c', 'pb_tin': STEEL_D, 'pb_gold': 's4a67b8', 'pb_medal': 's947839+',
  'pb_brass': CART, 'pb_copper': TIP,
 },
 # Revolver: the steel handgun. steel frame, a dark cylinder, black grip, brass trim, the orange front sight
 'w_revolver': {
  'rv_pearl': RUBBER, 'rv_chrome': 's56585c', 'rv_satin': 'm27292e', 'rv_gold': BRASS, 'hammer_wzN__rv_gold': STEEL_D,
  'rv_copper': TIP,
 },
 # Shotgun: blued steel and dark walnut, red shells
 'w_shotgun': {
  'sg_forend': 'r3b281c', 'sg_walnut': 'r3b281c', 'sg_hull': SHELL, 'sg_brass': CART,
 },
 # Half a Shotgun: dark cherry wood, steel barrels and receiver, red shells
 'w_sawnoff': {
  'so_candy': 'w452a1e', 'so_case': 's474b55', 'so_screw': 's6f747e', 'so_dash': 'm20242c', 'so_sticker': 's474b55',
  'so_hull': SHELL, 'so_cut': 's7d828c', 'so_endgrain': 'w553a29', 'so_tape': 'p1d1d21', 'so_blued': 'm20242c',
  'so_hammer': 'm262a33', 'so_ribtop': 'm20242c', 'so_brass': CART,
 },
 # Sniper: a dark tan stock on black steel, the violet lens, one small magenta mark (its web colour)
 'w_sniper': {
  'sn_pink': 'p57534a', 'sn_sticker': 'p57534a', 'sn_gold': 'pa2457c', 'sn_bolt': STEEL, 'sn_white': 'pc8c8c8',
 },
 # Second Opinion: dusk violet furniture (toned down), the medic cross stays
 'w_dmr': {
  'dm_wood': 'p363349', 'dm_bandaid': 'p363349', 'dm_tubing': 'p3d3a55', 'dm_chrome': STEEL, 'dm_diaphragm': STEEL,
  'dm_sticker': 'm27292f', 'dm_brass': CART, 'dm_copper': TIP,
 },
 # Hat Trick: slate body with darker panels, a blue magazine, its three rounds in dark brass
 'w_burst': {
  'burst_body_wzA__bu_blue': 'p2a323f', 'mag_wzA__bu_blue': 'p2f4f8f', 'bu_navy': 'r181b21', 'bu_yellow': 'p24345c',
  'bu_bread': 's7a6230', 'bu_crumb': 'p2a323f', 'bu_tape': 'p3a3d44', 'bu_chrome': STEEL, 'bu_sticker': 'p2a323f',
  'bu_brass': CART, 'bu_copper': TIP,
 },
 # Belt Sander: graphite body and ammunition box, an orange feed cover and switches, a black cable
 'w_lmg': {
  'lmg_body_wzA__lmg_orange': 'p34373d', 'lmg_body_wzB__lmg_orange': 'p34373d', 'cover_wzA__lmg_orange': 'pb5531f',
  'lmg_grit': 'r5a3b2e', 'lmg_cord': RUBBER, 'lmg_yellow': 'pb5531f', 'lmg_tag': 'p2b2e33', 'lmg_chrome': STEEL,
  'lmg_box': 'p2b2e33', 'lmg_brass': CART, 'lmg_copper': TIP,
 },
 # Lawn Mower: charcoal furniture, the drum is its machine green (that also tells it from the Assault Rifle's olive)
 'w_autoshot': {
  'as_green': 'p2b2e33', 'as_grass': 'p1e2024', 'as_red': 'm34373d', 'mag_wzN__as_red': 'm34373d', 'as_hazard': 'p36563e',
  'mag_wzB__as_dark': 'p36563e', 'as_keep': 'p2b2e33', 'as_mow': 'm121316', 'as_cord': 'p3a3d44', 'as_chrome': STEEL_D,
  'autoshot_body_wzB__as_dark': 'p22242a', 'as_park': 'm2b2e33',
 },
 # Yeehaw: saddle walnut, a steel receiver, brass trim
 'w_lever': {
  'lv_leather': 'r30231d', 'lv_case': 's565b66', 'lv_pink': 'r30231d', 'lv_gem_w': BRASS, 'lv_gem': BRASS,
  'lv_gold': BRASS, 'lv_forend': 'w432b1c', 'lv_walnut': 'w432b1c', 'lv_rope': 'r6f6249', 'lv_brass': CART,
 },
 # Redline: black with its red (touch-ups: the grip and the tape lose their pictures, chrome goes to steel)
 'w_redline': {
  'rl_grip': 'r2b2623', 'rl_tape': 'p9a2b27', 'rl_chrome': STEEL, 'rl_red': 'pb82a2a', 'rl_white': 'pd0d0d0',
  'rl_dark': 'p23252a',
 },
 # Marble Shotgun: aged brass and walnut, a dark smoked jar, the marbles in one blue family (they are the ammunition)
 'w_marbles': {
  'mb_brass': 's6b5c3e', 'mb_walnut': WALNUT, 'mb_plaque': 's6b5c3e', 'mb_zinc': STEEL_D, 'mb_ramrod': 'w553a29',
  'mb_label': 'g23262b66', 'mb_jar': 'g23262b66',
  'mb_marble0': 'p3d6fc4', 'mb_marble1': 'p5aa6d6', 'mb_marble2': 's6b5c3e', 'mb_marble3': 'p2c4f8f',
  'mb_marble4': 'p8fb4dc', 'mb_marble5': 'p9db9d8', 'mb_marble6': 'p4a90c8',
 },
 # Katana: a bright polished blade, black cord over the pale ray skin, the fittings as they are
 'w_katana': {
  'kt_blade': 'sd2d8e0', 'kt_ito': 'r1c1d21',
 },
}


def hex_rgb(h): return [int(h[j:j + 2], 16) / 255 for j in (0, 2, 4)]


def web_code(look):
    """the web look of a piece as a paint code (the same rule as rbxglb.look_code, + the picture mark)"""
    col = look['color']
    if look.get('glow', 0) > 0: code = 'n' + (look.get('glowColor') or col)
    elif look.get('alpha', 1) < 0.95: code = 'g' + col + '%02x' % max(0, min(255, round(look['alpha'] * 255)))
    elif look.get('metal', 0) > 0.5:
        code = ('m' if max(hex_rgb(col)) < 0.4 else 's') + col
    else: code = 'p' + col
    return code + ('+' if look.get('tex') else '')


def code_for(paint, gun, piece, web_look):
    """the paint code of one piece ('<node>__<material>') of one gun ('w_<id>') under a paint"""
    if paint not in PAINTS: raise SystemExit('unknown paint %r (have: %s)' % (paint, ', '.join(PAINTS)))
    if paint == 'calm':
        table = CALM.get(gun, {})
        mat = piece.split('__', 1)[1] if '__' in piece else piece
        code = table.get(piece) or table.get(mat)
        if code:
            if code.endswith('+') and not web_look.get('tex'): code = code[:-1]
            return code
    return web_code(web_look)


def parse(code):
    """'<kind><rrggbb>[aa][+]' -> (kind, 'rrggbb', alpha 0..1 or None, keep_picture)"""
    keep = code.endswith('+')
    if keep: code = code[:-1]
    kind, col, aa = code[0], code[1:7], code[7:9]
    if kind not in 'pmsngwr' or len(col) != 6: raise SystemExit('bad paint code %r' % code)
    int(col, 16)
    return kind, col, (int(aa, 16) / 255 if aa else None), keep


def repaint(report, paint, only=None):
    """write every piece's paint code into an export report (in place). returns the pieces whose table line matched
       nothing (a typo in the table)"""
    used = set()
    for gun, m in report.items():
        if only and gun not in only: continue
        if not all('look' in p for p in m['pieces']): continue  # (exported before looks were recorded)
        for p in m['pieces']:
            p['paint'] = code_for(paint, gun, p['name'], p['look'])
            parse(p['paint'])
            mat = p['name'].split('__', 1)[1]
            for k in (p['name'], mat):
                if k in CALM.get(gun, {}): used.add((gun, k))
        m['paint'] = paint
    return sorted((g, k) for g, t in CALM.items() for k in t if (g, k) not in used and g in report and (not only or g in only))


def write_luau(report, assets, paint, path):
    """the paint book Studio keeps (PolishBackup.WeaponPaint): every gun's asset id, bounds and BOTH paints"""
    def vec(a): return 'Vector3.new(%s)' % ', '.join(repr(x) for x in a)
    out = ['--!nocheck',
           '-- GENERATED by tools/roblox/weapon_paint.py from roblox/assets/weapons/export_report.json + assets.json.',
           '-- do not edit: change the table in weapon_paint.py and run it again. read by PolishBackup.WeaponImport',
           '-- (W.use, W.load). a code is "<kind><rrggbb>[aa][+]", see WeaponImport.',
           'return {',
           '\tpaint = "%s", -- the paint the templates wear' % paint,
           '\tguns = {']
    n = 0
    for gun in sorted(report):
        m = report[gun]
        wid = gun[2:] if gun.startswith('w_') else gun
        if wid not in assets or not m.get('turned') or not all('look' in p for p in m['pieces']): continue
        out.append('\t\t%s = {' % wid)
        out.append('\t\t\tid = %d, lo = %s, hi = %s,' % (assets[wid], vec(m['lo']), vec(m['hi'])))
        for name in PAINTS:
            codes = ', '.join('["%s"] = "%s"' % (p['name'], code_for(name, gun, p['name'], p['look'])) for p in m['pieces'])
            out.append('\t\t\t%s = { %s },' % (name, codes))
        out.append('\t\t},')
        n += 1
    out += ['\t},', '}', '']
    with open(path, 'w', newline='\n') as fh: fh.write('\n'.join(out))
    return n


def book_path(report_path):
    """roblox/studio-tools/WeaponPaint.luau and assets.json, found from where the report is (roblox/assets/weapons)"""
    import os
    d = os.path.dirname(os.path.abspath(report_path))
    return os.path.join(d, 'assets.json'), os.path.normpath(os.path.join(d, '..', '..', 'studio-tools', 'WeaponPaint.luau'))


def write_book(report, report_path, paint):
    import os
    ap, lp = book_path(report_path)
    if not (os.path.exists(ap) and os.path.isdir(os.path.dirname(lp))): return None
    with open(ap) as fh: assets = {k: v for k, v in json.load(fh).items() if k != 'note'}
    return lp, write_luau(report, assets, paint, lp)


# ---- THE KIT: the Roblox game's own models (tools/roblox/gun_models.py). they are built in their finished
# colours, so there is no paint table: a piece's code is its look in the file. their book is a second module,
# roblox/studio-tools/WeaponKit.luau (ServerStorage.PolishBackup.WeaponKit), read by WeaponImport's W.kit.
def kit_paths(report_path):
    import os
    d = os.path.dirname(os.path.abspath(report_path))
    return os.path.join(d, 'assets.json'), os.path.normpath(os.path.join(d, '..', '..', 'studio-tools', 'WeaponKit.luau'))


def write_kit(report, report_path):
    """the kit's book: every kit gun's asset id, bounds (they ride on the template as FileLo / FileHi, because a kit
       gun's box is not the web model's) and each piece's code"""
    import os
    ap, lp = kit_paths(report_path)
    if not (os.path.exists(ap) and os.path.isdir(os.path.dirname(lp))): return None
    with open(ap) as fh: assets = {k: v for k, v in json.load(fh).items() if k != 'note'}
    def vec(a): return 'Vector3.new(%s)' % ', '.join(repr(x) for x in a)
    out = ['--!nocheck',
           '-- GENERATED by tools/roblox/export_weapons.py --kit from roblox/assets/weapons-kit/export_report.json + assets.json.',
           '-- do not edit: change the builder in tools/roblox/gun_models.py and export again. read by',
           '-- PolishBackup.WeaponImport (W.kit, W.models). a code is "<kind><rrggbb>[aa]", see WeaponImport.',
           'return {',
           '	guns = {']
    n = 0
    for gun in sorted(report):
        m = report[gun]
        wid = gun[2:] if gun.startswith('w_') else gun
        if wid not in assets or not m.get('turned'): continue
        codes = ', '.join('["%s"] = "%s"' % (p['name'], web_code(p['look'])) for p in m['pieces'])
        out.append('		["%s"] = { id = %d, lo = %s, hi = %s, tris = %d, paint = { %s } },' % (wid, assets[wid], vec(m['lo']), vec(m['hi']), m['tris'], codes))
        n += 1
    out += ['	},', '}', '']
    with open(lp, 'w', newline=chr(10)) as fh: fh.write(chr(10).join(out))
    return lp, n


if __name__ == '__main__':
    argv = sys.argv[1:]
    paint = DEFAULT
    if '--paint' in argv:
        i = argv.index('--paint'); paint = argv[i + 1]; del argv[i:i + 2]
    path = argv[0]
    with open(path) as fh: rep = json.load(fh)
    unused = repaint(rep, paint)
    with open(path, 'w') as fh: json.dump(rep, fh, indent=1)
    print('painted', sum(1 for m in rep.values() if m.get('paint') == paint), 'guns with the', paint, 'paint')
    for g, k in unused: print('  TABLE LINE MATCHED NOTHING:', g, k)
    book = write_book(rep, path, paint)
    if book: print('wrote', book[0], '(%d guns, both paints, default %s)' % (book[1], paint))
