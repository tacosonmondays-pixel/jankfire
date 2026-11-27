--!strict
-- ZOMBIES' kit for the clients (27 Nov 2026; roblox/docs/ZOMBIES.md 4): ReplicatedStorage.JankfireZmKit. Studio, Edit:
--   require(game.ServerStorage.PolishBackup.ZmKit).importHeli(<asset id>, <name>?)
-- loads an uploaded helicopter as a Model in JankfireZmKit (default name "Heli"): anchored, no collisions, its pivot at
-- the skids' feet under the rotor's hub, nose -Z. Each piece is painted from its name ("zh_<piece>__<code>",
-- rbxglb.look_code: p plastic, n neon, g glass + alpha, t textured = keep its picture, white under it) and named
-- zh_<piece>. ZM.X.heli says which one the game flies (ZombieExtract.client).
--   "Heli"          the first, chunky one (tools/roblox/zm_heli_models.py)
--   "HeliA"/"HeliB" the web game's JANK NEWS heli rebuilt without writing (tools/roblox/zm_heli2_models.py), schemes
--                   A and B. Their marker cubes (zh_hubmark, zh_tailmark, zh_searchmark, zh_nosemark) set the pivot and
--                   the model's attributes HubMain / HubTail / SearchPin (pivot space), then go
local InsertService = game:GetService("InsertService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local K = {}

local function paint(p: BasePart, code: string)
	local kind, hex = string.sub(code, 1, 1), string.sub(code, 2, 7)
	if kind == "t" then
		-- a picture (glTF baseColorTexture) arrives as the MeshPart's TextureID: white under it
		p.Color = Color3.new(1, 1, 1)
		p.Material = Enum.Material.SmoothPlastic
		return
	end
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

function K.importHeli(id: number, name: string?): string
	local box = InsertService:LoadAsset(id)
	local heli = Instance.new("Model")
	heli.Name = name or "Heli"
	local n = 0
	local marks: { [string]: Vector3 } = {}
	for _, d in box:GetDescendants() do
		if not d:IsA("MeshPart") then continue end
		local full = d.Name
		local piece, code = string.match(full, "^(.-)__(%w+)")
		if not piece then piece, code = full, "p4b5148" end
		local p = d :: MeshPart
		if string.sub(piece :: string, -4) == "mark" then marks[piece :: string] = p.Position; continue end
		paint(p, code :: string)
		p.Name = piece :: string
		p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch = true, false, false, false
		-- (27 Nov test: the Glass material at 0.4 read as dark panels at night; clearer, so the cabin and its light read)
		if piece == "zh_glass" or piece == "zh_doorglass" then p.Material = Enum.Material.SmoothPlastic; p.Transparency = 0.62; p.Reflectance = 0.18 end
		p.Parent = heli
		n += 1
	end
	box:Destroy()
	local body = heli:FindFirstChild("zh_body")
	if body and body:IsA("BasePart") then heli.PrimaryPart = body end
	-- the pivot (LoadAsset centres a model, so the file's origin is lost): under the rotor's hub, at the skids' lowest
	-- point, facing the nose. the markers say where the hub and the nose are; the first heli has no markers: its rotor's
	-- centre is the hub, and its searchlight (zh_lamp) is under the nose
	local minY = math.huge
	for _, p in heli:GetChildren() do if p:IsA("BasePart") then minY = math.min(minY, p.Position.Y - p.Size.Y / 2) end end
	local rotor, lamp = heli:FindFirstChild("zh_rotor") :: BasePart?, heli:FindFirstChild("zh_lamp") :: BasePart?
	local hub = marks.zh_hubmark or (rotor and rotor.Position)
	local front = marks.zh_nosemark or (lamp and lamp.Position)
	local piv = nil
	if hub and front then
		local P = Vector3.new(hub.X, minY, hub.Z)
		local nose = Vector3.new(front.X - P.X, 0, front.Z - P.Z).Unit
		piv = CFrame.lookAt(P, P + nose)
		-- (with a PrimaryPart the model's pivot is that part's PivotOffset: WorldPivot alone is ignored)
		if heli.PrimaryPart then heli.PrimaryPart.PivotOffset = heli.PrimaryPart.CFrame:ToObjectSpace(piv) else heli.WorldPivot = piv end
		heli:SetAttribute("HubMain", piv:PointToObjectSpace(hub))
		if marks.zh_tailmark then heli:SetAttribute("HubTail", piv:PointToObjectSpace(marks.zh_tailmark)) end
		if marks.zh_searchmark then heli:SetAttribute("SearchPin", piv:PointToObjectSpace(marks.zh_searchmark)) end
		if marks.zh_doormark then heli:SetAttribute("DoorAt", piv:PointToObjectSpace(marks.zh_doormark)) end -- (the sliding door's centre)
	end
	local kit = ReplicatedStorage:FindFirstChild("JankfireZmKit")
	if not kit then
		kit = Instance.new("Folder")
		kit.Name = "JankfireZmKit"
		kit.Parent = ReplicatedStorage
	end
	local old = kit:FindFirstChild(heli.Name)
	if old then old:Destroy() end
	-- (park it far below everything: a clone is moved by its pivot anyway)
	heli:PivotTo(CFrame.new(0, -500, 0)) -- (and nose -Z)
	heli.Parent = kit
	local s, e = heli:GetBoundingBox()
	return string.format("%s: %d pieces, box %.1f x %.1f x %.1f at %s, hub %s", heli.Name, n, e.X, e.Y, e.Z, tostring(s.Position),
		tostring(heli:GetAttribute("HubMain")))
end

return K
