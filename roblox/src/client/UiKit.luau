--!strict
-- THE NEW UI's parts (27 Nov 2026). The owner picked from the ui-mocks sheet (roblox/docs/ui-mocks, side-session-notes
-- ui_mocks_OWNER_PICKS_27nov.webp):
--   A PLATE      the hub menu, the match HUD, the shop, the phone: built from the hub's own kit. Bone panels, flat and
--                near-square; only what you buy gets the queue pads' lip; ink is the action colour; a stencil slit
--                through every hero number
--   B BROADCAST  the Tab scoreboard, and the loadout's colours (the loadout is A's layout in B's colours): black slabs,
--                white for "selected / you", a cut corner on what is yours, a skew on what you press, Butter only on
--                what you can press now
-- Every screen takes its colours, fonts and shapes from here, so the two looks stay one system. Team colours stay
-- Shared.TeamColors'. Roblox fonts only (Builder Sans, Oswald).
--   K.A / K.B             the two palettes
--   K.tri(...)            a right triangle (a hard UIGradient step on a square: no images, no rotation, clips fine)
--   K.cut(frame, s, col)  cut a frame's corner (paints the triangle in the colour behind it)
--   K.skew(...)           a parallelogram (a rect with a triangle each side): the press shape
--   K.slit(label)         A's stencil slit through a hero number (a UIGradient transparency band)
--   K.heads(uid)          a Roblox head-shot image for a user id ("" for a stand-in)
local K = {}

local function face(family: string, weight: Enum.FontWeight): Font
	return Font.new("rbxasset://fonts/families/" .. family .. ".json", weight)
end
K.SANS = face("BuilderSans", Enum.FontWeight.Medium)
K.SANS_BOLD = face("BuilderSans", Enum.FontWeight.Bold)
K.SANS_HEAVY = face("BuilderSans", Enum.FontWeight.ExtraBold)
K.COND = face("Oswald", Enum.FontWeight.Bold) -- B's names and big numbers
K.COND_REG = face("Oswald", Enum.FontWeight.Regular)

local rgb = Color3.fromRGB
-- A PLATE: bone, its lip and ink (the hub kit's light panels and the queue pads' dark centre)
K.A = {
	BONE = rgb(229, 226, 219),
	BONE2 = rgb(212, 208, 199), -- a track, a pressed key
	LIP = rgb(170, 164, 152), -- the pads' lip under what you buy
	INK = rgb(29, 31, 35), -- the action colour, and text on bone
	INK2 = rgb(86, 83, 77), -- second-rank words on bone
	TICK = rgb(176, 99, 47), -- the stat bars' "secondary average" tick
	WORLD = rgb(255, 255, 255), -- text straight on the world
}
-- B BROADCAST: the slab, white for "selected / you", Butter for "press this"
K.B = {
	SLAB = rgb(13, 14, 16),
	SLAB_A = 0.06, -- (a slab is nearly solid: the cut corner paints the same colour)
	SLAB2 = rgb(22, 24, 27), -- a header strip, a hovered row
	LINE = rgb(34, 36, 41), -- the hairline between rows
	WHITE = rgb(242, 241, 238), -- the selected row / your row
	INK = rgb(16, 17, 19), -- text on white or Butter
	TEXT = rgb(240, 240, 236),
	MUTED = rgb(150, 152, 156),
	DIM = rgb(92, 94, 99),
	BUTTER = rgb(245, 221, 138), -- press this (and the party bracket)
	SHORT = rgb(232, 150, 92), -- "need X more"
	DANGER = rgb(235, 96, 86),
}

function K.new(class: string, props: { [string]: any }, parent: Instance?): any
	local o = Instance.new(class)
	for k, v in props do (o :: any)[k] = v end
	if parent then o.Parent = parent end
	return o
end

function K.text(parent: Instance, name: string, text: string, size: number, color: Color3, font: Font, align: Enum.TextXAlignment?): TextLabel
	return K.new("TextLabel", {
		Name = name, BackgroundTransparency = 1, FontFace = font, TextSize = size, Text = text, TextColor3 = color,
		TextXAlignment = align or Enum.TextXAlignment.Left, TextYAlignment = Enum.TextYAlignment.Center,
	}, parent)
end

