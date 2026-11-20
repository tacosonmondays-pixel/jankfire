# Bought VFX pack effects -> templates in ReplicatedStorage.JankfireVfx (the VFX session, 20 Nov 2026). Reads the pack's
# .rbxm OFFLINE (rbxfull/rbxlib: data only, nothing in it runs), keeps the chosen effects as compact JSON (defaults left out)
# and writes one small Luau builder to paste into Studio's command bar (Edit). The raw pack files and anything built from
# them stay out of git (the sellers' content); only this tool is here.
#   py -I pack_templates.py <pack.rbxm> <out.luau> "<path suffix>=<TemplateName>" ...
# Every built template gets the black-backed texture rule (black_fix.luau; ids in black_backed.json): a texture drawn on an
# opaque black square shows the square when its emitter's LightEmission is under 1, so those emitters get LightEmission 1
# and are kept quiet through Brightness and transparency instead (found by kill-effects on Static, v1133).
import sys, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rbxfull

# options: --root=<Service>.<Folder> (default ReplicatedStorage.JankfireVfx; the practice loop builds teachers into
# ServerStorage.VfxPractice so they never ship); a pick "#<n>=Name" takes the n-th Part under the pack's top folder (for
# packs whose effects are all called "VFXTemplate")
args = [a for a in sys.argv[1:] if not a.startswith('--')]
opts = dict(a[2:].split('=', 1) for a in sys.argv[1:] if a.startswith('--') and '=' in a)
ROOT_SVC, ROOT_NAME = opts.get('root', 'ReplicatedStorage.JankfireVfx').split('.', 1)
src, out = args[0], args[1]
picks = [a.split('=', 1) for a in args[2:]]
inst, parent = rbxfull.read(src)
kids = {}
for c, p in parent.items(): kids.setdefault(p, []).append(c)


def nm(r):
    v = inst[r]['props'].get('Name'); return v.decode('utf-8', 'replace') if isinstance(v, bytes) else str(v)


def path(r):
    o = [nm(r)]
    while r in parent and parent[r] in inst:
        r = parent[r]; o.append(nm(r))
    return '/'.join(reversed(o))


R = lambda x: round(x, 3)
ENUMS = {'Orientation': 'ParticleOrientation', 'FlipbookLayout': 'ParticleFlipbookLayout', 'FlipbookMode': 'ParticleFlipbookMode',
         'EmissionDirection': 'NormalId', 'Shape': 'ParticleEmitterShape', 'ShapeStyle': 'ParticleEmitterShapeStyle',
         'ShapeInOut': 'ParticleEmitterShapeInOut', 'TextureMode': 'TextureMode'}
SKIP = {'Name', 'AttributesSerialize', 'Tags', 'SourceAssetId', 'UniqueId', 'HistoryId', 'Capabilities', 'DefinesCapabilities',
        'Archivable', 'ScriptGuid', 'Source', 'Attachment0', 'Attachment1', 'Visible', 'Axis', 'SecondaryAxis'}
ALLOWED = {'ParticleEmitter', 'Attachment', 'Part', 'MeshPart', 'Beam', 'Trail', 'PointLight'}
DEFAULTS = {'Acceleration': ['V3', 0.0, 0.0, 0.0], 'Drag': 0.0, 'EmissionDirection': ['E', 'NormalId', 1], 'FlipbookBlendFrames': True,
            'FlipbookSizeX': 1, 'FlipbookSizeY': 1, 'FlipbookStartRandom': False, 'Shape': ['E', 'ParticleEmitterShape', 0],
            'ShapeInOut': ['E', 'ParticleEmitterShapeInOut', 0], 'ShapePartial': 1.0, 'ShapeStyle': ['E', 'ParticleEmitterShapeStyle', 0],
            'Squash': ['NS', [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]], 'TimeScale': 1.0, 'VelocityInheritance': 0.0, 'WindAffectsDrag': False,
            'LockedToPart': False, 'RotSpeed': ['NR', 0.0, 0.0], 'Rotation': ['NR', 0.0, 0.0], 'ZOffset': 0.0, 'LightInfluence': 0.0,
            'FlipbookLayout': ['E', 'ParticleFlipbookLayout', 0], 'FlipbookMode': ['E', 'ParticleFlipbookMode', 0], 'Enabled': False,
            'FlipbookFramerate': ['NR', 1.0, 1.0], 'Brightness': 1.0, 'Orientation': ['E', 'ParticleOrientation', 0]}
ATTRS = ('EmitCount', 'EmitDelay', 'EmitDuration', 'TimeScale_Start', 'TimeScale_End', 'TimeScale_Duration')


