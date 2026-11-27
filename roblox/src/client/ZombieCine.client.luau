--!strict
-- ZOMBIES' films (27 Nov 2026; roblox/docs/ZOMBIES.md 4.3; the owner: "cinematic for zombies mode please!!"). Both on
-- this client, timed by the server's clock from attributes on the arena model (server/ZombieExtract.luau), the camera,
-- bars, shake and kicks from CineKit.
--   the intro (IntroT0, IntroLen 7.5 s, skippable: Space, Enter, A, or SKIP on a phone): high over the school at night
--     in the fog with the title card; low by a boarded lobby window as a zombie lurches out of the fog into the boards
--     (a hit: a short hit-stop, a kick, zm_board and zm_planks); the squad in the lobby, low and wide, the bars lift and
--     the camera lands on your own view. Round 1 waits for it (the server).
--   the extraction out (XSt "out", XLift): wide from a roof corner as the squad runs into the helicopter's open side
--     and zombies spill onto the roof; low under the tail as it lifts and pulls away; high and far as it goes into the
--     fog, a fade; then the reward screen (ZombieExtract.client).
-- Rules (main, 27 Nov): animation cycles and mocap only (the zombie's own walk cycle, everyone's own run), recordings
-- only (zm_wind, zm_board, zm_planks; the helicopter's zm_heli plays on it in ZombieExtract.client; the boom), no
-- voices, the school's own muted night look, no text in the world: only the title card.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local SoundService = game:GetService("SoundService")
local TweenService = game:GetService("TweenService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local ZM = require(Shared:WaitForChild("ZM"))
local Cine = require(script.Parent:WaitForChild("CineKit")) :: any
local T = require(script.Parent:WaitForChild("Theme")) :: any
local Keys = require(script.Parent:WaitForChild("Keys")) :: any
local okSfx, Sfx = pcall(require, script.Parent:WaitForChild("Sfx"))
local zr = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Zm") :: RemoteEvent
local me = Players.LocalPlayer
local XC = ZM.X
local ZOMBIE_WALK = "rbxassetid://616168032" -- (Roblox's own zombie walk cycle, as the mode's zombies use)
local function srv(): number return workspace:GetServerTimeNow() end
local function flat(v: Vector3): Vector3 return Vector3.new(v.X, 0, v.Z) end
local function arena(): Model?
	local n = me:GetAttribute("ZmArena")
	local a = if type(n) == "string" then workspace:FindFirstChild(n) else nil
	return if a and a:IsA("Model") then a else nil
end
local function sfx(name: string, at: Vector3?, vol: number?)
	if okSfx and Sfx then pcall((Sfx :: any).play, name, at, vol) end
end
-- a looped bed: the library's Sound, cloned (loops can't go through Sfx.play), 2D, from silence
local function bed(name: string): Sound?
	local lib = ReplicatedStorage:FindFirstChild("JankfireSounds")
	local src = lib and lib:FindFirstChild(name)
	if not src or not src:IsA("Sound") then return nil end
	local s = src:Clone()
	s.Looped = true
	local full = s.Volume
	s:SetAttribute("Full", full)
	s.Volume = 0
	s.Parent = SoundService
	s:Play()
	return s
end
local function fade(s: Sound?, k: number, dur: number)
	if not s then return end
	local full = tonumber(s:GetAttribute("Full")) or 0.5
	TweenService:Create(s, TweenInfo.new(dur, Enum.EasingStyle.Sine), { Volume = full * k }):Play()
end
local okLook, HubLook = pcall(require, Shared:WaitForChild("HubLook"))
-- a film's key light: a soft cold light that rides with the camera (27 Nov test: at night in the school's look the
-- helicopter and the squad were black shapes on black). on this client only
local function keyLight(r: any, range: number, bright: number): BasePart
	local p = Instance.new("Part")
	p.Name = "ZmKeyLight"
	p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch = true, false, false, false
	p.Transparency = 1
	p.Size = Vector3.new(0.2, 0.2, 0.2)
	local l = Instance.new("PointLight")
	l.Range = range; l.Brightness = bright; l.Color = Color3.fromRGB(206, 216, 236); l.Shadows = false
	l.Parent = p
	p.Parent = workspace
	table.insert(r.trash, p)
	return p
