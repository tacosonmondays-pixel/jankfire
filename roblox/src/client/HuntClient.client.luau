--!strict
-- HOLDOUT on your screen (26 Nov 2026; roblox/docs/HUNT.md section 8). Stage 1, THE HOUSE:
--   * the round board on the hall wall (a SurfaceGui on the house's Hunt.Board part): the state of the next round and
--     how many are in the house (ReplicatedStorage attributes HuntPhase, HuntPlayers, HuntNext)
--   * the moves' keys, a quiet strip at the bottom: for a few seconds after you walk in, and while KEYS (H) is held
--   * arriving from the PLAY screen's HOLDOUT card closes the PLAY screen
-- No flavour text: the board says the state of play, the strip says the keys.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UIS = game:GetService("UserInputService")
local RunService = game:GetService("RunService")

local HC = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("HuntConfig")) :: any
local T = require(script.Parent:WaitForChild("Theme")) :: any
local Binds = require(script.Parent:WaitForChild("Binds")) :: any

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")

local function new(cls: string, props: { [string]: any }, parent: Instance?): any
	local o = Instance.new(cls)
	for k, v in props do (o :: any)[k] = v end
	if parent then o.Parent = parent end
	return o
end
local function label(parent: Instance, text: string, size: number, color: Color3, font: Font, align: Enum.TextXAlignment?): TextLabel
	return new("TextLabel", { BackgroundTransparency = 1, Text = text, TextSize = size, TextColor3 = color, FontFace = font,
		TextXAlignment = align or Enum.TextXAlignment.Left, TextYAlignment = Enum.TextYAlignment.Center }, parent)
end

-- ------------------------------------------------------------------ the board
local board: SurfaceGui? = nil
local bigLine: TextLabel? = nil
local subLine: TextLabel? = nil
local function buildBoard(part: BasePart)
	if board then board:Destroy() end
	local g = new("SurfaceGui", { Name = "HuntBoard", Face = Enum.NormalId.Front, Adornee = part, PixelsPerStud = 60,
		SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud, LightInfluence = 0.15, Brightness = 1.4, ResetOnSpawn = false,
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, pg)
	local plate = new("Frame", { BackgroundColor3 = T.BG, BackgroundTransparency = 0, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1) }, g)
	local pad = new("UIPadding", { PaddingLeft = UDim.new(0, 34), PaddingRight = UDim.new(0, 34), PaddingTop = UDim.new(0, 26), PaddingBottom = UDim.new(0, 26) }, plate)
	local top = label(plate, HC.TITLE, 30, T.MUTED, T.FONT_TITLE)
	top.Size = UDim2.new(1, 0, 0, 40)
	new("Frame", { BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Position = UDim2.fromOffset(0, 48), Size = UDim2.fromOffset(56, 4) }, plate)
	local big = label(plate, "", 50, T.TEXT, T.FONT_TITLE)
	big.Position = UDim2.fromOffset(0, 96); big.Size = UDim2.new(1, 0, 0, 120); big.TextWrapped = true
	local sub = label(plate, "", 30, T.SOFT, T.FONT_BOLD)
	sub.AnchorPoint = Vector2.new(0, 1); sub.Position = UDim2.new(0, 0, 1, 0); sub.Size = UDim2.new(1, 0, 0, 44)
	board, bigLine, subLine = g, big, sub
	_ = pad
end
local function refreshBoard()
	if not (bigLine and subLine) then return end
	local n = tonumber(ReplicatedStorage:GetAttribute("HuntPlayers")) or 0
	local phase = ReplicatedStorage:GetAttribute("HuntPhase")
	local nextT = ReplicatedStorage:GetAttribute("HuntNext")
	local need = HC.ROUND.minPlayers
	if phase == "starting" and type(nextT) == "number" then
		bigLine.Text = ("NEXT ROUND IN %d"):format(math.max(0, math.ceil(nextT - workspace:GetServerTimeNow())))
	elseif phase == "round" then
		bigLine.Text = "ROUND IN PLAY"
	else
		bigLine.Text = "WAITING FOR PLAYERS"
	end
	subLine.Text = if n >= need then ("%d IN THE HOUSE"):format(n) else ("%d IN THE HOUSE · %d TO START"):format(n, need)
