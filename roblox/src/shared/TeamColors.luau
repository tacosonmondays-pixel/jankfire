--!strict
-- TEAM COLOURS (20 Nov 2026, the owner: "maybe lets use differnt accent colors than the rivals one please": the old
-- pink / cyan / yellow read as Rivals'). the teams' colours and names in one place, for the pads (the hub session's
-- HubKit) and the matches: Matches (the score line, the pads' counts, "you're BLOSSOM", the winner), Hud (a team's name in
-- a callout takes its colour), Settings (the colour-blind sets and cbText), MatchLoadout (the scoreboard bars),
-- SpectateClient (the watch overlay), ModeConfig (the classic modes' two sides).
--   TeamColors.OLD = true   the old palette again, everywhere at once (the one switch)
--   TeamColors.SET          which new set is in use: "pastel" (the owner's pick) or "ember" (the set before it)
--   TeamColors.SETS[set]    a set's list (names: one short uppercase word, they read "you're BLOSSOM", "BLOSSOM WINS";
--                           muted = the pads' plate colour; glow = a richer take on the hue for the pads' neon lanes, so
--                           they don't wash to white: the hub kit's, never HUD text) and its colour-blind variants for
--                           Settings > HUD (protan, deutan, tritan), hex without "#"
--   TeamColors.NEW, CB_NEW  the set in use at load (kept for readers of the first version; list() and cb() follow SET)
-- team i: 1 and 2 the two sides of a team match, 3 and 4 the extra free-for-all sides
local TeamColors = {}

-- (true until the pads read this module too (the hub session's HubKit) and the owner says go, so pads and matches
-- change together)
TeamColors.OLD = false

type Entry = { name: string, hex: string, muted: string, glow: string? }
type Set = { list: { Entry }, cb: { [string]: { string } } }

TeamColors.OLD_LIST = {
	{ name = "PINK", hex = "#ff4fd8", muted = "#6e3a63" },
	{ name = "CYAN", hex = "#37d6ff", muted = "#2f5f6e" },
	{ name = "YELLOW", hex = "#ffe14d", muted = "#6e6335" },
	{ name = "GREEN", hex = "#7dff8a", muted = "#3a6e40" },
} :: { Entry }
TeamColors.OLD_CB = {
	protan = { "d98cbf", "56b4e9", "f0e442", "009e73" },
	deutan = { "cc79a7", "56b4e9", "f0e442", "009e73" },
	tritan = { "ff5a5a", "35c4c4", "f4f4f4", "8a8a8a" },
} :: { [string]: { string } }

TeamColors.SET = "pastel"
TeamColors.SETS = {
	-- (20 Nov 2026 ~23:10 UTC, the owner: "I dont like red whiet blue can it be pastel pink pastel blue and pastel yellow";
	-- values from the hub session, read as digits on the navy boards. colour-blind: pink against blue holds for deutan,
	-- and for protan by lightness; yellow holds against both; tritan sees the pink and the yellow alike, so its team 3 is
	-- white. MINT only in a four-way free-for-all)
	pastel = {
		list = {
			{ name = "BLOSSOM", hex = "#f4a7c8", muted = "#c98aa8", glow = "#e87fb0" },
			{ name = "SKY", hex = "#a3cbf2", muted = "#7fa3c8", glow = "#5b88e0" }, -- (glow: #6aa8e8 drifted to cyan under neon)
			{ name = "BUTTER", hex = "#f5dd8a", muted = "#c9b277", glow = "#e8c45a" },
			{ name = "MINT", hex = "#a6e3c4", muted = "#7fb89c", glow = "#5fcf9a" },
		},
		cb = {
			protan = { "cc79a7", "56b4e9", "f0e442", "009e73" },
			deutan = { "cc79a7", "56b4e9", "f0e442", "009e73" },
			tritan = { "f08aa8", "3fb6c6", "f4f4f4", "8a8a8a" },
		},
	},
	-- the hub session's first pick (20 Nov 2026): EMBER against STEEL, the warm-vs-cool pair that stays apart under
	-- protan, deutan and tritan; the third side IVORY (pale against a warm and a cool); SAGE only in a four-way. (EMBER and
	-- STEEL a little deeper on the hub session's ask: under neon the pads' lanes read redder and bluer than the counts)
	ember = {
		list = {
			{ name = "EMBER", hex = "#e8742a", muted = "#85492a" },
			{ name = "STEEL", hex = "#3f86d6", muted = "#355a86" },
			{ name = "IVORY", hex = "#efe6d2", muted = "#8d8676" },
			{ name = "SAGE", hex = "#93c17a", muted = "#56704b" },
		},
		cb = {
			protan = { "e69f00", "56b4e9", "f4f4f4", "009e73" },
			deutan = { "e69f00", "56b4e9", "f4f4f4", "009e73" },
			tritan = { "ff6a4a", "3a8fd8", "f4f4f4", "8a8a8a" },
		},
	},
} :: { [string]: Set }

local function active(): Set
	return TeamColors.SETS[TeamColors.SET] or TeamColors.SETS.pastel
end
TeamColors.NEW = active().list
TeamColors.CB_NEW = active().cb

function TeamColors.list(): { Entry }
	return if TeamColors.OLD then TeamColors.OLD_LIST else active().list
end
function TeamColors.cb(): { [string]: { string } }
	return if TeamColors.OLD then TeamColors.OLD_CB else active().cb
end
function TeamColors.hex(i: number): string
	local e = TeamColors.list()[i]
	return if e then string.lower(e.hex) else "#ffffff"
end
function TeamColors.color(i: number): Color3
	return Color3.fromHex(TeamColors.hex(i))
end
function TeamColors.name(i: number): string
	local e = TeamColors.list()[i]
	return if e then e.name else ("TEAM " .. tostring(i))
end
function TeamColors.muted(i: number): Color3
	local e = TeamColors.list()[i]
	return if e then Color3.fromHex(e.muted) else Color3.fromRGB(60, 60, 60)
end
-- the pads' neon colour of team i: its glow, else its own colour (never for HUD text)
function TeamColors.glow(i: number): Color3
	local e = TeamColors.list()[i]
	return if e and e.glow then Color3.fromHex(e.glow) else TeamColors.color(i)
end
-- the team number of a name ("BLOSSOM" -> 1), or nil
function TeamColors.index(name: string): number?
	for i, e in TeamColors.list() do if e.name == name then return i end end
	return nil
end

return TeamColors