end
-- the moon (27 Nov, main: "the intro reads almost black on a phone"): while a film plays, a cool fill on the night (the
-- school's ambient lifted, a touch more exposure, the haze a little thinner) so the school's shape and the squad read;
-- the look's own values back when it ends. still night: no sun, the same cold tint
local Lighting = game:GetService("Lighting")
-- (high: the fly-over's own, stronger: from 60-70 studs up the school was still a black shape in the haze on a phone)
local function moon(r: any, k: number, high: boolean?, dur: number?)
	local atm = Lighting:FindFirstChildOfClass("Atmosphere")
	r.moonWas = r.moonWas or { amb = Lighting.Ambient, out = Lighting.OutdoorAmbient, exp = Lighting.ExposureCompensation,
		dens = if atm then atm.Density else nil }
	local w = r.moonWas
	local ti = TweenInfo.new(dur or 0.35, Enum.EasingStyle.Sine)
	local amb = if high then Color3.fromRGB(118, 130, 160) else Color3.fromRGB(92, 104, 132)
	local out = if high then Color3.fromRGB(138, 156, 196) else Color3.fromRGB(104, 120, 158)
	TweenService:Create(Lighting, ti, { Ambient = w.amb:Lerp(amb, k), OutdoorAmbient = w.out:Lerp(out, k),
		ExposureCompensation = w.exp + (if high then 0.95 else 0.55) * k }):Play()
	if atm and w.dens then TweenService:Create(atm, ti, { Density = w.dens * (1 - (if high then 0.45 else 0.3) * k) }):Play() end
end
local function moonBack(r: any)
	local w = r.moonWas
	if not w then return end
	r.moonWas = nil
	local ti = TweenInfo.new(0.5, Enum.EasingStyle.Sine)
	TweenService:Create(Lighting, ti, { Ambient = w.amb, OutdoorAmbient = w.out, ExposureCompensation = w.exp }):Play()
	local atm = Lighting:FindFirstChildOfClass("Atmosphere")
	if atm and w.dens then TweenService:Create(atm, ti, { Density = w.dens }):Play() end
end

-- the title card, the skip line, the fade
local gui = T.new("ScreenGui", { Name = "JankZmCine", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 47, Enabled = true }, me:WaitForChild("PlayerGui"))
local title = T.text(gui, "Title", "", 34, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Left, true)
title.AnchorPoint = Vector2.new(0, 1); title.Position = UDim2.new(0, 56, 1, -110); title.Size = UDim2.fromOffset(700, 40)
title.TextTransparency = 1; title.TextStrokeTransparency = 1
local skipL = T.text(gui, "Skip", "", 13, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Right, true)
skipL.AnchorPoint = Vector2.new(1, 1); skipL.Position = UDim2.new(1, -40, 1, -24); skipL.Size = UDim2.fromOffset(260, 18)
local skipB = T.new("TextButton", { Name = "SkipButton", AnchorPoint = Vector2.new(1, 1), BackgroundColor3 = T.BG, BackgroundTransparency = 0.25,
	BorderSizePixel = 0, Text = "SKIP", TextColor3 = T.TEXT, FontFace = T.FONT_BOLD, TextSize = 14, Visible = false,
	Position = UDim2.new(1, -24, 1, -20), Size = UDim2.fromOffset(84, 34) }, gui)
T.corner(skipB)
local black = T.new("Frame", { Name = "Fade", BackgroundColor3 = Color3.new(0, 0, 0), BorderSizePixel = 0, BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, gui)
local function card(text: string, on: boolean, dur: number)
	title.Text = text
	TweenService:Create(title, TweenInfo.new(dur, Enum.EasingStyle.Sine), { TextTransparency = if on then 0 else 1, TextStrokeTransparency = if on then 0.6 else 1 }):Play()
end

-- while a film runs: every other HUD off (held each frame: some set themselves), the first-person gun hidden, your
-- own body shown; all put back after
local film: any = nil
local function hold(r: any)
	local pg = me:FindFirstChild("PlayerGui")
	if pg then
		for _, g in pg:GetChildren() do
			if g:IsA("ScreenGui") and g ~= gui and g.Name ~= "CineBars" and not (r.keep and r.keep[g.Name]) then
				if r.guis[g] == nil then r.guis[g] = g.Enabled end
				if g.Enabled then g.Enabled = false end
			end
		end
	end
	local cam = workspace.CurrentCamera
	for _, d in cam:GetDescendants() do
		if d:IsA("BasePart") and d.LocalTransparencyModifier < 1 then
			if r.vm[d] == nil then r.vm[d] = d.LocalTransparencyModifier end
			d.LocalTransparencyModifier = 1
		end
	end
	local ch = me.Character
	if ch and (r.showMe or r.showOnly) then
		-- (showOnly: just those parts of your body, the rest hidden: the extraction film's own hand at the lens)
		for _, d in ch:GetDescendants() do
			if (d:IsA("BasePart") or d:IsA("Decal")) and d.Name ~= "HumanoidRootPart" then
				local part = if d:IsA("Decal") then d.Parent else d
				local want = if r.showOnly then (if part and r.showOnly[part.Name] then 0 else 1) else 0
				if (d :: any).LocalTransparencyModifier ~= want then (d :: any).LocalTransparencyModifier = want end
			end
		end
	end
end
local function finish(handBack: boolean)
	local r = film
	if not r then return end
	film = nil
	if r.conn then r.conn:Disconnect() end
	for g, was in r.guis do if g.Parent then g.Enabled = was end end
	for d, was in r.vm do if d.Parent then d.LocalTransparencyModifier = was end end
	for _, x in r.trash do pcall(function() x:Destroy() end) end
	for _, s in r.beds do fade(s, 0, 0.5); task.delay(0.6, function() s:Destroy() end) end
	Cine.bars(false, 0.25)
	card("", false, 0.2)
	skipL.Text = ""; skipB.Visible = false
	if r.cine then r.cine.stop(handBack) end
	moonBack(r)
	me:SetAttribute("ZmFilm", nil) -- (the zombies HUD back: ZombiesClient)
	if r.onEnd then pcall(r.onEnd) end
end

-- ------------------------------------------------------------------ the intro: a news broadcast
-- (27 Nov, the owner: "have a news broadcast actually for the intro a zombies, it'll be like breaking news" and "Then it
-- cuts to shot of the school"). All its words are live UI here, never in a picture: BREAKING NEWS, LIVE and the one
-- headline, nothing else (no ticker, no flavour lines, zombie words only). No voices. The times: ZM.X.news.
--   the feed: a news helicopter's camera over the school's front at night (grain, scan lines, zoom brackets, focus
--     breathing, its searchlight sweeping the grounds, the moon so the school reads), the news sting and the rotor
--     wash; it zooms onto a boarded lobby window as a zombie slams the planks
--   the hit: the feed breaks into static, then black (signal lost)
--   the school: our own lens, outside at night in the fog, a slow push, the wind
--   the squad in the lobby, the bars lift, your own view
local NEWS_INK, NEWS_BONE = Color3.fromRGB(29, 31, 35), Color3.fromRGB(229, 226, 219) -- (A PLATE's ink and bone)
local function newsOverlay(r: any): any
	local o: any = {}
	local root = T.new("Frame", { Name = "Feed", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, gui)
	table.insert(r.trash, root)
	o.root = root
	-- scan lines and grain
	o.scan = {}
	for k = 1, 26 do
		local f = T.new("Frame", { BackgroundColor3 = Color3.new(1, 1, 1), BackgroundTransparency = 0.94, BorderSizePixel = 0,
			Size = UDim2.new(1, 0, 0, 2), Position = UDim2.fromScale(0, k / 26) }, root)
		table.insert(o.scan, f)
	end
	o.grain = {}
	for k = 1, 90 do
		local f = T.new("Frame", { BackgroundColor3 = if k % 2 == 0 then Color3.new(1, 1, 1) else Color3.new(0, 0, 0), BackgroundTransparency = 0.55,
			BorderSizePixel = 0, Size = UDim2.fromOffset(3, 3) }, root)
		table.insert(o.grain, f)
	end
	-- the zoom brackets: four corners round a box that closes in with the zoom
	o.box = T.new("Frame", { Name = "Brackets", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromScale(0.5, 0.5) }, root)
	for _, c in { { 0, 0 }, { 1, 0 }, { 0, 1 }, { 1, 1 } } do
		local h = T.new("Frame", { BackgroundColor3 = Color3.new(1, 1, 1), BackgroundTransparency = 0.15, BorderSizePixel = 0, AnchorPoint = Vector2.new(c[1], c[2]),
			Position = UDim2.fromScale(c[1], c[2]), Size = UDim2.fromOffset(34, 3) }, o.box)
		local v = T.new("Frame", { BackgroundColor3 = Color3.new(1, 1, 1), BackgroundTransparency = 0.15, BorderSizePixel = 0, AnchorPoint = Vector2.new(c[1], c[2]),
			Position = UDim2.fromScale(c[1], c[2]), Size = UDim2.fromOffset(3, 34) }, o.box)
		local _ = h; local _ = v
	end
	-- LIVE, top left
	local live = T.new("Frame", { Name = "Live", BackgroundColor3 = NEWS_INK, BackgroundTransparency = 0.1, BorderSizePixel = 0, Position = UDim2.fromOffset(40, 36), Size = UDim2.fromOffset(96, 34) }, root)
	T.new("UICorner", { CornerRadius = UDim.new(0, 3) }, live)
	o.dot = T.new("Frame", { BackgroundColor3 = Color3.fromRGB(214, 48, 44), BorderSizePixel = 0, Position = UDim2.fromOffset(12, 11), Size = UDim2.fromOffset(12, 12) }, live)
	T.new("UICorner", { CornerRadius = UDim.new(1, 0) }, o.dot)
	local lt = T.text(live, "L", "LIVE", 18, NEWS_BONE, T.FONT_HEAVY); lt.Position = UDim2.fromOffset(32, 0); lt.Size = UDim2.new(1, -36, 1, 0)
	-- the lower third: BREAKING NEWS slams in, the headline under it
	o.third = T.new("Frame", { Name = "Third", BackgroundTransparency = 1, Position = UDim2.new(0, -720, 1, -190), Size = UDim2.fromOffset(640, 104) }, root)
	local bn = T.new("Frame", { BackgroundColor3 = NEWS_INK, BorderSizePixel = 0, Size = UDim2.fromOffset(420, 56) }, o.third)
	T.new("UICorner", { CornerRadius = UDim.new(0, 3) }, bn)
	local bt = T.text(bn, "B", "BREAKING NEWS", 34, NEWS_BONE, T.FONT_HEAVY); bt.Position = UDim2.fromOffset(18, 0); bt.Size = UDim2.new(1, -24, 1, 0)
	o.line = T.new("Frame", { BackgroundColor3 = NEWS_BONE, BorderSizePixel = 0, Position = UDim2.fromOffset(0, 60), Size = UDim2.fromOffset(0, 40), ClipsDescendants = true }, o.third)
	T.new("UICorner", { CornerRadius = UDim.new(0, 3) }, o.line)
	local ht = T.text(o.line, "H", "OUTBREAK  ·  JANKFIELD HIGH", 22, NEWS_INK, T.FONT_HEAVY); ht.Position = UDim2.fromOffset(16, 0); ht.Size = UDim2.fromOffset(600, 40)
	-- the static: a black screen of grey blocks, new each frame, and a few tear bars
	o.static = T.new("Frame", { Name = "Static", BackgroundColor3 = Color3.new(0, 0, 0), BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), Visible = false }, gui)
	table.insert(r.trash, o.static)
	o.snow = {}
	for k = 1, 240 do
		local f = T.new("Frame", { BackgroundColor3 = Color3.new(1, 1, 1), BorderSizePixel = 0, Size = UDim2.fromOffset(4, 3) }, o.static)
		table.insert(o.snow, f)
	end
	o.tears = {}
	for k = 1, 5 do
		local f = T.new("Frame", { BackgroundColor3 = Color3.new(1, 1, 1), BackgroundTransparency = 0.6, BorderSizePixel = 0, Size = UDim2.new(1, 0, 0, 6) }, o.static)
		table.insert(o.tears, f)
	end
	return o
end

local function intro(a: Model)
	local t0 = a:GetAttribute("IntroT0")
	local len = tonumber(a:GetAttribute("IntroLen")) or XC.intro
	if type(t0) ~= "number" or srv() > t0 + len - 1.2 or film then return end
	local okM, map = pcall(ZM.read, a)
	if not okM or not map then return end
	local site = a:GetPivot()
	local function L(x: number, y: number, z: number): Vector3 return site:PointToWorldSpace(Vector3.new(x, y, z)) end
	local N = XC.news
	local r: any = { guis = {}, vm = {}, trash = {}, beds = {}, showMe = false, kind = "intro" }
	film = r
	me:SetAttribute("ZmFilm", true)
	if okLook and HubLook and HubLook.byArena and HubLook.byArena[a.Name] then pcall(HubLook.set, HubLook.byArena[a.Name], 0) end
	-- the news helicopter's camera for a window: out from it and up, drifting in (27 Nov test: from 90+ studs out the
	-- school's haze left the feed black; about 50 out it reads)
	local function feedFrom(at: Vector3, out: Vector3): (Vector3, Vector3)
		local sd = out:Cross(Vector3.new(0, 1, 0))
		return at + out * 58 + Vector3.new(0, 30, 0) - sd * 20, at + out * 46 + Vector3.new(0, 22, 0) - sd * 8
	end
	-- the window for the zoom: a lobby window the feed can see (27 Nov test: the front-most one was under the entrance's
	-- canopy behind a lamp post, a black hole at the zoom): a clear line from both camera spots, open sky above it, then
	-- the school's front (the most +z in the arena's frame)
	local rp = RaycastParams.new()
	rp.FilterType = Enum.RaycastFilterType.Exclude
	local ex = {}
	for _, pl in Players:GetPlayers() do if pl.Character then table.insert(ex, pl.Character) end end
	rp.FilterDescendantsInstances = ex
	local function clear(from: Vector3, to: Vector3): boolean return workspace:Raycast(from, to - from, rp) == nil end
	local w, best = nil, -math.huge
	for _, cand in map.windows do
		if cand.area ~= map.start then continue end
		local out = flat(cand.out - cand.inn).Unit
		local at = cand.at.Position
		local q0, q1 = feedFrom(at, out)
		local tgt = at + out * 2 + Vector3.new(0, 1, 0)
		local score = site:VectorToObjectSpace(out).Z
			+ (if clear(q0, tgt) then 2 else 0) + (if clear(q1, tgt) then 2 else 0)
			+ (if clear(at + out * 2.5, at + out * 2.5 + Vector3.new(0, 40, 0)) then 1 else 0)
		if score > best then best, w = score, cand end
	end
	w = w or map.windows[1]
	local outward = if w then flat(w.out - w.inn).Unit else site.LookVector * -1
	local side = outward:Cross(Vector3.new(0, 1, 0))
	local zroot: BasePart? = nil
	local src = ReplicatedStorage:FindFirstChild("JankfireZmCine")
	local zt = src and src:FindFirstChild("Zombie")
	if w and zt and zt:IsA("Model") then
		local m = zt:Clone()
		for _, d in m:GetDescendants() do if d:IsA("BasePart") then d.CanCollide = false; d.CanQuery = false; d.CanTouch = false end end
		zroot = m:FindFirstChild("HumanoidRootPart") :: BasePart?
		if zroot then zroot.Anchored = true end
		m.Parent = workspace
		table.insert(r.trash, m)
		local hum = m:FindFirstChildOfClass("Humanoid")
		if hum then
			local an = hum:FindFirstChildOfClass("Animator") or Instance.new("Animator", hum)
			local anim = Instance.new("Animation"); anim.AnimationId = ZOMBIE_WALK
			local ok, tr = pcall(function() return (an :: Animator):LoadAnimation(anim) end)
			if ok and tr then tr.Looped = true; tr:Play(0); r.walk = tr end
		end
	end
	local winAt = if w then w.at.Position else L(0, 6, 96)
	local zFrom = if w then w.out + outward * 9 else Vector3.zero
	local zTo = if w then w.out + outward * 1.4 else Vector3.zero
	-- the squad: their spawns' middle, the camera in front of them
	local c, face = Vector3.zero, Vector3.new(0, 0, -1)
	if #map.spawns > 0 then
		for _, s in map.spawns do c += s.Position end
		c /= #map.spawns
		face = flat(map.spawns[1].LookVector)
		if face.Magnitude < 0.1 then face = Vector3.new(0, 0, -1) end
		face = face.Unit
	end
	-- the news helicopter's camera: out front and up, drifting in; then the zoom onto the window
	local hp0, hp1 = feedFrom(winAt, outward)
	local front = winAt - outward * 22 + Vector3.new(0, 4, 0) -- (the wide: the building behind the window, its roof line)
	local deep = winAt - outward * 36 + Vector3.new(0, 10, 0) -- (the school shot looks into the building past the window)
	local function feedCam(t: number): (CFrame, number)
		local u = math.clamp(t / N.hit, 0, 1)
		local at = hp0:Lerp(hp1, u)
		local z0, z1 = N.zoom[1], N.zoom[2]
		local zu = math.clamp((t - z0) / (z1 - z0), 0, 1)
		zu = zu * zu * (3 - 2 * zu)
		-- (the zoom frames the boards and the zombie at them: 27 Nov test, on the window's middle the planter's hedge hid
		-- him below the frame)
		local look = front:Lerp(winAt + outward * 1.2 - Vector3.new(0, 1.6, 0), zu)
		local dist = (winAt - at).Magnitude
		local fovWin = math.deg(2 * math.atan(10.5 / dist))
		local fov = (34 + 1.2 * math.sin(t * 1.7)) * (1 - zu) + (fovWin + 0.4 * math.sin(t * 2.3)) * zu -- (the lens breathing)
		return CFrame.lookAt(at, look), fov
	end
	local shots = {
		{ name = "feed", t0 = 0, t1 = N.static[2], shake = 0.32,
			cam = function(u: number): CFrame local cf = feedCam(u * N.static[2]); return cf end,
			fov = function(u: number): number local _, f = feedCam(u * N.static[2]); return f end },
		{ name = "school", t0 = N.school[1] - 0.15, t1 = N.school[2], ease = "linear", shake = 0.12,
			from = { at = winAt + outward * 58 + Vector3.new(0, 5, 0) + side * 30, look = deep, fov = 46 },
			to = { at = winAt + outward * 47 + Vector3.new(0, 6.5, 0) + side * 24, look = deep - Vector3.new(0, 1, 0), fov = 44 } },
		{ name = "squad", t0 = N.squad[1], t1 = N.squad[2], ease = "out", shake = 0.15,
			from = { at = c + face * 22 + Vector3.new(0, 4.2, 0), look = c + Vector3.new(0, 2.8, 0), fov = 54 },
			to = { at = c + face * 17 + Vector3.new(0, 3.8, 0), look = c + Vector3.new(0, 3.0, 0), fov = 52 } },
		{ name = "land", t0 = N.squad[2], t1 = len, ease = "inout",
			from = { at = c + face * 17 + Vector3.new(0, 3.8, 0), look = c + Vector3.new(0, 3.0, 0), fov = 52 }, to = "gameplay" },
	}
	local function clk(): number return srv() - (t0 :: number) end
	-- (flag: HubLife leaves the light alone while it plays; 27 Nov test, its zone switch into the match ran the map room's
	-- black haze over the feed's first half second)
	r.cine = Cine.play(shots, { clock = clk, warm = 0.3, flag = "zmintro" })
	moon(r, 1, true, 0.01)
	-- (the feed only: the haze thinner still, a long lens through 50 studs of it; the school shot puts the moon's back)
	local fatm = Lighting:FindFirstChildOfClass("Atmosphere")
	if fatm and r.moonWas and r.moonWas.dens then TweenService:Create(fatm, TweenInfo.new(0.01), { Density = r.moonWas.dens * 0.3 }):Play() end -- (a tween: it replaces the moon's)
	-- the feed's look: a little colder and flatter (a camera's, on this screen only), its sounds, the searchlight
	local cc = Instance.new("ColorCorrectionEffect")
	cc.Saturation = -0.35; cc.Contrast = 0.04; cc.Brightness = 0.03; cc.TintColor = Color3.fromRGB(226, 240, 236); cc.Parent = workspace.CurrentCamera
	table.insert(r.trash, cc)
	local o = newsOverlay(r)
	local lib = ReplicatedStorage:FindFirstChild("JankfireSounds")
	local sting = nil
	if lib and lib:FindFirstChild("zm_news") then sting = (lib.zm_news :: Sound):Clone(); sting.Parent = SoundService; sting:Play(); table.insert(r.trash, sting) end
	local wash = bed("zm_heli")
	if wash then table.insert(r.beds, wash); fade(wash, 0.3, 0.4) end
	local beam = Instance.new("Part")
	beam.Anchored, beam.CanCollide, beam.CanQuery, beam.CanTouch = true, false, false, false
	beam.Transparency = 1; beam.Size = Vector3.new(0.2, 0.2, 0.2); beam.Parent = workspace
	local sl = Instance.new("SpotLight"); sl.Face = Enum.NormalId.Front; sl.Range = 60; sl.Angle = 24; sl.Brightness = 9
	sl.Color = Color3.fromRGB(236, 240, 232); sl.Shadows = true; sl.Parent = beam
	table.insert(r.trash, beam)
	local wind = nil
	local HIT = N.hit
	local hit, staticOn, schoolOn, lifted, banner, line = false, false, false, false, false, false
	skipL.Text = if Keys.isTouch() then "" else "SPACE  SKIP"
	skipB.Visible = Keys.isTouch()
	r.onEnd = function() zr:FireServer({ k = "xskip" }) end
	local rng = Random.new()
	r.conn = RunService.RenderStepped:Connect(function()
		local t = clk()
		hold(r)
		r.showMe = false
		local vs = workspace.CurrentCamera.ViewportSize
		-- the feed's overlay
		local feedOn = t < N.static[1]
		o.root.Visible = feedOn
		if feedOn then
			for k, f in o.scan do f.Position = UDim2.fromScale(0, ((k / #o.scan) + t * 0.05) % 1) end
			for _, f in o.grain do f.Position = UDim2.fromOffset(rng:NextInteger(0, math.max(1, vs.X)), rng:NextInteger(0, math.max(1, vs.Y))) end
			local zu = math.clamp((t - N.zoom[1]) / (N.zoom[2] - N.zoom[1]), 0, 1)
			o.box.Size = UDim2.fromScale(0.5 - 0.22 * zu, 0.5 - 0.2 * zu)
			o.dot.BackgroundTransparency = if (t % 1) < 0.55 then 0 else 0.7
			if not banner and t >= N.banner then
				banner = true
				TweenService:Create(o.third, TweenInfo.new(0.28, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Position = UDim2.new(0, 48, 1, -190) }):Play()
				if r.cine then r.cine.kick(0.5) end
			end
			if not line and t >= N.line then
				line = true
				TweenService:Create(o.line, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = UDim2.fromOffset(560, 40) }):Play()
			end
			-- the news helicopter's searchlight, from beside its camera: sweeping the grounds in front of the school, then
			-- held on the window for the zoom (27 Nov test: from high over the school the entrance canopy shaded it black)
			local sweep = winAt + outward * (9 + 6 * math.sin(t * 0.8)) + side * (16 * math.sin(t * 0.55)) - Vector3.new(0, 4, 0)
			sweep = sweep:Lerp(winAt + outward * 1.5 - Vector3.new(0, 1.2, 0), zu * zu * (3 - 2 * zu))
			local from = hp0:Lerp(hp1, math.clamp(t / N.hit, 0, 1)) + side * 3 - Vector3.new(0, 3, 0)
			beam.CFrame = CFrame.lookAt(from, sweep)
		else
			sl.Enabled = false
		end
		-- the moon, held each frame up to the squad (27 Nov test: the school's own zone look lands a beat after the film
		-- starts and took the moon back, the feed read black); the haze thinner still while the feed runs
		local mw = r.moonWas
		if mw and t < N.squad[1] then
			local amb, outd, ex = Color3.fromRGB(118, 130, 160), Color3.fromRGB(138, 156, 196), mw.exp + 0.95
			if Lighting.Ambient ~= amb then Lighting.Ambient = amb end
			if Lighting.OutdoorAmbient ~= outd then Lighting.OutdoorAmbient = outd end
			if Lighting.ExposureCompensation ~= ex then Lighting.ExposureCompensation = ex end
			local atm = Lighting:FindFirstChildOfClass("Atmosphere")
			local dn = if mw.dens then mw.dens * (if feedOn then 0.3 else 0.55) else nil
			if atm and dn and atm.Density ~= dn then atm.Density = dn end
		end
		-- the zombie: out of the dark to the boards, the slam, a step back
		if zroot then
			local zstart = N.zoom[1] - 0.4
			local u = math.clamp((t - zstart) / (HIT - 0.05 - zstart), 0, 1)
			local p = zFrom:Lerp(zTo, 1 - (1 - u) ^ 1.6)
			if t >= HIT and t < HIT + 0.12 then p = zTo - outward * 0.7
			elseif t >= HIT + 0.12 then p = zTo + outward * math.clamp((t - HIT - 0.12) * 1.2, 0, 0.9) end
			zroot.CFrame = CFrame.lookAt(p + Vector3.new(0, 3, 0), p + Vector3.new(0, 3, 0) - outward)
		end
		if not hit and t >= HIT then
			hit = true
			if r.cine then r.cine.kick(1.6) end
			sfx("zm_board", winAt, 1.0)
			task.delay(0.05, function() sfx("zm_planks", winAt, 0.8) end)
		end
		-- the static, then black: the signal's gone
		local inStatic = t >= N.static[1] and t < N.school[1]
		o.static.Visible = inStatic
		if inStatic then
			if not staticOn then
				staticOn = true
				if sting then TweenService:Create(sting, TweenInfo.new(0.15), { Volume = 0 }):Play() end
				if wash then fade(wash, 0, 0.2) end
				if cc.Parent then cc:Destroy() end
				sfx("zm_static", nil, 0.9)
			end
			local snowing = t < N.static[2]
			for _, f in o.snow do
				f.Visible = snowing
				if snowing then
					local g = rng:NextNumber(0.25, 1)
					f.BackgroundColor3 = Color3.new(g, g, g)
					f.Position = UDim2.fromOffset(rng:NextInteger(0, math.max(1, vs.X)), rng:NextInteger(0, math.max(1, vs.Y)))
				end
			end
			for _, f in o.tears do
				f.Visible = snowing
				f.Position = UDim2.fromScale(0, rng:NextNumber())
			end
		end
		-- the school: our own lens, the bars, the wind; then the squad, the bars lift, your view
		if not schoolOn and t >= N.school[1] then
			schoolOn = true
			Cine.bars(true, 0.01)
			moon(r, 1, true, 0.01)
			wind = bed("zm_wind")
			if wind then table.insert(r.beds, wind); fade(wind, 1, 0.5) end
		end
		r.showMe = t >= N.squad[1] and t < N.squad[2] - 0.1 -- (not into the hand-back: the lens goes into your own head)
		if t >= N.squad[1] and r.moonHigh ~= false then r.moonHigh = false; moon(r, 1, false, 0.25) end
		if not lifted and t >= N.squad[2] - 0.4 then lifted = true; Cine.bars(false, 0.6); if wind then fade(wind, 0, 0.8) end end
		if t >= len then finish(true) end
	end)
end
local function skip()
	if film and film.kind == "intro" then finish(true)
	elseif film and film.kind == "outro" and film.onSkip and film.aboard then film.onSkip() end -- (straight to the card)
end
Keys.began(function(io: any, _gp: boolean)
	if not film then return end
	local k = io.KeyCode
	if k == Enum.KeyCode.Space or k == Enum.KeyCode.Return or k == Enum.KeyCode.ButtonA then skip() end
end)
skipB.Activated:Connect(skip)

-- the crew member at the helicopter's door (the server's plain R15 in a flight suit): a built helmet with a dark visor,
-- anchored at the root, the reach (mocap) played on his own Animator
local function crewOf(r: any): (Model?, BasePart?, AnimationTrack?)
	local src = ReplicatedStorage:FindFirstChild("JankfireZmCine")
	local ct = src and src:FindFirstChild("Crew")
	if not ct or not ct:IsA("Model") then return nil, nil, nil end
	local m = ct:Clone()
	pcall(function() m:ScaleTo(0.85) end) -- (the cabin is 4.7 studs inside: a standing grown-up stoops a little)
	for _, d in m:GetDescendants() do if d:IsA("BasePart") then d.CanCollide = false; d.CanQuery = false; d.CanTouch = false end end
	local root = m:FindFirstChild("HumanoidRootPart") :: BasePart?
	if root then root.Anchored = true end
	local head = m:FindFirstChild("Head") :: BasePart?
	if head then
		local hs = head.Size
		local helm = Instance.new("Part") -- (27 Nov test: a SpecialMesh sphere didn't show; a Ball does)
		helm.Name = "Helmet"; helm.Color = Color3.fromRGB(64, 70, 58); helm.Material = Enum.Material.SmoothPlastic
		helm.Shape = Enum.PartType.Ball
		local hd = math.max(hs.X, hs.Y, hs.Z) * 1.22
		helm.Size = Vector3.new(hd, hd, hd); helm.CanCollide = false; helm.CanQuery = false; helm.Massless = true
		-- (Welds at set offsets from the head: 27 Nov test, the WeldConstraints left the helmet off his head in a game
		-- and the visor under his eyes, though they sat right in Edit)
		local c0 = CFrame.new(0, hs.Y * 0.22, hs.Z * 0.05)
		helm.CFrame = head.CFrame * c0
		local w = Instance.new("Weld"); w.Part0 = head; w.Part1 = helm; w.C0 = c0; w.Parent = helm
		helm.Parent = m
		local visor = Instance.new("Part")
		visor.Name = "Visor"; visor.Color = Color3.fromRGB(16, 20, 26); visor.Material = Enum.Material.Glass; visor.Transparency = 0.15
		visor.Size = Vector3.new(hs.X * 1.02, hs.Y * 0.36, 0.12); visor.CanCollide = false; visor.CanQuery = false; visor.Massless = true
		local v0 = CFrame.new(0, hs.Y * 0.12, -hs.Z * 0.62)
		visor.CFrame = head.CFrame * v0
		local w2 = Instance.new("Weld"); w2.Part0 = head; w2.Part1 = visor; w2.C0 = v0; w2.Parent = visor
		visor.Parent = m
	end
	-- (in the world before the clip loads: an Animator outside the game can't load one; 27 Nov test, his arms stayed down)
	m.Parent = workspace
	table.insert(r.trash, m)
	local track: AnimationTrack? = nil
	local hum = m:FindFirstChildOfClass("Humanoid")
	if hum then
		local an = hum:FindFirstChildOfClass("Animator") or Instance.new("Animator", hum)
		local anim = Instance.new("Animation"); anim.AnimationId = XC.reach
		local ok, tr = pcall(function() return (an :: Animator):LoadAnimation(anim) end)
		if ok and tr then tr.Looped = false; tr.Priority = Enum.AnimationPriority.Action; track = tr end
	end
	return m, root, track
end
-- hold a one-shot clip on its last frame
local function holdEnd(tr: AnimationTrack?)
	if tr and tr.IsPlaying and tr.Length > 0 and tr.TimePosition >= tr.Length - 0.04 and tr.Speed ~= 0 then tr:AdjustSpeed(0) end
end

-- ------------------------------------------------------------------ the extraction out
-- (27 Nov, the owner: "she sort of just teleports into the helicopter! How about it's first person, helicopter door
-- opens and there's a guy, he reaches out his hand, you take a step forward then shot its an away shot of the
-- helicopter flying off then boom displays your round"). For whoever got out: first person at the door, a settle; the
-- door slides back (ZombieExtract slides it, ZM.X.film.door); the crew member reaches out (mocap); your own hand comes
-- up from the bottom of the frame (the same mocap, your body hidden but that arm); a step forward with a small bob; a
-- hard cut on the hands meeting to the long lens as it lifts and flies off; then the stats card (ZombieExtract).
-- Space skips to the card. Anyone left behind gets the away shot only
local function outro(a: Model)
	local z = XC.zones[a.Name]
	local t0, lift = a:GetAttribute("XT0"), a:GetAttribute("XLift")
	if not z or type(t0) ~= "number" or type(lift) ~= "number" then return end
	local start = lift - XC.board
	if srv() > start + XC.outro - 0.5 then return end
	if film then finish(false) end
	local pad = ZM.padOf(a:GetPivot(), z)
	local liftT = lift - t0
	local F = XC.film
	local function heliCF(): CFrame
		return ZM.heliAt(pad, z, srv() - t0, liftT) or CFrame.lookAt(pad.Position + Vector3.new(0, 0.6, 0), pad.Position + Vector3.new(0, 0.6, 0) + pad.LookVector)
	end
	local function heliPos(): Vector3 return heliCF().Position + Vector3.new(0, 5, 0) end
	local function P(x: number, y: number, zz: number): Vector3 return pad:PointToWorldSpace(Vector3.new(x, y, zz)) end
	-- were you out? (the server's own test: standing in the zone when it ended)
	local ch = me.Character
	local hrp = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	local aboard = hrp ~= nil and (Vector3.new(hrp.Position.X - pad.Position.X, 0, hrp.Position.Z - pad.Position.Z)).Magnitude <= z.r + 2
	-- where the door is on the flying model (ZmKit's DoorAt; the first heli has none: its open side)
	local kit = ReplicatedStorage:FindFirstChild("JankfireZmKit")
	local want = me:GetAttribute("ZmHeli")
	local hm = kit and kit:FindFirstChild(if type(want) == "string" then want else (XC.heli or "Heli"))
	local doorAt = (hm and hm:GetAttribute("DoorAt")) :: any
	if typeof(doorAt) ~= "Vector3" then doorAt = Vector3.new(-4.6, 6.0, 1.0) end
	local side = if (doorAt :: Vector3).X >= 0 then 1 else -1 -- (which side the door is on: out of it is that way)
	local r: any = { guis = {}, vm = {}, trash = {}, beds = {}, showMe = false, kind = "outro", aboard = aboard }
	film = r
	me:SetAttribute("ZmFilm", true)
	local key = keyLight(r, 40, 1.4)
	moon(r, 0.8)
	local function clk(): number return srv() - start end
	local function doorW(): Vector3 return heliCF():PointToWorldSpace(doorAt) end
	-- the first-person camera: outside the door, eye level, facing in; a settle, then still, then the step with a bob
	local function eye(t: number): CFrame
		local hc = heliCF()
		local d = doorW()
		local out = hc.RightVector * side
		local back = if t < 0.6 then 7.6 - 1.0 * (1 - (1 - t / 0.6) ^ 2) else 6.6
		local bob = 0
		if t >= F.step[1] then
			local u = math.clamp((t - F.step[1]) / (F.step[2] - F.step[1]), 0, 1)
			back = 6.6 - 1.7 * (u * u * (3 - 2 * u))
			bob = -0.14 * math.sin(u * math.pi)
		end
		local at = d + out * back + Vector3.new(0, 0.25 + bob, 0)
		local look = d - out * 1.4 + Vector3.new(0, 0.35, 0)
		return CFrame.lookAt(at, look)
	end
	local shots
	if aboard then
		shots = {
			{ name = "door", t0 = 0, t1 = F.cut, shake = function(u: number) return if u < 0.16 then 0.35 else 0.18 end,
				cam = function(u: number): CFrame return eye(u * F.cut) end, fov = 62 },
			{ name = "away", t0 = F.cut, t1 = XC.outro, shake = 0.1,
				cam = function(u: number): CFrame return CFrame.lookAt(P(2, 16 + 2 * u, 38), heliPos()) end, fov = 32 },
		}
	else
		shots = {
			{ name = "away", t0 = 0, t1 = XC.outro, shake = 0.1,
				cam = function(u: number): CFrame return CFrame.lookAt(P(2, 16 + 2 * u, 38), heliPos()) end, fov = 32 },
		}
	end
	Cine.bars(true, 0.3)
	r.cine = Cine.play(shots, { clock = clk })
	local wind = bed("zm_wind")
	if wind then table.insert(r.beds, wind); fade(wind, 0.7, 0.8) end
	-- the crew member, and your own hand
	local crew, croot, ctr = nil, nil, nil
	local mytr: AnimationTrack? = nil
	local headDy = 1.5
	if aboard then
		crew, croot, ctr = crewOf(r)
		if hrp and hum then
			hrp.Anchored = true
			local head = ch and ch:FindFirstChild("Head") :: BasePart?
			if head then headDy = head.Position.Y - hrp.Position.Y end
			local an = hum:FindFirstChildOfClass("Animator")
			if an then
				local anim = Instance.new("Animation"); anim.AnimationId = XC.reach
				local ok, tr = pcall(function() return (an :: Animator):LoadAnimation(anim) end)
				if ok and tr then tr.Looped = false; tr.Priority = Enum.AnimationPriority.Action4; mytr = tr end
			end
		end
		r.showOnly = { LeftUpperArm = true, LeftLowerArm = true, LeftHand = true }
	end
	local crewOn, handOn, doorSaid, clasped, cut, faded = false, false, false, false, false, false
	r.conn = RunService.RenderStepped:Connect(function()
		local t = clk()
		hold(r)
		local cam = workspace.CurrentCamera
		key.CFrame = cam.CFrame * CFrame.new(1.5, 1.4, 1.5)
		if aboard and not cut then
			local hc = heliCF()
			-- the crew member stands in the doorway, a step in, facing out
			if crew and croot then
				local d = hc:PointToObjectSpace(doorW())
				local h = crew:FindFirstChildOfClass("Humanoid")
				local up = (if h then h.HipHeight else 1.7) + croot.Size.Y / 2
				local pos = hc:PointToWorldSpace(Vector3.new(d.X - side * 1.5, d.Y - 2.35 + up, d.Z))
				croot.CFrame = CFrame.lookAt(pos, pos + hc.RightVector * side)
			end
			-- your body under the lens, only the reaching arm to be seen
			if hrp then
				local e = eye(t)
				local f = Vector3.new(e.LookVector.X, 0, e.LookVector.Z).Unit
				-- (27 Nov tests: at the head the reaching hand stayed out of frame; a step ahead its arm came up at the frame's
				-- bottom left corner; a little right and up, it comes up to the middle to meet his)
				local rt = Vector3.new(e.RightVector.X, 0, e.RightVector.Z).Unit
				local p = e.Position - Vector3.new(0, headDy + 0.1, 0) + f * 1.7 + rt * 0.45
				hrp.CFrame = CFrame.lookAt(p, p + f)
			end
			if not doorSaid and t >= F.door[1] then
				doorSaid = true
				local lib = ReplicatedStorage:FindFirstChild("JankfireSounds")
				sfx(if lib and lib:FindFirstChild("zm_doorslide") then "zm_doorslide" else "hunt_door_open", doorW(), 0.9)
			end
			if not crewOn and t >= F.crew and ctr then crewOn = true; ctr:Play(0.2) end
			if not handOn and t >= F.hand and mytr then handOn = true; mytr:Play(0.15) end
			holdEnd(ctr); holdEnd(mytr)
			if not clasped and t >= F.step[2] then
				clasped = true
				if r.cine then r.cine.kick(0.6) end
				sfx(if (ReplicatedStorage:FindFirstChild("JankfireSounds") and ReplicatedStorage.JankfireSounds:FindFirstChild("zm_clasp")) then "zm_clasp" else "hunt_punch_hit", nil, 0.5)
			end
			-- (Studio: what the film did, for a test to read back)
			if game:GetService("RunService"):IsStudio() and math.floor(t * 4) ~= r.dbgT then
				r.dbgT = math.floor(t * 4)
				local lh = ch and ch:FindFirstChild("LeftHand") :: BasePart?
				me:SetAttribute("ZmFilmDbg", string.format("t %.2f crew %s hand %s ltm %s cam %s", t,
					if croot then tostring(hc:PointToObjectSpace(croot.Position)) else "-",
					if lh then tostring(cam.CFrame:PointToObjectSpace(lh.Position)) else "-",
					if lh then tostring(lh.LocalTransparencyModifier) else "-", tostring(hc:PointToObjectSpace(cam.CFrame.Position))))
			end
			if t >= F.cut then
				cut = true
				r.showOnly = {} -- (your body: gone in with him; the server hides it too)
				if crew then crew.Parent = nil end
			end
		end
		if not faded and t >= XC.outro - 0.6 then
			faded = true
			TweenService:Create(black, TweenInfo.new(0.6), { BackgroundTransparency = 0 }):Play()
		end
		if t >= XC.outro then
			finish(true)
			TweenService:Create(black, TweenInfo.new(0.8), { BackgroundTransparency = 1 }):Play()
		end
	end)
	-- Space: straight to the card
	skipL.Text = if Keys.isTouch() or not aboard then "" else "SPACE  SKIP"
	skipB.Visible = aboard and Keys.isTouch()
	r.onSkip = function()
		finish(true)
		black.BackgroundTransparency = 1
		me:SetAttribute("ZmCardNow", true)
	end
end

-- ------------------------------------------------------------------ watching the arena
local watched: Model? = nil
local conns: { RBXScriptConnection } = {}
local function watch()
	for _, c in conns do c:Disconnect() end
	table.clear(conns)
	if film then finish(true) end
	black.BackgroundTransparency = 1
	local a = nil
	for _ = 1, 40 do a = arena(); if a or not me:GetAttribute("ZmArena") then break end; task.wait(0.1) end
	watched = a
	if not a then return end
	local m = a :: Model
	local function check()
		if watched ~= m then return end
		if m:GetAttribute("XSt") == "out" then outro(m)
		elseif m:GetAttribute("IntroT0") and not film then intro(m) end
	end
	table.insert(conns, m:GetAttributeChangedSignal("IntroT0"):Connect(check))
	table.insert(conns, m:GetAttributeChangedSignal("XSt"):Connect(check))
	table.insert(conns, m:GetAttributeChangedSignal("XLift"):Connect(check))
	check()
end
me:GetAttributeChangedSignal("ZmArena"):Connect(function() task.spawn(watch) end)
task.spawn(watch)
