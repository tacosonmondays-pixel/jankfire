# Z-fighting inside the guns (16 Nov 2026: the hub's flicker scan found ~12 pairs on the armory's display guns, gaps of
# 0.002 - 0.019 studs). Two pieces of different looks whose faces lie in one plane, face the same way and overlap
# shimmer. The flicker session's tools/roblox/zfightfix.py finds and fixes them for the map kits in studs; a gun is
# built in metres and shown at many sizes, so here every gun is looked at in the studs of its SMALLEST static display
# (the hub armory's racks: HubRotundaRooms, a gun `len` studs long), where a gap in metres is the fewest studs. There
# each such pair is separated by EPS (0.04 studs: the smaller face, the detail, stands out; on undersides it steps back),
# which is a few millimetres on the gun (in hand and third person the gun is closer to the eye, so that gap is ample).
#   gun_zfix.zfix(g)  -> fix a built Gun's pieces in place (gun_set.py wraps every BUILD and SKINS builder with it)
#   blender -b --factory-startup -P tools/roblox/gun_zfix.py -- [ids ...|skins|all]   (report only, nothing written:
#   what is left after the fix; JF_NOZFIX=1 in the environment reports the guns as built, before it)
import sys, os, math
from mathutils import Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zfightfix

# the armory's racks: the long guns 6.6 studs long, the rest 3.9 (HubRotundaRooms racks). a gun not on a rack (or a
# skin, never on display) is taken as if it were, by its length
RACK = {'ar': 6.6, 'sniper': 6.6, 'redline': 6.6, 'lmg': 6.6,
        'smg': 3.9, 'pistol': 3.9, 'revolver': 3.9, 'sawnoff': 3.9, 'burst': 3.9, 'marbles': 3.9, 'shotgun': 3.9,
        'katana': 3.9}


def display_k(g):
    """studs per metre of the gun's smallest static display"""
    lo, hi = g.bounds()
    L = max(hi[2] - lo[2], 0.05)
    wid = g.name[2:].split('@')[0]
    ln = RACK.get(wid, 6.6 if L > 0.75 else 3.9)
    return ln / L


def _pieces(g, K):
    # in display studs, y up (the Blender frame is z up): M = scale K, then (x, y, z) -> (x, z, -y)
    M = Matrix.Scale(K, 4) @ Matrix.Rotation(-math.pi / 2, 4, 'X')
    P = {}
    for (node, slot), bm in g.pieces.items():
        bm.verts.index_update()  # (zfightfix reads triangles by vertex index: a builder's bmesh can carry stale ones,
        # and then every triangle is wrong. 16 Nov: the first two rounds looked clean here and were not in Roblox)
        s = g.slots[slot]
        zone = 'A' if '_wzA' in node else 'x'
        kind = {'n': 'neon', 'g': 'glass'}.get(s['kind'], 'plastic')
        look = '%s_%s_%s' % (kind, s['color'].lower(), zone)  # (same colour, same kind and zone: one look)
        P.setdefault((g.name + '|' + node, look), []).append((bm, M))
    return P


# zfightfix leaves out every triangle under MIN_AREA (0.01 sq studs) on its own: right for the map kits' big faces, but
# a gun's top faces are cut into small triangles, so on the armory scan (place version 396) eight top-face pairs it had
# not seen were still there. Here every triangle counts and a pair is one from HIT_AREA of overlap (the scan: 0.01)
HIT_AREA = 0.004


def _find(P):
    old = zfightfix.MIN_AREA
    zfightfix.MIN_AREA = 1e-6
    try:
        pieces, hits, plane_area = zfightfix.find(P)
    finally:
        zfightfix.MIN_AREA = old
    return pieces, {k: v for k, v in hits.items() if v[0] >= HIT_AREA}, plane_area


def report(g, K=None):
    K = K or display_k(g)
    pieces, hits, _ = _find(_pieces(g, K))
    out = []
    for (pa, pb, nk), (ar, n, da, db, na, nb) in sorted(hits.items(), key=lambda kv: -kv[1][0]):
        a, b = pieces[pa][0].split('|')[1], pieces[pb][0].split('|')[1]
        out.append('  %-26s %-26s gap %.4f studs, %.3f sq studs, normal (%.1f, %.1f, %.1f)' % (
            a + '__' + pieces[pa][1].split('_')[1], b + '__' + pieces[pb][1].split('_')[1], abs(da - db), ar, n.x, n.y, n.z))
    return K, out


