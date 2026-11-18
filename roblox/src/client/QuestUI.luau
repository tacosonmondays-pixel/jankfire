--!strict
-- the QUESTS screen (QuestClient opens it: U, the QUESTS button): today's three quests with their progress and the
-- reroll, the weekly bar with its steps, the wallet (Brass, Crate Tickets) and the way to the shop. the numbers are the
-- server's (Quests.luau, the remote JankfireRemotes.Quests); the pool and prices are Shared.QuestData.
-- also the toast when a quest finishes or a weekly step pays (QuestUI.toast), and the two icons, drawn from frames (no
-- uploads): QuestUI.icon("brass" | "tix", parent, size) for the shop and the HUD.
-- built from Theme; on a short or narrow screen (a phone) the panel fills the screen, the cards stack and the body
-- scrolls, every button at least 44 px.
local Players = game:GetService("Players")
local UIS = game:GetService("UserInputService")
local GuiService = game:GetService("GuiService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local T = require(script.Parent:WaitForChild("Theme"))
local MenuCursor = require(script.Parent:WaitForChild("MenuCursor")) :: any
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local QD = require(Shared:WaitForChild("QuestData"))
local Roster = require(Shared:WaitForChild("Roster"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local me = Players.LocalPlayer
local UI = {}

local BRASS = Color3.fromRGB(201, 164, 92)
local BRASS_DARK = Color3.fromRGB(138, 108, 52)
local BRASS_HI = Color3.fromRGB(236, 212, 158)
local TICKET = Color3.fromRGB(226, 219, 201)
local TICKET_INK = Color3.fromRGB(120, 112, 98)

local new = T.new
local function txt(parent: Instance, s: string, size: number, color: Color3?, font: Font?, align: Enum.TextXAlignment?): TextLabel
	local l = T.text(parent, "Text", s, size, color, font, align)
	l.TextTruncate = Enum.TextTruncate.AtEnd
	return l
end
local function at(o: GuiObject, x: number, y: number, w: number, h: number): GuiObject
	o.Position = UDim2.fromOffset(x, y)
	o.Size = UDim2.fromOffset(w, h)
	return o
end
local function comma(n: number): string
	local s = tostring(math.floor(n + 0.5))
	local out = s:reverse():gsub("(%d%d%d)", "%1,"):reverse()
	return (out:gsub("^,", ""))
end
UI.comma = comma

-- ------------------------------------------------------------------ the icons
-- Brass: a spent casing seen end-on (the rim, the head, the primer). a Crate Ticket: a stub with a torn line
function UI.icon(kind: string, parent: Instance?, size: number?): Frame
	local s = size or 16
	local f = new("Frame", { Name = if kind == "tix" then "TicketIcon" else "BrassIcon", BackgroundTransparency = 1, Size = UDim2.fromOffset(s, s) })
	if kind == "tix" then
		local body = new("Frame", { Name = "Stub", BorderSizePixel = 0, BackgroundColor3 = TICKET, AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.new(1, 0, 0.66, 0) }, f)
		T.corner(body, math.max(2, math.floor(s * 0.14)))
		-- the torn line: three dots down the stub, a third of the way in
		for i = 0, 2 do
			local d = new("Frame", { BorderSizePixel = 0, BackgroundColor3 = TICKET_INK, AnchorPoint = Vector2.new(0.5, 0.5),
				Position = UDim2.new(0.32, 0, 0.22 + i * 0.28, 0), Size = UDim2.fromOffset(math.max(1, math.floor(s * 0.09)), math.max(1, math.floor(s * 0.09))) }, body)
			T.corner(d, 99)
		end
		-- the notch on each end
		for _, x in { 0, 1 } do
			local n = new("Frame", { BorderSizePixel = 0, BackgroundColor3 = TICKET_INK, AnchorPoint = Vector2.new(0.5, 0.5),
				Position = UDim2.fromScale(x, 0.5), Size = UDim2.fromOffset(math.max(2, math.floor(s * 0.2)), math.max(2, math.floor(s * 0.2))), BackgroundTransparency = 0.25 }, body)
			T.corner(n, 99)
		end
	else
		local rim = new("Frame", { Name = "Rim", BorderSizePixel = 0, BackgroundColor3 = BRASS, Size = UDim2.fromScale(1, 1) }, f)
		T.corner(rim, 999)
		local head = new("Frame", { Name = "Head", BorderSizePixel = 0, BackgroundColor3 = BRASS_DARK, AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromScale(0.72, 0.72) }, rim)
		T.corner(head, 999)
		local face = new("Frame", { Name = "Face", BorderSizePixel = 0, BackgroundColor3 = BRASS, AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromScale(0.86, 0.86) }, head)
		T.corner(face, 999)
		local primer = new("Frame", { Name = "Primer", BorderSizePixel = 0, BackgroundColor3 = BRASS_HI, AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromScale(0.38, 0.38) }, face)
		T.corner(primer, 999)
	end
	if parent then f.Parent = parent end
	return f
end
-- a row laid out left to right that sizes itself: { { icon = kind, s = size } | { text, size, color, font } | { gap } }
local function row(parent: Instance, x: number, y: number, h: number, parts: { any }, right: boolean?): Frame
	local r = new("Frame", { Name = "Row", BackgroundTransparency = 1, Position = UDim2.fromOffset(x, y), Size = UDim2.fromOffset(0, h),
		AutomaticSize = Enum.AutomaticSize.X, AnchorPoint = Vector2.new(if right then 1 else 0, 0) }, parent)
	new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, VerticalAlignment = Enum.VerticalAlignment.Center,
		SortOrder = Enum.SortOrder.LayoutOrder, Padding = UDim.new(0, 5) }, r)
	for i, pt in parts do
		if pt.icon then
			UI.icon(pt.icon, r, pt.s or math.floor(h * 0.78)).LayoutOrder = i
		elseif pt.gap then
			new("Frame", { Name = "Gap", BackgroundTransparency = 1, Size = UDim2.fromOffset(pt.gap, 1), LayoutOrder = i }, r)
		else
			local l = T.text(r, "Text", pt.text, pt.size or 14, pt.color or T.TEXT, pt.font or T.FONT_BOLD)
			l.AutomaticSize = Enum.AutomaticSize.X
			l.Size = UDim2.fromOffset(0, h)
			l.LayoutOrder = i
		end
	end
	return r
end
UI.row = row

-- ------------------------------------------------------------------ the screen
local gui = new("ScreenGui", { Name = "JankQuests", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 24,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling, Enabled = false }, me:WaitForChild("PlayerGui"))
local scrim = new("TextButton", { Name = "Scrim", Text = "", AutoButtonColor = false, Modal = true, BackgroundColor3 = Color3.fromRGB(6, 7, 9),
	BackgroundTransparency = 0.35, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1) }, gui)
