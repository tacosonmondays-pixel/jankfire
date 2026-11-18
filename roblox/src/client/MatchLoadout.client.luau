--!strict
-- the match loadout (17 Nov 2026, the owner: "allow us to change weapons before first round and between rounds", then
-- "can you have renders when selecting loadout"). a round-based match (duels and team duels, ranked too; never a
-- classic mode, which keeps its own weapons) opens a loadout window: the countdown before each round (8 s before round
-- 1) and the break between rounds (6 s). the SERVER decides it: Matches sets the player attribute LoadoutWindow (the
-- server time it shuts) and clears it the moment the round goes live, and Loadout.luau only takes a pick in a match
-- while it is set. a pick goes to the Loadout remote ("pick"), like the hub screen's: alive (a countdown) it's in your
-- hands at once, dead (the break) you spawn with it next round.
-- while the window is open, without taking the mouse:
--   a strip of your four slots, each a live picture of the weapon wearing your own skin, hat and wrap (GunPreview),
--   under a header with the seconds left in big numbers and a bar that runs down with them.
-- L (the loadout key) takes the mouse (MenuCursor "matchloadout": the arrow free, clicks don't fire, you still move)
-- and opens the slot's picker on PRIMARY: every live weapon for that slot, each a picture in your looks, the one you
-- have marked. one click picks it; the picker stays open for the next slot (click a slot, or 1 2 3 4). L, Esc or DONE
-- closes it, and the window shutting closes it too. on a phone the slots are tapped straight away.
-- desktop: the strip sits low in the middle, the picker over it. phone (or a small screen): the strip sits at the top
-- under the score, the picker under it, clear of the stick and the fire buttons.
-- test hook: the LocalPlayer attribute MatchLoadoutTest = "open" | "slot:<slot>" | "close" | "pick:<slot>:<weapon>"
-- ("pick" answers on MatchLoadoutResult), "fake:844x390" (laid out in a box that size, as on that screen) | "real"
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Roster = require(Shared:WaitForChild("Roster")) :: any
local T = require(script.Parent:WaitForChild("Theme")) :: any
local Binds = require(script.Parent:WaitForChild("Binds")) :: any
local Keys = require(script.Parent:WaitForChild("Keys")) :: any
local MenuCursor = require(script.Parent:WaitForChild("MenuCursor")) :: any
local GunPreview = require(script.Parent:WaitForChild("GunPreview")) :: any
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Loadout") :: RemoteFunction

local me = Players.LocalPlayer
local new, text = T.new, T.text

local S = {
	tray = nil :: string?, -- the slot whose picker is open (the mouse is out while it is)
	fake = nil :: Vector2?,
	asking = nil :: string?, -- the weapon a pick is out for
	note = nil :: string?,
	total = 0, -- how long the window was when it opened (the bar)
	shown = false,
	small = nil :: boolean?, -- the layout drawn: phone-sized or not
	hover = nil :: string?,
}

-- (the window is shut the moment any of these says so, whichever comes first: the server's shut time passing on this
-- client's clock, the attribute cleared, RoundEnds set (the round is live). owner, 18 Nov: "your choose loudout stays on
-- screen until you move after the countdown")
local function windowLeft(): number?
	local w = me:GetAttribute("LoadoutWindow")
	if type(w) ~= "number" or me:GetAttribute("RoundEnds") ~= nil then return nil end
	local left = w - workspace:GetServerTimeNow()
	return if left > 0 then left else nil
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
	return (UIS.TouchEnabled and not UIS.KeyboardEnabled) or game:GetService("StarterPlayer"):GetAttribute("TouchForce") == true
		or me:GetAttribute("TouchForce") == true or S.fake ~= nil
end
local function small(): boolean
	if touch() then return true end
	local cam = workspace.CurrentCamera
	local sz = if cam then cam.ViewportSize / T.scaleNow() else Vector2.new(1280, 720)
	return sz.Y < 560 or sz.X < 900
end

-- ---------------------------------------------------------------- the screen
local gui = new("ScreenGui", { Name = "JankMatchLoadout", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 18,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, me:WaitForChild("PlayerGui"))
local scaled = T.scaled(gui)
-- (everything sits in root: the whole screen, or a phone-sized box in its middle for a fake-screen test)
local root = new("Frame", { Name = "Root", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
	Size = UDim2.fromScale(1, 1), Visible = false }, scaled)

-- the strip: a header (LOADOUT, the key, the seconds and a bar) over the four slots
local strip = new("Frame", { Name = "Strip", BackgroundTransparency = 1 }, root)
local head = T.plate(strip, "Head", UDim2.fromOffset(0, 0), UDim2.fromOffset(100, 34))
local title = text(head, "Title", "LOADOUT", 13, T.TEXT, T.FONT_HEAVY)
local cap = T.key(head, "L", UDim2.fromOffset(0, 6))
local secs = text(head, "Secs", "", 22, T.ACCENT, T.FONT_HEAVY, Enum.TextXAlignment.Right)
local sub = text(head, "Sub", "", 11, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Right)
local track = new("Frame", { Name = "Track", BorderSizePixel = 0, BackgroundColor3 = T.TRACK or T.CARD_HI, AnchorPoint = Vector2.new(0, 1) }, head)
local fill = new("Frame", { Name = "Fill", BorderSizePixel = 0, BackgroundColor3 = T.ACCENT, Size = UDim2.fromScale(1, 1) }, track)

type Tile = { slot: string, btn: TextButton, st: UIStroke, lab: TextLabel, name: TextLabel, vp: ViewportFrame, cam: Camera }
local tiles: { Tile } = {}
local setTray: (string?) -> ()
for i, slot in Roster.SLOTS do
	local btn = new("TextButton", { Name = "Slot" .. i, Text = "", AutoButtonColor = false, BorderSizePixel = 0, BackgroundColor3 = T.BG,
		BackgroundTransparency = T.BG_A }, strip)
	T.corner(btn, 6)
	local st = T.edge(btn)
	local lab = text(btn, "Slot", Roster.SLOT_NAMES[slot] or slot, 10, T.MUTED, T.FONT_BOLD)
	local vp, cam = GunPreview.viewport(btn, { Name = "Picture", BackgroundColor3 = T.CARD_HI, BackgroundTransparency = 0.55 })
	T.corner(vp, 4)
	local name = text(btn, "Name", "", 13, T.TEXT, T.FONT_HEAVY)
	name.TextScaled = true
	new("UITextSizeConstraint", { MaxTextSize = 13, MinTextSize = 8 }, name)
	btn.Activated:Connect(function() setTray(if S.tray == slot then nil else slot) end)
	table.insert(tiles, { slot = slot, btn = btn, st = st, lab = lab, name = name, vp = vp, cam = cam })
end

-- the picker: the slot's weapons in a grid, a line and DONE under it
local tray = T.plate(root, "Picker", UDim2.fromOffset(0, 0), UDim2.fromOffset(100, 100))
tray.Visible = false
local grid = new("Frame", { Name = "Grid", BackgroundTransparency = 1 }, tray)
local gridLayout = new("UIGridLayout", { SortOrder = Enum.SortOrder.LayoutOrder, CellPadding = UDim2.fromOffset(6, 6) }, grid)
local foot = text(tray, "Foot", "", 11, T.MUTED, T.FONT_BOLD)
foot.TextWrapped = true
local done = new("TextButton", { Name = "Done", AutoButtonColor = false, BorderSizePixel = 0, Text = "DONE", BackgroundColor3 = T.CARD,
	FontFace = T.FONT_HEAVY, TextSize = 12, TextColor3 = T.TEXT }, tray)
T.corner(done, 4)
done.Activated:Connect(function() setTray(nil) end)

type Card = { id: string, btn: TextButton, st: UIStroke, vp: ViewportFrame, cam: Camera }
local cards: { Card } = {}
local cardsFor = ""

-- ---------------------------------------------------------------- sizes
local G = { tw = 138, th = 108, gap = 8, hh = 34, cw = 96, ch = 82, cols = 7 }
local function layout()
	local sm = small()
	S.small = sm
	if S.fake then
		root.Size = UDim2.fromOffset(S.fake.X, S.fake.Y)
	else
		root.Size = UDim2.fromScale(1, 1)
	end
	if sm then
		G.tw, G.th, G.gap, G.hh, G.cw, G.ch, G.cols = 96, 76, 6, 28, 66, 56, 7
	else
		G.tw, G.th, G.gap, G.hh, G.cw, G.ch, G.cols = 138, 108, 8, 34, 96, 82, 7
	end
	local w = #tiles * G.tw + (#tiles - 1) * G.gap
	local h = G.hh + 6 + G.th
	strip.Size = UDim2.fromOffset(w, h)
	if sm then
		strip.AnchorPoint = Vector2.new(0.5, 0); strip.Position = UDim2.new(0.5, 0, 0, 62)
	else
		strip.AnchorPoint = Vector2.new(0.5, 1); strip.Position = UDim2.new(0.5, 0, 1, -100)
	end
	head.Size = UDim2.fromOffset(w, G.hh)
	local t = touch()
	cap.Visible = not t
	cap.Position = UDim2.fromOffset(10, math.floor((G.hh - 22) / 2) - 1)
	title.Position = UDim2.fromOffset(if t then 12 else 40, 0); title.Size = UDim2.new(0, 120, 1, -3)
	secs.AnchorPoint = Vector2.new(1, 0); secs.Position = UDim2.new(1, -12, 0, 0); secs.Size = UDim2.new(0, 44, 1, -3)
	secs.TextSize = if sm then 18 else 22
	sub.AnchorPoint = Vector2.new(1, 0); sub.Position = UDim2.new(1, -60, 0, 0); sub.Size = UDim2.new(0, 220, 1, -3)
	track.Position = UDim2.new(0, 10, 1, -4); track.Size = UDim2.new(1, -20, 0, 2)
	for i, tl in tiles do
		tl.btn.Position = UDim2.fromOffset((i - 1) * (G.tw + G.gap), G.hh + 6)
		tl.btn.Size = UDim2.fromOffset(G.tw, G.th)
		local pad = if sm then 6 else 8
		tl.lab.Position = UDim2.fromOffset(pad + 2, pad - 2); tl.lab.Size = UDim2.fromOffset(G.tw - pad * 2, 12)
		tl.lab.TextSize = if sm then 9 else 10
		local nh = if sm then 14 else 18
		tl.vp.Position = UDim2.fromOffset(pad, pad + 12); tl.vp.Size = UDim2.fromOffset(G.tw - pad * 2, G.th - pad * 2 - 12 - nh)
		tl.name.Position = UDim2.fromOffset(pad + 2, G.th - pad - nh); tl.name.Size = UDim2.fromOffset(G.tw - pad * 2 - 4, nh)
		local c = tl.name:FindFirstChildOfClass("UITextSizeConstraint")
		if c then c.MaxTextSize = if sm then 11 else 13 end
	end
	gridLayout.CellSize = UDim2.fromOffset(G.cw, G.ch)
end

-- ---------------------------------------------------------------- drawing
local function slotOf(i: number): string return Roster.SLOTS[i] end
local function current(slot: string): string?
	local i = table.find(Roster.SLOTS, slot)
	return if i then picks()[i] else nil
end
local function alive(): boolean
	local hum = me.Character and me.Character:FindFirstChildOfClass("Humanoid")
	return hum ~= nil and hum.Health > 0
end

local function drawTiles()
	local cur = picks()
	for i, tl in tiles do
		local wid = cur[i]
		local e = wid and Roster.byId[wid]
		tl.name.Text = if e then string.upper(e.name) else "-"
		if wid and e then task.defer(GunPreview.put, tl.vp, tl.cam, wid) end
		local on = S.tray == tl.slot
		tl.st.Color = if on then T.ACCENT else Color3.new(1, 1, 1)
		tl.st.Transparency = if on then 0.25 else 0.88
		tl.btn.BackgroundColor3 = if on then T.CARD else T.BG
	end
end

local ask: (string, string) -> ()
local function drawTray()
	local slot = S.tray
	if not slot then tray.Visible = false; return end
	local list = choices(slot)
	if cardsFor ~= slot then
		cardsFor = slot
		for _, c in cards do c.btn:Destroy() end
		table.clear(cards)
		for i, e in list do
			local btn = new("TextButton", { Name = e.id, Text = "", AutoButtonColor = false, BorderSizePixel = 0, BackgroundColor3 = T.CARD,
				LayoutOrder = i }, grid)
			T.corner(btn, 5)
			local st = T.edge(btn)
			local vp, cam = GunPreview.viewport(btn, { Name = "Picture", Position = UDim2.fromOffset(3, 3), Size = UDim2.new(1, -6, 1, -21) })
			local nm = text(btn, "Name", string.upper(e.name), 11, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Center)
			nm.AnchorPoint = Vector2.new(0, 1); nm.Position = UDim2.new(0, 4, 1, -3); nm.Size = UDim2.new(1, -8, 0, 14)
			nm.TextScaled = true
			new("UITextSizeConstraint", { MaxTextSize = 11, MinTextSize = 7 }, nm)
			btn.Activated:Connect(function() ask(slot, e.id) end)
			btn.MouseEnter:Connect(function() S.hover = e.id end)
			btn.MouseLeave:Connect(function() if S.hover == e.id then S.hover = nil end end)
			table.insert(cards, { id = e.id, btn = btn, st = st, vp = vp, cam = cam })
		end
	end
	-- its size: as many columns as fit (7 at most), rows under them
	local n = #cards
	local cols = math.max(1, math.min(G.cols, n))
	local rows = math.max(1, math.ceil(n / cols))
	local pad = if S.small then 8 else 10
	local gw = cols * G.cw + (cols - 1) * 6
	local gh = rows * G.ch + (rows - 1) * 6
	local fh = if S.small then 24 else 30
	local w = math.max(gw + pad * 2, 260)
	local h = pad + gh + 8 + fh + pad
	tray.Size = UDim2.fromOffset(w, h)
	grid.Position = UDim2.fromOffset(math.floor((w - gw) / 2), pad); grid.Size = UDim2.fromOffset(gw, gh)
	if S.small then
		tray.AnchorPoint = Vector2.new(0.5, 0)
		tray.Position = UDim2.new(0.5, 0, 0, 62 + G.hh + 6 + G.th + 6)
	else
		tray.AnchorPoint = Vector2.new(0.5, 1)
		tray.Position = UDim2.new(0.5, 0, 1, -100 - (G.hh + 6 + G.th) - 8)
	end
	foot.Position = UDim2.fromOffset(pad + 2, pad + gh + 8); foot.Size = UDim2.fromOffset(w - pad * 2 - 96, fh)
	foot.TextYAlignment = Enum.TextYAlignment.Center
	foot.Text = S.note or (if alive() then "picks go in your hands now" else "you spawn with your picks next round")
	foot.TextColor3 = if S.note then T.ACCENT else T.MUTED
	done.AnchorPoint = Vector2.new(1, 0); done.Position = UDim2.fromOffset(w - pad, pad + gh + 8); done.Size = UDim2.fromOffset(84, fh)
	done.Text = if touch() then "DONE" else "DONE  [L]"
	local cur = current(slot)
	for _, c in cards do
		local on = c.id == cur
		c.st.Color = if on then T.ACCENT else Color3.new(1, 1, 1)
		c.st.Transparency = if on then 0.15 else 0.9
		c.btn.BackgroundColor3 = if on then T.CARD_HI else T.CARD
		c.btn.BackgroundTransparency = if S.asking == c.id then 0.45 else 0
		task.defer(GunPreview.put, c.vp, c.cam, c.id)
	end
	tray.Visible = true
end

local function draw()
	if not S.shown then return end
	drawTiles()
	drawTray()
end

ask = function(slot: string, wid: string)
	if S.asking then return end
	if current(slot) == wid then return end
	S.asking = wid
	draw()
	task.spawn(function()
		local ok, r = pcall(function() return Remote:InvokeServer("pick", slot, wid) end)
		S.asking = nil
		if not ok or type(r) ~= "table" then S.note = "no answer, try again"
		elseif not r.ok then S.note = if type(r.why) == "string" then r.why else "refused"
		else S.note = nil end
		me:SetAttribute("MatchLoadoutResult", if ok and type(r) == "table" then (if r.ok then "ok" else tostring(r.why)) else "error")
		draw()
	end)
end

setTray = function(slot: string?)
	if slot and not windowLeft() then return end
	S.tray = slot
	S.note = nil
	MenuCursor.set("matchloadout", slot ~= nil, function() return S.tray ~= nil end)
	draw()
end

local function setShown(v: boolean)
	if v == S.shown then return end
	S.shown = v
	root.Visible = v
	if v then
		S.total = math.max(windowLeft() or 1, 1)
		layout()
		draw()
	else
		setTray(nil)
		for _, tl in tiles do GunPreview.clear(tl.vp) end
		for _, c in cards do c.btn:Destroy() end
		table.clear(cards)
		cardsFor = ""
	end
end

-- ---------------------------------------------------------------- keys
Keys.began(function(io: any, gp: boolean)
	if UIS:GetFocusedTextBox() or not S.shown then return end
	if Binds.is("loadout", io) then
		if gp and not S.tray then return end
		setTray(if S.tray then nil else "primary")
	elseif S.tray and not gp then
		if io.KeyCode == Enum.KeyCode.Escape then setTray(nil); return end
		local n = ({ [Enum.KeyCode.One] = 1, [Enum.KeyCode.Two] = 2, [Enum.KeyCode.Three] = 3, [Enum.KeyCode.Four] = 4 } :: any)[io.KeyCode]
		if n and slotOf(n) then setTray(slotOf(n)) end
	end
end)

me:GetAttributeChangedSignal("LoadoutNext"):Connect(function() if S.shown then draw() end end)
for _, a in { "Wraps", "Hats", "Skins" } do
	me:GetAttributeChangedSignal(a):Connect(function() if S.shown then draw() end end)
end
me.CharacterAdded:Connect(function() if S.shown then task.defer(draw) end end)
workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(function() if S.shown then layout(); draw() end end)

-- shown or not: checked on every change that can shut it, and every frame (Heartbeat runs even when nothing is drawn)
local function check()
	setShown(windowLeft() ~= nil and me:GetAttribute("Zone") == "match" and me:GetAttribute("FinisherT") == nil)
end
for _, a in { "LoadoutWindow", "RoundEnds", "Zone", "FinisherT" } do me:GetAttributeChangedSignal(a):Connect(check) end
RunService.Heartbeat:Connect(check)
task.spawn(function()
	local r = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Round", 60)
	if r and r:IsA("RemoteEvent") then
		r.OnClientEvent:Connect(function(m: any) if type(m) == "table" and m.start then setShown(false) end end)
	end
end)

local t0 = os.clock()
RunService.RenderStepped:Connect(function()
	check()
	local left = windowLeft()
	if not S.shown or not left then return end
	if left > S.total then S.total = left end
	local s = tostring(math.ceil(left))
	if secs.Text ~= s then secs.Text = s end
	fill.Size = UDim2.fromScale(math.clamp(left / S.total, 0, 1), 1)
	local subT = if S.tray or not touch() then "" else "TAP A SLOT"
	if sub.Text ~= subT then sub.Text = subT end
	if S.small ~= small() then layout(); draw() end
	-- (the pictures turn a little: the slots slowly, the weapon under the mouse in the picker a full turn)
	local t = os.clock() - t0
	for i, tl in tiles do GunPreview.turn(tl.vp, math.sin(t * 0.7 + i * 1.3) * 0.35) end
	for _, c in cards do
		if c.id == S.hover then GunPreview.turn(c.vp, t * 1.6) end
	end
end)

-- ------------------------------------------------------------------ test hook
me:GetAttributeChangedSignal("MatchLoadoutTest"):Connect(function()
	local v = me:GetAttribute("MatchLoadoutTest")
	if type(v) ~= "string" or v == "" then return end
	me:SetAttribute("MatchLoadoutTest", nil)
	local cmd, a, b = string.match(v, "^(%a+):?([^:]*):?(.*)$")
	if cmd == "open" then setTray("primary"); me:SetAttribute("MatchLoadoutResult", if S.tray then "open" else "shut")
	elseif cmd == "slot" then setTray(if a ~= "" then a else "primary")
	elseif cmd == "close" then setTray(nil)
	elseif cmd == "pick" then ask(a or "", b or "")
	elseif cmd == "fake" then
		local w, h = string.match(a or "", "^(%d+)x(%d+)$")
		S.fake = if w then Vector2.new(tonumber(w) :: number, tonumber(h) :: number) else nil
		if S.shown then layout(); draw() end
	elseif cmd == "real" then
		S.fake = nil
		if S.shown then layout(); draw() end
	end
end)
