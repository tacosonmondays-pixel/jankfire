-- PolishBackup.HubEgg (18 Nov 2026): places the hub egg, the web game's player as a mannequin on its plinth, hidden in
-- Hub v3 (what finding it does: ServerScriptService.Jankfire.HubEgg, repo server/HubEgg.server.luau).
--   local E = require(game.ServerStorage.PolishBackup.HubEgg:Clone()); print(E.build()); print(E.check())
-- The model is one upload (E.ASSET, from tools/roblox/hub_egg_dump.mjs -> hub_egg_mannequin.py): three MeshParts,
-- egg_body (the mannequin), egg_stand (the plinth) and egg_shell (the outline everyone else saw on a web player: inside
-- out, so only its rim shows). Their colours are baked vertex colours (Color stays white). It lands in the web's own
-- frame, 3 studs to the web metre: the mannequin faces -Z.
-- E.SPOT: the floor point under the plinth's middle, turned the way the mannequin faces (its LookVector). It lives in
-- its own folder, workspace.Map.Hub.HubEgg, outside the hub's Rotunda (the hub's R.build never touches it). Every part
-- carries Built = "HubEgg".
local InsertService = game:GetService("InsertService")

local E = {}
E.PUSH = 2
E.ASSET = 139602935358805 -- HubEggMannequin1 (hub_egg_1.glb), Approved 18 Nov
E.SPOT = CFrame.new(0, 0, 0) -- (set from the hub session's nook)
-- the recording that plays for the finder (Found): Pro Sound Effects' "Musical Toy Top 1" (Roblox's licensed library),
-- the run of toy-top notes from 1.3 to 3.0 s (measured silently: AudioAnalyzer onsets 1.36, 1.62, 1.79, 2.13, 2.45, 2.60)
E.SOUND = "rbxassetid://9117040176"
E.SOUND_REGION = NumberRange.new(1.3, 3.0)
E.SOUND_VOLUME = 0.35
E.OUTLINE = true -- the outline shell (false: hidden)
E.TOUCH = Vector3.new(6.2, 8.6, 6.2) -- the unseen box round the plinth that finds it

local function folderOf(): Folder
	local hub = workspace:WaitForChild("Map"):WaitForChild("Hub")
	local f = hub:FindFirstChild("HubEgg")
	if not f then
		f = Instance.new("Folder")
		f.Name = "HubEgg"
		f.Parent = hub
	end
	return f :: Folder
end

function E.remove()
	local hub = workspace:FindFirstChild("Map") and workspace.Map:FindFirstChild("Hub")
	local f = hub and hub:FindFirstChild("HubEgg")
	if f then f:Destroy() end
end

-- the upload, loaded: { body, stand, shell } MeshParts in one Model, its pivot at the plinth's bottom middle
local function load(): (Model?, string?)
	local ok, c = pcall(InsertService.LoadAsset, InsertService, E.ASSET)
	if not ok then return nil, "LoadAsset: " .. tostring(c) end
	local m = Instance.new("Model")
	m.Name = "Mannequin"
	local found = {}
	for _, d in (c :: Instance):GetDescendants() do
		if d:IsA("MeshPart") and (d.Name == "egg_body" or d.Name == "egg_stand" or d.Name == "egg_shell") then
			found[d.Name] = d
		end
	end
	if not (found.egg_body and found.egg_stand and found.egg_shell) then
		(c :: Instance):Destroy()
		return nil, "the upload is missing a piece"
	end
	for name, p in found do
		p.Parent = m
		p.Anchored = true
		p.Color = Color3.new(1, 1, 1) -- (the colours are in the mesh)
		p.Material = Enum.Material.SmoothPlastic
		p.Reflectance = 0
		p.CanTouch = false
		p:SetAttribute("Built", "HubEgg")
		if name == "egg_shell" then
			p.CanCollide = false
			p.CanQuery = false
			p.CastShadow = false
			p.Transparency = if E.OUTLINE then 0 else 1
		else
			p.CanCollide = true
			p.CanQuery = true
			p.CastShadow = true
		end
	end
	;(c :: Instance):Destroy()
	local st = found.egg_stand :: MeshPart
	m.WorldPivot = CFrame.new(st.Position.X, st.Position.Y - st.Size.Y / 2, st.Position.Z)
	return m, nil
