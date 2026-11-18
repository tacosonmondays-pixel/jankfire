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
I.ASSETS = { mannequin = 93735950095362, kennel = 114456936297774 }
-- take 2 of the dog and the slug (tools/roblox/pets_skinned.py; the owner found take 1's butted pieces "AI-ish"): ONE
-- skinned MeshPart each, its Bones inside it. the upload lands in the file's own frame (measured 18 Nov: the MeshPart at
-- its box's middle, the bones exactly where pets2_layout.json says, the root bone at the origin), so it goes in as it
-- lands. BONE: one bone and where it must be (the check)
I.SKINNED = {
	dog = { asset = 131881237894353, mesh = "pd_dog", bone = "head", at = Vector3.new(0, 0.784, -0.688) },
	slug = { asset = 70466317838874, mesh = "ps_slug", bone = "s0", at = Vector3.new(0, 0.4675, -0.527) },
}
-- the find's recording per pet (Roblox's licensed library, Pro Sound Effects): id, the stretch played, volume
I.SOUNDS = {
	-- (the hub egg's own recording: Pro Sound Effects "Musical Toy Top 1", its toy-top run, measured by the hub egg)
	mannequin = { id = "rbxassetid://9117040176", from = 1.3, to = 3.0, volume = 0.35 },
	-- (Pro Sound Effects "Metal Pole Impact With Wrench Bat 2": four quick clanks, onsets 6.85, 7.10, 7.42, 7.70 s,
	-- measured silently 18 Nov, peak 0.74)
	slug = { id = "rbxassetid://9116768705", from = 6.8, to = 7.95, volume = 0.3 },
	-- (Freesound 468443 "Squeaky Toy #1" by Breviceps, CC0, uploaded as is: one squeak, 0.45 s)
	dog = { id = "rbxassetid://75582875806945", volume = 0.5 },
} :: { [string]: { id: string, from: number?, to: number?, volume: number } }
-- (tools/roblox/pets_import_luau.py writes this from pets_layout.json)
-- LAYOUT BEGIN
I.LAYOUT = {
	mannequin = { size = Vector3.new(0.637, 1.853, 0.737), feet = 0.0950, pieces = {
		pm_body = { role = "body", joint = Vector3.new(0, 0, 0), centre = Vector3.new(-0.0868, 0.9144, -0.2023) },
		pm_shell = { role = "shell", joint = Vector3.new(0, 0, 0), centre = Vector3.new(-0.0884, 0.9208, -0.1952) },
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

-- a skinned pet: its one MeshPart and its Bones, as the upload put them, round a Root at the origin
local function skinned(pet: string): (Model?, string)
	local sk = I.SKINNED[pet]
	local c, err = load(sk.asset)
	if not c then return nil, err :: string end
	local mp = (c :: Instance):FindFirstChild(sk.mesh, true)
	if not (mp and mp:IsA("MeshPart")) then (c :: Instance):Destroy(); return nil, pet .. ": no " .. sk.mesh .. " in the upload" end
	local m = Instance.new("Model")
	m.Name = pet
	local root = Instance.new("Part")
	root.Name = "Root"
	root.Size = Vector3.new(0.2, 0.2, 0.2)
	root.Transparency = 1
	root.Anchored = true
	root.CanCollide = false; root.CanQuery = false; root.CanTouch = false
	root.CFrame = CFrame.new()
	root.Parent = m
	m.PrimaryPart = root
	mp.Parent = m
	mp.Anchored = true
	mp.CanCollide = false; mp.CanQuery = false; mp.CanTouch = false
	mp.Massless = true
	mp.Color = Color3.new(1, 1, 1) -- (the colours are in the mesh)
	mp.Material = Enum.Material.SmoothPlastic
	mp.Reflectance = 0
	mp.CastShadow = true
	mp:SetAttribute("Role", "body")
	m:SetAttribute("Skinned", true)
	;(c :: Instance):Destroy()
	local b = mp:FindFirstChild(sk.bone, true)
	local miss = if b and b:IsA("Bone") then (b.WorldPosition - sk.at).Magnitude else math.huge
	local nb = 0
	for _, d in mp:GetDescendants() do if d:IsA("Bone") then nb += 1 end end
	return m, ("%s: skinned, %d bones, %s off by %.3f"):format(pet, nb, sk.bone, miss)
end

function I.build(only: { string }?): string
	local out = {}
	local kit = ReplicatedStorage:FindFirstChild("JankfirePets")
	if not kit then
		kit = Instance.new("Folder")
		kit.Name = "JankfirePets"
		kit.Parent = ReplicatedStorage
	end
	for _, pet in only or { "mannequin" } do -- (the slug and the dog are parked: Flair PETS. I.build({ "dog" }) still builds one)
		local m, msg
		if I.SKINNED[pet] then m, msg = skinned(pet) else m, msg = assemble(pet, pet) end
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
