--!strict
-- NO NAME TAGS OR HEALTH BARS OVER PLAYERS' HEADS (21 Nov 2026, the owner: "can you get rid of health bars and name tags
-- above players heads"). Everywhere: the hub, matches, training, zombies, parties and spectating.
-- * StarterPlayer's NameDisplayDistance / HealthDisplayDistance are 0 (also set in the place).
-- * Every player character's Humanoid is DisplayDistanceType None and HealthDisplayType AlwaysOff, set here on the server
--   the moment it appears (a respawn, a morph or an R6/R15 swap is a new character or a new Humanoid) and put back to
--   None if anything on the server changes it.
-- * The cosmetic card titles over heads (client/OverheadTitles) stay: they show the title's words only, never a name.
-- NPCs, regulars, training dummies and zombie bots keep whatever their own scripts give them.
local Players = game:GetService("Players")
local StarterPlayer = game:GetService("StarterPlayer")

StarterPlayer.NameDisplayDistance = 0
StarterPlayer.HealthDisplayDistance = 0

local NONE = Enum.HumanoidDisplayDistanceType.None
local OFF = Enum.HumanoidHealthDisplayType.AlwaysOff

local watched: { [Humanoid]: boolean } = {}

local function hide(h: Humanoid)
	if h.DisplayDistanceType ~= NONE then h.DisplayDistanceType = NONE end
	if h.HealthDisplayType ~= OFF then h.HealthDisplayType = OFF end
	if h.NameDisplayDistance ~= 0 then h.NameDisplayDistance = 0 end
	if h.HealthDisplayDistance ~= 0 then h.HealthDisplayDistance = 0 end
end

local function watch(h: Humanoid)
	hide(h)
	if watched[h] then return end
	watched[h] = true
	for _, prop in { "DisplayDistanceType", "HealthDisplayType", "NameDisplayDistance", "HealthDisplayDistance" } do
		h:GetPropertyChangedSignal(prop):Connect(function() hide(h) end)
	end
	h.AncestryChanged:Connect(function(_, parent)
		if parent == nil then watched[h] = nil end
	end)
end

local function onCharacter(ch: Model)
	for _, c in ch:GetChildren() do
		if c:IsA("Humanoid") then watch(c) end
	end
	ch.ChildAdded:Connect(function(c)
		if c:IsA("Humanoid") then watch(c) end
	end)
end

local function onPlayer(p: Player)
	if p.Character then task.spawn(onCharacter, p.Character) end
	p.CharacterAdded:Connect(onCharacter)
end

for _, p in Players:GetPlayers() do task.spawn(onPlayer, p) end
Players.PlayerAdded:Connect(onPlayer)
