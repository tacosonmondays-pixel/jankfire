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
local TweenService = game:GetService("TweenService")

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
local BEAT = 18 -- (HC.INTRO.beats are written for an 18 s hide and scale to the real one)

-- the room's light: near black, the screen does the rest (a client-side look, only while the room is up)
HubLook.looks.hunt_intro_dark = {
	Lighting = {
		Ambient = Color3.fromRGB(22, 24, 30), OutdoorAmbient = Color3.fromRGB(16, 18, 24), Brightness = 0, -- (27 Nov test:
		ExposureCompensation = -0.1, EnvironmentDiffuseScale = 0, EnvironmentSpecularScale = 0.15, ClockTime = 0, -- blown)
		FogColor = Color3.fromRGB(0, 0, 0), FogStart = 0, FogEnd = 100000,
	},
	Atmosphere = { Density = 0, Haze = 0, Glare = 0 },
	Bloom = { Intensity = 0.35, Size = 24, Threshold = 1.8 },
	ColorCorrection = { Brightness = 0, Contrast = 0.08, Saturation = -0.2, TintColor = Color3.fromRGB(226, 234, 255) },
	SunRays = { Intensity = 0 },
}

local running: any = nil

local function effectsGroup(): SoundGroup?
	local m = SoundService:FindFirstChild("JankMaster")
	local g = m and m:FindFirstChild("Effects")
	return if g and g:IsA("SoundGroup") then g else nil
