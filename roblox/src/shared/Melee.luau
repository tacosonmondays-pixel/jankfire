--!strict
-- MELEE THAT CAN CLOSE THE GAP (26 Nov 2026). The owner: "Multiple people have pointed out melee feels useless I can
-- kinda gree! other than the sliper which is kinda op the rest of the melee weapons arent very forgiving thats why I
-- wanted to maybe try a better reel in or pull to help close gaps on players to actually utilize the melee weapons!"
-- (and on 21 Nov: "How do we make the melee weapons better?"). docs/MELEE.md has the whole account. This module holds
-- the numbers the client and the server share, and the pure hit maths:
--   * the LUNGE: a short dash at the person under your crosshair (Binds "lunge", Z / a pad's RS with a melee weapon out
--     / the phone's LUNGE; also right click on a melee weapon that has no right-click move of its own). client:
--     MeleeLunge.luau; server: MeleeLunge.server.luau (the say-so, the cooldown, the anti-cheat's ACGrace)
--   * the run with a melee weapon out: SPEED x on top of the weapon's own speedMul (Arsenal)
--   * the forgiving swing (HIT): a body is a column from the feet up HIT.top, HIT.radius wide; a swing reaches the
--     column's nearest point, and it looks back along the swing (from the press to the hit) for where they were
--   * the first swing after a REEL onto someone (REEL_HIT): a little more reach and damage for a short window
-- The Slipper (a throw) is left alone on purpose (the owner: "other than the sliper which is kinda op"), and the
-- Scythe's rifle form is a gun: neither is "swung".
local S = 3

local Melee = {}

-- a swung weapon: kind "melee" (the Katana, Knife, Bread, Scythe, Scales, Hand Slapper; the infection Claw too)
function Melee.swung(w: any): boolean
	return type(w) == "table" and w.kind == "melee"
end
-- a loadout melee (the speed bonus is for these; the infection Claw already runs x1.3)
function Melee.loadout(w: any): boolean
	return Melee.swung(w) and w.slot == "melee"
end
-- right click already does something with this one: the Katana's guard, the Knife's stab, the Scythe's dash, the
-- Scales' pillar. those lunge on the LUNGE key only; the rest (Bread, Hand Slapper, Claw) on right click too
function Melee.ownRight(w: any): boolean
	return type(w) == "table" and (w.id == "katana" or w.heavy ~= nil or w.dash ~= nil or w.gavel ~= nil)
end

-- run speed x this with a loadout melee weapon out (on top of its own speedMul: the Knife's 1.1, the Scythe's 0.95)
Melee.SPEED = 1.08

-- the lunge
Melee.LUNGE = {
	range = 22, -- studs, your chest to theirs: the farthest a lunge reaches (the brief: "within about 20 studs")
	near = 4.5, -- it stops this far off them: inside every swing's reach (the Hand Slapper's is 5.7)
	cone = 12, -- degrees round the crosshair they have to be in
	speed = 95, -- studs/s (a sprint is 43.5, a slide jump 60): 22 studs in about 0.2 s
	time = 0.3, -- s at most
	up = 35, -- degrees: at most this much up or down toward them (never down into the floor you stand on)
	keep = 0.15, -- of its speed carries on when it ends: a lunge, not a launch (0.4 carried you 3 studs into them, 26 Nov test)
	cd = 4, -- s
	slack = 8, -- studs past range the server allows (lag: they moved on its copy)
}

-- the forgiving swing: a body as a column (feet + 0 .. top, radius), and how far back along the swing to look
Melee.HIT = {
	top = 5.3, -- studs over the feet (an R15 head's top is 5.27)
	radius = 1.2, -- studs: half a body's width
	early = 0.05, -- s before the press the look back starts (a press a frame late still counts what you saw)
}

-- the first swing after a reel brings you onto someone (Config.hook reel; Main.server's "reeled"): within window s of
-- arriving, the next swing reaches `reach` studs further and hits x dmg. one swing only, hit or miss
Melee.REEL_HIT = { window = 0.8, reach = 3, dmg = 1.2 }

-- the point of a body's column (feet .. feet + top) nearest the line from eye along look (look a unit vector)
function Melee.bodyPoint(eye: Vector3, look: Vector3, feet: Vector3, top: number?): Vector3
	local L = top or Melee.HIT.top
	local b = look.Y -- (the column runs straight up)
	local w0 = feet - eye
	local dd, e = w0.Y, look:Dot(w0)
	local s: number
	local denom = 1 - b * b
	if denom < 1e-4 then
		s = eye.Y - feet.Y -- (looking straight up or down: the column's point at eye height)
	else
		s = (b * e - dd) / denom
	end
	s = math.clamp(s, 0, L)
	local t = e + s * b -- (the line's point nearest that one; not behind the eye)
	if t < 0 then s = math.clamp(-dd, 0, L) end
	return feet + Vector3.new(0, s, 0)
end

-- is a body (its feet) in a swing from eye along look: its nearest point within reach (+ its radius), and within cone
-- radians of the look (+ the angle its radius takes up at that distance). close in (1.5 m) anything in reach counts.
-- returns the point and its distance too
function Melee.inSwing(eye: Vector3, look: Vector3, feet: Vector3, reach: number, cone: number): (boolean, Vector3, number)
	local H = Melee.HIT
	local p = Melee.bodyPoint(eye, look, feet, H.top)
	local to = p - eye
	local d = to.Magnitude
	if d > reach + H.radius then return false, p, d end
	if d < 1.5 * S then return true, p, d end
	local widen = math.atan(H.radius / d)
	return look:Dot(to / d) >= math.cos(cone + widen), p, d
end

-- seconds until a cooldown that ends at `untilT` (server time) is over
function Melee.left(untilT: any, now: number): number
	return if type(untilT) == "number" then math.max(0, untilT - now) else 0
end

return Melee
