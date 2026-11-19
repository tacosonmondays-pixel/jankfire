--!strict
-- PAID GIFTS (19 Nov 2026, the owner: "weapon bundles should be gamepasses too! I want people to be able to gift them!
-- Should all passes be game passes?"). Roblox can't gift a game pass (one is only ever bought for your own account), so a
-- gift is a developer product bought for someone else:
--   the buyer picks the receiver in the shop (someone in this server, or by user name if they've played before: a save
--   of theirs exists), the shop prompts the offer's own product, and ShopReceipts calls Gifts.send with the receipt.
--   send writes the gift into the receiver's GIFT BOX (its own data store: "JankfireGiftBox_v1", "_studio" in Studio,
--   one key per receiver) BEFORE the receipt is granted, so a crash never loses one.
--   the box is emptied into the receiver's things the moment they're in a server: this one at once, another one told over
--   MessagingService ("jf_gift"), or when they next join. each gift is given once (every grant behind it is idempotent
--   by "gift:<purchaseId>"), then moved out of the box.
--   the receiver sees the present's reveal (GiftReveal.client, DevFx "gift"); everyone in the receiver's server (and the
--   buyer's, if that's another) reads the chat line "<buyer> gifted <receiver> <what>" (DevFx "giftchat"); the buyer's
--   shop says it went (the Gifts remote's "sent" note).
-- what can be gifted: Shop.giftable (bundles, weapon bundles, a whole skin set, coin packs; VIP through its own
-- product "vipgift"). never a container or a single. the switch: Shop.giftsOn (OFF until the owner has seen it).
-- a receiver Roblox's policy keeps from paid random items gets no container: a coin pack's Crates come as coins
-- (Purchases.packExtras decides that for the receiver). docs: roblox/docs/MONEY.md (Gifts)
-- for other server scripts:
--   Gifts.check(buyer, toUserId) -> (ok, why?)                      a receiver the shop can gift to right now
--   Gifts.send(buyer, toUserId, offerId, purchaseId) -> boolean     written to their box (the receipt can be granted)
-- the remote JankfireRemotes.Gifts (RemoteFunction, made here):
--   ("find", name)  -> { ok, id, name, display } | { ok = false, why }   someone not in this server, by user name
--   ("dev", "box")  -> Studio + the place's owner: their own box
-- and JankfireRemotes.GiftNote (RemoteEvent): the buyer's { k = "sent", to = name, what = name }
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local DataStoreService = game:GetService("DataStoreService")
local MessagingService = game:GetService("MessagingService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Shop = require(Shared:WaitForChild("Shop")) :: any
local LootTable = require(Shared:WaitForChild("LootTable")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local STUDIO = RunService:IsStudio()
local Gifts = {}
local DONE_KEPT = 100 -- (the newest given gift ids a box remembers: a receipt sent again can't give twice)
local TOPIC = "jf_gift"

local box: DataStore? = nil
local lootSaves: DataStore? = nil -- (someone has played before: their loot save exists, Loot.luau's store)
pcall(function()
	box = DataStoreService:GetDataStore(if STUDIO then "JankfireGiftBox_v1_studio" else "JankfireGiftBox_v1")
	lootSaves = DataStoreService:GetDataStore(if STUDIO then "JankfireLoot_v1_studio" else "JankfireLoot_v1")
end)

local function remote(name: string, class: string): Instance
	local r = Remotes:FindFirstChild(name)
	if not r then
		r = Instance.new(class)
		;(r :: Instance).Name = name
		;(r :: Instance).Parent = Remotes
	end
	return r :: Instance
end
local Remote = remote("Gifts", "RemoteFunction") :: RemoteFunction
local Note = remote("GiftNote", "RemoteEvent") :: RemoteEvent

local mods: { [string]: any } = {}
local function module(name: string): any
	local m = mods[name]
	if m ~= nil then return m or nil end
	local sc = script.Parent:FindFirstChild(name)
	local ok, r = false, nil
	if sc and sc:IsA("ModuleScript") then ok, r = pcall(require, sc) end
	mods[name] = if ok and type(r) == "table" then r else false
	return mods[name] or nil
end
local function devFx(): RemoteEvent?
	local r = Remotes:FindFirstChild("DevFx")
	return if r and r:IsA("RemoteEvent") then r else nil
end

-- the place's owner, in Studio only (the test tools)
local function isDev(p: Player): boolean
	if not STUDIO then return false end
	if game.CreatorType == Enum.CreatorType.User then return p.UserId == game.CreatorId end
	local ok, rank = pcall(function() return p:GetRankInGroup(game.CreatorId) end)
	return ok and rank == 255
end

-- the offer a gift is for (a coin pack: "coins:<id>"), giftable
local function offerOf(id: any): any
	if type(id) ~= "string" then return nil end
	local o = if string.match(id, "^coins:[%w_]+$") then Shop.coinPack(id) else (Shop.byId[id] or Shop.offer(id))
	return if o and Shop.giftable(o) then o else nil
end
-- its plain name for the chat line and the toasts: "the Assault bundle", "the Seraph skin set", "6,500 Coins", "VIP"
local function words(o: any): string
	if o.type == "coins" then return tostring(o.name) end
	if o.type == "vipgift" then return "VIP" end
	if o.type == "single" then return "the " .. tostring(o.name) .. " skin" end
	if o.type == "container" then return "a " .. tostring(o.name) end
	if o.set then return "the " .. tostring(o.name) .. " skin set" end
	return "the " .. tostring(o.name) .. " bundle"
end
-- what the receiver's present reveals (the loot opening's cards: GiftReveal.client)
local function revealItems(o: any): { any }
	local items = {}
	if o.type == "coins" then
		return { { type = "brass", id = "brass", name = "Coins", rarity = "rare", n = o.amount } }
	elseif o.type == "vipgift" then
		return { { type = "vip", id = "vip", name = "VIP", rarity = "vip" } }
	elseif o.type == "container" then
		return { { type = "container", id = o.id, name = o.name, rarity = o.rarity or "rare", n = 1 } }
	elseif o.type == "single" then
		return { { type = o.kind, id = o.item, name = o.name, rarity = o.rarity, weapon = o.weapon } }
	end
	local Roster = require(Shared:WaitForChild("Roster")) :: any
	for _, wid in (o.weapons or {}) :: { string } do
		local e = Roster.byId[wid]
		if e then table.insert(items, { type = "weapon", id = wid, name = e.name, rarity = "legendary" }) end
	end
	for _, it in (Shop.contents(o) or {}) :: { any } do
		local inf = type(it) == "table" and LootTable.info(it.kind, it.id)
		if inf and #items < 12 then table.insert(items, { type = it.kind, id = it.id, name = inf.name, rarity = inf.rarity, weapon = it.weapon or inf.weapon }) end
	end
	return items
end

-- ------------------------------------------------------------------ who can be gifted to
local found: { [Player]: { [number]: number } } = {} -- (the buyer's "find" answers: receiver id -> when)
local lastFind: { [Player]: number } = {}
function Gifts.check(buyer: Player, to: any): (boolean, string?)
	if not Shop.giftsOn() then return false, "gifts aren't on yet" end
	if type(to) ~= "number" or to ~= math.floor(to) or to <= 0 then return false, "who to?" end
	if to == buyer.UserId then return false, "that's you" end
	if Players:GetPlayerByUserId(to) then return true, nil end
	local f = found[buyer]
	if f and f[to] and os.clock() - f[to] < 900 then return true, nil end
	return false, "find them by name first"
end
local function find(p: Player, name: any): any
	if type(name) ~= "string" or #name < 3 or #name > 20 or not string.match(name, "^[%w_]+$") then
		return { ok = false, why = "a Roblox user name, 3 to 20 letters, numbers or _" }
	end
	local now = os.clock()
	if now - (lastFind[p] or 0) < 2 then return { ok = false, why = "one at a time" } end
	lastFind[p] = now
	local okId, id = pcall(function() return Players:GetUserIdFromNameAsync(name) end)
	if not okId or type(id) ~= "number" then return { ok = false, why = "no one called that" } end
	if id == p.UserId then return { ok = false, why = "that's you" } end
	-- (played before: a save of theirs exists. in this server: of course)
	if not Players:GetPlayerByUserId(id) then
		local s = lootSaves
		if not s then return { ok = false, why = "can't look them up right now" } end
		local okG, v = pcall(function() return (s :: DataStore):GetAsync("u" .. id) end)
		if not okG then return { ok = false, why = "can't look them up right now" } end
		if v == nil then return { ok = false, why = "they haven't played here yet" } end
	end
	local display = name
	pcall(function()
		local info = Players:GetUserInfosByUserIdsAsync({ id })
		if type(info) == "table" and type(info[1]) == "table" then
			name = info[1].Username or name
			display = info[1].DisplayName or name
		end
	end)
	found[p] = found[p] or {}
	;(found[p] :: any)[id] = os.clock()
	return { ok = true, id = id, name = name, display = display }
end

-- ------------------------------------------------------------------ the box
-- give one gift (true = all of it is written; every grant is idempotent by gid)
local function giveOne(p: Player, g: any, gid: string): boolean
	local o = offerOf(g.offer)
	if not o then warn("[jankfire] gifts: a gift of " .. tostring(g.offer) .. " the shop doesn't know"); return true end -- (dropped: nothing to give)
	if o.type == "vipgift" then
		local V = module("Vip")
		if not V or type(V.gift) ~= "function" then return false end
		local ok, res = pcall(V.gift, p, true)
		return ok and res == true
	elseif o.type == "coins" then
		local Q, P = module("Quests"), module("Purchases")
		if not Q or type(Q.buyBrass) ~= "function" then return false end
		local ok, res = pcall(Q.buyBrass, p, o.amount, gid)
		if not ok or res ~= true then return false end
		if o.extras and Shop.packExtrasOn() then
			if not P or type(P.packExtras) ~= "function" then return false end
			local okE, resE = pcall(P.packExtras, p, o, gid)
			return okE and resE == true
		end
		return true
	end
	-- a container: one in their stock, or its coins where Roblox's policy keeps them from paid random items
	if o.type == "container" then
		local L, Q = module("Loot"), module("Quests")
		if not L or type(L.grant) ~= "function" then return false end
		if type(L.restricted) ~= "function" or L.restricted(p) then
			if not Q or type(Q.buyBrass) ~= "function" then return false end
			local ok, res = pcall(Q.buyBrass, p, Shop.coinPrice(o, 1) or 0, gid)
			return ok and res == true
		end
		local ok, res = pcall(L.grant, p, o.id, gid)
		return ok and res == true
	end
	-- a bundle, a weapon bundle, a skin set or a single skin: its weapons, then its things (the ones they lack)
	if o.weapons then
		local P = module("Purchases")
		if not P or type(P.giveWeapon) ~= "function" then return false end
		for _, wid in o.weapons :: { string } do
			local ok, res = pcall(P.giveWeapon, p, wid, "gift", gid)
			if not ok or res ~= true then return false end
		end
	end
	local L = module("Loot")
	if not L or type(L.grant) ~= "function" then return false end
	local ok, res = pcall(L.grant, p, o.id, gid)
	return ok and res == true
end
local delivering: { [Player]: boolean } = {}
local again: { [Player]: boolean } = {}
local function deliver(p: Player)
	if delivering[p] then again[p] = true; return end
	local s = box
	if not s then return end
	delivering[p] = true
	repeat
		again[p] = false
		local okG, v = pcall(function() return (s :: DataStore):GetAsync("u" .. p.UserId) end)
		local list = {}
		if okG and type(v) == "table" and type(v.box) == "table" then
			for gid, g in v.box do if type(gid) == "string" and type(g) == "table" then table.insert(list, { gid = gid, g = g }) end end
		end
		table.sort(list, function(a, b) return (tonumber(a.g.t) or 0) < (tonumber(b.g.t) or 0) end)
		local given = {}
		for _, x in list do
			-- (their saves may still be loading: a few tries over a minute, then the next join)
			local done = false
			for _ = 1, 12 do
				if not p.Parent then break end
				if giveOne(p, x.g, x.gid) then done = true; break end
				task.wait(5)
			end
			if not done then break end
			table.insert(given, x.gid)
			local o = offerOf(x.g.offer)
			if o then
				local fx = devFx()
				local who = tostring(x.g.fromName or "someone")
				if fx then
					fx:FireClient(p, { k = "gift", text = "GIFT · " .. string.upper(if o.type == "coins" then o.name elseif o.type == "vipgift" then "VIP" else o.name),
						from = who, items = revealItems(o) })
					fx:FireAllClients({ k = "giftchat", text = ("%s gifted %s %s"):format(who, p.DisplayName, words(o)) })
				end
				print(("[jankfire] gifts: %s got %s from %s"):format(p.Name, tostring(x.g.offer), who))
			end
		end
		if #given > 0 then
			pcall(function()
				(s :: DataStore):UpdateAsync("u" .. p.UserId, function(old: any)
					local w = if type(old) == "table" then old else {}
					w.box = if type(w.box) == "table" then w.box else {}
					w.done = if type(w.done) == "table" then w.done else {}
					for _, gid in given do
						w.box[gid] = nil
						if not table.find(w.done, gid) then table.insert(w.done, gid) end
					end
					while #w.done > DONE_KEPT do table.remove(w.done, 1) end
					return w
				end)
			end)
		end
	until not again[p] or not p.Parent
	delivering[p] = nil
end

-- the gift, into the receiver's box (true once written: the receipt can be granted)
function Gifts.send(buyer: Player, to: number, offerId: string, purchaseId: string): boolean
	local s = box
	local o = offerOf(offerId)
	if not s or not o or type(to) ~= "number" then return false end
	local gid = "gift:" .. purchaseId
	local ok = pcall(function()
		(s :: DataStore):UpdateAsync("u" .. to, function(old: any)
			local w = if type(old) == "table" then old else {}
			w.box = if type(w.box) == "table" then w.box else {}
			w.done = if type(w.done) == "table" then w.done else {}
			if w.box[gid] or table.find(w.done, gid) then return w end -- (this receipt again: it's there already)
			w.box[gid] = { offer = o.id, from = buyer.UserId, fromName = buyer.DisplayName, t = os.time() }
			return w
		end)
	end)
	if not ok then return false end
	-- hand it over: here, or wherever they are
	local here = Players:GetPlayerByUserId(to)
	if here then
		task.spawn(deliver, here)
	else
		task.spawn(function() pcall(function() MessagingService:PublishAsync(TOPIC, { to = to }) end) end)
	end
	-- the buyer: a note, and the chat line in their server when the receiver is somewhere else
	local toName = if here then here.DisplayName else nil
	if not toName then
		pcall(function()
			local info = Players:GetUserInfosByUserIdsAsync({ to })
			if type(info) == "table" and type(info[1]) == "table" then toName = info[1].DisplayName end
		end)
	end
	if buyer.Parent then Note:FireClient(buyer, { k = "sent", to = toName or "them", what = words(o) }) end
	if not here then
		local fx = devFx()
		if fx then fx:FireAllClients({ k = "giftchat", text = ("%s gifted %s %s"):format(buyer.DisplayName, toName or "a friend", words(o)) }) end
	end
	print(("[jankfire] gifts: %s sent %s to %d"):format(buyer.Name, o.id, to))
	return true
end

Remote.OnServerInvoke = function(p: Player, op: unknown, a: unknown, b: unknown): any
	local ok, res = pcall(function(): any
		if op == "find" then
			if not Shop.giftsOn() then return { ok = false, why = "gifts aren't on yet" } end
			return find(p, a)
		elseif op == "dev" and a == "box" then
			if not isDev(p) then return { ok = false, why = "nope" } end
			local s = box
			if not s then return { ok = false, why = "no store" } end
			local okG, v = pcall(function() return (s :: DataStore):GetAsync("u" .. p.UserId) end)
			return { ok = okG, box = if okG then v else nil }
		end
		return { ok = false, why = "nope" }
	end)
	if not ok then warn("[jankfire] gifts: " .. tostring(res)); return { ok = false, why = "something broke. try again" } end
	return res
end

-- a receiver joins (or is told they have one in another server): the box, once their saves have had a moment
Players.PlayerAdded:Connect(function(p) task.delay(8, function() if p.Parent then deliver(p) end end) end)
for _, p in Players:GetPlayers() do task.delay(8, function() if p.Parent then deliver(p) end end) end
Players.PlayerRemoving:Connect(function(p) found[p] = nil; lastFind[p] = nil; again[p] = nil end)
if not STUDIO then
	task.spawn(function()
		pcall(function()
			MessagingService:SubscribeAsync(TOPIC, function(msg: any)
				local d = msg and msg.Data
				local to = type(d) == "table" and tonumber(d.to)
				local p = to and Players:GetPlayerByUserId(to)
				if p then task.spawn(deliver, p) end
			end)
		end)
	end)
end

return Gifts
