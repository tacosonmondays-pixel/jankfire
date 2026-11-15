--!strict
-- swap the map's placeholder boxes for the Blender models once they're in the place. Import the files from
-- roblox/assets/<map>/ (Studio: Avatar or Home tab > Import 3D, or bulk import), each as a Model named like its file
-- (p_acunit, arch_penthouse, ...), and put them in ServerStorage > JankfireMeshes. Then this runs when the server starts
-- (Main.server.luau), or in edit mode from the command bar:
--   require(game.ServerScriptService.Jankfire.MeshSwap).run()
-- Each ModelMarkers part is where one copy goes: its CFrame + Size are the model's box in the world, K is how many
-- studs one file metre becomes along each of the file's axes (props are fitted per axis onto their boxes, like the web
-- game), FileCenter / FileSize the model's box in the file. Like the web game, the boxes it stands for stay the
-- collision (just hidden); look-only boxes go.
local ServerStorage = game:GetService("ServerStorage")

local MeshSwap = {}

local function absV(v: Vector3): Vector3 return Vector3.new(math.abs(v.X), math.abs(v.Y), math.abs(v.Z)) end

export type Fit = { K: Vector3, FileSize: Vector3, Variant: string?, Hide: string?, TintColor: Color3? }

-- the maths: the parts of a copy of a template (tcf / tsize = the template's bounding box as it sits in storage),
-- moved and sized onto `place` (the marker's CFrame: the model's box centre in the world)
function MeshSwap.fitParts(copy: Instance, tcf: CFrame, tsize: Vector3, a: Fit, place: CFrame)
	local K, fsz = a.K, a.FileSize
	-- the importer's own scale (studs per file metre), per axis: so it doesn't matter what units it was imported in
	local function u(x: number, y: number): number return if y > 1e-4 and x > 1e-4 then x / y else 1 end
	local U = Vector3.new(u(tsize.X, fsz.X), u(tsize.Y, fsz.Y), u(tsize.Z, fsz.Z))
	local hide = {}
	if a.Hide then for n in string.gmatch(a.Hide, "[^,]+") do hide[n] = true end end
	for _, d in copy:GetDescendants() do
		if d:IsA("BasePart") then
			local tag = string.match(d.Name, "^(%w+)_") -- the part tag from export_models.py (v0, fence, door...)
			if (tag and string.match(tag, "^v%d$") and tag ~= a.Variant) or (tag and hide[tag]) then
				d:Destroy()
				continue
			end
			local rel = tcf:ToObjectSpace(d.CFrame) -- in the template's frame, from its box centre (= the file's)
			local q = rel.Position / U
			local kLocal = absV(rel.Rotation:VectorToObjectSpace(K)) -- K along this part's own axes
			local uLocal = absV(rel.Rotation:VectorToObjectSpace(U))
			d.Size = d.Size / uLocal * kLocal
			d.CFrame = place * CFrame.new(q * K) * rel.Rotation
			d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
			if a.TintColor and (d.Name == "tint" or d.Name == "car_paint" or string.match(d.Name, "_tint$")) then d.Color = a.TintColor end
		end
	end
end

-- one copy of a template, fitted onto a marker
function MeshSwap.fit(template: Model, marker: BasePart): Model?
	local K, fsz = marker:GetAttribute("K"), marker:GetAttribute("FileSize")
	if typeof(K) ~= "Vector3" or typeof(fsz) ~= "Vector3" then return nil end
	local v, h, t = marker:GetAttribute("Variant"), marker:GetAttribute("Hide"), marker:GetAttribute("TintColor")
	local tcf, tsize = template:GetBoundingBox()
	local copy = template:Clone()
	MeshSwap.fitParts(copy, tcf, tsize, {
		K = K, FileSize = fsz,
		Variant = if typeof(v) == "string" then v else nil,
		Hide = if typeof(h) == "string" then h else nil,
		TintColor = if typeof(t) == "Color3" then t else nil,
	}, marker.CFrame)
	copy.Name = marker.Name
	return copy
end

-- every marker whose model is in ServerStorage.JankfireMeshes gets its model; the boxes it stood for go invisible
function MeshSwap.run(map: Instance?): number
	local lib = ServerStorage:FindFirstChild("JankfireMeshes")
	map = map or workspace:FindFirstChild("Map")
	if not lib or not map then return 0 end
	-- every map's markers (step 3: Rooftop and the Range are both in the place)
	local folders = {}
	for _, d in map:GetDescendants() do if d.Name == "ModelMarkers" and d:IsA("Folder") then table.insert(folders, d) end end
	if #folders == 0 then return 0 end
	local out = map:FindFirstChild("Models") or Instance.new("Folder")
	out.Name = "Models"; out.Parent = map
	local done: { [string]: boolean } = {}
	local n = 0
	local all = {}
	for _, fo in folders do for _, m in fo:GetChildren() do table.insert(all, m) end end
	for _, m in all do
		if not m:IsA("BasePart") or m:GetAttribute("Swapped") then continue end
		local file = m:GetAttribute("Model")
		local t = typeof(file) == "string" and lib:FindFirstChild(file :: string)
		if not t or not t:IsA("Model") then continue end
		local copy = MeshSwap.fit(t, m)
		if copy then
			copy.Parent = out; m:SetAttribute("Swapped", true); n += 1
			local kind, id = string.match(m.Name, "^(%a+):(.+)$")
			if kind and id then done[kind .. ":" .. id] = true end
		end
	end
	for _, p in map:GetDescendants() do
		if not p:IsA("BasePart") then continue end
		local prop, arch = p:GetAttribute("PropId"), p:GetAttribute("ArchId")
		local key = if typeof(prop) == "string" then "prop:" .. prop elseif typeof(arch) == "string" then "arch:" .. arch else nil
		if key and done[key] then
			if p.CanCollide then p.Transparency = 1 else p:Destroy() end -- the collision stays, like the web game
		end
	end
	return n
end

return MeshSwap
