# The VFX practice loop's own effects (20 Nov 2026): each category rebuilt from our own textures (roblox/assets/vfx and
# the practice uploads), aiming at a bought pack's look layer by layer. Writes a Luau builder (Edit) that puts them in
# ServerStorage.VfxPractice as O_<cat>. Same JSON shape as tools/roblox/vfx/packs/pack_templates.py.
#   py -I own_effects.py <round> <out.luau>
import sys, json

ROUND = int(sys.argv[1])
TEX = {  # our own images (ids in roblox/assets/vfx/assets.json and roblox/docs/vfx/practice/README.md)
    'glow': 107753175681578, 'ring': 136567724057402, 'spark': 73042129135061, 'sparkle': 118739981349944,
    'streak': 127914373549121, 'chips': 81145557543325, 'dust4': 123624708348895, 'smoke4': 97407536340250,
    'lumps4': 82728391412819, 'cotton8': 96781809339333, 'boom4': 101632032329716, 'boom8': 92069836286961,
    'hitstar4': 123343427727495, 'gring4': 88961349137378, 'gburst4': 113903648900633, 'arc': 119340562514320,
    # round 2 (draw_r2.py)
    'hitstar2': 110290022029129, 'crack4': 137182173760983, 'puff4': 79705209147568, 'ink4': 114628023781415,
    'thinring': 86499394153319,
    # round 2, part b (draw_r2b.py, the round-1 critic's texture fixes)
    'hitstar3': 104577603786888, 'gburst2': 109446321378868, 'gring2': 137445507815789, 'splat4': 87402093208786,
    'hairring': 77478194219067, 'hairline': 94387206333196, 'windarc': 115049111171567, 'needle': 120682326983772,
    'dot': 117163101562671,
    # round 3 (draw_r3.py, the round-2 critic's texture fixes)
    'hitstar4b': 107149707376006, 'gburst3': 107406496303416, 'hairline2': 92955374417285, 'hairring2': 108479870084917,
    'burstdisc': 83958316271562, 'windarc2': 99774065189139, 'crack2': 131926890049423, 'puff2': 117654580630043,
    'brokenring': 96951839735929, 'dagger': 104703641730305,
}
OR = {'cam': 0, 'camup': 1, 'par': 2, 'perp': 3}
DIR = {'right': 0, 'top': 1, 'back': 2, 'left': 3, 'bottom': 4, 'front': 5}
FB = {'none': 0, '2x2': 1, '4x4': 2, '8x8': 3}
MODE = {'loop': 0, 'one': 1, 'ping': 2, 'random': 3}


def hexc(h):
    h = h.lstrip('#')
    return [round(int(h[i:i + 2], 16) / 255, 3) for i in (0, 2, 4)]


def NS(*kps):  # NS((t, v[, envelope]), ...); t is the fraction of the particle's life
    return ['NS', [[k[0], k[1], k[2] if len(k) > 2 else 0.0] for k in kps]]


def CS(*kps):  # CS((t, '#rrggbb'), ...) or one colour
    if isinstance(kps[0], str):
        kps = ((0, kps[0]), (1, kps[0]))
    return ['CS', [[t] + hexc(c) for t, c in kps]]


def NR(a, b=None):
    return ['NR', a, a if b is None else b]


