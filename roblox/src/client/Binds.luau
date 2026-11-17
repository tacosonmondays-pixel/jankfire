--!strict
-- the key bindings (Settings > KEYBINDS): every rebindable action, its keyboard keys (two slots, like the web game's
-- keys.js) and its controller button, saved with your settings (Settings.luau, keys "bind.<id>" = "kb1|kb2|pad").
-- scripts ask here instead of naming a key:
--   Binds.is("reload", io)          does this InputObject press the action (keyboard, mouse or controller)?
--   Binds.down("grapple")           is it held right now?
--   Binds.press("crouch", down, cur) for the actions with HOLD / TOGGLE (aim, crouch, sprint): the state after a press
--                                   or a release (hold: down; toggle: a press flips cur, a release keeps it)
--   Binds.on("crouch")              the last state press() gave (CrouchPoses / ThirdPerson read the crouch from here)
--   Binds.label("reload")           "R" (the controls line, the key caps)
-- the phone's buttons (Keys.luau, TouchControls) press an action's DEFAULT key as a pretend input (io.Touch = true):
-- those match the defaults here, so a player's own keyboard binds never break a touch button.
-- the movement keys (W A S D), jump (Space, A) and looking are Roblox's own controls and stay as they are.
local UIS = game:GetService("UserInputService")
local Players = game:GetService("Players")

local Settings = require(script.Parent:WaitForChild("Settings")) :: any

local Binds = {}

