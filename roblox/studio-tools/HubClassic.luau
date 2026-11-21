--!nocheck
-- THE ROTUNDA, back (21 Nov 2026). The owner, shown hub_round3_sheet.jpg (place v448): "do we still have the hib before I
-- asked for the like the expanded circle ?" ... "Yes, add it", then "make that the default one ... Until we fix the other
-- ones!" (HubTravel.DEFAULT = "classic"). Not a new builder: HubRotunda's own pre-v3 form (VERSION 2, Layout "lifts",
-- LoungeStyle "lounge", palette "glow": the v448 teal), built as a stage copy at its own site and re-homed into
-- Map.Hub.Classic under the multi-hub contract (side-session-notes/HUB-MARKERS.md):
--   * the folder: Hub "classic", Title "THE ROTUNDA", Order 7, Site; QueuePads / HubSpawns / HubArrive direct children
--     (NOT "Rotunda": HubTravel keeps that name for the retired ring)
--   * its 12 pads (the five lifts, Bank "lifts"; the seven upstairs, Bank "upper", reached by the two jump pads) carry
--     Hub; their old pink / cyan / yellow in the pastel TeamColors (K.recolorPads, the deep Side plates by Team)
--   * Hub on every tagged marker (regulars' places and points, VIP, holograms, jump pads, the gym's box spot)
--   * the training door ClassicToTraining (GateKit's red shutter at the armory's end) in Map.Hub.Doors, like
--     HotelToTraining (Land "@TrainSpawns", Say, Hub); training's ToHub brings players back here (HubTravel.arrive)
--   * what the old hub never had, through HubKit's helpers pointed at the folder: the HUBS terminal by the spawn rug,
--     the board and arm tables either side of it, an arcade spot in the east wall's gap, the code panel's spot on the
--     far wall's west wing, the spectate board on the round room's side 9 under the balcony, and a zombies room behind
--     a doorway cut in the far wall's east wing (its guide outside); the box spot gets Ring 1 / Half 8.7
-- Known differences from v448, baked into the builder since: you spawn in the big lounge; the armory is the 18 Nov
-- makeover (display bays, no maintenance bench); the gate is GateKit's shutter. The exact v448 source is git a08ad96.
--   usage (Studio's command bar, Edit): print(require(game.ServerStorage.PolishBackup.HubClassic:Clone()).build())
--   (opts.replace = true takes an existing Map.Hub.Classic and its ClassicToTraining away first)
local HCL = {}
HCL.SITE = Vector3.new(-1800, 240, -15800)
HCL.ID, HCL.FOLDER, HCL.TITLE, HCL.ORDER = "classic", "Classic", "THE ROTUNDA", 7
HCL.OLD_TEAM = { "ff4fd8", "37d6ff", "ffe14d" } -- (the Rotunda builder's R.TEAM)

local function rotunda()
	local m = game.ServerStorage.PolishBackup.HubRotunda:Clone()
	m:SetAttribute("Layout", "lifts"); m:SetAttribute("LoungeStyle", "lounge")
	local R = require(m); m:Destroy()
	R.ROOM = HCL.FOLDER
	return R
end

function HCL.build(opts)
	opts = opts or {}
	assert(game:GetService("RunService"):IsEdit(), "Edit mode only")
	local PB = game.ServerStorage.PolishBackup
	local CS = game:GetService("CollectionService")
	local SITE = HCL.SITE
	local hub = workspace.Map.Hub
	local out = {}
	if hub:FindFirstChild(HCL.FOLDER) then
		if not opts.replace then return "Map.Hub." .. HCL.FOLDER .. " is already there (opts.replace = true to rebuild)" end
		hub[HCL.FOLDER]:Destroy()
		local d = hub.Doors:FindFirstChild(HCL.FOLDER .. "ToTraining"); if d then d:Destroy() end
	end
	local near = workspace:GetPartBoundsInBox(CFrame.new(SITE + Vector3.new(0, 30, 10)), Vector3.new(240, 110, 240), OverlapParams.new())
	if #near > 0 then return "the site is not empty: " .. near[1]:GetFullName() end
	local R = rotunda()
	local ok, res = pcall(R.build, "stage", { version = 2, palette = "glow", at = SITE, stage = "HubStage_" .. HCL.FOLDER })
	if not ok then return "BUILD ERROR: " .. tostring(res) end
	table.insert(out, tostring(res))
	local stage = workspace.Map:FindFirstChild("HubStage_" .. HCL.FOLDER)
	local root = stage and stage:FindFirstChild(HCL.FOLDER)
	if not root then return table.concat(out, "\n") .. "\nno stage root" end
	-- re-home
	local g = root:FindFirstChild("Game")
	for _, n in { "QueuePads", "HubSpawns", "HubArrive" } do local f = g and g:FindFirstChild(n); if f then f.Parent = root end end
	local door = g and g:FindFirstChild("Doors") and g.Doors:FindFirstChild(HCL.FOLDER .. "ToTraining")
	if door then
		door:SetAttribute("Hub", HCL.ID); door:SetAttribute("Built", nil); door:SetAttribute("ForShow", nil)
		local ht = hub.Doors:FindFirstChild("HotelToTraining") -- (the same door as every other hub's: copy what it has that ours lacks)
		if ht then for k, v in ht:GetAttributes() do if door:GetAttribute(k) == nil and k ~= "Hub" then door:SetAttribute(k, v) end end end
		door.Parent = hub.Doors
	end
	if g then g:Destroy() end
	root:SetAttribute("Hub", HCL.ID); root:SetAttribute("Title", HCL.TITLE); root:SetAttribute("Order", HCL.ORDER)
	root:SetAttribute("Site", SITE); root:SetAttribute("Live", nil)
	root.Parent = hub
	stage:Destroy()
	-- the pads: Hub, pastel
	local K = require(PB.HubKit:Clone())
	for _, p in root.QueuePads:GetChildren() do p:SetAttribute("Hub", HCL.ID); p:SetAttribute("ForShow", nil) end
	K.recolorPads(root.QueuePads, { full = HCL.OLD_TEAM })
	local MAP = { [HCL.OLD_TEAM[1]] = K.TEAM[1], [HCL.OLD_TEAM[2]] = K.TEAM[2], [HCL.OLD_TEAM[3]] = K.TEAM[3] }
	for _, pad in root.QueuePads:GetChildren() do
		for _, d in pad:GetDescendants() do
			if d:IsA("BasePart") and d.Name:match("^Side%d") then
				local t = d:GetAttribute("Team") or tonumber(d.Name:match("%d+"))
				if t and K.TEAM_MUTED[t] then d.Color = Color3.fromHex(K.TEAM_MUTED[t]) end -- (the builder's deep shades: not caught by colour)
			elseif d:IsA("TextLabel") then
				local s = d.Text
				for old, new in MAP do s = s:gsub(old, new):gsub(old:upper(), new) end
				d.Text = s
			end
		end
	end
	-- Hub on every marker
	local NAMES = { HubSpawn = true, Arrive = true, NPCPoint = true, HubNPC = true, MiniGameSpot = true, HubSeat = true, VipPrompt = true, VipRoom = true, JumpPadTop = true }
	for _, d in root:GetDescendants() do
		if #CS:GetTags(d) > 0 or NAMES[d.Name] then d:SetAttribute("Hub", HCL.ID) end
		if d:GetAttribute("Built") == "Rotunda" then d:SetAttribute("Built", nil) end
	end
	-- the markers it never had (HubKit's helpers, their frames in world studs)
	local S = K.S
	S.root = root; S.site = CFrame.new(); S.hub = HCL.ID; S.live = true; S.style = "warm"; S.accent = "5fbcbf"; S.count = 0; S.lamps = 0; S.missing = 0
	local F7 = R.frame(SITE, 180, 0) -- (the lounge, due south: +x WEST, d = -z out from the round room's middle)
	local function L(x, d, toX, toD)
		if toX then return F7 * CFrame.lookAt(Vector3.new(x, 0, -d), Vector3.new(toX, 0, -toD)) end
		return F7 * CFrame.new(x, 0, -d)
	end
	K.travelTerminal(L(-21, 32.5, 0, 40.4))
	K.tableSpot(L(12.5, 35), "board")
	K.tableSpot(L(-12.5, 35), "arm")
	K.arcadeSpot(F7 * CFrame.new(-25.9, 0, -51.5) * CFrame.Angles(0, -math.pi / 2, 0))
	K.codePanelSpot(F7 * CFrame.new(21.5, 0, -67.95) * CFrame.Angles(0, math.pi, 0))
	local b9 = 9 * 360 / 14
	local rp = RaycastParams.new(); rp.FilterType = Enum.RaycastFilterType.Include; rp.FilterDescendantsInstances = { root }
	local up = workspace:Raycast((R.frame(SITE, b9, 25)).Position + Vector3.new(0, 2, 0), Vector3.new(0, 30, 0), rp)
	local yb = if up then up.Position.Y - SITE.Y else 12
	K.spectateSpot(R.frame(SITE, b9, 27.95) * CFrame.Angles(0, math.pi, 0) * CFrame.new(0, yb - 0.85 - 2.7, 0), 9.6, 5.4, {})
	-- the zombies room: a 5 x 8.5 doorway (F7 x -24.5..-19.5) cut out of the far wall's east wing, its dado and ledge
	local XC, DW, DH = -22, 5, 8.5
	local function cut(p, xa, xb, ytop)
		local cf = F7:ToObjectSpace(p.CFrame)
		local function half(axis) return math.abs((cf.RightVector * p.Size.X)[axis]) / 2 + math.abs((cf.UpVector * p.Size.Y)[axis]) / 2 + math.abs((cf.LookVector * p.Size.Z)[axis]) / 2 end
		local hx, hy, hz = half("X"), half("Y"), half("Z")
		local c = cf.Position
		local x0, x1, y0, y1, z0, z1 = c.X - hx, c.X + hx, c.Y - hy, c.Y + hy, c.Z - hz, c.Z + hz
		if x1 <= xa or x0 >= xb or y0 >= ytop then return end
		local pieces = {}
		if x0 < xa then table.insert(pieces, { x0, xa, y0, y1 }) end
		if x1 > xb then table.insert(pieces, { xb, x1, y0, y1 }) end
		if y1 > ytop then table.insert(pieces, { math.max(x0, xa), math.min(x1, xb), ytop, y1 }) end
		for _, q in pieces do
			local n = p:Clone()
			n.Size = Vector3.new(q[2] - q[1], q[4] - q[3], z1 - z0)
			n.CFrame = F7 * CFrame.new((q[1] + q[2]) / 2, (q[3] + q[4]) / 2, (z0 + z1) / 2)
			n.Parent = p.Parent
		end
		p:Destroy()
	end
	local cand = {}
	for _, d in root:GetDescendants() do
		if d:IsA("BasePart") and (d.Name == "LoungeWall" or d.Name == "LoungeDado" or d.Name == "LoungeLedge") then
			local v = F7:PointToObjectSpace(d.Position)
			if -v.Z > 67 and -v.Z < 70.5 and v.X < -2 then table.insert(cand, d) end
		end
	end
	for _, d in cand do cut(d, XC - DW / 2, XC + DW / 2, DH) end
	K.zombieRoom(F7 * CFrame.new(XC, 0, -68), { x0 = -7.5, x1 = 6, d = 16, h = 11, door = DW, guideSide = -1 }) -- (x1 6: 1 clear of the VIP room)
	for _, d in root:GetDescendants() do
		if d:IsA("BasePart") and d.Name == "MiniGameSpot" and d:GetAttribute("Game") == "box" then d:SetAttribute("Ring", 1); d:SetAttribute("Half", 8.7); d:SetAttribute("Hub", HCL.ID) end
	end
	local np = 0; for _, d in root:GetDescendants() do if d:IsA("BasePart") then np += 1 end end
	table.insert(out, ("Map.Hub.%s: %d parts, %d pads, %d spawns, %d arrivals; kit markers %d"):format(HCL.FOLDER, np, #root.QueuePads:GetChildren(), #root.HubSpawns:GetChildren(), #root.HubArrive:GetChildren(), S.count))
	return table.concat(out, "\n")
end

return HCL
