-- THE OPENING (client): a Crate, Duffel Bag or Spray Can drops in front of you onto the ground with a weighty bounce
-- and the camera eases round to it; it rattles, the lid / zip / cap pops; a reel of cards spins over the blurred world
-- (CS:GO-style, ours: our cards, our timing), slows with a tick per card and lands on what you got; then the prize
-- rises out of the open container and turns in front of you, on your own gun for a wrap or a hat, with EQUIP, OPEN
-- ANOTHER and DONE. SKIP (space) jumps ahead: the drop and pop are cut, the reel lands at once.
-- the server rolls (Loot.luau); this only shows what it said. the shop calls it:
--   local res = Loot:InvokeServer("open", kind)        -- kind = "crate" | "bag" | "spray"
--   if res.ok then local how = LootOpening.play(kind, res, { quick = false, again = true }) end
-- play() YIELDS until the player closes the reveal and returns "done" or "again" (OPEN ANOTHER). LootOpening.busy().
-- several at once (Loot "open", kind, 5 or 10: res.prizes): a row of containers, a quick reel each, then a grid of
-- everything, rarest first, each with EQUIP. Opening.show(data) draws someone ELSE's opening for a bystander (the
-- LootShow event: the container, the pop, the best prize over it with a sign; no reel).
-- it takes the camera and hides every other ScreenGui while it runs, and gives both back as they were.
-- the containers are ReplicatedStorage.JankfireLoot.<kind> (Blender, tools/roblox/loot_models.py, PolishBackup.LootImport);
-- a plain stand-in is built here if they aren't there. look: Theme.luau (dark cards, one amber accent), rarity colours
-- from Shared.LootTable (muted).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UIS = game:GetService("UserInputService")
local ContextActionService = game:GetService("ContextActionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local LootTable = require(Shared:WaitForChild("LootTable"))
local LootFloor = require(Shared:WaitForChild("LootFloor"))
local Roster = require(Shared:WaitForChild("Roster"))
local WeaponModels = require(Shared:WaitForChild("WeaponModels"))
local GunHats = require(Shared:WaitForChild("GunHats"))
local GunHatData = require(Shared:WaitForChild("GunHatData")) :: any
local T = require(script.Parent:WaitForChild("Theme"))
local Sfx = require(script.Parent:WaitForChild("Sfx"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local me = Players.LocalPlayer
local new = T.new
local WHITE = Color3.new(1, 1, 1)

local Opening = {}
local running = false
local current: any = nil -- (the opening that is playing: finish() reaches it)
function Opening.busy(): boolean return running end
-- end the opening from outside (the shop closing, a test): it skips to the end and play() returns `answer` ("done")
function Opening.finish(answer: string?)
	if current then current.result = answer or "done"; current.skip = true end
end

-- ---------------------------------------------------------------- timing (seconds)
local TIME = {
	fall = 0.42, bounce = 0.55, rattle = 0.8, pop = 0.5, -- the container
	spin = 6.2, spinQuick = 1.4, -- the reel
	land = 0.7, -- the winning card's moment before the reveal
	rise = 0.65, -- the prize coming up out of the container
}
local CARD_W, CARD_H, GAP = 176, 212, 12
local STEP = CARD_W + GAP

-- ---------------------------------------------------------------- little helpers
local function tw(o: Instance, t: number, props: { [string]: any }, style: Enum.EasingStyle?, dir: Enum.EasingDirection?): Tween
	local x = TweenService:Create(o, TweenInfo.new(t, style or Enum.EasingStyle.Quad, dir or Enum.EasingDirection.Out), props)
	x:Play()
	return x
end
local function rcol(r: string): Color3
	local e = LootTable.RARITY[r]
	return if e then e.color else T.MUTED
end
local function rname(r: string): string
	local e = LootTable.RARITY[r]
	return string.upper(if e then e.name else r)
end
-- the first of these sounds that has been uploaded (new loot sounds first, old ones as stand-ins)
local function snd(names: { string }, at: Vector3?, vol: number?, pitch: number?)
	local lib = ReplicatedStorage:FindFirstChild("JankfireSounds")
	for _, n in names do
		local s = lib and lib:FindFirstChild(n)
		if s and s:IsA("Sound") and s.SoundId ~= "" then pcall(Sfx.play, n, at, vol, pitch); return end
	end
end
local function easeOut(u: number, p: number): number u = math.clamp(u, 0, 1); return 1 - (1 - u) ^ p end
local function smooth(u: number): number u = math.clamp(u, 0, 1); return u * u * (3 - 2 * u) end

-- ---------------------------------------------------------------- the container (the Blender model, or a stand-in)
local STAND_IN = {
	crate = { size = Vector3.new(3.6, 2.2, 2.4), body = Color3.fromRGB(70, 75, 86), trim = Color3.fromRGB(46, 50, 58), accent = T.ACCENT },
	bag = { size = Vector3.new(3.8, 1.7, 1.8), body = Color3.fromRGB(86, 90, 74), trim = Color3.fromRGB(44, 46, 40), accent = T.ACCENT },
	spray = { size = Vector3.new(1.4, 3.2, 1.4), body = Color3.fromRGB(214, 218, 224), trim = Color3.fromRGB(60, 64, 72), accent = T.ACCENT },
}
local function part(m: Instance, name: string, size: Vector3, cf: CFrame, color: Color3, mat: Enum.Material?): Part
	return new("Part", { Name = name, Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, CastShadow = true,
		Size = size, CFrame = cf, Color = color, Material = mat or Enum.Material.SmoothPlastic,
		TopSurface = Enum.SurfaceType.Smooth, BottomSurface = Enum.SurfaceType.Smooth }, m)
end
local function standIn(kind: string): Model
	local d = STAND_IN[kind] or STAND_IN.crate
	local m = Instance.new("Model")
	m.Name = kind
	local s = d.size
	local lidH = if kind == "spray" then 0.7 else 0.35
	local body = part(m, "body", Vector3.new(s.X, s.Y - lidH, s.Z), CFrame.new(0, (s.Y - lidH) / 2, 0), d.body)
	part(m, "band", Vector3.new(s.X + 0.06, 0.22, s.Z + 0.06), CFrame.new(0, (s.Y - lidH) * 0.45, 0), d.trim)
	local lid = Instance.new("Model")
	lid.Name = if kind == "spray" then "Cap" elseif kind == "bag" then "Flap" else "Lid"
	local lp = part(lid, "lid", Vector3.new(s.X + 0.08, lidH, s.Z + 0.08), CFrame.new(0, s.Y - lidH / 2, 0), d.trim)
	part(lid, "latch", Vector3.new(0.5, 0.18, 0.12), CFrame.new(0, s.Y - lidH - 0.05, -s.Z / 2 - 0.08), d.accent)
	lid.PrimaryPart = lp
	lid:SetAttribute("Hinge", CFrame.new(0, s.Y - lidH / 2, s.Z / 2 + 0.04))
	lid.Parent = m
	local glow = part(m, "glow", Vector3.new(s.X * 0.9, 0.06, s.Z * 0.9), CFrame.new(0, s.Y - lidH - 0.02, 0), WHITE, Enum.Material.Neon)
	glow.Transparency = 1
	m.PrimaryPart = body
	m.WorldPivot = CFrame.identity
	m:SetAttribute("Height", s.Y)
	m:SetAttribute("Open", if kind == "spray" then "pop" elseif kind == "bag" then "flap" else "hinge")
	return m
end
-- a copy of the container, its pivot at the middle of its bottom face, every part quiet
local function container(kind: string): Model
	local lib = ReplicatedStorage:FindFirstChild("JankfireLoot")
	local t = lib and lib:FindFirstChild(kind)
	local m = if t and t:IsA("Model") then t:Clone() else standIn(kind)
	local low = math.huge
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
			if d.Name == "glow" then d.Transparency = 1 end -- (the light inside: on at the pop)
			local cf, sz = d.CFrame, d.Size
			low = math.min(low, cf.Position.Y - (math.abs(cf.RightVector.Y) * sz.X + math.abs(cf.UpVector.Y) * sz.Y + math.abs(cf.LookVector.Y) * sz.Z) / 2)
		end
	end
	-- the pivot is the middle of the bottom face (where it stands on the floor), set here on every copy: a Model's
	-- WorldPivot doesn't stick once it has a PrimaryPart, and the templates' pivots were their body's centre (the crate's
	-- ~1 stud up), so every container used to stand that far INTO the floor. (the template sits at its file's origin:
	-- x and z of the pivot are 0 there; the hinges in openBox are written in that frame)
	if low < math.huge then
		local cf = m:GetBoundingBox()
		local x = if math.abs(cf.Position.X) < 0.5 then 0 else cf.Position.X
		local z = if math.abs(cf.Position.Z) < 0.5 then 0 else cf.Position.Z
		local bottom = CFrame.new(x, low, z)
		local pp = m.PrimaryPart
		if pp then pp.PivotOffset = pp.CFrame:ToObjectSpace(bottom) else m.WorldPivot = bottom end
	end
	return m
end

-- ---------------------------------------------------------------- the prize models
-- which of your weapons wears the prize in the reveal: the one in your hands, else your primary (a hat: one that has a
-- seat for it)
local function loadoutIds(): { string }
	local out = {}
	for _, a in { "Loadout", "LoadoutNext" } do
		local s = me:GetAttribute(a)
		if type(s) == "string" then for id in string.gmatch(s, "[^,]+") do if not table.find(out, id) then table.insert(out, id) end end end
	end
	for _, id in { "ar", "redline", "katana" } do if not table.find(out, id) then table.insert(out, id) end end
	return out
end
local function showWeapon(item: any): string?
	-- (a wrap or a hat is won for one gun: that's the one it's shown on)
	local own = item.weapon and Roster.byId[item.weapon]
	if own and own.live and own.slot ~= "utility" then return item.weapon end
	local held = me:GetAttribute("Held")
	local list = loadoutIds()
	if type(held) == "string" then table.insert(list, 1, held) end
	for _, id in list do
		local e = Roster.byId[id]
		if e and e.live and e.slot ~= "utility" and id ~= "shredder" then
			if item.type ~= "hat" or GunHatData.SPOTS == nil or GunHatData.SPOTS[id] ~= nil then return id end
		end
	end
	return "ar"
end
-- the weapon wearing the prize, about 4.6 studs long, pivot at its middle; returns the model and the weapon id
local function prizeModel(item: any): (Model?, string?)
	local wid: string?
	local m: Model?
	if item.type == "skin" then
		wid = (LootTable.SKINS[item.id] or {})[3]
		if wid then m = WeaponModels.build(wid, 3, item.id) end
		if not m then
			local lib = ReplicatedStorage:FindFirstChild("JankfireSkins")
			local t = lib and lib:FindFirstChild(item.id)
			if t and t:IsA("Model") then m = t:Clone() end
		end
	else
		wid = showWeapon(item)
		m = WeaponModels.build(wid :: string, 3)
	end
	if not m then return nil, wid end
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.CastShadow = false end
	end
	if item.type == "wrap" then
		pcall(WeaponModels.wrap, m, item.id, "full")
	end
	local _, size = m:GetBoundingBox()
	local hm: Model? = nil
	if item.type == "hat" and wid then
		local ok, h = pcall(GunHats.attach, m, wid, item.id, 3, true, 2.4) -- (bigger than in the hand: it's the star here)
		if ok then hm = h end
	end
	local long = math.max(size.X, size.Y, size.Z)
	if long > 1e-3 then pcall(function() m:ScaleTo(m:GetScale() * (4.6 / long)) end) end
	local cf = m:GetBoundingBox()
	m.WorldPivot = cf
	return m, wid
end

-- ---------------------------------------------------------------- card pictures
local function wrapPicture(parent: GuiObject, id: string)
	local lib = ReplicatedStorage:FindFirstChild("JankfireWraps")
	local sa = lib and lib:FindFirstChild(id)
	local img = nil
	if sa and sa:IsA("SurfaceAppearance") then
		local ok, v = pcall(function() return (sa :: any).ColorMap end)
		if ok and type(v) == "string" and v ~= "" then img = v end
	end
	if img then
		new("ImageLabel", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Image = img, ScaleType = Enum.ScaleType.Tile,
			TileSize = UDim2.fromOffset(120, 120) }, parent)
		return
	end
	-- a colour wrap: its palette as bands (as the loadout's chips draw it)
	local w = Roster.wrapById[id]
	local pal = if w and #w.pal > 0 then w.pal else { Color3.fromRGB(120, 124, 132) }
	local f = new("Frame", { BackgroundColor3 = WHITE, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1) }, parent)
	if #pal == 1 then f.BackgroundColor3 = pal[1]; return end
	local kp = {}
	local n = if w and w.pat == "fade" then #pal else 6
	for i = 1, n do
		local c = pal[(i - 1) % #pal + 1]
		if w and w.pat == "fade" then
			table.insert(kp, ColorSequenceKeypoint.new((i - 1) / (n - 1), c))
		else
			local a, b = (i - 1) / n, i / n
			table.insert(kp, ColorSequenceKeypoint.new(if i == 1 then 0 else a + 0.001, c))
			table.insert(kp, ColorSequenceKeypoint.new(if i == n then 1 else b, c))
		end
	end
	new("UIGradient", { Color = ColorSequence.new(kp), Rotation = if w and w.pat == "fade" then 0 else 55 }, f)
end
local function modelPicture(parent: GuiObject, m: Model?)
	if not m then return end
	local vp = new("ViewportFrame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Ambient = Color3.fromRGB(150, 153, 162),
		LightColor = Color3.fromRGB(255, 248, 240), LightDirection = Vector3.new(-0.5, -1, -0.7) }, parent)
	local cam = new("Camera", { FieldOfView = 30 }, vp)
	vp.CurrentCamera = cam
	for _, d in m:GetDescendants() do if d:IsA("BasePart") then d.Anchored = true end end
	m.Parent = vp
	local cf, size = m:GetBoundingBox()
	local r = size.Magnitude / 2
	local dir = (Vector3.new(0.8, 0.5, -1)).Unit
	cam.CFrame = CFrame.lookAt(cf.Position + dir * (r / math.tan(math.rad(15)) * 1.05), cf.Position)
end
local function cardPicture(parent: GuiObject, item: any)
	if item.type == "wrap" then wrapPicture(parent, item.id)
	elseif item.type == "hat" then
		local t = GunHats.template(item.id)
		modelPicture(parent, if t then t:Clone() else nil)
	elseif item.type == "skin" then
		local lib = ReplicatedStorage:FindFirstChild("JankfireSkins")
		local t = lib and lib:FindFirstChild(item.id)
		modelPicture(parent, if t and t:IsA("Model") then t:Clone() else nil)
	else
		-- (a player card's look: its own module draws it, if it can)
		local cm = LootTable.cardStyles()
		if cm and type(cm.picture) == "function" then pcall(cm.picture, item.type, item.id, parent) end
	end
end

-- one card of the reel: a dark plate, the picture, a soft wash of the rarity colour from the bottom, the name, a bar
local function card(parent: Instance, item: any, x: number): Frame
	local c = new("Frame", { Name = "Card", BackgroundColor3 = T.CARD, BorderSizePixel = 0, Position = UDim2.fromOffset(x, 0),
		Size = UDim2.fromOffset(CARD_W, CARD_H) }, parent)
	T.corner(c, 6)
	T.edge(c)
	local col = rcol(item.rarity)
	local pic = new("Frame", { Name = "Pic", BackgroundColor3 = Color3.fromRGB(20, 22, 27), BorderSizePixel = 0, Position = UDim2.fromOffset(8, 8),
		Size = UDim2.fromOffset(CARD_W - 16, CARD_H - 72), ClipsDescendants = true }, c)
	T.corner(pic, 4)
	local wash = new("Frame", { Name = "Wash", BackgroundColor3 = col, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 3 }, pic)
	new("UIGradient", { Rotation = -90, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.55), NumberSequenceKeypoint.new(0.45, 1), NumberSequenceKeypoint.new(1, 1) }) }, wash)
	cardPicture(pic, item)
	local nm = new("TextLabel", { BackgroundTransparency = 1, Position = UDim2.fromOffset(10, CARD_H - 60), Size = UDim2.fromOffset(CARD_W - 20, 24),
		FontFace = T.FONT_BOLD, TextSize = 17, Text = item.name or item.id, TextColor3 = T.TEXT, TextXAlignment = Enum.TextXAlignment.Left,
		TextTruncate = Enum.TextTruncate.AtEnd }, c)
	nm.Name = "Name"
	new("TextLabel", { BackgroundTransparency = 1, Position = UDim2.fromOffset(10, CARD_H - 36), Size = UDim2.fromOffset(CARD_W - 20, 18),
		FontFace = T.FONT, TextSize = 13, TextTruncate = Enum.TextTruncate.AtEnd,
		Text = (if item.weapon and Roster.byId[item.weapon] then string.upper(Roster.byId[item.weapon].name)
			elseif item.type ~= "skin" and LootTable.gunless(item.type) then "PLAYER CARD"
			else string.upper(LootTable.TYPE_NAMES[item.type] or item.type)) .. "  ·  " .. rname(item.rarity),
		TextColor3 = T.MUTED, TextXAlignment = Enum.TextXAlignment.Left }, c)
	local bar = new("Frame", { Name = "Bar", BackgroundColor3 = col, BorderSizePixel = 0, AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.new(0, 0, 1, 0), Size = UDim2.new(1, 0, 0, 5), ZIndex = 2 }, c)
	T.corner(bar, 2)
	new("Frame", { Name = "Dim", BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 1, BorderSizePixel = 0,
		Size = UDim2.fromScale(1, 1), ZIndex = 8 }, c)
	return c
