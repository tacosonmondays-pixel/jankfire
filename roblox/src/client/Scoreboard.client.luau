--!strict
-- THE MATCH SCOREBOARD (21 Nov 2026, the owner: "when you press tab in match I want it to pull upa coreboard"): in a
-- match (every kind: duels, team modes, free-for-alls, the classic modes, ranked) the board shows while you hold it and
-- hides when you let go. The look is ScoreboardUI.luau's alone; the board comes from server/Scoreboard.luau (asked once
-- a second while it's open, so it keeps up with kills).
--   keyboard: hold Tab (Binds "scoreboard", rebindable in Settings > KEYBINDS)
--   controller: hold View (a tap still opens the menus: PadNav defers a match's View to its release and marks the hold
--               with the player attribute PadViewHold; the board comes after HOLD s)
--   phone: the SCORES pill on the top row (TouchControls) flips the player attribute ScoreboardTouch: tap to show, tap
--          again to hide
-- Roblox's own player list (also on Tab) is off while you're in a match, so Tab is only ours there; the hub keeps it.
-- (a ZOMBIES game and watching someone else's match have no board here: the server answers nil and nothing shows)
local Players = game:GetService("Players")
local UIS = game:GetService("UserInputService")
local StarterGui = game:GetService("StarterGui")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local me = Players.LocalPlayer
local UI = require(script.Parent:WaitForChild("ScoreboardUI")) :: any
local Binds = require(script.Parent:WaitForChild("Binds")) :: any
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Scoreboard") :: RemoteFunction

local HOLD = 0.3 -- s a pad's View is held before the board shows (a shorter press is the menus' tap)
local EVERY = 1 -- s between refreshes while it's open

local gui = Instance.new("ScreenGui")
gui.Name = "JankScoreboard"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = true
gui.DisplayOrder = 22
gui.Parent = me:WaitForChild("PlayerGui")
UI.mount(gui)

local function inMatch(): boolean
	return me:GetAttribute("Zone") == "match" and me:GetAttribute("ZmOn") == nil and me:GetAttribute("Watching") == nil
end

-- why it's open: any of these
local why = { key = false, pad = false, touch = false }
local open = false
local asking = false
local function refresh()
	if asking then return end
	asking = true
	local ok, board = pcall(function() return Remote:InvokeServer("board") end)
	asking = false
	if not open then return end
	if ok and type(board) == "table" then
		UI.render(board)
		UI.show(true)
	elseif ok and board == nil then -- (not in a match the server knows: nothing to show. false: asked too soon, keep it)
		UI.render(nil)
	end
end
local function update()
	local want = (why.key or why.pad or why.touch) and inMatch()
	if want == open then return end
	open = want
	if open then task.spawn(refresh) else UI.show(false) end
end

-- keyboard
UIS.InputBegan:Connect(function(io: InputObject)
	if UIS:GetFocusedTextBox() then return end
	if io.UserInputType == Enum.UserInputType.Keyboard and Binds.is("scoreboard", io) then why.key = true; update() end
end)
UIS.InputEnded:Connect(function(io: InputObject)
	if io.UserInputType == Enum.UserInputType.Keyboard and Binds.is("scoreboard", io) then why.key = false; update() end
end)
UIS.WindowFocusReleased:Connect(function() why.key = false; update() end) -- (alt-tabbed away with Tab held: no release comes)

-- controller: PadNav marks a held View in a match
me:GetAttributeChangedSignal("PadViewHold"):Connect(function()
	local v = me:GetAttribute("PadViewHold")
	if v == nil then why.pad = false; update(); return end
	task.delay(HOLD, function()
		if me:GetAttribute("PadViewHold") == v then why.pad = true; update() end
	end)
end)

-- phone: the SCORES pill
me:GetAttributeChangedSignal("ScoreboardTouch"):Connect(function()
	why.touch = me:GetAttribute("ScoreboardTouch") == true
	update()
end)

-- Roblox's player list: off in a match, back on outside one
local listOn: boolean? = nil
local function playerList()
	local want = not inMatch()
	if want == listOn then return end
	for _ = 1, 10 do
		if pcall(function() StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.PlayerList, want) end) then listOn = want; return end
		task.wait(0.5)
	end
end
local function zoneChanged()
	if not inMatch() then
		why.key, why.pad = false, false
		if me:GetAttribute("ScoreboardTouch") == true then me:SetAttribute("ScoreboardTouch", nil) end
		why.touch = false
	end
	update()
	task.spawn(playerList)
end
for _, a in { "Zone", "ZmOn", "Watching" } do me:GetAttributeChangedSignal(a):Connect(zoneChanged) end
task.spawn(playerList)

-- keep it current while it's open
task.spawn(function()
	while true do
		task.wait(EVERY)
		if open then refresh() end
	end
end)
