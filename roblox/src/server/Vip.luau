--!strict
-- VIP (the owner, 16 Nov: "the ducky set is a high tier set you get by purchasing vip, it comes with a couple skins, a
-- hat, a wrap, a border and a title? it also lets you enter the vip room?"). VIP is a game pass. this module decides who
-- is VIP (the only place that does) and hands them the VIP pack through the loot server.
--   who is VIP: the game pass (MarketplaceService:UserOwnsGamePassAsync on join, PromptGamePassPurchaseFinished for a
--   purchase made now) once Shop.VIP_PASS is set; while the shop is free (Shop.free(), Config.LOOT_FREE) anyone can
--   claim it from the shop ("Get VIP (free while testing)"), kept in a small save so it lasts; and the place's owner in
--   Studio can turn it on or off for a session (the "dev" op), to test the VIP room both ways.
--   the pack: the shop's offer "vip" (Shop.vipItems: every skin, wrap, hat and card look the loot module calls VIP-only),
--   given by Loot.grant(p, "vip", "vip-<signature>"): a pack that gains items later is granted again, once, and only the
--   new things land (the loot server skips what you own). VIP wraps and hats are worn on every gun.
-- for other server scripts (the hub's VIP room door):
--   local Vip = require(game.ServerScriptService.Jankfire:WaitForChild("Vip"))
--   Vip.isVip(player) -> boolean, Vip.changed:Connect(function(player, isVip) end)
-- for the clients: the player attribute "VIP" (true / nil), set here only (a client can't make itself VIP: never trust
-- it for a decision), and the remote JankfireRemotes.Vip (RemoteFunction, made here), which answers a table:
--   ("get")    -> { ok, vip, why ("pass" | "free" | "dev"), free, robux, pass, price, dev }
--   ("claim")  -> while free: VIP for good (saved); paid: { ok = false }
--   ("buy")    -> with Robux on and the pass made: Roblox's game pass prompt (the grant comes from the purchase event)
--   ("dev", "unlock" | "lock") -> Studio + the place's owner only: VIP on / off for this session (nothing saved)
-- docs: roblox/docs/SHOP.md (VIP)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local MarketplaceService = game:GetService("MarketplaceService")
local DataStoreService = game:GetService("DataStoreService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Shop = require(Shared:WaitForChild("Shop")) :: any

local Vip = {}

local changed = Instance.new("BindableEvent")
Vip.changed = changed.Event

local why: { [Player]: string } = {} -- who is VIP this session, and why
local devOff: { [Player]: boolean } = {} -- the owner's "lock" in Studio: not VIP this session, whatever else says so
local started = false

-- the free claims while testing, kept so a claim lasts (one small key per player; the loot save is the loot session's)
local store: DataStore? = nil
pcall(function() store = DataStoreService:GetDataStore("JankfireVip_v1") end)

local function loot(): any
	local m = script.Parent:FindFirstChild("Loot")
	if not (m and m:IsA("ModuleScript")) then return nil end
	local ok, L = pcall(require, m)
	return if ok and type(L) == "table" then L else nil
end

-- the place's owner, in Studio only (the same rule as the loot server's test tools)
local function isDev(p: Player): boolean
	if not RunService:IsStudio() then return false end
	if game.CreatorType == Enum.CreatorType.User then return p.UserId == game.CreatorId end
	local ok, rank = pcall(function() return p:GetRankInGroup(game.CreatorId) end)
	return ok and rank == 255
end

function Vip.isVip(p: Player): boolean
	return why[p] ~= nil and not devOff[p]
end
function Vip.reason(p: Player): string?
	return if Vip.isVip(p) then why[p] else nil
end

-- the pack's receipt id: the things in it, so a pack that grows is granted again (only the new things land)
local function packId(): string
	local keys = {}
	for _, it in Shop.vipItems() do table.insert(keys, it.kind .. ":" .. it.id) end
	table.sort(keys)
	local s = table.concat(keys, ",")
	local x = 0
	for i = 1, #s do x = (x * 31 + string.byte(s, i)) % 1000003 end
	return "vip-" .. #keys .. "-" .. x
end

-- hand over the pack once the player's loot save is loaded (a minute at most)
local function grantPack(p: Player)
	if #Shop.vipItems() == 0 then return end
	local id = packId()
	for _ = 1, 60 do
		if not p.Parent or not Vip.isVip(p) then return end
		local L = loot()
		if L and type(L.grant) == "function" and (type(L.ready) ~= "function" or L.ready(p)) then
			local ok, done = pcall(L.grant, p, "vip", id)
			if ok and done == true then return end
		end
		task.wait(1)
	end
	warn("[jankfire] vip: couldn't hand " .. p.Name .. " the VIP pack")
end

local function show(p: Player)
	local on = Vip.isVip(p)
	if (p:GetAttribute("VIP") == true) ~= on then
		p:SetAttribute("VIP", if on then true else nil)
		changed:Fire(p, on)
	end
	if on then task.spawn(grantPack, p) end
end

local function make(p: Player, reason: string)
	if not p.Parent then return end
	-- (a game pass outranks a free claim, which outranks the owner's test unlock)
	local rank: { [string]: number } = { dev = 1, free = 2, pass = 3 }
	local had = why[p]
	if had and (rank[had] or 0) >= (rank[reason] or 0) then show(p); return end
	why[p] = reason
	show(p)
end

-- does this player own the pass? (false when the pass isn't made yet or Roblox doesn't answer)
local function ownsPass(p: Player): boolean
	local pass = tonumber(Shop.VIP_PASS) or 0
	if pass <= 0 then return false end
	for _ = 1, 3 do
		local ok, has = pcall(function() return MarketplaceService:UserOwnsGamePassAsync(p.UserId, pass) end)
		if ok then return has == true end
		task.wait(1)
	end
	return false
end

-- a free claim from before (only counts while the shop is free)
local function claimedFree(p: Player): boolean
	if not Shop.free() or not store then return false end
	local s = store :: DataStore
	for _ = 1, 3 do
		local ok, v = pcall(function() return s:GetAsync("u" .. p.UserId) end)
		if ok then return type(v) == "table" and v.free == true end
		task.wait(1)
	end
	return false
end

local function joined(p: Player)
	if ownsPass(p) then make(p, "pass") return end
	if claimedFree(p) then make(p, "free") end
end

local lastAsk: { [Player]: number } = {}
local function handle(p: Player, op: unknown, a: unknown): any
	if op == "get" then
		return { ok = true, vip = Vip.isVip(p), why = Vip.reason(p), free = Shop.free(), robux = Shop.ROBUX == true,
			pass = tonumber(Shop.VIP_PASS) or 0, price = Shop.vip and Shop.vip.robux or 0, dev = isDev(p) }
	end
	local now = os.clock()
	if (lastAsk[p] or 0) > now - 1 then return { ok = false, why = "slow down" } end
	lastAsk[p] = now
	if op == "claim" then
		if Vip.isVip(p) then return { ok = true, vip = true } end
		if not Shop.free() then return { ok = false, why = "vip is a game pass now" } end
		-- (saved first, so the claim lasts; if the save is down it still counts for this session)
		if store then
			local s = store :: DataStore
			pcall(function() s:UpdateAsync("u" .. p.UserId, function() return { free = true, at = os.time() } end) end)
		end
		devOff[p] = nil
		make(p, "free")
		return { ok = true, vip = true }
	elseif op == "buy" then
		local pass = tonumber(Shop.VIP_PASS) or 0
		if Shop.free() then return { ok = false, why = "it's free while we test: claim it" } end
		if not Shop.ROBUX or pass <= 0 then return { ok = false, why = "not for sale yet" } end
		if Vip.isVip(p) then return { ok = true, vip = true } end
		MarketplaceService:PromptGamePassPurchase(p, pass)
		return { ok = true, prompted = true }
	elseif op == "dev" then
		if not isDev(p) then return { ok = false, why = "nope" } end
		if a == "unlock" then
			devOff[p] = nil
			make(p, "dev")
		elseif a == "lock" then
			devOff[p] = true
			show(p)
		else
			return { ok = false, why = "unlock or lock" }
		end
		return { ok = true, vip = Vip.isVip(p) }
	end
	return { ok = false, why = "nope" }
end

-- start once (on the first require, below)
function Vip.start()
	if started then return end
	started = true
	local remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
	local rf = remotes:FindFirstChild("Vip") :: RemoteFunction?
	if not rf then
		local made = Instance.new("RemoteFunction")
		made.Name = "Vip"
		made.Parent = remotes
		rf = made
	end
	local remote = rf :: RemoteFunction
	remote.OnServerInvoke = function(p: Player, op: unknown, a: unknown)
		local ok, res = pcall(handle, p, op, a)
		if not ok then
			warn("[jankfire] vip: " .. tostring(res))
			return { ok = false, why = "something broke. try again" }
		end
		return res
	end
	MarketplaceService.PromptGamePassPurchaseFinished:Connect(function(p: Player, passId: number, bought: boolean)
		if bought and passId == (tonumber(Shop.VIP_PASS) or 0) and passId > 0 then make(p, "pass") end
	end)
	Players.PlayerAdded:Connect(function(p) task.spawn(joined, p) end)
	for _, p in Players:GetPlayers() do task.spawn(joined, p) end
	Players.PlayerRemoving:Connect(function(p)
		why[p] = nil; devOff[p] = nil; lastAsk[p] = nil
	end)
end

-- (it starts on the first require: the shop's ShopReceipts requires it at server start, the hub's door may too)
Vip.start()
return Vip
