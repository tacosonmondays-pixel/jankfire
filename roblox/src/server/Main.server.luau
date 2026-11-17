--!strict
-- JANKFIRE (Roblox) server, step 1: run around Rooftop. it owns: the grapple's say-so (range, sight, rate) and the
-- street below (fall in and you die: "into the smog"). movement itself is the client's, like the web game; the
-- movement checks (teleport, noclip, fly, speed) are AntiCheat.server.luau's; damage and hits are Combat's (step 2)
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
-- the fall line is your match's arena's (matches run side by side, each in its own site: Matches.killY), else the
-- default arena's
local Matches = require(script.Parent:WaitForChild("Matches"))
local swapped = MeshSwap.run(map)
if swapped > 0 then print(("[jankfire] %d Blender models swapped in"):format(swapped)) end

Players.RespawnTime = 2

type Info = { hookTimes: { number }, rope: Beam?, anchor: Attachment?, last: Vector3?, lastT: number, tp: number? }
local info: { [Player]: Info } = {}

local function dropRope(i: Info)
	if i.rope then i.rope:Destroy(); i.rope = nil end
	if i.anchor then i.anchor:Destroy(); i.anchor = nil end
end

Players.PlayerAdded:Connect(function(p: Player)
	info[p] = { hookTimes = {}, lastT = 0 }
	p.CharacterAdded:Connect(function()
		local i = info[p]
		-- a new body gets moved to its spawn (the hub, the arena) right after it loads: give the teleport check a moment
		if i then dropRope(i); i.last = nil; i.lastT = os.clock() + 0.5 end
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
	b.Color = ColorSequence.new(Color3.fromRGB(236, 238, 242), Color3.fromRGB(176, 182, 192)) -- (a pale steel cable, like the one its owner sees)
	b.LightEmission = 0.3
	b:SetAttribute("Owner", p.UserId)
	b.Parent = workspace.Terrain
	i.rope, i.anchor = b, a1
end)

-- the street
RunService.Heartbeat:Connect(function()
	for p, i in info do
		local hum, root = alive(p)
		if not hum or not root then continue end
		local pos = root.Position
		local killY = Matches.killY(p)
		if pos.Y < killY then
			hum.Health = 0
			dropRope(i)
			CalloutRemote:FireClient(p, "INTO THE SMOG", 1.5)
			continue
		end
		-- (the teleport check is AntiCheat.server.luau's now, with the fly, noclip and speed checks: a server teleport
		-- still stamps the player's TeleportT attribute so it starts afresh from the new spot)
	end
end)
