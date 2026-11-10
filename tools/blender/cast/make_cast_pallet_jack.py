# PALLET JACK (Jack Marsh, 41, the Bottom's delivery man; OVERDUE's crewmate who dies in the tunnel, docs/story/TRAIN.md).
# A wide, unhurried man with an Overdrive Rig put INTO him, one part a year, paid for in soup: piston shins, a beer keg
# of a boiler sunk in his lower back with two thruster stacks behind his shoulders, a rocket-punch right forearm with the
# skin worn off the knuckles, a welded steel collarbone, hydraulic lines under the skin, scar tissue grown over plate.
# A hi-vis vest with MARSH DELIVERIES in marker (its own piece: he gives it to a child), work trousers turned up clear
# of the pistons, steel-toe boots, a soup-stained tea towel in the back pocket, and a hand truck he doesn't need.
#
#   public/models/cast/c_pallet_jack.glb          part_<joint>[__<tag>] like every cast model (looks.js dresses the code
#                                                 skeleton with it); a far LOD per joint; damage pieces (dmg*, hidden)
#   public/models/cast/c_pallet_jack.parts.json   every named part (joint, box, pivot, axis), the markers, the states
#   public/models/story/s_handtruck.glb           the hand truck (its own prop)
#
# the man: jackbody.py · the machine in him: jackrig.py · what happens to him: jackdmg.py · the truck: jacktruck.py
# blender52 -b --python tools/blender/cast/make_cast_pallet_jack.py [-- flags]
#   --no-export --no-ao --no-sheet --qa --stats --only=jack,truck
#   --sheet=turn,face,dmg,parts,scale,poses,clips   (default: turn,face,dmg,parts)   --clip=pj_impaled   --out=<dir>
import os, sys, math, json, time
T0 = time.time()
def lap(k): print('JF_LAP %-10s %6.1fs' % (k, time.time() - T0))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jackrig import *  # noqa
import jackdmg, jacktruck

OUT_GLB = os.path.join(MODELS, 'cast', 'c_pallet_jack.glb')
OUT_PARTS = os.path.join(MODELS, 'cast', 'c_pallet_jack.parts.json')
OUT_TRUCK = os.path.join(MODELS, 'story', 's_handtruck.glb')
SHEET_DIR = arg('out') or SHEETS
TMP = os.path.join(SHEETS, '_tmp')
FACE_OPTS = dict(eyeR=0.027, iris=0x7a5a36, lip=0xc27866, lipR=0.013, teeth='tomb', brow=0x3a2a22, browW=0.07, lidColor=SK)
FACE_JACK = dict(lid=0.7, jaw=0, st=1.05, smile=0.5, by=-0.003, bt=-0.3)
SCALE = JOINTS[ID]['scale']
STATES = {  # what each state shows and hides (the game's PJ.dmg does the same)
    'fresh': dict(on=[], off=[]),
    'run_through': dict(on=['dmgWound', 'dmgArm', 'dmgBoilerSplit'], off=['boiler', 'fire', 'vest']),
    'armour_broken': dict(on=['dmgWound', 'dmgArm', 'dmgBoilerSplit', 'dmgCollar', 'dmgLockL', 'dmgLockR', 'dmgStackL', 'dmgStackR'],
                          off=['boiler', 'fire', 'vest', 'collar', 'lockL', 'lockR', 'stackL', 'stackR', 'flapL', 'flapR']),
    'marrow_taken': dict(on=['dmgWound', 'dmgArm', 'dmgMarrow', 'dmgCollar', 'dmgLockL', 'dmgLockR', 'dmgStackL', 'dmgStackR'],
                         off=['boiler', 'fire', 'vest', 'collar', 'lockL', 'lockR', 'stackL', 'stackR', 'flapL', 'flapR']),
}


def build():
    J = Jack(); J.vals = {}
    materials(J); lap('materials')
    for fn in (head, torso, collar, boiler, stacks, vest, hips, legs, shins, arms, forearm_right, jackdmg.damage):
        fn(J); lap(fn.__name__)
    meta = {'face': True, 'parts': sorted(k for k in J.P.info if not k.startswith('dmg')), 'dmg': sorted(k for k in J.P.info if k.startswith('dmg')), 'states': STATES}
    root = J.P.root(meta); lap('join')
    return J, root


def base_parts(root): return [o for o in root.children if o.type == 'MESH' and '__dmg' not in o.name and '__lod' not in o.name]
def tag_of(o): return (o.name[len('part_'):].split('__') + [''])[1].rstrip('0123456789.')