# the gap a pair is given: 0.04 studs on the display (the map kits' EPS, twice the scan's 0.02), but never more than
# MAX_MM on the gun (the long guns on 3.9-stud racks are shown at ~3.2 studs a metre, where 0.04 studs is 12 mm: a band
# or a lens standing that far proud changes the gun; 8 mm is 0.026 studs there, still clear of the scan's 0.02)
MAX_MM = 8.0


def _fix(PIECES, eps, K, passes=16):
    """zfightfix.fix with a gun's rule for which face moves: the one already in front stands further out; of two level
       faces a trim (a _wzN piece: bands, stripes, lenses, rivets) stands out over a shell (_wzA / _wzB), and between
       two of a kind the smaller face in that plane does (the detail). (16 Nov: by area alone the Redline's body side was
       the smaller and grew over its flush stripe, burying it.)
       Faces pointing down move out too (unlike zfightfix: a gun's undersides are not ceilings). Returns the faces moved"""
    moved = 0
    TOL = zfightfix.TOL
    for _ in range(passes):
        pieces, hits, plane_area = _find(PIECES)
        if not hits: break
        need = {}
        for (pa, pb, nk), (ar, n, da, db, na, nb) in hits.items():
            sa = plane_area.get((pa, nk, round(da / TOL)), 0.0)
            sb = plane_area.get((pb, nk, round(db / TOL)), 0.0)
            ta, tb = '_wzN' in pieces[pa][0], '_wzN' in pieces[pb][0]
            # the face already in front is the one meant to be seen (the Hat Trick's three blue blocks stood 1.5 mm proud
            # of the dark handle panel: by 'trims first' the panel grew over them); level faces: the trim, then the smaller
            if abs(da - db) > 0.002: win = pa if da > db else pb
            elif ta != tb: win = pa if ta else pb
            else: win = pa if (sa < sb or (sa == sb and pa < pb)) else pb
            dw, do = (da, db) if win == pa else (db, da)
            nw = na if win == pa else nb
            push = (do - dw) + eps  # (always out: stepping an underside back, zfightfix's rule for ceilings, lifted the
            # Pool Cue's scope 2.8 mm off the cue)
            key = (win, nk, round(dw / 0.005))
            if key not in need or need[key][1] < push: need[key] = (nw, push, dw)
        for (pid, nk, _), (n, push, dw) in need.items():
            model, look, bm, M, g = pieces[pid]
            dl = M.inverted().to_3x3() @ (n * push)
            for v in bm.verts:
                # (only the face's own corners: within 0.3 mm of its plane. zfightfix's 0.006 studs is ~1 mm on a gun,
                # which took both faces of the Redline's 0.5 mm stripe and lifted it off the body)
                if abs(n.dot(M @ v.co) - dw) < 3e-4 * K: v.co += dl
        moved += len(need)
    return moved


def zfix(g, log=None):
    K = display_k(g)
    eps = min(0.04, MAX_MM / 1000.0 * K)
    n = _fix(_pieces(g, K), eps, K)
    if log: log('ZFIX %s: %d faces moved (display %.2f studs a metre, gap %.3f studs = %.1f mm)' % (g.name, n, K, eps, eps / K * 1000))
    return K, eps, n


if __name__ == '__main__':
    import gun_set
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ALL = dict(gun_set.BUILD); ALL.update(gun_set.SKINS)
    ids = argv or list(gun_set.BUILD)
    if ids == ['skins']: ids = [k for k in gun_set.SKINS if k != 'ar@cardboard']
    if ids == ['all']: ids = [k for k in ALL if k != 'ar@cardboard']
    tot = 0
    for wid in ids:
        g = ALL[wid]()
        K, lines = report(g)
        tot += len(lines)
        print('ZF %s: %d pairs (display %.2f studs a metre, 0.04 studs = %.1f mm)' % (wid, len(lines), K, 40 / K))
        for ln in lines: print(ln)
    print('ZF total', tot)
