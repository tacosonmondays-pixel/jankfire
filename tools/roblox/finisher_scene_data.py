# The in-game finisher scenes' data (19 Nov; v2 on 20 Nov for Tidecrest v4.2): the moving cut that finisher_r15.py
# plans for the videos (video:<v>), boiled down to what the game plays per frame on the killer's and the victim's own
# avatars - the lens (stage-local CFrame, FOV, and the body point a close lens rides on), each body's clip and moment
# (two blended at a weight where the plan blends) and where its root stands, the afterimages, what the scabbard and the
# blade are doing (rebuilt in the game from the real body's own hands), the effects to draw, the stand-in anchors the
# lens and the effects hang from, the two-tone hit frames - plus the fixed set (floor, pillars, trees, sky ring).
# client/FinisherScene.luau plays it with the uploaded animations (Finishers.SCENE_ANIMS).
# run: py tools/roblox/finisher_scene_data.py <out.luau> <scene id>=<video_dir> [<scene id>=<video_dir> ...]
import json, os, sys

LENS_KEY = {'mouth': 'mouth', 'k.UpperTorso': 'kU', 'k.Head': 'kH', 'k.LowerTorso': 'kL', 'v.Head': 'vH',
            'v.UpperTorso': 'vU', 'v.LowerTorso': 'vL'}
# the stand-in's part sizes (finisher_r15.SIZE): a real body's anchor offsets scale by its own part over these
SIZES = {'Head': (1.2, 1.2, 1.2), 'UpperTorso': (2.0, 1.6, 1.0), 'LowerTorso': (2.0, 0.4, 1.0)}
ALL = {'LowerTorso': (2, 0.4, 1), 'UpperTorso': (2, 1.6, 1), 'Head': (1.2, 1.2, 1.2), 'RightUpperArm': (1, 1.1687, 1),
       'RightLowerArm': (1, 1.0519, 1), 'RightHand': (1, 0.3, 1), 'LeftUpperArm': (1, 1.1687, 1),
       'LeftLowerArm': (1, 1.0519, 1), 'LeftHand': (1, 0.3, 1), 'RightUpperLeg': (1, 1.2166, 1),
       'RightLowerLeg': (1, 1.1931, 1), 'RightFoot': (1, 0.3, 1), 'LeftUpperLeg': (1, 1.2166, 1),
       'LeftLowerLeg': (1, 1.1931, 1), 'LeftFoot': (1, 0.3, 1)}


def lowest(parts):
    # the stand-in's lowest body point (stage-local y): the game sets a real body's lowest point there (no sinking)
    y = 1e9
    for n, c in parts.items():
        if n not in ALL:
            continue
        sx, sy, sz = (v / 2 for v in ALL[n])
        for cx in (-sx, sx):
            for cy in (-sy, sy):
                for cz in (-sz, sz):
                    y = min(y, c[1] + c[6] * cx + c[7] * cy + c[8] * cz)
    return y


def r(x, n=3):
    v = round(float(x), n)
    return '0' if v == 0 else repr(v)


def cf(c):
    return '{' + ','.join([r(v, 3) for v in c[:3]] + [r(v, 4) for v in c[3:]]) + '}'


def lua(v):
    if isinstance(v, str):
        return '"' + v + '"'
    if isinstance(v, (int, float)):
        return r(v, 3)
    return '{' + ','.join(lua(x) for x in v) + '}'


def body(a, clips):
    s = f'{{ {clips.index(a["clip"]) + 1}, {r(a["t"], 4)}, {cf(a["root"])}, {r(a.get("sc", 0))}'
    if a.get('clip2'):
        s += f', {clips.index(a["clip2"]) + 1}, {r(a["t2"], 4)}, {r(a["w2"], 3)}'
    return s + ' }'


def kat_of(f):
    k = (f.get('sem') or {}).get('kat')
    if not k:
        kat = f.get('kat') or []
        return 'kat = { 1 }' if kat and kat[0]['mode'] == 'hand' else None
    m = k['mode']
    if m == 'hand':
        return 'kat = { 1 }'
    if m == 'pack' and k.get('aim'):
        return f'kat = {{ 8, {cf(k["T"])}, {lua(k["aim"])}, {r(k["w"])} }}'
    if m == 'pack':
        return f'kat = {{ 3, {cf(k["T"])} }}'
    if m == 'trail':
        return 'kat = { 4 }'
    if m == 'home':
        return f'kat = {{ 5, {r(k.get("push", 0))} }}'
    if m == 'through':
        return 'kat = { 6 }'
    if m == 'out':
        return f'kat = {{ 7, {r(k["e"])} }}'
    return None


