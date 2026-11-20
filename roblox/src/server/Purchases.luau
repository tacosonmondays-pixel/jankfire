--!strict
-- what a player has bought for good that isn't loot (18 Nov 2026, the owner: "buying weapons with coins make sure thats
-- a thing"), and the record of every Robux receipt the shop has granted.
--   the Robux weapons (Unlocks.ROBUX, prices in Shop.MONEY.weapons): bought once and kept, with Robux (a developer
--   product, "weapon:<id>", granted by ShopReceipts.server.luau) or with Brass (the quests' soft currency: taken by the
--   server here, through Quests.spendBrass, never by a client). the player attribute RobuxOwned ("laser,minigun") is
--   set here only; Unlocks.forPlayer reads it on both sides.
--   the receipts: ShopReceipts asks Purchases.seen(p, purchaseId) first and marks each one it granted, so a receipt
--   Roblox sends again is granted once (every grant behind it is idempotent by the purchase id too: Loot, Deals,
--   Quests.buyBrass and giveWeapon here).
-- one session-locked save per player (Profiles.luau): "JankfirePurchases_v1", and "JankfirePurchases_v1_studio" in
-- Studio (Profiles adds it), never the live one.
-- a Brass buy is three writes: a pending mark here, the Brass in the quests' save, then the weapon here. a crash between
-- them is settled on the next join (Quests.spent says whether the Brass was taken: the weapon, or the mark dropped).
-- for other server scripts:
--   Purchases.ready(p) -> boolean                         the save is loaded
--   Purchases.owns(p, wid) -> boolean
--   Purchases.seen(p, purchaseId) -> boolean              a receipt already granted
--   Purchases.mark(p, purchaseId, key) -> boolean         remember a granted receipt (written)
--   Purchases.giveWeapon(p, wid, how, id) -> (ok, why?)   how "robux" | "brass" | "gift"; true once written
--   Purchases.unlockWeapons(p, wids, how, id) -> (ok, new, why?)  the owner's UNLOCKS: any locked live weapon (a Robux
--                                                         one or a level one), many in one write; Purchases.lockable(wid)
--   Purchases.buyWithBrass(p, wid) -> { ok, why?, wid? }  the Brass buy (the remote's "brass")
-- the remote JankfireRemotes.Purchases (RemoteFunction, made here):
--   ("state")        -> { ok, owned = { [wid] = true }, free = Unlocks.robuxFree() }
--   ("brass", wid)   -> Purchases.buyWithBrass
--   ("coins", offerId, n?) -> Purchases.buyWithCoins: in the coins-only shop (Shop.coinsOnly), a single on sale today, n
--                      containers (1, 5 or 10; never where Roblox's policy restricts paid random items) or one of your
--                      deals ("deal:<skin>"), for coins. same three writes as a weapon: a pending mark, the coins
--                      (Quests.spendBrass), the grant (Loot.grant / Deals.grant, idempotent by the id); settled on join
--   ("dev", "forget", wid) -> Studio + the place's owner only: takes a bought weapon back (to undo a test)
--   ("early", wid)   -> Purchases.buyEarly: a weapon that opens at a level, bought with coins before then (Shop.earlyOn)
--   ("pick", purchaseId, skinId) -> Purchases.pick: the skin chosen for a big coin pack's waiting pick ("coins": the
--                      coins instead, when every skin on its list is owned)
--   ("dev", "extras") / ("dev", "forgetExtras") -> Studio + the owner: their extras records / cleared (a test undone)
-- the big coin packs' extras (Shop.packExtrasOn): Purchases.packExtras(p, pack, purchaseId) -> boolean, from a coin
-- pack's receipt (ShopReceipts) or a gifted one (Gifts). the player attribute PackPicks ("<purchaseId>:<kind>,...")
-- lists the picks still waiting
-- docs: roblox/docs/MONEY.md
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Shop = require(Shared:WaitForChild("Shop")) :: any
local Unlocks = require(Shared:WaitForChild("Unlocks")) :: any
local Profiles = require(script.Parent:WaitForChild("Profiles"))

local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
if not Remotes:FindFirstChild("Purchases") then
	local r = Instance.new("RemoteFunction")
	r.Name = "Purchases"
	r.Parent = Remotes
end
local Remote = Remotes:WaitForChild("Purchases") :: RemoteFunction

local Purchases = {}
local RECEIPTS_KEPT = 500 -- (the newest; older ones still can't pay twice: every grant is idempotent by its id)

local function template(): any
	return { v = 1, weapons = {}, receipts = {}, order = {}, pending = {}, extras = {}, extrasOrder = {} }
end
local store = Profiles.new("JankfirePurchases_v1", template)

type State = { prof: Profiles.Profile?, ready: boolean, busy: boolean, budget: number, budgetT: number }
local st: { [Player]: State } = {}

-- the quests server (the Brass wallet), when it's in the place
local function quests(): any
	local m = script.Parent:FindFirstChild("Quests")
	if not (m and m:IsA("ModuleScript")) then return nil end
	local ok, Q = pcall(require, m)
	return if ok and type(Q) == "table" then Q else nil
end
-- another server module, when it's in the place (the loot server, the deals)
local function module(name: string): any
	local m = script.Parent:FindFirstChild(name)
	if not (m and m:IsA("ModuleScript")) then return nil end
	local ok, M = pcall(require, m)
	return if ok and type(M) == "table" then M else nil
end
-- hand over a coins buy (idempotent by its id: a second call finds it given)
local function grantCoinsBuy(p: Player, e: any, id: string): boolean
	local dskin = if type(e.offer) == "string" then string.match(e.offer, "^deal:([%w_]+)$") else nil
	if dskin then
		local D = module("Deals")
		if not D or type(D.grant) ~= "function" then return false end
		local ok, res = pcall(D.grant, p, dskin, id)
		return ok and res == true
	end
	local L = module("Loot")
	if not L or type(L.grant) ~= "function" then return false end
	local ok, res = pcall(L.grant, p, e.offer, id, if (tonumber(e.n) or 1) > 1 then e.n else nil)
	return ok and res == true
end

-- the place's owner, in Studio only (the loot server's and Vip's rule)
local function isDev(p: Player): boolean
	if not RunService:IsStudio() then return false end
	if game.CreatorType == Enum.CreatorType.User then return p.UserId == game.CreatorId end
	local ok, rank = pcall(function() return p:GetRankInGroup(game.CreatorId) end)
	return ok and rank == 255
end

local function dataOf(p: Player): any
	local s = st[p]
	return if s and s.ready and s.prof then s.prof.data else nil
end

local function forSale(wid: any): boolean
	return type(wid) == "string" and (Shop.MONEY.weapons :: any)[wid] ~= nil and Unlocks.robux(wid)
end

local function publish(p: Player)
	if not p.Parent then return end
	local d = dataOf(p)
	local list = {}
	if d then for wid in d.weapons do table.insert(list, wid) end end
	table.sort(list)
	p:SetAttribute("RobuxOwned", if #list > 0 then table.concat(list, ",") else nil)
end

-- write now (true once it's in the store; a Studio session without API access counts as written)
local function write(s: State): boolean
	local prof = s.prof :: Profiles.Profile
	prof.dirty = true
	return if prof.state == "cloud" then Profiles.save(store, prof) else prof.state == "off"
end

function Purchases.ready(p: Player): boolean return dataOf(p) ~= nil end
function Purchases.owns(p: Player, wid: string): boolean
	local d = dataOf(p)
	return d ~= nil and d.weapons[wid] ~= nil
end
function Purchases.seen(p: Player, purchaseId: any): boolean
	local d = dataOf(p)
	return d ~= nil and d.receipts[tostring(purchaseId)] ~= nil
end
function Purchases.mark(p: Player, purchaseId: any, key: any): boolean
	local s = st[p]
	local d = dataOf(p)
	if not s or not d then return false end
	local k = tostring(purchaseId)
	if d.receipts[k] then return true end
	d.receipts[k] = { t = os.time(), k = string.sub(tostring(key), 1, 60) }
	table.insert(d.order, k)
	while #d.order > RECEIPTS_KEPT do d.receipts[table.remove(d.order, 1)] = nil end
	return write(s)
end

-- the weapon, for good. idempotent: one they own already answers true, "already"
function Purchases.giveWeapon(p: Player, wid: string, how: string, id: string?): (boolean, string?)
	local s = st[p]
	local d = dataOf(p)
	if not s or not d then return false, "loading" end
	if not forSale(wid) then return false, "not a weapon the shop sells" end
	if d.weapons[wid] then return true, "already" end
	d.weapons[wid] = { t = os.time(), how = how, id = id }
	if not write(s) then
		d.weapons[wid] = nil
		return false, "couldn't save"
	end
	publish(p)
	print(("[jankfire] purchases: %s has the %s (%s)"):format(p.Name, wid, how))
	return true, nil
end

-- the owner's UNLOCKS (19 Nov 2026, OwnerDev.server's GIFT tab: "I want to be able to unlock stuff for my friends!!"):
-- weapons opened for good, the way an early coin unlock or a bought Robux weapon is (data.weapons: RobuxOwned, which
-- Unlocks treats as open whatever the level). any live weapon that has a lock: a Robux one, or one that opens past
-- level 1. the whole list in one write; the ones they have already are skipped. -> (ok, how many were new, why?)
function Purchases.lockable(wid: any): boolean
	local Roster = require(Shared:WaitForChild("Roster")) :: any
	local e = type(wid) == "string" and Roster.byId[wid]
	return e ~= nil and e ~= false and e.live == true and (Unlocks.robux(wid) or Unlocks.level(wid) > 1)
end
function Purchases.unlockWeapons(p: Player, wids: { string }, how: string, id: string?): (boolean, number, string?)
	local s = st[p]
	local d = dataOf(p)
	if not s or not d then return false, 0, "loading" end
	local new = {}
	for _, wid in wids do
		if Purchases.lockable(wid) and not d.weapons[wid] and not table.find(new, wid) then table.insert(new, wid) end
	end
	if #new == 0 then return true, 0, "already" end
	for _, wid in new do d.weapons[wid] = { t = os.time(), how = how, id = id } end
	if not write(s) then
		for _, wid in new do d.weapons[wid] = nil end
		return false, 0, "couldn't save"
	end
	publish(p)
	print(("[jankfire] purchases: %s has %d weapon(s) opened (%s)"):format(p.Name, #new, how))
	return true, #new, nil
end

-- ------------------------------------------------------------------ the big coin packs' extras (19 Nov)
-- decided once per purchase and written before anything is given (data.extras[purchaseId]): the Crates (or their coins
-- where Roblox's policy keeps the player from paid random items), Bullion (or its coins if they have it), the skin pick
-- (waiting until it's made; its coins at once if every skin on its list is theirs). each part goes under its own id
-- ("<purchase>:crates", ":gold", ":skin"), so a receipt Roblox sends again gives nothing twice
local EXTRAS_KEPT = 200
local function extrasOf(d: any): any
	if type(d.extras) ~= "table" then d.extras = {} end
	if type(d.extrasOrder) ~= "table" then d.extrasOrder = {} end
	return d.extras
end
local function publishPicks(p: Player)
	if not p.Parent then return end
	local d = dataOf(p)
	local list = {}
	if d and type(d.extras) == "table" then
		for pid, e in d.extras do
			if type(e) == "table" and e.pick == "pick" and not e.got then table.insert(list, { pid, e.kind, tonumber(e.t) or 0 }) end
		end
	end
	table.sort(list, function(a, b) return a[3] < b[3] end)
	local words = {}
	for _, x in list do table.insert(words, x[1] .. ":" .. x[2]) end
	p:SetAttribute("PackPicks", if #words > 0 then table.concat(words, ",") else nil)
end
local function ownsAllOf(L: any, p: Player, kind: string): boolean
	for _, id in Shop.pickList(kind) do if not L.owns(p, "skin", id) then return false end end
	return true
end
function Purchases.packExtras(p: Player, pack: any, pid: string): boolean
	local ex = type(pack) == "table" and pack.extras
	if type(ex) ~= "table" then return true end
	local s = st[p]
	local d = dataOf(p)
	if not s or not d then return false end
	local L, Q = module("Loot"), quests()
	if not L or not Q or type(L.grant) ~= "function" or type(L.owns) ~= "function" or type(Q.buyBrass) ~= "function" then return false end
	local all = extrasOf(d)
	local e = all[pid]
	if type(e) ~= "table" then
		-- 1. decided and written
		e = { t = os.time(), pack = pack.id }
		local n = math.floor(tonumber(ex.crates) or 0)
		if n > 0 then
			e.crates = n
			e.crateHow = if type(L.restricted) ~= "function" or L.restricted(p) then "coins" else "crate"
		end
		if ex.gold then e.gold = if L.owns(p, "wrap", Shop.PACK_GOLD, "ar") then "coins" else "wrap" end
		if type(ex.pick) == "string" then
			e.kind = ex.pick
			e.pick = if #Shop.pickList(ex.pick) == 0 or ownsAllOf(L, p, ex.pick) then "coins" else "pick"
		end
		all[pid] = e
		table.insert(d.extrasOrder, pid)
		-- (the oldest decided ones go past EXTRAS_KEPT; never a pick still waiting)
		local i = 1
		while #d.extrasOrder > EXTRAS_KEPT and i <= #d.extrasOrder do
			local old = all[d.extrasOrder[i]]
			if type(old) == "table" and old.pick == "pick" and not old.got then i += 1
			else all[d.extrasOrder[i]] = nil; table.remove(d.extrasOrder, i) end
		end
		if not write(s) then
			all[pid] = nil
			local j = table.find(d.extrasOrder, pid)
			if j then table.remove(d.extrasOrder, j) end
			return false
		end
	end
	-- 2. given, each part under its own id
	if e.crates then
		local ok, res
		if e.crateHow == "coins" then ok, res = pcall(Q.buyBrass, p, e.crates * Shop.extraCoins("crate"), pid .. ":crates")
		else ok, res = pcall(L.grant, p, "crate", pid .. ":crates", e.crates) end
		if not ok or res ~= true then return false end
	end
	if e.gold == "wrap" then
		local ok, res = pcall(L.grant, p, "pack:gold", pid .. ":gold")
		if not ok or res ~= true then return false end
	elseif e.gold == "coins" then
		local ok, res = pcall(Q.buyBrass, p, Shop.extraCoins("gold"), pid .. ":gold")
		if not ok or res ~= true then return false end
	end
	if e.pick == "coins" then
		local ok, res = pcall(Q.buyBrass, p, Shop.extraCoins("pick"), pid .. ":skin")
		if not ok or res ~= true then return false end
	end
	publishPicks(p)
	print(("[jankfire] purchases: %s's %s extras: crates %s, gold %s, skin %s"):format(p.Name, tostring(pack.id),
		tostring(e.crateHow), tostring(e.gold), tostring(e.pick)))
	return true
end
-- the skin chosen for a waiting pick ("coins": the coins instead, only when every skin on its list is theirs)
function Purchases.pick(p: Player, pid: any, skin: any): any
	local s = st[p]
	local d = dataOf(p)
	if not s or not d then return { ok = false, why = "still loading" } end
	if type(pid) ~= "string" or type(skin) ~= "string" then return { ok = false, why = "nope" } end
	local e = type(d.extras) == "table" and d.extras[pid] or nil
	if type(e) ~= "table" or e.pick ~= "pick" or type(e.kind) ~= "string" then return { ok = false, why = "nothing to pick" } end
	if e.got then publishPicks(p); return { ok = true, got = e.got, already = true } end
	local L, Q = module("Loot"), quests()
	if not L or not Q or type(L.grant) ~= "function" or type(Q.buyBrass) ~= "function" then return { ok = false, why = "the shop isn't open yet" } end
	if skin == "coins" then
		if not ownsAllOf(L, p, e.kind) then return { ok = false, why = "pick a skin you don't have" } end
	elseif not table.find(Shop.pickList(e.kind), skin) then
		return { ok = false, why = "that one isn't on the list" }
	elseif L.owns(p, "skin", skin) then
		return { ok = false, why = "you have that one" }
	end
	if s.busy then return { ok = false, why = "one at a time" } end
	s.busy = true
	local ok, res
	if skin == "coins" then ok, res = pcall(Q.buyBrass, p, Shop.extraCoins("pick"), pid .. ":skin")
	else ok, res = pcall(L.grant, p, "gift:skin:" .. skin, pid .. ":skin") end
	if not ok or res ~= true then
		s.busy = false
		return { ok = false, why = "couldn't give it. try again" }
	end
	-- (given under the pick's own id: a failed write here is fine, the next try finds it given and only marks it)
	e.got = skin
	write(s)
	s.busy = false
	publishPicks(p)
	print(("[jankfire] purchases: %s picked %s for %s"):format(p.Name, skin, pid))
	return { ok = true, got = skin, coins = if skin == "coins" then Shop.extraCoins("pick") else nil }
end

-- the Brass buy, all on the server: the price is the shop's, the Brass is taken by the quests' save
function Purchases.buyWithBrass(p: Player, wid: any): any
	local s = st[p]
	local d = dataOf(p)
	if not s or not d then return { ok = false, why = "your purchases are still loading" } end
	if not forSale(wid) then return { ok = false, why = "that isn't for sale" } end
	local w = wid :: string
	if d.weapons[w] then return { ok = false, why = "you have it already" } end
	if Unlocks.robuxFree() then return { ok = false, why = "it's free for now: keep your coins" } end
	local price = tonumber((Shop.MONEY.weapons :: any)[w].coins) or 0
	if price <= 0 then return { ok = false, why = "that isn't for sale for coins" } end
	local Q = quests()
	if not Q or type(Q.spendBrass) ~= "function" then return { ok = false, why = "the wallet isn't open" } end
	if (tonumber(p:GetAttribute("Brass")) or 0) < price then return { ok = false, why = "not enough coins" } end
	if s.busy then return { ok = false, why = "one at a time" } end
	s.busy = true
	local id = "weapon:" .. w
	-- 1. the mark (written), so a crash between the two saves is settled on the next join
	d.pending[id] = { wid = w, brass = price, t = os.time() }
	if not write(s) then
		d.pending[id] = nil
		s.busy = false
		return { ok = false, why = "couldn't save. try again" }
	end
	-- 2. the Brass (written in the quests' save; the same id twice takes it once)
	local ok, why = Q.spendBrass(p, price, "weapon " .. w, id)
	if not ok then
		d.pending[id] = nil
		write(s)
		s.busy = false
		return { ok = false, why = why or "couldn't take the coins" }
	end
	-- 3. the weapon (a failed write stays in memory: the next autosave writes it, and the mark settles it if not)
	d.weapons[w] = { t = os.time(), how = "brass", id = id }
	d.pending[id] = nil
	write(s)
	s.busy = false
	publish(p)
	print(("[jankfire] purchases: %s bought the %s for %d Brass"):format(p.Name, w, price))
	return { ok = true, wid = w }
end

-- an EARLY unlock (19 Nov): a weapon that opens at a level, with coins before the player gets there, kept for good
-- (RobuxOwned: Unlocks treats it as open whatever the level). the same three writes as buyWithBrass
function Purchases.buyEarly(p: Player, wid: any): any
	local s = st[p]
	local d = dataOf(p)
	if not s or not d then return { ok = false, why = "your purchases are still loading" } end
	if not Shop.earlyOn() then return { ok = false, why = "not yet" } end
	local price = Shop.earlyPrice(wid)
	if not price then return { ok = false, why = "that one doesn't open at a level" } end
	local w = wid :: string
	if d.weapons[w] then return { ok = false, why = "you have it already" } end
	if Unlocks.forPlayer(p, w) then return { ok = false, why = "it's open for you already" } end
	local Q = quests()
	if not Q or type(Q.spendBrass) ~= "function" then return { ok = false, why = "the wallet isn't open" } end
	if (tonumber(p:GetAttribute("Brass")) or 0) < price then return { ok = false, why = "not enough coins" } end
	if s.busy then return { ok = false, why = "one at a time" } end
	s.busy = true
	local id = "early:" .. w
	d.pending[id] = { wid = w, brass = price, t = os.time(), how = "early" }
	if not write(s) then
		d.pending[id] = nil
		s.busy = false
		return { ok = false, why = "couldn't save. try again" }
	end
	local ok, why = Q.spendBrass(p, price, "early " .. w, id)
	if not ok then
		d.pending[id] = nil
		write(s)
		s.busy = false
		return { ok = false, why = why or "couldn't take the coins" }
	end
	d.weapons[w] = { t = os.time(), how = "early", id = id }
	d.pending[id] = nil
	write(s)
	s.busy = false
	publish(p)
	print(("[jankfire] purchases: %s unlocked the %s early for %d coins"):format(p.Name, w, price))
	return { ok = true, wid = w }
end

-- a WEAPON BUNDLE for coins (19 Nov, the owner: "only skins cost robux"): every weapon in it you can't carry yet
-- unlocked for good (data.weapons, how "bundle": RobuxOwned), its cosmetics you lack (Loot.grant, idempotent), at
-- Shop.wbundleCoins. buy false: just the quote. the same three writes as any coins buy, settled on join after a crash
function Purchases.weaponBundle(p: Player, bid: any, buy: boolean): any
	local s = st[p]
	local d = dataOf(p)
	if not s or not d then return { ok = false, why = "your purchases are still loading" } end
	local o = if type(bid) == "string" then Shop.byId[bid] else nil
	if not o or not o.weapons or not Shop.weaponBundlesOn() then return { ok = false, why = "that isn't for sale" } end
	local L = module("Loot")
	if not L or type(L.owns) ~= "function" then return { ok = false, why = "the shop isn't open" } end
	local function lacksW(wid: string): boolean return not Unlocks.forPlayer(p, wid) end
	local function lacksI(it: any): boolean return not L.owns(p, it.kind, it.id, it.weapon) end
	local price, full = Shop.wbundleCoins(o, lacksW, lacksI)
	local weapons = {}
	for _, wid in Shop.wbundleWeapons(o) do if lacksW(wid) then table.insert(weapons, wid) end end
	if not buy then return { ok = true, price = price, full = full, weapons = weapons } end
	if price <= 0 then return { ok = false, why = "you have all of it already" } end
	local Q = quests()
	if not Q or type(Q.spendBrass) ~= "function" then return { ok = false, why = "the wallet isn't open" } end
	if (tonumber(p:GetAttribute("Brass")) or 0) < price then return { ok = false, why = "not enough coins" } end
	if s.busy then return { ok = false, why = "one at a time" } end
	s.busy = true
	d.nextId = (tonumber(d.nextId) or 0) + 1
	local id = ("wbundle:%d:%d"):format(p.UserId, d.nextId)
	local e = { offer = o.id, weapons = weapons, coins = price, t = os.time() }
	d.pending[id] = e
	if not write(s) then
		d.pending[id] = nil
		s.busy = false
		return { ok = false, why = "couldn't save. try again" }
	end
	local ok, why = Q.spendBrass(p, price, "bundle " .. o.id, id)
	if not ok then
		d.pending[id] = nil
		write(s)
		s.busy = false
		return { ok = false, why = why or "couldn't take the coins" }
	end
	for _, wid in weapons do if not d.weapons[wid] then d.weapons[wid] = { t = os.time(), how = "bundle", id = id } end end
	local given = grantCoinsBuy(p, e, id)
	if given then d.pending[id] = nil end
	write(s)
	s.busy = false
	publish(p)
	print(("[jankfire] purchases: %s bought the %s bundle for %d coins (%d weapons)"):format(p.Name, o.id, price, #weapons))
	return { ok = true, offer = o.id, weapons = weapons }
end

-- the coins buy, all on the server: the price is the shop's, the coins are taken by the quests' save
function Purchases.buyWithCoins(p: Player, offerId: any, n: any): any
	local s = st[p]
	local d = dataOf(p)
	if not s or not d then return { ok = false, why = "your purchases are still loading" } end
	if not Shop.coinsOnly() then return { ok = false, why = "that's sold for robux" } end
	if type(offerId) ~= "string" then return { ok = false, why = "nope" } end
	local price: number? = nil
	local count = 1
	local missing: number? = nil
	local label = offerId
	local dskin = string.match(offerId, "^deal:([%w_]+)$")
	if dskin then
		local D = module("Deals")
		local deal = D and type(D.offerFor) == "function" and D.offerFor(p, dskin)
		if not deal then return { ok = false, why = "that deal isn't yours today" } end
		price = Shop.coinDealPrice(dskin, deal.pct)
	else
		local o = Shop.offer(offerId)
		if not o then return { ok = false, why = "that isn't for sale" } end
		local L = module("Loot")
		if not L then return { ok = false, why = "the shop isn't open" } end
		if o.type == "single" then
			if not Shop.onSale(o.id) then return { ok = false, why = "not on sale today" } end
			if type(L.owns) == "function" and L.owns(p, o.kind, o.item, o.weapon) then return { ok = false, why = "you have it already" } end
		elseif o.type == "container" then
			-- (a container is a random item: never for coins where Roblox's policy restricts paid random items)
			if type(L.restricted) ~= "function" or L.restricted(p) then return { ok = false, why = "not available where you are" } end
			count = if n == 5 then 5 elseif n == 10 then 10 else 1
		elseif o.type == "bundle" and not o.weapons then
			-- (19 Nov: a bundle of wraps, hats or card looks is coins only; a skin set coins or Robux. what you lack)
			local miss = 0
			for _, it in Shop.contents(o) do if not (type(L.owns) == "function" and L.owns(p, it.kind, it.id, it.weapon)) then miss += 1 end end
			if miss == 0 then return { ok = false, why = "you have all of that already" } end
			missing = miss
		else
			return { ok = false, why = "that's sold for robux" }
		end
		price = Shop.coinPrice(o, count, missing)
		label = o.id
	end
	if not price or price <= 0 then return { ok = false, why = "that isn't for sale for coins" } end
	local Q = quests()
	if not Q or type(Q.spendBrass) ~= "function" then return { ok = false, why = "the wallet isn't open" } end
	if (tonumber(p:GetAttribute("Brass")) or 0) < price then return { ok = false, why = "not enough coins" } end
	if s.busy then return { ok = false, why = "one at a time" } end
	s.busy = true
	d.nextId = (tonumber(d.nextId) or 0) + 1
	local id = ("coins:%d:%d"):format(p.UserId, d.nextId)
	local e = { offer = offerId, n = count, coins = price, t = os.time() }
	-- 1. the mark (written), 2. the coins (the quests' save), 3. the thing (the loot server or the deals)
	d.pending[id] = e
	if not write(s) then
		d.pending[id] = nil
		s.busy = false
		return { ok = false, why = "couldn't save. try again" }
	end
	local ok, why = Q.spendBrass(p, price, "shop " .. label, id)
	if not ok then
		d.pending[id] = nil
		write(s)
		s.busy = false
		return { ok = false, why = why or "couldn't take the coins" }
	end
	local given = grantCoinsBuy(p, e, id)
	if given then d.pending[id] = nil end
	write(s)
	s.busy = false
	if not given then return { ok = false, why = "paid: it'll arrive when you next join" } end
	print(("[jankfire] purchases: %s bought %s x%d for %d coins"):format(p.Name, label, count, price))
	return { ok = true, offer = offerId, n = count }
end

-- a Brass buy a crash cut short: the weapon if the Brass was taken, else the mark goes. waits for the quests' save
local function settle(p: Player, s: State)
	local d = dataOf(p)
	if not d or next(d.pending) == nil then return end
	local t0 = os.clock()
	while p.Parent and os.clock() - t0 < 60 do
		local Q = quests()
		if Q and type(Q.spent) == "function" and Q.spent(p, "probe") ~= nil then break end
		task.wait(1)
	end
	local Q = quests()
	if not p.Parent or not Q or type(Q.spent) ~= "function" then return end
	for id, e in table.clone(d.pending) do
		local took = Q.spent(p, id)
		if took == true and type(e) == "table" and type(e.offer) == "string" then
			-- (a weapon bundle's weapons, for good, then its things)
			if type(e.weapons) == "table" then
				for _, wid in e.weapons do if type(wid) == "string" and not d.weapons[wid] then d.weapons[wid] = { t = os.time(), how = "bundle", id = id } end end
			end
			-- (a coins buy: the coins went, so it's handed over now; the grant is idempotent by the id)
			if grantCoinsBuy(p, e, id) then d.pending[id] = nil end
		elseif took == true and type(e) == "table" and (forSale(e.wid) or Shop.earlyPrice(e.wid) ~= nil) then
			d.weapons[e.wid] = d.weapons[e.wid] or { t = os.time(), how = if e.how == "early" then "early" else "brass", id = id }
			d.pending[id] = nil
		elseif took == false then
			d.pending[id] = nil
		end
	end
	write(s)
	publish(p)
end

local function spend(s: State): boolean
	local t = os.clock()
	s.budget = math.min(6, s.budget + (t - s.budgetT) * 2); s.budgetT = t
	if s.budget < 1 then return false end
	s.budget -= 1
	return true
end

local function handle(p: Player, op: unknown, a: unknown, b: unknown): any
	local s = st[p]
	if not s or not s.ready then return { ok = false, why = "your purchases are still loading" } end
	if not spend(s) then return { ok = false, why = "slow down" } end
	if op == "state" then
		local d = dataOf(p)
		local owned = {}
		if d then for wid in d.weapons do owned[wid] = true end end
		return { ok = true, owned = owned, free = Unlocks.robuxFree() }
	elseif op == "brass" then
		return Purchases.buyWithBrass(p, a)
	elseif op == "coins" then
		return Purchases.buyWithCoins(p, a, b)
	elseif op == "pick" then
		return Purchases.pick(p, a, b)
	elseif op == "early" then
		return Purchases.buyEarly(p, a)
	elseif op == "wbquote" then
		return Purchases.weaponBundle(p, a, false)
	elseif op == "wbundle" then
		return Purchases.weaponBundle(p, a, true)
	elseif op == "dev" then
		if not isDev(p) then return { ok = false, why = "nope" } end
		local d = dataOf(p)
		if a == "extras" and d then return { ok = true, extras = d.extras, order = d.extrasOrder } end
		if a == "forgetExtras" and d then
			d.extras = {}; d.extrasOrder = {}
			write(s)
			publishPicks(p)
			return { ok = true }
		end
		if a == "forget" and type(b) == "string" and d then
			d.weapons[b] = nil
			for id, e in d.pending do if type(e) == "table" and e.wid == b then d.pending[id] = nil end end
			write(s)
			publish(p)
			return { ok = true }
		end
		return { ok = false, why = "forget <weapon>" }
	end
	return { ok = false, why = "nope" }
end

local function load(p: Player)
	local s: State = { prof = nil, ready = false, busy = false, budget = 6, budgetT = os.clock() }
	st[p] = s
	local prof = Profiles.load(store, "u" .. p.UserId, function() return p.Parent ~= nil and st[p] == s end)
	if not prof then return end
	if st[p] ~= s then Profiles.release(store, prof); return end
	s.prof = prof
	s.ready = true
	prof.onLost.Event:Connect(function() warn("[jankfire] purchases: another server took " .. p.Name .. "'s save") end)
	publish(p)
	publishPicks(p) -- (a big pack's skin pick still waiting: the shop asks again)
	task.spawn(settle, p, s)
end

Remote.OnServerInvoke = function(p: Player, op: unknown, a: unknown, b: unknown)
	local ok, res = pcall(handle, p, op, a, b)
	if not ok then
		warn("[jankfire] purchases: " .. tostring(res))
		return { ok = false, why = "something broke. try again" }
	end
	return res
end
Players.PlayerAdded:Connect(function(p) task.spawn(load, p) end)
for _, p in Players:GetPlayers() do task.spawn(load, p) end
Players.PlayerRemoving:Connect(function(p)
	local s = st[p]
	st[p] = nil
	if s and s.prof then Profiles.save(store, s.prof, true) end
end)

return Purchases
