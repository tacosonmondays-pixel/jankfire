--!strict
-- the loot: what is in a Crate, a Duffel Bag and a Spray Can, the rarities and their weights, and the odds a player
-- sees before every open. the web game's own tables (shared/cosmetics.js: RARITY, CONTAINERS, rollPick), read by the
-- server (Loot.luau rolls with them) and by the clients (the shop shows the odds, Opening draws the cards).
--   crate: weapon skins (web COSMETICS.model + SKINS_2). a skin rolls only once its model is in the place
--          (ReplicatedStorage.JankfireSkins.<id>); until then the crate is "coming soon".
--   bag:   the Duffel Bag: hats (live), effects, kill effects, grapples (not on Roblox yet).
--   spray: the Spray Can (the web game's Box): wraps (live), sprays (not on Roblox yet).
-- free items are owned by everyone and never roll; `ach` items (achievement rewards) are never in a container.
-- a wrap or a hat is won for ONE gun (the owner, 16 Nov): what you own is (cosmetic, gun) pairs, "galaxy@ar". a roll
-- never gives a pair you already own: a rarity by weight among the rarities you still have a pair left in, a gun evenly
-- among the guns with something of it left, then any of those (web rollPick, on pairs). so the odds depend on what you own.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = script.Parent
local Roster = require(Shared:WaitForChild("Roster"))
local GunHats = require(Shared:WaitForChild("GunHats"))
local GunHatData = require(Shared:WaitForChild("GunHatData")) :: any

local L = {}

L.KINDS = { "crate", "bag", "spray" }

-- the web game's weights; the colours are ours (muted, the serious look), in the web game's order of hues
L.RARITY_ORDER = { "common", "rare", "epic", "legendary" }
L.RARITY = {
	free = { name = "Free", weight = 0, color = Color3.fromRGB(150, 156, 166) },
	common = { name = "Common", weight = 55, color = Color3.fromRGB(122, 178, 104) },
	rare = { name = "Rare", weight = 28, color = Color3.fromRGB(78, 150, 226) },
	epic = { name = "Epic", weight = 13, color = Color3.fromRGB(162, 108, 226) },
	legendary = { name = "Legendary", weight = 4, color = Color3.fromRGB(240, 178, 52) },
}

export type Item = { type: string, id: string, key: string, name: string, rarity: string, weapon: string? }

L.TYPE_NAMES = { wrap = "Wrap", hat = "Hat", skin = "Skin", effect = "Effect", kill = "Kill Effect", grapple = "Grapple", spray = "Spray",
	border = "Card Border", banner = "Card Banner", title = "Card Title" }

-- ------------------------------------------------------------------ other sessions' gun-less cosmetics (a hook)
-- the player cards' looks (ReplicatedStorage.Jankfire.CardStyles, the player-profiles session's): if that module is in
-- the place, its TYPES (e.g. border / banner / title) are owned like skins (key = the bare id, not on a gun) and roll
-- from its CONTAINER as one more "gun" (the reel shows PLAYER CARD). its shape: TYPES = { t }, info(t, id) ->
-- { name, rarity }?, ORDER[t] = { ids }, CONTAINER = "bag", optional picture(t, id, frame) for the reel's card
local cardMod: any = false
function L.cardStyles(): any
	if cardMod == false then
		cardMod = nil
		local m = Shared:FindFirstChild("CardStyles")
		if m and m:IsA("ModuleScript") then
			local ok, c = pcall(require, m)
			if ok and type(c) == "table" and type(c.TYPES) == "table" and type(c.info) == "function" then cardMod = c end
		end
	end
	return cardMod
end
local function isCardType(t: any): boolean
	local c = L.cardStyles()
	return c ~= nil and type(t) == "string" and table.find(c.TYPES, t) ~= nil
