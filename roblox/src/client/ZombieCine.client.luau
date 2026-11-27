--!strict
-- ZOMBIES' films (27 Nov 2026; roblox/docs/ZOMBIES.md 4.3; the owner: "cinematic for zombies mode please!!"). Both on
-- this client, timed by the server's clock from attributes on the arena model (server/ZombieExtract.luau), the camera,
-- bars, shake and kicks from CineKit.
--   the intro (IntroT0, IntroLen 9.9 s, skippable: Space, Enter, A, or SKIP on a phone): a BREAKING NEWS broadcast, the
--     news helicopter's feed onto the school's front gate as a crowd of zombies piles up against it, static, our own
--     shot of the school, the squad; the camera lands on your own view. Round 1 waits for it (the server). Below.
--   the extraction out (XSt "out", XLift): first person at the helicopter's door, the crew member reaching out, your
--     hand, the step; a hard cut to the long lens as it lifts and flies off; then the stats card (ZombieExtract.client).
-- Both are prewarmed (CineKit.prewarm; roblox/docs/PERFORMANCE.md): nothing pops in.
-- Rules (main, 27 Nov): animation cycles and mocap only, recordings only (licensed library sounds), no voices or crowd
-- sounds, the school's own night look with a moon fill, words only where asked (the broadcast's three).
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
-- (the rest of Roblox's own Zombie animation package, cycles all: its two idles, arms out, for the crowd pressing on
-- the gate, and its climb for the ones going up on the others' backs)
local ZOMBIE_IDLE = { "rbxassetid://616158929", "rbxassetid://616160636" }
local ZOMBIE_CLIMB = "rbxassetid://616156119"
local GATE_SOUNDS = { "zm_gaterattle", "zm_gateshake", "zm_gatebang", "zm_gateslam" }
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
-- far off: the recording's highs (and mids) cut, and a long reverb if wet is given (dB): a siren over the town at night
local function farOff(s: Sound, hi: number, mid: number, wet: number?)
	local eq = Instance.new("EqualizerSoundEffect"); eq.LowGain = 0; eq.MidGain = mid; eq.HighGain = hi; eq.Parent = s
	if wet then
		local rv = Instance.new("ReverbSoundEffect"); rv.DecayTime = 3.4; rv.Density = 1; rv.Diffusion = 1; rv.DryLevel = -3; rv.WetLevel = wet
		rv.Parent = s
	end
end
local function fade(s: Sound?, k: number, dur: number)
	if not s then return end
	local full = tonumber(s:GetAttribute("Full")) or 0.5
	TweenService:Create(s, TweenInfo.new(dur, Enum.EasingStyle.Sine), { Volume = full * k }):Play()
end
local okLook, HubLook = pcall(require, Shared:WaitForChild("HubLook"))
-- HOUSE HUNT's approved static (its old TV's noise: HuntConfig.INTRO.static), reused for the news feed's cut
local okHC, HuntConfig = pcall(require, Shared:WaitForChild("HuntConfig"))
local STATIC: { number } = if okHC and HuntConfig and HuntConfig.INTRO and HuntConfig.INTRO.static then HuntConfig.INTRO.static else {}
local function staticImages(): { Instance }
	local list = {}
	for _, id in STATIC do local l = Instance.new("ImageLabel"); l.Image = "rbxassetid://" .. tostring(id); table.insert(list, l) end
	return list
