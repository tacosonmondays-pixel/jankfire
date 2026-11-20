--!strict
-- the hub's menu stack on the left, top to bottom: PLAY, QUESTS, PARTY, PROFILE, SHOP, LOADOUT (owner, 18 Nov: "M play
-- should be at the top of the menus on the left in the main hub"). each button's own script asks here for its spot, so
-- the order lives in one place. design pixels in the HUD's scaled frame, from the bottom left; the stack ends just over
-- the health plate (FightHud, y -88). a phone (TouchControls: the same stack on the right) and a controller (PadNav: top
-- to bottom by position) follow these positions, so they need nothing of their own
local HubStack = {}

HubStack.ORDER = { "Play", "Quests", "Party", "Hubs", "Profile", "Shop", "Loadout" } -- (Hubs: travel between the hubs, HubTravelUI, 20 Nov)
HubStack.HEIGHT = { Play = 42 } :: { [string]: number } -- (the rest 36)
local X, BOTTOM, GAP, H = 24, -96, 8, 36

function HubStack.pos(id: string): UDim2
	local y = BOTTOM
	for i = #HubStack.ORDER, 1, -1 do
		local n = HubStack.ORDER[i]
		y -= HubStack.HEIGHT[n] or H
		if n == id then return UDim2.new(0, X, 1, y) end
		y -= GAP
	end
	return UDim2.new(0, X, 1, y)
end

return HubStack
