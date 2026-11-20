--!strict
-- THE GIFT PRESENT (18 Nov 2026, the owner: "the player gets notified by having a present box come up and appear, use
-- squash and stretch, it comes up, spins and opens to reveal what you've received!"). the owner's GIFT tab
-- (OwnerDev.server) sends the receiver DevFx { k = "gift", from, items }. here, on the receiver's screen:
--   a chunky present (a navy box, its lid, a gold ribbon and bow: few big shapes, one accent) in a ViewportFrame at the
--   middle of the screen, under a small "GIFT FROM <giver>" line:
--     1. RISE: it pops up from below, squashed as it comes, stretched as it rises, settling with an overshoot (pop)
--     2. WOBBLE: two quick wobbles, then a fast SPIN that slows (whoosh)
--     3. OPEN: the lid pops off with a squash, a burst of light and confetti (loot_pop)
--     4. REVEAL: what came, on the loot opening's own cards (LootOpening.card: the picture, the name, the rarity colour),
--        "x5" on a count; a bundle as a grid. the sting is the loot win of the best rarity in it
--   any click, tap or key jumps to the reveal; CLOSE (or B on a pad) puts it away
--   in a MATCH it waits (the toast says it came: OwnerDev.client): it plays between rounds (LoadoutWindow), at the end,
--   or back in the hub; never over a live round (one still up when the round goes live is put away at once, and plays
--   again at the next break if its cards weren't shown yet). one at a time, in the order they came
-- sounds are recordings from the place's library (Sfx): pop, slap_whoosh, loot_pop, loot_win_<rarity>. no voices
-- Studio photos: player attribute GiftHold = "rise" / "spin" / "reveal" holds the present at that moment
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")

local me = Players.LocalPlayer
local J = script.Parent
local T = require(J:WaitForChild("Theme")) :: any
local MenuCursor = require(J:WaitForChild("MenuCursor")) :: any
local Sfx: any = nil
local Opening: any = nil
local function mods()
	if Sfx == nil then local ok, m = pcall(require, J:WaitForChild("Sfx")); Sfx = if ok then m else false end
	if Opening == nil then local ok, m = pcall(require, J:WaitForChild("LootOpening")); Opening = if ok then m else false end
end
local function sound(name: string, vol: number?)
	if Sfx then pcall(Sfx.play, name, nil, vol) end
end
-- (19 Nov, the owner's XP and UNLOCKS) pictures the loot cards don't draw: a weapon (an unlock, or a mastery gift) as
-- the loadout shows it (GunPreview), and it.big ("XP", "LV 10", "ALL") in large letters over the picture
local Preview: any = nil
local function extraPicture(slot: Instance, it: any)
	local pic = slot:FindFirstChild("Pic", true)
	if not pic or not pic:IsA("GuiObject") then return end
	local wid = if type(it.weapon) == "string" then it.weapon elseif it.type == "weapon" and it.id ~= "all" then it.id else nil
	if wid then
		if Preview == nil then local ok, m = pcall(require, J:WaitForChild("GunPreview", 5)); Preview = if ok then m else false end
		if Preview then
			pcall(function()
				local vp, cam = Preview.viewport(pic, { Name = "Gun", Size = UDim2.fromScale(1, 1), ZIndex = 2 })
				Preview.put(vp, cam, wid)
			end)
		end
	end
	if type(it.big) == "string" then
		local l = T.text(pic, "Big", it.big, if wid then 26 else 46, T.ACCENT, T.FONT_HEAVY, Enum.TextXAlignment.Center)
		l.ZIndex = 4
		if wid then
			l.AnchorPoint = Vector2.new(0, 1); l.Position = UDim2.new(0, 0, 1, -6); l.Size = UDim2.new(1, 0, 0, 30)
		else
			l.Size = UDim2.fromScale(1, 1)
		end
	end
end

local queue: { any } = {}
local playing = false
local closeNow = false -- (CLOSE, or B on a pad)

-- ------------------------------------------------------------------ the present (built once, cloned per show)
local NAVY, NAVY_LID, GOLD = Color3.fromRGB(54, 64, 86), Color3.fromRGB(62, 74, 98), Color3.fromRGB(232, 190, 96)
local function part(m: Model, name: string, size: Vector3, cf: CFrame, color: Color3, shape: Enum.PartType?): Part
	local p = Instance.new("Part")
	p.Name = name
	if shape then p.Shape = shape end
	p.Size = size
	p.CFrame = cf
	p.Color = color
	p.Material = Enum.Material.SmoothPlastic
	p.Anchored = true
	p.CanCollide = false
	p.TopSurface, p.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
	p.Parent = m
	return p
end
local function present(): (Model, Model)
	local box = Instance.new("Model")
	box.Name = "Present"
	-- the box: a body with soft edges (a slab and two cross slabs make the rounded look), the ribbon round it
	part(box, "Body", Vector3.new(4, 3.2, 4), CFrame.new(0, 1.6, 0), NAVY)
	part(box, "EdgeX", Vector3.new(4.2, 2.8, 3.6), CFrame.new(0, 1.6, 0), NAVY)
	part(box, "EdgeZ", Vector3.new(3.6, 2.8, 4.2), CFrame.new(0, 1.6, 0), NAVY)
	part(box, "RibbonX", Vector3.new(4.26, 3.22, 0.7), CFrame.new(0, 1.6, 0), GOLD)
	part(box, "RibbonZ", Vector3.new(0.7, 3.22, 4.26), CFrame.new(0, 1.6, 0), GOLD)
	box.PrimaryPart = box:FindFirstChild("Body") :: BasePart
	local lid = Instance.new("Model")
	lid.Name = "Lid"
	part(lid, "Top", Vector3.new(4.5, 0.9, 4.5), CFrame.new(0, 3.55, 0), NAVY_LID)
	part(lid, "RibbonX", Vector3.new(4.56, 0.92, 0.7), CFrame.new(0, 3.55, 0), GOLD)
	part(lid, "RibbonZ", Vector3.new(0.7, 0.92, 4.56), CFrame.new(0, 3.55, 0), GOLD)
	-- the bow: two fat loops (squashed balls, tilted out) and a knot
	part(lid, "LoopL", Vector3.new(1.5, 0.9, 0.9), CFrame.new(-0.7, 4.35, 0) * CFrame.Angles(0, 0, math.rad(28)), GOLD, Enum.PartType.Ball)
	part(lid, "LoopR", Vector3.new(1.5, 0.9, 0.9), CFrame.new(0.7, 4.35, 0) * CFrame.Angles(0, 0, math.rad(-28)), GOLD, Enum.PartType.Ball)
	part(lid, "Knot", Vector3.new(0.75, 0.75, 0.75), CFrame.new(0, 4.25, 0), Color3.fromRGB(214, 170, 78), Enum.PartType.Ball)
	lid.PrimaryPart = lid:FindFirstChild("Top") :: BasePart
	lid.Parent = box
	return box, lid
end

-- ------------------------------------------------------------------ the screen
local gui = Instance.new("ScreenGui")
gui.Name = "JankGiftBox"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = true
gui.DisplayOrder = 85
gui.Enabled = false
gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
gui.Parent = me:WaitForChild("PlayerGui")
local dim = T.new("TextButton", { Name = "Dim", Text = "", AutoButtonColor = false, BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 1,
	BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), Selectable = false }, gui)
local stage = T.new("Frame", { Name = "Stage", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
	Size = UDim2.fromOffset(760, 520) }, gui)
local scale = T.new("UIScale", {}, stage)
local head = T.text(stage, "From", "", 16, T.ACCENT, T.FONT_BOLD, Enum.TextXAlignment.Center)
head.Position = UDim2.fromOffset(0, 8); head.Size = UDim2.new(1, 0, 0, 22)
local glow = T.new("Frame", { Name = "Glow", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(10, 10),
	BackgroundColor3 = Color3.fromRGB(255, 226, 150), BackgroundTransparency = 1, BorderSizePixel = 0, ZIndex = 1 }, stage)
T.corner(glow, 999)
T.new("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(1, 1) }) }, glow)
local vpHolder = T.new("Frame", { Name = "Box", AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, -40), Size = UDim2.fromOffset(300, 300),
	BackgroundTransparency = 1, ZIndex = 2 }, stage)
local vp = T.new("ViewportFrame", { Name = "View", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Ambient = Color3.fromRGB(150, 155, 170),
	LightColor = Color3.fromRGB(255, 248, 236), LightDirection = Vector3.new(-1, -2, -1.5), ZIndex = 2 }, vpHolder)
local cam = Instance.new("Camera")
cam.FieldOfView = 30
cam.Parent = vp
vp.CurrentCamera = cam
local reveal = T.new("Frame", { Name = "Reveal", BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 40), Size = UDim2.new(1, 0, 1, -100), ZIndex = 5, Visible = false }, stage)
local close = T.new("TextButton", { Name = "Close", Text = "CLOSE", FontFace = T.FONT_BOLD, TextSize = 15, AutoButtonColor = true, TextColor3 = T.INK,
	BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, -6), Size = UDim2.fromOffset(160, 40),
	Visible = false, ZIndex = 6 }, stage)
