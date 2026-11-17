--!strict
-- the equip screen for kill effects, emotes and grapple skins (doc FLAIR.md). FlairUI.open(tab?) / close() / isOpen() / preview(id).
-- the loadout's KILL EFFECT · EMOTES button opens it (the loadout steps aside first); not mid-match, like the loadout.
-- left: the items (a grid of kill effects; or the emote wheel's 8 slots over a row of emotes). right: the world, with a
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
local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")

local FlairUI = {}
local S = {
	open = false, tab = "kill", pick = { kill = "none", emote = "wave", grapple = "rope" } :: { [string]: string }, slot = 1,
	owned = { kill = {}, emote = {}, grapple = {} } :: { [string]: { [string]: boolean } }, tok = 0, hidden = {} :: { [ScreenGui]: boolean },
	cam = { active = false, closing = false, t0 = 0, dur = 0.5, from = CFrame.new(), to = CFrame.new(), saved = CFrame.new(), savedType = Enum.CameraType.Custom },
	spot = nil :: { s: Vector3, face: Vector3 }?, template = nil :: Model?, dummy = nil :: Model?, savedOpen = false,
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
local gui = new("ScreenGui", { Name = "JankFlair", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 31,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling, Enabled = false }, pg)
-- (a full-screen button under everything: Modal frees the mouse from first person; dark on the left, clear on the right
-- where the preview stands)
local catcher = new("TextButton", { Text = "", AutoButtonColor = false, BackgroundColor3 = Color3.fromRGB(8, 9, 12),
	BackgroundTransparency = 0, Size = UDim2.fromScale(1, 1), Modal = true }, gui)
new("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(0.42, 0.35),
	NumberSequenceKeypoint.new(0.62, 1), NumberSequenceKeypoint.new(1, 1) }) }, catcher)
local stage = new("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
	Size = UDim2.fromOffset(1920, 1080) }, gui)
local uiScale = new("UIScale", {}, stage)
local function fit()
	local v = (workspace.CurrentCamera :: Camera).ViewportSize
	uiScale.Scale = math.min(v.X / 1920, v.Y / 1080)
end

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

-- the two tabs, as the title
local tabs: { [string]: { b: TextButton, rule: Frame } } = {}
local TAB_X = { kill = 60, emote = 400, grapple = 690 }
local TAB_W = { kill = 320, emote = 270, grapple = 300 }
local TAB_TEXT = { kill = "KILL EFFECT", emote = "EMOTES", grapple = "GRAPPLE" }
for _, t in { "kill", "emote", "grapple" } do
	local b = new("TextButton", { AutoButtonColor = false, BackgroundTransparency = 1, Position = UDim2.fromOffset(TAB_X[t], 34),
		Size = UDim2.fromOffset(TAB_W[t], 60), FontFace = T.FONT_TITLE, TextSize = 40, Text = TAB_TEXT[t],
		TextColor3 = T.TEXT, TextXAlignment = Enum.TextXAlignment.Left, ZIndex = 3 }, stage)
	local rule = new("Frame", { BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Position = UDim2.fromOffset(2, 62), Size = UDim2.fromOffset(44, 3), ZIndex = 3 }, b)
	tabs[t] = { b = b, rule = rule }
end
local done = button(stage, "DONE  [ESC]", "white", UDim2.fromOffset(1700, 40), UDim2.fromOffset(160, 50))
local saveLbl = label(stage, "", 16, UDim2.fromOffset(1360, 100), UDim2.fromOffset(500, 22), T.MUTED, nil, Enum.TextXAlignment.Right)

-- the panel on the left
local panel = new("Frame", { BackgroundColor3 = T.BG, BackgroundTransparency = 0.12, BorderSizePixel = 0, Position = UDim2.fromOffset(60, 130),
	Size = UDim2.fromOffset(880, 900), ZIndex = 2 }, stage)
T.corner(panel, 8); T.edge(panel)

