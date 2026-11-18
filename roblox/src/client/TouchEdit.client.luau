--!strict
-- The touch layout editor (the owner, 18 Nov: "ui on mobile is a bit clunky, can you add a custom ui like remapping and
-- a button resizer for mobile players, and they can move buttons where they want"). Opened from Settings (TOUCH LAYOUT
-- at the top of CONTROLS on a phone, and of TOUCH) through the player attribute TouchEditOpen = true.
--   * the screen dims and every touch thing shows where it is: the buttons, the move stick, the top row (EMOTE, AUTO,
--     SETTINGS) and the HUD's WEAPON and HEALTH boxes. drag one to move it: it snaps to a light 8-point grid and stays
--     inside the safe area, clear of Roblox's own buttons (top left)
--   * tap one for its panel: SIZE (60-160 %), OPACITY (20-100 % of the TOUCH tab's BUTTON OPACITY), ACTION (a button:
--     what it presses, from TouchLayout.PICK; the katana's WAVE and the grapple's YANK keep theirs), HIDE (all but
--     SETTINGS, the stick and the boxes), the stick FLOATING (where your thumb lands) or FIXED, REMOVE (an added one)
--   * ADD BUTTON puts an extra button (up to 6) for any action; LAYOUT 1-3 are three saved layouts, the one shown when
--     you SAVE is the one used; RESET puts the shown one back to the default; CANCEL leaves without saving
--   * it only edits TouchLayout's records; TouchControls draws the game's buttons from the saved layout (TouchLayout
--     .changed), and hides its own while this is open
-- Test hook (Studio): player attribute TouchEditTest: "open", "slot:<1-3>", "select:<id>", "move:<id>,<x>,<y>" (the
-- middle, in the safe area's points), "size:<id>,<pct>", "alpha:<id>,<pct>", "act:<id>,<action>", "hide:<id>",
-- "show:<id>", "add:<action>", "remove:<id>", "stick:fixed|float", "pick:act|add|none", "reset", "save", "cancel",
-- "state" (writes TouchEditState as JSON). Drags with the mouse work too (a Studio test with TouchForce)
local Players = game:GetService("Players")
local UIS = game:GetService("UserInputService")
local RunService = game:GetService("RunService")
local HttpService = game:GetService("HttpService")

local T = require(script.Parent:WaitForChild("Theme"))
local TL = require(script.Parent:WaitForChild("TouchLayout"))
local Settings = require(script.Parent:WaitForChild("Settings"))
local okMC, MenuCursor = pcall(function() return require(script.Parent:WaitForChild("MenuCursor", 10) :: ModuleScript) :: any end)

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")
local MB1 = Enum.UserInputType.MouseButton1
local TOUCH = Enum.UserInputType.Touch
local GRID = 8 -- snap (points); the drawn grid is every 16

-- ------------------------------------------------------------------ state
local E = {
	open = false,
	slot = 1,
	work = {} :: { [number]: { any } }, -- the three layouts being edited
	dirty = {} :: { [number]: boolean },
	sel = nil :: string?, -- the selected thing's id
	pick = nil :: string?, -- "act" (the selected button's action) | "add" (a new button) | nil
	drag = nil :: any, -- { id, key, off: Vector2 }
	slide = nil :: any, -- { key, track: Frame, set: (number) -> () }
}

local function items(): { any } return E.work[E.slot] end
local function rec(id: string?): any
	if not id then return nil end
	for _, r in items() do if r.id == id then return r end end
	return nil
end

-- the same numbers TouchControls places with (its S.size, the HUD's scale, the mirror)
local function areaSize(): Vector2
	local f = me:GetAttribute("FakeScreen")
	if typeof(f) == "Vector2" then return f end
	local cam = workspace.CurrentCamera
	return if cam then cam.ViewportSize else Vector2.new(844, 390)
end
local function tsNow(): number
	local v = areaSize()
	local tab = math.min(v.X, v.Y) >= 600
	return math.clamp((tonumber(Settings.get("touch.size")) or 1) * (if tab then 1.2 else 1), 0.6, 1.7)
end
local function sdNow(): number
	local g = pg:FindFirstChild("JankfireFight")
	local u = g and g:FindFirstChild("Scaled") and (g :: any).Scaled:FindFirstChildOfClass("UIScale")
	return if u then u.Scale else T.scaleNow() * T.hudScale
end
local function lefty(): boolean return Settings.get("touch.lefty") == true end
local function alphaNow(): number return math.clamp(tonumber(Settings.get("touch.alpha")) or 0.75, 0.15, 1) end

-- ------------------------------------------------------------------ the screen
local back = T.new("ScreenGui", { Name = "JankTouchEditBack", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 79, Enabled = false }, pg) :: ScreenGui
back.ScreenInsets = Enum.ScreenInsets.None
local dim = T.new("TextButton", { Name = "Dim", Text = "", AutoButtonColor = false, BackgroundColor3 = Color3.new(0, 0, 0),
	BackgroundTransparency = 0.45, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), Selectable = false }, back) :: TextButton
local gui = T.new("ScreenGui", { Name = "JankTouchEdit", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 80, Enabled = false,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, pg) :: ScreenGui
gui.ScreenInsets = Enum.ScreenInsets.DeviceSafeInsets -- (the same safe area as TouchControls' layer)
local area = T.new("Frame", { Name = "Area", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, gui) :: Frame
local grid = T.new("Frame", { Name = "Grid", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ClipsDescendants = true }, area) :: Frame
local ghostsF = T.new("Frame", { Name = "Ghosts", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = 2 }, area) :: Frame
local edge = T.new("Frame", { Name = "Edge", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, area) :: Frame
T.new("UIStroke", { Color = T.EDGE, Transparency = 0.7, Thickness = 1 }, edge)

local gridFor = Vector2.zero
local function drawGrid(sz: Vector2)
	if sz == gridFor then return end
	gridFor = sz
	grid:ClearAllChildren()
	for x = 16, sz.X, 16 do
		T.new("Frame", { BackgroundColor3 = T.EDGE, BackgroundTransparency = if x % 64 == 0 then 0.86 else 0.93, BorderSizePixel = 0,
			Position = UDim2.fromOffset(x, 0), Size = UDim2.new(0, 1, 1, 0) }, grid)
	end
	for y = 16, sz.Y, 16 do
		T.new("Frame", { BackgroundColor3 = T.EDGE, BackgroundTransparency = if y % 64 == 0 then 0.86 else 0.93, BorderSizePixel = 0,
			Position = UDim2.fromOffset(0, y), Size = UDim2.new(1, 0, 0, 1) }, grid)
	end
end

-- ------------------------------------------------------------------ the things, drawn where they are
local ghosts: { [string]: TextButton } = {}
local placed: { [string]: { any } } = {} -- id -> { middle, size } (for the panel's side and the test's state)

local select: (string?) -> ()
local refreshPanel: () -> ()

local function ghostFor(r: any): TextButton
	local g = ghosts[r.id]
	if g and g.Parent then return g end
	local round = r.kind == "btn" or r.kind == "stick"
	g = T.new("TextButton", { Name = r.id, AutoButtonColor = false, AnchorPoint = Vector2.new(0.5, 0.5), BackgroundColor3 = T.BG,
		BorderSizePixel = 0, Text = "", FontFace = T.FONT_HEAVY, TextSize = 12, TextColor3 = T.TEXT, Selectable = false, ZIndex = 3 }, ghostsF) :: TextButton
	if round then T.new("UICorner", { CornerRadius = UDim.new(0.5, 0) }, g) else T.corner(g, if r.kind == "box" then 6 else 8) end
	T.new("UIStroke", { Name = "Line", Color = T.EDGE, Transparency = 0.5, Thickness = 1, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, g)
	if r.kind == "stick" then
		local knob = T.new("Frame", { Name = "Knob", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromScale(0.44, 0.44),
			BackgroundColor3 = T.TEXT, BackgroundTransparency = 0.6, BorderSizePixel = 0, ZIndex = 3 }, g)
		T.new("UICorner", { CornerRadius = UDim.new(0.5, 0) }, knob)
	end
	local hidden = T.text(g, "Hidden", "HIDDEN", 10, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center)
	hidden.AnchorPoint = Vector2.new(0.5, 0)
	hidden.Position = UDim2.new(0.5, 0, 1, 2)
	hidden.Size = UDim2.fromOffset(60, 12)
	hidden.ZIndex = 4
	hidden.Visible = false
	local id = r.id
	g.InputBegan:Connect(function(io: InputObject)
		if io.UserInputType ~= TOUCH and io.UserInputType ~= MB1 then return end
		if not E.open then return end
		E.pick = nil
		select(id)
		local p = placed[id]
		local at = Vector2.new(io.Position.X, io.Position.Y)
		local mid = if p then area.AbsolutePosition + p[1] else at
		E.drag = { id = id, key = if io.UserInputType == TOUCH then io else "mouse", off = mid - at, moved = false }
	end)
	ghosts[r.id] = g
	return g
end

local function drawGhosts()
	local sz = area.AbsoluteSize
	if sz.X < 10 then return end
	drawGrid(sz)
	local W, H = sz.X, sz.Y
	local ts, sd, lf = tsNow(), sdNow(), lefty()
	local avoid = TL.avoid(area.AbsolutePosition, typeof(me:GetAttribute("FakeScreen")) == "Vector2")
	local pt = TL.pillTop(pg, area.AbsolutePosition, W, ts)
	local a0 = alphaNow()
	local seen: { [string]: boolean } = {}
	for _, r in items() do
		seen[r.id] = true
		local c, s = TL.place(r, W, H, ts, sd, lf, avoid, pt)
		placed[r.id] = { c, s }
		local g = ghostFor(r)
		local pos, size = UDim2.fromOffset(c.X, c.Y), UDim2.fromOffset(s.X, s.Y)
		if g.Position ~= pos then g.Position = pos end
		if g.Size ~= size then g.Size = size end
		local label = TL.label(r)
		if g.Text ~= label then g.Text = label end
		local d = math.min(s.X, s.Y)
		g.TextSize = if r.kind == "box" then 13 elseif r.kind == "pill" then math.max(9, math.floor(11 * ts * r.s + 0.5))
			else math.floor(math.clamp(d * (if #label >= 6 then 0.2 else 0.24), 9, 17) + 0.5)
		local a = if r.kind == "box" then 0.8 else math.clamp(a0 * r.a, 0.1, 1)
		if r.hid then a = 0.18 end
		local on = E.sel == r.id
		g.BackgroundTransparency = if r.kind == "stick" then 1 - 0.2 * a else 1 - a * 0.72
		g.TextTransparency = (1 - a) * 0.55
		g.TextYAlignment = if r.kind == "stick" then Enum.TextYAlignment.Bottom else Enum.TextYAlignment.Center
		local line = g:FindFirstChild("Line") :: UIStroke
		line.Color = if on then T.ACCENT elseif r.act == "fire" then T.ACCENT else T.EDGE
		line.Thickness = if on then 2 else 1
		line.Transparency = if on then 0 else (if r.kind == "box" then 0.35 else 0.5)
		local hid = g:FindFirstChild("Hidden") :: TextLabel
		hid.Visible = r.hid
	end
	for id, g in ghosts do
		if not seen[id] then g:Destroy(); ghosts[id] = nil; placed[id] = nil end
	end
end

-- ------------------------------------------------------------------ the panel
local panel = T.new("Frame", { Name = "Panel", AnchorPoint = Vector2.new(0.5, 0), BackgroundColor3 = T.BG, BackgroundTransparency = 0.06,
	BorderSizePixel = 0, AutomaticSize = Enum.AutomaticSize.Y, Size = UDim2.fromOffset(440, 0), ZIndex = 10 }, area) :: Frame
T.corner(panel, 8)
T.edge(panel, nil, 0.75)
T.new("UIPadding", { PaddingLeft = UDim.new(0, 8), PaddingRight = UDim.new(0, 8), PaddingTop = UDim.new(0, 8), PaddingBottom = UDim.new(0, 8) }, panel)
T.new("UIListLayout", { FillDirection = Enum.FillDirection.Vertical, Padding = UDim.new(0, 6), SortOrder = Enum.SortOrder.LayoutOrder }, panel)

local function row(name: string, order: number): Frame
	local f = T.new("Frame", { Name = name, BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 30), LayoutOrder = order, ZIndex = 10 }, panel) :: Frame
	T.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 6), SortOrder = Enum.SortOrder.LayoutOrder,
		VerticalAlignment = Enum.VerticalAlignment.Center }, f)
	return f
end
local function chip(parent: Instance, name: string, text: string, order: number, w: number?): TextButton
	local b = T.new("TextButton", { Name = name, AutoButtonColor = false, BackgroundColor3 = T.CARD, BorderSizePixel = 0, FontFace = T.FONT_BOLD,
		TextSize = 12, TextColor3 = T.TEXT, Text = text, LayoutOrder = order, Size = UDim2.fromOffset(w or 0, 30), ZIndex = 11, Selectable = false,
		AutomaticSize = if w then Enum.AutomaticSize.None else Enum.AutomaticSize.X }, parent) :: TextButton
	T.corner(b, 5)
	T.edge(b, nil, 0.8)
	if not w then T.new("UIPadding", { PaddingLeft = UDim.new(0, 8), PaddingRight = UDim.new(0, 8) }, b) end
	return b
end
local function paint(b: TextButton, on: boolean, accent: boolean?)
	b.BackgroundColor3 = if on then T.ACCENT elseif accent then T.CARD_HI else T.CARD
	b.TextColor3 = if on then T.INK else T.TEXT
end

-- the bar: LAYOUT 1 2 3 · ADD BUTTON · RESET · CANCEL · SAVE
local bar = row("Bar", 1)
local layoutWord = T.text(bar, "Layout", "LAYOUT", 12, T.MUTED, T.FONT_BOLD)
layoutWord.Size = UDim2.fromOffset(46, 30); layoutWord.LayoutOrder = 0; layoutWord.ZIndex = 11
local slotBtns: { TextButton } = {}
for i = 1, 3 do slotBtns[i] = chip(bar, "Slot" .. i, tostring(i), i, 28) end
T.new("Frame", { Name = "Gap", BackgroundTransparency = 1, Size = UDim2.fromOffset(6, 30), LayoutOrder = 4 }, bar)
local addBtn = chip(bar, "Add", "ADD BUTTON", 5)
local resetBtn = chip(bar, "Reset", "RESET", 6)
local cancelBtn = chip(bar, "Cancel", "CANCEL", 7)
local saveBtn = chip(bar, "Save", "SAVE", 8)
paint(saveBtn, true)

-- the selected thing: its name, SIZE, OPACITY
local rowB = row("Sel", 2)
local selName = T.text(rowB, "Name", "", 13, T.TEXT, T.FONT_HEAVY)
selName.Size = UDim2.fromOffset(78, 30); selName.LayoutOrder = 0; selName.ZIndex = 11
selName.TextTruncate = Enum.TextTruncate.AtEnd
local hint = T.text(rowB, "Hint", "TAP A BUTTON TO EDIT IT, DRAG IT TO MOVE IT", 12, T.MUTED, T.FONT_BOLD)
hint.Size = UDim2.new(1, 0, 0, 30); hint.LayoutOrder = 9; hint.ZIndex = 11

type Slider = { holder: Frame, track: Frame, fill: Frame, knob: Frame, value: TextLabel, set: (number) -> (), min: number, max: number }
local function slider(parent: Instance, name: string, word: string, order: number, min: number, max: number, onSet: (number) -> ()): Slider
	local h = T.new("Frame", { Name = name, BackgroundTransparency = 1, Size = UDim2.fromOffset(160, 30), LayoutOrder = order, ZIndex = 11 }, parent) :: Frame
	local w = T.text(h, "Word", word, 11, T.MUTED, T.FONT_BOLD)
	w.Size = UDim2.fromOffset(160, 12); w.ZIndex = 11
	local v = T.text(h, "Value", "", 11, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Right)
	v.Size = UDim2.fromOffset(160, 12); v.ZIndex = 11
	local track = T.new("Frame", { Name = "Track", BackgroundColor3 = T.TRACK, BorderSizePixel = 0, Position = UDim2.fromOffset(0, 19), Size = UDim2.new(1, 0, 0, 5), ZIndex = 11 }, h) :: Frame
	T.corner(track, 3)
	local fill = T.new("Frame", { Name = "Fill", BackgroundColor3 = T.TEXT, BorderSizePixel = 0, Size = UDim2.fromScale(0.5, 1), ZIndex = 11 }, track) :: Frame
	T.corner(fill, 3)
	local knob = T.new("Frame", { Name = "Knob", AnchorPoint = Vector2.new(0.5, 0.5), BackgroundColor3 = T.TEXT, BorderSizePixel = 0,
		Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(14, 14), ZIndex = 12 }, track) :: Frame
	T.new("UICorner", { CornerRadius = UDim.new(0.5, 0) }, knob)
	local hit = T.new("TextButton", { Name = "Hit", Text = "", BackgroundTransparency = 1, Position = UDim2.fromOffset(-8, 8), Size = UDim2.new(1, 16, 0, 26),
		ZIndex = 13, Selectable = false }, h) :: TextButton
	local s: Slider = { holder = h, track = track, fill = fill, knob = knob, value = v, set = onSet, min = min, max = max }
	local function fromX(x: number)
		local t = math.clamp((x - track.AbsolutePosition.X) / math.max(1, track.AbsoluteSize.X), 0, 1)
		onSet(math.floor((min + (max - min) * t) * 20 + 0.5) / 20) -- (5 % steps)
	end
	hit.InputBegan:Connect(function(io: InputObject)
		if io.UserInputType ~= TOUCH and io.UserInputType ~= MB1 then return end
		E.slide = { key = if io.UserInputType == TOUCH then io else "mouse", fromX = fromX }
		fromX(io.Position.X)
	end)
	return s
end
local function showSlider(s: Slider, v: number)
	local t = math.clamp((v - s.min) / (s.max - s.min), 0, 1)
	s.fill.Size = UDim2.fromScale(t, 1)
	s.knob.Position = UDim2.fromScale(t, 0.5)
	s.value.Text = ("%d%%"):format(math.floor(v * 100 + 0.5))
end
local function changed() E.dirty[E.slot] = true end
local sizeS = slider(rowB, "Size", "SIZE", 1, TL.SIZE_MIN, TL.SIZE_MAX, function(v)
	local r = rec(E.sel)
	if r and TL.canSize(r) then r.s = math.clamp(v, TL.SIZE_MIN, TL.SIZE_MAX); changed(); refreshPanel() end
end)
local alphaS = slider(rowB, "Alpha", "OPACITY", 2, TL.ALPHA_MIN, 1, function(v)
	local r = rec(E.sel)
	if r and r.kind ~= "box" then r.a = math.clamp(v, TL.ALPHA_MIN, 1); changed(); refreshPanel() end
end)

-- what it does, hide, the stick's kind, remove
local rowC = row("Do", 3)
local actBtn = chip(rowC, "Action", "ACTION", 1)
local hideBtn = chip(rowC, "Hide", "HIDE", 2)
local stickBtn = chip(rowC, "Stick", "STICK: FLOATING", 3)
local removeBtn = chip(rowC, "Remove", "REMOVE", 4)
local deselBtn = chip(rowC, "Done", "DONE", 5)

-- the action list (ACTION / ADD BUTTON)
local pickF = T.new("Frame", { Name = "Pick", BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 0), AutomaticSize = Enum.AutomaticSize.Y,
	LayoutOrder = 4, ZIndex = 10, Visible = false }, panel) :: Frame
local pickWord = T.text(pickF, "Word", "", 11, T.MUTED, T.FONT_BOLD)
pickWord.Size = UDim2.new(1, 0, 0, 14); pickWord.ZIndex = 11
local pickGrid = T.new("Frame", { Name = "Grid", BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 18), Size = UDim2.new(1, 0, 0, 0),
	AutomaticSize = Enum.AutomaticSize.Y, ZIndex = 10 }, pickF) :: Frame
T.new("UIGridLayout", { CellSize = UDim2.fromOffset(66, 28), CellPadding = UDim2.fromOffset(5, 5), SortOrder = Enum.SortOrder.LayoutOrder }, pickGrid)
local pickBtns: { [string]: TextButton } = {}
for i, a in TL.PICK do
	local b = chip(pickGrid, a, TL.ACTIONS[a].label, i, 66)
	b.TextSize = 11
	pickBtns[a] = b
end
local pickBack = chip(pickGrid, "Back", "BACK", 99, 66)
pickBack.TextSize = 11
pickBack.BackgroundColor3 = T.CARD_HI
pickBack.Activated:Connect(function() E.pick = nil; refreshPanel() end)

-- ------------------------------------------------------------------ refresh
refreshPanel = function()
	for i, b in slotBtns do paint(b, i == E.slot) end
	addBtn.TextTransparency = if TL.freeExtra(items()) then 0 else 0.6
	paint(addBtn, E.pick == "add", false)
	local r = rec(E.sel)
	rowB.Visible = E.pick == nil -- (the action list takes their place: the panel stays short on a phone)
	selName.Visible = r ~= nil
	hint.Visible = r == nil
	sizeS.holder.Visible = r ~= nil and TL.canSize(r)
	alphaS.holder.Visible = r ~= nil and r.kind ~= "box"
	rowC.Visible = r ~= nil and E.pick == nil
	if r then
		selName.Text = TL.label(r)
		showSlider(sizeS, r.s)
		showSlider(alphaS, r.a)
		actBtn.Visible = TL.canAct(r)
		actBtn.Text = "ACTION: " .. (TL.ACTIONS[r.act] and TL.ACTIONS[r.act].label or "")
		paint(actBtn, E.pick == "act", false)
		hideBtn.Visible = TL.canHide(r)
		hideBtn.Text = if r.hid then "SHOW" else "HIDE"
		stickBtn.Visible = r.kind == "stick"
		stickBtn.Text = if r.act == "fixed" then "STICK: FIXED" else "STICK: FLOATING"
		removeBtn.Visible = TL.base(r.id).extra == true
	end
	pickF.Visible = E.pick ~= nil
	if E.pick then
		pickWord.Text = if E.pick == "add" then "ADD A BUTTON FOR" else "THIS BUTTON DOES"
		for a, b in pickBtns do paint(b, E.pick == "act" and r ~= nil and r.act == a) end
	end
	-- the panel goes to the half of the screen the selected thing isn't in, and is never wider than the screen
	local sz = area.AbsoluteSize
	panel.Size = UDim2.fromOffset(math.min(452, sz.X - 16), 0)
	local p = r and placed[r.id]
	local low = p ~= nil and p[1].Y < sz.Y * 0.5
	panel.AnchorPoint = if low then Vector2.new(0.5, 1) else Vector2.new(0.5, 0)
	panel.Position = if low then UDim2.new(0.5, 0, 1, -8) else UDim2.new(0.5, 0, 0, 8)
	drawGhosts()
end

select = function(id: string?)
	E.sel = id
	refreshPanel()
end

-- ------------------------------------------------------------------ actions
local function setOpen(on: boolean)
	if on == E.open then return end
	E.open = on
	E.drag, E.slide, E.pick = nil, nil, nil
	if on then
		E.work, E.dirty = {}, {}
		for n = 1, 3 do E.work[n] = TL.load(n) end
		E.slot = TL.slot()
		E.sel = nil
	end
	-- (in a test with a fake phone-sized screen the editor sits in the same box as the touch layer)
	local f = me:GetAttribute("FakeScreen")
	if typeof(f) == "Vector2" then
		area.AnchorPoint, area.Position, area.Size = Vector2.new(0.5, 0.5), UDim2.fromScale(0.5, 0.5), UDim2.fromOffset(f.X, f.Y)
	else
		area.AnchorPoint, area.Position, area.Size = Vector2.zero, UDim2.new(), UDim2.fromScale(1, 1)
	end
	back.Enabled, gui.Enabled = on, on
	if okMC then pcall(MenuCursor.set, "touchedit", on, function() return E.open end) end
	if me:GetAttribute("TouchEditOpen") ~= on then me:SetAttribute("TouchEditOpen", on) end
	if on then task.defer(refreshPanel) end
end
local function save()
	for n = 1, 3 do if E.dirty[n] then TL.save(n, E.work[n]) end end
	Settings.set("tl.slot", if E.slot == 1 then nil else E.slot)
	if type((Settings :: any).flush) == "function" then (Settings :: any).flush() end
	setOpen(false)
end
local function reset()
	E.work[E.slot] = TL.defaults()
	E.sel, E.pick = nil, nil
	changed()
	refreshPanel()
end
local function addFor(act: string)
	local id = TL.freeExtra(items())
	if not id then return end
	local r = TL.newExtra(id, act)
	table.insert(items(), r)
	changed()
	E.pick = nil
	select(id)
end
local function setAct(act: string)
	local r = rec(E.sel)
	if not r or not TL.canAct(r) or not TL.ACTIONS[act] then return end
	r.act = act
	changed()
	E.pick = nil
	refreshPanel()
end
local function remove(id: string)
	local list = items()
	for i, r in list do
		if r.id == id and TL.base(id).extra then table.remove(list, i); changed(); break end
	end
	if E.sel == id then E.sel = nil end
	refreshPanel()
end
local function moveTo(id: string, mid: Vector2)
	local r = rec(id)
	local p = placed[id]
	if not r or not p then return end
	local sz = area.AbsoluteSize
	local s = p[2]
	local x = math.floor(mid.X / GRID + 0.5) * GRID
	local y = math.floor(mid.Y / GRID + 0.5) * GRID
	local avoid = TL.avoid(area.AbsolutePosition, typeof(me:GetAttribute("FakeScreen")) == "Vector2")
	x, y = TL.clamp(x, y, s.X, s.Y, sz.X, sz.Y, avoid)
	TL.store(r, Vector2.new(x, y), sz.X, sz.Y, lefty())
	changed()
	drawGhosts()
end

for i, b in slotBtns do b.Activated:Connect(function() E.slot = i; E.sel, E.pick = nil, nil; refreshPanel() end) end
addBtn.Activated:Connect(function()
	if not TL.freeExtra(items()) then return end
	E.pick = if E.pick == "add" then nil else "add"
	if E.pick then E.sel = nil end
	refreshPanel()
end)
resetBtn.Activated:Connect(reset)
cancelBtn.Activated:Connect(function() setOpen(false) end)
saveBtn.Activated:Connect(save)
actBtn.Activated:Connect(function() E.pick = if E.pick == "act" then nil else "act"; refreshPanel() end)
hideBtn.Activated:Connect(function()
	local r = rec(E.sel)
	if r and TL.canHide(r) then r.hid = not r.hid; changed(); refreshPanel() end
end)
stickBtn.Activated:Connect(function()
	local r = rec(E.sel)
	if r and r.kind == "stick" then r.act = if r.act == "fixed" then "float" else "fixed"; changed(); refreshPanel() end
end)
removeBtn.Activated:Connect(function() if E.sel then remove(E.sel) end end)
deselBtn.Activated:Connect(function() E.pick = nil; select(nil) end)
for a, b in pickBtns do
	b.Activated:Connect(function()
		if E.pick == "add" then addFor(a) elseif E.pick == "act" then setAct(a) end
	end)
end
dim.Activated:Connect(function() if E.open then E.pick = nil; select(nil) end end)

-- dragging a thing, or a slider
UIS.InputChanged:Connect(function(io: InputObject)
	if not E.open then return end
	local t = io.UserInputType
	if t ~= TOUCH and t ~= Enum.UserInputType.MouseMovement then return end
	local key: any = if t == TOUCH then io else "mouse"
	local at = Vector2.new(io.Position.X, io.Position.Y)
	if E.slide and E.slide.key == key then E.slide.fromX(at.X); return end
	local d = E.drag
	if d and d.key == key then
		d.moved = true
		moveTo(d.id, at + d.off - area.AbsolutePosition)
	end
end)
UIS.InputEnded:Connect(function(io: InputObject)
	local t = io.UserInputType
	if t ~= TOUCH and t ~= MB1 then return end
	local key: any = if t == TOUCH then io else "mouse"
	if E.slide and E.slide.key == key then E.slide = nil end
	if E.drag and E.drag.key == key then E.drag = nil; refreshPanel() end
end)

-- open / close: the attribute (Settings' TOUCH LAYOUT row sets it)
me:GetAttributeChangedSignal("TouchEditOpen"):Connect(function() setOpen(me:GetAttribute("TouchEditOpen") == true) end)
-- the layout's size follows the screen (turning the phone, a test's fake box)
RunService.Heartbeat:Connect(function()
	if not E.open then return end
	local f = me:GetAttribute("FakeScreen")
	local want = if typeof(f) == "Vector2" then UDim2.fromOffset(f.X, f.Y) else UDim2.fromScale(1, 1)
	if area.Size ~= want then
		area.Size = want
		area.AnchorPoint = if typeof(f) == "Vector2" then Vector2.new(0.5, 0.5) else Vector2.zero
		area.Position = if typeof(f) == "Vector2" then UDim2.fromScale(0.5, 0.5) else UDim2.new()
	end
	drawGhosts()
end)

-- ------------------------------------------------------------------ test hook (Studio)
if RunService:IsStudio() then
	me:GetAttributeChangedSignal("TouchEditTest"):Connect(function()
		local v = me:GetAttribute("TouchEditTest")
		if type(v) ~= "string" or v == "" then return end
		me:SetAttribute("TouchEditTest", nil)
		local cmd, a = string.match(v, "^(%a+):?(.*)$")
		local args = string.split(a or "", ",")
		if cmd == "open" then setOpen(true)
		elseif cmd == "cancel" then setOpen(false)
		elseif cmd == "save" then save()
		elseif cmd == "reset" then reset()
		elseif cmd == "slot" then E.slot = math.clamp(tonumber(args[1]) or 1, 1, 3); E.sel = nil; refreshPanel()
		elseif cmd == "select" then E.pick = nil; select(if args[1] ~= "" then args[1] else nil)
		elseif cmd == "move" then
			drawGhosts()
			moveTo(args[1], Vector2.new(tonumber(args[2]) or 0, tonumber(args[3]) or 0)); refreshPanel()
		elseif cmd == "size" then local r = rec(args[1]); if r and TL.canSize(r) then r.s = math.clamp((tonumber(args[2]) or 100) / 100, TL.SIZE_MIN, TL.SIZE_MAX); changed(); refreshPanel() end
		elseif cmd == "alpha" then local r = rec(args[1]); if r then r.a = math.clamp((tonumber(args[2]) or 100) / 100, TL.ALPHA_MIN, 1); changed(); refreshPanel() end
		elseif cmd == "act" then E.sel = args[1]; setAct(args[2] or "")
		elseif cmd == "hide" or cmd == "show" then local r = rec(args[1]); if r and TL.canHide(r) then r.hid = cmd == "hide"; changed(); refreshPanel() end
		elseif cmd == "add" then addFor(args[1])
		elseif cmd == "remove" then remove(args[1])
		elseif cmd == "stick" then local r = rec("stick"); if r then r.act = if args[1] == "fixed" then "fixed" else "float"; changed(); refreshPanel() end
		elseif cmd == "pick" then E.pick = if args[1] == "none" then nil else args[1]; refreshPanel()
		elseif cmd == "state" then
			local dirty = {}
			for n = 1, 3 do if E.dirty[n] then table.insert(dirty, n) end end
			local out: any = { open = E.open, slot = E.slot, sel = E.sel or "", pick = E.pick or "", dirty = dirty, active = TL.slot(), items = {}, placed = {} }
			if E.open then
				for _, r in items() do
					table.insert(out.items, { id = r.id, act = r.act or "", fx = r.fx or -1, fy = r.fy or -1, s = r.s, a = r.a, hid = r.hid })
					local p = placed[r.id]
					if p then out.placed[r.id] = { math.floor(p[1].X), math.floor(p[1].Y), math.floor(p[2].X), math.floor(p[2].Y) } end
				end
			end
			me:SetAttribute("TouchEditState", HttpService:JSONEncode(out))
		end
	end)
end
