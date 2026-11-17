--!strict
-- LEADERBOARD UI: the ranked leaderboard (17 Nov: the hub's RANKED regular, Frisk1636, opens it with his prompt, and the
-- Play screen has a LEADERBOARD button). tabs DUELS | PARTY RANKED; your own rank, RP bar or placements at the top; this
-- server's placed players by rank points under it (the duels: each player's best mode); the season and the time left.
-- with PlayConfig.CROSS_SERVER on, a THIS SERVER | GLOBAL switch shows the global top 100 (off until publish).
-- quiet: names and numbers only, built from Theme and RankedStyle. the server side is RankedData.board.
-- open it: LeaderboardUI.open(tab?) on the client; Party.openBoard(player, tab?) on the server; or any ProximityPrompt
-- with the attribute RankedBoard = "duels" | "party" (PlayClient.client.luau)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local T = require(script.Parent:WaitForChild("Theme"))
local PlayUI = require(script.Parent:WaitForChild("PlayUI"))
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local RankedStyle = require(Shared:WaitForChild("RankedStyle"))

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")
local new, text = T.new, T.text
local ask = PlayUI.ask

local Board = {}
local S: any = { open = false, tab = "duels", scope = "server", data = nil, got = 0, fake = nil }

-- ------------------------------------------------------------------ the panel
local gui = new("ScreenGui", { Name = "JankBoard", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 24,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling, Enabled = false }, pg)
local scaled = T.scaled(gui)
local shade = new("TextButton", { Name = "Shade", AutoButtonColor = false, Text = "", BorderSizePixel = 0, BackgroundColor3 = Color3.new(0, 0, 0),
	BackgroundTransparency = 0.45, Size = UDim2.fromScale(1, 1), Modal = true }, scaled) -- (Modal: the mouse is free in first person)
local panel = T.plate(scaled, "Panel", UDim2.fromScale(0.5, 0.5), UDim2.fromOffset(560, 600))
panel.AnchorPoint = Vector2.new(0.5, 0.5)
panel.BackgroundTransparency = 0.06
shade.MouseButton1Click:Connect(function() Board.close() end)

local function button(parent: Instance, name: string, label: string, w: number, h: number): TextButton
	local b = new("TextButton", { Name = name, AutoButtonColor = false, BorderSizePixel = 0, Size = UDim2.fromOffset(w, h),
		BackgroundColor3 = T.CARD, BackgroundTransparency = 0, FontFace = T.FONT_HEAVY, TextSize = 12, Text = label, TextColor3 = T.MUTED }, parent)
	T.corner(b, 5)
	return b
end

local function fmtLeft(secs: number): string
	if secs <= 0 then return "SEASON ENDED" end
	local d, h, m = secs // 86400, (secs % 86400) // 3600, (secs % 3600) // 60
	if d > 0 then return ("%dD %dH LEFT"):format(d, h) end
	if h > 0 then return ("%dH %dM LEFT"):format(h, m) end
	return ("%dM LEFT"):format(math.max(1, m))
end
local function seasonLine(): string
	local s = S.data and S.data.season
	if type(s) ~= "table" then return "" end
	local left = (tonumber(s.ends) or 0) - (tonumber(s.now) or 0) - (os.clock() - S.got)
	return ("%s  ·  %s"):format(tostring(s.name or ("SEASON " .. tostring(s.n))), fmtLeft(math.floor(left)))
end
local function modeTag(v: any): string
	if type(v) ~= "table" or v.ladder == "party" or type(v.mode) ~= "string" then return "" end
	return string.upper(v.mode)
end