local holder = new("Frame", { Name = "Holder", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, gui)
local panel = new("Frame", { Name = "Panel", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), BackgroundColor3 = T.BG,
	BorderSizePixel = 0, Active = true }, holder)
local panelCorner = T.corner(panel, 10)
local scale = new("UIScale", {}, panel)

local state: any = nil -- the server's (Quests.luau stateFor)
local why: string? = nil -- a refusal to show under the cards
local isOpen = false
local fake: Vector2? = nil
local setFlag = false
local L = { compact = false, s = 1, W = 880, H = 556, btn = 32, pad = 24 }
local Remote: RemoteFunction? = nil

local function remote(): RemoteFunction?
	if not Remote then Remote = Remotes:FindFirstChild("Quests") :: RemoteFunction? end
	return Remote
end
local function invoke(...: any): any
	local r = remote()
	if not r then return { ok = false, why = "quests aren't ready yet" } end
	local ok, res = pcall(function(...) return (r :: RemoteFunction):InvokeServer(...) end, ...)
	if not ok or type(res) ~= "table" then return { ok = false, why = "no answer from the server" } end
	return res
end

local function screenSize(): Vector2
	if fake then return fake :: Vector2 end
	local cam = workspace.CurrentCamera
	return if cam then cam.ViewportSize else Vector2.new(1280, 720)
