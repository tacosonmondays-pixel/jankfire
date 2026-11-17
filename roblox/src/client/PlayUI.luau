--!strict
-- PLAY UI: the private lobby's screen (roblox/docs/MATCHMAKING.md): the modes on the left (CASUAL | RANKED), the party
-- on the right (members, INVITE, the leader's LEAD / KICK), the lineup in the middle (the room's camera on the party's
-- bodies, each with a nameplate), the big button at the bottom (FIND MATCH, the search clock, MATCH FOUND). also the
-- invite toast (anywhere but a match), small notices, and the ranked result card after a ranked match (on the end
-- screen, then in the lobby). everything is built from Theme (dark plates, one amber accent) and RankedStyle; no text
-- or pictures are uploaded. PlayClient.client.luau opens it and feeds it the server's pushes.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local T = require(script.Parent:WaitForChild("Theme"))
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local PlayConfig = require(Shared:WaitForChild("PlayConfig"))
local Ranked = require(Shared:WaitForChild("Ranked"))
local RankedStyle = require(Shared:WaitForChild("RankedStyle"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local Remote = Remotes:WaitForChild("Play") :: RemoteFunction

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")

local UI = {}
local S: any = {
	open = false, party = nil, ranked = {}, best = nil, tab = "casual", invites = {}, inviting = false, players = {},
	found = nil, fake = nil, busy = false,
}
UI.S = S

local GOOD = Color3.fromRGB(110, 214, 140) -- a rating gained (the only green: it carries information)
local new, text = T.new, T.text

-- ask the server; a refusal shows as a notice. returns the reply table
local notice: (string) -> ()
local function ask(op: string, a: any?, b: any?): any
	local ok, res = pcall(function() return Remote:InvokeServer(op, a, b) end)
	if not ok or type(res) ~= "table" then notice("no answer from the server"); return { ok = false } end
	if res.ok == false and type(res.why) == "string" and res.why ~= "" then notice(res.why) end
	return res
end
UI.ask = ask

local function mmss(s: number): string
	s = math.max(0, math.floor(s))
	return ("%d:%02d"):format(s // 60, s % 60)
end
local function modeName(id: string?): string
	local m = id and PlayConfig.byId[id]
	return if m then m.name else "?"
end
local function myParty(): any return S.party end
local function iLead(): boolean
	local pt = S.party
	return pt ~= nil and pt.leader == me.UserId
end
local function leaderName(): string
	local pt = S.party
	if not pt then return "" end
	for _, m in pt.members do if m.id == pt.leader then return m.display end end
	return ""
end

-- ------------------------------------------------------------------ the screen
local gui = new("ScreenGui", { Name = "JankPlay", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 20,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling, Enabled = true }, pg)
local scaled = T.scaled(gui)
-- (a fake screen size for phone layout tests: the screen is laid out in a box that size, centred)
local stage = new("Frame", { Name = "Stage", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, scaled)

local lobby = new("Frame", { Name = "Lobby", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Visible = false }, stage)
-- soft dark edges so the panels read over the room, the middle left clear for the lineup
local shadeL = new("Frame", { Name = "ShadeL", BorderSizePixel = 0, BackgroundColor3 = T.BG, Size = UDim2.new(0.42, 0, 1, 0) }, lobby)
new("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.18), NumberSequenceKeypoint.new(0.75, 0.75), NumberSequenceKeypoint.new(1, 1) }) }, shadeL)
local shadeR = new("Frame", { Name = "ShadeR", BorderSizePixel = 0, BackgroundColor3 = T.BG, AnchorPoint = Vector2.new(1, 0), Position = UDim2.fromScale(1, 0), Size = UDim2.new(0.38, 0, 1, 0) }, lobby)
new("UIGradient", { Rotation = 180, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(0.75, 0.78), NumberSequenceKeypoint.new(1, 1) }) }, shadeR)
local shadeB = new("Frame", { Name = "ShadeB", BorderSizePixel = 0, BackgroundColor3 = T.BG, AnchorPoint = Vector2.new(0, 1), Position = UDim2.fromScale(0, 1), Size = UDim2.new(1, 0, 0.3, 0) }, lobby)
new("UIGradient", { Rotation = 270, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3), NumberSequenceKeypoint.new(1, 1) }) }, shadeB)

-- the title, top left
local title = new("Frame", { Name = "Title", BackgroundTransparency = 1, Position = UDim2.fromOffset(32, 22), Size = UDim2.fromOffset(400, 60) }, lobby)
local kicker = text(title, "Kicker", "PRIVATE LOBBY", 12, T.MUTED, T.FONT_BOLD)
kicker.Size = UDim2.fromOffset(400, 16)
local big = text(title, "Big", "PLAY", 30, T.TEXT, T.FONT_TITLE)
big.Position = UDim2.fromOffset(0, 16); big.Size = UDim2.fromOffset(400, 38)

-- LEAVE, top right
local leaveB = new("TextButton", { Name = "Leave", AutoButtonColor = false, BackgroundColor3 = T.BG, BackgroundTransparency = T.BG_A, BorderSizePixel = 0,
	AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -32, 0, 28), Size = UDim2.fromOffset(150, 36), FontFace = T.FONT_BOLD, TextSize = 13,
	Text = "LEAVE LOBBY", TextColor3 = T.TEXT }, lobby)
T.corner(leaveB); T.edge(leaveB)

-- the panels (placed by fit())
local left = T.plate(lobby, "Modes", UDim2.fromOffset(32, 96), UDim2.fromOffset(300, 460))
local right = T.plate(lobby, "Party", UDim2.fromOffset(0, 96), UDim2.fromOffset(280, 360))
right.AnchorPoint = Vector2.new(1, 0)
local bottom = new("Frame", { Name = "Bottom", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, -28),
	Size = UDim2.fromOffset(480, 150) }, lobby)

