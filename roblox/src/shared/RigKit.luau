--!strict
-- the Overdrive Rig's forearms (the hold session, 19 Nov 2026): gun-models' kit model w_rig_arms (tools/roblox/gun_rig.py,
-- docs/GUN-MODELS.md) read once from its template (ReplicatedStorage.JankfireWeapons) into file metres, for the two
-- that draw it: RigArms.client (first person) and ThirdPerson (on every suited-up body).
-- the file's frame: fists toward -z, the right arm at +x. nodes armR > fistR, armL > fistL, ammoL (the rack's loaded
-- noses, on the left forearm). a piece's node is its name up to "_wz".
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local V = Vector3.new

local RigKit = {}
RigKit.LO, RigKit.HI = V(-0.4285, -0.105, -0.6008), V(0.4285, 0.221, 0.3991) -- (its file box, if the template has none)
RigKit.ELBOW = { r = V(0.3, 0, 0.35), l = V(-0.3, 0, 0.35) } -- (where each arm turns)
RigKit.GRIP = { r = V(0.3, -0.006, -0.47), l = V(-0.3, -0.006, -0.47) } -- (the palm's middle: where the avatar's hand sits)

export type Piece = {
	src: BasePart, -- (the template's piece: copied by make)
	side: string, -- "r" / "l"
	node: string, -- armr, fistr, arml, fistl, ammol
	q: Vector3, -- its middle, file metres
	rot: CFrame, -- its turn in the file's frame
	size: Vector3, -- file metres
	glow: boolean, -- (a glow strip: neon)
}

local cache: { Piece }? = nil
local cacheOf: Instance? = nil

-- (WeaponModels' partsBox: the pieces' own box about the template's pivot)
local function partsBox(tmpl: Model): (CFrame, Vector3)
	local pcf = tmpl:GetPivot()
	local lo, hi = Vector3.one * math.huge, -Vector3.one * math.huge
	for _, d in tmpl:GetDescendants() do
		if d:IsA("BasePart") then
			local rel = pcf:ToObjectSpace(d.CFrame)
			local s = d.Size / 2
			local e = V(
				math.abs(rel.XVector.X) * s.X + math.abs(rel.YVector.X) * s.Y + math.abs(rel.ZVector.X) * s.Z,
				math.abs(rel.XVector.Y) * s.X + math.abs(rel.YVector.Y) * s.Y + math.abs(rel.ZVector.Y) * s.Z,
				math.abs(rel.XVector.Z) * s.X + math.abs(rel.YVector.Z) * s.Y + math.abs(rel.ZVector.Z) * s.Z)
			lo = lo:Min(rel.Position - e); hi = hi:Max(rel.Position + e)
		end
	end
	if lo.X > hi.X then return tmpl:GetBoundingBox() end
	return pcf * CFrame.new((lo + hi) / 2), hi - lo
end

-- the pieces, or nil while the template isn't in the place (WeaponModels' fitImported: the template's box mapped back
-- onto the file's, so they land in file metres whatever size the upload came in at)
function RigKit.pieces(): { Piece }?
	local lib = ReplicatedStorage:FindFirstChild("JankfireWeapons")
	local tmpl = lib and lib:FindFirstChild("w_rig_arms")
	if not tmpl or not tmpl:IsA("Model") then return nil end
	if cache and cacheOf == tmpl then return cache end
	local flo, fhi = tmpl:GetAttribute("FileLo"), tmpl:GetAttribute("FileHi")
	local lo = if typeof(flo) == "Vector3" then flo else RigKit.LO
	local hi = if typeof(fhi) == "Vector3" then fhi else RigKit.HI
	local tcf, tsize = partsBox(tmpl)
	local fsz = hi - lo
	local centre = (lo + hi) / 2
	local U = V(tsize.X / math.max(fsz.X, 1e-4), tsize.Y / math.max(fsz.Y, 1e-4), tsize.Z / math.max(fsz.Z, 1e-4))
	local list: { Piece } = {}
	for _, d in tmpl:GetDescendants() do
		if not d:IsA("BasePart") then continue end
		local rel = tcf:ToObjectSpace(d.CFrame)
		local n = string.lower(d.Name)
		local node = string.match(n, "^(.-)_wz") or n
		table.insert(list, {
			src = d, side = if string.sub(node, -1) == "l" then "l" else "r", node = node,
			q = rel.Position / U + centre, rot = rel.Rotation, size = d.Size / U,
			glow = string.find(n, "glow", 1, true) ~= nil or d.Material == Enum.Material.Neon,
		})
	end
	cache, cacheOf = list, tmpl
	return list
end

-- a copy of a piece at k studs a file metre: no joints, touches and casts nothing, not placed
function RigKit.make(p: Piece, k: number): BasePart
	local c = p.src:Clone()
	for _, d in c:GetChildren() do
		if d:IsA("JointInstance") or d:IsA("WeldConstraint") or d:IsA("Attachment") then d:Destroy() end
	end
	c.Size = p.size * k
	c.Anchored = false; c.CanCollide = false; c.CanQuery = false; c.CanTouch = false; c.CastShadow = false; c.Massless = true
	return c
end

return RigKit