-- your own block: badge, rank, RP bar (or placements, or unranked), W-L and your place on the list
local function meBlock(parent: Instance, y: number, w: number, v: any, place: number?): number
	local h = 76
	local card = new("Frame", { Name = "Me", BorderSizePixel = 0, BackgroundColor3 = T.CARD, Position = UDim2.fromOffset(20, y), Size = UDim2.fromOffset(w, h) }, parent)
	T.corner(card, 6)
	local b = RankedStyle.badge(card, 56, v or { unranked = true, ladder = if S.tab == "party" then "party" else "duels" })
	b.Position = UDim2.fromOffset(12, 10)
	local x = 80
	local col = if v then RankedStyle.color(v) else T.MUTED
	local kick = text(card, "Kicker", "YOUR RANK" .. (if modeTag(v) ~= "" then "  ·  " .. modeTag(v) else ""), 11, T.MUTED, T.FONT_BOLD)
	kick.Position = UDim2.fromOffset(x, 12); kick.Size = UDim2.fromOffset(260, 14)
	local placed = v and v.placed == true and not v.unranked
	local name = if not v or v.unranked then "UNRANKED"
		elseif not placed then ("PLACEMENTS %d/%d"):format(math.min(v.n or 0, v.need or 5), v.need or 5)
		else tostring(v.name or "")
	local nm = text(card, "Rank", name, 18, if placed then col else T.TEXT, T.FONT_HEAVY)
	nm.Position = UDim2.fromOffset(x, 28); nm.Size = UDim2.fromOffset(260, 22)
	-- the bar: RP of 100 in the division (the top tier: its points, full); placements: one cell a match
	local barW = w - x - 120
	if placed then
		local track = new("Frame", { Name = "Track", BorderSizePixel = 0, BackgroundColor3 = T.TRACK, Position = UDim2.fromOffset(x, 56), Size = UDim2.fromOffset(barW, 6) }, card)
		T.corner(track, 3)
		local top = v.div == nil
		local fill = new("Frame", { Name = "Fill", BorderSizePixel = 0, BackgroundColor3 = col,
			Size = UDim2.new(if top then 1 else math.clamp(tonumber(v.progress) or ((v.rp or 0) / 100), 0, 1), 0, 1, 0) }, track)
		T.corner(fill, 3)
		local rp = text(card, "RP", if top then ("%d RP"):format(v.rp or 0) else ("%d/100"):format(v.rp or 0), 12, T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Right)
		rp.Position = UDim2.fromOffset(x + barW - 120, 34); rp.Size = UDim2.fromOffset(120, 16)
	elseif v and not v.unranked then
		local need = math.max(1, v.need or 5)
		local cw = math.floor((barW - (need - 1) * 4) / need)
		for i = 1, need do
			local c = new("Frame", { Name = "Cell", BorderSizePixel = 0, BackgroundColor3 = if i <= (v.n or 0) then T.TEXT else T.TRACK,
				Position = UDim2.fromOffset(x + (i - 1) * (cw + 4), 56), Size = UDim2.fromOffset(cw, 6) }, card)
			T.corner(c, 3)
		end
	end
	-- right: W-L and the place on this list
	local wl = if v and not v.unranked then ("%d-%d"):format(v.w or 0, v.l or 0) else "-"
	local r1 = text(card, "WL", wl, 18, T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Right)
	r1.Position = UDim2.fromOffset(w - 112, 14); r1.Size = UDim2.fromOffset(96, 22)
	local r1k = text(card, "WLk", "W-L", 11, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Right)
	r1k.Position = UDim2.fromOffset(w - 112, 36); r1k.Size = UDim2.fromOffset(96, 14)
	if place then
		local r2 = text(card, "Place", ("#%d"):format(place), 12, T.ACCENT, T.FONT_HEAVY, Enum.TextXAlignment.Right)
		r2.Position = UDim2.fromOffset(w - 112, 52); r2.Size = UDim2.fromOffset(96, 14)
	end
	return y + h
end

local function row(parent: Instance, i: number, r: any, w: number): Frame
	local mine = r.id == me.UserId
	local f = new("Frame", { Name = "Row" .. i, BorderSizePixel = 0, BackgroundColor3 = if mine then T.CARD_HI else T.CARD,
		BackgroundTransparency = if mine or i % 2 == 1 then 0 else 0.4, Size = UDim2.fromOffset(w, 38), LayoutOrder = i }, parent)
	T.corner(f, 5)
	if mine then T.edge(f, T.ACCENT, 0.55) end
	local n = text(f, "Place", tostring(i), 14, if i <= 3 then T.TEXT else T.MUTED, T.FONT_HEAVY, Enum.TextXAlignment.Center)
	n.Position = UDim2.fromOffset(4, 0); n.Size = UDim2.fromOffset(34, 38)
	local b = RankedStyle.badge(f, 30, r.v)
	b.Position = UDim2.fromOffset(42, 4)
	local nm = text(f, "Name", tostring(r.name or "?"), 14, T.TEXT, T.FONT_BOLD)
	nm.Position = UDim2.fromOffset(82, 0); nm.Size = UDim2.fromOffset(w - 82 - 250, 38)
	nm.TextTruncate = Enum.TextTruncate.AtEnd
	local v = r.v or {}
	local tag = modeTag(v)
	local rk = text(f, "Rank", tostring(v.name or "") .. (if tag ~= "" then "  ·  " .. tag else ""), 12, RankedStyle.color(v), T.FONT_HEAVY, Enum.TextXAlignment.Right)
	rk.Position = UDim2.fromOffset(w - 250, 0); rk.Size = UDim2.fromOffset(170, 38)
	local rp = text(f, "RP", ("%d RP"):format(v.rp or 0), 13, T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Right)
	rp.Position = UDim2.fromOffset(w - 76, 0); rp.Size = UDim2.fromOffset(64, 38)
	return f
