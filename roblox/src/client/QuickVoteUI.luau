--!strict
-- the votes when a match forms (server/Party.luau), over the Play screen's big button:
--   the MODE (QUICKPLAY): 3 modes its head-count fits, tap one (or press 1, 2 or 3)
--   the MAP (QUICKPLAY and casual duels, 17 Nov 2026, the owner: "also add map selector before hand"): 3 maps from the
--   rotation as cards with their pictures (shared/MapCards.luau) and names, and RANDOM (21 Nov 2026, the owner: "for
--   pads and casual andthing but ranked basically let us pick maps": any map of the rotation; no votes is RANDOM too),
--   tap one (4-7 under a mode vote; 1-4 alone). RANDOM's card shows the map it landed on once it's picked
-- both run on the same PlayConfig.VOTE s clock. most votes wins, a tie is drawn; the picks show until the match starts.
-- everything comes from the party view (found.vote / pick, found.mvote / map), so a reopened screen or a respawn
-- shows it again:
--   QuickVoteUI.sync(found)   PlayClient, on every party view
-- and a hub PAD's map vote (18 Nov, the owner: "map select for pads please"): while you stand on a full pad, its
-- countdown is a map vote (server/Matches.luau, Matches.PAD_VOTE s), the same three cards, keys 1-3 or a tap:
--   QuickVoteUI.syncPad(msg)  PlayClient, on PlayPush { t = "padvote", vote?, map? } (no vote: it's gone)
-- a party match's vote, if there is one, has the panel first.
-- a RANKED match's draft (19 Nov 2026, server/RankedDraft.luau, Matches.draftRoom) comes the same way, with kind: "wban"
-- (BAN A WEAPON: a grid of the primaries, your side's votes on them, tap one) then "mban" (BAN A MAP: the three cards,
-- keys 1-3; at the end the banned ones are marked and the map left is lit), the weapon bans on the map line
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local T = require(script.Parent:WaitForChild("Theme"))
local PlayUI = require(script.Parent:WaitForChild("PlayUI"))
local Keys = require(script.Parent:WaitForChild("Keys"))
local MenuCursor = require(script.Parent:WaitForChild("MenuCursor")) :: any
local Pad = require(script.Parent:WaitForChild("Pad")) :: any

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
	if cur.kind == "wban" then
		-- the draft's weapon ban: every primary as a small tile, your side's votes on each, yours lit
		local opts = cur.mvote.options or {}
		local cols = if c then 4 else 5
		local tw, th, g, pad = if c then 100 else 116, if c then 28 else 32, 6, if c then 12 else 16
		local headH = if c then 30 else 38
		local rows = math.max(1, math.ceil(#opts / cols))
		local W = cols * tw + (cols - 1) * g + pad * 2
		head.Visible = true
		head.Text = "BAN A WEAPON"
		head.TextSize = if c then 12 else 14
		head.Position = UDim2.fromOffset(pad, if c then 8 else 12); head.Size = UDim2.fromOffset(W - pad * 2 - 60, 18)
		mapHead.Visible = false
		table.clear(modeIds)
		table.clear(mapIds)
		local counts = cur.mvote.counts or {}
		for i, o in opts do
			mapIds[i] = o.id
			local mine = cur.mvote.mine == o.id
			local col, row = (i - 1) % cols, (i - 1) // cols
			local b = new("TextButton", { Name = "Weapon" .. i, AutoButtonColor = false, BorderSizePixel = 0, Text = "",
				BackgroundColor3 = if mine then T.CARD_HI else T.CARD, BackgroundTransparency = 0.05,
				Position = UDim2.fromOffset(pad + col * (tw + g), headH + row * (th + g)), Size = UDim2.fromOffset(tw, th) }, panel)
			T.corner(b, 4)
			if mine then T.edge(b, T.ACCENT, 0.2, 1) end
			local nm = text(b, "Name", string.upper(o.title or o.id), if c then 10 else 11, if mine then T.ACCENT else T.TEXT, T.FONT_HEAVY)
			nm.Position = UDim2.fromOffset(8, 0); nm.Size = UDim2.new(1, -28, 1, 0); nm.TextScaled = true
			new("UITextSizeConstraint", { MaxTextSize = if c then 10 else 11, MinTextSize = 7 }, nm)
			local k = counts[o.id] or 0
			if k > 0 then
				local vc = text(b, "Votes", tostring(k), if c then 10 else 11, T.ACCENT, T.FONT_HEAVY, Enum.TextXAlignment.Right)
				vc.Position = UDim2.new(1, -24, 0, 0); vc.Size = UDim2.new(0, 18, 1, 0)
			end
			b.MouseButton1Click:Connect(function() voteMap(i) end)
			table.insert(cards, b)
		end
		local H = headH + rows * (th + g) - g + pad
		panel.Size = UDim2.fromOffset(W, H)
		panel.Position = UDim2.new(0.5, 0, 1, if c then -126 else -190)
		clock.AnchorPoint = Vector2.new(1, 0); clock.Position = UDim2.new(1, -pad, 0, if c then 8 else 12); clock.Size = UDim2.fromOffset(60, 18)
		clock.TextSize = if c then 12 else 14
		gui.Enabled = true
		return
	end
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
		local mbanned = if cur.kind == "mban" then (cur.mbanned or {}) else {}
		if cur.kind == "mban" then
			-- (the draft: a ban, not a vote for; the weapon bans on the same line)
			local wb = cur.banned or {}
			mapHead.Text = (if won then "MAP" else "BAN A MAP") .. (if #wb > 0 then "   ·   BANNED: " .. string.upper(table.concat(wb, ", ")) else "")
		end
		local counts = cur.mvote.counts or {}
		local top = my + headH - (if c then 8 else 12)
		-- (RANDOM won: the picked map isn't one of the cards, so RANDOM's card shows it)
		local wonOnCard = false
		for _, o in maps do if o.id == won then wonOnCard = true end end
		for i, o in maps do
			mapIds[i] = o.id
			local mine = cur.mvote.mine == o.id
			local isWon = won == o.id or (o.random == true and won ~= nil and not wonOnCard)
			local shown = if o.random == true and isWon then cur.map else o
			local b = new("TextButton", { Name = "Map" .. i, AutoButtonColor = false, BorderSizePixel = 0, Text = "", ClipsDescendants = true,
				BackgroundColor3 = if isWon then T.ACCENT elseif mine then T.CARD_HI else T.CARD,
				BackgroundTransparency = if won and not isWon then 0.55 else 0.05,
				Position = UDim2.fromOffset(pad + (i - 1) * (cw + gap), top), Size = UDim2.fromOffset(cw, mapH) }, panel)
			T.corner(b, 5)
			if (mine and not isWon) or isWon then T.edge(b, T.ACCENT, if isWon then 0 else 0.3, if isWon then 2 else 1) end
			local pic = new("ImageLabel", { Name = "Thumb", BorderSizePixel = 0, BackgroundColor3 = T.BG, Image = shown.thumb or "",
				ScaleType = Enum.ScaleType.Crop, ImageTransparency = if won and not isWon then 0.6 else 0,
				Position = UDim2.fromOffset(0, 0), Size = UDim2.new(1, 0, 0, thumbH) }, b)
			T.corner(pic, 5)
			if o.random == true and not isWon then
				local any = text(pic, "Any", "ANY MAP", if c then 10 else 12, if won then T.DIM else T.MUTED, T.FONT_HEAVY, Enum.TextXAlignment.Center)
				any.Size = UDim2.fromScale(1, 1)
			end
			local ink = if isWon then T.INK elseif won then T.DIM else T.TEXT
			local nm = text(b, "Name", shown.title or shown.id, if c then 11 else 13, ink, T.FONT_HEAVY)
			nm.Position = UDim2.fromOffset(8, thumbH + (if c then 4 else 5)); nm.Size = UDim2.new(1, -64, 0, if c then 14 else 16); nm.TextScaled = true
			new("UITextSizeConstraint", { MaxTextSize = if c then 11 else 13, MinTextSize = 7 }, nm)
			local isBanned = table.find(mbanned, o.id) ~= nil
			local vc = text(b, "Votes", if isBanned then "BANNED" elseif o.random == true and isWon then "RANDOM" else votesText(counts[o.id] or 0), if c then 9 else 10, if isWon then T.INK elseif isBanned then T.DANGER else T.ACCENT, T.FONT_HEAVY, Enum.TextXAlignment.Right)
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

-- (21 Nov 2026, a controller on the Play screen: PadNav keeps the selection inside the top screen, the Play panel, so the
-- vote over it was out of reach. while a Play-queue vote is open it is a screen of its own for PadNav (a "cursor only"
-- MenuCursor name: you still move), so the stick and A reach its cards. a map room's vote has no menu over it: View
-- reaches its cards as before, and the stick still walks you to the plates)
Pad.MENUS.vote = { gui = "JankVote", back = function() end }
local menuOn = false
local function voteOpen(): boolean
	return cur ~= nil and ((cur.vote ~= nil and not cur.pick) or (cur.mvote ~= nil and not cur.map))
end
local function menuSync()
	local want = gui.Enabled and voteOpen() and cur.pad ~= true
	if want == menuOn then return end
	menuOn = want
	MenuCursor.set("vote", want, if want then function() return menuOn end else nil, true)
end

function QuickVoteUI.sync(found: any)
	partyCur = if type(found) == "table" and (type(found.vote) == "table" or type(found.mvote) == "table")
		then { vote = found.vote, pick = found.pick, mvote = found.mvote, map = found.map } else nil
	cur = partyCur or padCur
	QuickVoteUI.draw()
	menuSync()
end
function QuickVoteUI.syncPad(msg: any)
	padCur = if type(msg) == "table" and type(msg.vote) == "table" then { mvote = msg.vote, map = msg.map, pad = true,
		kind = msg.kind, banned = msg.banned, mbanned = msg.mbanned } else nil
	cur = partyCur or padCur
	QuickVoteUI.draw()
	menuSync()
end
function QuickVoteUI.fakeScreen(v: Vector2?)
	fake = v
	QuickVoteUI.draw()
end

local KEYS = { [Enum.KeyCode.One] = 1, [Enum.KeyCode.Two] = 2, [Enum.KeyCode.Three] = 3, [Enum.KeyCode.Four] = 4,
	[Enum.KeyCode.Five] = 5, [Enum.KeyCode.Six] = 6, [Enum.KeyCode.Seven] = 7 }
Keys.began(function(io: any, gp: boolean)
	if gp or not cur or cur.kind == "wban" then return end -- (the weapon ban: tiles only, too many for keys)
	local i = KEYS[io.KeyCode]
	if not i then return end
	local hasModes = cur.vote ~= nil
	if hasModes and i <= 3 then vote(i)
	elseif hasModes then voteMap(i - 3)
	else voteMap(i) end -- (voteMap ignores a key past the cards)
end)

RunService.Heartbeat:Connect(function()
	-- (nothing to show: off, every frame. a menu that hid this panel and puts it back when it closes, the loadout screen in
	-- a map room on 18 Nov, must never bring back an empty one)
	if menuOn and not (gui.Enabled and voteOpen()) then menuSync() end
	if not cur then if gui.Enabled then gui.Enabled = false end; return end
	local open = (cur.vote and not cur.pick) or (cur.mvote and not cur.map)
	if not open then clock.Text = ""; return end
	local v = cur.vote or cur.mvote
	local left = (v.ends or 0) - workspace:GetServerTimeNow()
	clock.Text = if left > 0 then tostring(math.ceil(left)) else ""
end)

return QuickVoteUI
