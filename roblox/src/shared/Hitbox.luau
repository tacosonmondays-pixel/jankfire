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

-- (18 Nov 2026: the whole visible head is a headshot) where this body's head really is, in studs over its feet line
-- (root - ROOT_UP): neck = the Head part's bottom, top = its top, from the rig's joints at rest (Motor6D C0 * C1^-1
-- up to the root, no animation), so the server and every client get the same numbers for R6, R15, short or tall.
-- the web's fixed boxes put the split at bodyTop, over the middle of a Roblox head: shots at its centre were body hits
export type Prof = { neck: number, top: number }
-- a body with no Head part says where its head is with the model attributes HitNeck / HitTop (studs over its feet
-- line). Cardboard Carl (bc_cutout, tools/roblox/range_models.py): the head is a ten-sided disc of radius 1.12 at
-- 5.85 over the feet, so 4.75 to 6.97 (the old head box began at 4.86: his chin was a body hit)
Hitbox.CUTOUT = { neck = 4.75, top = 6.97 }
local profs: { [Instance]: { t: number, p: Prof? } } = setmetatable({}, { __mode = "k" }) :: any
local function restInRoot(m: Instance, root: BasePart, part: BasePart): CFrame?
	local cf, cur = CFrame.identity, part
	for _ = 1, 10 do
		if cur == root then return cf end
		local joint: Motor6D? = nil
		for _, d in m:GetDescendants() do
			if d:IsA("Motor6D") and d.Part1 == cur and d.Part0 then joint = d; break end
		end
		if not joint then return nil end
		cf = joint.C0 * joint.C1:Inverse() * cf
		cur = joint.Part0 :: BasePart
	end
	return nil
end
function Hitbox.profile(m: Instance?): Prof?
	if not m then return nil end
	local c = profs[m]
	local now = os.clock()
	if c and now - c.t < 5 then return c.p end
	local root, head = m:FindFirstChild("HumanoidRootPart"), m:FindFirstChild("Head")
	local p: Prof? = nil
	if root and root:IsA("BasePart") and head and head:IsA("BasePart") then
		local rest = restInRoot(m, root, head)
		local mid = if rest then rest.Position.Y else root.CFrame:PointToObjectSpace(head.Position).Y
		local up, h = mid + Hitbox.ROOT_UP, head.Size.Y
		if up > 1 and up < 15 and h > 0.2 and h < 5 then p = { neck = up - h / 2, top = up + h / 2 } end
	elseif root then
		local nk, tp = m:GetAttribute("HitNeck"), m:GetAttribute("HitTop")
		if type(nk) == "number" and type(tp) == "number" and tp > nk then p = { neck = nk, top = tp } end
	end
	profs[m] = { t = now, p = p }
	return p
end

-- a fighter's boxes (scaled about the feet by k). pad = extra studs on every outer face: the server's lag allowance
-- when it re-checks a shot against where the target was (the client always passes none). prof (Hitbox.profile):
-- the body box ends at the neck and the head box starts there, never lower than the old top (nothing that was a
-- headshot stops being one)
function Hitbox.boxes(feet: Vector3, k: number, pad: number?, prof: Prof?): (Vector3, Vector3, Vector3, Vector3)
	local p = pad or 0
	local br, hr = B.bodyR * k + p, B.headR * k + p
	local split = if prof then math.min(prof.neck, B.bodyTop) * k else B.bodyTop * k
	local top = if prof then math.max(prof.top, B.headTop) * k else B.headTop * k
	return feet + Vector3.new(-br, -p, -br), feet + Vector3.new(br, split, br),
		feet + Vector3.new(-hr, split, -hr), feet + Vector3.new(hr, top + p, hr)
end

-- the nearest box this ray hits: distance and whether it was the head
function Hitbox.ray(o: Vector3, d: Vector3, feet: Vector3, k: number, pad: number?, prof: Prof?): (number?, boolean)
	local bl, bh, hl, hh = Hitbox.boxes(feet, k, pad, prof)
	local tb, th = Hitbox.rayBox(o, d, bl, bh), Hitbox.rayBox(o, d, hl, hh)
	if th and tb then
		-- (both: the body box sticks out further than the head box, so a shot rising to the chin clipped its top front
		-- corner first and was a body hit. decide by the height where the ray passes the body's own middle line: a
		-- real body, and a cardboard Carl most of all, is thin)
		local hx, hz = d.X, d.Z
		local hh2 = hx * hx + hz * hz
		if hh2 > 1e-6 then
			local t = -((o.X - feet.X) * hx + (o.Z - feet.Z) * hz) / hh2
			local y = o.Y + d.Y * t
			return math.min(tb, th), y >= hl.Y
		end
	end
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
