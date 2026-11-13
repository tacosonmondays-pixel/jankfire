--!strict
-- the three weapons as chunky code models (boxes and cylinders, from public/js/models.js redlineBuild / marbles and
-- public/js/blades/katana.js), in the web game's own frame: metres, -Z is forward, the grip near the origin. they keep
-- the spots the effects use (Muzzle, Sight, Grip attachments; the Redline's needle and vents; the katana's blade, which
-- stretches with kills). when the Blender model has been imported into ReplicatedStorage.JankfireWeapons (w_redline,
-- w_marbles, w_katana: see roblox/README.md), its pieces are fitted onto the same frame and the boxes hide.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local WeaponModels = {}

-- the Blender files' bounding boxes (metres, the file's frame): tools/roblox/export_weapons.py writes these
WeaponModels.FILES = {
	w_redline = { lo = Vector3.new(-0.0419, -0.1828, -0.505), hi = Vector3.new(0.0419, 0.0814, 0.2706) },
	w_marbles = { lo = Vector3.new(-0.0543, -0.1386, -0.3684), hi = Vector3.new(0.0543, 0.1479, 0.11) },
	w_katana = { lo = Vector3.new(-0.0345, -0.0617, -0.8357), hi = Vector3.new(0.0345, 0.0829, 0.1312) },
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

-- fit an imported Blender model (the importer's own scale and spot) onto the code model's frame
local function fitImported(b: Builder, tmpl: Model, file: { lo: Vector3, hi: Vector3 })
	local tcf, tsize = tmpl:GetBoundingBox()
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
			if string.find(n, "kat_blade", 1, true) then d.Name = "blade"
			elseif string.find(n, "needle", 1, true) then d.Name = "needle"
			elseif string.find(n, "vent", 1, true) then d.Name = "vent" end
			d.Parent = b.model
		end
	end
	copy:Destroy()
end

-- build a weapon. k = studs per web metre (viewmodel: 3 x its VM scale, third person: 3 x 1.5)
function WeaponModels.build(id: string, k: number): Model?
	local fn = BUILD[id]
	if not fn then return nil end
	local m = Instance.new("Model")
	m.Name = id
	local root = Instance.new("Part")
	root.Name = "Root"; root.Size = Vector3.new(0.05, 0.05, 0.05); root.Transparency = 1
	root.Anchored = false; root.CanCollide = false; root.CanQuery = false; root.CanTouch = false; root.Massless = true
	root.Parent = m
	m.PrimaryPart = root
	local b: Builder = { model = m, root = root, k = k }
	fn(b)
	for _, c in m:GetChildren() do if c:IsA("BasePart") and c ~= root then c:SetAttribute("Code", true) end end
	local lib = ReplicatedStorage:FindFirstChild("JankfireWeapons")
	local tmpl = lib and lib:FindFirstChild("w_" .. id)
	local file = (WeaponModels.FILES :: any)["w_" .. id]
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

return WeaponModels
