# packs a video's frames.json into upload-ready data modules (a ModuleScript returning the JSON in a long string), split
# in parts. Keys: <prefix>NNN per frame, each frame's 'stage' names its video's fixed set ('_stage_<video>').
# run: py -I tools/roblox/finisher_real_pack.py <frames.json> <video> <prefix> <parts> <out base dir>
import json, os, sys

src, video, prefix, parts, outb = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
F = json.load(open(src))
keys = sorted(k for k in F if not k.startswith('_'))
stage_key = '_stage_' + video
per = (len(keys) + parts - 1) // parts
for pi in range(parts):
    chunk = keys[pi * per:(pi + 1) * per]
    out = {}
    for k in chunk:
        f = F[k]
        if f.get('stage') is True:
            f['stage'] = stage_key
        out[prefix + k[1:]] = f
    if pi == 0:
        out[stage_key] = F['_stage']
    d = os.path.join(outb, f'fr_{video}_{pi}')
    os.makedirs(d, exist_ok=True)
    js = json.dumps(out, separators=(',', ':'))
    assert ']==]' not in js
    open(os.path.join(d, 'FinVideoData.luau'), 'w').write('return [==[' + js + ']==]')
    json.dump({'name': 'FinVideoData', 'tree': {'$className': 'Folder', 'FinVideoData': {'$path': 'FinVideoData.luau'}}},
              open(os.path.join(d, 'default.project.json'), 'w'))
    print(d, len(chunk), len(js))
