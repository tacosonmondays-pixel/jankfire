--!strict
-- Touch controls for phones and tablets: the web game's (public/js/touch.js, touch.css, autofire.js) on Roblox.
-- Only on a touch screen with no keyboard (Keys.isTouch). Roblox's own thumbstick and jump button are switched off
-- (GuiService.TouchControlsEnabled) so nothing is doubled.
--   * the left side: a move stick that appears where your thumb lands. 8-way on purpose (movement is forward / back /
--     left / right keys everywhere else too); pushed all the way up it runs (Shift).
--   * the right side: drag anywhere to look. FIRE, AIM and HOOK steer the look too while your thumb is on them.
--   * the buttons, at the web's places (finger points from the bottom corner on the fire side): FIRE, JUMP, SLIDE,
--     AIM (a tap toggle unless turned off), HOOK, STAB (the melee slot), SWAP (your last weapon), RELOAD; along the top
--     EMOTE (the wheel), AUTO (auto fire) and SETTINGS. The HUD's own boxes are buttons too: the three weapon chips (slots 1-3), the ammo
--     plate (reload) and the item plate (G, held for as long as you hold it).
--   * no second input path: every button presses its key through Keys.luau, so Move, Arsenal, Utility and the menus
--     run their own key code for it. Only looking is done here (the camera module's own touch turning is switched off,
--     so the look speed setting and FIRE-steering work).
--   * auto fire (autofire.js, rules kept): pulls the same trigger as FIRE when the crosshair is on an enemy in range and
--     in plain sight, after a short human-ish delay; never through walls, never a friend, snipers only when scoped in.
--     your thumb on FIRE always wins.
--   * settings: the settings page's TOUCH rows (Settings.luau: touch.sens, touch.size, touch.alpha, touch.aimToggle,
--     touch.autofire, touch.lefty), saved per player there.
--   * the hub: no weapons, so the fight buttons go and the PLAY / PARTY / PROFILE / SHOP / LOADOUT stack moves to the
--     right (the left is the stick's).
-- Test hook (Studio): player attribute TouchForce = true turns it all on with a mouse and keyboard; TouchTest takes
-- "down:<id>", "up:<id>", "tap:<id>", "stick:<x>,<y>" (-1..1, "stick:0,0" lets go), "look:<dx>,<dy>" (points),
-- "chip:<1-3>", "item:down" / "item:up", "ammo", "auto:on|off", "assist:<0-1.5>", "settings", "pill:<emote|auto|settings>", "state" (writes TouchState as JSON), "fake:844x390" (the HUD laid
-- out in a phone-sized box: Studio's device emulator can't be driven from a script), "real".
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local GuiService = game:GetService("GuiService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local HttpService = game:GetService("HttpService")

local Keys = require(script.Parent:WaitForChild("Keys"))
local T = require(script.Parent:WaitForChild("Theme"))
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Hitbox = require(Shared:WaitForChild("Hitbox"))

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")
local W = Weapons.list :: { [string]: any }
local SM = Weapons.S -- studs per metre (the web game's numbers are metres)
local MB1, MB2 = Enum.UserInputType.MouseButton1, Enum.UserInputType.MouseButton2
local SLOT_KEYS = { Enum.KeyCode.One, Enum.KeyCode.Two, Enum.KeyCode.Three }

-- ---------------------------------------------------------------- settings
local fake: Vector2? = nil -- (a test: the screen pretends to be this size, a box in the middle: fakeScreen below)
local function viewport(): Vector2
	if fake then return fake end
	local cam = workspace.CurrentCamera
	return if cam then cam.ViewportSize else Vector2.new(844, 390)
end
local function tablet(): boolean local v = viewport(); return math.min(v.X, v.Y) >= 600 end
-- the settings live in the settings page's store (Settings.luau, saved per player by SettingsServer; its TOUCH rows):
--   touch.sens   look speed            touch.size   button size, times the device's own (1, or 1.2 on a tablet: web)
--   touch.alpha  button opacity        touch.aimToggle  AIM is a tap toggle (holding a button while steering is a
--   touch.autofire  auto fire          hand cramp)     touch.lefty  the stick on the right, the buttons on the left
--   touch.assist aim assist strength (0 = off; aimassist.js)
-- (until Settings.luau is in the place, the web's defaults below hold)
local DEF: { [string]: any } = { ["touch.sens"] = 1, ["touch.alpha"] = 0.75, ["touch.aimToggle"] = true,
	["touch.autofire"] = true, ["touch.lefty"] = false, ["touch.size"] = 1, ["touch.assist"] = 1 }
local SettingsMod: any = nil
local function findSettings()
	if SettingsMod then return end
	local m = script.Parent:FindFirstChild("Settings")
	if m and m:IsA("ModuleScript") then
		local ok, r = pcall(require, m)
		if ok and type(r) == "table" and type((r :: any).get) == "function" then SettingsMod = r end
	end
end
local function get(k: string): any
	if SettingsMod then
		local ok, v = pcall(SettingsMod.get, k)
		if ok and v ~= nil then return v end
	end
	return DEF[k]
end
local function set(k: string, v: any)
	if SettingsMod and type(SettingsMod.set) == "function" then pcall(SettingsMod.set, k, v) else DEF[k] = v end
end
-- what this frame uses (read from the store every frame; a change shows at once)
local S = { sens = 1, size = if tablet() then 1.2 else 1, alpha = 0.75, aim = true, auto = true, lefty = false, assist = 1 }
local function readSettings(): boolean
	findSettings()
	local sens = tonumber(get("touch.sens")) or 1
	local size = math.clamp((tonumber(get("touch.size")) or 1) * (if tablet() then 1.2 else 1), 0.6, 1.7)
	local alpha = math.clamp(tonumber(get("touch.alpha")) or 0.75, 0.15, 1)
	local lefty = get("touch.lefty") == true
	local changed = size ~= S.size or alpha ~= S.alpha or lefty ~= S.lefty
	S.sens, S.size, S.alpha, S.lefty = math.clamp(sens, 0.1, 5), size, alpha, lefty
	S.aim = get("touch.aimToggle") ~= false
	S.auto = get("touch.autofire") ~= false
	S.assist = math.clamp(tonumber(get("touch.assist")) or 1, 0, 1.5)
	return changed
end

-- ---------------------------------------------------------------- state
local active = false -- touch controls on
local built = false
local controls: any = nil -- the control module (its moveFunction is what the keyboard drives too)
local cameraInput: any = nil -- the camera module's input reader (its touch turning is switched off while we're on)
local origRotation: any = nil

local function zone(): string? return me:GetAttribute("Zone") :: string? end
local function menuOpen(): boolean return me:GetAttribute("LoadoutOpen") == true end
local function settingsOpen(): boolean return me:GetAttribute("SettingsOpen") == true end
local function alive(): (Model?, Humanoid?, BasePart?)
	local ch = me.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not ch or not hum or not root or hum.Health <= 0 then return nil, nil, nil end
	return ch, hum, root
end
local function lo(): { string }
	local s = me:GetAttribute("Loadout")
	local out = {}
	if type(s) == "string" then for id in string.gmatch(s, "[^,]+") do if W[id] then table.insert(out, id) end end end
	return if #out == 3 then out else Weapons.loadout
end
local function heldWeapon(): string?
	local ch = me.Character
	local hw = ch and ch:FindFirstChild("HeldWeapon")
	local id = hw and hw:GetAttribute("Weapon")
	return if type(id) == "string" then id else nil
end
-- (weapons work in a match, in training and on the playground)
local function fightZone(): boolean local z = zone(); return z == "match" or z == "training" or z == "playground" end

-- ---------------------------------------------------------------- the layer
local gui: ScreenGui
local pad: Frame
local stickRing: Frame
local stickKnob: Frame
local topRow: Frame
local chips: Frame
local full: Frame -- (the whole screen, no insets: the HUD's own frame of reference)
-- how far the safe area sits in from the screen's right and bottom edges (a notch, the home bar), in points
local function insets(): (number, number)
	if not built or fake then return 0, 0 end
	local r = (full.AbsolutePosition.X + full.AbsoluteSize.X) - (pad.AbsolutePosition.X + pad.AbsoluteSize.X)
	local b = (full.AbsolutePosition.Y + full.AbsoluteSize.Y) - (pad.AbsolutePosition.Y + pad.AbsoluteSize.Y)
	return math.max(0, r), math.max(0, b)
end
-- Studio can't be told to be a phone from a script (its device emulator is hidden from them), so a test lays the HUD
-- out in a phone-sized box in the middle of the view: every ScreenGui's "Scaled" frame (Theme.scaled: the HUD's
-- plates, the hub's buttons) and this layer go into the box, with the scale a screen that size would get. nil = back
local fakeSaved: { [GuiObject]: { any } } = {}
local fakeEdge: Frame? = nil
local function fakeScreen(sz: Vector2?)
	for o, v in fakeSaved do
		if o.Parent then
			o.AnchorPoint, o.Position, o.Size = v[1], v[2], v[3]
			local sc = o:FindFirstChildOfClass("UIScale")
			if sc and v[4] then sc.Scale = v[4] end
		end
	end
	table.clear(fakeSaved)
	if fakeEdge then fakeEdge:Destroy(); fakeEdge = nil end
	fake = sz
	me:SetAttribute("FakeScreen", sz) -- (other screens lay themselves out for it too: LoadoutUI's phone layout)
	if not built then return end
	if not sz then
		pad.AnchorPoint, pad.Position, pad.Size = Vector2.zero, UDim2.new(), UDim2.fromScale(1, 1)
		return
	end
	local s = math.max(1, sz.Y / 720)
	local function box(o: GuiObject)
		local sc = o:FindFirstChildOfClass("UIScale")
		fakeSaved[o] = { o.AnchorPoint, o.Position, o.Size, if sc then sc.Scale else nil }
		o.AnchorPoint, o.Position = Vector2.new(0.5, 0.5), UDim2.fromScale(0.5, 0.5)
		if sc then sc.Scale = s; o.Size = UDim2.fromOffset(sz.X / s, sz.Y / s) else o.Size = UDim2.fromOffset(sz.X, sz.Y) end
	end
	for _, g in pg:GetChildren() do
		local f = g:IsA("ScreenGui") and g:FindFirstChild("Scaled")
		if f and f:IsA("GuiObject") then box(f) end
	end
	pad.AnchorPoint, pad.Position, pad.Size = Vector2.new(0.5, 0.5), UDim2.fromScale(0.5, 0.5), UDim2.fromOffset(sz.X, sz.Y)
	local e = T.new("Frame", { Name = "FakeScreen", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(sz.X, sz.Y), BackgroundTransparency = 1 }, full) :: Frame
	T.new("UIStroke", { Color = T.ACCENT, Thickness = 2, Transparency = 0.2 }, e)
	fakeEdge = e
end

type Btn = { id: string, key: any, label: string, x: number, y: number, d: number, look: boolean?, fight: boolean?,
	toggle: boolean?, katana: boolean?, body: boolean?, face: TextButton, scale: UIScale, stroke: UIStroke, down: boolean, finger: any, lit: boolean }
local BTNS: { Btn } = {}
local byId: { [string]: Btn } = {}
local function def(id: string, key: any, label: string, x: number, y: number, d: number, o: { [string]: boolean }?)
	local b: any = { id = id, key = key, label = label, x = x, y = y, d = d, down = false, lit = false }
	if o then for k, v in o do b[k] = v end end
	table.insert(BTNS, b)
	byId[id] = b
end
def("fire", MB1, "FIRE", 100, 92, 84, { look = true, fight = true })
def("jump", Enum.KeyCode.Space, "JUMP", 36, 50, 58)
def("crouch", Enum.KeyCode.C, "SLIDE", 34, 120, 50)
def("aim", MB2, "AIM", 44, 184, 50, { look = true, fight = true, toggle = true })
def("hook", Enum.KeyCode.E, "HOOK", 112, 176, 56, { look = true })
def("melee", Enum.KeyCode.Three, "STAB", 176, 152, 44, { fight = true })
def("swap", nil, "SWAP", 180, 98, 44, { fight = true })
def("reload", Enum.KeyCode.R, "RELOAD", 176, 44, 46, { fight = true })
def("wave", Enum.KeyCode.Q, "WAVE", 112, 240, 52, { fight = true, katana = true }) -- (the katana's slash wave: shown with the katana out, lit with the meter full)
def("yank", Enum.KeyCode.F, "YANK", 56, 244, 50, { fight = true, body = true }) -- (the grapple's yank: shown while your rope is on a person and it's ready. Move.client)
local TEXT_SIZE: { [string]: number } = { fire = 17, jump = 13, hook = 13, crouch = 12, aim = 12 }

type Pill = { face: TextButton, lit: boolean }
local pills: { [string]: Pill } = {}

-- ---------------------------------------------------------------- fingers
-- touch / mouse input -> { kind = "btn" | "look" | "stick", id, last }
type Finger = { kind: string, id: string?, last: Vector2 }
local fingers: { [any]: Finger } = {}
local boxUp: { [string]: () -> () } = {} -- (the HUD boxes' "let go", below)
local lookAcc = Vector2.zero
local mv = { finger = nil :: any, ox = 0, oy = 0, f = false, b = false, l = false, r = false, sprint = false }
local testStick: Vector2? = nil
local aimOn = false -- AIM toggled on (the toggle owns one press of the aim key)
local fireThumb = false
local swapHist = { cur = nil :: string?, prev = nil :: string? }

local function fingerKey(io: any): any
	if io.UserInputType == Enum.UserInputType.Touch then return io end
	return "mouse"
end

local function setAim(on: boolean)
	if on == aimOn then return end
	aimOn = on
	Keys.press(MB2, on)
	local b = byId.aim
	b.lit = on
end

local autoReset: () -> () -- (auto fire, below)

local function btnDown(b: Btn)
	if b.down then return end
	b.down = true
	b.scale.Scale = 0.92
	if b.id == "aim" and S.aim then setAim(not aimOn); return end
	if b.id == "swap" then
		local l = lo()
		local want = swapHist.prev and table.find(l, swapHist.prev)
		if not want then
			local cur = swapHist.cur and table.find(l, swapHist.cur) or 1
			want = if cur == 1 then 2 else 1
		end
		Keys.tap(SLOT_KEYS[want :: number])
		return
	end
	if b.id == "fire" then fireThumb = true; autoReset() end
	if b.key then Keys.press(b.key, true) end
end
local function btnUp(b: Btn)
	if not b.down then return end
	b.down = false
	b.scale.Scale = 1
	if b.id == "aim" and S.aim then return end
	if b.id == "swap" then return end
	if b.id == "fire" then fireThumb = false end
	if b.key then Keys.press(b.key, false) end
end

local itemDown = false
local function itemPress(down: boolean)
	if down == itemDown then return end
	itemDown = down
	Keys.press(Enum.KeyCode.G, down)
end

local function stickEnd()
	mv.finger = nil
	mv.f, mv.b, mv.l, mv.r = false, false, false, false
	if mv.sprint then mv.sprint = false; Keys.press(Enum.KeyCode.LeftShift, false) end
	if built then
		stickKnob.Position = UDim2.fromScale(0.5, 0.5)
		stickRing:SetAttribute("Live", false)
	end
end
local function stickSet(dx: number, dy: number, m: number)
	local on = m > 0.24
	local fw = on and dy < -0.36
	mv.f, mv.b, mv.l, mv.r = fw, on and dy > 0.36, on and dx < -0.36, on and dx > 0.36
	local run = fw and m > 0.9 -- all the way up = run
	if run ~= mv.sprint then mv.sprint = run; Keys.press(Enum.KeyCode.LeftShift, run) end
end
local function stickMove(pos: Vector2)
	local r = 52 * S.size
	local dx, dy = (pos.X - mv.ox) / r, (pos.Y - mv.oy) / r
	local m = math.sqrt(dx * dx + dy * dy)
	if m > 1 then dx /= m; dy /= m end
	stickKnob.Position = UDim2.new(0.5, dx * r * 0.62, 0.5, dy * r * 0.62)
	stickSet(dx, dy, m)
end

local function releaseAll()
	for k, f in fingers do
		if f.kind == "btn" and f.id and byId[f.id] then btnUp(byId[f.id]) end
		fingers[k] = nil
	end
	for _, b in BTNS do btnUp(b) end
	setAim(false)
	itemPress(false)
	stickEnd()
	testStick = nil
	lookAcc = Vector2.zero
	if autoReset then autoReset() end
end

-- ---------------------------------------------------------------- building it
local function style(face: TextButton, lit: boolean, accentEdge: boolean?)
	local a = math.clamp(S.alpha, 0.15, 1)
	face.BackgroundColor3 = if lit then T.ACCENT else T.BG
	face.BackgroundTransparency = if lit then 1 - a else 1 - a * 0.72
	face.TextColor3 = if lit then T.INK else T.TEXT
	face.TextTransparency = (1 - a) * 0.55
	local st = face:FindFirstChildOfClass("UIStroke")
	if st then
		st.Color = if accentEdge and not lit then T.ACCENT else T.EDGE
		st.Transparency = if accentEdge and not lit then 1 - a * 0.9 else 1 - (1 - T.EDGE_A) * a * 1.2
	end
end

local function applyLook()
	if not built then return end
	local ts = S.size
	for _, b in BTNS do
		b.face.Size = UDim2.fromOffset(b.d * ts, b.d * ts)
		b.face.Position = if S.lefty then UDim2.new(0, b.x * ts, 1, -b.y * ts) else UDim2.new(1, -b.x * ts, 1, -b.y * ts)
		b.face.TextSize = math.max(10, (TEXT_SIZE[b.id] or 10) * ts)
		style(b.face, b.lit, b.id == "fire")
	end
	local r = 104 * ts
	stickRing.Size = UDim2.fromOffset(r, r)
	stickKnob.Size = UDim2.fromOffset(46 * ts, 46 * ts)
	for _, p in pills do
		p.face.Size = UDim2.fromOffset(0, 34 * ts)
		p.face.TextSize = math.max(10, 12 * ts)
		style(p.face, p.lit)
	end
	topRow.Size = UDim2.fromOffset(0, 34 * ts)
end

-- the top row's buttons
local function pillPress(id: string)
	if not active then return end
	if id == "auto" then
		S.auto = not S.auto
		set("touch.autofire", S.auto)
		if not S.auto then autoReset() end
	elseif id == "emote" then
		Keys.tap(Enum.KeyCode.T) -- (the emote wheel's key: FlairClient opens its touch wheel for a touch press)
	else
		releaseAll()
		Keys.tap(Enum.KeyCode.P)
	end
end

local function newFace(parent: Instance, name: string, label: string, round: boolean): TextButton
	local f = T.new("TextButton", {
		Name = name, AutoButtonColor = false, AnchorPoint = Vector2.new(0.5, 0.5), BackgroundColor3 = T.BG,
		BorderSizePixel = 0, Text = label, FontFace = T.FONT_HEAVY, TextSize = 12, TextColor3 = T.TEXT, Selectable = false,
	}, parent) :: TextButton
	if round then T.new("UICorner", { CornerRadius = UDim.new(0.5, 0) }, f) else T.corner(f, 8) end
	T.edge(f)
	return f
end

local function build()
	readSettings()
	built = true
	gui = T.new("ScreenGui", { Name = "JankTouch", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 5,
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling, Enabled = false }, pg) :: ScreenGui
	gui.ScreenInsets = Enum.ScreenInsets.DeviceSafeInsets -- (clear of notches and the home bar)
	pad = T.new("Frame", { Name = "Pad", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, gui) :: Frame
	local fullGui = T.new("ScreenGui", { Name = "JankTouchFull", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 0 }, pg) :: ScreenGui
	fullGui.ScreenInsets = Enum.ScreenInsets.None
	full = T.new("Frame", { Name = "Full", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, fullGui) :: Frame

	-- the stick: a thin ring and a knob. resting (faint) on the left; live where the thumb lands
	stickRing = T.new("Frame", { Name = "Stick", AnchorPoint = Vector2.new(0.5, 0.5), BackgroundColor3 = T.BG,
		BackgroundTransparency = 0.8, Size = UDim2.fromOffset(104, 104) }, pad) :: Frame
	T.new("UICorner", { CornerRadius = UDim.new(0.5, 0) }, stickRing)
	T.edge(stickRing, T.EDGE, 0.55, 2)
	stickKnob = T.new("Frame", { Name = "Knob", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
		BackgroundColor3 = T.TEXT, BackgroundTransparency = 0.5, Size = UDim2.fromOffset(46, 46) }, stickRing) :: Frame
	T.new("UICorner", { CornerRadius = UDim.new(0.5, 0) }, stickKnob)

	for _, b in BTNS do
		local face = newFace(pad, b.id, b.label, true)
		local sc = T.new("UIScale", {}, face) :: UIScale
		b.face, b.scale = face, sc
		b.stroke = face:FindFirstChildOfClass("UIStroke") :: UIStroke
		face.InputBegan:Connect(function(io: InputObject)
			if io.UserInputType ~= Enum.UserInputType.Touch and io.UserInputType ~= MB1 then return end
			if not active or settingsOpen() then return end
			fingers[fingerKey(io)] = { kind = "btn", id = b.id, last = Vector2.new(io.Position.X, io.Position.Y) }
			btnDown(b)
		end)
	end

	-- the top row, fire side: EMOTE, AUTO and SETTINGS
	topRow = T.new("Frame", { Name = "Top", AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -16, 0, 12),
		BackgroundTransparency = 1, AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 34) }, pad) :: Frame
	T.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, HorizontalAlignment = Enum.HorizontalAlignment.Right,
		Padding = UDim.new(0, 8), SortOrder = Enum.SortOrder.LayoutOrder }, topRow)
	for i, p in { { "emote", "EMOTE" }, { "auto", "AUTO" }, { "settings", "SETTINGS" } } do
		local f = newFace(topRow, p[1], p[2], false)
		f.AnchorPoint = Vector2.zero
		f.LayoutOrder = i
		f.AutomaticSize = Enum.AutomaticSize.X
		T.new("UIPadding", { PaddingLeft = UDim.new(0, 14), PaddingRight = UDim.new(0, 14) }, f)
		pills[p[1]] = { face = f, lit = false }
		f.Activated:Connect(function() pillPress(p[1]) end)
	end

	-- the weapon chips (slots 1-3), bottom middle; the ammo plate and the item plate stack over them (moved there
	-- on a phone: the corner is the thumb's, like the web's touch.css)
	chips = T.new("Frame", { Name = "Chips", AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, -24),
		Size = UDim2.fromOffset(312, 30), BackgroundTransparency = 1 }, pad) :: Frame
	T.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, HorizontalAlignment = Enum.HorizontalAlignment.Center,
		Padding = UDim.new(0, 6), SortOrder = Enum.SortOrder.LayoutOrder }, chips)
	for i = 1, 3 do
		local f = newFace(chips, "Slot" .. i, "", false)
		f.AnchorPoint = Vector2.zero
		f.LayoutOrder = i
		f.Size = UDim2.fromOffset(100, 30)
		f.TextSize = 11
		f.FontFace = T.FONT_BOLD
		f.TextTruncate = Enum.TextTruncate.AtEnd
		T.new("UIPadding", { PaddingLeft = UDim.new(0, 6), PaddingRight = UDim.new(0, 6) }, f)
		f.Activated:Connect(function() if active and not settingsOpen() then Keys.tap(SLOT_KEYS[i]) end end)
	end
	applyLook()
end

-- ---------------------------------------------------------------- touches on the screen (not on a button)
local function safeRect(): (Vector2, Vector2)
	if built then return pad.AbsolutePosition, pad.AbsoluteSize end
	return Vector2.zero, viewport()
end
local function uiLive(): boolean
	return active and built and gui.Enabled and not settingsOpen()
end
UIS.InputBegan:Connect(function(io: InputObject, gp: boolean)
	if io.UserInputType ~= Enum.UserInputType.Touch or gp or not uiLive() then return end
	local pos = Vector2.new(io.Position.X, io.Position.Y)
	local o, sz = safeRect()
	local stickSide = if S.lefty then pos.X > o.X + sz.X * 0.58 else pos.X < o.X + sz.X * 0.42
	if mv.finger == nil and stickSide then
		mv.finger = io
		mv.ox, mv.oy = pos.X, pos.Y
		fingers[io] = { kind = "stick", last = pos }
		stickRing:SetAttribute("Live", true)
		stickRing.Position = UDim2.fromOffset(pos.X - o.X, pos.Y - o.Y)
	else
		fingers[io] = { kind = "look", last = pos }
	end
end)
UIS.InputChanged:Connect(function(io: InputObject)
	local t = io.UserInputType
	if t ~= Enum.UserInputType.Touch and t ~= Enum.UserInputType.MouseMovement then return end
	local key: any = if t == Enum.UserInputType.Touch then io else "mouse"
	local f = fingers[key]
	if not f then return end
	local pos = Vector2.new(io.Position.X, io.Position.Y)
	if f.kind == "stick" then stickMove(pos); return end
	local b = f.id and byId[f.id]
	if f.kind == "look" or (b and b.look) then lookAcc += pos - f.last end
	f.last = pos
end)
UIS.InputEnded:Connect(function(io: InputObject)
	local t = io.UserInputType
	if t ~= Enum.UserInputType.Touch and t ~= MB1 then return end
	local k = if t == Enum.UserInputType.Touch then io else "mouse"
	local f = fingers[k]
	if not f then return end
	fingers[k] = nil
	if f.kind == "btn" and f.id and byId[f.id] then btnUp(byId[f.id])
	elseif f.kind == "box" and f.id and boxUp[f.id] then boxUp[f.id]()
	elseif f.kind == "stick" then stickEnd() end
end)

-- ---------------------------------------------------------------- moving: the control module's own path
-- (the keyboard's: Move.client.luau hooks moveFunction to know the keys are fresh, then reads the Humanoid's
-- MoveDirection. the vector is made world-relative the way the control module does it)
local function worldMove(v: Vector3): Vector3
	local cam = workspace.CurrentCamera
	if not cam or v.Magnitude == 0 then return v end
	local _, _, _, R00, R01, R02, _, _, R12, _, _, R22 = cam.CFrame:GetComponents()
	local c, s
	if R12 < 1 and R12 > -1 then c, s = R22, R02 else c, s = R00, -R01 * math.sign(R12) end
	local n = math.sqrt(c * c + s * s)
	return Vector3.new((c * v.X + s * v.Z) / n, 0, (c * v.Z - s * v.X) / n)
end
-- (just after the control module's own step: a stick that's pushed wins. let go, it says "stopped" for a few frames
-- and then stays quiet, so nothing else's input is drowned out)
local idleFrames = 0
RunService:BindToRenderStep("JankTouchMove", Enum.RenderPriority.Input.Value + 1, function()
	if not active or not controls or type(controls.moveFunction) ~= "function" then return end
	if testStick then
		local v = testStick :: Vector2
		stickSet(v.X, v.Y, math.min(1, v.Magnitude))
	end
	local x = (if mv.r then 1 else 0) - (if mv.l then 1 else 0)
	local z = (if mv.b then 1 else 0) - (if mv.f then 1 else 0)
	local v = Vector3.new(x, 0, z)
	if v.Magnitude > 0 then v = v.Unit end
	if menuOpen() then v = Vector3.zero end
	if v.Magnitude == 0 then
		idleFrames += 1
		if idleFrames > 3 then return end
	else
		idleFrames = 0
	end
	pcall(controls.moveFunction, me, worldMove(v), false)
end)

-- ---------------------------------------------------------------- aim assist (public/js/aimassist.js, its rules and numbers kept)
-- thumbs on glass can't track like a mouse: near an enemy your look slows a bit and the crosshair gets a gentle tug
-- toward their body. only enemies (never your Team), only in plain sight (the map ray bullets use), only inside a small
-- ring round the crosshair at a capped turn rate, only while your thumbs are doing something, the body never the head,
-- and it only turns YOUR camera: hits are still the server's
local RING = 0.14 -- rad: enemies inside this ring slow your look (about 8 degrees)
local PULL = 0.085 -- rad: ...and inside this one the crosshair gets tugged
local RANGE = 90 * SM
local RATE = 0.38 -- rad/s: the fastest the tug ever turns you, at full strength
local AS = { t = nil :: any, at = -1, activeUntil = 0 }
local assistParams = RaycastParams.new()
assistParams.FilterType = Enum.RaycastFilterType.Include
local function wrapA(a: number): number
	while a > math.pi do a -= 2 * math.pi end
	while a < -math.pi do a += 2 * math.pi end
	return a
end
-- how far the sights are up (Arsenal: the view is base / (1 + (zoom - 1) * aim)) and the held gun's zoom
local function aimState(): (number, number)
	local w = W[heldWeapon() or ""]
	local cam = workspace.CurrentCamera
	if not w or not w.ads or not cam then return 0, 1 end
	local z = tonumber(w.ads.zoom) or 1
	if z <= 1 then return 0, 1 end
	local base = tonumber(me:GetAttribute("BaseFov")) or 80
	return math.clamp((base / cam.FieldOfView - 1) / (z - 1), 0, 1), z
end
local function assistOk(): boolean
	return active and fightZone() and not menuOpen() and not settingsOpen() and alive() ~= nil
end
-- the enemy nearest the crosshair, in sight: { ang, size, zoom, yawErr, pitchErr } or nil. worked out once per frame
local function assistTarget(now: number): any
	if AS.at == now then return AS.t end
	AS.at, AS.t = now, nil
	local cam = workspace.CurrentCamera
	if not cam then return nil end
	local e, l = cam.CFrame.Position, cam.CFrame.LookVector
	local aim, z = aimState()
	local zoom = if aim > 0.5 then math.max(1, z) else 1
	local yaw, pitch = math.atan2(-l.X, -l.Z), math.asin(math.clamp(l.Y, -1, 1))
	local myTeam = me:GetAttribute("Team")
	local map = workspace:FindFirstChild("Map")
	if map then assistParams.FilterDescendantsInstances = { map } end
	local best, bestAng = nil, math.huge
	local function try(m: Model, pl: Player?)
		if pl and myTeam ~= nil and pl:GetAttribute("Team") == myTeam then return end
		local hum = m:FindFirstChildOfClass("Humanoid")
		local root = m:FindFirstChild("HumanoidRootPart") :: BasePart?
		if not hum or not root or hum.Health <= 0 then return end
		local c = Hitbox.feet(root.Position) + Vector3.new(0, Weapons.BOX.bodyTop / 2, 0) -- (the body box's middle: never the head)
		local to = c - e
		local d = to.Magnitude
		if d > RANGE or d < 0.8 * SM then return end
		local dir = to / d
		local size = math.atan2(0.45 * SM, d) -- how wide the body looks from here: up close the ring grows with them
		local ang = math.acos(math.clamp(dir:Dot(l), -1, 1))
		if ang > (RING + size) / zoom or ang >= bestAng then return end -- (scoped in, the ring shrinks with the zoom)
		if map and workspace:Raycast(e, to, assistParams) then return end -- a wall in the way: not a target
		bestAng = ang
		best = { ang = ang, size = size, zoom = zoom, yawErr = wrapA(math.atan2(-dir.X, -dir.Z) - yaw), pitchErr = math.asin(dir.Y) - pitch }
	end
	for _, pl in Players:GetPlayers() do if pl ~= me and pl.Character then try(pl.Character, pl) end end
	local dm = workspace:FindFirstChild("Dummies")
	if dm then for _, m in dm:GetChildren() do if m:IsA("Model") then try(m, nil) end end end
	AS.t = best
	return best
end
-- every drag goes through this: how much to slow the turn right now (1 = not at all)
local function assistSlow(now: number): number
	AS.activeUntil = now + 0.35 -- (a thumb is steering)
	if S.assist <= 0 or not assistOk() then return 1 end
	local t = assistTarget(now)
	if not t then return 1 end
	local close = 1 - math.min(1, t.ang / ((RING + t.size) / t.zoom)) -- 0 at the rim of the ring, 1 dead on
	return 1 - math.min(0.6, 0.55 * S.assist) * (0.35 + 0.65 * close)
end
-- every frame: the tug (yaw, pitch to add)
local function assistTug(dt: number, now: number): (number, number)
	if S.assist <= 0 or not assistOk() then AS.t, AS.at = nil, now; return 0, 0 end
	local t = assistTarget(now)
	if not t or now > AS.activeUntil then return 0, 0 end
	local zone = (PULL + t.size) / t.zoom
	if t.ang > zone or t.ang < 0.004 then return 0, 0 end -- too far for a tug, or already on them
	local fall = 1 - t.ang / zone -- strongest near the middle, nothing at the rim: no yank when someone runs into the ring
	local step = math.min(t.ang * 0.5, RATE * math.min(1.5, S.assist) * (0.3 + 0.7 * fall) * dt / t.zoom)
	local f = step / t.ang
	return t.yawErr * f, t.pitchErr * f
end

-- ---------------------------------------------------------------- looking
-- the web's rate (main.js: 0.0088 rad per finger point x the look speed; sights up past half way: x the ADS speed /
-- the zoom; x the aim assist's slow-down), plus the assist's tug. turned as a change from this frame's look, after the
-- camera module and the gun's kick (Camera + 2), so the camera reads it back next frame like everything else that
-- moves it
RunService:BindToRenderStep("JankTouchLook", Enum.RenderPriority.Camera.Value + 2, function(dt: number)
	local d = lookAcc
	lookAcc = Vector2.zero
	if not active then return end
	local cam = workspace.CurrentCamera
	if not cam or cam.CameraType ~= Enum.CameraType.Custom then return end
	local now = os.clock()
	local yawD, pitchD = 0, 0
	if d.X ~= 0 or d.Y ~= 0 then
		local aim, z = aimState()
		local k = 0.0088 * S.sens * (if aim > 0.5 then (tonumber(get("look.ads")) or 1) / z else 1) * assistSlow(now)
		yawD, pitchD = -d.X * k, -d.Y * k
	end
	if mv.f or mv.b or mv.l or mv.r then AS.activeUntil = now + 0.35 end -- (the stick counts as doing something too)
	local ty, tp = assistTug(math.min(dt, 0.1), now)
	yawD += ty
	pitchD += tp
	if yawD == 0 and pitchD == 0 then return end
	local cf = cam.CFrame
	local pitch = math.asin(math.clamp(cf.LookVector.Y, -1, 1))
	local want = math.clamp(pitch + pitchD, -math.rad(80), math.rad(80))
	cam.CFrame = CFrame.new(cf.Position) * CFrame.fromAxisAngle(Vector3.yAxis, yawD) * cf.Rotation * CFrame.Angles(want - pitch, 0, 0)
end)

-- ---------------------------------------------------------------- auto fire (public/js/autofire.js, its rules kept)
-- presses the same fire key as FIRE after a short human-ish delay, so every weapon's own rules (rate, ammo, reloads:
-- Arsenal reloads an empty gun when its trigger is pulled, the server's hit checks) apply as if a thumb did it
local PAD = 0.12 * SM -- thumbs aren't pixel perfect: the crosshair counts a hair outside the hit box
local MANUAL: { [string]: boolean } = {} -- (web: the cig and the lasso, yours to time; none of those here yet)
type Rule = { mode: string, range: number, scope: boolean?, grace: number? }
local function ruleFor(id: string): Rule?
	local w = W[id]
	if not w or MANUAL[id] then return nil end
	if w.kind == "hitscan" then
		return { mode = if w.auto or w.spinup then "hold" else "tap", range = math.min(w.range or 150 * SM, 150 * SM),
			scope = w.ads ~= nil and w.ads.scope == true, grace = if w.spinup then 0.6 else 0.17 }
	end
	if w.kind == "melee" then return { mode = "tap", range = math.max(1.2 * SM, (w.range or 2.5 * SM) - 0.35 * SM) } end
	if w.kind == "cone" then return { mode = "hold", range = (w.range or 10 * SM) * 0.85, grace = 0.2 } end
	if w.kind == "proj" then return { mode = if w.auto then "hold" else "tap", range = 40 * SM, grace = 0.17 } end
	if w.kind == "bow" then return { mode = "draw", range = 70 * SM } end
	if w.kind == "beam" then return { mode = "hold", range = w.range or 100 * SM, grace = 0.25 } end
	if w.kind == "zap" then return { mode = "tap", range = (w.range or 9 * SM) * 0.95 } end
	return nil
end
local mapParams = RaycastParams.new()
mapParams.FilterType = Enum.RaycastFilterType.Include
-- the enemy under the crosshair: the nearest hit box (the game's own two boxes) the look ray touches, nothing solid
-- in between. a friend (same Team) never counts
local function underCrosshair(maxT: number): (Model?, number?)
	local cam = workspace.CurrentCamera
	if not cam then return nil end
	local o, d = cam.CFrame.Position, cam.CFrame.LookVector
	local myTeam = me:GetAttribute("Team")
	local best: Model?, bestT: number? = nil, nil
	local function try(m: Model, isPlayer: Player?)
		if isPlayer and myTeam ~= nil and isPlayer:GetAttribute("Team") == myTeam then return end
		local hum = m:FindFirstChildOfClass("Humanoid")
		local root = m:FindFirstChild("HumanoidRootPart") :: BasePart?
		if not hum or not root or hum.Health <= 0 then return end
		local feet = Hitbox.feet(root.Position)
		local dx, dz = feet.X - o.X, feet.Z - o.Z
		if dx * dx + dz * dz > (maxT + 9) * (maxT + 9) then return end
		local k = Hitbox.distScale((feet - o).Magnitude)
		local t = Hitbox.ray(o, d, feet, k, PAD)
		if t and t <= maxT and (not bestT or t < bestT) then best, bestT = m, t end
	end
	for _, p in Players:GetPlayers() do
		if p ~= me and p.Character then try(p.Character, p) end
	end
	local dm = workspace:FindFirstChild("Dummies")
	if dm then for _, m in dm:GetChildren() do if m:IsA("Model") then try(m, nil) end end end
	if not best or not bestT then return nil end
	local map = workspace:FindFirstChild("Map")
	if map then
		mapParams.FilterDescendantsInstances = { map }
		local wall = workspace:Raycast(o, d * bestT, mapParams)
		if wall and wall.Distance < bestT - PAD * 2 then return nil end
	end
	return best, bestT
end
local function scoped(id: string): boolean
	local w = W[id]
	local cam = workspace.CurrentCamera
	if not w or not w.ads or not cam then return false end
	local base = tonumber(me:GetAttribute("BaseFov")) or 80
	return cam.FieldOfView <= base / (1 + (w.ads.zoom - 1) * 0.9)
end
local A = { on = false, since = 0, seenAt = -1e9, react = 0, holding = false, upAt = 0, nextTap = 0, drawAt = 0, id = "" }
local function release()
	if A.holding then A.holding = false; Keys.press(MB1, false) end
	A.upAt = 0
end
autoReset = function() release(); A.on = false end
local function autoFrame(now: number)
	if not active or not S.auto or fireThumb or not fightZone() or menuOpen() or settingsOpen() or not alive() then autoReset(); return end
	local id = heldWeapon() or ""
	local w, rule = W[id], ruleFor(id)
	if id ~= A.id then autoReset(); A.id = id; A.nextTap = now + 0.22 end -- a new gun out: let it come up first
	if not rule or not w then return end
	local hit = underCrosshair(rule.range)
	local valid = hit ~= nil and (not rule.scope or scoped(id)) -- snipers: scoped in or it's on you (no-scopes stay a skill)
	if valid then
		if not A.on then -- a fresh target: a blink before the first shot
			A.on = true
			if now - A.seenAt > 0.3 then A.since = now; A.react = 0.12 + math.random() * 0.14 end
		end
		A.seenAt = now
	elseif A.on and now - A.seenAt > (rule.grace or 0) then
		A.on = false
	end
	local armed = A.on and now - A.since >= A.react
	if rule.mode == "hold" then
		if armed and not A.holding then A.holding = true; Keys.press(MB1, true)
		elseif not armed and A.holding then release() end
	elseif rule.mode == "tap" then
		if A.holding and now >= A.upAt then release() end
		if armed and valid and not A.holding and now >= A.nextTap then
			A.holding = true; Keys.press(MB1, true)
			A.upAt = now + 0.06 + math.random() * 0.04
			A.nextTap = now + math.max(if w.rate then 1 / w.rate else 0, 0.14) + 0.03 + math.random() * 0.07 -- a finger, not a metronome
		end
	elseif rule.mode == "draw" then
		if not A.holding and armed and valid and now >= A.nextTap then A.holding = true; A.drawAt = now; Keys.press(MB1, true)
		elseif A.holding and now - A.drawAt > 2.6 then release(); A.nextTap = now + 0.25 end
	end
end

-- ---------------------------------------------------------------- the HUD's boxes on a phone
-- FightHud's ammo plate and Utility's item plate move to the bottom middle over the weapon chips; each gets a clear
-- button laid over it (ammo: reload; item: G for as long as you hold it). put back when touch goes off
local moved: { [GuiObject]: UDim2 } = {}
local overlays: { [string]: TextButton } = {}
boxUp = {}
local function placeHudBox(name: string, pos: UDim2, onDown: () -> (), onUp: (() -> ())?)
	if onUp then boxUp[name] = onUp end
	local fight = pg:FindFirstChild("JankfireFight")
	local sc = fight and fight:FindFirstChild("Scaled")
	local plate = sc and sc:FindFirstChild(name)
	if not plate or not plate:IsA("GuiObject") then return end
	if not moved[plate] then moved[plate] = plate.Position end
	if plate.Position ~= pos then plate.Position = pos end
	if not overlays[name] or overlays[name].Parent ~= plate then
		local b = T.new("TextButton", { Name = "TouchTap", BackgroundTransparency = 1, Text = "", Size = UDim2.fromScale(1, 1),
			ZIndex = 20, Selectable = false }, plate) :: TextButton
		b.InputBegan:Connect(function(io: InputObject)
			if io.UserInputType ~= Enum.UserInputType.Touch and io.UserInputType ~= MB1 then return end
			if not active or settingsOpen() then return end
			fingers[fingerKey(io)] = { kind = "box", id = name, last = Vector2.new(io.Position.X, io.Position.Y) }
			onDown()
		end)
		overlays[name] = b
	end
end

-- the hub's buttons (QUESTS, PLAY, PARTY, PROFILE, SHOP, LOADOUT: the left-hand stack) go to the right side, same order
local HUB = { { "JankQuestsButton", nil }, { "JankPlayButton", "Play" }, { "JankPlayButton", "Party" },
	{ "JankProfileButton", "Profile" }, { "JankShopButton", "Shop" }, { "JankLoadoutButton", nil } }
local function hubButton(gname: string, child: string?): GuiObject?
	local g = pg:FindFirstChild(gname)
	local sc = g and g:FindFirstChild("Scaled")
	if not sc then return nil end
	if child then
		local c = sc:FindFirstChild(child)
		return if c and c:IsA("GuiObject") then c else nil
	end
	for _, c in sc:GetChildren() do if c:IsA("GuiObject") then return c end end -- (LoadoutUI's: a holder frame)
	return nil
end
local function placeHub(mode: string?) -- "hub": the right side; "away": off the screen (a fight outside a match)
	for _, h in HUB do
		local o = hubButton(h[1], h[2])
		if o then
			if mode == "away" then
				if not moved[o] then moved[o] = o.Position end
				local want = UDim2.new(0, -4000, moved[o].Y.Scale, moved[o].Y.Offset)
				if o.Position ~= want then o.Position = want end
			elseif mode == "hub" then
				if not moved[o] then moved[o] = o.Position end
				local orig = moved[o]
				-- right edge 160 points in from the right (JUMP, SLIDE and HOOK keep the corner), 76 lower than on the left
				local ts = S.size
				local ri, bi = insets()
				local want = UDim2.new(1, -(ri + 160 * ts) / T.scaleNow() - o.Size.X.Offset, orig.Y.Scale, orig.Y.Offset + 76 - bi / T.scaleNow())
				if o.Position ~= want then o.Position = want end
			elseif moved[o] then
				o.Position = moved[o]
				moved[o] = nil
			end
		end
	end
end

local function putBack()
	for o, p in moved do if o.Parent then o.Position = p end end
	table.clear(moved)
	for _, b in overlays do b:Destroy() end
	table.clear(overlays)
end

-- ---------------------------------------------------------------- on / off
local function hookModules()
	if controls and cameraInput then return end
	local pm = me:FindFirstChild("PlayerScripts") and (me :: any).PlayerScripts:FindFirstChild("PlayerModule")
	if not pm then return end
	if not controls then
		local ok, c = pcall(function() return (require(pm :: any) :: any):GetControls() end)
		if ok and type(c) == "table" then controls = c end
	end
	if not cameraInput then
		local cm = pm:FindFirstChild("CameraModule")
		local ci = cm and cm:FindFirstChild("CameraInput")
		if ci and ci:IsA("ModuleScript") then
			local ok, m = pcall(require, ci)
			if ok and type(m) == "table" and type((m :: any).getRotation) == "function" then
				cameraInput = m
				origRotation = (m :: any).getRotation
				-- the camera module's own touch turning is off while these controls are on (it would turn the camera a
				-- second time, at its own speed, from the same finger). a phone has no mouse or stick to lose
				;(m :: any).getRotation = function(...)
					if active then return Vector2.zero end
					return origRotation(...)
				end
			end
		end
	end
end

local function setActive(on: boolean)
	if on == active then return end
	active = on
	if on then
		if not built then build() end
		hookModules()
		pcall(function() GuiService.TouchControlsEnabled = false end)
		pcall(function() (me :: any).DevTouchMovementMode = Enum.DevTouchMovementMode.Scriptable end)
	else
		releaseAll()
		putBack()
		if built then gui.Enabled = false; chips.Visible = false; chips.Parent = pad end
		pcall(function() GuiService.TouchControlsEnabled = true end)
		pcall(function() (me :: any).DevTouchMovementMode = Enum.DevTouchMovementMode.UserChoice end)
		local sg = pg:FindFirstChild("JankSettings")
		local hint = sg and sg:FindFirstChild("Scaled") and (sg :: any).Scaled:FindFirstChild("Hint")
		if hint then hint.Visible = true end
	end
	me:SetAttribute("TouchOn", on)
end

-- ---------------------------------------------------------------- every frame: what shows
local lastWeapon: string? = nil
local lastLo = ""
RunService.Heartbeat:Connect(function()
	local want = Keys.isTouch()
	if want ~= active then setActive(want) end
	if not active or not built then return end
	if readSettings() then applyLook() end
	if not controls or not cameraInput then hookModules() end
	local ch = alive()
	local z = zone()
	local hub = z == "hub" or z == nil
	local fight = fightZone()
	local shown = ch ~= nil and not menuOpen()
	if gui.Enabled ~= shown then
		gui.Enabled = shown
		if not shown then releaseAll() end
	end
	if not fight and aimOn then setAim(false) end
	-- the settings panel's reminder ("P settings") goes: the SETTINGS button is here
	local sg = pg:FindFirstChild("JankSettings")
	local hint = sg and sg:FindFirstChild("Scaled") and (sg :: any).Scaled:FindFirstChild("Hint")
	if hint and hint.Visible then hint.Visible = false end
	-- an emote or a replay owns the camera: nothing to press but SETTINGS
	local cam = workspace.CurrentCamera
	local watching = cam ~= nil and cam.CameraType == Enum.CameraType.Scriptable and me:GetAttribute("Emote") == nil
	local kat, edgeFull = heldWeapon() == "katana", me:GetAttribute("EdgeFull") == true
	local yt = me:GetAttribute("YankT")
	local onBody = me:GetAttribute("HookBody") == true and not (type(yt) == "number" and workspace:GetServerTimeNow() < yt)
	for _, b in BTNS do
		local vis = (fight or not b.fight) and not watching and (not b.katana or kat) and (not b.body or onBody)
		if b.face.Visible ~= vis then b.face.Visible = vis end
		local lit = (b.id == "aim" and aimOn) or (b.id == "wave" and edgeFull)
		if lit ~= b.lit or b.face.BackgroundColor3 ~= (if lit then T.ACCENT else T.BG) then b.lit = lit; style(b.face, lit, b.id == "fire") end
	end
	local autoP = pills.auto
	autoP.face.Visible = fight
	if autoP.lit ~= S.auto then autoP.lit = S.auto; style(autoP.face, S.auto) end
	stickRing.Visible = not watching
	if not stickRing:GetAttribute("Live") then
		local ts = S.size
		local _, sz = safeRect()
		stickRing.Position = UDim2.fromOffset(100 * ts, sz.Y - 170 * ts)
		stickRing.BackgroundTransparency = 1 - 0.2 * S.alpha * 0.55
		stickKnob.BackgroundTransparency = 1 - 0.5 * S.alpha * 0.55
	else
		stickRing.BackgroundTransparency = 1 - 0.2 * S.alpha
		stickKnob.BackgroundTransparency = 1 - 0.5 * S.alpha
	end
	-- the weapon chips sit in the HUD's own frame, so they line up with the plates moved over them; names from your
	-- loadout, the one in your hands marked
	local fightGui = pg:FindFirstChild("JankfireFight")
	local hudFrame = fightGui and fightGui:FindFirstChild("Scaled")
	if hudFrame and chips.Parent ~= hudFrame then chips.Parent = hudFrame end
	local l = lo()
	local held = heldWeapon()
	if held ~= lastWeapon then
		if held and held ~= swapHist.cur then swapHist.prev = swapHist.cur; swapHist.cur = held end
		lastWeapon = held
		if aimOn then setAim(false) end -- (a new gun comes up from the hip)
	end
	chips.Visible = shown and fight and not watching
	local key = table.concat(l, ",") .. "|" .. tostring(held)
	if key ~= lastLo then
		lastLo = key
		for i = 1, 3 do
			local f = chips:FindFirstChild("Slot" .. i) :: TextButton?
			if f then
				local w = W[l[i]]
				f.Text = if w then string.upper(w.name) else ""
				local on = l[i] == held
				f.BackgroundColor3 = T.BG
				f.BackgroundTransparency = if on then 0.1 else 1 - 0.72 * S.alpha
				f.TextColor3 = if on then T.TEXT else T.SOFT
				local st = f:FindFirstChildOfClass("UIStroke")
				if st then st.Color = if on then T.ACCENT else T.EDGE; st.Transparency = if on then 0.2 else T.EDGE_A end
			end
		end
	end
	-- the HUD boxes, over the chips (design pixels of the HUD's own scaled frame), in every zone (the hub has a
	-- holstered ammo plate too); the speed readout goes up over the health plate, clear of the chips
	placeHudBox("Ammo", UDim2.new(0.5, -116, 1, -24 - 30 - 6 - 64), function() Keys.tap(Enum.KeyCode.R) end)
	placeHudBox("Utility", UDim2.new(0.5, -116, 1, -24 - 30 - 6 - 64 - 6 - 42), function() itemPress(true) end, function() itemPress(false) end)
	local hudGui = pg:FindFirstChild("JankfireHud")
	local speed = hudGui and hudGui:FindFirstChild("Scaled") and (hudGui :: any).Scaled:FindFirstChild("Speed")
	if speed and speed:IsA("GuiObject") then
		if not moved[speed] then moved[speed] = speed.Position end
		local want = UDim2.new(0, 24, 1, -88 - 8 - 64)
		if speed.Position ~= want then speed.Position = want end
	end
	placeHub(if hub then "hub" elseif fight then "away" else nil)
end)

RunService.RenderStepped:Connect(function()
	if active then autoFrame(os.clock()) end
end)
me.CharacterAdded:Connect(function() releaseAll() end)
me:GetAttributeChangedSignal("LoadoutOpen"):Connect(function() if menuOpen() then releaseAll() end end)
me:GetAttributeChangedSignal("Zone"):Connect(function() releaseAll() end)

-- ---------------------------------------------------------------- test hook (Play tests driven from Studio)
me:GetAttributeChangedSignal("TouchTest"):Connect(function()
	local v = me:GetAttribute("TouchTest")
	if type(v) ~= "string" or v == "" then return end
	me:SetAttribute("TouchTest", nil)
	local cmd, a = string.match(v, "^(%a+):?(.*)$")
	local b = byId[a or ""]
	if cmd == "down" and b then btnDown(b)
	elseif cmd == "up" and b then btnUp(b)
	elseif cmd == "tap" and b then btnDown(b); task.delay(0.12, function() btnUp(b) end)
	elseif cmd == "stick" then
		local x, y = string.match(a or "", "^(-?[%d%.]+),(-?[%d%.]+)$")
		local vx, vy = tonumber(x) or 0, tonumber(y) or 0
		if vx == 0 and vy == 0 then testStick = nil; stickEnd()
		elseif built then
			testStick = Vector2.new(vx, vy)
			-- (drawn as a thumb would push it, where the stick rests)
			local r = 52 * S.size
			local m = math.max(1, Vector2.new(vx, vy).Magnitude)
			stickRing:SetAttribute("Live", true)
			stickKnob.Position = UDim2.new(0.5, vx / m * r * 0.62, 0.5, vy / m * r * 0.62)
		end
	elseif cmd == "look" then
		local x, y = string.match(a or "", "^(-?[%d%.]+),(-?[%d%.]+)$")
		lookAcc += Vector2.new(tonumber(x) or 0, tonumber(y) or 0)
	elseif cmd == "chip" then
		local i = tonumber(a)
		if i and SLOT_KEYS[i] then Keys.tap(SLOT_KEYS[i]) end
	elseif cmd == "item" then itemPress(a == "down")
	elseif cmd == "ammo" then Keys.tap(Enum.KeyCode.R)
	elseif cmd == "auto" then S.auto = a ~= "off"; set("touch.autofire", S.auto); autoReset()
	elseif cmd == "settings" then releaseAll(); Keys.tap(Enum.KeyCode.P)
	elseif cmd == "pill" then pillPress(a or "")
	elseif cmd == "assist" then set("touch.assist", tonumber(a) or 1)
	elseif cmd == "fake" then
		local w, h = string.match(a or "", "^(%d+)x(%d+)$")
		fakeScreen(if w then Vector2.new(tonumber(w) :: number, tonumber(h) :: number) else nil)
	elseif cmd == "real" then fakeScreen(nil)
	elseif cmd == "state" then
		local cam = workspace.CurrentCamera
		me:SetAttribute("TouchState", HttpService:JSONEncode({
			active = active, shown = built and gui.Enabled, aim = aimOn, auto = S.auto, autoHolding = A.holding, autoOn = A.on,
			held = heldWeapon(), prev = swapHist.prev, sens = S.sens, size = S.size, alpha = S.alpha, aimToggle = S.aim,
			move = { mv.f, mv.b, mv.l, mv.r, mv.sprint }, controls = controls ~= nil, camInput = cameraInput ~= nil,
			touchCtl = GuiService.TouchControlsEnabled, look = cam and { cam.CFrame.LookVector.X, cam.CFrame.LookVector.Y, cam.CFrame.LookVector.Z },
			assist = AS.t and math.floor(math.deg(AS.t.ang) * 10) / 10, assistK = S.assist,
			fingers = (function() local n = 0; for _ in fingers do n += 1 end; return n end)(),
		}))
	end
end)
