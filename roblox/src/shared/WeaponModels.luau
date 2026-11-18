--!strict
-- the three weapons as chunky code models (boxes and cylinders, from public/js/models.js redlineBuild / marbles and
-- public/js/blades/katana.js), in the web game's own frame: metres, -Z is forward, the grip near the origin. they keep
-- the spots the effects use (Muzzle, Sight, Grip attachments; the Redline's needle and vents; the katana's blade, which
-- stretches with kills). when the Blender model has been imported into ReplicatedStorage.JankfireWeapons (w_redline,
-- w_marbles, w_katana: see roblox/README.md), its pieces are fitted onto the same frame and the boxes hide.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Weapons = require(script.Parent:WaitForChild("Weapons"))

local WeaponModels = {}

-- the Blender files' bounding boxes (metres, the file's frame): tools/roblox/export_weapons.py writes these
WeaponModels.FILES = {
	w_redline = { lo = Vector3.new(-0.0408, -0.2822, -0.47), hi = Vector3.new(0.0657, 0.0808, 0.5047) },
	w_marbles = { lo = Vector3.new(-0.0419, -0.136, -0.37), hi = Vector3.new(0.0407, 0.1677, 0.112) },
	w_katana = { lo = Vector3.new(-0.0374, -0.0394, -0.8357), hi = Vector3.new(0.0374, 0.0829, 0.1306) },
}

local function rgb(hex: number): Color3
	return Color3.fromRGB(bit32.rshift(hex, 16) % 256, bit32.rshift(hex, 8) % 256, hex % 256)
end

type Builder = { model: Model, root: BasePart, k: number }

local function part(b: Builder, name: string, shape: Enum.PartType, size: Vector3, color: number, pos: Vector3, rot: CFrame?): Part
	local p = Instance.new("Part")
	p.Name = name; p.Shape = shape; p.Color = rgb(color); p.Material = Enum.Material.SmoothPlastic
	p.Size = Vector3.new(math.max(size.X * b.k, 0.02), math.max(size.Y * b.k, 0.02), math.max(size.Z * b.k, 0.02))
	p.CFrame = b.root.CFrame * CFrame.new(pos * b.k) * (rot or CFrame.identity)
	p.Anchored = false; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Massless = true; p.CastShadow = false
	p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	local w = Instance.new("WeldConstraint"); w.Part0 = b.root; w.Part1 = p; w.Parent = p
	p.Parent = b.model
	return p
end
local function bx(b: Builder, name: string, w: number, h: number, d: number, color: number, x: number, y: number, z: number, rx: number?): Part
	return part(b, name, Enum.PartType.Block, Vector3.new(w, h, d), color, Vector3.new(x, y, z), if rx then CFrame.Angles(rx, 0, 0) else nil)
end
-- a cylinder along Z (Roblox cylinders run along X)
local function cylZ(b: Builder, name: string, r: number, len: number, color: number, x: number, y: number, z: number): Part
	return part(b, name, Enum.PartType.Cylinder, Vector3.new(len, r * 2, r * 2), color, Vector3.new(x, y, z), CFrame.Angles(0, math.pi / 2, 0))
end
local function ball(b: Builder, name: string, r: number, color: number, x: number, y: number, z: number): Part
	return part(b, name, Enum.PartType.Ball, Vector3.new(r * 2, r * 2, r * 2), color, Vector3.new(x, y, z))
end
local function spot(b: Builder, name: string, pos: Vector3)
	local a = Instance.new("Attachment"); a.Name = name; a.Position = pos * b.k; a.Parent = b.root
end

local BUILD: { [string]: (Builder) -> () } = {}

BUILD.redline = function(b)
	local body, accent, dark = 0x24262d, 0xc81e1e, 0x151515
	bx(b, "receiver", 0.06, 0.1, 0.3, body, 0, 0, -0.04)
	bx(b, "rail", 0.062, 0.018, 0.3, accent, 0, 0.058, -0.04)
	bx(b, "stripe", 0.062, 0.012, 0.16, accent, 0, -0.03, -0.07)
	bx(b, "grip", 0.04, 0.12, 0.05, dark, 0, -0.1, 0.05, -0.3)
	bx(b, "mag", 0.036, 0.16, 0.05, dark, 0, -0.12, -0.1)
	bx(b, "stock", 0.05, 0.08, 0.16, dark, 0, -0.01, 0.19)
	cylZ(b, "shroud", 0.034, 0.22, 0x3a3d45, 0, 0.01, -0.29)
	-- the vents in the shroud glow hotter the lower your HP (the client recolours every part named "vent")
	for i = 0, 3 do
		local v = bx(b, "vent", 0.072, 0.012, 0.022, 0x401010, 0, 0.012, -0.21 - i * 0.045)
		v.Material = Enum.Material.Neon
	end
	cylZ(b, "brake", 0.016, 0.07, 0x111111, 0, 0.01, -0.43)
	for _, sx in { -1, 1 } do bx(b, "brakefin", 0.006, 0.02, 0.03, 0x111111, sx * 0.016, 0.01, -0.42) end
	-- the tachometer on the left side, facing you: the needle is your fire rate
	part(b, "dial", Enum.PartType.Cylinder, Vector3.new(0.01, 0.072, 0.072), 0x101010, Vector3.new(-0.034, 0.03, -0.05))
	part(b, "dialface", Enum.PartType.Cylinder, Vector3.new(0.002, 0.062, 0.062), 0xf2f2f2, Vector3.new(-0.0395, 0.03, -0.05))
	local hub = bx(b, "needlehub", 0.004, 0.004, 0.004, 0xff2a2a, -0.041, 0.03, -0.05)
	hub.Transparency = 1
	local n = bx(b, "needle", 0.002, 0.026, 0.003, 0xff2a2a, -0.041, 0.041, -0.05)
	n.Material = Enum.Material.Neon
	spot(b, "Muzzle", Vector3.new(0, 0.01, -0.47))
	spot(b, "Sight", Vector3.new(0, 0.0737, 0.1058))
	spot(b, "Port", Vector3.new(0.032, 0.03, -0.06))
	spot(b, "Grip", Vector3.new(0, -0.09, 0.05))
	spot(b, "Fore", Vector3.new(0, -0.03, -0.22))
end

