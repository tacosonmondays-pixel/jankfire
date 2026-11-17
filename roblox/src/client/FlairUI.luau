--!strict
-- the equip screen for kill effects, emotes and grapple skins (doc FLAIR.md). FlairUI.open(tab?) / close() / isOpen() / preview(id).
-- the loadout's KILL EFFECT · EMOTES button opens it (the loadout steps aside first); not mid-match, like the loadout.
-- left: the items (a grid of kill effects or grapples; or the emote wheel's 8 slots over the emotes). right: the world, with a
-- copy of your own avatar standing in front of you (client-only) playing whatever you point at: the kill effect on it
-- (real particles: a ViewportFrame can't draw them), or the emote. the server owns every pick (FlairServer): this asks.
-- the look is Theme.luau's: dark plates, white words, one amber accent for the one button that does something.
local Players = game:GetService("Players")
local UIS = game:GetService("UserInputService")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Flair = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Flair")) :: any
local KillFx = require(script.Parent:WaitForChild("KillFx")) :: any
local T = require(script.Parent:WaitForChild("Theme")) :: any
local MenuCursor = require(script.Parent:WaitForChild("MenuCursor")) :: any
local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")

local FlairUI = {}
local S = {
	open = false, tab = "kill", pick = { kill = "none", emote = "wave", grapple = "rope" } :: { [string]: string }, slot = 1,
	owned = { kill = {}, emote = {}, grapple = {} } :: { [string]: { [string]: boolean } }, tok = 0, hidden = {} :: { [ScreenGui]: boolean },
	cam = { active = false, closing = false, t0 = 0, dur = 0.5, from = CFrame.new(), to = CFrame.new(), saved = CFrame.new(), savedType = Enum.CameraType.Custom },
	spot = nil :: { s: Vector3, face: Vector3 }?, template = nil :: Model?, dummy = nil :: Model?, savedOpen = false,
	fake = nil :: Vector2?, -- (a phone-sized test box: FlairUI.fakeScreen)
}
local controls: any = nil
task.spawn(function()
	pcall(function() controls = require(me:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: any):GetControls() end)
end)

local function ask(...: any): any
	local r = ReplicatedStorage:WaitForChild("JankfireRemotes"):FindFirstChild("Flair") :: RemoteFunction?
	if not r then return { ok = false, why = "no server" } end
	local ok, res = pcall(r.InvokeServer, r, ...)
	return if ok and type(res) == "table" then res else { ok = false, why = "no answer" }
end
local function new(class: string, props: { [string]: any }, parent: Instance?): any return T.new(class, props, parent) end
local function label(parent: Instance, text: string, size: number, pos: UDim2, sz: UDim2, color: Color3?, font: Font?, align: Enum.TextXAlignment?): TextLabel
	return new("TextLabel", { BackgroundTransparency = 1, FontFace = font or T.FONT, TextSize = size, Text = text, Position = pos, Size = sz,
		TextColor3 = color or T.TEXT, TextXAlignment = align or Enum.TextXAlignment.Left, TextWrapped = true, ZIndex = 3 }, parent)
end

-- ------------------------------------------------------------------ the screen
-- two layouts on the same rules: the desktop's 1920 x 1080 stage, and a compact 960 x 440 one for phones and tablets
-- (the mobile session measured the big one at ~36 % on a phone: DONE ~18 pt). on the compact stage every tap target is at
-- least 52 design px (measured 17 Nov in an 844 x 390 box: DONE and tabs 46 pt, EQUIP 46, wheel slots 51, cards 144 x 149), the screen keeps to the device's safe area (ScreenInsets), and the
-- kill effect / grapple grids are three across. which one: a touch device (the touch-controls session's Keys.isTouch,
-- which tests can force with TouchForce; else touch and no keyboard) or a fake box (FlairUI.fakeScreen, tests).
-- a layout is built the first time it's needed
local gui = new("ScreenGui", { Name = "JankFlair", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 31,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling, Enabled = false }, pg)
-- (a full-screen button under everything: Modal frees the mouse from first person; dark on the left, clear on the right
-- where the preview stands)
local catcher = new("TextButton", { Text = "", AutoButtonColor = false, BackgroundColor3 = Color3.fromRGB(8, 9, 12),
	BackgroundTransparency = 0, Size = UDim2.fromScale(1, 1), Modal = true }, gui)
new("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(0.42, 0.35),
	NumberSequenceKeypoint.new(0.62, 1), NumberSequenceKeypoint.new(1, 1) }) }, catcher)
local guiUI = new("ScreenGui", { Name = "JankFlairUI", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 32,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling, Enabled = false, ScreenInsets = Enum.ScreenInsets.DeviceSafeInsets }, pg)
-- the room the screen has: the safe area, or a fake box the size of a phone (tests)
local box = new("Frame", { Name = "Box", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
	Size = UDim2.fromScale(1, 1), ClipsDescendants = false }, guiUI)

