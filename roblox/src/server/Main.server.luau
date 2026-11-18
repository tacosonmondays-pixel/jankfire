--!strict
-- JANKFIRE (Roblox) server, step 1: run around Rooftop. it owns: the grapple's say-so (range, sight, rate) and the
-- street below (fall in and you die: "into the smog"). movement itself is the client's, like the web game; the
-- movement checks (teleport, noclip, fly, speed) are AntiCheat.server.luau's; damage and hits are Combat's (step 2)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Config"))
local HookCheck = require(script.Parent:WaitForChild("HookCheck"))
local HookChargeServer = require(script.Parent:WaitForChild("HookChargeServer")) -- (ranked: 2 grapple charges)
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
	-- (a RANKED duel or PARTY RANKED: a hook spends one of 2 charges; none left = cut. shared/HookCharges.luau)
	if not HookChargeServer.allow(p) then return cut("recharging") end
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

-- the open sky (18 Nov 2026, tools/roblox/wallbox.py): a walled arena has no lid any more. while you're in one, its SkyY
-- and its middle (ArenaAt: the site's, a copy's own) go on you: Move.client lets nothing lift you past the sky line and
-- slides you off the ledge round the edge. anyone SKY_OUT over the line (only a client that skipped Move.client gets
-- there) is out of the world, like under the fall line. (only over the site itself: the hub stands higher than any sky)
local SKY_OUT = 60
local skyNext: { [Player]: number } = {}
local function siteOf(p: Player, pos: Vector3): Model?
	local an = p:GetAttribute("Arena")
	if type(an) ~= "string" then return nil end
	local best: Model?, bd = nil, 2500
	local function try(m: Instance?)
		if m and m:IsA("Model") then
			local d = m:GetPivot().Position - pos
			local h = Vector2.new(d.X, d.Z).Magnitude
			if h < bd then best, bd = m :: Model, h end
		end
	end
	try(map:FindFirstChild(an))
	local copies = map:FindFirstChild("ArenaCopies")
	if copies then
		for _, c in copies:GetChildren() do
			if string.sub(c.Name, 1, #an + 5) == an .. "_copy" then try(c) end
		end
	end
	return best
end
Players.PlayerRemoving:Connect(function(p: Player) skyNext[p] = nil end)

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
		-- the sky line (above): what's on you follows your site, twice a second
		local now = os.clock()
		if now >= (skyNext[p] or 0) then
			skyNext[p] = now + 0.5
			local site = siteOf(p, pos)
			local sky = site and site:GetAttribute("SkyY")
			local at = if site and type(sky) == "number" then site:GetPivot().Position else nil
			if p:GetAttribute("SkyY") ~= sky then p:SetAttribute("SkyY", if type(sky) == "number" then sky else nil) end
			if p:GetAttribute("ArenaAt") ~= at then p:SetAttribute("ArenaAt", at) end
		end
		local sky, at = p:GetAttribute("SkyY"), p:GetAttribute("ArenaAt")
		if type(sky) == "number" and typeof(at) == "Vector3" and pos.Y > sky + SKY_OUT and Vector2.new(pos.X - at.X, pos.Z - at.Z).Magnitude < 600 then
			hum.Health = 0
			dropRope(i)
			CalloutRemote:FireClient(p, "OUT OF BOUNDS", 1.5)
			continue
		end
	end
end)
