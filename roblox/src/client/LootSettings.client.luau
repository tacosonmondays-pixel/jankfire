-- "SHOW MY OPENINGS TO OTHERS" in the settings panel (P, JankSettings): the owner, 16 Nov: "when they're on the ground,
-- other people can see it and what you get! you can disable that option in the settings like hide it from other
-- people". on by default; kept with your things on the server (Loot.luau op "setting"; it publishes the player
-- attribute LootShowOpenings). this script adds its row at the bottom of the panel and makes the panel taller, so it
-- needs no edit in JankSettings (other rows there: theirs). the switch looks like the panel's others: a track, a knob
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local lp = Players.LocalPlayer
local T = require(script.Parent:WaitForChild("Theme"))
local gui = lp:WaitForChild("PlayerGui"):WaitForChild("JankSettings", 60)
local panel = gui and gui:WaitForChild("Panel", 30)
if not panel or not panel:IsA("GuiObject") then return end
task.wait(1) -- (the panel's own rows are made in the same breath as the panel: let them all land first)

local ROW = 48
local y = panel.Size.Y.Offset - 8
panel.Size += UDim2.fromOffset(0, ROW)
local row = T.new("TextButton", { Name = "ShowOpenings", AutoButtonColor = false, Text = "", BackgroundTransparency = 1,
	Position = UDim2.fromOffset(0, y), Size = UDim2.new(1, 0, 0, ROW) }, panel)
local label = T.text(row, "Label", "SHOW MY OPENINGS", 12, T.MUTED, T.FONT_BOLD)
label.Position = UDim2.fromOffset(24, 8)
label.Size = UDim2.fromOffset(240, 16)
local sub = T.text(row, "Sub", "people near you see what you open", 12, T.DIM)
sub.Position = UDim2.fromOffset(24, 26)
sub.Size = UDim2.fromOffset(260, 16)
local sw = T.new("Frame", { Name = "Switch", AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -24, 0.5, 0), Size = UDim2.fromOffset(52, 28),
	BackgroundColor3 = T.TRACK, BorderSizePixel = 0 }, row)
T.corner(sw, 14)
local knob = T.new("Frame", { Size = UDim2.fromOffset(22, 22), Position = UDim2.fromOffset(3, 3), BackgroundColor3 = T.TEXT, BorderSizePixel = 0 }, sw)
T.corner(knob, 11)

local busy = false
local function paint()
	local on = lp:GetAttribute("LootShowOpenings") ~= false
	sw.BackgroundColor3 = if on then T.ACCENT else T.TRACK
	knob.Position = if on then UDim2.fromOffset(27, 3) else UDim2.fromOffset(3, 3)
end
paint()
lp:GetAttributeChangedSignal("LootShowOpenings"):Connect(paint)
row.MouseButton1Click:Connect(function()
	if busy then return end
	local rs = ReplicatedStorage:FindFirstChild("JankfireRemotes")
	local fn = rs and rs:FindFirstChild("Loot")
	if not (fn and fn:IsA("RemoteFunction")) then return end
	busy = true
	local want = lp:GetAttribute("LootShowOpenings") == false
	-- (flip it at once; the server's answer puts it right if it said no)
	sw.BackgroundColor3 = if want then T.ACCENT else T.TRACK
	knob.Position = if want then UDim2.fromOffset(27, 3) else UDim2.fromOffset(3, 3)
	task.spawn(function()
		pcall(function() (fn :: RemoteFunction):InvokeServer("setting", "showOpenings", want) end)
		busy = false
		paint()
	end)
end)
