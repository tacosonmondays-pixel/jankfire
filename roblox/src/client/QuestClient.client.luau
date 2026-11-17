-- the ways into the QUESTS screen (QuestUI.luau has it): the U key, any ProximityPrompt with the attribute QuestsOpen (the
-- hub's Dune), and the QUESTS button over PLAY (hub only, like the
-- other buttons in that column), the wallet in the top-right corner (Brass and Crate Tickets, from the player
-- attributes Quests.luau keeps), and the toasts the server pushes when a quest finishes or a weekly step pays.
-- a test hook (Play tests driven from Studio, which can't call into this script's modules): set the local player's
-- attribute QuestTest to "open", "close", "toast" (a made-up quest toast), "step" (a made-up weekly toast),
-- "reroll:<slot>", "fake:844x390" (a phone-sized box), "real" or "scroll:<y>"
local Players = game:GetService("Players")
local UIS = game:GetService("UserInputService")
local RunService = game:GetService("RunService")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local QuestUI = require(script.Parent:WaitForChild("QuestUI"))
local T = require(script.Parent:WaitForChild("Theme"))

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")

UIS.InputBegan:Connect(function(io, gp)
	if io.KeyCode ~= Enum.KeyCode.U or UIS:GetFocusedTextBox() then return end
	if gp and not QuestUI.isOpen() then return end
	-- (another menu up: the loadout, the shop, a card. only one at a time)
	if not QuestUI.isOpen() and me:GetAttribute("LoadoutOpen") then return end
	QuestUI.toggle()
end)

-- any ProximityPrompt carrying the attribute QuestsOpen (or QuestOpen) = true opens the panel: the hub's Dune ("Dune is
-- the quests guy")
ProximityPromptService.PromptTriggered:Connect(function(prompt, who)
	if who ~= me or (prompt:GetAttribute("QuestsOpen") ~= true and prompt:GetAttribute("QuestOpen") ~= true) then return end
	QuestUI.open()
end)

-- the server's pushes
task.spawn(function()
	local push = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("QuestPush", 60) :: RemoteEvent?
	if not push then return end
	push.OnClientEvent:Connect(function(msg: any)
		if type(msg) ~= "table" then return end
		if msg.t == "state" then QuestUI.setState(msg.state)
		else QuestUI.toast(msg) end
	end)
end)

me:GetAttributeChangedSignal("QuestTest"):Connect(function()
	local v = me:GetAttribute("QuestTest")
	if type(v) ~= "string" or v == "" then return end
	me:SetAttribute("QuestTest", nil)
	local cmd, rest = string.match(v, "^(%a+):?(.*)$")
	if cmd == "open" then QuestUI.open()
	elseif cmd == "close" then QuestUI.close()
	elseif cmd == "toast" then QuestUI.toast({ t = "done", text = "Get 10 kills", brass = 30, pts = 1 })
	elseif cmd == "step" then QuestUI.toast({ t = "step", tix = 1 })
	elseif cmd == "reroll" then QuestUI.reroll(tonumber(rest) or 1)
	elseif cmd == "scroll" then QuestUI.scrollTo(tonumber(rest) or 0)
	elseif cmd == "fake" then
		local w, h = string.match(rest or "", "^(%d+)x(%d+)$")
		if w then QuestUI.fakeScreen(Vector2.new(tonumber(w) :: number, tonumber(h) :: number)) end
	elseif cmd == "real" then QuestUI.fakeScreen(nil)
	end
end)

