-- the way into the Play screen (PlayUI.luau has it): the PLAY button (the amber one over PROFILE, hub only) or M.
-- outside a party it asks the server for your private lobby (a fade, then you stand on your plinth); in a party it
-- opens the lobby's screen. the screen is up whenever you are in a party and not in a match: after a match, back in
-- the lobby, it comes back by itself. the server's pushes (party state, invites, MATCH FOUND, ranked results, notices)
-- arrive on JankfireRemotes.PlayPush.
local Players = game:GetService("Players")
local UIS = game:GetService("UserInputService")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local PlayUI = require(script.Parent:WaitForChild("PlayUI"))
local T = require(script.Parent:WaitForChild("Theme"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local PushR = Remotes:WaitForChild("PlayPush") :: RemoteEvent

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")

-- a short fade over the jump into (or out of) the lobby
local fadeGui = T.new("ScreenGui", { Name = "JankPlayFade", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 60, Enabled = true }, pg)
local fade = T.new("Frame", { BorderSizePixel = 0, BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, fadeGui)
local function dip()
	fade.BackgroundTransparency = 0
	task.delay(0.35, function() T.tween(fade, 0.4, { BackgroundTransparency = 1 }) end)
end

local busy = false
local function play()
	if busy or me:GetAttribute("Zone") == "match" then return end
	if PlayUI.S.party then
		if not PlayUI.isOpen() then PlayUI.open() end
		return
	end
	busy = true
	T.tween(fade, 0.18, { BackgroundTransparency = 0 })
	task.wait(0.18)
	local r = PlayUI.ask("play")
	if not r.ok then T.tween(fade, 0.25, { BackgroundTransparency = 1 }); busy = false; return end
	local st = PlayUI.ask("state")
	PlayUI.setState(st)
	busy = false
	task.wait(0.25) -- (the fresh body lands on its plinth)
	dip()
end

-- should the lobby screen be up? in a party, out of a match, alive in the hub zone
local function wantOpen(): boolean
	local pt = PlayUI.S.party
	return pt ~= nil and not pt.inMatch and me:GetAttribute("Zone") ~= "match" and pt.room ~= nil
end
local function sync()
	local want = wantOpen()
	if want and not PlayUI.isOpen() then
		PlayUI.open()
	elseif not want and PlayUI.isOpen() then
		PlayUI.close()
	end
end

PushR.OnClientEvent:Connect(function(msg: any)
	if type(msg) ~= "table" then return end
	if msg.t == "party" then
		local wasIn = PlayUI.S.party ~= nil
		PlayUI.onParty(msg.party)
		if wasIn and not msg.party then PlayUI.close(); dip() end
		sync()
	elseif msg.t == "invite" then PlayUI.onInvite(msg)
	elseif msg.t == "inviteGone" then PlayUI.onInviteGone(msg.id)
	elseif msg.t == "toast" and type(msg.text) == "string" then PlayUI.notice(msg.text)
	elseif msg.t == "found" then
		pcall(function() require(script.Parent:WaitForChild("Sfx")).play("round_start") end)
	elseif msg.t == "ranked" and type(msg.result) == "table" then
		PlayUI.showResult(msg.result)
		task.spawn(function()
			local st = PlayUI.ask("state")
			if st.ok then PlayUI.setRanked(st.ranked, st.best) end
		end)
	end
end)
me:GetAttributeChangedSignal("Zone"):Connect(function() task.defer(sync) end)

UIS.InputBegan:Connect(function(io, gp)
	if io.KeyCode ~= Enum.KeyCode.M or gp or UIS:GetFocusedTextBox() then return end
	if PlayUI.isOpen() then return end -- (in the lobby the screen stays: LEAVE LOBBY takes you out)
	if me:GetAttribute("LoadoutOpen") == true then return end
	task.spawn(play)
end)

-- the button: amber, the top of the hub's stack (PROFILE, SHOP, LOADOUT under it), with its key
local hud = T.new("ScreenGui", { Name = "JankPlayButton", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 6, ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, pg)
local face = T.new("TextButton", {
	Name = "Play", AutoButtonColor = false, BackgroundColor3 = T.ACCENT, BorderSizePixel = 0,
	Position = UDim2.new(0, 24, 1, -266), Size = UDim2.fromOffset(136, 42), FontFace = T.FONT_SHOUT, TextSize = 16, Text = "PLAY",
	TextColor3 = T.INK, TextXAlignment = Enum.TextXAlignment.Left,
}, T.scaled(hud))
T.corner(face)
T.new("UIPadding", { PaddingLeft = UDim.new(0, 42) }, face)
local key = T.key(face, "M", UDim2.fromOffset(-34, 10))
key.BackgroundColor3 = T.INK
face.MouseEnter:Connect(function() face.BackgroundColor3 = T.ACCENT:Lerp(Color3.new(1, 1, 1), 0.18) end)
face.MouseLeave:Connect(function() face.BackgroundColor3 = T.ACCENT end)
face.MouseButton1Click:Connect(function() task.spawn(play) end)
RunService.Heartbeat:Connect(function()
	local show = not PlayUI.isOpen() and me:GetAttribute("LoadoutOpen") ~= true and me:GetAttribute("Zone") ~= "match"
	if face.Visible ~= show then face.Visible = show end
end)

-- after a respawn (back from a match) the lobby screen comes back if it should
me.CharacterAdded:Connect(function() task.delay(0.4, sync) end)

-- the state as it stands when this client starts (a rejoin mid-party)
task.spawn(function()
	local st = PlayUI.ask("state")
	if st.ok then PlayUI.setState(st); sync() end
end)

-- a test hook (Play tests driven from Studio can't call into this script's modules): set the local player's attribute
-- PlayTest to "play", "open", "close", "tab:ranked", "tab:casual", "invite", "uninvite", "fake:844x390", "real", "state"
me:GetAttributeChangedSignal("PlayTest"):Connect(function()
	local v = me:GetAttribute("PlayTest")
	if type(v) ~= "string" or v == "" then return end
	me:SetAttribute("PlayTest", nil)
	local cmd, a = string.match(v, "^(%a+):?(.*)$")
	if cmd == "play" then task.spawn(play)
	elseif cmd == "open" then PlayUI.open()
	elseif cmd == "close" then PlayUI.close()
	elseif cmd == "tab" then PlayUI.tab(a)
	elseif cmd == "invite" then PlayUI.invitePanel(true)
	elseif cmd == "uninvite" then PlayUI.invitePanel(false)
	elseif cmd == "fake" then
		local w, h = string.match(a, "^(%d+)x(%d+)$")
		if w then PlayUI.fakeScreen(Vector2.new(tonumber(w) :: number, tonumber(h) :: number)) end
	elseif cmd == "real" then PlayUI.fakeScreen(nil)
	elseif cmd == "state" then task.spawn(function() local st = PlayUI.ask("state"); if st.ok then PlayUI.setState(st) end end)
	end
end)
