--!strict
-- the HUD: a speedometer and the big callouts, in JANKFIRE's comic look (dark purple panel, thick pink border, hard
-- cyan offset shadow, yellow, Comic Neue). Roblox has no box-shadow, so the shadow is a cyan frame behind, offset 8 px
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local PINK, YELLOW, CYAN, PANEL = Color3.fromRGB(255, 79, 216), Color3.fromRGB(255, 225, 77), Color3.fromRGB(79, 216, 255), Color3.fromRGB(18, 8, 24)
local FONT = Font.new("rbxasset://fonts/families/ComicNeueAngular.json", Enum.FontWeight.Bold)

local Hud = {}
local gui = Instance.new("ScreenGui")
gui.Name = "JankfireHud"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = true
gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")

local function panel(name: string, pos: UDim2, size: UDim2): (Frame, TextLabel)
	local shadow = Instance.new("Frame")
	shadow.Name = name .. "Shadow"; shadow.BackgroundColor3 = CYAN; shadow.BorderSizePixel = 0
	shadow.Position = pos + UDim2.fromOffset(8, 8); shadow.Size = size; shadow.Rotation = -1.5
	shadow.Parent = gui
	local f = Instance.new("Frame")
	f.Name = name; f.BackgroundColor3 = PANEL; f.BackgroundTransparency = 0.08; f.BorderSizePixel = 0
	f.Position = pos; f.Size = size; f.Rotation = -1.5
	local st = Instance.new("UIStroke"); st.Color = PINK; st.Thickness = 4; st.ApplyStrokeMode = Enum.ApplyStrokeMode.Border; st.Parent = f
	f.Parent = gui
	local t = Instance.new("TextLabel")
	t.BackgroundTransparency = 1; t.Size = UDim2.fromScale(1, 1); t.FontFace = FONT; t.TextScaled = true
	t.TextColor3 = YELLOW; t.Text = ""; t.Parent = f
	return f, t
end

local _, speedText = panel("Speed", UDim2.new(0, 24, 1, -96), UDim2.fromOffset(190, 60))

local call = Instance.new("TextLabel")
call.Name = "Callout"; call.BackgroundTransparency = 1; call.AnchorPoint = Vector2.new(0.5, 0.5)
call.Position = UDim2.fromScale(0.5, 0.3); call.Size = UDim2.fromScale(0.6, 0.11); call.FontFace = FONT; call.TextScaled = true
call.TextColor3 = YELLOW; call.TextStrokeColor3 = Color3.new(0, 0, 0); call.TextStrokeTransparency = 0; call.Text = ""; call.Rotation = -3
call.Parent = gui
local callShadow = call:Clone()
callShadow.Name = "CalloutShadow"; callShadow.TextColor3 = PINK; callShadow.TextStrokeTransparency = 1; callShadow.ZIndex = 0
callShadow.Position = call.Position + UDim2.fromOffset(6, 6); callShadow.Parent = gui

local hint = Instance.new("TextLabel")
hint.Name = "Keys"; hint.BackgroundTransparency = 1; hint.AnchorPoint = Vector2.new(1, 1)
hint.Position = UDim2.new(1, -16, 1, -12); hint.Size = UDim2.fromOffset(420, 22); hint.FontFace = FONT; hint.TextSize = 18
hint.TextColor3 = Color3.new(1, 1, 1); hint.TextXAlignment = Enum.TextXAlignment.Right; hint.TextStrokeTransparency = 0.4
hint.Text = "shift run · C slide · hold E grapple · space on rope = fling · V camera"
hint.Parent = gui

local token = 0
function Hud.callout(text: string, dur: number)
	token += 1
	local my = token
	call.Text = text; callShadow.Text = text
	call.TextTransparency = 0; callShadow.TextTransparency = 0
	call.Size = UDim2.fromScale(0.75, 0.14)
	TweenService:Create(call, TweenInfo.new(0.12, Enum.EasingStyle.Back), { Size = UDim2.fromScale(0.6, 0.11) }):Play()
	task.delay(dur, function()
		if my ~= token then return end
		TweenService:Create(call, TweenInfo.new(0.2), { TextTransparency = 1 }):Play()
		TweenService:Create(callShadow, TweenInfo.new(0.2), { TextTransparency = 1 }):Play()
	end)
end

function Hud.speed(ms: number, sliding: boolean, hooked: boolean)
	speedText.Text = string.format("%d m/s%s", math.floor(ms + 0.5), if sliding then " SLIDE" elseif hooked then " ROPE" else "")
	speedText.TextColor3 = if ms > 20 then PINK else YELLOW
end

-- the server's callouts (e.g. "INTO THE SMOG")
local remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local co = remotes:WaitForChild("Callout") :: RemoteEvent
co.OnClientEvent:Connect(function(text: unknown, dur: unknown)
	if typeof(text) == "string" then Hud.callout(text, if typeof(dur) == "number" then dur else 1.2) end
end)

return Hud
