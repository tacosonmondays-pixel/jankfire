--!strict
-- the katana's moves as everyone sees them (docs/KATANA.md). the server decides all of it (server/Katana.luau, Rules):
--   the edge meter     five small bars inside the weapon plate, where a gun's ammo count goes, while your katana is
--                      out. no text. they fill ice blue with what you parry; full, they glow and a soft ring plays
--   the slash wave     the bound key (Settings > KEYBINDS "KATANA SLASH WAVE": Q, D-pad left; the phone's WAVE button)
--                      with the meter full: your slash and the crescent at once, everyone else's from the server's Fx
--                      "wave"; its hits ("waveHit") and where it breaks ("waveEnd")
--   the crit return    Fx "crit": a sharp flash at the blade, a bright line home to the shooter, its own recording
--   others' guards     a held guard stays up on their bodies (ThirdPerson.holdKat) until their "guardEnd"
-- Studio photos: the workspace attribute FxTimeScale freezes these too (0), like Fx.luau's
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local T = require(script.Parent:WaitForChild("Theme")) :: any
local H = require(script.Parent:WaitForChild("FightHud")) :: any
local VM = require(script.Parent:WaitForChild("Viewmodel")) :: any
local Fx = require(script.Parent:WaitForChild("Fx")) :: any
local Sfx = require(script.Parent:WaitForChild("Sfx")) :: any
local Binds = require(script.Parent:WaitForChild("Binds")) :: any
local Keys = require(script.Parent:WaitForChild("Keys")) :: any
local TP: any = nil
do
	local ok, m = pcall(require, script.Parent:WaitForChild("ThirdPerson"))
	if ok then TP = m end
end
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local FxR = Remotes:WaitForChild("Fx") :: RemoteEvent
local WaveR = Remotes:WaitForChild("KatanaWave", 20) :: RemoteEvent?

local me = Players.LocalPlayer
local camera = workspace.CurrentCamera
local S = Weapons.S
local P, WV = Weapons.PARRY, Weapons.WAVE
local ICE = Color3.fromRGB(159, 232, 255) -- the katana's accent (Weapons.list.parry.color)
local ICE_HOT = Color3.fromRGB(222, 247, 255) -- its bright core
local ICE_DEEP = Color3.fromRGB(96, 170, 214) -- the trailing body
local TEX = {
	core = "rbxassetid://72229869149513", -- a Beam core: v runs across it (Fx's tracer)
	glow = "rbxassetid://107753175681578", -- a soft round glow
	sparkle = "rbxassetid://118739981349944", -- four points
	streak = "rbxassetid://127914373549121", -- a soft white streak
}

-- the effects' own clock: FxTimeScale 0 freezes it for a photo (Studio)
local ts = 1
local function readTs()
	local v = workspace:GetAttribute("FxTimeScale")
	ts = if type(v) == "number" then math.max(0, v) else 1
end
readTs()
workspace:GetAttributeChangedSignal("FxTimeScale"):Connect(readTs)
local clock = 0

local folder = Instance.new("Folder")
folder.Name = "KatanaFx"
folder.Parent = workspace

local function ns(...: number): NumberSequence
	local a = { ... }
	local kp = {}
	for i = 1, #a, 2 do table.insert(kp, NumberSequenceKeypoint.new(a[i], a[i + 1])) end
	return NumberSequence.new(kp)
end
local function nr(a: number, b: number?): NumberRange return NumberRange.new(a, b or a) end
local function cs(a: Color3, b: Color3?): ColorSequence return if b then ColorSequence.new(a, b) else ColorSequence.new(a) end

-- a one-shot burst at a point: an Attachment in a part-less spot (Terrain), its emitters cleared after `life`
local emitters: { ParticleEmitter } = {}
local function burstAt(at: Vector3, list: { { [string]: any } }, life: number)
	local a = Instance.new("Attachment")
	a.WorldPosition = at
	a.Parent = workspace.Terrain
	for _, spec in list do
		local e = Instance.new("ParticleEmitter")
		e.Enabled = false
		e.LightEmission, e.LightInfluence = 1, 0
		e.TimeScale = ts
		local n = 0
		for k, v in spec do if k == "n" then n = v elseif k == "cf" then a.WorldCFrame = v else (e :: any)[k] = v end end
		e.Parent = a
		table.insert(emitters, e)
		e:Emit(n)
	end
	task.delay(life + 0.6, function()
		for _, e in a:GetChildren() do
			local i = table.find(emitters, e :: any)
			if i then table.remove(emitters, i) end
		end
		a:Destroy()
	end)
end
workspace:GetAttributeChangedSignal("FxTimeScale"):Connect(function() for _, e in emitters do e.TimeScale = ts end end)

-- a light that pops and fades on the effect clock
type Pop = { l: PointLight, a: Attachment, t: number, life: number, b: number }
local pops: { Pop } = {}
local function lightPop(at: Vector3, color: Color3, bright: number, range: number, life: number)
	local a = Instance.new("Attachment")
	a.WorldPosition = at
	a.Parent = workspace.Terrain
	local l = Instance.new("PointLight")
	l.Color, l.Brightness, l.Range, l.Shadows = color, bright, range, false
	l.Parent = a
	table.insert(pops, { l = l, a = a, t = 0, life = life, b = bright })
end

-- (Studio photos) the player attribute KatanaFreeze = "crit" or "wave" stops the effect clocks (this script's and Fx's,
-- through FxTimeScale on this client only) a moment into the next crit flash or wave flight (KatanaFreezeAt: how many
-- seconds into the flash or the flight)
local function freezeSoon(kind: string, after: number)
	if not RunService:IsStudio() or me:GetAttribute("KatanaFreeze") ~= kind then return end
	local at = tonumber(me:GetAttribute("KatanaFreezeAt"))
	task.delay(if at and kind == "wave" then after - 0.16 + at elseif at then at else after, function() workspace:SetAttribute("FxTimeScale", 0) end)
end

-- ------------------------------------------------------------------ the crit return
local lastCrit: { [any]: number } = {}
local function onCrit(f: any)
	local from = if typeof(f.from) == "Vector3" then f.from else nil
	local to = if typeof(f.to) == "Vector3" then f.to else nil
	if not from then return end
	local mine = f.by == me.UserId
	local dir = if to and (to - from).Magnitude > 0.1 then (to - from).Unit else camera.CFrame.LookVector
	-- (the blade, between you and the shooter; your own a stride further out and smaller: it's right at your eye)
	local at = from + dir * (if mine then 3.2 else 1.6) + Vector3.new(0, if mine then 0.9 else 0.6, 0)
	local k = if mine then 0.5 else 1
	local key = f.by or f.model or "?"
	local now = os.clock()
	local again = lastCrit[key] ~= nil and now - (lastCrit[key] :: number) < 0.07 -- (a spray's 2nd, 3rd bullet in one swing)
	lastCrit[key] = now
	-- the line home: hot white with an ice-blue core, thicker and longer-lived than a perfect parry's
	if to then
		Fx.tracer(at, to, Color3.new(1, 1, 1), 0.11 * S, 0.24)
		Fx.tracer(at, to, ICE, 0.045 * S, 0.45)
	end
	if not again then
		-- the sharp flash: a four-point star, a soft ice halo, hard white streaks thrown back the way the bullets came
		burstAt(at, {
			{ n = 1, Texture = TEX.sparkle, Size = ns(0, 2.4 * k, 0.35, 3.1 * k, 1, 0.4 * k), Lifetime = nr(0.13), Speed = nr(0),
				Rotation = nr(0, 45), Color = cs(Color3.new(1, 1, 1)), Transparency = ns(0, 0, 0.6, 0.1, 1, 1), Brightness = 4 },
			{ n = 1, Texture = TEX.glow, Size = ns(0, 2.5 * k, 1, 5.5 * k), Lifetime = nr(0.2), Speed = nr(0),
				Color = cs(ICE), Transparency = ns(0, if mine then 0.4 else 0.15, 1, 1), Brightness = if mine then 1.4 else 2 },
			{ n = 14, Texture = TEX.streak, Size = ns(0, 0.35, 1, 0.05), Lifetime = nr(0.1, 0.2), Speed = nr(40, 75),
				SpreadAngle = Vector2.new(28, 28), Orientation = Enum.ParticleOrientation.VelocityParallel,
				cf = CFrame.lookAt(at, at + dir) * CFrame.Angles(-math.pi / 2, 0, 0),
				Color = cs(Color3.new(1, 1, 1), ICE), Transparency = ns(0, 0, 1, 1), Drag = 3, Brightness = 3 },
		}, 0.25)
		lightPop(at, ICE_HOT, if mine then 2 else 3.2, 18, 0.18)
		Fx.sparks(at, dir, 30, 0.2)
		freezeSoon("crit", 0.035)
	else
		Fx.sparks(at, dir, 10, 0.12)
	end
	if not again or now - (lastCrit["snd" .. tostring(key)] or 0) > 0.09 then
		lastCrit["snd" .. tostring(key)] = now
		Sfx.play("crit_return", if mine then nil else at, if again then 0.7 else nil)
	end
	if mine then
		VM.hitStop = if again then 0.03 else 0.16
		VM.jolt(if again then 1.2 else 4)
		if not again then H.flash(0.42, 0.14, ICE_HOT) end
	end
end

-- ------------------------------------------------------------------ the slash wave
-- the crescent: an arc of camera-facing beams (a hot core, an ice glow, a dimmer body a little behind), its tips
-- swept back and lifted, rolled a little like a slash; frost motes shed behind it; a light rides with it
local HALF = WV.width / 2
local PHI = math.rad(58) -- (how far round the arc goes from the middle to a tip)
local R = HALF / math.sin(PHI)
local BACK = R * (1 - math.cos(PHI))
local LIFT = 0.12 * WV.width
local K = (4 / 3) * math.tan(PHI / 4) * R -- (a Bezier's handle for an arc that wide)
local ROLL = math.rad(9)

type Wave = {
	id: number?, mine: boolean, from: Vector3, dir: Vector3, len: number, speed: number, t0: number,
	part: Part, beams: { Beam }, emit: { ParticleEmitter }, light: PointLight, fly: Attachment?,
	ended: boolean, endT: number, why: string?, normal: Vector3?, born: number,
}
local waves: { Wave } = {}

local function attach(parent: BasePart, pos: Vector3, x: Vector3): Attachment
	local a = Instance.new("Attachment")
	local z = x:Cross(Vector3.yAxis).Unit -- (a square frame: the Beam bends along the attachment's X)
	a.CFrame = CFrame.fromMatrix(pos, x, z:Cross(x).Unit, z)
	a.Parent = parent
	return a
end
local function arcBeams(p: BasePart, z: number, color: Color3, w0: number, w1: number, tr0: number, tr1: number, bright: number, emission: number, out: { Beam })
	local c1 = attach(p, Vector3.new(0, 0, z), Vector3.new(-1, 0, 0))
	local c2 = attach(p, Vector3.new(0, 0, z), Vector3.new(1, 0, 0))
	local tipX, tipZ = HALF, z + BACK
	local tx, tz = math.cos(PHI), math.sin(PHI) -- (the arc's way at its tip: sideways, swept back)
	local l = attach(p, Vector3.new(-tipX, LIFT, tipZ), Vector3.new(-tx, 0.25, tz).Unit)
	local r = attach(p, Vector3.new(tipX, LIFT, tipZ), Vector3.new(tx, 0.25, tz).Unit)
	for _, pair in { { c1, l }, { c2, r } } do
		local b = Instance.new("Beam")
		b.Attachment0, b.Attachment1 = pair[1], pair[2]
		b.CurveSize0, b.CurveSize1 = K, K
		b.FaceCamera = true
		b.Segments = 20
		b.Width0, b.Width1 = w0, w1
		b.Color = cs(color)
		b.Transparency = ns(0, tr0, 1, tr1)
		b.Texture = TEX.core
		b.TextureMode = Enum.TextureMode.Stretch
		b.LightEmission, b.LightInfluence, b.Brightness = emission, 0, bright
		b.Parent = p
		table.insert(out, b)
	end
end

local function makeWave(from: Vector3, dir: Vector3, len: number, speed: number, startIn: number, mine: boolean, id: number?): Wave
	local p = Instance.new("Part")
	p.Name = "ColdFront"
	p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch, p.CastShadow = true, false, false, false, false
	p.Transparency = 1
	p.Size = Vector3.new(WV.width * 0.9, 1.2, 1.5)
	p.CFrame = CFrame.lookAt(from, from + dir)
	local beams: { Beam } = {}
	arcBeams(p, 1.4, ICE_DEEP, 2.6, 0.15, 0.62, 0.9, 1, 0.7, beams) -- the body, trailing
	arcBeams(p, 0.5, ICE, 4.4, 0.3, 0.38, 0.75, 1.6, 1, beams) -- the glow
	arcBeams(p, 0, ICE_HOT, 1.25, 0.08, 0, 0.25, 2.4, 1, beams) -- the edge
	local em: { ParticleEmitter } = {}
	for _, spec in {
		{ Texture = TEX.glow, Rate = 90, Lifetime = nr(0.3, 0.55), Speed = nr(3, 9), Size = ns(0, 0.45, 1, 0), Color = cs(ICE, ICE_HOT), Transparency = ns(0, 0.3, 1, 1) },
		{ Texture = TEX.sparkle, Rate = 45, Lifetime = nr(0.25, 0.45), Speed = nr(2, 6), Size = ns(0, 0.5, 1, 0), Color = cs(ICE_HOT), Transparency = ns(0, 0.1, 1, 1), RotSpeed = nr(-200, 200) },
	} :: { { [string]: any } } do
		local e = Instance.new("ParticleEmitter")
		e.LightEmission, e.LightInfluence = 1, 0
		e.EmissionDirection = Enum.NormalId.Back
		e.Shape = Enum.ParticleEmitterShape.Box
		e.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
		e.SpreadAngle = Vector2.new(25, 25)
		e.Drag = 4
		e.TimeScale = ts
		for k, v in spec do (e :: any)[k] = v end
		e.Parent = p
		table.insert(em, e)
		table.insert(emitters, e)
	end
	local light = Instance.new("PointLight")
	light.Color, light.Brightness, light.Range, light.Shadows = ICE, 1.3, 16, false
	light.Parent = p
	p.Parent = folder
	-- the flight's whoosh rides with it (a positional copy: Sfx.play puts it on an attachment we can move)
	local fly: Attachment? = nil
	task.delay(math.max(0, startIn), function()
		local s = Sfx.play("wave_fly", from)
		if s and s.Parent and s.Parent:IsA("Attachment") then fly = s.Parent :: Attachment end
	end)
	local w: Wave = {
		id = id, mine = mine, from = from, dir = dir, len = len, speed = speed, t0 = clock + startIn, part = p, beams = beams,
		emit = em, light = light, fly = nil, ended = false, endT = 0, why = nil, normal = nil, born = clock,
	}
	task.delay(math.max(0, startIn) + 0.05, function() w.fly = fly end)
	table.insert(waves, w)
	return w
end

-- where it breaks: a wall or a guard (a burst of ice shards, a flash, the recording); the end of its range (it just
-- fades); after its last victim (a smaller burst)
local function breakFx(at: Vector3, dir: Vector3, normal: Vector3?, why: string)
	if why == "range" then return end
	local n = normal or -dir
	burstAt(at, {
		{ n = 1, Texture = TEX.glow, Size = ns(0, 3, 1, 9), Lifetime = nr(0.24), Speed = nr(0), Color = cs(ICE_HOT, ICE), Transparency = ns(0, 0.1, 1, 1), Brightness = 2 },
		{ n = 28, Texture = TEX.streak, Size = ns(0, 0.5, 1, 0.05), Lifetime = nr(0.15, 0.32), Speed = nr(25, 55), SpreadAngle = Vector2.new(70, 70),
			Orientation = Enum.ParticleOrientation.VelocityParallel, cf = CFrame.lookAt(at, at + n) * CFrame.Angles(-math.pi / 2, 0, 0),
			Color = cs(Color3.new(1, 1, 1), ICE), Transparency = ns(0, 0, 1, 1), Drag = 5, Acceleration = Vector3.new(0, -30, 0), Brightness = 2.5 },
		{ n = 22, Texture = TEX.sparkle, Size = ns(0, 0.55, 1, 0), Lifetime = nr(0.3, 0.6), Speed = nr(8, 22), SpreadAngle = Vector2.new(80, 80),
			cf = CFrame.lookAt(at, at + n) * CFrame.Angles(-math.pi / 2, 0, 0), Color = cs(ICE_HOT), Transparency = ns(0, 0, 1, 1), Drag = 3,
			RotSpeed = nr(-300, 300), Acceleration = Vector3.new(0, -14, 0) },
	}, 0.6)
	lightPop(at, ICE, 3, 22, 0.3)
	Sfx.play("wave_wall", at)
end

local function endWave(w: Wave, why: string, at: Vector3?, normal: Vector3?)
	if w.ended then return end
	w.ended, w.endT, w.why = true, clock, why
	for _, e in w.emit do e.Enabled = false end
	local p = at or w.part.Position
	if at then w.part.CFrame = CFrame.lookAt(at, at + w.dir) * CFrame.Angles(0, 0, ROLL) end
	breakFx(p, w.dir, normal or w.normal, why)
end

local function hitFx(at: Vector3, dir: Vector3)
	burstAt(at, {
		{ n = 1, Texture = TEX.glow, Size = ns(0, 2, 1, 5), Lifetime = nr(0.18), Speed = nr(0), Color = cs(ICE_HOT), Transparency = ns(0, 0.1, 1, 1), Brightness = 2 },
		{ n = 16, Texture = TEX.streak, Size = ns(0, 0.4, 1, 0.05), Lifetime = nr(0.12, 0.25), Speed = nr(30, 55), SpreadAngle = Vector2.new(40, 40),
			Orientation = Enum.ParticleOrientation.VelocityParallel, cf = CFrame.lookAt(at, at + dir) * CFrame.Angles(-math.pi / 2, 0, 0),
			Color = cs(Color3.new(1, 1, 1), ICE), Transparency = ns(0, 0, 1, 1), Drag = 4, Brightness = 2.5 },
	}, 0.3)
	Sfx.play("wave_hit", at)
end

-- the wave's path: the same rules as the server's (Katana.cast), from your own chest
local mapParams = RaycastParams.new()
mapParams.FilterType = Enum.RaycastFilterType.Include
local function castMap(o: Vector3, d: Vector3, len: number): RaycastResult?
	local map = workspace:FindFirstChild("Map")
	if not map then return nil end
	mapParams.FilterDescendantsInstances = { map }
	return workspace:Raycast(o, d * len, mapParams)
end
local function aimDir(look: Vector3): Vector3?
	local u = look.Unit
	local flat = Vector3.new(u.X, 0, u.Z)
	if flat.Magnitude < 1e-3 then return nil end
	local lim = math.rad(WV.pitch)
	local pitch = math.clamp(math.asin(math.clamp(u.Y, -1, 1)), -lim, lim)
	return (flat.Unit * math.cos(pitch) + Vector3.new(0, math.sin(pitch), 0)).Unit
end

local pendingMine: Wave? = nil -- (drawn on your press, waiting for the server's id)
local function castLocal(): boolean
	local ch = me.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	if not root or not hum or hum.Health <= 0 then return false end
	local dir = aimDir(camera.CFrame.LookVector)
	if not dir then return false end
	local near = castMap(root.Position, dir, 1.5)
	local from = if near then near.Position - dir * 0.2 else root.Position + dir * 1.5
	local hit = if near then near else castMap(from, dir, WV.range)
	local len = if near then 0 elseif hit then (hit.Position - from).Magnitude else WV.range
	local w = makeWave(from, dir, len, WV.speed, WV.windup, true, nil)
	w.normal = if hit then hit.Normal else nil
	if Fx.skinWave then Fx.skinWave(me, from, dir, WV.windup) end -- (a skin's layer: the Infernal katana's Crimson Slash; VFX, 20 Nov)
	pendingMine = w
	freezeSoon("wave", WV.windup + 0.16)
	-- the slash itself: your blade's backhand, your body's, the release, a cold flash
	VM.play("kat_wave") -- (the pack's Ultimate, 20 Nov 2026)
	if TP and TP.swing then TP.swing(true, "kat_wave") end
	Sfx.play("wave_cast")
	H.flash(0.16, 0.3, ICE)
	VM.jolt(-2.5)
	return true
end

local function canWave(): boolean
	if VM.wid ~= "katana" then return false end
	if me:GetAttribute("EdgeFull") ~= true then return false end
	local z = me:GetAttribute("Zone")
	if (z == "hub" and me:GetAttribute("DevArms") ~= true) or me:GetAttribute("LoadoutOpen") == true or me:GetAttribute("MenuCursor") == true then return false end
	if os.clock() < (tonumber(me:GetAttribute("KatanaCast")) or 0) then return false end
	local ch = me.Character
	return ch ~= nil and ch:FindFirstChildOfClass("Tool") == nil
end

local deniedT = -math.huge
Keys.began(function(io: InputObject, gp: boolean)
	if gp or not WaveR then return end
	if not Binds.is("wave", io) then return end
	if not canWave() then
		if VM.wid == "katana" then deniedT = os.clock() end -- (the meter's bars blink: not yet)
		return
	end
	me:SetAttribute("KatanaCast", os.clock() + WV.lock) -- (Arsenal: no swing or guard while it goes)
	if castLocal() then (WaveR :: RemoteEvent):FireServer(camera.CFrame.LookVector) end
end)

local function finiteV(v: any): boolean
	return typeof(v) == "Vector3" and v.X == v.X and v.Y == v.Y and v.Z == v.Z and v.Magnitude < 1e6
end
local function byId(id: any): Wave?
	for _, w in waves do if w.id == id then return w end end
	return nil
end

-- ------------------------------------------------------------------ what the server says
local guards: { [Instance]: number } = {} -- someone else's body -> when its held guard comes down (os.clock)
FxR.OnClientEvent:Connect(function(f: any)
	if type(f) ~= "table" then return end
	local m = if typeof(f.model) == "Instance" then f.model else nil
	if f.k == "crit" then
		onCrit(f)
	elseif f.k == "guard" then
		if m and f.by ~= me.UserId then guards[m] = os.clock() + (if type(f.hold) == "number" then math.min(f.hold, 3) else P.win) end
	elseif f.k == "guardEnd" then
		if m and f.by ~= me.UserId then guards[m] = os.clock() + math.clamp(if type(f.at) == "number" then f.at else 0, 0, 3) end
	elseif f.k == "wave" then
		if type(f.id) ~= "number" or not finiteV(f.from) or not finiteV(f.dir) or type(f.len) ~= "number" then return end
		local mine = f.by == me.UserId
		local startIn = if type(f.t0) == "number" then f.t0 - workspace:GetServerTimeNow() else 0
		if mine and pendingMine and not pendingMine.id and clock - pendingMine.born < 1.5 then
			-- yours, drawn already: take the server's id, and its length if the walls disagree
			local w = pendingMine :: Wave
			w.id, w.len = f.id, f.len
			pendingMine = nil
			return
		end
		local w = makeWave(f.from, (f.dir :: Vector3).Unit, f.len, if type(f.speed) == "number" then f.speed else WV.speed, startIn, mine, f.id)
		w.normal = if typeof(f.normal) == "Vector3" then f.normal else nil
		if Fx.skinWave and type(f.by) == "number" then Fx.skinWave(Players:GetPlayerByUserId(f.by), f.from, (f.dir :: Vector3).Unit, startIn) end
		freezeSoon("wave", math.max(0, startIn) + 0.16)
		if not mine then
			local r = m and m:FindFirstChild("HumanoidRootPart") :: BasePart?
			if r then Sfx.play("wave_cast", r.Position) end
		end
	elseif f.k == "waveHit" then
		local w = byId(f.id)
		if typeof(f.at) == "Vector3" then hitFx(f.at, if w then w.dir else camera.CFrame.LookVector) end
	elseif f.k == "waveEnd" then
		local w = byId(f.id)
		if w and f.why ~= "wall" and f.why ~= "range" and typeof(f.at) == "Vector3" then
			endWave(w, f.why, f.at, nil) -- (a guard broke it, or its last victim: it stops right there)
		elseif w and typeof(f.at) == "Vector3" and type(f.d) == "number" then
			w.len = math.min(w.len, f.d) -- (a wall: it flies on to it, the frame code breaks it there)
		end
	end
end)
-- the meter's sound: once, when it fills
me:GetAttributeChangedSignal("EdgeFull"):Connect(function()
	if me:GetAttribute("EdgeFull") == true then Sfx.play("edge_full") end
end)

-- ------------------------------------------------------------------ the meter
local N = 5
local meter: Frame? = nil
local bars: { { track: Frame, fill: Frame, edge: UIStroke } } = {}
local shown = 0 -- (the fill as drawn: it eases to the real one)
local flashT = -math.huge -- (a parry just added to it: the new part flashes white)
local lastEdge = 0
local function buildMeter(): Frame?
	local pg = me:FindFirstChildOfClass("PlayerGui")
	local g = pg and pg:FindFirstChild("JankfireFight")
	local sc = g and g:FindFirstChild("Scaled")
	local plate = sc and sc:FindFirstChild("Ammo")
	if not plate then return nil end
	local old = plate:FindFirstChild("Edge")
	if old then old:Destroy() end
	local w, gap, h = 13, 3, 5
	local f = T.new("Frame", {
		Name = "Edge", BackgroundTransparency = 1, AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -16, 0, 25),
		Size = UDim2.fromOffset(N * w + (N - 1) * gap, h), Visible = false,
	}, plate)
	table.clear(bars)
	for i = 1, N do
		local tr = T.new("Frame", {
			Name = "Bar" .. i, BorderSizePixel = 0, BackgroundColor3 = T.TRACK, BackgroundTransparency = 0.15,
			Position = UDim2.fromOffset((i - 1) * (w + gap), 0), Size = UDim2.fromOffset(w, h), ClipsDescendants = true,
		}, f)
		T.corner(tr, 2)
		local fill = T.new("Frame", { Name = "Fill", BorderSizePixel = 0, BackgroundColor3 = ICE, Size = UDim2.fromScale(0, 1) }, tr)
		T.corner(fill, 2)
		local st = T.new("UIStroke", { Color = ICE, Thickness = 1, Transparency = 1 }, tr)
		table.insert(bars, { track = tr, fill = fill, edge = st })
	end
	return f
end
me:GetAttributeChangedSignal("Edge"):Connect(function()
	local e = tonumber(me:GetAttribute("Edge")) or 0
	if e > lastEdge + 0.005 then flashT = os.clock() end
	lastEdge = e
end)

-- ------------------------------------------------------------------ every frame
RunService.RenderStepped:Connect(function(dt: number)
	local now = os.clock()
	local sdt = dt * ts
	clock += sdt
	-- others' held guards
	if TP and TP.holdKat then
		for m, untilT in guards do
			if now >= untilT or not m.Parent then guards[m] = nil else TP.holdKat(m, "guard", 0.2) end
		end
	end
	-- light pops
	for i = #pops, 1, -1 do
		local L = pops[i]
		L.t += sdt
		if L.t >= L.life then L.a:Destroy(); table.remove(pops, i) else L.l.Brightness = L.b * (1 - L.t / L.life) ^ 2 end
	end
	-- the waves in the air
	for i = #waves, 1, -1 do
		local w = waves[i]
		if w.ended then
			local k = math.clamp((clock - w.endT) / 0.16, 0, 1)
			for _, b in w.beams do
				b.Transparency = ns(0, 1 - (1 - k) * 0.9 + 0, 1, 1)
				b.Width0 *= 1 + 0.6 * sdt / 0.16
			end
			w.light.Brightness = 1.3 * (1 - k)
			if k >= 1 then
				for _, e in w.emit do local j = table.find(emitters, e); if j then table.remove(emitters, j) end end
				local p = w.part
				task.delay(0.6, function() p:Destroy() end)
				table.remove(waves, i)
			end
			continue
		end
		-- (yours, drawn on the press: the server never took it, so it fades out quietly)
		if w.mine and not w.id and clock - w.born > 0.9 then endWave(w, "range", nil, nil); continue end
		local d = (clock - w.t0) * w.speed
		if d < 0 then
			-- the windup: not out yet
			w.part.CFrame = CFrame.new(0, -5000, 0)
			continue
		end
		d = math.min(d, w.len)
		local pos = w.from + w.dir * d
		local up = if math.abs(w.dir.Y) > 0.98 then Vector3.xAxis else Vector3.yAxis
		w.part.CFrame = CFrame.lookAt(pos, pos + w.dir, up) * CFrame.Angles(0, 0, ROLL)
		-- in over the first 50 ms
		local a = math.clamp((clock - w.t0) / 0.05, 0, 1)
		if a < 1 then for j, b in w.beams do b.Transparency = ns(0, 1 - a * (1 - ({ 0.62, 0.62, 0.38, 0.38, 0, 0 })[j]), 1, 1) end
		elseif not (w.part:GetAttribute("In") == true) then
			w.part:SetAttribute("In", true)
			local base = { { 0.62, 0.9 }, { 0.62, 0.9 }, { 0.38, 0.75 }, { 0.38, 0.75 }, { 0, 0.25 }, { 0, 0.25 } }
			for j, b in w.beams do b.Transparency = ns(0, base[j][1], 1, base[j][2]) end
		end
		local fly = w.fly
		if fly and fly.Parent then fly.WorldPosition = pos end
		if d >= w.len then endWave(w, if w.len < WV.range - 0.5 then "wall" else "range", pos, w.normal) end
	end
	-- the meter: only with your katana out (outside the hub)
	if not meter or not meter.Parent then meter = buildMeter() end
	local mtr = meter
	if mtr then
		local on = VM.wid == "katana" and (me:GetAttribute("Zone") ~= "hub" or me:GetAttribute("DevArms") == true) and me.Character ~= nil
		if mtr.Visible ~= on then mtr.Visible = on end
		if on then
			local e = math.clamp(tonumber(me:GetAttribute("Edge")) or 0, 0, 1)
			shown += (e - shown) * math.min(1, dt * 12)
			if math.abs(e - shown) < 0.002 then shown = e end
			local full = me:GetAttribute("EdgeFull") == true
			local pulse = 0.5 + 0.5 * math.sin(now * 5)
			local blink = now - deniedT < 0.35 and math.floor((now - deniedT) * 12) % 2 == 0
			local fresh = math.clamp(1 - (now - flashT) / 0.25, 0, 1)
			for i, b in bars do
				local k = math.clamp(shown * N - (i - 1), 0, 1)
				b.fill.Size = UDim2.fromScale(k, 1)
				b.fill.BackgroundColor3 = if full then ICE_HOT else ICE:Lerp(Color3.new(1, 1, 1), fresh * 0.7)
				b.edge.Transparency = if full then 0.15 + 0.45 * pulse else 1
				b.track.BackgroundTransparency = if blink then 0.6 else 0.15
			end
		end
	end
end)

-- (Studio photos: the meter shown from a script) the attribute KatanaHud = true on the player keeps it built
if RunService:IsStudio() then
	me:GetAttributeChangedSignal("KatanaHud"):Connect(function() meter = buildMeter() end)
	-- (photos) KatanaClip = an Anims row: your first person plays it now (VMClipHold freezes it), and your body too
	me:GetAttributeChangedSignal("KatanaClip"):Connect(function()
		local n = me:GetAttribute("KatanaClip")
		if type(n) ~= "string" then return end
		VM.play(n)
		if TP and TP.swing and (string.sub(n, 1, 9) == "kat_light" or n == "kat_wave") then TP.swing(true, n) end
	end)
end
