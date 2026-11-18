--!strict
-- BOXING, your side (shared/MiniGames.luau MG.BOX; server/MiniBox runs the bout). MiniGames.client calls this.
--   world: every client moves both boxers in the ring from their "<side>_act" (what each is doing since when) and plays
--          the bout's sounds from Ev. an R15 body plays the Mixamo clips in MG.BOX.CLIPS; an R6 body, or any move with
--          no clip yet, is posed by code (POSES below: each joint's turn in its parent part's frame, so the same table
--          poses R15 and R6). a landed big punch stops both bodies for a beat (hit-stop); a perfect dodge slows the
--          world for a moment
--   your screen: both boxers' health and stamina, the round and its clock, the other one's punch as it winds up (its
--          name and the side a hook comes from, filling to the moment it lands), PERFECT / COUNTER, knockdowns, the
--          result; alone, three bot buttons; after a bout, AGAIN. the camera: a low side-on shot from your right, your
--          boxer on the left of the screen
--   keys: left click JAB, right click HOOK, E UPPERCUT, hold S with a punch for a BODY blow, F (hold) BLOCK, C or Ctrl
--         DUCK, Q / R WEAVE left / right. a pad: RT jab, RB hook, Y uppercut, X body, LT (hold) block, A duck, the D-pad
--         or a flick of the left stick weaves, B leaves. a phone: the buttons on screen
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local TweenService = game:GetService("TweenService")
local MG = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("MiniGames")) :: any

local M = {}
local me = Players.LocalPlayer
local L = MG.L.box
local BX = MG.BOX
local ATTACK = { jab = true, hook = true, upper = true, body = true, feint = true }
local function now(): number return workspace:GetServerTimeNow() end
local function other(s: string): string return if s == "A" then "B" else "A" end

