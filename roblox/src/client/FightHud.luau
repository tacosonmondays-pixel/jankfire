--!strict
-- the fighting HUD in JANKFIRE's comic look (Hud.luau has the panels, speedometer and big callouts): crosshair + the
-- parry ring, hit markers (white x, red on a headshot), floating damage numbers, the hurt vignette and screen flashes,
-- HP and ammo, the clock and kill target, the kill feed in each weapon's colour, and the end screen
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))

local PINK, YELLOW, CYAN, PANEL, RED = Color3.fromRGB(255, 79, 216), Color3.fromRGB(255, 225, 77), Color3.fromRGB(79, 216, 255), Color3.fromRGB(18, 8, 24), Color3.fromRGB(255, 48, 48)
local FONT = Font.new("rbxasset://fonts/families/ComicNeueAngular.json", Enum.FontWeight.Bold)
local me = Players.LocalPlayer

local H = {}
local gui = Instance.new("ScreenGui")
gui.Name = "JankfireFight"; gui.ResetOnSpawn = false; gui.IgnoreGuiInset = true; gui.DisplayOrder = 2
gui.Parent = me:WaitForChild("PlayerGui")

local function label(parent: Instance, name: string, pos: UDim2, size: UDim2, text: string, color: Color3?, ts: number?): TextLabel
	local t = Instance.new("TextLabel")
	t.Name = name; t.BackgroundTransparency = 1; t.Position = pos; t.Size = size; t.FontFace = FONT
	t.Text = text; t.TextColor3 = color or Color3.new(1, 1, 1); t.TextStrokeTransparency = 0.2
	if ts then t.TextSize = ts else t.TextScaled = true end
	t.Parent = parent
	return t
end
-- a comic panel: dark purple-black, 4 px pink border, hard cyan offset shadow (8 px, no blur), a tilt
local function panel(name: string, pos: UDim2, size: UDim2, tilt: number?): Frame
	local sh = Instance.new("Frame")
	sh.Name = name .. "Shadow"; sh.BackgroundColor3 = CYAN; sh.BorderSizePixel = 0
	sh.Position = pos + UDim2.fromOffset(8, 8); sh.Size = size; sh.Rotation = tilt or 0
	sh.Parent = gui
	local f = Instance.new("Frame")
	f.Name = name; f.BackgroundColor3 = PANEL; f.BackgroundTransparency = 0.08; f.BorderSizePixel = 0
	f.Position = pos; f.Size = size; f.Rotation = tilt or 0
	local st = Instance.new("UIStroke"); st.Color = PINK; st.Thickness = 4; st.ApplyStrokeMode = Enum.ApplyStrokeMode.Border; st.Parent = f
	f.Parent = gui
	return f
end

-- ---------------------------------------------------------------- crosshair, parry ring, hit marker
local cross = Instance.new("Frame")
cross.Name = "Crosshair"; cross.BackgroundTransparency = 1; cross.AnchorPoint = Vector2.new(0.5, 0.5)
cross.Position = UDim2.fromScale(0.5, 0.5); cross.Size = UDim2.fromOffset(40, 40); cross.Parent = gui
for i, d in { Vector2.new(0, -1), Vector2.new(0, 1), Vector2.new(-1, 0), Vector2.new(1, 0) } do
	local b = Instance.new("Frame")
	b.Name = "Bar" .. i; b.BorderSizePixel = 0; b.BackgroundColor3 = Color3.new(1, 1, 1); b.AnchorPoint = Vector2.new(0.5, 0.5)
	b.Size = if d.X == 0 then UDim2.fromOffset(3, 9) else UDim2.fromOffset(9, 3)
	b.Position = UDim2.new(0.5, d.X * 10, 0.5, d.Y * 10)
	local s = Instance.new("UIStroke"); s.Thickness = 1; s.Color = Color3.new(0, 0, 0); s.Parent = b
	b.Parent = cross
end
local ring = Instance.new("Frame")
ring.Name = "ParryRing"; ring.AnchorPoint = Vector2.new(0.5, 0.5); ring.Position = UDim2.fromScale(0.5, 0.5)
ring.Size = UDim2.fromOffset(54, 54); ring.BackgroundTransparency = 1; ring.Visible = false; ring.Parent = gui
local rc = Instance.new("UICorner"); rc.CornerRadius = UDim.new(0.5, 0); rc.Parent = ring
local rs = Instance.new("UIStroke"); rs.Thickness = 3; rs.Color = Color3.fromRGB(159, 232, 255); rs.Parent = ring
local rg = Instance.new("UIGradient"); rg.Parent = rs

