--!strict
-- DAILY QUESTS + THE WEEKLY TRACK: the numbers and the quest pool (roblox/docs/QUESTS.md). the server (Quests.luau)
-- counts and pays; the screen (QuestUI.luau) and the shop read the same table. pure: no Instances.
-- the economy is simulated in tools/roblox/quest_econ.mjs: keep its TIERS / STEPS / PRICES the same as these.
--   * Brass: our own soft currency (spent casings). only quests and the weekly track pay it.
--   * Crate Tickets: only the weekly track gives them. 12 redeem a Crate (Brass never buys a Crate).
--   * 3 quests a day (one easy, one medium, one hard), new ones at 00:00 UTC, one free reroll a day.
--   * a finished quest pays its Brass and its weekly points at once. the weekly bar pays at its steps and starts
--     again on Monday 00:00 UTC.
local Q = {}

Q.TIERS = {
	easy = { brass = 30, pts = 1, name = "EASY" },
	medium = { brass = 50, pts = 2, name = "MEDIUM" },
	hard = { brass = 80, pts = 3, name = "HARD" },
}
Q.ORDER = { "easy", "medium", "hard" } -- one quest of each a day, in this order on the screen
Q.REROLLS = 1 -- free rerolls a day

-- the weekly bar: points from finished quests (most a week can give: 7 x 6 = 42); it's full at the last step
Q.STEPS = {
	{ at = 3, brass = 75 },
	{ at = 6, tix = 1 },
	{ at = 10, brass = 100 },
	{ at = 15, tix = 1 },
	{ at = 21, brass = 150 },
	{ at = 28, tix = 1 },
	{ at = 34, brass = 200 },
	{ at = 40, tix = 2 },
}
Q.FULL = Q.STEPS[#Q.STEPS].at

-- what the shop asks for a container (Shared.Shop ids). tix = Crate Tickets, brass = Brass; nil = not for that
Q.PRICES = {
	crate = { tix = 12 },
	bag = { tix = 6, brass = 2500 },
	spray = { tix = 3, brass = 1000 },
}
Q.CURRENCY = { brass = "Brass", tix = "Crate Tickets", tix1 = "Crate Ticket" }

-- ---------------------------------------------------------------- weapon groups (live weapons only count: Roster)
Q.CLASSES = {
	auto = { name = "an automatic", ids = { "ar", "smg", "burst", "lmg", "redline" } },
	marksman = { name = "a marksman rifle", ids = { "dmr", "lever" } },
	shotgun = { name = "a shotgun", ids = { "shotgun", "autoshot", "sawnoff", "marbles" } },
	side = { name = "a sidearm", ids = { "pistol", "revolver", "sawnoff", "marbles" } },
	sniper = { name = "the Sniper", ids = { "sniper" } },
	smg = { name = "the SMG", ids = { "smg" } },
	katana = { name = "the Katana", ids = { "katana" } },
	shredder = { name = "the Shredder", ids = { "shredder" } },
	item = { name = "your item", ids = { "frag", "medkit", "bubble", "duck", "smoke", "popper", "reverse", "wand", "camera", "quiz", "nvg", "radar", "laptop" } },
}
-- weapon id -> its groups
Q.CLASS_OF = {} :: { [string]: { string } }
for cid, c in Q.CLASSES do
	for _, wid in c.ids do
		Q.CLASS_OF[wid] = Q.CLASS_OF[wid] or {}
		table.insert(Q.CLASS_OF[wid], cid)
	end
end
for _, list in Q.CLASS_OF do table.sort(list) end

-- the range plates (RangeTest: Hub.TrainingGround.Range.Plates) and what the board calls them
Q.RANGE = { Easy = "CHILL", Medium = "NORMAL", Hard = "SWEATY" }
Q.LONG = 40 -- m: a long Sniper kill (1 m = 3 studs, Config.S)

-- ---------------------------------------------------------------- the pool
-- stat: what the server counts (Quests.luau), goal: how many. max = the best single value counts (a run's score, a
-- streak), not the sum. sub = which weapons count, shown small under the quest
export type Quest = { id: string, tier: string, stat: string, goal: number, text: string, max: boolean?, sub: string? }
local POOL: { Quest } = {
	-- easy
	{ id = "e_play", tier = "easy", stat = "play", goal = 3, text = "Play 3 matches" },
	{ id = "e_win", tier = "easy", stat = "win", goal = 1, text = "Win a match" },
	{ id = "e_kills", tier = "easy", stat = "kill", goal = 10, text = "Get 10 kills" },
	{ id = "e_dmg", tier = "easy", stat = "dmg", goal = 1500, text = "Deal 1,500 damage" },
	{ id = "e_rounds", tier = "easy", stat = "round", goal = 5, text = "Win 5 rounds" },
	{ id = "e_hs", tier = "easy", stat = "hs", goal = 6, text = "Land 6 headshots" },
	{ id = "e_items", tier = "easy", stat = "item", goal = 5, text = "Use your item 5 times" },
	{ id = "e_auto", tier = "easy", stat = "kill:auto", goal = 6, text = "Get 6 kills with an automatic" },
	{ id = "e_side", tier = "easy", stat = "kill:side", goal = 3, text = "Get 3 kills with a sidearm" },
	{ id = "e_shotgun", tier = "easy", stat = "kill:shotgun", goal = 4, text = "Get 4 kills with a shotgun" },
	{ id = "e_range", tier = "easy", stat = "range:Easy", goal = 20, max = true, text = "Score 20 on a CHILL range run" },
	-- medium
	{ id = "m_win", tier = "medium", stat = "win", goal = 2, text = "Win 2 matches" },
	{ id = "m_play", tier = "medium", stat = "play", goal = 5, text = "Play 5 matches" },
	{ id = "m_kills", tier = "medium", stat = "kill", goal = 25, text = "Get 25 kills" },
	{ id = "m_hs", tier = "medium", stat = "hs", goal = 15, text = "Land 15 headshots" },
	{ id = "m_hskill", tier = "medium", stat = "hskill", goal = 5, text = "Get 5 headshot kills" },
	{ id = "m_slide", tier = "medium", stat = "slidekill", goal = 3, text = "Get 3 kills while sliding" },
	{ id = "m_grapple", tier = "medium", stat = "grapplekill", goal = 3, text = "Get 3 kills on the grapple" },
	{ id = "m_sniper", tier = "medium", stat = "kill:sniper", goal = 5, text = "Get 5 kills with the Sniper" },
	{ id = "m_katana", tier = "medium", stat = "kill:katana", goal = 5, text = "Get 5 kills with the Katana" },
	{ id = "m_marksman", tier = "medium", stat = "kill:marksman", goal = 6, text = "Get 6 kills with a marksman rifle" },
	{ id = "m_streak", tier = "medium", stat = "streak", goal = 3, max = true, text = "Get 3 kills in a row without dying" },
	{ id = "m_ranked", tier = "medium", stat = "ranked", goal = 2, text = "Play 2 ranked matches" },
	{ id = "m_party", tier = "medium", stat = "party", goal = 2, text = "Play 2 matches with your party" },
	{ id = "m_void", tier = "medium", stat = "voidkill", goal = 3, text = "Knock 3 enemies off the map" },
	{ id = "m_dmg", tier = "medium", stat = "dmg", goal = 4000, text = "Deal 4,000 damage" },
	{ id = "m_range", tier = "medium", stat = "range:Medium", goal = 20, max = true, text = "Score 20 on a NORMAL range run" },
	-- hard
	{ id = "h_win", tier = "hard", stat = "win", goal = 4, text = "Win 4 matches" },
	{ id = "h_kills", tier = "hard", stat = "kill", goal = 50, text = "Get 50 kills" },
	{ id = "h_hskill", tier = "hard", stat = "hskill", goal = 12, text = "Get 12 headshot kills" },
	{ id = "h_flawless", tier = "hard", stat = "flawless", goal = 1, text = "Win a match without losing a round" },
	{ id = "h_streak", tier = "hard", stat = "streak", goal = 5, max = true, text = "Get 5 kills in a row without dying" },
	{ id = "h_rankedwin", tier = "hard", stat = "rankedwin", goal = 2, text = "Win 2 ranked matches" },
	{ id = "h_long", tier = "hard", stat = "longkill", goal = 3, text = "Get 3 Sniper kills from 40 m or more" },
	{ id = "h_range", tier = "hard", stat = "range:Hard", goal = 20, max = true, text = "Score 20 on a SWEATY range run" },
	{ id = "h_slide", tier = "hard", stat = "slidekill", goal = 8, text = "Get 8 kills while sliding" },
	{ id = "h_grapple", tier = "hard", stat = "grapplekill", goal = 8, text = "Get 8 kills on the grapple" },
	{ id = "h_itemkill", tier = "hard", stat = "kill:item", goal = 3, text = "Get 3 kills with your item" },
	{ id = "h_dmg", tier = "hard", stat = "dmg", goal = 10000, text = "Deal 10,000 damage" },
	{ id = "h_shredder", tier = "hard", stat = "kill:shredder", goal = 8, text = "Get 8 kills with the Shredder" },
}
Q.POOL = POOL
Q.byId = {} :: { [string]: Quest }
Q.byTier = { easy = {}, medium = {}, hard = {} } :: { [string]: { Quest } }
for _, q in POOL do
	Q.byId[q.id] = q
	table.insert(Q.byTier[q.tier], q)
end

-- the weapon names a class quest counts (the small line under it), from Roster names when the caller passes them
function Q.subOf(q: Quest, names: { [string]: string }?): string?
	local cid = string.match(q.stat, "^kill:(%w+)$")
	local c = cid and Q.CLASSES[cid]
	if not c or #c.ids <= 1 or cid == "item" then return nil end
	local out = {}
	for _, wid in c.ids do table.insert(out, if names and names[wid] then names[wid] else wid) end
	return table.concat(out, " · ")
end

-- ---------------------------------------------------------------- time (UTC)
local DAY = 86400
function Q.day(t: number): number return math.floor(t / DAY) end
-- weeks start on Monday 00:00 UTC (1 Jan 1970, day 0, was a Thursday)
function Q.week(t: number): number return (Q.day(t) + 3) // 7 end
function Q.dayLeft(t: number): number return (Q.day(t) + 1) * DAY - t end
function Q.weekLeft(t: number): number return ((Q.week(t) + 1) * 7 - 3) * DAY - t end
-- "5H 12M" / "3D 4H"
function Q.left(secs: number): string
	secs = math.max(0, math.floor(secs))
	local d, h, m = secs // DAY, (secs % DAY) // 3600, (secs % 3600) // 60
	if d > 0 then return ("%dD %dH"):format(d, h) end
	if h > 0 then return ("%dH %dM"):format(h, m) end
	return ("%dM"):format(math.max(1, m))
end

-- ---------------------------------------------------------------- the roll
-- a player's quest for one tier on one day: the same every time it's asked (seeded by the player, the day, the tier
-- and how many times they rerolled), never one of `avoid` (today's others, yesterday's, the one rerolled away)
local SALT = { easy = 11, medium = 23, hard = 37 }
function Q.roll(uid: number, day: number, tier: string, n: number, avoid: { [string]: boolean }?): string
	local list = Q.byTier[tier]
	local rng = Random.new((math.abs(uid) % 2147483647) * 7919 + day * 104729 + (SALT[tier] or 1) * 1009 + n * 31)
	local pick = {}
	for _, q in list do if not (avoid and avoid[q.id]) then table.insert(pick, q.id) end end
	if #pick == 0 then for _, q in list do table.insert(pick, q.id) end end
	return pick[rng:NextInteger(1, #pick)]
end

-- points -> the steps reached
function Q.stepsAt(pts: number): number
	local n = 0
	for i, s in Q.STEPS do if pts >= s.at then n = i end end
	return n
end

return Q
