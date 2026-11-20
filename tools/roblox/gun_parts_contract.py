# THE GUN PART CONTRACT (19 Nov 2026). The owner, after the exploded view: "Breaking down weapons will help with improving
# the model making future skins and creating proper animations right". So every kit gun is exported split into its
# REAL parts, each a node of its own ("<node>_wz<zone>__<slot>" pieces): reload animators (hold-hands, weapons-port:
# Reloads.luau, GunParts, Weapons mdl.parts) move parts by these names, skin makers paint and swap by part, and the
# exploded view (shared/GunExplode) takes the gun apart by them. The human-readable list is
# roblox/assets/weapons-kit/README.md; THIS table is the one the exporter checks.
#   python tools/roblox/gun_parts_contract.py            check every gun and skin in roblox/assets/weapons-kit/export_report.json
#   (export_weapons.py --kit runs the same check on the files it exports and prints PART CONTRACT lines)
# A skin must keep its base gun's part names and the pivots of the parts that move, so its reloads and BREAKDOWN work
# with no extra work: every MOVING node the base has, the skin has, and each one's middle within PIVOT_TOL of the base's.
import os, json, re

# the part names: node -> what it is (a node may carry several pieces, one per colour)
PARTS = {
    'body': 'the receiver / frame: the core every other part fits to (stays put in the breakdown)',
    'barrel': 'the barrel, its shroud, gas block, the brake when it is not a part of its own; minigun: barrels',
    'barrels': 'the minigun\'s spinning barrel cluster',
    'muzzle': 'a muzzle device that comes off on its own (brake, suppressor, flash hider)',
    'mag': 'the magazine (box, curved, drum, tube follower, the nail strip); the LMG\'s box',
    'belt': 'the LMG\'s belt (belt_00 .. belt_11 are its links)',
    'charge': 'the charging handle (rifles, SMGs)',
    'bolt': 'a bolt you work by hand (bolt-action rifles) or a visible bolt carrier',
    'cocker': 'a small gun\'s charging tab (Lefty & Righty)',
    'slide': 'a pistol\'s slide',
    'cylinder': 'a revolver\'s cylinder',
    'hammer': 'the hammer (revolver, pistol); lhammer = the lever gun\'s; hammerl / hammerr = a double\'s two',
    'pump': 'a pump action\'s sliding fore-end; the water pistol\'s pump',
    'lever': 'a lever action\'s lever',
    'hinge': 'a break action\'s barrels-and-hinge that tips open',
    'shell1': 'a break action\'s chambered shells (shell1, shell2)',
    'cover': 'a feed cover / dust cover that opens',
    'box': 'the minigun\'s ammo box',
    'tank': 'a water tank',
    'stock': 'the stock / butt',
    'grip': 'the pistol grip (and its trigger area when that is one piece)',
    'fore': 'a fixed fore-end or fore-grip',
    'guard': 'a handguard; tguard = the trigger guard when both exist',
    'sight': 'the rear sight (irons)',
    'fsight': 'the front sight post / blade; bead = a shotgun\'s bead',
    'rail': 'a top rail',
    'scope': 'a scope or optic (its lenses ride with it as lens)',
    'trim': 'small fittings that ride with whatever holds them: trim, rivet, mark, panel, dot, lens ...',
}
# the parts reloads and handling move: a skin must keep every one its base has, where its base has it
MOVING = {'mag', 'charge', 'bolt', 'cocker', 'slide', 'cylinder', 'hammer', 'lhammer', 'hammerl', 'hammerr', 'pump',
          'lever', 'hinge', 'shell1', 'shell2', 'cover', 'box', 'barrels', 'kat_blade', 'needle', 'jar'}
MOVING_RE = re.compile(r'^belt_\d+$')
PIVOT_TOL = 0.02   # metres: a moving part's middle may sit this far from the base's (a reshaped mag, a thicker slide)

