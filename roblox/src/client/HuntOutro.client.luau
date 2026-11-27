--!strict
-- HOUSE HUNT: the round's win films (the owner, 27 Nov 2026: "it was just a game you were playing"). Everyone in the
-- round sees the winners' film, then the results card (HuntRound holds the card for HC.OUTRO.len).
--   the gunman wins: a slow walk through the wrecked house, looking round (cushions knocked down, the last pink cubes
--     fading; no blood, no bodies); a static glitch; the lens pulls back out of a monitor showing that same view; his
--     own avatar at the desk in the intro's bedroom (room A), lit by the screen, playing; he leans back and stretches.
--   the hiders win: the survivors together in the house, out of breath; a static glitch; the lens pulls back out of the
--     attic's old TV showing them; the same avatars as friends on a couch round it (room B), pads in hand, cheering.
-- Both rooms come from the intro's kit (HuntIntroData's spots); the lens is CineKit's (the bars, the shake, the kick);
-- the grade is the intro's muted one; whatever anyone wears between the lens and a face fades (as in the intro).
-- Screens show only the game's own view (a ViewportFrame of the house), glow and static: nothing readable.
-- Sound: recordings only, no voices (the room's hum or the TV's hiss, a static burst, keys, pad clicks, single claps).
-- Server: HuntRound.finish fires Remote "outro" { win, who = { Model }, map = Model, len, t0 }.
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
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Hunt") :: RemoteEvent
local me = Players.LocalPlayer

