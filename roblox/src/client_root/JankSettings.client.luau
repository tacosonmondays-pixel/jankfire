-- the crosshair, and a little settings panel on P: field of view and mouse sensitivity.
-- comic look: dark purple panel, thick pink border, hard cyan shadow, yellow fill, Comic Neue.
local Players = game:GetService("Players")
local UIS = game:GetService("UserInputService")
local RunService = game:GetService("RunService")

local lp = Players.LocalPlayer
local PINK, CYAN, YELLOW = Color3.fromRGB(255, 79, 216), Color3.fromRGB(79, 216, 255), Color3.fromRGB(255, 225, 77)
local PANEL = Color3.fromRGB(18, 8, 24)
local FONT = Font.new("rbxasset://fonts/families/ComicNeueAngular.json", Enum.FontWeight.Bold)
local S = { fov = 80, sens = 1 }
local FOV_MIN, FOV_MAX = 50, 120
local SENS_MIN, SENS_MAX = 0.1, 3

local gui = Instance.new("ScreenGui")
gui.Name = "JankSettings"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = true
gui.DisplayOrder = 20
gui.Parent = lp:WaitForChild("PlayerGui")

-- crosshair: four short white bars and a dot, black outlines so it reads on the night sky and the bright signs
local cross = Instance.new("Frame")
cross.Name = "Crosshair"
cross.AnchorPoint = Vector2.new(0.5, 0.5)
cross.Position = UDim2.fromScale(0.5, 0.5)
cross.Size = UDim2.fromOffset(30, 30)
cross.BackgroundTransparency = 1
cross.Parent = gui
cross.Visible = false -- the weapons' FightHud draws the crosshair now
local function bar(x, y, w, h)
	local f = Instance.new("Frame")
	f.AnchorPoint = Vector2.new(0.5, 0.5)
	f.Position = UDim2.new(0.5, x, 0.5, y)
	f.Size = UDim2.fromOffset(w, h)
	f.BackgroundColor3 = Color3.new(1, 1, 1)
	f.BorderSizePixel = 0
	local st = Instance.new("UIStroke"); st.Thickness = 1.5; st.Color = Color3.new(0, 0, 0); st.Parent = f
	f.Parent = cross
	return f
end
bar(0, -9, 3, 8); bar(0, 9, 3, 8); bar(-9, 0, 8, 3); bar(9, 0, 8, 3)
local dot = bar(0, 0, 3, 3)
dot.BackgroundColor3 = PINK

local hint = Instance.new("TextLabel")
hint.AnchorPoint = Vector2.new(1, 0)
hint.Position = UDim2.new(1, -14, 0, 10)
hint.Size = UDim2.fromOffset(140, 22)
hint.BackgroundTransparency = 1
hint.FontFace = FONT
hint.TextSize = 16
hint.TextXAlignment = Enum.TextXAlignment.Right
hint.TextColor3 = Color3.new(1, 1, 1)
hint.TextStrokeTransparency = 0
hint.Text = "P = settings"
hint.Parent = gui

-- the panel
local shadow = Instance.new("Frame")
shadow.AnchorPoint = Vector2.new(0.5, 0.5)
shadow.Position = UDim2.new(0.5, 8, 0.5, 8)
shadow.Size = UDim2.fromOffset(360, 230)
shadow.BackgroundColor3 = CYAN
shadow.BorderSizePixel = 0
shadow.Visible = false
shadow.Parent = gui
local panel = Instance.new("TextButton") -- a button so Modal can free the mouse from first person while it's open
panel.AutoButtonColor = false
panel.Text = ""
panel.Modal = true
panel.AnchorPoint = Vector2.new(0.5, 0.5)
panel.Position = UDim2.fromScale(0.5, 0.5)
panel.Size = UDim2.fromOffset(360, 230)
panel.BackgroundColor3 = PANEL
panel.BackgroundTransparency = 0.08
panel.BorderSizePixel = 0
panel.Rotation = -1
panel.Visible = false
panel.Parent = gui
local ps = Instance.new("UIStroke"); ps.Thickness = 4; ps.Color = PINK; ps.ApplyStrokeMode = Enum.ApplyStrokeMode.Border; ps.Parent = panel
shadow.Rotation = -1

