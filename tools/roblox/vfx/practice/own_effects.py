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
}
OR = {'cam': 0, 'camup': 1, 'par': 2, 'perp': 3}
DIR = {'right': 0, 'top': 1, 'back': 2, 'left': 3, 'bottom': 4, 'front': 5}
FB = {'none': 0, '2x2': 1, '4x4': 2, '8x8': 3}
MODE = {'loop': 0, 'one': 1, 'ping': 2, 'random': 3}


def hexc(h):
    h = h.lstrip('#')
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


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


ROUNDS = {1: r1}
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
