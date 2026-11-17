--!strict
-- the owner's anti-cheat panel (server/AntiCheat.server.luau answers it, docs/ANTI-CHEAT.md): "/ac" in chat or F7.
-- who's in this server with how many points and their aim counts (kick, clear, ban when bans are on), and the review
-- log: every put back, kick, ban and aim flag, from every server. the server checks the owner on every call; anyone
-- else never gets this panel built at all
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")
local TextChatService = game:GetService("TextChatService")

local Theme = require(script.Parent:WaitForChild("Theme"))
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

-- ------------------------------------------------------------------ the panel
local gui = T.new("ScreenGui", { Name = "AntiCheatPanel", ResetOnSpawn = false, DisplayOrder = 60, IgnoreGuiInset = true, Enabled = false, ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, me:WaitForChild("PlayerGui"))
local root = T.scaled(gui)
local plate = T.plate(root, "Panel", UDim2.new(0.5, -380, 0.5, -240), UDim2.fromOffset(760, 480))
plate.BackgroundTransparency = 0.08

local title = T.text(plate, "Title", "ANTI-CHEAT", 18, T.TEXT, T.FONT_TITLE)
title.Position = UDim2.fromOffset(18, 12); title.Size = UDim2.fromOffset(300, 26)
local status = T.text(plate, "Status", "", 13, T.MUTED)
status.Position = UDim2.fromOffset(18, 38); status.Size = UDim2.fromOffset(560, 18)
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
local tabPlayers = button(plate, "TabPlayers", "PLAYERS", UDim2.fromOffset(18, 66), 100, true)
local tabLog = button(plate, "TabLog", "LOG", UDim2.fromOffset(126, 66), 100)
local note = T.text(plate, "Note", "", 13, T.SOFT, T.FONT, Enum.TextXAlignment.Right)
note.Position = UDim2.new(1, -420, 0, 70); note.Size = UDim2.fromOffset(400, 18)

local list = T.new("ScrollingFrame", {
	Name = "List", BackgroundColor3 = T.CARD, BackgroundTransparency = 0.2, BorderSizePixel = 0,
	Position = UDim2.fromOffset(18, 102), Size = UDim2.new(1, -36, 1, if hello.bans then -158 else -120),
	CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollBarThickness = 6, ScrollingDirection = Enum.ScrollingDirection.Y,
}, plate)
T.corner(list, 4)
T.new("UIListLayout", { Padding = UDim.new(0, 4), SortOrder = Enum.SortOrder.LayoutOrder }, list)
T.new("UIPadding", { PaddingTop = UDim.new(0, 6), PaddingLeft = UDim.new(0, 6), PaddingRight = UDim.new(0, 10), PaddingBottom = UDim.new(0, 6) }, list)

-- unban by user id (only with bans on)
if hello.bans then
	local box = T.new("TextBox", {
		Name = "UserId", PlaceholderText = "user id", Text = "", FontFace = T.FONT, TextSize = 13, TextColor3 = T.TEXT,
		PlaceholderColor3 = T.DIM, BackgroundColor3 = T.CARD_HI, BorderSizePixel = 0, ClearTextOnFocus = false,
		Position = UDim2.new(0, 18, 1, -44), Size = UDim2.fromOffset(180, 26),
	}, plate)
	T.corner(box, 4)
	local unban = button(plate, "Unban", "UNBAN", UDim2.new(0, 206, 1, -44), 90)
	unban.Activated:Connect(function()
		local id = tonumber(box.Text)
		if not id then note.Text = "type a user id"; return end
		local r = call("unban", id)
		note.Text = if type(r) == "table" and r.ok then "unbanned " .. id else ("unban: " .. tostring(type(r) == "table" and r.why or "no answer"))
	end)
end

local tab = "players"
local function clear()
	for _, c in list:GetChildren() do if c:IsA("Frame") then c:Destroy() end end
end

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

local refresh: () -> ()
local function playerRows(rows: { any })
	clear()
	for i, r in rows do
		local row = T.new("Frame", { Name = "Row", LayoutOrder = i, BackgroundColor3 = T.CARD_HI, BackgroundTransparency = 0.4, BorderSizePixel = 0, Size = UDim2.new(1, 0, 0, 52) }, list)
		T.corner(row, 4)
		local name = T.text(row, "Name", ("%s  @%s"):format(tostring(r.display), tostring(r.name)), 14, T.TEXT, T.FONT_BOLD)
		name.Position = UDim2.fromOffset(10, 5); name.Size = UDim2.fromOffset(300, 18)
		local pts = T.text(row, "Points", ("%d points"):format(tonumber(r.points) or 0), 13, if (tonumber(r.points) or 0) > 0 then T.ACCENT else T.MUTED, T.FONT_BOLD)
		pts.Position = UDim2.fromOffset(320, 5); pts.Size = UDim2.fromOffset(100, 18)
		local aim = T.text(row, "Aim", ("hits %d · head %d · snap %d · smoke %d"):format(r.hits or 0, r.heads or 0, r.snaps or 0, r.smoke or 0), 12, T.MUTED)
		aim.Position = UDim2.fromOffset(10, 27); aim.Size = UDim2.fromOffset(300, 16)
		local last = T.text(row, "Last", tostring(r.last or ""), 12, T.SOFT)
		last.Position = UDim2.fromOffset(320, 27); last.Size = UDim2.fromOffset(250, 16)
		last.TextTruncate = Enum.TextTruncate.AtEnd
		if r.uid ~= me.UserId then
			local x = 1
			local function act(label: string, w: number, fn: () -> ())
				local b = button(row, label, label, UDim2.new(1, -(x + w), 0, 13), w)
				x += w + 6
				twice(b, label, fn)
			end
			if hello.bans then
				act("BAN", 56, function()
					local res = call("ban", r.uid, nil, "cheating")
					note.Text = if type(res) == "table" and res.ok then "banned " .. tostring(r.name) else ("ban: " .. tostring(type(res) == "table" and res.why or "no answer"))
					refresh()
				end)
			end
			act("KICK", 60, function()
				local res = call("kick", r.uid, "")
				note.Text = if type(res) == "table" and res.ok then ("kicked %s%s"):format(tostring(r.name), if res.why then " (" .. res.why .. ")" else "") else ("kick: " .. tostring(type(res) == "table" and res.why or "no answer"))
				refresh()
			end)
			act("CLEAR", 64, function()
				local res = call("clear", r.uid)
				note.Text = if type(res) == "table" and res.ok then "cleared " .. tostring(r.name) else "clear: no answer"
				refresh()
			end)
		end
	end
end

local function hhmm(t: number): string
	return os.date("%d %b %H:%M", t) :: string
end
local function logRows(rows: { any })
	clear()
	if #rows == 0 then
		local row = T.new("Frame", { Name = "Row", BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 24) }, list)
		local l = T.text(row, "Empty", "Nothing caught yet.", 13, T.MUTED)
		l.Size = UDim2.fromScale(1, 1)
		return
	end
	for i, e in rows do
		local row = T.new("Frame", { Name = "Row", LayoutOrder = i, BackgroundColor3 = T.CARD_HI, BackgroundTransparency = if i % 2 == 0 then 0.6 else 0.8, BorderSizePixel = 0, Size = UDim2.new(1, 0, 0, 22) }, list)
		local soft = e.act == "flag"
		local function cell(name: string, text: string, x: number, w: number, color: Color3, font: Font?)
			local c = T.text(row, name, text, 12, color, font)
			c.Position = UDim2.fromOffset(x, 2); c.Size = UDim2.fromOffset(w, 18)
			c.TextTruncate = Enum.TextTruncate.AtEnd
		end
		cell("Time", hhmm(tonumber(e.t) or 0), 6, 92, T.MUTED)
		cell("Name", tostring(e.name), 100, 120, T.TEXT, T.FONT_BOLD)
		cell("Kind", tostring(e.kind), 222, 60, if soft then T.SOFT else T.ACCENT, T.FONT_BOLD)
		cell("Act", tostring(e.act) .. (if (tonumber(e.n) or 1) > 1 then (" x%d"):format(e.n) else ""), 284, 92, if e.act == "kick" or e.act == "ban" then T.DANGER else T.SOFT)
		cell("Info", tostring(e.info), 378, 330, T.SOFT)
	end
end

refresh = function()
	if not gui.Enabled then return end
	if tab == "players" then
		local rows = call("players")
		if type(rows) == "table" then playerRows(rows) end
	else
		local rows = call("log")
		if type(rows) == "table" then logRows(rows) end
	end
end

local function setTab(t: string)
	tab = t
	tabPlayers.BackgroundColor3 = if t == "players" then T.ACCENT else T.CARD_HI
	tabPlayers.TextColor3 = if t == "players" then T.INK else T.TEXT
	tabLog.BackgroundColor3 = if t == "log" then T.ACCENT else T.CARD_HI
	tabLog.TextColor3 = if t == "log" then T.INK else T.TEXT
	refresh()
end
tabPlayers.Activated:Connect(function() setTab("players") end)
tabLog.Activated:Connect(function() setTab("log") end)

local function toggle()
	gui.Enabled = not gui.Enabled
	if gui.Enabled then refresh() end
end
close.Activated:Connect(function() gui.Enabled = false end)

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

task.spawn(function()
	while true do
		task.wait(3)
		if gui.Enabled then refresh() end
	end
end)