end
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
local xWarm: any = nil -- (the extraction film's prewarm: xwarm, below)
-- who got out with the helicopter (the server's xout, by name): the extraction film seats the others in the cabin
local lastOut: any = nil
zr.OnClientEvent:Connect(function(x: any)
	if type(x) == "table" and x.k == "xout" and type(x.who) == "table" then lastOut = { who = x.who, t = srv() } end
end)
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
	skipL.Text = ""; skipL.Visible = true; skipB.Visible = false
	if r.cine then r.cine.stop(handBack) end
	moonBack(r)
	-- (the bodies the extraction film hid on this screen: drawn again)
	for _, real in (r.hideReal or {}) :: any do
		if real.Parent then
			for _, x in real:GetDescendants() do if x:IsA("BasePart") or x:IsA("Decal") then (x :: any).LocalTransparencyModifier = 0 end end
		end
	end
	if r.warm then pcall(r.warm.release) end
	if r.leadBlack then r.leadBlack = false; black.BackgroundTransparency = 1 end
	me:SetAttribute("ZmFilm", nil) -- (the zombies HUD back: ZombiesClient)
	me:SetAttribute("ZmBriefUp", nil)
	if r.onEnd then pcall(r.onEnd) end
end

-- ------------------------------------------------------------------ the intro: a news broadcast
-- (27 Nov, the owner: "have a news broadcast actually for the intro a zombies, it'll be like breaking news" and "Then it
-- cuts to shot of the school"). All its words are live UI here, never in a picture: BREAKING NEWS, LIVE and the one
-- headline, nothing else (no ticker, no flavour lines, zombie words only). No voices. The times: ZM.X.news.
--   the feed: a news helicopter's camera over the school's grounds at night (grain, scan lines, zoom brackets, focus
--     breathing, its searchlight sweeping, the moon so it reads), the news sting and the rotor wash; it zooms onto the
--     front gate (ZmFrontGate, studio-tools/ZmGate.luau) where a crowd of zombies piles up against it: pressing, the
--     ones behind pushing, two going up on the others' backs, arms through the bars; the gate rattles, heaves and
--     buckles (27 Nov, the owner: "can you do a shot of the school gate and multiple zombies piling up?")
--   the hit: the feed breaks into full-screen static (HOUSE HUNT's noise frames, a new one every frame, a roll, tears,
--     a brightness flutter; 27 Nov, the owner: "proper static"), then a hard cut to the school
--   the school: our own lens, outside at night in the fog, a slow push, the wind
--   the squad in the lobby, the bars lift, your own view
local NEWS_INK, NEWS_BONE = Color3.fromRGB(29, 31, 35), Color3.fromRGB(229, 226, 219) -- (A PLATE's ink and bone)
local NEWS_WARN = Color3.fromRGB(166, 32, 28) -- (the BREAKING NEWS box: a warning red, with the sirens; 27 Nov)
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
	-- (a fifth bigger than the first cut: main, 27 Nov, for phones)
	o.third = T.new("Frame", { Name = "Third", BackgroundTransparency = 1, Position = UDim2.new(0, -820, 1, -222), Size = UDim2.fromOffset(770, 124) }, root)
	local bn = T.new("Frame", { BackgroundColor3 = NEWS_WARN, BorderSizePixel = 0, Size = UDim2.fromOffset(505, 67) }, o.third)
	T.new("UICorner", { CornerRadius = UDim.new(0, 3) }, bn)
	local bt = T.text(bn, "B", "BREAKING NEWS", 41, NEWS_BONE, T.FONT_HEAVY); bt.Position = UDim2.fromOffset(22, 0); bt.Size = UDim2.new(1, -28, 1, 0)
	o.line = T.new("Frame", { BackgroundColor3 = NEWS_BONE, BorderSizePixel = 0, Position = UDim2.fromOffset(0, 72), Size = UDim2.fromOffset(0, 48), ClipsDescendants = true }, o.third)
	T.new("UICorner", { CornerRadius = UDim.new(0, 3) }, o.line)
	local ht = T.text(o.line, "H", "OUTBREAK  ·  JANKFIELD HIGH", 26, NEWS_INK, T.FONT_HEAVY); ht.Position = UDim2.fromOffset(19, 0); ht.Size = UDim2.fromOffset(720, 48)
	-- the static: full screen, HOUSE HUNT's noise frames (two stacked for the roll), a white flutter, a dark dropout,
	-- tear bands; all of it new every rendered frame while it runs
	o.static = T.new("Frame", { Name = "Static", BackgroundColor3 = Color3.new(0, 0, 0), BorderSizePixel = 0, Size = UDim2.fromScale(1, 1),
		Visible = false, ClipsDescendants = true }, gui)
	table.insert(r.trash, o.static)
	o.stIm = {}
	for k = 1, 2 do
		local im = T.new("ImageLabel", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Size = UDim2.fromScale(1.08, 1.02),
			Position = UDim2.fromScale(0.5, if k == 1 then 0.5 else -0.5), ScaleType = Enum.ScaleType.Crop,
			Image = if #STATIC > 0 then "rbxassetid://" .. tostring(STATIC[1]) else "" }, o.static)
		table.insert(o.stIm, im)
	end
	o.stFlash = T.new("Frame", { BackgroundColor3 = Color3.new(1, 1, 1), BackgroundTransparency = 1, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1) }, o.static)
	o.stDark = T.new("Frame", { BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 1, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1) }, o.static)
	o.tears = {}
	for k = 1, 4 do
		local f = T.new("Frame", { BackgroundColor3 = Color3.new(1, 1, 1), BackgroundTransparency = 0.6, BorderSizePixel = 0, Size = UDim2.new(1, 0, 0, 6) }, o.static)
		table.insert(o.tears, f)
	end
	return o
end

local function intro(a: Model)
	local t0 = a:GetAttribute("IntroT0")
	local len = tonumber(a:GetAttribute("IntroLen")) or XC.intro
	if type(t0) ~= "number" or film then return end
	do -- (too late to start? with the briefing up the film waits in it; once it closed the film ends its tail after)
		local b0, b1 = a:GetAttribute("BriefT0"), a:GetAttribute("BriefT1")
		local endT = if type(b1) == "number" then b1 + len - XC.news.push[2] elseif type(b0) == "number" then math.huge else t0 + len
		if srv() > endT - 1.2 then return end
	end
	local okM, map = pcall(ZM.read, a)
	if not okM or not map then return end
	local site = a:GetPivot()
	local function L(x: number, y: number, z: number): Vector3 return site:PointToWorldSpace(Vector3.new(x, y, z)) end
	local N = XC.news
	-- (keep: the briefing's screen (ZombieBrief.client) stays on while the film hides the rest)
	local r: any = { guis = {}, vm = {}, trash = {}, beds = {}, showMe = false, kind = "intro", keep = { JankZmBrief = true } }
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
	local winAt = if w then w.at.Position else L(0, 6, 96)
	-- the front gate: its frame (out = to the road), its two leaves (each part's place from its hinge)
	local gm = a:FindFirstChild("ZmFrontGate")
	local gbase = gm and gm:FindFirstChild("GateBase") :: BasePart?
	local GF = if gbase then gbase.CFrame else CFrame.lookAt(L(28, 0, 171), L(28, 0, 181))
	local G, GO, GR = GF.Position, GF.LookVector, GF.RightVector
	local UP = Vector3.new(0, 1, 0)
	local leaves = {}
	for _, nm in { "LeafL", "LeafR" } do
		local lf = gm and gm:FindFirstChild(nm)
		local hinge = lf and lf:GetAttribute("Hinge")
		if lf and typeof(hinge) == "Vector3" then
			local hcf = GF * CFrame.new(hinge)
			local parts, c, n = {}, Vector3.zero, 0
			for _, d in lf:GetDescendants() do
				if d:IsA("BasePart") then table.insert(parts, { p = d, rel = hcf:ToObjectSpace(d.CFrame), was = d.CFrame }); c += d.Position; n += 1 end
			end
			-- which way of turning about the hinge swings the leaf in (toward the school)
			local mid = (if n > 0 then c / n else hcf.Position) - hcf.Position
			local sgn = if (CFrame.Angles(0, 0.1, 0):VectorToWorldSpace(hcf:VectorToObjectSpace(mid)) - hcf:VectorToObjectSpace(mid)):Dot(hcf:VectorToObjectSpace(-GO)) > 0 then 1 else -1
			table.insert(leaves, { hcf = hcf, parts = parts, sgn = sgn, seed = #leaves * 7.3 + 1.1 })
		end
	end
	-- the crowd: the mode's own shambler, many times; each with its own clip (a cycle), speed, phase and sway
	-- (x across the gate, z out from it, y up; the front row's arms go through the bars)
	local CROWD = {
		{ -5.2, 1.25, 0, "idle" }, { -2.6, 1.3, 0, "idle" }, { 0.1, 1.2, 0, "idle" }, { 2.7, 1.3, 0, "idle" }, { 5.3, 1.25, 0, "idle" },
		{ -3.9, 2.7, 0, "walk" }, { -1.3, 2.75, 0, "walk" }, { 1.4, 2.7, 0, "walk" }, { 3.9, 2.8, 0, "walk" },
		{ -2.4, 4.1, 0, "walk" }, { 2.2, 4.2, 0, "walk" },
		{ -3.1, 2.0, 2.9, "climb" }, { 1.2, 2.0, 3.1, "climb" },
		{ 0.6, 15.0, 0, "arrive" },
		-- (spilling along the fence either side of the gate: the owner's "Finish the fence", 27 Nov)
		{ -12.6, 1.2, 0, "idle" }, { -15.8, 1.45, 0, "walk" }, { 12.9, 1.2, 0, "idle" }, { 16.1, 1.5, 0, "walk" },
	}
	-- (27 Nov, main: they read as one bright flat green mass. Each one dressed now: muted skins, worn shirts in dull
	-- colours, dark trousers, now and then a torn sleeve; a cool rim light from the street behind them, below)
	local SKIN = { Color3.fromRGB(104, 116, 92), Color3.fromRGB(122, 120, 102), Color3.fromRGB(92, 102, 96), Color3.fromRGB(116, 108, 92),
		Color3.fromRGB(98, 110, 104), Color3.fromRGB(112, 122, 104) }
	local SHIRT = { Color3.fromRGB(86, 80, 72), Color3.fromRGB(70, 78, 88), Color3.fromRGB(96, 70, 64), Color3.fromRGB(78, 84, 66),
		Color3.fromRGB(110, 104, 92), Color3.fromRGB(60, 66, 74), Color3.fromRGB(92, 88, 104) }
	local PANTS = { Color3.fromRGB(44, 46, 52), Color3.fromRGB(52, 48, 44), Color3.fromRGB(38, 42, 40), Color3.fromRGB(58, 56, 60) }
	local SKINPART = { Head = true, LeftHand = true, RightHand = true, LeftLowerArm = true, RightLowerArm = true }
	local SHIRTPART = { UpperTorso = true, LeftUpperArm = true, RightUpperArm = true }
	local PANTSPART = { LowerTorso = true, LeftUpperLeg = true, RightUpperLeg = true, LeftLowerLeg = true, RightLowerLeg = true }
	local FEET = { LeftFoot = true, RightFoot = true }
	local function dress(m: Model, rng2: Random)
		for _, d in m:GetDescendants() do
			if d:IsA("BodyColors") or d:IsA("Shirt") or d:IsA("Pants") or d:IsA("ShirtGraphic") then d:Destroy() end
		end
		-- (27 Nov, the owner: "zombies having glowing eyes": no face (it's the head's own picture), and glowing eyes of
		-- their own, made here (the server's, ZombieLight, can land a step after the film copies the body), half as big
		-- again as the game's: from the news lens, under the searchlight, that size didn't read)
		local hd = m:FindFirstChild("Head")
		if hd and hd:IsA("BasePart") then
			if hd:IsA("MeshPart") then hd.TextureID = "" end
			for _, d in hd:GetChildren() do
				if d:IsA("Decal") or (d:IsA("BasePart") and (d.Name == "ZmEyeL" or d.Name == "ZmEyeR")) then d:Destroy() end
			end
			local hs = hd.Size
			for _, side in { -1, 1 } do
				local e = Instance.new("Part")
				e.Name = if side < 0 then "ZmEyeL" else "ZmEyeR"
				e.Material = Enum.Material.Neon
				e.Color = ZM.EYE
				e.Size = Vector3.new(hs.X * 0.33, hs.Y * 0.16, 0.06)
				e.CanCollide, e.CanQuery, e.CanTouch, e.Massless, e.CastShadow = false, false, false, true, false
				e.CFrame = hd.CFrame * CFrame.new(side * hs.X * 0.2, hs.Y * 0.08, -hs.Z * 0.47)
				local w = Instance.new("WeldConstraint")
				w.Part0, w.Part1 = hd, e
				w.Parent = e
				e.Parent = hd
			end
		end
		local skin, shirt, pants = SKIN[rng2:NextInteger(1, #SKIN)], SHIRT[rng2:NextInteger(1, #SHIRT)], PANTS[rng2:NextInteger(1, #PANTS)]
		local torn = if rng2:NextNumber() < 0.45 then (if rng2:NextNumber() < 0.5 then "LeftUpperArm" else "RightUpperArm") else ""
		for _, p in m:GetChildren() do
			if p:IsA("BasePart") then
				if SKINPART[p.Name] or p.Name == torn then p.Color = skin
				elseif SHIRTPART[p.Name] then p.Color = shirt
				elseif PANTSPART[p.Name] then p.Color = pants
				elseif FEET[p.Name] then p.Color = Color3.fromRGB(34, 32, 30) end
				if p.Name ~= "HumanoidRootPart" then p.Material = Enum.Material.SmoothPlastic end
			end
		end
	end
	local crowd = {}
	local src = ReplicatedStorage:FindFirstChild("JankfireZmCine")
	local zt = src and src:FindFirstChild("Zombie")
	local crng = Random.new(20261127)
	if gbase and zt and zt:IsA("Model") then
		for i, c in CROWD do
			local m = zt:Clone()
			m.Name = "ZmGateCrowd"
			dress(m, crng)
			for _, d in m:GetDescendants() do if d:IsA("BasePart") then d.CanCollide = false; d.CanQuery = false; d.CanTouch = false end end
			local root = m:FindFirstChild("HumanoidRootPart") :: BasePart?
			if not root then m:Destroy(); continue end
			root.Anchored = true
			local hum = m:FindFirstChildOfClass("Humanoid")
			if hum then hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None end
			m.Parent = workspace -- (in the world before its clip loads)
			table.insert(r.trash, m)
			local tr: AnimationTrack? = nil
			if hum then
				local an = hum:FindFirstChildOfClass("Animator") or Instance.new("Animator", hum)
				local id = if c[4] == "idle" then ZOMBIE_IDLE[(i % 2) + 1] elseif c[4] == "climb" then ZOMBIE_CLIMB else ZOMBIE_WALK
				local anim = Instance.new("Animation"); anim.AnimationId = id
				local ok, t2 = pcall(function() return (an :: Animator):LoadAnimation(anim) end)
				if ok and t2 then
					t2.Looped = true; t2.Priority = Enum.AnimationPriority.Action
					local sp = if c[4] == "walk" then crng:NextNumber(0.5, 0.8) elseif c[4] == "climb" then crng:NextNumber(0.8, 1.1) else crng:NextNumber(0.8, 1.25)
					t2:Play(0, 1, sp)
					tr = t2
				end
			end
			table.insert(crowd, { m = m, root = root, tr = tr, x = c[1] + crng:NextNumber(-0.25, 0.25), z = c[2] + crng:NextNumber(-0.15, 0.15),
				y = c[3], kind = c[4], ph = crng:NextNumber(0, 6.28), w = crng:NextNumber(4.5, 7.5), yaw = crng:NextNumber(-10, 10), phased = false })
		end
	end
	-- the lobby terminal (studio-tools/ZmGate terminal): its screen, which way it faces, and how close fills the view.
	-- its picture is this client's (a SurfaceGui): the terminal's green while the film is in it, the power-down after
	local term = a:FindFirstChild("ZmTerminal")
	local screen = term and term:FindFirstChild("Screen") :: BasePart?
	local scr = if screen then screen.Position else L(0, 3.83, 55.8)
	local sf = if screen then screen.CFrame.ZVector else (site.ZVector)
	local sx = sf:Cross(Vector3.new(0, 1, 0)).Unit
	-- (studs out from the glass where its width fills the view at 32 degrees: from this screen's own shape, a wide window
	-- comes in closer. 27 Nov test: a fixed 16:9 distance left the bezel and the room in a 2.4:1 Studio view)
	local vs = workspace.CurrentCamera and workspace.CurrentCamera.ViewportSize or Vector2.new(16, 9)
	local aspect = math.max(1.2, vs.X / math.max(1, vs.Y))
	local FILL = math.min(1.85, 0.94 / (math.tan(math.rad(16)) * aspect))
	local pic = nil :: any
	if screen then
		local sg = Instance.new("SurfaceGui")
		sg.Name = "ZmTermPic"
		sg.Face = Enum.NormalId.Back -- (+z: toward the squad)
		sg.LightInfluence = 0
		sg.Brightness = 1.6
		sg.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		sg.PixelsPerStud = 120
		sg.Adornee = screen
		local bg = Instance.new("Frame")
		bg.BorderSizePixel = 0; bg.BackgroundColor3 = Color3.fromRGB(3, 6, 4); bg.Size = UDim2.fromScale(1, 1); bg.Parent = sg
		local lit = Instance.new("Frame") -- (the picture: it collapses to a line, a dot, then nothing)
		lit.Name = "Lit"; lit.BorderSizePixel = 0; lit.BackgroundColor3 = Color3.fromRGB(8, 30, 15) -- (the briefing's veil: ZombieBrief)
		lit.AnchorPoint = Vector2.new(0.5, 0.5); lit.Position = UDim2.fromScale(0.5, 0.5); lit.Size = UDim2.fromScale(1, 1)
		lit.ClipsDescendants = true; lit.Parent = bg
		local mono = Font.new("rbxasset://fonts/families/RobotoMono.json", Enum.FontWeight.Bold)
		-- (the briefing's own layout, small: what you'll see when it takes over; functional words only)
		local rows = { { "> LOADOUT", 0.05, 0.05, 0.08, true }, { "SIDEARM", 0.05, 0.17, 0.05 }, { "PASSIVE", 0.70, 0.17, 0.05 },
			{ "1  REVOLVER", 0.06, 0.25, 0.045 }, { "2  PISTOL", 0.06, 0.32, 0.045 }, { "3  SAWED-OFF", 0.06, 0.39, 0.045 },
			{ "4  LEFTY & RIGHTY", 0.06, 0.46, 0.045 }, { "BONUS PAY", 0.71, 0.25, 0.045 }, { "HEAD MONEY", 0.71, 0.32, 0.045 },
			{ "HOLD ON", 0.71, 0.39, 0.045 }, { "MENDER", 0.71, 0.46, 0.045 }, { "BOARD UP", 0.71, 0.53, 0.045 },
			{ "SCROUNGER", 0.71, 0.60, 0.045 }, { "> PICK A SIDEARM AND A PASSIVE_", 0.05, 0.86, 0.05, true }, { "READY", 0.72, 0.86, 0.06, true } }
		for _, rw in rows do
			local l = Instance.new("TextLabel")
			l.BackgroundTransparency = 1; l.Text = rw[1]; l.FontFace = mono; l.TextScaled = true
			l.TextColor3 = if rw[5] then Color3.fromRGB(110, 255, 150) else Color3.fromRGB(70, 200, 110)
			l.TextXAlignment = Enum.TextXAlignment.Left
			l.Position = UDim2.fromScale(rw[2], rw[3]); l.Size = UDim2.fromScale(0.6, rw[4])
			l.Parent = lit
		end
		for i = 0, 59 do -- (the scanlines)
			local f = Instance.new("Frame")
			f.BorderSizePixel = 0; f.BackgroundColor3 = Color3.new(0, 0, 0); f.BackgroundTransparency = 0.7
			f.Position = UDim2.fromScale(0, i / 60); f.Size = UDim2.fromScale(1, 1 / 180); f.Parent = lit
		end
		local glow = Instance.new("Frame")
		glow.Name = "Glow"; glow.BorderSizePixel = 0; glow.BackgroundColor3 = Color3.fromRGB(200, 255, 215); glow.BackgroundTransparency = 1
		glow.Size = UDim2.fromScale(1, 1); glow.Parent = lit
		sg.Parent = screen
		table.insert(r.trash, sg)
		pic = { lit = lit, glow = glow, bg = bg }
	end
	-- the news helicopter's camera: inside the grounds, up over the drive, drifting in; then the zoom onto the gate
	local hp0 = G - GO * 52 + UP * 26 - GR * 28
	local hp1 = G - GO * 40 + UP * 19 - GR * 12
	local front = G + UP * 2 + GO * 2 - GR * 6 -- (the wide: the drive, the gate, the street beyond)
	local gateLook = G + UP * 3.4 + GO * 1.2
	local deep = winAt - outward * 36 + Vector3.new(0, 10, 0) -- (the school shot looks into the building past the window)
	local function feedCam(t: number): (CFrame, number)
		local u = math.clamp(t / N.hit, 0, 1)
		local at = hp0:Lerp(hp1, u)
		local z0, z1 = N.zoom[1], N.zoom[2]
		local zu = math.clamp((t - z0) / (z1 - z0), 0, 1)
		zu = zu * zu * (3 - 2 * zu)
		local look = front:Lerp(gateLook, zu)
		local dist = (gateLook - at).Magnitude
		local fovWin = math.deg(2 * math.atan(8.5 / dist))
		local fov = (36 + 1.2 * math.sin(t * 1.7)) * (1 - zu) + (fovWin + 0.4 * math.sin(t * 2.3)) * zu -- (the lens breathing)
		return CFrame.lookAt(at, look), fov
	end
	local shots = {
		{ name = "feed", t0 = 0, t1 = N.static[2], shake = 0.32,
			cam = function(u: number): CFrame local cf = feedCam(u * N.static[2]); return cf end,
			fov = function(u: number): number local _, f = feedCam(u * N.static[2]); return f end },
		{ name = "school", t0 = N.school[1], t1 = N.school[2], ease = "linear", shake = 0.12,
			from = { at = winAt + outward * 58 + Vector3.new(0, 5, 0) + side * 30, look = deep, fov = 46 },
			to = { at = winAt + outward * 47 + Vector3.new(0, 6.5, 0) + side * 24, look = deep - Vector3.new(0, 1, 0), fov = 44 } },
		-- (27 Nov 2026, the owner's order) into the lobby terminal's screen till it fills the view: the BRIEFING holds
		-- there; then back out as it powers down, and into your own view
		{ name = "push", t0 = N.push[1], t1 = N.push[2], ease = "inout", shake = 0.05,
			from = { at = scr + sf * 11 + Vector3.new(0, 1.4, 0) - sx * 2.2, look = scr - Vector3.new(0, 0.2, 0), fov = 46 },
			to = { at = scr + sf * FILL, look = scr, fov = 32 } },
		{ name = "close", t0 = N.close[1], t1 = N.close[2], ease = "inout",
			from = { at = scr + sf * FILL, look = scr, fov = 32 },
			to = { at = scr + sf * 7 + Vector3.new(0, 0.9, 0) + sx * 1.4, look = scr - Vector3.new(0, 0.5, 0), fov = 44 } },
		{ name = "land", t0 = N.land[1], t1 = len, ease = "inout",
			from = { at = scr + sf * 7 + Vector3.new(0, 0.9, 0) + sx * 1.4, look = scr - Vector3.new(0, 0.5, 0), fov = 44 }, to = "gameplay" },
	}
	-- (27 Nov, main: if the prewarm isn't in when the lead ends, the black holds up to 2 s more, the sting carrying it:
	-- the film's own clock waits at 0 until it's in; the server's round 1 allows for it)
	-- (27 Nov 2026: the briefing (ZombieBrief) sits between the static and the school. while it's up the film holds in
	-- the static's last moment under it (r.inBrief); from BriefT1 the school plays on. a skip during the news jumps to
	-- it (r.toBrief))
	local AT = N.push[2]
	local function clk(): number
		local raw = srv() - (t0 :: number)
		if raw >= 0 and not r.warmReady and raw < 2 then r.shift = raw end
		local t = raw - (r.shift or 0)
		if type(a:GetAttribute("BriefT0")) == "number" then
			if r.toBrief and t < AT then t = AT end
			if t >= AT then
				local b1 = a:GetAttribute("BriefT1")
				if type(b1) == "number" and srv() >= b1 then
					t = AT + (srv() - b1)
					r.inBrief, r.briefDone = false, true
				else
					t = AT - 0.001
					r.inBrief = true
				end
			end
		end
		return t
	end
	-- (flag: HubLife leaves the light alone while it plays; 27 Nov test, its zone switch into the match ran the map room's
	-- black haze over the feed's first half second)
	r.cine = Cine.play(shots, { clock = clk, warm = 0.3, flag = "zmintro" })
	-- the lead (the server starts the film 1.4 s after the game): black, the prewarm under it, then the feed
	if (t0 :: number) - srv() > 0.05 then black.BackgroundTransparency = 0; r.leadBlack = true end
	-- the prewarm (27 Nov, the owner: "Things pop in because it renders as the clip plays"): every map piece the shots
	-- see kept drawn, everything the school, the cast and the sounds use preloaded under the lead and the feed's first
	-- second
	task.spawn(function()
		local lib0 = ReplicatedStorage:FindFirstChild("JankfireSounds")
		local sets: { Instance } = staticImages()
		table.insert(sets, a)
		local cineF = ReplicatedStorage:FindFirstChild("JankfireZmCine")
		if cineF then table.insert(sets, cineF) end
		for _, nm in { "zm_siren", "zm_drone", "zm_heli", "zm_static", "zm_wind", table.unpack(GATE_SOUNDS) } do
			local snd = lib0 and lib0:FindFirstChild(nm)
			if snd then table.insert(sets, snd) end
		end
		local w = Cine.prewarm(shots, { key = "zmintro", sets = sets, anims = { ZOMBIE_WALK, ZOMBIE_IDLE[1], ZOMBIE_IDLE[2], ZOMBIE_CLIMB }, timeout = 3 })
		if RunService:IsStudio() then print(("[ZombieCine] intro prewarm: ok %s, %.2f s, %d assets, %d pieces, %.2f s before the feed"):format(tostring(w.ok), w.waited, w.assets, #w.pieces, (t0 :: number) - srv())) end
		if film == r then r.warm = w; r.warmReady = true else w.release() end
	end)
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
	-- the sound under the feed (27 Nov, the owner: "Instead of like cheerful news could it be like warning sirens?"): an
	-- outdoor warning siren wailing over the town (PSE "Acme Whistle Wind Hurricane Siren 14": a hand-cranked siren's wind-up,
	-- long wail and wind-down; library, no upload), far off and echoing (farOff), from under the lead's black; a low drone
	-- under it (PSE "Evil Drone Eerie 1", only its low end). The siren drops under the static's burst and is cut with it;
	-- its wind-down carries faint into the school shot and is gone before the squad. An outdoor siren only: no alert tones
	local siren: Sound?, drone: Sound? = nil, nil
	local sirenTried = false
	local wash = bed("zm_heli")
	if wash then table.insert(r.beds, wash); fade(wash, 0.3, 0.4) end
	local rattle = bed("zm_gaterattle") -- (the crowd on the gate: up with the zoom, cut by the static)
	if rattle then table.insert(r.beds, rattle) end
	local nextBang, nextShake = 1.0, N.zoom[1] - 0.2
	local beam = Instance.new("Part")
	beam.Anchored, beam.CanCollide, beam.CanQuery, beam.CanTouch = true, false, false, false
	beam.Transparency = 1; beam.Size = Vector3.new(0.2, 0.2, 0.2); beam.Parent = workspace
	local sl = Instance.new("SpotLight"); sl.Face = Enum.NormalId.Front; sl.Range = 60; sl.Angle = 30; sl.Brightness = 3.5 -- (9 burnt the crowd white)
	sl.Color = Color3.fromRGB(236, 240, 232); sl.Shadows = true; sl.Parent = beam
	table.insert(r.trash, beam)
	-- the cool rim: from the street behind the crowd, up high, back toward the gate: their outlines against the dark
	local rim = Instance.new("Part")
	rim.Anchored, rim.CanCollide, rim.CanQuery, rim.CanTouch = true, false, false, false
	rim.Transparency = 1; rim.Size = Vector3.new(0.2, 0.2, 0.2)
	rim.CFrame = CFrame.lookAt(G + GO * 10 + UP * 9, G + UP * 3)
	rim.Parent = workspace
	local rl = Instance.new("SpotLight"); rl.Face = Enum.NormalId.Front; rl.Range = 22; rl.Angle = 75; rl.Brightness = 5
	rl.Color = Color3.fromRGB(150, 178, 232); rl.Shadows = false; rl.Parent = rim
	table.insert(r.trash, rim)
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
		local up = r.inBrief == true -- (the briefing's screen reads this: ZombieBrief.client)
		if me:GetAttribute("ZmBriefUp") ~= up then me:SetAttribute("ZmBriefUp", up) end
		skipL.Visible = not up
		skipB.Visible = Keys.isTouch() and not up
		if r.leadBlack and t >= 0 and (r.warmReady or srv() - (t0 :: number) >= 2) then
			r.leadBlack = false
			TweenService:Create(black, TweenInfo.new(0.15), { BackgroundTransparency = 1 }):Play()
		end
		if not sirenTried and t >= -1.3 then
			sirenTried = true
			if lib and lib:FindFirstChild("zm_siren") then
				local sg = (lib.zm_siren :: Sound):Clone()
				sg.Looped = false
				sg:SetAttribute("Full", sg.Volume)
				farOff(sg, -14, -2, -2)
				sg.Parent = SoundService; sg:Play(); table.insert(r.trash, sg)
				siren = sg
			end
			drone = bed("zm_drone")
			if drone then
				farOff(drone, -40, -14)
				table.insert(r.beds, drone); fade(drone, 1, 1.2)
			end
		end
		local vs = workspace.CurrentCamera.ViewportSize
		-- the feed's overlay
		local feedOn = t < N.static[1]
		o.root.Visible = feedOn and t >= 0 and not r.leadBlack -- (nothing of the feed over a held black)
		if feedOn then
			for k, f in o.scan do f.Position = UDim2.fromScale(0, ((k / #o.scan) + t * 0.05) % 1) end
			for _, f in o.grain do f.Position = UDim2.fromOffset(rng:NextInteger(0, math.max(1, vs.X)), rng:NextInteger(0, math.max(1, vs.Y))) end
			local zu = math.clamp((t - N.zoom[1]) / (N.zoom[2] - N.zoom[1]), 0, 1)
			o.box.Size = UDim2.fromScale(0.5 - 0.22 * zu, 0.5 - 0.2 * zu)
			o.dot.BackgroundTransparency = if (t % 1) < 0.55 then 0 else 0.7
			if not banner and t >= N.banner then
				banner = true
				TweenService:Create(o.third, TweenInfo.new(0.28, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Position = UDim2.new(0, 48, 1, -222) }):Play()
				if r.cine then r.cine.kick(0.5) end
			end
			if not line and t >= N.line then
				line = true
				TweenService:Create(o.line, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = UDim2.fromOffset(672, 48) }):Play()
			end
			-- the news helicopter's searchlight, from beside its camera: sweeping the crowd at the gate, then held on it
			local sweep = G + GO * (3 + 2 * math.sin(t * 0.8)) + GR * (7 * math.sin(t * 0.55)) + UP * 1.5
			sweep = sweep:Lerp(G + GO * 1.5 + UP * 2.5, zu * zu * (3 - 2 * zu))
			local from = hp0:Lerp(hp1, math.clamp(t / N.hit, 0, 1)) + GR * 3 - UP * 3
			beam.CFrame = CFrame.lookAt(from, sweep)
			sl.Brightness = 3.5 - 1.6 * zu -- (softer once it sits on the crowd)
			-- the crowd's sounds: the rattle up with the zoom, fists on the bars, the leaves heaving
			if rattle then rattle.Volume = (tonumber(rattle:GetAttribute("Full")) or 0.5) * (0.35 + 0.65 * zu) end
			if t >= nextBang and t < HIT then nextBang = t + rng:NextNumber(0.3, 0.65); sfx("zm_gatebang", nil, 0.35 + 0.45 * zu) end
			if t >= nextShake and t < HIT then nextShake = t + rng:NextNumber(1.0, 1.4); sfx("zm_gateshake", nil, 0.5 + 0.4 * zu) end
		else
			sl.Enabled = false
			rl.Enabled = false
		end
		-- the moon, held each frame up to the squad (27 Nov test: the school's own zone look lands a beat after the film
		-- starts and took the moon back, the feed read black); the haze thinner still while the feed runs
		local mw = r.moonWas
		if mw and t < N.push[1] then
			local amb, outd, ex = Color3.fromRGB(118, 130, 160), Color3.fromRGB(138, 156, 196), mw.exp + 0.95
			if Lighting.Ambient ~= amb then Lighting.Ambient = amb end
			if Lighting.OutdoorAmbient ~= outd then Lighting.OutdoorAmbient = outd end
			if Lighting.ExposureCompensation ~= ex then Lighting.ExposureCompensation = ex end
			local atm = Lighting:FindFirstChildOfClass("Atmosphere")
			local dn = if mw.dens then mw.dens * (if feedOn then 0.3 else 0.55) else nil
			if atm and dn and atm.Density ~= dn then atm.Density = dn end
		end
		-- the crowd at the gate: pressing, pushing, climbing; a lurch when it buckles. gone with the static
		local push = math.clamp((t - 0.5) / (HIT - 0.5), 0, 1) -- (the press builds to the buckle)
		local buck = if t >= HIT then math.min(1, (t - HIT) / 0.12) else 0
		if t < N.static[1] then
			for _, z in crowd do
				if z.tr and not z.phased and z.tr.Length > 0 then z.phased = true; z.tr.TimePosition = crng:NextNumber(0, z.tr.Length) end
				local sway = math.sin(t * z.w + z.ph)
				local zz, yy = z.z, z.y
				if z.kind == "arrive" then
					zz = 15 - 11.5 * math.clamp(t / 3.2, 0, 1) -- (walks up out of the street to the back of the crowd)
				end
				zz -= 0.18 * (0.5 + 0.5 * sway) * (0.4 + 0.6 * push) + 0.55 * buck -- (leaning in, harder as it builds; the lurch)
				if z.kind == "climb" then yy += 0.25 * math.sin(t * 3.1 + z.ph) + 0.4 * buck end
				local pos = G + GR * (z.x + 0.08 * math.sin(t * 1.9 + z.ph)) + GO * zz + UP * (3 + yy)
				local cf = CFrame.lookAt(pos, pos - GO) * CFrame.Angles(0, math.rad(z.yaw + 4 * math.sin(t * 1.3 + z.ph)), 0)
				if z.kind == "climb" then cf *= CFrame.Angles(math.rad(-22), 0, 0) end -- (leaning into the bars, over the backs)
				z.root.CFrame = cf
			end
			-- the leaves: rattling, heaving in as the press builds, a buckle at the hit
			for _, lf in leaves do
				local n1 = math.noise(t * 11, lf.seed) * 1.4 * (0.4 + push)
				local ang = (0.6 + 3.2 * push + 6.5 * buck + n1) * lf.sgn
				local lift = 0.04 * math.noise(t * 17, lf.seed + 3)
				local hc = lf.hcf * CFrame.new(0, lift, 0) * CFrame.Angles(0, math.rad(ang), 0)
				for _, q in lf.parts do q.p.CFrame = hc * q.rel end
			end
		elseif not r.crowdGone then
			r.crowdGone = true
			for _, z in crowd do z.m.Parent = nil end
			for _, lf in leaves do for _, q in lf.parts do q.p.CFrame = q.was end end -- (the gate as the map has it)
		end
		if not hit and t >= HIT then
			hit = true
			if r.cine then r.cine.kick(1.6) end
			sfx("zm_gateslam", nil, 1.0) -- (the gate buckles)
			task.delay(0.04, function() sfx("zm_gateshake", nil, 0.9) end)
		end
		-- the static, then black: the signal's gone
		local inStatic = t >= N.static[1] and t < N.school[1]
		o.static.Visible = inStatic
		if inStatic then
			if not staticOn then
				staticOn = true
				if siren then siren.Volume = (tonumber(siren:GetAttribute("Full")) or 1) * 0.1 end -- (under the burst)
				if drone then drone.Volume = 0 end
				if wash then fade(wash, 0, 0.2) end
				if rattle then rattle.Volume = 0 end
				if cc.Parent then cc:Destroy() end
				sfx("zm_static", nil, 0.9)
			end
			local u = math.clamp((t - N.static[1]) / math.max(0.05, N.school[1] - N.static[1]), 0, 1)
			for _, im in o.stIm do
				if #STATIC > 0 then im.Image = "rbxassetid://" .. tostring(STATIC[rng:NextInteger(1, #STATIC)]) end
				im.Rotation = if rng:NextNumber() < 0.5 then 0 else 180
				im.ImageTransparency = rng:NextNumber(0, 0.18)
			end
			-- the roll: one quick turn of the picture, then it judders
			local roll = if u < 0.35 then (u / 0.35) * 0.85 else 0.85 + rng:NextNumber(-0.03, 0.03)
			local jx = rng:NextNumber(-0.02, 0.02)
			o.stIm[1].Position = UDim2.fromScale(0.5 + jx, 0.5 + roll)
			o.stIm[2].Position = UDim2.fromScale(0.5 + jx, -0.5 + roll)
			-- the brightness flutter, a dark dropout now and then, the tears
			o.stFlash.BackgroundTransparency = rng:NextNumber(0.7, 0.97)
			o.stDark.BackgroundTransparency = if rng:NextNumber() < 0.14 then 0.35 else 1
			for _, f in o.tears do
				f.Visible = rng:NextNumber() < 0.7
				f.Size = UDim2.new(1, 0, 0, rng:NextInteger(3, 16))
				f.Position = UDim2.fromScale(0, rng:NextNumber())
				f.BackgroundTransparency = rng:NextNumber(0.25, 0.7)
			end
		end
		-- the school: our own lens, the bars, the wind; then the squad, the bars lift, your view
		if not schoolOn and t >= N.school[1] then
			schoolOn = true
			Cine.bars(true, 0.01)
			moon(r, 1, true, 0.01)
			wind = bed("zm_wind")
			if wind then table.insert(r.beds, wind); fade(wind, 1, 0.5) end
			-- the siren, fainter and further off now, winding down, gone before the squad
			if siren then
				local eq = siren:FindFirstChildOfClass("EqualizerSoundEffect")
				if eq then eq.HighGain = -26; eq.MidGain = -6 end
				siren.Volume = (tonumber(siren:GetAttribute("Full")) or 1) * 0.3
				TweenService:Create(siren, TweenInfo.new(math.max(0.3, N.school[2] - N.school[1] - 0.4), Enum.EasingStyle.Sine), { Volume = 0 }):Play()
			end
		end
		-- inside now: the lobby's own light (black frames over the change: a one-frame cut never shows a half-lit frame)
		if t >= N.push[1] and r.moonHigh ~= false then
			r.moonHigh = false
			moon(r, 1, false, 0.01)
			black.BackgroundTransparency = 0
			task.delay(0.06, function() if film == r and not r.leadBlack then black.BackgroundTransparency = 1 end end)
		end
		-- the terminal's picture: on through the push and the briefing; at the close it powers down (the picture folds to
		-- a bright line, the line to a dot, the dot out), with the CRT's own whine and click
		-- (the picture's own words fade as the push ends: the briefing takes over from plain green, its own layout coming in)
		if pic then
			local tx = math.clamp((t - (N.push[2] - 0.4)) / 0.3, 0, 1)
			if pic.tx ~= tx then
				pic.tx = tx
				for _, l in pic.lit:GetChildren() do if l:IsA("TextLabel") then l.TextTransparency = tx end end
			end
		end
		if pic and t >= N.close[1] then
			local u = t - N.close[1]
			if not r.offSaid and u >= 0.3 then
				r.offSaid = true
				sfx("zm_term_off", scr, 1)
				if okSfx and Sfx then pcall((Sfx :: any).play, "zm_term_hum", scr, 0.9, 0.62) end -- (the tube winding down)
			end
			local yS = if u < 0.3 then 1 elseif u < 0.55 then math.max(0.012, 1 - (u - 0.3) / 0.25) else 0.012
			local xS = if u < 0.55 then 1 elseif u < 0.75 then math.max(0.02, 1 - (u - 0.55) / 0.2) else 0.02
			pic.lit.Size = UDim2.fromScale(xS, yS)
			pic.glow.BackgroundTransparency = if u < 0.3 then 1 elseif u < 1.05 then 0.05 else 1
			pic.lit.Visible = u < 1.05
		end
		if not r.stepSaid and t >= N.land[1] then r.stepSaid = true; sfx("step_hard", nil, 0.55) end -- (you turn from the desk)
		if not lifted and t >= N.land[1] then lifted = true; Cine.bars(false, 0.6); if wind then fade(wind, 0, 0.8) end end
		if t >= len then finish(true) end
	end)
end
local function skip()
	if film and film.kind == "intro" then
		-- (the briefing: a skip during the news lands you in it, never past it (its own keys while it's up); after it
		-- the film ends as before)
		local a = arena()
		if a and type(a:GetAttribute("BriefT0")) == "number" and not film.briefDone then
			if not film.toBrief and not film.inBrief then
				film.toBrief = true
				zr:FireServer({ k = "xskip" })
			end
			return
		end
		-- (a late Enter meant for READY lands just after it closes: no skip in the first second of the school)
		local b1 = a and a:GetAttribute("BriefT1")
		if type(b1) == "number" and srv() < b1 + 1 then return end
		finish(true)
	elseif film and film.kind == "outro" and film.onSkip and film.aboard then film.onSkip() end -- (straight to the card)
end
Keys.began(function(io: any, _gp: boolean)
	if not film then return end
	local k = io.KeyCode
	if k == Enum.KeyCode.Space or k == Enum.KeyCode.Return or k == Enum.KeyCode.ButtonA then skip() end
end)
skipB.Activated:Connect(skip)

-- the crew member at the helicopter's door (the server's plain R15 in a flight suit): a built helmet with a dark visor,
-- anchored at the root, the reach (mocap) played on his own Animator. The helmet and visor are loose anchored parts
-- that follow his head each frame (r.gear; 27 Nov tests: welded inside his model the dome never drew in a game, though
-- it sat on his head and drew in Edit)
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
		helm.Size = Vector3.new(hd, hd, hd); helm.CanCollide = false; helm.CanQuery = false; helm.CanTouch = false; helm.Anchored = true
		local c0 = CFrame.new(0, hs.Y * 0.22, hs.Z * 0.05)
		helm.CFrame = head.CFrame * c0
		helm.Parent = workspace
		table.insert(r.trash, helm)
		local visor = Instance.new("Part")
		-- (opaque: a see-through Glass visor isn't drawn behind the door's window, so it came on only as the door slid open,
		-- with a white glint; 27 Nov frame check)
		visor.Name = "Visor"; visor.Color = Color3.fromRGB(16, 20, 26); visor.Material = Enum.Material.SmoothPlastic; visor.Reflectance = 0.12
		visor.Size = Vector3.new(hs.X * 1.02, hs.Y * 0.36, 0.12); visor.CanCollide = false; visor.CanQuery = false; visor.CanTouch = false; visor.Anchored = true
		local v0 = CFrame.new(0, hs.Y * 0.12, -hs.Z * 0.62)
		visor.CFrame = head.CFrame * v0
		visor.Parent = workspace
		table.insert(r.trash, visor)
		r.gear = { head = head, { p = helm, c0 = c0 }, { p = visor, c0 = v0 } }
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
-- the others who got out (27 Nov, the owner: teammates already aboard sit in the cabin): a copy of each one's body (a
-- player's or a squad bot's), scaled like the crew member, seated on a bench along the cabin's far side (Roblox's own R15
-- sit clip); their real bodies are hidden on this screen while the film runs (the bots walk to the door: the server
-- hides them at the cut)
local SIT = "rbxassetid://2506281703"
-- one seated copy of a body (a player's or a squad bot's), in the world, its sit clip playing. The game's own systems come
-- off at once (27 Nov, the finishers' frame check: a copy keeps the TPRig tag, and ThirdPerson draws its gun on it):
-- the tag, and ThirdPerson's and the server's gun pieces
local CollectionService = game:GetService("CollectionService")
local GUN_BITS = { TPGun = true, TPItem = true, TPRigArms = true, HeldWeapon = true }
local function seatCopy(s0: Model, at: CFrame?): (Model?, BasePart?)
	local was = s0.Archivable
	s0.Archivable = true
	local ok, c = pcall(function() return s0:Clone() end)
	s0.Archivable = was
	if not ok or not c then return nil, nil end
	local m = c :: Model
	CollectionService:RemoveTag(m, "TPRig")
	for _, d in m:GetDescendants() do
		if GUN_BITS[d.Name] and d.Parent then d:Destroy()
		elseif d:IsA("Script") or d:IsA("LocalScript") or d:IsA("Tool") or d:IsA("ForceField") or d:IsA("Sound") then d:Destroy()
		elseif d:IsA("BasePart") then d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.LocalTransparencyModifier = 0
		elseif d:IsA("Decal") then d.LocalTransparencyModifier = 0 end
	end
	pcall(function() m:ScaleTo(0.85) end)
	local root = m:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not root then m:Destroy(); return nil, nil end
	root.Anchored = true
	if at then root.CFrame = at end
	local hum = m:FindFirstChildOfClass("Humanoid")
	if hum then hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None end
	m.Parent = workspace
	if hum then
		local an = hum:FindFirstChildOfClass("Animator") or Instance.new("Animator", hum)
		local anim = Instance.new("Animation"); anim.AnimationId = SIT
		local ok2, tr = pcall(function() return (an :: Animator):LoadAnimation(anim) end)
		if ok2 and tr then tr.Looped = true; tr.Priority = Enum.AnimationPriority.Action; tr:Play(0) end
	end
	return m, root
end
local function matesOf(r: any, a: Model): { { m: Model, root: BasePart } }
	local seated = {}
	if not lastOut or srv() - lastOut.t > 20 then return seated end
	local cast = r.cast
	for _, nm in lastOut.who do
		if nm == me.DisplayName or #seated >= 3 then continue end
		local src: Model? = nil
		for _, pl in Players:GetPlayers() do
			if pl ~= me and pl.DisplayName == nm and pl.Character then src = pl.Character end
		end
		if not src then
			local b = a:FindFirstChild(nm, true)
			if b and b:IsA("Model") and b:FindFirstChildOfClass("Humanoid") then src = b end
		end
		if not src then continue end
		table.insert(r.hideReal, src)
		-- (the copy parked at the call, built and drawn by now: parkCast, below; a fresh one only if there's none)
		local pk = cast and cast.mates[nm]
		local m, root = nil, nil
		if pk and pk.m.Parent and pk.root.Parent then
			m, root = pk.m, pk.root
			cast.mates[nm] = nil
		else
			m, root = seatCopy(src :: Model)
		end
		if not m or not root then continue end
		table.insert(r.trash, m)
		table.insert(seated, { m = m, root = root })
	end
	return seated
end
-- the extraction film's cast, parked in the world out of sight from the call (27 Nov, the finishers' frame check: a mesh
-- is only built for drawing once it is in the workspace, so a copy made on the film's first frame comes in 2-6 frames
-- late, a body pale for its first frames, even with every asset fetched): the crew member with his helmet, and a seated
-- copy of each of the others in the game (players by display name, squad bots by name). The film takes them as they
-- stand (the crew member: outro; the seated: matesOf); what it doesn't take goes with the prewarm's release
local CAST_AT = CFrame.new(-4000, 3000, -40000) -- (far from every map, map room, copy row and stage)
local function parkCast(a: Model): any
	local cast: any = { trash = {}, mates = {} }
	local crew, croot, ctr = crewOf(cast)
	if crew and croot then
		croot.CFrame = CAST_AT
		local g = cast.gear
		if g and g.head and g.head.Parent then
			for _, x in ipairs(g) do x.p.CFrame = g.head.CFrame * x.c0 end
		end
		cast.crew = { m = crew, root = croot, track = ctr }
	end
	local k = 0
	local function add(key: string, src: Model)
		if cast.mates[key] or k >= 6 then return end
		k += 1
		local m, root = seatCopy(src, CAST_AT * CFrame.new(k * 6, 0, 0))
		if m and root then cast.mates[key] = { m = m, root = root } end
	end
	local zA = me:GetAttribute("ZmArena")
	for _, pl in Players:GetPlayers() do
		if pl ~= me and pl.Character and pl:GetAttribute("ZmArena") == zA then add(pl.DisplayName, pl.Character) end
	end
	for _, d in a:GetDescendants() do
		if d:IsA("Model") and string.match(d.Name, "^Bot %d+$") and d:FindFirstChildOfClass("Humanoid") then add(d.Name, d) end
	end
	cast.drop = function()
		for _, x in cast.trash do pcall(function() x:Destroy() end) end
		table.clear(cast.trash)
		for _, mt in cast.mates do pcall(function() mt.m:Destroy() end) end
		table.clear(cast.mates)
		local pc = cast.crew
		if pc then pcall(function() pc.m:Destroy() end) end
		cast.crew = nil
	end
	return cast
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
	local r: any = { guis = {}, vm = {}, trash = {}, beds = {}, showMe = false, kind = "outro", aboard = aboard, hideReal = {} }
	film = r
	me:SetAttribute("ZmFilm", true)
	local key = keyLight(r, 40, 1.4)
	moon(r, 0.8)
	-- (the first frames black: the film's own light comes in on its first frame and the renderer catches up a frame later;
	-- 27 Nov, the finishers' rule, docs/PERFORMANCE.md)
	black.BackgroundTransparency = 0
	local openFrames = 0
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
	-- (the prewarm started at the call, 90 s before: the film owns it now)
	if type(xWarm) == "table" then
		r.warm = xWarm
		r.cast = xWarm.cast
		xWarm = nil
	end
	local wind = bed("zm_wind")
	if wind then table.insert(r.beds, wind); fade(wind, 0.7, 0.8) end
	-- the crew member, and your own hand
	local crew, croot, ctr = nil, nil, nil
	local mytr: AnimationTrack? = nil
	local headDy = 1.5
	if aboard then
		local pc = r.cast and r.cast.crew
		if pc and pc.m.Parent and pc.root.Parent then
			crew, croot, ctr = pc.m, pc.root, pc.track
			r.gear = r.cast.gear
			for _, x in r.cast.trash do table.insert(r.trash, x) end
			table.clear(r.cast.trash)
			r.cast.crew = nil
		else
			crew, croot, ctr = crewOf(r)
		end
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
		-- (nothing of you until your hand comes up: 27 Nov test, the arm stood in the frame's corner from the start)
		r.showOnly = {}
		-- the others getting on (in the zone now): hidden on this screen from the first frame (27 Nov test: a bot walked
		-- across the doorway for half a second before the server's list put its copy on the bench)
		local function onPad(m: Model?)
			local rt = m and m:FindFirstChild("HumanoidRootPart") :: BasePart?
			return rt ~= nil and (Vector3.new(rt.Position.X - pad.Position.X, 0, rt.Position.Z - pad.Position.Z)).Magnitude <= z.r + 4
		end
		for _, pl in Players:GetPlayers() do
			if pl ~= me and pl.Character and onPad(pl.Character) then table.insert(r.hideReal, pl.Character) end
		end
		for _, d in a:GetDescendants() do
			if d:IsA("Model") and string.match(d.Name, "^Bot %d+$") and d:FindFirstChildOfClass("Humanoid") and onPad(d) then table.insert(r.hideReal, d) end
		end
	end
	local ARM = { LeftUpperArm = true, LeftLowerArm = true, LeftHand = true }
	local mates: any = nil
	local bench: BasePart? = nil
	local crewOn, handOn, doorSaid, clasped, cut, faded = false, false, false, false, false, false
	r.conn = RunService.RenderStepped:Connect(function()
		local t = clk()
		hold(r)
		if openFrames >= 0 then
			openFrames += 1
			if openFrames > 3 then openFrames = -1; black.BackgroundTransparency = 1 end
		end
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
				-- (his helmet and visor on his head, as it moves with the clip)
				local g = r.gear
				if g and g.head and g.head.Parent then
					for _, x in ipairs(g) do x.p.CFrame = g.head.CFrame * x.c0 end
				end
			end
			-- the others who got out, on the bench along the far side (the server's list can land a frame after the film)
			if not mates and lastOut and srv() - lastOut.t < 20 then
				mates = matesOf(r, a)
				if #mates > 0 then
					local b = Instance.new("Part")
					b.Name = "ZmBench"; b.Anchored = true; b.CanCollide = false; b.CanQuery = false; b.CanTouch = false
					b.Color = Color3.fromRGB(58, 60, 64); b.Material = Enum.Material.SmoothPlastic; b.Size = Vector3.new(1.3, 0.25, 4.8)
					b.Parent = workspace
					table.insert(r.trash, b)
					bench = b
				end
			end
			if mates and #mates > 0 then
				local d = hc:PointToObjectSpace(doorW())
				local seatTop = d.Y - 2.35 + 1.05
				if bench then bench.CFrame = hc * CFrame.new(d.X - side * 3.45, seatTop - 0.125, d.Z) end
				for k, mt in mates do
					local dz = ({ -1.45, 1.45, -2.9 })[k] or 0
					local pos = hc:PointToWorldSpace(Vector3.new(d.X - side * 3.25, seatTop + 0.4 + mt.root.Size.Y / 2, d.Z + dz))
					mt.root.CFrame = CFrame.lookAt(pos, pos + hc.RightVector * side)
				end
			end
			for _, real in r.hideReal do
				for _, x in real:GetDescendants() do
					if (x:IsA("BasePart") or x:IsA("Decal")) and (x :: any).LocalTransparencyModifier ~= 1 then (x :: any).LocalTransparencyModifier = 1 end
				end
			end
			-- your body under the lens, only the reaching arm to be seen
			if hrp then
				local e = eye(t)
				local f = Vector3.new(e.LookVector.X, 0, e.LookVector.Z).Unit
				-- (27 Nov tests: at the head the reaching hand stayed out of frame; a step ahead its arm came up at the frame's
				-- bottom left corner; a little right and up, it comes up to the middle to meet his)
				local rt = Vector3.new(e.RightVector.X, 0, e.RightVector.Z).Unit
				-- (the body starts low and rises with the reach: the hand comes up from the bottom of the frame)
				local rise = math.clamp((t - F.hand) / 0.45, 0, 1)
				local sink = 1.3 * (1 - rise) ^ 2
				local p = e.Position - Vector3.new(0, headDy + 0.1 + sink, 0) + f * 1.7 + rt * 0.45
				hrp.CFrame = CFrame.lookAt(p, p + f)
			end
			if not doorSaid and t >= F.door[1] then
				doorSaid = true
				local lib = ReplicatedStorage:FindFirstChild("JankfireSounds")
				sfx(if lib and lib:FindFirstChild("zm_doorslide") then "zm_doorslide" else "hunt_door_open", doorW(), 0.9)
			end
			if not crewOn and t >= F.crew and ctr then crewOn = true; ctr:Play(0.2) end
			if not handOn and t >= F.hand then
				handOn = true
				r.showOnly = ARM
				if mytr then mytr:Play(0.15) end
			end
			holdEnd(ctr); holdEnd(mytr)
			if not clasped and t >= F.step[2] then
				clasped = true
				if r.cine then r.cine.kick(0.6) end
				sfx(if (ReplicatedStorage:FindFirstChild("JankfireSounds") and ReplicatedStorage.JankfireSounds:FindFirstChild("zm_clasp")) then "zm_clasp" else "hunt_punch_hit", nil, 0.5)
			end
			if t >= F.cut then
				cut = true
				r.showOnly = {} -- (your body: gone in with him; the server hides it too)
				if crew then crew.Parent = nil end
				for _, x in ipairs(r.gear or {}) do x.p.Parent = nil end
				for _, mt in (mates or {}) :: any do mt.m.Parent = nil end
				if bench then bench.Parent = nil end
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
-- the extraction film's prewarm, from the call (the hold-out's 90 s): the roof, the helicopter's way out, the kit, the
-- crew member, the sounds and clips; the film takes it over (outro), or it's let go with the arena
local function xwarm(m: Model)
	if xWarm or m:GetAttribute("XSt") ~= "hold" then return end
	local z = XC.zones[m.Name]
	if not z then return end
	xWarm = true -- (claimed while it loads)
	task.spawn(function()
		local pad = ZM.padOf(m:GetPivot(), z)
		local pts = { pad.Position + Vector3.new(0, 6, 0), pad:PointToWorldSpace(Vector3.new(2, 16, 38)), pad:PointToWorldSpace(z.leave) }
		local sets: { Instance } = { m }
		for _, nm in { "JankfireZmKit", "JankfireZmCine" } do
			local f = ReplicatedStorage:FindFirstChild(nm)
			if f then table.insert(sets, f) end
		end
		local lib0 = ReplicatedStorage:FindFirstChild("JankfireSounds")
		for _, nm in { "zm_doorslide", "zm_clasp", "zm_wind", "zm_heli" } do
			local snd = lib0 and lib0:FindFirstChild(nm)
			if snd then table.insert(sets, snd) end
		end
		local w = Cine.prewarm(nil, { key = "zmextract", points = pts, sets = sets, anims = { XC.reach, SIT }, timeout = 30, keepFor = 300 })
		if RunService:IsStudio() then print(("[ZombieCine] extraction prewarm: ok %s, %.2f s, %d assets"):format(tostring(w.ok), w.waited, w.assets)) end
		if watched == m and xWarm == true then
			local cast = parkCast(m)
			local rel = w.release
			w.cast = cast
			w.release = function() pcall(rel); cast.drop() end
			xWarm = w
		else
			w.release()
		end
	end)
end
local conns: { RBXScriptConnection } = {}
local function watch()
	for _, c in conns do c:Disconnect() end
	table.clear(conns)
	if film then finish(true) end
	if type(xWarm) == "table" then xWarm.release() end
	xWarm = nil
	black.BackgroundTransparency = 1
	local a = nil
	for _ = 1, 40 do a = arena(); if a or not me:GetAttribute("ZmArena") then break end; task.wait(0.1) end
	watched = a
	if not a then return end
	local m = a :: Model
	local function check()
		if watched ~= m then return end
		if m:GetAttribute("XSt") == "hold" then xwarm(m) end
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

-- the early prewarm (27 Nov, main: start it as soon as this client is headed for ZOMBIES). From the moment its party
-- picks ZOMBIES (or a game starts) the school's, the films' and the helicopters' assets load in the background, assets
-- only (ZoneCull keeps the school put aside in the hub); the intro's own prewarm then finds them in
local okPU, PlayUI = pcall(function() return require(script.Parent:WaitForChild("PlayUI", 10) :: ModuleScript) :: any end)
local earlyT = -math.huge
local function early()
	if os.clock() - earlyT < 120 then return end
	earlyT = os.clock()
	task.spawn(function()
		local names = {}
		for nm in XC.zones do table.insert(names, nm) end
		local sets: { Instance } = staticImages()
		for _, nm in { "JankfireZmKit", "JankfireZmCine" } do
			local f = ReplicatedStorage:FindFirstChild(nm)
			if f then table.insert(sets, f) end
		end
		local lib0 = ReplicatedStorage:FindFirstChild("JankfireSounds")
		for _, nm in { "zm_siren", "zm_drone", "zm_heli", "zm_static", "zm_wind", "zm_doorslide", "zm_clasp", table.unpack(GATE_SOUNDS) } do
			local snd = lib0 and lib0:FindFirstChild(nm)
			if snd then table.insert(sets, snd) end
		end
		local w = Cine.prewarm(nil, { key = "zmearly", keep = false, names = names, sets = sets,
			anims = { ZOMBIE_WALK, ZOMBIE_IDLE[1], ZOMBIE_IDLE[2], ZOMBIE_CLIMB, XC.reach, SIT }, timeout = 90 })
		if RunService:IsStudio() then print(("[ZombieCine] early prewarm: ok %s, %.2f s, %d assets, %d pieces"):format(tostring(w.ok), w.waited, w.assets, #w.pieces)) end
	end)
end
task.spawn(function()
	while true do
		task.wait(1)
		local pt = if okPU and type(PlayUI) == "table" and PlayUI.S then PlayUI.S.party else nil
		if (pt and pt.mode == "zombies") or me:GetAttribute("ZmArena") then early() end
	end
end)
