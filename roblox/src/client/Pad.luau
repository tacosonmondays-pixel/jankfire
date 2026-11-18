--!strict
-- the controller (an Xbox or PlayStation pad through Roblox's Gamepad input, 18 Nov 2026, the owner: "can you add
-- controller support?"). one place for what the other scripts need to know about it; the buttons themselves are the
-- KEYBINDS' third column (Binds.luau) and every action reads them through Binds.is, like a key. the layout and the
-- reasons: roblox/docs/CONTROLLER.md
--   Pad.on()              the last thing used was a pad (a button, a trigger or a stick past a small push); a key,
--                         a click or a mouse move puts it back. Studio tests force it: attribute PadForce = true on the
--                         player or on StarterPlayer. the player attribute PadOn says the same (for anyone who reads it)
--   Pad.changed           BindableEvent, fired (on) when that flips
--   Pad.isPad(io)         this input came from a pad (a real InputObject, or a test's pretend one)
--   Pad.button(id)        the button the action `id` is on ("ButtonR2"), or ""
--   Pad.image(name)       the pad's own picture of that button (UserInputService:GetImageForKeyCode: Roblox picks the
--                         Xbox or the PlayStation set for the pad that's plugged in)
--   Pad.short(name)       its short name for a line of text: RB / R1, A / CROSS ...
--   Pad.chip(cap, letter) Theme.key calls this for every key cap: while a pad is on the cap shows the button the same
--                         action is on, as the pad's picture, in the same cap; an action with no button leaves an
--                         empty (invisible) cap. a cap can say what it's for: attribute PadAction = "<bind id>" or
--                         Pad = "<button name>" on the cap
--   Pad.say(text)         a hint's keys swapped for the pad's buttons ("press L" -> "press D-Up"), as Keys.say does
--                         for a phone
--   Pad.stick(n)          the raw stick (1 = move, 2 = look) as a Vector2, x right, y up
--   Pad.trigger(name)     ButtonL2 / ButtonR2 pressure, 0..1
local Players = game:GetService("Players")
local UIS = game:GetService("UserInputService")
local StarterPlayer = game:GetService("StarterPlayer")

local me = Players.LocalPlayer
local Pad = {}
Pad.changed = Instance.new("BindableEvent")

-- ------------------------------------------------------------------ which device is in your hands
local padOn = false
local function forced(): boolean
	return me:GetAttribute("PadForce") == true or StarterPlayer:GetAttribute("PadForce") == true
end
function Pad.on(): boolean return padOn or forced() end
local function setOn(v: boolean)
	if v == padOn then return end
	padOn = v
	me:SetAttribute("PadOn", Pad.on())
	Pad.changed:Fire(Pad.on())
end
local function forceChanged()
	me:SetAttribute("PadOn", Pad.on())
	Pad.changed:Fire(Pad.on())
end
me:GetAttributeChangedSignal("PadForce"):Connect(forceChanged)
StarterPlayer:GetAttributeChangedSignal("PadForce"):Connect(forceChanged)

local function gamepadType(t: any): boolean
	return typeof(t) == "EnumItem" and string.sub(t.Name, 1, 7) == "Gamepad"
end
function Pad.isPad(io: any): boolean
	local ok, yes = pcall(function() return gamepadType(io.UserInputType) end)
	return ok and yes == true
end
-- a stick resting a hair off centre, or a trigger touched, mustn't steal the screen from a mouse player
local PUSH = 0.3
UIS.InputBegan:Connect(function(io: InputObject)
	local t = io.UserInputType
	if gamepadType(t) then
		local n = io.KeyCode.Name
		if string.sub(n, 1, 10) ~= "Thumbstick" or io.Position.Magnitude > PUSH then setOn(true) end
	elseif t == Enum.UserInputType.Keyboard or t == Enum.UserInputType.MouseButton1 or t == Enum.UserInputType.MouseButton2
		or t == Enum.UserInputType.MouseButton3 or t == Enum.UserInputType.Touch then
		setOn(false)
	end
end)
UIS.InputChanged:Connect(function(io: InputObject)
	local t = io.UserInputType
	if gamepadType(t) then
		local k = io.KeyCode
		if k == Enum.KeyCode.Thumbstick1 or k == Enum.KeyCode.Thumbstick2 then
			if Vector2.new(io.Position.X, io.Position.Y).Magnitude > PUSH then setOn(true) end
		elseif (k == Enum.KeyCode.ButtonL2 or k == Enum.KeyCode.ButtonR2) and io.Position.Z > PUSH then
			setOn(true)
		end
	elseif t == Enum.UserInputType.MouseMovement then
		if io.Delta.Magnitude > 3 then setOn(false) end
	elseif t == Enum.UserInputType.MouseWheel then
		setOn(false)
	end
end)
-- (joining with a pad already in hand: Roblox's own guess)
task.defer(function()
	local ok, pref = pcall(function() return (UIS :: any).PreferredInput end)
	if ok and pref == (Enum :: any).PreferredInput.Gamepad then setOn(true)
	elseif gamepadType(UIS:GetLastInputType()) then setOn(true) end
	me:SetAttribute("PadOn", Pad.on())
end)

-- ------------------------------------------------------------------ the sticks and triggers
-- (Studio tests: Pad.fake = { [Enum.KeyCode.Thumbstick2] = Vector3 } stands in for the pad: a test sets it through the
-- PadTest attribute, PadLook.client)
Pad.fake = {} :: { [Enum.KeyCode]: Vector3 }
local function stateOf(code: Enum.KeyCode): Vector3
	local f = Pad.fake[code]
	if f then return f end
	if not UIS.GamepadEnabled then return Vector3.zero end
	local ok, list = pcall(function() return UIS:GetGamepadState(Enum.UserInputType.Gamepad1) end)
	if not ok or type(list) ~= "table" then return Vector3.zero end
	for _, o in list :: { InputObject } do
		if o.KeyCode == code then return o.Position end
	end
	return Vector3.zero
end
function Pad.stick(n: number): Vector2
	local p = stateOf(if n == 1 then Enum.KeyCode.Thumbstick1 else Enum.KeyCode.Thumbstick2)
	return Vector2.new(p.X, p.Y)
end
function Pad.trigger(name: string): number
	local p = stateOf(if name == "ButtonL2" then Enum.KeyCode.ButtonL2 else Enum.KeyCode.ButtonR2)
	return math.clamp(p.Z, 0, 1)
end

-- ------------------------------------------------------------------ buttons, pictures, names
local Binds: any = nil
local function binds(): any
	if Binds == nil then
		local m = script.Parent:FindFirstChild("Binds")
		local ok, b = pcall(require, m :: any)
		Binds = if ok and type(b) == "table" then b else false
	end
	return Binds or nil
end
function Pad.button(id: string): string
	local b = binds()
	if not b then return "" end
	local ok, v = pcall(function() return b.get(id)[3] end)
	return if ok and type(v) == "string" then v else ""
end

local imgCache: { [string]: string } = {}
function Pad.image(name: string): string
	if name == "" then return "" end
	local c = imgCache[name]
	if c then return c end
	local ok, img = pcall(function() return UIS:GetImageForKeyCode((Enum.KeyCode :: any)[name]) end)
	local s = if ok and img then tostring(img) else ""
	imgCache[name] = s
	return s
end
-- the pad's family, from the picture Roblox picks for it: "ps" or "xbox"
function Pad.family(): string
	local s = Pad.image("ButtonA")
	if string.find(string.lower(s), "playstation", 1, true) or string.find(string.lower(s), "ps4", 1, true) or string.find(string.lower(s), "ps5", 1, true) then return "ps" end
	return "xbox"
end
-- (the pictures change with the pad that's plugged in: a fresh one each time a pad joins)
UIS.GamepadConnected:Connect(function() table.clear(imgCache) end)

local XBOX = { ButtonA = "A", ButtonB = "B", ButtonX = "X", ButtonY = "Y", ButtonL1 = "LB", ButtonR1 = "RB", ButtonL2 = "LT",
	ButtonR2 = "RT", ButtonL3 = "LS", ButtonR3 = "RS", DPadUp = "D-UP", DPadDown = "D-DOWN", DPadLeft = "D-LEFT",
	DPadRight = "D-RIGHT", ButtonSelect = "VIEW", ButtonStart = "MENU", Thumbstick1 = "LEFT STICK", Thumbstick2 = "RIGHT STICK" }
local PS = { ButtonA = "CROSS", ButtonB = "CIRCLE", ButtonX = "SQUARE", ButtonY = "TRIANGLE", ButtonL1 = "L1", ButtonR1 = "R1",
	ButtonL2 = "L2", ButtonR2 = "R2", ButtonL3 = "L3", ButtonR3 = "R3", ButtonSelect = "TOUCHPAD", ButtonStart = "OPTIONS" }
function Pad.short(name: string): string
	if name == "" then return "" end
	local s = if Pad.family() == "ps" then (PS :: any)[name] else nil
	return s or (XBOX :: any)[name] or name
end

-- which action a key cap's letter belongs to: the key as bound now, else the default key
local SPECIAL: { [string]: string } = { SPACE = "ButtonA", ENTER = "ButtonA", ESC = "ButtonB" }
local function buttonForLetter(letter: string): string?
	local L = string.upper(letter)
	if L == "" then return nil end
	-- (a lone number is a pick on that screen (an answer, a vote, an ad): on a pad you select it instead)
	if string.match(L, "^%d$") then return "" end
	local b = binds()
	if b then
		for _, a in b.ACTIONS do
			local cur, def = b.get(a.id), b.default(a.id)
			for s = 1, 2 do
				if (cur[s] ~= "" and string.upper(b.nameOf(cur[s])) == L) or (def[s] ~= "" and string.upper(b.nameOf(def[s])) == L) then
					return cur[3]
				end
			end
		end
	end
	return SPECIAL[L]
end
Pad.buttonForLetter = buttonForLetter

-- ------------------------------------------------------------------ key caps
type Chip = { cap: Frame, letter: TextLabel?, glyph: ImageLabel, stroke: UIStroke?, bg: number, st: number, lv: boolean, padded: boolean }
local chips: { [Frame]: Chip } = setmetatable({}, { __mode = "k" }) :: any
local function paint(c: Chip)
	local cap = c.cap
	if not cap.Parent then return end
	local on = Pad.on()
	local btn: string? = nil
	if on then
		local direct = cap:GetAttribute("Pad")
		local act = cap:GetAttribute("PadAction")
		if type(direct) == "string" then btn = direct
		elseif type(act) == "string" then btn = Pad.button(act)
		else btn = buttonForLetter(if c.letter then c.letter.Text else "") or "" end
	end
	local img = if btn and btn ~= "" then Pad.image(btn) else ""
	if on then
		if not c.padded then
			-- (what the cap looked like before the pad: put back exactly that when the mouse or a key comes back)
			c.padded = true
			c.bg = cap.BackgroundTransparency
			c.st = if c.stroke then c.stroke.Transparency else 0
			c.lv = if c.letter then c.letter.Visible else true
		end
		if c.letter then c.letter.Visible = false end
		c.glyph.Image = img
		c.glyph.Visible = img ~= ""
		-- (an action with no button: the cap stays where it is but shows nothing)
		cap.BackgroundTransparency = if img ~= "" then c.bg else 1
		if c.stroke then c.stroke.Transparency = if img ~= "" then c.st else 1 end
	elseif c.padded then
		c.padded = false
		if c.letter then c.letter.Visible = c.lv end
		c.glyph.Visible = false
		cap.BackgroundTransparency = c.bg
		if c.stroke then c.stroke.Transparency = c.st end
	end
end
function Pad.chip(cap: Frame, _letter: string?)
	if chips[cap] then return end
	local letter = cap:FindFirstChild("Letter") :: TextLabel?
	local stroke = cap:FindFirstChildOfClass("UIStroke")
	local g = Instance.new("ImageLabel")
	g.Name = "Glyph"
	g.BackgroundTransparency = 1
	g.AnchorPoint = Vector2.new(0.5, 0.5)
	g.Position = UDim2.fromScale(0.5, 0.5)
	g.Size = UDim2.fromScale(0.82, 0.82)
	g.SizeConstraint = Enum.SizeConstraint.RelativeYY
	g.ScaleType = Enum.ScaleType.Fit
	g.ImageColor3 = Color3.fromRGB(240, 242, 245) -- (Theme.TEXT: the pad's pictures in the caps' own white)
	g.Visible = false
	g.ZIndex = cap.ZIndex + 1
	g.Parent = cap
	-- (a square glyph whatever the cap's width: RelativeYY, so both sides are parts of the cap's height)
	local c: Chip = { cap = cap, letter = letter, glyph = g, stroke = stroke, bg = 0, st = 0, lv = true, padded = false }
	chips[cap] = c
	if letter then letter:GetPropertyChangedSignal("Text"):Connect(function() paint(c) end) end
	cap:GetAttributeChangedSignal("Pad"):Connect(function() paint(c) end)
	cap:GetAttributeChangedSignal("PadAction"):Connect(function() paint(c) end)
	cap:GetPropertyChangedSignal("ZIndex"):Connect(function() g.ZIndex = cap.ZIndex + 1 end)
	task.defer(paint, c)
end
local function repaintAll()
	for _, c in chips do task.spawn(paint, c) end
end
Pad.changed.Event:Connect(repaintAll)
task.defer(function()
	local b = binds()
	if not b then return end
	local okS, Settings = pcall(require, script.Parent:WaitForChild("Settings") :: any)
	if okS and type(Settings) == "table" then
		(Settings :: any).onAny(function(k: string) if string.sub(k, 1, 5) == "bind." then task.defer(repaintAll) end end)
	end
end)

-- ------------------------------------------------------------------ hint text
function Pad.say(text: string, bracketsOnly: boolean?): string
	if not Pad.on() then return text end
	local function sw(k: string): string?
		local btn = buttonForLetter(k)
		if btn == nil then return nil end
		if btn == "" then return "" end
		return Pad.short(btn)
	end
	local s = text
	-- "the shop [B]" -> "the shop [RB]"; a key with no button: the bracket goes
	s = string.gsub(s, "%[(%w+)%]", function(k: string): string?
		local r = sw(k)
		if r == nil then return nil end
		return if r == "" then "" else "[" .. r .. "]"
	end)
	if bracketsOnly then return s end
	for _, verb in { "[Pp]ress", "[Hh]old", "PRESS", "HOLD" } do
		s = string.gsub(s, "(%f[%a]" .. verb .. ") (%w+)%f[%W]", function(w: string, k: string): string?
			if #k > 5 then return nil end
			local r = sw(k)
			if r == nil or r == "" then return nil end
			return w .. " " .. r
		end)
	end
	s = string.gsub(s, "%f[%w](%u%w?%w?) TO ", function(k: string): string?
		local r = sw(k)
		if r == nil or r == "" then return nil end
		return r .. " TO "
	end)
	return s
end

return Pad