end
task.spawn(function()
	local map = workspace:WaitForChild("Map")
	local house = map:WaitForChild(HC.HOUSE, 120)
	local hf = house and house:WaitForChild("Hunt", 60)
	local b = hf and hf:WaitForChild("Board", 30)
	if b and b:IsA("BasePart") then buildBoard(b); refreshBoard() end
end)
ReplicatedStorage:GetAttributeChangedSignal("HuntPlayers"):Connect(refreshBoard)
ReplicatedStorage:GetAttributeChangedSignal("HuntPhase"):Connect(refreshBoard)
local acc = 0
RunService.Heartbeat:Connect(function(dt)
	acc += dt
	if acc < 0.5 then return end
	acc = 0
	if ReplicatedStorage:GetAttribute("HuntPhase") == "starting" then refreshBoard() end
end)

-- ------------------------------------------------------------------ the keys strip
local strip = new("ScreenGui", { Name = "HuntKeys", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 4, Enabled = false }, pg)
local row = new("Frame", { BackgroundColor3 = T.BG, BackgroundTransparency = T.BG_A, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 1),
	Position = UDim2.new(0.5, 0, 1, -28), Size = UDim2.fromOffset(10, 40), AutomaticSize = Enum.AutomaticSize.X }, strip)
new("UICorner", { CornerRadius = UDim.new(0, T.RADIUS) }, row)
new("UIPadding", { PaddingLeft = UDim.new(0, 14), PaddingRight = UDim.new(0, 14) }, row)
new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, 16),
	SortOrder = Enum.SortOrder.LayoutOrder }, row)
local function item(i: number, key: string, what: string)
	local f = new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromOffset(10, 26), AutomaticSize = Enum.AutomaticSize.X, LayoutOrder = i }, row)
	new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, 7) }, f)
	local cap = new("TextLabel", { BackgroundColor3 = T.CARD, BorderSizePixel = 0, Text = key, TextSize = 13, TextColor3 = T.TEXT, FontFace = T.FONT_BOLD,
		Size = UDim2.fromOffset(10, 24), AutomaticSize = Enum.AutomaticSize.X, LayoutOrder = 1 }, f)
	new("UICorner", { CornerRadius = UDim.new(0, 4) }, cap)
	new("UIPadding", { PaddingLeft = UDim.new(0, 7), PaddingRight = UDim.new(0, 7) }, cap)
	local w = label(f, what, 14, T.SOFT, T.FONT_BOLD)
	w.Size = UDim2.fromOffset(10, 24); w.AutomaticSize = Enum.AutomaticSize.X; w.LayoutOrder = 2
end
local function keyOf(id: string, fallback: string): string
	local ok, l = pcall(function() return Binds.label(id) end)
	return if ok and type(l) == "string" and l ~= "" then l else fallback
end
local function fillStrip()
	for _, c in row:GetChildren() do if c:IsA("Frame") then c:Destroy() end end
	item(1, keyOf("fire", "CLICK"), "PUNCH · HOLD TO WIND UP")
	item(2, keyOf("grapple", "E"), "PUSH · HOLD FOR SUPER PUSH")
	item(3, keyOf("reel", "X"), "LIE DOWN")
end
local showUntil = 0
local function update()
	local inMode = me:GetAttribute("Hunt") ~= nil and me:GetAttribute("HuntRole") ~= "gunman"
	local held = false
	pcall(function() held = Binds.down("keys") end)
	strip.Enabled = inMode and (os.clock() < showUntil or held) and me:GetAttribute("LoadoutOpen") == nil
