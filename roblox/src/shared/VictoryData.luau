--!strict
-- THE VICTORY SCENE's numbers and rules (27 Nov 2026, the owner: "when you win in rivals, it plays a small cinematic that
-- shows off your characters doing like an action ... then it displays your stats and then if your teammates are there,
-- they appear behind ... If you have the custom cinematic finishers it replaces the default!"). Plan and decisions:
-- side-session-notes .../victory-scene/PLAN.md. Every match end: the winning side at the map's own victory spot (the
-- owner: "the victory screen will depend on the map! itll be a preloaded scene just placing our characters in!"; a
-- "Victory" model in the arena, server/VictoryServer.server.luau reads it) or, where a map has none yet, on THE RISER (a
-- set of our own, client-built far off the map: client/VictoryScene.luau); the best-ranked walks up at a low wide lens
-- and lands a mocap pose, teammates walk in behind and land theirs (no emotes since 27 Nov: V.ARRIVE), ~5.6 s with our
-- own camera; then the stats card (client/VictoryCard.luau, A PLATE) over the held shot. The best-ranked winner with a scene finisher equipped plays theirs against the enemy's
-- best instead (FinisherServer's Matches.endFinisher), then the card.
local V = {}

V.ON = true -- the switch: false = no scene and no card (FightHud's old end screen, as before 27 Nov)
V.LEN = 5.6 -- s, the default scene (the end screen and the trip home wait for it: m.finisherUntil)
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
-- (27 Nov, main from the v1436 sheet: "the heroes stand flat, holding the gun loosely at the hip ... read as idle, not a
-- win". Picked from a stick-figure sheet of 21 vault clips with the gun drawn along the forearm, as it is gripped:
-- scratchpad victory/poses) the one in front: a fighter's guard with the gun up by the face, or both arms up;
-- teammates: a cheer with the gun up, an aim, a low crouch, a lean; one sits on THE RISER's edge
V.POSES.fight = { anim = "rbxassetid://77302336464454", len = 3.3 } -- 18nov boxing 17 Idle Fight Stance
V.POSES.armsup = { anim = "rbxassetid://83482891664740", len = 2.03 } -- 20nov 111 Victory (boxing win), frames 31-91
V.POSES.aim = { anim = "rbxassetid://130770662917652", len = 2.33 } -- 19nov 09 Pistol Aim, frames 1-70
V.POSES.crouch = { anim = "rbxassetid://82585229078770", len = 0.13 } -- 19nov 04 Crouched To Sprint, frames 1-4 (held)
V.POSES.lean = { anim = "rbxassetid://76710822124387", len = 0.07 } -- 20nov 92 Pose Leaning Right (held)
V.POSES.sitledge = { anim = "rbxassetid://126271088986263", len = 2.1, sit = true } -- 17nov 01 Sit Swing Legs (a ledge)

-- THE WALK-UP (27 Nov, the owner: "Instead of an emote on the example victory you should be can it be a walk up into a
-- dynamic pose with a perspective shot?"). no emotes: everyone walks in and lands a pose. the poses that land are the
-- "move into a pose" stretches of vault mocap (20nov emotes, --no-loop: played once, held on their last frame, once =
-- true), picked from the stick-figure sheet: the charge's arm thrust (the weapon comes at the lens), the victory's arms
-- flung up, the rally's arm straight up, the fist pump's rise to its peak
V.POSES.chargein = { anim = "rbxassetid://117066882633761", len = 1.067, once = true } -- 127 Charge, frames 8-40
V.POSES.victoryup = { anim = "rbxassetid://79243821608278", len = 0.833, once = true } -- 110 Victory, frames 35-60
V.POSES.rallyup = { anim = "rbxassetid://139755019138832", len = 1.2, once = true } -- 102 Rallying, frames 90-126
V.POSES.pumpup = { anim = "rbxassetid://100266320103476", len = 0.6, once = true } -- 105 Fist Pump, frames 12-30
V.HERO_POSES = { "chargein", "victoryup" } -- the one in front
V.MATE_POSES = { "rallyup", "pumpup", "aim", "cheer" } -- teammates: each a different one where it can be
-- (until the owner's Mixamo clips come - a confident walk, a walk holding a gun: side-session-notes MIXAMO-CLIPS-NEEDED -
-- the walk is Roblox's own, its feet kept on the floor by the distance walked)
V.ARRIVE = {
	idle = "rbxassetid://507766388", idle6 = "rbxassetid://180435571", -- Roblox's own idles (R15, R6): before a late start
	speed = 5.2, mateSpeed = 4.6, -- studs/s walking in (they slow to a stop on their mark)
	stride = 6.8, -- studs walked per second of Roblox's walk clip at speed 1 (V.WALK: 4.2 studs/s at 0.62)
	hero = 8, mate = 5.5, -- studs back from their mark each starts, at most (rays: a wall or an edge behind cuts it)
	riserHero = 5.5, riserMate = 1.8, -- THE RISER: the stage's own depth; the riser's top
	minArrive = 1.3, -- s: the one in front never lands sooner (a short walk starts late, from an idle)
	stagger = 0.2, -- s between one landing and the next
	blend = 0.28, -- s from the walk into the pose (it starts 0.12 s before the stop)
}

-- THE WALK (a map's walk spot: the Spooky Forest, 27 Nov - "make them walk in the forest scared as the screen
-- distorts"). Until the owner's Mixamo clips come (Sneak Walk, Scared, Look Over Shoulder, Startled: main's list), real
-- mocap we have: Roblox's own walk, slowed, under upper-body layers (vault 18nov 17 Fight Stance --upper for the one in
-- front, the gun up nervously; 17nov 07 Frisk Look Around --upper for teammates glancing back), and 18nov 24 Hit Head Big
-- as the startle. Swap the ids when the clips arrive
V.WALK = {
	walk = "rbxassetid://507777826", -- (Roblox's default R15 walk)
	walk6 = "rbxassetid://180426354", -- (Roblox's default R6 walk)
	speed = 4.2, -- studs/s along the path
	animSpeed = 0.62, -- the walk clip slowed to the pace
	guard = "rbxassetid://123801588707582", -- upper body: the boxing guard, gun up by the face
	look = "rbxassetid://72083974683735", -- upper body: the look-around, glancing back
	startle = "rbxassetid://77302336464454", -- at the stinger they snap into a guard, the weapon up by the face (V.POSES.fight;
	-- 18nov 24 Hit Head Big put them on the floor: Studio v1458)
	startleAt = 1.0, -- s before the walk's end
	-- teammates huddle close behind the one in front: (right, back) in the path's frame
	mates = { Vector2.new(1.7, 2.5), Vector2.new(-1.8, 2.7), Vector2.new(0.3, 4.5) },
}

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
