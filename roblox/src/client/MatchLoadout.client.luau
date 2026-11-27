--!strict
-- the match loadout (17 Nov 2026, the owner: "allow us to change weapons before first round and between rounds", then
-- "can you have renders when selecting loadout"). a round-based match (duels and team duels, ranked too; never a
-- classic mode, which keeps its own weapons) opens a loadout window: the countdown before each round (20 s before round
-- 1) and the break between rounds (15 s), held at your spawn. the SERVER decides it: Matches sets the player attribute LoadoutWindow (the
-- server time it shuts) and clears it the moment the round goes live, and Loadout.luau only takes a pick in a match
-- while it is set. a pick goes to the Loadout remote ("pick"), like the hub screen's: alive (a countdown) it's in your
-- hands at once, dead (the break) you spawn with it next round.
-- while the window is open, without taking the mouse:
--   a strip of your four slots, each a live picture of the weapon wearing your own skin, hat and wrap (GunPreview),
--   under a header with the seconds left in big numbers and a bar that runs down with them.
-- L (the loadout key) takes the mouse (MenuCursor "matchloadout": the arrow free, clicks don't fire, you still move)
-- and opens the slot's picker on PRIMARY: every live weapon for that slot, each a picture in your looks, the one you
-- have marked. one click picks it; the picker stays open for the next slot (click a slot, or 1 2 3 4). L, Esc or DONE
-- closes it, and the window shutting closes it too. on a phone the slots are tapped straight away.
-- READY (18 Nov, the owner: "until move people lock in their set once both are ready"): the header's READY button, Space
-- (the "ready" key, Binds; the owner: "instead of enter to ready up in loadout phase can it be space") or a tap locks
-- your set for the round. while the window is open the ready key is taken before anything else sees it (a sink at
-- ContextActionService priority 3500): Space readies and never jumps, and no jump waits for the hold to let go. shut,
-- Space is a jump again (the MatchReady remote: Matches.ready; LoadoutReady on
-- you after). one tick a player, by team, says who has (ReadyTeams). everyone in: the window shuts early and the round
-- goes live 3 s later; whoever doesn't lock in keeps what they had.
-- desktop: the strip sits low in the middle, the picker over it. phone (or a small screen): the strip sits at the top
-- under the score, the picker under it, clear of the stick and the fire buttons.
-- test hook: the LocalPlayer attribute MatchLoadoutTest = "open" | "slot:<slot>" | "close" | "ready" | "pick:<slot>:<weapon>"
-- ("pick" answers on MatchLoadoutResult), "fake:844x390" (laid out in a box that size, as on that screen) | "real"
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ContextActionService = game:GetService("ContextActionService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Roster = require(Shared:WaitForChild("Roster")) :: any
-- (27 Nov 2026, the owner's pick: the picker belongs with the loadout, so B BROADCAST's colours: black slabs, square
-- corners, white for the chosen slot (with a cut corner), Butter only on READY. UiKit.themeB is Theme in those colours)
local K = require(script.Parent:WaitForChild("UiKit")) :: any
local T = K.themeB()
local Binds = require(script.Parent:WaitForChild("Binds")) :: any
local Keys = require(script.Parent:WaitForChild("Keys")) :: any
local MenuCursor = require(script.Parent:WaitForChild("MenuCursor")) :: any
local GunPreview = require(script.Parent:WaitForChild("GunPreview")) :: any
local Unlocks = require(Shared:WaitForChild("Unlocks")) :: any -- (weapons open by level, a few are Robux: docs/PROGRESSION.md)
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Loadout") :: RemoteFunction
local TeamColorsMod = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("TeamColors")) :: any -- (shared/TeamColors.luau: the pads' and the matches' palette, 20 Nov 2026)
local TEAM_COLORS = { TeamColorsMod.color(1), TeamColorsMod.color(2), TeamColorsMod.color(3), TeamColorsMod.color(4) } -- (the score's)

local me = Players.LocalPlayer
local new, text = T.new, T.text

local S = {
	tray = nil :: string?, -- the slot whose picker is open (the mouse is out while it is)
	fake = nil :: Vector2?,
	asking = nil :: string?, -- the weapon a pick is out for
	note = nil :: string?,
	total = 0, -- how long the window was when it opened (the bar)
	shown = false,
	small = nil :: boolean?, -- the layout drawn: phone-sized or not
	hover = nil :: string?,
	readying = false, -- (a READY is out to the server)
}
local function isReady(): boolean return me:GetAttribute("LoadoutReady") == true end

-- (the window is shut the moment any of these says so, whichever comes first: the server's shut time passing on this
-- client's clock, the attribute cleared, RoundEnds set (the round is live). owner, 18 Nov: "your choose loudout stays on
-- screen until you move after the countdown")
local function windowLeft(): number?
	local w = me:GetAttribute("LoadoutWindow")
	if type(w) ~= "number" or me:GetAttribute("RoundEnds") ~= nil then return nil end
	local left = w - workspace:GetServerTimeNow()
	return if left > 0 then left else nil
end
local function picks(): { string }
	local s = me:GetAttribute("LoadoutNext")
	return if type(s) == "string" then string.split(s, ",") else {}
end
local function choices(slot: string): { any }
	local out = {}
	for _, e in Roster.list do if e.slot == slot and e.live then table.insert(out, e) end end
	return out
end
local function touch(): boolean
	return (UIS.TouchEnabled and not UIS.KeyboardEnabled) or game:GetService("StarterPlayer"):GetAttribute("TouchForce") == true
		or me:GetAttribute("TouchForce") == true or S.fake ~= nil
end
local function small(): boolean
	if touch() then return true end
	local cam = workspace.CurrentCamera
	local sz = if cam then cam.ViewportSize / T.scaleNow() else Vector2.new(1280, 720)
	return sz.Y < 560 or sz.X < 900
end

-- ---------------------------------------------------------------- the screen
local gui = new("ScreenGui", { Name = "JankMatchLoadout", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 18,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, me:WaitForChild("PlayerGui"))
local scaled = T.scaled(gui)
-- (everything sits in root: the whole screen, or a phone-sized box in its middle for a fake-screen test)
local root = new("Frame", { Name = "Root", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
	Size = UDim2.fromScale(1, 1), Visible = false }, scaled)

-- the strip: a header (LOADOUT, the key, the seconds and a bar) over the four slots
local strip = new("Frame", { Name = "Strip", BackgroundTransparency = 1 }, root)
local head = T.plate(strip, "Head", UDim2.fromOffset(0, 0), UDim2.fromOffset(100, 34))
local title = text(head, "Title", "LOADOUT", 16, T.TEXT, K.COND)
local cap = T.key(head, "L", UDim2.fromOffset(0, 6))
do -- (27 Nov, ui-mocks round 8: the one key cap family: bone, an ink capital, no outline)
	cap.BackgroundColor3 = K.A.BONE
	local st = cap:FindFirstChildOfClass("UIStroke"); if st then st.Enabled = false end
	local l = cap:FindFirstChild("Letter") :: TextLabel?; if l then l.TextColor3 = K.A.INK end
end
local secs = text(head, "Secs", "", 22, T.TEXT, K.COND, Enum.TextXAlignment.Right)
local sub = text(head, "Sub", "", 11, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Right)
-- READY, and the ticks: who has locked in, by team
local readyB = new("TextButton", { Name = "Ready", AutoButtonColor = false, BorderSizePixel = 0, Text = "READY", BackgroundColor3 = K.B.BUTTER,
	FontFace = K.COND, TextSize = 15, TextColor3 = K.B.INK, AnchorPoint = Vector2.new(1, 0.5), TextXAlignment = Enum.TextXAlignment.Left }, head)
local readySt = T.edge(readyB, T.ACCENT, 1, 1)
-- (the press shape: a triangle each side in the button's colour) and its key, the player's own (Binds "ready"), in a cap
local readyL = K.tri(readyB, UDim2.new(0, -6, 0, 0), 6, 24, K.B.BUTTER, "br"); readyL.Size = UDim2.new(0, 6, 1, 0)
local readyR = K.tri(readyB, UDim2.new(1, 0, 0, 0), 6, 24, K.B.BUTTER, "tl"); readyR.Size = UDim2.new(0, 6, 1, 0)
readyB:GetPropertyChangedSignal("BackgroundColor3"):Connect(function() readyL.BackgroundColor3 = readyB.BackgroundColor3; readyR.BackgroundColor3 = readyB.BackgroundColor3 end)
new("UIPadding", { PaddingLeft = UDim.new(0, 10) }, readyB)
local readyKey = new("TextLabel", { Name = "Key", BackgroundColor3 = K.A.BONE, BorderSizePixel = 0, AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -6, 0.5, 0),
	Size = UDim2.fromOffset(0, 16), AutomaticSize = Enum.AutomaticSize.X, FontFace = K.SANS_HEAVY, TextSize = 10, TextColor3 = K.A.INK, Text = "" }, readyB) -- (round 8: the one cap family)
new("UIPadding", { PaddingLeft = UDim.new(0, 5), PaddingRight = UDim.new(0, 5) }, readyKey)
local ticks = new("Frame", { Name = "Ticks", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0, 0.5) }, head)
new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, 10),
	SortOrder = Enum.SortOrder.LayoutOrder }, ticks)
