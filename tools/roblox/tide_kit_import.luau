-- (Edit, execute_luau) THE TIDECREST KATANA AND SHEATH for client/FinisherPro.luau, into
-- ReplicatedStorage.JankfireFinisherSets.TidecrestKit (26 Nov 2026). The pro animator keyed the katana and the sheath on
-- their own tracks against our katana package (vault Exports\Katana for animator, tools/blender/katana_for_animator.py):
-- its Tidecrest KatanaModel (the Katana part at the grip, the blade from the guard face along -z, 3.22 studs) and
-- SheathModel (the Sheath part at the mouth, running along -z). The meshes come from the package's mesh upload (KIT);
-- each piece's place against its root, size, colour and material are the package's own (read out of its .rbxm by
-- tools/roblox/rbxm_read.py). FinisherPro clones these, anchors them and moves them every frame.
local KIT = 70393251319016
local D = {
	KatanaModel = { root = "Katana", atts = { Grip = { 0.0000, 0.0000, 0.0000 }, GuardFace = { 0.0000, 0.0000, -0.6200 }, BladeTip = { 0.0000, 0.1810, -3.8400 } }, parts = {
		{ "kat_blade_blade", { 0.0000, 0.0421, -2.2300, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.0500, 0.2797, 3.2200 }, { 44, 47, 55 }, 272, 0.00 },
		{ "kat_collar", { 0.0000, 0.0060, -0.6840, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.0900, 0.2280, 0.1320 }, { 196, 160, 86 }, 272, 0.00 },
		{ "kat_blade_gold", { -0.0000, 0.0827, -1.6182, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.0569, 0.0531, 1.8676 }, { 196, 160, 86 }, 272, 0.00 },
		{ "kat_beads", { 0.0000, 0.0000, -0.0270, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.1741, 0.2100, 0.8333 }, { 143, 114, 56 }, 272, 0.00 },
		{ "kat_tsuka", { 0.0000, 0.0000, -0.0290, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.1344, 0.1681, 0.8580 }, { 42, 37, 38 }, 272, 0.00 },
		{ "kat_fuchi", { 0.0000, 0.0000, -0.4710, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.1555, 0.1895, 0.0760 }, { 196, 160, 86 }, 272, 0.00 },
		{ "kat_guard_rim", { 0.0000, 0.0000, -0.5640, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.4800, 0.4800, 0.0920 }, { 196, 160, 86 }, 272, 0.00 },
		{ "kat_menuki_pale", { 0.0000, -0.0042, -0.0590, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.1825, 0.1060, 0.1609 }, { 236, 220, 174 }, 272, 0.00 },
		{ "kat_pommel", { 0.0000, 0.0000, 0.4350, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.1560, 0.1900, 0.1100 }, { 196, 160, 86 }, 272, 0.00 },
		{ "kat_seppa_back", { 0.0000, 0.0000, -0.5160, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.1760, 0.2360, 0.0160 }, { 196, 160, 86 }, 272, 0.00 },
		{ "kat_wrap_b", { 0.0006, 0.0000, -0.0265, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.1584, 0.1923, 0.8504 }, { 196, 160, 86 }, 272, 0.00 },
		{ "kat_guard", { 0.0000, 0.0000, -0.5640, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.4520, 0.4520, 0.0800 }, { 52, 53, 59 }, 272, 0.00 },
		{ "kat_blade_paleedge", { 0.0000, 0.0409, -2.2300, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.0360, 0.2806, 3.2200 }, { 207, 211, 217 }, 272, 0.00 },
		{ "kat_wrap_a", { 0.0006, -0.0000, -0.0265, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.1584, 0.1923, 0.8504 }, { 196, 160, 86 }, 272, 0.00 },
		{ "kat_menuki_heart", { 0.0000, -0.0015, -0.0597, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.1885, 0.0607, 0.1132 }, { 212, 154, 166 }, 272, 0.00 },
		{ "kat_seppa_front", { 0.0000, 0.0000, -0.6120, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.1760, 0.2360, 0.0160 }, { 196, 160, 86 }, 272, 0.00 },
	} },
	SheathModel = { root = "Sheath", atts = { SheathMouth = { 0.0000, 0.0000, 0.0000 }, SheathHip = { -0.1200, 0.0000, -0.4200 } }, parts = {
		{ "saya_slot", { 0.0000, 0.0060, -0.0015, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.0620, 0.2120, 0.0090 }, { 20, 21, 25 }, 272, 0.00 },
		{ "saya_cord", { -0.1038, 0.1358, -0.4200, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.0320, 0.2704, 0.1804 }, { 138, 46, 39 }, 272, 0.00 },
		{ "saya_mouth", { 0.0000, 0.0120, -0.0425, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.1679, 0.3178, 0.0850 }, { 196, 160, 86 }, 272, 0.00 },
		{ "saya_bands", { -0.0000, 0.0476, -1.7554, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.1548, 0.3230, 1.0916 }, { 196, 160, 86 }, 272, 0.00 },
		{ "saya_body", { 0.0000, 0.0502, -1.6650, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.1496, 0.3750, 3.1900 }, { 42, 37, 38 }, 272, 0.00 },
		{ "saya_blossoms_pale", { -0.0000, 0.0439, -1.7293, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.1637, 0.1277, 0.1933 }, { 236, 220, 174 }, 272, 0.00 },
		{ "saya_knob", { -0.0913, 0.0158, -0.4200, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.0550, 0.0840, 0.0680 }, { 196, 160, 86 }, 272, 0.00 },
		{ "saya_blossoms_heart", { -0.0000, 0.0472, -1.7301, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.1697, 0.0728, 0.1358 }, { 212, 154, 166 }, 272, 0.00 },
		{ "saya_cap", { -0.0000, 0.1120, -3.2950, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000, 0.0000, 0.0000, 1.0000 }, { 0.1441, 0.2652, 0.1300 }, { 196, 160, 86 }, 272, 0.00 },
	} },
}
local IS = game:GetService("InsertService")
local RS = game:GetService("ReplicatedStorage")
local sets = RS:FindFirstChild("JankfireFinisherSets")
if not sets then sets = Instance.new("Folder"); sets.Name = "JankfireFinisherSets"; sets.Parent = RS end
local root = IS:LoadAsset(KIT)
-- the upload's pieces by name: "kat_blade__blade_Node" holds the mesh for the package's "kat_blade_blade"
local byName = {}
for _, mp in root:GetDescendants() do
	if mp:IsA("MeshPart") then
		local nm = if mp.Parent and string.find(mp.Parent.Name, "__") then mp.Parent.Name else mp.Name
		local base, col = string.match(nm, "^(.-)__(%w+)_Node$")
		if base then
			byName[base .. "_" .. col] = mp
			byName[base] = byName[base] or mp
		end
	end
