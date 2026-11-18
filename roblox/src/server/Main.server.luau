--!strict
-- JANKFIRE (Roblox) server, step 1: run around Rooftop. it owns: the grapple's say-so (range, sight, rate) and the
-- street below (fall in and you die: "into the smog"). movement itself is the client's, like the web game; the
-- movement checks (teleport, noclip, fly, speed) are AntiCheat.server.luau's; damage and hits are Combat's (step 2)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local PhysicsService = game:GetService("PhysicsService")
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
local Fight = require(script.Parent:WaitForChild("Fight")) -- (a hook on a person: who they are, kill credit)
local Rules = require(script.Parent:WaitForChild("Rules"))
local swapped = MeshSwap.run(map)
if swapped > 0 then print(("[jankfire] %d Blender models swapped in"):format(swapped)) end

Players.RespawnTime = 2
-- the parts that stop bodies but no rays (WebArena's flag "c": rails, the columns over the roofs) are in JFRayBlind: it
-- collides with the players' groups (JFPlayers, JFShredded, VipGuest) but not with Default, where every ray, rope and
-- bullet is cast. (characters are never left in Default: HubVip and the Shredder put them in JFPlayers / VipGuest)
pcall(function() PhysicsService:RegisterCollisionGroup("JFRayBlind") end)
pcall(function() PhysicsService:CollisionGroupSetCollidable("JFRayBlind", "Default", false) end)

type Info = { hookTimes: { number }, rope: Beam?, anchor: Attachment?, last: Vector3?, lastT: number, tp: number?,
	body: Model?, bodyBlind: number, bodyNext: number, -- (body: the person the rope is tied to)
	bornT: number } -- (when the body loaded: the spawn grace below)
local info: { [Player]: Info } = {}

local function dropRope(i: Info)
	if i.rope then i.rope:Destroy(); i.rope = nil end
	if i.anchor then i.anchor:Destroy(); i.anchor = nil end
	i.body = nil
end

Players.PlayerAdded:Connect(function(p: Player)
	info[p] = { hookTimes = {}, lastT = 0, bodyBlind = 0, bodyNext = 0, bornT = 0 }
	p.CharacterAdded:Connect(function()
		local i = info[p]
		-- a new body gets moved to its spawn (the hub, the arena) right after it loads: give the teleport check a moment
		if i then dropRope(i); i.last = nil; i.lastT = os.clock() + 0.5; i.bornT = os.clock() end
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

-- the rope everyone sees, from the hooker's hand to a1 (the hooker's own client hides this one: it draws its own)
local function tieRope(i: Info, p: Player, a1: Attachment)
	dropRope(i)
	local root = (p.Character :: Model):FindFirstChild("HumanoidRootPart")
	local hand = (p.Character :: Model):FindFirstChild("RightHand") or root
	local a0 = hand and hand:FindFirstChildWhichIsA("Attachment")
	local b = Instance.new("Beam")
	b.Name = "Rope_" .. p.UserId -- (AntiCheat reads this name: on a rope, no fly checks)
	b.Attachment0 = a0; b.Attachment1 = a1
	b.Width0 = 0.25; b.Width1 = 0.25; b.FaceCamera = true; b.Segments = 1
	b.Color = ColorSequence.new(Color3.fromRGB(236, 238, 242), Color3.fromRGB(176, 182, 192)) -- (a pale steel cable, like the one its owner sees)
	b.LightEmission = 0.3
	b:SetAttribute("Owner", p.UserId)
	b.Parent = workspace.Terrain
	i.rope, i.anchor = b, a1
end

GrappleRemote.OnServerEvent:Connect(function(p: Player, what: unknown, point: unknown, body: unknown)
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
	-- a person (18 Nov 2026, the owner: "can you make it so you can grapple onto people"): a living player or training
	-- dummy, in range and in sight (now or a moment ago, for lag). the rope is tied to their chest and follows them
	-- (Move.client reels the hooker in; the heartbeat below drops it when they go). an enemy hooked is tagged like a
	-- knock (Rules.tagged): a fall or a hazard within 10 s is the hooker's kill, "via" the grapple. a teammate never is
	local tm = if typeof(body) == "Instance" and body:IsA("Model") then body :: Model else nil
	if tm then
		local tf = Fight.of(Players:GetPlayerFromCharacter(tm) or tm)
		local troot = tm:FindFirstChild("HumanoidRootPart") :: BasePart?
		local thum = tm:FindFirstChildOfClass("Humanoid")
		if not tf or not tf.alive or not troot or not thum or thum.Health <= 0 or tm == p.Character or not tm:IsDescendantOf(workspace) then
			return cut("nobody there")
		end
		local chestAt = troot.Position + Vector3.new(0, Config.hook.bodyUp, 0)
		local badB = HookCheck.body((chestAt - root.Position).Magnitude, Fight.sees(from, tf))
		if badB then return cut(badB) end
		if not HookChargeServer.allow(p) then return cut("recharging") end
		local mf = Fight.byPlayer[p]
		if mf and mf ~= tf and Fight.allow(mf, tf) then Rules.tagged(tf, mf, "grapple", os.clock()) end
		local a1 = Instance.new("Attachment")
		a1.Name = "RopeTie_" .. p.UserId
		a1.Position = Vector3.new(0, Config.hook.bodyUp, 0)
		a1.Parent = troot
		tieRope(i, p, a1)
		i.body, i.bodyBlind, i.bodyNext = tm, 0, os.clock() + 0.2
		return
	end
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
	tieRope(i, p, a1)
end)

-- the open sky (18 Nov 2026, tools/roblox/wallbox.py): a walled arena has no lid any more. while you're in one, its SkyY
-- and its middle (ArenaAt: the site's, a copy's own) go on you: Move.client lets nothing lift you past the sky line and
-- slides you off the ledge round the edge. anyone SKY_OUT over the line (only a client that skipped Move.client gets
-- there) is out of the world, like under the fall line. (only over the site itself: the hub stands higher than any sky)
local SKY_OUT = 60
local SPAWN_GRACE = 1 -- s (the spawn grace, in the heartbeat below)
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
		-- the spawn grace (18 Nov): LoadCharacter yields, and until Fight.spawn places the new body it stands wherever
		-- Roblox first put it (the Rooftop v1's SpawnLocations, y -11 to 13). no fall line or sky line applies to it
		-- until it's placed (its fighter alive again), or for SPAWN_GRACE at most. (today every fall line is lower than
		-- those pads, so this only guards against spawns or fall lines moving; the script's attribute SpawnGrace = 0
		-- turns it off for a test)
		local f = Fight.byPlayer[p]
		if f and not f.alive then
			local g = script:GetAttribute("SpawnGrace")
			if os.clock() - i.bornT < (if type(g) == "number" then g else SPAWN_GRACE) then continue end
		end
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
		-- a rope tied to a person (above), five times a second: they died, respawned or left, or the hooker hasn't seen
		-- them for a moment (the client lets go sooner; this is the say-so), and it drops
		if i.body and now >= i.bodyNext then
			i.bodyNext = now + 0.2
			local tm = i.body :: Model
			local tf = Fight.of(Players:GetPlayerFromCharacter(tm) or tm)
			local troot = tm:FindFirstChild("HumanoidRootPart") :: BasePart?
			if not tf or not tf.alive or not troot or not tm:IsDescendantOf(workspace) or not (i.anchor and i.anchor.Parent) then
				dropRope(i)
				GrappleRemote:FireClient(p, "cut", "gone")
			else
				local eye = pos + Vector3.new(0, 1.5, 0)
				local d = troot.Position + Vector3.new(0, Config.hook.bodyUp, 0) - eye
				local blocked = d.Magnitude > 0.1 and Fight.castMap(eye, d.Unit, d.Magnitude) ~= nil
				i.bodyBlind = if blocked then i.bodyBlind + 0.2 else 0
				if i.bodyBlind > Config.hook.bodyBlind + 0.4 then
					dropRope(i)
					GrappleRemote:FireClient(p, "cut", "out of sight")
				end
			end
		end
	end
end)
