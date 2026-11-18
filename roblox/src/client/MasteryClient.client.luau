-- WEAPON MASTERY on your screen (Shared.Mastery; docs/MASTERY.md), from the server's JankfireRemotes.MasteryPush:
--   a weapon levels up: a quiet plate at the top in the middle for 3 s, "LEVEL 12" over the weapon's name
--   a camo unlocks: the same plate with the camo's swatch, "GOLD UNLOCKED · ASSAULT RIFLE", and the reward sting
--     (one after another when several come at once)
--   a match ends: a card beside the end screen with each weapon you used, the XP it got, its level and its bar, for as
--     long as the end screen is up (or 10 s). left of it: the ranked card has the right (PlayUI)
-- functional words only (the owner's no-flavour-text rule). nothing here takes input: keyboard, pad and touch play on
-- (Studio tests: ServerStorage.JankMasteryTest "toast" sends these without changing anything)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local me = Players.LocalPlayer
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local M = require(Shared:WaitForChild("Mastery")) :: any
local Roster = require(Shared:WaitForChild("Roster")) :: any
local T = require(script.Parent:WaitForChild("Theme")) :: any
local MUI = require(script.Parent:WaitForChild("MasteryUI")) :: any
local okS, Sfx = pcall(function() return require(script.Parent:WaitForChild("Sfx", 10) :: ModuleScript) :: any end)
local function sting(name: string) if okS and type(Sfx) == "table" and Sfx.play then pcall(Sfx.play, name) end end

local pg = me:WaitForChild("PlayerGui")
local gui = T.new("ScreenGui", { Name = "JankMastery", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 8,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, pg)
local sc = T.scaled(gui)

local function wname(wid: string): string
	local e = Roster.byId[wid]
	return string.upper(if e then e.name else wid)
end

-- ------------------------------------------------------------------ the toasts
-- (under the account's level plate, JankLevel's at 104: both can come from one kill)
local toast = T.plate(sc, "MasteryToast", UDim2.new(0.5, 0, 0, 166), UDim2.fromOffset(300, 46))
toast.AnchorPoint = Vector2.new(0.5, 0)
toast.Visible = false
local tChip = T.new("Frame", { Name = "Camo", BorderSizePixel = 0, Position = UDim2.fromOffset(12, 10), Size = UDim2.fromOffset(40, 26), Visible = false }, toast)
T.corner(tChip, 3)
T.edge(tChip, nil, 0.7)
local tTitle = T.text(toast, "Title", "", 15, T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Center)
tTitle.Position = UDim2.fromOffset(12, 6); tTitle.Size = UDim2.new(1, -24, 0, 18)
local tSub = T.text(toast, "Sub", "", 11, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center)
tSub.Position = UDim2.fromOffset(12, 25); tSub.Size = UDim2.new(1, -24, 0, 14)

type Toast = { kind: string, w: string, lv: number?, c: string? }
local queue: { Toast } = {}
local running = false
local function show(t: Toast)
	if t.kind == "camo" and t.c then
		local camo = M.byId[t.c]
		tChip.Visible = true
		MUI.paint(tChip, t.c)
		tTitle.Text = ("%s UNLOCKED  ·  %s"):format(if camo then camo.name else string.upper(t.c), wname(t.w))
		tTitle.TextColor3 = T.ACCENT
		tTitle.Position = UDim2.fromOffset(62, 6); tTitle.Size = UDim2.new(1, -74, 0, 18)
		tSub.Position = UDim2.fromOffset(62, 25); tSub.Size = UDim2.new(1, -74, 0, 14)
		tSub.Text = "WRAPS  ·  LOADOUT"
		tTitle.TextXAlignment = Enum.TextXAlignment.Left; tSub.TextXAlignment = Enum.TextXAlignment.Left
		toast.Size = UDim2.fromOffset(math.clamp(#tTitle.Text * 9 + 90, 280, 520), 46)
		sting("loot_win_rare")
	else
		tChip.Visible = false
		tTitle.Text = "LEVEL " .. tostring(t.lv or "")
		tTitle.TextColor3 = T.TEXT
		tTitle.Position = UDim2.fromOffset(12, 6); tTitle.Size = UDim2.new(1, -24, 0, 18)
		tSub.Position = UDim2.fromOffset(12, 25); tSub.Size = UDim2.new(1, -24, 0, 14)
		tSub.Text = wname(t.w)
		tTitle.TextXAlignment = Enum.TextXAlignment.Center; tSub.TextXAlignment = Enum.TextXAlignment.Center
		toast.Size = UDim2.fromOffset(math.clamp(#tSub.Text * 8 + 60, 200, 420), 46)
		sting("ting")
	end
	toast.Visible = true
end
local function pump()
	if running then return end
	running = true
	task.spawn(function()
		while #queue > 0 do
			local t = table.remove(queue, 1) :: Toast
			show(t)
			task.wait(if t.kind == "camo" then 4 else 3)
		end
		toast.Visible = false
		running = false
	end)
end
local function enqueue(t: Toast)
	-- (several levels of one weapon at once, a test or a long match: only the highest)
	for i = #queue, 1, -1 do
		local q = queue[i]
		if t.kind == "level" and q.kind == "level" and q.w == t.w then table.remove(queue, i) end
	end
	table.insert(queue, t)
	pump()
end

-- ------------------------------------------------------------------ the match's card
local card = T.plate(sc, "MasteryMatch", UDim2.new(0.5, -262, 0.5, 0), UDim2.fromOffset(300, 100))
card.AnchorPoint = Vector2.new(1, 0.5)
card.Visible = false
card.ZIndex = 6
local cHead = T.text(card, "Head", "WEAPON XP", 12, T.MUTED, T.FONT_BOLD)
cHead.Position = UDim2.fromOffset(16, 12); cHead.Size = UDim2.new(1, -32, 0, 14); cHead.ZIndex = 7
local cList = T.new("Frame", { Name = "List", BackgroundTransparency = 1, Position = UDim2.fromOffset(16, 34), Size = UDim2.new(1, -32, 1, -44), ZIndex = 7 }, card)
T.new("UIListLayout", { Padding = UDim.new(0, 8), SortOrder = Enum.SortOrder.LayoutOrder }, cList)
local ROWS = 4
local cardTok = 0
-- the end screen's panel (FightHud's "End"), found once
local endPanel: GuiObject? = nil
local function findEnd(): GuiObject?
	if endPanel and endPanel.Parent then return endPanel end
	local f = pg:FindFirstChild("JankfireFight")
	if f then
		for _, d in f:GetDescendants() do
			if d.Name == "End" and d:IsA("Frame") and d:FindFirstChild("Board") then endPanel = d; return d end
		end
	end
	return nil
end
local function place()
	-- (a narrow screen has no room beside the end screen: the card goes along the bottom)
	local vp = (workspace.CurrentCamera :: Camera).ViewportSize
	local narrow = vp.X < 1100 or me:GetAttribute("TouchOn") == true
	if narrow then
		card.AnchorPoint = Vector2.new(0.5, 1); card.Position = UDim2.new(0.5, 0, 1, -12)
	else
		card.AnchorPoint = Vector2.new(1, 0.5); card.Position = UDim2.new(0.5, -262, 0.5, 0)
	end
end
local function showMatch(gains: { [string]: number }, now: { [string]: number })
	cardTok += 1
	local my = cardTok
	for _, d in cList:GetChildren() do if d:IsA("Frame") then d:Destroy() end end
	local list = {}
	for w, g in gains do if type(w) == "string" and (tonumber(g) or 0) > 0 then table.insert(list, { w = w, g = tonumber(g) :: number }) end end
	table.sort(list, function(a, b) if a.g ~= b.g then return a.g > b.g end return a.w < b.w end)
	if #list == 0 then return end
	local n = math.min(#list, ROWS)
	for i = 1, n do
		local x = list[i]
		local row = T.new("Frame", { Name = "Row", BackgroundTransparency = 1, LayoutOrder = i, Size = UDim2.new(1, 0, 0, 34), ZIndex = 7 }, cList)
		local nm = T.text(row, "Name", wname(x.w), 13, T.TEXT, T.FONT_BOLD)
		nm.Position = UDim2.fromOffset(0, 0); nm.Size = UDim2.new(1, -120, 0, 16); nm.ZIndex = 8; nm.TextTruncate = Enum.TextTruncate.AtEnd
		local gain = T.text(row, "Gain", "+" .. MUI.num(x.g), 13, T.ACCENT, T.FONT_HEAVY, Enum.TextXAlignment.Right)
		gain.Position = UDim2.new(1, -116, 0, 0); gain.Size = UDim2.fromOffset(60, 16); gain.ZIndex = 8
		local total = tonumber(now[x.w]) or 0
		local level, _, _, frac = M.progress(total)
		local lv = T.text(row, "Level", "LV " .. level, 13, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Right)
		lv.Position = UDim2.new(1, -50, 0, 0); lv.Size = UDim2.fromOffset(50, 16); lv.ZIndex = 8
		local track = T.new("Frame", { Name = "Track", BackgroundColor3 = T.TRACK, BorderSizePixel = 0, Position = UDim2.fromOffset(0, 24), Size = UDim2.new(1, 0, 0, 4), ZIndex = 8 }, row)
		T.corner(track, 2)
		-- (the bar fills from where the match started to where it is now)
		local _, _, _, before = M.progress(math.max(0, total - x.g))
		if M.levelOf(math.max(0, total - x.g)) < level then before = 0 end
		local fill = T.new("Frame", { Name = "Fill", BackgroundColor3 = if level >= M.MAX then T.ACCENT else T.TEXT, BorderSizePixel = 0,
			Size = UDim2.fromScale(before, 1), ZIndex = 9 }, track)
		T.corner(fill, 2)
		task.delay(0.35, function() T.tween(fill, 0.7, { Size = UDim2.fromScale(frac, 1) }) end)
	end
	card.Size = UDim2.fromOffset(300, 44 + n * 42)
	place()
	card.Visible = true
	-- up while the end screen is (at least 4 s, at most 12); 10 s if there's no end screen to follow
	task.spawn(function()
		local t0 = os.clock()
		task.wait(1)
		while my == cardTok do
			local e = findEnd()
			local dt = os.clock() - t0
			if dt > 12 or (e and not e.Visible and dt > 4) or (not e and dt > 10) then break end
			task.wait(0.25)
		end
		if my == cardTok then card.Visible = false end
	end)
end

-- ------------------------------------------------------------------ the server's word
local push = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("MasteryPush", 60) :: RemoteEvent?
if push then
	push.OnClientEvent:Connect(function(msg: any)
		if type(msg) ~= "table" then return end
		if msg.k == "level" and type(msg.w) == "string" then
			enqueue({ kind = "level", w = msg.w, lv = tonumber(msg.lv) })
		elseif msg.k == "camo" and type(msg.w) == "string" and type(msg.c) == "string" then
			enqueue({ kind = "camo", w = msg.w, c = msg.c })
		elseif msg.k == "match" and type(msg.gains) == "table" then
			showMatch(msg.gains, if type(msg.xp) == "table" then msg.xp else {})
		end
	end)
end