-- the name of what the preview shows (bottom right, over the world)
local nameBox = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(1160, 880), Size = UDim2.fromOffset(700, 140) }, stage)
local bigName = label(nameBox, "", 54, UDim2.fromOffset(0, 0), UDim2.fromOffset(700, 64), T.TEXT, T.FONT_TITLE)
bigName.TextStrokeTransparency = 0.7
local bigRule = new("Frame", { BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Position = UDim2.fromOffset(2, 70), Size = UDim2.fromOffset(44, 3), ZIndex = 3 }, nameBox)
local bigSub = label(nameBox, "", 18, UDim2.fromOffset(2, 82), UDim2.fromOffset(700, 24), T.SOFT, T.FONT_BOLD)
bigSub.TextStrokeTransparency = 0.75

-- a lock over an item you don't own: a small padlock drawn from frames
local function lock(parent: GuiObject, z: number)
	local veil = new("Frame", { Name = "Lock", BackgroundColor3 = Color3.fromRGB(8, 9, 12), BackgroundTransparency = 0.45, BorderSizePixel = 0,
		Size = UDim2.fromScale(1, 1), ZIndex = z }, parent)
	T.corner(veil, 6)
	local body = new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.new(0.5, 0, 0.5, 6), Size = UDim2.fromOffset(26, 20),
		BackgroundColor3 = T.SOFT, BorderSizePixel = 0, ZIndex = z + 1 }, veil)
	T.corner(body, 4)
	local shackle = new("Frame", { AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 0.5, -2), Size = UDim2.fromOffset(18, 18),
		BackgroundTransparency = 1, ZIndex = z + 1 }, veil)
	T.corner(shackle, 999)
	T.edge(shackle, T.SOFT, 0, 3)
	return veil
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

-- ------------------------------------------------------------------ the kill effect tab
local K = { frame = new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = 2 }, panel), cards = {} :: { Card } }
do
	local grid = new("ScrollingFrame", { BackgroundTransparency = 1, BorderSizePixel = 0, Position = UDim2.fromOffset(20, 20), Size = UDim2.fromOffset(840, 720),
		CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollingDirection = Enum.ScrollingDirection.Y,
		ScrollBarThickness = 6, ScrollBarImageColor3 = T.DIM, ZIndex = 3 }, K.frame)
	new("UIGridLayout", { CellSize = UDim2.fromOffset(196, 236), CellPadding = UDim2.fromOffset(12, 12), SortOrder = Enum.SortOrder.LayoutOrder }, grid)
	new("UIPadding", { PaddingTop = UDim.new(0, 4), PaddingLeft = UDim.new(0, 4) }, grid)
	for i, id in Flair.ORDER.kill do
		local c = card(grid, "kill", id, 196, 236, i)
		table.insert(K.cards, c)
	end
	K.equip = button(K.frame, "EQUIP", "main", UDim2.fromOffset(20, 800), UDim2.fromOffset(300, 64))
	K.note = label(K.frame, "", 16, UDim2.fromOffset(340, 820), UDim2.fromOffset(520, 24), T.MUTED, T.FONT_BOLD)
end

-- ------------------------------------------------------------------ the emote tab: the wheel's slots over the emotes
local M = { frame = new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = 2, Visible = false }, panel),
	slots = {} :: { { btn: TextButton, st: UIStroke, pic: Frame, empty: Frame, id: string } }, cards = {} :: { Card } }
