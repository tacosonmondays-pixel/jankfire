--!strict
-- the player card's looks: borders, backgrounds ("banner") and titles. what exists, how rare it is, and how to draw
-- it. everything is drawn from frames and gradients in the GUI, never an uploaded picture (nothing for moderation to
-- read, no text in an image). backgrounds start from the web game's name-card backgrounds (public/js/cards.js:
-- stripes, grid, sunset, stars, camo, flames, static), quieter; titles are the web game's end-of-match medals
-- (shared/medals.js). free ones everybody owns; the rest come from Duffel Bags and the shop and are kept by the loot
-- save (Loot.owns(p, "border", id): gun-less types, key = the id, like a weapon skin).
-- the card wears { border, banner, title } (Stats.luau keeps the pick); drawing is for clients only.
local RunService = game:GetService("RunService")

local C = {}

C.TYPES = { "border", "banner", "title" }
C.TYPE_NAMES = { border = "Border", banner = "Background", title = "Title" }
C.DEFAULT = { border = "hairline", banner = "slate", title = "none" }
-- the container the non-free ones roll from (LootTable's card hook reads it: the Duffel Bag, as one more "gun")
C.CONTAINER = "bag"

export type Item = { type: string, id: string, name: string, rarity: string, text: string? }

-- rarity tints (the same as LootTable.RARITY; copied so this module needs nothing else)
C.RARITY_COLOR = {
	free = Color3.fromRGB(150, 156, 166), common = Color3.fromRGB(122, 178, 104), rare = Color3.fromRGB(78, 150, 226),
	epic = Color3.fromRGB(162, 108, 226), legendary = Color3.fromRGB(240, 178, 52),
}

-- id = { name, rarity }, in the order the picker shows them
local BORDERS = {
	{ "hairline", "Hairline", "free" }, { "steel", "Steel", "free" },
	{ "brass", "Brass", "common" }, { "twin", "Twin Line", "common" },
	{ "brackets", "Brackets", "rare" }, { "ember", "Ember", "rare" },
	{ "gilded", "Gilded", "epic" }, { "prism", "Prism", "epic" },
	{ "halo", "Halo", "legendary" },
}
local BANNERS = {
	{ "slate", "Slate", "free" }, { "stripes", "Stripes", "free" }, { "grid", "Grid", "free" },
	{ "sunset", "Sunset", "common" }, { "stars", "Night Sky", "common" }, { "camo", "Camo", "common" },
	{ "flames", "Furnace", "rare" }, { "carbon", "Carbon", "rare" }, { "static", "Static", "rare" },
	{ "aurora", "Aurora", "epic" }, { "molten", "Molten", "epic" },
	{ "eclipse", "Eclipse", "legendary" },
}
-- titles: id, the words, rarity (the web medals keep their own words)
local TITLES = {
	{ "none", "", "free" }, { "rookie", "ROOKIE", "free" }, { "new_hire", "NEW HIRE", "free" },
	{ "first", "FIRST BLOOD", "common" }, { "multi2", "TWO FOR ONE", "common" }, { "revenge", "FILED A COMPLAINT", "common" },
	{ "pacifist", "CONSCIENTIOUS OBJECTOR", "common" },
	{ "hs", "HEAD OF HR", "rare" }, { "far", "LONG DISTANCE CALL", "rare" }, { "melee", "HANDS-ON MANAGER", "rare" },
	{ "void", "WASTE DISPOSAL", "rare" },
	{ "multi3", "BULK DISCOUNT", "epic" }, { "streak", "ON A TEAR", "epic" }, { "fast", "OVER THE LIMIT", "epic" },
	{ "untouch", "UNTOUCHABLE", "legendary" }, { "mvp", "EMPLOYEE OF THE MONTH", "legendary" },
}

C.ORDER = { border = {}, banner = {}, title = {} } :: { [string]: { string } }
C.ITEMS = { border = {}, banner = {}, title = {} } :: { [string]: { [string]: Item } }
for _, r in BORDERS do
	C.ITEMS.border[r[1]] = { type = "border", id = r[1], name = r[2], rarity = r[3] }
	table.insert(C.ORDER.border, r[1])
end
for _, r in BANNERS do
	C.ITEMS.banner[r[1]] = { type = "banner", id = r[1], name = r[2], rarity = r[3] }
	table.insert(C.ORDER.banner, r[1])
end
for _, r in TITLES do
	local name = if r[2] == "" then "No Title" else string.upper(string.sub(r[2], 1, 1)) .. string.lower(string.sub(r[2], 2))
	C.ITEMS.title[r[1]] = { type = "title", id = r[1], name = name, rarity = r[3], text = r[2] }
	table.insert(C.ORDER.title, r[1])
end

-- the item's row, or nil (ids come off the network: plain lookups only)
function C.info(t: any, id: any): Item?
	if type(t) ~= "string" or type(id) ~= "string" then return nil end
	local set = C.ITEMS[t]
	return if set then set[id] else nil
end
function C.isFree(t: string, id: string): boolean
	local i = C.info(t, id)
	return i ~= nil and i.rarity == "free"
end
function C.isType(t: any): boolean
	return t == "border" or t == "banner" or t == "title"
end
-- the non-free ones of a type, for a container's pool or the shop
function C.forSale(t: string): { Item }
	local out = {}
	for _, id in C.ORDER[t] or {} do
		local i = C.ITEMS[t][id]
		if i.rarity ~= "free" then table.insert(out, i) end
	end
	return out
end
function C.titleText(id: string?): string
	local i = C.info("title", id)
	return if i then i.text :: string else ""
end
function C.titleColor(id: string?): Color3
	local i = C.info("title", id)
	local c = C.RARITY_COLOR[if i then i.rarity else "free"]
	return c:Lerp(Color3.fromRGB(236, 238, 242), 0.35)
end

-- ------------------------------------------------------------------ drawing (clients)
local function new(class: string, props: { [string]: any }, parent: Instance?): any
	local o = Instance.new(class)
	for k, v in props do (o :: any)[k] = v end
	if parent then o.Parent = parent end
	return o
end
local function rgb(r: number, g: number, b: number): Color3 return Color3.fromRGB(r, g, b) end
local function seq(...: any): ColorSequence
	local args = { ... }
	if #args == 2 then return ColorSequence.new(args[1], args[2]) end
	local keys = {}
	for i, c in args do table.insert(keys, ColorSequenceKeypoint.new((i - 1) / (#args - 1), c)) end
	return ColorSequence.new(keys)
end

-- moving gradients: one loop for every one on screen (they drop out when their GUI is gone)
type Anim = { g: UIGradient, kind: string, speed: number, t0: number }
local anims: { Anim } = {}
local loop: RBXScriptConnection? = nil
local function animate(g: UIGradient, kind: string, speed: number)
	table.insert(anims, { g = g, kind = kind, speed = speed, t0 = os.clock() + math.random() * 10 })
	if loop or not RunService:IsClient() then return end
	loop = RunService.RenderStepped:Connect(function()
		local t = os.clock()
		for i = #anims, 1, -1 do
			local a = anims[i]
			if not a.g.Parent or not a.g:IsDescendantOf(game) then
				table.remove(anims, i)
			elseif a.kind == "spin" then
				a.g.Rotation = ((t - a.t0) * a.speed) % 360
			elseif a.kind == "drift" then
				a.g.Offset = Vector2.new(math.sin((t - a.t0) * a.speed) * 0.35, 0)
			elseif a.kind == "breathe" then
				a.g.Offset = Vector2.new(0, 0.12 + math.sin((t - a.t0) * a.speed) * 0.12)
			end
		end
	end)
end

-- a thin straight line from (x1, y1) to (x2, y2) in pixels inside `parent`
local function line(parent: Instance, x1: number, y1: number, x2: number, y2: number, w: number, color: Color3, alpha: number)
	local dx, dy = x2 - x1, y2 - y1
	local len = math.sqrt(dx * dx + dy * dy)
	new("Frame", { BorderSizePixel = 0, BackgroundColor3 = color, BackgroundTransparency = alpha, AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromOffset((x1 + x2) / 2, (y1 + y2) / 2), Size = UDim2.fromOffset(len, w), Rotation = math.deg(math.atan2(dy, dx)) }, parent)
end
local function blob(parent: Instance, x: number, y: number, w: number, h: number, color: Color3, alpha: number, rot: number?)
	local b = new("Frame", { BorderSizePixel = 0, BackgroundColor3 = color, BackgroundTransparency = alpha, AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromOffset(x, y), Size = UDim2.fromOffset(w, h), Rotation = rot or 0 }, parent)
	new("UICorner", { CornerRadius = UDim.new(1, 0) }, b)
	return b
end

-- the background's pieces for a box W x H (px)
local function drawBanner(g: GuiObject, id: string, W: number, H: number)
	local r = Random.new(#id * 97 + 13)
	if id == "stripes" then
		g.BackgroundColor3 = rgb(22, 24, 29)
		local step = 26
		for x = -H, W + H, step do line(g, x, H + 4, x + H * 0.9, -4, 9, rgb(44, 47, 56), 0) end
		new("UIGradient", { Color = seq(rgb(255, 255, 255), rgb(150, 150, 150)), Rotation = 90 }, g)
	elseif id == "grid" then
		g.BackgroundColor3 = rgb(14, 16, 22)
		local hy = H * 0.34
		local c = rgb(92, 110, 140)
		for i = -10, 10 do line(g, W / 2, hy, W / 2 + i * W * 0.14, H + 4, 1, c, 0.55) end
		for j = 0, 7 do
			local y = hy + math.pow(j / 7, 1.8) * (H - hy)
			line(g, 0, y, W, y, 1, c, 0.45 + (1 - j / 7) * 0.4)
		end
		new("Frame", { BorderSizePixel = 0, BackgroundColor3 = rgb(14, 16, 22), Size = UDim2.new(1, 0, 0, hy) }, g)
	elseif id == "sunset" then
		g.BackgroundColor3 = Color3.new(1, 1, 1)
		new("UIGradient", { Color = seq(rgb(36, 22, 50), rgb(122, 62, 92), rgb(196, 132, 78)), Rotation = 90 }, g)
		blob(g, W * 0.76, H * 0.86, H * 0.62, H * 0.62, rgb(232, 196, 120), 0.05)
		for i = 0, 5 do
			new("Frame", { BorderSizePixel = 0, BackgroundColor3 = rgb(34, 20, 42), Position = UDim2.new(0, 0, 1, -5 - i * 7), Size = UDim2.new(1, 0, 0, 2 + (5 - i) * 0.4) }, g)
		end
	elseif id == "stars" then
		g.BackgroundColor3 = Color3.new(1, 1, 1)
		new("UIGradient", { Color = seq(rgb(6, 7, 14), rgb(20, 22, 38)), Rotation = 90 }, g)
		for _ = 1, math.min(150, math.floor(W * H / 900)) do
			local s = if r:NextNumber() < 0.1 then 3 else (if r:NextNumber() < 0.5 then 2 else 1)
			local c = if r:NextNumber() < 0.15 then rgb(170, 190, 236) else rgb(240, 240, 246)
			new("Frame", { BorderSizePixel = 0, BackgroundColor3 = c, BackgroundTransparency = r:NextNumber() * 0.6,
				Position = UDim2.fromOffset(r:NextNumber() * W, r:NextNumber() * H), Size = UDim2.fromOffset(s, s) }, g)
		end
	elseif id == "camo" then
		g.BackgroundColor3 = rgb(70, 78, 56)
		local cols = { rgb(48, 56, 38), rgb(94, 102, 70), rgb(62, 52, 40) }
		for i = 1, math.min(90, math.floor(W * H / 1400)) do
			blob(g, r:NextNumber() * W, r:NextNumber() * H, 18 + r:NextNumber() * 48, 12 + r:NextNumber() * 22, cols[i % 3 + 1], 0, r:NextNumber() * 180)
		end
	elseif id == "flames" then
		g.BackgroundColor3 = Color3.new(1, 1, 1)
		new("UIGradient", { Color = seq(rgb(40, 12, 10), rgb(170, 70, 34), rgb(226, 166, 76)), Rotation = 90 }, g)
		for x = 0, W, 16 do
			local d = 12 + ((x * 7) % 22)
			new("Frame", { BorderSizePixel = 0, BackgroundColor3 = rgb(26, 8, 6), AnchorPoint = Vector2.new(0.5, 0.5), Rotation = 45,
				Position = UDim2.fromOffset(x, 0), Size = UDim2.fromOffset(d, d) }, g)
		end
	elseif id == "carbon" then
		g.BackgroundColor3 = rgb(20, 21, 24)
		for x = -H, W + H, 8 do line(g, x, H + 2, x + H, -2, 3, rgb(34, 36, 41), 0) end
		for x = -H, W + H, 16 do line(g, x, -2, x + H, H + 2, 2, rgb(12, 13, 15), 0.3) end
		new("UIGradient", { Color = seq(rgb(255, 255, 255), rgb(170, 170, 170)), Rotation = 60 }, g)
	elseif id == "static" then
		g.BackgroundColor3 = rgb(34, 35, 38)
		for _ = 1, math.min(180, math.floor(W * H / 320)) do
			local v = math.floor(30 + r:NextNumber() * 90)
			new("Frame", { BorderSizePixel = 0, BackgroundColor3 = rgb(v, v, v + 4), Position = UDim2.fromOffset(math.floor(r:NextNumber() * W / 3) * 3, math.floor(r:NextNumber() * H / 3) * 3),
				Size = UDim2.fromOffset(3 + math.floor(r:NextNumber() * 3) * 3, 3) }, g)
		end
	elseif id == "aurora" then
		g.BackgroundColor3 = rgb(8, 12, 20)
		for i, c in { { rgb(70, 196, 164), rgb(120, 92, 214) }, { rgb(96, 150, 230), rgb(70, 200, 150) } } do
			local band = new("Frame", { BorderSizePixel = 0, BackgroundColor3 = Color3.new(1, 1, 1), AnchorPoint = Vector2.new(0.5, 0.5),
				Position = UDim2.fromScale(0.5, 0.36 + i * 0.12), Size = UDim2.new(1.6, 0, 0, H * 0.34), Rotation = if i == 1 then -8 else 6 }, g)
			new("UICorner", { CornerRadius = UDim.new(1, 0) }, band)
			local gr = new("UIGradient", { Color = seq(c[1], c[2], c[1]),
				Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.3, 0.55), NumberSequenceKeypoint.new(0.7, 0.6), NumberSequenceKeypoint.new(1, 1) }) }, band)
			animate(gr, "drift", 0.18 + i * 0.07)
		end
	elseif id == "molten" then
		g.BackgroundColor3 = Color3.new(1, 1, 1)
		local gr = new("UIGradient", { Color = seq(rgb(14, 9, 8), rgb(70, 26, 12), rgb(214, 104, 38)), Rotation = 90 }, g)
		animate(gr, "breathe", 0.9)
		-- cooled crust: dark plates with the glow showing in the cracks between them
		for _ = 1, 7 do
			local w = (0.18 + r:NextNumber() * 0.22) * W
			local p = new("Frame", { BorderSizePixel = 0, BackgroundColor3 = rgb(22, 14, 12), AnchorPoint = Vector2.new(0.5, 0.5), Rotation = r:NextNumber() * 24 - 12,
				Position = UDim2.fromOffset(r:NextNumber() * W, H * (0.78 + r:NextNumber() * 0.3)), Size = UDim2.fromOffset(w, H * 0.22) }, g)
			new("UICorner", { CornerRadius = UDim.new(0, 6) }, p)
		end
	elseif id == "eclipse" then
		g.BackgroundColor3 = Color3.new(1, 1, 1)
		new("UIGradient", { Color = seq(rgb(4, 4, 7), rgb(14, 13, 20)), Rotation = 90 }, g)
		local d = H * 0.86
		local glow = blob(g, W * 0.74, H * 0.5, d * 1.5, d * 1.5, rgb(236, 210, 150), 0)
		new("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0.86), NumberSequenceKeypoint.new(1, 1) }), Rotation = 90 }, glow)
		local ring = blob(g, W * 0.74, H * 0.5, d, d, rgb(4, 4, 7), 0)
		local st = new("UIStroke", { Color = Color3.new(1, 1, 1), Thickness = math.max(2, math.floor(H * 0.025)) }, ring)
		local sg = new("UIGradient", { Color = seq(rgb(255, 244, 220), rgb(214, 160, 70), rgb(40, 30, 20), rgb(255, 244, 220)) }, st)
		animate(sg, "spin", 40)
	else -- slate (and anything unknown)
		g.BackgroundColor3 = Color3.new(1, 1, 1)
		new("UIGradient", { Color = seq(rgb(38, 42, 50), rgb(20, 22, 27)), Rotation = 90 }, g)
	end
end

-- a frame's size in its own (unscaled) pixels: its on-screen size over every UIScale on it and above it
local function designSize(f: GuiObject): Vector2
	local k = 1
	local a: Instance? = f
	while a and not a:IsA("LayerCollector") do
		local sc = a:FindFirstChildOfClass("UIScale")
		if sc then k *= sc.Scale end
		a = a.Parent
	end
	return f.AbsoluteSize / math.max(0.01, k)
end

-- backgrounds with turned pieces need a CanvasGroup to clip them to the box (a clipping frame doesn't clip turned
-- children); the rest use a plain clipping frame (every CanvasGroup costs a texture)
local TURNED = { stripes = true, grid = true, flames = true, carbon = true, aurora = true, molten = true, camo = true }

-- fill `frame` with background `id` (replaces the one there), clipped to its rounded box; it is redrawn if the frame
-- changes size
function C.paintBanner(frame: GuiObject, id: string?, corner: number?): GuiObject
	local old = frame:FindFirstChild("Banner")
	if old then old:Destroy() end
	local want = if C.info("banner", id) then id :: string else C.DEFAULT.banner
	local g = new(if TURNED[want] then "CanvasGroup" else "Frame", { Name = "Banner", BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 0, ClipsDescendants = true }, frame)
	if corner and corner > 0 then new("UICorner", { CornerRadius = UDim.new(0, corner) }, g) end
	local drawn = Vector2.zero
	local function draw()
		local s = designSize(frame)
		if s.X < 2 or s.Y < 2 or (s - drawn).Magnitude < 1 then return end
		drawn = s
		for _, c in g:GetChildren() do if not c:IsA("UICorner") then c:Destroy() end end
		drawBanner(g, want, s.X, s.Y)
	end
	draw()
	local con = frame:GetPropertyChangedSignal("AbsoluteSize"):Connect(draw)
	g.Destroying:Connect(function() con:Disconnect() end)
	return g
end

-- a border on `frame` (replaces the one there): strokes and corner pieces in a folder named Border
function C.paintBorder(frame: GuiObject, id: string?, corner: number?)
	local old = frame:FindFirstChild("Border")
	if old then old:Destroy() end
	local want = if C.info("border", id) then id :: string else C.DEFAULT.border
	local f = new("Frame", { Name = "Border", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = 20 }, frame)
	local rad = corner or 8
	new("UICorner", { CornerRadius = UDim.new(0, rad) }, f)
	local function stroke(o: Instance, thick: number, color: Color3, alpha: number): UIStroke
		return new("UIStroke", { Color = color, Thickness = thick, Transparency = alpha, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, o)
	end
	local function brackets(color: Color3, len: number, th: number)
		for _, c in { { 0, 0 }, { 1, 0 }, { 0, 1 }, { 1, 1 } } do
			local ax = Vector2.new(c[1], c[2])
			local h = new("Frame", { BorderSizePixel = 0, BackgroundColor3 = color, AnchorPoint = ax, Position = UDim2.new(c[1], (c[1] * 2 - 1) * -4, c[2], (c[2] * 2 - 1) * -4),
				Size = UDim2.fromOffset(len, th), ZIndex = 21 }, f)
			local v = h:Clone()
			v.Size = UDim2.fromOffset(th, len)
			v.Parent = f
		end
	end
	if want == "steel" then
		local s = stroke(f, 2, Color3.new(1, 1, 1), 0)
		new("UIGradient", { Color = seq(rgb(214, 220, 228), rgb(96, 102, 112)), Rotation = 90 }, s)
	elseif want == "brass" then
		local s = stroke(f, 2, Color3.new(1, 1, 1), 0)
		new("UIGradient", { Color = seq(rgb(236, 204, 132), rgb(140, 100, 50), rgb(220, 186, 110)), Rotation = 60 }, s)
	elseif want == "twin" then
		stroke(f, 1, rgb(236, 238, 242), 0.45)
		local inner = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(5, 5), Size = UDim2.new(1, -10, 1, -10), ZIndex = 20 }, f)
		new("UICorner", { CornerRadius = UDim.new(0, math.max(2, rad - 4)) }, inner)
		stroke(inner, 1, rgb(236, 238, 242), 0.7)
	elseif want == "brackets" then
		stroke(f, 1, rgb(236, 238, 242), 0.8)
		brackets(rgb(226, 230, 236), 18, 2)
	elseif want == "ember" then
		local s = stroke(f, 2, Color3.new(1, 1, 1), 0)
		animate(new("UIGradient", { Color = seq(rgb(240, 120, 60), rgb(90, 24, 16), rgb(240, 180, 90), rgb(90, 24, 16), rgb(240, 120, 60)) }, s), "spin", 30)
	elseif want == "gilded" then
		local s = stroke(f, 3, Color3.new(1, 1, 1), 0)
		new("UIGradient", { Color = seq(rgb(255, 230, 160), rgb(176, 124, 40), rgb(255, 214, 120), rgb(150, 104, 34)), Rotation = 35 }, s)
		brackets(rgb(240, 200, 110), 22, 3)
	elseif want == "prism" then
		local s = stroke(f, 3, Color3.new(1, 1, 1), 0)
		animate(new("UIGradient", { Color = seq(rgb(214, 120, 140), rgb(220, 190, 110), rgb(110, 200, 160), rgb(110, 150, 230), rgb(170, 120, 220), rgb(214, 120, 140)) }, s), "spin", 45)
	elseif want == "halo" then
		local glow = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(-4, -4), Size = UDim2.new(1, 8, 1, 8), ZIndex = 19 }, f)
		new("UICorner", { CornerRadius = UDim.new(0, rad + 4) }, glow)
		local gs = stroke(glow, 5, rgb(240, 214, 150), 0.78)
		animate(new("UIGradient", { Color = seq(rgb(255, 250, 236), rgb(214, 160, 70), rgb(255, 250, 236)) }, gs), "spin", 25)
		local s = stroke(f, 3, Color3.new(1, 1, 1), 0)
		animate(new("UIGradient", { Color = seq(rgb(255, 250, 236), rgb(214, 160, 70), rgb(120, 84, 30), rgb(255, 250, 236)) }, s), "spin", 25)
		brackets(rgb(250, 230, 180), 22, 3)
	else -- hairline
		stroke(f, 1, rgb(255, 255, 255), 0.8)
	end
