--!strict
-- THE OWNER'S DEALS (the owner, 17 Nov 2026: "I give players 3 special discounts on random skins if you talk to me!").
-- the owner's shopkeeper in the training area's gun shop has a prompt (the training session's ShopKeeper.server.luau:
-- ShopOpen = "tab:deals") that opens the shop on DEALS. the rules are Shared.Shop's (DEAL_OFF, DEAL_TOP, DEAL_PICK,
-- dealPrice); this picks and keeps them.
--   per player per UTC day: three weapon skins on sale they don't own, picked by rarity weight (DEAL_PICK), at most one
--   legendary, a different skin set and a different gun each where it can; each DEAL_OFF[rarity] % off, the rarest of
--   the three DEAL_TOP more. picked the first time the player asks that day and kept (one session-locked profile,
--   Profiles.luau, "JankfireDeals_v1", "_studio" in Studio), so they're the same all day. each can be had once.
--   free while the shop is (Shop.free()): "buy" here grants it (Loot.grant "skin:<id>", receipt "deal-<uid>-<day>-<id>").
--   with Robux on: the client sends ShopBuy "deal:<skin>"; ShopReceipts asks Deals.offerFor and, on the receipt,
--   Deals.grant(p, skin, purchaseId).
-- the remote JankfireRemotes.Deals (RemoteFunction), always a table:
--   ("get")        -> { ok, day, left (s), free, robux, deals = { { skin, weapon, name, rarity, pct, was, price, bought,
--                     owned } } }
--   ("buy", skin)  -> while free: { ok, why? }
-- Studio test: ServerStorage.JankDealsTest (BindableFunction): ("state", p), ("reset", p) (new picks on the next get)
-- docs: roblox/docs/SHOP.md (The owner's deals)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Shop = require(Shared:WaitForChild("Shop")) :: any
local Profiles = require(script.Parent:WaitForChild("Profiles"))
local Loot = require(script.Parent:WaitForChild("Loot")) :: any

local STUDIO = RunService:IsStudio()
local Deals = {}

local store = Profiles.new("JankfireDeals_v1" .. (if STUDIO then "_studio" else ""), function()
	return { day = -1, deals = {} }
end)
local profs: { [Player]: any } = {}
local lastAsk: { [Player]: number } = {}
local rng = Random.new()
local started = false

local function day(): number return math.floor(os.time() / 86400) end

-- the skin set a skin is in (SkinSets), for variety
local function setOf(id: string): string?
	local K = Shop.SkinSets :: any
	if not K or type(K.SETS) ~= "table" then return nil end
	for sid, s in K.SETS do
		if table.find(s.members or {}, id) then return sid end
	end
	return nil
end

-- today's three for this player
local function roll(p: Player): { any }
	local pool = {}
	for _, id in Shop.liveSkins() do
		local _, r = Shop.itemInfo("skin", id)
		if Shop.DEAL_PICK[r] and not Loot.owns(p, "skin", id) then
			table.insert(pool, { id = id, r = r, gun = Shop.skinWeapon(id), set = setOf(id) })
		end
	end
	local picked = {}
	local usedSet, usedGun, legend = {}, {}, false
	for _ = 1, Shop.DEALS do
		local total, ws = 0, {}
		for i, c in pool do
			local w = Shop.DEAL_PICK[c.r] or 0
			if c.set and usedSet[c.set] then w *= 0.1 end
			if c.gun and usedGun[c.gun] then w *= 0.25 end
			if c.r == "legendary" and legend then w = 0 end
			ws[i] = w
			total += w
		end
		if total <= 0 then break end
		local x = rng:NextNumber() * total
		local at = #pool
		for i, w in ws do
			x -= w
			if x < 0 then at = i; break end
		end
		local c = table.remove(pool, at)
		table.insert(picked, c)
		if c.set then usedSet[c.set] = true end
		if c.gun then usedGun[c.gun] = true end
		if c.r == "legendary" then legend = true end
	end
	-- (rarest first; the first gets the extra off)
	table.sort(picked, function(a, b)
		if Shop.rank(a.r) ~= Shop.rank(b.r) then return Shop.rank(a.r) > Shop.rank(b.r) end
		return a.id < b.id
	end)
	local out = {}
	for i, c in picked do
		table.insert(out, { skin = c.id, pct = (Shop.DEAL_OFF[c.r] or 20) + (if i == 1 then Shop.DEAL_TOP else 0), bought = false })
	end
	return out
end

-- the player's data with today's deals in it (picked now if they're not yet); nil while loading
local function today(p: Player): any?
	local prof = profs[p]
	if not prof or (prof.state ~= "cloud" and prof.state ~= "off") then return nil end
	local d = prof.data
	local t = day()
	if d.day ~= t then
		if type(Loot.ready) == "function" and not Loot.ready(p) then return nil end
		d.day = t
		d.deals = roll(p)
		prof.dirty = true
		task.spawn(Profiles.save, store, prof)
	end
	-- (a skin set's piece is never on a deal, the owner, 18 Nov: one picked before that goes. nothing had today: a new
	-- three; else just without it)
	local kept, had = {}, false
	for _, x in d.deals do
		if x.bought then had = true end
		if not (type(x.skin) == "string" and Shop.setOnly("skin", x.skin)) then table.insert(kept, x) end
	end
	if #kept ~= #d.deals then
		d.deals = if had then kept else roll(p)
		prof.dirty = true
		task.spawn(Profiles.save, store, prof)
	end
	return d
end

local function find(d: any, skin: unknown): any?
	if type(skin) ~= "string" then return nil end
	for _, x in d.deals do if x.skin == skin then return x end end
	return nil
end

-- one of today's deals, not had yet, for ShopReceipts (Robux): { skin, rarity, pct, price }
function Deals.offerFor(p: Player, skin: string): any?
	local d = today(p)
	local x = d and find(d, skin)
	if not x or x.bought or Loot.owns(p, "skin", skin) then return nil end
	local _, r = Shop.itemInfo("skin", skin)
	return { skin = skin, rarity = r, pct = x.pct, price = Shop.dealPrice("skin", skin, x.pct) }
end

-- give a deal's skin (true = written): the shop's free claim, or a Robux receipt (purchaseId)
function Deals.grant(p: Player, skin: string, purchaseId: any?): boolean
	local d = today(p)
	local x = d and find(d, skin)
	if not x then return false end
	local rid = if purchaseId ~= nil then tostring(purchaseId) else ("deal-%d-%d-%s"):format(p.UserId, d.day, skin)
	local ok, done = pcall(Loot.grant, p, "skin:" .. skin, rid)
	if not ok then warn("[jankfire] deals: Loot.grant: " .. tostring(done)) end
	if not (ok and done == true) then return false end
	x.bought = true
	local prof = profs[p]
	if prof then prof.dirty = true; task.spawn(Profiles.save, store, prof) end
	return true
end

local function view(p: Player, d: any): any
	local list = {}
	for _, x in d.deals do
		local name, r = Shop.itemInfo("skin", x.skin)
		table.insert(list, { skin = x.skin, weapon = Shop.skinWeapon(x.skin), name = name, rarity = r, pct = x.pct,
			was = Shop.singlePrice("skin", x.skin), price = Shop.dealPrice("skin", x.skin, x.pct), bought = x.bought == true,
			owned = Loot.owns(p, "skin", x.skin) == true })
	end
	return { ok = true, day = d.day, left = (d.day + 1) * 86400 - os.time(), free = Shop.free(), robux = Shop.ROBUX == true, deals = list }
end

local function handle(p: Player, op: unknown, a: unknown): any
	local now = os.clock()
	if (lastAsk[p] or 0) > now - 0.4 then return { ok = false, why = "slow down" } end
	lastAsk[p] = now
	local d = today(p)
	if not d then return { ok = false, why = "your stuff is still loading" } end
	if op == "get" then return view(p, d) end
	if op == "buy" then
		local x = find(d, a)
		if not x then return { ok = false, why = "that's not one of today's deals" } end
		if x.bought then return { ok = false, why = "you've had that deal" } end
		if Loot.owns(p, "skin", x.skin) then return { ok = false, why = "you have it already" } end
		if not Shop.free() then return { ok = false, why = if Shop.ROBUX then "buy it with robux" else "the shop is shut" } end
		if not Deals.grant(p, x.skin) then return { ok = false, why = "couldn't hand it over. try again" } end
		return { ok = true }
	end
	return { ok = false, why = "nope" }
end

local function joined(p: Player)
	local prof = Profiles.load(store, "u" .. p.UserId, function() return p.Parent ~= nil end)
	if not prof then return end
	if not p.Parent then Profiles.release(store, prof); return end
	profs[p] = prof
end

function Deals.test(op: string, a: any): any
	if not STUDIO then return nil end
	local prof = profs[a]
	if not prof then return nil end
	if op == "state" then return { day = prof.data.day, deals = prof.data.deals, state = prof.state } end
	if op == "reset" then prof.data.day = -1; prof.dirty = true; return true end
	return nil
end

function Deals.start()
	if started then return end
	started = true
	local remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
	local rf = remotes:FindFirstChild("Deals") :: RemoteFunction?
	if not rf then
		local made = Instance.new("RemoteFunction")
		made.Name = "Deals"
		made.Parent = remotes
		rf = made
	end
	(rf :: RemoteFunction).OnServerInvoke = function(p: Player, op: unknown, a: unknown)
		local ok, res = pcall(handle, p, op, a)
		if not ok then
			warn("[jankfire] deals: " .. tostring(res))
			return { ok = false, why = "something broke. try again" }
		end
		return res
	end
	Players.PlayerAdded:Connect(function(p) task.spawn(joined, p) end)
	for _, p in Players:GetPlayers() do task.spawn(joined, p) end
	Players.PlayerRemoving:Connect(function(p)
		local prof = profs[p]
		profs[p] = nil; lastAsk[p] = nil
		if prof then Profiles.release(store, prof) end
	end)
	if STUDIO then
		local bf = ServerStorage:FindFirstChild("JankDealsTest") :: BindableFunction?
		if not bf then
			local made = Instance.new("BindableFunction")
			made.Name = "JankDealsTest"
			made.Parent = ServerStorage
			bf = made
		end
		(bf :: BindableFunction).OnInvoke = function(op, a) return Deals.test(op, a) end
	end
end

Deals.start()
return Deals
