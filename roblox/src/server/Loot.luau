--!strict
-- LOOT: what you own (wraps, hats, skins), how many Crates / Duffel Bags / Spray Cans you have, and opening them.
-- the server owns all of it: rolls happen here only, with the web game's weights (Shared.LootTable.roll), and every
-- player's things live in one session-locked save (Profiles.luau: one server writes it at a time).
--
-- the remote ReplicatedStorage.JankfireRemotes.Loot (RemoteFunction), always answers a table { ok, why?, ... }:
--   ("inventory")          -> { free, robux, restricted, stock, owned = { wrap = {ids}, hat = {ids}, skin = {ids} },
--                               left = { kind = n }, soon = { kind = bool }, save = "loading"|"cloud"|"off"|"lost", dev }
--   ("buy", offerId, n?)   -> a shop offer (Shared.Shop): "crate" / "bag" / "spray" = n containers into your stock;
--                             "bundle_<name>" = its items; "wrap:<id>" / "hat:<id>" = one item from today's rotation.
--                             free while Config.LOOT_FREE. paid (Config.LOOT_ROBUX, off for now) goes through the
--                             shop's prompt and receipt instead (ShopReceipts.server.luau -> Loot.grant)
--   ("claim", offerId)     -> the same as buy (the shop's word for it while everything is free)
--   ("open", kind)         -> { prize, item, strip, stop, stock }: uses one from stock, or opens free (Config.LOOT_FREE)
--   ("dev", what)          -> Studio + the place's owner only: "unlock" (wear anything, this session only, nothing
--                             saved), "lock" (back to what you own), "reset" (own nothing, no stock: saved), "stock" (+5 each),
--                             "set", { wrap = {ids}, hat = {ids} } (an inventory back as it was before a test: saved)
-- player attributes for the clients: LootStock ("bag=0;crate=1;spray=2"), LootOwned (a number that goes up whenever
-- what you own changes: ask "inventory" again), LootSave.
-- the loadout asks Loot.owns() before it takes a wrap or a hat (Loadout.luau) and listens to Loot.changed.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local PolicyService = game:GetService("PolicyService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Config = require(Shared:WaitForChild("Config"))
local LootTable = require(Shared:WaitForChild("LootTable"))
local Profiles = require(script.Parent:WaitForChild("Profiles"))
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Loot") :: RemoteFunction

local Loot = {}
local CATALOG = "Shop" -- the shop's catalog in ReplicatedStorage.Jankfire (Shop.luau: offers, prices, product ids, rotation)
local TYPES = { "wrap", "hat", "skin" } -- what can be owned on Roblox today
local BUY_MAX = 10

local changed = Instance.new("BindableEvent")
Loot.changed = changed.Event -- (player): what they own changed (the loadout republishes)

local store = Profiles.new("JankfireLoot_v1", function()
	return { v = 1, inv = { wrap = {}, hat = {}, skin = {} }, stock = { crate = 0, bag = 0, spray = 0 },
		opened = { crate = 0, bag = 0, spray = 0 }, receipts = {}, since = os.time() }
end)

type State = { prof: Profiles.Profile?, owned: { [string]: { [string]: boolean } }, ready: boolean, rev: number,
	saveAt: number?, restricted: boolean, lastOpen: number, budget: number, budgetT: number, devAll: boolean }
local st: { [Player]: State } = {}
local rng = Random.new()

-- ------------------------------------------------------------------ what you own
local function sets(data: any): { [string]: { [string]: boolean } }
	local out = {}
	for _, t in TYPES do
		out[t] = {}
		local list = data.inv[t]
		if type(list) == "table" then
			for _, id in list do if type(id) == "string" and LootTable.info(t, id) then out[t][id] = true end end
		end
	end
	return out
end

function Loot.owns(p: Player, t: string, id: string): boolean
	if LootTable.isFree(t, id) then return true end
	local s = st[p]
	if s and s.devAll and LootTable.info(t, id) then return true end -- (the owner's Studio "unlock": this session only)
	local set = s and s.owned[t]
	return set ~= nil and set[id] == true
end
function Loot.ready(p: Player): boolean
	local s = st[p]
	return s ~= nil and s.ready
end
function Loot.ownedOf(p: Player): { [string]: { [string]: boolean } }
	local s = st[p]
	return if s then s.owned else {}
end

local function stockOf(s: State): { [string]: number }
	local out = { crate = 0, bag = 0, spray = 0 }
	local d = s.prof and s.prof.data
	if d then for _, k in LootTable.KINDS do out[k] = math.max(0, math.floor(tonumber(d.stock[k]) or 0)) end end
	return out
end

local function publish(p: Player)
	local s = st[p]
	if not s or not p.Parent then return end
	local stock = stockOf(s)
	p:SetAttribute("LootStock", ("bag=%d;crate=%d;spray=%d"):format(stock.bag, stock.crate, stock.spray))
	p:SetAttribute("LootOwned", s.rev)
	p:SetAttribute("LootSave", if not s.ready then "loading" elseif s.prof then s.prof.state else "off")
end

local function touch(p: Player, s: State, saveIn: number?)
	s.rev += 1
	if s.prof then s.prof.dirty = true end
	if saveIn then s.saveAt = math.min(s.saveAt or math.huge, os.clock() + saveIn) end
	publish(p)
	changed:Fire(p)
end

local function give(s: State, it: LootTable.Item)
	local d = (s.prof :: Profiles.Profile).data
	d.inv[it.type] = d.inv[it.type] or {}
	table.insert(d.inv[it.type], it.id)
	s.owned[it.type] = s.owned[it.type] or {}
	s.owned[it.type][it.id] = true
end

-- the place's owner, in Studio only (the test tools)
local function isDev(p: Player): boolean
	if not RunService:IsStudio() then return false end
	if game.CreatorType == Enum.CreatorType.User then return p.UserId == game.CreatorId end
	local ok, rank = pcall(function() return p:GetRankInGroup(game.CreatorId) end)
	return ok and rank == 255
end

local function catalog(): any
	local m = Shared:FindFirstChild(CATALOG)
	if not m or not m:IsA("ModuleScript") then return nil end
	local ok, c = pcall(require, m)
	return if ok and type(c) == "table" then c else nil
end

local function addStock(s: State, grant: { [string]: number })
	local d = (s.prof :: Profiles.Profile).data
	for kind, n in grant do
		if LootTable.CONTAINERS[kind] and type(n) == "number" and n > 0 then d.stock[kind] = (tonumber(d.stock[kind]) or 0) + math.floor(n) end
	end
end

-- a shop offer, given: a container = one more in stock (n of them), a bundle / single = its items (the ones you lack).
-- returns the items it gave
local function grantOffer(s: State, o: any, n: number?): { LootTable.Item }
	local got = {}
	if o.type == "container" then
		if LootTable.CONTAINERS[o.id] then addStock(s, { [o.id] = n or 1 }) end
		return got
	end
	local c = catalog()
	local items = if c and type(c.contents) == "function" then c.contents(o) else {}
	for _, it in items do
		local i = LootTable.info(it.kind, it.id)
		if i and i.rarity ~= "free" and not (s.owned[i.type] and s.owned[i.type][i.id]) then
			give(s, i)
			table.insert(got, i)
		end
	end
	return got
end

-- ------------------------------------------------------------------ the remote
local function spend(s: State): boolean
	local t = os.clock()
	s.budget = math.min(20, s.budget + (t - s.budgetT) * 4); s.budgetT = t
	if s.budget < 1 then return false end
	s.budget -= 1
	return true
end

local function inventory(p: Player, s: State): any
	local owned = {}
	for _, t in TYPES do
		local ids = {}
		for id in s.owned[t] or {} do table.insert(ids, id) end
		table.sort(ids)
		owned[t] = ids
	end
	local left, soon = {}, {}
	for _, k in LootTable.KINDS do
		local o = LootTable.odds(k, s.owned)
		left[k], soon[k] = o.left, o.soon
	end
	return { ok = true, free = Config.LOOT_FREE == true, robux = Config.LOOT_ROBUX == true, restricted = s.restricted,
		stock = stockOf(s), owned = owned, left = left, soon = soon,
		inv = { wrap = owned.wrap, hat = owned.hat, skin = owned.skin, stock = stockOf(s) },
		save = if not s.ready then "loading" elseif s.prof then s.prof.state else "off", dev = isDev(p), devAll = s.devAll }
end

local function handle(p: Player, op: unknown, a: unknown, b: unknown): any
	local s = st[p]
	if not s then return { ok = false, why = "still loading" } end
	if not spend(s) then return { ok = false, why = "slow down" } end
	if op == "inventory" then return inventory(p, s) end
	if not s.ready or not s.prof then return { ok = false, why = "your stuff is still loading" } end
	if s.prof.state == "lost" then return { ok = false, why = "your stuff opened in another server" } end
	local d = s.prof.data

	if op == "buy" or op == "claim" then
		-- a shop offer by id: "crate" / "bag" / "spray" (a container into your stock; count 1..10), "bundle_<name>"
		-- (a fixed set of items), "wrap:<id>" / "hat:<id>" (a single, only while it is in today's rotation)
		local c = catalog()
		local o = if c and type(c.offer) == "function" and type(a) == "string" then c.offer(a) else nil
		if not o and type(a) == "string" and LootTable.CONTAINERS[a] then o = { id = a, type = "container", robux = 0 } end
		if type(o) ~= "table" then return { ok = false, why = "that isn't for sale" } end
		if o.type == "single" and c and type(c.onSale) == "function" and not c.onSale(a) then return { ok = false, why = "that one's not in today's shop" } end
		local n = if o.type == "container" and type(b) == "number" and b == math.floor(b) then b else 1
		if n < 1 or n > BUY_MAX then return { ok = false, why = ("1 to %d at a time"):format(BUY_MAX) } end
		if Config.LOOT_ROBUX and (o.robux or 0) > 0 then
			-- (paid: the shop's prompt and receipt, ShopReceipts.server.luau -> Loot.grant)
			return { ok = false, why = "that one costs robux now" }
		end
		if not Config.LOOT_FREE and (o.robux or 0) > 0 then return { ok = false, why = "the shop is shut" } end
		if o.type ~= "container" and c and type(c.contents) == "function" then
			local missing = 0
			for _, it in c.contents(o) do if not Loot.owns(p, it.kind, it.id) then missing += 1 end end
			if missing == 0 then return { ok = false, why = "you have all of that already" } end
		end
		local got = grantOffer(s, o, n)
		touch(p, s, if o.type == "container" then 10 else 3)
		local items = {}
		for _, i in got do table.insert(items, { kind = i.type, type = i.type, id = i.id, name = i.name, rarity = i.rarity }) end
		return { ok = true, stock = stockOf(s), items = items }

	elseif op == "open" then
		if type(a) ~= "string" or not LootTable.CONTAINERS[a] then return { ok = false, why = "no such container" } end
		local now = os.clock()
		if now - s.lastOpen < 0.6 then return { ok = false, why = "slow down" } end
		local have = math.floor(tonumber(d.stock[a]) or 0)
		if have <= 0 and not Config.LOOT_FREE then return { ok = false, why = ("no %s left"):format(string.lower(LootTable.CONTAINERS[a].plural)) } end
		local prize, why = LootTable.roll(a, s.owned, rng)
		if not prize then
			return { ok = false, why = if why == "soon" then "coming soon: nothing in it is on roblox yet" else "you own everything in it already" }
		end
		s.lastOpen = now
		if have > 0 then d.stock[a] = have - 1 end
		d.opened[a] = (tonumber(d.opened[a]) or 0) + 1
		give(s, prize)
		touch(p, s, 3)
		local cards, stop = LootTable.strip(a, prize, rng)
		local strip = table.create(#cards)
		for i, c in cards do strip[i] = { type = c.type, id = c.id, name = c.name, rarity = c.rarity } end
		return { ok = true, prize = { type = prize.type, id = prize.id, name = prize.name, rarity = prize.rarity, kind = a, weapon = prize.weapon },
			item = { kind = prize.type, id = prize.id, name = prize.name, rarity = prize.rarity },
			strip = strip, stop = stop, stock = stockOf(s), usedStock = have > 0 }

	elseif op == "dev" then
		if not isDev(p) then return { ok = false, why = "nope" } end
		if a == "unlock" then
			-- (wear anything, this session only: nothing is saved, and containers still roll on what you really own)
			s.devAll = true
		elseif a == "lock" then
			s.devAll = false
		elseif a == "reset" then
			d.inv = { wrap = {}, hat = {}, skin = {} }
			d.stock = { crate = 0, bag = 0, spray = 0 }
			s.owned = sets(d)
		elseif a == "stock" then
			addStock(s, { crate = 5, bag = 5, spray = 5 })
		elseif a == "set" and type(b) == "table" then
			-- (put an inventory back as it was before a test: { wrap = {ids}, hat = {ids}, skin = {ids} })
			local inv = { wrap = {}, hat = {}, skin = {} }
			for _, t in TYPES do
				local list = (b :: any)[t]
				if type(list) == "table" then
					for _, id in list do if LootTable.info(t, id) and not table.find(inv[t], id) then table.insert(inv[t], id) end end
				end
			end
			d.inv = inv
			s.owned = sets(d)
		else
			return { ok = false, why = "unlock, lock, reset, stock or set" }
		end
		touch(p, s, 2)
		return inventory(p, s)
	end
	return { ok = false, why = "nope" }
end

Remote.OnServerInvoke = function(p: Player, op: unknown, a: unknown, b: unknown)
	local ok, res = pcall(handle, p, op, a, b)
	if not ok then
		warn("[jankfire] loot: " .. tostring(res))
		return { ok = false, why = "something broke. try again" }
	end
	return res
end

-- ------------------------------------------------------------------ Robux (Config.LOOT_ROBUX; off while testing)
-- the shop's ShopReceipts.server.luau owns Roblox's prompt and ProcessReceipt (one script may set it); when a receipt
-- comes it calls Loot.grant. a purchase only counts once it is written: the purchase id is saved with what it gave, so
-- a receipt Roblox sends twice (a crash before it heard back) gives once. false = not written: Roblox asks again later
function Loot.grant(p: Player, offerId: string, purchaseId: any): boolean
	local s = st[p]
	if not s or not s.ready or not s.prof or (s.prof.state ~= "cloud" and s.prof.state ~= "off") then return false end
	local prof = s.prof :: Profiles.Profile
	local d = prof.data
	local id = tostring(purchaseId)
	if table.find(d.receipts, id) then return true end
	local c = catalog()
	local o = if c and type(c.offer) == "function" and type(offerId) == "string" then c.offer(offerId) else nil
	if not o and type(offerId) == "string" and LootTable.CONTAINERS[offerId] then o = { id = offerId, type = "container" } end
	if type(o) ~= "table" then
		warn(("[jankfire] loot: grant of %s: no such offer"):format(tostring(offerId)))
		return false
	end
	local before = { stock = table.clone(d.stock), inv = {} :: any }
	for t, list in d.inv do before.inv[t] = table.clone(list) end
	grantOffer(s, o, 1)
	table.insert(d.receipts, id)
	while #d.receipts > 100 do table.remove(d.receipts, 1) end
	prof.dirty = true
	if not Profiles.save(store, prof) then
		-- not written: take it back
		d.stock, d.inv = before.stock, before.inv
		s.owned = sets(d)
		local i = table.find(d.receipts, id)
		if i then table.remove(d.receipts, i) end
		return false
	end
	touch(p, s)
	return true
end

-- may this player buy random items with Robux? (Roblox's PolicyService: false for some ages and countries)
function Loot.restricted(p: Player): boolean
	local s = st[p]
	return s == nil or s.restricted
end

-- ------------------------------------------------------------------ what you wore before
-- wraps and hats were free to wear before they had to be won: whatever is in your saved loadout (Loadout.luau hands it
-- over when it loads) becomes yours, once per player (data.migrated), so turning ownership on took nothing off anyone.
-- after that the loadout only saves what you own, so this can never give anything new
local oldPicks: { [Player]: { { type: string, id: string } } } = {}
local function applyOld(p: Player, s: State)
	local items = oldPicks[p]
	local prof = s.prof
	if not items or not prof then return end
	oldPicks[p] = nil
	if prof.data.migrated then return end
	for _, x in items do
		local i = LootTable.info(x.type, x.id)
		if i and i.rarity ~= "free" and not (s.owned[i.type] and s.owned[i.type][i.id]) then give(s, i) end
	end
	prof.data.migrated = true
	touch(p, s, 5)
end
function Loot.grandfather(p: Player, items: { { type: string, id: string } })
	oldPicks[p] = items
	local s = st[p]
	if s and s.ready then applyOld(p, s) end
end

-- ------------------------------------------------------------------ players
local function added(p: Player)
	if st[p] then return end
	local s: State = { prof = nil, owned = { wrap = {}, hat = {}, skin = {} }, ready = false, rev = 0, saveAt = nil,
		restricted = true, lastOpen = 0, budget = 20, budgetT = os.clock(), devAll = false } -- (restricted until Roblox says otherwise)
	st[p] = s
	publish(p)
	task.spawn(function()
		local ok, pol = pcall(function() return PolicyService:GetPolicyInfoForPlayerAsync(p) end)
		if ok and type(pol) == "table" then s.restricted = pol.ArePaidRandomItemsRestricted == true end
	end)
	local prof = Profiles.load(store, "u" .. p.UserId, function() return p.Parent ~= nil and st[p] == s end)
	if not prof then return end
	if st[p] ~= s then Profiles.release(store, prof); return end
	s.prof = prof
	s.owned = sets(prof.data)
	s.ready = true
	prof.onLost.Event:Connect(function()
		if p.Parent then p:Kick("your JANKFIRE stuff was opened in another server. rejoin to carry on") end
	end)
	s.rev += 1
	publish(p)
	changed:Fire(p)
	applyOld(p, s)
end

function Loot.init()
	for _, p in Players:GetPlayers() do task.spawn(added, p) end
	Players.PlayerAdded:Connect(added)
	Players.PlayerRemoving:Connect(function(p)
		local s = st[p]
		st[p] = nil
		oldPicks[p] = nil
		if s and s.prof then Profiles.release(store, s.prof) end
	end)
	-- an open is saved a few seconds after it lands (a burst of opens is one write)
	local acc = 0
	RunService.Heartbeat:Connect(function(dt)
		acc += dt
		if acc < 1 then return end
		acc = 0
		local t = os.clock()
		for p, s in st do
			if s.saveAt and t >= s.saveAt and s.prof and s.prof.state == "cloud" then
				s.saveAt = nil
				task.spawn(Profiles.save, store, s.prof)
			end
		end
	end)
end

return Loot
