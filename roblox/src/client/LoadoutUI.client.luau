-- the loadout screen (L, or the LOADOUT button in the hub). keys 1 2 3 = primary / secondary / melee, 4 or G = the utility
-- slot (the item on G: Shared.Items, Utility.client.luau); the whole web roster
-- is on show (what isn't on roblox yet is a "coming soon" card); a big 3D preview on a showcase table you can drag round;
-- the weapon's stats and gimmick; the wraps along the bottom (hover to try one on, click to wear it). the camera eases
-- off to a showcase spot and the world behind goes soft. the server owns every pick (Loadout.luau): this only asks.
-- it only opens in the hub; closing it there re-arms you with the new picks. the look is Theme.luau's: dark plates and
-- cards, white text, one amber accent (the selected card, the main button). a weapon's own colour is a small chip
local Players = game:GetService("Players")
local UIS = game:GetService("UserInputService")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local WeaponModels = require(Shared:WaitForChild("WeaponModels"))
local Roster = require(Shared:WaitForChild("Roster"))
local Items = require(Shared:WaitForChild("Items")) -- (the utility slot's charges, for its card)
local GunHats = require(Shared:WaitForChild("GunHats")) -- the hat on each weapon (the HATS tab)
local GunSkins = require(Shared:WaitForChild("GunSkins")) -- each weapon's skin, another body from a crate (the SKINS tab)
local Hud = require(script.Parent:WaitForChild("Hud"))
local Sfx = require(script.Parent:WaitForChild("Sfx"))
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Loadout") :: RemoteFunction
local Tools = ReplicatedStorage:WaitForChild("JankfireTools")

local me = Players.LocalPlayer
local T = require(script.Parent:WaitForChild("Theme"))
local ACCENT, TEXT, GREY, DIM, RED = T.ACCENT, T.TEXT, T.MUTED, T.DIM, T.DANGER
local PANEL, CARD, INK, WHITE = T.BG, T.CARD, T.INK, Color3.new(1, 1, 1)
local FONT, FONT_BOLD, FONT_TITLE = T.FONT, T.FONT_BOLD, T.FONT_TITLE
local KEYS = { [Enum.KeyCode.One] = 1, [Enum.KeyCode.Two] = 2, [Enum.KeyCode.Three] = 3, [Enum.KeyCode.Four] = 4, [Enum.KeyCode.G] = 4 }
-- (plain words only: the owner's no-flavour-text rule. 18 Nov: the jokey subtitles under LOADOUT went, and these names)
local MODE_NAMES = { normal = "HANDLE", reverse = "BARREL", full = "WHOLE GUN" }
local SOON_GIMMICK = "not on roblox yet."

local function play(name: string) pcall(Sfx.play, name) end
local function tw(o: Instance, t: number, props: { [string]: any }, style: Enum.EasingStyle?, dir: Enum.EasingDirection?): Tween
	local x = TweenService:Create(o, TweenInfo.new(t, style or Enum.EasingStyle.Quad, dir or Enum.EasingDirection.Out), props)
	x:Play()
	return x
end

-- ---------------------------------------------------------------- little builders
local function new(class: string, props: { [string]: any }, parent: Instance?): any
	local o = Instance.new(class)
	for k, v in props do (o :: any)[k] = v end
	if parent then o.Parent = parent end
	return o
end
local function label(parent: Instance, text: string, size: number, pos: UDim2, sz: UDim2, color: Color3?, align: Enum.TextXAlignment?): TextLabel
	return new("TextLabel", {
		BackgroundTransparency = 1, FontFace = FONT, TextSize = size, Text = text, Position = pos, Size = sz,
		TextColor3 = color or WHITE, TextXAlignment = align or Enum.TextXAlignment.Left, TextWrapped = true,
	}, parent)
end
-- a panel: a dark plate with a hairline edge. returns its holder and its body
local function panel(parent: Instance, pos: UDim2, size: UDim2): (Frame, Frame)
	local holder = new("Frame", { BackgroundTransparency = 1, Position = pos, Size = size }, parent)
	local body = new("Frame", { Name = "Body", BackgroundColor3 = PANEL, BackgroundTransparency = 0.12, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 2 }, holder)
	T.corner(body, 8)
	T.edge(body)
	return holder, body
end

-- a button: flat, rounded. main = amber with dark text; the rest (white, chip = a small one) are dark cards with white
-- text. under the mouse it gets a shade lighter, pressed a shade darker
type Btn = { holder: Frame, face: TextButton, mark: Frame, kind: string, enabled: boolean, base: Color3, set: (Btn, string, boolean?, Color3?) -> () }
local function button(parent: Instance, text: string, kind: string, pos: UDim2, size: UDim2): Btn
	local holder = new("Frame", { BackgroundTransparency = 1, Position = pos, Size = size }, parent)
	local base = if kind == "main" then ACCENT else CARD
	local face = new("TextButton", {
		AutoButtonColor = false, BackgroundColor3 = base, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), FontFace = FONT_BOLD,
		TextSize = math.floor(size.Y.Offset * (if kind == "chip" then 0.5 else 0.32)), Text = text,
		TextColor3 = if kind == "main" then INK else TEXT, ZIndex = 2,
	}, holder)
	T.corner(face)
	if kind ~= "main" then T.edge(face) end
	-- (b.mark: a short amber line under the words, shown on the one of a row that's picked. amber FILL is kept for the
	-- one button that does something: equip)
	local mark = new("Frame", { Name = "Mark", BackgroundColor3 = ACCENT, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, -3), Size = UDim2.new(0.5, 0, 0, 2), Visible = false, ZIndex = 3 }, face)
	local b: Btn = { holder = holder, face = face, mark = mark, kind = kind, enabled = true, base = base, set = nil :: any }
	local function lit(c: Color3): Color3 return c:Lerp(WHITE, 0.14) end
	face.MouseEnter:Connect(function() if b.enabled then face.BackgroundColor3 = lit(b.base) end end)
	face.MouseLeave:Connect(function() face.BackgroundColor3 = b.base end)
	face.MouseButton1Down:Connect(function() if b.enabled then face.BackgroundColor3 = b.base:Lerp(Color3.new(0, 0, 0), 0.14) end end)
	face.MouseButton1Up:Connect(function() if b.enabled then face.BackgroundColor3 = lit(b.base) end end)
	-- its words, whether it can be pressed, and (optional) a colour to hold: the accent marks the one that's on
	b.set = function(self: Btn, t: string, enabled: boolean?, col: Color3?)
		self.face.Text = t
		self.enabled = enabled ~= false
		self.base = col or (if self.kind == "main" and self.enabled then ACCENT else CARD)
		self.face.BackgroundColor3 = self.base
		self.face.TextColor3 = if self.base == ACCENT then INK elseif self.enabled or col ~= nil then TEXT else DIM
	end
	return b
end

-- ---------------------------------------------------------------- newest first, and the NEW dots (18 Nov; the rest below)
-- (one table: this script is near Luau's 200-local limit)
local News: any = { gotAt = {}, fresh = {}, rev = 0, pending = {}, tabDots = {}, orderFor = "", view = "", refresh = function(_e: any) end }
-- the NEW dot: a small quiet amber dot in a card's top right corner (no words)
function News.dot(parent: GuiObject, z: number, inset: number?): Frame
	local d = new("Frame", { Name = "New", BackgroundColor3 = ACCENT, BorderSizePixel = 0, AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.new(1, -(inset or 5), 0, inset or 5), Size = UDim2.fromOffset(10, 10), ZIndex = z, Visible = false }, parent)
	T.corner(d, 5)
	new("UIStroke", { Color = Color3.fromRGB(8, 9, 12), Thickness = 1.5, Transparency = 0.25 }, d)
	return d
end
-- weapon mastery (18 Nov, docs/MASTERY.md): the camos per gun (Shared.Mastery: the WRAPS strip's last four, MASTERY as
-- their source) and the level bars on the weapon card and the armory cards (MasteryUI). in News: no locals to spare
News.MW = require(Shared:WaitForChild("Mastery")) :: any
News.MUI = require(script.Parent:WaitForChild("MasteryUI")) :: any
News.mbar = function(_e: any) end
-- (18 Nov: the owner's loadout wouldn't open, a nil damage on the Shopping Cart Cannon threw while the screen was
-- built. every number the screen prints goes through News.fmt: a nil or a word where a number should be prints "n/a",
-- never throws. every part of the screen updates through News.guard, each card and tile on its own: one that throws
-- is logged once per message and skipped, and the rest still draw)
function News.fmt(f: string, ...: any): string
	local ok, s = pcall(string.format, f, ...)
	return if ok then s else "n/a"
end
News.errs = {}
function News.guard(name: string, fn: any, ...: any)
	local ok, err = pcall(fn, ...)
	if not ok then
		local msg = name .. ": " .. tostring(err)
		if not News.errs[msg] then News.errs[msg] = true; warn("[jankfire] loadout " .. msg) end
	end
end

-- ---------------------------------------------------------------- state from the server (player attributes)
local function pick(): { [string]: string }
	local s = me:GetAttribute("LoadoutNext")
	local out = { primary = "redline", secondary = "marbles", melee = "katana", utility = "frag" }
	if type(s) == "string" then
		local i = 0
		for id in string.gmatch(s, "[^,]+") do
			i += 1
			local slot = Roster.SLOTS[i]
			if slot and Roster.byId[id] then out[slot] = id end
		end
	end
	return out
end
local function wrapOf(wid: string): (string, string)
	local id, md = WeaponModels.wrapFor(me, wid)
	return id or "default", md or "normal"
end
local function slotIndex(slot: string): number return table.find(Roster.SLOTS, slot) or 1 end
-- the key a slot is used with in a fight: 1 2 3 for the weapons, G for the item
local function keyOf(slot: string): string return if slot == "utility" then "G" else tostring(slotIndex(slot)) end
local function onKey(slot: string): string return if slot == "utility" then "ON G" else "ON KEY " .. keyOf(slot) end
local function hatOf(wid: string): string return GunHats.hatFor(me, wid) or "none" end
local function skinOf(wid: string): string return GunSkins.skinFor(me, wid) or "default" end
-- a skin's name and rarity: the loot session's LootTable (the web game's list), if it is in the place
-- the guns session's concepts (SkinSets.CONCEPTS) carry their working names only in their builders' notes
-- (tools/roblox/gun_sets_cute3.py, gun_sets_ducky_art.py); the ones with none (the owner's Tripo picks) keep their ids
local CONCEPT_NAMES = {
	ar_cute_a = "Velvet", pistol_cute_a = "Velvet", ar_cute_b = "Starlight", pistol_cute_b = "Starlight",
	ar_cute_c = "Glasswing", pistol_cute_c = "Glasswing", ar_cute_d = "Sweet Shop", pistol_cute_d = "Sweet Shop",
	ar_duckling = "Duckling", smg_duckling = "Duckling", pistol_duckling = "Duckling",
	ar_seraph = "Seraph Rifle (first build)", -- (a concept since 18 Nov: the Tripo one is the set's rifle)
} :: { [string]: string }
local function skinInfo(id: string): (string, string)
	local mod = Shared:FindFirstChild("LootTable")
	local ok, L = false, nil
	if mod then ok, L = pcall(require, mod) end
	local row = ok and type(L) == "table" and type(L.SKINS) == "table" and L.SKINS[id] or nil
	if type(row) == "table" and type(row[1]) == "string" then return row[1], (if type(row[2]) == "string" then row[2] else "common") end
	if CONCEPT_NAMES[id] then return CONCEPT_NAMES[id], "common" end
	return (string.gsub(string.gsub(id, "^[%a]+_", ""), "_", " ")), "common"
end

-- ---------------------------------------------------------------- models for the previews
-- every preview is scaled to the same size (radius 3 studs) so the table and the camera never need to change
local function shredderModel(skin: string?): Model?
	local src = (skin and Tools:FindFirstChild("Shredder@" .. skin)) or Tools:FindFirstChild("Shredder")
	if not src then return nil end
	local m = Instance.new("Model")
	local big: BasePart? = nil
	for _, d in src:GetDescendants() do
		if d:IsA("BasePart") and d.Transparency < 0.99 and d.Name ~= "SuckField" then
			local c = d:Clone()
			for _, x in c:GetChildren() do
				if not (x:IsA("SurfaceAppearance") or x:IsA("SpecialMesh") or x:IsA("Decal") or x:IsA("Texture")) then x:Destroy() end
			end
			c.Anchored = true
			c.Parent = m
			if not big or c.Size.Magnitude > big.Size.Magnitude then big = c end
		end
	end
	m.PrimaryPart = big
	return m
end
-- an item (the utility slot): its own model (ReplicatedStorage.JankfireItems), or a crate until that's there
local itemNames = { smoke = "x_smoke", frag = "x_frag", medkit = "x_medkit", bubble = "x_bubble", quiz = "x_calc" } -- (quiz: the Pop Quiz is the calculator)
local crate: (Color3) -> Model
local function itemModel(id: string): Model?
	local lib = ReplicatedStorage:FindFirstChild("JankfireItems")
	local t = lib and lib:FindFirstChild(itemNames[id] or ("x_" .. id))
	-- (a gadget whose model is a kit weapon: the Overdrive Rig is its two forearms, guns-remodel's w_rig_arms)
	if not t and id == "overdrive" then local wl = ReplicatedStorage:FindFirstChild("JankfireWeapons"); t = wl and wl:FindFirstChild("w_rig_arms") end
	if t and t:IsA("Model") then return t:Clone() end
	local e = Roster.byId[id]
	return crate(if e then e.color else GREY)
end
-- a weapon that isn't on roblox yet: a plain grey crate with one strap in its colour
crate = function(color: Color3): Model
	local m = Instance.new("Model")
	local function bx(size: Vector3, c: Color3, cf: CFrame, mat: Enum.Material?): Part
		return new("Part", { Anchored = true, Size = size, Color = c, CFrame = cf, Material = mat or Enum.Material.SmoothPlastic, TopSurface = Enum.SurfaceType.Smooth, BottomSurface = Enum.SurfaceType.Smooth }, m)
	end
	local box = bx(Vector3.new(3.6, 2.2, 2.2), Color3.fromRGB(84, 88, 98), CFrame.identity)
	for _, y in { -1.08, 1.08 } do for _, z in { -1.08, 1.08 } do bx(Vector3.new(3.7, 0.16, 0.16), Color3.fromRGB(46, 49, 58), CFrame.new(0, y, z)) end end
	bx(Vector3.new(0.5, 2.26, 2.26), color, CFrame.new(0.7, 0, 0))
	m.PrimaryPart = box
	return m
end
local function previewModel(id: string, hat: string?, skin: string?): (Model?, CFrame)
	local e = Roster.byId[id]
	local m: Model?
	if not e or not e.live then m = crate(if e then e.color else GREY)
	elseif e.slot == "utility" then m = (require(script.Parent:WaitForChild("GunPreview")) :: any).itemModel(id, if skin ~= "default" then skin else nil) -- (a gadget, or its skin)
	elseif id == "shredder" then m = shredderModel(if skin ~= "default" then skin else nil)
	else m = WeaponModels.build(id, 3, if skin ~= "default" then skin else nil) end
	if not m then return nil, CFrame.identity end
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then d.Anchored = true; d.CastShadow = false end
	end
	local _, size = m:GetBoundingBox()
	local r = size.Magnitude / 2
	local want = if e and e.live then 3 else 2.3 -- (a crate is all bulk: a size down, or it swallows the podium)
	-- its hat goes on after it is measured, so a hat never shrinks the weapon or moves it on the table
	local hm = nil
	if hat and hat ~= "none" and e and e.live then
		hm = if id == "shredder" then GunHats.attachToolCopy(m, Tools:FindFirstChild("Shredder") :: Instance, hat) else GunHats.attach(m, id, hat, 3, true)
	end
	if r > 1e-3 then pcall(function() m:ScaleTo(m:GetScale() * (want / r)) end) end
	if hm then hm.Parent = nil end
	local cf = m:GetBoundingBox()
	if hm then hm.Parent = m end
	return m, m:GetPivot():ToObjectSpace(cf)
end
local function viewport(parent: Instance, props: { [string]: any }): (ViewportFrame, Camera)
	local vp = new("ViewportFrame", {
		BackgroundTransparency = 1, Ambient = Color3.fromRGB(150, 153, 162), LightColor = Color3.fromRGB(255, 248, 240),
		LightDirection = Vector3.new(-0.5, -1, -0.7),
	}, parent)
	for k, v in props do (vp :: any)[k] = v end
	local cam = new("Camera", { FieldOfView = 34 }, vp)
	vp.CurrentCamera = cam
	return vp, cam
end

-- ---------------------------------------------------------------- the screen
local pg = me:WaitForChild("PlayerGui")
local gui = new("ScreenGui", { Name = "JankLoadout", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 30, ZIndexBehavior = Enum.ZIndexBehavior.Sibling, Enabled = false }, pg)
-- a full-screen button under everything: Modal frees the mouse from first person while the screen is up, and it eats clicks
local catcher = new("TextButton", { Text = "", AutoButtonColor = false, BackgroundColor3 = Color3.fromRGB(8, 9, 12), BackgroundTransparency = 0.28, Size = UDim2.fromScale(1, 1), Modal = true }, gui)
local stage = new("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(1920, 1080) }, gui)
local uiScale = new("UIScale", {}, stage)
local function fit()
	local v = (workspace.CurrentCamera :: Camera).ViewportSize
	uiScale.Scale = math.min(v.X / 1920, v.Y / 1080)
end

-- title
local titleBox = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(60, 34), Size = UDim2.fromOffset(560, 110) }, stage)
local title = label(titleBox, "LOADOUT", 46, UDim2.fromOffset(0, 0), UDim2.fromOffset(560, 54), TEXT)
title.FontFace = FONT_TITLE
new("Frame", { Name = "Rule", BackgroundColor3 = ACCENT, BorderSizePixel = 0, Position = UDim2.fromOffset(2, 62), Size = UDim2.fromOffset(44, 3) }, titleBox)
local subtitle = label(titleBox, "", 18, UDim2.fromOffset(2, 76), UDim2.fromOffset(560, 24), GREY) -- (only training's TRY line)

-- done + the save status
local done = button(stage, "DONE  [L]", "white", UDim2.fromOffset(1700, 40), UDim2.fromOffset(160, 50))
local saveLbl = label(stage, "", 16, UDim2.fromOffset(1360, 100), UDim2.fromOffset(500, 22), GREY, Enum.TextXAlignment.Right)

-- ---------------------------------------------------------------- slot cards (left)
type Card = { slot: string, holder: Frame, body: TextButton, st: UIStroke, name: TextLabel, wrap: TextLabel, bar: Frame, vp: ViewportFrame, cam: Camera, key: string? }
local cards: { Card } = {}
local state = { slot = "primary", focus = "redline", hover = nil :: string?, filter = "all", open = false, hatHover = nil :: string?, modeHover = nil :: string?, skinHover = nil :: string? }
local refresh: () -> () = function() end
local hatsRefresh: (any) -> () = function() end -- (the HATS tab: set below)
local skinsRefresh: (any) -> () = function() end -- (the SKINS tab: set below)

-- (four cards since the utility slot: 102 tall on a 110 step, so the armory below keeps its place)
for i, slot in Roster.SLOTS do
	local y = 156 + (i - 1) * 110
	local holder = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(60, y), Size = UDim2.fromOffset(520, 102) }, stage)
	local body = new("TextButton", { Text = "", AutoButtonColor = false, BackgroundColor3 = PANEL, BackgroundTransparency = 0.12, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 2 }, holder)
	T.corner(body, 8)
	local st = T.edge(body)
	T.key(body, keyOf(slot), UDim2.fromOffset(22, 14)).Size = UDim2.fromOffset(28, 28)
	label(body, Roster.SLOT_NAMES[slot], 16, UDim2.fromOffset(66, 11), UDim2.fromOffset(220, 20), GREY).FontFace = FONT_BOLD
	local name = label(body, "", 28, UDim2.fromOffset(66, 32), UDim2.fromOffset(234, 36), TEXT)
	name.FontFace = FONT_BOLD; name.TextScaled = true
	new("UITextSizeConstraint", { MaxTextSize = 28 }, name)
	local wrap = label(body, "", 16, UDim2.fromOffset(66, 70), UDim2.fromOffset(240, 22), GREY)
	-- (the weapon's own colour: a short bar down the card's left edge)
	local bar = new("Frame", { BorderSizePixel = 0, Position = UDim2.fromOffset(0, 14), Size = UDim2.fromOffset(3, 74), ZIndex = 3 }, body)
	T.corner(bar, 2)
	-- (its picture: on a lighter backing and close up, so a dark gun reads on the dark card)
	local vp, cam = viewport(body, {
		Position = UDim2.fromOffset(300, 10), Size = UDim2.fromOffset(206, 82), BackgroundColor3 = T.CARD_HI, BackgroundTransparency = 0.35,
		Ambient = Color3.fromRGB(205, 208, 216),
	})
	T.corner(vp)
	cam.FieldOfView = 40
	local c: Card = { slot = slot, holder = holder, body = body, st = st, name = name, wrap = wrap, bar = bar, vp = vp, cam = cam }
	body.MouseButton1Click:Connect(function()
		state.slot = slot
		state.focus = pick()[slot]
		play("click")
		refresh()
	end)
	body.MouseEnter:Connect(function() body.BackgroundColor3 = CARD end)
	body.MouseLeave:Connect(function() body.BackgroundColor3 = PANEL end)
	table.insert(cards, c)
end

-- ---------------------------------------------------------------- the armory: every weapon for the chosen slot (left, below)
local _, armBody = panel(stage, UDim2.fromOffset(60, 598), UDim2.fromOffset(520, 442))
local armTitle = label(armBody, "THE ARMORY", 18, UDim2.fromOffset(20, 14), UDim2.fromOffset(300, 26), TEXT)
armTitle.FontFace = FONT_TITLE
local armCount = label(armBody, "", 16, UDim2.fromOffset(200, 16), UDim2.fromOffset(300, 22), GREY, Enum.TextXAlignment.Right)
local armList = new("ScrollingFrame", {
	BackgroundTransparency = 1, BorderSizePixel = 0, Position = UDim2.fromOffset(14, 52), Size = UDim2.fromOffset(496, 378),
	CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollingDirection = Enum.ScrollingDirection.Y,
	ScrollBarThickness = 6, ScrollBarImageColor3 = DIM, ZIndex = 3,
}, armBody)
new("UIGridLayout", { CellSize = UDim2.fromOffset(232, 82), CellPadding = UDim2.fromOffset(12, 12), SortOrder = Enum.SortOrder.LayoutOrder }, armList)
new("UIPadding", { PaddingTop = UDim.new(0, 4), PaddingLeft = UDim.new(0, 4), PaddingRight = UDim.new(0, 12), PaddingBottom = UDim.new(0, 8) }, armList)
type ArmCard = { id: string, btn: TextButton, st: UIStroke, tag: TextLabel, chip: Frame, color: Color3, new: Frame }
local armCards: { ArmCard } = {}
local armSlot = ""
local function buildArmory()
	if armSlot == state.slot then return end
	armSlot = state.slot
	for _, c in armCards do c.btn:Destroy() end
	table.clear(armCards)
	if News.bundleTiles then News.bundleTiles(state.slot) end -- (the weapon bundles, for coins, over the primaries: 19 Nov)
	local live, soon = 0, 0
	for i, e in Roster.list do
		if e.slot ~= state.slot then continue end
		if e.live then live += 1 else soon += 1 end
		local btn = new("TextButton", { Text = "", AutoButtonColor = false, BackgroundColor3 = CARD, BorderSizePixel = 0, LayoutOrder = i, ZIndex = 4 }, armList)
		T.corner(btn)
		local st = T.edge(btn)
		local chip = new("Frame", { BackgroundColor3 = e.color, BackgroundTransparency = if e.live then 0 else 0.6, BorderSizePixel = 0, Position = UDim2.fromOffset(12, 14), Size = UDim2.fromOffset(3, 54), ZIndex = 5 }, btn)
		T.corner(chip, 2)
		local nm = label(btn, e.name, 19, UDim2.fromOffset(26, 8), UDim2.fromOffset(196, 40), TEXT)
		nm.FontFace = FONT_BOLD; nm.ZIndex = 5; nm.TextScaled = true; nm.TextTransparency = if e.live then 0 else 0.45
		new("UITextSizeConstraint", { MaxTextSize = 19 }, nm)
		local tag = label(btn, "", 16, UDim2.fromOffset(26, 51), UDim2.fromOffset(196, 20), GREY)
		tag.FontFace = FONT_BOLD; tag.ZIndex = 5
		btn.MouseButton1Click:Connect(function()
			state.focus = e.id
			play("click")
			refresh()
		end)
		btn.MouseEnter:Connect(function() if state.focus ~= e.id then btn.BackgroundColor3 = T.CARD_HI end end)
		btn.MouseLeave:Connect(function() btn.BackgroundColor3 = CARD end)
		table.insert(armCards, { id = e.id, btn = btn, st = st, tag = tag, chip = chip, color = e.color, new = News.dot(btn, 6, 8) })
		News.guard("armory level " .. tostring(e.id), News.MUI.card, btn, e) -- (its weapon level: LV n and a hairline bar)
	end
	-- (just the count, the owner, 18 Nov: "get rid of where it says live ready free for now etc"; coming soon only when there are some)
	local word = if state.slot == "utility" then "gadget" else "weapon"
	armCount.Text = News.fmt("%d %s%s", live, word, if live == 1 then "" else "s") .. (if soon > 0 then News.fmt(" · %d coming soon", soon) else "")
	armList.CanvasPosition = Vector2.zero
end

-- ---------------------------------------------------------------- the preview: a showcase table with the weapon spinning over it (centre)
local previewBox = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(610, 104), Size = UDim2.fromOffset(800, 736) }, stage)
local vp, vcam = viewport(previewBox, { Size = UDim2.fromScale(1, 1), Active = true })
vcam.FieldOfView = 30
vcam.CFrame = CFrame.lookAt(Vector3.new(0, 3.4, 15.5), Vector3.new(0, -1.1, 0))
do -- a low round podium under the weapon: a dark base, a dark top and a thin amber rim. small, so the weapon leads
	local function p(size: Vector3, c: Color3, cf: CFrame, mat: Enum.Material?)
		new("Part", { Anchored = true, Shape = Enum.PartType.Cylinder, Size = size, Color = c, CFrame = cf, Material = mat or Enum.Material.SmoothPlastic, TopSurface = Enum.SurfaceType.Smooth, BottomSurface = Enum.SurfaceType.Smooth }, vp)
	end
	local up = CFrame.Angles(0, 0, math.pi / 2) -- (a cylinder standing up)
	p(Vector3.new(0.25, 5.0, 5.0), Color3.fromRGB(34, 37, 44), CFrame.new(0, -3.78, 0) * up)
	p(Vector3.new(0.5, 4.4, 4.4), Color3.fromRGB(52, 56, 66), CFrame.new(0, -3.4, 0) * up)
	-- the rim sits just under the top, so only its outer edge shows: the one amber line on the stage
	p(Vector3.new(0.05, 4.48, 4.48), ACCENT, CFrame.new(0, -3.19, 0) * up)
end
local nameBox = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 18), Size = UDim2.new(1, 0, 0, 60) }, previewBox)
local bigName = label(nameBox, "", 44, UDim2.fromOffset(0, 0), UDim2.fromScale(1, 1), TEXT, Enum.TextXAlignment.Center)
bigName.FontFace = FONT_TITLE; bigName.TextScaled = true; bigName.TextWrapped = false
new("UITextSizeConstraint", { MaxTextSize = 44 }, bigName)
-- a weapon that isn't on roblox yet: a quiet badge over its crate
local soonStamp = label(previewBox, "COMING SOON", 15, UDim2.fromScale(0.5, 0.5), UDim2.fromOffset(180, 38), GREY, Enum.TextXAlignment.Center)
soonStamp.FontFace = FONT_BOLD; soonStamp.AnchorPoint = Vector2.new(0.5, 0.5); soonStamp.BackgroundColor3 = PANEL; soonStamp.BackgroundTransparency = 0.1
T.corner(soonStamp); T.edge(soonStamp)
local hint = label(previewBox, "drag to spin it  ·  1 2 3 G pick a slot", 16, UDim2.new(0, 0, 1, -16), UDim2.new(1, 0, 0, 22), GREY, Enum.TextXAlignment.Center)
local toast = label(previewBox, "", 20, UDim2.new(0.5, 0, 0, 84), UDim2.fromOffset(700, 30), ACCENT, Enum.TextXAlignment.Center)
toast.FontFace = FONT_BOLD; toast.AnchorPoint = Vector2.new(0.5, 0); toast.TextTransparency = 1
local toastN = 0
local function say(text: string, color: Color3?)
	toastN += 1
	local n = toastN
	toast.Text = text; toast.TextColor3 = color or ACCENT
	toast.TextTransparency = 0
	task.delay(2.4, function()
		if toastN ~= n then return end
		tw(toast, 0.3, { TextTransparency = 1 })
	end)
