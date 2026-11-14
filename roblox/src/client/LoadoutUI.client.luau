-- the loadout screen (L, or the LOADOUT button in the hub). keys 1 2 3 = primary / secondary / melee; the whole web roster
-- is on show (what isn't on roblox yet is a "coming soon" card); a big 3D preview on a showcase table you can drag round;
-- the weapon's stats and gimmick; the wraps along the bottom (hover to try one on, click to wear it). the camera eases
-- off to a showcase spot and the world behind goes soft. the server owns every pick (Loadout.luau): this only asks.
-- it only opens in the hub; closing it there re-arms you with the new picks. comic look: dark purple panels, thick pink
-- borders, hard cyan shadows, a tilted yellow main button, Comic Neue
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
local Hud = require(script.Parent:WaitForChild("Hud"))
local Sfx = require(script.Parent:WaitForChild("Sfx"))
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Loadout") :: RemoteFunction
local Tools = ReplicatedStorage:WaitForChild("JankfireTools")

local me = Players.LocalPlayer
local PINK, CYAN, YELLOW = Color3.fromHex("ff4fd8"), Color3.fromHex("4fd8ff"), Color3.fromHex("ffe14d")
local PANEL, INK, WHITE = Color3.fromRGB(18, 8, 24), Color3.new(0, 0, 0), Color3.new(1, 1, 1)
local RED, GREEN, GREY = Color3.fromHex("ff3030"), Color3.fromHex("39ff14"), Color3.fromRGB(150, 135, 160)
local CARD = Color3.fromRGB(40, 20, 52) -- a card sitting on a panel
local FONT = Font.new("rbxasset://fonts/families/ComicNeueAngular.json", Enum.FontWeight.Bold)
local KEYS = { [Enum.KeyCode.One] = 1, [Enum.KeyCode.Two] = 2, [Enum.KeyCode.Three] = 3 }
local LINES = {
	"three slots. choose violence.",
	"no refunds. some take-backs.",
	"dress your gun for the job you want.",
	"pick your poison. it's all poison.",
	"the armory. touch everything.",
}
local MODE_NAMES = { normal = "HANDLE", reverse = "BUSINESS END", full = "FULL SEND" }
local SOON_GIMMICK = "already in the web game. roblox is still bolting it together."

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
local function stroke(o: Instance, th: number, c: Color3, text: boolean?): UIStroke
	return new("UIStroke", {
		Thickness = th, Color = c, LineJoinMode = Enum.LineJoinMode.Miter,
		ApplyStrokeMode = if text then Enum.ApplyStrokeMode.Contextual else Enum.ApplyStrokeMode.Border,
	}, o)
end
local function label(parent: Instance, text: string, size: number, pos: UDim2, sz: UDim2, color: Color3?, align: Enum.TextXAlignment?): TextLabel
	return new("TextLabel", {
		BackgroundTransparency = 1, FontFace = FONT, TextSize = size, Text = text, Position = pos, Size = sz,
		TextColor3 = color or WHITE, TextXAlignment = align or Enum.TextXAlignment.Left, TextWrapped = true,
	}, parent)
end
-- a panel: dark purple-black, thick pink border, a hard cyan shadow (no blur). returns its body
local function panel(parent: Instance, pos: UDim2, size: UDim2): (Frame, Frame)
	local holder = new("Frame", { BackgroundTransparency = 1, Position = pos, Size = size }, parent)
	new("Frame", { Name = "Shadow", BackgroundColor3 = CYAN, BorderSizePixel = 0, Position = UDim2.fromOffset(8, 8), Size = UDim2.fromScale(1, 1), ZIndex = 1 }, holder)
	local body = new("Frame", { Name = "Body", BackgroundColor3 = PANEL, BackgroundTransparency = 0.08, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 2 }, holder)
	stroke(body, 4, PINK)
	return holder, body
end

-- a chunky button with a hard shadow. main = yellow with a pink shadow; white; chip = small white
type Btn = { holder: Frame, face: TextButton, shadow: Frame, kind: string, enabled: boolean, set: (Btn, string, boolean?, Color3?) -> () }
local function button(parent: Instance, text: string, kind: string, pos: UDim2, size: UDim2, rot: number?): Btn
	local holder = new("Frame", { BackgroundTransparency = 1, Position = pos, Size = size, Rotation = rot or 0 }, parent)
	local off = if kind == "chip" then 4 else 6
	local shadow = new("Frame", { BackgroundColor3 = if kind == "main" then PINK else INK, BorderSizePixel = 0, Position = UDim2.fromOffset(off, off), Size = UDim2.fromScale(1, 1), ZIndex = 1 }, holder)
	local face = new("TextButton", {
		AutoButtonColor = false, BackgroundColor3 = if kind == "main" then YELLOW else WHITE, BorderSizePixel = 0,
		Size = UDim2.fromScale(1, 1), FontFace = FONT, TextSize = math.floor(size.Y.Offset * (if kind == "chip" then 0.5 else 0.42)),
		Text = text, TextColor3 = INK, ZIndex = 2,
	}, holder)
	stroke(face, if kind == "chip" then 2 else 3, INK)
	local b: Btn = { holder = holder, face = face, shadow = shadow, kind = kind, enabled = true, set = nil :: any }
	local function rest(hover: boolean)
		local lift = if hover and b.enabled then -2 else 0
		tw(face, 0.08, { Position = UDim2.fromOffset(lift, lift) })
		tw(shadow, 0.08, { Position = UDim2.fromOffset(off - lift, off - lift) })
	end
	face.MouseEnter:Connect(function() rest(true) end)
	face.MouseLeave:Connect(function() rest(false) end)
	face.MouseButton1Down:Connect(function()
		if not b.enabled then return end
		tw(face, 0.05, { Position = UDim2.fromOffset(off - 1, off - 1) }) -- pushed into its shadow
	end)
	face.MouseButton1Up:Connect(function() rest(true) end)
	b.set = function(self: Btn, t: string, enabled: boolean?, col: Color3?)
		self.face.Text = t
		self.enabled = enabled ~= false
		self.face.BackgroundColor3 = col or (if not self.enabled then Color3.fromRGB(110, 96, 120) elseif self.kind == "main" then YELLOW else WHITE)
		self.face.TextColor3 = if self.enabled then INK else Color3.fromRGB(40, 30, 46)
		self.shadow.BackgroundColor3 = if self.kind == "main" and self.enabled then PINK else INK
	end
	return b
end

-- ---------------------------------------------------------------- state from the server (player attributes)
local function pick(): { [string]: string }
	local s = me:GetAttribute("LoadoutNext")
	local out = { primary = "redline", secondary = "marbles", melee = "katana" }
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

-- ---------------------------------------------------------------- models for the previews
-- every preview is scaled to the same size (radius 3 studs) so the table and the camera never need to change
local function shredderModel(): Model?
	local src = Tools:FindFirstChild("Shredder")
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
-- a weapon that isn't on roblox yet: a taped-up crate in its colour
local function crate(color: Color3): Model
	local m = Instance.new("Model")
	local function bx(size: Vector3, c: Color3, cf: CFrame, mat: Enum.Material?): Part
		return new("Part", { Anchored = true, Size = size, Color = c, CFrame = cf, Material = mat or Enum.Material.SmoothPlastic, TopSurface = Enum.SurfaceType.Smooth, BottomSurface = Enum.SurfaceType.Smooth }, m)
	end
	local box = bx(Vector3.new(3.6, 2.2, 2.2), color, CFrame.identity, Enum.Material.Cardboard)
	for _, y in { -1.08, 1.08 } do for _, z in { -1.08, 1.08 } do bx(Vector3.new(3.7, 0.16, 0.16), INK, CFrame.new(0, y, z)) end end
	bx(Vector3.new(0.7, 2.26, 2.26), PINK, CFrame.new(0.6, 0, 0))
	bx(Vector3.new(0.9, 0.05, 0.9), WHITE, CFrame.new(-0.9, 1.12, 0.3) * CFrame.Angles(0, 0.4, 0))
	m.PrimaryPart = box
	return m
end
local function previewModel(id: string): (Model?, CFrame)
	local e = Roster.byId[id]
	local m: Model?
	if not e or not e.live then m = crate(if e then e.color else GREY)
	elseif id == "shredder" then m = shredderModel()
	else m = WeaponModels.build(id, 3) end
	if not m then return nil, CFrame.identity end
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then d.Anchored = true; d.CastShadow = false end
	end
	local _, size = m:GetBoundingBox()
	local r = size.Magnitude / 2
	if r > 1e-3 then pcall(function() m:ScaleTo(m:GetScale() * (3 / r)) end) end
	local cf = m:GetBoundingBox()
	return m, m:GetPivot():ToObjectSpace(cf)
end
local function viewport(parent: Instance, props: { [string]: any }): (ViewportFrame, Camera)
	local vp = new("ViewportFrame", {
		BackgroundTransparency = 1, Ambient = Color3.fromRGB(150, 130, 170), LightColor = Color3.fromRGB(255, 244, 236),
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
local catcher = new("TextButton", { Text = "", AutoButtonColor = false, BackgroundColor3 = Color3.fromRGB(14, 4, 20), BackgroundTransparency = 0.5, Size = UDim2.fromScale(1, 1), Modal = true }, gui)
local stage = new("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(1920, 1080) }, gui)
local uiScale = new("UIScale", {}, stage)
local function fit()
	local v = (workspace.CurrentCamera :: Camera).ViewportSize
	uiScale.Scale = math.min(v.X / 1920, v.Y / 1080)
end

-- title
local titleBox = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(60, 26), Size = UDim2.fromOffset(560, 120), Rotation = -2 }, stage)
label(titleBox, "LOADOUT", 80, UDim2.fromOffset(6, 6), UDim2.fromOffset(560, 84), PINK)
local title = label(titleBox, "LOADOUT", 80, UDim2.fromOffset(0, 0), UDim2.fromOffset(560, 84), YELLOW)
stroke(title, 3, INK, true)
local subtitle = label(titleBox, LINES[1], 24, UDim2.fromOffset(6, 84), UDim2.fromOffset(560, 30), WHITE)
stroke(subtitle, 1.5, INK, true)

-- done + the save status
local done = button(stage, "DONE  [L]", "white", UDim2.fromOffset(1680, 36), UDim2.fromOffset(180, 58), 1.5)
local saveLbl = label(stage, "", 18, UDim2.fromOffset(1360, 104), UDim2.fromOffset(500, 24), GREY, Enum.TextXAlignment.Right)
stroke(saveLbl, 1.5, INK, true)

-- ---------------------------------------------------------------- slot cards (left)
type Card = { slot: string, holder: Frame, shadow: Frame, body: TextButton, st: UIStroke, name: TextLabel, wrap: TextLabel, bar: Frame, vp: ViewportFrame, cam: Camera, key: string? }
local cards: { Card } = {}
local state = { slot = "primary", focus = "redline", hover = nil :: string?, filter = "all", open = false }
local refresh: () -> () = function() end

for i, slot in Roster.SLOTS do
	local y = 156 + (i - 1) * 146
	local holder = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(60, y), Size = UDim2.fromOffset(520, 130) }, stage)
	local shadow = new("Frame", { BackgroundColor3 = INK, BorderSizePixel = 0, Position = UDim2.fromOffset(8, 8), Size = UDim2.fromScale(1, 1), ZIndex = 1 }, holder)
	local body = new("TextButton", { Text = "", AutoButtonColor = false, BackgroundColor3 = PANEL, BackgroundTransparency = 0.08, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 2 }, holder)
	local st = stroke(body, 3, INK)
	local keyBox = new("Frame", { BackgroundColor3 = YELLOW, BorderSizePixel = 0, Position = UDim2.fromOffset(16, 16), Size = UDim2.fromOffset(52, 52), Rotation = -6 }, body)
	stroke(keyBox, 3, INK)
	label(keyBox, tostring(i), 36, UDim2.fromScale(0, 0), UDim2.fromScale(1, 1), INK, Enum.TextXAlignment.Center)
	label(body, Roster.SLOT_NAMES[slot], 20, UDim2.fromOffset(84, 12), UDim2.fromOffset(220, 22), CYAN)
	local name = label(body, "", 34, UDim2.fromOffset(84, 34), UDim2.fromOffset(240, 44), WHITE)
	name.TextScaled = true
	local wrap = label(body, "", 17, UDim2.fromOffset(84, 82), UDim2.fromOffset(240, 22), GREY)
	local bar = new("Frame", { BorderSizePixel = 0, AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(0, 0, 1, 0), Size = UDim2.new(1, 0, 0, 8), ZIndex = 3 }, body)
	local vp, cam = viewport(body, { Position = UDim2.fromOffset(300, 4), Size = UDim2.fromOffset(212, 118) })
	cam.FieldOfView = 40
	local c: Card = { slot = slot, holder = holder, shadow = shadow, body = body, st = st, name = name, wrap = wrap, bar = bar, vp = vp, cam = cam }
	body.MouseButton1Click:Connect(function()
		state.slot = slot
		state.focus = pick()[slot]
		play("click")
		refresh()
	end)
	body.MouseEnter:Connect(function() if state.slot ~= slot then tw(holder, 0.08, { Position = UDim2.fromOffset(66, y) }) end end)
	body.MouseLeave:Connect(function() tw(holder, 0.08, { Position = UDim2.fromOffset(60, y) }) end)
	table.insert(cards, c)