local ANGLE = { tr = -45, br = 45, bl = 135, tl = -135 }
-- a right triangle filling the half of a w x h box that holds `corner` ("tl", "tr", "bl", "br")
function K.tri(parent: Instance, pos: UDim2, w: number, h: number, color: Color3, corner: string, alpha: number?, z: number?): Frame
	local f = K.new("Frame", {
		Name = "Tri", BackgroundColor3 = color, BackgroundTransparency = alpha or 0, BorderSizePixel = 0, Position = pos,
		Size = UDim2.fromOffset(w, h), ZIndex = z or 1,
	}, parent)
	-- (the step's direction runs corner to corner; on a box that isn't square the diagonal still splits it in two)
	local ang = ANGLE[corner] or -45
	if w ~= h then
		local a = math.deg(math.atan2(h, w))
		ang = if corner == "tr" then -a elseif corner == "br" then a elseif corner == "bl" then 180 - a else -(180 - a)
	end
	K.new("UIGradient", {
		Rotation = ang,
		Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 1),
			NumberSequenceKeypoint.new(0.502, 0), NumberSequenceKeypoint.new(1, 0),
		}),
	}, f)
	return f
end

-- cut one corner of `frame` (default the top right): a triangle in `behind`, the colour of what's under the frame
function K.cut(frame: GuiObject, s: number, behind: Color3, corner: string?, alpha: number?): Frame
	local c = corner or "tr"
	local x = if c == "tr" or c == "br" then UDim.new(1, -s) else UDim.new(0, 0)
	local y = if c == "br" or c == "bl" then UDim.new(1, -s) else UDim.new(0, 0)
	local t = K.tri(frame, UDim2.new(x, y), s, s, behind, c, alpha, frame.ZIndex + 1)
	t.Name = "Cut"
	return t
end

-- a parallelogram leaning right ("/"), `skew` px of lean, as one holder: its centre rect is .Face (put text there)
function K.skew(parent: Instance, pos: UDim2, w: number, h: number, color: Color3, skew: number?, z: number?): Frame
	local k = skew or math.floor(h * 0.32)
	local holder = K.new("Frame", { Name = "Skew", BackgroundTransparency = 1, Position = pos, Size = UDim2.fromOffset(w, h), ZIndex = z or 1 }, parent)
	local faceF = K.new("Frame", {
		Name = "Face", BackgroundColor3 = color, BorderSizePixel = 0, Position = UDim2.fromOffset(k, 0),
		Size = UDim2.fromOffset(w - 2 * k, h), ZIndex = z or 1,
	}, holder)
	K.tri(holder, UDim2.fromOffset(0, 0), k, h, color, "br", nil, z)
	K.tri(holder, UDim2.fromOffset(w - k, 0), k, h, color, "tl", nil, z)
	return holder
end
-- recolour a skew made above
function K.skewColor(holder: Instance, color: Color3)
	for _, c in holder:GetChildren() do
		if c:IsA("Frame") then c.BackgroundColor3 = color end
	end
end

-- A's stencil slit: a thin transparent band a little under the middle of a hero number (PLAY, HP, ammo, scores)
function K.slit(label: TextLabel, at: number?, width: number?)
	local a = at or 0.53
	local w = width or 0.06
	K.new("UIGradient", {
		Name = "Slit", Rotation = 90,
		Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(a, 0), NumberSequenceKeypoint.new(a + 0.002, 1),
			NumberSequenceKeypoint.new(a + w, 1), NumberSequenceKeypoint.new(a + w + 0.002, 0), NumberSequenceKeypoint.new(1, 0),
		}),
	}, label)
end

