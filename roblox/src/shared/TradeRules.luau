--!strict
-- TRADING's rules (roblox/docs/TRADING.md; 18 Nov 2026, the owner: "we need trading"). what may change hands and the
-- numbers, shared by the server (server/Trading.luau checks every item again at the moment of the swap) and the clients
-- (client/TradeUI.luau marks what can't go in the picker). behind PlayConfig.TRADING_ON.
--   tradeable: owned cosmetics of the container rarities (common, rare, epic, legendary) of these types: wraps, hats,
--   weapon skins, kill effects, emotes, card borders, banners (the card backgrounds) and titles; and UNOPENED containers
--   (Crates, Duffel Bags, Spray Cans).
--   never: coins (Brass), Crate Tickets, VIP and anything VIP-only, the VIP daily's exclusives, code rewards (a skin set
--   with code = true: Ducky Classic), found things (the lore and OG titles, CardStyles "secret"), the OWNER title,
--   weapon mastery camos, free and default things, grapples (lore gifts), anything on a coming-soon weapon, and a shop
--   bundle's wrap (owned on every gun at once: the server checks that one against the save, R.BUNDLE)
local Shared = script.Parent
local LootTable = require(Shared:WaitForChild("LootTable")) :: any
local Roster = require(Shared:WaitForChild("Roster")) :: any
local okM, MasteryX = pcall(function() return require(Shared:WaitForChild("Mastery", 5) :: ModuleScript) end)
local Mastery: any = if okM then MasteryX else nil
local okS, SkinSetsX = pcall(function() return require(Shared:WaitForChild("SkinSets", 5) :: ModuleScript) end)
local SkinSets: any = if okS then SkinSetsX else nil

local R = {}

R.TYPES = { "wrap", "hat", "skin", "kill", "emote", "border", "banner", "title" }
R.RARITIES = { common = true, rare = true, epic = true, legendary = true, exotic = true } :: { [string]: boolean }
R.KINDS = table.clone(LootTable.KINDS or { "crate", "bag", "spray" }) -- (unopened containers: every kind, the spray sets too)

R.LEVEL = 5 -- player level (Stats' Level) to trade
R.AGE = 7 -- days: a Roblox account at least this old (fewer alt scams)
R.MAX_ITEMS = 16 -- items a side may put in one trade
R.MAX_STOCK = 99 -- of each container a side may put in
R.REQUEST_GAP = 5 -- s between trade requests from one player
R.REQUEST_LIFE = 20 -- s a request waits for an answer
R.CONFIRM_WAIT = 3 -- s from both locking to CONFIRM working (the final look)
R.IDLE = 300 -- s a trade may sit with nothing happening before it closes
R.HISTORY = 50 -- trades kept in each player's save
R.BUNDLE = "BUNDLE" -- (the reason for a shop bundle's every-gun wrap)

-- why this item can't be traded (a short label), or nil when it can. t = its type, key = its owned key ("id@gun" for a
-- wrap or a hat, the bare id for the rest). nothing here reads a save: the server adds the bundle check (R.BUNDLE)
function R.why(t: any, key: any): string?
	if type(t) ~= "string" or type(key) ~= "string" then return "NOT TRADEABLE" end
	if not table.find(R.TYPES, t) then return "NOT TRADEABLE" end
	local i = LootTable.pairInfo(t, key)
	if not i then return "NOT TRADEABLE" end
	local id = i.id :: string
	if i.rarity == "free" then return "FREE" end
	if LootTable.vipOnly(t, id) then return "VIP" end
	if LootTable.exclusive(t, id) then return "VIP DAILY" end
	if Mastery and ((t == "wrap" and Mastery.isCamo(id)) or Mastery.masteryOnly(t, id)) then return "MASTERY" end
	if i.rarity == "owner" then return "OWNER" end
	if i.rarity == "secret" then return "FOUND" end
	if t == "skin" and SkinSets and type(SkinSets.SKINS) == "table" then
		local row = SkinSets.SKINS[id]
		local set = if type(row) == "table" then row[4] else nil
		local s = if type(set) == "string" and type(SkinSets.SETS) == "table" then SkinSets.SETS[set] else nil
		if type(s) == "table" and s.code == true then return "CODE" end
		if type(s) == "table" and s.vip == true then return "VIP" end
	end
	-- the gun it's on (a wrap's or a hat's pair, a skin's own) must be live
	local w = i.weapon
	if type(w) == "string" and w ~= "" then
		local e = Roster.byId[w]
		if e and e.live ~= true then return "COMING SOON" end
	end
	if not R.RARITIES[i.rarity] then return "NOT TRADEABLE" end
	return nil
end

-- the item's row for a screen: { t, k, name, rarity, gun? } (gun = its weapon's name, for a pair or a skin)
function R.card(t: string, key: string): any?
	local i = LootTable.pairInfo(t, key)
	if not i then return nil end
	local gun: string? = nil
	if type(i.weapon) == "string" and i.weapon ~= "" then
		local e = Roster.byId[i.weapon]
		gun = if e then e.name else i.weapon
	end
	return { t = t, k = key, name = i.name, rarity = i.rarity, gun = gun, type = LootTable.TYPE_NAMES[t] or t }
end

return R
