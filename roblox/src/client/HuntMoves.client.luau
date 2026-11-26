--!strict
-- HOLDOUT's moves, your side (26 Nov 2026; roblox/docs/HUNT.md section 4). Awake while your Hunt attribute is set
-- (the house, a round as a hider). The keys are the game's own binds, free in this mode (no weapons, no grapple):
--   FIRE (click / RT)          tap: a jab. hold: the wind-up (the haymaker waits at its wind-up), let go: the haymaker
--   GRAPPLE (E / RB)           tap: a shove. hold 0.8 s: a super shove
--   AUTO GRAPPLE (X / D-Right) lie down on your back / get up (Space gets you up too). a push from your back goes
--                              along your whole look: look up at someone over you and they fly
-- The server judges every hit (server/HuntMoves). Also here: the trampoline and the bouncy beds (a part with the
-- attribute Trampoline: land on it, go back up; Space as you land goes higher, up to a cap), and the mode's own idle and
-- run (HuntAnims).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")

local HC = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("HuntConfig")) :: any
local Binds = require(script.Parent:WaitForChild("Binds")) :: any
local Body = require(script.Parent:WaitForChild("Body")) :: any
local Sfx = require(script.Parent:WaitForChild("Sfx")) :: any
local HuntAnims = require(script.Parent:WaitForChild("HuntAnims")) :: any
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Hunt") :: RemoteEvent

local me = Players.LocalPlayer
local camera = workspace.CurrentCamera
local MV, BO = HC.MOVES, HC.BOUNCE

local function body(): (Model?, Humanoid?, BasePart?)
	local ch = me.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not (ch and hum and root) or hum.Health <= 0 then return nil, nil, nil end
	return ch, hum, root
end
local function inMode(): boolean
	return me:GetAttribute("Hunt") ~= nil and me:GetAttribute("HuntRole") ~= "gunman"
end
local function menuUp(): boolean
	return me:GetAttribute("LoadoutOpen") ~= nil or me:GetAttribute("MiniGame") ~= nil
end
local function look(): Vector3 return camera.CFrame.LookVector end

-- ------------------------------------------------------------------ the mode's idle and run
local animOn = false
local function syncLocomotion()
	local ch = me.Character
	local want = inMode() and ch ~= nil
	if want == animOn then return end
	animOn = want
	if ch then HuntAnims.locomotion(ch, want) end
end
me:GetAttributeChangedSignal("Hunt"):Connect(syncLocomotion)
me:GetAttributeChangedSignal("HuntRole"):Connect(syncLocomotion)
me.CharacterAdded:Connect(function() animOn = false; task.wait(0.5); syncLocomotion() end)

-- ------------------------------------------------------------------ lying down
local lying = false
local sinkTo, sinkFrom, sinkT0, sinkDur = 0, 0, 0, 0.01
local function setSink(to: number, dur: number)
	sinkFrom, sinkTo, sinkT0, sinkDur = (Body.sink or 0), to, os.clock(), math.max(0.01, dur)
end
local function stopTrack(hum: Humanoid, name: string, fade: number?)
	local t = HuntAnims.track(hum, name)
	if t and t.IsPlaying then t:Stop(fade or 0.15) end
end
local function standUp()
	if not lying then return end
	lying = false
	Remote:FireServer("lie", false)
	Body.mini = 1
	setSink(0, MV.lie.getUp)
	local _, hum = body()
	if hum then
		stopTrack(hum, "lying", 0.1)
		local t = HuntAnims.track(hum, "liedown")
		if t then -- (the fall played backwards: up off your back)
			t:Play(0.05, 1, 0)
			t.TimePosition = math.max(0, t.Length - 0.02)
			t:AdjustSpeed(-1.5)
			task.delay(t.Length / 1.5, function() if t.IsPlaying then t:Stop(0.15) end end)
		end
	end
end
local function lieDown()
	local _, hum = body()
	if lying or not hum then return end
	lying = true
	Remote:FireServer("lie", true)
	Body.mini = MV.lie.speed
	-- the body sinks till the root's bottom is on the floor (R15: its HipHeight; R6 keeps its legs' height)
	local base = if hum.RigType == Enum.HumanoidRigType.R15 then math.max(0, hum.HipHeight - 0.05 + (Body.sink or 0)) else 0
	local t = HuntAnims.track(hum, "liedown")
	local dur = if t then math.max(0.3, t.Length) else 0.5
	setSink(base, dur * 0.8)
	if t then
		t:Play(0.1, 1, 1)
		task.delay(math.max(0, dur - 0.08), function()
			if not lying then return end
			local lt = HuntAnims.track(hum, "lying")
			if lt then lt:Play(0.08) end
		end)
	end
end
UIS.JumpRequest:Connect(function() if lying then standUp() end end)

