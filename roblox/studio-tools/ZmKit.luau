--!strict
-- ZOMBIES' kit for the clients (27 Nov 2026; roblox/docs/ZOMBIES.md 4): ReplicatedStorage.JankfireZmKit. Studio, Edit:
--   require(game.ServerStorage.PolishBackup.ZmKit).importHeli(<asset id>)
-- loads the uploaded helicopter (tools/roblox/zm_heli_models.py -> zm_heli.glb, uploaded as a Model), paints each piece
-- from its name ("zh_<piece>__<code>": p plastic, n neon, g glass + alpha; rbxglb.look_code), names it zh_<piece>, and
-- puts it in JankfireZmKit as "Heli": anchored, no collisions, its pivot at the skids' feet under the cabin, nose -Z
-- (ZombieExtract.client spins zh_rotor and zh_tail about their own centres)
local InsertService = game:GetService("InsertService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local K = {}

local function paint(p: BasePart, code: string)
	local kind, hex = string.sub(code, 1, 1), string.sub(code, 2, 7)
	local ok, c = pcall(Color3.fromHex, hex)
	if ok then p.Color = c end
	if kind == "n" then p.Material = Enum.Material.Neon
	elseif kind == "g" then
		p.Material = Enum.Material.Glass
		local a = tonumber(string.sub(code, 8, 9), 16)
		if a then p.Transparency = 1 - a / 255 end
	else
		p.Material = Enum.Material.SmoothPlastic
	end
end

function K.importHeli(id: number): string
	local box = InsertService:LoadAsset(id)
	local heli = Instance.new("Model")
	heli.Name = "Heli"
	local n = 0
	for _, d in box:GetDescendants() do
		if not d:IsA("MeshPart") then continue end
		local full = d.Name
		local piece, code = string.match(full, "^(.-)__(%w+)")
		if not piece then piece, code = full, "p4b5148" end
		local p = d :: MeshPart
		paint(p, code :: string)
		p.Name = piece :: string
		p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch = true, false, false, false
		if piece == "zh_glass" then p.Reflectance = 0.12 end
		p.Parent = heli
		n += 1
	end
	box:Destroy()
	local body = heli:FindFirstChild("zh_body")
	if body and body:IsA("BasePart") then heli.PrimaryPart = body end
	-- the pivot (27 Nov test: LoadAsset centres a model, so the file's origin is lost): under the rotor's hub, at the
	-- skids' lowest point, facing the nose (the searchlight is under it)
	local rotor, lamp = heli:FindFirstChild("zh_rotor") :: BasePart?, heli:FindFirstChild("zh_lamp") :: BasePart?
	local minY = math.huge
	for _, p in heli:GetChildren() do if p:IsA("BasePart") then minY = math.min(minY, p.Position.Y - p.Size.Y / 2) end end
	if rotor and lamp then
		local P = Vector3.new(rotor.Position.X, minY, rotor.Position.Z)
		local nose = Vector3.new(lamp.Position.X - P.X, 0, lamp.Position.Z - P.Z).Unit
		local piv = CFrame.lookAt(P, P + nose)
		-- (with a PrimaryPart the model's pivot is that part's PivotOffset: WorldPivot alone is ignored)
		if heli.PrimaryPart then heli.PrimaryPart.PivotOffset = heli.PrimaryPart.CFrame:ToObjectSpace(piv) else heli.WorldPivot = piv end
	end
	local kit = ReplicatedStorage:FindFirstChild("JankfireZmKit")
	if not kit then
		kit = Instance.new("Folder")
		kit.Name = "JankfireZmKit"
		kit.Parent = ReplicatedStorage
	end
	local old = kit:FindFirstChild("Heli")
	if old then old:Destroy() end
	-- (park it far below everything: a clone is moved by its pivot anyway)
	heli:PivotTo(CFrame.new(0, -500, 0)) -- (and nose -Z)
	heli.Parent = kit
	local s, e = heli:GetBoundingBox()
	return string.format("Heli: %d pieces, box %.1f x %.1f x %.1f at %s", n, e.X, e.Y, e.Z, tostring(s.Position))
end

return K
