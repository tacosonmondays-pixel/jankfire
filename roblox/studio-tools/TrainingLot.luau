--!nocheck
-- TRAINING LOT: the training area's secret outdoor grounds (16 Nov 2026), built into training v2 by TrainingV2.build
-- (it calls L.build(B, T) when ServerStorage.PolishBackup.TrainingLot is there). the owner, 16 Nov: "can you add a
-- large garage door that leads outside to the big rivals style training grounds, you have to do like a little easter
-- egg to get it or something".
-- the idea: the dummy yard now ends on a big roll-up GARAGE DOOR, on the axis you look down when you arrive, with a
-- panel beside it: three dark cardboard men and one line, "ask the gold ones." three GOLD CARLS hide in the training
-- rooms (on the bench in the bench bay; on the first beam over the range, looking down the lane; in the lit bay at
-- the course's near end, behind you as you climb). shoot all three within 90 s and the door rolls up (the server's
-- TheLot.server.luau). behind it a loading bay, and out through its portal THE BACK LOT: an open-air training ground
-- in a valley. the LONG LANE (Carls at 25, 50, 75 and 100 m from a roofed firing line, each row a step higher, a slate
-- backstop), THE BLOCKS (a container yard: container walls 2 and 3 high, a raised pad, a three-storey house, a catwalk
-- from its roof to a container tower, a slate kerb round it), THE CLIMB (one slate plinth: a pad onto a deck, a slide,
-- a cut gap, stepping drums, a summit, a walled canyon with two masts, a 48-stud finish tower) and THE HILL (slate
-- terraces, walled ramps, a core watchtower you are thrown up through), inside berms, trees and a ridge of hills that
-- hides the playground's towers (L.horizon checks it). you leave by the EXIT door beside the portal (down to the
-- basement and up its walk-out into the range: no teleport) or through the garage while it is up; anyone who has opened
-- it can stand at it to reopen it.
-- (push 7 is judge round 1's rework: vault Reviews\Back lot - judge round 1.md)
-- what the game reads (TheLot.server.luau): Hub.TrainingGround.Lot { Door, Doorway, Panel, Beacons, GoldSpots, Targets,
-- Area (one part or more) }; TrainingDoors.client: the walk-out's WalkOutDoor (OneWayDoor) and the gold dummies'
-- EggDoor; LaserDoors: Doors.EggPortal (NeedKey). kit: tools/roblox/lot_models.py (L.KIT).
--   usage (Edit, command bar): require(game.ServerStorage.PolishBackup.TrainingLot:Clone()).import()  (the kit), then
--   TrainingV2's T.build("live") builds the lot with everything else.
local L = {}
local SS = game:GetService("ServerStorage")
local InsertService = game:GetService("InsertService")
local CollectionService = game:GetService("CollectionService")
local SP, NEON = Enum.Material.SmoothPlastic, Enum.Material.Neon
local V3, CF = Vector3.new, CFrame.new
local RAD = math.rad

L.KIT = 102031091411579 -- the kit's Model asset (tl_kit_5: lot_models.py; kit 5: flicker fixes in the frames and the roller)
L.PORTAL_KIT = 125041627506798 -- the gold dummies' portal (te_portal_1: tools/roblox/egg_portal_models.py), L.import(L.PORTAL_KIT)
L.PUSH = 17

-- the plan (world coordinates). the yard's end wall is z -8258..-8262; the door runs in its middle plane
local G = 240                                                     -- the lot's ground
L.DOOR = { x = 12, y0 = 242, y1 = 258.5, z = -8260 }              -- the opening x -12..12, y 242..258.5
L.BAY = { x = 22, z0 = -8262, z1 = -8300, top = 264 }             -- the loading bay, inside
L.FACE = { x0 = -146, x1 = 92, z0 = -8300, z1 = -8304, top = 284 } -- the façade the lot sees (west end -100 until 18 Nov: the course grew west)
L.GOLD = { -- the gold Carls: feet, and a point he looks toward
	-- (16 Nov, the owner: a lone gold dummy in a wall opening "seems random". so each stands where targets belong: one
	-- among the dummy yard's marked dummies on its 30 m line, one on the range's first beam, one on top of the course's
	-- tower, the course's prize. the bench bay is the mirror now and the course bay is empty again)
	{ "yard 30 m", V3(-8, 242, -8237), V3(-8, 242, -8146) },
	{ "range beam", V3(66, 266.6, -8150), V3(66, 266.6, -8250) },
	{ "course tower", V3(-58, 268, -8170), V3(-30, 268, -8122) },
}

local C = { -- the lot's own colours (the hall's family, plus muted grass)
	grass = "959c89", grass2 = "8a927e", berm = "8b9580", hill = "8d9883", hill2 = "97a18c", conc = "b5b1a9", conc2 = "aeaaa2", joint = "a19d95",
	lane = "9f9d98", laneLine = "d9d5cc", rubber = "a59f96", house = "d8d3ca", house2 = "c6c0b5",
	rust = "a2806a", blue = "748596", sand = "b9ab8f", grey = "8f959d", drum = "9a8a74",
	-- (push 7, judge round 1: two muted container tones and one amber; the ridge; the door's mid-slate panels)
	slateC = "6c727b", warmC = "9a948a", amberC = "c9973f", tyre = "6a6f78", ridge = "8b9580", ridgeHi = "a3ab9c",
	housing = "9a9ea5", inset = "7d8088", pipOff = "c6c0b5", rock = "a39f98", glass = "aeb2b8",
}

local function folderIn(parent, name)
	local f = parent:FindFirstChild(name)
	if not f then f = Instance.new("Folder"); f.Name = name; f.Parent = parent end
	return f
end
local function lib() return SS:WaitForChild("JankfireMeshes") end

-- ---------------------------------------------------------------- the kit
function L.import(id: number?): string
	local MAT = { plastic = SP, neon = NEON }
	local kitId = id or L.KIT
	local ok, container = pcall(function() return InsertService:LoadAsset(kitId) end)
	if not ok or not container then return "LOAD FAILED " .. tostring(container) end
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
		m:SetAttribute("AssetId", kitId); m:SetAttribute("Kit", "lot"); m:SetAttribute("FileFrame", true)
		local old = lib():FindFirstChild(name)
		if old then old:Destroy() end
		m.Parent = lib()
		local _, size = m:GetBoundingBox()
		table.insert(names, ("%s %d (%.1f x %.1f x %.1f)"):format(name, #parts, size.X, size.Y, size.Z))
	end
	container:Destroy()
	table.sort(names)
	return #names .. " models" .. (if bad > 0 then ", " .. bad .. " pieces with no name rule" else "") .. "\n  " .. table.concat(names, "\n  ")
end

-- ---------------------------------------------------------------- helpers on top of TrainingV2's build context B
local B, P, LOT, TV
local function blk(name, x0, x1, y0, y1, z0, z1, hex, o) return B.blk("LotShell", name, x0, x1, y0, y1, z0, z1, hex, o) end
local function deco(name, x0, x1, y0, y1, z0, z1, hex, o)
	local t = table.clone(o or {}); t.ghost = true
	return B.blk("LotScenery", name, x0, x1, y0, y1, z0, z1, hex, t)
end
local function part(name, cf, size, hex, o) return B.part("LotShell", name, cf, size, hex, o) end
-- a box of ground from x0..x1, z0..z1 minus the holes { { x0, x1, z0, z1 } } (cut into strips along z)
local function ground(name, x0, x1, z0, z1, top, hex, holes)
	local zs = { z0, z1 }
	for _, h in holes or {} do table.insert(zs, h[3]); table.insert(zs, h[4]) end
	table.sort(zs, function(a, b) return a > b end) -- (z runs negative: north to south)
	for i = 1, #zs - 1 do
		local za, zb = zs[i], zs[i + 1]
		if za - zb < 0.01 or za > math.max(z0, z1) + 0.01 or zb < math.min(z0, z1) - 0.01 then continue end
		local zm = (za + zb) / 2
		local cuts = {}
		for _, h in holes or {} do
			if zm < math.max(h[3], h[4]) and zm > math.min(h[3], h[4]) then table.insert(cuts, { math.min(h[1], h[2]), math.max(h[1], h[2]) }) end
		end
		table.sort(cuts, function(a, b) return a[1] < b[1] end)
		local x = x0
		for _, c in cuts do
			if c[1] > x + 0.01 then blk(name, x, c[1], top - 8, top, za, zb, hex) end
			x = math.max(x, c[2])
		end
		if x1 > x + 0.01 then blk(name, x, x1, top - 8, top, za, zb, hex) end
	end
end
-- a wall along x (z0..z1 its thickness) with rectangular holes { { x0, x1, y0, y1 } }
local function wallX(name, x0, x1, y0, y1, z0, z1, hex, holes)
	local xs = { x0, x1 }
	for _, h in holes do table.insert(xs, h[1]); table.insert(xs, h[2]) end
	table.sort(xs)
	for i = 1, #xs - 1 do
		local a, b = xs[i], xs[i + 1]
		if b - a < 0.01 then continue end
		local xm = (a + b) / 2
		local spans = { { y0, y1 } }
		for _, h in holes do
			if xm > h[1] and xm < h[2] then
				local out = {}
				for _, s in spans do
					if h[3] > s[1] then table.insert(out, { s[1], math.min(h[3], s[2]) }) end
					if h[4] < s[2] then table.insert(out, { math.max(h[4], s[1]), s[2] }) end
				end
				spans = out
			end
		end
		for _, s in spans do if s[2] - s[1] > 0.01 then blk(name, a, b, s[1], s[2], z0, z1, hex) end end
	end
end
-- the same along z (x0..x1 its thickness), holes { { z0, z1, y0, y1 } }
local function wallZ(name, z0, z1, y0, y1, x0, x1, hex, holes)
	local zs = { z0, z1 }
	for _, h in holes do table.insert(zs, h[1]); table.insert(zs, h[2]) end
	table.sort(zs)
	for i = 1, #zs - 1 do
		local a, b = zs[i], zs[i + 1]
		if b - a < 0.01 then continue end
		local zm = (a + b) / 2
		local spans = { { y0, y1 } }
		for _, h in holes do
			if zm > math.min(h[1], h[2]) and zm < math.max(h[1], h[2]) then
				local out = {}
				for _, s in spans do
					if h[3] > s[1] then table.insert(out, { s[1], math.min(h[3], s[2]) }) end
					if h[4] < s[2] then table.insert(out, { math.max(h[4], s[1]), s[2] }) end
				end
				spans = out
			end
		end
		for _, s in spans do if s[2] - s[1] > 0.01 then blk(name, x0, x1, s[1], s[2], a, b, hex) end end
	end
end
-- a rounded white nose along an edge you step or jump from (a cylinder along x or z)
local function nose(name, axis, a0, a1, y, c, dia)
	dia = dia or 1.2
	if axis == "x" then return part(name, CF((a0 + a1) / 2, y, c), V3(math.abs(a1 - a0), dia, dia), P.trim, { cyl = true }) end
	return part(name, CF(c, y, (a0 + a1) / 2) * CFrame.Angles(0, math.pi / 2, 0), V3(math.abs(a1 - a0), dia, dia), P.trim, { cyl = true })
end
-- a kit model with a collision box (size, its middle over cf's floor point)
local function prop(tmpl, x, y, z, yaw, box, o)
	local cf = CF(x, y, z) * CFrame.Angles(0, RAD(yaw or 0), 0)
	local m = B.put(tmpl, cf, o)
	if m then m.Parent = B.root.LotScenery end
	if box then B.solid(tmpl .. "Box", cf * CF(0, box.Y / 2, 0), box) end
	return m
end
local function sign(name, lines, w, h, x, y, z, faceTo, o)
	local at = V3(x, y, z)
	local t = B.text(name, lines, w, h, CFrame.lookAt(at, V3(faceTo.X, y, faceTo.Z)), o)
	t.Parent = B.root.LotScenery
	return t
end
local function post(x, z, y0, y1)
	blk("SignPost", x - 1.2, x + 1.2, y0, y1, z - 1.2, z + 1.2, P.slate) -- (2.4 square, like the lane's posts: judge round 3)
end
-- a Carl's spot on the lot (TheLot stands a cardboard man here: he faces `look`)
local function target(x, y, z, look)
	B.marker(LOT.Targets, "Target", x, y, z, look)
	B.drum("LotScenery", "TargetRing", x, z, y + 0.03, y + 0.06, 4.2, P.trim, { ghost = true })
	B.drum("LotScenery", "TargetRingIn", x, z, y + 0.06, y + 0.1, 3.1, C.conc2, { ghost = true })
end

-- ---------------------------------------------------------------- a cardboard man in parts, facing +z (the panel's men, the backstop's relief)
-- (judge round 2: a disc over a block read as a toilet sign. a cut-out: a head, shoulders that taper to the hips, a
-- base. h = his height; parts are returned so the caller can tag them)
local function cardMan(name, x, y, z, h, hex, depth, o)
	local s = h / 3.6
	local out = {}
	local zc = z + depth / 2
	local function add(p) table.insert(out, p); return p end
	add(part(name, CF(x, y + 0.15 * s, zc), V3(2.0 * s, 0.3 * s, depth), hex, o))            -- base
	add(part(name, CF(x, y + 0.65 * s, zc), V3(1.6 * s, 0.7 * s, depth), hex, o))            -- hips
	add(part(name, CF(x, y + 1.35 * s, zc), V3(2.0 * s, 0.7 * s, depth), hex, o))            -- waist
	add(part(name, CF(x, y + 2.05 * s, zc), V3(2.4 * s, 0.7 * s, depth), hex, o))            -- shoulders
	local oc = table.clone(o or {}); oc.cyl = true
	add(part(name, CF(x, y + 3.0 * s, zc) * CFrame.Angles(0, math.pi / 2, 0), V3(depth, 1.2 * s, 1.2 * s), hex, oc)) -- head
	return out
end

-- ---------------------------------------------------------------- the garage door (the yard's side and the door)
-- (judge round 1: the end reads as one gate now. a slate roller box across the frame's head, a lit transom in the
-- lunette under the last rib, deep mid-slate panels with raised cardboard men that can be read from the yard's steps,
-- warm daylight under the door that lights the floor)
local function garage()
	local D = L.DOOR
	local yardFace = D.z + 2 -- -8258
	-- the portal through the wall, the slats in its middle plane (a hand's gap under them: daylight)
	B.put("tl_garageFrame", CF(0, D.y0, D.z), { name = "GarageFrame" }).Parent = B.root.LotScenery
	B.solid("GarageJamb", CF(-13.5, (D.y0 + 262) / 2, D.z), V3(3, 262 - D.y0, 6.4))
	B.solid("GarageJamb", CF(13.5, (D.y0 + 262) / 2, D.z), V3(3, 262 - D.y0, 6.4))
	local door = LOT.Door
	local N, H, GAP = 13, 1.3, 0.6
	for i = 0, N - 1 do
		local y0 = D.y0 + GAP + i * H
		local th = if i % 2 == 0 then 0.6 else 0.48
		local hex = if i == 0 then P.slate elseif i % 2 == 0 then P.pier else "868a91"
		local p = part("Slat", CF(0, y0 + H / 2, D.z), V3(24.6, H, th), hex)
		p.CanCollide = true; p.CanQuery = true
		p:SetAttribute("Shut", p.CFrame)
		p.Parent = door
	end
	for k = 0, 7 do -- the bottom rail's hazard blocks, both faces (they ride with the bottom slat)
		local x = -12.3 + 24.6 / 8 * (k + 0.5)
		if k % 2 == 0 then
			for _, sz in { -1, 1 } do
				local p = part("SlatHazard", CF(x, D.y0 + GAP + 0.65, D.z + sz * 0.33), V3(24.6 / 8, 1.1, 0.06), P.amber, { ghost = true })
				p:SetAttribute("Shut", p.CFrame)
				p.Parent = door
			end
		end
	end
	door:SetAttribute("Lift", N * H + GAP + 0.3)
	door:SetAttribute("Top", D.y1)
	-- (16 Nov, sealing: the slats are thin and a fast player can go through thin parts, so the doorway is also blocked
	-- by one unseen block 4 thick. TheLot turns it off with the slats when the door is up)
	local blockP = Instance.new("Part")
	blockP.Name = "DoorBlock"; blockP.Anchored = true; blockP.Transparency = 1; blockP.CanCollide = true; blockP.CanQuery = true; blockP.CanTouch = false
	blockP.Size = V3(24.6, D.y1 - D.y0, 4); blockP.CFrame = B.cf(0, (D.y0 + D.y1) / 2, D.z)
	blockP.Parent = LOT
	-- daylight under the door: a warm band that throws a fan of light across the yard's floor
	local sill = deco("ThresholdLight", -12, 12, D.y0, D.y0 + GAP, D.z - 0.24, D.z + 0.24, "ffd296", { mat = NEON })
	sill.CanQuery = true -- (sight lines and shots stop at the door, gap or not)
	local sl = Instance.new("SurfaceLight")
	sl.Face = Enum.NormalId.Back; sl.Color = Color3.fromRGB(255, 210, 150); sl.Range = 9; sl.Brightness = 2.4; sl.Angle = 120
	sl.Parent = sill
	-- nobody is shut in it
	local dw = Instance.new("Part")
	dw.Name = "Doorway"; dw.Anchored = true; dw.Transparency = 1; dw.CanCollide = false; dw.CanQuery = false; dw.CanTouch = false
	dw.Size = V3(24, D.y1 - D.y0, 9); dw.CFrame = B.cf(0, (D.y0 + D.y1) / 2, D.z)
	dw.Parent = LOT
	-- the roller box across the frame's head (yard side), and a lit transom in the lunette over it
	B.put("tl_roller", CF(0, D.y1 + 0.1, yardFace + 3.0), { name = "RollerYard", scale = 0.8, color = { ["7d8088"] = C.housing } }).Parent = B.root.LotScenery
	local function vaultAt(x) return 258 - 23.8 + math.sqrt(33.8 * 33.8 - x * x) end
	for k = -2, 2 do
		local x = k * 5
		local top = math.min(vaultAt(x - 2.2), vaultAt(x + 2.2)) - 0.4
		deco("TransomPane", x - 2.2, x + 2.2, 262.6, top, yardFace + 0.05, yardFace + 0.3, "dcc39a", { mat = NEON })
		if k < 2 then blk("TransomMullion", x + 2.2, x + 2.8, 262.4, vaultAt(x + 2.5), yardFace, yardFace + 0.5, C.housing) end
	end
	blk("TransomSill", -13, 13, 262.2, 262.6, yardFace, yardFace + 0.6, C.housing)
	local tp = deco("TransomLight", -1, 1, 263, 264, yardFace + 0.3, yardFace + 0.35, "dcc39a")
	tp.Transparency = 1
	local tl2 = Instance.new("SurfaceLight")
	tl2.Face = Enum.NormalId.Back; tl2.Color = Color3.fromRGB(255, 222, 176); tl2.Range = 22; tl2.Brightness = 1.2; tl2.Angle = 100
	tl2.Parent = tp
	-- the panels: deep mid-slate housings, the words on a darker inset, no strips
	local function housing(x0, x1)
		blk("GaragePanel", x0, x1, 243.6, 256, yardFace, yardFace + 1.5, C.housing)
		blk("GaragePanelInset", x0 + 0.6, x1 - 0.6, 244.2, 255.4, yardFace + 1.5, yardFace + 1.62, C.inset)
	end
	housing(15.6, 23.4); housing(-23.4, -15.6)
	-- (judge round 3: the panels read near-black; a warm spot on each from the vault)
	for _, x in { -19.5, 19.5 } do B.lamp(x, 257.5, yardFace + 5, "spot", 16, 2.5, "ffdeb0", { look = V3(x, 249.5, yardFace + 1.6), angle = 60 }) end
	local front = yardFace + 1.66
	local panel = LOT.Panel
	sign("PanelHead", { { "LOCKED", P.amber, "B", 1 } }, 5.4, 1.3, 19.5, 254.6, front, V3(19.5, 0, -8000), { clear = true }).Parent = panel
	for i, x in { 17.3, 19.5, 21.7 } do
		for _, q in cardMan("Pip", x, 249.7, front, 3.0, C.pipOff, 0.5, { ghost = true }) do q:SetAttribute("Pip", i); q.Parent = panel end
		sign("PipLabel", { { ({ "YARD", "RANGE", "COURSE" })[i], P.grey, "S", 1 } }, 2.1, 0.5, x, 248.9, front, V3(x, 0, -8000), { clear = true }).Parent = panel
	end
	local tm = Instance.new("Part")
	tm.Name = "Timer"; tm.Anchored = true; tm.CanCollide = false; tm.CanQuery = false; tm.CanTouch = false; tm.CastShadow = false
	tm.Transparency = 1; tm.Size = V3(5.4, 1.2, 0.1)
	tm.CFrame = B.at(CFrame.lookAt(V3(19.5, 246.9, front), V3(19.5, 246.9, -8000)))
	local g = Instance.new("SurfaceGui")
	g.Name = "Gui"; g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; g.PixelsPerStud = 40; g.LightInfluence = 0
	local tl = Instance.new("TextLabel")
	tl.Name = "Text"; tl.BackgroundTransparency = 1; tl.Size = UDim2.fromScale(1, 1); tl.TextScaled = true; tl.Text = "1:30"
	tl.TextColor3 = Color3.fromHex(P.pale); tl.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Heavy)
	tl.Parent = g; g.Parent = tm; tm.Parent = panel
	-- (the door's own sounds play from here: TheLot plays Ding, Open, Close and Buzz)
	local lib2 = game:GetService("ReplicatedStorage"):FindFirstChild("JankfireSounds")
	-- (16 Nov: it rolls up as you walk up to it. a motor's whirr up and down, a clatter when it is locked)
	for name, src in { Ding = { "ting", 1 }, Open = { "whirr", 0.8 }, Close = { "whirr", 0.62 }, Buzz = { "whoops", 1 }, Rattle = { "clatter", 0.85 } } do
		local s = lib2 and lib2:FindFirstChild(src[1])
		if s and s:IsA("Sound") then
			local c = s:Clone(); c.Name = name; c.PlaybackSpeed = s.PlaybackSpeed * src[2]
			c.RollOffMinDistance = 30; c.RollOffMaxDistance = 400; c.Parent = tm
		end
	end
	sign("PanelHint", { { 'ask the <font color="#f2b84b">gold</font> ones.', P.grey, "S", 1 } }, 6, 1.35, 19.5, 245, front, V3(19.5, 0, -8000), { clear = true, rich = true }).Parent = panel
	sign("KeepClear", { { "KEEP", P.amber, "B", 1 }, { "CLEAR", P.amber, "B", 1 } }, 5.4, 3.6, -19.5, 250.6, front, V3(-19.5, 0, -8000), { clear = true })
	for k = 0, 5 do -- the door's hazard band across the panel's foot, so the panel belongs to the door
		local x0 = -22.8 + 1.1 * k
		blk("PanelHazard", x0, x0 + 1.1, 244.5, 245.7, front - 0.1, front + 0.05, if k % 2 == 0 then P.amber else P.slate)
	end
	-- the beacons (the yard's two over the panels; two more on the lot's canopy). turned so one lens faces you
	local function beacon(x, y, z, yaw)
		blk("BeaconBracket", x - 1.2, x + 1.2, y - 0.6, y, z - 1.4, z + 1.4, P.slate)
		local m = B.put("tl_beacon", CF(x, y, z) * CFrame.Angles(0, RAD(yaw), 0), { name = "Beacon" })
		if not m then return end
		m.Parent = LOT.Beacons
		m:SetAttribute("Spin", 0)
		CollectionService:AddTag(m, "HubSpin")
		for _, d in m:GetDescendants() do
			if d:IsA("BasePart") and d.Material == NEON then
				d:SetAttribute("Lens", true); d.Material = SP; d.Color = Color3.fromRGB(150, 112, 62)
			end
		end
		local lens = m:FindFirstChildWhichIsA("BasePart")
		local l = Instance.new("PointLight")
		l.Color = Color3.fromRGB(255, 170, 60); l.Range = 16; l.Brightness = 1.4; l.Enabled = false
		l.Parent = lens
	end
	beacon(19.5, 256.6, yardFace + 1.4, 90)
	beacon(-19.5, 256.6, yardFace + 1.4, 90)
	-- the bay's side: the roller box over the opening
	B.put("tl_roller", CF(0, D.y1 + 0.3, D.z - 2 - 1.2 - 2.3), { name = "Roller" }).Parent = B.root.LotScenery
	return beacon
end

-- ---------------------------------------------------------------- the loading bay and the façade the lot sees
-- ---------------------------------------------------------------- the basement behind the EXIT door (T.BASEMENT)
-- (17 Nov, the owner: the EXIT door "seemly leads no where, can it be like a basement section?") a landing behind the
-- door, sixteen steps cut into the range's backstop running down east (a handrail on each wall, two caged lamps), and at
-- their foot an opening north into the basement under the range's far terrace: pipes along its ceiling on brackets, a
-- boiler with its flue and a squat tank, shelves of crates, a fuse box, caged lamps. its far door, in the west wall, is
-- the way out: stairs up through the backstop bank to a door onto the range's far terrace (T.BASEMENT.exit). below the
-- hall's floors (236) it has walls of its own; everything bounding it is solid and 2 thick (T.check's seal test has
-- points in it; L.check probes its floors for holes)
local function cagedLamp(x, y, z, range, bright)
	B.drum("LotScenery", "CagedLampBase", x, z, y - 0.3, y, 1.6, P.slate, { ghost = true })
	B.drum("LotScenery", "CagedLampBulb", x, z, y - 1.2, y - 0.3, 0.9, P.warm, { ghost = true, mat = NEON })
	for k = 0, 3 do
		local a = k * math.pi / 2 + math.pi / 4
		local cx, cz = x + math.cos(a) * 0.62, z + math.sin(a) * 0.62
		deco("CagedLampBar", cx - 0.06, cx + 0.06, y - 1.4, y - 0.3, cz - 0.06, cz + 0.06, P.slate)
	end
	deco("CagedLampRing", x - 0.7, x + 0.7, y - 1.5, y - 1.4, z - 0.7, z + 0.7, P.slate)
	B.lamp(x, y - 1.7, z, "point", range, bright, P.warm)
end
local function basement(BS)
	local W, R, FL = BS.well, BS.room, BS.floor
	local LOW = FL - 2 -- (the bottom of everything: solid down to here)
	local N = 16
	local xs = W.x0 + 4 -- (the landing behind the door, then the first step)
	local rise = (G - FL) / N
	local run = (W.x1 - 6 - W.x0 - 4) / N -- (the steps stop 6 short of the east wall: the foot's landing)
	local xf = xs + N * run
	-- the landing, the steps and the foot, each solid down to LOW
	blk("WellLanding", W.x0, xs, LOW, G, W.z0, W.z1, P.floor2)
	for i = 0, N - 1 do
		local xa = xs + i * run
		local top = G - rise * (i + 1)
		blk("WellStep", xa, xa + run, LOW, top, W.z0, W.z1, P.floor2)
		deco("WellStepEdge", xa + run - 0.3, xa + run, top, top + 0.04, W.z0 + 0.4, W.z1 - 0.4, P.trim)
	end
	blk("WellFoot", xf, W.x1, LOW, FL, W.z0, W.z1, P.floor2)
	-- (owner, 17 Nov: "there's a hole in the ground once you go down the stairs": the strip between the foot and the
	-- basement's floor, where the south wall stops to let you in, had no floor; L.check's floor probes walk it now)
	blk("WellThreshold", xf, W.x1, LOW, FL, W.z1, R.z0, P.floor2)
	-- a handrail on each wall, 3 over the steps' edges, on brackets into the wall. (owner, 17 Nov: "the railing down
	-- should be against the wall because the one that isnt is just floating": the south rail ran across the door's
	-- opening with nothing behind it; it now starts where it drops under the opening's sill, the wall behind it)
	local ang = math.atan2(G - FL, N * run)
	local mid = (W.z0 + W.z1) / 2
	local function railY(x) return G + 3 - (x - xs) * (G - FL) / (N * run) end
	local underSill = xs + (G + 3 - (G - 0.4)) * (N * run) / (G - FL) -- (where the rail is 0.4 under the opening's sill)
	for _, r in { { W.z0 + 0.45, W.z0, math.max(xs, underSill) }, { W.z1 - 0.45, W.z1, xs } } do
		local z, wz, xa = r[1], r[2], r[3]
		local xb = xf
		part("WellRail", CF((xa + xb) / 2, (railY(xa) + railY(xb)) / 2, z) * CFrame.Angles(0, 0, -ang), V3((xb - xa) / math.cos(ang), 0.35, 0.35), P.trim, { cyl = true })
		local nb = math.max(2, math.floor((xb - xa) / 4.5))
		for k = 0, nb - 1 do
			local x = xa + (k + 0.5) * (xb - xa) / nb
			local y = railY(x)
			blk("WellRailBracket", x - 0.15, x + 0.15, y - 0.3, y + 0.05, z, wz, P.slate)
		end
	end
	cagedLamp(W.x0 + 3, W.top - 0.1, mid, 24, 0.7)
	cagedLamp(W.x1 - 3, W.top - 0.1, mid, 30, 0.7)
	-- below the hall's floors: walls of its own round the well and the basement
	blk("WellWallS", W.x0 - 2, W.x1 + 2, LOW, 236, W.z0 - 2, W.z0, P.pier2)
	blk("BaseWallE", W.x1, W.x1 + 2, LOW, 236, W.z0 - 2, R.z1 + 2, P.pier2)
	blk("BaseWallS", R.x0 - 2, xf, LOW, 236, W.z1, R.z0, P.pier2) -- (open at the foot: the way in)
	blk("BaseWallN", R.x0 - 2, W.x1 + 2, LOW, 236, R.z1, R.z1 + 2, P.pier2)
	blk("BaseFloor", R.x0, R.x1, LOW, FL, R.z0, R.z1, P.floor2)
	blk("BaseCeiling", R.x0, R.x1, R.ceil, 235.9, R.z0, R.z1, P.ceil)
	deco("BaseSkirt", R.x0, R.x1, FL, FL + 1, R.z1 - 0.1, R.z1, P.slate)
	deco("BaseSkirt", R.x0, xf, FL, FL + 1, R.z0, R.z0 + 0.1, P.slate)
	-- the way out, walked (owner, 17 Nov: "can you make the exit actually connect to an exit because there should be no way
	-- for it to just tp you back into the main hub area"; it used to be a door in a niche whose trigger, Doors.LotExit,
	-- put you on the muster's spawns). the EXIT door in the west wall stands open onto a landing under the far terrace;
	-- stairs climb south, turn on a landing inside the backstop bank, climb east to a corridor at the far terrace's height,
	-- and a plain door in the bank's face, west of the big target, lets you out onto the far terrace (T.BASEMENT.exit;
	-- TrainingV2's range() leaves the hollow). that door opens from the corridor only, on the screen of whoever comes up it
	-- (a Model tagged OneWayDoor: TrainingDoors.client), so nobody in the hall gets down to the lot this way
	local EX = TV.BASEMENT.exit
	local DZ0, DZ1, DH = EX.land.z0 + 2, EX.land.z1, FL + 6.6
	local NX = R.x0 - 2
	wallZ("BaseWallW", R.z0 - 2, R.z1 + 2, LOW, 236, NX, R.x0, P.pier2, { { DZ0, DZ1, FL, DH } })
	blk("ExitJamb", R.x0, R.x0 + 0.4, FL, DH + 0.4, DZ0 - 0.8, DZ0, P.slate)
	blk("ExitJamb", R.x0, R.x0 + 0.4, FL, DH + 0.4, DZ1, DZ1 + 0.8, P.slate)
	blk("ExitHead", R.x0, R.x0 + 0.4, DH, DH + 0.4, DZ0, DZ1, P.slate)
	sign("WordBaseEXIT", { { "EXIT", P.amber, "B", 1 } }, 3.6, 1.0, R.x0 + 0.25, DH + 0.95, (DZ0 + DZ1) / 2, V3(R.x0 + 50, 0, (DZ0 + DZ1) / 2), { plate = P.board, thick = 0.2 })
	-- the door itself, held open flat against the landing's north wall, its push bar out
	blk("ExitLeaf", NX - (DZ1 - DZ0), NX, FL, DH, DZ1 - 0.3, DZ1, P.dark)
	deco("ExitPushBar", NX - (DZ1 - DZ0) + 0.8, NX - 0.8, FL + 3.4, FL + 3.8, DZ1 - 0.55, DZ1 - 0.3, P.trim)
	-- the stair hall's own walls under the hall's floors (over 236: the range's west wall, the bank's skin)
	local X0, TOP = EX.x0, EX.top
	local nA, nB = EX.fA.n, EX.fB.n
	local rise = (TOP - FL) / (nA + nB)
	local yA = FL + rise * nA
	local xB = EX.fB.x0 + nB -- (flight B's top: landing B east of it)
	blk("WalkWallW", X0 - 2, X0, LOW, 236, EX.land.z1 + 2, EX.back - 2, P.pier2)
	blk("WalkWallN", X0 - 2, NX, LOW, 236, EX.land.z1, EX.land.z1 + 2, P.pier2)
	blk("WalkWallS", X0 - 2, W.x0, LOW, 236, EX.back - 2, EX.back, P.pier2)
	blk("WalkWallE", EX.east, W.x0, LOW, 236, EX.skin, EX.back, P.pier2)
	blk("WalkWallA", EX.fA.x1, NX, LOW, EX.thin.y, EX.land.z0, EX.skin, P.pier2) -- (flight A's east side, up to the thin terrace)
	-- the landing behind the door, flight A (south), landing A, flight B (east), the corridor and landing B: solid down
	blk("WalkLanding", X0, NX, LOW, FL, EX.land.z0, EX.land.z1, P.floor2)
	for i = 0, nA - 1 do
		local za = EX.land.z0 - i
		local top = FL + rise * (i + 1)
		blk("WalkStep", X0, EX.fA.x1, LOW, top, za - 1, za, P.floor2)
		deco("WalkStepEdge", X0 + 0.4, EX.fA.x1 - 0.4, top, top + 0.04, za - 0.3, za, P.trim)
	end
	blk("WalkLandingA", X0, EX.landA.x1, LOW, yA, EX.landA.z0, EX.landA.z1, P.floor2)
	for j = 0, nB - 1 do
		local xa = EX.fB.x0 + j
		local top = yA + rise * (j + 1)
		blk("WalkStep", xa, xa + 1, LOW, top, EX.fB.z0, EX.fB.z1, P.floor2)
		deco("WalkStepEdge", xa, xa + 0.3, top, top + 0.04, EX.fB.z0 + 0.4, EX.fB.z1 - 0.4, P.trim)
	end
	blk("WalkTop", EX.hall.x0, EX.east, LOW, TOP, EX.hall.z0, EX.hall.z1, P.floor2)
	blk("WalkTop", xB, EX.east, LOW, TOP, EX.fB.z0, EX.hall.z0, P.floor2)
	-- walls between the flights and the corridor, floor to the bank's ceiling
	blk("WalkWall", EX.fA.x1, EX.hall.x0, LOW, EX.ceil, EX.skin, EX.landA.z1 - 1, P.pier2)
	blk("WalkWall", EX.hall.x0, xB, LOW, EX.ceil, EX.fB.z1, EX.hall.z0, P.pier2)
	-- a handrail along each flight's wall
	local angA = math.atan2(rise, 1)
	local lenA = nA / math.cos(angA)
	part("WalkRail", CF(X0 + 0.45, FL + rise * nA / 2 + 3, EX.land.z0 - nA / 2) * CFrame.Angles(angA, 0, 0) * CFrame.Angles(0, math.pi / 2, 0), V3(lenA, 0.35, 0.35), P.trim, { cyl = true })
	part("WalkRail", CF(EX.fB.x0 + nB / 2, yA + rise * nB / 2 + 3, EX.fB.z0 + 0.45) * CFrame.Angles(0, 0, angA), V3(nB / math.cos(angA), 0.35, 0.35), P.trim, { cyl = true })
	for k = 0, 2 do
		local d = (k + 0.5) * nA / 3
		local y = FL + rise * d + 3
		blk("WalkRailBracket", X0, X0 + 0.45, y - 0.3, y + 0.05, EX.land.z0 - d - 0.15, EX.land.z0 - d + 0.15, P.slate)
		local x = EX.fB.x0 + (k + 0.5) * nB / 3
		local y2 = yA + rise * (x - EX.fB.x0) + 3
		blk("WalkRailBracket", x - 0.15, x + 0.15, y2 - 0.3, y2 + 0.05, EX.fB.z0, EX.fB.z0 + 0.45, P.slate)
	end
	cagedLamp((X0 + NX) / 2, 235.9, (EX.land.z0 + EX.land.z1) / 2, 18, 0.55)
	cagedLamp((X0 + EX.fA.x1) / 2, EX.thin.y - 0.1, (EX.land.z0 + EX.face) / 2, 16, 0.5)
	cagedLamp((X0 + EX.landA.x1) / 2, EX.ceil - 0.1, (EX.landA.z0 + EX.landA.z1) / 2, 22, 0.6)
	cagedLamp((EX.hall.x0 + EX.east) / 2, EX.ceil - 0.1, (EX.hall.z0 + EX.hall.z1) / 2, 18, 0.55)
	-- the door out: a plain steel leaf in the bank's face, a slate frame on the terrace's side, no handle there; a push bar
	-- and EXIT on the corridor's side. it swings out onto the terrace on its opener's screen only; an unseen block behind
	-- it (a thin leaf alone lets a fast body through) goes with it. Hinge (its CFrame), Swing (radians), Center, Near
	local OD = EX.out
	local door = Instance.new("Model")
	door.Name = "WalkOutDoor"
	door:SetAttribute("ACPass", true) -- (the anti-cheat's noclip checks skip it: it is open on one screen only)
	local leaf = B.part("LotShell", "WalkOutLeaf", CF((OD.x0 + OD.x1) / 2, (TOP + OD.top) / 2, EX.face - 0.225), V3(OD.x1 - OD.x0 - 0.1, OD.top - TOP - 0.1, 0.25), P.dark)
	local bar = B.part("LotShell", "WalkOutPushBar", CF((OD.x0 + OD.x1) / 2, TOP + 3.6, EX.face - 0.47), V3(OD.x1 - OD.x0 - 1.2, 0.4, 0.25), P.trim, { ghost = true })
	for _, q in { leaf, bar } do q:SetAttribute("Shut", q.CFrame); q.Parent = door end
	local blkP = B.part("LotShell", "Block", CF((OD.x0 + OD.x1) / 2, (TOP + OD.top) / 2, EX.face - 0.7), V3(OD.x1 - OD.x0, OD.top - TOP, 0.6), P.slate, { tr = 1, noShadow = true })
	blkP.Parent = door
	local inside = B.part("LotShell", "Inside", CF((EX.hall.x0 + EX.east) / 2, (TOP + EX.ceil) / 2, (EX.hall.z0 + EX.hall.z1) / 2), V3(EX.east - EX.hall.x0, EX.ceil - TOP, EX.hall.z1 - EX.hall.z0), P.slate, { ghost = true, tr = 1 })
	inside.Parent = door
	for _, fr in { { OD.x0 - 0.5, OD.x0, TOP, OD.top + 0.5 }, { OD.x1, OD.x1 + 0.5, TOP, OD.top + 0.5 }, { OD.x0, OD.x1, OD.top, OD.top + 0.5 } } do
		blk("WalkOutFrame", fr[1], fr[2], fr[3], fr[4], EX.face, EX.face + 0.2, P.slate).Parent = door
	end
	door:SetAttribute("Hinge", B.at(CF(OD.x0 + 0.05, (TOP + OD.top) / 2, EX.face - 0.1)))
	door:SetAttribute("Swing", -math.pi / 2) -- (out onto the terrace, +Z, flat against its west jamb)
	door:SetAttribute("Center", B.at(CF((OD.x0 + OD.x1) / 2, TOP + 3, EX.face - 0.5)).Position)
	door:SetAttribute("Near", 5.5)
	door.Parent = B.root.LotShell
	CollectionService:AddTag(door, "OneWayDoor")
	sign("WordWalkOutEXIT", { { "EXIT", P.amber, "B", 1 } }, 3.6, 1.0, (OD.x0 + OD.x1) / 2, OD.top + 0.75, EX.skin - 0.25, V3((OD.x0 + OD.x1) / 2, 0, EX.skin - 60), { plate = P.board, thick = 0.2 })
	-- pipes along the ceiling on brackets
	for _, pp in { { R.z1 - 1.6, 1.4, C.slateC }, { R.z1 - 3.4, 1.0, P.pier }, { R.z1 - 4.9, 0.8, C.drum } } do
		part("BasePipe", CF((R.x0 + R.x1) / 2, R.ceil - 1.1, pp[1]), V3(R.x1 - R.x0, pp[2], pp[2]), pp[3], { cyl = true })
	end
	for x = R.x0 + 4, R.x1 - 2, 8 do blk("BasePipeBracket", x - 0.2, x + 0.2, R.ceil - 1.9, R.ceil, R.z1 - 5.6, R.z1 - 0.6, C.housing) end
	-- the boiler and its flue, a squat tank by it
	local bx, bz = R.x1 - 7, R.z1 - 9
	B.drum("LotShell", "BoilerBase", bx, bz, FL, FL + 0.6, 6.6, P.slate)
	B.drum("LotShell", "Boiler", bx, bz, FL + 0.6, FL + 6.4, 6, C.housing)
	B.drum("LotShell", "BoilerCap", bx, bz, FL + 6.4, FL + 7, 6.4, P.trim)
	B.drum("LotShell", "BoilerFlue", bx, bz, FL + 7, R.ceil, 1.2, C.slateC)
	part("BoilerDial", CF(bx - 3.02, FL + 3.6, bz), V3(0.12, 1.3, 1.3), P.pale, { cyl = true, ghost = true })
	B.drum("LotShell", "Tank", R.x1 - 16, R.z1 - 4.5, FL, FL + 4.6, 4.2, C.warmC)
	B.drum("LotShell", "TankCap", R.x1 - 16, R.z1 - 4.5, FL + 4.6, FL + 5, 4.4, P.trim)
	-- shelves of crates along the north wall
	local sx0, sx1, sz0, sz1 = R.x0 + 2, R.x0 + 16, R.z1 - 2.6, R.z1
	for _, x in { sx0, (sx0 + sx1) / 2 - 0.2, sx1 - 0.4 } do blk("ShelfPost", x, x + 0.4, FL, FL + 7.4, sz0, sz1, P.slate) end
	local boards = { FL + 1.2, FL + 3.8, FL + 6.4 }
	for _, y in boards do blk("ShelfBoard", sx0, sx1, y - 0.3, y, sz0, sz1, P.pier2) end
	for _, c in { { 0.6, 3.6, 1, 2.2, C.warmC }, { 4.2, 6.4, 1, 1.8, C.sand }, { 7.6, 10.8, 1, 2.2, C.slateC }, { 11.4, 13.4, 1, 1.6, C.warmC },
		{ 1, 4, 2, 2, C.sand }, { 8.2, 12.6, 2, 2.1, C.warmC }, { 0.8, 2.8, 3, 1.4, C.slateC }, { 9, 12, 3, 1.6, C.sand } } do
		local y = boards[c[3]]
		blk("ShelfCrate", sx0 + c[1], sx0 + c[2], y, y + c[4], sz0 + 0.3, sz1 - 0.1, c[5])
	end
	-- a fuse box on the south wall, its conduit up to the ceiling
	blk("FuseBox", R.x0 + 18, R.x0 + 21.5, FL + 1.8, FL + 5.4, R.z0, R.z0 + 0.8, C.housing)
	deco("FuseBoxDoor", R.x0 + 18.3, R.x0 + 21.2, FL + 2.1, FL + 5.1, R.z0 + 0.8, R.z0 + 0.86, C.inset)
	blk("FuseConduit", R.x0 + 19.5, R.x0 + 20, FL + 5.4, R.ceil, R.z0, R.z0 + 0.5, C.slateC)
	-- a regular down here (owner, 17 Nov: "can you add oxex21 @joxex21 down there"): the owner's friend on a crate in
	-- front of the shelves, facing the way in, clear of the walk to the far door. HubNPCs builds them from this place
	-- (a Seat tagged HubNPC) as it does the hub's regulars: their own avatar (or the saved copy JankfireNPCs.<Who>), their
	-- name over them, anchored, no shots; their clips and the living layer (breath, the head drifting, now and then to
	-- you) play on each screen. Idle: the hub's Mixamo seated breathing; Extra: a glance to the side now and then
	blk("SitCrate", R.x0 + 10.4, R.x0 + 13.6, FL, FL + 2.2, R.z1 - 7.6, R.z1 - 4.4, C.warmC)
	deco("SitCrateBand", R.x0 + 10.35, R.x0 + 13.65, FL + 0.9, FL + 1.3, R.z1 - 7.65, R.z1 - 4.35, C.slateC)
	local seat = Instance.new("Seat")
	seat.Name = "Regular_joxex21_Place"; seat.Size = V3(2, 0.2, 2); seat.Anchored = true; seat.CanCollide = false; seat.CanQuery = false
	seat.CanTouch = false; seat.Transparency = 1; seat.CastShadow = false; seat.Disabled = true
	local sat = V3(R.x0 + 12, FL + 2.3, R.z1 - 6)
	seat.CFrame = B.at(CFrame.lookAt(sat, V3(R.x0 + 22, FL + 2.3, R.z1 - 16)))
	seat:SetAttribute("Who", L.FRIEND.who); seat:SetAttribute("User", L.FRIEND.user); seat:SetAttribute("Pose", "sit")
	if L.FRIEND.id then seat:SetAttribute("UserId", L.FRIEND.id) end
	seat:SetAttribute("Idle", "rbxassetid://81991323034085") -- (the hub's seated breathing, Looticus's)
	seat:SetAttribute("Extra", "rbxassetid://114005193645149"); seat:SetAttribute("ExtraLen", 4); seat:SetAttribute("ExtraEvery", Vector2.new(15, 30))
	seat.Parent = B.root.LotScenery
	CollectionService:AddTag(seat, "HubNPC")
	-- caged lamps along the room
	for _, x in { R.x0 + 8, R.x0 + 20, R.x0 + 32 } do cagedLamp(x, R.ceil, (R.z0 + R.z1) / 2 - 4, 18, 0.55) end -- (south of the middle: clear of the boiler)
end

-- ---------------------------------------------------------------- the gold dummies' door (T.EGG_DOOR)
-- (17 Nov, the owner: a dead end in the training hall "should be the locked door connected to the dummies", "it should
-- lead to a portal teleporter that takes you to the training area that's in the air"): a roll-up garage door across a
-- corridor's end, LOCKED on a plate over it, and behind it a dark doorway (GateKit's GateBack: the owner, 17 Nov, "I like
-- the old black entrances for doors idk if i like the gold..").
-- it opens only on the screen of a player who has found the gold dummies (TheLot's key, the attribute LotKey):
-- TrainingDoors.client rolls it up as they come and lets them through; for everyone else it stays down and rattles.
-- the doorway's trigger (Hub.Doors.EggPortal: Land PlaygroundArrive, NeedKey LotKey) takes key holders, and only them,
-- to the playground's arrival (LaserDoors, with the anti-cheat's TeleportT stamp). the anti-cheat lets bodies through
-- its parts (ACPass). EGG = { cf = the floor in the middle of the opening's face (plan; its -Z the way you walk in),
-- w, h = the opening (GateKit's 8.4 x 9.96 if not given), cw, ch = the corridor's width and height (its sides and the
-- part over the frame are filled, so nobody walks round the door), wall = the fill's colour }. the corridor's end wall
-- stands DEPTH behind the opening's face (the door is built in front of it; nothing of the hall is cut).
-- EGG.room (18 Nov, the course's TOP door: the owner, "this is what should lead to the teleporter"): the door is only
-- EGG.door deep (its fill and the unseen block), there is no dark plate, and EGG.room studs behind the face (the
-- room's back wall, TrainingV2's topRoom) stands the portal (L.PORTAL_KIT's te_portal: a ring with a black middle on
-- a step; no light column, the owner: "I dont like the pillar of light from the teleporter"); its trigger is the black
-- middle, so a key holder walks through the door, across the room and into the ring
local EGG_COL = { slat = "6b7079", slat2 = "5f646d", frame = "4a4f58", back = "2b2d33" }
L.EGG_DEPTH = 3.2
L.PORTAL_BACK = 1.25 -- (the ring's plane, in front of the room's back wall)
local function eggDoor(EGG)
	local F: CFrame = EGG.cf
	local W, H = EGG.w or 8.4, EGG.h or 9.96
	local hw = W / 2
	local ROOM = EGG.room
	local DEPTH = if ROOM then EGG.door or 2.4 else L.EGG_DEPTH
	local function box(folder, name, x0, x1, y0, y1, d0, d1, hex, o)
		return B.part(folder, name, F * CF((x0 + x1) / 2, (y0 + y1) / 2, -(d0 + d1) / 2), V3(x1 - x0, y1 - y0, d1 - d0), hex, o)
	end
	local door = Instance.new("Model")
	door.Name = "EggDoor"
	door:SetAttribute("ACPass", true) -- (the anti-cheat's noclip checks skip it: it is open on some screens only)
	-- the corridor's sides and the part over the frame, filled from the face to the end wall
	local cw, ch = EGG.cw or W + 1.2, EGG.ch or H + 2.4
	local fill = EGG.wall or P.pier
	if cw / 2 > hw + 0.6 + 0.05 then
		box("LotShell", "EggFill", -cw / 2, -hw - 0.6, 0, ch, 0, DEPTH, fill)
		box("LotShell", "EggFill", hw + 0.6, cw / 2, 0, ch, 0, DEPTH, fill)
	end
	if ch > H + 0.6 + 0.05 then box("LotShell", "EggFill", -hw - 0.6, hw + 0.6, H + 0.6, ch, 0, DEPTH, fill) end
	-- the frame: slate jambs and a head round the opening, standing 0.3 proud of the fill
	box("LotShell", "EggFrame", -hw - 0.6, -hw, 0, H + 0.6, -0.3, 0.6, EGG_COL.frame).Parent = door
	box("LotShell", "EggFrame", hw, hw + 0.6, 0, H + 0.6, -0.3, 0.6, EGG_COL.frame).Parent = door
	box("LotShell", "EggFrame", -hw, hw, H, H + 0.6, -0.3, 0.6, EGG_COL.frame).Parent = door
	-- the slats, in the opening behind the frame's face; they roll up into the head (hidden over Top)
	local n = math.max(6, math.floor(H / 1.1))
	local sh = H / n
	for k = 0, n - 1 do
		local y = k * sh
		local sl = box("LotShell", "EggSlat", -hw, hw, y + 0.04, y + sh - 0.04, 0.6, 1.0, if k % 2 == 0 then EGG_COL.slat else EGG_COL.slat2)
		sl:SetAttribute("Shut", sl.CFrame)
		sl.Parent = door
	end
	if ROOM then -- (the room behind is lit: a dark sheet behind the slats rolls with them, so their gaps show no light)
		local sheet = box("LotShell", "EggSheet", -hw, hw, 0.02, H - 0.02, 1.0, 1.06, EGG_COL.back, { ghost = true })
		sheet:SetAttribute("Shut", sheet.CFrame)
		sheet.Parent = door
	end
	door:SetAttribute("Lift", H + 0.4)
	door:SetAttribute("Top", (F * CF(0, H, 0)).Y + B.O.Y)
	door:SetAttribute("Center", (F * CF(0, 1, 0)).Position + B.O)
	door:SetAttribute("Near", 11)
	-- an unseen block behind the slats (they are thin; a fast body goes through thin parts), up to the dark plate (or
	-- to the room)
	local blk2 = box("LotShell", "EggBlock", -hw, hw, 0, H, 1.0, if ROOM then DEPTH else DEPTH - 0.35, P.slate, { tr = 1, noShadow = true })
	blk2.Parent = door
	local trig = B.trigger("EggPortal", 0, 1, 0, 1, 0, 1, { Land = "PlaygroundArrive", Say = "YOU FOUND THE PLAYGROUND", NeedKey = "LotKey" })
	if not ROOM then
		-- the doorway at the corridor's end: the old dark plate, as GateKit's gates have it again (GateBack, "2b2d33")
		local back = box("LotScenery", "EggBack", -hw, hw, 0, H, DEPTH - 0.35, DEPTH - 0.05, EGG_COL.back, { ghost = true })
		back.Parent = door
		-- the trigger in front of the dark plate (Hub.Doors, read by LaserDoors): key holders only, to the playground
		trig.Size = V3(W - 0.6, H - 0.4, DEPTH - 1.2 + 0.6)
		trig.CFrame = B.at(F * CF(0, (H - 0.4) / 2, -(1.2 + DEPTH + 0.6) / 2))
	else
		-- the portal at the room's end, facing the door; you step up onto its step (unseen, solid: kit meshes have no
		-- collision) and the trigger in its black middle takes you. it starts 1.6 in front of the ring's plane (you are
		-- at the ring when you go) and runs back to the room's back wall: LaserDoors looks every 0.1 s, a walking body
		-- crosses 2 studs in that, and the first trigger (1.9 deep) was crossed between two looks (Play, 18 Nov)
		local ring = ROOM - L.PORTAL_BACK
		local pm = B.put("te_portal", F * CF(0, 0, -ring), { name = "EggPortalRing", raw = true })
		if pm then pm.Parent = B.root.LotScenery end
		B.solid("EggPortalStep", F * CF(0, 0.3, -(ring - 0.9)), V3(10.6, 0.6, 3.2))
		local t0, t1 = ring - 1.6, ROOM - 0.1
		trig.Size = V3(6.0, 6.4, t1 - t0)
		trig.CFrame = B.at(F * CF(0, 0.6 + 3.2, -(t0 + t1) / 2))
		-- a dim warm light over the ring, for its face (nothing shines up from it)
		local lr = F * CF(0, 9.6, -(ring - 2.2))
		B.lamp(lr.X, lr.Y, lr.Z, "point", 10, 0.45, "ffc27a")
	end
	-- LOCKED over it (a key holder's screen says OPEN), in the gold dummies' gold, no other words
	local pw = math.min(4.4, W - 1)
	local py = math.min(H + 0.85, ch - 1.3) -- (on the fill over the frame; low ceilings: as high as fits)
	local plate = box("LotScenery", "EggPlate", -pw / 2, pw / 2, py, py + 1.1, -0.12, 0, P.board, { ghost = true })
	local pg = Instance.new("SurfaceGui")
	pg.Name = "Gui"; pg.Face = Enum.NormalId.Back; pg.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; pg.PixelsPerStud = 40; pg.LightInfluence = 0
	local tl = Instance.new("TextLabel")
	tl.Name = "Text"; tl.BackgroundTransparency = 1; tl.Size = UDim2.fromScale(0.9, 0.8); tl.Position = UDim2.fromScale(0.05, 0.1)
	tl.TextScaled = true; tl.Text = "LOCKED"
	tl.TextColor3 = Color3.fromRGB(242, 184, 75); tl.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Heavy)
	tl.Parent = pg; pg.Parent = plate
	plate.Parent = door
	door.Parent = B.root.LotShell
	CollectionService:AddTag(door, "EggDoor")
	local lp = F * CF(0, math.min(H + 2.6, ch - 0.6), 1.2)
	B.lamp(lp.X, lp.Y, lp.Z, "point", 12, 0.55, "ffc27a")
	return door
end
L.eggDoor = eggDoor

local function bay(beacon)
	local Y = L.DOOR.y0
	local BX, Z0, Z1, TOP = L.BAY.x, L.BAY.z0, L.BAY.z1, L.BAY.top
	blk("BayFloor", -BX - 1.95, BX + 1.95, 236.05, Y, Z0, Z1 - 4, P.floor)
	blk("BayWall", -BX - 2, -BX, 236, TOP + 2, Z0, Z1, P.wall2)
	blk("BayWall", BX, BX + 2, 236, TOP + 2, Z0, Z1, P.wall2)
	blk("BayCeiling", -BX - 1.95, BX + 1.95, TOP + 0.1, TOP + 1.95, Z0, Z1, P.ceil) -- (clear of the portal's head and the walls' tops: flicker list)
	for _, sx in { -1, 1 } do
		deco("BayDado", sx * BX, sx * (BX - 0.2), Y, Y + 1.2, Z0, Z1, P.floor2)
		for _, z in { -8274, -8288 } do
			blk("BayPier", sx * BX, sx * (BX - 1.4), Y, TOP, z - 1.4, z + 1.4, P.pier)
		end
	end
	for _, z in { -8274, -8288 } do blk("BayBeam", -BX, BX, TOP - 2.2, TOP, z - 1.2, z + 1.2, P.pier) end
	for _, z in { -8268, -8281, -8294 } do
		local m = B.put("tv_lightbar", CF(0, TOP, z) * CFrame.Angles(0, math.pi / 2, 0), { name = "BayLight" })
		if m then m.Parent = B.root.LotScenery end
		B.lamp(0, TOP - 2, z, "spot", 30, 0.9, P.lampWhite, { angle = 110 })
	end
	for _, sx in { -1, 1 } do B.line(sx * 7, Z0 - 1, sx * 7, Z1 - 4, Y + 0.01, 0.6, P.line, "BayWalkLine") end
	-- what a loading bay keeps, against its walls (nothing in the portal's mouth)
	local greyCrate = { color = { b49a7a = "a8a29a", ["9c8466"] = "8f8a82" } } -- (round 4: the only brown on the lot)
	prop("tl_crate", -17.5, Y, -8266.5, 4, V3(4, 4, 4), greyCrate)
	prop("tl_crate", -17.5, Y + 4, -8266.5, -8, nil, greyCrate)
	prop("tl_crate", -17, Y, -8271, 12, V3(4, 4, 4), greyCrate)
	prop("tl_drum", 18.2, Y, -8268, 0, V3(2.8, 4.3, 2.8), { color = { a88a6a = C.drum } })
	prop("tl_drum", 17.6, Y, -8271.4, 40, V3(2.8, 4.3, 2.8), { color = { a88a6a = C.slateC } })
	prop("tl_drum", 14.9, Y, -8268.6, 70, V3(2.8, 4.3, 2.8), { color = { a88a6a = C.drum } })
	prop("tl_tyres", 18.5, Y, -8282, 0, V3(5.3, 4.5, 5.3), { color = { ["50545b"] = C.tyre } })
	prop("tv_bench", -18.6, Y, -8282, 90, V3(8, 2, 2.2), { color = { b49a7a = P.pier2 } })
	blk("ToolBoard", -BX, -BX + 0.3, Y + 4.5, Y + 10.5, -8287, -8277, C.housing)
	for k = 0, 3 do deco("ToolShape", -BX + 0.3, -BX + 0.42, Y + 6, Y + 9.2 - (k % 2) * 1.5, -8285.6 + k * 2.4, -8284.4 + k * 2.4, P.grey) end
	-- the façade: a tall wall the width of the hall with an attic over it (it hides the hall's roofs behind),
	-- piers, two gate towers either side of the portal, a window set 2 deep in every bay
	local F = L.FACE
	local exitX0, exitX1 = 52, 64 -- (full scale since judge round 3: it read bolted on)
	local WIN = { { -92, -72 }, { -68, -40 }, { 40, 70 }, { 74, 86 }, { -140, -120 }, { -116, -96 } } -- (the last two: the stretch added 18 Nov)
	local holes = { { -18, 18, Y - 0.05, TOP }, { exitX0, exitX1, G, G + 12 } }
	for _, b in WIN do table.insert(holes, { b[1] + 2.5, b[2] - 2.5, 268, 279 }) end
	wallX("Facade", F.x0, F.x1, 236, F.top, F.z0, F.z1, P.wall, holes)
	for i, b in ipairs(WIN) do -- (pale glazing set back 2 in a slate frame; two of them lit from inside)
		local gl = blk("FacadeWindow", b[1] + 2.5, b[2] - 2.5, 268, 279, F.z0, F.z0 - 2, C.glass)
		if i == 2 or i == 3 then
			local l = Instance.new("SurfaceLight"); l.Face = Enum.NormalId.Front; l.Color = Color3.fromRGB(255, 222, 180); l.Range = 14; l.Brightness = 1.2; l.Angle = 90
			l.Parent = gl
		end
		blk("FacadeWindowFrame", b[1] + 2, b[2] - 2, 279.05, 279.65, F.z0 - 2, F.z1 - 0.4, P.slate)
		blk("FacadeSill", b[1] + 2.5, b[2] - 2.5, 266.8, 268.04, F.z0 - 2, F.z1 - 1, C.housing)
		local w = (b[2] - 2.5) - (b[1] + 2.5)
		local n = math.clamp(math.floor(w / 9), 0, 2) -- (none in the narrow one: two read as bars)
		for k = 1, n do
			local x = b[1] + 2.5 + w * k / (n + 1)
			blk("FacadeMullion", x - 0.6, x + 0.6, 268, 279, F.z0 - 2, F.z0 - 2.6, P.slate)
		end
	end
	blk("FacadeAttic", F.x0, F.x1, F.top, 296, F.z0, F.z0 - 3, P.wall2)
	blk("FacadeAtticCap", F.x0 - 0.6, F.x1 + 0.6, 296, 297.4, F.z0 + 0.4, F.z0 - 3.8, P.trim)
	blk("FacadePlinth", F.x0 - 0.4, -40, G - 1, G + 2, F.z1, F.z1 - 0.6, P.slate)
	blk("FacadePlinth", 40, exitX0 - 1.2, G - 1, G + 2, F.z1, F.z1 - 0.6, P.slate)
	blk("FacadePlinth", exitX1 + 1.2, F.x1 + 0.4, G - 1, G + 2, F.z1, F.z1 - 0.6, P.slate)
	blk("FacadeCornice", F.x0 - 1, F.x1 + 1, F.top - 2, F.top, F.z1, F.z1 - 1.6, P.trim)
	for _, x in { -142, -118, -94, -70, 72, 88 } do
		blk("FacadePier", x - 2, x + 2, G - 1, F.top - 2, F.z1, F.z1 - 3, P.pier)
		blk("FacadePierCap", x - 2.4, x + 2.4, F.top - 2.8, F.top - 2, F.z1, F.z1 - 3.4, P.trim)
	end
	for _, sx in { -1, 1 } do
		local x0, x1 = sx * 28, sx * 40
		blk("GateTower", x0, x1, G - 1, 304, F.z1, F.z1 - 6, P.wall2)
		blk("GateTowerBase", x0 - sx * 0.4, x1 + sx * 0.4, G - 1, G + 3, F.z1, F.z1 - 6.6, P.slate)
		blk("GateTowerCap", x0 - sx * 0.6, x1 + sx * 0.6, 304, 305.6, F.z1 + 0.6, F.z1 - 6.8, P.trim)
		local xm = (x0 + x1) / 2
		blk("GateTowerSlot", xm - 1.6, xm + 1.6, 252, 298, F.z1 - 6, F.z1 - 6.5, P.dark)
		deco("GateTowerLight", xm - 0.7, xm + 0.7, 253, 297, F.z1 - 6.45, F.z1 - 6.6, P.panel, { mat = NEON })
		B.lamp(xm, 258, F.z1 - 9, "point", 18, 0.5, P.lampWhite)
	end
	-- the portal and its canopy, carried by the gate towers (no struts across the opening)
	B.put("tl_portal", CF(0, Y, F.z1 + 3.05), { name = "LotPortal" }).Parent = B.root.LotScenery
	blk("Canopy", -28, 28, 270, 272, F.z1, F.z1 - 22, P.pier2)
	blk("CanopyFascia", -28.5, 28.5, 269.2, 272.6, F.z1 - 22, F.z1 - 23.2, P.trim)
	blk("CanopyUnder", -26, 26, 269.8, 270, F.z1 - 1, F.z1 - 21, P.ceil, { ghost = true })
	for _, x in { -14, 14 } do
		local m = B.put("tv_lightbar", CF(x, 269.8, F.z1 - 12) * CFrame.Angles(0, math.pi / 2, 0), { name = "CanopyLight" })
		if m then m.Parent = B.root.LotScenery end
	end
	sign("WordBackLot", { { "THE BACK LOT", P.amber, "B", 1 } }, 24, 2.8, 0, 270.9, F.z1 - 23.45, V3(0, 0, -9000), { plate = P.board, thick = 0.25 })
	beacon(-25.5, 272.6, F.z1 - 20.5, 90)
	beacon(25.5, 272.6, F.z1 - 20.5, 90)
	-- the apron: a ramp down from the bay's floor, then concrete
	-- the arrival terrace (judge round 2: you came out onto a car park): the apron raised 4, a balcony over the lot, a
	-- slate parapet along its front broken by steps on the axis and a ramp at each end
	local TT = G + 4
	blk("Terrace", -44, 44, 234, TT, F.z1, -8336, C.conc)
	B.ramp("LotShell", "PortalRamp", "z", F.z1 - 6, TT, F.z1, Y, -18, 18, C.conc, { thick = 2 })
	for _, x in { -44, 44 } do nose("TerraceNose", "z", F.z1, -8336, TT - 0.5, x, 1.2) end
	for _, sp in { { -36, -12 }, { 12, 36 } } do
		blk("TerraceParapet", sp[1], sp[2], TT, TT + 3.5, -8334.4, -8336, P.slate)
		nose("TerraceParapetNose", "x", sp[1], sp[2], TT + 3.5, -8335.2, 1.2)
	end
	for k = 1, 4 do
		local z0 = -8336 - (k - 1) * 1.6
		blk("TerraceStep", -12, 12, 234, TT - 0.8 * k, z0, z0 - 1.6, C.conc)
		nose("TerraceStepNose", "x", -12, 12, TT - 0.8 * k - 0.35, z0, 0.7)
	end
	for _, sp in { { -44, -36 }, { 36, 44 } } do
		B.ramp("LotShell", "TerraceRamp", "z", -8352, G, -8336, TT, sp[1], sp[2], C.conc, { thick = 2 })
	end
	-- the exit: a door beside the portal, EXIT over it, down to the basement and out by its far door (basement)
	blk("ExitFloor", exitX0, exitX1, G - 1, G, F.z0, F.z1, P.floor2)
	B.put("tv_frameMid", CF((exitX0 + exitX1) / 2, G, F.z1 - 0.6) * CFrame.Angles(0, math.pi, 0), { name = "ExitFrame" }).Parent = B.root.LotScenery
	sign("WordEXIT", { { "EXIT", P.amber, "B", 1 } }, 7, 1.7, (exitX0 + exitX1) / 2, G + 16.4, F.z1 - 1.2, V3((exitX0 + exitX1) / 2, 0, -9000), { plate = P.board, thick = 0.2 })
	B.lamp((exitX0 + exitX1) / 2, G + 11, F.z1 - 3, "point", 14, 0.6, P.warm)
	basement(TV.BASEMENT)
	-- the board: where everything is, on two posts on the terrace, facing the portal (judge round 3: on the façade it
	-- faced the lot, so whoever read it had its left and right the wrong way round)
	sign("LotBoard", {
		{ "THE BACK LOT", P.amber, "B", 1.2 },
		{ "LONG LANE  ·  RIGHT", P.pale, "B", 0.62 },
		{ "THE BLOCKS  ·  AHEAD", P.pale, "B", 0.62 },
		{ "THE CLIMB  ·  LEFT", P.pale, "B", 0.62 },
		{ "THE HILL  ·  AT THE BACK", P.pale, "B", 0.62 },
	}, 12, 9, -26, 249.6, -8331, V3(-26, 0, -8000), { plate = P.board, thick = 0.3 })
	for _, x in { -30.5, -21.5 } do post(x, -8331.3, G + 4, 245.2) end
end

-- ---------------------------------------------------------------- the ground, the spine, the berms, the near ridge
-- (judge round 1: the playground's towers owned the horizon. one continuous ridge just behind the lot's back berm,
-- its height checked by rays from the lot's eye points to the towers' tops (L.horizon), hides them; the far ball
-- hills are gone)
L.RIDGE = { -- x, z, length (x), height x 2, depth, yaw, colour key: long flattened ellipsoids, their middles at ground level
	{ 0, -8885, 600, 470, 240, 0, "ridgeHi" }, { -250, -8875, 440, 400, 230, 6, "ridgeHi" }, { 250, -8875, 440, 400, 230, -6, "ridgeHi" },
	{ -125, -8880, 360, 300, 220, 0, "ridgeHi" }, { 125, -8880, 360, 300, 220, 0, "ridgeHi" }, -- (saddles, judge round 3)
	{ -140, -8822, 330, 240, 136, 0, "ridge" }, { 70, -8826, 380, 270, 140, 0, "ridge" }, { 250, -8822, 300, 220, 136, 0, "ridge" },
	{ -400, -8700, 240, 300, 300, 55, "ridge" }, { 400, -8700, 240, 300, 300, -55, "ridge" },
	{ -350, -8500, 200, 220, 280, 15, "ridgeHi" }, { 350, -8500, 200, 220, 280, -15, "ridgeHi" },
}
-- the trees (16 Nov, the owner: "the trees look funny outside because they're like glued to the hill, their base isn't
-- on the ground"): each stands upright where rays down at four sides of its trunk (r x its scale out) meet the ground.
-- its base goes `sink` under the lowest of the four, so the downhill side never shows a gap; where the ground rises more
-- than `steep` across the trunk it moves to a flatter spot near by (or is left out), and where it rises more than half a
-- stud a ground-coloured foot hides the seam. L.check holds every tree to it: no side over the ground, none deeper than
-- `deep` under it
L.TREE = { r = 0.8, sink = 0.3, steep = 1.6, deep = 2.3 }
-- the fence's line round the lot (plan x from -x to x, z from z0 to z1; its north side runs by the façade), and how far
-- every tree's box stays clear of it
L.FENCE = { x = 226, z0 = -8746, z1 = -8302, clear = 2.5 }
-- the regular in the basement (the owner's friend): the name over them, their Roblox username, their user id
L.FRIEND = { who = "joxex21", user = "joxex21", id = 194032313 } -- (their display name is their username)
local function treeSides(r) return { V3(r, 0, 0), V3(-r, 0, 0), V3(0, 0, r), V3(0, 0, -r) } end
local function land()
	local F = L.FACE
	ground("Ground", -200, 200, F.z1, -8760, G, C.grass, {})
	local function pad(name, x0, x1, z0, z1, hex) blk(name, x0, x1, G - 0.6, G + 0.06, z0, z1, hex or C.conc) end
	pad("Apron", -44, 44, F.z1, -8352)
	pad("Spine", -176, 176, -8352, -8378, C.conc2)
	for x = -160, 160, 24 do deco("SpineJoint", x - 0.2, x + 0.2, G + 0.06, G + 0.08, -8352, -8378, C.joint) end
	for x = -40, 40, 20 do deco("ApronJoint", x - 0.2, x + 0.2, G + 0.06, G + 0.08, F.z1 - 10, -8352, C.joint) end
	local function roll(x0, z0, x1, z1, dia, cy)
		local a, b = V3(x0, cy, z0), V3(x1, cy, z1)
		part("Berm", CFrame.lookAt((a + b) / 2, b) * CFrame.Angles(0, math.pi / 2, 0), V3((b - a).Magnitude, dia, dia), C.berm, { cyl = true })
	end
	roll(-204, -8250, -204, -8790, 52, 228)   -- west
	roll(204, -8250, 204, -8790, 52, 228)     -- east
	roll(-240, -8754, 240, -8754, 52, 228)    -- south
	roll(-240, -8282, F.x0 - 1, -8282, 52, 228) -- north, beside the hall (it ends at the façade's end)
	roll(93, -8282, 240, -8282, 52, 228)
	roll(-232, -8250, -232, -8620, 80, 222)
	roll(232, -8250, 232, -8620, 80, 222)
	-- (the lumps' and berms' surfaces for the trees: they go into a folder in the place for the rays, then back)
	-- the near ridge
	-- (a lump is the kit's smooth sphere sized as an ellipsoid; Roblox's own sphere mesh showed straight facets against
	-- the sky at this size, judge round 2. without the kit, the old way)
	local ball = lib():FindFirstChild("tl_ball")
	ball = ball and ball:FindFirstChildWhichIsA("MeshPart")
	local function lump(name, cf, size, hex)
		if ball then
			local p = ball:Clone()
			p.Name = name; p.Size = size; p.CFrame = B.at(cf); p.Color = Color3.fromHex(hex); p.Material = SP
			p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
			p.Parent = B.root.LotScenery
			B.count += 1
			return p
		end
		local p = B.part("LotScenery", name, cf, size, hex, { ghost = true })
		local mesh = Instance.new("SpecialMesh"); mesh.MeshType = Enum.MeshType.Sphere; mesh.Parent = p
		return p
	end
	-- (judge round 3: with their middles at ground level the lumps read as bald eggs with steep sides. each is now
	-- 2.5 times taller and 1.4 times longer and deeper, sunk so its crest stays where it was: a hill's cap, wide feet)
	local function sunk(r)
		local h = r[4] / 2
		local s = 2.5 * h
		return CF(r[1], G + h - s, r[2]) * CFrame.Angles(0, RAD(r[6]), 0), V3(r[3] * 1.4, 2 * s, r[5] * 1.4)
	end
	for _, r in L.RIDGE do
		local cf, size = sunk(r)
		lump("NearRidge", cf, size, C[r[7]])
	end
	local function ridgeY(x, z) -- the ridge's surface height over a point (the highest lump there), or nil
		local best
		for _, r in L.RIDGE do
			local c, size = sunk(r)
			local q = c:PointToObjectSpace(V3(x, G, z))
			local u = (q.X / (size.X / 2)) ^ 2 + (q.Z / (size.Z / 2)) ^ 2
			if u < 1 then
				local y = c.Position.Y + size.Y / 2 * math.sqrt(1 - u)
				best = if best then math.max(best, y) else y
			end
		end
		return best
	end
	local rng = Random.new(1116)
	local shapes = {}
	for _, d in B.root:GetDescendants() do
		if d:IsA("BasePart") and (d.Name == "NearRidge" or d.Name == "Berm") then table.insert(shapes, { p = d, parent = d.Parent, q = d.CanQuery }) end
	end
	local probeHome = Instance.new("Folder")
	probeHome.Name = "TreeGround"; probeHome.Parent = workspace
	for _, sh in shapes do sh.p.CanQuery = true; sh.p.Parent = probeHome end
	local rp = RaycastParams.new(); rp.FilterType = Enum.RaycastFilterType.Include; rp.FilterDescendantsInstances = { probeHome }
	local function groundAt(x, z): (number, string)
		local w = B.at(CF(x, 0, z)).Position
		local h = workspace:Raycast(V3(w.X, 700, w.Z), V3(0, -900, 0), rp)
		local y, hex = -math.huge, C.grass
		if h then y, hex = h.Position.Y, h.Instance.Color:ToHex() end
		if math.abs(x) <= 200 and z <= F.z1 and z >= -8760 and G > y then y, hex = G, C.grass end -- (the lot's grass)
		return y, hex
	end
	local function spread(x, z, r): (number, number)
		local lo, hi = math.huge, -math.huge
		for _, o in treeSides(r) do
			local y = groundAt(x + o.X, z + o.Z)
			lo, hi = math.min(lo, y), math.max(hi, y)
		end
		return lo, hi
	end
	local moved, dropped, feet = 0, 0, 0
	local function tree(x, z, _y, s, kind)
		local round = if kind then kind == "round" else rng:NextNumber() < 0.55
		local yaw = rng:NextNumber() * 6.28
		local scale = s or (1.1 + rng:NextNumber() * 0.9)
		local r = L.TREE.r * scale
		local lo, hi = spread(x, z, r)
		if hi - lo > L.TREE.steep or lo == -math.huge then -- too steep here: the nearest flatter spot within 12
			local found = false
			for _, d in { 3, 6, 9, 12 } do
				for k = 0, 7 do
					local a = k * math.pi / 4
					local nx, nz = x + d * math.cos(a), z + d * math.sin(a)
					local l2, h2 = spread(nx, nz, r)
					if l2 > -math.huge and h2 - l2 <= L.TREE.steep then x, z, lo, hi, found = nx, nz, l2, h2, true; break end
				end
				if found then break end
			end
			if not found then dropped += 1; return end
			moved += 1
		end
		local m = B.put(if round then "tl_treeRound" else "tl_treeCone", CF(x, lo - L.TREE.sink, z) * CFrame.Angles(0, yaw, 0), { name = "Tree", scale = scale })
		if m then m.Parent = B.root.LotScenery end
		if hi - lo > 0.5 then
			local _, hex = groundAt(x, z)
			lump("TreeFoot", CF(x, lo + (hi - lo) * 0.3, z), V3(r * 4.6, (hi - lo) + 1, r * 4.6), hex)
			feet += 1
		end
	end
	-- the treeline (16 Nov, the owner: "the trees were sort of just spammed", then "can you unclump the trees outside also
	-- dont let them be within the gate line!"): every tree stands outside the fence, its whole box (crown and all) at
	-- least L.FENCE.clear clear of it, in bands on the berms beyond it: west, east, north, and the south where the
	-- ridge's foot lets a tree stand. along a band each tree goes its own crown plus the last one's plus a varied gap on,
	-- set off the line a little, so no two crowns meet and no trunks stack; short runs of one kind (round trees and
	-- pines). a spot too steep to stand on is passed by, not shifted, so the gaps and the fence's clearance always
	-- hold. L.check holds every tree to all of it
	local placed = {}
	local function crown(kind, sc) return (if kind == "round" then 6 else 5) * sc end
	local function outside(x, z, hx, hz)
		local F = L.FENCE
		return x + hx < -F.x or x - hx > F.x or z + hz < F.z0 or z - hz > F.z1
	end
	local function plant(x, z, kind, sc): boolean
		local r = crown(kind, sc)
		local yaw = rng:NextNumber() * 6.28
		local est = r * (math.abs(math.cos(yaw)) + math.abs(math.sin(yaw))) + L.FENCE.clear
		if not outside(x, z, est, est) then return false end
		for _, t in placed do
			if math.sqrt((t.x - x) ^ 2 + (t.z - z) ^ 2) < t.r + r + 1.5 then return false end
		end
		local lo, hi = spread(x, z, L.TREE.r * sc)
		if lo == -math.huge or hi - lo > math.max(L.TREE.steep, 1.12 * sc) then dropped += 1; return false end -- (a big trunk stands on more slope)
		local m = B.put(if kind == "round" then "tl_treeRound" else "tl_treeCone", CF(x, lo - L.TREE.sink, z) * CFrame.Angles(0, yaw, 0), { name = "Tree", scale = sc })
		if not m then return false end
		-- (the real box: if it reaches the fence after all, no tree)
		local bcf, bsz = m:GetBoundingBox()
		local hx = math.abs(bcf.RightVector.X) * bsz.X / 2 + math.abs(bcf.UpVector.X) * bsz.Y / 2 + math.abs(bcf.LookVector.X) * bsz.Z / 2
		local hz = math.abs(bcf.RightVector.Z) * bsz.X / 2 + math.abs(bcf.UpVector.Z) * bsz.Y / 2 + math.abs(bcf.LookVector.Z) * bsz.Z / 2
		local at = bcf.Position - B.at(CFrame.identity).Position
		if not outside(at.X, at.Z, hx + L.FENCE.clear, hz + L.FENCE.clear) then m:Destroy(); return false end
		m.Parent = B.root.LotScenery
		if hi - lo > 0.5 then
			local _, hex = groundAt(x, z)
			lump("TreeFoot", CF(x, lo + (hi - lo) * 0.3, z), V3(L.TREE.r * sc * 4.6, (hi - lo) + 1, L.TREE.r * sc * 4.6), hex)
			feet += 1
		end
		table.insert(placed, { x = x, z = z, r = r })
		return true
	end
	-- a band from (ax, az) to (bx, bz): trees one after another along it, each set off the line by up to `side` (to its
	-- left as you walk it: negative for the other side), runs of 2 to 5 of one kind
	local function band(ax, az, bx, bz, side0, side1, kinds, s0, s1)
		local p0, p1 = Vector2.new(ax, az), Vector2.new(bx, bz)
		local len = (p1 - p0).Magnitude
		local dir = (p1 - p0).Unit
		local nrm = Vector2.new(-dir.Y, dir.X)
		local dist, lastR = 0, 0
		local kind, left = kinds[1], 0
		while true do
			if left <= 0 then kind = kinds[rng:NextInteger(1, #kinds)]; left = rng:NextInteger(2, 5) end
			local sc = s0 + rng:NextNumber() * (s1 - s0)
			local r = crown(kind, sc)
			dist += lastR + r + 2 + rng:NextNumber() * 5
			if dist >= len then break end
			local q = p0 + dir * dist + nrm * (side0 + rng:NextNumber() * (side1 - side0))
			if plant(q.X, q.Y, kind, sc) then lastR = r; left -= 1 else lastR = r * 0.4 end
		end
	end
	-- west and east: on the outer berms' near slope, round trees and pines in runs
	-- (big: from the lot's floor they must show over the 16-high fence in front of them)
	band(-250, -8292, -250, -8616, -1.5, 1.5, { "round", "cone" }, 1.7, 2.3)
	band(250, -8292, 250, -8616, -1.5, 1.5, { "cone", "round" }, 1.7, 2.3)
	-- the corners and the south: pines on the south berm's back, where the ridge's foot is not too steep
	band(-252, -8640, -252, -8790, -2, 2, { "cone" }, 1.6, 2.2)
	band(252, -8640, 252, -8790, -2, 2, { "cone" }, 1.6, 2.2)
	band(-236, -8772, 236, -8772, -3, 3, { "cone", "round" }, 1.6, 2.2)
	-- north, either side of the hall: round trees on the north berms' crest
	band(-240, -8283, L.FACE.x0 - 4, -8283, -2, 2, { "round" }, 1.4, 1.9)
	band(L.FACE.x1 + 4, -8283, 240, -8283, -2, 2, { "round" }, 1.4, 1.9)
	-- (the far ridge's row of plain dark crowns along its crest is gone: owner, 17 Nov, "can you get rid of the little
	-- dark green lumps on the hills?": the hills are smooth)
	-- the fence round the lot (16 Nov, the owner: "can you add a fence line in the outside section of the training, like
	-- where the trees are, so you can't see the ugly parts of it?"): on the berms' outer slopes just behind the round
	-- trees, closing on the façade's two ends. slate posts every 12 with pale caps, solid panels 16 high (a darker band
	-- at the foot, a framed inset, a pale rail on top), each panel's foot on the ground at its posts (rays, as for the
	-- trees). the groves and the hills show over it; what lies beyond it under the eye line does not. an unseen wall up
	-- to 600 along it keeps everyone in (L.check's ring test). (owner, 17 Nov: "can you raise the wall on the left side so
	-- its complete wall all at the same height": its top is one height all the way round, FH over the highest ground any
	-- post stands on; each panel reaches down to the ground at its own posts)
	local FH, STEP = 16, 12
	local fenceParts = 0
	local function postsOf(x0, z0, x1, z1)
		local a, e = V3(x0, 0, z0), V3(x1, 0, z1)
		local n = math.max(1, math.round((e - a).Magnitude / STEP))
		local out = {}
		for i = 0, n do
			local q = a + (e - a) * (i / n)
			local gy = groundAt(q.X, q.Z)
			if gy == -math.huge then gy = G end
			table.insert(out, { q = q, gy = gy })
		end
		return out
	end
	local FTOP = -math.huge -- (set below, from every run's posts)
	local function fenceRun(x0, z0, x1, z1)
		local a, e = V3(x0, 0, z0), V3(x1, 0, z1)
		local len = (e - a).Magnitude
		local dir = (e - a).Unit
		local rot = CFrame.Angles(0, math.atan2(-dir.X, -dir.Z), 0) -- (its -Z runs along the line)
		local prevQ, prevY = nil, nil
		for _, pt in postsOf(x0, z0, x1, z1) do
			local q, gy = pt.q, pt.gy
			part("FencePost", CF(q.X, (gy - 1 + FTOP + 0.6) / 2, q.Z) * rot, V3(1.4, FTOP + 0.6 - (gy - 1), 1.4), "5c6168")
			part("FencePostCap", CF(q.X, FTOP + 0.75, q.Z) * rot, V3(1.75, 0.4, 1.75), P.trim)
			fenceParts += 2
			if prevQ then
				local mid = (prevQ + q) / 2
				local seg = (q - prevQ).Magnitude - 1.2
				local avg = (prevY + gy) / 2
				local base = math.min(prevY, gy) - 1.5
				local top = FTOP
				local F = CF(mid.X, 0, mid.Z) * rot
				part("FencePanel", F * CF(0, (base + top) / 2, 0), V3(0.6, top - base, seg), "6c727b")
				part("FenceBand", F * CF(0, (base + avg + 2.5) / 2, 0), V3(0.7, avg + 2.5 - base, seg - 0.1), "5a5f69")
				part("FenceInset", F * CF(0, (avg + 3.3 + top - 1.2) / 2, 0), V3(0.7, top - 1.2 - avg - 3.3, seg - 2.4), "767b84")
				part("FenceRail", F * CF(0, top + 0.15, 0), V3(0.9, 0.4, seg + 0.2), P.trim)
				fenceParts += 4
			end
			prevQ, prevY = q, gy
		end
		B.solid("LotFenceWall", CF((x0 + x1) / 2, 480, (z0 + z1) / 2) * rot, V3(4, 560, len + 4)) -- (to 760: the ring test's long rays)
	end
	-- (the south side runs in front of the near ridge's foot and just behind the long lane's backstop: further out, the
	-- ridge's face rises straight from the berm)
	local FX, FZ0, FZ1 = L.FENCE.x, L.FENCE.z0, L.FENCE.z1
	local RUNS = { { -FX, FZ1, -FX, FZ0 }, { -FX, FZ0, FX, FZ0 }, { FX, FZ0, FX, FZ1 }, { -FX, FZ1, L.FACE.x0, FZ1 }, { L.FACE.x1, FZ1, FX, FZ1 } }
	for _, r in RUNS do for _, pt in postsOf(r[1], r[2], r[3], r[4]) do FTOP = math.max(FTOP, pt.gy + FH) end end
	B.fenceTop = FTOP
	fenceRun(-FX, FZ1, -FX, FZ0)
	fenceRun(-FX, FZ0, FX, FZ0)
	fenceRun(FX, FZ0, FX, FZ1)
	fenceRun(-FX, FZ1, L.FACE.x0, FZ1)
	fenceRun(L.FACE.x1, FZ1, FX, FZ1)
	-- (and over the façade: the lot is closed in on every side)
	B.solid("LotFaceWall", CF((L.FACE.x0 + L.FACE.x1) / 2, (L.FACE.top + 760) / 2, FZ1), V3(L.FACE.x1 - L.FACE.x0 + 4, 760 - L.FACE.top, 4))
	for _, sh in shapes do sh.p.Parent = sh.parent; sh.p.CanQuery = sh.q end
	probeHome:Destroy()
	B.treeNote = ("trees: %d moved to flatter ground, %d left out, %d feet; fence %d parts"):format(moved, dropped, feet, fenceParts)
end

-- ---------------------------------------------------------------- the long lane (east): a roofed firing line, four rows
-- (judge round 2: an 80-wide road lined with bollards. now walls 6 high both sides, three slate baffle frames across
-- it, stations as gates, a 30-high slate backstop)
local LANE = { x0 = 96, x1 = 176, z = -8402 }
local ROWS = { { 25, -8477, 241.2, { 104, 128, 152 } }, { 50, -8552, 242.6, { 114, 138, 162 } },
	{ 75, -8627, 244.2, { 108, 132, 156 } }, { 100, -8702, 246.2, { 118, 142, 166 } } }
local function longLane()
	local X0, X1, Z = LANE.x0, LANE.x1, LANE.z
	blk("LaneGround", X0, X1, G - 0.6, G + 0.06, Z, -8708, C.lane)
	for _, x in { 124, 148 } do deco("LaneLine", x - 0.3, x + 0.3, G + 0.06, G + 0.09, Z - 2, -8704, C.laneLine) end
	for _, w in { { X0 - 2, X0 }, { X1, X1 + 2 } } do
		blk("LaneWall", w[1], w[2], G, G + 6, Z, -8708, C.conc)
		nose("LaneWallNose", "z", Z, -8708, G + 6, (w[1] + w[2]) / 2, 1.6)
	end
	blk("ShelterDeck", X0, X1, G - 0.6, G + 1, -8380, Z, C.conc)
	nose("ShelterDeckNose", "x", X0, X1, G + 0.5, Z, 1)
	blk("ShelterBack", X0 - 2, X1 + 2, G, 256.95, -8378, -8380, P.wall)
	blk("ShelterRoof", X0 - 2, X1 + 2, 255, 257, -8378, Z - 3, P.slate)
	blk("ShelterFascia", X0 - 2.4, X1 + 2.4, 254.2, 257.6, Z - 3, Z - 4.2, P.trim)
	local PX = { X0, (X0 * 2 + X1) / 3, (X0 + X1 * 2) / 3, X1 }
	for _, x in PX do
		blk("ShelterPier", x - 1.6, x + 1.6, G + 1, 255, Z - 0.6, Z - 3.8, P.pier)
		blk("ShelterBeam", x - 1, x + 1, 253, 255, -8380, Z - 3, P.slate)
	end
	for _, cx in { 112, 136, 160 } do
		blk("Counter", cx - 9, cx + 9, G + 1, G + 4.2, Z + 1.6, Z, P.pier2)
		blk("CounterTop", cx - 9.3, cx + 9.3, G + 4.2, G + 4.6, Z + 1.9, Z - 0.3, P.trim)
		local m = B.put("tv_lightbar", CF(cx, 255, -8391) * CFrame.Angles(0, math.pi / 2, 0), { name = "ShelterLight" })
		if m then m.Parent = B.root.LotScenery end
		B.lamp(cx, 253, -8391, "point", 16, 0.5, P.lampWhite)
	end
	sign("WordLongLane", { { "LONG LANE", P.amber, "B", 1 } }, 16, 2.4, 136, 252, -8377.6, V3(136, 0, -8000), { plate = P.board, thick = 0.25 })
	-- the rows: a plinth a step higher each time (slate noses: the white ones read as parking kerbs), three Carls on it,
	-- each between two gate posts 2.4 square and 6 high, the distance on a post at the lane's edge
	for _, r in ROWS do
		local m, z, top, xs = r[1], r[2], r[3], r[4]
		blk("RowPlinth", X0, X1, G - 0.6, top, z + 2, z - 3, C.conc)
		part("RowNose", CF((X0 + X1) / 2, top - 0.45, z + 2), V3(X1 - X0, 0.9, 0.9), P.slate, { cyl = true })
		for _, x in xs do
			target(x, top, z, V3(x, top, Z))
			for _, sx in { -1, 1 } do
				blk("StationPost", x + sx * 3.8 - 1.2, x + sx * 3.8 + 1.2, top, top + 4.8, z - 1.2, z + 1.2, P.slate)
				blk("StationPostCap", x + sx * 3.8 - 1.3, x + sx * 3.8 + 1.3, top + 4.8, top + 5.4, z - 1.3, z + 1.3, P.amber)
			end
		end
		post(X0 + 3, z + 4, G, 251)
		sign("RowSign", { { tostring(m), P.amber, "B", 1 }, { "METRES", P.pale, "S", 0.34 } }, 4.4, 4.4, X0 + 3, 252, z + 5.4, V3(X0 + 3, 0, -8000), { plate = P.board, thick = 0.25 })
	end
	-- three baffle frames across the lane between the rows: legs at its edges, a lintel 22 up (every line from a shooter
	-- to a Carl stays under about G+12)
	for _, z in { -8440, -8515, -8590 } do
		blk("BaffleLeg", X0 - 4, X0 + 0.05, G, G + 22, z - 2, z + 2, P.pier)
		blk("BaffleLeg", X1 - 0.05, X1 + 4, G, G + 22, z - 2, z + 2, P.pier)
		blk("BaffleLintel", X0 - 6, X1 + 6, G + 22, G + 26, z - 3, z + 3, P.pier)
		nose("BaffleNose", "x", X0 - 6, X1 + 6, G + 22, z + 3, 1)
	end
	-- the backstop: a slate face 30 high, a pale coping, a lit amber strip at its foot
	blk("Backstop", X0 - 10, X1 + 10, 234, G + 30, -8708, -8712, P.pier)
	-- (judge round 3: the backstop's top sat just under the last baffle, so the lane ended on a panel in a frame. its
	-- middle 40 rises to G+42 as a crown with the cardboard man on it, 24 high)
	nose("BackstopCoping", "x", X0 - 10, 116, G + 30, -8708, 1.4)
	nose("BackstopCoping", "x", 156, X1 + 10, G + 30, -8708, 1.4)
	blk("BackstopCrown", 116, 156, G + 30, G + 42, -8708, -8712, P.pier)
	blk("BackstopCrownFill", 116, 156, G + 30, G + 42, -8712, -8742, P.pier2)
	nose("BackstopCrownCoping", "x", 116, 156, G + 42, -8708, 1.4)
	deco("BackstopStrip", X0, X1, G, G + 0.5, -8707.6, -8707.9, P.amberGlow, { mat = NEON })
	blk("BackstopFill", X0 - 10, X1 + 10, 234, G + 30, -8712, -8742, P.pier2)
	-- (the big cardboard man painted on it went on 16 Nov, the owner: "I dont like this". the rows of Carls are the
	-- lane's targets; the backstop is a plain wall under its crown)
end

-- ---------------------------------------------------------------- the blocks (middle): a container yard with a second level
-- (judge round 1: a car park; round 2: the house hid the watchtower from the axis. now the house group stands 38 to
-- the west, its catwalk runs north to a container tower, a container gateway opens the yard on the axis, and the axis
-- itself is an open alley to the hill with one amber container in it)
local function container(x, z, yaw, hex, y)
	y = y or G
	prop("tl_container", x, y, z, yaw, V3(20.2, 8.6, 8.2), { color = { a0a8b2 = hex }, name = "Container" })
end
local function stack(x, z, yaw, n, hexes)
	for k = 0, n - 1 do container(x, z, yaw, hexes[(k % #hexes) + 1], G + 8.6 * k) end
end
local function barrier(x, z, yaw, y) prop("tl_barrier", x, y or G, z, yaw, V3(10, 3.6, 2.6)) end
L.HOUSE = { x0 = -46, x1 = -14, z0 = -8466, z1 = -8494 } -- (the house group, 38 west of where it stood in push 7)
local function theBlocks()
	local X0, X1, Z0, Z1 = -62, 84, -8386, -8598
	blk("BlocksPad", X0, X1, G - 0.6, G + 0.05, Z0, Z1, C.conc)
	for x = -50, 80, 24 do deco("BlocksJoint", x - 0.2, x + 0.2, G + 0.05, G + 0.07, Z0, Z1, C.joint) end
	for z = -8410, -8590, -24 do deco("BlocksJoint", X0, X1, G + 0.05, G + 0.07, z - 0.2, z + 0.2, C.joint) end
	-- the kerb wall: the gateway on the axis (between the two gate stacks), a gap in the south for the hill's ramp
	local KH = G + 3.5
	for _, s in { { -59, -46 }, { 46, 59 }, { 62, 81 } } do blk("YardKerb", s[1], s[2], G, KH, Z0, Z0 - 1.6, P.slate) end
	for _, s in { { -59, -32 }, { 55, 81 } } do blk("YardKerb", s[1], s[2], G, KH, Z1 + 1.6, Z1, P.slate) end -- (the middle is the hill's bank)
	for z = Z0, Z1 + 1, -30 do
		local a, b = z - 3, math.max(z - 27, Z1)
		if a > b then
			blk("YardKerb", X0, X0 + 1.6, G, KH, a, b, P.slate)
			blk("YardKerb", X1 - 1.6, X1, G, KH, a, b, P.slate)
		end
	end
	-- the gateway: a 2-high container stack either side, the yard's name on the west one
	stack(-34, -8392, 0, 3, { C.slateC, C.warmC, C.slateC })
	stack(34, -8392, 0, 3, { C.warmC, C.slateC, C.warmC })
	sign("WordBlocks", { { "THE BLOCKS", P.amber, "B", 1 } }, 12, 2.2, -34, 249.6, -8387.6, V3(-34, 0, -8000), { plate = P.board, thick = 0.25 })
	-- the raised pad under the house group: 4 up, rounded edges, a ramp at each end
	local H = L.HOUSE
	local RX0, RX1, RZ0, RZ1, RT = H.x0 - 14, H.x1 + 14, -8440, -8520, G + 4
	blk("RaisedPad", RX0, RX1, 234, RT, RZ0, RZ1, C.conc2)
	nose("RaisedPadNose", "x", RX0, RX1, RT - 0.5, RZ0, 1.2); nose("RaisedPadNose", "x", RX0, RX1, RT - 0.5, RZ1, 1.2)
	nose("RaisedPadNose", "z", RZ0, RZ1, RT - 0.5, RX0, 1.2); nose("RaisedPadNose", "z", RZ0, RZ1, RT - 0.5, RX1, 1.2)
	B.ramp("LotShell", "RaisedPadRamp", "z", RZ0 + 12, G, RZ0, RT, RX1 - 16, RX1 - 4, C.conc2, { thick = 2 })
	B.ramp("LotShell", "RaisedPadRamp", "z", RZ1 - 12, G, RZ1, RT, RX1 - 16, RX1 - 4, C.conc2, { thick = 2 })
	-- the container walls: the 3-high tower the catwalk reaches, 2-high walls on the east, one amber on the axis
	stack(-30, -8420, 90, 3, { C.slateC, C.warmC, C.slateC })
	stack(50, -8440, 90, 2, { C.warmC, C.slateC })
	stack(50, -8510, 90, 2, { C.slateC, C.warmC })
	-- (judge round 3: the east half was bare paving. a 2-high container wall down the east edge in two runs, the gap
	-- between them the way through, a container bridge from the wall to the stack at (50, -8510))
	for _, z in { -8428, -8449, -8510, -8531, -8575 } do stack(76, z, 90, 2, if z % 2 == 0 then { C.warmC, C.slateC } else { C.slateC, C.warmC }) end
	container(63, -8510, 0, C.warmC, G + 17.2)
	for _, z in { -8506.4, -8513.6 } do -- (on the container's long edges; the pad lands over the north one)
		blk("BridgeParapet", 54, 72, G + 25.8, G + 29.3, z - 0.5, z + 0.5, P.slate)
		blk("BridgeCoping", 54, 72, G + 29.3, G + 29.7, z - 0.7, z + 0.7, P.trim)
	end
	B.pad(63, G, -8496, V3(0, 76, -10))
	stack(-50, -8566, 90, 2, { C.slateC, C.warmC })
	container(8, -8566, 0, C.amberC)
	container(-26, -8584, 0, C.warmC)
	-- the house: three storeys on the raised pad, an open roof behind a parapet
	local HX0, HX1, HZ0, HZ1 = H.x0, H.x1, H.z0, H.z1
	local W, F1, F2, F3, PT = 1.5, RT + 12, RT + 24, RT + 36, RT + 39.5
	local function walls(y0, y1, holesN, holesS, holesW, holesE)
		wallX("HouseWall", HX0, HX1, y0, y1, HZ0, HZ0 - W, C.house, holesN)
		wallX("HouseWall", HX0, HX1, y0, y1, HZ1 + W, HZ1, C.house, holesS)
		wallZ("HouseWall", HZ1 + W, HZ0 - W, y0, y1, HX0, HX0 + W, C.house, holesW)
		wallZ("HouseWall", HZ1 + W, HZ0 - W, y0, y1, HX1 - W, HX1, C.house, holesE)
	end
	local function X(dx) return HX0 + dx end -- (window positions from the house's west end)
	walls(RT, F1 - 1, { { X(10), X(18), RT, RT + 9 }, { X(3.5), X(7.5), RT + 3.5, RT + 7.5 }, { X(22), X(28), RT + 3.5, RT + 7.5 } },
		{ { X(20), X(28), RT, RT + 9 }, { X(5), X(11), RT + 3.5, RT + 7.5 } }, { { -8474, -8486, RT + 3.5, RT + 7.5 } }, { { -8474, -8482, RT, RT + 9 } })
	walls(F1, F2 - 1, { { X(4), X(10), F1 + 3, F1 + 7.5 }, { X(18), X(28), F1 + 3, F1 + 7.5 } }, { { X(6), X(16), F1 + 3, F1 + 7.5 }, { X(22), X(28), F1 + 3, F1 + 7.5 } },
		{ { -8472, -8488, F1 + 3, F1 + 7.5 } }, { { -8486, -8492.5, F1, F1 + 8.5 }, { -8470, -8478, F1 + 3, F1 + 7.5 } })
	walls(F2, F3 - 1, { { -33, -27, F2, F2 + 8 }, { X(3), X(9), F2 + 3, F2 + 7.5 } }, { { X(6), X(14), F2 + 3, F2 + 7.5 }, { X(20), X(28), F2 + 3, F2 + 7.5 } },
		{ { -8474, -8486, F2 + 3, F2 + 7.5 } }, { { -8472, -8488, F2 + 3, F2 + 7.5 } })
	walls(F3, PT, {}, {}, {}, {})
	blk("HouseFloor", HX0, HX1, F1 - 1, F1, HZ0, HZ1, C.house2)
	blk("HouseFloor", HX0 + W + 6, HX1, F2 - 1, F2, HZ0, HZ1, C.house2)
	blk("HouseFloor", HX0, HX1 - W - 6, F3 - 1, F3, HZ0, HZ1, C.house2)
	B.ramp("LotShell", "HouseInnerStair", "z", -8490, F1, -8468.5, F2, HX0 + W, HX0 + W + 6, C.house2, { thick = 1.2 })
	B.ramp("LotShell", "HouseInnerStair", "z", -8468.5, F2, -8490, F3, HX1 - W - 6, HX1 - W, C.house2, { thick = 1.2 })
	for _, y in { F1, F2, F3 } do blk("HouseFloorEdge", HX0 - 0.3, HX1 + 0.3, y - 1.4, y - 0.6, HZ0 + 0.3, HZ1 - 0.3, P.slate) end
	for _, e in { { HX0 - 0.3, HX1 + 0.3, HZ0 + 0.3, HZ0 - W - 0.3 }, { HX0 - 0.3, HX1 + 0.3, HZ1 + W + 0.3, HZ1 - 0.3 } } do
		blk("HouseCoping", e[1], e[2], PT, PT + 0.7, e[3], e[4], P.trim)
	end
	blk("HouseCoping", HX0 - 0.3, HX0 + W + 0.3, PT, PT + 0.7, HZ0 - W, HZ1 + W, P.trim)
	blk("HouseCoping", HX1 - W - 0.3, HX1 + 0.3, PT, PT + 0.7, HZ0 - W, HZ1 + W, P.trim)
	blk("HouseBase", HX0 - 0.2, HX1 + 0.2, RT, RT + 1, HZ0 + 0.2, HZ1 - 0.2, P.slate, { nq = true })
	-- the stair up its east side to the first floor, a parapet following its slope (not a billboard wall)
	B.ramp("LotShell", "HouseStair", "z", -8458, RT + 0.05, -8486, F1, HX1 + 1, HX1 + 7, C.house2, { thick = 1.4 })
	blk("HouseLanding", HX1, HX1 + 7, F1 - 1, F1, -8486, -8493, C.house2)
	B.ramp("LotShell", "HouseStairParapet", "z", -8458, RT + 3.5, -8486, F1 + 3.5, HX1 + 7, HX1 + 8, C.house, { thick = 3.5 })
	blk("HouseLandingParapet", HX1 + 7, HX1 + 8, F1, F1 + 3.5, -8486, -8493, C.house)
	-- the catwalk: north from the third storey's door to the top of the container tower, parapets with a pale coping,
	-- one slate pier at mid-span
	local towerTop = G + 8.6 * 3
	B.ramp("LotShell", "Catwalk", "z", HZ0, F2, -8430, towerTop, -33, -27, P.slate, { thick = 1.2 })
	for _, x in { -34, -27 } do
		B.ramp("LotShell", "CatwalkParapet", "z", HZ0, F2 + 3.5, -8430, towerTop + 3.5, x, x + 1, P.slate, { thick = 3.5 })
		B.ramp("LotShell", "CatwalkCoping", "z", HZ0, F2 + 3.9, -8430, towerTop + 3.9, x - 0.2, x + 1.2, P.trim, { thick = 0.4 })
	end
	blk("CatwalkPier", -32, -28, RT, (F2 + towerTop) / 2 - 1.4, -8450, -8446, P.slate)
	-- barriers in two clusters of three, at chest height against container walls (the small props are gone: noise)
	for _, z in { -8424, -8434.4, -8444.8 } do barrier(70, z, 90) end
	for _, z in { -8503, -8513.4, -8523.8 } do barrier(43.5, z, 90) end
	-- the Carls in the blocks: in the alleys, upstairs, on the catwalk and the tower
	local IN = V3(8, G, -8350)
	for _, k in { { 20, G, -8452 }, { -23, F1, -8471 }, { -36, F2, -8490 }, { -30, (F2 + towerTop) / 2, -8448 }, { -30, towerTop, -8418 },
		{ 60, G, -8470 }, { -32, G, -8574 }, { -8, RT, -8510 }, { 63, G + 25.8, -8510 } } do
		target(k[1], k[2], k[3], IN)
	end
end

-- ---------------------------------------------------------------- the climb (west): one built course on one slate base
-- (judge round 2: one long dark wall. now the slide is an off-white ramp between low parapets, every stage has its
-- number on the plinth's face, and the finish tower is 64 high with a pale top over its lit band)
local CX, CW = -120, 12 -- the course's middle line and half its width
local function slab(name, x0, x1, z0, z1, y0, top, wall, noPiers)
	blk(name, x0, x1, y0, top - 1, z0, z1, wall or P.pier2)
	blk(name .. "Top", x0, x1, top - 1, top, z0, z1, P.mass)
	nose(name .. "Nose", "x", x0, x1, top - 0.5, z0, 1.1); nose(name .. "Nose", "x", x0, x1, top - 0.5, z1, 1.1)
	nose(name .. "Nose", "z", z0, z1, top - 0.5, x0, 1.1); nose(name .. "Nose", "z", z0, z1, top - 0.5, x1, 1.1)
	if noPiers then return end -- (judge round 4: on the pale deck and summit they read as window slits)
	local lo, hi = math.min(x0, x1), math.max(x0, x1)
	local zn, zs = math.max(z0, z1), math.min(z0, z1)
	for z = zs + 6, zn - 4, 8 do
		blk(name .. "Pier", lo - 0.4, lo, y0 + 2, top - 1.6, z - 0.7, z + 0.7, P.slate)
		blk(name .. "Pier", hi, hi + 0.4, y0 + 2, top - 1.6, z - 0.7, z + 0.7, P.slate)
	end
end
local function theClimb()
	local X0, X1 = CX - CW, CX + CW
	local PL = G + 8
	-- the start (judge round 3: a stick and a disc on a thin mat, 12 short of the course): a rubber mat 1 up, from the
	-- spine to the plinth, a rounded nose on its front, the pad set into it, the course's name on the plinth's face
	blk("ClimbPad", CX - 14, CX + 14, G - 0.6, G + 1, -8380, -8404, C.rubber)
	part("ClimbPadLip", CF(CX, G + 0.5, -8379) * CFrame.Angles(0, math.pi, 0), V3(28, 1, 2), C.rubber, { wedge = true }) -- (round 4: the rolled nose read as a towel)
	sign("WordClimb", { { "THE CLIMB", P.amber, "B", 1 } }, 12, 2.4, CX, G + 4.6, -8403.75, V3(CX, 0, -8000), { plate = P.board, thick = 0.3 })
	slab("ClimbPlinth", X0, X1, -8404, -8500, 234, PL)
	slab("ClimbPlinth", X0, X1, -8512, -8616, 234, PL)
	-- 1: a pad throws you onto the deck
	B.pad(CX, G + 1, -8394, V3(0, 64, -21))
	slab("Deck", X0, X1, -8410, -8440, PL, 262, C.house2, true)
	-- 2: the slide: an off-white ramp (its sides too) with low slate parapets riding its edges, slate piers on its sides
	part("SlideRamp", CF(CX, (PL + 262) / 2, -8470), V3(16, 262 - PL, 60), P.mass, { wedge = true })
	for _, sx in { -1, 1 } do
		local a, b = CX + sx * 6.5, CX + sx * 8
		B.ramp("LotShell", "SlideParapet", "z", -8500, PL + 1.5, -8440, 262 + 1.5, math.min(a, b), math.max(a, b), P.mass, { thick = 1.5 })
		for _, z in { -8456, -8472, -8488 } do
			local h = PL + (262 - PL) * (z + 8500) / 60
			blk("SlidePier", CX + sx * 8, CX + sx * 8.5, PL, h - 0.6, z - 0.8, z + 0.8, P.slate)
		end
	end
	-- 3: the gap: a cut 12 long and 10 deep, steps up out of its east end
	blk("GapFloor", X0, X1, 234, PL - 10, -8500, -8512, P.floor2)
	for k = 1, 4 do
		local z0 = -8500 - (k - 1) * 3
		blk("GapStep", X1 - 4, X1, PL - 10, PL - 10 + 2.5 * k, z0, z0 - 3, P.slate)
	end
	-- 4: stepping drums, zig-zag, each 4 higher, to the summit
	for _, d in { { CX - 4, -8548, PL + 4 }, { CX + 4, -8560, PL + 8 }, { CX - 4, -8572, PL + 12 }, { CX + 4, -8584, PL + 16 } } do
		B.drum("LotShell", "StepDrum", d[1], d[2], PL, d[3] - 0.8, 8, P.pier2)
		B.drum("LotShell", "StepDrumTop", d[1], d[2], d[3] - 0.8, d[3], 8.4, P.mass)
	end
	slab("Summit", X0, X1, -8592, -8616, PL, PL + 20, C.house2, true)
	-- 5: the canyon: two slate walls 18 high, a way out through the east one; two masts with lit heads
	blk("CanyonWall", X0 - 2, X0, 234, G + 18, -8616, -8676, P.pier2)
	wallZ("CanyonWall", -8676, -8616, 234, G + 18, X1, X1 + 2, P.pier2, { { -8648, -8640, G + 0.05, G + 8 } })
	for _, x in { X0 - 1, X1 + 1 } do nose("CanyonWallNose", "z", -8616, -8676, G + 18, x, 1.2) end
	-- (judge round 3: on the tower's line their amber faces read as eyes on the finish tower. off the line, faces east
	-- and west)
	for _, m in { { CX - 5, -8634 }, { CX + 5, -8660 } } do
		local mx, z = m[1], m[2]
		blk("Mast", mx - 1.25, mx + 1.25, G, 282, z - 1.25, z + 1.25, P.slate)
		local hd = part("MastHead", CF(mx, 284, z), V3(4, 4.4, 4.4), P.slate, { cyl = true })
		hd.CanQuery = true; hd.CanCollide = true
		for _, sx in { -1, 1 } do
			part("MastFace", CF(mx + sx * 2.05, 284, z), V3(0.2, 3.2, 3.2), P.amber, { cyl = true, ghost = true, mat = SP })
		end
	end
	-- 6: the finish tower: 64 high, rounded corners, a lit band with the pale top over it, a flag. (its strong pad at the
	-- foot is gone: owner, 17 Nov, "remove this ... bounce pad": the climb itself is the way up)
	local TX0, TX1, TZ0, TZ1, TT = CX - 8, CX + 8, -8676, -8692, G + 64
	for _, band in { { 234, TT - 13, P.pier2 }, { TT - 12, TT - 1, P.mass } } do
		blk("FinishTower", TX0 + 1.5, TX1 - 1.5, band[1], band[2], TZ0, TZ1, band[3])
		blk("FinishTower", TX0, TX1, band[1], band[2], TZ0 - 1.5, TZ1 + 1.5, band[3])
		for _, cx in { TX0 + 1.5, TX1 - 1.5 } do for _, cz in { TZ0 - 1.5, TZ1 + 1.5 } do B.drum("LotShell", "FinishTowerCorner", cx, cz, band[1], band[2], 3, band[3]) end end
	end
	blk("FinishBand", TX0 + 1.6, TX1 - 1.6, TT - 13, TT - 12, TZ0 + 0.15, TZ1 - 0.15, P.amberGlow, { mat = NEON })
	blk("FinishBand", TX0 - 0.15, TX1 + 0.15, TT - 13, TT - 12, TZ0 - 1.6, TZ1 + 1.6, P.amberGlow, { mat = NEON })
	blk("FinishCap", TX0 - 1, TX1 + 1, TT - 1, TT + 0.6, TZ0 + 1, TZ1 - 1, P.mass)
	part("FinishFlagPole", CF(CX + 5, TT + 5.6, TZ1 + 4) * CFrame.Angles(0, 0, math.pi / 2), V3(10, 0.7, 0.7), P.pier, { cyl = true })
	part("FinishFlag", CF(CX + 5, TT + 8.6, TZ1 + 1.8), V3(0.25, 3.2, 4.4), P.amber)
	sign("WordTop", { { "TOP", P.amber, "B", 1 } }, 6, 1.8, CX, TT - 17, TZ0 + 0.2, V3(CX, 0, -8000), { plate = P.board, thick = 0.25 })
	for _, z in { -8382, -8386 } do B.chevron(CX, G + 0.05, z, 0, -1, 4, P.line) end
	-- the stages' numbers on the course's east face
	for i, z in { -8425, -8470, -8516, -8566, -8604, -8630 } do
		local x = if i == 6 then X1 + 2.2 else X1 + 0.2
		sign("StagePlate", { { tostring(i), P.amber, "B", 1 } }, 6, 6, x, G + 4, z, V3(0, 0, z), { plate = P.board, thick = 0.3 })
	end
end

-- ---------------------------------------------------------------- the hill (back middle) and its watchtower
-- (judge round 2: a stepped plinth 18 high with planks for ramps. now three tiers 8 high each, solid wedge ramps cut
-- flush between slate side walls with vertical ends, a lookout box: a deck between two solid slate side walls under
-- its roof, 54 over the ground)
local function wedgeRamp(name, dir, x0, x1, z0, z1, y0, rise, hex)
	local lo, hi = math.min(x0, x1), math.max(x0, x1)
	local zs, zn = math.min(z0, z1), math.max(z0, z1)
	local cx, cz = (lo + hi) / 2, (zs + zn) / 2
	local yaw = ({ ["+z"] = 0, ["-z"] = math.pi, ["+x"] = math.pi / 2, ["-x"] = -math.pi / 2 })[dir]
	local along = if dir == "+z" or dir == "-z" then zn - zs else hi - lo
	local across = if dir == "+z" or dir == "-z" then hi - lo else zn - zs
	local base = CF(cx, 0, cz) * CFrame.Angles(0, yaw, 0)
	local function at(dx, y) return base * CF(dx, y, 0) end
	part(name, at(0, y0 + rise / 2), V3(across, rise, along), hex, { wedge = true })
	for _, sx in { -1, 1 } do
		local dx = sx * (across / 2 + 0.75)
		part(name .. "Wall", at(dx, y0 + 1.5), V3(1.5, 3, along), P.pier)
		part(name .. "Wall", at(dx, y0 + 3 + rise / 2), V3(1.5, rise, along), P.pier, { wedge = true })
		local a, b = (base * CF(dx, y0 + 3, -along / 2)).Position, (base * CF(dx, y0 + 3 + rise, along / 2)).Position
		part(name .. "Nose", CFrame.lookAt((a + b) / 2, b) * CFrame.Angles(0, math.pi / 2, 0), V3((b - a).Magnitude, 1.1, 1.1), P.trim, { cyl = true })
	end
end
local function theHill()
	local HX, HZ = 12, -8656
	-- (judge round 3: three drums on flat grass read as a cake stand, and Roblox's own cylinders showed facets. tier 1 is
	-- now a grass bank, 140 across at the foot, with the slate tiers standing on it; every round thing is a kit mesh,
	-- with plain invisible solids to walk on)
	local cylMesh = lib():FindFirstChild("tl_cylinder")
	cylMesh = cylMesh and cylMesh:FindFirstChildWhichIsA("MeshPart")
	local bankMesh = lib():FindFirstChild("tl_bank")
	bankMesh = bankMesh and bankMesh:FindFirstChildWhichIsA("MeshPart")
	local function smooth(name, y0, y1, d, hex)
		if not cylMesh then return B.drum("LotShell", name, HX, HZ, y0, y1, d, hex) end
		local p = cylMesh:Clone()
		p.Name = name; p.Size = V3(d, y1 - y0, d); p.CFrame = B.at(CF(HX, (y0 + y1) / 2, HZ)); p.Color = Color3.fromHex(hex); p.Material = SP
		p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
		p.Parent = B.root.LotScenery
		B.count += 1
		B.drum("Collision", name .. "Solid", HX, HZ, y0, y1, d, hex, { tr = 1, noShadow = true })
		return p
	end
	if bankMesh then
		local bk = bankMesh:Clone()
		bk.Name = "HillBank"; bk.Size = V3(140, 8, 140); bk.CFrame = B.at(CF(HX, G + 4, HZ)); bk.Color = Color3.fromHex(C.grass); bk.Material = SP
		bk.Anchored = true; bk.CanCollide = false; bk.CanQuery = false; bk.CanTouch = false
		bk.Parent = B.root.LotScenery
		B.count += 1
		for k = 1, 16 do -- (the bank to walk on: sixteen half-stud steps under the mesh)
			B.drum("Collision", "HillBankStep", HX, HZ, 234, G + 0.5 * k, 2 * (70 - 18 * (k - 0.5) / 16), C.grass2, { tr = 1, noShadow = true })
		end
	else
		smooth("HillWall", 234, G + 6.8, 104, P.pier)
		smooth("HillCoping", G + 6.7, G + 7.9, 105.4, P.trim)
		smooth("HillGrass", G + 7.7, G + 8, 102.4, C.grass2)
	end
	for _, t in { { 72, G + 16 }, { 40, G + 24 } } do
		local d, top = t[1], t[2]
		smooth("HillWall", 234, top - 1.2, d, P.pier)
		smooth("HillCoping", top - 1.3, top - 0.1, d + 1.4, P.trim)
		smooth("HillGrass", top - 0.3, top, d - 1.6, C.grass2)
	end
	-- the ramps, spiralling: up from the yard (north, through the gap in its kerb), round to the east, round to the west
	-- (judge round 4: the bank buried the ramp from the yard; the bank is walkable all round, so it is the way up)
	wedgeRamp("HillRamp", "-x", HX + 51, HX + 35, HZ - 4, HZ + 4, G + 8, 8, C.conc)
	wedgeRamp("HillRamp", "+x", HX - 35, HX - 19, HZ - 4, HZ + 4, G + 16, 8, C.conc)
	post(HX - 10, -8582, G, 251)
	sign("WordHill", { { "THE HILL", P.amber, "B", 1 } }, 9, 2, HX - 10, 252.2, -8580.6, V3(HX - 10, 0, -8000), { plate = P.board, thick = 0.25 })
	-- the tower: a hollow slate core (a door north), a pad inside throws you up through a hatch onto the deck; two solid
	-- side walls east and west carry the roof, low parapets north and south
	local TY, DY, RY = G + 24, G + 54, G + 68
	local cx0, cx1, cz0, cz1 = HX - 5, HX + 5, HZ - 5, HZ + 5
	blk("TowerCore", cx0, cx1, TY, DY - 1.6, cz0, cz0 + 1.5, P.pier2)
	blk("TowerCore", cx0, cx0 + 1.5, TY, DY - 1.6, cz0, cz1, P.pier2)
	blk("TowerCore", cx1 - 1.5, cx1, TY, DY - 1.6, cz0, cz1, P.pier2)
	wallX("TowerCore", cx0, cx1, TY, DY - 1.6, cz1 - 1.5, cz1, P.pier2, { { HX - 2.2, HX + 2.2, TY, TY + 7.5 } })
	local h = 4.5
	for _, s in { { HX - 10, HX + 10, HZ + h, HZ + 10 }, { HX - 10, HX + 10, HZ - 10, HZ - h }, { HX - 10, HX - h, HZ - h, HZ + h }, { HX + h, HX + 10, HZ - h, HZ + h } } do
		blk("TowerDeck", s[1], s[2], DY - 1.6, DY, s[3], s[4], P.mass)
	end
	for _, sz in { -1, 1 } do
		blk("TowerParapet", HX - 7, HX + 7, DY, DY + 3.5, HZ + sz * 9, HZ + sz * 10, C.conc)
		nose("TowerParapetNose", "x", HX - 7, HX + 7, DY + 3.5, HZ + sz * 9.5, 1.1)
	end
	for _, sx in { -1, 1 } do
		blk("TowerSideWall", HX + sx * 7, HX + sx * 10, DY - 1.65, RY, HZ - 10, HZ + 10, P.slate)
	end
	blk("TowerRoof", HX - 11, HX + 11, RY, RY + 2, HZ - 11, HZ + 11, P.slate)
	blk("TowerRoofEdge", HX - 11.3, HX + 11.3, RY - 0.4, RY + 0.2, HZ - 11.3, HZ + 11.3, P.trim)
	B.pad(HX, TY, HZ, V3(0, 74, 5))
	B.lamp(HX, RY - 2, HZ, "point", 18, 0.4, P.warm)
	B.lamp(HX, TY + 6, HZ, "point", 10, 0.5, P.lampWhite)
	for _, k in { { -52, -8712 }, { 70, -8706 }, { -54, -8600 } } do target(k[1], G, k[2], V3(HX, G, HZ)) end
end

-- ---------------------------------------------------------------- the gold Carls (in the training rooms)
local function gold()
	for i = 1, 3 do
		local g = L.GOLD[i]
		B.marker(LOT.GoldSpots, "Gold" .. i, g[2].X, g[2].Y, g[2].Z, g[3])
	end
end

-- ---------------------------------------------------------------- build (called by TrainingV2.build with its context)
function L.build(b, T): string
	B, P, TV = b, T.P, T
	-- (18 Nov: the course was rebuilt bigger; its tower stands where TrainingV2 says)
	if TV.COURSE then L.GOLD[3] = { "course tower", TV.COURSE.tower, V3(-30, TV.COURSE.tower.Y, -8122) } end
	local root = B.root
	for _, n in { "LotShell", "LotScenery" } do folderIn(root, n) end
	LOT = folderIn(root, "Lot")
	for _, n in { "Door", "Panel", "Beacons", "GoldSpots", "Targets" } do folderIn(LOT, n) end
	LOT:SetAttribute("Push", L.PUSH)
	local before = B.count
	local beacon = garage()
	bay(beacon)
	land()
	longLane()
	theBlocks()
	theClimb()
	theHill()
	gold()
	if TV.EGG_DOOR then eggDoor(TV.EGG_DOOR) end -- (the gold dummies' door, where the training hall puts it)
	-- where you are on the lot (TheLot: the attribute OnLot, its light and sounds): the loading bay inside the garage door
	-- and everything past the façade. (17 Nov: one box from the garage door's line across the whole width took in the
	-- range's far end and the basement too, so they had the lot's open-air light; they are the hall's now, the basement's
	-- walk-out comes up into the range)
	local function area(x0, x1, z0, z1)
		local a = Instance.new("Part")
		a.Name = "Area"; a.Anchored = true; a.Transparency = 1; a.CanCollide = false; a.CanQuery = false; a.CanTouch = false
		local y0, y1 = 228, T.LOT[3]
		a.Size = V3(x1 - x0, y1 - y0, math.abs(z1 - z0)); a.CFrame = B.cf((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
		a.Parent = LOT
	end
	area(-L.BAY.x - 2, L.BAY.x + 2, L.DOOR.z - 1, L.FACE.z0 - 2)
	area(T.LOT[1], T.LOT[2], L.FACE.z0 - 2, T.LOT[4])
	return ("the back lot: %d things, %d targets, %d slats; %s"):format(B.count - before, #LOT.Targets:GetChildren(), #LOT.Door:GetChildren(), tostring(B.treeNote))
end

-- rays from eye points on the lot to the tops of the playground's tall parts: how many the near ridge hides
-- (the ridge is ellipsoids: the test is exact, not the parts' boxes)
function L.horizon(tg): string
	local tops = {}
	local pg = workspace.Map.Hub:FindFirstChild("Playground")
	if pg then for _, d in pg:GetDescendants() do if d:IsA("BasePart") and d.Size.Y > 100 then table.insert(tops, d.Position + V3(0, d.Size.Y / 2, 0)) end end end
	local lumps = {}
	for _, p in tg.LotScenery:GetChildren() do if p.Name == "NearRidge" then table.insert(lumps, p) end end
	local function hidden(a, b)
		for _, p in lumps do
			local h = p.Size / 2
			local la, lb = p.CFrame:PointToObjectSpace(a) / h, p.CFrame:PointToObjectSpace(b) / h
			local d = lb - la
			local A, Bq, Cq = d:Dot(d), 2 * la:Dot(d), la:Dot(la) - 1
			local disc = Bq * Bq - 4 * A * Cq
			if disc >= 0 then
				local s = math.sqrt(disc)
				local t1, t2 = (-Bq - s) / (2 * A), (-Bq + s) / (2 * A)
				if (t1 >= 0 and t1 <= 1) or (t2 >= 0 and t2 <= 1) or (t1 < 0 and t2 > 1) then return true end
			end
		end
		return false
	end
	local eyes = { { "apron", V3(0, 245, -8330) }, { "lane", V3(136, 246, -8400) }, { "climb pad", V3(-120, 245, -8396) },
		{ "summit", V3(-120, 273, -8604) }, { "catwalk", V3(38, 273, -8475) }, { "watchtower", V3(12, 293, -8656) } }
	local out = {}
	for _, e in eyes do
		local n = 0
		for _, t in tops do if hidden(e[2], t) then n += 1 end end
		table.insert(out, ("%s %d/%d"):format(e[1], n, #tops))
	end
	return "playground tops hidden by the ridge: " .. table.concat(out, ", ")
end

-- the lot's own checks (TrainingV2.check calls this): the data the server reads, and nothing solid on a Carl
function L.check(tg, mk, T, O): { string }
	local out = {}
	local lot = tg:FindFirstChild("Lot")
	if not lot then return { "MISSING Lot" } end
	local function need(c, what) if not c then table.insert(out, "MISSING Lot." .. what) end end
	need(lot:FindFirstChild("Door") and #lot.Door:GetChildren() >= 13, "Door (slats)")
	need(lot:FindFirstChild("Doorway"), "Doorway")
	need(lot:FindFirstChild("Area"), "Area")
	need(lot:FindFirstChild("Panel") and lot.Panel:FindFirstChild("Timer"), "Panel.Timer")
	local gs = lot:FindFirstChild("GoldSpots")
	need(gs and #gs:GetChildren() == 3, "GoldSpots (3)")
	need(lot:FindFirstChild("Targets") and #lot.Targets:GetChildren() >= 20, "Targets")
	need(lot:FindFirstChild("Beacons") and #lot.Beacons:GetChildren() == 4, "Beacons (4)")
	local doors = mk:FindFirstChild("Doors")
	if doors and doors:FindFirstChild("LotExit") then table.insert(out, "LEFT OVER Doors.LotExit (the basement's way out is walked now)") end
	local wd = tg:FindFirstChild("WalkOutDoor", true)
	need(wd and wd:FindFirstChild("Inside") and wd:FindFirstChild("Block") and wd:FindFirstChild("WalkOutLeaf"), "WalkOutDoor (leaf, Block, Inside)")
	local op = OverlapParams.new(); op.FilterType = Enum.RaycastFilterType.Include; op.FilterDescendantsInstances = { tg }; op.RespectCanCollide = true
	local rp = RaycastParams.new(); rp.FilterType = Enum.RaycastFilterType.Include; rp.FilterDescendantsInstances = { tg }
	local stuck, floating = 0, 0
	-- (the probe is a part, so round solids count by their shape: the hill bank's steps are 140 across and their boxes
	-- reached Carl spots 15 studs clear of them)
	local probe = Instance.new("Part"); probe.Anchored = true; probe.CanCollide = false; probe.CanQuery = false; probe.Size = V3(2.4, 6.4, 1.2)
	probe.Transparency = 1; probe.Parent = workspace
	for _, f in { lot.Targets, gs } do
		for _, s in f:GetChildren() do
			probe.CFrame = s.CFrame * CF(0, 3.6, 0)
			local hits = workspace:GetPartsInPart(probe, op)
			if #hits > 0 then stuck += 1; table.insert(out, "solid in " .. s.Name .. " at " .. tostring(s.Position) .. ": " .. hits[1].Name) end
			local down = workspace:Raycast(s.Position + V3(0, 0.5, 0), V3(0, -2, 0), rp)
			if not down then floating += 1; table.insert(out, "nothing under " .. s.Name .. " at " .. tostring(s.Position)) end
		end
	end
	probe:Destroy()
	table.insert(out, ("lot: %d targets, %d slats, Carl spots with something solid in them %d, standing on nothing %d"):format(
		#lot.Targets:GetChildren(), #lot.Door:GetChildren(), stuck, floating))
	table.insert(out, L.horizon(tg))
	table.insert(out, L.axis(tg))
	-- the long lane: from each counter to every Carl's chest and head (blocked = both lines blocked)
	local lanes, blocked = 0, 0
	for _, t in lot.Targets:GetChildren() do
		if t.Position.X > 96 and t.Position.X < 176 then
			for _, cx in { 112, 136, 160 } do
				local eye = V3(cx, 246.6, -8401)
				local c, h = t.Position + V3(0, 3.6, 0), t.Position + V3(0, 6.2, 0)
				local hc, hh = workspace:Raycast(eye, c - eye, rp), workspace:Raycast(eye, h - eye, rp)
				lanes += 1
				if hc and hh then blocked += 1 end
			end
		end
	end
	table.insert(out, ("long lane: counter-to-Carl lines blocked %d of %d"):format(blocked, lanes))
	-- the trees stand on the ground: at four sides of each trunk the ground is no lower than its base (no gap under it)
	-- and no more than L.TREE.deep over it
	local shapes, was = {}, {}
	for _, d in tg:GetDescendants() do
		if d:IsA("BasePart") and (d.Name == "NearRidge" or d.Name == "Berm" or d.Name == "Ground") then table.insert(shapes, d); was[d] = d.CanQuery; d.CanQuery = true end
	end
	local trp = RaycastParams.new(); trp.FilterType = Enum.RaycastFilterType.Include; trp.FilterDescendantsInstances = shapes
	local trees, gaps, deep = 0, 0, 0
	for _, m in tg:GetDescendants() do
		if m:IsA("Model") and m.Name == "Tree" then
			trees += 1
			local b = m:GetPivot().Position
			for _, o in treeSides(L.TREE.r * m:GetScale()) do
				local h = workspace:Raycast(V3(b.X + o.X, 700, b.Z + o.Z), V3(0, -900, 0), trp)
				local gy = if h then h.Position.Y else -math.huge
				if gy < b.Y - 0.05 then
					gaps += 1
					if gaps <= 6 then table.insert(out, ("tree over a gap at (%.0f, %.1f, %.0f): ground %.1f under a side"):format(b.X, b.Y, b.Z, gy)) end
					break
				elseif gy - b.Y > math.max(L.TREE.deep, 1.12 * m:GetScale() + L.TREE.sink + 0.05) then
					deep += 1
					if deep <= 6 then table.insert(out, ("tree buried %.1f at a side at (%.0f, %.1f, %.0f)"):format(gy - b.Y, b.X, b.Y, b.Z)) end
					break
				end
			end
		end
	end
	for d, q in was do d.CanQuery = q end
	table.insert(out, ("trees: %d, a gap under a side %d, deeper than %.1f at a side %d"):format(trees, gaps, L.TREE.deep, deep))
	-- every tree outside the fence, its whole box at least L.FENCE.clear off its line; trunks apart; crowns apart
	local FN = L.FENCE
	local over, list = 0, {}
	for _, m in tg:GetDescendants() do
		if m:IsA("Model") and m.Name == "Tree" then
			local bcf, bsz = m:GetBoundingBox()
			local hx = math.abs(bcf.RightVector.X) * bsz.X / 2 + math.abs(bcf.UpVector.X) * bsz.Y / 2 + math.abs(bcf.LookVector.X) * bsz.Z / 2
			local hz = math.abs(bcf.RightVector.Z) * bsz.X / 2 + math.abs(bcf.UpVector.Z) * bsz.Y / 2 + math.abs(bcf.LookVector.Z) * bsz.Z / 2
			local q = bcf.Position
			local clear = q.X + hx < -FN.x - FN.clear + 0.01 or q.X - hx > FN.x + FN.clear - 0.01 or q.Z + hz < FN.z0 - FN.clear + 0.01 or q.Z - hz > FN.z1 + FN.clear - 0.01
			if not clear then
				over += 1
				if over <= 6 then table.insert(out, ("TREE AT THE FENCE (%.0f, %.0f): box %.1f x %.1f"):format(q.X, q.Z, 2 * hx, 2 * hz)) end
			end
			local b = m:GetPivot().Position
			table.insert(list, { x = b.X, z = b.Z, r = math.min(bsz.X, bsz.Z) / 2 })
		end
	end
	local nearest, touching = math.huge, 0
	for i = 1, #list do
		for j = i + 1, #list do
			local dd = math.sqrt((list[i].x - list[j].x) ^ 2 + (list[i].z - list[j].z) ^ 2)
			nearest = math.min(nearest, dd)
			if dd < list[i].r + list[j].r then touching += 1 end
		end
	end
	table.insert(out, ("trees outside the fence: %d with a box over or inside it (clear %.1f); nearest two trunks %.1f apart; crowns running into each other %d"):format(
		over, FN.clear, nearest, touching))
	-- the fence keeps everyone in: from points on the lot (its floor, the long lane, the climb's top) rays every way but
	-- north (the hall is that side), flat and up 20 and 35 degrees, must meet something solid within 900
	local cp = RaycastParams.new(); cp.FilterType = Enum.RaycastFilterType.Include; cp.FilterDescendantsInstances = { tg }; cp.RespectCanCollide = true
	local ring, leaks = 0, 0
	for _, at in { V3(0, G + 4, -8500), V3(-150, G + 4, -8420), V3(150, G + 4, -8650), V3(0, G + 4, -8715), V3(-170, G + 4, -8330),
		V3(170, G + 4, -8330), V3(-120, G + 69, -8684) } do
		for k = 0, 23 do
			local a = k * math.pi / 12
			local h = V3(math.sin(a), 0, math.cos(a))
			if h.Z > 0.5 then continue end
			for _, el in { 0, 20, 35 } do
				local d = (h * math.cos(math.rad(el)) + V3(0, math.sin(math.rad(el)), 0)).Unit
				ring += 1
				if not workspace:Raycast(at, d * 900, cp) then
					leaks += 1
					if leaks <= 6 then table.insert(out, ("LOT LEAK from (%.0f, %.0f, %.0f) toward (%.2f, %.2f, %.2f)"):format(at.X, at.Y, at.Z, d.X, d.Y, d.Z)) end
				end
			end
		end
	end
	table.insert(out, ("the lot closed in: %d rays, leaks %d"):format(ring, leaks))
	-- the basement's floors (owner, 17 Nov: "there's a hole in the ground once you go down the stairs"): straight down from
	-- under each ceiling, a stud apart, over the room, the stairs' foot, the stairwell and the walk-out, every ray must
	-- meet a floor no lower than the basement's (columns that are solid at the start, a wall, are skipped); and on the
	-- walk-out, the head room over each floor
	local BS = T and T.BASEMENT
	if BS and BS.exit then
		local EX, R, W, FL = BS.exit, BS.room, BS.well, BS.floor
		local o = O or Vector3.zero
		local fp = RaycastParams.new(); fp.FilterType = Enum.RaycastFilterType.Include; fp.FilterDescendantsInstances = { tg }; fp.RespectCanCollide = true
		local inq = OverlapParams.new(); inq.FilterType = Enum.RaycastFilterType.Include; inq.FilterDescendantsInstances = { tg }; inq.RespectCanCollide = true
		local regions = { -- { name, x0, x1, z0, z1, start height, walk-out (head room counts) }
			{ "room", R.x0, R.x1, R.z0, R.z1, R.ceil - 0.5, false },
			{ "stairs' foot", W.x1 - 6, W.x1, W.z1, R.z0, R.ceil - 0.5, false },
			{ "stairwell", W.x0, W.x1, W.z0, W.z1, W.top - 0.5, false },
			{ "walk-out landing", EX.x0, EX.land.x1, EX.land.z0, EX.land.z1, 235.5, true },
			{ "flight A", EX.x0, EX.fA.x1, EX.face, EX.land.z0, EX.thin.y - 0.5, true },
			{ "the bank", EX.x0, EX.east, EX.back, EX.skin, EX.ceil - 0.5, true },
		}
		local probes, holes, minHead, headAt = 0, 0, math.huge, ""
		for _, rg in regions do
			for x = math.min(rg[2], rg[3]) + 0.5, math.max(rg[2], rg[3]) - 0.5, 1 do
				for z = math.min(rg[4], rg[5]) + 0.5, math.max(rg[4], rg[5]) - 0.5, 1 do
					local at = V3(x, rg[6], z) + o
					if #workspace:GetPartBoundsInBox(CFrame.new(at), V3(0.1, 0.1, 0.1), inq) > 0 then continue end
					probes += 1
					local h = workspace:Raycast(at, V3(0, -(rg[6] - FL + 6), 0), fp)
					for _ = 1, 4 do -- (a handrail is not a floor: look on past it)
						if not (h and string.find(h.Instance.Name, "Rail", 1, true)) then break end
						h = workspace:Raycast(h.Position - V3(0, 0.5, 0), V3(0, -(h.Position.Y - FL + 6), 0), fp)
					end
					if not h or h.Position.Y < FL + o.Y - 0.6 then
						holes += 1
						if holes <= 6 then table.insert(out, ("BASEMENT HOLE (%s) at (%.1f, %.1f)"):format(rg[1], x, z)) end
					elseif rg[7] then
						local from, up = h.Position + V3(0, 0.05, 0), nil
						for _ = 1, 4 do -- (handrails don't count: you walk beside them)
							up = workspace:Raycast(from, V3(0, 20, 0), fp)
							if up and string.find(up.Instance.Name, "Rail", 1, true) then from = up.Position + V3(0, 0.5, 0) else break end
						end
						local head = if up then up.Position.Y - h.Position.Y else 20
						if head < minHead then minHead, headAt = head, ("(%.1f, %.1f)"):format(x, z) end
					end
				end
			end
		end
		table.insert(out, ("the basement's floors: %d probes, holes %d; the walk-out's least head room %.1f at %s"):format(probes, holes, minHead, headAt))
	end
	-- the gold dummies' door (where T.EGG_DOOR puts it): its trigger takes key holders only and lands somewhere; shut (as
	-- everyone without the key has it) nothing gets past it: rays across the whole corridor at knee, waist and head
	-- height, from 3 in front of it toward the dark plate, all stop on something solid before the pocket behind it
	local EGG = T and T.EGG_DOOR
	if EGG then
		local ed = tg:FindFirstChild("EggDoor", true)
		need(ed and (EGG.room or ed:FindFirstChild("EggBack")) and ed:FindFirstChild("EggBlock") and ed:FindFirstChild("EggPlate"), "EggDoor (back, block, plate)")
		if EGG.room then need(tg:FindFirstChild("EggPortalRing", true) and tg:FindFirstChild("EggPortalStep", true), "the portal (EggPortalRing, EggPortalStep: L.import(L.PORTAL_KIT) first)") end
		local ep = doors and doors:FindFirstChild("EggPortal")
		need(ep and ep:GetAttribute("NeedKey") == "LotKey" and ep:GetAttribute("Land") == "PlaygroundArrive", "Doors.EggPortal (NeedKey LotKey, Land PlaygroundArrive)")
		local pa = doors and doors:FindFirstChild("PlaygroundArrive")
		need(pa and #pa:GetChildren() > 0, "Doors.PlaygroundArrive (the portal's landing)")
		local F = CF(O or Vector3.zero) * EGG.cf
		local W = EGG.w or 8.4
		local cw = EGG.cw or W + 1.2
		local sp = RaycastParams.new(); sp.FilterType = Enum.RaycastFilterType.Include; sp.FilterDescendantsInstances = { tg }; sp.RespectCanCollide = true
		local n, gaps = 0, 0
		for i = 0, 12 do
			local x = -cw / 2 + 0.3 + i * (cw - 0.6) / 12
			for _, y in { 1, 3, 5.5 } do
				n += 1
				local a = (F * CF(x, y, 3)).Position
				local b = (F * CF(x, y, -((if EGG.room then EGG.door or 2.4 else L.EGG_DEPTH) - 0.5))).Position
				if not workspace:Raycast(a, b - a, sp) then
					gaps += 1
					if gaps <= 4 then table.insert(out, ("EGG DOOR GAP at x %.1f, %.1f up"):format(x, y)) end
				end
			end
		end
		table.insert(out, ("the gold dummies' door shut: %d rays, gaps %d"):format(n, gaps))
	end
	return out
end

-- the watchtower ends the axis: rays from the yard's steps (through the open door), the terrace and in front of it to
-- points on the tower from the deck to the roof (the tower's own parts and the door's slats don't count)
function L.axis(tg): string
	local rp = RaycastParams.new(); rp.FilterType = Enum.RaycastFilterType.Exclude
	local ex = {}
	for _, d in tg:GetDescendants() do
		if d:IsA("BasePart") and (string.sub(d.Name, 1, 5) == "Tower" or (tg:FindFirstChild("Lot") and (d:IsDescendantOf(tg.Lot.Door) or d.Name == "DoorBlock"))) then table.insert(ex, d) end
	end
	local hub = workspace.Map:FindFirstChild("Hub")
	if hub and hub:FindFirstChild("Barrier") then table.insert(ex, hub.Barrier) end
	rp.FilterDescendantsInstances = ex
	local HX, HZ, DY, RY = 12, -8656, G + 54, G + 68
	local pts = {}
	for _, y in { DY + 1, DY + 4, RY - 2, RY + 1.5 } do for _, x in { HX - 9, HX, HX + 9 } do table.insert(pts, V3(x, y, HZ + 10.5)) end end
	local out = {}
	for _, e in { { "yard steps", V3(0, 247.5, -8222) }, { "terrace", V3(0, 249, -8322) }, { "below the terrace", V3(0, 245, -8346) } } do
		local n = 0
		for _, q in pts do if not workspace:Raycast(e[2], q - e[2], rp) then n += 1 end end
		table.insert(out, ("%s %d/%d"):format(e[1], n, #pts))
	end
	return "watchtower points in view: " .. table.concat(out, ", ")
end

return L
