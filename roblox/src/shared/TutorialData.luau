--!strict
-- THE WEAPON TUTORIAL ROOMS' DATA (20 Nov 2026, the owner: "a room with a course that teraches you how to use each gun
-- ... a button you press it, it pulls up a menu with all the weapons select one, and itll place a small course or
-- shooting thingyu dpeending on what you picked to teach you how to use it"). One entry per weapon (and per move on the
-- MOVES tab): its course kind and that kind's numbers, 1-3 move names with their input, and its goal.
-- Tutorials.server builds a room's course from it; TutorialUI shows the moves, the goal and the result.
-- The moves come from the weapons' own sessions (side-session-notes TUTORIAL-MOVES.md): move names only, no flavour.
--
-- A room's frame (Origin, 6 in from its mouth, looking in): x across (+ = your right as you walk in, -18..18 usable),
-- z into the room (0..100; the back wall is at 104), y up from the floor.
-- An input "@id" is a key binding's id (Binds): the menu shows the player's own key for it ("@fire" = LMB unless rebound).
--
-- pieces (the course's solid parts, all drawn as the room's hologram):
--   { "box", x, z, w, h, d, y? }     a block: centre x, z; w across, h up, d deep; y its foot (0)
--   { "post", x, z, h }              a target's stand, h high (a Carl stands on it: give the target y = h)
--   { "bar", x, z, w, y }            a bar across at height y (slide under it)
--   { "gate", x, z, w, h? }          a frame to pass through (counted: the goal's gates)
--   { "ledge", x, z, w, h, d }       a block whose top is a goal spot (the goal's reach)
--   { "pit", x, z, w, d }            a floor you mustn't touch: on it, you go back to the course's start
-- targets (cardboard Carls, the room's user's alone):
--   { x, z, y?, rail = { span, speed }?, hop = true?, back = true?, hp = n?, turret = true? }
--   rail: walks span studs each way at speed; hop: bobs up and down; back: faces away (a backstab); turret: the
--   PRACTICE TURRET, a Carl that fires a short Redline burst at you every 3 s (real shots: the katana's guard, a
--   bubble, a reverse card and smoke work on it). It never goes down; what you send back into it counts as "turret"
-- goal (all of them must be met): kills, hits, heads (headshot hits), turret (hits on the turret: sent back to it),
--   gates (every gate passed), reach (on the ledge),
--   hp (your HP back up to n: the medkit), time (seconds: the clock to beat is only shown)
local D = {}

export type Entry = {
	kind: string,
	moves: { { string } },
	goal: { [string]: number | boolean },
	start: { hp: number? }?,
	pieces: { any }?,
	targets: { any }?,
}

-- ------------------------------------------------------------------ the course kinds
local K = {}
-- far posts at 20 / 26 / 32 m, one walking between them, low cover to lean on at the front
K.FAR = function(): ({ any }, { any })
	return {
		{ "box", -9, 14, 10, 3, 2 }, { "box", 9, 14, 10, 3, 2 },
		{ "post", -10, 60, 3 }, { "post", 9, 78, 5 }, { "post", -3, 96, 7 },
	}, {
		{ -10, 60, 3 }, { 9, 78, 5 }, { -3, 96, 7 }, { 0, 70, 0, rail = { 12, 8 } },
	}
end
-- walking and hopping targets at 10 / 15 / 20 m, two pillars to break the line
K.TRACK = function(): ({ any }, { any })
	return {
		{ "box", -14, 38, 3, 9, 3 }, { "box", 14, 52, 3, 9, 3 },
	}, {
		{ -4, 30, 0, rail = { 9, 12 } }, { 5, 45, 0, rail = { 11, 14 } }, { 0, 60, 0, rail = { 13, 16 }, hop = true },
	}
end
-- three walls round corners, a Carl just past each, close
K.CLOSE = function(): ({ any }, { any })
	return {
		{ "box", -7, 14, 9, 9, 2 }, { "box", 7, 24, 9, 9, 2 }, { "box", -7, 34, 9, 9, 2 },
	}, {
		{ -13, 16 }, { 13, 26 }, { -13, 36 }, { 0, 44 },
	}
end
-- two groups of three, each behind a low wall
K.SPLASH = function(): ({ any }, { any })
	return {
		{ "box", -8, 20, 14, 3, 2 }, { "box", 8, 38, 14, 3, 2 },
	}, {
		{ -11, 24 }, { -8, 25.5 }, { -5, 24 }, { 5, 42 }, { 8, 43.5 }, { 11, 42 },
	}
end
-- a wall in the middle and two side walls: what's behind them only a bounce reaches
K.BOUNCE = function(): ({ any }, { any })
	return {
		{ "box", 0, 22, 16, 10, 2 }, { "box", -11, 44, 2, 10, 16 }, { "box", 11, 62, 2, 10, 16 },
	}, {
		{ -3, 30 }, { 3, 31 }, { -16, 46 }, { 16, 64 },
	}
end
-- three Carls to walk up to (melee)
K.MELEE = function(): ({ any }, { any })
	return {}, { { -5, 12 }, { 5, 20 }, { 0, 30 } }
end
-- the knife: three with their backs to you
K.BACKS = function(): ({ any }, { any })
	return {
		{ "box", 0, 22, 12, 4, 2 },
	}, { { -6, 14, 0, back = true }, { 6, 30, 0, back = true }, { 0, 40, 0, back = true, rail = { 8, 4 } } }
end
-- the scythe: three gates in a zigzag, a post to latch, three Carls past it
K.DASH = function(): ({ any }, { any })
	return {
		{ "gate", 0, 16, 8 }, { "gate", -9, 32, 8 }, { "gate", 8, 48, 8 }, { "box", 0, 64, 3, 16, 3 },
	}, { { -6, 74 }, { 6, 80 }, { 0, 88 } }
end
-- a ledge too high to jump: get up there with the weapon (the shotgun's floor shot, the bread's pogo), Carls on it
K.LAUNCH = function(): ({ any }, { any })
	return {
		{ "ledge", 0, 40, 18, 12, 12 },
	}, { { -4, 43, 12 }, { 4, 45, 12 }, { 0, 58 } }
end
-- a group of three, close, in the open (most gadgets)
K.GROUP = function(): ({ any }, { any })
	return {
		{ "box", -12, 30, 3, 6, 3 }, { "box", 12, 30, 3, 6, 3 },
	}, { { -3, 22 }, { 0, 24 }, { 3, 22 } }
end
-- one fast walker (the speed trap, the wand)
K.RUNNER = function(): ({ any }, { any })
	return {}, { { 0, 30, 0, rail = { 15, 22 } } }
end
-- the katana: the turret on a post ahead, three Carls beside its line
K.PARRY = function(): ({ any }, { any })
	return {
		{ "post", 0, 40, 4 },
	}, { { 0, 40, 4, turret = true, hp = 99999 }, { -9, 18 }, { 9, 24 }, { -6, 30 } }
end
-- a dome to stand in: the turret on a post, a group of three in front of it (the bubble, the reverse card)
K.DOME = function(): ({ any }, { any })
	return {
		{ "post", 0, 46, 4 }, { "box", -14, 26, 3, 6, 3 }, { "box", 14, 26, 3, 6, 3 },
	}, { { 0, 46, 4, turret = true, hp = 99999 }, { -4, 30 }, { 0, 32 }, { 4, 30 } }
end
-- the turret watches a long open floor up to a ledge (the smoke)
K.GUNLINE = function(): ({ any }, { any })
	return {
		{ "post", 0, 96, 6 }, { "ledge", 0, 72, 16, 3, 10 }, { "box", -10, 40, 6, 4, 2 }, { "box", 10, 52, 6, 4, 2 },
	}, { { 0, 96, 6, turret = true, hp = 99999 } }
end
-- nothing to shoot: a room to use it in (the medkit)
K.EMPTY = function(): ({ any }, { any })
	return {}, {}
end
-- the grapple: a tower to get on top of, two walls on the way to swing from
K.GRAPPLE = function(): ({ any }, { any })
	return {
		{ "box", -12, 30, 4, 18, 8 }, { "box", 12, 46, 4, 18, 8 }, { "ledge", 0, 76, 14, 20, 14 },
	}, {}
end
-- slides: two bars to slide under, then a gap only a slide jump clears, onto the end ledge
K.SLIDE = function(): ({ any }, { any })
	return {
		{ "bar", 0, 18, 30, 3.4 }, { "bar", 0, 32, 30, 3.4 },
		{ "box", 0, 52, 20, 2, 10 }, { "pit", 0, 66, 36, 18 }, { "ledge", 0, 82, 20, 2, 12 },
	}, {}
end
D.KINDS = K

-- ------------------------------------------------------------------ the entries
local W: { [string]: Entry } = {}
local function e(id: string, kind: string, moves: { { string } }, goal: { [string]: number | boolean }, x: any?)
	local t: any = { kind = kind, moves = moves, goal = goal }
	if x then for k, v in x do t[k] = v end end
	W[id] = t
end
-- FAR
e("sniper", "FAR", { { "SCOPE", "@aim" }, { "HEADSHOT", "ALWAYS KILLS" }, { "BODY SHOT", "KNOCKS THEM FLYING" } }, { kills = 4, heads = 3 })
e("dmr", "FAR", { { "QUICK SCOPE", "FIRE IN 0.3 S OF @aim" }, { "HEADSHOT", "ONE TO THE HEAD" } }, { kills = 6 })
e("lever", "FAR", { { "CRANK", "AFTER EVERY SHOT" }, { "CHAIN", "SAME TARGET, UP TO X1.45" } }, { kills = 5 })
e("bow", "FAR", { { "DRAW", "HOLD @fire, LET GO" }, { "TIPS", "A RANDOM TIP EACH ARROW" }, { "ARC", "AIM ABOVE THE FAR ONES" } }, { hits = 5 })
e("laser", "FAR", { { "CHARGE", "HOLD @fire, LET GO" }, { "TAP", "A SHORT WEAK BEAM" }, { "LINE UP", "ONE BEAM GOES THROUGH" } }, { kills = 5 })
e("revolver", "FAR", { { "TAP", "@fire" }, { "FAN", "HOLD @fire" }, { "BANK", "OFF A WALL" } }, { kills = 6 })
-- TRACK
e("ar", "TRACK", { { "ADS", "@aim" } }, { kills = 3 })
e("smg", "TRACK", { { "RUN AND GUN", "MOVE WHILE YOU FIRE" } }, { kills = 3 })
e("lmg", "TRACK", { { "BELT", "100 ROUNDS" }, { "HEAT", "THE BARREL GLOWS" }, { "SLOW AIM", "@aim" } }, { kills = 4 })
e("minigun", "TRACK", { { "SPIN UP", "HOLD @fire 0.6 S" }, { "SHOVE", "THE BULLETS PUSH" }, { "RECOIL FLY", "AIM DOWN AND HOLD" } }, { kills = 3 })
e("burst", "TRACK", { { "BURST", "ALL 3 ON ONE" } }, { kills = 3 })
e("redline", "TRACK", { { "LOW HP", "FIRES FASTER" } }, { kills = 3 }, { start = { hp = 40 } })
e("pistol", "TRACK", { { "TAP", "AS FAST AS YOU CLICK" }, { "SLIDE LOCK", "@reload WHEN EMPTY" } }, { kills = 3 })
e("akimbo", "TRACK", { { "LEFTY", "@fire" }, { "RIGHTY", "@aim" }, { "BOTH", "HOLD BOTH" } }, { kills = 3 })
e("nailgun", "TRACK", { { "PIN", "6 IN A ROW IN 1.2 S" } }, { kills = 3 })
e("water", "TRACK", { { "SOAK", "SLOWER AND SLIPPERY" } }, { hits = 6 })
e("taser", "TRACK", { { "STUN", "1 S" }, { "CHAIN", "THROUGH THE SOAKED" } }, { hits = 3 })
e("snowball", "TRACK", { { "FREEZE", "4 HITS" }, { "SHATTER", "ONE MORE" } }, { kills = 2 })
e("remote", "TRACK", { { "PAUSE", "@fire, 1.2 S" }, { "REWIND", "@aim, BACK 2 S" } }, { hits = 4 })
-- CLOSE
e("shotgun", "LAUNCH", { { "10 PELLETS", "@fire" }, { "FLOOR LAUNCH", "SHOOT THE FLOOR" } }, { kills = 3, reach = true })
e("autoshot", "CLOSE", { { "HOLD TO FIRE", "@fire" } }, { kills = 4 })
e("sawnoff", "CLOSE", { { "POINT BLANK", "@fire" }, { "FLOOR HOP", "SHOOT THE FLOOR" } }, { kills = 4 })
e("marbles", "CLOSE", { { "100 MARBLES", "POINT BLANK ONE-SHOTS" }, { "FLOOR TRAP", "MISSES TRIP THEM" } }, { kills = 4 })
e("cig", "CLOSE", { { "SWIG", "HOLD @fire" }, { "BREATHE FIRE", "LET GO" }, { "TOO LONG", "BURNS YOU" } }, { kills = 3 })
e("blower", "CLOSE", { { "PUSH", "HOLD @fire" }, { "HOVER", "AIM AT THE FLOOR" } }, { hits = 4 })
e("shredder", "CLOSE", { { "SUCK IN", "HOLD @fire" }, { "OVERHEAT", "4 S" } }, { kills = 3 })
e("slapper", "MELEE", { { "SLAP", "POINT BLANK" } }, { hits = 3 })
-- SPLASH
e("chicken", "SPLASH", { { "SPLASH", "@fire" }, { "BACK-BLAST", "EVERY SHOT KICKS YOU" }, { "ROCKET JUMP", "SHOOT YOUR FEET" } }, { kills = 6 })
e("frag", "SPLASH", { { "THROW", "@item" }, { "FUSE", "2.2 S, OFF WALLS" }, { "FRAG JUMP", "IT THROWS YOU TOO" } }, { kills = 3 })
e("popper", "GROUP", { { "CONFETTI", "@item, NO DAMAGE" }, { "LAUNCH", "YOU FLY BACK" } }, { hits = 3 })
e("bowling", "SPLASH", { { "ROLL", "ALONG THE FLOOR" } }, { kills = 6 })
e("cart", "SPLASH", { { "RAM", "@fire" }, { "COVER", "IT STAYS" }, { "RIDE", "@ride" } }, { kills = 3 })
-- BOUNCE
e("tennis", "BOUNCE", { { "BANK", "UP TO 5 BOUNCES" } }, { hits = 4 })
e("slipper", "BOUNCE", { { "BOOMERANG", "CURVES IN, COMES BACK" } }, { hits = 4 })
e("banana", "TRACK", { { "BONK", "THEY SLIP" }, { "PEEL", "MISSES STAY 12 S" } }, { hits = 4 })
e("cards", "GROUP", { { "PICK", "@aim" }, { "PLAY", "@fire" }, { "DRAW", "@reload" } }, { hits = 4 })
-- MELEE
e("katana", "PARRY", { { "GUARD", "HOLD @aim" }, { "CRIT RETURN", "@fire AS BULLETS ARRIVE" }, { "SLASH WAVE", "@wave WHEN FULL" } }, { turret = 3, kills = 3 })
e("knife", "BACKS", { { "SLASH", "@fire" }, { "STAB", "@aim" }, { "BACKSTAB", "FROM BEHIND" } }, { kills = 3 })
e("bread", "LAUNCH", { { "HOME RUN", "@fire" }, { "POGO", "SMACK THE FLOOR" } }, { hits = 3, reach = true })
e("scythe", "DASH", { { "REAP", "@fire" }, { "DASH", "@aim" }, { "RIFLE", "@form" } }, { gates = 3, kills = 3 })
-- GADGETS
e("medkit", "EMPTY", { { "HEAL", "@item, 45 IN 2 S" }, { "CARRY TWO", "" } }, { hp = 85 }, { start = { hp = 40 } })
e("bubble", "DOME", { { "DOME", "@item, 7 S" } }, { kills = 3 })
e("duck", "GROUP", { { "STICK", "@item" }, { "BLACK HOLE", "DRAGS THEM IN" } }, { hits = 3 })
e("smoke", "GUNLINE", { { "CLOUD", "@item, 10 S" } }, { reach = true })
e("reverse", "DOME", { { "REVERSE", "@item, 1.8 S" } }, { turret = 3 })
e("wand", "RUNNER", { { "BUBBLES", "HOLD @item" }, { "SEAL", "FLOATS THEM 5 S" } }, { hits = 2 })
e("camera", "RUNNER", { { "SNAP", "@item" }, { "PRINT", "@item AGAIN" }, { "WALK IN", "PUTS THEM BACK" } }, { hits = 1 })
e("quiz", "GROUP", { { "THROW", "@item" } }, { hits = 1 })
e("nvg", "GROUP", { { "NIGHT VISION", "@item" }, { "FLASH", "@flash" } }, { hits = 3 })
e("radar", "RUNNER", { { "RADAR", "HOLD @item" }, { "OVER 100", "3 S TO SLOW" } }, { hits = 1 })
e("laptop", "GROUP", { { "POP-UPS", "@item AT SOMEONE" } }, { hits = 1 })
e("overdrive", "GROUP", { { "SUIT UP", "@item, 12 S" }, { "ROCKET PUNCH", "HOLD @fire" }, { "MISSILES", "@aim" } }, { kills = 3 })
-- MOVES (no weapon: the movement itself)
e("move:grapple", "GRAPPLE", { { "GRAPPLE", "HOLD @grapple AT A WALL" }, { "GRAPPLE JUMP", "SPACE ON THE ROPE" } }, { reach = true })
e("move:slide", "SLIDE", { { "SLIDE", "@crouch WHILE FAST" }, { "SLIDE JUMP", "SPACE IN A SLIDE" }, { "BHOP", "JUMP AS YOU LAND" } }, { reach = true })
D.W = W
D.MOVES = { { id = "move:grapple", name = "GRAPPLE" }, { id = "move:slide", name = "SLIDE & JUMP" } }

-- the menu's tabs, in order: the Roster's slots, then the moves
D.TABS = { { "primary", "PRIMARY" }, { "secondary", "SECONDARY" }, { "melee", "MELEE" }, { "utility", "GADGETS" }, { "moves", "MOVES" } }

-- an entry's course: its pieces and targets (its own, or its kind's)
function D.course(id: string): ({ any }, { any })
	local en = W[id]
	if not en then return {}, {} end
	local pieces, targets = K[en.kind]()
	return (en.pieces or pieces), (en.targets or targets)
end

-- the goal in words, from counts so far (nil = none yet): "KILLS 2/6 · HEADSHOTS 1/3"
local GOAL_WORDS = { kills = "DOWN", hits = "HITS", heads = "HEADSHOTS", turret = "SENT BACK", gates = "GATES", reach = "REACH THE TOP", hp = "HP" }
local ORDER = { "turret", "kills", "heads", "hits", "gates", "hp", "reach" }
function D.goalText(goal: { [string]: any }, got: { [string]: any }?): string
	local parts = {}
	for _, k in ORDER do
		local need = goal[k]
		if need == nil then continue end
		local have = got and got[k]
		if k == "reach" then
			table.insert(parts, if have then "ON TOP" else GOAL_WORDS.reach)
		elseif k == "hp" then
			table.insert(parts, ("HP %d/%d"):format(math.floor(tonumber(have) or 0), need :: number))
		else
			table.insert(parts, ("%s %d/%d"):format(GOAL_WORDS[k], math.min(tonumber(have) or 0, need :: number), need :: number))
		end
	end
	return table.concat(parts, "  ·  ")
end
-- is the goal met?
function D.met(goal: { [string]: any }, got: { [string]: any }): boolean
	for k, need in goal do
		if k == "time" then continue end
		local have = got[k]
		if k == "reach" then if not have then return false end
		elseif (tonumber(have) or 0) < (need :: number) then return false end
	end
	return true
end

return D
