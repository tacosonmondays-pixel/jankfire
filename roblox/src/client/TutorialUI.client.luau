--!strict
-- THE WEAPON TUTORIAL ROOMS on this screen (20 Nov 2026; server/Tutorials.server.luau runs them, shared/TutorialData
-- holds one entry per weapon):
--   * the MENU (the room's console, E): every live weapon by the Roster's slots, and the MOVES tab. A pick tells the
--     server (the room rebuilds as that weapon's course) and asks the Loadout remote for the weapon, as the loadout
--     screen does (training's try layer: anything, never saved), then takes it out (its slot's key)
--   * the PANEL (left of the screen while you're in a room): the weapon, its move names with YOUR keys for them, the
--     goal and how far you are, then the time and your best this visit
--   * every room's COURSE is dressed as a hologram on this screen, with the build-in sweep, as it arrives (Hologram)
--   * a room that is someone else's: its mouth is solid for you (DoorBlock)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UIS = game:GetService("UserInputService")

local me = Players.LocalPlayer
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local TD = require(Shared:WaitForChild("TutorialData")) :: any
local Roster = require(Shared:WaitForChild("Roster")) :: any
local Holo = require(Shared:WaitForChild("Hologram")) :: any
local T = require(script.Parent:WaitForChild("Theme")) :: any
local MenuCursor = require(script.Parent:WaitForChild("MenuCursor")) :: any
local Binds = require(script.Parent:WaitForChild("Binds")) :: any
local Keys = require(script.Parent:WaitForChild("Keys")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local R = Remotes:WaitForChild("Tutorial", 60) :: RemoteEvent?
local LoadoutR = Remotes:WaitForChild("Loadout") :: RemoteFunction
if not R then return end

local new = T.new
local TEAL = Color3.fromRGB(143, 216, 207) -- (the wing's one accent)

-- ------------------------------------------------------------------ words: "@fire" -> your key for it
local function keysIn(s: string): string
	local out = string.gsub(s, "@([%w]+)", function(id: string)
		local ok, l = pcall(Binds.label, id)
		return if ok and type(l) == "string" and l ~= "" then string.upper(l) else string.upper(id)
	end)
	local ok, said = pcall(Keys.say, out)
	return if ok and type(said) == "string" then said else out
end

-- ------------------------------------------------------------------ the panel
local gui = new("ScreenGui", { Name = "TutorialHud", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 4, Enabled = false }, me:WaitForChild("PlayerGui"))
local sc = T.scaled(gui)
local panel = T.plate(sc, "Panel", UDim2.new(0, 16, 0.3, 0), UDim2.fromOffset(250, 60))
panel.AutomaticSize = Enum.AutomaticSize.Y
new("UIPadding", { PaddingLeft = UDim.new(0, 12), PaddingRight = UDim.new(0, 12), PaddingTop = UDim.new(0, 10), PaddingBottom = UDim.new(0, 10) }, panel)
new("UIListLayout", { Padding = UDim.new(0, 4), SortOrder = Enum.SortOrder.LayoutOrder }, panel)
local function line(name: string, order: number, size: number, color: Color3?, font: Font?): TextLabel
	local l = T.text(panel, name, "", size, color, font)
	l.LayoutOrder = order
	l.Size = UDim2.new(1, 0, 0, size + 4)
	l.TextWrapped = true
	l.AutomaticSize = Enum.AutomaticSize.Y
	return l
end
local head = line("Head", 1, 13, T.MUTED, T.FONT_BOLD)
local title = line("Title", 2, 22, T.TEXT, T.FONT_TITLE)
local movesBox = new("Frame", { Name = "Moves", BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 0), AutomaticSize = Enum.AutomaticSize.Y, LayoutOrder = 3 }, panel)
new("UIListLayout", { Padding = UDim.new(0, 2), SortOrder = Enum.SortOrder.LayoutOrder }, movesBox)
local goalL = line("Goal", 4, 15, TEAL, T.FONT_BOLD)
local resultL = line("Result", 5, 15, T.ACCENT, T.FONT_BOLD)

local cur: any = nil -- the course on screen: { wid, name, moves, goal, best }
local function setMoves(moves: { { string } })
	for _, c in movesBox:GetChildren() do if c:IsA("Frame") then c:Destroy() end end
	for i, mv in moves do
		local row = new("Frame", { Name = "Move" .. i, BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 20), LayoutOrder = i }, movesBox)
		local a = T.text(row, "Name", mv[1], 15, T.TEXT, T.FONT_HEAVY)
		a.Size = UDim2.new(0.5, 0, 1, 0)
		local b = T.text(row, "Key", keysIn(mv[2] or ""), 13, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Right)
		b.Size = UDim2.new(0.5, 0, 1, 0); b.Position = UDim2.fromScale(0.5, 0)
		b.TextTruncate = Enum.TextTruncate.AtEnd
	end
end
local function showRoom(i: number, note: string)
	gui.Enabled = true
	head.Text = ("TUTORIAL · ROOM %d"):format(i)
	title.Text = note
	setMoves({})
	goalL.Text = ""
	resultL.Text = ""
end
local function showCourse(c: any)
	cur = c
	gui.Enabled = true
	head.Text = ("TUTORIAL · ROOM %d"):format(c.room)
	title.Text = c.name
	setMoves(c.moves or {})
	goalL.Text = TD.goalText(c.goal, {})
	resultL.Text = if c.best then ("BEST %.1f S"):format(c.best) else ""
end

-- ------------------------------------------------------------------ the menu
local mg = new("ScreenGui", { Name = "TutorialMenu", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 30, Enabled = false }, me:WaitForChild("PlayerGui"))
local msc = T.scaled(mg)
local menu = T.plate(msc, "Menu", UDim2.fromScale(0.5, 0.5), UDim2.fromOffset(700, 430))
menu.AnchorPoint = Vector2.new(0.5, 0.5)
menu.BackgroundTransparency = 0.08
local mt = T.text(menu, "Title", "PICK A WEAPON", 20, T.TEXT, T.FONT_TITLE)
mt.Position = UDim2.fromOffset(18, 14); mt.Size = UDim2.new(1, -80, 0, 26)
local closeB = new("TextButton", { Name = "Close", Text = "X", FontFace = T.FONT_HEAVY, TextSize = 16, TextColor3 = T.TEXT, BackgroundColor3 = T.CARD,
	AutoButtonColor = true, Position = UDim2.new(1, -46, 0, 12), Size = UDim2.fromOffset(32, 30) }, menu)
T.corner(closeB, 5)
local tabsF = new("Frame", { Name = "Tabs", BackgroundTransparency = 1, Position = UDim2.fromOffset(18, 50), Size = UDim2.new(1, -36, 0, 30) }, menu)
new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 6), SortOrder = Enum.SortOrder.LayoutOrder }, tabsF)
local grid = new("ScrollingFrame", { Name = "Grid", BackgroundTransparency = 1, BorderSizePixel = 0, Position = UDim2.fromOffset(18, 92), Size = UDim2.new(1, -36, 1, -108),
	CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollBarThickness = 4, ScrollingDirection = Enum.ScrollingDirection.Y }, menu)