-- A's hero number straight on the world: the number with a soft drop shadow, both cut by the slit. sized to its text
-- (AutomaticSize X); `shadow` false for a number on a tile. returns the holder, the label and a setter
function K.hero(parent: Instance, name: string, size: number, font: Font, color: Color3, shadow: boolean?, slit: boolean?): (Frame, TextLabel, (string, Color3?) -> ())
	local h = K.new("Frame", { Name = name, BackgroundTransparency = 1, AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, size) }, parent)
	local sh: TextLabel? = nil
	if shadow ~= false then
		local s = K.text(h, "Shadow", "", size, Color3.new(0, 0, 0), font)
		s.AutomaticSize = Enum.AutomaticSize.X; s.Size = UDim2.fromOffset(0, size)
		s.Position = UDim2.fromOffset(0, math.max(1, math.floor(size / 28 + 0.5))); s.TextTransparency = 0.6
		if slit ~= false then K.slit(s) end
		sh = s
	end
	local l = K.text(h, "Value", "", size, color, font)
	l.AutomaticSize = Enum.AutomaticSize.X; l.Size = UDim2.fromOffset(0, size)
	if slit ~= false then K.slit(l) end
	local function set(t: string, c: Color3?)
		if l.Text ~= t then l.Text = t; if sh then sh.Text = t end end
		if c and l.TextColor3 ~= c then l.TextColor3 = c end
	end
	return h, l, set
end

-- the all-B alternative (27 Nov, main's ask: the A screens in B's colours, to show the owner side by side): while
-- ReplicatedStorage's attribute UiLook is "B", themeA() hands out B's slabs (Butter for the one button that does
-- something), the hub's PLAY is a Butter slab and the HUD's big numbers are Oswald. read when a screen is built
function K.alt(): boolean
	return game:GetService("ReplicatedStorage"):GetAttribute("UiLook") == "B"
