# MADAM CHAIR and her hat OVERSIGHT (working id hat_lord; OVERDUE's lord of the Gut: docs/story/cast/HAT_LORD.md).
# The owner's sketch (docs/story/cast_refs/hat_lord_owner_sketch.jpg): an enormous tilted brim, a round crown ringed
# by a thick band with growths bunched on it, a feeler at the low tip; under it a long wedge of a head with bands
# across where the eyes would be; a hard bar of shoulder; thin arms held out, long fingers down; a long taper to the
# floor. Read as: a narrow woman, 2.9 m to the top of her head, in a stiff coat worn on the shoulders (its yoke is the
# bar), and a hat that is an animal made of the rest of her board. Her eyes are on the hat.
#
#   public/models/cast/c_hat_lord.glb          part_<joint>[__<tag>] like every cast model, on the cast skeleton plus
#                                              her own joints (public/js/story/hatlook.js EXTRA); a far LOD per joint
#   public/models/cast/c_hat_lord.parts.json   every named part (joint, box), markers (her eye pair, the hat's weak
#                                              points, hands, the socket), the joints and their rest
#
# the woman: hatbody.py · the hat: hathat.py · the kit: hatkit.py · her clips: hl_clips.py · pose sheets: hatposes.py
# blender52 -b --python tools/blender/cast/make_cast_hat_lord.py [-- flags]
#   --no-export --no-ao --no-sheet --qa --stats --pieces --quick
#   --sheet=turn,sil,close,scale,poses,clips   (default: turn,sil,close)   --clip=hl_idle   --out=<dir>
import os, sys, math, json, time
T0 = time.time()
def lap(k): print('JF_LAP %-10s %6.1fs' % (k, time.time() - T0))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hatkit import *  # noqa
import hatbody, hathat

OUT_GLB = os.path.join(MODELS, 'cast', 'c_hat_lord.glb')
OUT_PARTS = os.path.join(MODELS, 'cast', 'c_hat_lord.parts.json')
SHEET_DIR = arg('out') or SHEETS
TMP = os.path.join(SHEETS, '_tmp_hl')
SKETCH = os.path.join(ROOT, 'docs', 'story', 'cast_refs', 'hat_lord_owner_sketch.jpg')
FAR_SKIP = ('socket', 'clasps', 'herLid', 'hatLid', 'herOrbit', 'bands')
# how she stands (the sketch): arms out from narrow shoulders and clear of the cape, forearms dropping to hands held
# just outside its corners, fingers down. hl_clips.py REST is the same numbers; the glb itself is at the skeleton's rest (arms hanging)
STANCE = {'arm.z': 1.0, 'armL.z': -1.0, 'arm.x': 0.04, 'armL.x': 0.04, 'foreR.z': -0.62, 'foreL.z': 0.62, 'foreR.x': 0.08, 'foreL.x': 0.08, 'handR.z': -0.38, 'handL.z': 0.38}
RIG = {}


def build():
    H = hatbody.Chair()
    hatbody.materials(H); lap('materials')
    for fn in (hatbody.head, hatbody.torso, hatbody.legs, hatbody.arms, hatbody.coat, hathat.brim, hathat.crown, hathat.neck, hathat.her_eyes, hathat.creature_eyes, hathat.growths, hathat.bands):
        fn(H); lap(fn.__name__)
    meta = {'face': True, 'parts': sorted(H.P.info), 'joints': JD['order']}
    if arg('pieces'):
        for (k, nm), n in sorted(H.P.tris.items(), key=lambda e: -e[1])[:int(arg('pieces')) if str(arg('pieces')).isdigit() else 60]: print('   JF_PIECE %-22s %-18s %5d' % (k, nm, n))
    if not arg('no-lod'): hatbody.coat(H, lod=True); hathat.brim(H, lod=True); hatbody.head(H, lod=True); hatbody.torso(H, lod=True)   # (thin shells get a far version built coarse; a decimate would fold them)
    root = H.P.root(meta); lap('join')
    return H, root


LOD_JOINTS = ('body', 'legL', 'legR', 'kneeL', 'kneeR', 'spine', 'neck', 'head', 'arm', 'armL', 'foreL', 'foreR', 'handL', 'handR', 'hat', 'crown', 'growthA', 'growthB', 'growthC', 'feeler')
LOD_TAGS = ('', 'yoke')


