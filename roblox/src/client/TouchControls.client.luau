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
--   * the layout is the player's (18 Nov, TouchLayout.luau + the editor TouchEdit.client, opened from Settings): every
--     button, the stick, the top row and the weapon / health boxes can be moved, sized, faded, hidden or given another
--     action, and extra buttons added; three layouts per player in their settings save. the defaults are the web's
--   * a phone (short side under 600 points) gets a compact HUD: the fight HUD's guis drawn smaller (Theme.guiK), the
--     weapon box (item, ammo, slot chips) small at the bottom left of the middle, clear of the gun; a slim health
--     plate with the speed over it in the corner; the top row slim and moved under the scoreboard if they'd touch;
--     swipe the ammo plate sideways to change weapon (a tap still reloads, on letting go)
-- Test hook (Studio): player attribute TouchForce = true turns it all on with a mouse and keyboard; TouchTest takes
-- "down:<id>", "up:<id>", "tap:<id>", "stick:<x>,<y>" (-1..1, "stick:0,0" lets go), "look:<dx>,<dy>" (points),
-- "chip:<1-3>", "item:down" / "item:up", "ammo", "swipe:<1|-1>", "auto:on|off", "assist:<0-1.5>", "settings", "pill:<emote|auto|settings>", "state" (writes TouchState as JSON), "fake:844x390" (the HUD laid
-- out in a phone-sized box: Studio's device emulator can't be driven from a script), "real". (ids are the layout's:
-- fire, jump, crouch, aim, hook, melee, swap, reload, wave, yank, x1..x6; TouchState's "pressed" is the last action)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local GuiService = game:GetService("GuiService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local HttpService = game:GetService("HttpService")

local Keys = require(script.Parent:WaitForChild("Keys"))
local T = require(script.Parent:WaitForChild("Theme"))
local TL = require(script.Parent:WaitForChild("TouchLayout"))
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
local function fightZone(): boolean local z = zone(); return z == "match" or z == "training" or z == "playground" or me:GetAttribute("DevArms") == true end -- (DevArms: the owner's dev weapons in the hub, OwnerDev)

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
	local s0 = math.max(1, sz.Y / 720)
	local function box(o: GuiObject, k: number)
		local sc = o:FindFirstChildOfClass("UIScale")
		fakeSaved[o] = { o.AnchorPoint, o.Position, o.Size, if sc then sc.Scale else nil }
		o.AnchorPoint, o.Position = Vector2.new(0.5, 0.5), UDim2.fromScale(0.5, 0.5)
		local s = s0 * k
		if sc then sc.Scale = s; o.Size = UDim2.fromOffset(sz.X / s, sz.Y / s) else o.Size = UDim2.fromOffset(sz.X, sz.Y) end
	end
	for _, g in pg:GetChildren() do
		local f = g:IsA("ScreenGui") and g:FindFirstChild("Scaled")
		if f and f:IsA("GuiObject") then box(f, T.hudScale * (T.guiK[g.Name] or 1)) end -- (the phone HUD's own size: phoneScale)
	end
	pad.AnchorPoint, pad.Position, pad.Size = Vector2.new(0.5, 0.5), UDim2.fromScale(0.5, 0.5), UDim2.fromOffset(sz.X, sz.Y)
	local e = T.new("Frame", { Name = "FakeScreen", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(sz.X, sz.Y), BackgroundTransparency = 1 }, full) :: Frame
	T.new("UIStroke", { Color = T.ACCENT, Thickness = 2, Transparency = 0.2 }, e)
	fakeEdge = e
end

-- the buttons come from the player's layout (TouchLayout: the web's places by default; moved, sized, given another
-- action or added in the editor). each knows its layout record and its action: the key it presses and how it behaves.
-- the "wave" button is the katana's slash wave (shown with the katana out, lit with the meter full) and, with the
-- Scythe out, its FORM switch (the same key; you never carry both); "yank" shows while your rope is on a person and
-- the yank is ready (Move.client)
type Btn = { id: string, act: string, A: any, rec: any, face: TextButton, scale: UIScale, stroke: UIStroke, down: boolean, lit: boolean }
local BTNS: { Btn } = {}
local byId: { [string]: Btn } = {}
local lastPress = "" -- (the last action a button pressed: TouchState, for tests)

type Pill = { face: TextButton, lit: boolean, rec: any }
local pills: { [string]: Pill } = {}
local recs: { [string]: any } = {} -- the layout's records by id (buttons, pills, the stick, the boxes)

-- ---------------------------------------------------------------- fingers
-- touch / mouse input -> { kind = "btn" | "look" | "stick", id, last }
type Finger = { kind: string, id: string?, last: Vector2, start: Vector2?, swiped: boolean? }
local fingers: { [any]: Finger } = {}
local boxUp: { [string]: (any) -> () } = {} -- (the HUD boxes' "let go", below: given the finger)
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
	Keys.press(MB2, on) -- (lit on every AIM button: the Heartbeat)
end

local autoReset: () -> () -- (auto fire, below)

local function btnDown(b: Btn)
	if b.down then return end
	b.down = true
	b.scale.Scale = 0.92
	lastPress = b.act
	if b.act == "aim" and S.aim then setAim(not aimOn); return end
	if b.act == "swap" then
		local l = lo()
		local want = swapHist.prev and table.find(l, swapHist.prev)
		if not want then
			local cur = swapHist.cur and table.find(l, swapHist.cur) or 1
			want = if cur == 1 then 2 else 1
		end
		Keys.tap(SLOT_KEYS[want :: number])
		return
	end
	if b.act == "fire" then fireThumb = true; autoReset() end
	local key = b.A and b.A.key
	if key then Keys.press(key, true, b.A.act) end -- (act: that action alone, TouchLayout)
end
local function btnUp(b: Btn)
	if not b.down then return end
	b.down = false
	b.scale.Scale = 1
	if b.act == "aim" and S.aim then return end
	if b.act == "swap" then return end
	if b.act == "fire" then
		fireThumb = false
		for _, o in BTNS do if o ~= b and o.down and o.act == "fire" then fireThumb = true end end -- (two FIRE buttons)
	end
	local key = b.A and b.A.key
	if key then Keys.press(key, false, b.A.act) end
end

local itemDown = false
local function itemPress(down: boolean)
	if down == itemDown then return end
	itemDown = down
	Keys.press(Enum.KeyCode.G, down)
end
-- the next (1) or the one before (-1) of your three, from the one in your hands
local function swipeWeapon(dir: number)
	local l = lo()
	local cur = table.find(l, heldWeapon() or "") or 1
	Keys.tap(SLOT_KEYS[(cur - 1 + dir) % 3 + 1])
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
local function stickR(): number return 52 * S.size * (if recs.stick then recs.stick.s else 1) end -- (the ring's radius)
local function stickFixed(): boolean return recs.stick ~= nil and recs.stick.act == "fixed" end
local function stickMove(pos: Vector2)
	local r = stickR()
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
-- own: this button's own see-through from the layout (x the TOUCH tab's BUTTON OPACITY)
-- (27 Nov 2026, the owner's pick from the ui-mocks sheet: the phone is A PLATE: bone discs with ink words, FIRE an ink
-- disc with a bone rim, a pressed or switched-on button turns ink; the stick a bone ring and knob)
local BONE, INK = Color3.fromRGB(229, 226, 219), Color3.fromRGB(29, 31, 35)
-- (the all-B alternative, ReplicatedStorage UiLook "B": dark slab discs with white words, FIRE Butter)
local ALT = game:GetService("ReplicatedStorage"):GetAttribute("UiLook") == "B"
if ALT then BONE, INK = Color3.fromRGB(13, 14, 16), Color3.fromRGB(240, 240, 236) end
local HUNT_WORDS = { fire = "PUNCH", hook = "PUSH", reel = "LIE" } -- (HOLDOUT's words: placeAll)
local function style(face: TextButton, lit: boolean, accentEdge: boolean?, own: number?)
	local a = math.clamp(S.alpha * (own or 1), 0.1, 1)
	local dark = lit ~= (accentEdge == true) -- (FIRE is ink at rest and bone while held; the rest the other way round)
	face.BackgroundColor3 = if ALT and accentEdge and not lit then Color3.fromRGB(245, 221, 138) elseif dark then INK else BONE
	face.BackgroundTransparency = 1 - a * 0.9
	face.TextColor3 = if ALT and accentEdge and not lit then Color3.fromRGB(16, 17, 19) elseif dark then BONE else INK
	face.TextTransparency = (1 - a) * 0.55
	local st = face:FindFirstChildOfClass("UIStroke")
	if st then
		st.Color = BONE
		st.Thickness = if accentEdge then 3 else 1
		st.Transparency = if accentEdge then 1 - a * 0.95 else 1
	end
end

local function applyLook()
	if not built then return end
	for _, b in BTNS do style(b.face, b.lit, b.act == "fire", b.rec.a) end
	for _, p in pills do style(p.face, p.lit, nil, if p.rec then p.rec.a else 1) end
	if pills.auto then pills.auto.face.Text = if S.auto then "AUTO FIRE ON" else "AUTO FIRE OFF" end -- (27 Nov: its state in words)
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
	elseif id == "board" then
		me:SetAttribute("ScoreboardTouch", me:GetAttribute("ScoreboardTouch") ~= true) -- (the match scoreboard: tap to show, tap to hide)
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
	if round then T.new("UICorner", { CornerRadius = UDim.new(0.5, 0) }, f) else T.corner(f, 3) end
	T.edge(f)
	return f
end
-- the words' size on a round button d points across (a long word a size down)
local function textFor(label: string, d: number): number
	return math.floor(math.clamp(d * 0.19, 9, 14) + 0.5) -- (27 Nov: one size whatever the word's length)
end

-- the buttons, made again from the layout each time it changes (the editor saved, another layout picked)
local function rebuildButtons()
	releaseAll()
	for _, b in BTNS do b.face:Destroy() end
	table.clear(BTNS)
	table.clear(byId)
	table.clear(recs)
	for _, r in TL.active() do
		recs[r.id] = r
		local A = if r.kind == "btn" then TL.ACTIONS[r.act] else nil
		if A then
			local b: any = { id = r.id, act = r.act, A = A, rec = r, down = false, lit = false }
			local face = newFace(pad, r.id, TL.label(r), true)
			b.face, b.scale = face, T.new("UIScale", {}, face)
			b.stroke = face:FindFirstChildOfClass("UIStroke")
			face.InputBegan:Connect(function(io: InputObject)
				if io.UserInputType ~= Enum.UserInputType.Touch and io.UserInputType ~= MB1 then return end
				if not active or settingsOpen() then return end
				fingers[fingerKey(io)] = { kind = "btn", id = b.id, last = Vector2.new(io.Position.X, io.Position.Y) }
				btnDown(b)
			end)
			table.insert(BTNS, b)
			byId[r.id] = b
		elseif r.kind == "pill" and pills[r.id] then
			pills[r.id].rec = r
		end
	end
	applyLook()
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

	-- the stick: a thin ring and a knob. resting (faint) where the layout puts it; live where the thumb lands
	stickRing = T.new("Frame", { Name = "Stick", AnchorPoint = Vector2.new(0.5, 0.5), BackgroundColor3 = INK,
		BackgroundTransparency = 0.86, Size = UDim2.fromOffset(104, 104) }, pad) :: Frame
	T.new("UICorner", { CornerRadius = UDim.new(0.5, 0) }, stickRing)
	T.edge(stickRing, if ALT then Color3.new(1, 1, 1) else BONE, 0.25, 3)
	stickKnob = T.new("Frame", { Name = "Knob", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
		BackgroundColor3 = if ALT then Color3.new(1, 1, 1) else BONE, BackgroundTransparency = 0.1, Size = UDim2.fromOffset(46, 46) }, stickRing) :: Frame
	T.new("UICorner", { CornerRadius = UDim.new(0.5, 0) }, stickKnob)

	-- the top row: SETTINGS, AUTO and EMOTE, each placed on its own (TL.place: right to left along the top, or where
	-- the player put it)
	topRow = T.new("Frame", { Name = "Top", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, pad) :: Frame
	for _, id in { "emote", "auto", "settings", "board" } do
		local f = newFace(topRow, id, TL.base(id).label, false)
		pills[id] = { face = f, lit = false, rec = nil }
		f.Activated:Connect(function() pillPress(id) end)
	end

	-- the weapon chips (slots 1-3): the bottom row of the weapon box (TL "weapon": the item plate, the ammo plate, these),
	-- inside the HUD's own scaled frame so they line up with the plates
	chips = T.new("Frame", { Name = "Chips", Size = UDim2.fromOffset(236, 28), BackgroundTransparency = 1 }, pad) :: Frame
	T.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, HorizontalAlignment = Enum.HorizontalAlignment.Center,
		Padding = UDim.new(0, 4), SortOrder = Enum.SortOrder.LayoutOrder }, chips)
	for i = 1, 3 do
		local f = newFace(chips, "Slot" .. i, "", false)
		f.AnchorPoint = Vector2.zero
		f.LayoutOrder = i
		-- (round 8: each chip as wide as its word, 58 to 112: "ASSAULT RIFLE" didn't fit a third of the row even at 8 px)
		f.Size = UDim2.fromOffset(0, 28); f.AutomaticSize = Enum.AutomaticSize.X
		f.TextSize = 11
		f.FontFace = T.FONT_BOLD
		f.TextWrapped = false
		f.TextTruncate = Enum.TextTruncate.AtEnd
		T.new("UISizeConstraint", { MinSize = Vector2.new(58, 28), MaxSize = Vector2.new(112, 28) }, f)
		T.new("UIPadding", { PaddingLeft = UDim.new(0, 8), PaddingRight = UDim.new(0, 8) }, f)
		f.Activated:Connect(function() if active and not settingsOpen() then Keys.tap(SLOT_KEYS[i]) end end)
	end
	rebuildButtons()
	TL.changed.Event:Connect(function() if built then rebuildButtons() end end)
end

-- ---------------------------------------------------------------- where everything goes (every frame)
-- the safe area's size, and Roblox's own buttons (top left) in its points
local function area(): (number, number, Rect?)
	local sz = pad.AbsoluteSize
	return sz.X, sz.Y, TL.avoid(pad.AbsolutePosition, fake ~= nil)
end
-- the HUD's design pixels to points (its Scaled frame's scale: the screen's, HUD SIZE, a phone's)
local function hudSd(): number
	local g = pg:FindFirstChild("JankfireFight")
	local u = g and g:FindFirstChild("Scaled") and (g :: any).Scaled:FindFirstChildOfClass("UIScale")
	return if u then u.Scale else T.scaleNow() * T.hudScale
end
-- a point in the safe area's points, as a position in a HUD gui's scaled frame (its design pixels)
local function toHud(gname: string, p: Vector2): UDim2?
	local g = pg:FindFirstChild(gname)
	local sc = g and g:FindFirstChild("Scaled")
	local u = sc and sc:FindFirstChildOfClass("UIScale")
	if not sc or not u or not sc:IsA("GuiObject") then return nil end
	local d = pad.AbsolutePosition + p - sc.AbsolutePosition
	return UDim2.fromOffset(math.floor(d.X / u.Scale + 0.5), math.floor(d.Y / u.Scale + 0.5))
end
local stickHome = Vector2.new(100, 220) -- (the stick's resting middle, in the safe area)
local function setIf(o: GuiObject, pos: UDim2, size: UDim2?)
	if o.Position ~= pos then o.Position = pos end
	if size and o.Size ~= size then o.Size = size end
end
local function placeAll()
	local W, H, avoid = area()
	if W < 10 or H < 10 then return end
	local ts, sd = S.size, hudSd()
	for _, b in BTNS do
		local c, s = TL.place(b.rec, W, H, ts, sd, S.lefty, avoid)
		setIf(b.face, UDim2.fromOffset(c.X, c.Y), UDim2.fromOffset(s.X, s.Y))
		local tx = textFor(b.face.Text, s.X)
		if b.face.TextSize ~= tx then b.face.TextSize = tx end
	end
	local pt = TL.pillTop(pg, pad.AbsolutePosition, W, ts)
	for id, p in pills do
		local r = p.rec or recs[id]
		if r then
			local c, s = TL.place(r, W, H, ts, sd, S.lefty, avoid, pt)
			setIf(p.face, UDim2.fromOffset(c.X, c.Y), UDim2.fromOffset(s.X, s.Y))
			local tx = math.max(9, math.floor(11 * ts * r.s + 0.5))
			if p.face.TextSize ~= tx then p.face.TextSize = tx end
		end
	end
	local sr = recs.stick
	if sr then
		local c, s = TL.place(sr, W, H, ts, sd, S.lefty, avoid)
		stickHome = c
		local ring = UDim2.fromOffset(s.X, s.X)
		if stickRing.Size ~= ring then stickRing.Size = ring; stickKnob.Size = UDim2.fromOffset(s.X * 0.44, s.X * 0.44) end
	end
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
	-- the stick's side: the side of the screen it rests on, out to 42 % (or a bit past where it rests); a FIXED stick
	-- (the layout) only takes a thumb that lands on or near it, and stays where it is
	local rel, r, fixed = pos - o, stickR(), stickFixed()
	local stickSide = if fixed then (rel - stickHome).Magnitude <= r * 1.5
		elseif stickHome.X < sz.X / 2 then rel.X < math.max(sz.X * 0.42, stickHome.X + r * 1.5)
		else rel.X > math.min(sz.X * 0.58, stickHome.X - r * 1.5)
	if mv.finger == nil and stickSide then
		mv.finger = io
		local base = if fixed then o + stickHome else pos
		mv.ox, mv.oy = base.X, base.Y
		fingers[io] = { kind = "stick", last = pos }
		stickRing:SetAttribute("Live", true)
		stickRing.Position = UDim2.fromOffset(base.X - o.X, base.Y - o.Y)
		if fixed then stickMove(pos) end
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
	if f.kind == "box" then -- (the ammo plate: a sideways swipe changes weapon)
		if f.id == "Ammo" and not f.swiped and f.start and math.abs(pos.X - f.start.X) > 26 then
			f.swiped = true
			swipeWeapon(if pos.X > f.start.X then 1 else -1)
		end
		f.last = pos
		return
	end
	local b = f.id and byId[f.id]
	if f.kind == "look" or (b and b.A.look) then lookAcc += pos - f.last end
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
	elseif f.kind == "box" and f.id and boxUp[f.id] then boxUp[f.id](f)
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
	if w.kind == "duo" then return { mode = "hold", range = 26 * SM, grace = 0.17 } end -- (26 Nov 2026, Soak & Shock: the Water Pistol's stream; ZAP is the aim button)
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
		-- (25 Nov 2026) the body as it's drawn, part by part, padded (Hitbox.rayModel): the shot's own test (Arsenal)
		local t = Hitbox.rayModel(o, d, m, PAD)
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
-- the weapon box (layout "weapon"): Utility's item plate, FightHud's ammo plate and the slot chips, stacked; each plate
-- gets a clear button laid over it (ammo: a tap reloads when you let go, a sideways swipe changes weapon; item: G for
-- as long as you hold it). the health box (layout "health"): the speed plate over a slimmer health plate. all of it put
-- back when touch goes off
local moved: { [GuiObject]: UDim2 } = {}
local resized: { [GuiObject]: UDim2 } = {}
local overlays: { [string]: TextButton } = {}
boxUp = {}
local function placePlate(gname: string, name: string, pos: UDim2, size: UDim2?)
	local g = pg:FindFirstChild(gname)
	local sc = g and g:FindFirstChild("Scaled")
	local plate = sc and sc:FindFirstChild(name)
	if not plate or not plate:IsA("GuiObject") then return end
	if not moved[plate] then moved[plate] = plate.Position end
	if plate.Position ~= pos then plate.Position = pos end
	if size then
		if not resized[plate] then resized[plate] = plate.Size end
		if plate.Size ~= size then plate.Size = size end
	end
end
local function placeHudBox(name: string, pos: UDim2, onDown: () -> (), onUp: ((any) -> ())?)
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
			local at = Vector2.new(io.Position.X, io.Position.Y)
			fingers[fingerKey(io)] = { kind = "box", id = name, last = at, start = at }
			onDown()
		end)
		overlays[name] = b
	end
end

-- the hub's buttons (QUESTS, PLAY, PARTY, PROFILE, SHOP, LOADOUT: the left-hand stack) go to the right side, same order
local HUB = { { "JankQuestsButton", nil }, { "JankPlayButton", "Play" }, { "JankPlayButton", "Party" }, { "JankHubsButton", "Hubs" },
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
	for o, z in resized do if o.Parent then o.Size = z end end
	table.clear(resized)
	for _, b in overlays do b:Destroy() end
	table.clear(overlays)
end

-- ---------------------------------------------------------------- a phone's HUD size
-- on a phone (short side under 600 points) the fight HUD is drawn smaller: its plates are laid out for a 720-tall
-- screen, and at 1x on a 390-point phone they took a third of the view (the owner's screenshot, 18 Nov). Theme.guiK
-- is the factor its Scaled frames take (Theme.scaled reads it); the menus keep their own phone layouts
local HUD_GUIS = { "JankfireFight", "JankfireHud", "JankfireModes" }
local phoneK: number? = nil
local function refit(name: string)
	local g = pg:FindFirstChild(name)
	local f = g and g:FindFirstChild("Scaled")
	local sc = f and f:FindFirstChildOfClass("UIScale")
	if not f or not sc or not f:IsA("GuiObject") then return end
	local s = T.scaleNow() * T.hudScale * (T.guiK[name] or 1)
	sc.Scale = s
	f.Size = UDim2.fromScale(1 / s, 1 / s)
end
local function phoneScale()
	local want: number? = if active and not tablet() then math.clamp(viewport().Y / 560, 0.62, 0.86) else nil
	if want == phoneK then return end
	phoneK = want
	for _, n in HUD_GUIS do T.guiK[n] = want end
	if fake then fakeScreen(fake) else for _, n in HUD_GUIS do refit(n) end end
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
		phoneScale() -- (the HUD back to its own size)
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
local function editOpen(): boolean return me:GetAttribute("TouchEditOpen") == true end -- (the layout editor: TouchEdit.client)
RunService.Heartbeat:Connect(function()
	local want = Keys.isTouch()
	if want ~= active then setActive(want) end
	if not active or not built then return end
	if readSettings() then applyLook() end
	if not controls or not cameraInput then hookModules() end
	phoneScale()
	local ch = alive()
	local z = zone()
	local hub = z == "hub" or z == nil
	local fight = fightZone()
	local shown = ch ~= nil and not menuOpen() and not editOpen()
	if gui.Enabled ~= shown then
		gui.Enabled = shown
		if not shown then releaseAll() end
	end
	if not fight and aimOn then setAim(false) end
	placeAll()
	-- the settings panel's reminder ("P settings") goes: the SETTINGS button is here
	local sg = pg:FindFirstChild("JankSettings")
	local hint = sg and sg:FindFirstChild("Scaled") and (sg :: any).Scaled:FindFirstChild("Hint")
	if hint and hint.Visible then hint.Visible = false end
	-- an emote or a replay owns the camera: nothing to press but SETTINGS
	local cam = workspace.CurrentCamera
	local watching = cam ~= nil and cam.CameraType == Enum.CameraType.Scriptable and me:GetAttribute("Emote") == nil
	local kat, edgeFull = heldWeapon() == "katana", me:GetAttribute("EdgeFull") == true
	local scy = heldWeapon() == "scythe" or heldWeapon() == "scythe_rifle"
	local swung = (W[heldWeapon() or ""] or {}).kind == "melee" -- (26 Nov 2026: the LUNGE button, MeleeLunge)
	local yt = me:GetAttribute("YankT")
	local onBody = me:GetAttribute("HookBody") == true and not (type(yt) == "number" and workspace:GetServerTimeNow() < yt)
	local rt = me:GetAttribute("ReelT") -- (the reel: on a rope, ready, after GO)
	local onRope = me:GetAttribute("OnRope") == true and me:GetAttribute("RoundLock") ~= true and not (type(rt) == "number" and workspace:GetServerTimeNow() < rt)
	-- (the AUTO GRAPPLE, LOCK: in a match after GO. shown while it cools down too: a tap then says how long, Move.client)
	local lockOn = (me:GetAttribute("Zone") == "match" or (RunService:IsStudio() and me:GetAttribute("AutoLockTest") == true)) and me:GetAttribute("RoundLock") ~= true
		and not me:GetAttribute("ZmOn") -- (a ZOMBIES game reads as Zone "match": no AUTO GRAPPLE there)
	-- (HOLDOUT, the player attribute Hunt: FIRE punches, HOOK pushes, the lock key lies down, no YANK. the presses are
	-- HuntMoves' through Keys; only the words change here. 27 Nov, hunt-mode's ask)
	local hunt = me:GetAttribute("Hunt") ~= nil
	for _, b in BTNS do
		local A = b.A
		local vis = (fight or not A.fight) and not watching and not b.rec.hid and (not A.q or kat or scy) and (not A.body or onBody) and (not A.rope or onRope) and (not A.lock or lockOn or hunt) and (not A.melee or swung)
			and not (hunt and b.act == "yank")
		if b.face.Visible ~= vis then b.face.Visible = vis end
		if not A.q then
			local word = if hunt and HUNT_WORDS[b.act] then HUNT_WORDS[b.act] else TL.label(b.rec)
			if b.face.Text ~= word then b.face.Text = word end
		end
		if A.q then -- (the katana's WAVE, or the Scythe's FORM in its place)
			local word = if scy then "FORM" else "WAVE"
			if b.face.Text ~= word then b.face.Text = word end
		end
		local lit = (b.act == "aim" and aimOn) or (b.act == "wave" and kat and edgeFull)
		if lit ~= b.lit or b.face.BackgroundColor3 ~= (if lit then T.ACCENT else T.BG) then b.lit = lit; style(b.face, lit, b.act == "fire", b.rec.a) end
	end
	for id, p in pills do
		local hid = p.rec ~= nil and p.rec.hid
		local vis = not hid and (id ~= "auto" or fight) and (id ~= "board" or (z == "match" and me:GetAttribute("ZmOn") == nil))
		if p.face.Visible ~= vis then p.face.Visible = vis end
	end
	local autoP = pills.auto
	if autoP.lit ~= S.auto then autoP.lit = S.auto; style(autoP.face, S.auto, nil, if autoP.rec then autoP.rec.a else 1) end
	local boardP = pills.board
	local boardOn = me:GetAttribute("ScoreboardTouch") == true
	if boardP and boardP.lit ~= boardOn then boardP.lit = boardOn; style(boardP.face, boardOn, nil, if boardP.rec then boardP.rec.a else 1) end
	stickRing.Visible = not watching
	local own = if recs.stick then recs.stick.a else 1
	if not stickRing:GetAttribute("Live") then
		stickRing.Position = UDim2.fromOffset(stickHome.X, stickHome.Y)
		stickRing.BackgroundTransparency = 1 - 0.2 * S.alpha * own * 0.55
		stickKnob.BackgroundTransparency = 1 - 0.85 * S.alpha * own * 0.55
	else
		stickRing.BackgroundTransparency = 1 - 0.2 * S.alpha * own
		stickKnob.BackgroundTransparency = 1 - 0.85 * S.alpha * own
	end
	-- the weapon chips sit in the HUD's own frame, so they line up with the plates over them; names from your
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
	-- the weapon box and the health box, where the layout puts them (design pixels of the HUD's own scaled frames), in
	-- every zone (the hub has a holstered ammo plate too)
	local Wa, Ha, avoid = area()
	local sd = hudSd()
	local wr, hr = recs.weapon, recs.health
	if wr and Wa > 10 then
		local c, s = TL.place(wr, Wa, Ha, S.size, sd, S.lefty, avoid)
		local o = toHud("JankfireFight", c - s / 2)
		if o then
			placeHudBox("Utility", o + UDim2.fromOffset(2, 0), function() itemPress(true) end, function() itemPress(false) end)
			placeHudBox("Ammo", o + UDim2.fromOffset(2, 48), function() end, function(f: any)
				if not (f and f.swiped) then Keys.tap(Enum.KeyCode.R) end -- (a tap reloads; a swipe changed weapon instead)
			end)
			local cp = o + UDim2.fromOffset(0, -34) -- (27 Nov: over the gadget card: under the taller A ammo they fell off a phone's screen)
			if chips.Position ~= cp then chips.Position = cp end
		end
	end
	if hr and Wa > 10 then
		local c, s = TL.place(hr, Wa, Ha, S.size, sd, S.lefty, avoid)
		local tl = c - s / 2
		local o1, o2 = toHud("JankfireHud", tl), toHud("JankfireFight", tl)
		if o1 then placePlate("JankfireHud", "Speed", o1) end
		if o2 then placePlate("JankfireFight", "Hp", o2 + UDim2.fromOffset(0, 60), UDim2.fromOffset(160, 64)) end -- (round 7: off the screen's bottom edge)
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
			local r = stickR()
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
	elseif cmd == "swipe" then swipeWeapon(if tonumber(a) == -1 then -1 else 1)
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
			pressed = lastPress, slot = TL.slot(), phoneK = phoneK, editing = editOpen(),
			-- where everything is (the safe area's points: middle x, y and width) and whether it shows
			btns = (function()
				local out = {}
				for _, b in BTNS do
					local p, z = b.face.AbsolutePosition - pad.AbsolutePosition, b.face.AbsoluteSize
					table.insert(out, { b.id, b.act, math.floor(p.X + z.X / 2), math.floor(p.Y + z.Y / 2), math.floor(z.X), b.face.Visible })
				end
				return out
			end)(),
			pills = (function()
				local out = {}
				for id, p in pills do
					local q, z = p.face.AbsolutePosition - pad.AbsolutePosition, p.face.AbsoluteSize
					out[id] = { math.floor(q.X + z.X / 2), math.floor(q.Y + z.Y / 2), math.floor(z.X), p.face.Visible }
				end
				return out
			end)(),
			stick = { math.floor(stickHome.X), math.floor(stickHome.Y), math.floor(stickRing.AbsoluteSize.X), if recs.stick then recs.stick.act else "" },
			area = { math.floor(pad.AbsoluteSize.X), math.floor(pad.AbsoluteSize.Y) },
		}))
	end
end)