local track = new("Frame", { Name = "Track", BorderSizePixel = 0, BackgroundColor3 = T.TRACK or T.CARD_HI, AnchorPoint = Vector2.new(0, 1) }, head)
local fill = new("Frame", { Name = "Fill", BorderSizePixel = 0, BackgroundColor3 = T.TEXT, Size = UDim2.fromScale(1, 1) }, track)
track.Visible = false -- (27 Nov, ui-mocks round 10: it read as ready progress beside "0 of 1 ready"; the seconds say the time)

type Tile = { slot: string, btn: TextButton, st: UIStroke, lab: TextLabel, name: TextLabel, vp: ViewportFrame, cam: Camera }
local tiles: { Tile } = {}
local setTray: (string?) -> ()
for i, slot in Roster.SLOTS do
	local btn = new("TextButton", { Name = "Slot" .. i, Text = "", AutoButtonColor = false, BorderSizePixel = 0, BackgroundColor3 = T.BG,
		BackgroundTransparency = T.BG_A }, strip)
	T.corner(btn, 6)
	local st = T.edge(btn)
	local lab = text(btn, "Slot", Roster.SLOT_NAMES[slot] or slot, 10, T.MUTED, T.FONT_BOLD)
	local vp, cam = GunPreview.viewport(btn, { Name = "Picture", BackgroundColor3 = T.CARD_HI, BackgroundTransparency = 0.55 })
	T.corner(vp, 4)
	local name = text(btn, "Name", "", 16, T.TEXT, K.COND) -- (round 10: the loadout's condensed Title Case)
	name.TextScaled = true
	new("UITextSizeConstraint", { MaxTextSize = 16, MinTextSize = 9 }, name)
	btn.Activated:Connect(function() setTray(if S.tray == slot then nil else slot) end)
	table.insert(tiles, { slot = slot, btn = btn, st = st, lab = lab, name = name, vp = vp, cam = cam })
end

-- the picker: the slot's weapons in a grid, a line and DONE under it
local tray = T.plate(root, "Picker", UDim2.fromOffset(0, 0), UDim2.fromOffset(100, 100))
tray.Visible = false
local grid = new("Frame", { Name = "Grid", BackgroundTransparency = 1 }, tray)
local gridLayout = new("UIGridLayout", { SortOrder = Enum.SortOrder.LayoutOrder, CellPadding = UDim2.fromOffset(6, 6) }, grid)
local foot = text(tray, "Foot", "", 11, T.MUTED, T.FONT_BOLD)
foot.TextWrapped = true
local done = new("TextButton", { Name = "Done", AutoButtonColor = false, BorderSizePixel = 0, Text = "DONE", BackgroundColor3 = T.CARD,
	FontFace = T.FONT_HEAVY, TextSize = 12, TextColor3 = T.TEXT }, tray)
T.corner(done, 4)
done.Activated:Connect(function() setTray(nil) end)

type Card = { id: string, btn: TextButton, st: UIStroke, vp: ViewportFrame, cam: Camera, lk: TextLabel }
local cards: { Card } = {}
local cardsFor = ""

-- ---------------------------------------------------------------- sizes
local G = { tw = 138, th = 108, gap = 8, hh = 34, cw = 96, ch = 82, cols = 7 }
local function layout()
	local sm = small()
	S.small = sm
	if S.fake then
		root.Size = UDim2.fromOffset(S.fake.X, S.fake.Y)
	else
		root.Size = UDim2.fromScale(1, 1)
	end
	if sm then
		G.tw, G.th, G.gap, G.hh, G.cw, G.ch, G.cols = 96, 76, 6, 28, 66, 56, 7
	else
		G.tw, G.th, G.gap, G.hh, G.cw, G.ch, G.cols = 138, 108, 8, 34, 96, 82, 7
	end
	local w = #tiles * G.tw + (#tiles - 1) * G.gap
	local h = G.hh + 6 + G.th
	strip.Size = UDim2.fromOffset(w, h)
	if sm then
		strip.AnchorPoint = Vector2.new(0.5, 0); strip.Position = UDim2.new(0.5, 0, 0, 62)
	else
		strip.AnchorPoint = Vector2.new(0.5, 1); strip.Position = UDim2.new(0.5, 0, 1, -100)
	end
	head.Size = UDim2.fromOffset(w, G.hh)
	local t = touch()
	cap.Visible = not t
	cap.Position = UDim2.fromOffset(10, math.floor((G.hh - 22) / 2) - 1)
	title.Position = UDim2.fromOffset(if t then 12 else 40, 0); title.Size = UDim2.new(0, 120, 1, -3)
	secs.AnchorPoint = Vector2.new(1, 0); secs.Position = UDim2.new(1, -12, 0, 0); secs.Size = UDim2.new(0, 52, 1, -3)
	secs.TextSize = if sm then 18 else 22
	sub.AnchorPoint = Vector2.new(1, 0); sub.Position = UDim2.new(1, -60, 0, 0); sub.Size = UDim2.new(0, 220, 1, -3)
	track.Position = UDim2.new(0, 10, 1, -4); track.Size = UDim2.new(1, -20, 0, 2)
	local rw = if sm then 76 else 124
	readyB.Size = UDim2.fromOffset(rw, G.hh - 10); readyB.Position = UDim2.new(1, if sm then -50 else -62, 0.5, -1)
	ticks.Position = UDim2.fromOffset(if t then 92 else 124, math.floor(G.hh / 2) - 1); ticks.Size = UDim2.fromOffset(w - (if t then 92 else 124) - rw - 70, 14)
	for i, tl in tiles do
		tl.btn.Position = UDim2.fromOffset((i - 1) * (G.tw + G.gap), G.hh + 6)
		tl.btn.Size = UDim2.fromOffset(G.tw, G.th)
		local pad = if sm then 6 else 8
		tl.lab.Position = UDim2.fromOffset(pad + 2, pad - 2); tl.lab.Size = UDim2.fromOffset(G.tw - pad * 2, 12)
		tl.lab.TextSize = if sm then 9 else 10
		local nh = if sm then 14 else 18
		tl.vp.Position = UDim2.fromOffset(pad, pad + 12); tl.vp.Size = UDim2.fromOffset(G.tw - pad * 2, G.th - pad * 2 - 12 - nh)
		tl.name.Position = UDim2.fromOffset(pad + 2, G.th - pad - nh); tl.name.Size = UDim2.fromOffset(G.tw - pad * 2 - 4, nh)
		local c = tl.name:FindFirstChildOfClass("UITextSizeConstraint")
		if c then c.MaxTextSize = if sm then 11 else 13 end
	end
	gridLayout.CellSize = UDim2.fromOffset(G.cw, G.ch)
end

-- ---------------------------------------------------------------- drawing
local function slotOf(i: number): string return Roster.SLOTS[i] end
local function current(slot: string): string?
	local i = table.find(Roster.SLOTS, slot)
	return if i then picks()[i] else nil
end
local function alive(): boolean
	local hum = me.Character and me.Character:FindFirstChildOfClass("Humanoid")
	return hum ~= nil and hum.Health > 0
end

-- the ticks: ReadyTeams = per team, "1" a player locked in, "0" one not ("1,0|0")
local function drawTicks()
	for _, c in ticks:GetChildren() do if c:IsA("Frame") then c:Destroy() end end
	for _, c in ticks:GetChildren() do if c:IsA("TextLabel") then c:Destroy() end end
	local board = me:GetAttribute("ReadyTeams")
	if type(board) ~= "string" then return end
	-- (27 Nov: words, not ticks: the critic read the ticks as unlabelled lights)
	local inN, allN = 0, 0
	for _, part in string.split(board, "|") do
		for _, mark in string.split(part, ",") do if mark ~= "" then allN += 1; if mark == "1" then inN += 1 end end end
	end
	local words = text(ticks, "Count", ("%d of %d ready"):format(inN, allN), if S.small then 11 else 13, T.MUTED, K.SANS_BOLD)
	words.AutomaticSize = Enum.AutomaticSize.X; words.Size = UDim2.fromOffset(0, 14)
	if true then return end
	local sz = if S.small then 8 else 9
	for t, part in string.split(board, "|") do
		if part == "" then continue end
		local g = new("Frame", { Name = "Team" .. t, BackgroundTransparency = 1, AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 14), LayoutOrder = t }, ticks)
		new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, 4),
			SortOrder = Enum.SortOrder.LayoutOrder }, g)
		local bar = new("Frame", { Name = "Bar", BorderSizePixel = 0, BackgroundColor3 = TEAM_COLORS[t] or T.MUTED, Size = UDim2.fromOffset(3, 12), LayoutOrder = 0 }, g)
		T.corner(bar, 1)
		for i, mark in string.split(part, ",") do
			local on = mark == "1"
			local d = new("Frame", { Name = "Tick" .. i, BorderSizePixel = 0, BackgroundColor3 = T.TEXT, BackgroundTransparency = if on then 0 else 1,
				Size = UDim2.fromOffset(sz, sz), LayoutOrder = i }, g)
			T.corner(d, 2)
			new("UIStroke", { Color = if on then T.TEXT else T.MUTED, Transparency = if on then 0.2 else 0.3, Thickness = 1 }, d)
		end
	end
