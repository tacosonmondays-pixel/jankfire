--!nocheck
-- THE ROTUNDA: the game's real hub since 2026-11-15, and its edit-time builder. the owner, about the bowling centre
-- (HubLab's "centre"): "I like the aspect and design buyt bolowing doesnt make sense for the game you know, keep it as a
-- hub we can use but lets rework the first rework"; asked which hub they meant: "it had a duck lounge, a big like circle
-- thing in the center with the branching paths leading into the rivals like pads that I said were a bit too on the nose".
-- so: the first round hub's plan (a round domed middle, a ring balcony, short halls that each frame the next room, a
-- small warm duck lounge), built in the bowling centre's look (slate shell, dark piers with light strips, a cream ring
-- with one pink line, wood dado, plain heavy lettering), as the ground-floor lobby of the arena. the pads are five open
-- lifts up to the arena, on an arc behind the round room's northern piers: one opening and one floor line per lift.
-- no pad corridor, no runway, no blast door.
-- HOLOGRAMS (owner, 16 Nov: "in the hub can the center gun thingy cycle your loadout but hologram style? we also need
-- holograms like in rivals with bundle sets that float and people can look at and interact with"): the builder only
-- leaves their places, B.holo: an invisible drum tagged HubHolo the size of the space a hologram may fill (attributes
-- Holo = "loadout" / "bundle", Slot, Radius, Height, Base = how far under its middle its lens is, Color = the palette's
-- accent). StarterPlayerScripts.HubHolo draws them on each player's screen: over the platform your own loadout in
-- turn, on the showroom's four plinths (the south wall either side of the lounge) the shop's bundles. R.check tests
-- the sight lines and keep-clear zones against those drums as if they were solid.
--   usage (Studio's command bar, Edit):
--     local R = require(game.ServerStorage.PolishBackup.HubRotunda:Clone()); print(R.build("live")); print(R.check())
--   R.build("stage")   a copy to look at, under workspace.Map.HubStage at R.STAGE (its pads are for show)
--   R.compare()        one copy of each palette side by side (R.COMPARE), to photograph; R.unstage() takes them away
--   R.build("live")    the real hub: Hub.Rotunda (Shell, Scenery, Collision), its five pads in Hub.QueuePads, spawn markers
--                      in Hub.HubSpawns, where the training hall's door lands you in Hub.Doors.HubArrive, the training
--                      gate's trigger in Hub.Doors. each of those is marked Built = "Rotunda". it takes the bowling
--                      centre away first (Hub.Lanes and everything marked Built = "HubLab")
--   R.check()          keep-clear zones, leaks, sight lines from every spawn point (pads, boards, the name, every door's
--                      name, one thing inside each room)
--   R.switch("lanes")  the bowling centre back (HubLab builds it; HubLab's own build also takes the Rotunda away, so
--                      HubLab's usage line alone does the same). R.switch("rotunda") = build("live") and check
-- a build wipes and remakes the hub: change the builder, never the built parts. the rooms are in three part modules
-- beside this one (R.PARTS); each returns function(B, R) and builds with the helpers below.
-- coordinates: the middle of the round room's floor is the origin. a FRAME is a bearing from that middle (0 = north,
-- the way you look when you spawn; 90 = east) and things are placed in it by x (to the right as you look outward), y
-- (up) and d (how far out from the middle). `face` is the way a thing's front looks in its frame: 0 = at the middle,
-- 180 = outward, 90 = to the right, -90 = to the left.
local R = {}
local hub = workspace.Map.Hub
local lib = game.ServerStorage.JankfireMeshes
local PB = game.ServerStorage.PolishBackup
local SP, Neon = Enum.Material.SmoothPlastic, Enum.Material.Neon

R.ROOM = "Rotunda" -- its folder in workspace.Map.Hub
R.MARK = "Rotunda" -- the Built attribute on what the server finds by name
R.SITE = Vector3.new(-200, 240, -10000) -- the hub's site (the bowling centre's too: only one of them is built at a time)
R.STAGE = Vector3.new(200, 240, -10000)
R.PARTS = { "HubRotundaCentre", "HubRotundaLifts", "HubRotundaRooms" }
R.PUSH = 32 -- (counts the pushes from the repo into Studio while the builder was being written)
-- the hub's own prop kit (tools/roblox/rotunda_props.py, one upload): chunky pieces that replaced the weakest old bc_
-- props on 16 Nov (owner: "some of the props dont look super like rivals ones!"). R.importProps() brings them into
-- JankfireMeshes; R.prop(new, old) places the new one if it is there, else the old
R.PROPS = 94371006780646 -- (the kit's Model asset: rk_planter, rk_punchbag, rk_tyres, rk_coffeetable, rk_lockers, rk_dumbbells, rk_bench)
-- the round room: 14 sides, 28 from the middle to a wall's face, walls and piers 3.4 thick, the ring balcony 14 up and
-- 5.5 deep. side i is at bearing i * 360 / 14; R.OPEN says which sides are ways out
R.N, R.A, R.WALL, R.RING_Y, R.RING_IN = 14, 28, 3.4, 14, 22.5
-- the FOCUS: the point on the platform, 6 south of the middle, that the spawn points stand round and that the five
-- lifts fan out from. each lift bay lies along the line from the focus through the middle of its opening, so from
-- where you appear every lift is framed by its own two piers (from the room's own middle they would be too far round
-- to the sides to be in a first look)
R.FOCUS = 6
R.OPEN = { [0] = "lift", [1] = "lift", [2] = "lift", [12] = "lift", [13] = "lift", [4] = "duels", [7] = "lounge", [10] = "armory" }
local TEAM = { "ff4fd8", "37d6ff", "ffe14d" } -- the teams' colours, in Matches' order
R.TEAM = TEAM
-- the five modes, left to right as you spawn: its side of the round room, and its pad's width and depth
R.MODES = {
	{ id = "1v1", title = "1V1", kind = "DUEL", teams = 2, size = 1, side = 12, w = 12.4, dp = 9.6 },
	{ id = "1v1v1", title = "1V1V1", kind = "THREE-WAY", teams = 3, size = 1, side = 13, w = 15.6, dp = 9.6 },
	{ id = "2v2", title = "2V2", kind = "DUOS", teams = 2, size = 2, side = 0, w = 13.6, dp = 11 },
	{ id = "3v3", title = "3V3", kind = "TRIOS", teams = 2, size = 3, side = 1, w = 14.4, dp = 11.2 },
	{ id = "4v4", title = "4V4", kind = "SQUADS", teams = 2, size = 4, side = 2, w = 15.6, dp = 11.2 },
}
-- THE DUEL HALL (side 4, where the gym was; HubRotundaRooms builds it): seven more pads round its walls (owner, 16 Nov:
-- "we also need more pads somewhere?"). R.HALL_BOX = x0, x1, the far wall's d, the height (side 4's frame: x to the
-- right looking outward, d out from the round room's middle); each pad: its name (= its PadId), its mode (R.MODES index),
-- the wall it stands against and where along it (far / near: x; left / right: d). R.HALL_SIZE = the hall pads' w, dp
R.HALL_BOX = { -25, 25, 92, 18 }
R.HALL_RING = 64 -- (how far out the ring's middle is, on the door's axis)
R.HALL_SIZE = { ["1v1"] = { 10, 8 }, ["2v2"] = { 12, 9 }, ["3v3"] = { 13.6, 10 } }
R.HALL = {
	{ name = "1v1_h1", mode = 1, wall = "far", at = -15.5 }, { name = "3v3_h1", mode = 4, wall = "far", at = 0 }, { name = "1v1_h2", mode = 1, wall = "far", at = 15.5 },
	{ name = "2v2_h1", mode = 3, wall = "left", at = 64 }, { name = "2v2_h2", mode = 3, wall = "right", at = 64 },
	{ name = "1v1_h3", mode = 1, wall = "near", at = -14.5 }, { name = "1v1_h4", mode = 1, wall = "near", at = 14.5 },
}
-- the paint. one palette is one switch (R.PALETTE); every palette paints the same build. the owner on the round hubs C to
-- G (16 Nov): "I like how it looked, I think with the new diesgn principles building somelike like it could be cool,
-- less colorfuil, maybe keep some color obviously, idk tryh different thing". so three treatments, photographed side by
-- side (R.compare), one picked as the default and the others kept here:
--   "arena"  calm slate and cream, near-monochrome: one pink line (the ring, the rail), yellow words over the lifts
--   "glow"   the cosy rotunda (E) made sober: a darker shell where the light does the work, the pink ring kept, a cyan
--            line to every lift and cyan words over them: a restrained version of the old neon pair
--   "warm"   warm stone, brass and timber: one amber accent instead of the pink, amber lines and words
-- keys (doorGlow and halo are optional: the glow palette's lit door lines and the ring over the name): shell/shell2 walls, pier/pier2 piers and frames, cream/creamHi the ring, rails and ribs, wood/band the dado and
-- the line over it, dome, floor/floor2, deck/padBase the lift decks, bay the shafts' back walls, plate the signs' plates,
-- accent the rail line, glow the platform's ring, ray the floor lines, dim the gallery's lit panels, word the words over
-- the lifts, train the training word, pale the words over the rooms, strip/panel/sky/light/warm the lights, brick/beam
-- /carpet the lounge, gymWall/gymFloor the gym, edge the pads' rims. remap repaints the kit's props (the colour in a
-- piece's name = its new colour): nothing near-black, nothing loud
R.PALETTE = "glow" -- (picked on 16 Nov from the three side by side: the closest to how the round hubs C to G looked, calmer)
local ARENA = {
	tint = "neutral",
	shell = "5e6672", shell2 = "68707c", pier = "3f4753", pier2 = "4a5260", cream = "ddd8cd", creamHi = "ece8df",
	wood = "bfae92", band = "62808a", dome = "767d86", floor = "6b7078", floor2 = "5a5f68", deck = "4f5863", padBase = "4f5863", bay = "78808c",
	plate = "2e3140", accent = "ff4fd8", glow = "ff4fd8", ray = "c9b660", dim = "858a92", word = "ffd84a", train = "7dff4f", pale = "f1ede2",
	strip = "f4f8ff", panel = "9a9fa8", sky = "8e9298", light = "f1f1ee", warm = "ffe2b8", brick = "a98b7c", beam = "8f7558", edge = "9a9fa8",
	carpet = "67635f", gymWall = "c4c0b6", gymFloor = "5a6069",
	flat = true, -- (brick, wood and crate grain become flat colour: "flat colours, no noisy textures", and round 1's judge)
	remap = { ["37d6ff"] = "86a9b3", ffe14d = "dccf9a", ["7dff4f"] = "9dbb93", ff9a1f = "cfa57c", ff4fd8 = "b7879f", ff4fd9 = "b7879f",
		["17141f"] = "3f4753", ["2e3140"] = "3f4753", ["2a2d38"] = "3f4753", ["120818"] = "3a414c", ["1b1b20"] = "3f4753", ["1a1824"] = "3f4753",
		["2a2c3e"] = "4a5260", ["26242e"] = "3f4753", ["1f2a3a"] = "3f4753", ["3b2a52"] = "e4ddcf", c8262e = "a8605c", ff2a3a = "c9605e", b44fff = "8f84a8",
		["3a3f4a"] = "566070", d6dbe3 = "b9bec8", ["5b6478"] = "566070", a4aab8 = "c9c5bb", ["8fe6ff"] = "a9c6cf", bfe9ff = "b9d0d6" },
}
local function over(base, t, remap)
	local p = table.clone(base)
	for k, v in t do p[k] = v end
	p.remap = table.clone(base.remap)
	for k, v in remap or {} do p.remap[k] = v end
	return p
end
R.PALETTES = {
	arena = ARENA,
	glow = over(ARENA, {
		-- (round 1's judge, 16 Nov: "the team colours leak into the building, so the pads don't stand out" and "the piers are
		-- near-black". so the pink, cyan and yellow are left to the pads and their boards; the building has ONE accent, a soft
		-- aqua, on the platform's ring, the floor lines, the lit strips and the ring over the showpiece; the piers are a
		-- mid slate, paler than the walls; floor, walls, piers and dome are four clearly different values)
		shell = "535a66", shell2 = "5c636f", pier = "68707c", pier2 = "747c88", cream = "b3aea4", creamHi = "c4bfb5",
		wood = "a48f6c", band = "6c6862", dome = "727a86", floor = "41464f", floor2 = "393e46", deck = "3a3f48", padBase = "3a3f48", bay = "6a727e",
		-- (round 2's judge, 16 Nov: teal had become a second base colour. so the aqua is kept to the floor lines and the
		-- platform's ring; the wall band, the gallery's panels and the ring overhead go neutral, the training word white)
		plate = "262a34", accent = "b3aea4", glow = "6fc9c9", ray = "4c8a8e", dim = "6a6e74", word = "e8eef2", pale = "e8eef2", strip = "d8eef2", panel = "8e98a2", sky = "7f8a96",
		train = "e8eef2", bayWash = "fff1dc", padCalm = 0.18,
		light = "e8f0f4", edge = "8e98a2", carpet = "4f4846", gymWall = "c9bfae", gymFloor = "4c515a",
		brick = "80746e", beam = "6b5a4c", -- (the lounge: flat brick under its warm lamps read salmon; a warm taupe and darker timber)
		doorGlow = "5fbcbf", halo = "d8eef2", -- (a line on every threshold; the ring over the showpiece)
	}, { f4f8ff = "d8eef2", ["17141f"] = "434a55", ["2e3140"] = "434a55", ["2a2d38"] = "434a55", ["1b1b20"] = "434a55", ["1a1824"] = "434a55",
		["26242e"] = "434a55", ["1f2a3a"] = "434a55", ["2a2c3e"] = "4c535e", ["5b6478"] = "5a616d", ["3a3f4a"] = "5a616d", a4aab8 = "b3aea4" }),
	warm = over(ARENA, {
		shell = "6b625b", shell2 = "746a62", pier = "463d37", pier2 = "51473f", cream = "e2d4bc", creamHi = "eee3cf",
		wood = "c49f72", band = "8c5f45", dome = "7b7068", floor = "6e665f", floor2 = "5e5751", deck = "4e4741", padBase = "4e4741", bay = "7d736a",
		plate = "2f2a28", accent = "e0a040", glow = "f0a646", ray = "d4a35c", dim = "958676", word = "ffcf7a", pale = "f5ecdc", strip = "ffe6c4",
		panel = "a89a88", sky = "a3968a", light = "fff0dc", warm = "ffd7a0", edge = "a89a88", carpet = "6b5446", gymWall = "d6c8b2", gymFloor = "625a54",
	}, { f4f8ff = "ffe6c4", ["37d6ff"] = "a9b39f", ff4fd8 = "c4977a", ff4fd9 = "c4977a", ["17141f"] = "463d37", ["2e3140"] = "463d37", ["2a2d38"] = "463d37",
		["120818"] = "463d37", ["1b1b20"] = "463d37", ["1a1824"] = "463d37", ["26242e"] = "463d37", ["1f2a3a"] = "463d37", ["2a2c3e"] = "51473f",
		["3b2a52"] = "eee3cf", d6dbe3 = "c8bba8", a4aab8 = "d2c3ab", ["5b6478"] = "6a5f57", ["3a3f4a"] = "5e544c", ["8fe6ff"] = "c9c2b0", bfe9ff = "d6cdb9" }),
}
-- side by side, to photograph: { palette, its site }. R.compare() builds one staging copy of each
R.COMPARE = { { "arena", Vector3.new(200, 240, -10000) }, { "glow", Vector3.new(600, 240, -10000) }, { "warm", Vector3.new(1000, 240, -10000) } }

local function folderIn(parent, name)
	local f = parent:FindFirstChild(name)
	if not f then f = Instance.new("Folder"); f.Name = name; f.Parent = parent end
	return f
end
local function hexOf(name) return name:match("_(%x%x%x%x%x%x)$") end

-- where a build's pieces are: the real hub's own folders, or the staging copy's (its Game folder)
function R.prop(new, old) return if lib:FindFirstChild(new) then new else old end
function R.propScale(new, sNew, sOld) return if lib:FindFirstChild(new) then sNew else sOld end
-- the prop kit into ServerStorage.JankfireMeshes, split by the pieces' names ("<model><n>__<kind>_<hex>"), each model's
-- pivot the file's own frame (its footprint's middle on the floor)
function R.importProps(id)
	id = id or R.PROPS
	local ok, container = pcall(function() return game:GetService("InsertService"):LoadAsset(id) end)
	if not ok or not container then return "LOAD FAILED " .. tostring(container) end
	local MAT = { plastic = SP, neon = Neon }
	local groups, bad = {}, 0
	for _, d in container:GetDescendants() do
		if not d:IsA("MeshPart") then continue end
		local model, kind, h = string.match(d.Name, "^(.-)%d+__(%a+)_(%x%x%x%x%x%x)")
		if not model or not MAT[kind] then bad += 1; continue end
		d.Material = MAT[kind]; d.Color = Color3.fromHex(h); d.TextureID = ""
		d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
		d.CastShadow = kind ~= "neon"
		groups[model] = groups[model] or {}
		table.insert(groups[model], d)
	end
	local names = {}
	for name, parts in groups do
		local m = Instance.new("Model")
		m.Name = name
		for _, p in parts do p.Parent = m end
		m.WorldPivot = CFrame.identity
		m:SetAttribute("AssetId", id); m:SetAttribute("Kit", "rotunda")
		local old = lib:FindFirstChild(name)
		if old then old:Destroy() end
		m.Parent = lib
		local _, size = m:GetBoundingBox()
		table.insert(names, ("%s %d (%.1f x %.1f x %.1f)"):format(name, #parts, size.X, size.Y, size.Z))
	end
	container:Destroy()
	table.sort(names)
	return #names .. " models" .. (if bad > 0 then ", " .. bad .. " pieces with no name rule" else "") .. "\n  " .. table.concat(names, "\n  ")
end

function R.places(stage) --(stage = the name of a staging copy's folder in workspace.Map; nil = the live hub, else HubStage)
	if not stage then
		local room = hub:FindFirstChild(R.ROOM)
		if room then
			return { live = true, O = R.SITE, room = room, pads = hub:FindFirstChild("QueuePads"), spawns = hub:FindFirstChild("HubSpawns"), arrive = hub.Doors:FindFirstChild("HubArrive"), doors = hub.Doors }
		end
		stage = "HubStage"
	end
	local st = workspace.Map:FindFirstChild(stage)
	local room = st and st:FindFirstChild(R.ROOM)
	local g = room and room:FindFirstChild("Game")
	if not g then return nil end
	return { live = false, O = room:GetAttribute("At") or R.STAGE, room = room, pads = g.QueuePads, spawns = g.HubSpawns, arrive = g.HubArrive, doors = g.Doors }
end
function R.frame(O, bearing, d, z0) return CFrame.new(O + Vector3.new(0, 0, z0 or 0)) * CFrame.Angles(0, -math.rad(bearing), 0) * CFrame.new(0, 0, -(d or 0)) end
-- the bearing, from the focus, of the middle of a side's opening; and how far from the focus a line at that bearing
-- crosses a circle r round the room's middle
function R.liftBearing(side)
	local b, r = math.rad(side * 360 / R.N), R.A + R.WALL / 2
	return math.deg(math.atan2(r * math.sin(b), r * math.cos(b) + R.FOCUS))
end
function R.reach(bearing, r)
	local b = math.rad(bearing)
	return R.FOCUS * math.cos(b) + math.sqrt(r * r - (R.FOCUS * math.sin(b)) ^ 2)
end

function R.new(live, opts)
	opts = opts or {}
	local pname = if R.PALETTES[opts.palette or R.PALETTE] then opts.palette or R.PALETTE else "arena"
	local P = table.clone(R.PALETTES[pname])
	P.name = pname
	local O = if live then R.SITE else opts.at or R.STAGE
	local stageName = opts.stage or "HubStage"
	local B = { live = live, O = O, P = P, G = { ghost = true }, count = 0, lamps = 0, shadows = 0, missing = {} }
	if live then
		for _, n in { R.ROOM, "Lanes" } do local old = hub:FindFirstChild(n); if old then old:Destroy() end end
		for _, f in { folderIn(hub, "QueuePads"), folderIn(hub, "HubSpawns"), folderIn(hub.Doors, "HubArrive"), hub.Doors } do
			for _, c in f:GetChildren() do local b = c:GetAttribute("Built"); if b == R.MARK or b == "HubLab" then c:Destroy() end end
		end
	else
		local stage = workspace.Map:FindFirstChild(stageName); if stage then stage:Destroy() end
	end
	local root = Instance.new("Folder"); root.Name = R.ROOM
	for _, n in { "Shell", "Scenery", "Collision" } do local f = Instance.new("Folder"); f.Name = n; f.Parent = root end
	B.root = root
	if live then
		B.pads, B.spawnFolder, B.arriveFolder, B.doors = hub.QueuePads, hub.HubSpawns, hub.Doors.HubArrive, hub.Doors
	else
		local g = Instance.new("Folder"); g.Name = "Game"; g.Parent = root
		B.pads, B.spawnFolder, B.arriveFolder, B.doors = folderIn(g, "QueuePads"), folderIn(g, "HubSpawns"), folderIn(g, "HubArrive"), folderIn(g, "Doors")
	end
	function B.fr(bearing, d) return R.frame(O, bearing, d) end
	function B.lf(bearing) return R.frame(O, bearing, 0, R.FOCUS) end -- a frame from the focus
	function B.side(i) return R.frame(O, i * 360 / R.N, 0) end
	function B.wid(r) return 2 * r * math.tan(math.pi / R.N) end -- a side's width, r from the middle

	-- a plain block: x0..x1 across, y0..y1 up, d0..d1 out. o.rot turns it about its own middle, o.ghost = seen but not
	-- felt (paint, trim), o.nc = no collision only
	function B.box(F, folder, name, x0, x1, y0, y1, d0, d1, hex, mat, o)
		o = o or {}
		local p = Instance.new(if o.wedge then "WedgePart" else "Part")
		p.Name = name; p.Anchored = true
		p.Size = Vector3.new(math.max(math.abs(x1 - x0), 0.05), math.max(math.abs(y1 - y0), 0.05), math.max(math.abs(d1 - d0), 0.05))
		p.CFrame = F * CFrame.new((x0 + x1) / 2, (y0 + y1) / 2, -(d0 + d1) / 2) * (o.rot or CFrame.identity)
		if P.flat and (mat == Enum.Material.Wood or mat == Enum.Material.Brick) then mat = SP end
		p.Color = Color3.fromHex(hex); p.Material = mat or SP
		p.Transparency = o.tr or 0
		if o.ghost then p.CanCollide = false; p.CanQuery = false; p.CanTouch = false end
		if o.nc then p.CanCollide = false end
		if o.noShadow or o.ghost then p.CastShadow = false end
		p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
		p.Parent = root[folder]
		B.count += 1
		return p
	end
	-- a disc or drum standing on its flat
	function B.cyl(F, folder, name, x, y0, y1, d, dia, hex, mat, o)
		local p = B.box(F, folder, name, x - dia / 2, x + dia / 2, y0, y1, d - dia / 2, d + dia / 2, hex, mat, o)
		p.Shape = Enum.PartType.Cylinder; p.Size = Vector3.new(math.max(y1 - y0, 0.05), dia, dia)
		p.CFrame = F * CFrame.new(x, (y0 + y1) / 2, -d) * CFrame.Angles(0, 0, math.pi / 2)
		return p
	end
	-- a slab w wide and t thick running from (dA, yA) to (dB, yB): dome panels, ribs, sloped soffits
	function B.bar(F, folder, name, x, w, t, dA, yA, dB, yB, hex, mat, o)
		local len = math.sqrt((dB - dA) ^ 2 + (yB - yA) ^ 2)
		local p = B.box(F, folder, name, x - w / 2, x + w / 2, 0, t, 0, len, hex, mat, o)
		p.CFrame = F * CFrame.new(x, (yA + yB) / 2, -(dA + dB) / 2) * CFrame.Angles(math.atan2(yB - yA, dB - dA), 0, 0)
		return p
	end
	-- a block d0..d1 deep and t thick running across a frame from (xA, yA) to (xB, yB): arch stones, cut corners
	function B.spar(F, folder, name, d0, d1, t, xA, yA, xB, yB, hex, mat, o)
		local len = math.sqrt((xB - xA) ^ 2 + (yB - yA) ^ 2)
		local p = B.box(F, folder, name, 0, len, 0, t, d0, d1, hex, mat, o)
		p.CFrame = F * CFrame.new((xA + xB) / 2, (yA + yB) / 2, -(d0 + d1) / 2) * CFrame.Angles(0, 0, math.atan2(yB - yA, xB - xA))
		return p
	end

	local boxSrc = hub.TrainingGround.PropCollision:FindFirstChild("RangeCounterBox")
	function B.solid(name, size, cf)
		local b
		if boxSrc then b = boxSrc:Clone() else b = Instance.new("Part"); b.Transparency = 1; b.Anchored = true; b.CanTouch = false end
		b.Name = name; b.Size = size; b.CFrame = cf; b.Parent = root.Collision
		return b
	end

	-- a model from the kit. (x, y, d) is the middle of its footprint on the floor it stands on (o.seat = "top": y is its
	-- top; "centre": its middle); o.back: the point its back goes against. o.scale, o.stretch = Vector3 (across, up,
	-- front to back; after the scale), o.color = { oldHex = newHex } (else the palette's remap), o.solid = true (its own
	-- box), a Vector3 (a box that size standing where it stands) or a list of { sx, sy, sz, ox, oy, oz }
	function B.put(F, tmpl, name, x, y, d, face, o)
		o = o or {}
		local t = lib:FindFirstChild(tmpl)
		if not t then B.missing[tmpl] = (B.missing[tmpl] or 0) + 1; return nil end
		local m = t:Clone(); m.Name = name or tmpl
		if o.scale and math.abs(o.scale - 1) > 0.005 then m:ScaleTo(o.scale) end
		local bcf, sz = m:GetBoundingBox()
		local st = o.stretch or Vector3.one
		local full = sz * st
		local a = math.rad(face or 0)
		local at = Vector3.new(x, y, -d)
		if o.back then at += Vector3.new(math.sin(a), 0, math.cos(a)) * (full.Z / 2) end
		local cy = if o.seat == "top" then y - full.Y / 2 elseif o.seat == "centre" then y else y + full.Y / 2
		local cf = F * CFrame.new(at.X, cy, at.Z) * CFrame.Angles(0, a, 0)
		m:PivotTo(cf * m:GetPivot():ToObjectSpace(bcf):Inverse())
		for _, p in m:GetDescendants() do
			if not p:IsA("BasePart") then continue end
			p.Anchored = true
			if o.stretch then
				local rel = cf:ToObjectSpace(p.CFrame)
				local function f(v) return math.abs(v.X) * st.X + math.abs(v.Y) * st.Y + math.abs(v.Z) * st.Z end
				p.Size = Vector3.new(p.Size.X * f(rel.RightVector), p.Size.Y * f(rel.UpVector), p.Size.Z * f(rel.LookVector))
				p.CFrame = cf * CFrame.new(rel.Position * st) * rel.Rotation
			end
			local key = hexOf(p.Name)
			local new = key and ((o.color and o.color[key]) or (not o.raw and P.remap[key]))
			if new then p.Color = Color3.fromHex(new) end
			if not o.keepMat and (p.Material == Enum.Material.Metal or p.Material == Enum.Material.Fabric or p.Material == Enum.Material.Rubber or p.Material == Enum.Material.DiamondPlate
				or (P.flat and (p.Material == Enum.Material.Wood or p.Material == Enum.Material.Brick))) then p.Material = SP end
			if o.noShadow then p.CastShadow = false end
		end
		m.Parent = root.Scenery
		local base = cf * CFrame.new(0, -full.Y / 2, 0)
		if typeof(o.solid) == "table" then
			for i, b in o.solid do B.solid((name or tmpl) .. "Box" .. i, Vector3.new(b[1], b[2], b[3]), base * CFrame.new(b[4] or 0, b[5] or b[2] / 2, b[6] or 0)) end
		elseif o.solid then
			local s = if typeof(o.solid) == "Vector3" then o.solid else full
			B.solid((name or tmpl) .. "Box", s, base * CFrame.new(0, s.Y / 2, 0))
		end
		B.count += 1
		return m, full, cf
	end

	-- one of the game's own weapon models as a display piece, `len` studs long, its middle at (x, y, d) in F. yaw 0 =
	-- its length across F (seen side-on from the middle), -90 or 90 = its length along F's d. no collision, no shadow,
	-- nothing that runs or sounds. its pivot is its middle, so HubLife can turn it in place (tag HubSpin)
	function B.gun(F, wname, len, x, y, d, yaw, name)
		local src = game.ReplicatedStorage:FindFirstChild("JankfireWeapons")
		local t = src and src:FindFirstChild(wname)
		if not t then B.missing[wname] = (B.missing[wname] or 0) + 1; return nil end
		local g = t:Clone(); g.Name = name or ("Gun_" .. wname)
		local Tags = game:GetService("CollectionService")
		for _, tag in Tags:GetTags(g) do Tags:RemoveTag(g, tag) end
		for _, q in g:GetDescendants() do
			if q:IsA("BasePart") then q.Anchored = true; q.CanCollide = false; q.CanQuery = false; q.CanTouch = false; q.CastShadow = false
			elseif q:IsA("LuaSourceContainer") or q:IsA("Sound") or q:IsA("ParticleEmitter") or q:IsA("Light") or q:IsA("Beam") or q:IsA("Trail") then q:Destroy() end
		end
		local _, sz = g:GetBoundingBox()
		g:ScaleTo(g:GetScale() * (len / math.max(sz.Z, 0.01)))
		local bcf = g:GetBoundingBox()
		local at = F * CFrame.new(x, y, -d) * CFrame.Angles(0, math.rad(90 + (yaw or 0)), 0)
		g:PivotTo(at * g:GetPivot():ToObjectSpace(bcf):Inverse())
		g.PrimaryPart = nil; g.WorldPivot = at
		g.Parent = root.Scenery
		B.count += 1
		return g
	end

	-- words on a plate. lines = { { text, hex, "B" (heavy) or "S", share of the height }, ... } top to bottom. o.both =
	-- the same on the back, o.clear = no plate, o.flush = (x, y, d) is the face the words are on, o.plate = its colour
	function B.text(F, name, lines, w, h, x, y, d, face, o)
		o = o or {}
		local thick = o.thick or 0.3
		local p = Instance.new("Part")
		p.Name = name; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
		p.Size = Vector3.new(w, h, thick)
		p.Color = Color3.fromHex(o.plate or P.plate); p.Material = SP
		p.Transparency = if o.clear then 1 else 0
		local a = math.rad(face or 0)
		local at = Vector3.new(x, y, -d)
		if o.flush then at -= Vector3.new(math.sin(a), 0, math.cos(a)) * (thick / 2) end
		p.CFrame = F * CFrame.new(at) * CFrame.Angles(0, a + math.pi, 0) * (o.rot or CFrame.identity)
		local sides = { Enum.NormalId.Front }
		if o.both then table.insert(sides, Enum.NormalId.Back) end
		for _, sd in sides do
			local total, tallest = 0, 0
			for _, ln in lines do total += ln[4]; tallest = math.max(tallest, ln[4]) end
			local k = 0.92 / math.max(total, 0.01)
			local g = Instance.new("SurfaceGui")
			g.Name = "Gui"; g.Face = sd; g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
			g.PixelsPerStud = math.min(o.pps or 30, math.max(8, math.floor(100 / math.max(tallest * k * h, 0.01))))
			g.LightInfluence = 0
			local yAt = 0.04
			for i, ln in lines do
				local t = Instance.new("TextLabel")
				t.Name = "Line" .. i; t.BackgroundTransparency = 1; t.TextScaled = true; t.RichText = o.rich or false
				t.Text = ln[1]; t.TextColor3 = Color3.fromHex(ln[2] or "ffffff")
				t.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", if ln[3] == "S" then Enum.FontWeight.SemiBold else Enum.FontWeight.Heavy)
				t.Size = UDim2.new(0.94, 0, ln[4] * k, 0); t.Position = UDim2.new(0.03, 0, yAt, 0)
				t.Parent = g
				yAt += ln[4] * k
			end
			g.Parent = p
		end
		p.Parent = root.Scenery
		B.count += 1
		return p
	end

	-- a real light at a point. o.spot (o.angle, o.face), o.shadows (at most about 11 of those in the hub)
	function B.lamp(F, x, y, d, range, bright, hex, o)
		o = o or {}
		local p = Instance.new("Part")
		p.Name = "LampSpot"; p.Size = Vector3.new(1, 0.2, 1); p.Transparency = 1; p.Anchored = true
		p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
		p.CFrame = F * CFrame.new(x, y, -d)
		local l = Instance.new(if o.spot then "SpotLight" else "PointLight")
		l.Range = range; l.Brightness = bright; l.Color = Color3.fromHex(hex or P.light); l.Shadows = o.shadows or false
		if o.spot then l.Face = o.face or Enum.NormalId.Bottom; l.Angle = o.angle or 120 end
		l.Parent = p
		p.Parent = root.Scenery
		B.lamps += 1
		if l.Shadows then B.shadows += 1 end
		return p
	end
	-- a hologram's place (see the top): its middle at (x, y, d), r across from its axis, h tall. o.base = how far under
	-- its middle the lens it rises from is (0 = no beam), o.slot = which bundle, o.prompt = a ProximityPrompt on it
	function B.holo(F, name, kind, x, y, d, r, h, o)
		o = o or {}
		local p = B.cyl(F, "Scenery", name, x, y - h / 2, y + h / 2, d, 2 * r, P.glow, nil, { ghost = true, tr = 1 })
		p:SetAttribute("Holo", kind); p:SetAttribute("HoloEnvelope", true)
		p:SetAttribute("Radius", r); p:SetAttribute("Height", h); p:SetAttribute("Base", o.base or 0)
		p:SetAttribute("Color", P.holo or P.glow)
		if o.slot then p:SetAttribute("Slot", o.slot) end
		if o.prompt then
			local pr = Instance.new("ProximityPrompt")
			pr.Name = "BundlePrompt"; pr.ActionText = o.prompt; pr.ObjectText = "Bundle"
			pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX; pr.HoldDuration = 0
			pr.MaxActivationDistance = 10; pr.RequiresLineOfSight = false; pr.ClickablePrompt = true
			pr.Exclusivity = Enum.ProximityPromptExclusivity.OnePerButton
			pr.Parent = p
		end
		game:GetService("CollectionService"):AddTag(p, "HubHolo")
		return p
	end
	-- a white light panel let into a ceiling whose underside is y: w across, l deep. o.hex = its colour
	function B.panel(F, x, y, d, w, l, o)
		o = o or {}
		B.box(F, "Scenery", "PanelHousing", x - w / 2 - 0.35, x + w / 2 + 0.35, y - 0.45, y + 0.05, d - l / 2 - 0.35, d + l / 2 + 0.35, P.pier, nil, B.G)
		return B.box(F, "Scenery", "LightPanel", x - w / 2, x + w / 2, y - 0.55, y - 0.4, d - l / 2, d + l / 2, o.hex or P.panel, Neon, B.G)
	end
	-- paint on a floor whose top is y
	function B.paint(F, name, x0, x1, y, d0, d1, hex, lift)
		return B.box(F, "Scenery", name, x0, x1, y + (lift or 0.03), y + (lift or 0.03) + 0.03, d0, d1, hex, nil, B.G)
	end

	-- a queue pad: a dark base, the team plates side by side (pink on the left as you face outward, the way the counts
	-- on its board read), a place for everybody on each plate: a socket with a white light in it, which is the Slot
	-- Matches switches (Off = 1: clear while the place is empty). y = the top of the deck it lies on
	function B.pad(F, md, x, y, d)
		local m = Instance.new("Model"); m.Name = md.name or md.id
		m:SetAttribute("Mode", md.id); m:SetAttribute("Teams", md.teams); m:SetAttribute("Size", md.size)
		-- (several pads share a mode since the duel hall: PadId tells them apart, Bank says where it stands)
		m:SetAttribute("PadId", m.Name); m:SetAttribute("Bank", md.bank or "lifts")
		m:SetAttribute(if live then "Built" else "ForShow", if live then R.MARK else true)
		local function plate(pn, cx, cd, sx, sd, hex, mat, yy, th)
			local p = Instance.new("Part")
			p.Name = pn; p.Anchored = true; p.Size = Vector3.new(sx, th, sd)
			p.CFrame = F * CFrame.new(x + cx, y + yy, -(d + cd))
			p.Color = Color3.fromHex(hex); p.Material = mat or SP
			p.CanCollide = false; p.CastShadow = false; p.TopSurface = Enum.SurfaceType.Smooth; p.Parent = m
			return p
		end
		plate("Base", 0, 0, md.w, md.dp, P.padBase, nil, 0.04, 0.08)
		local n = md.teams
		local pw, pd = (md.w - 1.2 - (n - 1) * 0.8) / n, md.dp - 1.2
		local cols = if md.size >= 4 then 2 else 1
		local rows = math.ceil(md.size / cols)
		for i = 1, n do
			local cx = -(md.w - 1.2) / 2 + pw / 2 + (i - 1) * (pw + 0.8)
			local s = plate("Side" .. i, cx, 0, pw, pd, TEAM[i], nil, 0.12, 0.14)
			if P.padCalm then s.Color = s.Color:Lerp(Color3.fromHex("8a8f98"), P.padCalm) end -- (a little under the full team colour: the plates were the loudest thing in the hub)
			s:SetAttribute("Team", i)
			for sl = 1, md.size do
				local c, r = (sl - 1) % cols, math.floor((sl - 1) / cols)
				local ox = if cols == 1 then 0 else (c - 0.5) * (pw / 2)
				local od = pd * (0.5 - (r + 0.5) / rows)
				local at = F * CFrame.new(x + cx + ox, y + 0.25, -(d + od)) * CFrame.Angles(0, 0, math.pi / 2)
				for _, k in { { "Socket", 3.2, 0.12, -0.04 }, { "Slot", 2.3, 0.14, 0 } } do
					local q = Instance.new("Part")
					q.Name = k[1]; q.Shape = Enum.PartType.Cylinder; q.Anchored = true; q.Size = Vector3.new(k[3], k[2], k[2])
					q.CFrame = at * CFrame.new(k[4], 0, 0)
					q.CanCollide = false; q.CanQuery = false; q.CanTouch = false; q.CastShadow = false
					if k[1] == "Slot" then
						q.Color = Color3.fromHex("f4f8ff"); q.Material = Neon; q.Transparency = 1
						q:SetAttribute("Team", i); q:SetAttribute("Slot", sl); q:SetAttribute("Off", 1)
					else
						q.Color = s.Color:Lerp(Color3.new(0, 0, 0), 0.22); q.Material = SP
					end
					q.Parent = m
				end
			end
		end
		for _, e in { { 0, md.dp / 2 - 0.2, md.w, 0.4 }, { 0, -md.dp / 2 + 0.2, md.w, 0.4 }, { md.w / 2 - 0.2, 0, 0.4, md.dp }, { -md.w / 2 + 0.2, 0, 0.4, md.dp } } do
			plate("Edge", e[1], e[2], e[3], e[4], P.edge, Neon, 0.14, 0.1)
		end
		m.Parent = B.pads
		B.count += 1
		return m
	end
	-- a pad's board, in the pad's model as its Sign: the mode, its kind, and the two lines Matches writes every 0.15 s
	-- on every label named Status and Sub in the pad (who is waiting, in the teams' colours; what happens next)
	function B.board(pad, F, md, w, h, x, y, d, face, o)
		o = o or {}
		local counts = {}
		for t = 1, md.teams do table.insert(counts, ('<font color="#%s">0/%d</font>'):format(TEAM[t], md.size)) end
		local p = B.text(F, "Sign", { { md.title, P.pale, "B", 0.3 }, { md.kind, "c8cdd6", "S", 0.13 }, { table.concat(counts, "   vs   "), "ffffff", "B", 0.33 }, { "step on a side to queue", "c8c8dc", "S", 0.15 } },
			w, h, x, y, d, face, { thick = o.thick or 0.4, plate = o.plate or "20232e", pps = 46, both = o.both })
		for _, g in p:GetChildren() do
			if g:IsA("SurfaceGui") then g.Line3.Name = "Status"; g.Status.RichText = true; g.Line4.Name = "Sub" end
		end
		p.Parent = pad
		return p
	end

	-- where you appear: list of { x, d } in the north frame, standing on a floor y up. each looks north
	local function marker(name, x, y, d, lookBearing, folder)
		local p = Instance.new("Part")
		p.Name = name; p.Size = Vector3.new(2, 0.2, 2); p.Transparency = 1; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
		local at = B.fr(0) * Vector3.new(x, y + 0.1, -d)
		local f = B.fr(lookBearing).LookVector
		p.CFrame = CFrame.lookAt(at, at + f)
		if live then p:SetAttribute("Built", R.MARK) end
		p.Parent = folder
		return p
	end
	function B.spawns(list, y) for _, s in list do marker("HubSpawn", s[1], y, s[2], 0, B.spawnFolder) end end
	-- where the training hall's door lands you: F's own x, d; you look the way `face` says
	function B.arrive(F, list, y, lookBearing)
		for _, s in list do
			local w = F * Vector3.new(s[1], 0, -s[2])
			local l = B.fr(0):PointToObjectSpace(w)
			marker("Arrive", l.X, y, -l.Z, lookBearing, B.arriveFolder)
		end
	end
	-- a box you walk into to be taken somewhere: land = a marker folder in Hub.Doors, or "@TrainSpawns"
	function B.trigger(F, name, x0, x1, y0, y1, d0, d1, land, say)
		local p = Instance.new("Part")
		p.Name = name; p.Anchored = true; p.Transparency = 1; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
		p.Size = Vector3.new(math.abs(x1 - x0), math.abs(y1 - y0), math.abs(d1 - d0))
		p.CFrame = F * CFrame.new((x0 + x1) / 2, (y0 + y1) / 2, -(d0 + d1) / 2)
		p:SetAttribute("Land", land); p:SetAttribute("Say", say)
		if live then p:SetAttribute("Built", R.MARK) end
		p.Parent = B.doors
		return p
	end
	-- a jump pad (Move throws you off any part with a Pad attribute: its launch velocity). vel = (to the right, up, outward)
	function B.jump(F, x, y, d, face, vel, scale)
		scale = scale or 0.8
		B.put(F, "bc_jumppad", "JumpPad", x, y, d, face, { scale = scale, color = { ff4fd8 = P.pier2, ["37d6ff"] = P.pier2, ffe14d = P.ray, d6dbe3 = P.pier2 } })
		local h = 4.2 * scale * 0.8
		local jp = B.box(F, "Scenery", "JumpPadTop", x - h, x + h, y, y + 0.5 * scale, d - h, d + h, P.pier, nil, { tr = 1 })
		jp:SetAttribute("Pad", F:VectorToWorldSpace(Vector3.new(vel.X, vel.Y, -vel.Z)))
		return jp
	end

	function B.done()
		for _, p in root:GetDescendants() do if p:IsA("BasePart") then p.Anchored = true end end
		root:SetAttribute("Palette", P.name); root:SetAttribute("Live", live); root:SetAttribute("At", O)
		local home = if live then hub else folderIn(workspace.Map, stageName)
		if live then
			hub:SetAttribute("Origin", O) -- (Matches: the fall line is 60 under this, the last-ditch spawn point 3 over it)
			local look = game.ReplicatedStorage.Jankfire:FindFirstChild("HubLook")
			if look then look:SetAttribute("HubTint", P.tint) end
		end
		-- (into the place in pieces: one write of the whole hub can stall Studio)
		local kids = root:GetChildren()
		for _, f in kids do f.Parent = nil end
		root.Parent = home
		for _, f in kids do f.Parent = root; task.wait() end
		local parts = 0
		for _, p in root:GetDescendants() do if p:IsA("BasePart") then parts += 1 end end
		local miss = {}
		for k, n in B.missing do table.insert(miss, k .. " x" .. n) end
		return ("%s (%s) built %s at (%d, %d, %d): %d things, %d parts, %d lamps, %d with shadows%s"):format(R.ROOM, P.name, if live then "LIVE" else "as a staging copy", O.X, O.Y, O.Z,
			#root:GetDescendants(), parts, B.lamps, B.shadows, if #miss > 0 then "  MISSING: " .. table.concat(miss, ", ") else "")
	end
	return B
end

-- mode "live" or "stage"; opts (both optional) = { palette = a key of R.PALETTES, at = a staging copy's site, stage =
-- its folder's name in workspace.Map }
function R.build(mode, opts)
	local live = mode == "live"
	local parts = {}
	for _, n in R.PARTS do
		local src = PB:FindFirstChild(n)
		if not src then return "no " .. n .. " in PolishBackup: nothing built" end
		local m = src:Clone(); local fn = require(m); m:Destroy()
		table.insert(parts, fn)
	end
	local B = R.new(live, opts)
	for _, fn in parts do fn(B, R); task.wait() end
	return B.done()
end

-- one staging copy of every palette in R.COMPARE, side by side, each checked
function R.compare()
	local out = {}
	for _, c in R.COMPARE do
		local name = "HubStage_" .. c[1]
		table.insert(out, R.build("stage", { palette = c[1], at = c[2], stage = name }))
		table.insert(out, (R.check(name):match("^[^\n]+")))
	end
	return table.concat(out, "\n")
end

-- the bowling centre back, or the Rotunda
function R.switch(which)
	if which == "lanes" then
		local m = PB.HubLab:Clone(); local L = require(m); m:Destroy()
		return "the bowling centre: " .. tostring(L.build("Hub3_Lanes")) .. "\n" .. L.check()
	end
	return R.build("live") .. "\n" .. R.check()
end

-- what the other edit-time tools had to learn about this hub, once (2026-11-15). safe to run again: each edit is made
-- only if its old text is still there, exactly once, and the script still parses afterwards.
--   HubLab        its build takes the Rotunda and everything marked Built = "Rotunda" away, so the bowling centre comes
--                 back with HubLab's own usage line
--   OverlapCheck  run() hands over to R.check() while the Rotunda is the hub
--   StudioExport  the four builder modules are in its list of helpers
-- it also takes the staging copy away (workspace.Map.HubStage)
function R.install()
	local out = {}
	local function edit(script, pairs)
		local s = script.Source
		for _, pr in pairs do
			local a, b = pr[1], pr[2]
			local i = s:find(a, 1, true)
			if not i then
				table.insert(out, script.Name .. (if s:find(b, 1, true) then ": already done" else ": OLD TEXT NOT FOUND: " .. a:sub(1, 60)))
				return
			end
			if s:find(a, i + 1, true) then table.insert(out, script.Name .. ": old text is there twice: " .. a:sub(1, 60)); return end
			s = s:sub(1, i - 1) .. b .. s:sub(i + #a)
		end
		local f, err = loadstring(s)
		if not f then table.insert(out, script.Name .. ": would not parse: " .. tostring(err)); return end
		script.Source = s
		table.insert(out, script.Name .. ": edited, " .. #s .. " characters")
	end
	edit(PB.HubLab, {
		{ 'local old = hub:FindFirstChild(L.ROOM); if old then old:Destroy() end\n\t\tH.padFolder',
			'for _, n in { L.ROOM, "Rotunda" } do local old = hub:FindFirstChild(n); if old then old:Destroy() end end -- ("Rotunda": the other hub, built by HubRotunda. only one of the two stands at a time)\n\t\tH.padFolder' },
		{ 'for _, c in f:GetChildren() do if c:GetAttribute("Built") == "HubLab" then c:Destroy() end end',
			'for _, c in f:GetChildren() do local b = c:GetAttribute("Built"); if b == "HubLab" or b == "Rotunda" then c:Destroy() end end' },
	})
	edit(PB.OverlapCheck, {
		{ 'if hub:FindFirstChild("Lanes") then return (require(game.ServerStorage.PolishBackup.HubLab:Clone()) :: any).check() end',
			'if hub:FindFirstChild("Rotunda") then return (require(game.ServerStorage.PolishBackup.HubRotunda:Clone()) :: any).check() end\n\tif hub:FindFirstChild("Lanes") then return (require(game.ServerStorage.PolishBackup.HubLab:Clone()) :: any).check() end' },
	})
	edit(PB.StudioExport, {
		{ '"StudioExport", "HubLab", "KitImport",', '"StudioExport", "HubLab", "HubRotunda", "HubRotundaCentre", "HubRotundaLifts", "HubRotundaRooms", "KitImport",' },
	})
	return table.concat(out, "\n") .. "\n" .. R.unstage() .. "\n" .. R.status()
end
-- every staging copy away (the folders in workspace.Map whose names start with HubStage)
function R.unstage()
	local n = 0
	for _, c in workspace.Map:GetChildren() do if c.Name:sub(1, 8) == "HubStage" then c:Destroy(); n += 1 end end
	return n .. " staging copies removed"
end
-- one line on what stands where
function R.status()
	local n = {}
	table.insert(n, "hub: " .. (if hub:FindFirstChild(R.ROOM) then "the Rotunda" elseif hub:FindFirstChild("Lanes") then "the bowling centre" else "NONE"))
	for _, name in { "QueuePads", "HubSpawns" } do local f = hub:FindFirstChild(name); table.insert(n, name .. " " .. (if f then #f:GetChildren() else 0)) end
	local arr = hub.Doors:FindFirstChild("HubArrive")
	table.insert(n, "HubArrive " .. (if arr then #arr:GetChildren() else 0))
	local doors = {}
	for _, d in hub.Doors:GetChildren() do if d:GetAttribute("Land") then table.insert(doors, d.Name) end end
	table.insert(n, "door triggers: " .. table.concat(doors, " "))
	local live = hub:FindFirstChild(R.ROOM)
	if live then table.insert(n, "palette " .. tostring(live:GetAttribute("Palette")) .. ", Live " .. tostring(live:GetAttribute("Live"))) end
	local st = 0
	for _, c in workspace.Map:GetChildren() do if c.Name:sub(1, 8) == "HubStage" then st += 1 end end
	table.insert(n, "staging copies " .. st)
	table.insert(n, "Lighting.Previewing " .. tostring(game.Lighting:GetAttribute("Previewing")))
	table.insert(n, "HubTint " .. tostring(game.ReplicatedStorage.Jankfire.HubLook:GetAttribute("HubTint")))
	local calm, all = 0, 0
	local ws = game.ReplicatedStorage:FindFirstChild("JankfireWeapons")
	for _, w in (if ws then ws:GetChildren() else {}) do all += 1; if w:GetAttribute("Paint") == "calm" then calm += 1 end end
	table.insert(n, ("weapons in the calm paint %d of %d"):format(calm, all))
	return table.concat(n, ", ")
end

-- ------------------------------------------------------------------ the check
-- walks that must stay clear, 0.4 to 8 over their floor: { what, bearing, x0, x1, d0, d1, floor y }
R.WALKS = {}
-- from where the leak test looks out in 26 directions: { bearing, x, y, d }
R.LEAKS = {}
-- what must show from every spawn point besides the pads' plates and boards: { what, its name in Scenery }
R.SIGHTS = { { "the name on the gallery over the middle lift", "GalleryName" } }
-- the overlap test: kit models set into walls, lids or floors on purpose are left out; parts are shrunk by this much first
R.STRUCTURE = { Pier = true, Rail = true, DomeRing = true, Bezel = true, TrainingPortal = true, WallLight = true, DropLight = true, CrownDuck = true, HoloProjector = true, HoloDuck = true }
R.OVERLAP_GAP = 0.06
local STEP = 360 / R.N
local DUELS, LOUNGE, ARM = 4 * STEP, 7 * STEP, 10 * STEP
R.DECK0, R.DECK1 = 49.8, 62.6 -- a lift's deck, from the focus: its front and the face of the wall behind it
for _, md in R.MODES do
	local b = R.liftBearing(md.side)
	table.insert(R.WALKS, { "the way from the platform to the " .. md.title .. " lift", b, -4.2, 4.2, R.reach(b, 14), R.DECK0 - 0.2, 0, R.FOCUS })
	table.insert(R.WALKS, { "the walk in front of the " .. md.title .. " lift", b, -5, 5, R.reach(b, 33.2), R.DECK0 - 0.2, 0, R.FOCUS })
	table.insert(R.LEAKS, { b, 0, 6, 43, R.FOCUS }); table.insert(R.LEAKS, { b, 0, 10, 56, R.FOCUS })
	table.insert(R.SIGHTS, { md.title .. " over its way in", "Way_" .. md.id })
end
for _, w in { { "the way to the lounge", LOUNGE, -4.2, 4.2, 14, 41, 0 }, { "the way into the duel hall", DUELS, -4.5, 4.5, 14, 44.5, 0 },
	{ "the way to the training gate", ARM, -4.2, 4.2, 14, 60.4, 0 }, { "the armory's aisle", ARM, -6, 6, 38.6, 60.4, 0 } } do table.insert(R.WALKS, w) end
for _, p in { { 0, 0, 8, 0 }, { 0, 0, 22, 0 }, { 0, 0, 18, 25 }, { 180, 0, 18, 25 }, { LOUNGE, 0, 6, 34 }, { LOUNGE, 0, 6, 50 }, { DUELS, 0, 6, 35 }, { DUELS, 0, 9, 50 }, { DUELS, 0, 10, 82 }, { ARM, 0, 6, 34 }, { ARM, 0, 6, 50 } } do table.insert(R.LEAKS, p) end
for _, w in { { "TRAINING over the armory's hatch", "Way_training" }, { "DUELS over its door", "Way_duels" }, { "LOUNGE over its arch", "Way_lounge" }, { "the duck in the lounge", "HoloDuck", true },
	{ "the training gate at the armory's far end", "TrainingPortal", true }, { "the target over the duel hall's 3v3", "Target", true } } do table.insert(R.SIGHTS, w) end
for k = 1, 3 do table.insert(R.SIGHTS, { "the bundle hologram on plinth " .. k, "HoloBundle" .. k, true }) end

local function obb(cfA, hA, cfB, hB)
	local A = { cfA.RightVector, cfA.UpVector, cfA.LookVector }
	local Bx = { cfB.RightVector, cfB.UpVector, cfB.LookVector }
	local a, b = { hA.X, hA.Y, hA.Z }, { hB.X, hB.Y, hB.Z }
	local T = cfB.Position - cfA.Position
	local function sep(ax)
		local ra, rb = 0, 0
		for i = 1, 3 do ra += a[i] * math.abs(A[i]:Dot(ax)); rb += b[i] * math.abs(Bx[i]:Dot(ax)) end
		return math.abs(T:Dot(ax)) > ra + rb - 0.05
	end
	for i = 1, 3 do if sep(A[i]) or sep(Bx[i]) then return false end end
	for i = 1, 3 do for j = 1, 3 do local c = A[i]:Cross(Bx[j]); if c.Magnitude > 1e-4 and sep(c.Unit) then return false end end end
	return true
end

function R.check(stage)
	local W = R.places(stage)
	if not W then return "no " .. R.ROOM .. " in Map.Hub or Map.HubStage: build it first" end
	local room, O = W.room, W.O
	local zones = {}
	local function zone(what, cf, half) table.insert(zones, { what = what, cf = cf, half = half }) end
	for _, f in { W.spawns, W.arrive } do
		for _, s in f:GetChildren() do
			if s:GetAttribute("Built") == R.MARK or not W.live then
				local p = s.Position
				zone(("%s at (%.1f, %.1f)"):format(s.Name, p.X - O.X, p.Z - O.Z), CFrame.new(p.X, p.Y - 0.1 + 4.2, p.Z), Vector3.new(4, 3.8, 4))
			end
		end
	end
	local pads = {}
	for _, pad in W.pads:GetChildren() do
		if pad:IsA("Model") and (pad:GetAttribute("Built") == R.MARK or not W.live) then
			table.insert(pads, pad)
			local b = pad:FindFirstChild("Base")
			if b then zone("pad " .. pad.Name, b.CFrame * CFrame.new(0, 4.2, 0), Vector3.new(b.Size.X / 2, 3.8, b.Size.Z / 2)) end
		end
	end
	for _, w in R.WALKS do
		zone(w[1], R.frame(O, w[2], 0, w[8]) * CFrame.new((w[3] + w[4]) / 2, (w[7] or 0) + 4.2, -(w[5] + w[6]) / 2), Vector3.new(math.abs(w[4] - w[3]) / 2, 3.8, math.abs(w[6] - w[5]) / 2))
	end
	local issues, seen, looked = {}, {}, 0
	local game_ = room:FindFirstChild("Game")
	for _, p in room:GetDescendants() do
		-- (a thing counts if you can see it or bump into it: lamp points and markers do not)
		if not p:IsA("BasePart") or (p.Transparency >= 1 and not p.CanCollide and not p:GetAttribute("HoloEnvelope")) or (game_ and p:IsDescendantOf(game_)) then continue end
		looked += 1
		local round = p:IsA("Part") and p.Shape == Enum.PartType.Cylinder
		for _, z in zones do
			local hit = obb(p.CFrame, p.Size / 2, z.cf, z.half)
			-- (a drum standing on its flat is round: how far its axis is from the zone's box decides)
			if hit and round and math.abs(p.CFrame.RightVector.Y) > 0.99 then
				local c = z.cf:PointToObjectSpace(p.Position)
				local dx, dz = math.max(math.abs(c.X) - z.half.X, 0), math.max(math.abs(c.Z) - z.half.Z, 0)
				hit = dx * dx + dz * dz < (p.Size.Y / 2 - 0.05) ^ 2
			end
			if hit then
				local top = p
				while top.Parent and top.Parent.Parent ~= room do top = top.Parent end
				local line = ("%s/%s  in  %s"):format(top.Parent and top.Parent.Name or "?", top.Name, z.what)
				if not seen[line] then seen[line] = true; table.insert(issues, line) end
			end
		end
	end
	-- props through props (the owner's play-test, 16 Nov: an SMG through a case, the katana through an ammo box): every
	-- pair of kit models and display guns in Scenery, part against part, each part shrunk by R.OVERLAP_GAP so things
	-- that only touch pass. the structural kit set into walls and lids on purpose (R.STRUCTURE) is left out
	local props = {}
	for _, m in room.Scenery:GetChildren() do
		if not m:IsA("Model") or R.STRUCTURE[m.Name] then continue end
		local parts = {}
		for _, p in m:GetDescendants() do if p:IsA("BasePart") and p.Transparency < 0.95 then table.insert(parts, p) end end
		if #parts > 0 then local cf, sz = m:GetBoundingBox(); table.insert(props, { m = m, parts = parts, cf = cf, half = sz / 2 }) end
	end
	local g = R.OVERLAP_GAP
	local function shrunk(p) return Vector3.new(math.max(p.Size.X / 2 - g, 0.01), math.max(p.Size.Y / 2 - g, 0.01), math.max(p.Size.Z / 2 - g, 0.01)) end
	local overlaps = 0
	for i = 1, #props do
		for j = i + 1, #props do
			local a, b = props[i], props[j]
			if not obb(a.cf, a.half, b.cf, b.half) then continue end
			local hit = nil
			for _, p in a.parts do
				for _, q in b.parts do
					if obb(p.CFrame, shrunk(p), q.CFrame, shrunk(q)) then hit = { p, q }; break end
				end
				if hit then break end
			end
			if hit then
				overlaps += 1
				local at = hit[1].Position - O
				table.insert(issues, ("OVERLAP: %s (%s) goes into %s (%s) near (%.1f, %.1f, %.1f)"):format(a.m.Name, hit[1].Name, b.m.Name, hit[2].Name, at.X, at.Y, at.Z))
			end
		end
	end
	-- sight: from the eye over every spawn marker (4.7 over it) the middle of every pad's plates, three points across
	-- every board and everything in R.SIGHTS must show. anything you can see counts as in the way, solid or not; a
	-- part is tested as its own box, turned as it is turned
	local blockers = {}
	for _, f in { room, W.pads } do
		for _, q in f:GetDescendants() do
			if q:IsA("BasePart") and (q.Transparency < 0.5 or q:GetAttribute("HoloEnvelope")) then -- (a hologram's drum: what may stand there)
				local cf, h = q.CFrame, q.Size / 2
				local r, u, l = cf.RightVector, cf.UpVector, cf.LookVector
				local e = Vector3.new(math.abs(r.X) * h.X + math.abs(u.X) * h.Y + math.abs(l.X) * h.Z, math.abs(r.Y) * h.X + math.abs(u.Y) * h.Y + math.abs(l.Y) * h.Z, math.abs(r.Z) * h.X + math.abs(u.Z) * h.Y + math.abs(l.Z) * h.Z)
				table.insert(blockers, { p = q, lo = cf.Position - e, hi = cf.Position + e, round = q:IsA("Part") and q.Shape == Enum.PartType.Cylinder })
			end
		end
	end
	local function hidden(a, b, target, fam)
		local dv = b - a
		local len = dv.Magnitude
		local lo, hi = a:Min(b), a:Max(b)
		fam = fam or (if target.Parent:IsA("Model") then target.Parent else nil)
		for _, k in blockers do
			if k.p ~= target and not (fam and k.p:IsDescendantOf(fam)) and not (k.hi.X < lo.X or k.lo.X > hi.X or k.hi.Y < lo.Y or k.lo.Y > hi.Y or k.hi.Z < lo.Z or k.lo.Z > hi.Z) then
				local cf, h = k.p.CFrame, k.p.Size / 2
				for t = 1, len - 1, 0.25 do -- (not the first stud or the last)
					local q = cf:PointToObjectSpace(a + dv * (t / len))
					if math.abs(q.X) < h.X and math.abs(q.Y) < h.Y and math.abs(q.Z) < h.Z and (not k.round or q.Y * q.Y + q.Z * q.Z < h.Y * h.Y) then return k.p end
				end
			end
		end
		return nil
	end
	local targets = {}
	for _, pad in pads do
		if pad:GetAttribute("Bank") == "hall" then continue end -- (the duel hall's pads are not seen from the spawn)
		for _, c in pad:GetChildren() do
			if c:IsA("BasePart") and c.Name:sub(1, 4) == "Side" then table.insert(targets, { "pad " .. pad.Name .. "'s " .. c.Name, c, c.Position, pad }) end
		end
		local sign = pad:FindFirstChild("Sign")
		if sign then for _, k in { -0.3, 0, 0.3 } do table.insert(targets, { "the board of " .. pad.Name, sign, sign.Position + sign.CFrame.RightVector * (sign.Size.X * k), pad }) end end
	end
	local inside = {} -- (looked for from the middle of the platform only: a room is not seen into from every spawn point)
	for _, w in R.SIGHTS do
		local q, fam = room.Scenery:FindFirstChild(w[2]), nil
		if q and q:IsA("Model") then fam = q; q = q.PrimaryPart or q:FindFirstChildWhichIsA("BasePart", true) end
		if q then table.insert(if w[3] then inside else targets, { w[1], q, if fam then fam:GetBoundingBox().Position else q.Position, fam }) else table.insert(issues, "SIGHT: nothing called " .. w[2] .. " to look for") end
	end
	local sights, lines, shut, spawnN = {}, 0, 0, 0
	for _, t in inside do
		lines += 1
		local by = hidden(O + Vector3.new(0, 5.9, 0), t[3], t[2], t[4])
		if by then shut += 1; table.insert(sights, ("SIGHT: %s hides %s from the middle of the platform"):format(by.Name, t[1])) end
	end
	for _, s in W.spawns:GetChildren() do
		if W.live and s:GetAttribute("Built") ~= R.MARK then continue end
		spawnN += 1
		local eye = s.Position + Vector3.new(0, 4.7, 0)
		for _, t in targets do
			lines += 1
			local by = hidden(eye, t[3], t[2], t[4])
			if by then
				shut += 1
				local line = ("SIGHT: %s hides %s from the spawn point at (%.1f, %.1f)"):format(by.Name, t[1], s.Position.X - O.X, s.Position.Z - O.Z)
				if not seen[line] then seen[line] = true; table.insert(sights, line) end
			end
		end
	end
	local rp = RaycastParams.new(); rp.FilterType = Enum.RaycastFilterType.Include; rp.FilterDescendantsInstances = { room.Shell }
	local leaks = 0
	for _, from in R.LEAKS do
		local at = R.frame(O, from[1], 0, from[5]) * Vector3.new(from[2], from[3], -from[4])
		for x = -1, 1 do for y = -1, 1 do for z = -1, 1 do
			if not (x == 0 and y == 0 and z == 0) and not workspace:Raycast(at, Vector3.new(x, y, z).Unit * 500, rp) then
				leaks += 1; table.insert(issues, ("LEAK from bearing %.0f, x %.0f, y %.0f, d %.0f toward (%d, %d, %d)"):format(from[1], from[2], from[3], from[4], x, y, z))
			end
		end end end
	end
	local shadows, lamps = 0, 0
	for _, l in room:GetDescendants() do if l:IsA("Light") then lamps += 1; if l.Shadows then shadows += 1 end end end
	if shadows > 11 then table.insert(issues, ("LAMPS: %d cast shadows (11 is the limit)"):format(shadows)) end
	if spawnN < 8 then table.insert(issues, ("SPAWNS: %d spawn markers (8 wanted)"):format(spawnN)) end
	if #pads ~= #R.MODES + #R.HALL then table.insert(issues, ("PADS: %d pads (%d wanted)"):format(#pads, #R.MODES + #R.HALL)) end
	local problems = #issues
	for _, line in sights do table.insert(issues, line) end
	local msg = ("%s (%s): %d keep-clear zones, %d parts looked at, %d problems, leaks %d, sight lines %d, hidden %d, props %d, overlaps %d, lamps %d (%d with shadows), pads %d"):format(
		R.ROOM, if W.live then "live" else "staging copy", #zones, looked, problems + #sights, leaks, lines, shut, #props, overlaps, lamps, shadows, #pads)
	if W.live then PB:SetAttribute("LastOverlapCheck", msg) end
	if #issues > 40 then local n = #issues; issues = table.move(issues, 1, 40, 1, {}); table.insert(issues, ("... and %d more"):format(n - 40)) end
	return msg .. (if #issues > 0 then "\n" .. table.concat(issues, "\n") else "")
end

-- camera spots for pictures: name = { eye, looking at }, each { bearing, x, y, d }. R.view(name) gives world points
R.VIEWS = {
	spawn = { { 0, 0, 5.9, -6 }, { 0, 0, 7, 50 } }, centre = { { 180, 0, 8, 23 }, { 0, 0, 11, 20 } }, dome = { { 180, 0, 3.5, 15 }, { 0, 0, 30, 3 } },
	balcony = { { 180, 0, 19.2, 25 }, { 0, 0, 9, 32 } }, lifts = { { 334.3, 0, 5.2, 34.5 }, { 22, 0, 8, 52 } }, lift = { { 0, 0, 6, 33 }, { 0, 0, 9, 56 } },
	back = { { 0, 0, 5.5, 41 }, { 180, 0, 9, 30 } }, lounge_door = { { 0, 0, 5.9, 3 }, { 180, 0, 5, 46 } }, lounge = { { 180, 6.5, 5.6, 39.5 }, { 180, -3, 4.2, 52 } },
	duels_door = { { DUELS + 180, 0, 5.9, 4 }, { DUELS, 0, 7, 76 } }, duels = { { DUELS, 0, 8.5, 41 }, { DUELS, 0, 5, 80 } },
	duels_back = { { DUELS, 12, 9, 86 }, { DUELS, -6, 3.5, 50 } },
	training_door = { { ARM + 180, 0, 5.9, 4 }, { ARM, 0, 5.5, 60 } }, armory = { { ARM, 8.5, 6, 39.5 }, { ARM, -7, 5.5, 58 } },
	holo = { { 180, 0, 5.4, 15 }, { 0, 0, 12.6, 0 } }, showroom = { { 0, 0, 6.2, 7 }, { 180, 0, 4.6, 27 } },
	plinth = { { 6 * STEP, -5, 5.6, 15.5 }, { 6 * STEP, 0, 4.8, 25 } },
}
-- every view as "name x y z x y z" lines, for the screen capture tool
function R.views()
	local out = {}
	for name in R.VIEWS do
		local a, b = R.view(name)
		if a then table.insert(out, ("%s %.1f %.1f %.1f %.1f %.1f %.1f"):format(name, a.X, a.Y, a.Z, b.X, b.Y, b.Z)) end
	end
	table.sort(out)
	return table.concat(out, "\n")
end
function R.view(name)
	local W = R.places()
	local v = R.VIEWS[name]
	if not W or not v then return nil end
	local a = R.frame(W.O, v[1][1]) * Vector3.new(v[1][2], v[1][3], -v[1][4])
	local b = R.frame(W.O, v[2][1]) * Vector3.new(v[2][2], v[2][3], -v[2][4])
	return a, b
end

return R
