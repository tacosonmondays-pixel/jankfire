--!strict
-- ZOMBIES dust in the light (27 Nov 2026, the owner: "Can you add ambiance stuff like dust particles under light?"),
-- this client only, built from HOUSE HUNT's HuntDust (the same motes and shafts, its traps already in: the VFX library's
-- soft glow at 0.11-0.13 studs and ~12% at their peak, lit by the scene (LightInfluence 1, a little emission); shafts
-- of two plain bands with 12 segments, a faint emission so they don't vanish under a lamp; every box pre-filled):
--   * motes under the lamps: a box from each of the nearest lit lamps down to the floor (the 8 nearest within 36 studs
--     of the camera), and a faint shaft under the 3 nearest. A dark area's lamps are off till the power: so are these
--   * the 2 nearest windows: a cool moonlit shaft in through the boards, motes in it
--   * your flashlight: motes in a long box ahead of your beam, left hanging in the air as you sweep; the scene lights
--     them, so they show only in the beam
--   * a dark area (ZM.DARK) before the power: a few slow, faint wisps round you, seen only in a beam
-- A slot that moves to another lamp gets a burst at once (no fade-up as you walk). Switch: workspace attribute
-- ZmDust = false (before / after shots, render cost).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local me = Players.LocalPlayer
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local ZM = require(Shared:WaitForChild("ZM"))
local D = require(script.Parent:WaitForChild("HuntDust")) :: any

local LAMPS, LAMP_R, SHAFTS, WINDOWS, WIN_R = 8, 36, 3, 2, 30
local WARM, MOON = Color3.fromRGB(255, 240, 214), Color3.fromRGB(176, 196, 232)

local function on(): boolean return me:GetAttribute("ZmOn") == true and workspace:GetAttribute("ZmDust") ~= false end
local function arena(): Model?
	local n = me:GetAttribute("ZmArena")
	local a = if type(n) == "string" then workspace:FindFirstChild(n) else nil
	return if a and a:IsA("Model") then a else nil
end

local folder = Instance.new("Folder")
folder.Name = "ZmDust"
local PARK = CFrame.new(0, -5000, 0)

-- a slot: a motes box (HuntDust.motes), maybe a shaft (HuntDust.shaft), moved from lamp to lamp
type Slot = { p: BasePart, e: ParticleEmitter, shaft: BasePart?, key: any }
local function emitterOf(p: BasePart): ParticleEmitter return p:FindFirstChildOfClass("ParticleEmitter") :: ParticleEmitter end
-- (27 Nov 2026, the owner: "The dust particles look like they're not moving!!": they settle and wander now, each one
-- turning and twinkling over its life, half again as big and bright as HOUSE HUNT's; the wander (Acceleration) is
-- nudged every couple of seconds per box, so the air seems to move)
local function kp(t: number, v: number): NumberSequenceKeypoint return NumberSequenceKeypoint.new(t, v) end
local function lively(e: ParticleEmitter)
	e.Speed = NumberRange.new(0.4, 1.0)
	e.Drag = 0.5
	e.SpreadAngle = Vector2.new(180, 180)
	e.Acceleration = Vector3.new(0, -0.08, 0)
	e.Rotation = NumberRange.new(0, 360)
	e.RotSpeed = NumberRange.new(-120, 120)
	e.Size = NumberSequence.new({ kp(0, 0.15), kp(0.25, 0.2), kp(0.5, 0.16), kp(0.75, 0.2), kp(1, 0.17) })
	e.Transparency = NumberSequence.new({ kp(0, 1), kp(0.1, 0.05), kp(0.25, 0.4), kp(0.4, 0.05), kp(0.55, 0.45), kp(0.7, 0.05), kp(0.85, 0.35), kp(1, 1) })
	e.Brightness = 2.4
	e.LightEmission = 0.5
