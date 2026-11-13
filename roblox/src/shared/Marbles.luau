--!strict
-- the Marble Shotgun's floor marbles (server/room.js marblePatch / slipsOn / marbleSlip, shared/marbles.js), in studs.
-- pure: the map is a cast function, so the tests run it on the real Rooftop boxes outside Roblox.
-- cast(origin, unitDir, maxLen) -> (distance, surface normal) or nil
local Weapons = require(script.Parent.Weapons)

local M = Weapons.MSLIP
local Marbles = {}

export type Cast = (Vector3, Vector3, number) -> (number?, Vector3?)
export type Patch = { id: number, c: Vector3, r: number, n: number, owner: any, born: number, untilT: number }

local function flatDist(a: Vector3, b: Vector3): number
	local dx, dz = a.X - b.X, a.Z - b.Z
	return math.sqrt(dx * dx + dz * dz)
end

-- where the shot's marbles came to rest: from the shooter's eye along each pellet (at most 12), drop off what it hit
-- (or the end of its range) straight down onto a floor. the biggest bunch that landed together makes the patch
function Marbles.patch(eye: Vector3, ends: { Vector3 }, range: number, cast: Cast): (Vector3?, number?, number?)
	local pts: { Vector3 } = {}
	local S = Weapons.S
	for _, e in ends do
		local v = e - eye
		local l = v.Magnitude
		if l < 1e-3 then continue end
		local d = v / l
		local L = math.min(range, l)
		local t, nrm = cast(eye, d, L)
		local a = if t and nrm then eye + d * t + nrm * (0.1 * S) - d * (0.05 * S) else eye + d * L
		local ft, fn = cast(a, Vector3.new(0, -1, 0), 40 * S)
		if ft and fn and fn.Y > 0.99 then table.insert(pts, Vector3.new(a.X, a.Y - ft, a.Z)) end
	end
	local best: { Vector3 } = {}
	for _, a in pts do
		local c = {}
		for _, b in pts do
			if math.abs(b.Y - a.Y) < 0.5 * S and flatDist(a, b) < 2.5 * S then table.insert(c, b) end
		end
		if #c > #best then best = c end
	end
	if #best < math.max(3, #ends * 0.3) then return nil end -- sprayed all over (or into the sky): no patch
	local cx, cz, top = 0, 0, -math.huge
	for _, b in best do cx += b.X / #best; cz += b.Z / #best; top = math.max(top, b.Y) end
	local ft, fn = cast(Vector3.new(cx, top + 0.4 * S, cz), Vector3.new(0, -1, 0), 1.4 * S)
	if not ft or not fn or fn.Y < 0.99 then -- the middle is in a pillar the marbles landed round: use the nearest marble
		local near = best[1]
		for _, b in best do if flatDist(b, Vector3.new(cx, 0, cz)) < flatDist(near, Vector3.new(cx, 0, cz)) then near = b end end
		cx, cz = near.X, near.Z
		ft, fn = cast(Vector3.new(cx, top + 0.4 * S, cz), Vector3.new(0, -1, 0), 1.4 * S)
		if not ft or not fn or fn.Y < 0.99 then return nil end
	end
	local y = top + 0.4 * S - (ft :: number)
	local ss = 0
	for _, b in best do ss += (b.X - cx) ^ 2 + (b.Z - cz) ^ 2 end
	local rms = math.sqrt(ss / #best)
	local r = math.clamp(0.9 * S + rms * 1.3, M.rMin, M.rMax)
	-- more marbles in a bigger patch so it doesn't read as a few specks
	local n = math.floor(M.n * math.min(1, (#best / #ends) * 1.4) * math.clamp((r / (1.6 * S)) ^ 2, 0.7, 1.6) + 0.5)
	return Vector3.new(cx, y, cz), r, n
end

-- is someone with their feet at `feet` on the patch
function Marbles.onPatch(c: Vector3, r: number, feet: Vector3, pad: number?): boolean
	local dy = feet.Y - c.Y
	return dy > M.feetLo and dy < M.feetHi and flatDist(feet, c) < r + (pad or 0)
end

-- a crouch walk is safe; anything faster slips (16.5 studs/s with these weapons)
function Marbles.safeSpeed(speedMul: number?): number
	return math.min(M.slide, math.max(M.walk, M.crouch * (speedMul or 1) + Weapons.S))
end

-- a slip scatters the marbles: fewer, smaller, gone under minN. returns the new (n, r) and whether it's gone
function Marbles.thin(n: number, r: number): (number, number, boolean)
	local nn = math.floor(n * M.thin)
	local nr = math.max(M.minR, r * M.thinR)
	return nn, nr, nn < M.minN
end

-- the caps: drop your oldest past `per`, then the room's oldest past `room`. patches in age order (oldest first)
function Marbles.toDrop(patches: { Patch }, owner: any): { Patch }
	local out = {}
	local mine = {}
	for _, p in patches do if p.owner == owner then table.insert(mine, p) end end
	local gone: { [Patch]: boolean } = {}
	while #mine >= M.per do local p = table.remove(mine, 1) :: Patch; gone[p] = true; table.insert(out, p) end
	local left = #patches - #out
	for _, p in patches do
		if left < M.room then break end
		if not gone[p] then gone[p] = true; table.insert(out, p); left -= 1 end
	end
	return out
end

return Marbles
