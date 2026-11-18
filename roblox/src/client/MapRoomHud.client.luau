--!strict
-- the hub's menus stay out of matches and out of a pad's map room (the zones MenuGate blocks: "match", and "staging",
-- server/MapRooms.luau). two jobs here:
--   the buttons: the hub's left-hand menu (QUESTS, PLAY and PARTY, PROFILE, SHOP, LOADOUT; 18 Nov 2026, the main
--   session after the owner's photos of the map room) goes. each is a ScreenGui of its own (QuestClient, PlayClient,
--   ProfileClient, ShopClient, LoadoutUI; on a phone TouchControls only moves the buttons inside them), so they're
--   switched off as wholes and back on when you leave, and their own scripts' per-frame Visible checks are left alone.
--   the vote cards, the timer, HP and the weapon panels are other GUIs and stay
--   the menus: going in closes any hub menu that's open (the owner, 18 Nov: "disable like all the other menus because I
--   can open shop and stats during a match"). each one's open function asks MenuGate first, so none opens there again
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local MenuGate = require(script.Parent:WaitForChild("MenuGate"))

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")

local NAMES = { "JankQuestsButton", "JankPlayButton", "JankProfileButton", "JankShopButton", "JankLoadoutButton" }
-- the hub menus' modules and how each closes (all of them do nothing when they're not open)
local MENUS = { ShopUI = "close", ProfileUI = "close", QuestUI = "close", PartyUI = "close", LeaderboardUI = "close", FlairUI = "close", PlayUI = "close", TradeUI = "close" }
local off: { [ScreenGui]: boolean } = {}

local function closeAll()
	for name, fn in MENUS do
		local m = script.Parent:FindFirstChild(name)
		if m and m:IsA("ModuleScript") then
			local ok, mod = pcall(require, m)
			if ok and type(mod) == "table" and type((mod :: any)[fn]) == "function" then pcall((mod :: any)[fn]) end
		end
	end
end
local was = false
local function zoneChanged()
	local blocked = MenuGate.blocked()
	if blocked and not was then closeAll() end
	was = blocked
end
-- out of a map room (on to the arena, or back to the hub): the camera is yours again, on your own body. a menu that held
-- it there (the loadout screen, on 18 Nov) could put back a camera on the room's old body in the sky. after the move
-- settles: the camera's subject is your Humanoid, and a Scriptable camera nothing drives goes back to Roblox's own (the
-- shoulder camera, a replay, a finisher or a menu still up keep theirs)
local function cameraHome()
	local cam = workspace.CurrentCamera
	local hum = me.Character and me.Character:FindFirstChildOfClass("Humanoid")
	if not cam or not hum or hum.Health <= 0 then return end
	if cam.CameraSubject ~= hum then cam.CameraSubject = hum end
	local held = me:GetAttribute("LoadoutOpen") == true or me:GetAttribute("Finishing") ~= nil or me:GetAttribute("ThirdPerson") == true
	if cam.CameraType == Enum.CameraType.Scriptable and not held then cam.CameraType = Enum.CameraType.Custom end
end
local lastZone = me:GetAttribute("Zone")
me:GetAttributeChangedSignal("Zone"):Connect(function()
	zoneChanged()
	local z = me:GetAttribute("Zone")
	if lastZone == "staging" and z ~= "staging" then
		for _, t in { 0.3, 1.2 } do task.delay(t, cameraHome) end -- (once the new body is in, and again after the spawn turn)
	end
	lastZone = z
end)
zoneChanged()

RunService.Heartbeat:Connect(function()
	local blocked = MenuGate.blocked()
	for _, n in NAMES do
		local g = pg:FindFirstChild(n)
		if g and g:IsA("ScreenGui") then
			if blocked then
				if g.Enabled then g.Enabled = false; off[g] = true end
			elseif off[g] then
				off[g] = nil
				g.Enabled = true
			end
		end
	end
end)
