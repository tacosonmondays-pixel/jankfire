--!strict
-- THE MATCH SCOREBOARD's look (21 Nov 2026, the owner: "when you press tab in match I want it to pull upa coreboard").
-- 27 Nov 2026: the owner's pick from the ui-mocks sheet, direction B BROADCAST (UiKit.luau): a broadcast score bug at
-- the top (the round on a skew tab, each side's score on its own colour, the clock between), the map under it, then
-- each side as a black table. Your row is white with a cut corner; your party is held by a Butter bracket; a player who
-- is down has a greyed, struck-through head and a dim name. Big numbers are Oswald, words Builder Sans.
-- Everything you see is drawn here and only here. Scoreboard.client decides when it shows and fetches the board
-- (server/Scoreboard.luau's shape: mode, ranked, ffa, cols, round, teams = { { t, name, wins, rows } }); the rest
-- (level, party, down or up, the map, the clock) this reads on the client from the players' own attributes.
--   UI.mount(gui)        build the holder in a ScreenGui (once)
--   UI.render(board)     draw a board (nil: nothing to show)
--   UI.show(on)          show or hide it
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local T = require(script.Parent:WaitForChild("Theme")) :: any
local K = require(script.Parent:WaitForChild("UiKit")) :: any
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local TeamColors = require(Shared:WaitForChild("TeamColors")) :: any
local RankedStyle = require(Shared:WaitForChild("RankedStyle")) :: any
local okArena, Arena = pcall(function() return require(Shared:WaitForChild("Arena", 5) :: any) end)

local UI = {}
local B = K.B

-- the look (design pixels: the HUD's 720-tall frame, Theme.scaled). the mock was 1080 tall: these are its sizes / 1.5
local LOOK = {
	W = 654, -- a table's width
	TOP = 27, -- the score bug's top
	CELL_W = 100, CELL_H = 80, -- a side's score cell
	CLOCK_W = 120,
	TAB_W = 72, TAB_H = 19, -- the ROUND tab on top of the bug
	MAP = 22, -- the map's name under the bug
	TABLES = 196, -- where the first table starts
	TEAM_H = 30, -- a side's name over its table
	HEAD_H = 26, -- the column names
	ROW_H = 36, -- a player (shrinks when many have to fit)
	GAP = 14, -- between sides
	NUM_W = 31, -- a number column
	WIDE_W = 64, -- a classic mode's own column (RUNG, LIVES)
	DMG_W = 50,
	PING_W = 46,
	BADGE = 20,
	FACE = 24, -- a head
	CUT = 11, -- your row's cut corner
	DIM_A = 0.45, -- the dim over the world behind the board
	EMPTY = "–",
	PING_BAD = 180,
}

local board: Frame? = nil
local dim: Frame? = nil

function UI.mount(gui: ScreenGui)
	-- the world dims behind the board, no blur (you're still in the fight)
	gui.DisplayOrder = math.max(gui.DisplayOrder, 40) -- (over the between-rounds weapon picker)
	dim = K.new("Frame", { Name = "Dim", BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = LOOK.DIM_A, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), Visible = false }, gui)
	local holder = T.scaled(gui)
	board = K.new("Frame", { Name = "Board", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0, 0), Size = UDim2.new(0, LOOK.W, 1, 0), Visible = false }, holder)
end

local function clear(f: Instance)
	for _, c in f:GetChildren() do c:Destroy() end
end

-- the number columns from the right edge: { label, width }, PING last
local function columns(b: any): { { any } }
	local out = {}
	for _, c in b.cols do
		local s = tostring(c)
		local w = if #b.cols <= 2 and #s > 2 then LOOK.WIDE_W elseif #s > 1 then LOOK.DMG_W else LOOK.NUM_W
		table.insert(out, { K.sentence(s), w })
	end
	table.insert(out, { "Ping", LOOK.PING_W })
	return out
end

local function playerOf(uid: any): Player?
	if type(uid) ~= "number" or uid <= 0 then return nil end
	return Players:GetPlayerByUserId(uid)
end
-- down = a Humanoid at 0 health. no body or no Humanoid yet (respawning, loading) is unknown: shown as up
local function isDown(p: Player?): boolean
	if not p then return false end
	local c = p.Character
	local h = c and c:FindFirstChildOfClass("Humanoid")
	return h ~= nil and h.Health <= 0
end

-- the score bug: [ROUND n] tab over each side's score on its colour, the clock between (team modes)
local function bug(p: Frame, b: any)
	local me = Players.LocalPlayer
	local teams = b.teams
	local cells = if b.ffa then 0 else #teams
	local w = cells * LOOK.CELL_W + LOOK.CLOCK_W
	local x = (LOOK.W - w) / 2
	local y = LOOK.TOP + LOOK.TAB_H - 2
	local half = math.ceil(cells / 2)
	local function cell(tm: any)
		local f = K.new("Frame", { Name = "Score", BackgroundColor3 = TeamColors.color(tm.t), BorderSizePixel = 0, Position = UDim2.fromOffset(x, y), Size = UDim2.fromOffset(LOOK.CELL_W, LOOK.CELL_H) }, p)
		local n = K.text(f, "N", tostring(tonumber(tm.wins) or 0), 60, B.INK, K.COND, Enum.TextXAlignment.Center)
		n.Size = UDim2.fromScale(1, 1)
		x += LOOK.CELL_W
	end
	for i = 1, half do cell(teams[i]) end
	-- the clock: the round's time left, or the break's
	local clockF = K.new("Frame", { Name = "Clock", BackgroundColor3 = B.SLAB, BorderSizePixel = 0, Position = UDim2.fromOffset(x, y), Size = UDim2.fromOffset(LOOK.CLOCK_W, LOOK.CELL_H) }, p)
	local now = workspace:GetServerTimeNow()
	local ends = me:GetAttribute("RoundEnds")
	local win = me:GetAttribute("LoadoutWindow")
	local left = if type(ends) == "number" then ends - now elseif type(win) == "number" then win - now else 0
	local ct = K.text(clockF, "T", K.clock(left), 40, B.TEXT, K.COND, Enum.TextXAlignment.Center)
	ct.Size = UDim2.fromScale(1, 1)
	x += LOOK.CLOCK_W
	for i = half + 1, cells do cell(teams[i]) end
	-- the round, on a white skew tab sitting on the bug
	if type(b.round) == "number" and b.round > 0 then
		local tab = K.skew(p, UDim2.fromOffset((LOOK.W - LOOK.TAB_W) / 2, LOOK.TOP), LOOK.TAB_W, LOOK.TAB_H, B.WHITE, 6, 2)
		local tt = K.text(tab, "Round", "ROUND " .. b.round, 12, B.INK, K.COND, Enum.TextXAlignment.Center)
		tt.Size = UDim2.fromScale(1, 1)
		tt.ZIndex = 3
	end
	-- the map, and the mode under it
	local title = ""
	if okArena and type(Arena) == "table" then
		local ok, t = pcall(Arena.title, me:GetAttribute("Arena"))
		if ok and type(t) == "string" then title = t end
	end
	local mt = K.text(p, "Map", string.upper(title), LOOK.MAP, B.TEXT, K.COND, Enum.TextXAlignment.Center)
	mt.Position = UDim2.fromOffset(0, y + LOOK.CELL_H + 6)
	mt.Size = UDim2.fromOffset(LOOK.W, LOOK.MAP + 4)
	mt.TextStrokeTransparency = 0.7
	local mode = string.lower(tostring(b.mode or ""))
	if b.ranked then mode = "ranked " .. mode end
	local md = K.text(p, "Mode", string.upper(string.sub(mode, 1, 1)) .. string.sub(mode, 2), 13, B.MUTED, K.SANS_BOLD, Enum.TextXAlignment.Center)
	md.Position = UDim2.fromOffset(0, y + LOOK.CELL_H + 10 + LOOK.MAP)
	md.Size = UDim2.fromOffset(LOOK.W, 16)
	md.TextStrokeTransparency = 0.8
end

-- the number cells of a row (or the column names), right to left
local function numbers(parent: Instance, cols: { { any } }, values: { any }?, ping: number?, hh: number, color: Color3, font: Font, size: number, header: boolean, z: number)
	local x = LOOK.W - 12
	for i = #cols, 1, -1 do
		local c = cols[i]
		x -= c[2]
		local txt: string
		local tc = color
		if header then
			txt = c[1]
		elseif i == #cols then
			txt = if ping then tostring(ping) else LOOK.EMPTY
			tc = if ping and ping >= LOOK.PING_BAD then B.DANGER else color
		else
			local v = values and values[i]
			txt = if v == nil then LOOK.EMPTY else tostring(v)
		end
		local l = K.text(parent, "C" .. i, txt, size, tc, font, Enum.TextXAlignment.Center)
		l.Position = UDim2.fromOffset(x, 0)
		l.Size = UDim2.fromOffset(c[2], hh)
		l.ZIndex = z
	end
end

-- a side's table: its name in its colour, the column names, the rows. returns the y under it
local function sideTable(p: Frame, b: any, cols: { { any } }, title: string?, col: Color3?, rows: { any }, y: number, rowH: number, chips: { [any]: Color3 }?): number
	local me = Players.LocalPlayer
	local myParty = me:GetAttribute("Party")
	if title then
		local tn = K.text(p, "Team", string.upper(title), 24, col or B.TEXT, K.COND)
		tn.Position = UDim2.fromOffset(0, y)
		tn.Size = UDim2.fromOffset(300, LOOK.TEAM_H)
		tn.TextStrokeTransparency = 0.75
		y += LOOK.TEAM_H + 2
	end
	local h = LOOK.HEAD_H + #rows * rowH
	local slab = K.new("Frame", { Name = "Table", BackgroundColor3 = B.SLAB, BackgroundTransparency = B.SLAB_A, BorderSizePixel = 0, Position = UDim2.fromOffset(0, y), Size = UDim2.fromOffset(LOOK.W, h) }, p)
	numbers(slab, cols, nil, nil, LOOK.HEAD_H, B.MUTED, K.SANS_BOLD, 13, true, 2)
	local ph = K.text(slab, "PlayerHead", "Player", 13, B.MUTED, K.SANS_BOLD)
	ph.Position = UDim2.fromOffset(50, 0)
	ph.Size = UDim2.fromOffset(120, LOOK.HEAD_H)
	local yy = LOOK.HEAD_H
	local partyRows: { number } = {} -- the rows (top y) of your party in this table, for the bracket
	for _, r in rows do
		local mine = r.uid == me.UserId
		local pl = playerOf(r.uid)
		local down = (not r.empty) and isDown(pl)
		local rowF = K.new("Frame", { Name = "Row", BackgroundColor3 = if mine then B.WHITE else B.SLAB, BackgroundTransparency = if mine then 0 else 1, BorderSizePixel = 0, Position = UDim2.fromOffset(0, yy), Size = UDim2.fromOffset(LOOK.W, rowH), ZIndex = 2 }, slab)
		K.new("Frame", { Name = "Line", BackgroundColor3 = B.LINE, BorderSizePixel = 0, Size = UDim2.new(1, 0, 0, 1), ZIndex = 2 }, rowF)
		if mine then K.cut(rowF, LOOK.CUT, B.SLAB) end
		local fg = if mine then B.INK else B.TEXT
		if r.empty then
			local l = K.text(rowF, "Name", "Empty", 15, B.DIM, K.SANS_BOLD)
			l.Position = UDim2.fromOffset(50, 0)
			l.Size = UDim2.fromOffset(200, rowH)
			l.ZIndex = 3
		else
			if chips and chips[r] then
				K.new("Frame", { Name = "Chip", BackgroundColor3 = chips[r], BorderSizePixel = 0, Size = UDim2.new(0, 4, 1, 0), ZIndex = 3 }, rowF)
			end
			-- the head (greyed and struck through while they're down)
			local hb = K.new("Frame", { Name = "Face", BackgroundColor3 = if mine then Color3.fromRGB(214, 212, 206) else Color3.fromRGB(42, 44, 49), BorderSizePixel = 0, Position = UDim2.fromOffset(12, (rowH - LOOK.FACE) / 2), Size = UDim2.fromOffset(LOOK.FACE, LOOK.FACE), ZIndex = 3 }, rowF)
			K.new("UICorner", { CornerRadius = UDim.new(0, 4) }, hb)
			local img = K.head(r.uid)
			if img ~= "" then
				K.new("ImageLabel", { Name = "Img", BackgroundTransparency = 1, Image = img, Size = UDim2.fromScale(1, 1), ZIndex = 4, ImageTransparency = if down then 0.65 else 0 }, hb)
			end
			if down then
				hb.BackgroundTransparency = 0.5
				local s = K.new("Frame", { Name = "Down", BackgroundColor3 = B.TEXT, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(math.floor(LOOK.FACE * 1.3), 2), Rotation = -45, ZIndex = 5 }, hb)
				K.new("UIStroke", { Color = B.SLAB, Thickness = 1 }, s)
			end
			local x = 12 + LOOK.FACE + 14
			if b.ranked and r.rank then
				local holder = K.new("Frame", { Name = "Rank", BackgroundTransparency = 1, Position = UDim2.fromOffset(x - 4, (rowH - LOOK.BADGE) / 2), Size = UDim2.fromOffset(LOOK.BADGE, LOOK.BADGE), ZIndex = 3 }, rowF)
				pcall(RankedStyle.badge, holder, LOOK.BADGE, r.rank)
				x += LOOK.BADGE + 2
			end
			-- the name and the level side by side (a list lays the level after the name, whatever its width)
			local nr = K.new("Frame", { Name = "NameRow", BackgroundTransparency = 1, Position = UDim2.fromOffset(x, 0), Size = UDim2.fromOffset(330, rowH), ZIndex = 3 }, rowF)
			K.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, 8), SortOrder = Enum.SortOrder.LayoutOrder }, nr)
			local name = K.text(nr, "Name", tostring(r.name or ""), 16, fg, K.SANS_BOLD)
			name.AutomaticSize = Enum.AutomaticSize.X
			name.Size = UDim2.fromOffset(0, rowH)
			name.ZIndex = 3
			name.LayoutOrder = 1
			if down then name.TextTransparency = 0.55 end
			local lvl = pl and pl:GetAttribute("Level")
			if type(lvl) == "number" and b.allLevels then
				local lv = K.text(nr, "Level", "LV " .. lvl, 11, if mine then Color3.fromRGB(110, 108, 104) else B.MUTED, K.SANS_HEAVY)
				lv.AutomaticSize = Enum.AutomaticSize.X
				lv.Size = UDim2.fromOffset(0, rowH)
				lv.Position = UDim2.fromOffset(0, 1)
				lv.ZIndex = 3
				lv.LayoutOrder = 2
				if down then lv.TextTransparency = 0.55 end
			end
			numbers(rowF, cols, r.v or {}, r.ping, rowH, fg, K.COND, 22, false, 3)
			local pingL = rowF:FindFirstChild("C" .. #cols) :: TextLabel?
			if pingL and not mine and not (r.ping and r.ping >= LOOK.PING_BAD) then pingL.TextColor3 = B.MUTED end
			if myParty ~= nil and pl and pl:GetAttribute("Party") == myParty then table.insert(partyRows, yy) end
		end
		yy += rowH
	end
	-- your party: a Butter bracket left of the table over each run of rows next to each other (only with a mate in it)
	if #partyRows >= 2 then
		local i = 1
		while i <= #partyRows do
			local j = i
			while j < #partyRows and partyRows[j + 1] == partyRows[j] + rowH do j += 1 end
			if j > i then
				local top, bot = y + partyRows[i] + 5, y + partyRows[j] + rowH - 5
				K.new("Frame", { Name = "Party", BackgroundColor3 = B.BUTTER, BorderSizePixel = 0, Position = UDim2.fromOffset(-14, top), Size = UDim2.fromOffset(2, bot - top) }, p)
				K.new("Frame", { Name = "PartyT", BackgroundColor3 = B.BUTTER, BorderSizePixel = 0, Position = UDim2.fromOffset(-14, top), Size = UDim2.fromOffset(6, 2) }, p)
				K.new("Frame", { Name = "PartyB", BackgroundColor3 = B.BUTTER, BorderSizePixel = 0, Position = UDim2.fromOffset(-14, bot - 2), Size = UDim2.fromOffset(6, 2) }, p)
			end
			i = j + 1
		end
	end
	return y + h
end

local function byKills(a: any, b: any): boolean
	if (a.empty == true) ~= (b.empty == true) then return not a.empty end
	local av, bv = a.v or {}, b.v or {}
	local a1, b1 = tonumber(av[1]) or 0, tonumber(bv[1]) or 0
	if a1 ~= b1 then return a1 > b1 end
	return (tonumber(av[2]) or 0) < (tonumber(bv[2]) or 0)
end

function UI.render(b: any?)
	local p = board
	if not p then return end
	clear(p)
	if type(b) ~= "table" or type(b.teams) ~= "table" then
		p.Visible = false
		if dim then dim.Visible = false end
		return
	end
	local cols = columns(b)
	-- (every player row has a level, or none shows: a stand-in has none)
	b.allLevels = true
	for _, tm in b.teams do
		for _, r in tm.rows do
			if not r.empty then
				local pl = playerOf(r.uid)
				if not (pl and type(pl:GetAttribute("Level")) == "number") then b.allLevels = false end
			end
		end
	end
	bug(p, b)
	-- the rows have to fit under the bug: shrink them when there are many
	local n, sides = 0, 0
	for _, tm in b.teams do n += #tm.rows; sides += 1 end
	if b.ffa then sides = 1 end
	local room = 708 - LOOK.TABLES - sides * (LOOK.TEAM_H + 2 + LOOK.HEAD_H + LOOK.GAP)
	local rowH = math.clamp(math.floor(room / math.max(1, n)), 24, LOOK.ROW_H)
	local y = LOOK.TABLES
	if b.ffa then
		local all, chips = {}, {}
		for _, tm in b.teams do for _, r in tm.rows do table.insert(all, r); chips[r] = TeamColors.color(tm.t) end end
		table.sort(all, byKills)
		sideTable(p, b, cols, nil, nil, all, y, rowH, chips)
	else
		for i, tm in b.teams do
			if i > 1 then y += LOOK.GAP end
			local rows = table.clone(tm.rows)
			table.sort(rows, byKills)
			y = sideTable(p, b, cols, tostring(tm.name or ""), TeamColors.color(tm.t), rows, y, rowH, nil)
		end
	end
end

function UI.show(on: boolean)
	local p = board
	if p and not on then p.Visible = false end
	if p and on and #p:GetChildren() > 0 then p.Visible = true end
	if dim then dim.Visible = p ~= nil and p.Visible end
	local open = p ~= nil and p.Visible
	if Players.LocalPlayer:GetAttribute("BoardOpen") ~= (if open then true else nil) then Players.LocalPlayer:SetAttribute("BoardOpen", if open then true else nil) end
end

return UI