end

-- ---------------------------------------------------------------- the armory: every weapon for the chosen slot (left, below)
local _, armBody = panel(stage, UDim2.fromOffset(60, 598), UDim2.fromOffset(520, 442))
local armTitle = label(armBody, "THE ARMORY", 28, UDim2.fromOffset(18, 8), UDim2.fromOffset(300, 36), YELLOW)
stroke(armTitle, 2, INK, true)
local armCount = label(armBody, "", 18, UDim2.fromOffset(200, 14), UDim2.fromOffset(300, 26), GREY, Enum.TextXAlignment.Right)
local armList = new("ScrollingFrame", {
	BackgroundTransparency = 1, BorderSizePixel = 0, Position = UDim2.fromOffset(14, 52), Size = UDim2.fromOffset(496, 378),
	CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollingDirection = Enum.ScrollingDirection.Y,
	ScrollBarThickness = 8, ScrollBarImageColor3 = PINK, ZIndex = 3,
}, armBody)
new("UIGridLayout", { CellSize = UDim2.fromOffset(232, 82), CellPadding = UDim2.fromOffset(12, 12), SortOrder = Enum.SortOrder.LayoutOrder }, armList)
new("UIPadding", { PaddingTop = UDim.new(0, 4), PaddingLeft = UDim.new(0, 4), PaddingRight = UDim.new(0, 12), PaddingBottom = UDim.new(0, 8) }, armList)
type ArmCard = { id: string, btn: TextButton, st: UIStroke, tag: TextLabel }
local armCards: { ArmCard } = {}
local armSlot = ""
local function buildArmory()
	if armSlot == state.slot then return end
	armSlot = state.slot
	for _, c in armCards do c.btn:Destroy() end
	table.clear(armCards)
	local live, soon = 0, 0
	for i, e in Roster.list do
		if e.slot ~= state.slot then continue end
		if e.live then live += 1 else soon += 1 end
		local btn = new("TextButton", { Text = "", AutoButtonColor = false, BackgroundColor3 = CARD, BorderSizePixel = 0, LayoutOrder = i, ZIndex = 4 }, armList)
		local st = stroke(btn, 2, INK)
		local chip = new("Frame", { BackgroundColor3 = e.color, BorderSizePixel = 0, Position = UDim2.fromOffset(10, 10), Size = UDim2.fromOffset(16, 62), ZIndex = 5 }, btn)
		stroke(chip, 2, INK)
		local nm = label(btn, e.name, 21, UDim2.fromOffset(36, 6), UDim2.fromOffset(188, 44), WHITE)
		nm.ZIndex = 5; nm.TextScaled = true; nm.TextTransparency = if e.live then 0 else 0.35
		new("UITextSizeConstraint", { MaxTextSize = 22 }, nm)
		local tag = label(btn, "", 15, UDim2.fromOffset(36, 52), UDim2.fromOffset(188, 22), GREY)
		tag.ZIndex = 5
		btn.MouseButton1Click:Connect(function()
			state.focus = e.id
			play("click")
			refresh()
		end)
		btn.MouseEnter:Connect(function() if state.focus ~= e.id then btn.BackgroundColor3 = Color3.fromRGB(58, 30, 74) end end)
		btn.MouseLeave:Connect(function() btn.BackgroundColor3 = CARD end)
		table.insert(armCards, { id = e.id, btn = btn, st = st, tag = tag })
	end
	armCount.Text = ("%d live · %d coming soon"):format(live, soon)
	armList.CanvasPosition = Vector2.zero
