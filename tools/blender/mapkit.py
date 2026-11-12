# Map-prop kit on top of rpkit.py (Blender 5.2): shapes the Suburb props share (rounded toy boxes, chamfered blocks,
# lathes, sheets that hug a surface), and the finish every one of them gets: baked AO x tint into COLOR_0, lod0 under the
# root and the far copy under `lod1` (shared/propcap.js + public/js/propfield.js), the asset-QA gate, the compact glb,
# and a studio sheet. Everything in GAME coordinates (x right, y up, front -z), like lib.py.
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rpkit import *  # noqa
from rpkit import _link
import lib


def rbox(hx, hy, hz, k=24, rows=10, n=3.2, nv=None, y_lo=-1.0, y_hi=1.0):
    """a rounded toy box (superellipse in plan and in height), centred, poles on y; y_lo / y_hi cut it flat"""
    nv = nv or n; R = []
    for i in range(rows + 1):
        t = lerp(y_lo, y_hi, i / rows)
        s = max(1e-3, (1 - abs(t) ** nv) ** (1 / nv)) if abs(t) < 1 else 1e-3
        R.append(superring(t * hy, hx * s, hz * s, k, n))
    return p_loft(R, cap0=y_lo > -1, cap1=y_hi < 1, tip0=None if y_lo > -1 else V3((0, -hy, 0)), tip1=None if y_hi < 1 else V3((0, hy, 0)))


def cbox(x0, y0, z0, x1, y1, z1, ch=0.02, bottom=False, chb=0.0):
    """a block with its top edges chamfered by ch (and its bottom ones by chb)"""
    def rect(y, d): return [V3((x0 + d, y, z0 + d)), V3((x1 - d, y, z0 + d)), V3((x1 - d, y, z1 - d)), V3((x0 + d, y, z1 - d))]
    R = ([rect(y0, chb), rect(y0 + chb, 0)] if chb else [rect(y0, 0)]) + [rect(y1 - ch, 0), rect(y1, ch)]
    return orient_from(p_loft(R, cap0=bottom, cap1=True), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def lathe_p(profile, k=20):
    """(r, y) profile turned round y. Go out along the bottom, up, and back in along the top: the faces look out.
    r = 0 at either end closes it with a point"""
    tips = [V3((0, profile[i][1], 0)) if profile[i][0] < 1e-6 else None for i in (0, -1)]
    R = [[V3((math.sin(2 * math.pi * j / k) * r, y, math.cos(2 * math.pi * j / k) * r)) for j in range(k)] for r, y in profile if r > 1e-6]
    return p_loft(R, tip0=tips[0], tip1=tips[1])


def sheet_rows(rows, flip=True):
    """a sheet through rows of game points (each row left to right, rows bottom to top): it faces -z when flip"""
    return p_grid([[V3(p) for p in r] for r in rows], flip=flip)


def tube_ring(c, r, rt, k=16, kt=6, axis='z'):
    """a closed ring (a steering wheel, a monocle) of radius r round c, tube radius rt, in the plane facing axis"""
    pts = []
    for j in range(k + 1):
        a = 2 * math.pi * j / k; u, v = math.cos(a) * r, math.sin(a) * r
        pts.append(V3(c) + (V3((u, v, 0)) if axis == 'z' else V3((0, v, u)) if axis == 'x' else V3((u, 0, v))))
    return p_tube(pts, rt, k=kt)


def finish_prop(fid, lods, meta, ao=(0.45, 0.6), qa_on=False, out_dir=None):
    """lods = {'lod0': [Buf...], 'lod1': [Buf...]} -> baked, joined under the root, QA'd, exported (compact). -> root, objs"""
    out = {}
    for lod, bufs in lods.items():
        out[lod] = [b.obj(sharp=40) for b in bufs if b.F]
    for i, lod in enumerate(('lod0', 'lod1')):
        bake_ao(out[lod], dist=ao[i], samples=24, lo=0.42)
        for o in out[lod]: final_colour(o)
    meta = dict(meta); meta.setdefault('kind', 'prop')
    meta['tris'] = sum(tri_count(o) for o in out['lod0']); meta['tris_lod1'] = sum(tri_count(o) for o in out['lod1'])
    root = lib.prop_finish(fid, out['lod0'], out['lod1'], meta)
    lo, hi = bounds(out['lod0'])
    print('JF_TRIS', fid, 'lod0', meta['tris'], 'lod1', meta['tris_lod1'], 'mats', sorted({m.name for o in out['lod0'] for m in o.data.materials}), 'bounds', r3(lo), r3(hi))
    res = None
    if qa_on:
        res = [qa(fid + ' lod0', out['lod0'], eps=0.0005, tol=0.004), qa(fid + ' lod1', out['lod1'], eps=0.0005, tol=0.004)]
    if out_dir is not False:
        d = out_dir or MODELS; path = os.path.join(d, fid + '.glb'); tmp = os.path.join(d, '_tmp_' + fid + '.glb')
        compact_glb(export_glb(root, tmp)); os.replace(tmp, path)
        print('JF_OUT', path, os.path.getsize(path) // 1024, 'KB')
    return root, out


def studio(sky=0xffd3ec, floor=0x6abf4a):
    clear_studio(); world(sky, 0.55)
    area(2600, (-8, 12, -14), (0, 3, 0), 10, (1.0, 0.95, 0.9))
    area(900, (12, 6, 6), (0, 3, 0), 8, (0.85, 0.9, 1.0))
    area(500, (0, 4, 14), (0, 3, 0), 6, (1.0, 0.8, 0.9))
    lib.box((120, 0.02, 120), pos=(0, -0.012, 0), m=mat('pv_floor', floor, rough=0.9), name='jf_set_floor')


def sheet_set(fid, prefix, out, groups, scale=1.0):
    """groups = [(name, [(caption, cam, target, lens)], cols, label, res, show_lod1)] -> tools/blender/sheets/<fid>[_name].jpg"""
    colour_preview([m for m in bpy.data.materials if m.name.startswith(prefix)], True)
    tmp = os.path.join(SHEETS, '_tmp_' + fid); os.makedirs(tmp, exist_ok=True)
    for name, views, cols, label, res, show1 in groups:
        for o in out['lod0']: o.hide_render = show1
        for o in out['lod1']: o.hide_render = not show1
        paths, labels = [], []
        for k, (cap, cam, tg, lens) in enumerate(views):
            p_ = os.path.join(tmp, '%s_%d.png' % (name, k)); shot(p_, cam, tg, lens=lens, res=res, samples=16); paths.append(p_); labels.append(cap)
        contact(paths, os.path.join(SHEETS, fid + ('' if name == 'sheet' else '_' + name)), label, cols=cols, labels=labels)
    for o in out['lod0'] + out['lod1']: o.hide_render = False
    try: os.rmdir(tmp)
    except OSError: pass
