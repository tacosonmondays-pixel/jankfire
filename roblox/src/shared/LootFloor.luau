--!strict
-- where a loot container stands: the floor under a point, for LootOpening (your own opening, a batch's row) and for
-- Loot.luau (the spot others see). the owner, 16 Nov: "make sure the stuff doesnt clip through the ground".
-- the traps, all met in the hub:
--   * your feet: HipHeight is not where the feet are with this game's movement (1.2 studs off in the hub), so the feet
--     are measured from the foot parts themselves;
--   * floors rays can't see: many floor pieces are CanQuery off. a ray that ends far from the feet (a hole, a ceiling)
--     is not trusted; then the floor is where the feet are;
--   * thin decorative tops over the floor a ray hits, in ANOTHER folder: the hub's dais (Shell.Dais, 241.20) wears
--     Scenery.DaisTop / SpawnRing / DaisInner, round discs up to 0.12 studs higher. so after the ray, the container
--     stands on the highest visible piece that covers the point (discs tested as discs) within half a stud over the hit,
--     looked for among everything under the hit part's grandparent (cached a few seconds).
local F = {}

local function lowest(p: BasePart): number
	local cf, sz = p.CFrame, p.Size
	return cf.Position.Y - (math.abs(cf.RightVector.Y) * sz.X + math.abs(cf.UpVector.Y) * sz.Y + math.abs(cf.LookVector.Y) * sz.Z) / 2
end
local function highest(p: BasePart): number
	local cf, sz = p.CFrame, p.Size
	return cf.Position.Y + (math.abs(cf.RightVector.Y) * sz.X + math.abs(cf.UpVector.Y) * sz.Y + math.abs(cf.LookVector.Y) * sz.Z) / 2
end

-- the lowest point of a character's feet (nil: no character)
function F.feet(ch: Model?): number?
	if not ch then return nil end
	local low = math.huge
	for _, n in { "LeftFoot", "RightFoot", "Left Leg", "Right Leg" } do
		local p = ch:FindFirstChild(n)
		if p and p:IsA("BasePart") then low = math.min(low, lowest(p)) end
	end
	if low < math.huge then return low end
	local root = ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local hum = ch:FindFirstChildOfClass("Humanoid")
	return if root then root.Position.Y - root.Size.Y / 2 - (if hum then hum.HipHeight else 2) else nil
end

-- does this part cover the point (x, z) from above? a cylinder is tested as its round face (a flat disc stands with its
-- axis, local X, upright), anything else as its box
local function covers(d: BasePart, x: number, z: number): boolean
	local p = d.CFrame:PointToObjectSpace(Vector3.new(x, d.Position.Y, z))
	if d:IsA("Part") and d.Shape == Enum.PartType.Cylinder then
		local up = math.abs(d.CFrame.RightVector.Y) > 0.9 -- (the disc lies flat)
		if up then
			local r = math.min(d.Size.Y, d.Size.Z) / 2
			return p.Y * p.Y + p.Z * p.Z <= r * r
		end
	end
	local sz = d.Size
	return math.abs(p.X) <= sz.X / 2 and math.abs(p.Z) <= sz.Z / 2
end

-- the pieces rays can't see under a scope (cached for a few seconds: a batch asks ten times in a row)
local cache: { [Instance]: { t: number, parts: { BasePart } } } = {}
local function hidden(scope: Instance): { BasePart }
	local c = cache[scope]
	if c and os.clock() - c.t < 4 then return c.parts end
	local list = {}
	for _, d in scope:GetDescendants() do
		if d:IsA("BasePart") and not d.CanQuery and d.Transparency < 0.99 then table.insert(list, d) end
	end
	cache[scope] = { t = os.clock(), parts = list }
	return list
end

-- the floor's height under `at` (feetY: the opener's feet; ignore: what the ray must not hit, e.g. the character)
function F.at(at: Vector3, feetY: number, ignore: { Instance }): number
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = ignore
	local down = workspace:Raycast(Vector3.new(at.X, feetY + 3, at.Z), Vector3.new(0, -8, 0), params)
	if not down or down.Position.Y < feetY - 1.5 or down.Position.Y > feetY + 2.5 then return feetY end
	local y = down.Position.Y
	local scope: Instance? = down.Instance.Parent
	if scope and scope.Parent and scope.Parent ~= workspace and scope.Parent ~= game then scope = scope.Parent end
	if scope then
		for _, d in hidden(scope) do
			local top = highest(d)
			if top > y and top <= down.Position.Y + 0.5 and covers(d, at.X, at.Z) then y = top end
		end
	end
	return y
end

return F