def em(name, tex, life, size, *, trans=None, color='#ffffff', le=1.0, bright=1.0, speed=0.001, spread=(0, 0),
       drag=0.0, accel=None, orient='cam', direction='top', flip=None, mode='one', fps=None, rot=None, rotspeed=None,
       squash=None, z=0.0, locked=False, count=1, delay=0.0, duration=0.0, startrandom=False, inout=None, rate=10):
    p = {'Texture': 'rbxassetid://%d' % TEX[tex], 'Lifetime': NR(*life) if isinstance(life, tuple) else NR(life),
         'Size': size if isinstance(size, list) else NS((0, size), (1, size)),
         'Transparency': trans or NS((0, 0), (1, 1)), 'Color': CS(color) if isinstance(color, str) else color,
         'LightEmission': le, 'Brightness': bright, 'Speed': NR(*speed) if isinstance(speed, tuple) else NR(speed),
         'SpreadAngle': ['V2', spread[0], spread[1]], 'Drag': drag, 'Orientation': ['E', 'ParticleOrientation', OR[orient]],
         'EmissionDirection': ['E', 'NormalId', DIR[direction]], 'ZOffset': z, 'LockedToPart': locked, 'Rate': rate}
    if accel:
        p['Acceleration'] = ['V3'] + list(accel)
    if flip:
        p['FlipbookLayout'] = ['E', 'ParticleFlipbookLayout', FB[flip]]
        p['FlipbookMode'] = ['E', 'ParticleFlipbookMode', MODE[mode]]
        if fps:
            p['FlipbookFramerate'] = NR(fps)
        if startrandom:
            p['FlipbookStartRandom'] = True
    if rot is not None:
        p['Rotation'] = NR(*rot) if isinstance(rot, tuple) else NR(rot)
    if rotspeed is not None:
        p['RotSpeed'] = NR(*rotspeed) if isinstance(rotspeed, tuple) else NR(rotspeed)
    if squash:
        p['Squash'] = squash
    if inout:
        p['ShapeInOut'] = ['E', 'ParticleEmitterShapeInOut', {'out': 0, 'in': 1, 'both': 2}[inout]]
    a = {'EmitCount': float(count), 'EmitDelay': float(delay)}
    if duration:
        a['EmitDuration'] = float(duration)
    return {'c': 'ParticleEmitter', 'n': name, 'p': p, 'a': a}


def att(name, kids, cf=None):
    return {'c': 'Attachment', 'n': name, 'p': {'CFrame': cf or ['CF', 0, 0, 0]}, 'k': kids}


def part(name, kids):
    return {'c': 'Part', 'n': name, 'p': {}, 'k': kids}


FADE_IN_OUT = NS((0, 1), (0.5, 0), (1, 1))
SQUASH_INK = NS((0, 0.285), (0.303, 0.45, 0.45), (0.6, 1.312, 0.241), (1, 1.613))