-- notices: a small plate under the top edge, gone after a moment
local noteBox = T.plate(stage, "Notice", UDim2.new(0.5, 0, 0, 108), UDim2.fromOffset(360, 34))
noteBox.AnchorPoint = Vector2.new(0.5, 0); noteBox.Visible = false; noteBox.ZIndex = 30
local noteText = text(noteBox, "Text", "", 13, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Center)
noteText.Size = UDim2.fromScale(1, 1); noteText.ZIndex = 31
local noteTok = 0
notice = function(s: string)
	noteTok += 1
	local my = noteTok
	noteText.Text = string.upper(s)
	noteBox.Size = UDim2.fromOffset(math.clamp(noteText.TextBounds.X + 40, 200, 560), 34)
	noteBox.Visible = true
	task.delay(2.6, function() if my == noteTok then noteBox.Visible = false end end)
end
UI.notice = notice

-- layout: the panels' sizes for this screen (a phone gets a compact one)
local L: any = { compact = false, W = 1280, H = 720 }
local function screenSize(): Vector2
	if S.fake then return S.fake end
	local cam = workspace.CurrentCamera
	local s = T.scaleNow()
	return if cam then cam.ViewportSize / s else Vector2.new(1280, 720)
end

local function fit()
	local sz = screenSize()
	L.W, L.H = sz.X, sz.Y
	L.compact = sz.Y < 560 or sz.X < 960
	if S.fake then
		stage.AnchorPoint = Vector2.new(0.5, 0.5)
		stage.Position = UDim2.fromScale(0.5, 0.5)
		stage.Size = UDim2.fromOffset(sz.X, sz.Y)
		stage.ClipsDescendants = true
	else
		stage.AnchorPoint = Vector2.zero; stage.Position = UDim2.new(); stage.Size = UDim2.fromScale(1, 1); stage.ClipsDescendants = false
	end
	local c = L.compact
	local pad = if c then 14 else 32
	L.pad = pad
	L.cardH = if c then 44 else 62
	L.leftW = if c then 214 else 300
	L.rightW = if c then 206 else 280
	L.top = if c then 58 else 96
	title.Position = UDim2.fromOffset(pad, if c then 10 else 22)
	big.TextSize = if c then 22 else 30
	kicker.TextSize = if c then 10 else 12
	leaveB.Position = UDim2.new(1, -pad, 0, if c then 12 else 28)
	leaveB.Size = UDim2.fromOffset(if c then 112 else 150, if c then 30 else 36)
	leaveB.TextSize = if c then 11 else 13
	left.Position = UDim2.fromOffset(pad, L.top)
	right.Position = UDim2.new(1, -pad, 0, L.top)
	bottom.Position = UDim2.new(0.5, 0, 1, if c then -10 else -28)
	bottom.Size = UDim2.fromOffset(if c then 300 else 480, if c then 108 else 150)
end

-- the plate's own hairline in another colour (a frame shows only one UIStroke: never add a second)
local function stroke(f: Instance, color: Color3, alpha: number)
	local s = f:FindFirstChildOfClass("UIStroke")
	if not s then s = T.edge(f, color, alpha, 1) end
	(s :: UIStroke).Color = color; (s :: UIStroke).Transparency = alpha
end
local function clear(f: Instance, keep: { [string]: boolean }?)
	for _, c in f:GetChildren() do
		if c:IsA("GuiObject") and not (keep and keep[c.Name]) then c:Destroy() end
	end
end
local function button(parent: Instance, name: string, label: string, accent: boolean, size: UDim2, pos: UDim2): TextButton
	local b = new("TextButton", { Name = name, AutoButtonColor = false, BorderSizePixel = 0, Size = size, Position = pos,
		BackgroundColor3 = if accent then T.ACCENT else T.CARD_HI, BackgroundTransparency = 0, FontFace = T.FONT_HEAVY,
		TextSize = 13, Text = label, TextColor3 = if accent then T.INK else T.TEXT }, parent)
	T.corner(b, 5)
	if not accent then T.edge(b, nil, 0.8) end
	b.MouseEnter:Connect(function() b.BackgroundColor3 = if accent then T.ACCENT:Lerp(Color3.new(1, 1, 1), 0.18) else T.CARD_HI:Lerp(Color3.new(1, 1, 1), 0.08) end)
	b.MouseLeave:Connect(function() b.BackgroundColor3 = if accent then T.ACCENT else T.CARD_HI end)
	return b
end

