-- PolishBackup.PetImport (18 Nov 2026): builds the PETS' models from their uploads (tools/roblox/pets_models.py; doc
-- FLAIR.md "Pets"). run in Edit:
--   local I = require(game.ServerStorage.PolishBackup.PetImport:Clone()); print(I.build()); print(I.check())
--   (I.build({ "mannequin" }): only those pets; the kennel is always rebuilt)
-- what it makes:
--   ReplicatedStorage.JankfirePets.<id> (mannequin, slug, dog): a Model, PrimaryPart "Root" (unseen, at the pet's middle
--     on the floor, facing -Z, at the world's origin), its MeshParts placed round it, each with the joint it turns on
--     (attributes Role, Joint, Side, Front, N: client/PetRig.luau reads them), colours baked in the mesh (Color white),
--     no collisions, queries or touches; "Found" (Sound) in it: the recording the finder hears (FlairServer plays it)
--   ServerStorage.JankfirePetKit.Kennel: the meat dog's kennel (PetSecrets.server puts one in every Gut arena): the
--     kennel mesh and an unseen solid box round its walls (stops you and shots, like any wall; the bowl doesn't)
-- the uploads land in the file's own frame (rbxglb.turn_for_roblox): each piece's middle is where pets_layout.json says,
-- so the pieces are put there exactly (and checked: every piece must agree on the upload's offset)
local InsertService = game:GetService("InsertService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local I = {}
I.ASSETS = { mannequin = 93735950095362, slug = 77552236809847, dog = 75123181576256, kennel = 114456936297774 }
-- the find's recording per pet (Roblox's licensed library, Pro Sound Effects): id, the stretch played, volume
I.SOUNDS = {} :: { [string]: { id: string, from: number?, to: number?, volume: number } }
-- (tools/roblox/pets_import_luau.py writes this from pets_layout.json)
-- LAYOUT BEGIN
I.LAYOUT = {
	mannequin = { size = Vector3.new(0.637, 1.853, 0.737), feet = 0.0950, pieces = {
		pm_body = { role = "body", joint = Vector3.new(0, 0, 0), centre = Vector3.new(-0.0868, 0.9144, -0.2023) },
		pm_shell = { role = "shell", joint = Vector3.new(0, 0, 0), centre = Vector3.new(-0.0884, 0.9208, -0.1952) },
	} },
	slug = { size = Vector3.new(1.564, 1.359, 3.089), pieces = {
		ps_mask = { role = "mask", joint = Vector3.new(0, 0.425, -0.731), centre = Vector3.new(0, 0.68, -0.799) },
		ps_seg1 = { role = "seg", joint = Vector3.new(0, 0.4369, -0.357), centre = Vector3.new(0, 0.5032, -0.3634), n = 1 },
		ps_seg2 = { role = "seg", joint = Vector3.new(0, 0.3869, 0.17), centre = Vector3.new(0, 0.4153, 0.1636), n = 2 },
		ps_seg3 = { role = "seg", joint = Vector3.new(0, 0.3227, 0.663), centre = Vector3.new(0, 0.3374, 0.6566), n = 3 },
		ps_seg4 = { role = "seg", joint = Vector3.new(0, 0.2441, 1.0795), centre = Vector3.new(0, 0.2441, 1.1496), n = 4 },
		ps_armL = { role = "arm", joint = Vector3.new(-0.425, 0.4675, -0.527), centre = Vector3.new(-0.5738, 0.2812, -1.0516), side = -1 },
		ps_armR = { role = "arm", joint = Vector3.new(0.425, 0.4675, -0.527), centre = Vector3.new(0.5738, 0.2812, -1.0516), side = 1 },
	} },
	dog = { size = Vector3.new(0.895, 1.256, 2.664), pieces = {
		pd_body = { role = "body", joint = Vector3.new(0, 0.576, 0), centre = Vector3.new(0, 0.6097, 0.1324) },
		pd_head = { role = "head", joint = Vector3.new(0, 0.784, -0.688), centre = Vector3.new(0, 0.944, -0.97) },
		pd_tail = { role = "tail", joint = Vector3.new(0, 0.608, 0.992), centre = Vector3.new(0, 0.76, 1.112) },
		pd_legFL = { role = "leg", joint = Vector3.new(-0.192, 0.44, -0.336), centre = Vector3.new(-0.192, 0.254, -0.376), side = -1, front = true },
		pd_legFR = { role = "leg", joint = Vector3.new(0.192, 0.44, -0.336), centre = Vector3.new(0.192, 0.254, -0.376), side = 1, front = true },
		pd_legBL = { role = "leg", joint = Vector3.new(-0.192, 0.44, 0.576), centre = Vector3.new(-0.192, 0.254, 0.536), side = -1, front = false },
		pd_legBR = { role = "leg", joint = Vector3.new(0.192, 0.44, 0.576), centre = Vector3.new(0.192, 0.254, 0.536), side = 1, front = false },
	} },
	kennel = { size = Vector3.new(3.367, 3.26, 4.135), door = Vector3.new(0, 0, -1.9), pieces = {
		pk_kennel = { role = "kennel", joint = Vector3.new(0, 0, 0), centre = Vector3.new(0, 1.63, -0.2925) },
	} },
}
-- LAYOUT END

local function load(id: number): (Folder?, string?)
	local ok, c = pcall(InsertService.LoadAsset, InsertService, id)
	if not ok then return nil, "LoadAsset " .. id .. ": " .. tostring(c) end
	return c :: any, nil
end

-- the upload's MeshParts by name, placed where the layout says, around a Root at the origin. -> the model, the worst miss
local function assemble(pet: string, name: string): (Model?, string)
	local lay = I.LAYOUT[pet]
	local c, err = load(I.ASSETS[pet])
	if not c then return nil, err :: string end
	local m = Instance.new("Model")
	m.Name = name
	local root = Instance.new("Part")
	root.Name = "Root"
	root.Size = Vector3.new(0.2, 0.2, 0.2)
	root.Transparency = 1
	root.Anchored = true
	root.CanCollide = false; root.CanQuery = false; root.CanTouch = false
	root.CFrame = CFrame.new()
	root.Parent = m
	m.PrimaryPart = root
	local off: Vector3? = nil
	local worst = 0
	local n = 0
	for _, d in (c :: Instance):GetDescendants() do
		local p = d:IsA("MeshPart") and lay.pieces[d.Name]
		if p then
			local mp = d :: MeshPart
			local o = mp.Position - p.centre
			if not off then off = o end
			worst = math.max(worst, (o - (off :: Vector3)).Magnitude)
			mp.Parent = m
			mp.CFrame = CFrame.new(p.centre)
			mp.Anchored = true
			mp.CanCollide = false; mp.CanQuery = false; mp.CanTouch = false
			mp.Massless = true
			mp.Color = Color3.new(1, 1, 1) -- (the colours are in the mesh)
			mp.Material = Enum.Material.SmoothPlastic
			mp.Reflectance = 0
			mp.CastShadow = p.role ~= "shell"
			pcall(function() (mp :: any).DoubleSided = false end) -- (the outline shell is inside out: one side only shows its rim)
			mp:SetAttribute("Role", p.role)
			mp:SetAttribute("Joint", p.joint)
			if p.side then mp:SetAttribute("Side", p.side) end
			if p.front ~= nil then mp:SetAttribute("Front", p.front) end
			if p.n then mp:SetAttribute("N", p.n) end
			n += 1
		end
	end
	;(c :: Instance):Destroy()
	local want = 0
	for _ in lay.pieces do want += 1 end
	if n ~= want then m:Destroy(); return nil, ("%s: %d of %d pieces in the upload"):format(pet, n, want) end
	if lay.feet then m:SetAttribute("Feet", lay.feet) end
	return m, ("%s: %d pieces, worst miss %.3f"):format(pet, n, worst)
end

local function sound(pet: string, into: Instance)
	local s = I.SOUNDS[pet]
	if not s then return end
	local snd = Instance.new("Sound")
	snd.Name = "Found"
	snd.SoundId = s.id
	snd.Volume = s.volume
	if s.from and s.to then
		snd.PlaybackRegionsEnabled = true
		snd.PlaybackRegion = NumberRange.new(s.from, s.to)
	end
	snd.Parent = into
end

function I.build(only: { string }?): string
	local out = {}
	local kit = ReplicatedStorage:FindFirstChild("JankfirePets")
	if not kit then
		kit = Instance.new("Folder")
		kit.Name = "JankfirePets"
		kit.Parent = ReplicatedStorage
	end
	for _, pet in only or { "mannequin", "slug", "dog" } do
		local m, msg = assemble(pet, pet)
		table.insert(out, msg)
		if m then
			sound(pet, m)
			local old = (kit :: Instance):FindFirstChild(pet)
			if old then old:Destroy() end
			m.Parent = kit
		end
	end
	-- the kennel: its mesh, and a solid box round its walls
	local k, msg = assemble("kennel", "Kennel")
	table.insert(out, msg)
	if k then
		local solid = Instance.new("Part")
		solid.Name = "Solid"
		solid.Size = Vector3.new(2.95, 3.0, 2.75)
		solid.CFrame = CFrame.new(0, 1.5, 0)
		solid.Transparency = 1
		solid.Anchored = true
		solid.CanCollide = true; solid.CanQuery = true; solid.CanTouch = false
		solid.Material = Enum.Material.SmoothPlastic
		solid.Color = Color3.fromRGB(239, 227, 214)
		solid.Parent = k
		for _, d in k:GetDescendants() do if d:IsA("BasePart") then d:SetAttribute("Built", "PetKennel") end end
		local f = ServerStorage:FindFirstChild("JankfirePetKit")
		if not f then
			f = Instance.new("Folder")
			f.Name = "JankfirePetKit"
			f.Parent = ServerStorage
		end
		local old = (f :: Instance):FindFirstChild("Kennel")
		if old then old:Destroy() end
		k.Parent = f
	end
	return table.concat(out, " | ")
end

function I.check(): string
	local out = {}
	local kit = ReplicatedStorage:FindFirstChild("JankfirePets")
	for _, pet in { "mannequin", "slug", "dog" } do
		local m = kit and kit:FindFirstChild(pet)
		if not m then table.insert(out, pet .. ": MISSING") continue end
		local cf, size = (m :: Model):GetBoundingBox()
		local snd = m:FindFirstChild("Found")
		table.insert(out, ("%s: %d parts, %.2f x %.2f x %.2f, floor %.2f, sound %s"):format(pet, #m:GetChildren(), size.X, size.Y, size.Z,
			cf.Position.Y - size.Y / 2, if snd then (snd :: Sound).SoundId else "none"))
	end
	local f = ServerStorage:FindFirstChild("JankfirePetKit")
	table.insert(out, "kennel " .. tostring(f and f:FindFirstChild("Kennel") ~= nil))
	return table.concat(out, " | ")
end

return I