end

-- ---------------------------------------------------------------- the preview: a showcase table with the weapon spinning over it (centre)
local previewBox = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(610, 104), Size = UDim2.fromOffset(800, 736) }, stage)
local vp, vcam = viewport(previewBox, { Size = UDim2.fromScale(1, 1), Active = true })
vcam.FieldOfView = 30
vcam.CFrame = CFrame.lookAt(Vector3.new(0, 3.4, 15.5), Vector3.new(0, -1.1, 0))
do -- a round display podium (neon rims, its top at y -2.75) with junk on it from the last guy
	local function p(shape: Enum.PartType, size: Vector3, c: Color3, cf: CFrame, mat: Enum.Material?)
		new("Part", { Anchored = true, Shape = shape, Size = size, Color = c, CFrame = cf, Material = mat or Enum.Material.SmoothPlastic, TopSurface = Enum.SurfaceType.Smooth, BottomSurface = Enum.SurfaceType.Smooth }, vp)
	end
	local B, Ball, Cyl = Enum.PartType.Block, Enum.PartType.Ball, Enum.PartType.Cylinder
	local up = CFrame.Angles(0, 0, math.pi / 2) -- (a cylinder standing up)
	p(Cyl, Vector3.new(0.35, 7.4, 7.4), Color3.fromRGB(30, 20, 40), CFrame.new(0, -4.25, 0) * up)
	p(Cyl, Vector3.new(1.2, 6.4, 6.4), Color3.fromRGB(62, 44, 80), CFrame.new(0, -3.35, 0) * up)
	-- the neon rims sit just under the top / inside the body, so only their outer edge shows
	p(Cyl, Vector3.new(0.14, 6.7, 6.7), CYAN, CFrame.new(0, -2.86, 0) * up, Enum.Material.Neon)
	p(Cyl, Vector3.new(0.12, 6.55, 6.55), PINK, CFrame.new(0, -3.6, 0) * up, Enum.Material.Neon)
	for _, m in { { 2.3, 1.3, "7fd0ff" }, { 2.6, 0.5, "ffe14d" }, { -2.5, 1.0, "ff4fd8" }, { 1.8, 2.0, "39ff14" } } do
		p(Ball, Vector3.new(0.42, 0.42, 0.42), Color3.fromHex(m[3]), CFrame.new(m[1], -2.54, m[2]), Enum.Material.Glass)
	end
	for _, s in { { -2.0, 1.9, 0.6 }, { -1.2, 2.5, 1.9 }, { 2.0, -1.8, 0.3 } } do
		p(Cyl, Vector3.new(0.65, 0.24, 0.24), Color3.fromHex("d8a840"), CFrame.new(s[1], -2.63, s[2]) * CFrame.Angles(0, s[3], 0), Enum.Material.Metal)
	end
	p(B, Vector3.new(2.2, 0.04, 0.5), PINK, CFrame.new(0.7, -2.73, 2.4) * CFrame.Angles(0, -0.3, 0))
	p(B, Vector3.new(1.0, 0.04, 1.0), YELLOW, CFrame.new(-2.1, -2.73, -1.2) * CFrame.Angles(0, 0.4, 0))
