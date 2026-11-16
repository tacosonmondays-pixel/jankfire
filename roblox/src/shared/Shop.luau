--!strict
-- the shop's catalog: everything the SHOP screen sells (ShopUI.luau), what the hub's bundle holograms show, and what
-- the loot server checks before it grants (JankfireRemotes.Loot "buy"). three kinds of offer, each with an id:
--   containers  "crate" / "bag" / "spray": a random item; the odds and pools are the loot module's (Shop.odds reads them)
--   bundles     "bundle_<name>": a fixed themed set of wraps and hats, each for a named weapon (only things that exist
--               on roblox today)
--   singles     "wrap:<id>@<weapon>" / "hat:<id>@<weapon>": one item for one weapon, sold only while it is in today's
--               featured rotation
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
local RANK = { free = 0, common = 1, rare = 2, epic = 3, legendary = 4 }
function Shop.rank(r: string): number return RANK[r] or 0 end

-- what a single costs, by kind and rarity (Robux; unused while free)
Shop.PRICE = {
	wrap = { free = 0, common = 75, rare = 150, epic = 300, legendary = 600 },
	hat = { free = 0, common = 100, rare = 200, epic = 400, legendary = 750 },
}
Shop.KIND_NAMES = { wrap = "Wrap", hat = "Hat" }

-- wraps that never go in a bundle or the rotation: their picture versions broke Roblox's image rules and they are
-- plain colour wraps now (roblox-upload-content-rules), or they are the free ones everyone has
Shop.HELD_BACK = { qr = true, barcode = true, meat = true, organ = true, corp = true, memo = true, jersey = true, default = true }