def islands_drop(o, small=None, verts_under=0):
    """take out loose islands: small(verts, size) -> True, or fewer than verts_under vertices"""
    bm = bmesh.new(); bm.from_mesh(o.data); seen = set(); kill = []
    for v in bm.verts:
        if v in seen: continue
        isl = [v]; seen.add(v); st = [v]
        while st:
            x = st.pop()
            for e in x.link_edges:
                y = e.other_vert(x)
                if y not in seen: seen.add(y); isl.append(y); st.append(y)
        lo = Vector((min(w.co.x for w in isl), min(w.co.y for w in isl), min(w.co.z for w in isl))); hi = Vector((max(w.co.x for w in isl), max(w.co.y for w in isl), max(w.co.z for w in isl)))
        if len(isl) < verts_under or (small and small(len(isl), (hi - lo).length)): kill += isl
    if kill: bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bm.to_mesh(o.data); bm.free(); o.data.update()


def add_far_hl(root, ratio=0.16):
    """the far model (past 30 m): each of the big joints' solid shapes decimated, trim and teeth and fingers left off.
    the cape and the brim are already there, built coarse"""
    out = []
    for jn in LOD_JOINTS:
        src = [o for o in root.children if o.type == 'MESH' and joint_of(o) == jn and tag_of(o) in LOD_TAGS]
        if not src: continue
        cs = []
        for o in src:
            c = o.copy(); c.data = o.data.copy(); bpy.context.scene.collection.objects.link(c); c.data.transform(o.matrix_world); c.matrix_world = Matrix.Identity(4); c.parent = None; cs.append(c)
        o = join(cs, 'part_%s__lod' % jn)
        islands_drop(o, small=lambda n, size: (n < 70 and size < 0.3) or size < 0.07)
        me = o.data; me.calc_loop_triangles(); n = len(me.loop_triangles)
        if n == 0: bpy.data.objects.remove(o, do_unlink=True); continue
        if n > 40:
            d = o.modifiers.new('dec', 'DECIMATE'); d.ratio = max(ratio, min(1.0, 40 / n)); apply_mods(o)
            bm = bmesh.new(); bm.from_mesh(o.data)
            bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges)
            loose = [v for v in bm.verts if not v.link_faces]
            if loose: bmesh.ops.delete(bm, geom=loose, context='VERTS')
            bm.to_mesh(o.data); bm.free()
            drop_flakes(o, 6e-6); islands_drop(o, verts_under=10); outward(o)
        o.parent = root; o.hide_render = True; out.append(o)
    return out


def base_parts(root): return [o for o in root.children if o.type == 'MESH' and '__lod' not in o.name]
def joint_of(o): return o.name[len('part_'):].split('__')[0].rstrip('0123456789.')
def tag_of(o): return (o.name[len('part_'):].split('__') + [''])[1].rstrip('0123456789.')


def bake(H, root):
    allp = [o for o in root.children if o.type == 'MESH']
    for o in allp: o.hide_render = False
    rpkit.bake_ao(allp, dist=0.25, samples=12, lo=0.55)


def stats(root):
    rows = tri_report(root)
    b = sum(n for nm, n in rows if '__lod' not in nm); l = sum(n for nm, n in rows if '__lod' in nm)
    hat = sum(n for nm, n in rows if '__lod' not in nm and nm[len('part_'):].split('__')[0].rstrip('0123456789.') not in STD)
    print('JF_TRIS model %d (the hat, its hands and her fingers %d) | far LOD %d | total in file %d' % (b, hat, l, b + l))
    if arg('stats'):
        for nm, n in sorted(rows, key=lambda r: -r[1]): print('   %-34s %6d' % (nm, n))
    return b, l


