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
-- codes: p plastic · n neon · m dark metal · s shiny metal (Metal + a little Reflectance) · g glass (+ 2 hex digits of
-- alpha), then rrggbb.
-- usage (Edit, execute_luau):
--   local W = require(game.ServerStorage.PolishBackup.WeaponImport:Clone())
--   return W.run({ smg = { id = 123456, lo = Vector3.new(-0.0387, -0.222, -0.3705), hi = Vector3.new(0.0293, 0.068, 0.3219) } })
-- options (second argument): into = a folder to put the templates in instead of JankfireWeapons (to compare before
-- replacing), flat = true to drop the pictures and keep only flat colours.
local W = {}

local function paint(d, kind, hex, aa)
	local c = Color3.fromHex(hex)
	d.Color = c
	d.Reflectance = 0
	d.Transparency = 0
	if kind == "n" then d.Material = Enum.Material.Neon
	elseif kind == "m" then d.Material = Enum.Material.Metal
	elseif kind == "s" then d.Material = Enum.Material.Metal; d.Reflectance = 0.1 -- (SmoothPlastic + more shine washed big silver pieces out to white under the hall's lamps)
	elseif kind == "g" then
		d.Material = Enum.Material.Glass
		local a = if aa ~= "" then tonumber(aa, 16) / 255 else 0.4
		d.Transparency = math.clamp(1 - a, 0.2, 0.75)
	else d.Material = Enum.Material.SmoothPlastic end
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
			local base, kind, hex, aa = d.Name:match("^(.+)__(%a)(%x%x%x%x%x%x)(%x?%x?)$")
			if base then paint(d, kind, hex, aa); d.Name = base else bad += 1 end
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
