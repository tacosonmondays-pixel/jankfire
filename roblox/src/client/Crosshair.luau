--!strict
-- the crosshair you design in Settings > CROSSHAIR, drawn into FightHud's Crosshair frame (first and third person:
-- the shoulder camera keeps it in the middle of the screen, TP.crosshair aims the shot at what's under it) and into
-- the page's own preview. one drawing function for both, so the preview is the crosshair.
-- options (Settings keys xh.*): style cross / dot / circle / t, colour (hex), size (line length), thickness, gap,
-- outline (0 = none), centre dot (0 = none), opacity, show spread (the gap opens with the gun's spread), hide while
-- aiming, the shotgun spread circle (below). defaults = the crosshair the game always had, with the shotgun circle
-- on.
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
-- a shape: bars ({ x, y, width, height }: each one's middle, in pixels from the crosshair's middle), a centre dot (its
-- size, 0 = none) and a ring (the radius its inner edge sits on, nil = none; ringT its line, ringK its share of the
-- opacity). the player's own crosshair is one shape (XH.own), each weapon reticle another (XH.drawFor)
export type Shape = { bars: { { number } }, dot: number, ring: number?, ringT: number?, ringK: number? }

-- each holder keeps its pieces: 8 bars, a dot, a ring and the ring's outline (built once, then only resized and
-- recoloured)
local MAX_BARS = 8
type Pieces = { bars: { Frame }, strokes: { UIStroke }, dot: Frame, dotStroke: UIStroke, ring: Frame, ringStroke: UIStroke,
	under: Frame, underStroke: UIStroke, key: string }
local built: { [Frame]: Pieces } = setmetatable({}, { __mode = "k" }) :: any

local function piece(parent: Frame, name: string): (Frame, UIStroke)
	local f = Instance.new("Frame")
	f.Name = name; f.BorderSizePixel = 0; f.AnchorPoint = Vector2.new(0.5, 0.5); f.ZIndex = 2; f.Visible = false
	local s = Instance.new("UIStroke"); s.Color = Color3.new(0, 0, 0); s.Parent = f
	f.Parent = parent
	return f, s
