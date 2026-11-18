--!nonstrict
-- the settings page (P): tabs down the left, rows on the right, every change live (Settings.luau keeps the values,
-- SettingsApply.client.luau and the scripts that read them do the work). the look is Theme's: a dark plate, cards for
-- rows, white and grey words, the one amber accent for what's on. no icons, no jokes: a short label, and under it in
-- grey one plain line on what it does.
--   UI.build(gui)    once, into the JankSettings ScreenGui (JankSettings.client.luau)
--   UI.setOpen(on)   show / hide;  UI.isOpen();  UI.capturing (true while a key cap waits for a key)
--   UI.show(tabId)   jump to a tab (tests: the photo sheet)
local Players = game:GetService("Players")
local UIS = game:GetService("UserInputService")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ContextActionService = game:GetService("ContextActionService")

local me = Players.LocalPlayer
local T = require(script.Parent:WaitForChild("Theme"))
local Settings = require(script.Parent:WaitForChild("Settings"))
local Binds = require(script.Parent:WaitForChild("Binds"))
local XH = require(script.Parent:WaitForChild("Crosshair"))
local Pad = require(script.Parent:WaitForChild("Pad")) -- (the controller's button pictures and names: the CONTROLLER tab)

local UI = { capturing = false }
-- a controller steps a slider: its grab is what gets selected, left and right nudge it (PadNav.client)
UI.nudge = setmetatable({}, { __mode = "k" })
local W, H = 1000, 640 -- the page in design pixels (Theme's 720-tall screen)
local RAIL = 212
local ROW_H = 60

local page, scrim, scale, list, header, message, resetBtn, statusText
local tabs = {}
local tabButtons = {}
local current = nil
local refreshers = {} -- key -> { fn }
local anyRefresh = {} -- fns run on every change (preset sub-lines, the preview)
local dragging = nil
local listening = nil
local order = 0

-- ------------------------------------------------------------------ small pieces
local function nextOrder() order += 1; return order end
local function onKey(k, fn)
	refreshers[k] = refreshers[k] or {}
	table.insert(refreshers[k], fn)
end
Settings.onAny(function(k)
	if refreshers[k] then for _, fn in refreshers[k] do task.spawn(fn) end end
	for _, fn in anyRefresh do task.spawn(fn, k) end
end)

local msgTok = 0
local function say(text, warn)
	msgTok += 1
	local my = msgTok
	message.Text = text
	message.TextColor3 = if warn then T.DANGER else T.ACCENT
	task.delay(4, function() if my == msgTok then message.Text = "" end end)
end

local function snap(v, step)
	if not step or step <= 0 then return v end
	return tonumber(string.format("%.4f", math.floor(v / step + 0.5) * step))
end

local function section(text, sub)
	local f = T.new("Frame", { Name = "Section", BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, if sub then 46 else 32), LayoutOrder = nextOrder() }, list)
	local l = T.text(f, "Text", text, 12, T.MUTED, T.FONT_BOLD)
	l.Position = UDim2.fromOffset(4, 12); l.Size = UDim2.new(1, -8, 0, 16)
	if sub then
		local s = T.text(f, "Sub", sub, 12, T.DIM)
		s.Position = UDim2.fromOffset(4, 28); s.Size = UDim2.new(1, -8, 0, 16)
	end
	return f
end

local function rowName(key) return "Row_" .. string.gsub(key or "x", "[^%w]", "_") end
local function rowFrame(label, sub, h, name)
	local r = T.new("Frame", { Name = name or "Row", BackgroundColor3 = T.CARD, BorderSizePixel = 0, Size = UDim2.new(1, 0, 0, h or ROW_H), LayoutOrder = nextOrder() }, list)
	T.corner(r, 6)
	local l = T.text(r, "Label", label, 14, T.TEXT, T.FONT_BOLD)
	l.Position = UDim2.fromOffset(18, if sub then 11 else 0)
	l.Size = UDim2.new(0.46, -18, 0, if sub then 18 else (h or ROW_H))
	l.TextTruncate = Enum.TextTruncate.AtEnd
	local s = nil
	if sub then
		s = T.text(r, "Sub", sub, 12, T.DIM)
		s.Position = UDim2.fromOffset(18, 32); s.Size = UDim2.new(0.5, -18, 0, 16)
		s.TextTruncate = Enum.TextTruncate.AtEnd
	end
	local ctl = T.new("Frame", { Name = "Control", BackgroundTransparency = 1, AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -16, 0.5, 0),
		Size = UDim2.new(0.5, -20, 0, 34) }, r)
	r.MouseEnter:Connect(function() r.BackgroundColor3 = T.CARD_HI end)
	r.MouseLeave:Connect(function() r.BackgroundColor3 = T.CARD end)
	return r, ctl, s, l
end

-- what to do after the player changed a row: a graphics switch makes the preset CUSTOM
local function changed(def, before)
	if def.marks and Settings.get(def.key) ~= before then Settings.set(def.marks, "custom") end
	if def.after then def.after() end
end

-- ------------------------------------------------------------------ a slider
local function slider(def)
	local r, ctl = rowFrame(def.label, def.sub, nil, rowName(def.key))
	local track = T.new("Frame", { Name = "Track", AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.new(0, 8, 0.5, 0), Size = UDim2.new(1, -96, 0, 6),
		BackgroundColor3 = T.TRACK, BorderSizePixel = 0 }, ctl)
	T.corner(track, 3)
	local fill = T.new("Frame", { Name = "Fill", BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Size = UDim2.fromScale(0, 1) }, track)
	T.corner(fill, 3)
	local knob = T.new("Frame", { Name = "Knob", AnchorPoint = Vector2.new(0.5, 0.5), Size = UDim2.fromOffset(18, 18), BackgroundColor3 = T.TEXT, BorderSizePixel = 0, ZIndex = 2 }, track)
	T.corner(knob, 9)
	T.edge(knob, T.BG, 0, 2)
	local box = T.new("TextBox", { Name = "Value", AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, 0, 0.5, 0), Size = UDim2.fromOffset(74, 32),
		BackgroundColor3 = T.BG, BorderSizePixel = 0, FontFace = T.FONT_BOLD, TextSize = 14, TextColor3 = T.TEXT, Text = "", ClearTextOnFocus = false }, ctl)
	T.corner(box, 4); T.edge(box)
	local function get()
		local v = Settings.get(def.key)
		if v == nil and def.auto then v = def.auto() end -- (no value yet: the automatic one)
		return if type(v) == "number" then v else def.min
	end
	local function refresh()
		local u = math.clamp((get() - def.min) / (def.max - def.min), 0, 1)
		fill.Size = UDim2.fromScale(u, 1)
		knob.Position = UDim2.fromScale(u, 0.5)
		if not box:IsFocused() then box.Text = def.fmt(get()) end
	end
	local function setV(v)
		local before = Settings.get(def.key)
		Settings.set(def.key, math.clamp(snap(v, def.step), def.min, def.max))
		changed(def, before)
	end
	local s = { track = track }
	function s.setFromX(x)
		local u = math.clamp((x - track.AbsolutePosition.X) / math.max(1, track.AbsoluteSize.X), 0, 1)
		setV(def.min + (def.max - def.min) * u)
	end
	local grab = T.new("TextButton", { Name = "Grab", BackgroundTransparency = 1, Text = "", Position = UDim2.new(0, -10, 0, -14), Size = UDim2.new(1, 20, 1, 28), ZIndex = 3 }, track)
	grab.MouseButton1Down:Connect(function(x) dragging = s; s.setFromX(x) end)
	box.Selectable = false
	grab.NextSelectionLeft = grab; grab.NextSelectionRight = grab
	UI.nudge[grab] = function(d) setV(get() + d * math.max(def.step or 0, (def.max - def.min) / 40)) end
	box.FocusLost:Connect(function()
		local n = tonumber(string.match(box.Text, "%-?[%d%.]+") or "")
		if n then setV(n / (def.scale or 1)) end
		refresh()
	end)
	onKey(def.key, refresh)
	refresh()
	return r
