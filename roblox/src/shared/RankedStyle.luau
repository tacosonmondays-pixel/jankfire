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

-- ------------------------------------------------------------------ Party Ranked's badges (the classic modes' ladder)
-- each tier's badge hints at what it is made of, drawn clean from frames like the duels' shields: a damp napkin with its
-- corner folded, a taped cardboard box, a kraft bag with a crinkled top, a roll of duct tape, a riveted metal plate, a
-- framed glass pane, a rubber duck in a small crown. the division is 1 to 3 round pips under it (III one, I three)
local PARTY: { [string]: { color: Color3, deep: Color3 } } = {
	napkin = { color = Color3.fromRGB(226, 234, 242), deep = Color3.fromRGB(150, 176, 204) },
	cardboard = { color = Color3.fromRGB(186, 138, 88), deep = Color3.fromRGB(122, 84, 48) },
	paperbag = { color = Color3.fromRGB(210, 174, 120), deep = Color3.fromRGB(150, 116, 72) },
	ducttape = { color = Color3.fromRGB(158, 164, 174), deep = Color3.fromRGB(88, 94, 104) },
	sheetmetal = { color = Color3.fromRGB(196, 206, 218), deep = Color3.fromRGB(112, 124, 140) },
	glass = { color = Color3.fromRGB(150, 220, 236), deep = Color3.fromRGB(64, 132, 156) },
	duck = { color = Color3.fromRGB(255, 208, 64), deep = Color3.fromRGB(214, 140, 30) },
}
RankedStyle.PARTY = PARTY

local function isParty(v: any): boolean
	return v ~= nil and (v.ladder == "party" or PARTY[v.tier] ~= nil)
end

local function round(f: Frame, r: number?)
	new("UICorner", { CornerRadius = if r then UDim.new(0, r) else UDim.new(1, 0) }, f)
end
local function box(parent: Instance, name: string, x: number, y: number, w: number, h: number, color: Color3, z: number, rot: number?): Frame
	return new("Frame", { Name = name, BorderSizePixel = 0, BackgroundColor3 = color, ZIndex = z, AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromOffset(x, y), Size = UDim2.fromOffset(math.max(1, math.floor(w)), math.max(1, math.floor(h))), Rotation = rot or 0 }, parent)
end

