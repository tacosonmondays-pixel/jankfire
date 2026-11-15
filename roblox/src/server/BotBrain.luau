--!strict
-- the bots' decisions, pure (the tests run them): who to go after, which of the three weapons fits the range, where to
-- stand (web room.js botThink: a preferred range per weapon, strafing, melee runs straight in), when to fire, when to
-- grapple and when to try a parry. Bots.luau moves the bodies and fires through the same server rules as players
local Shared = game:GetService("ReplicatedStorage"):WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))

local S = Weapons.S
local W = Weapons.list
local B = {}

-- normal difficulty (web BOT_DIFF normal): aim error, how fast it turns, how long before it reacts to someone it sees
B.DIFF = { err = 0.045, turn = 6, react = 0.35 }
B.NAMES = { "Gary", "Linda", "Steve", "Brenda", "Kevin", "Doug", "Karen", "Phil", "Tina", "Rick", "Deb", "Carl", "Pam", "Todd", "Barb", "Chad" }

-- where a bot likes to stand with each weapon, studs from the target (web: marbles 1.5-4 m, default 7-22 m, melee
-- right up close at 0.7 x its reach)
function B.pref(wid: string, kat: number): (number, number)
	if wid == "marbles" then return 1.5 * S, 4 * S end
	if W[wid] and W[wid].kind == "melee" then return 0, Weapons.reach(W[wid], kat) * 0.7 end
	return 7 * S, 22 * S
end

-- the right weapon for the range (with a little give, so it doesn't flick back and forth at the boundary)
function B.weapon(dist: number, current: string, kat: number): string
	local reach = Weapons.reach(W.katana, kat)
	local give = if current == "katana" then 3 elseif current == "marbles" then 4 else 0
	if dist < reach + 2 + (if current == "katana" then give else 0) then return "katana" end
	if dist < 12 * S + (if current == "marbles" then give else 0) then return "marbles" end
	return "redline"
end

export type Seen = { f: any, dist: number, vis: boolean }
-- the target: the nearest one, people it can't see count 2.5x farther (web botTarget)
function B.target(list: { Seen }): Seen?
	local best, bestD = nil, math.huge
	for _, s in list do
		local d = s.dist * (if s.vis then 1 else 2.5)
		if d < bestD then best, bestD = s, d end
	end
	return best
end

-- the flat direction to walk: in if too far (or out of sight), out if too close, plus a strafe (not for melee:
-- circling at arm's length never lines up a swing). to = target - bot, flat
function B.wish(to: Vector3, dist: number, vis: boolean, lo: number, hi: number, strafe: number, melee: boolean): Vector3
	local flat = Vector3.new(to.X, 0, to.Z)
	if flat.Magnitude < 1e-3 then return Vector3.zero end
	local f = flat.Unit
	local w = Vector3.zero
	if dist > hi or not vis then w += f elseif dist < lo then w -= f end
	if not melee then w += Vector3.new(-f.Z, 0, f.X) * strafe * 0.8 end
	return if w.Magnitude > 1e-3 then w.Unit else Vector3.zero
end

-- fire only at someone in sight, roughly in front (turned within 0.25 rad, or 0.6 for a swing), after reacting
function B.canFire(vis: boolean, seenFor: number, aimOff: number, dist: number, wid: string, kat: number): boolean
	if not vis then return false end
	local w = W[wid]
	if w.kind == "melee" then return dist < Weapons.reach(w, kat) + 1 and aimOff < 0.6 end
	return seenFor >= B.DIFF.react and aimOff < 0.25 and dist < w.range
end

-- grapple when the target is across a gap (no floor ahead) and within the hook's range, or to save itself from the
-- smog (falling, and well below the floor it came from)
function B.wantHook(floorAhead: boolean, toTarget: number, falling: boolean, belowFloor: number): string?
	if falling and belowFloor > 6 * S then return "save" end
	if not floorAhead and toTarget < 85 * S then return "cross" end
	return nil
end

-- a parry, sometimes: katana out, the guard ready, and someone in front about to hit it (a gun pointed at it within
-- ~12 degrees, or a blade within reach). chance per second, rolled by the caller with dt
function B.parryChance(holdingKatana: boolean, ready: boolean, threat: string?): number
	if not holdingKatana or not ready or not threat then return 0 end
	return if threat == "blade" then 1.2 else 0.6
end

-- how many bots the match wants: the room size (the Bots knob + 1) minus the people in it (MODES.md fillBots)
function B.wanted(humans: number, seats: number): number
	return math.max(0, seats - humans)
end

return B
