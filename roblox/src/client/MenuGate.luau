--!strict
-- MENU GATE (18 Nov 2026, the owner: "disable like all the other menus because I can open shop and stats during a
-- match"): the hub's menus open only out of a match and out of a pad's map room. one rule for all of them, read from
-- the player's Zone attribute (Matches sets it on the server: "match", "staging" for a map room, else the hub's own):
--   blocked there: the shop, the profile / stats / player cards, quests, the party panel, the Play screen, the hub's
--   loadout screen, the leaderboard, the customize (flair) screen
--   always allowed: settings, the emote wheel, the cursor toggle, REPORT, the match loadout picker in its window, READY
-- each menu's own open function asks MenuGate.allowed(name) first, before it touches MenuCursor or LoadoutOpen, so a
-- refused menu leaves nothing behind. MapRoomHud.client closes any that are open when you go in and hides the hub's
-- menu buttons there
local Players = game:GetService("Players")

local me = Players.LocalPlayer

local MenuGate = {}
MenuGate.BLOCKED = { match = true, staging = true } :: { [string]: boolean }
MenuGate.ALWAYS = { settings = true, emote = true, cursor = true, report = true, matchloadout = true, ready = true } :: { [string]: boolean }

function MenuGate.blocked(): boolean
	local z = me:GetAttribute("Zone")
	return type(z) == "string" and MenuGate.BLOCKED[z] == true
end

-- may the menu `name` open now?
function MenuGate.allowed(name: string): boolean
	if MenuGate.ALWAYS[name] then return true end
	return not MenuGate.blocked()
end

return MenuGate
