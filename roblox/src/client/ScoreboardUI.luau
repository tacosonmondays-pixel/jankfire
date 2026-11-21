--!strict
-- THE MATCH SCOREBOARD's look (21 Nov 2026, the owner: "when you press tab in match I want it to pull upa coreboard").
-- Everything you see is drawn here and only here, so a restyle (the UI art direction being mocked) is this file alone:
-- the sizes and colours are the LOOK table below, built from Theme (the match HUD's plates and Builder fonts) and the
-- teams' colours from Shared.TeamColors. Scoreboard.client decides when it shows and fetches the board
-- (server/Scoreboard.luau's shape: mode, ranked, ffa, cols, round, teams = { { t, name, wins, rows } }).
--   UI.mount(gui)        build the holder in a ScreenGui (once)
--   UI.render(board)     draw a board (nil: nothing to show)
--   UI.show(on)          show or hide it
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local T = require(script.Parent:WaitForChild("Theme")) :: any
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local TeamColors = require(Shared:WaitForChild("TeamColors")) :: any
local RankedStyle = require(Shared:WaitForChild("RankedStyle")) :: any

local UI = {}

-- the look (design pixels: the HUD's 720-tall frame, Theme.scaled)
local LOOK = {
	W = 560, -- the panel's width
	Y = 0.46, -- its middle, down the screen
	PAD = 12, -- inside the panel
	HEAD_H = 40, -- the mode, the round, the score
	COLS_H = 20, -- the column names
	TEAM_H = 26, -- a side's strip (team modes)
	ROW_H = 30, -- a player
	GAP = 8, -- between sides
	NUM_W = 52, -- a number column
	WIDE_W = 74, -- a classic mode's own column (RUNG, LIVES)
	PING_W = 56,
	BADGE = 22, -- a ranked match's rank badge
	ME_BG = T.CARD_HI, -- your own row
	ROW_BG = T.CARD,
	ROW_A = 0.35, -- a row's see-through
	EMPTY = "—",
	PING_BAD = 180, -- ms: red from here
}

local root: Frame? = nil
local panel: Frame? = nil

function UI.mount(gui: ScreenGui)
	local holder = T.scaled(gui)
	root = holder
	local p = T.plate(holder, "Board", UDim2.fromScale(0.5, LOOK.Y), UDim2.fromOffset(LOOK.W, 100))
	p.AnchorPoint = Vector2.new(0.5, 0.5)
	p.Visible = false
	panel = p
end

local function clear(f: Instance)
	for _, c in f:GetChildren() do
		if not c:IsA("UICorner") and not c:IsA("UIStroke") then c:Destroy() end
	end
end

-- the number columns from the right edge: { label, width } (PING last)
local function columns(board: any): { { any } }
	local out = {}
	for _, c in board.cols do
		local w = if #board.cols <= 2 and string.len(c) > 2 then LOOK.WIDE_W else LOOK.NUM_W
		table.insert(out, { c, w })
	end
	table.insert(out, { "PING", LOOK.PING_W })
	return out
end

local function numberCells(parent: Frame, cols: { { any } }, values: { any }, ping: number?, y: number, h: number, header: boolean, color: Color3?)
	local x = LOOK.W - LOOK.PAD
	for i = #cols, 1, -1 do
		local c = cols[i]
		x -= c[2]
		local txt: string
		local col = color or T.TEXT
		if header then
			txt = c[1]
			col = T.MUTED
		elseif i == #cols then
			txt = if ping then tostring(ping) else LOOK.EMPTY
			col = if ping and ping >= LOOK.PING_BAD then T.DANGER else T.MUTED
		else
			local v = values[i]
			txt = if v == nil then LOOK.EMPTY else tostring(v)
		end
		local l = T.text(parent, "C" .. i, txt, if header then 11 else 15, col, if header then T.FONT_BOLD else T.FONT_BOLD, Enum.TextXAlignment.Center)
		l.Position = UDim2.fromOffset(x, y)
		l.Size = UDim2.fromOffset(c[2], h)
	end
	return x -- (where the numbers start: the name ends before it)
end

local function row(parent: Frame, board: any, cols: { { any } }, r: any, y: number, mine: boolean, chip: Color3?)
	local bg = T.new("Frame", { Name = "Row", BackgroundColor3 = if mine then LOOK.ME_BG else LOOK.ROW_BG, BackgroundTransparency = if mine then 0.1 else LOOK.ROW_A,
		BorderSizePixel = 0, Position = UDim2.fromOffset(LOOK.PAD, y), Size = UDim2.fromOffset(LOOK.W - LOOK.PAD * 2, LOOK.ROW_H - 2) }, parent)
	T.corner(bg, 4)
	if mine then T.edge(bg, T.ACCENT, 0.2, 1) end
	local x = LOOK.PAD + 10
	if chip then
		local c = T.new("Frame", { Name = "Chip", BackgroundColor3 = chip, BorderSizePixel = 0, Position = UDim2.fromOffset(LOOK.PAD + 6, y + 7), Size = UDim2.fromOffset(4, LOOK.ROW_H - 16) }, parent)
		T.corner(c, 2)
		x = LOOK.PAD + 16
	end
	if r.empty then
		local l = T.text(parent, "Name", "EMPTY", 13, T.DIM, T.FONT_BOLD)
		l.Position = UDim2.fromOffset(x, y)
		l.Size = UDim2.fromOffset(200, LOOK.ROW_H - 2)
		return
	end
	if board.ranked and r.rank then
		local holder = T.new("Frame", { Name = "Rank", BackgroundTransparency = 1, Position = UDim2.fromOffset(x - 2, y + (LOOK.ROW_H - 2 - LOOK.BADGE) / 2), Size = UDim2.fromOffset(LOOK.BADGE, LOOK.BADGE) }, parent)
		pcall(RankedStyle.badge, holder, LOOK.BADGE, r.rank)
		x += LOOK.BADGE + 4
	end
	local nx = numberCells(parent, cols, r.v or {}, r.ping, y, LOOK.ROW_H - 2, false, nil)
	local l = T.text(parent, "Name", tostring(r.name or ""), 15, if mine then T.TEXT else T.SOFT, if mine then T.FONT_HEAVY else T.FONT_BOLD)
	l.Position = UDim2.fromOffset(x, y)
	l.Size = UDim2.fromOffset(math.max(40, nx - x - 6), LOOK.ROW_H - 2)
	l.TextTruncate = Enum.TextTruncate.AtEnd
end

function UI.render(board: any?)
	local p = panel
	if not p then return end
	clear(p)
	if type(board) ~= "table" or type(board.teams) ~= "table" then p.Visible = false; return end
	local myUid = Players.LocalPlayer.UserId
	local cols = columns(board)
	local y = LOOK.PAD
	-- the head: the mode and round on the left, the score on the right (each side's wins in its colour)
	local mode = T.text(p, "Mode", tostring(board.mode or ""), 18, T.TEXT, T.FONT_TITLE)
	mode.Position = UDim2.fromOffset(LOOK.PAD + 4, y)
	mode.Size = UDim2.fromOffset(200, LOOK.HEAD_H - 8)
	if type(board.round) == "number" and board.round > 0 then
		local rd = T.text(p, "Round", "ROUND " .. board.round, 12, T.MUTED, T.FONT_BOLD)
		rd.Position = UDim2.fromOffset(LOOK.PAD + 4, y + LOOK.HEAD_H - 16)
		rd.Size = UDim2.fromOffset(200, 14)
	end
	local parts = {}
	for _, tm in board.teams do table.insert(parts, ('<font color="%s">%d</font>'):format(TeamColors.hex(tm.t), tonumber(tm.wins) or 0)) end
	local score = T.text(p, "Score", table.concat(parts, '<font color="#6a707a">  –  </font>'), 22, T.TEXT, T.FONT_TITLE, Enum.TextXAlignment.Right)
	score.RichText = true
	score.Position = UDim2.fromOffset(LOOK.W - LOOK.PAD - 300, y)
	score.Size = UDim2.fromOffset(300 - 4, LOOK.HEAD_H - 8)
	y += LOOK.HEAD_H
	-- the column names
	numberCells(p, cols, {}, nil, y, LOOK.COLS_H, true, nil)
	local nm = T.text(p, "NameHead", "PLAYER", 11, T.MUTED, T.FONT_BOLD)
	nm.Position = UDim2.fromOffset(LOOK.PAD + 10, y)
	nm.Size = UDim2.fromOffset(120, LOOK.COLS_H)
	y += LOOK.COLS_H + 2
	if board.ffa then
		-- free-for-all: everyone in one list, the best first, a chip of their side's colour
		local all = {}
		for _, tm in board.teams do for _, r in tm.rows do table.insert(all, { r = r, t = tm.t }) end end
		table.sort(all, function(a, b)
			if (a.r.empty == true) ~= (b.r.empty == true) then return not a.r.empty end
			local av, bv = a.r.v or {}, b.r.v or {}
			local a1, b1 = tonumber(av[1]) or 0, tonumber(bv[1]) or 0
			if a1 ~= b1 then return a1 > b1 end
			return (tonumber(av[2]) or 0) < (tonumber(bv[2]) or 0)
		end)
		for _, x in all do
			row(p, board, cols, x.r, y, x.r.uid == myUid, TeamColors.color(x.t))
			y += LOOK.ROW_H
		end
	else
		for i, tm in board.teams do
			if i > 1 then y += LOOK.GAP end
			local col = TeamColors.color(tm.t)
			local bar = T.new("Frame", { Name = "TeamBar", BackgroundColor3 = col, BorderSizePixel = 0, Position = UDim2.fromOffset(LOOK.PAD, y + 4), Size = UDim2.fromOffset(4, LOOK.TEAM_H - 8) }, p)
			T.corner(bar, 2)
			local tn = T.text(p, "Team", string.upper(tostring(tm.name or "")), 14, col, T.FONT_HEAVY)
			tn.Position = UDim2.fromOffset(LOOK.PAD + 12, y)
			tn.Size = UDim2.fromOffset(220, LOOK.TEAM_H)
			local tw = T.text(p, "Wins", tostring(tonumber(tm.wins) or 0), 16, col, T.FONT_HEAVY, Enum.TextXAlignment.Right)
			tw.Position = UDim2.fromOffset(LOOK.W - LOOK.PAD - 80, y)
			tw.Size = UDim2.fromOffset(76, LOOK.TEAM_H)
			y += LOOK.TEAM_H
			local rows = table.clone(tm.rows)
			table.sort(rows, function(a, b)
				if (a.empty == true) ~= (b.empty == true) then return not a.empty end
				local av, bv = a.v or {}, b.v or {}
				return (tonumber(av[1]) or 0) > (tonumber(bv[1]) or 0)
			end)
			for _, r in rows do
				row(p, board, cols, r, y, r.uid == myUid, nil)
				y += LOOK.ROW_H
			end
		end
	end
	y += LOOK.PAD - 2
	p.Size = UDim2.fromOffset(LOOK.W, y)
end

function UI.show(on: boolean)
	local p = panel
	if p and not on then p.Visible = false end
	if p and on and #p:GetChildren() > 2 then p.Visible = true end
end

return UI