new("UIGridLayout", { CellSize = UDim2.fromOffset(158, 44), CellPadding = UDim2.fromOffset(8, 8), SortOrder = Enum.SortOrder.LayoutOrder }, grid)

local open = false
local tab = "primary"
local tabBtns: { [string]: TextButton } = {}
local function closeMenu()
	open = false
	mg.Enabled = false
	MenuCursor.set("tutorial", false)
end

local function equip(wid: string)
	local e = Roster.byId[wid]
	if not e then return end
	task.spawn(function()
		local ok, res = pcall(function() return LoadoutR:InvokeServer("pick", e.slot, wid) end)
		if not ok or type(res) ~= "table" or res.ok ~= true then return end
		-- take it out: its slot's key, once the menu has let go of the keys
		local n = if e.slot == "primary" then 1 elseif e.slot == "secondary" then 2 elseif e.slot == "melee" then 3 else nil
		if not n then return end
		task.wait(0.7)
		local b = Binds.get("slot" .. n)
		local kc = b and (Enum.KeyCode :: any)[b[1]]
		if kc then pcall(Keys.tap, kc) end
	end)
end

local function pick(wid: string)
	closeMenu()
	R:FireServer("pick", wid)
	if string.sub(wid, 1, 5) ~= "move:" then equip(wid) end