end

local seasonL: TextLabel? = nil
function Board.refresh()
	for _, c in panel:GetChildren() do if c:IsA("GuiObject") then c:Destroy() end end
	-- fits the screen (a phone in landscape is short: the list scrolls)
	local cam = workspace.CurrentCamera
	local view = S.fake or (if cam then cam.ViewportSize else Vector2.new(1280, 720))
	local sc = T.scaleNow()
	local W = math.floor(math.min(560, view.X / sc - 24))
	local H = math.floor(math.min(600, view.Y / sc - 24))
	panel.Size = UDim2.fromOffset(W, H)
	local inner = W - 40
	-- the header
	local kick = text(panel, "Kicker", "RANKED", 12, T.MUTED, T.FONT_BOLD)
	kick.Position = UDim2.fromOffset(20, 16); kick.Size = UDim2.fromOffset(200, 14)
	local title = text(panel, "Title", "LEADERBOARD", 24, T.TEXT, T.FONT_TITLE)
	title.Position = UDim2.fromOffset(20, 30); title.Size = UDim2.fromOffset(300, 30)
	local sl = text(panel, "Season", seasonLine(), 12, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Right)
	sl.Position = UDim2.fromOffset(W - 20 - 36 - 260, 22); sl.Size = UDim2.fromOffset(250, 16)
	seasonL = sl
	local x = button(panel, "Close", "X", 32, 32)
	x.Position = UDim2.fromOffset(W - 20 - 32, 16); x.TextColor3 = T.TEXT
	x.MouseButton1Click:Connect(function() Board.close() end)
	-- the tabs, and the scope switch when the global lists are on
	local y = 72
	for i, t in { { id = "duels", label = "DUELS" }, { id = "party", label = "PARTY RANKED" } } do
		local on = S.tab == t.id
		local b = button(panel, "Tab" .. t.id, t.label, 130, 30)
		b.Position = UDim2.fromOffset(20 + (i - 1) * 136, y)
		b.BackgroundColor3 = if on then T.CARD_HI else T.CARD
		b.TextColor3 = if on then T.TEXT else T.MUTED
		if on then
			new("Frame", { Name = "Under", BorderSizePixel = 0, BackgroundColor3 = T.ACCENT, AnchorPoint = Vector2.new(0.5, 1),
				Position = UDim2.new(0.5, 0, 1, -2), Size = UDim2.fromOffset(60, 2) }, b)
		end
		b.MouseButton1Click:Connect(function() if S.tab ~= t.id then S.tab = t.id; Board.refresh() end end)
	end
	local d = S.data
	if d and d.cross then
		for i, t in { { id = "server", label = "THIS SERVER" }, { id = "global", label = "GLOBAL" } } do
			local on = S.scope == t.id
			local b = button(panel, "Scope" .. t.id, t.label, 100, 30)
			b.Position = UDim2.fromOffset(W - 20 - 206 + (i - 1) * 106, y)
			b.BackgroundColor3 = if on then T.CARD_HI else T.CARD
			b.TextColor3 = if on then T.TEXT else T.MUTED
			b.MouseButton1Click:Connect(function()
				if S.scope ~= t.id then S.scope = t.id; Board.refresh(); task.spawn(Board.fetch) end
			end)
		end
	else
		local sv = text(panel, "Scope", "THIS SERVER", 11, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Right)
		sv.Position = UDim2.fromOffset(W - 20 - 200, y + 8); sv.Size = UDim2.fromOffset(200, 14)
	end
	y += 42
	-- your own rank on this tab
	local list = {}
	if d then
		if S.scope == "global" and type(d.global) == "table" then list = d.global[S.tab] or {} else list = d[S.tab] or {} end
	end
	local place = nil
	for i, r in list do if r.id == me.UserId then place = i end end
	local mine = if d and d.me then d.me[S.tab] else nil
	y = meBlock(panel, y, inner, mine, place) + 14
	-- the list
	local hdr = new("Frame", { Name = "Head", BackgroundTransparency = 1, Position = UDim2.fromOffset(20, y), Size = UDim2.fromOffset(inner, 14) }, panel)
	for _, c in { { "#", 4, 34, Enum.TextXAlignment.Center }, { "PLAYER", 82, 200, Enum.TextXAlignment.Left }, { "RANK", inner - 250, 170, Enum.TextXAlignment.Right },
		{ "RP", inner - 76, 64, Enum.TextXAlignment.Right } } do
		local l = text(hdr, "H", c[1] :: string, 11, T.MUTED, T.FONT_BOLD, c[4] :: Enum.TextXAlignment)
		l.Position = UDim2.fromOffset(c[2] :: number, 0); l.Size = UDim2.fromOffset(c[3] :: number, 14)
	end
	y += 20
	local sf = new("ScrollingFrame", { Name = "List", BackgroundTransparency = 1, BorderSizePixel = 0, Position = UDim2.fromOffset(20, y),
		Size = UDim2.fromOffset(inner + 6, H - y - 16), CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y,
		ScrollBarThickness = 4, ScrollBarImageColor3 = T.MUTED, ScrollingDirection = Enum.ScrollingDirection.Y }, panel)
	new("UIListLayout", { Padding = UDim.new(0, 4), SortOrder = Enum.SortOrder.LayoutOrder }, sf)
	if not d then
		local l = text(sf, "Wait", "LOADING", 12, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center)
		l.Size = UDim2.fromOffset(inner, 40)
	elseif #list == 0 then
		local l = text(sf, "Empty", if S.scope == "global" then "NO RANKED PLAYERS YET" else "NO RANKED PLAYERS IN THIS SERVER YET", 12, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center)
		l.Size = UDim2.fromOffset(inner, 40)
	else
		for i, r in list do row(sf, i, r, inner) end
	end