end

-- spin: slow on its own, drag to turn it (it keeps a little of your flick)
local spin = { yaw = math.pi / 2, pitch = 0.12, vel = 0.45, drag = false, lastX = 0, lastY = 0, dragT = -math.huge }
local shown: { id: string, model: Model, rel: CFrame, hat: string? }? = nil
local shownWrap = ""
vp.InputBegan:Connect(function(io)
	if io.UserInputType == Enum.UserInputType.MouseButton1 or io.UserInputType == Enum.UserInputType.Touch then
		spin.drag, spin.lastX, spin.lastY = true, io.Position.X, io.Position.Y
	end
end)
UIS.InputChanged:Connect(function(io)
	if not spin.drag then return end
	if io.UserInputType ~= Enum.UserInputType.MouseMovement and io.UserInputType ~= Enum.UserInputType.Touch then return end
	local dx, dy = io.Position.X - spin.lastX, io.Position.Y - spin.lastY
	spin.lastX, spin.lastY = io.Position.X, io.Position.Y
	spin.yaw += dx * 0.012
	spin.pitch = math.clamp(spin.pitch + dy * 0.006, -0.7, 0.9)
	spin.vel = dx * 0.6
	spin.dragT = os.clock()
end)
UIS.InputEnded:Connect(function(io)
	if io.UserInputType == Enum.UserInputType.MouseButton1 or io.UserInputType == Enum.UserInputType.Touch then spin.drag = false end
end)

-- ---------------------------------------------------------------- the info panel (right)
local _, info = panel(stage, UDim2.fromOffset(1440, 136), UDim2.fromOffset(420, 698))
-- (the weapon's own colour: a short bar beside its name)
local infoChip = new("Frame", { BackgroundColor3 = GREY, BorderSizePixel = 0, Position = UDim2.fromOffset(22, 24), Size = UDim2.fromOffset(3, 32) }, info)
T.corner(infoChip, 2)
local infoName = label(info, "", 32, UDim2.fromOffset(36, 18), UDim2.fromOffset(362, 44), TEXT)
infoName.FontFace = FONT_BOLD; infoName.TextScaled = true
new("UITextSizeConstraint", { MaxTextSize = 32 }, infoName)
local chipRow = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(22, 72), Size = UDim2.fromOffset(380, 24) }, info)
new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 8), SortOrder = Enum.SortOrder.LayoutOrder }, chipRow)
local function tagChip(order: number): (Frame, TextLabel)
	local f = new("Frame", { BackgroundColor3 = CARD, BorderSizePixel = 0, Size = UDim2.fromOffset(0, 26), AutomaticSize = Enum.AutomaticSize.X, LayoutOrder = order }, chipRow)
	T.corner(f, 4)
	new("UIPadding", { PaddingLeft = UDim.new(0, 9), PaddingRight = UDim.new(0, 9) }, f)
	local l = label(f, "", 15, UDim2.new(), UDim2.fromScale(0, 1), GREY, Enum.TextXAlignment.Center)
	l.FontFace = FONT_BOLD; l.AutomaticSize = Enum.AutomaticSize.X; l.TextWrapped = false
	return f, l
