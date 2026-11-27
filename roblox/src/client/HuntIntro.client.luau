--!strict
-- HOUSE HUNT: the gunman's intro (the owner, 27 Nov 2026; roblox/docs/HUNT.md section 11). On the gunman's screen only,
-- for exactly the hide time: a person in a dark room lit only by a screen, slow cinematic angles; they start to lose
-- it; "boom!", an angle from straight above as their head snaps up into the lens; a cut outside the map,
-- they look up; they look down as the camera swings round behind them, the bars lift and the game is theirs.
-- Two rooms on the same beats (the owner: "we can try both"): A their bedroom (a PC screen), B an attic (an old TV's
-- static). The server (HuntRound) sends Remote "intro" { set, len, t0, outside, lead } and holds the real body still:
-- in its sealed pen, then at the outside spot for the last two beats. Everything here is on this client.
-- Guardrails (main): no gun anywhere in it, nothing readable on a screen, plain props, mocap only, no voices.
-- The room and the screen come from HuntIntroData (tools/roblox/hunt_intro_models.py); the camera,
-- the bars and the shake from CineKit; the light is HubLook's (the "Finishing" attribute keeps the zone look off it).
-- Test: the Studio hook's round { role = "gunman", introSet = "A" | "B" } plays it.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local SoundService = game:GetService("SoundService")

local J = ReplicatedStorage:WaitForChild("Jankfire")
local HC = require(J:WaitForChild("HuntConfig")) :: any
local Data = require(J:WaitForChild("HuntIntroData")) :: any
local HubLook = require(J:WaitForChild("HubLook")) :: any
local Cine = require(script.Parent:WaitForChild("CineKit")) :: any
local Sfx: any = nil
pcall(function() Sfx = require(script.Parent:WaitForChild("Sfx", 5) :: ModuleScript) end)
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Hunt") :: RemoteEvent
local me = Players.LocalPlayer

