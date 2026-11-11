# Far LODs for round 1's props (the forklift, the school bus, the number balls): their scripts build lod0 exactly as
# before plus a `lod1` (a few hundred tris, the same paints), and main() here exports them so the close-up players
# already have stays the shipped one, byte for byte (lod_splice.py: Blender 4.0's booleans don't rebuild it exactly).
#   main(build, 'p_forklift')   flags after '--': --no-sheet, --no-export, --qa, --fresh (export the rebuild whole)
# Sheets: tools/blender/sheets/<id>_lod1.jpg (the far one; round 1's <id>.jpg still shows lod0, redone with --fresh).
import os, sys, tempfile, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh, bpy
import lib
from lib import gv, _obj
import lod_splice


def far_wheel(r, w, pos, tire, hub, seg=8, hub_k=0.42, out=None, name='far_wheel'):
    """an octagon tyre for a far LOD: the tread and the outer wall in `tire`, the hub disc in the middle of it in `hub`
    (one mesh, so nothing floats or fights). Its flats sit on r: the bottom one on the ground for a wheel at height r.
    No inner wall (it's inside the body). out = +1 / -1 which way along game z the outside is (default: away from 0).
    hub_k 0.42: round 1's wheels are a black disc with light spokes, about that much light from far away."""
    s = out or (1 if pos[2] >= 0 else -1)
    R = r / math.cos(math.pi / seg)
    bm = bmesh.new()
    def ring(rad, dz):
        return [bm.verts.new(gv(pos[0] + math.cos(2 * math.pi * (k + 0.5) / seg) * rad, pos[1] + math.sin(2 * math.pi * (k + 0.5) / seg) * rad, pos[2] + dz)) for k in range(seg)]
    a, b, c = ring(R, -s * w / 2), ring(R, s * w / 2), ring(R * hub_k, s * w / 2)
    faces = []
    for k in range(seg):
        k1 = (k + 1) % seg
        faces.append((bm.faces.new((a[k], a[k1], b[k1], b[k])), 0, None))  # tread
        faces.append((bm.faces.new((b[k], b[k1], c[k1], c[k])), 0, s))  # outer wall
    faces.append((bm.faces.new(c), 1, s))  # hub
    ctr, ax = gv(*pos), gv(0, 0, 1)
    for f, mi, side in faces:  # tread faces look out from the axle, the wall and hub out of the side
        f.material_index = mi
        f.normal_update()
        d = f.calc_center_median() - ctr
        want = (d - ax * d.dot(ax)) if side is None else ax * side
        if f.normal.dot(want) < 0: f.normal_flip()
    o = _obj(name, bm, tire)
    o.data.materials.append(hub)
    lib.smooth(o, 50)  # (a round tread, a sharp rim)
    return o


def attach_far(parent, parts, name='lod1'):
    """hang far-LOD parts under an empty named lod1 under parent (the game draws whatever is under it from far away),
    keeping where they are in the world"""
    bpy.context.view_layer.update()  # (fresh matrix_world for parts placed this session)
    e = lib._link(bpy.data.objects.new(name, None))
    e.parent = parent; e.matrix_parent_inverse = parent.matrix_world.inverted()
    for p in parts:
        lib.apply_mods(p)
        mw = p.matrix_world.copy(); p.parent = e; p.matrix_world = mw
    return e


def lods(root):
    far = [o for o in root.children_recursive if o.type == 'EMPTY' and lod_splice.FAR.match(o.name)]
    l1 = [o for e in far for o in e.children_recursive if o.type == 'MESH']
    l0 = [o for o in root.children_recursive if o.type == 'MESH' and o not in l1]
    return far, l0, l1


def qa(objs, tag, eps=0.001, tol=0.004):
    sys.path.insert(0, os.path.join(lib.ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    res = qa_check.run(objects=[o.name for o in objs], profile='game', eps=eps, tol=tol)
    print(f'QA_RESULT {tag} pass={res.get("pass")} errors={len(res.get("errors", []))} warnings={len(res.get("warnings", []))}')
    for k in ('errors', 'warnings'):
        for e in res.get(k, []): print('QA_' + k.upper()[:-1], tag, e)
    return res


def tris(objs):
    dg = bpy.context.evaluated_depsgraph_get(); t = 0
    for o in objs:
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); t += len(me.loop_triangles); o.evaluated_get(dg).to_mesh_clear()
    return t


def _move(objs, parent):  # re-parent keeping the world transform
    for o in objs:
        mw = o.matrix_world.copy(); o.parent = parent; o.matrix_world = mw


def main(build, file_id, **sheet_kw):
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    lib.reset()
    root = build()
    far, l0, l1 = lods(root)
    mats = lambda objs: sorted({s.material.name for o in objs for s in o.material_slots if s.material})
    print(f'JF_LODS {file_id}: lod0 {tris(l0)} tris {mats(l0)}, lod1 {tris(l1)} tris {mats(l1)}')
    if '--qa' in argv:
        qa(l0, file_id + ':lod0'); qa(l1, file_id + ':lod1', tol=0.01)
    if '--no-export' not in argv:
        shipped = os.path.join(lib.MODELS, file_id + '.glb')
        if '--fresh' in argv or not os.path.exists(shipped): lib.export(root, file_id)
        else:  # the rebuild goes to a temp folder; only its lod1 (and the root's metadata) goes into the shipped file
            keep, lib.MODELS = lib.MODELS, tempfile.mkdtemp(prefix='jf_farlod_')
            try: fresh = lib.export(root, file_id)
            finally: lib.MODELS = keep
            n, under = lod_splice.splice(shipped, fresh, shipped)
            print(f'JF_SPLICE {file_id}: lod0 kept as shipped, {n} lod1 under {sorted(set(under))}, {os.path.getsize(shipped) // 1024} KB')
            os.remove(fresh); os.rmdir(os.path.dirname(fresh))
    if '--no-sheet' not in argv:
        # the far one alone, under its own root so the label counts its tris. lod0's sheet only for a --fresh export
        # (kept as shipped, round 1's sheet still shows it: a rebuild's booleans can come out a bit different)
        homes = [(e, e.parent) for e in far]
        hold = lib._link(bpy.data.objects.new(file_id + '_lod1', None))
        _move(far, hold)
        if '--fresh' in argv or not os.path.exists(os.path.join(lib.SHEETS, file_id + '.jpg')):
            for o in l1: o.hide_render = True
            lib.sheet(root, file_id, **sheet_kw)
            for o in l1: o.hide_render = False
        for o in l0: o.hide_render = True
        lib.sheet(hold, file_id + '_lod1', **sheet_kw)
        for o in l0: o.hide_render = False
        for e, p in homes: _move([e], p)
        bpy.data.objects.remove(hold, do_unlink=True)