end
local _, slotChipL = tagChip(1)
local _, liveChipL = tagChip(2)
liveChipL.RichText = true
-- what it is, then its gimmick in a box, then its four numbers: each as tall as it needs, one under the other, so the
-- spare room is all in one place (above the equip button) and not in the middle of the panel
local words = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(22, 114), Size = UDim2.fromOffset(376, 490) }, info)
new("UIListLayout", { Padding = UDim.new(0, 18), SortOrder = Enum.SortOrder.LayoutOrder }, words)
local infoDesc = label(words, "", 17, UDim2.new(), UDim2.new(1, 0, 0, 0), TEXT)
infoDesc.AutomaticSize = Enum.AutomaticSize.Y; infoDesc.TextYAlignment = Enum.TextYAlignment.Top; infoDesc.LayoutOrder = 1
local gimBox = new("Frame", { BackgroundColor3 = CARD, BorderSizePixel = 0, Size = UDim2.new(1, 0, 0, 0), AutomaticSize = Enum.AutomaticSize.Y, LayoutOrder = 2 }, words)
T.corner(gimBox); T.edge(gimBox)
new("UIPadding", { PaddingLeft = UDim.new(0, 14), PaddingRight = UDim.new(0, 14), PaddingTop = UDim.new(0, 11), PaddingBottom = UDim.new(0, 13) }, gimBox)
new("UIListLayout", { Padding = UDim.new(0, 5), SortOrder = Enum.SortOrder.LayoutOrder }, gimBox)
local gimTitle = label(gimBox, "THE GIMMICK", 14, UDim2.new(), UDim2.new(1, 0, 0, 16), ACCENT)
gimTitle.FontFace = FONT_BOLD; gimTitle.LayoutOrder = 1
local gimText = label(gimBox, "", 16, UDim2.new(), UDim2.new(1, 0, 0, 0), TEXT)
gimText.AutomaticSize = Enum.AutomaticSize.Y; gimText.TextYAlignment = Enum.TextYAlignment.Top; gimText.LayoutOrder = 2
type StatRow = { name: TextLabel, val: TextLabel, fill: Frame }
local statRows: { StatRow } = {}
for i = 1, 4 do
	local row = new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 50), LayoutOrder = 2 + i }, words)
	local name = label(row, "", 16, UDim2.fromOffset(0, 3), UDim2.fromOffset(200, 22), GREY)
	name.FontFace = FONT_BOLD
	local val = label(row, "", 20, UDim2.new(1, -228, 0, 0), UDim2.fromOffset(228, 26), TEXT, Enum.TextXAlignment.Right)
	val.FontFace = FONT_BOLD
	local bg = new("Frame", { BackgroundColor3 = T.TRACK, BorderSizePixel = 0, Position = UDim2.fromOffset(0, 34), Size = UDim2.new(1, 0, 0, 10) }, row)
	T.corner(bg, 5)
	local fill = new("Frame", { BackgroundColor3 = TEXT, BorderSizePixel = 0, Size = UDim2.fromScale(0, 1) }, bg)
	T.corner(fill, 5)
	table.insert(statRows, { name = name, val = val, fill = fill })