end
local themeBPress: any = nil
-- Theme in A's colours, for a menu that should sit light on the game (the shop, the hub's menus): bone plates and cards,
-- ink words, ink for the one button that does something (its words bone), near-square corners, no hairlines. a menu
-- swaps its `local T = require(Theme)` for this and every T.* read and T.plate / T.text / T.key follows
local themeA: any = nil
function K.themeA(): any
	if K.alt() then
		if themeBPress then return themeBPress end
		local base = K.themeB()
		local P: any = { ACCENT = K.B.BUTTER, INK = K.B.INK, MARK = K.B.BUTTER }
		themeBPress = setmetatable(P, { __index = base })
		return themeBPress
	end
	if themeA then return themeA end
	local Theme = require(script.Parent:WaitForChild("Theme")) :: any
	local c = Color3.fromRGB
	local P: any = {
		BG = c(212, 208, 199), BG_A = 0.02, CARD = c(229, 226, 219), CARD_HI = c(240, 238, 233), TRACK = c(196, 191, 181),
		EDGE = c(0, 0, 0), EDGE_A = 0.9, TEXT = c(29, 31, 35), MUTED = c(86, 83, 77), SOFT = c(64, 62, 58), DIM = c(140, 136, 128),
		ACCENT = c(29, 31, 35), INK = c(229, 226, 219), DANGER = c(196, 64, 56), RADIUS = 3,
		-- (one family in A: Builder Sans. Theme's wide Builder Extended titles read as a third face next to it)
		FONT_TITLE = Theme.FONT_HEAVY, FONT_SHOUT = Theme.FONT_HEAVY, MARK = c(229, 226, 219),
	}
	P.corner = function(o: Instance, r: number?): UICorner return Theme.corner(o, if r and r >= 20 then r else 3) end
	P.edge = function(o: Instance, color: Color3?, alpha: number?, thick: number?): UIStroke
		return Theme.edge(o, color or P.EDGE, alpha or P.EDGE_A, thick)
	end
	P.text = function(parent: Instance, name: string, text: string, size: number, color: Color3?, font: Font?, align: Enum.TextXAlignment?, shadow: boolean?): TextLabel
		return Theme.text(parent, name, text, size, color or P.TEXT, font, align, shadow)
	end
	P.plate = function(parent: Instance, name: string, pos: UDim2, size: UDim2): Frame
		local f = Theme.new("Frame", { Name = name, BackgroundColor3 = P.BG, BackgroundTransparency = P.BG_A, BorderSizePixel = 0, Position = pos, Size = size }, parent)
		P.corner(f)
		Theme.edge(f, P.EDGE, 1) -- (kept, invisible: code that finds a plate's stroke still finds one)
		return f
	end
	P.key = function(parent: Instance, letter: string, pos: UDim2): Frame
		local f = Theme.key(parent, letter, pos)
		f.BackgroundColor3 = P.TRACK
		local st = f:FindFirstChildOfClass("UIStroke")
		if st then st.Transparency = 1 end
		local l = f:FindFirstChild("Letter") :: TextLabel?
		if l then l.TextColor3 = P.TEXT end
		return f
	end
	themeA = setmetatable(P, { __index = Theme })
	return themeA
end

-- Theme in B's colours, for a dark menu that belongs with the loadout (the between-rounds picker): black slabs, square
-- corners, no hairlines, white for what's chosen (ACCENT is white here), Oswald titles. Butter, B's "press this", is
-- the caller's own (K.B.BUTTER) on the one button that does something
local themeB: any = nil
function K.themeB(): any
	if themeB then return themeB end
	local Theme = require(script.Parent:WaitForChild("Theme")) :: any
	local c = Color3.fromRGB
	local P: any = {
		BG = K.B.SLAB, BG_A = K.B.SLAB_A, CARD = c(24, 26, 30), CARD_HI = c(40, 42, 48), TRACK = c(44, 46, 52),
		EDGE = c(255, 255, 255), EDGE_A = 1, TEXT = K.B.TEXT, MUTED = K.B.MUTED, SOFT = c(200, 200, 196), DIM = K.B.DIM,
		ACCENT = K.B.WHITE, INK = K.B.INK, DANGER = K.B.DANGER, RADIUS = 0, FONT_TITLE = K.COND, FONT_SHOUT = K.COND,
	}
	P.corner = function(o: Instance, r: number?): UICorner return Theme.corner(o, if r and r >= 20 then r else 0) end
	P.edge = function(o: Instance, color: Color3?, alpha: number?, thick: number?): UIStroke
		return Theme.edge(o, color or P.EDGE, alpha or P.EDGE_A, thick)
	end
	P.text = function(parent: Instance, name: string, text: string, size: number, color: Color3?, font: Font?, align: Enum.TextXAlignment?, shadow: boolean?): TextLabel
		return Theme.text(parent, name, text, size, color or P.TEXT, font, align, shadow)
	end
	P.plate = function(parent: Instance, name: string, pos: UDim2, size: UDim2): Frame
		local f = Theme.new("Frame", { Name = name, BackgroundColor3 = P.BG, BackgroundTransparency = P.BG_A, BorderSizePixel = 0, Position = pos, Size = size }, parent)
		Theme.edge(f, P.EDGE, 1) -- (kept, invisible: code that finds a plate's stroke still finds one)
		return f
	end
	themeB = setmetatable(P, { __index = Theme })
	return themeB
end

-- a padlock drawn flat (a shackle and a body), one colour: the emoji one read as another icon family
function K.lock(parent: Instance, s: number, color: Color3, z: number?): Frame
	local f = K.new("Frame", { Name = "Padlock", BackgroundTransparency = 1, Size = UDim2.fromOffset(s, s), ZIndex = z or 1 }, parent)
	local sh = K.new("Frame", { Name = "Shackle", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromScale(0.5, 0.04),
		Size = UDim2.fromScale(0.56, 0.6), ZIndex = z or 1 }, f)
	K.new("UICorner", { CornerRadius = UDim.new(0.5, 0) }, sh)
	K.new("UIStroke", { Color = color, Thickness = math.max(1.5, s / 9) }, sh)
	local body = K.new("Frame", { Name = "Body", BackgroundColor3 = color, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.fromScale(0.5, 1),
		Size = UDim2.fromScale(0.82, 0.56), ZIndex = (z or 1) + 1 }, f)
	K.new("UICorner", { CornerRadius = UDim.new(0, math.max(1, math.floor(s / 8))) }, body)
	return f
end

function K.head(uid: number?): string
	if type(uid) == "number" and uid > 0 then return ("rbxthumb://type=AvatarHeadShot&id=%d&w=48&h=48"):format(uid) end
	return ""
end

-- "m:ss" for a count of seconds
function K.clock(s: number): string
	local n = math.max(0, math.floor(s + 0.5))
	return ("%d:%02d"):format(n // 60, n % 60)
end

-- a column label in sentence case: "DMG" -> "Dmg", "K" stays "K"
function K.sentence(s: string): string
	if #s <= 1 then return s end
	return string.upper(string.sub(s, 1, 1)) .. string.lower(string.sub(s, 2))
end

return K
