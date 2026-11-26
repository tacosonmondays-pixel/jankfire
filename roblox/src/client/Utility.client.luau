--!strict
-- your utility (key G) and everyone's items out in the world. the server owns all of it (Utility.luau): this file
-- presses G, shows the item in your own avatar's left hand while it's used, keeps the charges on the HUD (the
-- server's count, player attributes Item / ItemN / ItemAt), and draws what the server says is happening (ItemFx):
-- thrown items on the same flight the server runs (Shared.Items.step, corrected on every bounce), the blasts, the
-- smoke clouds, the shield domes, the medkit's heal. the numbers are the web game's (roblox/docs/WEAPONS.md "Phase 2:
-- ITEMS"); the look is ours: calm, solid, no jank props
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Debris = game:GetService("Debris")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Items = require(Shared:WaitForChild("Items"))
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Holds = require(Shared:WaitForChild("Holds")) :: any
local AvatarArms = require(Shared:WaitForChild("AvatarArms"))
local T = require(script.Parent:WaitForChild("Theme"))
local H = require(script.Parent:WaitForChild("FightHud"))
local Hud = require(script.Parent:WaitForChild("Hud"))
local Sfx = require(script.Parent:WaitForChild("Sfx"))
local VM = require(script.Parent:WaitForChild("Viewmodel")) :: any
local Body = require(script.Parent:WaitForChild("Body")) -- (the popper's kick back is your own movement)
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local ItemR = Remotes:WaitForChild("Item") :: RemoteEvent
local ItemFx = Remotes:WaitForChild("ItemFx") :: RemoteEvent

local S = Items.S
local L = Items.list
local me = Players.LocalPlayer
local camera = workspace.CurrentCamera
local templates = ReplicatedStorage:WaitForChild("JankfireItems", 8)

local folder = Instance.new("Folder")
folder.Name = "JankfireItemFx"
folder.Parent = workspace

local function myChar(): (Model?, Humanoid?, BasePart?)
	local ch = me.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not ch or not hum or not root or hum.Health <= 0 then return nil, nil, nil end
	return ch, hum, root
end
local function inHub(): boolean return me:GetAttribute("Zone") == "hub" and me:GetAttribute("DevArms") ~= true end -- (DevArms: the owner's dev weapons, OwnerDev)
local function menuOpen(): boolean return me:GetAttribute("LoadoutOpen") == true end
local function thirdPerson(): boolean
	local _, _, root = myChar()
	-- (third person is on: the shoulder camera can come in closer than that in a tight corner)
	return me:GetAttribute("ThirdPerson") == true or (root ~= nil and (camera.CFrame.Position - root.Position).Magnitude > 4.5)
end
local function smooth(u: number): number u = math.clamp(u, 0, 1); return u * u * (3 - 2 * u) end

-- ---------------------------------------------------------------- the models (ReplicatedStorage.JankfireItems)
-- each template is a Model at world size (1 m = 3 studs) whose pivot is its middle; attributes GripPos / GripRot say
-- where your fist goes and how it's turned (its Y up through the fist). until a template is there, a plain stand-in
local function part(shape: Enum.PartType, size: Vector3, color: Color3, mat: Enum.Material?): BasePart
	local p = Instance.new("Part")
	p.Shape = shape; p.Size = size; p.Color = color; p.Material = mat or Enum.Material.SmoothPlastic
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	return p
end
local function standIn(name: string): Model
	local m = Instance.new("Model")
	m.Name = name
	local root: BasePart
	if name == "x_frag" then
		root = part(Enum.PartType.Ball, Vector3.one * 0.6, Color3.fromHex("5f6b3c"))
		local cap = part(Enum.PartType.Cylinder, Vector3.new(0.18, 0.26, 0.26), Color3.fromHex("4a4d52"))
		cap.CFrame = CFrame.new(0, 0.34, 0) * CFrame.Angles(0, 0, math.pi / 2); cap.Parent = m
	elseif name == "x_smoke" then
		root = part(Enum.PartType.Cylinder, Vector3.new(0.78, 0.42, 0.42), Color3.fromHex("8c9096"))
		root.CFrame = CFrame.Angles(0, 0, math.pi / 2)
	elseif name == "x_medkit" then
		root = part(Enum.PartType.Block, Vector3.new(0.66, 0.46, 0.26), Color3.fromHex("d8dadd"))
		local band = part(Enum.PartType.Block, Vector3.new(0.67, 0.12, 0.27), Color3.fromHex("c0453f")); band.Parent = m
	elseif name == "x_popper" then
		root = part(Enum.PartType.Cylinder, Vector3.new(0.5, 0.24, 0.24), Color3.fromHex("b8708a"))
		root.CFrame = CFrame.Angles(0, 0, math.pi / 2)
	elseif name == "x_duck" then
		root = part(Enum.PartType.Ball, Vector3.new(1.4, 1.2, 1.7), Color3.fromHex("d8b440"))
		local head = part(Enum.PartType.Ball, Vector3.one * 0.9, Color3.fromHex("d8b440"))
		head.CFrame = CFrame.new(0, 0.7, -0.45); head.Parent = m
	elseif name == "x_calc" then
		root = part(Enum.PartType.Block, Vector3.new(0.45, 0.9, 0.12), Color3.fromHex("3b3f48"))
		local scr = part(Enum.PartType.Block, Vector3.new(0.36, 0.2, 0.02), Color3.fromHex("9fb59a")); scr.Name = "screen"
		scr.CFrame = CFrame.new(0, 0.28, -0.065); scr.Parent = m
	elseif name == "x_laptop" then
		root = part(Enum.PartType.Block, Vector3.new(0.9, 0.06, 0.6), Color3.fromHex("565b65"))
		local lid = part(Enum.PartType.Block, Vector3.new(0.9, 0.6, 0.05), Color3.fromHex("3b3f48")); lid.Name = "lid"
		lid.CFrame = CFrame.new(0, 0.3, 0.3) * CFrame.Angles(-0.25, 0, 0); lid.Parent = m
	elseif name == "x_radar" then
		root = part(Enum.PartType.Block, Vector3.new(0.3, 0.36, 0.7), Color3.fromHex("3b3f48"))
		local scr = part(Enum.PartType.Block, Vector3.new(0.24, 0.14, 0.02), Color3.fromHex("2e4250")); scr.Name = "screen"
		scr.CFrame = CFrame.new(0, 0.05, 0.36); scr.Parent = m
	elseif name == "x_cage" then
		root = part(Enum.PartType.Block, Vector3.new(5, 0.3, 5), Color3.fromHex("3b3f48"))
		root.CFrame = CFrame.new(0, 7.2, 0)
		for _, x in { -2.3, 2.3 } do for _, z in { -2.3, 2.3 } do
			local post = part(Enum.PartType.Block, Vector3.new(0.3, 7.2, 0.3), Color3.fromHex("8e939a")); post.CFrame = CFrame.new(x, 3.6, z); post.Parent = m
		end end
	elseif name == "x_camera" then
		root = part(Enum.PartType.Block, Vector3.new(0.47, 0.26, 0.28), Color3.fromHex("e2e2dc"))
		local flash = part(Enum.PartType.Block, Vector3.new(0.13, 0.06, 0.02), Color3.fromHex("cfcac0")); flash.Name = "flash"
		flash.CFrame = CFrame.new(-0.14, 0.11, -0.14); flash.Parent = m
	elseif name == "x_photoframe" then
		-- (origin: the floor under the middle; the picture faces -z)
		root = part(Enum.PartType.Block, Vector3.new(6.3, 7.1, 0.18), Color3.fromHex("ecebe4"))
		root.CFrame = CFrame.new(0, 3.55, 0.05)
		local pic = part(Enum.PartType.Block, Vector3.new(5.6, 5.6, 0.05), Color3.fromHex("2c2824")); pic.Name = "pic"
		pic.CFrame = CFrame.new(0, 1.08 + 2.85, -0.07); pic.Parent = m
	elseif name == "x_wand" then
		root = part(Enum.PartType.Cylinder, Vector3.new(0.04, 0.3, 0.3), Color3.fromHex("b56f88"))
		root.CFrame = CFrame.Angles(0, math.pi / 2, 0)
		local stick = part(Enum.PartType.Block, Vector3.new(0.06, 0.6, 0.06), Color3.fromHex("3b3f48")); stick.CFrame = CFrame.new(0, -0.45, 0); stick.Parent = m
	elseif name == "x_nvg" then
		root = part(Enum.PartType.Block, Vector3.new(0.6, 0.22, 0.2), Color3.fromHex("3b3f48"))
		for _, x in { -0.14, 0.14 } do
			local l = part(Enum.PartType.Cylinder, Vector3.new(0.2, 0.16, 0.16), Color3.fromHex("4fbf7a"), Enum.Material.Neon); l.Name = "lens"
			l.CFrame = CFrame.new(x, 0, -0.18) * CFrame.Angles(0, math.pi / 2, 0); l.Parent = m
		end
	elseif name == "x_reverse" then
		root = part(Enum.PartType.Block, Vector3.new(0.21, 0.32, 0.02), Color3.fromHex("a23a34"))
	else
		root = part(Enum.PartType.Cylinder, Vector3.new(0.2, 0.6, 0.6), Color3.fromHex("4a4f57"))
		root.CFrame = CFrame.Angles(0, 0, math.pi / 2)
		local lens = part(Enum.PartType.Cylinder, Vector3.new(0.06, 0.4, 0.4), Color3.fromHex("6fd6ef"), Enum.Material.Neon)
		lens.CFrame = CFrame.new(0, 0.12, 0) * CFrame.Angles(0, 0, math.pi / 2); lens.Parent = m
	end
	root.Name = "Body"
	root.Parent = m
	m.PrimaryPart = root
	m.WorldPivot = CFrame.identity
	return m
end
local MODEL = { frag = "x_frag", smokegren = "x_smoke", smoke = "x_smoke", medkit = "x_medkit", bubble = "x_bubble", popper = "x_popper", reverse = "x_reverse", duck = "x_duck",
	quiz = "x_calc", calc = "x_calc", laptop = "x_laptop", nvg = "x_nvg", radar = "x_radar", radarDown = "x_radar", cage = "x_cage",
	camera = "x_camera", snap = "x_camera", print = "x_camera", photoframe = "x_photoframe", wand = "x_wand",
	goggles = "x_nvg", gogglesOff = "x_nvg" }
-- owner: whose gadget it is (the owner's skin and wrap for it, the same "Skins" / "Wraps" attributes as their guns,
-- keyed by the gadget's own id: owner, 18 Nov 2026, "Gadgets should have skins and be wrappable"). nil = the plain one
local function itemModel(id: string, owner: Player?): Model
	local name = MODEL[id] or ("x_" .. id)
	local t = templates and templates:FindFirstChild(name)
	local gid = if L[id] then id else ({ smokegren = "smoke", calc = "quiz", snap = "camera", print = "camera", goggles = "nvg",
		gogglesOff = "nvg", radarDown = "radar" } :: { [string]: string })[id]
	local GS = require(Shared:WaitForChild("GunSkins")) :: any
	local sk = if owner and gid then GS.template(gid, GS.skinFor and GS.skinFor(owner, gid) or nil) else nil
	if sk and sk:GetAttribute("Item") then t = sk end
	local m = if t and t:IsA("Model") then t:Clone() else standIn(name)
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.CastShadow = false end
	end
	if owner and gid then
		local WM = require(Shared:WaitForChild("WeaponModels")) :: any
		local wid, md = WM.wrapFor(owner, gid)
		if wid then pcall(WM.wrap, m, wid, md) end
	end
	return m
end
local function gripOf(m: Model): CFrame
	local gp = m:GetAttribute("GripPos")
	local gr = m:GetAttribute("GripRot")
	local p = if typeof(gp) == "Vector3" then gp else Vector3.zero
	local r = if typeof(gr) == "Vector3" then gr else Vector3.zero
	return CFrame.new(p * m:GetScale()) * CFrame.fromEulerAnglesXYZ(r.X, r.Y, r.Z)
end

-- ---------------------------------------------------------------- the HUD: your item, above the ammo plate
local fight = me:WaitForChild("PlayerGui"):WaitForChild("JankfireFight")
local hud = fight:WaitForChild("Scaled")
local plate = T.plate(hud, "Utility", UDim2.new(1, -256, 1, -138), UDim2.fromOffset(232, 42))
T.key(plate, "G", UDim2.fromOffset(12, 10))
local chip = T.new("Frame", { Name = "Chip", BorderSizePixel = 0, BackgroundColor3 = T.MUTED, Position = UDim2.fromOffset(44, 11), Size = UDim2.fromOffset(3, 20) }, plate)
T.corner(chip, 2)
local nameL = T.text(plate, "Name", "", 15, T.TEXT, T.FONT_BOLD)
nameL.Position = UDim2.fromOffset(54, 11); nameL.Size = UDim2.fromOffset(110, 20); nameL.TextTruncate = Enum.TextTruncate.AtEnd
local pipsBox = T.new("Frame", { Name = "Charges", BackgroundTransparency = 1, AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -14, 0.5, 0), Size = UDim2.fromOffset(60, 14) }, plate)
T.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, HorizontalAlignment = Enum.HorizontalAlignment.Right, VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, 5), SortOrder = Enum.SortOrder.LayoutOrder }, pipsBox)
type Pip = { box: Frame, fill: Frame }
local pips: { Pip } = {}
local function setPips(n: number)
	while #pips < n do
		local b = T.new("Frame", { Name = "Pip", LayoutOrder = #pips + 1, BorderSizePixel = 0, BackgroundColor3 = T.TRACK, Size = UDim2.fromOffset(12, 12), ClipsDescendants = true }, pipsBox)
		T.corner(b, 3)
		local f = T.new("Frame", { Name = "Fill", BorderSizePixel = 0, BackgroundColor3 = T.TEXT, AnchorPoint = Vector2.new(0, 1), Position = UDim2.fromScale(0, 1), Size = UDim2.fromScale(1, 1) }, b)
		T.corner(f, 3)
		table.insert(pips, { box = b, fill = f })
	end
	while #pips > n do (table.remove(pips) :: Pip).box:Destroy() end
end
local pend: { n: number, t: number }? = nil -- a use the server hasn't answered yet (shown at once, like the web HUD)
-- (training, the server's zone: it sets ItemFree. items cost nothing and never recharge, so the plate stays full)
local function charges(): (number, number)
	local n = tonumber(me:GetAttribute("ItemN")) or 0
	if pend and os.clock() - pend.t < 1 and me:GetAttribute("ItemFree") ~= true then n = math.min(n, pend.n) end
	local at = tonumber(me:GetAttribute("ItemAt")) or 0
	return n, at
end
me:GetAttributeChangedSignal("ItemN"):Connect(function() pend = nil end)
me:GetAttributeChangedSignal("ItemFree"):Connect(function() pend = nil end)
local function hudStep()
	local id = me:GetAttribute("Item")
	local it = if type(id) == "string" then L[id] else nil
	local _, _, root = myChar()
	plate.Visible = it ~= nil and it.live and not inHub() and not menuOpen() and root ~= nil
	if not it or not plate.Visible then return end
	local label = if it.id == "nvg" then (if me:GetAttribute("NV") then "Goggles · on  [N] flash" else "Night Vision Goggles")
		elseif it.id == "camera" and me:GetAttribute("Photo") then (if charges() > 0 then "Camera · print" else ("Camera · %ds"):format(math.max(1, math.ceil((tonumber(me:GetAttribute("ItemAt")) or 0) - workspace:GetServerTimeNow())))) else it.name
	if nameL.Text ~= label then nameL.Text = label end
	chip.BackgroundColor3 = it.color
	setPips(it.charges)
	local n, at = charges()
	local left = if at > 0 then at - workspace:GetServerTimeNow() else 0
	local k = if at > 0 then math.clamp(1 - left / it.recharge, 0, 1) else 0
	for i, p in pips do
		if i <= n then p.fill.Size = UDim2.fromScale(1, 1); p.fill.BackgroundColor3 = T.TEXT
		elseif i == n + 1 and at > 0 then p.fill.Size = UDim2.fromScale(1, k); p.fill.BackgroundColor3 = T.MUTED
		else p.fill.Size = UDim2.fromScale(1, 0) end
	end
	nameL.TextColor3 = if n > 0 then T.TEXT else T.MUTED
end

-- ---------------------------------------------------------------- the item in your hand (first person)
-- the off hand fetches it: with a two-handed gun out, your gun's own left hand leaves the gun for it (Viewmodel's
-- offHook); with a sidearm or the katana's free hand gone, a left arm of your own avatar comes up just for it. one
-- path in camera space (studs; x right, y up, -z ahead) per kind: when the hand is where, how it's turned
type Key = { t: number, p: Vector3, r: Vector3 }
local function K(t: number, x: number, y: number, z: number, rx: number, ry: number, rz: number): Key
	return { t = t, p = Vector3.new(x, y, z), r = Vector3.new(rx, ry, rz) }
end
-- release / use = when it leaves the hand (the server throws on the press, so the hand is already on its way)
-- (the one-handed holds sit where Rivals' do at our 80 degree FOV: about 15% left of the crosshair, 25% under it;
-- the up-in-front ones, the laptop, the print and the wand, stay in front)
local PI2 = math.pi * 2
-- every clip comes up on a quick arc that overshoots its hold and settles, does its one motion with some snap, and drops
-- away; the path runs smoothly through its keys (see sampleClip). cam = a small nod of your view along the way (pitch,
-- yaw in radians), so a throw leans into it
local CLIPS = {
	-- (the web game's throw: the item leaves your hand 0.1 s after the press, the same frame as before. a wind-up up and
	-- back by your shoulder, the snap forward, a follow-through that finishes forward and down)
	throw = { dur = 0.52, out = 0.34, release = 0.1, inT = 0.03, keys = {
		K(0, -0.85, -1.35, -0.9, 0.6, 0.3, 0.4), K(0.035, -0.72, -0.62, -1.05, 0.25, 0.3, 0.35),
		K(0.07, -1.05, -0.18, -0.9, 0.95, 0.4, 0.6), K(0.1, -0.45, -0.36, -1.75, -0.5, 0.15, 0.1),
		K(0.17, -0.22, -0.78, -2.0, -1.05, 0.05, -0.1), K(0.3, -0.28, -1.5, -1.5, -0.9, 0.0, -0.2), K(0.52, -0.8, -1.6, -1.0, 0.4, 0.2, 0.3) },
		cam = { { 0, 0, 0 }, { 0.07, 0.022, 0.018 }, { 0.12, -0.03, -0.015 }, { 0.3, 0, 0 } } },
	-- the medkit: up on an arc, the latch twisted open, pulled in to your chest while it heals, a squeeze, gone at 0.62
	medkit = { dur = 0.82, out = 0.62, release = 0.62, keys = {
		K(0, -0.85, -1.4, -0.95, 0.6, 0.2, 0.3), K(0.08, -0.62, -0.7, -1.1, 0.15, 0.6, 0.1), K(0.14, -0.5, -0.5, -1.2, -0.02, 0.45, 0.05),
		K(0.2, -0.52, -0.6, -1.15, 0.2, 0.5, 0.12), K(0.3, -0.48, -0.56, -1.12, 0.45, 0.2, -0.28), K(0.42, -0.38, -0.74, -0.88, 0.62, 0.15, -0.2),
		K(0.5, -0.4, -0.68, -0.92, 0.55, 0.15, -0.14), K(0.62, -0.45, -0.86, -0.95, 0.6, 0.2, -0.1), K(0.82, -0.8, -1.55, -0.9, 0.7, 0.2, 0.3) },
		cam = { { 0, 0, 0 }, { 0.42, -0.018, 0 }, { 0.62, 0, 0 } } },
	-- (web pop_popper: snaps up by 0.07 s, pops at 0.08, the yank at 0.10, eased back by 0.34, gone by 0.5)
	popper = { dur = 0.5, out = 0.3, release = 9, inT = 0.04, keys = {
		K(0, -0.85, -1.35, -1.0, 0.4, 0.1, 0.2), K(0.05, -0.6, -0.55, -1.25, -0.7, 0.15, 0.1), K(0.08, -0.56, -0.48, -1.35, -1.15, 0.15, 0.1),
		K(0.1, -0.52, -0.38, -1.02, -1.65, 0.25, 0.2), K(0.18, -0.55, -0.5, -1.15, -1.25, 0.2, 0.12), K(0.34, -0.58, -0.62, -1.22, -1.0, 0.15, 0.1),
		K(0.5, -0.8, -1.5, -1.0, 0.3, 0.1, 0.25) },
		cam = { { 0, 0, 0 }, { 0.08, 0, 0 }, { 0.1, 0.03, 0.01 }, { 0.26, 0, 0 } } },
	-- the reverse card: flicked up spinning, past its hold and back, then thrust out at them ("no u"), back, dropped at 0.8
	reverse = { dur = 0.8, out = 0.6, release = 9, inT = 0.04, keys = {
		K(0, -0.7, -1.35, -1.0, 0.3, 0, 0.2), K(0.1, -0.55, -0.5, -1.15, -0.2, PI2 * 0.8, 0.15), K(0.16, -0.48, -0.34, -1.35, 0.05, PI2 + 0.3, 0),
		K(0.24, -0.5, -0.42, -1.2, 0, PI2, 0.05), K(0.31, -0.4, -0.36, -1.55, -0.12, PI2, -0.06), K(0.42, -0.5, -0.43, -1.25, 0, PI2 + 0.15, 0.05),
		K(0.62, -0.52, -0.5, -1.22, 0.1, PI2 + 0.2, 0.08), K(0.8, -0.7, -1.5, -1.0, 0.4, PI2, 0.25) },
		cam = { { 0, 0, 0 }, { 0.31, -0.012, 0 }, { 0.45, 0, 0 } } },
	laptop = { dur = 1.05, out = 0.85, release = 9, inT = 0.06, keys = { -- (held by its left edge, facing you: it opens, lights, goes out to them)
		K(0, -0.85, -1.4, -1.0, 0.5, 0.2, 0.15), K(0.07, -0.82, -0.78, -1.1, 0.5, 0.32, 0.12), K(0.12, -0.75, -0.6, -1.2, 0.26, 0.25, 0.05),
		K(0.4, -0.75, -0.6, -1.22, 0.22, 0.24, 0.04), K(0.5, -0.69, -0.55, -1.55, -0.1, 0.2, 0.0),
		K(0.85, -0.71, -0.58, -1.45, -0.05, 0.22, 0.02), K(1.05, -0.9, -1.5, -1.0, 0.5, 0.2, 0.2) } },
	radar = { dur = 1e6, out = 1e6 - 1, release = 1e9, inT = 0.05, keys = {
		K(0, -0.8, -1.4, -1.0, 0.4, 0.2, 0.1), K(0.1, -0.62, -0.5, -1.25, -0.12, 0.36, 0), K(0.17, -0.6, -0.5, -1.3, 0.04, 0.3, 0.04),
		K(1e6, -0.6, -0.5, -1.3, 0.04, 0.3, 0.04) } },
	radarDown = { dur = 0.16, out = 0.0, release = 9, inT = 0.001, keys = {
		K(0, -0.6, -0.5, -1.3, 0.04, 0.3, 0.04), K(0.16, -0.75, -1.4, -1.0, 0.4, 0.2, 0.1) } },
	-- the camera: up to your eye on an arc, CLACK at 0.3 (the shutter kicks it), back down
	snap = { dur = 0.85, out = 0.55, release = 9, inT = 0.05, keys = {
		K(0, -0.6, -1.3, -1.0, 0.4, 0.1, 0.2), K(0.1, -0.32, -0.55, -0.85, 0.15, -0.1, 0), K(0.17, -0.2, -0.29, -0.72, -0.04, -0.06, -0.04),
		K(0.3, -0.21, -0.32, -0.75, 0, -0.06, -0.02), K(0.36, -0.21, -0.28, -0.68, 0.16, -0.06, 0.04),
		K(0.52, -0.21, -0.32, -0.75, 0.02, -0.06, -0.02), K(0.85, -0.6, -1.4, -1.0, 0.4, 0.1, 0.2) },
		cam = { { 0, 0, 0 }, { 0.3, 0, 0 }, { 0.34, 0.012, 0 }, { 0.5, 0, 0 } } },
	print = { dur = 1.3, out = 1.05, release = 1.14, inT = 0.05, keys = {
		K(0, -0.3, -1.35, -1.0, 0.3, math.pi, 0.4), K(0.12, -0.1, -0.45, -1.2, 0.6, math.pi, 0.15), K(0.2, -0.04, -0.3, -1.25, 0.48, math.pi, 0.05),
		K(0.82, -0.02, -0.3, -1.25, 0.45, math.pi, -0.04), K(1.0, 0.0, -0.26, -1.18, 0.3, math.pi, 0), K(1.14, 0.05, -0.05, -2.0, -0.4, math.pi, 0.2),
		K(1.3, 0.1, 0.1, -2.6, -0.6, math.pi, 0.3) },
		cam = { { 0, 0, 0 }, { 1.0, 0, 0 }, { 1.12, -0.02, 0 }, { 1.3, 0, 0 } } },
	-- the wand: up to your mouth on an arc, a little wiggle while the four bubbles go, down
	wand = { dur = 0.85, out = 0.62, release = 9, inT = 0.05, keys = {
		K(0, -0.45, -1.6, -0.9, 0.15, 0.35, -0.25), K(0.08, -0.25, -0.95, -0.72, 0.1, 0.4, -0.1), K(0.13, -0.17, -0.8, -0.64, -0.04, 0.35, -0.3),
		K(0.22, -0.17, -0.83, -0.66, 0, 0.35, -0.17), K(0.32, -0.16, -0.82, -0.66, 0, 0.35, -0.33), K(0.42, -0.17, -0.83, -0.66, 0, 0.35, -0.18),
		K(0.62, -0.17, -0.83, -0.66, 0, 0.35, -0.25), K(0.85, -0.45, -1.6, -0.9, 0.15, 0.35, -0.25) } },
	-- the shield puck: up on an arc, lifted, then slammed down to set it off (it goes at 0.5)
	bubble = { dur = 0.66, out = 0.46, release = 0.5, inT = 0.04, keys = {
		K(0, -0.8, -1.35, -1.0, 0.5, 0.1, 0.2), K(0.08, -0.6, -0.55, -1.3, -0.05, 0.2, 0.05), K(0.13, -0.52, -0.44, -1.35, -0.2, 0.25, 0),
		K(0.2, -0.5, -0.52, -1.3, -0.1, 0.25, 0.05), K(0.3, -0.5, -0.38, -1.28, 0.32, 0.25, 0.05), K(0.38, -0.5, -0.64, -1.25, -0.28, 0.25, 0.05),
		K(0.5, -0.52, -0.66, -1.25, -0.2, 0.25, 0.05), K(0.66, -0.8, -1.5, -1.0, 0.5, 0.1, 0.3) },
		cam = { { 0, 0, 0 }, { 0.3, 0, 0 }, { 0.38, -0.02, 0 }, { 0.55, 0, 0 } } },
	-- the night vision goggles: your hand brings them up over your head and pulls them down over your eyes (the green
	-- comes on as they reach them), or pushes them back up off your eyes
	goggles = { dur = 0.5, out = 0.24, release = 0.2, inT = 0.04, keys = {
		K(0, -0.5, -1.25, -0.8, 0.4, 0, 0.2), K(0.08, -0.2, 0.2, -0.75, -0.5, 0, 0.05), K(0.12, -0.08, 0.32, -0.65, -0.7, 0, 0),
		K(0.2, 0, 0.0, -0.42, 0, 0, 0), K(0.32, -0.35, -0.75, -0.7, 0.3, 0, 0.1), K(0.5, -0.55, -1.4, -0.8, 0.5, 0, 0.2) },
		cam = { { 0, 0, 0 }, { 0.18, -0.015, 0 }, { 0.32, 0, 0 } } },
	gogglesOff = { dur = 0.46, out = 0.2, release = 9, inT = 0.001, keys = {
		K(0, 0, 0.0, -0.42, 0, 0, 0), K(0.1, -0.06, 0.34, -0.66, -0.7, 0, 0), K(0.18, -0.25, 0.1, -0.8, -0.3, 0, 0.1),
		K(0.46, -0.55, -1.4, -0.8, 0.5, 0, 0.2) },
		cam = { { 0, 0, 0 }, { 0.1, 0.012, 0 }, { 0.25, 0, 0 } } },
	-- cooking a grenade (Items.COOK): up in front, a twist that pulls the pin (0.13), then up and back by your shoulder
	-- where it's held for as long as G is (the clip's last key holds); cookThrow lets it go from there (0.03 s)
	cook = { dur = 60, out = 59.9, release = 1e9, inT = 0.04, keys = {
		K(0, -0.85, -1.35, -0.9, 0.6, 0.3, 0.4), K(0.08, -0.62, -0.66, -1.15, 0.2, 0.3, 0.3), K(0.13, -0.6, -0.6, -1.12, 0.25, 0.3, -0.25),
		K(0.2, -0.64, -0.64, -1.14, 0.2, 0.3, 0.35), K(0.36, -0.98, -0.34, -0.98, 0.86, 0.4, 0.56), K(0.5, -0.95, -0.36, -1.0, 0.84, 0.4, 0.55) },
		cam = { { 0, 0, 0 }, { 0.13, -0.008, 0 }, { 0.3, 0, 0 } } },
	cookThrow = { dur = 0.45, out = 0.27, release = 0.03, inT = 0.001, keys = {
		K(0, -0.95, -0.36, -1.0, 0.84, 0.4, 0.55), K(0.03, -0.45, -0.36, -1.75, -0.5, 0.15, 0.1),
		K(0.1, -0.22, -0.78, -2.0, -1.05, 0.05, -0.1), K(0.23, -0.28, -1.5, -1.5, -0.9, 0.0, -0.2), K(0.45, -0.8, -1.6, -1.0, 0.4, 0.2, 0.3) },
		cam = { { 0, 0, 0 }, { 0.05, -0.03, -0.015 }, { 0.23, 0, 0 } } },
}
local function hermite(p0: any, p1: any, p2: any, p3: any, t0: number, t1: number, t2: number, t3: number, u: number): any
	local span = t2 - t1
	local m1 = if t2 > t0 then (p2 - p0) * (span / (t2 - t0)) else p2 - p1
	local m2 = if t3 > t1 then (p3 - p1) * (span / (t3 - t1)) else p2 - p1
	local u2, u3 = u * u, u * u * u
	return p1 * (2 * u3 - 3 * u2 + 1) + m1 * (u3 - 2 * u2 + u) + p2 * (3 * u2 - 2 * u3) + m2 * (u3 - u2)
end
local function sampleClip(c: any, t: number): CFrame
	local keys = c.keys
	local n = #keys
	if t <= keys[1].t then local k = keys[1]; return CFrame.new(k.p) * CFrame.fromEulerAnglesXYZ(k.r.X, k.r.Y, k.r.Z) end
	if t >= keys[n].t then local k = keys[n]; return CFrame.new(k.p) * CFrame.fromEulerAnglesXYZ(k.r.X, k.r.Y, k.r.Z) end
	local i = 1
	while i < n - 1 and t > keys[i + 1].t do i += 1 end
	local k0, k1, k2, k3 = keys[math.max(1, i - 1)], keys[i], keys[i + 1], keys[math.min(n, i + 2)]
	-- (the first and last keys are rests: their tangents come from their one neighbour, halved, so it leaves and
	-- arrives softly)
	local t0 = if i == 1 then k1.t - (k2.t - k1.t) else k0.t
	local t3 = if i + 1 == n then k2.t + (k2.t - k1.t) else k3.t
	local u = (t - k1.t) / (k2.t - k1.t)
	local p = hermite(if i == 1 then k1.p else k0.p, k1.p, k2.p, if i + 1 == n then k2.p else k3.p, t0, k1.t, k2.t, t3, u)
	local r = hermite(if i == 1 then k1.r else k0.r, k1.r, k2.r, if i + 1 == n then k2.r else k3.r, t0, k1.t, k2.t, t3, u)
	return CFrame.new(p) * CFrame.fromEulerAnglesXYZ(r.X, r.Y, r.Z)
end
-- the clip's nod of your view right now (pitch, yaw), eased between its keys
local function sampleCam(c: any, t: number): Vector2
	local ks = c.cam
	if not ks then return Vector2.zero end
	for i = 1, #ks - 1 do
		local a, b = ks[i], ks[i + 1]
		if t >= a[1] and t <= b[1] then
			local u = smooth((t - a[1]) / math.max(1e-4, b[1] - a[1]))
			return Vector2.new(a[2] + (b[2] - a[2]) * u, a[3] + (b[3] - a[3]) * u)
		end
	end
	return Vector2.zero
end
-- the left hand's own arm, when the gun has no left hand of its own: a hold row for a thing held in the fist
Holds.holds.item_hand = { Left = { pose = "grip", at = Vector3.zero, rot = Vector3.zero, size = 0.9 } }
local FP_K = 0.95 -- the item in first person, against its world size (the guns are drawn a little under world size)
local FP_SIZE = { duck = 0.35, frag = 0.75 } -- (the thrown duck is 0.6 m long, web pj_duck: in your hand it's a toy; a throwable in
-- hand is about 11% of the screen wide, as in Rivals)
type Hand = { id: string, clip: any, t0: number, model: Model, grip: CFrame, own: Model?, root: BasePart?, gone: boolean, lastF: CFrame?, extra: any? }
local hand: Hand? = nil
local extraStep: ((Hand, number) -> ())? = nil -- (the camera's print sliding out: the camera below)
-- how far the hand has gone from its hold to the item: there in 0.06 s, back over the clip's last part
local function mixAt(h: Hand, t: number): number
	return smooth(t / (h.clip.inT or 0.06)) * (1 - smooth((t - h.clip.out) / (h.clip.dur - h.clip.out)))
end
local function dropHand()
	local h = hand
	if not h then return end
	hand = nil
	VM.offHook = nil
	h.model:Destroy()
	if h.own then h.own:Destroy() end
end
local function startHand(id: string, clipName: string?)
	dropHand()
	if thirdPerson() or not VM.model then return end
	local clip = CLIPS[clipName or id] or CLIPS.throw
	if id == "nvg" then return end -- (the goggles go on your head, not in your hand: the hand that puts them on is "goggles")
	local m = itemModel(id, me)
	m:ScaleTo(FP_K * (FP_SIZE[id] or 1))
	m.Parent = camera
	local h: Hand = { id = id, clip = clip, t0 = os.clock(), model = m, grip = gripOf(m), gone = false }
	if id == "quiz" then h.grip *= CFrame.Angles(0, -math.pi, 0) end -- (the calculator's screen and keys face you)
	if id == "laptop" then
		-- (the laptop faces you too, so you watch it open and light up: held by its other side edge, its left as you see it)
		local gp = h.grip.Position
		h.grip = CFrame.new(-gp.X, gp.Y, gp.Z) * CFrame.Angles(0, -math.pi, 0)
	end
	-- the gun's own left hand if it has one, else an arm of our own
	local rows = Holds.holds[VM.wid]
	if not (rows and rows.Left) then
		local own = Instance.new("Model")
		own.Name = "ItemArm"
		local root = part(Enum.PartType.Block, Vector3.one * 0.1, Color3.new(), nil)
		root.Name = "Root"; root.Transparency = 1; root.Parent = own
		own.PrimaryPart = root
		own.Parent = camera
		if AvatarArms.hold(own, root, "item_hand", S, nil, Holds.size or 1) then h.own, h.root = own, root else own:Destroy() end
	end
	hand = h
	if not h.own then
		-- (worked out from the camera when the viewmodel asks, so the hand and the item agree in the same frame)
		VM.offHook = function(): (CFrame?, number, boolean)
			local cur = hand
			if not cur then return nil, 0, false end
			local t = os.clock() - cur.t0
			return camera.CFrame * sampleClip(cur.clip, t), mixAt(cur, t), false
		end
	end
end
-- the hand's frame in the world this frame; returns false when the clip is over
local function handStep(): boolean
	local h = hand
	if not h then return false end
	local t = os.clock() - h.t0
	if t >= h.clip.dur or thirdPerson() or menuOpen() or not myChar() then dropHand(); return false end
	local F = camera.CFrame * sampleClip(h.clip, t) -- the fist's frame
	h.lastF = F
	if not h.gone and t >= h.clip.release then
		h.gone = true
		for _, d in h.model:GetDescendants() do if d:IsA("BasePart") then d.Transparency = 1 end end
	end
	-- the item sits in the fist; while the hand is still on its way (or on its way back) it isn't drawn, so it never
	-- floats where the hand isn't
	local mix = mixAt(h, t)
	h.model:PivotTo(F * h.grip:Inverse())
	local hide = if mix < 0.75 then 1 else 0
	for _, d in h.model:GetDescendants() do if d:IsA("BasePart") then d.LocalTransparencyModifier = hide end end
	if h.own and h.root then
		-- (the own arm rises from below the screen and goes back there: no hold to return to)
		local low = camera.CFrame * CFrame.new(-0.6, -2.2, -0.8)
		h.root.CFrame = low:Lerp(F, mix)
		AvatarArms.aim(h.own, camera.CFrame)
		h.model:PivotTo(h.root.CFrame * h.grip:Inverse())
		for _, d in h.model:GetDescendants() do if d:IsA("BasePart") then d.LocalTransparencyModifier = 0 end end
	end
	if h.extra and extraStep then extraStep(h, t) end
	return true
end
-- where the item leaves your hand (a thrown one's flight starts there and slides onto the server's line)
local function releasePoint(): Vector3?
	local h = hand
	if not h or not h.lastF then return nil end
	return h.model:GetPivot().Position
end

-- (what the rest of the script calls in the cook, camera and wand blocks below: the main chunk has a 200 local limit)
local X = {} :: any
-- ---------------------------------------------------------------- pressing G
local lastUse = -math.huge
local toggleGoggles: () -> () -- (the goggles below)
local radarHold: (boolean) -> () -- (the speed trap below)
local snapAt: (number) -> () -- (the camera below)
local whiteFlash: (number, number) -> ()
local printIn: () -> ()
local wandIn: () -> () -- (the bubble wand below)
local laptopIn: () -> () -- (the laptop's lid, below)
;(require(script.Parent:WaitForChild("Keys")) :: any).began(function(io: InputObject, gp: boolean) -- (Keys: the phone's item plate presses G too)
	if gp or not require(script.Parent:WaitForChild("Binds")).is("item", io) then return end -- (G, or the player's own key: Settings)
	if menuOpen() or inHub() then return end
	local _, _, root = myChar()
	if not root then return end
	local id = me:GetAttribute("Item")
	local it = if type(id) == "string" then L[id] else nil
	if not it or not it.live then return end
	if me:GetAttribute("Quiz") then return end -- (sitting a pop quiz: no items)
	if me:GetAttribute("RoundLock") == true then Sfx.play("empty", nil, 0.5); return end -- (before GO / between rounds: gadgets wait for the round, no throw, nothing spent)
	if me:GetAttribute("Trap") then Sfx.play("blub", nil, 0.6); return end -- (in a bubble: BUBBLED is already up)
	if it.id == "nvg" then toggleGoggles(); return end
	if it.id == "radar" then radarHold(true); return end
	if X.cooking() then X.cookRelease(); return end -- (a cooked grenade whose key-up was lost: this press throws it)
	local t = os.clock()
	-- (training, ItemFree: only the short training gap between two presses)
	local useGap = if me:GetAttribute("ItemFree") == true then Items.SPAM_FREE_CLIENT else Items.SPAM_CLIENT
	if it.id == "camera" and not me:GetAttribute("Photo") then
		if t - lastUse < useGap then return end
		lastUse = t
		local eye = if thirdPerson() then root.Position + Vector3.new(0, Hitbox.EYE_UP - Hitbox.ROOT_UP, 0) else camera.CFrame.Position
		ItemR:FireServer("camera", eye, camera.CFrame.LookVector)
		snapAt(t)
		startHand("snap")
		handStep()
		return
	end
	if it.id == "camera" and t - lastUse < useGap then
		-- (G again straight after the snap: the print goes as soon as the server will take it, not lost)
		local again = lastUse
		task.delay(useGap - (t - lastUse) + 0.03, function()
			if lastUse ~= again or not me:GetAttribute("Photo") or me:GetAttribute("Item") ~= "camera" then return end
			local n0 = charges()
			if n0 <= 0 then return end
			local _, _, r0 = myChar()
			if not r0 then return end
			lastUse = os.clock()
			pend = { n = n0 - 1, t = lastUse }
			local eye0 = if thirdPerson() then r0.Position + Vector3.new(0, Hitbox.EYE_UP - Hitbox.ROOT_UP, 0) else camera.CFrame.Position
			ItemR:FireServer("camera", eye0, camera.CFrame.LookVector)
			startHand("print")
			printIn()
			handStep()
		end)
		return
	end
	if t - lastUse < useGap then return end
	local n, nextAt = charges()
	if n <= 0 then
		Sfx.play("empty")
		if it.id == "camera" and me:GetAttribute("Photo") then
			-- (the photo is held, the print waits for the charge: say when, not just "recharging")
			local left = math.max(1, math.ceil(nextAt - workspace:GetServerTimeNow()))
			Hud.callout(("PRINT READY IN %d S"):format(left), 1.2)
		else
			Hud.callout(string.lower(it.name) .. ": recharging", 0.8)
		end
		return
	end
	lastUse = t
	pend = { n = n - 1, t = t }
	if X.cooks(it.id) then X.cookStart(it.id); return end -- (a grenade: the pin comes out, G up throws it)
	-- from your eye (the camera itself in first person, so it leaves from under the crosshair), along your look
	local eye = if thirdPerson() then root.Position + Vector3.new(0, Hitbox.EYE_UP - Hitbox.ROOT_UP, 0) else camera.CFrame.Position
	ItemR:FireServer(it.id, eye, camera.CFrame.LookVector)
	if it.id == "overdrive" then return end -- (the rig: no hand throw here, its own arms and sounds are RigClient's)
	if it.id == "camera" then
		startHand("print")
		printIn()
		handStep()
		return
	end
	startHand(it.id)
	if it.id == "wand" then wandIn() elseif it.id == "laptop" then laptopIn() elseif it.id == "medkit" then X.medkitIn() end
	handStep()
	if it.id ~= "popper" and it.id ~= "reverse" and it.id ~= "laptop" and it.id ~= "wand" then -- (those make their sound when the server says it happened)
		Sfx.play(if it.id == "medkit" then "heal" elseif it.id == "bubble" then "reverse" else "swing")
		-- (a skin's own layer on top: the medkit opening, a thrown one's throw)
		if (Sfx :: any).skinItem then (Sfx :: any).skinItem(me, it.id, if it.id == "medkit" then "open" else "throw") end
	end
end)

-- ---------------------------------------------------------------- the world: emitters
local TEX = {
	fire = "rbxasset://textures/particles/fire_main.dds",
	smoke = "rbxasset://textures/particles/smoke_main.dds",
	blob = "rbxassetid://96136840417410",
	ring = "rbxasset://textures/particles/explosion01_shockwave_main.dds",
	spark = "rbxasset://textures/particles/sparkles_main.dds",
}
local function ns(...: number): NumberSequence
	local a = { ... }
	local k = {}
	for i = 1, #a, 2 do table.insert(k, NumberSequenceKeypoint.new(a[i], a[i + 1])) end
	return NumberSequence.new(k)
end
local function cs(...: Color3): ColorSequence
	local a = { ... }
	if #a == 1 then return ColorSequence.new(a[1]) end
	local k = {}
	for i, c in a do table.insert(k, ColorSequenceKeypoint.new((i - 1) / (#a - 1), c)) end
	return ColorSequence.new(k)
end
local NR = NumberRange.new
-- a host part for one effect's emitters, gone after `life` s
local function host(at: Vector3, life: number): BasePart
	local p = part(Enum.PartType.Block, Vector3.one * 0.2, Color3.new(), nil)
	p.Name = "ItemFx"; p.Transparency = 1; p.CFrame = CFrame.new(at); p.Parent = folder
	Debris:AddItem(p, life)
	return p
end
local function emitter(parent: Instance, props: { [string]: any }): ParticleEmitter
	local e = Instance.new("ParticleEmitter")
	e.Enabled = false; e.Rate = 0; e.LockedToPart = false
	for k, v in props do (e :: any)[k] = v end
	e.Parent = parent
	return e
end

-- the screen shake: added on top of the camera each frame and taken off again the next (like Arsenal's)
local shake = 0
local applied = Vector2.zero
RunService:BindToRenderStep("JankfireItemShake", Enum.RenderPriority.Camera.Value + 2, function(dt: number)
	shake = math.max(0, shake - dt * 2.4)
	local want = if shake > 0 then Vector2.new((math.random() - 0.5), (math.random() - 0.5)) * shake * 0.035 else Vector2.zero
	local h = hand
	if h and h.clip.cam and not thirdPerson() then want += sampleCam(h.clip, os.clock() - h.t0) end
	local d = want - applied
	if d.Magnitude > 0 then camera.CFrame = camera.CFrame * CFrame.Angles(d.X, d.Y, 0) end
	applied = want
end)
local function shakeFrom(at: Vector3, k: number)
	local f = math.max(0, 1 - (camera.CFrame.Position - at).Magnitude / Items.SHAKE)
	shake = math.max(shake, f * k)
end

-- ---------------------------------------------------------------- the frag's blast
local function floorBelow(at: Vector3, depth: number): Vector3?
	local map = workspace:FindFirstChild("Map")
	if not map then return nil end
	local rp = RaycastParams.new()
	rp.FilterType = Enum.RaycastFilterType.Include
	rp.FilterDescendantsInstances = { map }
	local r = workspace:Raycast(at + Vector3.new(0, 0.5, 0), Vector3.new(0, -depth, 0), rp)
	return r and r.Position
end
local function boom(at: Vector3, R: number)
	-- the look is Fx.explosion (the VFX pipeline, roblox/docs/VFX-PIPELINE.md: the web's fireball flipbook, white pop,
	-- soot, sparks and feathers, plus a ring across the floor, its dust and a light). the sound and the shake stay here
	local FxM = require(script.Parent:WaitForChild("Fx")) :: any
	FxM.explosion(at, R)
	Sfx.play("boom", at)
	shakeFrom(at, 1)
end

-- ---------------------------------------------------------------- thrown items in flight
type Vis = { id: number, k: string, p: Vector3, v: Vector3, r: number, bounce: number, grav: number, born: number, fuse: number,
	model: Model, axis: Vector3, ang: number, off: Vector3, mine: boolean, lamp: BasePart?, target: Instance? }
local flying: { [number]: Vis } = {}
local mapRp = RaycastParams.new()
mapRp.FilterType = Enum.RaycastFilterType.Include
local function cast(o: Vector3, r: number, move: Vector3): (number?, Vector3?)
	local map = workspace:FindFirstChild("Map")
	if not map then return nil, nil end
	mapRp.FilterDescendantsInstances = { map }
	local res = workspace:Spherecast(o, r, move, mapRp)
	if res then return res.Distance, res.Normal end
	return nil, nil
end
local function addFlying(m: any)
	if type(m.id) ~= "number" or typeof(m.p) ~= "Vector3" or typeof(m.v) ~= "Vector3" or not Items.PROJ[m.w] then return end
	if flying[m.id] then return end
	local w = Items.PROJ[m.w]
	local model = itemModel(m.w, if type(m.o) == "number" then Players:GetPlayerByUserId(m.o) else nil)
	model.Parent = folder
	do local FxM = require(script.Parent:WaitForChild("Fx")) :: any; if FxM.itemFlight then pcall(FxM.itemFlight, model) end end -- (a skin's flight trail)
	local mine = m.o == me.UserId
	if m.w == "duck" and not mine then Sfx.play("squeak", m.p, 0.8) end
	local vis: Vis = { id = m.id, k = m.w, p = m.p, v = m.v, r = w.r, bounce = w.bounce, grav = w.grav, born = os.clock(),
		fuse = if type(m.fuse) == "number" then m.fuse else w.fuse, model = model,
		axis = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5).Unit, ang = 0, off = Vector3.zero, mine = mine,
		lamp = model:FindFirstChild("lamp", true) :: BasePart? }
	if X.pinParts then for _, q in X.pinParts(model) do q.Transparency = 1 end end -- (thrown: the pin's out)
	-- yours leaves from your hand and slides onto the server's line within a moment
	local rel = if mine then releasePoint() else nil
	if rel then vis.off = rel - m.p end
	flying[m.id] = vis
	if not mine then Sfx.play("swing", m.p, 0.8) end
	if not mine and type(m.o) == "number" and (Sfx :: any).skinItem then
		(Sfx :: any).skinItem(Players:GetPlayerByUserId(m.o), if m.w == "smokegren" then "smoke" elseif m.w == "calc" then "quiz" else m.w, "throw", m.p)
	end
end
-- went: the server says it went off there (its fuse ran out, or the duck stuck): a skin's landing effect plays
local function dropFlying(id: any, went: boolean?, at: Vector3?)
	local v = if type(id) == "number" then flying[id] else nil
	if not v then return end
	flying[id] = nil
	if went then
		local FxM = require(script.Parent:WaitForChild("Fx")) :: any
		if FxM.itemLand then pcall(FxM.itemLand, v.model, at or (v.p + v.off)) end
	end
	v.model:Destroy()
end
-- someone's middle (their feet + 0.9 m: what the duck homes on and the hole sits at)
local function middleOf(m: Instance?): Vector3?
	local r = m and m:FindFirstChild("HumanoidRootPart") :: BasePart?
	return r and r.Position - Vector3.new(0, Hitbox.ROOT_UP - Items.CENTRE, 0)
end
local function flyStep(dt: number)
	for _, v in flying do
		if v.k == "duck" then
			local c = middleOf(v.target)
			if c and v.v.Magnitude > Items.DUCK.minSpeed then v.v = Items.steer(v.v, c - v.p, Items.DUCK.turn * dt) end
		end
		Items.step(v, dt, cast)
		v.off *= math.exp(-dt / 0.07)
		local spd = v.v.Magnitude
		v.ang += dt * math.min(spd, 20 * S) * 0.12
		local cf = CFrame.new(v.p + v.off) * CFrame.fromAxisAngle(v.axis, v.ang)
		-- (a duck flies beak first, rocking a little, not tumbling)
		if v.k == "duck" and v.v.Magnitude > 1 then
			local fl = Vector3.new(v.v.X, 0, v.v.Z)
			local ahead = if fl.Magnitude > 0.1 then fl.Unit else Vector3.zAxis
			cf = CFrame.lookAt(v.p + v.off, v.p + v.off + ahead) * CFrame.Angles(math.sin(v.ang * 3) * 0.25, 0, math.sin(v.ang * 2) * 0.2)
		end
		v.model:PivotTo(cf)
		-- the frag's lamp blinks faster as the fuse runs down
		if v.lamp then
			local left = v.fuse - (os.clock() - v.born)
			local hz = if left < 0.6 then 12 elseif left < 1.2 then 6 else 3
			v.lamp.Transparency = if math.floor(os.clock() * hz * 2) % 2 == 0 then 0 else 0.85
		end
	end
end

-- ---------------------------------------------------------------- smoke clouds
type Cloud = { id: number, h: BasePart?, ems: { ParticleEmitter }, untilT: number }
local cloudsLive: { [number]: Cloud } = {}
local SMOKE_COL = Color3.fromRGB(176, 180, 186)
local function addCloud(id: number, at: Vector3, r: number, left: number)
	if cloudsLive[id] then return end
	-- the look is Fx.smokeCloud (the VFX pipeline: the web's own soft smoke sheet, puffing low and wide for the cloud's
	-- life, thinning out over its last 3 s). this file keeps the bookkeeping and the sound
	local FxM = require(script.Parent:WaitForChild("Fx")) :: any
	FxM.smokeCloud(id, at, r, left)
	local h: BasePart? = nil
	local ems: { ParticleEmitter } = {}
	cloudsLive[id] = { id = id, h = h, ems = ems, untilT = os.clock() + left }
	Sfx.play("blow", at)
end
local function cloudStep()
	local t = os.clock()
	for id, c in cloudsLive do
		-- (stop feeding it ~3 s before the end, so it's thinned out by the time the server's cloud is gone)
		if t >= c.untilT - 3 then
			for _, e in c.ems do e.Enabled = false end
			if t >= c.untilT then cloudsLive[id] = nil end
		end
	end
end

-- ---------------------------------------------------------------- shield domes
type Dome = { id: number, ball: BasePart, ring: BasePart?, t0: number, untilT: number, r: number }
local domes: { [number]: Dome } = {}
local DOME_COL = Color3.fromRGB(96, 206, 236)
local function addDome(id: number, at: Vector3, r: number, left: number, fresh: boolean)
	if domes[id] then return end
	local ball = part(Enum.PartType.Ball, Vector3.one * r * 2, DOME_COL, Enum.Material.ForceField)
	ball.Name = "ShieldDome"; ball.CFrame = CFrame.new(at); ball.Parent = folder
	local fl = floorBelow(at, r)
	local ring: BasePart? = nil
	if fl then
		-- where the dome meets the floor: a faint band, so you can tell if you're inside from first person
		local rr = part(Enum.PartType.Cylinder, Vector3.new(0.08, 2, 2), DOME_COL, Enum.Material.Neon)
		local flat = math.sqrt(math.max(0, r * r - (at.Y - fl.Y) ^ 2))
		rr.Size = Vector3.new(0.06, flat * 2, flat * 2)
		rr.CFrame = CFrame.new(fl + Vector3.new(0, 0.04, 0)) * CFrame.Angles(0, 0, math.pi / 2)
		rr.Transparency = 0.82
		rr.Parent = folder
		ring = rr
	end
	domes[id] = { id = id, ball = ball, ring = ring, t0 = if fresh then os.clock() else -math.huge, untilT = os.clock() + left, r = r }
	-- the layers round it (Fx.domeOpen, the VFX pipeline: an opening flash and floor ring, two orbiting bands, ripples)
	local FxM = require(script.Parent:WaitForChild("Fx")) :: any
	FxM.domeOpen(id, at, r, fl, fresh)
	if fresh then Sfx.play("reverse", at, 0.9) end
end
local function dropDome(id: any)
	local d = if type(id) == "number" then domes[id] else nil
	if not d then return end
	domes[id] = nil
	local FxM = require(script.Parent:WaitForChild("Fx")) :: any
	FxM.domeClose(id, true) -- (its skin bursts into droplets)
	Sfx.play("pop", d.ball.Position)
	local ball, ring = d.ball, d.ring
	task.spawn(function()
		local t0 = os.clock()
		while ball.Parent do
			local u = (os.clock() - t0) / 0.18
			if u >= 1 then break end
			ball.Size = Vector3.one * d.r * 2 * (1 + 0.08 * u)
			ball.Transparency = u
			RunService.RenderStepped:Wait()
		end
		ball:Destroy()
		if ring then ring:Destroy() end
	end)
end
local function domeStep()
	local t = os.clock()
	for _, d in domes do
		-- in: from 70 % with a little overshoot over 0.16 s. its last second: it flickers
		local age = t - d.t0
		local k = if age < 0.16 then 0.7 + 0.3 * (1 + 2.2 * (age / 0.16 - 1) ^ 3 + 1.2 * (age / 0.16 - 1) ^ 2) else 1
		d.ball.Size = Vector3.one * d.r * 2 * k
		local left = d.untilT - t
		d.ball.Transparency = if left < 1 and math.floor(t * 14) % 2 == 0 then 0.6 else 0
	end
end
local function domeHit(at: Vector3)
	emitter(host(at, 2), { Texture = TEX.blob, LightEmission = 1, LightInfluence = 0, Brightness = 3,
		Color = cs(Color3.fromRGB(220, 250, 255), DOME_COL), Size = ns(0, 0.25 * S, 1, 0),
		Lifetime = NR(0.2, 0.4), Speed = NR(3 * S, 8 * S), SpreadAngle = Vector2.new(70, 70), Drag = 3 }):Emit(8)
	Sfx.play("ricochet", at, 0.6)
end

-- ---------------------------------------------------------------- the medkit
local function healFx(model: Instance?, mine: boolean)
	local root = model and model:FindFirstChild("HumanoidRootPart") :: BasePart?
	if root then
		-- the look is Fx.heal (the VFX pipeline: two green ribbons spiralling up, a ring of light at the feet, sparkles)
		local FxM = require(script.Parent:WaitForChild("Fx")) :: any
		FxM.heal(root)
		if not mine then Sfx.play("heal", root.Position, 0.8) end
	end
	if mine then H.flash(0.1, 0.5, Color3.fromRGB(120, 230, 150)) end
end

-- ---------------------------------------------------------------- the party popper
local CONFETTI = { Color3.fromRGB(240, 240, 234), Color3.fromRGB(226, 190, 96), Color3.fromRGB(206, 112, 150), Color3.fromRGB(104, 186, 198) }
local function confetti(at: Vector3, dir: Vector3, n: number, speed: number)
	local h = host(at, 3)
	for i, c in CONFETTI do
		local e = emitter(h, { Texture = TEX.blob, LightInfluence = 0.6, LightEmission = 0.2, Color = cs(c),
			Size = ns(0, 0.07 * S, 1, 0.05 * S), Transparency = ns(0, 0, 0.8, 0, 1, 1), Lifetime = NR(0.8, 1.6),
			Speed = NR(speed * 0.4, speed), SpreadAngle = Vector2.new(22, 22), Drag = 2.2,
			Acceleration = Vector3.new(0, -9 * S, 0), Rotation = NR(0, 360), RotSpeed = NR(-400, 400),
			EmissionDirection = Enum.NormalId.Top, Orientation = Enum.ParticleOrientation.FacingCamera })
		h.CFrame = CFrame.lookAt(at, at + dir) * CFrame.Angles(-math.pi / 2, 0, 0)
		e:Emit(math.ceil(n / #CONFETTI) + (if i == 1 then n % #CONFETTI else 0))
	end
end
local function popperFx(m: any)
	local d = if typeof(m.d) == "Vector3" and m.d.Magnitude > 0.5 then m.d.Unit else nil
	if not d then return end
	local mine = m.o == me.UserId
	local from: Vector3? = nil
	if mine and hand and hand.id == "popper" then from = (hand.model:GetPivot() * CFrame.new(0, 0.35, 0)).Position end
	if not from then
		local model = if typeof(m.model) == "Instance" then m.model else nil
		local head = model and model:FindFirstChild("Head") :: BasePart?
		from = if head then head.Position + d * 1.5 elseif typeof(m.p) == "Vector3" then m.p + d * 1.5 else nil
	end
	if not from then return end
	confetti(from, d, 40, 9 * S) -- (web: 40 off the muzzle)
	confetti(from + d * 2, d, 30, 14 * S) -- (and a longer spray down the aim, web fx.confetti)
	Sfx.play("popper", if mine then nil else from)
	if mine then
		-- you fly back along your look (web: -d x recoil + lift up; your own movement, like the web game)
		local P = Items.POPPER
		Body.push(-d * P.recoil + Vector3.new(0, P.lift, 0))
		shake = math.max(shake, 0.45)
	end
end

-- ---------------------------------------------------------------- the reverse card: over the holder's head while it's up
type Card = { model: Model, root: BasePart?, ring: BasePart, untilT: number, ang: number }
local cards: { [number]: Card } = {}
local REV_COL = Color3.fromRGB(176, 58, 52)
local function dropCard(uid: number)
	local c = cards[uid]
	if not c then return end
	cards[uid] = nil
	c.model:Destroy(); c.ring:Destroy()
end
local function addCard(uid: number, model: Instance?, dur: number)
	dropCard(uid)
	local root = model and model:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not root then return end
	local cm = itemModel("reverse", Players:GetPlayerByUserId(uid))
	cm:ScaleTo(10) -- (web: a 0.7 x 1.05 m card, 2.9 m over their head)
	cm.Parent = folder
	-- a flat ring round them at the waist (a see-through plate with the ring picture on both faces)
	local ring = part(Enum.PartType.Block, Vector3.new(1.05 * S * 2, 0.05, 1.05 * S * 2), REV_COL, nil)
	ring.Transparency = 1
	for _, face in { Enum.NormalId.Top, Enum.NormalId.Bottom } do
		local dc = Instance.new("Decal")
		dc.Texture = TEX.ring; dc.Face = face; dc.Color3 = Color3.fromRGB(236, 110, 96); dc.Transparency = 0.35; dc.Parent = ring
	end
	ring.Parent = folder
	cards[uid] = { model = cm, root = root, ring = ring, untilT = os.clock() + dur, ang = 0 }
end
local function cardStep(dt: number)
	local t = os.clock()
	for uid, c in cards do
		if t >= c.untilT or not c.root or not c.root.Parent then dropCard(uid); continue end
		c.ang += dt * 9 -- (web: 9 rad/s)
		local feet = c.root.Position - Vector3.new(0, Hitbox.ROOT_UP, 0)
		c.model:PivotTo(CFrame.new(feet + Vector3.new(0, 2.9 * S + 1.6, 0)) * CFrame.Angles(0, c.ang, 0))
		-- a thin ring round them at the waist, turning the other way (where the web game has its two arrows)
		local ring = c.ring
		ring.CFrame = CFrame.new(feet + Vector3.new(0, 1 * S, 0)) * CFrame.Angles(0, -c.ang * 0.5, 0)
		local fade = if c.untilT - t < 0.6 and math.floor(t * 12) % 2 == 0 then 0.8 else 0.35
		for _, dc in ring:GetChildren() do if dc:IsA("Decal") then dc.Transparency = fade end end
	end
end
local function reverseFx(m: any)
	local model = if typeof(m.model) == "Instance" then m.model else nil
	local root = model and model:FindFirstChild("HumanoidRootPart") :: BasePart?
	local at = if root then root.Position else nil
	if type(m.o) == "number" then addCard(m.o, model, if type(m.dur) == "number" then m.dur else Items.REVERSE.dur) end
	if at then
		emitter(host(at + Vector3.new(0, 1, 0), 2), { Texture = TEX.blob, LightEmission = 0.8, LightInfluence = 0.2, Brightness = 2,
			Color = cs(Color3.fromRGB(236, 96, 80), Color3.fromRGB(240, 200, 110)), Size = ns(0, 0.2 * S, 1, 0),
			Lifetime = NR(0.3, 0.55), Speed = NR(4 * S, 8 * S), SpreadAngle = Vector2.new(180, 20), Drag = 3 }):Emit(36)
	end
	Sfx.play("reverse", if m.o == me.UserId then nil else at)
	if m.o == me.UserId then Hud.callout("REVERSE", 1.0); shake = math.max(shake, 0.2) end
end
local function reflectFx(m: any)
	local model = if typeof(m.model) == "Instance" then m.model else nil
	local root = model and model:FindFirstChild("HumanoidRootPart") :: BasePart?
	if root then
		emitter(host(root.Position + Vector3.new(0, 1, 0), 2), { Texture = TEX.blob, LightEmission = 0.8, LightInfluence = 0.2, Brightness = 2,
			Color = cs(Color3.fromRGB(236, 96, 80), Color3.fromRGB(240, 200, 110)), Size = ns(0, 0.18 * S, 1, 0),
			Lifetime = NR(0.25, 0.45), Speed = NR(3 * S, 6 * S), SpreadAngle = Vector2.new(180, 180), Drag = 3 }):Emit(18)
	end
	if m.o == me.UserId then Hud.callout("REVERSED THEM", 0.9)
	elseif m.by == me.UserId then Hud.callout("REVERSED", 0.9) end
end

-- ---------------------------------------------------------------- the rubber duck's black hole
-- a void you can see from across a room without it shouting: a black core, a dim violet shell, a thin ring turning
-- round it, a small duck orbiting, sparks drawn into the middle; it grows in over 0.3 s and pulses. the duck stuck to
-- someone rides their chest at 1.5x, wobbling (web duck.js). your own speed gets eaten inside it (Body.onStep below)
-- (16 Nov evening, the owner: "actual blackhole effect for duck pls": Fx draws the whole hole now, a black horizon, a
-- spinning accretion disk, the lensing halo, bits spiralling in; Fx.holeOpen returns true and the core, shell, ring and
-- spark shell below are not made. they stay as the look if Fx can't draw it)
type HoleV = { id: number, p: Vector3, on: Instance?, born: number, R: number, mine: boolean, core: BasePart?, shell: BasePart?,
	ring: BasePart?, pull: BasePart?, orbit: Model, stuck: Model?, ang: number }
local holesV: { [number]: HoleV } = {}
local VOID = Color3.fromRGB(10, 8, 14)
local VIOLET = Color3.fromRGB(122, 84, 190)
local function addHole(m: any)
	local id = m.id
	if type(id) ~= "number" or holesV[id] or typeof(m.p) ~= "Vector3" then return end
	local on = if typeof(m.on) == "Instance" then m.on else nil
	local R = if type(m.R) == "number" then m.R else Items.DUCK.holeR
	local age = if type(m.age) == "number" then m.age else 0
	local FxM = require(script.Parent:WaitForChild("Fx")) :: any
	-- (age: already open for late joiners)
	local drawn = FxM.holeOpen(id, m.p, R, age, if type(m.life) == "number" then m.life else nil) == true -- (life: a Duck Rain hole's own)
	local core: BasePart?, shell: BasePart?, ring: BasePart?, pull: BasePart? = nil, nil, nil, nil
	if not drawn then
		core = part(Enum.PartType.Ball, Vector3.one * 2 * S, VOID, Enum.Material.SmoothPlastic)
		local sh = part(Enum.PartType.Ball, Vector3.one * 3 * S, VIOLET, Enum.Material.Neon); sh.Transparency = 0.78; shell = sh
		local rg = part(Enum.PartType.Block, Vector3.new(4.4 * S, 0.05, 4.4 * S), VIOLET, nil); rg.Transparency = 1; ring = rg
		for _, face in { Enum.NormalId.Top, Enum.NormalId.Bottom } do
			local dc = Instance.new("Decal")
			dc.Texture = TEX.ring; dc.Face = face; dc.Color3 = Color3.fromRGB(170, 130, 235); dc.Transparency = 0.25; dc.Parent = rg
		end
		-- sparks drawn in from a shell at 0.6 of its reach (an inward sphere emitter: they fly to the middle)
		local pl = part(Enum.PartType.Ball, Vector3.one * R * 1.2, VIOLET, nil); pl.Transparency = 1; pull = pl
		local e = emitter(pl, { Texture = TEX.blob, LightEmission = 1, LightInfluence = 0, Brightness = 2,
			Color = cs(Color3.fromRGB(200, 170, 255), VIOLET), Size = ns(0, 0.12 * S, 1, 0.04 * S), Transparency = ns(0, 0.2, 1, 0.9),
			Lifetime = NR(0.5, 0.7), Speed = NR(R * 0.6 / 0.6, R * 0.6 / 0.5), Rate = 40,
			Shape = Enum.ParticleEmitterShape.Sphere, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
			ShapeInOut = Enum.ParticleEmitterShapeInOut.Inward, Orientation = Enum.ParticleOrientation.VelocityParallel, Squash = ns(0, 2, 1, 2) })
		e.Enabled = true
		for _, x in { core, shell, ring, pull } do (x :: BasePart).Parent = folder end
	end
	local holeBy = if type(m.o) == "number" then Players:GetPlayerByUserId(m.o) else nil
	local orbit = itemModel("duck", holeBy); orbit:ScaleTo(0.35)
	orbit.Parent = folder
	local hv: HoleV = { id = id, p = m.p, on = on, born = os.clock() - age, R = R, mine = m.o == me.UserId, core = core, shell = shell,
		ring = ring, pull = pull, orbit = orbit, stuck = nil, ang = 0 }
	if on then
		local dm = itemModel("duck", holeBy); dm:ScaleTo(0.7); dm.Parent = folder
		hv.stuck = dm
	end
	holesV[id] = hv
	if age < 0.5 then Sfx.play("hole", m.p, 0.9) end
	if age < 0.5 and holeBy and (Sfx :: any).skinItem then (Sfx :: any).skinItem(holeBy, "duck", "land", m.p) end -- (the duck's skin layer as it sticks)
end
local function updHole(m: any)
	local hv = if type(m.id) == "number" then holesV[m.id] else nil
	if not hv then addHole(m); return end
	if typeof(m.p) == "Vector3" then hv.p = m.p end
	hv.on = if typeof(m.on) == "Instance" then m.on else nil
	if not hv.on and hv.stuck then hv.stuck:Destroy(); hv.stuck = nil end
end
local function popHole(m: any)
	local hv = if type(m.id) == "number" then holesV[m.id] else nil
	if hv then
		holesV[m.id] = nil
		for _, x in { hv.core, hv.shell, hv.ring, hv.pull } do if x then x:Destroy() end end
		hv.orbit:Destroy()
		if hv.stuck then hv.stuck:Destroy() end
	end
	do
		local FxM = require(script.Parent:WaitForChild("Fx")) :: any
		FxM.holePop(m.id, if m.quiet or typeof(m.p) ~= "Vector3" then nil else m.p, if type(m.r) == "number" then m.r else nil)
	end
	if m.quiet or typeof(m.p) ~= "Vector3" then return end
	-- the pop (web fx.blast: a purple flash + 60 purple fire bits) + boom and a squeak, shake
	local at = m.p :: Vector3
	local r = if type(m.r) == "number" then m.r else Items.DUCK.blastR
	local flash = part(Enum.PartType.Ball, Vector3.one * r * 0.5, Color3.fromRGB(196, 160, 255), Enum.Material.Neon)
	flash.CFrame = CFrame.new(at); flash.Parent = folder
	task.spawn(function()
		local t0 = os.clock()
		while flash.Parent do
			local u = (os.clock() - t0) / 0.3
			if u >= 1 then break end
			flash.Size = Vector3.one * r * (0.5 + 0.9 * u)
			flash.Transparency = u
			RunService.RenderStepped:Wait()
		end
		flash:Destroy()
	end)
	emitter(host(at, 3), { Texture = TEX.fire, LightEmission = 1, LightInfluence = 0, Brightness = 2,
		Color = cs(Color3.fromRGB(230, 210, 255), Color3.fromRGB(150, 100, 230), Color3.fromRGB(70, 40, 120)),
		Size = ns(0, r * 0.12, 1, r * 0.04), Transparency = ns(0, 0, 1, 1), Lifetime = NR(0.25, 0.5),
		Speed = NR(r * 1.2, r * 2.4), SpreadAngle = Vector2.new(180, 180), Drag = 4, Rotation = NR(0, 360) }):Emit(60)
	Sfx.play("boom", at, 0.8)
	Sfx.play("squeak", at)
	shakeFrom(at, 1)
end
local function holeStep(dt: number)
	local t = os.clock()
	local FxM = require(script.Parent:WaitForChild("Fx")) :: any
	for _, hv in holesV do
		if hv.on then
			local c = middleOf(hv.on)
			if c then hv.p = c end
		end
		FxM.holeMove(hv.id, hv.p)
		hv.ang += dt
		local age = t - hv.born
		-- grows in over 0.3 s once open, pulses 8 % at 20 rad/s; the ring turns at 3 rad/s, the little duck orbits at 6
		local g = if age < 0 then 0 else math.min(1, age / 0.3)
		local pulse = 1 + 0.08 * math.sin(t * 20)
		local k = g * pulse
		local core, shell, ring, pull = hv.core, hv.shell, hv.ring, hv.pull
		if core and shell and ring and pull then
			core.Size = Vector3.one * 2 * S * math.max(k, 0.01)
			shell.Size = Vector3.one * 3 * S * math.max(k, 0.01)
			core.CFrame = CFrame.new(hv.p); shell.CFrame = CFrame.new(hv.p); pull.CFrame = CFrame.new(hv.p)
			ring.Size = Vector3.new(4.4 * S * math.max(g, 0.01), 0.05, 4.4 * S * math.max(g, 0.01))
			ring.CFrame = CFrame.new(hv.p) * CFrame.Angles(0.35, hv.ang * 3, 0)
			local em = pull:FindFirstChildOfClass("ParticleEmitter")
			if em then em.Enabled = age >= 0 end
		end
		local oa = hv.ang * 6
		hv.orbit:PivotTo(CFrame.new(hv.p + Vector3.new(math.cos(oa), 0.15, math.sin(oa)) * 2.6 * S * g) * CFrame.Angles(0, -oa, 0))
		if hv.stuck then
			local r = hv.on and hv.on:FindFirstChild("HumanoidRootPart") :: BasePart?
			if r then
				-- beak first in their chest, 0.42 m in front of them, shaking +-0.5 rad at 7-8 Hz
				local cf = r.CFrame * CFrame.new(0, 0.2, -0.42 * S) * CFrame.Angles(math.sin(t * 47) * 0.5, math.pi, math.sin(t * 44) * 0.4)
				hv.stuck:PivotTo(cf)
			end
		end
	end
end

-- your momentum inside someone else's hole (web player.js holeEat + physics.js holeDrag): Move.client.luau calls
-- this every physics step with its own state. a rope within snapR of the middle snaps
local squeeze = Instance.new("ColorCorrectionEffect")
squeeze.Name = "JankHoleSqueeze"; squeeze.Enabled = false
squeeze.Parent = game:GetService("Lighting")
local holeF = 0
local GrappleR = Remotes:WaitForChild("Grapple") :: RemoteEvent
Body.onStep = function(st: any, chest: Vector3, dt: number)
	holeF = 0
	if not next(holesV) then return end
	local t = os.clock()
	local at = chest - Vector3.new(0, Hitbox.ROOT_UP - Items.CENTRE, 0)
	for _, hv in holesV do
		if t < hv.born or hv.mine then continue end -- (not open yet; your own hole doesn't eat yours)
		local myModel = me.Character
		local k = Items.DUCK.drag * (if hv.on and hv.on == myModel then Items.DUCK.onDrag else 1)
		local vel, d = Items.holeDrag(at, Vector3.new(st.vx, st.vy, st.vz), hv.p, hv.R, k, dt)
		if not d then continue end
		st.vx, st.vy, st.vz = vel.X, vel.Y, vel.Z
		holeF = math.max(holeF, 1 - d / hv.R)
		if st.hook and d < Items.DUCK.snapR then
			st.hook = nil
			GrappleR:FireServer("release")
			Hud.callout("ROPE SNAPPED", 0.7)
			Sfx.play("ropesnap")
		end
	end
end
local function squeezeStep()
	-- (a violet squeeze over the view while a hole eats your speed: web duck.js, opacity holeF x 1.5, at most 0.9.
	-- 17 Nov, Duck Rain: with sky holes everywhere you are nearly always in one, and the whole arena went lavender:
	-- now only in the inner 60 % of a hole's reach, at most half, paler)
	local a = 0.5 * math.clamp((holeF - 0.4) / 0.6, 0, 1)
	squeeze.Enabled = a > 0.01
	if squeeze.Enabled then
		squeeze.TintColor = Color3.new(1, 1, 1):Lerp(Color3.fromRGB(214, 198, 255), a)
		squeeze.Saturation = -0.4 * a
		squeeze.Contrast = 0.2 * a
	end
end

-- ---------------------------------------------------------------- keys a pop-up or an exam has taken (Arsenal leaves them alone)
local busy: { [string]: { number } } = {}
local function setBusy(who: string, keys: { number }?)
	busy[who] = keys
	local all = {}
	for _, ks in busy do for _, k in ks do if not table.find(all, k) then table.insert(all, k) end end end
	table.sort(all)
	me:SetAttribute("BusyKeys", if #all > 0 then table.concat(all, ",") else nil)
end
local NUM = { [Enum.KeyCode.One] = 1, [Enum.KeyCode.Two] = 2, [Enum.KeyCode.Three] = 3, [Enum.KeyCode.Four] = 4, [Enum.KeyCode.Five] = 5,
	[Enum.KeyCode.KeypadOne] = 1, [Enum.KeyCode.KeypadTwo] = 2, [Enum.KeyCode.KeypadThree] = 3, [Enum.KeyCode.KeypadFour] = 4, [Enum.KeyCode.KeypadFive] = 5 }
local overlay = Instance.new("ScreenGui")
overlay.Name = "JankfireItemsOverlay"; overlay.ResetOnSpawn = false; overlay.IgnoreGuiInset = true; overlay.DisplayOrder = 8
overlay.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
overlay.Parent = me:WaitForChild("PlayerGui")
local stage = T.scaled(overlay)

-- ---------------------------------------------------------------- the laptop's pop-up ads (web public/js/ads.js)
-- five windows at fixed spots over your view, one on the crosshair; each has its key in its close box (the mouse is
-- busy aiming): 1-5 close them; closing one sometimes brings back an ARE YOU SURE? (at most `sure` of them). they all
-- go when the time is up or you die. the words are the web game's own nonsense, minus anything Roblox wouldn't want
local COPY = {
	{ "CONGRATULATIONS", "you are the 1,000,000th person shot here today.", "CLAIM NOTHING" },
	{ "DOCTORS HATE HIM", "local man stops dying with one weird trick (cover).", "LEARN COVER" },
	{ "JANK COLA", "now with 30% more can.", "THIRST" },
	{ "LOSE 100 HP FAST", "ask the person who sent you this.", "ASK THEM" },
	{ "BREAD", "it's bread. buy bread.", "BREAD" },
	{ "ONE WEIRD SPOON", "spoon owners in your area are furious.", "SEE SPOON" },
	{ "IS YOUR GRASS TOUCHED?", "take our 40 minute quiz to find out.", "START QUIZ" },
	{ "DEAD MALL CLEARANCE", "everything must go. it already went. come look at where it was.", "LOOK" },
	{ "PREMIUM WALLS", "subscribe today. now 12% more solid.", "WALL ME" },
	{ "A MESSAGE FROM HR", "the tall guy would like a word. he is somewhere else.", "OH NO" },
	{ "MARBLES!", "you dropped these. all of them. everywhere.", "PICK UP" },
	{ "RATE THIS DEATH", "how likely are you to recommend being shot to a friend?", "TEN" },
	{ "FREE HAT", "the hat is free. the head costs extra.", "BUY HEAD" },
}
local SURE = { "ARE YOU SURE?", "closing ads hurts the ad's feelings.", "I'M SORRY" }
local BARS = { Color3.fromRGB(206, 112, 150), Color3.fromRGB(96, 168, 196), Color3.fromRGB(214, 180, 90), Color3.fromRGB(120, 176, 120) }
local SPOTS = { Vector2.new(0.5, 0.46), Vector2.new(0.26, 0.3), Vector2.new(0.74, 0.32), Vector2.new(0.3, 0.68), Vector2.new(0.72, 0.66) }
type Ad = { slot: number, frame: Frame, sure: boolean }
local ads = { live = {} :: { Ad }, queue = {} :: { number }, untilT = 0, sure = 0, qT = 0, n = 0, deck = {} :: { number } }
local adTip: TextLabel? = nil
local function adKeys()
	local ks = {}
	for _, a in ads.live do table.insert(ks, a.slot) end
	setBusy("ads", if #ks > 0 then ks else nil)
end
local function nextCopy(): { string }
	if #ads.deck == 0 then for i = 1, #COPY do table.insert(ads.deck, math.random(1, #ads.deck + 1), i) end end
	return COPY[table.remove(ads.deck) :: number]
end
local function adOpen(slot: number, copy: { string }, isSure: boolean)
	for _, a in ads.live do if a.slot == slot then return end end
	ads.n += 1
	local at = SPOTS[slot]
	local f = T.new("Frame", { Name = "Ad", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(at.X + (math.random() - 0.5) * 0.05, at.Y + (math.random() - 0.5) * 0.05),
		Size = UDim2.fromOffset(300, 136), BackgroundColor3 = T.BG, BackgroundTransparency = 0.04, BorderSizePixel = 0, ZIndex = 10 + ads.n, Rotation = (math.random() - 0.5) * 4 }, stage)
	T.corner(f, 6); T.edge(f, if isSure then T.DANGER else nil, if isSure then 0.2 else nil)
	f.InputBegan:Connect(function(io: InputObject) -- (a phone: tap an ad to close it, as its number key would)
		if io.UserInputType == Enum.UserInputType.Touch then
			local K = require(script.Parent:WaitForChild("Keys")) :: any
			K.tap(({ Enum.KeyCode.One, Enum.KeyCode.Two, Enum.KeyCode.Three, Enum.KeyCode.Four, Enum.KeyCode.Five })[slot])
		end
	end)
	local bar = T.new("Frame", { Name = "Bar", BackgroundColor3 = if isSure then T.DANGER else BARS[ads.n % #BARS + 1], BorderSizePixel = 0, Size = UDim2.new(1, 0, 0, 30), ZIndex = 10 + ads.n }, f)
	T.corner(bar, 6)
	local title = T.text(bar, "Title", copy[1], 14, T.INK, T.FONT_HEAVY); title.Position = UDim2.fromOffset(12, 0); title.Size = UDim2.new(1, -60, 1, 0); title.ZIndex = 11 + ads.n
	local key = T.key(bar, tostring(slot), UDim2.new(1, -30, 0, 4)); key.ZIndex = 11 + ads.n
	for _, d in key:GetDescendants() do if d:IsA("GuiObject") then d.ZIndex = 12 + ads.n end end
	local body = T.text(f, "Body", copy[2], 15, T.TEXT, T.FONT); body.Position = UDim2.fromOffset(14, 38); body.Size = UDim2.new(1, -28, 0, 48)
	body.TextWrapped = true; body.TextYAlignment = Enum.TextYAlignment.Top; body.ZIndex = 11 + ads.n
	local btn = T.text(f, "Button", copy[3], 13, T.INK, T.FONT_BOLD, Enum.TextXAlignment.Center); btn.BackgroundColor3 = T.ACCENT; btn.BackgroundTransparency = 0
	btn.Position = UDim2.fromOffset(14, 96); btn.Size = UDim2.fromOffset(130, 26); btn.ZIndex = 11 + ads.n; T.corner(btn, 4)
	local sc = T.new("UIScale", { Scale = 0.3 }, f)
	T.tween(sc, 0.14, { Scale = 1 }, Enum.EasingStyle.Back)
	table.insert(ads.live, { slot = slot, frame = f, sure = isSure })
	adKeys()
	Sfx.play(if isSure then "empty" else "click", nil, 0.8)
end
local function adShut(a: Ad, quiet: boolean?)
	local i = table.find(ads.live, a)
	if i then table.remove(ads.live, i) end
	local f = a.frame
	local sc = f:FindFirstChildOfClass("UIScale")
	if sc then T.tween(sc, 0.14, { Scale = 0.1 }, Enum.EasingStyle.Quad, Enum.EasingDirection.In) end
	task.delay(0.16, function() f:Destroy() end)
	adKeys()
	if not quiet then Sfx.play("click") end
end
local function adsReset()
	for _, a in table.clone(ads.live) do adShut(a, true) end
	table.clear(ads.queue); ads.untilT = 0; ads.sure = 0
	if adTip then adTip.Visible = false end
	setBusy("ads", nil)
end
local function onAds(m: any)
	adsReset()
	local n = math.clamp(math.floor(tonumber(m.n) or Items.ADS.n), 1, #SPOTS)
	local dur = math.clamp(tonumber(m.dur) or Items.ADS.dur, 1, 20)
	ads.untilT = os.clock() + dur
	ads.sure = math.clamp(math.floor(tonumber(m.sure) or 0), 0, 4)
	for i = 1, n do table.insert(ads.queue, math.random(1, #ads.queue + 1), i) end
	ads.qT = 0
	Hud.callout(if m.by == me.UserId then "YOUR OWN ADS" else "YOU HAVE BEEN ADVERTISED TO", 1.6)
	if not adTip then
		adTip = T.text(stage, "AdTip", "", 15, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Center)
		local tip = adTip :: TextLabel
		tip.AnchorPoint = Vector2.new(0.5, 0); tip.Position = UDim2.new(0.5, 0, 0, 64); tip.Size = UDim2.fromOffset(0, 30)
		tip.AutomaticSize = Enum.AutomaticSize.X; tip.BackgroundColor3 = T.BG; tip.BackgroundTransparency = 0.1; tip.ZIndex = 500
		T.corner(tip, 4); T.new("UIPadding", { PaddingLeft = UDim.new(0, 12), PaddingRight = UDim.new(0, 12) }, tip)
	end
end
local function adsStep(dt: number)
	if ads.untilT == 0 then return end
	local _, _, root = myChar()
	if os.clock() >= ads.untilT or not root then adsReset(); return end -- (time's up, or you died: the ads let you go)
	if #ads.queue > 0 then
		ads.qT -= dt
		if ads.qT <= 0 then ads.qT = 0.16; adOpen(table.remove(ads.queue, 1) :: number, nextCopy(), false) end
	end
	local tip = adTip
	if tip then
		tip.Visible = true
		tip.Text = (if (require(script.Parent:WaitForChild("Keys")) :: any).isTouch() then "tap an ad to close it  ·  %d left" else "press the number on an ad to close it  ·  %d left"):format(#ads.live + #ads.queue)
	end
end
;(require(script.Parent:WaitForChild("Keys")) :: any).began(function(io: InputObject, gp: boolean) -- (a phone: tapping an ad presses its number)
	local k = NUM[io.KeyCode]
	if not k or gp or #ads.live == 0 then return end
	for _, a in ads.live do
		if a.slot == k then
			adShut(a)
			if not a.sure and ads.sure > 0 and math.random() < 0.45 then
				ads.sure -= 1
				task.delay(0.26, function() if os.clock() < ads.untilT then adOpen(k, SURE, true) end end)
			end
			return
		end
	end
end)

-- ---------------------------------------------------------------- the night vision goggles (web public/js/goggles.js)
-- G flips them down or up (free); with them on the dark goes green and everyone you can see gets a glowing outline
-- (Roblox draws at most 31 outlines: the nearest; they don't show through walls); N or the middle button flashes
-- (a charge). a flash on you: white, then fading, longer the more you looked at it (twice as long in goggles)
local nvLook = Instance.new("ColorCorrectionEffect")
nvLook.Name = "JankNightVision"; nvLook.Enabled = false; nvLook.Parent = game:GetService("Lighting")
local nvK, nvLastT = 0, -math.huge
local glows: { [Instance]: Highlight } = {}
toggleGoggles = function()
	local t = os.clock()
	if t - nvLastT < Items.NVG.toggle then return end
	nvLastT = t
	local on = not (me:GetAttribute("NV") == true)
	ItemR:FireServer("nv", on)
	startHand(if on then "goggles" else "gogglesOff")
	Sfx.play("click", nil, if on then 1 else 0.8, if on then 1.2 else 0.9)
end
local function glowsClear()
	for m, h in glows do h:Destroy(); glows[m] = nil end
end
local function nvStep(dt: number)
	local on = me:GetAttribute("NV") == true and not thirdPerson()
	nvK = math.clamp(nvK + (if on then dt else -dt) / 0.3, 0, 1) -- (they flip down over 0.3 s)
	nvLook.Enabled = nvK > 0.01
	if nvLook.Enabled then
		nvLook.TintColor = Color3.new(1, 1, 1):Lerp(Color3.fromRGB(150, 255, 170), nvK)
		nvLook.Brightness = 0.18 * nvK
		nvLook.Contrast = 0.12 * nvK
		nvLook.Saturation = -0.7 * nvK
	end
	if not on then if next(glows) then glowsClear() end return end
	-- the outlines: everyone else (players and dummies), nearest first, at most 31
	local cam = camera.CFrame.Position
	local list = {}
	for _, pl in Players:GetPlayers() do
		if pl ~= me and pl.Character then table.insert(list, pl.Character) end
	end
	local dummies = workspace:FindFirstChild("Dummies")
	if dummies then for _, m in dummies:GetChildren() do if m:IsA("Model") then table.insert(list, m) end end end
	local dist: { [Instance]: number } = {}
	for _, m in list do
		local r = m:FindFirstChild("HumanoidRootPart") :: BasePart?
		dist[m] = if r then (r.Position - cam).Magnitude else math.huge
	end
	table.sort(list, function(a, b) return dist[a] < dist[b] end)
	local keep: { [Instance]: boolean } = {}
	for i = 1, math.min(31, #list) do
		local m = list[i]
		if dist[m] > 600 then break end
		keep[m] = true
		if not glows[m] then
			local h = Instance.new("Highlight")
			h.Adornee = m; h.FillTransparency = 1; h.OutlineColor = Color3.fromRGB(190, 255, 200); h.OutlineTransparency = 0.1
			h.DepthMode = Enum.HighlightDepthMode.Occluded
			h.Parent = folder
			glows[m] = h
		end
	end
	for m, h in glows do if not keep[m] then h:Destroy(); glows[m] = nil end end
end
-- goggles on everyone's head who wears them (web: lenses green)
local headGoggles: { [Player]: Model } = {}
local function headStep()
	for _, pl in Players:GetPlayers() do
		local on = pl:GetAttribute("NV") == true and pl.Character ~= nil
		local g = headGoggles[pl]
		local head = pl.Character and pl.Character:FindFirstChild("Head") :: BasePart?
		if on and head and not (pl == me and not thirdPerson()) then
			if not g then g = itemModel("nvg", pl); g:ScaleTo(1.25); g.Parent = folder; headGoggles[pl] = g end
			local gm = g :: Model
			gm:PivotTo(head.CFrame * CFrame.new(0, 0.15, -0.55))
		elseif g then g:Destroy(); headGoggles[pl] = nil end
	end
	for pl, g in headGoggles do if not pl.Parent then g:Destroy(); headGoggles[pl] = nil end end
end
-- the flash: N or the middle mouse button, goggles on
UserInputService.InputBegan:Connect(function(io: InputObject, gp: boolean)
	if gp or not require(script.Parent:WaitForChild("Binds")).is("flash", io) then return end -- (N / the middle button, or the player's own)
	if me:GetAttribute("Item") ~= "nvg" or me:GetAttribute("NV") ~= true or menuOpen() or inHub() then return end
	if me:GetAttribute("RoundLock") == true then Sfx.play("empty", nil, 0.5); return end -- (before GO: the flash waits too)
	local _, _, root = myChar()
	if not root then return end
	local n = charges()
	if n <= 0 then Sfx.play("empty"); Hud.callout("night vision goggles: recharging", 0.8); return end
	pend = { n = n - 1, t = os.clock() }
	local eye = if thirdPerson() then root.Position + Vector3.new(0, Hitbox.EYE_UP - Hitbox.ROOT_UP, 0) else camera.CFrame.Position
	ItemR:FireServer("nvg", eye, camera.CFrame.LookVector)
end)
local whiteout = T.new("Frame", { Name = "Flashed", BackgroundColor3 = Color3.new(1, 1, 1), BackgroundTransparency = 1, BorderSizePixel = 0,
	Size = UDim2.fromScale(1, 1), ZIndex = 1000 }, overlay)
local after = Instance.new("BlurEffect"); after.Name = "JankFlashed"; after.Size = 0; after.Enabled = false; after.Parent = game:GetService("Lighting")
whiteFlash = function(a: number, secs: number)
	whiteout.BackgroundTransparency = 1 - a
	T.tween(whiteout, secs, { BackgroundTransparency = 1 }, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
end
local function onFlashed(m: any)
	local secs = math.clamp(tonumber(m.s) or 1, 0.1, 8)
	whiteout.BackgroundTransparency = 0
	after.Enabled = true; after.Size = 24
	task.delay(secs * 0.4, function()
		T.tween(whiteout, secs * 0.6, { BackgroundTransparency = 1 }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
	end)
	T.tween(after, math.max(1.3, secs), { Size = 0 })
	task.delay(math.max(1.3, secs) + 0.05, function() if after.Size < 0.5 then after.Enabled = false end end)
	local by = if type(m.by) == "number" then Players:GetPlayerByUserId(m.by) else nil
	Hud.callout(if m.nv then "MY EYES! (THE GOGGLES MADE IT WORSE)" elseif by then "FLASHED BY " .. string.upper(by.DisplayName) else "FLASHED", 1.4)
	shake = math.max(shake, 0.35)
end
local function nvflashFx(m: any)
	if typeof(m.p) ~= "Vector3" then return end
	local at = m.p + (if typeof(m.d) == "Vector3" then m.d * 1.5 else Vector3.zero)
	local b = part(Enum.PartType.Ball, Vector3.one, Color3.fromRGB(220, 255, 225), Enum.Material.Neon)
	b.CFrame = CFrame.new(at); b.Parent = folder
	task.spawn(function()
		local t0 = os.clock()
		while b.Parent do
			local u = (os.clock() - t0) / 0.35
			if u >= 1 then break end
			b.Size = Vector3.one * (1 + 9 * S * u) -- (web: grows to 9 m over 0.35 s)
			b.Transparency = 0.3 + 0.7 * u
			RunService.RenderStepped:Wait()
		end
		b:Destroy()
	end)
	Sfx.play("pop", at, 1.2)
end

-- ---------------------------------------------------------------- the pop quiz (web public/js/quiz.js)
-- everyone sees a big calculator hovering in front of the one sitting it, the question on its screen and a sign over
-- their head; the one sitting it gets the paper: the question, four answers on keys 1-4 (or a click), the clock.
-- the right answer never comes from the server until it's over
type Exam = { model: Instance?, calc: Model?, sign: BillboardGui?, untilT: number, mine: boolean, paper: Frame?, picked: boolean, at: Vector3? }
local exams: { [string]: Exam } = {}
local function keyOf(m: any): string return if type(m.o) == "number" then "p" .. m.o elseif typeof(m.model) == "Instance" then "m" .. m.model:GetFullName() else "?" end
local function examClose(k: string)
	local e = exams[k]
	if not e then return end
	exams[k] = nil
	if e.calc then e.calc:Destroy() end
	if e.sign then e.sign:Destroy() end
	if e.paper then e.paper:Destroy() end
	if e.mine then setBusy("quiz", nil) end
end
local function answer(i: number)
	local e = exams["p" .. me.UserId]
	if not e or e.picked or os.clock() > e.untilT + 0.15 then return end
	e.picked = true
	ItemR:FireServer("ans", i)
	if e.paper then
		local b = e.paper:FindFirstChild("A" .. i) :: TextButton?
		if b then b.BackgroundColor3 = T.CARD_HI end
	end
	Sfx.play("click")
end
local function onQuiz(m: any)
	local k = keyOf(m)
	examClose(k)
	local model = if typeof(m.model) == "Instance" then m.model else nil
	local mine = m.o == me.UserId
	local left = math.clamp(tonumber(m.left) or Items.QUIZ.time, 0, 10)
	local e: Exam = { model = model, untilT = os.clock() + left, mine = mine, picked = false, at = if typeof(m.at) == "Vector3" then m.at else nil }
	-- the calculator, 4.6 x, in front of their face, the question on its screen
	local calc = itemModel("calc"); calc:ScaleTo(4.6); calc.Parent = folder
	local scr = calc:FindFirstChild("screen", true) :: BasePart?
	if scr then
		local sg = Instance.new("SurfaceGui"); sg.Face = Enum.NormalId.Front; sg.LightInfluence = 0; sg.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; sg.PixelsPerStud = 60
		local tl = T.text(sg, "Q", tostring(m.q) .. " = ?", 40, Color3.fromRGB(22, 34, 22), T.FONT_HEAVY, Enum.TextXAlignment.Center)
		tl.Size = UDim2.fromScale(1, 1); tl.TextScaled = true
		sg.Parent = scr
	end
	-- (its face, screen and keys, looks at the one sitting it; everyone else sees its back: the question goes there too)
	local body = calc:FindFirstChild("body", true) :: BasePart?
	if body then
		local sb = Instance.new("SurfaceGui"); sb.Face = Enum.NormalId.Back; sb.LightInfluence = 0; sb.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; sb.PixelsPerStud = 60
		local lcd = T.new("Frame", { Name = "Lcd", BackgroundColor3 = Color3.fromHex("9fb59a"), BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0),
			Position = UDim2.fromScale(0.5, 0.18), Size = UDim2.fromScale(0.8, 0.22) }, sb)
		T.corner(lcd, 6)
		local tb = T.text(lcd, "Q", tostring(m.q) .. " = ?", 40, Color3.fromRGB(22, 34, 22), T.FONT_HEAVY, Enum.TextXAlignment.Center)
		tb.Size = UDim2.fromScale(1, 1); tb.TextScaled = true
		sb.Parent = body
	end
	e.calc = calc
	-- the sign over their head
	local head = model and model:FindFirstChild("Head") :: BasePart?
	if head then
		local bb = Instance.new("BillboardGui"); bb.Size = UDim2.fromOffset(220, 58); bb.StudsOffset = Vector3.new(0, 4.2, 0); bb.AlwaysOnTop = false; bb.LightInfluence = 0
		bb.Adornee = head; bb.Parent = folder
		local plate = T.new("Frame", { BackgroundColor3 = T.BG, BackgroundTransparency = 0.1, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1) }, bb)
		T.corner(plate, 6)
		local l1 = T.text(plate, "Title", "POP QUIZ", 14, T.ACCENT, T.FONT_HEAVY, Enum.TextXAlignment.Center); l1.Size = UDim2.new(1, 0, 0, 26)
		local l2 = T.text(plate, "Q", tostring(m.q) .. " = ?", 18, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Center); l2.Position = UDim2.fromOffset(0, 24); l2.Size = UDim2.new(1, 0, 0, 30)
		e.sign = bb
	end
	if mine then
		-- the paper: the question big, four answers on 1-4, the clock running down
		local paper = T.plate(stage, "Exam", UDim2.new(0.5, -230, 0.5, 70), UDim2.fromOffset(460, 200))
		paper.ZIndex = 300
		local t1 = T.text(paper, "Title", "POP QUIZ  ·  pens up", 14, T.ACCENT, T.FONT_HEAVY); t1.Position = UDim2.fromOffset(18, 10); t1.Size = UDim2.new(1, -36, 0, 20); t1.ZIndex = 301
		local q = T.text(paper, "Question", tostring(m.q) .. " = ?", 32, T.TEXT, T.FONT_HEAVY); q.Position = UDim2.fromOffset(18, 34); q.Size = UDim2.new(1, -120, 0, 42); q.ZIndex = 301
		local clock = T.text(paper, "Clock", "", 28, T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Right); clock.Position = UDim2.new(1, -110, 0, 34); clock.Size = UDim2.fromOffset(92, 42); clock.ZIndex = 301
		for i = 0, 3 do
			local b = T.new("TextButton", { Name = "A" .. i, Text = "", AutoButtonColor = false, BackgroundColor3 = T.CARD, BorderSizePixel = 0,
				Position = UDim2.fromOffset(18 + i * 106, 92), Size = UDim2.fromOffset(98, 88), ZIndex = 301 }, paper)
			T.corner(b, 6); T.edge(b)
			local kk = T.key(b, tostring(i + 1), UDim2.fromOffset(8, 8)); kk.ZIndex = 302
			for _, d in kk:GetDescendants() do if d:IsA("GuiObject") then d.ZIndex = 303 end end
			local v = T.text(b, "Value", tostring((m.a or {})[i + 1] or "?"), 28, T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Center)
			v.Position = UDim2.fromOffset(0, 30); v.Size = UDim2.new(1, 0, 0, 48); v.ZIndex = 302
			b.MouseButton1Click:Connect(function() answer(i) end)
		end
		e.paper = paper
		setBusy("quiz", { 1, 2, 3, 4 })
		Hud.callout("POP QUIZ!", 1.0)
		-- (sitting it: off your rope)
		local st = Body.st
		if st and st.hook then st.hook = nil; GrappleR:FireServer("release") end
	else
		local by = if type(m.by) == "number" then Players:GetPlayerByUserId(m.by) else nil
		if by == me then Hud.callout("POP QUIZ FOR " .. string.upper(if model then model.Name else "THEM"), 1.2) end
	end
	exams[k] = e
end
local function onQuizEnd(m: any)
	local k = keyOf(m)
	local e = exams[k]
	local mine = m.o == me.UserId
	if e and e.paper and type(m.c) == "number" then
		-- the right one goes green, a wrong pick red, for a moment before it all goes
		local good = e.paper:FindFirstChild("A" .. m.c) :: TextButton?
		if good then good.BackgroundColor3 = Color3.fromRGB(64, 120, 78) end
		if type(m.i) == "number" and m.i >= 0 and m.i ~= m.c then
			local bad = e.paper:FindFirstChild("A" .. m.i) :: TextButton?
			if bad then bad.BackgroundColor3 = Color3.fromRGB(140, 52, 50) end
		end
	end
	local model = if e then e.model elseif typeof(m.model) == "Instance" then m.model else nil
	local root = model and model:FindFirstChild("HumanoidRootPart") :: BasePart?
	if m.ok then
		if root then
			emitter(host(root.Position + Vector3.new(0, 2, 0), 2), { Texture = TEX.blob, LightEmission = 0.8, LightInfluence = 0.2, Brightness = 2,
				Color = cs(Color3.fromRGB(255, 226, 120), Color3.fromRGB(230, 180, 60)), Size = ns(0, 0.2 * S, 1, 0), Lifetime = NR(0.5, 0.9),
				Speed = NR(3 * S, 7 * S), SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, -8 * S, 0) }):Emit(40)
		end
		if mine then Hud.callout("GOLD STAR!  NOTHING CAN HURT YOU", 1.6) end
	elseif mine and not m.gone then
		Hud.callout(if m.i == -1 then "PENS DOWN. TOO SLOW." else "WRONG.", 1.4)
	end
	task.delay(if mine then 0.9 else 0, function() examClose(k) end)
end
local function examStep()
	local t = os.clock()
	for k, e in exams do
		local r = e.model and e.model:FindFirstChild("HumanoidRootPart") :: BasePart?
		if e.calc and r then
			-- hovering in front of their face, bobbing, swaying (1.7 m out for your own, so you can read it)
			local dist = (if e.mine then 1.7 else 1.05) * S
			local cf = r.CFrame * CFrame.new(0, 1.9 + math.sin(t * 3) * 0.15, -dist) * CFrame.Angles(0, math.pi + math.sin(t * 1.3) * 0.1, 0)
			e.calc:PivotTo(cf)
		end
		if e.paper then
			local clock = e.paper:FindFirstChild("Clock") :: TextLabel?
			if clock then
				local left = math.max(0, e.untilT - t)
				clock.Text = ("%.1f"):format(left)
				clock.TextColor3 = if left < 2 then T.DANGER else T.TEXT
			end
		end
		if t > e.untilT + 3 then examClose(k) end -- (a lost end message: don't leave it hanging)
	end
end
UserInputService.InputBegan:Connect(function(io: InputObject, gp: boolean)
	local k = NUM[io.KeyCode]
	if gp or not k or k > 4 or not exams["p" .. me.UserId] then return end
	answer(k - 1)
end)
-- sitting a quiz: you stay where it got you; the gold star: x1.25 run speed for 4 s
local prevStep = Body.onStep
Body.onStep = function(st: any, chest: Vector3, dt: number)
	if prevStep then prevStep(st, chest, dt) end
	if me:GetAttribute("Quiz") then st.vx, st.vz = 0, 0; if st.vy > 0 then st.vy = 0 end end
end
local function boostStep()
	local fu = tonumber(me:GetAttribute("FastUntil")) or 0
	Body.boost = if workspace:GetServerTimeNow() < fu then Items.QUIZ.fast else 1
end

-- ---------------------------------------------------------------- the speed trap (web public/js/secondaries.js)
-- hold G: the radar gun comes up in your hand and reads whoever is under your crosshair every 0.15 s (the server
-- measures their speed from its own record of where they've been). the numbers float over their heads; over 100
-- km/h they get 3 s to slow down, over Items.SPEED.jail (140) the cage drops on them
local radarOn = false
local radarNext = 0
local lastReading = ""
local function aimedAt(): Instance?
	-- the one nearest your crosshair, inside a small cone (the server makes up its own mind with lag slack)
	local cf = camera.CFrame
	local best, bd = nil, math.cos(0.1 + 0.06)
	local function try(m: Instance)
		local r = m:FindFirstChild("HumanoidRootPart") :: BasePart?
		if not r then return end
		local to = r.Position - cf.Position
		local dist = to.Magnitude
		if dist < 1 or dist > Items.SPEED.range + 12 then return end
		local dot = to.Unit:Dot(cf.LookVector)
		if dot > bd then best, bd = m, dot end
	end
	for _, pl in Players:GetPlayers() do if pl ~= me and pl.Character then try(pl.Character) end end
	local dummies = workspace:FindFirstChild("Dummies")
	if dummies then for _, m in dummies:GetChildren() do try(m) end end
	return best
end
radarHold = function(on: boolean)
	if on == radarOn then return end
	radarOn = on
	if on then
		startHand("radar")
		radarNext = 0
	else
		ItemR:FireServer("radar", "off")
		if hand and hand.id == "radar" then startHand("radarDown") end
	end
end
;(require(script.Parent:WaitForChild("Keys")) :: any).ended(function(io: InputObject)
	if radarOn and require(script.Parent:WaitForChild("Binds")).is("item", io) then radarHold(false) end
	if X.cooking() and require(script.Parent:WaitForChild("Binds")).is("item", io) then X.cookRelease() end -- (a cooked grenade goes)
end)
local function radarStep()
	if not radarOn then return end
	if me:GetAttribute("Item") ~= "radar" or not myChar() or menuOpen() or inHub() then radarHold(false); return end
	local t = os.clock()
	if t >= radarNext then
		radarNext = t + Items.SPEED.scan
		ItemR:FireServer("radar", camera.CFrame.LookVector, aimedAt())
	end
	-- the readout on the gun
	local h = hand
	local scr = h and h.id == "radar" and h.model:FindFirstChild("screen", true) :: BasePart?
	if scr then
		local sg = scr:FindFirstChildOfClass("SurfaceGui")
		if not sg then
			sg = Instance.new("SurfaceGui"); sg.Face = Enum.NormalId.Back; sg.LightInfluence = 0
			sg.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; sg.PixelsPerStud = 200; sg.Parent = scr
			local tl = T.text(sg, "Read", "", 40, Color3.fromRGB(150, 230, 255), T.FONT_HEAVY, Enum.TextXAlignment.Center); tl.Size = UDim2.fromScale(1, 1); tl.TextScaled = true
		end
		local tl = (sg :: SurfaceGui):FindFirstChild("Read") :: TextLabel?
		if tl then tl.Text = if lastReading ~= "" then lastReading else "---" end
	end
end
-- the number over someone's head (each reading: 0.7 s), the ticket's countdown over theirs
local tags: { [Instance]: { gui: BillboardGui, label: TextLabel, untilT: number, ticket: number? } } = {}
local function tagOn(model: Instance?): any
	local head = model and model:FindFirstChild("Head") :: BasePart?
	if not head or not model then return nil end
	local t = tags[model]
	if not t then
		local bb = Instance.new("BillboardGui"); bb.Size = UDim2.fromOffset(200, 40); bb.StudsOffset = Vector3.new(0, 3.2, 0); bb.LightInfluence = 0; bb.AlwaysOnTop = true
		bb.Adornee = head; bb.Parent = folder
		local l = T.text(bb, "Read", "", 22, T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Center, true); l.Size = UDim2.fromScale(1, 1)
		t = { gui = bb, label = l, untilT = 0, ticket = nil }
		tags[model] = t
	end
	return t
end
local function tagStep()
	local n = os.clock()
	for m, t in tags do
		if t.ticket and n < t.ticket then
			local left = t.ticket - n
			t.label.Text = ("SLOW DOWN!  %.1f"):format(left)
			t.label.TextColor3 = if math.floor(n * 6) % 2 == 0 then Color3.fromRGB(235, 77, 75) else Color3.fromRGB(96, 150, 255)
		elseif n < t.untilT then
			-- (the reading)
		else
			t.gui:Destroy(); tags[m] = nil
		end
	end
end
local cages: { [Instance]: { model: Model, at: Vector3, t0: number, up: number? } } = {}
local function cageStep()
	local n = os.clock()
	for key, c in cages do
		local dropT = n - c.t0
		-- drops 7 m in 0.22 s, a 0.18 m bounce until 0.36 s; on the way out it's hauled up (y += 30 u^2, 0.6 s)
		local y = if dropT < 0.22 then 7 * S * (1 - (dropT / 0.22) ^ 2) elseif dropT < 0.36 then 0.18 * S * math.sin((dropT - 0.22) / 0.14 * math.pi) else 0
		if c.up then
			local u = n - c.up
			if u > 0.6 then c.model:Destroy(); cages[key] = nil; continue end
			y = 30 * S * u * u
		end
		c.model:PivotTo(CFrame.new(c.at + Vector3.new(0, y, 0)))
	end
end
local function onRadarFx(m: any)
	local model = if typeof(m.to) == "Instance" then m.to else nil
	local v = tonumber(m.v) or 0
	local over = v > Items.SPEED.limit
	if m.o == me.UserId then
		lastReading = ("%d"):format(v)
		Sfx.play("click", nil, 0.5, if over then 1.6 else 1.2)
	end
	local t = tagOn(model)
	if t and not t.ticket then
		t.label.Text = ("%d km/h"):format(v)
		t.label.TextColor3 = if over then T.DANGER else T.TEXT
		t.untilT = os.clock() + 0.7
	end
end
local function onTicket(m: any)
	local model = if typeof(m.model) == "Instance" then m.model else nil
	local t = tagOn(model)
	if t then t.ticket = os.clock() + (tonumber(m.s) or Items.SPEED.warn) end
	if m.o == me.UserId then Hud.callout(("SLOW DOWN!  under %d km/h"):format(tonumber(m.lim) or Items.SPEED.limit), 2.0) end
	if m.by == me.UserId then Hud.callout(("TICKET · %d km/h"):format(tonumber(m.v) or 0), 1.0) end
end
local function onTicketEnd(m: any)
	local model = if typeof(m.model) == "Instance" then m.model else nil
	local t = model and tags[model]
	if t then t.ticket = nil; t.untilT = 0 end
	if m.o == me.UserId and m.ok then Hud.callout("WARNING · drive safe out there", 1.4) end
end
local function onJail(m: any)
	local model = if typeof(m.model) == "Instance" then m.model else nil
	if not model or typeof(m.p) ~= "Vector3" then return end
	local old = cages[model]
	if old then old.model:Destroy() end
	local cage = itemModel("cage"); cage.Parent = folder
	cages[model] = { model = cage, at = m.p, t0 = os.clock() }
	Sfx.play("thwack", m.p)
	shakeFrom(m.p, 0.8)
	if m.o == me.UserId then Hud.callout("PULLED OVER", 1.6)
	elseif m.by == me.UserId then Hud.callout(("BUSTED!  %d KM/H"):format(tonumber(m.v) or 0), 1.6) end
end
local function onJailEnd(m: any)
	local model = if typeof(m.model) == "Instance" then m.model else nil
	local c = model and cages[model]
	if c then c.up = os.clock() end
end
-- jailed: you stay in the cage
do
	local prev = Body.onStep
	Body.onStep = function(st: any, chest: Vector3, dt: number)
		if prev then prev(st, chest, dt) end
		if me:GetAttribute("Jail") then st.vx, st.vz = 0, 0; if st.vy > 0 then st.vy = 0 end; if st.hook then st.hook = nil; GrappleR:FireServer("release") end end
	end
end

-- ---------------------------------------------------------------- cooking a grenade (Items.COOK)
-- G down with the frag or the smoke bomb pulls the pin (the server starts the fuse on its own clock), G up throws it
-- with what's left. a ring of ticks round the crosshair drains while you hold it (warm in the last second, with four
-- ticks you hear); held to the end it goes off in your hand: the server says so ("cookx"). others hear the pin come out
-- and see it held up (ThirdPerson's "cook" pose); a quick tap throws it as it always did
do
local CK = Items.COOK
local cooking: { id: string, t0: number, total: number, ticks: number }? = nil
local N, RAD = 28, 22
local WARM = Color3.fromRGB(255, 176, 92)
local ring = T.new("Frame", { Name = "CookRing", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5),
	Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(2 * RAD + 10, 2 * RAD + 10), Visible = false, ZIndex = 5 }, overlay)
local ticks: { Frame } = {}
for i = 1, N do
	local a = (i - 1) / N * math.pi * 2
	local tk = T.new("Frame", { Name = "T" .. i, BorderSizePixel = 0, BackgroundColor3 = T.TEXT, AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.new(0.5, math.sin(a) * RAD, 0.5, -math.cos(a) * RAD), Size = UDim2.fromOffset(2, 6), Rotation = math.deg(a), ZIndex = 5 }, ring)
	T.corner(tk, 1)
	local sk = Instance.new("UIStroke"); sk.Color = Color3.new(0, 0, 0); sk.Transparency = 0.55; sk.Thickness = 1; sk.Parent = tk
	ticks[i] = tk
end
-- the pin and its ring on a grenade model (they're out once it's cooking or thrown)
local function pinParts(m: Instance): { BasePart }
	local out = {}
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") and (string.match(d.Name, "^pin") or string.match(d.Name, "^ring")) then table.insert(out, d) end
	end
	return out
end
X.pinParts = pinParts
X.cooks = function(id: string): boolean return CK.ids[id] == true and L[id] ~= nil and L[id].proj ~= nil end
X.cooking = function(): boolean return cooking ~= nil end
X.cookStart = function(id: string)
	local w = Items.PROJ[L[id].proj :: string]
	local ck = { id = id, t0 = os.clock(), total = CK.grace + w.fuse, ticks = 0 }
	cooking = ck
	ItemR:FireServer("cook", id)
	Sfx.play("pin")
	startHand(id, "cook")
	local h = hand
	if h and h.id == id then
		h.extra = { cook = true, out = false, pins = pinParts(h.model), lamp = h.model:FindFirstChild("lamp", true), t0 = ck.t0, total = ck.total }
	end
	handStep()
end
X.cookRelease = function()
	local ck = cooking
	if not ck then return end
	cooking = nil
	ring.Visible = false
	local _, _, root = myChar()
	if not root then return end
	local eye = if thirdPerson() then root.Position + Vector3.new(0, Hitbox.EYE_UP - Hitbox.ROOT_UP, 0) else camera.CFrame.Position
	ItemR:FireServer(ck.id, eye, camera.CFrame.LookVector)
	if os.clock() - ck.t0 < CK.grace then
		startHand(ck.id) -- (a tap: the throw as it always was)
	else
		startHand(ck.id, "cookThrow") -- (from where it was held up: the snap forward)
		local h = hand
		if h then h.extra = { cook = true, out = true, pins = pinParts(h.model) } end
	end
	handStep()
	Sfx.play("swing")
	if (Sfx :: any).skinItem then (Sfx :: any).skinItem(me, ck.id, "throw") end -- (a skin's own layer on the throw)
end
-- the hand holding it: the pin comes out at 0.13 s, the lamp on top blinks faster as the fuse runs down
X.cookHand = function(h: any, t: number)
	local e = h.extra
	if e.out or t >= 0.13 then for _, q in e.pins do q.Transparency = 1 end end
	local lamp = e.lamp
	if not e.out and lamp and lamp:IsA("BasePart") then
		local left = e.total - (os.clock() - e.t0)
		local hz = if left < 0.6 then 12 elseif left < 1.2 then 6 else 3
		lamp.Transparency = if t < 0.13 or math.floor(os.clock() * hz * 2) % 2 == 0 then 0 else 0.85
	end
end
-- the ring: drains clockwise from the top over the whole fuse; the last second warm, with a tick every quarter
X.cookStep = function()
	local ck = cooking
	if not ck then
		if ring.Visible then ring.Visible = false end
		return
	end
	local el = os.clock() - ck.t0
	local _, _, root = myChar()
	if not root or el > ck.total + 1.5 then cooking = nil; ring.Visible = false; return end -- (the server's "cookx" normally ends it first)
	local left = math.max(0, ck.total - el)
	ring.Visible = not menuOpen()
	local lit = math.ceil(left / ck.total * N)
	local col = if left < 1 then WARM else T.TEXT
	for i, tk in ticks do
		tk.BackgroundColor3 = col
		tk.BackgroundTransparency = if i > N - lit then 0 else 0.82
	end
	if left > 0 and left < 1 then
		local want = math.min(4, math.floor((1 - left) * 4) + 1)
		while ck.ticks < want do ck.ticks += 1; Sfx.play("fuse_tick") end
	end
end
-- the server: someone pulled a pin (you hear theirs where they stand); a cooked grenade is over (it went off in the
-- hand, was dropped by a death, went with you into the hub, or the server said no)
X.onCook = function(m: any)
	if m.o == me.UserId then return end
	local at = middleOf(if typeof(m.model) == "Instance" then m.model else nil)
	if at then Sfx.play("pin", at) end
end
X.onCookEnd = function(m: any)
	if m.o ~= me.UserId then return end
	cooking = nil
	ring.Visible = false
	if m.why == "no" then pend = nil end
	local h = hand
	if h and h.extra and h.extra.cook and not h.extra.out then dropHand() end
end
end

-- (what the rest of the script calls in the camera and wand blocks below: the main chunk has a 200 local limit)
-- ---------------------------------------------------------------- the instant camera (web public/js/photo.js)
do
-- nobody uploads a picture: the server says where a photo was taken (the spot, which way it looked) and every client
-- builds that view itself, a ViewportFrame of the map's parts round that spot. your photo shows on a card by your
-- item while you hold it, on the print as it comes out, and on the frame it prints into
local P = Items.PHOTO
local BROWN = Color3.new(0.23, 0.15, 0.1)
local WARM = Color3.new(1, 0.95, 0.87) -- (the instant-film look: a touch warm)
local mapParts: { BasePart } = {}
local mapT = -math.huge
local function mapList(): { BasePart }
	if os.clock() - mapT < 30 then return mapParts end
	mapT = os.clock()
	table.clear(mapParts)
	local map = workspace:FindFirstChild("Map")
	if map then for _, d in map:GetDescendants() do if d:IsA("BasePart") and d.Transparency < 0.95 then table.insert(mapParts, d) end end end
	return mapParts
end
local KEEP = { SpecialMesh = true, SurfaceAppearance = true, Decal = true, Texture = true }
type Photo = { folder: Folder, cam: Camera }
-- the map round the spot, as the photo saw it: the nearest 700 parts in front of it within 200 studs
local function photoOf(pos: Vector3, yaw: number, pitch: number): Photo
	local eye = pos + Vector3.new(0, Hitbox.EYE_UP, 0)
	local cf = CFrame.new(eye) * CFrame.fromOrientation(pitch, yaw, 0)
	local look = cf.LookVector
	local near: { { p: BasePart, d: number } } = {}
	for _, pt in mapList() do
		if not pt.Parent then continue end
		local h = pt.Size / 2
		local l = pt.CFrame:PointToObjectSpace(eye)
		local c = Vector3.new(math.clamp(l.X, -h.X, h.X), math.clamp(l.Y, -h.Y, h.Y), math.clamp(l.Z, -h.Z, h.Z))
		local d = (l - c).Magnitude
		if d > 200 then continue end
		if d > 12 then
			local w = pt.CFrame:PointToWorldSpace(c) - eye
			if w.Unit:Dot(look) < 0.3 then continue end
		end
		table.insert(near, { p = pt, d = d })
	end
	table.sort(near, function(a, b) return a.d < b.d end)
	local f = Instance.new("Folder")
	f.Name = "Photo"
	for i = 1, math.min(#near, 700) do
		local ok, cl = pcall(function() return near[i].p:Clone() end)
		if ok and cl then
			for _, d in cl:GetDescendants() do if not KEEP[d.ClassName] then d:Destroy() end end
			cl.Anchored = true
			cl.Parent = f
		end
	end
	local cam = Instance.new("Camera")
	cam.FieldOfView = 72
	cam.CFrame = cf
	return { folder = f, cam = cam }
end
local function viewport(parent: Instance): ViewportFrame
	local vf = Instance.new("ViewportFrame")
	vf.Name = "Photo"
	vf.Size = UDim2.fromScale(1, 1)
	vf.BorderSizePixel = 0
	vf.BackgroundColor3 = Color3.fromRGB(176, 190, 204) -- (the sky, where the map leaves a gap)
	vf.Ambient = Color3.fromRGB(150, 148, 144)
	vf.LightColor = Color3.fromRGB(235, 230, 220)
	vf.LightDirection = -game:GetService("Lighting"):GetSunDirection()
	vf.ImageColor3 = WARM
	vf.Parent = parent
	return vf
end
local function show(vf: ViewportFrame, ph: Photo)
	for _, c in vf:GetChildren() do if c:IsA("Folder") or c:IsA("Camera") then c:Destroy() end end
	ph.folder.Parent = vf
	ph.cam.Parent = vf
	vf.CurrentCamera = ph.cam
end
local function onSurface(pt: BasePart, face: Enum.NormalId): ViewportFrame
	local sg = Instance.new("SurfaceGui")
	sg.Name = "JankPhoto"
	sg.Face = face
	sg.SizingMode = Enum.SurfaceGuiSizingMode.FixedSize
	sg.CanvasSize = Vector2.new(256, 256)
	sg.LightInfluence = 0
	sg.ResetOnSpawn = false
	sg.Adornee = pt
	sg.Parent = me:WaitForChild("PlayerGui")
	pt.Destroying:Connect(function() sg:Destroy() end)
	return viewport(sg)
end

-- the photo you're holding: a small print by your item, tipped a little, "G · PRINT" on its margin
local thumb = T.new("Frame", { Name = "Photo", BackgroundColor3 = Color3.fromHex("ecebe4"), BorderSizePixel = 0, Visible = false,
	AnchorPoint = Vector2.new(1, 1), Position = UDim2.new(1, -200, 1, -150), Size = UDim2.fromOffset(104, 126), Rotation = -4 }, hud)
T.corner(thumb, 3)
T.new("UIStroke", { Color = Color3.fromHex("26282d"), Thickness = 2, Transparency = 0.3 }, thumb)
local thumbBox = T.new("Frame", { Name = "Pic", BackgroundTransparency = 1, Position = UDim2.fromOffset(7, 7), Size = UDim2.fromOffset(90, 90), ClipsDescendants = true }, thumb)
local thumbVf = viewport(thumbBox)
local thumbL = T.text(thumb, "Print", "G · PRINT", 13, Color3.fromHex("26282d"), T.FONT_BOLD, Enum.TextXAlignment.Center)
thumbL.Position = UDim2.fromOffset(0, 100); thumbL.Size = UDim2.new(1, 0, 0, 20)
local held: Photo? = nil
local function thumbStep()
	thumb.Visible = me:GetAttribute("Photo") == true and me:GetAttribute("Item") == "camera" and not inHub() and not menuOpen() and myChar() ~= nil
	if thumb.Visible then
		local n, at = charges()
		local left = math.ceil(at - workspace:GetServerTimeNow())
		thumbL.Text = if n > 0 or left <= 0 then "G · PRINT" else ("G · PRINT IN %d S"):format(left)
	end
end

-- the snap: at 0.3 s into the clip the shutter goes, a white flash over the screen, the camera's flash window lights
local snapT = -math.huge
snapAt = function(t: number) snapT = t end
local function camStep()
	local t = os.clock() - snapT
	if t >= 0.3 and snapT > 0 then
		snapT = -math.huge
		Sfx.play("shutter")
		whiteFlash(0.85, 0.22)
		shake = math.max(shake, 0.15)
		local h = hand
		local fl = h and h.id == "snap" and h.model:FindFirstChild("flash", true) :: BasePart?
		if fl then
			local c, mt = fl.Color, fl.Material
			fl.Color = Color3.new(1, 1, 1); fl.Material = Enum.Material.Neon
			task.delay(0.1, function() if fl.Parent then fl.Color = c; fl.Material = mt end end)
		end
	end
end

-- the print: a white card slides out of the slot under the lens toward you (the camera is turned round), your photo
-- on it developing up from brown, then the whole thing is flicked forward and becomes the frame
printIn = function()
	local h = hand
	if not h or h.id ~= "print" then return end
	local k = h.model:GetScale() * S
	local card = part(Enum.PartType.Block, Vector3.new(0.086, 0.002, 0.104) * k, Color3.fromHex("ecebe4"))
	card.Name = "printcard"; card.Parent = h.model
	local pic = part(Enum.PartType.Block, Vector3.new(0.076, 0.001, 0.076) * k, Color3.fromHex("2c2824"))
	pic.Name = "printpic"; pic.Parent = h.model
	local vf = onSurface(pic, Enum.NormalId.Top)
	vf.ImageColor3 = BROWN
	if held then show(vf, held); held = nil end
	h.extra = { card = card, pic = pic, vf = vf, k = k }
	Sfx.play("whirr")
end
local function printStep(h: Hand, t: number)
	local e = h.extra
	local out = math.clamp((t - 0.2) / 0.55, 0, 1)
	local base = h.model:GetPivot() * CFrame.new(Vector3.new(0, -0.056, -0.046 - out * 0.09) * e.k)
	e.card.CFrame = base * CFrame.new(Vector3.new(0, 0, -0.052) * e.k)
	e.pic.CFrame = base * CFrame.new(Vector3.new(0, 0.0015, -0.058) * e.k) * CFrame.Angles(0, math.pi, 0)
	local show = t > 0.18 and not h.gone
	for _, pt in { e.card, e.pic } do pt.Transparency = if show then 0 else 1 end
	local dev = math.clamp((t - 0.3) / 0.8, 0, 1)
	e.vf.ImageColor3 = BROWN:Lerp(WARM, dev)
	if t >= 0.82 and not e.flick then e.flick = true; Sfx.play("swing") end
end

-- the frames standing in the world
type Frame = { id: number, o: number?, model: Model, at: CFrame, born: number, untilT: number, vf: ViewportFrame?, grown: boolean,
	parts: { { p: BasePart, rel: CFrame, size: Vector3 } } }
local frames: { [number]: Frame } = {}
local function sparkle(at: Vector3, n: number, speed: number)
	emitter(host(at, 1.5), { Texture = TEX.blob, LightEmission = 0.8, LightInfluence = 0.2,
		Color = cs(Color3.fromRGB(250, 250, 246), Color3.fromRGB(196, 222, 232)), Size = ns(0, 0.12 * S, 1, 0),
		Lifetime = NR(0.35, 0.7), Speed = NR(speed * 0.4, speed), SpreadAngle = Vector2.new(180, 180), Drag = 3 }):Emit(n)
end
local function dropFrame(id: any, quiet: boolean)
	local F = if type(id) == "number" then frames[id] else nil
	if not F then return end
	frames[id] = nil
	if not quiet then
		local at = F.at.Position + Vector3.new(0, 1.2 * S, 0)
		sparkle(at, 40, 7 * S)
		Sfx.play("framepop", at)
	end
	F.model:Destroy()
end
local function onFrame(m: any)
	if type(m.id) ~= "number" or typeof(m.p) ~= "Vector3" or type(m.ph) ~= "table" or typeof(m.ph.p) ~= "Vector3" then return end
	dropFrame(m.id, true)
	local model = itemModel("photoframe")
	local at = CFrame.new(m.p) * CFrame.Angles(0, tonumber(m.y) or 0, 0)
	-- (each part's place and size against the frame's foot: it grows by setting them, never ScaleTo)
	-- (the template's parts sit round its own origin, the floor under its middle: each one's CFrame is its place against
	-- the frame's foot. its PrimaryPart pivot is not that point, so it is never moved by PivotTo)
	local parts = {}
	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") then table.insert(parts, { p = d, rel = d.CFrame, size = d.Size }); d.CFrame = at * d.CFrame end
	end
	model.Parent = folder
	local pic = model:FindFirstChild("pic", true) :: BasePart?
	local vf = nil
	if pic then
		vf = onSurface(pic, Enum.NormalId.Front)
		show(vf, photoOf(m.ph.p, tonumber(m.ph.y) or 0, tonumber(m.ph.x) or 0))
		vf.ImageColor3 = BROWN
	end
	local fresh = m.fresh ~= false
	local F: Frame = { id = m.id, o = if type(m.o) == "number" then m.o else nil, model = model, at = at,
		born = if fresh then os.clock() else os.clock() - 5, untilT = os.clock() + (tonumber(m.left) or P.life), vf = vf, grown = false, parts = parts }
	frames[m.id] = F
	if F.o == me.UserId then held = nil end
	if fresh then
		Sfx.play("framepop", m.p)
		if F.o ~= me.UserId then Sfx.play("whirr", m.p) end
		sparkle(m.p + Vector3.new(0, 1.2 * S, 0), 30, 6 * S)
	end
end
local function frameStep()
	local n = os.clock()
	for id, F in frames do
		if n > F.untilT + 1.5 then dropFrame(id, true); continue end
		local age, left = n - F.born, F.untilT - n
		-- pops up out of the floor with an overshoot and a wobble, develops from brown over 1.6 s, flickers in its last 3 s
		if not F.grown then
			local x = math.min(1, age / 0.45) - 1
			local k = math.max(0.02, 1 + 2.70158 * x * x * x + 1.70158 * x * x)
			local wob = math.sin(age * 9) * 0.06 * math.exp(-age * 2.5)
			local base = F.at * CFrame.Angles(0, 0, wob)
			for _, e in F.parts do
				e.p.Size = e.size * k
				e.p.CFrame = base * CFrame.new(e.rel.Position * k) * e.rel.Rotation
			end
			if age >= 1.6 then -- (the wobble has died down: put it exactly where it stands)
				F.grown = true
				for _, e in F.parts do e.p.Size = e.size; e.p.CFrame = F.at * e.rel end
			end
		end
		local vf = F.vf
		if vf then
			vf.ImageColor3 = BROWN:Lerp(WARM, math.clamp(age / 1.6, 0, 1))
			vf.ImageTransparency = if left < 3 and math.sin(n * (12 + (3 - left) * 10)) < 0 then 0.45 else 0
		end
	end
end
local function onSnap(m: any)
	if m.o == me.UserId then
		if typeof(m.p) == "Vector3" then
			held = photoOf(m.p, tonumber(m.y) or 0, tonumber(m.x) or 0)
			show(thumbVf, held)
		end
		local n, at = charges()
		local left = math.ceil(at - workspace:GetServerTimeNow())
		Hud.callout(if n > 0 or left <= 0 then "PHOTO TAKEN · G TO PRINT IT" else ("PHOTO TAKEN · PRINT READY IN %d S"):format(left), 1.6)
	else
		local model = if typeof(m.model) == "Instance" then m.model else nil
		local head = model and model:FindFirstChild("Head") :: BasePart?
		if head then
			Sfx.play("shutter", head.Position)
			local l = Instance.new("PointLight"); l.Brightness = 6; l.Range = 18; l.Color = Color3.new(1, 1, 1); l.Parent = head
			Debris:AddItem(l, 0.1)
		end
	end
end
-- you went through: there you are, facing the way the photo was taken
local function onPtp(m: any)
	local _, _, root = myChar()
	if not root or typeof(m.p) ~= "Vector3" then return end
	local yaw, pitch = tonumber(m.y) or 0, tonumber(m.x) or 0
	local to = m.p + Vector3.new(0, Hitbox.ROOT_UP, 0)
	root.AssemblyLinearVelocity = Vector3.zero
	root.CFrame = CFrame.new(to) * CFrame.Angles(0, yaw, 0)
	local st = Body.st :: any
	if st then
		st.vx, st.vy, st.vz = 0, 0, 0
		if st.hook then st.hook = nil; GrappleR:FireServer("release") end -- (a rope can't follow you through a photo)
	end
	camera.CFrame = CFrame.new(to + Vector3.new(0, Hitbox.EYE_UP - Hitbox.ROOT_UP, 0)) * CFrame.fromOrientation(pitch, yaw, 0)
	Sfx.play("photoin")
	whiteFlash(0.65, 0.35)
	shake = math.max(shake, 0.4)
	Hud.callout("WISH YOU WERE HERE", 1.3)
end
-- the show: someone went into a frame at a and came out at b
local function teleFx(m: any)
	local model = if typeof(m.model) == "Instance" then m.model else nil
	local isMe = model ~= nil and model == me.Character
	for i, at in { m.a, m.b } do
		if typeof(at) ~= "Vector3" then continue end
		sparkle(at, if i == 2 then 50 else 34, (if i == 2 then 9 else 6) * S)
		if not isMe then Sfx.play(if i == 1 then "photoout" else "photoin", at) end
	end
	local F = if type(m.f) == "number" then frames[m.f] else nil
	if F and F.o == me.UserId and not isMe then
		local who = model and Players:GetPlayerFromCharacter(model)
		Hud.callout((if who then string.upper(who.DisplayName) else "SOMEONE") .. " WENT IN YOUR PHOTO", 1.2)
	end
end
me:GetAttributeChangedSignal("Photo"):Connect(function() if not me:GetAttribute("Photo") and not (hand and hand.id == "print") then held = nil end end)
X.onSnap = onSnap
X.onFrame = onFrame
X.dropFrame = dropFrame
X.onPtp = onPtp
X.teleFx = teleFx
X.camStep = camStep
X.frameStep = frameStep
X.thumbStep = thumbStep
X.printStep = printStep
end

-- ---------------------------------------------------------------- the bubble wand (web public/js/wand.js)
do
-- the soap film in the ring bulges each time a bubble leaves it; bubbles fly on the shared formula (Items.soapAt); the
-- one sealed in floats in a giant bubble everyone sees, and sees the world through its film
local SW, WD = Items.SOAP, Items.WAND
local FILM = Color3.fromRGB(214, 236, 248)
local function soapBall(d: number): BasePart
	local b = part(Enum.PartType.Block, Vector3.one * d, FILM, Enum.Material.ForceField)
	local mesh = Instance.new("SpecialMesh"); mesh.MeshType = Enum.MeshType.Sphere; mesh.Parent = b
	return b
end
local SHEEN = { Color3.fromRGB(206, 232, 246), Color3.fromRGB(232, 214, 240), Color3.fromRGB(214, 240, 222) }
local function sheen(t: number): Color3 -- (a soap film's colours drifting round, kept pale)
	local u = (t * 0.35) % 3
	local i = math.floor(u)
	return SHEEN[i + 1]:Lerp(SHEEN[(i + 1) % 3 + 1], u - i)
end
local function droplets(at: Vector3, n: number, speed: number)
	emitter(host(at, 1.2), { Texture = TEX.blob, LightEmission = 0.5, LightInfluence = 0.5, Color = cs(Color3.fromRGB(230, 244, 252), Color3.fromRGB(200, 226, 240)),
		Size = ns(0, 0.09 * S, 1, 0), Lifetime = NR(0.25, 0.5), Speed = NR(speed * 0.4, speed), SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, -12 * S, 0) }):Emit(n)
end
wandIn = function()
	local h = hand
	if not h or h.id ~= "wand" then return end
	local k = h.model:GetScale()
	local film = part(Enum.PartType.Cylinder, Vector3.new(0.012 * S, 0.084 * S, 0.084 * S) * k, FILM, Enum.Material.Glass)
	film.Name = "film"; film.Transparency = 0.55; film.Parent = h.model
	h.extra = { film = film, k = k }
end
local function wandStep(h: Hand, t: number)
	local e = h.extra
	local blowing = t > 0.1 and t < 0.1 + WD.bubbles * WD.gap
	local th = if blowing then 0.012 + (((t - 0.1) % WD.gap) / WD.gap) * 0.09 else 0.012
	e.film.Size = Vector3.new(th * S, 0.084 * S, 0.084 * S) * e.k
	e.film.CFrame = h.model:GetPivot() * CFrame.new(0, 0, -th * S * e.k / 2) * CFrame.Angles(0, math.pi / 2, 0)
end
-- the laptop opens in your hand: the lid (and its screen) swing up about the hinge at the deck's back edge from shut,
-- past open and back (an overshoot and a settle), then the screen lights: a pale glow on the keys and your hand
local LIT = Color3.fromRGB(120, 172, 214) -- (Neon brightens it: on screen a pale blue)
laptopIn = function()
	local h = hand
	if not h or h.id ~= "laptop" then return end
	local m = h.model
	local deck, lid, scr = m:FindFirstChild("body") :: BasePart?, m:FindFirstChild("lid") :: BasePart?, m:FindFirstChild("screen") :: BasePart?
	if not deck or not lid then return end
	-- (still lying as the template does, axis-aligned: the hinge is the deck's back edge at its middle height)
	local piv = m:GetPivot()
	local hinge = deck.Position + Vector3.new(0, 0, deck.Size.Z / 2)
	local v = lid.Position - hinge
	local lean = math.atan2(-v.Z, v.Y) -- (how far the open lid leans forward of upright)
	local light = Instance.new("PointLight"); light.Color = LIT; light.Range = 7; light.Brightness = 0; light.Shadows = false
	light.Parent = scr or lid
	h.extra = { piv = piv, hinge = piv:PointToObjectSpace(hinge), shut = -(math.pi / 2 - lean - 0.06),
		parts = { { p = lid, rel = piv:ToObjectSpace(lid.CFrame) }, if scr then { p = scr, rel = piv:ToObjectSpace(scr.CFrame) } else nil },
		scr = scr, color = if scr then scr.Color else nil, light = light, lit = false, clicked = false }
end
local function laptopStep(h: Hand, t: number)
	local e = h.extra
	-- 0 = shut, 1 = open: an ease-out with a little overshoot past open (back-out), from 0.06 s to 0.4 s
	local u = math.clamp((t - 0.06) / 0.34, 0, 1)
	local c1 = 1.4
	local open = 1 + (c1 + 1) * (u - 1) ^ 3 + c1 * (u - 1) ^ 2
	local th = e.shut * (1 - open)
	local base = h.model:GetPivot()
	local hc = CFrame.new(e.hinge)
	local swing = hc * CFrame.Angles(th, 0, 0) * hc:Inverse()
	for _, q in e.parts do q.p.CFrame = base * swing * q.rel end
	if not e.clicked and u >= 0.55 then e.clicked = true; Sfx.play("click", nil, 0.6, 1.5) end
	-- the screen comes on: a white blink, then a pale glow
	if e.scr and t >= 0.3 then
		local k = math.clamp((t - 0.3) / 0.12, 0, 1)
		if not e.lit then e.lit = true; e.scr.Material = Enum.Material.Neon end
		e.scr.Color = Color3.new(1, 1, 1):Lerp(LIT, k)
		e.light.Brightness = 2.2 - 1.2 * k
	end
end
-- the medkit (v3, 18 Nov 2026): its lid ("lid", "lidhandle": every part named lid*) swings up and AWAY from you about
-- its front bottom edge as the hand comes up (so you look into the tray, the lid standing beyond it), stays open while
-- you take what you need, and shuts as it goes down
do
	X.medkitIn = function()
		local h = hand
		if not h or h.id ~= "medkit" then return end
		local m = h.model
		local lid = m:FindFirstChild("lid") :: BasePart?
		if not lid then return end
		local piv = m:GetPivot()
		local rel = piv:ToObjectSpace(lid.CFrame)
		local parts = {}
		for _, d in m:GetChildren() do
			if d:IsA("BasePart") and string.sub(d.Name, 1, 3) == "lid" then table.insert(parts, { p = d, rel = piv:ToObjectSpace(d.CFrame) }) end
		end
		h.extra = { medkit = true, hinge = Vector3.new(0, rel.Position.Y - lid.Size.Y / 2, rel.Position.Z - lid.Size.Z / 2), parts = parts }
		local FxM = require(script.Parent:WaitForChild("Fx")) :: any
		if FxM.itemUse then pcall(FxM.itemUse, m) end -- (a skin's own effect as its lid opens: the Bento's steam)
	end
	X.medkitStep = function(h: Hand, t: number)
		local e = h.extra
		-- 0 = shut, 1 = open: up with a little overshoot from 0.05 to 0.22 s, shut again from 0.5 to 0.6 s
		local u = math.clamp((t - 0.05) / 0.17, 0, 1)
		local c1 = 1.3
		local open = 1 + (c1 + 1) * (u - 1) ^ 3 + c1 * (u - 1) ^ 2
		open *= 1 - smooth((t - 0.5) / 0.1)
		local hc = CFrame.new(e.hinge)
		local swing = hc * CFrame.Angles(-1.95 * open, 0, 0) * hc:Inverse()
		local base = h.model:GetPivot()
		for _, q in e.parts do q.p.CFrame = base * swing * q.rel end
	end
end
extraStep = function(h: Hand, t: number)
	if h.extra.cook then X.cookHand(h, t); return end
	if h.extra.medkit then X.medkitStep(h, t); return end
	if h.id == "print" then X.printStep(h, t) elseif h.id == "wand" then wandStep(h, t) elseif h.id == "laptop" then laptopStep(h, t) end
end

type Soap = { p0: Vector3, v0: Vector3, t0: number, ball: BasePart }
local soaps: { [number]: Soap } = {}
local function addSoap(m: any)
	if type(m.id) ~= "number" or typeof(m.p) ~= "Vector3" or typeof(m.v) ~= "Vector3" or soaps[m.id] then return end
	local b = soapBall(SW.r * 2)
	b.CFrame = CFrame.new(m.p)
	b.Parent = folder
	soaps[m.id] = { p0 = m.p, v0 = m.v, t0 = os.clock(), ball = b }
	Sfx.play("bloop", m.p, if m.o == me.UserId then 0.7 else 0.5, 0.8 + math.random() * 0.45)
end
local function dropSoap(id: any, at: any): boolean
	local sp = if type(id) == "number" then soaps[id] else nil
	if not sp then return false end
	soaps[id] = nil
	local p = if typeof(at) == "Vector3" then at else sp.ball.Position
	sp.ball:Destroy()
	droplets(p, 10, 3 * S)
	Sfx.play("plip", p, 0.6, 0.8 + math.random() * 0.5)
	return true
end
local function soapStep()
	local n = os.clock()
	for id, sp in soaps do
		local t = n - sp.t0
		if t > SW.life + 0.5 then sp.ball:Destroy(); soaps[id] = nil; continue end
		local k = math.sin(t * 11 + id) * 0.08
		sp.ball.Size = Vector3.new(1 + k, 1 - k, 1 + k * 0.6) * SW.r * 2
		sp.ball.CFrame = CFrame.new(Items.soapAt(sp.p0, sp.v0, id, t))
	end
end

-- sealed in yourself: no film over your view, no countdown, just BUBBLED on the announcer line while you're in it
-- (20 Nov 2026, the owner: "can we get rid of the ui for getting bublled and just have a message saying bubbled on screen")

type Trap = { o: number?, model: Instance?, untilT: number, born: number, ball: BasePart?, v: Vector3 }
local traps: { [string]: Trap } = {}
local myTrap: Trap? = nil
local bursts: { { ball: BasePart, t: number } } = {}
local function trapCentre(model: Instance?): Vector3?
	local r = model and model:FindFirstChild("HumanoidRootPart") :: BasePart?
	return r and r.Position + Vector3.new(0, WD.y - Hitbox.ROOT_UP, 0)
end
local function nameOf(model: Instance?): string
	local pl = model and Players:GetPlayerFromCharacter(model)
	return string.upper(if pl then pl.DisplayName elseif model then model.Name else "SOMEONE")
end
local function endMine(loud: boolean)
	myTrap = nil
	Hud.calloutOff("BUBBLED")
	if not loud then return end
	Sfx.play("bigpop")
	droplets(camera.CFrame.Position + camera.CFrame.LookVector * 2, 60, 5 * S)
	shake = math.max(shake, 0.45)
	Hud.callout("POP!", 0.8)
end
local function onTrap(m: any)
	local model = if typeof(m.model) == "Instance" then m.model else nil
	local k = keyOf(m)
	local old = traps[k]
	if old and old.ball then old.ball:Destroy() end
	local tr: Trap = { o = if type(m.o) == "number" then m.o else nil, model = model, untilT = os.clock() + (tonumber(m.left) or WD.dur), born = os.clock(),
		ball = nil, v = if typeof(m.v) == "Vector3" then m.v else Vector3.zero }
	traps[k] = tr
	if m.o == me.UserId then
		-- sealed in: off your rope, floating with the bubble (Body.onStep below), the film over your view
		local st = Body.st :: any
		if st and st.hook then st.hook = nil; GrappleR:FireServer("release") end
		Body.push(Vector3.new(0, tr.v.Y, 0)) -- (off the floor, so the Humanoid lets go of it)
		myTrap = tr
		Sfx.play("glorp")
		droplets(camera.CFrame.Position + camera.CFrame.LookVector * 2, 30, 4 * S)
		Hud.callout("BUBBLED", tr.untilT - os.clock() + 0.4) -- (up while you're in it; endMine takes it down)
		shake = math.max(shake, 0.3)
		return
	end
	tr.ball = soapBall(WD.r * 2)
	local c = trapCentre(model)
	if c then
		tr.ball.CFrame = CFrame.new(c)
		Sfx.play("glorp", c)
		droplets(c, 24, 4 * S)
	end
	tr.ball.Parent = folder
	if m.by == me.UserId then Hud.callout("BUBBLED " .. nameOf(model), 1.3) end
end
local function onTrapEnd(m: any)
	local k = keyOf(m)
	local tr = traps[k]
	traps[k] = nil
	local loud = m.why ~= "gone"
	if m.o == me.UserId then
		-- (p: we weren't where the bubble went: drop from where the server has us)
		local _, _, root = myChar()
		if typeof(m.p) == "Vector3" and root then root.CFrame = root.CFrame.Rotation + m.p + Vector3.new(0, Hitbox.ROOT_UP, 0) end
		if myTrap then endMine(loud) end
	elseif tr and tr.ball then
		if loud then
			local p = tr.ball.Position
			Sfx.play("bigpop", p)
			droplets(p, 70, 7 * S)
			shake = math.max(shake, 0.5 - (p - camera.CFrame.Position).Magnitude / (30 * S))
			table.insert(bursts, { ball = tr.ball, t = 0 })
		else
			tr.ball:Destroy()
		end
	end
	if m.pb == me.UserId and m.why == "hit" and m.o ~= me.UserId then
		Hud.callout("POPPED " .. nameOf(if typeof(m.model) == "Instance" then m.model else nil), 0.9)
	end
end
local function trapStep(dt: number)
	local n = os.clock()
	local mine = myTrap
	if mine then
		if n > mine.untilT + 0.4 or not myChar() then endMine(myChar() ~= nil) -- (our timer ran out a hair before the server's pop)
		elseif math.random() < dt * 1.6 then Sfx.play("blub", nil, 0.5, 0.7 + math.random() * 0.6) end
	end
	for k, tr in traps do
		if tr.o == me.UserId then continue end
		local ball = tr.ball
		local c = trapCentre(tr.model)
		local hum = tr.model and tr.model:FindFirstChildOfClass("Humanoid")
		if not ball or not c or n > tr.untilT + 1.5 or (hum and hum.Health <= 0) then
			if ball then ball:Destroy() end
			traps[k] = nil
			continue
		end
		local age, left = n - tr.born, tr.untilT - n
		local x = math.min(1, age / 0.3) - 1
		local grow = math.max(0.2, 1 + 2.70158 * x * x * x + 1.70158 * x * x) -- (pops in with an overshoot)
		local wob = (0.025 + (if left < 1 then (1 - math.max(0, left)) * 0.07 else 0)) * math.sin(n * 13) -- (shakier right before it pops)
		ball.Size = Vector3.new(1 + wob, 1 - wob, 1 + wob) * WD.r * 2 * grow
		ball.CFrame = CFrame.new(c)
		ball.Color = sheen(n + #k)
	end
	for i = #bursts, 1, -1 do
		local b = bursts[i]
		b.t += dt
		if b.t >= 0.14 then b.ball:Destroy(); table.remove(bursts, i); continue end
		b.ball.Size *= 1 + dt * 2.4
		b.ball.Transparency = b.t / 0.14
	end
end
-- sealed in: you go where it floats, no rope
do
	local prev = Body.onStep
	Body.onStep = function(st: any, chest: Vector3, dt: number)
		if prev then prev(st, chest, dt) end
		local tr = myTrap
		if tr and me:GetAttribute("Trap") then
			st.vx, st.vy, st.vz = tr.v.X, tr.v.Y, tr.v.Z
			if st.hook then st.hook = nil; GrappleR:FireServer("release") end
		end
	end
end
X.addSoap = addSoap
X.dropSoap = dropSoap
X.onTrap = onTrap
X.onTrapEnd = onTrapEnd
X.soapStep = soapStep
X.trapStep = trapStep
end

-- ---------------------------------------------------------------- what the server says
local function onFx(m: any)
	if type(m) ~= "table" then return end
	local k = m.k
	if k == "ps" and m.w == "soap" then X.addSoap(m)
	elseif k == "ps" then addFlying(m)
	elseif k == "cook" then X.onCook(m)
	elseif k == "cookx" then X.onCookEnd(m)
	elseif k == "pb" then
		local v = if type(m.id) == "number" then flying[m.id] else nil
		if v and typeof(m.p) == "Vector3" and typeof(m.v) == "Vector3" then
			v.off += v.p - m.p -- (a small correction slides in instead of jumping)
			v.p, v.v = m.p, m.v
		end
	elseif k == "pd" then if not X.dropSoap(m.id, m.p) then dropFlying(m.id, m.x == true, if typeof(m.p) == "Vector3" then m.p else nil) end
	elseif k == "boom" and typeof(m.p) == "Vector3" then
		boom(m.p, if type(m.r) == "number" then m.r else 7.5 * S)
		if type(m.o) == "number" and (Sfx :: any).skinItem then (Sfx :: any).skinItem(Players:GetPlayerByUserId(m.o), "frag", "blast", m.p) end
	elseif k == "smoke" and type(m.id) == "number" and typeof(m.p) == "Vector3" then
		addCloud(m.id, m.p, if type(m.r) == "number" then m.r else 6.5 * S, if type(m.left) == "number" then m.left else 10)
		if type(m.o) == "number" and (Sfx :: any).skinItem then (Sfx :: any).skinItem(Players:GetPlayerByUserId(m.o), "smoke", "cloud", m.p) end
	elseif k == "bub+" and type(m.id) == "number" and typeof(m.p) == "Vector3" then
		addDome(m.id, m.p, if type(m.r) == "number" then m.r else 4.4 * S, if type(m.left) == "number" then m.left else 7, m.fresh ~= false and type(m.o) == "number")
	elseif k == "bubx" then dropDome(m.id)
	elseif k == "bubhit" and typeof(m.p) == "Vector3" then domeHit(m.p)
	elseif k == "medkit" then
		healFx(if typeof(m.model) == "Instance" then m.model else nil, m.o == me.UserId)
		-- (someone else's medkit: their skin's layer where they stand; yours played as you pressed G)
		local hr = if typeof(m.model) == "Instance" then m.model:FindFirstChild("HumanoidRootPart") else nil
		if type(m.o) == "number" and m.o ~= me.UserId and hr and hr:IsA("BasePart") and (Sfx :: any).skinItem then
			(Sfx :: any).skinItem(Players:GetPlayerByUserId(m.o), "medkit", "open", hr.Position)
		end
	elseif k == "popper" then popperFx(m)
	elseif k == "reverse" then reverseFx(m)
	elseif k == "reversex" and type(m.o) == "number" then dropCard(m.o)
	elseif k == "reflect" then reflectFx(m)
	elseif k == "dh" then
		local v = if type(m.id) == "number" then flying[m.id] else nil
		if v then
			if typeof(m.p) == "Vector3" and typeof(m.v) == "Vector3" then v.off += v.p - m.p; v.p, v.v = m.p, m.v end
			v.target = if typeof(m.h) == "Instance" then m.h else nil
		end
	elseif k == "dstick" then
		Sfx.play("quack", middleOf(if typeof(m.on) == "Instance" then m.on else nil))
		if m.o == me.UserId then Hud.callout("QUACK! STUCK", 1.0) end
		if m.onUid == me.UserId then Hud.callout("A DUCK IS STUCK TO YOU", 1.2) end
	elseif k == "ads" then onAds(m)
	elseif k == "ads!" then
		pend = nil
		Sfx.play("empty"); Hud.callout("NO SIGNAL · POINT IT AT SOMEONE", 1.0)
	elseif k == "adsfx" then
		local tm = if typeof(m.tm) == "Instance" then m.tm else nil
		local r = tm and tm:FindFirstChild("HumanoidRootPart") :: BasePart?
		if r then confetti(r.Position + Vector3.new(0, 2.5, 0), Vector3.yAxis, 16, 5 * S) end
		Sfx.play("click", nil, 0.9, 1.4)
		if m.o == me.UserId and m.to ~= me.UserId then Hud.callout("ADS SERVED", 1.2) end
	elseif k == "flashed" then onFlashed(m)
	elseif k == "nvflash" then nvflashFx(m)
	elseif k == "quiz" then onQuiz(m)
	elseif k == "quizx" then onQuizEnd(m)
	elseif k == "calchit" then
		if typeof(m.p) == "Vector3" then
			emitter(host(m.p, 2), { Texture = TEX.blob, LightEmission = 0.6, LightInfluence = 0.4, Color = cs(Color3.fromRGB(200, 240, 225), Color3.fromRGB(240, 240, 230)),
				Size = ns(0, 0.15 * S, 1, 0), Lifetime = NR(0.3, 0.5), Speed = NR(3 * S, 6 * S), SpreadAngle = Vector2.new(180, 180) }):Emit(24)
			Sfx.play("bonk", m.p)
		end
	elseif k == "radar" then onRadarFx(m)
	elseif k == "ticket" then onTicket(m)
	elseif k == "ticketx" then onTicketEnd(m)
	elseif k == "jail" then onJail(m)
	elseif k == "jailx" then onJailEnd(m)
	elseif k == "trap" then X.onTrap(m)
	elseif k == "trapx" then X.onTrapEnd(m)
	elseif k == "snap" then X.onSnap(m)
	elseif k == "photo!" then
		pend = nil
		Sfx.play("empty"); Hud.callout("NO PHOTO: " .. string.upper(tostring(m.why or "")), 1.4)
	elseif k == "frame" then X.onFrame(m)
	elseif k == "framex" then X.dropFrame(m.id, m.why == "gone" or m.why == "new")
	elseif k == "ptp" then X.onPtp(m)
	elseif k == "tele" then X.teleFx(m)
	elseif k == "hs" then addHole(m)
	elseif k == "hu" then updHole(m)
	elseif k == "he" then popHole(m)
	elseif k == "list" and type(m.list) == "table" then
		for _, e in m.list do if type(e) == "table" then e.fresh = false; onFx(e) end end
	end
end
ItemFx.OnClientEvent:Connect(onFx)

RunService.RenderStepped:Connect(function(dt: number)
	handStep()
	flyStep(math.min(dt, 0.1))
	cloudStep()
	domeStep()
	cardStep(dt)
	holeStep(dt)
	squeezeStep()
	adsStep(dt)
	nvStep(dt)
	headStep()
	examStep()
	boostStep()
	radarStep()
	tagStep()
	cageStep()
	X.camStep()
	X.frameStep()
	X.thumbStep()
	X.soapStep()
	X.trapStep(dt)
	X.cookStep()
	hudStep()
end)
