--!strict
-- HOUSE HUNT's ragdoll (owner, 27 Nov 2026: "Push is a light push that ragdolls the enemy or other survivors, super push
-- is the same but like the handslapper and punch ragdolls and stuns you can't untagdoll for a few seconds we need ragdoll
-- mechanic and a button to unragdoll!!"). Server-run, R15 and R6: the body's Motor6Ds (all but the root's) stand down
-- and limited ball sockets hold the limbs, then the joints come back on the get-up. A player's own client runs their
-- body's physics: it is told ("rag", v) and goes limp (HuntMoves.client); a stand-in is the server's own.
--   HuntRagdoll.down(f, v, dur, minT) -> bool   down for dur s (gets up by itself then); the get-up button works after
--                                               minT s. false if already down, dead, or just got up (IMMUNE s)
--   HuntRagdoll.ask(p)                         the get-up button (Space / pad A / phone jump: HuntMoves.client)
--   HuntRagdoll.isDown(f)
-- While down: the anti-cheat's grace (a fling is no cheat), StunUntil (the game's own stun: no shooting, no moving),
-- the player attributes HuntRag / HuntRagMin (server time) for the client's GET UP key.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local HC = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("HuntConfig")) :: any
local Fight = require(script.Parent:WaitForChild("Fight")) :: any
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Hunt") :: RemoteEvent
local RG = HC.RAGDOLL

local HuntRagdoll = {}

-- each joint's swing (deg off its rest, along the bone) and twist; "up" joints point up the body, the rest down it
local LIMIT: { [string]: { number } } = {
	Neck = { 35, 30 }, Waist = { 30, 20 },
	LeftShoulder = { 85, 45 }, RightShoulder = { 85, 45 }, LeftElbow = { 70, 8 }, RightElbow = { 70, 8 },
	LeftWrist = { 35, 15 }, RightWrist = { 35, 15 },
	LeftHip = { 60, 20 }, RightHip = { 60, 20 }, LeftKnee = { 70, 8 }, RightKnee = { 70, 8 },
	LeftAnkle = { 30, 12 }, RightAnkle = { 30, 12 },
	["Left Shoulder"] = { 85, 45 }, ["Right Shoulder"] = { 85, 45 }, ["Left Hip"] = { 60, 20 }, ["Right Hip"] = { 60, 20 },
}
local UPWARD = { Neck = true, Waist = true }
local ROOTS = { Root = true, RootJoint = true }

type Down = { f: any, model: Model, hum: Humanoid, p: Player?, made: { Instance }, motors: { Motor6D }, minT: number,
	endT: number, neck: boolean, stun: number?, collide: { [BasePart]: boolean } }
local down: { [any]: Down } = {}
local immune: { [any]: number } = {}

local function serverNow(): number return workspace:GetServerTimeNow() end

function HuntRagdoll.isDown(f: any): boolean return f ~= nil and down[f] ~= nil end

local function setStun(r: Down, untilT: number)
	local cur = 0
	if r.p then cur = tonumber(r.p:GetAttribute("StunUntil")) or 0 end
	local v = math.max(cur, untilT)
	r.stun = v
	if r.p then r.p:SetAttribute("StunUntil", v) end
	r.hum:SetAttribute("StunUntil", v)
	if not r.p then r.model:SetAttribute("StunUntil", v) end
end