local DESK = {
	key = "desk", W = 1920, H = 1080,
	tabs = { y = 34, h = 60, font = 40, ruleY = 62, x = { kill = 60, emote = 400, grapple = 690 }, w = { kill = 320, emote = 270, grapple = 300 } },
	done = { 1700, 40, 160, 50, "DONE  [ESC]" }, save = { 1360, 100, 500, 22, 16 },
	panel = { 60, 130, 880, 900 },
	grid = { 20, 20, 840, 720, 196, 236, 12 }, equip = { 20, 800, 300, 64 }, note = { 340, 820, 520, 24, 16 },
	ring = { cx = 440, cy = 280, R = 196, cell = 100 },
	emotes = { 20, 560, 840, 190, 131, 190, 10 }, clear = { 336, 812, 170, 40 }, mnote = { 520, 820, 340, 24, 16 },
	name = { 1160, 880, 700, 54, 18 },
}
local PHONE = {
	key = "phone", W = 960, H = 440,
	tabs = { y = 5, h = 52, font = 26, ruleY = 46, x = { kill = 16, emote = 210, grapple = 356 }, w = { kill = 186, emote = 138, grapple = 160 } },
	done = { 836, 5, 112, 52, "DONE" }, save = { 576, 60, 372, 16, 12 },
	panel = { 16, 62, 548, 372 },
	grid = { 8, 8, 532, 298, 164, 170, 8 }, equip = { 8, 312, 200, 54 }, note = { 218, 330, 322, 20, 12 },
	row = { x = 8, y = 8, cell = 58, gap = 8 },
	emotes = { 8, 74, 532, 232, 164, 170, 8 }, clear = { 216, 312, 150, 54 }, mnote = { 376, 330, 164, 20, 12 },
	name = { 590, 352, 360, 30, 13 },
}

-- a flat button (the loadout's look): main = amber with dark words; chip/white = a dark card
type Btn = { face: TextButton, kind: string, enabled: boolean, base: Color3, set: (Btn, string, boolean?) -> () }
local function button(parent: Instance, text: string, kind: string, pos: UDim2, size: UDim2): Btn
	local base = if kind == "main" then T.ACCENT else T.CARD
	local face = new("TextButton", { AutoButtonColor = false, BackgroundColor3 = base, BorderSizePixel = 0, Position = pos, Size = size,
		FontFace = T.FONT_BOLD, TextSize = math.floor(size.Y.Offset * (if kind == "chip" then 0.4 else 0.34)), Text = text,
		TextColor3 = if kind == "main" then T.INK else T.TEXT, ZIndex = 4 }, parent)
	T.corner(face)
	if kind ~= "main" then T.edge(face) end
	local b: Btn = { face = face, kind = kind, enabled = true, base = base, set = nil :: any }
	face.MouseEnter:Connect(function() if b.enabled then face.BackgroundColor3 = b.base:Lerp(Color3.new(1, 1, 1), 0.14) end end)
	face.MouseLeave:Connect(function() face.BackgroundColor3 = b.base end)
	b.set = function(self: Btn, t: string, enabled: boolean?)
		self.face.Text = t
		self.enabled = enabled ~= false
		self.base = if self.kind == "main" and self.enabled then T.ACCENT else T.CARD
		self.face.BackgroundColor3 = self.base
		self.face.TextColor3 = if self.base == T.ACCENT then T.INK elseif self.enabled then T.TEXT else T.DIM
	end
	return b
end

-- a lock over an item you don't own: a small padlock drawn from frames
local function lock(parent: GuiObject, z: number)
	-- (a light dim, so you still see what it is, and a small padlock in the top-right corner, where a worn one has its
	-- mark: a lock in the middle covered the picture. 17 Nov, the main session)
	local veil = new("Frame", { Name = "Lock", BackgroundColor3 = Color3.fromRGB(8, 9, 12), BackgroundTransparency = 0.62, BorderSizePixel = 0,
		Size = UDim2.fromScale(1, 1), ZIndex = z }, parent)
	T.corner(veil, 6)
	local badge = new("Frame", { Name = "Badge", AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -5, 0, 5), Size = UDim2.fromOffset(22, 22),
		BackgroundColor3 = Color3.fromRGB(14, 15, 19), BackgroundTransparency = 0.15, BorderSizePixel = 0, ZIndex = z + 1 }, veil)
	T.corner(badge, 11)
	local body = new("Frame", { AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromOffset(11, 10), Size = UDim2.fromOffset(11, 8),
		BackgroundColor3 = T.SOFT, BorderSizePixel = 0, ZIndex = z + 2 }, badge)
	T.corner(body, 2)
	local shackle = new("Frame", { AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.fromOffset(11, 12), Size = UDim2.fromOffset(7, 8),
		BackgroundTransparency = 1, ZIndex = z + 2 }, badge)
	T.corner(shackle, 999)
	T.edge(shackle, T.SOFT, 0, 2)
	return veil
end

-- moving previews on the cards (the shop session's FlairAnim: kill effects as flipbooks once they have a sheet, emotes as
-- your own avatar). the owner, 17 Nov: "for kill effects in shop can they be small previews? same with in inv?"
local FlairAnimMod: any = nil
local function flairAnim(): any
	if FlairAnimMod == nil then
		local m = script.Parent:FindFirstChild("FlairAnim")
		local ok, r = false, nil
		if m then ok, r = pcall(require, m) end
		FlairAnimMod = if ok and type(r) == "table" then r else false
	end
	return if FlairAnimMod then FlairAnimMod else nil
end

