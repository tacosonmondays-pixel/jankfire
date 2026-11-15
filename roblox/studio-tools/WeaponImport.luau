--!nocheck
-- edit-time tool: brings uploaded weapon models (Open Cloud Model assets made by tools/roblox/export_weapons.py) into
-- ReplicatedStorage.JankfireWeapons as w_<id> templates, with nothing done by hand. the exporter already turned the
-- model so the upload lands in the file's own frame (metres, -Z forward: tools/roblox/rbxglb.py holds what was
-- measured) and wrote each piece's look into its name, "<node>__<material>__<code>". this module
--   1. paints every piece from its code and takes the code off the name again (the game finds pieces by
--      "<node>__<material>": needle, vents, kat_blade, _wzA / _wzB / _wzN wrap zones),
--   2. keeps a piece's picture if its material had one (the part's Color is the picture's average: a fallback if the
--      picture doesn't load; a wrap takes the picture off and puts it back),
--   3. CHECKS the facing: the template's box must equal the bounds the exporter printed (lo / hi, file metres). a
--      model that arrived turned has its long end on the wrong side and is refused.
-- a PAINT CODE is "<kind><rrggbb>[aa][+]": p plastic · n neon · m dark metal · s shiny metal (Metal + a little
-- Reflectance) · g glass (+ 2 hex digits of alpha) · w wood · r rubber / grip; "+" keeps the piece's picture.
-- THE PAINT IS A SWITCH (tools/roblox/weapon_paint.py: "calm", the Roblox game's quiet finish, or "web", the web
-- game's): the name of a piece always carries its WEB look; spec.paint = { ["<node>__<material>"] = code } paints
-- over it. the picture a piece arrived with is remembered in its WebTex attribute, so either paint can be put back
-- on a template without loading the asset again:
--   W.paint({ smg = { ["mag_wzA__smg_teal"] = "p2fc8b8", ... } }, { name = "calm" })
-- (node tools/roblox/weapon_import_call.mjs prints both calls from export_report.json.)
-- usage (Edit, execute_luau):
--   local W = require(game.ServerStorage.PolishBackup.WeaponImport:Clone())
--   return W.run({ smg = { id = 123456, lo = Vector3.new(-0.0387, -0.222, -0.3705), hi = Vector3.new(0.0293, 0.068, 0.3219), paint = { ... } } })
-- options (second argument): into = a folder to put the templates in instead of JankfireWeapons (to compare before
-- replacing), flat = true to drop the pictures and keep only flat colours, name = the paint's name (kept on the
-- template as its Paint attribute).
local W = {}