# the parts each kind of gun must have as its own pieces (any one of a tuple will do)
TYPES = {
    'rifle':    ['body', 'barrel', 'mag', 'charge', 'grip', ('sight', 'fsight', 'scope', 'rail')],
    # (a skeleton / thumbhole stock with the grip in it, as on the real SVD: the grip is the stock's)
    'thumbhole': ['body', 'barrel', 'mag', 'charge', 'stock', ('sight', 'fsight', 'scope', 'rail')],
    'bolt':     ['body', 'barrel', 'bolt', 'mag', 'stock', ('scope', 'sight')],
    'pump':     ['body', 'barrel', 'pump', 'stock', ('sight', 'fsight', 'bead')],
    'lever':    ['body', 'barrel', 'lever', 'lhammer', 'stock', ('sight', 'bead')],
    'revolver': ['body', 'barrel', 'cylinder', 'hammer', 'grip', 'sight'],
    'pistol':   ['body', 'slide', 'mag', 'grip'],
    'break':    ['body', 'hinge', 'hammerl', 'hammerr', 'shell1', 'shell2', 'grip'],
    'lmg':      ['body', 'barrel', 'mag', 'cover', 'grip', 'stock'],
    'minigun':  ['body', 'barrels', 'box', 'grip'],
    'nailgun':  ['body', 'mag', 'grip'],
    'water':    ['body', 'tank', 'pump', 'grip'],
    'akimbo':   ['body', 'mag', 'cocker', 'grip'],
    'katana':   ['kat_blade', 'kat_guard', 'kat_tsuka'],
}
GUN_TYPE = {
    'ar': 'rifle', 'smg': 'rifle', 'burst': 'rifle', 'dmr': 'thumbhole', 'autoshot': 'rifle', 'redline': 'rifle',
    'sniper': 'bolt', 'shotgun': 'pump', 'lever': 'lever', 'revolver': 'revolver', 'pistol': 'pistol',
    'sawnoff': 'break', 'lmg': 'lmg', 'minigun': 'minigun', 'nailgun': 'nailgun', 'water': 'water', 'akimbo': 'akimbo',
    'katana': 'katana',
    # (the gimmick and premium weapons keep their own logic: the marble jar, the chicken launcher, the tennis hopper,
    # the scythe's two forms, melee props ... no contract beyond their own moving parts)
}


def node_of(piece_name):
    n = piece_name.lower()
    m = re.match(r'^(.+?)_wz', n)
    return m.group(1) if m else n.split('__')[0]


def nodes_of(entry):
    """{node: (lo, hi)} from an export_report entry (its pieces' boxes, file frame metres)"""
    out = {}
    for p in entry.get('pieces', []):
        nd = node_of(p['name'])
        lo, hi = p['lo'], p['hi']
        if nd in out:
            a, b = out[nd]
            out[nd] = ([min(x, y) for x, y in zip(a, lo)], [max(x, y) for x, y in zip(b, hi)])
        else:
            out[nd] = (list(lo), list(hi))
    return out


def is_moving(nd): return nd in MOVING or bool(MOVING_RE.match(nd))


def check(report, name):
    """problems with one exported model (its report key, e.g. 'w_ar' or 'w_ar@ar_toy'): [str]"""
    e = report.get(name)
    if not e: return ['not in the report']
    key = name[2:] if name.startswith('w_') else name
    base = key.split('@')[0]
    mine = nodes_of(e)
    out = []
    t = GUN_TYPE.get(base)
    if t:
        for need in TYPES[t]:
            opts = need if isinstance(need, tuple) else (need,)
            if not any(o in mine for o in opts):
                out.append('no %s part (%s)' % ('/'.join(opts), t))
    if '@' in key:
        b = report.get('w_' + base)
        if b:
            theirs = nodes_of(b)
            for nd, (lo, hi) in theirs.items():
                if not is_moving(nd): continue
                if nd not in mine:
                    out.append('lacks the base\'s moving part %s' % nd)
                    continue
                c0 = [(x + y) / 2 for x, y in zip(lo, hi)]
                l1, h1 = mine[nd]
                c1 = [(x + y) / 2 for x, y in zip(l1, h1)]
                d = sum((x - y) ** 2 for x, y in zip(c0, c1)) ** 0.5
                if d > PIVOT_TOL:
                    out.append('moving part %s sits %.0f mm off the base\'s' % (nd, d * 1000))
    return out


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    rp = os.path.join(here, '..', '..', 'roblox', 'assets', 'weapons-kit', 'export_report.json')
    report = json.load(open(rp))
    bad = 0
    for name in sorted(report):
        p = check(report, name)
        if p:
            bad += 1
            print('PART CONTRACT %-32s %s' % (name, '; '.join(p)))
    print('%d of %d models with notes' % (bad, len(report)))
