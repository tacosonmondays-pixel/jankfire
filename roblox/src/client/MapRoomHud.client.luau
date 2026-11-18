--!strict
-- in a pad's map room (the "staging" zone: server/MapRooms.luau, Matches) the hub's left-hand menu goes, as it does in
-- a match (18 Nov 2026, the main session after the owner's photos): QUESTS, PLAY and PARTY, PROFILE, SHOP, LOADOUT.
-- each is a ScreenGui of its own (QuestClient, PlayClient, ProfileClient, ShopClient, LoadoutUI; on a phone
-- TouchControls only moves the buttons inside them), so they're switched off here as wholes and back on when you leave,
-- and their own scripts' per-frame Visible checks are left alone. the vote cards, the timer, HP and the weapon panels
-- are other GUIs and stay
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")

local NAMES = { "JankQuestsButton", "JankPlayButton", "JankProfileButton", "JankShopButton", "JankLoadoutButton" }
local off: { [ScreenGui]: boolean } = {}

RunService.Heartbeat:Connect(function()
	local staging = me:GetAttribute("Zone") == "staging"
	for _, n in NAMES do
		local g = pg:FindFirstChild(n)
		if g and g:IsA("ScreenGui") then
			if staging then
				if g.Enabled then g.Enabled = false; off[g] = true end
			elseif off[g] then
				off[g] = nil
				g.Enabled = true
			end
		end
	end
end)