def r1():
    """round 1: a straight layer-for-layer rebuild of each teacher, our textures in place of the seller's"""
    E = []
    # HIT (teacher: Combat Punch-01, one 4x4 flipbook: star -> sparkle ring -> thin ring, 0.5 s)
    E.append(part('O_Hit', [att('Main', [
        em('star', 'hitstar4', 0.5, NS((0, 0.6), (0.15, 2.2), (1, 3.3)), trans=NS((0, 1), (0.08, 0), (0.35, 0), (1, 1)),
           flip='4x4', orient='perp', direction='front', rot=(-45, 45), bright=1.5, z=1, locked=True)])]))
    # GUARD BREAK (teacher: Guard break + Guard break 2: a ring flipbook widening and a starburst flipbook in front)
    E.append(part('O_Guard', [att('Main', [
        em('ring', 'gring4', 0.5, NS((0, 0.5), (0.5, 3.75), (1, 5.1)), trans=NS((0, 0), (1, 0)), flip='4x4',
           orient='perp', direction='front', rot=(-360, 360), bright=2, z=1, locked=True),
        em('burst', 'gburst4', 0.5, NS((0, 3.4), (0.4, 4.4), (0.63, 3.8), (1, 0.1)), trans=NS((0, 0), (1, 0)),
           flip='4x4', bright=3, z=4, locked=True)])]))
    # DASH (teacher: Combat dash: streaks, chips, drifting bits, rings ahead turning back, a glow; all pale, 0.2-0.6 s)
    pale = '#ecfffc'
    E.append(part('O_Dash', [
        em('lines', 'streak', (0.2, 0.6), 0.62, trans=FADE_IN_OUT, color=pale, speed=7.786, orient='par',
           direction='left', squash=NS((0, -1), (1, -1)), count=13, delay=0.11),
        em('debris', 'chips', (0.2, 0.6), NS((0, 0.234), (1, 0)), trans=FADE_IN_OUT, color=pale, speed=7.786,
           direction='left', rot=(-360, 360), rotspeed=(-1000, 1000), flip='2x2', mode='random', count=5, delay=0.11),
        em('bits down', 'sparkle', (0.2, 0.6), 0.337, trans=FADE_IN_OUT, color=pale, speed=7.786, direction='left',
           accel=(0, -4.672, 0), rot=(-360, 360), count=5, delay=0.11),
        em('bits up', 'sparkle', (0.2, 0.6), 0.337, trans=FADE_IN_OUT, color=pale, speed=7.786, direction='left',
           accel=(0, 4.672, 0), rot=(-360, 360), count=5, delay=0.11),
        att('Rings', [em('circles', 'ring', (0.2, 0.6), NS((0, 0), (0.489, 2.595, 2.076), (1, 5.191)), trans=FADE_IN_OUT,
                         color=pale, speed=5.191, spread=(6, 6), orient='perp', rot=(-360, 360), rotspeed=-250, count=9)],
            cf=['CF', 4.817, 0, 0, 0, -1, 0, 1, 0, 0, 0, 0, 1]),
        em('glow', 'glow', (0.2, 0.6), 3.114, trans=NS((0, 1), (0.5, 0.925), (1, 1)), color=pale, le=0.5,
           direction='left', rot=(-360, 360), count=9, delay=0.11)]))
    # SLASH (teacher: Combat Slash-03, a spinning wind slash: two impact flashes and four spinning arcs growing to 14-20
    # studs over 1 s, flat under the attachment)
    grey = '#737373'
    spin = dict(orient='perp', direction='bottom', inout='in', rot=(-360, 360), locked=True, z=1)
    E.append(part('O_Slash', [att('Main', [
        em('impact1', 'glow', 0.3, 2, trans=NS((0, 1), (0.2, 0), (0.8, 0), (1, 1)), color=grey, spread=(1, 1), **spin),
        em('spin2', 'arc', 1.0, NS((0, 0), (1, 14.97)), trans=NS((0, 1), (0.5, 0.869), (1, 1)), le=0.0, speed=2,
           spread=(5, 5), rotspeed=100, **spin),
        em('spin3', 'arc', 1.0, NS((0, 0), (0.487, 12.227), (1, 19.584)), trans=NS((0, 1), (0.5, 0), (1, 1)),
           color='#525252', bright=0.3, speed=(0, 9.585), spread=(1, 1), drag=9, rotspeed=100, orient='perp',
           rot=(-360, 360), locked=True, count=4, delay=0.1),
        em('spin5', 'arc', 1.0, NS((0, 0), (1, 14)), trans=NS((0, 0), (0.8, 0), (1, 1)), color=grey, le=0.75,
           speed=17.5, spread=(6, 6), rotspeed=250, **spin),
        em('impact2', 'ring', 0.3, NS((0, 2), (1, 10)), trans=NS((0, 1), (0.2, 0), (0.8, 0), (1, 1)), color=grey,
           spread=(1, 1), **spin),
        em('spin4', 'arc', 1.0, NS((0, 0), (1, 9.146)), trans=NS((0, 1), (0.2, 0), (0.8, 0), (1, 1)), color=grey,
           le=0.75, speed=17.5, spread=(6, 6), rotspeed=250, **spin),
        em('spin1', 'arc', 1.0, NS((0, 0), (1, 14)), trans=NS((0, 0), (0.8, 0), (1, 1)), color=grey, le=0.75,
           speed=17.5, spread=(6, 6), rotspeed=250, **spin)], cf=['CF', 0, -4.801, 0])]))
    # GROUND IMPACT (teacher: Combat Slam: a flat grey ring growing to 23 studs, 50 dust puffs thrown out and dragged to a
    # stop, 28 chips, a flat sparkle burst, dark-edged cloud puffs)
    E.append(part('O_Slam', [att('Attachment', [
        em('ring', 'ring', (0.55, 0.85), NS((0, 0), (1, 22.807, 4.165)), trans=NS((0, 0.3), (1, 1)), color='#6f6f6f',
           bright=2, spread=(10, 10), orient='perp', rot=(0, 1000), rotspeed=(-150, 150), count=3),
        em('dust', 'dust4', (0.45, 0.8), NS((0, 1), (1, 2.8)), trans=NS((0, 0), (1, 1)), le=0.0, speed=(35, 75),
           spread=(0, 1000), drag=10, direction='front', flip='4x4', rot=(0, 1000), count=50),
        em('chips', 'chips', (0.15, 1.45), 0.6, trans=NS((0, 0), (1, 0)), color='#d8d8d8', le=0.0, speed=(25, 50),
           spread=(1000, 1000), drag=15, flip='2x2', mode='random', rot=90, count=28),
        em('flare', 'hitstar4', (0.45, 0.65), NS((0, 1.71), (1, 8.812)), trans=NS((0, 0.3), (1, 1)), bright=2,
           spread=(1000, 1000), orient='perp', flip='4x4', rot=(0, 1000), count=2),
        em('clouds', 'cotton8', (0.65, 1.0), NS((0, 0), (0.25, 1.625, 0.687), (0.54, 2.375, 0.875), (0.885, 0.938, 0.562), (1, 0)),
           trans=NS((0, 0), (1, 0.2)), le=0.0, speed=(5, 25), spread=(45, 2323), drag=2, direction='left', flip='8x8',
           rot=(0, 1000), rotspeed=(-233, 233), count=23)])]))
    # EXPLOSION (teacher: 100+ pack #50, an anime ink blast in 0.75 s: a one-frame white flash, fast shard streaks dragged
    # and falling, dark ink blobs stretching out, orange flame bursts a beat later, bright licks, 40 dark dots, an orange ring)
    orange = '#ff8a3d'
    E.append(part('O_X', [att('Attachment', [
        em('flash', 'glow', 0.06, 20, trans=NS((0, 0.4), (1, 1)), bright=3, z=8, locked=True),
        em('shards', 'spark', 0.5, NS((0, 8.963, 2.411), (0.093, 7.193, 1.742), (0.134, 2.867, 1.499), (0.286, 1.252, 0.793), (0.517, 0.25, 0.135), (1, 0)),
           trans=NS((0, 0), (1, 0)), bright=2, speed=(145.9, 304), spread=(360, 360), drag=25, accel=(0, -85.125, 0),
           orient='par', direction='front', rot=90, count=20),
        em('ink', 'boom4', (0.1, 0.25), 5.246, trans=NS((0, 0), (1, 0)), color='#2b2b2b', le=0.0, speed=134.4,
           spread=(360, 360), drag=40, orient='par', direction='front', flip='4x4', rot=-90, squash=SQUASH_INK, z=1, count=6),
        em('flame', 'boom4', (0.08, 0.2), 5.246, trans=NS((0, 1), (0.088, 1), (0.136, 0), (1, 0)), color=orange, le=0.6,
           speed=134.4, spread=(360, 360), drag=40, orient='par', direction='front', flip='4x4', rot=-90,
           squash=SQUASH_INK, count=6),
        em('licks', 'boom8', (0.362, 0.543), NS((0, 0), (0.072, 2.104, 0.61), (0.381, 3.094, 1.246), (1, 0.78, 0.78)),
           trans=NS((0, 0), (1, 0)), color='#fff2c8', bright=2, speed=(15.8, 94.8), spread=(80, 80), drag=4.95,
           orient='par', direction='front', flip='8x8', rot=-90, squash=NS((0, 1.689), (1, 0.902)), count=4),
        em('dots', 'chips', (0.55, 0.75), NS((0, 0.65, 0.65), (1, 0)), trans=NS((0, 0), (1, 0)), color='#222222', le=0.0,
           speed=(25.4, 114.3), spread=(360, 360), drag=7, flip='2x2', mode='random', rot=(-360, 360),
           rotspeed=(-180, 180), count=40),
        em('firering', 'ring', 0.3, NS((0, 3.95), (1, 10.307)), trans=NS((0, 0), (1, 1)), color=orange, rot=(-360, 360),
           z=-0.243, count=1)])]))
    return E