-- ------------------------------------------------------------------ the modes (left)
local refresh: () -> ()
local function modeList()
	clear(left)
	local c = L.compact
	local pt = myParty()
	local n = if pt then #pt.members else 1
	local lead = iLead()
	local W = L.leftW
	-- CASUAL | RANKED
	local tabs = new("Frame", { Name = "Tabs", BackgroundTransparency = 1, Position = UDim2.fromOffset(12, 12), Size = UDim2.fromOffset(W - 24, if c then 28 else 34) }, left)
	for i, id in { "casual", "ranked" } do
		local on = S.tab == id
		local tb = new("TextButton", { Name = id, AutoButtonColor = false, BorderSizePixel = 0, BackgroundColor3 = if on then T.CARD_HI else T.CARD,
			BackgroundTransparency = if on then 0 else 0.3, Position = UDim2.new((i - 1) * 0.5, if i == 2 then 3 else 0, 0, 0), Size = UDim2.new(0.5, -3, 1, 0),
			FontFace = T.FONT_HEAVY, TextSize = if c then 11 else 13, Text = string.upper(id), TextColor3 = if on then T.TEXT else T.MUTED }, tabs)
		T.corner(tb, 5)
		if on then
			local bar = new("Frame", { BorderSizePixel = 0, BackgroundColor3 = T.ACCENT, AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, 0), Size = UDim2.new(0.5, 0, 0, 2) }, tb)
			T.corner(bar, 1)
		end
		tb.MouseButton1Click:Connect(function()
			if S.tab == id then return end
			S.tab = id
			-- the leader's pick follows the tab (a ranked tab can't keep 1v1v1)
			if lead and pt then
				local mode = pt.mode
				if id == "ranked" and not (PlayConfig.byId[mode] and PlayConfig.byId[mode].ranked) then mode = "2v2" end
				if PlayConfig.fits(PlayConfig.byId[mode], n, id == "ranked") then task.spawn(ask, "mode", mode, id == "ranked") end
			end
			refresh()
		end)
	end
	local y = (if c then 28 else 34) + 22
	local ranked = S.tab == "ranked"
	for _, m in PlayConfig.MODES do
		if ranked and not m.ranked then continue end
		local fits, why = PlayConfig.fits(m, n, ranked)
		local picked = pt ~= nil and pt.mode == m.id and pt.ranked == ranked
		local card = new("TextButton", { Name = m.id, AutoButtonColor = false, BorderSizePixel = 0, Text = "",
			BackgroundColor3 = if picked then T.CARD_HI else T.CARD, BackgroundTransparency = if picked then 0 else 0.2,
			Position = UDim2.fromOffset(12, y), Size = UDim2.fromOffset(W - 24, L.cardH) }, left)
		T.corner(card, 5)
		if picked then
			T.edge(card, T.ACCENT, 0.35, 1)
			local bar = new("Frame", { BorderSizePixel = 0, BackgroundColor3 = T.ACCENT, Position = UDim2.fromOffset(0, 8), Size = UDim2.new(0, 3, 1, -16) }, card)
			T.corner(bar, 2)
		end
		local nm = text(card, "Name", m.name, if c then 16 else 21, if fits then T.TEXT else T.DIM, T.FONT_TITLE)
		nm.Position = UDim2.fromOffset(14, if c then 5 else 9); nm.Size = UDim2.new(1, -90, 0, if c then 20 else 26)
		local sub = if not fits then (why or "") elseif m.teams == 3 then "three solo sides · first to 5 rounds" else ("%d a side · first to 5 rounds"):format(m.size)
		local sl = text(card, "Sub", sub, if c then 10 else 12, if fits then T.MUTED else T.DIM, T.FONT)
		sl.Position = UDim2.fromOffset(14, if c then 25 else 36); sl.Size = UDim2.new(1, if ranked then (if c then -64 else -120) else -24, 0, 16)
		sl.TextTruncate = Enum.TextTruncate.AtEnd
		if ranked then
			local v = S.ranked[m.id]
			local bs = if c then 32 else 44
			local badge = RankedStyle.badge(card, bs, v)
			badge.AnchorPoint = Vector2.new(1, 0.5); badge.Position = UDim2.new(1, -10, 0.5, -6)
			local lab = text(card, "Rank", RankedStyle.label(v), if c then 8 else 10, RankedStyle.color(v), T.FONT_BOLD, Enum.TextXAlignment.Center)
			lab.AnchorPoint = Vector2.new(1, 0); lab.Position = UDim2.new(1, -8, 1, if c then -13 else -16); lab.Size = UDim2.fromOffset(100, 12)
			lab.TextXAlignment = Enum.TextXAlignment.Right
			lab.TextScaled = false; lab.TextTruncate = Enum.TextTruncate.AtEnd
		end
		card.MouseButton1Click:Connect(function()
			if not lead then notice("only the leader (" .. leaderName() .. ") picks the mode"); return end
			if not fits then notice(why or "that mode doesn't fit your party"); return end
			task.spawn(function() ask("mode", m.id, ranked) end)
		end)
		y += L.cardH + 8
	end
	-- what the pick means, under the cards
	local foot = text(left, "Foot", "", if c then 10 else 12, T.MUTED, T.FONT)
	foot.Position = UDim2.fromOffset(14, y + 2); foot.Size = UDim2.fromOffset(W - 28, 34); foot.TextWrapped = true
	foot.TextYAlignment = Enum.TextYAlignment.Top
	if pt and not lead then
		foot.Text = "only the leader (" .. leaderName() .. ") picks the mode and starts the search"
	elseif ranked then
		foot.Text = ("%d placement matches, then your rank shows. parties within %d rating"):format(Ranked.PLACEMENTS, Ranked.PARTY_SPREAD)
	else
		foot.Text = "same arenas and rules as the pads. your party plays on one team"
	end
	left.Size = UDim2.fromOffset(W, y + 44)
end