def bake(J, root):
    """AO into the vertex colours, each group lit by what it really sits against (he is baked without his vest on)"""
    allp = [o for o in root.children if o.type == 'MESH']
    vestp = [o for o in allp if tag_of(o) == 'vest']; dmg = [o for o in allp if tag_of(o).startswith('dmg')]
    base = [o for o in allp if o not in vestp and o not in dmg]
    for o in allp: o.hide_render = False
    rpkit.bake_ao(base, dist=0.22, samples=12, lo=0.42)
    rpkit.bake_ao(vestp, dist=0.22, samples=12, lo=0.5, also=base)
    swapped = set(STATES['marrow_taken']['off'])
    rpkit.bake_ao(dmg, dist=0.22, samples=12, lo=0.42, also=[o for o in base if tag_of(o) not in swapped])


def parts_json(J, root):
    """boxes (root space at rest, the game's metres: x1.18), pivots and axes of the moving pieces, markers, states"""
    S = SCALE
    def r3(v): return [round(float(x) * S, 4) for x in v]
    def gpt(joint, p): b = castlib.joint_matrix(ID, joint) @ gv(*p); return Vector((b.x, b.z, -b.y))
    def gdr(joint, d): b = castlib.joint_matrix(ID, joint).to_3x3() @ gv(*d); b.normalize(); return [round(x, 4) for x in (b.x, b.z, -b.y)]
    parts = {}
    for o in root.children:
        if o.type != 'MESH' or '__lod' in o.name: continue
        t = tag_of(o)
        if not t: continue
        lo, hi = rpkit.bounds([o])
        e = parts.setdefault(t, dict(joint=o.name[len('part_'):].split('__')[0], c=None, h=None))
        if e['c'] is not None:
            plo = Vector(e['_lo']); phi = Vector(e['_hi']); lo = Vector(map(min, lo, plo)); hi = Vector(map(max, hi, phi))
        e['_lo'], e['_hi'] = tuple(lo), tuple(hi); e['c'] = r3((lo + hi) / 2); e['h'] = r3((hi - lo) / 2)
    for t, e in parts.items():
        e.pop('_lo', None); e.pop('_hi', None)
        inf = J.P.info.get(t, {})
        if inf.get('note'): e['note'] = inf['note']
    markers = {}; moving = {}
    for k, v in J.marks.items():
        joint, p = v[0], v[1]
        ent = dict(joint=joint, at=r3(gpt(joint, p)), local=[round(float(x), 4) for x in p])
        if len(v) > 2: ent['dir'] = gdr(joint, v[2]); ent['localDir'] = [round(float(x), 4) for x in Vector(v[2]).normalized()]
        if k in parts and J.P.info.get(k, {}).get('pivot') is not None:
            moving[k] = dict(joint=joint, pivot=ent['local'], axis=ent.get('localDir'), **J.vals.get(k, {}))
        else: markers[k] = ent
    allb = rpkit.bounds(base_parts(root)); sz = allb[1] - allb[0]
    out = dict(v=1, model='c_pallet_jack.glb', scale=S, units='metres, root space at rest, feet at y 0, front -z (boxes: c = centre, h = half size). `local` = the joint\'s own frame at unit scale',
               height=round(float(allb[1].y) * S, 3), body=dict(r=round(float(max(sz.x, sz.z)) * 0.36 * S, 3), h=round(float(sz.y) * S, 3), c=r3((allb[0] + allb[1]) / 2)),
               parts=parts, moving=moving, markers=markers, states=STATES,
               rig=dict(stackRise=STACK_RISE, flapOpen=1.2, cockPull=COCK_PULL, punchReach=PUNCH_REACH))
    return out


def write_parts(J, root):
    out = parts_json(J, root)
    if os.path.exists(OUT_PARTS):   # the game side adds the clips' marks and samples (tools/blender/cast/pjparts.cjs): keep them
        try:
            old = json.load(open(OUT_PARTS))
            for k in ('marks', 'clips', 'props'):
                if k in old: out[k] = old[k]
        except Exception: pass
    json.dump(out, open(OUT_PARTS, 'w'), indent=1)
    print('JF_PARTS', OUT_PARTS, len(out['parts']), 'parts', len(out['markers']), 'markers')
    return out


def stats(root):
    rows = tri_report(root)
    b = sum(n for nm, n in rows if '__dmg' not in nm and '__lod' not in nm); d = sum(n for nm, n in rows if '__dmg' in nm and not nm.endswith('Far')); l = sum(n for nm, n in rows if '__lod' in nm or nm.endswith('Far'))
    v = sum(n for nm, n in rows if nm.endswith('__vest'))
    print('JF_TRIS base %d (of which the vest %d) | damage pieces %d | far LOD %d | total in file %d' % (b, v, d, l, b + d + l))
    if arg('stats'):
        for nm, n in sorted(rows, key=lambda r: -r[1]): print('   %-34s %6d' % (nm, n))
    return b, d, l


# ------------------------------------------------------------------------------------------------ pictures
def face_objs(J, pose=None):
    fo = standin_face(ID, FACE_OPTS, pose or FACE_JACK)
    return fo


