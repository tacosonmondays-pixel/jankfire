-- the settings panel on P: field of view and mouse sensitivity (Jankfire.Theme has the look: a dark card, white text,
-- amber slider fills). the crosshair is FightHud's
local Players = game:GetService("Players")
local UIS = game:GetService("UserInputService")
local RunService = game:GetService("RunService")

local lp = Players.LocalPlayer
local T = require(script.Parent:WaitForChild("Jankfire"):WaitForChild("Theme"))
local S = { fov = 80, sens = 1 }
local FOV_MIN, FOV_MAX = 50, 120
local SENS_MIN, SENS_MAX = 0.1, 3

local gui = Instance.new("ScreenGui")
gui.Name = "JankSettings"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = true
gui.DisplayOrder = 20
gui.Parent = lp:WaitForChild("PlayerGui")

-- the reminder, top right
local hint = T.plate(T.scaled(gui), "Hint", UDim2.new(1, -136, 0, 14), UDim2.fromOffset(112, 30))
T.key(hint, "P", UDim2.fromOffset(5, 4))
local hintText = T.text(hint, "Text", "settings", 13, T.MUTED, T.FONT_BOLD)
hintText.Position = UDim2.fromOffset(36, 0)
hintText.Size = UDim2.new(1, -40, 1, 0)

-- the panel, on a dimmed screen
local scrim = T.new("Frame", { Name = "Scrim", BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 0.5, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), Visible = false }, gui)
local panel = T.new("TextButton", { -- a button so Modal can free the mouse from first person while it's open
	Name = "Panel", AutoButtonColor = false, Text = "", Modal = true, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
	Size = UDim2.fromOffset(380, 210), BackgroundColor3 = T.BG, BackgroundTransparency = 0, BorderSizePixel = 0, Visible = false,
}, gui)
T.corner(panel, 8)
T.edge(panel)
local panelScale = T.new("UIScale", { Scale = T.scaleNow() }, panel) -- (it grows with the screen, like the HUD)
local title = T.text(panel, "Title", "SETTINGS", 18, T.TEXT, T.FONT_TITLE)
title.Position = UDim2.fromOffset(24, 24)
title.Size = UDim2.fromOffset(220, 24)
local close = T.new("TextButton", {
	Name = "Close", AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -24, 0, 22), Size = UDim2.fromOffset(28, 28), AutoButtonColor = false,
	BackgroundColor3 = T.CARD, BorderSizePixel = 0, Text = "",
}, panel)
T.corner(close, 4)
-- (the cross is drawn: two thin bars)
local crossBars = {}
for _, rot in { 45, -45 } do
	table.insert(crossBars, T.new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(14, 2), Rotation = rot, BackgroundColor3 = T.MUTED, BorderSizePixel = 0 }, close))
end
close.MouseEnter:Connect(function() close.BackgroundColor3 = T.CARD_HI; for _, b in crossBars do b.BackgroundColor3 = T.TEXT end end)
close.MouseLeave:Connect(function() close.BackgroundColor3 = T.CARD; for _, b in crossBars do b.BackgroundColor3 = T.MUTED end end)

-- a slider: its name on the left and its value on the right, a thin track with an amber fill and a round white knob
local dragging = nil
local function slider(y, name, min, max, get, set, fmt)
	local label = T.text(panel, "Label", name, 12, T.MUTED, T.FONT_BOLD)
	label.Position = UDim2.fromOffset(24, y)
	label.Size = UDim2.fromOffset(220, 16)
	local value = T.text(panel, "Value", "", 15, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Right)
	value.Position = UDim2.new(1, -124, 0, y - 2)
	value.Size = UDim2.fromOffset(100, 18)
	local bg = T.new("Frame", { Name = "Track", Position = UDim2.fromOffset(24, y + 32), Size = UDim2.new(1, -48, 0, 8), BackgroundColor3 = T.TRACK, BorderSizePixel = 0 }, panel)
	T.corner(bg, 4)
	local fill = T.new("Frame", { Name = "Fill", BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Size = UDim2.fromScale(0, 1) }, bg)
	T.corner(fill, 4)
	local knob = T.new("Frame", { Name = "Knob", AnchorPoint = Vector2.new(0.5, 0.5), Size = UDim2.fromOffset(18, 18), BackgroundColor3 = T.TEXT, BorderSizePixel = 0, ZIndex = 2 }, bg)
	T.corner(knob, 9)
	T.edge(knob, T.BG, 0, 2)
	local s = { bg = bg }
	function s.refresh()
		local u = (get() - min) / (max - min)
		fill.Size = UDim2.fromScale(u, 1)
		knob.Position = UDim2.fromScale(u, 0.5)
		value.Text = fmt(get())
	end
	function s.setFromX(x)
		local u = math.clamp((x - bg.AbsolutePosition.X) / bg.AbsoluteSize.X, 0, 1)
		set(min + (max - min) * u)
		s.refresh()
	end
	local grab = Instance.new("TextButton") -- a taller invisible hit area over the bar
	grab.BackgroundTransparency = 1
	grab.Text = ""
	grab.Position = UDim2.new(0, -6, 0, -10)
	grab.Size = UDim2.new(1, 12, 1, 20)
	grab.ZIndex = 3
	grab.Parent = bg
	grab.MouseButton1Down:Connect(function(x) dragging = s; s.setFromX(x) end)
	s.refresh()
	return s
end
local fovS = slider(74, "FIELD OF VIEW", FOV_MIN, FOV_MAX, function() return S.fov end, function(v) S.fov = math.floor(v + 0.5) end, function(v) return tostring(v) end)
local sensS = slider(146, "MOUSE SENSITIVITY", SENS_MIN, SENS_MAX, function() return S.sens end, function(v) S.sens = math.floor(v * 20 + 0.5) / 20 end, function(v) return string.format("%.2fx", v) end)

UIS.InputChanged:Connect(function(io)
	if dragging and (io.UserInputType == Enum.UserInputType.MouseMovement or io.UserInputType == Enum.UserInputType.Touch) then dragging.setFromX(io.Position.X) end
end)
UIS.InputEnded:Connect(function(io)
	if io.UserInputType == Enum.UserInputType.MouseButton1 or io.UserInputType == Enum.UserInputType.Touch then dragging = nil end
end)

local open = false
local function setOpen(v)
	open = v
	panelScale.Scale = T.scaleNow()
	panel.Visible = v
	scrim.Visible = v
	lp:SetAttribute("SettingsOpen", v) -- (FightHud hides the crosshair under the panel)
	dragging = nil
end
close.MouseButton1Click:Connect(function() setOpen(false) end)
UIS.InputBegan:Connect(function(io, gp)
	if gp then return end
	if io.KeyCode == Enum.KeyCode.P then setOpen(not open) end
end)

-- keep the camera on your settings (a new camera or a respawn won't undo them); hide the mouse arrow under the crosshair
RunService.RenderStepped:Connect(function()
	local cam = workspace.CurrentCamera
	local lp = game:GetService("Players").LocalPlayer
	if lp:GetAttribute("BaseFov") ~= S.fov then lp:SetAttribute("BaseFov", S.fov) end -- Arsenal applies it (and the ADS zoom)
	if UIS.MouseDeltaSensitivity ~= S.sens then UIS.MouseDeltaSensitivity = S.sens end
	UIS.MouseIconEnabled = open or lp:GetAttribute("LoadoutOpen") == true -- (the loadout screen needs the arrow too)
end)
