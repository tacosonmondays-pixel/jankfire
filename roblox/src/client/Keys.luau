--!strict
-- One way in for every key: the keyboard and mouse, and the phone's touch buttons (TouchControls.client.luau), which
-- press the same keys. The web game's rule (public/js/touch.js): no second input path. A script that listens with
-- Keys.began / Keys.ended instead of UserInputService.InputBegan / InputEnded hears both, so a touch button does
-- exactly what its key does, in the same code. A touch press arrives as a plain table with the InputObject fields the
-- handlers read (KeyCode, UserInputType, UserInputState, Position, Delta, plus Touch = true) and gameProcessed false.
--   Keys.press(code, down)  a button goes down / up. code: an Enum.KeyCode, or Enum.UserInputType.MouseButton1/2/3
--   Keys.press(code, down, act)  the same, for that one action only (Binds matches it to act alone: the phone's REEL
--                           and YANK both press F, 26 Nov 2026)
--   Keys.tap(code)          down and up at once
--   Keys.isDown(code)       the real key, or a touch button holding it (the crouch pose reads C this way)
--   Keys.fromTouch(io)      true for a touch button's pretend press. USE THIS, never io.Touch: a real InputObject
--                           throws on a field it doesn't have ("Touch is not a valid member of InputObject"; it bit the
--                           settings page's Binds and the emote wheel on 17 Nov)
--   Keys.isTouch()          a phone or a tablet: touch and no keyboard (a touch laptop plays with its keys). Studio
--                           tests force it with the attribute TouchForce = true on the player, or on StarterPlayer
--                           (set in Edit before Play, so the HUD is made the phone's way from the start; take it off
--                           again before saving)
--   Keys.name(code)         what the key is called on a phone: the touch button's name ("HOOK" for E), or nil
--   Keys.say(text)          on a phone, a hint's keys swapped for button names ("press L" -> "tap LOADOUT"); else as is
local Players = game:GetService("Players")
local UIS = game:GetService("UserInputService")

local Keys = {}

type Handler = (io: any, gp: boolean) -> ()
local beganFns: { Handler } = {}
local endedFns: { Handler } = {}
local held: { [any]: number } = {} -- code -> how many touch buttons hold it

local StarterPlayer = game:GetService("StarterPlayer")
function Keys.isTouch(): boolean
	local me = Players.LocalPlayer
	if (me and me:GetAttribute("TouchForce") == true) or StarterPlayer:GetAttribute("TouchForce") == true then return true end
	return UIS.TouchEnabled and not UIS.KeyboardEnabled
end

function Keys.fromTouch(io: any): boolean
	return typeof(io) == "table" and io.Touch == true
end

function Keys.began(fn: Handler)
	UIS.InputBegan:Connect(fn)
	table.insert(beganFns, fn)
end
function Keys.ended(fn: Handler)
	UIS.InputEnded:Connect(function(io: InputObject, gp: boolean) fn(io, gp) end)
	table.insert(endedFns, fn)
end

local function fake(code: any, down: boolean, act: string?): any
	local isMouse = typeof(code) == "EnumItem" and code.EnumType == Enum.UserInputType
	return {
		KeyCode = if isMouse then Enum.KeyCode.Unknown else code,
		UserInputType = if isMouse then code else Enum.UserInputType.Keyboard,
		UserInputState = if down then Enum.UserInputState.Begin else Enum.UserInputState.End,
		Position = Vector3.zero, Delta = Vector3.zero, Touch = true, Act = act,
	}
end