end

-- ---------------------------------------------------------------- the screen
local function button(parent: Instance, text: string, main: boolean, pos: UDim2, size: UDim2): TextButton
	local b = new("TextButton", { AutoButtonColor = false, BackgroundColor3 = if main then T.ACCENT else T.CARD, BorderSizePixel = 0,
		Position = pos, Size = size, FontFace = T.FONT_BOLD, TextSize = math.floor(size.Y.Offset * 0.36), Text = text,
		TextColor3 = if main then T.INK else T.TEXT, ZIndex = 20 }, parent)
	T.corner(b)
	if not main then T.edge(b) end
	local base = b.BackgroundColor3
	b.MouseEnter:Connect(function() b.BackgroundColor3 = base:Lerp(WHITE, 0.14) end)
	b.MouseLeave:Connect(function() b.BackgroundColor3 = base end)
	return b
end

type Ui = { gui: ScreenGui, stage: Frame, scale: UIScale, title: TextLabel, odds: TextLabel, skip: TextButton,
	reel: CanvasGroup, strip: Frame, marker: Frame, flash: Frame, reveal: Frame, rName: TextLabel, rKind: TextLabel, rOn: TextLabel,
	equip: TextButton, again: TextButton, done: TextButton }
local function buildUi(): Ui
	local pg = me:WaitForChild("PlayerGui")
	local gui = new("ScreenGui", { Name = "JankLootOpening", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 60,
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling, Enabled = true }, pg)
	-- (Modal frees the mouse from first person while it's up, and the button eats clicks on the world)
	new("TextButton", { Name = "Catcher", Text = "", AutoButtonColor = false, BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Modal = true }, gui)
	local flash = new("Frame", { Name = "Flash", BackgroundColor3 = WHITE, BackgroundTransparency = 1, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 1 }, gui)
	-- (a soft dark band at the top and the bottom so the words read over any room)
	local shadeTop = new("Frame", { Name = "ShadeTop", BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 0, BorderSizePixel = 0,
		Size = UDim2.new(1, 0, 0.22, 0), ZIndex = 1 }, gui)
	new("UIGradient", { Rotation = 90, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 1) }) }, shadeTop)
	local shadeBot = new("Frame", { Name = "ShadeBot", BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 0, BorderSizePixel = 0,
		AnchorPoint = Vector2.new(0, 1), Position = UDim2.fromScale(0, 1), Size = UDim2.new(1, 0, 0.38, 0), ZIndex = 1 }, gui)
	new("UIGradient", { Rotation = 270, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(1, 1) }) }, shadeBot)
	local stage = new("Frame", { Name = "Stage", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(1920, 1080), ZIndex = 2 }, gui)
	local scale = new("UIScale", {}, stage)
	local title = new("TextLabel", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromOffset(960, 70),
		Size = UDim2.fromOffset(1200, 44), FontFace = T.FONT_TITLE, TextSize = 34, Text = "", TextColor3 = T.TEXT, TextTransparency = 1 }, stage)
	new("UIStroke", { Thickness = 1, Transparency = 0.7, Color = Color3.new(0, 0, 0), ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual }, title)
	local odds = new("TextLabel", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromOffset(960, 118),
		Size = UDim2.fromOffset(1200, 24), FontFace = T.FONT, TextSize = 17, Text = "", TextColor3 = T.SOFT, TextTransparency = 1 }, stage)
	local skip = button(stage, "SKIP  [SPACE]", false, UDim2.fromOffset(1700, 980), UDim2.fromOffset(170, 46))
	-- the reel: a band across the middle, cards on a strip that slides left under a fixed marker
	-- (a CanvasGroup, so the gradient fades the cards themselves out at both ends, not just the band behind them)
	local reel = new("CanvasGroup", { Name = "Reel", BackgroundColor3 = T.BG, BackgroundTransparency = 0.25, BorderSizePixel = 0,
		AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromOffset(960, 540), Size = UDim2.fromOffset(1920, CARD_H + 56), ClipsDescendants = true, Visible = false }, stage)
	new("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.18, 0), NumberSequenceKeypoint.new(0.82, 0), NumberSequenceKeypoint.new(1, 1) }) }, reel)
	local strip = new("Frame", { Name = "Strip", BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 28), Size = UDim2.fromOffset(STEP * 60, CARD_H) }, reel)
	local marker = new("Frame", { Name = "Marker", BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.fromOffset(960, 6), Size = UDim2.fromOffset(4, CARD_H + 44), ZIndex = 10 }, reel)
	for _, y in { 0, 1 } do
		local tri = new("Frame", { BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5), Rotation = 45,
			Position = UDim2.new(0.5, 0, y, 0), Size = UDim2.fromOffset(14, 14), ZIndex = 10 }, marker)
		local _ = tri
	end
	-- the reveal: bottom centre, under the turning prize
	local reveal = new("Frame", { Name = "Reveal", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.fromOffset(960, 1030),
		Size = UDim2.fromOffset(900, 250), Visible = false }, stage)
	local rKind = new("TextLabel", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 0), Size = UDim2.new(1, 0, 0, 26),
		FontFace = T.FONT_BOLD, TextSize = 20, Text = "", TextColor3 = T.TEXT }, reveal)
	local rName = new("TextLabel", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 28), Size = UDim2.new(1, 0, 0, 70),
		FontFace = T.FONT_TITLE, TextSize = 60, Text = "", TextColor3 = T.TEXT }, reveal)
	new("UIStroke", { Thickness = 1.5, Transparency = 0.6, Color = Color3.new(0, 0, 0), ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual }, rName)
	local rOn = new("TextLabel", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 100), Size = UDim2.new(1, 0, 0, 24),
		FontFace = T.FONT, TextSize = 18, Text = "", TextColor3 = T.SOFT }, reveal)
	local equip = button(reveal, "EQUIP", true, UDim2.fromOffset(120, 160), UDim2.fromOffset(250, 56))
	local again = button(reveal, "OPEN ANOTHER", false, UDim2.fromOffset(390, 160), UDim2.fromOffset(220, 56))
	local done = button(reveal, "DONE", false, UDim2.fromOffset(630, 160), UDim2.fromOffset(150, 56))
	return { gui = gui, stage = stage, scale = scale, title = title, odds = odds, skip = skip, reel = reel, strip = strip, marker = marker,
		flash = flash, reveal = reveal, rName = rName, rKind = rKind, rOn = rOn, equip = equip, again = again, done = done }