local DRAW: { [string]: (Frame, number, any) -> () } = {}
-- (each draws into a square of s px, centred on (s/2, s*0.44): the pips sit under it)
DRAW.napkin = function(b, s, c)
	local cx, cy, w = s / 2, s * 0.37, math.floor(s * 0.54)
	-- a square sheet with its top right corner dog-eared: the sheet less that corner, and the flap folded down over it
	-- (built from straight pieces, so nothing is painted in the background's colour)
	local sheet = new("Frame", { Name = "Napkin", BackgroundTransparency = 1, ZIndex = 2, AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromOffset(cx, cy), Size = UDim2.fromOffset(w, w) }, b)
	local L = math.max(2, math.floor(w * 0.36))
	local function piece(name: string, x: number, y: number, pw: number, ph: number)
		new("Frame", { Name = name, BorderSizePixel = 0, BackgroundColor3 = c.color, ZIndex = 2,
			Position = UDim2.fromOffset(x, y), Size = UDim2.fromOffset(pw, ph) }, sheet)
	end
	piece("Left", 0, 0, w - L, w)
	piece("LowerRight", w - L, L, L, w - L)
	-- the flap: the lower left half of the corner's square, cut by a clipped turned square
	local corner = new("Frame", { Name = "Corner", BackgroundTransparency = 1, ClipsDescendants = true, ZIndex = 3,
		Position = UDim2.fromOffset(w - L, 0), Size = UDim2.fromOffset(L, L) }, sheet)
	box(corner, "Flap", 0, L, L * 1.42, L * 1.42, c.deep:Lerp(c.color, 0.4), 3, 45)
	-- two drips hanging under it
	for i, o in { { -0.13, 0.27, 0.1 }, { 0.12, 0.29, 0.14 } } do
		local d = box(b, "Drip" .. i, cx + o[1] * s, cy + o[2] * s, s * 0.065, s * o[3], c.deep, 1)
		round(d)
	end
end
DRAW.cardboard = function(b, s, c)
	local cx, cy, w = s / 2, s * 0.44, s * 0.6
	local face = box(b, "Box", cx, cy, w, w * 0.84, c.color, 2)
	round(face, math.max(1, math.floor(w * 0.06)))
	box(b, "Flap", cx, cy - w * 0.2, w, math.max(1, s * 0.025), c.deep, 3)
	box(b, "Tape", cx, cy - w * 0.08, w * 0.2, w * 0.66, c.color:Lerp(Color3.new(1, 1, 1), 0.45), 3)
end
DRAW.paperbag = function(b, s, c)
	local cx, cy, w = s / 2, s * 0.47, s * 0.52
	local bag = box(b, "Bag", cx, cy, w, w * 0.92, c.color, 2)
	round(bag, math.max(1, math.floor(w * 0.06)))
	-- the crinkled top: a row of small turned squares along its edge
	local n = 4
	for i = 1, n do
		local x = cx - w / 2 + (i - 0.5) * (w / n)
		box(b, "Crinkle" .. i, x, cy - w * 0.46, w / n * 0.72, w / n * 0.72, c.color, 2, 45)
	end
	box(b, "Fold", cx, cy - w * 0.28, w, math.max(1, s * 0.022), c.deep, 3)
end
DRAW.ducttape = function(b, s, c)
	local cx, cy, w = s / 2, s * 0.44, s * 0.58
	local tail = box(b, "Tail", cx + w * 0.28, cy + w * 0.36, w * 0.5, w * 0.2, c.color, 1, -18)
	round(tail, math.max(1, math.floor(s * 0.02)))
	local roll = box(b, "Roll", cx, cy, w, w, c.color, 2)
	round(roll)
	new("UIGradient", { Color = ColorSequence.new(c.color:Lerp(Color3.new(1, 1, 1), 0.25), c.deep), Rotation = 60 }, roll)
	local hole = box(b, "Core", cx, cy, w * 0.44, w * 0.44, CORE, 3)
	round(hole)
end
DRAW.sheetmetal = function(b, s, c)
	local cx, cy, w = s / 2, s * 0.44, s * 0.58
	local plate = box(b, "Plate", cx, cy, w, w, c.color, 2)
	round(plate, math.max(1, math.floor(w * 0.1)))
	new("UIGradient", { Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, c.deep), ColorSequenceKeypoint.new(0.45, c.color:Lerp(Color3.new(1, 1, 1), 0.35)),
		ColorSequenceKeypoint.new(1, c.deep) }), Rotation = 35 }, plate)
	for _, o in { { -1, -1 }, { 1, -1 }, { -1, 1 }, { 1, 1 } } do
		local r = box(b, "Rivet", cx + o[1] * w * 0.34, cy + o[2] * w * 0.34, s * 0.065, s * 0.065, c.deep:Lerp(CORE, 0.4), 3)
		round(r)
	end
end
DRAW.glass = function(b, s, c)
	local cx, cy, w = s / 2, s * 0.44, s * 0.6
	local frame = box(b, "Frame", cx, cy, w, w, c.deep, 2)
	round(frame, math.max(1, math.floor(w * 0.08)))
	local pane = box(b, "Pane", cx, cy, w * 0.78, w * 0.78, c.color, 3)
	round(pane, math.max(1, math.floor(w * 0.05)))
	pane.BackgroundTransparency = 0.18
	pane.ClipsDescendants = true
	-- two clean sheen lines across it
	for i, o in { { -0.12, 0.06 }, { 0.12, 0.03 } } do
		box(pane, "Sheen" .. i, w * 0.39 + o[1] * w, w * 0.39, w * o[2] + 1, w * 1.3, Color3.new(1, 1, 1), 4, 35).BackgroundTransparency = 0.35
	end
