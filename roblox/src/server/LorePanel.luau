--!strict
-- THE CODE PANELS' MAKE (20 Nov 2026: three new hubs, one panel in each; the hub session's markers). One chunky
-- terminal: a plinth, the cabinet with one trim band, a console leaning toward you with a dim screen and a row of keys,
-- its prompt ("Code": CodePanel.client opens the screen) and its Show spot (where a code's NPC stops in its cutscene,
-- LoreLife.client). Every panel is a Model named CodePanel tagged CodePanel (CollectionService): the screen, the
-- server's nearness check and the cutscene use the one nearest the player.
--   LorePanel.make(base, parent, show?, scan?) -> (Model, string)
--     base   the floor point under its front middle; its LookVector is the way the screen faces (where you stand)
--     show   where the NPC stops, in the panel's frame (x right, -z out toward you); nil = picked here: the clearer of
--            its two sides (5.6 studs out; 0.8, else 1.8, else 2.6 in front, for a panel flush on a wall), else the
--            clearest 3 x 3 near where you stand, from the boxes of every
--            visible part under `scan` (meshes with queries off count too)
--   LorePanel.fromSpots() -> string
--     every CodePanelSpot under Map.Hub (a hub builder's marker: a Part with its bottom-centre on the floor, its
--     LookVector out of the screen, attribute Hub) gets a panel as its sibling unless one is there. LoreNPCs.server
--     runs it at start and every few seconds, so a hub rebuild that wipes its Scenery gets its panel back by itself
local CollectionService = game:GetService("CollectionService")

local LorePanel = {}
local TAG = "CodePanel"
local DARK, BODY, TRIM = Color3.fromRGB(70, 74, 82), Color3.fromRGB(184, 178, 166), Color3.fromRGB(196, 162, 88)

local function plain(p: BasePart, collide: boolean?)
	p.Anchored = true
	p.CanCollide = collide == true
	p.CanQuery = false
	p.CanTouch = false
	p.Massless = true
end

-- every visible part's box under scan, near a point, floors left out
local function boxesNear(scan: Instance?, at: Vector3, skip: Instance?): { { Vector3 } }
	local out = {}
	if not scan then return out end
	for _, p in scan:GetDescendants() do
		if p:IsA("BasePart") and p.Transparency < 1 and (p.Position - at).Magnitude < 30 and not (skip and p:IsDescendantOf(skip)) then
			local cf, sz = p.CFrame, p.Size / 2
			local ex = Vector3.new(
				math.abs(cf.RightVector.X) * sz.X + math.abs(cf.UpVector.X) * sz.Y + math.abs(cf.LookVector.X) * sz.Z,
				math.abs(cf.RightVector.Y) * sz.X + math.abs(cf.UpVector.Y) * sz.Y + math.abs(cf.LookVector.Y) * sz.Z,
				math.abs(cf.RightVector.Z) * sz.X + math.abs(cf.UpVector.Z) * sz.Y + math.abs(cf.LookVector.Z) * sz.Z)
			if p.Position.Y + ex.Y > at.Y + 0.2 then table.insert(out, { p.Position - ex, p.Position + ex }) end
		end
	end
	return out
end
local function room(boxes: { { Vector3 } }, w: Vector3, half: number): number
	local lo, hi = w + Vector3.new(-half, 0.2, -half), w + Vector3.new(half, 6.6, half)
	local near = math.huge
	for _, b in boxes do
		if b[1].X < hi.X and b[2].X > lo.X and b[1].Y < hi.Y and b[2].Y > lo.Y and b[1].Z < hi.Z and b[2].Z > lo.Z then return -1 end
		if b[1].Y < hi.Y and b[2].Y > lo.Y then
			local dx = math.max(b[1].X - w.X, 0, w.X - b[2].X)
			local dz = math.max(b[1].Z - w.Z, 0, w.Z - b[2].Z)
			near = math.min(near, math.sqrt(dx * dx + dz * dz))
		end
	end
	return near
