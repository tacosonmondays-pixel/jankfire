--!strict
-- LOOT: what you own (wraps, hats, skins), how many Crates / Duffel Bags / Spray Cans you have, and opening them.
-- a wrap or a hat is owned for ONE gun (the owner, 16 Nov: "spray cans should give you a wrap for only one gun at a
-- time! some with the charms/hats"): keys "<id>@<weapon>" (LootTable.key); a weapon skin is already one gun's.
-- the server owns all of it: rolls happen here only, with the web game's weights (Shared.LootTable.roll), and every
-- player's things live in one session-locked save (Profiles.luau: one server writes it at a time).
--
-- the remote ReplicatedStorage.JankfireRemotes.Loot (RemoteFunction), always answers a table { ok, why?, ... }:
--   ("inventory")          -> { free, robux, restricted, stock, owned = { wrap = {"id@gun"}, hat = {"id@gun"}, skin = {ids} },
--                               left = { kind = n }, soon = { kind = bool }, save = "loading"|"cloud"|"off"|"lost", dev }
--   ("buy", offerId, n?)   -> a shop offer (Shared.Shop): "crate" / "bag" / "spray" = n containers into your stock;
--                             "bundle_<name>" = its items; "wrap:<id>" / "hat:<id>" = one item from today's rotation.
--                             free while Config.LOOT_FREE. paid (Config.LOOT_ROBUX, off for now) goes through the
--                             shop's prompt and receipt instead (ShopReceipts.server.luau -> Loot.grant)
--   ("claim", offerId)     -> the same as buy (the shop's word for it while everything is free)
--   ("open", kind, n?)     -> n = 1 / 5 / 10 at once: { prize, item, strip, stop (the first), prizes, items, strips, stops,
--                             n, stock }: uses stock first, or opens free (Config.LOOT_FREE). others nearby see it
--                             (the LootShow event) unless you turned that off: ("setting", "showOpenings", false)
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
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local Remote = Remotes:WaitForChild("Loot") :: RemoteFunction
-- the openings others see (LootShow.client.luau draws them): made here if the place doesn't have it yet
local Show = Remotes:FindFirstChild("LootShow") :: RemoteEvent?
if not Show then
	local e = Instance.new("RemoteEvent")
	e.Name = "LootShow"
	e.Parent = Remotes
	Show = e
end
local SHOW_RANGE = 160 -- studs: players further away than this don't get the event

local Loot = {}
local CATALOG = "Shop" -- the shop's catalog in ReplicatedStorage.Jankfire (Shop.luau: offers, prices, product ids, rotation)
local function TYPES(): { string } return LootTable.ownTypes() end -- what can be owned on Roblox today
local BUY_MAX = 10

local changed = Instance.new("BindableEvent")
Loot.changed = changed.Event -- (player): what they own changed (the loadout republishes)

local store = Profiles.new("JankfireLoot_v1", function()
	-- (v 2: wraps and hats are "<id>@<weapon>" pairs; v 1 had bare ids, owned on every gun: migrate() below)
	return { v = 2, inv = { wrap = {}, hat = {}, skin = {} }, stock = { crate = 0, bag = 0, spray = 0 },
		opened = { crate = 0, bag = 0, spray = 0 }, receipts = {}, since = os.time(),
		settings = { showOpenings = true } } -- (others see your openings: Settings [P])
end)

type State = { prof: Profiles.Profile?, owned: { [string]: { [string]: boolean } }, ready: boolean, rev: number,
	saveAt: number?, restricted: boolean, lastOpen: number, budget: number, budgetT: number, devAll: boolean }
local st: { [Player]: State } = {}
local rng = Random.new()

-- ------------------------------------------------------------------ what you own
-- (wraps and hats are owned one gun at a time: their keys are "<id>@<weapon>"; a skin's key is its id)
local function sets(data: any): { [string]: { [string]: boolean } }
	local out = {}
	for _, t in TYPES() do
		out[t] = {}
		local list = data.inv[t]
		if type(list) == "table" then
			for _, k in list do
				local i = LootTable.pairInfo(t, k)
				if i then out[t][i.key] = true end
			end
		end
	end
	return out
end

-- a save from before wraps and hats were won one gun at a time (v 1: bare ids, worn on every gun) becomes pairs on
-- every gun that takes it, so nobody loses anything (16 Nov 2026: only that day's test saves had v 1)
local function migrate(data: any)
	if (tonumber(data.v) or 1) >= 2 then return end
	for _, t in { "wrap", "hat" } do
		local out, seen = {}, {}
		for _, k in (if type(data.inv[t]) == "table" then data.inv[t] else {}) do
			local id, w = LootTable.split(k)
			local guns = if w then { w } else LootTable.weapons(t)
			for _, g in guns do
				local i = LootTable.pairInfo(t, LootTable.key(t, id :: string, g))
				if i and not seen[i.key] then seen[i.key] = true; table.insert(out, i.key) end
			end
		end
		data.inv[t] = out
	end
	data.v = 2
end

-- does this player own this cosmetic on this gun? free things: yes, everywhere. no gun given: on any gun
function Loot.owns(p: Player, t: string, id: string, weapon: string?): boolean
	if LootTable.isFree(t, id) then return true end
	local s = st[p]
	if not s then return false end
	if s.devAll and LootTable.info(t, id) then return true end -- (the owner's Studio "unlock": every pair, this session only)
	local set = s.owned[t]
	if not set then return false end
	if t == "skin" or weapon then return set[LootTable.key(t, id, weapon)] == true end
	for k in set do if LootTable.split(k) == id then return true end end
	return false
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
	local set = s.prof and s.prof.data.settings
	p:SetAttribute("LootShowOpenings", not (type(set) == "table" and set.showOpenings == false))
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
	local key = LootTable.key(it.type, it.id, it.weapon)
	d.inv[it.type] = d.inv[it.type] or {}
	table.insert(d.inv[it.type], key)
	s.owned[it.type] = s.owned[it.type] or {}
	s.owned[it.type][key] = true
end
-- the pairs a shop item stands for: { kind, id, weapon } is one pair; with no weapon (an old-style bundle) every gun
local function pairsOf(it: any): { LootTable.Item }
	local out = {}
	if type(it) ~= "table" or type(it.kind) ~= "string" or type(it.id) ~= "string" then return out end
	local guns = if it.kind == "skin" then { "" } elseif type(it.weapon) == "string" then { it.weapon } else LootTable.weapons(it.kind)
	for _, g in guns do
		local i = LootTable.pairInfo(it.kind, LootTable.key(it.kind, it.id, if g ~= "" then g else nil))
		if i then table.insert(out, i) end
	end
	return out
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
		for _, i in pairsOf(it) do
			if i.rarity ~= "free" and not (s.owned[i.type] and s.owned[i.type][i.key]) then
				give(s, i)
				table.insert(got, i)
			end
		end
	end
	return got
end

-- ------------------------------------------------------------------ others see your openings
-- the owner, 16 Nov: "when they're on the ground, other people can see it and what you get! you can disable that
-- option in the settings like hide it from other people". after an open, everyone else within SHOW_RANGE studs gets
-- one small event: where the container lands (in front of you, as the server sees you), what it was and what came out.
-- their client draws the container, the pop and the prize over it (no reel). off in Settings = nothing is sent.
local function spotOf(p: Player, ahead: number?, side: number?): CFrame?
	local ch = p.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not root then return nil end
	local look = root.CFrame.LookVector
	local flat = Vector3.new(look.X, 0, look.Z)
	flat = if flat.Magnitude > 1e-3 then flat.Unit else Vector3.new(0, 0, -1)
	local right = flat:Cross(Vector3.yAxis)
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { ch :: Instance }
	local from = root.Position + Vector3.new(0, 0.5, 0)
	local dist = ahead or 7.5
	local hit = workspace:Raycast(from, flat * (dist + 2.5), params)
	if hit then dist = math.max(3.2, hit.Distance - 2.5) end
	local spot = from + flat * dist + right * (side or 0)
	local down = workspace:Raycast(spot + Vector3.new(0, 5, 0), Vector3.new(0, -24, 0), params)
	local y = if down then down.Position.Y else root.Position.Y - 3
	local g = Vector3.new(spot.X, y, spot.Z)
	return CFrame.lookAt(g, g - flat) * CFrame.Angles(0, math.rad(-20), 0)
end
local function showData(p: Player, kind: string, prizes: { any }, cf: CFrame): any
	local list = {}
	for i, q in prizes do
		if i > 10 then break end
		list[i] = { type = q.type, id = q.id, weapon = q.weapon, name = q.name, rarity = q.rarity }
	end
	return { uid = p.UserId, who = p.DisplayName, kind = kind, cf = cf, prizes = list, n = #prizes }
end
local function broadcast(p: Player, s: State, kind: string, prizes: { any })
	local set = s.prof and s.prof.data.settings
	if type(set) == "table" and set.showOpenings == false then return end
	local cf = spotOf(p)
	if not cf or not Show then return end
	local data = showData(p, kind, prizes, cf)
	for _, q in Players:GetPlayers() do
		if q ~= p then
			local qr = q.Character and q.Character:FindFirstChild("HumanoidRootPart") :: BasePart?
			if qr and (qr.Position - cf.Position).Magnitude <= SHOW_RANGE then (Show :: RemoteEvent):FireClient(q, data) end
		end
	end
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
	for _, t in TYPES() do
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
		save = if not s.ready then "loading" elseif s.prof then s.prof.state else "off", dev = isDev(p), devAll = s.devAll,
		showOpenings = not (s.prof ~= nil and type(s.prof.data.settings) == "table" and s.prof.data.settings.showOpenings == false) }
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
			for _, it in c.contents(o) do
				for _, i in pairsOf(it) do if i.rarity ~= "free" and not (s.owned[i.type] and s.owned[i.type][i.key]) then missing += 1 end end
			end
			if missing == 0 then return { ok = false, why = "you have all of that already" } end
		end
		local got = grantOffer(s, o, n)
		touch(p, s, if o.type == "container" then 10 else 3)
		local items = {}
		for _, i in got do table.insert(items, { kind = i.type, type = i.type, id = i.id, weapon = i.weapon, key = i.key, name = i.name, rarity = i.rarity }) end
		return { ok = true, stock = stockOf(s), items = items }

	elseif op == "open" then
		-- ("open", kind, n): n = 1, 5 or 10 at once, rolled one after another in this one request (the same odds, and
		-- never a pair twice: each prize is yours before the next roll). fewer left than n: as many as there are
		if type(a) ~= "string" or not LootTable.CONTAINERS[a] then return { ok = false, why = "no such container" } end
		local n = if b == 5 then 5 elseif b == 10 then 10 else 1
		local now = os.clock()
		if now - s.lastOpen < (if n > 1 then 1.2 else 0.6) then return { ok = false, why = "slow down" } end
		local have = math.floor(tonumber(d.stock[a]) or 0)
		if have < n and not Config.LOOT_FREE then
			return { ok = false, why = if have <= 0 then ("no %s left"):format(string.lower(LootTable.CONTAINERS[a].plural)) else ("you only have %d"):format(have) }
		end
		local prizes = {}
		for i = 1, n do
			local prize, why = LootTable.roll(a, s.owned, rng)
			if not prize then
				if i == 1 then
					return { ok = false, why = if why == "soon" then "coming soon: nothing in it is on roblox yet" else "you own everything in it already" }
				end
				break
			end
			give(s, prize)
			table.insert(prizes, prize)
		end
		s.lastOpen = now
		local used = math.min(have, #prizes)
		d.stock[a] = have - used
		d.opened[a] = (tonumber(d.opened[a]) or 0) + #prizes
		touch(p, s, 3)
		local function slim(c: any): any
			return { type = c.type, id = c.id, weapon = c.weapon, key = c.key, name = c.name, rarity = c.rarity }
		end
		local strips, stops, list, items = {}, {}, {}, {}
		for i, q in prizes do
			local cards, stop = LootTable.strip(a, q, rng, if #prizes > 1 then LootTable.STRIP_QUICK else nil)
			local strip = table.create(#cards)
			for j, c in cards do strip[j] = slim(c) end
			strips[i], stops[i] = strip, stop
			list[i] = slim(q)
			items[i] = { kind = q.type, id = q.id, weapon = q.weapon, key = q.key, name = q.name, rarity = q.rarity }
		end
		broadcast(p, s, a, prizes)
		local first = prizes[1]
		return { ok = true, n = #prizes, short = #prizes < n,
			prize = { type = first.type, id = first.id, weapon = first.weapon, key = first.key, name = first.name, rarity = first.rarity, kind = a },
			item = items[1], strip = strips[1], stop = stops[1],
			prizes = list, items = items, strips = strips, stops = stops,
			stock = stockOf(s), usedStock = used > 0, used = used }

	elseif op == "setting" then
		-- ("setting", "showOpenings", on): others see your openings or not (Settings [P]); saved with your things
		if a ~= "showOpenings" or type(b) ~= "boolean" then return { ok = false, why = "nope" } end
		d.settings = if type(d.settings) == "table" then d.settings else {}
		d.settings.showOpenings = b
		touch(p, s, 5)
		return { ok = true, showOpenings = b }

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
		elseif a == "show" then
			-- (what others see when you open, sent to you yourself, a few studs to the side: nothing is given.
			-- ("dev", "show", { kind = "spray", n = 1, ahead = 9, side = 6 }))
			local o = if type(b) == "table" then b :: any else {}
			local kind = if type(o.kind) == "string" and LootTable.CONTAINERS[o.kind] then o.kind else "spray"
			local pool = LootTable.pool(kind)
			if #pool == 0 or not Show then return { ok = false, why = "nothing to show" } end
			local cf = spotOf(p, tonumber(o.ahead) or 9, tonumber(o.side) or 6)
			if not cf then return { ok = false, why = "no character" } end
			local prizes = {}
			local count = math.clamp(math.floor(tonumber(o.n) or 1), 1, 10)
			for i = 1, count do
				local q = pool[rng:NextInteger(1, #pool)]
				if type(o.rarity) == "string" and i == 1 then
					for _, x in pool do if x.rarity == o.rarity then q = x; break end end
				end
				prizes[i] = q
			end
			(Show :: RemoteEvent):FireClient(p, showData(p, kind, prizes, cf))
			return { ok = true }
		elseif a == "set" and type(b) == "table" then
			-- (put an inventory back as it was before a test: { wrap = {keys}, hat = {keys}, skin = {ids} })
			local inv = { wrap = {}, hat = {}, skin = {} }
			for _, t in TYPES() do
				local list = (b :: any)[t]
				if type(list) == "table" then
					for _, k in list do
						local i = LootTable.pairInfo(t, k)
						if i and not table.find(inv[t], i.key) then table.insert(inv[t], i.key) end
					end
				end
			end
			d.inv = inv
			s.owned = sets(d)
		else
			return { ok = false, why = "unlock, lock, reset, stock, set or show" }
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
local oldPicks: { [Player]: { { type: string, id: string, weapon: string? } } } = {}
local function applyOld(p: Player, s: State)
	local items = oldPicks[p]
	local prof = s.prof
	if not items or not prof then return end
	oldPicks[p] = nil
	if prof.data.migrated then return end
	for _, x in items do
		local i = LootTable.pairInfo(x.type, LootTable.key(x.type, x.id, x.weapon))
		if i and i.rarity ~= "free" and not (s.owned[i.type] and s.owned[i.type][i.key]) then give(s, i) end
	end
	prof.data.migrated = true
	touch(p, s, 5)
end
function Loot.grandfather(p: Player, items: { { type: string, id: string, weapon: string? } })
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
	migrate(prof.data)
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