def enc(k, v):
    if isinstance(v, bool) or isinstance(v, (int, float)): return R(v) if isinstance(v, float) else v
    if isinstance(v, bytes): return v.decode('utf-8', 'replace')
    if isinstance(v, tuple):
        t = v[0]
        if t == 'Color3': return ['C3', R(v[1]), R(v[2]), R(v[3])]
        if t == 'Vector2': return ['V2', R(v[1]), R(v[2])]
        if t == 'Vector3': return ['V3', R(v[1]), R(v[2]), R(v[3])]
        if t == 'NumberRange': return ['NR', R(v[1]), R(v[2])]
        if t == 'NumberSequence': return ['NS', [[R(a), R(b), R(c)] for a, b, c in v[1]]]
        if t == 'ColorSequence': return ['CS', [[R(a), R(r), R(g), R(b)] for a, r, g, b, e in v[1]]]
        if t == 'CFrame':
            rot = v[4]
            if isinstance(rot, tuple) and rot and rot[0] == 'id': return ['CF', R(v[1]), R(v[2]), R(v[3])]
            return ['CF', R(v[1]), R(v[2]), R(v[3])] + [round(a, 5) for a in rot]
        if t == 'Enum':
            e = ENUMS.get(k)
            return ['E', e, v[1]] if e else None
    return None


def node(r, top_name=None):
    o = inst[r]; cls = o['class']
    if cls not in ALLOWED: return None
    p = {}
    for k, v in o['props'].items():
        if k in SKIP: continue
        if cls in ('Part', 'MeshPart') and k not in ('CFrame',): continue
        if cls == 'Attachment' and k != 'CFrame': continue
        e = enc(k, v)
        if e is None: continue
        if k == 'Enabled' and cls == 'ParticleEmitter': e = False
        if k in DEFAULTS and DEFAULTS[k] == e: continue  # (defaults left out: a new instance has them)
        if k in ('FlipbookIncompatible',): continue
        p[k] = e
    a = {k: float(v) for k, v in rbxfull.attrs(o['props'].get('AttributesSerialize', b'')).items() if k in ATTRS and isinstance(v, (int, float))}
    ch = [x for x in (node(c) for c in kids.get(r, [])) if x]
    d = {'c': cls, 'n': top_name or nm(r), 'p': p}
    if a: d['a'] = a
    if ch: d['k'] = ch
    return d


data = []
for suffix, tname in picks:
    if suffix.startswith('#'):
        tops = [r for r in inst if parent.get(r) not in inst]
        parts = [k for k in kids.get(tops[0], []) if inst[k]['class'] in ('Part', 'MeshPart')]
        n = int(suffix[1:])
        hits = [parts[n - 1]] if 0 < n <= len(parts) else []
    else:
        hits = [r for r in inst if path(r).endswith(suffix) and inst[r]['class'] in ('Part', 'MeshPart')]
    if not hits: print('NOT FOUND', suffix); continue
    data.append(node(hits[0], tname))
js = json.dumps(data, separators=(',', ':'))
assert ']==]' not in js
lua = '''local data = game:GetService("HttpService"):JSONDecode([==[''' + js + ''']==])
local root = game:GetService("%ROOTSVC%"):FindFirstChild("%ROOTNAME%") or Instance.new("Folder")
root.Name = "%ROOTNAME%"; root.Parent = game:GetService("%ROOTSVC%")
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
local bad = 0
local function build(d, parentInst)
	local i = Instance.new(d.c)
	i.Name = d.n
	for k, v in d.p do
		local x = val(v)
		if x ~= nil then if not pcall(function() (i :: any)[k] = x end) then bad += 1 end end
	end
	if i:IsA("BasePart") then i.Anchored = true; i.CanCollide = false; i.CanQuery = false; i.CanTouch = false; i.Transparency = 1; i.CastShadow = false end
	if d.a then for k, v in d.a do i:SetAttribute(k, v) end end
	if d.k then for _, c in d.k do build(c, i) end end
	i.Parent = parentInst
	return i
end
local made = {}
for _, d in data do
	local old = root:FindFirstChild(d.n)
	if old then old:Destroy() end
	local t = build(d, root)
	for _, x in t:GetDescendants() do
		if (x:IsA("Beam") or x:IsA("Trail")) and not x.Attachment0 then
			local at = {} for _, y in x.Parent:GetChildren() do if y:IsA("Attachment") then table.insert(at, y) end end
			if #at >= 2 then x.Attachment0 = at[1]; x.Attachment1 = at[2] end
		end
	end
	table.insert(made, d.n)
end
return #made .. " templates (" .. bad .. " props skipped): " .. table.concat(made, ", ")
'''
bb = json.load(open(os.path.join(HERE, 'black_backed.json'), encoding='utf-8'))
rule = open(os.path.join(HERE, 'black_fix.luau'), encoding='utf-8').read()
rule = rule.replace('%BLACK%', ', '.join('"%s"' % i for i in bb['black'])).replace('%DARK%', ', '.join('"%s"' % i for i in bb.get('dark_too', []))).replace('%DIM%', ', '.join('"%s"' % i for i in bb.get('dim', [])))
lua = lua.replace('local made = {}', rule + 'local made = {}', 1).replace('\ttable.insert(made, d.n)', '\tfixTree(t)\n\ttable.insert(made, d.n)', 1)
assert 'fixTree(t)' in lua
lua = lua.replace('%ROOTSVC%', ROOT_SVC).replace('%ROOTNAME%', ROOT_NAME)
open(out, 'w', encoding='utf-8', newline='\n').write(lua)
print('bytes', len(lua), 'effects', len(data))
