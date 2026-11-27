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
local TOP = 92 -- (the plate's top, pinned: critic round 3 - it sat at a different height on every screen)
local top = TOP -- (a short screen: near the top edge)
local plateH = 400
-- the screen: the camera's, or a Studio test's phone-sized box (the player attribute FakeScreen, set by TouchTest's
-- "fake:WxH": the card lays itself out in that box, as on a phone)
local function screen(): (Vector2, boolean)
	local f = me:GetAttribute("FakeScreen")
	if typeof(f) == "Vector2" then return f, true end
	local cam = workspace.CurrentCamera
	return (if cam then cam.ViewportSize else Vector2.new(1280, 720)), false
end
local function fit()
	local vp, fake = screen()
	compact = vp.Y < 560 or me:GetAttribute("TouchOn") == true
	top = if compact then 16 else TOP
	local s = if compact then math.clamp(vp.Y / 520, 0.6, 1) else math.clamp(vp.Y / 720, 0.8, 2)
	-- (a tall card on a short screen shrinks to fit it: a 4v4 card with its rewards and the picks ran off a 390-point
	-- phone, 27 Nov)
	s = math.max(0.45, math.min(s, vp.Y / (top + plateH + 14)))
	scale.Scale = s
	if fake then
		holder.AnchorPoint, holder.Position = Vector2.new(0.5, 0.5), UDim2.fromScale(0.5, 0.5)
		holder.Size = UDim2.fromOffset(vp.X / s, vp.Y / s)
	else
		holder.AnchorPoint, holder.Position = Vector2.zero, UDim2.new()
		holder.Size = UDim2.fromScale(1 / s, 1 / s)
	end
end
fit()
do
	local cam = workspace.CurrentCamera
	if cam then cam:GetPropertyChangedSignal("ViewportSize"):Connect(fit) end
	me:GetAttributeChangedSignal("FakeScreen"):Connect(function() task.defer(fit) end)
end

-- the plate, and a soft shadow under it (critic round 1: the bone plate all but vanished on the bright set)
local shade = K.new("Frame", { Name = "Shade", BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 0.6, BorderSizePixel = 0,
	AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -44, 0, TOP + 6), Size = UDim2.fromOffset(W + 4, 404) }, holder)
K.new("UICorner", { CornerRadius = UDim.new(0, 5) }, shade)
local plate = K.new("Frame", { Name = "Plate", BackgroundColor3 = A.BONE, BorderSizePixel = 0, AnchorPoint = Vector2.new(1, 0),
	Position = UDim2.new(1, -48, 0, TOP), Size = UDim2.fromOffset(W, 400) }, holder)