local function text(parent, t, size, pos, sz, align)
	local l = Instance.new("TextLabel")
	l.BackgroundTransparency = 1
	l.FontFace = FONT
	l.TextSize = size
	l.TextColor3 = Color3.new(1, 1, 1)
	l.TextStrokeTransparency = 0.4
	l.TextXAlignment = align or Enum.TextXAlignment.Left
	l.Position = pos
	l.Size = sz
	l.Text = t
	l.Parent = parent
	return l
end
local title = text(panel, "SETTINGS", 30, UDim2.fromOffset(18, 10), UDim2.fromOffset(200, 36))
title.TextColor3 = YELLOW
local close = Instance.new("TextButton")
close.AnchorPoint = Vector2.new(1, 0)
close.Position = UDim2.new(1, -14, 0, 14)
close.Size = UDim2.fromOffset(30, 30)
close.BackgroundColor3 = Color3.fromRGB(255, 48, 48)
close.BorderSizePixel = 0
close.FontFace = FONT
close.TextSize = 20
close.TextColor3 = Color3.new(1, 1, 1)
close.Text = "X"
local cs = Instance.new("UIStroke"); cs.Thickness = 2; cs.Color = Color3.new(0, 0, 0); cs.ApplyStrokeMode = Enum.ApplyStrokeMode.Border; cs.Parent = close
close.Parent = panel

-- a slider: label + value, a bar with a yellow fill and a white knob with a hard shadow
local dragging = nil
local function slider(y, name, min, max, get, set, fmt)
	local label = text(panel, "", 20, UDim2.fromOffset(18, y), UDim2.fromOffset(320, 24))
	local bg = Instance.new("Frame")
	bg.Position = UDim2.fromOffset(20, y + 32)
	bg.Size = UDim2.fromOffset(318, 14)
	bg.BackgroundColor3 = Color3.fromRGB(45, 25, 60)
	bg.BorderSizePixel = 0
	local bs = Instance.new("UIStroke"); bs.Thickness = 2; bs.Color = Color3.new(0, 0, 0); bs.Parent = bg
	bg.Parent = panel
	local fill = Instance.new("Frame")
	fill.BackgroundColor3 = YELLOW
	fill.BorderSizePixel = 0
	fill.Parent = bg
	local knobShadow = Instance.new("Frame")
	knobShadow.AnchorPoint = Vector2.new(0.5, 0.5)
	knobShadow.Size = UDim2.fromOffset(18, 24)
	knobShadow.BackgroundColor3 = PINK
	knobShadow.BorderSizePixel = 0
	knobShadow.Parent = bg
	local knob = Instance.new("Frame")
	knob.AnchorPoint = Vector2.new(0.5, 0.5)
	knob.Size = UDim2.fromOffset(18, 24)
	knob.BackgroundColor3 = Color3.new(1, 1, 1)
	knob.BorderSizePixel = 0
	local ks = Instance.new("UIStroke"); ks.Thickness = 2; ks.Color = Color3.new(0, 0, 0); ks.Parent = knob
	knob.Parent = bg
	local s = { bg = bg }
	function s.refresh()
		local u = (get() - min) / (max - min)
		fill.Size = UDim2.fromScale(u, 1)
		knob.Position = UDim2.fromScale(u, 0.5)
		knobShadow.Position = UDim2.new(u, 4, 0.5, 4)
		label.Text = name .. "   " .. fmt(get())
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
local fovS = slider(62, "FIELD OF VIEW", FOV_MIN, FOV_MAX, function() return S.fov end, function(v) S.fov = math.floor(v + 0.5) end, function(v) return tostring(v) end)
local sensS = slider(140, "MOUSE SENSITIVITY", SENS_MIN, SENS_MAX, function() return S.sens end, function(v) S.sens = math.floor(v * 20 + 0.5) / 20 end, function(v) return string.format("%.2fx", v) end)

UIS.InputChanged:Connect(function(io)
	if dragging and (io.UserInputType == Enum.UserInputType.MouseMovement or io.UserInputType == Enum.UserInputType.Touch) then dragging.setFromX(io.Position.X) end
end)
UIS.InputEnded:Connect(function(io)
	if io.UserInputType == Enum.UserInputType.MouseButton1 or io.UserInputType == Enum.UserInputType.Touch then dragging = nil end
end)

local open = false
local function setOpen(v)
	open = v
	panel.Visible = v
	shadow.Visible = v
	cross.Visible = false
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
