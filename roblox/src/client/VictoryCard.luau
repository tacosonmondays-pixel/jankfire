--!strict
-- THE MATCH'S STATS CARD (27 Nov 2026; shared/VictoryData.luau has the why). It comes up over the victory scene's held
-- shot (client/VictoryScene.luau) and replaces FightHud's old end screen while VictoryData.ON. A PLATE, the owner's pick
-- for the match HUD (client/UiKit.luau, roblox/docs/ui-mocks): one bone plate, near-square, ink words, the stencil slit
-- only through the hero word and the score; colour only for teams. Its numbers are the same counts the Tab board shows
-- (Scoreboard.board) and the same XP the level plate shows, so they add up across screens.
--   Card.show(d)              d = { result, sub, tiles = { { n, color, mine } }, place, cols, mine = { numbers },
--                                   level = { lv, from, to, gain }, mastery = { { name, lv, from, to, gain } },
--                                   coins, quests = { { text, n, goal, done } }, board = { { color, name, rows } },
--                                   boardCols, compact }
--   Card.rewards(d)           the same table: redraws the rewards (they settle a moment after the match ends)
--   Card.wait(n, label)       the drain bar at the bottom ("Back to the hub in %d")
--   Card.skip(on)             the SKIP chip (SPACE / B) while the scene runs
--   Card.hide()   Card.visible()
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local me = Players.LocalPlayer
local K = require(script.Parent:WaitForChild("UiKit")) :: any
local A = K.A

local Card = {}
Card.onSkip = nil :: (() -> ())?

local W = 404 -- design pixels (a 720-tall screen; the holder scales with the screen)
local PAD = 22

local gui = K.new("ScreenGui", { Name = "JankVictoryCard", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 47,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling, Enabled = false }, me:WaitForChild("PlayerGui"))
local holder = K.new("Frame", { Name = "Scaled", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, gui)
local scale = K.new("UIScale", {}, holder)
local compact = false
local function fit()
	local cam = workspace.CurrentCamera
	local vp = if cam then cam.ViewportSize else Vector2.new(1280, 720)
	compact = vp.Y < 560 or me:GetAttribute("TouchOn") == true
	local s = if compact then math.clamp(vp.Y / 520, 0.6, 1) else math.clamp(vp.Y / 720, 0.8, 2)
	scale.Scale = s
	holder.Size = UDim2.fromScale(1 / s, 1 / s)
end
fit()
do
	local cam = workspace.CurrentCamera
	if cam then cam:GetPropertyChangedSignal("ViewportSize"):Connect(fit) end
end

-- the plate, and a soft shadow under it (critic round 1: the bone plate all but vanished on the bright set)
local shade = K.new("Frame", { Name = "Shade", BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 0.72, BorderSizePixel = 0,
	AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -44, 0.5, 6), Size = UDim2.fromOffset(W + 4, 404) }, holder)
K.new("UICorner", { CornerRadius = UDim.new(0, 5) }, shade)
local plate = K.new("Frame", { Name = "Plate", BackgroundColor3 = A.BONE, BorderSizePixel = 0, AnchorPoint = Vector2.new(1, 0.5),
	Position = UDim2.new(1, -48, 0.5, 0), Size = UDim2.fromOffset(W, 400) }, holder)
K.new("UICorner", { CornerRadius = UDim.new(0, 3) }, plate)
local body = K.new("Frame", { Name = "Body", BackgroundTransparency = 1, Position = UDim2.fromOffset(PAD, PAD - 4), Size = UDim2.new(1, -2 * PAD, 1, -2 * PAD) }, plate)
local list = K.new("UIListLayout", { SortOrder = Enum.SortOrder.LayoutOrder, Padding = UDim.new(0, 0) }, body)
-- the foot: the wait and the skip chip live under the plate's body, always at its bottom
local foot = K.new("Frame", { Name = "Foot", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(0, PAD, 1, -16),
	Size = UDim2.new(1, -2 * PAD, 0, 30) }, plate)
