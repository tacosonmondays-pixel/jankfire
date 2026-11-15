--!strict
-- who a ray hits: the web game's two fixed boxes per player (body + head, shared/physics.js), never the R15 limbs, so
-- animation never changes who you hit. pure maths on Vector3s (the tests run it outside Roblox)
local Weapons = require(script.Parent.Weapons)

local Hitbox = {}
local B = Weapons.BOX
local S = Weapons.S

-- an R15 root sits 3 studs over the feet (HipHeight 2 + half the root's 2 studs): the web game's chest (feet + 1 m)
Hitbox.ROOT_UP = 3
-- the eye: feet + 1.6 m standing
Hitbox.EYE_UP = 1.6 * S

function Hitbox.feet(rootPos: Vector3): Vector3 return rootPos - Vector3.new(0, Hitbox.ROOT_UP, 0) end

-- far people are bigger targets (public/js/remote.js distScale): x1 up to 25 m, x1.8 from 85 m
function Hitbox.distScale(dist: number): number
	return 1 + math.clamp((dist - 25 * S) / (60 * S), 0, 1) * 0.8
end

-- ray vs axis-aligned box: the distance along the ray, or nil
function Hitbox.rayBox(o: Vector3, d: Vector3, lo: Vector3, hi: Vector3): number?
	local tmin, tmax = -math.huge, math.huge
	for _, ax in { "X", "Y", "Z" } do
		local oa, da = (o :: any)[ax] :: number, (d :: any)[ax] :: number
		local la, ha = (lo :: any)[ax] :: number, (hi :: any)[ax] :: number
		if math.abs(da) < 1e-9 then
			if oa < la or oa > ha then return nil end
		else
			local t1, t2 = (la - oa) / da, (ha - oa) / da
			if t1 > t2 then t1, t2 = t2, t1 end
			tmin, tmax = math.max(tmin, t1), math.min(tmax, t2)
			if tmin > tmax then return nil end
		end
	end
	if tmax < 0 then return nil end
	return math.max(tmin, 0)
end

-- a fighter's boxes (scaled about the feet by k)
function Hitbox.boxes(feet: Vector3, k: number): (Vector3, Vector3, Vector3, Vector3)
	local br, hr = B.bodyR * k, B.headR * k
	return feet + Vector3.new(-br, 0, -br), feet + Vector3.new(br, B.bodyTop * k, br),
		feet + Vector3.new(-hr, B.bodyTop * k, -hr), feet + Vector3.new(hr, B.headTop * k, hr)
end

-- the nearest box this ray hits: distance and whether it was the head
function Hitbox.ray(o: Vector3, d: Vector3, feet: Vector3, k: number): (number?, boolean)
	local bl, bh, hl, hh = Hitbox.boxes(feet, k)
	local tb, th = Hitbox.rayBox(o, d, bl, bh), Hitbox.rayBox(o, d, hl, hh)
	if th and (not tb or th <= tb) then return th, true end
	return tb, false
end

-- a random direction in a cone of half-angle ~s around d (public/js/weapons.js spreadDir): a uniform point in a disc
function Hitbox.spreadDir(d: Vector3, s: number, r1: number, r2: number): Vector3
	if s <= 0 then return d end
	local up = if math.abs(d.Y) > 0.95 then Vector3.xAxis else Vector3.yAxis
	local a = d:Cross(up).Unit
	local b = a:Cross(d).Unit
	local m, ang = math.sqrt(r1) * s, r2 * math.pi * 2
	return (d + a * (math.cos(ang) * m) + b * (math.sin(ang) * m)).Unit
end

-- melee: is a point inside the swing's cone (skipped this close: a body hugging you always counts)
function Hitbox.inCone(eye: Vector3, look: Vector3, pt: Vector3, range: number, cone: number): boolean
	local to = pt - eye
	local dist = to.Magnitude
	if dist > range then return false end
	if dist < 1.5 * S then return true end
	return look:Dot(to.Unit) >= math.cos(cone)
end

return Hitbox
