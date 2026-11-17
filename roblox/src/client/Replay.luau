--!strict
-- REPLAY: plays the server's recorded clips (server/Recorder.luau; roblox/docs/REPLAY.md; the web game's
-- public/js/replay.js). two kinds:
--   KILLCAM: you were killed: the last ~5 s from over your killer's shoulder. SKIP or the next round ends it
--   PLAY OF THE MATCH: after the end screen, the match's best kill run (or clutch) from over its hero's shoulder, a
--     short slow-down at each of the hero's kills. SKIP ends it for you
-- every player in the clip is a GHOST: a clone of their own character as it last spawned (ReplayClient keeps those),
-- tagged TPRig, so ThirdPerson.luau poses it exactly like a live player: the gun at its real skin, wrap and hat
-- (TPPlayer), the aim and the kick of each shot. a dummy's ghost is a clone of the dummy. shots, swings and kills are
-- drawn again from the clip's events through the game's own effects (Fx, Sfx). the live players are hidden while it
-- plays, and so is the rest of the HUD; the camera is ours
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local ContextActionService = game:GetService("ContextActionService")
local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local T = require(script.Parent:WaitForChild("Theme"))
local Fx = require(script.Parent:WaitForChild("Fx"))
local Sfx = require(script.Parent:WaitForChild("Sfx"))
local TP = require(script.Parent:WaitForChild("ThirdPerson"))
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local W = Weapons.list

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")
local new, text = T.new, T.text

local Replay = {}
Replay.templates = {} :: { [number]: Model } -- userId -> a clean copy of that player's look (ReplayClient fills it)
local TRACER = Color3.fromRGB(255, 240, 160)
local SLOW = { before = 0.25, after = 0.45, speed = 0.35 }
local CAM = { back = 11, side = 3.2, up = 2.2, fov = 70 }

type Track = { s: { number }, p: { Vector3 }, yaw: { number }, pitch: { number }, flags: { number }, pose: { number },
	w: { number }, hp: { number }, alive: { number } }
type Ghost = { slot: number, info: any, model: Model, root: BasePart, hum: Humanoid?, track: Track, i: number,
	wid: string?, fire: number, swing: number, gone: boolean, run: AnimationTrack?, idle: AnimationTrack?, skins: { [string]: string } }

local st: any = nil -- the clip playing now

