-- edit-time helper for placing look-only prop models (from ServerStorage.JankfireMeshes) without overlaps: every prop's
-- world box is checked against everything placed so far and against keep-out boxes (pads, spawns, doors, walkways).
-- a prop that would overlap is NOT placed and is reported. not used at runtime
local JM = game.ServerStorage.JankfireMeshes
local P = {}
P.boxes = {} :: { { lo: Vector3, hi: Vector3, name: string, keep: boolean? } }
P.log = {} :: { string }

function P.reset() P.boxes = {}; P.log = {} end

local function aabb(cf: CFrame, sz: Vector3): (Vector3, Vector3)
	local lo, hi = Vector3.one * math.huge, -Vector3.one * math.huge
	for _, sx in { -1, 1 } do for _, sy in { -1, 1 } do for _, sz2 in { -1, 1 } do
		local p = cf * Vector3.new(sx * sz.X / 2, sy * sz.Y / 2, sz2 * sz.Z / 2)
		lo = lo:Min(p); hi = hi:Max(p)
	end end end
	return lo, hi
end
P.aabb = aabb

function P.keepOut(name: string, lo: Vector3, hi: Vector3)
	table.insert(P.boxes, { lo = lo, hi = hi, name = name, keep = true })
end
function P.register(name: string, inst: Instance)
	local cf, sz
	if inst:IsA("Model") then cf, sz = inst:GetBoundingBox() else cf, sz = (inst :: BasePart).CFrame, (inst :: BasePart).Size end
	local lo, hi = aabb(cf, sz)
	table.insert(P.boxes, { lo = lo, hi = hi, name = name })
end

local function hits(lo: Vector3, hi: Vector3, tol: number): string?
	for _, b in P.boxes do
		if lo.X < b.hi.X - tol and hi.X > b.lo.X + tol and lo.Y < b.hi.Y - tol and hi.Y > b.lo.Y + tol and lo.Z < b.hi.Z - tol and hi.Z > b.lo.Z + tol then
			return b.name
		end
	end
	return nil
end
P.hits = hits

-- o: { name=, at=Vector3 (centre x, floor y, centre z), scale=, yaw=, parent=, keep={child models to keep},
--      wall={axis="x"|"z", face=number, side=1|-1} (snap the box against a wall face), tint={[GlbMat]=Color3},
--      lift=number (raise above the floor), label= }
function P.place(o: any): Model?
	local src = JM:FindFirstChild(o.name)
	if not src then table.insert(P.log, "missing template " .. o.name); return nil end
	local m = src:Clone()
	if o.keep then
		local root = if #m:GetChildren() == 1 and m:GetChildren()[1]:IsA("Model") then m:GetChildren()[1] else m
		for _, c in root:GetChildren() do
			if not table.find(o.keep, c.Name) then c:Destroy() end
		end
	end
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
			if o.tint and o.tint[d:GetAttribute("GlbMat")] then d.Color = o.tint[d:GetAttribute("GlbMat")] end
		end
	end
	if o.scale and o.scale ~= 1 then m:ScaleTo(o.scale) end
	local cf0, sz0 = m:GetBoundingBox()
	m:PivotTo(CFrame.Angles(0, o.yaw or 0, 0) * (cf0:Inverse() * m:GetPivot()))
	local cf, sz = m:GetBoundingBox()
	local lo, hi = aabb(cf, sz)
	local size = hi - lo
	local c = (lo + hi) / 2
	local want = Vector3.new(o.at.X, o.at.Y + (o.lift or 0) + size.Y / 2, o.at.Z)
	if o.wall then
		if o.wall.axis == "x" then want = Vector3.new(o.wall.face + o.wall.side * (size.X / 2 + 0.15), want.Y, want.Z)
		else want = Vector3.new(want.X, want.Y, o.wall.face + o.wall.side * (size.Z / 2 + 0.15)) end
	end
	m:PivotTo(m:GetPivot() + (want - c))
	lo, hi = lo + (want - c), hi + (want - c)
	local clash = hits(lo, hi, 0.02)
	if clash then
		table.insert(P.log, ("SKIPPED %s %s: overlaps %s"):format(o.label or o.name, tostring(o.at), clash))
		m:Destroy()
		return nil
	end
	m.Name = o.label or o.name
	m.Parent = o.parent
	table.insert(P.boxes, { lo = lo, hi = hi, name = m.Name })
	return m
end

return P
