--!strict
-- QUICKPLAY's vote (server/Party.luau; PlayConfig QUICKPLAY): when a quickplay match forms, its players see 3 modes its
-- head-count fits and tap one (or press 1, 2 or 3) for PlayConfig.VOTE s. most votes wins, a tie is drawn, no votes =
-- a weighted draw; the pick shows until the match starts. it sits over the Play screen's big button. everything comes
-- from the party view (found.vote, found.pick), so a reopened screen or a respawn shows it again:
--   QuickVoteUI.sync(found)   PlayClient, on every party view
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local T = require(script.Parent:WaitForChild("Theme"))
local PlayUI = require(script.Parent:WaitForChild("PlayUI"))
local Keys = require(script.Parent:WaitForChild("Keys"))

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")
local new, text = T.new, T.text

local QuickVoteUI = {}
local cur: any = nil -- the found view on screen: { vote = { options, ends, counts, mine }, pick }
local optIds: { string } = {}

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
local cards: { TextButton } = {}

local function vote(i: number)
	local id = optIds[i]
	if not id or not cur or cur.pick then return end
	if cur.vote then cur.vote.mine = id end
	QuickVoteUI.draw()
	task.spawn(function()
		local r = PlayUI.ask("vote", id)
		if type(r) == "table" and not r.ok and type(r.why) == "string" then PlayUI.notice(r.why) end
	end)
end

-- lay the panel out for the screen (a small screen: smaller cards) and fill it from cur
function QuickVoteUI.draw()
	for _, c in cards do c:Destroy() end
	table.clear(cards)
	if not cur or not cur.vote then gui.Enabled = false; return end
	local cam = workspace.CurrentCamera
	local sz = if cam then cam.ViewportSize / T.scaleNow() else Vector2.new(1280, 720)
	local c = sz.Y < 560 or sz.X < 960
	local cw, ch, gap, pad = if c then 150 else 180, if c then 66 else 86, if c then 8 else 10, if c then 12 else 16
	local opts = cur.vote.options or {}
	local n = math.max(1, #opts)
	local W = n * cw + (n - 1) * gap + pad * 2
	panel.Size = UDim2.fromOffset(W, (if c then 34 else 42) + ch + pad)
	panel.Position = UDim2.new(0.5, 0, 1, if c then -126 else -190)
	head.Position = UDim2.fromOffset(pad, if c then 8 else 12); head.Size = UDim2.fromOffset(W - pad * 2 - 60, 18)
	head.TextSize = if c then 12 else 14
	clock.AnchorPoint = Vector2.new(1, 0); clock.Position = UDim2.new(1, -pad, 0, if c then 8 else 12); clock.Size = UDim2.fromOffset(60, 18)
	clock.TextSize = if c then 12 else 14
	local pick = cur.pick
	head.Text = if pick then "PICKED" else "VOTE FOR THE MODE"
	table.clear(optIds)
	local counts = cur.vote.counts or {}
	for i, o in opts do
		optIds[i] = o.id
		local mine = cur.vote.mine == o.id
		local won = pick == o.id
		local b = new("TextButton", { Name = "Option" .. i, AutoButtonColor = false, BorderSizePixel = 0, Text = "",
			BackgroundColor3 = if won then T.ACCENT elseif mine then T.CARD_HI else T.CARD,
			BackgroundTransparency = if pick and not won then 0.55 else 0.05,
			Position = UDim2.fromOffset(pad + (i - 1) * (cw + gap), if c then 30 else 38), Size = UDim2.fromOffset(cw, ch) }, panel)
		T.corner(b, 5)
		if mine and not won then T.edge(b, T.ACCENT, 0.3, 1) end
		local ink = if won then T.INK elseif pick then T.DIM else T.TEXT
		local nm = text(b, "Name", o.name or o.id, if c then 13 else 16, ink, T.FONT_TITLE)
		nm.Position = UDim2.fromOffset(10, if c then 6 else 9); nm.Size = UDim2.new(1, -40, 0, 20); nm.TextTruncate = Enum.TextTruncate.AtEnd
		local sb = text(b, "Sub", o.sub or "", if c then 9 else 10, if won then T.INK else T.MUTED, T.FONT)
		sb.Position = UDim2.fromOffset(10, if c then 24 else 30); sb.Size = UDim2.new(1, -20, 0, if c then 24 else 30)
		sb.TextWrapped = true; sb.TextYAlignment = Enum.TextYAlignment.Top; sb.TextTruncate = Enum.TextTruncate.AtEnd
		local k = counts[o.id] or 0
		local vc = text(b, "Votes", if k == 1 then "1 VOTE" elseif k > 1 then ("%d VOTES"):format(k) else "", if c then 9 else 11, if won then T.INK else T.ACCENT, T.FONT_HEAVY)
		vc.Position = UDim2.new(0, 10, 1, if c then -15 else -19); vc.Size = UDim2.new(1, -20, 0, 14)
		if not pick then T.key(b, tostring(i), UDim2.new(1, -30, 0, 8)) end
		b.MouseButton1Click:Connect(function() vote(i) end)
		table.insert(cards, b)
	end
	gui.Enabled = true
end

function QuickVoteUI.sync(found: any)
	if type(found) ~= "table" or type(found.vote) ~= "table" then
		cur = nil
		gui.Enabled = false
		for _, c in cards do c:Destroy() end
		table.clear(cards)
		return
	end
	cur = { vote = found.vote, pick = found.pick }
	QuickVoteUI.draw()
end

Keys.began(function(io: any, gp: boolean)
	if gp or not cur or cur.pick then return end
	local i = if io.KeyCode == Enum.KeyCode.One then 1 elseif io.KeyCode == Enum.KeyCode.Two then 2 elseif io.KeyCode == Enum.KeyCode.Three then 3 else nil
	if i then vote(i) end
end)

RunService.Heartbeat:Connect(function()
	if not cur or not cur.vote then return end
	if cur.pick then clock.Text = ""; return end
	local left = (cur.vote.ends or 0) - workspace:GetServerTimeNow()
	clock.Text = if left > 0 then tostring(math.ceil(left)) else ""
end)

return QuickVoteUI