end

-- ---------------------------------------------------------------- the world: where it lands, the camera
-- ---------------------------------------------------------------- the floor (nothing goes through it)
-- (the owner, 16 Nov: "make sure the stuff doesnt clip through the ground".) the rules: Shared.LootFloor (your feet
-- from the foot parts, a ray trusted only near them, the highest visible piece rays can't see on top of it)
-- (the floor rules live in Shared.LootFloor: the server's spot for others uses the same ones)
local function feetOf(ch: Model?): number? return LootFloor.feet(ch) end
local function floorY(at: Vector3, feetY: number, ignore: { Instance }): number return LootFloor.at(at, feetY, ignore) end

local function ground(): (CFrame?, Vector3)
	local ch = me.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not root then return nil, Vector3.zero end
	local look = (workspace.CurrentCamera :: Camera).CFrame.LookVector
	local flat = Vector3.new(look.X, 0, look.Z)
	flat = if flat.Magnitude > 1e-3 then flat.Unit else Vector3.new(0, 0, -1)
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { ch :: Instance }
	local from = root.Position + Vector3.new(0, 0.5, 0)
	local dist = 7.5
	local hit = workspace:Raycast(from, flat * (dist + 2.5), params)
	if hit then dist = math.max(3.2, hit.Distance - 2.5) end -- (never through a wall)
	local spot = from + flat * dist
	local feetY = feetOf(ch) :: number
	local g = Vector3.new(spot.X, floorY(spot, feetY, { ch :: Instance }), spot.Z)
	-- the container faces you, turned a little so it reads as a solid thing (a three-quarter view)
	local cf = CFrame.lookAt(g, g - flat) * CFrame.Angles(0, math.rad(-20), 0)
	return cf, flat
end

-- ---------------------------------------------------------------- one opening
type Run = { ui: Ui, kind: string, res: any, opts: any, skip: boolean, skipAt: number, result: string?,
	box: Model?, prize: Model?, base: CFrame, flat: Vector3, height: number, light: PointLight?, rim: PointLight?,
	cam: { from: CFrame, to: CFrame, t0: number, dur: number, shake: number, shakeT: number, fov: number },
	blur: BlurEffect, tint: ColorCorrectionEffect, dof: DepthOfFieldEffect, hidden: { [ScreenGui]: boolean },
	saved: { cf: CFrame, type: Enum.CameraType, fov: number, loadoutOpen: any }, conns: { RBXScriptConnection },
	spin: number, prizeY: number, prizeFrom: number?, wid: string?, boxes: { any }? }

local function camTo(R: Run, to: CFrame, dur: number)
	local c = workspace.CurrentCamera :: Camera
	R.cam.from, R.cam.to, R.cam.t0, R.cam.dur = c.CFrame, to, os.clock(), dur
end
local function shake(R: Run, amp: number) R.cam.shake, R.cam.shakeT = amp, os.clock() end

-- wait t seconds, or less once SKIP is pressed (returns at once then)
local function hold(R: Run, t: number)
	local t0 = os.clock()
	while os.clock() - t0 < t and not R.skip do RunService.RenderStepped:Wait() end
end

local function particles(at: Vector3, color: Color3, kind: string): Part
	local p = new("Part", { Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, Transparency = 1,
		Size = Vector3.new(0.2, 0.2, 0.2), CFrame = CFrame.new(at) }, workspace)
	local e: ParticleEmitter
	if kind == "dust" then
		e = new("ParticleEmitter", { Texture = "rbxasset://textures/particles/smoke_main.dds", Rate = 0, Lifetime = NumberRange.new(0.6, 1.1),
			Speed = NumberRange.new(5, 9), SpreadAngle = Vector2.new(80, 8), Drag = 4, Acceleration = Vector3.new(0, 1.5, 0),
			Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.8), NumberSequenceKeypoint.new(1, 2.4) }),
			Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.55), NumberSequenceKeypoint.new(1, 1) }),
			Color = ColorSequence.new(Color3.fromRGB(196, 192, 184)), LightEmission = 0, EmissionDirection = Enum.NormalId.Top,
			Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-40, 40) }, p)
		e:Emit(16)
	else
		e = new("ParticleEmitter", { Texture = "rbxasset://textures/particles/sparkles_main.dds", Rate = 0, Lifetime = NumberRange.new(0.5, 1.0),
			Speed = NumberRange.new(8, 16), SpreadAngle = Vector2.new(55, 55), Drag = 3, Acceleration = Vector3.new(0, -12, 0),
			Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(1, 0) }),
			Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(1, 1) }),
			Color = ColorSequence.new(color), LightEmission = 0.8, EmissionDirection = Enum.NormalId.Top }, p)
		e:Emit(if kind == "big" then 60 else 26)
	end
	task.delay(2.5, function() p:Destroy() end)
	return p
end