local function paint(d, code)
	local kind, hex, aa, keep = string.match(code, "^(%a)(%x%x%x%x%x%x)(%x?%x?)(%+?)$")
	if not kind then return false end
	d.Color = Color3.fromHex(hex)
	d.Reflectance = 0
	d.Transparency = 0
	if kind == "n" then d.Material = Enum.Material.Neon
	elseif kind == "m" then d.Material = Enum.Material.Metal
	elseif kind == "s" then d.Material = Enum.Material.Metal; d.Reflectance = 0.1 -- (SmoothPlastic + more shine washed big silver pieces out to white under the hall's lamps)
	elseif kind == "g" then
		d.Material = Enum.Material.Glass
		local a = if aa ~= "" then tonumber(aa, 16) / 255 else 0.4
		d.Transparency = math.clamp(1 - a, 0.2, 0.75)
	elseif kind == "w" then d.Material = Enum.Material.Wood
	elseif kind == "r" then d.Material = Enum.Material.Plastic
	else d.Material = Enum.Material.SmoothPlastic end
	if d:IsA("MeshPart") then
		local web = d:GetAttribute("WebTex")
		if web == nil then web = d.TextureID; d:SetAttribute("WebTex", web) end
		d.TextureID = if keep == "+" then web else ""
	end
	return true
end
W.paintPiece = paint

-- repaint templates that are already in the place: list = { <weapon id> = { ["<piece name>"] = code } }
function W.paint(list, opts)
	opts = opts or {}
	local lib = opts.into or game.ReplicatedStorage.JankfireWeapons
	local out = {}
	for wid, codes in list do
		local m = lib:FindFirstChild("w_" .. wid)
		if not m then table.insert(out, "w_" .. wid .. ": NOT IN THE PLACE"); continue end
		local done, miss, bad, pics = 0, {}, {}, 0
		local seen = {}
		for _, d in m:GetDescendants() do
			if not d:IsA("MeshPart") then continue end
			local code = codes[d.Name]
			seen[d.Name] = true
			if not code then table.insert(miss, d.Name)
			elseif paint(d, code) then done += 1 else table.insert(bad, d.Name .. "=" .. code) end
			if d.TextureID ~= "" then pics += 1 end
		end
		local extra = {}
		for name in codes do if not seen[name] then table.insert(extra, name) end end
		if opts.name then m:SetAttribute("Paint", opts.name) end
		table.insert(out, ("w_%s: %d pieces painted (%d keep a picture)%s%s%s"):format(wid, done, pics,
			if #miss > 0 then ", NOT IN THE TABLE: " .. table.concat(miss, " ") else "",
			if #bad > 0 then ", BAD CODES: " .. table.concat(bad, " ") else "",
			if #extra > 0 then ", in the table but not in the model: " .. table.concat(extra, " ") else ""))
	end
	table.sort(out)
	return table.concat(out, "\n")
end

-- the axis-aligned box of a set of parts (each part's own box, turned by its CFrame)
local function box(parts)
	local lo, hi = Vector3.one * math.huge, -Vector3.one * math.huge
	for _, p in parts do
		local cf, h = p.CFrame, p.Size / 2
		for sx = -1, 1, 2 do for sy = -1, 1, 2 do for sz = -1, 1, 2 do
			local q = cf:PointToWorldSpace(Vector3.new(h.X * sx, h.Y * sy, h.Z * sz))
			lo = lo:Min(q); hi = hi:Max(q)
		end end end
	end
	return lo, hi
end
W.box = box

function W.run(list, opts)
	opts = opts or {}
	local IS = game:GetService("InsertService")
	local lib = opts.into or game.ReplicatedStorage.JankfireWeapons
	local out = {}
	for wid, spec in list do
		local name = "w_" .. wid
		local ok, container = pcall(function() return IS:LoadAsset(spec.id) end)
		if not ok or not container then table.insert(out, name .. ": LOAD FAILED " .. tostring(container)); continue end
		local m = Instance.new("Model")
		m.Name = name
		local parts, bad, pics = {}, 0, 0
		for _, d in container:GetDescendants() do
			if not d:IsA("MeshPart") then continue end
			local base, web = d.Name:match("^(.+)__(%a%x%x%x%x%x%x%x?%x?)$")
			if base then
				d.Name = base
				local code = spec.paint and spec.paint[base]
				if not (code and paint(d, code)) then paint(d, web .. (if d.TextureID ~= "" then "+" else "")) end
			else bad += 1 end
			if opts.flat then d.TextureID = "" end
			if d.TextureID ~= "" then pics += 1 end
			d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.Massless = true
			d.CastShadow = false
			table.insert(parts, d)
		end
		for _, d in parts do d.Parent = m end
		container:Destroy()
		if #parts == 0 then table.insert(out, name .. ": HAD NO MESHES"); m:Destroy(); continue end
		local lo, hi = box(parts)
		local note = ""
		if spec.lo and spec.hi then
			local tol = 0.004 + (spec.hi - spec.lo).Magnitude * 0.01
			local off = math.max((lo - spec.lo).Magnitude, (hi - spec.hi).Magnitude)
			if off > tol then
				table.insert(out, ("%s: REFUSED, it did not land in the file's frame (box %s .. %s, the exporter said %s .. %s, off by %.4f). was it exported with the current export_weapons.py?"):format(name, tostring(lo), tostring(hi), tostring(spec.lo), tostring(spec.hi), off))
				m:Destroy()
				continue
			end
			note = (" facing ok (off %.4f)"):format(off)
		else
			note = " FACING NOT CHECKED (no lo / hi given)"
		end
		m.WorldPivot = CFrame.new((lo + hi) / 2)
		m:SetAttribute("AssetId", spec.id)
		m:SetAttribute("FileFrame", true) -- (its pieces sit where the file has them: nothing was turned in Studio)
		if opts.name then m:SetAttribute("Paint", opts.name) end
		local old = lib:FindFirstChild(name)
		if old then old:Destroy() end
		m.Parent = lib
		table.insert(out, ("%s: %d pieces (%d with a picture, %d with no look code)%s, box %.4f %.4f %.4f .. %.4f %.4f %.4f"):format(name, #parts, pics, bad, note, lo.X, lo.Y, lo.Z, hi.X, hi.Y, hi.Z))
		task.wait()
	end
	table.sort(out)
	return table.concat(out, "\n")
end

return W
