# The finisher videos' retime pass (20 Nov; the owner: "make each scene longer now to create suspense"): stretches
# chosen shots in time without reshooting. Frames come from the capture map (key -> image; keys a capture run skipped
# are blended from their neighbours); a stretched shot samples its own frames at a slower rate, cross-fading between
# neighbours so slow pushes stay smooth. Writes a frame folder (000.png ...), a retimed shots.json and the sound cues
# moved to match.
# run: py tools/roblox/finisher_video_retime.py <caps.json> <shots.json> <out dir> <stretch.json> [cues.json cues_out.json]
#   stretch.json: {"SHOT NAME": factor, ...} (shots not named keep 1.0)
import json, math, os, sys
from PIL import Image

W, H = 1280, 720


def to_169(im):
    w, h = im.size
    if abs(w / h - 16 / 9) > 0.01 and w / h < 16 / 9:
        ch = int(round(w * 9 / 16))
        top = (h - ch) // 2
        im = im.crop((0, top, w, top + ch))
    return im.resize((W, H), Image.LANCZOS)


def main():
    caps_p, shots_p, out, stretch_p = sys.argv[1:5]
    caps = json.load(open(caps_p))
    shots = json.load(open(shots_p))
    stretch = json.load(open(stretch_p))
    total = sum(c for _, c in shots['shots'])
    pre = sorted(caps)[0][0] if caps else 'v'
    have = {int(k[1:]): p for k, p in caps.items()}
    cache = {}
    shot_of = []
    for si, (_, c) in enumerate(shots['shots']):
        shot_of += [si] * c

    def src(i):
        # frame i of the original cut (a skipped key: the blend of its nearest shot neighbours)
        if i in cache:
            return cache[i]
        if i in have:
            im = to_169(Image.open(have[i]).convert('RGB'))
        else:
            # (only from its own shot: a blend across a cut would show both shots at once)
            same = [j for j in have if shot_of[j] == shot_of[i]]
            lo = max((j for j in same if j < i), default=None)
            hi = min((j for j in same if j > i), default=None)
            if lo is None and hi is None:
                lo = max((j for j in have if j < i), default=None)
            if lo is None or hi is None:
                im = src(lo if lo is not None else hi)
            else:
                im = Image.blend(src(lo), src(hi), (i - lo) / (hi - lo))
        cache[i] = im
        return im

    os.makedirs(out, exist_ok=True)
    new_shots, k, start_old, start_new, n_out = [], 0, {}, {}, 0
    for name, c in shots['shots']:
        f = float(stretch.get(name, 1.0))
        m = max(1, int(round(c * f)))
        start_old[name], start_new[name] = k, n_out
        for j in range(m):
            x = k + (j * (c - 1) / max(1, m - 1) if m > 1 else 0)
            i0 = int(math.floor(x))
            a = x - i0
            im = src(i0) if a < 1e-3 or i0 + 1 >= k + c else Image.blend(src(i0), src(i0 + 1), a)
            im.save(os.path.join(out, f'{n_out:03d}.png'))
            n_out += 1
        new_shots.append([name, m])
        k += c
        # (the cache only needs the current shot and its edges)
        for key in [q for q in cache if q < k - 2]:
            del cache[key]
    json.dump({'fps': shots['fps'], 'shots': new_shots}, open(os.path.join(out, 'shots.json'), 'w'))
    print('retime', total, '->', n_out, 'frames', new_shots)
    if len(sys.argv) > 6:
        cues = json.load(open(sys.argv[5]))
        names = []
        for name, c in shots['shots']:
            names += [name] * c
        for q in cues:
            f0 = q['frame']
            nm = names[min(max(0, f0), total - 1)]
            fac = float(stretch.get(nm, 1.0))
            q['frame'] = int(round(start_new[nm] + (f0 - start_old[nm]) * fac))
            if q.get('len'):
                q['len'] = int(round(q['len'] * fac))
        json.dump(cues, open(sys.argv[6], 'w'), indent=1)
        print('cues retimed', len(cues))


main()
