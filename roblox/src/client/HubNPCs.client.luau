--!strict
-- the hub's regulars, on your own screen: a dot after a regular's name while something waits for you there. HubNPCs
-- (server) tags the label's TextLabel "RegularBadge" with Base (its text) and BadgeFlag (one of your player
-- attributes: Dune's is QuestNews, which the quests server sets when today's quests or a finished one are new to you
-- and clears when you open the QUESTS screen). while that attribute is true for you, the label shows an amber dot
local Players = game:GetService("Players")
local CollectionService = game:GetService("CollectionService")

local me = Players.LocalPlayer
local DOT = '  <font color="#ffc24a">●</font>'

local function watch(t: Instance)
	if not t:IsA("TextLabel") then return end
	local flag, base = t:GetAttribute("BadgeFlag"), t:GetAttribute("Base")
	if type(flag) ~= "string" or type(base) ~= "string" then return end
	local function apply()
		if not t.Parent then return end
		t.Text = if me:GetAttribute(flag) == true then base .. DOT else base
	end
	apply()
	me:GetAttributeChangedSignal(flag):Connect(apply)
end
CollectionService:GetInstanceAddedSignal("RegularBadge"):Connect(watch)
for _, t in CollectionService:GetTagged("RegularBadge") do watch(t) end
