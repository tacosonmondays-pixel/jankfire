--!nonstrict
-- THE CYLINDER (hub-originals, 20 Nov 2026; the owner: "one more thats completely new and unique with our design not
-- based on current infrastructure"). A revolver's cylinder the size of a building lying in its frame; its chambers are
-- the rooms. You spawn at the south end of the pad hall (the frame's side plates hold ten pads in bays) facing the
-- cylinder's face, which rises in the tall transept at the hall's end: six round mouths at three heights round the
-- pin's boss. Low chambers: the LOUNGE (west: shop, bar, tables, arcade, code panel) and the ARMORY (east: the training
-- gate at its back); side chambers (jump pads up to their balconies): SPECTATE (west) and the ranked boards (east);
-- upper chambers: ZOMBIES (east, a jump pad from the east balcony) and the LOADED chamber (west: a giant round, its
-- primer toward you). The gym is behind the frame's front, through the portal behind the spawn; the VIP room and the
-- golf room open off the transept. Plan: vault Hubs/The Cylinder plan.md.
-- The look is a chunky Blender kit modelled in the site's own frame (tools/roblox/cylinder_models.py, one upload:
-- HC.KIT; HC.import() puts it in ServerStorage.JankfireMeshes.HubCylinderKit); its collisions are unseen boxes from the
-- same numbers (HubCylinderData, tools/roblox/hub_data.py); walls, floors and the roof are textured Parts here; the
-- hub's functions are HubKit's features.
local HC = {}
HC.ID, HC.FOLDER, HC.TITLE, HC.ORDER = "cylinder", "Cylinder", "THE CYLINDER", 6
HC.SITE = CFrame.new(-1800, 240, -14200)
HC.KIT = 105308309547631 -- hub_cylinder_kit_9 (board surrounds clear of the 13 x 6.5 board frames; kit 8 was 113574524501076)
-- (kit 8: (the owner's 26 Nov pass: the pin brought down over a round dais, framed bays and board surrounds clear of the boards, panels on the upper walls; kit 7 was 85328731311453, kit 6 117516859260764)
HC.LIB = "HubCylinderKit"
local SS = game:GetService("ServerStorage")
local MAT = Enum.Material
-- the breech (kit 5, the same numbers as cylinder_models.py): the octagon's middle (z), inradius, wall top, lid; its bay
-- sides by plan angle (+x toward +z, 270 = north): 1V1..5V5, then the loadout bay; a bay's width, floor, inside height
local OC_Z, OC_R, OC_H, OC_CEIL = 77, 37.4, 26, 28
-- (kit 6, the owner's classic pads: one pad per bay, its board on the bay's back wall) ten bays: the lifts bank west from the
-- spawn round to the face (1V1..4V4), the east twins mirrored
local OC_BAYS = { 120, 150, 180, 210, 240, 60, 30, 0, 330, 300 }
local OB_W, OB_D, OB_FLOOR, OB_IN, OB_MOUTH = 17, 15, 0.8, 18.5, 16
local WARM = { cy_pilaster = "dcd6ca", cy_baylintel = "dcd6ca", cy_beam = "d2ccc0", cy_bayframe = "dcd6ca", cy_wallpanel = "dcd6ca", cy_pinband = "dcd6ca", cy_middais = "d2ccc0" }
local WALL, WALL2, FLOORC, STEELC = "a7a9ab", "b4b6b8", "8a8c8e", "8d9196" -- (walls a step darker than the piers and beams)

-- ------------------------------------------------------------------------------------------------ the kit
local KIND = { slate = MAT.Slate, concrete = MAT.Concrete, plastic = MAT.SmoothPlastic, neon = MAT.Neon, glass = MAT.Glass }
local PAINT = { ["8d9196"] = true, ["7a7e84"] = true, ["9ea2a7"] = true, ["9a8f80"] = true }
local PLASTER = { c4c5c2 = true, b4b6b8 = true }
local function dress(p: BasePart, kind: string?)
	if p.Material == MAT.Neon or p.Material == MAT.Glass or p.Transparency >= 0.99 then return end
	local h = string.lower(p.Color:ToHex())
	if kind == "slate" or p.Material == MAT.Slate then p.Material = MAT.Slate; p.MaterialVariant = "TrSlate"
	elseif kind == "concrete" or p.Material == MAT.Concrete then p.Material = MAT.Concrete; p.MaterialVariant = "TrConcrete"
	elseif PAINT[h] then p.Material = MAT.Plastic; p.MaterialVariant = "TrPaint"
	elseif PLASTER[h] then p.Material = MAT.Plastic; p.MaterialVariant = "TrPlaster" end
end
function HC.import(id: number?): string
	local kit = id or HC.KIT
	local ok, c = pcall(function() return game:GetService("InsertService"):LoadAsset(kit) end)
	if not ok or not c then return "LOAD FAILED " .. tostring(c) end
	local lib = SS:FindFirstChild("JankfireMeshes") or Instance.new("Folder", SS)
	lib.Name = "JankfireMeshes"
	local old = lib:FindFirstChild(HC.LIB); if old then old:Destroy() end
	local f = Instance.new("Folder"); f.Name = HC.LIB; f:SetAttribute("AssetId", kit)
	local groups, n = {}, 0
	for _, d in c:GetDescendants() do
		if not d:IsA("MeshPart") then continue end
		local model, kind, h = string.match(d.Name, "^(.-)%d+__(%a+)_(%x%x%x%x%x%x)")
		if not model or not KIND[kind] then continue end
		d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
		d.Color = Color3.fromHex(h); d.TextureID = ""; d.Material = KIND[kind]
		d.CastShadow = kind ~= "neon" and kind ~= "glass"
		dress(d, kind)
		groups[model] = groups[model] or {}
		table.insert(groups[model], d)
		n += 1
	end
	local names = {}
	for name, parts in groups do
		local m = Instance.new("Model"); m.Name = name
		for _, p in parts do p.Parent = m end
		m.WorldPivot = CFrame.identity; m.Parent = f
		table.insert(names, name .. " " .. #parts)
	end
	c:Destroy(); f.Parent = lib
	table.sort(names)
	return ("%d pieces in %d models: %s"):format(n, #names, table.concat(names, ", "))
end

-- ------------------------------------------------------------------------------------------------ the build
function HC.build(K, parent, name, site, live)
	local P = K.P
	local F0 = CFrame.new()
	local DR = require((SS:WaitForChild("PolishBackup"):WaitForChild("HubDress") :: ModuleScript):Clone())
	site = site or HC.SITE
	local f = K.begin(parent, name or HC.FOLDER, site, HC.ID, { Title = HC.TITLE, Order = HC.ORDER }, live)
	local box = K.box
	local function sbox(...) local p = box(F0, "Shell", ...); dress(p); return p end
	-- the kit, pivoted to the site; then the unseen collision boxes
	local lib = SS:FindFirstChild("JankfireMeshes") and SS.JankfireMeshes:FindFirstChild(HC.LIB)
	local kit = Instance.new("Folder"); kit.Name = "Kit"; kit.Parent = f
	if lib then
		for _, m in lib:GetChildren() do
			if m.Name == "cy_lintel" or m.Name == "cy_rifling" then continue end -- (the lintel is built below; the rifling read as diagonal struts)
			if m.Name == "cy_case" or m.Name == "cy_bullet" or m.Name == "cy_primer" or m.Name == "cy_primerring" then continue end -- (judges: a gun pun; one lit emblem instead)
			local c = m:Clone(); c:PivotTo(site)
			local warm = WARM[m.Name] -- (judge round 9: the breech one flat blue-grey: its structure a warm off-white, paler than the walls)
			if warm then for _, p in c:GetDescendants() do if p:IsA("BasePart") then p.Color = Color3.fromHex(warm) end end end
			for _, p in c:GetDescendants() do if p:IsA("BasePart") then p:SetAttribute("Hub", HC.ID); K.S.count += 1 end end
			c.Parent = kit
		end
	else
		f:SetAttribute("KitMissing", true)
	end
	local data = require((SS:WaitForChild("PolishBackup"):WaitForChild("HubCylinderData") :: ModuleScript):Clone())
	for _, b in data.coll do
		local p = Instance.new("Part")
		p.Name = "Col" .. b[1]; p.Anchored = true; p.CanCollide = true; p.CanQuery = true; p.CanTouch = false
		p.CastShadow = false; p.Transparency = 1
		p.Size = Vector3.new(b[5], b[6], b[7])
		p.CFrame = site * CFrame.new(b[2], b[3], b[4]) * CFrame.Angles(0, math.rad(b[8]), 0) * CFrame.Angles(math.rad(b[9]), 0, 0) * CFrame.Angles(0, 0, math.rad(b[10]))
		p:SetAttribute("Hub", HC.ID); p.Parent = f.Shell
		K.S.count += 1
	end

	-- ============================================================== THE HALL (spawn, pads) and THE TRANSEPT
	sbox("Floor", -48, 48, -1, 0, -0.5, 24, FLOORC, MAT.Concrete)
	-- (judge round 8: any straight hall of pads reads as the RIVALS pad corridor) THE BREECH: a twelve-sided steel room
	-- between the spawn and the face, its north side open on the transept and the cylinder's face, its south side the gym's
	-- portal; the other ten sides deep bays, one classic pad in each (the lifts bank west, 1V1 by the spawn round to 4V4 by
	-- the face; the east twins mirrored), its count board on the bay's back wall, the mode set into each bay's lintel, a warm
	-- panel over each pad; the pin's boss hanging from the lid lit underneath; cream spokes from the middle's inlay
	for k = 1, 10 do
		local a = math.rad(OC_BAYS[k])
		local ux, uz = math.cos(a), math.sin(a)
		local Fb = CFrame.lookAt(Vector3.new(0, 0, OC_Z), Vector3.new(ux, 0, OC_Z + uz)) -- (its -Z out along the bay, +X right)
		local md = K.MODES[(k - 1) % 5 + 1]
		local east = k > 5
		local r0 = OC_R + 1.0
		local back = OC_R + OB_D - 0.5
		local F = K.facing(ux * r0, OC_Z + uz * r0, ux, uz, OB_FLOOR)
		local boardAt = K.facing(ux * back, OC_Z + uz * back, -ux, -uz, OB_FLOOR + 6.2 + 2.75) -- (flat on the back wall: the owner, "changed my mind no angeld")
		if K.padClassic then
			K.pad(F, md, if east then "east" else "lifts", if east then md.id .. "_e" else md.id, { boardAt = boardAt, boardTitle = false }) -- (one name per pad: the bay's lintel sign names it)
		else
			K.pad(F, md, if east then "east" else "lifts", if east then md.id .. "_e" else md.id, { lampY = 13 })
		end
		K.panel(Fb, 0, OB_IN, -(OC_R + 6.5), 6, 6, { bright = 0.55, range = 20, lightHex = "fff1df" })
		local spot = box(Fb, "Scenery", "PadSpot", -0.5, 0.5, OB_IN - 0.6, OB_IN - 0.5, -(OC_R + 6.5) - 0.5, -(OC_R + 6.5) + 0.5, P.pale, nil, { ghost = true, tr = 1 })
		K.light(spot, 20, 1.8, "fff4e6", { kind = "SpotLight", face = Enum.NormalId.Bottom, angle = 100 }) -- (26 Nov, the fair judges: the pads the brightest things)
		local wash = box(F0, "Scenery", "WallWash", -0.5, 0.5, 25.9, 26.1, -0.5, 0.5, P.pale, nil, { ghost = true, tr = 1 }) -- (the framed panel over the bay washed)
		wash.CFrame = site * CFrame.lookAt(Vector3.new(ux * 22, 26, OC_Z + uz * 22), Vector3.new(ux * 37, 22.8, OC_Z + uz * 37))
		K.light(wash, 24, 0.7, "fff1df", { kind = "SpotLight", face = Enum.NormalId.Front, angle = 50 })
		local sx, sz = ux * (OC_R - 1.42), OC_Z + uz * (OC_R - 1.42)
		K.sign(K.facing(sx, sz, -ux, -uz, OB_MOUTH + 1.7), "Scenery", "BaySign", 13.5, 2.4, 0, 0, 0,
			{ { md.title .. "  ·  " .. md.kind, "f2f0ea", 0.8 } }, { pps = 40, plate = "4a4f57", thick = 0.15, bright = 1.2 })
		local A, B = Vector3.new(ux * 12.6, 0.02, OC_Z + uz * 12.6), Vector3.new(ux * (OC_R - 1.5), 0.02, OC_Z + uz * (OC_R - 1.5))
		local sp = box(F0, "Scenery", "FloorLine", -0.6, 0.6, 0, 0.05, -0.5, 0.5, "dcd6ca", MAT.Plastic)
		sp.MaterialVariant = "TrPaint"; sp.Size = Vector3.new(1.2, 0.05, (B - A).Magnitude); sp.CFrame = site * CFrame.lookAt((A + B) / 2, B)
	end
	-- your loadout and the bundles back in the transept either side of the face (no free side in the breech now)
	K.holoLoadout(K.at(F0, -30, 18, -60))
	K.bundles(K.at(F0, 30, 18, 60))
	for _, zz in { { OC_Z + 12.6, OC_Z + OC_R - 1 }, { OC_Z - OC_R - 12, OC_Z - 12.6 } } do -- (the spawn's line in, the line on to the face)
		box(F0, "Scenery", "FloorLine", -0.6, 0.6, 0, 0.05, zz[1], zz[2], "d6d5d0", MAT.Plastic).MaterialVariant = "TrPaint"
	end
	-- the boss: a lit ring under its stepped end, a downlight; panels in the lid's coffers round it, a warm wash on the walls
	-- (a thin lit ring round the pin's end, not a glowing disc: a steel cover over its middle)
	-- (kit 7, the owner's 26 Nov pass: no lit ring; the pin comes down to 14 up, a recessed downlight in its end)
	local dl = K.cyl(F0, "Scenery", "PinLight", 0, 14.08, 14.2, OC_Z, 4.4, "a9adb4", MAT.Neon, { ghost = true, noshadow = true }) -- (a dull lens: it blew out white from below)
	K.light(dl, 30, 1.0, "f2f4f8", { kind = "SpotLight", face = Enum.NormalId.Bottom, angle = 90 })
	for i = 0, 5 do -- (between the twelve radial beams)
		local q = math.rad(i * 60)
		K.panel(CFrame.new(math.cos(q) * 15.5, 0, OC_Z + math.sin(q) * 15.5) * CFrame.Angles(0, -q, 0), 0, OC_CEIL, 0, 4, 6, { bright = 0.22, range = 30, hex = "b7bbc2" })
	end
	-- the middle (judge round 9: an empty octagon): a pale round bench under the pin's boss, a squat column in it with a
	-- thin lit band below its cap, all in the structure's warm off-white (kept under the sightline to the face's boss)
	-- (kit 7, the fair judges: the squat column hid the bays and its band lit nothing) the kit's smooth two-step dais under
	-- the lowered pin; unseen cylinders give it its collision
	for _, st in { { 0, 0.7, 20 }, { 0.7, 1.4, 14.4 } } do
		local c = K.cyl(F0, "Shell", "MidDais", 0, st[1], st[2], OC_Z, st[3], "d2ccc0", MAT.Plastic)
		c.Transparency = 1; c.CastShadow = false
	end
	-- the gym's portal through the south side, its name over it toward the middle
	K.sign(K.facing(0, OC_Z + OC_R - 0.05, 0, -1), "Scenery", "WaySign", 8, 2, 0, 16.4, 0, { { "GYM", P.pale, 0.72 } }, { pps = 46 })
	-- the transept's light: panels under the strap, three lamps on the face
	for _, x in { -24, 0, 24 } do K.panel(F0, x, 64, 12, 10, 10, { range = 70, bright = 0.5, hex = "c9ccd2" }) end
	for _, x in { -20, 20 } do
		local lamp = box(F0, "Scenery", "FaceLamp", x - 1, x + 1, 63, 64, 20, 22, "b4b6b8", nil, { ghost = true })
		K.light(lamp, 80, 1.4, "f2f4f8", { kind = "SpotLight", face = Enum.NormalId.Front, angle = 60 })
		lamp.CFrame = site * CFrame.lookAt(Vector3.new(x, 63.5, 21), Vector3.new(x * 0.4, 30, 0))
	end
	-- signs over the low chambers' mouths and the side chambers' (on the face, just proud of it)
	local function faceSign(x, y, w, text) K.sign(K.facing(x, 1.0, 0, 1), "Scenery", "WaySign", w, 2.4, 0, y, 0, { { text, "3f444c", 0.74 } }, { pps = 46, plate = "c4c5c2", thick = 1.0, bright = 1 }) end -- (set into the face: its own grey, dark letters)
	faceSign(-13, 17.05, 18, "LOUNGE  ·  SHOP"); faceSign(13, 17.05, 18, "ARMORY  ·  TRAINING") -- (each 2.2 over its mouth's top, at least half its width)
	faceSign(-26, 38.7, 13, "SPECTATE"); faceSign(26, 38.7, 13, "RANKED"); faceSign(13, 60.35, 13, "ZOMBIES")

	-- the spawn at the hall's south end, facing the face; the arrival, the HUBS terminal
	for i = 0, 7 do K.marker(F0, "HubSpawns", "Spawn", -4.2 + (i % 4) * 2.8, 0.1, 102 + math.floor(i / 4) * 3, 0) end
	K.marker(F0, "HubArrive", "Arrive", 0, 0.1, 96, 0)
	K.travelTerminal(K.at(F0, -12, 108, -60))
	-- the transept: your loadout and the bundles either side; jump pads that throw you straight into the side chambers'
	-- mouths (spectate west, ranked east) and one into the zombies chamber (upper east)
	for _, sd in { -1, 1 } do K.jumpPad(K.facing(sd * 36, 6, -sd * 10, -12), Vector3.new(0, 66, 11.6)) end
	K.jumpPad(K.facing(18, 16, -5, -22), Vector3.new(0, 86, 15)) -- (up into the zombies chamber)
	-- the name over the hall's mouth, read from the spawn: a chunky header beam across it (judge: the name 3x bigger)
	-- the JANKFIRE name on the pin's boss, facing the hall
	K.sign(K.facing(0, 2.75, 0, 1), "Scenery", "NameSign", 10.4, 2.6, 0, 25, 0, { { "JANKFIRE", "3f444c", 0.8 } }, { pps = 40, plate = "9ea2a7", bright = 1 }) -- (dark letters in the boss's own grey)

	-- ============================================================== THE CHAMBERS
	-- the lounge (lower west): the shop by the way in, the chess table on a low round plinth, the seats on a raised round
	-- dais in the middle third, the arm-wrestling table, the bar against the far cap under a warm backlit band, chunky drum
	-- lamps under the ribs, the code panel on the east wall
	local FL = CFrame.new(-13, -4, 0)
	local function disc(nm, z, dia, h, hex)
		local p = K.cyl(FL, "Shell", nm, 0, -0.02, h, z, dia, hex, MAT.Plastic); p.MaterialVariant = "TrPlaster"
	end
	local beforeS = DR.snap(f)
	K.shop(K.at(FL, -3.6, -15, -90), 10) -- (in from the curved wall: its shelves cut the ribs)
	DR.shop(K, f, beforeS, K.at(FL, -3.6, -15, -90), 10)
	disc("TablePlinth", -26, 10.6, 0.4, "a39d92"); K.tableSpot(K.at(FL, 0, -26, 0, 0.4), "board")
	local beforeC = DR.snap(f) -- (the seats in the kit's sunken pit, two steps down: its floor at FL y -1.2)
	K.cluster(K.at(FL, 0.5, -43, 180, -1.2), { npcSofa = true, hex = "8a7a6a" })
	for _, d in f:GetDescendants() do if not beforeC[d] and d.Name == "Rug" then d:Destroy() end end
	disc("TablePlinth", -58, 10.6, 0.4, "a39d92"); K.tableSpot(K.at(FL, 0, -58, 0, 0.4), "arm")
	K.arcadeSpot(K.at(FL, -8.6, -66, -90))
	K.bar(K.at(FL, 0, -70.5, 180), 12)
	K.light(box(FL, "Scenery", "BarGlow", -7, 7, 8.4, 12.2, -75.95, -75.7, "b8a488", MAT.Neon, { ghost = true, noshadow = true, tr = 0.5 }), 24, 0.4, P.warm)
	for _, e in { { -7.6, -7 }, { 7, 7.6 } } do box(FL, "Scenery", "BarGlowHousing", e[1], e[2], 7.8, 12.8, -76, -75.4, "c4c5c2", MAT.Plastic).MaterialVariant = "TrPaint" end
	box(FL, "Scenery", "BarGlowHousing", -7.6, 7.6, 12.2, 12.8, -76, -75.4, "c4c5c2", MAT.Plastic).MaterialVariant = "TrPaint"
	box(FL, "Scenery", "BarGlowHousing", -7.6, 7.6, 7.8, 8.4, -76, -75.4, "c4c5c2", MAT.Plastic).MaterialVariant = "TrPaint"
	K.codePanelSpot(K.at(FL, 8.6, -12, 90))
	for _, z in { -26, -43, -68 } do
		K.cyl(FL, "Scenery", "DrumLamp", 0, 14.6, 16.2, z, 3.4, "b4b6b8", MAT.Plastic, { ghost = true }).MaterialVariant = "TrPlaster"
		K.light(K.cyl(FL, "Scenery", "DrumGlow", 0, 14.45, 14.6, z, 2.8, P.warm, MAT.Neon, { ghost = true, noshadow = true }), 22, 0.85, P.warm)
	end
	-- the armory (lower east): HubKit's armory hall inside the rifled bore, its lid left off so the rifling shows
	local FA = CFrame.new(13, -4, 0)
	local before = {}
	for _, d in f:GetDescendants() do before[d] = true end
	K.armory(FA, { d0 = 7, d1 = 74, w = 8.5, h = 11, open = 8, door = "CylinderToTraining" })
	for _, d in f:GetDescendants() do
		if not before[d] and d:IsA("BasePart") then
			if d.Name == "ArmoryLid" or d.Name == "CeilingBeam" or d.Name == "PanelHousing" or d.Name == "LightPanel" or d.Name == "ArmoryRunner" then d:Destroy()
			elseif d.Name == "CaseFoot" or d.Name == "CaseLid" or d.Name == "CaseBase" or d.Name == "CaseTop" then d.Color = Color3.fromHex("7a7e84"); d.Material = MAT.Plastic; d.MaterialVariant = "TrPaint"
			elseif d.Name == "ArmoryWall" or d.Name == "RackBoard" then d.Color = Color3.fromHex("d8d2c6"); d.Material = MAT.Plastic; d.MaterialVariant = "TrPlaster" end -- (a warm off-white: it read sterile)
		end
	end
	DR.armory(K, f, before, FA, { w = 8.5, d0 = 7, d1 = 74, h = 11, pitch = 11.5, gunLen = 7, backHex = "5b6068" })
	for _, z in { -15, -32, -49, -66 } do -- (26 Nov, the fair judges: the vault near-black: warm fills along it)
		K.light(box(FA, "Scenery", "VaultFill", -0.3, 0.3, 9.6, 9.8, z - 0.3, z + 0.3, P.pale, nil, { ghost = true, tr = 1 }), 18, 0.8, "fff1df")
	end
	for _, z in { -20, -44, -66 } do -- (the three tubes in chunky housings, at ~60%)
		box(FA, "Scenery", "VaultGlowHousing", -1.2, 1.2, 16.75, 17.8, z - 4.6, z + 4.6, "9ea2a7", MAT.Plastic, { ghost = true }).MaterialVariant = "TrPaint"
		K.light(box(FA, "Scenery", "VaultGlow", -0.7, 0.7, 16.6, 16.75, z - 4, z + 4, "f2f4f8", MAT.Neon, { ghost = true, noshadow = true }), 22, 0.42, "f2f4f8")
	end
	-- (the armory's bundle hologram stood in its narrow aisle: the transept shows the bundles)
	for _, d in f:GetDescendants() do
		if not before[d] and (d:IsA("BasePart") or d:IsA("Model")) then
			local ok, pos = pcall(function() return if d:IsA("Model") then d:GetPivot().Position else (d :: BasePart).Position end)
			if ok and (d.Name == "Plinth" or d:HasTag("HubHolo") or string.find(d.Name, "^ShowName")) then
				local lp = site:PointToObjectSpace(pos)
				if lp.X > 2 and lp.X < 25 and lp.Z < -5 and lp.Y < 14 then d:Destroy() end
			end
		end
	end
	-- (judge round 9: no screw heads: the breech replaced the hall whose walls held them)
	-- spectate (side west): the big board just inside the mouth, facing out over the transept (watch from below or the ledge)
	local FS = CFrame.new(-26, 18.5, 0)
	K.spectateSpot(K.at(FS, 0, -14, 180, 6.4), 16, 9)
	-- the ranked boards (side east), just inside its mouth, facing out
	local FR = CFrame.new(26, 18.5, 0)
	K.boardSpot(K.at(FR, -4.4, -14, 180, 5.6), "duels", 8, 6)
	K.boardSpot(K.at(FR, 4.4, -14, 180, 5.6), "party", 8, 6)
	for _, Fc in { FS, FR } do -- (the side chambers' own light, under their crowns)
		for _, z in { -8, -20, -46, -68 } do K.light(box(Fc, "Scenery", "VaultLamp", -0.5, 0.5, 16.4, 16.6, z - 0.5, z + 0.5, P.pale, nil, { ghost = true, tr = 1 }), 26, 1.1, "fff1df") end -- (lit, warm: they read as dark holes)
	end
	-- zombies (upper east): HubKit's wrecked room inside the bore, its guide at the mouth
	local beforeZ = DR.snap(f)
	K.zombieRoom(CFrame.new(13, 41, -6), { x0 = -7.5, x1 = 7.5, t = 1, d = 30, h = 9.5, door = 9, guideSide = 1 })
	for _, d in f:GetDescendants() do if not beforeZ[d] and (d.Name == "ZmSign" or d.Name == "ZmSignNail") then d:Destroy() end end
	-- the upper west mouth: one lit emblem (a pale stone disc, backlit by a warm halo) where the cartridge was
	local Fe = CFrame.new(-12.5, 46.65, -5) * CFrame.Angles(math.pi / 2, 0, 0) -- (its y = toward the hall)
	K.cyl(Fe, "Scenery", "EmblemDisc", 0, -1.5, 0, 0, 17, "d6d5d0", MAT.Plastic).MaterialVariant = "TrPaint"
	K.cyl(Fe, "Scenery", "EmblemBoss", 0, 0, 0.5, 0, 9, "c4c5c2", MAT.Plastic).MaterialVariant = "TrPaint"
	-- (the owner, 26 Nov: no useless indicator lights: the halo a pale stone ring, a warm lamp behind the disc washing it)
	K.cyl(Fe, "Scenery", "EmblemHalo", 0, -1.9, -1.6, 0, 19.4, "c4c5c2", MAT.Plastic, { ghost = true }).MaterialVariant = "TrPaint"
	K.light(K.box(Fe, "Scenery", "EmblemLamp", -0.5, 0.5, -2.4, -2.2, -0.5, 0.5, P.pale, nil, { ghost = true, tr = 1 }), 18, 0.8, "ffd9a8")
	for _, x in { 6, 20 } do -- (work lights on its front, seen from the transept)
		local g = box(F0, "Scenery", "ZmWorkLight", x - 0.5, x + 0.5, 50, 50.2, -1.5, -1.3, P.pale, nil, { ghost = true, tr = 1 })
		g.CFrame = site * CFrame.lookAt(Vector3.new(x, 50, -1.4), Vector3.new(13, 44, -7))
		K.light(g, 18, 0.9, "ffe2bf", { kind = "SpotLight", face = Enum.NormalId.Front, angle = 70 })
	end

	-- ============================================================== OFF THE TRANSEPT: VIP (east), GOLF (west)
	K.vip(K.facing(42, 12, 1, 0), { w = 10, d = 22, h = 11, front = 14, frontH = 13 })
	K.golfRoom(CFrame.new(), { x0 = -95, x1 = -51, z0 = -36, z1 = 44, h = 18, door = { -51, 6, 16 } })
	-- (hub-minigames, 20 Nov: K.golfRoom centres the course for a 100-long room; this one is 80, so the marker sat 10 off
	-- and the far row of holes ran through the wall) the golf marker at the room's middle, its look kept
	for _, d in f:GetDescendants() do
		if d:IsA("BasePart") and d:GetAttribute("Game") == "golf" then
			local p = site:PointToObjectSpace(d.Position)
			d.CFrame = CFrame.new(site * Vector3.new((-95 - 51) / 2, p.Y, (-36 + 44) / 2)) * d.CFrame.Rotation
			d:SetAttribute("Door", Vector3.new(-23, 0, -7)) -- (hub-minigames: the doorway's floor centre in the marker's space; the prompt stands by it)
		end
	end
	sbox("Floor", -49, -48, -1, 0, 6, 16, FLOORC, MAT.Concrete)

	-- ============================================================== THE GYM (behind the frame's front)
	local FG = CFrame.Angles(0, -math.pi / 2, 0) -- (its x runs south, its z runs west)
	local beforeG = DR.snap(f)
	K.gym(FG, { x0 = 132, x1 = 196, z0 = -32, z1 = 32, h = 16, open = { 132, -9, 9 }, rings = { { 148, -14 }, { 180, -14 }, { 148, 14 }, { 180, 14 } },
		locker = { x0 = 160, x1 = 196, z0 = 34, z1 = 58, door = { 182, 188 } } })
	do -- (26 Nov, the owner's pass + the Still's judge rounds 6-14: the thin lamp rods and stems gone, the near-blacks lifted,
		-- eight bags not twenty, beams across the lid with housed panels between them, warm fills under it)
		local FGw = site * FG
		local GONE = { Girder = true, PanelHousing = true, LightPanel = true, LampBeam = true, LampShade = true, Lamp = true, RodToBeam = true,
			SpeedBag = true, SpeedBagBoard = true, SpeedBagBracket = true, SpeedBagSwivel = true, Kettlebell = true, KbShelf = true, KbLeg = true,
			MedBall = true, BallShelf = true, BallLeg = true, GymPad = true, GymPadCap = true, Mirror = true, MirrorFrame = true, TimerRim = true, TimerFace = true }
		for _, d in f:GetDescendants() do
			if beforeG[d] or not d:IsA("BasePart") or d.Parent == nil then continue end
			local lp = FGw:PointToObjectSpace(d.Position)
			local inGym = lp.X > 131 and lp.X < 199 and math.abs(lp.Z) < 34
			if d.Name == "GymLid" then d.Color = Color3.fromHex("aaa59c"); d.Material = MAT.Plastic; d.MaterialVariant = "TrPlaster"
			elseif inGym and (GONE[d.Name] or (string.find(d.Name, "Mirror") ~= nil)) then d:Destroy()
			elseif d.Name == "RingRope" then d.Size = Vector3.new(d.Size.X, 0.6, 0.6)
			elseif d.Name == "GymFloor" then d.Color = Color3.fromHex("918b80"); d.Material = MAT.Concrete; d.MaterialVariant = "TrConcrete"
			elseif d.Name == "RingMat" then d.Color = Color3.fromHex("8c8e90"); d.Material = MAT.Plastic; d.Reflectance = 0
			elseif d.Name == "BagRail" then d.Size = Vector3.new(d.Size.X, 1.2, 1.2); d.Color = Color3.fromHex("8a8e93")
			elseif d.Name == "BagChain" then d.Size = Vector3.new(d.Size.X, 0.5, 0.5)
			elseif inGym and string.find(d.Name, "Post") then d.Color = Color3.fromHex("8a8e93") -- (one muted colour: no candy stripes)
			elseif d.Name == "RingApron" or d.Name == "RingBase" or d.Name == "RingStep" then d.Color = Color3.fromHex("a39d92"); d.Material = MAT.Plastic; d.MaterialVariant = "TrPlaster"
			elseif d.Name == "GymWall" then d.Color = Color3.fromHex("ada79c"); d.Material = MAT.Slate; d.MaterialVariant = "TrSlate" end
		end
		local bags = {}
		for _, d in f:GetDescendants() do if d.Name == "HeavyBag" and d:IsA("BasePart") and not beforeG[d] then table.insert(bags, d) end end
		table.sort(bags, function(a, b) return (a.Position.X + a.Position.Z * 0.001) < (b.Position.X + b.Position.Z * 0.001) end)
		if #bags > 8 then
			local keep = {}
			for i = 0, 7 do keep[bags[1 + math.floor(i * (#bags - 1) / 7 + 0.5)]] = true end
			for _, b in bags do
				if not keep[b] then
					for _, d in f:GetDescendants() do
						if d.Name == "BagChain" and d:IsA("BasePart") and (Vector3.new(d.Position.X, 0, d.Position.Z) - Vector3.new(b.Position.X, 0, b.Position.Z)).Magnitude < 0.5 then d:Destroy() end
					end
					b:Destroy()
				end
			end
		end
		for _, x in { 140, 156, 172, 188 } do box(FG, "Scenery", "GymBeam", x - 1.3, x + 1.3, 14.0, 15.98, -32, 32, "e2dccf", MAT.Plastic).MaterialVariant = "TrPlaster" end
		for _, x in { 148, 164, 180 } do K.panel(FG, x, 16, 0, 5, 9, { bright = 0.45, range = 30 }) end
		for _, x in { 140, 164, 188 } do for _, z in { -18, 18 } do
			K.light(box(FG, "Scenery", "GymFill", x - 0.3, x + 0.3, 14.6, 14.8, z - 0.3, z + 0.3, P.pale, nil, { ghost = true, tr = 1 }), 22, 0.7, "fff1df")
		end end
		for _, d in f:GetDescendants() do
			if not beforeG[d] and d:IsA("BasePart") and d.Parent ~= nil then
				local c = d.Color
				if c.R + c.G + c.B < 0.62 and d.Material ~= MAT.Neon and d.Transparency < 0.95 then d.Color = Color3.fromHex("858a90") end
			end
		end
		for _, x in { 144, 164, 184 } do for _, sd in { -1, 1 } do
			local w = box(FG, "Scenery", "GymWash", x - 0.3, x + 0.3, 13.6, 13.8, sd * 20 - 0.3, sd * 20 + 0.3, P.pale, nil, { ghost = true, tr = 1 })
			w.CFrame = site * FG * CFrame.lookAt(Vector3.new(x, 13.7, sd * 20), Vector3.new(x, 6, sd * 32))
			K.light(w, 18, 0.7, "fff1df", { kind = "SpotLight", face = Enum.NormalId.Front, angle = 80 })
		end end
		for _, x in { 140, 156, 172, 188 } do for _, sd in { -1, 1 } do -- (bare long walls: a pale pilaster under each beam, the locker door kept clear)
			if sd > 0 and x > 178 and x < 192 then continue end
			box(FG, "Scenery", "GymPilaster", x - 1.3, x + 1.3, 0, 14.0, math.min(sd * 32, sd * 30.9), math.max(sd * 32, sd * 30.9), "e2dccf", MAT.Plastic).MaterialVariant = "TrPlaster"
		end end
		for _, x in { 148, 180 } do for _, z in { -14, 14 } do -- (a chunky lamp under the lid over each ring)
			box(FG, "Scenery", "RingLampHousing", x - 2.2, x + 2.2, 15.0, 15.98, z - 2.2, z + 2.2, "b9b2a5", MAT.Plastic, { ghost = true })
			local g = box(FG, "Scenery", "RingLampGlow", x - 1.8, x + 1.8, 14.85, 15.0, z - 1.8, z + 1.8, P.light, MAT.Neon, { ghost = true, noshadow = true })
			K.light(g, 26, 1.3, "fff4e6", { kind = "SpotLight", face = Enum.NormalId.Bottom, angle = 110 })
		end end
	end

	-- ============================================================== THE REGULARS
	local LOOT = { { "sit", -1.1, 0.25, -46.4, 180 }, { "sit", 2.1, 0.25, -46.4, 180 } } -- (26 Nov, Clip v2 in Play: he stood 0.4 in the shop's ledge, and behind the bar in its shelves)
	K.npc(FL, "Looticus", LOOT[1][2], LOOT[1][3], LOOT[1][4], LOOT[1][5])
	for k, w in LOOT do K.npcPoint(FL, "Looticus", k, "spot", w[1], w[2], w[3], w[4], w[5]) end
	local FR2 = { { "stop", -30 }, { "via", -26 }, { "stop", -22 } }
	K.npc(F0, "Frisk1636", FR2[1][2], 18.5, -4, 180)
	for k, w in FR2 do K.npcPoint(F0, "Frisk1636", k, w[1], "stand", w[2], 18.5, -4, 180, { pause = if w[1] == "stop" then { 8, 16 } else nil }) end
	local DU = { { "stop", 134.5, -14, -90 }, { "via", 134.5, -27.4, 180 }, { "stop", 148, -27.4, 180 }, { "via", 163, -27.4, 180 }, { "stop", 163, -14, 90 } }
	K.npc(FG, "Dune", DU[1][2], 0, DU[1][3], DU[1][4])
	for k, w in DU do K.npcPoint(FG, "Dune", k, w[1], "stand", w[2], 0, w[3], w[4], { pause = if w[1] == "stop" then { 4, 8 } else nil }) end

	for _, d in f:GetDescendants() do
		if not d:IsA("BasePart") or d:IsA("MeshPart") then continue end
		if d.Name == "LiveBoardPanel" or d.Name == "SpectatePanel" then d.Color = Color3.fromHex("3c4148") end
		if d.Name == "TableRug" then d.Color = Color3.fromHex("9c958a"); d.Material = MAT.Concrete; d.MaterialVariant = "TrConcrete" end
		if d.Name == "PlinthRing" or d.Name == "PlinthLens" then d.Transparency = 0.45 end
		if d.MaterialVariant == "" then dress(d) end
	end
	DR.tone(K, f, { leather = "8c8078" })
	for _, d in f.Kit:GetDescendants() do -- (the roof's sight strip blew out: a soft grey glow)
		if d:IsA("BasePart") and d.Parent and d.Parent.Name == "cy_sight" then d.Color = Color3.fromHex("666a70"); d.Transparency = 0.35 end
		if d:IsA("BasePart") and d.Parent and (d.Parent.Name == "cy_case" or d.Parent.Name == "cy_bullet") then d.Color = Color3.fromHex(if d.Parent.Name == "cy_case" then "6a5d48" else "5e5046") end
		if d:IsA("BasePart") and d.Parent and d.Parent.Name == "cy_primer" then d.Color = Color3.fromHex("8a7350") end
	end
	K.lookZone("cylinder", -120, 120, -40, 100, -100, 210)
	return f
end

function HC.walks(K)
	local F0 = CFrame.new()
	return {
		{ "the spawn's floor", F0, -10, 10, 98, 112, 0 },
		{ "the breech west of the middle", F0, -22, -11, 57, 97, 0 }, -- (kit 7: the dais is 20 across)
		{ "the breech east of the middle", F0, 11, 22, 57, 97, 0 },
		{ "the breech south of the middle", F0, -8, 8, 88, 97, 0 },
		{ "the breech north of the middle", F0, -8, 8, 57, 66, 0 },
		{ "the passage to the face", F0, -8, 8, 28, 42, 0 },
		{ "the transept", F0, -20, 20, 4, 22, 0 },
		{ "the gym's portal", F0, -6, 6, 120, 136, 0 },
		{ "the lounge", CFrame.new(-13, -4, 0), -2.2, 3.0, -20, -8, 0 },
		{ "the armory", CFrame.new(13, -4, 0), -2.5, 2.5, -70, -8, 0 },
		{ "to the golf room", F0, -60, -44, 9, 13, 0 },
	}
end
function HC.leaks()
	local F0 = CFrame.new()
	return { { F0, 0, 10, 70 }, { F0, 0, 8, 164 }, { F0, -13, 2, -40 }, { F0, 13, 2, -40 }, { F0, 0, 20, 12 }, { F0, -72, 8, 4 }, { F0, 55, 6, 12 } }
end
HC.SHOTS = {
	{ "spawn", Vector3.new(0, 5.4, 107), Vector3.new(0, 14, 0) },
	{ "breech_w", Vector3.new(14, 5.4, 82), Vector3.new(-60, 10, 66) },
	{ "breech_e", Vector3.new(-14, 5.4, 82), Vector3.new(60, 10, 66) },
	{ "up", Vector3.new(0, 4, 96), Vector3.new(0, 30, 77) },
	{ "lounge2", Vector3.new(-18, 2.6, -9), Vector3.new(-9, 0, -58) },
	{ "armory2", Vector3.new(18, 3, -5), Vector3.new(9, 2.5, -62) },
	{ "zombies", Vector3.new(4, 26, 26), Vector3.new(11, 45, -6) },
	{ "transept", Vector3.new(0, 6, 34), Vector3.new(0, 30, 0) },
	{ "face", Vector3.new(0, 16, 34), Vector3.new(0, 30, 0) },
	{ "lounge", Vector3.new(-13, 3, 4), Vector3.new(-13, 1, -60) },
	{ "armory", Vector3.new(13, 3, 4), Vector3.new(13, 2, -70) },
	{ "gym", Vector3.new(0, 6, 126), Vector3.new(0, 4, 190) },
	{ "balcony", Vector3.new(-30, 24, 6), Vector3.new(20, 10, 60) },
}
return HC
