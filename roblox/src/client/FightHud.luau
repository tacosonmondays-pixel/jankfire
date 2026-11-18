--!strict
-- the fighting HUD (Theme.luau has the look; Hud.luau the speed readout, the announcer line and the controls line):
-- crosshair + the parry ring, the hit marker (white ticks, red on a headshot), floating damage numbers, the hurt rim
-- and screen flashes, health and ammo, the top line (mode, round, score, clock), the kill feed (a chip in each weapon's
-- colour), the death line, the end screen and the scope
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Items = require(Shared:WaitForChild("Items")) -- (the utility slot: a frag kill in the feed, G on the controls line)

local T = require(script.Parent:WaitForChild("Theme"))
local Settings = require(script.Parent:WaitForChild("Settings")) :: any -- (Settings > CROSSHAIR / HUD: what's shown and how)
local XH = require(script.Parent:WaitForChild("Crosshair")) :: any
local WHITE, BLACK = Color3.new(1, 1, 1), Color3.new(0, 0, 0)
local me = Players.LocalPlayer

local H = {}
local gui = Instance.new("ScreenGui")
gui.Name = "JankfireFight"; gui.ResetOnSpawn = false; gui.IgnoreGuiInset = true; gui.DisplayOrder = 2
gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling -- (a card's text is drawn on its card, whatever the card's own ZIndex)
gui.Parent = me:WaitForChild("PlayerGui")

-- put a label where it goes
local function at(o: GuiObject, pos: UDim2, size: UDim2) o.Position = pos; o.Size = size end
-- the plates live in here and grow with the screen (Theme.scaled); the crosshair, hit marker, hurt rim, flash and
-- scope stay straight in the gui, pixel for pixel
local hud = T.scaled(gui)

-- ---------------------------------------------------------------- crosshair, parry ring, hit marker
local cross = Instance.new("Frame")
cross.Name = "Crosshair"; cross.BackgroundTransparency = 1; cross.AnchorPoint = Vector2.new(0.5, 0.5)
cross.Position = UDim2.fromScale(0.5, 0.5); cross.Size = UDim2.fromOffset(40, 40); cross.Parent = gui
-- (its pieces are the player's own design, Settings > CROSSHAIR: Crosshair.luau draws them here every frame. the
-- defaults are the four white bars with a dark outline it always had)
XH.draw(cross, XH.opts(), 0, 0)
-- a dot sight's reticle (the Redline aimed): a small red dot with a soft rim, a little under 1% of the screen's height
local redDot = Instance.new("Frame")
redDot.Name = "RedDot"; redDot.AnchorPoint = Vector2.new(0.5, 0.5); redDot.Position = UDim2.fromScale(0.5, 0.5)
redDot.SizeConstraint = Enum.SizeConstraint.RelativeYY; redDot.Size = UDim2.fromScale(0.0085, 0.0085)
redDot.BackgroundColor3 = Color3.fromRGB(255, 52, 52); redDot.BorderSizePixel = 0; redDot.Visible = false
local rdc = Instance.new("UICorner"); rdc.CornerRadius = UDim.new(0.5, 0); rdc.Parent = redDot
local redGlow = Instance.new("UIStroke"); redGlow.Thickness = 2; redGlow.Color = Color3.fromRGB(255, 120, 110); redGlow.Transparency = 1; redGlow.Parent = redDot
redDot.Parent = gui
local ring = Instance.new("Frame")
ring.Name = "ParryRing"; ring.AnchorPoint = Vector2.new(0.5, 0.5); ring.Position = UDim2.fromScale(0.5, 0.5)
ring.Size = UDim2.fromOffset(54, 54); ring.BackgroundTransparency = 1; ring.Visible = false; ring.Parent = gui
local rc = Instance.new("UICorner"); rc.CornerRadius = UDim.new(0.5, 0); rc.Parent = ring
local rs = Instance.new("UIStroke"); rs.Thickness = 2; rs.Color = T.ACCENT; rs.Parent = ring
local rg = Instance.new("UIGradient"); rg.Parent = rs

-- the hit marker: four short ticks on the diagonals, pointing in at the crosshair
local marker = T.new("Frame", {
	Name = "HitMarker", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
	Size = UDim2.fromOffset(26, 26), Visible = false,
}, gui)
local ticks: { Frame } = {}
for _, d in { Vector2.new(-1, -1), Vector2.new(1, -1), Vector2.new(-1, 1), Vector2.new(1, 1) } do
	local t = T.new("Frame", {
		Name = "Tick", BorderSizePixel = 0, BackgroundColor3 = WHITE, AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5 + d.X * 0.33, 0.5 + d.Y * 0.33), Size = UDim2.new(0, 2, 0.36, 0),
		Rotation = if d.X * d.Y > 0 then -45 else 45,
	}, marker)
	T.new("UIStroke", { Thickness = 1, Color = BLACK, Transparency = 0.4 }, t)
	table.insert(ticks, t)
end

local markTok = 0
function H.hit(head: boolean)
	if Settings.get("hud.hits") == false then return end -- (Settings > HUD: HIT MARKERS)
	markTok += 1
	local my = markTok
	local s = if head then 34 else 26
	marker.Size = UDim2.fromOffset(s, s)
	for _, t in ticks do t.BackgroundColor3 = if head then T.DANGER else WHITE end
	marker.Visible = true
	task.delay(0.18, function() if my == markTok then marker.Visible = false end end)
end

