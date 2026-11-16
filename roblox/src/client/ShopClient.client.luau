-- the ways into the shop (ShopUI.luau has the screen): the B key, the SHOP button over the LOADOUT button (hub only,
-- like it), and any ProximityPrompt carrying the attribute ShopOpen: "<offer id>" opens it on that offer (the hub's
-- bundle holograms: "bundle_nightshift"), "tab:<tab>" on a tab ("tab:containers")
local Players = game:GetService("Players")
local UIS = game:GetService("UserInputService")
local RunService = game:GetService("RunService")
local ProximityPromptService = game:GetService("ProximityPromptService")

local ShopUI = require(script.Parent:WaitForChild("ShopUI"))
local T = require(script.Parent:WaitForChild("Theme"))

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")

UIS.InputBegan:Connect(function(io, gp)
	if io.KeyCode ~= Enum.KeyCode.B or UIS:GetFocusedTextBox() then return end
	if gp and not ShopUI.isOpen() then return end
	ShopUI.toggle()
end)

ProximityPromptService.PromptTriggered:Connect(function(prompt, who)
	if who ~= me then return end
	local v = prompt:GetAttribute("ShopOpen")
	if type(v) ~= "string" or v == "" then return end
	local tab = string.match(v, "^tab:(%a+)$")
	if tab then ShopUI.open(tab) else ShopUI.open(nil, v) end
end)

-- a test hook (Play tests driven from Studio, which can't call into this script's modules): set the local player's
-- attribute ShopTest to "open", "open:<tab>", "open::<offer id>", "close", "fake:844x390" (a phone-sized box) or "real"
me:GetAttributeChangedSignal("ShopTest"):Connect(function()
	local v = me:GetAttribute("ShopTest")
	if type(v) ~= "string" or v == "" then return end
	me:SetAttribute("ShopTest", nil)
	-- (an offer id can hold a colon itself: "wrap:galaxy@smg", so only the command is split off)
	local cmd, rest = string.match(v, "^(%a+):?(.*)$")
	if cmd == "open" then
		local tab, id = string.match(rest or "", "^([^:]*):?(.*)$")
		ShopUI.open(if tab and tab ~= "" then tab else nil, if id and id ~= "" then id else nil)
	elseif cmd == "close" then ShopUI.close()
	elseif cmd == "fake" then
		local w, h = string.match(rest or "", "^(%d+)x(%d+)$")
		if w then ShopUI.fakeScreen(Vector2.new(tonumber(w) :: number, tonumber(h) :: number)) end
	elseif cmd == "real" then ShopUI.fakeScreen(nil)
	elseif cmd == "inspect" then ShopUI.inspect(rest)
	elseif cmd == "odds" then ShopUI.odds(rest)
	elseif cmd == "ask" then ShopUI.ask(rest)
	elseif cmd == "count" then -- "count:spray:5": the x1 / x5 / x10 pick for a container
		local cid, nn = string.match(rest or "", "^([%w_]+):(%d+)$")
		if cid then ShopUI.S.count[cid] = tonumber(nn); if ShopUI.isOpen() then ShopUI.refill() end end
	elseif cmd == "commit" then ShopUI.commit()
	elseif cmd == "back" then ShopUI.uninspect()
	end
end)

-- the button: a plate like the HUD's, just over the LOADOUT button, with its key
local hud = T.new("ScreenGui", { Name = "JankShopButton", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 6, ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, pg)
local face = T.new("TextButton", {
	Name = "Shop", AutoButtonColor = false, BackgroundColor3 = T.BG, BackgroundTransparency = T.BG_A, BorderSizePixel = 0,
	Position = UDim2.new(0, 24, 1, -174), Size = UDim2.fromOffset(136, 36), FontFace = T.FONT_BOLD, TextSize = 13, Text = "SHOP",
	TextColor3 = T.TEXT, TextXAlignment = Enum.TextXAlignment.Left,
}, T.scaled(hud))
T.corner(face); T.edge(face)
T.new("UIPadding", { PaddingLeft = UDim.new(0, 42) }, face)
T.key(face, "B", UDim2.fromOffset(-34, 7))
face.MouseEnter:Connect(function() face.BackgroundTransparency = 0.1 end)
face.MouseLeave:Connect(function() face.BackgroundTransparency = T.BG_A end)
face.MouseButton1Click:Connect(function() ShopUI.open() end)
RunService.Heartbeat:Connect(function()
	local show = not ShopUI.isOpen() and not me:GetAttribute("LoadoutOpen") and me:GetAttribute("Zone") ~= "match"
	if face.Visible ~= show then face.Visible = show end
end)
