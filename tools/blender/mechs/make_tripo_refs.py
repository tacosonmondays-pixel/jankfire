# Pictures for Tripo's image-to-3D (the owner makes the final mech meshes there): each mech's body from the front,
# left, back and right (orthographic, one scale for all four, an A-pose with the arms out so they don't fuse to the
# body, plain white, even light from a white world only, no gloss, no glow, no decals or text), without its moving
# parts, and each moving part on its own (PAPER PLANE's wing pair and crane drone, NIGHT SHIFT's sword and shield).
#   blender52 -b -P tools/blender/mechs/make_tripo_refs.py -- [mech=paperplane|nightshift] [spp=48] [res=1024]
# writes docs/mechs/tripo/<mech>_body_{front,left,back,right}.png and <mech>_<part>_{3q,flat}.png
import os, sys, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mechkit import *

ARGS = dict(a.split('=', 1) if '=' in a else (a, '1') for a in (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []))
OUT = os.path.join(ROOT, 'docs', 'mechs', 'tripo')
SPP, RES = int(ARGS.get('spp', 48)), int(ARGS.get('res', 1024))
BACKDROP = 0xc9ced6  # light neutral grey (exposure lifts it a little)
PARTS = {'paperplane': {'wings': ['wing_L', 'wing_R'], 'drone': ['drone']}, 'nightshift': {'sword': ['sword'], 'shield': ['shield']}}
r = math.radians
APOSE = {'upperarm_R': (0, 0, r(32)), 'upperarm_L': (0, 0, r(-32)), 'forearm_R': (0, 0, r(6)), 'forearm_L': (0, 0, r(-6)),
         'thigh_R': (0, 0, r(5)), 'thigh_L': (0, 0, r(-5)), 'foot_R': (0, 0, r(-5)), 'foot_L': (0, 0, r(5))}


def matte(mats):
    """no clear coat, no mirror metal, glows off: the picture shows shape and paint, nothing Tripo would bake in as a highlight"""
    for m in bpy.data.materials:
        if not m.use_nodes or m.name.startswith('jf_'): continue
        b = m.node_tree.nodes.get('Principled BSDF')
        if not b: continue
        b.inputs['Coat Weight'].default_value = 0.0
        b.inputs['Roughness'].default_value = max(0.55, b.inputs['Roughness'].default_value)
        b.inputs['Metallic'].default_value = min(0.25, b.inputs['Metallic'].default_value)
        b.inputs['Emission Strength'].default_value = 0.0