def scene(sid, vdir):
    frames = json.load(open(os.path.join(vdir, 'frames.json')))
    shots = json.load(open(os.path.join(vdir, 'shots.json')))
    keys = sorted(k for k in frames if not k.startswith('_'))
    clips = []
    for k in keys:
        f = frames[k]
        for a in list(f.get('anim', {}).values()) + list(f.get('ghost', {}).values()):
            for c in (a['clip'], a.get('clip2')):
                if c and c not in clips:
                    clips.append(c)
    out = [f'\t{sid} = {{', f'\t\tfps = {shots["fps"]},',
           '\t\tclips = { ' + ', '.join(f'"{c}"' for c in clips) + ' },',
           '\t\tshots = { ' + ', '.join(f'{{ "{n}", {c} }}' for n, c in shots['shots']) + ' },',
           '\t\tsizes = { ' + ', '.join(f'{n} = {{ {s[0]}, {s[1]}, {s[2]} }}' for n, s in SIZES.items()) + ' },']
    st = frames.get('_stage', {}).get('props', [])
    out.append('\t\tstage = {')
    for p in st:
        s, c = p['size'], p['col']
        out.append(f'\t\t\t{{ "{p["shape"]}", {r(s[0])}, {r(s[1])}, {r(s[2])}, {cf(p["cf"])}, {r(c[0])}, {r(c[1])}, {r(c[2])}, "{p["mat"]}", "{p["tag"]}" }},')
    out.append('\t\t},')
    out.append('\t\tf = {')
    for k in keys:
        f = frames[k]
        sem = f.get('sem') or {}
        parts = [f'c = {cf(f["lens"]["cf"])}', f'fov = {r(f["lens"]["fov"], 2)}']
        need = set()
        la = LENS_KEY.get(sem.get('lens') or '')
        if la:
            parts.append(f'la = "{la}"')
            need.add(la)
        for n, a in sorted(f.get('anim', {}).items()):
            parts.append(f'{n} = {body(a, clips)}')
        for rg in f.get('rigs', []):
            if rg['name'] in ('k', 'v') and rg['name'] in f.get('anim', {}):
                parts.append(f'g{rg["name"]} = {r(lowest(rg["parts"]))}')
        gh = f.get('ghost') or {}
        if gh:
            parts.append('g = { ' + ', '.join(f'{{ {clips.index(a["clip"]) + 1}, {r(a["t"], 4)}, {cf(a["root"])}, {r(a["tr"])} }}'
                                               for _, a in sorted(gh.items())) + ' }')
        kt = kat_of(f)
        if kt:
            parts.append(kt)
        sh = sem.get('sh')
        if sh:
            parts.append(f'sh = {{ 1, {r(sh["m0"])}, {r(sh.get("fwd", 0))} }}' if sh['mode'] == 'lhand' else 'sh = { 2 }')
        if f.get('katL') and abs(f['katL'] - 1) > 1e-3:
            parts.append(f'L = {r(f["katL"], 3)}')
        if f.get('impact'):
            inv = f['impact'].get('bg', [1, 1, 1])[0] < 0.5
            parts.append('hit = ' + ('2' if inv else '1'))
        fxl = f.get('fx') or []
        if fxl:
            parts.append('fx = { ' + ', '.join(lua(e) for e in fxl) + ' }')
            for e in fxl:
                if e[0]:
                    need.add(e[0])
        if f.get('stage') is None and st:
            # (a frame the plan built on its own stage: a wide lens cleared the pillars in its way - the game hides
            # those pieces of the fixed set, by their 1-based place in the stage list)
            have = [tuple(round(x, 2) for x in p['cf'][:3]) for p in f.get('props', []) if p['tag'] == 'pillar']
            gone = [ix + 1 for ix, p in enumerate(st) if p['tag'] == 'pillar'
                    and tuple(round(x, 2) for x in p['cf'][:3]) not in have]
            if gone:
                parts.append('hide = { ' + ', '.join(str(g) for g in gone) + ' }')
        anc = f.get('anc') or {}
        if need:
            parts.append('an = { ' + ', '.join(f'{n} = {cf(anc[n])}' for n in sorted(need) if n in anc) + ' }')
        out.append('\t\t\t{ ' + ', '.join(parts) + ' },')
    out.append('\t\t},')
    out.append('\t},')
    return out


def main():
    dst = sys.argv[1]
    body_ = []
    for a in sys.argv[2:]:
        sid, vdir = a.split('=', 1)
        body_ += scene(sid, vdir)
    head = ['--!strict',
            '-- FINISHER SCENE DATA - generated by tools/roblox/finisher_scene_data.py from the video plan of',
            '-- tools/roblox/finisher_r15.py (video:<v>); do not edit by hand, rebuild it. Per frame (24 fps):',
            '--   c = the lens (CFrame components, stage-local), fov, la = the body point a close lens rides on (mouth = the',
            "--   scabbard's mouth, kH/kU/kL = the killer's head/upper/lower torso, vH/vU = the victim's);",
            '--   k / v = { clip index, clip time, root CFrame, scatter[, clip2 index, time2, weight2] }; g = afterimages',
            "--   { clip index, time, root, transparency }; gk / gv = the stand-in's lowest body point (y, stage-local);",
            "--   kat = the blade: {1} in the right hand, {3, T} the pack's sword track, {4} trailing, {5, push} home in the",
            '--   scabbard, {6} from the hand through the mouth, {7, e} streaming out e studs, {8, T, aim, w} the pack track',
            '--   turned to aim; sh = the scabbard {1, m0, fwd} in the left hand / {2} on the hip; L = the blade length (x the',
            '--   skin); hit = 1 two-tone / 2 its inverse;',
            '--   fx = effects { anchor, kind, ... } (ring, stroke, burst, drift, splats, glint, sweat; stage-local points)',
            "--   an = the stand-in anchors this frame's lens and effects hang from (moved onto the real bodies in the game).",
            '-- Stage-local = 600 studs over the scene origin; the stage list is the fixed set.',
            'return {']
    open(dst, 'w', encoding='utf8', newline='\n').write('\n'.join(head + body_ + ['} :: any', '']))
    print('wrote', dst, os.path.getsize(dst))


main()