local waitT = K.text(foot, "Wait", "", 13, A.INK2, K.SANS)
waitT.Size = UDim2.new(1, -150, 0, 16)
local waitN = K.text(foot, "Secs", "", 14, A.INK, K.SANS_HEAVY, Enum.TextXAlignment.Right) -- (the seconds left, on the right)
waitN.AnchorPoint = Vector2.new(1, 0); waitN.Position = UDim2.new(1, 0, 0, 0); waitN.Size = UDim2.new(0, 40, 0, 16)
local track = K.new("Frame", { Name = "Track", BackgroundColor3 = A.BONE2, BorderSizePixel = 0, Position = UDim2.fromOffset(0, 22), Size = UDim2.new(1, 0, 0, 4) }, foot)
local fill = K.new("Frame", { Name = "Fill", BackgroundColor3 = A.INK, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1) }, track)
local skipB = K.new("TextButton", { Name = "Skip", AutoButtonColor = false, BackgroundColor3 = A.INK, BorderSizePixel = 0, AnchorPoint = Vector2.new(1, 0),
	Position = UDim2.new(1, 0, 0, -4), Size = UDim2.fromOffset(100, 22), Text = "", Visible = false, ZIndex = 3 }, foot)
K.new("UICorner", { CornerRadius = UDim.new(0, 3) }, skipB)
local skipWord = K.text(skipB, "Word", "SKIP", 12, A.BONE, K.SANS_HEAVY)
skipWord.Position = UDim2.fromOffset(10, 0); skipWord.Size = UDim2.new(0, 40, 1, 0)
local skipKey = K.text(skipB, "Key", "SPACE", 11, A.BONE, K.SANS_BOLD, Enum.TextXAlignment.Right)
skipKey.Position = UDim2.new(1, -60, 0, 0); skipKey.Size = UDim2.new(0, 52, 1, 0); skipKey.TextTransparency = 0.35
skipB.Activated:Connect(function() if Card.onSkip then (Card.onSkip :: () -> ())() end end)
local function keyWord()
	local pad = UserInputService.GamepadEnabled and (UserInputService:GetLastInputType().Name:sub(1, 7) == "Gamepad")
	local touch = UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled
	skipKey.Text = if pad then "B" elseif touch then "" else "SPACE"
end

-- ------------------------------------------------------------------ pieces
local order = 0
local function nextOrder(): number order += 1; return order end
local function gap(h: number)
	K.new("Frame", { Name = "Gap", BackgroundTransparency = 1, LayoutOrder = nextOrder(), Size = UDim2.new(1, 0, 0, h) }, body)
end
local function label(text: string): TextLabel
	local l = K.text(body, "Label", string.upper(text), 11, A.INK2, K.SANS_BOLD)
	l.LayoutOrder = nextOrder(); l.Size = UDim2.new(1, 0, 0, 16)
	return l
end
local function fmt(n: number): string
	local s = tostring(math.floor(n + 0.5))
	local out = s:reverse():gsub("(%d%d%d)", "%1,"):reverse()
	return (out:gsub("^,", ""))
end
local function bar(parent: Instance, pos: UDim2, size: UDim2, from: number, to: number, delay: number)
	local tr = K.new("Frame", { Name = "Bar", BackgroundColor3 = A.BONE2, BorderSizePixel = 0, Position = pos, Size = size }, parent)
	local was = K.new("Frame", { Name = "Was", BackgroundColor3 = A.INK2, BorderSizePixel = 0, Size = UDim2.fromScale(math.clamp(from, 0, 1), 1) }, tr)
	local now = K.new("Frame", { Name = "Now", BackgroundColor3 = A.INK, BorderSizePixel = 0, Position = UDim2.fromScale(math.clamp(from, 0, 1), 0),
		Size = UDim2.fromScale(0, 1) }, tr)
	local w = math.max(0, math.clamp(to, 0, 1) - math.clamp(from, 0, 1))
	-- (a level gained: the bar starts over from empty)
	if to < from then was.Size = UDim2.fromScale(0, 1); now.Position = UDim2.fromScale(0, 0); w = math.clamp(to, 0, 1) end
	task.delay(delay, function()
		if now.Parent then TweenService:Create(now, TweenInfo.new(0.6, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), { Size = UDim2.fromScale(w, 1) }):Play() end
	end)
	return tr