end

local function fill()
	for _, c in grid:GetChildren() do if c:IsA("GuiButton") then c:Destroy() end end
	local list = {}
	if tab == "moves" then
		for _, m in TD.MOVES do table.insert(list, { id = m.id, name = m.name }) end
	else
		for _, e in Roster.list do
			if e.slot == tab and e.live and TD.W[e.id] then table.insert(list, { id = e.id, name = string.upper(e.name) }) end
		end
	end
	for i, it in list do
		local b = new("TextButton", { Name = it.id, Text = it.name, FontFace = T.FONT_BOLD, TextSize = 14, TextColor3 = T.TEXT, TextWrapped = true,
			BackgroundColor3 = T.CARD, AutoButtonColor = true, LayoutOrder = i }, grid)
		T.corner(b, 5)
		T.edge(b, nil, if cur and cur.wid == it.id then 0.2 else 0.85)
		b.MouseButton1Click:Connect(function() pick(it.id) end)
	end
	for id, tb in tabBtns do
		tb.BackgroundColor3 = if id == tab then TEAL else T.CARD
		tb.TextColor3 = if id == tab then T.INK else T.TEXT
	end
end
for i, t in TD.TABS do
	local tb = new("TextButton", { Name = t[1], Text = t[2], FontFace = T.FONT_HEAVY, TextSize = 13, BackgroundColor3 = T.CARD, TextColor3 = T.TEXT,
		AutoButtonColor = true, Size = UDim2.fromOffset(118, 30), LayoutOrder = i }, tabsF)
	T.corner(tb, 5)
	tabBtns[t[1]] = tb
	tb.MouseButton1Click:Connect(function() tab = t[1]; fill() end)
end
closeB.MouseButton1Click:Connect(closeMenu)
UIS.InputBegan:Connect(function(io: InputObject, _gp: boolean)
	if not open then return end
	if io.KeyCode == Enum.KeyCode.Escape or io.KeyCode == Enum.KeyCode.Backspace or io.KeyCode == Enum.KeyCode.ButtonB then closeMenu() end
end)
local function openMenu(curWid: string?)
	if curWid then
		local e = Roster.byId[curWid]
		tab = if string.sub(curWid, 1, 5) == "move:" then "moves" elseif e then e.slot else tab
	end
	open = true
	mg.Enabled = true
	fill()
	MenuCursor.set("tutorial", true, function() return open end)
end

-- ------------------------------------------------------------------ the server's words
R.OnClientEvent:Connect(function(op: string, d: any)
	if op == "claimed" then
		cur = nil
		showRoom(d.room, "USE THE CONSOLE")
	elseif op == "open" then
		openMenu(d.wid)
	elseif op == "course" then
		showCourse(d)
	elseif op == "prog" then
		if cur then goalL.Text = TD.goalText(cur.goal, d.got) end
	elseif op == "done" then
		if cur then goalL.Text = TD.goalText(cur.goal, d.got) end
		resultL.Text = if d.newBest then ("DONE  %.1f S  ·  BEST") :format(d.time) else ("DONE  %.1f S  ·  BEST %.1f S"):format(d.time, d.best)
	elseif op == "left" then
		cur = nil
		gui.Enabled = false
		if open then closeMenu() end
	end
end)

