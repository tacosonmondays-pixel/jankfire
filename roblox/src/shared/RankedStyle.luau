--!strict
-- RANKED STYLE: how a rank looks (clients only: it makes GUI objects). the Play screen and the player card
-- (ProfileUI's right-hand mark, agreed with the player-cards session) draw ranks with it:
--   RankedStyle.badge(parent, size, ranked) -> a square Frame `size` px across, no text in it. the caller places it
--   RankedStyle.label(ranked) -> "GOLD II", "APEX 2,114", "PLACEMENTS 2/5", "UNRANKED"
--   RankedStyle.color(ranked) -> the colour that line is drawn in
-- `ranked` is a rank view from the server (RankedData.view): { tier = "gold", div = 1..3 or nil, placed, name, r, n,
-- need, mode? } or nil / { unranked = true }. a player card's `ranked` is the player's best mode (RankedData.summary),
-- with the same fields.
-- the badge, drawn from frames (no uploaded pictures): a shield in the tier's metal (Shared.Ranks' colours) with a dark
-- core and 1 to 3 chevrons for the division (III one, I three); a frame round it from Platinum, side blades from
-- Diamond, a crown point from Master, three points for Apex. placements: a pale hollow shield with a dot per
-- placement match (filled = played). unranked: a hollow grey shield with a short dash.
local Shared = script.Parent
local Ranks = require(Shared:WaitForChild("Ranks"))
local Ranked = require(Shared:WaitForChild("Ranked"))

local RankedStyle = {}

local CORE = Color3.fromRGB(18, 20, 24)
local GREY = Color3.fromRGB(120, 126, 136)
local PALE = Color3.fromRGB(196, 200, 208)

local metal: { [string]: { color: Color3, deep: Color3 } } = {}
for _, t in Ranks.TIERS do metal[t.id] = { color = t.color, deep = t.deep } end

local function new(class: string, props: { [string]: any }, parent: Instance?): any
	local o = Instance.new(class)
	for k, v in props do (o :: any)[k] = v end
	if parent then o.Parent = parent end
	return o
end

local function unranked(v: any): boolean
	return v == nil or v.unranked == true or (type(v.n) == "number" and v.n <= 0 and v.placed ~= true)
end
local function placing(v: any): boolean
	return not unranked(v) and v.placed ~= true
end
local function tierIndex(v: any): number
	for i, t in Ranked.TIERS do if t.id == v.tier then return i end end
	return 1
end

function RankedStyle.label(v: any): string
	if unranked(v) then return "UNRANKED" end
	if type(v.name) == "string" and v.name ~= "" then
		-- the player card names the mode its rank is from: "GOLD II  ·  2V2"
		if v.card == true and v.placed == true and type(v.mode) == "string" then return v.name .. "  ·  " .. string.upper(v.mode) end
		return v.name
	end
	return "RANKED"
end

function RankedStyle.color(v: any): Color3
	if unranked(v) then return GREY end
	if placing(v) then return PALE end
	local m = metal[v.tier] or metal.iron
	return m.color:Lerp(Color3.new(1, 1, 1), 0.25)
end

-- one shield shape, W wide, its top-left at (x, y) in the box: a rounded block over a point (a turned square)
local function shield(box: Frame, x: number, y: number, W: number, color: Color3, z: number, alpha: number?): { Frame }
	local a = alpha or 0
	local top = new("Frame", { Name = "ShieldTop", BorderSizePixel = 0, BackgroundColor3 = color, BackgroundTransparency = a, ZIndex = z,
		Position = UDim2.fromOffset(x, y), Size = UDim2.fromOffset(W, math.floor(W * 0.74)) }, box)
	new("UICorner", { CornerRadius = UDim.new(0, math.max(2, math.floor(W * 0.16))) }, top)
	local side = math.floor(W / math.sqrt(2) + 0.5)
	local pt = new("Frame", { Name = "ShieldPoint", BorderSizePixel = 0, BackgroundColor3 = color, BackgroundTransparency = a, ZIndex = z,
		AnchorPoint = Vector2.new(0.5, 0.5), Rotation = 45, Position = UDim2.fromOffset(x + W / 2, y + W * 0.68),
		Size = UDim2.fromOffset(side, side) }, box)
	new("UICorner", { CornerRadius = UDim.new(0, math.max(1, math.floor(W * 0.06))) }, pt)
	return { top, pt }
end

-- a chevron (a V pointing down) centred at (cx, cy), w wide
local function chevron(box: Frame, cx: number, cy: number, w: number, thick: number, color: Color3, z: number)
	local len = w * 0.6
	for _, sgn in { -1, 1 } do
		local b = new("Frame", { Name = "Chevron", BorderSizePixel = 0, BackgroundColor3 = color, ZIndex = z, AnchorPoint = Vector2.new(0.5, 0.5),
			Rotation = sgn * -32, Position = UDim2.fromOffset(cx + sgn * w * 0.24, cy), Size = UDim2.fromOffset(math.floor(len), thick) }, box)
		new("UICorner", { CornerRadius = UDim.new(1, 0) }, b)
	end
end

