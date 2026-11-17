--!strict
-- FLAIR: kill effects and emotes. what exists, how rare, which are free, and a drawn tile for the shop, the loot reel and
-- the equip screen. (17 Nov 2026, the owner: "Can we also have basic kill effects? Reference the rivals ones!! As well
-- as other games and maybe some emotes??"; research in the vault, Research\Kill effects and emotes.md; doc FLAIR.md)
--   kill:  what plays on a body when YOU get the kill (client/KillFx.luau draws it, server/FlairServer picks the real
--          killer's). one per player, not per weapon: the web game's own rule (shared/cosmetics.js "kill").
--          "none" is the default: the body falls apart as it always has.
--   emote: a short animation on the wheel (hold T). made with Studio's prompt-to-animation tool (generate_animation).
-- the shape is CardStyles' (the loot and shop hooks read both): TYPES, info(t, id) -> { name, rarity }?, ORDER[t],
-- CONTAINER (the Duffel Bag), forSale(t), picture(t, id, frame). free ones everybody owns; the rest are kept by the
-- loot save as gun-less types (Loot.owns(p, "kill", id), key = the id, like a weapon skin).
local F = {}

F.TYPES = { "kill", "emote" }
F.TYPE_NAMES = { kill = "Kill Effect", emote = "Emote" }
F.CONTAINER = "bag"
F.SLOTS = 8 -- the emote wheel (Fortnite's current wheel has 8; a slot may repeat an emote)
F.DEFAULT = { kill = "none", emotes = { "wave", "salute", "", "", "", "", "", "" } }
F.COOLDOWN = 2 -- s between emotes (Rivals has none; spam guard)

export type Item = { type: string, id: string, name: string, rarity: string, vip: boolean? }
export type Kill = Item & { dur: number, tint: Color3 }
export type Emote = Item & { anim: string, len: number, loop: boolean }

-- rarity tints (the same as LootTable.RARITY; copied so this module needs nothing else)
F.RARITY_COLOR = {
	free = Color3.fromRGB(150, 156, 166), common = Color3.fromRGB(122, 178, 104), rare = Color3.fromRGB(78, 150, 226),
	epic = Color3.fromRGB(162, 108, 226), legendary = Color3.fromRGB(240, 178, 52),
	vip = Color3.fromRGB(255, 208, 72),
}
F.VIP_ONLY = "vip"

-- kill effects: id, name, rarity, seconds, the one colour it carries (tiles and the equip screen's chip)
local KILLS = {
	{ "none", "Default", "free", 0, Color3.fromRGB(150, 156, 166) },
	{ "dissolve", "Dissolve", "free", 1.3, Color3.fromRGB(214, 224, 236) },
	{ "shatter", "Shatter", "free", 1.0, Color3.fromRGB(176, 214, 236) },
	{ "ember", "Ember", "rare", 1.4, Color3.fromRGB(236, 120, 52) },
	{ "ink", "Ink", "epic", 1.2, Color3.fromRGB(58, 62, 96) },
	{ "ascend", "Ascend", "epic", 1.5, Color3.fromRGB(255, 232, 186) },
	{ "static", "Static", "legendary", 1.0, Color3.fromRGB(150, 226, 255) },
}
-- emotes: id, name, rarity, animation, seconds, loops (one-shots end on their own; a loop runs till you move)
-- (the clips: generate_animation, 17 Nov 2026; wave and salute re-uploaded as Animations through Open Cloud (the tool's
-- own publish timed out), the rest as the tool published them. prompts in FLAIR.md)
local EMOTES = {
	{ "wave", "Wave", "free", "rbxassetid://132747832692830", 2.97, false },
	{ "salute", "Salute", "free", "rbxassetid://134567333056285", 2.97, false },
	{ "clap", "Slow Clap", "common", "rbxassetid://77903138772400", 2.97, false },
	{ "victory", "Fist Pump", "rare", "rbxassetid://89328448326408", 2.47, false },
	{ "bow", "Bow", "rare", "rbxassetid://87535060714783", 2.97, false },
	{ "groove", "Groove", "epic", "rbxassetid://135577596597530", 3.97, true },
}

F.ORDER = { kill = {}, emote = {} } :: { [string]: { string } }
F.ITEMS = { kill = {}, emote = {} } :: { [string]: { [string]: any } }
for _, r in KILLS do
	table.insert(F.ORDER.kill, r[1])
	F.ITEMS.kill[r[1]] = { type = "kill", id = r[1], name = r[2], rarity = r[3], dur = r[4], tint = r[5] }
end
for _, r in EMOTES do
	table.insert(F.ORDER.emote, r[1])
	F.ITEMS.emote[r[1]] = { type = "emote", id = r[1], name = r[2], rarity = r[3], anim = r[4], len = r[5], loop = r[6] }
end

function F.isType(t: any): boolean
	return t == "kill" or t == "emote"
end
function F.info(t: any, id: any): any
	if not F.isType(t) or type(id) ~= "string" then return nil end
	return F.ITEMS[t][id]
end
function F.isFree(t: string, id: string): boolean
	local i = F.info(t, id)
	return i ~= nil and i.rarity == "free"
end
function F.isVip(t: string, id: string): boolean
	local i = F.info(t, id)
	return i ~= nil and i.rarity == F.VIP_ONLY
end
-- what the shop may sell and a bag may roll: not free, not VIP-only, and (an emote) its clip is uploaded
function F.forSale(t: string): { any }
	local out = {}
	for _, id in (F.ORDER[t] or {}) do
		local i = F.ITEMS[t][id]
		if i and i.rarity ~= "free" and i.rarity ~= F.VIP_ONLY and (t ~= "emote" or i.anim ~= "rbxassetid://0") then
			table.insert(out, i)
		end
	end
	return out
end
-- the wheel's slots from the player attribute "Emotes" ("wave,salute,,,,,,")
function F.slotsOf(s: any): { string }
	local out = {}
	local parts = if type(s) == "string" then string.split(s, ",") else {}
	for i = 1, F.SLOTS do
		local id = parts[i] or ""
		out[i] = if F.info("emote", id) then id else ""
	end
	return out
end

-- ------------------------------------------------------------------ the tile (drawn from frames: no uploads)
-- a figure on a dark card, the effect's one colour on it; for an emote, the figure's arms show the move. the shop,
-- the loot reel and the equip screen call it on an empty frame of any size (it redraws when the size changes)
local function new(class: string, props: { [string]: any }, parent: Instance?): any
	local o = Instance.new(class)
	for k, v in props do (o :: any)[k] = v end
	if parent then o.Parent = parent end
	return o
end
local function round(o: Instance, r: number?) new("UICorner", { CornerRadius = if r then UDim.new(0, r) else UDim.new(0.5, 0) }, o) end
local PALE = Color3.fromRGB(196, 202, 212)

-- one limb: a rounded bar from (x0, y0) to (x1, y1) in the figure's 0..1 box
local BS = Vector2.new(64, 80) -- the figure box's pixel size while drawing (set by F.picture)
local function limb(p: Frame, x0: number, y0: number, x1: number, y1: number, w: number, c: Color3, z: number)
	local dx, dy = x1 - x0, y1 - y0
	local s = BS
	local len = math.sqrt((dx * s.X) ^ 2 + (dy * s.Y) ^ 2)
	local f = new("Frame", {
		BackgroundColor3 = c, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale((x0 + x1) / 2, (y0 + y1) / 2), Size = UDim2.fromOffset(len + w, w),
		Rotation = math.deg(math.atan2(dy * s.Y, dx * s.X)), ZIndex = z,
	}, p)
	round(f)
end

-- arm poses per emote: (shoulder -> elbow -> hand) for the left and right arm, in the figure box
local ARMS = {
	wave = { { 0.36, 0.34, 0.26, 0.5, 0.3, 0.64 }, { 0.64, 0.34, 0.8, 0.22, 0.78, 0.06 } },
	salute = { { 0.36, 0.34, 0.3, 0.5, 0.32, 0.64 }, { 0.64, 0.34, 0.78, 0.3, 0.6, 0.16 } },
	clap = { { 0.36, 0.34, 0.34, 0.5, 0.48, 0.44 }, { 0.64, 0.34, 0.66, 0.5, 0.52, 0.44 } },
	victory = { { 0.36, 0.34, 0.3, 0.5, 0.32, 0.64 }, { 0.64, 0.34, 0.74, 0.2, 0.7, 0.04 } },
	bow = { { 0.38, 0.4, 0.4, 0.52, 0.52, 0.48 }, { 0.62, 0.4, 0.66, 0.56, 0.64, 0.68 } },
	groove = { { 0.36, 0.34, 0.22, 0.42, 0.2, 0.28 }, { 0.64, 0.34, 0.74, 0.5, 0.86, 0.46 } },
}

local function figure(box: Frame, body: Color3, arms: any, lean: number)
	local z = box.ZIndex + 1
	local head = new("Frame", { BackgroundColor3 = body, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5 + lean * 0.5, 0.17 + math.abs(lean) * 0.3), Size = UDim2.fromScale(0.2, 0.2), ZIndex = z }, box)
	new("UIAspectRatioConstraint", {}, head)
	round(head)
	local w = math.max(3, BS.X * 0.11)
	limb(box, 0.5 + lean * 0.4, 0.33, 0.5, 0.62, w * 1.6, body, z) -- the body
	limb(box, 0.45, 0.62, 0.4, 0.95, w, body, z) -- legs
	limb(box, 0.55, 0.62, 0.6, 0.95, w, body, z)
	for _, a in arms do
		limb(box, a[1] + lean * 0.3, a[2], a[3], a[4], w * 0.85, body, z)
		limb(box, a[3], a[4], a[5], a[6], w * 0.85, body, z)
	end
end

local DOWN = { { 0.36, 0.34, 0.3, 0.5, 0.32, 0.64 }, { 0.64, 0.34, 0.7, 0.5, 0.68, 0.64 } }

local function drawKill(box: Frame, id: string, tint: Color3)
	local z = box.ZIndex + 1
	if id == "dissolve" then
		figure(box, PALE, DOWN, 0)
		-- the lower half gone to motes
		local cut = new("Frame", { BackgroundColor3 = Color3.fromRGB(22, 24, 30), BorderSizePixel = 0, Position = UDim2.fromScale(0, 0.62),
			Size = UDim2.fromScale(1, 0.4), ZIndex = z + 2 }, box)
		new("UIGradient", { Transparency = NumberSequence.new(1, 0), Rotation = 90 }, cut)
		for i = 1, 14 do
			local d = new("Frame", { BackgroundColor3 = tint, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
				Position = UDim2.fromScale(0.3 + ((i * 37) % 41) / 100, 0.48 + ((i * 23) % 50) / 100 * 0.9),
				Size = UDim2.fromScale(0.035, 0.035), BackgroundTransparency = (i % 4) * 0.2, ZIndex = z + 3 }, box)
			new("UIAspectRatioConstraint", {}, d)
			round(d)
		end
	elseif id == "shatter" then
		figure(box, tint, DOWN, 0)
		for i = 1, 9 do
			local a = i * 40
			local r = 0.3 + (i % 3) * 0.08
			local sh = new("Frame", { BackgroundColor3 = tint, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
				Position = UDim2.fromScale(0.5 + math.cos(math.rad(a)) * r, 0.5 + math.sin(math.rad(a)) * r * 0.9),
				Size = UDim2.fromScale(0.07, 0.035), Rotation = a + 30, BackgroundTransparency = 0.15, ZIndex = z + 3 }, box)
			sh.Name = "Shard"
		end
		for _, l in { { 0.42, 0.2, 0.56, 0.5 }, { 0.56, 0.5, 0.46, 0.8 }, { 0.5, 0.36, 0.62, 0.42 } } do
			limb(box, l[1], l[2], l[3], l[4], 2, Color3.fromRGB(30, 34, 42), z + 3)
		end
	elseif id == "ember" then
		figure(box, Color3.fromRGB(40, 34, 32), DOWN, 0)
		local g = new("Frame", { BackgroundColor3 = tint, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = z, BackgroundTransparency = 0 }, box)
		new("UIGradient", { Rotation = 90, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.6, 0.75), NumberSequenceKeypoint.new(1, 0.35) }) }, g)
		for i = 1, 10 do
			local d = new("Frame", { BackgroundColor3 = if i % 3 == 0 then Color3.fromRGB(255, 196, 120) else tint, BorderSizePixel = 0,
				AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.25 + ((i * 31) % 50) / 100, 0.08 + ((i * 17) % 40) / 100),
				Size = UDim2.fromScale(0.03, 0.03), ZIndex = z + 3 }, box)
			new("UIAspectRatioConstraint", {}, d)
			round(d)
		end
	elseif id == "ink" then
		figure(box, Color3.fromRGB(14, 14, 20), DOWN, 0)
		for i = 1, 8 do
			local a = i * 45 + 10
			local r = 0.32 + (i % 2) * 0.1
			local b = new("Frame", { BackgroundColor3 = if i % 4 == 0 then tint else Color3.fromRGB(14, 14, 20), BorderSizePixel = 0,
				AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5 + math.cos(math.rad(a)) * r, 0.52 + math.sin(math.rad(a)) * r),
				Size = UDim2.fromScale(0.06 + (i % 3) * 0.025, 0.06 + (i % 3) * 0.025), ZIndex = z + 3 }, box)
			new("UIAspectRatioConstraint", {}, b)
			round(b)
		end
	elseif id == "ascend" then
		local col = new("Frame", { BackgroundColor3 = tint, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromScale(0.5, 0),
			Size = UDim2.fromScale(0.5, 1), ZIndex = z }, box)
		new("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0.55), NumberSequenceKeypoint.new(1, 1) }) }, col)
		local inner = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromScale(0, -0.08), Size = UDim2.fromScale(1, 1), ZIndex = z }, box)
		figure(inner, Color3.fromRGB(255, 246, 228), DOWN, 0)
	elseif id == "static" then
		local back = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromScale(0.06, 0), Size = UDim2.fromScale(1, 1), ZIndex = z }, box)
		figure(back, Color3.fromRGB(70, 120, 150), DOWN, 0)
		local front = new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = z + 2 }, box)
		figure(front, tint, DOWN, 0)
		for _, y in { 0.24, 0.46, 0.7 } do
			new("Frame", { BackgroundColor3 = Color3.fromRGB(220, 244, 255), BorderSizePixel = 0, Position = UDim2.fromScale(0.16, y),
				Size = UDim2.fromScale(0.68, 0.025), ZIndex = z + 5 }, box)
			new("Frame", { BackgroundColor3 = Color3.fromRGB(22, 24, 30), BorderSizePixel = 0, Position = UDim2.fromScale(0.2, y + 0.03),
				Size = UDim2.fromScale(0.6, 0.045), ZIndex = z + 5 }, box)
		end
	else -- the default: a plain figure, slumped
		figure(box, PALE, DOWN, 0.06)
	end
