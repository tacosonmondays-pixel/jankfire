--!strict
-- HOUSE HUNT: the hiders' short intro (the owner, 27 Nov 2026: "if you get survivor you get a small cinematic of your
-- character walking scared in the map?.. and then it says survive!! You can skip it!! It'll be short regardless").
-- On each hider's own screen, HC.HIDER_INTRO.len s as the round starts: a copy of their own avatar walking scared up to
-- their spot (Roblox's walk slowed, with the gunman intro's upper-body look round), bars, the gunman intro's muted
-- grade, a heartbeat; then SURVIVE (A's hero type) hits in with the game's own impact and the lens glides back to the
-- game's camera. Skip: Space, B on a pad, a tap. It costs no hiding time: HuntRound adds these seconds to the hide.
-- While it plays their real body is held still and kept off this screen, and every other HUD is off (put back after;
-- HuntClient also stands back while the HuntIntro attribute is set).
-- Server: HuntRound sends Remote "hintro" { len, t0, at = their spot } to each hider.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local SoundService = game:GetService("SoundService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local J = ReplicatedStorage:WaitForChild("Jankfire")
local HC = require(J:WaitForChild("HuntConfig")) :: any
local Cine = require(script.Parent:WaitForChild("CineKit")) :: any
local UiKit: any = nil
pcall(function() UiKit = require(script.Parent:WaitForChild("UiKit", 5) :: ModuleScript) end)
local Sfx: any = nil
pcall(function() Sfx = require(script.Parent:WaitForChild("Sfx", 5) :: ModuleScript) end)
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Hunt") :: RemoteEvent
local me = Players.LocalPlayer

local running: any = nil

local function effectsGroup(): SoundGroup?
	local m = SoundService:FindFirstChild("JankMaster")
	local g = m and m:FindFirstChild("Effects")
	return if g and g:IsA("SoundGroup") then g else nil
end
-- a table is a Roblox library recording { id, vol, speed? }; a string is the game's own library by name (Sfx)
local function sound(e: any, looped: boolean, vol: number?): Sound?
	if type(e) == "string" then
		if Sfx then pcall(Sfx.play, e, nil, vol or 1) end
		return nil
	end
	if type(e) ~= "table" or not e.id then return nil end
	local s = Instance.new("Sound")
	s.Name = "HuntHiderIntroSound"
	s.SoundId = "rbxassetid://" .. tostring(e.id)
	s.Volume = e.vol or 0.5
	s.PlaybackSpeed = e.speed or 1
	s.Looped = looped
	s.SoundGroup = effectsGroup()
	s.Parent = SoundService
	s:Play()
	return s
end

local function stop(skipped: boolean?)
	local r = running
	if not r then return end
	running = nil
	r.alive = false
	if r.conn then r.conn:Disconnect() end
	if r.skip then r.skip:Disconnect() end
	for _, s in r.sounds do
		pcall(function()
			local tw = TweenService:Create(s, TweenInfo.new(if skipped then 0.25 else 1.0), { Volume = 0 })
			tw.Completed:Once(function() s:Destroy() end)
			tw:Play()
		end)
	end
	if r.grade then r.grade:Destroy() end
	if r.gui then r.gui:Destroy() end
	if r.copy then r.copy:Destroy() end
	if r.unbind then pcall(function() RunService:UnbindFromRenderStep("HuntHiderHide") end) end
	for d, v in r.hidden do if d.Parent then (d :: any).LocalTransparencyModifier = v end end
	if r.root and r.root.Parent then
		if r.face then -- (she stands where her copy stopped, facing the way it walked)
			r.root.CFrame = CFrame.lookAt(r.root.Position, r.root.Position + r.face)
		end
		r.root.Anchored = r.wasAnchored
	end
	for g, was in r.guis do if g.Parent then g.Enabled = was end end
	Cine.bars(false, if skipped then 0.2 else 0.4)
	if r.cine then r.cine.stop(true) end -- (onto the game's own camera on their current body)
	me:SetAttribute("HuntIntro", nil)
end

-- a copy of a body: limbs, what they wear, clothes; nothing else (no tools, scripts or names over it)
local LIMBS = { Head = true, HumanoidRootPart = true, UpperTorso = true, LowerTorso = true, Torso = true,
	LeftUpperArm = true, LeftLowerArm = true, LeftHand = true, RightUpperArm = true, RightLowerArm = true, RightHand = true,
	LeftUpperLeg = true, LeftLowerLeg = true, LeftFoot = true, RightUpperLeg = true, RightLowerLeg = true, RightFoot = true,
	["Left Arm"] = true, ["Right Arm"] = true, ["Left Leg"] = true, ["Right Leg"] = true }
local function copyBody(m: Model): Model?
	local was = m.Archivable
	m.Archivable = true
	local ok, c = pcall(function() return m:Clone() end)
	m.Archivable = was
	if not ok or not c then return nil end
	for _, ch in c:GetChildren() do
		local keepIt = ch:IsA("Humanoid") or ch:IsA("Accessory") or ch:IsA("Clothing") or ch:IsA("ShirtGraphic")
			or ch:IsA("BodyColors") or ch:IsA("CharacterMesh") or (ch:IsA("BasePart") and LIMBS[ch.Name])
		if not keepIt then ch:Destroy() end
	end
	for _, d in c:GetDescendants() do
		if d:IsA("Script") or d:IsA("LocalScript") or d:IsA("BillboardGui") then d:Destroy()
		elseif d:IsA("BasePart") then
			d.CanCollide = false; d.CanTouch = false; d.CanQuery = false; d.Anchored = false; d.LocalTransparencyModifier = 0
		end
	end
	local hum = c:FindFirstChildOfClass("Humanoid")
	local root = c:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not hum or not root then c:Destroy(); return nil end
	hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	hum.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
	hum.PlatformStand = true
	root.Anchored = true
	c.Name = "HuntHiderIntroBody"
	return c
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

local function play(a: any)
	stop()
	local HI = HC.HIDER_INTRO
	if type(a) ~= "table" or not HI or not HI.on then return end
	local len = tonumber(a.len) or HI.len or 5
	local t0 = tonumber(a.t0) or workspace:GetServerTimeNow()
	local function T(): number return workspace:GetServerTimeNow() - t0 end
	-- the body the round makes for them (the spawn re-makes it): wait until it stands at their spot
	local at: Vector3? = if typeof(a.at) == "Vector3" then a.at else nil
	local ch: Model? = nil
	while T() < len - 1.5 do
		local c = me.Character
		local rr = c and c:FindFirstChild("HumanoidRootPart") :: BasePart?
		if c and rr and me:GetAttribute("Hunt") == "round" and (not at or (rr.Position - (at :: Vector3)).Magnitude < 12) then ch = c; break end
		task.wait(0.05)
	end
	if not ch or me:GetAttribute("HuntRole") ~= "hider" then return end
	task.wait(0.15) -- (one more beat: the spawn puts the body at its spot, then the round's look settles)
	local root = (ch :: Model):FindFirstChild("HumanoidRootPart") :: BasePart
	local hum = (ch :: Model):FindFirstChildOfClass("Humanoid")
	if not root or not hum then return end
	local rig = if hum.RigType == Enum.HumanoidRigType.R6 then "R6" else "R15"
	local r: any = { alive = true, sounds = {}, guis = {}, hidden = {}, root = root, wasAnchored = root.Anchored }
	running = r
	me:SetAttribute("HuntIntro", "hider")
	root.Anchored = true -- (held still while it plays: the hide gave these seconds back)
	local function hideReal()
		for _, d in (ch :: Model):GetDescendants() do
			if d:IsA("BasePart") or d:IsA("Decal") then
				if r.hidden[d] == nil then r.hidden[d] = (d :: any).LocalTransparencyModifier end
				(d :: any).LocalTransparencyModifier = 1
			end
		end
	end
	hideReal()
	-- (after the game's camera each frame: in first person its own controller would show the body again)
	RunService:BindToRenderStep("HuntHiderHide", Enum.RenderPriority.Last.Value + 90, hideReal)
	r.unbind = true

	-- the copy: a few studs behind their spot (never through a wall), walking scared up to it
	local copy = copyBody(ch :: Model)
	if not copy then stop(); return end
	r.copy = copy
	local spot = root.CFrame
	local flat = Vector3.new(spot.LookVector.X, 0, spot.LookVector.Z)
	flat = if flat.Magnitude > 1e-3 then flat.Unit else Vector3.new(0, 0, -1)
	spot = CFrame.lookAt(spot.Position, spot.Position + flat)
	local rp = RaycastParams.new()
	rp.FilterType = Enum.RaycastFilterType.Exclude
	rp.FilterDescendantsInstances = { ch :: Model, copy }
	-- (v1, 27 Nov: a spot against a sofa left no room to walk and put the lens on top of her) she walks in from the side
	-- with the most room (her own facing preferred), and the lens stands still where it has the most room in front of her
	local function free(at: Vector3, dir: Vector3, far: number): number
		local h = workspace:Raycast(at, dir * far, rp)
		return if h then (h.Position - at).Magnitude else far
	end
	local base = spot.Position
	local walkD, best, room = flat, -1e9, 0
	for i = 0, 15 do
		local a = i * math.pi / 8
		local d = Vector3.new(math.sin(a), 0, math.cos(a)) -- (the way she walks: she comes in from -d)
		local f = math.min(free(base, -d, 10), free(base + Vector3.new(0, 1.5, 0), -d, 10))
		local score = math.min(f, 8) + 1.5 * d:Dot(flat)
		if score > best then walkD, best, room = d, score, f end
	end
	spot = CFrame.lookAt(base, base + walkD)
	r.face = walkD
	local back = math.clamp(room - 1.8, 1.5, HI.walkFrom or 7)
	local from = spot * CFrame.new(0, 0, back)
	local eyeAt = base + Vector3.new(0, 1.2, 0)
	local camD, camBest, camRoom = walkD, -1e9, 0
	for i = -6, 6 do
		local d = CFrame.fromAxisAngle(Vector3.yAxis, math.rad(i * 15)) * walkD
		local f = free(eyeAt, d, 9)
		local score = math.min(f, 7) - math.abs(i) * 0.12
		if score > camBest then camD, camBest, camRoom = d, score, f end
	end
	local camDist = math.clamp(camRoom - 0.8, 2.4, 6.5)
	local camAt = eyeAt + camD * camDist + Vector3.new(0, 0.25, 0)
	local camFov = if camDist < 4 then 62 else 50
	copy:PivotTo(from)
	copy.Parent = workspace
	local walk = track(copy, HC.OUTRO and HC.OUTRO.walk and HC.OUTRO.walk[rig], Enum.AnimationPriority.Action)
	if walk then walk.Looped = true; walk:Play(0.1); walk:AdjustSpeed(HI.walkSpeed or 0.45) end
	local look = track(copy, HC.INTRO.lookAround and HC.INTRO.lookAround[rig], Enum.AnimationPriority.Action2)
	if look then look.Looped = true; look:Play(0.3); look.TimePosition = 1.2; look:AdjustSpeed(0.9) end
	local titleAt = math.max(1.5, len - (HI.title or 1.6))
	local homeAt = len - (HI.home or 0.35)

	-- the lens: still, in front of her where there's room, turning to keep her as she comes; a slow push on the word.
	-- it ends on a cut to the game's camera (v1's glide back swung through her head)
	local function body(): CFrame return copy:GetPivot() end
	local function smooth(u: number): number return u * u * (3 - 2 * u) end
	local function aim(): Vector3 return body().Position + Vector3.new(0, 0.9, 0) end
	local shots = {
		{ name = "walk", t0 = 0, t1 = titleAt, fov = camFov, cam = function() return CFrame.lookAt(camAt, aim()) end },
		{ name = "title", t0 = titleAt, t1 = len, fov = function(u) return camFov - 4 * smooth(u) end,
			cam = function(u)
				local a = aim()
				return CFrame.lookAt(camAt + (a - camAt).Unit * math.max(0, math.min(0.7, camDist - 2.2)) * smooth(u), a)
			end },
	}
	-- the grade (the gunman intro's muted colour), the bars, the heartbeat
	local cam = workspace.CurrentCamera
	local G = HC.INTRO.grade
	if G and cam then
		local cc = Instance.new("ColorCorrectionEffect")
		cc.Name = "HuntHiderIntroGrade"
		cc.Saturation = G.saturation; cc.Contrast = G.contrast; cc.Brightness = G.brightness; cc.TintColor = G.tint
		cc.Parent = cam
		r.grade = cc
	end
	Cine.bars(true, 0.3)
	r.cine = Cine.play(shots, { clock = T, flag = "hunthider" })
	local bed = sound(HI.sounds and HI.sounds.heart, true)
	if bed then table.insert(r.sounds, bed) end

	-- SURVIVE: one word, A's hero type straight on the world, a quick hit in
	local pg = me:FindFirstChildOfClass("PlayerGui")
	local gui = Instance.new("ScreenGui")
	gui.Name = "HuntSurvive"; gui.IgnoreGuiInset = true; gui.DisplayOrder = 46; gui.ResetOnSpawn = false
	gui.Parent = pg
	r.gui = gui
	local vp = if cam then cam.ViewportSize else Vector2.new(1280, 720)
	local size = math.floor(math.clamp(vp.Y * 0.2, 64, 170)) -- (v1's 0.15 read small)
	local holder = Instance.new("Frame")
	holder.Name = "Word"; holder.BackgroundTransparency = 1; holder.AnchorPoint = Vector2.new(0.5, 0.5)
	holder.Position = UDim2.fromScale(0.5, 0.7); holder.Size = UDim2.new(1, 0, 0, size); holder.Visible = false -- (under her face)
	holder.Parent = gui
	local scale = Instance.new("UIScale"); scale.Parent = holder
	local labels: { TextLabel } = {}
	if UiKit and UiKit.hero then
		local h, _, set = UiKit.hero(holder, "Survive", size, UiKit.SANS_HEAVY, UiKit.A.WORLD, true, true)
		set("SURVIVE")
		h.AnchorPoint = Vector2.new(0.5, 0.5); h.Position = UDim2.fromScale(0.5, 0.5)
		for _, d in h:GetChildren() do if d:IsA("TextLabel") then table.insert(labels, d) end end
	else
		local w = Instance.new("TextLabel")
		w.BackgroundTransparency = 1; w.Size = UDim2.fromScale(1, 1); w.Text = "SURVIVE"; w.TextScaled = true
		w.Font = Enum.Font.GothamBlack; w.TextColor3 = Color3.new(1, 1, 1)
		w.Parent = holder
		table.insert(labels, w)
	end
	local rest: { [TextLabel]: number } = {}
	for _, l in labels do rest[l] = l.TextTransparency; l.TextTransparency = 1 end
	-- skip: Space, B, a tap (straight back to the game)
	r.skip = UserInputService.InputBegan:Connect(function(io: InputObject)
		if running ~= r then return end
		if io.KeyCode == Enum.KeyCode.Space or io.KeyCode == Enum.KeyCode.ButtonB or io.UserInputType == Enum.UserInputType.Touch then
			stop(true)
		end
	end)

	local shown, faded = false, false
	r.conn = RunService.RenderStepped:Connect(function()
		if not r.alive then return end
		local t = T()
		-- the screen is the film's: every other HUD off (put back as it was)
		if pg then
			for _, g in pg:GetChildren() do
				if g:IsA("ScreenGui") and g ~= gui and g.Name ~= "CineBars" then
					if r.guis[g] == nil then r.guis[g] = g.Enabled end
					if g.Enabled then g.Enabled = false end
				end
			end
		end
		-- the copy walks up to their spot, slowing to stop on it
		local u = math.clamp(t / math.max(0.5, titleAt + 0.3), 0, 1)
		copy:PivotTo(from:Lerp(spot, 1 - (1 - u) ^ 2))
		if u >= 1 and walk and walk.IsPlaying then walk:Stop(0.35) end
		if not shown and t >= titleAt then
			shown = true
			holder.Visible = true
			scale.Scale = 1.4
			TweenService:Create(scale, TweenInfo.new(0.16, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Scale = 1 }):Play()
			for _, l in labels do TweenService:Create(l, TweenInfo.new(0.1), { TextTransparency = rest[l] }):Play() end
			if r.cine then r.cine.kick(5) end
			sound(HI.sounds and HI.sounds.hit, false, HI.sounds and HI.sounds.hitVol)
		end
		if shown and not faded and t >= homeAt then
			faded = true
			for _, l in labels do TweenService:Create(l, TweenInfo.new(len - homeAt), { TextTransparency = 1 }):Play() end
		end
		if t >= len then stop() end
	end)
end

-- the survivors' role card (owner, 27 Nov: "no cinematic for survivor!! When you load in, it'll tell you survivor!!"):
-- one word in A's hero type, a quick hit in with the game's impact, a hold, a fade; it never stops them moving
local function roleCard()
	local RC = HC.ROLE_CARD
	if not RC or not RC.on then return end
	local w0 = os.clock()
	while (me:GetAttribute("Hunt") ~= "round" or me:GetAttribute("HuntRole") == nil) and os.clock() - w0 < 2 do task.wait(0.05) end
	if me:GetAttribute("Hunt") ~= "round" or me:GetAttribute("HuntRole") ~= "hider" then return end
	task.wait(RC.delay or 0.35)
	local pg = me:FindFirstChildOfClass("PlayerGui")
	if not pg then return end
	local old = pg:FindFirstChild("HuntRoleCard")
	if old then old:Destroy() end
	local gui = Instance.new("ScreenGui")
	gui.Name = "HuntRoleCard"; gui.IgnoreGuiInset = true; gui.DisplayOrder = 46; gui.ResetOnSpawn = false
	gui.Parent = pg
	local cam = workspace.CurrentCamera
	local vp = if cam then cam.ViewportSize else Vector2.new(1280, 720)
	local size = math.floor(math.clamp(vp.Y * 0.17, 60, 150))
	local holder = Instance.new("Frame")
	holder.BackgroundTransparency = 1; holder.AnchorPoint = Vector2.new(0.5, 0.5)
	holder.Position = UDim2.fromScale(0.5, 0.4); holder.Size = UDim2.new(1, 0, 0, size)
	holder.Parent = gui
	local scale = Instance.new("UIScale"); scale.Scale = 1.4; scale.Parent = holder
	local labels: { TextLabel } = {}
	if UiKit and UiKit.hero then
		local h, _, set = UiKit.hero(holder, "Role", size, UiKit.SANS_HEAVY, UiKit.A.WORLD, true, true)
		set(RC.word or "SURVIVOR")
		h.AnchorPoint = Vector2.new(0.5, 0.5); h.Position = UDim2.fromScale(0.5, 0.5)
		for _, d in h:GetChildren() do if d:IsA("TextLabel") then table.insert(labels, d) end end
	else
		local w = Instance.new("TextLabel")
		w.BackgroundTransparency = 1; w.Size = UDim2.fromScale(1, 1); w.Text = RC.word or "SURVIVOR"; w.TextScaled = true
		w.Font = Enum.Font.GothamBlack; w.TextColor3 = Color3.new(1, 1, 1); w.Parent = holder
		table.insert(labels, w)
	end
	local rest: { [TextLabel]: number } = {}
	for _, l in labels do rest[l] = l.TextTransparency; l.TextTransparency = 1 end
	TweenService:Create(scale, TweenInfo.new(0.16, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Scale = 1 }):Play()
	for _, l in labels do TweenService:Create(l, TweenInfo.new(0.1), { TextTransparency = rest[l] }):Play() end
	sound(RC.hit, false, RC.hitVol)
	task.wait((RC.hold or 1.7) + 0.16)
	for _, l in labels do TweenService:Create(l, TweenInfo.new(RC.fade or 0.5), { TextTransparency = 1 }):Play() end
	task.wait((RC.fade or 0.5) + 0.05)
	gui:Destroy()
end

Remote.OnClientEvent:Connect(function(op: string, a: any)
	if op == "round" then
		task.spawn(roleCard)
	elseif op == "hintro" then
		task.spawn(play, a)
	elseif op == "results" or op == "outro" then
		if running then stop(true) end
	end
end)
me:GetAttributeChangedSignal("Hunt"):Connect(function()
	if me:GetAttribute("Hunt") ~= "round" and running then stop(true) end
end)