local OUT_AT = CFrame.new(300, 4000, 84000) -- (the room's spot: next to the intro's, far off every map; client-only)
local PINK = Color3.fromRGB(255, 176, 204) -- (the break-up's cubes: HuntFx)

if not HubLook.looks.hunt_intro_dark then -- (HuntIntro defines it; the same dark room, in case it hasn't run)
	HubLook.looks.hunt_intro_dark = {
		Lighting = { Ambient = Color3.fromRGB(22, 24, 30), OutdoorAmbient = Color3.fromRGB(16, 18, 24), Brightness = 0,
			ExposureCompensation = -0.1, EnvironmentDiffuseScale = 0, EnvironmentSpecularScale = 0.15, ClockTime = 0,
			FogColor = Color3.fromRGB(0, 0, 0), FogStart = 0, FogEnd = 100000 },
		Atmosphere = { Density = 0, Haze = 0, Glare = 0 },
		Bloom = { Intensity = 0.35, Size = 24, Threshold = 1.8 },
		ColorCorrection = { Brightness = 0, Contrast = 0.08, Saturation = -0.2, TintColor = Color3.fromRGB(226, 234, 255) },
		SunRays = { Intensity = 0 },
	}
end

local running: any = nil

local function effectsGroup(): SoundGroup?
	local m = SoundService:FindFirstChild("JankMaster")
	local g = m and m:FindFirstChild("Effects")
	return if g and g:IsA("SoundGroup") then g else nil
end
-- a recording by its library id: looped beds and one-shots, optionally out in the world at a point
local function sound(e: any, vol: number?, looped: boolean?, at: Vector3?, into: Instance?): Sound?
	if type(e) ~= "table" or not e.id then return nil end
	local s = Instance.new("Sound")
	s.Name = "HuntOutroSound"
	s.SoundId = "rbxassetid://" .. tostring(e.id)
	s.Volume = (e.vol or 0.5) * (vol or 1)
	s.Looped = looped == true
	if e.region then
		s.PlaybackRegionsEnabled = true
		s.PlaybackRegion = NumberRange.new(e.region[1], e.region[2])
		if looped then s.LoopRegion = NumberRange.new(e.region[1], e.region[2]) end
	end
	s.SoundGroup = effectsGroup()
	if at and into then
		local a = Instance.new("Attachment")
		a.Parent = (workspace :: any).Terrain
		a.WorldPosition = at
		s.RollOffMode = Enum.RollOffMode.InverseTapered; s.RollOffMinDistance = 6; s.RollOffMaxDistance = 60
		s.Parent = a
		if not looped then s.Ended:Once(function() a:Destroy() end) end
	else
		s.Parent = SoundService
		if not looped then s.Ended:Once(function() s:Destroy() end) end
	end
	s:Play()
	return s
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
	for _, s in r.sounds do
		pcall(function()
			local tw = TweenService:Create(s, TweenInfo.new(0.6), { Volume = 0 })
			tw.Completed:Once(function() s:Destroy() end)
			tw:Play()
		end)
	end
	if r.grade then r.grade:Destroy() end
	if r.blur then r.blur:Destroy() end
	if r.static then r.static:Destroy() end
	for d, v in r.hidden do if d.Parent then (d :: any).LocalTransparencyModifier = v end end -- (the real bodies back)
	for _, f in r.folders do if f.Parent then f:Destroy() end end
	for g, was in r.guis do if g.Parent then g.Enabled = was end end
	Cine.bars(false, 0.3)
	HubLook.set(roundLook(), 0)
	if r.cine then r.cine.stop(true) end
	if r.warm then r.warm.release(); r.warm = nil end
	me:SetAttribute("HuntOutro", nil)
end

-- a copy of a body: no scripts, no tools, no gun, no name over it, held still at its root
local function copyBody(m: Model): (Model?, string)
	local was = m.Archivable
	m.Archivable = true
	local ok, c = pcall(function() return m:Clone() end)
	m.Archivable = was
	if not ok or not c then return nil, "R15" end
	-- only the body: its limbs, what he wears, his clothes (v1 test: the gunman's rifle came along to the desk)
	local LIMBS = { Head = true, HumanoidRootPart = true, UpperTorso = true, LowerTorso = true, Torso = true,
		LeftUpperArm = true, LeftLowerArm = true, LeftHand = true, RightUpperArm = true, RightLowerArm = true, RightHand = true,
		LeftUpperLeg = true, LeftLowerLeg = true, LeftFoot = true, RightUpperLeg = true, RightLowerLeg = true, RightFoot = true,
		["Left Arm"] = true, ["Right Arm"] = true, ["Left Leg"] = true, ["Right Leg"] = true }
	for _, ch in c:GetChildren() do
		local keepIt = ch:IsA("Humanoid") or ch:IsA("Accessory") or ch:IsA("Clothing") or ch:IsA("ShirtGraphic")
			or ch:IsA("BodyColors") or ch:IsA("CharacterMesh") or (ch:IsA("BasePart") and LIMBS[ch.Name])
		if not keepIt then ch:Destroy() end
	end
	for _, d in c:GetDescendants() do
		if d:IsA("Script") or d:IsA("LocalScript") or d:IsA("BillboardGui") or d:GetAttribute("Gun") then d:Destroy() end
	end
	local hum = c:FindFirstChildOfClass("Humanoid")
	local root = c:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not hum or not root then c:Destroy(); return nil, "R15" end
	hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	hum.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
	root.Anchored = true
	for _, d in c:GetDescendants() do if d:IsA("BasePart") then d.CanCollide = false; d.CanTouch = false end end
	return c, if hum.RigType == Enum.HumanoidRigType.R6 then "R6" else "R15"
end
local function rootHeight(c: Model, rig: string): number
	local hum = c:FindFirstChildOfClass("Humanoid") :: Humanoid
	local root = c:FindFirstChild("HumanoidRootPart") :: BasePart
	return if rig == "R6" then 3.0 else hum.HipHeight + root.Size.Y / 2
end
local function track(c: Model, id: number?, prio: Enum.AnimationPriority): AnimationTrack?
	if not id then return nil end
	local hum = c:FindFirstChildOfClass("Humanoid")
	if not hum then return nil end
	local an = hum:FindFirstChildOfClass("Animator") or Instance.new("Animator", hum)
	local a = Instance.new("Animation")
	a.AnimationId = "rbxassetid://" .. tostring(id)
	local ok, tr = pcall(function() return (an :: Animator):LoadAnimation(a) end)
	if not ok or not tr then return nil end
	tr.Priority = prio
	return tr
end
local function spotCF(t: { number }): CFrame return CFrame.new(t[1], t[2], t[3]) * CFrame.Angles(0, math.rad(t[4]), 0) end
-- one of the kit's pieces at a spot (each piece stands at its room's origin in the kit)
local function piece(kit: Instance, name: string, at: CFrame, into: Instance): Model?
	local src = kit:FindFirstChild(name)
	if not src then return nil end
	local m = src:Clone() :: Model
	local key = Data.pieces and Data.pieces[name]
	local o: Vector3 = if key then Data.origin[key] else Vector3.zero
	local inv = CFrame.new(o):Inverse()
	for _, p in m:GetDescendants() do if p:IsA("BasePart") then p.CFrame = at * (inv * p.CFrame) end end
	m.Parent = into
	return m
end

local function play(a: any)
	stop()
	local OUT = HC.OUTRO
	if type(a) ~= "table" or not OUT or not OUT.on then return end
	local win = if a.win == "gunman" then "gunman" else "hiders"
	local len = tonumber(a.len) or OUT.len
	local t0 = tonumber(a.t0) or workspace:GetServerTimeNow()
	local k = len / OUT.len
	local function T(): number return workspace:GetServerTimeNow() - t0 end
	local function beat(n: string): number return OUT.beats[n] * k end
	local kit = ReplicatedStorage:WaitForChild(HC.INTRO.kit, 3)
	if not kit then return end
	local who: { Model } = {}
	for _, m in (type(a.who) == "table" and a.who or {}) do if typeof(m) == "Instance" and m:IsA("Model") then table.insert(who, m) end end
	local map: Instance? = if typeof(a.map) == "Instance" then a.map else nil
	local r: any = { alive = true, sounds = {}, guis = {}, folders = {}, hidden = {} }
	running = r
	me:SetAttribute("HuntOutro", win)
	local S = OUT.sounds
	local function keep(s: Sound?) if s then table.insert(r.sounds, s) end end
	-- the real bodies out of the house's shot (their copies play it)
	local function hide(m: Model, on: boolean)
		for _, d in m:GetDescendants() do
			if d:IsA("BasePart") or d:IsA("Decal") then
				if on then
					if r.hidden[d] == nil then r.hidden[d] = (d :: any).LocalTransparencyModifier end
					(d :: any).LocalTransparencyModifier = 1
				elseif r.hidden[d] ~= nil then
					(d :: any).LocalTransparencyModifier = r.hidden[d]; r.hidden[d] = nil
				end
			end
		end
	end

	-- ---------------------------------------------------------------- 1. the house
	local house = Instance.new("Folder")
	house.Name = "HuntOutroHouse"
	house.Parent = workspace
	table.insert(r.folders, house)
	local bodies: { any } = {}
	local walk: { CFrame } = {}
	local groupAt: Vector3? = nil
	local mapDef = nil
	if type(a.mapId) == "string" then for _, d in HC.MAPS do if d.id == a.mapId then mapDef = d end end end
	for _, m in who do hide(m, true) end
	local origin: CFrame = if typeof(a.origin) == "CFrame" then a.origin elseif map and map:IsA("Model") then (map :: Model):GetPivot() else CFrame.new()
	local function L(t: { number }): Vector3 return origin * Vector3.new(t[1], t[2], t[3]) end
	if win == "gunman" then
		-- his walk: the map's path, else from where he stands, forward along his look
		local W = mapDef and mapDef.outroWalk
		if W then
			for _, p in W.path do table.insert(walk, CFrame.new(L(p))) end
		else
			local gm = who[1]
			local hd = gm and gm:FindFirstChild("Head") :: BasePart?
			local p0 = if hd then hd.Position else origin.Position + Vector3.new(0, 5.5, 0)
			local f = if hd then Vector3.new(hd.CFrame.LookVector.X, 0, hd.CFrame.LookVector.Z).Unit else origin.LookVector
			table.insert(walk, CFrame.new(p0 - f * 2)); table.insert(walk, CFrame.new(p0 + f * 6))
		end
		-- the wreck (main, 27 Nov: "start the walk with destroyed place"): the map's own list of things knocked over,
		-- else cushions along the way; and the last pink cubes, fading
		local wreck = mapDef and mapDef.outroWreck
		if wreck then
			for _, w in wreck do
				local at = origin * CFrame.new(w[2], w[3], w[4]) * CFrame.Angles(0, math.rad(w[5] or 0), 0)
					* CFrame.Angles(math.rad(w[6] or 0), 0, math.rad(w[7] or 0))
				piece(kit, w[1], at, house)
			end
		end
		local cubes: { BasePart } = {}
		for i = 1, #walk do
			local p = walk[i].Position
			local rng = Random.new(i * 17)
			local down = workspace:Raycast(p, Vector3.new(0, -12, 0))
			local floorY = if down then down.Position.Y else p.Y - 5.5
			if i < #walk and not wreck then
				local at = CFrame.new(p.X + rng:NextNumber(-3, 3), floorY, p.Z + rng:NextNumber(-3, 3)) * CFrame.Angles(0, rng:NextNumber(0, 6.28), math.rad(rng:NextNumber(-8, 8)))
				piece(kit, "hiW_cushion", at, house)
			end
			for _ = 1, 4 do
				local c = Instance.new("Part")
				c.Anchored = true; c.CanCollide = false; c.CanQuery = false; c.CanTouch = false; c.CastShadow = false
				c.Material = Enum.Material.SmoothPlastic; c.Color = PINK
				local s = rng:NextNumber(0.35, 0.8)
				c.Size = Vector3.new(s, s, s)
				c.CFrame = CFrame.new(p.X + rng:NextNumber(-4, 4), floorY + s / 2, p.Z + rng:NextNumber(-4, 4)) * CFrame.Angles(0, rng:NextNumber(0, 6.28), 0)
				c.Parent = house
				table.insert(cubes, c)
			end
		end
		r.cubes = cubes
	else
		-- the survivors together, out of breath: copies of their bodies round the map's spot (else the first one's)
		local G = mapDef and mapDef.outroGroup
		local first = who[1] and who[1]:FindFirstChild("HumanoidRootPart") :: BasePart?
		groupAt = if G then L(G) elseif first then first.Position - Vector3.new(0, 3, 0) else origin.Position
		local face = if G and G[4] then (origin * CFrame.Angles(0, math.rad(G[4]), 0)).LookVector else Vector3.new(0, 0, 1)
		-- (owner, 27 Nov: "make them walk also"): through the house together, a loose wedge, looking round as they go
		local GW = mapDef and mapDef.outroGroupWalk
		local gFrom: Vector3 = if GW then L(GW.from) else groupAt :: Vector3
		local gTo: Vector3 = if GW then L(GW.to) else groupAt :: Vector3
		local gd = gTo - gFrom
		local gDir = if gd.Magnitude > 0.1 then Vector3.new(gd.X, 0, gd.Z).Unit else face
		r.gFrom, r.gTo, r.gDir = gFrom, gTo, gDir
		local GR = OUT.group or {}
		local SC = OUT.scared or {}
		local mine = table.find(who, me.Character) -- (through your own eyes when you're one of them)
		if mine and mine > 1 then who[1], who[mine] = who[mine], who[1] end
		for i, src in who do
			local c, rig = copyBody(src)
			if c then
				local g = GR[i] or { side = (if i % 2 == 0 then 1 else -1) * 1.6, back = 1.7 * i, speed = 0.5, phase = (i * 0.29) % 1 }
				local lead = i == 1 and GW ~= nil
				c.Parent = house
				local base = track(c, if GW then (OUT.walk and OUT.walk[rig]) else (HC.ANIMS[rig] and HC.ANIMS[rig].idle), Enum.AnimationPriority.Action)
				if base then base.Looped = true; base:Play(0); base:AdjustSpeed(if GW then (if lead then SC.walkSpeed or 0.4 else g.speed or 0.5) else 1.15) end
				if lead then -- (scared: hunched, her arms in, glancing round; mocap from the vault until Mixamo's scared walk)
					local hu = track(c, SC.hunch and SC.hunch[rig], Enum.AnimationPriority.Action2)
					if hu then hu.Looped = false; hu:Play(0.3, SC.hunchWeight or 0.85, 0); hu.TimePosition = 0.07 end
					local gl = track(c, SC.glance and SC.glance[rig], Enum.AnimationPriority.Action3)
					if gl then gl.Looped = true; gl:Play(0.5, 1, 0.85) end
				elseif GW then
					local la = HC.INTRO.lookAround and HC.INTRO.lookAround[rig]
					local lk = track(c, la, Enum.AnimationPriority.Action2)
					if lk then lk.Looped = true; lk:Play(0.6, 0.8, 0.6 + 0.1 * (i % 3)); lk.TimePosition = i * 0.9 end
				end
				table.insert(bodies, { m = c, rig = rig, src = src, g = g, walk = base, h = rootHeight(c, rig) })
			end
		end
		local DW = mapDef and mapDef.outroDoor
		if DW then
			r.door = {}
			local w = (DW[2] - DW[1]) / 2
			local h = DW[5] or 9.8
			for _, sgn in { -1, 1 } do
				local hinge = origin * CFrame.new(if sgn < 0 then DW[1] else DW[2], DW[4] or 0, DW[3])
				local leaf = Instance.new("Part")
				leaf.Name = "HuntOutroDoor"; leaf.Anchored = true; leaf.CanCollide = false; leaf.CanQuery = false; leaf.CanTouch = false
				leaf.Size = Vector3.new(w - 0.05, h, 0.35); leaf.Color = Color3.fromRGB(138, 122, 104); leaf.Material = Enum.Material.SmoothPlastic
				local function at(open: number): CFrame return hinge * CFrame.Angles(0, sgn * open, 0) * CFrame.new(-sgn * w / 2, h / 2, 0) end
				leaf.CFrame = at(0)
				leaf.Parent = house
				table.insert(r.door, { leaf = leaf, at = at })
			end
			local sun = Instance.new("Part") -- (the daylight outside it, coming in as it opens)
			sun.Name = "HuntOutroDaylight"; sun.Anchored = true; sun.CanCollide = false; sun.CanQuery = false; sun.CanTouch = false
			sun.Transparency = 1; sun.Size = Vector3.new(0.2, 0.2, 0.2)
			sun.CFrame = origin * CFrame.new((DW[1] + DW[2]) / 2, (DW[4] or 0) + h * 0.6, DW[3] + 3)
			local sl = Instance.new("PointLight"); sl.Brightness = 0; sl.Range = 26; sl.Shadows = false; sl.Color = Color3.fromRGB(255, 242, 222)
			sl.Parent = sun
			sun.Parent = house
			r.daylight = sl
		end
		if GW and bodies[1] then -- (first person: her own body is the lens, not in the shot)
			r.fp = true
			r.fpEyeH = bodies[1].h + 1.55
			bodies[1].m.Parent = nil
		end
		-- each one's place along the hall at t s (the lead's pace uneven; the rest behind her, never in step)
		r.placeGroup = function(t: number)
			local L = (gTo - gFrom).Magnitude
			local right = gDir:Cross(Vector3.yAxis)
			local pace = SC.pace or 2.4
			local lead = math.clamp(pace * t + (SC.uneven or 0.22) * math.sin(t * 2.6) / 2.6 * pace, 0, L)
			for _, b in bodies do
				local g = b.g
				local d = lead - (g.back or 0)
				if g.pauseAt and t > g.pauseAt then -- (stops for a look back, then hurries to catch up)
					local over = t - g.pauseAt
					local pl = g.pauseLen or 0.9
					local lost = math.min(over, pl) * pace - math.max(0, over - pl) * pace * ((g.hurry or 1.5) - 1)
					d -= math.max(0, lost)
					if b.walk then
						local want = if over < pl then 0.06 elseif lost > 0 then (g.speed or 0.5) * (g.hurry or 1.5) else (g.speed or 0.5)
						if math.abs(b.walk.Speed - want) > 0.01 then b.walk:AdjustSpeed(want) end
					end
				end
				d = math.max(d, -2.2) -- (never back through the wall behind the start)
				local ph = (g.phase or 0) * 6.283
				local at = gFrom + gDir * d + right * ((g.side or 0) + 0.22 * math.sin(t * 0.9 + ph)) + Vector3.new(0, b.h, 0)
				local fwd = CFrame.fromAxisAngle(Vector3.yAxis, 0.07 * math.sin(t * 0.7 + ph)) * gDir
				b.m:PivotTo(CFrame.lookAt(at, at + fwd))
			end
			r.leadAt = gFrom + gDir * lead
		end
		r.placeGroup(0)
	end

	-- ---------------------------------------------------------------- 2. the room (built now, shown after the glitch)
	local set = if win == "gunman" then "A" else "B"
	local room = Instance.new("Folder")
	room.Name = "HuntOutroRoom"
	table.insert(r.folders, room)
	local roomOrigin: Vector3 = Data.origin[set]
	local base = OUT_AT * CFrame.new(-roomOrigin)
	for _, nm in { "hi" .. set .. "_room", "hi" .. set .. "_props" } do
		local src = kit:FindFirstChild(nm)
		if src then
			local m = src:Clone()
			for _, p in m:GetDescendants() do if p:IsA("BasePart") then p.CFrame = base * p.CFrame end end
			m.Parent = room
		end
	end
	local SP = Data.spots or {}
	local function P(v: Vector3): Vector3 return (OUT_AT * CFrame.new(v)).Position end
	local function spot(name: string): CFrame return OUT_AT * spotCF(SP[name]) end
	if set == "A" then piece(kit, "hiA_chair", spot("chairDesk"), room) else piece(kit, "hiB_couch", spot("couch"), room) end
	-- the screen: the house as it was a moment ago (a ViewportFrame), then static, its glow on the room
	local sd = Data.screens[set]
	local screen = Instance.new("Part")
	screen.Name = "Screen"; screen.Anchored = true; screen.CanCollide = false; screen.CanQuery = false; screen.CanTouch = false
	screen.CastShadow = false; screen.Size = sd.size; screen.Transparency = 0
	screen.CFrame = CFrame.lookAt(P(sd.at), P(sd.at + Vector3.new(0, 0, 1)))
	screen.Color = Color3.fromRGB(20, 22, 26); screen.Material = Enum.Material.SmoothPlastic
	screen.Parent = room
	local light = Instance.new("SurfaceLight")
	light.Face = Enum.NormalId.Front; light.Angle = 150; light.Range = sd.light.range; light.Brightness = sd.light.brightness * (if set == "A" then 0.9 else 1.5) -- (v2: B near black; v6: A's sitter blew out white)
	light.Color = Color3.fromHex(sd.light.col); light.Shadows = false -- (owner, 27 Nov: hard screen shadows striped the outfits)
	light.Parent = screen
	local sg = Instance.new("SurfaceGui")
	sg.Face = Enum.NormalId.Front; sg.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; sg.PixelsPerStud = 180
	sg.LightInfluence = 0; sg.Brightness = 1.6
	sg.Parent = screen
	local vp = Instance.new("ViewportFrame")
	vp.Size = UDim2.fromScale(1, 1); vp.BackgroundColor3 = Color3.fromRGB(12, 13, 16); vp.BorderSizePixel = 0
	vp.Ambient = Color3.fromRGB(190, 186, 178); vp.LightColor = Color3.fromRGB(255, 244, 226); vp.LightDirection = Vector3.new(-0.4, -1, -0.3)
	vp.Parent = sg
	local vcam = Instance.new("Camera")
	vcam.FieldOfView = 70
	vcam.Parent = vp
	vp.CurrentCamera = vcam
	local snow = Instance.new("ImageLabel") -- (the TV's own static over the picture, light in A, heavier in B)
	snow.Size = UDim2.fromScale(1, 1); snow.BackgroundTransparency = 1; snow.ScaleType = Enum.ScaleType.Crop
	snow.ImageTransparency = if set == "B" then 0.55 else 0.85
	snow.Parent = sg
	-- the players: the gunman at his desk, or the survivors on the couch, the armchair and behind them
	local roomBodies: { any } = {}
	local function seat(src: Model, at: CFrame, kind: string)
		local c, rig = copyBody(src)
		if not c then return end
		if kind == "seat" then
			-- (the seated clip drops the hips sitDrop studs below the root: the root goes that far over the seat, a
			-- little back from its front so the thighs lie on it)
			local drop = (OUT.sitDrop and OUT.sitDrop[rig]) or 1.2
			c:PivotTo(at * CFrame.new(0, drop, OUT.sitBack or 0.2))
		else
			c:PivotTo(at * CFrame.new(0, rootHeight(c, rig), 0))
		end
		c.Parent = room
		table.insert(roomBodies, { m = c, rig = rig, kind = kind, seatY = at.Position.Y })
	end
	if set == "A" then
		if who[1] then seat(who[1], spot("deskSeat"), "seat") end
	else
		local seats = { "seat1", "seat2", "seat3" }
		local stands = { "stand1", "stand2", "stand3" }
		for i, src in who do
			if i <= #seats then seat(src, spot(seats[i]), "seat")
			elseif i - #seats <= #stands then seat(src, spot(stands[i - #seats]), "stand") end
		end
	end

	-- ---------------------------------------------------------------- the lens
	local lastHouseCF = CFrame.new()
	local function houseCam(u: number): CFrame
		if win == "gunman" then
			local n = #walk
			if n == 0 then return CFrame.new() end
			local x = math.clamp(u, 0, 1) * (n - 1)
			local i = math.min(n - 1, math.floor(x))
			local f = x - i
			local p = if n == 1 then walk[1].Position else walk[i + 1].Position:Lerp(walk[i + 2].Position, Cine.ease(f))
			local W = mapDef and mapDef.outroWalk
			local looks = W and W.looks
			local at: Vector3
			if looks and #looks > 0 then
				local lx = math.clamp(u, 0, 1) * (#looks - 1)
				local li = math.min(#looks - 1, math.floor(lx))
				at = if #looks == 1 then L(looks[1]) else L(looks[li + 1]):Lerp(L(looks[li + 2]), Cine.ease(lx - li))
			else
				local fwd = if n >= 2 then (walk[n].Position - walk[1].Position).Unit else Vector3.new(0, 0, -1)
				at = p + (CFrame.fromAxisAngle(Vector3.yAxis, math.sin(u * math.pi * 2) * 0.6) * fwd) * 10
			end
			p += Vector3.new(0, math.sin(u * 14) * 0.06, 0) -- (a walk's bob)
			return CFrame.lookAt(p, at)
		else
			if r.gFrom and r.fp then -- (owner: "can it be first person like how the hunters is?": her eyes, scared, calm)
				local tt = u * math.max(0.1, beat("glitch") - (OUT.hitstop or 0.2))
				local lead = (r.leadAt or r.gFrom) :: Vector3
				r.eyeAt = if r.eyeAt then (r.eyeAt :: Vector3):Lerp(lead, 0.25) else lead
				local eye = (r.eyeAt :: Vector3) + Vector3.new(0, (r.fpEyeH or 4.5) + 0.03 * math.sin(tt * 2.4), 0) -- (a breath, no bob)
				local K = OUT.hiderLooks or { { 0, 0, -4 } }
				local yaw, pitch = K[1][2], K[1][3]
				for i = 1, #K - 1 do
					local a0, a1 = K[i], K[i + 1]
					if tt >= a1[1] then yaw, pitch = a1[2], a1[3]
					elseif tt >= a0[1] then
						local x = math.clamp((tt - a0[1]) / (a1[1] - a0[1]), 0, 1)
						local k = x * x * x * (x * (x * 6 - 15) + 10) -- (smootherstep: the owner's "smoother")
						yaw, pitch = a0[2] + (a1[2] - a0[2]) * k, a0[3] + (a1[3] - a0[3]) * k
						break
					end
				end
				local dir = CFrame.fromAxisAngle(Vector3.yAxis, math.rad(yaw)) * (r.gDir :: Vector3)
				dir = CFrame.fromAxisAngle(dir:Cross(Vector3.yAxis), math.rad(pitch)) * dir
				return CFrame.lookAt(eye, eye + dir)
			end
			if r.gFrom then -- (a slow dolly back in front of her as she leads them down the hall; no handheld)
				local lead = (r.leadAt or r.gFrom) :: Vector3
				r.lensAt = if r.lensAt then (r.lensAt :: Vector3):Lerp(lead, 0.08) else lead
				local center = r.lensAt :: Vector3
				local right = (r.gDir :: Vector3):Cross(Vector3.yAxis)
				return CFrame.lookAt(center + r.gDir * Cine.lerp(7.2, 6.4, u) + right * 1.3 + Vector3.new(0, 4.2, 0), center - r.gDir * 1.6 + Vector3.new(0, 3.0, 0))
			end
			-- a slow arc in front of them at eye height (they face it)
			local c = (groupAt or origin.Position) + Vector3.new(0, 3.4, 0)
			local face = if mapDef and mapDef.outroGroup and mapDef.outroGroup[4] then (origin * CFrame.Angles(0, math.rad(mapDef.outroGroup[4]), 0)).LookVector else Vector3.new(0, 0, 1)
			local dir = CFrame.fromAxisAngle(Vector3.yAxis, Cine.lerp(-0.45, 0.35, Cine.ease(u))) * face
			return CFrame.lookAt(c + dir * Cine.lerp(10.5, 8.5, Cine.ease(u)) + Vector3.new(0, 1.6, 0), c)
		end
	end
	-- the pull back: from the screen filling the frame (its picture continuing the house's view) out into the room
	local fovPull = 50
	local function fillDist(): number return (sd.size.Y / 2) / math.tan(math.rad(fovPull) / 2) * 1.02 end
	local scrN = screen.CFrame.LookVector -- (out of the screen, toward the room)
	local scrP = screen.Position
	local pullEnd: CFrame
	local reveal: (number) -> CFrame
	if set == "A" then
		local s = spot("deskSeat")
		local over = s.Position + s.RightVector * 2.2 + Vector3.new(0, 2.2, 0) + s.LookVector * -3.6
		pullEnd = CFrame.lookAt(over, scrP + Vector3.new(0, -0.4, 0))
		local headAt: Vector3? = nil
		local function seatedHead(): Vector3 -- (where the sitter's head is as the reveal starts: held, so the lens stays calm)
			if headAt then return headAt end
			for _, b in roomBodies do
				local h = b.m:FindFirstChild("Head") :: BasePart?
				if h then headAt = h.Position; return h.Position end
			end
			return s.Position + Vector3.new(0, 3.6, 0)
		end
		local revealFrom: Vector3? = nil
		reveal = function(u) -- (v6 framed her chest, head out of shot; v7 sat behind the monitor: the first spot that sees her face)
			local e = Cine.ease(u)
			local hd = seatedHead()
			if not revealFrom then
				local ex = RaycastParams.new()
				ex.FilterType = Enum.RaycastFilterType.Exclude
				local mine: { Instance } = {}
				for _, b in roomBodies do table.insert(mine, b.m) end
				ex.FilterDescendantsInstances = mine
				for _, c in { { 3.0, 2.6 }, { 2.2, 3.4 }, { 1.2, 3.8 }, { 3.0, -2.6 }, { 2.2, -3.4 }, { 0.4, 4.0 }, { 0.4, -4.0 }, { -1.2, 3.6 } } do
					local p = s.Position + s.LookVector * c[1] * 1.6 + s.RightVector * c[2] * 1.6 -- (v8, v9: wider; her head was cut)
					p = Vector3.new(p.X, hd.Y + 0.3, p.Z)
					if not workspace:Raycast(hd, p - hd, ex) then revealFrom = p; break end
					p = Vector3.new(hd.X, p.Y, hd.Z) + (p - Vector3.new(hd.X, p.Y, hd.Z)) / 1.6 -- (blocked further out: try the old distance)
					if not workspace:Raycast(hd, p - hd, ex) then revealFrom = p; break end
				end
				if not revealFrom then revealFrom = hd + s.RightVector * 2.6 + Vector3.new(0, 0.4, 0) end
			end
			local p0 = revealFrom :: Vector3
			return CFrame.lookAt(p0 + (hd - p0).Unit * 0.5 * e, hd + Vector3.new(0, 0.1, 0)) -- (a slow push in, on her face)
		end
	else
		local c = spot("couch")
		pullEnd = CFrame.lookAt(c.Position + c.LookVector * -3.4 + Vector3.new(0, 5.0, 0), scrP + Vector3.new(0, -0.6, 0))
		reveal = function(u)
			local e = Cine.ease(u)
			-- (v3: with their hips fitted onto the seats the old lens framed only laps: higher, further back, on faces)
			local from = scrP + scrN * Cine.lerp(2.2, 2.8, e) + c.RightVector * Cine.lerp(3.2, 2.8, e) + Vector3.new(0, 0.9, 0)
			return CFrame.lookAt(from, c.Position + Vector3.new(-0.6, 4.4, 0))
		end
	end
	local smoother = function(u: number): number u = math.clamp(u, 0, 1); return u * u * u * (u * (u * 6 - 15) + 10) end
	local shots = {
		{ name = "house", t0 = 0, t1 = beat("glitch"), fov = 58, shake = function(u) return if win == "gunman" then 1.2 else 0 end,
			cam = function(u)
				-- (the hit-stop: the last hitstop s before the glitch the house holds on one frame, the lens kicking)
				local hs = OUT.hitstop or 0.2
				local run = math.max(0.1, beat("glitch") - hs)
				local tt = u * beat("glitch")
				if tt >= run then return lastHouseCF end
				local cf = houseCam(tt / run); lastHouseCF = cf; return cf
			end },
		{ name = "glitch", t0 = beat("glitch"), t1 = beat("pull"), fov = 58, shake = 2.5,
			cam = function(_u) return lastHouseCF end },
		{ name = "pull", t0 = beat("pull"), t1 = beat("reveal"), fov = fovPull,
			cam = function(u)
				local e = smoother(u)
				local from = CFrame.lookAt(scrP + scrN * fillDist(), scrP)
				return from:Lerp(pullEnd, e)
			end },
		{ name = "reveal", t0 = beat("reveal"), t1 = len, fov = if set == "B" then 64 else 52, shake = 0.4, cam = reveal },
	}

	-- ---------------------------------------------------------------- the look, the grade, the bars, the sound
	local cam = workspace.CurrentCamera
	local G = HC.INTRO.grade
	if G and cam then
		local cc = Instance.new("ColorCorrectionEffect")
		cc.Name = "HuntOutroGrade"
		cc.Saturation = G.saturation; cc.Contrast = G.contrast; cc.Brightness = G.brightness; cc.TintColor = G.tint
		cc.Parent = cam
		r.grade = cc
	end
	Cine.bars(true, 0.4)
	r.cine = Cine.play(shots, { clock = T, flag = "huntoutro" })
	-- (main, 27 Nov, "nothing pops in") the room, its props, the copies, the clips and the sounds load in the background
	-- from the first frame: the room isn't seen until the pull-out (beats.pull), the house copy's kit is the lobby's.
	-- No shots handed over: two of their lenses keep eased state a call ahead of the film would seed
	task.spawn(function()
		local sets: { Instance } = {}
		for _, f in r.folders do table.insert(sets, f) end
		local animIds: { string } = {}
		for _, rigIds in OUT.anims or {} do
			if type(rigIds) == "table" then
				for _, id in rigIds do if type(id) == "number" then table.insert(animIds, "rbxassetid://" .. id) end end
			end
		end
		local soundIds: { string } = {}
		for _, s in S do
			if type(s) == "table" and type(s.id) == "number" then table.insert(soundIds, "rbxassetid://" .. s.id)
			elseif type(s) == "table" then
				for _, x in s do if type(x) == "table" and type(x.id) == "number" then table.insert(soundIds, "rbxassetid://" .. x.id) end end
			end
		end
		local pts: { Vector3 } = {}
		for _, f in r.folders do
			local ok, cf = pcall(function() return (f :: any):GetPivot() end)
			if ok and typeof(cf) == "CFrame" then table.insert(pts, cf.Position) end
		end
		local w = Cine.prewarm(nil, { key = "huntoutro", sets = sets, points = pts, anims = animIds, sounds = soundIds,
			timeout = math.max(1, beat("pull") - 1), keepFor = len + 5 })
		if RunService:IsStudio() then print(("[HuntOutro] prewarm: ok %s, %.2f s, %d assets, %d pieces"):format(tostring(w.ok), w.waited, w.assets, #w.pieces)) end
		if r.alive then r.warm = w else w.release() end
	end)
	keep(sound(S.house, 1, true))
	keep(sound(S.houseTone, 1, true))
	if win ~= "gunman" then keep(sound(S.heart, 1, true)) end -- (her heartbeat under the walk)

	-- the full-screen static of the glitch (the intro's static pictures: soft grey noise, nothing readable)
	local pg = me:FindFirstChildOfClass("PlayerGui")
	local st = Instance.new("ScreenGui")
	st.Name = "CineBars_Static"; st.IgnoreGuiInset = true; st.DisplayOrder = 44; st.ResetOnSpawn = false; st.Enabled = false
	local img = Instance.new("ImageLabel")
	img.Size = UDim2.fromScale(1, 1); img.BackgroundColor3 = Color3.fromRGB(40, 42, 46); img.BorderSizePixel = 0
	img.ScaleType = Enum.ScaleType.Crop; img.Parent = st
	st.Parent = pg
	r.static = st

	local fired: { [string]: boolean } = {}
	local function once(key: string, at: number): boolean
		if fired[key] or T() < at then return false end
		fired[key] = true
		return true
	end
	local nextFrame, frame = 0, 1
	local nextClap = 0
	local holdFade: { [BasePart]: number } = {}
	local rp = RaycastParams.new()
	rp.FilterType = Enum.RaycastFilterType.Include
	r.conn = RunService.RenderStepped:Connect(function(dt: number)
		if not r.alive then return end
		local t = T()
		-- the survivors walk until the hit-stop holds them
		if r.door and t >= (OUT.doorAt or 4.5) and t <= beat("glitch") then -- (the front door swings open, daylight in)
			local x = math.clamp((t - (OUT.doorAt or 4.5)) / 0.9, 0, 1)
			local k = x * x * x * (x * (x * 6 - 15) + 10)
			for _, d in r.door do d.leaf.CFrame = d.at(k * math.rad(100)) end
			if r.daylight then r.daylight.Brightness = 3.0 * k end
			if not r.doorSnd then
				r.doorSnd = true
				local lib = ReplicatedStorage:FindFirstChild("JankfireSounds")
				local ds = lib and lib:FindFirstChild("hunt_door_open")
				if ds and ds:IsA("Sound") then local c = ds:Clone(); c.Parent = SoundService; c:Play(); c.Ended:Once(function() c:Destroy() end) end
			end
		end
		if r.placeGroup then
			local run = math.max(0.1, beat("glitch") - (OUT.hitstop or 0.2))
			if t <= run then r.placeGroup(math.max(0, t)) end
			for _, b in bodies do -- (each walk on its own step: a phase off the others once the clip has loaded)
				if b.walk and not b.phased and b.walk.Length > 0 then b.phased = true; b.walk.TimePosition = b.walk.Length * ((b.g and b.g.phase) or 0) end
			end
		end
		-- each sitter's hips onto its seat once the seated clip has them down, whatever the avatar's size (owner, 27 Nov:
		-- "make sure they're actually sitting and not clipped")
		for _, b in roomBodies do
			if b.kind == "seat" and not b.fitted and b.sit and b.sit.IsPlaying and b.sit.TimePosition > 0.12 then
				b.fitted = true
				local lowest = math.huge
				for _, nm in { "LowerTorso", "LeftUpperLeg", "RightUpperLeg", "Torso", "Left Leg", "Right Leg" } do
					local pt = b.m:FindFirstChild(nm)
					if pt and pt:IsA("BasePart") then
						local cf, sz = pt.CFrame, pt.Size
						local hh = 0.5 * (math.abs(cf.RightVector.Y) * sz.X + math.abs(cf.UpVector.Y) * sz.Y + math.abs(cf.LookVector.Y) * sz.Z)
						-- (an R6 leg is one piece, thigh and shin: its middle is what lies on the seat)
						lowest = math.min(lowest, if nm == "Left Leg" or nm == "Right Leg" then pt.Position.Y - 0.5 else pt.Position.Y - hh)
					end
				end
				if lowest < math.huge then b.m:PivotTo(b.m:GetPivot() + Vector3.new(0, b.seatY + 0.05 - lowest, 0)) end
			end
		end
		-- the film owns the screen: every HUD off but the bars and the static
		if pg then
			for _, g in pg:GetChildren() do
				if g:IsA("ScreenGui") and g.Name ~= "CineBars" and g ~= st then
					if r.guis[g] == nil then r.guis[g] = g.Enabled end
					if g.Enabled then g.Enabled = false end
				end
			end
		end
		-- static frames (the glitch on the whole screen; the TV's own snow)
		if os.clock() >= nextFrame then
			nextFrame = os.clock() + 1 / 15
			frame = (frame % #HC.INTRO.static) + 1
			local id = "rbxassetid://" .. tostring(HC.INTRO.static[frame])
			img.Image = id
			snow.Image = id
		end
		-- the last pink cubes fade as he walks
		if r.cubes then
			local f = math.clamp(t / math.max(0.5, beat("glitch")), 0, 1)
			for _, c in r.cubes do c.Transparency = f * 0.85 end
		end
		if r.fill then r.fill.Position = workspace.CurrentCamera.CFrame.Position end
		-- the hit-stop before the glitch: the house holds for a beat, the lens kicks, then static
		if once("stop", beat("glitch") - (OUT.hitstop or 0.2)) then
			if r.cine then r.cine.kick(10) end
			for _, b in bodies do
				local hum = b.m:FindFirstChildOfClass("Humanoid")
				local an = hum and hum:FindFirstChildOfClass("Animator")
				if an then for _, tr in (an :: Animator):GetPlayingAnimationTracks() do tr:AdjustSpeed(0) end end
			end
		end
		if once("glitch", beat("glitch")) then
			st.Enabled = true
			sound(S.burst, 1)
			-- the house's view into the screen's picture: its nearby pieces, as the lens saw them a moment ago
			vcam.CFrame = lastHouseCF
			vcam.FieldOfView = 58
			local near = lastHouseCF.Position
			local src = { house, map }
			for _, root in src do
				if root then
					for _, d in (root :: Instance):GetDescendants() do
						if d:IsA("BasePart") and d.Transparency < 0.95 and (d.Position - near).Magnitude - d.Size.Magnitude / 2 < 140 then
							local ok, c = pcall(function() return d:Clone() end)
							if ok and c then for _, ch in c:GetChildren() do if not (ch:IsA("SpecialMesh") or ch:IsA("SurfaceAppearance") or ch:IsA("Decal") or ch:IsA("Texture")) then ch:Destroy() end end; c.Parent = vp end
						end
					end
				end
			end
			for _, b in bodies do
				for _, d in b.m:GetDescendants() do
					if d:IsA("BasePart") and d.Transparency < 0.95 then
						local ok, c = pcall(function() return d:Clone() end)
						if ok and c then c.Parent = vp end
					end
				end
			end
			vp:SetAttribute("Pieces", #vp:GetChildren()) -- (a debug read: how many pieces the screen's picture holds)
			for _, s in r.sounds do pcall(function() s:Stop() end) end
			room.Parent = workspace -- (under the static: the pull's first frame is never an empty sky)
		end
		if once("room", beat("pull")) then
			st.Enabled = false
			house:Destroy()
			for _, m in who do hide(m, false) end
			HubLook.set("hunt_intro_dark", 0)
			local F = OUT.fill
			if F then -- (main on v8: the pull out read near black on a phone: a soft fill rides with the lens)
				local fp = Instance.new("Part")
				fp.Name = "HuntOutroFill"; fp.Anchored = true; fp.CanCollide = false; fp.CanQuery = false; fp.CanTouch = false
				fp.Transparency = 1; fp.Size = Vector3.new(0.2, 0.2, 0.2); fp.CastShadow = false
				fp.Position = workspace.CurrentCamera.CFrame.Position
				local fl = Instance.new("PointLight")
				fl.Brightness = F.brightness; fl.Range = F.range; fl.Shadows = false; fl.Color = Color3.fromRGB(214, 222, 236)
				fl.Parent = fp
				fp.Parent = room
				r.fill = fp; r.fillLight = fl
			end
			keep(sound(if set == "A" then S.hum else S.hiss, 1, true))
			-- the players at the screen: seated (and a stretch for him), pads in hand and cheering for them
			for i, b in roomBodies do
				local id = (OUT.anims[b.rig] or {})
				if b.kind == "seat" then
					local s = track(b.m, id.sit, Enum.AnimationPriority.Action)
					if s then s.Looped = true; s:Play(0); b.sit = s end
				else
					local s = track(b.m, HC.ANIMS[b.rig] and HC.ANIMS[b.rig].idle, Enum.AnimationPriority.Action)
					if s then s.Looped = true; s:Play(0); s.TimePosition = i * 0.4 end
				end
				if set == "B" then
					local hand = b.m:FindFirstChild("RightHand") or b.m:FindFirstChild("Right Arm")
					local pad = piece(kit, "hiB_pad", CFrame.new(), b.m)
					if pad and hand and hand:IsA("BasePart") then
						local at = hand.CFrame * CFrame.new(0, if b.rig == "R6" then -1.0 else -0.25, -0.35)
						for _, pp in pad:GetDescendants() do
							if pp:IsA("BasePart") then
								pp.CFrame = at * pp.CFrame
								pp.Anchored = false; pp.CanCollide = false; pp.Massless = true
								local w = Instance.new("WeldConstraint"); w.Part0 = hand; w.Part1 = pp; w.Parent = pp
							end
						end
					end
				end
			end
			if set == "A" then sound(S.keys, 1, false, P(Data.screens.A.at), room) end
		end
		-- the reveal: he leans back and stretches; they cheer, clap, click their pads
		if once("reveal", beat("reveal")) then
			if r.fillLight then TweenService:Create(r.fillLight, TweenInfo.new(0.8), { Brightness = (OUT.fill and OUT.fill.reveal) or 0.2 }):Play() end
			for i, b in roomBodies do
				local id = (OUT.anims[b.rig] or {})
				if set == "A" then
					local s = track(b.m, id.stretch, Enum.AnimationPriority.Action2)
					if s then s:Play(0.8, 1, OUT.stretchSpeed or 0.75) end -- (owner: "too snappy": slower, eased in)
					sound(S.creak, 0.8, false, b.m:GetPivot().Position, room)
				else
					local pick = if i % 3 == 1 then id.cheer elseif i % 3 == 2 then id.clap else id.pump
					local s = track(b.m, pick, Enum.AnimationPriority.Action2)
					if s then s.Looped = (pick == id.clap); s:Play(0.2) end
					if i == 1 then sound(S.creak, 0.8, false, b.m:GetPivot().Position, room) end
					sound(S.pad, 0.9, false, b.m:GetPivot().Position, room)
				end
			end
		end
		if set == "B" and t >= beat("reveal") + 0.25 and os.clock() >= nextClap and #roomBodies > 0 then
			nextClap = os.clock() + 0.18 + math.random() * 0.22
			local b = roomBodies[math.random(1, #roomBodies)]
			local claps = S.claps or {}
			if #claps > 0 then sound(claps[math.random(1, #claps)], 0.55 + math.random() * 0.3, false, b.m:GetPivot().Position, room) end
		end
		-- (owner, 27 Nov: hair and heads see-through: nothing anyone wears fades any more; everyone stays solid)
		local _ = holdFade
		if t >= len then stop() end
	end)
end

Remote.OnClientEvent:Connect(function(op: string, a: any)
	if op == "outro" then
		task.spawn(play, a)
	elseif op == "results" then
		if running then stop() end
	end
end)
me:GetAttributeChangedSignal("Hunt"):Connect(function()
	if me:GetAttribute("Hunt") ~= "round" and running then stop() end
end)
