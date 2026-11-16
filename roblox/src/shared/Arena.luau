--!strict
-- which arena matches are played in. workspace.Map's attribute "Arena" names a model under Map: "Rooftop" (v1, the
-- default, also when the attribute is missing) or "RooftopV2" (v2, built by ServerStorage.PolishBackup.RooftopV2).
-- every script that needs the arena (team spawns, spawn points, the fall line) asks here, so flipping the one
-- attribute moves all of them.
local Arena = {}

Arena.DEFAULT = "Rooftop"

local function map(): Instance?
	return workspace:FindFirstChild("Map")
end

function Arena.name(): string
	local m = map()
	local n = m and m:GetAttribute("Arena")
	if type(n) == "string" and m and m:FindFirstChild(n) then return n end
	return Arena.DEFAULT
end

function Arena.get(): Instance?
	local m = map()
	return m and m:FindFirstChild(Arena.name())
end

-- below this height you are "into the smog"
function Arena.killY(): number
	local a = Arena.get()
	local k = a and a:GetAttribute("KillY")
	return if type(k) == "number" then k else -485
end

-- the x the team spawns face (the arena's centre line)
function Arena.centreX(): number
	local a = Arena.get()
	local x = a and a:GetAttribute("CentreX")
	return if type(x) == "number" then x else 0
end

return Arena