-- a card: the drawn tile, the name, the rarity
type Card = { id: string, t: string, btn: TextButton, st: UIStroke, tag: TextLabel, lockF: Frame?, pic: Frame }
local function card(parent: Instance, t: string, id: string, w: number, h: number, order: number): Card
	local i = Flair.info(t, id)
	local btn = new("TextButton", { Text = "", AutoButtonColor = false, BackgroundColor3 = T.CARD, BorderSizePixel = 0,
		Size = UDim2.fromOffset(w, h), LayoutOrder = order, ZIndex = 3 }, parent)
	T.corner(btn, 8)
	local st = T.edge(btn)
	local ph = h - 62
	local pic = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(6, 6), Size = UDim2.fromOffset(w - 12, ph), ZIndex = 4 }, btn)
	Flair.picture(t, id, pic)
	if t == "kill" or t == "emote" then
		local fa = flairAnim()
		if fa then pcall(fa.attach, pic, t, id) end -- (nil when there's nothing to move yet: the still tile stays)
	end
	local nm = label(btn, string.upper(i.name), 17, UDim2.fromOffset(10, ph + 10), UDim2.fromOffset(w - 20, 22), T.TEXT, T.FONT_BOLD)
	nm.ZIndex = 6; nm.TextScaled = true
	new("UITextSizeConstraint", { MaxTextSize = 17 }, nm)
	local chip = new("Frame", { BackgroundColor3 = Flair.RARITY_COLOR[i.rarity] or T.MUTED, BorderSizePixel = 0, Position = UDim2.fromOffset(10, ph + 38),
		Size = UDim2.fromOffset(8, 8), ZIndex = 6 }, btn)
	T.corner(chip, 2)
	local rar = label(btn, string.upper(i.rarity), 12, UDim2.fromOffset(24, ph + 33), UDim2.fromOffset(w - 34, 18), T.MUTED, T.FONT_BOLD)
	rar.ZIndex = 6
	-- (worn: "EQUIPPED" over the rarity's place on the right)
	local tag = label(btn, "", 12, UDim2.fromOffset(10, ph + 33), UDim2.fromOffset(w - 20, 18), T.ACCENT, T.FONT_BOLD, Enum.TextXAlignment.Right)
	tag.ZIndex = 6
	local c: Card = { id = id, t = t, btn = btn, st = st, tag = tag, lockF = nil, pic = pic }
	btn.MouseEnter:Connect(function() btn.BackgroundColor3 = T.CARD_HI end)
	btn.MouseLeave:Connect(function() btn.BackgroundColor3 = T.CARD end)
	return c
end

-- ------------------------------------------------------------------ a layout: tabs, the panel and its three tabs' contents
-- (what a press does is shared by both layouts: set below)
local onTab: (string) -> () = function() end
local onPick: (string, string) -> () = function() end
local onSlot: (number) -> () = function() end
local onEquip: (string) -> () = function() end
local onClear: () -> () = function() end

local function at(r: { any }): (UDim2, UDim2) return UDim2.fromOffset(r[1], r[2]), UDim2.fromOffset(r[3], r[4]) end
local function grid(parent: Instance, g: { number }): ScrollingFrame
	local sf = new("ScrollingFrame", { BackgroundTransparency = 1, BorderSizePixel = 0, Position = UDim2.fromOffset(g[1], g[2]), Size = UDim2.fromOffset(g[3], g[4]),
		CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollingDirection = Enum.ScrollingDirection.Y,
		ScrollBarThickness = 6, ScrollBarImageColor3 = T.DIM, ZIndex = 3 }, parent)
	new("UIGridLayout", { CellSize = UDim2.fromOffset(g[5], g[6]), CellPadding = UDim2.fromOffset(g[7], g[7]), SortOrder = Enum.SortOrder.LayoutOrder }, sf)
	new("UIPadding", { PaddingTop = UDim.new(0, 4), PaddingLeft = UDim.new(0, 4) }, sf)
	return sf
end
local function slotCell(parent: Instance, i: number, pos: UDim2, cell: number, anchor: Vector2): any
	local btn = new("TextButton", { Text = "", AutoButtonColor = false, AnchorPoint = anchor, Position = pos, Size = UDim2.fromOffset(cell, cell),
		BackgroundColor3 = T.CARD, BorderSizePixel = 0, ZIndex = 3 }, parent)
	T.corner(btn, 10)
	local st = T.edge(btn)
	local pic = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(5, 5), Size = UDim2.new(1, -10, 1, -10), ZIndex = 4 }, btn)
	local empty = new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(22, 22),
		BackgroundTransparency = 1, ZIndex = 4 }, btn)
	T.corner(empty, 999)
	T.edge(empty, T.DIM, 0.4, 2)
	local num = label(btn, tostring(i), 12, UDim2.fromOffset(6, 4), UDim2.fromOffset(20, 14), T.DIM, T.FONT_BOLD)
	num.ZIndex = 6
	btn.MouseButton1Click:Connect(function() onSlot(i) end)
	return { btn = btn, st = st, pic = pic, empty = empty, id = "" }
end

