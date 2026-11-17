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
} :: { [string]: string }

-- (a copy's name, "Gut_copy2", is its arena's)
function MapCards.thumb(arena: string?): string
	if type(arena) ~= "string" then return "" end
	local base = string.match(arena, "^(.-)_copy%d+$") or arena
	return MapCards.THUMBS[base] or ""
end

return MapCards
