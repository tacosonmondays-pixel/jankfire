--!strict
-- which arena matches are played in. workspace.Map's attribute "Arena" names a model under Map: "Rooftop" (v1, the
-- default, also when the attribute is missing), "RooftopV2" (v2, built by ServerStorage.PolishBackup.RooftopV2) or
-- "RooftopV3" (v3, v1's layout redressed: PolishBackup.RooftopV3). every script that needs the arena (team spawns,
-- spawn points, the fall line, the match light) asks here, so flipping the one attribute moves all of them.
-- the rotation: workspace.Map's attribute "ArenaPool" is a comma list of arenas ("RooftopV2,RooftopV3", the owner's
-- pick of 16 Nov: "Why not both XD"). when it names at least one built arena, Matches takes the next one from it
-- just before the players go in (Arena.pick) and sets "Arena" to it. with no pool, "Arena" stays as it is set.
-- PolishBackup.RooftopV3's R.use("both") / R.use("v1"|"v2"|"v3") sets both attributes
local Arena = {}

Arena.DEFAULT = "Rooftop"
-- what the match's first banner calls each arena (a model's own attribute "Title" wins)
Arena.TITLES = { Rooftop = "ROOFTOP: DUSK", RooftopV2 = "ROOFTOP: SKYLINE", RooftopV3 = "ROOFTOP" }

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

-- the rotation's arenas: the built ones ArenaPool names, in its order, each once
function Arena.pool(): { string }
	local m = map()
	local s = m and m:GetAttribute("ArenaPool")
	local out = {}
	if type(s) == "string" and m then
		for n in string.gmatch(s, "[^,%s]+") do
			if m:FindFirstChild(n) and not table.find(out, n) then table.insert(out, n) end
		end
	end
	return out
end

-- the next arena out of `pool`: never `last` again while there is another one (two arenas take turns); the first
-- pick (no `last`) is a random one. nil for an empty pool. pure, so it can be tested
function Arena.pick(pool: { string }, last: string?, rand: (number) -> number): string?
	if #pool == 0 then return nil end
	local others = {}
	for _, n in pool do if n ~= last then table.insert(others, n) end end
	if #others == 0 then return pool[1] end
	return others[rand(#others)]
end

-- what the banner calls an arena
function Arena.title(name: string?): string
	local n = name or Arena.name()
	local m = map()
	local a = m and m:FindFirstChild(n)
	local t = a and a:GetAttribute("Title")
	if type(t) == "string" and t ~= "" then return t end
	return Arena.TITLES[n] or "ROOFTOP"
end

return Arena
