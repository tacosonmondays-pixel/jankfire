--!strict
-- JANKFIRE (Roblox) server, step 1: run around Rooftop. it owns: the grapple's say-so (range, sight, rate), the
-- street below (fall in and you die: "into the smog"), and a teleport check. movement itself is the client's, like the
-- web game; damage and hits will be the server's too when weapons land (step 2)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Config"))
local HookCheck = require(script.Parent:WaitForChild("HookCheck"))
local MeshSwap = require(script.Parent:WaitForChild("MeshSwap"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local GrappleRemote = Remotes:WaitForChild("Grapple") :: RemoteEvent
local CalloutRemote = Remotes:WaitForChild("Callout") :: RemoteEvent

local map = workspace:WaitForChild("Map")
local killY = (map:FindFirstChildWhichIsA("Model") and map:FindFirstChildWhichIsA("Model"):GetAttribute("KillY")) or -485
local swapped = MeshSwap.run(map)
if swapped > 0 then print(("[jankfire] %d Blender models swapped in"):format(swapped)) end

Players.RespawnTime = 2

type Info = { hookTimes: { number }, rope: Beam?, anchor: Attachment?, last: Vector3?, lastT: number }
local info: { [Player]: Info } = {}

local function dropRope(i: Info)
	if i.rope then i.rope:Destroy(); i.rope = nil end
	if i.anchor then i.anchor:Destroy(); i.anchor = nil end
end

Players.PlayerAdded:Connect(function(p: Player)
	info[p] = { hookTimes = {}, lastT = 0 }
	p.CharacterAdded:Connect(function()
		local i = info[p]
		if i then dropRope(i); i.last = nil end
	end)
end)
Players.PlayerRemoving:Connect(function(p: Player)
	local i = info[p]
	if i then dropRope(i) end
	info[p] = nil
end)

local function alive(p: Player): (Humanoid?, BasePart?)
	local ch = p.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not hum or not root or hum.Health <= 0 then return nil, nil end
	return hum, root
end

GrappleRemote.OnServerEvent:Connect(function(p: Player, what: unknown, point: unknown)
	local i = info[p]
	if not i or type(what) ~= "string" then return end
	if what == "release" then dropRope(i); return end
	if what ~= "hook" then return end
	local function cut(why: string)
		dropRope(i)
		GrappleRemote:FireClient(p, "cut", why)
	end
	if not HookCheck.rate(i.hookTimes, os.clock()) then return cut("too many") end
	local hum, root = alive(p)
	if not hum or not root then return cut("dead") end
	if typeof(point) ~= "Vector3" then return cut("bad point") end
	local pt = point :: Vector3
	local bad = HookCheck.point(pt.X, pt.Y, pt.Z)
	if bad then return cut(bad) end
	local from = root.Position + Vector3.new(0, 1.5, 0) -- about the head
	local toPoint = (pt - from).Magnitude
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { p.Character :: Instance }
	local dir = if toPoint > 1e-3 then (pt - from).Unit else Vector3.yAxis
	local hit = workspace:Raycast(from, dir * (toPoint + 3), params)
	bad = HookCheck.reach((pt - root.Position).Magnitude, toPoint, hit and (hit.Position - from).Magnitude or nil)
	if bad then return cut(bad) end
	-- the rope everyone sees (the hooker's own client hides this one: it draws its own right away)
	dropRope(i)
	local a1 = Instance.new("Attachment")
	a1.WorldPosition = pt
	a1.Parent = workspace.Terrain
	local hand = (p.Character :: Model):FindFirstChild("RightHand") or root
	local a0 = hand:FindFirstChildWhichIsA("Attachment")
	local b = Instance.new("Beam")
	b.Name = "Rope_" .. p.UserId
	b.Attachment0 = a0; b.Attachment1 = a1
	b.Width0 = 0.25; b.Width1 = 0.25; b.FaceCamera = true; b.Segments = 1
	b.Color = ColorSequence.new(Color3.fromRGB(255, 79, 216), Color3.fromRGB(255, 225, 77))
	b.LightEmission = 0.6
	b:SetAttribute("Owner", p.UserId)
	b.Parent = workspace.Terrain
	i.rope, i.anchor = b, a1
end)

-- the street, the teleport check
RunService.Heartbeat:Connect(function()
	local now = os.clock()
	for p, i in info do
		local hum, root = alive(p)
		if not hum or not root then continue end
		local pos = root.Position
		if pos.Y < killY then
			hum.Health = 0
			dropRope(i)
			CalloutRemote:FireClient(p, "INTO THE SMOG", 1.5)
			continue
		end
		if now - i.lastT >= 0.25 then
			if i.last then
				local d = (pos - i.last).Magnitude
				if d > Config.check.maxSpeed * (now - i.lastT) + Config.check.slack then
					root.CFrame = CFrame.new(i.last) * root.CFrame.Rotation -- back where you were
					root.AssemblyLinearVelocity = Vector3.zero
					warn(("[jankfire] %s moved %d studs in %.2fs: put back"):format(p.Name, d, now - i.lastT))
					pos = i.last
				end
			end
			i.last, i.lastT = pos, now
		end
	end
end)
