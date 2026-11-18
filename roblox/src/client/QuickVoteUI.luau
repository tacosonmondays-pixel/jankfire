--!strict
-- the votes when a match forms (server/Party.luau), over the Play screen's big button:
--   the MODE (QUICKPLAY): 3 modes its head-count fits, tap one (or press 1, 2 or 3)
--   the MAP (QUICKPLAY and casual duels, 17 Nov 2026, the owner: "also add map selector before hand"): 3 maps from the
--   rotation as cards with their pictures (shared/MapCards.luau) and names, tap one (4, 5, 6 under a mode vote; 1, 2,
--   3 alone)
-- both run on the same PlayConfig.VOTE s clock. most votes wins, a tie is drawn; the picks show until the match starts.
-- everything comes from the party view (found.vote / pick, found.mvote / map), so a reopened screen or a respawn
-- shows it again:
--   QuickVoteUI.sync(found)   PlayClient, on every party view
-- and a hub PAD's map vote (18 Nov, the owner: "map select for pads please"): while you stand on a full pad, its
-- countdown is a map vote (server/Matches.luau, Matches.PAD_VOTE s), the same three cards, keys 1-3 or a tap:
--   QuickVoteUI.syncPad(msg)  PlayClient, on PlayPush { t = "padvote", vote?, map? } (no vote: it's gone)
-- a party match's vote, if there is one, has the panel first
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local T = require(script.Parent:WaitForChild("Theme"))
local PlayUI = require(script.Parent:WaitForChild("PlayUI"))
local Keys = require(script.Parent:WaitForChild("Keys"))

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")
local new, text = T.new, T.text

local QuickVoteUI = {}
-- the found view on screen: { vote = { options, ends, counts, mine }?, pick, mvote = { options, ends, counts, mine }?, map }
local cur: any = nil
local partyCur: any = nil -- (the party match's)
local padCur: any = nil -- (the pad's: { mvote, map, pad = true })
local modeIds: { string } = {}
local mapIds: { string } = {}
local fake: Vector2? = nil -- (tests: lay it out as on a screen this size, PlayTest "votefake:844x390")

local gui = new("ScreenGui", { Name = "JankVote", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 21,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling, Enabled = false }, pg)
local scaled = T.scaled(gui)
local panel = T.plate(scaled, "Vote", UDim2.new(0.5, 0, 1, -190), UDim2.fromOffset(592, 150))
panel.AnchorPoint = Vector2.new(0.5, 1)
do
	local s = panel:FindFirstChildOfClass("UIStroke")
	if s then s.Color = T.ACCENT; s.Transparency = 0.5 end
end
local head = text(panel, "Head", "VOTE FOR THE MODE", 14, T.TEXT, T.FONT_HEAVY)
local clock = text(panel, "Clock", "", 14, T.ACCENT, T.FONT_HEAVY, Enum.TextXAlignment.Right)
local mapHead = text(panel, "MapHead", "VOTE FOR THE MAP", 14, T.TEXT, T.FONT_HEAVY)
local cards: { GuiObject } = {}

local function send(op: string, id: string)
	task.spawn(function()
		local r = PlayUI.ask(op, id)
		if type(r) == "table" and not r.ok and type(r.why) == "string" then PlayUI.notice(r.why) end
	end)
end
local function vote(i: number)
	local id = modeIds[i]
	if not id or not cur or not cur.vote or cur.pick then return end
	cur.vote.mine = id
	QuickVoteUI.draw()
	send("vote", id)
end
local function voteMap(i: number)
	local id = mapIds[i]
	if not id or not cur or not cur.mvote or cur.map then return end
	cur.mvote.mine = id
	QuickVoteUI.draw()
	send(if cur.pad then "padvote" else "mapvote", id)
end

local function votesText(k: number): string
	return if k == 1 then "1 VOTE" elseif k > 1 then ("%d VOTES"):format(k) else ""
end

-- lay the panel out for the screen (a small screen: smaller cards) and fill it from cur
function QuickVoteUI.draw()
	for _, c in cards do c:Destroy() end
	table.clear(cards)
	if not cur or not (cur.vote or cur.mvote) then gui.Enabled = false; return end
	local cam = workspace.CurrentCamera
	local sz = fake or (if cam then cam.ViewportSize / T.scaleNow() else Vector2.new(1280, 720))
	local c = sz.Y < 560 or sz.X < 960
	local cw, ch, gap, pad = if c then 150 else 180, if c then 66 else 86, if c then 8 else 10, if c then 12 else 16
	local headH = if c then 30 else 38
	local modes = if cur.vote then cur.vote.options or {} else {}
	local maps = if cur.mvote then cur.mvote.options or {} else {}
	local n = math.max(1, #modes, #maps)
	local W = n * cw + (n - 1) * gap + pad * 2
	local thumbH = math.floor(cw * (if c then 0.5 else 9 / 16))
	local mapH = thumbH + (if c then 22 else 26)
	local y = 0
	table.clear(modeIds)
	table.clear(mapIds)
	local keyAt = 1

	head.Visible = #modes > 0
	if #modes > 0 then
		head.Position = UDim2.fromOffset(pad, if c then 8 else 12); head.Size = UDim2.fromOffset(W - pad * 2 - 60, 18)
		head.TextSize = if c then 12 else 14
		local pick = cur.pick
		head.Text = if pick then "PICKED" else "VOTE FOR THE MODE"
		local counts = cur.vote.counts or {}
		for i, o in modes do
			modeIds[i] = o.id
			local mine = cur.vote.mine == o.id
			local won = pick == o.id
			local b = new("TextButton", { Name = "Option" .. i, AutoButtonColor = false, BorderSizePixel = 0, Text = "",
				BackgroundColor3 = if won then T.ACCENT elseif mine then T.CARD_HI else T.CARD,
				BackgroundTransparency = if pick and not won then 0.55 else 0.05,
				Position = UDim2.fromOffset(pad + (i - 1) * (cw + gap), headH), Size = UDim2.fromOffset(cw, ch) }, panel)
			T.corner(b, 5)
			if mine and not won then T.edge(b, T.ACCENT, 0.3, 1) end
			local ink = if won then T.INK elseif pick then T.DIM else T.TEXT
			local nm = text(b, "Name", o.name or o.id, if c then 13 else 16, ink, T.FONT_TITLE)
			-- (a long name shrinks to fit rather than being cut: ONE IN THE CHAMBER, SPOONS & GRAPPLES)
			nm.Position = UDim2.fromOffset(10, if c then 6 else 9); nm.Size = UDim2.new(1, -40, 0, if c then 16 else 20); nm.TextScaled = true
			new("UITextSizeConstraint", { MaxTextSize = if c then 13 else 16, MinTextSize = 8 }, nm)
			local sb = text(b, "Sub", o.sub or "", if c then 9 else 10, if won then T.INK else T.MUTED, T.FONT)
			sb.Position = UDim2.fromOffset(10, if c then 24 else 30); sb.Size = UDim2.new(1, -20, 0, if c then 24 else 30)
			sb.TextWrapped = true; sb.TextYAlignment = Enum.TextYAlignment.Top; sb.TextTruncate = Enum.TextTruncate.AtEnd
			local vc = text(b, "Votes", votesText(counts[o.id] or 0), if c then 9 else 11, if won then T.INK else T.ACCENT, T.FONT_HEAVY)
			vc.Position = UDim2.new(0, 10, 1, if c then -15 else -19); vc.Size = UDim2.new(1, -20, 0, 14)
			if not pick then T.key(b, tostring(i), UDim2.new(1, -30, 0, 8)) end
			b.MouseButton1Click:Connect(function() vote(i) end)
			table.insert(cards, b)
		end
		y = headH + ch + (if c then 8 else 10)
		keyAt = 4
	end

	mapHead.Visible = #maps > 0
	if #maps > 0 then
		local my = y + (if c then 8 else 12)
		mapHead.Position = UDim2.fromOffset(pad, my); mapHead.Size = UDim2.fromOffset(W - pad * 2 - 60, 18)
		mapHead.TextSize = if c then 12 else 14
		local won = cur.map and cur.map.id
		mapHead.Text = if won then "MAP" else "VOTE FOR THE MAP"
		local counts = cur.mvote.counts or {}
		local top = my + headH - (if c then 8 else 12)
		for i, o in maps do
			mapIds[i] = o.id
			local mine = cur.mvote.mine == o.id
			local isWon = won == o.id
			local b = new("TextButton", { Name = "Map" .. i, AutoButtonColor = false, BorderSizePixel = 0, Text = "", ClipsDescendants = true,
				BackgroundColor3 = if isWon then T.ACCENT elseif mine then T.CARD_HI else T.CARD,
				BackgroundTransparency = if won and not isWon then 0.55 else 0.05,
				Position = UDim2.fromOffset(pad + (i - 1) * (cw + gap), top), Size = UDim2.fromOffset(cw, mapH) }, panel)
			T.corner(b, 5)
			if (mine and not isWon) or isWon then T.edge(b, T.ACCENT, if isWon then 0 else 0.3, if isWon then 2 else 1) end
			local pic = new("ImageLabel", { Name = "Thumb", BorderSizePixel = 0, BackgroundColor3 = T.BG, Image = o.thumb or "",
				ScaleType = Enum.ScaleType.Crop, ImageTransparency = if won and not isWon then 0.6 else 0,
				Position = UDim2.fromOffset(0, 0), Size = UDim2.new(1, 0, 0, thumbH) }, b)
			T.corner(pic, 5)
			local ink = if isWon then T.INK elseif won then T.DIM else T.TEXT
			local nm = text(b, "Name", o.title or o.id, if c then 11 else 13, ink, T.FONT_HEAVY)
			nm.Position = UDim2.fromOffset(8, thumbH + (if c then 4 else 5)); nm.Size = UDim2.new(1, -64, 0, if c then 14 else 16); nm.TextScaled = true
			new("UITextSizeConstraint", { MaxTextSize = if c then 11 else 13, MinTextSize = 7 }, nm)
			local vc = text(b, "Votes", votesText(counts[o.id] or 0), if c then 9 else 10, if isWon then T.INK else T.ACCENT, T.FONT_HEAVY, Enum.TextXAlignment.Right)
			vc.AnchorPoint = Vector2.new(1, 0)
			vc.Position = UDim2.new(1, -8, 0, thumbH + (if c then 5 else 6)); vc.Size = UDim2.fromOffset(54, 14)
			if not won then T.key(b, tostring(keyAt + i - 1), UDim2.new(1, -30, 0, 8)) end
			b.MouseButton1Click:Connect(function() voteMap(i) end)
			table.insert(cards, b)
		end
		y = top + mapH + pad
	else
		y += pad - (if c then 8 else 10)
	end

	panel.Size = UDim2.fromOffset(W, y)
	panel.Position = UDim2.new(0.5, 0, 1, if c then -126 else -190)
	clock.AnchorPoint = Vector2.new(1, 0); clock.Position = UDim2.new(1, -pad, 0, if c then 8 else 12); clock.Size = UDim2.fromOffset(60, 18)
	clock.TextSize = if c then 12 else 14
	gui.Enabled = true
end

function QuickVoteUI.sync(found: any)
	partyCur = if type(found) == "table" and (type(found.vote) == "table" or type(found.mvote) == "table")
		then { vote = found.vote, pick = found.pick, mvote = found.mvote, map = found.map } else nil
	cur = partyCur or padCur
	QuickVoteUI.draw()
end
function QuickVoteUI.syncPad(msg: any)
	padCur = if type(msg) == "table" and type(msg.vote) == "table" then { mvote = msg.vote, map = msg.map, pad = true } else nil
	cur = partyCur or padCur
	QuickVoteUI.draw()
end
function QuickVoteUI.fakeScreen(v: Vector2?)
	fake = v
	QuickVoteUI.draw()
end

local KEYS = { [Enum.KeyCode.One] = 1, [Enum.KeyCode.Two] = 2, [Enum.KeyCode.Three] = 3, [Enum.KeyCode.Four] = 4,
	[Enum.KeyCode.Five] = 5, [Enum.KeyCode.Six] = 6 }
Keys.began(function(io: any, gp: boolean)
	if gp or not cur then return end
	local i = KEYS[io.KeyCode]
	if not i then return end
	local hasModes = cur.vote ~= nil
	if hasModes and i <= 3 then vote(i)
	elseif hasModes then voteMap(i - 3)
	elseif i <= 3 then voteMap(i) end
end)

RunService.Heartbeat:Connect(function()
	if not cur then return end
	local open = (cur.vote and not cur.pick) or (cur.mvote and not cur.map)
	if not open then clock.Text = ""; return end
	local v = cur.vote or cur.mvote
	local left = (v.ends or 0) - workspace:GetServerTimeNow()
	clock.Text = if left > 0 then tostring(math.ceil(left)) else ""
end)

return QuickVoteUI