-- ------------------------------------------------------------------ the party (right)
local thumbs: { [number]: string } = {}
local function headshot(parent: Instance, id: number, name: string, size: number)
	local holder = new("Frame", { Name = "Head", BorderSizePixel = 0, BackgroundColor3 = T.TRACK, Size = UDim2.fromOffset(size, size) }, parent)
	T.corner(holder, size // 2)
	local initial = text(holder, "Initial", string.upper(string.sub(name, 1, 1)), math.floor(size * 0.45), T.SOFT, T.FONT_HEAVY, Enum.TextXAlignment.Center)
	initial.Size = UDim2.fromScale(1, 1)
	if id > 0 then
		local img = new("ImageLabel", { Name = "Img", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Image = thumbs[id] or "" }, holder)
		T.corner(img, size // 2)
		if not thumbs[id] then
			task.spawn(function()
				local ok, url = pcall(function() return Players:GetUserThumbnailAsync(id, Enum.ThumbnailType.HeadShot, Enum.ThumbnailSize.Size100x100) end)
				if ok and type(url) == "string" then thumbs[id] = url; if img.Parent then img.Image = url end end
			end)
		end
	end
	return holder
end

local function partyPanel()
	clear(right)
	local c = L.compact
	local W = L.rightW
	local pt = myParty()
	local lead = iLead()
	local hdr = text(right, "Header", "", if c then 12 else 14, T.TEXT, T.FONT_HEAVY)
	hdr.Position = UDim2.fromOffset(14, 10); hdr.Size = UDim2.fromOffset(W - 120, 22)
	hdr.RichText = true
	local n = if pt then #pt.members else 1
	hdr.Text = ('PARTY  <font color="%s">%d/%d</font>'):format(T.hex(T.MUTED), n, PlayConfig.PARTY_MAX)
	local inv = button(right, "Invite", if S.inviting then "BACK" else "INVITE", not S.inviting and n < PlayConfig.PARTY_MAX,
		UDim2.fromOffset(if c then 74 else 96, if c then 24 else 28), UDim2.new(1, if c then -84 else -108, 0, 8))
	inv.TextSize = if c then 11 else 12
	inv.MouseButton1Click:Connect(function()
		S.inviting = not S.inviting
		if S.inviting then
			task.spawn(function()
				local r = ask("players")
				S.players = if r.ok and type(r.list) == "table" then r.list else {}
				refresh()
			end)
		end
		refresh()
	end)
	local y = if c then 40 else 46
	local rowH = if c then 40 else 52
	if S.inviting then
		-- everyone else in this server, with INVITE (or INVITED)
		local list = S.players or {}
		if #list == 0 then
			local e = text(right, "Empty", "nobody else is in this server yet", if c then 11 else 12, T.MUTED, T.FONT)
			e.Position = UDim2.fromOffset(14, y); e.Size = UDim2.fromOffset(W - 28, 20)
			y += 28
		end
		for i, o in list do
			if i > (if c then 5 else 7) then break end
			local row = new("Frame", { Name = "P" .. i, BorderSizePixel = 0, BackgroundColor3 = T.CARD, BackgroundTransparency = 0.2,
				Position = UDim2.fromOffset(10, y), Size = UDim2.fromOffset(W - 20, rowH - 6) }, right)
			T.corner(row, 5)
			local hs = headshot(row, o.id, o.display, rowH - 18)
			hs.Position = UDim2.fromOffset(6, 6)
			local nm = text(row, "Name", o.display, if c then 12 else 14, T.TEXT, T.FONT_BOLD)
			nm.Position = UDim2.fromOffset(rowH, 0); nm.Size = UDim2.new(1, -rowH - 86, 1, 0); nm.TextTruncate = Enum.TextTruncate.AtEnd
			local tag = if o.mine then "IN PARTY" elseif o.invited then "INVITED" elseif o.inMatch then "IN A MATCH" else nil
			if tag then
				local t = text(row, "Tag", tag, if c then 9 else 11, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Right)
				t.AnchorPoint = Vector2.new(1, 0); t.Position = UDim2.new(1, -10, 0, 0); t.Size = UDim2.new(0, 80, 1, 0)
			else
				local b = button(row, "Go", "INVITE", true, UDim2.fromOffset(if c then 58 else 70, if c then 22 else 26), UDim2.new(1, if c then -64 else -78, 0.5, if c then -11 else -13))
				b.TextSize = if c then 10 else 12
				b.MouseButton1Click:Connect(function()
					task.spawn(function()
						local r = ask("invite", o.id)
						if r.ok then o.invited = true; notice("invite sent to " .. o.display); refresh() end
					end)
				end)
			end
			y += rowH
		end
		right.Size = UDim2.fromOffset(W, y + 8)
		return
	end
	if not pt then right.Size = UDim2.fromOffset(W, y + 8); return end
	for i, m in pt.members do
		local row = new("Frame", { Name = "M" .. i, BorderSizePixel = 0, BackgroundColor3 = if m.id == me.UserId then T.CARD_HI else T.CARD,
			BackgroundTransparency = 0.15, Position = UDim2.fromOffset(10, y), Size = UDim2.fromOffset(W - 20, rowH - 6) }, right)
		T.corner(row, 5)
		local hs = headshot(row, m.id, m.display, rowH - 18)
		hs.Position = UDim2.fromOffset(6, 6)
		if m.leader then
			-- the leader's mark: a small amber diamond on the headshot's corner
			local d = new("Frame", { Name = "Lead", BorderSizePixel = 0, BackgroundColor3 = T.ACCENT, Rotation = 45, AnchorPoint = Vector2.new(0.5, 0.5),
				Position = UDim2.fromOffset(rowH - 14, 8), Size = UDim2.fromOffset(9, 9), ZIndex = 3 }, row)
			T.corner(d, 2)
		end
		local nm = text(row, "Name", m.display, if c then 12 else 14, T.TEXT, T.FONT_BOLD)
		nm.Position = UDim2.fromOffset(rowH, if c then 3 else 6); nm.Size = UDim2.new(1, -rowH - 70, 0, 18); nm.TextTruncate = Enum.TextTruncate.AtEnd
		local subT = if m.leader then "LEADER" else "MEMBER"
		if m.rank then subT = subT .. "  ·  " .. RankedStyle.label(m.rank) end
		local sub = text(row, "Sub", subT, if c then 9 else 11, if m.leader then T.ACCENT else T.MUTED, T.FONT_BOLD)
		sub.Position = UDim2.fromOffset(rowH, if c then 20 else 25); sub.Size = UDim2.new(1, -rowH - 70, 0, 14); sub.TextTruncate = Enum.TextTruncate.AtEnd
		if m.rank then
			local b = RankedStyle.badge(row, rowH - 14, m.rank)
			b.AnchorPoint = Vector2.new(1, 0.5); b.Position = UDim2.new(1, -6, 0.5, 0)
		end
		-- the leader's say over someone else: LEAD (real players only) and KICK
		if lead and m.id ~= me.UserId and not pt.inMatch then
			local bx = if m.rank then -(rowH - 4) else -6
			local k = button(row, "Kick", "KICK", false, UDim2.fromOffset(if c then 36 else 42, if c then 18 else 20), UDim2.new(1, bx - (if c then 36 else 42), 0.5, if c then -9 else -10))
			k.TextSize = if c then 9 else 10
			k.MouseButton1Click:Connect(function() task.spawn(ask, "kick", m.id) end)
			if not m.standIn then
				local l = button(row, "Promote", "LEAD", false, UDim2.fromOffset(if c then 36 else 42, if c then 18 else 20), UDim2.new(1, bx - (if c then 78 else 90), 0.5, if c then -9 else -10))
				l.TextSize = if c then 9 else 10
				l.MouseButton1Click:Connect(function() task.spawn(ask, "promote", m.id) end)
			end
		end
		y += rowH
	end
	-- the invites still open
	for _, iv in pt.outgoing or {} do
		local t = text(right, "Out" .. iv.id, ("INVITED  ·  %s"):format(string.upper(iv.name)), if c then 10 else 11, T.MUTED, T.FONT_BOLD)
		t.Position = UDim2.fromOffset(16, y); t.Size = UDim2.fromOffset(W - 80, 18); t.TextTruncate = Enum.TextTruncate.AtEnd
		t:SetAttribute("Ends", os.clock() + (iv.left or 0))
		local cd = text(right, "OutT" .. iv.id, "", if c then 10 else 11, T.DIM, T.FONT_BOLD, Enum.TextXAlignment.Right)
		cd.Name = "Countdown"; cd:SetAttribute("Ends", os.clock() + (iv.left or 0))
		cd.Position = UDim2.new(1, -60, 0, y); cd.Size = UDim2.fromOffset(46, 18)
		y += 22
	end
	right.Size = UDim2.fromOffset(W, y + 8)
end

-- ------------------------------------------------------------------ the big button (bottom)
local function bottomBar()
	clear(bottom)
	local c = L.compact
	local pt = myParty()
	if not pt then return end
	local W = if c then 300 else 480
	local bw, bh = if c then 220 else 320, if c then 44 else 56
	-- the pick, over the button: RANKED · 2V2 and your rank in it
	local pick = text(bottom, "Pick", "", if c then 13 else 16, T.TEXT, T.FONT_TITLE, Enum.TextXAlignment.Center)
	pick.Position = UDim2.fromOffset(0, 0); pick.Size = UDim2.fromOffset(W, 22); pick.RichText = true
	local mine = if pt.ranked then S.ranked[pt.mode] else nil
	pick.Text = (if pt.ranked then "RANKED" else "CASUAL") .. "  ·  " .. modeName(pt.mode)
		.. (if mine then ('  <font color="%s">%s</font>'):format(T.hex(RankedStyle.color(mine)), RankedStyle.label(mine)) else "")
	local y = if c then 30 else 36
	local main: GuiObject
	if pt.found then
		main = new("Frame", { Name = "Found", BorderSizePixel = 0, BackgroundColor3 = T.ACCENT, Size = UDim2.fromOffset(bw, bh), Position = UDim2.fromOffset((W - bw) // 2, y) }, bottom)
		T.corner(main, 6)
		local t = text(main, "Text", if pt.found.waiting then "WAITING FOR AN ARENA" else "MATCH FOUND", if c then 15 else 19, T.INK, T.FONT_SHOUT, Enum.TextXAlignment.Center)
		t.Size = UDim2.new(1, 0, 0.62, 0)
		local cd = text(main, "Countdown", "", if c then 11 else 13, T.INK, T.FONT_BOLD, Enum.TextXAlignment.Center)
		cd.Position = UDim2.fromScale(0, 0.55); cd.Size = UDim2.new(1, 0, 0.4, 0)
		cd:SetAttribute("FoundAt", pt.found.at)
	elseif pt.queue then
		main = T.plate(bottom, "Searching", UDim2.fromOffset((W - bw) // 2, y), UDim2.fromOffset(bw, bh))
		stroke(main, T.ACCENT, 0.45)
		local t = text(main, "Clock", "SEARCHING", if c then 15 else 18, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Center)
		t.Size = UDim2.new(1, 0, 0.62, 0); t:SetAttribute("Since", pt.queue.since)
		local sub = text(main, "Range", if pt.ranked then "" else "looking for players", if c then 10 else 12, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center)
		sub.Position = UDim2.fromScale(0, 0.55); sub.Size = UDim2.new(1, 0, 0.4, 0)
		if pt.ranked then sub:SetAttribute("Since", pt.queue.since) end
		-- the spinner: a small amber bar sliding under the clock
		local track = new("Frame", { Name = "Track", BorderSizePixel = 0, BackgroundColor3 = T.TRACK, Position = UDim2.new(0, 14, 1, -6), Size = UDim2.new(1, -28, 0, 2) }, main)
		T.corner(track, 1)
		local dot = new("Frame", { Name = "Dot", BorderSizePixel = 0, BackgroundColor3 = T.ACCENT, Size = UDim2.new(0.22, 0, 1, 0) }, track)
		T.corner(dot, 1)
		local cancelB = button(bottom, "Cancel", "CANCEL", false, UDim2.fromOffset(if c then 64 else 96, bh), UDim2.fromOffset((W - bw) // 2 + bw + 8, y))
		cancelB.MouseButton1Click:Connect(function() task.spawn(ask, "cancel") end)
	elseif iLead() then
		local b = button(bottom, "Find", "FIND MATCH", true, UDim2.fromOffset(bw, bh), UDim2.fromOffset((W - bw) // 2, y))
		b.FontFace = T.FONT_SHOUT; b.TextSize = if c then 16 else 20
		b.MouseButton1Click:Connect(function() task.spawn(ask, "find") end)
		main = b
	else
		main = T.plate(bottom, "Waiting", UDim2.fromOffset((W - bw) // 2, y), UDim2.fromOffset(bw, bh))
		local t = text(main, "Text", "WAITING FOR " .. string.upper(leaderName()), if c then 12 else 14, T.MUTED, T.FONT_HEAVY, Enum.TextXAlignment.Center)
		t.Size = UDim2.fromScale(1, 1); t.TextTruncate = Enum.TextTruncate.AtEnd
	end
	local _ = main
end

-- ------------------------------------------------------------------ nameplates over the lineup
-- (each plate is its own BillboardGui straight in PlayerGui with ResetOnSpawn off: a respawn clears anything else there)
local plateList: { BillboardGui } = {}
local plates = { GetChildren = function(_: any): { BillboardGui } return plateList end,
	ClearAllChildren = function(_: any) for _, b in plateList do b:Destroy() end; table.clear(plateList) end }
local function bodyOf(m: any): BasePart?
	if m.standIn then
		local f = workspace:FindFirstChild("PartyLobbies")
		if not f then return nil end
		for _, d in f:GetDescendants() do
			if d:IsA("Model") and d:GetAttribute("StandIn") == m.id then return d:FindFirstChild("Head") :: BasePart? end
		end
		return nil
	end
	local p = Players:GetPlayerByUserId(m.id)
	local ch = p and p.Character
	return ch and ch:FindFirstChild("Head") :: BasePart?
end
local function namePlates()
	plates:ClearAllChildren()
	local pt = myParty()
	if not S.open or not pt or pt.inMatch then return end
	for _, m in pt.members do
		local head = bodyOf(m)
		if not head then continue end
		local bb = new("BillboardGui", { Name = "JankPlayPlate" .. m.id, Adornee = head, AlwaysOnTop = true, LightInfluence = 0, Size = UDim2.fromOffset(190, 46),
			StudsOffsetWorldSpace = Vector3.new(0, 2.1, 0), ResetOnSpawn = false }, pg)
		table.insert(plateList, bb)
		local row = new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, bb)
		local lay = new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, HorizontalAlignment = Enum.HorizontalAlignment.Center,
			VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, 6), SortOrder = Enum.SortOrder.LayoutOrder }, row)
		local _ = lay
		if m.rank then
			local b = RankedStyle.badge(row, 30, m.rank)
			b.LayoutOrder = 1
		end
		if m.leader then
			local d = new("Frame", { Name = "Lead", BorderSizePixel = 0, BackgroundColor3 = T.ACCENT, Rotation = 45, Size = UDim2.fromOffset(9, 9), LayoutOrder = 2 }, row)
			T.corner(d, 2)
		end
		local nm = text(row, "Name", m.display, 15, T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Center, true)
		nm.AutomaticSize = Enum.AutomaticSize.X; nm.Size = UDim2.fromOffset(0, 22); nm.LayoutOrder = 3
	end
end

-- ------------------------------------------------------------------ the room's camera
local CAM = "JankPlayCam"
local savedCam: any = nil
local function lineupCF(): CFrame?
	local pt = myParty()
	local room = pt and pt.room
	if not room or typeof(room.cam) ~= "CFrame" then return nil end
	-- keep the party in the middle of the screen: the camera slides across to the centre of the plinths in use
	local sx, n = 0, 0
	for _, s in room.spots or {} do if typeof(s) == "CFrame" then sx += s.Position.X; n += 1 end end
	local dx = if n > 0 then sx / n - room.focus.X else 0
	return room.cam + Vector3.new(dx, 0, 0)
end
local fovConn: RBXScriptConnection? = nil
local function bindCam(on: boolean)
	local cam = workspace.CurrentCamera :: Camera
	if on then
		if savedCam then return end
		savedCam = { type = cam.CameraType, fov = cam.FieldOfView }
		local want = 40
		fovConn = cam:GetPropertyChangedSignal("FieldOfView"):Connect(function()
			if math.abs(cam.FieldOfView - want) > 0.01 then cam.FieldOfView = want end
		end)
		RunService:BindToRenderStep(CAM, Enum.RenderPriority.Last.Value + 60, function()
			local c = workspace.CurrentCamera :: Camera
			local cf = lineupCF()
			if not cf then return end
			c.CameraType = Enum.CameraType.Scriptable
			c.FieldOfView = want
			c.CFrame = cf
			c.Focus = cf * CFrame.new(0, 0, -16)
			-- the mouse is free while the screen is up (first person would lock it to the middle)
			UIS.MouseBehavior = Enum.MouseBehavior.Default
			UIS.MouseIconEnabled = true
			-- your own body shows in the lineup (first person hides it)
			local ch = me.Character
			if ch then
				for _, d in ch:GetDescendants() do
					if (d:IsA("BasePart") or d:IsA("Decal")) and d.LocalTransparencyModifier ~= 0 then d.LocalTransparencyModifier = 0 end
				end
			end
		end)
	else
		if not savedCam then return end
		pcall(function() RunService:UnbindFromRenderStep(CAM) end)
		if fovConn then fovConn:Disconnect(); fovConn = nil end
		cam.CameraType = if savedCam.type == Enum.CameraType.Scriptable then Enum.CameraType.Custom else savedCam.type
		cam.FieldOfView = savedCam.fov
		savedCam = nil
	end
end

-- ------------------------------------------------------------------ open / close
local hidden: { [ScreenGui]: boolean } = {}
local savedOpen: any = nil
local function controls(on: boolean)
	pcall(function()
		local c = require(me:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: any):GetControls()
		if on then c:Enable() else c:Disable() end
	end)
end

refresh = function()
	if not S.open then return end
	fit()
	modeList()
	partyPanel()
	bottomBar()
	namePlates()
end
UI.refresh = function() refresh() end

function UI.isOpen(): boolean return S.open end

function UI.open()
	if S.open or not S.party then return end
	S.open = true
	savedOpen = me:GetAttribute("LoadoutOpen")
	table.clear(hidden)
	for _, g in pg:GetChildren() do
		if g:IsA("ScreenGui") and g ~= gui and g.Name ~= "JankPlayFade" and g.Enabled then hidden[g] = true; g.Enabled = false end
	end
	me:SetAttribute("LoadoutOpen", true) -- (a menu is up: hands, weapons, movement and the other screens hold still)
	me:SetAttribute("PlayOpen", true)
	controls(false)
	lobby.Visible = true
	bindCam(true)
	refresh()
	if UI.placeResult then UI.placeResult() end
end

function UI.close()
	if not S.open then return end
	S.open = false
	S.inviting = false
	lobby.Visible = false
	plates:ClearAllChildren()
	bindCam(false)
	for g in hidden do if g.Parent then g.Enabled = true end end
	table.clear(hidden)
	me:SetAttribute("LoadoutOpen", if savedOpen == true then true else false)
	me:SetAttribute("PlayOpen", nil)
	controls(true)
end

leaveB.MouseButton1Click:Connect(function()
	task.spawn(function()
		local r = ask("leave")
		if r.ok then S.party = nil; UI.close() end
	end)
end)

-- ------------------------------------------------------------------ the invite toast (anywhere but a match)
local toastF = T.plate(stage, "Invite", UDim2.new(0.5, 0, 0, 24), UDim2.fromOffset(440, 78))
toastF.AnchorPoint = Vector2.new(0.5, 0); toastF.Visible = false; toastF.ZIndex = 40
stroke(toastF, T.ACCENT, 0.5)
local tHead = text(toastF, "Head", "", 15, T.TEXT, T.FONT_HEAVY); tHead.ZIndex = 41
tHead.Position = UDim2.fromOffset(16, 10); tHead.Size = UDim2.new(1, -190, 0, 20); tHead.TextTruncate = Enum.TextTruncate.AtEnd
local tSub = text(toastF, "Sub", "", 12, T.MUTED, T.FONT_BOLD); tSub.ZIndex = 41
tSub.Position = UDim2.fromOffset(16, 34); tSub.Size = UDim2.new(1, -190, 0, 16)
local tJoin = button(toastF, "Join", "JOIN", true, UDim2.fromOffset(78, 34), UDim2.new(1, -172, 0, 14)); tJoin.ZIndex = 41
local tNo = button(toastF, "Decline", "DECLINE", false, UDim2.fromOffset(78, 34), UDim2.new(1, -88, 0, 14)); tNo.ZIndex = 41
local tTrack = new("Frame", { BorderSizePixel = 0, BackgroundColor3 = T.TRACK, Position = UDim2.new(0, 16, 1, -12), Size = UDim2.new(1, -32, 0, 3), ZIndex = 41 }, toastF)
T.corner(tTrack, 2)
local tFill = new("Frame", { BorderSizePixel = 0, BackgroundColor3 = T.ACCENT, Size = UDim2.fromScale(1, 1), ZIndex = 42 }, tTrack)
T.corner(tFill, 2)
local function topInvite(): any
	local best = nil
	for _, iv in S.invites do if not best or iv.expires < best.expires then best = iv end end
	return best
end
local function answer(yes: boolean)
	local iv = topInvite()
	if not iv then return end
	for i, x in S.invites do if x == iv then table.remove(S.invites, i); break end end
	task.spawn(function() ask("answer", iv.id, yes) end)
end
tJoin.MouseButton1Click:Connect(function() answer(true) end)
tNo.MouseButton1Click:Connect(function() answer(false) end)

-- ------------------------------------------------------------------ the ranked result card
local res = T.plate(stage, "RankedResult", UDim2.new(0.5, 0, 1, -200), UDim2.fromOffset(400, 112))
res.AnchorPoint = Vector2.new(0.5, 1); res.Visible = false; res.ZIndex = 35
-- where the card sits: right of the end screen in a match, over the big button in the lobby
local function placeResult()
	local c = L.compact
	local inMatch = me:GetAttribute("Zone") == "match" and not S.open
	if inMatch and not c then
		res.AnchorPoint = Vector2.new(0, 0.5); res.Position = UDim2.new(0.5, 262, 0.5, 0)
	elseif inMatch then
		res.AnchorPoint = Vector2.new(0.5, 0); res.Position = UDim2.new(0.5, 0, 0, 10)
	else
		res.AnchorPoint = Vector2.new(0.5, 1); res.Position = UDim2.new(0.5, 0, 1, if c then -126 else -196)
	end
end
UI.placeResult = placeResult
local resTok = 0
function UI.showResult(r: any)
	if type(r) ~= "table" or type(r.rank) ~= "table" then return end
	resTok += 1
	local my = resTok
	clear(res)
	local c = L.compact
	placeResult()
	local W = if c then 320 else 400
	res.Size = UDim2.fromOffset(W, 112)
	stroke(res, if r.won then T.ACCENT else T.EDGE, if r.won then 0.4 else T.EDGE_A)
	local bs = 76
	local badge = RankedStyle.badge(res, bs, r.rank)
	badge.Position = UDim2.fromOffset(12, 12)
	for _, d in badge:GetDescendants() do if d:IsA("GuiObject") then d.ZIndex += 35 end end
	local x = bs + 22
	local head = text(res, "Head", (if r.won then "WIN" else "LOSS") .. "  ·  RANKED " .. modeName(r.mode), 12, if r.won then T.ACCENT else T.SOFT, T.FONT_HEAVY)
	head.Position = UDim2.fromOffset(x, 12); head.Size = UDim2.fromOffset(W - x - 12, 16); head.ZIndex = 36
	local nm = text(res, "Rank", RankedStyle.label(r.rank), 18, RankedStyle.color(r.rank), T.FONT_TITLE)
	nm.Position = UDim2.fromOffset(x, 30); nm.Size = UDim2.fromOffset(W - x - 12, 24); nm.ZIndex = 36
	-- the rating and the change
	local num = text(res, "Rating", Ranked.comma(r.before), 22, T.TEXT, T.FONT_HEAVY)
	num.Position = UDim2.fromOffset(x, 56); num.Size = UDim2.fromOffset(110, 26); num.ZIndex = 36
	local d = tonumber(r.delta) or 0
	local dl = text(res, "Delta", (if d >= 0 then "+" else "−") .. tostring(math.abs(d)), 18, if d >= 0 then GOOD else T.DANGER, T.FONT_HEAVY)
	dl.Position = UDim2.fromOffset(x + 92, 59); dl.Size = UDim2.fromOffset(70, 22); dl.ZIndex = 36
	local tag = if r.placedNow then "PLACED" elseif r.promoted then "PROMOTED" elseif r.demoted then "DEMOTED"
		elseif r.rank.placed ~= true then ("PLACEMENT %d OF %d"):format(r.rank.n or 0, r.rank.need or Ranked.PLACEMENTS) else ""
	local tg = text(res, "Tag", tag, 11, if r.demoted then T.DANGER else T.ACCENT, T.FONT_HEAVY, Enum.TextXAlignment.Right)
	tg.Position = UDim2.new(1, -132, 0, 62); tg.Size = UDim2.fromOffset(120, 16); tg.ZIndex = 36
	-- the division bar: where you stand in it, sliding from before to after
	local track = new("Frame", { BorderSizePixel = 0, BackgroundColor3 = T.TRACK, Position = UDim2.fromOffset(x, 90), Size = UDim2.fromOffset(W - x - 14, 5), ZIndex = 36 }, res)
	T.corner(track, 3)
	local col = RankedStyle.color(r.rank)
	local p1 = math.clamp(tonumber(r.rank.progress) or 0, 0, 1)
	local p0 = p1
	if r.rank.placed and not r.promoted and not r.demoted and not r.placedNow and type(r.rank.hi) == "number" then
		local lo = r.rank.lo or (r.rank.hi - Ranked.DIV)
		p0 = math.clamp((r.before - lo) / math.max(1, r.rank.hi - lo), 0, 1)
	elseif r.promoted then p0 = 0 elseif r.demoted then p0 = 1 end
	local fill = new("Frame", { BorderSizePixel = 0, BackgroundColor3 = col, Size = UDim2.fromScale(math.max(0.02, p0), 1), ZIndex = 37 }, track)
	T.corner(fill, 3)
	res.Visible = true
	res.BackgroundTransparency = 1
	T.tween(res, 0.25, { BackgroundTransparency = T.BG_A })
	task.delay(0.6, function()
		if my ~= resTok then return end
		T.tween(fill, 1.1, { Size = UDim2.fromScale(math.max(0.02, p1), 1) }, Enum.EasingStyle.Quart)
		-- the number counts to its new value
		local t0 = os.clock()
		while my == resTok and os.clock() - t0 < 1.1 do
			local u = 1 - (1 - (os.clock() - t0) / 1.1) ^ 3
			num.Text = Ranked.comma(r.before + (r.after - r.before) * u)
			task.wait()
		end
		if my == resTok then num.Text = Ranked.comma(r.after) end
	end)
	task.delay(14, function() if my == resTok then res.Visible = false end end)
end

-- ------------------------------------------------------------------ the server's pushes
function UI.setState(st: any)
	if type(st) ~= "table" then return end
	S.ranked = if type(st.ranked) == "table" then st.ranked else S.ranked
	S.best = st.best
	S.invites = if type(st.invites) == "table" then st.invites else S.invites
	UI.onParty(st.party)
end
function UI.onParty(view: any)
	local had = S.party
	S.party = view
	if view then
		if not had or had.ranked ~= view.ranked then S.tab = if view.ranked then "ranked" else "casual" end
		if had and #had.members ~= #view.members and S.inviting then S.inviting = false end
	end
	refresh()
end
function UI.onInvite(iv: any)
	if type(iv) ~= "table" then return end
	for _, x in S.invites do if x.id == iv.id then return end end
	table.insert(S.invites, iv)
end
function UI.onInviteGone(id: any)
	for i, x in S.invites do if x.id == id then table.remove(S.invites, i); break end end
end
function UI.setRanked(modes: any, best: any)
	if type(modes) == "table" then S.ranked = modes end
	S.best = best
	refresh()
end

-- ------------------------------------------------------------------ the clocks (searching, found, invites)
local acc, plateT = 0, 0
RunService.Heartbeat:Connect(function(dt)
	-- the invite toast: the soonest-ending one, not in a match
	local now = workspace:GetServerTimeNow()
	for i = #S.invites, 1, -1 do if (S.invites[i].expires or 0) < now then table.remove(S.invites, i) end end
	local iv = topInvite()
	local show = iv ~= nil and me:GetAttribute("Zone") ~= "match"
	if toastF.Visible ~= show then toastF.Visible = show end
	if show then
		tHead.Text = string.upper(iv.fromName or "?") .. " INVITED YOU"
		tSub.Text = ("%s %s  ·  PARTY OF %d"):format(if iv.ranked then "RANKED" else "CASUAL", modeName(iv.mode), iv.size or 1)
		tFill.Size = UDim2.fromScale(math.clamp((iv.expires - now) / PlayConfig.INVITE_TTL, 0, 1), 1)
	end
	acc += dt
	if acc < 0.1 or not S.open then return end
	acc = 0
	-- the nameplates follow the bodies: a respawn or a stand-in arriving late gets its plate
	plateT += 0.1
	if plateT >= 0.5 then
		plateT = 0
		local pt = S.party
		local ok = pt ~= nil and #plates:GetChildren() == #pt.members
		if ok then
			for _, b in plates:GetChildren() do
				local a = (b :: BillboardGui).Adornee
				if not a or not a:IsDescendantOf(workspace) then ok = false end
			end
		end
		if not ok and pt and not pt.inMatch then namePlates() end
	end
	for _, d in bottom:GetDescendants() do
		if d:IsA("TextLabel") then
			local since = d:GetAttribute("Since")
			if type(since) == "number" then
				if d.Name == "Clock" then d.Text = "SEARCHING  " .. mmss(now - since)
				else
					local w = Ranked.window(now - since)
					d.Text = if w == math.huge then "any rating" else ("rating %s  ±%d"):format(Ranked.comma(S.party and S.party.queue and S.party.queue.rating or 0), math.floor(w))
				end
			end
			local at = d:GetAttribute("FoundAt")
			if type(at) == "number" then d.Text = if at - now > 0 then ("GOING IN %d"):format(math.ceil(at - now)) else "GOING IN" end
		elseif d.Name == "Dot" and d:IsA("Frame") then
			local u = (os.clock() * 0.6) % 1
			d.Position = UDim2.fromScale(u * 0.78, 0)
		end
	end
	for _, d in right:GetChildren() do
		local ends = d:GetAttribute("Ends")
		if d.Name == "Countdown" and type(ends) == "number" and d:IsA("TextLabel") then d.Text = mmss(ends - os.clock()) end
	end
end)

-- ------------------------------------------------------------------ test helpers (PlayClient's PlayTest attribute)
function UI.tab(id: string) S.tab = if id == "ranked" then "ranked" else "casual"; refresh() end
function UI.invitePanel(on: boolean)
	S.inviting = on
	if on then
		task.spawn(function()
			local r = ask("players")
			S.players = if r.ok and type(r.list) == "table" then r.list else {}
			refresh()
		end)
	end
	refresh()
end
function UI.fakeScreen(v: Vector2?) S.fake = v; refresh() end
-- (tests: what the nameplates are on)
function UI.plateInfo(): any
	local out = {}
	for _, b in plates:GetChildren() do
		local a = (b :: BillboardGui).Adornee
		table.insert(out, b.Name .. " -> " .. (if a then a:GetFullName() else "nil") .. " enabled=" .. tostring((b :: BillboardGui).Enabled))
	end
	return out
end
local cam0 = workspace.CurrentCamera
if cam0 then cam0:GetPropertyChangedSignal("ViewportSize"):Connect(function() if S.open then refresh() end end) end

return UI