do
	local cx, cy, R, CELL = 440, 280, 196, 100
	local ring = new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromOffset(cx, cy), Size = UDim2.fromOffset(R * 2 + CELL + 24, R * 2 + CELL + 24),
		BackgroundColor3 = T.CARD, BackgroundTransparency = 0.6, BorderSizePixel = 0, ZIndex = 2 }, M.frame)
	T.corner(ring, 999)
	M.centre = label(M.frame, "", 22, UDim2.fromOffset(cx - 120, cy - 30), UDim2.fromOffset(240, 30), T.TEXT, T.FONT_TITLE, Enum.TextXAlignment.Center)
	M.centreSub = label(M.frame, "", 14, UDim2.fromOffset(cx - 120, cy + 4), UDim2.fromOffset(240, 20), T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center)
	for i = 1, Flair.SLOTS do
		local a = math.rad(-90 + (i - 1) * 360 / Flair.SLOTS)
		local btn = new("TextButton", { Text = "", AutoButtonColor = false, AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.fromOffset(cx + math.cos(a) * R, cy + math.sin(a) * R), Size = UDim2.fromOffset(CELL, CELL),
			BackgroundColor3 = T.CARD, BorderSizePixel = 0, ZIndex = 3 }, M.frame)
		T.corner(btn, 10)
		local st = T.edge(btn)
		local pic = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(5, 5), Size = UDim2.new(1, -10, 1, -10), ZIndex = 4 }, btn)
		local empty = new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(24, 24),
			BackgroundTransparency = 1, ZIndex = 4 }, btn)
		T.corner(empty, 999)
		T.edge(empty, T.DIM, 0.4, 2)
		local num = label(btn, tostring(i), 12, UDim2.fromOffset(6, 4), UDim2.fromOffset(20, 14), T.DIM, T.FONT_BOLD)
		num.ZIndex = 6
		M.slots[i] = { btn = btn, st = st, pic = pic, empty = empty, id = "" }
	end
	local row = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(20, 560), Size = UDim2.fromOffset(840, 190), ZIndex = 3 }, M.frame)
	new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 10), SortOrder = Enum.SortOrder.LayoutOrder }, row)
	for i, id in Flair.ORDER.emote do
		table.insert(M.cards, card(row, "emote", id, 131, 190, i))
	end
	M.equip = button(M.frame, "PUT IN SLOT 1", "main", UDim2.fromOffset(20, 800), UDim2.fromOffset(300, 64))
	M.clear = button(M.frame, "EMPTY SLOT", "chip", UDim2.fromOffset(336, 812), UDim2.fromOffset(170, 40))
	M.note = label(M.frame, "", 16, UDim2.fromOffset(520, 820), UDim2.fromOffset(340, 24), T.MUTED, T.FONT_BOLD)
end

-- ------------------------------------------------------------------ the grapple tab: the eight skins
local G = { frame = new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = 2, Visible = false }, panel), cards = {} :: { Card } }
do
	local grid = new("ScrollingFrame", { BackgroundTransparency = 1, BorderSizePixel = 0, Position = UDim2.fromOffset(20, 20), Size = UDim2.fromOffset(840, 720),
		CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollingDirection = Enum.ScrollingDirection.Y,
		ScrollBarThickness = 6, ScrollBarImageColor3 = T.DIM, ZIndex = 3 }, G.frame)
	new("UIGridLayout", { CellSize = UDim2.fromOffset(196, 236), CellPadding = UDim2.fromOffset(12, 12), SortOrder = Enum.SortOrder.LayoutOrder }, grid)
	new("UIPadding", { PaddingTop = UDim.new(0, 4), PaddingLeft = UDim.new(0, 4) }, grid)
	for i, id in Flair.ORDER.grapple do table.insert(G.cards, card(grid, "grapple", id, 196, 236, i)) end
	G.equip = button(G.frame, "EQUIP", "main", UDim2.fromOffset(20, 800), UDim2.fromOffset(300, 64))
	G.note = label(G.frame, "", 16, UDim2.fromOffset(340, 820), UDim2.fromOffset(520, 24), T.MUTED, T.FONT_BOLD)
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
	for t, x in tabs do
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
	M.centre.Text = if inSlot then string.upper(inSlot.name) else ""
	M.centreSub.Text = "SLOT " .. S.slot
	local eid = S.pick.emote
	if not owns("emote", eid) then M.equip:set("LOCKED", false); M.note.Text = "FROM DUFFEL BAGS AND THE SHOP"
	elseif sl[S.slot] == eid then M.equip:set("IN SLOT " .. S.slot, false); M.note.Text = ""
	else M.equip:set("PUT IN SLOT " .. S.slot, true); M.note.Text = "" end
	M.clear:set("EMPTY SLOT", sl[S.slot] ~= "")
	-- the big name over the world
	local i = Flair.info(S.tab, S.pick[S.tab])
	bigName.Text = if i then string.upper(i.name) else ""
	bigRule.BackgroundColor3 = if i then (Flair.RARITY_COLOR[i.rarity] or T.ACCENT) else T.ACCENT
	bigSub.Text = if i then (string.upper(i.rarity) .. "  ·  " .. string.upper(Flair.TYPE_NAMES[S.tab])) else ""
	local sv = me:GetAttribute("FlairSave")
	saveLbl.Text = if sv == "off" then "NOT SAVING THIS SESSION" elseif sv == "lost" then "SAVED ELSEWHERE: CHANGES HERE WON'T KEEP" else ""
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
	for k = 0, 7 do
		local a = math.rad(({ 0, 45, -45, 90, -90, 135, -135, 180 })[k + 1])
		local d = CFrame.fromAxisAngle(Vector3.yAxis, a):VectorToWorldSpace(base)
		if not workspace:Raycast(from, d * 11, params) then
			local floor = workspace:Raycast(root.Position + d * 7 + Vector3.new(0, 3, 0), Vector3.new(0, -12, 0), params)
			if floor then return { s = floor.Position, face = -d } end
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
						tr:Play(0.2)
						local t0 = os.clock()
						local len = if e.loop then e.len * 2 else e.len
						while S.open and S.tok == tok and os.clock() - t0 < len do
							if e.loop and not tr.IsPlaying then tr:Play(0) end
							task.wait(0.05)
						end
						tr:Stop(0.25)
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

