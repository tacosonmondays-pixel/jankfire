--!strict
-- THE VIP DAILY REWARD: the table, the roll and the odds (the server, VipDaily.luau, rolls and pays; the client shows the
-- reel; the docs quote VipDailyData.odds). the owner, 17 Nov 2026: "If you talk to Trisangle in the vip room as long as
-- you have vip you get a random daily reward with the best thing being a special wrap skin hat anddddd skin case. Bags
-- cans coins etc will be filler rewards".
--   * once a day per player (a new day at 00:00 UTC), VIP only.
--   * filler most days: Brass (the quests' coin), a Spray Can, a Duffel Bag. rare: a Crate (the skin case). the best,
--     very rare: a wrap, a hat and a weapon skin you can only get here (EXCLUSIVE; off until they're made).
--   * not too generous: about 320 Brass' worth a day on average (a Spray Can is 1,000 Brass in the shop, a Duffel Bag
--     2,500), next to a quest grinder's 231 Brass a day. a Crate about every 100 days (1%: the quests' sim showed 2%
--     nearly halved a regular VIP's wait for one; it stays mainly a ticket reward), one of the three every 100.
-- pure: no Instances, no requires. docs: roblox/docs/SHOP.md (VIP daily reward)
local D = {}

export type Entry = { id: string, kind: string, n: number?, cid: string?, w: number, tier: string, rarity: string }
export type Prize = { id: string, kind: string, n: number?, cid: string?, item: string?, tier: string, rarity: string, name: string }

-- the three things only this reward gives: the Triangulum trio (the skin-concepts session's design, 17 Nov; shared notes
-- triangulum-vip-brief.md), made by the wraps, hats and gun models sessions. a slot turns on by itself once its item is
-- in the place (nil = off). this list IS the daily-only mark: they are never sold (Shop.dailyOnly), never in a container
-- (the loot pools skip VipDailyData.isExclusive), a skin set or the VIP pack. never mark them vip: the VIP pack gives
-- every vip thing
D.EXCLUSIVE = {
	wrap = "triangulum" :: string?, -- Triangulum (a wrap: worn on every gun, like the VIP pack's)
	hat = "tricorne" :: string?, -- Star Tricorne (every gun with a hat spot)
	skin = "sniper_triangulum" :: string?, -- Triangulum (the Sniper)
}
function D.isExclusive(kind: string, id: string): boolean
	return (D.EXCLUSIVE :: any)[kind] == id
end

-- weights out of 1,000 (with the three off, the other 990 share it out)
D.TABLE = {
	-- filler: most days
	{ id = "brass_s", kind = "brass", n = 40, w = 420, tier = "filler", rarity = "common" },
	{ id = "brass_m", kind = "brass", n = 100, w = 270, tier = "filler", rarity = "common" },
	{ id = "spray", kind = "container", cid = "spray", w = 130, tier = "filler", rarity = "common" },
	{ id = "brass_l", kind = "brass", n = 250, w = 110, tier = "filler", rarity = "rare" },
	{ id = "bag", kind = "container", cid = "bag", w = 50, tier = "filler", rarity = "rare" },
	-- rare: the skin case
	{ id = "crate", kind = "container", cid = "crate", w = 10, tier = "rare", rarity = "epic" },
	-- the best: only here
	{ id = "x_wrap", kind = "wrap", w = 4, tier = "best", rarity = "exotic" }, -- (Triangulum moves: Exotic since 20 Nov)
	{ id = "x_hat", kind = "hat", w = 3, tier = "best", rarity = "legendary" },
	{ id = "x_skin", kind = "skin", w = 3, tier = "best", rarity = "legendary" },
} :: { Entry }
D.byId = {} :: { [string]: Entry }
for _, e in D.TABLE do D.byId[e.id] = e end

D.CONTAINER_NAMES = { spray = "Spray Can", bag = "Duffel Bag", crate = "Crate" }
D.FALLBACK_FULL = "brass_m" -- a container you can't hold more of (the free-testing cap) pays this instead
D.FALLBACK_OWNED = "crate" -- one of the three you already have pays another of them, else this

-- the day (UTC) and when the next one starts
function D.day(t: number?): number return math.floor((t or os.time()) / 86400) end
function D.nextAt(day: number): number return (day + 1) * 86400 end

-- what the roll needs from the game (the server passes the real ones; a simulation passes stand-ins):
--   live(kind, id): the exclusive item is in the place; owns(kind, id): the player has it; full(cid): no more room for
--   that container; name(kind, id): an item's name
export type Ctx = { live: ((string, string) -> boolean)?, owns: ((string, string) -> boolean)?, full: ((string) -> boolean)?,
	name: ((string, string) -> string)? }

-- the entries that can come up today
function D.active(ctx: Ctx?): { Entry }
	local out = {}
	for _, e in D.TABLE do
		if e.tier ~= "best" then
			table.insert(out, e)
		else
			local id = (D.EXCLUSIVE :: any)[e.kind]
			if type(id) == "string" and (not ctx or not ctx.live or ctx.live(e.kind, id)) then table.insert(out, e) end
		end
	end
	return out
end

local function pick(list: { Entry }, rng: Random): Entry
	local total = 0
	for _, e in list do total += e.w end
	local x = rng:NextNumber() * total
	for _, e in list do
		x -= e.w
		if x < 0 then return e end
	end
	return list[#list]
end

function D.prize(e: Entry, ctx: Ctx?): Prize
	local p: Prize = { id = e.id, kind = e.kind, n = e.n, cid = e.cid, tier = e.tier, rarity = e.rarity, name = "" }
	if e.kind == "brass" then
		p.name = tostring(e.n) .. " Coins" -- (Brass in the code is Coins on screen, 18 Nov)
	elseif e.kind == "container" then
		p.name = D.CONTAINER_NAMES[e.cid or ""] or tostring(e.cid)
	else
		p.item = (D.EXCLUSIVE :: any)[e.kind]
		p.name = if ctx and ctx.name and p.item then ctx.name(e.kind, p.item :: string)
			elseif p.item then p.item :: string
			else ({ wrap = "The daily wrap", hat = "The daily hat", skin = "The daily weapon skin" } :: any)[e.kind] or e.kind
	end
	return p
end

-- today's prize: by weight; one of the three you have already becomes another of them you lack (else a Crate); a
-- container you've no room for becomes 100 Brass
function D.roll(rng: Random, ctx: Ctx?): Prize
	local list = D.active(ctx)
	local e = pick(list, rng)
	if e.tier == "best" and ctx and ctx.owns then
		local id = (D.EXCLUSIVE :: any)[e.kind]
		if ctx.owns(e.kind, id) then
			local left = {}
			for _, x in list do
				if x.tier == "best" and not ctx.owns(x.kind, (D.EXCLUSIVE :: any)[x.kind]) then table.insert(left, x) end
			end
			e = if #left > 0 then pick(left, rng) else D.byId[D.FALLBACK_OWNED]
		end
	end
	if e.kind == "container" and ctx and ctx.full and ctx.full(e.cid :: string) then e = D.byId[D.FALLBACK_FULL] end
	return D.prize(e, ctx)
end

-- the reel the reveal spins: n cards drawn by weight, the prize on card `land`
D.REEL = 32
D.LAND = 27
function D.reel(prize: Prize, rng: Random, ctx: Ctx?): { Prize }
	local list = D.active(ctx)
	local out = {}
	for i = 1, D.REEL do
		out[i] = if i == D.LAND then prize else D.prize(pick(list, rng), ctx)
	end
	return out
end

-- the odds, for the docs and a test: { id, kind, name, tier, pct, days } (days = the average wait for it, claiming
-- every day), with the three exclusives on or off
function D.odds(withBest: boolean?): { any }
	local total = 0
	for _, e in D.TABLE do if e.tier ~= "best" or withBest then total += e.w end end
	local out = {}
	for _, e in D.TABLE do
		if e.tier ~= "best" or withBest then
			local pct = e.w / total * 100
			table.insert(out, { id = e.id, kind = e.kind, name = D.prize(e).name, tier = e.tier, pct = pct, days = 100 / pct })
		end
	end
	return out
end

return D