def white_world():
    """even white light from every side, but a light grey backdrop behind the model (white plates would vanish on white)"""
    sc = bpy.context.scene
    w = bpy.data.worlds.new('jf_white'); sc.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes['Background']; bg.inputs['Color'].default_value = (1, 1, 1, 1); bg.inputs['Strength'].default_value = 1.0
    bg2 = nt.nodes.new('ShaderNodeBackground'); bg2.inputs['Color'].default_value = srgb(BACKDROP); bg2.inputs['Strength'].default_value = 1.0
    lp = nt.nodes.new('ShaderNodeLightPath'); mix = nt.nodes.new('ShaderNodeMixShader'); out = nt.nodes['World Output']
    nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs[0]); nt.links.new(bg.outputs[0], mix.inputs[1]); nt.links.new(bg2.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = 0.25
    sc.render.film_transparent = False


def subtree(mk, names):
    out = set()
    for n in names:
        e = mk.E[n]; out.add(e); out.update(e.children_recursive)
    return [o for o in out if o.type == 'MESH']


def bbox(objs):
    lo = V((1e9,) * 3); hi = V((-1e9,) * 3)
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ V(c); lo = V(map(min, lo, w)); hi = V(map(max, hi, w))
    return lo, hi  # blender coords


def cam_up(loc_b, target_b, up_b, ortho=None, lens=50):
    """a camera at blender point loc looking at target with a chosen up (so a sword can stand up in the picture)"""
    cam = camera((0, 0, 0), (0, 0, 1), lens, ortho)
    f = (target_b - loc_b).normalized(); rgt = f.cross(up_b).normalized(); u = rgt.cross(f)
    M3 = Matrix((rgt, u, -f)).transposed()
    cam.matrix_world = Matrix.Translation(loc_b) @ M3.to_4x4()
    return cam


def shoot(name):
    p = os.path.join(OUT, name + '.png'); render(p); print('JF_REF', os.path.relpath(p, ROOT)); return p


def main(which):
    lib.reset(); lib._mats.clear()
    mod = importlib.import_module(which); mod.DECALS = False
    mk = mod.build(); mk.build_tree()
    os.makedirs(OUT, exist_ok=True)
    matte(mk.M); white_world()
    cycles(SPP, (RES, RES)); clear_set(); white_world()
    parts = PARTS[which]; moving = {k: subtree(mk, v) for k, v in parts.items()}
    every = [o for o in mk.root.children_recursive if o.type == 'MESH']
    hide_all = lambda keep: [setattr(o, 'hide_render', o not in keep) for o in every]
    # the body: A-pose, moving parts hidden, four orthographic sides at one scale
    mk.pose(APOSE)
    gone = set(o for v in moving.values() for o in v)
    body = [o for o in every if o not in gone]
    hide_all(set(body))
    lo, hi = bbox(body); c = (lo + hi) / 2; size = max(hi.z - lo.z, hi.x - lo.x, hi.y - lo.y) * 1.12
    for v, d in (('front', V((0, 1, 0))), ('left', V((-1, 0, 0))), ('back', V((0, -1, 0))), ('right', V((1, 0, 0)))):
        # (blender +y = game -z = the way the mech faces: 'front' looks at its face; 'left' = from its left side)
        cam_up(c + d * 60, c, V((0, 0, 1)), ortho=size)
        shoot(f'{which}_body_{v}')
    # the moving parts, each on its own: a 3/4 view and a flat one
    mk.pose({})
    for k, objs in moving.items():
        hide_all(set(objs)); lo, hi = bbox(objs); c = (lo + hi) / 2; ext = (hi - lo).length
        if which == 'nightshift' and k == 'sword':
            G, d = V(gv(*mod.JT['sword'])), V(gv(*mod.GRIP)).normalized()  # blade up, looking at a flat
            w = d.cross(V(gv(1, 0, 0))).normalized()  # edge to edge (as in nightshift.sword)
            flat_dir = d.cross(w).normalized()  # a flat's normal: look straight at the broad side
            cam_up(c + flat_dir * 40, c, d, ortho=ext * 1.08); shoot(f'{which}_{k}_flat')
            cam_up(c + (flat_dir * 0.85 + w * 0.5).normalized() * ext * 1.9, c, d, lens=50); shoot(f'{which}_{k}_3q')
        elif which == 'nightshift' and k == 'shield':
            n = V(gv(-1, 0, 0))  # the shield's face looks out of the arm (-x at rest)
            cam_up(c + n * 40, c, V((0, 0, 1)), ortho=ext * 0.95); shoot(f'{which}_{k}_flat')
            cam_up(c + (n * 0.75 + V(gv(0, 0, -1)) * 0.55 + V((0, 0, 0.25))).normalized() * ext * 1.9, c, V((0, 0, 1)), lens=50); shoot(f'{which}_{k}_3q')
        else:  # the wing pair (stowed V) and the crane: from behind (their top faces) and a 3/4
            back = V(gv(0, 0, 1))
            cam_up(c + back * 40, c, V((0, 0, 1)), ortho=ext * 0.9); shoot(f'{which}_{k}_flat')
            cam_up(c + (back * 0.8 + V(gv(-1, 0, 0)) * 0.5 + V((0, 0, 0.35))).normalized() * ext * 1.8, c, V((0, 0, 1)), lens=50); shoot(f'{which}_{k}_3q')
    clear_set()


if __name__ == '__main__':
    for m in ([ARGS['mech']] if 'mech' in ARGS else ['paperplane', 'nightshift']): main(m)