end

-- draw the tile into `frame` (cleared first). the frame keeps its own size, corner and background
function F.picture(t: string, id: string, frame: GuiObject)
	local i = F.info(t, id)
	local function draw()
		for _, c in frame:GetChildren() do if c.Name == "FlairPic" then c:Destroy() end end
		if not i then return end
		local s = frame.AbsoluteSize
		if s.X < 2 or s.Y < 2 then return end
		local holder = new("Frame", { Name = "FlairPic", BackgroundColor3 = Color3.fromRGB(22, 24, 30), BorderSizePixel = 0,
			Size = UDim2.fromScale(1, 1), ZIndex = frame.ZIndex, ClipsDescendants = true }, frame)
		round(holder, 6)
		-- the rarity's colour, a soft glow from below
		local glow = new("Frame", { BackgroundColor3 = F.RARITY_COLOR[i.rarity] or PALE, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = frame.ZIndex }, holder)
		new("UIGradient", { Rotation = 90, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.7, 0.92), NumberSequenceKeypoint.new(1, 0.7) }) }, glow)
		-- the figure in a square in the middle
		local side = math.min(s.X, s.Y) * 0.84
		BS = Vector2.new(side * 0.8, side)
		local box = new("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.52),
			Size = UDim2.fromOffset(side * 0.8, side), ZIndex = frame.ZIndex + 1 }, holder)
		if t == "kill" then drawKill(box, id, i.tint)
		else
			local lean = if id == "bow" then 0.16 elseif id == "groove" then -0.06 else 0
			figure(box, PALE, ARMS[id] or DOWN, lean)
		end
	end
	draw()
	local con: RBXScriptConnection? = nil
	con = frame:GetPropertyChangedSignal("AbsoluteSize"):Connect(function()
		if not frame.Parent then if con then con:Disconnect() end return end
		draw()
	end)
end
F.preview = F.picture

return F
