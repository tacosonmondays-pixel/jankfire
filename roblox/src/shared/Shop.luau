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
-- ShopReceipts doesn't even take receipts (nothing can be charged)
Shop.ROBUX = Config.LOOT_ROBUX == true
-- the featured rotation turns over every day at 00:00 UTC
Shop.ROTATE = 86400
-- how many single items the daily rotation shows
Shop.DAILY = 6

-- free while we test: Config.LOOT_FREE when the loot module has added it, else free
function Shop.free(): boolean
	if Config.LOOT_FREE ~= nil then return Config.LOOT_FREE == true end
	return true
end

-- ---------------------------------------------------------------- rarities (the opening's muted colours, LootTable.RARITY;
-- the loadout's Roster.RARITY if the loot module isn't there)
Shop.RARITY = if LootTable and LootTable.RARITY then LootTable.RARITY else Roster.RARITY
Shop.RARITY_ORDER = { "free", "common", "rare", "epic", "legendary" }
local RANK = { free = 0, common = 1, rare = 2, epic = 3, legendary = 4, vip = 5 }
function Shop.rank(r: string): number return RANK[r] or 0 end
-- the VIP pack's own rarity colour (the player cards' VIP gold): a VIP thing reads "VIP", not a rarity
Shop.VIP_COLOR = Color3.fromRGB(255, 208, 72)

-- what a single costs, by kind and rarity (Robux; unused while free)
Shop.PRICE = {
	wrap = { free = 0, common = 75, rare = 150, epic = 300, legendary = 600 },
	hat = { free = 0, common = 100, rare = 200, epic = 400, legendary = 750 },
	skin = { free = 0, common = 150, rare = 300, epic = 600, legendary = 1200 },
	border = { free = 0, common = 50, rare = 100, epic = 200, legendary = 400 },
	banner = { free = 0, common = 50, rare = 100, epic = 200, legendary = 400 },
	title = { free = 0, common = 40, rare = 80, epic = 160, legendary = 320 },
	kill = { free = 0, common = 100, rare = 200, epic = 400, legendary = 800 },
	emote = { free = 0, common = 100, rare = 200, epic = 400, legendary = 800 },
}
Shop.KIND_NAMES = { wrap = "Wrap", hat = "Hat", skin = "Skin", border = "Border", banner = "Background", title = "Title",
	kill = "Kill Effect", emote = "Emote" }

-- wraps that never go in a bundle or the rotation: their picture versions broke Roblox's image rules and they are
-- plain colour wraps now (roblox-upload-content-rules), or they are the free ones everyone has
Shop.HELD_BACK = { qr = true, barcode = true, meat = true, organ = true, corp = true, memo = true, jersey = true, default = true }