end
local equipBtn = button(info, "EQUIP IT", "main", UDim2.fromOffset(22, 614), UDim2.fromOffset(376, 60))
News.mbar = News.MUI.panel(info, words) -- (the weapon's level under its name: LV, XP, the next camo)
-- buying a Robux weapon (Unlocks.ROBUX) here once they aren't free for everyone (Unlocks.robuxFree): the equip button
-- halves, Robux on the left (the shop's prompt, ShopBuy "weapon:<id>"), Coins on the right (the server takes them,
-- JankfireRemotes.Purchases "brass", after a second press to be sure; not enough: the shop's COINS tab). prices:
-- Shop.MONEY.weapons. 18 Nov
News.Shop = require(Shared:WaitForChild("Shop")) :: any
News.brassBtn = button(info, "", "white", UDim2.fromOffset(214, 614), UDim2.fromOffset(184, 60))
News.brassBtn.holder.Visible = false
News.armT = 0
function News.weaponOffer(wid: string): any
	local ok, o = pcall(News.Shop.weaponOffer, wid)
	return if ok then o else nil
end
function News.digits(n: number): string
	local s = tostring(math.floor(n))
	while true do
		local k
		s, k = string.gsub(s, "^(%d+)(%d%d%d)", "%1,%2")
		if k == 0 then return s end
	end
end
function News.split(on: boolean)
	equipBtn.holder.Size = UDim2.fromOffset(if on then 184 else 376, 60)
	News.brassBtn.holder.Visible = on
end
-- (19 Nov, the owner: "make sure only skins cost robux!": a Robux weapon is bought with coins here, one button)
function News.coinsOnly(): boolean
	local S = News.Shop
	return S ~= nil and type(S.coinsOnly) == "function" and S.coinsOnly() == true
end
function News.buyLook(e: any)
	local o = News.weaponOffer(e.id)
	local S = News.Shop
	if News.coinsOnly() then
		local armed = News.arm == e.id and os.clock() - News.armT < 4
		equipBtn:set(if armed then "SURE? " .. News.digits(o.coins) .. " COINS" else "BUY · " .. News.digits(o.coins) .. " COINS", true)
		return
	end
	equipBtn:set(News.digits(o.robux) .. " ROBUX", S.ROBUX == true and S.productFor(o) ~= nil)
	local armed = News.arm == e.id and os.clock() - News.armT < 4
	local have = tonumber(me:GetAttribute("Brass")) or 0
	News.brassBtn:set(if armed then "SURE? " .. News.digits(o.coins) else News.digits(o.coins) .. " COINS", true, if have >= o.coins then nil else CARD)
end
-- an EARLY unlock (19 Nov): a weapon that opens at a level, with coins before then (Shop.earlyOn; the server takes the
-- coins: Purchases "early", after a second press to be sure; not enough: the shop's COINS tab)
function News.earlyPrice(wid: string): number?
	local S = News.Shop
	if not (S and type(S.earlyOn) == "function" and S.earlyOn()) then return nil end
	local ok, v = pcall(S.earlyPrice, wid)
	return if ok and type(v) == "number" then v else nil
end
function News.payEarly(e: any)
	local price = News.earlyPrice(e.id)
	if not price then return end
	if (tonumber(me:GetAttribute("Brass")) or 0) < price then
		play("empty"); say("not enough coins.", RED)
		local okS, ShopUI = pcall(require, script.Parent:WaitForChild("ShopUI"))
		if okS and type(ShopUI) == "table" and type(ShopUI.open) == "function" then News.close(); task.delay(0.1, ShopUI.open, "coins") end
		return
	end
	if News.arm ~= e.id or os.clock() - News.armT > 4 then
		News.arm, News.armT = e.id, os.clock()
		play("click"); refresh()
		task.delay(4.1, function() if News.arm == e.id then News.arm = nil; refresh() end end)
		return
	end
	News.arm = nil
	local f = ReplicatedStorage:FindFirstChild("JankfireRemotes")
	local r = f and f:FindFirstChild("Purchases")
	local ok, res = pcall(function() return (r :: RemoteFunction):InvokeServer("early", e.id) end)
	if ok and type(res) == "table" and res.ok then
		play("ting"); say(string.lower(e.name) .. " is yours for good. equip it.")
	else
		play("empty"); say(if ok and type(res) == "table" and type(res.why) == "string" then res.why else "that didn't work.", RED)
	end
	refresh()
end
function News.payRobux(e: any)
	local o = News.weaponOffer(e.id)
	local f = ReplicatedStorage:FindFirstChild("JankfireRemotes")
	local r = f and f:FindFirstChild("ShopBuy")
	if not o or not News.Shop.ROBUX or not News.Shop.productFor(o) or not (r and r:IsA("RemoteEvent")) then
		play("empty"); say("not for sale for robux yet.", RED)
		return
	end
	(r :: RemoteEvent):FireServer(o.id)
end
News.brassBtn.face.MouseButton1Click:Connect(function()
	if not News.brassBtn.enabled then return end
	local e = Roster.byId[state.focus]
	if e then News.payBrass(e) end
end)
-- a Robux weapon for coins (the server takes them: Purchases "brass", after a second press)
function News.payBrass(e: any)
	if News.buyFor ~= e.id or not News.weaponOffer(e.id) then return end
	if (tonumber(me:GetAttribute("Brass")) or 0) < News.weaponOffer(e.id).coins then
		-- (not enough coins: the shop's COINS tab)
		play("empty"); say("not enough coins.", RED)
		local okS, ShopUI = pcall(require, script.Parent:WaitForChild("ShopUI"))
		if okS and type(ShopUI) == "table" and type(ShopUI.open) == "function" then News.close(); task.delay(0.1, ShopUI.open, "coins") end
		return
	end
	if News.arm ~= e.id or os.clock() - News.armT > 4 then
		News.arm, News.armT = e.id, os.clock()
		play("click"); refresh()
		task.delay(4.1, function() if News.arm == e.id then News.arm = nil; refresh() end end)
		return
	end
	News.arm = nil
	local f = ReplicatedStorage:FindFirstChild("JankfireRemotes")
	local r = f and f:FindFirstChild("Purchases")
	local ok, res = pcall(function() return (r :: RemoteFunction):InvokeServer("brass", e.id) end)
	if ok and type(res) == "table" and res.ok then
		play("ting"); say(string.lower(e.name) .. " is yours. equip it.")
	else
		play("empty"); say(if ok and type(res) == "table" and type(res.why) == "string" then res.why else "that didn't work.", RED)
	end
	refresh()
end

-- WEAPON BUNDLES for coins (19 Nov, the owner: "only skins cost robux"): Assault and Explosives as two tiles at the top of
-- the primaries. a tile shows the server's quote (Purchases "wbquote": the weapons you can't carry yet and the
-- cosmetics you lack, Shop.WBUNDLE_OFF percent under their coin prices); a press arms it, the second buys ("wbundle")
News.bTiles = {} :: { any }
function News.bundleTiles(slot: string)
	for _, t in News.bTiles do t.btn:Destroy() end
	table.clear(News.bTiles)
	local S = News.Shop
	if slot ~= "primary" or not (S and type(S.weaponBundlesOn) == "function" and S.weaponBundlesOn()) then return end
	for i, o in S.weaponBundles do
		local btn = new("TextButton", { Text = "", AutoButtonColor = false, BackgroundColor3 = CARD, BorderSizePixel = 0, LayoutOrder = -10 + i, ZIndex = 4 }, armList)
		T.corner(btn)
		T.edge(btn, ACCENT, 0.45)
		local nm = label(btn, string.upper(o.name) .. " BUNDLE", 19, UDim2.fromOffset(16, 8), UDim2.fromOffset(206, 40), TEXT)
		nm.FontFace = FONT_BOLD; nm.ZIndex = 5; nm.TextScaled = true
		new("UITextSizeConstraint", { MaxTextSize = 19 }, nm)
		local tag = label(btn, "", 16, UDim2.fromOffset(16, 51), UDim2.fromOffset(206, 20), ACCENT)
		tag.FontFace = FONT_BOLD; tag.ZIndex = 5
		local t = { id = o.id, btn = btn, tag = tag, price = nil :: number? }
		table.insert(News.bTiles, t)
		task.spawn(News.quoteBundle, t)
		btn.MouseButton1Click:Connect(function() News.buyBundle(t) end)
	end
end
function News.quoteBundle(t: any)
	local f = ReplicatedStorage:FindFirstChild("JankfireRemotes")
	local r = f and f:FindFirstChild("Purchases")
	if not r then return end
	local ok, res = pcall(function() return (r :: RemoteFunction):InvokeServer("wbquote", t.id) end)
	if not t.btn.Parent then return end
	if not (ok and type(res) == "table" and res.ok) then t.tag.Text = ""; return end
	t.price = tonumber(res.price) or 0
	local nW = if type(res.weapons) == "table" then #res.weapons else 0
	local armed = News.arm == t.id and os.clock() - News.armT < 4
	t.tag.Text = if t.price <= 0 then "YOURS" elseif armed then "SURE? " .. News.digits(t.price) .. " COINS"
		else (if nW > 0 then nW .. " WEAPONS · " else "") .. News.digits(t.price) .. " COINS"
end
function News.buyBundle(t: any)
	if not t.price or t.price <= 0 then return end
	if (tonumber(me:GetAttribute("Brass")) or 0) < t.price then
		play("empty"); say("not enough coins.", RED)
		local okS, ShopUI = pcall(require, script.Parent:WaitForChild("ShopUI"))
		if okS and type(ShopUI) == "table" and type(ShopUI.open) == "function" then News.close(); task.delay(0.1, ShopUI.open, "coins") end
		return
	end
	if News.arm ~= t.id or os.clock() - News.armT > 4 then
		News.arm, News.armT = t.id, os.clock()
		play("click"); task.spawn(News.quoteBundle, t)
		task.delay(4.1, function() if News.arm == t.id then News.arm = nil; if t.btn.Parent then News.quoteBundle(t) end end end)
		return
	end
	News.arm = nil
	local f = ReplicatedStorage:FindFirstChild("JankfireRemotes")
	local r = f and f:FindFirstChild("Purchases")
	local ok, res = pcall(function() return (r :: RemoteFunction):InvokeServer("wbundle", t.id) end)
	if ok and type(res) == "table" and res.ok then
		play("ting"); say("the bundle is yours. its weapons are unlocked for good.")
	else
		play("empty"); say(if ok and type(res) == "table" and type(res.why) == "string" then res.why else "that didn't work.", RED)
	end
	refresh()
	for _, x in News.bTiles do task.spawn(News.quoteBundle, x) end
end

-- the stats of a live weapon come from the weapon table itself (Weapons.luau); the rest from the web numbers
local function statsFor(id: string): { Roster.Stat }
	local e = Roster.byId[id]
	local w = Weapons.list[id]
	if not e then return {} end
	if not w or w.slot == "none" or not e.live then return e.stats or {} end
	-- (a weapon may have no damage, range or rate of its own: the Shopping Cart Cannon runs people over with its cart,
	-- the TV Remote pauses them. every number is read with tonumber and printed with News.fmt: "n/a" and an empty bar,
	-- never a throw. 18 Nov: a nil damage here kept the owner's loadout from opening at all)
	local S = tonumber(Weapons.S) or 1
	local pel = tonumber(w.pellets) or 1
	local dmg, range, grow = tonumber(w.dmg), tonumber(w.range), tonumber(w.grow) or 0
	local cd, rate, rateMax, mag = tonumber(w.cd), tonumber(w.rate), tonumber(w.rateMax), tonumber(w.mag)
	local out = {}
	table.insert(out, { label = "DAMAGE", text = if not dmg then "n/a" elseif pel > 1 then News.fmt("%g x%d", dmg, pel) else News.fmt("%g", dmg), bar = if dmg then math.min(1, dmg * pel / 120) else 0 })
	if w.kind == "melee" then
		local r = 1 / (if cd and cd > 0 then cd else 1)
		table.insert(out, { label = "SWING RATE", text = News.fmt("%.3g/s", r), bar = math.min(1, r / 22) })
		table.insert(out, { label = "REACH", text = if range then News.fmt("%.2g m, +%.2g a kill", range / S, grow / S) else "n/a", bar = if range then math.min(1, math.sqrt(math.max(0, range / S / 500))) else 0 })
		table.insert(out, { label = "MAG", text = "n/a", bar = 0 })
	else
		local r = rate or (if cd and cd > 0 then 1 / cd else 1)
		table.insert(out, { label = "FIRE RATE", text = if rateMax then News.fmt("%g-%g/s", r, rateMax) else News.fmt("%.2g/s", r), bar = math.min(1, (rateMax or r) / 22) })
		table.insert(out, { label = "RANGE", text = if range then News.fmt("%g m", range / S) else "n/a", bar = if range then math.min(1, math.sqrt(math.max(0, range / S / 500))) else 0 })
		table.insert(out, { label = "MAG", text = if mag then tostring(mag) else "no reload", bar = math.min(1, (mag or 60) / 60) })
	end
	return out
end

-- ---------------------------------------------------------------- the wraps (bottom)
local _, wbar = panel(stage, UDim2.fromOffset(610, 852), UDim2.fromOffset(1250, 188))
local wTitle = label(wbar, "WRAPS", 18, UDim2.fromOffset(20, 12), UDim2.fromOffset(110, 26), TEXT)
wTitle.FontFace = FONT_TITLE
local wName = label(wbar, "", 16, UDim2.fromOffset(130, 12), UDim2.fromOffset(420, 26), TEXT)
wName.FontFace = FONT_BOLD
wName.RichText = true; wName.TextWrapped = false
local modeBtns: { [string]: Btn } = {}
-- the three modes: HANDLE paints the handle side (the _wzA pieces), BUSINESS END the barrel end (_wzB), FULL SEND the
-- whole gun; the first two leave the rest in its factory paint, so the gun comes out two-tone. each chip carries a small
-- two-block gun (stock end left, muzzle right) with the painted half lit, and hovering a chip tries it on the preview
local MODE_HALVES = { normal = { true, false }, reverse = { false, true }, full = { true, true } }
for i, md in Roster.MODES do
	local b = button(wbar, MODE_NAMES[md], "chip", UDim2.fromOffset(1250 - 20 - (4 - i) * 154, 10), UDim2.fromOffset(146, 30))
	new("UIPadding", { PaddingLeft = UDim.new(0, 16) }, b.face)
	for k, lit in MODE_HALVES[md] do
		local blk = new("Frame", {
			BackgroundColor3 = if lit then TEXT else DIM, BorderSizePixel = 0, AnchorPoint = Vector2.new(0, 0.5),
			Position = UDim2.new(0, 8 + (k - 1) * 9, 0.5, 0), Size = UDim2.fromOffset(8, if k == 1 then 10 else 6), ZIndex = 4,
		}, b.holder)
		T.corner(blk, 2)
	end
	b.face.MouseEnter:Connect(function() state.modeHover = md; if state.open then refresh() end end)
	b.face.MouseLeave:Connect(function() if state.modeHover == md then state.modeHover = nil; if state.open then refresh() end end end)
	b.face.SelectionGained:Connect(function() state.modeHover = md; if state.open then refresh() end end) -- (a controller's pick tries it on, as the mouse's hover)
	b.face.SelectionLost:Connect(function() if state.modeHover == md then state.modeHover = nil; if state.open then refresh() end end end)
	modeBtns[md] = b
end
local filters = { "all", "common", "rare", "epic", "legendary" }
local filterBtns: { [string]: TextButton } = {}
for i, f in filters do
	local t = new("TextButton", {
		Text = string.upper(f), FontFace = FONT_BOLD, TextSize = 16, AutoButtonColor = false, BackgroundTransparency = 1, RichText = true,
		TextColor3 = GREY, TextXAlignment = Enum.TextXAlignment.Left, Position = UDim2.fromOffset(22 + (i - 1) * 128, 45), Size = UDim2.fromOffset(122, 22),
	}, wbar)
	filterBtns[f] = t
end
label(wbar, "hover to try it on · click to wear it", 15, UDim2.fromOffset(700, 46), UDim2.fromOffset(530, 20), GREY, Enum.TextXAlignment.Right)
local swatchRow = new("ScrollingFrame", {
	BackgroundTransparency = 1, BorderSizePixel = 0, Position = UDim2.fromOffset(12, 72), Size = UDim2.fromOffset(1226, 114),
	CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.X, ScrollingDirection = Enum.ScrollingDirection.X,
	ScrollBarThickness = 5, ScrollBarImageColor3 = DIM, VerticalScrollBarInset = Enum.ScrollBarInset.None, ZIndex = 3,
}, wbar)
new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 8), SortOrder = Enum.SortOrder.LayoutOrder, VerticalAlignment = Enum.VerticalAlignment.Top }, swatchRow) -- (the hats row's spacing)
new("UIPadding", { PaddingLeft = UDim.new(0, 6), PaddingTop = UDim.new(0, 14), PaddingRight = UDim.new(0, 12) }, swatchRow)
-- (its ‹ › arrows: added below, once arrows() exists)
local noPaint = new("TextLabel", {
	BackgroundColor3 = PANEL, BackgroundTransparency = 0, BorderSizePixel = 0, Position = UDim2.fromOffset(12, 72), Size = UDim2.fromOffset(1226, 108),
	FontFace = FONT, TextSize = 16, TextColor3 = GREY, Text = "not on roblox yet.", ZIndex = 10, Visible = false, Active = true,
}, wbar)

-- a swatch: a paint chip with the wrap's palette laid on it like its pattern, a thin line under it in its rarity's colour
local function bands(cols: { Color3 }): ColorSequence
	local n = #cols
	local kp = {}
	for i, c in cols do
		local a, b = (i - 1) / n, i / n
		table.insert(kp, ColorSequenceKeypoint.new(if i == 1 then 0 else a + 0.001, c))
		table.insert(kp, ColorSequenceKeypoint.new(if i == n then 1 else b, c))
	end
	return ColorSequence.new(kp)
end
-- a wrap with a picture (ReplicatedStorage.JankfireWraps, docs/WRAP-TEXTURES.md) shows a piece of it, about 9 x 6 cm of
-- gun, so its stars, petals and stripes read at chip size
local WRAPS = ReplicatedStorage:WaitForChild("JankfireWraps", 10)
local function paintChip(chip: Frame, wr: Roster.Wrap)
	local sa = WRAPS and WRAPS:FindFirstChild(wr.id)
	local img = sa and sa:GetAttribute("Swatch")
	if type(img) == "string" then
		chip.BackgroundColor3 = WHITE
		local im = new("ImageLabel", { Image = img, BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ImageRectSize = Vector2.new(384, 256), ZIndex = 5 }, chip)
		T.corner(im, 4)
		-- a band of the wrap's second colour along the bottom: the dark tone the other half of the gun takes
		local dark = sa:GetAttribute("Dark")
		if typeof(dark) == "Color3" then
			local band = new("Frame", { BackgroundColor3 = dark, BorderSizePixel = 0, AnchorPoint = Vector2.new(0, 1), Position = UDim2.fromScale(0, 1), Size = UDim2.new(1, 0, 0.24, 0), ZIndex = 5 }, chip)
			T.corner(band, 4)
		end
		return
	end
	local pal = wr.pal
	if #pal == 0 then
		chip.BackgroundColor3 = T.TRACK
		label(chip, "OG", 15, UDim2.new(), UDim2.fromScale(1, 1), GREY, Enum.TextXAlignment.Center).FontFace = FONT_BOLD
		return
	end
	if #pal == 1 then chip.BackgroundColor3 = pal[1]; return end
	chip.BackgroundColor3 = WHITE
	local g = new("UIGradient", { Rotation = 35 }, chip)
	if wr.pat == "fade" then
		local kp = {}
		for i, c in pal do table.insert(kp, ColorSequenceKeypoint.new((i - 1) / (#pal - 1), c)) end
		g.Color = ColorSequence.new(kp)
	elseif wr.pat == "speck" then
		local cols = {}
		for i = 1, 7 do table.insert(cols, if i % 3 == 0 then pal[2 + (math.floor(i / 3) - 1) % (#pal - 1)] else pal[1]) end
		g.Color = bands(cols)
	elseif wr.pat == "bands" then
		g.Color = bands(pal)
	else
		local cols = {}
		for i = 1, 6 do table.insert(cols, pal[(i - 1) % #pal + 1]) end
		g.Color = bands(cols)
	end
end
local function finishWord(wr: Roster.Wrap): string?
	local sa = WRAPS and WRAPS:FindFirstChild(wr.id)
	if sa then local f = sa:GetAttribute("Finish"); return if type(f) == "string" then f else nil end
	if wr.neon then return "GLOWS" end
	local m = wr.mat
	if m == "Metal" or m == "Foil" then return "SHINY" end
	if m == "Glass" or m == "Ice" or m == "ForceField" then return "SEE-THRU" end
	if m == "CrackedLava" then return "HOT" end
	if m and m ~= "Plastic" then return string.upper(m) end
	return nil
end
-- what you own (Loot.luau, the Loot remote): a wrap or hat is won for ONE gun ("<id>@<weapon>"), so the bars show
-- a lock on what you don't own for the gun being edited, and where it is won. you can still hover it to try it on; the
-- server won't put it on (Loadout.luau)
local owned: { [string]: { [string]: boolean } } = {}
local ownedKnown = false
-- (the owner, 18 Nov 2026: "if you unlock a spray it should be placed at the start of the scroll"): News.gotAt[type][key]
-- = its place in the loot save's own list (bigger = newer: inventory .order); News.fresh[type][key] = its count while
-- it's NEW (inventory .fresh), until its strip has been shown and you've moved on, or you picked it (News.flush: "seen")
function News.note(t: string, key: string)
	News.pending[t] = News.pending[t] or {}
	News.pending[t][key] = true
end
function News.flush()
	local f = ReplicatedStorage:FindFirstChild("JankfireRemotes")
	local r = f and f:FindFirstChild("Loot")
	for t, keys in News.pending do
		local list = {}
		for k in keys do
			table.insert(list, k)
			if News.fresh[t] then News.fresh[t][k] = nil end
		end
		if #list > 0 and r and r:IsA("RemoteFunction") then
			task.spawn(function() pcall(function() (r :: RemoteFunction):InvokeServer("seen", t, list) end) end)
		end
	end
	table.clear(News.pending)
end
local function owns(t: string, id: string): boolean
	if not ownedKnown then return true end -- (not heard yet, or the owner's Studio unlock: lock nothing)
	if t == "hat" and id == "none" then return true end
	local row: any = if t == "wrap" then Roster.wrapById[id] elseif t == "hat" then GunHats.HATS[id] else nil
	if row and row.rarity == "free" then return true end
	local set = owned[t]
	return set ~= nil and set[id .. "@" .. state.focus] == true
end
local function fetchOwned()
	local f = ReplicatedStorage:FindFirstChild("JankfireRemotes")
	local r = f and f:FindFirstChild("Loot")
	if not (r and r:IsA("RemoteFunction")) then return end
	local ok, res = pcall(function() return (r :: RemoteFunction):InvokeServer("inventory") end)
	if ok and type(res) == "table" and res.ok and type(res.owned) == "table" then
		owned = {}
		for t, ids in res.owned do
			local set = {}
			for _, id in ids do set[id] = true end
			owned[t] = set
		end
		ownedKnown = res.devAll ~= true
		News.gotAt, News.fresh = {}, {}
		for t, keys in (if type(res.order) == "table" then res.order else {}) :: any do
			local g = {}
			for i, k in keys do g[k] = i end
			News.gotAt[t] = g
		end
		for t, keys in (if type(res.fresh) == "table" then res.fresh else {}) :: any do
			local fs = {}
			for k, n in keys do if type(k) == "string" then fs[k] = if type(n) == "number" then n else 1 end end
			News.fresh[t] = fs
		end
		News.rev += 1
	end
end
-- a lock over a card you don't own: the card dims, a small padlock in its corner
local function lockOver(parent: GuiObject, z: number): Frame
	local f = new("Frame", { Name = "Lock", BackgroundColor3 = Color3.fromRGB(8, 9, 12), BackgroundTransparency = 0.5, BorderSizePixel = 0,
		Size = UDim2.fromScale(1, 1), ZIndex = z, Visible = false }, parent)
	T.corner(f, 4)
	local l = label(f, "\u{1F512}", 13, UDim2.new(1, -33, 0, 2), UDim2.fromOffset(31, 17), WHITE, Enum.TextXAlignment.Center)
	l.Name = "Glyph"; l.ZIndex = z + 1
	return f
end
-- TRY IN TRAINING (Loadout.luau, the owner's ask): in the training hall and its playground you can wear anything, owned or
-- not; it isn't saved, and your own loadout comes back when you leave. the server says when (the attribute Trying, and
-- its zone); a thing you don't own shows TRY there instead of the lock
local function trying(): boolean
	local z = me:GetAttribute("Zone")
	return me:GetAttribute("Trying") == true or z == "training" or z == "playground"
end
local function lockLook(lk: Frame)
	local g = lk:FindFirstChild("Glyph") :: TextLabel?
	local t = trying()
	if g then g.Text = if t then "TRY" else "🔒"; g.TextColor3 = if t then ACCENT else WHITE; g.FontFace = FONT_BOLD end
	lk.BackgroundTransparency = if t then 0.82 else 0.5
end
-- a strip that can outgrow its panel (the owner, 17 Nov: "The weapons run off and you can [not] scroll through!!"):
-- a horizontal ScrollingFrame (wheel, drag, swipe) with a ‹ and a › at its ends that page along it, shown only when
-- there's more that way; into(row, child) brings a card into view (the one you wear, when the tab opens)
-- (CanvasPosition is in screen pixels, like the Absolute* sizes, even under a UIScale (the desktop fit, the phone
-- layout): measured in Play, 17 Nov. so everything here is in screen pixels; k stays for the record)
local function span(row: ScrollingFrame): (number, number, number)
	local view = row.AbsoluteWindowSize.X
	return 1, view, math.max(0, row.AbsoluteCanvasSize.X - view)
end
local function arrows(row: ScrollingFrame, parent: GuiObject)
	local function btn(txt: string, right: boolean): TextButton
		local b = new("TextButton", { Text = txt, AutoButtonColor = false, BackgroundColor3 = Color3.fromRGB(16, 18, 22), BackgroundTransparency = 0.15,
			BorderSizePixel = 0, AnchorPoint = Vector2.new(if right then 1 else 0, 0.5), FontFace = FONT_BOLD, TextSize = 26, TextColor3 = TEXT,
			Size = UDim2.fromOffset(34, 64), ZIndex = 20, Visible = false }, parent)
		T.corner(b, 6)
		b.MouseButton1Click:Connect(function()
			local _, view, maxX = span(row)
			local x = math.clamp(row.CanvasPosition.X + (if right then view * 0.8 else -view * 0.8), 0, maxX)
			TweenService:Create(row, TweenInfo.new(0.25, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CanvasPosition = Vector2.new(x, 0) }):Play()
		end)
		return b
	end
	local l, r = btn("‹", false), btn("›", true)
	local function place()
		local pos, size = row.Position, row.Size
		l.Position = UDim2.new(pos.X.Scale, pos.X.Offset + 2, pos.Y.Scale, pos.Y.Offset + size.Y.Offset / 2)
		r.Position = UDim2.new(pos.X.Scale + size.X.Scale, pos.X.Offset + size.X.Offset - 2, pos.Y.Scale, pos.Y.Offset + size.Y.Offset / 2)
		local _, _, maxX = span(row)
		l.Visible = row.Visible and maxX > 1 and row.CanvasPosition.X > 1
		r.Visible = row.Visible and maxX > 1 and row.CanvasPosition.X < maxX - 1
	end
	for _, prop in { "CanvasPosition", "AbsoluteCanvasSize", "AbsoluteWindowSize", "Position", "Size", "Visible" } do
		row:GetPropertyChangedSignal(prop):Connect(place)
	end
	place()
end
local function into(row: ScrollingFrame, child: GuiObject)
	local k, view, maxX = span(row)
	local x0 = (child.AbsolutePosition.X - row.AbsolutePosition.X) / k + row.CanvasPosition.X
	local w = child.AbsoluteSize.X / k
	if x0 < row.CanvasPosition.X then row.CanvasPosition = Vector2.new(math.clamp(x0 - 40, 0, maxX), 0)
	elseif x0 + w > row.CanvasPosition.X + view then row.CanvasPosition = Vector2.new(math.clamp(x0 + w - view + 40, 0, maxX), 0) end
end
local swatchLocks: { [string]: Frame } = {}
arrows(swatchRow, wbar)
local hatLocks: { [string]: Frame } = {}
type Swatch = { wr: Roster.Wrap, holder: Frame, chip: TextButton, shadow: Frame, st: UIStroke, tick: TextLabel, new: Frame }
local swatches: { Swatch } = {}
local onSwatch: (Roster.Wrap) -> () = function() end
local onHover: (string?) -> () = function() end
for i, wr in News.MW.wrapList() do -- (Roster.wraps, then the mastery camos)
	local holder = new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromOffset(86, 92), LayoutOrder = i, ZIndex = 4 }, swatchRow)
	local shadow = new("Frame", { BackgroundColor3 = Roster.RARITY[wr.rarity].color, BorderSizePixel = 0, Position = UDim2.fromOffset(4, 57), Size = UDim2.fromOffset(78, 3), ZIndex = 4 }, holder)
	T.corner(shadow, 2)
	local chip = new("TextButton", { Text = "", AutoButtonColor = false, BorderSizePixel = 0, Position = UDim2.fromOffset(4, 0), Size = UDim2.fromOffset(78, 52), ZIndex = 5 }, holder)
	T.corner(chip, 4)
	local st = T.edge(chip, nil, 0.8)
	paintChip(chip, wr)
	for _, d in chip:GetChildren() do if d:IsA("TextLabel") then d.ZIndex = 6 end end
	local fw = finishWord(wr)
	if fw then
		-- (the finish word, on a small dark pill in the chip's corner)
		local l = label(chip, fw, 12, UDim2.new(1, -3, 1, -3), UDim2.fromOffset(0, 16), WHITE, Enum.TextXAlignment.Center)
		l.AnchorPoint = Vector2.new(1, 1); l.AutomaticSize = Enum.AutomaticSize.X; l.FontFace = FONT_BOLD; l.ZIndex = 6; l.TextWrapped = false
		l.BackgroundColor3 = PANEL; l.BackgroundTransparency = 0.2
		T.corner(l, 3)
		new("UIPadding", { PaddingLeft = UDim.new(0, 4), PaddingRight = UDim.new(0, 4) }, l)
	end
	local tick = label(chip, "✓", 20, UDim2.fromOffset(2, 0), UDim2.fromOffset(22, 22), WHITE, Enum.TextXAlignment.Center)
	tick.ZIndex = 7; tick.Visible = false; tick.TextStrokeColor3 = Color3.new(0, 0, 0); tick.TextStrokeTransparency = 0.3
	local nm = label(holder, wr.name, 14, UDim2.fromOffset(0, 64), UDim2.fromOffset(86, 28), GREY, Enum.TextXAlignment.Center)
	nm.TextYAlignment = Enum.TextYAlignment.Top; nm.ZIndex = 5
	chip.MouseEnter:Connect(function() onHover(wr.id) end)
	chip.MouseLeave:Connect(function() onHover(nil) end)
	chip.SelectionGained:Connect(function() onHover(wr.id) end) -- (a controller's pick tries it on, as the mouse's hover)
	chip.SelectionLost:Connect(function() onHover(nil) end)
	chip.MouseButton1Click:Connect(function() onSwatch(wr) end)
	table.insert(swatches, { wr = wr, holder = holder, chip = chip, shadow = shadow, st = st, tick = tick, new = News.dot(chip, 9) })
	swatchLocks[wr.id] = lockOver(chip, 8)
end
local function applyFilter()
	-- (a mastery camo shows once its picture is in the place: Mastery.live)
	for _, s in swatches do s.holder.Visible = (state.filter == "all" or s.wr.rarity == state.filter or s.wr.id == "default") and (not s.wr.mastery or News.MW.live(s.wr.id)) end
	for f, t in filterBtns do
		-- (a dot in the rarity's colour; the name goes white on the one that's picked)
		local dot = if f == "all" then "" else ('<font color="#%s">●</font>  '):format(Roster.RARITY[f].color:ToHex())
		t.Text = dot .. string.upper(f)
		t.TextColor3 = if f == state.filter then TEXT else GREY
	end
	swatchRow.CanvasPosition = Vector2.zero
end
for f, t in filterBtns do
	t.MouseButton1Click:Connect(function() state.filter = f; play("click"); applyFilter() end)
end

-- ---------------------------------------------------------------- refresh: everything from the server's attributes + what's focused
local cardKey: { [string]: string } = {}
local function cardModel(c: Card, id: string)
	local wid, md = wrapOf(id)
	local k = id .. "|" .. wid .. "|" .. md .. "|" .. hatOf(id) .. "|" .. skinOf(id)
	if cardKey[c.slot] == k then return end
	cardKey[c.slot] = k
	for _, d in c.vp:GetChildren() do if d:IsA("Model") then d:Destroy() end end
	local m, rel = previewModel(id, hatOf(id), skinOf(id))
	if not m then return end
	WeaponModels.wrap(m, wid, md)
	m:PivotTo(CFrame.Angles(0.18, math.pi / 2, 0) * rel:Inverse())
	m.Parent = c.vp
	c.cam.CFrame = CFrame.lookAt(Vector3.new(0, 0.8, 5.6), Vector3.new(0, 0, 0))
end

local function showPreview(id: string)
	local wid, md = wrapOf(id)
	if state.hover and Roster.byId[id] and Roster.byId[id].live then wid = state.hover end
	if state.modeHover and Roster.byId[id] and Roster.byId[id].live then md = state.modeHover end
	local hat = if state.hatHover and Roster.byId[id] and Roster.byId[id].live then state.hatHover else hatOf(id)
	local skin = if state.skinHover and Roster.byId[id] and Roster.byId[id].live then state.skinHover else skinOf(id)
	if shown and shown.id == id and shown.hat == hat and shown.skin == skin then
		local k = wid .. "/" .. md
		if shownWrap ~= k then shownWrap = k; WeaponModels.wrap(shown.model, wid, md) end
		return
	end
	local turnIn = not shown or shown.id ~= id
	if shown then shown.model:Destroy(); shown = nil end
	local m, rel = previewModel(id, hat, skin)
	if not m then return end
	WeaponModels.wrap(m, wid, md)
	shownWrap = wid .. "/" .. md
	m.Parent = vp
	shown = { id = id, model = m, rel = rel, hat = hat, skin = skin }
	if turnIn then spin.yaw -= 0.7 end -- a small turn-in on the swap (it eases back to its rest pose; not for a hat)
end

refresh = function()
	local p = pick()
	-- (each part below updates through News.guard, every card and tile on its own: one bad weapon, look or stat is
	-- logged and skipped, and the rest still draw. 18 Nov)
	for _, c in cards do
		News.guard("slot card " .. tostring(c.slot), function()
			local id = p[c.slot]
			local e = Roster.byId[id]
			local on = c.slot == state.slot
			c.name.Text = e.name
			c.bar.BackgroundColor3 = e.color
			local wid, md = wrapOf(id)
			local wr = Roster.wrapById[wid]
			local item = if c.slot == "utility" then Items.list[id] else nil
			c.wrap.Text = if item then News.fmt("%d %s · %g s each", item.charges, if item.charges == 1 then "charge" else "charges", item.recharge)
				elseif wid == "default" then "factory paint" else ("wrap: %s · %s"):format(wr and wr.name or wid, string.lower(MODE_NAMES[md] or md))
			c.st.Color = if on then ACCENT else WHITE
			c.st.Transparency = if on then 0 else T.EDGE_A
			c.st.Thickness = if on then 2 else 1
			cardModel(c, id)
		end)
	end
	News.guard("armory", buildArmory)
	for _, a in armCards do
		News.guard("armory tile " .. tostring(a.id), function()
			local e = Roster.byId[a.id]
			local equipped = p[state.slot] == a.id
			local focused = state.focus == a.id
			a.st.Color = if focused then ACCENT else WHITE
			a.st.Transparency = if focused then 0 elseif equipped then 0.4 else T.EDGE_A
			a.st.Thickness = if focused then 2 else 1
			-- (a weapon's colour shows on the one you're looking at and the one you carry; the rest of the list stays grey)
			a.chip.BackgroundColor3 = if focused or equipped then a.color else T.TRACK
			-- (weapons open by level, a few are Robux and free for now: Unlocks, docs/PROGRESSION.md. training: anything)
			local U = require(Shared:WaitForChild("Unlocks")) :: any
			local okU, whyU = U.forPlayer(me, a.id)
			okU = okU or trying()
			-- (no status words under the name, the owner, 18 Nov: the key it's on when you carry it, COMING SOON, a Robux
			-- weapon you don't have its price, a locked one what unlocks it; nothing else)
			local o = if not okU and U.robux(a.id) then News.weaponOffer(a.id) else nil
			-- (a level's weapon can be unlocked early with coins: "LV 7 · or 1,500 COINS", 19 Nov)
			local ep = if not okU and not o and type(whyU) == "string" and string.sub(whyU, 1, 6) == "LEVEL " then News.earlyPrice(a.id) else nil
			a.tag.Text = if equipped then onKey(state.slot) elseif not e.live then "COMING SOON"
				elseif o then (if News.coinsOnly() then News.digits(o.coins) .. " COINS" else News.digits(o.robux) .. " ROBUX")
				elseif ep then "LV " .. string.sub(whyU :: string, 7) .. " · or " .. News.digits(ep) .. " COINS"
				elseif not okU then whyU or "LOCKED" else ""
			a.tag.TextColor3 = if equipped then ACCENT elseif o then TEXT elseif not e.live or not okU then DIM else GREY
			a.btn.BackgroundTransparency = if e.live and not okU then 0.45 else 0
		end)
	end
	-- the focused weapon
	local e = Roster.byId[state.focus] or Roster.byId[p[state.slot]]
	if not e then return end
	local w = Weapons.list[e.id]
	News.guard("header", function()
		bigName.Text = string.upper(e.name)
		soonStamp.Visible = not e.live
		infoName.Text = e.name; infoChip.BackgroundColor3 = e.color
	end)
	News.guard("mastery bar", News.mbar, e)
	News.guard("info", function()
		slotChipL.Text = Roster.SLOT_NAMES[e.slot]
		liveChipL.Text = if e.live then '<font color="#6fd08a">●</font>  LIVE ON ROBLOX' else "COMING SOON"
		liveChipL.TextColor3 = if e.live then TEXT else DIM
		infoDesc.Text = if e.live and w and w.desc ~= "" then w.desc else string.lower(string.sub(e.desc, 1, 1)) .. string.sub(e.desc, 2)
		gimText.Text = if e.gimmick ~= "" then e.gimmick else SOON_GIMMICK
	end)
	News.guard("stats", function()
		local okS, st = pcall(statsFor, e.id)
		if not okS or type(st) ~= "table" then
			local why = st
			News.guard("stats of " .. tostring(e.id), function() error(why, 0) end)
			st = {}
		end
		for i, row in statRows do
			News.guard("stat row " .. i, function()
				local s = st[i]
				row.name.Text = if s then tostring(s.label or "") else ""
				row.val.Text = if s then tostring(s.text or "") else ""
				local b = if s then tonumber(s.bar) else nil
				local full = if b and b == b and s.text ~= "n/a" then math.clamp(b, 0.03, 1) else 0 -- (nothing to measure: an empty track)
				tw(row.fill, 0.2, { Size = UDim2.fromScale(full, 1) })
			end)
		end
	end)
	News.guard("equip button", function()
		local okE, whyE = (require(Shared:WaitForChild("Unlocks")) :: any).forPlayer(me, e.id)
		-- (a Robux weapon you don't have while they aren't free: buy it here, Robux or Brass. 18 Nov)
		local buy = e.live and not okE and not trying() and p[e.slot] ~= e.id and whyE == "ROBUX" and News.weaponOffer(e.id) ~= nil
		News.buyFor = if buy then e.id else nil
		News.split(buy and not News.coinsOnly())
		-- (a level's weapon, early with coins: UNLOCK NOW, then SURE?)
		local ep = if e.live and not okE and not trying() and p[e.slot] ~= e.id and type(whyE) == "string" and string.sub(whyE, 1, 6) == "LEVEL "
			then News.earlyPrice(e.id) else nil
		News.earlyFor = if ep then e.id else nil
		if not e.live then equipBtn:set("COMING SOON", false)
		elseif buy then News.buyLook(e)
		elseif ep then
			local armed = News.arm == e.id and os.clock() - News.armT < 4
			equipBtn:set(if armed then "SURE? " .. News.digits(ep) .. " COINS" else "UNLOCK NOW · " .. News.digits(ep) .. " COINS", true)
		elseif not okE and not trying() and p[e.slot] ~= e.id then equipBtn:set(if whyE == "ROBUX" then "ROBUX" else (whyE or "LOCKED") .. " UNLOCKS IT", false)
		elseif p[e.slot] == e.id then equipBtn:set(onKey(e.slot) .. "  ✓", false, T.CARD_HI); equipBtn.face.TextColor3 = ACCENT
		else equipBtn:set(if e.slot == "utility" then "EQUIP IT · G" else "EQUIP IT · KEY " .. keyOf(e.slot), true) end
	end)
	News.guard("preview", showPreview, e.id)
	-- wraps for the focused weapon
	local wid, md = "default", nil
	News.guard("worn wrap", function() wid, md = wrapOf(e.id) end)
	News.guard("wrap name", function()
		local shownId = if state.hover and e.live then state.hover else wid
		local wr = Roster.wrapById[shownId]
		if wr then
			local rc = if wr.mastery then ACCENT else Roster.RARITY[wr.rarity].color
			wName.Text = ('%s  <font color="#%s">%s</font>%s'):format(wr.name, rc:ToHex(),
				if wr.mastery then News.fmt("MASTERY  ·  LV %d", News.MW.byId[wr.id] and News.MW.byId[wr.id].level or 0) else string.upper(Roster.RARITY[wr.rarity].name),
				if (state.hover and state.hover ~= wid) or (state.modeHover and state.modeHover ~= md) then '  <font color="#9ca2ac">(trying it on)</font>' else "")
		end
	end)
	noPaint.Visible = not e.live -- (the gadgets take paint since 18 Nov)
	noPaint.Text = "not on roblox yet."
	for _, s in swatches do
		News.guard("wrap tile " .. tostring(s.wr and s.wr.id), function()
			local on = s.wr.id == wid
			s.tick.Visible = on
			local lk = swatchLocks[s.wr.id]
			if lk then lk.Visible = not owns("wrap", s.wr.id); lockLook(lk) end
			-- (a mastery camo's lock says the weapon level that unlocks it)
			local mg = if s.wr.mastery and lk and not trying() then lk:FindFirstChild("Glyph") :: TextLabel? else nil
			if mg then mg.Text = News.fmt("LV %d", News.MW.byId[s.wr.id] and News.MW.byId[s.wr.id].level or 0); mg.FontFace = FONT_BOLD; mg.Size = UDim2.fromOffset(44, 17); mg.Position = UDim2.new(1, -46, 0, 2) end
			s.st.Color = if on then ACCENT else WHITE
			s.st.Transparency = if on then 0 else 0.8
			s.st.Thickness = if on then 2 else 1
		end)
	end
	News.guard("paint modes", function()
		local paints = e.live
		for m, b in modeBtns do
			local on = m == md and paints
			b:set(MODE_NAMES[m], paints, if on then T.CARD_HI else nil)
			b.mark.Visible = on
		end
	end)
	News.guard("hats", hatsRefresh, e)
	News.guard("skins", skinsRefresh, e)
	News.guard("new marks", News.refresh, e)
	News.guard("save line", function()
		local save = me:GetAttribute("LoadoutSave")
		saveLbl.Text = if save == "cloud" then "saves to your account" elseif save == "off" then "NOT SAVING · studio has API access off" else "fetching your stuff..."
		saveLbl.TextColor3 = if save == "off" then RED else GREY
	end)
end

-- (one bad weapon, look or row must never keep the screen from opening or updating: an error in a refresh is caught and
-- logged once per message, and the rest goes on. 18 Nov: a nil in one weapon's stats threw inside setOpen, before the
-- screen showed, and left it shut for good)
do
	local inner = refresh
	local lastErr = ""
	refresh = function()
		local ok, err = pcall(inner)
		if not ok and tostring(err) ~= lastErr then
			lastErr = tostring(err)
			warn("[jankfire] loadout refresh: " .. lastErr)
		end
	end
end

-- ---------------------------------------------------------------- talking to the server
local function ask(...: any): (boolean, string?)
	local ok, res = pcall(function(...) return Remote:InvokeServer(...) end, ...)
	if not ok or type(res) ~= "table" then return false, "the server didn't answer" end
	return res.ok == true, if type(res.why) == "string" then res.why else nil
end

equipBtn.face.MouseButton1Click:Connect(function()
	if not equipBtn.enabled then return end
	local e = Roster.byId[state.focus]
	if not e or not e.live then return end
	if News.buyFor == e.id then if News.coinsOnly() then News.payBrass(e) else News.payRobux(e) end; return end -- (a Robux weapon you don't have: coins since 19 Nov)
	if News.earlyFor == e.id then News.payEarly(e); return end -- (a level's weapon, early with coins)
	local ok, why = ask("pick", e.slot, e.id)
	if ok then
		state.slot = e.slot
		play("ting")
		say(if e.slot == "utility" then ("%s on G. close this to grab it."):format(string.lower(e.name))
			else News.fmt("%s on key %d. close this to grab it.", string.lower(e.name), slotIndex(e.slot)))
	else
		play("empty")
		say(why or "that didn't work.", RED)
	end
	refresh()
end)

onSwatch = function(wr)
	local e = Roster.byId[state.focus]
	if not e or not e.live then return end
	local _, md = wrapOf(e.id)
	-- (a mastery camo says its level here; any other look you don't own: the server's refusal names where it comes from,
	-- VIP, the daily reward or spray cans. 18 Nov)
	if not owns("wrap", wr.id) and not trying() and wr.mastery then
		play("empty")
		say(News.fmt("%s for the %s unlocks at %s level %d.", wr.name, string.lower(e.name), string.lower(e.name), News.MW.byId[wr.id] and News.MW.byId[wr.id].level or 0), RED)
		return
	end
	local ok, why = ask("wrap", e.id, wr.id, md)
	if ok then
		play("click")
		say(if wr.id == "default" then "factory paint." else ("%s, wrapped in %s."):format(string.lower(e.name), wr.name))
	else
		play("empty"); say(why or "that didn't work.", RED)
	end
	refresh()
end
onHover = function(id)
	state.hover = id
	if state.open then refresh() end
end
for md, b in modeBtns do
	b.face.MouseButton1Click:Connect(function()
		local e = Roster.byId[state.focus]
		if not e or not e.live then return end
		local wid = wrapOf(e.id)
		local ok, why = ask("wrap", e.id, wid, md)
		if ok then play("click") else say(why or "that didn't work.", RED) end
		refresh()
	end)
end

-- ---------------------------------------------------------------- the hats (bottom, a tab beside the wraps)
-- a small hat that sits on the weapon (GunHats.luau): one per weapon, hover to try it on, click to put it on. it shares
-- the wraps' place at the bottom: two tabs over the bar switch between them. the cards show each hat turning slowly
-- with its moving bits going (GunHatsClient)
local tab = "wraps"
local tabBtns: { [string]: Btn } = {}
for i, t in { "wraps", "hats", "skins" } do
	tabBtns[t] = button(stage, string.upper(t), "chip", UDim2.fromOffset(610 + (i - 1) * 112, 808), UDim2.fromOffset(104, 34))
end
for t, b in tabBtns do News.tabDots[t] = News.dot(b.face, 4, 6) end -- (a dot on a tab with something NEW for this weapon)
local hHolder, hbar = panel(stage, UDim2.fromOffset(610, 852), UDim2.fromOffset(1250, 188))
hHolder.Visible = false
local hTitle = label(hbar, "HATS", 18, UDim2.fromOffset(20, 12), UDim2.fromOffset(110, 26), TEXT)
hTitle.FontFace = FONT_TITLE
local hName = label(hbar, "", 16, UDim2.fromOffset(130, 12), UDim2.fromOffset(520, 26), TEXT)
hName.FontFace = FONT_BOLD; hName.RichText = true; hName.TextWrapped = false
label(hbar, "hover to try it on · click to put it on", 15, UDim2.fromOffset(700, 14), UDim2.fromOffset(530, 20), GREY, Enum.TextXAlignment.Right)
local hatRow = new("ScrollingFrame", {
	BackgroundTransparency = 1, BorderSizePixel = 0, Position = UDim2.fromOffset(12, 48), Size = UDim2.fromOffset(1226, 136),
	CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.X, ScrollingDirection = Enum.ScrollingDirection.X,
	ScrollBarThickness = 5, ScrollBarImageColor3 = DIM, VerticalScrollBarInset = Enum.ScrollBarInset.None, ZIndex = 3,
}, hbar)
new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 8), SortOrder = Enum.SortOrder.LayoutOrder }, hatRow)
new("UIPadding", { PaddingLeft = UDim.new(0, 6), PaddingRight = UDim.new(0, 12) }, hatRow)
arrows(hatRow, hbar)
local noHats = new("TextLabel", {
	BackgroundColor3 = PANEL, BackgroundTransparency = 0, BorderSizePixel = 0, Position = UDim2.fromOffset(12, 48), Size = UDim2.fromOffset(1226, 132),
	FontFace = FONT, TextSize = 16, TextColor3 = GREY, Text = "not on roblox yet.", ZIndex = 10, Visible = false, Active = true,
}, hbar)
-- (each hat on a card: its own little stage, seen from the front left; the googly eyes and the halo, which lean
-- toward the player holding the gun, turned to face you)
local CARD_TURN = { eyes = math.pi, halo = math.pi }
type HatCard = { id: string, chip: TextButton, st: UIStroke, tick: TextLabel, spin: Model?, holder: Frame, new: Frame }
local hatCards: { HatCard } = {}
local onHat: (string) -> () = function() end
-- (the cards share the row: 102 px each up to eleven, narrower past that so None and every hat fit (round 12 made it
-- thirteen), never under 86: past that the row scrolls)
local CW = math.max(86, math.min(102, math.floor((1226 - 6 - 8 * (#GunHats.ORDER - 1)) / #GunHats.ORDER)))
for i, hid in GunHats.ORDER do
	local h = GunHats.HATS[hid]
	local holder = new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromOffset(CW, 128), LayoutOrder = i, ZIndex = 4 }, hatRow)
	local chip = new("TextButton", { Text = "", AutoButtonColor = false, BackgroundColor3 = CARD, BorderSizePixel = 0, Size = UDim2.fromOffset(CW, 88), ZIndex = 5 }, holder)
	T.corner(chip, 4)
	local st = T.edge(chip, nil, 0.8)
	local spinM: Model? = nil
	if hid == "none" then
		label(chip, "NONE", 15, UDim2.new(), UDim2.fromScale(1, 1), GREY, Enum.TextXAlignment.Center).FontFace = FONT_BOLD
	else
		local hv, hcam = viewport(chip, { Size = UDim2.fromScale(1, 1), BackgroundTransparency = 1, ZIndex = 6, Ambient = Color3.fromRGB(170, 173, 182) })
		hcam.FieldOfView = 30
		local hm = GunHats.make(hid, CFrame.Angles(0, CARD_TURN[hid] or 0, 0), 3, nil)
		if hm then
			local _, sz = hm:GetBoundingBox()
			local r = math.max(sz.Magnitude / 2, 0.5)
			hm.Parent = hv
			spinM = hm
			hcam.CFrame = CFrame.lookAt(Vector3.new(-r * 1.9, r * 1.55, -r * 2.6), Vector3.new(0, r * 0.62, 0))
		end
	end
	local tick = label(chip, "\u{2713}", 20, UDim2.fromOffset(2, 0), UDim2.fromOffset(22, 22), WHITE, Enum.TextXAlignment.Center)
	tick.ZIndex = 7; tick.Visible = false; tick.TextStrokeColor3 = Color3.new(0, 0, 0); tick.TextStrokeTransparency = 0.3
	local line = new("Frame", { BackgroundColor3 = Roster.RARITY[h.rarity].color, BorderSizePixel = 0, Position = UDim2.fromOffset(4, 93), Size = UDim2.fromOffset(CW - 8, 3), ZIndex = 4 }, holder)
	T.corner(line, 2)
	local nm = label(holder, h.name, 14, UDim2.fromOffset(0, 100), UDim2.fromOffset(CW, 18), GREY, Enum.TextXAlignment.Center)
	nm.TextYAlignment = Enum.TextYAlignment.Top; nm.ZIndex = 5
	nm.TextScaled = true -- (a long name on a narrow card shrinks to fit, at most 14)
	new("UITextSizeConstraint", { MaxTextSize = 14 }, nm)
	chip.MouseEnter:Connect(function() state.hatHover = hid; if state.open then refresh() end end)
	chip.MouseLeave:Connect(function() if state.hatHover == hid then state.hatHover = nil end; if state.open then refresh() end end)
	chip.SelectionGained:Connect(function() state.hatHover = hid; if state.open then refresh() end end) -- (a controller's pick tries it on)
	chip.SelectionLost:Connect(function() if state.hatHover == hid then state.hatHover = nil end; if state.open then refresh() end end)
	chip.MouseButton1Click:Connect(function() onHat(hid) end)
	table.insert(hatCards, { id = hid, chip = chip, st = st, tick = tick, spin = spinM, holder = holder, new = News.dot(chip, 9) })
	hatLocks[hid] = lockOver(chip, 8)
end
-- ---------------------------------------------------------------- the skins (a third tab): another body per weapon
-- the focused weapon's skins that are in the place (GunSkins.forWeapon), one card each plus DEFAULT; hover to try it
-- on in the big preview, click to wear it. a skin you don't own says so (the server checks: Loot.owns)
local sHolder, sbar = panel(stage, UDim2.fromOffset(610, 852), UDim2.fromOffset(1250, 188))
sHolder.Visible = false
local sTitle = label(sbar, "SKINS", 18, UDim2.fromOffset(20, 12), UDim2.fromOffset(110, 26), TEXT)
sTitle.FontFace = FONT_TITLE
local sName = label(sbar, "", 16, UDim2.fromOffset(130, 12), UDim2.fromOffset(520, 26), TEXT)
sName.FontFace = FONT_BOLD; sName.RichText = true; sName.TextWrapped = false
-- (where the shown skin comes from, then how to use the row: News.source. 18 Nov)
News.src = label(sbar, "hover to try it on · click to wear it", 15, UDim2.fromOffset(700, 14), UDim2.fromOffset(530, 20), GREY, Enum.TextXAlignment.Right)
local skinRow = new("ScrollingFrame", {
	BackgroundTransparency = 1, BorderSizePixel = 0, Position = UDim2.fromOffset(12, 48), Size = UDim2.fromOffset(1226, 136),
	CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.X, ScrollingDirection = Enum.ScrollingDirection.X,
	ScrollBarThickness = 5, ScrollBarImageColor3 = DIM, VerticalScrollBarInset = Enum.ScrollBarInset.None, ZIndex = 3,
}, sbar)
new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 8), SortOrder = Enum.SortOrder.LayoutOrder }, skinRow)
new("UIPadding", { PaddingLeft = UDim.new(0, 6), PaddingRight = UDim.new(0, 12) }, skinRow)
arrows(skinRow, sbar)
local noSkins = new("TextLabel", {
	BackgroundColor3 = PANEL, BackgroundTransparency = 0, BorderSizePixel = 0, Position = UDim2.fromOffset(12, 48), Size = UDim2.fromOffset(1226, 132),
	FontFace = FONT, TextSize = 16, TextColor3 = GREY, Text = "", ZIndex = 10, Visible = false, Active = true,
}, sbar)
type SkinCard = { id: string, st: UIStroke, tick: TextLabel, lock: Frame?, holder: Frame, new: Frame, concept: boolean }
local skinCards: { SkinCard } = {}
local skinsFor = ""
local onSkin: (string) -> () = function() end
local function skinCard(sid: string, order: number, wid: string, concept: boolean?)
	-- (the hats row's cards exactly: CW wide, the same spacing; the owner, 17 Nov, on the HATS tab: "This is right and
	-- easily fixable by allowing scroll!!")
	local holder = new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromOffset(CW, 128), LayoutOrder = order, ZIndex = 4 }, skinRow)
	holder:SetAttribute("SkinId", sid)
	local chip = new("TextButton", { Text = "", AutoButtonColor = false, BackgroundColor3 = CARD, BorderSizePixel = 0, Size = UDim2.fromOffset(CW, 88), ZIndex = 5 }, holder)
	T.corner(chip, 4)
	local st = T.edge(chip, nil, 0.8)
	local name, rarity = "Default", "common"
	if sid == "default" then
		label(chip, "DEFAULT", 15, UDim2.new(), UDim2.fromScale(1, 1), GREY, Enum.TextXAlignment.Center).FontFace = FONT_BOLD
	else
		name, rarity = skinInfo(sid)
		local sv, scam = viewport(chip, { Size = UDim2.fromScale(1, 1), BackgroundTransparency = 1, ZIndex = 6, Ambient = Color3.fromRGB(170, 173, 182) })
		local m, rel = previewModel(wid, nil, sid)
		if m then
			m:PivotTo(CFrame.Angles(0.18, math.pi / 2, 0) * rel:Inverse())
			m.Parent = sv
			scam.CFrame = CFrame.lookAt(Vector3.new(0, 0.6, 5.8), Vector3.new(0, 0, 0))
		end
	end
	local tick = label(chip, "\u{2713}", 20, UDim2.fromOffset(2, 0), UDim2.fromOffset(22, 22), WHITE, Enum.TextXAlignment.Center)
	tick.ZIndex = 7; tick.Visible = false; tick.TextStrokeColor3 = Color3.new(0, 0, 0); tick.TextStrokeTransparency = 0.3
	local rr = Roster.RARITY[rarity] or Roster.RARITY.common
	local line = new("Frame", { BackgroundColor3 = rr.color, BorderSizePixel = 0, Position = UDim2.fromOffset(4, 93), Size = UDim2.fromOffset(CW - 8, 3), ZIndex = 4 }, holder)
	T.corner(line, 2)
	local nm = label(holder, name, 14, UDim2.fromOffset(0, 100), UDim2.fromOffset(CW, 18), GREY, Enum.TextXAlignment.Center)
	nm.TextYAlignment = Enum.TextYAlignment.Top; nm.ZIndex = 5
	nm.TextScaled = true -- (as the hats: a long name shrinks to fit, at most 14)
	new("UITextSizeConstraint", { MaxTextSize = 14 }, nm)
	chip.MouseEnter:Connect(function() state.skinHover = sid; if state.open then refresh() end end)
	chip.MouseLeave:Connect(function() if state.skinHover == sid then state.skinHover = nil end; if state.open then refresh() end end)
	chip.SelectionGained:Connect(function() state.skinHover = sid; if state.open then refresh() end end) -- (a controller's pick tries it on)
	chip.SelectionLost:Connect(function() if state.skinHover == sid then state.skinHover = nil end; if state.open then refresh() end end)
	chip.MouseButton1Click:Connect(function() onSkin(sid) end)
	if concept then
		holder:SetAttribute("Concept", true)
		local tag = label(chip, "CONCEPT", 10, UDim2.new(1, -62, 0, 3), UDim2.fromOffset(58, 14), GREY, Enum.TextXAlignment.Right)
		tag.FontFace = FONT_BOLD; tag.ZIndex = 8
	end
	table.insert(skinCards, { id = sid, st = st, tick = tick, lock = if sid ~= "default" and not concept then lockOver(chip, 8) else nil,
		holder = holder, new = News.dot(chip, 9), concept = concept == true })
end
local lastSeen = ""
local function showWorn(e: any)
	if not state.open then return end
	-- (something NEW for this weapon on the shown strip: it's at the start, so the strip starts there)
	local cardsOf: { any } = if tab == "wraps" then swatches elseif tab == "hats" then hatCards else skinCards
	for _, x in cardsOf do
		if x.new.Visible then
			local row = if tab == "wraps" then swatchRow elseif tab == "hats" then hatRow else skinRow
			row.CanvasPosition = Vector2.zero
			return
		end
	end
	if tab == "wraps" then
		local wid = wrapOf(e.id)
		for _, sw in swatches do if sw.wr.id == wid and sw.holder.Visible then into(swatchRow, sw.holder); return end end
		swatchRow.CanvasPosition = Vector2.zero
	elseif tab == "hats" then
		local hid = hatOf(e.id)
		for _, c in hatCards do if c.id == hid then into(hatRow, c.chip.Parent :: GuiObject); return end end
		hatRow.CanvasPosition = Vector2.zero
	else
		local sid = skinOf(e.id)
		for _, c in skinRow:GetChildren() do
			if c:IsA("GuiObject") and c:GetAttribute("SkinId") == sid then into(skinRow, c); return end
		end
		skinRow.CanvasPosition = Vector2.zero
	end
end
skinsRefresh = function(e: any)
	-- the row follows the focused weapon: rebuilt when the focus (or the skins in the place) change
	-- (the guns session's concepts, SkinSets.CONCEPTS, are in the place for the owner to choose from: never shown to
	-- players, who can't have them; the owner (in Studio, or the place's creator) sees them at the end, tagged CONCEPT,
	-- to look at in the big preview. a test sees the players' row with the attribute PlayerView = true)
	local ids, extra = {}, {}
	local ss = Shared:FindFirstChild("SkinSets")
	local okS, SS = false, nil
	if ss and ss:IsA("ModuleScript") then okS, SS = pcall(require, ss) end
	local concepts = if okS and type(SS) == "table" and type((SS :: any).CONCEPTS) == "table" then (SS :: any).CONCEPTS else {}
	local ownerView = (RunService:IsStudio() or (game.CreatorType == Enum.CreatorType.User and me.UserId == game.CreatorId))
		and me:GetAttribute("PlayerView") ~= true
	for _, sid in GunSkins.forWeapon(e.id) do
		if not table.find(concepts, sid) then table.insert(ids, sid)
		elseif ownerView then table.insert(extra, sid) end
	end
	local k = e.id .. ":" .. table.concat(ids, ",") .. "|" .. table.concat(extra, ",")
	local rebuilt = k ~= skinsFor
	if k ~= skinsFor then
		skinsFor = k
		for _, c in skinRow:GetChildren() do if c:IsA("Frame") then c:Destroy() end end
		table.clear(skinCards)
		if e.live and #ids + #extra > 0 then
			-- (each tile on its own: one bad skin row or concept never empties the strip. 18 Nov)
			News.guard("skin tile default", skinCard, "default", 0, e.id)
			for i, sid in ids do News.guard("skin tile " .. tostring(sid), skinCard, sid, i, e.id) end
			for i, sid in extra do News.guard("concept tile " .. tostring(sid), skinCard, sid, 1000 + i, e.id, true) end
		end
	end
	local cur = skinOf(e.id)
	-- (the worn wrap, hat or skin comes into view when the screen opens, the tab changes or another weapon is focused)
	local seenKey = tab .. "|" .. e.id
	if state.open and (seenKey ~= lastSeen or rebuilt) then
		lastSeen = seenKey
		task.delay(0.1, showWorn, e)
	end
	local shownId = if state.skinHover and e.live then state.skinHover else cur
	News.guard("skin name", function()
		if shownId == "default" then
			sName.Text = "Default"
		else
			local nm, rar = skinInfo(shownId)
			local rr = Roster.RARITY[rar] or Roster.RARITY.common
			sName.Text = ('%s  <font color="#%s">%s</font>%s'):format(nm, rr.color:ToHex(), string.upper(rr.name),
				if state.skinHover and state.skinHover ~= cur then '  <font color="#9ca2ac">(trying it on)</font>' else "")
		end
		local src = if shownId ~= "default" and e.live then News.source(shownId) else ""
		News.src.Text = (if src ~= "" then src .. "  ·  " else "") .. "hover to try it on · click to wear it"
	end)
	noSkins.Visible = not e.live or #ids + #extra == 0
	noSkins.Text = if not e.live then "not on roblox yet." else "no skins for this one yet."
	for _, c in skinCards do
		News.guard("skin tile " .. tostring(c.id), function()
			local on = c.id == cur
			c.tick.Visible = on
			if c.lock then
				local set = owned.skin
				-- (a free skin, the Classic set, is everyone's: LootTable's rarity "free")
				c.lock.Visible = ownedKnown and not (set ~= nil and set[c.id] == true) and select(2, skinInfo(c.id)) ~= "free"
				lockLook(c.lock)
			end
			c.st.Color = if on then ACCENT else WHITE
			c.st.Transparency = if on then 0 else 0.8
			c.st.Thickness = if on then 2 else 1
		end)
	end
end
onSkin = function(sid: string)
	local e = Roster.byId[(skinsFor:match("^([%w_]+):")) or state.focus]
	if not e or not e.live then return end
	local set = owned.skin
	if string.find(skinsFor, sid, 1, true) and not (set ~= nil and set[sid] == true) and select(2, skinInfo(sid)) ~= "free" then
		for _, c in skinRow:GetChildren() do
			if c:GetAttribute("SkinId") == sid and c:GetAttribute("Concept") then
				play("empty"); say("a concept, not in the game. hover it to see it on the gun.", RED)
				return
			end
		end
	end
	local ok, why = ask("skin", e.id, sid)
	if ok then
		play("click")
		say(if sid == "default" then "back to the plain one." else ("%s, now as the %s."):format(string.lower(e.name), string.lower((skinInfo(sid)))))
	else
		play("empty"); say(why or "that didn't work.", RED)
	end
	refresh()
end
me:GetAttributeChangedSignal("Skins"):Connect(function() if state.open then refresh() end end)

local function setTab(t: string)
	tab = t
	wbar.Parent.Visible = t == "wraps"
	hHolder.Visible = t == "hats"
	sHolder.Visible = t == "skins"
	state.hover, state.hatHover, state.modeHover, state.skinHover = nil, nil, nil, nil
	for name, b in tabBtns do
		b:set(string.upper(name), true, if name == t then T.CARD_HI else nil)
		b.mark.Visible = name == t
	end
end
for name, b in tabBtns do
	b.face.MouseButton1Click:Connect(function() if tab ~= name then play("click"); setTab(name); if state.open then refresh() end end end)
end
setTab("wraps")
hatsRefresh = function(e: any)
	local cur = hatOf(e.id)
	local shownId = if state.hatHover and e.live then state.hatHover else cur
	local h = GunHats.HATS[shownId]
	News.guard("hat name", function()
		if h then
			local rc = Roster.RARITY[h.rarity].color
			hName.Text = ('%s  <font color="#%s">%s</font>%s'):format(h.name, rc:ToHex(), string.upper(Roster.RARITY[h.rarity].name),
				if state.hatHover and state.hatHover ~= cur then '  <font color="#9ca2ac">(trying it on)</font>' else "")
		end
	end)
	noHats.Visible = not e.live or e.slot == "utility"
	noHats.Text = if e.slot == "utility" then "items don't wear hats." else "not on roblox yet."
	for _, c in hatCards do
		News.guard("hat tile " .. tostring(c.id), function()
			local on = c.id == cur
			c.tick.Visible = on
			local lk = hatLocks[c.id]
			if lk then lk.Visible = not owns("hat", c.id); lockLook(lk) end
			c.st.Color = if on then ACCENT else WHITE
			c.st.Transparency = if on then 0 else 0.8
			c.st.Thickness = if on then 2 else 1
		end)
	end
end
-- ---------------------------------------------------------------- newest first, and the NEW dots (18 Nov)
-- (the owner: "if you unlock a spray it should be placed at the start of the scroll") every strip (wraps, hats, skins,
-- the gadgets' too) runs: what you own newest first (the loot save's order), then the free ones (the plain one first),
-- then the rest as listed. a NEW dot on what's fresh; the shown strip's NEW ones count as seen once you move on (another
-- tab or weapon, or closing). a dot on a tab, and on an armory weapon, with something new
-- where a skin comes from, in plain words for the SKINS row's header (the owner, 18 Nov: it said "from crates" for
-- skins that never come from crates): "from crates", "<set> set", "VIP", "VIP daily reward", "code", "free", "concept"
function News.source(sid: string): string
	local mod = Shared:FindFirstChild("LootTable")
	local ok, L = false, nil
	if mod then ok, L = pcall(require, mod) end
	if not ok or type(L) ~= "table" then return "" end
	if L.concept(sid) then return "concept" end
	local row = L.SKINS[sid]
	if type(row) ~= "table" then return "" end
	if row[2] == "free" then return "free" end
	if L.exclusive("skin", sid) then return "VIP daily reward" end
	if L.vipOnly("skin", sid) then return "VIP" end
	local ss = Shared:FindFirstChild("SkinSets")
	local okS, S = false, nil
	if ss then okS, S = pcall(require, ss) end
	local srow = if okS and type(S) == "table" and type(S.SKINS) == "table" then S.SKINS[sid] else nil
	local set = if type(srow) == "table" and type(S.SETS) == "table" then S.SETS[srow[4]] else nil
	if type(set) == "table" then return if set.code then "code" else set.name .. " set" end
	return "from crates"
end
function News.skinGun(id: string): string?
	local mod = Shared:FindFirstChild("LootTable")
	local ok, L = false, nil
	if mod then ok, L = pcall(require, mod) end
	local row = ok and type(L) == "table" and type(L.SKINS) == "table" and L.SKINS[id] or nil
	return if type(row) == "table" and type(row[3]) == "string" then row[3] else nil
end
function News.key(t: string, id: string, gun: string): string return if t == "skin" then id else id .. "@" .. gun end
function News.got(t: string, id: string, gun: string): number?
	local g = News.gotAt[t]
	return if g then g[News.key(t, id, gun)] else nil
end
function News.isNew(t: string, id: string, gun: string): boolean
	local f = News.fresh[t]
	return f ~= nil and f[News.key(t, id, gun)] ~= nil
end
function News.sort(list: { any })
	table.sort(list, function(a, b)
		if a.plain ~= b.plain then return a.plain end -- (the plain one is always first: the owner, 18 Nov)
		if a.g ~= b.g then return a.g < b.g end
		if a.g == 0 and a.n ~= b.n then return a.n > b.n end
		return a.i < b.i
	end)
	for o, x in list do x.holder.LayoutOrder = o end
end
-- the weapons with something new, and the newest NEW thing of all: its type and weapon
function News.guns(): ({ [string]: boolean }, string?, string?)
	local out, best, bt, bg = {}, -1, nil, nil
	for _, t in { "wrap", "hat", "skin" } do
		for k, n in News.fresh[t] or {} do
			local g = if t == "skin" then News.skinGun(k) else string.match(k, "@([%w_]+)$")
			local re = if g then Roster.byId[g] else nil
			if g and re and re.live and (t ~= "hat" or re.slot ~= "utility") then
				out[g] = true
				if type(n) == "number" and n > best then best, bt, bg = n, t, g end
			end
		end
	end
	return out, bt, bg
end
News.refresh = function(e: any)
	local gun = e.id
	local k = gun .. "|" .. News.rev .. "|" .. skinsFor
	if k ~= News.orderFor then
		News.orderFor = k
		local list = {}
		for i, s in swatches do
			local n = News.got("wrap", s.wr.id, gun)
			-- (the mastery camos sit with the free ones near the front, after them: something to aim for)
			table.insert(list, { holder = s.holder, g = if n then 0 elseif s.wr.rarity == "free" or s.wr.mastery then 1 else 2, n = n or 0, plain = s.wr.id == "default", i = i })
		end
		News.sort(list)
		list = {}
		for i, c in hatCards do
			local n = News.got("hat", c.id, gun)
			local hh = GunHats.HATS[c.id]
			table.insert(list, { holder = c.holder, g = if n then 0 elseif c.id == "none" or (hh ~= nil and hh.rarity == "free") then 1 else 2, n = n or 0, plain = c.id == "none", i = i })
		end
		News.sort(list)
		list = {}
		for i, c in skinCards do
			if c.concept then c.holder.LayoutOrder = 1000 + i; continue end
			local n = News.got("skin", c.id, gun)
			table.insert(list, { holder = c.holder, g = if n then 0 elseif c.id == "default" or select(2, skinInfo(c.id)) == "free" then 1 else 2, n = n or 0, plain = c.id == "default", i = i })
		end
		News.sort(list)
	end
	-- (a new view: what the last one showed has been seen)
	local view = if state.open then tab .. "|" .. gun else ""
	if view ~= News.view then News.view = view; News.flush() end
	local has = { wraps = false, hats = false, skins = false }
	for _, s in swatches do
		local nw = e.live and s.holder.Visible and News.isNew("wrap", s.wr.id, gun)
		s.new.Visible = nw
		if nw then has.wraps = true; if state.open and tab == "wraps" then News.note("wrap", News.key("wrap", s.wr.id, gun)) end end
	end
	for _, c in hatCards do
		local nw = e.live and e.slot ~= "utility" and News.isNew("hat", c.id, gun)
		c.new.Visible = nw
		if nw then has.hats = true; if state.open and tab == "hats" then News.note("hat", News.key("hat", c.id, gun)) end end
	end
	for _, c in skinCards do
		local nw = e.live and not c.concept and News.isNew("skin", c.id, gun)
		c.new.Visible = nw
		if nw then has.skins = true; if state.open and tab == "skins" then News.note("skin", c.id) end end
	end
	for t, d in News.tabDots do d.Visible = has[t] == true end
	local ng = News.guns()
	for _, a in armCards do a.new.Visible = ng[a.id] == true end
end
onHat = function(hid: string)
	local e = Roster.byId[state.focus]
	if not e or not e.live or e.slot == "utility" then return end
	if not owns("hat", hid) and not trying() then
		play("empty")
		local h = GunHats.HATS[hid] :: any
		-- (a VIP hat, GunHatData vip = true, comes with the VIP pack on every gun, never from a container; the VIP daily
		-- reward's own hat, Shared.VipDailyData's EXCLUSIVE, only from Trisangle)
		local daily = false
		local vd = Shared:FindFirstChild("VipDailyData")
		if vd and vd:IsA("ModuleScript") then
			local okD, VD = pcall(require, vd)
			daily = okD and type(VD) == "table" and type((VD :: any).isExclusive) == "function" and (VD :: any).isExclusive("hat", hid) == true
		end
		say(if daily then ("the %s comes only from Trisangle's VIP daily reward, in the VIP room."):format(string.lower(h.name))
			elseif h.vip then ("the %s comes with VIP. see the shop [B]."):format(string.lower(h.name))
			else ("a %s for the %s comes in duffel bags. open one in the shop [B]."):format(string.lower(h.name), string.lower(e.name)), RED)
		return
	end
	local ok, why = ask("hat", e.id, hid)
	if ok then
		play("click")
		say(if hid == "none" then "hat off." else ("%s, now in a %s."):format(string.lower(e.name), string.lower(GunHats.HATS[hid].name)))
	else
		play("empty"); say(why or "that didn't work.", RED)
	end
	refresh()
end
me:GetAttributeChangedSignal("Hats"):Connect(function() if state.open then refresh() end end)
-- (the cards turn slowly while the screen is up)
RunService.RenderStepped:Connect(function()
	if not state.open or tab ~= "hats" then return end
	local a = os.clock() * 0.6
	for _, c in hatCards do
		local m = c.spin
		if m then m:PivotTo(CFrame.Angles(0, a + (CARD_TURN[c.id] or 0), 0)) end
	end
end)

-- ---------------------------------------------------------------- open / close: the camera move, the blur, the slide-in
local blur = new("BlurEffect", { Name = "JankLoadoutBlur", Size = 0, Enabled = false }, Lighting)
local tint = new("ColorCorrectionEffect", { Name = "JankLoadoutTint", Enabled = false }, Lighting)
local controls: any = nil
task.spawn(function()
	pcall(function() controls = require(me:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: any):GetControls() end)
end)

local cam = { from = CFrame.identity, to = CFrame.identity, t0 = 0, dur = 0.55, saved = nil :: CFrame?, savedHead = Vector3.zero, closing = false, active = false }
local function head(): BasePart?
	local ch = me.Character
	local h = ch and ch:FindFirstChild("Head")
	return if h and h:IsA("BasePart") then h else nil
end
-- the showcase spot: out in front of you, a bit up and to the side, looking back past you (your blurry self in the back)
local function showcaseCF(): CFrame?
	local h = head()
	if not h then return nil end
	local look = (workspace.CurrentCamera :: Camera).CFrame.LookVector
	local flat = Vector3.new(look.X, 0, look.Z)
	flat = if flat.Magnitude > 1e-3 then flat.Unit else Vector3.new(0, 0, -1)
	local right = flat:Cross(Vector3.yAxis)
	local dir = flat * 9 + right * 3 + Vector3.new(0, 1.6, 0)
	local dist = dir.Magnitude
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { me.Character :: Instance }
	local hit = workspace:Raycast(h.Position, dir, params)
	if hit then dist = math.max(3, hit.Distance - 1.2) end -- (never through a wall)
	local eye = h.Position + dir.Unit * dist
	return CFrame.lookAt(eye, h.Position + right * 1.2 - Vector3.new(0, 0.4, 0))
end
local function ease(u: number): number u = math.clamp(u, 0, 1); return 1 - (1 - u) ^ 3 end

RunService:BindToRenderStep("JankLoadoutCam", Enum.RenderPriority.Camera.Value + 5, function()
	if not cam.active then return end
	local c = workspace.CurrentCamera :: Camera
	local u = ease((os.clock() - cam.t0) / cam.dur)
	if cam.closing then
		local h = head()
		local back = if cam.saved and h then cam.saved.Rotation + (h.Position + (cam.saved.Position - cam.savedHead)) else cam.to
		c.CFrame = cam.from:Lerp(back, u)
		if u >= 1 then
			cam.active, cam.closing = false, false
			c.CameraType = Enum.CameraType.Custom
		end
	else
		c.CameraType = Enum.CameraType.Scriptable
		local drift = CFrame.Angles(math.sin(os.clock() * 0.4) * 0.006, math.sin(os.clock() * 0.27) * 0.012, 0)
		c.CFrame = cam.from:Lerp(cam.to, u) * drift
	end
end)

local panelsIn: { { o: GuiObject, from: UDim2, to: UDim2 } } = {}
for _, o in stage:GetChildren() do
	if o:IsA("GuiObject") then
		local p = o.Position
		local dx = if p.X.Offset < 600 then -28 elseif p.X.Offset > 1400 then 28 else 0
		local dy = if dx == 0 then (if p.Y.Offset > 800 then 20 else -16) else 0
		table.insert(panelsIn, { o = o, from = p + UDim2.fromOffset(dx, dy), to = p })
	end
end

local function canOpen(): (boolean, string?)
	if not require(script.Parent:WaitForChild("MenuGate")).allowed("loadout") then return false, nil end -- (no hub menus in a match or a map room: MenuGate, play-party-ranked's; the match picker has L in its window)
	-- (in a match's loadout window the key opens the small picker instead: client/MatchLoadout.luau, play-party-ranked's)
	if me:GetAttribute("Zone") == "match" then return false, if me:GetAttribute("LoadoutWindow") ~= nil then nil else "NOT MID-MATCH" end
	local ch = me.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	if not hum or hum.Health <= 0 then return false, nil end
	return true, nil
end

local hidden: { [ScreenGui]: boolean } = {}
local setOpen: (boolean) -> ()
setOpen = function(v: boolean)
	if v == state.open then return end
	if v then
		local ok, why = canOpen()
		if not ok then if why then Hud.callout(why, 1.2) end; return end
		local to = showcaseCF()
		if not to then return end
		state.open = true
		me:SetAttribute("LoadoutOpen", true)
		require(script.Parent:WaitForChild("MenuCursor")).set("loadout", true, function() return state.open end)
		-- (nothing from here to the screen showing may throw: guarded, 18 Nov)
		News.guard("open focus", function() state.focus = pick()[state.slot] end)
		-- (something NEW since last time: open on the newest one's weapon and tab, where it's first in the strip. 18 Nov)
		News.guard("open on the newest", function()
			local _, nt, ng = News.guns()
			if nt and ng and Roster.byId[ng] then
				state.slot = Roster.byId[ng].slot
				state.focus = ng
				setTab(if nt == "wrap" then "wraps" elseif nt == "hat" then "hats" else "skins")
			end
		end)
		state.hover, state.hatHover, state.modeHover = nil, nil, nil
		subtitle.Text = if trying() then "TRY ANYTHING HERE  ·  YOUR LOADOUT COMES BACK WHEN YOU LEAVE" else ""
		subtitle.TextColor3 = if trying() then ACCENT else GREY
		-- the rest of the HUD steps aside while the screen is up (it comes back as it was)
		table.clear(hidden)
		for _, g in pg:GetChildren() do
			if g:IsA("ScreenGui") and g ~= gui and g.Enabled then hidden[g] = true; g.Enabled = false end
		end
		News.guard("fit", fit)
		refresh()
		News.guard("filter", applyFilter)
		task.spawn(function() fetchOwned(); if state.open then refresh() end end)
		gui.Enabled = true
		for i, x in panelsIn do
			x.o.Position = x.from
			task.delay((i - 1) * 0.02, function() if state.open then tw(x.o, 0.22, { Position = x.to }) end end)
		end
		catcher.BackgroundTransparency = 1
		tw(catcher, 0.35, { BackgroundTransparency = 0.28 })
		blur.Enabled = true; tint.Enabled = true
		tw(blur, 0.45, { Size = 22 })
		tw(tint, 0.45, { Brightness = -0.05, Saturation = -0.75, TintColor = Color3.fromRGB(232, 236, 244) })
		local c = workspace.CurrentCamera :: Camera
		local h = head()
		cam.saved, cam.savedHead = c.CFrame, if h then h.Position else c.CFrame.Position
		cam.from, cam.to, cam.t0, cam.dur, cam.closing, cam.active = c.CFrame, to, os.clock(), 0.55, false, true
		if controls then pcall(function() controls:Disable() end) end
		play("click")
	else
		state.open = false
		state.hover, state.hatHover, state.modeHover = nil, nil, nil
		lastSeen = "" -- (the worn things come into view again next time)
		News.flush(); News.view = "" -- (what was shown counts as seen)
		require(script.Parent:WaitForChild("MenuCursor")).set("loadout", false)
		me:SetAttribute("LoadoutOpen", false)
		gui.Enabled = false
		for g in hidden do if g.Parent then g.Enabled = true end end
		table.clear(hidden)
		tw(blur, 0.3, { Size = 0 })
		tw(tint, 0.3, { Brightness = 0, Saturation = 0, TintColor = WHITE })
		task.delay(0.32, function() if not state.open then blur.Enabled = false; tint.Enabled = false end end)
		local c = workspace.CurrentCamera :: Camera
		cam.from, cam.t0, cam.dur, cam.closing = c.CFrame, os.clock(), 0.35, true
		if controls then pcall(function() controls:Enable() end) end
		if shown then shown.model:Destroy(); shown = nil end
		play("click")
		-- in the hub, the new picks go in now
		task.spawn(function()
			local ok, why = ask("arm")
			if ok and why == "armed" then Hud.callout("LOCKED IN", 0.9) end
		end)
	end
end

done.face.MouseButton1Click:Connect(function() setOpen(false) end)
News.close = function() setOpen(false) end -- (the loadout's way out, for code above setOpen: the coins buy, 18 Nov)
-- kill effect and emotes have their own screen (FlairUI.luau, the flair session's; doc FLAIR.md): this button, left of
-- DONE, opens it. the loadout steps aside first (its camera and blur would sit over that screen's preview)
local flairBtn = button(stage, "KILL EFFECT  ·  EMOTES", "white", UDim2.fromOffset(1360, 40), UDim2.fromOffset(320, 50))
flairBtn.face.MouseButton1Click:Connect(function()
	local m = script.Parent:FindFirstChild("FlairUI")
	if not m then return end
	local home = cam.saved -- (your own view from before the loadout: the flair screen comes back to it, not to the loadout's)
	setOpen(false)
	task.delay(0.05, function()
		local ok, F = pcall(require, m)
		if ok and type(F) == "table" then (F :: any).open(nil, home) end
	end)
end)
UIS.InputBegan:Connect(function(io, gp)
	if require(script.Parent:WaitForChild("Binds")).is("loadout", io) and not UIS:GetFocusedTextBox() then -- (L, or the player's own key)
		if gp and not state.open then return end
		setOpen(not state.open)
		return
	end
	if not state.open or gp then return end
	local i = KEYS[io.KeyCode]
	if i then
		state.slot = Roster.SLOTS[i]
		state.focus = pick()[state.slot]
		play("click")
		refresh()
	end
end)

-- a controller's B backs out (PadNav.client asks through the player attribute MenuBack)
me:GetAttributeChangedSignal("MenuBack"):Connect(function()
	local v = me:GetAttribute("MenuBack")
	if state.open and type(v) == "string" and string.sub(v, 1, 7) == "loadout" then setOpen(false) end
end)

-- the screen follows the server: picks / wraps / save status changing, a match grabbing you, a death
-- (what you own: asked when the screen opens and whenever you win something)
me:GetAttributeChangedSignal("LootOwned"):Connect(function() task.spawn(function() fetchOwned(); if state.open then refresh() end end) end)
for _, a in { "LoadoutNext", "Wraps", "LoadoutSave", "Hats", "Skins", "Trying", "Level", "WeaponsKept", "UnlockAll", "RobuxOwned", "Brass" } do
	me:GetAttributeChangedSignal(a):Connect(function() if state.open then refresh() end end)
end
-- (in or out of training with the screen up: the TRY line and marks follow)
me:GetAttributeChangedSignal("Trying"):Connect(function()
	if not state.open then return end
	subtitle.Text = if trying() then "TRY ANYTHING HERE  ·  YOUR LOADOUT COMES BACK WHEN YOU LEAVE" else ""
	subtitle.TextColor3 = if trying() then ACCENT else GREY
end)
me:GetAttributeChangedSignal("Zone"):Connect(function()
	if (me:GetAttribute("Zone") == "match" or me:GetAttribute("Zone") == "staging") and state.open then setOpen(false) end -- (and a pad's map room: MenuGate)
end)
local function watchChar(ch: Model)
	local hum = ch:WaitForChild("Humanoid", 10)
	if hum and hum:IsA("Humanoid") then hum.Died:Connect(function() if state.open then setOpen(false) end end) end
end
me.CharacterAdded:Connect(watchChar)
if me.Character then task.spawn(watchChar, me.Character) end

-- the spin, every frame while it's up
RunService.RenderStepped:Connect(function(dt)
	if not state.open then return end
	fit()
	if shown then
		local now = os.clock()
		if not spin.drag then
			-- a flick coasts; left alone, it eases back to a three-quarter side view and sways a little there, so the
			-- weapon is never left edge-on to you
			if now - spin.dragT > 1.2 then
				local rest = math.pi / 2 + 0.45 + math.sin(now * 0.45) * 0.28
				local turn = ((rest - spin.yaw + math.pi) % (2 * math.pi)) - math.pi
				spin.vel = 0
				spin.yaw += turn * math.min(1, dt * 2.4)
			else
				spin.vel *= math.max(0, 1 - dt * 2.5)
				spin.yaw += spin.vel * dt
			end
			spin.pitch += (0.12 - spin.pitch) * math.min(1, dt * 0.8)
		end
		local bob = math.sin(now * 1.2) * 0.04
		shown.model:PivotTo(CFrame.new(0, -0.3 + bob, 0) * CFrame.Angles(spin.pitch, spin.yaw, 0) * shown.rel:Inverse())
	end
end)

-- ---------------------------------------------------------------- the hub button
local hudGui = new("ScreenGui", { Name = "JankLoadoutButton", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 6, ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, pg)
-- (a plate like the HUD's, just above the health plate, with the key it's on)
local hubBtn = button(T.scaled(hudGui), "LOADOUT", "white", require(script.Parent:WaitForChild("HubStack")).pos("Loadout"), UDim2.fromOffset(136, 36)) -- (the stack's order: HubStack)
hubBtn.base = T.BG; hubBtn.face.BackgroundColor3 = T.BG; hubBtn.face.BackgroundTransparency = T.BG_A
hubBtn.face.TextSize = 13; hubBtn.face.TextXAlignment = Enum.TextXAlignment.Left
new("UIPadding", { PaddingLeft = UDim.new(0, 42) }, hubBtn.face)
T.key(hubBtn.face, "L", UDim2.fromOffset(-34, 7))
hubBtn.face.MouseButton1Click:Connect(function() setOpen(true) end)
RunService.Heartbeat:Connect(function()
	local show = not state.open and me:GetAttribute("Zone") ~= "match"
	if hubBtn.holder.Visible ~= show then hubBtn.holder.Visible = show end
end)

-- ---------------------------------------------------------------- the phone layout (touch controls, 17 Nov)
-- the 1920 x 1080 screen above, scaled down to fit a phone, left every button a third of its size (DONE: 18 points tall
-- on an 844 x 390 phone; the armory's names 6 points). on a touch screen whose short side is under 600 points the same
-- pieces are laid out on a 1300 x 600 canvas instead, in two pages picked at the top left: WEAPONS (the slot cards, the
-- armory, the weapon's card with a bigger EQUIP) and LOOKS (the preview, the slot cards small, the wraps / hats /
-- skins bar full width). tap targets come out 40-65 points. nothing else changes: the same buttons, the same code.
-- (a Studio test fakes the screen: the player attribute FakeScreen, a Vector2, set by TouchControls' "fake:WxH")
-- (all in its own function: this script's main chunk is near Luau's 200-local limit)
do
local function phoneLayout()
	local deskFit = fit
	local PW, PH = 1300, 600
	local page = "gear"
	local on = false
	local saved: { [Instance]: { [string]: any } } = {}
	local function keep(o: Instance, prop: string)
		saved[o] = saved[o] or {}
		if saved[o][prop] == nil then saved[o][prop] = (o :: any)[prop] end
	end
	local function set(o: Instance, prop: string, v: any)
		keep(o, prop)
		if (o :: any)[prop] ~= v then (o :: any)[prop] = v end
	end
	local function scaleOf(o: Instance): UIScale
		local sc = o:FindFirstChild("PhoneScale") :: UIScale?
		if not sc then sc = new("UIScale", { Name = "PhoneScale" }, o) end
		return sc :: UIScale
	end
	local function put(o: GuiObject, x: number, y: number, k: number, vis: boolean)
		set(o, "Position", UDim2.fromOffset(x, y))
		set(o, "Visible", vis)
		local sc = scaleOf(o)
		if sc.Scale ~= k then sc.Scale = k end
	end
	local function screen(): Vector2
		local f = me:GetAttribute("FakeScreen")
		if typeof(f) == "Vector2" then return f end
		return (workspace.CurrentCamera :: Camera).ViewportSize
	end
	local function phone(): boolean
		local v = screen()
		local touch = (UIS.TouchEnabled and not UIS.KeyboardEnabled) or me:GetAttribute("TouchOn") == true
		return touch and math.min(v.X, v.Y) < 600
	end
	-- the page buttons (phone only)
	local pageBtns: { [string]: Btn } = {}
	for i, p in { { "gear", "WEAPONS" }, { "looks", "LOOKS" } } do
		local b = button(stage, p[2], "chip", UDim2.fromOffset(20 + (i - 1) * 212, 12), UDim2.fromOffset(200, 60))
		b.holder.Visible = false
		b.face.TextSize = 24
		b.face.MouseButton1Click:Connect(function() if page ~= p[1] then page = p[1]; play("click") end end)
		pageBtns[p[1]] = b
	end
	-- (a test picks the page: the player attribute LoadoutPhonePage = "gear" or "looks")
	me:GetAttributeChangedSignal("LoadoutPhonePage"):Connect(function()
		local v = me:GetAttribute("LoadoutPhonePage")
		if v == "gear" or v == "looks" then page = v end
	end)
	local armHolder = armBody.Parent :: Frame
	local infoHolder = info.Parent :: Frame
	local bars = { wraps = wbar.Parent :: Frame, hats = hHolder, skins = sHolder }
	local function layout()
		local gear = page == "gear"
		set(stage, "Size", UDim2.fromOffset(PW, PH))
		set(titleBox, "Visible", false)
		set(saveLbl, "Visible", false)
		for name, b in pageBtns do
			b.holder.Visible = true
			b.mark.Visible = name == page
			b.face.BackgroundColor3 = if name == page then T.CARD_HI else b.base
		end
		put(flairBtn.holder, 768, 12, 1, true)
		set(flairBtn.holder, "Size", UDim2.fromOffset(320, 60))
		set(flairBtn.face, "TextSize", 19)
		put(done.holder, 1100, 12, 1, true)
		set(done.holder, "Size", UDim2.fromOffset(180, 60))
		set(done.face, "TextSize", 22)
		set(done.face, "Text", "DONE")
		for i, c in cards do
			if gear then put(c.holder, 20, 88 + (i - 1) * 99, 0.89, true) -- (463 x 91: a column down the left)
			else put(c.holder, 372 + ((i - 1) % 2) * 328, 152 + (i - 1) // 2 * 72, 0.6, true) end -- (two by two, beside the preview)
		end
		put(armHolder, 499, 88, 0.89, gear)
		put(infoHolder, 978, 88, 0.72, gear)
		set(equipBtn.holder, "Position", UDim2.fromOffset(22, 596))
		set(equipBtn.holder, "Size", UDim2.fromOffset(376, 88))
		set(equipBtn.face, "TextSize", 28)
		put(previewBox, 20, 88, 0.42, not gear)
		for i, t in { "wraps", "hats", "skins" } do
			put(tabBtns[t].holder, 372 + (i - 1) * 172, 88, 1, not gear)
			set(tabBtns[t].holder, "Size", UDim2.fromOffset(160, 52))
			set(tabBtns[t].face, "TextSize", 24)
			put(bars[t], 20, 404, 1, not gear and tab == t)
		end
		-- (no slide-in on a phone: the pieces open where they are)
		for _, x in panelsIn do keep(x, "from"); keep(x, "to"); x.from = x.o.Position; x.to = x.o.Position end
		uiScale.Scale = math.min(screen().X / PW, screen().Y / PH)
	end
	local function undo()
		for o, props in saved do
			for prop, v in props do (o :: any)[prop] = v end
		end
		table.clear(saved)
		for _, b in pageBtns do b.holder.Visible = false end
		for _, o in stage:GetDescendants() do if o:IsA("UIScale") and o.Name == "PhoneScale" then o.Scale = 1 end end
		setTab(tab)
	end
	fit = function()
		local want = phone()
		if want then layout(); on = true; return end
		if on then on = false; undo() end
		deskFit()
	end
end
phoneLayout()
end
