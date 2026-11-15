-- SERIOUS PASS (15 Nov 2026): the repaint that takes the Rooftop, the training hall and the playground from the web
-- game's loud comic paint to a calm one: neutral structure, warm white light, one amber accent, red only for danger.
-- paint, materials, sign type and the Rooftop's saved light only: nothing moves, no part is added or removed (a
-- sign's text outline is the one thing deleted). run in Edit, from a clone (a require of the original is cached):
--   local S = require(game.ServerStorage.PolishBackup.SeriousPass:Clone()); print(S.all())
--   S.training()   the training hall and the playground        S.rooftop()   the Rooftop, its mesh templates, its ads
--   S.light()      the Rooftop's saved Lighting                 S.restore()   the paint as it was before the pass
-- every one is safe to run again: rules go by name where they can, and a colour that is already calm is left alone.
-- the paint from before is kept in PolishBackup.PreSeriousPass (S.restore reads it; S.backup makes it, once)
local ServerStorage = game:GetService("ServerStorage")
local Lighting = game:GetService("Lighting")

local S = {}
local hex = Color3.fromHex
local SP, CONC, NEON, PAVE = Enum.Material.SmoothPlastic, Enum.Material.Concrete, Enum.Material.Neon, Enum.Material.Pavement
-- the three lights: warm white, cool white, amber. none is pure white: a Neon part at 255 reads as an unlit white bar
local WARM, COOL, AMBERGLOW = hex("f2dcc0"), hex("dfe8ee"), hex("f0c468")
local AMBER, OFFWHITE, STEEL, DARK, BOARD = hex("d6a738"), hex("e6e3dc"), hex("4a5a70"), hex("3b3f49"), hex("16181d")
local TITLE = Font.new("rbxasset://fonts/families/BuilderExtended.json", Enum.FontWeight.Bold)
local BODY = Font.new("rbxasset://fonts/families/BuilderSans.json", Enum.FontWeight.Medium)
local HEAVY = Font.new("rbxasset://fonts/families/BuilderSans.json", Enum.FontWeight.ExtraBold)
local TEMPLATE_NAMES = { "p_acunit", "p_billboard", "p_billboard_post", "p_car_hatch", "p_car_sedan", "p_car_taxi", "p_crate", "p_lollipop", "p_palm", "p_streetlight", "p_watertower", "arch_liftroom", "arch_penthouse", "arch_pooldeck", "arch_rt_mast", "arch_rt_signs" }

local function hub(): Instance return workspace:WaitForChild("Map"):WaitForChild("Hub") end
local function roof(): Instance return workspace:WaitForChild("Map"):WaitForChild("Rooftop") end
local function report(n: number, log: { [string]: number }, what: string): string
	local out = {}
	for k, v in log do table.insert(out, k .. "=" .. v) end
	table.sort(out)
	return what .. ": " .. n .. " changes (" .. table.concat(out, ", ") .. ")"
end