end
local function pct(v) return ("%d%%"):format(math.floor(v * 100 + 0.5)) end
local function times(v) return ("%.2fx"):format(v) end
local function px(v) return ("%d px"):format(v) end

-- ------------------------------------------------------------------ a switch (the whole row is the button)
local function switch(def)
	local r, ctl = rowFrame(def.label, def.sub, nil, rowName(def.key or def.attr))
	local sw = T.new("Frame", { Name = "Switch", AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, 0, 0.5, 0), Size = UDim2.fromOffset(52, 28),
		BackgroundColor3 = T.TRACK, BorderSizePixel = 0 }, ctl)
	T.corner(sw, 14)
	local knob = T.new("Frame", { Size = UDim2.fromOffset(22, 22), Position = UDim2.fromOffset(3, 3), BackgroundColor3 = T.TEXT, BorderSizePixel = 0 }, sw)
	T.corner(knob, 11)
	local get = def.get or function() return Settings.get(def.key) == true end
	local function refresh()
		local on = get()
		sw.BackgroundColor3 = if on then T.ACCENT else T.TRACK
		knob.Position = if on then UDim2.fromOffset(27, 3) else UDim2.fromOffset(3, 3)
	end
	local btn = T.new("TextButton", { Name = "Hit", BackgroundTransparency = 1, Text = "", Size = UDim2.fromScale(1, 1), ZIndex = 4 }, r)
	btn.MouseButton1Click:Connect(function()
		if def.flip then def.flip(); task.delay(0.05, refresh); return end
		local before = Settings.get(def.key)
		Settings.set(def.key, not get())
		changed(def, before)
	end)
	if def.key then onKey(def.key, refresh) end
	if def.attr then me:GetAttributeChangedSignal(def.attr):Connect(refresh) end
	refresh()
	return r
end

-- ------------------------------------------------------------------ a choice: pills, the one picked in amber
local function choice(def)
	local r, ctl, sub = rowFrame(def.label, def.sub or (if def.subFn then "" else nil), nil, rowName(def.key))
	local holder = T.new("Frame", { Name = "Pills", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, ctl)
	T.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, HorizontalAlignment = Enum.HorizontalAlignment.Right,
		VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, 6), SortOrder = Enum.SortOrder.LayoutOrder }, holder)
	local pills = {}
	for i, o in def.options do
		local b = T.new("TextButton", { Name = "Pill_" .. tostring(o[1]), LayoutOrder = i, AutoButtonColor = false, AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 32),
			BackgroundColor3 = T.TRACK, BorderSizePixel = 0, FontFace = T.FONT_BOLD, TextSize = 13, TextColor3 = T.TEXT, Text = o[2] }, holder)
		T.corner(b, 5)
		T.new("UIPadding", { PaddingLeft = UDim.new(0, 12), PaddingRight = UDim.new(0, 12) }, b)
		b.MouseButton1Click:Connect(function()
			local before = Settings.get(def.key)
			Settings.set(def.key, o[1])
			changed(def, before)
		end)
		pills[i] = b
	end
	local function refresh()
		local v = Settings.get(def.key)
		for i, o in def.options do
			local on = v == o[1]
			pills[i].BackgroundColor3 = if on then T.ACCENT else T.TRACK
			pills[i].TextColor3 = if on then T.INK else T.TEXT
		end
		if def.subFn and sub then sub.Text = def.subFn() end
	end
	onKey(def.key, refresh)
	if def.also then for _, k in def.also do onKey(k, refresh) end end
	refresh()
	return r
end

-- ------------------------------------------------------------------ colour swatches (+ a hex box)
local function colours(def)
	local r, ctl = rowFrame(def.label, def.sub, nil, rowName(def.key))
	local holder = T.new("Frame", { Name = "Swatches", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, ctl)
	T.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, HorizontalAlignment = Enum.HorizontalAlignment.Right,
		VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, 8), SortOrder = Enum.SortOrder.LayoutOrder }, holder)
	local sw = {}
	for i, c in def.swatches do -- c = { value, Color3 }
		local b = T.new("TextButton", { Name = "Swatch_" .. tostring(c[1]), LayoutOrder = i, AutoButtonColor = false, Text = "", Size = UDim2.fromOffset(26, 26),
			BackgroundColor3 = c[2], BorderSizePixel = 0 }, holder)
		T.corner(b, 5)
		local st = T.edge(b, T.TEXT, 1, 2)
		b.MouseButton1Click:Connect(function() Settings.set(def.key, c[1]) end)
		sw[i] = { b = b, st = st, v = c[1] }
	end
	local box = nil
	if def.hex then
		box = T.new("TextBox", { Name = "Hex", LayoutOrder = 100, Size = UDim2.fromOffset(86, 32), BackgroundColor3 = T.BG, BorderSizePixel = 0,
			FontFace = T.FONT_BOLD, TextSize = 13, TextColor3 = T.TEXT, Text = "", ClearTextOnFocus = false, PlaceholderText = "#RRGGBB" }, holder)
		T.corner(box, 4); T.edge(box)
		box.FocusLost:Connect(function()
			local h = string.lower(string.gsub(box.Text, "[^%x]", ""))
			if #h == 6 then Settings.set(def.key, h) else say("A COLOR IS SIX HEX DIGITS, LIKE #FFE14D", true) end
			box.Text = "#" .. string.upper(tostring(Settings.get(def.key)))
		end)
	end
	local function refresh()
		local v = Settings.get(def.key)
		for _, s in sw do s.st.Transparency = if s.v == v then 0 else 1 end
		if box and not box:IsFocused() then box.Text = "#" .. string.upper(tostring(v)) end
	end
	onKey(def.key, refresh)
	refresh()
	return r
end