end
local nameBox = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 6), Size = UDim2.new(1, 0, 0, 90), Rotation = -2 }, previewBox)
local bigNameShadow = label(nameBox, "", 66, UDim2.fromOffset(5, 5), UDim2.fromScale(1, 1), INK, Enum.TextXAlignment.Center)
local bigName = label(nameBox, "", 66, UDim2.fromOffset(0, 0), UDim2.fromScale(1, 1), WHITE, Enum.TextXAlignment.Center)
for _, l in { bigName, bigNameShadow } do l.TextScaled = true; l.TextWrapped = false; new("UITextSizeConstraint", { MaxTextSize = 66 }, l) end
stroke(bigName, 3, INK, true)
local soonStamp = label(previewBox, "COMING SOON", 64, UDim2.fromScale(0.5, 0.48), UDim2.fromOffset(470, 96), RED, Enum.TextXAlignment.Center)
soonStamp.AnchorPoint = Vector2.new(0.5, 0.5); soonStamp.Rotation = -9; soonStamp.BackgroundColor3 = WHITE; soonStamp.BackgroundTransparency = 0.15
stroke(soonStamp, 5, RED)
local hint = label(previewBox, "drag to spin it  ·  1 2 3 pick a slot", 18, UDim2.new(0, 0, 1, -30), UDim2.new(1, 0, 0, 24), GREY, Enum.TextXAlignment.Center)
stroke(hint, 1.5, INK, true)
local toast = label(previewBox, "", 24, UDim2.new(0.5, 0, 1, -76), UDim2.fromOffset(700, 36), YELLOW, Enum.TextXAlignment.Center)
toast.AnchorPoint = Vector2.new(0.5, 0); toast.TextTransparency = 1
local toastStroke = stroke(toast, 2, INK, true)
toastStroke.Transparency = 1
local toastN = 0
local function say(text: string, color: Color3?)
	toastN += 1
	local n = toastN
	toast.Text = text; toast.TextColor3 = color or YELLOW
	toast.TextTransparency = 0; toastStroke.Transparency = 0
	toast.Rotation = math.random(-2, 2)
	task.delay(2.4, function()
		if toastN ~= n then return end
		tw(toast, 0.3, { TextTransparency = 1 }); tw(toastStroke, 0.3, { Transparency = 1 })
	end)