BUILD.marbles = function(b)
	local wood, brass = 0x6b3a1a, 0xc8a050
	bx(b, "grip", 0.036, 0.12, 0.048, wood, 0, -0.07, 0.07, -0.45)
	bx(b, "stock", 0.044, 0.06, 0.2, wood, 0, -0.012, 0.0)
	bx(b, "lock", 0.05, 0.05, 0.1, 0x34343c, 0, 0.004, -0.03)
	bx(b, "guard", 0.006, 0.035, 0.05, 0x1a1a1a, 0, -0.05, 0.02)
	bx(b, "forestock", 0.04, 0.035, 0.12, wood, 0, -0.022, -0.15)
	-- the brass blunderbuss barrel, flaring at the mouth
	cylZ(b, "barrel", 0.019, 0.16, brass, 0, 0.012, -0.16)
	cylZ(b, "barrel2", 0.026, 0.06, brass, 0, 0.012, -0.27)
	cylZ(b, "bell", 0.04, 0.035, brass, 0, 0.012, -0.32)
	cylZ(b, "bellmouth", 0.052, 0.02, brass, 0, 0.012, -0.355)
	cylZ(b, "band", 0.023, 0.016, 0xa07830, 0, 0.012, -0.1)
	cylZ(b, "band", 0.023, 0.016, 0xa07830, 0, 0.012, -0.22)
	part(b, "neck", Enum.PartType.Cylinder, Vector3.new(0.03, 0.03, 0.03), brass, Vector3.new(0, 0.045, -0.06), CFrame.Angles(0, 0, math.pi / 2))
	local jar = part(b, "jar", Enum.PartType.Cylinder, Vector3.new(0.075, 0.072, 0.072), 0xcfefff, Vector3.new(0, 0.098, -0.06), CFrame.Angles(0, 0, math.pi / 2))
	jar.Material = Enum.Material.Glass; jar.Transparency = 0.6
	part(b, "lid", Enum.PartType.Cylinder, Vector3.new(0.012, 0.076, 0.076), 0x2a2a2a, Vector3.new(0, 0.141, -0.06), CFrame.Angles(0, 0, math.pi / 2))
	local cols = { 0x2f7bff, 0x19c37d, 0xff4f4f, 0xffd23b, 0xb07dff, 0xff8a1a, 0x37d6ff }
	for i = 0, 9 do
		local a, k = i * 2.4, (i % 4) / 4
		local m = ball(b, "marble", 0.012, cols[i % #cols + 1], math.cos(a) * 0.018 * (0.3 + k), 0.074 + math.floor(i / 4) * 0.012 * 1.7, -0.06 + math.sin(a) * 0.018 * (0.3 + k))
		m.Material = Enum.Material.Glass
	end
	spot(b, "Muzzle", Vector3.new(0, 0.012, -0.37))
	spot(b, "Grip", Vector3.new(0, -0.06, 0.07))
	spot(b, "Fore", Vector3.new(0, -0.03, -0.15))
end

-- the blade's origin (the back of the habaki): it stretches along -Z from here
WeaponModels.BLADE_Z = -0.139
BUILD.katana = function(b)
	bx(b, "tsuka", 0.028, 0.034, 0.24, 0x26305a, 0, 0, 0.0)
	bx(b, "kashira", 0.03, 0.036, 0.03, 0x26242b, 0, 0, 0.12)
	bx(b, "fuchi", 0.03, 0.036, 0.014, 0x26242b, 0, 0, -0.125)
	part(b, "tsuba", Enum.PartType.Cylinder, Vector3.new(0.005, 0.08, 0.07), 0x3b342e, Vector3.new(0, 0, -0.134), CFrame.Angles(0, math.pi / 2, 0))
	bx(b, "habaki", 0.012, 0.034, 0.034, 0xc9963f, 0, 0, -0.156)
	-- the blade: a shallow curve (sori) from the machi up to the tip, edge down. every piece is named "blade"
	local R = (0.7 * 0.7 / 4 + 0.017 * 0.017) / (2 * 0.017)
	local segs = 6
	for i = 0, segs - 1 do
		local t0 = 2 * math.asin(0.7 / (2 * R)) * i / segs
		local t1 = 2 * math.asin(0.7 / (2 * R)) * (i + 1) / segs
		local z0, y0 = -R * math.sin(t0), R * (1 - math.cos(t0))
		local z1, y1 = -R * math.sin(t1), R * (1 - math.cos(t1))
		local w = 0.031 + (0.0215 - 0.031) * (i + 0.5) / segs
		local len = math.sqrt((z1 - z0) ^ 2 + (y1 - y0) ^ 2)
		local mz, my = (z0 + z1) / 2, (y0 + y1) / 2
		local ang = math.atan2(y1 - y0, -(z1 - z0))
		local p = part(b, "blade", Enum.PartType.Block, Vector3.new(0.006, w, len + 0.002), if i == segs - 1 then 0xdde2e7 else 0xb4bcc6,
			Vector3.new(0, 0.0151 - w / 2 + my, WeaponModels.BLADE_Z + mz), CFrame.Angles(ang, 0, 0))
		p.Material = Enum.Material.Metal; p.Reflectance = 0.25
	end
	spot(b, "Muzzle", Vector3.new(0, 0.0829, -0.8357))
	spot(b, "Mid", Vector3.new(0, 0.03, -0.45)) -- 45% of the way: where the swing smear starts
	spot(b, "Grip", Vector3.new(0, 0, -0.083))
	spot(b, "Fore", Vector3.new(0, 0, 0.085))
end

-- the classic modes' melee (17 Nov 2026): code stand-ins until the kit models are in JankfireWeapons (w_knife, w_spoon,
-- w_claw). chunky, flat colours; the grip at the origin, the tip along -Z; Muzzle = the tip, Mid = 45% of the way there
BUILD.knife = function(b)
	bx(b, "handle", 0.026, 0.032, 0.11, 0x2b2622, 0, 0, 0.035)
	bx(b, "guard", 0.034, 0.042, 0.012, 0x3a3d45, 0, 0.002, -0.026)
	local blade = bx(b, "blade", 0.006, 0.034, 0.12, 0xc8d0dc, 0, 0.004, -0.092)
	blade.Material = Enum.Material.Metal; blade.Reflectance = 0.2
	local tip = bx(b, "blade", 0.006, 0.022, 0.04, 0xdde2e7, 0, 0.01, -0.165, -0.25)
	tip.Material = Enum.Material.Metal; tip.Reflectance = 0.25
	-- (the spots are the kit model's, gun-models WeaponKit: a fitted model keeps the code model's spots)
	spot(b, "Muzzle", Vector3.new(0, 0.0026, -0.2138))
	spot(b, "Mid", Vector3.new(0, 0.0012, -0.0797))
	spot(b, "Grip", Vector3.new(0, 0, 0.03))
end
-- (weapons batch A, 18 Nov 2026) code stand-ins for the Bread and the Hand Slapper until their kit models are in
-- JankfireWeapons (w_bread, w_slapper; the guns-remodel session builds them): the grip at the origin, the tip along -Z
BUILD.bread = function(b)
	bx(b, "loaf", 0.2, 0.15, 1.42, 0xc8965a, 0, 0.02, -0.68)
	bx(b, "crust", 0.17, 0.04, 1.36, 0xa87448, 0, 0.105, -0.68)
	for i = 0, 4 do bx(b, "score", 0.18, 0.012, 0.03, 0x8e6038, 0, 0.128, -0.2 - i * 0.26, -0.35) end
	bx(b, "heel", 0.16, 0.12, 0.2, 0xb88450, 0, 0.0, 0.1)
	spot(b, "Muzzle", Vector3.new(0, 0, -1.45)) -- (the kit model's spots: export_report.json)
	spot(b, "Mid", Vector3.new(0, 0.0011, -0.5865))
	spot(b, "Grip", Vector3.new(0, 0.002, 0.12))
end
BUILD.slapper = function(b)
	cylZ(b, "stick", 0.016, 0.5, 0xd6d0c6, 0, 0, -0.18)
	bx(b, "grip", 0.04, 0.04, 0.14, 0x3a3d45, 0, 0, 0.05)
	bx(b, "hand", 0.17, 0.035, 0.18, 0xd68aa6, 0, 0, -0.56)
	for i = 0, 3 do bx(b, "hand", 0.032, 0.03, 0.1, 0xd68aa6, -0.06 + i * 0.04, 0, -0.69) end
	bx(b, "hand", 0.035, 0.03, 0.09, 0xd68aa6, 0.1, 0, -0.55, 0.0)
	spot(b, "Muzzle", Vector3.new(0, 0, -0.7))
	spot(b, "Mid", Vector3.new(0, 0, -0.28475))
	spot(b, "Grip", Vector3.new(0, 0, 0.055))
end
-- the knife's spoon look (web knife_spoon: a serving spoon that still stabs)
BUILD.spoon = function(b)
	cylZ(b, "handle", 0.009, 0.2, 0xc8ccd2, 0, 0, -0.02)
	local bowl = part(b, "bowl", Enum.PartType.Cylinder, Vector3.new(0.016, 0.07, 0.07), 0xd4d8de, Vector3.new(0, 0.004, -0.15), CFrame.Angles(0, 0, math.pi / 2))
	bowl.Material = Enum.Material.Metal; bowl.Reflectance = 0.3
	bx(b, "lip", 0.05, 0.012, 0.03, 0xd4d8de, 0, 0.004, -0.188)
	spot(b, "Muzzle", Vector3.new(-0.0027, -0.0067, -0.132))
	spot(b, "Mid", Vector3.new(-0.0012, -0.003, -0.0429))
	spot(b, "Grip", Vector3.new(0, 0, 0.03))
end
-- the zombie claw (web models.js claw): a torn cuff and four long dirty nails out of the fist
BUILD.claw = function(b)
	cylZ(b, "cuff", 0.05, 0.06, 0x4a5a3a, 0, -0.005, 0.05)
	for i = 0, 3 do
		local x = -0.045 + i * 0.03
		bx(b, "finger", 0.022, 0.024, 0.07, 0x55782b, x, 0.004, -0.04, -0.2)
		bx(b, "nail", 0.012, 0.012, 0.07, 0xd8cf9a, x, -0.006, -0.1, -0.45)
	end
	spot(b, "Muzzle", Vector3.new(0, -0.0332, -0.149))
	spot(b, "Mid", Vector3.new(0, 0, -0.05))
	spot(b, "Grip", Vector3.new(0, 0, 0))
end

-- a plain gun with no hand-written code model: a stand-in from its row in Weapons (mdl = the Blender file's bounds and
-- the spots, metres): a receiver, a barrel to the muzzle, a grip, a stripe in the weapon's colour. it only shows
-- until the Blender model (JankfireWeapons.w_<id>) is imported, and it carries the same Muzzle / Grip / Fore /
-- Sight / Port spots the hands and effects use
local function buildPlain(b: Builder, mdl: any, color: Color3)
	local lo, hi = mdl.lo :: Vector3, mdl.hi :: Vector3
	local muzzle, grip = mdl.muzzle :: Vector3, mdl.grip :: Vector3
	local w = math.max(hi.X - lo.X, 0.04)
	local back = hi.Z
	local mid = back + (muzzle.Z - back) * 0.55 -- the receiver runs from the butt to here, the barrel from here on
	bx(b, "receiver", w * 0.8, 0.1, back - mid, 0x24262d, 0, muzzle.Y - 0.01, (back + mid) / 2)
	cylZ(b, "barrel", 0.018, mid - muzzle.Z, 0x111111, 0, muzzle.Y, (mid + muzzle.Z) / 2)
	bx(b, "grip", w * 0.55, 0.13, 0.05, 0x151515, 0, grip.Y - 0.02, grip.Z, -0.3)
	local stripe = bx(b, "stripe", w * 0.82, 0.014, (back - mid) * 0.6, 0, 0, muzzle.Y + 0.045, (back + mid) / 2)
	stripe.Color = color
	spot(b, "Muzzle", muzzle); spot(b, "Grip", grip)
	if mdl.fore then spot(b, "Fore", mdl.fore) end -- (a sidearm is held in one hand: no off-hand spot)
	if mdl.sight then spot(b, "Sight", mdl.sight) end
	if mdl.port then spot(b, "Port", mdl.port) end
end

-- fit an imported Blender model (the importer's own scale and spot) onto the code model's frame
-- the template's box: the AABB of its parts in its pivot's frame. (not tmpl:GetBoundingBox(): on the kit models that
-- box comes out up to 40% wider than the parts themselves, which squashed every held gun across and moved its pieces
-- off the row's pivots; the Revolver's cylinder sat 8 mm off its axis after a shot. found 16 Nov 2026)
local function partsBox(tmpl: Model): (CFrame, Vector3)
	local pcf = tmpl:GetPivot()
	local lo, hi = Vector3.one * math.huge, -Vector3.one * math.huge
	for _, d in tmpl:GetDescendants() do
		if d:IsA("BasePart") then
			local rel = pcf:ToObjectSpace(d.CFrame)
			local s = d.Size / 2
			local e = Vector3.new(
				math.abs(rel.XVector.X) * s.X + math.abs(rel.YVector.X) * s.Y + math.abs(rel.ZVector.X) * s.Z,
				math.abs(rel.XVector.Y) * s.X + math.abs(rel.YVector.Y) * s.Y + math.abs(rel.ZVector.Y) * s.Z,
				math.abs(rel.XVector.Z) * s.X + math.abs(rel.YVector.Z) * s.Y + math.abs(rel.ZVector.Z) * s.Z)
			lo = lo:Min(rel.Position - e); hi = hi:Max(rel.Position + e)
		end
	end
	if lo.X > hi.X then return tmpl:GetBoundingBox() end
	return pcf * CFrame.new((lo + hi) / 2), hi - lo
end

local function fitImported(b: Builder, tmpl: Model, file: { lo: Vector3, hi: Vector3 })
	local tcf, tsize = partsBox(tmpl)
	local fsz = file.hi - file.lo
	local centre = (file.lo + file.hi) / 2
	local U = Vector3.new(tsize.X / math.max(fsz.X, 1e-4), tsize.Y / math.max(fsz.Y, 1e-4), tsize.Z / math.max(fsz.Z, 1e-4))
	local copy = tmpl:Clone()
	for _, d in copy:GetDescendants() do
		if d:IsA("BasePart") then
			local rel = tcf:ToObjectSpace(d.CFrame)
			local q = rel.Position / U + centre -- back in file metres
			d.Size = d.Size / U * b.k
			d.CFrame = b.root.CFrame * CFrame.new(q * b.k) * rel.Rotation
			d.Anchored = false; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.Massless = true; d.CastShadow = false
			local w = Instance.new("WeldConstraint"); w.Part0 = b.root; w.Part1 = d; w.Parent = d
			-- the Blender pieces keep the code model's jobs by name: the blade stretches, the needle turns, the vents glow
			local n = string.lower(d.Name)
			local wz = string.match(n, "_wz(%a+)")
			if wz then d:SetAttribute("WrapZone", wz) end -- (the wrap zone survives the renames below)
			if string.find(n, "kat_blade", 1, true) then d.Name = "blade"
			elseif string.find(n, "needle", 1, true) then
				d.Name = "needle"
				d:SetAttribute("Pivot", Vector3.new(-0.03186, 0.0277, -0.04992)) -- the needle node's origin in the file
			elseif string.find(n, "_jar", 1, true) then d.Transparency = 0.6; d.Material = Enum.Material.Glass
			elseif string.find(n, "vent", 1, true) then d.Name = "vent" end
			d.Parent = b.model
		end
	end
	copy:Destroy()
end

-- build a weapon. k = studs per web metre (viewmodel: 3 x its VM scale, third person: 3 x 1.5). skin = a weapon skin's
-- id (GunSkins: its model in ReplicatedStorage.JankfireSkins, same frame and moving pieces as the gun): drawn instead
function WeaponModels.build(id: string, k: number, skin: string?): Model?
	-- (the knife's spoon look in a classic mode: its own model, w_spoon / BUILD.spoon, not a catalog skin)
	local look = if id == "knife" and skin == "spoon" then "spoon" else id
	if look == "spoon" then skin = nil end
	local fn = BUILD[look]
	local row = (Weapons.list :: any)[id]
	local mdl = row and row.mdl
	if not fn and not mdl then return nil end
	local m = Instance.new("Model")
	m.Name = id
	local root = Instance.new("Part")
	root.Name = "Root"; root.Size = Vector3.new(0.05, 0.05, 0.05); root.Transparency = 1
	root.Anchored = false; root.CanCollide = false; root.CanQuery = false; root.CanTouch = false; root.Massless = true
	root.Parent = m
	m.PrimaryPart = root
	local b: Builder = { model = m, root = root, k = k }
	if fn then fn(b) else buildPlain(b, mdl, row.color) end
	for _, c in m:GetChildren() do if c:IsA("BasePart") and c ~= root then c:SetAttribute("Code", true) end end
	local lib = ReplicatedStorage:FindFirstChild("JankfireWeapons")
	local tmpl = lib and lib:FindFirstChild("w_" .. look)
	local skins = skin and ReplicatedStorage:FindFirstChild("JankfireSkins")
	local st = skins and skins:FindFirstChild(skin :: string)
	if st and st:IsA("Model") and st:GetAttribute("Weapon") == id then tmpl = st; m:SetAttribute("Skin", skin) end
	local file = (WeaponModels.FILES :: any)["w_" .. id] or mdl -- (a plain gun keeps its bounds in its row)
	-- the models are a switch (PolishBackup.WeaponImport, W.models): a kit model's box is not the web model's, so a
	-- template carries its own file bounds and they win over the row's
	local flo, fhi = tmpl and tmpl:GetAttribute("FileLo"), tmpl and tmpl:GetAttribute("FileHi")
	if typeof(flo) == "Vector3" and typeof(fhi) == "Vector3" then file = { lo = flo, hi = fhi } end
	if tmpl and tmpl:IsA("Model") and file then
		local ok, err = pcall(fitImported, b, tmpl, file)
		if ok then
			-- the Blender blade replaces the code blade (same name): drop the code one so the stretch moves the right one
			for _, c in m:GetChildren() do
				if c:IsA("BasePart") and c:GetAttribute("Code") and c.Name ~= "needlehub" then c:Destroy() end
			end
		else
			warn("[jankfire] couldn't fit the Blender " .. id .. ": " .. tostring(err))
		end
	end
	-- remember every blade piece's rest spot so the stretch is always from the rest pose
	for _, c in m:GetChildren() do
		if c:IsA("BasePart") and c.Name == "blade" then
			local rel = root.CFrame:ToObjectSpace(c.CFrame)
			c:SetAttribute("RestCF", rel); c:SetAttribute("RestSize", c.Size)
		end
	end
	local tip = root:FindFirstChild("Muzzle") :: Attachment?
	if tip then tip:SetAttribute("Rest", tip.Position) end
	-- (the VFX pipeline's hook: on a client, Fx sets this to hang a high-tier skin's effects on the gun, Fx.skinIdle)
	local onBuilt = (WeaponModels :: any).onBuilt
	if onBuilt then onBuilt(m, k) end
	return m
end

-- the katana grows with kills: stretch the blade along its length by 1 + 0.55 n from its origin, tip with it
-- (public/js/models.js setKatana: a look; the reach itself is +1.5 studs a kill, on the server)
function WeaponModels.setKatana(m: Model, n: number, k: number)
	local root = m.PrimaryPart
	if not root then return end
	local s = 1 + 0.55 * math.max(0, n)
	local z0 = WeaponModels.BLADE_Z * k
	for _, c in m:GetChildren() do
		if c:IsA("BasePart") and c.Name == "blade" then
			local rel, size = c:GetAttribute("RestCF"), c:GetAttribute("RestSize")
			if typeof(rel) ~= "CFrame" or typeof(size) ~= "Vector3" then continue end
			local p = rel.Position
			local np = Vector3.new(p.X, p.Y, z0 + (p.Z - z0) * s)
			-- stretch along the piece's own axis that runs down the blade (z for the code blocks)
			local zAxis = rel.Rotation:VectorToObjectSpace(Vector3.zAxis)
			local sv = Vector3.new(1 + (s - 1) * math.abs(zAxis.X), 1 + (s - 1) * math.abs(zAxis.Y), 1 + (s - 1) * math.abs(zAxis.Z))
			local wc = c:FindFirstChildOfClass("WeldConstraint")
			if wc then wc.Enabled = false end
			c.Size = size * sv
			c.CFrame = root.CFrame * CFrame.new(np) * rel.Rotation
			if wc then wc.Enabled = true end
		end
	end
	local tip = root:FindFirstChild("Muzzle") :: Attachment?
	local rest = tip and tip:GetAttribute("Rest")
	if tip and typeof(rest) == "Vector3" then tip.Position = Vector3.new(rest.X, rest.Y, z0 + (rest.Z - z0) * s) end
	local mid = root:FindFirstChild("Mid") :: Attachment?
	if mid and tip then mid.Position = tip.Position * 0.55 + Vector3.new(0, 0, z0 * 0.45) end
end


-- ------------------------------------------------------------------ wraps (the loadout screen's paint jobs)
-- which part of a weapon a wrap paints (public/js/wrapzones.js): the Blender pieces say so in their names (_wzA = the
-- handle side, _wzB = the business end, _wzN = trims that keep their look unless the wrap is on FULL, _wzAB = both);
-- anything untagged goes by its colour (greys and near-blacks read as the metal: B). the wrap itself (Roster.wraps) is a
-- palette laid over the painted pieces in order along the weapon: solid, alt(ernating), speck (every third), cycle,
-- fade / bands (by where the piece sits along the weapon's length). a wrap can always be taken off again: every
-- painted piece remembers its own look
local Roster = require(script.Parent:WaitForChild("Roster"))
WeaponModels.MODES = { "normal", "reverse", "full" }

local function zoneOf(p: BasePart, root: Instance?): string
	local tagged = p:GetAttribute("WrapZone") -- (fitImported keeps the tag of a piece it renames: blade, needle, vent)
	if type(tagged) == "string" then return tagged end
	-- its own name, or a parent's (the Shredder's pieces sit in models named sd_trim_wzN etc.)
	local x: Instance? = p
	while x and x ~= root do
		local m = string.match(string.lower(x.Name), "_wz(%a+)")
		if m == "a" or m == "b" or m == "n" or m == "ab" then return m end
		x = x.Parent
	end
	local oc = p:GetAttribute("WrapColor")
	local c: Color3 = if typeof(oc) == "Color3" then oc else p.Color
	local _, s, v = c:ToHSV()
	return if s < 0.2 or v < 0.15 then "b" else "a"
end
WeaponModels.zoneOf = zoneOf

local function paints(mode: string, zone: string): boolean
	if mode == "full" or zone == "ab" then return true end
	return if mode == "reverse" then zone == "b" else zone == "a"
end

local stash: { [BasePart]: SurfaceAppearance } = setmetatable({}, { __mode = "k" }) :: any

-- a wrap with a picture: ReplicatedStorage.JankfireWraps holds one SurfaceAppearance per textured wrap (drawn by
-- tools/roblox/wrap_textures.py, built by studio-tools/WrapBook.luau; docs/WRAP-TEXTURES.md). It goes on every piece the
-- kit export unfolded (attribute WrapUV, tools/roblox/gun_uvs.py), so stars are stars and stripes taper; a piece with
-- no UVs (a code model's boxes, a gun from before the unfold) still gets the wrap's palette laid over it, below
local function picture(wrapId: string): SurfaceAppearance?
	local lib = ReplicatedStorage:FindFirstChild("JankfireWraps")
	local sa = lib and lib:FindFirstChild(wrapId)
	return if sa and sa:IsA("SurfaceAppearance") then sa else nil
end
WeaponModels.picture = picture
-- a picture shows blank while it downloads: the client fetches the ones its player wears before they are needed
if game:GetService("RunService"):IsClient() then
	task.defer(function()
		local me = game:GetService("Players").LocalPlayer
		local CP = game:GetService("ContentProvider")
		local asked: { [string]: boolean } = {}
		local function fetch()
			local s = me:GetAttribute("Wraps")
			local want = {}
			if type(s) == "string" then
				for id in string.gmatch(s, "[%w_]+=([%w_]+)/") do
					local sa = picture(id)
					if sa and not asked[id] then asked[id] = true; table.insert(want, sa) end
				end
			end
			if #want > 0 then pcall(CP.PreloadAsync, CP, want) end
		end
		me:GetAttributeChangedSignal("Wraps"):Connect(fetch)
		fetch()
	end)
end

local function restore(p: BasePart)
	if not p:GetAttribute("Wrapped") then return end
	local c, mat, r, t = p:GetAttribute("WrapColor"), p:GetAttribute("WrapMat"), p:GetAttribute("WrapRefl"), p:GetAttribute("WrapTr")
	if typeof(c) == "Color3" then p.Color = c end
	if type(mat) == "string" then pcall(function() p.Material = (Enum.Material :: any)[mat] end) end
	if type(r) == "number" then p.Reflectance = r end
	if type(t) == "number" then p.Transparency = t end
	local tex = p:GetAttribute("WrapTex")
	if p:IsA("MeshPart") and type(tex) == "string" then p.TextureID = tex end
	local worn = p:FindFirstChild("WrapSA")
	if worn then worn:Destroy() end
	for _, n in { "WrapHole", "WrapHoleGlow" } do
		local g = p:FindFirstChild(n)
		if g then g:Destroy() end
	end
	local sa = stash[p]
	if sa then sa.Parent = p; stash[p] = nil end
	p:SetAttribute("Wrapped", nil)
end

local function remember(p: BasePart)
	if p:GetAttribute("Wrapped") then return end
	p:SetAttribute("WrapColor", p.Color); p:SetAttribute("WrapMat", p.Material.Name)
	p:SetAttribute("WrapRefl", p.Reflectance); p:SetAttribute("WrapTr", p.Transparency)
	if p:IsA("MeshPart") then p:SetAttribute("WrapTex", p.TextureID) end
	p:SetAttribute("Wrapped", true)
end

-- the pieces a wrap can touch: visible ones, not the invisible root / handle / suction field, never a hat on the gun
-- (GunHats marks every hat part NoWrap)
local function pieces(m: Instance): { BasePart }
	local out = {}
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") and d.Name ~= "Root" and d.Name ~= "SuckField" and not d:GetAttribute("NoWrap") then
			local t = d:GetAttribute("WrapTr")
			local tr = if type(t) == "number" then t else d.Transparency
			if tr < 0.99 then table.insert(out, d) end
		end
	end
	return out
end

-- ONE hero picture per gun (Black Hole; the owner, 16 Nov 2026: "the black hole wrap should have one black hole and
-- like an effect of the wrap being pulled towards it"). A wrap's tile repeats every 25 cm, so a hole drawn in it was
-- several. A wrap whose picture carries the attributes Decal (lit: the space round the hole wound into a spiral) and
-- DecalGlow (unlit: the black core and the photon ring, which blooms) gets them once, as two SurfaceGuis on one face:
-- of every piece that wears the picture (either half, so the hole sits in the same place in every mode), the face that
-- looks most to the gun's left (the side first person looks at), the biggest, marked down when the piece is behind the
-- hand (the stock: out of first person's view) or low (the mag: at the screen's bottom edge). It is as big as that face
-- is tall and slides to the face's back end, nearest the eye (on the rifle: the receiver, just above the hand).
-- client/WrapAnim turns the spiral inward, breathes the ring and sends a faint ripple down into the hole.
-- docs/WRAP-TEXTURES.md, "One black hole". The picture's attribute DecalStyle picks the kind: "hole" (the default:
-- Black Hole's spin, ripple and motes) or "mark" (Triangulum, 17 Nov: still; DecalAspect makes the picture wider than
-- tall, and DecalStars gives each star of the glow picture its own label so WrapAnim breathes them one after another).
-- A skin that carries its own mark refuses one (NO_HERO, or the model's attribute NoHeroDecal): no two marks on a gun
local HOLE_PPS = 256 -- SurfaceGui pixels per stud
WeaponModels.HOLE_PPS = HOLE_PPS
local NO_HERO: { [string]: boolean } = { sniper_triangulum = true } -- (the Triangulum Sniper wears the mark already)
local function hole(m: Instance, worn: { BasePart }, ref: CFrame, pic: SurfaceAppearance, all: { BasePart })
	local sk = m:GetAttribute("Skin")
	if (type(sk) == "string" and NO_HERO[sk]) or m:GetAttribute("NoHeroDecal") then return end
	local style = pic:GetAttribute("DecalStyle")
	if type(style) ~= "string" then style = "hole" end
	local asp = pic:GetAttribute("DecalAspect")
	local aspect = if type(asp) == "number" and asp > 0 then asp else 1
	local left, back, up = -ref.RightVector, -ref.LookVector, ref.UpVector
	local grip = m:FindFirstChild("Grip", true)
	local gp = if grip and grip:IsA("Attachment") then grip.WorldPosition else ref.Position
	local best: BasePart?, bestScore, bestFace, bestN, bestW, bestH = nil, 0, Enum.NormalId.Left, Vector3.zero, 0, 0
	for _, p in worn do
		if not (p:IsA("MeshPart") and p:GetAttribute("WrapUV")) then continue end
		local cf, s = p.CFrame, p.Size
		local rel = p.Position - gp
		local wgt = (if rel:Dot(back) > 0.1 then 0.3 else 1) * (if rel:Dot(up) < -0.25 then 0.5 else 1)
		for _, f in {
			{ Enum.NormalId.Left, -cf.RightVector, s.Z, s.Y }, { Enum.NormalId.Right, cf.RightVector, s.Z, s.Y },
			{ Enum.NormalId.Top, cf.UpVector, s.X, s.Z }, { Enum.NormalId.Bottom, -cf.UpVector, s.X, s.Z },
			{ Enum.NormalId.Front, cf.LookVector, s.X, s.Y }, { Enum.NormalId.Back, -cf.LookVector, s.X, s.Y },
		} do
			local n = f[2] :: Vector3
			if n:Dot(left) > 0.7 and f[3] * f[4] * wgt > bestScore then
				best, bestScore, bestFace, bestN, bestW, bestH = p, f[3] * f[4] * wgt, f[1], n, f[3], f[4]
			end
		end
	end
	if not best then return end
	local hS = math.min(bestH, bestW / aspect) -- (the picture's height in studs; its width is aspect times that)
	local d = hS * HOLE_PPS
	-- along a side face the canvas's +x runs to the right of someone facing it (-normal x the part's up: on Left, the
	-- part's +Z); slide the hole that way or back, whichever is the gun's back, as far as it fits
	local x = 0.5
	local side = bestFace ~= Enum.NormalId.Top and bestFace ~= Enum.NormalId.Bottom
	if side and bestW > hS * aspect * 1.15 then
		local mx = hS * aspect * 0.55 / bestW
		x = if (-bestN):Cross(best.CFrame.UpVector):Dot(back) > 0 then 1 - mx else mx
	end
	-- the gun's small trims standing over the picture (the rifle's olive kit-mark slots, a rivet: _wzN pieces) broke its
	-- one clean shape (the skin concepts session, 17 Nov, from the v564 sheet): they hide while it shows. Remembered like
	-- any wrapped piece, so changing or taking off the wrap brings them back
	if side then
		local n, upv = bestN, best.CFrame.UpVector
		local xdir = (-n):Cross(upv)
		local function half(b: BasePart, v: Vector3): number
			local c, z = b.CFrame, b.Size
			return math.abs(v:Dot(c.RightVector)) * z.X / 2 + math.abs(v:Dot(c.UpVector)) * z.Y / 2 + math.abs(v:Dot(c.LookVector)) * z.Z / 2
		end
		local facePt = best.Position + n * half(best, n)
		local rc = facePt + xdir * ((x - 0.5) * bestW)
		local hx, hy = hS * aspect * 0.45, hS * 0.45
		for _, p in all do
			if p == best or zoneOf(p, m) ~= "n" then continue end
			local rel = p.Position - rc
			if math.abs(rel:Dot(xdir)) > hx + half(p, xdir) or math.abs(rel:Dot(upv)) > hy + half(p, upv) then continue end
			if (p.Position - facePt):Dot(n) + half(p, n) < 0.002 then continue end -- (inside the body: it covers nothing)
			remember(p)
			p.Transparency = 1
		end
	end
	local stars = {}
	local ss = pic:GetAttribute("DecalStars")
	if style == "mark" and type(ss) == "string" then
		for sx, sy, sr in string.gmatch(ss, "(%d+),(%d+),(%d+)") do table.insert(stars, { tonumber(sx), tonumber(sy), tonumber(sr) }) end
	end
	for _, spec in { { "WrapHole", pic:GetAttribute("Decal"), false }, { "WrapHoleGlow", pic:GetAttribute("DecalGlow"), true } } do
		if type(spec[2]) ~= "string" then continue end
		local g = Instance.new("SurfaceGui")
		g.Name = spec[1]
		g.Face = bestFace
		g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		g.PixelsPerStud = HOLE_PPS
		g.LightInfluence = if spec[3] then 0 else 1
		g.Brightness = if spec[3] then 4 else 1
		g.ZOffset = if spec[3] then 0.02 else 0.01
		g.ClipsDescendants = true
		g:SetAttribute("D", d)
		g:SetAttribute("Style", style)
		if spec[3] and #stars > 0 then
			-- one label a star (the glow picture is 1024 px wide): its square of the picture, at its place on the face
			local pw, ph = 1024, math.floor(1024 / aspect + 0.5)
			for i, st in stars do
				local R = math.floor(st[3] * 1.6)
				local ox, oy = math.max(0, st[1] - R), math.max(0, st[2] - R)
				local ex, ey = math.min(pw, st[1] + R), math.min(ph, st[2] + R)
				local im = Instance.new("ImageLabel")
				im.Name = "Star"
				im.BackgroundTransparency = 1
				im.Image = spec[2] :: string
				im.ImageRectOffset = Vector2.new(ox, oy)
				im.ImageRectSize = Vector2.new(ex - ox, ey - oy)
				im.AnchorPoint = Vector2.new(0, 0)
				im.Position = UDim2.new(x, (ox / pw - 0.5) * d * aspect, 0.5, (oy / ph - 0.5) * d)
				im.Size = UDim2.fromOffset((ex - ox) / pw * d * aspect, (ey - oy) / ph * d)
				im.ZIndex = 2
				im:SetAttribute("I", i)
				im.Parent = g
			end
		else
			local im = Instance.new("ImageLabel")
			im.Name = "Pic"
			im.BackgroundTransparency = 1
			im.Image = spec[2] :: string
			im.AnchorPoint = Vector2.new(0.5, 0.5)
			im.Position = UDim2.fromScale(x, 0.5)
			im.Size = UDim2.fromOffset(d * aspect, d)
			im.ZIndex = 2
			im.Parent = g
		end
		if spec[3] and style == "hole" then
			-- the ripple falling in (WrapAnim shrinks it from the rim to the ring and fades it in and out)
			local pu = Instance.new("Frame")
			pu.Name = "Pulse"
			pu.BackgroundTransparency = 1
			pu.AnchorPoint = Vector2.new(0.5, 0.5)
			pu.Position = UDim2.fromScale(x, 0.5)
			pu.Size = UDim2.fromOffset(d * 0.9, d * 0.9)
			pu.ZIndex = 1
			local cr = Instance.new("UICorner")
			cr.CornerRadius = UDim.new(0.5, 0)
			cr.Parent = pu
			local st = Instance.new("UIStroke")
			st.Color = Color3.fromHex("ffb066")
			st.Thickness = math.max(1, d * 0.008)
			st.Transparency = 1
			st.Parent = pu
			pu.Parent = g
			-- glowing motes falling in (the owner, 16 Nov evening: "cool effects"): WrapAnim winds each down the spiral
			-- from the rim to the ring, faster as it nears, fading in and out; under the picture, so the core swallows them
			for i = 1, 10 do
				local mo = Instance.new("ImageLabel")
				mo.Name = "Mote"
				mo.BackgroundTransparency = 1
				mo.Image = "rbxassetid://107753175681578" -- (Fx's soft glow dot)
				mo.ImageColor3 = Color3.fromHex("ffe4bc")
				mo.ImageTransparency = 1
				mo.AnchorPoint = Vector2.new(0.5, 0.5)
				mo.Size = UDim2.fromOffset(d * 0.05, d * 0.05)
				mo.ZIndex = 1
				mo:SetAttribute("I", i)
				mo.Parent = g
			end
		end
		g:SetAttribute("X", x)
		g:AddTag("WrapHole")
		g.Parent = best
	end
end

-- paint a weapon model (or a Tool) with a wrap. nil / "default" takes the wrap off
function WeaponModels.wrap(m: Instance, wrapId: string?, mode: string?)
	local list = pieces(m)
	for _, p in list do restore(p) end
	local wr = wrapId and Roster.wrapById[wrapId]
	if not wr or #wr.pal == 0 then return end
	local md = if mode and table.find(WeaponModels.MODES, mode) then mode else "normal"
	-- along the weapon's longest side, in its own frame
	local ref: CFrame
	if m:IsA("Model") then ref = m:GetPivot()
	else
		local h = m:FindFirstChild("Handle")
		ref = if h and h:IsA("BasePart") then h.CFrame else CFrame.identity
	end
	local lo, hi = Vector3.one * math.huge, -Vector3.one * math.huge
	local at: { [BasePart]: Vector3 } = {}
	for _, p in list do
		local v = ref:PointToObjectSpace(p.Position)
		at[p] = v; lo = lo:Min(v); hi = hi:Max(v)
	end
	local span = hi - lo
	local axis = if span.X >= span.Y and span.X >= span.Z then "X" elseif span.Y >= span.Z then "Y" else "Z"
	local len = math.max((span :: any)[axis], 1e-3)
	local painted = {}
	for _, p in list do if paints(md, zoneOf(p, m)) then table.insert(painted, p) end end
	-- the same order everywhere (server, client, preview): along the weapon, then by name
	table.sort(painted, function(a, b)
		local za, zb = (at[a] :: any)[axis], (at[b] :: any)[axis]
		if math.abs(za - zb) > 1e-3 then return za < zb end
		return a.Name < b.Name
	end)
	local n = #wr.pal
	local mat = if wr.mat then (Enum.Material :: any)[wr.mat] else Enum.Material.SmoothPlastic
	local pic = picture(wr.id)
	-- on an unfolded gun a picture wrap leaves the pieces without UVs alone: those are its glow and glass parts
	-- (WeaponImport gives them no WrapUV), and the old palette made them pale shards amid the picture
	local unfolded = false
	if pic then
		for _, p in painted do
			if p:IsA("MeshPart") and p:GetAttribute("WrapUV") then unfolded = true; break end
		end
	end
	for i, p in painted do
		local uv = p:IsA("MeshPart") and p:GetAttribute("WrapUV")
		if unfolded and not uv then continue end
		remember(p)
		if pic and uv then
			local old = p:FindFirstChildOfClass("SurfaceAppearance")
			if old then stash[p] = old; old.Parent = nil end
			p.TextureID = ""; p.Material = Enum.Material.SmoothPlastic; p.Reflectance = 0
			local t0 = p:GetAttribute("WrapTr")
			p.Transparency = if type(t0) == "number" then t0 else 0
			local s = pic:Clone()
			s.Name = "WrapSA"
			s:SetAttribute("Wrap", wr.id) -- (client/WrapAnim finds the animated ones by this and the tag: glow, tint)
			s:AddTag("WrapSA")
			s.Parent = p
			continue
		end
		local u = ((at[p] :: any)[axis] - (lo :: any)[axis]) / len
		local k = 1
		if wr.pat == "alt" then k = (i - 1) % 2 + 1
		elseif wr.pat == "cycle" then k = (i - 1) % n + 1
		elseif wr.pat == "speck" then k = if i % 3 == 0 and n > 1 then 2 + (math.floor(i / 3) - 1) % (n - 1) else 1
		elseif wr.pat == "bands" then k = math.clamp(math.floor(u * n) + 1, 1, n) end
		local c = wr.pal[k]
		if wr.pat == "fade" and n > 1 then
			local x = u * (n - 1)
			local j = math.clamp(math.floor(x) + 1, 1, n - 1)
			c = wr.pal[j]:Lerp(wr.pal[j + 1], x - (j - 1))
			k = if x - (j - 1) < 0.5 then j else j + 1
		end
		p.Color = c
		p.Material = if wr.neon and table.find(wr.neon, k) then Enum.Material.Neon else mat
		p.Reflectance = wr.refl or 0
		local t0 = p:GetAttribute("WrapTr")
		p.Transparency = math.max(if type(t0) == "number" then t0 else 0, wr.tr or 0)
		if p:IsA("MeshPart") then p.TextureID = "" end
		local sa = p:FindFirstChildOfClass("SurfaceAppearance")
		if sa then stash[p] = sa; sa.Parent = nil end
	end
	-- a wrap is a palette (docs/WRAP-TEXTURES.md, after the Rivals study): on HANDLE or BUSINESS END the other half of
	-- the gun takes a dark tone of the same wrap (the picture tinted down by its Second colour, or the palette's first
	-- colour darkened), not the gun's factory paint, so the gun reads as one design in two tones. trims (_wzN), glow and
	-- glass keep their look; the gun's glow pieces take the wrap's Accent
	if md ~= "full" then
		local other = if md == "reverse" then "a" else "b"
		local sec = if pic then pic:GetAttribute("Second") else nil
		for _, p in list do
			if zoneOf(p, m) ~= other then continue end
			if p.Material == Enum.Material.Neon or p.Material == Enum.Material.Glass then continue end
			local uv = p:IsA("MeshPart") and p:GetAttribute("WrapUV")
			if pic and unfolded and not uv then continue end
			remember(p)
			local old = p:FindFirstChildOfClass("SurfaceAppearance")
			if old then stash[p] = old; old.Parent = nil end
			if p:IsA("MeshPart") then p.TextureID = "" end
			p.Material = Enum.Material.SmoothPlastic; p.Reflectance = 0
			if pic and uv then
				local s = pic:Clone()
				s.Name = "WrapSA"
				s.Color = if typeof(sec) == "Color3" then sec else Color3.new(0.35, 0.35, 0.35)
				s.EmissiveStrength = pic.EmissiveStrength * 0.3
				s:SetAttribute("Wrap", wr.id)
				s:AddTag("WrapSA")
				s.Parent = p
			else
				local c = wr.pal[1]
				p.Color = Color3.new(c.R * 0.35, c.G * 0.35, c.B * 0.35)
			end
		end
	end
	if pic and unfolded and pic:GetAttribute("Decal") then
		local worn = {}
		for _, p in list do if p:FindFirstChild("WrapSA") then table.insert(worn, p) end end
		hole(m, worn, ref, pic, list)
	end
	local acc = if pic then pic:GetAttribute("Accent") else nil
	if typeof(acc) == "Color3" then
		for _, p in list do
			if p.Material == Enum.Material.Neon and not (p:IsA("MeshPart") and p:GetAttribute("WrapUV")) then
				remember(p)
				p.Color = acc
			end
		end
	end
end

-- a player's wrap on one weapon, from the "Wraps" attribute the server keeps ("redline=cherry/normal;katana=gold/full")
function WeaponModels.wrapFor(p: Player, wid: string): (string?, string?)
	local s = p:GetAttribute("Wraps")
	if type(s) ~= "string" then return nil, nil end
	for w, id, md in string.gmatch(s, "([%w_]+)=([%w_]+)/(%a+)") do
		if w == wid then return id, md end
	end
	return nil, nil
end

return WeaponModels