-- wraps and hats are owned PER WEAPON (the owner, 16 Nov: "spray cans should give you a wrap for only one gun at a
-- time"): an item is (kind, id, weapon), written "<id>@<weapon>" where one string is needed (Shop.key)
export type Item = { kind: string, id: string, weapon: string? }
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
	local lib = ReplicatedStorage:FindFirstChild("JankfireSkins")
	local m = lib and lib:FindFirstChild(id)
	return m ~= nil and m:IsA("Model") and m:GetAttribute("Weapon") == row[3]
end
-- every skin on sale, sorted by id (VIP ones aren't: they come with VIP)
function Shop.liveSkins(): { string }
	local out = {}
	if LootTable and type(LootTable.SKINS) == "table" then
		-- (never a free one: the Classic set is everyone's already. 18 Nov)
		for id, row in LootTable.SKINS do if row[2] ~= "free" and Shop.skinLive(id) and not Shop.vipOnly("skin", id) and not Shop.dailyOnly("skin", id) then table.insert(out, id) end end
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
	{ id = "crate", type = "container", name = "Crate", rarity = "epic", robux = 120, productId = nil,
		blurb = "One weapon skin you don't have yet.", pool = "weapon skins" },
	{ id = "bag", type = "container", name = "Duffel Bag", rarity = "rare", robux = 90, productId = nil,
		blurb = "One hat you don't have yet, for one gun.", pool = "hats" },
	{ id = "spray", type = "container", name = "Spray Can", rarity = "common", robux = 60, productId = nil,
		blurb = "One wrap you don't have yet, for one gun.", pool = "wraps" },
} :: { Offer }
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
-- themed sets that dress several guns: every wrap and hat in a set is for one named weapon. hero = what the big
-- preview and the hub's hologram show: one weapon wearing its wrap and hat from the set. robux is about 60% of the
-- singles' worth (Shop.worth). the line under a bundle's name only says what's in it (Shop.describe)
local function W(id: string, weapon: string): Item return { kind = "wrap", id = id, weapon = weapon } end
local function H(id: string, weapon: string): Item return { kind = "hat", id = id, weapon = weapon } end
Shop.bundles = {
	{ id = "bundle_nightshift", type = "bundle", name = "Night Shift", rarity = "legendary",
		items = { W("hex", "ar"), H("tophat", "ar"), W("carbon", "smg"), W("lchrome", "revolver"), W("matte", "pistol") },
		hero = { weapon = "ar", wrap = "hex", hat = "tophat" } },
	{ id = "bundle_fieldissue", type = "bundle", name = "Field Issue", rarity = "rare",
		items = { W("digital", "sniper"), H("cowboy", "sniper"), W("urban", "ar"), W("desert", "shotgun"), W("arctic", "dmr") },
		hero = { weapon = "sniper", wrap = "digital", hat = "cowboy" } },
	{ id = "bundle_teahouse", type = "bundle", name = "Tea House", rarity = "legendary",
		items = { W("kintsugi", "katana"), H("chef", "katana"), W("seigaiha", "smg"), W("asanoha", "revolver"), W("shibori", "lever"), W("sakura", "burst") },
		hero = { weapon = "katana", wrap = "kintsugi", hat = "chef" } },
	{ id = "bundle_deepspace", type = "bundle", name = "Deep Space", rarity = "legendary",
		items = { W("nebula", "smg"), H("halo", "smg"), W("galaxy", "lmg"), W("aurora", "sniper"), W("blackhole", "redline") },
		hero = { weapon = "smg", wrap = "nebula", hat = "halo" } },
	{ id = "bundle_machineshop", type = "bundle", name = "Machine Shop", rarity = "epic",
		items = { W("damascus", "shotgun"), H("propeller", "shotgun"), W("brushed", "lmg"), W("copper", "sawnoff"), W("titanium", "autoshot") },
		hero = { weapon = "shotgun", wrap = "damascus", hat = "propeller" } },
	{ id = "bundle_quarry", type = "bundle", name = "Quarry", rarity = "legendary",
		items = { W("marble", "redline"), H("crown", "redline"), W("jade", "marbles"), W("granite", "sawnoff"), W("geode", "pistol"), W("opal", "revolver") },
		hero = { weapon = "redline", wrap = "marble", hat = "crown" } },
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
		-- (the VIP set isn't sold: its skins are the VIP pack's)
		if vipSet(sid, s) then continue end
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
	local guns, seen = {}, {}
	for _, it in items do
		if Shop.isCard(it.kind) then n.card += 1 else n[it.kind] = (n[it.kind] or 0) + 1 end
		if it.weapon and not seen[it.weapon] then seen[it.weapon] = true; table.insert(guns, Shop.weaponName(it.weapon)) end
	end
	local parts = {}
	local function add(c: number, one: string, many: string)
		if c == 1 then table.insert(parts, one) elseif c > 1 then table.insert(parts, c .. " " .. many) end
	end
	add(n.skin, "a weapon skin", "weapon skins"); add(n.wrap, "a wrap", "wraps"); add(n.hat, "a hat", "hats")
	add(n.kill or 0, "a kill effect", "kill effects"); add(n.emote or 0, "an emote", "emotes")
	if n.card > 0 and #parts == 0 then return "A border, a background and a title for your player card." end
	local what = joinWords(parts)
	what = string.upper(string.sub(what, 1, 1)) .. string.sub(what, 2)
	return if #guns > 0 then what .. " for the " .. joinWords(guns) .. "." else what .. "."
end

-- ---------------------------------------------------------------- lookups
Shop.byId = {} :: { [string]: Offer }
for _, o in Shop.containers do Shop.byId[o.id] = o end
for _, b in Shop.bundles do
	local worth = 0
	for _, it in b.items :: { Item } do worth += Shop.singlePrice(it.kind, it.id) end
	b.robux = math.floor(worth * 0.6 / 10 + 0.5) * 10 - 1
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
-- what completing a skin set costs when `missing` of its skins are left: that share of the set's price
-- (the whole set: its own price). a developer product per set and count, "set_seraph" / "set_seraph:3" (Shop.PRODUCTS)
function Shop.setPrice(o: Offer, missing: number?): number
	local total = #(o.items :: { Item })
	local m = missing or total
	if m >= total or total == 0 then return o.robux end
	return math.max(0, math.floor(o.robux * m / total / 10 + 0.5) * 10 - 1)
end

-- the singles the rotation can show (wraps and hats that are not free, not held back and not VIP)
Shop.singlesPool = {} :: { Item }
for _, w in Roster.wraps do
	if w.rarity ~= "free" and not Shop.HELD_BACK[w.id] and not Shop.vipOnly("wrap", w.id) and not Shop.dailyOnly("wrap", w.id) then table.insert(Shop.singlesPool, W(w.id)) end
end
for _, id in GunHatData.ORDER do
	local h = GunHatData.HATS[id]
	if id ~= "none" and h and h.rarity ~= "free" and not Shop.vipOnly("hat", id) and not Shop.dailyOnly("hat", id) then table.insert(Shop.singlesPool, H(id)) end
end

-- ---------------------------------------------------------------- VIP (a game pass; Vip.luau decides who has it)
-- the game pass's id once it's made on the Creator Hub (Monetization > Passes); 0 = not made yet. with Shop.ROBUX on
-- and this set, the shop's GET VIP shows Roblox's pass prompt; while the shop is free anyone can claim VIP
Shop.VIP_PASS = 0
Shop.vip = { id = "vip", type = "pass", name = "VIP", rarity = "vip", robux = 399, productId = nil,
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
		-- (in the VIP set's own order: its first is the top piece, the Ducky LMG; then the rarest, then by id)
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
	return n
end

-- ---------------------------------------------------------------- the owner's deals (Deals.luau on the server picks them)
-- the owner, 17 Nov 2026: "I give players 3 special discounts on random skins if you talk to me!". per player per UTC
-- day: three weapon skins on sale (Shop.liveSkins: not VIP, not daily-only, not a concept) that they don't own, at
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
function Shop.day(t: number?): number return math.floor((t or os.time()) / Shop.ROTATE) end
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
-- nothing in this container is on roblox yet
function Shop.soon(containerId: string): boolean
	return LootTable ~= nil and type(LootTable.soon) == "function" and LootTable.soon(containerId) == true
end

-- ---------------------------------------------------------------- developer products (off while Shop.ROBUX is false)
-- when real prices go on: make one developer product per container and bundle on the Creator Hub (Monetization >
-- Developer Products, priced as `robux` above) and paste its id here. singles share one product per kind and rarity
-- ("wrap:epic", "hat:legendary", "skin:epic"): the server remembers which single you asked for
-- (ShopReceipts.server.luau). a skin set has one product for the whole set ("set_seraph") and one per count of skins
-- left to complete it ("set_seraph:1" .. ":4", priced as Shop.setPrice)
Shop.PRODUCTS = {
	-- crate = 0, bag = 0, spray = 0,
	-- bundle_nightshift = 0, ...
	-- set_seraph = 0, ["set_seraph:1"] = 0, ["set_seraph:2"] = 0, ["set_seraph:3"] = 0, ["set_seraph:4"] = 0,
	-- ["wrap:common"] = 0, ["wrap:rare"] = 0, ["wrap:epic"] = 0, ["wrap:legendary"] = 0,
	-- ["hat:common"] = 0, ["hat:rare"] = 0, ["hat:epic"] = 0, ["hat:legendary"] = 0,
	-- ["skin:common"] = 0, ["skin:rare"] = 0, ["skin:epic"] = 0, ["skin:legendary"] = 0,
	-- ["kill:rare"] = 0, ["kill:epic"] = 0, ["kill:legendary"] = 0, ["emote:common"] = 0, ["emote:rare"] = 0, ...
	-- (the owner's deals: one per rarity and discount, priced as Shop.dealPrice)
	-- ["deal:common:20"] = 0, ["deal:common:25"] = 0, ["deal:rare:25"] = 0, ["deal:rare:30"] = 0, ["deal:epic:30"] = 0,
	-- ["deal:epic:35"] = 0, ["deal:legendary:35"] = 0, ["deal:legendary:40"] = 0,
} :: { [string]: number }
Shop.byProduct = {} :: { [number]: string } -- product id -> offer id, or a tier ("wrap:epic")
for key, pid in Shop.PRODUCTS do
	if type(pid) == "number" and pid > 0 then
		Shop.byProduct[pid] = key
		local o = Shop.byId[key]
		if o then o.productId = pid end
	end
end
-- the developer product an offer is bought with (nil: not for sale for Robux yet). missing = for a skin set, how
-- many of its skins the buyer still lacks (fewer than all: the "complete the set" product for that count)
function Shop.productFor(o: Offer, missing: number?): number?
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
