--!strict
-- the shop's catalog: everything the SHOP screen sells (ShopUI.luau), what the hub's bundle holograms show, and what
-- the loot server checks before it grants (JankfireRemotes.Loot "buy"). three kinds of offer, each with an id:
--   containers  "crate" / "bag" / "spray": a random item; the odds and pools are the loot module's (Shop.odds reads them)
--   bundles     "bundle_<name>": a fixed themed set of wraps and hats, each for a named weapon (only things that exist
--               on roblox today)
--   singles     "wrap:<id>@<weapon>" / "hat:<id>@<weapon>": one item for one weapon, sold only while it is in today's
--               featured rotation; "skin:<id>" one weapon skin (a skin is already one gun's); "border:<id>" etc. one
--               player card look; "kill:<id>" / "emote:<id>" one kill effect or emote (the flair session's Flair.luau)
--   skin sets   "<set id>" ("set_seraph"): every skin of one of SkinSets' sets, a bundle with a banner (the guns
--               session's SkinSets.luau); on sale once all its skins are in the place
--   VIP         "vip": the game pass (Vip.luau on the server decides who has it); its pack is every VIP-only thing
--               (Shop.vipItems), handed over by the loot server, never sold on its own
-- wraps and hats are owned per weapon: an item is { kind, id, weapon } (Shop.key: "sakura@smg")
-- every offer has a Robux price (`robux`) and a slot for its developer product (`productId`), but nothing costs
-- anything while the loot switch is on (Config.LOOT_FREE; Shop.free()) and no purchase prompt is ever shown while
-- Shop.ROBUX is false (ShopReceipts.server.luau routes receipts once it's on). docs: roblox/docs/SHOP.md
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Roster = require(script.Parent:WaitForChild("Roster"))
local GunHatData = require(script.Parent:WaitForChild("GunHatData")) :: any
local Config = require(script.Parent:WaitForChild("Config")) :: any
-- the loot module's tables (the pools, the odds, the rarity colours the opening uses), if it's in the place
local LootTable: any = nil
do
	local m = script.Parent:FindFirstChild("LootTable")
	if m and m:IsA("ModuleScript") then
		local ok, L = pcall(require, m)
		if ok and type(L) == "table" then LootTable = L end
	end
end

local Shop = {}

-- the player card's looks (the player-cards session's CardStyles: borders, backgrounds, titles), if it's in the place.
-- they are gun-less: an item { kind = "border"|"banner"|"title", id }, kept under the bare id
do
	local m = script.Parent:FindFirstChild("CardStyles")
	if m and m:IsA("ModuleScript") then
		local ok, C = pcall(require, m)
		if ok and type(C) == "table" and type((C :: any).info) == "function" then Shop.CardStyles = C end
	end
end
Shop.CARD_KINDS = { border = true, banner = true, title = true }
function Shop.isCard(kind: string?): boolean return kind ~= nil and Shop.CARD_KINDS[kind] == true end
-- the weapon skin sets (the guns session's SkinSets: which skins make a set, its banner colours), if it's in the place
do
	local m = script.Parent:FindFirstChild("SkinSets")
	if m and m:IsA("ModuleScript") then
		local ok, K = pcall(require, m)
		if ok and type(K) == "table" and type((K :: any).SETS) == "table" then Shop.SkinSets = K end
	end
end
-- kill effects and emotes (the flair session's Flair), if it's in the place. gun-less like the card looks: an item
-- { kind = "kill"|"emote", id }, kept under the bare id; one kill effect for every gun, emotes on the wheel
do
	local m = script.Parent:FindFirstChild("Flair")
	if m and m:IsA("ModuleScript") then
		local ok, F = pcall(require, m)
		if ok and type(F) == "table" and type((F :: any).info) == "function" then Shop.Flair = F end
	end
end
Shop.FLAIR_KINDS = { kill = true, emote = true }
function Shop.isFlair(kind: string?): boolean return kind ~= nil and Shop.FLAIR_KINDS[kind] == true end
-- a kill effect or emote that can be sold: Flair.forSale's (not free, not VIP, an emote only once its clip is uploaded)
function Shop.flairForSale(kind: string, id: string): boolean
	local F = Shop.Flair :: any
	if not (F and Shop.isFlair(kind) and type(F.forSale) == "function") then return false end
	local ok, list = pcall(F.forSale, kind)
	if not ok or type(list) ~= "table" then return false end
	for _, i in list do if i.id == id then return true end end
	return false
end
-- the VIP daily reward's table (VipDailyData): its three daily-only things (a wrap, a hat, a weapon skin) are never
-- sold, never in the rotation, a bundle or the VIP pack; the server pays them through Loot.grant with a hidden offer
-- "vipdaily:<kind>:<id>" (Shop.offer; type "pass", so the loot server's "buy" refuses it)
do
	local m = script.Parent:FindFirstChild("VipDailyData")
	if m and m:IsA("ModuleScript") then
		local ok, D = pcall(require, m)
		if ok and type(D) == "table" and type((D :: any).isExclusive) == "function" then Shop.VipDaily = D end
	end
end
function Shop.dailyOnly(kind: string, id: string): boolean
	local D = Shop.VipDaily :: any
	return D ~= nil and D.isExclusive(kind, id) == true
end
-- a found thing (CardStyles rarity "secret": the hub egg's OG title): never sold, only "egg:<kind>:<id>" through the
-- server's Loot.grant (Shop.offer)
function Shop.secret(kind: string, id: string): boolean
	local C = Shop.CardStyles :: any
	return Shop.isCard(kind) and C ~= nil and type(C.isSecret) == "function" and C.isSecret(kind, id) == true
end
-- kept under the bare id, not "<id>@<weapon>": card looks, kill effects and emotes (no gun) and weapon skins (already
-- one gun's)
function Shop.gunless(kind: string?): boolean return kind == "skin" or Shop.isCard(kind) or Shop.isFlair(kind) end

-- ---------------------------------------------------------------- switches
-- real-money purchases: Config.LOOT_ROBUX (the loot module's switch, off). false = no prompt is ever shown and
-- ShopReceipts doesn't even take receipts (nothing can be charged). THE switch for real money: docs/MONEY.md
Shop.ROBUX = Config.LOOT_ROBUX == true
-- (Studio only: a play test of the paid shop. the Play server sets ReplicatedStorage's attribute MoneyTest = true (never
-- saved: Play's copy goes when it stops): Robux on and free off, here and on every client, and the Robux weapons locked
-- (Unlocks.robuxFree). Studio test purchases charge nothing. a live game never reads it. 18 Nov)
Shop.testMoney = false
if RunService:IsStudio() then
	local function sync()
		Shop.testMoney = ReplicatedStorage:GetAttribute("MoneyTest") == true
		Shop.ROBUX = Shop.testMoney or Config.LOOT_ROBUX == true
	end
	sync()
	ReplicatedStorage:GetAttributeChangedSignal("MoneyTest"):Connect(sync)
end
-- the featured rotation turns over every day at 00:00 UTC
Shop.ROTATE = 86400
-- how many single items the daily rotation shows
Shop.DAILY = 6

-- free while we test: Config.LOOT_FREE when the loot module has added it, else free
function Shop.free(): boolean
	if Shop.testMoney then return false end
	if Config.LOOT_FREE ~= nil then return Config.LOOT_FREE == true end
	return true
end

-- ---------------------------------------------------------------- rarities (the opening's muted colours, LootTable.RARITY;
-- the loadout's Roster.RARITY if the loot module isn't there)
Shop.RARITY = if LootTable and LootTable.RARITY then LootTable.RARITY else Roster.RARITY
Shop.RARITY_ORDER = { "free", "common", "rare", "epic", "legendary", "exotic" }
local RANK = { free = 0, common = 1, rare = 2, epic = 3, legendary = 4, exotic = 5, vip = 6 }
function Shop.rank(r: string): number return RANK[r] or 0 end
-- the VIP pack's own rarity colour (the player cards' VIP gold): a VIP thing reads "VIP", not a rarity
Shop.VIP_COLOR = Color3.fromRGB(255, 208, 72)

-- ---------------------------------------------------------------- every price, in one table (18 Nov, the owner: "make
-- them for the shop bundles as well, bundles, coins, buying weapons with coins"). Robux numbers are what the developer
-- products and the VIP pass were made at: change one here AND on its product (Creator Hub > Monetization), or the
-- prompt charges Roblox's price while the shop shows this one (with Robux on, the shop reads the products' own prices:
-- ShopUI.livePrices). Coins = the one soft currency (called Brass in the code: the quests' wallet, QuestData; earned
-- from quests and the weekly track, bought in coin packs); what Coins and tickets redeem a container for is
-- QuestData.PRICES (the quests session's). the list of products and ids: docs/MONEY.md
Shop.MONEY = {
	vip = 399, -- the VIP game pass (Shop.VIP_PASS)
	containers = { crate = 120, bag = 90, spray = 60 },
	-- one item, by kind and rarity (singles share one product per kind and rarity: "wrap:epic")
	singles = {
		wrap = { free = 0, common = 75, rare = 150, epic = 300, legendary = 600 },
		hat = { free = 0, common = 100, rare = 200, epic = 400, legendary = 750 },
		skin = { free = 0, common = 150, rare = 300, epic = 600, legendary = 1200 },
		border = { free = 0, common = 50, rare = 100, epic = 200, legendary = 400 },
		banner = { free = 0, common = 50, rare = 100, epic = 200, legendary = 400 },
		title = { free = 0, common = 40, rare = 80, epic = 160, legendary = 320 },
		kill = { free = 0, common = 100, rare = 200, epic = 400, legendary = 800 },
		emote = { free = 0, common = 100, rare = 200, epic = 400, legendary = 800 },
	},
	-- a themed bundle costs this share of its items' singles, rounded to ..9 (a skin set: its whole worth, no discount;
	-- the owner's deals: Shop.DEAL_OFF below)
	bundleShare = 0.6,
	-- the Robux-exclusive weapons (Unlocks.ROBUX): Robux, or Coins, each its own price. kept for good once bought
	weapons = {
		minigun = { robux = 249, coins = 5000 },
		laser = { robux = 199, coins = 4000 }, -- (Big Laser Pointer)
		chicken = { robux = 199, coins = 4000 }, -- (Chicken Rocket)
		akimbo = { robux = 249, coins = 5000 }, -- (Lefty & Righty)
	},
	-- coin packs (the owner's prices, 18 Nov: 99 / 499 / 1999 / 4500 Robux). 12 coins a Robux, and the bigger packs a
	-- bonus on top (8%, 17%, 30%), never so much that coins bought with Robux redeem a container or buy a weapon for less
	-- than its own Robux price (the best rate, about 15.6 a Robux: a Spray Can's 1,000 coins is 64 Robux against its 60).
	-- image = the pack's picture (guns-remodel's renders, uploaded as images)
	coins = {
		{ id = "coins_1200", coins = 1200, bonus = 0, robux = 99, image = "rbxassetid://76861915103827" },
		{ id = "coins_6500", coins = 6000, bonus = 500, robux = 499, image = "rbxassetid://88259913823049" },
		{ id = "coins_28000", coins = 24000, bonus = 4000, robux = 1999, image = "rbxassetid://93667428578542",
			extras = { pick = "legendary", crates = 1 } }, -- (the extras: Shop.packExtrasOn, below)
		{ id = "coins_70000", coins = 54000, bonus = 16000, robux = 4500, image = "rbxassetid://125116964696727",
			extras = { pick = "finisher", gold = true, crates = 3 } },
	},
}
-- what a single costs, by kind and rarity (Robux; unused while free)
Shop.PRICE = Shop.MONEY.singles

-- ---------------------------------------------------------------- the coins-only shop (18 Nov, the owner: "wraps and skins
-- that aren't a part of bundles should be coin purchased; the only thing you buy with robux are weapons, gadgets and
-- bundles, like in rivals"). with the switch on, single items, the owner's deals and containers are bought with coins
-- only (Purchases.luau takes them on the server), never prompted for Robux (their developer products stay, and a late
-- receipt is still granted); Robux buys the weapons, bundles and skin sets, coin packs and VIP. OFF until the owner
-- approves the prices below. (Studio: a play test turns it on with ReplicatedStorage's attribute CoinsOnlyTest)
Shop.SINGLES_COINS_ONLY = true -- (ON since 19 Nov: the owner approved the coin prices)
function Shop.coinsOnly(): boolean
	if Shop.SINGLES_COINS_ONLY then return true end
	return RunService:IsStudio() and ReplicatedStorage:GetAttribute("CoinsOnlyTest") == true
end
-- what Robux may buy (19 Nov 2026, the owner: "make sure only skins cost robux!" and "weapons shouldnt have a tab
-- then!"): weapon skins, one at a time or as a skin set (coins buy them too), containers (how skins are sold: coins too,
-- with the odds and the restriction checks as ever), coin packs and VIP. never a weapon, a weapon bundle, a gadget, a
-- wrap, hat, card look, kill effect or emote, or a bundle of those: coins only. their developer products stay for the
-- receipts of what was bought before (the weapon ones are off sale)
function Shop.robuxFor(o: any): boolean
	if type(o) ~= "table" then return false end
	if not Shop.coinsOnly() then return true end
	if o.type == "single" then return o.kind == "skin" end
	if o.type == "container" or o.type == "coins" or o.type == "pass" or o.type == "vipgift" then return true end
	if o.type == "bundle" then return o.set ~= nil end
	return false
end
-- coin prices, paced to what a player earns (about 1,000-1,500 coins a week from quests and the weekly track): a common
-- in a day or two, a legendary in a few weeks. containers about what their items are worth on average (never a
-- duplicate). the owner's deals: the skin's coin price less the deal's percent
Shop.MONEY.coinPrices = {
	singles = {
		skin = { common = 300, rare = 800, epic = 2000, legendary = 5000 },
		wrap = { common = 200, rare = 500, epic = 1200, legendary = 3000 },
		hat = { common = 250, rare = 600, epic = 1500, legendary = 3500 },
		kill = { common = 250, rare = 600, epic = 1500, legendary = 3500 },
		emote = { common = 250, rare = 600, epic = 1500, legendary = 3500 },
		border = { common = 150, rare = 400, epic = 900, legendary = 2000 },
		banner = { common = 150, rare = 400, epic = 900, legendary = 2000 },
		title = { common = 100, rare = 300, epic = 700, legendary = 1500 },
	},
	containers = { crate = 900, bag = 600, spray = 500 },
}
-- (the spray sets, 20 Nov 2026: each can at the first Spray Can's prices, Robux and coins. their tickets and coins to
-- redeem are QuestData.PRICES'; their products are in Shop.PRODUCTS)
do
	local rc, cc = Shop.MONEY.containers :: any, Shop.MONEY.coinPrices.containers :: any
	for _, id in (if LootTable and type(LootTable.SPRAY_SETS) == "table" then LootTable.SPRAY_SETS else {}) :: { string } do
		rc[id] = rc.spray; cc[id] = cc.spray
	end
end
-- (Exotic, 20 Nov: the moving wraps. priced as a Legendary for now, so no price moved: a single, a bundle's worth)
for _, t in Shop.MONEY.singles :: any do t.exotic = t.legendary end
for _, t in Shop.MONEY.coinPrices.singles :: any do t.exotic = t.legendary end
-- an offer's coin price in the coins-only shop (n containers), or nil: not sold for coins
function Shop.coinPrice(o: any, n: number?, missing: number?): number?
	if type(o) ~= "table" then return nil end
	local cp = Shop.MONEY.coinPrices :: any
	if o.type == "single" then
		local t = cp.singles[o.kind]
		return if t then t[o.rarity] else nil
	elseif o.type == "container" then
		if o.legacy then return nil end -- (the first Spray Can: not sold any more)
		local c = cp.containers[o.id]
		return if c then c * (n or 1) else nil
	elseif o.type == "bundle" and not o.weapons and type(o.items) == "table" then
		-- (19 Nov: a bundle of wraps, hats or card looks, coins only: 40% under its pieces' coin prices, to the nearest 50.
		-- a skin set: its skins' coin prices, no discount; missing = how many you still lack, pro rata)
		local sum = 0
		for _, it in o.items do
			local t = cp.singles[it.kind]
			local _, r = Shop.itemInfo(it.kind, it.id)
			sum += (t and t[r]) or 0
		end
		if sum <= 0 then return nil end
		if o.set then
			local total = #o.items
			local m = missing or total
			if m >= total then return sum end
			return math.max(10, math.ceil(sum * m / total / 10) * 10)
		end
		return math.max(50, math.floor(sum * Shop.MONEY.bundleShare / 50 + 0.5) * 50)
	end
	return nil
end
-- one of the owner's deals in coins: the skin's coin price less the deal's percent, to the nearest 10
function Shop.coinDealPrice(skin: string, pct: number): number
	local _, r = Shop.itemInfo("skin", skin)
	local full = (Shop.MONEY.coinPrices :: any).singles.skin[r] or 0
	return math.max(10, math.floor(full * (100 - pct) / 100 / 10 + 0.5) * 10)
end
Shop.KIND_NAMES = { wrap = "Wrap", hat = "Hat", skin = "Skin", border = "Border", banner = "Background", title = "Title",
	kill = "Kill Effect", emote = "Emote" }

-- wraps that never go in a bundle or the rotation: their picture versions broke Roblox's image rules and they are
-- plain colour wraps now (roblox-upload-content-rules), or they are the free ones everyone has
Shop.HELD_BACK = { qr = true, barcode = true, meat = true, organ = true, corp = true, memo = true, jersey = true, default = true }
-- the big coin packs' own gold wrap (Bullion, Roster): only the 4,500 pack gives it, never the rotation, a bundle or a
-- container (LootTable.exclusive). not Mastery Gold, which stays earned by weapon level
Shop.PACK_GOLD = "packgold"

-- wraps and hats are owned PER WEAPON (the owner, 16 Nov: "spray cans should give you a wrap for only one gun at a
-- time"): an item is (kind, id, weapon), written "<id>@<weapon>" where one string is needed (Shop.key)
export type Item = { kind: string, id: string, weapon: string?, every: boolean? } -- (every: a bundle's wrap, on every gun)
export type Hero = { weapon: string, wrap: string?, hat: string?, skin: string? }
export type Offer = {
	id: string, type: string, name: string, blurb: string, rarity: string,
	robux: number, productId: number?,
	items: { Item }?, hero: Hero?, -- a bundle
	set: string?, pair: string?, colour: Color3?, accent: Color3?, -- a skin set (a bundle with a banner)
	kind: string?, item: string?, weapon: string?, -- a single
	pool: string?, -- a container: what it holds, in words
}

-- ---------------------------------------------------------------- weapons (what a wrap or a hat can be for)
-- every weapon that's on roblox and takes paint and hats: the live primaries, secondaries and the melee, in the
-- loadout's order (the utility items don't)
Shop.WEAPONS = {} :: { string }
Shop.WEAPON_SET = {} :: { [string]: boolean }
for _, e in Roster.list do
	if e.live and e.slot ~= "utility" then table.insert(Shop.WEAPONS, e.id); Shop.WEAPON_SET[e.id] = true end
end
function Shop.weaponName(wid: string?): string
	local e = wid and Roster.byId[wid]
	return if e then e.name else "any weapon"
end
-- the string an owned item is kept under: "<id>@<weapon>" ("sakura@smg"); just "<id>" when it has no weapon
function Shop.key(kind: string, id: string, weapon: string?): string
	return if weapon then id .. "@" .. weapon else id
end
-- and back: "sakura@smg" -> "sakura", "smg"
function Shop.unkey(s: string): (string, string?)
	local id, w = string.match(s, "^([%w_]+)@([%w_]+)$")
	if id then return id, w end
	return s, nil
end

-- ---------------------------------------------------------------- weapon skins
-- a skin's row { name, rarity, weapon }: the loot module's LootTable.SKINS (what it rolls and grants), else a set
-- piece's row from SkinSets (until the loot module has merged them in: shown, but not sold)
local function skinRow(id: string): { any }?
	local row = LootTable and type(LootTable.SKINS) == "table" and LootTable.SKINS[id]
	if not row and Shop.SkinSets then row = (Shop.SkinSets :: any).SKINS and (Shop.SkinSets :: any).SKINS[id] end
	return if type(row) == "table" then row else nil
end
-- the weapon a skin dresses (nil: no such skin)
function Shop.skinWeapon(id: string): string?
	local row = skinRow(id)
	return if row then row[3] else nil
end
-- a skin can be sold: the loot module knows it (it can grant it) and its model is in the place
-- (ReplicatedStorage.JankfireSkins.<id>, the same check the loot module rolls by)
function Shop.skinLive(id: string): boolean
	local row = LootTable and type(LootTable.SKINS) == "table" and LootTable.SKINS[id]
	if type(row) ~= "table" then return false end
	-- (the guns session's concepts for the owner to choose from are in the place but never on sale)
	local K = Shop.SkinSets :: any
	if K and type(K.CONCEPTS) == "table" and table.find(K.CONCEPTS, id) then return false end
	-- (a skin with no model that only changes its weapon's effects: the Shadow Cross. live with its weapon. 18 Nov)
	if (row :: any).effectOnly == true then
		local e = Roster.byId[row[3]]
		return e ~= nil and e.live == true
	end
	local lib = ReplicatedStorage:FindFirstChild("JankfireSkins")
	local m = lib and lib:FindFirstChild(id)
	return m ~= nil and m:IsA("Model") and m:GetAttribute("Weapon") == row[3]
end
-- a skin set's piece (the owner, 18 Nov 2026: "weapons from sets can't be pulled from crates or be discounted"): sold
-- only in its set (Shop.sets), at the set's own price: never a single, never in the daily rotation, never one of the
-- owner's deals. the loot module's LootTable.setOnly (it keeps them out of every container), else the sets' lists here
function Shop.setOnly(kind: string, id: string): boolean
	if kind ~= "skin" then return false end
	if LootTable and type(LootTable.setOnly) == "function" then
		local ok, v = pcall(LootTable.setOnly, kind, id)
		if ok and v then return true end
	end
	local K = Shop.SkinSets :: any
	if K and type(K.SETS) == "table" then
		for _, s in K.SETS do if type(s) == "table" and table.find(s.members or {}, id) then return true end end
	end
	return false
end
-- every skin on sale as a single, sorted by id (VIP ones aren't: they come with VIP; set pieces aren't: their set is)
function Shop.liveSkins(): { string }
	local out = {}
	if LootTable and type(LootTable.SKINS) == "table" then
		-- (never a free one: the Classic set is everyone's already. 18 Nov)
		for id, row in LootTable.SKINS do if row[2] ~= "free" and Shop.skinLive(id) and not Shop.vipOnly("skin", id) and not Shop.dailyOnly("skin", id) and not Shop.setOnly("skin", id) then table.insert(out, id) end end
	end
	table.sort(out)
	return out
end

-- ---------------------------------------------------------------- VIP only
-- a VIP thing (the Ducky set's skins, the VIP wrap and hat, the VIP card looks) comes only with VIP (Vip.luau, the
-- game pass): never sold, never in a bundle, a set banner or the daily rotation, never in a container. what is VIP is
-- each thing's own data, read by the loot module (LootTable.vipOnly: a wrap's or hat's vip = true, a skin of a VIP
-- set, a card look of rarity "vip"), so this list never needs keeping
function Shop.vipOnly(kind: string, id: string): boolean
	if LootTable and type(LootTable.vipOnly) == "function" then
		local ok, v = pcall(LootTable.vipOnly, kind, id)
		if ok and v then return true end
	end
	if Shop.isCard(kind) and Shop.CardStyles then
		local C = Shop.CardStyles :: any
		if type(C.isVip) == "function" then
			local ok, v = pcall(C.isVip, kind, id)
			if ok and v then return true end
		end
	end
	if Shop.isFlair(kind) and Shop.Flair then
		local F = Shop.Flair :: any
		if type(F.isVip) == "function" then
			local ok, v = pcall(F.isVip, kind, id)
			if ok and v then return true end
		end
	end
	return false
end
-- a skin set that is VIP (the Ducky set): marked vip = true, or any of its skins is VIP
local function vipSet(sid: string, s: any): boolean
	if s.vip == true or sid == "set_ducky" then return true end
	for _, kid in s.members or {} do if Shop.vipOnly("skin", kid) then return true end end
	return false
end

-- ---------------------------------------------------------------- items
function Shop.itemInfo(kind: string, id: string): (string, string)
	if kind == "wrap" then
		local w = Roster.wrapById[id]
		if w then return w.name, w.rarity end
	elseif kind == "hat" then
		local h = GunHatData.HATS[id]
		if h then return h.name, h.rarity end
	elseif kind == "skin" then
		local row = skinRow(id)
		if row then return row[1], row[2] end
	elseif Shop.isCard(kind) and Shop.CardStyles then
		local c = (Shop.CardStyles :: any).info(kind, id)
		if c then return c.name, c.rarity end
	elseif Shop.isFlair(kind) and Shop.Flair then
		local f = (Shop.Flair :: any).info(kind, id)
		if f then return f.name, f.rarity end
	end
	return id, "common"
end
function Shop.exists(kind: string, id: string, weapon: string?): boolean
	if Shop.isCard(kind) then -- (a card look is never for a gun)
		return weapon == nil and Shop.CardStyles ~= nil and (Shop.CardStyles :: any).info(kind, id) ~= nil
	end
	if Shop.isFlair(kind) then -- (nor is a kill effect or an emote; "none" is no kill effect)
		return weapon == nil and id ~= "none" and Shop.Flair ~= nil and (Shop.Flair :: any).info(kind, id) ~= nil
	end
	if kind == "skin" then -- (a skin is its own gun's: a weapon given must be that one)
		return Shop.skinLive(id) and (weapon == nil or weapon == Shop.skinWeapon(id))
	end
	if weapon ~= nil and not Shop.WEAPON_SET[weapon] then return false end
	if kind == "wrap" then return Roster.wrapById[id] ~= nil end
	if kind == "hat" then
		return GunHatData.HATS[id] ~= nil and id ~= "none" and (weapon == nil or GunHatData.SPOTS[weapon] ~= nil)
	end
	return false
end
-- "Sakura Storm · SMG" ("Brackets" for a card look: it has no gun)
function Shop.itemLabel(it: Item): string
	local name = Shop.itemInfo(it.kind, it.id)
	if it.kind == "wrap" and it.every then return name .. " · Every gun" end -- (a bundle's wrap)
	local w = it.weapon or (if it.kind == "skin" then Shop.skinWeapon(it.id) else nil)
	if not w and (it.kind == "wrap" or it.kind == "hat") and Shop.vipOnly(it.kind, it.id) then return name .. " · Every gun" end
	return if w then name .. " · " .. Shop.weaponName(w) else name
end
-- the single offer id for an item: "skin:<id>" / "border:<id>" (bare), "wrap:<id>@<weapon>"
function Shop.singleId(it: Item): string
	if Shop.gunless(it.kind) or not it.weapon then return it.kind .. ":" .. it.id end
	return it.kind .. ":" .. it.id .. "@" .. it.weapon
end
function Shop.singlePrice(kind: string, id: string): number
	local _, r = Shop.itemInfo(kind, id)
	local t = (Shop.PRICE :: any)[kind]
	return if t then t[r] or 0 else 0
end

-- ---------------------------------------------------------------- containers
-- the names and prices are the shop's; what's inside and the odds are the loot module's (Jankfire.LootTable, the web
-- game's CONTAINERS): crates hold weapon skins, duffel bags hats, spray cans wraps
-- (the words on screen say what it is and nothing else: the owner's no-flavour-text rule)
Shop.containers = {
	{ id = "crate", type = "container", name = "Crate", rarity = "epic", robux = Shop.MONEY.containers.crate, productId = nil,
		blurb = "One weapon skin you don't have yet.", pool = "weapon skins" },
	{ id = "bag", type = "container", name = "Duffel Bag", rarity = "rare", robux = Shop.MONEY.containers.bag, productId = nil,
		blurb = "One hat you don't have yet, for one gun.", pool = "hats" },
} :: { Offer }
-- the spray sets (the owner, 20 Nov 2026: "can you divide the sprays into different sets?"): a Spray Can each, its wraps
-- the set's (LootTable.SPRAY_SETS); then the first Spray Can (every wrap): legacy, never sold, kept so the ones in saves
-- show in INVENTORY and open. boxSet / label: the set's name (CASE 1, DUFFEL BAG SET 1, COSMIC SET) and the name with
-- it on one line, the loot module's
for _, id in (if LootTable and type(LootTable.SPRAY_SETS) == "table" then LootTable.SPRAY_SETS else {}) :: { string } do
	local c = LootTable.CONTAINERS[id]
	table.insert(Shop.containers, { id = id, type = "container", name = c.name, rarity = "common", robux = Shop.MONEY.containers.spray,
		productId = nil, blurb = "One wrap from the " .. c.set .. " you don't have yet, for one gun.", pool = "wraps", spray = true } :: any)
end
table.insert(Shop.containers, { id = "spray", type = "container", name = "Spray Can", rarity = "common", robux = Shop.MONEY.containers.spray,
	productId = nil, blurb = "One wrap you don't have yet, for one gun.", pool = "wraps", legacy = true } :: any)
for _, o in Shop.containers do
	local c = LootTable and LootTable.CONTAINERS[o.id]
	local x = o :: any
	if c then x.boxSet = c.set; x.label = c.label end
end
-- (the Duffel Bag also holds the player card's looks and the kill effects and emotes, once the loot module keeps them)
do
	local kept: { [string]: boolean } = {}
	if LootTable and type(LootTable.ownTypes) == "function" then
		local ok, ts = pcall(LootTable.ownTypes)
		if ok and type(ts) == "table" then for _, t in ts do kept[t] = true end end
	end
	local more = {}
	if Shop.CardStyles and (Shop.CardStyles :: any).CONTAINER == "bag" then table.insert(more, "a player card look") end
	if Shop.Flair and (Shop.Flair :: any).CONTAINER == "bag" then
		if kept.kill then table.insert(more, "a kill effect") end
		if kept.emote then table.insert(more, "an emote") end
	end
	if #more == 1 then
		Shop.containers[2].blurb = "One hat for one gun, or " .. more[1] .. ", you don't have yet."
	elseif #more > 1 then
		Shop.containers[2].blurb = "One thing you don't have yet: a hat for one gun, " .. table.concat(more, ", ", 1, #more - 1) .. " or " .. more[#more] .. "."
	end
end

-- redeeming a container with the quests' currencies (the quests session's QuestData.PRICES, roblox/docs/QUESTS.md
-- section 6): { crate = { tix = 12 }, bag = { tix = 6, brass = 2500 }, ... }; tix = Crate Tickets, brass = Brass, a
-- missing one = that currency can't buy it (Brass never buys a Crate). the quests server takes the price and puts the
-- container in stock (JankfireRemotes.Quests "redeem"); the shop then opens it from stock
do
	local m = script.Parent:FindFirstChild("QuestData")
	if m and m:IsA("ModuleScript") then
		local ok, Q = pcall(require, m)
		if ok and type(Q) == "table" and type((Q :: any).PRICES) == "table" then Shop.QuestData = Q end
	end
end
function Shop.redeemPrice(cid: string): { tix: number?, brass: number? }?
	local Q = Shop.QuestData :: any
	local p = Q and Q.PRICES[cid]
	if type(p) ~= "table" then return nil end
	local tix = if type(p.tix) == "number" and p.tix > 0 then p.tix else nil
	local brass = if type(p.brass) == "number" and p.brass > 0 then p.brass else nil
	if not tix and not brass then return nil end
	return { tix = tix, brass = brass }
end

-- ---------------------------------------------------------------- bundles
-- themed sets that dress several guns. a bundle's wrap is for EVERY gun (the owner, 18 Nov 2026: "the wraps in the
-- bundle are given to all guns, if a bundle has a wrap its for all guns"): every = true, and the loot server gives every
-- gun's pair, guns added later too; its weapon is only the one it's shown on. a hat is for its one named weapon.
-- hero = what the big preview and the hub's hologram show: one weapon wearing its wrap and hat from the set. robux is
-- about 60% of the singles' worth (Shop.worth). the line under a bundle's name only says what's in it (Shop.describe)
local function W(id: string, weapon: string): Item return { kind = "wrap", id = id, weapon = weapon, every = true } end
local function H(id: string, weapon: string): Item return { kind = "hat", id = id, weapon = weapon } end
Shop.bundles = {
	{ id = "bundle_nightshift", type = "bundle", name = "Night Shift", rarity = "legendary",
		items = { W("hex", "ar"), H("tophat", "ar"), W("carbon", "smg"), W("lchrome", "revolver"), W("matte", "pistol") },
		hero = { weapon = "ar", wrap = "hex", hat = "tophat" } },
	{ id = "bundle_fieldissue", type = "bundle", name = "Field Issue", rarity = "rare",
		items = { W("digital", "sniper"), H("cowboy", "sniper"), W("urban", "ar"), W("desert", "shotgun"), W("arctic", "dmr") },
		hero = { weapon = "sniper", wrap = "digital", hat = "cowboy" } },
	{ id = "bundle_teahouse", type = "bundle", name = "Tea House", rarity = "legendary",
		items = { W("koi", "katana"), H("chef", "katana"), W("seigaiha", "smg"), W("asanoha", "revolver"), W("shibori", "lever"), W("sakura", "burst") },
		hero = { weapon = "katana", wrap = "koi", hat = "chef" } },
	{ id = "bundle_deepspace", type = "bundle", name = "Deep Space", rarity = "legendary",
		items = { W("nebula", "smg"), H("halo", "smg"), W("holo", "lmg"), W("aurora", "sniper"), W("blackhole", "redline") },
		hero = { weapon = "smg", wrap = "nebula", hat = "halo" } },
	{ id = "bundle_machineshop", type = "bundle", name = "Machine Shop", rarity = "epic",
		items = { W("titanium", "shotgun"), H("propeller", "shotgun"), W("brushed", "lmg"), W("hazard", "sawnoff"), W("chrome", "autoshot") },
		hero = { weapon = "shotgun", wrap = "titanium", hat = "propeller" } },
	{ id = "bundle_quarry", type = "bundle", name = "Quarry", rarity = "legendary",
		items = { W("geode", "redline"), H("crown", "redline"), W("jade", "marbles"), W("granite", "sawnoff"), W("crackle", "pistol"), W("ice", "revolver") },
		hero = { weapon = "redline", wrap = "geode", hat = "crown" } },
} :: any

-- the player card's set (the player-cards session's pick: a quiet, serious one). no hero: it dresses your card, not a
-- gun, so it's never the day's featured bundle or a hub hologram's (those take bundles with a hero). last in the list
if Shop.CardStyles then
	table.insert(Shop.bundles, { id = "bundle_cards", type = "bundle", name = "Head Office", rarity = "rare",
		items = { { kind = "border", id = "brackets" }, { kind = "banner", id = "carbon" }, { kind = "title", id = "hs" } },
		hero = nil } :: any)
end

-- the weapon skin sets (SkinSets.SETS, in their order): every skin of the set, as one bundle with the set's id. its
-- hero is the set's top piece (the rarest, the first in the set's list on a tie). a set is on sale only once every
-- one of its skins is (Shop.ready); bought again later it gives only the ones you're missing, at that share of the
-- set's price (Shop.setPrice)
Shop.sets = {} :: { Offer }
if Shop.SkinSets then
	local K = Shop.SkinSets :: any
	local ids = if type(K.ordered) == "function" then K.ordered() else {}
	for _, sid in ids do
		local s = K.SETS[sid]
		-- (the VIP set isn't sold: its skins are the VIP pack's. nor a code's set: Ducky Classic, only the hub's code panel
		-- gives it. 18 Nov)
		if vipSet(sid, s) or s.code == true then continue end
		local items, top, topR = {}, nil, -1
		for _, kid in s.members do
			if Shop.dailyOnly("skin", kid) then continue end -- (the VIP daily reward's own skin never comes in a set)
			local w = Shop.skinWeapon(kid)
			table.insert(items, { kind = "skin", id = kid, weapon = w })
			local _, r = Shop.itemInfo("skin", kid)
			if w and Shop.rank(r) > topR then top, topR = kid, Shop.rank(r) end
		end
		local hero = if top then { weapon = Shop.skinWeapon(top) :: string, skin = top } else nil
		local o = { id = sid, type = "bundle", set = sid, name = s.name, rarity = Shop.RARITY_ORDER[topR + 1] or "rare",
			items = items, hero = hero, pair = s.pair, colour = s.colour, accent = s.accent }
		table.insert(Shop.bundles, o)
		table.insert(Shop.sets, o)
	end
end

-- what's in a bundle, in plain words: "4 wraps and a hat for the Assault Rifle, SMG, Revolver and Pistol."
local function joinWords(list: { string }): string
	if #list <= 1 then return list[1] or "" end
	return table.concat(list, ", ", 1, #list - 1) .. " and " .. list[#list]
end
function Shop.describe(items: { Item }): string
	local n = { skin = 0, wrap = 0, hat = 0, card = 0 }
	local every = 0 -- (a bundle's wraps: every gun's, 18 Nov)
	local guns, seen = {}, {}
	for _, it in items do
		if it.kind == "wrap" and it.every then every += 1; continue end
		if Shop.isCard(it.kind) then n.card += 1 else n[it.kind] = (n[it.kind] or 0) + 1 end
		if it.weapon and not seen[it.weapon] then seen[it.weapon] = true; table.insert(guns, Shop.weaponName(it.weapon)) end
	end
	local parts = {}
	local function add(c: number, one: string, many: string)
		if c == 1 then table.insert(parts, one) elseif c > 1 then table.insert(parts, c .. " " .. many) end
	end
	add(n.skin, "a weapon skin", "weapon skins"); add(n.wrap, "a wrap", "wraps"); add(n.hat, "a hat", "hats")
	add(n.kill or 0, "a kill effect", "kill effects"); add(n.emote or 0, "an emote", "emotes")
	if n.card > 0 and #parts == 0 and every == 0 then return "A border, a background and a title for your player card." end
	local what = joinWords(parts)
	if #guns > 0 and what ~= "" then what ..= " for the " .. joinWords(guns) end
	if every > 0 then
		-- ("4 wraps for every gun and a hat for the Assault Rifle.")
		local ew = (if every == 1 then "a wrap" else every .. " wraps") .. " for every gun"
		what = if what ~= "" then ew .. " and " .. what else ew
	end
	return string.upper(string.sub(what, 1, 1)) .. string.sub(what, 2) .. "."
end

-- ---------------------------------------------------------------- lookups
Shop.byId = {} :: { [string]: Offer }
for _, o in Shop.containers do Shop.byId[o.id] = o end
for _, b in Shop.bundles do
	local worth = 0
	for _, it in b.items :: { Item } do worth += Shop.singlePrice(it.kind, it.id) end
	-- (a skin set is never discounted, the owner, 18 Nov: its own price is its pieces' whole worth. the other bundles,
	-- wraps, hats and card looks, are 40% under theirs)
	b.robux = if b.set then worth else math.floor(worth * Shop.MONEY.bundleShare / 10 + 0.5) * 10 - 1
	b.productId = nil
	b.blurb = Shop.describe(b.items)
	Shop.byId[b.id] = b
end
-- a bundle that can be sold right now: a skin set once every skin in it is in the place (and known to the loot
-- module); the rest always
function Shop.ready(o: Offer): boolean
	if o.set then
		for _, it in o.items :: { Item } do if not Shop.exists(it.kind, it.id) then return false end end
	end
	return true
end
-- the bundles on show (the BUNDLES grid, the featured pick, the hub): ready ones, skin sets not among them unless asked
function Shop.shown(withSets: boolean?): { Offer }
	local out = {}
	for _, b in Shop.bundles do
		if Shop.ready(b) and (withSets or not b.set) then table.insert(out, b) end
	end
	return out
end
-- what completing a skin set costs when `missing` of its skins are left: that share of the set's price, rounded up
-- (pro rata, never under it: no discount on a set, 18 Nov) (the whole set: its own price). a developer product per set
-- and count, "set_seraph" / "set_seraph:3" (Shop.PRODUCTS)
function Shop.setPrice(o: Offer, missing: number?): number
	local total = #(o.items :: { Item })
	local m = missing or total
	if m >= total or total == 0 then return o.robux end
	return math.max(0, math.ceil(o.robux * m / total))
end

-- ---------------------------------------------------------------- weapon bundles (19 Nov, the owner: "we should have
-- bundles that include some free weapons too, maybe assault bundle can come with like burst minigun smg etc. Explosives
-- janky can come with like pepper a couple other silly ones"). Robux only (no coins). each one unlocks its Robux weapon
-- for good (Purchases.giveWeapon: it stays when Unlocks.WEAPONS_ROBUX_FREE goes off) and dresses every weapon in it: a
-- wrap for that one weapon each (not every gun's, unlike the cosmetic bundles), plus a hat or card looks. wraps, hats and
-- card looks that exist only (skins are paused). its price is under the sum of its parts (Shop.worth counts the weapon:
-- Assault 1,359 -> 799, Explosives 1,474 -> 799). shown on the shop's WEAPONS page; not in the BUNDLES grid, the featured
-- pick or the hub's holograms (those walk Shop.bundles). OFF until the owner reviews them (Studio: WeaponBundlesTest)
Shop.WEAPON_BUNDLES_ON = true -- (ON since 19 Nov, the owner)
function Shop.weaponBundlesOn(): boolean
	if Shop.WEAPON_BUNDLES_ON then return true end
	return RunService:IsStudio() and ReplicatedStorage:GetAttribute("WeaponBundlesTest") == true
end
local function G(id: string, weapon: string): Item return { kind = "wrap", id = id, weapon = weapon } end -- (that gun's only)
-- (the Explosives bundle's fire wrap: Molten, the living lava, once it is in Roster; Tangerine until then. 27 Nov)
local FIRE = if Roster.wrapById.molten then "molten" else "tangerine"
Shop.weaponBundles = {
	{ id = "wbundle_assault", type = "bundle", name = "Assault", rarity = "legendary", robux = 799, weapons = { "minigun" },
		items = { G("tiger", "minigun"), G("camo", "ar"), G("tape", "smg"), G("ghost", "burst"), G("digital", "lmg"), G("arctic", "dmr"),
			{ kind = "title", id = "zero_recoil" }, { kind = "banner", id = "camo" } },
		hero = { weapon = "minigun", wrap = "tiger" },
		blurb = "The Minigun for good, a wrap for six guns, a title and a background." },
	{ id = "wbundle_explosives", type = "bundle", name = "Explosives", rarity = "legendary", robux = 799, weapons = { "chicken" },
		items = { G(FIRE, "chicken"), H("eyes", "chicken"), G("bowling", "bowling"), G("cherry", "cig"), G("hazard", "frag"),
			G("sprinkles", "popper"), G("memphis", "banana"), G("barcode", "cart"), { kind = "banner", id = "flames" } },
		hero = { weapon = "chicken", wrap = FIRE, hat = "eyes" },
		blurb = "The Chicken Rocket for good, a wrap for seven weapons, a hat and a background." },
} :: any
for _, b in Shop.weaponBundles do b.productId = nil; Shop.byId[b.id] = b end
-- (19 Nov, the owner: "only skins cost robux": the weapon bundles are COIN bundles now, sold in the loadout's armory, not
-- the shop: every weapon in one you can't carry yet (its Robux weapon, and the level weapons you haven't reached) unlocked
-- for good, plus its cosmetics you lack, WBUNDLE_OFF percent under their coin prices (a Robux weapon at its coin price,
-- a level one at its early-unlock price). Purchases "wbquote" / "wbundle". their Robux products are off sale)
Shop.WBUNDLE_OFF = 25
function Shop.wbundleWeapons(o: any): { string }
	local out, seen = {}, {}
	for _, wid in (o.weapons or {}) :: { string } do if not seen[wid] then seen[wid] = true; table.insert(out, wid) end end
	for _, it in (o.items or {}) :: { any } do
		local w = it.weapon
		if type(w) == "string" and not seen[w] and Roster.byId[w] then seen[w] = true; table.insert(out, w) end
	end
	return out
end
function Shop.wbundleCoins(o: any, lacksWeapon: (string) -> boolean, lacksItem: (any) -> boolean): (number, number)
	local full = 0
	for _, wid in Shop.wbundleWeapons(o) do
		if lacksWeapon(wid) then
			local m = (Shop.MONEY.weapons :: any)[wid]
			full += if m then m.coins else ((Shop :: any).earlyPrice(wid) or 0)
		end
	end
	local cp = Shop.MONEY.coinPrices :: any
	for _, it in (o.items or {}) :: { any } do
		if lacksItem(it) then
			local t = cp.singles[it.kind]
			local _, r = Shop.itemInfo(it.kind, it.id)
			full += (t and t[r]) or 0
		end
	end
	if full <= 0 then return 0, 0 end
	return math.max(50, math.floor(full * (100 - Shop.WBUNDLE_OFF) / 100 / 50 + 0.5) * 50), full
end

-- the singles the rotation can show (wraps and hats that are not free, not held back and not VIP)
Shop.singlesPool = {} :: { Item }
for _, w in Roster.wraps do
	if w.rarity ~= "free" and not Shop.HELD_BACK[w.id] and w.id ~= Shop.PACK_GOLD and not Shop.vipOnly("wrap", w.id) and not Shop.dailyOnly("wrap", w.id) then table.insert(Shop.singlesPool, W(w.id)) end
end
for _, id in GunHatData.ORDER do
	local h = GunHatData.HATS[id]
	if id ~= "none" and h and h.rarity ~= "free" and not Shop.vipOnly("hat", id) and not Shop.dailyOnly("hat", id) then table.insert(Shop.singlesPool, H(id)) end
end

-- ---------------------------------------------------------------- VIP (a game pass; Vip.luau decides who has it)
-- the game pass (made 18 Nov 2026 by the main session, off sale, 399 Robux, the gold Royal Duck icon). with Shop.ROBUX on
-- the shop's GET VIP shows Roblox's pass prompt; while the shop is free anyone can still claim VIP (Vip.luau)
Shop.VIP_PASS = 2093409349
Shop.vip = { id = "vip", type = "pass", name = "VIP", rarity = "vip", robux = Shop.MONEY.vip, productId = nil,
	blurb = "The Ducky pack, the VIP room and a daily reward.",
	perks = { "The Ducky pack: its weapon skins, a wrap and a hat on every gun, a card border and a title",
		"The VIP room in the hub", "A daily reward from Trisangle in the VIP room" } } :: any
Shop.byId.vip = Shop.vip
-- what the VIP pack holds today: every VIP thing that's in the place (it grows as they land; Vip.luau grants the new
-- ones once). wraps and hats have no weapon: they're worn on every gun
function Shop.vipItems(): { Item }
	local out = {}
	if LootTable and type(LootTable.SKINS) == "table" then
		local ids = {}
		for id in LootTable.SKINS do if Shop.vipOnly("skin", id) and Shop.skinLive(id) and not Shop.dailyOnly("skin", id) then table.insert(ids, id) end end
		-- (in the VIP set's own order: its first is the top piece, the Tripo ducks' SMG since 18 Nov; then the rarest, then by id)
		local at: { [string]: number } = {}
		local K = Shop.SkinSets :: any
		if K and type(K.SETS) == "table" then
			for sid, s in K.SETS do
				if vipSet(sid, s) then for i, kid in s.members or {} do at[kid] = i end end
			end
		end
		table.sort(ids, function(a, b)
			if (at[a] or 99) ~= (at[b] or 99) then return (at[a] or 99) < (at[b] or 99) end
			local _, ra = Shop.itemInfo("skin", a)
			local _, rb = Shop.itemInfo("skin", b)
			if Shop.rank(ra) ~= Shop.rank(rb) then return Shop.rank(ra) > Shop.rank(rb) end
			return a < b
		end)
		for _, id in ids do table.insert(out, { kind = "skin", id = id, weapon = Shop.skinWeapon(id) }) end
	end
	for _, w in Roster.wraps do if Shop.vipOnly("wrap", w.id) and not Shop.dailyOnly("wrap", w.id) then table.insert(out, { kind = "wrap", id = w.id }) end end
	for _, id in GunHatData.ORDER do if id ~= "none" and Shop.vipOnly("hat", id) and not Shop.dailyOnly("hat", id) then table.insert(out, { kind = "hat", id = id }) end end
	if Shop.CardStyles then
		local C = Shop.CardStyles :: any
		for _, k in { "border", "banner", "title" } do
			for _, cid in ((C.ORDER or {})[k] or {}) :: { string } do
				if Shop.vipOnly(k, cid) then table.insert(out, { kind = k, id = cid }) end
			end
		end
	end
	if Shop.Flair then
		local F = Shop.Flair :: any
		for _, k in { "kill", "emote" } do
			for _, fid in ((F.ORDER or {})[k] or {}) :: { string } do
				if Shop.vipOnly(k, fid) then table.insert(out, { kind = k, id = fid }) end
			end
		end
	end
	return out
end
-- what the VIP tile shows big: the pack's top skin wearing the VIP hat (or a rifle with the VIP wrap)
function Shop.vipHero(): Hero?
	local skin, wrap, hat = nil, nil, nil
	for _, it in Shop.vipItems() do
		if it.kind == "skin" and not skin then skin = it end
		if it.kind == "wrap" and not wrap then wrap = it.id end
		if it.kind == "hat" and not hat then hat = it.id end
	end
	if skin then return { weapon = skin.weapon :: string, skin = skin.id, hat = hat } end
	if wrap or hat then return { weapon = "ar", wrap = wrap, hat = hat } end
	return nil
end

-- a single: one wrap or hat for one weapon, id "wrap:<id>@<weapon>" / "hat:<id>@<weapon>"; one weapon skin,
-- "skin:<id>" (its weapon is its own: the offer carries it, the id doesn't); or one card look, "border:<id>" /
-- "banner:<id>" / "title:<id>", kill effect "kill:<id>" or emote "emote:<id>" (no weapon)
local function single(kind: string, id: string, weapon: string?): Offer?
	if not Shop.exists(kind, id, weapon) or Shop.vipOnly(kind, id) or Shop.dailyOnly(kind, id) or Shop.secret(kind, id) then return nil end
	if kind == "wrap" and id == Shop.PACK_GOLD then return nil end -- (the big packs' own)
	if Shop.setOnly(kind, id) then return nil end -- (a set's piece: only its set sells it, 18 Nov)
	if Shop.isFlair(kind) and not Shop.flairForSale(kind, id) then return nil end
	local name, rarity = Shop.itemInfo(kind, id)
	if rarity == "free" then return nil end
	local oid = if Shop.gunless(kind) then kind .. ":" .. id else kind .. ":" .. id .. "@" .. (weapon :: string)
	return { id = oid, type = "single", name = name, rarity = rarity,
		blurb = "", robux = Shop.singlePrice(kind, id), productId = nil, kind = kind, item = id,
		weapon = if kind == "skin" then Shop.skinWeapon(id) else weapon }
end

-- any offer by id: a container, a bundle or skin set, or a single ("wrap:galaxy@smg", "hat:crown@katana",
-- "skin:ar_keytar", "border:brackets")
function Shop.offer(id: any): Offer?
	if type(id) ~= "string" then return nil end
	local o = Shop.byId[id]
	if o then return if Shop.ready(o) then o else nil end
	-- (one of the VIP daily reward's own three: never on sale, only the server's Loot.grant takes it)
	local dk, did = string.match(id, "^vipdaily:(%a+):([%w_]+)$")
	if dk and did then
		if not Shop.dailyOnly(dk, did) or not Shop.exists(dk, did) then return nil end
		local name, rarity = Shop.itemInfo(dk, did)
		return { id = id, type = "pass", name = name, rarity = rarity, blurb = "", robux = 0, productId = nil,
			items = { { kind = dk, id = did, weapon = if dk == "skin" then Shop.skinWeapon(did) else nil } } }
	end
	-- (a found thing's prize, the hub egg's: never on sale, only the server's Loot.grant takes it)
	local ek, eid = string.match(id, "^egg:(%a+):([%w_]+)$")
	if ek and eid then
		if not Shop.secret(ek, eid) or not Shop.exists(ek, eid) then return nil end
		local name, rarity = Shop.itemInfo(ek, eid)
		return { id = id, type = "pass", name = name, rarity = rarity, blurb = "", robux = 0, productId = nil,
			items = { { kind = ek, id = eid } } }
	end
	-- (the big coin packs' Bullion wrap, on every gun: only the server's Loot.grant takes it, Purchases.packExtras)
	if id == "pack:gold" then
		if not Roster.wrapById[Shop.PACK_GOLD] then return nil end
		local name, rarity = Shop.itemInfo("wrap", Shop.PACK_GOLD)
		return { id = id, type = "pass", name = name, rarity = rarity, blurb = "", robux = 0, productId = nil,
			items = { { kind = "wrap", id = Shop.PACK_GOLD, weapon = "ar", every = true } } }
	end
	-- (a gift: anything that exists, given by the server alone through Loot.grant, never on sale or in the shop: a lore
	-- NPC's prize, 18 Nov, the Janitor's "gift:grapple:plunger". a wrap or hat takes its gun after an @ ("gift:wrap:galaxy@smg"),
	-- else it's on every gun. type "pass": the loot server's "buy" refuses it)
	local gk, gid, gw = string.match(id, "^gift:(%a+):([%w_]+)@?([%w_]*)$")
	if gk and gid then
		local info = if LootTable and type(LootTable.info) == "function" then LootTable.info(gk, gid) else nil
		if type(info) ~= "table" then return nil end
		return { id = id, type = "pass", name = info.name, rarity = info.rarity, blurb = "", robux = 0, productId = nil,
			items = { { kind = gk, id = gid, weapon = if gw ~= "" then gw elseif gk == "skin" then Shop.skinWeapon(gid) else nil } } }
	end
	local kind, item, weapon = string.match(id, "^(%a+):([%w_]+)@([%w_]+)$")
	if kind and item and weapon and not Shop.gunless(kind) then return single(kind, item, weapon) end
	local ck, cid = string.match(id, "^(%a+):([%w_]+)$")
	if ck and cid and Shop.gunless(ck) then return single(ck, cid, nil) end
	return nil
end

-- what an offer gives, each { kind, id, weapon } (a container gives itself: the loot server adds one to your stock)
function Shop.contents(o: Offer): { Item }
	if o.type == "bundle" then return o.items :: { Item } end
	if o.type == "pass" then return (o.items :: { Item }?) or Shop.vipItems() end
	if o.type == "single" then return { { kind = o.kind :: string, id = o.item :: string, weapon = o.weapon } } end
	return {}
end
-- what a bundle's items would cost one by one
function Shop.worth(o: Offer): number
	local n = 0
	for _, it in Shop.contents(o) do n += Shop.singlePrice(it.kind, it.id) end
	-- (a weapon bundle's weapon, at its own Robux price)
	for _, wid in ((o :: any).weapons or {}) :: { string } do
		local m = (Shop.MONEY.weapons :: any)[wid]
		if m then n += m.robux end
	end
	return n
end

-- ---------------------------------------------------------------- the owner's deals (Deals.luau on the server picks them)
-- the owner, 17 Nov 2026: "I give players 3 special discounts on random skins if you talk to me!". per player per UTC
-- day: three weapon skins on sale (Shop.liveSkins: not VIP, not daily-only, not a concept, not a set's) they don't own, at
-- most one legendary, a different skin set and gun each where it can. each is DEAL_OFF[rarity] percent off its single
-- price, the rarest of the three DEAL_TOP more: 20 to 40% off. they stay the same all day; each can be had once.
-- offer ids "deal:<skin>" (only the player's own deals: the server checks), a product per rarity and discount when
-- Robux goes on ("deal:legendary:40", Shop.PRODUCTS)
Shop.DEALS = 3
Shop.DEAL_OFF = { common = 20, rare = 25, epic = 30, legendary = 35 }
Shop.DEAL_TOP = 5
Shop.DEAL_PICK = { common = 40, rare = 35, epic = 20, legendary = 5 } -- how likely each rarity is picked
function Shop.dealPrice(kind: string, id: string, pct: number): number
	local full = Shop.singlePrice(kind, id)
	if full <= 0 then return 0 end
	return math.max(9, math.floor(full * (100 - pct) / 100 / 10 + 0.5) * 10 - 1)
end

-- ---------------------------------------------------------------- the featured rotation
-- one hero bundle and Shop.DAILY singles a day, the same for everyone (seeded by the UTC day number), so the server can
-- check a single is on sale today without keeping any state
function Shop.day(t: number?): number
	-- (Studio tests, 27 Nov: ReplicatedStorage's attribute ShopDayTest = n shows the day n days on, server and clients alike)
	local shift = if RunService:IsStudio() then tonumber(ReplicatedStorage:GetAttribute("ShopDayTest")) or 0 else 0
	return math.floor((t or os.time()) / Shop.ROTATE) + math.floor(shift)
end
function Shop.secondsLeft(t: number?): number
	local now = t or os.time()
	return (Shop.day(now) + 1) * Shop.ROTATE - now
end
local rotCache: { [number]: { hero: string, daily: { string } } } = {}
function Shop.rotation(day: number?): { hero: string, daily: { string } }
	local d = day or Shop.day()
	local hit = rotCache[d]
	if hit then return hit end
	local rng = Random.new(d * 7919 + 17)
	-- (the hero is a bundle with a hero piece: the gun bundles and the skin sets on sale, in a fixed cycle)
	local heroes = {}
	for _, b in Shop.shown(true) do if b.hero then table.insert(heroes, b.id) end end
	local hero = heroes[(d % #heroes) + 1]
	-- wraps and two hats, each for one weapon, at least one epic-or-better, no cosmetic and no weapon twice; with
	-- weapon skins in the place one of the six is a skin, with the player card's looks one is a card look, and with
	-- kill effects and emotes one is one of those (and one hat, not two)
	local wraps, hats = {}, {}
	for _, it in Shop.singlesPool do table.insert(if it.kind == "wrap" then wraps else hats, it) end
	local weapons = table.clone(Shop.WEAPONS)
	local function gun(): string
		if #weapons == 0 then weapons = table.clone(Shop.WEAPONS) end
		return table.remove(weapons, rng:NextInteger(1, #weapons)) :: string
	end
	local function draw(from: { Item }, n: number, out: { string })
		local bag = table.clone(from)
		for _ = 1, math.min(n, #bag) do
			local i = rng:NextInteger(1, #bag)
			table.insert(out, bag[i].kind .. ":" .. bag[i].id .. "@" .. gun())
			table.remove(bag, i)
		end
	end
	local daily = {}
	-- (with the player card's looks in the place, one of the six is a border, background or title)
	local cards = {}
	if Shop.CardStyles then
		for _, k in { "border", "banner", "title" } do
			for _, cid in ((Shop.CardStyles :: any).ORDER[k] or {}) :: { string } do
				local _, r = Shop.itemInfo(k, cid)
				if r ~= "free" and not Shop.vipOnly(k, cid) and not Shop.secret(k, cid) then table.insert(cards, k .. ":" .. cid) end
			end
		end
	end
	local skins = {}
	for _, sid in Shop.liveSkins() do
		local _, r = Shop.itemInfo("skin", sid)
		if r ~= "free" then table.insert(skins, "skin:" .. sid) end
	end
	-- (with kill effects and emotes in the place, one of the six is one of them, in a hat's place)
	local flair = {}
	if Shop.Flair then
		for _, k in { "kill", "emote" } do
			local ok, list = pcall((Shop.Flair :: any).forSale, k)
			if ok and type(list) == "table" then
				for _, i in list do if single(k, i.id, nil) then table.insert(flair, k .. ":" .. i.id) end end
			end
		end
	end
	local nHats = if #flair > 0 then 1 else 2
	draw(wraps, Shop.DAILY - nHats - (if #cards > 0 then 1 else 0) - (if #skins > 0 then 1 else 0) - (if #flair > 0 then 1 else 0), daily)
	draw(hats, nHats, daily)
	if #cards > 0 then table.insert(daily, cards[rng:NextInteger(1, #cards)]) end
	if #skins > 0 then table.insert(daily, skins[rng:NextInteger(1, #skins)]) end
	if #flair > 0 then table.insert(daily, flair[rng:NextInteger(1, #flair)]) end
	local best = 0
	for _, id in daily do
		local o = Shop.offer(id)
		if o then best = math.max(best, Shop.rank(o.rarity)) end
	end
	if best < 3 then
		local big = {}
		local have = {}
		for _, id in daily do have[(string.match(id, "^%a+:([%w_]+)@") or "")] = true end
		for _, it in wraps do
			local _, r = Shop.itemInfo(it.kind, it.id)
			if Shop.rank(r) >= 3 and not have[it.id] then table.insert(big, it) end
		end
		if #big > 0 then
			local it = big[rng:NextInteger(1, #big)]
			local w = string.match(daily[1], "@([%w_]+)$") :: string
			daily[1] = "wrap:" .. it.id .. "@" .. w
		end
	end
	-- dearest first, so the row reads from the big one down
	table.sort(daily, function(a, b)
		local oa, ob = Shop.offer(a), Shop.offer(b)
		local ra, rb = if oa then Shop.rank(oa.rarity) else 0, if ob then Shop.rank(ob.rarity) else 0
		if ra ~= rb then return ra > rb end
		return a < b
	end)
	local r = { hero = hero, daily = daily }
	-- (the skins on sale are read from the place: a client asking before it has all of it isn't remembered)
	if game:IsLoaded() then rotCache[d] = r end
	return r
end

-- can this offer be bought right now? containers and bundles always; a single only while it's in today's rotation
-- (yesterday's too, for a few minutes after the turn, so a click made just before midnight still goes through)
function Shop.onSale(id: string, t: number?): boolean
	local o = Shop.offer(id)
	if not o then return false end
	if o.type == "pass" then return false end -- (VIP isn't bought through the till: Vip.luau, the game pass)
	if (o :: any).weapons and (not Shop.weaponBundlesOn() or Shop.coinsOnly()) then return false end -- (the weapon bundles: coins in the armory now, never the shop's Robux)
	if o.type == "vipgift" and not Shop.giftsOn() then return false end -- (VIP as a gift: the gifts' switch)
	if (o :: any).legacy then return false end -- (the first Spray Can: not sold any more, 20 Nov)
	if o.type ~= "single" then return true end
	local now = t or os.time()
	if table.find(Shop.rotation(Shop.day(now)).daily, id) then return true end
	if now % Shop.ROTATE < 300 and table.find(Shop.rotation(Shop.day(now) - 1).daily, id) then return true end
	return false
end

-- ---------------------------------------------------------------- container odds
-- read from the loot module (LootTable.odds: the same function the server rolls by) so the shop never shows numbers
-- the server doesn't use. a roll never gives what you already own, so the odds depend on what you own:
-- owned = { wrap = { [id] = true }, hat = ..., skin = ... }. returns rows { rarity, pct (0..100), count (left to get),
-- total } and the whole LootTable answer (.soon: nothing in it on roblox yet, .empty: you own all of it, .items), or
-- nil if the loot module isn't there
function Shop.odds(containerId: string, owned: any?): ({ { rarity: string, pct: number, count: number?, total: number? } }?, any)
	if not LootTable or type(LootTable.odds) ~= "function" then return nil, nil end
	local ok, o = pcall(LootTable.odds, containerId, owned)
	if not ok or type(o) ~= "table" then return nil, nil end
	local rows = {}
	for _, r in o.rarities or {} do
		table.insert(rows, { rarity = r.rarity, pct = (r.chance or 0) * 100, count = r.left, total = r.total })
	end
	return rows, o
end
-- every final outcome and its own chance (LootTable.oddsDetail): groups of { rarity, name, gun, each (0..1), items }
function Shop.oddsDetail(containerId: string, owned: any?): { any }?
	if not LootTable or type(LootTable.oddsDetail) ~= "function" then return nil end
	local ok, d = pcall(LootTable.oddsDetail, containerId, owned)
	return if ok and type(d) == "table" then d else nil
end
-- nothing in this container is on roblox yet
function Shop.soon(containerId: string): boolean
	return LootTable ~= nil and type(LootTable.soon) == "function" and LootTable.soon(containerId) == true
end

-- ---------------------------------------------------------------- the Robux weapons and coin packs (18 Nov)
-- the Robux-exclusive weapons (Unlocks.ROBUX) as offers, "weapon:<id>": bought once and kept for good, with Robux (its
-- developer product, ShopReceipts) or with Coins (taken by the server: Purchases.luau). prices: Shop.MONEY.weapons
local function digits(n: number): string
	local s = tostring(math.floor(n))
	while true do
		local k
		s, k = string.gsub(s, "^(%d+)(%d%d%d)", "%1,%2")
		if k == 0 then return s end
	end
end
Shop.WEAPON_IDS = {} :: { string } -- (cheapest first)
for wid in Shop.MONEY.weapons do table.insert(Shop.WEAPON_IDS, wid) end
table.sort(Shop.WEAPON_IDS, function(a: string, b: string): boolean
	local x, y = (Shop.MONEY.weapons :: any)[a].robux, (Shop.MONEY.weapons :: any)[b].robux
	return if x ~= y then x < y else a < b
end)
function Shop.weaponOffer(wid: any): any
	if type(wid) ~= "string" then return nil end
	local m = (Shop.MONEY.weapons :: any)[wid]
	local e = Roster.byId[wid]
	if not m or not e then return nil end
	return { id = "weapon:" .. wid, type = "weapon", name = e.name, rarity = "legendary", blurb = "", robux = m.robux,
		coins = m.coins, productId = nil, weapon = wid }
end
-- coin packs for Robux, "coins:<id>" (Shop.MONEY.coins, in order): amount = what lands, the pack's bonus in it
function Shop.coinPacks(): { any }
	local out = {}
	for _, b in Shop.MONEY.coins do
		table.insert(out, { id = "coins:" .. b.id, type = "coins", name = digits(b.coins + b.bonus) .. " Coins", rarity = "common",
			blurb = "", robux = b.robux, amount = b.coins + b.bonus, bonus = b.bonus, image = b.image, productId = nil, extras = (b :: any).extras })
	end
	return out
end
function Shop.coinPack(id: any): any
	for _, o in Shop.coinPacks() do if o.id == id then return o end end
	return nil
end

-- ---------------------------------------------------------------- the big coin packs' extras (19 Nov, the owner: "the
-- bigger packs should come with rewards like rivals gives you, weapon skins for the 2 biggest packs, a finisher for a
-- random weapon I think, a gold wrap, a skin case etc"). 1,999: a legendary weapon skin you PICK and a Crate. 4,500: a
-- skin with a finisher you pick, the Bullion wrap on every gun and 3 Crates. the skin is chosen from a short list, never
-- random (a random item bought with Robux would be a paid random item): the pick waits in the buyer's save until it's
-- made (Purchases.packExtras, ShopUI's PICK panel), so a crash never loses it. own every skin on the list (or Bullion)
-- already: coins of the same worth instead, and they're told. the Crates follow the paid-random-items rules (odds before
-- any opening; where Roblox's policy keeps a player from them, coins of the same worth). every purchase gives them again.
-- OFF until the owner reviews them (Studio: PackExtrasTest)
Shop.PACK_EXTRAS_ON = true -- (ON since 19 Nov, the owner)
function Shop.packExtrasOn(): boolean
	if Shop.PACK_EXTRAS_ON then return true end
	return RunService:IsStudio() and ReplicatedStorage:GetAttribute("PackExtrasTest") == true
end
-- the lists a skin is picked from: legendary weapon skins that are no set's piece, and the skins with a finisher (every
-- one is a set's: Shared.Finishers). a skin not in the place drops out (Shop.pickList)
Shop.PICKS = {
	legendary = { "ar_keytar", "katana_neon", "sniper_musket", "knife_butterfly", "scythe_reaper", "duck_gold", "spin_aura" },
	finisher = { "ar_seraph_tripo", "ar_infernal", "katana_sakura", "smg_pumpkin", "revolver_dust", "lever_dust", "revolver_star", "lever_star" },
}
Shop.PICK_WORDS = { legendary = "LEGENDARY SKIN", finisher = "FINISHER SKIN" }
function Shop.pickList(kind: string): { string }
	local out = {}
	for _, id in ((Shop.PICKS :: any)[kind] or {}) :: { string } do
		if Shop.skinLive(id) and not Shop.vipOnly("skin", id) and not Shop.dailyOnly("skin", id) then table.insert(out, id) end
	end
	return out
end
-- what an extra is worth in coins when it's given as coins (the coins-only shop's prices): the skin a legendary skin,
-- Bullion a legendary wrap, a Crate its coin price
function Shop.extraCoins(what: string): number
	local cp = Shop.MONEY.coinPrices :: any
	if what == "pick" then return cp.singles.skin.legendary end
	if what == "gold" then return cp.singles.wrap.legendary end
	if what == "crate" then return cp.containers.crate end
	return 0
end
-- the extras in short words for a pack's card: "+ LEGENDARY SKIN  ·  + CRATE" (restricted: the Crates as coins)
function Shop.extrasWords(o: any, restricted: boolean?): string?
	local ex = type(o) == "table" and o.extras
	if type(ex) ~= "table" or not Shop.packExtrasOn() then return nil end
	local parts = {}
	if ex.pick then table.insert(parts, "+ " .. ((Shop.PICK_WORDS :: any)[ex.pick] or "SKIN")) end
	if ex.gold then table.insert(parts, "+ GOLD WRAP") end
	local n = tonumber(ex.crates) or 0
	if n > 0 then
		table.insert(parts, if restricted then "+ " .. digits(n * Shop.extraCoins("crate")) .. " COINS" elseif n == 1 then "+ CRATE" else "+ " .. n .. " CRATES")
	end
	return table.concat(parts, "  ·  ")
end

-- ---------------------------------------------------------------- gifts (19 Nov, the owner: "weapon bundles should be
-- gamepasses too! I want people to be able to gift them! Should all passes be game passes?"). Roblox can't gift a game
-- pass (one is only ever bought for your own account), so what can be gifted stays a developer product and the shop gifts
-- it itself: the buyer picks someone (in this server, or by name if they've played before), pays through the same
-- product, and the server's Gifts module puts it in the receiver's gift box (a save of its own) and hands it over the
-- moment they're in a server, with the present's reveal and a chat line. giftable: bundles (the cosmetic ones, the
-- weapon bundles, a skin set: the whole set), coin packs, and VIP through its own product ("vipgift": VIP itself stays a
-- game pass, for yourself). never a container or a single. OFF until the owner has seen it (Studio: GiftsTest)
Shop.GIFTS_ON = true -- (ON since 19 Nov, the owner)
function Shop.giftsOn(): boolean
	if Shop.GIFTS_ON then return true end
	return RunService:IsStudio() and ReplicatedStorage:GetAttribute("GiftsTest") == true
end
Shop.vipGift = { id = "vipgift", type = "vipgift", name = "VIP", rarity = "vip", robux = Shop.MONEY.vip, productId = nil,
	blurb = "VIP for someone else: the Ducky pack, the VIP room and its daily reward, for good." } :: any
Shop.byId.vipgift = Shop.vipGift
function Shop.giftable(o: any): boolean
	if type(o) ~= "table" then return false end
	-- (19 Nov, the owner's rule: gifts are what Robux buys. a weapon skin, a skin set, coins, a container, VIP)
	if o.type == "coins" or o.type == "vipgift" or o.type == "container" then return true end
	if o.type == "single" then return o.kind == "skin" end
	if o.type == "bundle" then return o.set ~= nil end
	return false
end

-- ---------------------------------------------------------------- early unlocks (19 Nov, the owner: "coin is supposed to
-- be able to buy weapons early!"). a weapon or gadget that opens at a level (Unlocks.LEVEL, 2 and up) can be bought with
-- coins before the player gets there, for good: the server takes the coins and keeps it (Purchases "early", the same
-- three writes as a Robux weapon's coins buy, its RobuxOwned list), and reaching the level later changes nothing. priced
-- by the level it opens at, under the Robux weapons' coin prices (4,000-5,000). OFF until the owner reviews the prices
-- (Studio: EarlyTest)
Shop.EARLY_ON = true -- (ON since 19 Nov, the owner)
function Shop.earlyOn(): boolean
	if Shop.EARLY_ON then return true end
	return RunService:IsStudio() and ReplicatedStorage:GetAttribute("EarlyTest") == true
end
-- coins by the level a weapon opens at (up to that level: that price)
Shop.MONEY.earlyCoins = {
	{ upTo = 3, coins = 500 }, { upTo = 6, coins = 1000 }, { upTo = 9, coins = 1500 }, { upTo = 12, coins = 2000 },
	{ upTo = 15, coins = 2500 }, { upTo = 18, coins = 3000 }, { upTo = 21, coins = 3500 }, { upTo = 99, coins = 4000 },
}
-- a weapon's early-unlock price in coins, or nil: not one that opens at a level (a Robux weapon, level 1, not live)
function Shop.earlyPrice(wid: any): number?
	if type(wid) ~= "string" then return nil end
	local e = Roster.byId[wid]
	if not e or not e.live then return nil end
	if Shop.Unlocks == nil then
		local m = script.Parent:FindFirstChild("Unlocks")
		local ok, U = false, nil
		if m and m:IsA("ModuleScript") then ok, U = pcall(require, m) end
		Shop.Unlocks = if ok and type(U) == "table" then U else false
	end
	local U = Shop.Unlocks :: any
	if not U or U.ROBUX[wid] then return nil end
	local lv = U.LEVEL[wid] or 1
	if lv <= 1 then return nil end
	for _, b in (Shop.MONEY :: any).earlyCoins do if lv <= b.upTo then return b.coins end end
	return nil
end

-- ---------------------------------------------------------------- developer products (off while Shop.ROBUX is false)
-- made 18 Nov 2026 with Open Cloud, 88 of them (docs/MONEY.md has the list with names and prices): one per container,
-- bundle and coin pack; one per skin set and per count of skins left to complete it ("set_seraph:3", priced as
-- Shop.setPrice); singles share one per kind and rarity ("wrap:epic": the server remembers which single you asked for,
-- ShopReceipts); the owner's deals one per rarity and discount ("deal:legendary:40", priced as Shop.dealPrice); one per
-- Robux weapon ("weapon:minigun"). each is on sale with its store page off: only the game's own prompt sells it, and
-- nothing prompts while Shop.ROBUX is false. a price changed in Shop.MONEY needs the product's price changed too
Shop.PRODUCTS = {
	-- (containers)
	crate = 3733200177, bag = 3733200704, spray = 3733200725,
	-- (and in fives and tens, made 19 Nov 2026: every count has its Robux price beside its coin price)
	["crate:5"] = 3733759267, ["crate:10"] = 3733759286, ["bag:5"] = 3733759307, ["bag:10"] = 3733759328,
	["spray:5"] = 3733759347, ["spray:10"] = 3733759369,
	-- (the spray sets, made 20 Nov 2026, one, five and ten each. the first Spray Can's three above stay for late receipts)
	spraycosmic = 3734017670, ["spraycosmic:5"] = 3734017731, ["spraycosmic:10"] = 3734017737,
	sprayjapan = 3734017743, ["sprayjapan:5"] = 3734017756, ["sprayjapan:10"] = 3734017761,
	sprayluxe = 3734017820, ["sprayluxe:5"] = 3734017829, ["sprayluxe:10"] = 3734017837,
	spraywild = 3734017844, ["spraywild:5"] = 3734017857, ["spraywild:10"] = 3734017866,
	spraydiner = 3734017939, ["spraydiner:5"] = 3734017949, ["spraydiner:10"] = 3734017956,
	sprayoffice = 3734017965, ["sprayoffice:5"] = 3734017974, ["sprayoffice:10"] = 3734017983,
	-- (bundles)
	bundle_nightshift = 3733200745, bundle_fieldissue = 3733200855, bundle_teahouse = 3733200884,
	bundle_deepspace = 3733200908, bundle_machineshop = 3733201016, bundle_quarry = 3733201039,
	bundle_cards = 3733201064,
	-- (skin sets, and completing one with n skins left)
	set_seraph = 3733201174, ["set_seraph:1"] = 3733201190, ["set_seraph:2"] = 3733201209,
	["set_seraph:3"] = 3733201426, ["set_seraph:4"] = 3733201313, set_infernal = 3733201329,
	["set_infernal:1"] = 3733201448, ["set_infernal:2"] = 3733201459, ["set_infernal:3"] = 3733201580,
	["set_infernal:4"] = 3733201598, set_halloween = 3733201617, ["set_halloween:1"] = 3733201706,
	["set_halloween:2"] = 3733201726, ["set_halloween:3"] = 3733201741, ["set_halloween:4"] = 3733201837,
	set_tidecrest = 3733201862, ["set_tidecrest:1"] = 3733201889, ["set_tidecrest:2"] = 3733201991,
	["set_tidecrest:3"] = 3733202011, ["set_tidecrest:4"] = 3733202029, set_dust = 3733202122,
	["set_dust:1"] = 3733202140, ["set_dust:2"] = 3733202160, ["set_dust:3"] = 3733202240, ["set_dust:4"] = 3733202257,
	set_star = 3733202273, ["set_star:1"] = 3733202349, ["set_star:2"] = 3733202363, ["set_star:3"] = 3733202382,
	["set_star:4"] = 3733202477,
	-- (singles, one per kind and rarity)
	["banner:common"] = 3733202493, ["banner:rare"] = 3733202511, ["banner:epic"] = 3733202602,
	["banner:legendary"] = 3733202625, ["border:common"] = 3733202645, ["border:rare"] = 3733202732,
	["border:epic"] = 3733202751, ["border:legendary"] = 3733202769, ["emote:common"] = 3733202887,
	["emote:rare"] = 3733202906, ["emote:epic"] = 3733202924, ["emote:legendary"] = 3733203016,
	["hat:common"] = 3733203035, ["hat:rare"] = 3733203049, ["hat:epic"] = 3733203160, ["hat:legendary"] = 3733203176,
	["kill:common"] = 3733203199, ["kill:rare"] = 3733203280, ["kill:epic"] = 3733203293,
	["kill:legendary"] = 3733203306, ["skin:common"] = 3733203365, ["skin:rare"] = 3733203381,
	["skin:epic"] = 3733203397, ["skin:legendary"] = 3733203496, ["title:common"] = 3733203514,
	["title:rare"] = 3733203535, ["title:epic"] = 3733203612, ["title:legendary"] = 3733203626,
	["wrap:common"] = 3733203644, ["wrap:rare"] = 3733203745, ["wrap:epic"] = 3733203760,
	["wrap:legendary"] = 3733203775,
	-- (the owner's deals, per rarity and discount)
	["deal:common:20"] = 3733203865, ["deal:common:25"] = 3733203886, ["deal:rare:25"] = 3733203909,
	["deal:rare:30"] = 3733204023, ["deal:epic:30"] = 3733204043, ["deal:epic:35"] = 3733204068,
	["deal:legendary:35"] = 3733204169, ["deal:legendary:40"] = 3733204190,
	-- (the Robux weapons)
	["weapon:minigun"] = 3733204206, ["weapon:laser"] = 3733204303, ["weapon:chicken"] = 3733204322,
	["weapon:akimbo"] = 3733204340,
	-- (coin packs)
	["coins:coins_1200"] = 3733204424, ["coins:coins_6500"] = 3733204431, ["coins:coins_28000"] = 3733204444,
	["coins:coins_70000"] = 3733204487,
	-- (the weapon bundles and VIP as a gift: made 19 Nov 2026, prompted only while their switches are on)
	wbundle_assault = 3733671860, wbundle_explosives = 3733671907, vipgift = 3733671921,
} :: { [string]: number }
Shop.byProduct = {} :: { [number]: string } -- product id -> offer id, or a tier ("wrap:epic")
for key, pid in Shop.PRODUCTS do
	if type(pid) == "number" and pid > 0 then
		Shop.byProduct[pid] = key
		local o = Shop.byId[key]
		if o then o.productId = pid end
	end
end
-- a container's product for n at once: one ("crate"), or the five and ten packs ("crate:5"); nil for another count
-- a container's family for its model ("spray" for every Spray Can), and a copy of it painted in its set's colour (20 Nov)
function Shop.boxBase(id: string): string
	return if LootTable and type(LootTable.base) == "function" then LootTable.base(id) else id
end
function Shop.boxTint(m: Instance, id: string)
	if LootTable and type(LootTable.tint) == "function" then LootTable.tint(m, id) end
end
function Shop.containerProduct(cid: string, n: number?): number?
	local k = math.floor(n or 1)
	local pid = Shop.PRODUCTS[if k > 1 then cid .. ":" .. k else cid]
	return if type(pid) == "number" and pid > 0 then pid else nil
end
-- the developer product an offer is bought with (nil: not for sale for Robux yet). missing = for a skin set, how
-- many of its skins the buyer still lacks (fewer than all: the "complete the set" product for that count)
function Shop.productFor(o: Offer, missing: number?): number?
	if o.type == "weapon" or o.type == "coins" then -- ("weapon:minigun", "coins:coins_1200")
		local wp = Shop.PRODUCTS[o.id]
		return if type(wp) == "number" and wp > 0 then wp else nil
	end
	if o.type == "single" then
		local pid = Shop.PRODUCTS[(o.kind :: string) .. ":" .. o.rarity]
		return if type(pid) == "number" and pid > 0 then pid else nil
	end
	local key = o.id
	if o.set and missing and missing > 0 and missing < #(o.items :: { Item }) then key = o.id .. ":" .. missing end
	local pid = Shop.PRODUCTS[key]
	return if type(pid) == "number" and pid > 0 then pid else nil
end

return Shop
