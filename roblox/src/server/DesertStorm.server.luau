--!strict
-- DESERT v2's sandstorm (17 Nov 2026; the owner: "make the shape unique, give it like unique properties"): for every
-- desert arena (MapId "desert2": the one in workspace.Map and its copies in Map.ArenaCopies) this picks when a storm
-- blows through, a few times a match, and writes it on the arena: StormAt (the server time it starts) and StormLen
-- (seconds). Each screen plays it itself (DesertStorm.client): the haze thickens to a sandy wall and sand blows past,
-- then it clears. It changes nothing in play but how far you can see, the same for everyone.
local FIRST_MIN, FIRST_MAX = 20, 40     -- the first one, seconds after the arena appears (a match's start)
local GAP_MIN, GAP_MAX = 70, 120        -- then this long between storms
local LEN = 18                          -- each one's length
local LEAD = 3                          -- seconds from the decision to its start
local rng = Random.new()
local running: { [Instance]: boolean } = {}

local function loop(root: Model)
	if running[root] then return end
	running[root] = true
	task.spawn(function()
		task.wait(rng:NextNumber(FIRST_MIN, FIRST_MAX))
		while root.Parent do
			root:SetAttribute("StormLen", LEN)
			root:SetAttribute("StormAt", workspace:GetServerTimeNow() + LEAD)
			task.wait(LEAD + LEN + rng:NextNumber(GAP_MIN, GAP_MAX))
		end
		running[root] = nil
	end)
end

local function watch(folder: Instance)
	local function try(m: Instance)
		if m:IsA("Model") and m:GetAttribute("MapId") == "desert2" then loop(m) end
	end
	for _, m in folder:GetChildren() do try(m) end
	folder.ChildAdded:Connect(try)
end

local map = workspace:WaitForChild("Map")
watch(map)
local copies = map:FindFirstChild("ArenaCopies")
if copies then watch(copies) end
map.ChildAdded:Connect(function(c) if c.Name == "ArenaCopies" then watch(c) end end)