T.corner(close, 6)
local confetti = T.new("Frame", { Name = "Confetti", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = 4 }, stage)

local function fit()
	local v = workspace.CurrentCamera and workspace.CurrentCamera.ViewportSize or Vector2.new(1280, 720)
	scale.Scale = math.clamp(math.min(v.X / 800, v.Y / 580), 0.5, 1.4)
end

-- a pad: B backs out, the selection sits on CLOSE (PadNav's Pad.MENUS, once PadNav has put it there)
task.spawn(function()
	local pm = J:FindFirstChild("Pad")
	local ok, Pad = false, nil
	if pm and pm:IsA("ModuleScript") then ok, Pad = pcall(require, pm) end
	if not ok or type(Pad) ~= "table" then return end
	for _ = 1, 60 do
		if type((Pad :: any).MENUS) == "table" then
			(Pad :: any).MENUS.giftbox = { gui = "JankGiftBox", back = function() closeNow = true end,
				first = function() return if close.Visible then close else nil end }
			return
		end
		task.wait(1)
	end
end)

-- ------------------------------------------------------------------ easing
local function ease(t: number): number return 1 - (1 - t) ^ 3 end
local function back(t: number): number local c = 1.7; return 1 + (c + 1) * (t - 1) ^ 3 + c * (t - 1) ^ 2 end
local function lerp(a: number, b: number, t: number): number return a + (b - a) * t end

-- the reveal: one card per thing (a count on it), a grid when there are several
local function drawReveal(items: { any })
	for _, c in reveal:GetChildren() do c:Destroy() end
	mods()
	local n = math.min(#items, 12)
	local cw, ch = 176, 212
	if Opening and Opening.CARD then cw, ch = Opening.CARD.w, Opening.CARD.h end
	local cols = math.min(n, if n <= 4 then n else 6)
	local rows = math.ceil(n / cols)
	local k = math.min(1, 720 / (cols * (cw + 12)), 400 / (rows * (ch + 12)))
	local holder = T.new("Frame", { Name = "Cards", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(cols * (cw + 12) - 12, rows * (ch + 12) - 12), ZIndex = 5 }, reveal)
	T.new("UIScale", { Scale = k }, holder)
	for i = 1, n do
		local it = items[i]
		local col, row = (i - 1) % cols, (i - 1) // cols
		local slot = T.new("Frame", { Name = "Slot" .. i, BackgroundTransparency = 1, Position = UDim2.fromOffset(col * (cw + 12), row * (ch + 12)),
			Size = UDim2.fromOffset(cw, ch), ZIndex = 5 }, holder)
		local s = T.new("UIScale", { Scale = 0.2 }, slot)
		local ok = Opening and type(Opening.card) == "function" and pcall(Opening.card, slot, it, 0)
		if ok and (it.type == "xp" or it.type == "mastery" or it.type == "weapon") then extraPicture(slot, it) end
		if not ok then
			local c = T.new("Frame", { BackgroundColor3 = T.CARD, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1) }, slot)
			T.corner(c, 6)
			local l = T.text(c, "Name", tostring(it.name), 18, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Center)
			l.Size = UDim2.fromScale(1, 1)
		end
		if (tonumber(it.n) or 1) > 1 then
			local badge = T.new("TextLabel", { Name = "Count", BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, AnchorPoint = Vector2.new(1, 0),
				Position = UDim2.new(1, -8, 0, 8), Size = UDim2.fromOffset(0, 26), AutomaticSize = Enum.AutomaticSize.X, FontFace = T.FONT_HEAVY,
				TextSize = 17, Text = "x" .. tostring(it.n), TextColor3 = T.INK, ZIndex = 9 }, slot)
			T.new("UIPadding", { PaddingLeft = UDim.new(0, 8), PaddingRight = UDim.new(0, 8) }, badge)
			T.corner(badge, 5)
		end
		task.delay(0.06 * (i - 1), function() T.tween(s, 0.32, { Scale = 1 }, Enum.EasingStyle.Back, Enum.EasingDirection.Out) end)
	end
	reveal.Visible = true
end

-- confetti: small flat bits flung out of the box and falling
local function burst()
	local cols = { T.ACCENT, Color3.fromRGB(240, 242, 245), Color3.fromRGB(120, 168, 222), Color3.fromRGB(232, 190, 96) }
	local origin = Vector2.new(380, 300)
	for i = 1, 36 do
		local f = T.new("Frame", { BackgroundColor3 = cols[(i % #cols) + 1], BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.fromOffset(origin.X, origin.Y), Size = UDim2.fromOffset(math.random(6, 11), math.random(10, 16)), Rotation = math.random(0, 360), ZIndex = 4 }, confetti)
		local a = math.rad(math.random(200, 340))
		local sp = math.random(260, 520)
		local vx, vy = math.cos(a) * sp, math.sin(a) * sp
		local t0 = os.clock()
		local conn: RBXScriptConnection
		conn = RunService.RenderStepped:Connect(function()
			local t = os.clock() - t0
			if t > 1.6 or not f.Parent then conn:Disconnect(); f:Destroy(); return end
			f.Position = UDim2.fromOffset(origin.X + vx * t, origin.Y + vy * t + 520 * t * t)
			f.Rotation += 9
			f.BackgroundTransparency = math.clamp((t - 1.0) / 0.6, 0, 1)
		end)
	end
end

-- ------------------------------------------------------------------ one show
local function show(g: any)
	playing = true
	mods()
	fit()
	for _, c in vp:GetChildren() do if c:IsA("Model") or c:IsA("WorldModel") then c:Destroy() end end
	for _, c in confetti:GetChildren() do c:Destroy() end
	reveal.Visible = false
	close.Visible = false
	head.Text = "GIFT FROM " .. string.upper(string.sub(tostring(g.from or ""), 1, 30))
	head.TextTransparency = 0
	local box, lid = present()
	box.Parent = vp
	-- every part's rest place and size from the box's base, to squash and stretch it for real (a viewport's frame can't)
	type Bit = { p: BasePart, cf: CFrame, size: Vector3, lid: boolean }
	local bits: { Bit } = {}
	for _, d in box:GetDescendants() do
		if d:IsA("BasePart") then table.insert(bits, { p = d, cf = d.CFrame, size = d.Size, lid = d:IsDescendantOf(lid) }) end
	end
	local lidOff = CFrame.identity
	cam.CFrame = CFrame.lookAt(Vector3.new(0, 4.6, 13.5), Vector3.new(0, 2.3, 0))
	gui.Enabled = true
	MenuCursor.set("giftbox", true, function() return gui.Enabled end)
	T.tween(dim, 0.25, { BackgroundTransparency = 0.45 })
	local skip = false
	local conns = {}
	table.insert(conns, dim.Activated:Connect(function() skip = true end))
	table.insert(conns, UIS.InputBegan:Connect(function(io: InputObject)
		if io.UserInputType == Enum.UserInputType.Keyboard or io.UserInputType == Enum.UserInputType.MouseButton1
			or io.UserInputType == Enum.UserInputType.Touch or io.UserInputType == Enum.UserInputType.Gamepad1 then skip = true end
	end))
	closeNow = false
	table.insert(conns, close.Activated:Connect(function() closeNow = true end))
	-- (a present begun in a break is put away the moment the round goes live: never over a live round. if its cards
	-- weren't shown yet, it plays again at the next break; found in the v1054 test)
	local live = false
	table.insert(conns, RunService.Heartbeat:Connect(function()
		if not live and me:GetAttribute("Zone") == "match" and me:GetAttribute("LoadoutWindow") == nil and me:GetAttribute("GiftHold") == nil then
			live = true
			skip = true
			closeNow = true
		end
	end))

	vpHolder.Size = UDim2.fromOffset(300, 300)
	local function setBox(y: number, sx: number, sy: number, yaw: number, tilt: number)
		vpHolder.Position = UDim2.new(0.5, 0, 1, -40 + y)
		local turn = CFrame.Angles(0, yaw, 0) * CFrame.Angles(0, 0, tilt)
		for _, b in bits do
			local pos = b.cf.Position
			local rot = b.cf - pos
			local at = CFrame.new(pos.X * sx, pos.Y * sy, pos.Z * sx) * rot
			if b.lid then at = lidOff * at end
			b.p.Size = Vector3.new(b.size.X * sx, b.size.Y * sy, b.size.Z * sx)
			b.p.CFrame = turn * at
		end
	end
	local function held(name: string): boolean
		return RunService:IsStudio() and me:GetAttribute("GiftHold") == name
	end
	local function run(dur: number, name: string, f: (number) -> ())
		local t0 = os.clock()
		while not skip do
			local t = math.clamp((os.clock() - t0) / dur, 0, 1)
			if held(name) then t = 0.5 end
			f(t)
			if t >= 1 and not held(name) then break end
			RunService.RenderStepped:Wait()
		end
	end
	-- 1. rise: from below, squashed coming in, stretched as it goes up, an overshoot to rest
	sound("pop", 0.8)
	run(0.55, "rise", function(t)
		local e = back(t)
		local y = lerp(260, 0, e)
		local stretch = math.sin(t * math.pi) -- (most stretched mid-flight)
		local sx = if t < 0.15 then lerp(1.25, 1, t / 0.15) else 1 - 0.12 * stretch
		local sy = if t < 0.15 then lerp(0.75, 1, t / 0.15) else 1 + 0.18 * stretch
		setBox(y, sx, sy, 0.4, 0)
	end)
	-- the landing squash
	run(0.18, "land", function(t)
		local k = math.sin(t * math.pi)
		setBox(0, 1 + 0.16 * k, 1 - 0.14 * k, 0.4, 0)
	end)
	-- 2. two wobbles, then a fast spin that slows
	run(0.45, "wobble", function(t)
		setBox(0, 1, 1, 0.4, math.sin(t * math.pi * 4) * 0.16 * (1 - t))
	end)
	if not live then sound("slap_whoosh", 0.6) end
	run(1.05, "spin", function(t)
		local yaw = 0.4 + ease(t) * math.pi * 6
		local k = math.sin(t * math.pi)
		setBox(-14 * k, 1 - 0.05 * k, 1 + 0.06 * k, yaw, 0)
	end)
	-- 3. the lid pops: the box squashes, the lid flies up and tumbles off, light and confetti
	run(0.12, "squash", function(t)
		setBox(0, 1 + 0.18 * t, 1 - 0.16 * t, 0.4, 0)
	end)
	if not live then sound("loot_pop", 0.9) end
	if not skip then burst() end
	glow.BackgroundTransparency = 0.15
	glow.Size = UDim2.fromOffset(40, 40)
	T.tween(glow, 0.5, { Size = UDim2.fromOffset(620, 620), BackgroundTransparency = 1 })
	run(0.5, "open", function(t)
		local e = ease(t)
		lidOff = CFrame.new(1.6 * e, 4.5 * e - 2.5 * t * t, 0) * CFrame.new(0, 3.55, 0) * CFrame.Angles(0, 0, -1.1 * e) * CFrame.new(0, -3.55, 0)
		setBox(0, lerp(1.18, 1, e), lerp(0.84, 1, e), 0.4, 0)
	end)
	if live then -- (the round went live before the cards: away, and again at the next break)
		table.insert(queue, 1, g)
		for _, c in conns do c:Disconnect() end
		T.tween(dim, 0.2, { BackgroundTransparency = 1 })
		gui.Enabled = false
		MenuCursor.set("giftbox", false)
		box:Destroy()
		playing = false
		return
	end
	-- 4. the reveal: the box fades back, the cards come in
	local items = if type(g.items) == "table" then g.items else {}
	local best = "common"
	local rank = { common = 1, rare = 2, epic = 3, legendary = 4, vip = 4 }
	for _, it in items do if (rank[it.rarity] or 0) > (rank[best] or 0) then best = it.rarity end end
	sound("loot_win_" .. (if best == "vip" then "legendary" else best), 0.8)
	T.tween(vpHolder, 0.25, { Size = UDim2.fromOffset(0, 0) })
	drawReveal(items)
	close.Visible = true
	skip = false
	while held("reveal") do RunService.RenderStepped:Wait() end
	-- (closed by CLOSE / B; a minute at most)
	local t0 = os.clock()
	while not closeNow and os.clock() - t0 < 60 do RunService.RenderStepped:Wait() end
	for _, c in conns do c:Disconnect() end
	T.tween(dim, 0.2, { BackgroundTransparency = 1 })
	gui.Enabled = false
	MenuCursor.set("giftbox", false)
	box:Destroy()
	playing = false
end

-- ------------------------------------------------------------------ when it may play
-- not over a live round: in a match only between rounds (LoadoutWindow) and never while a loot opening runs
local function free(): boolean
	if me:GetAttribute("Zone") == "match" and me:GetAttribute("LoadoutWindow") == nil then return false end
	if me:GetAttribute("LootOpening") ~= nil then return false end
	return true
end
task.spawn(function()
	while true do
		task.wait(0.4)
		if not playing and #queue > 0 and free() then
			local g = table.remove(queue, 1)
			local ok, err = pcall(show, g)
			if not ok then
				warn("[jankfire] gift present: " .. tostring(err))
				gui.Enabled = false
				MenuCursor.set("giftbox", false)
				playing = false
			end
		end
	end
end)

local Fx = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("DevFx", 60) :: RemoteEvent?
if Fx then
	Fx.OnClientEvent:Connect(function(d: any)
		if type(d) ~= "table" or d.k ~= "gift" or type(d.items) ~= "table" then return end
		if #queue >= 8 then return end -- (a run of gifts: the first eight play, the rest are in the save all the same)
		table.insert(queue, { from = d.from, items = d.items })
	end)
end
