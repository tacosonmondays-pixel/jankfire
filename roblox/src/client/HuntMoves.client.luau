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
local Keys = require(script.Parent:WaitForChild("Keys")) :: any -- (27 Nov: the one input path, so the phone's buttons reach the moves)
local Body = require(script.Parent:WaitForChild("Body")) :: any
local Sfx = require(script.Parent:WaitForChild("Sfx")) :: any
local HuntAnims = require(script.Parent:WaitForChild("HuntAnims")) :: any
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Hunt") :: RemoteEvent

local me = Players.LocalPlayer
local camera = workspace.CurrentCamera
local MV, BO = HC.MOVES, HC.BOUNCE
local function serverNow(): number return workspace:GetServerTimeNow() end

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
-- ------------------------------------------------------------------ the ragdoll (owner, 27 Nov: "we need ragdoll mechanic
-- and a button to unragdoll"): the server stands the joints down (HuntRagdoll); this client runs the body's physics
local ragOn = false
local collide: { [BasePart]: boolean } = {}
local rising: AnimationTrack? = nil
local function goLimp(v: Vector3)
	local ch, hum, root = body()
	if not (ch and hum and root) then return end
	ragOn = true
	if lying then lying = false; Body.mini = 1; setSink(0, 0.01) end
	hum:SetStateEnabled(Enum.HumanoidStateType.Physics, true)
	hum:ChangeState(Enum.HumanoidStateType.Physics)
	for _, d in ch:GetDescendants() do
		if d:IsA("BasePart") and d.Name ~= "HuntDisguise" then
			if collide[d] == nil then collide[d] = d.CanCollide end
			d.CanCollide = d ~= root and d.Parent == ch
			d.AssemblyLinearVelocity = v
		end
	end
end
local function getUp()
	local ch, hum = body()
	ragOn = false
	for d, c in collide do if d.Parent then d.CanCollide = c end end
	collide = {}
	if not (ch and hum) then return end
	hum:ChangeState(Enum.HumanoidStateType.GettingUp)
	local RG = HC.RAGDOLL
	local rig = if hum.RigType == Enum.HumanoidRigType.R6 then "R6" else "R15"
	local id = RG and RG.getUp and RG.getUp[rig]
	local an = hum:FindFirstChildOfClass("Animator")
	if id and an then -- (the vault's Getting Up mocap)
		if not (rising and rising.Parent) then
			local a = Instance.new("Animation"); a.AnimationId = "rbxassetid://" .. tostring(id)
			local ok, t = pcall(function() return (an :: Animator):LoadAnimation(a) end)
			rising = if ok then t else nil
			if rising then rising.Priority = Enum.AnimationPriority.Action4; rising.Looped = false end
		end
		if rising then rising:Play(0.05, 1, RG.riseSpeed or 1.8) end
	end
end
Remote.OnClientEvent:Connect(function(op: string, a: any)
	if op ~= "rag" then return end
	if typeof(a) == "Vector3" then goLimp(a) else getUp() end
end)
local function canGetUp(): boolean
	local m = tonumber(me:GetAttribute("HuntRagMin"))
	return ragOn and m ~= nil and serverNow() >= m
end
UIS.JumpRequest:Connect(function()
	if ragOn then
		if canGetUp() then Remote:FireServer("getup") end
		return
	end
	if lying then standUp() end
end)
-- the GET UP key: bottom middle while you're down (dim till it works)
local upGui = Instance.new("ScreenGui")
upGui.Name = "HuntGetUp"; upGui.ResetOnSpawn = false; upGui.DisplayOrder = 30; upGui.Enabled = false
local upBox = Instance.new("Frame")
upBox.AnchorPoint = Vector2.new(0.5, 1); upBox.Position = UDim2.new(0.5, 0, 1, -150); upBox.Size = UDim2.fromOffset(170, 40)
upBox.BackgroundColor3 = Color3.fromRGB(229, 226, 219); upBox.BorderSizePixel = 0; upBox.Parent = upGui
Instance.new("UICorner", upBox).CornerRadius = UDim.new(0, 3)
local upKey = Instance.new("TextLabel")
upKey.BackgroundColor3 = Color3.fromRGB(29, 31, 35); upKey.BorderSizePixel = 0; upKey.Position = UDim2.fromOffset(6, 6)
upKey.Size = UDim2.fromOffset(58, 28); upKey.Font = Enum.Font.GothamBold; upKey.TextSize = 12
upKey.TextColor3 = Color3.fromRGB(229, 226, 219); upKey.Text = "SPACE"; upKey.Parent = upBox
Instance.new("UICorner", upKey).CornerRadius = UDim.new(0, 3)
local upTxt = Instance.new("TextLabel")
upTxt.BackgroundTransparency = 1; upTxt.Position = UDim2.fromOffset(72, 0); upTxt.Size = UDim2.new(1, -78, 1, 0)
upTxt.Font = Enum.Font.GothamBlack; upTxt.TextSize = 16; upTxt.TextColor3 = Color3.fromRGB(29, 31, 35)
upTxt.TextXAlignment = Enum.TextXAlignment.Left; upTxt.Text = "GET UP"; upTxt.Parent = upBox
upGui.Parent = me:WaitForChild("PlayerGui")

-- ------------------------------------------------------------------ punch and push
local punchDown, punchT = false, 0
local pushDown, pushT = false, 0
local nextPunch, nextPush, nextSuper, nextAny = 0, 0, 0, 0
local function punchReady(): boolean
	local cd = tonumber(me:GetAttribute("HuntCd_punch")) or 0
	return os.clock() >= nextPunch and serverNow() >= cd
end
local function windPose(hum: Humanoid)
	local t = HuntAnims.track(hum, "haymaker")
	if t then t:Play(0.08, 1, 1) end
end
Keys.began(function(io: any, gp: boolean)
	if gp or not inMode() or menuUp() or ragOn then return end
	local _, hum = body()
	if not hum then return end
	if Binds.is("fire", io) then
		if not punchReady() or os.clock() < nextAny or punchDown then return end
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
Keys.ended(function(io: any)
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
			nextPunch = os.clock() + (if me:GetAttribute("HuntWeapon") then MV.jab.cd else MV.punch.whiff)
			nextAny = os.clock() + MV.lock
			Sfx.play("swing", nil, 0.5)
		else
			if hay then hay:AdjustSpeed(1.25) end
			Remote:FireServer("hay", look())
			nextPunch = os.clock() + (if me:GetAttribute("HuntWeapon") then MV.hay.cd else MV.punch.whiff)
			nextAny = os.clock() + MV.lock
			Sfx.play("swing", nil, 0.8)
		end
	elseif Binds.is("grapple", io) and pushDown then
		pushDown = false
		if not hum or not inMode() then return end
		local held = os.clock() - pushT
		local super = held >= MV.super.hold and os.clock() >= nextSuper
		if os.clock() < nextAny or ragOn then return end
		if not super and os.clock() < nextPush then return end
		if not lying then local s = HuntAnims.track(hum, "shove"); if s then s:Play(0.05, 1, if super then 0.85 else 1.1) end end
		Remote:FireServer(if super then "super" else "push", look())
		nextPush = os.clock() + MV.push.cd
		nextAny = os.clock() + MV.lock
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
	if ragOn then
		if hum:GetState() ~= Enum.HumanoidStateType.Physics then hum:ChangeState(Enum.HumanoidStateType.Physics) end
		if me:GetAttribute("HuntRag") == nil then getUp() end -- (the server let you up and its word got lost)
	end
	upGui.Enabled = ragOn
	if ragOn then
		local ok = canGetUp()
		upBox.BackgroundTransparency = if ok then 0 else 0.45
		upTxt.TextTransparency = if ok then 0 else 0.45
		local pad = UIS:GetLastInputType().Name:find("Gamepad") ~= nil
		upKey.Text = if UIS.TouchEnabled and not UIS.KeyboardEnabled then "JUMP" elseif pad then "A" else "SPACE"
	end
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
