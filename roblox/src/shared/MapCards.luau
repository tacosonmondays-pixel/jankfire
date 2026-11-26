--!strict
-- the map cards' pictures (the map vote and the PARTY card's map pick: server/Party.luau, client/QuickVoteUI.luau,
-- client/ModesTab.luau). one wide picture an arena, taken in Studio from over a corner of the play area under the
-- arena's own look (HubLook.preview), 17 Nov 2026; uploaded as decals, these are their image ids. no text, signs or
-- logos in any of them. an arena with no picture yet gets a plain card with its name (thumb = "")
local MapCards = {}

MapCards.THUMBS = {
	RooftopV2 = "rbxassetid://93707330689323", -- ROOFTOP: SKYLINE
	RooftopV3 = "rbxassetid://118363873222671", -- ROOFTOP
	Crate = "rbxassetid://99099294642625", -- CRATE
	Platform = "rbxassetid://74163846778368", -- PLATFORM
	Bazaar = "rbxassetid://76328107850945", -- BAZAAR
	Gut = "rbxassetid://82998499636054", -- THE GUT
	BazaarV2 = "rbxassetid://131742520863260", -- BAZAAR: ROOFTOPS
	DesertV2 = "rbxassetid://92556822417681", -- DESERT: CANYON
	SuburbV2 = "rbxassetid://134037734020157", -- SUBURB: CUL-DE-SAC
	Backrooms = "rbxassetid://114619621384993", -- BACKROOMS (18 Nov: Cycles renders of the kit, tools/roblox/card_render.py)
	Forest = "rbxassetid://76491374027623", -- SPOOKY FOREST
	ArcticCabin = "rbxassetid://112923749467887", -- ARCTIC CABIN
	Skatepark = "rbxassetid://92147472353603", -- SKATEPARK
	Station = "rbxassetid://92722876561811", -- STATION
	JankfieldHigh = "rbxassetid://139658727063957", -- JANKFIELD HIGH (the zombies school: its courtyard at night, card_render.py)
	JankfieldHighV2A = "rbxassetid://79637765738576", -- JANKFIELD HIGH v2A (old: the locker hall and the main stairs)
	JankfieldHighV2B = "rbxassetid://121043658001469", -- JANKFIELD HIGH v2B (new: the same view)
} :: { [string]: string }

-- a map vote's three (or fewer) cards out of `pool`, never `last` while there's anything else. pure but for the dice
function MapCards.offer(pool: { string }, last: string?, n: number?): { string }
	local left = {}
	for _, id in pool do if id ~= last then table.insert(left, id) end end
	if #left == 0 then left = table.clone(pool) end
	local out = {}
	while #out < (n or 3) and #left > 0 do table.insert(out, table.remove(left, math.random(#left)) :: string) end
	return out
end
-- the winner of votes ({ [voter] = id }): most votes, a tie drawn among the top, no votes at all drawn among all
function MapCards.result(options: { string }, votes: { [any]: string }): string?
	local counts = {}
	for _, id in votes do counts[id] = (counts[id] or 0) + 1 end
	local best, top = {}, 0
	for _, id in options do
		local c = counts[id] or 0
		if c > top then best, top = { id }, c elseif c == top then table.insert(best, id) end
	end
	return if #best > 0 then best[math.random(#best)] else nil
end
-- RANDOM (21 Nov 2026, the owner: "for pads and casual andthing but ranked basically let us pick maps"): every vote but
-- ranked offers its maps and RANDOM, a card of its own. RANDOM is any map of the rotation for the match (MapCards.draw)
MapCards.RANDOM = "random"
function MapCards.randomCard(): any return { id = MapCards.RANDOM, title = "RANDOM", thumb = "", random = true } end
-- the winner of a vote with RANDOM on it: most votes among the maps and RANDOM, a tie drawn among the top, no votes at
-- all = RANDOM. the caller turns RANDOM into a map (MapCards.draw)
function MapCards.resultOrRandom(options: { string }, votes: { [any]: string }): string
	local counts = MapCards.counts(votes)
	local all = table.clone(options)
	table.insert(all, MapCards.RANDOM)
	local best, top = {}, 0
	for _, id in all do
		local c = counts[id] or 0
		if c > top then best, top = { id }, c elseif c == top and c > 0 then table.insert(best, id) end
	end
	if top == 0 then return MapCards.RANDOM end
	return best[math.random(#best)]
end
-- RANDOM's map: any one of pool, never last while there's another (nil: an empty pool)
function MapCards.draw(pool: { string }, last: string?): string?
	local left = {}
	for _, id in pool do if id ~= last then table.insert(left, id) end end
	if #left == 0 then left = table.clone(pool) end
	return if #left > 0 then left[math.random(#left)] else nil
end
function MapCards.counts(votes: { [any]: string }): { [string]: number }
	local counts = {}
	for _, id in votes do counts[id] = (counts[id] or 0) + 1 end
	return counts
end

-- (a copy's name, "Gut_copy2", is its arena's)
function MapCards.thumb(arena: string?): string
	if type(arena) ~= "string" then return "" end
	local base = string.match(arena, "^(.-)_copy%d+$") or arena
	return MapCards.THUMBS[base] or ""
end

return MapCards