end
local function newSlot(name: string, col: Color3, withShaft: boolean, width: number, see: number): Slot
	local p = D.motes(folder, PARK, Vector3.new(6, 8, 6), col, { name = name, rate = 3, prefill = false })
	local s: Slot = { p = p, e = emitterOf(p), shaft = nil, key = nil }
	lively(s.e)
	s.e.Enabled = false
	if withShaft then
		s.shaft = D.shaft(folder, PARK.Position, PARK.Position - Vector3.new(0, 8, 0), width, col, { name = name .. "Shaft", see = see })
		for _, b in (s.shaft :: BasePart):GetDescendants() do if b:IsA("Beam") then b.Enabled = false end end
	end
	return s
end
local function shaftOn(s: Slot, on: boolean)
	if not s.shaft then return end
	for _, b in s.shaft:GetDescendants() do if b:IsA("Beam") then b.Enabled = on end end
end
-- move a shaft (its part sits at the top; the second attachment is the bottom)
local function shaftTo(s: Slot, top: Vector3, bot: Vector3)
	local sp = s.shaft
	if not sp then return end
	sp.CFrame = CFrame.new(top)
	local bm = sp:FindFirstChildOfClass("Beam")
	if bm and bm.Attachment0 and bm.Attachment1 then
		bm.Attachment0.Position = Vector3.zero
		bm.Attachment1.Position = bot - top
	end
end
local function place(s: Slot, cf: CFrame, size: Vector3, col: Color3?)
	s.p.CFrame = cf
	s.p.Size = size
	if col then s.e.Color = ColorSequence.new(col) end
	s.e.Enabled = true
	s.e:Emit(math.floor(s.e.Rate * 9)) -- (pre-filled where it lands: no fade-up)
end
local function off(s: Slot)
	s.key = nil
	s.e.Enabled = false
	shaftOn(s, false)
end

local lampSlots: { Slot } = {}
for i = 1, LAMPS do table.insert(lampSlots, newSlot("Lamp" .. i, WARM, false, 0, 0)) end
-- the lamp shafts: a pool of their own, always on the nearest three (a beam moves for nothing; the motes stay put)
local lampShafts: { Slot } = {}
for i = 1, SHAFTS do
	-- (27 Nov, in Play: a warm 0.9 shaft read as a beige pillar under the school's cool tubes: their own white, fainter)
	local sh = newSlot("LampShaft" .. i, Color3.fromRGB(214, 226, 240), true, 2.6, 0.95)
	sh.p.Parent = nil -- (only the beams: no motes of its own)
	table.insert(lampShafts, sh)
end
local winSlots: { Slot } = {}
for i = 1, WINDOWS do table.insert(winSlots, newSlot("Window" .. i, MOON, true, 3.6, 0.92)) end
local beam = D.motes(folder, PARK, Vector3.new(3.5, 3.5, 14), WARM, { name = "Beam", rate = 9, prefill = false })
local beamE = emitterOf(beam)
lively(beamE)
beamE.Enabled = false
local wisps = D.motes(folder, PARK, Vector3.new(16, 6, 16), Color3.fromRGB(200, 204, 210), { name = "Wisps", rate = 1.5, prefill = false, emission = 0.1 })
local wispE = emitterOf(wisps)
wispE.Size = NumberSequence.new(0.9, 1.2) -- (soft puffs of the same glow, very faint)
wispE.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.3, 0.9),
	NumberSequenceKeypoint.new(0.7, 0.9), NumberSequenceKeypoint.new(1, 1) })
wispE.Speed = NumberRange.new(0.2, 0.5)
wispE.Enabled = false

local function allOff()
	for _, s in lampSlots do off(s) end
	for _, s in lampShafts do s.key = nil; shaftOn(s, false) end
	for _, s in winSlots do off(s) end
	beamE.Enabled = false; wispE.Enabled = false
end

