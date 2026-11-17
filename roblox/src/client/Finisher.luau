--!strict
-- FINISHER: plays one finisher cut (shared/Finishers.luau; roblox/docs/FINISHERS.md). The server sends the last moments
-- of the match recording before a winning kill (server/FinisherServer); this plays them on the replay's own ghost
-- bodies (client/Replay.luau: the same clean copies of each player, posed by ThirdPerson with their real skin, wrap and
-- hat) under a scripted camera, shot by shot:
--   HERO     low and in front of the shooter, pushing in as they line up the shot (the recording at half speed)
--   CHARGE   (the full cut) tight on the gun as the skin's light gathers into an orb at the muzzle
--   CHASE    the killing shot, slowed to a visible slug in the skin's colours, the lens riding beside it (bullet time,
--            a wide FOV punch that settles)                       (WHIP for a blade: the lens whips round the swing)
--   IMPACT   a close, tilted look at the hit, slowed: one flash, a shock ring, the theme's burst
--   RESOLVE  an orbit round the victim as the theme plays out (client/FinisherFx.luau), pulling out, then a fade
-- Every lens spot is tested against the map's solid boxes the way the replay camera does (Replay.clearTo), so no
-- shot ever sits inside a wall. Live bodies and the other screens are hidden while it plays, letterbox bars come in,
-- the colours are graded for the theme. SPACE / B / the SKIP button end it; so does a round going live, a respawn, or
-- a replay starting. It takes the camera only: nothing waits on it.
-- F.play(msg) -> boolean     msg = the server's (t = "finisher", id, kind, clip, focus, victim, w, skin, melee, by, role)
-- F.preview(id, opts?)       the same cut staged in front of you, from a made-up recording (the shop's preview, tests)
-- F.stop()                   F.isPlaying()
-- test knobs: workspace attributes FinisherSpeed (0..1, slows the whole cut for photos) and FinisherFreeze (hold at
-- that many s into the cut); the player attribute FinisherT shows where it is
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ContextActionService = game:GetService("ContextActionService")
local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local T = require(script.Parent:WaitForChild("Theme"))
local Replay = require(script.Parent:WaitForChild("Replay")) :: any
local Fx = require(script.Parent:WaitForChild("Fx")) :: any
local Sfx = require(script.Parent:WaitForChild("Sfx")) :: any
local TP = require(script.Parent:WaitForChild("ThirdPerson")) :: any
local FFx = require(script.Parent:WaitForChild("FinisherFx")) :: any
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Finishers = require(Shared:WaitForChild("Finishers")) :: any
local Weapons = require(Shared:WaitForChild("Weapons")) :: any
local SkinSets = require(Shared:WaitForChild("SkinSets")) :: any
local W = Weapons.list

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")
local new, text = T.new, T.text
local smooth, lerp, seg = FFx.smooth, FFx.lerp, FFx.seg
local UP = Vector3.yAxis

local F = {}
F.dummyLooks = {} :: { [string]: Model } -- (Studio tests: a training dummy's look as it spawned, FinisherClient keeps them)

local st: any = nil

local function smoother(x: number): number x = math.clamp(x, 0, 1); return x * x * x * (x * (x * 6 - 15) + 10) end
local function easeOut(x: number, p: number): number return 1 - (1 - math.clamp(x, 0, 1)) ^ p end
local function flat(v: Vector3): Vector3 return Vector3.new(v.X, 0, v.Z) end
local function unitOr(v: Vector3, alt: Vector3): Vector3 return if v.Magnitude > 1e-4 then v.Unit else alt end

-- ------------------------------------------------------------------ the camera's walls (the replay's)
-- the lens wants `want`, looking at `subject`: pulled in front of anything solid between them
local function safe(subject: Vector3, want: Vector3): Vector3
	local d = want - subject
	local L = d.Magnitude
	if L < 0.05 then return want end
	local free = Replay.clearTo(subject, want)
	if free < L - 0.01 then return subject + d.Unit * free end
	return want
end
-- how much of a set of lens spots round a subject is clear (0 = all blocked, #spots = all clear)
local function room(subject: Vector3, spots: { Vector3 }): number
	local n = 0
	for _, w in spots do
		local L = (w - subject).Magnitude
		if L > 0.01 then n += math.min(Replay.clearTo(subject, w), L) / L end
	end
	return n
end

-- ------------------------------------------------------------------ the overlay
local gui = new("ScreenGui", { Name = "JankFinisher", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 46, Enabled = false,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, pg)
local flashF = new("Frame", { Name = "Flash", BorderSizePixel = 0, BackgroundColor3 = Color3.new(1, 1, 1), BackgroundTransparency = 1,
	Size = UDim2.fromScale(1, 1), ZIndex = 1 }, gui)
local barTop = new("Frame", { Name = "BarTop", BorderSizePixel = 0, BackgroundColor3 = Color3.new(0, 0, 0), Size = UDim2.new(1, 0, 0, 0), ZIndex = 2 }, gui)
local barBot = new("Frame", { Name = "BarBottom", BorderSizePixel = 0, BackgroundColor3 = Color3.new(0, 0, 0), AnchorPoint = Vector2.new(0, 1),
	Position = UDim2.fromScale(0, 1), Size = UDim2.new(1, 0, 0, 0), ZIndex = 2 }, gui)
local scaled = T.scaled(gui)
scaled.ZIndex = 3
local nameT = text(scaled, "Finisher", "", 30, T.TEXT, T.FONT_TITLE, Enum.TextXAlignment.Left)
nameT.AnchorPoint = Vector2.new(0, 1); nameT.Position = UDim2.new(0, 44, 1, -14); nameT.Size = UDim2.fromOffset(600, 34); nameT.ZIndex = 4
local skinT = text(scaled, "Skin", "", 12, T.ACCENT, T.FONT_HEAVY, Enum.TextXAlignment.Left)
skinT.AnchorPoint = Vector2.new(0, 1); skinT.Position = UDim2.new(0, 46, 1, -49); skinT.Size = UDim2.fromOffset(600, 16); skinT.ZIndex = 4
local rule = new("Frame", { Name = "Rule", BorderSizePixel = 0, BackgroundColor3 = T.ACCENT, AnchorPoint = Vector2.new(0, 1),
	Position = UDim2.new(0, 46, 1, -9), Size = UDim2.fromOffset(0, 2), ZIndex = 4 }, scaled)
local skipB = new("TextButton", { Name = "Skip", AutoButtonColor = false, BackgroundColor3 = T.BG, BackgroundTransparency = T.BG_A, BorderSizePixel = 0,
	AnchorPoint = Vector2.new(1, 1), Position = UDim2.new(1, -28, 1, -14), Size = UDim2.fromOffset(132, 36), FontFace = T.FONT_BOLD, TextSize = 13,
	Text = "SKIP", TextColor3 = T.TEXT, TextXAlignment = Enum.TextXAlignment.Left, ZIndex = 4 }, scaled)
T.corner(skipB); T.edge(skipB)
new("UIPadding", { PaddingLeft = UDim.new(0, 66) }, skipB)
local skey = T.key(skipB, "", UDim2.fromOffset(-58, 7))
skey.Size = UDim2.fromOffset(50, 22)
skey.ZIndex = 5
local skeyT = skey:FindFirstChild("Letter") :: TextLabel?
if skeyT then skeyT.Text = "SPACE"; skeyT.TextSize = 10; skeyT.ZIndex = 6 end
local fadeF = new("Frame", { Name = "Fade", BorderSizePixel = 0, BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 1,
	Size = UDim2.fromScale(1, 1), ZIndex = 10 }, gui)
local BAR = 0.105 -- (each letterbox bar, of the screen's height)

-- ------------------------------------------------------------------ the clip's data
-- a track's position and yaw at clip time t (for laying out the stage before anything is posed)
local function trackAt(tr: any, t: number): (Vector3, number)
	local n = #tr.s
	local i = 1
	while i < n and tr.s[i + 1] <= t do i += 1 end
	local j = math.min(n, i + 1)
	local u = if j > i and tr.s[j] > tr.s[i] then math.clamp((t - tr.s[i]) / (tr.s[j] - tr.s[i]), 0, 1) else 0
	return tr.p[i]:Lerp(tr.p[j], u), tr.yaw[i]
end

local function infoOf(clip: any, slot: number): any
	local i = clip.info[tostring(slot)] or clip.info[slot]
	return i
end

local function lowest(m: Model, fallback: number): number
	local y = math.huge
	for _, n in { "LeftFoot", "RightFoot", "Left Leg", "Right Leg" } do
		local p = m:FindFirstChild(n) :: BasePart?
		if p and p:IsA("BasePart") then y = math.min(y, p.Position.Y - p.Size.Y / 2) end
	end
	return if y < math.huge then y else fallback
end

local function setFade(m: Model, a: number)
	for _, d in m:GetDescendants() do
		if (d:IsA("BasePart") or d:IsA("Decal")) and d.LocalTransparencyModifier ~= a then d.LocalTransparencyModifier = a end
	end
end

-- ------------------------------------------------------------------ hiding the rest of the game while it plays
local hidden: { [ScreenGui]: boolean } = {}
local function hideScreens()
	for _, g in pg:GetChildren() do
		if g:IsA("ScreenGui") and g ~= gui and g.Name ~= "JankPlayFade" and g.Enabled then hidden[g] = true; g.Enabled = false end
	end
end
local function showScreens()
	for g in hidden do if g.Parent then g.Enabled = true end end
	table.clear(hidden)
end
local function controls(on: boolean)
	pcall(function()
		local c = require(me:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: any):GetControls()
		if on then c:Enable() else c:Disable() end
	end)
end

-- ------------------------------------------------------------------ sounds
local function sfx(name: string, vol: number?)
	pcall(Sfx.play, name, nil, vol or 1)
end

-- ------------------------------------------------------------------ the shots: each gives the lens, where it looks, FOV, roll (deg)
local SHOTS = {}

-- HERO: low, in front of the shooter and off to one side, pushing in; the recording runs at about half speed
function SHOTS.hero(s: any, u: number): (Vector3, Vector3, number, number)
	local K = s.kg.root.Position
	local head = s.kg.model:FindFirstChild("Head") :: BasePart?
	local focus = (if head then head.Position else K + UP * 1.6) - UP * 0.45
	local f, r, sd = s.fwd, s.right, s.side
	local e = easeOut(u, 3)
	local p = (K + f * 5.0 + r * sd * 4.9):Lerp(K + f * 3.3 + r * sd * 3.0, e)
	local low = math.max(s.kFloor + 0.85, K.Y - 1.8)
	p = Vector3.new(p.X, lerp(low, low + 0.55, e), p.Z)
	return safe(focus, p), focus + f * 0.9, lerp(54, 43, smooth(u)), -sd * lerp(6, 2, u)
end

-- EYES (High Noon, in place of HERO): the standoff. Straight in on the shooter's eyes from in front, pushing in while
-- the lens widens, so they hold their size and the world behind them stretches away (a dolly zoom)
function SHOTS.eyes(s: any, u: number): (Vector3, Vector3, number, number)
	local head = s.kg.model:FindFirstChild("Head") :: BasePart?
	local eye = (if head then head.Position else s.kg.root.Position + UP * 1.6) + UP * 0.12
	local e = smooth(u)
	local p = eye + s.fwd * lerp(7.5, 2.6, e) + s.right * s.side * lerp(0.6, 0.25, e)
	return safe(eye, p), eye, lerp(17, 46, e), 0
end

-- CHARGE: tight on the gun from beside the muzzle, looking back along it, a slow push as the light gathers
function SHOTS.charge(s: any, u: number): (Vector3, Vector3, number, number)
	local M = s.M :: Vector3
	local e = smooth(u)
	local p = (M + s.right * s.side * 2.3 + s.fwd * 1.3 + UP * 0.45):Lerp(M + s.right * s.side * 1.6 + s.fwd * 0.8 + UP * 0.3, e)
	local look = M - s.fwd * 0.9
	return safe(look, p), look, lerp(44, 36, e), s.side * lerp(-8, -11, e)
end

-- CHASE: the killing shot as a slug, the lens riding just behind and beside it; a wide punch that settles
function SHOTS.chase(s: any, u: number): (Vector3, Vector3, number, number)
	local M, H = s.M :: Vector3, s.H :: Vector3
	local d = H - M
	local dir = s.dir :: Vector3
	local p = easeOut(u, 2.3)
	local slug = M + d * p
	if s.slug then s.slug.set(slug, dir) end
	local want = slug - dir * 3.1 + s.sideV * 1.25 + UP * 0.6
	local look = slug + dir * lerp(6, 2.2, p)
	return safe(slug, want), look, lerp(84, 58, easeOut(u, 2)), s.side * math.sin(u * math.pi) * 4
end

-- WHIP (a blade): the lens whips round the shooter through the swing
function SHOTS.whip(s: any, u: number): (Vector3, Vector3, number, number)
	local K = s.kg.root.Position
	local c = K + UP * 1.1
	local a = s.whipA0 + math.rad(150) * s.side * smoother(u)
	local r = lerp(5.6, 4.3, u)
	local want = c + Vector3.new(math.cos(a) * r, lerp(0.1, 0.9, u), math.sin(a) * r)
	return safe(c, want), c + s.fwd * lerp(0.5, 3.5, u), lerp(72, 56, u), s.side * math.sin(u * math.pi) * 5
end

-- IMPACT: close and tilted on the hit, pushing in (no shake: it is slowed down)
function SHOTS.impact(s: any, u: number): (Vector3, Vector3, number, number)
	local H = s.H :: Vector3
	local e = easeOut(u, 3)
	local p = (H + s.sideV * 3.9 - s.dir * 1.6 + UP * 0.35):Lerp(H + s.sideV * 2.8 - s.dir * 1.1 + UP * 0.5, e)
	return safe(H, p), H + UP * 0.15, lerp(50, 40, e), s.side * 9 * (1 - 0.4 * u)
end

-- RESOLVE: an orbit round the victim as the theme plays out, rising and pulling out
function SHOTS.resolve(s: any, u: number): (Vector3, Vector3, number, number)
	local o = s.theme.orbit
	local V = (s.vBase :: CFrame).Position
	local e = smoother(u)
	local ang = s.orbA0 + math.rad(o.sweep) * s.orbDir * e
	local r = lerp(o.r0, o.r1, smooth(u))
	local h = lerp(o.h0, o.h1, smooth(u))
	local look = V + UP * (lerp(o.look0, o.look1, smooth(u)) + (s.S.focusUp or 0))
	local want = V + Vector3.new(math.cos(ang) * r, h, math.sin(ang) * r)
	return safe(look, want), look, lerp(o.fov0, o.fov1, smooth(u)), 0
end

-- ------------------------------------------------------------------ moments
-- the clip time each shot plays at (s from the kill tk), u = 0..1 through the shot
local function clipTime(s: any, shot: string, u: number): number
	local tk = s.tk
	if shot == "hero" or shot == "eyes" then return tk - 0.45 + 0.4 * u
	elseif shot == "charge" then return tk - 0.05 + 0.02 * u
	elseif shot == "chase" then return tk - 0.03
	elseif shot == "whip" then return tk - 0.3 + 0.27 * u
	elseif shot == "impact" then return tk - 0.03 + 0.06 * u
	else return tk + 0.03 + 0.4 * u end
end

-- the killer's recorded shot as it happens (not the killing one: the chase draws that)
local function applyShot(s: any, e: any)
	local g = s.kg
	if not g.model.Parent then return end
	if e.t == "swing" then
		g.swing += 1
		g.model:SetAttribute("TPSwing", g.swing)
		sfx("swing", 0.7)
		return
	end
	g.fire += 1
	g.model:SetAttribute("TPFire", g.fire)
	local from = TP.muzzle(g.model) or (g.root.Position + UP * 1.5)
	local ends = {}
	for _, v in e.e or {} do if typeof(v) == "Vector3" then table.insert(ends, v) end end
	local sw = if type(e.w) == "string" then W[e.w] else nil
	if ends[1] and (ends[1] - from).Magnitude > 0.1 then
		pcall(Fx.gunShot, sw or { fx = {}, tracer = Color3.fromRGB(255, 240, 160) }, CFrame.lookAt(from, ends[1]), ends, nil, false)
	end
	if sw then pcall(Sfx.gun, sw, 0, from) end
end

-- the victim leaves the replay's hands: no gun, no walk, no third-person pose; their reaction (a generated clip when one
-- is in, else a shove back) and the theme move them from here
local function takeVictim(s: any)
	local vg = s.vg
	vg.model:SetAttribute("TPWeapon", nil)
	if vg.run then vg.run:Stop(0.1) end
	if vg.idle then vg.idle:Stop(0.1) end
	task.delay(0.05, function() if vg.model.Parent then CollectionService:RemoveTag(vg.model, "TPRig") end end)
	s.vBase = vg.root.CFrame
	s.vFloor = vg.root.Position.Y - (s.hipV or 3)
	s.S.floorY = s.vFloor
	s.S.victim = { model = vg.model, root = vg.root, base = s.vBase }
	local an = s.row.anim and Finishers.ANIMS[s.row.anim]
	if an and an.id ~= "" and vg.hum then
		local animator = vg.hum:FindFirstChildOfClass("Animator")
		if animator then
			local a = Instance.new("Animation")
			a.AnimationId = if string.find(an.id, "rbxassetid", 1, true) then an.id else "rbxassetid://" .. an.id
			local ok, track = pcall(function() return (animator :: Animator):LoadAnimation(a) end)
			if ok and track then
				track.Looped = false
				track.Priority = Enum.AnimationPriority.Action4
				track:Play(0.05, 1, 0.35 * an.speed)
				s.react = track
				s.reactSpeed = an.speed
			end
		end
	end
end

-- ------------------------------------------------------------------ stopping
local fadeTok = 0
function F.isPlaying(): boolean return st ~= nil end

function F.stop(quiet: boolean?)
	local s = st
	if not s then return end
	st = nil
	pcall(function() RunService:UnbindFromRenderStep("JankFinisherCam") end)
	pcall(function() ContextActionService:UnbindAction("JankFinisherSkip") end)
	if s.react then pcall(function() s.react:Stop(0) end) end
	for _, g in { s.kg, s.vg } do if g and g.model then g.model:Destroy() end end
	if s.run then FFx.clear(s.run) end
	if s.cc then s.cc:Destroy() end
	Replay.hideLive(false)
	showScreens()
	local cam = workspace.CurrentCamera :: Camera
	cam.CameraType = Enum.CameraType.Custom
	cam.FieldOfView = s.fov or 70
	me:SetAttribute("LoadoutOpen", s.loadoutWas == true)
	me:SetAttribute("Finishing", nil)
	me:SetAttribute("FinisherT", nil)
	controls(true)
	-- back from black, then the overlay goes
	fadeTok += 1
	local tok = fadeTok
	barTop.Size = UDim2.new(1, 0, 0, 0); barBot.Size = UDim2.new(1, 0, 0, 0)
	nameT.Text = ""; skinT.Text = ""; rule.Size = UDim2.fromOffset(0, 2); skipB.Visible = false
	flashF.BackgroundTransparency = 1
	if quiet then
		fadeF.BackgroundTransparency = 1
		gui.Enabled = false
		return
	end
	fadeF.BackgroundTransparency = math.min(fadeF.BackgroundTransparency, 0.15)
	T.tween(fadeF, 0.28, { BackgroundTransparency = 1 })
	task.delay(0.3, function() if tok == fadeTok and not st then gui.Enabled = false end end)
end

-- ------------------------------------------------------------------ playing
function F.play(msg: any): boolean
	F.stop(true)
	local row = Finishers.LIST[msg.id]
	if not row or not row.built then return false end
	local theme = FFx.THEMES[row.theme]
	local clip = msg.clip
	if not theme or type(clip) ~= "table" or type(clip.frames) ~= "table" or #clip.frames < 2 then return false end
	if Replay.isPlaying() then Replay.stop() end
	local tracks = Replay.decode(clip)
	local kt, vt = tracks[msg.focus], tracks[msg.victim]
	local ki, vi = infoOf(clip, msg.focus), infoOf(clip, msg.victim)
	if not kt or not vt or not ki or not vi or #kt.s == 0 or #vt.s == 0 then return false end
	-- the killing weapon in the killer's hands all through (a test arms a skin they may not have out)
	local weapons = table.clone(clip.weapons or {})
	local wi = table.find(weapons, msg.w)
	if not wi then table.insert(weapons, msg.w); wi = #weapons end
	for i in kt.w do kt.w[i] = wi :: number end
	-- the kill's moment, and the victim's last frame standing
	local tk: number? = nil
	local killShot: any = nil
	for _, e in clip.ev do
		if e.t == "kill" and e.v == msg.victim then tk = e.s end
	end
	tk = tk or vt.s[#vt.s]
	for _, e in clip.ev do
		if (e.t == "shot" or e.t == "swing") and e.s <= (tk :: number) + 0.05 then killShot = e end
	end
	local tv = vt.s[1]
	for i, t in vt.s do if vt.alive[i] == 1 then tv = t end end
	-- the ghosts: the two of them only
	local function ghost(slot: number, info: any, tr: any): any
		local inf = table.clone(info)
		if inf.kind ~= "player" and type(inf.modelName) == "string" and F.dummyLooks[inf.modelName] then
			inf.template = F.dummyLooks[inf.modelName]:Clone()
		elseif inf.kind == "player" and not Replay.templates[inf.id] and msg.preview and msg.previewLook then
			inf.template = msg.previewLook:Clone()
		end
		local ok, g = pcall(Replay.makeGhost, slot, inf, tr)
		return if ok then g else nil
	end
	local kg = ghost(msg.focus, ki, kt)
	local vg = ghost(msg.victim, vi, vt)
	if not kg or not vg then
		if kg then kg.model:Destroy() end
		if vg then vg.model:Destroy() end
		return false
	end
	-- (how high each root rides over its feet, read off the copy as it stands, before anything moves it: the floor
	-- under a moved body is its root minus this, with no wait for its joints to catch up)
	local function hip(g: any): number
		local y = g.root.Position.Y
		return math.clamp(y - lowest(g.model, y - 3), 1.5, 5)
	end
	local hipK, hipV = hip(kg), hip(vg)
	-- the stage: who stood where at the kill
	local K0 = trackAt(kt, tk :: number)
	local V0 = trackAt(vt, math.min(tk :: number, tv))
	local _, kyaw = trackAt(kt, tk :: number)
	local look = Vector3.new(-math.sin(kyaw), 0, -math.cos(kyaw))
	local fwd = unitOr(flat(V0 - K0), look)
	local right = fwd:Cross(UP).Unit
	local H = V0 + UP * 0.9
	if killShot and type(killShot.e) == "table" then
		for _, v in killShot.e do
			if typeof(v) == "Vector3" and (v - V0).Magnitude < 5 then H = v; break end
		end
	end
	local melee = msg.melee == true or (W[msg.w] and W[msg.w].kind == "melee")
	local cut = Finishers.cut(if msg.kind == "short" then "short" else "full", melee, row)
	local total = 0
	for _, sh in cut do total += sh[2] end
	-- the hero's side: the one with more room in front of them
	local function sideRoom(sd: number): number
		local c = K0 + UP * 1.3
		return room(c, { K0 + fwd * 5 + right * sd * 4.9 - UP * 1.6, K0 + fwd * 3.3 + right * sd * 3 - UP * 1.2, V0 + right * sd * 3.9 + UP * 0.4 })
	end
	Replay.gatherCamParts((K0 + V0) / 2)
	local side = if sideRoom(-1) > sideRoom(1) + 0.2 then -1 else 1
	local cam = workspace.CurrentCamera :: Camera
	local s: any = {
		msg = msg, row = row, theme = theme, cut = cut, total = total, w = 0, tk = tk, tv = tv, kt = kt, vt = vt,
		kg = kg, vg = vg, weapons = weapons, K0 = K0, V0 = V0, fwd = fwd, right = right, side = side, H = H, M = nil,
		dir = unitOr(H - (K0 + UP * 1.5), fwd), sideV = right * side, melee = melee, killShot = killShot,
		shot = 0, shotName = nil, shotT0 = 0, ei = 1, kFloor = K0.Y - hipK, hipV = hipV, fov = cam.FieldOfView, loadoutWas = me:GetAttribute("LoadoutOpen"),
		run = FFx.new(), S = { V = V0, H = H, fwd = fwd, right = right, side = side, floorY = V0.Y - hipV, dir = fwd },
		took = false, impacted = false, resolved = false, cues = {},
		lastCF = cam.CFrame, fadeOut = false, held = false,
	}
	s.S.dir = s.dir
	-- (the events from the start of the cut on; the kill shot itself is the chase's)
	local t0 = clipTime(s, cut[1][1], 0)
	while s.ei <= #clip.ev and clip.ev[s.ei].s < t0 - 0.02 do s.ei += 1 end
	-- first poses
	Replay.poseGhost(kg, t0, weapons)
	Replay.poseGhost(vg, math.min(t0, tv), weapons)
	-- the colour grade
	local cc = Instance.new("ColorCorrectionEffect")
	cc.Name = "JankFinisherGrade"
	cc.Parent = cam
	s.cc = cc
	st = s
	-- the overlay and the rest of the game
	nameT.Text = string.upper(row.name)
	local srow = SkinSets.SKINS[msg.skin]
	skinT.Text = if srow then string.upper(srow[1]) elseif type(msg.skin) == "string" then string.upper(string.gsub(string.match(msg.skin, "_(.+)$") or msg.skin, "_", " ")) else ""
	skinT.TextColor3 = row.colour
	rule.BackgroundColor3 = row.colour
	nameT.TextTransparency = 1; skinT.TextTransparency = 1
	skipB.Visible = true
	fadeTok += 1
	fadeF.BackgroundTransparency = 1
	gui.Enabled = true
	table.clear(hidden)
	hideScreens()
	me:SetAttribute("LoadoutOpen", true) -- (the hands and the guns hold still, no menu opens, the shoulder camera lets go)
	me:SetAttribute("Finishing", true)
	-- (a safety net: whatever ends it, the flag that holds back killcams never outlives it)
	task.delay(s.total + 3, function()
		if not st and me:GetAttribute("Finishing") then me:SetAttribute("Finishing", nil) end
	end)
	controls(false)
	Replay.hideLive(true)
	ContextActionService:BindActionAtPriority("JankFinisherSkip", function(_, state)
		if state == Enum.UserInputState.Begin then F.stop() end
		return Enum.ContextActionResult.Sink
	end, false, 3600, Enum.KeyCode.Space, Enum.KeyCode.ButtonB)
	RunService:BindToRenderStep("JankFinisherCam", Enum.RenderPriority.Last.Value + 72, function(dt: number)
		local ok, err = pcall(F._step, dt)
		if not ok then
			warn("[jankfire] finisher: " .. tostring(err))
			F.stop()
		end
	end)
	return true
end

-- one frame
function F._step(dt: number)
	local s = st
	if not s then return end
	if Replay.isPlaying() then F.stop(true); return end
	dt = math.min(dt, 0.1)
	-- (test knobs: slow the whole cut, or hold it at a moment, for photos)
	local speed = workspace:GetAttribute("FinisherSpeed")
	if type(speed) == "number" then dt *= math.clamp(speed, 0, 1) end
	local freeze = workspace:GetAttribute("FinisherFreeze")
	local before = s.w
	s.w += dt
	if type(freeze) == "number" then s.w = math.min(s.w, freeze) end
	local moving = s.w > before + 1e-6
	FFx.timeScale(s.run, if not moving then 0 else (if s.shotName == "impact" then 0.35 elseif s.shotName == "chase" then 0.25 else 1)
		* (if type(speed) == "number" then math.clamp(speed, 0.02, 1) else 1))
	if s.react then s.react:AdjustSpeed(if not moving then 0 else (if s.shotName == "impact" then 0.35 else 1) * (s.reactSpeed or 1) * (if type(speed) == "number" then math.clamp(speed, 0, 1) else 1)) end
	me:SetAttribute("FinisherT", math.floor(s.w * 100) / 100)
	-- which shot
	local acc, idx = 0, #s.cut
	for i, sh in s.cut do
		if s.w < acc + sh[2] then idx = i; break end
		acc += sh[2]
	end
	local t0 = 0
	for i = 1, idx - 1 do t0 += s.cut[i][2] end
	local name = s.cut[idx][1]
	local u = math.clamp((s.w - t0) / s.cut[idx][2], 0, 1)
	local cam = workspace.CurrentCamera :: Camera
	if idx ~= s.shot then
		s.shot = idx
		s.shotName = name
		s.blendFrom = if name == "chase" or name == "whip" then cam.CFrame else nil
		F._enter(s, name)
	end
	-- the recording
	local ct = clipTime(s, name, u)
	local ev = s.msg.clip.ev
	while s.ei <= #ev and ev[s.ei].s <= ct do
		local e = ev[s.ei]
		s.ei += 1
		if e ~= s.killShot and (e.t == "shot" or e.t == "swing") and (e.id == s.msg.focus or e.k == s.msg.focus) then pcall(applyShot, s, e) end
	end
	Replay.poseGhost(s.kg, ct, s.weapons)
	if not s.took then Replay.poseGhost(s.vg, math.min(ct, s.tv), s.weapons) end
	if name == "charge" and s.charge then s.charge.set(u) end
	-- a blade with no recorded swing: swing it here
	if name == "whip" and u >= 0.32 and not s.swung then
		s.swung = true
		if not s.killShot then
			s.kg.swing += 1
			s.kg.model:SetAttribute("TPSwing", s.kg.swing)
		end
		sfx("swing", 0.9)
		sfx("skin_" .. tostring(s.msg.skin) .. "_swing", 1)
	end
	-- the theme
	if name == "impact" and s.theme.impactStep then pcall(s.theme.impactStep, s.run, s.S, u) end
	if s.resolved and name == "resolve" then
		pcall(s.theme.resolve, s.run, s.S, u, dt)
		for _, c in s.theme.sounds.resolve or {} do
			if u >= c[1] and not s.cues[c] then s.cues[c] = true; sfx(c[2], c[3]) end
		end
	end
	-- the victim, once the theme has them
	if s.took then
		local vg = s.vg
		local rec = 1
		if name == "impact" then rec = easeOut(u, 2) end
		-- (no reaction clip: a shove along the shot and a tip away from it)
		local back = (s.vBase :: CFrame):VectorToObjectSpace(s.dir)
		local bf = Vector3.new(back.X, 0, back.Z)
		local shove = CFrame.new()
		if not s.react and bf.Magnitude > 1e-3 then
			shove = CFrame.new(bf.Unit * 0.45 * rec) * CFrame.fromAxisAngle(UP:Cross(bf.Unit), math.rad(9 * rec))
		end
		vg.root.CFrame = (s.vBase :: CFrame) * shove * (s.S.victimOffset or CFrame.new())
		local fa = s.S.victimFade or 0
		if fa ~= s.vFade then s.vFade = fa; setFade(vg.model, fa) end
	end
	-- the lens
	local pos, look, fov, roll = SHOTS[name](s, u)
	local cf = CFrame.lookAt(pos, look) * CFrame.Angles(0, 0, math.rad(roll))
	if s.blendFrom and u < 0.16 then cf = (s.blendFrom :: CFrame):Lerp(cf, smooth(u / 0.16)) end
	cam.CameraType = Enum.CameraType.Scriptable
	cam.CFrame = cf
	cam.FieldOfView = fov
	cam.Focus = CFrame.new(look)
	s.lastCF = cf
	-- the shooter fades when the lens rides past them
	local head = s.kg.model:FindFirstChild("Head") :: BasePart?
	if head then
		local k = math.clamp((3.2 - (pos - head.Position).Magnitude) / 1.6, 0, 0.85)
		if k ~= s.kFade then s.kFade = k; setFade(s.kg.model, k) end
	end
	-- the overlay: bars in, the names on the last shot, the flash, the fade out
	local barK = smooth(s.w / 0.2) * (1 - smooth((s.w - (s.total - 0.2)) / 0.2))
	barTop.Size = UDim2.new(1, 0, BAR * barK, 0)
	barBot.Size = UDim2.new(1, 0, BAR * barK, 0)
	local nameK = if name == "resolve" then smooth(u / 0.18) else 0
	nameT.TextTransparency = 1 - nameK
	skinT.TextTransparency = 1 - nameK
	rule.Size = UDim2.fromOffset(math.floor(220 * easeOut(nameK, 3)), 2)
	if s.flashT then
		local k = math.clamp((s.w - s.flashT) / 0.2, 0, 1)
		flashF.BackgroundTransparency = lerp(0.55, 1, k)
		if k >= 1 then s.flashT = nil end
	end
	local g = s.row.grade
	local gk = smooth(s.w / 0.25)
	local pop = if s.popT then math.max(0, 1 - (s.w - s.popT) / 0.18) else 0
	if s.popT and s.w - s.popT < 0.08 then
		-- the impact frame: the whole picture for a moment in two tones, black and the theme's colour
		s.cc.TintColor = s.theme.flash
		s.cc.Saturation = -1
		s.cc.Contrast = 1
		s.cc.Brightness = 0.05
	else
		s.cc.TintColor = Color3.new(1, 1, 1):Lerp(g.tint, gk)
		s.cc.Saturation = g.sat * gk
		s.cc.Contrast = g.con * gk
		s.cc.Brightness = g.bright * gk + 0.16 * pop
	end
	local endK = smooth((s.w - (s.total - 0.18)) / 0.18)
	fadeF.BackgroundTransparency = 1 - endK
	-- everything else stays hidden (a new screen like the end board may open under it)
	hideScreens()
	Replay.hideLive(true)
	if s.w >= s.total then F.stop() end
end

-- a shot begins
function F._enter(s: any, name: string)
	local S = s.S
	if name == "hero" then
		sfx("photoin", 0.45)
	elseif name == "eyes" then
		sfx("reverse", 0.5)
	elseif name == "charge" then
		-- the light gathers at the muzzle
		s.M = TP.muzzle(s.kg.model) or (s.kg.root.Position + UP * 1.5 + s.fwd * 1.5)
		s.charge = FFx.charge(s.run, s.M :: Vector3, s.theme.slug)
		sfx("reverse", 0.8)
	elseif name == "chase" then
		-- the killing shot: the flash, the gun and its skin layer, a whoosh; the slug sets off from the muzzle
		if s.charge then s.charge.done() end
		local M = TP.muzzle(s.kg.model) or s.M or (s.kg.root.Position + UP * 1.5 + s.fwd * 1.5)
		s.M = M
		s.dir = unitOr(s.H - M, s.fwd)
		S.dir = s.dir
		local sv = s.dir:Cross(UP)
		s.sideV = (if sv.Magnitude > 1e-3 then sv.Unit else s.right) * s.side
		s.kg.fire += 1
		s.kg.model:SetAttribute("TPFire", s.kg.fire)
		pcall(Fx.flash, CFrame.lookAt(M, s.H), false, s.theme.flash)
		local sw = W[s.msg.w]
		if sw then pcall(Sfx.gun, sw, 0, nil) end
		sfx("skin_" .. tostring(s.msg.skin) .. "_fire", 1)
		sfx("photoin", 0.6)
		s.slug = FFx.slug(s.run, s.theme.slug)
		s.slug.set(M, s.dir)
	elseif name == "whip" then
		local a = s.fwd + s.right * s.side * 1.2
		s.whipA0 = math.atan2(a.Z, a.X)
		sfx("photoin", 0.5)
	elseif name == "impact" then
		if s.slug then s.slug.done() end
		takeVictim(s)
		s.took = true
		s.S.H = s.H
		s.flashT = s.w
		s.popT = s.w
		flashF.BackgroundColor3 = s.theme.flash
		pcall(FFx.smoke, s.run, s.H, s.dir, s.theme.smoke)
		pcall(s.theme.impact, s.run, S)
		for _, n in s.theme.sounds.impact or {} do sfx(n, 0.9) end
		sfx("skin_" .. tostring(s.msg.skin) .. "_hit", 1)
	elseif name == "resolve" then
		if not s.took then takeVictim(s); s.took = true end
		s.resolved = true
		-- the orbit starts where the impact lens was and turns the way with more room
		local V = (s.vBase :: CFrame).Position
		local o = s.theme.orbit
		local c = s.lastCF.Position - V
		s.orbA0 = math.atan2(c.Z, c.X)
		local function arc(sgn: number): number
			local spots = {}
			for _, k in { 0.35, 0.7, 1 } do
				local a = s.orbA0 + math.rad(o.sweep) * sgn * k
				local r = lerp(o.r0, o.r1, k)
				table.insert(spots, V + Vector3.new(math.cos(a) * r, lerp(o.h0, o.h1, k), math.sin(a) * r))
			end
			return room(V + UP * o.look0, spots)
		end
		s.orbDir = if arc(-s.side) > arc(s.side) + 0.15 then -s.side else s.side
	end
end

-- ------------------------------------------------------------------ a preview: the same cut, staged in front of you
-- (the shop's skin card and tests): a made-up recording of you and a stand-in 16 studs ahead, the shot at 1.2 s
local function packFrame(recs: { { any } }): buffer
	local b = buffer.create(#recs * 24)
	for i, r in recs do
		local o = (i - 1) * 24
		local p: Vector3, yaw: number = r[2], r[3]
		buffer.writeu32(b, o, r[1])
		buffer.writef32(b, o + 4, p.X); buffer.writef32(b, o + 8, p.Y); buffer.writef32(b, o + 12, p.Z)
		buffer.writei16(b, o + 16, math.floor(yaw * 100 + 0.5))
		buffer.writei8(b, o + 18, 0)
		buffer.writeu8(b, o + 19, r[5] or 0)
		buffer.writeu8(b, o + 20, 0)
		buffer.writeu8(b, o + 21, r[4] or 1)
		buffer.writeu8(b, o + 22, 100)
		buffer.writeu8(b, o + 23, 1)
	end
	return b
end

function F.preview(fid: string, opts: any?): boolean
	local row = Finishers.LIST[fid]
	if not row or not row.built then return false end
	local skin = (opts and opts.skin) or row.skins[1]
	local srow = SkinSets.SKINS[skin]
	local wid = (opts and opts.weapon) or (srow and srow[3]) or "ar"
	local ch = me.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local at: CFrame = (opts and opts.at) or (if root then root.CFrame else CFrame.new(0, 10, 0))
	local dist = (opts and opts.dist) or (if W[wid] and W[wid].kind == "melee" then 5 else 16)
	local K = at.Position
	local fwd = unitOr(flat(at.LookVector), Vector3.new(0, 0, -1))
	local V = K + fwd * dist
	local kyaw = math.atan2(-fwd.X, -fwd.Z)
	local vyaw = math.atan2(fwd.X, fwd.Z)
	local frames = {}
	local t0 = os.clock()
	for i = 0, 18 do
		local t = t0 + i / 12
		table.insert(frames, { s = t, b = packFrame({ { 1, K, kyaw, 1, 0 }, { 2, V + at.RightVector * math.sin(i / 3) * 0.3, vyaw, 1, 0 } }) })
	end
	local tk = t0 + 1.4
	local H = V + Vector3.new(0, 0.9, 0)
	local look = Replay.templates[me.UserId]
	local victimInfo: any = { id = -2, name = "Stand-in", kind = "dummy", slot = 2 }
	local d = next(F.dummyLooks)
	if opts and opts.victimLook then victimInfo.template = opts.victimLook:Clone()
	elseif d then victimInfo.modelName = d
	elseif look then victimInfo.template = look:Clone()
	elseif ch then
		local was = ch.Archivable
		ch.Archivable = true
		local c = ch:Clone()
		ch.Archivable = was
		victimInfo.template = Replay.clean(c)
	end
	local clip = {
		t0 = t0, t1 = t0 + 1.5, rec = 24, frames = frames, weapons = { wid },
		ev = { { s = tk - 0.01, t = if W[wid] and W[wid].kind == "melee" then "swing" else "shot", id = 1, w = wid, e = { H } }, { s = tk, t = "kill", v = 2, k = 1, w = wid } },
		info = { ["1"] = { id = me.UserId, name = me.DisplayName, kind = "player", slot = 1, skins = wid .. "=" .. skin }, ["2"] = victimInfo },
	}
	local previewLook = nil
	if not look and ch then
		local was = ch.Archivable
		ch.Archivable = true
		previewLook = Replay.clean(ch:Clone())
		ch.Archivable = was
	end
	return F.play({ t = "finisher", id = fid, kind = (opts and opts.kind) or "full", clip = clip, focus = 1, victim = 2, w = wid, skin = skin,
		melee = W[wid] and W[wid].kind == "melee", by = me.DisplayName, role = "killer", preview = true, previewLook = previewLook })
end

skipB.MouseButton1Click:Connect(function() F.stop() end)

return F
