--!strict
-- swimmable water: every Part tagged "JankWater" (the Rooftop pool's Rooftop.Water.PoolWater: invisible, its top face
-- is the surface) gets filled with Terrain water, so the Humanoid really swims in it (buoyancy, the Swimming state,
-- Move's paddling). Terrain can't be cloned with a map, so this fills each volume when it appears and empties it when
-- it goes: a copy of the arena moved somewhere else gets its own water. Terrain cells are 4 studs: the fill is pushed
-- out to whole cells sideways and down (into the pool's thick walls and floor, hidden), the top stays exact.
local CollectionService = game:GetService("CollectionService")
local Terrain = workspace.Terrain

local TAG = "JankWater"
local filled: { [BasePart]: { cf: CFrame, size: Vector3 } } = {}

local function region(p: BasePart): (CFrame, Vector3)
	local c, h = p.Position, p.Size / 2
	local lo, hi = c - h, c + h
	local function down(v: number): number return math.floor(v / 4) * 4 end
	local function up(v: number): number return math.ceil(v / 4) * 4 end
	local a = Vector3.new(down(lo.X), down(lo.Y), down(lo.Z))
	local b = Vector3.new(up(hi.X), hi.Y, up(hi.Z))
	return CFrame.new((a + b) / 2), b - a
end

local function fill(p: Instance)
	-- (NoTerrain: a volume that only tells the effects where water is, like the shallow hot tub)
	if not p:IsA("BasePart") or not p:IsDescendantOf(workspace) or p:GetAttribute("NoTerrain") then return end
	local cf, size = region(p)
	Terrain:FillBlock(cf, size, Enum.Material.Water)
	filled[p] = { cf = cf, size = size }
end

local function empty(p: Instance)
	local r = filled[p :: BasePart]
	if not r then return end
	filled[p :: BasePart] = nil
	Terrain:FillBlock(r.cf, r.size, Enum.Material.Air)
end

CollectionService:GetInstanceAddedSignal(TAG):Connect(fill)
CollectionService:GetInstanceRemovedSignal(TAG):Connect(empty)
for _, p in CollectionService:GetTagged(TAG) do fill(p) end
