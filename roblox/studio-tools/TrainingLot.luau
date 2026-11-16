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
-- hides the playground's towers (L.horizon checks it). you leave by the EXIT door beside the portal (back on the
-- muster's spawn points) or through the garage while it is up; anyone who has opened it can stand at it to reopen it.
-- (push 7 is judge round 1's rework: vault Reviews\Back lot - judge round 1.md)
-- what the game reads (TheLot.server.luau): Hub.TrainingGround.Lot { Door, Doorway, Panel, Beacons, GoldSpots, Targets,
-- Area }; LaserDoors: the trigger Hub.Doors.LotExit (Land "@TrainSpawns"). kit: tools/roblox/lot_models.py (L.KIT).
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
L.PUSH = 15

-- the plan (world coordinates). the yard's end wall is z -8258..-8262; the door runs in its middle plane
local G = 240                                                     -- the lot's ground
L.DOOR = { x = 12, y0 = 242, y1 = 258.5, z = -8260 }              -- the opening x -12..12, y 242..258.5
L.BAY = { x = 22, z0 = -8262, z1 = -8300, top = 264 }             -- the loading bay, inside
L.FACE = { x0 = -100, x1 = 92, z0 = -8300, z1 = -8304, top = 284 } -- the façade the lot sees
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
function L.import(): string
	local MAT = { plastic = SP, neon = NEON }
	local ok, container = pcall(function() return InsertService:LoadAsset(L.KIT) end)
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
		m:SetAttribute("AssetId", L.KIT); m:SetAttribute("Kit", "lot"); m:SetAttribute("FileFrame", true)
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
local B, P, LOT
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
	local WIN = { { -92, -72 }, { -68, -40 }, { 40, 70 }, { 74, 86 } }
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
	for _, x in { -94, -70, 72, 88 } do
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
	-- the exit: a door in a recess beside the portal, EXIT over it; walk in and you are back on the muster's spawns
	blk("ExitBack", exitX0, exitX1, G, G + 12, F.z0, F.z0 - 0.6, P.slate)
	blk("ExitFloor", exitX0, exitX1, G - 1, G, F.z0, F.z1, P.floor2)
	B.put("tv_frameMid", CF((exitX0 + exitX1) / 2, G, F.z1 - 0.6) * CFrame.Angles(0, math.pi, 0), { name = "ExitFrame" }).Parent = B.root.LotScenery
	sign("WordEXIT", { { "EXIT", P.amber, "B", 1 } }, 7, 1.7, (exitX0 + exitX1) / 2, G + 16.4, F.z1 - 1.2, V3((exitX0 + exitX1) / 2, 0, -9000), { plate = P.board, thick = 0.2 })
	B.lamp((exitX0 + exitX1) / 2, G + 11, F.z1 - 3, "point", 14, 0.6, P.warm)
	B.trigger("LotExit", exitX0 + 0.5, exitX1 - 0.5, G, G + 11, F.z0 - 0.6, F.z1 + 0.3, { Land = "@TrainSpawns", Say = "BACK INSIDE" })
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
	roll(-240, -8282, -101, -8282, 52, 228)   -- north, beside the hall
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
	local function tree(x, z, _y, s)
		local round = rng:NextNumber() < 0.55
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
	for z = -8300, -8780, -17 do tree(-200 + rng:NextNumber() * 6, z + rng:NextNumber() * 6, 251.5); tree(200 - rng:NextNumber() * 6, z + rng:NextNumber() * 6, 251.5) end
	for x = -190, 190, 17 do tree(x + rng:NextNumber() * 6, -8750 - rng:NextNumber() * 6, 251.5) end
	for x = -190, -112, 17 do tree(x + rng:NextNumber() * 4, -8284 + rng:NextNumber() * 4, 251.5) end
	for x = 104, 190, 17 do tree(x + rng:NextNumber() * 4, -8284 + rng:NextNumber() * 4, 251.5) end
	for z = -8270, -8610, -22 do tree(-236 - rng:NextNumber() * 6, z, 258); tree(236 + rng:NextNumber() * 6, z, 258) end
	-- clumps of big trees on the ridge's lower slopes
	-- (the berm and its trees stand in front of the ridge's steep foot)
	for _, c in { { -230, -8764 }, { -120, -8762 }, { -20, -8768 }, { 90, -8764 }, { 200, -8762 }, { 290, -8760 }, { -290, -8760 } } do
		for _ = 1, 5 do
			local x, z = c[1] + rng:NextNumber(-16, 16), c[2] + rng:NextNumber(-4, 4)
			local y = ridgeY(x, z)
			if y then tree(x, z, y - 1.5, 2 + rng:NextNumber() * 0.6) end
		end
	end
	-- rock shelves set into the ridge's lower slopes, behind the tree clumps (one feature for the biggest thing in view)
	-- (rock shelves were tried in push 10: against the ridge they read as grey discs floating in the sky; dropped)
	-- a few inside, on the grass between the zones (none in front of the exit, none tall near the climb)
	for _, t in { { -70, -8556 }, { 88, -8396 }, { 90, -8470 }, { 88, -8560 }, { -60, -8640 }, { 86, -8700 }, { -60, -8330 }, { -104, -8338 } } do
		tree(t[1], t[2], G)
	end
	for _, sh in shapes do sh.p.Parent = sh.parent; sh.p.CanQuery = sh.q end
	probeHome:Destroy()
	B.treeNote = ("trees: %d moved to flatter ground, %d left out, %d feet"):format(moved, dropped, feet)
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
	-- 6: the finish tower: 64 high, rounded corners, a lit band with the pale top over it, a flag; a strong pad at its foot
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
	B.pad(CX + 22, G, (TZ0 + TZ1) / 2, V3(-12.8, 104, 0)) -- (feet about 3 over the edge as they cross it)
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
	B, P = b, T.P
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
	local a = Instance.new("Part")
	a.Name = "Area"; a.Anchored = true; a.Transparency = 1; a.CanCollide = false; a.CanQuery = false; a.CanTouch = false
	local z0, z1, x0, x1, y0, y1 = L.DOOR.z - 1, T.LOT[4], T.LOT[1], T.LOT[2], 228, T.LOT[3]
	a.Size = V3(x1 - x0, y1 - y0, math.abs(z1 - z0)); a.CFrame = B.cf((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
	a.Parent = LOT
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
function L.check(tg, mk): { string }
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
	need(doors and doors:FindFirstChild("LotExit"), "Doors.LotExit")
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
				elseif gy - b.Y > L.TREE.deep then
					deep += 1
					if deep <= 6 then table.insert(out, ("tree buried %.1f at a side at (%.0f, %.1f, %.0f)"):format(gy - b.Y, b.X, b.Y, b.Z)) end
					break
				end
			end
		end
	end
	for d, q in was do d.CanQuery = q end
	table.insert(out, ("trees: %d, a gap under a side %d, deeper than %.1f at a side %d"):format(trees, gaps, L.TREE.deep, deep))
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
