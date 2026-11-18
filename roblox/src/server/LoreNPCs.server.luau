--!strict
-- THE HIDDEN NPCS, the server half (18 Nov 2026; the book: Shared.LoreData, the rigs: Shared.LoreRigs, the spots:
-- ServerStorage.PolishBackup.LoreSpots). The owner: "Perhaps the hidden NPCs including guy from hr can be rehidden
-- around hub areas? As well as the cast from [the JANKFIRE] story?"
-- workspace.Map.Lore holds one Model per NPC (attribute LoreId; a hidden "Root" part on the floor under them). They
-- stand still here: their idle, head turns and speech bubbles are drawn on each player's own screen (LoreLife.client).
-- FINDING ONE: your body within reach of their Root (the web's own reach, LoreData.REACH / UP / DOWN) counts, once per
-- player, saved in this script's own store (JankfireLore_v1, Profiles: Studio saves go to its _studio twin). The first
-- time, their gift (the web's: a container, or a cosmetic, or a container if you own that already) through Loot.grant
-- with one receipt per player and NPC, a small line on the HUD ("NEW GRAPPLE · PLUNGER", Hud's small kind), and the
-- remote tells your screen to have them say their gift line.
-- The player's attributes: LoreFound (how many), LoreList (their ids, comma separated), LoreTotal (how many there are):
-- the profile card shows "n / N" (ProfileUI); nothing else nags.
-- Remote JankfireRemotes.Lore (server -> client): ("found", id, firstTime), ("hrtake", at) from HrGuy.server.
-- ServerStorage.LoreFindEvent (BindableEvent): (player, id) counts a find that isn't a walk-up (the HR guy's).
-- Studio play tests: ServerStorage.LoreTest (BindableFunction, Studio only):
--   "state"           every NPC: where, the first player's distance, found or not; the save's state
--   "find", id        the first player finds them now, wherever they stand
--   "forget", id?     takes one (or every) find off the first player's save (Studio's _studio store only)
--   "near", id        moves the first player to stand in front of them (a TeleportT stamp first)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local LoreData = require(Shared:WaitForChild("LoreData")) :: any
local Profiles = require(script.Parent:WaitForChild("Profiles")) :: any
local Loot = require(script.Parent:WaitForChild("Loot")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local CalloutR = Remotes:WaitForChild("Callout") :: RemoteEvent
local LoreR = Remotes:WaitForChild("Lore") :: RemoteEvent

local STUDIO = RunService:IsStudio()
local TICK = 0.4 -- s between reach checks
local GIFT_WORDS = { grapple = "GRAPPLE", kill = "KILL EFFECT", effect = "EFFECT", hat = "HAT", emote = "EMOTE" }
local CONTAINER_WORDS = { crate = "+1 CRATE", bag = "+1 DUFFEL BAG", spray = "+1 SPRAY CAN" }

local store = Profiles.new("JankfireLore_v1", function()
	return { v = 1, found = {} }
end)

type State = { prof: any?, ready: boolean, busy: { [string]: boolean } }
local st: { [Player]: State } = {}

local function lore(): Instance?
	local map = workspace:FindFirstChild("Map")
	return map and map:FindFirstChild("Lore")
end
-- each NPC's find point: its Root part (the floor under them), by id
local function points(): { [string]: BasePart }
	local out = {}
	local f = lore()
	if not f then return out end
	for _, m in f:GetChildren() do
		local id = m:GetAttribute("LoreId")
		local r = m:FindFirstChild("Root")
		if type(id) == "string" and r and r:IsA("BasePart") and LoreData.get(id) then out[id] = r end
	end
	return out
end
local function rootOf(p: Player): BasePart?
	local ch = p.Character
	local r = ch and ch:FindFirstChild("HumanoidRootPart")
	return if r and r:IsA("BasePart") then r else nil
end
-- the web's canReach: a cylinder round them, a bit up and down from your feet (the root is ~3 over the feet)
local function inReach(r: BasePart, at: BasePart): boolean
	local feet = r.Position - Vector3.new(0, 3, 0)
	local d = at.Position - feet
	local flat = Vector3.new(d.X, 0, d.Z).Magnitude
	local reach = (at:GetAttribute("Reach") :: number?) or LoreData.REACH
	local up = (at:GetAttribute("Up") :: number?) or LoreData.UP -- (a cat up on a fridge: findable from the floor)
	return flat < reach and d.Y < up and d.Y > -LoreData.DOWN
end

local function publish(p: Player)
	local s = st[p]
	local n, list = 0, {}
	if s and s.prof then
		for _, id in LoreData.ORDER do
			if s.prof.data.found[id] then n += 1; table.insert(list, id) end
		end
	end
	p:SetAttribute("LoreTotal", LoreData.total())
	p:SetAttribute("LoreFound", n)
	p:SetAttribute("LoreList", table.concat(list, ","))
end

-- the gift (and later, the flair session's title for each find: LoreData entries' title ids go through the same door)
local function give(p: Player, e: any): string?
	local g = e.gift
	if not g then return nil end
	local receipt = "lore-" .. e.id .. "-" .. p.UserId .. (if STUDIO then "-" .. os.time() else "")
	if g.container then
		if Loot.grant(p, g.container, receipt) then return CONTAINER_WORDS[g.container] end
		return nil
	end
	if g.kind and g.id then
		if Loot.owns(p, g.kind, g.id) then
			local c = g.orElse or "bag"
			if Loot.grant(p, c, receipt) then return CONTAINER_WORDS[c] end
			return nil
		end
		-- the shop's server-only gift pass first ("gift:<kind>:<id>", shop-gui, 18 Nov: any item, grapples included,
		-- never on sale), then the item's own single offer (kill effects and emotes have one)
		local words = GIFT_WORDS[g.kind] or string.upper(g.kind)
		if Loot.grant(p, "gift:" .. g.kind .. ":" .. g.id, receipt) or Loot.grant(p, g.kind .. ":" .. g.id, receipt) then
			return "NEW " .. words .. " · " .. string.upper(g.id)
		end
		-- (the cosmetic has no offer right now, e.g. not on sale yet: its container instead, so nobody goes without)
		local c = g.orElse or "bag"
		if Loot.grant(p, c, receipt .. "-c") then return CONTAINER_WORDS[c] end
	end
	return nil
end

-- the secret title for a find (CardStyles "lore_<id>", rarity secret: Loot.grant of "egg:title:<id>", one receipt each),
-- and OVERDUE once every one of them is found
local TITLES = { gary = "REGIONAL MANAGER", dale = "OUT OF ORDER", janitor = "HAS SEEN THINGS", smiles = "MANDATORY FUN",
	todd = "INTERN", hr = "HAD A QUICK CHAT" }
local function titleFor(p: Player, tid: string): string?
	local receipt = "lore-title-" .. tid .. "-" .. p.UserId .. (if STUDIO then "-" .. os.time() else "")
	if Loot.owns(p, "title", tid) then return nil end
	return if Loot.grant(p, "egg:title:" .. tid, receipt) then tid else nil
end
local function allFound(s: State): boolean
	for _, id in LoreData.ORDER do if not s.prof.data.found[id] then return false end end
	return true
end
local function allCats(s: State): boolean
	for _, id in LoreData.CATS do if not s.prof.data.found[id] then return false end end
	return true
end

local function find(p: Player, id: string)
	local s = st[p]
	local e = LoreData.get(id)
	if not s or not s.ready or not s.prof or not e or s.busy[id] then return end
	local d = s.prof.data
	if d.found[id] then return end
	s.busy[id] = true
	d.found[id] = os.time()
	s.prof.dirty = true
	publish(p)
	LoreR:FireClient(p, "found", id, true)
	task.spawn(function()
		local note = give(p, e)
		if note then CalloutR:FireClient(p, note, 2.6) end
		if TITLES[id] and titleFor(p, "lore_" .. id) then
			task.wait(if note then 2.8 else 0)
			CalloutR:FireClient(p, "NEW TITLE · " .. TITLES[id], 2.6)
		end
		if LoreData.get(id).kind == "cat" and allCats(s) and titleFor(p, "lore_cats") then
			task.wait(2.8)
			CalloutR:FireClient(p, "NEW TITLE · BOARD MEMBER", 2.6)
		end
		if allFound(s) and titleFor(p, "lore_all") then
			task.wait(2.8)
			CalloutR:FireClient(p, "NEW TITLE · OVERDUE", 2.6)
		end
		s.busy[id] = nil
	end)
end

-- ------------------------------------------------------------------ players
local function added(p: Player)
	if st[p] then return end
	local s: State = { prof = nil, ready = false, busy = {} }
	st[p] = s
	publish(p)
	local prof = Profiles.load(store, "u" .. p.UserId, function() return p.Parent ~= nil and st[p] == s end)
	if not prof then return end
	if st[p] ~= s then Profiles.release(store, prof); return end
	if type(prof.data.found) ~= "table" then prof.data.found = {} end
	for k in prof.data.found do if not LoreData.get(k) then prof.data.found[k] = nil end end -- (one taken out of the game)
	s.prof = prof
	s.ready = true
	publish(p)
	-- (someone who found everything before OVERDUE existed, or whose grant didn't save: theirs now, quietly)
	task.delay(8, function()
		if st[p] ~= s or not s.ready then return end
		if allCats(s) then titleFor(p, "lore_cats") end
		if allFound(s) then titleFor(p, "lore_all") end
	end)
end
for _, p in Players:GetPlayers() do task.spawn(added, p) end
Players.PlayerAdded:Connect(added)
Players.PlayerRemoving:Connect(function(p)
	local s = st[p]
	st[p] = nil
	if s and s.prof then Profiles.release(store, s.prof) end
end)

-- finds that aren't a walk-up (the Tall Guy From HR finds you: HrGuy.server fires this when he has someone)
local findEv = ServerStorage:FindFirstChild("LoreFindEvent") or Instance.new("BindableEvent")
findEv.Name = "LoreFindEvent"
findEv.Parent = ServerStorage;
(findEv :: BindableEvent).Event:Connect(function(p: Player, id: string)
	if typeof(p) == "Instance" and p:IsA("Player") and type(id) == "string" then find(p, id) end
end)

-- ------------------------------------------------------------------ the reach check
task.spawn(function()
	while true do
		task.wait(TICK)
		local pts = points()
		if next(pts) == nil then continue end
		for p, s in st do
			if not s.ready then continue end
			local r = rootOf(p)
			if not r then continue end
			for id, at in pts do
				if not s.prof.data.found[id] and inReach(r, at) then find(p, id) end
			end
		end
	end
end)

-- ------------------------------------------------------------------ Studio test hook
if STUDIO then
	local hook = ServerStorage:FindFirstChild("LoreTest") or Instance.new("BindableFunction")
	hook.Name = "LoreTest"
	hook.Parent = ServerStorage;
	(hook :: BindableFunction).OnInvoke = function(op: string, a: any): any
		local p = Players:GetPlayers()[1]
		local s = p and st[p]
		if op == "state" then
			local out = { ready = s and s.ready or false, save = s and s.prof and s.prof.state or "none", npcs = {} :: any }
			local r = p and rootOf(p)
			for id, at in points() do
				out.npcs[id] = { at = tostring(at.Position), dist = if r then math.floor((r.Position - at.Position).Magnitude * 10) / 10 else -1,
					found = s and s.prof and s.prof.data.found[id] ~= nil or false, reach = r ~= nil and inReach(r, at) }
			end
			out.attrs = p and { p:GetAttribute("LoreFound"), p:GetAttribute("LoreTotal"), p:GetAttribute("LoreList") } or nil
			return out
		elseif op == "find" and p then
			find(p, tostring(a))
			return p:GetAttribute("LoreList")
		elseif op == "forget" and s and s.prof then
			if a then s.prof.data.found[tostring(a)] = nil else s.prof.data.found = {} end
			s.prof.dirty = true
			publish(p)
			return p:GetAttribute("LoreList")
		elseif op == "near" and p then
			local at = points()[tostring(a)]
			local r = rootOf(p)
			if not at or not r then return "no" end
			local m = at.Parent :: Model
			local visit = at:GetAttribute("Visit")
			local off = if typeof(visit) == "Vector3" then visit else m:GetPivot().LookVector * 7
			p:SetAttribute("TeleportT", os.clock())
			local spot = at.Position + off + Vector3.new(0, 3.2, 0)
			r.CFrame = CFrame.lookAt(spot, Vector3.new(at.Position.X, spot.Y, at.Position.Z))
			return tostring(spot)
		end
		return "ops: state, find id, forget id?, near id"
	end
end