end
-- a number that counts up from 0 once it's on screen
local function countUp(l: TextLabel, n: number, prefix: string?, delay: number)
	l.Text = (prefix or "") .. "0"
	task.delay(delay, function()
		local t0 = os.clock()
		while l.Parent and os.clock() - t0 < 0.55 do
			local u = 1 - (1 - (os.clock() - t0) / 0.55) ^ 3
			l.Text = (prefix or "") .. fmt(n * u)
			task.wait()
		end
		if l.Parent then l.Text = (prefix or "") .. fmt(n) end
	end)
end

-- ------------------------------------------------------------------ the sections
local function head(d: any)
	local h = K.new("Frame", { Name = "Head", BackgroundTransparency = 1, LayoutOrder = nextOrder(), Size = UDim2.new(1, 0, 0, 74) }, body)
	local word = K.text(h, "Result", d.result or "", 52, A.INK, K.SANS_HEAVY)
	word.Size = UDim2.new(1, -120, 0, 54)
	K.slit(word, 0.56, 0.07) -- (the stencil slit: the hero word only)
	local sub = K.text(h, "Sub", string.upper(d.sub or ""), 12, A.INK2, K.SANS_BOLD)
	sub.Position = UDim2.fromOffset(2, 54); sub.Size = UDim2.new(1, -120, 0, 16); sub.TextTruncate = Enum.TextTruncate.AtEnd
	-- the score: one flat tile per side in its colour, yours first and full, the others dimmed (the HUD's own tiles)
	local tiles = d.tiles or {}
	local x = 0
	for i = #tiles, 1, -1 do
		local t = tiles[i]
		local tw = 46
		local tile = K.new("Frame", { Name = "Tile" .. i, BackgroundColor3 = t.color, BackgroundTransparency = if t.mine then 0 else 0.5,
			BorderSizePixel = 0, AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -x, 0, 6), Size = UDim2.fromOffset(tw, 46) }, h)
		K.new("UICorner", { CornerRadius = UDim.new(0, 3) }, tile)
		local n = K.text(tile, "N", tostring(t.n), 30, A.INK, K.SANS_HEAVY, Enum.TextXAlignment.Center)
		n.Size = UDim2.fromScale(1, 1)
		if not t.mine then n.TextTransparency = 0.35 end
		x += tw + 6
		if #tiles > 2 and x > 140 then break end
	end
	if d.place then
		local pl = K.text(h, "Place", d.place, 13, A.INK, K.SANS_HEAVY, Enum.TextXAlignment.Right)
		pl.AnchorPoint = Vector2.new(1, 0); pl.Position = UDim2.new(1, 0, 0, 54); pl.Size = UDim2.fromOffset(120, 16)
	end
end