end

-- a small sample of one item in `frame` (a shop tile, the picker): the background, the border, or a title on slate
function C.preview(t: string, id: string, frame: GuiObject)
	for _, c in frame:GetChildren() do if c.Name == "Banner" or c.Name == "Border" or c.Name == "Title" then c:Destroy() end end
	if t == "banner" then
		C.paintBanner(frame, id, 6)
		C.paintBorder(frame, "hairline", 6)
	elseif t == "border" then
		C.paintBanner(frame, "slate", 6)
		C.paintBorder(frame, id, 6)
	elseif t == "title" then
		C.paintBanner(frame, "slate", 6)
		C.paintBorder(frame, "hairline", 6)
		local txt = C.titleText(id)
		new("TextLabel", { Name = "Title", BackgroundTransparency = 1, Size = UDim2.new(1, -12, 1, 0), Position = UDim2.fromOffset(6, 0), ZIndex = 5,
			Text = if txt == "" then "—" else txt, TextColor3 = C.titleColor(id), TextScaled = true, TextWrapped = true,
			FontFace = Font.new("rbxasset://fonts/families/BuilderSans.json", Enum.FontWeight.Bold) }, frame)
		local cap = frame:FindFirstChild("Title") :: TextLabel
		new("UITextSizeConstraint", { MaxTextSize = 15 }, cap)
	end
end
-- (the loot reel's name for it: LootTable's card hook calls picture(t, id, frame) to draw a card look on a reel card)
C.picture = C.preview

return C