local marker = Instance.new("TextLabel")
marker.Name = "HitMarker"; marker.BackgroundTransparency = 1; marker.AnchorPoint = Vector2.new(0.5, 0.5)
marker.Position = UDim2.fromScale(0.5, 0.5); marker.Size = UDim2.fromOffset(34, 34); marker.FontFace = FONT; marker.TextScaled = true
marker.Text = "x"; marker.TextColor3 = Color3.new(1, 1, 1); marker.TextStrokeTransparency = 0; marker.TextTransparency = 1; marker.Parent = gui

local markTok = 0
function H.hit(head: boolean)
	markTok += 1
	local my = markTok
	marker.Text = if head then "✖" else "x"
	marker.TextColor3 = if head then RED else Color3.new(1, 1, 1)
	marker.TextTransparency = 0
	marker.Size = UDim2.fromOffset(if head then 46 else 34, if head then 46 else 34)
	task.delay(0.18, function() if my == markTok then marker.TextTransparency = 1 end end)
end

-- the parry ring: full while the guard is open, draining over the cooldown, a blink when it's ready again
function H.parryRing(state: string, k: number)
	ring.Visible = state ~= "hidden"
	if state == "open" then rs.Color = Color3.fromRGB(159, 232, 255); rs.Transparency = 0; rg.Transparency = NumberSequence.new(0)
	elseif state == "drain" then
		rs.Color = Color3.fromRGB(120, 140, 160); rs.Transparency = 0.3
		local kk = math.clamp(k, 0.001, 0.999)
		rg.Rotation = -90
		rg.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(kk, 0), NumberSequenceKeypoint.new(math.min(0.9999, kk + 0.001), 1), NumberSequenceKeypoint.new(1, 1) })
	elseif state == "ready" then rs.Color = Color3.new(1, 1, 1); rs.Transparency = 0; rg.Transparency = NumberSequence.new(0) end
end

