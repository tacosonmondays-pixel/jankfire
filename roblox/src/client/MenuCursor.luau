--!strict
-- one shared "a menu needs the cursor" state (the owner, 17 Nov: "sometimes your mouse cursor disappears when you open
-- crates and stuff"). every screen that wants the mouse puts its name in while it's up and takes it out when it goes:
--   MenuCursor.set("shop", true, function() return S.open end)   ...   MenuCursor.set("shop", false)
-- (the shop and its inventory, a crate/bag/spray-can reveal, the loadout, settings, quests, the player card, the Play
-- panel, the party panel, the leaderboard, the emote wheel and the equip screen, a report, the anti-cheat panel).
-- while any name is in:
--   the mouse is free (MouseBehavior Default) and the arrow shows (MouseIconEnabled), written every frame after the
--   cameras, so first person, the shoulder camera and the emote camera can't lock it again;
--   the player attribute MenuCursor is true (what ShoulderCam, FlairClient, Arsenal and JankSettings read: the camera
--   holds its look, clicks don't fire or aim);
--   LoadoutOpen (the one "hold still" flag: hands, weapons, movement) stays up while a menu is in. a screen closing
--   over another one clears it on its way out (they each save and restore it): it goes straight back up. and the
--   other way: left up with nothing holding it (M.holding: no menu, finisher, crate reveal or play of the match) it
--   goes down by itself half a second later.
-- a name put in "cursor only" (the fourth argument: Toggle Cursor, CursorToggle.client) frees the mouse the same way
-- but isn't a menu: it doesn't keep LoadoutOpen up, so you still move. MenuCursor.menu() says whether a real menu is in.
-- when the last name goes the game's own rule is back: first person and the shoulder camera lock the mouse again on
-- their next frame and JankSettings hides the arrow under the crosshair.
-- the alive function (optional) says whether that screen is really still up: a screen that went away by a path that
-- forgot to take its name out is let go on the next frame, so the mouse can't be left free in the game.
-- (a name put in twice is still one; taking out a name that isn't in does nothing. MenuCursor.list() says who's in;
-- the player attribute MenuCursorBy names them too, for tests: a test logs the mouse each frame from its own RenderStep)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")

local me = Players.LocalPlayer
local M = {}

type Holder = { alive: (() -> boolean)?, menu: boolean }
local held: { [string]: Holder } = {}
local n, menus = 0, 0

local function names(): { string }
	local out = {}
	for k in held do table.insert(out, k) end
	table.sort(out)
	return out
end

local function publish()
	me:SetAttribute("MenuCursor", n > 0)
	me:SetAttribute("MenuCursorBy", if n > 0 then table.concat(names(), ",") else nil)
end

local function free()
	if UIS.MouseBehavior ~= Enum.MouseBehavior.Default then UIS.MouseBehavior = Enum.MouseBehavior.Default end
	if not UIS.MouseIconEnabled then UIS.MouseIconEnabled = true end
end

function M.set(name: string, on: boolean, alive: (() -> boolean)?, cursorOnly: boolean?)
	local h = held[name]
	if on then
		if h then
			if h.menu then menus -= 1 end
		else
			n += 1
		end
		local menu = cursorOnly ~= true
		held[name] = { alive = alive, menu = menu }
		if menu then menus += 1 end
		publish()
		free()
	elseif h then
		held[name] = nil
		n -= 1
		if h.menu then menus -= 1 end
		publish()
	end
end
function M.on(): boolean return n > 0 end
function M.menu(): boolean return menus > 0 end
function M.has(name: string): boolean return held[name] ~= nil end
function M.list(): { string } return names() end

-- LoadoutOpen can't outlive everything that holds it (18 Nov 2026, the owner: "sometimes when you go into 3rd person it
-- locks your camera away from your character and doesnt let you go back into first person"). each screen saves
-- LoadoutOpen as it opens and puts that back as it closes; closed in another order than they opened (the Play panel
-- and the party panel, a finisher and the play of the match, a crate opened with Toggle Cursor on, the settings page
-- or the match's loadout picker up while another screen closed: the guard below raised it again) the last one left a
-- true that nothing held: the shoulder camera held still for a menu that wasn't there, V and the guns were ignored.
-- what holds it: a menu here (menus), a finisher (Finishing), a crate reveal (LootOpening), the play of the match
-- (Replay). up with none of them for STALE seconds, it goes down; M.unstick() takes it down at once (V: Move.client)
local Replay: any = nil
task.defer(function() -- (after this module has loaded: Replay's own requires may come back here)
	local m = script.Parent:WaitForChild("Replay", 30)
	if not m then return end
	local ok, r = pcall(require, m)
	if ok then Replay = r end
end)
function M.holding(): boolean
	if menus > 0 then return true end
	if me:GetAttribute("Finishing") or me:GetAttribute("LootOpening") ~= nil then return true end
	if Replay and Replay.isPlaying and Replay.isPlaying() then return true end
	return false
end
local STALE = 0.5
local staleT: number? = nil
function M.unstick(): boolean
	staleT = nil
	if me:GetAttribute("LoadoutOpen") == true and not M.holding() then
		me:SetAttribute("LoadoutOpen", false)
		return true
	end
	return false
end

-- after every camera (Roblox's first person at Camera, the shoulder camera just before it, the Play panel's lineup at
-- Last + 60): while a menu is up the mouse stays free and the arrow shows
RunService:BindToRenderStep("JankMenuCursor", Enum.RenderPriority.Last.Value + 100, function()
	if me:GetAttribute("LoadoutOpen") == true and not M.holding() then
		staleT = staleT or os.clock()
		if os.clock() - (staleT :: number) >= STALE then M.unstick() end
	else
		staleT = nil
	end
	if n == 0 then return end
	local gone: { string }? = nil
	for k, h in held do
		if h.alive then
			local ok, up = pcall(h.alive)
			if ok and not up then
				gone = gone or {}
				table.insert(gone :: { string }, k)
			end
		end
	end
	if gone then for _, k in gone do M.set(k, false) end end
	if n > 0 then free() end
end)

-- a screen closing over another one clears LoadoutOpen (each saves it when it opens and puts that back when it
-- closes, and the order they close in isn't the order they opened in): while a menu is still up it goes back up
me:GetAttributeChangedSignal("LoadoutOpen"):Connect(function()
	if menus > 0 and me:GetAttribute("LoadoutOpen") ~= true then
		task.defer(function()
			if menus > 0 and me:GetAttribute("LoadoutOpen") ~= true then me:SetAttribute("LoadoutOpen", true) end
		end)
	end
end)

return M