def tile(paths, dst, label, cols, labels=None):
    return rpkit.contact(paths, dst, label, cols=cols, labels=labels)


def sheet_turn(J, root, tb, td):
    """front, 3/4, side, back, 3/4 back and the face, with his face on (the stand-in for the game's)"""
    os.makedirs(TMP, exist_ok=True)
    show_only(root)
    H = 1.82; c = gv(0, 0.9, 0)
    studio(H, c)
    floor_disc(1.6)
    ps = []
    for i, (nm, deg) in enumerate((('front', 0), ('three quarter', 40), ('his left side', 90), ('back', 180), ('three quarter back', 222), ('his right side', 270))):
        ps.append(cam_shot(os.path.join(TMP, 'pj_t%d.png' % i), (0, 0.9, 0), deg, H * 2.55, lens=70, res=(440, 580)))
    hh = max((o.matrix_world @ v.co).z for o in base_parts(root) if tag_of(o) not in ('stackL', 'stackR', 'flapL', 'flapR') for v in o.data.vertices)
    return tile(ps, os.path.join(SHEET_DIR, 'c_pallet_jack'), 'c_pallet_jack  PALLET JACK  %d tris (+%d damage pieces)  %.2f m tall in the game' % (tb, td, hh * SCALE), 3,
                ['front', 'three quarter', 'his left', 'back', 'three quarter back', 'his right'])


def sheet_face(J, root):
    os.makedirs(TMP, exist_ok=True)
    show_only(root)
    hc = (0, 1.565, -0.1)
    studio(0.5, gv(*hc), key=1.0)
    ps = []
    for i, (deg, up, dist, lens, tgt) in enumerate(((0, 0.04, 0.95, 85, hc), (32, 0.08, 0.95, 85, hc), (90, 0.05, 0.95, 85, (0, 1.565, -0.03)), (-35, 0.25, 0.95, 85, hc), (150, 0.1, 1.0, 85, (0, 1.56, 0.0)), (18, 0.02, 1.9, 85, (0, 1.36, -0.1)))):
        ps.append(cam_shot(os.path.join(TMP, 'pj_f%d.png' % i), tgt, deg, dist, lens=lens, res=(480, 480), up=up))
    return tile(ps, os.path.join(SHEET_DIR, 'c_pallet_jack_face'), 'PALLET JACK  the face at talk distance (eyes, lids, brows and mouth are the game\'s code face, stood in here)', 3,
                ['front', 'three quarter', 'his left', 'from above his right', 'behind his left ear', 'head and shoulders'])


def sheet_parts(J, root):
    os.makedirs(TMP, exist_ok=True)
    show_only(root)
    studio(0.9, gv(0, 1.0, 0.2), key=1.1)
    floor_disc(1.6)
    V = [('the boiler: a beer keg', (0.0, 1.03, 0.36), 180, 0.1, 1.15, 70), ('gauge, level glass, stacks', (-0.05, 1.2, 0.36), 222, 0.3, 1.25, 70), ('bleed valve, fire door', (0.08, 0.98, 0.38), 152, 0.02, 0.95, 70),
         ('stacks and rain caps', (0, 1.56, 0.4), 180, 0.55, 1.0, 70), ('the welded collarbone', (0.0, 1.27, -0.2), 12, 0.22, 0.85, 70), ('the rocket forearm', (0.5, 0.84, 0.0), 300, 0.1, 0.95, 70),
         ('knuckles, cocking collar', (0.5, 0.66, -0.02), 20, -0.1, 0.75, 70), ('exhaust bell, hatch', (0.5, 0.95, 0.08), 232, 0.2, 0.85, 70), ('piston shins', (0.0, 0.22, -0.03), 28, 0.12, 1.25, 70),
         ('shin lock, guard, boot', (0.19, 0.16, -0.06), 300, 0.1, 0.95, 70), ('plates under scar, lines', (-0.4, 1.25, 0.0), 60, 0.25, 0.95, 70), ('towel, belt, keys', (0.05, 0.72, 0.2), 205, 0.05, 1.0, 70)]
    ps = [cam_shot(os.path.join(TMP, 'pj_p%d.png' % i), t, deg, d, lens=ln, res=(440, 400), up=up) for i, (_, t, deg, up, d, ln) in enumerate(V)]
    return tile(ps, os.path.join(SHEET_DIR, 'c_pallet_jack_parts'), 'PALLET JACK  the rig parts, close up (each one is its own named piece)', 4, [v[0] for v in V])


