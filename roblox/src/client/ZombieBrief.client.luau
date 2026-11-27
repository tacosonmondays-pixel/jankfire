--!strict
-- ZOMBIES: the BRIEFING's screen (27 Nov 2026; roblox/docs/ZOMBIES.md 4.14; the server side: server/ZombieBrief.luau).
-- The owner: "Can the cutscene static into like a green text pc code style menu? Thats where you select you weapons and
-- passives and stuff? There will be a cool weapon graphic that's like a green grid hologram thing?"
-- The intro's static switches on into a green CRT terminal (ZombieCine holds the film under it: ZmBriefUp): scanlines,
-- a faint flicker and a rolling bar, green monospace text typed out, a cursor. Functional words only. Left: the four
-- sidearms (ZM.BRIEF.sidearms) and the squad's picks; the middle: the picked sidearm as a hologram (a ViewportFrame:
-- see-through green, an outline, on a green grid with a ring, turning, a scan line sweeping it; all four built and
-- parked when it opens, so nothing builds on a click) and its plain stats; right: the passives (ZM.BRIEF.passives) and
-- what the picked one does; READY and the shared timer. It switches off as the server closes it (BriefT1).
-- Input: mouse (click), keyboard (W/S or arrows move, A/D or left/right change column, 1-4 the sidearm, Space picks,
-- Enter READY), a pad (Roblox's selection between the rows, A picks, the bumpers change column: Pad.MENUS.zmbrief),
-- touch (tap). MenuCursor "zmbrief" frees the mouse while it's up.
-- Sounds (recorded, the library's; store.json zm_term_*): the switch-on, key ticks under the typing, a pick, READY,
-- the switch-off.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local HttpService = game:GetService("HttpService")
local GuiService = game:GetService("GuiService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local ZM = require(Shared:WaitForChild("ZM"))
local Weapons = require(Shared:WaitForChild("Weapons"))
local WeaponModels = require(Shared:WaitForChild("WeaponModels"))
local J = script.Parent
local T = require(J:WaitForChild("Theme")) :: any
local Keys = require(J:WaitForChild("Keys")) :: any
local MenuCursor = require(J:WaitForChild("MenuCursor")) :: any
local okPad, Pad = pcall(require, J:WaitForChild("Pad"))
local okSfx, Sfx = pcall(require, J:WaitForChild("Sfx"))
local zr = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Zm") :: RemoteEvent
local me = Players.LocalPlayer
local W = Weapons.list :: any
local B = ZM.BRIEF

local G = Color3.fromRGB(96, 255, 140) -- (the phosphor)
local G_DIM = Color3.fromRGB(50, 160, 86)
local G_HOLO = Color3.fromRGB(70, 230, 120)
local BG = Color3.fromRGB(2, 10, 5)
local MONO = Font.new("rbxasset://fonts/families/RobotoMono.json", Enum.FontWeight.Regular)
local MONO_B = Font.new("rbxasset://fonts/families/RobotoMono.json", Enum.FontWeight.Bold)
local ON_T, OFF_T = 0.36, 0.35 -- (the switch-on; the switch-off, the server's SWITCH_OFF)

local function srv(): number return workspace:GetServerTimeNow() end
local function sfx(name: string, vol: number?)
	if okSfx and Sfx then pcall((Sfx :: any).play, name, nil, vol) end
end
local function arena(): Model?
	local n = me:GetAttribute("ZmArena")
	local a = if type(n) == "string" then workspace:FindFirstChild(n) else nil
	return if a and a:IsA("Model") then a else nil
end

-- ------------------------------------------------------------------ the screen
local gui = T.new("ScreenGui", { Name = "JankZmBrief", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 60, Enabled = false,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, me:WaitForChild("PlayerGui"))
local screen = T.new("Frame", { Name = "Screen", BackgroundColor3 = BG, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1) }, gui)
local root = T.scaled(screen)

local function lbl(parent: Instance, name: string, text: string, max: number, color: Color3?, font: Font?, align: Enum.TextXAlignment?,
	pos: UDim2, size: UDim2): TextLabel
	local l = T.new("TextLabel", {
		Name = name, BackgroundTransparency = 1, Text = text, TextColor3 = color or G, FontFace = font or MONO, TextScaled = true,
		TextXAlignment = align or Enum.TextXAlignment.Left, TextYAlignment = Enum.TextYAlignment.Center, Position = pos, Size = size,
		TextStrokeColor3 = G, TextStrokeTransparency = 0.9, -- (a faint phosphor halo)
	}, parent)
	T.new("UITextSizeConstraint", { MaxTextSize = max, MinTextSize = 6 }, l)
	return l
end
local function rule(y: number)
	T.new("Frame", { Name = "Rule", BackgroundColor3 = G_DIM, BackgroundTransparency = 0.35, BorderSizePixel = 0,
		Position = UDim2.fromScale(0.05, y), Size = UDim2.new(0.9, 0, 0, 2) }, root)
end

-- the header: what this is, the timer
local title = lbl(root, "Title", "> LOADOUT", 34, G, MONO_B, nil, UDim2.fromScale(0.05, 0.05), UDim2.fromScale(0.4, 0.05))
local timer = lbl(root, "Timer", "00:18", 34, G, MONO_B, Enum.TextXAlignment.Right, UDim2.fromScale(0.65, 0.05), UDim2.fromScale(0.3, 0.05))
rule(0.115)
rule(0.865)

-- a column of rows (buttons: the mouse, a tap, a pad's selection)
type Row = { b: TextButton, t: TextLabel, mark: TextLabel, id: string }
local function column(name: string, heading: string, x: number, y: number, w: number, h: number, ids: { string }, textOf: (string) -> string): (TextLabel, { Row })
	local head = lbl(root, name .. "Head", heading, 26, G_DIM, MONO_B, nil, UDim2.fromScale(x, y), UDim2.fromScale(w, 0.04))
	local box = T.new("Frame", { Name = name, BackgroundTransparency = 1, Position = UDim2.fromScale(x, y + 0.05), Size = UDim2.fromScale(w, h) }, root)
	local rows: { Row } = {}
	for i, id in ids do
		local b = T.new("TextButton", { Name = "Row_" .. id, AutoButtonColor = false, BackgroundColor3 = G, BackgroundTransparency = 1,
			BorderSizePixel = 0, Text = "", Position = UDim2.fromScale(0, (i - 1) / #ids), Size = UDim2.new(1, 0, 1 / #ids, -4), Selectable = true }, box)
		local mark = lbl(b, "Mark", ">", 26, G, MONO_B, nil, UDim2.fromScale(0.015, 0.1), UDim2.fromScale(0.07, 0.8))
		mark.Visible = false
		local t = lbl(b, "Text", textOf(id), 24, G, MONO, nil, UDim2.fromScale(0.09, 0.14), UDim2.fromScale(0.9, 0.72))
		table.insert(rows, { b = b, t = t, mark = mark, id = id })
	end
	return head, rows
end
local function sideText(id: string): string
	local i = table.find(B.sidearms, id) or 0
	return tostring(i) .. "  " .. string.upper((W[id] and W[id].name) or id)
end
local sideHead, sideRows = column("Side", "SIDEARM", 0.05, 0.15, 0.25, 0.30, B.sidearms, sideText)
local pasHead, pasRows = column("Pas", "PASSIVE", 0.70, 0.15, 0.25, 0.40, B.order, function(id: string): string return B.passives[id].name end)
local pasDesc = lbl(root, "PasDesc", "", 22, G_DIM, MONO, nil, UDim2.fromScale(0.70, 0.62), UDim2.fromScale(0.25, 0.12))
pasDesc.TextWrapped = true
pasDesc.TextYAlignment = Enum.TextYAlignment.Top

-- the squad: a name and READY, then what they picked
local squadHead = lbl(root, "SquadHead", "SQUAD", 26, G_DIM, MONO_B, nil, UDim2.fromScale(0.05, 0.53), UDim2.fromScale(0.25, 0.04))
local squadBox = T.new("Frame", { Name = "Squad", BackgroundTransparency = 1, Position = UDim2.fromScale(0.05, 0.58), Size = UDim2.fromScale(0.25, 0.26) }, root)
local squadLines: { { n: TextLabel, s: TextLabel, k: TextLabel } } = {}
for i = 1, 4 do
	local y = (i - 1) / 4
	local n = lbl(squadBox, "Name" .. i, "", 20, G, MONO_B, nil, UDim2.fromScale(0, y), UDim2.fromScale(0.7, 0.12))
	local s = lbl(squadBox, "State" .. i, "", 20, G, MONO_B, Enum.TextXAlignment.Right, UDim2.fromScale(0.7, y), UDim2.fromScale(0.3, 0.12))
	local k = lbl(squadBox, "Kit" .. i, "", 17, G_DIM, MONO, nil, UDim2.fromScale(0.04, y + 0.115), UDim2.fromScale(0.96, 0.1))
	table.insert(squadLines, { n = n, s = s, k = k })
end

-- the middle: the hologram, the name, the stats
local vp = T.new("ViewportFrame", { Name = "Holo", BackgroundTransparency = 1, Position = UDim2.fromScale(0.31, 0.13), Size = UDim2.fromScale(0.38, 0.46),
	Ambient = Color3.fromRGB(70, 170, 100), LightColor = Color3.fromRGB(170, 255, 195), LightDirection = Vector3.new(-0.5, -1, -0.7) }, root)
local vcam = Instance.new("Camera")
vcam.FieldOfView = 30
vcam.CFrame = CFrame.lookAt(Vector3.new(0, 2.2, 8.6), Vector3.new(0, 0.05, 0))
vcam.Parent = vp
vp.CurrentCamera = vcam
local gunName = lbl(root, "GunName", "", 34, G, MONO_B, Enum.TextXAlignment.Center, UDim2.fromScale(0.31, 0.595), UDim2.fromScale(0.38, 0.05))
local statBox = T.new("Frame", { Name = "Stats", BackgroundTransparency = 1, Position = UDim2.fromScale(0.33, 0.655), Size = UDim2.fromScale(0.34, 0.195) }, root)
local STAT_NAMES = { "DAMAGE", "FIRE RATE", "MAGAZINE", "RELOAD", "RANGE", "SPARE ROUNDS" }
local statRows: { { name: TextLabel, segs: { Frame }, v: TextLabel } } = {}
for i, nm in STAT_NAMES do
	local y = (i - 1) / #STAT_NAMES
	local h = 1 / #STAT_NAMES
	local name = lbl(statBox, "S" .. i, nm, 19, G_DIM, MONO, nil, UDim2.fromScale(0, y + h * 0.1), UDim2.fromScale(0.36, h * 0.8))
	local segs = {}
	for k = 1, 10 do
		table.insert(segs, T.new("Frame", { Name = "Seg" .. k, BorderSizePixel = 0, BackgroundColor3 = G, BackgroundTransparency = 0.85,
			Position = UDim2.fromScale(0.38 + (k - 1) * 0.038, y + h * 0.25), Size = UDim2.fromScale(0.03, h * 0.5) }, statBox))
	end
	local v = lbl(statBox, "V" .. i, "", 19, G, MONO_B, Enum.TextXAlignment.Right, UDim2.fromScale(0.78, y + h * 0.1), UDim2.fromScale(0.22, h * 0.8))
	table.insert(statRows, { name = name, segs = segs, v = v })
end

-- the bottom: the prompt line, the keys, READY
local prompt = lbl(root, "Prompt", "> ", 24, G, MONO, nil, UDim2.fromScale(0.05, 0.882), UDim2.fromScale(0.6, 0.045))
local hint = lbl(root, "Hint", "", 18, G_DIM, MONO, nil, UDim2.fromScale(0.05, 0.93), UDim2.fromScale(0.6, 0.032))
local ready = T.new("TextButton", { Name = "Ready", AutoButtonColor = false, BackgroundColor3 = G, BackgroundTransparency = 1, BorderSizePixel = 0,
	Text = "", Position = UDim2.fromScale(0.70, 0.882), Size = UDim2.fromScale(0.25, 0.075), Selectable = true }, root)
T.new("UIStroke", { Color = G, Thickness = 2, ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, ready)
local readyT = lbl(ready, "Text", "READY", 30, G, MONO_B, Enum.TextXAlignment.Center, UDim2.fromScale(0.04, 0.12), UDim2.fromScale(0.92, 0.76))

-- the tube: scanlines, the rolling bar, the flicker, the dark edges, then the switch's shutters and line on top
local fx = T.new("Frame", { Name = "Tube", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = 5 }, screen)
for i = 0, 179 do
	T.new("Frame", { Name = "Scan", BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 0.72, BorderSizePixel = 0,
		Position = UDim2.fromScale(0, i / 180), Size = UDim2.fromScale(1, 1 / 540), ZIndex = 5 }, fx)
end
local roll = T.new("Frame", { Name = "Roll", BackgroundColor3 = G, BackgroundTransparency = 0, BorderSizePixel = 0, Size = UDim2.fromScale(1, 0.16), ZIndex = 5 }, fx)
T.new("UIGradient", { Rotation = 90, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0.95), NumberSequenceKeypoint.new(1, 1) }) }, roll)
local flick = T.new("Frame", { Name = "Flicker", BackgroundColor3 = G, BackgroundTransparency = 1, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 5 }, fx)
for _, e in { { 0, 0, 1, 0.16, 90, false }, { 0, 0.84, 1, 0.16, 90, true }, { 0, 0, 0.1, 1, 0, false }, { 0.9, 0, 0.1, 1, 0, true } } do
	local f = T.new("Frame", { Name = "Edge", BackgroundColor3 = Color3.new(0, 0, 0), BorderSizePixel = 0,
		Position = UDim2.fromScale(e[1] :: number, e[2] :: number), Size = UDim2.fromScale(e[3] :: number, e[4] :: number), ZIndex = 5 }, fx)
	local a0, a1 = 0.35, 1
	if e[6] then a0, a1 = 1, 0.35 end
	T.new("UIGradient", { Rotation = e[5] :: number, Transparency = NumberSequence.new(a0, a1) }, f)
end
local shutTop = T.new("Frame", { Name = "ShutTop", BackgroundColor3 = Color3.new(0, 0, 0), BorderSizePixel = 0, Size = UDim2.fromScale(1, 0.5), ZIndex = 8 }, screen)
local shutBot = T.new("Frame", { Name = "ShutBot", BackgroundColor3 = Color3.new(0, 0, 0), BorderSizePixel = 0, AnchorPoint = Vector2.new(0, 1),
	Position = UDim2.fromScale(0, 1), Size = UDim2.fromScale(1, 0.5), ZIndex = 8 }, screen)
local line = T.new("Frame", { Name = "Line", BackgroundColor3 = Color3.fromRGB(210, 255, 220), BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
	Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.new(0, 0, 0, 3), ZIndex = 9 }, screen)
-- (27 Nov 2026, the owner's order: the briefing is the lobby terminal's own screen. the film pushes into it till it fills
-- the view (ZombieCine), this fades in over that picture, and at the close fades back to it: the film powers it down
-- in the world. the shutters and the line stay shut away)
local veil = T.new("Frame", { Name = "Veil", BackgroundColor3 = Color3.fromRGB(12, 44, 22), BorderSizePixel = 0, BackgroundTransparency = 1,
	Size = UDim2.fromScale(1, 1), ZIndex = 9 }, screen)

-- ------------------------------------------------------------------ the hologram (built when it opens, parked)
local GRID_Y = -1.25
local holoParts: { BasePart } = {}
local function holoPart(size: Vector3, cf: CFrame, alpha: number, color: Color3?): Part
	local p = Instance.new("Part")
	p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch, p.CastShadow = true, false, false, false, false
	p.Material = Enum.Material.SmoothPlastic
	p.Color = color or G
	p.Transparency = alpha
	p.Size = size
	p.CFrame = cf
	p.Parent = vp
	table.insert(holoParts, p)
	return p
end
do
	for i = -5, 5 do
		holoPart(Vector3.new(0.025, 0.01, 8), CFrame.new(i * 0.8, GRID_Y, 0), 0.55)
		holoPart(Vector3.new(8, 0.01, 0.025), CFrame.new(0, GRID_Y, i * 0.8), 0.55)
	end
	for k = 0, 39 do
		local a = k / 40 * math.pi * 2
		holoPart(Vector3.new(0.5, 0.012, 0.05), CFrame.new(0, GRID_Y + 0.01, 0) * CFrame.Angles(0, -a, 0) * CFrame.new(0, 0, -3.1) * CFrame.Angles(0, math.pi / 2, 0), 0.3)
	end
end
local sweep = holoPart(Vector3.new(5.2, 0.03, 2.4), CFrame.new(0, 0, 0), 0.72, Color3.fromRGB(190, 255, 210))
local PARK = CFrame.new(0, -500, 0)
local holo: { [string]: { m: Model, off: CFrame } | false } = {}
local function holoOf(id: string): { m: Model, off: CFrame }?
	local h = holo[id]
	if h ~= nil then return if h then h else nil end
	local ok, built = pcall(WeaponModels.build, id, 1)
	if not ok or not built then holo[id] = false; return nil end
	local m = built :: Model
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored, d.CanCollide, d.CanQuery, d.CanTouch, d.CastShadow = true, false, false, false, false
			d.Material = Enum.Material.SmoothPlastic
			d.Color = G_HOLO
			d.Reflectance = 0
			d.Transparency = if d.Transparency >= 0.95 then 1 else 0.3
			if d:IsA("MeshPart") then pcall(function() (d :: any).TextureID = "" end) end
		elseif d:IsA("SurfaceAppearance") or d:IsA("Decal") or d:IsA("Texture") or d:IsA("ParticleEmitter") or d:IsA("Light")
			or d:IsA("Beam") or d:IsA("Trail") or d:IsA("Highlight") or d:IsA("Script") or d:IsA("LocalScript") then
			d:Destroy()
		end
	end
	local _, size = m:GetBoundingBox()
	local long = math.max(size.X, size.Y, size.Z)
	if long > 0 then pcall(function() m:ScaleTo(m:GetScale() * (4.2 / long)) end) end
	local bb = m:GetBoundingBox()
	local off = m:GetPivot():ToObjectSpace(bb) -- (the box's centre from the pivot: it turns about its middle)
	local hl = Instance.new("Highlight")
	hl.FillTransparency = 1
	hl.OutlineColor = G
	hl.OutlineTransparency = 0.1
	hl.DepthMode = Enum.HighlightDepthMode.Occluded
	hl.Adornee = m
	hl.Parent = m
	m:PivotTo(PARK)
	m.Parent = vp
	local rec = { m = m, off = off }
	holo[id] = rec
	return rec
end

-- ------------------------------------------------------------------ the stats (plain, from the weapon's own numbers)
local function statsOf(id: string): { { fill: number, v: string } }
	local w = W[id] or {}
	local dmg = if id == "revolver" then ZM.R.revolverDmg else (w.dmg or 0)
	local pel = w.pellets or 1
	local hands = w.hands or 1
	local mag = w.mag or 0
	local spare = math.max(0, (ZM.ammo(id) or 0) - mag)
	local function f(x: number, top: number): number return math.clamp(x / top, 0, 1) end
	local function num(x: number): string return if math.abs(x - math.floor(x)) < 0.05 then tostring(math.floor(x + 0.5)) else string.format("%.1f", x) end
	return {
		{ fill = f(dmg * pel, 60), v = if pel > 1 then pel .. " x " .. num(dmg) else num(dmg) },
		{ fill = f((w.rate or 1) * hands, 12), v = num(w.rate or 1) .. "/s" .. (if hands > 1 then " x2" else "") },
		{ fill = f(mag * hands, 24), v = if hands > 1 then mag .. " x2" else tostring(mag) },
		{ fill = math.clamp(1 - ((w.reload or 2) - 1) / 2, 0.05, 1), v = string.format("%.1f s", w.reload or 0) },
		{ fill = f(w.range or 0, 750), v = tostring(math.floor((w.range or 0) + 0.5)) },
		{ fill = f(spare, 260), v = tostring(spare) },
	}
end

-- ------------------------------------------------------------------ the typing
type Typing = { l: TextLabel, at: number, cps: number }
local typing: { Typing } = {}
local function typeIn(l: TextLabel, delay: number, cps: number?)
	l.MaxVisibleGraphemes = 0
	for i = #typing, 1, -1 do if typing[i].l == l then table.remove(typing, i) end end
	table.insert(typing, { l = l, at = os.clock() + delay, cps = cps or 75 })
end
local function setTyped(l: TextLabel, text: string, cps: number?)
	if l.Text == text then return end
	l.Text = text
	typeIn(l, 0, cps or 120)
end
local tickT = 0
local function typeStep()
	local any = false
	local t = os.clock()
	for i = #typing, 1, -1 do
		local x = typing[i]
		local n = math.floor((t - x.at) * x.cps)
		local len = utf8.len(x.l.Text) or #x.l.Text
		if n >= len then
			x.l.MaxVisibleGraphemes = -1
			table.remove(typing, i)
		else
			x.l.MaxVisibleGraphemes = math.max(0, n)
			if n > 0 then any = true end
		end
	end
	if any and t >= tickT then tickT = t + 0.055; sfx("zm_term_key", 0.5) end
end

-- ------------------------------------------------------------------ the state
local open, closing = false, false
local openT = 0
local mySide = B.sidearms[1]
local myPas: string? = nil
local myReady = false
local col, idx = 1, { 1, 1, 1 } -- (the keyboard's cursor: 1 sidearms, 2 passives, 3 READY)
local promptText = ""
local lastSquad = ""
local function say(text: string)
	promptText = text
	setTyped(prompt, "> " .. text, 140)
end
local function rowsOf(c: number): { Row }? return if c == 1 then sideRows elseif c == 2 then pasRows else nil end
local function focusButton(): GuiButton
	local rs = rowsOf(col)
	return if rs then rs[idx[col]].b else ready
end
local function hints()
	if Keys.isTouch() then hint.Text = ""
	elseif okPad and Pad and (Pad :: any).on and (Pad :: any).on() then hint.Text = "A PICK    LB RB COLUMN"
	else hint.Text = "W S MOVE    A D COLUMN    SPACE PICK    ENTER READY" end
end
local function paint()
	for i, r in sideRows do
		local picked = r.id == mySide
		local focus = col == 1 and idx[1] == i
		r.b.BackgroundTransparency = if picked then 0.05 elseif focus then 0.86 else 1
		r.t.TextColor3 = if picked then BG else G
		r.mark.Visible = focus and not picked
	end
	for i, r in pasRows do
		local picked = r.id == myPas
		local focus = col == 2 and idx[2] == i
		r.b.BackgroundTransparency = if picked then 0.05 elseif focus then 0.86 else 1
		r.t.TextColor3 = if picked then BG else G
		r.mark.Visible = focus and not picked
	end
	ready.BackgroundTransparency = if myReady then 0.05 elseif col == 3 then 0.86 else 1
	readyT.TextColor3 = if myReady then BG else G
end
local function showGun(id: string)
	setTyped(gunName, string.upper((W[id] and W[id].name) or id), 90)
	for i, s in statsOf(id) do
		local row = statRows[i]
		setTyped(row.v, s.v, 90)
		local lit = math.max(1, math.floor(s.fill * 10 + 0.5))
		for k, seg in row.segs do seg.BackgroundTransparency = if k <= lit then 0.1 else 0.85 end
	end
end
local function showPas(id: string?)
	local d = if id then B.passives[id] else nil
	setTyped(pasDesc, if d then string.upper(d.desc) else "", 110)
end
local function pickSide(id: string)
	if not open or closing or myReady or not table.find(B.sidearms, id) then return end
	if mySide ~= id then
		mySide = id
		zr:FireServer({ k = "bpick", w = id })
		sfx("zm_term_sel", 0.8)
		say("SIDEARM  " .. string.upper(W[id].name))
		showGun(id)
	end
	col, idx[1] = 1, table.find(B.sidearms, id) or 1
	paint()
end
local function pickPas(id: string)
	if not open or closing or myReady or not B.passives[id] then return end
	if myPas ~= id then
		myPas = id
		zr:FireServer({ k = "bpick", p = id })
		sfx("zm_term_sel", 0.8)
		say("PASSIVE  " .. B.passives[id].name)
		showPas(id)
	end
	col, idx[2] = 2, table.find(B.order, id) or 1
	paint()
end
local function doReady()
	if not open or closing or myReady then return end
	myReady = true
	zr:FireServer({ k = "bready" })
	sfx("zm_term_ready", 0.9)
	say("READY")
	col = 3
	paint()
end
for _, r in sideRows do
	r.b.Activated:Connect(function() pickSide(r.id) end)
	r.b.MouseEnter:Connect(function() if open and not myReady then col, idx[1] = 1, table.find(B.sidearms, r.id) or 1; paint() end end)
end
for _, r in pasRows do
	r.b.Activated:Connect(function() pickPas(r.id) end)
	r.b.MouseEnter:Connect(function() if open and not myReady then col, idx[2] = 2, table.find(B.order, r.id) or 1; paint() end end)
end
ready.Activated:Connect(doReady)
ready.MouseEnter:Connect(function() if open and not myReady then col = 3; paint() end end)

local function move(d: number)
	local rs = rowsOf(col)
	if not rs then return end
	idx[col] = math.clamp(idx[col] + d, 1, #rs)
	sfx("zm_term_key", 0.45)
	paint()
end
local function switchCol(d: number)
	col = math.clamp(col + d, 1, 3)
	sfx("zm_term_key", 0.45)
	paint()
	if GuiService.SelectedObject then GuiService.SelectedObject = focusButton() end
end
UIS.InputBegan:Connect(function(io: InputObject, gp: boolean)
	if not open or closing or io.UserInputType ~= Enum.UserInputType.Keyboard then return end
	local k = io.KeyCode
	if k == Enum.KeyCode.Return or k == Enum.KeyCode.KeypadEnter then doReady(); return end
	if gp or myReady then return end
	if k == Enum.KeyCode.W or k == Enum.KeyCode.Up then move(-1)
	elseif k == Enum.KeyCode.S or k == Enum.KeyCode.Down then move(1)
	elseif k == Enum.KeyCode.A or k == Enum.KeyCode.Left then switchCol(-1)
	elseif k == Enum.KeyCode.D or k == Enum.KeyCode.Right then switchCol(1)
	elseif k == Enum.KeyCode.Space then
		if col == 1 then pickSide(B.sidearms[idx[1]]) elseif col == 2 then pickPas(B.order[idx[2]]) else doReady() end
	else
		local n = ({ [Enum.KeyCode.One] = 1, [Enum.KeyCode.Two] = 2, [Enum.KeyCode.Three] = 3, [Enum.KeyCode.Four] = 4 } :: any)[k]
		if n and B.sidearms[n] then pickSide(B.sidearms[n]) end
	end
end)
-- a pad: Roblox's own selection moves between the rows (PadNav keeps it in this screen), the bumpers change column
if okPad and Pad then
	local P = Pad :: any
	if type(P.MENUS) ~= "table" then P.MENUS = {} end
	P.MENUS.zmbrief = { gui = "JankZmBrief", tabs = function(dir: number) switchCol(dir); GuiService.SelectedObject = focusButton() end }
end

-- the squad's column, from the server's rows
local function squad(a: Model)
	local raw = a:GetAttribute("BriefSquad")
	if type(raw) ~= "string" or raw == lastSquad then return end
	lastSquad = raw
	local ok, rows = pcall(HttpService.JSONDecode, HttpService, raw)
	if not ok or type(rows) ~= "table" then return end
	local humans, readyN = 0, 0
	for i, line in squadLines do
		local r = rows[i]
		if r then
			local w = W[r.w]
			local ps = B.passives[r.p]
			setTyped(line.n, string.upper(tostring(r.n)), 120)
			setTyped(line.s, if r.r then "READY" else "...", 120)
			setTyped(line.k, string.upper((w and w.name) or tostring(r.w)) .. "  /  " .. (if ps then ps.name else "-"), 120)
			if not r.bot then humans += 1; if r.r then readyN += 1 end end
		else
			line.n.Text, line.s.Text, line.k.Text = "", "", ""
		end
	end
	readyT.Text = if myReady then string.format("READY  %d/%d", readyN, humans) else "READY"
end

-- ------------------------------------------------------------------ open / close
local function show(a: Model)
	open, closing = true, false
	openT = os.clock()
	gui.Enabled = true
	myReady = false
	lastSquad = ""
	mySide = if type(me:GetAttribute("ZmSidearm")) == "string" then me:GetAttribute("ZmSidearm") :: string else B.sidearms[1]
	myPas = if type(me:GetAttribute("ZmPassive")) == "string" then me:GetAttribute("ZmPassive") :: string else nil
	col, idx = 1, { table.find(B.sidearms, mySide) or 1, if myPas then table.find(B.order, myPas) or 1 else 1, 1 }
	MenuCursor.set("zmbrief", true, function() return open end)
	for _, id in B.sidearms do holoOf(id) end -- (all four now, parked: nothing builds on a click)
	-- in from the terminal's own picture (the film is already in it: on, no switch)
	shutTop.Size = UDim2.fromScale(1, 0); shutBot.Size = UDim2.fromScale(1, 0)
	line.BackgroundTransparency = 1
	veil.BackgroundTransparency = 0
	-- the words, typed in order
	readyT.Text = "READY"
	prompt.Text = ""
	typeIn(title, ON_T, 60)
	typeIn(timer, ON_T + 0.1, 60)
	typeIn(sideHead, ON_T + 0.2, 60)
	for i, r in sideRows do typeIn(r.t, ON_T + 0.3 + i * 0.07, 70) end
	typeIn(pasHead, ON_T + 0.35, 60)
	for i, r in pasRows do typeIn(r.t, ON_T + 0.45 + i * 0.07, 70) end
	typeIn(squadHead, ON_T + 0.7, 60)
	for i, s in statRows do typeIn(s.name, ON_T + 0.5 + i * 0.05, 80) end
	typeIn(readyT, ON_T + 0.9, 60)
	gunName.Text = ""
	for _, s in statRows do s.v.Text = "" end
	pasDesc.Text = ""
	task.delay(ON_T + 0.45, function()
		if not open then return end
		showGun(mySide)
		showPas(myPas)
		say(if myPas then "SIDEARM AND PASSIVE SET" else "PICK A SIDEARM AND A PASSIVE")
	end)
	hints()
	typeIn(hint, ON_T + 1.0, 90)
	paint()
	squad(a)
	if okPad and Pad and (Pad :: any).on and (Pad :: any).on() then
		task.delay(ON_T, function() if open then GuiService.SelectedObject = focusButton() end end)
	end
end
local function hide()
	open, closing = false, false
	gui.Enabled = false
	MenuCursor.set("zmbrief", false)
	if GuiService.SelectedObject and GuiService.SelectedObject:IsDescendantOf(gui) then GuiService.SelectedObject = nil end
	table.clear(typing)
	for _, h in holo do if h then h.m:PivotTo(PARK) end end
end

-- the server's word on the picks (it checks them)
me:GetAttributeChangedSignal("ZmSidearm"):Connect(function()
	local w = me:GetAttribute("ZmSidearm")
	if open and type(w) == "string" and w ~= mySide then mySide = w; showGun(w); paint() end
end)
me:GetAttributeChangedSignal("ZmPassive"):Connect(function()
	local p = me:GetAttribute("ZmPassive")
	if open and type(p) == "string" and p ~= myPas then myPas = p; showPas(p); paint() end
end)

local yaw = 0
RunService.RenderStepped:Connect(function(dt: number)
	local a = arena()
	local want, b1 = false, nil
	if a and me:GetAttribute("ZmOn") == true then
		local b0 = a:GetAttribute("BriefT0")
		b1 = a:GetAttribute("BriefT1")
		if type(b0) == "number" and not (type(b1) == "number" and srv() >= b1) then
			local filmUp = me:GetAttribute("ZmFilm") == true
			-- (the film holds under it: ZombieCine says when; no film here (it started too late) = straight in)
			want = if filmUp then me:GetAttribute("ZmBriefUp") == true else (srv() >= b0 and a:GetAttribute("St") == "pre")
		end
	end
	if want and not open and a then show(a) elseif not want and open then hide() end
	if not open or not a then return end
	local t = os.clock()
	-- in from the terminal's picture, and back to it at the close (the film powers it down in the world)
	local u = (t - openT) / 0.25
	local off = if type(b1) == "number" then math.clamp(1 - (b1 - srv()) / OFF_T, 0, 1) else 0
	if off > 0 and not closing then closing = true; MenuCursor.set("zmbrief", false) end
	veil.BackgroundTransparency = if off > 0 then 1 - off else math.clamp(u, 0, 1)
	-- the tube: a flicker, the rolling bar
	flick.BackgroundTransparency = 0.955 + math.random() * 0.045
	roll.Position = UDim2.fromScale(0, ((t * 0.14) % 1.3) - 0.16)
	-- the timer (it blinks in its last 5 s), the cursor at the prompt
	local bEnd = a:GetAttribute("BriefEnd")
	local left = if type(bEnd) == "number" then math.max(0, math.ceil(bEnd - srv())) else 0
	local tt = string.format("00:%02d", math.min(left, 99))
	if timer.Text ~= tt then timer.Text = tt; if left <= 5 and left > 0 then sfx("zm_term_key", 0.6) end end
	timer.TextTransparency = if left <= 5 and (t % 0.6) > 0.3 then 0.6 else 0
	local cursorOn = (t % 1.0) < 0.55
	local want2 = "> " .. promptText .. (if cursorOn then "_" else " ")
	if prompt.MaxVisibleGraphemes == -1 and prompt.Text ~= want2 then prompt.Text = want2 end
	typeStep()
	squad(a)
	-- a pad's selection is the cursor too
	local sel = GuiService.SelectedObject
	if sel and sel:IsDescendantOf(gui) then
		for i, r in sideRows do if r.b == sel and (col ~= 1 or idx[1] ~= i) then col, idx[1] = 1, i; paint() end end
		for i, r in pasRows do if r.b == sel and (col ~= 2 or idx[2] ~= i) then col, idx[2] = 2, i; paint() end end
		if sel == ready and col ~= 3 then col = 3; paint() end
	end
	-- the hologram: the picked one turns on the grid; the scan line sweeps up it
	yaw += dt * 0.6
	for id, h in holo do
		if h then
			if id == mySide then
				h.m:PivotTo(CFrame.new(0, 0.15, 0) * CFrame.Angles(0, yaw + math.pi / 2, 0) * CFrame.Angles(0, 0, math.rad(4) * math.sin(t * 0.9)) * h.off:Inverse())
			elseif h.m:GetPivot().Position.Y > -400 then
				h.m:PivotTo(PARK)
			end
		end
	end
	local sw = (t * 0.55) % 1
	sweep.CFrame = CFrame.new(0, GRID_Y + 0.05 + sw * 2.9, 0)
	sweep.Transparency = 0.62 + 0.3 * sw
end)
