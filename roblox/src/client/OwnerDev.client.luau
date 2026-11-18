--!strict
-- THE OWNER'S DEV MENU, the client half (server/OwnerDev.server.luau checks and does every command; docs/OWNER-DEV.md).
-- two parts:
--   everyone's: a body the server freezes (attribute DevFrozen) is held still here, by its own client (the client owns
--     its body), and let go when the attribute goes
--   the owner's (the place's creator, and only after the server says so): the menu, and the powers the server switched
--     on, read from the owner's own attributes (DevFly = speed, DevNoclip, DevSpeed, DevArms):
--       fly: WASD or the stick where the camera looks, Space / pad A up, Ctrl or C / pad B down, nothing pressed holds
--         you in the air (the movement script stands down while Body.flying: Move.client)
--       noclip: the body's parts stop colliding (the Humanoid still stands on floors), so walls are air
--       run speed: Body.devSpeed, x the run speed (Move.client)
--       weapons in the hub: DevArms (the hub's weapon checks let it through); a weapon picked here goes into the
--         loadout's try layer (never saved), like trying one in training
--     the menu: F8, "/dev" in chat, or the small DEV button (touch, pad: VIEW reaches it); X flings and Z freezes or
--     lets go whoever you look at. it works everywhere, matches too: a match a power touches counts for nothing (the
--     server flags it; the status line says so)
-- plain and functional on purpose: no flavour text (the owner's rule)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local TextChatService = game:GetService("TextChatService")

local me = Players.LocalPlayer

-- ------------------------------------------------------------------ everyone's: held still while frozen
do
	local held: BasePart? = nil
	local function hold()
		local ch = me.Character
		local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		if me:GetAttribute("DevFrozen") == true then
			if root then
				root.AssemblyLinearVelocity = Vector3.zero
				root.Anchored = true
				held = root
			end
		elseif held then
			local r = held :: BasePart
			held = nil
			if r.Parent then
				r.Anchored = false
				r.AssemblyLinearVelocity = Vector3.zero
			end
		end
	end
	me:GetAttributeChangedSignal("DevFrozen"):Connect(hold)
	me.CharacterAdded:Connect(function(ch)
		held = nil
		ch:WaitForChild("HumanoidRootPart", 5)
		hold()
	end)
end

-- ------------------------------------------------------------------ the owner's only
if not (game.CreatorType == Enum.CreatorType.User and me.UserId > 0 and me.UserId == game.CreatorId) then return end
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("OwnerDev", 30) :: RemoteFunction?
if not Remote then return end
local function call(...: any): any
	local args = table.pack(...)
	local ok, res = pcall(function() return (Remote :: RemoteFunction):InvokeServer(table.unpack(args, 1, args.n)) end)
	return if ok then res else nil
end
local hello = call("hello")
if type(hello) ~= "table" or hello.owner ~= true then return end

local J = script.Parent
local T = require(J:WaitForChild("Theme")) :: any
local MenuCursor = require(J:WaitForChild("MenuCursor")) :: any
local Body = require(J:WaitForChild("Body")) :: any
local Roster = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Roster")) :: any
local LoadoutR = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Loadout", 30) :: RemoteFunction?

local function zone(): string return tostring(me:GetAttribute("Zone") or "hub") end
local function inMatch(): boolean return zone() == "match" end
local function typing(): boolean return UIS:GetFocusedTextBox() ~= nil end

-- ------------------------------------------------------------------ fly
local Fly = {}
do
	local lv: LinearVelocity? = nil
	local ao: AlignOrientation? = nil
	local on = false
	local controls: any = nil
	task.spawn(function()
		local ok, c = pcall(function()
			return (require(me:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: any) :: any):GetControls()
		end)
		if ok and type(c) == "table" then controls = c end
	end)
	local function parts(): (Humanoid?, BasePart?)
		local ch = me.Character
		local hum = ch and ch:FindFirstChildOfClass("Humanoid")
		local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		if not hum or not root or hum.Health <= 0 then return nil, nil end
		return hum, root
	end
	function Fly.stop()
		if lv then lv:Destroy(); lv = nil end
		if ao then ao:Destroy(); ao = nil end
		if not on then return end
		on = false
		Body.flying = false
		local hum, root = parts()
		if hum then hum.PlatformStand = false end
		if root then
			local jm = root:FindFirstChild("JankMove")
			if jm and jm:IsA("LinearVelocity") then jm.Enabled = true end
			root.AssemblyLinearVelocity = root.AssemblyLinearVelocity * 0.2 -- (stops where you let go)
		end
	end
	local function start(root: BasePart, hum: Humanoid)
		local att = root:FindFirstChild("RootAttachment") :: Attachment?
		if not att then
			local a = Instance.new("Attachment")
			a.Name = "RootAttachment"
			a.Parent = root
			att = a
		end
		local v = Instance.new("LinearVelocity")
		v.Name = "JankDevFly"
		v.Attachment0 = att
		v.RelativeTo = Enum.ActuatorRelativeTo.World
		v.VelocityConstraintMode = Enum.VelocityConstraintMode.Vector
		v.MaxForce = math.huge
		v.VectorVelocity = Vector3.zero
		v.Parent = root
		local o = Instance.new("AlignOrientation")
		o.Name = "JankDevFlyTurn"
		o.Mode = Enum.OrientationAlignmentMode.OneAttachment
		o.Attachment0 = att
		o.RigidityEnabled = true
		o.CFrame = CFrame.lookAt(Vector3.zero, root.CFrame.LookVector)
		o.Parent = root
		lv, ao = v, o
		local jm = root:FindFirstChild("JankMove")
		if jm and jm:IsA("LinearVelocity") then jm.Enabled = false end -- (the movement script's own: it stands down)
		hum.PlatformStand = true
		Body.flying = true
		on = true
	end
	local function key(k: Enum.KeyCode): boolean return UIS:IsKeyDown(k) end
	local function padDown(k: Enum.KeyCode): boolean
		local ok, d = pcall(function() return UIS:IsGamepadButtonDown(Enum.UserInputType.Gamepad1, k) end)
		return ok and d == true
	end
	RunService:BindToRenderStep("JankDevFly", Enum.RenderPriority.Camera.Value + 2, function()
		local speed = me:GetAttribute("DevFly")
		local hum, root = parts()
		if type(speed) ~= "number" or not hum or not root then Fly.stop(); return end
		if not on or not lv or not lv.Parent then
			Fly.stop()
			start(root, hum)
		end
		local cam = workspace.CurrentCamera
		if not cam or not lv or not ao then return end
		local mv = Vector3.zero
		if controls and not typing() then
			local ok, v = pcall(function() return controls:GetMoveVector() end)
			if ok and typeof(v) == "Vector3" then mv = v end
		end
		local dir = cam.CFrame:VectorToWorldSpace(mv)
		local up = 0
		if not typing() then
			if key(Enum.KeyCode.Space) or padDown(Enum.KeyCode.ButtonA) then up += 1 end
			if key(Enum.KeyCode.LeftControl) or key(Enum.KeyCode.C) or padDown(Enum.KeyCode.ButtonB) then up -= 1 end
		end
		local v = dir * speed + Vector3.new(0, up * speed, 0)
		if v.Magnitude > speed then v = v.Unit * speed end
		lv.VectorVelocity = v
		local lk = cam.CFrame.LookVector
		local flat = Vector3.new(lk.X, 0, lk.Z)
		if flat.Magnitude > 1e-3 then ao.CFrame = CFrame.lookAt(Vector3.zero, flat.Unit) end
		if not hum.PlatformStand then hum.PlatformStand = true end
	end)
	me.CharacterAdded:Connect(function() lv, ao, on = nil, nil, false; Body.flying = false end)
end

-- ------------------------------------------------------------------ noclip and run speed
do
	local saved: { [BasePart]: boolean } = {}
	RunService.Stepped:Connect(function()
		local ch = me.Character
		if me:GetAttribute("DevNoclip") == true and ch then
			for _, d in ch:GetDescendants() do
				if d:IsA("BasePart") and d.CanCollide then
					saved[d] = true
					d.CanCollide = false
				end
			end
		elseif next(saved) then
			for part in saved do if part.Parent then part.CanCollide = true end end
			table.clear(saved)
		end
	end)
	local function speed()
		local s = me:GetAttribute("DevSpeed")
		Body.devSpeed = if type(s) == "number" then math.clamp(s, 1, 4) else 1
	end
	me:GetAttributeChangedSignal("DevSpeed"):Connect(speed)
	me:GetAttributeChangedSignal("Zone"):Connect(speed)
	speed()
end

-- ------------------------------------------------------------------ the menu
local gui = T.new("ScreenGui", { Name = "OwnerDev", ResetOnSpawn = false, DisplayOrder = 61, IgnoreGuiInset = true, Enabled = false, ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, me:WaitForChild("PlayerGui"))
local scaled = T.scaled(gui)
local plate = T.plate(scaled, "Panel", UDim2.new(0.5, -390, 0.5, -255), UDim2.fromOffset(780, 510))
plate.BackgroundTransparency = 0.08

local title = T.text(plate, "Title", "DEV", 18, T.TEXT, T.FONT_TITLE)
title.Position = UDim2.fromOffset(18, 12); title.Size = UDim2.fromOffset(200, 26)
local status = T.text(plate, "Status", "", 13, T.MUTED)
status.Position = UDim2.fromOffset(18, 38); status.Size = UDim2.fromOffset(560, 18)
local note = T.text(plate, "Note", "", 13, T.SOFT, T.FONT, Enum.TextXAlignment.Left)
note.Position = UDim2.new(0, 18, 1, -30); note.Size = UDim2.new(1, -36, 0, 18)

local function button(parent: Instance, name: string, text: string, pos: UDim2, w: number, h: number?): TextButton
	local b = T.new("TextButton", {
		Name = name, Text = text, FontFace = T.FONT_BOLD, TextSize = 13, AutoButtonColor = true, TextColor3 = T.TEXT,
		BackgroundColor3 = T.CARD_HI, BorderSizePixel = 0, Position = pos, Size = UDim2.fromOffset(w, h or 28),
	}, parent)
	T.corner(b, 4)
	return b
end
local function lit(b: TextButton, on: boolean)
	b.BackgroundColor3 = if on then T.ACCENT else T.CARD_HI
	b.TextColor3 = if on then T.INK else T.TEXT
end
local function said(res: any, fallback: string)
	if type(res) == "table" and res.ok then note.Text = tostring(res.did or fallback)
	else note.Text = "refused: " .. tostring(if type(res) == "table" and res.why then res.why else "no answer") end
end

local close = button(plate, "Close", "CLOSE", UDim2.new(1, -86, 0, 14), 70)
close.Modal = true -- (frees the mouse from first person while the menu is up)

-- the left half: me
local ME_X, ME_W = 18, 360
local function label(parent: Instance, name: string, text: string, x: number, y: number, w: number): TextLabel
	local l = T.text(parent, name, text, 12, T.MUTED, T.FONT_BOLD)
	l.Position = UDim2.fromOffset(x, y); l.Size = UDim2.fromOffset(w, 16)
	return l
end
label(plate, "MeHead", "ME", ME_X, 66, 100)

local flyB = button(plate, "Fly", "FLY", UDim2.fromOffset(ME_X, 86), 110)
local noclipB = button(plate, "Noclip", "NOCLIP", UDim2.fromOffset(ME_X + 118, 86), 110)
local armsB = button(plate, "Arms", "WEAPONS IN HUB", UDim2.fromOffset(ME_X + 236, 86), 124)

-- a slider: a track you click or drag (mouse, touch), and - / + (a pad, or a fine step)
type Slider = { set: (number) -> (), value: () -> number }
local function slider(name: string, text: string, y: number, lo: number, hi: number, step: number, fmt: string, send: (number) -> ()): Slider
	label(plate, name .. "Label", text, ME_X, y + 6, 90)
	local minus = button(plate, name .. "Minus", "-", UDim2.fromOffset(ME_X + 92, y), 28)
	local track = T.new("TextButton", { Name = name .. "Track", Text = "", AutoButtonColor = false, BackgroundColor3 = T.TRACK, BorderSizePixel = 0,
		Position = UDim2.fromOffset(ME_X + 126, y + 11), Size = UDim2.fromOffset(150, 6), Selectable = false }, plate)
	T.corner(track, 3)
	local fill = T.new("Frame", { Name = "Fill", BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Size = UDim2.fromScale(0, 1) }, track)
	T.corner(fill, 3)
	local knob = T.new("Frame", { Name = "Knob", AnchorPoint = Vector2.new(0.5, 0.5), BackgroundColor3 = T.TEXT, BorderSizePixel = 0,
		Position = UDim2.fromScale(0, 0.5), Size = UDim2.fromOffset(14, 14) }, track)
	T.corner(knob, 7)
	local plus = button(plate, name .. "Plus", "+", UDim2.fromOffset(ME_X + 282, y), 28)
	local val = T.text(plate, name .. "Value", "", 13, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Right)
	val.Position = UDim2.fromOffset(ME_X + 312, y + 5); val.Size = UDim2.fromOffset(48, 18)
	local v = lo
	local function draw()
		local a = (v - lo) / (hi - lo)
		fill.Size = UDim2.fromScale(a, 1)
		knob.Position = UDim2.fromScale(a, 0.5)
		val.Text = fmt:format(v)
	end
	local function snap(x: number): number return math.clamp(math.floor((x - lo) / step + 0.5) * step + lo, lo, hi) end
	local dragging: InputObject? = nil
	local function fromX(x: number)
		local a = math.clamp((x - track.AbsolutePosition.X) / math.max(1, track.AbsoluteSize.X), 0, 1)
		v = snap(lo + a * (hi - lo))
		draw()
	end
	track.InputBegan:Connect(function(io: InputObject)
		if io.UserInputType == Enum.UserInputType.MouseButton1 or io.UserInputType == Enum.UserInputType.Touch then
			dragging = io
			fromX(io.Position.X)
		end
	end)
	UIS.InputChanged:Connect(function(io: InputObject)
		if not dragging then return end
		if io.UserInputType == Enum.UserInputType.MouseMovement or io == dragging then fromX(io.Position.X) end
	end)
	UIS.InputEnded:Connect(function(io: InputObject)
		if dragging and (io == dragging or io.UserInputType == Enum.UserInputType.MouseButton1) then
			dragging = nil
			send(v)
		end
	end)
	minus.Activated:Connect(function() v = snap(v - step); draw(); send(v) end)
	plus.Activated:Connect(function() v = snap(v + step); draw(); send(v) end)
	draw()
	return { set = function(x: number) if not dragging then v = snap(x); draw() end end, value = function() return v end }
end

local flySpeed = slider("FlySpeed", "FLY SPEED", 124, 20, 300, 10, "%d", function(x) said(call("set", "flySpeed", x), "fly speed " .. x) end)
local runSpeed = slider("RunSpeed", "RUN SPEED", 160, 1, 4, 0.25, "%.2fx", function(x) said(call("set", "speed", x), ("run speed %.2fx"):format(x)) end)

-- weapons: every live one, by slot. a pick goes into the try layer (never saved): in the hub only with WEAPONS IN HUB on
label(plate, "WeaponsHead", "GIVE ME A WEAPON", ME_X, 200, 200)
local wlist = T.new("ScrollingFrame", {
	Name = "Weapons", BackgroundColor3 = T.CARD, BackgroundTransparency = 0.2, BorderSizePixel = 0,
	Position = UDim2.fromOffset(ME_X, 220), Size = UDim2.fromOffset(ME_W, 252),
	CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollBarThickness = 6, ScrollingDirection = Enum.ScrollingDirection.Y,
}, plate)
T.corner(wlist, 4)
T.new("UIGridLayout", { CellSize = UDim2.fromOffset(110, 26), CellPadding = UDim2.fromOffset(6, 6), SortOrder = Enum.SortOrder.LayoutOrder }, wlist)
T.new("UIPadding", { PaddingTop = UDim.new(0, 6), PaddingLeft = UDim.new(0, 6), PaddingRight = UDim.new(0, 6), PaddingBottom = UDim.new(0, 6) }, wlist)
local weaponButtons: { [string]: TextButton } = {}
do
	local order = 0
	for _, slot in Roster.SLOTS do
		for _, e in Roster.list do
			if e.slot ~= slot or not e.live then continue end
			order += 1
			local b = T.new("TextButton", {
				Name = "W_" .. e.id, Text = string.upper(e.name), FontFace = T.FONT_BOLD, TextSize = 11, TextScaled = false,
				TextTruncate = Enum.TextTruncate.AtEnd, AutoButtonColor = true, TextColor3 = T.TEXT, BackgroundColor3 = T.CARD_HI,
				BorderSizePixel = 0, LayoutOrder = order,
			}, wlist)
			T.corner(b, 4)
			local bar = T.new("Frame", { Name = "Slot", BackgroundColor3 = e.color or T.DIM, BorderSizePixel = 0, Size = UDim2.new(0, 3, 1, -8), Position = UDim2.fromOffset(3, 4) }, b)
			T.corner(bar, 1)
			weaponButtons[e.id] = b
			b.Activated:Connect(function()
				if not LoadoutR then note.Text = "no loadout remote"; return end
				local z = zone()
				if z ~= "training" and z ~= "playground" and me:GetAttribute("DevArms") ~= true then
					local r = call("set", "arms", true)
					if type(r) ~= "table" or not r.ok then said(r, ""); return end
				end
				local ok, okP, why = pcall(function() return (LoadoutR :: RemoteFunction):InvokeServer("pick", e.slot, e.id) end)
				note.Text = if ok and okP then ("%s in hand (key %d)"):format(e.name, (table.find(Roster.SLOTS, e.slot) or 1))
					else "refused: " .. tostring(if ok then why else okP)
			end)
		end
	end
end

-- the right half: everyone else
local PL_X, PL_W = 398, 364
label(plate, "PlayersHead", "PLAYERS", PL_X, 66, 100)
local hint = T.text(plate, "Hint", "X  fling   ·   Z  freeze / let go   (whoever you look at)", 12, T.DIM, T.FONT, Enum.TextXAlignment.Right)
hint.Position = UDim2.fromOffset(PL_X + 60, 66); hint.Size = UDim2.fromOffset(PL_W - 60, 16)
local plist = T.new("ScrollingFrame", {
	Name = "Players", BackgroundColor3 = T.CARD, BackgroundTransparency = 0.2, BorderSizePixel = 0,
	Position = UDim2.fromOffset(PL_X, 86), Size = UDim2.fromOffset(PL_W, 350),
	CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollBarThickness = 6, ScrollingDirection = Enum.ScrollingDirection.Y,
}, plate)
T.corner(plist, 4)
T.new("UIListLayout", { Padding = UDim.new(0, 4), SortOrder = Enum.SortOrder.LayoutOrder }, plist)
T.new("UIPadding", { PaddingTop = UDim.new(0, 6), PaddingLeft = UDim.new(0, 6), PaddingRight = UDim.new(0, 10), PaddingBottom = UDim.new(0, 6) }, plist)
local unfreezeB = button(plate, "UnfreezeAll", "LET EVERYONE GO", UDim2.fromOffset(PL_X, 444), 140)
local offB = button(plate, "AllOff", "ALL MY POWERS OFF", UDim2.fromOffset(PL_X + 148, 444), 150)


local open = false
local refreshPlayers: () -> ()
local function drawMe()
	local fly = me:GetAttribute("DevFly")
	lit(flyB, type(fly) == "number")
	flyB.Text = if type(fly) == "number" then "FLY: ON" else "FLY: OFF"
	local nc = me:GetAttribute("DevNoclip") == true
	lit(noclipB, nc)
	noclipB.Text = if nc then "NOCLIP: ON" else "NOCLIP: OFF"
	local arms = me:GetAttribute("DevArms") == true
	lit(armsB, arms)
	armsB.Text = if arms then "WEAPONS: ON" else "WEAPONS IN HUB"
	local fs = me:GetAttribute("DevFlySpeed")
	if type(fs) == "number" then flySpeed.set(fs) end
	local rs = me:GetAttribute("DevSpeed")
	runSpeed.set(if type(rs) == "number" then rs else 1)
	local z = zone()
	local words = { hub = "HUB", training = "TRAINING", playground = "PLAYGROUND", staging = "MAP ROOM", match = "MATCH" }
	local how = if me:GetAttribute("DevOn") == true then "anti-cheat leaves you alone" else "no powers on"
	if z == "match" then how = if me:GetAttribute("MatchDev") ~= nil then "this match counts for nothing now" else "a power used here makes this match count for nothing" end
	status.Text = ("%s  ·  %s"):format(words[z] or string.upper(z), how)
end
for _, a in { "DevFly", "DevNoclip", "DevArms", "DevFlySpeed", "DevSpeed", "DevOn", "Zone", "MatchDev" } do
	me:GetAttributeChangedSignal(a):Connect(function() if open then drawMe() end end)
end

flyB.Activated:Connect(function() said(call("set", "fly", type(me:GetAttribute("DevFly")) ~= "number"), "fly") end)
noclipB.Activated:Connect(function() said(call("set", "noclip", me:GetAttribute("DevNoclip") ~= true), "noclip") end)
armsB.Activated:Connect(function() said(call("set", "arms", me:GetAttribute("DevArms") ~= true), "weapons") end)
unfreezeB.Activated:Connect(function() said(call("unfreezeAll"), "everyone let go"); task.defer(refreshPlayers) end)
offB.Activated:Connect(function() said(call("set", "off"), "all off") end)

local function cell(parent: Instance, name: string, text: string, x: number, w: number, color: Color3?, font: Font?)
	local l = T.text(parent, name, text, 12, color or T.TEXT, font or T.FONT, Enum.TextXAlignment.Left)
	l.Position = UDim2.fromOffset(x, 0); l.Size = UDim2.new(0, w, 1, 0)
	l.TextTruncate = Enum.TextTruncate.AtEnd
	return l
end
refreshPlayers = function()
	if not open then return end
	local res = call("players")
	for _, c in plist:GetChildren() do if c:IsA("Frame") then c:Destroy() end end
	if type(res) ~= "table" or not res.ok or type(res.players) ~= "table" then return end
	if #res.players == 0 then
		local row = T.new("Frame", { Name = "Empty", BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 26) }, plist)
		cell(row, "Text", "nobody else here", 4, 300, T.DIM)
		return
	end
	for i, r in res.players do
		local row = T.new("Frame", { Name = "Row_" .. tostring(r.user or i), BackgroundColor3 = T.CARD_HI, BackgroundTransparency = 0.4, BorderSizePixel = 0,
			Size = UDim2.new(1, 0, 0, 30), LayoutOrder = i }, plist)
		T.corner(row, 4)
		local away = false
		cell(row, "Name", tostring(r.name), 8, 96, T.TEXT, T.FONT_BOLD)
		cell(row, "Zone", if r.frozen then "FROZEN" else string.upper(tostring(r.zone)), 104, 64, if r.frozen then T.ACCENT else T.MUTED)
		local x = 170
		local function act(name: string, text: string, w: number, fn: () -> ())
			local b = button(row, name, text, UDim2.fromOffset(x, 3), w, 24)
			b.TextSize = 11
			x += w + 4
			if away then b.AutoButtonColor = false; b.TextColor3 = T.DIM end
			b.Activated:Connect(function() if not away then fn(); task.delay(0.2, refreshPlayers) end end)
		end
		act("Fling", "FLING", 44, function() said(call("fling", r.ref), "flung") end)
		act("Freeze", if r.frozen then "LET GO" else "FREEZE", 52, function() said(call("freeze", r.ref, not r.frozen), "done") end)
		act("Goto", "GO TO", 40, function() said(call("goto", r.ref), "done") end)
		act("Bring", "BRING", 40, function() said(call("bring", r.ref), "done") end)
	end
end

local function setOpen(on: boolean)
	if open == on then return end
	open = on
	gui.Enabled = on
	MenuCursor.set("dev", on, function() return gui.Enabled end, true) -- (the mouse, but you can still move: try a fly with it up)
	if on then
		drawMe()
		refreshPlayers()
	end
end
local function toggle() setOpen(not open) end
close.Activated:Connect(function() setOpen(false) end)
gui:GetPropertyChangedSignal("Enabled"):Connect(function() if not gui.Enabled and open then setOpen(false) end end)
task.spawn(function()
	while true do
		task.wait(2)
		if open then refreshPlayers() end
	end
end)

-- a pad: B backs out of it, VIEW reaches the DEV button (PadNav's Pad.MENUS, once PadNav has put it there)
task.spawn(function()
	local pm = J:FindFirstChild("Pad")
	local ok, Pad = false, nil
	if pm and pm:IsA("ModuleScript") then ok, Pad = pcall(require, pm) end
	if not ok or type(Pad) ~= "table" then return end
	for _ = 1, 60 do
		if type((Pad :: any).MENUS) == "table" then
			(Pad :: any).MENUS.dev = { gui = "OwnerDev", back = function() setOpen(false) end }
			return
		end
		task.wait(1)
	end
end)

-- the DEV button: a small one in the corner, the owner's only (touch, and a pad through VIEW; a mouse can click it too)
do
	local bg = T.new("ScreenGui", { Name = "JankDevButton", ResetOnSpawn = false, DisplayOrder = 5, IgnoreGuiInset = true, ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, me:WaitForChild("PlayerGui"))
	local b = T.new("TextButton", {
		Name = "Dev", Text = "DEV", FontFace = T.FONT_BOLD, TextSize = 12, AutoButtonColor = true, TextColor3 = T.ACCENT,
		BackgroundColor3 = T.BG, BackgroundTransparency = 0.3, BorderSizePixel = 0,
		AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -12, 0, 64), Size = UDim2.fromOffset(46, 24),
	}, bg)
	T.corner(b, 4)
	T.edge(b, T.ACCENT, 0.6)
	b.Activated:Connect(toggle)
end

-- F8, "/dev", X and Z
if TextChatService.ChatVersion == Enum.ChatVersion.TextChatService then
	local cmd = Instance.new("TextChatCommand")
	cmd.Name = "JankDev"
	cmd.PrimaryAlias = "/dev"
	cmd.Parent = TextChatService
	cmd.Triggered:Connect(function() toggle() end)
end
me:GetAttributeChangedSignal("DevPanel"):Connect(toggle)
local function lookDir(): Vector3?
	local cam = workspace.CurrentCamera
	return if cam then cam.CFrame.LookVector else nil
end
UIS.InputBegan:Connect(function(io: InputObject, gp: boolean)
	if gp or typing() then return end
	if io.KeyCode == Enum.KeyCode.F8 then
		toggle()
	elseif io.KeyCode == Enum.KeyCode.X or io.KeyCode == Enum.KeyCode.Z then
		local lk = lookDir()
		if not lk then return end
		local res = call(if io.KeyCode == Enum.KeyCode.X then "flingAim" else "freezeAim", lk)
		if open then said(res, "done"); task.delay(0.2, refreshPlayers) end
	end
end)

-- (Studio tests: player attribute DevMenuTest = "open" / "close")
if RunService:IsStudio() then
	me:GetAttributeChangedSignal("DevMenuTest"):Connect(function()
		local v = me:GetAttribute("DevMenuTest")
		if v == "open" then setOpen(true) elseif v == "close" then setOpen(false) end
	end)
end