-- ---------------------------------------------------------------- the training hall and the playground
-- kit pieces by the start of their name (wh_rack0__plastic_2b7fa8 > wh_rack0)
local HALL: { [string]: Color3 } = {
	wh_rack0 = STEEL, wh_rack1 = hex("a8814a"), wh_rack6 = OFFWHITE, wh_van0 = OFFWHITE, wh_van1 = AMBER, wh_crate2 = OFFWHITE,
	wh_rollup1 = hex("4b505b"), wh_rollup6 = OFFWHITE, floorgrate1 = DARK,
	-- the crates and boxes: under the hall's lamps a mid wood renders toy orange and an olive renders lime, so both go down
	wh_crate0 = hex("8a6a48"), wh_crate1 = hex("75583a"), wh_rack2 = hex("75583a"), wh_rack5 = hex("8a6a48"), wh_forklift5 = hex("75583a"),
	ammocrate0 = hex("46512f"),
}
function S.training(): string
	local n, log = 0, {} :: { [string]: number }
	local function set(d: BasePart, c: Color3?, m: Enum.Material?, why: string)
		if c then d.Color = c end
		if m then d.Material = m end
		n += 1; log[why] = (log[why] or 0) + 1
	end
	for _, root in { hub():WaitForChild("TrainingGround"), hub():WaitForChild("Playground") } do
		for _, d in root:GetDescendants() do
			if not d:IsA("BasePart") then continue end
			if string.find(d.Name, "_wz%a__") then continue end -- a weapon on display: its colours are the weapon's
			if d:FindFirstAncestor("ToHubDoor") or d:FindFirstAncestor("ReturnDoor") then continue end -- the door kit, shared with the hub
			if d:FindFirstAncestor("Pads") or string.sub(d.Name, 1, 7) == "jumppad" then continue end -- a jump pad keeps its cyan: it says jump
			-- the playground's blocks: white, then pale grey, both read as a test level on a bright sky (judged twice). a
			-- dark slate makes the grid a pattern and leaves the jump pads as the only colour
			if d.MaterialVariant == "JankGrid" then
				if d.Color ~= hex("5a6170") then set(d, hex("5a6170"), nil, "playground block") end
				continue
			end
			local key = string.match(d.Name, "^([%a_]+%d*)__")
			local rule = key and HALL[key]
			local h, s, v = d.Color:ToHSV()
			local hue = h * 360
			if rule then set(d, rule, nil, "kit piece")
			elseif d.Name == "lanemat8" then
				-- the firing range's booth panels: their pink is a baked picture, so the picture goes and they are off-white
				if d:IsA("MeshPart") and d.TextureID ~= "" then d.TextureID = ""; set(d, OFFWHITE, nil, "flattened") end
			elseif d.Name == "lanemat4" or d.Name == "lanemat15" then
				-- the range's foam walls: a noisy speckled picture > one flat dark slate
				if d:IsA("MeshPart") and d.TextureID ~= "" then d.TextureID = ""; set(d, hex("3a3d47"), SP, "flattened") end
			elseif string.sub(d.Name, 1, 4) == "skid" and d.Material == Enum.Material.Fabric then
				-- the bales on the pallets: the knitted Fabric material > flat
				if d:IsA("MeshPart") then d.TextureID = "" end
				set(d, hex("a8956e"), SP, "flattened")
			elseif d.Name == "skid2" then
				-- the sacks on the pallets: a woven picture > flat
				if d:IsA("MeshPart") and d.TextureID ~= "" then d.TextureID = ""; set(d, hex("9a8660"), SP, "flattened") end
			elseif d.Name == "Floor" and d.Parent ~= nil and d.Parent.Name == "Shell" then
				-- the hall's floor: the lamps light it to about twice its paint, so the paint is dark
				if d.Color ~= hex("3c3e44") then set(d, hex("3c3e44"), nil, "floor") end
			elseif d.Name == "Accent" then
				-- the thin strips: the lines on the floor become a muted painted amber (no glow), the coloured strips on
				-- the walls become warm white light
				-- (8f7b40 looks dull here and right in the hall: the lamps overhead light the floor to about 1.6x)
				if d.Size.Y < 0.1 then if d.Color ~= hex("8f7b40") then set(d, hex("8f7b40"), SP, "floor line") end
				elseif d.Material ~= NEON then continue
				elseif hue > 35 and hue < 70 then set(d, hex("cdb45c"), SP, "wall line") elseif s > 0.3 then set(d, WARM, nil, "wall strip") end
			elseif d.Name == "Hazard" then set(d, AMBER, nil, "hazard")
			elseif d.Name == "Easy" then set(d, hex("6fd08a"), nil, "plate")
			elseif d.Name == "Medium" then set(d, hex("ffc43d"), nil, "plate")
			elseif d.Name == "Hard" then set(d, hex("eb4d4b"), nil, "plate")
			elseif d.Name == "PlinkerGlow" or d.Name == "band0" or d.Name == "beacon" then continue -- danger and targets stay red
			elseif d.Material == NEON then
				if s > 0.35 and hue >= 70 and hue <= 340 then set(d, WARM, nil, "coloured glow > warm white") end
			elseif s > 0.45 and v > 0.35 then
				local wood = d.Material == Enum.Material.Wood or d.Material == Enum.Material.WoodPlanks
				if hue >= 255 and hue <= 345 then set(d, if v > 0.6 then OFFWHITE else DARK, nil, "pink or purple")
				elseif hue >= 165 and hue < 200 then set(d, OFFWHITE, nil, "cyan")
				elseif hue >= 200 and hue < 255 then set(d, STEEL, nil, "blue")
				elseif hue >= 40 and hue < 65 and not wood and d.Color ~= AMBER then set(d, AMBER, nil, "yellow > amber")
				elseif hue >= 15 and hue < 40 and s > 0.8 and not wood then set(d, hex("b8742f"), nil, "orange")
				elseif (hue < 15 or hue > 345) and s > 0.6 and v > 0.6 then set(d, hex("9a4640"), nil, "red")
				end
			end
		end
		-- the signs: one type family, white titles, grey second lines, a hairline frame, a neutral dark board
		for _, g in root:GetDescendants() do
			if not g:IsA("SurfaceGui") then continue end
			local part = g.Adornee or g.Parent
			local plate = part ~= nil and (part.Name == "Easy" or part.Name == "Medium" or part.Name == "Hard")
			if part and part:IsA("BasePart") and not plate then part.Color = BOARD end
			for _, o in g:GetDescendants() do
				if o:IsA("UIStroke") then
					if o.Parent and o.Parent:IsA("TextLabel") then o:Destroy() else o.Color = Color3.new(1, 1, 1); o.Transparency = 0.8; o.Thickness = 3 end
				elseif o:IsA("Frame") then o.BackgroundColor3 = BOARD
				elseif o:IsA("TextLabel") then
					local second = string.find(o.FontFace.Family, "Fredoka") ~= nil or o.Name == "Sub" or o.Name == "Line" or o.FontFace == BODY
					if plate then o.FontFace = HEAVY; o.TextColor3 = hex("0e0f12")
					elseif o.Name == "Score" or o.Name == "Left" then o.FontFace = HEAVY; o.TextColor3 = hex("f0f2f5")
					elseif o.Name == "ScoreT" or o.Name == "LeftT" then o.FontFace = HEAVY; o.TextColor3 = hex("9ca2ac")
					elseif second then o.FontFace = BODY; o.TextColor3 = hex("c8ccd3"); o.TextWrapped = true
					else o.FontFace = TITLE; o.TextColor3 = hex("f0f2f5") end
				end
			end
			-- a zone sign (a title over one small line): the small line gets room for two rows, and a short amber bar
			-- sits between the two
			local frame = g:FindFirstChildOfClass("Frame")
			local title: TextLabel?, small: TextLabel? = nil, nil
			for _, o in g:GetDescendants() do
				if o:IsA("TextLabel") then if o.FontFace == BODY then small = o elseif o.FontFace == TITLE then title = o end end
			end
			if frame and title and small and small.Name ~= "Sub" and small.Name ~= "Line" then
				small.Position = UDim2.fromScale(0.04, 0.7); small.Size = UDim2.fromScale(0.92, 0.26)
				local bar = frame:FindFirstChild("Bar") or Instance.new("Frame")
				bar.Name = "Bar"; bar.BorderSizePixel = 0; bar.BackgroundColor3 = hex("ffc43d"); bar.AnchorPoint = Vector2.new(0.5, 0)
				bar.Position = UDim2.fromScale(0.5, 0.655); bar.Size = UDim2.fromScale(0.07, 0.022); bar.Parent = frame
			end
			n += 1; log.sign = (log.sign or 0) + 1
		end
	end
	return report(n, log, "training hall + playground")