end
local function measure()
	local vs = screenSize()
	local top = if fake then 0 else GuiService.TopbarInset.Height
	local w, h = vs.X, vs.Y - top
	holder.Position = UDim2.fromOffset(0, top)
	holder.Size = if fake then UDim2.fromOffset(vs.X, vs.Y) else UDim2.new(1, 0, 1, -top)
	L.compact = h < 600 or w < 760
	if L.compact then
		L.s = math.clamp(math.min(w / 420, h / 400), 0.7, 1.3)
		L.W, L.H = math.floor(w / L.s), math.floor(h / L.s)
		L.btn = math.max(32, math.ceil(46 / L.s))
		L.pad = 14
		panelCorner.CornerRadius = UDim.new(0, 0)
	else
		L.s = math.clamp(math.min(w / 960, h / 640), 0.75, 2)
		L.W, L.H = 880, 556
		L.btn = 32
		L.pad = 24
		panelCorner.CornerRadius = UDim.new(0, 10)
	end
	scale.Scale = L.s
	panel.Size = UDim2.fromOffset(L.W, L.H)
end

local function button(parent: Instance, s: string, x: number, y: number, w: number, h: number, accent: boolean?, off: boolean?): TextButton
	local base = if accent then T.ACCENT else T.CARD_HI
	local b = new("TextButton", { Name = "Button", AutoButtonColor = false, Text = s, FontFace = T.FONT_BOLD, TextSize = 13,
		TextColor3 = if accent then T.INK elseif off then T.DIM else T.TEXT, BackgroundColor3 = base, BorderSizePixel = 0 }, parent)
	at(b, x, y, w, h)
	T.corner(b)
	if off then b.Active = false; b.BackgroundTransparency = 0.5; return b end
	b.MouseEnter:Connect(function() b.BackgroundColor3 = if accent then base:Lerp(Color3.new(1, 1, 1), 0.18) else T.TRACK end)
	b.MouseLeave:Connect(function() b.BackgroundColor3 = base end)
	return b
end
local function sectionTitle(parent: Instance, s: string, x: number, y: number, w: number): TextLabel
	return at(txt(parent, s, 12, T.MUTED, T.FONT_BOLD), x, y, w, 16) :: TextLabel
end
local function rightNote(parent: Instance, s: string, x: number, y: number, w: number): TextLabel
	return at(txt(parent, s, 12, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Right), x, y, w, 16) :: TextLabel
end
-- a drawn tick (no glyph fonts)
local function tick(parent: Instance, x: number, y: number, s: number, color: Color3)
	local a = new("Frame", { BorderSizePixel = 0, BackgroundColor3 = color, AnchorPoint = Vector2.new(0.5, 0.5), Rotation = -45,
		Position = UDim2.fromOffset(x + s * 0.3, y + s * 0.62), Size = UDim2.fromOffset(math.max(2, s * 0.14), s * 0.42) }, parent)
	T.corner(a, 2)
	local b = new("Frame", { BorderSizePixel = 0, BackgroundColor3 = color, AnchorPoint = Vector2.new(0.5, 0.5), Rotation = 45,
		Position = UDim2.fromOffset(x + s * 0.6, y + s * 0.45), Size = UDim2.fromOffset(math.max(2, s * 0.14), s * 0.78) }, parent)
	T.corner(b, 2)
end

local names: { [string]: string } = {}
for _, e in Roster.list or {} do names[e.id] = e.name end
local function rosterName(id: string): string
	if names[id] then return names[id] end
	local e = Roster.byId and Roster.byId[id]
	return if e then e.name else id