-- ------------------------------------------------------------ the arena's lamps and windows
local lights: { Light } = {}
local floorOf: { [Light]: number } = {}
-- (27 Nov 2026: the school's tubes flicker now, SchoolLife.client) a lamp lit any time in the last 4 s keeps its dust,
-- so a stutter doesn't hop the motes to another lamp; its shaft goes out and back with it (shaftConn)
local lastOn: { [Light]: number } = {}
local LIT_FOR = 4
local shaftConn: { [number]: RBXScriptConnection } = {}
local seen: Model? = nil
local map: any = nil
local rp = RaycastParams.new()
rp.FilterType = Enum.RaycastFilterType.Exclude
local function lampAt(l: Light): Vector3?
	local par = l.Parent
	if par and par:IsA("BasePart") then return par.Position end
	if par and par:IsA("Attachment") then return par.WorldPosition end
	return nil
end
local function learn(a: Model)
	seen = a
	table.clear(lights); table.clear(floorOf); table.clear(lastOn)
	for _, d in a:GetDescendants() do
		if d:IsA("PointLight") or d:IsA("SpotLight") or d:IsA("SurfaceLight") then table.insert(lights, d) end
	end
	local ok, m = pcall(ZM.read, a)
	map = if ok then m else nil
	local ex: { Instance } = { folder }
	for _, p in Players:GetPlayers() do if p.Character then table.insert(ex, p.Character) end end
	local dm = workspace:FindFirstChild("Dummies")
	if dm then table.insert(ex, dm) end
	rp.FilterDescendantsInstances = ex
end
local function floorUnder(l: Light, at: Vector3): number
	local f = floorOf[l]
	if f then return f end
	-- (from under the fixture: a hit within a stud and a half is the lamp's own housing, cast on from below it)
	local from = at - Vector3.new(0, 0.6, 0)
	local hit = workspace:Raycast(from, Vector3.new(0, -24, 0), rp)
	if hit and from.Y - hit.Position.Y < 1.5 then hit = workspace:Raycast(hit.Position - Vector3.new(0, 0.3, 0), Vector3.new(0, -24, 0), rp) end
	f = if hit then hit.Position.Y else at.Y - 10
	floorOf[l] = f
	return f
end

-- every half second: which lamps and windows get dust
local function pick()
	local a = arena()
	if not on() or not a then
		if folder.Parent then allOff(); folder.Parent = nil end
		return
	end
	if a ~= seen then learn(a) end
	if folder.Parent ~= workspace then folder.Parent = workspace end
	local cam = workspace.CurrentCamera
	if not cam then return end
	local eye = cam.CFrame.Position
	-- the lamps: lit, near, nearest first; a slot keeps its lamp while it's still in the list (no churn)
	local near = {}
	local now = os.clock()
	for _, l in lights do
		if l.Parent and l.Enabled and l.Brightness > 0 then lastOn[l] = now end
		if l.Parent and now - (lastOn[l] or -math.huge) < LIT_FOR then
			local at = lampAt(l)
			if at then
				local d = (at - eye).Magnitude
				if d < LAMP_R then table.insert(near, { l = l, at = at, d = d }) end
			end
		end
	end
	table.sort(near, function(x, y) return x.d < y.d end)
	local want: { [any]: any } = {}
	for i = 1, math.min(#near, LAMPS) do want[near[i].l] = near[i] end
	for _, s in lampSlots do if s.key and not want[s.key] then off(s) end end
	for _, s in lampSlots do if s.key then want[s.key] = nil end end
	for _, s in lampSlots do
		if not s.key then
			local l, n = next(want)
			if l then
				want[l] = nil
				s.key = l
				local f = floorUnder(l, n.at)
				local h = math.clamp(n.at.Y - f - 0.6, 2, 14)
				place(s, CFrame.new(n.at.X, f + h / 2 + 0.3, n.at.Z), Vector3.new(6, h, 6), WARM:Lerp(l.Color, 0.35))
			end
		end
	end
	for i, s in lampShafts do
		local n = near[i]
		if n then
			local l = n.l :: Light
			if s.key ~= l then
				s.key = l
				shaftTo(s, n.at - Vector3.new(0, 0.5, 0), Vector3.new(n.at.X, floorUnder(l, n.at) + 0.2, n.at.Z))
				if shaftConn[i] then shaftConn[i]:Disconnect() end
				shaftConn[i] = l:GetPropertyChangedSignal("Enabled"):Connect(function() if s.key == l then shaftOn(s, l.Enabled) end end)
			end
			shaftOn(s, l.Enabled)
		else
			s.key = nil
			if shaftConn[i] then shaftConn[i]:Disconnect(); shaftConn[i] = nil end
			shaftOn(s, false)
		end
	end
	-- the windows (the map's zombie windows: the moon comes in where the boards are)
	local wins = {}
	if map and map.windows then
		for _, w in map.windows do
			local d = ((w.inn :: Vector3) - eye).Magnitude
			if d < WIN_R then table.insert(wins, { w = w, d = d }) end
		end
		table.sort(wins, function(x, y) return x.d < y.d end)
	end
	for i, s in winSlots do
		local n = wins[i]
		if n then
			if s.key ~= n.w then
				s.key = n.w
				local w = n.w
				local inward = w.n :: Vector3 -- (a window's n points in, to the play side: Zombies spawns at out facing n)
				local c = (w.inn :: Vector3) + inward * 2.5 + Vector3.new(0, 2.6, 0)
				place(s, CFrame.lookAt(c, c + inward), Vector3.new(5, 5, 4), nil)
				-- (in at the window's top, down to the floor a few studs inside)
				shaftTo(s, (w.at :: CFrame).Position + Vector3.new(0, 1.5, 0), (w.inn :: Vector3) + inward * 6 + Vector3.new(0, 0.2, 0))
			end
			shaftOn(s, true)
		else
			off(s)
		end
	end
end
task.spawn(function()
	while true do
		local ok, err = pcall(pick)
		if not ok and RunService:IsStudio() then warn("[ZombieDust] " .. tostring(err)) end
		task.wait(0.5)
	end
end)

-- the air moving: every couple of seconds each box's motes get a new gentle sideways wander (and keep settling)
task.spawn(function()
	local rng = Random.new()
	while true do
		task.wait(1.6 + rng:NextNumber() * 1.2)
		if not folder.Parent then continue end
		for _, s in lampSlots do
			if s.e.Enabled then s.e.Acceleration = Vector3.new(rng:NextNumber(-0.14, 0.14), -0.08 + rng:NextNumber(-0.03, 0.03), rng:NextNumber(-0.14, 0.14)) end
		end
		for _, s in winSlots do
			if s.e.Enabled then s.e.Acceleration = Vector3.new(rng:NextNumber(-0.14, 0.14), -0.06, rng:NextNumber(-0.14, 0.14)) end
		end
	end
end)

-- every frame: the box ahead of your flashlight, the wisps round you in the dark. the beam's motes swirl away from the
-- way you move (the air you push), on top of their own wander
local nextDark, dark = 0, false
local lastCam: Vector3? = nil
local camVel = Vector3.zero
RunService.RenderStepped:Connect(function(dt: number)
	if not folder.Parent then return end
	local cam = workspace.CurrentCamera
	if not cam then return end
	local cp = cam.CFrame.Position
	if lastCam and dt > 0 then
		local v = (cp - lastCam) / dt
		if v.Magnitude < 60 then camVel = camVel:Lerp(v, math.clamp(dt * 4, 0, 1)) end
	end
	lastCam = cp
	local push = -camVel * 0.12
	if push.Magnitude > 1.6 then push = push.Unit * 1.6 end
	beamE.Acceleration = Vector3.new(push.X, -0.08 + push.Y * 0.3, push.Z)
	local mine = me:GetAttribute("ZmLight") == true and me:GetAttribute("ZmFilm") ~= true
	if mine and not beamE.Enabled then beamE.Enabled = true; beamE:Emit(30) elseif not mine then beamE.Enabled = false end
	if mine then beam.CFrame = cam.CFrame * CFrame.new(0, -0.3, -8.5) end
	local t = os.clock()
	if t >= nextDark then
		nextDark = t + 0.3
		local a = arena()
		dark = false
		if a and map and a:GetAttribute("Power") ~= true then
			local id = ZM.areaAt(map, cam.CFrame.Position)
			dark = id ~= nil and ZM.DARK[id] == true
		end
	end
	if dark and not wispE.Enabled then wispE.Enabled = true; wispE:Emit(12) elseif not dark then wispE.Enabled = false end
	if dark then wisps.CFrame = CFrame.new(cam.CFrame.Position) end
end)