end
local function drawReady()
	local r = isReady()
	readyB.Text = if r then "LOCKED IN" else "READY"
	readyKey.Text = string.upper(Binds.label("ready")) -- (round 8: capitals, like every other cap)
	readyKey.Visible = not r and not touch() and readyKey.Text ~= ""
	readyB.BackgroundColor3 = if r then T.CARD else K.B.BUTTER
	readyB.TextColor3 = if r then T.MUTED else K.B.INK
	readySt.Transparency = 1
	readyB.BackgroundTransparency = if S.readying then 0.4 else 0
	for _, tl in tiles do tl.btn.BackgroundTransparency = if r then 0.4 else T.BG_A end
end

local function drawTiles()
	local cur = picks()
	for i, tl in tiles do
		local wid = cur[i]
		local e = wid and Roster.byId[wid]
		tl.name.Text = if e then e.name else "-"
		local on = S.tray == tl.slot
		if wid and e then
			task.defer(function()
				pcall(GunPreview.put, tl.vp, tl.cam, wid)
				-- (27 Nov: a flat silhouette, the loadout's icon family: white parts lit only by a white ambient)
				tl.vp.Ambient = Color3.new(1, 1, 1); tl.vp.LightColor = Color3.new(0, 0, 0); tl.vp.BackgroundTransparency = 1
				for _, d in tl.vp:GetDescendants() do
					if d:IsA("BasePart") then d.Color = Color3.new(1, 1, 1); d.Material = Enum.Material.SmoothPlastic; if d:IsA("MeshPart") then d.TextureID = "" end
					elseif d:IsA("Decal") or d:IsA("Texture") or d:IsA("SurfaceAppearance") then d:Destroy() end
				end
				-- (round 9: one scale for every slot, the loadout's: the room a long rifle needs, a gadget closer; a pistol filled
				-- its tile like the rifle did)
				local m = tl.vp:FindFirstChildWhichIsA("Model")
				local a = tl.vp.AbsoluteSize
				if m and a.Y > 0 then
					local cf, sz = m:GetBoundingBox()
					local asp = a.X / a.Y
					-- (round 10: by class, as the loadout's rows: the preview models are all about 6 studs)
					local classK = ({ primary = 1, secondary = 0.6, melee = 0.95, utility = 0.5 } :: { [string]: number })[tl.slot] or 1
					local r = math.max(math.max(sz.X, sz.Z) / 2 / asp, sz.Y / 2) * 1.1 / classK
					local dist = r / math.tan(math.rad(tl.cam.FieldOfView / 2))
					tl.cam.CFrame = CFrame.lookAt(cf.Position - tl.cam.CFrame.LookVector * dist, cf.Position)
				end
			end)
		end
		tl.vp.ImageColor3 = if on then K.B.INK else Color3.new(1, 1, 1)
		tl.st.Transparency = 1
		tl.btn.BackgroundColor3 = if on then K.B.WHITE else T.BG
		tl.lab.TextColor3 = if on then Color3.fromRGB(96, 96, 96) else T.MUTED
		tl.name.TextColor3 = if on then K.B.INK else T.TEXT
		local cut = tl.btn:FindFirstChild("Cut") or K.cut(tl.btn, 10, T.BG)
		cut.Visible = on
	end
end

local ask: (string, string) -> ()
local function drawTray()
	local slot = S.tray
	if not slot then tray.Visible = false; return end
	local list = choices(slot)
	if cardsFor ~= slot then
		cardsFor = slot
		for _, c in cards do c.btn:Destroy() end
		table.clear(cards)
		for i, e in list do
			local btn = new("TextButton", { Name = e.id, Text = "", AutoButtonColor = false, BorderSizePixel = 0, BackgroundColor3 = T.CARD,
				LayoutOrder = i }, grid)
			T.corner(btn, 5)
			local st = T.edge(btn)
			local vp, cam = GunPreview.viewport(btn, { Name = "Picture", Position = UDim2.fromOffset(3, 3), Size = UDim2.new(1, -6, 1, -21) })
			local nm = text(btn, "Name", string.upper(e.name), 11, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Center)
			nm.AnchorPoint = Vector2.new(0, 1); nm.Position = UDim2.new(0, 4, 1, -3); nm.Size = UDim2.new(1, -8, 0, 14)
			nm.TextScaled = true
			new("UITextSizeConstraint", { MaxTextSize = 11, MinTextSize = 7 }, nm)
			-- (LEVEL n on a locked one, ROBUX on a Robux one: Unlocks)
			local lk = text(btn, "Lock", "", 9, T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Center)
			lk.Position = UDim2.fromOffset(3, 3); lk.Size = UDim2.new(1, -6, 0, 12); lk.ZIndex = 3
			btn.Activated:Connect(function() ask(slot, e.id) end)
			btn.MouseEnter:Connect(function() S.hover = e.id end)
			btn.MouseLeave:Connect(function() if S.hover == e.id then S.hover = nil end end)
			table.insert(cards, { id = e.id, btn = btn, st = st, vp = vp, cam = cam, lk = lk })
		end
	end
	-- its size: as many columns as fit (7 at most), rows under them
	local n = #cards
	local cols = math.max(1, math.min(G.cols, n))
	local rows = math.max(1, math.ceil(n / cols))
	local pad = if S.small then 8 else 10
	local gw = cols * G.cw + (cols - 1) * 6
	local gh = rows * G.ch + (rows - 1) * 6
	local fh = if S.small then 24 else 30
	local w = math.max(gw + pad * 2, 260)
	local h = pad + gh + 8 + fh + pad
	tray.Size = UDim2.fromOffset(w, h)
	grid.Position = UDim2.fromOffset(math.floor((w - gw) / 2), pad); grid.Size = UDim2.fromOffset(gw, gh)
	if S.small then
		tray.AnchorPoint = Vector2.new(0.5, 0)
		tray.Position = UDim2.new(0.5, 0, 0, 62 + G.hh + 6 + G.th + 6)
	else
		tray.AnchorPoint = Vector2.new(0.5, 1)
		tray.Position = UDim2.new(0.5, 0, 1, -100 - (G.hh + 6 + G.th) - 8)
	end
	foot.Position = UDim2.fromOffset(pad + 2, pad + gh + 8); foot.Size = UDim2.fromOffset(w - pad * 2 - 96, fh)
	foot.TextYAlignment = Enum.TextYAlignment.Center
	foot.Text = S.note or (if alive() then "Picks go in your hands now" else "You spawn with your picks next round")
	foot.TextColor3 = if S.note then K.B.BUTTER else T.MUTED
	done.AnchorPoint = Vector2.new(1, 0); done.Position = UDim2.fromOffset(w - pad, pad + gh + 8); done.Size = UDim2.fromOffset(84, fh)
	done.Text = "DONE"
	local cur = current(slot)
	for _, c in cards do
		local on = c.id == cur
		c.st.Color = if on then T.ACCENT else Color3.new(1, 1, 1)
		c.st.Transparency = if on then 0.15 else 0.9
		c.btn.BackgroundColor3 = if on then T.CARD_HI else T.CARD
		local okU, whyU = Unlocks.forPlayer(me, c.id)
		c.lk.Text = if not okU then (whyU or "LOCKED") elseif Unlocks.robux(c.id) then (if Unlocks.robuxFree() then "ROBUX · FREE" else "ROBUX") else ""
		c.lk.TextColor3 = if okU then T.MUTED else T.TEXT
		c.vp.ImageTransparency = if okU then 0 else 0.65
		c.btn.BackgroundTransparency = if S.asking == c.id then 0.45 elseif not okU then 0.5 else 0
		task.defer(GunPreview.put, c.vp, c.cam, c.id)
	end
	tray.Visible = true
end

local function draw()
	if not S.shown then return end
	drawTiles()
	drawTray()
	drawTicks()
	drawReady()
end

ask = function(slot: string, wid: string)
	if S.asking then return end
	if current(slot) == wid then return end
	local okU, whyU = Unlocks.forPlayer(me, wid)
	if not okU then
		S.note = if whyU == "ROBUX" then "a robux weapon" else string.lower(whyU or "locked") .. " unlocks it"
		draw()
		return
	end
	S.asking = wid
	draw()
	task.spawn(function()
		local ok, r = pcall(function() return Remote:InvokeServer("pick", slot, wid) end)
		S.asking = nil
		if not ok or type(r) ~= "table" then S.note = "no answer, try again"
		elseif not r.ok then S.note = if type(r.why) == "string" then r.why else "refused"
		else S.note = nil end
		me:SetAttribute("MatchLoadoutResult", if ok and type(r) == "table" then (if r.ok then "ok" else tostring(r.why)) else "error")
		draw()
	end)
end

setTray = function(slot: string?)
	if slot and (not windowLeft() or isReady()) then return end -- (locked in: your set is fixed for the round)
	S.tray = slot
	S.note = nil
	MenuCursor.set("matchloadout", slot ~= nil, function() return S.tray ~= nil end)
	draw()
end

-- the ready key, sunk while the window is open (Space is jump the rest of the time). a mouse button bind is left to
-- the Keys path below
local readyUp: () -> ()
local sinking = false
local function sinkReady(on: boolean)
	if on == sinking then return end
	sinking = on
	if on then
		local codes = {}
		for _, n in Binds.get("ready") do
			if n ~= "" and string.sub(n, 1, 11) ~= "MouseButton" then
				local ok, kc = pcall(function() return (Enum.KeyCode :: any)[n] end)
				if ok and kc then table.insert(codes, kc) end
			end
		end
		if #codes == 0 then sinking = false; return end
		ContextActionService:BindActionAtPriority("JankReadyKey", function(_, state: Enum.UserInputState, _io: InputObject)
			if UIS:GetFocusedTextBox() then return Enum.ContextActionResult.Pass end
			if state == Enum.UserInputState.Begin then readyUp() end
			return Enum.ContextActionResult.Sink
		end, false, 3500, table.unpack(codes))
	else
		pcall(function() ContextActionService:UnbindAction("JankReadyKey") end)
		-- (a jump asked for while you were held doesn't go off as the hold lets go)
		local hum = me.Character and me.Character:FindFirstChildOfClass("Humanoid")
		if hum then hum.Jump = false end
	end
end

local function setShown(v: boolean)
	if v == S.shown then return end
	S.shown = v
	root.Visible = v
	sinkReady(v)
	if v then
		S.total = math.max(windowLeft() or 1, 1)
		layout()
		draw()
	else
		setTray(nil)
		for _, tl in tiles do GunPreview.clear(tl.vp) end
		for _, c in cards do c.btn:Destroy() end
		table.clear(cards)
		cardsFor = ""
	end
end

-- READY: lock your set in for the round (the server's MatchReady: everyone in, the round goes early)
local readyR: RemoteFunction? = nil
task.spawn(function()
	local r = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("MatchReady", 60)
	if r and r:IsA("RemoteFunction") then readyR = r end
end)
readyUp = function()
	if isReady() or S.readying or not windowLeft() or not readyR then return end
	S.readying = true
	setTray(nil)
	draw()
	task.spawn(function()
		local ok, r = pcall(function() return (readyR :: RemoteFunction):InvokeServer() end)
		S.readying = false
		if not ok or type(r) ~= "table" or not r.ok then S.note = if ok and type(r) == "table" and type(r.why) == "string" then r.why else "no answer, try again" end
		me:SetAttribute("MatchLoadoutResult", if ok and type(r) == "table" and r.ok then "ready" else "not ready")
		draw()
	end)
end
readyB.Activated:Connect(readyUp)

-- ---------------------------------------------------------------- keys
Keys.began(function(io: any, gp: boolean)
	if UIS:GetFocusedTextBox() or not S.shown then return end
	if Binds.is("ready", io) and not gp then
		readyUp()
	elseif Binds.is("loadout", io) then
		if gp and not S.tray then return end
		setTray(if S.tray then nil else "primary")
	elseif S.tray and not gp then
		if io.KeyCode == Enum.KeyCode.Escape then setTray(nil); return end
		local n = ({ [Enum.KeyCode.One] = 1, [Enum.KeyCode.Two] = 2, [Enum.KeyCode.Three] = 3, [Enum.KeyCode.Four] = 4 } :: any)[io.KeyCode]
		if n and slotOf(n) then setTray(slotOf(n)) end
	end
end)

me:GetAttributeChangedSignal("LoadoutNext"):Connect(function() if S.shown then draw() end end)
me:GetAttributeChangedSignal("ReadyTeams"):Connect(function() if S.shown then drawTicks() end end)
me:GetAttributeChangedSignal("LoadoutReady"):Connect(function()
	if isReady() then setTray(nil) end
	if S.shown then draw() end
end)
for _, a in { "Wraps", "Hats", "Skins", "Level", "WeaponsKept", "UnlockAll" } do
	me:GetAttributeChangedSignal(a):Connect(function() if S.shown then draw() end end)
end
me.CharacterAdded:Connect(function() if S.shown then task.defer(draw) end end)
workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(function() if S.shown then layout(); draw() end end)

-- shown or not: checked on every change that can shut it, and every frame (Heartbeat runs even when nothing is drawn)
local function check()
	setShown(windowLeft() ~= nil and me:GetAttribute("Zone") == "match" and me:GetAttribute("FinisherT") == nil)
end
for _, a in { "LoadoutWindow", "RoundEnds", "Zone", "FinisherT" } do me:GetAttributeChangedSignal(a):Connect(check) end
RunService.Heartbeat:Connect(check)
task.spawn(function()
	local r = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Round", 60)
	if r and r:IsA("RemoteEvent") then
		r.OnClientEvent:Connect(function(m: any) if type(m) == "table" and m.start then setShown(false) end end)
	end
end)

local t0 = os.clock()
RunService.RenderStepped:Connect(function()
	check()
	local left = windowLeft()
	if not S.shown or not left then return end
	if left > S.total then S.total = left end
	local s = tostring(math.ceil(left)) .. " s" -- (with its unit: a bare number read as an unlabelled one)
	if secs.Text ~= s then secs.Text = s end
	fill.Size = UDim2.fromScale(math.clamp(left / S.total, 0, 1), 1)
	local subT = "" -- (the READY button sits there now)
	if sub.Text ~= subT then sub.Text = subT end
	if S.small ~= small() then layout(); draw() end
	-- (the pictures turn a little: the slots slowly, the weapon under the mouse in the picker a full turn)
	local t = os.clock() - t0
	for i, tl in tiles do GunPreview.turn(tl.vp, math.sin(t * 0.7 + i * 1.3) * 0.35) end
	for _, c in cards do
		if c.id == S.hover then GunPreview.turn(c.vp, t * 1.6) end
	end
end)

-- ------------------------------------------------------------------ test hook
me:GetAttributeChangedSignal("MatchLoadoutTest"):Connect(function()
	local v = me:GetAttribute("MatchLoadoutTest")
	if type(v) ~= "string" or v == "" then return end
	me:SetAttribute("MatchLoadoutTest", nil)
	local cmd, a, b = string.match(v, "^(%a+):?([^:]*):?(.*)$")
	if cmd == "open" then setTray("primary"); me:SetAttribute("MatchLoadoutResult", if S.tray then "open" else "shut")
	elseif cmd == "ready" then readyUp()
	elseif cmd == "slot" then setTray(if a ~= "" then a else "primary")
	elseif cmd == "close" then setTray(nil)
	elseif cmd == "pick" then ask(a or "", b or "")
	elseif cmd == "fake" then
		local w, h = string.match(a or "", "^(%d+)x(%d+)$")
		S.fake = if w then Vector2.new(tonumber(w) :: number, tonumber(h) :: number) else nil
		if S.shown then layout(); draw() end
	elseif cmd == "real" then
		S.fake = nil
		if S.shown then layout(); draw() end
	end
end)