end
-- a type you own without a gun: skins (already one gun's) and the card looks
function L.gunless(t: string): boolean
	return t == "skin" or isCardType(t)
end
-- every type that can be owned (Loot.luau keeps a list per type)
function L.ownTypes(): { string }
	local out = { "wrap", "hat", "skin" }
	local c = L.cardStyles()
	if c then for _, t in c.TYPES do if not table.find(out, t) then table.insert(out, t) end end end
	return out
end

L.CONTAINERS = {
	crate = { name = "Crate", plural = "Crates", desc = "weapon skins", types = { "skin" } },
	bag = { name = "Duffel Bag", plural = "Duffel Bags", desc = "hats, effects, kill effects and grapples", types = { "hat", "effect", "kill", "grapple" } },
	spray = { name = "Spray Can", plural = "Spray Cans", desc = "wraps and sprays", types = { "wrap", "spray" } },
}

-- every weapon skin of the web game: id = { name, rarity, weapon } (COSMETICS.model, SKINS_2, STREAK_SKINS; the free
-- Kitchen Knife and the achievement-only Golden Sniper are left out: they never roll)
L.SKINS = {
	knife_bowie = { "Bowie", "common", "knife" }, knife_cleaver = { "Cleaver", "rare", "knife" },
	knife_switch = { "Switchblade", "rare", "knife" }, knife_karambit = { "Karambit", "epic", "knife" },
	knife_butterfly = { "Butterfly", "legendary", "knife" }, knife_spoon = { "Spoon", "epic", "knife" },
	slapper_foam = { "Foam Finger", "rare", "slapper" }, slapper_paw = { "Bear Paw", "epic", "slapper" },
	bread_croissant = { "Croissant Club", "epic", "bread" }, ar_toy = { "Toy Blaster", "common", "ar" },
	ar_bullpup = { "Bullpup", "rare", "ar" }, smg_uzi = { "Pocket Uzi", "rare", "smg" },
	shotgun_double = { "Double Barrel", "rare", "shotgun" }, minigun_gatling = { "Old Gatling", "epic", "minigun" },
	sniper_musket = { "Musket", "legendary", "sniper" }, revolver_flint = { "Flintlock", "epic", "revolver" },
	chicken_turkey = { "Turkey Launcher", "rare", "chicken" }, bowling_cannon = { "Hand Cannon", "epic", "bowling" },
	nailgun_staple = { "Office Stapler", "rare", "nailgun" }, tennis_machine = { "Ball Machine", "epic", "tennis" },
	cart_basket = { "Basket Case", "rare", "cart" }, banana_bunch = { "Bunch Blaster", "rare", "banana" },
	bow_compound = { "Compound Bow", "rare", "bow" }, cig_cigar = { "Fat Cigar", "rare", "cig" },
	blower_dryer = { "Hair Dryer", "epic", "blower" }, popper_bottle = { "Champagne", "epic", "popper" },
	reverse_skip = { "Skip Card", "common", "reverse" }, snowball_ice = { "Ice Cube", "rare", "snowball" },
	slipper_croc = { "Croc", "epic", "slipper" }, scythe_reaper = { "Reaper", "legendary", "scythe" },
	katana_bokken = { "Bokken", "common", "katana" }, marbles_gumball = { "Gumball Machine", "rare", "marbles" },
	bloodcross_shadow = { "Shadow Cross", "epic", "bloodcross" }, redline_hotrod = { "Hot Rod", "epic", "redline" },
	katana_shirasaya = { "Shirasaya", "rare", "katana" }, scales_kangaroo = { "Kangaroo Court", "rare", "scales" },
	shredder_chipper = { "Wood Chipper", "epic", "shredder" }, lasso_hose = { "Garden Hose", "rare", "lasso" },
	laser_cattoy = { "Cat Laser", "rare", "laser" }, burst_ticket = { "Take A Number", "epic", "burst" },
	lmg_leaf = { "Leaf Shredder", "epic", "lmg" }, dmr_pen = { "Fountain Pen", "rare", "dmr" },
	lever_capgun = { "Cap Gun", "common", "lever" }, autoshot_trimmer = { "Weed Whacker", "rare", "autoshot" },
	pistol_calc = { "Calculator", "common", "pistol" }, akimbo_walkie = { "Walkie Talkies", "rare", "akimbo" },
	sawnoff_pepper = { "Pepper Mills", "epic", "sawnoff" }, cards_business = { "Business Cards", "common", "cards" },
	water_flower = { "Squirt Flower", "rare", "water" }, water_hose = { "Hose Nozzle", "common", "water" },
	taser_zapper = { "Bug Zapper", "rare", "taser" }, remote_pad = { "Game Pad", "epic", "remote" },
	ar_keytar = { "Keytar", "legendary", "ar" }, smg_label = { "Label Maker", "rare", "smg" },
	shotgun_umbrella = { "Brolly", "epic", "shotgun" }, sniper_cue = { "Pool Cue", "epic", "sniper" },
	revolver_drill = { "Cordless Drill", "rare", "revolver" }, katana_baguette = { "Baguette Katana", "rare", "katana" },
	katana_neon = { "Neon Tube", "legendary", "katana" }, knife_ladle = { "Ladle", "common", "knife" },
	knife_pizza = { "Pizza Cutter", "common", "knife" }, knife_keycard = { "Keycard", "epic", "knife" },
	knife_fish = { "Frozen Fish", "rare", "knife" }, bread_sliced = { "Sliced Loaf", "common", "bread" },
	slipper_flipflop = { "Flip-Flop", "common", "slipper" },
	wreck_bowling = { "Bowling Ball", "common", "wreckingball" }, wreck_meatball = { "Meatball", "rare", "wreckingball" },
	wreck_disco = { "Disco Ball", "epic", "wreckingball" }, duck_flamingo = { "Pool Flamingo", "rare", "giantduck" },
	duck_robot = { "Robo Duck", "epic", "giantduck" }, duck_gold = { "Golden Duck", "legendary", "giantduck" },
	strike_pigeon = { "Pigeon Raid", "common", "chickenstrike" }, strike_drone = { "Drone Strike", "epic", "chickenstrike" },
	moon_heelys = { "Heelys", "common", "moonboots" }, moon_rocket = { "Rocket Sneakers", "rare", "moonboots" },
	moon_clown = { "Clown Shoes", "epic", "moonboots" }, spin_halo = { "Halo", "rare", "spinbot" },
	spin_aura = { "Anime Aura", "legendary", "spinbot" }, sat_pizza = { "Pizza Dish", "rare", "satellite" },
	sat_blimp = { "CCTV Blimp", "epic", "satellite" },
}

-- the skin sets' skins (Shared.SkinSets: the guns session owns their names, rarities and tiers) join the list above, so a
-- crate rolls them like any skin once their model is in JankfireSkins (16 Nov, the owner: "can the weapon skins, not all
-- of them but a couple, be like sets?"). a skin already listed keeps its row
local skinSets: any = nil
do
	local m = script.Parent:FindFirstChild("SkinSets")
	local ok, S = false, nil
	if m and m:IsA("ModuleScript") then ok, S = pcall(require, m) end
	if ok and type(S) == "table" then
		skinSets = S
		for id, row in (if type(S.SKINS) == "table" then S.SKINS else {}) do
			if L.SKINS[id] == nil and type(row) == "table" and type(row[1]) == "string" and type(row[2]) == "string" and type(row[3]) == "string" then
				L.SKINS[id] = { row[1], row[2], row[3] }
			end
		end
	end
end
-- a weapon skin's tier (SkinSets.TIER: basic = small changes to the base gun, mid = a new model, high = a remodel with
-- its own effects): "basic" / "mid" / "high" and its name, or nil (no tier, or no SkinSets in the place)
function L.tier(id: string): (string?, string?)
	local t = skinSets and type(skinSets.TIER) == "table" and skinSets.TIER[id] or nil
	if type(t) ~= "string" then return nil, nil end
	local e = type(skinSets.TIERS) == "table" and skinSets.TIERS[t] or nil
	return t, if type(e) == "table" and type(e.name) == "string" then e.name else t
end
-- a high-tier skin's effects spec (SkinSets.FX, played by the client's Fx.skinIdle), or nil
function L.skinFx(id: string): any
	return skinSets and type(skinSets.FX) == "table" and skinSets.FX[id] or nil
