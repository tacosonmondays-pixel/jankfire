--!strict
-- the owner's anti-cheat panel (server/AntiCheat.server.luau answers it, docs/ANTI-CHEAT.md): "/ac" in chat or F7.
--   PLAYERS: who's in this server with how many points and their aim counts (kick, clear, confirm cheater; ban when
--     bans are on)
--   LOG: every put back, kick, ban, aim flag, report and confirm, from every server
--   REPORTS: players' reports (server/Reports.luau): the reason, the public chat it kept, the reported player's
--     anti-cheat state, whether the match recording came with it; dismiss, kick, ban, confirm cheater
--   the bottom row works on any user id, online or not: CONFIRM (the restores: Stats, ranked, quests), UNCONFIRM (a
--   wrong catch), ERASE (Roblox's right-to-erasure), UNBAN (with bans on)
-- the server checks the owner on every call; anyone else never gets this panel built at all
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")
local TextChatService = game:GetService("TextChatService")

local Theme = require(script.Parent:WaitForChild("Theme"))
local MenuCursor = require(script.Parent:WaitForChild("MenuCursor")) :: any
local T = Theme
local me = Players.LocalPlayer
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("AntiCheat", 30) :: RemoteFunction?
if not Remote then return end

local function call(...: any): any
	local args = table.pack(...)
	local ok, res = pcall(function() return (Remote :: RemoteFunction):InvokeServer(table.unpack(args, 1, args.n)) end)
	return if ok then res else nil
end

local hello = call("hello")
if type(hello) ~= "table" or hello.admin ~= true then return end

local REASON = { cheating = "Cheating", chat = "Abusive chat", griefing = "Griefing", other = "Other" }

-- ------------------------------------------------------------------ the panel
local gui = T.new("ScreenGui", { Name = "AntiCheatPanel", ResetOnSpawn = false, DisplayOrder = 60, IgnoreGuiInset = true, Enabled = false, ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, me:WaitForChild("PlayerGui"))
local root = T.scaled(gui)
local plate = T.plate(root, "Panel", UDim2.new(0.5, -400, 0.5, -260), UDim2.fromOffset(800, 520))
plate.BackgroundTransparency = 0.08

local title = T.text(plate, "Title", "ANTI-CHEAT", 18, T.TEXT, T.FONT_TITLE)
title.Position = UDim2.fromOffset(18, 12); title.Size = UDim2.fromOffset(300, 26)
local status = T.text(plate, "Status", "", 13, T.MUTED)
status.Position = UDim2.fromOffset(18, 38); status.Size = UDim2.fromOffset(600, 18)
status.Text = if hello.studio then "Studio test: kicks and bans are only written down"
	else ("Kicks %s  ·  Bans %s  ·  %d points in %d s is a kick"):format(if hello.kicks then "on" else "off", if hello.bans then "on" else "off", hello.kickAt or 0, hello.window or 0)

local function button(parent: Instance, name: string, text: string, pos: UDim2, w: number, accent: boolean?): TextButton
	local b = T.new("TextButton", {
		Name = name, Text = text, FontFace = T.FONT_BOLD, TextSize = 13, AutoButtonColor = true,
		TextColor3 = if accent then T.INK else T.TEXT, BackgroundColor3 = if accent then T.ACCENT else T.CARD_HI,
		BorderSizePixel = 0, Position = pos, Size = UDim2.fromOffset(w, 26),
	}, parent)
	T.corner(b, 4)
	return b
end

local close = button(plate, "Close", "CLOSE", UDim2.new(1, -86, 0, 14), 70)
close.Modal = true -- (frees the mouse from first person while the panel is up)
local tabs: { [string]: TextButton } = {
	players = button(plate, "TabPlayers", "PLAYERS", UDim2.fromOffset(18, 66), 100, true),
	log = button(plate, "TabLog", "LOG", UDim2.fromOffset(126, 66), 100),
	reports = button(plate, "TabReports", "REPORTS", UDim2.fromOffset(234, 66), 100),
}
local note = T.text(plate, "Note", "", 13, T.SOFT, T.FONT, Enum.TextXAlignment.Right)
note.Position = UDim2.new(1, -440, 0, 70); note.Size = UDim2.fromOffset(420, 18)

local list = T.new("ScrollingFrame", {
	Name = "List", BackgroundColor3 = T.CARD, BackgroundTransparency = 0.2, BorderSizePixel = 0,
	Position = UDim2.fromOffset(18, 102), Size = UDim2.new(1, -36, 1, -158),
	CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollBarThickness = 6, ScrollingDirection = Enum.ScrollingDirection.Y,
}, plate)
T.corner(list, 4)
T.new("UIListLayout", { Padding = UDim.new(0, 4), SortOrder = Enum.SortOrder.LayoutOrder }, list)
T.new("UIPadding", { PaddingTop = UDim.new(0, 6), PaddingLeft = UDim.new(0, 6), PaddingRight = UDim.new(0, 10), PaddingBottom = UDim.new(0, 6) }, list)

-- a button that asks once more before it acts
local function twice(b: TextButton, label: string, act: () -> ())
	local armed = 0
	b.Activated:Connect(function()
		if os.clock() - armed < 3 then
			armed = 0
			b.Text = label
			act()
		else
			armed = os.clock()
			b.Text = "SURE?"
			task.delay(3, function() if os.clock() - armed >= 2.9 then b.Text = label end end)
		end
	end)
end
local function answer(what: string, res: any): string
	if type(res) == "table" and res.ok then return what .. (if res.why then " (" .. tostring(res.why) .. ")" else "") end
	return what .. " failed: " .. tostring(if type(res) == "table" and res.why then res.why else "no answer")
end

local tab = "players"
local detail: string? = nil -- (the report open in REPORTS)
local refresh: () -> ()

-- ------------------------------------------------------------------ the bottom row: any user id
do
	local box = T.new("TextBox", {
		Name = "UserId", PlaceholderText = "user id", Text = "", FontFace = T.FONT, TextSize = 13, TextColor3 = T.TEXT,
		PlaceholderColor3 = T.DIM, BackgroundColor3 = T.CARD_HI, BorderSizePixel = 0, ClearTextOnFocus = false,
		Position = UDim2.new(0, 18, 1, -44), Size = UDim2.fromOffset(160, 26),
	}, plate)
	T.corner(box, 4)
	local function id(): number?
		local n = tonumber(box.Text)
		if not n then note.Text = "type a user id" end
		return n
	end
	local x = 186
	local function act(name: string, label: string, w: number, fn: (number) -> ())
		local b = button(plate, name, label, UDim2.new(0, x, 1, -44), w)
		x += w + 6
		twice(b, label, function() local n = id(); if n then fn(n) end end)
	end
	act("Confirm", "CONFIRM CHEATER", 140, function(n)
		local r = call("confirm", n)
		note.Text = answer("confirmed " .. n, r) .. (if type(r) == "table" and r.since then (if r.since > 0 then ", since " .. os.date("%d %b", r.since) else ", everything") else "")
	end)
	act("Unconfirm", "UNCONFIRM", 100, function(n) note.Text = answer("unconfirmed " .. n, call("unconfirm", n)) end)
	act("Erase", "ERASE DATA", 100, function(n)
		local r = call("erase", n)
		note.Text = if type(r) == "table" and r.ok and r.res then ("erased: %d reports, %d scrubbed, %d log lines"):format(r.res.reports, r.res.scrubbed, r.res.logLines) else answer("erase", r)
	end)
	if hello.bans then
		act("Unban", "UNBAN", 80, function(n) note.Text = answer("unbanned " .. n, call("unban", n)) end)
	end
end

local function clear()
	for _, c in list:GetChildren() do if c:IsA("Frame") then c:Destroy() end end
end
local order = 0
local function rowFrame(h: number, alpha: number?): Frame
	order += 1
	local row = T.new("Frame", { Name = "Row", LayoutOrder = order, BackgroundColor3 = T.CARD_HI, BackgroundTransparency = alpha or 0.4, BorderSizePixel = 0, Size = UDim2.new(1, 0, 0, h) }, list)
	T.corner(row, 4)
	return row
end
local function cell(row: Instance, name: string, text: string, x: number, w: number, color: Color3, font: Font?, size: number?, y: number?)
	local c = T.text(row, name, text, size or 12, color, font)
	c.Position = UDim2.fromOffset(x, y or 2); c.Size = UDim2.fromOffset(w, 18)
	c.TextTruncate = Enum.TextTruncate.AtEnd
	return c
end
local function hhmm(t: number): string
	return os.date("%d %b %H:%M", t) :: string
end
local function empty(text: string)
	local row = rowFrame(24, 1)
	cell(row, "Empty", text, 6, 600, T.MUTED, nil, 13)
end

-- ------------------------------------------------------------------ PLAYERS
local function playerRows(rows: { any })
	clear()
	for _, r in rows do
		local row = rowFrame(52)
		cell(row, "Name", ("%s  @%s"):format(tostring(r.display), tostring(r.name)), 10, 300, T.TEXT, T.FONT_BOLD, 14, 5)
		cell(row, "Points", ("%d points"):format(tonumber(r.points) or 0), 320, 100, if (tonumber(r.points) or 0) > 0 then T.ACCENT else T.MUTED, T.FONT_BOLD, 13, 5)
		cell(row, "Aim", ("hits %d · head %d · snap %d · smoke %d"):format(r.hits or 0, r.heads or 0, r.snaps or 0, r.smoke or 0), 10, 300, T.MUTED, nil, 12, 27)
		cell(row, "Last", tostring(r.last or ""), 320, 200, T.SOFT, nil, 12, 27)
		if r.uid ~= me.UserId then
			local x = 1
			local function act(label: string, w: number, fn: () -> ())
				local b = button(row, label, label, UDim2.new(1, -(x + w), 0, 13), w)
				x += w + 6
				twice(b, label, fn)
			end
			if hello.bans then
				act("BAN", 50, function()
					note.Text = answer("banned " .. tostring(r.name), call("ban", r.uid, nil, "cheating"))
					refresh()
				end)
			end
			act("KICK", 54, function() note.Text = answer("kicked " .. tostring(r.name), call("kick", r.uid, "")); refresh() end)
			act("CONFIRM", 76, function() note.Text = answer("confirmed " .. tostring(r.name), call("confirm", r.uid)) end)
			act("CLEAR", 60, function() note.Text = answer("cleared " .. tostring(r.name), call("clear", r.uid)); refresh() end)
		end
	end
end

-- ------------------------------------------------------------------ LOG
local function logRows(rows: { any })
	clear()
	if #rows == 0 then empty("Nothing caught yet."); return end
	for i, e in rows do
		local row = rowFrame(22, if i % 2 == 0 then 0.6 else 0.8)
		local soft = e.act == "flag"
		cell(row, "Time", hhmm(tonumber(e.t) or 0), 6, 92, T.MUTED)
		cell(row, "Name", tostring(e.name), 100, 120, T.TEXT, T.FONT_BOLD)
		cell(row, "Kind", tostring(e.kind), 222, 64, if soft then T.SOFT else T.ACCENT, T.FONT_BOLD)
		cell(row, "Act", tostring(e.act) .. (if (tonumber(e.n) or 1) > 1 then (" x%d"):format(e.n) else ""), 288, 100, if e.act == "kick" or e.act == "ban" then T.DANGER else T.SOFT)
		cell(row, "Info", tostring(e.info), 390, 350, T.SOFT)
	end
end

-- ------------------------------------------------------------------ REPORTS
local function reportRows(rows: { any })
	clear()
	local open = 0
	for _, e in rows do if e.state == "open" then open += 1 end end
	note.Text = ("%d reports, %d open"):format(#rows, open)
	if #rows == 0 then empty("No reports."); return end
	for i, e in rows do
		local row = rowFrame(26, if e.state == "open" then 0.35 else 0.75)
		cell(row, "Time", hhmm(tonumber(e.t) or 0), 6, 92, T.MUTED, nil, 12, 4)
		cell(row, "Who", tostring(e.whoName), 100, 140, T.TEXT, T.FONT_BOLD, 12, 4)
		cell(row, "Why", REASON[e.why] or tostring(e.why), 244, 100, if e.why == "cheating" then T.ACCENT else T.SOFT, T.FONT_BOLD, 12, 4)
		cell(row, "By", "by " .. tostring(e.byName), 346, 130, T.MUTED, nil, 12, 4)
		cell(row, "What", ("%d lines%s · %s"):format(tonumber(e.lines) or 0, if e.rec then " · match" else "", tostring(e.ctx)), 478, 140, T.MUTED, nil, 12, 4)
		cell(row, "State", string.upper(tostring(e.state)), 620, 80, if e.state == "open" then T.ACCENT else T.DIM, T.FONT_BOLD, 11, 4)
		local open2 = T.new("TextButton", { Name = "Open", Text = "", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = 3 }, row)
		local id = e.id
		open2.Activated:Connect(function() detail = id; refresh() end)
	end
end

local function reportDetail(r: any)
	clear()
	if type(r) ~= "table" then empty("That report is gone (erased or past 30 days)."); return end
	local head = rowFrame(58, 0.2)
	cell(head, "Title", ("%s  ·  %s"):format(string.upper(tostring(r.whoName)), REASON[r.why] or tostring(r.why)), 10, 420, T.TEXT, T.FONT_BOLD, 15, 6)
	cell(head, "Sub", ("reported by %s · %s · from the %s%s"):format(tostring(r.byName), hhmm(tonumber(r.t) or 0), tostring(r.ctx),
		if r.match then (" · match %s%s"):format(tostring(r.match), if r.mode then " " .. tostring(r.mode) else "") else ""), 10, 520, T.MUTED, nil, 12, 32)
	local x = 1
	local function act(label: string, w: number, fn: () -> (), sure: boolean?)
		local b = button(head, label, label, UDim2.new(1, -(x + w), 0, 6), w)
		x += w + 6
		if sure then twice(b, label, fn) else b.Activated:Connect(fn) end
	end
	act("BACK", 60, function() detail = nil; refresh() end)
	act("DISMISS", 76, function() note.Text = answer("dismissed", call("dismiss", r.id)); detail = nil; refresh() end, true)
	if r.here then act("KICK", 54, function() note.Text = answer("kicked " .. tostring(r.whoName), call("kick", r.who, "", r.id)) end, true) end
	if hello.bans then act("BAN", 50, function() note.Text = answer("banned " .. tostring(r.whoName), call("ban", r.who, nil, "cheating")) end, true) end
	act("CONFIRM", 76, function()
		local res = call("confirm", r.who, nil, r.id)
		note.Text = answer("confirmed " .. tostring(r.whoName), res) .. (if type(res) == "table" and res.since then (if res.since > 0 then ", since " .. os.date("%d %b", res.since) else ", everything") else "")
	end, true)
	-- the reported player's anti-cheat state when the report was made
	local f = r.flags
	local fr = rowFrame(22, 0.6)
	if type(f) == "table" then
		local totals = {}
		if type(f.totals) == "table" then for k, n in f.totals do table.insert(totals, k .. " " .. tostring(n)) end end
		cell(fr, "Flags", ("anti-cheat: %d points here · %s kicks · totals: %s%s"):format(tonumber(f.points) or 0, tostring(f.kicks or 0),
			if #totals > 0 then table.concat(totals, ", ") else "none",
			if type(f.aim) == "table" then (" · aim: hits %d head %d snap %d smoke %d"):format(f.aim.hits or 0, f.aim.heads or 0, f.aim.snaps or 0, f.aim.smoke or 0) else ""), 8, 740, T.SOFT, nil, 12, 2)
		for _, v in f.recent or {} do
			local vr = rowFrame(20, 0.8)
			cell(vr, "Catch", ("%s %s: %s (%ds before)"):format(tostring(v.kind), tostring(v.act), tostring(v.info), tonumber(v.ago) or 0), 18, 720, T.MUTED, nil, 11, 1)
		end
	else
		cell(fr, "Flags", "anti-cheat: nothing on record", 8, 740, T.MUTED, nil, 12, 2)
	end
	local rr = rowFrame(22, 0.6)
	cell(rr, "Rec", if r.rec then ("match recording kept (%d KB)"):format(math.floor((tonumber(r.recBytes) or 0) / 1024)) else "no match recording", 8, 740, T.SOFT, nil, 12, 2)
	-- the public chat it kept (the reported player's lines stand out)
	local ch = rowFrame(22, 0.6)
	cell(ch, "Chat", ("public chat, the %d lines before the report"):format(#(r.chat or {})), 8, 740, T.SOFT, T.FONT_BOLD, 12, 2)
	for _, l in r.chat or {} do
		local lr = rowFrame(20, 0.85)
		cell(lr, "Time", os.date("%H:%M:%S", tonumber(l.t) or 0) :: string, 8, 64, T.DIM, nil, 11, 1)
		cell(lr, "Name", tostring(l.name), 74, 130, if l.who then T.ACCENT else T.TEXT, T.FONT_BOLD, 12, 1)
		cell(lr, "Text", tostring(l.x), 206, 540, if l.who then T.TEXT else T.SOFT, nil, 12, 1)
	end
end

refresh = function()
	if not gui.Enabled then return end
	order = 0
	if tab == "players" then
		local rows = call("players")
		if type(rows) == "table" then playerRows(rows) end
	elseif tab == "log" then
		local rows = call("log")
		if type(rows) == "table" then logRows(rows) end
	elseif detail then
		reportDetail(call("report", detail))
	else
		local rows = call("reports")
		if type(rows) == "table" then reportRows(rows) end
	end
end

local function setTab(t: string)
	tab = t
	detail = nil
	for k, b in tabs do
		b.BackgroundColor3 = if k == t then T.ACCENT else T.CARD_HI
		b.TextColor3 = if k == t then T.INK else T.TEXT
	end
	refresh()
end
for k, b in tabs do b.Activated:Connect(function() setTab(k) end) end

local function toggle()
	gui.Enabled = not gui.Enabled
	if gui.Enabled then refresh() end
end
close.Activated:Connect(function() gui.Enabled = false end)
gui:GetPropertyChangedSignal("Enabled"):Connect(function() MenuCursor.set("anticheat", gui.Enabled) end) -- (the mouse shows while it's up)

-- F7, or "/ac" in chat: with the new chat a command of this client's own (nothing goes out); with the legacy chat
-- (this place's) the server hears it and bumps our ACPanel attribute
if TextChatService.ChatVersion == Enum.ChatVersion.TextChatService then
	local cmd = Instance.new("TextChatCommand")
	cmd.Name = "JankAntiCheat"
	cmd.PrimaryAlias = "/ac"
	cmd.Parent = TextChatService
	cmd.Triggered:Connect(function() toggle() end)
end
me:GetAttributeChangedSignal("ACPanel"):Connect(toggle)
UserInputService.InputBegan:Connect(function(io: InputObject, gp: boolean)
	if not gp and io.KeyCode == Enum.KeyCode.F7 then toggle() end
end)

-- (the open list refreshes itself; a report being read doesn't)
task.spawn(function()
	while true do
		task.wait(3)
		if gui.Enabled and not (tab == "reports" and detail) then refresh() end
	end
end)