def r2():
    """round 2: the round-1 critic's fixes (scores hit 4, guard 3, dash 2, slash 4, slam 3, explosion 5)"""
    E = []
    # HIT: a cel-edged star only in the first frames, then a sparse small-sparkle ring on one thin line, gone by
    # frame 11; size on the pack's straight line
    E.append(part('O_Hit', [att('Main', [
        em('star', 'hitstar3', 0.5, NS((0, 0.44), (1, 3.3)), trans=NS((0, 1), (0.08, 0), (0.35, 0), (1, 1)),
           flip='4x4', orient='perp', direction='front', rot=(-45, 45), bright=1, z=1, locked=True)])]))
    # GUARD BREAK: a solid jagged burst overdriven to white (Brightness 20) that turns into thick rings and shards and is
    # gone by 65% of life; the ring jumps out fast and fades from 45%
    E.append(part('O_Guard', [att('Main', [
        em('ring', 'gring2', 0.5, NS((0, 0.5), (0.2, 3.2), (0.5, 4.4), (1, 5.1)), trans=NS((0, 0), (0.45, 0), (0.65, 1), (1, 1)),
           flip='4x4', orient='perp', direction='front', rot=(-360, 360), bright=3, z=1, locked=True),
        em('burst', 'gburst2', 0.5, NS((0, 3.4), (0.3, 4.4), (0.55, 2), (0.65, 0), (1, 0)), trans=NS((0, 0), (1, 0)),
           color='#fff8e8', flip='4x4', bright=20, z=4, locked=True)])]))
    # DASH: hairline rings, hairline streaks, tiny dots, the glow nearly gone
    pale = '#ecfffc'
    E.append(part('O_Dash', [
        em('lines', 'hairline', (0.2, 0.6), 0.62, trans=FADE_IN_OUT, color=pale, speed=7.786, orient='par',
           direction='left', squash=NS((0, -1), (1, -1)), count=13, delay=0.11),
        em('debris', 'chips', (0.2, 0.6), NS((0, 0.234), (1, 0)), trans=FADE_IN_OUT, color=pale, speed=7.786,
           direction='left', rot=(-360, 360), rotspeed=(-1000, 1000), flip='2x2', mode='random', count=5, delay=0.11),
        em('bits down', 'dot', (0.2, 0.6), 0.15, trans=FADE_IN_OUT, color=pale, speed=7.786, direction='left',
           accel=(0, -4.672, 0), count=5, delay=0.11),
        em('bits up', 'dot', (0.2, 0.6), 0.15, trans=FADE_IN_OUT, color=pale, speed=7.786, direction='left',
           accel=(0, 4.672, 0), count=5, delay=0.11),
        att('Rings', [em('circles', 'hairring', (0.2, 0.6), NS((0, 0), (0.489, 2.595, 2.076), (1, 5.191)),
                         trans=NS((0, 1), (0.5, 0.45), (1, 1)), color=pale, speed=5.191, spread=(6, 6), orient='perp',
                         rot=(-360, 360), rotspeed=-250, count=9)],
            cf=['CF', 4.817, 0, 0, 0, -1, 0, 1, 0, 0, 0, 0, 1]),
        em('glow', 'glow', (0.2, 0.6), 3.114, trans=NS((0, 1), (0.5, 0.975), (1, 1)), color=pale, le=0.5,
           direction='left', rot=(-360, 360), count=9, delay=0.11)]))
    # SLASH: solid hot impact flashes (glow, brighter, paler), feathery open wind arcs instead of the solid crescent
    grey = '#737373'
    spin = dict(orient='perp', direction='bottom', inout='in', rot=(-360, 360), locked=True, z=1)
    E.append(part('O_Slash', [att('Main', [
        em('impact1', 'glow', 0.3, 3, trans=NS((0, 1), (0.2, 0), (0.8, 0), (1, 1)), color=grey, bright=3, spread=(1, 1), **spin),
        em('spin2', 'windarc', 1.0, NS((0, 0), (1, 14.97)), trans=NS((0, 1), (0.5, 0.869), (1, 1)), le=0.0, speed=2,
           spread=(5, 5), rotspeed=100, **spin),
        em('spin3', 'windarc', 1.0, NS((0, 0), (0.487, 12.227), (1, 19.584)), trans=NS((0, 1), (0.5, 0), (1, 1)),
           color='#525252', bright=0.3, speed=(0, 9.585), spread=(1, 1), drag=9, rotspeed=100, orient='perp',
           rot=(-360, 360), locked=True, count=4, delay=0.1),
        em('spin5', 'windarc', 1.0, NS((0, 0), (1, 14)), trans=NS((0, 0), (0.8, 0), (1, 1)), color=grey, le=0.75,
           speed=17.5, spread=(6, 6), rotspeed=250, **spin),
        em('impact2', 'glow', 0.3, NS((0, 2), (1, 10)), trans=NS((0, 1), (0.2, 0), (0.8, 0), (1, 1)), color='#bfbfbf',
           bright=3, spread=(1, 1), **spin),
        em('spin4', 'windarc', 1.0, NS((0, 0), (1, 9.146)), trans=NS((0, 1), (0.2, 0), (0.8, 0), (1, 1)), color=grey,
           le=0.75, speed=17.5, spread=(6, 6), rotspeed=250, **spin),
        em('spin1', 'windarc', 1.0, NS((0, 0), (1, 14)), trans=NS((0, 0), (0.8, 0), (1, 1)), color=grey, le=0.75,
           speed=17.5, spread=(6, 6), rotspeed=250, **spin)], cf=['CF', 0, -4.801, 0])]))
    # GROUND IMPACT: dark floor cracks that stay, big packed cartoon puffs in a belt, the ring nearly hidden, dark chips
    E.append(part('O_Slam', [att('Attachment', [
        em('crack', 'crack4', 2.0, 30, trans=NS((0, 0), (0.7, 0), (1, 1)), color='#3c3a38', le=0.0, orient='perp',
           flip='4x4', rot=(-180, 180), count=1),
        em('ring', 'ring', (0.55, 0.85), NS((0, 0), (1, 22.807, 4.165)), trans=NS((0, 0.75), (1, 1)), color='#6f6f6f',
           le=0.0, bright=1, spread=(10, 10), orient='perp', rot=(0, 1000), rotspeed=(-150, 150), count=3),
        em('dust', 'puff4', (0.45, 0.8), NS((0, 2), (1, 4.5)), trans=NS((0, 0), (1, 1)), le=0.0, speed=(35, 75),
           spread=(0, 1000), drag=10, direction='front', flip='4x4', rot=(-20, 20), count=50),
        em('chips', 'chips', (0.3, 0.8), 0.35, trans=NS((0, 0), (0.8, 0), (1, 1)), color='#2a2a2a', le=0.0, speed=(25, 50),
           spread=(1000, 1000), drag=15, flip='2x2', mode='random', rot=90, count=28),
        em('flare', 'hitstar3', (0.45, 0.65), NS((0, 1.71), (1, 8.812)), trans=NS((0, 0.3), (1, 1)), bright=2,
           spread=(1000, 1000), orient='perp', flip='4x4', rot=(0, 1000), count=2),
        em('clouds', 'puff4', (0.65, 1.0), NS((0, 0), (0.25, 2.925, 1.237), (0.54, 4.275, 1.575), (0.885, 1.688, 1.0), (1, 0)),
           trans=NS((0, 0), (1, 0.2)), le=0.0, speed=(10, 16), spread=(45, 2323), drag=4, direction='left', flip='4x4',
           rot=(-20, 20), rotspeed=(-30, 30), count=23)])]))
    # EXPLOSION: a longer soft flash, needle shards, hard black splats (LE -5 draws black), pale flame and ring
    E.append(part('O_X', [att('Attachment', [
        em('flash', 'glow', 0.1, 20, trans=NS((0, 0.3), (0.6, 0.35), (1, 1)), bright=3, z=8, locked=True),
        em('shards', 'needle', 0.5, NS((0, 8.963, 2.411), (0.093, 7.193, 1.742), (0.134, 2.867, 1.499), (0.286, 1.252, 0.793), (0.517, 0.25, 0.135), (1, 0)),
           trans=NS((0, 0), (1, 0)), bright=4, speed=(145.9, 304), spread=(360, 360), drag=25, accel=(0, -85.125, 0),
           orient='par', direction='front', count=20),
        em('ink', 'splat4', (0.1, 0.25), 4, trans=NS((0, 0), (1, 0)), le=-5.0, speed=134.4, spread=(360, 360), drag=40,
           orient='par', direction='front', flip='4x4', rot=-90, squash=SQUASH_INK, z=1, count=10),
        em('flame', 'boom4', (0.08, 0.2), 5.246, trans=NS((0, 1), (0.088, 1), (0.136, 0), (1, 0)), color='#ffe2b0', le=0.6,
           speed=134.4, spread=(360, 360), drag=40, orient='par', direction='front', flip='4x4', rot=-90,
           squash=SQUASH_INK, count=6),
        em('licks', 'boom8', (0.362, 0.543), NS((0, 0), (0.072, 2.104, 0.61), (0.381, 3.094, 1.246), (1, 0.78, 0.78)),
           trans=NS((0, 0), (1, 0)), color='#fff2c8', bright=2, speed=(15.8, 94.8), spread=(80, 80), drag=4.95,
           orient='par', direction='front', flip='8x8', rot=-90, squash=NS((0, 1.689), (1, 0.902)), count=4),
        em('dots', 'chips', (0.55, 0.75), NS((0, 0.65, 0.65), (1, 0)), trans=NS((0, 0), (1, 0)), color='#222222', le=0.0,
           speed=(25.4, 114.3), spread=(360, 360), drag=7, flip='2x2', mode='random', rot=(-360, 360),
           rotspeed=(-180, 180), count=40),
        em('firering', 'ring', 0.3, NS((0, 3.95), (1, 10.307)), trans=NS((0, 0.4), (0.4, 1), (1, 1)), color='#fff0d0',
           rot=(-360, 360), z=-0.243, count=1)])]))
    return E


