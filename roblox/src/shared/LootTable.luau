--!strict
-- the loot: what is in a Crate, a Duffel Bag and a Spray Can, the rarities and their weights, and the odds a player
-- sees before every open. the web game's own tables (shared/cosmetics.js: RARITY, CONTAINERS, rollPick), read by the
-- server (Loot.luau rolls with them) and by the clients (the shop shows the odds, Opening draws the cards).
--   crate: weapon skins (web COSMETICS.model + SKINS_2). a skin rolls only once its model is in the place
--          (ReplicatedStorage.JankfireSkins.<id>); until then the crate is "coming soon".
--   bag:   the Duffel Bag: hats (live), effects, kill effects, grapples (not on Roblox yet).
--   spray: the Spray Can (the web game's Box): wraps (live), sprays (not on Roblox yet).
-- free items are owned by everyone and never roll; `ach` items (achievement rewards) are never in a container.
-- a roll never gives what you already own: pick a rarity by weight among the rarities you still have something left
-- in, then any item of that rarity you don't own (web rollPick). so the odds below depend on what you own.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = script.Parent
local Roster = require(Shared:WaitForChild("Roster"))
local GunHats = require(Shared:WaitForChild("GunHats"))

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

export type Item = { type: string, id: string, name: string, rarity: string, weapon: string? }

L.TYPE_NAMES = { wrap = "Wrap", hat = "Hat", skin = "Skin", effect = "Effect", kill = "Kill Effect", grapple = "Grapple", spray = "Spray" }

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

-- ------------------------------------------------------------------ the catalog: every item that can exist, by type
-- (only what is on Roblox: wraps from Roster, hats from GunHatData, skins whose model is in the place)
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
		return if w then { type = t, id = id, name = w.name, rarity = w.rarity } else nil
	elseif t == "hat" then
		local h = if id ~= "none" then GunHats.HATS[id] else nil
		return if h then { type = t, id = id, name = h.name, rarity = h.rarity } else nil
	elseif t == "skin" then
		local s = L.SKINS[id]
		return if s then { type = t, id = id, name = s[1], rarity = s[2], weapon = s[3] } else nil
	end
	return nil
end

-- free things everyone owns (and things that don't exist: never owned)
function L.isFree(t: string, id: string): boolean
	local i = L.info(t, id)
	return i ~= nil and i.rarity == "free"
end

-- everything that can come out of this container today (non-free), in a fixed order
function L.pool(kind: string): { Item }
	local out = {}
	local c = L.CONTAINERS[kind]
	if not c then return out end
	for _, t in c.types do
		if t == "wrap" then
			for _, w in Roster.wraps do
				if w.rarity ~= "free" and L.RARITY[w.rarity] then table.insert(out, { type = t, id = w.id, name = w.name, rarity = w.rarity }) end
			end
		elseif t == "hat" then
			for _, id in GunHats.ORDER do
				local h = GunHats.HATS[id]
				if h and id ~= "none" and h.rarity ~= "free" and L.RARITY[h.rarity] then table.insert(out, { type = t, id = id, name = h.name, rarity = h.rarity }) end
			end
		elseif t == "skin" then
			local live = skinsLive()
			local ids = {}
			for id in L.SKINS do if live[id] then table.insert(ids, id) end end
			table.sort(ids)
			for _, id in ids do
				local s = L.SKINS[id]
				table.insert(out, { type = t, id = id, name = s[1], rarity = s[2], weapon = s[3] })
			end
		end
	end
	return out
end

-- "coming soon": nothing of this kind is on Roblox yet
function L.soon(kind: string): boolean
	return #L.pool(kind) == 0
end

-- owned: { [type]: { [id]: true } } (nil = owns nothing). returns the rarities you can still get with their chances
-- (0..1, adding up to 1), each item's own chance, and how many you have left. the shop shows this before every open
export type Odds = { rarities: { { rarity: string, name: string, chance: number, left: number, total: number } },
	items: { { type: string, id: string, name: string, rarity: string, chance: number, owned: boolean } },
	left: number, total: number, soon: boolean, empty: boolean }
function L.odds(kind: string, owned: { [string]: { [string]: boolean } }?): Odds
	local pool = L.pool(kind)
	local left, total = {}, {}
	local function has(i: Item): boolean
		local s = owned and owned[i.type]
		return s ~= nil and s[i.id] == true
	end
	for _, i in pool do
		total[i.rarity] = (total[i.rarity] or 0) + 1
		if not has(i) then left[i.rarity] = (left[i.rarity] or 0) + 1 end
	end
	local sum = 0
	for r, n in left do if n > 0 then sum += L.RARITY[r].weight end end
	local out: Odds = { rarities = {}, items = {}, left = 0, total = #pool, soon = #pool == 0, empty = sum == 0 }
	for _, r in L.RARITY_ORDER do
		if total[r] then
			local n = left[r] or 0
			out.left += n
			table.insert(out.rarities, { rarity = r, name = L.RARITY[r].name, chance = if n > 0 and sum > 0 then L.RARITY[r].weight / sum else 0, left = n, total = total[r] })
		end
	end
	local rc = {}
	for _, x in out.rarities do rc[x.rarity] = x end
	for _, i in pool do
		local o = has(i)
		local x = rc[i.rarity]
		table.insert(out.items, { type = i.type, id = i.id, name = i.name, rarity = i.rarity, owned = o,
			chance = if o or not x or x.left == 0 then 0 else x.chance / x.left })
	end
	return out
end

-- ------------------------------------------------------------------ the roll (the server's; pure, so a sample can be run anywhere)
-- web rollPick: a rarity by weight among the rarities you still have something left in, then any unowned item of it.
-- returns nil, "soon" (nothing of this kind on Roblox yet) or nil, "empty" (you own all of it)
function L.roll(kind: string, owned: { [string]: { [string]: boolean } }?, rng: Random): (Item?, string?)
	local pool = L.pool(kind)
	if #pool == 0 then return nil, "soon" end
	local left: { [string]: { Item } } = {}
	for _, i in pool do
		local s = owned and owned[i.type]
		if not (s and s[i.id]) then
			left[i.rarity] = left[i.rarity] or {}
			table.insert(left[i.rarity], i)
		end
	end
	local total = 0
	for _, r in L.RARITY_ORDER do if left[r] then total += L.RARITY[r].weight end end
	if total <= 0 then return nil, "empty" end
	local x = rng:NextNumber() * total
	local pick: string? = nil
	for _, r in L.RARITY_ORDER do
		if left[r] then
			pick = pick or r -- (the first one with something left, as the web game falls back to)
			x -= L.RARITY[r].weight
			if x <= 0 then pick = r; break end
		end
	end
	local list = left[pick :: string]
	return list[rng:NextInteger(1, #list)], nil
end

-- the reel the opening spins: n cards drawn from the whole container by the same rarity weights (owned things too: it
-- shows what is inside), with the prize at `stop`. returns the cards and stop
L.STRIP = 52
function L.strip(kind: string, prize: Item, rng: Random): ({ Item }, number)
	local pool = L.pool(kind)
	local by: { [string]: { Item } } = {}
	for _, i in pool do by[i.rarity] = by[i.rarity] or {}; table.insert(by[i.rarity], i) end
	local total = 0
	for _, r in L.RARITY_ORDER do if by[r] then total += L.RARITY[r].weight end end
	local stop = rng:NextInteger(L.STRIP - 8, L.STRIP - 5)
	local out = {}
	for n = 1, L.STRIP do
		if n == stop or total <= 0 then
			table.insert(out, prize)
		else
			local x = rng:NextNumber() * total
			local pick = "common"
			for _, r in L.RARITY_ORDER do
				if by[r] then pick = r; x -= L.RARITY[r].weight; if x <= 0 then break end end
			end
			local list = by[pick]
			table.insert(out, list[rng:NextInteger(1, #list)])
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