function RankedStyle.badge(parent: Instance, size: number, v: any): Frame
	local s = math.max(16, math.floor(size))
	local box = new("Frame", { Name = "RankedBadge", BackgroundTransparency = 1, Size = UDim2.fromOffset(s, s) }, parent)
	-- the shield: 0.62 of the box wide, its point near the bottom
	local W = math.floor(s * 0.62)
	local x0, y0 = math.floor((s - W) / 2), math.floor(s * 0.1)
	if unranked(v) or placing(v) then
		local edge = if unranked(v) then GREY else PALE
		shield(box, x0, y0, W, edge, 1)
		local inset = math.max(2, math.floor(s * 0.045))
		shield(box, x0 + inset, y0 + inset, W - inset * 2, CORE, 2)
		if unranked(v) then
			local d = new("Frame", { Name = "Dash", BorderSizePixel = 0, BackgroundColor3 = GREY, ZIndex = 3, AnchorPoint = Vector2.new(0.5, 0.5),
				Position = UDim2.fromOffset(s / 2, y0 + W * 0.5), Size = UDim2.fromOffset(math.floor(W * 0.36), math.max(2, math.floor(s * 0.05))) }, box)
			new("UICorner", { CornerRadius = UDim.new(1, 0) }, d)
		else
			-- a dot per placement match: played ones filled
			local need = math.max(1, math.floor(tonumber(v.need) or Ranked.PLACEMENTS))
			local played = math.clamp(math.floor(tonumber(v.n) or 0), 0, need)
			local dot = math.max(3, math.floor(W * 0.11))
			local gap = math.max(2, math.floor(dot * 0.55))
			local total = need * dot + (need - 1) * gap
			for i = 1, need do
				local f = new("Frame", { Name = "Dot", BorderSizePixel = 0, ZIndex = 3, BackgroundColor3 = if i <= played then PALE else GREY,
					BackgroundTransparency = if i <= played then 0 else 0.55,
					Position = UDim2.fromOffset(math.floor(s / 2 - total / 2 + (i - 1) * (dot + gap)), math.floor(y0 + W * 0.5 - dot / 2)),
					Size = UDim2.fromOffset(dot, dot) }, box)
				new("UICorner", { CornerRadius = UDim.new(1, 0) }, f)
			end
		end
		return box
	end
	local ti = tierIndex(v)
	local m = metal[v.tier] or metal.iron
	local light = m.color:Lerp(Color3.new(1, 1, 1), 0.35)
	-- side blades (Diamond up): two slim bars behind the shield, swept up
	if ti >= 5 then
		for _, sgn in { -1, 1 } do
			local b = new("Frame", { Name = "Blade", BorderSizePixel = 0, BackgroundColor3 = m.color, ZIndex = 1, AnchorPoint = Vector2.new(0.5, 0.5),
				Rotation = sgn * 24, Position = UDim2.fromOffset(s / 2 + sgn * W * 0.62, y0 + W * 0.42),
				Size = UDim2.fromOffset(math.max(3, math.floor(s * 0.08)), math.floor(W * 0.72)) }, box)
			new("UICorner", { CornerRadius = UDim.new(1, 0) }, b)
			new("UIGradient", { Color = ColorSequence.new(light, m.deep), Rotation = 90 }, b)
		end
	end
	-- the frame (Platinum up): a slightly bigger shield in the deep metal behind the body
	if ti >= 4 then
		local pad = math.max(2, math.floor(s * 0.045))
		shield(box, x0 - pad, y0 - pad, W + pad * 2, m.deep, 1)
	end
	-- the body, a lit edge along its top, and the dark core
	shield(box, x0, y0, W, m.color, 2)
	local lit = new("Frame", { Name = "Lit", BorderSizePixel = 0, BackgroundColor3 = light, ZIndex = 3,
		Position = UDim2.fromOffset(x0 + math.floor(W * 0.14), y0), Size = UDim2.fromOffset(math.floor(W * 0.72), math.max(1, math.floor(s * 0.03))) }, box)
	new("UICorner", { CornerRadius = UDim.new(1, 0) }, lit)
	local inset = math.max(2, math.floor(s * 0.07))
	shield(box, x0 + inset, y0 + inset, W - inset * 2, CORE, 3)
	-- crown points (Master: one, Apex: three) over the top edge
	if ti >= 6 then
		local n = if ti >= 7 then 3 else 1
		local pt = math.max(4, math.floor(s * 0.13))
		for i = 1, n do
			local off = if n == 1 then 0 else (i - 2) * W * 0.3
			local c = new("Frame", { Name = "Crown", BorderSizePixel = 0, BackgroundColor3 = if i == 2 or n == 1 then light else m.color, ZIndex = 4,
				AnchorPoint = Vector2.new(0.5, 0.5), Rotation = 45, Position = UDim2.fromOffset(s / 2 + off, y0 - pt * 0.15),
				Size = UDim2.fromOffset(pt, pt) }, box)
			new("UICorner", { CornerRadius = UDim.new(0, math.max(1, math.floor(pt * 0.15))) }, c)
		end
	end
	-- the division: chevrons (III one, II two, I three); Apex one long bright bar
	local cw = W - inset * 2
	local thick = math.max(2, math.floor(s * 0.05))
	if v.div == nil then
		local bar = new("Frame", { Name = "Top", BorderSizePixel = 0, BackgroundColor3 = light, ZIndex = 5, AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.fromOffset(s / 2, y0 + W * 0.5), Size = UDim2.fromOffset(math.floor(cw * 0.5), thick + 1) }, box)
		new("UICorner", { CornerRadius = UDim.new(1, 0) }, bar)
	else
		local count = math.clamp(math.floor(v.div), 1, 3)
		local step = math.max(thick + 2, math.floor(cw * 0.17))
		local mid = y0 + W * 0.52
		for i = 1, count do
			chevron(box, s / 2, mid + (i - (count + 1) / 2) * step, cw * 0.62, thick, light, 5)
		end
	end
	return box
end

return RankedStyle
