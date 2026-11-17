--!strict
-- ZoneCull: this client only draws the places you are near (the owner, 16 Nov 2026: "something lags really badly in
-- the training hub"; 9-12 fps there in Studio). Every map lives in one place: the hub's Rotunda, the playground,
-- training (and its back lot), the Rooftop v1, v2 and v3 arenas and any match copies, about 21,000 parts and 390 lights,
-- all of it drawn and lit for every player all the time. Here each big piece of workspace.Map is put aside on THIS
-- client (into ReplicatedStorage.ZoneCullHidden, which is not drawn) while neither your body nor your camera is near
-- it, and back into its own place the moment either comes near. The server keeps the real map: hits, spawns,
-- matches and everybody else are untouched, and the server's own changes still reach a piece that is put aside.
--
-- What counts as a piece: every child of workspace.Map with at least MIN_PARTS parts (the arenas, Map.Models), every
-- such child of Map.Hub (Rotunda, Playground, TrainingGround) and every match copy in Map.ArenaCopies. Small folders
-- (spawns, doors, zones, pads, barriers) always stay.
-- "Near": inside the piece's box grown by MARGIN studs. A piece comes back at once (checked before physics every
-- frame, so a teleport lands on a floor), and goes only after you have been out past MARGIN + SLACK for HIDE_AFTER s.
-- A player in a match also keeps the arena named by their "Arena" attribute.
-- Switch: workspace attribute ZoneCull = false shows everything again (Studio tests, or if something goes wrong).
-- Readout: this script's attribute Hidden lists what is put aside now.
-- Scripts that look things up by path see a put-aside piece as missing (TrainingDoors' trainingGround() is nil and it
-- scans again when the piece is back); GunHatsClient also looks in ZoneCullHidden. See roblox/docs/PERFORMANCE.md.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local me = Players.LocalPlayer
local MIN_PARTS = 200
local MARGIN = 250
local SLACK = 60
local HIDE_AFTER = 1.0
local REBOX = 20 -- seconds between re-measuring a piece's box (builders can grow a piece)

local hidden = Instance.new("Folder")
hidden.Name = "ZoneCullHidden"
hidden.Parent = ReplicatedStorage

type Piece = { inst: Instance, home: Instance, lo: Vector3, hi: Vector3, boxT: number, away: number, out: boolean }
local pieces: { [Instance]: Piece } = {}

local function box(i: Instance): (Vector3, Vector3, number)
	local lo, hi, n = Vector3.one * math.huge, -Vector3.one * math.huge, 0
	for _, d in i:GetDescendants() do
		if d:IsA("BasePart") then
			n += 1
			local r = d.Size.Magnitude / 2
			local p = d.Position
			lo = lo:Min(p - Vector3.new(r, r, r)); hi = hi:Max(p + Vector3.new(r, r, r))
		end
	end
	return lo, hi, n
end

local function near(pc: Piece, at: Vector3?, grow: number): boolean
	if not at then return false end
	local g = Vector3.new(grow, grow, grow)
	local lo, hi = pc.lo - g, pc.hi + g
	return at.X >= lo.X and at.Y >= lo.Y and at.Z >= lo.Z and at.X <= hi.X and at.Y <= hi.Y and at.Z <= hi.Z
end

local function show(pc: Piece)
	if not pc.out then return end
	pc.out = false
	if pc.home.Parent ~= nil or pc.home == workspace then pc.inst.Parent = pc.home end
end
local function hide(pc: Piece)
	if pc.out then return end
	pc.out = true
	pc.inst.Parent = hidden
end
local function forget(i: Instance)
	pieces[i] = nil
end

-- find the pieces (the map can be rebuilt: new instances come, old ones go)
local function consider(i: Instance, home: Instance)
	if pieces[i] then return end
	if not (i:IsA("Model") or i:IsA("Folder")) then return end
	local lo, hi, n = box(i)
	if n < MIN_PARTS and i:GetAttribute("ZonePiece") ~= true then return end -- (a small arena says so: Crate, 17 Nov)
	pieces[i] = { inst = i, home = home, lo = lo, hi = hi, boxT = os.clock(), away = 0, out = false }
	i.AncestryChanged:Connect(function(_, parent)
		local pc = pieces[i]
		if not pc then return end
		if parent == nil then forget(i) -- (the server took it away)
		elseif parent ~= hidden and parent ~= pc.home then pc.home = parent; pc.out = false end
	end)
end
local function scan()
	local map = workspace:FindFirstChild("Map")
	if not map then return end
	for _, c in map:GetChildren() do
		if c.Name ~= "Hub" and c.Name ~= "ArenaCopies" then consider(c, map) end
	end
	local hub = map:FindFirstChild("Hub")
	if hub then for _, c in hub:GetChildren() do consider(c, hub) end end
	local copies = map:FindFirstChild("ArenaCopies")
	if copies then for _, c in copies:GetChildren() do consider(c, copies) end end
end

local function showAll()
	for _, pc in pieces do show(pc) end
end

local lastScan, lastList = -math.huge, ""
local function step()
	local now = os.clock()
	if now - lastScan > 2 then lastScan = now; scan() end
	if workspace:GetAttribute("ZoneCull") == false then
		showAll()
		if lastList ~= "" then lastList = ""; script:SetAttribute("Hidden", "") end
		return
	end
	local ch = me.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local at = root and root.Position
	local cam = workspace.CurrentCamera
	local eye = cam and cam.CFrame.Position
	local arena = me:GetAttribute("Arena")
	local list = {}
	for i, pc in pieces do
		if not pc.out and now - pc.boxT > REBOX then
			pc.boxT = now
			local lo, hi, n = box(i)
			if n > 0 then pc.lo, pc.hi = lo, hi end
		end
		local m = (script:GetAttribute("Margin") :: number?) or MARGIN -- (Settings > GRAPHICS: VIEW DISTANCE)
		local keep = near(pc, at, m) or near(pc, eye, m) or (type(arena) == "string" and i.Name == arena)
		if keep then
			pc.away = 0
			show(pc)
		elseif not pc.out then
			if near(pc, at, m + SLACK) or near(pc, eye, m + SLACK) then
				pc.away = 0
			else
				if pc.away == 0 then pc.away = now end
				if now - pc.away >= HIDE_AFTER then hide(pc) end
			end
		end
		if pc.out then table.insert(list, i.Name) end
	end
	table.sort(list)
	local s = table.concat(list, ",")
	if s ~= lastList then lastList = s; script:SetAttribute("Hidden", s) end
end

-- before physics (a teleport lands on a floor that is there) and before drawing (the camera moved)
RunService.PreSimulation:Connect(step)
RunService.PreRender:Connect(step)