local SET_AT = CFrame.new(0, 4000, 84000) -- (the room's spot: far off every map; client-only parts)
local BEAT = 16 -- (the beats below are written for a 16 s hide and scale to the real one)

-- the room's light: near black, the screen does the rest (a client-side look, only while the room is up)
HubLook.looks.hunt_intro_dark = {
	Lighting = {
		Ambient = Color3.fromRGB(6, 7, 9), OutdoorAmbient = Color3.fromRGB(5, 6, 8), Brightness = 0,
		ExposureCompensation = 0.35, EnvironmentDiffuseScale = 0, EnvironmentSpecularScale = 0.15, ClockTime = 0,
		FogColor = Color3.fromRGB(0, 0, 0), FogStart = 0, FogEnd = 100000,
	},
	Atmosphere = { Density = 0, Haze = 0, Glare = 0 },
	Bloom = { Intensity = 0.7, Size = 26, Threshold = 1.1 },
	ColorCorrection = { Brightness = 0, Contrast = 0.18, Saturation = -0.25, TintColor = Color3.fromRGB(226, 234, 255) },
	SunRays = { Intensity = 0 },
}

local running: any = nil

local function loop(name: string, vol: number): Sound?
	local lib = ReplicatedStorage:FindFirstChild("JankfireSounds")
	local src = lib and lib:FindFirstChild(name)
	if not (src and src:IsA("Sound")) then return nil end
	local s = src:Clone()
	s.Looped = true; s.Volume = (src :: Sound).Volume * vol; s.Parent = SoundService
	s:Play()
	return s
end
local function sfx(name: string, vol: number?)
	if Sfx then pcall(Sfx.play, name, nil, vol) end
end

local function roundLook(): string?
	local an = me:GetAttribute("Arena")
	local by = (HubLook :: any).byArena
	if type(an) == "string" and by and by[an] and HubLook.looks[by[an]] then return by[an] end
	return nil
end

local function stop()
	local r = running
	if not r then return end
	running = nil
	r.alive = false
	if r.conn then r.conn:Disconnect() end
	for _, s in r.sounds do pcall(function() s:Stop(); s:Destroy() end) end
	for _, tr in r.realTracks do pcall(function() tr:Stop(0.3) end) end
	if r.folder then r.folder:Destroy() end
	Cine.bars(false, 0.2)
	HubLook.set(roundLook(), 0)
	if r.cine then r.cine.stop(true) end -- (lands on the gameplay camera; LoadoutOpen and Finishing put back)
	me:SetAttribute("HuntIntro", nil)
end

local function play(a: any)
	stop()
	if type(a) ~= "table" or not HC.INTRO or not HC.INTRO.on then return end
	local set = if a.set == "B" then "B" else "A"
	local len = tonumber(a.len) or BEAT
	local t0 = tonumber(a.t0) or workspace:GetServerTimeNow()
	local O: CFrame = if typeof(a.outside) == "CFrame" then a.outside else CFrame.new()
	local k = len / BEAT
	local function T(): number return workspace:GetServerTimeNow() - t0 end
	local kit = ReplicatedStorage:WaitForChild(HC.INTRO.kit, 3)
	local ch = me.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	if not kit or not ch or not hum then return end
	local rig = if hum.RigType == Enum.HumanoidRigType.R6 then "R6" else "R15"
	local r: any = { alive = true, sounds = {}, realTracks = {} }
	running = r
	me:SetAttribute("HuntIntro", set)

	-- the room
	local folder = Instance.new("Folder")
	folder.Name = "HuntIntroSet"
	r.folder = folder
	local origin: Vector3 = Data.origin[set]
	local base = SET_AT * CFrame.new(-origin)
	for _, nm in { "hi" .. set .. "_room", "hi" .. set .. "_props" } do
		local src = kit:FindFirstChild(nm)
		if src then
			local m = src:Clone()
			for _, p in m:GetDescendants() do if p:IsA("BasePart") then p.CFrame = base * p.CFrame end end
			m.Parent = folder
		end
	end
	local function P(x: number, y: number, z: number): Vector3 return (SET_AT * CFrame.new(x, y, z)).Position end
	-- the screen: one part, its light toward him
	local sd = Data.screens[set]
	local screen = Instance.new("Part")
	screen.Name = "Screen"; screen.Anchored = true; screen.CanCollide = false; screen.CanQuery = false; screen.CanTouch = false
	screen.CastShadow = false; screen.Size = sd.size
	screen.CFrame = CFrame.lookAt(P(sd.at.X, sd.at.Y, sd.at.Z), P(sd.at.X, sd.at.Y, sd.at.Z + 1))
	screen.Color = Color3.fromHex(sd.col)
	screen.Material = if set == "A" then Enum.Material.Neon else Enum.Material.SmoothPlastic
	screen.Parent = folder
	local light = Instance.new("SurfaceLight")
	light.Face = Enum.NormalId.Front; light.Angle = 150; light.Range = sd.light.range; light.Brightness = sd.light.brightness
	light.Color = Color3.fromHex(sd.light.col); light.Shadows = true
	light.Parent = screen
	local noise: ImageLabel? = nil
	if set == "B" then
		local sg = Instance.new("SurfaceGui")
		sg.Face = Enum.NormalId.Front; sg.LightInfluence = 0; sg.Brightness = 1.6; sg.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		sg.PixelsPerStud = 60; sg.Parent = screen
		local im = Instance.new("ImageLabel")
		im.BackgroundTransparency = 1; im.Size = UDim2.fromScale(1, 1); im.ScaleType = Enum.ScaleType.Crop
		im.Image = "rbxassetid://" .. tostring(HC.INTRO.static[1]); im.Parent = sg
		noise = im
		task.spawn(function() -- (the static's frames loaded up front, so the screen never blinks empty)
			local list = {}
			for _, id in HC.INTRO.static do
				local l = Instance.new("ImageLabel"); l.Image = "rbxassetid://" .. tostring(id); table.insert(list, l)
			end
			pcall(function() game:GetService("ContentProvider"):PreloadAsync(list) end)
		end)
	end
	-- him: a copy of his own body, standing in the middle of the room, facing the screen
	local was = ch.Archivable
	ch.Archivable = true
	local body = ch:Clone()
	ch.Archivable = was
	if not body then stop(); return end
	for _, d in body:GetDescendants() do
		if d:IsA("Script") or d:IsA("LocalScript") or d:IsA("Tool") or d:IsA("ForceField") or d:IsA("BillboardGui") then d:Destroy() end
	end
	for _, d in body:GetDescendants() do
		if d.Name == "Viewmodel" or d:GetAttribute("Gun") then d:Destroy() end -- (no gun anywhere in the intro)
	end
	local bh = body:FindFirstChildOfClass("Humanoid") :: Humanoid
	local broot = body:FindFirstChild("HumanoidRootPart") :: BasePart
	bh.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	bh.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
	broot.Anchored = true
	local rootH = if rig == "R6" then 3.0 else bh.HipHeight + broot.Size.Y / 2
	body:PivotTo(SET_AT * CFrame.new(0, rootH, 0))
	body.Parent = folder
	folder.Parent = workspace
	local head = body:FindFirstChild("Head") :: BasePart
	local hy = if head then head.Position.Y - SET_AT.Y else rootH + 1.6
	local animator = bh:FindFirstChildOfClass("Animator") or Instance.new("Animator", bh)
	local ids = HC.INTRO.anims[rig]
	local function track(onto: Animator, id: number?, prio: Enum.AnimationPriority): AnimationTrack?
		if not id then return nil end
		local an = Instance.new("Animation")
		an.AnimationId = "rbxassetid://" .. tostring(id)
		local ok, tr = pcall(function() return onto:LoadAnimation(an) end)
		if not ok or not tr then return nil end
		tr.Priority = prio
		return tr
	end
	local A = {
		calm = track(animator, HC.ANIMS[rig] and HC.ANIMS[rig].idle, Enum.AnimationPriority.Idle),
		crazy = track(animator, ids.crazy, Enum.AnimationPriority.Action),
		nod = track(animator, ids.nod, Enum.AnimationPriority.Action2),
		shake = track(animator, ids.shake, Enum.AnimationPriority.Action2),
		snap = track(animator, ids.snap, Enum.AnimationPriority.Action3),
	}
	if A.calm then A.calm.Looped = true; A.calm:Play(0) end

	-- the bars and the drone (the light goes dark once the camera is ours: below)
	Cine.bars(true, 0.4)
	local d = loop(HC.INTRO.sounds.drone, 0.9); if d then table.insert(r.sounds, d) end
	if set == "B" then local h = loop(HC.INTRO.sounds.hiss, 0.5); if h then table.insert(r.sounds, h) end end

	-- the shots (16 s; k scales them to the real hide). set space: his feet at the origin, the screen at -z
	local headP = function(): Vector3 return P(0, hy, 0) end
	local function look(from: Vector3, at: Vector3, roll: number?): CFrame
		local cf = CFrame.lookAt(from, at)
		return if roll then cf * CFrame.Angles(0, 0, math.rad(roll)) else cf
	end
	local function lerpV(a: Vector3, b: Vector3, u: number): Vector3 return a:Lerp(b, Cine.ease(u)) end
	-- outside: O faces the map; the real head (once the server has moved him there), else where it will be
	local realHead = function(): Vector3
		local c2 = me.Character
		local hd = c2 and c2:FindFirstChild("Head") :: BasePart?
		if hd and (hd.Position - O.Position).Magnitude < 12 then return hd.Position end
		return O.Position + Vector3.new(0, hy, 0)
	end
	local flat = Vector3.new(O.LookVector.X, 0, O.LookVector.Z)
	if flat.Magnitude < 1e-3 then flat = Vector3.new(0, 0, -1) end
	flat = flat.Unit
	local shots = {
		-- 1. the room: a low wide, a slow push, a profile
		{ name = "wide", t0 = 0, t1 = 2.2 * k, fov = function(u) return Cine.lerp(56, 52, u) end,
			cam = function(u) return look(lerpV(P(5.2, 1.1, 6.2), P(4.7, 1.25, 5.6), u), P(0, hy - 0.8, -1.2)) end },
		{ name = "push", t0 = 2.2 * k, t1 = 3.9 * k, fov = function(u) return Cine.lerp(42, 36, u) end,
			cam = function(u) return look(lerpV(P(0.2, hy + 0.3, 7.2), P(0.1, hy + 0.15, 4.3), u), P(0, hy - 0.35, 0)) end },
		{ name = "profile", t0 = 3.9 * k, t1 = 5.5 * k, fov = 30, shake = 0.5,
			cam = function(u) return look(lerpV(P(5.6, hy, -0.5), P(4.9, hy, -0.25), u), headP()) end },
		-- 2. the build: shorter shots, the shake growing
		{ name = "shoulder", t0 = 5.5 * k, t1 = 6.6 * k, fov = 34, shake = 1.2,
			cam = function(u) return look(lerpV(P(1.7, hy - 0.9, 1.9), P(1.45, hy - 0.8, 1.6), u), P(0.2, hy - 1.0, 0)) end },
		{ name = "behind", t0 = 6.6 * k, t1 = 7.7 * k, fov = 46, shake = 1.8,
			cam = function(u) return look(lerpV(P(0.8, hy + 0.55, 3.0), P(0.55, hy + 0.45, 2.4), u), P(sd.at.X, sd.at.Y, sd.at.Z)) end },
		{ name = "dutch", t0 = 7.7 * k, t1 = 8.8 * k, fov = 40, shake = 2.6,
			cam = function(u) return look(lerpV(P(-2.5, 1.4, -2.6), P(-2.25, 1.6, -2.3), u), headP(), 14) end },
		{ name = "face", t0 = 8.8 * k, t1 = 9.7 * k, fov = 30, shake = 3.6,
			cam = function(u) return look(lerpV(P(0.5, hy, -2.5), P(0.3, hy, -2.05), u), headP()) end },
		{ name = "rush", t0 = 9.7 * k, t1 = 10.4 * k, fov = function(u) return Cine.lerp(34, 26, u) end, shake = function(u) return 4.5 + 2.0 * u end,
			cam = function(u) return look(lerpV(P(0, hy + 0.1, -3.4), P(0, hy + 0.05, -1.7), u), headP()) end },
		-- 3. the snap: straight above, the head up into the lens
		{ name = "above", t0 = 10.4 * k, t1 = 11.4 * k, fov = 52, shake = function(u) return 8 * (1 - u) ^ 2 end,
			cam = function(u) local top = P(0, hy + 5.2 - 0.6 * Cine.ease(u), 0.02); return CFrame.lookAt(top, headP(), Vector3.zAxis) end },
		-- 4. outside: low in front of him (between him and the map), looking up at him
		{ name = "outside", t0 = 11.4 * k, t1 = 13.4 * k, fov = 44, shake = 0.5,
			cam = function(u)
				local f = flat
				local rt = f:Cross(Vector3.yAxis)
				local from = O.Position + f * Cine.lerp(5.4, 4.9, u) + rt * 2.4 + Vector3.new(0, 1.1, 0)
				return look(from, realHead() + Vector3.new(0, 0.4, 0))
			end },
		-- 5. the turn: round to behind him as he looks down, then into his eyes, the bars up
		{ name = "turn", t0 = 13.4 * k, t1 = len, fov = function(u) local _, gf = Cine.gameplay(flat); return Cine.lerp(44, gf, Cine.ease(math.clamp((u - 0.55) / 0.45, 0, 1))) end,
			cam = function(u)
				local f = flat
				local hp = realHead()
				local a = Cine.ease(math.clamp(u / 0.7, 0, 1))                    -- round him: front-side to behind
				local ang = math.rad(Cine.lerp(25, 180, a))
				local dir = (CFrame.fromAxisAngle(Vector3.yAxis, ang) * f)
				local rad = Cine.lerp(5.0, 3.2, a)
				local orbit = CFrame.lookAt(hp + dir * rad + Vector3.new(0, Cine.lerp(-0.6, 0.6, a), 0), hp + f * 4)
				local w = Cine.ease(math.clamp((u - 0.7) / 0.3, 0, 1))             -- then onto the game's own camera
				local g = Cine.gameplay(flat)
				return orbit:Lerp(g, w)
			end },
	}
	r.cine = Cine.play(shots, { clock = T, flag = "huntintro" })
	HubLook.set("hunt_intro_dark", 0) -- (Finishing is set now: HubLife leaves the light to us)

	-- the cues: the clips, the flicker, the heartbeat, the hit, outside
	local fired: { [string]: boolean } = {}
	local function once(key: string, at: number): boolean
		if fired[key] or T() < at then return false end
		fired[key] = true
		return true
	end
	local baseCol = screen.Color
	local baseB = light.Brightness
	local nextBeat, nextFrame, frame = 0, 0, 1
	r.conn = RunService.RenderStepped:Connect(function()
		if not r.alive then return end
		local t = T()
		-- the screen: a steady glow, then a flicker that grows with the build; a white flash on the snap
		local build = math.clamp((t - 5.5 * k) / (4.9 * k), 0, 1)
		local f = 0.92 + 0.08 * math.noise(t * 6, 2.2)
		if build > 0 then
			f -= build * 0.55 * math.max(0, math.noise(t * (9 + 14 * build), 5.7))
			if math.noise(t * 3.1, 9.9) > 0.55 - 0.35 * build then f *= 0.25 end -- (a dropout)
		end
		if t >= 10.4 * k and t < 10.55 * k then f = 3.2 end
		light.Brightness = baseB * math.max(0.05, f)
		screen.Color = baseCol:Lerp(Color3.new(0, 0, 0), math.clamp(1 - f, 0, 0.9))
		if noise and os.clock() >= nextFrame then
			nextFrame = os.clock() + 1 / 15
			frame = (frame % #HC.INTRO.static) + 1
			noise.Image = "rbxassetid://" .. tostring(HC.INTRO.static[frame])
		end
		if build > 0 and t < 10.4 * k and os.clock() >= nextBeat then -- (a heartbeat building)
			nextBeat = os.clock() + Cine.lerp(0.95, 0.38, build)
			sfx(HC.INTRO.sounds.heart, 0.5 + 0.5 * build)
			if math.random() < 0.35 * build then sfx(HC.INTRO.sounds.buzz, 0.4 + 0.4 * build) end
		end
		-- his clips
		if once("crazy", 5.5 * k) and A.crazy then A.crazy:Play(0.2, 1, 1) end
		if once("nod", 6.6 * k) and A.nod then A.nod:Play(0.1, 1, 1.4) end
		if once("shake", 7.7 * k) and A.shake then A.shake:Play(0.1, 1, 1.6) end
		if once("crazy2", 8.8 * k) and A.crazy then A.crazy.TimePosition = 2.0; A.crazy:AdjustSpeed(1.5) end
		if once("snap", 10.4 * k) then
			if A.snap then A.snap:Play(0.04, 1, 1.3) end
			if r.cine then r.cine.kick(9) end
			sfx(HC.INTRO.sounds.hit, 1)
		end
		-- outside: the round's light, the air, the real body looks up and then down
		if once("outside", 11.4 * k) then
			HubLook.set(roundLook(), 0)
			for _, s in r.sounds do pcall(function() s:Stop() end) end
			local air = loop(HC.INTRO.sounds.air, 0.7); if air then table.insert(r.sounds, air) end
			if folder.Parent then folder.Parent = nil end
			local rc = me.Character
			local rh = rc and rc:FindFirstChildOfClass("Humanoid")
			local ra = rh and rh:FindFirstChildOfClass("Animator")
			if ra then
				local up = track(ra, ids.snap, Enum.AnimationPriority.Action3)
				if up then up:Play(0.15, 1, 1); up.TimePosition = math.max(0, up.Length - 0.25); up:AdjustSpeed(0); table.insert(r.realTracks, up) end
				r.realAnimator = ra
			end
		end
		if once("down", 13.4 * k) and r.realAnimator then
			for _, tr in r.realTracks do tr:Stop(0.35) end
			local dn = track(r.realAnimator, ids.look, Enum.AnimationPriority.Action3)
			if dn then dn:Play(0.3, 1, 1.1); table.insert(r.realTracks, dn) end
		end
		if once("bars", 14.6 * k) then Cine.bars(false, 0.8) end
		if t >= len then stop() end
	end)
end

Remote.OnClientEvent:Connect(function(op: string, a: any)
	if op == "intro" then
		task.spawn(play, a)
	elseif op == "results" or op == "phase" and a == "hunt" then
		if running and op == "results" then stop() end
	end
end)
me:GetAttributeChangedSignal("Hunt"):Connect(function()
	if me:GetAttribute("Hunt") ~= "round" and running then stop() end
end)