def layer(E, part_name, name):
    """the emitter `name` inside effect `part_name` (for a round written as patches on the last)"""
    def walk(d):
        if d['c'] == 'ParticleEmitter' and d['n'] == name:
            return d
        for c in d.get('k', []):
            r = walk(c)
            if r:
                return r
        return None
    for d in E:
        if d['n'] == part_name:
            r = walk(d)
            if r:
                return r
    raise KeyError(part_name + '.' + name)


def drop(E, part_name, name):
    def walk(d):
        d['k'] = [c for c in d.get('k', []) if not (c['c'] == 'ParticleEmitter' and c['n'] == name)]
        for c in d['k']:
            walk(c)
    for d in E:
        if d['n'] == part_name:
            walk(d)


def tex(k):
    return 'rbxassetid://%d' % TEX[k]


def r3():
    """round 3: the round-2 critic's fixes, as patches on round 2 (scores hit 6, guard 4, dash 4, slash 6, slam 4,
    explosion 4)"""
    E = r2()
    # HIT: star only in frames 0-1 and wider than tall; a bigger ring (0.45 -> 0.9) with sparkles only early, then hair ticks
    layer(E, 'O_Hit', 'star')['p']['Texture'] = tex('hitstar4b')
    # GUARD: the burst a squat chunky body (frames 0-1) then three thin separate rings (2-5), gone by 40% of life
    g = layer(E, 'O_Guard', 'burst')['p']
    g['Texture'] = tex('gburst3')
    g['Size'] = NS((0, 3.4), (0.2, 4.4), (0.38, 3), (0.4, 0), (1, 0))
    layer(E, 'O_Guard', 'ring')['p']['Transparency'] = NS((0, 0), (0.4, 0), (0.6, 1), (1, 1))
    # DASH: the hairline across the sprite (Squash -1 widens it), one-sided single rings, fewer and smaller bits, strung
    # out along the path by a spread of speeds
    for n in ('lines', 'debris', 'bits up', 'bits down'):
        layer(E, 'O_Dash', n)['p']['Speed'] = NR(4, 12)
    layer(E, 'O_Dash', 'lines')['p']['Texture'] = tex('hairline2')
    for n in ('bits up', 'bits down'):
        layer(E, 'O_Dash', n)['p']['Size'] = NS((0, 0.08), (1, 0.08))
    c = layer(E, 'O_Dash', 'circles')['p']
    c['Texture'] = tex('hairring2')
    c['Transparency'] = NS((0, 1), (0.5, 0.6), (1, 1))
    layer(E, 'O_Dash', 'glow')['a']['EmitCount'] = 3.0
    # SLASH: a crisp ray burst for the impact (smaller), the first flash paler and brighter, arcs with a bright main stroke
    i2 = layer(E, 'O_Slash', 'impact2')['p']
    i2['Texture'] = tex('burstdisc')
    i2['Size'] = NS((0, 2), (1, 7))
    i1 = layer(E, 'O_Slash', 'impact1')['p']
    i1['Color'] = CS('#bfbfbf')
    i1['Brightness'] = 4
    for n in ('spin1', 'spin2', 'spin3', 'spin4', 'spin5'):
        layer(E, 'O_Slash', n)['p']['Texture'] = tex('windarc2')
    # GROUND: clouds thrown wide again (a flat belt), small dust back, thin pale cracks full-size from the start and
    # under the clouds, puffs shrinking instead of holed, fewer chips
    cl = layer(E, 'O_Slam', 'clouds')['p']
    cl['Speed'] = NR(5, 25)
    cl['Drag'] = 2
    cl['Texture'] = tex('puff2')
    d = layer(E, 'O_Slam', 'dust')['p']
    d['Texture'] = tex('dust4')
    d['Size'] = NS((0, 1), (1, 2.8))
    d['Transparency'] = NS((0, 0.3), (1, 1))
    k = layer(E, 'O_Slam', 'crack')['p']
    k['Texture'] = tex('crack2')
    k['Color'] = CS('#5a5650')
    k['ZOffset'] = -3
    layer(E, 'O_Slam', 'chips')['a']['EmitCount'] = 14.0
    # EXPLOSION: the flash 70% see-through like the pack, black ink painted black, the flame gone, white dagger licks,
    # a black broken swirl ring
    f = layer(E, 'O_X', 'flash')['p']
    f['Transparency'] = NS((0, 0.7), (0.6, 0.75), (1, 1))
    f['Brightness'] = 1
    ink = layer(E, 'O_X', 'ink')['p']
    ink['Color'] = CS('#000000')
    ink['LightEmission'] = 0.0
    ink['LightInfluence'] = 0.0
    drop(E, 'O_X', 'flame')
    lk = layer(E, 'O_X', 'licks')['p']
    lk['Texture'] = tex('dagger')
    lk['Color'] = CS('#ffffff')
    for n in ('FlipbookLayout', 'FlipbookMode'):
        lk.pop(n, None)
    layer(E, 'O_X', 'shards')['p']['Texture'] = tex('dagger')
    fr = layer(E, 'O_X', 'firering')['p']
    fr['Texture'] = tex('brokenring')
    fr['Color'] = CS('#000000')
    fr['LightEmission'] = 0.0
    fr['LightInfluence'] = 0.0
    fr['Transparency'] = NS((0, 0), (0.7, 0), (1, 1))
    return E