end
local function subFor(id: string): string?
	local q = QD.byId[id]
	if not q then return nil end
	local cid = string.match(q.stat, "^kill:(%w+)$")
	local c = cid and QD.CLASSES[cid]
	if not c or #c.ids <= 1 or cid == "item" then return nil end
	local out = {}
	for _, wid in c.ids do
		local e = Roster.byId and Roster.byId[wid]
		if not e or e.live then table.insert(out, rosterName(wid)) end
	end
	return table.concat(out, " · ")
end

-- ------------------------------------------------------------------ pieces
local busy = false
local function reroll(slot: number)
	if busy then return end
	busy = true
	local res = invoke("reroll", slot)
	busy = false
	if res.ok then state = res; why = nil else why = res.why end
	UI.refresh()
end

local function questCard(parent: Instance, q: any, x: number, y: number, w: number, h: number)
	local c = new("Frame", { Name = "Quest" .. tostring(q.slot), BackgroundColor3 = T.CARD, BorderSizePixel = 0 }, parent)
	at(c, x, y, w, h)
	T.corner(c)
	if q.done then T.edge(c, T.ACCENT, 0.55, 1) end
	local tier = QD.TIERS[q.tier]
	local p = 16
	-- the tier: its name and 1-3 pips
	at(txt(c, if tier then tier.name else "", 11, T.MUTED, T.FONT_BOLD), p, 14, 80, 14)
	local nP = if q.tier == "hard" then 3 elseif q.tier == "medium" then 2 else 1
	for i = 1, 3 do
		local d = new("Frame", { BorderSizePixel = 0, BackgroundColor3 = if i <= nP then T.SOFT else T.TRACK, Position = UDim2.fromOffset(w - p - (4 - i) * 10, 17), Size = UDim2.fromOffset(6, 6) }, c)
		T.corner(d, 99)
	end
	-- the quest
	local compact = h < 150
	local title = txt(c, q.text, if compact then 16 else 18, T.TEXT, T.FONT_BOLD)
	title.TextWrapped = true
	title.TextTruncate = Enum.TextTruncate.None
	title.TextYAlignment = Enum.TextYAlignment.Top
	at(title, p, 36, w - p * 2, if compact then 22 else 46)
	local sub = subFor(q.id)
	if sub then
		local sl = txt(c, sub, 11, T.MUTED, T.FONT)
		sl.TextWrapped = true
		sl.TextYAlignment = Enum.TextYAlignment.Top
		at(sl, p, if compact then 58 else 84, w - p * 2, if compact then 14 else 28)
	end
	-- progress
	local barY = h - 62
	local frac = if q.goal > 0 then math.clamp(q.n / q.goal, 0, 1) else 0
	at(txt(c, ("%s / %s"):format(comma(q.n), comma(q.goal)), 13, if q.done then T.ACCENT else T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Right), p, barY - 20, w - p * 2, 16)
	local track = new("Frame", { Name = "Track", BackgroundColor3 = T.TRACK, BorderSizePixel = 0 }, c)
	at(track, p, barY, w - p * 2, 6)
	T.corner(track, 3)
	local fill = new("Frame", { Name = "Fill", BackgroundColor3 = if q.done then T.ACCENT else T.TEXT, BorderSizePixel = 0, Size = UDim2.fromScale(frac, 1) }, track)
	T.corner(fill, 3)
	-- the reward, and the reroll or DONE
	local ry = h - 40
	row(c, p, ry, 24, { { icon = "brass", s = 18 }, { text = comma(tier and tier.brass or 0), size = 14 }, { gap = 6 },
		{ text = ("+%d WEEKLY"):format(tier and tier.pts or 0), size = 11, color = T.MUTED } })
	if q.done then
		tick(c, w - p - 64, ry + 3, 18, T.ACCENT)
		at(txt(c, "DONE", 13, T.ACCENT, T.FONT_HEAVY, Enum.TextXAlignment.Right), w - p - 44, ry, 44, 24)
	elseif state and (state.rerolls or 0) > 0 then
		local bw = 80
		local b = button(c, "REROLL", w - p - bw, ry - math.floor((L.btn - 24) / 2), bw, math.max(24, L.btn - 6))
		b.TextSize = 12
		b.MouseButton1Click:Connect(function() reroll(q.slot) end)
	end