end

-- spin: slow on its own, drag to turn it (it keeps a little of your flick)
local spin = { yaw = math.pi / 2, pitch = 0.12, vel = 0.45, drag = false, lastX = 0, lastY = 0, dragT = -math.huge }
local shown: { id: string, model: Model, rel: CFrame }? = nil
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
local infoName = label(info, "", 40, UDim2.fromOffset(22, 14), UDim2.fromOffset(380, 48), WHITE)
infoName.TextScaled = true
new("UITextSizeConstraint", { MaxTextSize = 42 }, infoName)
stroke(infoName, 2.5, INK, true)
local chipRow = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(22, 68), Size = UDim2.fromOffset(380, 26) }, info)
new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 10), SortOrder = Enum.SortOrder.LayoutOrder }, chipRow)
local function tagChip(order: number): (Frame, TextLabel)
	local f = new("Frame", { BackgroundColor3 = INK, BorderSizePixel = 0, Size = UDim2.fromOffset(0, 26), AutomaticSize = Enum.AutomaticSize.X, LayoutOrder = order }, chipRow)
	new("UIPadding", { PaddingLeft = UDim.new(0, 8), PaddingRight = UDim.new(0, 8) }, f)
	local l = label(f, "", 16, UDim2.new(), UDim2.fromScale(0, 1), WHITE, Enum.TextXAlignment.Center)
	l.AutomaticSize = Enum.AutomaticSize.X; l.TextWrapped = false
	return f, l
end
local slotChip, slotChipL = tagChip(1)
local liveChip, liveChipL = tagChip(2)
local infoDesc = label(info, "", 19, UDim2.fromOffset(22, 106), UDim2.fromOffset(376, 120), WHITE)
infoDesc.TextYAlignment = Enum.TextYAlignment.Top
local gimBox = new("Frame", { BackgroundColor3 = CARD, BorderSizePixel = 0, Position = UDim2.fromOffset(22, 232), Size = UDim2.fromOffset(376, 104), Rotation = -1 }, info)
stroke(gimBox, 2, YELLOW)
label(gimBox, "THE GIMMICK", 16, UDim2.fromOffset(12, 6), UDim2.fromOffset(200, 20), YELLOW)
local gimText = label(gimBox, "", 18, UDim2.fromOffset(12, 28), UDim2.fromOffset(352, 70), WHITE)
gimText.TextYAlignment = Enum.TextYAlignment.Top
type StatRow = { name: TextLabel, val: TextLabel, fill: Frame }
local statRows: { StatRow } = {}
for i = 1, 4 do
	local y = 352 + (i - 1) * 60
	local name = label(info, "", 17, UDim2.fromOffset(22, y), UDim2.fromOffset(200, 22), CYAN)
	local val = label(info, "", 19, UDim2.fromOffset(170, y), UDim2.fromOffset(228, 22), WHITE, Enum.TextXAlignment.Right)
	new("Frame", { BackgroundColor3 = INK, BorderSizePixel = 0, Position = UDim2.fromOffset(26, y + 30), Size = UDim2.fromOffset(376, 18) }, info)
	local bg = new("Frame", { BackgroundColor3 = CARD, BorderSizePixel = 0, Position = UDim2.fromOffset(22, y + 26), Size = UDim2.fromOffset(376, 18) }, info)
	stroke(bg, 2, INK)
	local fill = new("Frame", { BorderSizePixel = 0, Size = UDim2.fromScale(0, 1) }, bg)
	table.insert(statRows, { name = name, val = val, fill = fill })
end
local equipBtn = button(info, "EQUIP IT", "main", UDim2.fromOffset(22, 604), UDim2.fromOffset(376, 70), -1.5)

-- the stats of a live weapon come from the weapon table itself (Weapons.luau); the rest from the web numbers
local function statsFor(id: string): { Roster.Stat }
	local e = Roster.byId[id]
	local w = Weapons.list[id]
	if not w or w.slot == "none" or not e.live then return e.stats end
	local S = Weapons.S
	local pel = w.pellets or 1
	local out = {}
	table.insert(out, { label = "DAMAGE", text = if pel > 1 then ("%g x%d"):format(w.dmg, pel) else ("%g"):format(w.dmg), bar = math.min(1, w.dmg * pel / 120) })
	if w.kind == "melee" then
		local r = 1 / (w.cd or 1)
		table.insert(out, { label = "SWING RATE", text = ("%.3g/s"):format(r), bar = math.min(1, r / 22) })
		table.insert(out, { label = "REACH", text = ("%.2g m, +%.2g a kill"):format(w.range / S, (w.grow or 0) / S), bar = math.min(1, math.sqrt(w.range / S / 500)) })
		table.insert(out, { label = "MAG", text = "it's a sword", bar = 1 })
	else
		local r = w.rate or 1
		table.insert(out, { label = "FIRE RATE", text = if w.rateMax then ("%g-%g/s"):format(r, w.rateMax) else ("%.2g/s"):format(r), bar = math.min(1, (w.rateMax or r) / 22) })
		table.insert(out, { label = "RANGE", text = ("%g m"):format(w.range / S), bar = math.min(1, math.sqrt(w.range / S / 500)) })
		table.insert(out, { label = "MAG", text = if w.mag then tostring(w.mag) else "lots", bar = math.min(1, (w.mag or 60) / 60) })
	end
	return out
end

