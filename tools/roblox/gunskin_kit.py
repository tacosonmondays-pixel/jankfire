# THE WEAPON SKINS' shared start (the web game's skins as Roblox kit models, 16 Nov 2026). Builders live in
# gun_skins_1.py .. gun_skins_3.py; tools/roblox/gun_set.py collects their SKINS into the live set's SKINS.
#   blender -b --factory-startup -P tools/roblox/gun_set.py -- <out_dir> ar@ar_toy        (build)
#   blender -b --factory-startup -P tools/roblox/gun_preview.py -- <out_dir> --set live ar@ar_toy   (look)
#   blender -b --factory-startup -P tools/roblox/gun_check.py -- skins                    (one piece each, moving nodes)
#
# A SKIN IS A WHOLE OTHER BODY FOR ONE LIVE GUN, and it keeps that gun's CONTRACT with the game:
#   - the spots (muzzle, sight, port, grip, fore) are the gun's own (skin() copies them): the flash, the aim line, the
#     brass and the hands come from them. The grip piece sits ON the grip spot with the gun's rake, the fore piece's
#     underside on the fore spot (the off hand holds there); the aim line runs over the top to the muzzle's end.
#   - the nodes the game moves keep their names and sit where the moving makes sense, at about the base gun's place:
#     mag (drops straight down from its pivot and comes back), charge, pump (slides back along the tube), bolt (lifts
#     about the bore and slides back), lever, lhammer, slide (back), hammer / hammerL / hammerR (tip about x),
#     cylinder (turns 60 degrees a shot about the z axis through the row's pivot: six-fold symmetric round that axis),
#     hinge group (Half a Shotgun: hinge, hinge_trim, forend, forend_iron, shell1, shell2 tip down about the pin),
#     cover (the Belt Sander's feed cover), belt_00..belt_11 (one link each: the game hides them as ammo runs down),
#     lmg_heat (glows with heat), needle (the Redline's tachometer needle: turns about its pivot), redline_vents (glow),
#     kat_blade / kat_guard / kat_tsuka / kat_trims (the katana: kat_blade stretches with kills).
#     Where the skin's object has no such part, leave the node out: nothing moves (better than a part moving wrongly).
#   - about the gun's size (within ~10% of the base gun's bounds; gun_set prints both).
#   - wrap zones in the piece names: _wzA = the big shell a wrap paints (every skin needs some), _wzB = dark / metal,
#     _wzN = trims. Slots: one name per colour (body, frame, dark, black, accent, glow (Neon), ...).
# THE LOOK (look C, gunkit_c.py): boxes with one clean, fairly wide chamfer; tubes 8-sided and shaded round; chunky,
# nothing thinner than ~12 mm sticking out; 2 or 3 flat colours plus at most one small glow; the theme carried by the
# silhouette (the web skin's idea), not by pictures. Colours a step calmer and darker than the web skins (the hall's
# lamps push colour). NO readable text, numbers, logos, codes, QR- or barcode-like patterns anywhere (Roblox rules):
# a calculator's keys are plain blocks, a label maker's tape is blank.
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gunkit_c import *   # (look C, the shared pieces, Gun, A = gun_models)
import gunkit


def skin(wid, skinid):
    """a fresh Gun for the skin "<wid>@<skinid>": its file name, look C, and the live gun's spots. returns (g, base)
       where base is the live gun (gun_set.BUILD[wid]()) to read sizes and pivots from"""
    import gun_set  # (here, not at the top: gun_set imports the skin files)
    base = gun_set.BUILD[wid]()
    gunkit.use_style('C')
    g = Gun('w_%s@%s' % (wid, skinid))
    g.spots = dict(base.spots)
    return g, base
