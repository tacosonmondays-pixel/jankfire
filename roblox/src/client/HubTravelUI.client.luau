--!strict
-- the HUBS chooser (20 Nov 2026; the owner: "let me have an option to travel between hubs"): a small panel listing the
-- hubs (the one you're in marked, how many people are in each), opened by a hub's travel terminal (a ProximityPrompt
-- with the attribute HubTravel) or the HUBS entry in the hub's left menu (it fires this script's OpenHubs). Picking one
-- fades the screen out, asks the server to move you (JankfireRemotes.HubTravel "go"), and fades back in there.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local ProximityPromptService = game:GetService("ProximityPromptService")
local UserInputService = game:GetService("UserInputService")

local me = Players.LocalPlayer
local rf = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("HubTravel") :: RemoteFunction
local MenuCursor = require(script.Parent:WaitForChild("MenuCursor")) :: any -- (the mouse free while the chooser is up: the hub is first person)
local MenuGate = require(script.Parent:WaitForChild("MenuGate")) :: any

local open = Instance.new("BindableEvent")
open.Name = "OpenHubs"
open.Parent = script

local gui = Instance.new("ScreenGui")
gui.Name = "HubTravel"; gui.ResetOnSpawn = false; gui.IgnoreGuiInset = true; gui.DisplayOrder = 40
gui.Parent = me:WaitForChild("PlayerGui")

local fade = Instance.new("Frame")
fade.Name = "Fade"; fade.Size = UDim2.fromScale(1, 1); fade.BackgroundColor3 = Color3.new(0, 0, 0); fade.BackgroundTransparency = 1
fade.BorderSizePixel = 0; fade.ZIndex = 50; fade.Parent = gui

local panel = Instance.new("Frame")
panel.Name = "Panel"; panel.AnchorPoint = Vector2.new(0.5, 0.5); panel.Position = UDim2.fromScale(0.5, 0.5)
panel.Size = UDim2.fromOffset(420, 120); panel.BackgroundColor3 = Color3.fromHex("15181d"); panel.BackgroundTransparency = 0.08
panel.BorderSizePixel = 0; panel.Visible = false; panel.ZIndex = 20; panel.Parent = gui
Instance.new("UICorner", panel).CornerRadius = UDim.new(0, 10)
local stroke = Instance.new("UIStroke", panel); stroke.Color = Color3.fromHex("b3aea4"); stroke.Transparency = 0.6; stroke.Thickness = 1.5
local pad = Instance.new("UIPadding", panel)
pad.PaddingTop = UDim.new(0, 14); pad.PaddingBottom = UDim.new(0, 14); pad.PaddingLeft = UDim.new(0, 16); pad.PaddingRight = UDim.new(0, 16)
local list = Instance.new("UIListLayout", panel); list.Padding = UDim.new(0, 8); list.SortOrder = Enum.SortOrder.LayoutOrder

local function label(parent: Instance, text: string, size: number, font: Enum.Font, color: string, order: number): TextLabel
	local t = Instance.new("TextLabel")
	t.BackgroundTransparency = 1; t.Text = text; t.TextSize = size; t.Font = font; t.TextColor3 = Color3.fromHex(color)
	t.TextXAlignment = Enum.TextXAlignment.Left; t.Size = UDim2.new(1, 0, 0, size + 6); t.LayoutOrder = order; t.ZIndex = 21
	t.Parent = parent
	return t
end

local busy = false
local function close()
	panel.Visible = false
	MenuCursor.set("hubs", false)
end
local function travel(id: string)
	if busy then return end
	busy = true
	close()
	TweenService:Create(fade, TweenInfo.new(0.25), { BackgroundTransparency = 0 }):Play()
	task.wait(0.27)
	local ok, res, why = pcall(function() return rf:InvokeServer("go", id) end)
	task.wait(if ok and res then 0.25 else 0.05)
	TweenService:Create(fade, TweenInfo.new(0.35), { BackgroundTransparency = 1 }):Play()
	if not (ok and res) then -- (why not, for a moment at the top of the screen)
		local t = Instance.new("TextLabel")
		t.AnchorPoint = Vector2.new(0.5, 0); t.Position = UDim2.new(0.5, 0, 0, 90); t.Size = UDim2.fromOffset(420, 30)
		t.BackgroundColor3 = Color3.fromHex("15181d"); t.BackgroundTransparency = 0.2; t.BorderSizePixel = 0
		t.Text = ("CAN'T TRAVEL: %s"):format(string.upper(tostring(if ok then why else "try again"))); t.Font = Enum.Font.GothamBlack
		t.TextSize = 15; t.TextColor3 = Color3.fromHex("e8ecef"); t.ZIndex = 30; t.Parent = gui
		Instance.new("UICorner", t).CornerRadius = UDim.new(0, 6)
		task.delay(2.2, function() t:Destroy() end)
	end
	busy = false
end

