-- the settings page on P (its key can be changed: Settings > KEYBINDS). the page: Jankfire.SettingsUI; the values and
-- their save: Jankfire.Settings; what they do: Jankfire.SettingsApply. this script makes the ScreenGui, the reminder in
-- the top right corner and opens and closes the page. while it's open the player attribute SettingsOpen is true
-- (FightHud hides the crosshair under it, the shoulder camera frees the mouse)
local Players = game:GetService("Players")
local UIS = game:GetService("UserInputService")
local RunService = game:GetService("RunService")

local lp = Players.LocalPlayer
local J = script.Parent:WaitForChild("Jankfire")
local T = require(J:WaitForChild("Theme"))
local Binds = require(J:WaitForChild("Binds"))
local UI = require(J:WaitForChild("SettingsUI"))
local MenuCursor = require(J:WaitForChild("MenuCursor")) :: any

local gui = Instance.new("ScreenGui")
gui.Name = "JankSettings"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = true
gui.DisplayOrder = 20
gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
gui.Parent = lp:WaitForChild("PlayerGui")

-- the reminder, top right
local hint = T.plate(T.scaled(gui), "Hint", UDim2.new(1, -136, 0, 14), UDim2.fromOffset(112, 30))
local cap = T.key(hint, "P", UDim2.fromOffset(5, 4))
local hintText = T.text(hint, "Text", "settings", 13, T.MUTED, T.FONT_BOLD)
hintText.Position = UDim2.fromOffset(36, 0)
hintText.Size = UDim2.new(1, -40, 1, 0)
local function hintKey()
	local k = Binds.label("settings")
	local letter = cap:FindFirstChild("Letter")
	if letter then letter.Text = if k == "" then "-" else k end
	cap.Size = UDim2.fromOffset(math.max(22, 10 + 8 * #k), 22)
	hintText.Position = UDim2.fromOffset(cap.Size.X.Offset + 14, 0)
	hint.Size = UDim2.fromOffset(cap.Size.X.Offset + 90, 30)
	hint.Position = UDim2.new(1, -(cap.Size.X.Offset + 114), 0, 14)
end
hintKey()
require(J:WaitForChild("Settings")).changed("bind.settings", function() task.defer(hintKey) end)

UI.build(gui)

local open = false
local function setOpen(v)
	open = v
	UI.setOpen(v)
	lp:SetAttribute("SettingsOpen", v) -- (FightHud hides the crosshair under the page)
end
-- (through Keys.began: the phone's SETTINGS button presses P as a pretend key, TouchControls)
local okK, Keys = pcall(require, J:WaitForChild("Keys", 10))
local function onKey(io, gp)
	if gp or UI.capturing or UIS:GetFocusedTextBox() then return end
	if Binds.is("settings", io) then setOpen(not open) end
end
if okK and type(Keys) == "table" and Keys.began then Keys.began(onKey) else UIS.InputBegan:Connect(onKey) end
-- the close button and RESET live in the page; it tells us when it closed itself
lp:GetAttributeChangedSignal("SettingsOpen"):Connect(function()
	local v = lp:GetAttribute("SettingsOpen") == true
	if v ~= open then open = v; UI.setOpen(v) end
end)
local _ = UI.isOpen

-- hide the mouse arrow under the crosshair. the page is one of the menus that need it (MenuCursor: the mouse is free
-- and shows while any is up); a menu or cinematic that only holds still (LoadoutOpen) keeps it as before
RunService.RenderStepped:Connect(function()
	if open and not UI.isOpen() then open = false; lp:SetAttribute("SettingsOpen", false) end
	if MenuCursor.has("settings") ~= open then MenuCursor.set("settings", open) end
	UIS.MouseIconEnabled = open or MenuCursor.on() or lp:GetAttribute("LoadoutOpen") == true
end)