end
DRAW.duck = function(b, s, c)
	local cx, cy = s / 2, s * 0.48
	local body = box(b, "Body", cx + s * 0.03, cy + s * 0.07, s * 0.58, s * 0.36, c.color, 2)
	round(body)
	new("UIGradient", { Color = ColorSequence.new(c.color:Lerp(Color3.new(1, 1, 1), 0.2), c.deep), Rotation = 90 }, body)
	local head = box(b, "Head", cx - s * 0.12, cy - s * 0.16, s * 0.3, s * 0.3, c.color, 3)
	round(head)
	local beak = box(b, "Beak", cx - s * 0.3, cy - s * 0.13, s * 0.15, s * 0.08, Color3.fromRGB(255, 132, 40), 4)
	round(beak)
	local eye = box(b, "Eye", cx - s * 0.16, cy - s * 0.2, s * 0.05, s * 0.05, CORE, 4)
	round(eye)
	-- the top tier's crown: three small points over the head
	for i = -1, 1 do
		box(b, "Crown", cx - s * 0.12 + i * s * 0.07, cy - s * 0.33 - (if i == 0 then s * 0.02 else 0), s * 0.07, s * 0.07,
			if i == 0 then Color3.fromRGB(255, 240, 200) else c.deep, 4, 45)
	end
end

local function partyBadge(parent: Instance, s: number, v: any): Frame
	local b = new("Frame", { Name = "PartyBadge", BackgroundTransparency = 1, Size = UDim2.fromOffset(s, s) }, parent)
	if unranked(v) or placing(v) then
		-- a hollow round tile: a dash, or a dot per placement match
		local tile = box(b, "Tile", s / 2, s * 0.46, s * 0.62, s * 0.62, CORE, 1)
		round(tile, math.floor(s * 0.16))
		new("UIStroke", { Color = if unranked(v) then GREY else PALE, Thickness = math.max(1, math.floor(s * 0.04)) }, tile)
		if unranked(v) then
			local d = box(b, "Dash", s / 2, s * 0.46, s * 0.22, math.max(2, s * 0.05), GREY, 2)
			round(d)
		else
			local need = math.max(1, math.floor(tonumber(v.need) or Ranked.PLACEMENTS))
			local played = math.clamp(math.floor(tonumber(v.n) or 0), 0, need)
			local dot = math.max(3, math.floor(s * 0.07))
			for i = 1, need do
				local f = box(b, "Dot", s / 2 + (i - (need + 1) / 2) * dot * 1.6, s * 0.46, dot, dot, if i <= played then PALE else GREY, 2)
				f.BackgroundTransparency = if i <= played then 0 else 0.55
				round(f)
			end
		end
		return b
	end
	local c = PARTY[v.tier] or PARTY.napkin
	local draw = DRAW[v.tier] or DRAW.napkin
	-- the drawing is scaled up in its box so it fills it like the duels' shields fill theirs (the player-cards session:
	-- at 53 px the art was about 30 px). its centre stays at (s/2, s*0.44), or s/2 for the top tier, which has no pips
	local S = math.floor(s * 1.3)
	local cy = if v.div ~= nil then s * 0.44 else s * 0.5
	local art = new("Frame", { Name = "Art", BackgroundTransparency = 1, Size = UDim2.fromOffset(S, S),
		Position = UDim2.fromOffset(math.floor(s / 2 - S / 2), math.floor(cy - S * 0.44)) }, b)
	draw(art, S, c)
	-- the division: pips under it
	if v.div ~= nil then
		local count = math.clamp(math.floor(v.div), 1, 3)
		local dot = math.max(3, math.floor(s * 0.075))
		for i = 1, count do
			local p = box(b, "Pip", s / 2 + (i - (count + 1) / 2) * dot * 1.7, s * 0.91, dot, dot, c.color:Lerp(Color3.new(1, 1, 1), 0.3), 5)
			round(p)
		end
	end
	return b
end

function RankedStyle.label(v: any): string
	if unranked(v) then return "UNRANKED" end
	if type(v.name) == "string" and v.name ~= "" then
		-- the player card names the mode its rank is from: "GOLD II  ·  2V2"
		if v.card == true and v.placed == true and type(v.mode) == "string" then return v.name .. "  ·  " .. (if v.mode == "party" then "PARTY" else string.upper(v.mode)) end
		return v.name
	end
	return "RANKED"
end

function RankedStyle.color(v: any): Color3
	if unranked(v) then return GREY end
	if placing(v) then return PALE end
	if isParty(v) then local c = PARTY[v.tier] or PARTY.napkin; return c.color:Lerp(Color3.new(1, 1, 1), 0.15) end
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
	if isParty(v) then return partyBadge(parent, s, v) end -- (Party Ranked: the classic modes' playful ladder)
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
