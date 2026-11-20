--!strict
-- TRADING (roblox/docs/TRADING.md; 18 Nov 2026, the owner: "we need trading"). two players in one server swap owned
-- cosmetics and unopened containers (Shared.TradeRules says what may go). behind PlayConfig.TRADING_ON, off until the
-- owner's content questionnaire says the game has trading.
--   * who: anyone in this server, in the hub (not a match, a map room or training), level TradeRules.LEVEL+, a Roblox
--     account TradeRules.AGE+ days old, and Roblox's PolicyService saying IsPaidItemTradingAllowed for BOTH (we don't
--     track whether a thing was bought or earned, so a no blocks trading outright; blocked until it answers). one trade
--     at a time; a request every REQUEST_GAP s; the other side may decline
--   * the window: both sides add items, then both LOCK. any change unlocks both. both locked = the final look: CONFIRM
--     works CONFIRM_WAIT s later, both must confirm, any change resets it
--   * the swap (here, never the client): every item is checked again (owned in the save, tradeable), then
--       1. prepare: the trade goes into both loot saves (data.tradePend) and both are written. a failure: taken out
--          again, nothing moved
--       2. decide: the ledger's "t:<id>" is written once (UpdateAsync: only if empty). commit or abort, whoever writes
--          first; a save that loads with a trade pending asks the ledger and writes "abort" if nobody decided yet. so a
--          crash anywhere can't leave one save traded and the other not
--       3. apply: each save gives its side and takes the other's (data.tradeDone: a receipt, so it happens once), keeps
--          the trade in its history (data.trades, the last TradeRules.HISTORY), and is written. a save that fails here is
--          already right in memory (written by the autosave or on leave) and, if the server dies first, finishes the
--          trade from its pending copy the next time it loads (Loot.loaded -> resolve)
--     anything worn that went (a wrap, a hat, a skin, a kill effect, a card look) comes off: Loot.changed, the loadout,
--     flair and the card each check what you own
--   * the owner's log: the ledger keeps every trade ("t:<id>": both ids and names, the items, the time) and every
--     player's trade ids ("p:<userId>", newest first). Trading.lookup(userId) reads them (the REPORT / CONFIRM CHEATER
--     tools). "JankfireTrades_v1", "_studio" in Studio
-- the remote JankfireRemotes.Trade (RemoteFunction) answers { ok, why?, ... }:
--   ("state")                 -> { on, can, why, inv = { { t, k, name, rarity, gun?, type, no? } }, stock, trade?, asks }
--   ("request", userId)       ("answer", fromId, yes)     ("cancel")
--   ("add", t, key)  ("remove", t, key)  ("stock", kind, n)  ("lock")  ("unlock")  ("confirm")
--   ("history")               -> { list = the save's trades, newest first }
-- JankfireRemotes.TradePush (RemoteEvent): { t = "trade", view? } (the window; no view = closed), { t = "ask", from,
-- name, ends } / { t = "askgone", from }, { t = "note", text }, { t = "done", gave, got, with }
-- the remote's attribute On says whether trading is open (the clients show TRADE buttons by it)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local DataStoreService = game:GetService("DataStoreService")
local PolicyService = game:GetService("PolicyService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local PlayConfig = require(Shared:WaitForChild("PlayConfig")) :: any
local R = require(Shared:WaitForChild("TradeRules")) :: any
local Loot = require(script.Parent:WaitForChild("Loot")) :: any

local Trading = {}
local STUDIO = RunService:IsStudio()

local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local function remote(class: string, name: string): any
	local r = Remotes:FindFirstChild(name)
	if not r then
		r = Instance.new(class)
		r.Name = name
		r.Parent = Remotes
	end
	return r
end
local Remote = remote("RemoteFunction", "Trade") :: RemoteFunction
local Push = remote("RemoteEvent", "TradePush") :: RemoteEvent

local LEDGER = "JankfireTrades_v1" .. (if STUDIO then "_studio" else "")
local ledger: DataStore? = nil
do
	local ok, ds = pcall(function() return DataStoreService:GetDataStore(LEDGER) end)
	if ok then ledger = ds end
end

local studioOn = false -- (Studio: a test switched it on, whatever the saved switch says)
function Trading.on(): boolean
	if STUDIO and studioOn then return true end
	return PlayConfig.TRADING_ON == true
end

local function now(): number return os.clock() end
local function deepCopy(t: any): any
	if type(t) ~= "table" then return t end
	local o = {}
	for k, v in t do o[k] = deepCopy(v) end
	return o
end

-- ------------------------------------------------------------------ who: a player, or a Studio stand-in
type Stand = { id: number, name: string, level: number, age: number, policy: boolean?, zone: string, inbox: { any } }
local stands: { [number]: Stand } = {}
local policy: { [number]: boolean } = {} -- (PolicyService's answer; missing = not known yet = blocked)
local testGate: { [number]: { level: number?, age: number?, policy: boolean? } } = {} -- (Studio tests)

local function playerOf(id: number): Player? return Players:GetPlayerByUserId(id) end
local function here(id: number): boolean return playerOf(id) ~= nil or stands[id] ~= nil end
local function nameOf(id: number): string
	local p = playerOf(id)
	if p then return p.DisplayName end
	local s = stands[id]
	return if s then s.name else "?"
end
local function handleOf(id: number): any?
	local p = playerOf(id)
	if p then return Loot.tradeHandle(p) end
	if stands[id] then return Loot.testHandle(id) end
	return nil
end
local function push(id: number, msg: any)
	local p = playerOf(id)
	if p then Push:FireClient(p, msg); return end
	local s = stands[id]
	if s then
		table.insert(s.inbox, msg)
		while #s.inbox > 40 do table.remove(s.inbox, 1) end
	end
end
local function note(id: number, text: string) push(id, { t = "note", text = text }) end

-- may this one trade right now? (false and a short reason)
local function can(id: number): (boolean, string?)
	if not Trading.on() then return false, "TRADING ISN'T OPEN YET" end
	local p, s = playerOf(id), stands[id]
	if not p and not s then return false, "NOT IN THIS SERVER" end
	local g = testGate[id] or {}
	local pol: boolean? = g.policy
	if pol == nil then pol = if s then s.policy else policy[id] end
	if pol == nil then return false, "ONE MOMENT" end
	if pol == false then return false, "NOT AVAILABLE WHERE YOU ARE" end
	local level = g.level or (if s then s.level else tonumber((p :: Player):GetAttribute("Level"))) or 0
	if level < R.LEVEL then return false, ("LEVEL %d TO TRADE"):format(R.LEVEL) end
	local age = g.age or (if s then s.age else (p :: Player).AccountAge)
	if age < R.AGE then return false, ("ACCOUNT UNDER %d DAYS OLD"):format(R.AGE) end
	local zone = if s then s.zone else ((p :: Player):GetAttribute("Zone") or "hub")
	if zone ~= "hub" then return false, "HUB ONLY" end
	local h = handleOf(id)
	if not h then return false, "YOUR THINGS ARE STILL LOADING" end
	if h.state() ~= "cloud" then return false, "YOUR SAVE ISN'T REACHABLE" end
	if type(h.data.tradePend) == "table" then return false, "A TRADE IS STILL FINISHING" end
	if not ledger then return false, "THE TRADE LOG ISN'T REACHABLE" end
	return true, nil
end

-- ------------------------------------------------------------------ what you own (read from the save itself)
local function has(d: any, t: string, k: string): boolean
	local list = d.inv and d.inv[t]
	return type(list) == "table" and table.find(list, k) ~= nil
end
-- a shop bundle's wrap is owned on every gun at once (data.every.wrap): one gun's pair of it can't go alone
local function bundled(d: any, t: string, k: string): boolean
	if t ~= "wrap" then return false end
	local id = string.match(k, "^([%w_]+)@") or k
	local ev = type(d.every) == "table" and d.every.wrap
	return type(ev) == "table" and ev[id] == true
end
local function whyNot(d: any, t: string, k: string): string?
	local w = R.why(t, k)
	if w then return w end
	if bundled(d, t, k) then return R.BUNDLE end
	return nil
end
local function stockOf(d: any, kind: string): number
	return math.max(0, math.floor(tonumber(d.stock and d.stock[kind]) or 0))
end
-- everything this save holds that a trade could show, tradeable or not (the picker), types in R.TYPES order
local RANK = { exotic = 0, legendary = 1, epic = 2, rare = 3, common = 4 }
local function inventory(d: any): { any }
	local out = {}
	for _, t in R.TYPES do
		local seen = {}
		for _, k in (if type(d.inv) == "table" and type(d.inv[t]) == "table" then d.inv[t] else {}) do
			if type(k) ~= "string" or seen[k] then continue end
			seen[k] = true
			local c = R.card(t, k)
			if c then
				c.no = whyNot(d, t, k)
				table.insert(out, c)
			end
		end
	end
	table.sort(out, function(a, b)
		local ta, tb = table.find(R.TYPES, a.t) or 99, table.find(R.TYPES, b.t) or 99
		if ta ~= tb then return ta < tb end
		if (a.no == nil) ~= (b.no == nil) then return a.no == nil end
		local ra, rb = RANK[a.rarity] or 9, RANK[b.rarity] or 9
		if ra ~= rb then return ra < rb end
		if a.name ~= b.name then return a.name < b.name end
		return a.k < b.k
	end)
	return out
end

-- ------------------------------------------------------------------ trades
type Item = { t: string, k: string }
type Offer = { items: { Item }, stock: { [string]: number }, locked: boolean, confirmed: boolean }
type Trade = { id: string, a: number, b: number, offers: { [number]: Offer }, phase: string, reviewAt: number?, last: number, rev: number }
local trades: { [number]: Trade } = {} -- (by user id: both sides point at the same one)
local asks: { [number]: { [number]: number } } = {} -- asks[to][from] = when it lapses (os.clock)
local lastAsk: { [number]: number } = {}
local swapping: { [string]: boolean } = {} -- (trade ids being swapped here: a pending copy of one is left alone)

local function other(tr: Trade, id: number): number return if tr.a == id then tr.b else tr.a end
local function offerView(o: Offer): any
	local items = {}
	for _, it in o.items do
		local c = R.card(it.t, it.k)
		if c then table.insert(items, c) end
	end
	return { items = items, stock = table.clone(o.stock), locked = o.locked, confirmed = o.confirmed }
end
local function viewFor(tr: Trade, id: number): any
	local them = other(tr, id)
	local v = { id = tr.id, rev = tr.rev, phase = tr.phase, me = offerView(tr.offers[id]), them = offerView(tr.offers[them]) }
	v.them.id, v.them.name = them, nameOf(them)
	if tr.reviewAt then v.confirmAt = workspace:GetServerTimeNow() + math.max(0, tr.reviewAt + R.CONFIRM_WAIT - now()) end
	return v
end
local function show(tr: Trade)
	push(tr.a, { t = "trade", view = viewFor(tr, tr.a) })
	push(tr.b, { t = "trade", view = viewFor(tr, tr.b) })
end
local function close(tr: Trade, why: string?)
	if trades[tr.a] == tr then trades[tr.a] = nil end
	if trades[tr.b] == tr then trades[tr.b] = nil end
	tr.phase = "closed"
	for _, id in { tr.a, tr.b } do
		push(id, { t = "trade" })
		if why then note(id, why) end
	end
end
-- something changed: both unlock, confirmations go, back to adding
local function changed(tr: Trade)
	for _, o in tr.offers do o.locked, o.confirmed = false, false end
	tr.phase, tr.reviewAt = "edit", nil
	tr.rev += 1
	tr.last = now()
	show(tr)
end
local function open(a: number, b: number)
	local tr: Trade = { id = HttpService:GenerateGUID(false), a = a, b = b, phase = "edit", last = now(), rev = 1,
		offers = { [a] = { items = {}, stock = {}, locked = false, confirmed = false }, [b] = { items = {}, stock = {}, locked = false, confirmed = false } } }
	trades[a], trades[b] = tr, tr
	for _, id in { a, b } do
		if asks[id] then for from in asks[id] do push(id, { t = "askgone", from = from }) end end
		asks[id] = nil
	end
	show(tr)
end

-- ------------------------------------------------------------------ the swap
local testFail: { [string]: { [number]: boolean } } = { prepare = {}, final = {} } -- (Studio tests: that side's save "fails")
local testLedgerFail = false

-- the ledger's decision for trade id: "commit" | "abort", written once (only if nobody wrote it yet). want = what this
-- server would like; rec = the trade (written with a commit). nil = the ledger didn't answer
local function decide(id: string, want: string, rec: any?): string?
	if not ledger then return nil end
	if testLedgerFail and STUDIO then return nil end
	local ds = ledger :: DataStore
	for try = 1, 3 do
		local result: string? = nil
		local ok = pcall(function()
			ds:UpdateAsync("t:" .. id, function(old: any)
				if type(old) == "table" and (old.state == "commit" or old.state == "abort") then
					result = old.state
					return nil
				end
				result = want
				if want == "commit" then
					local r = deepCopy(rec)
					r.state = "commit"
					return r
				end
				return { id = id, state = "abort", t = os.time() }
			end)
		end)
		if ok then return result end
		-- (it may have landed all the same: read it)
		local okG, v = pcall(function() return ds:GetAsync("t:" .. id) end)
		if okG and type(v) == "table" and (v.state == "commit" or v.state == "abort") then return v.state end
		task.wait(try)
	end
	return nil
end
local function readDecision(id: string): (boolean, string?)
	if not ledger then return false, nil end
	local ok, v = pcall(function() return (ledger :: DataStore):GetAsync("t:" .. id) end)
	if not ok then return false, nil end
	return true, if type(v) == "table" then v.state else nil
end

local FRESH_MAX = 300
local function takeKey(d: any, t: string, k: string)
	local list = d.inv and d.inv[t]
	if type(list) ~= "table" then return end
	for i = #list, 1, -1 do if list[i] == k then table.remove(list, i) end end
	local f = type(d.fresh) == "table" and d.fresh[t]
	if type(f) == "table" then f[k] = nil end
end
local function giveKey(d: any, t: string, k: string)
	d.inv = if type(d.inv) == "table" then d.inv else {}
	d.inv[t] = if type(d.inv[t]) == "table" then d.inv[t] else {}
	if table.find(d.inv[t], k) then return end
	table.insert(d.inv[t], k) -- (on the end: the newest, the way Loot keeps the order things were got in)
	d.fresh = if type(d.fresh) == "table" then d.fresh else {}
	local f = d.fresh[t]
	if type(f) ~= "table" then f = {}; d.fresh[t] = f end
	d.freshN = (tonumber(d.freshN) or 0) + 1
	f[k] = d.freshN -- (NEW in the loadout)
	local n = 0
	for _ in f do n += 1 end
	if n > FRESH_MAX then
		local oldK, oldN = nil, math.huge
		for kk, v in f do if type(v) == "number" and v < oldN then oldK, oldN = kk, v end end
		if oldK then f[oldK] = nil end
	end
end
-- one save's half of a committed trade, once (data.tradeDone). side = "a" | "b"
local function applyHalf(d: any, rec: any, side: string): boolean
	d.tradeDone = if type(d.tradeDone) == "table" then d.tradeDone else {}
	if table.find(d.tradeDone, rec.id) then
		if type(d.tradePend) == "table" and d.tradePend.id == rec.id then d.tradePend = nil end
		return false
	end
	local mine, theirs = rec[side], rec[if side == "a" then "b" else "a"]
	for _, it in mine.gives do takeKey(d, it.t, it.k) end
	d.stock = if type(d.stock) == "table" then d.stock else {}
	for kind, n in mine.stock do d.stock[kind] = math.max(0, stockOf(d, kind) - n) end
	for _, it in theirs.gives do giveKey(d, it.t, it.k) end
	for kind, n in theirs.stock do d.stock[kind] = stockOf(d, kind) + n end
	table.insert(d.tradeDone, rec.id)
	while #d.tradeDone > 100 do table.remove(d.tradeDone, 1) end
	d.trades = if type(d.trades) == "table" then d.trades else {}
	table.insert(d.trades, 1, { id = rec.id, t = rec.t, with = theirs.id, withName = theirs.name,
		gave = deepCopy(mine.gives), gaveStock = deepCopy(mine.stock), got = deepCopy(theirs.gives), gotStock = deepCopy(theirs.stock) })
	while #d.trades > R.HISTORY do table.remove(d.trades) end
	d.tradePend = nil
	return true
end

-- a side's offer, checked against its save as it is now: nil = fine, else why
local function check(id: number, o: Offer, d: any): string?
	for _, it in o.items do
		if not has(d, it.t, it.k) then return nameOf(id) .. " no longer has one of the items" end
		local w = whyNot(d, it.t, it.k)
		if w then return "an item can't be traded: " .. w end
	end
	for kind, n in o.stock do
		if n > stockOf(d, kind) then return nameOf(id) .. " no longer has enough containers" end
	end
	return nil
end

local function saveSide(h: any, what: string): boolean
	if STUDIO and testFail[what] and testFail[what][h.id] then return false end
	return h.save()
end
-- written later, a few tries (memory is right already; the autosave and the leave save write it too)
local function saveSoon(h: any)
	task.spawn(function()
		for try = 1, 3 do
			if saveSide(h, "final") then return end
			task.wait(3 * try)
		end
		warn(("[jankfire] trade: %d's save didn't write; it will on the next save, or finish the trade when it loads"):format(h.id))
	end)
end
-- the owner's log: each side's trade ids, newest first
local function index(id: number, tradeId: string)
	if not ledger then return end
	pcall(function()
		(ledger :: DataStore):UpdateAsync("p:" .. id, function(old: any)
			local list = if type(old) == "table" then old else {}
			table.insert(list, 1, tradeId)
			while #list > 200 do table.remove(list) end
			return list
		end)
	end)
end

local function back(tr: Trade, why: string)
	if tr.phase == "closed" then return end
	changed(tr)
	for _, id in { tr.a, tr.b } do note(id, why) end
end

local function swap(tr: Trade)
	if tr.phase ~= "review" then return end
	tr.phase = "swap"
	show(tr)
	local A, B = tr.a, tr.b
	local ha, hb = handleOf(A), handleOf(B)
	if not ha or not hb then back(tr, "a save isn't loaded: nothing changed"); return end
	local why = check(A, tr.offers[A], ha.data) or check(B, tr.offers[B], hb.data)
	if why then back(tr, why); return end
	local function side(id: number): any
		local o = tr.offers[id]
		local stock = {}
		for kind, n in o.stock do if n > 0 then stock[kind] = n end end
		return { id = id, name = nameOf(id), gives = deepCopy(o.items), stock = stock }
	end
	local rec = { id = HttpService:GenerateGUID(false), t = os.time(), a = side(A), b = side(B) }
	swapping[rec.id] = true
	-- 1. prepare: the trade waits in both saves
	ha.data.tradePend, hb.data.tradePend = deepCopy(rec), deepCopy(rec)
	local okA = saveSide(ha, "prepare")
	local okB = okA and saveSide(hb, "prepare")
	if not (okA and okB) then
		ha.data.tradePend, hb.data.tradePend = nil, nil
		task.spawn(ha.save); task.spawn(hb.save)
		swapping[rec.id] = nil
		back(tr, "couldn't save: nothing changed. try again")
		return
	end
	-- 2. decide
	local dec = decide(rec.id, "commit", rec)
	if dec ~= "commit" then
		if dec == "abort" then
			ha.data.tradePend, hb.data.tradePend = nil, nil
			task.spawn(ha.save); task.spawn(hb.save)
			swapping[rec.id] = nil
			back(tr, "couldn't finish: nothing changed. try again")
		else
			-- (the ledger didn't answer: both keep the pending copy and the resolver asks again; nothing moves till it does)
			swapping[rec.id] = nil
			close(tr, "the trade log didn't answer: the trade finishes or goes back when it does")
		end
		return
	end
	-- 3. apply, both halves, then write
	applyHalf(ha.data, rec, "a")
	applyHalf(hb.data, rec, "b")
	ha.done(); hb.done()
	saveSoon(ha); saveSoon(hb)
	swapping[rec.id] = nil
	task.spawn(index, A, rec.id)
	task.spawn(index, B, rec.id)
	close(tr, nil)
	push(A, { t = "done", with = nameOf(B), gave = rec.a.gives, gaveStock = rec.a.stock, got = rec.b.gives, gotStock = rec.b.stock })
	push(B, { t = "done", with = nameOf(A), gave = rec.b.gives, gaveStock = rec.b.stock, got = rec.a.gives, gotStock = rec.a.stock })
end

-- a save with a trade pending (it loaded, or the ledger didn't answer before): ask the ledger and finish it either way
local function resolve(h: any): string?
	local pend = h.data.tradePend
	if type(pend) ~= "table" or type(pend.id) ~= "string" then return nil end
	if swapping[pend.id] then return "busy" end
	local ok, state = readDecision(pend.id)
	if not ok then return nil end
	if state == nil then state = decide(pend.id, "abort") end -- (nobody decided: it never happened)
	if state == "commit" then
		local sideName = if pend.a and pend.a.id == h.id then "a" else "b"
		applyHalf(h.data, pend, sideName)
		h.done()
		saveSoon(h)
		task.spawn(index, h.id, pend.id)
		return "commit"
	elseif state == "abort" then
		h.data.tradePend = nil
		saveSoon(h)
		return "abort"
	end
	return nil
end

-- ------------------------------------------------------------------ the ops
local function ask(from: number, to: number): (boolean, string?)
	local ok, why = can(from)
	if not ok then return false, why end
	if from == to then return false, "THAT'S YOU" end
	if not here(to) then return false, "NOT IN THIS SERVER" end
	if trades[from] then return false, "FINISH YOUR TRADE FIRST" end
	if trades[to] then return false, "THEY'RE IN A TRADE" end
	local okT, whyT = can(to)
	if not okT then return false, if whyT == "HUB ONLY" then "THEY'RE NOT IN THE HUB" else "THEY CAN'T TRADE RIGHT NOW" end
	if now() - (lastAsk[from] or -math.huge) < R.REQUEST_GAP then return false, "WAIT A MOMENT" end
	-- (they asked you already: that's a yes)
	if asks[from] and asks[from][to] and asks[from][to] > now() then
		asks[from][to] = nil
		open(to, from)
		return true, nil
	end
	lastAsk[from] = now()
	asks[to] = asks[to] or {}
	asks[to][from] = now() + R.REQUEST_LIFE
	push(to, { t = "ask", from = from, name = nameOf(from), ends = workspace:GetServerTimeNow() + R.REQUEST_LIFE })
	return true, nil
end
local function answer(to: number, from: number, yes: boolean): (boolean, string?)
	local list = asks[to]
	local t = list and list[from]
	if list then list[from] = nil end
	if not t or t < now() then return false, "THAT REQUEST HAS GONE" end
	if not yes then note(from, nameOf(to) .. " declined the trade"); return true, nil end
	if trades[to] or trades[from] then return false, "ONE OF YOU IS IN A TRADE" end
	local ok, why = can(to)
	if not ok then return false, why end
	local ok2 = can(from)
	if not ok2 then return false, "THEY CAN'T TRADE RIGHT NOW" end
	open(from, to)
	return true, nil
end
local function editable(id: number): (Trade?, string?)
	local tr = trades[id]
	if not tr then return nil, "NO TRADE OPEN" end
	if tr.phase == "swap" then return nil, "SWAPPING" end
	return tr, nil
end
local function add(id: number, t: any, k: any): (boolean, string?)
	local tr, why = editable(id)
	if not tr then return false, why end
	if type(t) ~= "string" or type(k) ~= "string" then return false, "?" end
	local o = tr.offers[id]
	for _, it in o.items do if it.t == t and it.k == k then return true, nil end end
	if #o.items >= R.MAX_ITEMS then return false, ("%d ITEMS AT MOST"):format(R.MAX_ITEMS) end
	local h = handleOf(id)
	if not h then return false, "YOUR THINGS ARE STILL LOADING" end
	if not has(h.data, t, k) then return false, "YOU DON'T HAVE THAT" end
	local w = whyNot(h.data, t, k)
	if w then return false, "NOT TRADEABLE: " .. w end
	table.insert(o.items, { t = t, k = k })
	changed(tr)
	return true, nil
end
local function remove(id: number, t: any, k: any): (boolean, string?)
	local tr, why = editable(id)
	if not tr then return false, why end
	local o = tr.offers[id]
	for i, it in o.items do
		if it.t == t and it.k == k then
			table.remove(o.items, i)
			changed(tr)
			return true, nil
		end
	end
	return true, nil
end
local function setStock(id: number, kind: any, n: any): (boolean, string?)
	local tr, why = editable(id)
	if not tr then return false, why end
	if type(kind) ~= "string" or not table.find(R.KINDS, kind) or type(n) ~= "number" or n ~= n then return false, "?" end
	local h = handleOf(id)
	if not h then return false, "YOUR THINGS ARE STILL LOADING" end
	local want = math.clamp(math.floor(n), 0, math.min(R.MAX_STOCK, stockOf(h.data, kind)))
	local o = tr.offers[id]
	if (o.stock[kind] or 0) == want then return true, nil end
	o.stock[kind] = if want > 0 then want else nil
	changed(tr)
	return true, nil
end
local function empty(o: Offer): boolean
	if #o.items > 0 then return false end
	for _, n in o.stock do if n > 0 then return false end end
	return true
end
local function lock(id: number): (boolean, string?)
	local tr, why = editable(id)
	if not tr then return false, why end
	if tr.phase ~= "edit" then return true, nil end
	if empty(tr.offers[tr.a]) and empty(tr.offers[tr.b]) then return false, "ADD SOMETHING FIRST" end
	tr.offers[id].locked = true
	tr.last = now()
	if tr.offers[tr.a].locked and tr.offers[tr.b].locked then
		tr.phase, tr.reviewAt = "review", now()
	end
	tr.rev += 1
	show(tr)
	return true, nil
end
local function unlock(id: number): (boolean, string?)
	local tr, why = editable(id)
	if not tr then return false, why end
	changed(tr)
	return true, nil
end
local function confirm(id: number): (boolean, string?)
	local tr, why = editable(id)
	if not tr then return false, why end
	if tr.phase ~= "review" or not tr.reviewAt then return false, "BOTH LOCK FIRST" end
	if now() < tr.reviewAt + R.CONFIRM_WAIT - 0.15 then return false, "LOOK IT OVER FIRST" end
	tr.offers[id].confirmed = true
	tr.last = now()
	tr.rev += 1
	if tr.offers[tr.a].confirmed and tr.offers[tr.b].confirmed then
		task.spawn(swap, tr)
	else
		show(tr)
	end
	return true, nil
end
local function cancel(id: number): (boolean, string?)
	local tr = trades[id]
	if not tr then return true, nil end
	if tr.phase == "swap" then return false, "SWAPPING" end
	close(tr, nil)
	note(other(tr, id), nameOf(id) .. " cancelled the trade")
	return true, nil
end

local function stateFor(id: number): any
	local ok, why = can(id)
	local h = handleOf(id)
	local out: any = { ok = true, on = Trading.on(), can = ok, why = why, inv = {}, stock = {}, asks = {} }
	if h then
		out.inv = inventory(h.data)
		for _, kind in R.KINDS do out.stock[kind] = stockOf(h.data, kind) end
	end
	local tr = trades[id]
	if tr then out.trade = viewFor(tr, id) end
	for from, t in asks[id] or {} do
		if t > now() then table.insert(out.asks, { from = from, name = nameOf(from), ends = workspace:GetServerTimeNow() + (t - now()) }) end
	end
	return out
end
local function historyOf(id: number): any
	local h = handleOf(id)
	if not h then return { ok = false, why = "YOUR THINGS ARE STILL LOADING" } end
	local list = {}
	for _, x in (if type(h.data.trades) == "table" then h.data.trades else {}) do
		local function cards(items: any): { any }
			local out = {}
			for _, it in (if type(items) == "table" then items else {}) do
				local c = R.card(it.t, it.k)
				table.insert(out, c or { t = it.t, k = it.k, name = it.k, rarity = "common", type = it.t })
			end
			return out
		end
		table.insert(list, { id = x.id, t = x.t, with = x.with, withName = x.withName, gave = cards(x.gave), gaveStock = x.gaveStock or {},
			got = cards(x.got), gotStock = x.gotStock or {} })
	end
	return { ok = true, list = list }
end

local function handle(id: number, op: any, a: any, b: any, c: any): any
	if op == "state" then return stateFor(id)
	elseif op == "history" then return historyOf(id) end
	local ok, why
	if op == "request" then ok, why = ask(id, tonumber(a) or 0)
	elseif op == "answer" then ok, why = answer(id, tonumber(a) or 0, b == true)
	elseif op == "add" then ok, why = add(id, a, b)
	elseif op == "remove" then ok, why = remove(id, a, b)
	elseif op == "stock" then ok, why = setStock(id, a, b)
	elseif op == "lock" then ok, why = lock(id)
	elseif op == "unlock" then ok, why = unlock(id)
	elseif op == "confirm" then ok, why = confirm(id)
	elseif op == "cancel" then ok, why = cancel(id)
	else return { ok = false, why = "?" } end
	return { ok = ok == true, why = why }
end

-- ------------------------------------------------------------------ the owner's log
-- the last n trades this user id was in (newest first), straight from the ledger: { { id, t, a = { id, name, gives,
-- stock }, b = ..., state } }. for the REPORT / CONFIRM CHEATER tools; works for anyone, here or not
function Trading.lookup(userId: number, n: number?): { any }
	local out = {}
	if not ledger then return out end
	local ds = ledger :: DataStore
	local ok, ids = pcall(function() return ds:GetAsync("p:" .. tostring(userId)) end)
	if not ok or type(ids) ~= "table" then return out end
	for i = 1, math.min(#ids, n or 20) do
		local okR, rec = pcall(function() return ds:GetAsync("t:" .. tostring(ids[i])) end)
		if okR and type(rec) == "table" then table.insert(out, rec) end
	end
	return out
end

-- ------------------------------------------------------------------ wiring
local budget: { [Player]: { n: number, t: number } } = {}
local function spend(p: Player): boolean
	local bt = budget[p] or { n = 20, t = now() }
	budget[p] = bt
	bt.n = math.min(20, bt.n + (now() - bt.t) * 6); bt.t = now()
	if bt.n < 1 then return false end
	bt.n -= 1
	return true
end
local function fetchPolicy(p: Player)
	for try = 1, 4 do
		if not p.Parent then return end
		local ok, info = pcall(function() return PolicyService:GetPolicyInfoForPlayerAsync(p) end)
		if ok and type(info) == "table" then
			policy[p.UserId] = (info :: any).IsPaidItemTradingAllowed == true
			return
		end
		task.wait(2 * try)
	end
end
local function left(id: number)
	local tr = trades[id]
	if tr and tr.phase ~= "swap" then
		close(tr, nil)
		note(other(tr, id), nameOf(id) .. " left: the trade is off")
	end
	asks[id] = nil
	for _, list in asks do list[id] = nil end
	lastAsk[id] = nil
end

function Trading.init()
	Remote:SetAttribute("On", Trading.on())
	Remote.OnServerInvoke = function(p: Player, op: any, a: any, b: any, c: any): any
		if not spend(p) then return { ok = false, why = "SLOW DOWN" } end
		local ok, res = pcall(handle, p.UserId, op, a, b, c)
		if not ok then
			warn("[jankfire] trade: " .. tostring(res))
			return { ok = false, why = "SOMETHING WENT WRONG" }
		end
		return res
	end
	for _, p in Players:GetPlayers() do task.spawn(fetchPolicy, p) end
	Players.PlayerAdded:Connect(function(p) task.spawn(fetchPolicy, p) end)
	Players.PlayerRemoving:Connect(function(p)
		left(p.UserId)
		budget[p] = nil
		policy[p.UserId] = nil
	end)
	-- a save that loads with a trade still pending (a crash mid-swap, the ledger slow): finish it either way
	Loot.loaded:Connect(function(p: Player)
		local h = Loot.tradeHandle(p)
		if h and type(h.data.tradePend) == "table" then task.spawn(resolve, h) end
	end)
	-- the watch: requests lapse, trades close when a side leaves the hub or nothing happens for IDLE s, pending saves
	-- here (the ledger didn't answer) are asked again
	local acc, slow = 0, 0
	RunService.Heartbeat:Connect(function(dt)
		acc += dt
		if acc < 0.5 then return end
		slow += acc
		acc = 0
		Remote:SetAttribute("On", Trading.on())
		local t = now()
		for to, list in asks do
			for from, at in list do
				if at < t then list[from] = nil; push(to, { t = "askgone", from = from }) end
			end
		end
		local seen: { [Trade]: boolean } = {}
		for _, tr in trades do
			if seen[tr] then continue end
			seen[tr] = true
			if tr.phase == "swap" then continue end
			for _, id in { tr.a, tr.b } do
				if not here(id) then left(id); break end
				local okC, why = can(id)
				if not okC and why == "HUB ONLY" then
					close(tr, "the trade is off: " .. nameOf(id) .. " left the hub")
					break
				end
			end
			if tr.phase ~= "closed" and t - tr.last > R.IDLE then close(tr, "the trade timed out") end
		end
		if slow >= 15 then
			slow = 0
			for _, p in Players:GetPlayers() do
				if trades[p.UserId] then continue end
				local h = Loot.tradeHandle(p)
				if h and type(h.data.tradePend) == "table" then task.spawn(resolve, h) end
			end
		end
	end)
	if STUDIO then Trading.testHook() end
end

-- ------------------------------------------------------------------ Studio tests (ServerStorage.JankTradeTest)
--   ("on") / ("off")                    trading here, whatever PlayConfig.TRADING_ON says
--   ("stand", id, name, opts)           a stand-in trader (id < 0) with its own loot save (Loot.testHandle): opts = { level,
--                                       age, policy (true / false / nil = not known yet) }; ("unstand", id)
--   ("give", id, type, key) / ("setstock", id, kind, n)   put a thing in a stand-in's save (saved)
--   ("inv", id)                         { inv = { type = { keys } }, stock, pend, done, trades = #, every }
--   ("gate", id, { level, age, policy }) / ("gate", id, nil)   a player's gate as if they were that level / age / policy
--   ("ask", standId, toId)  ("answer", standId, fromId, yes)  ("add"|"remove"|"stock"|"lock"|"unlock"|"confirm"|"cancel", standId, ...)
--                                       the stand-in does that (the same ops a player's remote does)
--   ("fail", "prepare"|"final"|"ledger", id, on)   that side's save write fails at that step (ledger: the decision)
--   ("crash", standId)                  the stand-in's save is dropped unwritten (a server dying); ("reload", standId) loads
--                                       it again from the store and finishes what was pending, like a rejoin
--   ("snap", id) / ("restore", id)      a copy of a save's things (inv, stock, fresh, every, trades, receipts) and back
--   ("clearlog", id)                    a save's trade history, receipts and pending copy cleared
--   ("state", id)  ("inbox", standId)  ("lookup", id)  ("trade", id)
local snaps: { [number]: any } = {}
function Trading.test(op: string, a: any, b: any, c: any, d: any): any
	if not STUDIO then return nil end
	if op == "on" then studioOn = true; Remote:SetAttribute("On", true); return true
	elseif op == "off" then studioOn = false; Remote:SetAttribute("On", Trading.on()); return false
	elseif op == "stand" then
		local id = tonumber(a) or -901
		if id >= 0 then return false end
		local o = if type(c) == "table" then c else {}
		stands[id] = { id = id, name = tostring(b or "Stand-in"), level = tonumber(o.level) or 10, age = tonumber(o.age) or 30,
			policy = if o.policy == nil then true else o.policy == true, zone = "hub", inbox = {} }
		if o.policy == "unknown" then stands[id].policy = nil end
		local h = Loot.testHandle(id)
		return { ok = h ~= nil, state = h and h.state() }
	elseif op == "unstand" then
		local id = tonumber(a) or 0
		left(id)
		stands[id] = nil
		Loot.testHandle(id, true)
		return true
	elseif op == "give" or op == "setstock" then
		local id = tonumber(a) or 0
		local h = handleOf(id)
		if not h then return false end
		if op == "give" then giveKey(h.data, tostring(b), tostring(c)) else
			h.data.stock = if type(h.data.stock) == "table" then h.data.stock else {}
			h.data.stock[tostring(b)] = tonumber(c) or 0
		end
		h.done()
		return h.save()
	elseif op == "inv" then
		local h = handleOf(tonumber(a) or 0)
		if not h then return nil end
		local d = h.data
		local inv = {}
		for _, t in R.TYPES do inv[t] = if type(d.inv) == "table" and type(d.inv[t]) == "table" then table.clone(d.inv[t]) else {} end
		return { inv = inv, stock = deepCopy(d.stock), pend = d.tradePend and d.tradePend.id, done = deepCopy(d.tradeDone),
			trades = if type(d.trades) == "table" then #d.trades else 0, every = deepCopy(d.every), state = h.state() }
	elseif op == "gate" then
		local id = tonumber(a) or 0
		testGate[id] = if type(b) == "table" then { level = tonumber(b.level), age = tonumber(b.age), policy = if b.policy == nil then nil else b.policy == true } else nil
		return true
	elseif op == "fail" then
		if a == "ledger" then testLedgerFail = c == true or b == true; return testLedgerFail end
		local list = testFail[tostring(a)]
		if not list then return false end
		list[tonumber(b) or 0] = if c == false then nil else true
		return true
	elseif op == "crash" then
		local id = tonumber(a) or 0
		return Loot.testHandle(id, "drop")
	elseif op == "reload" then
		local id = tonumber(a) or 0
		local h = Loot.testHandle(id)
		if not h then return { ok = false } end
		return { ok = true, resolved = resolve(h) }
	elseif op == "snap" then
		local h = handleOf(tonumber(a) or 0)
		if not h then return false end
		local d = h.data
		snaps[tonumber(a) or 0] = { inv = deepCopy(d.inv), stock = deepCopy(d.stock), fresh = deepCopy(d.fresh), freshN = d.freshN,
			every = deepCopy(d.every), trades = deepCopy(d.trades), tradeDone = deepCopy(d.tradeDone), tradePend = deepCopy(d.tradePend) }
		return true
	elseif op == "restore" then
		local id = tonumber(a) or 0
		local h, s = handleOf(id), snaps[id]
		if not h or not s then return false end
		-- (every field, the ones that were empty too: a test's trades and receipts go)
		for _, k in { "inv", "stock", "fresh", "freshN", "every", "trades", "tradeDone", "tradePend" } do h.data[k] = deepCopy(s[k]) end
		h.done()
		return h.save()
	elseif op == "clearlog" then
		-- (a save's trade history, receipts and pending copy cleared: test trades out of a Studio save)
		local h = handleOf(tonumber(a) or 0)
		if not h then return false end
		h.data.trades, h.data.tradeDone, h.data.tradePend = nil, nil, nil
		return h.save()
	elseif op == "state" then return stateFor(tonumber(a) or 0)
	elseif op == "inbox" then local s = stands[tonumber(a) or 0]; return s and s.inbox
	elseif op == "lookup" then return Trading.lookup(tonumber(a) or 0, tonumber(b))
	elseif op == "trade" then
		local tr = trades[tonumber(a) or 0]
		return tr and { id = tr.id, phase = tr.phase, a = tr.a, b = tr.b, offers = deepCopy(tr.offers) }
	else
		-- a stand-in does what a player's remote would
		local id = tonumber(a) or 0
		if not stands[id] then return { ok = false, why = "no such stand-in" } end
		if op == "ask" then op = "request" end
		return handle(id, op, b, c, d)
	end
end
function Trading.testHook()
	local old = ServerStorage:FindFirstChild("JankTradeTest")
	if old then old:Destroy() end
	local fn = Instance.new("BindableFunction")
	fn.Name = "JankTradeTest"
	fn.OnInvoke = function(op: string, a: any, b: any, c: any, d: any): any return Trading.test(op, a, b, c, d) end
	fn.Parent = ServerStorage
end

return Trading