end
local function build(holder: Frame): Pieces
	local p = built[holder]
	if p and p.dot.Parent == holder then return p end
	for _, c in holder:GetChildren() do if c:IsA("GuiObject") then c:Destroy() end end -- (a UIScale on the holder stays)
	local bars, strokes = {}, {}
	for i = 1, MAX_BARS do
		local b, s = piece(holder, "Bar" .. i)
		table.insert(bars, b); table.insert(strokes, s)
	end
	local dot, ds = piece(holder, "Dot")
	local dc = Instance.new("UICorner"); dc.CornerRadius = UDim.new(0.5, 0); dc.Parent = dot
	local function round(name: string, z: number): (Frame, UIStroke)
		local r = Instance.new("Frame")
		r.Name = name; r.BackgroundTransparency = 1; r.AnchorPoint = Vector2.new(0.5, 0.5); r.Position = UDim2.fromScale(0.5, 0.5); r.ZIndex = z
		r.Visible = false
		local rc = Instance.new("UICorner"); rc.CornerRadius = UDim.new(0.5, 0); rc.Parent = r
		local rs = Instance.new("UIStroke"); rs.ApplyStrokeMode = Enum.ApplyStrokeMode.Border; rs.Color = Color3.new(0, 0, 0); rs.Parent = r
		r.Parent = holder
		return r, rs
	end
	local under, us = round("Under", 1) -- (the ring's outline: drawn first, under it)
	local ring, rs = round("Ring", 2)
	p = { bars = bars, strokes = strokes, dot = dot, dotStroke = ds, ring = ring, ringStroke = rs, under = under, underStroke = us, key = "" }
	built[holder] = p
	return p
end

-- the player's own crosshair as a shape: style, size, thickness, gap (+ extra px: the spread), dot
function XH.own(o: Opts, extra: number?): Shape
	local gap = o.gap + math.floor((extra or 0) + 0.5)
	local bars = {}
	if o.style == "cross" or o.style == "t" then
		local a = gap + o.size / 2 -- (each bar sits gap px out from the middle: up, down, left, right; a T has no top)
		if o.style == "cross" then table.insert(bars, { 0, -a, o.thick, o.size }) end
		table.insert(bars, { 0, a, o.thick, o.size })
		table.insert(bars, { -a, 0, o.size, o.thick })
		table.insert(bars, { a, 0, o.size, o.thick })
	end
	return { bars = bars, dot = if o.style == "dot" then (if o.dot > 0 then o.dot else 4) else o.dot,
		ring = if o.style == "circle" then gap + o.size / 2 else nil, ringT = o.thick, ringK = 1 }
end

-- draw into holder (a frame centred where the crosshair goes) the player's crosshair (extra = more gap in px), or a
-- given shape, in o's colour, outline and opacity. fade 0..1 (1 = gone). writes only what changed, so it runs every frame
function XH.draw(holder: Frame, o: Opts, fade: number, extra: any?)
	local shape: Shape = if type(extra) == "table" then extra else XH.own(o, if type(extra) == "number" then extra else 0)
	local p = build(holder)
	local live = o.alpha * (1 - math.clamp(fade, 0, 1)) -- (how much of it shows)
	local tr = 1 - live
	local outT = if o.outline > 0 then tr else 1
	local rk = shape.ringK or 1
	local parts = { o.color:ToHex(), o.outline, math.floor(tr * 100), shape.dot, shape.ring or -1, shape.ringT or 0, rk }
	for _, b in shape.bars do table.insert(parts, table.concat(b, ":")) end
	local key = table.concat(parts, ",")
	if key == p.key then return end
	p.key = key
	local ow = math.max(o.outline, 1)
	for i, f in p.bars do
		local b = shape.bars[i]
		f.Visible = b ~= nil
		if b then
			f.Size = UDim2.fromOffset(b[3], b[4])
			f.Position = UDim2.new(0.5, b[1], 0.5, b[2])
			f.BackgroundColor3 = o.color
			f.BackgroundTransparency = tr
			p.strokes[i].Thickness = ow; p.strokes[i].Transparency = outT
		end
	end
	p.dot.Visible = shape.dot > 0
	p.dot.Size = UDim2.fromOffset(shape.dot, shape.dot)
	p.dot.Position = UDim2.fromScale(0.5, 0.5)
	p.dot.BackgroundColor3 = o.color
	p.dot.BackgroundTransparency = tr
	p.dotStroke.Thickness = ow; p.dotStroke.Transparency = outT
	-- the ring: its inner edge on the radius (a Border stroke grows outward), so what it rings is inside the line
	local r = shape.ring
	local ringT = shape.ringT or o.thick
	p.ring.Visible = r ~= nil and r > 0
	if r and r > 0 then
		local dia = math.max(4, math.floor(r * 2 + 0.5))
		p.ring.Size = UDim2.fromOffset(dia, dia)
		p.ringStroke.Thickness = ringT
		p.ringStroke.Color = o.color
		p.ringStroke.Transparency = 1 - live * rk
	end
	-- (a ring can't have an outline of its own: a dark ring under it, outline px wider on both sides, does the job. a
	-- Border stroke only grows outward, so the dark one starts outline px further in)
	p.under.Visible = p.ring.Visible and o.outline > 0
	if p.under.Visible then
		local d = p.ring.Size.X.Offset - o.outline * 2
		p.under.Size = UDim2.fromOffset(d, d)
		p.underStroke.Thickness = ringT + o.outline * 2
		p.underStroke.Transparency = 1 - live * rk
	end
end

-- how many pixels a cone of `spread` covers from the middle of the screen. spread is the cone's edge as the tangent
-- of its angle, the way Hitbox.spreadDir rolls a shot (the offset across the look is up to spread), so a shot of that
-- spread lands inside this radius
function XH.spreadPx(spread: number, fovDeg: number, screenH: number): number
	if spread <= 0 then return 0 end
	return spread / math.tan(math.rad(fovDeg) / 2) * screenH / 2
end

-- ------------------------------------------------------------------ the shotgun spread circle
-- SHOTGUN SPREAD CIRCLE (xh.weapon, on by default; owner, 21 Nov: "just have the circle for the shotguns not normal
-- guns"): a shotgun (any gun that fires more than one pellet, read live from its row in Weapons.luau) shows a circle
-- on its pellet cone instead of the crosshair: Arsenal's spread now (base + bloom, x the sights' ads.spread as you
-- aim) at this FOV and zoom, so every pellet lands inside the line. it stays up, half faded, down the sights (sights
-- don't show the spread). the player's colour, outline, opacity, thickness and dot apply. every other weapon, every
-- weapon with the setting off, and a shotgun holstered in the hub (weapons-free: Arsenal, HubHolster) keep the
-- player's own crosshair
local Weapons = require(game:GetService("ReplicatedStorage"):WaitForChild("Jankfire"):WaitForChild("Weapons")) :: any
local me = game:GetService("Players").LocalPlayer

function XH.isShotgun(wid: string?): boolean
	local w = if wid then Weapons.list[wid] else nil
	return w ~= nil and w.kind == "hitscan" and (w.pellets or 1) > 1
end
-- (Arsenal's own hub rule: weapons away in the hub unless the owner's dev weapons are out)
local function holstered(): boolean
	return me ~= nil and me:GetAttribute("Zone") == "hub" and me:GetAttribute("DevArms") ~= true
end

XH.last = { class = "own", shape = nil :: Shape?, spreadPx = 0 } -- (what was drawn last: Studio tests read it)
-- the crosshair for the weapon in hand (FightHud, every frame): the shotgun's circle, or the player's own crosshair
-- (its gap opening with the spread when DYNAMIC is on). spread = Arsenal's spread now
function XH.drawFor(holder: Frame, o: Opts, fade: number, wid: string?, spread: number, cam: Camera?)
	if not cam then XH.draw(holder, o, fade, 0); return end
	local h = cam.ViewportSize.Y
	local sp = XH.spreadPx(math.max(0, spread), cam.FieldOfView, h)
	local cls, shape = "own", nil :: Shape?
	if Settings.get("xh.weapon") ~= false and XH.isShotgun(wid) and not holstered() then
		cls = "shotgun"
		shape = { bars = {}, dot = o.dot, ring = math.clamp(sp, 6, h * 0.45), ringT = o.thick, ringK = 1 }
		fade *= 0.5
	else
		shape = XH.own(o, if o.spread then math.min(60, sp) else 0)
	end
	XH.last.class = cls; XH.last.shape = shape; XH.last.spreadPx = sp
	XH.draw(holder, o, fade, shape)
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
