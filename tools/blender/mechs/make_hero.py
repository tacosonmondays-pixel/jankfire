# A Battle Island hero (docs/mechs/ROSTER.md) as a game file: the concept model on its joint tree, its markers and
# spray slots, the painted-metal look, the hero kit's stickers, every clip it defines (snap keys, events) keyed and
# exported. Each hero is a module next to this one with build() (a mechkit Mech), marks(mk) and clips().
#   blender52 -b -P tools/blender/mechs/make_hero.py -- hero=wrecking [qa] [no-bake] [no-merge] [no-skin] [flat] [no-export] [no-lod] [out=<glb>]
#   -> public/models/x_mech_<hero>.glb (root meta jf: joints, marks, clips, decal_slots, palettes, height, lod)
# The near model and a far LOD (<joint>_lod1, built with mechkit.LO: see make_mechs_rig.build_lod) in one file.
import os, sys, json, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mechkit import *
import make_mechs_rig as R
import clips as C

LOD_DIST = 26  # metres (Mid; mechlook scales it per preset)
ARGS = dict(a.split('=', 1) if '=' in a else (a, '1') for a in (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []))


def main(hero):
    lib.reset(); lib._mats.clear()
    mod = importlib.import_module(hero)
    mk = R.build_lod(mod, far='no-lod' not in ARGS)
    far = list(mk.lods.values()); near = [o for o in mk.root.children_recursive if o.type == 'MESH' and o not in far]
    marks = R.add_marks(mk, mod.marks(mk))  # (the spray slots' mk_spray_* markers come from meta['spray'])
    slots = mk.meta.pop('spray', [])
    look = None
    if 'flat' not in ARGS:  # (painted metal: the house look since 2026-11-12)
        import metalkit; look = metalkit.apply(mk, bake='no-bake' not in ARGS, skip=getattr(mod, 'PAPER', ()))
        if 'no-merge' not in ARGS and 'no-bake' not in ARGS:  # (the draw-call pass: one trim material for the flat paints)
            merged = metalkit.merge_trim(mk); print('JF_TRIM', hero, 'merged', ' '.join(merged['trim']), '| kept', ' '.join(merged['kept']))
    if 'qa' in ARGS:
        sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts')); import qa_check
        for lab, objs in (('near', near), ('far', far)):  # (apart: the two overlap by design)
            if not objs: continue
            res = qa_check.run(objects=[o.name for o in objs], profile='game', eps=0.0008, tol=0.004)
            print('QA_PASS', hero, lab, res['pass'], 'errors', len(res['errors'])); [print('QA_ERROR', lab, e) for e in res['errors'][:40]]
    clip_list = mod.clips()
    R.key_clips(mk, mod, clip_list)
    meta = dict(mk.meta); meta.pop('marks', None)
    tn, tf = R.tris_of(near), R.tris_of(far)
    meta.update({'phase': 'concept rig (a Tripo mesh swaps in later)', 'fps': C.FPS, 'marks': marks, 'root_motion': False, 'decal_slots': slots,
                 'metal_look': look, 'clips': [R.clip_meta(cl) for cl in clip_list]})
    if far: meta['lod'] = {'far': '_lod1', 'dist': LOD_DIST, 'tris': [tn, tf]}  # (the game swaps <joint>_mesh for <joint>_lod1 past dist metres)
    mk.root['jf'] = json.dumps(meta)
    print('JF_CLIPS', hero, len(clip_list), ' '.join(cl['name'] for cl in clip_list))
    print('JF_TRIS', hero, 'near', tn, 'far', tf)
    if 'no-export' not in ARGS:
        path = ARGS.get('out', os.path.join(lib.MODELS, f'x_mech_{hero}.glb'))
        R.export(mk, path, **({'export_vertex_color': 'ACTIVE'} if look and 'no-bake' not in ARGS else {}))
        if getattr(mod, 'SKIN', False) and 'no-skin' not in ARGS:  # (one rigid-skinned mesh per LOD: a handful of draws, not one per joint per material)
            import skin_glb; skin_glb.main(path, path, mk.prefix)
    return mk


main(ARGS.get('hero', 'wrecking'))
