-- real-money purchases for the shop. OFF: while Shared.Shop.ROBUX is false this script prompts nothing and does not
-- even set MarketplaceService.ProcessReceipt (only one script in a game may set it), so nothing can be charged.
-- (Studio only: a play test of the paid shop sets ReplicatedStorage's MoneyTest = true from the Play server; Shop.ROBUX
-- follows it and this sets ProcessReceipt then. Studio test purchases charge nothing. docs/MONEY.md)
-- when it's on:
--   the client asks (JankfireRemotes.ShopBuy, an offer id); this checks the offer is on sale and has a developer
--   product (Shop.PRODUCTS), remembers which offer you asked for, and shows Roblox's purchase prompt. the ids:
--     a container, bundle, skin set or single (Shop.offer), "deal:<skin>" (one of your deals today),
--     "weapon:<id>" (a Robux weapon you don't have: Shop.weaponOffer), "coins:<pack>" (coins: Shop.coinPack)
--   Roblox calls ProcessReceipt; this
--     1. answers PurchaseGranted at once for a receipt it granted before (Purchases.seen: the receipt record, a save
--        per player, split from live in Studio);
--     2. works out what was bought from the product (for a shared product, "wrap:epic" or a deal's, the one you asked
--        for) and grants it: Loot.grant(player, offerId, purchaseId) for loot, Deals.grant for a deal,
--        Purchases.giveWeapon for a weapon, Quests.buyBrass for coins (Brass in the code). each is written to its save BEFORE it answers
--        true, and each is idempotent by the purchase id (a receipt Roblox sends twice is granted once even if step 3
--        was lost);
--     3. marks the receipt (Purchases.mark) and only then tells Roblox PurchaseGranted. anything that fails:
--        NotProcessedYet, and Roblox asks again later (the player's next join).
-- see roblox/docs/SHOP.md and roblox/docs/MONEY.md
local Players = game:GetService("Players")
local MarketplaceService = game:GetService("MarketplaceService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shop = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Shop"))
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("ShopBuy") :: RemoteEvent

-- VIP (a game pass, not a developer product: no receipt here) is Vip.luau's, its daily reward from Trisangle
-- VipDaily.luau's, the owner's deals Deals.luau's and the Robux weapons and receipt record Purchases.luau's; requiring
-- them starts them
for _, name in { "Vip", "VipDaily", "Deals", "Purchases" } do
	task.spawn(function()
		local m = script.Parent:WaitForChild(name, 30)
		if m and m:IsA("ModuleScript") then
			local ok, err = pcall(require, m)
			if not ok then warn("[jankfire] " .. string.lower(name) .. " didn't start: " .. tostring(err)) end
		end
	end)
end

local ASK_TTL = 600 -- s: how long a "this single, please" waits for its receipt
local asked: { [string]: { offer: string, product: number, t: number } } = {} -- ("<userId>:<productId>")
local lastAsk: { [Player]: number } = {}

local function module(name: string): any
	local m = script.Parent:FindFirstChild(name)
	if not (m and m:IsA("ModuleScript")) then return nil end
	local ok, M = pcall(require, m)
	return if ok and type(M) == "table" then M else nil
end
local function loot(): any return module("Loot") end
local function deals(): any return module("Deals") end -- (the owner's deals: "deal:<skin>", only the player's own of today)
local function purchases(): any return module("Purchases") end
local function quests(): any return module("Quests") end

local function prompt(p: Player, offerId: string, pid: number)
	asked[p.UserId .. ":" .. pid] = { offer = offerId, product = pid, t = os.clock() } -- (per product: a second ask can't strand the first's receipt)
	MarketplaceService:PromptProductPurchase(p, pid)
end

Remote.OnServerEvent:Connect(function(p: Player, offerId: unknown)
	if not Shop.ROBUX or Shop.free() then return end
	if type(offerId) ~= "string" then return end
	local now = os.clock()
	if (lastAsk[p] or 0) > now - 1 then return end
	lastAsk[p] = now
	-- a Robux weapon: only one you don't have yet (a second buy would pay for nothing)
	local wid = string.match(offerId, "^weapon:([%w_]+)$")
	if wid then
		local wo = Shop.weaponOffer(wid)
		local P = purchases()
		if not wo or not P or not P.ready(p) or P.owns(p, wid) then return end
		local wpid = Shop.productFor(wo)
		if wpid then prompt(p, wo.id, wpid) end
		return
	end
	-- a coin pack
	if string.match(offerId, "^coins:[%w_]+$") then
		local bo = Shop.coinPack(offerId)
		local bpid = if bo then Shop.productFor(bo) else nil
		if bo and bpid then prompt(p, bo.id, bpid) end
		return
	end
	-- one of the owner's deals: its product is the rarity's and the discount's ("deal:legendary:40")
	local dskin = string.match(offerId, "^deal:([%w_]+)$")
	if dskin then
		local D = deals()
		local d = D and type(D.offerFor) == "function" and D.offerFor(p, dskin)
		if not d then return end
		local dpid = Shop.PRODUCTS["deal:" .. d.rarity .. ":" .. d.pct]
		if type(dpid) ~= "number" or dpid <= 0 then return end
		prompt(p, offerId, dpid)
		return
	end
	local o = Shop.offer(offerId)
	if not o or not Shop.onSale(o.id) then return end
	-- a paid random item (a container) never goes to a player Roblox's policy keeps them from (the shop's screen hides
	-- the button; this is the server's own say, the anti-cheat audit, 17 Nov 2026)
	if o.type == "container" then
		local L = loot()
		if not L or type(L.restricted) ~= "function" or L.restricted(p) then return end
	end
	-- (a skin set you already have some of: the "complete the set" product for the count you're missing)
	local missing: number? = nil
	if o.set then
		local L = loot()
		if not L or type(L.owns) ~= "function" then return end
		local n = 0
		for _, it in Shop.contents(o) do if not L.owns(p, it.kind, it.id) then n += 1 end end
		if n == 0 then return end
		missing = n
	end
	local pid = Shop.productFor(o, missing)
	if not pid then return end
	prompt(p, o.id, pid)
end)
Players.PlayerRemoving:Connect(function(p) lastAsk[p] = nil end)

-- grant one receipt (true = granted and written)
local function grant(p: Player, info: any): boolean
	local key = Shop.byProduct[info.ProductId]
	if not key then
		warn("[jankfire] a receipt for a product the shop doesn't know: " .. tostring(info.ProductId))
		return false
	end
	local pid = tostring(info.PurchaseId)
	-- a Robux weapon
	local wid = string.match(key, "^weapon:([%w_]+)$")
	if wid then
		local P = purchases()
		if not P then return false end
		local ok, res = pcall(P.giveWeapon, p, wid, "robux", pid)
		if not ok then warn("[jankfire] Purchases.giveWeapon failed: " .. tostring(res)) end
		return ok and res == true
	end
	-- coins (Brass in the code)
	if string.match(key, "^coins:[%w_]+$") then
		local bo = Shop.coinPack(key)
		local Q = quests()
		if not bo or not Q or type(Q.buyBrass) ~= "function" then return false end
		local ok, res = pcall(Q.buyBrass, p, bo.amount, pid)
		if not ok then warn("[jankfire] Quests.buyBrass failed: " .. tostring(res)) end
		return ok and res == true
	end
	local offerId = key
	if not Shop.byId[key] then
		-- a shared product ("wrap:epic", "deal:legendary:40"): the offer this player asked for
		local a = asked[info.PlayerId .. ":" .. info.ProductId]
		if not a or a.product ~= info.ProductId or os.clock() - a.t > ASK_TTL then
			warn("[jankfire] a receipt with no matching ask: " .. pid)
			return false
		end
		offerId = a.offer
	end
	local ok, granted
	local dskin = string.match(offerId, "^deal:([%w_]+)$")
	if dskin then
		-- (one of the owner's deals: the skin, and the deal marked had)
		local D = deals()
		if not D or type(D.grant) ~= "function" then return false end
		ok, granted = pcall(D.grant, p, dskin, pid)
	else
		local L = loot()
		if not L or type(L.grant) ~= "function" then return false end
		-- (a container for a player Roblox's policy keeps from paid random items is never granted: the receipt waits and
		-- Roblox returns the Robux. the shop never prompts them; this is for a purchase made some other way. 18 Nov)
		local co = Shop.byId[offerId]
		if co and co.type == "container" and type(L.restricted) == "function" and L.restricted(p) then
			warn("[jankfire] a container receipt for a restricted player, not granted: " .. pid)
			return false
		end
		ok, granted = pcall(L.grant, p, offerId, pid)
	end
	if not ok then warn("[jankfire] the grant failed: " .. tostring(granted)) end
	if ok and granted == true then
		local ak = info.PlayerId .. ":" .. info.ProductId
		if asked[ak] and asked[ak].offer == offerId then asked[ak] = nil end
		return true
	end
	return false
end

local function process(info: any): Enum.ProductPurchaseDecision
	local p = Players:GetPlayerByUserId(info.PlayerId)
	if not p then return Enum.ProductPurchaseDecision.NotProcessedYet end -- (they left: granted when they're back)
	local P = purchases()
	if not P or not P.ready(p) then return Enum.ProductPurchaseDecision.NotProcessedYet end
	if P.seen(p, info.PurchaseId) then return Enum.ProductPurchaseDecision.PurchaseGranted end
	if not grant(p, info) then return Enum.ProductPurchaseDecision.NotProcessedYet end
	-- (the record: a failed write is all right, the grant above is idempotent by the purchase id)
	pcall(P.mark, p, info.PurchaseId, Shop.byProduct[info.ProductId])
	return Enum.ProductPurchaseDecision.PurchaseGranted
end

-- (set once Robux is on: at start in a live game, or when a Studio play test turns MoneyTest on)
local armed = false
local function arm()
	if armed or not Shop.ROBUX then return end
	armed = true
	MarketplaceService.ProcessReceipt = process
end
arm()
if RunService:IsStudio() then
	ReplicatedStorage:GetAttributeChangedSignal("MoneyTest"):Connect(function() task.defer(arm) end)

	-- (Studio tests: ServerStorage.JankMoneyTest, a BindableFunction for the Play server's command bar)
	--   ("receipt", userId, productId, purchaseId) -> the decision a receipt gets (simulated: nothing is charged)
	--   ("ask", userId, offerId, productId) -> remembers an ask without a prompt (a shared product's simulated receipt)
	--   ("vipgift", userId, on) -> Vip.gift(player, on): the owner's VIP gift, given or taken back
	local ServerStorage = game:GetService("ServerStorage")
	local old = ServerStorage:FindFirstChild("JankMoneyTest")
	if old then old:Destroy() end
	local fn = Instance.new("BindableFunction")
	fn.Name = "JankMoneyTest"
	fn.OnInvoke = function(op: string, uid: number, a: any, b: any): any
		if op == "receipt" then
			local d = process({ PlayerId = uid, ProductId = a, PurchaseId = tostring(b), CurrencySpent = 0,
				CurrencyType = Enum.CurrencyType.Robux, PlaceIdWherePurchased = game.PlaceId })
			return d.Name
		elseif op == "ask" then
			if type(a) ~= "string" or type(b) ~= "number" then return false end
			asked[uid .. ":" .. b] = { offer = a, product = b, t = os.clock() }
			return true
		elseif op == "vipgift" then -- ("vipgift", userId, on): Vip.gift, the dev menu's call
			local p = Players:GetPlayerByUserId(uid)
			local V = module("Vip")
			if not p or not V or type(V.gift) ~= "function" then return "no player or no Vip.gift" end
			local ok, why = V.gift(p, a ~= false)
			return { ok = ok, why = why, vip = p:GetAttribute("VIP") }
		end
		return nil
	end
	fn.Parent = ServerStorage
end
