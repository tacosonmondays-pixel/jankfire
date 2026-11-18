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
--   Purchases.buyWithBrass(p, wid) -> { ok, why?, wid? }  the Brass buy (the remote's "brass")
-- the remote JankfireRemotes.Purchases (RemoteFunction, made here):
--   ("state")        -> { ok, owned = { [wid] = true }, free = Unlocks.robuxFree() }
--   ("brass", wid)   -> Purchases.buyWithBrass
--   ("dev", "forget", wid) -> Studio + the place's owner only: takes a bought weapon back (to undo a test)
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
	return { v = 1, weapons = {}, receipts = {}, order = {}, pending = {} }
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

-- the Brass buy, all on the server: the price is the shop's, the Brass is taken by the quests' save
function Purchases.buyWithBrass(p: Player, wid: any): any
	local s = st[p]
	local d = dataOf(p)
	if not s or not d then return { ok = false, why = "your purchases are still loading" } end
	if not forSale(wid) then return { ok = false, why = "that isn't for sale" } end
	local w = wid :: string
	if d.weapons[w] then return { ok = false, why = "you have it already" } end
	if Unlocks.robuxFree() then return { ok = false, why = "it's free for now: keep your Brass" } end
	local price = tonumber((Shop.MONEY.weapons :: any)[w].brass) or 0
	if price <= 0 then return { ok = false, why = "that isn't for sale for Brass" } end
	local Q = quests()
	if not Q or type(Q.spendBrass) ~= "function" then return { ok = false, why = "the wallet isn't open" } end
	if (tonumber(p:GetAttribute("Brass")) or 0) < price then return { ok = false, why = "not enough Brass" } end
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
		return { ok = false, why = why or "couldn't take the Brass" }
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
		if took == true and type(e) == "table" and forSale(e.wid) then
			d.weapons[e.wid] = d.weapons[e.wid] or { t = os.time(), how = "brass", id = id }
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
	elseif op == "dev" then
		if not isDev(p) then return { ok = false, why = "nope" } end
		local d = dataOf(p)
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