end
me:GetAttributeChangedSignal("Hunt"):Connect(function()
	if me:GetAttribute("Hunt") ~= nil then
		fillStrip()
		showUntil = os.clock() + 12
		-- (arrived from the PLAY screen's HOLDOUT card: close it)
		task.spawn(function()
			local m = script.Parent:FindFirstChild("PlayUI")
			if m then
				local ok, PlayUI = pcall(require, m)
				if ok and PlayUI and PlayUI.isOpen and PlayUI.isOpen() then pcall(PlayUI.close) end
			end
		end)
	end
	update()
end)
RunService.RenderStepped:Connect(update)
_ = UIS

-- ------------------------------------------------------------------ the round (stage 2)
-- top centre: the phase and its clock; under it your role (the gunman's gun by name) and his two passives, which
-- everyone sees. the gunman, sealed in while they hide, sees a dark screen with the count. the end: the result card
local Weapons = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Weapons")) :: any
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Hunt") :: RemoteEvent
local rg = new("ScreenGui", { Name = "HuntRound", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 5, Enabled = false }, pg)
local top = new("Frame", { BackgroundColor3 = T.BG, BackgroundTransparency = T.BG_A, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0),
	Position = UDim2.new(0.5, 0, 0, 62), Size = UDim2.fromOffset(300, 92) }, rg)
new("UICorner", { CornerRadius = UDim.new(0, T.RADIUS) }, top)
local phaseL = label(top, "", 13, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center)
phaseL.Position = UDim2.fromOffset(0, 8); phaseL.Size = UDim2.new(1, 0, 0, 16)
local clockL = label(top, "", 30, T.TEXT, T.FONT_TITLE, Enum.TextXAlignment.Center)
clockL.Position = UDim2.fromOffset(0, 24); clockL.Size = UDim2.new(1, 0, 0, 34)
local roleL = label(top, "", 13, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Center)
roleL.Position = UDim2.fromOffset(0, 58); roleL.Size = UDim2.new(1, 0, 0, 16)
local passL = label(top, "", 11, T.MUTED, T.FONT, Enum.TextXAlignment.Center)
passL.Position = UDim2.fromOffset(0, 74); passL.Size = UDim2.new(1, 0, 0, 14)
local shade = new("Frame", { BackgroundColor3 = Color3.fromRGB(8, 9, 11), BackgroundTransparency = 0.08, BorderSizePixel = 0,
	Size = UDim2.fromScale(1, 1), Visible = false, ZIndex = 0 }, rg)
local shadeL = label(shade, "THE HIDERS ARE HIDING", 22, T.SOFT, T.FONT_TITLE, Enum.TextXAlignment.Center)
shadeL.AnchorPoint = Vector2.new(0.5, 0.5); shadeL.Position = UDim2.fromScale(0.5, 0.55); shadeL.Size = UDim2.fromOffset(600, 30)
local card = new("Frame", { BackgroundColor3 = T.BG, BackgroundTransparency = 0.08, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
	Position = UDim2.fromScale(0.5, 0.42), Size = UDim2.fromOffset(420, 150), Visible = false }, rg)
new("UICorner", { CornerRadius = UDim.new(0, T.RADIUS) }, card)
new("Frame", { BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Position = UDim2.fromOffset(28, 26), Size = UDim2.fromOffset(40, 3) }, card)
local cardBig = label(card, "", 32, T.TEXT, T.FONT_TITLE)
cardBig.Position = UDim2.fromOffset(28, 38); cardBig.Size = UDim2.new(1, -56, 0, 40)
local cardA = label(card, "", 15, T.SOFT, T.FONT_BOLD)
cardA.Position = UDim2.fromOffset(28, 84); cardA.Size = UDim2.new(1, -56, 0, 20); cardA.TextTruncate = Enum.TextTruncate.AtEnd
local cardB = label(card, "", 14, T.MUTED, T.FONT)
cardB.Position = UDim2.fromOffset(28, 108); cardB.Size = UDim2.new(1, -56, 0, 20); cardB.TextTruncate = Enum.TextTruncate.AtEnd

local function passivesText(): string
	local ids = ReplicatedStorage:GetAttribute("HuntPassives")
	if type(ids) ~= "string" or ids == "" then return "" end
	local names = {}
	for id in string.gmatch(ids, "[^,]+") do
		for _, pv in HC.PASSIVES do if pv.id == id then table.insert(names, pv.name) end end
	end
	return "GUNMAN: " .. table.concat(names, " · ")
end
local function gunName(): string
	local id = ReplicatedStorage:GetAttribute("HuntGun")
	local w = type(id) == "string" and Weapons.list and Weapons.list[id]
	return if w then string.upper(w.name) else ""
end
local cardUntil = 0
RunService.RenderStepped:Connect(function()
	local inRound = me:GetAttribute("Hunt") == "round"
	local ph = ReplicatedStorage:GetAttribute("HuntRoundPhase")
	-- (the gunman's intro owns the screen while it plays: no board, no hide shade; HuntIntro)
	rg.Enabled = me:GetAttribute("HuntIntro") == nil and me:GetAttribute("HuntOutro") == nil and (inRound and ph ~= nil or os.clock() < cardUntil)
	card.Visible = os.clock() < cardUntil
	if not (inRound and ph) then shade.Visible = false; top.Visible = false; return end
	top.Visible = ph ~= "end"
	local ends = ReplicatedStorage:GetAttribute("HuntRoundEnd")
	local left = if type(ends) == "number" then math.max(0, ends - workspace:GetServerTimeNow()) else 0
	clockL.Text = ("%d:%02d"):format(math.floor(left / 60), math.floor(left % 60))
	local role = me:GetAttribute("HuntRole")
	phaseL.Text = if ph == "hide" then "HIDE" elseif ReplicatedStorage:GetAttribute("HuntFightBack") then "FIGHT BACK" else "HUNT"
	roleL.Text = if role == "gunman" then ("GUNMAN · %s"):format(gunName()) else "HIDER"
	passL.Text = passivesText()
	shade.Visible = ph == "hide" and role == "gunman" and left > 0.5 -- (v7: no one-frame flash as the intro hands over)
	if shade.Visible then shadeL.Text = ("THE HIDERS ARE HIDING · %d"):format(math.ceil(left)) end
end)
-- ------------------------------------------------------------------ stage 3: points, the two trap slots, the trap menu
-- bottom right: your points and the two traps you carry (keys of the PRIMARY / SECONDARY slots use them). UTILITY (G)
-- opens the trap menu: six tiles, each with its key (1-6 buys while the menu is up), its price and one plain line
local TRAPS = HC.TRAPS
local inv = new("Frame", { BackgroundColor3 = T.BG, BackgroundTransparency = T.BG_A, BorderSizePixel = 0, AnchorPoint = Vector2.new(1, 1),
	Position = UDim2.new(1, -24, 1, -24), Size = UDim2.fromOffset(250, 96), Visible = false }, rg)
new("UICorner", { CornerRadius = UDim.new(0, T.RADIUS) }, inv)
local ptsL = label(inv, "", 24, T.TEXT, T.FONT_TITLE, Enum.TextXAlignment.Right)
ptsL.Position = UDim2.new(0, 12, 0, 6); ptsL.Size = UDim2.new(1, -24, 0, 28)
local ptsCap = label(inv, "POINTS", 11, T.MUTED, T.FONT_BOLD)
ptsCap.Position = UDim2.fromOffset(12, 12); ptsCap.Size = UDim2.fromOffset(80, 16)
local slotL = {}
for i = 1, 2 do
	local s = new("Frame", { BackgroundColor3 = T.CARD, BorderSizePixel = 0, Position = UDim2.new(0, 12 + (i - 1) * 116, 0, 44), Size = UDim2.fromOffset(110, 42) }, inv)
	new("UICorner", { CornerRadius = UDim.new(0, 4) }, s)
	local k = label(s, tostring(i), 11, T.MUTED, T.FONT_BOLD); k.Position = UDim2.fromOffset(8, 4); k.Size = UDim2.fromOffset(20, 14)
	local n = label(s, "", 13, T.TEXT, T.FONT_BOLD); n.Position = UDim2.fromOffset(8, 18); n.Size = UDim2.new(1, -14, 0, 18); n.TextTruncate = Enum.TextTruncate.AtEnd
	slotL[i] = { k = k, n = n }
end
local menu = new("Frame", { BackgroundColor3 = T.BG, BackgroundTransparency = 0.12, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 1),
	Position = UDim2.new(0.5, 0, 1, -140), Size = UDim2.fromOffset(640, 196), Visible = false }, rg)
new("UICorner", { CornerRadius = UDim.new(0, T.RADIUS) }, menu)
local mTitle = label(menu, "TRAPS", 13, T.MUTED, T.FONT_BOLD); mTitle.Position = UDim2.fromOffset(16, 10); mTitle.Size = UDim2.fromOffset(200, 16)
local tiles = {}
for i, tr in TRAPS do
	local col, row2 = (i - 1) % 3, math.floor((i - 1) / 3)
	local tile = new("TextButton", { AutoButtonColor = false, Text = "", BackgroundColor3 = T.CARD, BorderSizePixel = 0,
		Position = UDim2.fromOffset(16 + col * 204, 34 + row2 * 78), Size = UDim2.fromOffset(196, 72) }, menu)
	new("UICorner", { CornerRadius = UDim.new(0, 4) }, tile)
	local k = label(tile, tostring(i), 11, T.MUTED, T.FONT_BOLD); k.Position = UDim2.fromOffset(10, 6); k.Size = UDim2.fromOffset(16, 14)
	local n = label(tile, tr.name, 14, T.TEXT, T.FONT_BOLD); n.Position = UDim2.fromOffset(26, 5); n.Size = UDim2.fromOffset(120, 16)
	local c = label(tile, tostring(tr.cost), 14, T.ACCENT, T.FONT_BOLD, Enum.TextXAlignment.Right); c.Position = UDim2.new(1, -60, 0, 5); c.Size = UDim2.fromOffset(50, 16)
	local d = label(tile, tr.say, 12, T.SOFT, T.FONT); d.Position = UDim2.fromOffset(10, 26); d.Size = UDim2.new(1, -20, 0, 38); d.TextWrapped = true
	d.TextYAlignment = Enum.TextYAlignment.Top
	tile.MouseButton1Click:Connect(function() Remote:FireServer("buy", tr.id) end)
	tiles[i] = { tile = tile, cost = tr.cost }
end
local trapName: { [string]: string } = {}
for _, tr in TRAPS do trapName[tr.id] = tr.name end
local found = label(rg, "", 18, T.TEXT, T.FONT_TITLE, Enum.TextXAlignment.Center)
found.AnchorPoint = Vector2.new(0.5, 0.5); found.Position = UDim2.fromScale(0.5, 0.66); found.Size = UDim2.fromOffset(500, 26); found.Visible = false
local foundUntil = 0
local function hiderInRound(): boolean
	return me:GetAttribute("Hunt") == "round" and me:GetAttribute("HuntRole") == "hider" and ReplicatedStorage:GetAttribute("HuntRoundPhase") == "hunt"
end
RunService.RenderStepped:Connect(function()
	local on = hiderInRound()
	inv.Visible = on
	if not on then menu.Visible = false end
	found.Visible = os.clock() < foundUntil
	if not on then return end
	local pts = tonumber(me:GetAttribute("HuntPoints")) or 0
	ptsL.Text = tostring(pts)
	local items = {}
	local raw = me:GetAttribute("HuntItems")
	if type(raw) == "string" then
		for id, uses in string.gmatch(raw, "([%w_]+):(%d+)") do table.insert(items, { id = id, uses = tonumber(uses) or 1 }) end
	end
	for i = 1, 2 do
		local it = items[i]
		slotL[i].n.Text = if it then (trapName[it.id] or it.id) .. (if it.uses > 1 then (" ×%d"):format(it.uses) else "") else "—"
		slotL[i].n.TextColor3 = if it then T.TEXT else T.DIM
	end
	local wpn = me:GetAttribute("HuntWeapon")
	ptsCap.Text = if type(wpn) == "string" and HC.WEAPONS[wpn] then HC.WEAPONS[wpn].name else "POINTS"
	for _, tl in tiles do tl.tile.BackgroundColor3 = if pts >= tl.cost and #items < HC.POINTS.carry then T.CARD_HI else T.CARD end
end)
UIS.InputBegan:Connect(function(io: InputObject, gp: boolean)
	if gp or not hiderInRound() then return end
	if Binds.is("item", io) then menu.Visible = not menu.Visible; return end
	if menu.Visible then
		local k = io.KeyCode.Value - Enum.KeyCode.One.Value + 1
		if io.UserInputType == Enum.UserInputType.Keyboard and k >= 1 and k <= #TRAPS then Remote:FireServer("buy", TRAPS[k].id) end
		return
	end
	if Binds.is("slot1", io) then Remote:FireServer("use", 1, workspace.CurrentCamera.CFrame.LookVector)
	elseif Binds.is("slot2", io) then Remote:FireServer("use", 2, workspace.CurrentCamera.CFrame.LookVector) end
end)

Remote.OnClientEvent:Connect(function(op: string, a: any)
	if op == "found" then
		found.Text = if type(a) == "string" and HC.WEAPONS[a] then HC.WEAPONS[a].name else "NOTHING HERE"
		foundUntil = os.clock() + 1.6
		return
	end
	if op ~= "results" or type(a) ~= "table" then return end
	if me:GetAttribute("Hunt") ~= "round" then return end
	cardBig.Text = if a.winner == "gunman" then "GUNMAN WINS" elseif a.winner == "hiders" then "HIDERS WIN" else "ROUND OVER"
	local n = if type(a.survivors) == "table" then #a.survivors else 0
	cardA.Text = if a.winner == "hiders" and a.why == "the gunman is down" then "GUNMAN DOWN" -- (27 Nov: plain facts, no lowercase whisper)
		elseif n > 0 then ("%d SURVIVED: %s"):format(n, table.concat(a.survivors, ", ")) else "NO SURVIVORS"
	cardB.Text = ("GUNMAN %s · %d KILLS"):format(tostring(a.gunman or "-"), tonumber(a.kills) or 0)
	cardUntil = os.clock() + HC.ROUND.results
end)
