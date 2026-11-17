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
local PartyUI = require(script.Parent:WaitForChild("PartyUI"))
local LeaderboardUI = require(script.Parent:WaitForChild("LeaderboardUI"))
local QuickJoinUI = require(script.Parent:WaitForChild("QuickJoinUI"))
local QuickVoteUI = require(script.Parent:WaitForChild("QuickVoteUI"))
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
	local pt = PlayUI.S.party
	if pt and pt.room then
		if not PlayUI.isOpen() then PlayUI.open() end
		return
	end
	if PartyUI.isOpen() then PartyUI.close() end
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
		local hadRoom = PlayUI.S.party ~= nil and PlayUI.S.party.room ~= nil
		PlayUI.onParty(msg.party)
		if hadRoom and not (msg.party and msg.party.room) and not (msg.party and msg.party.inMatch) then PlayUI.close(); dip() end
		sync()
		PartyUI.changed()
		QuickVoteUI.sync(msg.party and msg.party.found) -- (a QUICKPLAY match's vote on its mode)
	elseif msg.t == "openBoard" then LeaderboardUI.open(msg.tab) -- (Party.openBoard: the hub's RANKED regular)
	elseif msg.t == "invite" then PlayUI.onInvite(msg)
	elseif msg.t == "inviteGone" then PlayUI.onInviteGone(msg.id)
	elseif msg.t == "quick" then QuickJoinUI.show(msg) -- (QUICK JOIN: someone stepped on a hub pad, server/QuickJoin.luau)
	elseif msg.t == "quickGone" then QuickJoinUI.gone(msg.id)
	elseif msg.t == "toast" and type(msg.text) == "string" then
		PlayUI.notice(msg.text)
		if msg.refresh then -- (a ranked restore: the menu's ranks change too)
			task.spawn(function()
				local st = PlayUI.ask("state")
				if st.ok then PlayUI.setState(st) end
			end)
		end
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
	local Binds = require(script.Parent:WaitForChild("Binds")) -- (J and M, or the player's own keys: Settings > KEYBINDS)
	if Binds.is("party", io) and not gp and not UIS:GetFocusedTextBox() and me:GetAttribute("Zone") ~= "match" then
		if PartyUI.isOpen() or me:GetAttribute("LoadoutOpen") ~= true or PlayUI.isOpen() then PartyUI.toggle() end
		return
	end
	if not Binds.is("play", io) or gp or UIS:GetFocusedTextBox() then return end
	if PlayUI.isOpen() then return end -- (in the lobby the screen stays: LEAVE LOBBY takes you out)
	if me:GetAttribute("LoadoutOpen") == true then return end
	task.spawn(play)
end)

-- the button: amber, the top of the hub's stack (PROFILE, SHOP, LOADOUT under it), with its key
local hud = T.new("ScreenGui", { Name = "JankPlayButton", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 6, ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, pg)
local face = T.new("TextButton", {
	Name = "Play", AutoButtonColor = false, BackgroundColor3 = T.ACCENT, BorderSizePixel = 0,
	Position = UDim2.new(0, 24, 1, -312), Size = UDim2.fromOffset(136, 42), FontFace = T.FONT_SHOUT, TextSize = 16, Text = "PLAY",
	TextColor3 = T.INK, TextXAlignment = Enum.TextXAlignment.Left,
}, T.scaled(hud))
T.corner(face)
T.new("UIPadding", { PaddingLeft = UDim.new(0, 42) }, face)
local key = T.key(face, "M", UDim2.fromOffset(-34, 10))
key.BackgroundColor3 = T.INK
face.MouseEnter:Connect(function() face.BackgroundColor3 = T.ACCENT:Lerp(Color3.new(1, 1, 1), 0.18) end)
face.MouseLeave:Connect(function() face.BackgroundColor3 = T.ACCENT end)
face.MouseButton1Click:Connect(function() task.spawn(play) end)
-- PARTY, under it: everyone in the server, invites, cards (PartyUI). it counts your party when you have one
local partyB = T.new("TextButton", {
	Name = "Party", AutoButtonColor = false, BackgroundColor3 = T.BG, BackgroundTransparency = T.BG_A, BorderSizePixel = 0,
	Position = UDim2.new(0, 24, 1, -262), Size = UDim2.fromOffset(136, 36), FontFace = T.FONT_BOLD, TextSize = 13, Text = "PARTY",
	TextColor3 = T.TEXT, TextXAlignment = Enum.TextXAlignment.Left, RichText = true,
}, face.Parent)
T.corner(partyB); T.edge(partyB)
T.new("UIPadding", { PaddingLeft = UDim.new(0, 42) }, partyB)
T.key(partyB, "J", UDim2.fromOffset(-34, 7))
partyB.MouseEnter:Connect(function() partyB.BackgroundTransparency = 0.1 end)
partyB.MouseLeave:Connect(function() partyB.BackgroundTransparency = T.BG_A end)
partyB.MouseButton1Click:Connect(function() PartyUI.toggle() end)
PlayUI.openParty = function() PartyUI.open() end
(PlayUI :: any).openBoard = function() LeaderboardUI.open() end
-- any ProximityPrompt with the attribute RankedBoard = "duels" | "party" (or RankedOpen = true, the hub's name for it)
-- opens the leaderboard on that tab (the hub's RANKED regular, Frisk1636)
game:GetService("ProximityPromptService").PromptTriggered:Connect(function(prompt, who)
	if who ~= me then return end
	local v = prompt:GetAttribute("RankedBoard")
	if v == nil or v == false then v = prompt:GetAttribute("RankedOpen") end
	if v == nil or v == false then return end
	LeaderboardUI.open(if v == "party" then "party" else "duels")
end)
RunService.Heartbeat:Connect(function()
	local show = not PlayUI.isOpen() and me:GetAttribute("LoadoutOpen") ~= true and me:GetAttribute("Zone") ~= "match"
	if face.Visible ~= show then face.Visible = show end
	if partyB.Visible ~= show then partyB.Visible = show end
	local pt = PlayUI.S.party
	local label = if pt then ('PARTY  <font color="%s">%d/%d</font>'):format(T.hex(T.MUTED), #pt.members, pt.max or 4) else "PARTY"
	if partyB.Text ~= label then partyB.Text = label end
end)

-- after a respawn (back from a match) the lobby screen comes back if it should
me.CharacterAdded:Connect(function() task.delay(0.4, sync) end)

-- the state as it stands when this client starts (a rejoin mid-party)
task.spawn(function()
	local st = PlayUI.ask("state")
	if st.ok then PlayUI.setState(st); sync() end
end)

-- a test hook (Play tests driven from Studio can't call into this script's modules): set the local player's attribute
-- PlayTest to "play", "open", "close", "tab:duels", "tab:modes", "invite", "uninvite", "fake:844x390", "real", "state",
-- "party", "unparty", "partyfake:844x390" (the PARTY panel), "badges" / "nobadges" (both ladders on one sheet),
-- "samplemodes" (Studio: three sample classic modes on the MODES tab; JankPlayTest "samplemodes" for the server),
-- "board" / "board:party" / "noboard" / "boardfake:844x390" (the ranked leaderboard)
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
	elseif cmd == "badges" then PlayUI.badgeSheet(true)
	elseif cmd == "nobadges" then PlayUI.badgeSheet(false)
	elseif cmd == "samplemodes" then PlayUI.sampleModes()
	elseif cmd == "board" then LeaderboardUI.open(if a ~= "" then a else nil)
	elseif cmd == "noboard" then LeaderboardUI.close()
	elseif cmd == "boardfake" then
		local w, h = string.match(a, "^(%d+)x(%d+)$")
		LeaderboardUI.fakeScreen(if w then Vector2.new(tonumber(w) :: number, tonumber(h) :: number) else nil)
	elseif cmd == "party" then PartyUI.open()
	elseif cmd == "unparty" then PartyUI.close()
	elseif cmd == "partyfake" then
		local w, h = string.match(a, "^(%d+)x(%d+)$")
		if w then PartyUI.fakeScreen(Vector2.new(tonumber(w) :: number, tonumber(h) :: number)) end
	elseif cmd == "state" then task.spawn(function() local st = PlayUI.ask("state"); if st.ok then PlayUI.setState(st) end end)
	end
end)