-- ---------------------------------------------------------------- the wraps (bottom)
local _, wbar = panel(stage, UDim2.fromOffset(610, 852), UDim2.fromOffset(1250, 188))
local wTitle = label(wbar, "WRAPS", 28, UDim2.fromOffset(18, 6), UDim2.fromOffset(110, 36), YELLOW)
stroke(wTitle, 2, INK, true)
local wName = label(wbar, "", 24, UDim2.fromOffset(130, 8), UDim2.fromOffset(420, 32), WHITE)
wName.RichText = true; wName.TextWrapped = false
local modeBtns: { [string]: Btn } = {}
for i, md in Roster.MODES do
	local b = button(wbar, MODE_NAMES[md], "chip", UDim2.fromOffset(1250 - 18 - (4 - i) * 156, 10), UDim2.fromOffset(146, 32), 0)
	modeBtns[md] = b
end
local filters = { "all", "common", "rare", "epic", "legendary" }
local filterBtns: { [string]: TextButton } = {}
for i, f in filters do
	local t = new("TextButton", {
		Text = string.upper(f), FontFace = FONT, TextSize = 16, AutoButtonColor = false, BackgroundTransparency = 1,
		TextColor3 = if f == "all" then WHITE else Roster.RARITY[f].color, Position = UDim2.fromOffset(20 + (i - 1) * 104, 46), Size = UDim2.fromOffset(96, 22),
	}, wbar)
	filterBtns[f] = t
end
label(wbar, "hover to try it on · click to wear it", 15, UDim2.fromOffset(700, 46), UDim2.fromOffset(530, 22), GREY, Enum.TextXAlignment.Right)
local swatchRow = new("ScrollingFrame", {
	BackgroundTransparency = 1, BorderSizePixel = 0, Position = UDim2.fromOffset(12, 72), Size = UDim2.fromOffset(1226, 114),
	CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.X, ScrollingDirection = Enum.ScrollingDirection.X,
	ScrollBarThickness = 7, ScrollBarImageColor3 = PINK, VerticalScrollBarInset = Enum.ScrollBarInset.None, ZIndex = 3,
}, wbar)
new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 10), SortOrder = Enum.SortOrder.LayoutOrder, VerticalAlignment = Enum.VerticalAlignment.Top }, swatchRow)
new("UIPadding", { PaddingLeft = UDim.new(0, 6), PaddingTop = UDim.new(0, 14), PaddingRight = UDim.new(0, 12) }, swatchRow)
local noPaint = new("TextLabel", {
	BackgroundColor3 = PANEL, BackgroundTransparency = 0.15, Position = UDim2.fromOffset(12, 72), Size = UDim2.fromOffset(1226, 108),
	FontFace = FONT, TextSize = 26, TextColor3 = GREY, Text = "no paint on vapourware. pick something that's live.", ZIndex = 10, Visible = false, Active = true,
}, wbar)

-- a swatch: a paint chip with the wrap's palette laid on it like its pattern, a hard shadow in its rarity's colour
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
local function paintChip(chip: Frame, wr: Roster.Wrap)
	local pal = wr.pal
	if #pal == 0 then
		chip.BackgroundColor3 = Color3.fromRGB(70, 60, 80)
		local l = label(chip, "OG", 26, UDim2.new(), UDim2.fromScale(1, 1), WHITE, Enum.TextXAlignment.Center)
		stroke(l, 2, INK, true)
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
	if wr.neon then return "GLOWS" end
	local m = wr.mat
	if m == "Metal" or m == "Foil" then return "SHINY" end
	if m == "Glass" or m == "Ice" or m == "ForceField" then return "SEE-THRU" end
	if m == "CrackedLava" then return "HOT" end
	if m and m ~= "Plastic" then return string.upper(m) end
	return nil
end
type Swatch = { wr: Roster.Wrap, holder: Frame, chip: TextButton, shadow: Frame, st: UIStroke, tick: TextLabel }
local swatches: { Swatch } = {}
local onSwatch: (Roster.Wrap) -> () = function() end
local onHover: (string?) -> () = function() end
for i, wr in Roster.wraps do
	local holder = new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromOffset(86, 92), LayoutOrder = i, ZIndex = 4 }, swatchRow)
	local shadow = new("Frame", { BackgroundColor3 = Roster.RARITY[wr.rarity].color, BorderSizePixel = 0, Position = UDim2.fromOffset(5, 5), Size = UDim2.fromOffset(78, 54), ZIndex = 4 }, holder)
	local chip = new("TextButton", { Text = "", AutoButtonColor = false, BorderSizePixel = 0, Size = UDim2.fromOffset(78, 54), ZIndex = 5 }, holder)
	local st = stroke(chip, 3, INK)
	paintChip(chip, wr)
	for _, d in chip:GetChildren() do if d:IsA("TextLabel") then d.ZIndex = 6 end end
	local fw = finishWord(wr)
	if fw then
		local l = label(chip, fw, 11, UDim2.new(0, 3, 1, -15), UDim2.new(1, -6, 0, 13), WHITE, Enum.TextXAlignment.Right)
		l.ZIndex = 6; l.TextWrapped = false
		stroke(l, 1.5, INK, true)
	end
	local tick = label(chip, "✓", 26, UDim2.new(0, -8, 1, -20), UDim2.fromOffset(30, 30), YELLOW, Enum.TextXAlignment.Center)
	tick.ZIndex = 7; tick.Visible = false
	stroke(tick, 2.5, INK, true)
	local nm = label(holder, wr.name, 13, UDim2.fromOffset(0, 62), UDim2.fromOffset(86, 32), WHITE, Enum.TextXAlignment.Center)
	nm.TextYAlignment = Enum.TextYAlignment.Top; nm.ZIndex = 5
	chip.MouseEnter:Connect(function() onHover(wr.id) end)
	chip.MouseLeave:Connect(function() onHover(nil) end)
	chip.MouseButton1Click:Connect(function() onSwatch(wr) end)
	table.insert(swatches, { wr = wr, holder = holder, chip = chip, shadow = shadow, st = st, tick = tick })