-- ------------------------------------------------------------------ the rooms in the world: courses as holograms, the mouths
local dressed: { [Instance]: boolean } = {}
local function dress(cm: Instance)
	if dressed[cm] or not cm:IsA("Model") then return end
	if not cm:GetAttribute("Ready") then
		cm:GetAttributeChangedSignal("Ready"):Once(function() dress(cm) end)
		return
	end
	dressed[cm] = true
	pcall(function() Holo.apply(cm, { build = 1.2, see = 0.35, glitch = false, flicker = 0.02 }) end)
	cm.AncestryChanged:Connect(function() if not cm.Parent then dressed[cm] = nil end end)
end
local function mouth(room: Instance)
	local db = room:FindFirstChild("DoorBlock") :: BasePart?
	if not db then return end
	local u = room:GetAttribute("User")
	db.CanCollide = type(u) == "number" and u ~= me.UserId
end
local wired: { [Instance]: boolean } = {}
local function wireRoom(room: Instance)
	if wired[room] then return end
	wired[room] = true
	room.ChildAdded:Connect(function(c: Instance) if c.Name == "Course" then dress(c) end end)
	local c = room:FindFirstChild("Course")
	if c then dress(c) end
	room:GetAttributeChangedSignal("User"):Connect(function() mouth(room) end)
	mouth(room)
end
task.spawn(function()
	while true do
		local hub = workspace:FindFirstChild("Map") and workspace.Map:FindFirstChild("Hub")
		local tg = hub and hub:FindFirstChild("TrainingGround")
		local tut = tg and tg:FindFirstChild("Tutorial")
		if tut then for _, room in tut:GetChildren() do if room:IsA("Folder") then wireRoom(room) end end end
		task.wait(3)
	end
end)

-- ------------------------------------------------------------------ the parkour clock (server/Parkour.server.luau)
task.spawn(function()
	local PkR = Remotes:WaitForChild("Parkour", 120) :: RemoteEvent?
	if not PkR then return end
	local RunService = game:GetService("RunService")
	local pg = new("ScreenGui", { Name = "ParkourHud", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 4, Enabled = false }, me:WaitForChild("PlayerGui"))
	local psc = T.scaled(pg)
	local plate = T.plate(psc, "Clock", UDim2.new(0.5, 0, 0, 64), UDim2.fromOffset(220, 60))
	plate.AnchorPoint = Vector2.new(0.5, 0)
	local big = T.text(plate, "Time", "0.0", 28, T.TEXT, T.FONT_TITLE, Enum.TextXAlignment.Center)
	big.Size = UDim2.new(1, 0, 0, 34); big.Position = UDim2.fromOffset(0, 4)
	local note = T.text(plate, "Note", "", 13, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center)
	note.Size = UDim2.new(1, 0, 0, 16); note.Position = UDim2.fromOffset(0, 39)
	local t0: number? = nil
	local best: number? = nil
	local function bestText(): string return if best then ("BEST %.1f S"):format(best) else "OFF THE DECK TO START" end
	RunService.RenderStepped:Connect(function()
		if t0 then big.Text = ("%.1f"):format(os.clock() - t0) end
	end)
	PkR.OnClientEvent:Connect(function(op: string, d: any)
		d = d or {}
		if op == "on" or op == "ready" then
			pg.Enabled = true
			t0 = nil
			best = d.best or best
			big.Text = "0.0"
			big.TextColor3 = T.TEXT
			note.Text = bestText()
		elseif op == "go" then
			t0 = os.clock()
			big.TextColor3 = T.TEXT
			note.Text = bestText()
		elseif op == "cp" then
			note.Text = ("CHECKPOINT %d/%d  ·  %.1f S"):format(d.n, d.of, d.split)
		elseif op == "done" then
			t0 = nil
			best = d.best
			big.Text = ("%.1f"):format(d.time)
			big.TextColor3 = TEAL
			note.Text = if d.newBest then "DONE  ·  YOUR BEST" else ("DONE  ·  BEST %.1f S"):format(d.best)
		elseif op == "off" then
			t0 = nil
			pg.Enabled = false
		end
	end)
end)
