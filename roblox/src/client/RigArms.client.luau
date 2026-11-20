--!strict
-- the Overdrive Rig's forearms in first person (the hold session, 19 Nov 2026; the gadget is weapons-port's, plan
-- overdrive-gadget-plan.md in main's notes; the model is gun-models' w_rig_arms, docs/GUN-MODELS.md). while your Rig
-- attribute is set the two giant forearms fill the bottom of the screen in place of what you hold (the gun and your own
-- arms are hidden: inside the rig they are its arms). poses after the web's rigarms.js:
--   at rest low left / right, knuckles forward, the forearms running back out of the bottom corners; a breath, a
--   cheap servo's twitch now and then, the arms lag your mouse and pump when you run
--   the punch's wind-up (RigClient.charge): the right fist drawn back and up, shaking harder the more it's charged,
--   its glow strip going white-hot; the punch (RigClient.punched): snapped out from wherever the wind-up left it
--   the salvo (RigClient.fired): both arms kick; the rack's loaded noses (ammoL) gone until it's ready again (5 s)
--   suiting up: they come up from below; powering down: they drop away
-- third person (yours and everyone's) is ThirdPerson's: the forearms over the body's own. bound after Arsenal (which
-- runs at Camera + 2 and shows the gun), so the gun stays hidden the same frame.
-- Studio tuning: this script's attributes Scale (model size, x the game's 3 studs a metre), RestP / RestR (the rest pose,
-- camera metres / radians for the right arm; the left is its mirror), Unit (camera metres to studs, x 3)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local VM = require(script.Parent:WaitForChild("Viewmodel")) :: any
local TP = require(script.Parent:WaitForChild("ThirdPerson")) :: any
local RigClient: any = nil -- (weapons-port's: required once it's in the place)

local me = Players.LocalPlayer
local S = Weapons.S
local CF, V = CFrame.new, Vector3.new

-- the model's elbows (file metres; RigKit.ELBOW), where each arm turns
local ELBOW = { r = V(0.3, 0, 0.35), l = V(-0.3, 0, 0.35) }
local MISS_READY = 5 -- (s: the rack's reload, Rig.server's)