end
local function applyFilter()
	for _, s in swatches do s.holder.Visible = state.filter == "all" or s.wr.rarity == state.filter or s.wr.id == "default" end
	for f, t in filterBtns do
		t.Text = if f == state.filter then "[" .. string.upper(f) .. "]" else string.upper(f)
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
	local k = id .. "|" .. wid .. "|" .. md
	if cardKey[c.slot] == k then return end
	cardKey[c.slot] = k
	for _, d in c.vp:GetChildren() do if d:IsA("Model") then d:Destroy() end end
	local m, rel = previewModel(id)
	if not m then return end
	WeaponModels.wrap(m, wid, md)
	m:PivotTo(CFrame.Angles(0.18, math.pi / 2, 0) * rel:Inverse())
	m.Parent = c.vp
	c.cam.CFrame = CFrame.lookAt(Vector3.new(0, 1.1, 7.6), Vector3.new(0, 0, 0))
end

local function showPreview(id: string)
	local wid, md = wrapOf(id)
	if state.hover and Roster.byId[id] and Roster.byId[id].live then wid = state.hover end
	if shown and shown.id == id then
		local k = wid .. "/" .. md
		if shownWrap ~= k then shownWrap = k; WeaponModels.wrap(shown.model, wid, md) end
		return
	end
	if shown then shown.model:Destroy(); shown = nil end
	local m, rel = previewModel(id)
	if not m then return end
	WeaponModels.wrap(m, wid, md)
	shownWrap = wid .. "/" .. md
	m.Parent = vp
	shown = { id = id, model = m, rel = rel }
	spin.vel = 3.2 -- a little whoosh on the swap
end

refresh = function()
	local p = pick()
	for _, c in cards do
		local id = p[c.slot]
		local e = Roster.byId[id]
		local on = c.slot == state.slot
		c.name.Text = e.name
		c.bar.BackgroundColor3 = e.color
		local wid, md = wrapOf(id)
		local wr = Roster.wrapById[wid]
		c.wrap.Text = if wid == "default" then "factory paint" else ("wrap: %s · %s"):format(wr and wr.name or wid, string.lower(MODE_NAMES[md] or md))
		c.st.Color = if on then PINK else INK
		c.st.Thickness = if on then 4 else 3
		c.shadow.BackgroundColor3 = if on then CYAN else INK
		cardModel(c, id)
	end
	buildArmory()
	local slotN = slotIndex(state.slot)
	for _, a in armCards do
		local e = Roster.byId[a.id]
		local equipped = p[state.slot] == a.id
		a.st.Color = if state.focus == a.id then PINK elseif equipped then YELLOW else INK
		a.st.Thickness = if state.focus == a.id or equipped then 3 else 2
		a.tag.Text = if equipped then ("ON KEY %d"):format(slotN) elseif e.live then "LIVE · ready" else "COMING SOON"
		a.tag.TextColor3 = if equipped then YELLOW elseif e.live then GREEN else GREY
	end
	-- the focused weapon
	local e = Roster.byId[state.focus] or Roster.byId[p[state.slot]]
	local w = Weapons.list[e.id]
	bigName.Text = string.upper(e.name); bigNameShadow.Text = bigName.Text
	bigName.TextColor3 = e.color
	soonStamp.Visible = not e.live
	infoName.Text = e.name; infoName.TextColor3 = e.color
	slotChipL.Text = Roster.SLOT_NAMES[e.slot]; slotChip.BackgroundColor3 = INK; slotChipL.TextColor3 = CYAN
	liveChipL.Text = if e.live then "LIVE ON ROBLOX" else "COMING SOON"
	liveChip.BackgroundColor3 = if e.live then GREEN else PINK
	liveChipL.TextColor3 = INK
	infoDesc.Text = if e.live and w and w.desc ~= "" then w.desc else string.lower(string.sub(e.desc, 1, 1)) .. string.sub(e.desc, 2)
	gimText.Text = if e.gimmick ~= "" then e.gimmick else SOON_GIMMICK
	local st = statsFor(e.id)
	for i, row in statRows do
		local s = st[i]
		row.name.Text = s and s.label or ""
		row.val.Text = s and s.text or ""
		row.fill.BackgroundColor3 = e.color
		tw(row.fill, 0.25, { Size = UDim2.fromScale(s and math.clamp(s.bar, 0.03, 1) or 0, 1) }, Enum.EasingStyle.Back)
	end
	local slotOf = slotIndex(e.slot)
	if not e.live then equipBtn:set("COMING SOON", false)
	elseif p[e.slot] == e.id then equipBtn:set(("ON KEY %d  ✓"):format(slotOf), false, WHITE)
	else equipBtn:set(("EQUIP IT · KEY %d"):format(slotOf), true) end
	showPreview(e.id)
	-- wraps for the focused weapon
	local wid, md = wrapOf(e.id)
	local shownId = if state.hover and e.live then state.hover else wid
	local wr = Roster.wrapById[shownId]
	if wr then
		local rc = Roster.RARITY[wr.rarity].color
		wName.Text = ('%s  <font color="#%s">%s</font>%s'):format(wr.name, rc:ToHex(), string.upper(Roster.RARITY[wr.rarity].name),
			if state.hover and state.hover ~= wid then '  <font color="#968aa0">(trying it on)</font>' else "")
	end
	noPaint.Visible = not e.live
	for _, s in swatches do
		local on = s.wr.id == wid
		s.tick.Visible = on
		s.st.Color = if on then PINK else INK
		s.st.Thickness = if on then 4 else 3
		s.chip.Position = if on then UDim2.fromOffset(-2, -6) else UDim2.new()
		s.chip.Rotation = if on then -4 else 0
	end
	for m, b in modeBtns do
		b:set(MODE_NAMES[m], e.live, if m == md then YELLOW else WHITE)
	end
	local save = me:GetAttribute("LoadoutSave")
	saveLbl.Text = if save == "cloud" then "saves to your account" elseif save == "off" then "NOT SAVING · studio has API access off" else "fetching your stuff..."
	saveLbl.TextColor3 = if save == "off" then RED else GREY
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
	local ok, why = ask("pick", e.slot, e.id)
	if ok then
		state.slot = e.slot
		play("ting")
		say(("%s on key %d. close this to grab it."):format(string.lower(e.name), slotIndex(e.slot)))
	else
		play("empty")
		say(why or "nope.", RED)
	end
	refresh()
