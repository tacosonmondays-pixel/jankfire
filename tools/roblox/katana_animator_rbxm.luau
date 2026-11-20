-- THE KATANA FOR THE ANIMATOR, AS AN .rbxm (20 Nov 2026). Run in Studio (Edit) through execute_luau after uploading
-- tools/blender/katana_for_animator.py's roblox/katana_sheath_roblox.glb as a Model (Open Cloud). It loads that upload,
-- paints each piece from its name ("<part>__<colour>"), builds:
--   KatanaModel   root part "Katana" (at Grip) + its pieces welded on, Attachments Grip / GuardFace / BladeTip
--   SheathModel   root part "Sheath" (at SheathMouth) + its pieces, Attachments SheathMouth / SheathHip
--   Rig           a blank block R15 (the place's own sizes and Motor6Ds) holding copies of both: Motor6D "Katana"
--                 (RightHand -> Katana) and Motor6D "Sheath" (LowerTorso -> Sheath), so the Animation Editor shows a
--                 Katana track and a Sheath track
-- and returns the folder serialized (SerializationService) as base64: the caller writes it out as the .rbxm.
local ASSETS = { Blank = 100140368503106, Tidecrest = 77461839355162 }   -- (the two uploads, 20 Nov)
local COL = { steel = "a7adb5", edge = "e6eaef", spine = "7a8089", brass = "9c8c6a", iron = "3a3d45", core = "d6d1c4",
	wrap = "2b2e35", lacquer = "2a2c33", horn = "a9a49b", cord = "6f675b", slot = "141519", body = "cfcbc3",
	blade = "2c2f37", paleedge = "cfd3d9", tciron = "34353b", lac = "2a2526", gold = "c4a056", goldd = "8f7238",
	pale = "ecdcae", heart = "d49aa6", red = "8a2e27" }
local Z_FACE = -0.62
local GRIP_IN_HAND = CFrame.new(0, -0.12, 0)
local HIP = CFrame.new(-1.1200, 0.1000, -0.7500, 0.99903, 0.02197, 0.03815, -0.00000, -0.86664, 0.49894, 0.04403, -0.49845, -0.86580)
local SIZE = { HumanoidRootPart = Vector3.new(2, 2, 1), LowerTorso = Vector3.new(2, 0.4, 1), UpperTorso = Vector3.new(2, 1.6, 1),
	Head = Vector3.new(1.2, 1.2, 1.2), RightUpperArm = Vector3.new(1, 1.1687, 1), RightLowerArm = Vector3.new(1, 1.0519, 1),
	RightHand = Vector3.new(1, 0.3, 1), LeftUpperArm = Vector3.new(1, 1.1687, 1), LeftLowerArm = Vector3.new(1, 1.0519, 1),
	LeftHand = Vector3.new(1, 0.3, 1), RightUpperLeg = Vector3.new(1, 1.2166, 1), RightLowerLeg = Vector3.new(1, 1.1931, 1),
	RightFoot = Vector3.new(1, 0.3, 1), LeftUpperLeg = Vector3.new(1, 1.2166, 1), LeftLowerLeg = Vector3.new(1, 1.1931, 1),
	LeftFoot = Vector3.new(1, 0.3, 1) }
local JOINTS = {
	{ "Root", "HumanoidRootPart", "LowerTorso", Vector3.new(0, -1, 0), Vector3.new(0, -0.2, 0) },
	{ "Waist", "LowerTorso", "UpperTorso", Vector3.new(0, 0.2, 0), Vector3.new(0, -0.8, 0) },
	{ "Neck", "UpperTorso", "Head", Vector3.new(0, 0.8, 0), Vector3.new(0, -0.586, 0) },
	{ "RightShoulder", "UpperTorso", "RightUpperArm", Vector3.new(1, 0.563, 0), Vector3.new(-0.5, 0.3943, 0) },
	{ "RightElbow", "RightUpperArm", "RightLowerArm", Vector3.new(0, -0.3342, 0), Vector3.new(0, 0.2586, 0) },
	{ "RightWrist", "RightLowerArm", "RightHand", Vector3.new(0, -0.5009, 0), Vector3.new(0, 0.125, 0) },
	{ "LeftShoulder", "UpperTorso", "LeftUpperArm", Vector3.new(-1, 0.563, 0), Vector3.new(0.5, 0.3943, 0) },
	{ "LeftElbow", "LeftUpperArm", "LeftLowerArm", Vector3.new(0, -0.3341, 0), Vector3.new(0, 0.2587, 0) },
	{ "LeftWrist", "LeftLowerArm", "LeftHand", Vector3.new(0, -0.5009, 0), Vector3.new(0, 0.125, 0) },
	{ "RightHip", "LowerTorso", "RightUpperLeg", Vector3.new(0.5, -0.2, 0), Vector3.new(0, 0.4208, 0) },
	{ "RightKnee", "RightUpperLeg", "RightLowerLeg", Vector3.new(0, -0.4009, 0), Vector3.new(0, 0.3792, 0) },
	{ "RightAnkle", "RightLowerLeg", "RightFoot", Vector3.new(0, -0.5472, 0), Vector3.new(0, 0.1019, 0) },
	{ "LeftHip", "LowerTorso", "LeftUpperLeg", Vector3.new(-0.5, -0.2, 0), Vector3.new(0, 0.4208, 0) },
	{ "LeftKnee", "LeftUpperLeg", "LeftLowerLeg", Vector3.new(0, -0.4011, 0), Vector3.new(0, 0.379, 0) },
	{ "LeftAnkle", "LeftLowerLeg", "LeftFoot", Vector3.new(0, -0.5472, 0), Vector3.new(0, 0.1019, 0) },
}

local SS = game:GetService("ServerStorage")
local old = SS:FindFirstChild("KatanaForAnimatorTmp")
if old then old:Destroy() end
local folder = Instance.new("Folder")
folder.Name = "KatanaForAnimatorTmp"

local pieces = {}
local function load(asset)
	local loaded = game:GetService("InsertService"):LoadAsset(asset)
	pieces = {}
	for _, d in loaded:GetDescendants() do
		if d:IsA("MeshPart") then
			local nm = d.Name
			if d.Parent and d.Parent:IsA("Model") and d.Parent.Name:match("_Node$") then nm = d.Parent.Name:gsub("_Node$", "") end
			pieces[nm] = d
		end
	end
	return loaded
end

local function rootPart(name, cf)
	local p = Instance.new("Part")
	p.Name = name
	p.Size = Vector3.new(0.2, 0.2, 0.2)
	p.Transparency = 1
	p.CanCollide, p.CanQuery, p.CanTouch, p.Anchored = false, false, false, false
	p.Massless = true
	p.CFrame = cf
	return p
end

local function attach(p, name, pos)
	local a = Instance.new("Attachment")
	a.Name = name
	a.Position = pos
	a.Parent = p
end

local function buildPair()
	local km = Instance.new("Model"); km.Name = "KatanaModel"
	local sm = Instance.new("Model"); sm.Name = "SheathModel"
	local kr = rootPart("Katana", CFrame.new()); kr.Parent = km
	local sr = rootPart("Sheath", CFrame.new(0, 0, Z_FACE)); sr.Parent = sm
	attach(kr, "Grip", Vector3.new(0, 0, 0))
	attach(kr, "GuardFace", Vector3.new(0, 0, Z_FACE))
	attach(kr, "BladeTip", Vector3.new(0, 0.181, -2.92))
	attach(sr, "SheathMouth", Vector3.new(0, 0, 0))
	attach(sr, "SheathHip", Vector3.new(-0.12, 0, -0.42))
	local n = 0
	local many = {}
	for nm in pieces do
		local part = nm:match("^(.-)__%w+$") or nm
		many[part] = (many[part] or 0) + 1
	end
	for nm, src in pieces do
		local part, colour = nm:match("^(.-)__(%w+)$")
		part = part or nm
		local m = src:Clone()
		m.Name = (many[part] > 1 and colour) and (part .. "_" .. colour) or part   -- (kat_blade_edge / _steel / _spine)
		m.Color = Color3.fromHex(COL[colour] or "cccccc")
		m.Material = Enum.Material.SmoothPlastic
		m.CanCollide, m.CanQuery, m.CanTouch, m.Anchored = false, false, false, false
		m.Massless = true
		m.CastShadow = true
		local kat = part:sub(1, 4) == "kat_"
		m:SetAttribute("Part", part)
		m.Parent = kat and km or sm
		local w = Instance.new("WeldConstraint")
		w.Part0 = kat and kr or sr
		w.Part1 = m
		w.Parent = m
		n += 1
	end
	km.PrimaryPart = kr; sm.PrimaryPart = sr
	return km, sm, n
end

local total = 0
for _, style in { "Blank", "Tidecrest" } do
	local loaded = load(ASSETS[style])
	local sub = Instance.new("Folder")
	sub.Name = style
	sub.Parent = folder
	-- 1. the sheathed pair on its own, at the origin (the katana's Grip)
	local km, sm, n = buildPair()
	km.Parent = sub; sm.Parent = sub
	if style ~= "Blank" then   -- (the Tidecrest pair beside the blank one)
		km:PivotTo(CFrame.new(1.5, 0, 0) * km:GetPivot()); sm:PivotTo(CFrame.new(1.5, 0, 0) * sm:GetPivot())
	end

	-- 2. the blank R15 holding both
	local rig = Instance.new("Model"); rig.Name = "R15_Katana_Rig"
	local hum = Instance.new("Humanoid"); hum.RigType = Enum.HumanoidRigType.R15; hum.Parent = rig
	local parts = {}
	local centre = { HumanoidRootPart = Vector3.new(0, 3, 0) }
	for _, j in JOINTS do centre[j[3]] = centre[j[2]] + j[4] - j[5] end
	for name, size in SIZE do
		local p = Instance.new("Part")
		p.Name = name
		p.Size = size
		p.CFrame = CFrame.new(centre[name])
		p.Color = Color3.fromHex(COL.body)
		p.Material = Enum.Material.SmoothPlastic
		p.TopSurface, p.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
		p.Anchored = name == "HumanoidRootPart"
		if name == "HumanoidRootPart" then p.Transparency = 1; p.CanCollide = false end
		p.Parent = rig
		parts[name] = p
	end
	for _, j in JOINTS do
		local m6 = Instance.new("Motor6D")
		m6.Name = j[1]
		m6.Part0, m6.Part1 = parts[j[2]], parts[j[3]]
		m6.C0, m6.C1 = CFrame.new(j[4]), CFrame.new(j[5])
		m6.Parent = parts[j[3]]
		-- (the R15 rig attachments the avatar system expects at each joint)
		local a0 = Instance.new("Attachment"); a0.Name = j[1] .. "RigAttachment"; a0.Position = j[4]; a0.Parent = parts[j[2]]
		local a1 = Instance.new("Attachment"); a1.Name = j[1] .. "RigAttachment"; a1.Position = j[5]; a1.Parent = parts[j[3]]
	end
	rig.PrimaryPart = parts.HumanoidRootPart
	local km2, sm2 = buildPair()
	km2.Parent = rig; sm2.Parent = rig
	local kj = Instance.new("Motor6D"); kj.Name = "Katana"
	kj.Part0, kj.Part1 = parts.RightHand, km2.PrimaryPart
	kj.C0, kj.C1 = GRIP_IN_HAND, CFrame.new()
	kj.Parent = parts.RightHand
	local sj = Instance.new("Motor6D"); sj.Name = "Sheath"
	sj.Part0, sj.Part1 = parts.LowerTorso, sm2.PrimaryPart
	sj.C0, sj.C1 = HIP, CFrame.new()
	sj.Parent = parts.LowerTorso
	-- put the katana and sheath where their joints hold them (the welds carry the pieces)
	km2:PivotTo(parts.RightHand.CFrame * GRIP_IN_HAND)
	sm2:PivotTo(parts.LowerTorso.CFrame * HIP)
	rig:PivotTo(CFrame.new(8, 0, style == "Blank" and 0 or 6) * rig:GetPivot())
	rig.Parent = sub
	loaded:Destroy()
	total += n
end
folder.Parent = SS

local buf = game:GetService("SerializationService"):SerializeInstancesAsync({ folder })
local b64 = buffer.tostring(game:GetService("EncodingService"):Base64Encode(buf))
return ("pieces=%d bytes=%d\n%s"):format(total, buffer.len(buf), b64)
