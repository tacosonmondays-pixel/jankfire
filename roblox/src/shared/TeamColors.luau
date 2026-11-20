--!strict
-- TEAM COLOURS (20 Nov 2026, the owner: "maybe lets use differnt accent colors than the rivals one please": the old
-- pink / cyan / yellow read as Rivals'). the teams' colours and names in one place, for the pads (the hub session's
-- HubKit) and the matches: Matches (the score line, the pads' counts, "you're EMBER", the winner), Hud (a team's name in a
-- callout takes its colour), Settings (the colour-blind sets and cbText), MatchLoadout (the scoreboard bars),
-- SpectateClient (the watch overlay), ModeConfig (the classic modes' two sides).
--   TeamColors.OLD = true   the old palette again, everywhere at once (the one switch)
--   TeamColors.NEW          the palette in use: the hub session picks it (names: one short uppercase word, they read
--                           "you're EMBER", "EMBER WINS"); muted = the pads' plate colour
--   TeamColors.CB_NEW       colour-blind variants of NEW for Settings > HUD (protan, deutan, tritan), hex without "#"
-- team i: 1 and 2 the two sides of a team match, 3 and 4 the extra free-for-all sides
local TeamColors = {}

-- (true until the pads read this module too (the hub session's HubKit), so pads and matches change together)
TeamColors.OLD = true

type Entry = { name: string, hex: string, muted: string }

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

-- the hub session's pick (20 Nov 2026): EMBER against STEEL, the warm-vs-cool pair that stays apart under protan,
-- deutan and tritan; the third side IVORY (pale against a warm and a cool, so a 1V1V1 never puts orange beside green for
-- red-green colour-blind players); SAGE only in a four-way free-for-all, where the colour-blind sets take over
TeamColors.NEW = {
	{ name = "EMBER", hex = "#ef8a32", muted = "#8a5530" },
	{ name = "STEEL", hex = "#4d94dc", muted = "#3d5f88" },
	{ name = "IVORY", hex = "#efe6d2", muted = "#8d8676" },
	{ name = "SAGE", hex = "#93c17a", muted = "#56704b" },
} :: { Entry }
TeamColors.CB_NEW = {
	protan = { "e69f00", "56b4e9", "f4f4f4", "009e73" },
	deutan = { "e69f00", "56b4e9", "f4f4f4", "009e73" },
	tritan = { "ff6a4a", "3a8fd8", "f4f4f4", "8a8a8a" },
} :: { [string]: { string } }

function TeamColors.list(): { Entry }
	return if TeamColors.OLD then TeamColors.OLD_LIST else TeamColors.NEW
end
function TeamColors.cb(): { [string]: { string } }
	return if TeamColors.OLD then TeamColors.OLD_CB else TeamColors.CB_NEW
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
-- the team number of a name ("EMBER" -> 1), or nil
function TeamColors.index(name: string): number?
	for i, e in TeamColors.list() do if e.name == name then return i end end
	return nil
end

return TeamColors