end)

onSwatch = function(wr)
	local e = Roster.byId[state.focus]
	if not e or not e.live then return end
	local _, md = wrapOf(e.id)
	local ok, why = ask("wrap", e.id, wr.id, md)
	if ok then
		play("click")
		say(if wr.id == "default" then "factory paint. classic." else ("%s, wrapped in %s."):format(string.lower(e.name), wr.name))
	else
		play("empty"); say(why or "nope.", RED)
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
		if ok then play("click") else say(why or "nope.", RED) end
		refresh()
	end)
end

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
		local dx = if p.X.Offset < 600 then -90 elseif p.X.Offset > 1400 then 90 else 0
		local dy = if dx == 0 then (if p.Y.Offset > 800 then 70 else -50) else 0
		table.insert(panelsIn, { o = o, from = p + UDim2.fromOffset(dx, dy), to = p })
	end
end

local function canOpen(): (boolean, string?)
	if me:GetAttribute("Zone") == "match" then return false, "NOT MID-MATCH, CHAMP" end
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
		local p = pick()
		state.focus = p[state.slot]
		state.hover = nil
		subtitle.Text = LINES[math.random(#LINES)]
		-- the rest of the HUD steps aside while the screen is up (it comes back as it was)
		table.clear(hidden)
		for _, g in pg:GetChildren() do
			if g:IsA("ScreenGui") and g ~= gui and g.Enabled then hidden[g] = true; g.Enabled = false end
		end
		fit()
		refresh()
		applyFilter()
		gui.Enabled = true
		for i, x in panelsIn do
			x.o.Position = x.from
			task.delay((i - 1) * 0.025, function() if state.open then tw(x.o, 0.38, { Position = x.to }, Enum.EasingStyle.Back) end end)
		end
		catcher.BackgroundTransparency = 1
		tw(catcher, 0.35, { BackgroundTransparency = 0.5 })
		blur.Enabled = true; tint.Enabled = true
		tw(blur, 0.45, { Size = 22 })
		tw(tint, 0.45, { Brightness = -0.05, Saturation = -0.35, TintColor = Color3.fromRGB(236, 222, 255) })
		local c = workspace.CurrentCamera :: Camera
		local h = head()
		cam.saved, cam.savedHead = c.CFrame, if h then h.Position else c.CFrame.Position
		cam.from, cam.to, cam.t0, cam.dur, cam.closing, cam.active = c.CFrame, to, os.clock(), 0.55, false, true
		if controls then pcall(function() controls:Disable() end) end
		play("click")
	else
		state.open = false
		state.hover = nil
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
UIS.InputBegan:Connect(function(io, gp)
	if io.KeyCode == Enum.KeyCode.L and not UIS:GetFocusedTextBox() then
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

-- the screen follows the server: picks / wraps / save status changing, a match grabbing you, a death
for _, a in { "LoadoutNext", "Wraps", "LoadoutSave" } do
	me:GetAttributeChangedSignal(a):Connect(function() if state.open then refresh() end end)
end
me:GetAttributeChangedSignal("Zone"):Connect(function()
	if me:GetAttribute("Zone") == "match" and state.open then setOpen(false) end
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
			-- a flick coasts, then it settles back into the slow turntable spin
			if now - spin.dragT > 1.2 then spin.vel += (0.45 - spin.vel) * math.min(1, dt * 1.5)
			else spin.vel *= math.max(0, 1 - dt * 2.5) end
			spin.yaw += spin.vel * dt
			spin.pitch += (0.12 - spin.pitch) * math.min(1, dt * 0.8)
		end
		local bob = math.sin(now * 1.6) * 0.09
		shown.model:PivotTo(CFrame.new(0, -0.3 + bob, 0) * CFrame.Angles(spin.pitch, spin.yaw, 0) * shown.rel:Inverse())
	end
end)

-- ---------------------------------------------------------------- the hub button
local hudGui = new("ScreenGui", { Name = "JankLoadoutButton", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 6 }, pg)
local hubBtn = button(hudGui, "LOADOUT  [L]", "main", UDim2.new(0, 22, 1, -266), UDim2.fromOffset(196, 52), -2)
hubBtn.face.MouseButton1Click:Connect(function() setOpen(true) end)
RunService.Heartbeat:Connect(function()
	local show = not state.open and me:GetAttribute("Zone") ~= "match"
	if hubBtn.holder.Visible ~= show then hubBtn.holder.Visible = show end
end)
