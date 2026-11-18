--!strict
-- THE CODE PANEL, on your screen (18 Nov 2026, the owner: "there should be a control panel somewhere that you type in
-- jank actually make codes and every code spawns in an NPC, ill give the codes weekly by weekly at some point"). The
-- terminal is workspace.Map.Lore.CodePanel (PolishBackup.LoreSpots builds it where L.PANEL says); its prompt opens a
-- small screen: CODE, a box, ENTER. The server checks the code (LoreNPCs.server, remote LoreCode); a right one closes
-- the screen and the NPC's cutscene plays (LoreLife.client). A reward code shows what it gave (its item names) in the
-- screen instead, or CLAIMED for one already used. Wrong: the box shakes and says so; too many
-- wrong: WAIT and the seconds left. Only in the hub (MenuGate "lorecode"); keyboard (the box takes the keys, Enter
-- sends, Esc closes), controller (PadNav: the box is picked first, A types, B backs out) and phone (tap the box for the
-- on-screen keyboard). It closes when you walk away from the panel or go into a match.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UIS = game:GetService("UserInputService")
local GuiService = game:GetService("GuiService")
local RunService = game:GetService("RunService")

local me = Players.LocalPlayer
local J = script.Parent
local T = require(J:WaitForChild("Theme")) :: any
local MenuCursor = require(J:WaitForChild("MenuCursor")) :: any
local MenuGate = require(J:WaitForChild("MenuGate")) :: any
local okPad, Pad = pcall(function() return require(J:WaitForChild("Pad", 5)) :: any end)
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local NAME = "lorecode" -- (MenuCursor / MenuGate / PadNav name)
local GUI = "JankCode"
local LEAVE = 16 -- studs from the panel: further and the screen closes
local MAXLEN = 24

local S = { gui = nil :: ScreenGui?, box = nil :: TextBox?, status = nil :: TextLabel?, enter = nil :: TextButton?, busy = false,
	waitUntil = 0, panel = nil :: Model? }

local function panelModel(): Model?
	local map = workspace:FindFirstChild("Map")
	local l = map and map:FindFirstChild("Lore")
	local m = l and l:FindFirstChild("CodePanel")
	return if m and m:IsA("Model") then m else nil
end

local function close()
	if S.gui then S.gui:Destroy() end
	S.gui, S.box, S.status, S.enter = nil, nil, nil, nil
	S.busy = false
	MenuCursor.set(NAME, false)
	if GuiService.SelectedObject then GuiService.SelectedObject = nil end
end

local function say(text: string, color: Color3?)
	if S.status then
		S.status.Text = text
		S.status.TextColor3 = color or T.SOFT
	end
end
local function shake()
	local b = S.box
	if not b then return end
	local x0 = b.Position
	task.spawn(function()
		for i, dx in { 8, -7, 5, -3, 0 } do
			if S.box ~= b then return end
			b.Position = x0 + UDim2.fromOffset(dx, 0)
			task.wait(0.04 + i * 0.005)
		end
		b.Position = x0
	end)
end

local function submit()
	local b = S.box
	if not b or S.busy then return end
	if os.clock() < S.waitUntil then return end
	local text = b.Text
	if string.gsub(text, "%s", "") == "" then return end
	local remote = Remotes:FindFirstChild("LoreCode")
	if not remote or not remote:IsA("RemoteFunction") then say("TRY AGAIN", T.DANGER); return end
	S.busy = true
	say("…")
	local g = S.gui
	local ok, res = pcall(function() return (remote :: RemoteFunction):InvokeServer("try", text) end)
	if S.gui ~= g then return end
	S.busy = false
	if not ok or type(res) ~= "table" then say("TRY AGAIN", T.DANGER); return end
	if res.ok and res.reward then
		-- a reward: what it gave, in the box's place (or CLAIMED), then the screen goes
		b.Visible = false
		if S.enter then S.enter.Visible = false end
		local list = T.text(b.Parent :: Instance, "Rewards", "", 16, T.ACCENT, T.FONT_HEAVY, Enum.TextXAlignment.Center)
		list.Position = UDim2.fromOffset(20, 52); list.Size = UDim2.fromOffset(300, 96)
		list.TextWrapped = true; list.TextYAlignment = Enum.TextYAlignment.Center
		if res.again then
			list.Text = "CLAIMED"; list.TextColor3 = T.MUTED
		else
			list.Text = table.concat(if type(res.items) == "table" then res.items else {}, "\n")
		end
		say("")
		task.delay(if res.again then 1.4 else 3.2, function() if S.gui == g then close() end end)
		return
	end
	if res.ok then
		say(if res.again then "FOUND" else "", T.ACCENT)
		b.Text = ""
		-- (closed at once: the cutscene is about to start, and it must not start with this menu still up)
		close()
		return
	end
	if res.why == "wait" then
		local secs = tonumber(res.wait) or 60
		S.waitUntil = os.clock() + secs
		b.Text = ""
		shake()
	elseif res.why == "wrong" then
		say("WRONG", T.DANGER)
		shake()
		b.Text = ""
		task.delay(1.4, function() if S.gui == g and S.status and S.status.Text == "WRONG" then say("") end end)
	elseif res.why == "far" then
		close()
	elseif res.why == "later" then
		say("TRY AGAIN", T.DANGER)
	else
		say("TRY AGAIN", T.DANGER)
	end
end

local function open()
	if S.gui then return end
	if not MenuGate.allowed(NAME) then return end
	local pm = panelModel()
	if not pm then return end
	S.panel = pm
	local g = T.new("ScreenGui", { Name = GUI, ResetOnSpawn = false, DisplayOrder = 70, IgnoreGuiInset = true, ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, me:WaitForChild("PlayerGui"))
	S.gui = g
	MenuCursor.set(NAME, true, function() return g.Parent ~= nil end)
	local root = T.scaled(g)
	-- (Modal: frees the mouse from first person while this is up. a tap outside does nothing: on a phone that's how
	-- the on-screen keyboard goes away)
	T.new("TextButton", { Name = "Scrim", Text = "", AutoButtonColor = false, Modal = true, Selectable = false, BackgroundColor3 = Color3.new(0, 0, 0),
		BackgroundTransparency = 0.55, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1) }, root)
	local W, H = 340, 182
	local plate = T.plate(root, "Panel", UDim2.new(0.5, -W / 2, 0.5, -H / 2 - 40), UDim2.fromOffset(W, H))
	plate.BackgroundTransparency = 0.04
	local title = T.text(plate, "Title", "CODE", 18, T.TEXT, T.FONT_TITLE)
	title.Position = UDim2.fromOffset(20, 16); title.Size = UDim2.fromOffset(200, 24)
	local x = T.new("TextButton", { Name = "Close", Text = "X", FontFace = T.FONT_BOLD, TextSize = 16, TextColor3 = T.MUTED, AutoButtonColor = true,
		BackgroundColor3 = T.CARD, BorderSizePixel = 0, Position = UDim2.fromOffset(W - 46, 14), Size = UDim2.fromOffset(30, 30) }, plate)
	T.corner(x, 4)
	x.Activated:Connect(close)
	local box = T.new("TextBox", {
		Name = "Box", Text = "", PlaceholderText = "", ClearTextOnFocus = false, MultiLine = false, TextEditable = true,
		FontFace = T.FONT_BOLD, TextSize = 24, TextColor3 = T.TEXT, TextXAlignment = Enum.TextXAlignment.Center,
		BackgroundColor3 = T.CARD, BorderSizePixel = 0, Position = UDim2.fromOffset(20, 54), Size = UDim2.fromOffset(W - 40, 46),
	}, plate) :: TextBox
	T.corner(box, 4)
	T.edge(box, nil, 0.8)
	S.box = box
	box:GetPropertyChangedSignal("Text"):Connect(function()
		if #box.Text > MAXLEN then box.Text = string.sub(box.Text, 1, MAXLEN) end
	end)
	box.FocusLost:Connect(function(enterPressed: boolean)
		if enterPressed then submit() end
	end)
	local enter = T.new("TextButton", {
		Name = "Enter", Text = "ENTER", FontFace = T.FONT_HEAVY, TextSize = 15, TextColor3 = T.INK, AutoButtonColor = true,
		BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Position = UDim2.fromOffset(20, 110), Size = UDim2.fromOffset(W - 40, 38),
	}, plate) :: TextButton
	T.corner(enter, 4)
	S.enter = enter
	enter.Activated:Connect(submit)
	local status = T.text(plate, "Status", "", 13, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Center)
	status.Position = UDim2.fromOffset(20, 154); status.Size = UDim2.fromOffset(W - 40, 18)
	S.status = status
	-- a controller: B backs out, the box is picked first (A on it brings up the pad's keyboard)
	if okPad and type(Pad) == "table" and Pad.MENUS then
		Pad.MENUS[NAME] = { gui = GUI, back = close, first = function(): GuiObject? return S.box end }
	end
	local padOn = okPad and type(Pad) == "table" and Pad.on and Pad.on()
	if padOn then
		GuiService.SelectedObject = box
	elseif UIS.KeyboardEnabled then
		task.defer(function() if S.box == box then box:CaptureFocus() end end)
	end
end

-- the panel's prompt (the panel may be built or moved after this starts: looked for again every few seconds)
local wired: { [Instance]: boolean } = {}
task.spawn(function()
	while true do
		local m = panelModel()
		if m then
			for _, d in m:GetDescendants() do
				if d:IsA("ProximityPrompt") and not wired[d] then
					wired[d] = true
					d.Triggered:Connect(open)
					d.Destroying:Connect(function() wired[d] = nil end)
				end
			end
		end
		task.wait(3)
	end
end)

UIS.InputBegan:Connect(function(io: InputObject)
	if S.gui and io.KeyCode == Enum.KeyCode.Escape then close() end
end)

-- the wait's countdown; walking off or a match closes it
RunService.Heartbeat:Connect(function()
	if not S.gui then return end
	local left = S.waitUntil - os.clock()
	if left > 0 then
		say(("WAIT %d"):format(math.ceil(left)), T.DANGER)
		if S.enter then S.enter.AutoButtonColor = false; S.enter.BackgroundColor3 = T.TRACK end
	elseif S.enter and S.enter.BackgroundColor3 == T.TRACK then
		S.enter.AutoButtonColor = true; S.enter.BackgroundColor3 = T.ACCENT
		say("")
	end
	if MenuGate.blocked() then close(); return end
	local ch = me.Character
	local r = ch and ch:FindFirstChild("HumanoidRootPart")
	local pm = S.panel
	if r and r:IsA("BasePart") and pm and pm.Parent and (r.Position - pm:GetPivot().Position).Magnitude > LEAVE then close() end
end)
