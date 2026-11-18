--!strict
-- WEAPON MASTERY (the owner, 18 Nov 2026: "you'll be able to level up weapons to unlock gold, damascus, diamond and
-- galaxy camo for their respective guns"). every weapon has its own level, 1 to MAX, from XP earned WITH it in real
-- matches (server/MasteryXp.luau keeps it, in the stats save). on the way up it unlocks four camos for that gun alone.
-- docs/MASTERY.md. this module is shared and pure: the numbers, the curve, the camos, and whether a camo is live.
--
--   XP (the server decides, real matches only: never the hub, training, its dummies, a ghost match or a dev match)
--     a kill 100, +25 if the last hit was a headshot, an assist 50 (you hurt them in the 10 s before someone on your
--     side killed them: to the weapon you hurt them most with), a round won 50 and the match won 50 (each to the
--     weapon you held longest in that round / match)
--   the curve: level n to n + 1 takes STEP + GROW x (n - 1) XP. an even 1v1 to five is about 550 XP for the gun you
--     use, so GOLD (level 10, 4,860 XP) is about 9 matches with one gun, DAMASCUS (20, 15,960) about 29, DIAMOND (30,
--     33,060) about 60 and GALAXY (40, 56,160) about 102. XP stops at 40
--   the camos: wraps in Roster.wrapById only (Roster.masteryWraps), never in Roster.wraps: the containers, the shop's
--     rotation, bundles and the VIP pack all walk that list, so none of them can ever hold one. a camo is granted for its
--     gun alone ("mastery_gold@ar") through Loot.grant("mastery:mastery_gold@ar"), once
--   live: a camo shows (the loadout's strip, the bars' next-camo swatch) and is granted only once its picture is in the
--     place (ReplicatedStorage.JankfireWraps.<id>, built by the wraps session's WrapBook), or while ReplicatedStorage
--     has the attribute MasteryLive = true (Studio tests). a player who passed its level before it went live gets it on
--     their next join or level
-- the clients read the player attribute Mastery ("ar=5120;smg=40": XP per weapon, M.decode) and the remote event
-- JankfireRemotes.MasteryPush (level ups, camo unlocks, the match's gains: client/MasteryClient.client.luau)
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Roster = require(script.Parent:WaitForChild("Roster")) :: any

local M = {}

M.MAX = 40
M.XP = { kill = 100, headshot = 25, assist = 50, roundWin = 50, matchWin = 50 }
M.ASSIST_WINDOW = 10 -- s: hurt within this long before the kill
M.STEP, M.GROW = 300, 60

export type Camo = { id: string, name: string, level: number }
-- in order, the owner's: gold, damascus, diamond, galaxy. the ids are the wraps session's (Roster, WrapBook)
M.CAMOS = {
	{ id = "mastery_gold", name = "GOLD", level = 10 },
	{ id = "mastery_damascus", name = "DAMASCUS", level = 20 },
	{ id = "mastery_diamond", name = "DIAMOND", level = 30 },
	{ id = "mastery_galaxy", name = "GALAXY", level = 40 },
} :: { Camo }
M.byId = {} :: { [string]: Camo }
for _, c in M.CAMOS do M.byId[c.id] = c end

-- ------------------------------------------------------------------ the curve
-- XP from level n to n + 1 (0 at MAX)
function M.need(level: number): number
	if level >= M.MAX then return 0 end
	return M.STEP + M.GROW * (math.max(1, level) - 1)
end
-- XP to reach level n from nothing
function M.total(level: number): number
	local n = math.clamp(math.floor(level), 1, M.MAX) - 1
	return n * M.STEP + M.GROW * n * (n - 1) / 2
end
function M.levelOf(xp: any): number
	local x = math.max(0, tonumber(xp) or 0)
	local lv = 1
	while lv < M.MAX and x >= M.total(lv + 1) do lv += 1 end
	return lv
end
-- level, XP into it, XP it takes, and the fraction (1 at MAX)
function M.progress(xp: any): (number, number, number, number)
	local x = math.max(0, math.floor(tonumber(xp) or 0))
	local lv = M.levelOf(x)
	if lv >= M.MAX then return lv, 0, 0, 1 end
	local into, need = x - M.total(lv), M.need(lv)
	return lv, into, need, math.clamp(into / need, 0, 1)
end

-- ------------------------------------------------------------------ the camos
function M.isCamo(id: any): boolean
	return type(id) == "string" and M.byId[id] ~= nil
end
-- a mastery camo by its wrap row too (Roster's mastery = true): never sold, rolled, bundled or gifted
function M.masteryOnly(t: string, id: any): boolean
	if t ~= "wrap" or type(id) ~= "string" then return false end
	if M.byId[id] then return true end
	local w = Roster.wrapById[id]
	return w ~= nil and w.mastery == true
end
-- the camo's wrap name ("Mastery Gold") or the ladder's own word ("GOLD")
function M.camoName(id: string): string
	local c = M.byId[id]
	return if c then c.name else string.upper(id)
end
-- its picture is in the place, or a Studio test switched them all on
function M.live(id: string): boolean
	if not M.byId[id] then return false end
	if ReplicatedStorage:GetAttribute("MasteryLive") == true then return true end
	local lib = ReplicatedStorage:FindFirstChild("JankfireWraps")
	return lib ~= nil and lib:FindFirstChild(id) ~= nil
end
-- the camos a weapon at this level has earned, in order
function M.earned(level: number): { Camo }
	local out = {}
	for _, c in M.CAMOS do if level >= c.level then table.insert(out, c) end end
	return out
end
-- the next camo above this level, or nil (all four earned)
function M.nextCamo(level: number): Camo?
	for _, c in M.CAMOS do if c.level > level then return c end end
	return nil
end
-- the next LIVE camo above this level (what the bars show), or nil
function M.nextLive(level: number): Camo?
	for _, c in M.CAMOS do if c.level > level and M.live(c.id) then return c end end
	return nil
end
-- the camo unlocked by reaching exactly this level, or nil
function M.camoAt(level: number): Camo?
	for _, c in M.CAMOS do if c.level == level then return c end end
	return nil
end

-- ------------------------------------------------------------------ weapons
-- every weapon that levels: the live roster (guns, melee and gadgets: a gadget takes a wrap too)
function M.weapons(): { string }
	local out = {}
	for _, e in Roster.list do if e.live then table.insert(out, e.id) end end
	return out
end
function M.levels(wid: any): boolean
	local e = if type(wid) == "string" then Roster.byId[wid] else nil
	return e ~= nil and e.live == true
end
-- the loadout's WRAPS strip: every wrap of Roster.wraps, then the mastery camos (Roster.masteryWraps)
function M.wrapList(): { any }
	local out = table.clone(Roster.wraps)
	for _, w in (Roster.masteryWraps or {}) :: { any } do table.insert(out, w) end
	return out
end

-- ------------------------------------------------------------------ the attribute
-- { ar = 5120 } <-> "ar=5120;smg=40" (weapons with XP only, sorted)
function M.encode(map: { [string]: number }): string
	local keys = {}
	for k, v in map do if type(k) == "string" and (tonumber(v) or 0) > 0 then table.insert(keys, k) end end
	table.sort(keys)
	local parts = table.create(#keys)
	for i, k in keys do parts[i] = k .. "=" .. math.floor(tonumber(map[k]) or 0) end
	return table.concat(parts, ";")
end
function M.decode(s: any): { [string]: number }
	local out = {}
	if type(s) ~= "string" then return out end
	for k, v in string.gmatch(s, "([%w_]+)=(%d+)") do out[k] = tonumber(v) :: number end
	return out
end
-- a player's XP with a weapon, from their attribute (0 if none)
function M.xpOf(p: Player, wid: string): number
	return M.decode(p:GetAttribute("Mastery"))[wid] or 0
end

return M
