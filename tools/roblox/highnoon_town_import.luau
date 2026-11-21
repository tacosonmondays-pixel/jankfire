-- (Edit, execute_luau) HIGH NOON'S KIT TOWNS into ReplicatedStorage.JankfireFinisherSets: each kit upload (built by
-- tools/roblox/highnoon_town.py, A or B, uploaded as a Model under the owner's account) painted from its pieces' names
-- and pivoted on its origin marker, plus the blank cowboy onlooker (a plain blocky R15, no face, a hat, a bandana, a
-- vest; its gear comes from the first town imported). The owner picked TOWN A on 20 Nov: only A is in the place.
-- B is the spare, a switch away: put "B" in TOWNS below and run this, then set FinisherScene's EXTRA.highnoon.town = "B"
-- (its onlookers' spots are already in FinisherTownData). The uploads:
-- (A: 102998946016322 since 21 Nov 00:00 UTC, the rooms 5.7 studs deep - the onlookers' clips swing 2.3 studs each way;
-- before that 129998660975275 (3.7 deep, never in the place) and 100621445605287 (1.9 deep))
local UPLOADS = { HighNoonTownA = 102998946016322, HighNoonTownB = 134839016753792 }
local TOWNS = { "A" } -- the towns to (re)import
local IS = game:GetService("InsertService")
local RS = game:GetService("ReplicatedStorage")
local folder = RS:FindFirstChild("JankfireFinisherSets")
if not folder then folder = Instance.new("Folder"); folder.Name = "JankfireFinisherSets"; folder.Parent = RS end
local function mat(n) local ok, m = pcall(function() return (Enum.Material :: any)[n] end); return if ok and m then m else nil end
local MAT = { planks = mat("WoodPlanks"), wood = mat("Wood"), plaster = mat("Plaster") or mat("Sandstone"), shingle = mat("RoofShingles") or mat("Slate"),
	metal = mat("Metal"), fabric = mat("Fabric"), plastic = mat("SmoothPlastic"), glass = mat("Glass") }
local report = {}
local gearSrc = nil
local function import(id, name)
	local old = folder:FindFirstChild(name); if old then old:Destroy() end
	local root = IS:LoadAsset(id)
	local m = root:FindFirstChildWhichIsA("Model") or root
	local origin, n, west = nil, 0, { 0, 0 }
	for _, p in m:GetDescendants() do
		if p:IsA("BasePart") then
			n += 1
			local kind, hex = string.match(p.Name, "__(%a+)_(%x%x%x%x%x%x)$")
			if kind then p.Color = Color3.fromHex(hex); p.Material = MAT[kind] or Enum.Material.SmoothPlastic end
			p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
			if string.sub(p.Name, 1, 9) == "kitorigin" then origin = p end
		end
	end
	if not origin then root:Destroy(); return name .. ": NO ORIGIN" end
	local o = origin.Position + Vector3.new(0, 60, 0)
	-- (the west row must sit at -x from the origin: the upload's axes check)
	for _, p in m:GetDescendants() do
		if p:IsA("BasePart") and string.sub(p.Name, 1, 4) == "west" then west[1] += (p.Position.X - o.X); west[2] += 1 end
	end
	local mm = Instance.new("Model")
	mm.Name = name
	for _, p in m:GetDescendants() do if p:IsA("BasePart") then p.Parent = mm end end
	origin:Destroy()
	mm.WorldPivot = CFrame.new(o)
	-- the gear (parked 40 under the street): kept once for the onlooker, then out of the town
	local g = {}
	for _, p in mm:GetChildren() do
		if string.sub(p.Name, 1, 4) == "gear" then table.insert(g, p) end
	end
	if not gearSrc then
		gearSrc = {}
		for _, p in g do local c = p:Clone(); c:SetAttribute("Rel", c.Position - o); table.insert(gearSrc, c) end
	end
	for _, p in g do p:Destroy() end
	mm.Parent = folder
	root:Destroy()
	return string.format("%s: %d parts, west mean x %.1f", name, n, west[1] / math.max(1, west[2]))
end
for _, t in TOWNS do
	local name = "HighNoonTown" .. t
	table.insert(report, import(UPLOADS[name], name))
end
-- the onlooker
local old = folder:FindFirstChild("Onlooker"); if old then old:Destroy() end
local P = game:GetService("Players")
local npc = P:CreateHumanoidModelFromDescription(Instance.new("HumanoidDescription"), Enum.HumanoidRigType.R15)
npc.Name = "Onlooker"
for _, d in npc:GetDescendants() do
	if d:IsA("Decal") then d:Destroy() end      -- (no face)
	if d:IsA("Script") or d:IsA("LocalScript") then d:Destroy() end
end
npc:PivotTo(CFrame.new(0, 200, 0))
local head = npc:FindFirstChild("Head")
local ut = npc:FindFirstChild("UpperTorso")
local k = head.Size.X / 1.3
for _, p in gearSrc or {} do
	local rel = p:GetAttribute("Rel")
	p:SetAttribute("Rel", nil)
	if string.sub(p.Name, 1, 7) == "gearhat" then
		-- (the hat's base was at (0, -40, 0): it sits on the head's top, a little down over it)
		local base = head.CFrame * CFrame.new(0, head.Size.Y / 2 - 0.25 * k, 0)
		p.Size = p.Size * k
		p.CFrame = base * CFrame.new((rel - Vector3.new(0, -40, 0)) * k)
		p:SetAttribute("Gear", "hat")
		local w = Instance.new("WeldConstraint"); w.Part0 = head; w.Part1 = p; w.Parent = p
	elseif string.sub(p.Name, 1, 11) == "gearbandana" then
		p.Size = p.Size * k
		p.CFrame = head.CFrame * CFrame.new(0, -head.Size.Y * 0.32 - 0.1 * k, -head.Size.Z / 2 - 0.08)
		p:SetAttribute("Gear", "bandana")
		local w = Instance.new("WeldConstraint"); w.Part0 = head; w.Part1 = p; w.Parent = p
	elseif string.sub(p.Name, 1, 8) == "gearvest" then
		p.Size = Vector3.new(ut.Size.X * 1.06, ut.Size.Y * 0.92, ut.Size.Z * 1.18)
		p.CFrame = ut.CFrame * CFrame.new(0, -ut.Size.Y * 0.03, 0)
		p:SetAttribute("Gear", "vest")
		local w = Instance.new("WeldConstraint"); w.Part0 = ut; w.Part1 = p; w.Parent = p
	end
	p.Anchored = false; p.CanCollide = false; p.Massless = true
	p.Parent = npc
end
npc.Parent = folder
local hum = npc:FindFirstChildOfClass("Humanoid")
table.insert(report, string.format("Onlooker: head %s, torso %s, hip %.2f, animator %s, gear %d", tostring(head.Size), tostring(ut.Size), hum.HipHeight,
	tostring(hum:FindFirstChildOfClass("Animator") ~= nil), #(gearSrc or {})))
return table.concat(report, " | ")