-- ------------------------------------------------------------------ a plain button row
local function button(def)
	local r, ctl = rowFrame(def.label, def.sub)
	local b = T.new("TextButton", { Name = "Button", AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, 0, 0.5, 0), AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 32), AutoButtonColor = false, BackgroundColor3 = T.TRACK, BorderSizePixel = 0, FontFace = T.FONT_BOLD, TextSize = 13,
		TextColor3 = T.TEXT, Text = def.text }, ctl)
	T.corner(b, 5)
	T.new("UIPadding", { PaddingLeft = UDim.new(0, 14), PaddingRight = UDim.new(0, 14) }, b)
	b.MouseEnter:Connect(function() b.BackgroundColor3 = T.CARD_HI end)
	b.MouseLeave:Connect(function() b.BackgroundColor3 = T.TRACK end)
	b.MouseButton1Click:Connect(function() def.click(b) end)
	return r, b
end

-- ------------------------------------------------------------------ key caps (the KEYBINDS tab)
local function capText(name) return if name == "" then "—" else string.upper(Binds.nameOf(name)) end
local capRefresh = {}
local function stopListening(cancelled)
	if not listening then return end
	local l = listening
	listening = nil
	UI.capturing = false
	pcall(function() ContextActionService:UnbindAction("JankBindSink") end)
	l.refresh()
	if cancelled then say("NOTHING CHANGED") end
end
local function keyRow(a)
	local r, ctl = rowFrame(a.label, nil, 48, "Key_" .. a.id)
	local caps = {}
	for slot = 1, 3 do
		local b = T.new("TextButton", { Name = "Cap" .. slot, AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -(3 - slot) * 112, 0.5, 0),
			Size = UDim2.fromOffset(104, 32), AutoButtonColor = false, BackgroundColor3 = T.BG, BorderSizePixel = 0, FontFace = T.FONT_BOLD, TextSize = 13,
			TextColor3 = T.TEXT, Text = "" }, ctl)
		T.corner(b, 5)
		T.edge(b, nil, 0.8)
		caps[slot] = b
	end
	local function refresh()
		local b = Binds.get(a.id)
		for slot = 1, 3 do
			local on = listening and listening.id == a.id and listening.slot == slot
			caps[slot].Text = if on then (if slot == 3 then "PRESS A BUTTON" else "PRESS A KEY") else capText(b[slot])
			caps[slot].BackgroundColor3 = if on then T.ACCENT else T.BG
			caps[slot].TextColor3 = if on then T.INK elseif b[slot] == "" then T.DIM else T.TEXT
		end
	end
	for slot = 1, 3 do
		caps[slot].MouseButton1Click:Connect(function()
			if listening and listening.id == a.id and listening.slot == slot then
				-- (the flashing cap clicked again: left mouse button, like the web game)
				if slot ~= 3 then
					local moved = Binds.set(a.id, slot, "MouseButton1")
					stopListening(false)
					if moved then say(("LMB WAS ON %s: IT HAS THIS ONE'S OLD KEY NOW"):format(moved)) end
				end
				return
			end
			stopListening(false)
			task.defer(function()
				listening = { id = a.id, slot = slot, refresh = refresh, cap = caps[slot] }
				UI.capturing = true
				-- (while it waits, the key goes to the cap only: no reloading or opening the shop on the way)
				ContextActionService:BindActionAtPriority("JankBindSink", function(_, state, io)
					if state == Enum.UserInputState.Begin then task.defer(UI.capture, io) end
					return Enum.ContextActionResult.Sink
				end, false, 4000,
					Enum.UserInputType.Keyboard, Enum.UserInputType.Gamepad1)
				refresh()
			end)
		end)
	end
	onKey("bind." .. a.id, refresh)
	table.insert(capRefresh, refresh)
	refresh()
	return r
end
-- ------------------------------------------------------------------ a controller button (the CONTROLLER tab): the pad's
-- own picture of the button and its name. select it, press it, then press the new button (the KEYBINDS' third column)
local function padRow(a)
	local r, ctl = rowFrame(a.label, nil, 48, "Pad_" .. a.id)
	local b = T.new("TextButton", { Name = "Cap3", AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, 0, 0.5, 0), Size = UDim2.fromOffset(170, 32),
		AutoButtonColor = false, BackgroundColor3 = T.BG, BorderSizePixel = 0, FontFace = T.FONT_BOLD, TextSize = 13, TextColor3 = T.TEXT, Text = "" }, ctl)
	T.corner(b, 5)
	T.edge(b, nil, 0.8)
	T.new("UIPadding", { PaddingLeft = UDim.new(0, 30) }, b)
	local g = T.new("ImageLabel", { Name = "Glyph", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.new(0, -24, 0.5, 0),
		Size = UDim2.fromOffset(22, 22), ScaleType = Enum.ScaleType.Fit, ImageColor3 = T.TEXT }, b)
	local function refresh()
		local name = Binds.get(a.id)[3]
		local on = listening and listening.id == a.id and listening.slot == 3
		b.Text = if on then "PRESS A BUTTON" elseif name == "" then "—" else Pad.short(name)
		g.Image = if on or name == "" then "" else Pad.image(name)
		b.BackgroundColor3 = if on then T.ACCENT else T.BG
		b.TextColor3 = if on then T.INK elseif name == "" then T.DIM else T.TEXT
	end
	b.MouseButton1Click:Connect(function()
		if listening and listening.id == a.id and listening.slot == 3 then return end
		stopListening(false)
		task.defer(function()
			listening = { id = a.id, slot = 3, refresh = refresh, cap = b }
			UI.capturing = true
			ContextActionService:BindActionAtPriority("JankBindSink", function(_, state, io)
				if state == Enum.UserInputState.Begin then task.defer(UI.capture, io) end
				return Enum.ContextActionResult.Sink
			end, false, 4000, Enum.UserInputType.Keyboard, Enum.UserInputType.Gamepad1)
			refresh()
		end)
	end)
	onKey("bind." .. a.id, refresh)
	table.insert(capRefresh, refresh)
	refresh()
	return r
end
local function fixedRow(f)
	local r, ctl = rowFrame(f.label, nil, 48)
	r.BackgroundTransparency = 0.5
	for slot, text in { f.kb, "", f.pad } do
		if text ~= "" then
			local b = T.text(ctl, "Fixed", string.upper(text), 13, T.DIM, T.FONT_BOLD, Enum.TextXAlignment.Center)
			b.AnchorPoint = Vector2.new(1, 0.5); b.Position = UDim2.new(1, -(3 - slot) * 112, 0.5, 0); b.Size = UDim2.fromOffset(104, 32)
		end
	end
	return r