-- ------------------------------------------------------------------ the button, over PLAY
local hud = T.new("ScreenGui", { Name = "JankQuestsButton", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 6, ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, pg)
local root = T.scaled(hud)
local face = T.new("TextButton", {
	Name = "Quests", AutoButtonColor = false, BackgroundColor3 = T.BG, BackgroundTransparency = T.BG_A, BorderSizePixel = 0,
	Position = UDim2.new(0, 24, 1, -358), Size = UDim2.fromOffset(136, 36), FontFace = T.FONT_BOLD, TextSize = 13, Text = "QUESTS",
	TextColor3 = T.TEXT, TextXAlignment = Enum.TextXAlignment.Left,
}, root)
T.corner(face); T.edge(face)
T.new("UIPadding", { PaddingLeft = UDim.new(0, 42) }, face)
T.key(face, "U", UDim2.fromOffset(-34, 7))
-- something new (QuestNews): a small amber dot on the button's top right corner
local dot = T.new("Frame", { Name = "News", BorderSizePixel = 0, BackgroundColor3 = T.ACCENT, AnchorPoint = Vector2.new(0.5, 0.5),
	Position = UDim2.new(1, -2, 0, 2), Size = UDim2.fromOffset(8, 8), Visible = false }, face)
T.corner(dot, 99)
-- today's quests done, 0/3..3/3
local count = T.text(face, "Done", "0/3", 12, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Right)
count.Position = UDim2.fromOffset(0, 0)
count.Size = UDim2.new(1, -12, 1, 0)
face.MouseEnter:Connect(function() face.BackgroundTransparency = 0.1 end)
face.MouseLeave:Connect(function() face.BackgroundTransparency = T.BG_A end)
face.MouseButton1Click:Connect(function() QuestUI.open() end)

-- ------------------------------------------------------------------ the wallet, top right
-- (its own ScreenGui: on a phone TouchControls moves JankQuestsButton.Scaled's one child, the button, into its right-
-- hand stack. the wallet sits at y 58 on every screen: under the touch row of EMOTE / SETTINGS pills on a phone (agreed
-- 17 Nov) and under the settings pill on a computer)
local walletGui = T.new("ScreenGui", { Name = "JankQuestsWallet", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 6, ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, pg)
local wallet = T.plate(T.scaled(walletGui), "Wallet", UDim2.new(1, -24, 0, 58), UDim2.fromOffset(0, 32))
wallet.AnchorPoint = Vector2.new(1, 0)
wallet.AutomaticSize = Enum.AutomaticSize.X
T.new("UIPadding", { PaddingLeft = UDim.new(0, 12), PaddingRight = UDim.new(0, 12) }, wallet)
local line = QuestUI.row(wallet, 0, 4, 24, { { icon = "brass", s = 16 }, { text = "0", size = 14, font = T.FONT_HEAVY }, { gap = 10 },
	{ icon = "tix", s = 16 }, { text = "0", size = 14, font = T.FONT_HEAVY } })
line.Position = UDim2.fromOffset(0, 4)
local function texts(): { TextLabel }
	local out = {}
	for _, c in line:GetChildren() do if c:IsA("TextLabel") then table.insert(out, c) end end
	table.sort(out, function(a, b) return a.LayoutOrder < b.LayoutOrder end)
	return out
end
local function refresh()
	local t = texts()
	if t[1] then t[1].Text = QuestUI.comma(tonumber(me:GetAttribute("Brass")) or 0) end
	if t[2] then t[2].Text = QuestUI.comma(tonumber(me:GetAttribute("CrateTickets")) or 0) end
	count.Text = ("%d/3"):format(tonumber(me:GetAttribute("QuestsDone")) or 0)
	count.TextColor3 = if (tonumber(me:GetAttribute("QuestsDone")) or 0) >= 3 then T.ACCENT else T.MUTED
	dot.Visible = me:GetAttribute("QuestNews") == true
end
for _, a in { "Brass", "CrateTickets", "QuestsDone", "QuestNews" } do me:GetAttributeChangedSignal(a):Connect(refresh) end
refresh()

RunService.Heartbeat:Connect(function()
	local ready = me:GetAttribute("QuestSave") ~= nil and me:GetAttribute("QuestSave") ~= "loading"
	local show = ready and not QuestUI.isOpen() and not me:GetAttribute("LoadoutOpen") and me:GetAttribute("Zone") ~= "match"
	if face.Visible ~= show then face.Visible = show end
	if wallet.Visible ~= show then wallet.Visible = show end
end)
