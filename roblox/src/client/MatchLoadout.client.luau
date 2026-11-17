--!strict
-- changing your loadout in a match (17 Nov 2026, the owner: "allow us to change weapons before first round and
-- between rounds"). a round-based match (duels and team duels, ranked too; never a classic mode, which keeps its own
-- weapons) opens a loadout window: the countdown before each round and the break between rounds. the SERVER decides
-- it: Matches sets the player attribute LoadoutWindow (the server time it shuts) and clears it the moment the round
-- goes live, and Loadout.luau only takes a pick in a match while it is set.
-- while it's open: "CHANGE LOADOUT [L] · 5" sits over the weapon bar (a button to tap on a phone), and L (the
-- loadout key, Binds) opens this small picker: a row a slot (PRIMARY, SECONDARY, MELEE, UTILITY), < WEAPON > through
-- the slot's live weapons. a pick goes to the server's Loadout remote like the big screen's ("pick"), which checks it
-- the same way. alive (the countdown), it's in your hands at once; dead (the break), you spawn with it next round.
-- the window shutting closes the picker. the full loadout screen (LoadoutUI, the shop session's) stays the hub's.
-- test hook: the LocalPlayer attribute MatchLoadoutTest = "open" | "close" | "pick:slot:weapon" ("pick" answers on
-- MatchLoadoutResult), "fake:844x390" (laid out as on a screen that size)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Roster = require(Shared:WaitForChild("Roster"))
local T = require(script.Parent:WaitForChild("Theme"))
local Binds = require(script.Parent:WaitForChild("Binds")) :: any
local MenuCursor = require(script.Parent:WaitForChild("MenuCursor")) :: any
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Loadout") :: RemoteFunction

local me = Players.LocalPlayer
local new, text = T.new, T.text

local open = false
local fake: Vector2? = nil
local busy = false

local function windowLeft(): number?
	local w = me:GetAttribute("LoadoutWindow")
	if type(w) ~= "number" then return nil end
	return math.max(0, w - workspace:GetServerTimeNow())
end
local function picks(): { string }
	local s = me:GetAttribute("LoadoutNext")
	return if type(s) == "string" then string.split(s, ",") else {}
end
local function choices(slot: string): { any }
	local out = {}
	for _, e in Roster.list do if e.slot == slot and e.live then table.insert(out, e) end end
	return out
end
local function touch(): boolean
	return (UIS.TouchEnabled and not UIS.KeyboardEnabled) or game:GetService("StarterPlayer"):GetAttribute("TouchForce") == true or fake ~= nil
end

local gui = new("ScreenGui", { Name = "JankMatchLoadout", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 18, Enabled = true },
	me:WaitForChild("PlayerGui"))
local scaled = T.scaled(gui)

-- the hint over the weapon bar: CHANGE LOADOUT [L] · 5 (a button on a phone)
local hint = new("TextButton", { Name = "Hint", AutoButtonColor = false, BorderSizePixel = 0, Text = "", AnchorPoint = Vector2.new(0.5, 1),
	Position = UDim2.new(0.5, 0, 1, -164), Size = UDim2.fromOffset(250, 38), BackgroundColor3 = T.BG, BackgroundTransparency = 0.12, Visible = false }, scaled)
T.corner(hint, 5)
local hs = T.edge(hint, T.ACCENT, 0.45, 1)
local hintText = text(hint, "Label", "CHANGE LOADOUT", 14, T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Left)
hintText.Position = UDim2.fromOffset(44, 0); hintText.Size = UDim2.new(1, -96, 1, 0)
local hintKey = T.key(hint, "L", UDim2.fromOffset(12, 8))
local hintClock = text(hint, "Clock", "", 14, T.ACCENT, T.FONT_HEAVY, Enum.TextXAlignment.Right)
hintClock.AnchorPoint = Vector2.new(1, 0); hintClock.Position = UDim2.new(1, -14, 0, 0); hintClock.Size = UDim2.new(0, 40, 1, 0)
_ = hs

-- the picker
local panel = T.plate(scaled, "Picker", UDim2.new(0.5, 0, 0.5, 0), UDim2.fromOffset(440, 330))
panel.AnchorPoint = Vector2.new(0.5, 0.5)
panel.Visible = false
do
	local s = panel:FindFirstChildOfClass("UIStroke")
	if s then s.Color = T.ACCENT; s.Transparency = 0.5 end
end
local title = text(panel, "Title", "LOADOUT", 18, T.TEXT, T.FONT_HEAVY)
local clock = text(panel, "Clock", "", 13, T.ACCENT, T.FONT_HEAVY, Enum.TextXAlignment.Right)
local foot = text(panel, "Foot", "", 11, T.MUTED, T.FONT_BOLD)
local closeB = new("TextButton", { Name = "Close", AutoButtonColor = false, BorderSizePixel = 0, Text = "DONE", BackgroundColor3 = T.CARD,
	FontFace = T.FONT_HEAVY, TextSize = 13, TextColor3 = T.TEXT }, panel)
T.corner(closeB, 4)
local rows: { Frame } = {}
local note: string? = nil

local function ask(slot: string, wid: string)
	if busy then return end
	busy = true
	task.spawn(function()
		local ok, r = pcall(function() return Remote:InvokeServer("pick", slot, wid) end)
		busy = false
		if not ok or type(r) ~= "table" then note = "no answer, try again"
		elseif not r.ok then note = if type(r.why) == "string" then r.why else "refused"
		else note = nil end
		me:SetAttribute("MatchLoadoutResult", if ok and type(r) == "table" then (if r.ok then "ok" else tostring(r.why)) else "error")
	end)
end

local function draw()
	for _, r in rows do r:Destroy() end
	table.clear(rows)
	if not open then panel.Visible = false; return end
	local cam = workspace.CurrentCamera
	local sz = fake or (if cam then cam.ViewportSize / T.scaleNow() else Vector2.new(1280, 720))
	local c = sz.Y < 560 or sz.X < 960
	local W = if c then 400 else 440
	local rowH, gap, pad = if c then 50 else 56, 6, 16
	local top = if c then 44 else 52
	local H = top + #Roster.SLOTS * (rowH + gap) - gap + 12 + (if c then 46 else 50)
	panel.Size = UDim2.fromOffset(W, H)
	panel.Position = if c then UDim2.new(0.5, 0, 0.5, -10) else UDim2.new(0.5, 0, 0.5, 0)
	title.Position = UDim2.fromOffset(pad, if c then 10 else 14); title.Size = UDim2.fromOffset(W - pad * 2 - 90, 22)
	clock.AnchorPoint = Vector2.new(1, 0); clock.Position = UDim2.new(1, -pad, 0, if c then 13 else 17); clock.Size = UDim2.fromOffset(110, 16)
	local cur = picks()
	for i, slot in Roster.SLOTS do
		local list = choices(slot)
		local wid = cur[i]
		local idx = 1
		for j, e in list do if e.id == wid then idx = j end end
		local e = list[idx]
		local row = new("Frame", { Name = "Row" .. i, BorderSizePixel = 0, BackgroundColor3 = T.CARD, BackgroundTransparency = 0.15,
			Position = UDim2.fromOffset(pad, top + (i - 1) * (rowH + gap)), Size = UDim2.fromOffset(W - pad * 2, rowH) }, panel)
		T.corner(row, 5)
		local lab = text(row, "Slot", Roster.SLOT_NAMES[slot] or slot, 10, T.MUTED, T.FONT_BOLD)
		lab.Position = UDim2.fromOffset(12, if c then 6 else 8); lab.Size = UDim2.fromOffset(120, 12)
		local dot = new("Frame", { Name = "Dot", BorderSizePixel = 0, BackgroundColor3 = if e and typeof(e.color) == "Color3" then e.color else T.TEXT,
			Position = UDim2.fromOffset(12, if c then 26 else 30), Size = UDim2.fromOffset(8, 8) }, row)
		T.corner(dot, 4)
		local nm = text(row, "Name", if e then string.upper(e.name) else "-", if c then 14 else 16, T.TEXT, T.FONT_HEAVY)
		nm.Position = UDim2.fromOffset(26, if c then 19 else 22); nm.Size = UDim2.new(1, -150, 0, if c then 20 else 22)
		nm.TextScaled = true
		new("UITextSizeConstraint", { MaxTextSize = if c then 14 else 16, MinTextSize = 8 }, nm)
		local aw = if c then 52 else 46
		local function arrow(name: string, glyph: string, x: number, step: number)
			local b = new("TextButton", { Name = name, AutoButtonColor = false, BorderSizePixel = 0, Text = glyph, BackgroundColor3 = T.BG,
				BackgroundTransparency = 0.05, AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.new(1, x, 0.5, 0), Size = UDim2.fromOffset(aw, rowH - 10),
				FontFace = T.FONT_HEAVY, TextSize = 16, TextColor3 = if #list > 1 then T.TEXT else T.DIM }, row)
			T.corner(b, 4)
			b.Activated:Connect(function()
				if #list < 2 then return end
				ask(slot, list[(idx - 1 + step) % #list + 1].id)
			end)
		end
		arrow("Prev", "<", -(aw * 2 + 12), -1)
		arrow("Next", ">", -(aw + 6), 1)
		table.insert(rows, row)
	end
	local fy = top + #Roster.SLOTS * (rowH + gap) - gap + 12
	foot.Position = UDim2.fromOffset(pad, fy); foot.Size = UDim2.fromOffset(W - pad * 2 - 110, if c then 34 else 38)
	foot.TextWrapped = true; foot.TextYAlignment = Enum.TextYAlignment.Center
	local hum = me.Character and me.Character:FindFirstChildOfClass("Humanoid")
	local alive = hum ~= nil and hum.Health > 0
	foot.Text = note or (if alive then "picks go in your hands now" else "you spawn with your picks next round")
	foot.TextColor3 = if note then T.ACCENT else T.MUTED
	closeB.AnchorPoint = Vector2.new(1, 0); closeB.Position = UDim2.new(1, -pad, 0, fy); closeB.Size = UDim2.fromOffset(if c then 100 else 96, if c then 34 else 38)
	panel.Visible = true
end

local function setOpen(v: boolean)
	if v and not windowLeft() then return end
	if v == open then return end
	open = v
	note = nil
	MenuCursor.set("matchloadout", v, function() return open end)
	draw()
end
closeB.Activated:Connect(function() setOpen(false) end)
hint.Activated:Connect(function() setOpen(true) end)

UIS.InputBegan:Connect(function(io: InputObject, gp: boolean)
	if UIS:GetFocusedTextBox() then return end
	if Binds.is("loadout", io) then
		if not windowLeft() then return end
		if gp and not open then return end
		setOpen(not open)
	elseif open and not gp and io.KeyCode == Enum.KeyCode.Escape then
		setOpen(false)
	end
end)
me:GetAttributeChangedSignal("LoadoutNext"):Connect(function() if open then draw() end end)
me:GetAttributeChangedSignal("LoadoutWindow"):Connect(function()
	if not windowLeft() and open then setOpen(false) end
end)
me.CharacterAdded:Connect(function() if open then task.defer(draw) end end)

RunService.Heartbeat:Connect(function()
	local left = windowLeft()
	local show = left ~= nil and not open
	if hint.Visible ~= show then hint.Visible = show end
	if left then
		local s = tostring(math.ceil(left))
		if hintClock.Text ~= s then hintClock.Text = s end
		local ct = "LIVE IN " .. s
		if clock.Text ~= ct then clock.Text = ct end
	end
	local t = touch()
	if hintKey.Visible == t then hintKey.Visible = not t end
	hintText.Position = UDim2.fromOffset(if t then 16 else 44, 0)
	if open and not left then setOpen(false) end
end)

-- ------------------------------------------------------------------ test hook
me:GetAttributeChangedSignal("MatchLoadoutTest"):Connect(function()
	local v = me:GetAttribute("MatchLoadoutTest")
	if type(v) ~= "string" or v == "" then return end
	me:SetAttribute("MatchLoadoutTest", nil)
	local cmd, a, b = string.match(v, "^(%a+):?([^:]*):?(.*)$")
	if cmd == "open" then setOpen(true); me:SetAttribute("MatchLoadoutResult", if open then "open" else "shut")
	elseif cmd == "close" then setOpen(false)
	elseif cmd == "pick" then ask(a or "", b or "")
	elseif cmd == "fake" then
		local w, h = string.match(a or "", "^(%d+)x(%d+)$")
		fake = if w then Vector2.new(tonumber(w) :: number, tonumber(h) :: number) else nil
		draw()
	end
end)