def parts_json(H, root):
    def r4(v): return [round(float(x), 4) for x in v]
    parts = {}
    for o in root.children:
        if o.type != 'MESH' or '__lod' in o.name: continue
        t = tag_of(o) or ('_' + joint_of(o))
        lo, hi = rpkit.bounds([o])
        e = parts.setdefault(t, dict(joint=joint_of(o), c=None, h=None))
        if e['c'] is not None: lo = Vector(map(min, lo, Vector(e['_lo']))); hi = Vector(map(max, hi, Vector(e['_hi'])))
        e['_lo'], e['_hi'] = tuple(lo), tuple(hi); e['c'] = r4((lo + hi) / 2); e['h'] = r4((hi - lo) / 2)
    named = {}
    for t, e in parts.items():
        e.pop('_lo', None); e.pop('_hi', None)
        if t.startswith('_'): continue
        inf = H.P.info.get(t, {})
        if inf.get('note'): e['note'] = inf['note']
        named[t] = e
    markers = {k: dict(joint=j, local=r4(p), at=r4(to_root(j, p))) for k, (j, p) in H.marks.items()}
    allb = rpkit.bounds(base_parts(root)); bodyb = rpkit.bounds([o for o in base_parts(root) if joint_of(o) in STD])
    joints = {n: dict(parent=JD['parents'][n], p=JD['local'][n]['p'], r=JD['local'][n]['r'], at=r4(JP[n]), own=n not in STD) for n in JD['order']}
    look = dict(eyes=['eyeHR', 'eyeHL'], lids=['lidHR', 'lidHL'], at='eyeAt', aim=['hat', 'hatNeck'], note='her eyes are on the hat: aim the hat (and turn eyeH*) at what she looks at; her face stays level')
    hit = dict(head=dict(joint='head', c=r4(to_root('head', (0, 0.3, -0.01))), h=[0.17, 0.31, 0.18]),
               hat=dict(joint='hat', c=r4(to_root('hat', (0.02, 0.2, 0))), h=[0.34, 0.2, 0.33]),
               weak=[k for k in sorted(markers) if k.startswith('weak')], her_eyes=['eyeHRAt', 'eyeHLAt'], hands=['palmR', 'palmL'], socket='socketAt')
    return dict(v=1, model='c_hat_lord.glb', scale=JD['scale'], units='metres, root space at rest, feet at y 0, front -z, +x her right (boxes: c = centre, h = half size). `local` = the joint\'s own frame',
                height=round(float(bodyb[1].y), 3), heightWithHat=round(float(allb[1].y), 3), brimSpan=round(float(allb[1].x - allb[0].x), 3),
                body=dict(r=0.42, h=round(float(bodyb[1].y), 3), c=r4((bodyb[0] + bodyb[1]) / 2)),
                parts=named, joints=joints, markers=markers, look=look, hit=hit)


def write_parts(H, root):
    out = parts_json(H, root)
    if os.path.exists(OUT_PARTS):   # the game side adds clip marks and samples: keep them
        try:
            old = json.load(open(OUT_PARTS))
            for k in ('marks', 'clips', 'game'):
                if k in old: out[k] = old[k]
        except Exception: pass
    json.dump(out, open(OUT_PARTS, 'w'), indent=1)
    print('JF_PARTS', OUT_PARTS, len(out['parts']), 'parts', len(out['markers']), 'markers', '| height', out['height'], 'with hat', out['heightWithHat'], 'brim', out['brimSpan'])
    return out


def run_qa(root):
    res = {}
    groups = {'whole': [o for o in base_parts(root)], 'far': [o for o in root.children if o.type == 'MESH' and '__lod' in o.name]}
    for k, objs in groups.items():
        if not objs: continue
        for o in objs: o.hide_render = False; o.hide_viewport = False
        res[k] = rpkit.qa(k, objs, eps=0.0008, tol=0.006 if k == 'whole' else 0.04, quiet=not arg('qa-warn'))   # (the far model is lumps seen from 30 m: its pieces may sit a few centimetres apart)
    return res


# ------------------------------------------------------------------------------------------------ pictures
def standin_mouth(H, smile=0.3, jaw=0.0):
    """her mouth is the game's code face (face.js): stood in here so the sheets show a mouth. never exported"""
    M = to_root('head', (0, hatbody.MOUTH_Y, -0.1215)); w = 0.066 * 0.92; lr = 0.008
    lip = mat('si_lip_hl', 0x5a1230, rough=0.3)
    curve = lambda x: smile * 1.3 * (x / w) * (x / w) * w * 0.55
    up = [(M.x + (i / 5 - 0.5) * w * 1.1, M.y + curve((i / 5 - 0.5) * w), M.z - 0.004 * math.cos((i / 5 - 0.5) * 3)) for i in range(6)]
    lo = [(M.x + (i / 5 - 0.5) * w * 0.9, M.y + curve((i / 5 - 0.5) * w) * 0.8 - lr * 1.6 - jaw * 0.03, M.z + 0.002) for i in range(6)]
    out = [sweep(up, [lr * 0.6] + [lr] * 4 + [lr * 0.6], lip, seg=6, name='si_lip'), sweep(lo, [lr * 0.7] + [lr * 1.1] * 4 + [lr * 0.7], lip, seg=6, name='si_lip2')]
    for o in out: o['standin'] = 1
    return out


