# MADAM CHAIR's pose and clip sheets from Blender: the model posed with the very numbers the game plays (hl_clips.py).
#   --sheet=poses   one key pose a clip                          -> sheets/c_hat_lord_poses.jpg
#   --sheet=clips   a contact strip per clip (10 frames)         -> sheets/c_hat_lord_clip_<name>.jpg   (--clip=a,b for some)
# What the game adds on top is not here: the hat turning to look at you, and her walk laid over a clip when she moves
# (hl_walk is shown as its own strip). --quick renders them with Workbench (flat light, no vertex colour).
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hatkit import *  # noqa
import hl_clips

# clip: (the moment that says it, camera (target, degrees round her from the front, up, distance))
FULL = ((0, 1.75, 0), 24, 0.1, 9.6); HATV = ((0, 2.5, -0.3), 28, 0.02, 6.2); FACE = ((0, 2.72, -0.15), 14, -0.2, 3.0)
KEY = {'hl_idle': (1.75, FULL), 'hl_walk': (0.35, ((0, 1.6, 0), 62, 0.08, 9.6)), 'hl_duck': (2.2, ((0, 1.5, -0.2), 55, 0.08, 9.6)), 'hl_talk': (1.5, HATV), 'hl_offer': (1.9, ((0.1, 1.9, -0.3), 40, 0.08, 7.4)),
       'hl_bow': (1.3, ((0, 1.9, -0.2), 62, 0.06, 8.0)), 'hl_lunge': (1.6, ((0, 2.0, -0.5), 58, 0.04, 8.0)), 'hl_reveal': (2.6, FACE), 'hl_reveal_end': (0.9, FACE), 'hl_attack_tell': (1.0, FULL),
       'hl_strike': (0.3, ((0, 1.8, -0.3), 30, 0.2, 9.6)), 'hl_stagger': (0.14, ((0, 1.7, 0), 60, 0.08, 9.6)), 'hl_hat_off': (4.2, ((0, 1.9, 0), 40, 0.08, 11.5))}


def run(H, root, sheets, SHEET_DIR, TMP, G):
    view = G['view']; RIG = G['RIG']; vis = G['vis']
    os.makedirs(TMP, exist_ok=True)
    vis()
    studio(3.5, gv(0, 1.78, 0)); floor_disc(3.2)
    names = list(hl_clips.CLIPS)
    if 'poses' in sheets:
        ps = []; labs = []
        for n in names:
            t, (tg, deg, up, dist) = KEY[n]
            apply_pose_hl(RIG, hl_clips.evaluate(n, t))
            ps.append(view(os.path.join(TMP, 'hl_k_%s.png' % n), tg, deg, dist, lens=70, res=(400, 440), up=up)); labs.append('%s  %.1f s' % (n[3:], t))
        rpkit.contact(ps, os.path.join(SHEET_DIR, 'c_hat_lord_poses'), 'MADAM CHAIR  one moment from each clip (the game plays these numbers)', 5, labs)
    if 'clips' in sheets:
        only = str(arg('clip')).split(',') if arg('clip') and arg('clip') is not True else names
        for n in names:
            if n not in only: continue
            C = hl_clips.CLIPS[n]; dur = hl_clips.duration(n); N = 10
            _, (tg, deg, up, dist) = KEY[n]
            ts = [dur * i / (N - (0 if C['loop'] else 1)) for i in range(N)]
            ps = []; labs = []
            for i, t in enumerate(ts):
                apply_pose_hl(RIG, hl_clips.evaluate(n, t))
                mk = [m for mt, m in C['marks'] if (ts[i - 1] if i else -1) < mt <= t]
                ps.append(view(os.path.join(TMP, 'hl_f_%s_%d.png' % (n, i)), tg, deg, dist, lens=70, res=(330, 380), up=up)); labs.append('%.2f s%s' % (t, ('  ' + ' '.join(mk)) if mk else ''))
            rpkit.contact(ps, os.path.join(SHEET_DIR, 'c_hat_lord_clip_' + n[3:]), 'MADAM CHAIR  %s  %s  (%s)' % (n, ('loop %.1f s' % C['loop']) if C['loop'] else ('%.1f s' % dur) + ('' if C['len'] else ', held'), C['note'][:110]), 5, labs)
    apply_pose_hl(RIG, G['STANCE'])