local function build(L: any): any
	local V: any = { L = L }
	local stage = new("Frame", { Name = L.key, BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(L.W, L.H), Visible = false }, box)
	V.stage = stage
	V.scale = new("UIScale", {}, stage)
	-- the three tabs, as the title
	V.tabs = {}
	for _, t in { "kill", "emote", "grapple" } do
		local b = new("TextButton", { AutoButtonColor = false, BackgroundTransparency = 1, Position = UDim2.fromOffset(L.tabs.x[t], L.tabs.y),
			Size = UDim2.fromOffset(L.tabs.w[t], L.tabs.h), FontFace = T.FONT_TITLE, TextSize = L.tabs.font,
			Text = ({ kill = "KILL EFFECT", emote = "EMOTES", grapple = "GRAPPLE" })[t],
			TextColor3 = T.TEXT, TextXAlignment = Enum.TextXAlignment.Left, ZIndex = 3 }, stage)
		local rule = new("Frame", { BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Position = UDim2.fromOffset(2, L.tabs.ruleY), Size = UDim2.fromOffset(44, 3), ZIndex = 3 }, b)
		V.tabs[t] = { b = b, rule = rule }
		b.MouseButton1Click:Connect(function() onTab(t) end)
	end
	local p, s = at(L.done)
	V.done = button(stage, L.done[5], "white", p, s)
	V.done.face.MouseButton1Click:Connect(function() FlairUI.close() end)
	p, s = at(L.save)
	V.saveLbl = label(stage, "", L.save[5], p, s, T.MUTED, nil, Enum.TextXAlignment.Right)
	-- the panel on the left
	p, s = at(L.panel)
	local panel = new("Frame", { BackgroundColor3 = T.BG, BackgroundTransparency = 0.12, BorderSizePixel = 0, Position = p, Size = s, ZIndex = 2 }, stage)
	T.corner(panel, 8); T.edge(panel)
	-- the name of what the preview shows (bottom right, over the world)
	local n = L.name
	local nameBox = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(n[1], n[2]), Size = UDim2.fromOffset(n[3], n[4] * 2.6) }, stage)
	V.bigName = label(nameBox, "", n[4], UDim2.fromOffset(0, 0), UDim2.fromOffset(n[3], n[4] * 1.2), T.TEXT, T.FONT_TITLE)
	V.bigName.TextStrokeTransparency = 0.7
	V.bigRule = new("Frame", { BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Position = UDim2.fromOffset(2, n[4] * 1.3), Size = UDim2.fromOffset(44, 3), ZIndex = 3 }, nameBox)
	V.bigSub = label(nameBox, "", n[5], UDim2.fromOffset(2, n[4] * 1.3 + 10), UDim2.fromOffset(n[3], n[5] + 6), T.SOFT, T.FONT_BOLD)
	V.bigSub.TextStrokeTransparency = 0.75

	-- kill effects and grapples: a grid of cards, EQUIP under it
	for _, t in { "kill", "grapple" } do
		local X = { frame = new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = 2, Visible = false }, panel), cards = {} }
		local g = grid(X.frame, L.grid)
		for i, id in Flair.ORDER[t] do
			local c = card(g, t, id, L.grid[5], L.grid[6], i)
			c.btn.MouseButton1Click:Connect(function() onPick(t, id) end)
			table.insert(X.cards, c)
		end
		p, s = at(L.equip)
		X.equip = button(X.frame, "EQUIP", "main", p, s)
		X.equip.face.MouseButton1Click:Connect(function() onEquip(t) end)
		p, s = at(L.note)
		X.note = label(X.frame, "", L.note[5], p, s, T.MUTED, T.FONT_BOLD)
		if t == "kill" then V.K = X else V.G = X end
	end

	-- emotes: the wheel's 8 slots (a ring on the desktop, a row on a phone) over the emotes
	local M = { frame = new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = 2, Visible = false }, panel), slots = {}, cards = {} }
	if L.ring then
		local r = L.ring
		local ring = new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromOffset(r.cx, r.cy), Size = UDim2.fromOffset(r.R * 2 + r.cell + 24, r.R * 2 + r.cell + 24),
			BackgroundColor3 = T.CARD, BackgroundTransparency = 0.6, BorderSizePixel = 0, ZIndex = 2 }, M.frame)
		T.corner(ring, 999)
		M.centre = label(M.frame, "", 22, UDim2.fromOffset(r.cx - 120, r.cy - 30), UDim2.fromOffset(240, 30), T.TEXT, T.FONT_TITLE, Enum.TextXAlignment.Center)
		M.centreSub = label(M.frame, "", 14, UDim2.fromOffset(r.cx - 120, r.cy + 4), UDim2.fromOffset(240, 20), T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center)
		for i = 1, Flair.SLOTS do
			local a = math.rad(-90 + (i - 1) * 360 / Flair.SLOTS)
			M.slots[i] = slotCell(M.frame, i, UDim2.fromOffset(r.cx + math.cos(a) * r.R, r.cy + math.sin(a) * r.R), r.cell, Vector2.new(0.5, 0.5))
		end
	else
		local r = L.row
		for i = 1, Flair.SLOTS do
			M.slots[i] = slotCell(M.frame, i, UDim2.fromOffset(r.x + (i - 1) * (r.cell + r.gap), r.y), r.cell, Vector2.zero)
		end
	end
	local e = L.emotes
	local holder: Instance
	if L.ring then
		-- (one row that scrolls sideways: ten free emotes since 17 Nov, six fit)
		holder = new("ScrollingFrame", { BackgroundTransparency = 1, BorderSizePixel = 0, Position = UDim2.fromOffset(e[1], e[2]), Size = UDim2.fromOffset(e[3], e[4] + 12),
			CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.X, ScrollingDirection = Enum.ScrollingDirection.X,
			ScrollBarThickness = 6, ScrollBarImageColor3 = T.DIM, VerticalScrollBarInset = Enum.ScrollBarInset.None, ZIndex = 3 }, M.frame)
		new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, e[7]), SortOrder = Enum.SortOrder.LayoutOrder }, holder)
		-- (the mouse wheel moves a sideways row too: a wheel over it scrolls it across, a card at a time)
		local row = holder :: ScrollingFrame
		row.InputChanged:Connect(function(io: InputObject)
			if io.UserInputType ~= Enum.UserInputType.MouseWheel then return end
			local most = math.max(0, row.AbsoluteCanvasSize.X - row.AbsoluteWindowSize.X)
			local step = (e[5] + e[7]) * (row.AbsoluteSize.X / math.max(1, e[3]))
			row.CanvasPosition = Vector2.new(math.clamp(row.CanvasPosition.X - io.Position.Z * step, 0, most), 0)
		end)
	else
		holder = grid(M.frame, e)
	end
	for i, id in Flair.ORDER.emote do
		local c = card(holder, "emote", id, e[5], e[6], i)
		c.btn.MouseButton1Click:Connect(function() onPick("emote", id) end)
		table.insert(M.cards, c)
	end
	p, s = at(L.equip)
	M.equip = button(M.frame, "PUT IN SLOT 1", "main", p, s)
	M.equip.face.MouseButton1Click:Connect(function() onEquip("emote") end)
	p, s = at(L.clear)
	M.clear = button(M.frame, "EMPTY SLOT", "chip", p, s)
	M.clear.face.MouseButton1Click:Connect(function() onClear() end)
	p, s = at(L.mnote)
	M.note = label(M.frame, "", L.mnote[5], p, s, T.MUTED, T.FONT_BOLD)
	V.M = M
	return V