def scale_figure(x=1.75, z=0.1):
    """a 1.8 m figure: the player's height"""
    g = mat('hl_fig', 0x9a9aa4, rough=0.7)
    out = [ball(0.105, (x, 1.69, z), g, scale=(0.92, 1.1, 1.0), seg=12, rings=8, name='jf_set_fig'), cyl(0.045, 0.1, (x, 1.55, z), g, axis='y', seg=8, name='jf_set_fig'),
           box((0.4, 0.5, 0.2), (x, 1.26, z), g, bev=0.05, name='jf_set_fig'), box((0.3, 0.16, 0.18), (x, 0.95, z), g, bev=0.04, name='jf_set_fig')]
    for sx in (-1, 1):
        out += [box((0.12, 0.86, 0.14), (x + sx * 0.09, 0.44, z), g, bev=0.03, name='jf_set_fig'), box((0.09, 0.62, 0.1), (x + sx * 0.26, 1.2, z), g, bev=0.03, name='jf_set_fig')]
    return out


def wb_shot(path, cam_pos, target, res=(600, 800), ortho=None, lens=70, flat=None, bg=(1, 1, 1)):
    """workbench: fast. flat = a colour: every surface that colour, no light (a silhouette)"""
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    if flat is not None: sh.light = 'FLAT'; sh.color_type = 'SINGLE'; sh.single_color = flat; sh.show_shadows = False; sh.show_cavity = False
    else: sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_shadows = True; sh.show_cavity = True; sh.cavity_type = 'BOTH'; sh.show_specular_highlight = True
    sc.display.render_aa = '8'
    sc.world = sc.world or bpy.data.worlds.new('w'); sc.world.use_nodes = False; sc.world.color = bg
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x, sc.render.resolution_y = res
    cam = rpkit._link(bpy.data.objects.new('pc', bpy.data.cameras.new('pc'))); sc.camera = cam
    cd = cam.data; cd.clip_start = 0.05; cd.clip_end = 400
    if ortho: cd.type = 'ORTHO'; cd.ortho_scale = ortho
    else: cd.lens = lens
    cam.location = gv(*cam_pos); rpkit._look_at(cam, gv(*target))
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    return path


def view(path, target, deg, dist, lens=70, res=(440, 580), up=0.12, quick=False):
    if quick or arg('quick'):
        a = math.radians(deg); d = Vector((math.sin(a), math.cos(a), up)).normalized(); t = gv(*target); pos = t + d * dist
        return wb_shot(path, (pos.x, pos.z, -pos.y), target, res=res, lens=lens, bg=(0.17, 0.13, 0.2))
    return cam_shot(path, target, deg, dist, lens=lens, res=res, up=up)


def vis(lod=False):
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.name.startswith('part_'): continue
        hide = (tag_of(o) == 'lod') != lod
        o.hide_render = hide; o.hide_viewport = hide


def posed(joint, p=(0, 0, 0)):
    """a joint-frame point where it is NOW (the pose rig), game axes"""
    b = RIG[joint].matrix_world @ (jm(joint).inverted() @ gv(*to_root(joint, p)))
    return (b.x, b.z, -b.y)


def sheet_turn(H, root, tb, info):
    os.makedirs(TMP, exist_ok=True)
    vis()
    Hh = 3.5; c = gv(0, 1.78, 0)
    studio(Hh, c); floor_disc(2.6); fig = scale_figure()
    ps = []
    for i, (nm, deg) in enumerate((('front', 0), ('three quarter', 38), ('her right', 90), ('back', 180), ('three quarter back', 218), ('her left', 270))):
        ps.append(view(os.path.join(TMP, 'hl_t%d.png' % i), (0, 1.78, 0), deg, Hh * 2.45, lens=70, res=(520, 600)))
    for o in fig: bpy.data.objects.remove(o, do_unlink=True)
    return rpkit.contact(ps, os.path.join(SHEET_DIR, 'c_hat_lord'), 'c_hat_lord  MADAM CHAIR and OVERSIGHT  %d tris  %.2f m to the top of her head, %.2f with the hat, brim %.2f m  (the grey figure is 1.8 m)' % (tb, info['height'], info['heightWithHat'], info['brimSpan']), 3,
                         ['front', 'three quarter', 'her right: the low wing, the feeler', 'back', 'three quarter back', 'her left: the long wing'])