-- ------------------------------------------------------------------ the world's clock (slow-mo, hit-stop)
-- visual time: runs at `speed` (1, or slower for a perfect dodge's beat; 0 in a hit-stop), so poses and clips slow
-- together. game time (the server's) never stops: a pose catches up after the beat
local VT = { t = 0, speed = 1, slowUntil = 0, stopUntil = 0 }
local function vnow(): number return VT.t end
local function slowmo(len: number) VT.slowUntil = os.clock() + len end
local function hitstop(len: number) VT.stopUntil = math.max(VT.stopUntil, os.clock() + len) end
-- (Studio test only, MiniTest "box:hold:<s>": your next perfect dodge freezes for s seconds, the ring and the PERFECT
-- line held, and the autopilot's counter skipped, so a screen capture can catch the moment. the real beat is 0.4 s)
local HOLD = { pending = 0, ev = "", len = 0, untilT = 0 }
local function holdFor(e: string): number
	if HOLD.ev == e then return HOLD.len end
	if HOLD.pending <= 0 then return 0 end
	HOLD.ev = e; HOLD.len = HOLD.pending; HOLD.pending = 0; HOLD.untilT = os.clock() + HOLD.len
	return HOLD.len
end
RunService.RenderStepped:Connect(function(dt: number)
	local s = 1
	if os.clock() < VT.stopUntil then s = 0
	elseif os.clock() < VT.slowUntil then s = 0.3 end
	VT.speed = s
	VT.t += dt * s
end)

-- ------------------------------------------------------------------ poses (degrees, each joint in its parent's frame)
-- logical joints: rs re ls le (shoulders, elbows), waist, neck, rh rk lh lk (hips, knees), root (a turn of the whole
-- body) and off (the body moved, studs). an orthodox stance: the left hand leads
type Pose = { [string]: any }
local GUARD: Pose = { rs = { 55, 0, 12 }, re = { 108, 0, 0 }, ls = { 62, 0, -12 }, le = { 100, 0, 0 }, waist = { -6, -14, 0 },
	neck = { 0, 12, 0 }, rh = { 14, 0, 4 }, rk = { -22, 0, 0 }, lh = { -4, 0, -4 }, lk = { -12, 0, 0 }, root = { 0, 0, 0 }, off = { 0, 0, 0 } }
local function with(base: Pose, t: Pose): Pose
	local o = table.clone(base)
	for k, v in t do o[k] = v end
	return o
end
local CROUCH = { rh = { 40, 0, 4 }, rk = { -62, 0, 0 }, lh = { 30, 0, -4 }, lk = { -52, 0, 0 } }
local POSES: { [string]: Pose } = {
	guard = GUARD,
	jab_c = with(GUARD, { ls = { 52, 0, -10 }, le = { 122, 0, 0 }, waist = { -6, -20, 0 } }),
	jab_s = with(GUARD, { ls = { 90, 0, -3 }, le = { 4, 0, 0 }, waist = { -4, 16, 0 }, neck = { 0, -6, 0 } }),
	hookR_c = with(GUARD, { rs = { 0, -10, 72 }, re = { 100, 0, 0 }, waist = { -6, -32, 0 } }),
	hookR_s = with(GUARD, { rs = { 0, 58, 86 }, re = { 92, 0, 0 }, waist = { -4, 36, 0 }, neck = { 0, -14, 0 } }),
	hookL_c = with(GUARD, { ls = { 0, 10, -72 }, le = { 100, 0, 0 }, waist = { -6, 10, 0 } }),
	hookL_s = with(GUARD, { ls = { 0, -58, -86 }, le = { 92, 0, 0 }, waist = { -4, -34, 0 }, neck = { 0, 12, 0 } }),
	upper_c = with(with(GUARD, CROUCH), { rs = { 18, 0, 16 }, re = { 112, 0, 0 }, waist = { -16, -22, 0 }, off = { 0, -0.45, 0 } }),
	upper_s = with(GUARD, { rs = { 122, 0, 8 }, re = { 78, 0, 0 }, waist = { 8, 20, 0 }, neck = { -10, 0, 0 }, off = { 0, 0.08, 0 } }),
	body_c = with(with(GUARD, CROUCH), { rs = { 40, 0, 16 }, re = { 112, 0, 0 }, waist = { -12, -22, 0 }, off = { 0, -0.5, 0 } }),
	body_s = with(with(GUARD, CROUCH), { rs = { 66, 0, 4 }, re = { 10, 0, 0 }, waist = { -26, 20, 0 }, off = { 0, -0.6, -0.15 } }),
	block = with(GUARD, { rs = { 76, 0, 8 }, re = { 138, 0, 0 }, ls = { 76, 0, -8 }, le = { 138, 0, 0 }, waist = { -12, -4, 0 }, neck = { -8, 0, 0 } }),
	duck = with(with(GUARD, CROUCH), { waist = { -32, -8, 0 }, rh = { 66, 0, 4 }, rk = { -96, 0, 0 }, lh = { 62, 0, -4 }, lk = { -92, 0, 0 }, off = { 0, -1.05, 0 } }),
	weaveL = with(with(GUARD, CROUCH), { waist = { -20, -6, 26 }, off = { -0.65, -0.6, 0 } }),
	weaveR = with(with(GUARD, CROUCH), { waist = { -20, -16, -26 }, off = { 0.65, -0.6, 0 } }),
	hit = with(GUARD, { rs = { 34, 0, 22 }, re = { 72, 0, 0 }, ls = { 34, 0, -22 }, le = { 72, 0, 0 }, waist = { 16, 0, 0 }, neck = { 26, 0, 0 }, off = { 0, 0, 0.35 } }),
	hitL = with(GUARD, { rs = { 34, 0, 22 }, re = { 72, 0, 0 }, ls = { 34, 0, -22 }, le = { 72, 0, 0 }, waist = { 10, 0, -16 }, neck = { 10, 0, -22 }, off = { 0.3, 0, 0.2 } }),
	hitR = with(GUARD, { rs = { 34, 0, 22 }, re = { 72, 0, 0 }, ls = { 34, 0, -22 }, le = { 72, 0, 0 }, waist = { 10, 0, 16 }, neck = { 10, 0, 22 }, off = { -0.3, 0, 0.2 } }),
	hitB = with(with(GUARD, CROUCH), { rs = { 42, 0, 6 }, re = { 122, 0, 0 }, ls = { 42, 0, -6 }, le = { 122, 0, 0 }, waist = { -30, 0, 0 }, neck = { -10, 0, 0 }, off = { 0, -0.35, 0.2 } }),
	open = with(GUARD, { rs = { 20, 0, 26 }, re = { 40, 0, 0 }, ls = { 30, 0, -30 }, le = { 50, 0, 0 }, waist = { -18, 26, 10 }, off = { 0, -0.2, 0 } }),
	down = with(GUARD, { rs = { 10, 0, 70 }, re = { 20, 0, 0 }, ls = { 10, 0, -70 }, le = { 20, 0, 0 }, waist = { 6, 0, 0 }, neck = { 14, 0, 0 },
		rh = { 30, 0, 6 }, rk = { -40, 0, 0 }, lh = { 10, 0, -6 }, lk = { -20, 0, 0 }, root = { 82, 0, 0 }, off = { 0, -2.15, 1.3 } }),
}
local JOINTS = {
	R15 = { rs = { "RightUpperArm", "RightShoulder" }, re = { "RightLowerArm", "RightElbow" }, ls = { "LeftUpperArm", "LeftShoulder" },
		le = { "LeftLowerArm", "LeftElbow" }, waist = { "UpperTorso", "Waist" }, neck = { "Head", "Neck" }, rh = { "RightUpperLeg", "RightHip" },
		rk = { "RightLowerLeg", "RightKnee" }, lh = { "LeftUpperLeg", "LeftHip" }, lk = { "LeftLowerLeg", "LeftKnee" }, root = { "LowerTorso", "Root" } },
	R6 = { rs = { "Torso", "Right Shoulder" }, ls = { "Torso", "Left Shoulder" }, neck = { "Torso", "Neck" }, rh = { "Torso", "Right Hip" },
		lh = { "Torso", "Left Hip" }, root = { "HumanoidRootPart", "RootJoint" } },
}
local function lerpPose(a: Pose, b: Pose, u: number): Pose
	local o = {}
	for k, v in a do
		local w = b[k] or v
		o[k] = { v[1] + (w[1] - v[1]) * u, v[2] + (w[2] - v[2]) * u, v[3] + (w[3] - v[3]) * u }
	end
	return o
end
local function ease(u: number): number u = math.clamp(u, 0, 1); return u * u * (3 - 2 * u) end

-- ------------------------------------------------------------------ one boxer's body
type Body = { ch: Model, r6: boolean, joints: { [string]: { j: Instance, frame: CFrame } }, cur: Pose?, tracks: { [string]: AnimationTrack },
	playing: AnimationTrack?, playingKey: string?, actKey: string?, gloves: boolean }
local function joint(ch: Model, partName: string, name: string): (Instance?, CFrame)
	local p = ch:FindFirstChild(partName)
	local j = p and p:FindFirstChild(name)
	if not j then return nil, CFrame.identity end
	if j:IsA("Motor6D") then return j, j.C0 - j.C0.Position end
	if j:IsA("AnimationConstraint") then
		local a0 = (j :: AnimationConstraint).Attachment0
		return j, if a0 then a0.CFrame - a0.CFrame.Position else CFrame.identity
	end
	return nil, CFrame.identity
end
local function bodyOf(ch: Model): Body?
	local hum = ch:FindFirstChildOfClass("Humanoid")
	if not hum then return nil end
	local r6 = hum.RigType == Enum.HumanoidRigType.R6
	local js = {}
	for k, v in (if r6 then JOINTS.R6 else JOINTS.R15) do
		local j, fr = joint(ch, v[1], v[2])
		if j then js[k] = { j = j, frame = fr } end
	end
	return { ch = ch, r6 = r6, joints = js, cur = nil, tracks = {}, playing = nil, playingKey = nil, actKey = nil, gloves = false }
end
local function applyPose(b: Body, pose: Pose)
	for k, jj in b.joints do
		local v = pose[k]
		if not v then continue end
		local fr = jj.frame
		local rot = CFrame.Angles(math.rad(v[1]), math.rad(v[2]), math.rad(v[3]))
		local t = fr:Inverse() * rot * fr
		if k == "root" then
			local o = pose.off or { 0, 0, 0 }
			-- (the whole body moved: in the root joint's own frame)
			t = fr:Inverse() * CFrame.new(o[1], o[2], o[3]) * rot * fr
		end
		(jj.j :: any).Transform = t
	end
end

-- the clips (R15): MG.BOX.CLIPS[key] = { id, imp = when the punch lands in the clip, len }; a key with no clip is posed
local function clipFor(b: Body, key: string): (AnimationTrack?, any)
	local c = BX.CLIPS and BX.CLIPS[key]
	if b.r6 or not c or not c.id then return nil, nil end
	local tr = b.tracks[key]
	if tr then return tr, c end
	local hum = b.ch:FindFirstChildOfClass("Humanoid")
	local an = hum and (hum:FindFirstChildOfClass("Animator") or hum:WaitForChild("Animator", 1)) :: Animator?
	if not an then return nil, nil end
	local a = Instance.new("Animation")
	a.AnimationId = c.id
	local ok, t = pcall(an.LoadAnimation, an, a)
	if not ok or not t then return nil, nil end
	t.Priority = Enum.AnimationPriority.Action4
	t.Looped = c.loop == true
	b.tracks[key] = t
	return t, c
end

-- what a boxer's act means right now: a pose (blended), or a clip with a speed
local function parseAct(s: any): (string, string, number, number)
	if type(s) ~= "string" then return "idle", "-", 0, 0 end
	local a, sd, t0, len = string.match(s, "^(%a+):(%S):([%d%.%-]+):([%d%.%-]+)$")
	return a or "idle", sd or "-", tonumber(t0) or 0, tonumber(len) or 0
end
local function attackKey(a: string, sd: string): string
	if a == "hook" then return if sd == "L" then "hookL" else "hookR" end
	return a
end
-- the pose a body should be in for this act at (game) time t
local function poseAt(a: string, sd: string, t0: number, len: number, t: number): (Pose, number)
	local dt = t - t0
	if a == "jab" or a == "hook" or a == "upper" or a == "body" or a == "feint" then
		local k = if a == "hook" then (if sd == "L" then "hookL" else "hookR") elseif a == "feint" then "jab" else a
		local c, s = POSES[k .. "_c"], POSES[k .. "_s"]
		if dt < len then return lerpPose(GUARD, c, ease(dt / math.max(0.05, len))), 14 end
		local u = dt - len
		if u < 0.09 then return lerpPose(c, s, ease(u / 0.09)), 60 end
		local rec = (BX.MOVES[a] and BX.MOVES[a].rec or 0.3)
		if u < 0.09 + 0.12 then return s, 60 end
		return lerpPose(s, GUARD, ease((u - 0.21) / math.max(0.1, rec - 0.1))), 18
	elseif a == "duck" or a == "weave" then
		local k = if a == "duck" then "duck" elseif sd == "L" then "weaveL" else "weaveR"
		local p = POSES[k]
		local u = dt / math.max(0.05, len)
		if u < 0.3 then return lerpPose(GUARD, p, ease(u / 0.3)), 40 end
		if u < 0.75 then return p, 40 end
		return lerpPose(p, GUARD, ease((u - 0.75) / 0.25)), 30
	elseif a == "block" then return POSES.block, 26
	elseif a == "hit" then
		local p = if sd == "B" then POSES.hitB elseif sd == "L" then POSES.hitL elseif sd == "R" then POSES.hitR else POSES.hit
		local u = dt / math.max(0.05, len)
		if u < 0.25 then return lerpPose(GUARD, p, ease(u / 0.25)), 50 end
		return lerpPose(p, GUARD, ease((u - 0.25) / 0.75)), 16
	elseif a == "open" then return POSES.open, 12
	elseif a == "down" then return lerpPose(POSES.hit, POSES.down, ease(dt / 0.55)), 30
	elseif a == "up" then return lerpPose(POSES.down, GUARD, ease(dt / math.max(0.2, len))), 20
	end
	-- the guard, breathing
	local g = table.clone(GUARD)
	local s = math.sin(t * 5.2) * 0.04
	g.off = { 0, s, 0 }
	return g, 10
end

-- ------------------------------------------------------------------ the world (everyone)
local function bodyFor(model: Model, side: string): Model?
	local id = model:GetAttribute("Id")
	for _, p in Players:GetPlayers() do
		if p:GetAttribute("MiniGameId") == id and p:GetAttribute("MiniSide") == side and p.Character then return p.Character end
	end
	for _, c in model:GetChildren() do
		if c:IsA("Model") and c:GetAttribute("MiniSide") == side and c:FindFirstChildOfClass("Humanoid") then return c end
	end
	return nil
end

local view: { [Model]: any } = {}
local function ring(at: Vector3, color: Color3, r: number, hold: number?)
	local p = Instance.new("Part")
	p.Name = "MiniBoxRing"; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Shape = Enum.PartType.Cylinder; p.Material = Enum.Material.SmoothPlastic; p.Color = color
	p.Size = Vector3.new(0.04, r, r); p.Transparency = 0.2
	p.CFrame = CFrame.lookAt(at, workspace.CurrentCamera.CFrame.Position) * CFrame.Angles(0, math.pi / 2, 0)
	p.Parent = workspace
	local wait = hold or 0
	if wait > 0 then p.Size = Vector3.new(0.04, r * 1.8, r * 1.8) end
	task.delay(wait, function()
		TweenService:Create(p, TweenInfo.new(0.22, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(0.04, r * 3, r * 3), Transparency = 1 }):Play()
	end)
	task.delay(wait + 0.25, function() p:Destroy() end)
end

function M.world(model: Model, api: any): ((number) -> ())?
	local root = model:WaitForChild("Root", 10) :: BasePart?
	if not root then return nil end
	local V = { bodies = {} :: { [string]: Body }, lastEv = nil :: string? }
	view[model] = V
	local function soundAt(name: string, at: Vector3, vol: number?, pitch: number?)
		api.Sfx.play(name, at, vol, pitch)
	end
	-- the bout's events: sounds, the ring at a landed punch, hit-stop and slow-mo
	model:GetAttributeChangedSignal("Ev"):Connect(function()
		local e = model:GetAttribute("Ev")
		if type(e) ~= "string" or e == V.lastEv then return end
		V.lastEv = e
		local _, kind, who, move, flags = string.match(e, "^(%d+):(%a+):(%S+):(%S+):(.*)$")
		local b = who and V.bodies[who]
		local head = b and (b.ch:FindFirstChild("Head") :: BasePart?)
		local at = if head then head.Position else root.Position + Vector3.new(0, 4, 0)
		local mine = me:GetAttribute("MiniGameId") == model:GetAttribute("Id")
		if kind == "hit" then
			local big = flags and string.find(flags, "big") ~= nil
			local body = flags and string.find(flags, "body") ~= nil
			local torso = b and (b.ch:FindFirstChild("UpperTorso") or b.ch:FindFirstChild("Torso")) :: BasePart?
			local spot = if body and torso then torso.Position else at
			soundAt(if body then "bread_bonk" else "hurt", spot, 0.9)
			if big then soundAt("lasso_slam", spot, 0.45) end
			ring(spot, Color3.fromRGB(236, 232, 224), if big then 0.9 else 0.6)
			if big then hitstop(0.085) end
			if mine then
				local hit = who == me:GetAttribute("MiniSide")
				api.shake(if big then (if hit then 0.03 else 0.018) else (if hit then 0.012 else 0.006), if big then 0.3 else 0.16)
			end
		elseif kind == "block" then
			soundAt("land", at, 0.7, 1.15)
			if mine then api.shake(0.006, 0.12) end
		elseif kind == "dodge" then
			soundAt("swing", at, 0.5)
		elseif kind == "perfect" then
			soundAt("wave_fly", at, 0.7, 0.85)
			local hold = if mine and who == me:GetAttribute("MiniSide") then holdFor(e) else 0
			if hold > 0 then hitstop(hold) else slowmo(0.4) end
			ring(at, Color3.fromRGB(255, 196, 61), 1.0, hold)
		elseif kind == "down" then
			soundAt("bowl_hit", root.Position, 0.9)
			soundAt("land", root.Position, 0.8)
			if mine then api.shake(0.025, 0.4) end
		elseif kind == "bell" then
			local ring1 = root.Position + Vector3.new(0, 6, 0)
			soundAt("door_vip_bell", ring1, 0.9, 0.55)
			if move == "start" or move == "end" then task.delay(0.28, function() soundAt("door_vip_bell", ring1, 0.9, 0.55) end) end
		end
	end)
	-- each boxer's body, every frame: its clip, or its pose
	local lastAct: { [string]: string } = {}
	local stepConn = RunService.Stepped:Connect(function(_, dt: number)
		if not model:IsDescendantOf(workspace) then return end
		local t = now()
		for _, side in { "A", "B" } do
			local ch = bodyFor(model, side)
			local b = V.bodies[side]
			if b and b.ch ~= ch then
				-- (that body has left the ring: its joints and clips back to its own)
				for _, jj in b.joints do pcall(function() (jj.j :: any).Transform = CFrame.identity end) end
				for _, tr in b.tracks do tr:Stop(0.1) end
				V.bodies[side] = nil
				b = nil
			end
			if not ch then continue end
			if not b then
				b = bodyOf(ch)
				V.bodies[side] = b
				if not b then continue end
			end
			local body = b :: Body
			local a, sd, t0, len = parseAct(model:GetAttribute(side .. "_act"))
			-- visual time: in a hit-stop the pose holds; in the slow beat it moves at a third
			local vt = t - (os.clock() < VT.stopUntil and 0.085 or 0)
			-- a clip if there is one for this act (R15), else the pose
			local key = if ATTACK[a] then attackKey(a, sd) elseif a == "weave" then (if sd == "L" then "weaveL" else "weaveR")
				elseif a == "hit" then (if sd == "B" then "hitBody" elseif len >= 0.45 then "hitBig" else "hitHead") elseif a == "idle" then "idle" else a
			local tr, c = clipFor(body, key)
			local actSig = (model:GetAttribute(side .. "_act") or "") :: string
			if tr and c then
				if body.playingKey ~= key or lastAct[side] ~= actSig then
					lastAct[side] = actSig
					if body.playing and body.playing ~= tr then body.playing:Stop(0.08) end
					local speed = 1
					if ATTACK[a] and len > 0 and c.imp then speed = c.imp / len end
					if (a == "duck" or a == "weave") and len > 0 and c.len then speed = c.len / (len + 0.15) end
					if a == "up" and len > 0 and c.len then speed = c.len / len end
					tr:Play(0.08, 1, speed)
					if c.from then tr.TimePosition = c.from end
					body.playing = tr
					body.playingKey = key
				end
				-- after the punch lands it plays on at its own speed; the slow beat and a hit-stop slow every clip
				if ATTACK[a] and c.imp and tr.TimePosition >= c.imp then tr:AdjustSpeed(VT.speed) end
				if not ATTACK[a] and a ~= "duck" and a ~= "weave" and a ~= "up" and not (c.hold and tr.TimePosition >= c.hold) then tr:AdjustSpeed(VT.speed) end
				if (a == "down" or a == "block") and c.hold and tr.TimePosition >= c.hold then tr:AdjustSpeed(0) end
				continue
			end
			if body.playing then body.playing:Stop(0.1); body.playing = nil; body.playingKey = nil end
			local pose, k = poseAt(a, sd, t0, len, vt)
			if VT.speed == 0 and body.cur then pose = body.cur end
			local u = 1 - math.exp(-dt * k * (if VT.speed > 0 then VT.speed else 0))
			body.cur = if body.cur then lerpPose(body.cur :: Pose, pose, u) else pose
			applyPose(body, body.cur :: Pose)
		end
	end)
	model.Destroying:Connect(function() stepConn:Disconnect() end)
	return nil
end

-- ------------------------------------------------------------------ your screen
local S: { [string]: any } = {}

local function bar(parent: Instance, T: any, name: string, x: number, w: number, y: number, h: number, color: Color3, right: boolean): Frame
	local tr = T.new("Frame", { Name = name, BackgroundColor3 = T.TRACK, BorderSizePixel = 0, Position = UDim2.fromOffset(x, y), Size = UDim2.fromOffset(w, h) }, parent)
	T.corner(tr, h // 2)
	local f = T.new("Frame", { Name = "Fill", BackgroundColor3 = color, BorderSizePixel = 0, AnchorPoint = Vector2.new(if right then 1 else 0, 0),
		Position = UDim2.fromScale(if right then 1 else 0, 0), Size = UDim2.fromScale(1, 1) }, tr)
	T.corner(f, h // 2)
	return f
end

local MOVE_NAME = { jab = "JAB", hook = "HOOK", upper = "UPPERCUT", body = "BODY", feint = "JAB" }

local function send(api: any, a: string)
	api.send({ op = "act", a = a, t = now() })
end

local function layout()
	local api = S.api
	local T = api.T
	local m = S.model
	local st = m:GetAttribute("State")
	local o = other(S.side)
	local oppName = m:GetAttribute(o .. "Name")
	local oppBot = (m:GetAttribute(o .. "Id") or 0) == -1
	S.oppL.Text = if oppName then string.upper(oppName :: string) else "WAITING"
	for _, b in S.panel:GetChildren() do if b:IsA("GuiButton") then b.Visible = false end end
	local first: GuiObject? = nil
	S.sub.Text = ""
	if st == "open" then
		S.status.Text = if oppName then "" else "WAITING FOR AN OPPONENT"
		S.status.TextColor3 = T.TEXT
		if not oppName or oppBot then
			S.sub.Text = "OR BOX A BOT"
			for _, b in S.botB do b.Visible = true end
			first = S.botB[2]
		end
	elseif st == "done" then
		local w = m:GetAttribute("Winner")
		local why = m:GetAttribute("Why")
		S.status.Text = if w == "draw" then "DRAW" elseif w == S.side then "YOU WIN" else "YOU LOSE"
		S.status.TextColor3 = if w == S.side then T.ACCENT else T.TEXT
		S.sub.Text = if why == "ko" then "KNOCKOUT" elseif why == "points" then "ON POINTS" elseif why == "left" then "OPPONENT LEFT" else ""
		local mine, theirs = m:GetAttribute("Again" .. S.side), m:GetAttribute("Again" .. o)
		if mine and not theirs then S.sub.Text ..= "   ·   WAITING FOR A REMATCH" end
		S.againB.Visible = not mine
		first = S.againB
		if oppBot then for _, b in S.botB do b.Visible = true end end
	end
	local y = 0
	for _, b in S.panel:GetChildren() do
		if b:IsA("GuiButton") and b.Visible then b.Position = UDim2.fromOffset(y, 0); y += 142 end
	end
	S.panel.Size = UDim2.fromOffset(math.max(0, y - 10), 40)
	api.nav(first ~= nil and api.padOn(), first)
end

function M.open(api: any, model: Model, side: string)
	local T = api.T
	S = { api = api, model = model, side = side, conns = {}, botB = {}, sHeld = false, blockHeld = false, stick = 0, lastEv = nil }
	local root = api.root
	local o = other(side)
	-- the top: you (left) and them (right), health over stamina; the round and its clock between
	local top = T.new("Frame", { Name = "Top", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0, 16), Size = UDim2.fromOffset(900, 80) }, root)
	local function side_(x: number, right: boolean): (TextLabel, Frame, Frame, TextLabel)
		local plate = T.plate(top, if right then "Them" else "You", UDim2.fromOffset(x, 0), UDim2.fromOffset(360, 64))
		local name = T.text(plate, "Name", "", 13, if right then T.SOFT else T.ACCENT, T.FONT_TITLE, if right then Enum.TextXAlignment.Right else Enum.TextXAlignment.Left)
		name.Position = UDim2.fromOffset(14, 6); name.Size = UDim2.new(1, -28, 0, 16)
		local hp = bar(plate, T, "Hp", 14, 332, 28, 14, T.TEXT, right)
		local stb = bar(plate, T, "St", 14, 332, 47, 6, T.ACCENT, right)
		local kd = T.text(plate, "Kd", "", 12, T.DANGER, T.FONT_BOLD, if right then Enum.TextXAlignment.Left else Enum.TextXAlignment.Right)
		kd.Position = UDim2.fromOffset(14, 6); kd.Size = UDim2.new(1, -28, 0, 16)
		return name, hp, stb, kd
	end
	local youName
	youName, S.youHp, S.youSt, S.youKd = side_(0, false)
	S.oppL, S.oppHp, S.oppSt, S.oppKd = side_(540, true)
	youName.Text = "YOU"
	local mid = T.plate(top, "Round", UDim2.fromOffset(372, 0), UDim2.fromOffset(156, 64))
	S.roundL = T.text(mid, "Round", "", 12, T.MUTED, T.FONT_TITLE, Enum.TextXAlignment.Center)
	S.roundL.Position = UDim2.fromOffset(0, 6); S.roundL.Size = UDim2.new(1, 0, 0, 16)
	S.clockL = T.text(mid, "Clock", "", 26, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Center)
	S.clockL.Position = UDim2.fromOffset(0, 24); S.clockL.Size = UDim2.new(1, 0, 0, 32)
	-- the tell: their punch, winding up
	local tell = T.plate(root, "Tell", UDim2.new(0.5, 150, 0, 104), UDim2.fromOffset(190, 46))
	S.tell = tell
	S.tellL = T.text(tell, "Move", "", 16, T.ACCENT, T.FONT_TITLE, Enum.TextXAlignment.Center)
	S.tellL.Position = UDim2.fromOffset(0, 4); S.tellL.Size = UDim2.new(1, 0, 0, 22)
	local tb = T.new("Frame", { Name = "Track", BackgroundColor3 = T.TRACK, BorderSizePixel = 0, Position = UDim2.fromOffset(16, 32), Size = UDim2.new(1, -32, 0, 5) }, tell)
	T.corner(tb, 3)
	S.tellF = T.new("Frame", { Name = "Fill", BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Size = UDim2.fromScale(0, 1) }, tb)
	T.corner(S.tellF, 3)
	tell.Visible = false
	-- the middle
	S.status = T.text(root, "Status", "", 34, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Center, true)
	S.status.AnchorPoint = Vector2.new(0.5, 0.5); S.status.Position = UDim2.fromScale(0.5, 0.36); S.status.Size = UDim2.fromOffset(700, 44)
	S.sub = T.text(root, "Sub", "", 15, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Center, true)
	S.sub.AnchorPoint = Vector2.new(0.5, 0); S.sub.Position = UDim2.new(0.5, 0, 0.36, 28); S.sub.Size = UDim2.fromOffset(700, 20)
	S.flash = T.text(root, "Flash", "", 22, T.ACCENT, T.FONT_SHOUT, Enum.TextXAlignment.Center, true)
	S.flash.AnchorPoint = Vector2.new(0.5, 0.5); S.flash.Position = UDim2.fromScale(0.5, 0.27); S.flash.Size = UDim2.fromOffset(500, 30)
	S.flash.TextTransparency = 1
	S.panel = T.new("Frame", { Name = "Panel", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0.36, 60), Size = UDim2.fromOffset(420, 40) }, root)
	for i, lv in MG.LEVELS do
		local b = api.button(S.panel, "Bot_" .. lv, "BOT · " .. MG.LEVEL_NAME[lv], UDim2.new(), UDim2.fromOffset(132, 40), i == 2)
		b.Activated:Connect(function() api.send({ op = "bot", level = lv }) end)
		S.botB[i] = b
	end
	S.againB = api.button(S.panel, "Again", "AGAIN", UDim2.new(), UDim2.fromOffset(132, 40), true)
	S.againB.Activated:Connect(function() api.send({ op = "again" }) end)
	-- the keys
	S.keys = T.text(root, "Keys", "", 13, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center, true)
	S.keys.AnchorPoint = Vector2.new(0.5, 1); S.keys.Position = UDim2.new(0.5, 0, 1, -16); S.keys.Size = UDim2.fromOffset(980, 18)
	-- a phone's buttons
	if api.isTouch() then
		local pad = T.new("Frame", { Name = "TouchPad", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, root)
		local function tb_(name: string, text: string, pos: UDim2, size: number, down: () -> (), up: (() -> ())?)
			local b = api.button(pad, name, text, pos, UDim2.fromOffset(size, size), false)
			b.AnchorPoint = Vector2.new(0.5, 0.5)
			T.corner(b, size // 2)
			b.MouseButton1Down:Connect(down)
			if up then b.MouseButton1Up:Connect(up); b.MouseLeave:Connect(up) end
		end
		tb_("Jab", "JAB", UDim2.new(1, -70, 1, -150), 84, function() send(api, "jab") end)
		tb_("Hook", "HOOK", UDim2.new(1, -170, 1, -110), 76, function() send(api, "hook") end)
		tb_("Upper", "UPPER", UDim2.new(1, -90, 1, -250), 72, function() send(api, "upper") end)
		tb_("Body", "BODY", UDim2.new(1, -190, 1, -210), 68, function() send(api, "body") end)
		tb_("Block", "BLOCK", UDim2.new(0, 80, 1, -150), 84, function() api.send({ op = "block", on = true }) end, function() api.send({ op = "block", on = false }) end)
		tb_("Duck", "DUCK", UDim2.new(0, 180, 1, -110), 72, function() send(api, "duck") end)
		tb_("WeaveL", "◀", UDim2.new(0, 60, 1, -250), 64, function() send(api, "weaveL") end)
		tb_("WeaveR", "▶", UDim2.new(0, 150, 1, -270), 64, function() send(api, "weaveR") end)
	end
	-- keys and buttons
	local function blockSet(on: boolean)
		if S.blockHeld == on then return end
		S.blockHeld = on
		api.send({ op = "block", on = on })
	end
	table.insert(S.conns, UIS.InputBegan:Connect(function(io: InputObject, gp: boolean)
		if gp then return end
		local k, ut = io.KeyCode, io.UserInputType
		if k == Enum.KeyCode.S then S.sHeld = true end
		if ut == Enum.UserInputType.MouseButton1 then send(api, if S.sHeld then "body" else "jab")
		elseif ut == Enum.UserInputType.MouseButton2 then send(api, if S.sHeld then "body" else "hook")
		elseif k == Enum.KeyCode.E then send(api, "upper")
		elseif k == Enum.KeyCode.Q or k == Enum.KeyCode.DPadLeft then send(api, "weaveL")
		elseif k == Enum.KeyCode.R or k == Enum.KeyCode.DPadRight then send(api, "weaveR")
		elseif k == Enum.KeyCode.C or k == Enum.KeyCode.LeftControl then send(api, "duck")
		elseif k == Enum.KeyCode.F or k == Enum.KeyCode.ButtonL2 then blockSet(true)
		elseif k == Enum.KeyCode.ButtonR2 then send(api, "jab")
		elseif k == Enum.KeyCode.ButtonR1 then send(api, "hook")
		elseif k == Enum.KeyCode.ButtonY then send(api, "upper")
		elseif k == Enum.KeyCode.ButtonX then send(api, "body") end
	end))
	table.insert(S.conns, UIS.InputEnded:Connect(function(io: InputObject)
		local k = io.KeyCode
		if k == Enum.KeyCode.S then S.sHeld = false end
		if k == Enum.KeyCode.F or k == Enum.KeyCode.ButtonL2 then blockSet(false) end
	end))
	for _, a in { "State", "AName", "BName", "AId", "BId", "Winner", "Why", "AgainA", "AgainB" } do
		table.insert(S.conns, model:GetAttributeChangedSignal(a):Connect(layout))
	end
	table.insert(S.conns, model:GetAttributeChangedSignal("Ev"):Connect(function()
		local e = model:GetAttribute("Ev")
		local _, kind, who = string.match(tostring(e), "^(%d+):(%a+):(%S+)")
		if kind == "perfect" and who == side then
			S.flash.Text = "PERFECT  ·  COUNTER"
			S.flash.TextTransparency = 0
			local fl = S.flash
			task.delay(holdFor(tostring(e)), function()
				T.tween(fl, 0.9, { TextTransparency = 1 }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
			end)
		elseif kind == "hit" and who == o and string.find(tostring(e), "counter") then
			S.flash.Text = "COUNTER"
			S.flash.TextTransparency = 0
			T.tween(S.flash, 0.7, { TextTransparency = 1 }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
		end
	end))
	layout()
	-- the camera: a low side-on shot from your right, turned toward your end; your boxer on the left of the screen
	local mirror = if side == "A" then 1 else -1
	local c = L.cam
	api.camera = function(): CFrame?
		local r = model:FindFirstChild("Root") :: BasePart?
		if not r then return nil end
		local a = math.rad(c.angle)
		local eye = Vector3.new(math.cos(a) * c.dist * mirror, c.up, math.sin(a) * c.dist * mirror)
		return CFrame.lookAt(r.CFrame * eye, r.CFrame * Vector3.new(0, c.aim, 0))
	end
	api.fov = 50
	S.step = RunService.RenderStepped:Connect(function(dt: number)
		local st = model:GetAttribute("State")
		local t = now()
		-- the slow beat: the camera leans in
		api.fov = if os.clock() < VT.slowUntil then 44 else 50
		-- bars
		local function fill(f: Frame, v: any, max: number) f.Size = UDim2.fromScale(math.clamp((tonumber(v) or 0) / max, 0, 1), 1) end
		fill(S.youHp, model:GetAttribute(side .. "_hp"), BX.HP)
		fill(S.youSt, model:GetAttribute(side .. "_st"), BX.ST_MAX)
		fill(S.oppHp, model:GetAttribute(o .. "_hp"), BX.HP)
		fill(S.oppSt, model:GetAttribute(o .. "_st"), BX.ST_MAX)
		S.youHp.BackgroundColor3 = if (tonumber(model:GetAttribute(side .. "_hp")) or 100) < 30 then T.DANGER else T.TEXT
		local function kd(n: any): string return string.rep("●", tonumber(n) or 0) end
		S.youKd.Text = kd(model:GetAttribute(side .. "_kd"))
		S.oppKd.Text = kd(model:GetAttribute(o .. "_kd"))
		-- the round and its clock
		local round = model:GetAttribute("Round") or 0
		S.roundL.Text = if round > 0 then "ROUND " .. round .. " / " .. BX.ROUNDS else "BOXING"
		local left = if st == "fight" then math.max(0, ((model:GetAttribute("RoundEnd") or t) :: number) - t)
			elseif st == "rest" then math.max(0, BX.REST - (t - ((model:GetAttribute("At") or t) :: number))) else 0
		S.clockL.Text = if st == "fight" or st == "rest" then ("%d:%02d"):format(left // 60, math.floor(left % 60)) else ""
		-- the middle
		if st == "count" then
			local n = BX.COUNT - (t - ((model:GetAttribute("At") or t) :: number))
			S.status.Text = if n > 0 then tostring(math.ceil(n)) else "BOX"
			S.status.TextColor3 = T.TEXT
		elseif st == "fight" then
			local since = t - ((model:GetAttribute("At") or t) :: number)
			-- (only as a round starts: not again after a get-up)
			local fresh = ((model:GetAttribute("RoundEnd") or t) :: number) - t > BX.ROUND - 1
			S.status.Text = if since < 0.7 and round > 0 and fresh then "ROUND " .. round else ""
		elseif st == "rest" then
			S.status.Text = "REST"
		elseif st == "down" then
			local n = math.ceil(t - ((model:GetAttribute("At") or t) :: number))
			local who = model:GetAttribute("A_act") and (if parseAct(model:GetAttribute(side .. "_act")) == "down" then "YOU" else "THEM")
			S.status.Text = "DOWN  " .. math.clamp(n, 1, BX.DOWN)
			S.status.TextColor3 = if who == "YOU" then T.DANGER else T.ACCENT
		end
		-- their tell: the punch they're winding up, filling to the moment it lands
		local a, sd, t0, len = parseAct(model:GetAttribute(o .. "_act"))
		if ATTACK[a] and st == "fight" and t < t0 + len then
			S.tell.Visible = true
			-- (a hook from their right hand lands on your left: the arrow points at the side to weave to)
			local arrow = if a == "hook" then (if sd == "R" then "◀ " else "") else ""
			local arrowR = if a == "hook" and sd == "L" then " ▶" else ""
			S.tellL.Text = arrow .. MOVE_NAME[a] .. arrowR
			S.tellL.TextColor3 = if a == "upper" or a == "body" then T.DANGER else T.ACCENT
			S.tellF.Size = UDim2.fromScale(math.clamp((t - t0) / math.max(0.05, len), 0, 1), 1)
		else
			S.tell.Visible = false
		end
		-- the keys line (short)
		S.keys.Text = if st ~= "fight" then ""
			elseif api.isTouch() then ""
			elseif api.padOn() then "RT JAB · RB HOOK · Y UPPER · X BODY · LT BLOCK · A DUCK · ◀ ▶ WEAVE"
			else "CLICK JAB · RIGHT CLICK HOOK · E UPPER · S + PUNCH BODY · F BLOCK · C DUCK · Q / R WEAVE"
		-- (a Studio test's autopilot, MiniTest "box:auto": a perfect dodge into every punch, then the counter)
		if S.auto and st == "fight" then
			local oa, osd, ot0, olen = parseAct(model:GetAttribute(o .. "_act"))
			if ATTACK[oa] and oa ~= "feint" and S.autoSeen ~= ot0 and t >= ot0 + olen - 0.09 then
				S.autoSeen = ot0
				local d = if oa == "jab" then "duck" elseif oa == "hook" then (if osd == "R" then "weaveL" else "weaveR") else "weaveL"
				send(api, d)
				task.delay(0.32, function()
					if S.auto and os.clock() >= HOLD.untilT then send(api, if oa == "hook" then "upper" else "hook") end
				end)
			end
		end
		-- a pad: a flick of the left stick weaves
		if api.padOn() and st == "fight" then
			local x = api.Pad.stick(1).X
			if math.abs(x) > 0.75 and S.stick == 0 then S.stick = if x > 0 then 1 else -1; send(api, if x > 0 then "weaveR" else "weaveL")
			elseif math.abs(x) < 0.35 then S.stick = 0 end
		end
	end)
end

function M.close()
	if S.blockHeld and S.api then S.api.send({ op = "block", on = false }) end
	if S.step then S.step:Disconnect() end
	for _, c in S.conns or {} do c:Disconnect() end
	if S.api then S.api.camera = nil; S.api.fov = nil; S.api.nav(false) end
	S = {}
end

function M.remote(_d: any) end

function M.space(down: boolean, io: any): boolean
	if not S.model then return false end
	local st = S.model:GetAttribute("State")
	if io and io.KeyCode == Enum.KeyCode.ButtonA then
		if down and st == "fight" then send(S.api, "duck") end
		return st == "fight" or st == "count" or st == "down" or st == "rest"
	end
	return st == "fight" or st == "count" or st == "down" or st == "rest"
end

function M.back(): boolean return false end

function M.confirmLeave(): string?
	if not S.model then return nil end
	local st = S.model:GetAttribute("State")
	if st == "fight" or st == "count" or st == "down" or st == "rest" then return "PRESS AGAIN TO LEAVE: YOU FORFEIT" end
	return nil
end

-- Studio test: MiniTest "box:<act>" (jab, hook, upper, body, duck, weaveL, weaveR), "box:block:on|off",
-- "box:auto" (dodge the bot's punches perfectly and counter: the autopilot for photos), "box:hold:<s>" (your next
-- perfect dodge freezes s seconds for a photo)
function M.test(v: string): string
	local a = string.match(v, "^box:(%a+)$")
	if v == "box:auto" then S.auto = not S.auto; return "auto " .. tostring(S.auto) end
	local hold = tonumber(string.match(v, "^box:hold:([%d%.]+)$"))
	if hold then HOLD.pending = math.clamp(hold, 0, 5); return "hold " .. HOLD.pending end
	if a and a ~= "auto" then send(S.api, a); return "sent " .. a end
	local on = string.match(v, "^box:block:(%a+)$")
	if on then S.api.send({ op = "block", on = on == "on" }); return "block " .. on end
	return game:GetService("HttpService"):JSONEncode({ state = S.model and S.model:GetAttribute("State") })
end

return M
