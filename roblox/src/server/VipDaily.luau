--!strict
-- THE VIP DAILY REWARD (the owner, 17 Nov 2026: "If you talk to Trisangle in the vip room as long as you have vip you get
-- a random daily reward with the best thing being a special wrap skin hat anddddd skin case. Bags cans coins etc will be
-- filler rewards"). the table, the roll and the odds are Shared.VipDailyData; this pays it.
--   the prompt: a ProximityPrompt "VipDailyPrompt" (tag "VipDailyPrompt") on Trisangle's place: the hub's HubNPC spot
--   whose Who is "Trisangle", or any HubNPC part with the attribute VipDaily = true (HubNPCs.server.luau builds her).
--   pressing it: VIP is checked here (Vip.isVip); not VIP = the client opens the shop's VIP tile. once a day (00:00 UTC).
--   the save: one session-locked profile per player (Profiles.luau), "JankfireVipDaily_v1" ("_studio" in Studio):
--   { day (the last claimed), n (claims), pending?, log }. a claim writes day + pending FIRST (a second claim the same
--   day, here or in another server, is refused by that), then pays: Brass through the quests server (Quests.giveBrass),
--   a container or one of the three daily-only items through Loot.grant, each with the receipt id "vd-<userId>-<day>"
--   (both idempotent). paid = pending cleared; not paid (a save down) = paid again on the next try or the next join.
--   the client: the remote JankfireRemotes.VipDaily (RemoteEvent) pushes { t = "won", prize, reel, late? },
--   { t = "later", at } (claimed today: the next at that unix time), { t = "notvip" }, { t = "error", why }; the player
--   attribute VipDailyNext is when the next claim opens (0 = it's ready).
--   Studio test: ServerStorage.JankVipDailyTest (BindableFunction): ("claim", p, prizeId?) -> what was pushed (prizeId
--   picks the prize: "spray", "crate", ...), ("reset", p),
--   ("state", p), ("sim", n, "best"?) -> the counts of n rolls.
-- docs: roblox/docs/SHOP.md (VIP daily reward)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local CollectionService = game:GetService("CollectionService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Data = require(Shared:WaitForChild("VipDailyData"))
local Config = require(Shared:WaitForChild("Config")) :: any
local Shop = require(Shared:WaitForChild("Shop")) :: any
local Profiles = require(script.Parent:WaitForChild("Profiles"))
local Loot = require(script.Parent:WaitForChild("Loot")) :: any
local Vip = require(script.Parent:WaitForChild("Vip")) :: any

local STUDIO = RunService:IsStudio()
local FREE_CAP = 10 -- (Loot.luau's BUY_MAX: while containers are free, stock past this is lost)
local TAG = "VipDailyPrompt"

local VipDaily = {}

local store = Profiles.new("JankfireVipDaily_v1" .. (if STUDIO then "_studio" else ""), function()
	return { day = -1, n = 0, pending = nil, log = {} }
end)
local profs: { [Player]: any } = {}
local busy: { [Player]: boolean } = {}
local lastPush: { [Player]: any } = {}
local forced: { [Player]: string } = {} -- (Studio tests only)
local rng = Random.new()
local started = false

local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local function remote(): RemoteEvent
	local r = Remotes:FindFirstChild("VipDaily")
	if r and r:IsA("RemoteEvent") then return r end
	local made = Instance.new("RemoteEvent")
	made.Name = "VipDaily"
	made.Parent = Remotes
	return made
end

local function push(p: Player, msg: any)
	lastPush[p] = msg
	if p.Parent then remote():FireClient(p, msg) end
end

-- when the next claim opens (0 = now), for the prompt's words
local function show(p: Player)
	local prof = profs[p]
	if not prof then return end
	local today = Data.day()
	p:SetAttribute("VipDailyNext", if prof.data.day == today then Data.nextAt(today) else 0)
end

-- the quests server (Brass), if it's in the place
local function quests(): any
	local m = script.Parent:FindFirstChild("Quests")
	if not (m and m:IsA("ModuleScript")) then return nil end
	local ok, Q = pcall(require, m)
	return if ok and type(Q) == "table" then Q else nil
end

-- containers in stock (the loot server's LootStock attribute: "bag=0;crate=1;spray=2")
local function stockOf(p: Player): { [string]: number }
	local out = {}
	local s = p:GetAttribute("LootStock")
	if type(s) == "string" then
		for k, v in string.gmatch(s, "(%a+)=(%d+)") do out[k] = tonumber(v) or 0 end
	end
	return out
end

-- what the roll needs to know about this player
local function ctxFor(p: Player): any
	return {
		live = function(kind: string, id: string): boolean return Shop.exists(kind, id) == true end,
		owns = function(kind: string, id: string): boolean return Loot.owns(p, kind, id) == true end,
		full = function(cid: string): boolean return Config.LOOT_FREE == true and (stockOf(p)[cid] or 0) >= FREE_CAP end,
		name = function(kind: string, id: string): string return (Shop.itemInfo(kind, id)) end,
	}
end

-- pay a prize (true = written by whoever keeps it)
local function pay(p: Player, prize: any, rid: string): boolean
	if prize.kind == "brass" then
		local Q = quests()
		if not Q or type(Q.giveBrass) ~= "function" then return false end
		local ok, done = pcall(Q.giveBrass, p, prize.n, rid)
		if not ok then warn("[jankfire] vip daily: giveBrass: " .. tostring(done)) end
		return ok and done == true
	end
	if type(Loot.ready) == "function" and not Loot.ready(p) then return false end
	local offer = if prize.kind == "container" then prize.cid else ("vipdaily:%s:%s"):format(prize.kind, tostring(prize.item))
	local ok, done = pcall(Loot.grant, p, offer, rid)
	if not ok then warn("[jankfire] vip daily: Loot.grant: " .. tostring(done)) end
	return ok and done == true
end

-- a prize claimed but not yet paid (a save was down): pay it now
local function settle(p: Player): boolean
	local prof = profs[p]
	if not prof or not prof.data.pending then return true end
	local pd = prof.data.pending
	if not pay(p, pd.prize, pd.rid) then return false end
	prof.data.pending = nil
	prof.dirty = true
	return true
end
local function settleSoon(p: Player)
	for _ = 1, 60 do
		if not p.Parent or not profs[p] then return end
		if settle(p) then return end
		task.wait(2)
	end
	warn("[jankfire] vip daily: couldn't pay " .. p.Name .. "'s prize yet (it's kept: next join)")
end

local function claimNow(p: Player)
	if not Vip.isVip(p) then push(p, { t = "notvip" }); return end
	local prof = profs[p]
	if not prof or (prof.state ~= "cloud" and prof.state ~= "off") then
		push(p, { t = "error", why = if prof and prof.state == "lost" then "your save opened in another server" else "still loading. try again in a moment" })
		return
	end
	local d = prof.data
	local today = Data.day()
	if d.pending and not settle(p) then
		push(p, { t = "error", why = "your last one is still on its way" })
		return
	end
	if d.day == today then show(p); push(p, { t = "later", at = Data.nextAt(today) }); return end
	if type(Loot.ready) == "function" and not Loot.ready(p) then push(p, { t = "error", why = "still loading. try again in a moment" }); return end
	local ctx = ctxFor(p)
	local prize = Data.roll(rng, ctx)
	-- (a Studio test can pick today's prize: VipDaily.test("claim", p, "spray"))
	local f = forced[p]
	if STUDIO and f and Data.byId[f] then prize = Data.prize(Data.byId[f], ctx) end
	forced[p] = nil
	local rid = ("vd-%d-%d"):format(p.UserId, today)
	-- (the day and the prize are written first: from here a second claim today is refused, here or anywhere)
	local was = d.day
	d.day = today
	d.pending = { rid = rid, prize = prize }
	prof.dirty = true
	if not Profiles.save(store, prof) then
		d.day = was
		d.pending = nil
		push(p, { t = "error", why = "couldn't save. try again" })
		return
	end
	show(p)
	local paid = pay(p, prize, rid)
	if paid then d.pending = nil end
	d.n += 1
	table.insert(d.log, { day = today, id = prize.id, item = prize.item })
	while #d.log > 30 do table.remove(d.log, 1) end
	prof.dirty = true
	task.spawn(Profiles.save, store, prof)
	push(p, { t = "won", prize = prize, reel = Data.reel(prize, rng, ctx), land = Data.LAND, late = not paid or nil })
	if not paid then task.spawn(settleSoon, p) end
end

function VipDaily.claim(p: Player)
	if busy[p] then return end
	busy[p] = true
	local ok, err = pcall(claimNow, p)
	busy[p] = nil
	if not ok then
		warn("[jankfire] vip daily: " .. tostring(err))
		push(p, { t = "error", why = "something broke. try again" })
	end
end

-- ---------------------------------------------------------------- the prompt on Trisangle's place
local function hook(spot: Instance)
	if not spot:IsA("BasePart") then return end
	if not (spot:GetAttribute("VipDaily") == true or spot:GetAttribute("Who") == "Trisangle") then return end
	-- (once only: the hub moves the prompt onto her avatar, who walks between the VIP room's seats, so the spot keeps a
	-- mark instead of the prompt)
	if spot:FindFirstChild("VipDailyPrompt") or spot:GetAttribute("VipDailyHooked") then return end
	spot:SetAttribute("VipDailyHooked", true)
	local pr = Instance.new("ProximityPrompt")
	pr.Name = "VipDailyPrompt"
	pr.ActionText = "Daily reward"
	pr.ObjectText = tostring(spot:GetAttribute("Who") or "")
	pr.KeyboardKeyCode = Enum.KeyCode.E
	pr.HoldDuration = 0
	pr.MaxActivationDistance = 8
	pr.RequiresLineOfSight = false
	pr.Parent = spot
	CollectionService:AddTag(pr, TAG)
	pr.Triggered:Connect(function(p: Player) task.spawn(VipDaily.claim, p) end)
end

-- ---------------------------------------------------------------- players
local function joined(p: Player)
	local prof = Profiles.load(store, "u" .. p.UserId, function() return p.Parent ~= nil end)
	if not prof then return end
	if not p.Parent then Profiles.release(store, prof); return end
	profs[p] = prof
	show(p)
	if prof.data.pending then task.spawn(settleSoon, p) end
end

-- ---------------------------------------------------------------- Studio test
function VipDaily.test(op: string, a: any, b: any): any
	if not STUDIO then return nil end
	if op == "claim" then
		lastPush[a] = nil
		if type(b) == "string" then forced[a] = b end
		VipDaily.claim(a)
		return lastPush[a]
	elseif op == "reset" then
		local prof = profs[a]
		if not prof then return false end
		prof.data.day = -1
		prof.dirty = true
		show(a)
		return true
	elseif op == "state" then
		local prof = profs[a]
		return if prof then { day = prof.data.day, n = prof.data.n, pending = prof.data.pending ~= nil, state = prof.state, next = a:GetAttribute("VipDailyNext") } else nil
	elseif op == "sim" then
		-- n rolls for a player who owns none of the three and has room for everything; "best" = the three counted as in
		-- the place for the run (stand-in ids where a slot has none), else counted as not made yet
		local n = tonumber(a) or 10000
		local saved = table.clone(Data.EXCLUSIVE :: any)
		if b == "best" then
			local ex = Data.EXCLUSIVE :: any
			ex.wrap = ex.wrap or "sim_wrap"; ex.hat = ex.hat or "sim_hat"; ex.skin = ex.skin or "sim_skin"
		end
		local best = b == "best"
		local ctx = { live = function() return best end, owns = function() return false end, full = function() return false end }
		local r = Random.new(17)
		local counts: { [string]: number } = {}
		for _ = 1, n do
			local pz = Data.roll(r, ctx)
			counts[pz.id] = (counts[pz.id] or 0) + 1
		end
		local ex = Data.EXCLUSIVE :: any
		ex.wrap, ex.hat, ex.skin = saved.wrap, saved.hat, saved.skin
		return counts
	end
	return nil
end

function VipDaily.start()
	if started then return end
	started = true
	remote()
	CollectionService:GetInstanceAddedSignal("HubNPC"):Connect(hook)
	for _, s in CollectionService:GetTagged("HubNPC") do hook(s) end
	Players.PlayerAdded:Connect(function(p) task.spawn(joined, p) end)
	for _, p in Players:GetPlayers() do task.spawn(joined, p) end
	Players.PlayerRemoving:Connect(function(p)
		local prof = profs[p]
		profs[p] = nil; busy[p] = nil; lastPush[p] = nil
		if prof then Profiles.release(store, prof) end
	end)
	if STUDIO then
		local bf = ServerStorage:FindFirstChild("JankVipDailyTest") :: BindableFunction?
		if not bf then
			local made = Instance.new("BindableFunction")
			made.Name = "JankVipDailyTest"
			made.Parent = ServerStorage
			bf = made
		end
		(bf :: BindableFunction).OnInvoke = function(op, a, b) return VipDaily.test(op, a, b) end
	end
end

VipDaily.start()
return VipDaily
