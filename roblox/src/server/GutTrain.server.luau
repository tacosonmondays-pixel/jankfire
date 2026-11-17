--!strict
-- THE GUT's train (17 Nov 2026; the owner: "the big train boss can pass by as an Easter egg"): for every Gut arena (the
-- one in workspace.Map and its copies in Map.ArenaCopies) this picks when the train passes through the subway, a few
-- times a match at random gaps, and writes it on the arena: TrainAt (the server time its face reaches the station) and
-- TrainDir (1 from the west, -1 from the east). Each screen plays the run itself (GutLife.client): the warning, the
-- train behind the platform's glass. The train never touches anyone: it runs on its own track behind a full-height
-- glass screen, with no collision and no shots, so it can never decide a fight.
local GAP_MIN, GAP_MAX = 40, 85       -- seconds between runs
local LEAD = 8                        -- seconds from the decision to the face reaching the station (> the client's warning)
local rng = Random.new()
local running: { [Instance]: boolean } = {}

local function loop(root: Model)
	if running[root] then return end
	running[root] = true
	task.spawn(function()
		task.wait(rng:NextNumber(12, 30))                  -- (the first one comes early in a match)
		while root.Parent do
			root:SetAttribute("TrainDir", if rng:NextNumber() < 0.5 then 1 else -1)
			root:SetAttribute("TrainAt", workspace:GetServerTimeNow() + LEAD)
			task.wait(LEAD + 10 + rng:NextNumber(GAP_MIN, GAP_MAX))
		end
		running[root] = nil
	end)
end

local function watch(folder: Instance)
	local function try(m: Instance)
		if m:IsA("Model") and m:GetAttribute("MapId") == "gut" then loop(m) end
	end
	for _, m in folder:GetChildren() do try(m) end
	folder.ChildAdded:Connect(try)
end

local map = workspace:WaitForChild("Map")
watch(map)
local copies = map:FindFirstChild("ArenaCopies")
if copies then watch(copies) end
map.ChildAdded:Connect(function(c) if c.Name == "ArenaCopies" then watch(c) end end)