end

-- ---------------------------------------------------------------- the Rooftop
-- the map's own boxes are named after the web game's materials: name > { colour (hex, or nil to keep), material }.
-- a neon name is two things: the glowing strip (Neon) and, for the three street signs, a dark board (not Neon)
local ROOF: { [string]: { any } } = {
	asphaltn = { "2f3138" }, pavecity = { "3b3d45" }, wetroad = { "34363d" }, wetroadz = { "37393f" },
	-- the two side roofs' floor: mid-grey pavers. the paver pattern gives the bare deck a scale and a surface. tried and
	-- dropped: pale concrete 8b8d93 (floor, parapet, hut and towers became one grey: a baseplate), dark asphalt 4d5058
	-- (black in the evening shadow, which covers half of each roof), mid asphalt 7c7f88 (a featureless slab)
	asphalt = { "868990", PAVE },
	office = { "70747c" }, -- the concrete towers round the arena: darker and cooler than the roofs you play on
	tvstatic = { "1c2028", SP }, -- the penthouse's telly: a white Neon slab blew out; a dark screen
	brick = { "8a6c5e" }, tenement = { "715a50" }, stone = { nil, CONC }, grid = { "70737a", SP }, chrome = { nil, SP },
	sidemint = { "8a979c" }, sideorange = { "a38c78" }, sidepink = { "9c9498" }, sidelemon = { "b0a98c" },
	toypink = { "9c9196" }, toypurple = { "7e7c8c" }, toyteal = { "82959a" }, toyyellow = { "b5a36c" }, toyorange = { "a98a6c" },
	pink = { "a79aa0" }, roofpink = { "8a7f86" },
	adcity1 = { "2f3642" }, adcity2 = { "5b4541" }, adcity3 = { "3f4a44" }, adcity4 = { "85765f" }, adcity5 = { "403c4c" }, adcity6 = { "37505a" },
	lawn = { "5f7a4c" }, leaves = { "4f7044" }, leaves2 = { "7d9a52" }, blossom = { "c4b6ba" },
	glassblock = { "4c5b6e" }, cloth = { "a89b8e", SP }, wood = { "7b6a58" }, poolfloor = { "4696a5" }, poolwall = { "4696a5" },
	adparty = { "16181d" }, adjankbank = { "1a2230" }, addj = { "16181d" },
}
local GLOW: { [string]: Color3 } = { -- the neon strips: the west roof and far towers cool, the east warm, the middle amber
	neoncyan = COOL, neongreen = COOL, neonbar = COOL, neonpink = WARM, neonnoodle = WARM, neonwork = WARM,
	neonyellow = AMBERGLOW, neonhotel = AMBERGLOW, lamp = WARM,
}
-- the Blender models (ServerStorage.JankfireMeshes, fitted over the boxes when the server starts): a piece is found by
-- its name. name > { new hex or nil, material }
local TEMPLATES: { [string]: { [string]: { any } } } = {
	arch_penthouse = {
		-- (ph_white is the frame AND the ceiling: white Plaster read as unlit outside and noisy inside, so graphite)
		ph_white = { "3a3c43", SP }, ph_pink = { "c9c7c2", SP }, ph_chrome = { "4d515a", SP }, ph_granite = { "3a3d45", SP },
		ph_floor = { "4a4b50", SP }, ph_carpet = { "4b4e57" }, ph_deck = { "8d8a86" }, ph_frost = { "5a606a" }, ph_pad = { nil, CONC },
		ph_glass = { "465a69" }, ph_glassin = { "4c5560" }, ph_padline = { "e3b54a" },
		ph_padlamp = { "f2dcc0" }, ph_neon = { "f2dcc0" }, ph_lamp = { "f2dcc0" },
	},
	arch_pooldeck = {
		pd_case = { "2b2e35", SP }, pd_deck = { "2f3138" }, pd_stripe = { "7d828c", SP }, pd_ring = { "c9a646", SP }, pd_alu = { nil, SP },
		pd_flamingo = { "c8a45c" }, pd_canvas = { "b9b5ab", Enum.Material.Fabric }, pd_c_toyteal = { "bdbab2" },
		pd_neonyellow = { "f0e2c0" }, pd_neongreen = { "f0e2c0" }, pd_neoncyan = { "f0e2c0" }, pd_lamp = { "f0e2c0" }, pd_neonpink = { "f2dcc0" },
	},
	arch_liftroom = {
		lr_wall = { "a3a19c" }, lr_coping = { "8b8984" }, lr_gravel = { nil, CONC }, lr_neon = { "f2dcc0" }, door_lr_sign = { "f2dcc0" },
		["lr_band@trim"] = { "c9c7c1", SP }, ["v0_lr_band@trim"] = { "c9c7c1", SP }, ["v1_lr_band@trim"] = { "c9c7c1", SP },
		["v2_lr_band@trim"] = { "c9c7c1", SP }, ["door_lr_door@trim"] = { "a9abb0", SP },
	},
	arch_rt_signs = { sg_steel = { "50545d", SP }, sg_chrome = { "8f939b", SP }, sg_grate = { nil, SP }, sg_neonpink = { "f2dcc0" } },
	p_acunit = { ac_metal = { nil, SP }, ac_paint = { "9a9da3", SP } }, -- (Metal on a box that size mirrors the sky like chrome)
}
-- the furniture on the roofs you play on (the same names are plain blocks out in the city): charcoal, one amber
local FURNITURE: { [string]: { any } } = {
	toypink = { "34363d", SP }, toyteal = { "4a4e57", SP }, toypurple = { "3e4048", SP }, toyyellow = { "c9a646", SP }, toyorange = { "8a6a48", SP },
}
-- the cars and trees take a tint from their marker: old hex > new
local TINTS: { [string]: string } = {
	c8202c = "8a3c3a", ["2050b0"] = "3e5078", e8c020 = "b89c46", ["2a8a4a"] = "4c6e58",
	["3b8b31"] = "4f7044", ["94ec1c"] = "7d9a52", f95cca = "c4b0b8",
}
function S.rooftop(): string
	local n, log = 0, {} :: { [string]: number }
	local function count(why: string) n += 1; log[why] = (log[why] or 0) + 1 end
	local r = roof()
	for i, d in r:GetDescendants() do
		if i % 1500 == 0 then task.wait() end
		if not d:IsA("BasePart") then continue end
		local glow = GLOW[d.Name]
		local rule = ROOF[d.Name]
		local arena = d.Parent ~= nil and d.Parent.Name ~= "City" -- (the roofs you play on, not the city round them)
		if arena and FURNITURE[d.Name] then rule = FURNITURE[d.Name] end
		if glow then
			-- (out in the city the strips are a third dimmer: lit windows in the distance, not white lines on every tower)
			if d.Material == NEON then d.Color = if arena then glow else glow:Lerp(Color3.new(0, 0, 0), 0.32); count("glow")
			else d.Color = hex("101216"); count("sign board") end
		elseif rule then
			if rule[1] then d.Color = hex(rule[1]) end
			if rule[2] then d.Material = rule[2] end
			count("box")
		elseif string.sub(d.Name, 1, 10) == "jumppad5__" then d.Color = hex("f4f8ff"); count("jump pad") -- (the pad's pink ring; its cyan stays: it says jump)
		end
		local t = d:GetAttribute("TintColor")
		if typeof(t) == "Color3" and TINTS[t:ToHex()] then d:SetAttribute("TintColor", hex(TINTS[t:ToHex()])); count("tint") end
	end
	local lib = ServerStorage:FindFirstChild("JankfireMeshes")
	for name, rules in TEMPLATES do
		local m = lib and lib:FindFirstChild(name)
		if not m then continue end
		for _, d in m:GetDescendants() do
			if not d:IsA("BasePart") then continue end
			local rule = rules[d.Name]
			if not rule then continue end
			if rule[1] then d.Color = hex(rule[1]) end
			if rule[2] then d.Material = rule[2] end
			count("model piece")
		end
	end
	-- the billboards and street signs: the same type as every other sign; a street sign's letters glow amber
	for _, g in r:GetDescendants() do
		if not g:IsA("SurfaceGui") then continue end
		local part = g.Adornee or g.Parent
		local street = part ~= nil and GLOW[part.Name] ~= nil
		local board = if part and part.Name == "adjankbank" then hex("1a2230") elseif street then hex("101216") else hex("1c2028")
		for _, o in g:GetDescendants() do
			if o:IsA("UIStroke") then
				if o.Parent and o.Parent:IsA("TextLabel") then o:Destroy()
				elseif street then o.Color = AMBERGLOW; o.Transparency = 0; o.Thickness = 3
				else o.Color = Color3.new(1, 1, 1); o.Transparency = 0.8; o.Thickness = 3 end
			elseif o:IsA("UIGradient") then o:Destroy()
			elseif o:IsA("Frame") then o.BackgroundColor3 = board
			elseif o:IsA("TextLabel") then
				local second = string.find(o.FontFace.Family, "Fredoka") ~= nil or o.FontFace == BODY
				if second then o.FontFace = BODY; o.TextColor3 = hex("aab0ba")
				else o.FontFace = TITLE; o.TextColor3 = if street then hex("ffd98a") elseif o.Text == "JANKFIRE" then hex("ffc43d") else hex("f0f2f5") end
			end
		end
		count("ad")
	end
	return report(n, log, "rooftop")
end

-- ---------------------------------------------------------------- the Rooftop's saved light
-- the same evening, without the pink: a warm low sun and cool shadows (that contrast is what gives grey buildings
-- depth), a haze the colour of the horizon, more light in the shadows, less glare and bloom, less saturation.
-- (the hub and the training hall have their own looks in ReplicatedStorage.Jankfire.HubLook; this is the saved one)
S.LIGHT = {
	Brightness = 3, ExposureCompensation = 0.05, Ambient = hex("69738c"), OutdoorAmbient = hex("8a94ad"),
	ColorShift_Top = Color3.fromRGB(255, 205, 160),
	Atmosphere = { Density = 0.22, Haze = 0.6, Glare = 0.3, Color = hex("c4c2c2"), Decay = hex("8a8890") }, -- (a warmer haze put a pink wall on the horizon)
	Bloom = { Intensity = 0.35, Size = 24, Threshold = 2.2 },
	ColorCorrection = { Saturation = 0.06, Contrast = 0.15 },
}
function S.light(): string
	if Lighting:GetAttribute("Previewing") then return "light: a HubLook preview is on, so the saved light was not touched. turn the preview off and run S.light() again" end
	local n = 0
	for k, v in S.LIGHT :: { [string]: any } do
		if type(v) == "table" then
			local o = Lighting:FindFirstChild(k)
			if o then for p, x in v do (o :: any)[p] = x; n += 1 end end
		else (Lighting :: any)[k] = v; n += 1 end
	end
	return "light: " .. n .. " values set"
end

-- ---------------------------------------------------------------- the backup, and putting it back
function S.backup(): string
	local pb = ServerStorage:WaitForChild("PolishBackup")
	if pb:FindFirstChild("PreSeriousPass") then return "backup: already there (" .. #pb.PreSeriousPass:GetDescendants() .. " things), left as it is" end
	local root = Instance.new("Folder"); root.Name = "PreSeriousPass"
	local r = Instance.new("Folder"); r.Name = "Rooftop"
	for _, c in roof():GetChildren() do c:Clone().Parent = r; task.wait() end
	r.Parent = root
	hub():WaitForChild("TrainingGround"):Clone().Parent = root
	hub():WaitForChild("Playground"):Clone().Parent = root
	local t = Instance.new("Folder"); t.Name = "MeshTemplates"
	for _, name in TEMPLATE_NAMES do
		local m = ServerStorage.JankfireMeshes:FindFirstChild(name)
		if m then m:Clone().Parent = t end
	end
	t.Parent = root
	root.Parent = pb
	return "backup: made (" .. #root:GetDescendants() .. " things)"
end
-- paint only: every part gets its old colour, material and tint back, every sign its old face. it goes part by part in
-- the same order as the backup, so it refuses a place whose parts no longer line up (something was added or removed)
local function repaint(cur: Instance, old: Instance): (number, string?)
	local a, b = {}, {}
	for _, d in cur:GetDescendants() do if d:IsA("BasePart") then table.insert(a, d) end end
	for _, d in old:GetDescendants() do if d:IsA("BasePart") then table.insert(b, d) end end
	if #a ~= #b then return 0, ("%s has %d parts, its backup %d"):format(cur.Name, #a, #b) end
	for i, d in a do
		local o = b[i]
		if d.Name ~= o.Name then return 0, ("%s: part %d is %s, its backup's is %s"):format(cur.Name, i, d.Name, o.Name) end
	end
	for i, d in a do
		local o = b[i]
		d.Color = o.Color; d.Material = o.Material
		if d:IsA("MeshPart") and o:IsA("MeshPart") and d.TextureID ~= o.TextureID then d.TextureID = o.TextureID end
		if o:GetAttribute("TintColor") ~= nil then d:SetAttribute("TintColor", o:GetAttribute("TintColor")) end
		for _, g in d:GetChildren() do if g:IsA("SurfaceGui") then g:Destroy() end end
		for _, g in o:GetChildren() do if g:IsA("SurfaceGui") then g:Clone().Parent = d end end
		if i % 1500 == 0 then task.wait() end
	end
	return #a, nil
end
function S.restore(): string
	local bak = ServerStorage:WaitForChild("PolishBackup"):FindFirstChild("PreSeriousPass")
	if not bak then return "restore: there is no PolishBackup.PreSeriousPass" end
	local out = {}
	local pairs_ = {
		{ roof(), bak:FindFirstChild("Rooftop") }, { hub():FindFirstChild("TrainingGround"), bak:FindFirstChild("TrainingGround") },
		{ hub():FindFirstChild("Playground"), bak:FindFirstChild("Playground") },
	}
	for _, name in TEMPLATE_NAMES do
		table.insert(pairs_, { ServerStorage.JankfireMeshes:FindFirstChild(name), bak.MeshTemplates:FindFirstChild(name) })
	end
	for _, p in pairs_ do
		if p[1] and p[2] then
			local n, why = repaint(p[1], p[2])
			table.insert(out, if why then "SKIPPED " .. why else p[1].Name .. " " .. n)
		end
	end
	local light = bak:GetAttribute("Light")
	return "restore: " .. table.concat(out, "; ") .. ". the old light is not set by this: its numbers are " .. tostring(light)
end

function S.all(): string
	return table.concat({ S.backup(), S.training(), S.rooftop(), S.light() }, "\n")
end

return S