end

local VIEWS: { [string]: any } = {}
local V: any = nil -- the layout on screen
local KeysMod: any = nil
local function touchDevice(): boolean
	if KeysMod == nil then
		local m = script.Parent:FindFirstChild("Keys")
		local ok, res = false, nil
		if m and m:IsA("ModuleScript") then ok, res = pcall(require, m) end
		KeysMod = if ok and type(res) == "table" and type(res.isTouch) == "function" then res else false
	end
	if KeysMod then
		local ok, yes = pcall(KeysMod.isTouch)
		if ok then return yes == true end
	end
	return UIS.TouchEnabled and not UIS.KeyboardEnabled
end
local function useView()
	local L = if S.fake or touchDevice() then PHONE else DESK
	if not VIEWS[L.key] then VIEWS[L.key] = build(L) end
	V = VIEWS[L.key]
	for _, v in VIEWS do v.stage.Visible = v == V end
end
local function fit()
	if not V then return end
	local s = box.AbsoluteSize
	if s.X < 2 or s.Y < 2 then return end
	V.scale.Scale = math.min(s.X / V.L.W, s.Y / V.L.H)
end

-- ------------------------------------------------------------------ what's on screen
local function slots(): { string } return Flair.slotsOf(me:GetAttribute("Emotes")) end
local function wornKill(): string
	local k = me:GetAttribute("KillFx")
	return if type(k) == "string" and Flair.info("kill", k) then k else "none"
end
local function wornGrapple(): string
	local g = me:GetAttribute("Grapple")
	return if type(g) == "string" and Flair.info("grapple", g) then g else "rope"
end
local function owns(t: string, id: string): boolean return Flair.isFree(t, id) or S.owned[t][id] == true end

local function paintCard(c: Card, selected: boolean, worn: boolean)
	c.st.Color = if selected then T.ACCENT else T.EDGE
	c.st.Transparency = if selected then 0 else T.EDGE_A
	c.st.Thickness = if selected then 2 else 1
	c.tag.Text = if worn then "EQUIPPED" else ""
	local mine = owns(c.t, c.id)
	if not mine and not c.lockF then c.lockF = lock(c.pic, 8) end
	if c.lockF then c.lockF.Visible = not mine end
end

local function refresh()
	if not V then return end
	local K, M, G = V.K, V.M, V.G
	for t, x in V.tabs do
		x.b.TextColor3 = if S.tab == t then T.TEXT else T.DIM
		x.rule.Visible = S.tab == t
	end
	K.frame.Visible = S.tab == "kill"
	M.frame.Visible = S.tab == "emote"
	G.frame.Visible = S.tab == "grapple"
	local wg = wornGrapple()
	for _, c in G.cards do paintCard(c, c.id == S.pick.grapple, c.id == wg) end
	local gid = S.pick.grapple
	if not owns("grapple", gid) then G.equip:set("LOCKED", false); G.note.Text = "FROM DUFFEL BAGS AND THE SHOP"
	elseif gid == wg then G.equip:set("EQUIPPED", false); G.note.Text = ""
	else G.equip:set("EQUIP", true); G.note.Text = "" end
	local worn = wornKill()
	for _, c in K.cards do paintCard(c, c.id == S.pick.kill, c.id == worn) end
	local kid = S.pick.kill
	if not owns("kill", kid) then K.equip:set("LOCKED", false); K.note.Text = "FROM DUFFEL BAGS AND THE SHOP"
	elseif kid == worn then K.equip:set("EQUIPPED", false); K.note.Text = ""
	else K.equip:set("EQUIP", true); K.note.Text = "" end
	local sl = slots()
	for i, s in M.slots do
		if s.id ~= sl[i] then
			s.id = sl[i]
			for _, c in s.pic:GetChildren() do c:Destroy() end
			if s.id ~= "" then Flair.picture("emote", s.id, s.pic) end
			s.empty.Visible = s.id == ""
		end
		local on = i == S.slot
		s.st.Color = if on then T.ACCENT else T.EDGE
		s.st.Transparency = if on then 0 else T.EDGE_A
		s.st.Thickness = if on then 2 else 1
	end
	for _, c in M.cards do paintCard(c, c.id == S.pick.emote, table.find(sl, c.id) ~= nil) end
	local inSlot = Flair.info("emote", sl[S.slot])
	if M.centre then
		M.centre.Text = if inSlot then string.upper(inSlot.name) else ""
		M.centreSub.Text = "SLOT " .. S.slot
	end
	local eid = S.pick.emote
	if not owns("emote", eid) then M.equip:set("LOCKED", false); M.note.Text = "FROM DUFFEL BAGS AND THE SHOP"
	elseif sl[S.slot] == eid then M.equip:set("IN SLOT " .. S.slot, false); M.note.Text = ""
	else M.equip:set("PUT IN SLOT " .. S.slot, true); M.note.Text = "" end
	M.clear:set("EMPTY SLOT", sl[S.slot] ~= "")
	-- the big name over the world
	local i = Flair.info(S.tab, S.pick[S.tab])
	V.bigName.Text = if i then string.upper(i.name) else ""
	V.bigRule.BackgroundColor3 = if i then (Flair.RARITY_COLOR[i.rarity] or T.ACCENT) else T.ACCENT
	V.bigSub.Text = if i then (string.upper(i.rarity) .. "  ·  " .. string.upper(Flair.TYPE_NAMES[S.tab])) else ""
	local sv = me:GetAttribute("FlairSave")
	V.saveLbl.Text = if sv == "off" then "NOT SAVING THIS SESSION" elseif sv == "lost" then "SAVED ELSEWHERE: CHANGES HERE WON'T KEEP" else ""