end
-- the next input after a cap was clicked. keys and controller buttons come through the sink (so they reach no other
-- script on the way); mouse buttons through InputBegan
local function capture(io)
	if not listening then return end
	local l = listening
	local k = io.KeyCode
	if k == Enum.KeyCode.Escape or k == Enum.KeyCode.ButtonSelect then stopListening(true); return end -- (a pad's View cancels)
	if k == Enum.KeyCode.Backspace or k == Enum.KeyCode.Delete then
		Binds.set(l.id, l.slot, "")
		stopListening(false)
		say("KEY CLEARED")
		return
	end
	if io.UserInputType == Enum.UserInputType.MouseButton1 then
		-- (a click away from the cap: nothing changes. the cap itself handles a click on it. the page ignores the gui
		-- inset, so its AbsolutePosition and the mouse share one frame)
		local p, sz = l.cap.AbsolutePosition, l.cap.AbsoluteSize
		local m = UIS:GetMouseLocation()
		if not (m.X >= p.X and m.X <= p.X + sz.X and m.Y >= p.Y and m.Y <= p.Y + sz.Y) then stopListening(true) end
		return
	end
	local name = Binds.inputName(io, l.slot)
	if not name then
		if io.UserInputType == Enum.UserInputType.Keyboard or string.sub(io.UserInputType.Name, 1, 7) == "Gamepad" then
			say(if l.slot == 3 then "THAT COLUMN TAKES CONTROLLER BUTTONS" else "THAT KEY CAN'T BE USED", true)
		end
		return
	end
	local moved = Binds.set(l.id, l.slot, name)
	stopListening(false)
	if moved then say(("%s WAS ON %s: IT HAS THIS ONE'S OLD KEY NOW"):format(string.upper(Binds.nameOf(name)), moved)) end
	for _, f in capRefresh do f() end
end
UI.capture = capture
UIS.InputBegan:Connect(function(io)
	if not listening then return end
	local t = io.UserInputType
	if t == Enum.UserInputType.MouseButton1 or t == Enum.UserInputType.MouseButton2 or t == Enum.UserInputType.MouseButton3 then capture(io) end
end)

-- ------------------------------------------------------------------ the crosshair preview: dark and light ground
local previewHolders = {}
local function preview()
	local f = T.new("Frame", { Name = "Preview", BackgroundColor3 = T.CARD, BorderSizePixel = 0, Size = UDim2.new(1, 0, 0, 168), LayoutOrder = nextOrder(), ClipsDescendants = true }, list)
	T.corner(f, 6)
	local grounds = {
		{ Color3.fromRGB(34, 38, 46), Color3.fromRGB(58, 64, 76) }, -- a dark wall
		{ Color3.fromRGB(150, 160, 174), Color3.fromRGB(206, 210, 216) }, -- a pale sky over a pale floor
	}
	for i, g in grounds do
		local half = T.new("Frame", { Name = "Ground" .. i, BorderSizePixel = 0, BackgroundColor3 = g[1], Position = UDim2.fromScale((i - 1) * 0.5, 0), Size = UDim2.fromScale(0.5, 1) }, f)
		T.new("UIGradient", { Rotation = 90, Color = ColorSequence.new(g[1], g[2]) }, half)
		local holder = T.new("Frame", { Name = "Crosshair", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(40, 40) }, half)
		-- (the preview is drawn at its true pixel size: the page's scale is undone for it)
		local undo = T.new("UIScale", { Name = "Undo" }, holder)
		table.insert(previewHolders, { holder = holder, undo = undo })
	end
	local tag = T.text(f, "Note", "PREVIEW", 11, T.MUTED, T.FONT_BOLD)
	tag.Position = UDim2.fromOffset(12, 8); tag.Size = UDim2.fromOffset(120, 14)
	return f
end
local pulseT = 0
local function drawPreview()
	local o = XH.opts()
	local extra = 0
	if o.spread then extra = 6 * math.max(0, math.sin(pulseT * 2.2)) ^ 2 end -- (show spread: it opens and closes as if firing)
	for _, p in previewHolders do
		p.undo.Scale = 1 / math.max(0.01, scale.Scale)
		XH.draw(p.holder, o, 0, extra)
	end
end

-- ------------------------------------------------------------------ the crosshair code row
local function codeRow()
	local r, ctl = rowFrame("CROSSHAIR CODE", "copy to share, or paste one and press Enter", nil, "Row_code")
	local box = T.new("TextBox", { Name = "Code", AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, 0, 0.5, 0), Size = UDim2.fromOffset(240, 32),
		BackgroundColor3 = T.BG, BorderSizePixel = 0, FontFace = Font.new("rbxasset://fonts/families/RobotoMono.json", Enum.FontWeight.Bold), TextSize = 14,
		TextColor3 = T.TEXT, Text = "", ClearTextOnFocus = false, TextEditable = true }, ctl)
	T.corner(box, 4); T.edge(box)
	local function refresh() if not box:IsFocused() then box.Text = XH.encode() end end
	box.FocusLost:Connect(function(enter)
		local typed = box.Text
		if typed ~= XH.encode() and #typed > 0 then
			local ok, why = XH.apply(typed)
			if ok then say("CROSSHAIR CODE APPLIED") else say(string.upper(why or "not a crosshair code"), true) end
		end
		refresh()
	end)
	table.insert(anyRefresh, function(k) if string.sub(k, 1, 3) == "xh." then refresh() end end)
	refresh()
	return r
end

-- ------------------------------------------------------------------ the tabs
-- (a phone: the touch layout editor, TouchEdit.client: move, size, fade, hide and remap the touch buttons. at the top of
-- CONTROLS while the touch controls are on, and of TOUCH)
function UI.touchEditRow()
	button({ label = "TOUCH LAYOUT", sub = "move, resize and remap the buttons", text = "EDIT", click = function()
		me:SetAttribute("SettingsOpen", false)
		me:SetAttribute("TouchEditOpen", true)
	end })
end
local function percentOff(v) return if v <= 0 then "OFF" else px(v) end
local XH_PRESETS = {
	{ "DEFAULT", "X1CFFFFFF82510A2" },
	{ "DOT", "X1DFFFFFF12014A2" },
	{ "SMALL CROSS", "X1CFFFFFF52310A2" },
	{ "CIRCLE", "X1OFFFFFF22912A2" },
}

tabs = {
	{ id = "controls", title = "CONTROLS", reset = { "look.", "fov", "aim.toggle", "crouch.toggle", "sprint.toggle", "gfx.shake", "gfx.recoil" }, build = function()
		if me:GetAttribute("TouchOn") == true then UI.touchEditRow() end
		section("MOUSE")
		slider({ key = "look.sens", label = "SENSITIVITY", min = 0.05, max = 3, step = 0.01, fmt = function(v) return ("%.2f"):format(v) end })
		slider({ key = "look.ySpeed", label = "VERTICAL SENSITIVITY", sub = "multiplier on up and down", min = 0.5, max = 1.5, step = 0.01, fmt = pct, scale = 100 })
		switch({ key = "look.invert", label = "INVERT MOUSE Y" })
		section("ZOOM", "1.00 keeps the same feel as hip fire at every zoom")
		slider({ key = "look.ads", label = "ZOOM SENSITIVITY RATIO", sub = "iron sights and red dots", min = 0.2, max = 2, step = 0.01, fmt = times })
		slider({ key = "look.sniper", label = "SCOPED SENSITIVITY", sub = "Sniper, 4x scope", min = 0.2, max = 2, step = 0.01, fmt = times })
		slider({ key = "look.dmr", label = "SCOPED SENSITIVITY", sub = "Marksman Rifle, 2.6x scope", min = 0.2, max = 2, step = 0.01, fmt = times })
		section("VIEW")
		slider({ key = "fov", label = "FIELD OF VIEW", sub = "vertical, in degrees", min = 50, max = 120, step = 1, fmt = function(v) return tostring(v) end })
		switch({ key = "fov.kick", label = "FOV KICK", sub = "the view widens as you speed up" })
		switch({ key = "gfx.shake", label = "SCREEN SHAKE" })
		slider({ key = "gfx.recoil", label = "VISUAL RECOIL", sub = "how much the gun kicks on screen; aim is the same", min = 0, max = 1, step = 0.1, fmt = pct, scale = 100 })
		section("HOLD OR TOGGLE")
		local ht = { { false, "HOLD" }, { true, "TOGGLE" } }
		choice({ key = "aim.toggle", label = "AIM DOWN SIGHTS", options = ht })
		choice({ key = "crouch.toggle", label = "CROUCH", options = ht })
		choice({ key = "sprint.toggle", label = "SPRINT", options = ht })
	end },
	{ id = "keys", title = "KEYBINDS", reset = { "bind." }, build = function()
		local head = T.new("Frame", { Name = "Columns", BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 28), LayoutOrder = nextOrder() }, list)
		for slot, text in { "KEY", "ALTERNATE", "CONTROLLER" } do
			local l = T.text(head, "Col", text, 11, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center)
			l.AnchorPoint = Vector2.new(1, 0.5); l.Position = UDim2.new(1, -16 - (3 - slot) * 112, 0.5, 0); l.Size = UDim2.fromOffset(104, 16)
		end
		local hint = T.text(head, "How", "click a key, then press the new one. Backspace clears, Esc cancels", 12, T.DIM)
		hint.Position = UDim2.fromOffset(4, 6); hint.Size = UDim2.new(0.5, 0, 0, 16)
		local group = nil
		for _, a in Binds.ACTIONS do
			if a.group ~= group then
				group = a.group
				section(group)
				if group == "MOVEMENT" then for _, f in Binds.FIXED do fixedRow(f) end end
			end
			keyRow(a)
		end
	end, onReset = function() Binds.resetAll() end },
	{ id = "pad", title = "CONTROLLER", reset = { "pad." }, build = function()
		section("LOOK", "the right stick")
		slider({ key = "pad.sens", label = "LOOK SENSITIVITY", min = 0.2, max = 3, step = 0.05, fmt = times })
		slider({ key = "pad.ads", label = "AIM SENSITIVITY", sub = "multiplier while aiming down sights", min = 0.2, max = 2, step = 0.05, fmt = times })
		slider({ key = "pad.ySpeed", label = "VERTICAL SENSITIVITY", sub = "multiplier on up and down", min = 0.5, max = 1.5, step = 0.01, fmt = pct, scale = 100 })
		switch({ key = "pad.invert", label = "INVERT LOOK Y" })
		choice({ key = "pad.curve", label = "RESPONSE CURVE", options = { { "linear", "LINEAR" }, { "standard", "STANDARD" }, { "dynamic", "DYNAMIC" } } })
		slider({ key = "pad.dead", label = "INNER DEADZONE", sub = "how far the stick moves before you turn", min = 0, max = 0.4, step = 0.01, fmt = pct, scale = 100 })
		slider({ key = "pad.outer", label = "OUTER DEADZONE", sub = "how near the edge counts as all the way", min = 0, max = 0.3, step = 0.01, fmt = pct, scale = 100 })
		switch({ key = "pad.accel", label = "LOOK ACCELERATION", sub = "turning speeds up with the stick held all the way" })
		section("AIM ASSIST", "controller only, never a mouse; ranked holds it to 60%")
		switch({ key = "pad.assist", label = "AIM ASSIST" })
		slider({ key = "pad.assistK", label = "AIM ASSIST STRENGTH", min = 0.1, max = 1, step = 0.05, fmt = pct, scale = 100 })
		section("HOLD OR TOGGLE")
		local ht = { { false, "HOLD" }, { true, "TOGGLE" } }
		choice({ key = "pad.aimToggle", label = "AIM DOWN SIGHTS", options = ht })
		choice({ key = "pad.crouchToggle", label = "CROUCH", options = ht })
		choice({ key = "pad.sprintToggle", label = "SPRINT", options = ht })
		section("BUTTONS", ("select one, press %s, then press the new button. %s cancels"):format(Pad.short("ButtonA"), Pad.short("ButtonSelect")))
		for _, f in { { label = "MOVE", kb = "", pad = Pad.short("Thumbstick1") }, { label = "LOOK", kb = "", pad = Pad.short("Thumbstick2") },
			{ label = "JUMP", kb = "", pad = Pad.short("ButtonA") }, { label = "MENUS AND SETTINGS", kb = "", pad = Pad.short("ButtonSelect") },
			{ label = "BACK OUT OF A MENU", kb = "", pad = Pad.short("ButtonB") } } do fixedRow(f) end
		for _, a in Binds.ACTIONS do padRow(a) end
	end, onReset = function()
		-- (the controller column only: the keyboard's keys stay as they are)
		for _, a in Binds.ACTIONS do
			local b, d = Binds.get(a.id), Binds.default(a.id)
			if b[3] ~= d[3] then Settings.set("bind." .. a.id, table.concat({ b[1], b[2], d[3] }, "|")) end
		end
	end },
	{ id = "crosshair", title = "CROSSHAIR", reset = { "xh." }, build = function()
		preview()
		local pr = T.new("Frame", { Name = "Presets", BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 40), LayoutOrder = nextOrder() }, list)
		T.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, 8) }, pr)
		for i, p in XH_PRESETS do
			local b = T.new("TextButton", { Name = "Preset", LayoutOrder = i, AutoButtonColor = false, AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 30),
				BackgroundColor3 = T.TRACK, BorderSizePixel = 0, FontFace = T.FONT_BOLD, TextSize = 12, TextColor3 = T.TEXT, Text = p[1] }, pr)
			T.corner(b, 5)
			T.new("UIPadding", { PaddingLeft = UDim.new(0, 12), PaddingRight = UDim.new(0, 12) }, b)
			b.MouseButton1Click:Connect(function() XH.apply(p[2]) end)
		end
		choice({ key = "xh.style", label = "STYLE", options = { { "cross", "CROSS" }, { "dot", "DOT" }, { "circle", "CIRCLE" }, { "t", "T" } } })
		local sw = {}
		for _, h in XH.SWATCHES do table.insert(sw, { h, Color3.fromHex(h) }) end
		colours({ key = "xh.color", label = "COLOR", sub = "or a hex code, #RRGGBB", swatches = sw, hex = true })
		slider({ key = "xh.size", label = "SIZE", min = 1, max = 20, step = 1, fmt = px })
		slider({ key = "xh.thick", label = "THICKNESS", min = 1, max = 6, step = 1, fmt = px })
		slider({ key = "xh.gap", label = "GAP", min = 0, max = 20, step = 1, fmt = px })
		slider({ key = "xh.outline", label = "OUTLINE", min = 0, max = 3, step = 1, fmt = percentOff })
		slider({ key = "xh.dot", label = "DOT", min = 0, max = 6, step = 1, fmt = percentOff })
		slider({ key = "xh.alpha", label = "ALPHA", min = 0.1, max = 1, step = 0.05, fmt = pct, scale = 100 })
		switch({ key = "xh.spread", label = "DYNAMIC", sub = "the gap opens as your shots spread" })
		switch({ key = "xh.hideAim", label = "HIDE WHILE AIMING" })
		codeRow()
	end },
	{ id = "audio", title = "AUDIO", reset = { "vol.", "snd." }, build = function()
		section("VOLUME")
		local v = { min = 0, max = 150, step = 1, fmt = function(x) return ("%d%%"):format(x) end }
		local function vol(key, label, sub) slider({ key = key, label = label, sub = sub, min = v.min, max = v.max, step = v.step, fmt = v.fmt }) end
		vol("vol.master", "MASTER VOLUME")
		vol("vol.weapons", "WEAPON VOLUME", "guns, reloads, melee, hits")
		vol("vol.effects", "EFFECTS VOLUME", "footsteps, impacts, explosions")
		vol("vol.ui", "UI VOLUME", "menus and crates")
		section("FEEDBACK")
		switch({ key = "snd.hit", label = "HIT SOUND" })
		switch({ key = "snd.kill", label = "KILL SOUND" })
	end },
	{ id = "graphics", title = "GRAPHICS", reset = { "gfx.preset", "gfx.shadows", "gfx.particles", "gfx.bloom", "gfx.colour", "gfx.view", "gfx.othersKill", "gfx.othersSkin", "gfx.othersFinisher", "gfx.speedLines", "gfx.titles", "gfx.fps" }, build = function()
		local NAMES = { low = "LOW", med = "MEDIUM", high = "HIGH" }
		choice({ key = "gfx.preset", label = "GRAPHICS QUALITY", options = { { "auto", "AUTO" }, { "low", "LOW" }, { "med", "MEDIUM" }, { "high", "HIGH" } },
			subFn = function()
				local p = Settings.get("gfx.preset")
				if p == "auto" then return "auto: Roblox's graphics level, " .. (NAMES[Settings.autoLevel and Settings.autoLevel() or "high"] or "HIGH") end
				if p == "custom" then return "custom" end
				return "sets the options below"
			end })
		section("DETAIL")
		switch({ key = "gfx.shadows", label = "SHADOWS", marks = "gfx.preset" })
		slider({ key = "gfx.particles", label = "PARTICLE DETAIL", min = 0.25, max = 1, step = 0.05, fmt = pct, scale = 100, marks = "gfx.preset" })
		switch({ key = "gfx.bloom", label = "BLOOM", marks = "gfx.preset" })
		switch({ key = "gfx.colour", label = "COLOR CORRECTION" })
		switch({ key = "gfx.speedLines", label = "SPEED LINES", sub = "streaks and wind at speed" })
		choice({ key = "gfx.view", label = "RENDER DISTANCE", options = { { "near", "NEAR" }, { "normal", "NORMAL" }, { "far", "FAR" } }, marks = "gfx.preset" })
		section("OTHER PLAYERS")
		switch({ key = "gfx.othersKill", label = "OTHER PLAYERS' KILL EFFECTS" })
		switch({ key = "gfx.titles", label = "SHOW TITLES", sub = "card titles over players' heads" })
		switch({ key = "gfx.othersSkin", label = "OTHER PLAYERS' SKIN EFFECTS", sub = "animated wraps and flames" })
		switch({ key = "gfx.othersFinisher", label = "OTHER PLAYERS' FINISHERS" })
		section("PERFORMANCE")
		switch({ key = "gfx.fps", label = "SHOW FPS", sub = "and ping, top left" })
	end },
	{ id = "hud", title = "HUD", reset = { "hud." }, build = function()
		slider({ key = "hud.scale", label = "HUD SCALE", min = 0.75, max = 1.25, step = 0.05, fmt = pct, scale = 100 })
		section("ON SCREEN")
		switch({ key = "hud.dmg", label = "DAMAGE NUMBERS" })
		switch({ key = "hud.hits", label = "HIT MARKERS" })
		switch({ key = "hud.feed", label = "KILL FEED" })
		switch({ key = "hud.keys", label = "SHOW KEY HINTS", sub = "off: hold " .. Binds.label("keys") })
		switch({ key = "hud.othersLoot", label = "OTHER PLAYERS' CRATE OPENINGS" })
		switch({ key = "hud.quickJoin", label = "QUICK JOIN POP-UPS", sub = "when someone steps on a hub pad" })
		switch({ key = "hud.killcam", label = "KILLCAM", sub = "your last seconds from your killer's side" })
		section("COLOR")
		local cb = choice({ key = "hud.cb", label = "COLORBLIND MODE", sub = "", options = { { "off", "OFF" }, { "protan", "PROTAN" }, { "deutan", "DEUTAN" }, { "tritan", "TRITAN" } } })
		-- (the three team colours as they'll look, in the sub line's place)
		local sub = cb:FindFirstChild("Sub")
		local chips = {}
		for i = 1, 3 do
			local c = T.new("Frame", { Name = "Team" .. i, BorderSizePixel = 0, Position = UDim2.fromOffset(18 + (i - 1) * 22, 33), Size = UDim2.fromOffset(16, 14) }, cb)
			T.corner(c, 3)
			chips[i] = c
		end
		if sub then sub.Position = UDim2.fromOffset(18 + 3 * 22 + 4, 32); sub.Text = "team colors" end
		local function paint() for i, c in chips do c.BackgroundColor3 = Color3.fromHex(string.sub(Settings.teamHex(i), 2)) end end
		onKey("hud.cb", paint); paint()
		local en = {}
		for _, n in Settings.ENEMY_ORDER do table.insert(en, { n, Settings.ENEMY[n] }) end
		colours({ key = "hud.enemy", label = "ENEMY HIGHLIGHT COLOR", swatches = en })
	end },
	{ id = "privacy", title = "PRIVACY", reset = {}, build = function()
		switch({ label = "HIDE MY STATS", sub = "others see your name, rank and card only", attr = "StatsPrivate",
			get = function() return me:GetAttribute("StatsPrivate") == true end,
			flip = function()
				local fn = ReplicatedStorage:FindFirstChild("JankfireRemotes") and ReplicatedStorage.JankfireRemotes:FindFirstChild("Profile")
				if fn and fn:IsA("RemoteFunction") then
					local want = me:GetAttribute("StatsPrivate") ~= true
					task.spawn(function() pcall(function() fn:InvokeServer("private", want) end) end)
				end
			end })
		switch({ label = "SHARE MY CRATE OPENINGS", sub = "players near you see what you open", attr = "LootShowOpenings",
			get = function() return me:GetAttribute("LootShowOpenings") ~= false end,
			flip = function()
				local fn = ReplicatedStorage:FindFirstChild("JankfireRemotes") and ReplicatedStorage.JankfireRemotes:FindFirstChild("Loot")
				if fn and fn:IsA("RemoteFunction") then
					local want = me:GetAttribute("LootShowOpenings") == false
					task.spawn(function() pcall(function() fn:InvokeServer("setting", "showOpenings", want) end) end)
				end
			end })
	end, onReset = function()
		local rs = ReplicatedStorage:FindFirstChild("JankfireRemotes")
		local pf = rs and rs:FindFirstChild("Profile")
		local lf = rs and rs:FindFirstChild("Loot")
		task.spawn(function()
			if pf and me:GetAttribute("StatsPrivate") == true then pcall(function() pf:InvokeServer("private", false) end) end
			if lf and me:GetAttribute("LootShowOpenings") == false then pcall(function() lf:InvokeServer("setting", "showOpenings", true) end) end
		end)
	end },
	{ id = "touch", title = "TOUCH", reset = { "touch." }, visible = function()
		-- (TouchOn: TouchControls has the phone layout up, its StarterPlayer TouchForce test included, so the tab and the
		-- buttons always agree)
		return UIS.TouchEnabled or me:GetAttribute("TouchOn") == true or me:GetAttribute("TouchForce") == true
			or me:GetAttribute("SettingsAllTabs") == true
	end, build = function()
		UI.touchEditRow()
		slider({ key = "touch.sens", label = "TOUCH SENSITIVITY", min = 0.3, max = 3, step = 0.05, fmt = times })
		slider({ key = "touch.size", label = "BUTTON SIZE", sub = "on top of the device's own size", min = 0.7, max = 1.4, step = 0.05, fmt = pct, scale = 100 })
		slider({ key = "touch.assist", label = "AIM ASSIST", min = 0, max = 1.5, step = 0.05,
			fmt = function(v) return if v <= 0 then "OFF" else ("%.2fx"):format(v) end })
		slider({ key = "touch.alpha", label = "BUTTON OPACITY", min = 0.2, max = 1, step = 0.05, fmt = pct, scale = 100 })
		switch({ key = "touch.autofire", label = "AUTO FIRE", sub = "shoots when the crosshair is on someone" })
		switch({ key = "touch.aimToggle", label = "TOGGLE AIM DOWN SIGHTS", sub = "off: hold to aim" })
		switch({ key = "touch.lefty", label = "LEFT-HANDED LAYOUT" })
		for _, def in Settings.extra.touch or {} do
			if def.kind == "slider" then
				slider({ key = def.key, label = def.label, sub = def.sub, min = def.min, max = def.max, step = def.step,
					fmt = function(v) return (def.fmt or "%.2f"):format(v) end })
			elseif def.kind == "switch" then switch({ key = def.key, label = def.label, sub = def.sub })
			elseif def.kind == "choice" then choice({ key = def.key, label = def.label, sub = def.sub, options = def.options }) end
		end
	end },
}