-- ---------------------------------------------------------------- damage numbers (over the victim, in the world)
function H.dmgNum(at: Vector3, amount: number, head: boolean)
	local a = Instance.new("Attachment")
	a.WorldPosition = at + Vector3.new(math.random() - 0.5, 1, math.random() - 0.5)
	a.Parent = workspace.Terrain
	local bb = Instance.new("BillboardGui")
	bb.Size = UDim2.fromOffset(90, 40); bb.AlwaysOnTop = true; bb.LightInfluence = 0; bb.Adornee = a; bb.Parent = a
	local t = label(bb, "N", UDim2.fromScale(0, 0), UDim2.fromScale(1, 1), tostring(amount) .. (if head then "!!" else ""), if head then RED else YELLOW)
	t.TextStrokeTransparency = 0
	TweenService:Create(a, TweenInfo.new(0.9), { WorldPosition = a.WorldPosition + Vector3.new(0, 3, 0) }):Play()
	TweenService:Create(t, TweenInfo.new(0.9, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { TextTransparency = 1, TextStrokeTransparency = 1 }):Play()
	task.delay(0.95, function() a:Destroy() end)
end

-- ---------------------------------------------------------------- hurt vignette + screen flash
local vig = Instance.new("Frame")
-- (a stroke draws outside its frame: the frame sits 90 px in from every edge so the 90 px stroke covers the screen's rim)
vig.Name = "Hurt"; vig.Position = UDim2.fromOffset(90, 90); vig.Size = UDim2.new(1, -180, 1, -180); vig.BackgroundTransparency = 1; vig.BorderSizePixel = 0; vig.Parent = gui
local vs = Instance.new("UIStroke"); vs.Thickness = 90; vs.Color = RED; vs.Transparency = 1; vs.ApplyStrokeMode = Enum.ApplyStrokeMode.Border; vs.Parent = vig
local hurtA = 0
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
local hpPanel = panel("Hp", UDim2.new(0, 24, 1, -176), UDim2.fromOffset(190, 62), 1.5)
local hpBar = Instance.new("Frame")
hpBar.Name = "Bar"; hpBar.BorderSizePixel = 0; hpBar.BackgroundColor3 = Color3.fromRGB(57, 255, 20); hpBar.Position = UDim2.fromOffset(8, 40)
hpBar.Size = UDim2.new(1, -16, 0, 12); hpBar.Parent = hpPanel
local hpText = label(hpPanel, "Text", UDim2.fromOffset(8, 2), UDim2.new(1, -16, 0, 36), "100 HP", YELLOW)
local ammoPanel = panel("Ammo", UDim2.new(1, -244, 1, -150), UDim2.fromOffset(220, 84), -1.5)
local wName = label(ammoPanel, "Weapon", UDim2.fromOffset(10, 4), UDim2.new(1, -20, 0, 30), "", Color3.new(1, 1, 1))
local ammoText = label(ammoPanel, "Count", UDim2.fromOffset(10, 34), UDim2.new(1, -20, 0, 44), "", YELLOW)
function H.hp(hp: number)
	hpText.Text = tostring(math.max(0, math.ceil(hp))) .. " HP"
	hpBar.Size = UDim2.new(math.clamp(hp / 100, 0, 1), -16, 0, 12)
	hpBar.BackgroundColor3 = if hp > 50 then Color3.fromRGB(57, 255, 20) elseif hp > 25 then YELLOW else RED
end
function H.weapon(wid: string, mag: number?, reloading: boolean, kat: number)
	local w = Weapons.list[wid]
	if not w then return end
	wName.Text = w.name; wName.TextColor3 = w.color
	if w.kind == "melee" then
		ammoText.Text = if kat > 0 then ("%d kills · %.1f m"):format(kat, Weapons.reach(w, kat) / Weapons.S) else "RMB parry"
	elseif reloading then ammoText.Text = "RELOADING"
	else ammoText.Text = ("%d / %d"):format(mag or 0, w.mag or 0) end
end

-- ---------------------------------------------------------------- clock + kill target
local top = panel("Round", UDim2.new(0.5, -150, 0, 14), UDim2.fromOffset(300, 46), -1)
local topText = label(top, "Text", UDim2.fromOffset(8, 4), UDim2.new(1, -16, 1, -8), "", YELLOW)
function H.round(target: number, left: number, myKills: number)
	local m, s = math.floor(math.max(0, left) / 60), math.floor(math.max(0, left)) % 60
	topText.Text = ("first to %d · %d:%02d · you %d"):format(target, m, s, myKills)
end

-- ---------------------------------------------------------------- kill feed (top right, 6 lines, 7 s)
local feed = Instance.new("Frame")
feed.Name = "Feed"; feed.BackgroundTransparency = 1; feed.AnchorPoint = Vector2.new(1, 0); feed.Position = UDim2.new(1, -16, 0, 80)
feed.Size = UDim2.fromOffset(460, 6 * 30); feed.Parent = gui
local fl = Instance.new("UIListLayout"); fl.HorizontalAlignment = Enum.HorizontalAlignment.Right; fl.Padding = UDim.new(0, 4)
fl.SortOrder = Enum.SortOrder.LayoutOrder; fl.Parent = feed
local feedN = 0
local function hex(c: Color3): string return c:ToHex() end
function H.feed(killer: string?, wid: string, victim: string, suffix: string?)
	feedN += 1
	local w = Weapons.list[wid]
	local row = Instance.new("TextLabel")
	row.Name = "Line"; row.LayoutOrder = feedN; row.BackgroundColor3 = PANEL; row.BackgroundTransparency = 0.25; row.BorderSizePixel = 0
	row.AutomaticSize = Enum.AutomaticSize.X; row.Size = UDim2.fromOffset(0, 26); row.FontFace = FONT; row.TextSize = 20; row.RichText = true
	row.TextColor3 = Color3.new(1, 1, 1)
	local tag = if w then ('<font color="#%s">[%s]</font>'):format(hex(w.color), w.name) else ""
	local function esc(s: string): string return (s:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;")) end
	row.Text = (" %s  %s  %s%s "):format(if killer then esc(killer) else "", tag, esc(victim), if suffix then "  " .. suffix else "")
	local pad = Instance.new("UIPadding"); pad.PaddingLeft = UDim.new(0, 6); pad.PaddingRight = UDim.new(0, 6); pad.Parent = row
	row.Parent = feed
	local lines = {}
	for _, c in feed:GetChildren() do if c:IsA("TextLabel") then table.insert(lines, c) end end
	table.sort(lines, function(a, b) return a.LayoutOrder < b.LayoutOrder end)
	while #lines > 6 do (table.remove(lines, 1) :: TextLabel):Destroy() end
	task.delay(7, function() if row.Parent then row:Destroy() end end)
end

-- ---------------------------------------------------------------- death line
local deathText = label(gui, "Death", UDim2.new(0.2, 0, 0.62, 0), UDim2.new(0.6, 0, 0.06, 0), "", Color3.new(1, 1, 1))
deathText.Visible = false
function H.dead(text: string?)
	deathText.Visible = text ~= nil
	deathText.Text = text or ""
end

-- ---------------------------------------------------------------- end screen
local endPanel = panel("End", UDim2.new(0.5, -260, 0.5, -210), UDim2.fromOffset(520, 420), -1)
local endShadow = gui:FindFirstChild("EndShadow") :: Frame
endPanel.Visible = false; endShadow.Visible = false
local endTitle = label(endPanel, "Title", UDim2.fromOffset(16, 10), UDim2.new(1, -32, 0, 64), "", YELLOW)
local endList = Instance.new("Frame")
endList.Name = "Board"; endList.BackgroundTransparency = 1; endList.Position = UDim2.fromOffset(24, 84); endList.Size = UDim2.new(1, -48, 1, -140); endList.Parent = endPanel
local el = Instance.new("UIListLayout"); el.Padding = UDim.new(0, 4); el.SortOrder = Enum.SortOrder.LayoutOrder; el.Parent = endList
local endNext = label(endPanel, "Next", UDim2.new(0, 16, 1, -48), UDim2.new(1, -32, 0, 34), "", CYAN)
local endTok = 0
function H.endScreen(winner: string?, iWon: boolean, board: { { any } }, nextIn: number)
	endTok += 1
	local my = endTok
	for _, c in endList:GetChildren() do if c:IsA("TextLabel") then c:Destroy() end end
	endTitle.Text = if iWon then "YOU WIN" elseif winner then winner .. " wins" else "NOBODY WINS (no kills, no glory)"
	for i, r in board do
		if i > 8 then break end
		local row = label(endList, "Row", UDim2.new(), UDim2.new(1, 0, 0, 30), ("%d.  %s   %d kills · %d deaths"):format(i, tostring(r[1]), r[2], r[3]),
			if r[4] == me.UserId then YELLOW else Color3.new(1, 1, 1), 22)
		row.TextXAlignment = Enum.TextXAlignment.Left; row.LayoutOrder = i
	end
	endPanel.Visible = true; endShadow.Visible = true
	task.spawn(function()
		local t0 = os.clock()
		while my == endTok and os.clock() - t0 < nextIn do
			endNext.Text = ("next round in %d"):format(math.ceil(nextIn - (os.clock() - t0)))
			task.wait(0.25)
		end
		if my == endTok then endPanel.Visible = false; endShadow.Visible = false end
	end)
end
function H.hideEnd() endTok += 1; endPanel.Visible = false; endShadow.Visible = false end

-- the per-frame bits
function H.step(dt: number, aim: number, scopeHide: boolean)
	hurtA = math.max(0, hurtA - dt * 0.9)
	vs.Transparency = 1 - hurtA
	cross.Visible = not scopeHide
	for _, c in cross:GetChildren() do
		if c:IsA("Frame") then c.BackgroundTransparency = aim * 0.6 end
	end
end

-- the controls line (bottom right) for step 2
local keysHint = gui.Parent and (gui.Parent :: Instance):FindFirstChild("JankfireHud")
local hint = keysHint and keysHint:FindFirstChild("Keys") :: TextLabel?
if hint then
	hint.Size = UDim2.fromOffset(760, 22)
	hint.Text = "1 Redline · 2 Marble Shotgun · 3 Katana · LMB fire · RMB aim / parry · R reload · shift run · C slide · hold E grapple · V camera"
end

return H