-- ------------------------------------------------------------------ the clip's data
-- every record of every frame into one track per slot (the clip's frames all hold the same fighters)
local function decode(clip: any): { [number]: Track }
	local tracks: { [number]: Track } = {}
	local REC = clip.rec or 24
	for _, f in clip.frames do
		local b = f.b
		if typeof(b) ~= "buffer" then continue end
		local n = buffer.len(b) // REC
		for k = 0, n - 1 do
			local o = k * REC
			local slot = buffer.readu32(b, o)
			local tr = tracks[slot]
			if not tr then
				tr = { s = {}, p = {}, yaw = {}, pitch = {}, flags = {}, pose = {}, w = {}, hp = {}, alive = {} }
				tracks[slot] = tr
			end
			local t = tr :: Track
			table.insert(t.s, f.s)
			table.insert(t.p, Vector3.new(buffer.readf32(b, o + 4), buffer.readf32(b, o + 8), buffer.readf32(b, o + 12)))
			table.insert(t.yaw, buffer.readi16(b, o + 16) / 100)
			table.insert(t.pitch, buffer.readi8(b, o + 18))
			table.insert(t.flags, buffer.readu8(b, o + 19))
			table.insert(t.pose, buffer.readu8(b, o + 20))
			table.insert(t.w, buffer.readu8(b, o + 21))
			table.insert(t.hp, buffer.readu8(b, o + 22))
			table.insert(t.alive, buffer.readu8(b, o + 23))
		end
	end
	return tracks
end

local function parseSkins(v: any): { [string]: string }
	local out = {}
	if type(v) ~= "string" then return out end
	for w, sk in string.gmatch(v, "([%w_]+)=([%w_]+)") do out[w] = sk end
	return out
end

-- ------------------------------------------------------------------ ghosts
local folder: Folder? = nil
local function ghostFolder(): Folder
	if folder and folder.Parent then return folder end
	local f = Instance.new("Folder")
	f.Name = "JankReplayGhosts"
	f.Parent = workspace
	folder = f
	return f
end

-- a clean copy of a body to make a ghost from: the player's kept look, else their body as it is, else the dummy
local function sourceFor(info: any): Model?
	if info.kind == "player" then
		local t = Replay.templates[info.id]
		if t then return t end
		local p = Players:GetPlayerByUserId(info.id)
		local ch = p and p.Character
		if ch then
			local was = ch.Archivable
			ch.Archivable = true
			local c = ch:Clone()
			ch.Archivable = was
			return c
		end
		return nil
	end
	local d = workspace:FindFirstChild("Dummies")
	local m = d and type(info.modelName) == "string" and d:FindFirstChild(info.modelName)
	if m and m:IsA("Model") then
		local was = m.Archivable
		m.Archivable = true
		local c = m:Clone()
		m.Archivable = was
		return c
	end
	return nil
end

-- strip a copy down to a body: no scripts, no held gun, no tools; nothing collides, only the root is anchored
function Replay.clean(c: Model): Model
	local anim = c:FindFirstChild("Animate")
	local runId, idleId
	if anim then
		local run = anim:FindFirstChild("run")
		local ra = run and run:FindFirstChildWhichIsA("Animation")
		local idle = anim:FindFirstChild("idle")
		local ia = idle and idle:FindFirstChildWhichIsA("Animation")
		runId = ra and (ra :: Animation).AnimationId
		idleId = ia and (ia :: Animation).AnimationId
	end
	for _, d in c:GetDescendants() do
		if d:IsA("BaseScript") or d:IsA("Tool") or d:IsA("ForceField") or d:IsA("BillboardGui") or d:IsA("Sound")
			or d.Name == "HeldWeapon" or d.Name == "TPGun" then
			d:Destroy()
		end
	end
	for _, d in c:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = d.Name == "HumanoidRootPart"
			d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.CastShadow = false
			d.LocalTransparencyModifier = 0
		end
	end
	if runId then c:SetAttribute("RunAnim", runId) end
	if idleId then c:SetAttribute("IdleAnim", idleId) end
	return c
end

local function makeGhost(slot: number, info: any, tr: Track): Ghost?
	local src = sourceFor(info)
	if not src then return nil end
	local m = Replay.clean(if src.Parent == nil and Replay.templates[info.id] == src then src:Clone() else src)
	local root = m:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not root then m:Destroy(); return nil end
	m.Name = "Ghost_" .. tostring(info.name)
	local hum = m:FindFirstChildOfClass("Humanoid")
	if hum then
		hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
		pcall(function() (hum :: any).EvaluateStateMachine = false end)
		hum.PlatformStand = false
	end
	if info.kind == "player" then m:SetAttribute("TPPlayer", info.id) end
	m:SetAttribute("Skin", nil)
	m.Parent = ghostFolder()
	CollectionService:AddTag(m, "TPRig")
	local g: Ghost = { slot = slot, info = info, model = m, root = root, hum = hum, track = tr, i = 1, wid = nil, fire = 0, swing = 0,
		gone = false, run = nil, idle = nil, skins = parseSkins(info.skins) }
	-- the legs: their own run and idle (anchored root, so the walk is ours to weigh)
	local animator = hum and hum:FindFirstChildOfClass("Animator")
	if hum and not animator then animator = Instance.new("Animator"); animator.Parent = hum end
	if animator then
		for _, k in { "RunAnim", "IdleAnim" } do
			local id = m:GetAttribute(k)
			if type(id) == "string" and id ~= "" then
				local a = Instance.new("Animation")
				a.AnimationId = id
				local ok, track = pcall(function() return (animator :: Animator):LoadAnimation(a) end)
				if ok and track then
					track.Looped = true
					track:Play(0.1, if k == "IdleAnim" then 1 else 0.01)
					if k == "RunAnim" then g.run = track else g.idle = track end
				end
			end
		end
	end
	return g
end

-- ------------------------------------------------------------------ moving the ghosts
local function lerpAngle(a: number, b: number, u: number): number
	local d = (b - a + math.pi) % (2 * math.pi) - math.pi
	return a + d * u
end

-- a ghost at replay time t: between its two frames around t
local function poseGhost(g: Ghost, t: number, weapons: { string })
	local tr = g.track
	local n = #tr.s
	if n == 0 then return end
	while g.i < n and tr.s[g.i + 1] <= t do g.i += 1 end
	local i = g.i
	local j = math.min(n, i + 1)
	local u = if j > i and tr.s[j] > tr.s[i] then math.clamp((t - tr.s[i]) / (tr.s[j] - tr.s[i]), 0, 1) else 0
	local alive = tr.alive[i] == 1 and not g.gone
	if not alive then
		if g.model.Parent then g.model.Parent = nil end
		return
	end
	if not g.model.Parent then g.model.Parent = ghostFolder() end
	local p = tr.p[i]:Lerp(tr.p[j], u)
	local yaw = lerpAngle(tr.yaw[i], tr.yaw[j], u)
	g.root.CFrame = CFrame.new(p) * CFrame.Angles(0, yaw, 0)
	local pitch = tr.pitch[i] + (tr.pitch[j] - tr.pitch[i]) * u
	g.model:SetAttribute("TP", Vector3.new(pitch, 0, tr.flags[i]))
	g.model:SetAttribute("Pose", if tr.pose[i] == 1 then "crouch" elseif tr.pose[i] == 2 then "slide" else "stand")
	local wid = weapons[tr.w[i]]
	if wid ~= g.wid then
		g.wid = wid
		g.model:SetAttribute("Skin", if wid then g.skins[wid] else nil)
		g.model:SetAttribute("TPWeapon", wid)
	end
	-- the legs: run while moving
	local speed = if j > i and tr.s[j] > tr.s[i] then (Vector3.new(tr.p[j].X - tr.p[i].X, 0, tr.p[j].Z - tr.p[i].Z)).Magnitude / (tr.s[j] - tr.s[i]) else 0
	local w = math.clamp(speed / 20, 0, 1)
	if g.run then g.run:AdjustWeight(math.max(0.01, w), 0.15); g.run:AdjustSpeed(math.clamp(speed / 16, 0.5, 1.6)) end
	if g.idle then g.idle:AdjustWeight(math.max(0.01, 1 - w), 0.15) end
end

-- where a ghost's eyes are and where it looks (for the camera)
local function eyeOf(g: Ghost): (Vector3, Vector3, number)
	local head = g.model:FindFirstChild("Head") :: BasePart?
	local eye = if head then head.Position else g.root.Position + Vector3.new(0, 2.6, 0)
	local tr = g.track
	local yaw = tr.yaw[g.i] or 0
	local pitch = math.rad(tr.pitch[g.i] or 0)
	local dir = Vector3.new(-math.sin(yaw) * math.cos(pitch), math.sin(pitch), -math.cos(yaw) * math.cos(pitch))
	return eye, dir, yaw
end

-- ------------------------------------------------------------------ the events
local function applyEvent(e: any)
	local g = st.ghosts[e.id or e.k or 0]
	if e.t == "shot" then
		if not g or g.gone or not g.model.Parent then return end
		g.fire += 1
		g.model:SetAttribute("TPFire", g.fire)
		local from = TP.muzzle(g.model) or (eyeOf(g))
		local ends = {}
		for _, v in e.e or {} do if typeof(v) == "Vector3" then table.insert(ends, v) end end
		local first = ends[1]
		local sw = if type(e.w) == "string" then W[e.w] else nil
		local sfx = (sw and sw.fx) or {}
		if first and (first - from).Magnitude > 0.1 then
			pcall(Fx.gunShot, sw or { fx = sfx, tracer = TRACER }, CFrame.lookAt(from, first), if sfx.spray then {} else ends, nil, false)
		end
		if sfx.spray then pcall(Fx.marbles, from, ends, 8) end
		if sw then pcall(Sfx.gun, sw, 0, from) end
		pcall(Fx.shotEnds, from, ends, sfx.spray == true)
	elseif e.t == "swing" then
		if not g or g.gone then return end
		g.swing += 1
		g.model:SetAttribute("TPSwing", g.swing)
		pcall(Sfx.play, "swing", g.root.Position)
	elseif e.t == "kill" then
		local v = st.ghosts[e.v]
		if v and not v.gone then
			local at = v.root.Position + Vector3.new(0, 1.5, 0)
			pcall(Fx.sparks, at, Vector3.yAxis, 26, 0.2)
			v.gone = true
			v.model.Parent = nil
		end
		if e.k == st.focus then
			pcall(Sfx.play, "kill")
			st.kills += 1
			if st.killText then st.killText.Text = if st.kills >= 2 then ("%d KILLS"):format(st.kills) else "KILL" end
		end
	end
end

-- ------------------------------------------------------------------ the camera: over the focus's shoulder
local rayP = RaycastParams.new()
rayP.FilterType = Enum.RaycastFilterType.Include
local function camStep(dt: number)
	local cam = workspace.CurrentCamera :: Camera
	cam.CameraType = Enum.CameraType.Scriptable
	if math.abs(cam.FieldOfView - CAM.fov) > 0.01 then cam.FieldOfView = CAM.fov end
	local f: Ghost? = st.ghosts[st.focus]
	local eye, dir, yaw
	if f and not f.gone and f.model.Parent then
		eye, dir, yaw = eyeOf(f)
		st.lastEye, st.lastYaw = eye, yaw
	elseif st.lastEye then -- the focus died: drift round where they were
		st.lastYaw += dt * 0.6
		eye, yaw = st.lastEye, st.lastYaw
		dir = Vector3.new(-math.sin(yaw) * 0.8, -0.45, -math.cos(yaw) * 0.8).Unit
	else
		return
	end
	local right = Vector3.new(math.cos(yaw), 0, -math.sin(yaw))
	local map = workspace:FindFirstChild("Map")
	rayP.FilterDescendantsInstances = if map then { map } else {}
	local best = nil
	for _, o in { { st.side or 1, CAM.up }, { -(st.side or 1), CAM.up }, { 0, CAM.up * 2.6 } } do
		local want = eye - dir * CAM.back + right * (o[1] * CAM.side) + Vector3.new(0, o[2], 0)
		local d = want - eye
		local L = d.Magnitude
		local hit = workspace:Raycast(eye, d, rayP)
		local free = if hit then math.max(1, (hit.Position - eye).Magnitude - 1) else L
		if not best or free > best.free + 1.2 then best = { free = free, d = d.Unit, side = o[1] } end
		if free >= L then break end
	end
	if best.side ~= 0 then st.side = best.side end
	local pos = eye + best.d * best.free
	local look = eye + dir * 90
	if not st.camPos then st.camPos, st.camLook = pos, look end
	st.camPos = st.camPos:Lerp(pos, math.min(1, dt * 12))
	st.camLook = st.camLook:Lerp(look, math.min(1, dt * 9))
	cam.CFrame = CFrame.lookAt(st.camPos, st.camLook)
	cam.Focus = CFrame.new(eye)
end

-- ------------------------------------------------------------------ the overlay: what this is, who, SKIP
local gui = new("ScreenGui", { Name = "JankReplay", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 45, Enabled = false,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, pg)
-- thin cinema bars, top and bottom
local barTop = new("Frame", { Name = "BarTop", BorderSizePixel = 0, BackgroundColor3 = Color3.new(0, 0, 0), Size = UDim2.new(1, 0, 0.07, 0) }, gui)
local barBot = new("Frame", { Name = "BarBottom", BorderSizePixel = 0, BackgroundColor3 = Color3.new(0, 0, 0), AnchorPoint = Vector2.new(0, 1),
	Position = UDim2.fromScale(0, 1), Size = UDim2.new(1, 0, 0.07, 0) }, gui)
local _ = barTop; local _b = barBot
local scaled = T.scaled(gui)
local banner = T.plate(scaled, "Banner", UDim2.new(0.5, 0, 0, 62), UDim2.fromOffset(420, 78))
banner.AnchorPoint = Vector2.new(0.5, 0)
local kicker = text(banner, "Kicker", "", 12, T.ACCENT, T.FONT_HEAVY, Enum.TextXAlignment.Center)
kicker.Position = UDim2.fromOffset(0, 10); kicker.Size = UDim2.new(1, 0, 0, 16)
local who = text(banner, "Who", "", 24, T.TEXT, T.FONT_TITLE, Enum.TextXAlignment.Center)
who.Position = UDim2.fromOffset(0, 26); who.Size = UDim2.new(1, 0, 0, 30); who.TextTruncate = Enum.TextTruncate.AtEnd
local what = text(banner, "What", "", 13, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Center)
what.Position = UDim2.fromOffset(0, 54); what.Size = UDim2.new(1, 0, 0, 16)
local track = new("Frame", { Name = "Progress", BorderSizePixel = 0, BackgroundColor3 = T.TRACK, AnchorPoint = Vector2.new(0.5, 1),
	Position = UDim2.new(0.5, 0, 1, -64), Size = UDim2.fromOffset(360, 3) }, scaled)
T.corner(track, 2)
local fill = new("Frame", { BorderSizePixel = 0, BackgroundColor3 = T.ACCENT, Size = UDim2.fromScale(0, 1) }, track)
T.corner(fill, 2)
local skipB = new("TextButton", { Name = "Skip", AutoButtonColor = false, BackgroundColor3 = T.BG, BackgroundTransparency = T.BG_A, BorderSizePixel = 0,
	AnchorPoint = Vector2.new(1, 1), Position = UDim2.new(1, -28, 1, -54), Size = UDim2.fromOffset(132, 36), FontFace = T.FONT_BOLD, TextSize = 13,
	Text = "SKIP", TextColor3 = T.TEXT, TextXAlignment = Enum.TextXAlignment.Left }, scaled)
T.corner(skipB); T.edge(skipB)
new("UIPadding", { PaddingLeft = UDim.new(0, 66) }, skipB)
local skey = T.key(skipB, "", UDim2.fromOffset(-58, 7))
skey.Size = UDim2.fromOffset(50, 22)
local skeyT = skey:FindFirstChild("Letter") :: TextLabel?
if skeyT then skeyT.Text = "SPACE"; skeyT.TextSize = 10 end

-- ------------------------------------------------------------------ playing
local hidden: { [ScreenGui]: boolean } = {}
local function hideLive(on: boolean)
	-- (the live bodies would stand among the ghosts: hidden on this screen while it plays)
	for _, p in Players:GetPlayers() do
		local ch = p.Character
		if ch then for _, d in ch:GetDescendants() do if d:IsA("BasePart") or d:IsA("Decal") then d.LocalTransparencyModifier = if on then 1 else 0 end end end
	end
	local dm = workspace:FindFirstChild("Dummies")
	if dm then for _, d in dm:GetDescendants() do if d:IsA("BasePart") or d:IsA("Decal") then d.LocalTransparencyModifier = if on then 1 else 0 end end end
end

local function controls(on: boolean)
	pcall(function()
		local c = require(me:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: any):GetControls()
		if on then c:Enable() else c:Disable() end
	end)
end

function Replay.isPlaying(): boolean return st ~= nil end
function Replay.mode(): string? return if st then st.mode else nil end

function Replay.stop()
	local s = st
	if not s then return end
	st = nil
	pcall(function() RunService:UnbindFromRenderStep("JankReplayCam") end)
	pcall(function() ContextActionService:UnbindAction("JankReplaySkip") end)
	if s.conn then s.conn:Disconnect() end
	for _, g in s.ghosts do g.model:Destroy() end
	hideLive(false)
	gui.Enabled = false
	for g in hidden do if g.Parent then g.Enabled = true end end
	table.clear(hidden)
	local cam = workspace.CurrentCamera :: Camera
	cam.CameraType = Enum.CameraType.Custom
	cam.FieldOfView = s.fov or 70
	if s.menu then me:SetAttribute("LoadoutOpen", s.loadoutWas == true) end
	controls(true)
	if s.onEnd then task.spawn(s.onEnd) end
end

-- play a clip from the server: msg = { t = "killcam" | "potm", clip, focus, ... }
function Replay.play(msg: any, opts: any?): boolean
	Replay.stop()
	local clip = msg.clip
	if type(clip) ~= "table" or type(clip.frames) ~= "table" or #clip.frames < 3 then return false end
	local tracks = decode(clip)
	local ghosts: { [number]: Ghost } = {}
	for k, info in clip.info or {} do
		local slot = tonumber(k) :: number
		local tr = tracks[slot]
		if tr and #tr.s > 0 then
			local ok, g = pcall(makeGhost, slot, info, tr)
			if ok and g then ghosts[slot] = g end
		end
	end
	local t0 = clip.frames[1].s
	local t1 = clip.frames[#clip.frames].s
	local mode = if msg.t == "potm" then "potm" else "killcam"
	-- the hero's kills slow down a moment (the play of the match)
	local slow = {}
	if mode == "potm" then
		for _, e in clip.ev do if e.t == "kill" and e.k == msg.focus then table.insert(slow, { e.s - SLOW.before, e.s + SLOW.after }) end end
	end
	local cam = workspace.CurrentCamera :: Camera
	st = { mode = mode, clip = clip, ghosts = ghosts, focus = msg.focus, t = t0, t0 = t0, t1 = t1, ei = 1, slow = slow, kills = 0,
		fov = cam.FieldOfView, camPos = nil, camLook = nil, side = 1, lastEye = nil, lastYaw = 0, onEnd = opts and opts.onEnd,
		menu = mode == "potm", loadoutWas = me:GetAttribute("LoadoutOpen"), killText = nil }
	-- the overlay
	if mode == "killcam" then
		kicker.Text = "KILLCAM"
		who.Text = string.upper(tostring(msg.by or "?"))
		local wpn = if type(msg.w) == "string" and W[msg.w] then W[msg.w].name else nil
		what.Text = if wpn then string.upper(wpn) else ""
		st.killText = nil
	else
		kicker.Text = "PLAY OF THE MATCH"
		who.Text = string.upper(tostring(msg.name or "?"))
		what.Text = tostring(msg.label or "")
		st.killText = nil
	end
	table.clear(hidden)
	for _, g in pg:GetChildren() do
		if g:IsA("ScreenGui") and g ~= gui and g.Name ~= "JankPlayFade" and g.Enabled then hidden[g] = true; g.Enabled = false end
	end
	gui.Enabled = true
	if st.menu then me:SetAttribute("LoadoutOpen", true) end -- (the hands and the guns hold still, and no menu opens)
	controls(false)
	hideLive(true)
	ContextActionService:BindActionAtPriority("JankReplaySkip", function(_, state)
		if state == Enum.UserInputState.Begin then Replay.stop() end
		return Enum.ContextActionResult.Sink
	end, false, 3500, Enum.KeyCode.Space, Enum.KeyCode.ButtonB)
	RunService:BindToRenderStep("JankReplayCam", Enum.RenderPriority.Last.Value + 70, function(dt: number)
		local s = st
		if not s then return end
		dt = math.min(dt, 0.1)
		local sp = 1
		for _, w in s.slow do if s.t >= w[1] and s.t <= w[2] then sp = SLOW.speed end end
		s.t += dt * sp
		while s.ei <= #s.clip.ev and s.clip.ev[s.ei].s <= s.t do
			local ok, err = pcall(applyEvent, s.clip.ev[s.ei])
			if not ok then warn("[jankfire] replay event: " .. tostring(err)) end
			s.ei += 1
		end
		for _, g in s.ghosts do poseGhost(g, s.t, s.clip.weapons or {}) end
		camStep(dt)
		fill.Size = UDim2.fromScale(math.clamp((s.t - s.t0) / math.max(0.01, s.t1 - s.t0), 0, 1), 1)
		hideLive(true) -- (every frame: other scripts set these too, and a respawn mid-replay brings a new body)
		if s.t >= s.t1 then Replay.stop() end
	end)
	return true
end

skipB.MouseButton1Click:Connect(function() Replay.stop() end)

return Replay