function FlairUI.open(tab: string?)
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
	S.pick.kill = wornKill()
	local sl = slots()
	S.pick.emote = if sl[S.slot] ~= "" then sl[S.slot] else Flair.ORDER.emote[1]
	S.pick.grapple = wornGrapple()
	table.clear(S.hidden)
	for _, g in pg:GetChildren() do
		if g:IsA("ScreenGui") and g ~= gui and g.Enabled then S.hidden[g] = true; g.Enabled = false end
	end
	fit()
	refresh()
	gui.Enabled = true
	catcher.BackgroundTransparency = 1
	T.tween(catcher, 0.35, { BackgroundTransparency = 0 })
	local cam = workspace.CurrentCamera :: Camera
	local c = S.cam
	c.saved, c.savedType = cam.CFrame, cam.CameraType
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

-- ------------------------------------------------------------------ input
for t, x in tabs do
	x.b.MouseButton1Click:Connect(function()
		if S.tab == t then return end
		S.tab = t
		refresh()
		previewLoop()
	end)
end
for _, c in K.cards do
	c.btn.MouseButton1Click:Connect(function()
		S.pick.kill = c.id
		refresh()
		previewLoop()
	end)
end
for _, c in M.cards do
	c.btn.MouseButton1Click:Connect(function()
		S.pick.emote = c.id
		refresh()
		previewLoop()
	end)
end
for i, s in M.slots do
	s.btn.MouseButton1Click:Connect(function()
		S.slot = i
		if s.id ~= "" then S.pick.emote = s.id; previewLoop() end
		refresh()
	end)
end
for _, c in G.cards do
	c.btn.MouseButton1Click:Connect(function()
		S.pick.grapple = c.id
		refresh()
		previewLoop()
	end)
end
G.equip.face.MouseButton1Click:Connect(function()
	if not G.equip.enabled then return end
	local res = ask("grapple", S.pick.grapple)
	if not res.ok then G.note.Text = string.upper(tostring(res.why or "")) end
	task.wait(0.1)
	refresh()
end)
K.equip.face.MouseButton1Click:Connect(function()
	if not K.equip.enabled then return end
	local res = ask("kill", S.pick.kill)
	if not res.ok then K.note.Text = string.upper(tostring(res.why or "")) end
	task.wait(0.1)
	refresh()
end)
M.equip.face.MouseButton1Click:Connect(function()
	if not M.equip.enabled then return end
	local res = ask("slot", S.slot, S.pick.emote)
	if not res.ok then M.note.Text = string.upper(tostring(res.why or "")) end
	task.wait(0.1)
	refresh()
end)
M.clear.face.MouseButton1Click:Connect(function()
	if not M.clear.enabled then return end
	ask("slot", S.slot, "")
	task.wait(0.1)
	refresh()
end)
done.face.MouseButton1Click:Connect(FlairUI.close)
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