def sheet_dmg(J, root):
    os.makedirs(TMP, exist_ok=True)
    studio(1.82, gv(0, 0.9, 0)); floor_disc(1.6)
    ps = []; labs = []
    def shots(key, st, views):
        show_only(root, tags_on=st['on'], tags_off=st['off'])
        for (lab, t, deg, up, d, res) in views:
            ps.append(cam_shot(os.path.join(TMP, 'pj_d%d.png' % len(ps)), t, deg, d, lens=70, res=(440, 480), up=up)); labs.append(key + ': ' + lab)
    full = lambda deg: ('', (0, 0.9, 0), deg, 0.12, 1.82 * 2.5, None)
    shots('fresh, vest off', dict(on=[], off=['vest']), [('front', (0, 0.9, 0), 20, 0.12, 4.6, None), ('back', (0, 0.9, 0), 200, 0.12, 4.6, None)])
    shots('run through', STATES['run_through'], [('front', (0, 0.9, 0), 25, 0.12, 4.6, None), ('back', (0, 0.9, 0), 205, 0.12, 4.6, None), ('the hole under his ribs', (0.03, 1.0, -0.3), 28, 0.12, 1.25, None),
                                                 ('the boiler split, venting', (0.02, 1.05, 0.4), 205, 0.2, 1.3, None), ('side: through him', (0, 1.0, 0), 90, 0.05, 2.3, None)])
    shots('armour broken', STATES['armour_broken'], [('front', (0, 0.9, 0), 25, 0.12, 4.6, None), ('back', (0, 0.9, 0), 215, 0.12, 4.6, None), ('collarbone weld sprung', (0.02, 1.27, -0.2), 14, 0.25, 0.85, None),
                                                     ('shin locks blown', (0.0, 0.2, -0.05), 30, 0.1, 1.2, None), ('stacks bent', (0, 1.5, 0.4), 200, 0.4, 1.3, None)])
    shots('marrow taken', STATES['marrow_taken'], [('back', (0, 0.9, 0), 190, 0.12, 4.6, None), ('the boiler opened, the gap in his spine', (0.0, 1.03, 0.36), 186, 0.12, 1.15, None), ('from his left', (0.0, 1.03, 0.3), 232, 0.2, 1.25, None)])
    show_only(root)
    return tile(ps, os.path.join(SHEET_DIR, 'c_pallet_jack_damage'), 'PALLET JACK  damage states: run_through, armour_broken, marrow_taken (hidden pieces, swapped in by name)', 5, labs)


def main():
    only = (arg('only') or 'jack,truck').split(',')
    sheets = [] if arg('no-sheet') else (arg('sheet') or 'turn,face,dmg,parts').split(',')
    reset()
    if 'truck' in only:
        troot = jacktruck.build_truck()
        if not arg('no-ao'): rpkit.bake_ao([o for o in troot.children if o.type == 'MESH'], dist=0.2, samples=12, lo=0.45)
        for o in troot.children:
            if o.type == 'MESH': ensure_tint(o); rpkit.final_colour(o)
        if arg('qa'): rpkit.qa('handtruck', [o for o in troot.children if o.type == 'MESH'], tol=0.006, quiet=not arg('qa-warn'))
        if not arg('no-export'):
            rpkit.export_glb(troot, OUT_TRUCK); rpkit.compact_glb(OUT_TRUCK)
        tt = sum(n for _, n in tri_report(troot)); print('JF_TRIS handtruck', tt)
        if 'truck' in sheets or ('turn' in sheets and 'jack' not in only):
            preview_colours(); jacktruck.sheet_truck(troot, tt, SHEET_DIR, TMP)
        for o in [troot] + list(troot.children): o.hide_render = True; o.hide_viewport = True
        if 'jack' not in only: return
    J, root = build()
    if not arg('no-ao'): bake(J, root)
    for o in root.children:
        if o.type == 'MESH': ensure_tint(o); rpkit.final_colour(o)
    lap('ao'); far = add_far(root, ratio=0.13, own=('vest',)); lap('far')
    tb, td, tl = stats(root)
    if arg('qa'): jackdmg.run_qa(J, root, tag_of)
    out = write_parts(J, root) if not arg('no-export') else parts_json(J, root)
    if not arg('no-export'):
        for o in root.children: o.hide_render = False
        rpkit.export_glb(root, OUT_GLB); rpkit.compact_glb(OUT_GLB)
        print('JF_SIZE %d KB' % (os.path.getsize(OUT_GLB) // 1024))
    if not sheets: return
    preview_colours()
    fo = face_objs(J)
    lap('face'); 
    if 'turn' in sheets: sheet_turn(J, root, tb, td); lap('turn')
    if 'face' in sheets: sheet_face(J, root)
    if 'parts' in sheets: sheet_parts(J, root)
    if 'dmg' in sheets: sheet_dmg(J, root)
    if any(s in sheets for s in ('scale', 'poses', 'clips')):
        import jackposes
        jackposes.run(J, root, fo, sheets, SHEET_DIR, TMP, globals())


main()