function Keys.press(code: any, down: boolean, act: string?)
	if act then -- (one action's own press: no key of its own, so nothing that listens for the key itself hears it)
		local io = fake(Enum.KeyCode.Unknown, down, act)
		for _, fn in (if down then beganFns else endedFns) do task.spawn(fn, io, false) end
		return
	end
	local n = held[code] or 0
	if down then
		held[code] = n + 1
		if n > 0 then return end -- (already down: a second button on the same key)
	else
		if n <= 0 then return end
		held[code] = n - 1
		if n > 1 then return end
	end
	local io = fake(code, down)
	for _, fn in (if down then beganFns else endedFns) do task.spawn(fn, io, false) end
end
function Keys.tap(code: any)
	Keys.press(code, true)
	Keys.press(code, false)
end
-- a test's pretend controller button (PadLook.client's PadTest "press:ButtonR2"): every Keys.began / ended listener
-- hears it as a pad's (UserInputType Gamepad1, no Touch field), so Binds matches the player's own controller column
function Keys.padPress(code: any, down: boolean)
	local io = { KeyCode = code, UserInputType = Enum.UserInputType.Gamepad1,
		UserInputState = if down then Enum.UserInputState.Begin else Enum.UserInputState.End, Position = Vector3.zero, Delta = Vector3.zero }
	for _, fn in (if down then beganFns else endedFns) do task.spawn(fn, io, false) end
end
-- a touch button's own count (TouchControls lets go of everything it holds when a menu opens)
function Keys.heldByTouch(code: any): boolean return (held[code] or 0) > 0 end

function Keys.isDown(code: any): boolean
	if (held[code] or 0) > 0 then return true end
	if typeof(code) == "EnumItem" and code.EnumType == Enum.UserInputType then return UIS:IsMouseButtonPressed(code) end
	return UIS:IsKeyDown(code)
end

-- the touch buttons' names (TouchControls draws them with these words)
local NAMES: { [any]: string } = {
	[Enum.UserInputType.MouseButton1] = "FIRE", [Enum.UserInputType.MouseButton2] = "AIM",
	[Enum.KeyCode.Space] = "JUMP", [Enum.KeyCode.C] = "SLIDE", [Enum.KeyCode.LeftControl] = "SLIDE",
	[Enum.KeyCode.E] = "HOOK", [Enum.KeyCode.R] = "RELOAD", [Enum.KeyCode.Three] = "STAB", [Enum.KeyCode.G] = "YOUR ITEM",
	[Enum.KeyCode.T] = "EMOTE", [Enum.KeyCode.P] = "SETTINGS", [Enum.KeyCode.L] = "LOADOUT", [Enum.KeyCode.B] = "SHOP",
	[Enum.KeyCode.M] = "PLAY", [Enum.KeyCode.J] = "PARTY", [Enum.KeyCode.K] = "PROFILE",
}
Keys.NAMES = NAMES
function Keys.name(code: any): string? return NAMES[code] end

local LETTER: { [string]: string } = {}
for code, name in NAMES do
	if typeof(code) == "EnumItem" and code.EnumType == Enum.KeyCode and #code.Name == 1 then LETTER[code.Name] = name end
end
LETTER["E"] = "HOOK"

function Keys.say(text: string): string
	if not Keys.isTouch() then
		-- (a controller in your hands: the keys swapped for its buttons, Pad.say)
		local pm = script.Parent:FindFirstChild("Pad")
		local ok, Pad = false, nil
		if pm then ok, Pad = pcall(require, pm) end
		if ok and type(Pad) == "table" and (Pad :: any).on() then return (Pad :: any).say(text) end
		return text
	end
	local s = text
	-- "the shop [B]": the button is on screen with its name, the key goes
	s = string.gsub(s, "%s*%[(%u)%]", function(k: string): string? return if LETTER[k] then "" else nil end)
	-- "press L" / "hold G" / "G TO PRINT IT"
	s = string.gsub(s, "(%f[%a][Pp]ress) (%u)%f[%A]", function(w: string, k: string): string?
		return if LETTER[k] then (if w == "Press" then "Tap " else "tap ") .. LETTER[k] else nil
	end)
	s = string.gsub(s, "(%f[%a][Hh]old) (%u)%f[%A]", function(w: string, k: string): string?
		return if LETTER[k] then w .. " " .. LETTER[k] else nil
	end)
	s = string.gsub(s, "%f[%w](%u) TO ", function(k: string): string? return if LETTER[k] then "TAP " .. LETTER[k] .. " TO " else nil end)
	return s
end

return Keys
