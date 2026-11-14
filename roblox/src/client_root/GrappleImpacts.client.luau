-- grapple impacts: swinging into things at speed has consequences. clip a ledge (something about waist-to-head
-- high) and it vaults you up into the air; slam face-first into a wall or a big object and you ragdoll for a moment.
-- only on the rope or just after letting go, so plain running into walls stays plain.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local lp = Players.LocalPlayer
local GrappleRemote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Grapple")
local ImpactRemote = ReplicatedStorage:WaitForChild("ImpactRemote")
local Hud
pcall(function() Hud = require(script.Parent:WaitForChild("Jankfire"):WaitForChild("Hud")) end)

local LAUNCH_MIN = 35 -- studs/s sideways to get vaulted off a ledge
local RAGDOLL_MIN = 50 -- studs/s to get ragdolled by a wall
local LOSS = 0.45 -- lose this share of your speed in one step = you hit something
local AFTER = 0.6 -- s after letting go of the rope that still counts
local COOLDOWN = 1.2
local RAGDOLL_FOR = 1.6

local lastV, ropeT, lastHit, ragdolling = nil, -10, -10, false

local function onRope(ch)
	for _, b in ipairs(workspace.Terrain:GetChildren()) do
		if b:IsA("Beam") and b.Attachment0 and b.Attachment0:IsDescendantOf(ch) then return true end
	end
	return false
end

local function letGo(kind)
	GrappleRemote:FireServer("release") -- the rope everyone else sees
	ImpactRemote:FireServer(kind) -- and ours: the server tells Move to drop it
end

local function launch(root, dir, speed)
	letGo("launch")
	root.AssemblyLinearVelocity = dir * speed * 0.75 + Vector3.new(0, 45 + speed * 0.4, 0)
	if Hud then Hud.callout("LEDGE LAUNCH", 0.7) end
end

local function ragdoll(ch, hum, root, dir, speed)
	letGo("ragdoll")
	ragdolling = true
	local motors, extras, collide, sockets = {}, {}, {}, {}
	for _, m in ipairs(ch:GetDescendants()) do
		-- every joint goes floppy except the neck (your camera) and the root. old rigs: Motor6D; new avatar joints:
		-- AnimationConstraint, with a matching "<joint>BallSocket" already there for ragdolls
		local isMotor = m:IsA("Motor6D")
		if (isMotor or m:IsA("AnimationConstraint")) and m.Name ~= "Root" and m.Name ~= "Neck" and m.Enabled then
			local p0 = if isMotor then m.Part0 else (m.Attachment0 and m.Attachment0.Parent)
			local p1 = if isMotor then m.Part1 else (m.Attachment1 and m.Attachment1.Parent)
			local bs = p1 and p1:FindFirstChild(m.Name .. "BallSocket")
			if bs and bs:IsA("BallSocketConstraint") then
				table.insert(sockets, { bs = bs, was = bs.Enabled })
				bs.Enabled = true
			elseif p0 and p1 then
				local a0 = p0:FindFirstChild(m.Name .. "RigAttachment")
				local a1 = p1:FindFirstChild(m.Name .. "RigAttachment")
				if a0 and a1 then
					bs = Instance.new("BallSocketConstraint")
					bs.Attachment0, bs.Attachment1 = a0, a1
					bs.LimitsEnabled = true; bs.UpperAngle = 70
					bs.TwistLimitsEnabled = true; bs.TwistLowerAngle = -50; bs.TwistUpperAngle = 50
					bs.Parent = p1
					table.insert(extras, bs)
				end
			end
			if bs and p0 and p1 then
				local nc = Instance.new("NoCollisionConstraint")
				nc.Part0, nc.Part1 = p0, p1
				nc.Parent = p1
				table.insert(extras, nc)
				m.Enabled = false
				table.insert(motors, m)
			end
		end
	end
	for _, p in ipairs(ch:GetDescendants()) do
		if p:IsA("BasePart") and p.Name ~= "HumanoidRootPart" and not p:FindFirstAncestorOfClass("Tool") and not p:FindFirstAncestorOfClass("Accessory") then
			collide[p] = p.CanCollide; p.CanCollide = true
		end
	end
	local jm = root:FindFirstChild("JankMove") -- Move's sideways-velocity holder: off, so you actually tumble
	if jm then jm.Enabled = false end
	hum.PlatformStand = true
	root.AssemblyLinearVelocity = -dir * speed * 0.3 + Vector3.new(0, 18, 0) -- BONK: bounce back off it
	root.AssemblyAngularVelocity = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * 14
	if Hud then Hud.callout("BONK", 0.8) end
	task.delay(RAGDOLL_FOR, function()
		for _, e in ipairs(extras) do e:Destroy() end
		for _, s in ipairs(sockets) do if s.bs.Parent then s.bs.Enabled = s.was end end
		for _, m in ipairs(motors) do if m.Parent then m.Enabled = true end end
		for p, cc in pairs(collide) do if p.Parent then p.CanCollide = cc end end
		if hum.Parent and hum.Health > 0 then
			hum.PlatformStand = false
			hum:ChangeState(Enum.HumanoidStateType.GettingUp)
			if jm and jm.Parent then jm.Enabled = true end
		end
		ragdolling = false
	end)