function HuntRagdoll.down(f: any, v: Vector3, dur: number, minT: number): boolean
	if not f or down[f] or not f.alive then return false end
	if (immune[f] or 0) > os.clock() then return false end
	local model = Fight.model(f)
	local hum = model and model:FindFirstChildOfClass("Humanoid")
	local root = model and model:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not (model and hum and root) or hum.Health <= 0 then return false end
	local p: Player? = if f.kind == "player" then f.ref else nil
	local r: Down = { f = f, model = model, hum = hum, p = p, made = {}, motors = {}, minT = os.clock() + minT,
		endT = os.clock() + dur, neck = hum.RequiresNeck, stun = nil, collide = {} }
	for _, m in model:GetDescendants() do
		if m:IsA("Motor6D") and not ROOTS[m.Name] and m.Part0 and m.Part1 and m.Enabled then
			local L = LIMIT[m.Name] or { 45, 20 }
			local rot = if UPWARD[m.Name] then CFrame.Angles(0, 0, math.pi / 2) else CFrame.Angles(0, 0, -math.pi / 2)
			local a0 = Instance.new("Attachment"); a0.Name = "HuntRagA"; a0.CFrame = m.C0 * rot; a0.Parent = m.Part0
			local a1 = Instance.new("Attachment"); a1.Name = "HuntRagB"; a1.CFrame = m.C1 * rot; a1.Parent = m.Part1
			local bs = Instance.new("BallSocketConstraint")
			bs.Name = "HuntRag"; bs.Attachment0 = a0; bs.Attachment1 = a1
			bs.LimitsEnabled = true; bs.UpperAngle = L[1]
			bs.TwistLimitsEnabled = true; bs.TwistLowerAngle = -L[2]; bs.TwistUpperAngle = L[2]
			bs.Parent = m.Part0
			local nc = Instance.new("NoCollisionConstraint")
			nc.Name = "HuntRag"; nc.Part0 = m.Part0; nc.Part1 = m.Part1; nc.Parent = m.Part0
			table.insert(r.made, a0); table.insert(r.made, a1); table.insert(r.made, bs); table.insert(r.made, nc)
			table.insert(r.motors, m)
		end
	end
	hum.RequiresNeck = false
	for _, m in r.motors do m.Enabled = false end
	down[f] = r
	setStun(r, serverNow() + dur + 0.2) -- (no shooting, no moving: a downed hunter can't fire)
	if p then
		p:SetAttribute("ACGrace", os.clock() + dur + 2.5) -- (the anti-cheat: a fling is no cheat)
		p:SetAttribute("HuntRag", serverNow() + dur)
		p:SetAttribute("HuntRagMin", serverNow() + minT)
		Remote:FireClient(p, "rag", v)
	else
		hum.PlatformStand = true
		hum:ChangeState(Enum.HumanoidStateType.Physics)
		for _, d in model:GetDescendants() do
			if d:IsA("BasePart") then
				r.collide[d] = d.CanCollide
				d.CanCollide = d ~= root
				d.AssemblyLinearVelocity = v
			end
		end
	end
	return true
end

local getUpTracks: { [Humanoid]: AnimationTrack } = {}
local function up(f: any)
	local r = down[f]
	if not r then return end
	down[f] = nil
	immune[f] = os.clock() + (RG.immune or 2)
	for _, i in r.made do i:Destroy() end
	if r.hum.Parent and r.hum.Health > 0 then
		for _, m in r.motors do if m.Parent then m.Enabled = true end end
		r.hum.RequiresNeck = r.neck
		local rise = (RG.riseTime or 1.5)
		setStun(r, serverNow() + rise) -- (the get-up plays: no moving till you're up)
		if r.p then
			r.p:SetAttribute("TeleportT", os.clock()) -- (where the fling left you is where you are)
			r.p:SetAttribute("ACGrace", os.clock() + rise + 1.5)
			r.p:SetAttribute("HuntRag", nil); r.p:SetAttribute("HuntRagMin", nil)
			Remote:FireClient(r.p, "rag", nil)
		else
			for d, c in r.collide do if d.Parent then d.CanCollide = c end end
			r.hum.PlatformStand = false
			r.hum:ChangeState(Enum.HumanoidStateType.GettingUp)
			local root = r.model:FindFirstChild("HumanoidRootPart") :: BasePart?
			if root then -- (stand the stand-in up where it lies, facing the way it lies)
				local lv = root.CFrame.LookVector
				local flat = Vector3.new(lv.X, 0, lv.Z)
				if flat.Magnitude < 0.05 then flat = Vector3.new(0, 0, -1) end
				root.CFrame = CFrame.lookAt(root.Position + Vector3.new(0, 1.5, 0), root.Position + Vector3.new(0, 1.5, 0) + flat.Unit)
			end
			local an = r.hum:FindFirstChildOfClass("Animator")
			local rig = if r.hum.RigType == Enum.HumanoidRigType.R6 then "R6" else "R15"
			local id = RG.getUp and RG.getUp[rig]
			if an and id then
				local tr = getUpTracks[r.hum]
				if not tr then
					local a = Instance.new("Animation"); a.AnimationId = "rbxassetid://" .. tostring(id)
					local ok, t = pcall(function() return (an :: Animator):LoadAnimation(a) end)
					if ok and t then tr = t; t.Priority = Enum.AnimationPriority.Action4; t.Looped = false; getUpTracks[r.hum] = t end
				end
				if tr then tr:Play(0.05, 1, RG.riseSpeed or 1.8) end
			end
		end
	else
		if r.p then r.p:SetAttribute("HuntRag", nil); r.p:SetAttribute("HuntRagMin", nil) end
	end
end
HuntRagdoll.up = up

function HuntRagdoll.ask(p: Player)
	local f = Fight.byPlayer[p]
	local r = f and down[f]
	if r and os.clock() >= r.minT then up(f) end
end

RunService.Heartbeat:Connect(function()
	local t = os.clock()
	for f, r in down do
		if t >= r.endT or not r.model.Parent or r.hum.Health <= 0 or not f.alive then up(f) end
	end
end)
Players.PlayerRemoving:Connect(function(p)
	local f = Fight.byPlayer[p]
	if f then down[f] = nil; immune[f] = nil end
end)

return HuntRagdoll
