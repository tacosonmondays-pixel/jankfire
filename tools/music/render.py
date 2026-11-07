# render tracks: python render.py [slug ...]   (no args = all). writes public/music/<slug>.ogg + a report
# story beds: python render.py --story [slug ...]   (tracks with SUBDIR = 'story' land in public/music/story/<slug>.ogg)
import sys, os, json, importlib, time, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from analyze import measure, ffmpeg_loud
import soundfile as sf

OUT = os.path.join(HERE, '..', '..', 'public', 'music')
WORK = os.environ.get('JF_MUSIC_WORK', os.path.join(HERE, '.cache', 'work'))
TRACKS = ['jank_cola_rave', 'spoon_fight_tekno', 'rubber_duck_hardcore', 'hung_jury_hardcore', 'banana_peel_acid', 'wrecking_ball_warmup']
STORY = ['story_bottom', 'story_gut', 'story_commute']  # OVERDUE district beds: played by district, not in TRACKS


def run(slug):
    T = time.time()
    mod = importlib.import_module('tracks.' + slug)
    s = mod.build()
    mix, stems = s.render()
    np.save(os.path.join(WORK, slug + '_mix.npy'), mix.astype(np.float32))
    sub = getattr(mod, 'SUBDIR', '')  # story beds live in their own folder so they never join the PvP shuffle
    os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    ogg = os.path.join(OUT, sub, slug + '.ogg'); wav = os.path.join(WORK, slug + '.wav')
    ceil = -2.3
    for _ in range(4):  # vorbis can overshoot the master's ceiling a little: re-master lower until the file itself is safe
        out = s.master(mix, getattr(mod, 'TARGET', -8.0), ceil)
        sf.write(wav, out.astype(np.float32), 44100, subtype='FLOAT')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav, '-c:a', 'libvorbis', '-q:a', str(getattr(mod, 'QUALITY', 6)),
                        '-metadata', f'title={mod.TITLE}', '-metadata', f'artist={getattr(mod, "ARTIST", "JANKFIRE")}', ogg], check=True)
        _, tp, _ = ffmpeg_loud(ogg)
        if tp <= -1.1: break
        ceil -= tp + 1.15
        print(f'  {slug}: file true peak {tp} dBTP, re-mastering at ceiling {ceil:.2f}', flush=True)
    lp = os.path.join(WORK, 'lengths.json')  # exact sample counts, for the browser gapless check (t_music.cjs)
    L = json.load(open(lp)) if os.path.exists(lp) else {}
    L[(sub + '/' if sub else '') + slug + '.ogg'] = int(s.n); json.dump(L, open(lp, 'w'), indent=1)
    kicks = [float(s.t(b)) % s.L for b in s.kicks]
    r = measure(ogg, stems, kicks, png=os.path.join(WORK, slug + '.png'), title=f'{mod.TITLE} ({slug})')
    r['gains_db'] = s.gains; r['bpm'] = getattr(mod, 'BPM', None); r['render_s'] = round(time.time() - T, 1)
    print(json.dumps(r), flush=True)
    return r


if __name__ == '__main__':
    os.makedirs(WORK, exist_ok=True)
    args = sys.argv[1:]
    story = '--story' in args; args = [a for a in args if a != '--story']
    rep = [run(s) for s in (args or (STORY if story else TRACKS))]
    with open(os.path.join(WORK, 'report.json'), 'a') as f:
        for r in rep: f.write(json.dumps(r) + '\n')