K.new("UICorner", { CornerRadius = UDim.new(0, 3) }, plate)
K.new("UIStroke", { Color = Color3.fromRGB(190, 186, 177), Thickness = 1, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, plate)
local body = K.new("Frame", { Name = "Body", BackgroundTransparency = 1, Position = UDim2.fromOffset(PAD, PAD - 4), Size = UDim2.new(1, -2 * PAD, 1, -2 * PAD) }, plate)
local list = K.new("UIListLayout", { SortOrder = Enum.SortOrder.LayoutOrder, Padding = UDim.new(0, 0) }, body)
-- the foot: the wait and the skip chip live under the plate's body, always at its bottom
local RIGHT = 10 -- (every number on the card ends on this right edge, and the ink row's text sits this far in from both)
local foot = K.new("Frame", { Name = "Foot", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(0, PAD, 1, -16),
	Size = UDim2.new(1, -2 * PAD, 0, 18) }, plate)
local waitT = K.text(foot, "Wait", "", 12, A.INK2, K.SANS_BOLD)
waitT.Size = UDim2.new(1, -150, 1, 0)
local waitN = K.text(foot, "Secs", "", 12, A.INK, K.SANS_HEAVY, Enum.TextXAlignment.Right) -- (the seconds left, on the right)
waitN.AnchorPoint = Vector2.new(1, 0); waitN.Position = UDim2.new(1, -RIGHT, 0, 0); waitN.Size = UDim2.new(0, 40, 1, 0)
local track = K.new("Frame", { Name = "Track", BackgroundColor3 = A.BONE2, BorderSizePixel = 0, AnchorPoint = Vector2.new(0, 1),
	Position = UDim2.new(0, PAD, 1, -8), Size = UDim2.new(1, -2 * PAD - RIGHT, 0, 2), Visible = false }, plate)
local fill = K.new("Frame", { Name = "Fill", BackgroundColor3 = A.INK, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1) }, track)
local skipB = K.new("TextButton", { Name = "Skip", AutoButtonColor = false, BackgroundColor3 = A.INK, BorderSizePixel = 0, AnchorPoint = Vector2.new(1, 0),
	Position = UDim2.new(1, -RIGHT, 0, -3), Size = UDim2.fromOffset(100, 22), Text = "", Visible = false, ZIndex = 3 }, foot)
K.new("UICorner", { CornerRadius = UDim.new(0, 3) }, skipB)
local skipWord = K.text(skipB, "Word", "SKIP", 12, A.BONE, K.SANS_HEAVY)
skipWord.Position = UDim2.fromOffset(10, 0); skipWord.Size = UDim2.new(0, 40, 1, 0)
local skipKey = K.text(skipB, "Key", "SPACE", 11, A.BONE, K.SANS_BOLD, Enum.TextXAlignment.Right)
skipKey.Position = UDim2.new(1, -60, 0, 0); skipKey.Size = UDim2.new(0, 52, 1, 0); skipKey.TextTransparency = 0.35
skipB.Activated:Connect(function() if Card.onSkip then (Card.onSkip :: () -> ())() end end)

-- PLAY AGAIN and LEAVE (27 Nov; the queue side is play-party-ranked's: Play "again" / "againview", PlayPush "again").
-- PLAY AGAIN is ink with the queue pads' lip under it (A PLATE: only what you press gets the lip); LEAVE is a bone key.
-- under them: what PLAY AGAIN queues, and the leader's pick or how many have picked
Card.onPick = nil :: ((boolean) -> ())?
local picks = K.new("Frame", { Name = "Picks", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(0, PAD, 1, -40),
	Size = UDim2.new(1, -2 * PAD - RIGHT, 0, 58), Visible = false }, plate)
local function keyCap(parent: Instance, text: string, color: Color3)
	local k = K.text(parent, "Key", text, 10, color, K.SANS_BOLD, Enum.TextXAlignment.Right)
	k.AnchorPoint = Vector2.new(1, 0); k.Position = UDim2.new(1, -10, 0, 0); k.Size = UDim2.new(0, 80, 1, 0); k.TextTransparency = 0.4
	return k
end
local againB = K.new("TextButton", { Name = "Again", AutoButtonColor = false, BackgroundColor3 = A.INK, BorderSizePixel = 0, Text = "",
	Size = UDim2.new(0.6, -4, 0, 34) }, picks)
K.new("UICorner", { CornerRadius = UDim.new(0, 3) }, againB)
K.new("Frame", { Name = "Lip", BackgroundColor3 = A.LIP, BorderSizePixel = 0, Position = UDim2.new(0, 2, 1, 0), Size = UDim2.new(1, -4, 0, 3) }, againB)
local againWord = K.text(againB, "Word", "PLAY AGAIN", 14, A.BONE, K.SANS_HEAVY)
againWord.Position = UDim2.fromOffset(12, 0); againWord.Size = UDim2.new(1, -90, 1, 0)
local againKey = keyCap(againB, "ENTER", A.BONE)
local leaveB = K.new("TextButton", { Name = "Leave", AutoButtonColor = false, BackgroundColor3 = A.BONE2, BorderSizePixel = 0, Text = "",
	AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, 0, 0, 0), Size = UDim2.new(0.4, -4, 0, 34) }, picks)
K.new("UICorner", { CornerRadius = UDim.new(0, 3) }, leaveB)
local leaveWord = K.text(leaveB, "Word", "LEAVE", 13, A.INK, K.SANS_HEAVY)
leaveWord.Position = UDim2.fromOffset(12, 0); leaveWord.Size = UDim2.new(1, -60, 1, 0)
local leaveKey = keyCap(leaveB, "BKSP", A.INK)
local queueT = K.text(picks, "Queue", "", 11, A.INK2, K.SANS_BOLD)
queueT.Position = UDim2.fromOffset(2, 42); queueT.Size = UDim2.new(0.6, -4, 0, 14)
local statusT = K.text(picks, "Status", "", 11, A.INK2, K.SANS_BOLD, Enum.TextXAlignment.Right)
statusT.AnchorPoint = Vector2.new(1, 0); statusT.Position = UDim2.new(1, 0, 0, 42); statusT.Size = UDim2.new(0.6, 0, 0, 14)
againB.Activated:Connect(function() if Card.onPick and againB.Visible then (Card.onPick :: (boolean) -> ())(true) end end)
leaveB.Activated:Connect(function() if Card.onPick then (Card.onPick :: (boolean) -> ())(false) end end)
local function pickKeys()
	local pad = UserInputService.GamepadEnabled and (UserInputService:GetLastInputType().Name:sub(1, 7) == "Gamepad")
	local touch = UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled
	againKey.Text = if pad then "A" elseif touch then "" else "ENTER"
	leaveKey.Text = if pad then "B" elseif touch then "" else "BKSP"
end
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
local instantBars = false -- (a redraw of the same rewards draws its bars as they are: no fill playing again)
local function bar(parent: Instance, pos: UDim2, size: UDim2, from: number, to: number, delay: number)
	local tr = K.new("Frame", { Name = "Bar", BackgroundColor3 = A.BONE2, BorderSizePixel = 0, Position = pos, Size = size }, parent)
	local was = K.new("Frame", { Name = "Was", BackgroundColor3 = A.LIP, BorderSizePixel = 0, Size = UDim2.fromScale(math.clamp(from, 0, 1), 1) }, tr)
	local now = K.new("Frame", { Name = "Now", BackgroundColor3 = A.INK, BorderSizePixel = 0, Position = UDim2.fromScale(math.clamp(from, 0, 1), 0),
		Size = UDim2.fromScale(0, 1) }, tr)
	local w = math.max(0, math.clamp(to, 0, 1) - math.clamp(from, 0, 1))
	-- (a level gained: the bar starts over from empty)
	if to < from then was.Size = UDim2.fromScale(0, 1); now.Position = UDim2.fromScale(0, 0); w = math.clamp(to, 0, 1) end
	if instantBars then now.Size = UDim2.fromScale(w, 1); return tr end
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
	local sub = K.text(h, "Sub", d.sub or "", 12, A.INK2, K.SANS_BOLD)
	sub.Position = UDim2.fromOffset(2, 54); sub.Size = UDim2.new(1, -120, 0, 16); sub.TextTruncate = Enum.TextTruncate.AtEnd
	-- the score: one flat tile per side in its colour (the HUD's own tiles). yours first and big, level with the word's
	-- top; the others small and faded, sitting on its baseline
	local tiles = d.tiles or {}
	local x = RIGHT
	for i = #tiles, 1, -1 do
		local t = tiles[i]
		local tw = 50
		local tile = K.new("Frame", { Name = "Tile" .. i, BackgroundColor3 = if t.won then t.color else A.BONE, BorderSizePixel = 0,
			AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -x, 0, 4), Size = UDim2.fromOffset(tw, tw) }, h)
		K.new("UICorner", { CornerRadius = UDim.new(0, 3) }, tile)
		if not t.won then K.new("UIStroke", { Color = t.color:Lerp(A.INK, 0.35), Thickness = 2, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, tile) end
		local n = K.text(tile, "N", tostring(t.n), 32, A.INK, K.SANS_HEAVY, Enum.TextXAlignment.Center)
		n.Size = UDim2.fromScale(1, 1)
		local nm = K.text(h, "TileName" .. i, string.upper(tostring(t.name or "")), 11, A.INK2, K.SANS_BOLD, Enum.TextXAlignment.Center)
		nm.AnchorPoint = Vector2.new(1, 0); nm.Position = UDim2.new(1, -x + 6, 0, 57); nm.Size = UDim2.fromOffset(tw + 12, 12)
		x += tw + 8
		if #tiles > 2 and x > 150 then break end
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
	local rh = if d.compact or rowsN > 6 then 21 else 24
	local ts = if d.compact or rowsN > 6 then 13 else 14
	local shownSides = {}
	for _, s in sides do
		if #(s.rows or {}) > 0 then
			local rows = table.clone(s.rows)
			table.sort(rows, function(a, b)
				local ka, kb = tonumber((a.v or {})[1]) or 0, tonumber((b.v or {})[1]) or 0
				if ka ~= kb then return ka > kb end
				return (tonumber((a.v or {})[#cols]) or 0) > (tonumber((b.v or {})[#cols]) or 0)
			end)
			table.insert(shownSides, { name = s.name, color = s.color, rows = rows })
		end
	end
	sides = shownSides
	for si, s in sides do
		-- the side's line: its colour, its name, its score; the columns' names on the first one
		local hd = K.new("Frame", { Name = "Side" .. si, BackgroundTransparency = 1, LayoutOrder = nextOrder(), Size = UDim2.new(1, 0, 0, 20) }, body)
		if s.name ~= "" then
			local chip = K.new("Frame", { Name = "Team", BackgroundColor3 = s.color, BorderSizePixel = 0, Position = UDim2.fromOffset(0, 5), Size = UDim2.fromOffset(5, 10) }, hd)
			K.new("UICorner", { CornerRadius = UDim.new(0, 1) }, chip)
			local nm = K.text(hd, "Name", string.upper(tostring(s.name or "")), 13, A.INK, K.SANS_HEAVY)
			nm.Position = UDim2.fromOffset(RIGHT, 0); nm.Size = UDim2.new(1, -RIGHT - COLW * #cols, 1, 0)
		end
		if si == 1 then
			for ci, c in cols do
				local hc = K.text(hd, "H" .. ci, string.upper(c), 12, A.INK2, K.SANS_BOLD, Enum.TextXAlignment.Right)
				hc.AnchorPoint = Vector2.new(1, 0); hc.Position = UDim2.new(1, -RIGHT - COLW * (#cols - ci), 0, 0); hc.Size = UDim2.new(0, COLW - 4, 1, 0)
			end
		end
		for ri, r in s.rows or {} do
			local row = K.new("Frame", { Name = ("S%dR%d"):format(si, ri), BackgroundColor3 = A.INK, BackgroundTransparency = if r.mine then 0 else 1,
				BorderSizePixel = 0, LayoutOrder = nextOrder(), Size = UDim2.new(1, 0, 0, rh) }, body)
			if r.mine then K.new("UICorner", { CornerRadius = UDim.new(0, 2) }, row) end
			local tc = if r.mine then A.BONE else A.INK
			local rn = K.text(row, "Name", tostring(r.name or ""), ts, tc, if r.mine then K.SANS_HEAVY else K.SANS_BOLD)
			rn.Position = UDim2.fromOffset(RIGHT, 0); rn.Size = UDim2.new(1, -RIGHT - COLW * #cols, 1, 0); rn.TextTruncate = Enum.TextTruncate.AtEnd
			for ci = 1, #cols do
				local val = tonumber((r.v or {})[ci]) or 0
				local v = K.text(row, "V" .. ci, fmt(val), ts, tc, if r.mine then K.SANS_HEAVY else K.SANS_BOLD, Enum.TextXAlignment.Right)
				v.AnchorPoint = Vector2.new(1, 0); v.Position = UDim2.new(1, -RIGHT - COLW * (#cols - ci), 0, 0); v.Size = UDim2.new(0, COLW - 4, 1, 0)
			end
		end
		if si < #sides then gap(12) end
	end
end

local rewardsBox: Frame? = nil
local function rewardRow(parent: Instance, i: number, name: string, tag: string?, gain: string?, from: number?, to: number?)
	local r = K.new("Frame", { Name = "R" .. i, BackgroundTransparency = 1, LayoutOrder = i, Size = UDim2.new(1, 0, 0, if from and to then 30 else 22) }, parent)
	local line = K.new("Frame", { Name = "Line", BackgroundTransparency = 1, Size = UDim2.new(1, -110, 0, 18) }, r)
	K.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, VerticalAlignment = Enum.VerticalAlignment.Center,
		Padding = UDim.new(0, 8), SortOrder = Enum.SortOrder.LayoutOrder }, line)
	local nm = K.text(line, "Name", name, 14, A.INK, K.SANS_HEAVY)
	nm.AutomaticSize = Enum.AutomaticSize.X; nm.Size = UDim2.fromOffset(0, 18); nm.LayoutOrder = 1
	if tag then
		local tg = K.text(line, "Tag", tag, 12, A.INK2, K.SANS_BOLD)
		tg.AutomaticSize = Enum.AutomaticSize.X; tg.Size = UDim2.fromOffset(0, 18); tg.LayoutOrder = 2
	end
	if gain then
		local g = K.text(r, "Gain", gain, 14, A.INK, K.SANS_HEAVY, Enum.TextXAlignment.Right)
		g.AnchorPoint = Vector2.new(1, 0); g.Position = UDim2.new(1, -RIGHT, 0, 0); g.Size = UDim2.new(0, 110, 0, 18)
	end
	if from and to then bar(r, UDim2.fromOffset(0, 21), UDim2.new(1, -RIGHT, 0, 5), from, to, 0.4 + 0.08 * i) end
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
		-- (the tag is where you are in the level, the same numbers the bar draws)
		local tag = if lv.up then "LEVEL UP" elseif lv.into and lv.need then (fmt(lv.into) .. " / " .. fmt(lv.need) .. " XP") else nil
		rewardRow(box, i, "LEVEL " .. tostring(lv.lv), tag, "+" .. fmt(lv.gain) .. " XP", lv.from, lv.to)
	end
	for _, m in d.mastery or {} do
		if i >= (if d.compact then 3 else 5) then break end
		i += 1
		rewardRow(box, i, string.upper(m.name), "MASTERY " .. tostring(m.lv), "+" .. fmt(m.gain) .. " XP", m.from, m.to)
	end
	for _, q in d.quests or {} do
		if i >= (if d.compact then 4 else 7) then break end
		i += 1
		local r = rewardRow(box, i, q.text, nil, if q.done then "DONE" else (tostring(q.n) .. " / " .. tostring(q.goal)), q.from, math.clamp(q.n / math.max(1, q.goal), 0, 1))
		local nm = r:FindFirstChild("Name", true) :: TextLabel?
		if nm then nm.FontFace = K.SANS_BOLD; nm.TextSize = 13 end
	end
	if (d.coins or 0) ~= 0 then
		i += 1
		rewardRow(box, i, "COINS", if d.wallet then fmt(d.wallet) else nil, (if d.coins > 0 then "+" else "") .. fmt(d.coins))
	end
	if i == 0 then
		local none = K.text(box, "None", "NO XP FROM THIS MATCH", 12, A.INK2, K.SANS_BOLD)
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
	plate.Size = UDim2.fromOffset(W, math.floor(h + PAD + 4 + 34 + (if picks.Visible then 62 else 0)))
	shade.Size = UDim2.fromOffset(W + 4, plate.Size.Y.Offset + 4)
	if math.abs(plate.Size.Y.Offset - plateH) > 1 then
		plateH = plate.Size.Y.Offset
		fit()
		plate.Position = UDim2.new(1, -48, 0, top)
		shade.Position = UDim2.new(1, -44, 0, top + 6)
	end
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
	plate.Position = UDim2.new(1, -12, 0, top)
	plate.BackgroundTransparency = 0.2
	shade.Position = UDim2.new(1, -8, 0, top + 6)
	TweenService:Create(plate, TweenInfo.new(0.32, Enum.EasingStyle.Quart, Enum.EasingDirection.Out),
		{ Position = UDim2.new(1, -48, 0, top), BackgroundTransparency = 0 }):Play()
	TweenService:Create(shade, TweenInfo.new(0.32, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), { Position = UDim2.new(1, -44, 0, top + 6) }):Play()
	task.defer(size)
end

local function sig(d: any): string
	local parts = { tostring(d.level and d.level.gain), tostring(d.level and d.level.lv), tostring(d.coins), tostring(d.wallet) }
	for _, m in d.mastery or {} do table.insert(parts, tostring(m.name) .. m.gain) end
	for _, q in d.quests or {} do table.insert(parts, tostring(q.text) .. q.n) end
	return table.concat(parts, "|")
end
function Card.rewards(d: any)
	if not shown or not rewardsBox or not rewardsBox.Parent then return end
	local was = sig(shown)
	shown.level, shown.mastery, shown.coins, shown.quests = d.level, d.mastery, d.coins, d.quests
	if d.wallet then shown.wallet = d.wallet end
	if sig(shown) == was then return end -- (nothing new: the bars keep playing as they are)
	instantBars = true
	fillRewards(rewardsBox, shown)
	instantBars = false
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
	words = string.gsub(string.gsub(words, "%%d", ""), " the ", " ")
	waitT.Text = string.upper(words)
	track.Visible = true
	task.spawn(function()
		local t0 = os.clock()
		while my == waitTok and os.clock() - t0 < n do
			waitN.Text = tostring(math.max(0, math.ceil(n - (os.clock() - t0))))
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
	picks.Visible = false
	waitT.Text = ""; waitN.Text = ""; track.Visible = false
end
-- the picks from the queue's view: { can, why, role, queue, pick, lead, picked, of } (nil: no picks offered)
function Card.again(view: any?)
	if type(view) ~= "table" then picks.Visible = false; task.defer(size); return end
	pickKeys()
	picks.Visible = true
	local can = view.can == true
	againB.Visible = can
	leaveB.Size = if can then UDim2.new(0.4, -4, 0, 34) else UDim2.new(1, 0, 0, 34)
	local member = view.role == "member"
	againWord.Text = if view.pick == "again" then (if member then "YOU'RE IN" else "QUEUED") else "PLAY AGAIN"
	leaveWord.Text = if view.pick == "leave" then "LEAVING" else "LEAVE"
	againB.BackgroundTransparency = if view.pick == "leave" then 0.6 else 0
	leaveB.BackgroundTransparency = if view.pick == "again" then 0.6 else 0
	queueT.Text = if can then string.upper(tostring(view.queue or "")) else string.upper(tostring(view.why or ""))
	local status = ""
	if member then
		status = if view.lead == "again" then "LEADER: PLAY AGAIN" elseif view.lead == "leave" then "LEADER: LEAVE" else "WAITING FOR THE LEADER"
	elseif type(view.picked) == "number" and type(view.of) == "number" and view.of > 1 then
		status = ("%d OF %d PICKED"):format(view.picked, view.of)
	end
	statusT.Text = status
	task.defer(size)
end
function Card.picksOn(): boolean return picks.Visible end
function Card.visible(): boolean return gui.Enabled end
function Card.gui(): ScreenGui return gui end

return Card