export type Action = { id: string, label: string, group: string, kb: { string }, pad: string?, toggle: string? }
-- (order = the order of the KEYBINDS tab)
Binds.ACTIONS = {
	{ id = "fire", label = "FIRE", group = "COMBAT", kb = { "MouseButton1" }, pad = "ButtonR2" },
	{ id = "aim", label = "AIM · PARRY", group = "COMBAT", kb = { "MouseButton2" }, pad = "ButtonL2", toggle = "aim.toggle" },
	{ id = "reload", label = "RELOAD", group = "COMBAT", kb = { "R" }, pad = "ButtonX" },
	{ id = "slot1", label = "WEAPON 1", group = "COMBAT", kb = { "One" } },
	{ id = "slot2", label = "WEAPON 2", group = "COMBAT", kb = { "Two" } },
	{ id = "slot3", label = "WEAPON 3", group = "COMBAT", kb = { "Three" } },
	{ id = "slot4", label = "SHREDDER", group = "COMBAT", kb = { "Four" } },
	{ id = "next", label = "NEXT WEAPON", group = "COMBAT", kb = {}, pad = "ButtonY" },
	{ id = "item", label = "UTILITY ITEM", group = "COMBAT", kb = { "G" }, pad = "ButtonR1" },
	{ id = "flash", label = "GOGGLES FLASH", group = "COMBAT", kb = { "N", "MouseButton3" } },
	{ id = "sprint", label = "SPRINT", group = "MOVEMENT", kb = { "LeftShift", "RightShift" }, pad = "ButtonL3", toggle = "sprint.toggle" },
	{ id = "crouch", label = "CROUCH · SLIDE", group = "MOVEMENT", kb = { "C", "LeftControl" }, pad = "ButtonB", toggle = "crouch.toggle" },
	{ id = "grapple", label = "GRAPPLE", group = "MOVEMENT", kb = { "E" }, pad = "ButtonL1" },
	{ id = "camera", label = "CAMERA VIEW", group = "MOVEMENT", kb = { "V" }, pad = "ButtonR3" },
	{ id = "emote", label = "EMOTE WHEEL", group = "MENUS", kb = { "T" }, pad = "DPadRight" },
	{ id = "loadout", label = "LOADOUT", group = "MENUS", kb = { "L" } },
	{ id = "play", label = "PLAY", group = "MENUS", kb = { "M" } },
	{ id = "party", label = "PARTY", group = "MENUS", kb = { "J" } },
	{ id = "shop", label = "SHOP", group = "MENUS", kb = { "B" } },
	{ id = "profile", label = "PROFILE", group = "MENUS", kb = { "K" } },
	{ id = "settings", label = "SETTINGS", group = "MENUS", kb = { "P" } },
	{ id = "keys", label = "SHOW KEYS (HOLD)", group = "MENUS", kb = { "H" } },
	{ id = "quickjoin", label = "QUICK JOIN", group = "MENUS", kb = { "F" } }, -- (the hub pad pop-up: QuickJoinUI)
} :: { Action }
Binds.FIXED = { -- (shown in the tab, greyed: Roblox's own controls)
	{ label = "MOVE", kb = "W A S D", pad = "Left stick" },
	{ label = "JUMP", kb = "Space", pad = "A" },
	{ label = "LOOK", kb = "Mouse", pad = "Right stick" },
}
-- never bindable: Roblox's menu, chat, console and screenshot keys
Binds.RESERVED = { Escape = true, Slash = true, Backquote = true, F9 = true, F11 = true, F12 = true, Unknown = true, ButtonStart = true, ButtonSelect = true }

local byId: { [string]: Action } = {}
for _, a in Binds.ACTIONS do byId[a.id] = a end
Binds.byId = byId

-- ------------------------------------------------------------------ the current bindings
type Bind = { string } -- { kb1, kb2, pad } ("" = none)
local binds: { [string]: Bind } = {}
local defaults: { [string]: Bind } = {}
local function default(id: string): Bind
	local a = byId[id]
	return { a.kb[1] or "", a.kb[2] or "", a.pad or "" }
end
local function parse(id: string, v: any): Bind
	if type(v) ~= "string" then return default(id) end
	local p = string.split(v, "|")
	return { p[1] or "", p[2] or "", p[3] or "" }
end
local function load(id: string) binds[id] = parse(id, Settings.get("bind." .. id)) end
for _, a in Binds.ACTIONS do
	defaults[a.id] = default(a.id)
	Settings.DEFAULTS["bind." .. a.id] = table.concat(defaults[a.id], "|")
	load(a.id)
end
Settings.onAny(function(k: string)
	local id = string.match(k, "^bind%.(.+)$")
	if id and byId[id] then load(id) end
end)

function Binds.get(id: string): Bind return binds[id] or { "", "", "" } end
function Binds.default(id: string): Bind return defaults[id] or { "", "", "" } end

-- does `name` (a KeyCode or a MouseButton name) match this input?
local function hits(name: string, io: any): boolean
	if name == "" then return false end
	if string.sub(name, 1, 11) == "MouseButton" then return io.UserInputType.Name == name end
	return io.KeyCode.Name == name
end
local lastTouch = false -- (the last input Binds.is matched came from a touch button)
local function isRaw(id: string, io: any): boolean
	-- (a real InputObject has no Touch field: reading it throws. only the touch buttons' pretend inputs are tables)
	local touch = typeof(io) == "table" and io.Touch == true
	local b = if touch then defaults[id] else binds[id]
	if not b then return false end
	local yes = hits(b[1], io) or hits(b[2], io) or hits(b[3], io)
	if yes then lastTouch = touch end
	return yes
end
-- every key and click in the game goes through here, so it can never throw: a slip falls back to the default keys
-- (17 Nov: one unguarded field read killed all keyboard and mouse input for four minutes)
local warned = false
function Binds.is(id: string, io: any): boolean
	local ok, yes = pcall(isRaw, id, io)
	if ok then return yes == true end
	if not warned then warned = true; warn("[jankfire] Binds.is: " .. tostring(yes) .. " (using the default keys)") end
	local b = defaults[id]
	if not b then return false end
	local ok2, y2 = pcall(function() return hits(b[1], io) or hits(b[2], io) or hits(b[3], io) end)
	return ok2 and y2 == true
end
-- which of slots 1-3 this input picks (the loadout's keys), or nil
function Binds.slot(io: any): number?
	for i = 1, 3 do if Binds.is("slot" .. i, io) then return i end end
	return nil
end

local function held(name: string): boolean
	if name == "" then return false end
	if string.sub(name, 1, 11) == "MouseButton" then
		local ok, v = pcall(function() return UIS:IsMouseButtonPressed((Enum.UserInputType :: any)[name]) end)
		return ok and v == true
	end
	local ok, kc = pcall(function() return (Enum.KeyCode :: any)[name] end)
	if not ok or not kc then return false end
	if string.sub(name, 1, 6) == "Button" or string.sub(name, 1, 4) == "DPad" then
		local ok2, v = pcall(function() return UIS:IsGamepadButtonDown(Enum.UserInputType.Gamepad1, kc) end)
		return ok2 and v == true
	end
	return UIS:IsKeyDown(kc)
end
function Binds.down(id: string): boolean
	local b = binds[id]
	if not b or UIS:GetFocusedTextBox() then return false end
	return held(b[1]) or held(b[2]) or held(b[3])
end

-- hold or toggle (Settings: aim.toggle, crouch.toggle, sprint.toggle)
local state: { [string]: boolean } = {}
function Binds.toggles(id: string): boolean
	local a = byId[id]
	return a ~= nil and a.toggle ~= nil and Settings.get(a.toggle) == true
end
-- (a touch button's press is always a hold: TouchControls holds AIM down itself while its own toggle is on)
function Binds.press(id: string, down: boolean, cur: boolean?): boolean
	local was = if cur ~= nil then cur else state[id] == true
	local v = if Binds.toggles(id) and not lastTouch then (if down then not was else was) else down
	state[id] = v
	return v
end
function Binds.on(id: string): boolean return state[id] == true end
function Binds.clear(id: string) state[id] = false end
Players.LocalPlayer.CharacterAdded:Connect(function() table.clear(state) end)

-- ------------------------------------------------------------------ names on screen
local SHORT = {
	MouseButton1 = "LMB", MouseButton2 = "RMB", MouseButton3 = "MMB", LeftShift = "Shift", RightShift = "R Shift",
	LeftControl = "Ctrl", RightControl = "R Ctrl", LeftAlt = "Alt", RightAlt = "R Alt", Space = "Space", Return = "Enter",
	Backspace = "Bksp", CapsLock = "Caps", One = "1", Two = "2", Three = "3", Four = "4", Five = "5", Six = "6",
	Seven = "7", Eight = "8", Nine = "9", Zero = "0", Minus = "-", Equals = "=", LeftBracket = "[", RightBracket = "]",
	Semicolon = ";", Quote = "'", Comma = ",", Period = ".", BackSlash = "\\", Up = "Up", Down = "Down", Left = "Left",
	Right = "Right", ButtonR2 = "RT", ButtonL2 = "LT", ButtonR1 = "RB", ButtonL1 = "LB", ButtonR3 = "RS", ButtonL3 = "LS",
	ButtonA = "A", ButtonB = "B", ButtonX = "X", ButtonY = "Y", DPadLeft = "D-Left", DPadRight = "D-Right", DPadUp = "D-Up",
	DPadDown = "D-Down", Tab = "Tab", Insert = "Ins", Delete = "Del", PageUp = "PgUp", PageDown = "PgDn", Home = "Home", End = "End",
}
function Binds.nameOf(name: string): string
	if name == "" then return "" end
	if SHORT[name] then return SHORT[name] end
	local kp = string.match(name, "^Keypad(.+)$")
	if kp then return "Num " .. (SHORT[kp] or kp) end
	return name
end
-- the action's first keyboard key (or its second, or its button), for the controls line
function Binds.label(id: string): string
	local b = binds[id]
	if not b then return "" end
	local s = if b[1] ~= "" then b[1] elseif b[2] ~= "" then b[2] else b[3]
	return Binds.nameOf(s)
end

-- ------------------------------------------------------------------ rebinding (the KEYBINDS tab)
local function save(id: string)
	Settings.set("bind." .. id, table.concat(binds[id], "|"))
end
-- what an input would bind as: a key or mouse button for slots 1-2, a controller button for slot 3. nil = not bindable
function Binds.inputName(io: InputObject, slot: number): string?
	local t = io.UserInputType
	if slot == 3 then
		if string.sub(t.Name, 1, 7) ~= "Gamepad" then return nil end
		local n = io.KeyCode.Name
		if string.sub(n, 1, 10) == "Thumbstick" then return nil end
		return if Binds.RESERVED[n] then nil else n
	end
	if t == Enum.UserInputType.MouseButton1 or t == Enum.UserInputType.MouseButton2 or t == Enum.UserInputType.MouseButton3 then return t.Name end
	if t ~= Enum.UserInputType.Keyboard then return nil end
	local n = io.KeyCode.Name
	return if Binds.RESERVED[n] then nil else n
end
-- set one slot. if another action had that key in the same column, it gets this slot's old key (a swap, like keys.js).
-- returns the label of the action it moved, if any
function Binds.set(id: string, slot: number, name: string): string?
	local b = binds[id]
	if not b then return nil end
	local old = b[slot]
	if old == name then return nil end
	local moved: string? = nil
	if name ~= "" then
		for _, a in Binds.ACTIONS do
			local o = binds[a.id]
			for s = 1, 3 do
				if (s == 3) == (slot == 3) and o[s] == name and not (a.id == id and s == slot) then
					o[s] = old -- (its own other slot: the two swap; another action: it takes this slot's old key)
					if a.id ~= id then
						moved = a.label
						save(a.id)
					end
				end
			end
		end
	end
	b[slot] = name
	save(id)
	return moved
end
function Binds.reset(id: string) Settings.set("bind." .. id, nil) end
function Binds.resetAll()
	for _, a in Binds.ACTIONS do Settings.set("bind." .. a.id, nil) end
end

return Binds