-- the board: each side under its own name and score; your row in ink. its numbers are the Tab board's own
local COLW = 46
local function board(d: any)
	local sides = d.board or {}
	if #sides == 0 then return end
	local cols = d.boardCols or {}
	local rowsN = 0
	for _, s in sides do rowsN += #(s.rows or {}) end
	local rh = if d.compact or rowsN > 6 then 20 else 23
	local ts = if d.compact or rowsN > 6 then 12 else 13
	for si, s in sides do
		-- the side's line: its colour, its name, its score; the columns' names on the first one
		local hd = K.new("Frame", { Name = "Side" .. si, BackgroundTransparency = 1, LayoutOrder = nextOrder(), Size = UDim2.new(1, 0, 0, 20) }, body)
		local chip = K.new("Frame", { Name = "Team", BackgroundColor3 = s.color, BorderSizePixel = 0, Position = UDim2.fromOffset(0, 5), Size = UDim2.fromOffset(10, 10) }, hd)
		K.new("UICorner", { CornerRadius = UDim.new(0, 2) }, chip)
		local nm = K.text(hd, "Name", string.upper(tostring(s.name or "")) .. (if s.score then ("  " .. tostring(s.score)) else ""), 12, A.INK, K.SANS_HEAVY)
		nm.Position = UDim2.fromOffset(16, 0); nm.Size = UDim2.new(1, -16 - COLW * #cols, 1, 0)
		if si == 1 then
			for ci, c in cols do
				local hc = K.text(hd, "H" .. ci, string.upper(c), 11, A.INK2, K.SANS_BOLD, Enum.TextXAlignment.Right)
				hc.AnchorPoint = Vector2.new(1, 0); hc.Position = UDim2.new(1, -8 - COLW * (#cols - ci), 0, 0); hc.Size = UDim2.new(0, COLW - 4, 1, 0)
			end
		end
		for ri, r in s.rows or {} do
			local row = K.new("Frame", { Name = ("S%dR%d"):format(si, ri), BackgroundColor3 = A.INK, BackgroundTransparency = if r.mine then 0 else 1,
				BorderSizePixel = 0, LayoutOrder = nextOrder(), Size = UDim2.new(1, 0, 0, rh) }, body)
			if r.mine then K.new("UICorner", { CornerRadius = UDim.new(0, 2) }, row) end
			local tc = if r.mine then A.BONE else A.INK
			local rn = K.text(row, "Name", tostring(r.name or ""), ts, tc, K.SANS_HEAVY)
			rn.Position = UDim2.fromOffset(16, 0); rn.Size = UDim2.new(1, -16 - COLW * #cols, 1, 0); rn.TextTruncate = Enum.TextTruncate.AtEnd
			for ci = 1, #cols do
				local val = tonumber((r.v or {})[ci]) or 0
				local v = K.text(row, "V" .. ci, fmt(val), ts, tc, if r.mine then K.SANS_HEAVY else K.SANS_BOLD, Enum.TextXAlignment.Right)
				v.AnchorPoint = Vector2.new(1, 0); v.Position = UDim2.new(1, -8 - COLW * (#cols - ci), 0, 0); v.Size = UDim2.new(0, COLW - 4, 1, 0)
			end
		end
		if si < #sides then gap(12) end
	end
end

local rewardsBox: Frame? = nil
local function rewardRow(parent: Instance, i: number, name: string, tag: string?, gain: string?, from: number?, to: number?)
	local r = K.new("Frame", { Name = "R" .. i, BackgroundTransparency = 1, LayoutOrder = i, Size = UDim2.new(1, 0, 0, 30) }, parent)
	local nm = K.text(r, "Name", name, 14, A.INK, K.SANS_HEAVY)
	nm.Size = UDim2.new(0.5, 0, 0, 18); nm.TextTruncate = Enum.TextTruncate.AtEnd
	if tag then
		local tg = K.text(r, "Tag", tag, 12, A.INK2, K.SANS_BOLD)
		tg.Position = UDim2.new(0.5, 4, 0, 0); tg.Size = UDim2.new(0.3, 0, 0, 18)
	end
	if gain then
		local g = K.text(r, "Gain", gain, 14, A.INK, K.SANS_HEAVY, Enum.TextXAlignment.Right)
		g.AnchorPoint = Vector2.new(1, 0); g.Position = UDim2.new(1, 0, 0, 0); g.Size = UDim2.new(0.25, 0, 0, 18)
	end
	if from and to then bar(r, UDim2.fromOffset(0, 21), UDim2.new(1, 0, 0, 4), from, to, 0.4 + 0.08 * i) end
	return r
end
-- what the match gave you, one row each (no row for what it didn't): the level and its XP, each weapon's mastery, coins,
-- the quests that moved. their own box, so a later redraw keeps its spot
local function fillRewards(box: Frame, d: any)
	for _, c in box:GetChildren() do if not c:IsA("UIListLayout") then c:Destroy() end end
	local i = 0
	local lv = d.level
	if lv and (lv.gain or 0) > 0 then
		i += 1
		rewardRow(box, i, "LEVEL " .. tostring(lv.lv), nil, "+" .. fmt(lv.gain) .. " XP", lv.from, lv.to)
	end
	for _, m in d.mastery or {} do
		if i >= (if d.compact then 3 else 5) then break end
		i += 1
		rewardRow(box, i, string.upper(m.name), "MASTERY " .. tostring(m.lv), "+" .. fmt(m.gain), m.from, m.to)
	end
	if (d.coins or 0) ~= 0 then
		i += 1
		rewardRow(box, i, "COINS", nil, (if d.coins > 0 then "+" else "") .. fmt(d.coins))
	end
	for _, q in d.quests or {} do
		if i >= (if d.compact then 4 else 7) then break end
		i += 1
		local r = rewardRow(box, i, q.text, nil, if q.done then "DONE" else (tostring(q.n) .. "/" .. tostring(q.goal)), q.from, math.clamp(q.n / math.max(1, q.goal), 0, 1))
		local nm = r:FindFirstChild("Name") :: TextLabel?
		if nm then nm.FontFace = K.SANS; nm.Size = UDim2.new(0.75, 0, 0, 18); nm.TextSize = 13 end
	end
	if i == 0 then
		local none = K.text(box, "None", if lv then ("Level " .. tostring(lv.lv) .. ". Practice and private matches give no XP.") else "No XP this match.", 13, A.INK2, K.SANS)
		none.LayoutOrder = 1; none.Size = UDim2.new(1, 0, 0, 18); none.TextWrapped = true
	end
end
local function rewards(d: any)
	local f = K.new("Frame", { Name = "Rewards", BackgroundTransparency = 1, LayoutOrder = nextOrder(), AutomaticSize = Enum.AutomaticSize.Y,
		Size = UDim2.new(1, 0, 0, 0) }, body)
	K.new("UIListLayout", { SortOrder = Enum.SortOrder.LayoutOrder, Padding = UDim.new(0, 4) }, f)
	rewardsBox = f
	fillRewards(f, d)
end

-- ------------------------------------------------------------------ show / hide
local shown: any = nil
local function size()
	local h = list.AbsoluteContentSize.Y / scale.Scale
	plate.Size = UDim2.fromOffset(W, math.floor(h + PAD + 4 + 54))
	shade.Size = UDim2.fromOffset(W + 4, plate.Size.Y.Offset + 4)
end
list:GetPropertyChangedSignal("AbsoluteContentSize"):Connect(size)

function Card.show(d: any)
	fit()
	d.compact = compact
	shown = d
	order = 0
	for _, c in body:GetChildren() do if not c:IsA("UIListLayout") then c:Destroy() end end
	head(d)
	gap(16)
	board(d)
	gap(16)
	rewards(d)
	gap(8)
	keyWord()
	gui.Enabled = true
	-- in from the right, quick
	plate.Position = UDim2.new(1, -12, 0.5, 0)
	plate.BackgroundTransparency = 0.2
	shade.Position = UDim2.new(1, -8, 0.5, 6)
	TweenService:Create(plate, TweenInfo.new(0.32, Enum.EasingStyle.Quart, Enum.EasingDirection.Out),
		{ Position = UDim2.new(1, -48, 0.5, 0), BackgroundTransparency = 0 }):Play()
	TweenService:Create(shade, TweenInfo.new(0.32, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), { Position = UDim2.new(1, -44, 0.5, 6) }):Play()
	task.defer(size)
end

function Card.rewards(d: any)
	if not shown or not rewardsBox or not rewardsBox.Parent then return end
	shown.level, shown.mastery, shown.coins, shown.quests = d.level, d.mastery, d.coins, d.quests
	fillRewards(rewardsBox, shown)
	task.defer(size)
end

local waitTok = 0
function Card.wait(n: number, lab: string?)
	waitTok += 1
	local my = waitTok
	fill.Size = UDim2.fromScale(1, 1)
	TweenService:Create(fill, TweenInfo.new(math.max(0.1, n), Enum.EasingStyle.Linear), { Size = UDim2.fromScale(0, 1) }):Play()
	-- (the server's words, "back to the hub in %d" / "play of the match in %d": the words on the left, the seconds on the
	-- right, each with its unit)
	local words = string.gsub(lab or "back to the hub in %d", "%s*in %%d%s*$", "")
	words = string.gsub(words, "%%d", "")
	waitT.Text = string.upper(string.sub(words, 1, 1)) .. string.sub(words, 2)
	task.spawn(function()
		local t0 = os.clock()
		while my == waitTok and os.clock() - t0 < n do
			waitN.Text = tostring(math.max(0, math.ceil(n - (os.clock() - t0)))) .. " s"
			task.wait(0.2)
		end
	end)
end
function Card.skip(on: boolean)
	keyWord()
	skipB.Visible = on
end
function Card.hide()
	waitTok += 1
	shown = nil
	gui.Enabled = false
	skipB.Visible = false
	waitT.Text = ""; waitN.Text = ""
end
function Card.visible(): boolean return gui.Enabled end
function Card.gui(): ScreenGui return gui end

return Card
