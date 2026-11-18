--!strict
-- THE HIDDEN NPCS' SPOTS (18 Nov 2026): builds workspace.Map.Lore, one Model per NPC of Shared.LoreData, out of its
-- upload (Shared.LoreRigs: one MeshPart per moving piece, made by tools/roblox/lore_dump.mjs + lore_meshes.py from the
-- web's own lorenpcs.js) put together in the web's build pose at its spot. Outside every builder: HubRotunda, TrainingV2
-- and TrainingLot never touch Map.Lore, so their rebuilds keep the NPCs; run L.check() after one to see that each spot
-- still has its floor and its head room.
--   local L = require(game.ServerStorage.PolishBackup.LoreSpots:Clone())
--   print(L.build())          every NPC (or L.build({ "gary" }) for some)
--   print(L.check())          floor under each, nothing through their body, the find point reachable
-- Each Model: attribute LoreId; "Root" (hidden, on the floor under them, facing their way: the server's find point,
-- the client's frame, the TALK prompt's attachment PromptAt); the pieces (MeshParts named <id>_<piece>, attribute
-- Piece); extras (Gary's desk, Dale's machine's block, Smiles' balloon strings). No collisions on the NPCs themselves,
-- no queries anywhere (unshootable, like the hub's regulars); a desk and a machine block players with a hidden box.
-- Map.Lore has ZonePiece = true: ZoneCull puts the whole folder aside on a client that is far from the hub (in a match).
local InsertService = game:GetService("InsertService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Rigs = require(Shared:WaitForChild("LoreRigs")) :: any
local Data = require(Shared:WaitForChild("LoreData")) :: any

local L = {}

-- where each one is: at = the floor point under them (y is found by a ray from at + 6 down, unless top is given),
-- look = the way they face (flat), visit = where a tester stands to meet them (offset from at, studs), area = notes
L.SPOTS = {
	gary = { at = Vector3.new(-39, 245, -8472), look = Vector3.new(11, 0, -11), visit = Vector3.new(7, 0, -9),
		area = "back lot: the house's empty ground floor, the north-west corner, at his desk facing the room" },
	dale = { at = Vector3.new(-49.25, 240, -8579.7), look = Vector3.new(0, 0, 1), visit = Vector3.new(0, 0, -8),
		area = "back lot: behind the south-west container stack, his machine against its far end" },
	janitor = { at = Vector3.new(64, 226.4, -8283), look = Vector3.new(-6, 0, 8), visit = Vector3.new(-5, 0, 7),
		area = "the basement boiler room, mopping by the boiler" },
	smiles = { at = Vector3.new(48.7, 464, -9376), look = Vector3.new(-1, 0, 0), top = true, visit = Vector3.new(7, 0, 0),
		area = "the playground: on the Hook (the hanging pod), legs over the west edge, looking at the sunset" },
	todd = { at = Vector3.new(-90, 273.6, -8263), look = Vector3.new(1, 0, 0.6), visit = Vector3.new(6, 0, 2),
		area = "training: on top of the course's far tower (TOWER2), to one side of the grapple landing" },
	-- the story cast
	auntie = { at = Vector3.new(-51, 246.05, -8142), look = Vector3.new(0, 0, 1), visit = Vector3.new(0, -3, 7),
		area = "training: the course's watch steps, the top step, writing in her notebook" },
	lumps = { at = Vector3.new(-124, 304, -9448), look = Vector3.new(-1, 0, 0), visit = Vector3.new(8, 0, 0),
		area = "the playground: a low west block, facing the sunset" },
	gordo = { at = Vector3.new(76, 240, -8590), look = Vector3.new(0, 0, 1), visit = Vector3.new(0, 0, -8),
		area = "back lot: behind the south-east container stack" },
	mina = { at = Vector3.new(-39.3, 244.05, -8076), look = Vector3.new(0, 0, -1), visit = Vector3.new(-3, 0, -6),
		area = "training: by the locked roll-up door in the course's egg corridor, waiting at the gate" },
	sharon = { at = Vector3.new(-20, 256, -8471), look = Vector3.new(-10, 0, -9), visit = Vector3.new(-6, 0, -6),
		area = "back lot: the house's first floor, the north-east corner" },
	dumpling = { at = Vector3.new(-124, 240, -10004), look = Vector3.new(0.2, 0, 1), visit = Vector3.new(4, 0, 4),
		area = "the Rotunda: the gym's south corner by the punch bag, peeking at the ring (6 studs off Dune's walk)" },
	pallet_jack = { at = Vector3.new(13, 242, -8276), look = Vector3.new(-1, 0, 0), visit = Vector3.new(-7, 0, 0),
		area = "back lot: in the bay inside the garage, among the drums and tyres" },
	eotm = { at = Vector3.new(-120, 303, -8684), look = Vector3.new(0, 0, 1), visit = Vector3.new(3, 0, -4),
		area = "back lot: on top of the finish tower" },
	overtime = { at = Vector3.new(-150, 240, -8712), look = Vector3.new(1, 0, 1), visit = Vector3.new(7, 0, 7),
		area = "back lot: the far south-west corner by the back fence, watching" },
} :: { [string]: any }

local function folder(): Folder
	local map = workspace:WaitForChild("Map")
	local f = map:FindFirstChild("Lore")
	if not f then
		f = Instance.new("Folder")
		f.Name = "Lore"
		f.Parent = map
	end
	(f :: Folder):SetAttribute("ZonePiece", true)
	return f :: Folder
end

local rayParams = RaycastParams.new()
rayParams.FilterType = Enum.RaycastFilterType.Exclude
local function excludes(): { Instance }
	local out: { Instance } = {}
	local map = workspace:FindFirstChild("Map")
	local lore = map and map:FindFirstChild("Lore")
	if lore then table.insert(out, lore) end
	local hub = map and map:FindFirstChild("Hub")
	local bar = hub and hub:FindFirstChild("Barrier")
	if bar then table.insert(out, bar) end
	return out
end

-- the spot's frame: floor found by a ray (or the highest visible top under it, for a seat on a mesh)
function L.frame(id: string): (CFrame?, string?)
	local s = L.SPOTS[id]
	if not s then return nil, "no spot" end
	rayParams.FilterDescendantsInstances = excludes()
	local y = s.at.Y
	if s.top then
		local best = -math.huge
		for _, p in workspace:GetPartBoundsInBox(CFrame.new(s.at + Vector3.new(0, 1, 0)), Vector3.new(1, 8, 1)) do
			if p:IsA("BasePart") and p.Transparency < 1 and not p:IsDescendantOf(folder()) then
				best = math.max(best, p.Position.Y + p.Size.Y / 2)
			end
		end
		if best > -math.huge then y = best end
	else
		local r = workspace:Raycast(s.at + Vector3.new(0, 6, 0), Vector3.new(0, -14, 0), rayParams)
		if not r then return nil, "no floor under " .. tostring(s.at) end
		y = r.Position.Y
	end
	local look = Vector3.new(s.look.X, 0, s.look.Z).Unit
	local at = Vector3.new(s.at.X, y, s.at.Z)
	return CFrame.lookAt(at, at + look), nil
end

-- the joints' frames in the web's build pose, relative to the NPC's root (studs)
function L.restJoints(rig: any): { [string]: CFrame }
	local cf: { [string]: CFrame } = {}
	for _, j in rig.joints do
		local c = j.cf
		local rel = CFrame.new(c[1], c[2], c[3], c[4], c[5], c[6], c[7])
		cf[j.name] = if j.parent then cf[j.parent] * rel else rel
	end
	return cf
end

local cache: { [number]: Model } = {}
local function loadAsset(asset: number): (Model?, string?)
	if cache[asset] and cache[asset].Parent == nil then return cache[asset], nil end
	local ok, m = pcall(InsertService.LoadAsset, InsertService, asset)
	if not ok then return nil, "LoadAsset " .. asset .. ": " .. tostring(m) end
	cache[asset] = m
	return m, nil
end

local function plain(p: BasePart, collide: boolean?)
	p.Anchored = true
	p.CanCollide = collide == true
	p.CanQuery = false
	p.CanTouch = false
	p.Massless = true
end

-- Gary's desk: the web's is the map's (his things stand on a desk 0.73 m up, 1.18 m in front of him). a plain office
-- desk in the hub's kit colours: a top, a drawer pedestal on his right, a panel on his left, a modesty board
local function garyDesk(m: Model, base: CFrame)
	local desk = Instance.new("Model")
	desk.Name = "Desk"
	local TOP, H, CZ, W, D = Color3.fromRGB(176, 166, 150), 2.19, -3.51, 4.6, 2.7
	local function box(name: string, size: Vector3, at: Vector3, col: Color3, mat: Enum.Material?)
		local p = Instance.new("Part")
		p.Name = name; p.Size = size; p.CFrame = base * CFrame.new(at); p.Color = col
		p.Material = mat or Enum.Material.SmoothPlastic; p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
		plain(p, true)
		p.Parent = desk
		return p
	end
	box("Top", Vector3.new(W, 0.16, D), Vector3.new(0, H - 0.08, CZ), TOP)
	box("Pedestal", Vector3.new(1.3, H - 0.16, D - 0.2), Vector3.new(W / 2 - 0.7, (H - 0.16) / 2, CZ), Color3.fromRGB(104, 108, 116), Enum.Material.Metal)
	box("Panel", Vector3.new(0.14, H - 0.16, D - 0.2), Vector3.new(-W / 2 + 0.12, (H - 0.16) / 2, CZ), Color3.fromRGB(104, 108, 116), Enum.Material.Metal)
	box("Modesty", Vector3.new(W - 1.4, 1.1, 0.1), Vector3.new(-0.55, H - 0.75, CZ - D / 2 + 0.15), Color3.fromRGB(96, 100, 108), Enum.Material.Metal)
	for i = 0, 2 do -- drawer fronts, handles
		box("Drawer", Vector3.new(1.16, 0.56, 0.06), Vector3.new(W / 2 - 0.7, 0.42 + i * 0.62, CZ + D / 2 - 0.08), Color3.fromRGB(122, 126, 134), Enum.Material.Metal)
		box("Handle", Vector3.new(0.5, 0.06, 0.06), Vector3.new(W / 2 - 0.7, 0.52 + i * 0.62, CZ + D / 2 - 0.02), Color3.fromRGB(58, 60, 66), Enum.Material.Metal)
	end
	desk.Parent = m
end

-- one NPC, put together at its spot
function L.make(id: string): (Model?, string?)
	local rig = Rigs[id]
	local e = Data.get(id)
	if not rig or not e then return nil, "unknown " .. id end
	local base, why = L.frame(id)
	if not base then return nil, why end
	local src, err = loadAsset(rig.asset)
	if not src then return nil, err end
	local found: { [string]: MeshPart } = {}
	for _, d in (src :: Model):GetDescendants() do
		if d:IsA("MeshPart") and rig.pieces[d.Name] then found[d.Name] = d end
	end
	local m = Instance.new("Model")
	m.Name = "Lore_" .. id
	m:SetAttribute("LoreId", id)
	m:SetAttribute("Asset", rig.asset)
	local root = Instance.new("Part")
	root.Name = "Root"; root.Size = Vector3.new(1, 0.2, 1); root.CFrame = base; root.Transparency = 1
	plain(root)
	root.Parent = m
	m.PrimaryPart = root
	local s = L.SPOTS[id]
	if s.visit then root:SetAttribute("Visit", s.visit) end
	local joints = L.restJoints(rig)
	-- Smiles' balloons sit over his glove at rest (the web puts them there every frame)
	if id == "smiles" and joints.armL then
		local armL
		for _, j in rig.joints do if j.name == "armL" then armL = j end end
		local glove = joints.armL * CFrame.new(Vector3.new(0.38, -0.05, -0.53) * armL.k)
		for i, b in { { -0.25, 0.1, 1.6 }, { 0.05, 0.3, 1.85 }, { 0.3, 0.05, 1.5 } } do
			if joints["balloon" .. i] then joints["balloon" .. i] = CFrame.new(glove.Position + Vector3.new(b[1], b[3], b[2]) * 3) end
		end
	end
	local missing = {}
	for name, pc in rig.pieces do
		local src2 = found[name]
		if not src2 then table.insert(missing, name); continue end
		local p = src2:Clone()
		p.Name = name
		p:SetAttribute("Piece", name)
		p:SetAttribute("Joint", pc.joint)
		p.Color = Color3.new(1, 1, 1) -- (vertex colours multiply with Color)
		p.Material = if pc.glass then Enum.Material.Glass else Enum.Material.SmoothPlastic
		p.Transparency = if pc.glass then 0.55 else 0
		p.CastShadow = not pc.glass
		p.CFrame = base * joints[pc.joint] * CFrame.new(pc.at[1], pc.at[2], pc.at[3])
		plain(p)
		p.Parent = m
	end
	-- the TALK prompt (the client shows the next lines when it is used; finding them needs only coming near)
	local pa = Instance.new("Attachment")
	pa.Name = "PromptAt"
	pa.Position = Vector3.new(0, 4.6, 0)
	pa.Parent = root
	local pr = Instance.new("ProximityPrompt")
	pr.Name = "Talk"; pr.ActionText = "Talk"; pr.ObjectText = e.name
	pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX; pr.HoldDuration = 0
	pr.MaxActivationDistance = 11; pr.RequiresLineOfSight = false
	pr.Exclusivity = Enum.ProximityPromptExclusivity.OnePerButton
	pr.Parent = pa
	if id == "gary" then garyDesk(m, base) end
	if id == "dale" then -- the machine's hidden box: you can't walk through it
		local b = Instance.new("Part")
		b.Name = "MachineBlock"; b.Size = Vector3.new(3.0, 5.7, 2.5); b.Transparency = 1
		b.CFrame = base * CFrame.new(-0.75, 2.85, -2.22)
		plain(b, true)
		b.Parent = m
	end
	if id == "smiles" then -- the balloons' strings: beams from his glove to each knot (LoreLife moves the ends)
		local hand = m:FindFirstChild("smiles_armL") :: BasePart?
		local armL
		for _, j in rig.joints do if j.name == "armL" then armL = j end end
		if hand and armL then
			local g = Instance.new("Attachment")
			g.Name = "Glove"
			g.Parent = hand
			g.WorldCFrame = base * joints.armL * CFrame.new(Vector3.new(0.38, -0.05, -0.53) * armL.k)
			for i = 1, 3 do
				local bp = m:FindFirstChild("smiles_balloon" .. i) :: BasePart?
				if bp then
					local k = Instance.new("Attachment")
					k.Name = "Knot"
					k.Parent = bp
					k.WorldPosition = (base * joints["balloon" .. i] * CFrame.new(0, -0.72, 0)).Position
					local bm = Instance.new("Beam")
					bm.Name = "String"; bm.Attachment0 = g; bm.Attachment1 = k
					bm.Width0 = 0.07; bm.Width1 = 0.07; bm.FaceCamera = true; bm.Segments = 1
					bm.Color = ColorSequence.new(Color3.fromRGB(236, 234, 228)); bm.LightInfluence = 1
					bm.Transparency = NumberSequence.new(0)
					bm.Parent = bp
				end
			end
		end
	end
	if #missing > 0 then return m, "missing pieces: " .. table.concat(missing, ", ") end
	return m, nil
end

-- the Tall Guy From HR's template (ServerStorage.LoreHR): his pieces in the web's build pose round a hidden Root at his
-- feet (HrGuy.server clones it into Map.Lore while he visits; HrGuy.client poses him from his Pose seed)
function L.hr(): string
	local rig = Rigs.hr
	local src, err = loadAsset(rig.asset)
	if not src then return "HR: " .. tostring(err) end
	local m = Instance.new("Model")
	m.Name = "LoreHR"
	local root = Instance.new("Part")
	root.Name = "Root"; root.Size = Vector3.new(1, 0.2, 1); root.CFrame = CFrame.identity; root.Transparency = 1
	plain(root)
	root.Parent = m
	m.PrimaryPart = root
	local joints = L.restJoints(rig)
	local n = 0
	for _, d in (src :: Model):GetDescendants() do
		local pc = d:IsA("MeshPart") and rig.pieces[d.Name]
		if pc then
			local p = (d :: MeshPart):Clone()
			p.Color = Color3.new(1, 1, 1); p.Material = Enum.Material.SmoothPlastic; p.CastShadow = true
			p:SetAttribute("Joint", pc.joint)
			p.CFrame = joints[pc.joint] * CFrame.new(pc.at[1], pc.at[2], pc.at[3])
			plain(p)
			p.Parent = m
			n += 1
		end
	end
	local old = game:GetService("ServerStorage"):FindFirstChild("LoreHR")
	if old then old:Destroy() end
	m.Parent = game:GetService("ServerStorage")
	return ("LoreHR: %d pieces"):format(n)
end

function L.build(ids: { string }?): string
	local f = folder()
	local out = {}
	for _, id in (ids or Data.ORDER) do
		if not L.SPOTS[id] then continue end
		local old = f:FindFirstChild("Lore_" .. id)
		local m, why = L.make(id)
		if m then
			if old then old:Destroy() end
			m.Parent = f
			table.insert(out, id .. (if why then " (" .. why .. ")" else "") .. " at " .. tostring(m:GetPivot().Position))
		else
			table.insert(out, id .. ": NOT BUILT, " .. tostring(why))
		end
	end
	return "Lore.build: " .. table.concat(out, "; ")
end

-- each spot: the floor still under the root, nothing solid through the body, the find point reachable from the visit
-- spot (a ray from the visitor's feet height to the root finds no wall... a seat on an edge is checked from its visit)
function L.check(): string
	local f = folder()
	local probs, lines = 0, {}
	rayParams.FilterDescendantsInstances = excludes()
	for _, id in Data.ORDER do
		if not L.SPOTS[id] then continue end
		local m = f:FindFirstChild("Lore_" .. id) :: Model?
		local s = L.SPOTS[id]
		if not m then probs += 1; table.insert(lines, id .. ": not built"); continue end
		local root = m:FindFirstChild("Root") :: BasePart
		local note = {}
		local want = L.frame(id)
		if not want then probs += 1; table.insert(note, "NO FLOOR")
		elseif (want.Position - root.Position).Magnitude > 0.6 then probs += 1; table.insert(note, ("FLOOR MOVED %.1f"):format((want.Position - root.Position).Magnitude)) end
		-- body: a box round the person (not the props), solid map parts inside it
		local op = OverlapParams.new()
		op.FilterType = Enum.RaycastFilterType.Exclude
		op.FilterDescendantsInstances = excludes()
		local hits = {}
		-- (a real probe part: GetPartBoundsInBox would count a turned wall by its whole square box)
		local probe = Instance.new("Part")
		probe.Anchored = true; probe.CanCollide = false; probe.CanQuery = false; probe.Transparency = 1
		probe.Size = Vector3.new(1.6, 5.6, 1.6); probe.CFrame = root.CFrame * CFrame.new(0, 3.6, 0)
		probe.Parent = workspace
		for _, p in workspace:GetPartsInPart(probe, op) do
			if p:IsA("BasePart") and p.CanCollide and p.Transparency < 1 then table.insert(hits, p.Name) end
		end
		probe:Destroy()
		if #hits > 0 then probs += 1; table.insert(note, "THROUGH: " .. table.concat(hits, ",")) end
		-- the visit spot: a floor there, and a clear line to them
		local v = root.Position + s.visit
		local fl = workspace:Raycast(v + Vector3.new(0, 4, 0), Vector3.new(0, -10, 0), rayParams)
		if not fl then probs += 1; table.insert(note, "NO FLOOR AT VISIT") end
		local eye = v + Vector3.new(0, 4.5, 0)
		local to = root.Position + Vector3.new(0, 3.5, 0)
		local wall = workspace:Raycast(eye, to - eye, rayParams)
		if wall and (wall.Position - to).Magnitude > 1.5 then probs += 1; table.insert(note, "WALL " .. wall.Instance.Name) end
		table.insert(lines, ("%s %s"):format(id, if #note > 0 then table.concat(note, " ") else "ok"))
	end
	return ("Lore.check: %d problem(s). %s"):format(probs, table.concat(lines, " | "))
end

return L
