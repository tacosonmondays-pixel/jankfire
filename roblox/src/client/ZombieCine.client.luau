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
	if ch and r.showMe then
		for _, d in ch:GetDescendants() do
			if (d:IsA("BasePart") or d:IsA("Decal")) and d.Name ~= "HumanoidRootPart" and (d :: any).LocalTransparencyModifier ~= 0 then
				(d :: any).LocalTransparencyModifier = 0
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

-- ------------------------------------------------------------------ the intro
local function intro(a: Model)
	local t0 = a:GetAttribute("IntroT0")
	local len = tonumber(a:GetAttribute("IntroLen")) or XC.intro
	if type(t0) ~= "number" or srv() > t0 + len - 1.2 or film then return end
	local okM, map = pcall(ZM.read, a)
	if not okM or not map then return end
	local site = a:GetPivot()
	local function L(x: number, y: number, z: number): Vector3 return site:PointToWorldSpace(Vector3.new(x, y, z)) end
	local r: any = { guis = {}, vm = {}, trash = {}, beds = {}, showMe = false, kind = "intro" }
	film = r
	me:SetAttribute("ZmFilm", true)
	-- the school's own night look from the first frame (27 Nov test: the hub's daylight flashed before the zone's look)
	if okLook and HubLook and HubLook.byArena and HubLook.byArena[a.Name] then pcall(HubLook.set, HubLook.byArena[a.Name], 0) end
	-- the window and the zombie for the second shot: a lobby window with clear floor inside it for the camera (27 Nov
	-- test: the first one put the lens inside the front desk)
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = { a }
	local w = nil
	local pick = map.windows[tonumber(a:GetAttribute("IntroWin")) or 0]
	for _, cand in map.windows do
		if cand.area ~= map.start then continue end
		local o = flat(cand.out - cand.inn).Unit
		local from = cand.inn + Vector3.new(0, 3.2, 0)
		local clear = workspace:Raycast(from, -o * 9, params) == nil -- (nothing between the boards and the lens)
		local floor = workspace:Raycast(from - o * 7, Vector3.new(0, -5, 0), params) ~= nil -- (and a floor under it)
		if clear and floor then w = cand; break end
	end
	w = w or pick or map.windows[1]
	local outward = if w then flat(w.out - w.inn).Unit else Vector3.new(0, 0, 1)
	local side = outward:Cross(Vector3.new(0, 1, 0))
	local zb: Model? = nil
	local zroot: BasePart? = nil
	local src = ReplicatedStorage:FindFirstChild("JankfireZmCine")
	local zt = src and src:FindFirstChild("Zombie")
	if w and zt and zt:IsA("Model") then
		zb = zt:Clone()
		local m = zb :: Model
		for _, d in m:GetDescendants() do if d:IsA("BasePart") then d.CanCollide = false; d.CanQuery = false; d.CanTouch = false end end
		zroot = m:FindFirstChild("HumanoidRootPart") :: BasePart?
		if zroot then zroot.Anchored = true end
		m.Parent = workspace
		table.insert(r.trash, m)
		local hum = m:FindFirstChildOfClass("Humanoid")
		if hum then
			local an = hum:FindFirstChildOfClass("Animator") or Instance.new("Animator", hum)
			local anim = Instance.new("Animation")
			anim.AnimationId = ZOMBIE_WALK
			local ok, tr = pcall(function() return (an :: Animator):LoadAnimation(anim) end)
			if ok and tr then tr.Looped = true; tr:Play(0); r.walk = tr end
		end
		local up = m:FindFirstChild("UpperTorso") or zroot
		if up then
			local l = Instance.new("PointLight") -- (a cold rim off the night outside: the body reads through the boards)
			l.Range = 9; l.Brightness = 1.4; l.Color = Color3.fromRGB(170, 190, 230); l.Shadows = false
			l.Parent = up
		end
	end
	local zFrom = if w then w.out + outward * 10 else Vector3.zero
	local zTo = if w then w.out + outward * 1.4 else Vector3.zero
	local HIT = 4.05
	-- the squad: their spawns' middle, the camera in front of them
	local c, face = Vector3.zero, Vector3.new(0, 0, -1)
	if #map.spawns > 0 then
		for _, s in map.spawns do c += s.Position end
		c /= #map.spawns
		face = flat(map.spawns[1].LookVector)
		if face.Magnitude < 0.1 then face = Vector3.new(0, 0, -1) end
		face = face.Unit
	else
		local ch = me.Character
		local hrp = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		if hrp then c = hrp.Position - Vector3.new(0, 3, 0); face = flat(hrp.CFrame.LookVector).Unit end
	end
	local shots = {
		-- (closer than the first cut: in the haze the far school was a black shape)
		{ name = "fly", t0 = 0, t1 = 2.9, ease = "linear", shake = 0.12,
			from = { at = L(-78, 70, -112), look = L(-4, 24, -20), fov = 50 },
			to = { at = L(-34, 58, -2), look = L(12, 8, 92), fov = 48 } },
		{ name = "window", t0 = 2.9, t1 = 5.0, ease = "out", shake = 0.22,
			-- (27 Nov test: from 7 studs in, the first frames were inside a prop the clear-line ray can't see (CanQuery off))
			from = { at = (if w then w.inn - outward * 5.6 + side * 0.8 + Vector3.new(0, 3.2, 0) else c), look = (if w then w.at.Position - Vector3.new(0, 0.6, 0) else c), fov = 56 },
			to = { at = (if w then w.inn - outward * 4.6 + side * 0.5 + Vector3.new(0, 3.0, 0) else c), look = (if w then w.at.Position - Vector3.new(0, 0.4, 0) else c), fov = 52 } },
		{ name = "squad", t0 = 5.0, t1 = 6.9, ease = "out", shake = 0.15,
			from = { at = c + face * 22 + Vector3.new(0, 4.2, 0), look = c + Vector3.new(0, 2.8, 0), fov = 54 },
			to = { at = c + face * 17 + Vector3.new(0, 3.8, 0), look = c + Vector3.new(0, 3.0, 0), fov = 52 } },
		{ name = "land", t0 = 6.9, t1 = len, ease = "inout",
			from = { at = c + face * 17 + Vector3.new(0, 3.8, 0), look = c + Vector3.new(0, 3.0, 0), fov = 52 }, to = "gameplay" },
	}
	local function clk(): number return srv() - (t0 :: number) end
	Cine.bars(true, 0.01)
	r.cine = Cine.play(shots, { clock = clk, warm = 0.3 })
	local key = keyLight(r, 40, 1.6)
	moon(r, 1, true, 0.01)
	local eased = false
	local wind = bed("zm_wind")
	if wind then table.insert(r.beds, wind); fade(wind, 1, 0.6) end
	local label = string.upper(map.label)
	local hit, titled, carded, lifted = false, false, false, false
	skipL.Text = if Keys.isTouch() then "" else "SPACE  SKIP"
	skipB.Visible = Keys.isTouch()
	r.onEnd = function() zr:FireServer({ k = "xskip" }) end
	r.conn = RunService.RenderStepped:Connect(function()
		local t = clk()
		hold(r)
		r.showMe = t >= 5.0 and t < 6.8 -- (not into the hand-back: the lens goes into your own head)
		local cam = workspace.CurrentCamera
		key.CFrame = cam.CFrame * CFrame.new(1.5, 1.2, 1)
		key:FindFirstChildOfClass("PointLight").Enabled = t >= 2.9 -- (the window and the squad: the fly-over has the moon)
		if not eased and t >= 2.9 then eased = true; moon(r, 1, false, 0.25) end -- (inside: the softer fill)
		if t >= 6.9 and r.moonWas then moonBack(r) end -- (eased back as the camera lands in your view)
		if not titled and t >= 0.6 then titled = true; card(label, true, 0.4); sfx("boom", nil, 0.6) end
		if not carded and t >= 2.55 then carded = true; card(label, false, 0.35) end
		-- the zombie: out of the fog to the boards, the hit, a step back
		if zroot then
			local u = math.clamp((t - 2.9) / (HIT - 0.05 - 2.9), 0, 1)
			local p = zFrom:Lerp(zTo, 1 - (1 - u) ^ 1.6)
			if t >= HIT and t < HIT + 0.12 then p = zTo - outward * 0.7 -- (into the boards)
			elseif t >= HIT + 0.12 then p = zTo + outward * math.clamp((t - HIT - 0.12) * 1.2, 0, 0.9) end
			zroot.CFrame = CFrame.lookAt(p + Vector3.new(0, 3, 0), p + Vector3.new(0, 3, 0) - outward)
			if r.walk then r.walk:AdjustSpeed(if t >= HIT and t < HIT + 0.08 then 0 else 1) end -- (the hit-stop)
		end
		if not hit and t >= HIT then
			hit = true
			if r.cine then r.cine.kick(1.5) end
			local at = if w then w.at.Position else nil
			sfx("zm_board", at, 1.0)
			task.delay(0.06, function() sfx("zm_planks", at, 0.8) end)
			if wind then fade(wind, 0.35, 0.1); task.delay(0.5, function() if film == r then fade(wind, 1, 0.6) end end) end
		end
		if not lifted and t >= 6.7 then lifted = true; Cine.bars(false, 0.6); if wind then fade(wind, 0, 0.8) end end
		if t >= len then finish(true) end
	end)
end
local function skip()
	if film and film.kind == "intro" then finish(true) end
end
Keys.began(function(io: any, _gp: boolean)
	if not film or film.kind ~= "intro" then return end
	local k = io.KeyCode
	if k == Enum.KeyCode.Space or k == Enum.KeyCode.Return or k == Enum.KeyCode.ButtonA then skip() end
end)
skipB.Activated:Connect(skip)

-- ------------------------------------------------------------------ the extraction out
local function outro(a: Model)
	local z = XC.zones[a.Name]
	local t0, lift = a:GetAttribute("XT0"), a:GetAttribute("XLift")
	if not z or type(t0) ~= "number" or type(lift) ~= "number" then return end
	local start = lift - XC.board
	if srv() > start + XC.outro - 0.5 then return end
	if film then finish(false) end
	local pad = ZM.padOf(a:GetPivot(), z)
	local liftT = lift - t0
	local function heliPos(): Vector3
		local cf = ZM.heliAt(pad, z, srv() - t0, liftT)
		return if cf then cf.Position + Vector3.new(0, 6, 0) else pad.Position + Vector3.new(0, 6, 0)
	end
	local r: any = { guis = {}, vm = {}, trash = {}, beds = {}, showMe = true, kind = "outro" }
	film = r
	me:SetAttribute("ZmFilm", true)
	local key = keyLight(r, 75, 1.7)
	moon(r, 0.8)
	local function P(x: number, y: number, zz: number): Vector3 return pad:PointToWorldSpace(Vector3.new(x, y, zz)) end
	local shots = {
		{ name = "board", t0 = 0, t1 = 3.4, ease = "linear", shake = 0.2,
			from = { at = P(-27, 8.5, 19), look = P(-2, 5, 0), fov = 52 },
			to = { at = P(-23, 7.5, 15), look = P(-2, 5.5, 0), fov = 50 } },
		-- (27 Nov test: from pad (9, 2.4, 27) the lens sat inside the HVAC unit by the skylights; west of the tail now,
		-- clear of the units and the skylights on the school's roof (school_layout.py's roof props))
		{ name = "lift", t0 = 3.4, t1 = 6.6, shake = 0.3,
			cam = function(u: number): CFrame
				local at = P(-14 + 2 * u, 3.0 - 0.4 * u, 20 - 3 * u)
				return CFrame.lookAt(at, heliPos())
			end, fov = 56 },
		-- (and from over the courtyard's edge, a long lens on it going north into the fog: the far wide shot was black)
		{ name = "away", t0 = 6.6, t1 = XC.outro, shake = 0.1,
			cam = function(u: number): CFrame
				local at = P(2, 16 + 2 * u, 38)
				return CFrame.lookAt(at, heliPos())
			end, fov = 32 },
	}
	local function clk(): number return srv() - start end
	Cine.bars(true, 0.3)
	r.cine = Cine.play(shots, { clock = clk })
	local wind = bed("zm_wind")
	if wind then table.insert(r.beds, wind); fade(wind, 0.7, 0.8) end
	-- your own body runs for the open side (your own run cycle: the Humanoid walks it)
	local ch = me.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	local hrp = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if hum and hrp and flat(hrp.Position - pad.Position).Magnitude <= z.r + 2 then
		hum:MoveTo(pad.Position - pad.RightVector * 4.2 + Vector3.new(0, 3, 0))
	end
	local faded = false
	r.conn = RunService.RenderStepped:Connect(function()
		local t = clk()
		hold(r)
		key.CFrame = workspace.CurrentCamera.CFrame * CFrame.new(2, 3, 2)
		if not faded and t >= XC.outro - 0.6 then
			faded = true
			TweenService:Create(black, TweenInfo.new(0.6), { BackgroundTransparency = 0 }):Play()
		end
		if t >= XC.outro then
			finish(true)
			TweenService:Create(black, TweenInfo.new(0.8), { BackgroundTransparency = 1 }):Play()
		end
	end)
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
