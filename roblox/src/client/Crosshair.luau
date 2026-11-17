--!strict
-- the crosshair you design in Settings > CROSSHAIR, drawn into FightHud's Crosshair frame (first and third person:
-- the shoulder camera keeps it in the middle of the screen, TP.crosshair aims the shot at what's under it) and into
-- the page's own preview. one drawing function for both, so the preview is the crosshair.
-- options (Settings keys xh.*): style cross / dot / circle / t, colour (hex), size (line length), thickness, gap,
-- outline (0 = none), centre dot (0 = none), opacity, show spread (the gap opens with the gun's spread), hide while
-- aiming. defaults = the crosshair the game always had.
-- a share code: "X1" + style letter + colour hex + seven base-36 digits (size, thickness, gap, outline, dot, opacity
-- in tenths, flags), 16 letters and numbers, e.g. X1CFFFFFF82510A2. nothing else in it, no links.
local Settings = require(script.Parent:WaitForChild("Settings")) :: any

local XH = {}

export type Opts = { style: string, color: Color3, size: number, thick: number, gap: number, outline: number, dot: number,
	alpha: number, spread: boolean, hideAim: boolean }

local STYLES = { cross = "C", dot = "D", circle = "O", t = "T" }
local STYLE_OF = { C = "cross", D = "dot", O = "circle", T = "t" }
XH.STYLES = { "cross", "dot", "circle", "t" }
-- the colour swatches on the page (calm, readable ones; any other through the code or the hex box)
XH.SWATCHES = { "ffffff", "7dff8a", "ffe14d", "37d6ff", "ff6ae0", "ff4b4b" }

local function num(k: string, lo: number, hi: number): number
	local v = Settings.get(k)
	return math.clamp(math.floor((if type(v) == "number" then v else Settings.DEFAULTS[k]) + 0.5), lo, hi)
end
local function hexColor(s: any): Color3
	if type(s) == "string" and string.match(s, "^%x%x%x%x%x%x$") then return Color3.fromHex(s) end
	return Color3.new(1, 1, 1)
end

-- the options as they are now
function XH.opts(): Opts
	local a = Settings.get("xh.alpha")
	return {
		style = if STYLES[Settings.get("xh.style")] then Settings.get("xh.style") else "cross",
		color = hexColor(Settings.get("xh.color")),
		size = num("xh.size", 1, 20), thick = num("xh.thick", 1, 6), gap = num("xh.gap", 0, 20),
		outline = num("xh.outline", 0, 3), dot = num("xh.dot", 0, 6),
		alpha = math.clamp(if type(a) == "number" then a else 1, 0.1, 1),
		spread = Settings.get("xh.spread") == true, hideAim = Settings.get("xh.hideAim") ~= false,
	}
end

-- ------------------------------------------------------------------ drawing
-- each holder keeps its pieces: 4 bars, a dot, a ring (built once, then only resized and recoloured)
type Pieces = { bars: { Frame }, dot: Frame, ring: Frame, ringStroke: UIStroke, under: Frame, underStroke: UIStroke, strokes: { UIStroke }, key: string }
local built: { [Frame]: Pieces } = setmetatable({}, { __mode = "k" }) :: any

local function piece(parent: Frame, name: string): (Frame, UIStroke)
	local f = Instance.new("Frame")
	f.Name = name; f.BorderSizePixel = 0; f.AnchorPoint = Vector2.new(0.5, 0.5); f.ZIndex = 2
	local s = Instance.new("UIStroke"); s.Color = Color3.new(0, 0, 0); s.Parent = f
	f.Parent = parent
	return f, s
end
local function build(holder: Frame): Pieces
	local p = built[holder]
	if p and p.dot.Parent == holder then return p end
	for _, c in holder:GetChildren() do if c:IsA("GuiObject") then c:Destroy() end end -- (a UIScale on the holder stays)
	local strokes = {}
	local bars = {}
	for i = 1, 4 do
		local b, s = piece(holder, "Bar" .. i)
		table.insert(bars, b); table.insert(strokes, s)
	end
	local dot, ds = piece(holder, "Dot")
	table.insert(strokes, ds)
	local dc = Instance.new("UICorner"); dc.CornerRadius = UDim.new(0.5, 0); dc.Parent = dot
	local function round(name: string, z: number): (Frame, UIStroke)
		local r = Instance.new("Frame")
		r.Name = name; r.BackgroundTransparency = 1; r.AnchorPoint = Vector2.new(0.5, 0.5); r.Position = UDim2.fromScale(0.5, 0.5); r.ZIndex = z
		local rc = Instance.new("UICorner"); rc.CornerRadius = UDim.new(0.5, 0); rc.Parent = r
		local rs = Instance.new("UIStroke"); rs.ApplyStrokeMode = Enum.ApplyStrokeMode.Border; rs.Color = Color3.new(0, 0, 0); rs.Parent = r
		r.Parent = holder
		return r, rs
	end
	local under, us = round("Under", 1) -- (the ring's outline: drawn first, under it)
	local ring, rs = round("Ring", 2)
	p = { bars = bars, dot = dot, ring = ring, ringStroke = rs, under = under, underStroke = us, strokes = strokes, key = "" }
	built[holder] = p
	return p
end

-- draw o into holder (a frame centred where the crosshair goes). fade 0..1 (1 = gone), extra = more gap in pixels
-- (the spread). writes only what changed, so it can run every frame
function XH.draw(holder: Frame, o: Opts, fade: number, extra: number?)
	local p = build(holder)
	local gap = o.gap + math.floor((extra or 0) + 0.5)
	local tr = 1 - o.alpha * (1 - math.clamp(fade, 0, 1))
	local key = table.concat({ o.style, o.color:ToHex(), o.size, o.thick, gap, o.outline, o.dot, math.floor(tr * 100) }, ",")
	if key == p.key then return end
	p.key = key
	local lines = o.style == "cross" or o.style == "t"
	local outT = if o.outline > 0 then tr else 1
	-- the bars: up, down, left, right (a T has no top). each sits gap px out from the middle
	local dirs = { Vector2.new(0, -1), Vector2.new(0, 1), Vector2.new(-1, 0), Vector2.new(1, 0) }
	for i, b in p.bars do
		local d = dirs[i]
		local show = lines and not (o.style == "t" and i == 1)
		b.Visible = show
		if show then
			local along = gap + o.size / 2
			b.Size = if d.X == 0 then UDim2.fromOffset(o.thick, o.size) else UDim2.fromOffset(o.size, o.thick)
			-- (odd thickness: half a pixel off so the bar lands on whole pixels)
			b.Position = UDim2.new(0.5, d.X * along, 0.5, d.Y * along)
			b.BackgroundColor3 = o.color
			b.BackgroundTransparency = tr
		end
		local s = p.strokes[i]
		s.Thickness = math.max(o.outline, 1); s.Transparency = outT
	end
	-- the dot: the centre dot, or the whole crosshair in the dot style
	local dotSize = if o.style == "dot" then (if o.dot > 0 then o.dot else 4) else o.dot
	p.dot.Visible = dotSize > 0
	p.dot.Size = UDim2.fromOffset(dotSize, dotSize)
	p.dot.Position = UDim2.fromScale(0.5, 0.5)
	p.dot.BackgroundColor3 = o.color
	p.dot.BackgroundTransparency = tr
	local ds = p.strokes[5]
	ds.Thickness = math.max(o.outline, 1); ds.Transparency = outT
	-- the ring: its line on the gap + half the size, thickness = the line thickness
	local circle = o.style == "circle"
	p.ring.Visible = circle
	if circle then
		local r = gap + o.size / 2
		local dia = math.max(4, math.floor(r * 2 + 0.5))
		p.ring.Size = UDim2.fromOffset(dia, dia)
		p.ringStroke.Thickness = o.thick
		p.ringStroke.Color = o.color
		p.ringStroke.Transparency = tr
	end
	-- (a ring can't have an outline of its own: a dark ring under it, outline px wider on both sides, does the job.
	-- a Border stroke only grows outward, so the dark one starts outline px further in)
	p.under.Visible = circle and o.outline > 0
	if p.under.Visible then
		local d = p.ring.Size.X.Offset - o.outline * 2
		p.under.Size = UDim2.fromOffset(d, d)
		p.underStroke.Thickness = o.thick + o.outline * 2
		p.underStroke.Transparency = outT
	end
end

-- how many pixels a cone of `spread` (radians, the half-angle the shots land in) covers at the middle of the screen
function XH.spreadPx(spread: number, fovDeg: number, screenH: number): number
	if spread <= 0 then return 0 end
	return math.tan(spread) / math.tan(math.rad(fovDeg) / 2) * screenH / 2
end

-- ------------------------------------------------------------------ share codes
local B36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
local function d36(n: number): string
	n = math.clamp(math.floor(n), 0, 35)
	return string.sub(B36, n + 1, n + 1)
end
local function n36(c: string): number?
	local i = string.find(B36, c, 1, true)
	return if i then i - 1 else nil
end
function XH.encode(o: Opts?): string
	local x = o or XH.opts()
	local flags = (if x.spread then 1 else 0) + (if x.hideAim then 2 else 0)
	return "X1" .. STYLES[x.style] .. string.upper(x.color:ToHex()) .. d36(x.size) .. d36(x.thick) .. d36(x.gap)
		.. d36(x.outline) .. d36(x.dot) .. d36(math.floor(x.alpha * 10 + 0.5)) .. d36(flags)
end
-- a code back to settings values (a table of key -> value), or nil and why
function XH.decode(code: string): ({ [string]: any }?, string?)
	local s = string.upper((string.gsub(code, "[^%w]", "")))
	if #s ~= 16 or string.sub(s, 1, 2) ~= "X1" then return nil, "not a crosshair code" end
	local style = STYLE_OF[string.sub(s, 3, 3)]
	local hex = string.sub(s, 4, 9)
	if not style or not string.match(hex, "^%x%x%x%x%x%x$") then return nil, "not a crosshair code" end
	local v = {}
	for i = 10, 16 do
		local n = n36(string.sub(s, i, i))
		if not n then return nil, "not a crosshair code" end
		v[i - 9] = n
	end
	local size, thick, gap, outline, dot, alpha, flags = v[1], v[2], v[3], v[4], v[5], v[6], v[7]
	if size < 1 or size > 20 or thick < 1 or thick > 6 or gap > 20 or outline > 3 or dot > 6 or alpha < 1 or alpha > 10 or flags > 3 then
		return nil, "a number in it is out of range"
	end
	return {
		["xh.style"] = style, ["xh.color"] = string.lower(hex), ["xh.size"] = size, ["xh.thick"] = thick, ["xh.gap"] = gap,
		["xh.outline"] = outline, ["xh.dot"] = dot, ["xh.alpha"] = alpha / 10, ["xh.spread"] = flags % 2 == 1,
		["xh.hideAim"] = flags >= 2,
	}, nil
end
function XH.apply(code: string): (boolean, string?)
	local t, why = XH.decode(code)
	if not t then return false, why end
	for k, val in t do Settings.set(k, val) end
	return true, nil
end

return XH