end

local function weekly(parent: Instance, x: number, y: number, w: number, h: number)
	local c = new("Frame", { Name = "Weekly", BackgroundColor3 = T.CARD, BorderSizePixel = 0 }, parent)
	at(c, x, y, w, h)
	T.corner(c)
	local pts = math.min(state.pts or 0, QD.FULL)
	local p = 18
	row(c, p, 8, 26, { { text = tostring(pts), size = 22, font = T.FONT_HEAVY }, { text = ("/ %d POINTS"):format(QD.FULL), size = 12, color = T.MUTED } })
	-- the bar and its steps
	local bx, bw = p + 8, w - (p + 8) * 2
	local by = 56
	local track = new("Frame", { Name = "Track", BackgroundColor3 = T.TRACK, BorderSizePixel = 0 }, c)
	at(track, bx, by, bw, 6)
	T.corner(track, 3)
	local fill = new("Frame", { Name = "Fill", BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Size = UDim2.fromScale(pts / QD.FULL, 1) }, track)
	T.corner(fill, 3)
	for i, s in QD.STEPS do
		local cx = bx + math.floor(bw * s.at / QD.FULL)
		local got = (state.got or 0) >= i
		local node = new("Frame", { Name = "Step" .. i, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
			BackgroundColor3 = if got then T.ACCENT else T.CARD, Position = UDim2.fromOffset(cx, by + 3), Size = UDim2.fromOffset(14, 14) }, c)
		T.corner(node, 99)
		T.edge(node, if got then T.ACCENT else T.EDGE, if got then 0 else 0.7, 1.5)
		-- the reward under it
		local kind = if s.tix then "tix" else "brass"
		local n = if s.tix then tostring(s.tix) else comma(s.brass or 0)
		local hold = new("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromOffset(cx, by + 14), Size = UDim2.fromOffset(60, 20) }, c)
		local lay = row(hold, 0, 0, 20, { { icon = kind, s = 14 }, { text = n, size = 12, color = if got then T.ACCENT else T.SOFT } })
		lay.AnchorPoint = Vector2.new(0.5, 0)
		lay.Position = UDim2.fromScale(0.5, 0)
		at(txt(c, tostring(s.at), 10, T.DIM, T.FONT_BOLD, Enum.TextXAlignment.Center), cx - 15, by - 20, 30, 12)
	end
end

local function walletRow(parent: Instance, x: number, y: number, w: number, h: number)
	local c = new("Frame", { Name = "Wallet", BackgroundColor3 = T.CARD, BorderSizePixel = 0 }, parent)
	at(c, x, y, w, h)
	T.corner(c)
	local p = 18
	local compact = L.compact
	row(c, p, 10, 22, { { icon = "tix", s = 18 }, { text = comma(state.tix or 0), size = 16, font = T.FONT_HEAVY }, { gap = 4 },
		{ text = "CRATE TICKETS", size = 11, color = T.MUTED } })
	local line = ("Crate %d · Duffel Bag %d · Spray Can %d tickets"):format(QD.PRICES.crate.tix or 0, QD.PRICES.bag.tix or 0, QD.PRICES.spray.tix or 0)
	local line2 = ("Duffel Bag %s · Spray Can %s Brass"):format(comma(QD.PRICES.bag.brass or 0), comma(QD.PRICES.spray.brass or 0))
	local bw = if compact then w - p * 2 else 150
	at(txt(c, line, 12, T.SOFT, T.FONT), p, 36, w - p * 2 - (if compact then 0 else bw + 12), 16)
	at(txt(c, line2, 12, T.MUTED, T.FONT), p, 54, w - p * 2 - (if compact then 0 else bw + 12), 16)
	local b = button(c, "OPEN SHOP", if compact then p else w - p - bw, if compact then 78 else math.floor((h - L.btn) / 2), bw, L.btn, true)
	b.MouseButton1Click:Connect(function()
		local sm = script.Parent:FindFirstChild("ShopUI")
		UI.close()
		if sm then
			local ok, Shop = pcall(require, sm)
			if ok and type(Shop) == "table" and type((Shop :: any).open) == "function" then pcall((Shop :: any).open, "containers") end
		end
	end)
end

-- ------------------------------------------------------------------ draw
local body: ScrollingFrame? = nil
local function draw()
	if not isOpen then return end
	measure()
	for _, c in panel:GetChildren() do if c:IsA("GuiObject") then c:Destroy() end end
	local W, pad = L.W, L.pad
	-- the header: the title, the wallet, CLOSE
	at(txt(panel, "QUESTS", if L.compact then 20 else 26, T.TEXT, T.FONT_TITLE), pad, if L.compact then 12 else 20, 220, 32)
	local cb = button(panel, "CLOSE", W - pad - 80, if L.compact then 10 else 20, 80, L.btn)
	cb.MouseButton1Click:Connect(function() UI.close() end)
	if state and state.ok then
		local wr = row(panel, W - pad - 80 - 20, if L.compact then 10 else 20, L.btn, { { icon = "brass", s = 18 }, { text = comma(state.brass or 0), size = 16, font = T.FONT_HEAVY },
			{ gap = 10 }, { icon = "tix", s = 18 }, { text = comma(state.tix or 0), size = 16, font = T.FONT_HEAVY } }, true)
		wr.Name = "Wallet"
	end
	local top = if L.compact then 10 + L.btn + 10 else 68
	local sc = new("ScrollingFrame", { Name = "Body", BackgroundTransparency = 1, BorderSizePixel = 0, ScrollBarThickness = 4,
		ScrollBarImageColor3 = T.MUTED, Position = UDim2.fromOffset(0, top), Size = UDim2.new(1, 0, 1, -top), CanvasSize = UDim2.fromOffset(0, 0),
		ScrollingDirection = Enum.ScrollingDirection.Y }, panel)
	body = sc
	if not state or not state.ok then
		at(txt(sc, if state and state.why then state.why else "loading…", 14, T.MUTED, T.FONT_BOLD), pad, 10, W - pad * 2, 20)
		return
	end
	local y = 6
	local cw = W - pad * 2
	-- DAILY
	sectionTitle(sc, "DAILY", pad, y, 200)
	local rr = state.rerolls or 0
	rightNote(sc, ("NEW QUESTS IN %s%s"):format(QD.left(state.dayLeft or 0), if rr > 0 then "  ·  " .. rr .. " FREE REROLL" else ""), pad, y, cw)
	y += 22
	local list = state.list or {}
	if L.compact then
		for _, q in list do
			questCard(sc, q, pad, y, cw, if subFor(q.id) then 142 else 128)
			y += (if subFor(q.id) then 142 else 128) + 10
		end
	else
		local gap = 14
		local qw = math.floor((cw - gap * 2) / 3)
		for i, q in list do questCard(sc, q, pad + (i - 1) * (qw + gap), y, qw, 200) end
		y += 200 + 10
	end
	if why then
		at(txt(sc, why, 12, T.DANGER, T.FONT_BOLD), pad, y, cw, 16)
	end
	y += 20
	-- WEEKLY
	sectionTitle(sc, "WEEKLY", pad, y, 200)
	rightNote(sc, "RESETS IN " .. QD.left(state.weekLeft or 0), pad, y, cw)
	y += 22
	weekly(sc, pad, y, cw, 100)
	y += 100 + 14
	-- the wallet and the shop
	local wh = if L.compact then 78 + L.btn + 14 else 80
	walletRow(sc, pad, y, cw, wh)
	y += wh + 8
	if state.owed then
		at(txt(sc, ("OWED AFTER A CHEAT RESTORE: %s Brass, %d tickets. new rewards pay this first"):format(comma(state.owed.b or 0), state.owed.x or 0), 12, T.DANGER, T.FONT_BOLD), pad, y, cw, 16)
		y += 20
	end
	y += pad - 8
	sc.CanvasSize = UDim2.fromOffset(0, y)
end
UI.refresh = function() if isOpen then draw() end end

local function setMenuFlag(on: boolean)
	MenuCursor.set("quests", on, function() return isOpen end) -- (the mouse is free and shows while it's up)
	if on then
		if not me:GetAttribute("LoadoutOpen") then me:SetAttribute("LoadoutOpen", true); setFlag = true end
	elseif setFlag then
		setFlag = false
		me:SetAttribute("LoadoutOpen", false)
	end
	me:SetAttribute("QuestsOpen", on)
end

local fetching = false
local function fetch()
	if fetching then return end
	fetching = true
	task.spawn(function()
		local res = invoke("state")
		fetching = false
		if res.ok or not state then state = res end
		UI.refresh()
	end)
end

function UI.open()
	if not require(script.Parent:WaitForChild("MenuGate")).allowed("quests") then return end -- (no hub menus in a match or a map room: MenuGate, play-party-ranked's)
	why = nil
	if not isOpen then
		isOpen = true
		gui.Enabled = true
		setMenuFlag(true)
	end
	draw()
	fetch()
	if me:GetAttribute("QuestNews") == true then task.spawn(invoke, "seen") end -- (QuestNews off: the badge over Dune)
end
function UI.close()
	if not isOpen then return end
	isOpen = false
	if me:GetAttribute("QuestNews") == true then task.spawn(invoke, "seen") end -- (finished while it was open: seen too)
	gui.Enabled = false
	setMenuFlag(false)
	body = nil
	for _, c in panel:GetChildren() do if c:IsA("GuiObject") then c:Destroy() end end
end
function UI.isOpen(): boolean return isOpen end
function UI.toggle() if isOpen then UI.close() else UI.open() end end
function UI.fakeScreen(v: Vector2?) fake = v; UI.refresh() end
function UI.setState(s: any) if type(s) == "table" and s.ok then state = s; UI.refresh() end end
function UI.state(): any return state end
function UI.reroll(slot: number) reroll(slot) end
function UI.scrollTo(y: number) if body then body.CanvasPosition = Vector2.new(0, y) end end

scrim.MouseButton1Click:Connect(function() UI.close() end)
local cam = workspace.CurrentCamera
if cam then cam:GetPropertyChangedSignal("ViewportSize"):Connect(function() if isOpen and not fake then task.defer(draw) end end) end
UIS.InputBegan:Connect(function(io)
	if isOpen and io.KeyCode == Enum.KeyCode.Escape then UI.close() end
end)

-- ------------------------------------------------------------------ the toast
-- a quest finished / a weekly step paid: a small plate at the top for a few seconds, one at a time
local toastGui = new("ScreenGui", { Name = "JankQuestToast", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 30,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, me:WaitForChild("PlayerGui"))
local toastRoot = T.scaled(toastGui)
local queue: { any } = {}
local showing = false
local function showNext()
	if showing or #queue == 0 then return end
	showing = true
	local m = table.remove(queue, 1)
	local w, h = 380, 62
	local y0 = if me:GetAttribute("Zone") == "match" then 76 else 56 -- (in a match: under the score plate)
	local f = T.plate(toastRoot, "Toast", UDim2.new(0.5, 0, 0, y0), UDim2.fromOffset(w, h))
	f.AnchorPoint = Vector2.new(0.5, 0)
	f.BackgroundTransparency = 1
	local bar = new("Frame", { BorderSizePixel = 0, BackgroundColor3 = T.ACCENT, Position = UDim2.fromOffset(0, 14), Size = UDim2.fromOffset(3, h - 28) }, f)
	T.corner(bar, 2)
	local head = txt(f, m.head, 11, T.MUTED, T.FONT_BOLD)
	at(head, 18, 10, w - 130, 14)
	local line = txt(f, m.line, 16, T.TEXT, T.FONT_BOLD)
	at(line, 18, 28, w - 130, 22)
	local parts = {}
	for i, r in m.rewards do
		if i > 1 then table.insert(parts, { gap = 6 }) end
		table.insert(parts, { icon = r.kind, s = 18 })
		table.insert(parts, { text = "+" .. r.n, size = 16, font = T.FONT_HEAVY })
	end
	local rw = row(f, w - 16, 19, 24, parts, true)
	rw.Name = "Reward"
	-- in: a short drop and fade; out the same way
	local texts = {}
	for _, d in f:GetDescendants() do
		if d:IsA("TextLabel") then table.insert(texts, d); d.TextTransparency = 1 end
	end
	local frames = {}
	for _, d in f:GetDescendants() do
		if d:IsA("Frame") and d.BackgroundTransparency < 1 then table.insert(frames, { d, d.BackgroundTransparency }); d.BackgroundTransparency = 1 end
	end
	local stroke = f:FindFirstChildOfClass("UIStroke")
	local sa = if stroke then stroke.Transparency else 1
	if stroke then stroke.Transparency = 1 end
	f.Position = UDim2.new(0.5, 0, 0, y0 - 12)
	T.tween(f, 0.22, { Position = UDim2.new(0.5, 0, 0, y0), BackgroundTransparency = T.BG_A })
	for _, l in texts do T.tween(l, 0.22, { TextTransparency = 0 }) end
	for _, fr in frames do T.tween(fr[1], 0.22, { BackgroundTransparency = fr[2] }) end
	if stroke then T.tween(stroke, 0.22, { Transparency = sa }) end
	local sfx = script.Parent:FindFirstChild("Sfx")
	if sfx then
		local ok, S = pcall(require, sfx)
		if ok and type(S) == "table" and type((S :: any).play) == "function" then pcall((S :: any).play, UI.TOAST_SOUND) end
	end
	task.delay(m.secs or 3.2, function()
		T.tween(f, 0.25, { Position = UDim2.new(0.5, 0, 0, y0 - 12), BackgroundTransparency = 1 })
		for _, l in texts do T.tween(l, 0.25, { TextTransparency = 1 }) end
		for _, fr in frames do T.tween(fr[1], 0.25, { BackgroundTransparency = 1 }) end
		if stroke then T.tween(stroke, 0.25, { Transparency = 1 }) end
		task.delay(0.3, function()
			f:Destroy()
			showing = false
			showNext()
		end)
	end)
end
UI.TOAST_SOUND = "click"
-- a push from the server (QuestPush): { t = "done", text, brass, pts } or { t = "step", brass?, tix? }
function UI.toast(msg: any)
	if type(msg) ~= "table" then return end
	if msg.t == "done" then
		table.insert(queue, { head = "QUEST COMPLETE", line = tostring(msg.text or ""), rewards = { { kind = "brass", n = comma(tonumber(msg.brass) or 0) } } })
	elseif msg.t == "step" then
		local r = {}
		if msg.brass then table.insert(r, { kind = "brass", n = comma(tonumber(msg.brass) or 0) }) end
		if msg.tix then table.insert(r, { kind = "tix", n = tostring(msg.tix) }) end
		local what = if msg.tix then (if msg.tix == 1 then "1 Crate Ticket" else msg.tix .. " Crate Tickets") else comma(tonumber(msg.brass) or 0) .. " Brass"
		table.insert(queue, { head = "WEEKLY REWARD", line = what, rewards = r })
	else
		return
	end
	showNext()
end

return UI
