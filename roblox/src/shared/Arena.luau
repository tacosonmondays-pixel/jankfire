--!strict
-- which arena matches are played in. workspace.Map's attribute "Arena" names a model under Map: "Rooftop" (v1, the
-- default, also when the attribute is missing), "RooftopV2" (v2, built by ServerStorage.PolishBackup.RooftopV2),
-- "RooftopV3" (v3, v1's layout redressed: PolishBackup.RooftopV3) or one of the maps ported from the web game
-- (17 Nov: "Crate"; built by PolishBackup.WebArena, which gives each its Title, Look and MaxTeam attributes).
-- the rotation: workspace.Map's attribute "ArenaPool" is a comma list of arenas ("RooftopV2,RooftopV3", the owner's
-- pick of 16 Nov: "Why not both XD"). each pad takes the next one from it for its next match (Arena.pick); with no
-- pool, matches use "Arena". PolishBackup.RooftopV3's R.use("both") / R.use("v1"|"v2"|"v3") sets both attributes.
-- matches run side by side (16 Nov, more pads in the hub): each live match has its own "site", the arena itself when
-- no other match is in it, else a copy of it Arena.GAP studs along x (Matches makes the copies and clears them). so a
-- match asks ITS site for its team spawns, fall line and centre line: Arena.killY(site), Arena.centreX(site). asked
-- without a site they answer for "Arena" (the training dummies). a player in a match carries the attribute "Arena"
-- (the arena's name, a copy's too): their screen's light follows it (HubLife)
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

-- below this height you are "into the smog" (a site's, or the default arena's)
function Arena.killY(site: Instance?): number
	local a = site or Arena.get()
	local k = a and a:GetAttribute("KillY")
	return if type(k) == "number" then k else -485
end

-- the x the team spawns face (the arena's centre line; a copy carries its own, moved with it)
function Arena.centreX(site: Instance?): number
	local a = site or Arena.get()
	local x = a and a:GetAttribute("CentreX")
	return if type(x) == "number" then x else 0
end

-- the rotation's arenas: the built ones ArenaPool names, in its order, each once. with a team size, only the arenas that
-- take it (an arena's attribute "MaxTeam": the ported web maps, 17 Nov; Crate is too small for a 4v4); if none does,
-- all of them
function Arena.pool(teamSize: number?): { string }
	local m = map()
	local s = m and m:GetAttribute("ArenaPool")
	local out, fits = {}, {}
	if type(s) == "string" and m then
		for n in string.gmatch(s, "[^,%s]+") do
			local a = m:FindFirstChild(n)
			if a and not table.find(out, n) then
				table.insert(out, n)
				local cap = a:GetAttribute("MaxTeam")
				if not (teamSize and type(cap) == "number" and cap > 0 and teamSize > cap) then table.insert(fits, n) end
			end
		end
	end
	return if #fits > 0 then fits else out
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

-- where copy k (1, 2, 3...) of an arena goes: k steps of GAP along x, one side then the other (+x, -x, +2x, -2x).
-- the arenas' cities are 6,144 studs across, so copies never touch, and each is far past the others' fog (FogEnd
-- 2,300 to 2,600). the height stays, so a copy's fall line (KillY) is its arena's
Arena.GAP = 7000
function Arena.copyOffset(k: number): Vector3
	local step = math.ceil(k / 2) * Arena.GAP
	return Vector3.new(if k % 2 == 1 then step else -step, 0, 0)
end
-- arenas that can't be copied: v1's Blender models live outside it (Map.Models, MeshSwap), so a copy would be bare.
-- v1 takes one match at a time
Arena.NO_COPY = { Rooftop = true } :: { [string]: boolean }

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
