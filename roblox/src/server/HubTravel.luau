--!strict
-- HUB TRAVEL (20 Nov 2026; the owner: "can you model all 3 and let me have an option to travel between hubs"). The game
-- has several hubs: the ring (the legacy Map.Hub.Rotunda with Map.Hub.QueuePads / HubSpawns, until it retires) and the
-- new ones, each a folder Map.Hub.<Folder> (Square, Concourse, Atrium) with the attribute Hub (its id: "square" ...),
-- Title, Order, Site, and its own QueuePads / HubSpawns / HubArrive (side-session-notes/HUB-MARKERS.md; play-party's
-- Matches reads the same: a pad's or a player's Hub, none = "ring").
--   * a player's attribute Hub says which hub they are in: the nearest hub's site, while they are within REACH of one
--     (in a match, in training or far away it keeps the last); LastHub is saved (its own small store)
--   * HubTravel.go(p, id) moves them to that hub's arrival point (TeleportT first: the anti-cheat), not in a match, a
--     mini-game or a party room, at most once every COOLDOWN s
--   * HubTravel.homeOf(p): where they respawn outside a match: a spawn of their hub (Party.homeOf falls back to it)
--   * HubTravel.arrive(p): where they land coming back from training (LaserDoors' ToHub)
-- New players start in DEFAULT (when it is built). HubTravelServer.server.luau runs the remote, the tracking and the saves.
local Players = game:GetService("Players")

local HubTravel = {}
HubTravel.DEFAULT = "square" -- (20 Nov, all three hubs live: main's call, the owner told; the ring is retired to a spare)
HubTravel.REACH = 520 -- (studs from a hub's site that count as being in it)
HubTravel.COOLDOWN = 3

local function hubRoot(): Instance? return workspace:FindFirstChild("Map") and workspace.Map:FindFirstChild("Hub") end

export type HubInfo = { id: string, title: string, order: number, folder: Instance?, site: Vector3 }
-- the hubs there are now: every Map.Hub child folder with a Hub attribute and spawns, and the ring (Map.Hub itself) while
-- its Rotunda stands
function HubTravel.list(): { HubInfo }
	local out: { HubInfo } = {}
	local hub = hubRoot()
	if not hub then return out end
	for _, c in hub:GetChildren() do
		local id = c:GetAttribute("Hub")
		if type(id) == "string" and c:IsA("Folder") and c:FindFirstChild("HubSpawns") then
			local site = c:GetAttribute("Site")
			table.insert(out, { id = id, title = tostring(c:GetAttribute("Title") or string.upper(id)), order = tonumber(c:GetAttribute("Order")) or 9,
				folder = c, site = if typeof(site) == "Vector3" then site else Vector3.zero })
		end
	end
	if hub:FindFirstChild("Rotunda") and hub:FindFirstChild("HubSpawns") then
		local o = hub:GetAttribute("Origin")
		table.insert(out, { id = "ring", title = "THE RING", order = 9, folder = hub, site = if typeof(o) == "Vector3" then o else Vector3.new(-200, 240, -10000) })
	end
	table.sort(out, function(a, b) return a.order < b.order end)
	return out
end
function HubTravel.find(id: string?): HubInfo?
	if type(id) ~= "string" then return nil end
	for _, h in HubTravel.list() do if h.id == id then return h end end
	return nil
end
-- the hub whose site is nearest a point, if within REACH
function HubTravel.at(pos: Vector3): HubInfo?
	local best, bd = nil, HubTravel.REACH
	for _, h in HubTravel.list() do
		local d = (Vector3.new(pos.X, 0, pos.Z) - Vector3.new(h.site.X, 0, h.site.Z)).Magnitude
		if d < bd then best, bd = h, d end
	end
	return best
end
-- a player's hub: where they are, else the one they were last in, else the default, else the ring
function HubTravel.hubOf(p: Player): HubInfo?
	return HubTravel.find(p:GetAttribute("Hub") :: string?) or HubTravel.find(p:GetAttribute("LastHub") :: string?)
		or HubTravel.find(HubTravel.DEFAULT) or HubTravel.find("ring")
end
local function pick(folder: Instance?): BasePart?
	if not folder then return nil end
	local list = {}
	for _, c in folder:GetChildren() do if c:IsA("BasePart") then table.insert(list, c) end end
	return if #list > 0 then list[math.random(#list)] else nil
end
local function spawnsOf(h: HubInfo): Instance?
	return h.folder and h.folder:FindFirstChild("HubSpawns")
end
local function arriveOf(h: HubInfo): BasePart?
	if h.id == "ring" then -- (the ring's arrival points are the training door's: the markers in Map.Hub.Doors.HubArrive)
		local doors = h.folder and h.folder:FindFirstChild("Doors")
		local a = doors and doors:FindFirstChild("HubArrive")
		if a and a:IsA("BasePart") then return a end
		local m = pick(a)
		if m then return m end
	end
	return pick(h.folder and h.folder:FindFirstChild("HubArrive")) or pick(spawnsOf(h))
end
-- where a player respawns outside a match: a spawn of their hub (CFrame on its marker, looking its way)
function HubTravel.homeOf(p: Player): CFrame?
	local h = HubTravel.hubOf(p)
	local s = h and pick(spawnsOf(h))
	return if s then s.CFrame else nil
end
function HubTravel.arrive(p: Player): BasePart?
	local h = HubTravel.hubOf(p)
	return if h then arriveOf(h) else nil
end

-- the move. checks are the caller's (HubTravelServer: not in a match, a mini-game or a party room); this stamps the
-- anti-cheat and moves the body onto the hub's arrival point, facing its way
local lastGo: { [Player]: number } = {}
function HubTravel.move(p: Player, id: string): (boolean, string?)
	local h = HubTravel.find(id)
	if not h then return false, "no such hub" end
	local t = lastGo[p]
	if t and os.clock() - t < HubTravel.COOLDOWN then return false, "wait" end
	local ch = p.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	if not (ch and root and hum) or hum.Health <= 0 then return false, "no body" end
	local to = arriveOf(h)
	if not to then return false, "no arrival point" end
	lastGo[p] = os.clock()
	if hum.SeatPart then hum.Sit = false end
	p:SetAttribute("TeleportT", os.clock())
	root.AssemblyLinearVelocity = Vector3.zero
	local at = to.Position + Vector3.new(0, 3, 0)
	local look = Vector3.new(to.CFrame.LookVector.X, 0, to.CFrame.LookVector.Z)
	ch:PivotTo(CFrame.lookAt(at, at + (if look.Magnitude > 0.01 then look.Unit else Vector3.new(0, 0, -1))))
	p:SetAttribute("Hub", h.id)
	p:SetAttribute("LastHub", h.id)
	return true, nil
end
Players.PlayerRemoving:Connect(function(p) lastGo[p] = nil end)

return HubTravel