end
local function pickShow(base: CFrame, scan: Instance?, skip: Instance?): Vector3
	local boxes = boxesNear(scan, base.Position, skip)
	local best, bestRoom = nil, -1
	-- (its two sides, a step further out each time: a panel flush on a wall has the wall's box under 0.8 out)
	for _, z in { -0.8, -1.8, -2.6 } do
		for _, c in { Vector3.new(5.6, 0, z), Vector3.new(-5.6, 0, z) } do
			local r = room(boxes, (base * CFrame.new(c)).Position, 1.5)
			if r > bestRoom then best, bestRoom = c, r end
		end
		if best and bestRoom >= 1 then return best end
	end
	for x = -4, 4, 0.5 do
		for z = -2, -9, -0.5 do
			local c = Vector3.new(x, 0, z)
			if math.abs(z + 4.5) + math.abs(x) < 2.8 or c.Magnitude < 3 then continue end
			local r = room(boxes, (base * CFrame.new(c)).Position, 1.5)
			if r > bestRoom then best, bestRoom = c, r end
		end
	end
	return best or Vector3.new(5.6, 0, -0.8)
end

function LorePanel.make(base: CFrame, parent: Instance, show: Vector3?, scan: Instance?): (Model, string)
	local m = Instance.new("Model")
	m.Name = "CodePanel"
	local function box(name: string, size: Vector3, cf: CFrame, col: Color3, collide: boolean, mat: Enum.Material?): Part
		local p = Instance.new("Part")
		p.Name = name; p.Size = size; p.CFrame = cf; p.Color = col
		p.Material = mat or Enum.Material.SmoothPlastic; p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
		plain(p, collide)
		p.CastShadow = true
		p.Parent = m
		return p
	end
	box("Plinth", Vector3.new(3.4, 0.5, 2.6), base * CFrame.new(0, 0.25, 0.2), DARK, true, Enum.Material.Metal)
	box("Cabinet", Vector3.new(2.6, 3.4, 1.7), base * CFrame.new(0, 2.2, 0.4), BODY, true)
	box("Trim", Vector3.new(2.64, 0.2, 1.74), base * CFrame.new(0, 3.35, 0.4), TRIM, false)
	local head = base * CFrame.new(0, 4.2, 0.15) * CFrame.Angles(math.rad(-28), 0, 0)
	box("Console", Vector3.new(3.0, 0.55, 2.6), head, BODY, true)
	local screen = box("Screen", Vector3.new(2.4, 0.06, 1.25), head * CFrame.new(0, 0.29, 0.5), Color3.fromRGB(42, 62, 66), false)
	local glow = Instance.new("SurfaceLight")
	glow.Face = Enum.NormalId.Top; glow.Color = Color3.fromRGB(170, 214, 210); glow.Brightness = 0.35; glow.Range = 5; glow.Angle = 70
	glow.Parent = screen
	for i = -2, 2 do
		box("Key", Vector3.new(0.4, 0.1, 0.32), head * CFrame.new(i * 0.5, 0.31, -0.7), DARK, false, Enum.Material.Metal)
	end
	local root = box("Root", Vector3.new(1, 0.2, 1), base * CFrame.new(0, 0.1, 0), DARK, false)
	root.Transparency = 1
	local pa = Instance.new("Attachment")
	pa.Name = "PromptAt"
	pa.Parent = root -- (parent first: WorldPosition on a loose attachment is kept as its offset)
	pa.WorldPosition = (head * CFrame.new(0, 1.2, 0)).Position
	local pr = Instance.new("ProximityPrompt")
	pr.Name = "Code"; pr.ActionText = "Code"; pr.ObjectText = ""
	pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX; pr.HoldDuration = 0
	pr.MaxActivationDistance = 9; pr.RequiresLineOfSight = false
	pr.Exclusivity = Enum.ProximityPromptExclusivity.OnePerButton
	pr.Parent = pa
	m.PrimaryPart = root
	m.WorldPivot = base
	-- the Show spot: given, or the clearer one here; on the floor, facing where you stand
	local sc = show or pickShow(base, scan, m)
	local you = (base * CFrame.new(0, 0, -4.5)).Position
	local sp = (base * CFrame.new(sc)).Position
	local rp = RaycastParams.new()
	rp.FilterType = Enum.RaycastFilterType.Exclude
	rp.FilterDescendantsInstances = { m }
	local sh = workspace:Raycast(sp + Vector3.new(0, 6, 0), Vector3.new(0, -14, 0), rp)
	local spAt = Vector3.new(sp.X, if sh then sh.Position.Y else base.Y, sp.Z)
	local showP = box("Show", Vector3.new(1, 0.2, 1), CFrame.lookAt(spAt, Vector3.new(you.X, spAt.Y, you.Z)), DARK, false)
	showP.Transparency = 1
	m.Parent = parent
	CollectionService:AddTag(m, TAG)
	return m, ("CodePanel at %s facing %s; spawn-ins at %s (local %s)%s"):format(tostring(base.Position), tostring(base.LookVector),
		tostring(spAt), tostring(sc), if sh then "" else " (NO FLOOR there)")
end

-- the hubs' markers: a panel beside each that hasn't one
function LorePanel.fromSpots(): string
	local map = workspace:FindFirstChild("Map")
	local hub = map and map:FindFirstChild("Hub")
	if not hub then return "no Map.Hub" end
	local out = {}
	for _, spot in hub:GetDescendants() do
		if not (spot:IsA("BasePart") and spot.Name == "CodePanelSpot") then continue end
		local parent = spot.Parent :: Instance
		local have = false
		for _, c in parent:GetChildren() do
			if c.Name == "CodePanel" and c:IsA("Model") and c:GetAttribute("Spot") == spot:GetFullName() then have = true end
		end
		if have then continue end
		local lv = spot.CFrame.LookVector
		local look = Vector3.new(lv.X, 0, lv.Z)
		look = if look.Magnitude > 1e-3 then look.Unit else Vector3.new(0, 0, -1)
		local at = spot.Position - Vector3.new(0, spot.Size.Y / 2, 0)
		-- (the hub's own folder: what the Show spot keeps clear of)
		local scan: Instance = spot
		while scan.Parent and scan.Parent ~= hub do scan = scan.Parent :: Instance end
		local m, report = LorePanel.make(CFrame.lookAt(at, at + look), parent, nil, scan)
		m:SetAttribute("Spot", spot:GetFullName())
		m:SetAttribute("Hub", spot:GetAttribute("Hub"))
		table.insert(out, tostring(spot:GetAttribute("Hub")) .. ": " .. report)
	end
	return if #out > 0 then table.concat(out, " | ") else "no new panels"
end

-- every panel there is (the hubs' and the ring's), and the one nearest a point
function LorePanel.all(): { Model }
	local out = {}
	for _, m in CollectionService:GetTagged(TAG) do
		if m:IsA("Model") and m:IsDescendantOf(workspace) then table.insert(out, m) end
	end
	-- (the ring's, if it was built before the tag)
	local map = workspace:FindFirstChild("Map")
	local l = map and map:FindFirstChild("Lore")
	local old = l and l:FindFirstChild("CodePanel")
	if old and old:IsA("Model") and not table.find(out, old) then table.insert(out, old) end
	return out
end
function LorePanel.nearest(at: Vector3): Model?
	local best, bd = nil, math.huge
	for _, m in LorePanel.all() do
		local d = (m:GetPivot().Position - at).Magnitude
		if d < bd then best, bd = m, d end
	end
	return best
end

return LorePanel