-- ------------------------------------------------------------------ showing a tab
local function clearList()
	for _, c in list:GetChildren() do if not c:IsA("UIListLayout") and not c:IsA("UIPadding") then c:Destroy() end end
	table.clear(refreshers)
	table.clear(anyRefresh)
	table.clear(previewHolders)
	table.clear(capRefresh)
	order = 0
end
local resetArmed = 0
function UI.show(id)
	stopListening(false)
	local tab = nil
	for _, t in tabs do if t.id == id then tab = t end end
	if not tab then return end
	current = tab
	UI.tabId = id -- (a controller's bumpers step the tabs: PadNav.client)
	clearList()
	header.Text = tab.title
	message.Text = ""
	resetArmed = 0
	resetBtn.Text = "RESET TO DEFAULT"
	tab.build()
	list.CanvasPosition = Vector2.zero
	for tid, b in tabButtons do
		local on = tid == id
		b.btn.BackgroundTransparency = if on then 0 else 1
		b.bar.Visible = on
		b.label.TextColor3 = if on then T.TEXT else T.MUTED
	end
end

-- ------------------------------------------------------------------ the page
function UI.build(gui)
	scrim = T.new("Frame", { Name = "Scrim", BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 0.45, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), Visible = false }, gui)
	page = T.new("TextButton", { -- (a button so Modal can free the mouse from first person while it's open)
		Name = "Page", AutoButtonColor = false, Text = "", Modal = true, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(W, H), BackgroundColor3 = T.BG, BorderSizePixel = 0, Visible = false }, gui)
	T.corner(page, 8)
	T.edge(page)
	scale = T.new("UIScale", {}, page)
	-- the rail
	local rail = T.new("Frame", { Name = "Rail", BackgroundColor3 = Color3.fromRGB(12, 14, 17), BorderSizePixel = 0, Size = UDim2.new(0, RAIL, 1, 0) }, page)
	T.corner(rail, 8)
	T.new("Frame", { Name = "Square", BackgroundColor3 = rail.BackgroundColor3, BorderSizePixel = 0, Position = UDim2.new(1, -8, 0, 0), Size = UDim2.new(0, 8, 1, 0) }, rail)
	local title = T.text(rail, "Title", "SETTINGS", 20, T.TEXT, T.FONT_TITLE)
	title.Position = UDim2.fromOffset(24, 26); title.Size = UDim2.fromOffset(RAIL - 40, 26)
	T.new("Frame", { Name = "Rule", BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Position = UDim2.fromOffset(24, 60), Size = UDim2.fromOffset(32, 3) }, rail)
	local tabList = T.new("Frame", { Name = "Tabs", BackgroundTransparency = 1, Position = UDim2.fromOffset(12, 84), Size = UDim2.new(1, -24, 1, -150) }, rail)
	T.new("UIListLayout", { Padding = UDim.new(0, 4), SortOrder = Enum.SortOrder.LayoutOrder }, tabList)
	for i, t in tabs do
		local btn = T.new("TextButton", { Name = t.id, LayoutOrder = i, AutoButtonColor = false, Text = "", BackgroundColor3 = T.CARD, BackgroundTransparency = 1,
			BorderSizePixel = 0, Size = UDim2.new(1, 0, 0, 42) }, tabList)
		T.corner(btn, 6)
		local bar = T.new("Frame", { Name = "Bar", BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Position = UDim2.fromOffset(0, 11), Size = UDim2.fromOffset(3, 20), Visible = false }, btn)
		T.corner(bar, 2)
		local label = T.text(btn, "Label", t.title, 14, T.MUTED, T.FONT_BOLD)
		label.Position = UDim2.fromOffset(16, 0); label.Size = UDim2.new(1, -20, 1, 0)
		btn.MouseEnter:Connect(function() if current ~= t then label.TextColor3 = T.SOFT end end)
		btn.MouseLeave:Connect(function() if current ~= t then label.TextColor3 = T.MUTED end end)
		btn.MouseButton1Click:Connect(function() UI.show(t.id) end)
		tabButtons[t.id] = { btn = btn, bar = bar, label = label, tab = t }
	end
	statusText = T.text(rail, "Status", "", 11, T.DIM, T.FONT_BOLD)
	statusText.Position = UDim2.new(0, 24, 1, -56); statusText.Size = UDim2.new(1, -40, 0, 14)
	local closeHint = T.text(rail, "CloseHint", "", 11, T.DIM, T.FONT_BOLD)
	closeHint.Position = UDim2.new(0, 24, 1, -36); closeHint.Size = UDim2.new(1, -40, 0, 14)
	local function status()
		statusText.Text = if Settings.state == "cloud" then "SAVED TO YOUR ACCOUNT" elseif Settings.state == "loading" then "LOADING YOUR SETTINGS" else "KEPT FOR THIS SESSION"
		-- (a controller in your hands: B closes it, PadNav.client)
		closeHint.Text = ("%s TO CLOSE"):format(if Pad.on() then Pad.short("ButtonB") else string.upper(Binds.label("settings")))
	end
	Settings.loaded.Event:Connect(status)
	Pad.changed.Event:Connect(status)
	status()
	UI.status = status
	-- the content
	local content = T.new("Frame", { Name = "Content", BackgroundTransparency = 1, Position = UDim2.fromOffset(RAIL + 24, 0), Size = UDim2.new(1, -RAIL - 48, 1, 0) }, page)
	header = T.text(content, "Header", "", 20, T.TEXT, T.FONT_TITLE)
	header.Position = UDim2.fromOffset(0, 26); header.Size = UDim2.new(0.5, 0, 0, 26)
	message = T.text(content, "Message", "", 12, T.ACCENT, T.FONT_BOLD)
	message.Position = UDim2.fromOffset(0, 56); message.Size = UDim2.new(1, -60, 0, 16)
	message.TextTruncate = Enum.TextTruncate.AtEnd
	resetBtn = T.new("TextButton", { Name = "Reset", AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -44, 0, 24), AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 30), AutoButtonColor = false, BackgroundColor3 = T.TRACK, BorderSizePixel = 0, FontFace = T.FONT_BOLD, TextSize = 12,
		TextColor3 = T.TEXT, Text = "RESET TO DEFAULT" }, content)
	T.corner(resetBtn, 5)
	T.new("UIPadding", { PaddingLeft = UDim.new(0, 12), PaddingRight = UDim.new(0, 12) }, resetBtn)
	resetBtn.MouseButton1Click:Connect(function()
		if not current then return end
		if os.clock() - resetArmed > 3 then
			resetArmed = os.clock()
			resetBtn.Text = "CLICK AGAIN TO RESET"
			resetBtn.BackgroundColor3 = T.ACCENT; resetBtn.TextColor3 = T.INK
			task.delay(3, function()
				if os.clock() - resetArmed >= 3 then resetBtn.Text = "RESET TO DEFAULT"; resetBtn.BackgroundColor3 = T.TRACK; resetBtn.TextColor3 = T.TEXT end
			end)
			return
		end
		resetArmed = 0
		resetBtn.Text = "RESET TO DEFAULT"; resetBtn.BackgroundColor3 = T.TRACK; resetBtn.TextColor3 = T.TEXT
		if current.onReset then current.onReset() end
		if #current.reset > 0 then Settings.reset(current.reset) end
		say(current.title .. " BACK TO THE DEFAULTS")
	end)
	local close = T.new("TextButton", { Name = "Close", AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, 0, 0, 24), Size = UDim2.fromOffset(30, 30),
		AutoButtonColor = false, BackgroundColor3 = T.CARD, BorderSizePixel = 0, Text = "" }, content)
	T.corner(close, 5)
	local bars = {}
	for _, rot in { 45, -45 } do
		table.insert(bars, T.new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(14, 2), Rotation = rot, BackgroundColor3 = T.MUTED, BorderSizePixel = 0 }, close))
	end
	close.MouseEnter:Connect(function() close.BackgroundColor3 = T.CARD_HI; for _, b in bars do b.BackgroundColor3 = T.TEXT end end)
	close.MouseLeave:Connect(function() close.BackgroundColor3 = T.CARD; for _, b in bars do b.BackgroundColor3 = T.MUTED end end)
	close.MouseButton1Click:Connect(function() UI.setOpen(false) end)
	list = T.new("ScrollingFrame", { Name = "List", BackgroundTransparency = 1, BorderSizePixel = 0, Position = UDim2.fromOffset(0, 80), Size = UDim2.new(1, 0, 1, -96),
		CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollBarThickness = 4, ScrollBarImageColor3 = T.MUTED, ScrollingDirection = Enum.ScrollingDirection.Y,
		VerticalScrollBarInset = Enum.ScrollBarInset.ScrollBar }, content)
	T.new("UIListLayout", { Padding = UDim.new(0, 6), SortOrder = Enum.SortOrder.LayoutOrder }, list)
	T.new("UIPadding", { PaddingRight = UDim.new(0, 10), PaddingBottom = UDim.new(0, 12) }, list)

	-- dragging a slider
	UIS.InputChanged:Connect(function(io)
		if dragging and (io.UserInputType == Enum.UserInputType.MouseMovement or io.UserInputType == Enum.UserInputType.Touch) then dragging.setFromX(io.Position.X) end
	end)
	UIS.InputEnded:Connect(function(io)
		if io.UserInputType == Enum.UserInputType.MouseButton1 or io.UserInputType == Enum.UserInputType.Touch then dragging = nil end
	end)
	-- the preview's pulse
	RunService.RenderStepped:Connect(function(dt)
		if not page.Visible or not current or current.id ~= "crosshair" then return end
		pulseT += dt
		drawPreview()
	end)
	local function fit()
		local cam = workspace.CurrentCamera
		local vs = if cam then cam.ViewportSize else Vector2.new(1280, 720)
		scale.Scale = math.min(T.scaleNow(), vs.X * 0.96 / W, vs.Y * 0.92 / H)
	end
	UI.fit = fit
	if workspace.CurrentCamera then workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(fit) end
	fit()
	-- the touch rows the touch controls add later land in the tab if it's open
	Settings.rowAdded.Event:Connect(function(tab) if current and current.id == tab and page.Visible then UI.show(tab) end end)
	-- show only the tabs this device has
	for _, t in tabs do tabButtons[t.id].btn.Visible = t.visible == nil or t.visible() end
	UI.show("controls")
	-- (Studio tests: SettingsTest "tab:audio" shows a tab; opening is the SettingsOpen attribute, JankSettings)
	Settings.testHook.Event:Connect(function(op, rest)
		if op == "tab" then
			for _, t in tabs do tabButtons[t.id].btn.Visible = t.visible == nil or t.visible() end
			UI.show(rest)
		end
	end)
end

function UI.isOpen() return page ~= nil and page.Visible end
function UI.setOpen(on)
	if not page then return end
	if on then
		UI.fit()
		for _, t in tabs do tabButtons[t.id].btn.Visible = t.visible == nil or t.visible() end
		UI.status()
		if current then UI.show(current.id) end
	else
		stopListening(false)
		Settings.flush()
	end
	page.Visible = on
	scrim.Visible = on
	dragging = nil
end

return UI
