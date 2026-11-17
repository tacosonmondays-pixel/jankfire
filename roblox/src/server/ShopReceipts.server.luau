-- real-money purchases for the shop. OFF: while Shared.Shop.ROBUX is false this script prompts nothing and does not
-- even set MarketplaceService.ProcessReceipt (only one script in a game may set it), so nothing can be charged.
-- when it's on:
--   the client asks (JankfireRemotes.ShopBuy, an offer id); this checks the offer is on sale and has a developer
--   product (Shop.PRODUCTS), remembers which offer you asked for, and shows Roblox's purchase prompt;
--   Roblox calls ProcessReceipt; this works out the offer (the product's own offer, or for a shared single product
--   the one you asked for) and has the loot server grant it: Loot.grant(player, offerId, purchaseId). the loot server
--   saves the grant with the purchase id (so a receipt Roblox sends twice is granted once) BEFORE it answers true,
--   and only then does this tell Roblox PurchaseGranted. anything else: NotProcessedYet, and Roblox asks again later.
-- see roblox/docs/SHOP.md
local Players = game:GetService("Players")
local MarketplaceService = game:GetService("MarketplaceService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shop = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Shop"))
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("ShopBuy") :: RemoteEvent

-- VIP (a game pass, not a developer product: no receipt here) is Vip.luau's, its daily reward from Trisangle
-- VipDaily.luau's, and the owner's deals Deals.luau's; requiring them starts them
for _, name in { "Vip", "VipDaily", "Deals" } do
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

local function loot(): any
	local folder = script.Parent
	local m = folder and folder:FindFirstChild("Loot")
	if not (m and m:IsA("ModuleScript")) then return nil end
	local ok, L = pcall(require, m)
	return if ok and type(L) == "table" then L else nil
end
-- the owner's deals (Deals.luau): "deal:<skin>", only the player's own of today
local function deals(): any
	local m = script.Parent:FindFirstChild("Deals")
	if not (m and m:IsA("ModuleScript")) then return nil end
	local ok, D = pcall(require, m)
	return if ok and type(D) == "table" then D else nil
end

Remote.OnServerEvent:Connect(function(p: Player, offerId: unknown)
	if not Shop.ROBUX or Shop.free() then return end
	local now = os.clock()
	if (lastAsk[p] or 0) > now - 1 then return end
	lastAsk[p] = now
	-- one of the owner's deals: its product is the rarity's and the discount's ("deal:legendary:40")
	local dskin = if type(offerId) == "string" then string.match(offerId, "^deal:([%w_]+)$") else nil
	if dskin then
		local D = deals()
		local d = D and type(D.offerFor) == "function" and D.offerFor(p, dskin)
		if not d then return end
		local dpid = Shop.PRODUCTS["deal:" .. d.rarity .. ":" .. d.pct]
		if type(dpid) ~= "number" or dpid <= 0 then return end
		asked[p.UserId .. ":" .. dpid] = { offer = offerId :: string, product = dpid, t = now }
		MarketplaceService:PromptProductPurchase(p, dpid)
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
	asked[p.UserId .. ":" .. pid] = { offer = o.id, product = pid, t = now } -- (per product: a second ask can't strand the first's receipt)
	MarketplaceService:PromptProductPurchase(p, pid)
end)
Players.PlayerRemoving:Connect(function(p) lastAsk[p] = nil end)

if Shop.ROBUX then
	MarketplaceService.ProcessReceipt = function(info: any): Enum.ProductPurchaseDecision
		local p = Players:GetPlayerByUserId(info.PlayerId)
		if not p then return Enum.ProductPurchaseDecision.NotProcessedYet end -- (they left: granted when they're back)
		local key = Shop.byProduct[info.ProductId]
		if not key then
			warn("[jankfire] a receipt for a product the shop doesn't know: " .. tostring(info.ProductId))
			return Enum.ProductPurchaseDecision.NotProcessedYet
		end
		local offerId = key
		if not Shop.byId[key] then
			-- a shared single product ("wrap:epic"): the single this player asked for
			local a = asked[info.PlayerId .. ":" .. info.ProductId]
			if not a or a.product ~= info.ProductId or os.clock() - a.t > ASK_TTL then
				warn("[jankfire] a single's receipt with no matching ask: " .. info.PurchaseId)
				return Enum.ProductPurchaseDecision.NotProcessedYet
			end
			offerId = a.offer
		end
		local L = loot()
		if not L or type(L.grant) ~= "function" then return Enum.ProductPurchaseDecision.NotProcessedYet end
		local ok, granted
		local dskin = string.match(offerId, "^deal:([%w_]+)$")
		if dskin then
			-- (one of the owner's deals: the skin, and the deal marked had)
			local D = deals()
			if not D or type(D.grant) ~= "function" then return Enum.ProductPurchaseDecision.NotProcessedYet end
			ok, granted = pcall(D.grant, p, dskin, info.PurchaseId)
		else
			ok, granted = pcall(L.grant, p, offerId, info.PurchaseId)
		end
		if ok and granted == true then
			local ak = info.PlayerId .. ":" .. info.ProductId
			if asked[ak] and asked[ak].offer == offerId then asked[ak] = nil end
			return Enum.ProductPurchaseDecision.PurchaseGranted
		end
		if not ok then warn("[jankfire] Loot.grant failed: " .. tostring(granted)) end
		return Enum.ProductPurchaseDecision.NotProcessedYet
	end
end
