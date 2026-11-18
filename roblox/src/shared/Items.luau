--!strict
-- the utility slot (key G): every item in the web game (WEAPONS.md "Phase 2: ITEMS", "Items basics"), with the web
-- game's charges and recharge times exactly (the final values, after shared/weapons.js:570 gave the six gadgets
-- longer clocks and `carry`), and the numbers each one runs on. distances, speeds and accelerations in studs (x3 from
-- metres); times, damage, rates, counts and angles as they are. the server (Utility.luau) and your client
-- (Utility.client.luau) both read this. live = playable on roblox today (the rest are on the loadout screen as
-- "coming soon"); the batch they arrived in is in roblox/docs/BATCH-ITEMS.md
local S = 3
local Items = {}
Items.S = S

-- the loadout screen's order (web ITEM_ORDER, shared/weapons.js:368, plus radar and laptop pushed after it)
Items.ORDER = { "frag", "medkit", "bubble", "duck", "smoke", "popper", "reverse", "wand", "camera", "quiz", "nvg", "radar", "laptop" }
Items.DEFAULT = "frag" -- (web DEFAULT_LOADOUT.item)

Items.SPAM = 0.4 -- s between two uses the server accepts (web room.js useItem: 400 ms; the client waits 420)
Items.SPAM_CLIENT = 0.42
-- in training (the server's zone: the hall, its back lot and basement, the playground; Zones.luau) items cost nothing
-- and never recharge: only this short gap between two uses stays, so a held-down G can't flood the room (the owner,
-- 17 Nov 2026: "training room should also have no cooldown on stuff since its for training")
Items.SPAM_FREE = 0.2
Items.SPAM_FREE_CLIENT = 0.22
-- COOKING (the owner, 18 Nov 2026: "allow us to cook grenades pls"): the items with a fuse that only counts down (the
-- frag, the smoke bomb; the duck homes and sticks, the calculator hits: those stay as they are). G down pulls the pin
-- and the fuse starts on the server's clock; G up throws it with what is left. the first `grace` s are free, so a
-- tap throws with the whole fuse as before; past grace + fuse it goes off in your hand (the frag's blast hurts you
-- too: your own kill, nobody's credit). a cooked throw keeps at least `min` s of fuse
Items.COOK = { grace = 0.2, min = 0.05, ids = { frag = true, smoke = true } :: { [string]: boolean } }
Items.EYE = 4 * S -- a claimed throw point must be this close to the server's eye (and in clear sight of it), else the eye is used
Items.SWAP = 5.25 -- s into a life a new pick still lands at once (web selectItem: 5 s + a round trip, max 1 s)
Items.THROW = 0.7 * S -- thrown items leave this far along your look from the throw point (web makeProj call)

local function hex(h: string): Color3 return Color3.fromHex(h) end

export type Item = {
	id: string, name: string, color: Color3, desc: string, charges: number, recharge: number, carry: boolean?,
	keep: boolean?, live: boolean, proj: string?, feed: Color3?,
	heal: number?, healRate: number?, healMax: number?, -- the medkit
	dur: number?, r: number?, up: number?, -- the shield bubble (dome) and the smoke (cloud)
}
-- charges = the most you hold, recharge = seconds per charge (one comes back each time, until full). carry = a gadget:
-- its count and clock survive dying and swapping items. everything else is full again when you respawn
Items.list = {
	frag = { id = "frag", name = "Frag Grenade", color = hex("9ab04a"), feed = hex("7a8a3a"), charges = 2, recharge = 18, live = true, proj = "frag",
		desc = "Bounces, goes off 2.2 s after it leaves your hand. Knocks everyone near it flying, you too (you take no damage)." },
	medkit = { id = "medkit", name = "Medkit", color = hex("ff4f4f"), charges = 2, recharge = 20, live = true,
		heal = 45, healRate = 26, healMax = 100,
		desc = "Heals 45 over under two seconds, never past full. Keeps going while you're shot. Carry two." },
	bubble = { id = "bubble", name = "Shield Bubble", color = hex("4fd8ff"), charges = 1, recharge = 28, live = true,
		dur = 7, r = 4.4 * S, up = 1 * S,
		desc = "A dome for 7 s where you stand. Nothing from outside it can hurt anyone inside, enemies included." },
	duck = { id = "duck", name = "Rubber Duck", color = hex("ffd23b"), charges = 1, recharge = 20, live = true, proj = "duck",
		desc = "Homes in and sticks to an enemy. The black hole opens on them and follows them: their friends get dragged in, speed gets eaten, ropes snap. Then it pops." },
	smoke = { id = "smoke", name = "Smoke Bomb", color = hex("9aa0a8"), charges = 3, recharge = 14, live = true, proj = "smokegren",
		dur = 10, r = 6.5 * S,
		desc = "A thick cloud nobody can see through for 10 s." },
	popper = { id = "popper", name = "Party Popper", color = hex("ff6bd0"), charges = 2, recharge = 9, live = true,
		desc = "A confetti blast: everyone in front of you gets shoved away hard and you get launched backwards. Zero damage, all void kills and escapes." },
	reverse = { id = "reverse", name = "Reverse Card", color = hex("ff3b3b"), charges = 1, recharge = 22, live = true,
		desc = "For 1.8 s every bullet, blast and shove aimed at you goes back to whoever sent it. Everyone sees you flash it." },
	wand = { id = "wand", name = "Bubble Wand", color = hex("9fe8ff"), charges = 2, recharge = 32, carry = true, live = true,
		desc = "Blow a stream of soap bubbles. An enemy one touches is sealed in a giant bubble that floats up and away for 5 s, then pops and drops them. Over the void, that's your kill." },
	camera = { id = "camera", name = "Instant Camera", color = hex("c9a7ff"), charges = 1, recharge = 42, carry = true, live = true,
		desc = "G snaps a photo. G again prints it as a frame you can walk into: it puts you back where you took it. Anyone can use it." },
	quiz = { id = "quiz", name = "Pop Quiz", color = hex("7fffd4"), charges = 2, recharge = 40, carry = true, live = true, proj = "calc",
		desc = "Throw a calculator. Whoever it hits gets a maths question. Wrong or slow: dead. Right: gold star, HP and a shield." },
	nvg = { id = "nvg", name = "Night Vision Goggles", color = hex("3dff8a"), charges = 2, recharge = 28, carry = true, keep = true, live = true,
		desc = "G puts them on: the dark goes green, people glow. Middle click flashes everyone you can see." },
	radar = { id = "radar", name = "Speed Trap", color = hex("2e7bff"), charges = 2, recharge = 32, carry = true, live = true,
		desc = "Hold G to point a radar gun. Over 100 km/h: 3 s to slow down or jail. Over 200: jail on the spot." },
	laptop = { id = "laptop", name = "Laptop", color = hex("4fd8ff"), charges = 1, recharge = 42, carry = true, live = true,
		desc = "Open it at someone. Their screen fills with pop-up ads for 7 s. They can close them. There are a lot." },
} :: { [string]: Item }

-- the thrown ones (web shared/weapons.js WEAPONS.frag :262, smokegren :264): speed along your look, + up, + this
-- share of your own velocity; gravity, radius, how much of the speed into a surface comes back (no friction: what
-- runs along a surface keeps going, like the web game), the fuse from the throw, the most it lives
export type Proj = {
	speed: number, up: number, inherit: number, grav: number, r: number, bounce: number, fuse: number, life: number,
	radius: number?, dmg: number?, kb: number?, kbUp: number?,
}
Items.PROJ = {
	-- the frag's blast (room.js explodeAt): everyone within radius of the blast, through walls (web rule), takes
	-- dmg x (0.3 + 0.7 f) and a shove of kb x (0.4 + 0.6 f) away from it + kbUp x f up, f = 1 - dist / radius.
	-- the thrower: no damage, the whole shove (frag jumps)
	frag = { speed = 24 * S, up = 3 * S, inherit = 0.35, grav = 22 * S, r = 0.15 * S, bounce = 0.42, fuse = 2.2, life = 6,
		radius = 7.5 * S, dmg = 105, kb = 34 * S, kbUp = 6 * S },
	smokegren = { speed = 22 * S, up = 3 * S, inherit = 0.35, grav = 22 * S, r = 0.15 * S, bounce = 0.35, fuse = 1.3, life = 5 },
	-- the rubber duck (WEAPONS.duck :247): the fuse is when the hole opens where it is if it hasn't stuck to anyone
	duck = { speed = 22 * S, up = 3 * S, inherit = 0.35, grav = 22 * S, r = 0.3 * S, bounce = 0.45, fuse = 1.0, life = 6 },
	-- the pop quiz's calculator (WEAPONS.calc :263): thrown a bit softer, it hits the first enemy it touches; no fuse
	calc = { speed = 30 * S, up = 2 * S, inherit = 0.3, grav = 16 * S, r = 0.22 * S, bounce = 0.35, fuse = math.huge, life = 3.5 },
} :: { [string]: Proj }
-- the duck's homing, sticking and black hole (WEAPONS.duck, room.js duckFly / makeHole / tickHoles, player.js holeEat):
-- homes on the nearest enemy within homeR inside a cone (cos homeCos) of its flight, in sight, turning at most turn
-- rad/s, while faster than minSpeed. touching one (its radius + pad against their boxes) sticks: the hole opens ON them
-- stick s later and rides their middle. the hole lives holeTime s; every 0.1 s everyone within holeR is pulled toward
-- its middle by (pull (1 - d/R) + push0) x 0.1 x min(1, d/ramp) + lift x min(1, d/ramp) up, the one it's stuck to
-- takes stuckDmg, anyone within near takes nearDmg; then it pops (blastR, blastKb x (0.4 + 0.6 f) + blastUp x f,
-- blastDmg x f; the thrower: the shove, no damage). inside its radius your momentum is eaten (drag /s, x onDrag if
-- it's stuck to you) and a rope within snapR snaps
Items.DUCK = {
	homeR = 25 * S, homeCos = 0.5, turn = 3, minSpeed = 4 * S, pad = 0.1 * S, stick = 0.3,
	holeTime = 3, holeR = 15 * S, pull = 70 * S, push0 = 8 * S, lift = 1 * S, ramp = 1.5 * S, pulse = 0.1,
	stuckDmg = 1, near = 2 * S, nearDmg = 3,
	blastR = 9 * S, blastKb = 30 * S, blastUp = 8 * S, blastDmg = 45,
	drag = 6, onDrag = 0.5, snapR = 6 * S,
}
Items.CENTRE = 0.9 * S -- a person's centre over their feet (web room.js center): what a blast measures to
-- the party popper (web WEAPONS.popper :237): everyone within range of your eye and inside the cone of your look (any
-- angle that close: 1.5 m), in sight, gets kb along you -> them (feet to feet) + kbUp; you fly back recoil along
-- your look + lift up. no damage. the cone is judged against where each target is and was a moment ago (lag)
Items.POPPER = { range = 9 * S, cone = 0.6, close = 1.5 * S, kb = 50 * S, kbUp = 12 * S, recoil = 17 * S, lift = 5 * S }
-- the reverse card (web WEAPONS.reverse :242): for dur s every hit aimed at you goes back to whoever sent it. the web
-- game's 3 s cut by 40% (the owner, 18 Nov 2026: "can you nerf duration of reverse card"); charges and recharge as the web
Items.REVERSE = { dur = 1.8 }
-- the laptop (web ADS :558, server/ads.js): the enemy nearest your aim (their feet + aimUp) within range and the cone,
-- nothing solid closer than slack short of them; n pop-ups for dur s (sure of them come back once), then safe s before
-- the next laptop can reach them
Items.ADS = { range = 45 * S, cone = 0.3, aimUp = 1.1 * S, slack = 0.6 * S, n = 5, dur = 7, sure = 2, safe = 6 }
-- the night vision goggles (web NVG :490, server/gear.js nvFlash): G puts them on or off (free, at most every toggle
-- s; the server takes one every 0.7 of that), a flash (a charge) blinds everyone within range in the cone of your aim
-- (any angle within close) in clear sight (walls, smoke, domes stop it) for lerp(dur, k) s, k = how straight they
-- look at you, x nvMul if they wear goggles, x (1 - 0.3 dist / range)
Items.NVG = { range = 34 * S, cone = 0.62, close = 2 * S, dur = { 0.6, 3.2 }, nvMul = 2, toggle = 0.35 }
-- the pop quiz (web QUIZ :485, server/gear.js): time s to answer (+ slack), right = invuln s nothing hurts you, +heal
-- up to healMax, x fast run speed for fastT s; wrong or slow = dead. safe s before another quiz; held within hold of
-- the spot it hit you. bots (the dummies) get it right this often, after botT s
-- the speed trap (web SPEED :531, server/secondaries.js): hold G to point it; a reading every scan s on whoever is
-- under your crosshair within range and the cone (lag slack added), in sight (walls, smoke); the speed is the path
-- through the positions the server saw over the last window s. over limit km/h: a ticket (a charge): warn s to get
-- back under it or jail; over jail km/h: jail at once. jailT s in a cage, then safe s before the next ticket (warnSafe
-- after a warning). km/h are of metres: studs/s x 1.2. one ticket per shooter every gap s
Items.SPEED = { range = 70 * S, cone = 0.1, scan = 0.15, window = 0.5, limit = 100, jail = 200, warn = 3, grace = 0.5, jailT = 3.5,
	safe = 12, warnSafe = 4, gap = 0.9, kmh = 3.6 / S, drop = 40 * S }
-- the instant camera (web PHOTO :480, server/gear.js): the snap is free (a floor within drop under you, flat enough);
-- printing costs the charge: a frame stands at in front of you (pulled to wall off a wall) on the floor, facing you, for
-- life s. anyone whose feet are in its opening (w wide, depth deep, from 0.8 m under its foot to h - 0.6 m up), or who
-- crossed it since last tick within 3 m, goes through (each person once every cd s): to where the photo was taken,
-- facing the way it looked. whoever stands within frag (flat) and fragH (up) of that spot is telefragged
Items.PHOTO = { at = 1.9 * S, wall = 0.6 * S, life = 20, w = 1.8 * S, h = 2.1 * S, depth = 0.55 * S, cd = 1.6, frag = 0.9 * S, fragH = 1.6 * S,
	drop = 3 * S, cross = 3 * S, below = 0.8 * S, top = 0.6 * S }
-- the bubble wand (web ITEMS.wand, WEAPONS.soap, shared/wand.js): G blows 4 slow soap bubbles 0.09 s apart. the first
-- enemy one touches is sealed in a giant bubble (y over their feet, r across; a box of half box round it takes the
-- hits) that floats them rise up and drift along the way the bubble went for dur s, then pops and drops them. any hit
-- only pops it. after a pop: no new bubble for max(safe, safeK x how long they were in)
Items.SOAP = { speed = 11 * S, r = 0.4 * S, drag = 1.4, drift = 1 * S, lift = 0.25 * S, bob = 0.2 * S, sway = 0.25 * S, life = 4 }
Items.WAND = { bubbles = 4, gap = 0.09, dur = 5, rise = 2 * S, drift = 1.5 * S, safe = 1.5, safeK = 0.6, y = 1.14 * S, r = 1.38 * S, box = 1.1 * S,
	mouth = 0.15 * S, wall = 0.8 * S }
-- where a soap bubble is t s after it was blown: a formula, not a simulation, so the server (the hits) and every client
-- (the drawing) agree without syncing. it slows from the blow to a lazy drift the same way, floats up a little, and
-- bobs and sways out of step with its neighbours (seed = its id)
function Items.soapAt(p0: Vector3, v0: Vector3, seed: number, t: number): Vector3
	local w = Items.SOAP
	local hl = math.sqrt(v0.X * v0.X + v0.Z * v0.Z)
	local dx = if hl > 1e-6 then v0.X / hl else 0
	local dz = if hl > 1e-6 then v0.Z / hl else 0
	local D = Vector3.new(dx * w.drift, w.lift, dz * w.drift)
	local e = (1 - math.exp(-w.drag * t)) / w.drag
	local ph = seed * 2.39996
	local bob = w.bob * (math.sin(t * 4.2 + ph) - math.sin(ph))
	local sway = w.sway * (math.sin(t * 2.6 + ph * 1.7) - math.sin(ph * 1.7))
	return p0 + D * t + (v0 - D) * e + Vector3.new(-dz * sway, bob, dx * sway)
end
Items.QUIZ = { time = 6, slack = 0.15, invuln = 2.5, heal = 25, healMax = 125, fast = 1.25, fastT = 4, safe = 10, hold = 0.8 * S, bot = 0.7, botT = { 1.3, 4.2 } }

-- a pop quiz question (web makeQuestion, server/gear.js): one of ten kinds, small numbers, four options (the answer +
-- plausible wrongs), shuffled. returns the question, the options and the index of the right one (never sent out)
function Items.question(rnd: Random): (string, { number }, number)
	local function ri(a: number, b: number): number return rnd:NextInteger(a, b) end
	local kind = ri(0, 9)
	local q, a
	if kind <= 1 then local x, y = ri(12, 79), ri(11, 49); q, a = ("%d + %d"):format(x, y), x + y
	elseif kind == 2 then local x = ri(40, 99); local y = ri(11, x - 5); q, a = ("%d − %d"):format(x, y), x - y
	elseif kind <= 4 then local x, y = ri(3, 12), ri(3, 12); q, a = ("%d × %d"):format(x, y), x * y
	elseif kind == 5 then local y, a0 = ri(2, 9), ri(3, 12); q, a = ("%d ÷ %d"):format(a0 * y, y), a0
	elseif kind == 6 then local x, y, z = ri(2, 9), ri(2, 9), ri(2, 20); q, a = ("%d × %d + %d"):format(x, y, z), x * y + z
	elseif kind == 7 then local x = ri(2, 13); q, a = ("%d²"):format(x), x * x
	elseif kind == 8 then local x = ri(10, 60) * 2; q, a = ("half of %d"):format(x), x / 2
	else local x, y, z = ri(20, 60), ri(5, 19), ri(2, 15); q, a = ("%d − %d + %d"):format(x, y, z), x - y + z end
	-- wrong answers that look right: off by a bit, off by ten, digits swapped
	local opts = { a }
	local tries = { a + 1, a - 1, a + 2, a - 2, a + 10, a - 10, tonumber(string.reverse(tostring(a))) or a, a + ri(3, 9), a - ri(3, 9) }
	while #opts < 4 do
		local v
		if #tries > 0 then v = table.remove(tries, ri(1, #tries)) else v = a + ri(-20, 20) end
		if v and v >= 0 and v == math.floor(v) and not table.find(opts, v) then table.insert(opts, v) end
	end
	for i = #opts, 2, -1 do local j = ri(1, i); opts[i], opts[j] = opts[j], opts[i] end
	return q, opts, table.find(opts, a) :: number
end
Items.SHAKE = 25 * S -- the screen shakes 1 - dist / this on a blast (web main.js:1932)

-- ------------------------------------------------------------------ charges (web room.js itemCharges)
export type Ic = { i: string, n: number, next: number } -- next: when the next charge comes back (0 = the clock is stopped)
function Items.fresh(id: string): Ic
	return { i = id, n = Items.list[id].charges, next = 0 }
end
-- bring back every charge whose time has come
function Items.tick(c: Ic, now: number)
	local it = Items.list[c.i]
	while c.n < it.charges and c.next > 0 and now >= c.next do
		c.n += 1
		c.next = if c.n < it.charges then c.next + it.recharge else 0
	end
end
-- every charge back at once, no clock running (training)
function Items.refill(c: Ic)
	c.n = Items.list[c.i].charges
	c.next = 0
end
-- use one: the clock starts if it wasn't running
function Items.spend(c: Ic, now: number)
	c.n -= 1
	if c.next == 0 then c.next = now + Items.list[c.i].recharge end
end
-- swapping item mid-life (web selectItem): what you already used this life stays used
function Items.swapped(old: Ic, id: string, now: number): Ic
	local used = Items.list[old.i].charges - old.n
	local it = Items.list[id]
	return { i = id, n = math.max(0, it.charges - used), next = if used > 0 then now + it.recharge else 0 }
end

-- ------------------------------------------------------------------ the shield bubble (room.js inBubble / bubbleBlocks)
export type Bubble = { id: number, p: Vector3, r: number, untilT: number }
function Items.inBubble(b: Bubble, feet: Vector3): boolean
	return (feet + Vector3.new(0, Items.list.bubble.up :: number, 0) - b.p).Magnitude < b.r
end
-- is a hit on someone whose feet are at `tFeet` dropped? the attacker's feet (nil = damage with nobody behind it: then
-- `from`, where it came from). anyone inside a dome is safe from anyone outside it; inside the same one, fair game
function Items.blocks(bubbles: { Bubble }, tFeet: Vector3, aFeet: Vector3?, from: Vector3?): boolean
	if not aFeet and not from then return false end
	for _, b in bubbles do
		if not Items.inBubble(b, tFeet) then continue end
		if aFeet then
			if not Items.inBubble(b, aFeet) then return true end
		elseif ((from :: Vector3) - b.p).Magnitude >= b.r then
			return true
		end
	end
	return false
end

-- ------------------------------------------------------------------ smoke (room.js smokeBlocks)
-- does a cloud stand in the sight line a -> c (the line's closest point to a cloud's centre is inside it)
export type Cloud = { id: number, p: Vector3, r: number, untilT: number }
function Items.smokeBlocks(clouds: { Cloud }, a: Vector3, c: Vector3): boolean
	local d = c - a
	local l2 = d:Dot(d)
	if l2 < 1e-9 then l2 = 1 end
	for _, s in clouds do
		local k = math.clamp((s.p - a):Dot(d) / l2, 0, 1)
		if (a + d * k - s.p).Magnitude < s.r then return true end
	end
	return false
end

-- ------------------------------------------------------------------ flight (web shared/physics.js stepProjectile)
-- one step of a thrown item. cast(origin, radius, move) -> the distance the ball travels before it touches the map and
-- the surface normal there, or nil. a touch keeps the speed along the surface and sends back `bounce` of the speed into
-- it (the web game does this per axis against boxes; against Roblox's map it is done along the surface's normal).
-- returns how hard it hit something this step (the speed it had into the surface; 0 = it touched nothing, a few
-- studs/s = it is rolling along a floor)
export type Flying = { p: Vector3, v: Vector3, r: number, bounce: number, grav: number }
function Items.step(pr: Flying, dt: number, cast: (Vector3, number, Vector3) -> (number?, Vector3?)): number
	pr.v -= Vector3.new(0, pr.grav * dt, 0)
	local left = dt
	local hit = 0
	for _ = 1, 4 do
		local move = pr.v * left
		local len = move.Magnitude
		if len < 1e-5 then break end
		local d, n = cast(pr.p, pr.r, move)
		if not d or not n then pr.p += move; break end
		-- to the touch, a hair back off the surface (a sphere cast can't see a surface it starts inside)
		pr.p += move.Unit * math.max(0, d - 0.02) + n * 0.02
		local vn = pr.v:Dot(n)
		if vn < 0 then
			hit = math.max(hit, -vn)
			pr.v -= n * (vn * (1 + pr.bounce))
		end
		left *= math.max(0, 1 - d / len)
		if left < 1e-4 then break end
	end
	return hit
end

-- turn a velocity toward `to` by at most maxA radians, keeping its speed (web shared/physics.js steer)
function Items.steer(v: Vector3, to: Vector3, maxA: number): Vector3
	local sp, tl = v.Magnitude, to.Magnitude
	if sp < 1e-6 or tl < 1e-6 then return v end
	local a0, b = v / sp, to / tl
	local ang = math.acos(math.clamp(a0:Dot(b), -1, 1))
	if ang < 1e-4 then return v end
	local a, s = math.min(ang, maxA), math.sin(ang)
	if s < 1e-4 then return v end -- (flying straight away: no defined way to turn)
	local k0, k1 = math.sin(ang - a) / s, math.sin(a) / s
	return (a0 * k0 + b * k1) * sp
end

-- a black hole eats momentum (web shared/physics.js holeDrag): within R of c, the part of your velocity NOT falling
-- straight in decays by exp(-k f (2 - f) dt), f = 1 - d/R. `at` = your middle. returns the new velocity and the
-- distance to c (or nil outside)
function Items.holeDrag(at: Vector3, vel: Vector3, c: Vector3, R: number, k: number, dt: number): (Vector3, number?)
	local to = c - at
	local d = to.Magnitude
	if not (d < R) then return vel, nil end
	local f = 1 - d / R
	local keep = math.exp(-k * f * (2 - f) * dt)
	local u = if d > 0.5 * S then math.max(0, vel:Dot(to)) / (d * d) else 0
	local into = to * u
	return into + (vel - into) * keep, d
end

-- where a thrown item starts and how fast it leaves (web useItem -> makeProj): from the throw point o along the look d
function Items.launch(k: string, o: Vector3, d: Vector3, vel: Vector3): (Vector3, Vector3)
	local w = Items.PROJ[k]
	return o + d * Items.THROW, d * w.speed + Vector3.new(0, w.up, 0) + vel * w.inherit
end

return Items
