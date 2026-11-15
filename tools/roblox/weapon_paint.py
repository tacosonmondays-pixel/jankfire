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
STEEL = 's868b95'      # mid steel (was bright chrome)
STEEL_D = 'm3a3d45'    # dark steel
POLY = 'p1e2024'       # black polymer
RUBBER = 'r1d1e21'     # black rubber / grip
BRASS = 'sb08d45'      # muted brass (was shiny gold)
SHELL = 'pb3312c'      # shotgun hulls: the one red left
WALNUT = 'w4a3222'

CALM = {
 # Assault Rifle: olive furniture on gunmetal, a smoked magazine
 'w_ar': {
  'ar_olive': 'p4c5639', 'ar_grip': 'r3e472f', 'ar_tape': 'p343c28', 'ar_neon': 'p1b1c20', 'ar_sticker': 'm2c3036',
  'ar_charm': STEEL_D, 'ar_mag': 'g2b2e34b8', 'ar_magbase': POLY, 'ar_white': 'pc8c8c8',
 },
 # Plan B: black frame, steel slide, anodised blue controls
 'w_pistol': {
  'pb_frame': POLY, 'pb_pearl': 'r2a2c31', 'pb_satin': 's7d838d', 'pb_polish': STEEL, 'pb_rib': 'm4a4e57',
  'pb_roll_r': 's7d838d', 'pb_roll_l': 's7d838d', 'pb_tin': STEEL_D, 'pb_gold': 's5676cf', 'pb_medal': 'sb08d45+',
 },
 # Revolver: stainless, a black grip, brass controls, the orange front sight
 'w_revolver': {
  'rv_pearl': RUBBER, 'rv_satin': 's6c717b', 'rv_chrome': 's838892', 'rv_gold': BRASS,
 },
 # Shotgun: blued steel and dark walnut, red shells
 'w_shotgun': {
  'sg_forend': WALNUT, 'sg_walnut': WALNUT, 'sg_hull': SHELL,
 },
 # Half a Shotgun: cherry wood, a steel receiver, red shells
 'w_sawnoff': {
  'so_candy': 'w5c3324', 'so_case': 's4d525d', 'so_screw': STEEL, 'so_dash': 'm232c40', 'so_sticker': 's4d525d',
  'so_hull': SHELL, 'so_cut': 's9aa0aa', 'so_endgrain': 'w6e4a33', 'so_tape': 'p1d1d21',
 },
 # Sniper: a tan stock on black steel, the violet lens
 'w_sniper': {
  'sn_pink': 'p8f8268', 'sn_sticker': 'p8f8268', 'sn_gold': STEEL_D, 'sn_bolt': STEEL, 'sn_white': 'pc8c8c8',
 },
 # Second Opinion: dusk violet furniture (toned down), the medic cross stays
 'w_dmr': {
  'dm_wood': 'p474262', 'dm_bandaid': 'p474262', 'dm_tubing': 'p7d6fc4', 'dm_chrome': STEEL, 'dm_diaphragm': STEEL,
 },
 # Hat Trick: slate blue body, blue controls
 'w_burst': {
  'burst_body_wzA__bu_blue': 'p2f3a4d', 'mag_wzA__bu_blue': 'p2f3a4d', 'bu_navy': 'p252b3a', 'bu_yellow': 'p3f6fc9',
  'bu_bread': RUBBER, 'bu_crumb': RUBBER, 'bu_tape': 'p3a3d44', 'bu_chrome': STEEL,
 },
 # Belt Sander: graphite body, an orange feed cover and switches, a black cable
 'w_lmg': {
  'lmg_body_wzA__lmg_orange': 'p34373d', 'lmg_body_wzB__lmg_orange': 'p34373d', 'cover_wzA__lmg_orange': 'pd2622a',
  'lmg_grit': 'r6b4636', 'lmg_cord': RUBBER, 'lmg_yellow': 'pd2622a', 'lmg_tag': 'p333e29', 'lmg_chrome': STEEL,
 },
 # Lawn Mower: machine green furniture (toned down), the red pull-start
 'w_autoshot': {
  'as_green': 'p41674a', 'as_grass': 'p365a3e', 'as_red': SHELL, 'as_hazard': 'm26282d', 'as_keep': 'p41674a',
  'as_mow': 'm121316', 'as_cord': 'p8e8e8e', 'as_chrome': STEEL,
 },
 # Yeehaw: saddle walnut, a steel receiver, brass trim
 'w_lever': {
  'lv_leather': 'r3a2a22', 'lv_case': 's666b76', 'lv_pink': 'r3a2a22', 'lv_gem_w': BRASS, 'lv_gem': BRASS,
  'lv_gold': BRASS, 'lv_forend': 'w573823', 'lv_walnut': 'w573823', 'lv_rope': 'r85765a',
 },
 # Redline: black with its red (touch-ups: the grip and the tape lose their pictures, chrome goes to steel)
 'w_redline': {
  'rl_grip': 'r2b2623', 'rl_tape': 'pa8322c', 'rl_chrome': STEEL, 'rl_red': 'pc22a2a', 'rl_white': 'pd0d0d0',
 },
 # Marble Shotgun: antique brass and walnut; the marbles stay bright (they are the ammunition)
 'w_marbles': {
  'mb_brass': 's9a7a3e', 'mb_walnut': WALNUT, 'mb_plaque': 's9a7a3e', 'mb_zinc': STEEL, 'mb_ramrod': 'w6e4a33',
  'mb_label': 'pb9b3a6',
 },
 # Katana: as it is, the gold a little older
 'w_katana': {
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
