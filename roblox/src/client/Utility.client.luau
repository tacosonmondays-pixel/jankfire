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
local function inHub(): boolean return me:GetAttribute("Zone") == "hub" end
local function menuOpen(): boolean return me:GetAttribute("LoadoutOpen") == true end
local function thirdPerson(): boolean
	local _, _, root = myChar()
	return root ~= nil and (camera.CFrame.Position - root.Position).Magnitude > 4.5
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
	quiz = "x_calc", calc = "x_calc", laptop = "x_laptop", nvg = "x_nvg" }
local function itemModel(id: string): Model
	local name = MODEL[id] or ("x_" .. id)
	local t = templates and templates:FindFirstChild(name)
	local m = if t and t:IsA("Model") then t:Clone() else standIn(name)
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.CastShadow = false end
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
local function charges(): (number, number)
	local n = tonumber(me:GetAttribute("ItemN")) or 0
	if pend and os.clock() - pend.t < 1 then n = math.min(n, pend.n) end
	local at = tonumber(me:GetAttribute("ItemAt")) or 0
	return n, at
end
me:GetAttributeChangedSignal("ItemN"):Connect(function() pend = nil end)
local function hudStep()
	local id = me:GetAttribute("Item")
	local it = if type(id) == "string" then L[id] else nil
	local _, _, root = myChar()
	plate.Visible = it ~= nil and it.live and not inHub() and not menuOpen() and root ~= nil
	if not it or not plate.Visible then return end
	local label = if it.id == "nvg" then (if me:GetAttribute("NV") then "Goggles · on  [N] flash" else "Night Vision Goggles") else it.name
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
local CLIPS = {
	throw = { dur = 0.52, out = 0.3, release = 0.1, inT = 0.04, keys = {
		K(0, -0.55, -1.25, -0.95, 0.7, 0.2, 0.35), K(0.06, -0.46, -0.58, -1.05, 0.15, 0.25, 0.25),
		K(0.18, -0.2, -0.5, -1.8, -0.55, 0.1, 0.05), K(0.52, -0.5, -1.5, -1.1, 0.4, 0.2, 0.3) } },
	medkit = { dur = 0.82, out = 0.52, release = 0.62, keys = {
		K(0, -0.5, -1.3, -1.0, 0.6, 0.2, 0.2), K(0.13, -0.32, -0.62, -1.18, 0.2, 0.45, 0.12),
		K(0.34, -0.3, -0.58, -1.12, 0.32, 0.55, 0.16), K(0.56, -0.42, -0.95, -1.0, 0.5, 0.35, 0.2), K(0.82, -0.55, -1.55, -0.9, 0.7, 0.2, 0.3) } },
	-- (web pop_popper: snaps up by 0.07 s, the yank at 0.10, eased back by 0.34, gone by 0.5; it pops at 0.08)
	popper = { dur = 0.5, out = 0.3, release = 9, inT = 0.05, keys = {
		K(0, -0.5, -1.3, -1.0, 0.4, 0.1, 0.2), K(0.07, -0.36, -0.52, -1.3, -1.05, 0.15, 0.1),
		K(0.1, -0.34, -0.47, -1.12, -1.35, 0.2, 0.12), K(0.34, -0.38, -0.62, -1.22, -1.0, 0.15, 0.1), K(0.5, -0.55, -1.5, -1.0, 0.3, 0.1, 0.25) } },
	-- (web pop_reverse: up from below by 0.16 s, spun round on the way, held, settles 0.62, drops at 0.8)
	reverse = { dur = 0.8, out = 0.6, release = 9, inT = 0.05, keys = {
		K(0, -0.45, -1.3, -1.0, 0.3, 0, 0.2), K(0.16, -0.3, -0.42, -1.25, 0, math.pi * 2, 0.05),
		K(0.5, -0.3, -0.44, -1.25, 0, math.pi * 2 + 0.25, 0.05), K(0.62, -0.32, -0.5, -1.22, 0.1, math.pi * 2 + 0.2, 0.08), K(0.8, -0.5, -1.5, -1.0, 0.4, math.pi * 2, 0.25) } },
	-- (web pop_laptop: up from below by 0.10 s, shoved forward screen first at 0.18 with an overshoot, held while it
	-- "loads" to 0.7, dropped by 0.9)
	laptop = { dur = 0.9, out = 0.7, release = 9, inT = 0.06, keys = {
		K(0, -0.4, -1.4, -1.0, 0.5, 0.2, 0.15), K(0.1, -0.3, -0.62, -1.2, 0.05, 0.25, 0.05),
		K(0.18, -0.24, -0.55, -1.55, -0.1, 0.2, 0.0), K(0.7, -0.26, -0.58, -1.45, -0.05, 0.22, 0.02), K(0.9, -0.45, -1.5, -1.0, 0.5, 0.2, 0.2) } },
	bubble = { dur = 0.66, out = 0.4, release = 0.5, keys = {
		K(0, -0.45, -1.3, -1.0, 0.5, 0.1, 0.2), K(0.12, -0.3, -0.5, -1.35, -0.1, 0.2, 0.05),
		K(0.3, -0.3, -0.52, -1.3, -0.15, 0.25, 0.05), K(0.66, -0.5, -1.5, -1.0, 0.5, 0.1, 0.3) } },
}
local function sampleClip(c: any, t: number): CFrame
	local keys = c.keys
	local a, b = keys[1], keys[#keys]
	for i = 1, #keys - 1 do
		if t >= keys[i].t and t <= keys[i + 1].t then a, b = keys[i], keys[i + 1]; break end
	end
	local u = if b.t > a.t then smooth((t - a.t) / (b.t - a.t)) else 1
	local p = a.p:Lerp(b.p, u)
	local r = a.r:Lerp(b.r, u)
	return CFrame.new(p) * CFrame.fromEulerAnglesXYZ(r.X, r.Y, r.Z)
end
-- the left hand's own arm, when the gun has no left hand of its own: a hold row for a thing held in the fist
Holds.holds.item_hand = { Left = { pose = "grip", at = Vector3.zero, rot = Vector3.zero, size = 0.9 } }
local FP_K = 0.95 -- the item in first person, against its world size (the guns are drawn a little under world size)
local FP_SIZE = { duck = 0.45 } -- (the thrown duck is 0.6 m long, web pj_duck: in your hand it's a toy)
type Hand = { id: string, clip: any, t0: number, model: Model, grip: CFrame, own: Model?, root: BasePart?, gone: boolean, lastF: CFrame? }
local hand: Hand? = nil
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
local function startHand(id: string)
	dropHand()
	if thirdPerson() or not VM.model then return end
	local clip = CLIPS[id] or CLIPS.throw
	if id == "nvg" then return end -- (the goggles go on your head, not in your hand: see the goggles below)
	local m = itemModel(id)
	m:ScaleTo(FP_K * (FP_SIZE[id] or 1))
	m.Parent = camera
	local h: Hand = { id = id, clip = clip, t0 = os.clock(), model = m, grip = gripOf(m), gone = false }
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
	return true
end
-- where the item leaves your hand (a thrown one's flight starts there and slides onto the server's line)
local function releasePoint(): Vector3?
	local h = hand
	if not h or not h.lastF then return nil end
	return h.model:GetPivot().Position
end

-- ---------------------------------------------------------------- pressing G
local lastUse = -math.huge
local toggleGoggles: () -> () -- (the goggles below)
UserInputService.InputBegan:Connect(function(io: InputObject, gp: boolean)
	if gp or io.KeyCode ~= Enum.KeyCode.G then return end
	if menuOpen() or inHub() then return end
	local _, _, root = myChar()
	if not root then return end
	local id = me:GetAttribute("Item")
	local it = if type(id) == "string" then L[id] else nil
	if not it or not it.live then return end
	if me:GetAttribute("Quiz") then return end -- (sitting a pop quiz: no items)
	if it.id == "nvg" then toggleGoggles(); return end
	local t = os.clock()
	if t - lastUse < Items.SPAM_CLIENT then return end
	local n = charges()
	if n <= 0 then
		Sfx.play("empty")
		Hud.callout(string.lower(it.name) .. ": recharging", 0.8)
		return
	end
	lastUse = t
	pend = { n = n - 1, t = t }
	-- from your eye (the camera itself in first person, so it leaves from under the crosshair), along your look
	local eye = if thirdPerson() then root.Position + Vector3.new(0, Hitbox.EYE_UP - Hitbox.ROOT_UP, 0) else camera.CFrame.Position
	ItemR:FireServer(it.id, eye, camera.CFrame.LookVector)
	startHand(it.id)
	handStep()
	if it.id ~= "popper" and it.id ~= "reverse" and it.id ~= "laptop" then -- (those make their sound when the server says it happened)
		Sfx.play(if it.id == "medkit" then "heal" elseif it.id == "bubble" then "reverse" else "swing")
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
	local h = host(at, 4)
	-- a hot white core that swells to half the radius and is gone in a blink (web: a flash sphere at half the radius)
	local core = part(Enum.PartType.Ball, Vector3.one * R * 0.35, Color3.fromRGB(255, 236, 196), Enum.Material.Neon)
	core.CFrame = CFrame.new(at); core.Parent = folder
	local light = Instance.new("PointLight")
	light.Color = Color3.fromRGB(255, 190, 120); light.Range = R * 1.6; light.Brightness = 8; light.Shadows = false; light.Parent = core
	task.spawn(function()
		local t0 = os.clock()
		while core.Parent do
			local t = os.clock() - t0
			if t > 0.32 then break end
			local u = t / 0.32
			core.Size = Vector3.one * R * (0.35 + 0.7 * smooth(u * 2.5))
			core.Transparency = math.clamp((t - 0.05) / 0.12, 0, 1)
			light.Brightness = 8 * (1 - u)
			RunService.RenderStepped:Wait()
		end
		core:Destroy()
	end)
	-- the fireball: orange, quick, thrown out and dragged back
	emitter(h, { Texture = TEX.fire, LightEmission = 1, LightInfluence = 0, Brightness = 3, ZOffset = 1,
		Color = cs(Color3.fromRGB(255, 246, 214), Color3.fromRGB(255, 168, 64), Color3.fromRGB(196, 66, 24)),
		Size = ns(0, R * 0.22, 0.35, R * 0.38, 1, R * 0.12), Transparency = ns(0, 0, 0.6, 0.25, 1, 1),
		Lifetime = NR(0.22, 0.45), Speed = NR(R * 0.9, R * 2.2), SpreadAngle = Vector2.new(180, 180), Drag = 6,
		Rotation = NR(0, 360), RotSpeed = NR(-120, 120) }):Emit(34)
	-- the smoke it leaves: dark grey, rolling up and out
	emitter(h, { Texture = TEX.smoke, LightInfluence = 1, Color = cs(Color3.fromRGB(96, 94, 92), Color3.fromRGB(150, 150, 150)),
		Size = ns(0, R * 0.25, 1, R * 0.7), Transparency = ns(0, 0.15, 0.5, 0.35, 1, 1),
		Lifetime = NR(1.4, 2.4), Speed = NR(R * 0.3, R * 0.9), SpreadAngle = Vector2.new(180, 180), Drag = 2.5,
		Acceleration = Vector3.new(0, 1.2 * S, 0), Rotation = NR(0, 360), RotSpeed = NR(-30, 30) }):Emit(22)
	-- hot sparks (web: 22)
	emitter(h, { Texture = TEX.blob, LightEmission = 1, LightInfluence = 0, Brightness = 5,
		Orientation = Enum.ParticleOrientation.VelocityParallel,
		Color = cs(Color3.fromRGB(255, 252, 225), Color3.fromRGB(255, 196, 90), Color3.fromRGB(255, 110, 30)),
		Size = ns(0, 0.09 * S, 1, 0), Squash = ns(0, 2.5, 1, 2.5),
		Lifetime = NR(0.3, 0.75), Speed = NR(R * 1.2, R * 2.6), SpreadAngle = Vector2.new(180, 180),
		Acceleration = Vector3.new(0, -22 * S, 0), Drag = 1.2 }):Emit(22)
	-- a ring across the floor when it goes off near one
	local fl = floorBelow(at, R * 0.5)
	if fl then
		local ring = part(Enum.PartType.Block, Vector3.new(1, 0.05, 1), Color3.new(), nil)
		ring.Transparency = 1; ring.CFrame = CFrame.new(fl + Vector3.new(0, 0.12, 0)); ring.Parent = folder
		local dc = Instance.new("Decal")
		dc.Texture = TEX.ring; dc.Face = Enum.NormalId.Top; dc.Color3 = Color3.fromRGB(255, 226, 190); dc.Transparency = 0.35; dc.Parent = ring
		task.spawn(function()
			local t0 = os.clock()
			while ring.Parent do
				local u = (os.clock() - t0) / 0.42
				if u >= 1 then break end
				local s = R * 2 * (1 - (1 - u) ^ 3)
				ring.Size = Vector3.new(math.max(1, s), 0.05, math.max(1, s))
				dc.Transparency = 0.35 + 0.65 * u
				RunService.RenderStepped:Wait()
			end
			ring:Destroy()
		end)
		-- dust kicked off the floor
		emitter(host(fl + Vector3.new(0, 0.6, 0), 3), { Texture = TEX.smoke, LightInfluence = 1, Color = cs(Color3.fromRGB(170, 164, 156)),
			Size = ns(0, 0.8 * S, 1, 2.6 * S), Transparency = ns(0, 0.3, 1, 1), Lifetime = NR(0.6, 1.2),
			Speed = NR(R * 0.6, R * 1.1), SpreadAngle = Vector2.new(90, 8), Drag = 4, Rotation = NR(0, 360),
			EmissionDirection = Enum.NormalId.Top }):Emit(16)
	end
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
	local model = itemModel(m.w)
	model.Parent = folder
	local mine = m.o == me.UserId
	if m.w == "duck" and not mine then Sfx.play("squeak", m.p, 0.8) end
	local vis: Vis = { id = m.id, k = m.w, p = m.p, v = m.v, r = w.r, bounce = w.bounce, grav = w.grav, born = os.clock(),
		fuse = if type(m.fuse) == "number" then m.fuse else w.fuse, model = model,
		axis = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5).Unit, ang = 0, off = Vector3.zero, mine = mine,
		lamp = model:FindFirstChild("lamp", true) :: BasePart? }
	-- yours leaves from your hand and slides onto the server's line within a moment
	local rel = if mine then releasePoint() else nil
	if rel then vis.off = rel - m.p end
	flying[m.id] = vis
	if not mine then Sfx.play("swing", m.p, 0.8) end
end
local function dropFlying(id: any)
	local v = if type(id) == "number" then flying[id] else nil
	if not v then return end
	flying[id] = nil
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
type Cloud = { id: number, h: BasePart, ems: { ParticleEmitter }, untilT: number }
local cloudsLive: { [number]: Cloud } = {}
local SMOKE_COL = Color3.fromRGB(176, 180, 186)
local function addCloud(id: number, at: Vector3, r: number, left: number)
	if cloudsLive[id] then return end
	local h = host(at, left + 5)
	local ems = {}
	-- a dense core and a ring of puffs round it, low and wide like the web game's 6.5 m x 3.5 m column: opaque soft
	-- blobs inside, wispy smoke on the edges, so a player standing in it really is hidden
	local spots = { Vector3.new(0, r * 0.12, 0) }
	for i = 0, 7 do
		local a = i / 8 * math.pi * 2
		table.insert(spots, Vector3.new(math.cos(a) * r * 0.55, r * (0.05 + 0.1 * (i % 2)), math.sin(a) * r * 0.55))
	end
	for i = 0, 3 do
		local a = (i + 0.5) / 4 * math.pi * 2
		table.insert(spots, Vector3.new(math.cos(a) * r * 0.28, r * 0.32, math.sin(a) * r * 0.28))
	end
	for i, o in spots do
		local att = Instance.new("Attachment")
		att.Position = o; att.Parent = h
		-- (thick: the first photo in the hall showed the far door through it, so twice the puffs, bigger, fully solid)
		local core = emitter(att, { Texture = TEX.blob, LightInfluence = 1, LightEmission = 0, Color = cs(SMOKE_COL),
			Size = ns(0, r * 0.5, 1, r * 0.75), Transparency = ns(0, 1, 0.1, 0, 0.8, 0.05, 1, 1),
			Lifetime = NR(2.6, 3.4), Rate = 7, Speed = NR(0.3 * S, 1.2 * S), SpreadAngle = Vector2.new(180, 180), Drag = 1,
			Rotation = NR(0, 360), RotSpeed = NR(-12, 12), Acceleration = Vector3.new(0, 0.15 * S, 0) })
		core.Enabled = true
		core:Emit(6)
		table.insert(ems, core)
		if i % 2 == 1 then
			local wisp = emitter(att, { Texture = TEX.smoke, LightInfluence = 1, Color = cs(SMOKE_COL),
				Size = ns(0, r * 0.5, 1, r * 0.8), Transparency = ns(0, 1, 0.15, 0.2, 1, 1),
				Lifetime = NR(2.2, 3), Rate = 2, Speed = NR(0.5 * S, 1.6 * S), SpreadAngle = Vector2.new(180, 180), Drag = 0.8,
				Rotation = NR(0, 360), RotSpeed = NR(-20, 20) })
			wisp.Enabled = true
			table.insert(ems, wisp)
		end
	end
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
	if fresh then Sfx.play("reverse", at, 0.9) end
end
local function dropDome(id: any)
	local d = if type(id) == "number" then domes[id] else nil
	if not d then return end
	domes[id] = nil
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
		local att = Instance.new("Attachment")
		att.Position = Vector3.new(0, 0.6, 0); att.Parent = root
		local e = emitter(att, { Texture = TEX.blob, LightEmission = 0.6, LightInfluence = 0.4, Brightness = 2,
			Color = cs(Color3.fromRGB(236, 255, 240), Color3.fromRGB(120, 230, 150)), Size = ns(0, 0.22 * S, 1, 0),
			Transparency = ns(0, 0.1, 1, 1), Lifetime = NR(0.6, 1.0), Rate = 16, Speed = NR(1.2 * S, 2.4 * S),
			SpreadAngle = Vector2.new(50, 50), Acceleration = Vector3.new(0, 2 * S, 0), Drag = 1.5 })
		e.Enabled = true
		task.delay(1, function() e.Enabled = false end)
		Debris:AddItem(att, 2.2)
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
	local cm = itemModel("reverse")
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
type HoleV = { id: number, p: Vector3, on: Instance?, born: number, R: number, mine: boolean, core: BasePart, shell: BasePart,
	ring: BasePart, pull: BasePart, orbit: Model, stuck: Model?, ang: number }
local holesV: { [number]: HoleV } = {}
local VOID = Color3.fromRGB(10, 8, 14)
local VIOLET = Color3.fromRGB(122, 84, 190)
local function addHole(m: any)
	local id = m.id
	if type(id) ~= "number" or holesV[id] or typeof(m.p) ~= "Vector3" then return end
	local on = if typeof(m.on) == "Instance" then m.on else nil
	local core = part(Enum.PartType.Ball, Vector3.one * 2 * S, VOID, Enum.Material.SmoothPlastic)
	local shell = part(Enum.PartType.Ball, Vector3.one * 3 * S, VIOLET, Enum.Material.Neon); shell.Transparency = 0.78
	local ring = part(Enum.PartType.Block, Vector3.new(4.4 * S, 0.05, 4.4 * S), VIOLET, nil); ring.Transparency = 1
	for _, face in { Enum.NormalId.Top, Enum.NormalId.Bottom } do
		local dc = Instance.new("Decal")
		dc.Texture = TEX.ring; dc.Face = face; dc.Color3 = Color3.fromRGB(170, 130, 235); dc.Transparency = 0.25; dc.Parent = ring
	end
	-- sparks drawn in from a shell at 0.6 of its reach (an inward sphere emitter: they fly to the middle)
	local R = if type(m.R) == "number" then m.R else Items.DUCK.holeR
	local pull = part(Enum.PartType.Ball, Vector3.one * R * 1.2, VIOLET, nil); pull.Transparency = 1
	local e = emitter(pull, { Texture = TEX.blob, LightEmission = 1, LightInfluence = 0, Brightness = 2,
		Color = cs(Color3.fromRGB(200, 170, 255), VIOLET), Size = ns(0, 0.12 * S, 1, 0.04 * S), Transparency = ns(0, 0.2, 1, 0.9),
		Lifetime = NR(0.5, 0.7), Speed = NR(R * 0.6 / 0.6, R * 0.6 / 0.5), Rate = 40,
		Shape = Enum.ParticleEmitterShape.Sphere, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
		ShapeInOut = Enum.ParticleEmitterShapeInOut.Inward, Orientation = Enum.ParticleOrientation.VelocityParallel, Squash = ns(0, 2, 1, 2) })
	e.Enabled = true
	local orbit = itemModel("duck"); orbit:ScaleTo(0.35)
	for _, x in { core, shell, ring, pull } do x.Parent = folder end
	orbit.Parent = folder
	local age = if type(m.age) == "number" then m.age else 0
	local hv: HoleV = { id = id, p = m.p, on = on, born = os.clock() - age, R = R, mine = m.o == me.UserId, core = core, shell = shell,
		ring = ring, pull = pull, orbit = orbit, stuck = nil, ang = 0 }
	if on then
		local dm = itemModel("duck"); dm:ScaleTo(0.7); dm.Parent = folder
		hv.stuck = dm
	end
	holesV[id] = hv
	if age < 0.5 then Sfx.play("hole", m.p, 0.9) end
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
		for _, x in { hv.core, hv.shell, hv.ring, hv.pull } do x:Destroy() end
		hv.orbit:Destroy()
		if hv.stuck then hv.stuck:Destroy() end
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
	for _, hv in holesV do
		if hv.on then
			local c = middleOf(hv.on)
			if c then hv.p = c end
		end
		hv.ang += dt
		local age = t - hv.born
		-- grows in over 0.3 s once open, pulses 8 % at 20 rad/s; the ring turns at 3 rad/s, the little duck orbits at 6
		local g = if age < 0 then 0 else math.min(1, age / 0.3)
		local pulse = 1 + 0.08 * math.sin(t * 20)
		local k = g * pulse
		hv.core.Size = Vector3.one * 2 * S * math.max(k, 0.01)
		hv.shell.Size = Vector3.one * 3 * S * math.max(k, 0.01)
		hv.core.CFrame = CFrame.new(hv.p); hv.shell.CFrame = CFrame.new(hv.p); hv.pull.CFrame = CFrame.new(hv.p)
		hv.ring.Size = Vector3.new(4.4 * S * math.max(g, 0.01), 0.05, 4.4 * S * math.max(g, 0.01))
		hv.ring.CFrame = CFrame.new(hv.p) * CFrame.Angles(0.35, hv.ang * 3, 0)
		local oa = hv.ang * 6
		hv.orbit:PivotTo(CFrame.new(hv.p + Vector3.new(math.cos(oa), 0.15, math.sin(oa)) * 2.6 * S * g) * CFrame.Angles(0, -oa, 0))
		local em = hv.pull:FindFirstChildOfClass("ParticleEmitter")
		if em then em.Enabled = age >= 0 end
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
	-- (a violet squeeze over the view while a hole eats your speed: web duck.js, opacity holeF x 1.5, at most 0.9)
	local a = math.min(0.9, holeF * 1.5)
	squeeze.Enabled = a > 0.01
	if squeeze.Enabled then
		squeeze.TintColor = Color3.new(1, 1, 1):Lerp(Color3.fromRGB(196, 170, 255), a)
		squeeze.Saturation = -0.5 * a
		squeeze.Contrast = 0.25 * a
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
		tip.Text = ("press the number on an ad to close it  ·  %d left"):format(#ads.live + #ads.queue)
	end
end
UserInputService.InputBegan:Connect(function(io: InputObject, gp: boolean)
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
			if not g then g = itemModel("nvg"); g:ScaleTo(1.25); g.Parent = folder; headGoggles[pl] = g end
			(g :: Model):PivotTo(head.CFrame * CFrame.new(0, 0.15, -0.55))
		elseif g then g:Destroy(); headGoggles[pl] = nil end
	end
	for pl, g in headGoggles do if not pl.Parent then g:Destroy(); headGoggles[pl] = nil end end
end
-- the flash: N or the middle mouse button, goggles on
UserInputService.InputBegan:Connect(function(io: InputObject, gp: boolean)
	if gp or not (io.KeyCode == Enum.KeyCode.N or io.UserInputType == Enum.UserInputType.MouseButton3) then return end
	if me:GetAttribute("Item") ~= "nvg" or me:GetAttribute("NV") ~= true or menuOpen() or inHub() then return end
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
		-- (the screen faces both ways, so the one sitting it can read it too)
		local sg2 = sg:Clone(); sg2.Face = Enum.NormalId.Back; sg2.Parent = scr
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

-- ---------------------------------------------------------------- what the server says
local function onFx(m: any)
	if type(m) ~= "table" then return end
	local k = m.k
	if k == "ps" then addFlying(m)
	elseif k == "pb" then
		local v = if type(m.id) == "number" then flying[m.id] else nil
		if v and typeof(m.p) == "Vector3" and typeof(m.v) == "Vector3" then
			v.off += v.p - m.p -- (a small correction slides in instead of jumping)
			v.p, v.v = m.p, m.v
		end
	elseif k == "pd" then dropFlying(m.id)
	elseif k == "boom" and typeof(m.p) == "Vector3" then boom(m.p, if type(m.r) == "number" then m.r else 7.5 * S)
	elseif k == "smoke" and type(m.id) == "number" and typeof(m.p) == "Vector3" then
		addCloud(m.id, m.p, if type(m.r) == "number" then m.r else 6.5 * S, if type(m.left) == "number" then m.left else 10)
	elseif k == "bub+" and type(m.id) == "number" and typeof(m.p) == "Vector3" then
		addDome(m.id, m.p, if type(m.r) == "number" then m.r else 4.4 * S, if type(m.left) == "number" then m.left else 7, m.fresh ~= false and type(m.o) == "number")
	elseif k == "bubx" then dropDome(m.id)
	elseif k == "bubhit" and typeof(m.p) == "Vector3" then domeHit(m.p)
	elseif k == "medkit" then healFx(if typeof(m.model) == "Instance" then m.model else nil, m.o == me.UserId)
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
	hudStep()
end)