end
-- a looped bed from HC.INTRO.sounds: a table plays its Roblox library id (with its slice) under EFFECTS; a string
-- clones the game's library Sound of that name. vol scales its level (0: starts silent, a caller brings it up)
local function bed(e: any, vol: number?): Sound?
	local s: Sound
	if type(e) == "table" and e.id then
		s = Instance.new("Sound")
		s.Name = "HuntIntroSound"
		s.SoundId = "rbxassetid://" .. tostring(e.id)
		s.Volume = (e.vol or 0.5) * (vol or 1)
		if e.region then
			s.PlaybackRegionsEnabled = true
			s.PlaybackRegion = NumberRange.new(e.region[1], e.region[2])
			s.LoopRegion = NumberRange.new(e.region[1], e.region[2])
		end
		s.SoundGroup = effectsGroup()
	elseif type(e) == "string" then
		local lib = ReplicatedStorage:FindFirstChild("JankfireSounds")
		local src = lib and lib:FindFirstChild(e)
		if not (src and src:IsA("Sound")) then return nil end
		s = src:Clone()
		s.Volume = (src :: Sound).Volume * (vol or 1)
	else
		return nil
	end
	s.Looped = true
	s.Parent = SoundService
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
	if r.solid then pcall(function() RunService:UnbindFromRenderStep("HuntIntroSolid") end) end
	for _, s in r.sounds do pcall(function() s:Stop(); s:Destroy() end) end
	if r.tail then -- (the birds: peace carries on past the hand-back and fades out)
		local b = r.tail
		local tw = TweenService:Create(b, TweenInfo.new(4, Enum.EasingStyle.Sine), { Volume = 0 })
		tw.Completed:Once(function() b:Destroy() end)
		tw:Play()
	end
	if r.grade then r.grade:Destroy() end
	if r.blur then r.blur:Destroy() end
	local function giveBack()
		local ch = me.Character
		local ref = ch and (ch:FindFirstChild("UpperTorso") or ch:FindFirstChild("Torso")) :: BasePart?
		local v = if ref then ref.LocalTransparencyModifier else 0
		for h in r.touched or {} do
			if h.Parent then
				h.LocalTransparencyModifier = v
				for _, d in h:GetChildren() do if d:IsA("Decal") then d.LocalTransparencyModifier = v end end
			end
		end
	end
	giveBack(); task.delay(0.25, giveBack) -- (his own things back as the game's first-person view keeps them)
	for _, tr in r.realTracks do pcall(function() tr:Stop(0.3) end) end
	if r.folder then r.folder:Destroy() end
	for g, was in r.guis do if g.Parent then g.Enabled = was end end -- (the HUD back)
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
	local r: any = { alive = true, sounds = {}, realTracks = {}, guis = {} }
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
	-- the office chair (its own piece since the win films move it to the desk): pushed back and turned
	local chairSrc = if set == "A" then kit:FindFirstChild("hiA_chair") else nil
	local ci = Data.spots and Data.spots.chairIntro
	if chairSrc and ci then
		local at = SET_AT * CFrame.new(ci[1], ci[2], ci[3]) * CFrame.Angles(0, math.rad(ci[4]), 0)
		local m = chairSrc:Clone()
		local inv = CFrame.new(Data.origin.A):Inverse()
		for _, p in m:GetDescendants() do if p:IsA("BasePart") then p.CFrame = at * (inv * p.CFrame) end end
		m.Parent = folder
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
	light.Color = Color3.fromHex(sd.light.col); light.Shadows = false -- (owner, 27 Nov: its hard shadows striped a frilly outfit)
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
		snap = track(animator, ids.snapTop or ids.snap, Enum.AnimationPriority.Action3), -- (arms free: down, off her face)
	}
	if A.calm then A.calm.Looped = true; A.calm:Play(0) end

	-- the bars and the drone (the light goes dark once the camera is ours: below)
	Cine.bars(true, 0.4)
	-- the sound (the owner, 27 Nov): the room's hum (B: and its TV's static), a heartbeat building louder and faster
	-- under it to the snap, then peace: birds outside
	local S = HC.INTRO.sounds
	local hum = bed(S.hum); if hum then table.insert(r.sounds, hum) end
	local humVol = if hum then hum.Volume else 0
	if set == "B" then local h = bed(S.hiss); if h then table.insert(r.sounds, h) end end
	local heart = bed(S.heart, 0) -- (one bed: its speed and level built up each frame below)
	local shift: PitchShiftSoundEffect? = nil
	if heart then
		table.insert(r.sounds, heart)
		local ps = Instance.new("PitchShiftSoundEffect") -- (holds the beat's pitch as it speeds up)
		ps.Octave = 1
		ps.Parent = heart
		shift = ps
	end
	-- the grade (the owner: liminal, "greyish until the zoom into first person and the bars disappear"): on the
	-- camera, so the zone looks under it never touch it
	local G = HC.INTRO.grade
	local cam = workspace.CurrentCamera
	if G and cam then
		local cc = Instance.new("ColorCorrectionEffect")
		cc.Name = "HuntIntroGrade"
		cc.Saturation = G.saturation; cc.Contrast = G.contrast; cc.Brightness = G.brightness; cc.TintColor = G.tint
		cc.Parent = cam
		r.grade = cc
		if (G.blur or 0) > 0 then
			local b = Instance.new("BlurEffect")
			b.Name = "HuntIntroBlur"
			b.Size = G.blur
			b.Parent = cam
			r.blur = b
		end
	end

	-- the shots (16 s; k scales them to the real hide). set space: his feet at the origin, the screen at -z
	local headP = function(): Vector3 return P(0, hy, 0) end
	-- (main, 27 Nov: on a heavily layered avatar the close-ups were a white jumble of frills) each close-up is about
	-- his face or his hands, read live off the body and eased so a jerky clip never jerks the lens
	local function limb(m: Model?, a: string, b: string): BasePart?
		local x = m and (m:FindFirstChild(a) or m:FindFirstChild(b))
		return if x and x:IsA("BasePart") then x else nil
	end
	local lHand, rHand = limb(body, "LeftHand", "Left Arm"), limb(body, "RightHand", "Right Arm")
	local eased: { [string]: Vector3 } = {}
	local function follow(key: string, p: Vector3, dt: number)
		local e = eased[key]
		eased[key] = if e then e:Lerp(p, math.min(1, dt * 8)) else p
	end
	local headLive = function(): Vector3 return eased.head or headP() end
	local handsLive = function(): Vector3 return eased.hands or P(0.2, hy - 1.0, 0) end
	local function facePoint(): Vector3 -- (the front of his face: what the lens must see past)
		if not head then return headLive() end
		return headLive() + head.CFrame.LookVector * head.Size.Z * 0.5
	end
	-- anything he wears that stands between the lens and what the shot is about, or right at the lens, fades out
	-- (LocalTransparencyModifier: this screen only); everything else stays as he dressed it
	local L = HC.INTRO.lens or { fade = 0.92, near = 1.2 }
	local handleSets: { [Model]: { BasePart } } = {}
	local touched: { [BasePart]: boolean } = {}
	local holdFade: { [BasePart]: number } = {}
	r.touched = touched
	local rp = RaycastParams.new()
	rp.FilterType = Enum.RaycastFilterType.Include
	local function handlesOf(m: Model): { BasePart }
		local l = handleSets[m]
		if l then return l end
		l = {}
		for _, acc in m:GetChildren() do
			if acc:IsA("Accessory") then
				for _, d in acc:GetDescendants() do if d:IsA("BasePart") then table.insert(l, d) end end
			end
		end
		handleSets[m] = l
		return l
	end
	for _, h in handlesOf(body) do h.CanQuery = true end -- (the copy only: the lens rays must find its frills)
	local function clearLens(m: Model?, subj: Vector3, dt: number, nearAt: number?)
		if not m or not m.Parent then return end
		local hs = handlesOf(m)
		if #hs == 0 then return end
		local camP = workspace.CurrentCamera.CFrame.Position
		local dir = subj - camP
		-- (owner on v11, 27 Nov: "her hair is like invisible or clear?": nothing of hers fades for standing between the
		-- lens and her face any more; only what the lens is right inside, which would show its inside faces)
		local block: { [BasePart]: boolean } = {}
		local _ = dir
		for _, h in hs do
			local o = h.CFrame:PointToObjectSpace(camP)
			local hz = h.Size / 2
			local near = (o - Vector3.new(math.clamp(o.X, -hz.X, hz.X), math.clamp(o.Y, -hz.Y, hz.Y), math.clamp(o.Z, -hz.Z, hz.Z))).Magnitude < (nearAt or L.near)
			if block[h] or near then holdFade[h] = os.clock() + 0.6 end -- (sticky: a frill flicking in and out read as shaking)
			local goal = if (holdFade[h] or 0) > os.clock() then L.fade else 0
			local cur = h.LocalTransparencyModifier
			if math.abs(goal - cur) > 0.003 then
				h.LocalTransparencyModifier = cur + (goal - cur) * math.min(1, dt * 7)
				touched[h] = true
			end
		end
	end
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
	-- a steady point on him (his root, not his head: a head in a mocap clip never holds still)
	local realBody = function(): Vector3
		local c2 = me.Character
		local rr = c2 and c2:FindFirstChild("HumanoidRootPart") :: BasePart?
		if rr and (rr.Position - O.Position).Magnitude < 12 then return rr.Position + Vector3.new(0, 1.9, 0) end
		return O.Position + Vector3.new(0, hy - 0.4, 0)
	end
	local flat = Vector3.new(O.LookVector.X, 0, O.LookVector.Z)
	if flat.Magnitude < 1e-3 then flat = Vector3.new(0, 0, -1) end
	flat = flat.Unit
	local function beat(name: string): number return HC.INTRO.beats[name] * k end
	local rt = flat:Cross(Vector3.yAxis)
	-- behind him, the house ahead: where the swing ends and the hold pushes in from
	local function behindCF(hp: Vector3, rad: number, up: number, side: number?): CFrame
		local s = side or 2.0 -- (over his right shoulder: straight behind, his head filled the frame's middle; v6/v7 tests)
		return CFrame.lookAt(hp - flat * rad + rt * s + Vector3.new(0, up, 0), hp + flat * 6 + rt * (s * 0.4))
	end
	local function smoother(u: number): number u = math.clamp(u, 0, 1); return u * u * u * (u * (u * 6 - 15) + 10) end
	local function steadyHead(): Vector3 return realBody() - Vector3.new(0, 0.4, 0) end -- (her root's, still: no bob)
	-- (v12: nothing of hers fades now, so on a big-hat avatar the close rush and the push from behind ended inside the
	-- hat) how far what she wears reaches from her head along a direction; the close lenses keep that much off, plus room
	local function reach(m: Model?, from: Vector3, axis: Vector3): number
		local best = 0
		if not m then return 0 end
		for _, acc in m:GetChildren() do
			if acc:IsA("Accessory") then
				for _, d in acc:GetDescendants() do
					if d:IsA("BasePart") then
						local cf, h = d.CFrame, d.Size / 2
						for _, sx in { -1, 1 } do for _, sy in { -1, 1 } do for _, sz in { -1, 1 } do
							best = math.max(best, ((cf * Vector3.new(sx * h.X, sy * h.Y, sz * h.Z)) - from):Dot(axis))
						end end end
					end
				end
			end
		end
		return math.min(best, 6)
	end
	local fz = (P(0, 0, -1) - P(0, 0, 0)).Unit -- (the room's front of her face)
	local roomFront: number? = nil
	local function nearFront(want: number): number -- (a close-up's distance from her head, past what she wears in front)
		if roomFront == nil then roomFront = reach(body, headP(), fz) end
		return math.max(want, (roomFront :: number) + 0.55) -- (owner on v13: the close rushes back, just outside what she wears)
	end
	local ext: { side: number, rad: number, close: number, reach: number }? = nil
	local function behindExt(): { side: number, rad: number, close: number, reach: number }
		if ext then return ext end
		local ch = me.Character
		local hd = ch and ch:FindFirstChild("Head") :: BasePart?
		if not ch or not hd then return { side = 2.0, rad = 3.7, close = 2.3, reach = 0 } end
		local back = reach(ch, hd.Position, -flat)
		local right = reach(ch, hd.Position, rt)
		-- (v16: the leaves hung on her other side: the hide distance is what she wears' reach every way round)
		local all = math.max(back, right, reach(ch, hd.Position, flat), reach(ch, hd.Position, -rt), reach(ch, hd.Position, Vector3.yAxis))
		ext = { side = math.max(2.0, right + 0.9), rad = math.max(3.7, back + 2.0), close = math.max(2.3, back + 1.2), reach = all }
		return ext :: any
	end
	-- (owner on v14: "When it snaps to outside she should still be look up with the same camera angle") the match cut:
	-- the room's top-down framing on her real body outside, her face still up (the same clip's last frame), only the
	-- world round her changed; read off her real head a moment after the cut
	local function realHeadPart(): BasePart?
		local c2 = me.Character
		local hd = c2 and c2:FindFirstChild("Head") :: BasePart?
		if hd and (hd.Position - O.Position).Magnitude < 12 then return hd end
		return nil
	end
	local function topOutside(u: number): CFrame
		local a = math.rad(74)
		local n = (flat * math.cos(a) + Vector3.yAxis * math.sin(a)).Unit
		local crown = (Vector3.yAxis * math.cos(a) - flat * math.sin(a)).Unit
		local p = realHead()
		local hd = realHeadPart()
		if hd and T() >= beat("outside") + 0.12 then
			if not r.outFace then r.outFace = { n = hd.CFrame.LookVector, c = hd.CFrame.UpVector, p = hd.Position, t = T() } end
			local f = r.outFace
			local k = smoother(math.clamp((T() - f.t) / 0.25, 0, 1))
			n = n:Lerp(f.n, k).Unit; crown = crown:Lerp(f.c, k).Unit; p = p:Lerp(f.p, k)
		end
		local d = Cine.lerp(5.0, 5.5, smoother(u))
		return CFrame.lookAt(p + n * d + flat * 0.4, p + n * 0.25, crown)
	end
	local shots = {
		-- 1. the room: a low wide, a slow push, a profile (27 Nov: trimmed, to give the end outside its room)
		{ name = "wide", t0 = 0, t1 = beat("push"), fov = function(u) return Cine.lerp(56, 52, u) end,
			cam = function(u) return look(lerpV(P(5.2, 1.1, 6.2), P(4.7, 1.25, 5.6), u), P(0, hy - 0.8, -1.2)) end },
		{ name = "push", t0 = beat("push"), t1 = beat("profile"), fov = function(u) return Cine.lerp(42, 36, u) end,
			cam = function(u) return look(lerpV(P(0.2, hy + 0.3, 7.2), P(0.1, hy + 0.15, 4.3), u), P(0, hy - 0.35, 0)) end },
		{ name = "profile", t0 = beat("profile"), t1 = beat("build"), fov = 30, shake = 0.5,
			cam = function(u) return look(lerpV(P(5.6, hy, -0.5), P(4.9, hy, -0.25), u), headLive()) end },
		-- 2. the build: shorter shots, the shake growing
		{ name = "shoulder", t0 = beat("build"), t1 = beat("behind"), fov = 34, shake = 1.6,
			cam = function(u) return look(lerpV(P(1.7, hy - 0.9, 1.9), P(1.45, hy - 0.8, 1.6), u), handsLive()) end }, -- (his shaking hands)
		{ name = "behind", t0 = beat("behind"), t1 = beat("dutch"), fov = 46, shake = 2.3,
			cam = function(u) return look(lerpV(P(0.8, hy + 0.55, 3.0), P(0.55, hy + 0.45, 2.4), u), P(sd.at.X, sd.at.Y, sd.at.Z)) end },
		{ name = "dutch", t0 = beat("dutch"), t1 = beat("face"), fov = 40, shake = 3.2,
			cam = function(u) return look(lerpV(P(-2.5, hy - 0.1, -2.6), P(-2.25, hy, -2.3), u), headLive(), 14) end }, -- (owner on v12: no lens from below)
		{ name = "face", t0 = beat("face"), t1 = beat("rush"), fov = 30, shake = 4.2,
			cam = function(u) local z = nearFront(2.05); return look(lerpV(P(0.5, hy, -(z + 0.45)), P(0.3, hy, -z), u), headLive()) end },
		{ name = "rush", t0 = beat("rush"), t1 = beat("snap"), fov = function(u) return Cine.lerp(34, 26, u) * 1.7 / nearFront(1.7) end, shake = function(u) return 5.0 + 2.5 * u end,
			cam = function(u) local z = nearFront(1.7); return look(lerpV(P(0, hy + 0.1, -(z + 1.7)), P(0, hy + 0.05, -z), u), headLive()) end },
		-- 3. the snap: high and in front, his face snapping up into the lens (27 Nov: straight down it was hair and
		-- hats on a dressed-up avatar; from the front the face reads on any body)
		-- (owner on v11: "I wanted to be staring straight up": the lens straight above her, a touch in front so her face,
		-- tipped 74 deg up by the clip, looks right into it; her body still below; a slow sink and turn)
		-- (owner on v12: "I want the camera to be above her head look down at her!!") high above her head looking down the
		-- line straight out of her upturned face: her face centred, a third of the frame, chin to the frame's foot (the lens
		-- rolled to her crown), a touch forward of her face so a brim can't cover it, lit by a soft key; a slow pull up.
		-- before her face lands the line is the clip's (74 deg up); once it lands (the hit-stop), her real face's
		{ name = "above", t0 = beat("snap"), t1 = beat("outside"), fov = 50, shake = function(u) return 3 * (1 - u) ^ 2 end,
			cam = function(u)
				local d = Cine.lerp(3.2, 5.0, smoother(u))
				local a = math.rad(74)
				local n = (fz * math.cos(a) + Vector3.yAxis * math.sin(a)).Unit
				local crown = (Vector3.yAxis * math.cos(a) - fz * math.sin(a)).Unit
				local face = headLive()
				local hd = body:FindFirstChild("Head") :: BasePart?
				if hd and T() >= beat("snap") + 0.32 then
					if not r.faceAt then r.faceAt = { n = hd.CFrame.LookVector, c = hd.CFrame.UpVector, p = hd.Position, t = T() } end
					local f = r.faceAt
					local k = smoother(math.clamp((T() - f.t) / 0.45, 0, 1))
					n = n:Lerp(f.n, k).Unit; crown = crown:Lerp(f.c, k).Unit; face = face:Lerp(f.p, k)
				end
				return CFrame.lookAt(face + n * d + fz * 0.4, face + n * 0.25, crown)
			end },
		-- 4. outside: the match cut (above), held a beat, still rising slowly
		{ name = "outside", t0 = beat("outside"), t1 = beat("around"), fov = 50, cam = function(u) return topOutside(u) end },
		-- 5. the look round (owner, 27 Nov): a slow drift out to a three-quarter as his head and shoulders turn left and
		-- right and his hands come down
		{ name = "around", t0 = beat("around"), t1 = beat("swing"),
			fov = function(u) local k = smoother(math.clamp(u / 0.4, 0, 1)); return Cine.lerp(50, Cine.lerp(44, 38, u), k) end,
			cam = function(u) -- (owner: "why is she shaking?": the lens followed her moving head, with a handheld on top)
				local e = Cine.ease(u)
				local from = O.Position + flat * Cine.lerp(5.0, 6.2, e) + rt * Cine.lerp(2.4, 3.6, e) + Vector3.new(0, Cine.lerp(1.1, 1.9, e), 0)
				local cf = look(from, realBody() - Vector3.new(0, 0.7 * e, 0))
				local k = smoother(math.clamp(u / 0.4, 0, 1)) -- (a crane down out of the top-down as her head comes down)
				return if k < 1 then topOutside(1):Lerp(cf, k) else cf
			end },
		-- 6. the swing: round to behind him as he looks down
		{ name = "swing", t0 = beat("swing"), t1 = beat("hold"), fov = 40,
			cam = function(u)
				local hp = steadyHead()
				local a = Cine.ease(u)
				local X = behindExt() -- (ends exactly on the hold's first spot, clear of what she wears)
				local e = -flat * X.rad + rt * X.side
				local endDeg = math.deg(math.atan2(flat:Cross(e.Unit).Y, flat:Dot(e.Unit)))
				local dir = CFrame.fromAxisAngle(Vector3.yAxis, math.rad(Cine.lerp(-30, endDeg, a))) * flat
				local at = hp:Lerp(hp + flat * 6 + rt * (X.side * 0.4), Cine.ease(math.clamp((u - 0.2) / 0.8, 0, 1)))
				return CFrame.lookAt(hp + dir * Cine.lerp(6.4, e.Magnitude, a) + Vector3.new(0, Cine.lerp(0.2, 0.9, a), 0), at)
			end },
		-- 7. the hold (owner: "more before the zoom in"): his back to us, the house ahead, a slow push
		{ name = "hold", t0 = beat("hold"), t1 = beat("enter"), fov = 40,
			cam = function(u) local X = behindExt(); return behindCF(steadyHead(), Cine.lerp(X.rad, X.rad - 0.5, u), 0.9, X.side) end },
		-- 8. (owner on v14: "I liked the original transition into gameplay, it was a lot smoother") one smootherstep push
		-- into her eyes, as v8's: round her shoulder (the side comes in last, so it passes what she wears), her head solid
		-- till the lens is at it, then gone as first person hides it
		{ name = "enter", t0 = beat("enter"), t1 = len,
			fov = function(u) local _, gf = Cine.gameplay(flat); return Cine.lerp(40, gf, smoother(u)) end,
			cam = function(u)
				local X = behindExt()
				local e = smoother(u)
				local hp = steadyHead()
				local side = X.side * (1 - smoother(math.clamp((u - 0.3) / 0.7, 0, 1)))
				local back = (X.rad - 0.5) * (1 - e)
				local pos = hp - flat * back + rt * side + Vector3.new(0, 0.9 * (1 - e), 0)
				local g = Cine.gameplay(flat)
				local at = (hp + flat * 6 + rt * (X.side * 0.4)):Lerp(g.Position + g.LookVector * 6, e)
				return CFrame.lookAt(pos, at):Lerp(g, smoother(math.clamp((u - 0.8) / 0.2, 0, 1)))
			end },
	}
	r.cine = Cine.play(shots, { clock = T, flag = "huntintro", warm = 0.4 })
	RunService:BindToRenderStep("HuntIntroSolid", Enum.RenderPriority.Last.Value + 90, function()
		if not r.alive or r.fp or T() < beat("outside") then return end
		local ch = me.Character
		if not ch then return end
		for _, d in ch:GetDescendants() do
			if (d:IsA("BasePart") or d:IsA("Decal")) and (d :: any).LocalTransparencyModifier ~= 0 then (d :: any).LocalTransparencyModifier = 0 end
		end
	end)
	r.solid = true
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
	local pg = me:FindFirstChildOfClass("PlayerGui")
	r.conn = RunService.RenderStepped:Connect(function(dt: number)
		if not r.alive then return end
		local t = T()
		-- what the lens is on: his live head and hands, eased; his frills cleared out of the way
		if head and head.Parent then follow("head", head.Position, dt) end
		if lHand and rHand then follow("hands", (lHand.Position + rHand.Position) / 2, dt) end
		local shot = r.cine and r.cine.shot
		if t < beat("outside") then
			clearLens(body, if shot == "shoulder" then handsLive() elseif shot == "behind" then P(sd.at.X, sd.at.Y, sd.at.Z) else facePoint(), dt)
		else -- (out front: his face; behind him: the house past him; as the lens goes into his head his hair fades)
			-- (owner on v11: her hair and then her whole head went see-through out here: the lens fades nothing of hers
			-- now, and the game's own camera can't either: HuntIntroSolid holds her at 0 until the cut into first person)
			local hd0 = me.Character and me.Character:FindFirstChild("Head") :: BasePart?
			-- (v15: the lens brushed the hat's leaves: her head and what she wears go as the lens reaches what she wears)
			local atHead = hd0 ~= nil and shot == "enter" and (workspace.CurrentCamera.CFrame.Position - hd0.Position).Magnitude < math.max(1.0, math.min(3.2, behindExt().reach + 0.25))
			if not r.fp and (atHead or t >= len - 0.12) then
				r.fp = true
				local ch = me.Character -- (first person: her head and what she wears off this screen, as the game does)
				if ch then
					for _, d in ch:GetDescendants() do
						local bp = if d:IsA("BasePart") then d elseif d:IsA("Decal") and d.Parent and d.Parent:IsA("BasePart") then d.Parent else nil
						if bp and (bp.Name == "Head" or (bp.Parent and bp.Parent:IsA("Accessory"))) then
							(d :: any).LocalTransparencyModifier = 1
							if d:IsA("BasePart") then touched[d] = true end
						end
					end
				end
			end
		end
		-- the snap holds on its last frame: her face straight up until the cut outside
		if A.snap and not r.snapHeld and A.snap.IsPlaying and A.snap.Length > 0 and A.snap.TimePosition >= A.snap.Length - 0.05 then
			r.snapHeld = true
			A.snap:AdjustSpeed(0)
		end
		-- the hit-stop on the snap (main, 27 Nov: the Tidecrest impact language): his body holds for a beat while the
		-- lens kicks and the hit lands
		local HS = HC.INTRO.hitstop
		if HS then
			local a0 = beat("snap") + HS.at
			if r.frozen == nil and t >= a0 and t < a0 + HS.len then
				r.frozen = {}
				for _, tr in A do if tr.IsPlaying then r.frozen[tr] = tr.Speed; tr:AdjustSpeed(0) end end
			elseif r.frozen and t >= a0 + HS.len then
				for tr, sp in r.frozen do tr:AdjustSpeed(sp) end
				r.frozen = false
			end
		end
		-- the screen is the film's: every HUD off while it plays (held each frame: some HUDs set themselves every
		-- frame), each put back as it was at the end
		if pg then
			for _, g in pg:GetChildren() do
				if g:IsA("ScreenGui") and g.Name ~= "CineBars" then
					if r.guis[g] == nil then r.guis[g] = g.Enabled end
					if g.Enabled then g.Enabled = false end
				end
			end
		end
		-- the screen: a steady glow, then a flicker that grows with the build; a white flash on the snap
		local build = math.clamp((t - beat("build")) / (beat("snap") - beat("build")), 0, 1)
		local f = 0.92 + 0.08 * math.noise(t * 6, 2.2)
		if build > 0 then
			f -= build * 0.55 * math.max(0, math.noise(t * (9 + 14 * build), 5.7))
			if math.noise(t * 3.1, 9.9) > 0.55 - 0.35 * build then f *= 0.25 end -- (a dropout)
		end
		if t >= beat("snap") and t < beat("snap") + 0.15 * k then f = 1.8 end
		light.Brightness = baseB * math.max(0.05, f)
		screen.Color = baseCol:Lerp(Color3.new(0, 0, 0), math.clamp(1 - f, 0, 0.9))
		if noise and os.clock() >= nextFrame then
			nextFrame = os.clock() + 1 / 15
			frame = (frame % #HC.INTRO.static) + 1
			noise.Image = "rbxassetid://" .. tostring(HC.INTRO.static[frame])
		end
		-- the heartbeat: louder and faster up to the snap, the hum ducking under it
		local HB = HC.INTRO.heart
		if heart and HB and t < beat("snap") then
			local u = math.clamp((t - HB.from * k) / (beat("snap") - HB.from * k), 0, 1)
			local rate = Cine.lerp(HB.rate[1], HB.rate[2], u ^ 1.4)
			heart.PlaybackSpeed = rate
			if shift then shift.Octave = math.clamp(1 / rate, 0.5, 2) end
			heart.Volume = if t < HB.from * k then 0 else S.heart.vol * Cine.lerp(HB.gain[1], HB.gain[2], u ^ 1.6)
			if hum then hum.Volume = humVol * Cine.lerp(1, HB.duck, u) end
		end
		if build > 0 and t < beat("snap") and os.clock() >= nextBeat then -- (the screen's buzz with its flicker)
			nextBeat = os.clock() + Cine.lerp(0.95, 0.38, build)
			if math.random() < 0.35 * build then sfx(S.buzz, 0.4 + 0.4 * build) end
		end
		-- the grade lifts with the bars, into the game's own colour
		if r.grade and G then
			local w = 1 - math.clamp((t - beat("bars")) / math.max(0.3, len - 0.2 - beat("bars")), 0, 1) -- (with the push in)
			r.grade.Saturation = G.saturation * w
			r.grade.Contrast = G.contrast * w
			r.grade.Brightness = G.brightness * w
			r.grade.TintColor = Color3.new(1, 1, 1):Lerp(G.tint, w)
			if r.blur then r.blur.Size = (G.blur or 0) * w end
		end
		-- his clips
		-- (owner on v13: "I liked the old like manic movements": the possessed build, quicker again)
		if once("crazy", beat("build")) and A.crazy then A.crazy:Play(0.15, 1, 1.25) end
		if once("nod", beat("behind")) and A.nod then A.nod:Play(0.08, 1, 1.8) end
		if once("shake", beat("dutch")) and A.shake then A.shake:Play(0.08, 1, 2.0) end
		if once("crazy2", beat("face")) and A.crazy then A.crazy.TimePosition = 2.0; A.crazy:AdjustSpeed(1.9) end
		if r.key then r.key.Position = workspace.CurrentCamera.CFrame.Position end
		if once("snap", beat("snap")) then
			local kp = Instance.new("Part")
			kp.Name = "HuntIntroKey"; kp.Anchored = true; kp.CanCollide = false; kp.CanQuery = false; kp.CanTouch = false
			kp.Transparency = 1; kp.Size = Vector3.new(0.2, 0.2, 0.2); kp.CastShadow = false
			kp.Position = workspace.CurrentCamera.CFrame.Position
			local kl = Instance.new("PointLight")
			kl.Brightness = 0.9; kl.Range = 8; kl.Shadows = false; kl.Color = Color3.fromRGB(236, 240, 248) -- (owner: a face that reads on a phone)
			kl.Parent = kp
			kp.Parent = folder
			r.key = kp
			for _, k in { "crazy", "nod", "shake" } do local tr = A[k]; if tr and tr.IsPlaying then tr:Stop(0.15) end end -- (arms down)
			if A.snap then A.snap.Looped = false; A.snap:Play(0.03, 1, 1.7) end -- (owner: "a sudden look up": a whip, not an ease)
			if r.cine then r.cine.kick(12) end
			sfx(S.hit, 1)
			for _, s in r.sounds do pcall(function() s:Stop() end) end -- (the room's sound ends on the hit: then peace)
		end
		-- outside: the round's light, the birds, the real body looks up and then down
		if once("outside", beat("outside")) then
			HubLook.set(roundLook(), 0)
			local burst = bed(S.burst) -- (a static burst on the cut outside: the owner's "static sounds")
			if burst then burst.Looped = false; burst.Ended:Once(function() burst:Destroy() end) end
			local birds = bed(S.birds, 0)
			if birds then -- (peace: the birds come up, and carry on past the hand-back: stop fades them)
				r.tail = birds
				TweenService:Create(birds, TweenInfo.new(1.6, Enum.EasingStyle.Sine), { Volume = S.birds.vol }):Play()
			end
			if folder.Parent then folder.Parent = nil end
			local rc = me.Character
			local rh = rc and rc:FindFirstChildOfClass("Humanoid")
			local ra = rh and rh:FindFirstChildOfClass("Animator")
			if ra then
				local up = track(ra, ids.snapTop or ids.snap, Enum.AnimationPriority.Action3)
				if up then up:Play(0, 1, 1); up.TimePosition = math.max(0, up.Length - 0.05); up:AdjustSpeed(0); table.insert(r.realTracks, up) end
				r.realAnimator = ra
			end
		end
		-- the look round (owner, 27 Nov): his hands come down slowly into a relaxed stand as he looks left and right
		if once("around", beat("around")) and r.realAnimator then
			for _, tr in r.realTracks do tr:Stop(2.4) end
			local CA = HC.INTRO.calm or { idle = 0.3, look = 1.2 }
			local rest = track(r.realAnimator, HC.ANIMS[rig] and HC.ANIMS[rig].idle, Enum.AnimationPriority.Action)
			if rest then rest.Looped = true; rest:Play(1.6, 1, CA.idle); table.insert(r.realTracks, rest) end
			local la = HC.INTRO.lookAround and HC.INTRO.lookAround[rig]
			local lk = track(r.realAnimator, la, Enum.AnimationPriority.Action2)
			if lk then lk.Looped = false; lk:Play(1.0, 1, CA.look); table.insert(r.realTracks, lk); r.lookTrack = lk end
		end
		if once("down", beat("swing")) and r.realAnimator then
			if r.lookTrack then r.lookTrack:Stop(0.6) end
			local dn = track(r.realAnimator, ids.look, Enum.AnimationPriority.Action3)
			if dn then dn:Play(0.5, 1, 0.9); table.insert(r.realTracks, dn) end
		end
		if once("bars", beat("bars")) then Cine.bars(false, math.max(0.8, len - 0.2 - beat("bars"))) end
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