-- the parry ring: full while the guard is open, draining over the cooldown, a blink when it's ready again
function H.parryRing(state: string, k: number)
	ring.Visible = state ~= "hidden"
	if state == "open" then rs.Color = T.ACCENT; rs.Transparency = 0; rg.Transparency = NumberSequence.new(0)
	elseif state == "drain" then
		rs.Color = T.MUTED; rs.Transparency = 0.3
		local kk = math.clamp(k, 0.001, 0.999)
		rg.Rotation = -90
		rg.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(kk, 0), NumberSequenceKeypoint.new(math.min(0.9999, kk + 0.001), 1), NumberSequenceKeypoint.new(1, 1) })
	elseif state == "ready" then rs.Color = Color3.new(1, 1, 1); rs.Transparency = 0; rg.Transparency = NumberSequence.new(0) end
end

-- ---------------------------------------------------------------- damage numbers (over the victim, in the world)
function H.dmgNum(at: Vector3, amount: number, head: boolean)
	if Settings.get("hud.dmg") == false then return end -- (Settings > HUD: DAMAGE NUMBERS)
	local a = Instance.new("Attachment")
	a.WorldPosition = at + Vector3.new(math.random() - 0.5, 1, math.random() - 0.5)
	a.Parent = workspace.Terrain
	local bb = Instance.new("BillboardGui")
	bb.Size = UDim2.fromOffset(90, 40); bb.AlwaysOnTop = true; bb.LightInfluence = 0; bb.Adornee = a; bb.Parent = a
	-- (a headshot's number is red and a size up)
	local t = T.text(bb, "N", tostring(amount), if head then 28 else 22, if head then T.DANGER else T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Center)
	t.Size = UDim2.fromScale(1, 1); t.TextStrokeTransparency = 0.3
	TweenService:Create(a, TweenInfo.new(0.9, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { WorldPosition = a.WorldPosition + Vector3.new(0, 2.4, 0) }):Play()
	TweenService:Create(t, TweenInfo.new(0.9, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { TextTransparency = 1, TextStrokeTransparency = 1 }):Play()
	task.delay(0.95, function() a:Destroy() end)
end

-- ---------------------------------------------------------------- hurt vignette + screen flash
-- the hurt rim: four soft red bands, one along each edge of the screen, fading to nothing towards the middle
local vig = T.new("Frame", { Name = "Hurt", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, gui)
local rims: { Frame } = {}
for _, r in {
	{ UDim2.fromScale(0, 0), UDim2.fromScale(1, 0.24), 90 }, { UDim2.fromScale(0, 0.76), UDim2.fromScale(1, 0.24), -90 },
	{ UDim2.fromScale(0, 0), UDim2.fromScale(0.17, 1), 0 }, { UDim2.fromScale(0.83, 0), UDim2.fromScale(0.17, 1), 180 },
} :: { { any } } do
	local f = T.new("Frame", { Name = "Rim", BorderSizePixel = 0, BackgroundColor3 = T.DANGER, BackgroundTransparency = 1, Position = r[1], Size = r[2] }, vig)
	T.new("UIGradient", {
		Rotation = r[3],
		Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(0.45, 0.75), NumberSequenceKeypoint.new(1, 1) }),
	}, f)
	table.insert(rims, f)
end
local hurtA = 0
local lowA = 0 -- (a faint steady rim while you are at 25 health or under: H.hp sets it)
function H.hurt(amount: number) hurtA = math.min(0.85, hurtA + amount / 40) end
local flash = Instance.new("Frame")
flash.Name = "Flash"; flash.Size = UDim2.fromScale(1, 1); flash.BackgroundColor3 = Color3.new(1, 1, 1); flash.BackgroundTransparency = 1
flash.BorderSizePixel = 0; flash.ZIndex = 10; flash.Parent = gui
function H.flash(op: number, dur: number, color: Color3?)
	flash.BackgroundColor3 = color or Color3.new(1, 1, 1)
	flash.BackgroundTransparency = 1 - op
	TweenService:Create(flash, TweenInfo.new(dur), { BackgroundTransparency = 1 }):Play()
end

-- ---------------------------------------------------------------- HP, ammo, weapon
-- health, bottom left: the number, and a thin bar that goes white > amber > red as it empties
local hpPlate = T.plate(hud, "Hp", UDim2.new(0, 24, 1, -88), UDim2.fromOffset(212, 64))
local hpEdge = hpPlate:FindFirstChildOfClass("UIStroke") :: UIStroke
local hpText = T.text(hpPlate, "Value", "100", 34, T.TEXT, T.FONT_HEAVY)
at(hpText, UDim2.fromOffset(16, 7), UDim2.new(1, -32, 0, 34))
hpText.RichText = true -- (the number, then a small grey HP right beside it)
local hpShown = -1
local hpTrack = T.new("Frame", { Name = "Track", BorderSizePixel = 0, BackgroundColor3 = T.TRACK, Position = UDim2.new(0, 16, 1, -19), Size = UDim2.new(1, -32, 0, 6) }, hpPlate)
T.corner(hpTrack, 3)
local hpBar = T.new("Frame", { Name = "Bar", BorderSizePixel = 0, BackgroundColor3 = T.TEXT, Size = UDim2.fromScale(1, 1) }, hpTrack)
T.corner(hpBar, 3)
-- weapon and ammo, bottom right: a chip in the weapon's colour, its name, what it's doing; the count on the right
local ammoPlate = T.plate(hud, "Ammo", UDim2.new(1, -256, 1, -88), UDim2.fromOffset(232, 64))
local wChip = T.new("Frame", { Name = "Chip", BorderSizePixel = 0, BackgroundColor3 = T.MUTED, Position = UDim2.fromOffset(16, 14), Size = UDim2.fromOffset(3, 36) }, ammoPlate)
T.corner(wChip, 2)
local wName = T.text(ammoPlate, "Weapon", "", 16, T.TEXT, T.FONT_BOLD)
at(wName, UDim2.fromOffset(28, 13), UDim2.fromOffset(110, 20))
wName.TextTruncate = Enum.TextTruncate.AtEnd
local wSub = T.text(ammoPlate, "State", "", 13, T.MUTED, T.FONT_BOLD)
at(wSub, UDim2.fromOffset(28, 35), UDim2.fromOffset(190, 16))
local ammoText = T.text(ammoPlate, "Count", "", 34, T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Right)
at(ammoText, UDim2.new(1, -122, 0, 6), UDim2.fromOffset(106, 38))
ammoText.RichText = true
function H.hp(hp: number)
	local v = math.max(0, math.ceil(hp))
	if v ~= hpShown then
		hpShown = v
		hpText.Text = ('%d<font size="14" color="%s">  HP</font>'):format(v, T.hex(T.MUTED))
	end
	local low = hp <= 25 -- (nearly dead: the whole plate turns, not just the number, and the screen's rim glows faintly)
	lowA = if low and hp > 0 then 0.3 else 0
	hpText.TextColor3 = if low then T.DANGER else T.TEXT
	hpPlate.BackgroundColor3 = if low then Color3.fromRGB(42, 18, 21) else T.BG
	hpEdge.Color = if low then T.DANGER else T.EDGE
	hpEdge.Transparency = if low then 0.35 else T.EDGE_A
	hpBar.Size = UDim2.fromScale(math.clamp(hp / (tonumber(game:GetService("Players").LocalPlayer:GetAttribute("HpMax")) or 100), 0, 1), 1) -- (HpMax: infection's 200 HP zombies)
	hpBar.BackgroundColor3 = if hp > 50 then T.TEXT elseif hp > 25 then T.ACCENT else T.DANGER
end
function H.weapon(wid: string, mag: number?, reloading: boolean, kat: number, note: string?)
	local w = Weapons.list[wid]
	if not w then return end
	local count, sub, subColor, countColor = "", "", T.MUTED, T.TEXT
	if note then -- (the Shredder: its heat instead of ammo; HOLSTERED in the hub)
		sub = note
		if note == "OVERHEATED" then subColor = T.DANGER end
	elseif w.kind == "melee" or w.mag == nil then -- (and a weapon with no magazine, the Taser: no count)
		-- (right click: the katana parries, the knife stabs, the claw does nothing)
		sub = if kat > 0 then (if kat == 1 then "%d kill · %.1f m" else "%d kills · %.1f m"):format(kat, Weapons.reach(w, kat) / Weapons.S)
			elseif w.heavy then "RMB stab" elseif w.id == "katana" then "RMB parry" elseif w.dash then "RMB dash" else ""
	else
		count = ('%d<font size="15" color="%s">  / %d</font>'):format(mag or 0, T.hex(T.MUTED), w.mag or 0)
		if reloading then sub = "RELOADING"; subColor = T.ACCENT; countColor = T.DIM
		elseif (mag or 0) <= 0 then countColor = T.DANGER end
	end
	-- (a classic mode's spoon look: the knife is the Spoon, Modes.luau's SpoonLook)
	local shown = if wid == "knife" and game:GetService("Players").LocalPlayer:GetAttribute("SpoonLook") then "Spoon" else w.name
	if wName.Text ~= shown then wName.Text = shown end
	wChip.BackgroundColor3 = w.color
	if ammoText.Text ~= count then ammoText.Text = count end
	ammoText.TextColor3 = countColor
	if wSub.Text ~= sub then wSub.Text = sub end
	wSub.TextColor3 = subColor
end

-- ---------------------------------------------------------------- clock + kill target
-- where you are (hub, training, playground): low in the middle, just above the controls line (Hud's "Keys"). it used
-- to sit top centre, then top left: both covered one of the hub's hanging signs in the first view you get. down here
-- it is over the floor, and the top centre is the match scoreboard's alone
local top = T.new("TextLabel", {
	Name = "Round", AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, -62), Size = UDim2.fromOffset(0, 30),
	AutomaticSize = Enum.AutomaticSize.X, BackgroundColor3 = T.BG, BackgroundTransparency = T.BG_A, BorderSizePixel = 0,
	FontFace = T.FONT_BOLD, TextSize = 15, TextColor3 = T.TEXT, RichText = true, Text = "", Visible = false,
}, hud)
T.corner(top)
local topEdge = T.edge(top)
-- (16 Nov, owner: "can we hide this?") the where-you-are line is hidden. it shows for a few seconds when you come
-- into a place (the hub, training, the playground) and fades out. a match's scoreboard stays up all match
local TOP_HOLD = 3
local topTok = 0
local function flashTop()
	topTok += 1
	local my = topTok
	if not top.Visible then top.TextTransparency = 1; top.BackgroundTransparency = 1; topEdge.Transparency = 1 end
	top.Visible = true
	T.tween(top, 0.2, { TextTransparency = 0, BackgroundTransparency = T.BG_A })
	T.tween(topEdge, 0.2, { Transparency = T.EDGE_A })
	task.delay(TOP_HOLD, function()
		if my ~= topTok then return end
		T.tween(top, 0.6, { TextTransparency = 1, BackgroundTransparency = 1 })
		T.tween(topEdge, 0.6, { Transparency = 1 })
		task.delay(0.65, function() if my == topTok then top.Visible = false end end)
	end)
end
T.new("UIPadding", { PaddingLeft = UDim.new(0, 16), PaddingRight = UDim.new(0, 16) }, top)
-- a match's scoreboard, in the same spot: mode and round on the left, the score big in the middle (each team's wins in
-- its own colour), the clock on the right. the two sides are the same width, so the score sits on the screen's centre
local score = T.new("Frame", {
	Name = "Score", AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0, 12), Size = UDim2.fromOffset(0, 46),
	AutomaticSize = Enum.AutomaticSize.X, BackgroundColor3 = T.BG, BackgroundTransparency = 0.14, BorderSizePixel = 0, Visible = false,
}, hud)
T.corner(score); T.edge(score)
T.new("UIListLayout", {
	FillDirection = Enum.FillDirection.Horizontal, VerticalAlignment = Enum.VerticalAlignment.Center, SortOrder = Enum.SortOrder.LayoutOrder,
}, score)
-- three cells, each with its words in its middle: mode and round | the score | the clock. a hairline between them
local function scoreCell(order: number, name: string, size: number, color: Color3, font: Font, width: number): TextLabel
	local l = T.text(score, name, "", size, color, font, Enum.TextXAlignment.Center)
	l.LayoutOrder = order; l.Size = UDim2.new(0, width, 1, 0)
	if order < 5 then
		T.new("Frame", { Name = "Rule", LayoutOrder = order + 1, BorderSizePixel = 0, BackgroundColor3 = T.EDGE, BackgroundTransparency = 0.84, Size = UDim2.fromOffset(1, 22) }, score)
	end
	return l
end
local scoreMode = scoreCell(1, "Mode", 14, T.MUTED, T.FONT_BOLD, 156)
local scoreNum = scoreCell(3, "Wins", 28, T.TEXT, T.FONT_HEAVY, 0)
scoreNum.RichText = true; scoreNum.AutomaticSize = Enum.AutomaticSize.X
T.new("UIPadding", { PaddingLeft = UDim.new(0, 26), PaddingRight = UDim.new(0, 26) }, scoreNum)
local scoreClock = scoreCell(5, "Clock", 18, T.TEXT, T.FONT_BOLD, 156)
local lastScore = "" -- (the end screen shows it under the result)
local topRaw = ""
-- the top line in the hub (where you are) and in a match (mode, round, score, clock): RichText. a where-you-are line
-- ("HUB · weapons away · ...") gets its place in white and the rest quieter; a match's line ("MODE · ROUND n ·
-- score · clock", Matches.hudText + Arsenal's clock) is laid out as the scoreboard
function H.top(text: string)
	text = Settings.cbText(text) -- (the team colours, colour-blind safe if Settings > HUD says so)
	if topRaw == text then return end
	topRaw = text
	local parts = if string.find(text, "<font", 1, true) then string.split(text, " · ") else nil
	if parts and #parts >= 3 then
		scoreMode.Text = parts[1] .. "    " .. parts[2]
		scoreNum.Text = parts[3]; lastScore = parts[3]
		scoreClock.Text = parts[4] or ""
		score.Visible = true; top.Visible = false; topTok += 1
		return
	end
	score.Visible = false
	local cut = string.find(text, " · ", 1, true)
	if cut and not parts then
		top.Text = ('%s<font color="%s">    %s</font>'):format(string.sub(text, 1, cut - 1), T.hex(T.MUTED), string.sub(text, cut + #" · "))
	else
		top.Text = text
	end
	flashTop()
end
function H.round(target: number, left: number, myKills: number)
	local m, s = math.floor(math.max(0, left) / 60), math.floor(math.max(0, left)) % 60
	H.top(("first to %d · %d:%02d · you %d"):format(target, m, s, myKills))
end

-- ---------------------------------------------------------------- kill feed (top right, 6 lines, 7 s)
local feed = Instance.new("Frame")
feed.Name = "Feed"; feed.BackgroundTransparency = 1; feed.AnchorPoint = Vector2.new(1, 0); feed.Position = UDim2.new(1, -24, 0, 64)
feed.Size = UDim2.fromOffset(520, 6 * 34); feed.Parent = hud
local fl = Instance.new("UIListLayout"); fl.HorizontalAlignment = Enum.HorizontalAlignment.Right; fl.Padding = UDim.new(0, 4)
fl.SortOrder = Enum.SortOrder.LayoutOrder; fl.Parent = feed
local feedN = 0
-- a line: who  | weapon  who (your own name in amber). the weapon's colour is the small chip before its name
function H.feed(killer: string?, wid: string, victim: string, suffix: string?)
	if Settings.get("hud.feed") == false then return end -- (Settings > HUD: KILL FEED)
	feedN += 1
	local it = Items.list[wid]
	local w: any = Weapons.list[wid] or (if it then { name = it.name, color = it.feed or it.color } else nil)
	local row = T.new("Frame", {
		Name = "Line", LayoutOrder = feedN, BackgroundColor3 = T.BG, BackgroundTransparency = T.BG_A, BorderSizePixel = 0,
		AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 30),
	})
	T.corner(row, 4)
	T.new("UIPadding", { PaddingLeft = UDim.new(0, 10), PaddingRight = UDim.new(0, 10) }, row)
	T.new("UIListLayout", {
		FillDirection = Enum.FillDirection.Horizontal, VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, 8),
		SortOrder = Enum.SortOrder.LayoutOrder,
	}, row)
	local function cell(order: number, text: string, color: Color3, font: Font)
		local l = T.text(row, "Cell", text, 15, color, font)
		l.LayoutOrder = order; l.AutomaticSize = Enum.AutomaticSize.X; l.Size = UDim2.fromOffset(0, 30)
	end
	local function mine(name: string): boolean return name == me.DisplayName or name == me.Name end
	if killer then cell(1, killer, if mine(killer) then T.ACCENT else T.TEXT, T.FONT_BOLD) end
	if w then
		local chip = T.new("Frame", { Name = "Chip", LayoutOrder = 2, BorderSizePixel = 0, BackgroundColor3 = w.color, Size = UDim2.fromOffset(3, 15) }, row)
		T.corner(chip, 2)
		cell(3, w.name, T.SOFT, T.FONT)
	end
	cell(4, victim, if mine(victim) then T.ACCENT else T.TEXT, T.FONT_BOLD)
	if suffix then cell(5, suffix, T.SOFT, T.FONT) end
	row.Parent = feed
	local lines = {}
	for _, c in feed:GetChildren() do if c:IsA("Frame") then table.insert(lines, c) end end
	table.sort(lines, function(a, b) return a.LayoutOrder < b.LayoutOrder end)
	while #lines > 6 do (table.remove(lines, 1) :: Frame):Destroy() end
	task.delay(7, function() if row.Parent then row:Destroy() end end)
end

-- ---------------------------------------------------------------- death line
-- a band across the middle with a red bar at its left end: who got you in big white letters, how in small grey ones
local deathText = T.new("TextLabel", {
	Name = "Death", AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromScale(0.5, 0.58), Size = UDim2.fromOffset(0, 52),
	AutomaticSize = Enum.AutomaticSize.X, BackgroundColor3 = T.BG, BackgroundTransparency = 0.14, BorderSizePixel = 0,
	FontFace = T.FONT_BOLD, TextSize = 22, TextColor3 = T.TEXT, RichText = true, Text = "", Visible = false,
}, hud)
T.corner(deathText); T.edge(deathText)
T.new("UIPadding", { PaddingLeft = UDim.new(0, 30), PaddingRight = UDim.new(0, 26) }, deathText)
T.corner(T.new("Frame", { Name = "Bar", BorderSizePixel = 0, BackgroundColor3 = T.DANGER, Position = UDim2.new(0, -18, 0.5, -13), Size = UDim2.fromOffset(3, 26) }, deathText), 2)
local function esc(s: string): string return (s:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;")) end
function H.dead(text: string?)
	deathText.Visible = text ~= nil
	if not text then deathText.Text = ""; return end
	-- the words are Arsenal's and are not changed: "killed by NAME  (WEAPON)", "NAME knocked you into the smog  (WEAPON)"
	local function quiet(s: string): string return ('<font color="%s" size="15">%s</font>'):format(T.hex(T.MUTED), esc(s)) end
	local who, wpn = string.match(text, "^killed by (.-)  %((.+)%)$")
	if who then deathText.Text = quiet("killed by") .. "   " .. esc(who) .. "   " .. quiet(wpn); return end
	local who2, how, wpn2 = string.match(text, "^(.-) (knocked you into the smog)  %((.+)%)$")
	if who2 then deathText.Text = esc(who2) .. "   " .. quiet(how) .. "   " .. quiet(wpn2); return end
	deathText.Text = esc(text)
end

-- ---------------------------------------------------------------- end screen
-- a dimmed screen and one card: who won, the board as a table (place, player, kills, deaths; your row marked), what's next
local endShadow = T.new("Frame", { Name = "EndScrim", BackgroundColor3 = BLACK, BackgroundTransparency = 1, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), Visible = false, ZIndex = 4 }, hud)
local endPanel = T.new("Frame", {
	Name = "End", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(500, 420),
	BackgroundColor3 = T.BG, BackgroundTransparency = 0.05, BorderSizePixel = 0, Visible = false, ZIndex = 5,
}, hud)
T.corner(endPanel, 8); T.edge(endPanel)
local endScale = T.new("UIScale", {}, endPanel)
local MID = Enum.TextXAlignment.Center
local endKicker = T.text(endPanel, "Kicker", "MATCH OVER", 12, T.MUTED, T.FONT_BOLD, MID)
at(endKicker, UDim2.fromOffset(28, 24), UDim2.new(1, -56, 0, 14))
local endTitle = T.text(endPanel, "Title", "", 40, T.TEXT, T.FONT_TITLE, MID)
at(endTitle, UDim2.fromOffset(28, 44), UDim2.new(1, -56, 0, 48))
endTitle.TextScaled = true
T.new("UITextSizeConstraint", { MaxTextSize = 40, MinTextSize = 14 }, endTitle)
-- the final score under the result, each team's wins in its colour (H.top keeps it from the match line)
local endScore = T.text(endPanel, "Score", "", 26, T.TEXT, T.FONT_HEAVY, MID)
at(endScore, UDim2.fromOffset(28, 96), UDim2.new(1, -56, 0, 30))
endScore.RichText = true
local endRule = T.new("Frame", { Name = "Rule", BorderSizePixel = 0, BackgroundColor3 = T.ACCENT, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0, 136), Size = UDim2.fromOffset(44, 3) }, endPanel)
-- one row of the board (the heading uses it too): place, player, kills, deaths
local function cells(parent: Instance, texts: { string }, size: number, color: Color3, font: Font, nameColor: Color3?)
	local L, R = Enum.TextXAlignment.Left, Enum.TextXAlignment.Right
	for i, s in { { 14, 26, L }, { 44, 214, L }, { 262, 76, R }, { 346, 86, R } } :: { { any } } do
		local l = T.text(parent, "Cell" .. i, texts[i], size, if i == 2 and nameColor then nameColor else color, font, s[3])
		at(l, UDim2.fromOffset(s[1], 0), UDim2.new(0, s[2], 1, 0))
		l.TextTruncate = Enum.TextTruncate.AtEnd
	end
end
local endHead = T.new("Frame", { Name = "Head", BackgroundTransparency = 1, Position = UDim2.fromOffset(28, 156), Size = UDim2.new(1, -56, 0, 20) }, endPanel)
cells(endHead, { "#", "PLAYER", "KILLS", "DEATHS" }, 11, T.MUTED, T.FONT_BOLD)
local endList = T.new("Frame", { Name = "Board", BackgroundTransparency = 1, Position = UDim2.fromOffset(28, 180), Size = UDim2.new(1, -56, 0, 8 * 40) }, endPanel)
T.new("UIListLayout", { Padding = UDim.new(0, 2), SortOrder = Enum.SortOrder.LayoutOrder }, endList)
local endNext = T.text(endPanel, "Next", "", 14, T.MUTED, T.FONT, Enum.TextXAlignment.Center)
at(endNext, UDim2.new(0, 28, 1, -50), UDim2.new(1, -56, 0, 18))
-- the wait for what's next, as a thin bar that drains
local endTrack = T.new("Frame", { Name = "Wait", BorderSizePixel = 0, BackgroundColor3 = T.TRACK, Position = UDim2.new(0, 28, 1, -22), Size = UDim2.new(1, -56, 0, 3) }, endPanel)
T.corner(endTrack, 2)
local endFill = T.new("Frame", { Name = "Fill", BorderSizePixel = 0, BackgroundColor3 = T.MUTED, Size = UDim2.fromScale(1, 1) }, endTrack)
T.corner(endFill, 2)
local endTok = 0
function H.endScreen(winner: string?, iWon: boolean, board: { { any } }, nextIn: number, nextLabel: string?)
	endTok += 1
	local my = endTok
	for _, c in endList:GetChildren() do if c:IsA("Frame") then c:Destroy() end end
	endTitle.Text = if iWon then "YOU WIN" elseif winner then string.upper(winner .. " wins") else "NOBODY WINS (no kills, no glory)"
	endTitle.TextColor3 = if iWon then T.ACCENT else T.TEXT
	endScore.Text = lastScore
	endRule.BackgroundColor3 = if iWon then T.ACCENT else T.DIM
	local n = 0
	for i, r in board do
		if i > 8 then break end
		n += 1
		local mine = r[4] == me.UserId
		local row = T.new("Frame", {
			Name = "Row", LayoutOrder = i, BorderSizePixel = 0, BackgroundColor3 = if mine then T.CARD_HI else T.CARD,
			BackgroundTransparency = if mine then 0 else 0.4, Size = UDim2.new(1, 0, 0, 38),
		}, endList)
		T.corner(row, 4)
		if mine then
			T.corner(T.new("Frame", { Name = "Mine", BorderSizePixel = 0, BackgroundColor3 = T.ACCENT, Position = UDim2.fromOffset(0, 9), Size = UDim2.fromOffset(3, 20) }, row), 2)
		end
		cells(row, { tostring(i), tostring(r[1]), tostring(r[2]), tostring(r[3]) }, 15, if mine then T.TEXT else T.MUTED, T.FONT_BOLD, if mine then T.ACCENT else T.TEXT)
	end
	endPanel.Size = UDim2.fromOffset(500, 180 + math.max(n, 1) * 40 + 70)
	endFill.Size = UDim2.fromScale(1, 1); T.tween(endFill, nextIn, { Size = UDim2.fromScale(0, 1) }, Enum.EasingStyle.Linear)
	endPanel.Visible = true; endShadow.Visible = true
	endShadow.BackgroundTransparency = 1; T.tween(endShadow, 0.2, { BackgroundTransparency = 0.5 })
	endScale.Scale = 0.96; T.tween(endScale, 0.16, { Scale = 1 })
	task.spawn(function()
		local t0 = os.clock()
		while my == endTok and os.clock() - t0 < nextIn do
			endNext.Text = (nextLabel or "next round in %d"):format(math.ceil(nextIn - (os.clock() - t0)))
			task.wait(0.25)
		end
		if my == endTok then endPanel.Visible = false; endShadow.Visible = false end
	end)
end
function H.hideEnd() endTok += 1; endPanel.Visible = false; endShadow.Visible = false end

-- the per-frame bits
-- the scopes (a scoped gun hides itself behind them: Arsenal). Both black the screen outside a round lens with a soft
-- edge, like looking down a tube (Rivals' and Valorant's snipers: the lens nearly the screen's height, the gun gone).
-- the Sniper's ("full"): a lens 96% of the screen's height and a duplex reticle, thin lines through the middle and thick
-- posts from the rim. the Second Opinion's ("short", the marksman's): a lens 88% high and its own reticle, a red dot
-- with short side lines and a post from below. (16 Nov 2026, owner: "aim down sights should look like the rivals
-- ones", "scopes look bad for the non snipers", later "reference rivals aim down sights and valorant ones".) the black
-- is one ring's very thick outline; the soft edge is a few fainter rings inside it
local scope = Instance.new("Frame")
scope.Name = "Scope"; scope.BackgroundTransparency = 1; scope.Size = UDim2.fromScale(1, 1); scope.Visible = false; scope.ZIndex = 0
scope.ClipsDescendants = true
scope.Parent = gui
local lens = Instance.new("Frame")
lens.Name = "Lens"; lens.AnchorPoint = Vector2.new(0.5, 0.5); lens.Position = UDim2.fromScale(0.5, 0.5)
lens.SizeConstraint = Enum.SizeConstraint.RelativeYY; lens.Size = UDim2.fromScale(0.96, 0.96); lens.BackgroundTransparency = 1
lens.ZIndex = 0 -- (under the panels: HP, ammo and the top line stay readable through the black)
local lensCorner = Instance.new("UICorner"); lensCorner.CornerRadius = UDim.new(0.5, 0); lensCorner.Parent = lens
local lensRim = Instance.new("UIStroke"); lensRim.Thickness = 2400; lensRim.Color = Color3.new(0, 0, 0); lensRim.Parent = lens
lens.Parent = scope
-- a reticle piece: a black bar (or a red dot) in the lens, placed by its anchor, position and size (lens scale + px)
local function bar(parent: Instance, anchor: Vector2, pos: UDim2, size: UDim2, color: Color3?)
	local f = Instance.new("Frame")
	f.BorderSizePixel = 0; f.BackgroundColor3 = color or Color3.new(0, 0, 0); f.AnchorPoint = anchor
	f.Position = pos; f.Size = size; f.ZIndex = 0; f.Parent = parent
	return f
end
local function reticle(name: string): Frame
	local r = Instance.new("Frame")
	r.Name = name; r.BackgroundTransparency = 1; r.Size = UDim2.fromScale(1, 1); r.ZIndex = 0; r.Visible = false; r.Parent = lens
	return r
end
local MID = Vector2.new(0.5, 0.5)
-- the Sniper's duplex: thin lines right across, thick posts on the outer fifth of each arm
local duplex = reticle("Duplex")
bar(duplex, MID, UDim2.fromScale(0.5, 0.5), UDim2.new(1, 0, 0, 2))
bar(duplex, MID, UDim2.fromScale(0.5, 0.5), UDim2.new(0, 2, 1, 0))
bar(duplex, Vector2.new(0, 0.5), UDim2.fromScale(0, 0.5), UDim2.new(0.19, 0, 0, 6))
bar(duplex, Vector2.new(1, 0.5), UDim2.fromScale(1, 0.5), UDim2.new(0.19, 0, 0, 6))
bar(duplex, Vector2.new(0.5, 0), UDim2.fromScale(0.5, 0), UDim2.new(0, 6, 0.19, 0))
bar(duplex, Vector2.new(0.5, 1), UDim2.fromScale(0.5, 1), UDim2.new(0, 6, 0.19, 0))
-- the Second Opinion's: a red dot, short lines either side with a gap round it, a post coming up from below
local marks = reticle("Marksman")
bar(marks, Vector2.new(1, 0.5), UDim2.fromScale(0.465, 0.5), UDim2.new(0.3, 0, 0, 2))
bar(marks, Vector2.new(0, 0.5), UDim2.fromScale(0.535, 0.5), UDim2.new(0.3, 0, 0, 2))
bar(marks, Vector2.new(0.5, 0), UDim2.fromScale(0.5, 0.535), UDim2.new(0, 2, 0.2, 0))
bar(marks, Vector2.new(0.5, 1), UDim2.fromScale(0.5, 1), UDim2.new(0, 6, 0.27, 0))
local mdot = bar(marks, MID, UDim2.fromScale(0.5, 0.5), UDim2.fromScale(0.011, 0.011), Color3.fromRGB(255, 52, 52))
local mdc = Instance.new("UICorner"); mdc.CornerRadius = UDim.new(0.5, 0); mdc.Parent = mdot
-- the soft edge: rings just inside the lens's rim, darkest at the rim (their width follows the lens's size on screen)
local SOFT = { 0.25, 0.45, 0.62, 0.76, 0.87, 0.94 } -- transparency, rim inward
local softRings = {}
for i, tr in SOFT do
	local r = Instance.new("Frame")
	r.Name = "Soft" .. i; r.BackgroundTransparency = 1; r.AnchorPoint = Vector2.new(0.5, 0.5); r.Position = UDim2.fromScale(0.5, 0.5)
	r.ZIndex = 0
	local c = Instance.new("UICorner"); c.CornerRadius = UDim.new(0.5, 0); c.Parent = r
	local st = Instance.new("UIStroke"); st.Color = Color3.new(0, 0, 0); st.Transparency = tr; st.Parent = r
	r.Parent = lens
	table.insert(softRings, { frame = r, stroke = st, i = i })
end
local function softFit()
	local d = lens.AbsoluteSize.Y
	local w = math.max(1, d * 0.012) -- each ring about 1.2% of the lens across
	for _, r in softRings do
		local inset = (r.i - 0.5) * w * 2
		r.frame.Size = UDim2.new(1, -inset, 1, -inset)
		r.stroke.Thickness = w
	end
end
lens:GetPropertyChangedSignal("AbsoluteSize"):Connect(softFit)
softFit()
local scopeKind = ""
function H.scope(on: boolean, kind: string?)
	if scope.Visible ~= on then scope.Visible = on end
	kind = kind or "full"
	if on and kind ~= scopeKind then
		scopeKind = kind
		local short = kind == "short"
		lens.Size = if short then UDim2.fromScale(0.88, 0.88) else UDim2.fromScale(0.96, 0.96)
		duplex.Visible = not short
		marks.Visible = short
	end
end

-- wid = the weapon in hand, spread = its spread now (radians: Arsenal's own number), for the look speed (Settings.live,
-- SettingsApply) and a crosshair that shows the spread
function H.step(dt: number, aim: number, scopeHide: boolean, wid: string?, spread: number?)
	local L = Settings.live
	L.aim = aim; L.scoped = scopeHide; L.wid = wid or ""; L.spread = spread or 0
	hurtA = math.max(0, hurtA - dt * 0.9)
	local rim = math.max(hurtA, lowA)
	for _, r in rims do r.BackgroundTransparency = 1 - rim end
	-- (no crosshair through the scope, over the end screen or under the settings panel)
	local shown = not scopeHide and not endPanel.Visible and me:GetAttribute("SettingsOpen") ~= true
	cross.Visible = shown
	-- aiming down a gun's sights: the sights mark the middle and the crosshair goes (Rivals, Valorant); a dot sight
	-- (Viewmodel's AimSight: the Redline) shows its red dot; a gun with no sights keeps a faint crosshair
	local kind = me:GetAttribute("AimSight")
	local sighted = kind == "iron" or kind == "dot"
	local fade = if sighted then math.clamp((aim - 0.45) / 0.4, 0, 1) else aim * 0.6
	if shown then
		local o = XH.opts()
		if not o.hideAim then fade = 0 end -- (Settings: HIDE WHILE AIMING off keeps it up)
		local cam = workspace.CurrentCamera
		local extra = if o.spread and cam then math.min(60, XH.spreadPx(spread or 0, cam.FieldOfView, cam.ViewportSize.Y)) else 0
		XH.draw(cross, o, fade, extra)
	end
	local d = if kind == "dot" and shown then math.clamp((aim - 0.6) / 0.3, 0, 1) else 0
	redDot.Visible = d > 0
	redDot.BackgroundTransparency = 1 - d
	redGlow.Transparency = 1 - d * 0.45
end

-- the controls line (bottom right) for step 2
-- (waited for: Hud.luau may make its gui after this module loads. on 16 Nov a test found the line still in Hud's
-- default words because it wasn't there yet)
task.spawn(function()
local keysHint = gui.Parent and (gui.Parent :: Instance):WaitForChild("JankfireHud", 30)
local hint = keysHint and keysHint:WaitForChild("Keys", 10) :: TextLabel?
if hint then
	-- keys 1 2 3 follow your loadout (Loadout.luau sets it on every arm; L opens the loadout screen)
	local lp = game:GetService("Players").LocalPlayer
	local WL = require(game:GetService("ReplicatedStorage"):WaitForChild("Jankfire"):WaitForChild("Weapons")).list
	local function keysLine()
		local s = lp:GetAttribute("Loadout")
		local ids = if type(s) == "string" then string.split(s, ",") else { "redline", "marbles", "katana" }
		local parts = {}
		-- (each key in white, what it does in grey)
		local function key(k: string, what: string) table.insert(parts, ('<font color="%s"><b>%s</b></font> %s'):format(T.hex(T.TEXT), k, what)) end
		local B0 = require(script.Parent:WaitForChild("Binds")) :: any -- (the keys as the player bound them: Settings > KEYBINDS)
		-- (a controller in your hands: its buttons, and an action with none is left out. Pad.luau)
		local pm = script.Parent:FindFirstChild("Pad")
		local okP, P = false, nil :: any
		if pm then okP, P = pcall(require, pm) end
		local pad = okP and P.on()
		local B = { label = function(id: string): string
			if not pad then return B0.label(id) end
			local b = P.button(id)
			return if b ~= "" then P.short(b) else ""
		end }
		local function key2(k: string, what: string) if k ~= "" and k ~= "hold " then key(k, what) end end
		if pad then key2(B.label("next"), "next weapon"); key2(B.label("slot3"), "melee") else
			for i, id in ids do key(B.label("slot" .. i), if WL[id] then WL[id].name else id) end
		end
		local item = Items.list[lp:GetAttribute("Item") :: any]
		if item and item.live then key2(B.label("item"), string.lower(item.name)) end
		for _, p in { { B.label("loadout"), "loadout" }, { B.label("fire"), "fire" }, { B.label("aim"), "aim / parry" }, { B.label("reload"), "reload" }, { B.label("sprint"), "run" },
			{ B.label("crouch"), "slide" }, { "hold " .. B.label("grapple"), "grapple" }, { B.label("camera"), "camera" }, { "hold " .. B.label("keys"), "show keys" } } do
			key2(p[1], p[2])
		end
		local line = hint :: TextLabel
		line.Text = table.concat(parts, "     ")
	end
	keysLine()
	lp:GetAttributeChangedSignal("Loadout"):Connect(keysLine)
	lp:GetAttributeChangedSignal("Item"):Connect(keysLine)
	Settings.onAny(function(k: string) if string.sub(k, 1, 5) == "bind." then keysLine() end end)
	task.spawn(function() -- (and when a controller is picked up or put down)
		local okP, P = pcall(require, script.Parent:WaitForChild("Pad", 10))
		if okP and type(P) == "table" and P.changed then P.changed.Event:Connect(keysLine) end
	end)
end
end)

return H