end

function Board.fetch()
	local r = ask("board", S.scope == "global")
	if type(r) == "table" and r.ok then
		S.data = r
		S.got = os.clock()
		if not r.cross then S.scope = "server" end
	end
	if S.open then Board.refresh() end
end

-- ------------------------------------------------------------------ open / close
local saved: any = nil
local function controls(on: boolean)
	pcall(function()
		local c = require(me:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: any):GetControls()
		if on then c:Enable() else c:Disable() end
	end)
end
function Board.isOpen(): boolean return S.open end
function Board.open(tab: string?)
	if me:GetAttribute("Zone") == "match" then return end
	if tab == "duels" or tab == "party" then S.tab = tab end
	if S.open then Board.refresh(); return end
	S.open = true
	saved = me:GetAttribute("LoadoutOpen")
	me:SetAttribute("LoadoutOpen", true) -- (a menu is up: hands and movement hold still, the mouse is free)
	if not PlayUI.isOpen() then controls(false) end
	gui.Enabled = true
	Board.refresh()
	task.spawn(Board.fetch)
end
function Board.close()
	if not S.open then return end
	S.open = false
	gui.Enabled = false
	if not PlayUI.isOpen() then
		me:SetAttribute("LoadoutOpen", if saved == true then true else false)
		controls(true)
	end
end
function Board.toggle(tab: string?) if S.open then Board.close() else Board.open(tab) end end
function Board.fakeScreen(v: Vector2?) S.fake = v; if S.open then Board.refresh() end end

UIS.InputBegan:Connect(function(io)
	if S.open and io.KeyCode == Enum.KeyCode.Escape then Board.close() end
end)
local tick = 0
RunService.RenderStepped:Connect(function(dt)
	if not S.open then return end
	UIS.MouseBehavior = Enum.MouseBehavior.Default
	if me:GetAttribute("Zone") == "match" then Board.close(); return end
	tick += dt
	if tick > 1 then
		tick = 0
		if seasonL and seasonL.Parent then seasonL.Text = seasonLine() end
	end
end)

return Board
