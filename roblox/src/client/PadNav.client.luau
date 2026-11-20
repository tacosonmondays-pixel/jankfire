--!strict
-- menus on a controller (18 Nov 2026, controller support; the whole layout: docs/CONTROLLER.md). Roblox's own gamepad
-- selection does the moving (GuiService.SelectedObject: the D-pad and the left stick step between buttons, A presses
-- the one picked); this script decides WHERE it may go and adds the rest:
--   * while a menu is up (MenuCursor: the shop, the loadout, settings, ...) the selection lives in that menu's screen:
--     it starts on a sensible button, comes back after the screen rebuilds its buttons (to the one nearest where it
--     was), never lands on a full-screen catcher, never wanders out to the HUD behind. a list scrolls to it
--   * B backs out of the top menu (an overlay first: the shop's inspect / odds / confirm), the bumpers step a menu's
--     tabs (settings, the shop, the Play panel), left and right nudge a settings slider, the right stick scrolls
--   * no menu up: nothing is selected (the sticks are yours). VIEW goes to the buttons on screen: a pop-up first (the
--     match loadout strip, an invite, quick join, a vote), else the hub's menu column and SETTINGS; with nothing else
--     there (a match) it opens SETTINGS. B or VIEW again leaves them. (Start is Roblox's own menu)
--   * the picked button wears one quiet ring (white, rounded: PlayerGui.SelectionImageObject); a mouse player never
--     sees it (the selection is cleared the moment the mouse moves)
--   * hints: bracketed keys in menu text ("DONE  [L]") follow the pad too (Pad.say), and a few key caps say which pad
--     button they mean (Pad attribute: the View glyph by SETTINGS, B on the shop's CLOSE and on SKIP)
-- (VIEW's order: pop-up ads / a quiz, the end-of-match board's REPORTs, the match loadout strip, an invite, quick join, a
-- vote, then the hub's menu column and SETTINGS)
-- Studio tests: player attribute PadNavTest = "bar" (as VIEW), "back" (as B), "tab:1" / "tab:-1" (the bumpers),
-- "nudge:1" / "nudge:-1", "select:<full name>" ; PadNavState (read) = JSON of the top menu and the selection
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local GuiService = game:GetService("GuiService")
local HttpService = game:GetService("HttpService")

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui") :: PlayerGui
local J = script.Parent
local Pad = require(J:WaitForChild("Pad")) :: any
local MenuCursor = require(J:WaitForChild("MenuCursor")) :: any
local Keys = require(J:WaitForChild("Keys")) :: any
local T = require(J:WaitForChild("Theme")) :: any

local mods: { [string]: any } = {}
local function mod(name: string): any
	local m = mods[name]
	if m ~= nil then return m or nil end
	local s = J:FindFirstChild(name)
	local ok, r = false, nil
	if s and s:IsA("ModuleScript") then ok, r = pcall(require, s) end
	mods[name] = if ok and type(r) == "table" then r else false
	return mods[name] or nil
end

-- ------------------------------------------------------------------ the ring
pcall(function() GuiService.AutoSelectGuiEnabled = false end) -- (VIEW is ours: Roblox's own "select the first thing" is off)
local ring = Instance.new("Frame")
ring.Name = "JankPadFocus"
ring.BackgroundColor3 = T.TEXT
ring.BackgroundTransparency = 0.93
ring.BorderSizePixel = 0
ring.Position = UDim2.fromOffset(-3, -3) -- (a selection image's AnchorPoint is ignored: placed from its top left)
ring.Size = UDim2.new(1, 6, 1, 6)
do
	local c = Instance.new("UICorner"); c.CornerRadius = UDim.new(0, 7); c.Parent = ring
	local s = Instance.new("UIStroke"); s.Color = T.TEXT; s.Thickness = 2; s.Transparency = 0.05
	s.ApplyStrokeMode = Enum.ApplyStrokeMode.Border; s.Parent = ring
end
pcall(function() (pg :: any).SelectionImageObject = ring end)

-- ------------------------------------------------------------------ the menus (MenuCursor names)
local function tapEsc() Keys.tap(Enum.KeyCode.Escape) end
local backN = 0
local function menuBack(name: string)
	backN += 1
	me:SetAttribute("MenuBack", name .. "#" .. backN)
end
local function cycle(list: { string }, cur: string?, dir: number): string?
	if #list == 0 then return nil end
	local i = (cur and table.find(list, cur)) or 1
	return list[(i - 1 + dir) % #list + 1]
end

local profTab, boardTab = "profile", "duels" -- (the profile card's and the ranked board's tab, as last stepped or pressed)
type Spec = { gui: string, back: (() -> ())?, tabs: ((number) -> ())?, nav: boolean?, first: (() -> GuiObject?)? }
local MENUS: { [string]: Spec } = {
	settings = {
		gui = "JankSettings",
		back = function() me:SetAttribute("SettingsOpen", false) end,
		tabs = function(dir: number)
			local UI = mod("SettingsUI")
			local g = pg:FindFirstChild("JankSettings")
			local rail = g and g:FindFirstChild("Page") and g.Page:FindFirstChild("Rail")
			local tabsF = rail and rail:FindFirstChild("Tabs")
			if not (UI and tabsF) then return end
			local list = {}
			for _, b in tabsF:GetChildren() do
				if b:IsA("GuiButton") and b.Visible then table.insert(list, b) end
			end
			table.sort(list, function(a: any, b: any) return a.LayoutOrder < b.LayoutOrder end)
			local ids = {}
			for _, b in list do table.insert(ids, b.Name) end
			local nxt = cycle(ids, UI.tabId, dir)
			if nxt then UI.show(nxt) end
		end,
		first = function()
			local UI = mod("SettingsUI")
			local g = pg:FindFirstChild("JankSettings")
			local tabsF = g and g:FindFirstChild("Tabs", true)
			local b = tabsF and UI and UI.tabId and tabsF:FindFirstChild(UI.tabId)
			return if b and b:IsA("GuiButton") then b else nil
		end,
	},
	shop = {
		gui = "JankShop",
		back = function()
			local S = mod("ShopUI")
			if not S then return end
			local U = S.UI or {}
			if U.confirm and U.confirm.Visible then S.unconfirm()
			elseif U.panel and U.panel.Visible and S.unpanel then S.unpanel() -- (the shop's PICK, GIFT and how-many panel: B cancels)
			elseif U.odds and U.odds.Visible then S.shutOverlays()
			elseif U.insp and U.insp.Visible then S.back()
			else S.close() end
		end,
		tabs = function(dir: number)
			local S = mod("ShopUI")
			if not S or not S.S then return end
			local U = S.UI or {}
			if (U.confirm and U.confirm.Visible) or (U.odds and U.odds.Visible) or (U.insp and U.insp.Visible) then return end
			local nxt = cycle({ "featured", "deals", "bundles", "containers", "inventory" }, S.S.tab, dir)
			if nxt then S.tab(nxt) end
		end,
	},
	loadout = { gui = "JankLoadout", back = function() menuBack("loadout") end },
	matchloadout = { gui = "JankMatchLoadout", back = tapEsc },
	play = {
		gui = "JankPlay",
		tabs = function(dir: number)
			local P = mod("PlayUI")
			if P and P.S and P.tab then
				local nxt = cycle({ "duels", "modes" }, P.S.tab, dir)
				if nxt then P.tab(nxt) end
			end
		end,
	},
	party = { gui = "JankParty", back = function() local m = mod("PartyUI"); if m then m.close() end end },
	quests = { gui = "JankQuests", back = function() local m = mod("QuestUI"); if m then m.close() end end },
	card = {
		gui = "JankProfile",
		back = function() local m = mod("ProfileUI"); if m then m.close() end end,
		tabs = function(dir: number) -- (the card's tab is its own; PadNav keeps count: the bumpers, or A on a Tab_ button)
			local m = mod("ProfileUI")
			local nxt = cycle({ "profile", "customize", "players" }, profTab, dir)
			if m and m.tab and nxt then profTab = nxt; m.tab(nxt) end
		end,
	},
	loot = {
		gui = "JankLootOpening",
		back = function()
			local O = mod("LootOpening")
			if not O then return end
			local g = pg:FindFirstChild("JankLootOpening")
			local rv = g and g:FindFirstChild("Reveal", true) :: GuiObject?
			local sm = g and g:FindFirstChild("Summary", true) :: GuiObject?
			if (rv and rv.Visible) or (sm and sm.Visible) then O.finish("done") else O.skip() end
		end,
	},
	board = {
		gui = "JankBoard",
		back = function() local m = mod("LeaderboardUI"); if m then m.close() end end,
		tabs = function(dir: number)
			local m = mod("LeaderboardUI")
			local nxt = cycle({ "duels", "party" }, boardTab, dir)
			if m and m.open and nxt then boardTab = nxt; m.open(nxt) end
		end,
	},
	wheel = { gui = "JankEmoteWheel", nav = false, back = tapEsc }, -- (the right stick points: FlairClient)
	flair = { gui = "JankFlairUI", back = function() local m = mod("FlairUI"); if m then m.close() end end },
	report = { gui = "ReportDialog", back = function() local m = mod("ReportUI"); if m then m.close() end end },
	anticheat = { gui = "AntiCheatPanel", back = function() local g = pg:FindFirstChild("AntiCheatPanel"); if g and g:IsA("ScreenGui") then g.Enabled = false end end },
}
Pad.MENUS = MENUS -- (other scripts may add their own screen: Pad.MENUS.<MenuCursor name> = { gui = ..., back = fn })

-- the order menus came up in: the newest is the one B talks to
local order: { string } = {}
local function syncOrder()
	local now = MenuCursor.list()
	local set = {}
	for _, n in now do set[n] = true end
	for i = #order, 1, -1 do if not set[order[i]] then table.remove(order, i) end end
	for _, n in now do if not table.find(order, n) then table.insert(order, n) end end
end
local function guiOf(spec: Spec): ScreenGui?
	local g = pg:FindFirstChild(spec.gui)
	return if g and g:IsA("ScreenGui") and g.Enabled then g else nil
end
local function topMenu(): (string?, Spec?, ScreenGui?)
	for i = #order, 1, -1 do
		local spec = MENUS[order[i]]
		if spec then
			local g = guiOf(spec)
			if g then return order[i], spec, g end
		end
	end
	return nil, nil, nil
end

-- ------------------------------------------------------------------ what can be picked
local function shown(o: Instance, root: Instance): boolean
	local p: Instance? = o
	while p and p ~= root do
		if p:IsA("GuiObject") and not p.Visible then return false end
		if p:IsA("ScreenGui") then return p.Enabled and p == root end
		p = p.Parent
	end
	if p and p:IsA("ScreenGui") then return p.Enabled end
	return p == root
end
local function viewport(): Vector2
	local cam = workspace.CurrentCamera
	return if cam then cam.ViewportSize else Vector2.new(1280, 720)
end
-- catchers (a full-screen button that only stops clicks) and buttons that hold other buttons are never picked. it's
-- measured each time, not once: a screen laid out after it was first seen (a scrim still at size 0) must count
local function catcher(o: GuiObject): boolean
	local vp = viewport()
	return o.AbsoluteSize.X >= vp.X * 0.85 and o.AbsoluteSize.Y >= vp.Y * 0.85
end
local function prep(g: ScreenGui)
	for _, d in g:GetDescendants() do
		if d:IsA("GuiButton") and d.Selectable and d.AbsoluteSize.X > 0 and (catcher(d) or d:FindFirstChildWhichIsA("GuiButton", true)) then
			d.Selectable = false
		end
	end
	-- (the screen's own top frames keep the selection in: it stops at their edges instead of going out to the HUD)
	for _, c in g:GetChildren() do
		if c:IsA("GuiObject") and not c:GetAttribute("PadGroup") then
			c:SetAttribute("PadGroup", true)
			c.SelectionGroup = true
			c.SelectionBehaviorUp = Enum.SelectionBehavior.Stop
			c.SelectionBehaviorDown = Enum.SelectionBehavior.Stop
			c.SelectionBehaviorLeft = Enum.SelectionBehavior.Stop
			c.SelectionBehaviorRight = Enum.SelectionBehavior.Stop
		end
	end
end
local function pickable(o: Instance, root: Instance): boolean
	if not o:IsA("GuiObject") or not o.Selectable then return false end
	if not (o:IsA("GuiButton") or o:IsA("TextBox") or o:GetAttribute("PadPick")) then return false end
	if o.AbsoluteSize.X < 4 or o.AbsoluteSize.Y < 4 then return false end
	if o:IsA("GuiButton") and (catcher(o) or o:FindFirstChildWhichIsA("GuiButton", true)) then return false end
	return shown(o, root)
end
local function candidates(root: Instance): { GuiObject }
	local out = {}
	for _, d in root:GetDescendants() do
		if pickable(d, root) then table.insert(out, d :: GuiObject) end
	end
	return out
end
local function centre(o: GuiObject): Vector2 return o.AbsolutePosition + o.AbsoluteSize / 2 end
local function topLeft(list: { GuiObject }): GuiObject?
	local best, bk = nil, math.huge
	for _, o in list do
		local p = o.AbsolutePosition
		local k = math.floor(p.Y / 12) * 100000 + p.X -- (rows first, then left to right)
		if k < bk then best, bk = o, k end
	end
	return best
end
local function nearest(list: { GuiObject }, at: Vector2): GuiObject?
	local best, bd = nil, math.huge
	for _, o in list do
		local d = (centre(o) - at).Magnitude
		if d < bd then best, bd = o, d end
	end
	return best
end

-- a list scrolls the picked button into view
local function scrollTo(o: GuiObject)
	local p = o.Parent
	while p and not p:IsA("ScreenGui") do
		if p:IsA("ScrollingFrame") then
			local sf = p :: ScrollingFrame
			local win = sf.AbsoluteWindowSize
			local rel = o.AbsolutePosition - sf.AbsolutePosition
			local cp = sf.CanvasPosition
			local m = 16
			local x, y = cp.X, cp.Y
			if rel.Y < m then y += rel.Y - m elseif rel.Y + o.AbsoluteSize.Y > win.Y - m then y += rel.Y + o.AbsoluteSize.Y - (win.Y - m) end
			if rel.X < m then x += rel.X - m elseif rel.X + o.AbsoluteSize.X > win.X - m then x += rel.X + o.AbsoluteSize.X - (win.X - m) end
			local maxV = sf.AbsoluteCanvasSize - win
			sf.CanvasPosition = Vector2.new(math.clamp(x, 0, math.max(0, maxV.X)), math.clamp(y, 0, math.max(0, maxV.Y)))
			return
		end
		p = p.Parent
	end
end

-- ------------------------------------------------------------------ VIEW: the buttons on screen
local bar: { GuiObject }? = nil
local barKind = ""
local barLinks: { GuiObject } = {}
local madeSel: { GuiObject } = {} -- (frames made pickable for VIEW: the settings hint, an ad)
local function hint(): GuiObject?
	local g = pg:FindFirstChild("JankSettings")
	local sc = g and g:FindFirstChild("Scaled")
	local h = sc and sc:FindFirstChild("Hint")
	return if h and h:IsA("GuiObject") and shown(h, g :: Instance) then h else nil
end
local function addShown(out: { GuiObject }, root: Instance?, names: { string }?)
	if not root then return end
	local gui = root:FindFirstAncestorOfClass("ScreenGui") or root
	if root:IsA("ScreenGui") and not root.Enabled then return end
	for _, d in root:GetDescendants() do
		if d:IsA("GuiButton") and d.Selectable and shown(d, gui) and d.AbsoluteSize.X >= 4 and (not names or table.find(names, d.Name)) then
			table.insert(out, d)
		end
	end
end
local function barTargets(): ({ GuiObject }, string, string)
	local out: { GuiObject } = {}
	-- what someone threw at you first: pop-up ads (a number key closes each) and a pop quiz (Utility.client's overlay)
	local ov = pg:FindFirstChild("JankfireItemsOverlay")
	if ov and ov:IsA("ScreenGui") and ov.Enabled then
		for _, d in ov:GetDescendants() do
			if d:IsA("GuiObject") and shown(d, ov) and ((d.Name == "Ad" and d:FindFirstChild("Bar")) or (d:IsA("GuiButton") and string.match(d.Name, "^A%d$") and d.Parent and d.Parent.Name == "Exam")) then
				table.insert(out, d)
			end
		end
		table.sort(out, function(a, b) return a.AbsolutePosition.X < b.AbsolutePosition.X end)
		if #out > 0 then return out, "row", "pop" end
	end
	-- the end-of-match board: its REPORT buttons (ReportClient puts one on every other player's row)
	local fight = pg:FindFirstChild("JankfireFight")
	local endF = fight and fight:FindFirstChild("End", true)
	if endF and endF:IsA("GuiObject") and shown(endF, fight :: Instance) then
		addShown(out, endF, { "Report" })
		table.sort(out, function(a, b) return a.AbsolutePosition.Y < b.AbsolutePosition.Y end)
		if #out > 0 then return out, "column", "board" end
	end
	-- a pop-up: the match loadout strip, an invite, quick join, a vote
	local ml = pg:FindFirstChild("JankMatchLoadout")
	local strip = ml and ml:FindFirstChild("Strip", true)
	if strip and strip:IsA("GuiObject") and shown(strip, ml :: Instance) then
		addShown(out, strip, { "Slot1", "Slot2", "Slot3", "Slot4", "Ready" })
		if #out > 0 then return out, "row", "strip" end
	end
	local jp = pg:FindFirstChild("JankPlay")
	local st = jp and jp:FindFirstChild("Scaled") and jp.Scaled:FindFirstChild("Stage")
	local inv = st and st:FindFirstChild("Invite")
	if inv and inv:IsA("GuiObject") and not inv:IsA("GuiButton") and shown(inv, jp :: Instance) then
		addShown(out, inv, { "Join", "Decline" })
		if #out > 0 then return out, "row", "invite" end
	end
	local q = pg:FindFirstChild("JankQuick")
	if q then addShown(out, q, { "Join" }) end
	if #out > 0 then return out, "row", "quick" end
	local tq = pg:FindFirstChild("JankTradeAsk") -- (a trade request: TradeUI, play-party-ranked's)
	if tq then addShown(out, tq, { "Accept", "Decline" }) end
	if #out > 0 then return out, "row", "trade" end
	local v = pg:FindFirstChild("JankVote")
	if v then addShown(out, v) end
	if #out > 0 then return out, "row", "vote" end
	-- the hub's menu column, then SETTINGS
	for _, n in { "JankLoadoutButton", "JankPlayButton", "JankShopButton", "JankProfileButton", "JankQuestsButton", "JankHubsButton", "JankDevButton" } do -- (JankDevButton: the owner's only, OwnerDev.client; JankHubsButton: HubTravelUI)
		addShown(out, pg:FindFirstChild(n))
	end
	table.sort(out, function(a, b) return a.AbsolutePosition.Y < b.AbsolutePosition.Y end)
	local h = hint()
	if h then table.insert(out, h) end
	return out, "column", "menus"
end
local function endBar()
	if not bar then return end
	for _, o in barLinks do
		if o.Parent then o.NextSelectionUp = nil; o.NextSelectionDown = nil; o.NextSelectionLeft = nil; o.NextSelectionRight = nil end
	end
	table.clear(barLinks)
	for _, o in madeSel do o.Selectable = false end
	table.clear(madeSel)
	bar = nil
	if GuiService.SelectedObject and GuiService.SelectedObject:IsDescendantOf(pg) then GuiService.SelectedObject = nil end
end
local function openSettings() me:SetAttribute("SettingsOpen", true) end
local function startBar(auto: boolean?)
	local list, how, kind = barTargets()
	local h = hint()
	if auto and kind ~= "pop" then return end -- (the last ad closed: back to playing)
	if #list == 0 or (#list == 1 and list[1] == h) then openSettings(); return end
	barKind = kind
	for i, o in list do
		if not o:IsA("GuiButton") and not o.Selectable then o.Selectable = true; table.insert(madeSel, o) end
		local prev, nxt = list[(i - 2) % #list + 1], list[i % #list + 1]
		if how == "column" then
			o.NextSelectionUp = prev; o.NextSelectionDown = nxt; o.NextSelectionLeft = o; o.NextSelectionRight = o
		else
			o.NextSelectionLeft = prev; o.NextSelectionRight = nxt; o.NextSelectionUp = o; o.NextSelectionDown = o
		end
		table.insert(barLinks, o)
	end
	bar = list
	GuiService.SelectedObject = list[1]
end

-- ------------------------------------------------------------------ every frame: where the selection may be
local lastAt: Vector2? = nil
local lastTop: string? = nil
local dirty = true
local prepT = 0
pg.DescendantAdded:Connect(function() dirty = true end)
local function ours(o: Instance?): boolean return o ~= nil and o:IsDescendantOf(pg) end
GuiService:GetPropertyChangedSignal("SelectedObject"):Connect(function()
	local o = GuiService.SelectedObject
	if o and ours(o) then lastAt = centre(o); task.defer(scrollTo, o) end
end)

local nudgeHeld: number? = nil -- (-1 / 1 while a D-pad side or the stick holds a slider over)
local nudgeNext = 0
local function nudger(): ((number) -> ())?
	local o = GuiService.SelectedObject
	local UI = o and mod("SettingsUI")
	return if UI and UI.nudge then UI.nudge[o] else nil
end
RunService:BindToRenderStep("JankPadNav", Enum.RenderPriority.Last.Value + 110, function(dt: number)
	syncOrder()
	local sel = GuiService.SelectedObject
	if not Pad.on() then
		if bar then endBar() end
		if sel and ours(sel) then GuiService.SelectedObject = nil end
		lastTop = nil
		return
	end
	local name, spec, g = topMenu()
	if name ~= lastTop then
		lastTop = name
		lastAt = nil
		if name then endBar() end
		if name == "card" then profTab = "profile" end
		dirty = true
	end
	if spec and g then
		if spec.nav == false then
			if sel and ours(sel) then GuiService.SelectedObject = nil end
			return
		end
		if dirty and os.clock() - prepT > 0.25 then dirty = false; prepT = os.clock(); prep(g) end
		if not (sel and sel:IsDescendantOf(g) and pickable(sel, g)) then
			local list = candidates(g)
			local pick = if lastAt then nearest(list, lastAt :: Vector2) else nil
			if not pick and spec.first then
				local f = spec.first()
				if f and pickable(f, g) then pick = f end
			end
			pick = pick or topLeft(list)
			if pick ~= sel then GuiService.SelectedObject = pick end
			sel = pick
		elseif sel then
			lastAt = centre(sel)
		end
		-- the right stick scrolls the list the selection is in (or the screen's biggest)
		local st = Pad.stick(2)
		if math.abs(st.Y) > 0.3 then
			local sf: ScrollingFrame? = nil
			local p = sel and sel.Parent
			while p and p ~= g do
				if p:IsA("ScrollingFrame") then sf = p; break end
				p = p.Parent
			end
			if not sf then
				local area = 0
				for _, d in g:GetDescendants() do
					if d:IsA("ScrollingFrame") and shown(d, g) and d.AbsoluteSize.X * d.AbsoluteSize.Y > area then sf = d; area = d.AbsoluteSize.X * d.AbsoluteSize.Y end
				end
			end
			if sf then
				local maxY = math.max(0, sf.AbsoluteCanvasSize.Y - sf.AbsoluteWindowSize.Y)
				local y = math.clamp(sf.CanvasPosition.Y - st.Y * 1100 * dt, 0, maxY)
				sf.CanvasPosition = Vector2.new(sf.CanvasPosition.X, y)
			end
		end
		-- a slider held over: it keeps stepping
		local fn = nudger()
		local sx = Pad.stick(1).X
		local dir = nudgeHeld or (if sx > 0.6 then 1 elseif sx < -0.6 then -1 else nil)
		if fn and dir then
			if os.clock() >= nudgeNext then
				fn(dir)
				nudgeNext = os.clock() + (if nudgeNext == 0 then 0.35 else 0.06)
			end
		else
			nudgeNext = 0
		end
		return
	end
	-- no menu: VIEW's buttons, or nothing
	if bar then
		if not (sel and table.find(bar, sel) and shown(sel, sel:FindFirstAncestorOfClass("ScreenGui") :: Instance)) then
			local was = barKind
			endBar()
			if was == "pop" then startBar(true) end -- (an ad closed: the next one)
		end
		return
	end
	if sel and ours(sel) then GuiService.SelectedObject = nil end
end)

-- ------------------------------------------------------------------ the buttons
local function capturing(): boolean
	local UI = mod("SettingsUI")
	return UI ~= nil and UI.capturing == true
end
local function back()
	if capturing() then return end
	if bar then endBar(); return end
	syncOrder()
	local _, spec = topMenu()
	-- (a beat later: the B that closes a menu must not reach the crouch in the same moment)
	if spec and spec.back then task.delay(0.03, spec.back) end
end
local function tabs(dir: number)
	if capturing() then return end
	local _, spec = topMenu()
	if spec and spec.tabs then spec.tabs(dir) end
end
UIS.InputBegan:Connect(function(io: InputObject)
	if not Pad.isPad(io) then return end
	local k = io.KeyCode
	if k == Enum.KeyCode.ButtonB then back()
	elseif k == Enum.KeyCode.ButtonL1 then tabs(-1)
	elseif k == Enum.KeyCode.ButtonR1 then tabs(1)
	elseif k == Enum.KeyCode.ButtonSelect then
		if capturing() then return end
		syncOrder()
		local name = topMenu()
		if name == "settings" then me:SetAttribute("SettingsOpen", false)
		elseif name then return
		elseif bar then endBar()
		else startBar() end
	elseif k == Enum.KeyCode.ButtonA then
		local h = hint()
		local o = GuiService.SelectedObject
		local tn = o and string.match(o.Name, "^Tab_?(%a+)$")
		if tn and (tn == "profile" or tn == "customize" or tn == "players") then profTab = tn end
		if tn and (tn == "duels" or tn == "party") then boardTab = tn end
		if bar and h and o == h then endBar(); openSettings()
		elseif bar and o and o.Name == "Ad" then
			-- (an ad closes with its number key: the same key, through Keys, as a phone's tap)
			local cap = o:FindFirstChild("Key", true)
			local n = cap and cap:FindFirstChild("Letter") and tonumber((cap :: any).Letter.Text)
			local code = n and ({ Enum.KeyCode.One, Enum.KeyCode.Two, Enum.KeyCode.Three, Enum.KeyCode.Four, Enum.KeyCode.Five })[n]
			if code then Keys.tap(code) end
		end
	elseif k == Enum.KeyCode.DPadLeft or k == Enum.KeyCode.DPadRight then
		local fn = nudger()
		if fn then
			nudgeHeld = if k == Enum.KeyCode.DPadRight then 1 else -1
			fn(nudgeHeld :: number)
			nudgeNext = os.clock() + 0.35
		end
	end
end)
UIS.InputEnded:Connect(function(io: InputObject)
	if io.KeyCode == Enum.KeyCode.DPadLeft or io.KeyCode == Enum.KeyCode.DPadRight then nudgeHeld = nil end
end)

-- ------------------------------------------------------------------ hints that follow the pad
-- key caps that mean a pad button their letter doesn't say: the View glyph where VIEW goes, B where B backs out
local function capOf(root: Instance?, under: string?): Instance?
	if not root then return nil end
	local host = if under then root:FindFirstChild(under, true) else root
	return host and host:FindFirstChild("Key", true)
end
local function decorate()
	local function mark(cap: Instance?, btn: string)
		if cap and cap:GetAttribute("Pad") ~= btn then cap:SetAttribute("Pad", btn) end
	end
	mark(capOf(pg:FindFirstChild("JankSettings"), "Hint"), "ButtonSelect")
	mark(capOf(pg:FindFirstChild("JankMatchLoadout"), "Head"), "ButtonSelect")
	mark(capOf(pg:FindFirstChild("JankQuick"), "Join"), "ButtonSelect")
	mark(capOf(pg:FindFirstChild("JankFinisher"), "Skip"), "ButtonB")
	mark(capOf(pg:FindFirstChild("JankReplay"), "Skip"), "ButtonB")
	local ov = pg:FindFirstChild("JankfireItemsOverlay")
	if ov then
		for _, d in ov:GetDescendants() do
			if d.Name == "Key" and d.Parent and (d.Parent.Name == "Bar" or string.match(d.Parent.Name, "^A%d$")) then mark(d, "ButtonSelect") end
		end
	end
	local S = mods.ShopUI
	if S and S.UI and S.UI.closeKey then mark(S.UI.closeKey, "ButtonB") end
end
task.spawn(function()
	while true do
		pcall(decorate)
		if MenuCursor.has("shop") and mods.ShopUI == nil then mod("ShopUI") end
		task.wait(1)
	end
end)
-- bracketed keys in a screen's words ("DONE  [L]", "SKIP  [SPACE]"): the pad's button, or nothing for a key it lacks
local texts: { [Instance]: string } = setmetatable({}, { __mode = "k" }) :: any
local written: { [Instance]: string } = setmetatable({}, { __mode = "k" }) :: any
local SKIP_GUIS = { JankfireFight = true, JankFps = true, JankfireHud = true } -- (the HUD's own every-frame words)
local function retext(o: TextLabel | TextButton)
	local orig = texts[o]
	if not orig then return end
	local src = orig
	-- (a crate's SKIP is A on a pad: LootOpening's own sink. other SPACE hints follow the binds)
	if string.sub(src, 1, 4) == "SKIP" then src = string.gsub(src, "%[SPACE%]", "[" .. Pad.short("ButtonA") .. "]") end
	local want = if Pad.on() then Pad.say(src, true) else orig
	if o.Text ~= want then written[o] = want; o.Text = want end
end
local function watch(o: Instance)
	if not (o:IsA("TextLabel") or o:IsA("TextButton")) or texts[o] then return end
	local sg = o:FindFirstAncestorOfClass("ScreenGui")
	if sg and SKIP_GUIS[sg.Name] then return end
	local t = o :: TextLabel
	if not string.find(t.Text, "%[%w+%]") then
		-- (it may get its words later)
		local c: RBXScriptConnection? = nil
		c = t:GetPropertyChangedSignal("Text"):Connect(function()
			if texts[o] then if c then c:Disconnect() end return end
			if string.find(t.Text, "%[%w+%]") then
				if c then c:Disconnect() end
				watch(o)
			end
		end)
		return
	end
	texts[o] = t.Text
	t:GetPropertyChangedSignal("Text"):Connect(function()
		if t.Text == written[o] then return end -- (our own write coming back)
		texts[o] = t.Text
		retext(t)
	end)
	retext(t)
end
pg.DescendantAdded:Connect(function(d)
	if d:IsA("TextLabel") or d:IsA("TextButton") then task.defer(watch, d) end
end)
for _, d in pg:GetDescendants() do watch(d) end
Pad.changed.Event:Connect(function()
	for o in texts do if o.Parent then retext(o :: any) end end
end)

-- ------------------------------------------------------------------ Studio tests
if RunService:IsStudio() then
	me:GetAttributeChangedSignal("PadNavTest"):Connect(function()
		local raw = me:GetAttribute("PadNavTest")
		if type(raw) ~= "string" then return end
		local cmd = string.gsub(raw, "#%d+$", "")
		local op, rest = string.match(cmd, "^(%a+):?(.*)$")
		if op == "bar" then
			syncOrder()
			if topMenu() then return end
			if bar then endBar() else startBar() end
		elseif op == "back" then back()
		elseif op == "tab" then tabs(tonumber(rest) or 1)
		elseif op == "nudge" then
			local fn = nudger()
			if fn then fn(tonumber(rest) or 1) end
		elseif op == "select" then
			local o: Instance? = game
			for part in string.gmatch(rest, "[^%.]+") do
				if o == game and part == "game" then continue end
				o = o and o:FindFirstChild(part)
			end
			if o and o:IsA("GuiObject") then GuiService.SelectedObject = o end
		end
	end)
	RunService.Heartbeat:Connect(function()
		if me:GetAttribute("PadNavWatch") ~= true then return end
		local name = topMenu()
		local o = GuiService.SelectedObject
		me:SetAttribute("PadNavState", HttpService:JSONEncode({ top = name or "", order = order, bar = bar ~= nil,
			sel = if o then o:GetFullName() else "", pos = if o then { o.AbsolutePosition.X, o.AbsolutePosition.Y } else {} }))
	end)
end