-- the lid / zip / cap of a container, at u = 0 (shut) .. 1 (open). works on a scaled copy too (a batch, a bystander's)
local function openBox(box: Model?, u: number)
	if not box then return end
	local how = box:GetAttribute("Open") or "hinge"
	local bp = box:GetPivot()
	local k = box:GetScale()
	for _, m in box:GetChildren() do
		if m:IsA("Model") and (m.Name == "Lid" or m.Name == "Cap" or m.Name == "Flap" or m.Name == "FlapL" or m.Name == "FlapR" or m.Name == "Zip") then
			local rest = m:GetAttribute("Rest") :: CFrame?
			if not rest then rest = bp:ToObjectSpace(m:GetPivot()); m:SetAttribute("Rest", rest) end
			local hinge = m:GetAttribute("Hinge")
			-- (the hinge is written in the container's own frame at full size: scale it with the container)
			local h: CFrame = if typeof(hinge) == "CFrame" then CFrame.new(hinge.Position * k) * hinge.Rotation else (rest :: CFrame)
			local cf: CFrame
			if m.Name == "Zip" then
				-- the zip pull runs along the top from one end to the other
				local run = ((m:GetAttribute("Run") :: number?) or 2.4) * k
				cf = bp * CFrame.new(run * u, 0, 0) * (rest :: CFrame)
			elseif how == "pop" then
				-- the cap: up off the can, over, and down onto the floor beside it, landing on its side
				local v = math.clamp(u, 0, 1)
				local drop = math.max(0, h.Position.Y - 0.72 * k) -- (its middle ends one radius off the floor)
				local up = 2.0 * k * math.sin(math.pi * v) - drop * v * v
				cf = bp * CFrame.new(1.9 * k * v, up, 0.6 * k * v) * h * CFrame.Angles(0, v * 3.2, -v * math.pi / 2) * h:Inverse() * (rest :: CFrame)
			else
				-- (Angle is signed: + lifts a lid hinged at its back edge (+z), - one hinged at its front edge)
				local ang = (m:GetAttribute("Angle") :: number?) or (if how == "flap" then 75 else 108)
				cf = bp * h * CFrame.Angles(math.rad(ang) * u, 0, 0) * h:Inverse() * (rest :: CFrame)
			end
			m:PivotTo(cf)
		end
	end
end
local function openPose(R: Run, u: number) openBox(R.box, u) end

-- ---------------------------------------------------------------- nothing goes through the floor
-- (the owner, 16 Nov: "make sure the stuff doesnt clip through the ground".) a container's pivot is the middle of its
-- bottom face. tipped by ax about its own x and az about its z, its edges would dip under the floor by half its depth
-- (width) times the sine, so every pose is lifted by exactly that; nothing is ever put below its floor spot; the exits
-- shrink and fade into the container's own footprint instead of sinking
local LIFT = 0.04 -- (a hair over the floor, so the bottom face never flickers against it)
local function halves(box: Model): (number, number)
	local hx, hz = box:GetAttribute("HalfX"), box:GetAttribute("HalfZ")
	if type(hx) ~= "number" or type(hz) ~= "number" then
		local cf, size = box:GetBoundingBox()
		local c = box:GetPivot():PointToObjectSpace(cf.Position)
		hx, hz = math.abs(c.X) + size.X / 2, math.abs(c.Z) + size.Z / 2
		box:SetAttribute("HalfX", hx); box:SetAttribute("HalfZ", hz)
	end
	return hx :: number, hz :: number
end
-- the box on its floor spot `at`, y studs up, tipped (ax, ay, az), shifted (dx, dz): never under the floor
local function place(box: Model, at: CFrame, y: number, ax: number?, ay: number?, az: number?, dx: number?, dz: number?)
	local hx, hz = halves(box)
	local a, c = ax or 0, az or 0
	local dip = hz * math.abs(math.sin(a)) + hx * math.abs(math.sin(c))
	box:PivotTo(at * CFrame.new(dx or 0, math.max(0, y) + dip + LIFT, dz or 0) * CFrame.Angles(a, ay or 0, c))
end
-- a prize (a gun model) as it rises out of a container: its lowest point, measured once, so it starts above the top
local function halfHeight(m: Model): number
	local _, size = m:GetBoundingBox()
	return size.Y / 2 + math.max(size.X, size.Z) * 0.06 -- (+ what its little tilt adds)
end
-- leaving: everything shrinks into its own footprint and fades; lights go out with it
local function fadeOut(models: { Model? }, dur: number)
	local list = {}
	for _, m in models do
		if m and m.Parent then
			local parts, lights = {}, {}
			for _, d in m:GetDescendants() do
				if d:IsA("BasePart") then parts[d] = d.Transparency
				elseif d:IsA("Light") then lights[d] = d.Brightness end
			end
			table.insert(list, { m = m, k = m:GetScale(), parts = parts, lights = lights })
		end
	end
	local t0 = os.clock()
	while true do
		local u = math.min(1, (os.clock() - t0) / dur)
		local e = smooth(u)
		for _, o in list do
			if o.m.Parent then
				pcall(function() o.m:ScaleTo(o.k * (1 - 0.75 * e)) end) -- (about its pivot: a container's sits on the floor)
				for p, tr in o.parts do p.Transparency = tr + (1 - tr) * e end
				for l, b in o.lights do l.Brightness = b * (1 - e) end
			end
		end
		if u >= 1 then break end
		RunService.RenderStepped:Wait()
	end
end

-- the reel: build the cards, spin, land. returns the winning card
local function spinReel(R: Run, items: { any }, stop: number, dur: number): Frame
	local ui = R.ui
	for _, c in ui.strip:GetChildren() do c:Destroy() end
	local cards = {}
	for i, it in items do cards[i] = card(ui.strip, it, (i - 1) * STEP) end
	local rng = Random.new()
	local mid = 960
	-- where the strip ends: the prize card under the marker, somewhere across its width (never right on an edge)
	local within = rng:NextNumber(-0.38, 0.38) * CARD_W
	local xEnd = mid - ((stop - 1) * STEP + CARD_W / 2) - within
	local xStart = mid - (2 * STEP + CARD_W / 2) - rng:NextNumber(0, STEP)
	ui.strip.Position = UDim2.fromOffset(xStart, 28)
	ui.reel.Visible = true
	ui.reel.Position = UDim2.fromOffset(960, 580)
	ui.reel.BackgroundTransparency = 1
	tw(ui.reel, 0.3, { Position = UDim2.fromOffset(960, 540), BackgroundTransparency = 0.25 })
	local t0 = os.clock()
	local lastIdx = math.floor((mid - xStart) / STEP)
	local lastTick = 0
	local p = if dur > 3 then 4 else 3 -- (quart out: fast, then a long slow crawl past the last few cards)
	while true do
		local u = (os.clock() - t0) / dur
		if R.skip then u = 1 end
		local x = xStart + (xEnd - xStart) * easeOut(u, p)
		ui.strip.Position = UDim2.fromOffset(x, 28)
		local idx = math.floor((mid - x) / STEP)
		if idx ~= lastIdx and not R.skip then
			lastIdx = idx
			local now = os.clock()
			if now - lastTick > 0.03 then
				lastTick = now
				local slow = 1 - easeOut(u, 1.5)
				snd({ "loot_tick", "click" }, nil, 0.55 + 0.25 * (1 - slow), 1.0 + 0.06 * (1 - slow))
				-- (the marker nods with each card going by)
				ui.marker.Size = UDim2.fromOffset(6, CARD_H + 44)
				task.delay(0.04, function() ui.marker.Size = UDim2.fromOffset(4, CARD_H + 44) end)
			end
		end
		if u >= 1 then break end
		RunService.RenderStepped:Wait()
	end
	return cards[stop]
end

-- the world as it was when we're done: camera, HUD, controls, effects
local function restore(R: Run)
	for _, c in R.conns do c:Disconnect() end
	pcall(function() RunService:UnbindFromRenderStep("JankLootCam") end)
	pcall(function() ContextActionService:UnbindAction("JankLootSink") end)
	local c = workspace.CurrentCamera :: Camera
	c.CameraType = R.saved.type
	c.FieldOfView = R.saved.fov
	R.blur:Destroy(); R.tint:Destroy(); R.dof:Destroy()
	if R.box then R.box:Destroy() end
	for _, b in R.boxes or {} do if b.m then b.m:Destroy() end end
	if R.prize then R.prize:Destroy() end
	R.ui.gui:Destroy()
	for g in R.hidden do if g.Parent then g.Enabled = true end end
	me:SetAttribute("LoadoutOpen", R.saved.loadoutOpen)
	me:SetAttribute("LootOpening", nil)
	pcall(function()
		local controls = require(me:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: any):GetControls()
		controls:Enable()
	end)
end

-- ---------------------------------------------------------------- equipping a prize (the loadout's own ops)
local RANK = { common = 1, rare = 2, epic = 3, legendary = 4 }
-- the gun a prize goes on: its own (a wrap or hat is won for one gun; a skin is one gun's)
local function gunOf(item: any): string?
	local w = item.weapon or (item.type == "skin" and (LootTable.SKINS[item.id] or {})[3]) or nil
	local e = w and Roster.byId[w]
	return if e and e.live and e.slot ~= "utility" then w else nil
end
local function canEquip(item: any): boolean
	return (item.type == "wrap" or item.type == "hat" or item.type == "skin") and gunOf(item) ~= nil
end
local function equipItem(item: any): (boolean, string?)
	local lo = Remotes:FindFirstChild("Loadout") :: RemoteFunction?
	local wid = gunOf(item)
	if not lo or not wid then return false, "can't go on anything yet" end
	local ok, r = pcall(function()
		if item.type == "wrap" then
			local _, mode = WeaponModels.wrapFor(me, wid :: string)
			return (lo :: RemoteFunction):InvokeServer("wrap", wid, item.id, if mode and mode ~= "" then mode else "full")
		elseif item.type == "hat" then
			return (lo :: RemoteFunction):InvokeServer("hat", wid, item.id)
		end
		return (lo :: RemoteFunction):InvokeServer("skin", wid, item.id)
	end)
	if ok and type(r) == "table" and r.ok then return true, nil end
	return false, if ok and type(r) == "table" and type(r.why) == "string" then r.why else "couldn't equip"
end

-- the odds line this open was rolled with (what you owned before it: the prizes are taken back out)
local function oddsText(kind: string, prizes: { any }): string
	local owned = {}
	local okInv, inv = pcall(function() return (Remotes:FindFirstChild("Loot") :: RemoteFunction):InvokeServer("inventory") end)
	if okInv and type(inv) == "table" and type(inv.owned) == "table" then
		for t, ids in inv.owned do owned[t] = {}; for _, id in ids do owned[t][id] = true end end
		for _, q in prizes do if owned[q.type] then owned[q.type][q.key or q.id] = nil end end
	end
	return "ODDS  " .. LootTable.oddsLine(LootTable.odds(kind, owned))
end

-- ---------------------------------------------------------------- several at once (x5, x10)
-- the owner: "make sure you can open multiple". they drop in a row (two rows of five for ten), smaller, one after
-- another; they pop together; a quick reel per prize runs one after another (SKIP: straight to the end); then a grid
-- of everything you got, rarest first, each with EQUIP; OPEN ANOTHER opens the same number again
local function runMany(R: Run): string
	local ui, kind, res = R.ui, R.kind, R.res
	local info = LootTable.CONTAINERS[kind] or LootTable.CONTAINERS.crate
	local prizes = res.prizes :: { any }
	local n = #prizes
	local cam = workspace.CurrentCamera :: Camera
	ui.title.Text = ("%s  x%d"):format(string.upper(info.name), n)
	ui.odds.Text = oddsText(kind, prizes)
	tw(ui.title, 0.4, { TextTransparency = 0 }); tw(ui.odds, 0.4, { TextTransparency = 0.1 })

	-- 1. the row
	local flat = R.flat
	local right = flat:Cross(Vector3.yAxis)
	local g = R.base.Position + flat * 2.5
	local face = CFrame.lookAt(g, g - flat)
	local probe = container(kind)
	local _, sz = probe:GetBoundingBox()
	local fullH = (probe:GetAttribute("Height") :: number?) or 2.4
	probe:Destroy()
	-- (sized by the container's footprint, so a row of five is about 12 studs wide whatever it is: the cans stay big)
	local foot = math.max(sz.X, sz.Z)
	local k = math.min(1, 12.5 / (5 * foot + 4 * 0.8))
	local stepX = foot * k + 0.8
	local stepZ = foot * k + 1.2
	local boxes = {}
	R.boxes = boxes
	for i = 1, n do
		local back = n > 5 and i <= 5
		local inRow = if n > 5 then (if back then 5 else n - 5) else n
		local col = if n > 5 and not back then i - 6 else i - 1
		local x = (col - (inRow - 1) / 2) * stepX
		local at = face * CFrame.new(x, 0, if back then stepZ else 0) * CFrame.Angles(0, math.rad(-14 + col * 7), 0)
		-- (each on its own bit of floor: a pad or a step under one of them lifts that one)
		at = CFrame.new(at.X, floorY(at.Position, g.Y, { me.Character :: Instance }), at.Z) * at.Rotation
		local b = container(kind)
		b:ScaleTo(k)
		local lp = new("Part", { Name = "Light", Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, Transparency = 1,
			Size = Vector3.new(0.2, 0.2, 0.2) }, b)
		lp.CFrame = b:GetPivot() * CFrame.new(0, fullH * k + 0.5, 0)
		local light = new("PointLight", { Color = WHITE, Brightness = 0, Range = 8, Shadows = false }, lp)
		place(b, at, 11)
		b.Parent = workspace
		openBox(b, 0)
		boxes[i] = { m = b, at = at, t0 = os.clock() + (i - 1) * 0.07, light = light }
	end
	R.height = fullH * k
	local eye = g - flat * 8.6 + Vector3.new(0, 5.4, 0)
	camTo(R, CFrame.lookAt(eye, g + flat * (if n > 5 then 1.2 else 0) + Vector3.new(0, 0.9, 0)), 0.7)
	R.cam.fov = 62
	-- they fall one after another, land with a thud (one at the first and one at the last: no rattle of ten) and hop
	local firstLand, lastLand = false, false
	while true do
		local now = os.clock()
		local done = true
		for i, b in boxes do
			local u = (now - b.t0) / 0.36
			if R.skip then u = 3 end
			if u < 1 then
				done = false
				local y = 11 * (1 - math.max(0, u) ^ 2)
				place(b.m, b.at, y, 0.1 * (1 - math.max(0, u)))
			else
				local v = (u - 1) * 0.36 / 0.4
				if v < 1 then
					done = false
					place(b.m, b.at, 0.45 * math.sin(v * math.pi) * (1 - v))
				else
					place(b.m, b.at, 0)
				end
				if i == 1 and not firstLand then firstLand = true; snd({ "loot_land", "bonk" }, b.at.Position, 1, 0.7); shake(R, 0.2) end
				if i == n and not lastLand and n > 1 then lastLand = true; snd({ "loot_land", "bonk" }, b.at.Position, 0.8, 0.8) end
			end
			openBox(b.m, 0)
		end
		if done then break end
		RunService.RenderStepped:Wait()
	end
	if not R.skip then hold(R, 0.25) end
	-- 2. they pop together (a ripple, one sound)
	snd({ "loot_pop", "bigpop", "pop" }, g, 1, 1)
	particles(g + Vector3.new(0, R.height, 0), Color3.fromRGB(255, 236, 200), "pop")
	for _, b in boxes do
		for _, d in b.m:GetDescendants() do
			if d:IsA("BasePart") and d.Name == "glow" then d.Transparency = 0; d.Material = Enum.Material.Neon end
		end
		b.light.Brightness = 2
	end
	local arc = boxes[1].m:GetAttribute("Open") == "pop"
	local pt = if R.skip then 0.25 elseif arc then 0.8 else 0.5
	local t0 = os.clock()
	while true do
		local all = true
		for i, b in boxes do
			local u = math.clamp((os.clock() - t0 - (i - 1) * 0.05) / pt, 0, 1)
			if u < 1 then all = false end
			local s = 1.70158
			openBox(b.m, if arc then u else 1 + (s + 1) * (u - 1) ^ 3 + s * (u - 1) ^ 2)
		end
		if all then break end
		RunService.RenderStepped:Wait()
	end

	-- 3. a quick reel per prize, one after another
	tw(R.blur, 0.4, { Size = 16 })
	tw(R.tint, 0.4, { Brightness = -0.06, Saturation = -0.5, Contrast = 0.05 })
	if not R.result then R.skip = false end
	for i, prize in prizes do
		if R.skip then break end
		ui.title.Text = ("%s  %d / %d"):format(string.upper(info.name), i, n)
		local items = (res.strips or {})[i]
		local stop = (res.stops or {})[i]
		if type(items) ~= "table" or type(stop) ~= "number" or not items[stop] then
			items, stop = {}, 20
			for j = 1, 24 do items[j] = prize end
		end
		local win = spinReel(R, items, stop, 0.95)
		local col = rcol(prize.rarity)
		local stroke = win:FindFirstChildOfClass("UIStroke")
		if stroke then stroke.Color = col; stroke.Transparency = 0; stroke.Thickness = 3 end
		tw(new("UIScale", { Scale = 1 }, win), 0.2, { Scale = 1.08 }, Enum.EasingStyle.Back)
		boxes[i].light.Color = col
		boxes[i].light.Brightness = 2 + (RANK[prize.rarity] or 1)
		local rank = RANK[prize.rarity] or 1
		-- (a sting only for the big ones: ten chimes in a row would be noise)
		if rank >= 3 then
			snd(if rank == 4 then { "loot_win_legendary", "round_end" } else { "loot_win_epic", "round_start" }, nil, 0.9, 1)
			ui.flash.BackgroundColor3 = col; ui.flash.BackgroundTransparency = 0.78
			tw(ui.flash, 0.6, { BackgroundTransparency = 1 })
		end
		hold(R, if rank >= 3 then 0.55 else 0.22)
	end
	-- (SKIP: everything lands at once)
	for i, prize in prizes do
		boxes[i].light.Color = rcol(prize.rarity)
		boxes[i].light.Brightness = 2 + (RANK[prize.rarity] or 1)
	end
	ui.reel.Visible = false
	ui.skip.Visible = false
	tw(R.blur, 0.4, { Size = 10 })
	tw(R.tint, 0.4, { Brightness = -0.12, Saturation = -0.35, Contrast = 0.04 })
	snd({ "loot_win_rare", "ting" }, nil, 0.8, 1)

	-- 4. everything you got, rarest first, each with EQUIP
	local order = table.clone(prizes)
	table.sort(order, function(a, b)
		local ra, rb = RANK[a.rarity] or 0, RANK[b.rarity] or 0
		if ra ~= rb then return ra > rb end
		return (a.name or "") < (b.name or "")
	end)
	ui.title.Text = ("YOU GOT %d"):format(n)
	local grid = new("Frame", { Name = "Summary", BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 0), Size = UDim2.fromOffset(1920, 1080), ZIndex = 5 }, ui.stage)
	local cols = math.min(5, n)
	local rows = math.ceil(n / 5)
	local CW, CH, BH, GX, GY = CARD_W, CARD_H, 38, 22, 26
	local x0 = 960 - (cols * CW + (cols - 1) * GX) / 2
	local y0 = 540 - (rows * (CH + BH + 8) + (rows - 1) * GY) / 2 + 10
	for i, item in order do
		local r, c = math.floor((i - 1) / 5), (i - 1) % 5
		local inRow = math.min(5, n - r * 5)
		local xr = 960 - (inRow * CW + (inRow - 1) * GX) / 2 -- (a short last row sits in the middle)
		local holder = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(xr + c * (CW + GX), y0 + r * (CH + BH + 8 + GY) + 30),
			Size = UDim2.fromOffset(CW, CH + BH + 8) }, grid)
		local cd = card(holder, item, 0)
		local stroke = cd:FindFirstChildOfClass("UIStroke")
		if stroke and (RANK[item.rarity] or 0) >= 3 then stroke.Color = rcol(item.rarity); stroke.Transparency = 0.1; stroke.Thickness = 2 end
		local eq = canEquip(item)
		local b = button(holder, if eq then "EQUIP" else "IN YOUR INVENTORY", false, UDim2.fromOffset(0, CH + 8), UDim2.fromOffset(CW, BH))
		b.TextSize = 14
		if eq then
			b.MouseButton1Click:Connect(function()
				if b.Text == "EQUIPPED" or b.Text == "..." then return end
				b.Text = "..."
				local ok, why = equipItem(item)
				b.Text = if ok then "EQUIPPED" else string.upper(why or "couldn't")
				if ok then pcall(Sfx.play, "click") end
			end)
		else
			b.TextColor3 = T.MUTED
		end
		holder.Position += UDim2.fromOffset(0, 24)
		cd.BackgroundTransparency = 1
		tw(holder, 0.3 + i * 0.03, { Position = holder.Position - UDim2.fromOffset(0, 24) })
		tw(cd, 0.3 + i * 0.03, { BackgroundTransparency = 0 })
	end
	if res.short then
		local note = new("TextLabel", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromOffset(960, 150),
			Size = UDim2.fromOffset(1000, 24), FontFace = T.FONT, TextSize = 17, TextColor3 = T.SOFT, ZIndex = 6,
			Text = "that was everything left in them for you" }, grid)
		local _ = note
	end
	local again = R.opts.again ~= false
	local bAgain = button(grid, ("OPEN %d MORE"):format(n), true, UDim2.fromOffset(960 - 230, 960), UDim2.fromOffset(250, 56))
	local bDone = button(grid, "DONE", false, UDim2.fromOffset(960 + 40, 960), UDim2.fromOffset(190, 56))
	bAgain.Visible = again
	if not again then bDone.Position = UDim2.fromOffset(960 - 95, 960) end
	local answer: string? = nil
	bDone.MouseButton1Click:Connect(function() answer = "done" end)
	bAgain.MouseButton1Click:Connect(function() answer = "again" end)
	while not answer do
		if R.result then answer = R.result end
		RunService.RenderStepped:Wait()
	end

	-- 5. away
	grid:Destroy()
	tw(R.tint, 0.3, { Brightness = 0, Saturation = 0, Contrast = 0 })
	tw(R.blur, 0.3, { Size = 0 })
	local st = os.clock()
	local sv = R.saved.cf
	R.cam.from, R.cam.t0, R.cam.dur = cam.CFrame, os.clock(), 0.45
	local ch = me.Character
	local h = ch and ch:FindFirstChild("Head") :: BasePart?
	R.cam.to = if h then CFrame.new(h.Position + Vector3.new(0, 0.1, 0)) * sv.Rotation else sv
	R.cam.fov = R.saved.fov
	local all = {}
	for _, b in boxes do table.insert(all, b.m) end
	fadeOut(all, 0.45)
	while os.clock() - st < 0.45 do RunService.RenderStepped:Wait() end
	return answer :: string
end

-- ---------------------------------------------------------------- what others see (LootShow.client.luau)
-- someone near you opened something: their container drops on the ground in front of them, pops, and the best prize
-- rises over it and turns, with a sign: who, what, which gun, its rarity. no reel, one quiet sound, about six seconds.
-- several at once are fine (at most four drawn at a time); far away (more than 170 studs) is not drawn
local showing = 0
local function showOne(d: any)
	local kind = if LootTable.CONTAINERS[d.kind] then d.kind else "crate"
	local best = d.prizes[1]
	for _, q in d.prizes do if (RANK[q.rarity] or 0) > (RANK[best.rarity] or 0) then best = q end end
	local col = rcol(best.rarity)
	local box = container(kind)
	local k = 0.8
	box:ScaleTo(k)
	local hgt = ((box:GetAttribute("Height") :: number?) or 2.4) * k
	local base: CFrame = d.cf
	place(box, base, 9)
	box.Parent = workspace
	openBox(box, 0)
	local lp = new("Part", { Name = "ShowLight", Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, Transparency = 1,
		Size = Vector3.new(0.2, 0.2, 0.2), CFrame = base * CFrame.new(0, hgt + 0.6, 0) }, box)
	local light = new("PointLight", { Color = WHITE, Brightness = 0, Range = 10, Shadows = false }, lp)
	local quiet = showing > 2 -- (a crowd of openings: no sound from the extra ones)
	-- the drop and the hop
	local t0 = os.clock()
	while true do
		local u = (os.clock() - t0) / 0.38
		if u >= 1 then break end
		place(box, base, 9 * (1 - u * u))
		openBox(box, 0)
		RunService.RenderStepped:Wait()
	end
	if not quiet then snd({ "loot_land", "bonk" }, base.Position, 0.45, 0.75) end
	particles(base.Position + Vector3.new(0, 0.2, 0), WHITE, "dust")
	t0 = os.clock()
	while os.clock() - t0 < 0.35 do
		local v = (os.clock() - t0) / 0.35
		place(box, base, 0.5 * math.sin(v * math.pi) * (1 - v))
		openBox(box, 0)
		RunService.RenderStepped:Wait()
	end
	place(box, base, 0)
	task.wait(0.35)
	-- the pop
	for _, x in box:GetDescendants() do
		if x:IsA("BasePart") and x.Name == "glow" then x.Transparency = 0; x.Material = Enum.Material.Neon end
	end
	particles(base.Position + Vector3.new(0, hgt, 0), col, if (RANK[best.rarity] or 0) >= 4 then "big" else "pop")
	local arc = box:GetAttribute("Open") == "pop"
	local pt = if arc then 0.8 else 0.45
	t0 = os.clock()
	while true do
		local u = math.min(1, (os.clock() - t0) / pt)
		local s = 1.70158
		openBox(box, if arc then u else 1 + (s + 1) * (u - 1) ^ 3 + s * (u - 1) ^ 2)
		light.Color = col
		light.Brightness = 5 * (1 - u) + 2.5 * u
		if u >= 1 then break end
		RunService.RenderStepped:Wait()
	end
	-- the prize over it, and the sign
	local m = prizeModel(best)
	local top = hgt + 2.0
	local from = hgt
	if m then
		pcall(function() m:ScaleTo(m:GetScale() * 0.7) end)
		from = hgt + LIFT + halfHeight(m) + 0.1 -- (up from just over the open top)
		top = math.max(top, from + 0.5)
		m.Parent = workspace
	end
	local anchor = new("Part", { Name = "ShowSign", Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, Transparency = 1,
		Size = Vector3.new(0.2, 0.2, 0.2), CFrame = base * CFrame.new(0, top + 1.5, 0) }, box)
	local bb = new("BillboardGui", { Size = UDim2.new(7.5, 0, 2.3, 0), StudsOffset = Vector3.new(0, 0.4, 0), MaxDistance = 150,
		LightInfluence = 0, AlwaysOnTop = false, ResetOnSpawn = false }, anchor)
	local plate = new("Frame", { BackgroundColor3 = T.BG, BackgroundTransparency = 0.2, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1) }, bb)
	T.corner(plate, 6)
	new("UIStroke", { Color = col, Thickness = 1.5, Transparency = 0.2 }, plate)
	local function line(y: number, h: number, text: string, color: Color3, font: Font)
		new("TextLabel", { BackgroundTransparency = 1, Position = UDim2.fromScale(0.04, y), Size = UDim2.fromScale(0.92, h), Text = text,
			TextColor3 = color, FontFace = font, TextScaled = true, TextXAlignment = Enum.TextXAlignment.Center }, plate)
	end
	local info = LootTable.CONTAINERS[kind]
	local gun = best.weapon and Roster.byId[best.weapon]
	line(0.06, 0.24, ("%s opened %s"):format(tostring(d.who or "someone"), if (d.n or 1) > 1 then ("%d %s"):format(d.n, string.lower(info.plural)) else "a " .. string.lower(info.name)), T.SOFT, T.FONT)
	line(0.32, 0.38, string.upper(best.name or best.id or ""), col, T.FONT_BOLD)
	line(0.72, 0.22, (if gun then string.upper(gun.name) .. "  ·  " else "") .. rname(best.rarity) .. (if (d.n or 1) > 1 then ("  ·  +%d MORE"):format(d.n - 1) else ""), T.MUTED, T.FONT)
	-- turn it for a while, then everything sinks away
	local rise0 = os.clock()
	local face = base.Rotation
	while os.clock() - rise0 < 4.2 do
		local u = easeOut((os.clock() - rise0) / 0.6, 3)
		if m and m.Parent then
			local y = from + (top - from) * u + math.sin(os.clock() * 1.3) * 0.06
			m:PivotTo(CFrame.new(base.Position + Vector3.new(0, y, 0)) * face * CFrame.Angles(0, math.pi / 2 + (os.clock() - rise0) * 0.8, 0))
		end
		RunService.RenderStepped:Wait()
	end
	bb.Enabled = false
	fadeOut({ box, m }, 0.5)
	if m then m:Destroy() end
	box:Destroy()
end
function Opening.show(d: any)
	if type(d) ~= "table" or typeof(d.cf) ~= "CFrame" or type(d.prizes) ~= "table" or #d.prizes == 0 then return end
	if showing >= 4 then return end
	local c = workspace.CurrentCamera
	if c and (c.CFrame.Position - (d.cf :: CFrame).Position).Magnitude > 170 then return end
	showing += 1
	task.spawn(function()
		local ok, err = pcall(showOne, d)
		showing -= 1
		if not ok then warn("[jankfire] someone's opening didn't draw: " .. tostring(err)) end
	end)
end

local function run(R: Run): string
	local ui, kind, res = R.ui, R.kind, R.res
	local info = LootTable.CONTAINERS[kind] or LootTable.CONTAINERS.crate
	local prize = res.prize or res.item or {}
	prize.type = prize.type or prize.kind
	local quick = R.opts.quick == true
	local cam = workspace.CurrentCamera :: Camera

	-- title + the odds this open was rolled with
	ui.title.Text = string.upper(info.name)
	local owned = {}
	local okInv, inv = pcall(function() return (Remotes:FindFirstChild("Loot") :: RemoteFunction):InvokeServer("inventory") end)
	if okInv and type(inv) == "table" and type(inv.owned) == "table" then
		for t, ids in inv.owned do owned[t] = {}; for _, id in ids do owned[t][id] = true end end
		-- (the prize is owned by now: the odds you opened with had it still in)
		if owned[prize.type] then owned[prize.type][prize.key or prize.id] = nil end
	end
	ui.odds.Text = "ODDS  " .. LootTable.oddsLine(LootTable.odds(kind, owned))
	tw(ui.title, 0.4, { TextTransparency = 0 }); tw(ui.odds, 0.4, { TextTransparency = 0.1 })

	-- 1. the drop: from high up, onto the ground, a heavy bounce, dust; the camera comes round to look
	local base = R.base
	local box = container(kind)
	R.box = box
	R.height = (box:GetAttribute("Height") :: number?) or 2.4
	local glow = Instance.new("PointLight")
	glow.Color = WHITE; glow.Brightness = 0; glow.Range = 12; glow.Shadows = false
	local lightPart = new("Part", { Name = "Light", Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, Transparency = 1,
		Size = Vector3.new(0.2, 0.2, 0.2), CFrame = base * CFrame.new(0, R.height + 0.6, 0) }, box)
	glow.Parent = lightPart
	R.light = glow
	local drop = if quick then 6 else 15
	place(box, base, drop, 0.12, 0.5, -0.08)
	box.Parent = workspace
	openPose(R, 0)
	local flat = R.flat
	local right = flat:Cross(Vector3.yAxis)
	local look = base.Position + Vector3.new(0, R.height * 0.5, 0)
	-- (the camera stands a couple of studs in front of you, a little to the side: your own body stays behind it)
	local eye = base.Position - flat * 5.4 + right * 1.3 + Vector3.new(0, 2.9 + R.height * 0.4, 0)
	camTo(R, CFrame.lookAt(eye, look), if quick then 0.35 else 0.75)
	R.cam.fov = 52
	local fall = if quick then 0.28 else TIME.fall
	local t0 = os.clock()
	while true do
		local u = math.min(1, (os.clock() - t0) / fall)
		local y = drop * (1 - u * u)
		local a = 1 - u
		place(box, base, y, 0.12 * a, 0.5 * a * a, -0.08 * a)
		openPose(R, 0)
		if u >= 1 then break end
		RunService.RenderStepped:Wait()
	end
	snd({ "loot_land", "bonk" }, base.Position, 1.2, 0.62)
	shake(R, if quick then 0.15 else 0.35)
	particles(base.Position + Vector3.new(0, 0.2, 0), WHITE, "dust")
	-- the bounce: two hops that die away, with a rock forward and back
	local bt = if quick then 0.3 else TIME.bounce
	t0 = os.clock()
	while true do
		local u = math.min(1, (os.clock() - t0) / bt)
		local hop = if u < 0.62 then 0.9 * math.sin(u / 0.62 * math.pi) else 0.22 * math.sin((u - 0.62) / 0.38 * math.pi)
		local rock = math.sin(u * math.pi * 3) * (1 - u) * 0.09
		place(box, base, hop * (if quick then 0.5 else 1), rock, 0, rock * 0.4)
		openPose(R, 0)
		if u >= 1 then break end
		RunService.RenderStepped:Wait()
	end
	place(box, base, 0)
	if not quick then hold(R, 0.15) end

	-- 2. the rattle, then the pop: light leaks out of the seam, the lid / zip / cap goes
	if not quick and not R.skip then
		t0 = os.clock()
		while os.clock() - t0 < TIME.rattle and not R.skip do
			local u = (os.clock() - t0) / TIME.rattle
			local amp = 0.02 + 0.07 * u * u
			place(box, base, 0, math.sin(os.clock() * 47) * amp, 0, math.sin(os.clock() * 59) * amp,
				math.sin(os.clock() * 61) * amp * 0.4, math.cos(os.clock() * 53) * amp * 0.3)
			openPose(R, 0)
			glow.Brightness = 2.2 * u
			RunService.RenderStepped:Wait()
		end
		place(box, base, 0)
	end
	snd({ "loot_pop", "bigpop", "pop" }, base.Position, 1, 1)
	shake(R, 0.18)
	particles(base.Position + Vector3.new(0, R.height, 0), Color3.fromRGB(255, 236, 200), "pop")
	for _, d in box:GetDescendants() do
		if d:IsA("BasePart") and d.Name == "glow" then d.Transparency = 0; d.Material = Enum.Material.Neon end
	end
	local arc = box:GetAttribute("Open") == "pop"
	local pt = if quick or R.skip then 0.3 elseif arc then 0.8 else TIME.pop
	t0 = os.clock()
	while true do
		local u = math.min(1, (os.clock() - t0) / pt)
		-- (back-out: a lid or flap swings past open and settles; a cap flies on its arc)
		local s = 1.70158
		local e = if arc then u else 1 + (s + 1) * (u - 1) ^ 3 + s * (u - 1) ^ 2
		openPose(R, e)
		glow.Brightness = 6 * (1 - u) + 2.4 * u
		if u >= 1 then break end
		RunService.RenderStepped:Wait()
	end

	-- 3. the reel over the soft world
	tw(R.blur, 0.4, { Size = 18 })
	tw(R.tint, 0.4, { Brightness = -0.06, Saturation = -0.5, Contrast = 0.05 })
	local items = res.strip
	local stop = res.stop
	if type(items) ~= "table" or #items == 0 or type(stop) ~= "number" or not items[stop] then
		items, stop = {}, 40
		for i = 1, 46 do items[i] = prize end
	end
	local spinDur = if quick or R.skip then TIME.spinQuick else TIME.spin
	if not R.result then R.skip = false end -- (the skip that cut the pop doesn't also cut the reel: press again for that)
	local win = spinReel(R, items, stop, spinDur)

	-- 4. it lands: the winner grows, the rest go dark, the screen breathes its colour
	local col = rcol(prize.rarity)
	for _, c in ui.strip:GetChildren() do
		if c:IsA("Frame") and c ~= win then
			local dim = c:FindFirstChild("Dim")
			if dim then tw(dim :: Frame, 0.3, { BackgroundTransparency = 0.5 }) end
		end
	end
	local sc = new("UIScale", { Scale = 1 }, win)
	tw(sc, 0.35, { Scale = 1.1 }, Enum.EasingStyle.Back)
	local stroke = win:FindFirstChildOfClass("UIStroke")
	if stroke then stroke.Color = col; stroke.Transparency = 0; stroke.Thickness = 3 end
	ui.flash.BackgroundColor3 = col
	ui.flash.BackgroundTransparency = 0.72
	tw(ui.flash, 0.8, { BackgroundTransparency = 1 })
	local rank = ({ common = 1, rare = 2, epic = 3, legendary = 4 })[prize.rarity] or 1
	local stings = ({ { "loot_win_common", "ting" }, { "loot_win_rare", "ting" }, { "loot_win_epic", "round_start" }, { "loot_win_legendary", "round_end", "round_start" } })[rank]
	snd(stings, nil, 1, 1)
	glow.Color = col
	glow.Brightness = 2 + rank
	if rank >= 3 then
		shake(R, 0.12 * rank)
		particles(base.Position + Vector3.new(0, R.height, 0), col, if rank == 4 then "big" else "pop")
	end
	if not R.result then R.skip = false end
	hold(R, if quick then 0.35 else TIME.land)

	-- 5. the reveal: the reel goes, the prize comes up out of the container and turns; the camera leans in
	tw(ui.reel, 0.3, { Position = UDim2.fromOffset(960, 600), BackgroundTransparency = 1 })
	task.delay(0.3, function() ui.reel.Visible = false end)
	tw(R.blur, 0.5, { Size = 0 }) -- (the depth of field below keeps the room soft, not the prize)
	tw(R.tint, 0.5, { Brightness = -0.06, Saturation = -0.3, Contrast = 0.06 })
	ui.skip.Visible = false
	tw(ui.title, 0.3, { TextTransparency = 1 }); tw(ui.odds, 0.3, { TextTransparency = 1 })
	local m, wid = prizeModel(prize)
	R.wid = wid
	R.prizeY = math.min(R.height, 2.6) + 3.0
	if m then
		R.prize = m
		R.prizeFrom = R.height + LIFT + halfHeight(m) + 0.1 -- (it comes up from just over the open top: never through it)
		R.prizeY = math.max(R.prizeY, R.prizeFrom + 0.6)
		m:PivotTo(base * CFrame.new(0, R.prizeFrom, 0))
		m.Parent = workspace
		local rim = Instance.new("PointLight")
		rim.Color = col; rim.Brightness = 1.6; rim.Range = 9; rim.Shadows = false
		local key = Instance.new("SpotLight")
		key.Color = Color3.fromRGB(255, 250, 244); key.Brightness = 2.2; key.Range = 16; key.Angle = 50; key.Face = Enum.NormalId.Front
		local lp = new("Part", { Name = "PrizeLight", Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, Transparency = 1,
			Size = Vector3.new(0.2, 0.2, 0.2) }, m)
		lp.CFrame = CFrame.lookAt(base.Position - flat * 4 + Vector3.new(0, R.prizeY + 2.5, 0), base.Position + Vector3.new(0, R.prizeY, 0))
		key.Parent = lp
		local lp2 = new("Part", { Name = "PrizeRim", Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, Transparency = 1,
			Size = Vector3.new(0.2, 0.2, 0.2), CFrame = base * CFrame.new(0, R.height + 0.3, 1.2) }, m)
		rim.Parent = lp2
		R.rim = rim
	end
	local riseT0 = os.clock()
	local focus = base.Position + Vector3.new(0, R.prizeY, 0)
	local eye2 = base.Position - flat * 5.6 + right * 0.9 + Vector3.new(0, R.prizeY + (if prize.type == "hat" then 1.4 else 0.7), 0)
	camTo(R, CFrame.lookAt(eye2, focus - Vector3.new(0, 0.25, 0)), 0.8)
	R.dof.Enabled = true
	R.dof.FocusDistance = (eye2 - focus).Magnitude
	-- the turn (and the rise) run every frame from here until the end
	table.insert(R.conns, RunService.RenderStepped:Connect(function(dt)
		local pm = R.prize
		if not pm or not pm.Parent then return end
		R.spin += dt * 0.7
		local u = easeOut((os.clock() - riseT0) / TIME.rise, 3)
		local y0 = R.prizeFrom or R.height
		local y = y0 + (R.prizeY - y0) * u + math.sin(os.clock() * 1.3) * 0.08 * u
		local face = CFrame.lookAt(Vector3.zero, -flat)
		pm:PivotTo(CFrame.new(base.Position + Vector3.new(0, y, 0)) * face * CFrame.Angles(0, math.pi / 2 + 0.5 + math.sin(R.spin) * 0.55, 0) * CFrame.Angles(0.1, 0, 0))
	end))

	-- the words and the buttons
	local tname = LootTable.TYPE_NAMES[prize.type] or "Item"
	ui.rKind.Text = rname(prize.rarity) .. "  ·  " .. string.upper(tname)
	ui.rKind.TextColor3 = col
	ui.rName.Text = string.upper(prize.name or prize.id or "")
	local we = wid and Roster.byId[wid]
	ui.rOn.Text = if prize.type == "skin" then "a new look for your " .. (if we then we.name else "weapon")
		elseif we and prize.weapon then "for your " .. we.name .. " only" elseif we then "shown on your " .. we.name else ""
	local can = canEquip(prize)
	local eqGun = gunOf(prize)
	ui.equip.Visible = can
	ui.equip.Text = if can and eqGun then "EQUIP ON " .. string.upper(Roster.byId[eqGun].name) else "EQUIP"
	ui.equip.Size = UDim2.fromOffset(math.max(250, #ui.equip.Text * 13 + 40), 56)
	local again = R.opts.again ~= false
	ui.again.Visible = again
	-- lay the row out in the middle
	local row = {}
	for _, b in { ui.equip, ui.again, ui.done } do if b.Visible then table.insert(row, b) end end
	local width = 0
	for _, b in row do width += b.Size.X.Offset end
	width += (#row - 1) * 16
	local x = 450 - width / 2
	for _, b in row do b.Position = UDim2.fromOffset(x, 160); x += b.Size.X.Offset + 16 end
	ui.reveal.Visible = true
	ui.reveal.Position = UDim2.fromOffset(960, 1060)
	tw(ui.reveal, 0.4, { Position = UDim2.fromOffset(960, 1030) })

	local answer: string? = nil
	ui.done.MouseButton1Click:Connect(function() answer = "done" end)
	ui.again.MouseButton1Click:Connect(function() answer = "again" end)
	ui.equip.MouseButton1Click:Connect(function()
		if not can or ui.equip.Text == "EQUIPPED" or ui.equip.Text == "..." then return end
		ui.equip.Text = "..."
		local ok, why = equipItem(prize)
		if ok then
			ui.equip.Text = "EQUIPPED"
			ui.equip.BackgroundColor3 = T.CARD
			ui.equip.TextColor3 = T.TEXT
			pcall(Sfx.play, "click")
		else
			ui.equip.Text = string.upper(why or "couldn't equip")
		end
	end)
	while not answer do
		if R.result then answer = R.result end
		RunService.RenderStepped:Wait()
	end

	-- 6. away: the prize and the container sink, the camera goes home
	tw(ui.reveal, 0.25, { Position = UDim2.fromOffset(960, 1100) })
	tw(R.dof, 0.3, { FarIntensity = 0, NearIntensity = 0 })
	tw(R.tint, 0.3, { Brightness = 0, Saturation = 0, Contrast = 0 })
	if R.prize then R.prize:Destroy(); R.prize = nil end
	local st = os.clock()
	local sv = R.saved.cf
	R.cam.from, R.cam.t0, R.cam.dur = cam.CFrame, os.clock(), 0.45
	local ch = me.Character
	local h = ch and ch:FindFirstChild("Head") :: BasePart?
	R.cam.to = if h then CFrame.new(h.Position + Vector3.new(0, 0.1, 0)) * sv.Rotation else sv
	R.cam.fov = R.saved.fov
	fadeOut({ R.box }, 0.45)
	while os.clock() - st < 0.45 do RunService.RenderStepped:Wait() end
	return answer :: string
end

-- ---------------------------------------------------------------- the one entry point
function Opening.play(kind: string, res: any, opts: any?): string
	if running then return "busy" end
	if type(res) ~= "table" or not res.ok or type(res.prize or res.item) ~= "table" then return "done" end
	if not LootTable.CONTAINERS[kind] then kind = "crate" end
	local base, flat = ground()
	if not base then return "done" end
	running = true
	local cam = workspace.CurrentCamera :: Camera
	local ui = buildUi()
	local R: Run = {
		ui = ui, kind = kind, res = res, opts = opts or {}, skip = false, skipAt = 0, result = nil,
		box = nil, prize = nil, base = base, flat = flat, height = 2.4, light = nil, rim = nil,
		cam = { from = cam.CFrame, to = cam.CFrame, t0 = os.clock(), dur = 0.01, shake = 0, shakeT = 0, fov = cam.FieldOfView },
		blur = new("BlurEffect", { Name = "JankLootBlur", Size = 0 }, cam),
		tint = new("ColorCorrectionEffect", { Name = "JankLootTint" }, cam),
		dof = new("DepthOfFieldEffect", { Name = "JankLootDof", Enabled = false, FarIntensity = 0.75, NearIntensity = 0, InFocusRadius = 4, FocusDistance = 8 }, cam),
		hidden = {}, saved = { cf = cam.CFrame, type = cam.CameraType, fov = cam.FieldOfView, loadoutOpen = me:GetAttribute("LoadoutOpen") },
		conns = {}, spin = 0, prizeY = 4, wid = nil, boxes = nil,
	}
	-- everything else steps aside: the HUD and menus, your hands (LoadoutOpen = a menu is up: Arsenal, Utility and
	-- Move hold still), the keys that would open other screens
	for _, g in (me:WaitForChild("PlayerGui")):GetChildren() do
		if g:IsA("ScreenGui") and g ~= ui.gui and g.Enabled then R.hidden[g] = true; g.Enabled = false end
	end
	me:SetAttribute("LoadoutOpen", true)
	me:SetAttribute("LootOpening", kind)
	pcall(function()
		local controls = require(me:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: any):GetControls()
		controls:Disable()
	end)
	ContextActionService:BindActionAtPriority("JankLootSink", function(_, state, io)
		if state == Enum.UserInputState.Begin and (io.KeyCode == Enum.KeyCode.Space or io.KeyCode == Enum.KeyCode.ButtonA) then
			R.skip = true
		end
		return Enum.ContextActionResult.Sink
	end, false, 3000, Enum.KeyCode.Space, Enum.KeyCode.ButtonA, Enum.KeyCode.L, Enum.KeyCode.B, Enum.KeyCode.G, Enum.KeyCode.Q,
		Enum.KeyCode.E, Enum.KeyCode.R, Enum.KeyCode.F, Enum.KeyCode.One, Enum.KeyCode.Two, Enum.KeyCode.Three, Enum.KeyCode.Four, Enum.KeyCode.Tab)
	ui.skip.MouseButton1Click:Connect(function() R.skip = true end)
	-- the camera: eased moves plus a little shake, every frame after Roblox's own camera
	RunService:BindToRenderStep("JankLootCam", Enum.RenderPriority.Camera.Value + 6, function()
		local c = workspace.CurrentCamera :: Camera
		c.CameraType = Enum.CameraType.Scriptable
		local u = easeOut((os.clock() - R.cam.t0) / math.max(0.01, R.cam.dur), 3)
		local cf = R.cam.from:Lerp(R.cam.to, u)
		local k = math.max(0, 1 - (os.clock() - R.cam.shakeT) / 0.35) * R.cam.shake
		if k > 0 then
			local t = os.clock()
			cf *= CFrame.new(math.sin(t * 71) * k * 0.3, math.sin(t * 83) * k * 0.3, 0) * CFrame.Angles(math.sin(t * 57) * k * 0.02, 0, math.sin(t * 61) * k * 0.02)
		end
		c.CFrame = cf
		c.FieldOfView += (R.cam.fov - c.FieldOfView) * 0.12
		local v = c.ViewportSize
		ui.scale.Scale = math.min(v.X / 1920, v.Y / 1080)
	end)
	-- a death or a match grabbing you ends it
	local function bail() R.result = "done"; R.skip = true end
	table.insert(R.conns, me:GetAttributeChangedSignal("Zone"):Connect(function() if me:GetAttribute("Zone") == "match" then bail() end end))
	local hum = me.Character and me.Character:FindFirstChildOfClass("Humanoid")
	if hum then table.insert(R.conns, hum.Died:Connect(bail)) end

	current = R
	local many = type(res.prizes) == "table" and #res.prizes > 1
	local ok, out = pcall(if many then runMany else run, R)
	current = nil
	restore(R)
	running = false
	if not ok then
		warn("[jankfire] the opening broke: " .. tostring(out))
		return "done"
	end
	return out
end

-- (for others: the shop's previews, LootShow.client.luau)
Opening.container = container
Opening.openBox = openBox
Opening.prizeModel = prizeModel

return Opening
