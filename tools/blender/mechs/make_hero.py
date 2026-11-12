# A Battle Island hero (docs/mechs/ROSTER.md) as a game file: the concept model on its joint tree, its markers and
# spray slots, the painted-metal look, the hero kit's stickers, every clip it defines (snap keys, events) keyed and
# exported. Each hero is a module next to this one with build() (a mechkit Mech), marks(mk) and clips().
#   blender52 -b -P tools/blender/mechs/make_hero.py -- hero=wreckingball [qa] [no-bake] [flat] [no-export] [out=<glb>]
#   -> public/models/x_mech_<hero>.glb (root meta jf: joints, marks, clips, decal_slots, palettes, height)
import os, sys, json, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mechkit import *
import make_mechs_rig as R
import clips as C

ARGS = dict(a.split('=', 1) if '=' in a else (a, '1') for a in (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []))


def main(hero):
    lib.reset(); lib._mats.clear()
    mod = importlib.import_module(hero)
    mk = mod.build(); mk.build_tree()
    marks = R.add_marks(mk, mod.marks(mk))  # (the spray slots' mk_spray_* markers come from meta['spray'])
    slots = mk.meta.pop('spray', [])
    look = None
    if 'flat' not in ARGS:  # (painted metal: the house look since 2026-11-12)
        import metalkit; look = metalkit.apply(mk, bake='no-bake' not in ARGS, skip=getattr(mod, 'PAPER', ()))
    if 'qa' in ARGS:
        sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts')); import qa_check
        res = qa_check.run(objects=[o.name for o in mk.root.children_recursive if o.type == 'MESH'], profile='game', eps=0.0008, tol=0.004)
        print('QA_PASS', hero, res['pass'], 'errors', len(res['errors'])); [print('QA_ERROR', e) for e in res['errors'][:40]]
    clip_list = mod.clips()
    R.key_clips(mk, mod, clip_list)
    meta = dict(mk.meta); meta.pop('marks', None)
    meta.update({'phase': 'concept rig (a Tripo mesh swaps in later)', 'fps': C.FPS, 'marks': marks, 'root_motion': False, 'decal_slots': slots,
                 'metal_look': look, 'clips': [R.clip_meta(cl) for cl in clip_list]})
    mk.root['jf'] = json.dumps(meta)
    print('JF_CLIPS', hero, len(clip_list), ' '.join(cl['name'] for cl in clip_list))
    print('JF_TRIS', hero, mk.tris())
    if 'no-export' not in ARGS:
        R.export(mk, ARGS.get('out', os.path.join(lib.MODELS, f'x_mech_{hero}.glb')), **({'export_vertex_color': 'ACTIVE'} if look and 'no-bake' not in ARGS else {}))
    return mk


main(ARGS.get('hero', 'wreckingball'))