local function show()
	if busy or not MenuGate.allowed("hubs") then return end
	local ok, hubs = pcall(function() return rf:InvokeServer("list") end)
	if not ok or type(hubs) ~= "table" then return end
	for _, c in panel:GetChildren() do if c:IsA("GuiObject") then c:Destroy() end end
	label(panel, "HUBS", 22, Enum.Font.GothamBlack, "e8ecef", 0)
	for i, h in hubs do
		local row = Instance.new("Frame")
		row.Size = UDim2.new(1, 0, 0, 44); row.BackgroundColor3 = Color3.fromHex(if h.here then "2a3038" else "20242b")
		row.BorderSizePixel = 0; row.LayoutOrder = i; row.ZIndex = 21; row.Parent = panel
		Instance.new("UICorner", row).CornerRadius = UDim.new(0, 8)
		local name = Instance.new("TextLabel")
		name.BackgroundTransparency = 1; name.Position = UDim2.fromOffset(12, 0); name.Size = UDim2.new(1, -140, 1, 0)
		name.Text = tostring(h.title); name.Font = Enum.Font.GothamBlack; name.TextSize = 18; name.TextColor3 = Color3.fromHex("e8ecef")
		name.TextXAlignment = Enum.TextXAlignment.Left; name.ZIndex = 22; name.Parent = row
		local count = Instance.new("TextLabel")
		count.BackgroundTransparency = 1; count.AnchorPoint = Vector2.new(1, 0); count.Position = UDim2.new(1, -112, 0, 0); count.Size = UDim2.fromOffset(60, 44)
		count.Text = ("%d here"):format(tonumber(h.players) or 0); count.Font = Enum.Font.GothamSemibold; count.TextSize = 14
		count.TextColor3 = Color3.fromHex("9fa8b2"); count.ZIndex = 22; count.Parent = row
		local b = Instance.new("TextButton")
		b.AnchorPoint = Vector2.new(1, 0.5); b.Position = UDim2.new(1, -8, 0.5, 0); b.Size = UDim2.fromOffset(96, 32)
		b.BackgroundColor3 = Color3.fromHex(if h.here then "3a3f47" else "e9a64a"); b.AutoButtonColor = not h.here
		b.Text = if h.here then "YOU'RE HERE" else "GO"; b.Font = Enum.Font.GothamBlack; b.TextSize = if h.here then 12 else 16
		b.TextColor3 = Color3.fromHex(if h.here then "c8cdd6" else "15181d"); b.ZIndex = 22; b.Parent = row
		Instance.new("UICorner", b).CornerRadius = UDim.new(0, 6)
		if not h.here then b.Activated:Connect(function() travel(h.id) end) end
	end
	local x = Instance.new("TextButton")
	x.Size = UDim2.new(1, 0, 0, 30); x.LayoutOrder = 99; x.BackgroundTransparency = 1; x.Text = "CLOSE"
	x.Font = Enum.Font.GothamSemibold; x.TextSize = 14; x.TextColor3 = Color3.fromHex("9fa8b2"); x.ZIndex = 21; x.Parent = panel
	x.Activated:Connect(close)
	panel.Size = UDim2.fromOffset(420, 14 + 28 + #hubs * 52 + 38 + 14)
	panel.Visible = true
	MenuCursor.set("hubs", true, function() return panel.Visible end)
end

open.Event:Connect(show)

-- the HUBS button in the hub's left menu (HubStack), like the SHOP one: shown in the hub only
do
	local RunService = game:GetService("RunService")
	local T = require(script.Parent:WaitForChild("Theme")) :: any
	local hud = T.new("ScreenGui", { Name = "JankHubsButton", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 6, ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, me:WaitForChild("PlayerGui"))
	local face = T.new("TextButton", {
		Name = "Hubs", AutoButtonColor = false, BackgroundColor3 = T.BG, BackgroundTransparency = T.BG_A, BorderSizePixel = 0,
		Position = require(script.Parent:WaitForChild("HubStack")).pos("Hubs"), Size = UDim2.fromOffset(136, 36), FontFace = T.FONT_BOLD, TextSize = 13, Text = "HUBS",
		TextColor3 = T.TEXT, TextXAlignment = Enum.TextXAlignment.Left,
	}, T.scaled(hud))
	T.corner(face); T.edge(face)
	T.new("UIPadding", { PaddingLeft = UDim.new(0, 42) }, face)
	T.key(face, "H", UDim2.fromOffset(-34, 7))
	-- (27 Nov 2026: the look is HubStack.style's: the hub menu in A PLATE, the owner's pick from the ui-mocks sheet)
	require(script.Parent:WaitForChild("HubStack")).style(face, "Hubs")
	face.MouseButton1Click:Connect(show)
	-- H opens and closes it, where the button shows
	UserInputService.InputBegan:Connect(function(io: InputObject, gp: boolean)
		if gp or io.KeyCode ~= Enum.KeyCode.H then return end
		if panel.Visible then close() elseif face.Visible then show() end
	end)
	RunService.Heartbeat:Connect(function()
		local z = me:GetAttribute("Zone")
		local vis = (z == nil or z == "hub") and not me:GetAttribute("LoadoutOpen") and me:GetAttribute("Lobby") == nil
		if face.Visible ~= vis then face.Visible = vis end
	end)
end
ProximityPromptService.PromptTriggered:Connect(function(prompt: ProximityPrompt)
	if prompt:GetAttribute("HubTravel") == true then show() end
end)
UserInputService.InputBegan:Connect(function(io: InputObject, gp: boolean)
	if not gp and io.KeyCode == Enum.KeyCode.Escape and panel.Visible then close() end
end)
