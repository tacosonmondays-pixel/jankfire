--!strict
-- XP, level and rank. the level is the web game's, exactly (server/accounts.js levelOf / xpForLevel: no cap) and so is
-- the XP that counts on roblox (server/room.js): a kill on a player +20, a round won +50, 2 a minute of match time.
-- the hub and the training hall give nothing (the web lobby and training mode don't). the web game has no rank, so
-- the rank is ours: eight tiers over the levels, three divisions each (III, then II, then I), and the top tier shows
-- the level instead. its badge is drawn from frames (no pictures): a diamond in the tier's colour, a ring from Silver,
-- wings from Platinum, a crest from Master. the server keeps only the XP; everything else is worked out from it.
local Ranks = {}

Ranks.XP = { kill = 20, roundWin = 50, perMinute = 2 }

function Ranks.levelOf(xp: number): number
	return math.floor(math.sqrt(math.max(0, xp) / 40)) + 1
end
function Ranks.xpForLevel(l: number): number
	return (l - 1) * (l - 1) * 40
end

export type Tier = { id: string, name: string, from: number, color: Color3, deep: Color3 }
-- from = the first level of the tier. colours are metals, quiet: the badge is the only colour on a card's header
Ranks.TIERS = {
	{ id = "iron", name = "IRON", from = 1, color = Color3.fromRGB(138, 144, 152), deep = Color3.fromRGB(70, 74, 82) },
	{ id = "bronze", name = "BRONZE", from = 5, color = Color3.fromRGB(196, 136, 92), deep = Color3.fromRGB(98, 62, 40) },
	{ id = "silver", name = "SILVER", from = 10, color = Color3.fromRGB(206, 212, 220), deep = Color3.fromRGB(104, 110, 122) },
	{ id = "gold", name = "GOLD", from = 15, color = Color3.fromRGB(236, 190, 78), deep = Color3.fromRGB(128, 92, 26) },
	{ id = "platinum", name = "PLATINUM", from = 22, color = Color3.fromRGB(126, 210, 200), deep = Color3.fromRGB(38, 102, 98) },
	{ id = "diamond", name = "DIAMOND", from = 30, color = Color3.fromRGB(128, 178, 246), deep = Color3.fromRGB(40, 74, 136) },
	{ id = "master", name = "MASTER", from = 40, color = Color3.fromRGB(184, 140, 238), deep = Color3.fromRGB(78, 48, 128) },
	{ id = "apex", name = "APEX", from = 55, color = Color3.fromRGB(246, 236, 214), deep = Color3.fromRGB(150, 112, 50) },
} :: { Tier }
Ranks.DIVS = { "III", "II", "I" }

export type Rank = {
	xp: number, level: number, tier: Tier, tierIndex: number, div: number?, name: string,
	into: number, need: number, progress: number, -- XP into this level, XP this level takes, 0..1
}

function Ranks.of(xp: number?): Rank
	local x = math.max(0, math.floor(tonumber(xp) or 0))
	local level = Ranks.levelOf(x)
	local ti = 1
	for i, t in Ranks.TIERS do if level >= t.from then ti = i end end
	local tier = Ranks.TIERS[ti]
	local nextFrom = if Ranks.TIERS[ti + 1] then Ranks.TIERS[ti + 1].from else nil
	local div: number? = nil
	local name: string
	if nextFrom then
		local width = nextFrom - tier.from
		div = math.min(3, math.floor((level - tier.from) * 3 / width) + 1)
		name = tier.name .. " " .. Ranks.DIVS[div :: number]
	else
		name = tier.name .. " " .. level
	end
	local lo, hi = Ranks.xpForLevel(level), Ranks.xpForLevel(level + 1)
	return {
		xp = x, level = level, tier = tier, tierIndex = ti, div = div, name = name,
		into = x - lo, need = hi - lo, progress = math.clamp((x - lo) / math.max(1, hi - lo), 0, 1),
	}
end

-- ------------------------------------------------------------------ the badge (clients only: it makes GUI objects)
local function new(class: string, props: { [string]: any }, parent: Instance?): any
	local o = Instance.new(class)
	for k, v in props do (o :: any)[k] = v end
	if parent then o.Parent = parent end
	return o
end
local function grad(o: Instance, a: Color3, b: Color3, rot: number)
	new("UIGradient", { Color = ColorSequence.new(a, b), Rotation = rot }, o)
end

-- a square frame `size` px across holding the badge for this rank; put it where you like (AnchorPoint is yours)
function Ranks.badge(parent: Instance, size: number, r: Rank): Frame
	local t = r.tier
	local ti = r.tierIndex
	local box = new("Frame", { Name = "RankBadge", BackgroundTransparency = 1, Size = UDim2.fromOffset(size, size) }, parent)
	local s = size
	local light = t.color:Lerp(Color3.new(1, 1, 1), 0.35)
	-- wings (Platinum up): two slim blades behind the diamond
	if ti >= 5 then
		for _, side in { -1, 1 } do
			local w = new("Frame", { Name = "Wing", AnchorPoint = Vector2.new(0.5, 0.5), BorderSizePixel = 0, BackgroundColor3 = t.color,
				Position = UDim2.fromScale(0.5 + side * 0.3, 0.56), Size = UDim2.fromOffset(math.floor(s * 0.36), math.max(2, math.floor(s * 0.1))),
				Rotation = side * -28 }, box)
			new("UICorner", { CornerRadius = UDim.new(1, 0) }, w)
			grad(w, t.deep, t.color, if side < 0 then 180 else 0)
			if ti >= 6 then
				local w2 = w:Clone()
				w2.Position = UDim2.fromScale(0.5 + side * 0.27, 0.7)
				w2.Size = UDim2.fromOffset(math.floor(s * 0.28), math.max(2, math.floor(s * 0.08)))
				w2.Rotation = side * -14
				w2.Parent = box
			end
		end
	end
	-- crest (Master up): a small diamond over the top point
	if ti >= 7 then
		local c = new("Frame", { Name = "Crest", AnchorPoint = Vector2.new(0.5, 0.5), BorderSizePixel = 0, BackgroundColor3 = light,
			Position = UDim2.fromScale(0.5, 0.1), Size = UDim2.fromOffset(math.floor(s * 0.16), math.floor(s * 0.16)), Rotation = 45, ZIndex = 3 }, box)
		new("UICorner", { CornerRadius = UDim.new(0, math.max(1, math.floor(s * 0.02))) }, c)
	end
	-- ring (Silver up): a thin diamond outline round the body
	if ti >= 3 then
		local ring = new("Frame", { Name = "Ring", AnchorPoint = Vector2.new(0.5, 0.5), BackgroundTransparency = 1, Position = UDim2.fromScale(0.5, 0.52),
			Size = UDim2.fromOffset(math.floor(s * 0.6), math.floor(s * 0.6)), Rotation = 45, ZIndex = 1 }, box)
		new("UICorner", { CornerRadius = UDim.new(0, math.max(2, math.floor(s * 0.06))) }, ring)
		new("UIStroke", { Color = t.color, Thickness = math.max(1, math.floor(s * 0.03)), Transparency = 0.15 }, ring)
	end
	-- the body: a diamond with a lit top edge, and a dark core
	local body = new("Frame", { Name = "Body", AnchorPoint = Vector2.new(0.5, 0.5), BorderSizePixel = 0, BackgroundColor3 = Color3.new(1, 1, 1),
		Position = UDim2.fromScale(0.5, 0.52), Size = UDim2.fromOffset(math.floor(s * 0.46), math.floor(s * 0.46)), Rotation = 45, ZIndex = 2 }, box)
	new("UICorner", { CornerRadius = UDim.new(0, math.max(2, math.floor(s * 0.05))) }, body)
	grad(body, light, t.deep, 45)
	local core = new("Frame", { Name = "Core", AnchorPoint = Vector2.new(0.5, 0.5), BorderSizePixel = 0, BackgroundColor3 = Color3.fromRGB(18, 20, 24),
		Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromScale(0.58, 0.58), ZIndex = 3 }, body)
	new("UICorner", { CornerRadius = UDim.new(0, math.max(1, math.floor(s * 0.03))) }, core)
	-- the division: 1 to 3 short upright bars in the core (I = three), the top tier a single bright bar
	local bars = if r.div then (r.div :: number) else 3
	local holder = new("Frame", { Name = "Div", AnchorPoint = Vector2.new(0.5, 0.5), BackgroundTransparency = 1, Position = UDim2.fromScale(0.5, 0.52),
		Size = UDim2.fromOffset(math.floor(s * 0.26), math.floor(s * 0.16)), ZIndex = 5 }, box)
	new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, HorizontalAlignment = Enum.HorizontalAlignment.Center,
		VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, math.max(1, math.floor(s * 0.03))) }, holder)
	for _ = 1, bars do
		local b = new("Frame", { BorderSizePixel = 0, BackgroundColor3 = light, Size = UDim2.fromOffset(math.max(2, math.floor(s * 0.045)), math.floor(s * 0.15)), ZIndex = 5 }, holder)
		new("UICorner", { CornerRadius = UDim.new(1, 0) }, b)
	end
	return box
end

return Ranks