-- ------------------------------------------------------------------ punch and push
local punchDown, punchT = false, 0
local pushDown, pushT = false, 0
local nextPunch, nextPush, nextSuper = 0, 0, 0
local function windPose(hum: Humanoid)
	local t = HuntAnims.track(hum, "haymaker")
	if t then t:Play(0.08, 1, 1) end
end
UIS.InputBegan:Connect(function(io: InputObject, gp: boolean)
	if gp or not inMode() or menuUp() then return end
	local _, hum = body()
	if not hum then return end
	if Binds.is("fire", io) then
		if os.clock() < nextPunch or punchDown then return end
		punchDown, punchT = true, os.clock()
		Remote:FireServer("wind")
		if not lying then windPose(hum) end
	elseif Binds.is("grapple", io) then
		if pushDown then return end
		pushDown, pushT = true, os.clock()
		Remote:FireServer("hold")
	elseif Binds.is("reel", io) then
		if lying then standUp() else lieDown() end
	end
end)
UIS.InputEnded:Connect(function(io: InputObject)
	local _, hum = body()
	if Binds.is("fire", io) and punchDown then
		punchDown = false
		if not hum or not inMode() then return end
		local held = os.clock() - punchT
		local hay = HuntAnims.track(hum, "haymaker")
		if held < MV.hay.wind then
			if hay and hay.IsPlaying then hay:Stop(0.08) end
			if not lying then local j = HuntAnims.track(hum, "jab"); if j then j:Play(0.05, 1, 1.2) end end
			Remote:FireServer("jab", look())
			nextPunch = os.clock() + MV.jab.cd
			Sfx.play("swing", nil, 0.5)
		else
			if hay then hay:AdjustSpeed(1.25) end
			Remote:FireServer("hay", look())
			nextPunch = os.clock() + MV.hay.cd
			Sfx.play("swing", nil, 0.8)
		end
	elseif Binds.is("grapple", io) and pushDown then
		pushDown = false
		if not hum or not inMode() then return end
		local held = os.clock() - pushT
		local super = held >= MV.super.hold and os.clock() >= nextSuper
		if not super and os.clock() < nextPush then return end
		if not lying then local s = HuntAnims.track(hum, "shove"); if s then s:Play(0.05, 1, if super then 0.85 else 1.1) end end
		Remote:FireServer(if super then "super" else "push", look())
		nextPush = os.clock() + MV.push.cd
		if super then nextSuper = os.clock() + MV.super.cd end
		Sfx.play("hunt_shove", nil, if super then 1 else 0.6)
	end
end)

-- ------------------------------------------------------------------ every frame: the wind-up's hold, the sink, bounces
local ray = RaycastParams.new()
ray.FilterType = Enum.RaycastFilterType.Exclude
local wasAir, lastBounce, airMinVy = false, 0, 0
RunService.Heartbeat:Connect(function()
	local ch, hum, root = body()
	-- the sink eases (Move.client lowers HipHeight by Body.sink)
	local a = math.clamp((os.clock() - sinkT0) / sinkDur, 0, 1)
	a = a * a * (3 - 2 * a)
	Body.sink = sinkFrom + (sinkTo - sinkFrom) * a
	if not (ch and hum and root) then
		if lying then lying = false; Body.mini = 1; Body.sink = 0; sinkTo = 0 end
		return
	end
	if lying and not inMode() then standUp() end
	-- the haymaker waits at the end of its wind-up while the button is held
	if punchDown then
		local hay = HuntAnims.track(hum, "haymaker")
		if hay and hay.IsPlaying and hay.TimePosition >= (HC.ANIMS.windAt or 0.53) and hay.Speed > 0 then hay:AdjustSpeed(0) end
	end
	-- the trampoline (any body, in the mode or not: it's a trampoline)
	local vy = root.AssemblyLinearVelocity.Y
	local air = hum.FloorMaterial == Enum.Material.Air
	if air then airMinVy = math.min(airMinVy, vy) end
	if not air and os.clock() - lastBounce > BO.gap then
		ray.FilterDescendantsInstances = { ch }
		local hit = workspace:Raycast(root.Position, Vector3.new(0, -(hum.HipHeight + root.Size.Y / 2 + 1.6), 0), ray)
		local pw = hit and hit.Instance:GetAttribute("Trampoline")
		if type(pw) == "number" and pw > 0 and not lying then
			local fall = math.max(0, -airMinVy)
			local up = math.max(BO.base * pw, fall * BO.keep)
			if UIS:IsKeyDown(Enum.KeyCode.Space) or hum.Jump then up += BO.boost * pw end
			up = math.min(up, BO.max * pw)
			local v = root.AssemblyLinearVelocity
			Body.throw(Vector3.new(v.X, up, v.Z))
			hum:ChangeState(Enum.HumanoidStateType.Freefall)
			lastBounce = os.clock()
			Sfx.play("hunt_bounce", nil, math.clamp(up / 60, 0.4, 1))
		end
	end
	if not air then airMinVy = 0 end
	wasAir = air
end)
