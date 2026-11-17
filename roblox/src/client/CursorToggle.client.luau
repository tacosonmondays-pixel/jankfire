-- Toggle Cursor (the owner, 17 Nov: "allow a button to toggle mouse cursor"). Left Alt, or the player's own key
-- (Settings > KEYBINDS: TOGGLE CURSOR), frees the mouse and shows the arrow without opening a menu; pressed again it
-- locks again. it's one of MenuCursor's names ("toggle", cursor only), so it never fights the menus: with a menu up
-- the mouse is free anyway and the key only turns the toggle off; turned off under a menu, the menu keeps the mouse.
-- while it's on:
--   the camera holds its look (MenuCursor: the mouse no longer turns first person or the shoulder camera);
--   clicks don't fire, swing or aim (Arsenal reads MenuCursor; a Tool in your hands, the Shredder, is set to
--   ManualActivationOnly so a click can't start it);
--   movement, jumping, reloads and the other keys work as normal (it isn't a menu: LoadoutOpen stays as it was);
--   a small plate at the top in the middle says CURSOR FREE and the key.
-- it turns itself off at a death, a respawn and a round's start. phones have no mouse: the key does nothing there.
-- (Studio tests: the player attribute CursorFree is true while it's on; CursorTest = "on" / "off" sets it)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local me = Players.LocalPlayer
local J = script.Parent
local Binds = require(J:WaitForChild("Binds")) :: any
local MenuCursor = require(J:WaitForChild("MenuCursor")) :: any
local T = require(J:WaitForChild("Theme")) :: any
local Keys = require(J:WaitForChild("Keys")) :: any

-- the plate (its ScreenGui stays on: the menus switch other screens off and back on as they open and close, so the
-- plate's own Visible says whether it shows)
local gui = T.new("ScreenGui", { Name = "JankCursorFree", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 45,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, me:WaitForChild("PlayerGui"))
local plate = T.plate(T.scaled(gui), "Hint", UDim2.new(0.5, -72, 0, 66), UDim2.fromOffset(144, 30))
plate.Visible = false
local label = T.text(plate, "Text", "CURSOR FREE", 13, T.TEXT, T.FONT_BOLD)
label.Position = UDim2.fromOffset(12, 0)
label.Size = UDim2.new(1, -24, 1, 0)
local cap = T.key(plate, "Alt", UDim2.fromOffset(0, 4))
local function layout()
	local k = Binds.label("cursor")
	local letter = cap:FindFirstChild("Letter") :: TextLabel?
	if letter then letter.Text = if k == "" then "-" else k end
	local cw = math.max(22, 10 + 8 * #k)
	cap.Size = UDim2.fromOffset(cw, 22)
	local tw = 96 -- ("CURSOR FREE" at 13)
	plate.Size = UDim2.fromOffset(12 + tw + 8 + cw + 5, 30)
	plate.Position = UDim2.new(0.5, -math.floor(plate.Size.X.Offset / 2), 0, 66)
	cap.Position = UDim2.fromOffset(12 + tw + 8, 4)
end
layout()

-- a Tool in your hands (the Shredder) starts on any click into the world: while the mouse is out, only a script can
local tools: { [Tool]: boolean } = {}
local function holdTools(on: boolean)
	if on then
		local ch = me.Character
		if not ch then return end
		for _, t in ch:GetChildren() do
			if t:IsA("Tool") and tools[t] == nil then
				tools[t] = t.ManualActivationOnly
				t.ManualActivationOnly = true
				pcall(function() t:Deactivate() end) -- (a trigger held as it came out lets go)
			end
		end
	else
		for t, was in tools do if t.Parent then t.ManualActivationOnly = was end end
		table.clear(tools)
	end
end

local on = false
local function set(v: boolean)
	if v == on then return end
	on = v
	MenuCursor.set("toggle", v, function() return on end, true)
	me:SetAttribute("CursorFree", if v then true else nil)
	if v then layout() end
	plate.Visible = v
	holdTools(v)
end

Keys.began(function(io: any, _gp: boolean)
	if Keys.fromTouch(io) or UIS:GetFocusedTextBox() or not UIS.MouseEnabled then return end
	if not Binds.is("cursor", io) then return end
	if on then set(false)
	elseif not MenuCursor.menu() then set(true) end -- (a menu up has the mouse already)
end)

-- off by itself: a death, a respawn, a round's start
local function watch(ch: Model)
	set(false)
	ch.ChildAdded:Connect(function(c) if on and c:IsA("Tool") then holdTools(true) end end)
	local hum = ch:WaitForChild("Humanoid", 10) :: Humanoid?
	if hum then hum.Died:Connect(function() set(false) end) end
end
me.CharacterAdded:Connect(watch)
if me.Character then task.spawn(watch, me.Character) end
task.spawn(function()
	local r = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Round", 60)
	if r and r:IsA("RemoteEvent") then
		r.OnClientEvent:Connect(function(m: any) if type(m) == "table" and m.start then set(false) end end)
	end
end)

if RunService:IsStudio() then
	me:GetAttributeChangedSignal("CursorTest"):Connect(function()
		local v = me:GetAttribute("CursorTest")
		if v == nil then return end
		me:SetAttribute("CursorTest", nil)
		if v == "on" then set(true) elseif v == "off" then set(false) end
	end)
end