-- the pose (the web's REST and SCALE: its forearm 0.64 to the wrist at 0.78, ours is 0.70 long)
local P = {
	scale = 0.72, -- studs a model metre / 3
	unit = 1.0, -- studs a camera metre / 3
	restP = V(0.36, -0.33, -0.1), -- the right elbow, camera metres
	restR = V(0.26, 0.26, 0.14), -- its turn (YXZ, radians): fist up, in toward the middle, rolled in
}
-- the web's clips (anim.js rig_*): keys { t, p, r, ease }; arm "r" / "l" / "both" (both: x, ry, rz mirrored on the left)
type Key = { t: number, p: Vector3, r: Vector3, e: string }
local function K(t: number, p: { number }?, r: { number }?, e: string?): Key
	local pp, rr = p or { 0, 0, 0 }, r or { 0, 0, 0 }
	return { t = t, p = V(pp[1], pp[2], pp[3]), r = V(rr[1], rr[2], rr[3]), e = e or "smooth" }
end
local CLIPS: { [string]: { arm: string, keys: { Key } } } = {
	rig_on = { arm = "both", keys = { K(0, { 0.12, -0.6, 0.3 }, { 1.0, 0, 0 }), K(0.34, { 0, 0.035, 0 }, { -0.1, 0, 0 }, "back"), K(0.55) } },
	rig_off = { arm = "both", keys = { K(0), K(0.45, { 0.12, -0.65, 0.3 }, { 1.0, 0, 0 }, "in") } },
	rig_punch = { arm = "r", keys = { K(0), K(0.05, { -0.18, 0.05, -0.14 }, { -0.23, 0.05, -0.22 }, "snap"), K(0.28, { -0.18, 0.05, -0.17 }, { -0.23, 0.05, -0.22 }), K(0.55) } },
	rig_miss = { arm = "both", keys = { K(0), K(0.06, { 0, -0.05, 0.05 }, { 0.14, 0, 0 }, "snap"), K(0.32) } },
}
local EASE: { [string]: (number) -> number } = {
	linear = function(u) return u end,
	smooth = function(u) return u * u * (3 - 2 * u) end,
	snap = function(u) return 1 - (1 - u) ^ 3 end,
	["in"] = function(u) return u * u * u end,
	back = function(u) local c = 1.9; return 1 + (c + 1) * (u - 1) ^ 3 + c * (u - 1) ^ 2 end,
}
local function sample(name: string, t: number): (Vector3?, Vector3?)
	local keys = CLIPS[name].keys
	if t >= keys[#keys].t then return nil, nil end
	local i = 1
	while i < #keys - 1 and t >= keys[i + 1].t do i += 1 end
	local k0, k1 = keys[i], keys[i + 1]
	local u = math.clamp((t - k0.t) / math.max(1e-6, k1.t - k0.t), 0, 1)
	local e = (EASE[k1.e] or EASE.smooth)(u)
	return k0.p:Lerp(k1.p, e), k0.r:Lerp(k1.r, e)
end
local function R(x: number): number return (math.random() * 2 - 1) * x end

-- ------------------------------------------------------------------ the model (RigKit: the kit template in file metres)
type Piece = { part: BasePart, side: string, q: Vector3, rot: CFrame, ammo: boolean, glow: Color3? }
local built: { model: Model, pieces: { Piece }, scale: number }? = nil

local function build(scale: number)
	if built then built.model:Destroy(); built = nil end
	local Kit = Shared:FindFirstChild("RigKit")
	local list = Kit and (require(Kit :: ModuleScript) :: any).pieces()
	if not list then return end
	local m = Instance.new("Model")
	m.Name = "RigArms"
	local pieces: { Piece } = {}
	for _, pc in list do
		local d = (require(Kit :: ModuleScript) :: any).make(pc, S * scale) :: BasePart
		d.Anchored = true
		table.insert(pieces, { part = d, side = pc.side, q = pc.q - ELBOW[pc.side], rot = pc.rot, ammo = pc.node == "ammol", glow = if pc.glow then d.Color else nil })
		d.Parent = m
	end
	built = { model = m, pieces = pieces, scale = scale }
end

-- ------------------------------------------------------------------ the pose
type Arm = { s: number, twitch: Vector3, twitchR: number, twitchT: number }
local arms: { r: Arm, l: Arm } = {
	r = { s = 1, twitch = Vector3.zero, twitchR = 0, twitchT = 0 },
	l = { s = -1, twitch = Vector3.zero, twitchR = 0, twitchT = 0 },
}
local clips: { { name: string, t: number } } = {}
local function play(name: string)
	for i = #clips, 1, -1 do if clips[i].name == name then table.remove(clips, i) end end
	table.insert(clips, { name = name, t = 0 })
end
local was = false -- (rigged last frame)
local lastPunch, lastFire = math.huge, math.huge
local cw, ck = 0, 0 -- (the wind-up's weight and its charge)
local chargeP, chargeR = Vector3.zero, Vector3.zero -- (where the wind-up has the right arm: the punch starts there)
local punchFrom: { p: Vector3, r: Vector3 }? = nil
local swayX, swayY, lastYaw, lastPitch = 0, 0, nil :: number?, 0
local phase = 0
local clock = 0

local function attr(name: string, default: any): any
	local v = script:GetAttribute(name)
	return if typeof(v) == typeof(default) then v else default
end

local function hideGun()
	local m = VM.model
	if not m then return end
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then d.LocalTransparencyModifier = 1
		elseif d:IsA("SpotLight") then d.Enabled = false end
	end
end

local function step(dt: number)
	if not RigClient then
		local mod = script.Parent:FindFirstChild("RigClient")
		if not mod then return end
		RigClient = require(mod :: ModuleScript)
	end
	clock += dt
	local camera = workspace.CurrentCamera
	local on = RigClient.on() == true
	if on and not was then play("rig_on"); lastPunch, lastFire = RigClient.punched() or math.huge, RigClient.fired() or math.huge end
	if was and not on then play("rig_off") end
	was = on
	local leaving = false
	for _, c in clips do if c.name == "rig_off" then leaving = true end end
	local show = (on or leaving) and not TP.thirdPerson()
	local ch = me.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	if not show or not hum or hum.Health <= 0 then
		if built and built.model.Parent then built.model.Parent = nil end
		clips = {}
		return
	end
	local scale = attr("Scale", P.scale)
	if not built or built.scale ~= scale then build(scale) end
	local B = built
	if not B then return end
	if B.model.Parent ~= camera then B.model.Parent = camera end
	hideGun()
	-- what happened: a new punch, a new salvo (the seconds since went down)
	local pt, ft = RigClient.punched(), RigClient.fired()
	if pt and pt < lastPunch then play("rig_punch"); punchFrom = { p = chargeP, r = chargeR } end
	if ft and ft < lastFire then play("rig_miss") end
	lastPunch, lastFire = pt or math.huge, ft or math.huge
	for i = #clips, 1, -1 do
		local c = clips[i]
		c.t += dt
		local keys = CLIPS[c.name].keys
		if c.t >= keys[#keys].t then table.remove(clips, i) end
	end
	-- the mouse lag (the web's: half the look's turn this frame, capped, eased) and the run's pump
	local look = camera.CFrame.LookVector
	local yaw, pitch = math.atan2(-look.X, -look.Z), math.asin(math.clamp(look.Y, -1, 1))
	local dy = if lastYaw then yaw - lastYaw else 0
	if dy > math.pi then dy -= 2 * math.pi elseif dy < -math.pi then dy += 2 * math.pi end
	local dp = pitch - lastPitch
	lastYaw, lastPitch = yaw, pitch
	local f60 = 1 / math.max(dt * 60, 1e-3) -- (per 60th of a second, so the lag is the same at any frame rate)
	swayX += (math.clamp(dy * 0.5 * f60, -0.08, 0.08) - swayX) * math.min(1, dt * 7)
	swayY += (math.clamp(dp * 0.5 * f60, -0.08, 0.08) - swayY) * math.min(1, dt * 7)
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local vel = if root then root.AssemblyLinearVelocity else Vector3.zero
	local spd = V(vel.X, 0, vel.Z).Magnitude
	local run = if hum.FloorMaterial ~= Enum.Material.Air then math.clamp(spd / 22, 0, 1) else 0
	phase += spd * dt / 9 -- (one swing of each arm a stride or so)
	-- the wind-up
	ck = RigClient.charge()
	cw += ((if ck > 0 then 1 else 0) - cw) * math.min(1, dt * 14)
	local unit = S * attr("Unit", P.unit)
	local restP, restR = attr("RestP", P.restP), attr("RestR", P.restR)
	local cam = camera.CFrame
	local cfs: { CFrame } = table.create(#B.pieces)
	local parts: { BasePart } = table.create(#B.pieces)
	local elbows: { [string]: CFrame } = {}
	for side, A in arms do
		local s, isR = A.s, side == "r"
		A.twitchT -= dt
		if A.twitchT <= 0 then A.twitchT = 0.7 + math.random() * 1.6; A.twitch = V(R(0.008), R(0.006), 0); A.twitchR = R(0.03) end
		local p = V(restP.X * s, restP.Y, restP.Z)
		local r = V(restR.X, restR.Y * s, restR.Z * s)
		local br = clock * 1.4 + (if isR then 0 else 1.7)
		p += V(math.sin(br) * 0.004 + swayX * 0.22, math.sin(br * 1.3) * 0.004 - swayY * 0.14, 0) + A.twitch
		r += V(0, 0, A.twitchR + swayX * 0.6 * s)
		local pump = math.sin(phase * math.pi * 2 + (if isR then 0 else math.pi)) * run
		p += V(0, math.abs(pump) * 0.012, pump * 0.06); r += V(pump * 0.12, 0, 0)
		if isR then
			if cw > 0.01 then
				local j = ck * ck * 0.014
				chargeP = V(0.05 + R(j), -0.05 - ck * 0.02 + R(j), 0.1 + ck * 0.04 + R(j)) * cw
				chargeR = V(0.08 + ck * 0.06 + R(j * 6), 0.1 + ck * 0.05, 0.3 + ck * 0.1 + R(j * 6)) * cw
				p += chargeP; r += chargeR
			else
				chargeP, chargeR = Vector3.zero, Vector3.zero
			end
			if punchFrom then -- (the punch starts from where the wind-up left the fist)
				local pc
				for _, c in clips do if c.name == "rig_punch" then pc = c end end
				local kk = if pc then math.max(0, 1 - pc.t / 0.06) else 0
				if kk <= 0 then punchFrom = nil else p += punchFrom.p * kk; r += punchFrom.r * kk end
			end
		end
		for _, c in clips do
			local arm = CLIPS[c.name].arm
			if arm ~= "both" and (arm == "r") ~= isR then continue end
			local cp, cr = sample(c.name, c.t)
			if cp and cr then
				local m = if arm == "both" then s else 1
				p += V(cp.X * m, cp.Y, cp.Z); r += V(cr.X, cr.Y * m, cr.Z * m)
			end
		end
		elbows[side] = cam * CF(p * unit) * CFrame.fromEulerAnglesYXZ(r.X, r.Y, r.Z)
	end
	-- the glow strips: dull at rest, white-hot with the charge, a flash on the punch
	local pc
	for _, c in clips do if c.name == "rig_punch" then pc = c end end
	local g = math.max(ck * cw, if pc then math.max(0, 1 - pc.t / 0.4) else 0)
	local k = S * scale
	local ammoOut = lastFire < MISS_READY
	for _, pc2 in B.pieces do
		table.insert(parts, pc2.part)
		table.insert(cfs, elbows[pc2.side] * CF(pc2.q * k) * pc2.rot)
		if pc2.ammo then pc2.part.LocalTransparencyModifier = if ammoOut then 1 else 0 end
		if pc2.glow and pc2.side == "r" then pc2.part.Color = (pc2.glow :: Color3):Lerp(Color3.new(1, 0.92, 1), g) end
	end
	workspace:BulkMoveTo(parts, cfs, Enum.BulkMoveMode.FireCFrameChanged)
end

local warned = false
RunService:BindToRenderStep("JankfireRigArms", Enum.RenderPriority.Camera.Value + 3, function(dt: number)
	local ok, err = pcall(step, dt)
	if not ok and not warned then warned = true; warn("[jankfire] rig arms: " .. tostring(err)) end
end)