end
local kit = Instance.new("Folder")
kit.Name = "TidecrestKit"
local report = {}
for mname, m in D do
	local model = Instance.new("Model")
	model.Name = mname
	local r = Instance.new("Part")
	r.Name = m.root; r.Size = Vector3.new(0.2, 0.2, 0.2); r.Transparency = 1; r.Anchored = true; r.CanCollide = false; r.CanQuery = false
	r.CanTouch = false; r.CFrame = CFrame.new(); r.Parent = model
	for an, p in m.atts do local a = Instance.new("Attachment"); a.Name = an; a.Position = Vector3.new(p[1], p[2], p[3]); a.Parent = r end
	for _, q in m.parts do
		local src = byName[q[1]]
		if not src then table.insert(report, "MISSING " .. q[1]); continue end
		local c = src:Clone()
		for _, x in c:GetChildren() do if not x:IsA("SurfaceAppearance") then x:Destroy() end end
		c.Name = q[1]
		local want = Vector3.new(q[3][1], q[3][2], q[3][3])
		-- (the mesh's own axes: its loaded size must line up with the package's, else say so)
		local s = c.Size
		local function near(a, b) return math.abs(a - b) <= math.max(0.02, 0.08 * b) end
		if not (near(s.X, want.X) and near(s.Y, want.Y) and near(s.Z, want.Z)) then
			table.insert(report, ("AXES %s: upload %.3f %.3f %.3f vs %.3f %.3f %.3f"):format(q[1], s.X, s.Y, s.Z, want.X, want.Y, want.Z))
		end
		c.Size = want
		local t = q[2]
		c.CFrame = CFrame.new(t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10], t[11], t[12])
		c.Color = Color3.fromRGB(q[4][1], q[4][2], q[4][3])
		c.Transparency = q[6]
		c.Anchored = true; c.CanCollide = false; c.CanQuery = false; c.CanTouch = false; c.Massless = true
		-- (27 Nov, films with no pop-in: the blade and the sheath at full detail - RenderFidelity can't change at run time)
		if c:IsA("MeshPart") then c.RenderFidelity = Enum.RenderFidelity.Precise end
		c.Parent = model
	end
	model.PrimaryPart = r
	model.Parent = kit
	table.insert(report, mname .. ": " .. (#model:GetChildren() - 1) .. " pieces")
end
root:Destroy()
local old = sets:FindFirstChild("TidecrestKit"); if old then old:Destroy() end
kit.Parent = sets
return table.concat(report, " | ")
