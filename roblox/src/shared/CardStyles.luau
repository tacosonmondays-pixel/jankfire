--!strict
-- the player card's looks: borders, backgrounds ("banner") and titles. what exists, how rare it is, and how to draw
-- it. borders and titles are drawn in the GUI. backgrounds are real photos and textures since 16 Nov (the owner: the
-- drawn ones looked "very ai ish"): public-domain NASA photos and CC0 Poly Haven / ambientCG skies and textures, each
-- checked at full size (no text, logos, faces or watermarks), cropped to 1024x320 and graded quieter; C.CREDITS has
-- where each came from. Slate (a plain gradient) and Static (TV noise) stay drawn. titles are the web game's
-- end-of-match medals (shared/medals.js). free ones everybody owns; the rest come from Duffel Bags and the shop and are kept by the loot
-- save (Loot.owns(p, "border", id): gun-less types, key = the id, like a weapon skin).
-- the card wears { border, banner, title } (Stats.luau keeps the pick); drawing is for clients only.
local RunService = game:GetService("RunService")

local C = {}

C.TYPES = { "border", "banner", "title" }
C.TYPE_NAMES = { border = "Border", banner = "Background", title = "Title" }
C.DEFAULT = { border = "hairline", banner = "slate", title = "none" }
-- the container the non-free ones roll from (LootTable's card hook reads it: the Duffel Bag, as one more "gun")
C.CONTAINER = "bag"

export type Item = { type: string, id: string, name: string, rarity: string, text: string?, vip: boolean? } -- (vip: VIP-pack only)

-- rarity tints (the same as LootTable.RARITY; copied so this module needs nothing else)
C.RARITY_COLOR = {
	free = Color3.fromRGB(150, 156, 166), common = Color3.fromRGB(122, 178, 104), rare = Color3.fromRGB(78, 150, 226),
	epic = Color3.fromRGB(162, 108, 226), legendary = Color3.fromRGB(240, 178, 52),
	vip = Color3.fromRGB(255, 208, 72),
	secret = Color3.fromRGB(232, 132, 206), -- (the web game's pink, a step quieter)
}
-- "vip": the VIP pack's own (the shop session's): never in a container (LootTable rolls only the rarities it knows),
-- never in the shop's rotation or bundles (forSale leaves them out), owned only through Loot.grant of the VIP offer
C.VIP_ONLY = "vip"
function C.isVip(t: string, id: string): boolean
	local i = C.info(t, id)
	return i ~= nil and i.rarity == C.VIP_ONLY
end
-- "secret": found, never bought or rolled (18 Nov 2026: the hub's hidden mannequin of the web game's player gives the
-- OG title, server/HubEgg.server.luau). never in a container (LootTable rolls only the rarities it knows), never in the
-- shop (forSale and Shop leave them out), owned only through Loot.grant of "egg:<type>:<id>" (Shop.offer); the card's
-- picker shows one only once it is yours
C.SECRET = "secret"
function C.isSecret(t: string, id: string): boolean
	local i = C.info(t, id)
	return i ~= nil and i.rarity == C.SECRET
end

-- id = { name, rarity }, in the order the picker shows them
local BORDERS = {
	{ "hairline", "Hairline", "free" }, { "steel", "Steel", "free" },
	{ "brass", "Brass", "common" }, { "twin", "Twin Line", "common" },
	{ "brackets", "Brackets", "rare" }, { "ember", "Ember", "rare" },
	{ "gilded", "Gilded", "epic" }, { "prism", "Prism", "epic" },
	{ "halo", "Halo", "legendary" },
	{ "ducky", "Ducky", "vip" },
}
local BANNERS = {
	{ "slate", "Slate", "free" }, { "concrete", "Concrete", "free" }, { "metal", "Metal", "free" },
	{ "sunset", "Sunset", "common" }, { "stars", "Night Sky", "common" }, { "camo", "Camo", "common" },
	{ "flames", "Furnace", "rare" }, { "carbon", "Carbon", "rare" }, { "static", "Static", "rare" },
	{ "aurora", "Aurora", "epic" }, { "molten", "Molten", "epic" },
	{ "eclipse", "Eclipse", "legendary" },
}
-- the backgrounds that are pictures (uploaded 16 Nov 2026, all Approved), and where each came from
C.IMAGES = {
	concrete = "rbxassetid://80093131602053", metal = "rbxassetid://119268820513573",
	sunset = "rbxassetid://131169722023201", stars = "rbxassetid://109006184975619", camo = "rbxassetid://131795114784336",
	flames = "rbxassetid://76170896329040", carbon = "rbxassetid://126045915944582",
	aurora = "rbxassetid://88607740740565", molten = "rbxassetid://77558571123420",
	eclipse = "rbxassetid://76928894691984",
} :: { [string]: string }
C.CREDITS = {
	concrete = "Poly Haven, concrete_wall_008 (CC0)", metal = "Poly Haven, metal_plate_02 (CC0)",
	sunset = "Poly Haven, the_sky_is_on_fire (CC0)", stars = "Poly Haven, satara_night_no_lamps (CC0)",
	camo = "Poly Haven, japanese_sycamore bark (CC0)", flames = "ambientCG, Lava004 (CC0)", carbon = "ambientCG, Fabric004 (CC0)",
	aurora = "NASA, iss058e005282 (public domain)", molten = "ambientCG, Lava001 (CC0)",
	eclipse = "NASA / Carla Thomas, AFRC2017-0233-005 (public domain)",
} :: { [string]: string }
-- titles: id, the words, rarity (the web medals keep their own words)
local TITLES = {
	{ "none", "", "free" }, { "rookie", "ROOKIE", "free" }, { "new_hire", "NEW HIRE", "free" },
	{ "first", "FIRST BLOOD", "common" }, { "multi2", "TWO FOR ONE", "common" }, { "revenge", "FILED A COMPLAINT", "common" },
	{ "pacifist", "CONSCIENTIOUS OBJECTOR", "common" },
	{ "hs", "HEAD OF HR", "rare" }, { "far", "LONG DISTANCE CALL", "rare" }, { "melee", "HANDS-ON MANAGER", "rare" },
	{ "void", "WASTE DISPOSAL", "rare" },
	{ "multi3", "BULK DISCOUNT", "epic" }, { "streak", "ON A TEAR", "epic" }, { "fast", "OVER THE LIMIT", "epic" },
	{ "untouch", "UNTOUCHABLE", "legendary" }, { "mvp", "EMPLOYEE OF THE MONTH", "legendary" },
	-- (17 Nov 2026: the owner's picks, "can one be princess some cute ones cool ones meme ones etc"; rarities the main
	-- session's, the owner may move them. they also show over heads: client/OverheadTitles)
	-- cute
	{ "princess", "PRINCESS", "legendary" }, { "stardust", "STARDUST", "epic" }, { "duckling", "DUCKLING", "rare" },
	{ "soft_serve", "SOFT SERVE", "rare" }, { "cutie", "CUTIE", "rare" }, { "bunny", "BUNNY", "common" },
	{ "bonbon", "BONBON", "common" }, { "kitten", "KITTEN", "common" }, { "squishy", "SQUISHY", "common" },
	-- cool
	{ "apex", "APEX", "legendary" }, { "phantom", "PHANTOM", "epic" }, { "deadeye", "DEADEYE", "epic" },
	{ "zero_recoil", "ZERO RECOIL", "epic" }, { "nightshade", "NIGHTSHADE", "epic" }, { "headhunter", "HEADHUNTER", "rare" },
	{ "afterburner", "AFTERBURNER", "rare" }, { "cold_blooded", "COLD BLOODED", "rare" }, { "blackout", "BLACKOUT", "rare" },
	{ "iron_dome", "IRON DOME", "rare" }, { "ironclad", "IRONCLAD", "common" }, -- (IRON DOME: the owner's, 17 Nov)
	-- meme
	{ "sigma", "SIGMA", "epic" }, { "skill_issue", "SKILL ISSUE", "rare" }, { "alpha", "ALPHA", "rare" },
	{ "lone_wolf", "LONE WOLF", "rare" }, { "sweat", "SWEAT", "common" }, { "npc", "NPC", "common" }, { "bot", "BOT", "common" },
	{ "chud", "CHUD", "common" },
	-- JANKFIRE's own
	{ "jank_certified", "JANK CERTIFIED", "legendary" }, { "patient_zero", "PATIENT ZERO", "epic" },
	{ "duck_rain_survivor", "DUCK RAIN SURVIVOR", "epic" }, { "spoon_main", "SPOON MAIN", "rare" },
	{ "vip", "VIP", "vip", "VIP" }, -- (the VIP pack's title, words "VIP"; 4th: its name when it isn't sentence case)
	{ "og", "OG", "secret", "OG" }, -- (found: the hub's hidden mannequin, 18 Nov)
}

C.ORDER = { border = {}, banner = {}, title = {} } :: { [string]: { string } }
C.ITEMS = { border = {}, banner = {}, title = {} } :: { [string]: { [string]: Item } }
for _, r in BORDERS do
	C.ITEMS.border[r[1]] = { type = "border", id = r[1], name = r[2], rarity = r[3], vip = if r[3] == "vip" then true else nil }
	table.insert(C.ORDER.border, r[1])
end
for _, r in BANNERS do
	C.ITEMS.banner[r[1]] = { type = "banner", id = r[1], name = r[2], rarity = r[3], vip = if r[3] == "vip" then true else nil }
	table.insert(C.ORDER.banner, r[1])
end
for _, r in TITLES do
	local name = if r[4] then r[4] elseif r[2] == "" then "No Title" else string.upper(string.sub(r[2], 1, 1)) .. string.lower(string.sub(r[2], 2))
	C.ITEMS.title[r[1]] = { type = "title", id = r[1], name = name, rarity = r[3], text = r[2], vip = if r[3] == "vip" then true else nil }
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
-- the ones a container or the shop's rotation may hand out: not free, not VIP-only
function C.forSale(t: string): { Item }
	local out = {}
	for _, id in C.ORDER[t] or {} do
		local i = C.ITEMS[t][id]
		if i.rarity ~= "free" and i.rarity ~= C.VIP_ONLY and i.rarity ~= C.SECRET then table.insert(out, i) end
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
	if i and i.rarity == C.VIP_ONLY then return c end -- (VIP keeps its full gold)
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

-- the drawn backgrounds' pieces for a box W x H (px): Static, and Slate (the default, and what a picture shows while it
-- loads)
local function drawBanner(g: GuiObject, id: string, W: number, H: number)
	local r = Random.new(#id * 97 + 13)
	if id == "static" then
		g.BackgroundColor3 = rgb(34, 35, 38)
		for _ = 1, math.min(180, math.floor(W * H / 320)) do
			local v = math.floor(30 + r:NextNumber() * 90)
			new("Frame", { BorderSizePixel = 0, BackgroundColor3 = rgb(v, v, v + 4), Position = UDim2.fromOffset(math.floor(r:NextNumber() * W / 3) * 3, math.floor(r:NextNumber() * H / 3) * 3),
				Size = UDim2.fromOffset(3 + math.floor(r:NextNumber() * 3) * 3, 3) }, g)
		end
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

-- fill `frame` with background `id` (replaces the one there), clipped to its rounded box. a picture fills the box and
-- crops what doesn't fit (centred); a drawn one is redrawn if the frame changes size
function C.paintBanner(frame: GuiObject, id: string?, corner: number?): GuiObject
	local old = frame:FindFirstChild("Banner")
	if old then old:Destroy() end
	local want = if C.info("banner", id) then id :: string else C.DEFAULT.banner
	local img = C.IMAGES[want]
	if img then
		local p = new("ImageLabel", { Name = "Banner", BorderSizePixel = 0, BackgroundColor3 = rgb(20, 22, 27), Size = UDim2.fromScale(1, 1), ZIndex = 0,
			Image = img, ScaleType = Enum.ScaleType.Crop }, frame)
		if corner and corner > 0 then new("UICorner", { CornerRadius = UDim.new(0, corner) }, p) end
		return p
	end
	local g = new("Frame", { Name = "Banner", BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 0, ClipsDescendants = true }, frame)
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
	elseif want == "ducky" then
		-- the VIP border: yellow and gold with a slow shimmer, a warm glow, gold corners, and a little duck sitting on
		-- the top edge near the left corner (drawn: tail, body, wing, head, beak, eye; no picture, no text)
		local glow = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(-4, -4), Size = UDim2.new(1, 8, 1, 8), ZIndex = 19 }, f)
		new("UICorner", { CornerRadius = UDim.new(0, rad + 4) }, glow)
		stroke(glow, 6, rgb(255, 214, 90), 0.8)
		local s = stroke(f, 3, Color3.new(1, 1, 1), 0)
		animate(new("UIGradient", { Color = seq(rgb(255, 228, 112), rgb(214, 150, 30), rgb(255, 242, 176), rgb(196, 132, 24), rgb(255, 228, 112)) }, s), "spin", 28)
		brackets(rgb(246, 202, 84), 20, 3)
		local YELLOW, GOLD, DEEP = rgb(255, 212, 66), rgb(188, 130, 28), rgb(232, 174, 40)
		local duck = new("Frame", { Name = "Duck", BackgroundTransparency = 1, Position = UDim2.fromOffset(16, -14), Size = UDim2.fromOffset(34, 20), ZIndex = 22 }, f)
		local function piece(x: number, y: number, w: number, h: number, color: Color3, rot: number?, round: boolean?, edge: boolean?): Frame
			local p = new("Frame", { BorderSizePixel = 0, BackgroundColor3 = color, Position = UDim2.fromOffset(x, y), Size = UDim2.fromOffset(w, h), Rotation = rot or 0, ZIndex = 23 }, duck)
			new("UICorner", { CornerRadius = if round == false then UDim.new(0, 2) else UDim.new(1, 0) }, p)
			if edge then new("UIStroke", { Color = GOLD, Thickness = 1.5 }, p) end
			return p
		end
		piece(1, 6, 7, 7, YELLOW, 45, false, true) -- the tail
		piece(3, 6, 22, 13, YELLOW, 0, true, true) -- the body
		piece(18, 0, 12, 12, YELLOW, 0, true, true) -- the head
		piece(9, 9, 10, 6, DEEP, -8, true, false).ZIndex = 24 -- the wing
		piece(28, 5, 6, 4, rgb(240, 140, 40), 0, false, false).ZIndex = 24 -- the beak
		piece(25, 3, 2, 2, rgb(34, 26, 16), 0, true, false).ZIndex = 25 -- the eye
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
