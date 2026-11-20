--!strict
-- QUICK JOIN (17 Nov 2026, the owner: "also when someone steps on a pad, make a pop up to quick join and itll teleport
-- them to one of the pad sides"). someone stands on a hub queue pad (Matches' pads, either bank) that still has room:
-- everyone else free in the hub gets a small pop-up (client/QuickJoinUI.luau) with who is waiting, the mode and QUICK
-- JOIN. pressing it asks the server (the Play remote's "quickjoin" op, through Party.ops), which moves them onto the
-- side with room (the emptier side; the lower one on a tie), stamping the anti-cheat's TeleportT first. from there the
-- pad's own queue (Matches.padStep) takes over, as if they had walked on.
--   who gets one: in the hub (not training, the playground, a match or a private lobby), not on a pad, not the one who
--   stepped on, not a party member whose leader is someone else. a party leader brings the party's members who are
--   free in the hub, onto one side together, and only gets the pop-up when one side has room for all of them. the
--   client drops it while a menu is up (shop, loadout, Play screen: the LoadoutOpen attribute) and when Settings > HUD
--   > QUICK JOIN POP-UPS is off.
--   no spam: one pop-up at a time; gone after SHOW s; gone the moment the pad fills or the one waiting steps off; at
--   most one per player every GAP s. someone has to stay on a pad SETTLE s before anyone hears about it (a foot passing
--   over doesn't count), and one stay on a pad is told about once.
-- Studio tests (ServerStorage.JankPlayTest, PlayServer forwards the "qj..." ops): pretend people on a pad, since a play
-- test has one player. pretend people count for the pop-ups only, never for the pad's own queue:
--   T:Invoke("qjstand", padName, side, name)   a pretend person steps on (told about after SETTLE, like anyone)
--   T:Invoke("qjoff", padName)                  everyone pretend steps off that pad (nil: every pad)
--   T:Invoke("qjgap", secs)                     the per-player gap (tests run several cases in a row)
--   T:Invoke("qjstate", player)                 the pads as QUICK JOIN sees them, and the player's pop-up
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Hitbox = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Hitbox"))

local QuickJoin = {}
QuickJoin.SHOW = 6 -- s a pop-up stays up
QuickJoin.GAP = 20 -- s between two pop-ups for one player
QuickJoin.SETTLE = 1 -- s on a pad before the others hear about it

type Who = { name: string, player: Player? } -- a real player, or a Studio test's pretend person
type Stay = { pad: Model, since: number, told: boolean }
type Offer = { id: number, pad: Model, padId: number, who: Who, at: number }

local Matches: any
local Party: any
local pushR: RemoteEvent
local padIds: { [Model]: number } = {}
local nextPadId = 0
local stays: { [Who]: Stay } = {} -- everyone on a pad now, real and pretend
local whoOf: { [Player]: Who } = {}
local offers: { [Player]: Offer } = {}
local lastShown: { [Player]: number } = {}
local nextOffer = 0
local fakes: { [Model]: { { who: Who, side: number } } } = {} -- (Studio tests)

local function now(): number return os.clock() end
local function push(p: Player, msg: any) if p.Parent then pushR:FireClient(p, msg) end end
local function padId(pad: Model): number
	local id = padIds[pad]
	if not id then nextPadId += 1; id = nextPadId; padIds[pad] = id end
	return id
end
local function whoFor(p: Player): Who
	local w = whoOf[p]
	if not w then w = { name = p.DisplayName, player = p }; whoOf[p] = w end
	return w
end

-- one pad as QUICK JOIN sees it: how many on each side (real and pretend), its size, full or not, who is on it
type View = { counts: { number }, size: number, teams: number, full: boolean, on: { [Who]: number } }
local function viewOf(pad: Model, seen: any): View
	local teams = (pad:GetAttribute("Teams") :: number?) or 2
	local size = (pad:GetAttribute("Size") :: number?) or 1
	local counts, on = {}, {}
	for t = 1, teams do
		counts[t] = 0
		local list = seen and seen.sides and seen.sides[t]
		if list then for _, p in list do counts[t] += 1; on[whoFor(p)] = t end end
	end
	for _, f in fakes[pad] or {} do
		if counts[f.side] then counts[f.side] += 1; on[f.who] = f.side end
	end
	local full = true
	for t = 1, teams do if counts[t] < size then full = false end end
	return { counts = counts, size = size, teams = teams, full = full, on = on }
end

-- the people a press moves: the player, or a leader and the party's members free in the hub. nil = no pop-up for them
local function onAPad(p: Player): boolean
	local w = whoOf[p]
	return w ~= nil and stays[w] ~= nil
end
local function freeInHub(p: Player): boolean
	if not p.Parent or p:GetAttribute("Zone") ~= "hub" or p:GetAttribute("Lobby") ~= nil then return false end
	if p:GetAttribute("Watching") ~= nil then return false end -- (watching a match: Spectate.luau)
	if Matches.matchOf(p) ~= nil or onAPad(p) then return false end
	local ch = p.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	return hum ~= nil and hum.Health > 0 and ch:FindFirstChild("HumanoidRootPart") ~= nil
end
local function groupFor(p: Player): { Player }?
	if not freeInHub(p) then return nil end
	local leader, members = Party.groupOf(p)
	if not members then return { p } end
	if leader ~= p then return nil end
	local out = { p }
	for _, m in members do if m ~= p and freeInHub(m) then table.insert(out, m) end end
	return out
end
-- the side a group of n goes to: the emptier side with room for all of them (the lower one on a tie)
local function sideFor(v: View, n: number): number?
	local best: number? = nil
	for t = 1, v.teams do
		if v.size - v.counts[t] >= n and (best == nil or v.counts[t] < v.counts[best :: number]) then best = t end
	end
	return best
end

local function drop(p: Player)
	local o = offers[p]
	if not o then return end
	offers[p] = nil
	push(p, { t = "quickGone", id = o.id })
end

-- someone has stayed on a pad SETTLE s: everyone free in the hub hears about it (the gap and one-at-a-time allowing)
local function announce(pad: Model, who: Who, v: View)
	if v.full then return end
	local mode = string.upper(tostring(pad:GetAttribute("Mode") or pad.Name))
	local waiting = 0
	for _ in v.on do waiting += 1 end
	-- (20 Nov 2026, several hubs: HUB-MARKERS.md) only players in the pad's own hub hear about it (their Hub attribute,
	-- HubTravel's; none = the ring). a hub with no pads of its own yet (not built) takes offers from any
	local padHub = Matches.padHub(pad)
	local hubsWithPads: { [string]: boolean } = {}
	for _, pd in Matches.allPads() do hubsWithPads[Matches.padHub(pd)] = true end
	for _, q in Players:GetPlayers() do
		if q == who.player or offers[q] then continue end
		local qh = Matches.playerHub(q)
		if qh ~= padHub and hubsWithPads[qh] then continue end
		if now() - (lastShown[q] or -math.huge) < QuickJoin.GAP then continue end
		local group = groupFor(q)
		if not group or not sideFor(v, #group) then continue end
		nextOffer += 1
		local o: Offer = { id = nextOffer, pad = pad, padId = padId(pad), who = who, at = now() }
		offers[q] = o
		lastShown[q] = now()
		push(q, { t = "quick", id = o.id, who = who.name, more = waiting - 1, mode = mode, party = #group, show = QuickJoin.SHOW,
			counts = v.counts, size = v.size })
	end
end

local function step()
	local seen = Matches.padView()
	local views: { [Model]: View } = {}
	local pads: { [Model]: boolean } = {}
	for pad in seen do pads[pad] = true end
	for pad in fakes do if pad.Parent then pads[pad] = true end end
	for pad in pads do views[pad] = viewOf(pad, seen[pad]) end
	-- who is where now: new stays start, finished ones end
	local here: { [Who]: Model } = {}
	for pad, v in views do for w in v.on do here[w] = pad end end
	for w, s in stays do if here[w] ~= s.pad then stays[w] = nil end end
	for w, pad in here do
		local s = stays[w]
		if not s then stays[w] = { pad = pad, since = now(), told = false } end
	end
	for w, s in stays do
		if not s.told and now() - s.since >= QuickJoin.SETTLE then
			s.told = true
			announce(s.pad, w, views[s.pad])
		end
	end
	-- pop-ups that should go: shown long enough, the pad filled, the one waiting stepped off, or the player isn't free
	for q, o in offers do
		local v = views[o.pad]
		local s = stays[o.who]
		if now() - o.at > QuickJoin.SHOW + 0.5 or not v or v.full or not s or s.pad ~= o.pad or not groupFor(q) then drop(q) end
	end
end

-- move one body onto a pad side: its slot (Slot parts carry Team and Slot) or the middle of the side, facing into the
-- hub (a side's look points out at the wall behind the pad: the first test faced you into the corner). the
-- anti-cheat's TeleportT stamp goes first, as every server move does
local function standOn(p: Player, pad: Model, t: number, slot: number): Vector3?
	local ch = p.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local side = pad:FindFirstChild("Side" .. t) :: BasePart?
	if not ch or not root or not side then return nil end
	local spot = side.Position
	for _, c in pad:GetChildren() do
		if c.Name == "Slot" and c:IsA("BasePart") and c:GetAttribute("Team") == t and c:GetAttribute("Slot") == slot then
			spot = Vector3.new(c.Position.X, spot.Y, c.Position.Z)
		end
	end
	local top = spot + Vector3.new(0, side.Size.Y / 2, 0)
	local pos = top + Vector3.new(0, Hitbox.ROOT_UP + 0.2, 0)
	local look = -side.CFrame.LookVector * Vector3.new(1, 0, 1)
	if look.Magnitude < 0.1 then look = Vector3.new(0, 0, -1) end
	local hum = ch:FindFirstChildOfClass("Humanoid")
	if hum and hum.SeatPart then
		local weld = hum.SeatPart:FindFirstChild("SeatWeld")
		if weld then weld:Destroy() end
	end
	p:SetAttribute("TeleportT", os.clock()) -- (the anti-cheat's teleport check starts afresh from the pad)
	root.AssemblyLinearVelocity = Vector3.zero
	ch:PivotTo(CFrame.lookAt(pos, pos + look.Unit))
	return look.Unit
end

-- the QUICK JOIN button (the Play remote's "quickjoin" op, a = the pop-up's id)
function QuickJoin.join(p: Player, id: any): any
	local o = offers[p]
	if not o or o.id ~= id then return { ok = false, why = "that pad has moved on" } end
	offers[p] = nil
	local group = groupFor(p)
	if not group then return { ok = false, why = "not from here" } end
	local pad = o.pad
	if not pad.Parent then return { ok = false, why = "that pad has moved on" } end
	local v = viewOf(pad, Matches.padView()[pad])
	local t = sideFor(v, #group)
	if not t then return { ok = false, why = "that pad is full" } end
	local facing: Vector3? = nil
	for i, m in group do
		local lv = standOn(m, pad, t, v.counts[t] + i)
		if m == p then facing = lv end
		if m ~= p then drop(m) end
	end
	-- (look: where to turn the camera; a first-person camera keeps its own direction through a server move)
	return { ok = true, side = t, moved = #group, look = if facing then { facing.X, facing.Z } else nil }
end

function QuickJoin.init(matches: any, party: any, remotes: Instance)
	Matches, Party = matches, party
	pushR = remotes:WaitForChild("PlayPush") :: RemoteEvent
	Party.ops.quickjoin = QuickJoin.join
	Players.PlayerRemoving:Connect(function(p)
		offers[p] = nil
		lastShown[p] = nil
		local w = whoOf[p]
		if w then stays[w] = nil; whoOf[p] = nil end
	end)
	local acc = 0
	RunService.Heartbeat:Connect(function(dt)
		acc += dt
		if acc < 0.2 then return end
		acc = 0
		local ok, err = pcall(step)
		if not ok then warn("[jankfire] quick join: " .. tostring(err)) end
	end)
end

-- ------------------------------------------------------------------ Studio tests
function QuickJoin.test(op: string, a: any, b: any, c: any): any
	if not RunService:IsStudio() then return nil end
	-- (a pad by name: "1v1" = the first, the ring's; "square:1v1" = that hub's. every hub's pads: Matches.allPads)
	local function padNamed(x: any): Model?
		local sx = tostring(x)
		local hubId, name = string.match(sx, "^(%w+):(.+)$")
		for _, pd in Matches.allPads() do
			if pd.Name == (name or sx) and (hubId == nil or Matches.padHub(pd) == hubId) then return pd end
		end
		return nil
	end
	if op == "qjstand" then
		local pad = padNamed(a)
		if not pad or not pad:IsA("Model") then return { ok = false, why = "no pad " .. tostring(a) } end
		local list = fakes[pad] or {}
		fakes[pad] = list
		table.insert(list, { who = { name = if type(c) == "string" then c else "Stand-in" }, side = tonumber(b) or 1 })
		return { ok = true, on = #list }
	elseif op == "qjoff" then
		if a == nil then fakes = {} else
			local pad = padNamed(a)
			if pad then fakes[pad :: Model] = nil end
		end
		return { ok = true }
	elseif op == "qjgap" then
		QuickJoin.GAP = tonumber(a) or 20
		return { ok = true, gap = QuickJoin.GAP }
	elseif op == "qjstate" then
		local out: any = { pads = {}, gap = QuickJoin.GAP }
		local seen = Matches.padView()
		for pad in seen do
			local v = viewOf(pad, seen[pad])
			local n = 0
			for _ in v.on do n += 1 end
			if n > 0 then out.pads[Matches.padHub(pad) .. ":" .. pad.Name] = { counts = v.counts, size = v.size, full = v.full } end
		end
		if typeof(a) == "Instance" and a:IsA("Player") then
			local o = offers[a]
			out.offer = if o then { id = o.id, pad = Matches.padHub(o.pad) .. ":" .. o.pad.Name, who = o.who.name, age = now() - o.at } else nil
			out.free = freeInHub(a)
			out.zone = a:GetAttribute("Zone")
		end
		return out
	end
	return nil
end

return QuickJoin