end

function E.build(spot: CFrame?): string
	spot = spot or E.SPOT
	E.remove()
	local m, why = load()
	if not m then return "STOPPED: " .. tostring(why) end
	local f = folderOf()
	f:SetAttribute("Built", "HubEgg")
	f:SetAttribute("Asset", E.ASSET)
	f:SetAttribute("Push", E.PUSH)
	m:PivotTo(spot :: CFrame)
	m.Parent = f
	local t = Instance.new("Part")
	t.Name = "Touch"
	t.Anchored = true
	t.CanCollide = false
	t.CanQuery = false
	t.CanTouch = true
	t.CastShadow = false
	t.Transparency = 1
	t.Size = E.TOUCH
	t.CFrame = (spot :: CFrame) * CFrame.new(0, E.TOUCH.Y / 2, 0)
	t:SetAttribute("Built", "HubEgg")
	local pr = Instance.new("ProximityPrompt")
	pr.ActionText = "Touch"
	pr.ObjectText = ""
	pr.HoldDuration = 0.25
	pr.MaxActivationDistance = 9
	pr.RequiresLineOfSight = false
	pr.Parent = t
	local s = Instance.new("Sound")
	s.Name = "Found"
	s.SoundId = E.SOUND
	s.Volume = E.SOUND_VOLUME
	s.PlaybackRegionsEnabled = true
	s.PlaybackRegion = E.SOUND_REGION
	s.Parent = t
	t.Parent = f
	local _, size = m:GetBoundingBox()
	return ("hub egg built at %s, facing %s, %.1f x %.1f x %.1f studs"):format(
		tostring((spot :: CFrame).Position), tostring((spot :: CFrame).LookVector), size.X, size.Y, size.Z)
end

-- what touches it, what it stands on, how far you can see it from: lines to read
function E.check(): string
	local hub = workspace:FindFirstChild("Map") and workspace.Map:FindFirstChild("Hub")
	local f = hub and hub:FindFirstChild("HubEgg")
	local m = f and f:FindFirstChild("Mannequin")
	if not (m and m:IsA("Model")) then return "no hub egg" end
	local out = {}
	local cf, size = m:GetBoundingBox()
	local op = OverlapParams.new()
	op.FilterType = Enum.RaycastFilterType.Exclude
	op.FilterDescendantsInstances = { f }
	-- (things inside its box, a touch smaller: a wall through the mannequin, a lamp in its head)
	local inside = {}
	for _, p in workspace:GetPartBoundsInBox(cf, size - Vector3.new(0.4, 0.4, 0.4), op) do
		if p.Transparency < 1 and p.CanCollide then table.insert(inside, p:GetFullName()) end
	end
	table.insert(out, ("in its box: %d%s"):format(#inside, if #inside > 0 then " (" .. table.concat(inside, ", ", 1, math.min(#inside, 5)) .. ")" else ""))
	-- (the floor under the plinth's middle)
	local rp = RaycastParams.new()
	rp.FilterType = Enum.RaycastFilterType.Exclude
	rp.FilterDescendantsInstances = { f }
	local base = m:GetPivot().Position
	local r = workspace:Raycast(base + Vector3.new(0, 2, 0), Vector3.new(0, -6, 0), rp)
	table.insert(out, if r then ("floor %.2f under the plinth (%s)"):format(base.Y - r.Position.Y, r.Instance:GetFullName()) else "NO FLOOR under the plinth")
	-- (head room)
	local up = workspace:Raycast(base + Vector3.new(0, 1, 0), Vector3.new(0, 30, 0), rp)
	table.insert(out, if up then ("ceiling %.1f over the plinth's foot"):format(up.Position.Y - base.Y) else "open above")
	return table.concat(out, "\n")
end

return E