ROUNDS = {1: r1, 2: r2, 3: r3}
DATA = ROUNDS[ROUND]()
js = json.dumps(DATA, separators=(',', ':'))
assert ']==]' not in js
APPLY = '''local root = game:GetService("ServerStorage"):FindFirstChild("VfxPractice") or Instance.new("Folder")
root.Name = "VfxPractice"; root.Parent = game:GetService("ServerStorage")
local function val(v)
	if type(v) ~= "table" then return v end
	local t = v[1]
	if t == "C3" then return Color3.new(v[2], v[3], v[4])
	elseif t == "V2" then return Vector2.new(v[2], v[3])
	elseif t == "V3" then return Vector3.new(v[2], v[3], v[4])
	elseif t == "NR" then return NumberRange.new(v[2], v[3])
	elseif t == "NS" then local k = {} for _, q in v[2] do table.insert(k, NumberSequenceKeypoint.new(q[1], q[2], q[3])) end return NumberSequence.new(k)
	elseif t == "CS" then local k = {} for _, q in v[2] do table.insert(k, ColorSequenceKeypoint.new(q[1], Color3.new(q[2], q[3], q[4]))) end return ColorSequence.new(k)
	elseif t == "CF" then if #v > 4 then return CFrame.new(table.unpack(v, 2, 13)) end return CFrame.new(v[2], v[3], v[4])
	elseif t == "E" then for _, it in (Enum :: any)[v[2]]:GetEnumItems() do if it.Value == v[3] then return it end end end
	return nil
end
local bad = {}
local function build(d, parentInst)
	local i = Instance.new(d.c)
	i.Name = d.n
	for k, v in d.p do
		local x = val(v)
		if x ~= nil then if not pcall(function() (i :: any)[k] = x end) then table.insert(bad, d.n .. "." .. k) end end
	end
	if i:IsA("BasePart") then i.Anchored = true; i.CanCollide = false; i.CanQuery = false; i.CanTouch = false; i.Transparency = 1; i.CastShadow = false; i.Size = Vector3.new(1, 1, 1) end
	if d.a then for k, v in d.a do i:SetAttribute(k, v) end end
	if d.k then for _, c in d.k do build(c, i) end end
	i.Parent = parentInst
	return i
end
local made = {}
for _, d in data do
	local old = root:FindFirstChild(d.n)
	if old then old:Destroy() end
	build(d, root)
	table.insert(made, d.n)
end
return #made .. " own effects, round ROUNDNO (" .. #bad .. " props skipped " .. table.concat(bad, ",") .. "): " .. table.concat(made, ", ")
'''
lua = 'local data = game:GetService("HttpService"):JSONDecode([==[' + js + ']==])\n' + APPLY.replace('ROUNDNO', str(ROUND))
open(sys.argv[2], 'w', encoding='utf-8', newline='\n').write(lua)
print('bytes', len(lua), 'effects', len(DATA))