end

local function fetch()
	local res = ask("state")
	if not res.ok then return end
	for _, t in Flair.TYPES do
		S.owned[t] = {}
		for _, id in (res.owned and res.owned[t] or {}) do S.owned[t][id] = true end
	end
end

-- ------------------------------------------------------------------ the stand-in: a copy of you in the world
local function myParts(): (Model?, BasePart?, Humanoid?)
	local ch = me.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	return ch, root, hum
end
-- where it stands: 7 studs off in the most open direction (yours first), on the floor
local function findSpot(): { s: Vector3, face: Vector3 }?
	local ch, root = myParts()
	if not ch or not root then return nil end
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { ch }
	local look = workspace.CurrentCamera.CFrame.LookVector
	local base = Vector3.new(look.X, 0, look.Z)
	base = if base.Magnitude > 1e-3 then base.Unit else Vector3.new(0, 0, -1)
	local from = root.Position + Vector3.new(0, 1, 0)
	-- (not with one of the hub's holograms behind it: the loadout one floats just over heads, and seen past the copy
	-- of you it looks like a gun floating on it. the holograms' places are the parts tagged HubHolo, HubHolo.client)
	local holos = game:GetService("CollectionService"):GetTagged("HubHolo")
	local function holoBehind(d: Vector3): boolean
		for _, h in holos do
			if h:IsA("BasePart") then
				local v = (h.Position - root.Position) * Vector3.new(1, 0, 1)
				local along = v:Dot(d)
				local r = tonumber(h:GetAttribute("Radius")) or 3
				if along > 2 and along < 45 and (v - d * along).Magnitude < r + 4 then return true end
			end
		end
		return false
	end
	for pass = 1, 2 do
		for k = 0, 7 do
			local a = math.rad(({ 0, 45, -45, 90, -90, 135, -135, 180 })[k + 1])
			local d = CFrame.fromAxisAngle(Vector3.yAxis, a):VectorToWorldSpace(base)
			if (pass == 2 or not holoBehind(d)) and not workspace:Raycast(from, d * 11, params) then
				local floor = workspace:Raycast(root.Position + d * 7 + Vector3.new(0, 3, 0), Vector3.new(0, -12, 0), params)
				if floor then return { s = floor.Position, face = -d } end
			end
		end
	end
	return { s = root.Position + base * 6 - Vector3.new(0, 3, 0), face = -base }
end
local function makeTemplate(): Model?
	local ch = myParts()
	if not ch then return nil end
	local was = ch.Archivable
	ch.Archivable = true
	local ok, c = pcall(function() return ch:Clone() end)
	ch.Archivable = was
	if not ok or not c then return nil end
	for _, d in c:GetDescendants() do
		if d:IsA("LuaSourceContainer") or d:IsA("Tool") or d:IsA("ForceField") or d.Name == "HeldWeapon" or d:IsA("Sound") then d:Destroy()
		elseif d:IsA("BasePart") then
			d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.LocalTransparencyModifier = 0
		elseif d:IsA("Decal") then (d :: any).LocalTransparencyModifier = 0 end
	end
	for _, d in c:GetChildren() do if d:IsA("Model") then d:Destroy() end end -- (gun copies, hats on guns)
	local hum = c:FindFirstChildOfClass("Humanoid")
	if hum then
		hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
		hum.EvaluateStateMachine = false
		hum.BreakJointsOnDeath = false
	end
	c.Name = "JankFlairStandIn"
	return c
end
local function standIn(anchoredAll: boolean): Model?
	if S.dummy then S.dummy:Destroy(); S.dummy = nil end
	local tpl, sp = S.template, S.spot
	if not tpl or not sp then return nil end
	local m = tpl:Clone()
	local root = m:FindFirstChild("HumanoidRootPart") :: BasePart?
	local hum = m:FindFirstChildOfClass("Humanoid")
	if not root or not hum then m:Destroy(); return nil end
	local h = hum.HipHeight + root.Size.Y / 2
	m:PivotTo(CFrame.lookAt(sp.s + Vector3.new(0, h, 0), sp.s + Vector3.new(0, h, 0) + sp.face))
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then d.Anchored = anchoredAll or d == root end
	end
	m.Parent = workspace
	S.dummy = m
	return m
end

-- the camera: from a little to the side, the stand-in on the right of the screen (the panel covers the left)
local function camTarget(): CFrame?
	local sp = S.spot
	if not sp then return nil end
	local focus = sp.s + Vector3.new(0, 2.7, 0)
	local side = sp.face:Cross(Vector3.yAxis)
	local eye = focus + sp.face * 8.2 - side * 2.4 + Vector3.new(0, 0.6, 0)
	return CFrame.lookAt(eye, focus) * CFrame.Angles(0, math.rad(22), 0)
end
RunService:BindToRenderStep("JankFlairCam", Enum.RenderPriority.Camera.Value + 7, function()
	local c = S.cam
	if not c.active then return end
	local cam = workspace.CurrentCamera :: Camera
	local u = math.clamp((os.clock() - c.t0) / c.dur, 0, 1)
	u = 1 - (1 - u) ^ 3
	if c.closing then
		local ch, root = myParts()
		local h = ch and ch:FindFirstChild("Head") :: BasePart?
		local back = if h and c.savedType ~= Enum.CameraType.Scriptable then c.saved.Rotation + h.Position + Vector3.new(0, 0.2, 0) else c.saved
		cam.CFrame = c.from:Lerp(back, u)
		if u >= 1 then
			c.active, c.closing = false, false
			cam.CameraType = if c.savedType == Enum.CameraType.Scriptable then Enum.CameraType.Custom else c.savedType
		end
		local _ = root
	else
		cam.CameraType = Enum.CameraType.Scriptable
		local drift = CFrame.Angles(math.sin(os.clock() * 0.4) * 0.004, math.sin(os.clock() * 0.27) * 0.008, 0)
		cam.CFrame = c.from:Lerp(c.to, u) * drift
	end
end)

-- the preview, over and over while the screen is up: a kill effect on the stand-in, or an emote
local function previewLoop()
	S.tok += 1
	local tok = S.tok
	task.spawn(function()
		while S.open and S.tok == tok do
			local t, id = S.tab, S.pick[S.tab]
			if t == "kill" then
				local m = standIn(true)
				if not m then return end
				task.wait(0.55)
				if not S.open or S.tok ~= tok then break end
				if id == "none" then
					-- the default: it falls apart, as bodies always have
					for _, d in m:GetDescendants() do
						if d:IsA("AnimationConstraint") or d:IsA("Motor6D") then d:Destroy()
						elseif d:IsA("BasePart") then
							d.Anchored = false
							d.AssemblyLinearVelocity = Vector3.new(math.random() * 8 - 4, math.random() * 6, math.random() * 8 - 4)
						end
					end
					task.wait(1.6)
				else
					KillFx.play(m, id, { preview = true })
					task.wait((Flair.info("kill", id).dur or 1) + 0.9)
				end
			elseif t == "grapple" then
				-- a rope from the stand-in's right hand up past its shoulder to a point overhead, the skin's head on the end
				-- (shared/GrappleLook.luau draws it, the grapple look's own module; a plain cable if it isn't in yet)
				local m = standIn(true)
				if not m then return end
				local hand = m:FindFirstChild("RightHand") :: BasePart?
				local a0 = hand and (hand:FindFirstChild("RightGripAttachment") or hand:FindFirstChildWhichIsA("Attachment")) :: Attachment?
				local sp = S.spot
				local cleanup: (() -> ())? = nil
				if a0 and sp then
					local side = sp.face:Cross(Vector3.yAxis)
					local to = a0.WorldPosition + Vector3.new(0, 7.5, 0) - sp.face * 3 + side * 3
					local mod = ReplicatedStorage.Jankfire:FindFirstChild("GrappleLook")
					local ok, GL = false, nil
					if mod then ok, GL = pcall(require, mod) end
					if ok and type(GL) == "table" and type((GL :: any).preview) == "function" then
						local ok2, c = pcall((GL :: any).preview, a0, to, id)
						if ok2 and type(c) == "function" then cleanup = c end
					else
						local a1 = Instance.new("Attachment")
						a1.WorldPosition = to
						a1.Parent = workspace.Terrain
						local b = Instance.new("Beam")
						b.Attachment0 = a0; b.Attachment1 = a1; b.Width0 = 0.25; b.Width1 = 0.25; b.FaceCamera = true; b.Segments = 1
						b.Color = ColorSequence.new(Color3.fromRGB(236, 238, 242), Color3.fromRGB(176, 182, 192))
						b.Parent = workspace.Terrain
						cleanup = function() b:Destroy(); a1:Destroy() end
					end
				end
				while S.open and S.tok == tok do task.wait(0.1) end
				if cleanup then pcall(cleanup) end
			else
				local m = standIn(false)
				if not m then return end
				local e = Flair.info("emote", id)
				local hum = m:FindFirstChildOfClass("Humanoid")
				local an = hum and hum:FindFirstChildOfClass("Animator")
				if e and an and e.anim ~= "rbxassetid://0" then
					task.wait(0.25)
					local a = Instance.new("Animation")
					a.AnimationId = e.anim
					local ok, tr = pcall(an.LoadAnimation, an, a)
					if ok and tr then
						tr.Priority = Enum.AnimationPriority.Action4
						tr.Looped = false
						tr:Play(0.3)
						local t0 = os.clock()
						local len = if e.loop then e.len * 2 else e.len + 3 -- (a one-shot ends on the track's own time, below)
						while S.open and S.tok == tok and os.clock() - t0 < len do
							if e.loop and not tr.IsPlaying then tr:Play(0.3) end
							if not e.loop and (tr.TimePosition >= e.len - 0.35 or (os.clock() - t0 > 1 and not tr.IsPlaying)) then break end
							task.wait(0.05)
						end
						tr:Stop(0.35)
					end
					task.wait(0.7)
				else
					task.wait(1)
				end
			end
		end
	end)
end

-- ------------------------------------------------------------------ open / close
local function canOpen(): boolean
	if me:GetAttribute("Zone") == "match" then return false end
	local _, root, hum = myParts()
	return root ~= nil and hum ~= nil and hum.Health > 0
end

function FlairUI.isOpen(): boolean return S.open end

-- home: the camera to come back to, when a screen that had the camera opens this one (the loadout's button passes its own
-- saved view: at that moment the loadout's camera is still flying home, and coming back to it put the camera out at the
-- loadout's showcase spot after DONE, so first person's gun was hidden until it got back. 17 Nov, the owner: "when you go
-- to loadout and kill effects then leave it it renders your gun away for a second")
function FlairUI.open(tab: string?, home: CFrame?)
	if tab == "kill" or tab == "emote" or tab == "grapple" then S.tab = tab end
	if S.open then refresh(); previewLoop(); return end
	if not canOpen() then return end
	if me:GetAttribute("LoadoutOpen") == true then return end -- (another screen is up)
	S.spot = findSpot()
	S.template = makeTemplate()
	local to = camTarget()
	if not to or not S.template then return end
	S.open = true
	S.savedOpen = false
	me:SetAttribute("LoadoutOpen", true)
	MenuCursor.set("flair", true, function() return S.open end)
	S.pick.kill = wornKill()
	local sl = slots()
	S.pick.emote = if sl[S.slot] ~= "" then sl[S.slot] else Flair.ORDER.emote[1]
	S.pick.grapple = wornGrapple()
	table.clear(S.hidden)
	for _, g in pg:GetChildren() do
		if g:IsA("ScreenGui") and g ~= gui and g ~= guiUI and g.Enabled then S.hidden[g] = true; g.Enabled = false end
	end
	useView()
	fit()
	refresh()
	gui.Enabled = true
	guiUI.Enabled = true
	catcher.BackgroundTransparency = 1
	T.tween(catcher, 0.35, { BackgroundTransparency = 0 })
	local cam = workspace.CurrentCamera :: Camera
	local c = S.cam
	c.saved, c.savedType = cam.CFrame, cam.CameraType
	if home then
		c.saved, c.savedType = home, Enum.CameraType.Custom
	elseif cam.CameraType == Enum.CameraType.Scriptable then
		-- (some other screen's camera is out: come back to your own eyes, facing the way you face)
		local ch, root = myParts()
		local h = ch and ch:FindFirstChild("Head") :: BasePart?
		if h and root then c.saved, c.savedType = CFrame.lookAt(h.Position, h.Position + root.CFrame.LookVector), Enum.CameraType.Custom end
	end
	c.from, c.to, c.t0, c.dur, c.closing, c.active = cam.CFrame, to, os.clock(), 0.55, false, true
	if controls then pcall(function() controls:Disable() end) end
	task.spawn(function() fetch(); if S.open then refresh() end end)
	previewLoop()
end

function FlairUI.close()
	if not S.open then return end
	S.open = false
	S.tok += 1
	gui.Enabled = false
	guiUI.Enabled = false
	MenuCursor.set("flair", false)
	me:SetAttribute("LoadoutOpen", false)
	for g in S.hidden do if g.Parent then g.Enabled = true end end
	table.clear(S.hidden)
	local cam = workspace.CurrentCamera :: Camera
	local c = S.cam
	c.from, c.t0, c.dur, c.closing = cam.CFrame, os.clock(), 0.35, true
	if controls then pcall(function() controls:Enable() end) end
	if S.dummy then S.dummy:Destroy(); S.dummy = nil end
	if S.template then S.template:Destroy(); S.template = nil end
end

-- show one item on the stand-in (the test hook; the cards do the same)
function FlairUI.preview(id: string)
	for _, t in Flair.TYPES do
		if Flair.info(t, id) then S.tab = t; S.pick[t] = id end
	end
	if S.open then refresh(); previewLoop() end
end

-- a phone-sized box for tests (Vector2, points), or nil for the real screen: the compact layout in that box
function FlairUI.fakeScreen(v: Vector2?)
	S.fake = v
	box.Size = if v then UDim2.fromOffset(v.X, v.Y) else UDim2.fromScale(1, 1)
	if S.open then useView(); fit(); refresh() end
end

-- ------------------------------------------------------------------ input (both layouts call these)
onTab = function(t: string)
	if S.tab == t then return end
	S.tab = t
	refresh()
	previewLoop()
end
onPick = function(t: string, id: string)
	S.pick[t] = id
	refresh()
	previewLoop()
end
onSlot = function(i: number)
	S.slot = i
	local id = slots()[i]
	if id and id ~= "" then S.pick.emote = id; previewLoop() end
	refresh()
end
onEquip = function(t: string)
	if not V then return end
	local X = if t == "kill" then V.K elseif t == "grapple" then V.G else V.M
	if not X.equip.enabled then return end
	local res = if t == "emote" then ask("slot", S.slot, S.pick.emote) else ask(t, S.pick[t])
	if not res.ok then X.note.Text = string.upper(tostring(res.why or "")) end
	task.wait(0.1)
	refresh()
end
onClear = function()
	if not V or not V.M.clear.enabled then return end
	ask("slot", S.slot, "")
	task.wait(0.1)
	refresh()
end
catcher.MouseButton1Click:Connect(function() end)
UIS.InputBegan:Connect(function(io, _gp)
	if S.open and io.KeyCode == Enum.KeyCode.Escape then FlairUI.close() end
end)
for _, a in { "KillFx", "Emotes", "Grapple", "FlairSave", "LootOwned" } do
	me:GetAttributeChangedSignal(a):Connect(function()
		if not S.open then return end
		if a == "LootOwned" then task.spawn(function() fetch(); if S.open then refresh() end end) else refresh() end
	end)
end
me:GetAttributeChangedSignal("Zone"):Connect(function() if me:GetAttribute("Zone") == "match" then FlairUI.close() end end)
me.CharacterAdded:Connect(function() FlairUI.close() end)
RunService.RenderStepped:Connect(function() if S.open then fit() end end)

return FlairUI