end

-- Move holds your velocity at its own maths, so pressed against a wall you still read as moving: go by how far you
-- really moved this frame, and look ahead along that for what you're about to hit
local lastPos, airSince = nil, nil
RunService.Heartbeat:Connect(function(dt)
	local ch = lp.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	local root = ch and ch:FindFirstChild("HumanoidRootPart")
	if not hum or not root or hum.Health <= 0 or dt <= 0 then lastPos = nil return end
	local now = os.clock()
	if onRope(ch) then ropeT = now end
	-- off the ground for a moment (a swing), not the little hops of running up stairs
	if hum.FloorMaterial == Enum.Material.Air then airSince = airSince or now else airSince = nil end
	local pos = root.Position
	local prev = lastPos
	lastPos = pos
	if not prev or ragdolling or now - lastHit < COOLDOWN or now - ropeT > AFTER then return end
	local moved = Vector3.new(pos.X - prev.X, 0, pos.Z - prev.Z)
	local s0 = moved.Magnitude / dt
	if s0 < LAUNCH_MIN or s0 > 600 then return end -- (600+: a teleport or a respawn, not a swing)
	local dir = moved.Unit
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { ch }
	local feetY = pos.Y - hum.HipHeight - root.Size.Y / 2
	local reach = 1.6 + s0 * dt * 1.5 -- touching it, or will be next frame
	local function probe(h)
		local r = workspace:Raycast(Vector3.new(pos.X, feetY + h, pos.Z), dir * reach, params)
		return r and r.Instance.CanCollide and r or nil
	end
	-- only real things count: stairs, curbs and slopes never do.
	-- a wall = an upright face you hit at both chest and head height at the same distance
	-- a ledge = an upright face low down, clear above it, with a top your legs clip (0.8+ studs above your feet)
	-- and you have to be in the air (swinging), except for a truly huge hit into a wall
	local function upright(r) return r and math.abs(r.Normal.Y) < 0.35 end
	local low = probe(0.6) or probe(1.6) or probe(3)
	local chest, head = probe(3), probe(5.2) or probe(6.5)
	if not upright(low) and not upright(head) then return end
	local airborne = (airSince ~= nil and now - airSince >= 0.08) or not workspace:Raycast(Vector3.new(pos.X, feetY + 0.2, pos.Z), Vector3.new(0, -2.2, 0), params)
	local wall = upright(chest) and upright(head) and math.abs(chest.Distance - head.Distance) < 1.5
	if not wall and upright(low) and not head and airborne then
		local top = workspace:Raycast(Vector3.new(low.Position.X, feetY + 6, low.Position.Z) + dir * 0.6, Vector3.new(0, -6.5, 0), params)
		local rise = top and top.Position.Y - feetY
		if top and top.Normal.Y > 0.7 and rise > 0.8 and rise < 5.5 then
			lastHit = now
			launch(root, dir, s0)
			return
		end
	end
	if wall and s0 >= RAGDOLL_MIN and (airborne or s0 >= 80) then
		lastHit = now
		ragdoll(ch, hum, root, dir, s0)
	end
end)