end

-- ------------------------------------------------------------------ the catalog: every item that can exist, by type
-- (only what is on Roblox: wraps from Roster, hats from GunHatData, skins whose model is in the place)
-- ---------------------------------------------------------------- VIP only
-- the owner, 16 Nov: the Ducky set comes with the VIP game pass (the shop session's), never from a container. a VIP
-- thing is in no container and no odds; only Loot.grant gives it (the shop's VIP offer), and a VIP wrap or hat is worn
-- on every gun (Loot.owns). it's VIP when it's listed here, or its own data says vip = true (a wrap in Roster, a hat in
-- GunHats, a card look in its module's info), or it's a skin of a SkinSets set marked vip = true (or the Ducky set)
-- (the shop session's ids, 16 Nov: the Ducky wrap, the VIP duck hat, the Ducky border, the VIP title)
L.VIP_ONLY = { skin = {}, wrap = { ducky = true }, hat = { vipduck = true }, border = { ducky = true }, title = { vip = true } } :: { [string]: { [string]: boolean } }
function L.vipOnly(t: string, id: string): boolean
	local list = L.VIP_ONLY[t]
	if list and list[id] then return true end
	if t == "wrap" then
		local w = Roster.wrapById[id]
		return w ~= nil and (w :: any).vip == true
	elseif t == "hat" then
		local h = GunHats.HATS[id]
		return h ~= nil and (h :: any).vip == true
	elseif t == "skin" then
		local S = skinSets
		local row = S and type(S.SKINS) == "table" and S.SKINS[id] or nil
		local set = if type(row) == "table" then row[4] else nil
		local info = if set and type(S.SETS) == "table" then S.SETS[set] else nil
		return set == "set_ducky" or (type(info) == "table" and info.vip == true)
	elseif isCardType(t) then
		local cm = L.cardStyles()
		if not cm or type(cm.info) ~= "function" then return false end
		local ok, c = pcall(cm.info, t, id)
		return ok and type(c) == "table" and c.vip == true
	end
	return false
end

local function skinsLive(): { [string]: boolean }
	local lib = ReplicatedStorage:FindFirstChild("JankfireSkins")
	local out = {}
	if lib then for _, m in lib:GetChildren() do out[m.Name] = true end end
	return out
end

-- the item's row, or nil if there is no such thing (ids come off the network: only plain lookups here)
function L.info(t: any, id: any): Item?
	if type(t) ~= "string" or type(id) ~= "string" then return nil end
	if t == "wrap" then
		local w = Roster.wrapById[id]
		return if w then { type = t, id = id, key = id, name = w.name, rarity = w.rarity } else nil
	elseif t == "hat" then
		local h = if id ~= "none" then GunHats.HATS[id] else nil
		return if h then { type = t, id = id, key = id, name = h.name, rarity = h.rarity } else nil
	elseif t == "skin" then
		local s = L.SKINS[id]
		return if s then { type = t, id = id, key = id, name = s[1], rarity = s[2], weapon = s[3] } else nil
	elseif isCardType(t) then
		local ok, c = pcall(L.cardStyles().info, t, id)
		if ok and type(c) == "table" and type(c.name) == "string" and type(c.rarity) == "string" then
			return { type = t, id = id, key = id, name = c.name, rarity = c.rarity }
		end
	end
	return nil
end

-- free things everyone owns, on every gun (and things that don't exist: never owned)
function L.isFree(t: string, id: string): boolean
	local i = L.info(t, id)
	return i ~= nil and i.rarity == "free"
end

-- ------------------------------------------------------------------ one gun at a time
-- (owner, 16 Nov 2026: "spray cans should give you a wrap for only one gun at a time! some with the charms/hats"): a
-- wrap or a hat is owned for ONE weapon, a pair written "<id>@<weapon>" ("galaxy@ar", "crown@katana"). a weapon skin
-- already belongs to one weapon: its key is its own id. the weapons are the live ones that take paint (Roster: live, not
-- an item on G); a hat only goes on a weapon with a seat for it (GunHatData.SPOTS)
function L.key(t: string, id: string, weapon: string?): string
	if L.gunless(t) or not weapon then return id end
	return id .. "@" .. weapon
end
-- "<id>@<weapon>" -> id, weapon (a bare id -> id, nil)
function L.split(key: any): (string?, string?)
	if type(key) ~= "string" then return nil, nil end
	local id, w = string.match(key, "^([%w_]+)@([%w_]+)$")
	if id then return id, w end
	return key, nil
end
function L.weapons(t: string): { string }
	local out = {}
	for _, e in Roster.list do
		if e.live and e.slot ~= "utility" and (t ~= "hat" or (GunHatData.SPOTS ~= nil and GunHatData.SPOTS[e.id] ~= nil)) then
			table.insert(out, e.id)
		end
	end
	return out
end
function L.takes(t: string, weapon: any): boolean
	return type(weapon) == "string" and table.find(L.weapons(t), weapon) ~= nil
end
-- a pair from the network or a save: its row with the weapon, or nil if there is no such pair
function L.pairInfo(t: any, key: any): Item?
	if type(t) == "string" and L.gunless(t) then return L.info(t, key) end
	local id, w = L.split(key)
	local i = L.info(t, id)
	if not i or not w or not L.takes(t, w) then return nil end
	i.weapon, i.key = w, (id :: string) .. "@" .. w
	return i
end

-- the cosmetics that can come out of this container today (non-free), one row each, in a fixed order
function L.cosmetics(kind: string): { Item }
	local out = {}
	local c = L.CONTAINERS[kind]
	if not c then return out end
	for _, t in c.types do
		if t == "wrap" then
			for _, w in Roster.wraps do
				if w.rarity ~= "free" and L.RARITY[w.rarity] and not L.vipOnly(t, w.id) then table.insert(out, { type = t, id = w.id, key = w.id, name = w.name, rarity = w.rarity }) end
			end
		elseif t == "hat" then
			for _, id in GunHats.ORDER do
				local h = GunHats.HATS[id]
				if h and id ~= "none" and h.rarity ~= "free" and L.RARITY[h.rarity] and not L.vipOnly(t, id) then table.insert(out, { type = t, id = id, key = id, name = h.name, rarity = h.rarity }) end
			end
		elseif t == "skin" then
			local live = skinsLive()
			local ids = {}
			for id in L.SKINS do if live[id] and not L.vipOnly(t, id) then table.insert(ids, id) end end
			table.sort(ids)
			for _, id in ids do
				local s = L.SKINS[id]
				table.insert(out, { type = t, id = id, key = id, name = s[1], rarity = s[2], weapon = s[3] })
			end
		end
	end
	-- (the card looks, in the container their module names)
	local cm = L.cardStyles()
	if cm and cm.CONTAINER == kind and type(cm.ORDER) == "table" then
		for _, t in cm.TYPES do
			for _, id in (cm.ORDER[t] or {}) do
				local i = L.info(t, id)
				if i and i.rarity ~= "free" and L.RARITY[i.rarity] and not L.vipOnly(t, id) then table.insert(out, i) end
			end
		end
	end
	return out
end
-- the guns a cosmetic can be won for
-- (a card look is gun-less: it rolls as one more "gun", CARD, so a bag lands on it about as often as on one gun)
local CARD = "card"
local function gunsOf(i: Item): { string }
	if i.type == "skin" then return { i.weapon :: string } end
	if isCardType(i.type) then return { CARD } end
	return L.weapons(i.type)
end
local function pairOf(i: Item, w: string): Item
	local gun = if w == CARD then nil else w
	return { type = i.type, id = i.id, name = i.name, rarity = i.rarity, weapon = gun, key = L.key(i.type, i.id, gun) }
end

-- every (cosmetic, gun) pair that can come out of this container today
function L.pool(kind: string): { Item }
	local out = {}
	for _, i in L.cosmetics(kind) do
		for _, w in gunsOf(i) do table.insert(out, pairOf(i, w)) end
	end
	return out
end

-- "coming soon": nothing of this kind is on Roblox yet
function L.soon(kind: string): boolean
	return #L.cosmetics(kind) == 0
end

-- what is left to win, by rarity: for each rarity, the guns that still have something of it and per gun the cosmetics
-- left for it. owned: { [type]: { [key]: true } }
type Left = { [string]: { guns: { string }, by: { [string]: { Item } }, n: number, total: number } }
local function leftOf(kind: string, owned: { [string]: { [string]: boolean } }?): Left
	local out: Left = {}
	for _, i in L.cosmetics(kind) do
		local r = out[i.rarity]
		if not r then r = { guns = {}, by = {}, n = 0, total = 0 }; out[i.rarity] = r end
		local s = owned and owned[i.type]
		for _, w in gunsOf(i) do
			r.total += 1
			if not (s and s[L.key(i.type, i.id, w)]) then
				if not r.by[w] then r.by[w] = {}; table.insert(r.guns, w) end
				table.insert(r.by[w], i)
				r.n += 1
			end
		end
	end
	return out
end

-- the odds, before every open (the shop shows them): the rarities you can still get with their chances (0..1, adding
-- up to 1) and how many PAIRS are left of each; each cosmetic's chance (over all the guns it can still land on); how
-- many guns are in play (the gun is picked evenly among the guns that still have something of the rolled rarity).
-- owned: { [type]: { [key]: true } } (nil = owns nothing)
export type Odds = { rarities: { { rarity: string, name: string, chance: number, left: number, total: number } },
	items: { { type: string, id: string, name: string, rarity: string, chance: number, owned: boolean, ownedOn: number, guns: number } },
	left: number, total: number, weapons: number, soon: boolean, empty: boolean }
function L.odds(kind: string, owned: { [string]: { [string]: boolean } }?): Odds
	local cos = L.cosmetics(kind)
	local left = leftOf(kind, owned)
	local sum = 0
	for r, x in left do if x.n > 0 then sum += L.RARITY[r].weight end end
	local guns = 0
	for _, i in cos do guns = math.max(guns, #gunsOf(i)) end
	local out: Odds = { rarities = {}, items = {}, left = 0, total = 0, weapons = guns, soon = #cos == 0, empty = sum == 0 }
	local pr = {}
	for _, r in L.RARITY_ORDER do
		local x = left[r]
		if x then
			out.left += x.n; out.total += x.total
			pr[r] = if x.n > 0 and sum > 0 then L.RARITY[r].weight / sum else 0
			table.insert(out.rarities, { rarity = r, name = L.RARITY[r].name, chance = pr[r], left = x.n, total = x.total })
		end
	end
	for _, i in cos do
		local x = left[i.rarity]
		local s = owned and owned[i.type]
		local chance, on, gs = 0, 0, gunsOf(i)
		for _, w in gs do
			if s and s[L.key(i.type, i.id, w)] then on += 1
			elseif x and #x.guns > 0 and x.by[w] then chance += (pr[i.rarity] or 0) / #x.guns / #x.by[w] end
		end
		table.insert(out.items, { type = i.type, id = i.id, name = i.name, rarity = i.rarity, chance = chance,
			owned = on == #gs, ownedOn = on, guns = #gs })
	end
	return out
end

-- ------------------------------------------------------------------ the roll (the server's; pure, so a sample can be run anywhere)
-- the web game's rollPick, on pairs: a rarity by weight among the rarities you still have a pair left in; a gun, evenly,
-- among the guns that still have something of that rarity; then any cosmetic of that rarity you don't own for that gun.
-- so a gun never comes up for nothing, and you never get a pair you already have. returns the pair, or nil, "soon"
-- (nothing of this kind on Roblox yet) / nil, "empty" (you own every pair)
function L.roll(kind: string, owned: { [string]: { [string]: boolean } }?, rng: Random): (Item?, string?)
	if L.soon(kind) then return nil, "soon" end
	local left = leftOf(kind, owned)
	local total = 0
	for _, r in L.RARITY_ORDER do if left[r] and left[r].n > 0 then total += L.RARITY[r].weight end end
	if total <= 0 then return nil, "empty" end
	local x = rng:NextNumber() * total
	local pick: string? = nil
	for _, r in L.RARITY_ORDER do
		if left[r] and left[r].n > 0 then
			pick = pick or r -- (the first one with something left, as the web game falls back to)
			x -= L.RARITY[r].weight
			if x <= 0 then pick = r; break end
		end
	end
	local lr = left[pick :: string]
	local w = lr.guns[rng:NextInteger(1, #lr.guns)]
	local list = lr.by[w]
	return pairOf(list[rng:NextInteger(1, #list)], w), nil
end

-- the reel the opening spins: n cards drawn from the whole container by the same rarity weights (owned pairs too: it
-- shows what is inside), each on a gun, with the prize at `stop`. returns the cards and stop
L.STRIP = 52
L.STRIP_QUICK = 26 -- (a batch's reels are short: ten of them run one after another)
function L.strip(kind: string, prize: Item, rng: Random, len: number?): ({ Item }, number)
	local N = len or L.STRIP
	local by: { [string]: { Item } } = {}
	for _, i in L.cosmetics(kind) do by[i.rarity] = by[i.rarity] or {}; table.insert(by[i.rarity], i) end
	local total = 0
	for _, r in L.RARITY_ORDER do if by[r] then total += L.RARITY[r].weight end end
	local stop = rng:NextInteger(N - 8, N - 5)
	local out = {}
	for n = 1, N do
		if n == stop or total <= 0 then
			table.insert(out, prize)
		else
			local x = rng:NextNumber() * total
			local pick = "common"
			for _, r in L.RARITY_ORDER do
				if by[r] then pick = r; x -= L.RARITY[r].weight; if x <= 0 then break end end
			end
			local list = by[pick]
			local i = list[rng:NextInteger(1, #list)]
			local gs = gunsOf(i)
			table.insert(out, pairOf(i, gs[rng:NextInteger(1, #gs)]))
		end
	end
	return out, stop
end

-- the odds as one line ("Common 55% · Rare 28% · Epic 13% · Legendary 4%")
function L.oddsLine(o: Odds): string
	local parts = {}
	for _, x in o.rarities do
		if x.chance > 0 then
			local pct = x.chance * 100
			table.insert(parts, ("%s %s%%"):format(x.name, if pct >= 9.95 or pct == math.floor(pct) then ("%d"):format(math.floor(pct + 0.5)) else ("%.1f"):format(pct)))
		end
	end
	return table.concat(parts, "  ·  ")
end

return L