def sheet_sil(H, root):
    """the silhouette, front on, beside the owner's sketch"""
    os.makedirs(TMP, exist_ok=True)
    vis(); rpkit.clear_studio()
    p = wb_shot(os.path.join(TMP, 'hl_sil.png'), (-0.2, 1.84, -30), (-0.2, 1.84, 0), res=(1000, 1100), ortho=4.05, flat=(0, 0, 0))
    dst = os.path.join(SHEET_DIR, 'c_hat_lord_silhouette.jpg')
    # the sketch, cropped to the figure and scaled to the same height
    os.system(f'ffmpeg -loglevel error -y -i "{SKETCH}" -i "{p}" -filter_complex "[0:v]crop=1360:1496:130:440,scale=1000:1100,eq=contrast=1.5:brightness=0.04[a];[a][1:v]hstack=inputs=2" -q:v 3 "{dst}"')
    print('JF_SHEET', dst)
    return dst


def sheet_close(H, root):
    os.makedirs(TMP, exist_ok=True)
    vis()
    hc = to_root('hat', (0, 0.2, 0)); ec = to_root('hat', (0, 0.22, -0.3)); fc = to_root('head', (0, 0.2, -0.1)); sk = to_root('spine', (0, 0.42, -0.1))
    hr = Vector(posed('handR', (0, -0.14, 0))); studio(1.4, gv(*hc), key=1.0)
    V = [('the hat from above', tuple(hc), 20, 0.75, 3.6, 50), ('the underside: what you see from 1.8 m', (0, 2.72, -0.1), 12, -0.55, 3.2, 50), ('the band: its mouth, the clasps', tuple(to_root('hat', (0.1, 0.1, -0.3))), 25, 0.1, 1.35, 70),
         ('the growths on her right of the crown', tuple(to_root('hat', (0.3, 0.22, -0.05))), 70, 0.25, 1.3, 70), ('HER eyes: the brown pair', tuple(ec), 0, 0.05, 0.75, 70), ('her face under the brim: its fingers over where her eyes would be', tuple(fc), 12, -0.12, 1.3, 70),
         ('the low wing and the feeler', tuple(to_root('brimRb', (0.3, 0, 0))), 30, -0.1, 1.5, 70), ('her right hand', tuple(hr), 40, 0.05, 0.9, 70), ('the chest: the empty socket', tuple(sk), 8, 0.05, 1.2, 70),
         ('the bar, a hook, the collar', (0.3, 2.2, 0.05), 40, 0.3, 1.6, 70), ('the cape from behind', (0, 1.3, 0.2), 180, 0.1, 6.0, 70), ('legs and shoes inside the cape', (0, 0.5, 0), 15, 0.1, 2.8, 70)]
    ps = [view(os.path.join(TMP, 'hl_c%d.png' % i), t, deg, d, lens=ln, res=(440, 400), up=up) for i, (_, t, deg, up, d, ln) in enumerate(V)]
    return rpkit.contact(ps, os.path.join(SHEET_DIR, 'c_hat_lord_closeups'), 'MADAM CHAIR and OVERSIGHT  close up', 4, [v[0] for v in V])


def main():
    sheets = [] if arg('no-sheet') else (arg('sheet') or 'turn,sil,close').split(',')
    reset()
    H, root = build()
    if not arg('no-ao'): bake(H, root); lap('ao')
    for o in root.children:
        if o.type == 'MESH': ensure_tint(o); rpkit.final_colour(o)
    if not arg('no-lod'): add_far_hl(root); lap('far')
    tb, tl = stats(root)
    if arg('qa'): run_qa(root); lap('qa')
    info = write_parts(H, root) if not arg('no-export') else parts_json(H, root)
    if arg('no-export'): print('JF_SIZE height', info['height'], 'with hat', info['heightWithHat'], 'brim', info['brimSpan'])
    if not arg('no-export'):
        for o in root.children: o.hide_render = False
        rpkit.export_glb(root, OUT_GLB); rpkit.compact_glb(OUT_GLB)
        print('JF_SIZE %d KB' % (os.path.getsize(OUT_GLB) // 1024))
    if not sheets: return
    preview_colours()
    RIG.update(pose_rig_hl(root, extra=[(o, 'head') for o in standin_mouth(H)])); apply_pose_hl(RIG, STANCE)
    if 'sil' in sheets: sheet_sil(H, root); lap('sil')
    if 'turn' in sheets: sheet_turn(H, root, tb, info); lap('turn')
    if 'close' in sheets: sheet_close(H, root); lap('close')
    if any(s in sheets for s in ('scale', 'poses', 'clips')):
        import hatposes
        hatposes.run(H, root, sheets, SHEET_DIR, TMP, globals())


main()
