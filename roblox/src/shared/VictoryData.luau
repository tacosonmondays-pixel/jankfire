--!strict
-- THE VICTORY SCENE's numbers and rules (27 Nov 2026, the owner: "when you win in rivals, it plays a small cinematic that
-- shows off your characters doing like an action ... then it displays your stats and then if your teammates are there,
-- they appear behind ... If you have the custom cinematic finishers it replaces the default!"). Plan and decisions:
-- side-session-notes .../victory-scene/PLAN.md. Every match end: the winning side at the map's own victory spot (the
-- owner: "the victory screen will depend on the map! itll be a preloaded scene just placing our characters in!"; a
-- "Victory" model in the arena, server/VictoryServer.server.luau reads it) or, where a map has none yet, on THE RISER (a
-- set of our own, client-built far off the map: client/VictoryScene.luau); the best-ranked in front doing their emote
-- (else a mocap victory pose), teammates behind, ~5 s with our own camera; then the stats card (client/VictoryCard.luau,
-- A PLATE) over the held shot. The best-ranked winner with a scene finisher equipped plays theirs against the enemy's
-- best instead (FinisherServer's Matches.endFinisher), then the card.
local V = {}

V.ON = true -- the switch: false = no scene and no card (FightHud's old end screen, as before 27 Nov)
V.LEN = 5.0 -- s, the default scene (the end screen and the trip home wait for it: m.finisherUntil)
V.SLACK = 0.6 -- s on top of LEN for the hold: the payload's trip, the bodies built
V.SKIP_AFTER = 2.0 -- s before a viewer may skip to the card
V.MATES = 3 -- teammates on the riser at most (4v4: three behind the one in front)
V.CINE_WINDOW = 15 -- s: a FinisherServer hold this fresh (m.finisherFrom) means its cinematic is this match's end

-- the victory poses: Mixamo mocap (vault Assets\mixamo-20nov-emotes, converted with tools/blender/mixamo_r15.py for R15
-- and --r6, merged into one upload each by merge_r15_r6.py: one id plays on both bodies). never hand-posed
V.POSES = {
	victory = { anim = "rbxassetid://114557290874118", len = 8.53 }, -- 110 Victory: celebrating after a win
	pump = { anim = "rbxassetid://116343615193002", len = 3.8 }, -- 105 Fist Pump
	cheer = { anim = "rbxassetid://137626299809553", len = 2.9 }, -- 100 Cheering, two fists
	idle1 = { anim = "rbxassetid://113793177482452", len = 1.87 }, -- 112 Victory Idle
	idle2 = { anim = "rbxassetid://137233841835376", len = 1.67 }, -- 113 Victory Idle
	idle3 = { anim = "rbxassetid://89818155764325", len = 1.8 }, -- 114 Victory Idle
}
V.HERO_POSES = { "victory", "pump" } -- the one in front, when they have no emote of their own
V.MATE_POSES = { "idle1", "idle2", "idle3", "cheer" } -- teammates: each a different one where it can be

-- the emote wheel's own defaults (shared/Flair F.DEFAULT.emotes): a wheel slot holding one of these isn't a pick
local DEFAULTS = { wave = true, hello = true, salute = true, point = true, shrug = true, cheer = true, laugh = true, dance = true }
V.DEFAULTS = DEFAULTS

-- the emote a player shows off: the first slot of their wheel (player attribute "Emotes", "a,b,,c") that isn't one of the
-- defaults. nil = none picked: they get a victory pose
function V.emoteOf(wheel: any): string?
	if type(wheel) ~= "string" then return nil end
	for _, id in string.split(wheel, ",") do
		if id ~= "" and not DEFAULTS[id] then return id end
	end
	return nil
end

-- a stable pick from a list for a player (the same body gets the same pose every time), skipping ones already used
function V.pick(list: { string }, uid: number, used: { [string]: boolean }?): string
	local n = #list
	local start = (math.abs(math.floor(uid)) % n) + 1
	for i = 0, n - 1 do
		local id = list[(start - 1 + i) % n + 1]
		if not used or not used[id] then return id end
	end
	return list[start]
end

-- THE RANKING (the owner, 27 Nov: "the person who did the best has theirs play against the enemy best"): one order
-- drives the one in front, the teammates behind, the finisher that plays and its victim. Team modes: most kills, then
-- most damage, then most assists, then fewest deaths, then the lower UserId. Classic modes: the mode's own result order
-- first (row.order, m.results: place then its score), then the same. rows: { uid, k, d, a, dmg, order? }
function V.better(a: any, b: any): boolean
	if a.order and b.order and a.order ~= b.order then return a.order < b.order end
	if a.k ~= b.k then return a.k > b.k end
	if a.dmg ~= b.dmg then return a.dmg > b.dmg end
	if a.a ~= b.a then return a.a > b.a end
	if a.d ~= b.d then return a.d < b.d end
	return a.uid < b.uid
end
function V.rank(rows: { any }): { any }
	table.sort(rows, V.better)
	return rows
end

return V
