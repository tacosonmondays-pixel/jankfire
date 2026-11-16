-- the ways into the player cards (ProfileUI.luau has the screen): K or the PROFILE button (over SHOP, hub only) for
-- your own (its PLAYERS tab lists everyone in the server), and in the hub a click on someone (the crosshair or the
-- mouse arrow on them; a tap on a phone) opens theirs. a small "VIEW PROFILE" line under the crosshair says when a
-- click would. (Tab is left to Roblox's own player list)
local Players = game:GetService("Players")
local UIS = game:GetService("UserInputService")
local RunService = game:GetService("RunService")

local ProfileUI = require(script.Parent:WaitForChild("ProfileUI"))
local T = require(script.Parent:WaitForChild("Theme"))

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")
local RANGE = 90 -- studs: how far away a click still finds someone

local function menuUp(): boolean
	return me:GetAttribute("LoadoutOpen") == true or me:GetAttribute("ShopOpen") == true or me:GetAttribute("SettingsOpen") == true
end
local function inHub(): boolean return me:GetAttribute("Zone") == "hub" end

-- who is under this screen point (viewport pixels for a mouse, GUI pixels for a touch), if anyone: their user id and
-- display name. (Studio play tests only: a model with the attribute ProfileStandIn = a user id stands in for a player,
-- so the click can be tested alone)
local function playerAt(pos: Vector2, gui: boolean): (number?, string?)
	local cam = workspace.CurrentCamera
	if not cam then return nil end
	local ray = if gui then cam:ScreenPointToRay(pos.X, pos.Y) else cam:ViewportPointToRay(pos.X, pos.Y)
	local rp = RaycastParams.new()
	rp.FilterType = Enum.RaycastFilterType.Exclude
	rp.FilterDescendantsInstances = { me.Character :: any }
	local hit = workspace:Raycast(ray.Origin, ray.Direction * RANGE, rp)
	if not hit then return nil end
	for _, o in Players:GetPlayers() do
		if o ~= me and o.Character and hit.Instance:IsDescendantOf(o.Character) then return o.UserId, o.DisplayName end
	end
	if RunService:IsStudio() then
		local m = hit.Instance:FindFirstAncestorWhichIsA("Model")
		while m do
			local id = m:GetAttribute("ProfileStandIn")
			if type(id) == "number" then return id, "STAND-IN" end
			m = m.Parent and m.Parent:FindFirstAncestorWhichIsA("Model")
		end
	end
	return nil
end
local function aimPoint(): Vector2
	if UIS.MouseBehavior == Enum.MouseBehavior.LockCenter then
		local cam = workspace.CurrentCamera
		return if cam then cam.ViewportSize / 2 else Vector2.zero
	end
	return UIS:GetMouseLocation()
end

UIS.InputBegan:Connect(function(io, gp)
	if UIS:GetFocusedTextBox() then return end
	if io.KeyCode == Enum.KeyCode.K then
		if gp and not ProfileUI.isOpen() then return end
		if menuUp() and not ProfileUI.isOpen() then return end
		ProfileUI.toggle()
	elseif io.UserInputType == Enum.UserInputType.MouseButton1 and not gp then
		if ProfileUI.isOpen() or menuUp() or not inHub() then return end
		local id = playerAt(aimPoint(), false)
		if id then ProfileUI.open(id, "profile") end
	end
end)
UIS.TouchTap:Connect(function(points, gp)
	if gp or ProfileUI.isOpen() or menuUp() or not inHub() then return end
	local p = points[1]
	if not p then return end
	local id = playerAt(Vector2.new(p.X, p.Y), true)
	if id then ProfileUI.open(id, "profile") end
end)

-- the button: a plate like SHOP's, just over it, with its key
local hud = T.new("ScreenGui", { Name = "JankProfileButton", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 6, ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, pg)
local scaled = T.scaled(hud)
local face = T.new("TextButton", {
	Name = "Profile", AutoButtonColor = false, BackgroundColor3 = T.BG, BackgroundTransparency = T.BG_A, BorderSizePixel = 0,
	Position = UDim2.new(0, 24, 1, -216), Size = UDim2.fromOffset(136, 36), FontFace = T.FONT_BOLD, TextSize = 13, Text = "PROFILE",
	TextColor3 = T.TEXT, TextXAlignment = Enum.TextXAlignment.Left,
}, scaled)
T.corner(face); T.edge(face)
T.new("UIPadding", { PaddingLeft = UDim.new(0, 42) }, face)
T.key(face, "K", UDim2.fromOffset(-34, 7))
face.MouseEnter:Connect(function() face.BackgroundTransparency = 0.1 end)
face.MouseLeave:Connect(function() face.BackgroundTransparency = T.BG_A end)
face.MouseButton1Click:Connect(function() ProfileUI.open() end)

-- "VIEW PROFILE · NAME" under the crosshair while it is on someone in the hub (not on a touch screen: a tap just works)
local hint = T.plate(scaled, "ProfileHint", UDim2.new(0.5, 0, 0.5, 34), UDim2.fromOffset(200, 28))
hint.AnchorPoint = Vector2.new(0.5, 0)
hint.Visible = false
local hk = T.key(hint, "", UDim2.fromOffset(4, 3))
hk.Size = UDim2.fromOffset(22, 22)
-- (a drawn mouse button in the key cap: no glyphs)
local mb = T.new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(9, 13), BackgroundTransparency = 1 }, hk)
T.corner(mb, 4); T.edge(mb, T.TEXT, 0.2, 1.5)
T.new("Frame", { Position = UDim2.fromOffset(0, 0), Size = UDim2.fromOffset(5, 6), BackgroundColor3 = T.TEXT, BorderSizePixel = 0 }, mb)
local hintText = T.text(hint, "Text", "", 12, T.TEXT, T.FONT_BOLD)
hintText.Position = UDim2.fromOffset(32, 0)
hintText.Size = UDim2.new(1, -38, 1, 0)
hintText.TextTruncate = Enum.TextTruncate.AtEnd
local acc = 0
RunService.Heartbeat:Connect(function(dt)
	local show = not ProfileUI.isOpen() and not menuUp() and me:GetAttribute("Zone") ~= "match"
	if face.Visible ~= show then face.Visible = show end
	acc += dt
	if acc < 0.12 then return end
	acc = 0
	local who: string? = nil
	if show and inHub() and UIS.MouseEnabled then
		local _, name = playerAt(aimPoint(), false)
		who = name
	end
	if who then
		hintText.Text = "VIEW PROFILE  ·  " .. string.upper(who)
		hint.Size = UDim2.fromOffset(math.clamp(hintText.TextBounds.X + 46, 150, 320), 28)
		if UIS.MouseBehavior ~= Enum.MouseBehavior.LockCenter then
			local m = UIS:GetMouseLocation()
			local s = T.scaleNow()
			hint.Position = UDim2.fromOffset(m.X / s, m.Y / s + 22)
		else
			hint.Position = UDim2.new(0.5, 0, 0.5, 34)
		end
	end
	hint.Visible = who ~= nil
end)

-- a test hook (Play tests driven from Studio can't call into this script's modules): set the local player's attribute
-- ProfileTest to "open", "open:<userId>", "tab:<profile|customize|players>", "close", "fake:844x390" (lay out for a
-- phone-sized screen), "real", "scroll:<y>"
me:GetAttributeChangedSignal("ProfileTest"):Connect(function()
	local v = me:GetAttribute("ProfileTest")
	if type(v) ~= "string" or v == "" then return end
	me:SetAttribute("ProfileTest", nil)
	local cmd, a = string.match(v, "^(%a+):?(.*)$")
	if cmd == "open" then ProfileUI.open(tonumber(a), nil)
	elseif cmd == "tab" then if ProfileUI.isOpen() then ProfileUI.tab(a) else ProfileUI.open(nil, a) end
	elseif cmd == "close" then ProfileUI.close()
	elseif cmd == "fake" then
		local w, h = string.match(a, "^(%d+)x(%d+)$")
		if w then ProfileUI.fakeScreen(Vector2.new(tonumber(w) :: number, tonumber(h) :: number)) end
	elseif cmd == "real" then ProfileUI.fakeScreen(nil)
	elseif cmd == "scroll" then ProfileUI.scrollTo(tonumber(a) or 0)
	end
end)