-- wraps and hats are owned PER WEAPON (the owner, 16 Nov: "spray cans should give you a wrap for only one gun at a
-- time"): an item is (kind, id, weapon), written "<id>@<weapon>" where one string is needed (Shop.key)
export type Item = { kind: string, id: string, weapon: string? }
export type Hero = { weapon: string, wrap: string?, hat: string? }
export type Offer = {
	id: string, type: string, name: string, blurb: string, rarity: string,
	robux: number, productId: number?,
	items: { Item }?, hero: Hero?, -- a bundle
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

-- ---------------------------------------------------------------- items
function Shop.itemInfo(kind: string, id: string): (string, string)
	if kind == "wrap" then
		local w = Roster.wrapById[id]
		if w then return w.name, w.rarity end
	elseif kind == "hat" then
		local h = GunHatData.HATS[id]
		if h then return h.name, h.rarity end
	end
	return id, "common"
end
function Shop.exists(kind: string, id: string, weapon: string?): boolean
	if weapon ~= nil and not Shop.WEAPON_SET[weapon] then return false end
	if kind == "wrap" then return Roster.wrapById[id] ~= nil end
	if kind == "hat" then
		return GunHatData.HATS[id] ~= nil and id ~= "none" and (weapon == nil or GunHatData.SPOTS[weapon] ~= nil)
	end
	return false
end
-- "Sakura Storm · SMG"
function Shop.itemLabel(it: Item): string
	local name = Shop.itemInfo(it.kind, it.id)
	return if it.weapon then name .. " · " .. Shop.weaponName(it.weapon) else name
end
function Shop.singlePrice(kind: string, id: string): number
	local _, r = Shop.itemInfo(kind, id)
	local t = (Shop.PRICE :: any)[kind]
	return if t then t[r] or 0 else 0
end

-- ---------------------------------------------------------------- containers
-- the names and prices are the shop's; what's inside and the odds are the loot module's (Jankfire.LootTable, the web
-- game's CONTAINERS): crates hold weapon skins (none on Roblox yet: "coming soon"), duffel bags hats, spray cans wraps
Shop.containers = {
	{ id = "crate", type = "container", name = "Crate", rarity = "epic", robux = 120, productId = nil,
		blurb = "a sealed case. one weapon skin inside.", pool = "weapon skins" },
	{ id = "bag", type = "container", name = "Duffel Bag", rarity = "rare", robux = 90, productId = nil,
		blurb = "zipped shut. a hat you don't have yet.", pool = "hats" },
	{ id = "spray", type = "container", name = "Spray Can", rarity = "common", robux = 60, productId = nil,
		blurb = "shake it. a wrap you don't have yet.", pool = "wraps" },
} :: { Offer }

-- ---------------------------------------------------------------- bundles
-- themed sets that dress several guns: every wrap and hat in a set is for one named weapon. hero = what the big
-- preview and the hub's hologram show: one weapon wearing its wrap and hat from the set. robux is about 60% of the
-- singles' worth (Shop.worth)
local function W(id: string, weapon: string): Item return { kind = "wrap", id = id, weapon = weapon } end
local function H(id: string, weapon: string): Item return { kind = "hat", id = id, weapon = weapon } end
Shop.bundles = {
	{ id = "bundle_nightshift", type = "bundle", name = "Night Shift", rarity = "legendary",
		blurb = "dark metal, one cold glow. for people who play after midnight.",
		items = { W("hex", "ar"), H("tophat", "ar"), W("carbon", "smg"), W("lchrome", "revolver"), W("matte", "pistol") },
		hero = { weapon = "ar", wrap = "hex", hat = "tophat" } },
	{ id = "bundle_fieldissue", type = "bundle", name = "Field Issue", rarity = "rare",
		blurb = "four camos and a hat that has seen things. standard kit.",
		items = { W("digital", "sniper"), H("cowboy", "sniper"), W("urban", "ar"), W("desert", "shotgun"), W("arctic", "dmr") },
		hero = { weapon = "sniper", wrap = "digital", hat = "cowboy" } },
	{ id = "bundle_teahouse", type = "bundle", name = "Tea House", rarity = "legendary",
		blurb = "waves, leaves and gold in the cracks. very calm. still a gun.",
		items = { W("kintsugi", "katana"), H("chef", "katana"), W("seigaiha", "smg"), W("asanoha", "revolver"), W("shibori", "lever"), W("sakura", "burst") },
		hero = { weapon = "katana", wrap = "kintsugi", hat = "chef" } },
	{ id = "bundle_deepspace", type = "bundle", name = "Deep Space", rarity = "legendary",
		blurb = "dust, dots and a hole that eats light. halo included.",
		items = { W("nebula", "smg"), H("halo", "smg"), W("galaxy", "lmg"), W("aurora", "sniper"), W("blackhole", "redline") },
		hero = { weapon = "smg", wrap = "nebula", hat = "halo" } },
	{ id = "bundle_machineshop", type = "bundle", name = "Machine Shop", rarity = "epic",
		blurb = "brushed, folded, oxidised, anodised. it all still works.",
		items = { W("damascus", "shotgun"), H("propeller", "shotgun"), W("brushed", "lmg"), W("copper", "sawnoff"), W("titanium", "autoshot") },
		hero = { weapon = "shotgun", wrap = "damascus", hat = "propeller" } },
	{ id = "bundle_quarry", type = "bundle", name = "Quarry", rarity = "legendary",
		blurb = "cut stone and one opal. heavier than it looks.",
		items = { W("marble", "redline"), H("crown", "redline"), W("jade", "marbles"), W("granite", "sawnoff"), W("geode", "pistol"), W("opal", "revolver") },
		hero = { weapon = "redline", wrap = "marble", hat = "crown" } },
} :: { Offer }

-- ---------------------------------------------------------------- lookups
Shop.byId = {} :: { [string]: Offer }
for _, o in Shop.containers do Shop.byId[o.id] = o end
for _, b in Shop.bundles do
	local worth = 0
	for _, it in b.items :: { Item } do worth += Shop.singlePrice(it.kind, it.id) end
	b.robux = math.floor(worth * 0.6 / 10 + 0.5) * 10 - 1
	b.productId = nil
	Shop.byId[b.id] = b
end

-- the singles the rotation can show (wraps and hats that are not free and not held back)
Shop.singlesPool = {} :: { Item }
for _, w in Roster.wraps do
	if w.rarity ~= "free" and not Shop.HELD_BACK[w.id] then table.insert(Shop.singlesPool, W(w.id)) end
end
for _, id in GunHatData.ORDER do
	local h = GunHatData.HATS[id]
	if id ~= "none" and h and h.rarity ~= "free" then table.insert(Shop.singlesPool, H(id)) end
end

-- a single: one wrap or hat for one weapon, id "wrap:<id>@<weapon>" / "hat:<id>@<weapon>"
local function single(kind: string, id: string, weapon: string): Offer?
	if not Shop.exists(kind, id, weapon) then return nil end
	local name, rarity = Shop.itemInfo(kind, id)
	return { id = kind .. ":" .. id .. "@" .. weapon, type = "single", name = name, rarity = rarity, blurb = "",
		robux = Shop.singlePrice(kind, id), productId = nil, kind = kind, item = id, weapon = weapon }
end

-- any offer by id: a container, a bundle, or a single ("wrap:galaxy@smg", "hat:crown@katana")
function Shop.offer(id: any): Offer?
	if type(id) ~= "string" then return nil end
	local o = Shop.byId[id]
	if o then return o end
	local kind, item, weapon = string.match(id, "^(%a+):([%w_]+)@([%w_]+)$")
	if kind and item and weapon then return single(kind, item, weapon) end
	return nil
end

-- what an offer gives, each { kind, id, weapon } (a container gives itself: the loot server adds one to your stock)
function Shop.contents(o: Offer): { Item }
	if o.type == "bundle" then return o.items :: { Item } end
	if o.type == "single" then return { { kind = o.kind :: string, id = o.item :: string, weapon = o.weapon } } end
	return {}
end
-- what a bundle's items would cost one by one
function Shop.worth(o: Offer): number
	local n = 0
	for _, it in Shop.contents(o) do n += Shop.singlePrice(it.kind, it.id) end
	return n
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
	local hero = Shop.bundles[(d % #Shop.bundles) + 1].id
	-- four wraps and two hats, each for one weapon, at least one epic-or-better, no cosmetic and no weapon twice
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
	draw(wraps, Shop.DAILY - 2, daily)
	draw(hats, 2, daily)
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
	rotCache[d] = r
	return r
end

-- can this offer be bought right now? containers and bundles always; a single only while it's in today's rotation
-- (yesterday's too, for a few minutes after the turn, so a click made just before midnight still goes through)
function Shop.onSale(id: string, t: number?): boolean
	local o = Shop.offer(id)
	if not o then return false end
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
-- nothing in this container is on roblox yet (the crate, until weapon skins land)
function Shop.soon(containerId: string): boolean
	return LootTable ~= nil and type(LootTable.soon) == "function" and LootTable.soon(containerId) == true
end

-- ---------------------------------------------------------------- developer products (off while Shop.ROBUX is false)
-- when real prices go on: make one developer product per container and bundle on the Creator Hub (Monetization >
-- Developer Products, priced as `robux` above) and paste its id here. singles share one product per kind and rarity
-- ("wrap:epic", "hat:legendary"): the server remembers which single you asked for (ShopReceipts.server.luau)
Shop.PRODUCTS = {
	-- crate = 0, bag = 0, spray = 0,
	-- bundle_nightshift = 0, ...
	-- ["wrap:common"] = 0, ["wrap:rare"] = 0, ["wrap:epic"] = 0, ["wrap:legendary"] = 0,
	-- ["hat:common"] = 0, ["hat:rare"] = 0, ["hat:epic"] = 0, ["hat:legendary"] = 0,
} :: { [string]: number }
Shop.byProduct = {} :: { [number]: string } -- product id -> offer id, or a tier ("wrap:epic")
for key, pid in Shop.PRODUCTS do
	if type(pid) == "number" and pid > 0 then
		Shop.byProduct[pid] = key
		local o = Shop.byId[key]
		if o then o.productId = pid end
	end
end
-- the developer product an offer is bought with (nil: not for sale for Robux yet)
function Shop.productFor(o: Offer): number?
	if o.type == "single" then
		local pid = Shop.PRODUCTS[(o.kind :: string) .. ":" .. o.rarity]
		return if type(pid) == "number" and pid > 0 then pid else nil
	end
	local pid = Shop.PRODUCTS[o.id]
	return if type(pid) == "number" and pid > 0 then pid else nil
end

return Shop
