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

local ASK_TTL = 600 -- s: how long a "this single, please" waits for its receipt
local asked: { [number]: { offer: string, product: number, t: number } } = {}
local lastAsk: { [Player]: number } = {}

local function loot(): any
	local folder = script.Parent
	local m = folder and folder:FindFirstChild("Loot")
	if not (m and m:IsA("ModuleScript")) then return nil end
	local ok, L = pcall(require, m)
	return if ok and type(L) == "table" then L else nil
end

Remote.OnServerEvent:Connect(function(p: Player, offerId: unknown)
	if not Shop.ROBUX or Shop.free() then return end
	local now = os.clock()
	if (lastAsk[p] or 0) > now - 1 then return end
	lastAsk[p] = now
	local o = Shop.offer(offerId)
	if not o or not Shop.onSale(o.id) then return end
	local pid = Shop.productFor(o)
	if not pid then return end
	asked[p.UserId] = { offer = o.id, product = pid, t = now }
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
			local a = asked[info.PlayerId]
			if not a or a.product ~= info.ProductId or os.clock() - a.t > ASK_TTL then
				warn("[jankfire] a single's receipt with no matching ask: " .. info.PurchaseId)
				return Enum.ProductPurchaseDecision.NotProcessedYet
			end
			offerId = a.offer
		end
		local L = loot()
		if not L or type(L.grant) ~= "function" then return Enum.ProductPurchaseDecision.NotProcessedYet end
		local ok, granted = pcall(L.grant, p, offerId, info.PurchaseId)
		if ok and granted == true then
			if asked[info.PlayerId] and asked[info.PlayerId].offer == offerId then asked[info.PlayerId] = nil end
			return Enum.ProductPurchaseDecision.PurchaseGranted
		end
		if not ok then warn("[jankfire] Loot.grant failed: " .. tostring(granted)) end
		return Enum.ProductPurchaseDecision.NotProcessedYet
	end
end
