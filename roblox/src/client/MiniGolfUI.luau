--!strict
-- SLAP GOLF, your side (shared/MiniGames.luau MG.GOLF and MG.L.golf; server/MiniGolf runs the round and owns the
-- dummies). MiniGames.client calls this like the other games' screens.
--   world (everyone near the course): the sounds and the juice of every shot from Ev (the slap's whoosh and smack, a
--          dust puff, the golfer's arm swinging the Hand Slapper; a bouncy post's boing, a rail's bonk; the cup's pop
--          with confetti; out of bounds), and the aim line from the dummy whose shot it is
--   your screen: the hole and its par, each golfer's strokes (this hole, and the round against par), whose shot it is,
--          the power meter while you charge, the result of each shot, the card between holes and at the end; in the
--          lobby the golfers and START (the first one in starts the round); AGAIN after a round
--   the camera: behind your dummy along your aim while it's your shot (turn it to aim), chasing a dummy in flight,
--          over the course in the lobby and between holes
--   keys: A / D or the arrow keys (or drag with the right button) aim, hold click or Space to charge, let go to slap.
--          a pad: the left stick aims, hold RT (or A) to charge. a phone: drag to aim, hold SLAP
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local TweenService = game:GetService("TweenService")
local MG = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("MiniGames")) :: any

local M = {}
local me = Players.LocalPlayer
local L = MG.L.golf
local GB = MG.GOLF
local function now(): number return workspace:GetServerTimeNow() end
local function flat(v: Vector3): Vector3 return Vector3.new(v.X, 0, v.Z) end
local function dirOf(yaw: number): Vector3 return Vector3.new(-math.sin(yaw), 0, -math.cos(yaw)) end

-- ------------------------------------------------------------------ reading the course
local function cardOf(model: Model, s: string): { number }
	local c = model:GetAttribute(s .. "_card")
	local out = {}
	if type(c) == "string" then for n in string.gmatch(c, "%-?%d+") do table.insert(out, tonumber(n) or 0) end end
	return out
end
local function orderOf(model: Model): { string }
	local o = model:GetAttribute("Order")
	local out = {}
	if type(o) == "string" then for s in string.gmatch(o, "[A-D]") do table.insert(out, s) end end
	return out
end
local function dummyTorso(model: Model, s: string): BasePart?
	local d = model:FindFirstChild("Dummy_" .. s)
	return d and d:FindFirstChild("UpperTorso") :: BasePart?
end
local function holePart(model: Model, i: number, name: string): BasePart?
	local course = model:FindFirstChild("Course")
	local h = course and course:FindFirstChild("Hole" .. i)
	return h and h:FindFirstChild(name) :: BasePart?
end
-- a golfer's body: a person's character, or a Studio stand-in's
local function golferBody(model: Model, s: string): Model?
	local id = model:GetAttribute("Id")
	for _, p in Players:GetPlayers() do
		if p:GetAttribute("MiniGameId") == id and p:GetAttribute("MiniSide") == s and p.Character then return p.Character end
	end
	for _, c in model:GetChildren() do
		if c:IsA("Model") and c.Name == "StandIn" and c:GetAttribute("MiniSide") == s then return c end
	end
	return nil
end
local function vsPar(model: Model, card: { number }): (number, number)
	local strokes, par = 0, 0
	for i, n in card do
		if n > 0 then strokes += n; par += GB.HOLES[i].par end
	end
	return strokes, strokes - par
end
local function parText(d: number): string return if d == 0 then "E" elseif d > 0 then "+" .. d else tostring(d) end

-- ------------------------------------------------------------------ the golfer's arm (the swing everyone sees)
local function joint(ch: Model, partName: string, name: string): (Instance?, CFrame)
	local p = ch:FindFirstChild(partName)
	local j = p and p:FindFirstChild(name)
	if not j then return nil, CFrame.identity end
	if j:IsA("Motor6D") then return j, j.C0 - j.C0.Position end
	if j:IsA("AnimationConstraint") then
		local a0 = (j :: AnimationConstraint).Attachment0
		return j, if a0 then a0.CFrame - a0.CFrame.Position else CFrame.identity
	end
	return nil, CFrame.identity
end
-- the arm's turn (degrees, in the body's frame: +x raises it forward) at a moment of the swing; nil = its own animation
local WIND = { -55, 10, 38 }
local HIT = { 78, -28, 12 }
local FOLLOW = { 100, -45, 8 }
local function lerp3(a: { number }, b: { number }, u: number): { number }
	u = math.clamp(u, 0, 1)
	u = u * u * (3 - 2 * u)
	return { a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u, a[3] + (b[3] - a[3]) * u }
end
local REST = { 0, 0, 0 }
local swings: { [Model]: { t0: number, from: { number } } } = {}
local winds: { [Model]: number } = {} -- (your own charge: the arm goes back as the meter fills)
local function armAt(ch: Model): ({ number }?, number)
	local s = swings[ch]
	if s then
		local t = os.clock() - s.t0
		if t < 0.09 then return lerp3(s.from, HIT, t / 0.09), 0.6 end
		if t < 0.2 then return HIT, 0.6 end
		if t < 0.36 then return lerp3(HIT, FOLLOW, (t - 0.2) / 0.16), 0.3 end
		if t < 0.75 then return lerp3(FOLLOW, REST, (t - 0.36) / 0.39), 0.3 end
		swings[ch] = nil
	end
	local w = winds[ch]
	if w and w > 0 then return lerp3(REST, WIND, w), 0.5 end
	return nil, 0
end
local function applyArm(ch: Model, turn: { number }, elbow: number)
	local hum = ch:FindFirstChildOfClass("Humanoid")
	local r6 = hum ~= nil and hum.RigType == Enum.HumanoidRigType.R6
	local sj, sf = joint(ch, if r6 then "Torso" else "RightUpperArm", if r6 then "Right Shoulder" else "RightShoulder")
	if sj then
		local rot = CFrame.Angles(math.rad(turn[1]), math.rad(turn[2]), math.rad(turn[3]));
		(sj :: any).Transform = sf:Inverse() * rot * sf
	end
	if not r6 then
		local ej, ef = joint(ch, "RightLowerArm", "RightElbow")
		if ej then (ej :: any).Transform = ef:Inverse() * CFrame.Angles(math.rad(elbow * 40), 0, 0) * ef end
	end
end
RunService.Stepped:Connect(function()
	for ch in swings do
		local turn, e = armAt(ch)
		if turn and ch.Parent then applyArm(ch, turn, e) end
	end
	for ch, w in winds do
		if not swings[ch] and w > 0 and ch.Parent then applyArm(ch, lerp3(REST, WIND, w), 0.5) end
	end
end)

-- ------------------------------------------------------------------ the juice
local function burst(at: Vector3, opts: { [string]: any }, n: number, life: number)
	local p = Instance.new("Part")
	p.Name = "GolfFx"; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Transparency = 1
	p.Size = Vector3.new(0.2, 0.2, 0.2); p.CFrame = CFrame.new(at)
	local e = Instance.new("ParticleEmitter")
	e.Enabled = false
	for k, v in opts do (e :: any)[k] = v end
	e.Parent = p
	p.Parent = workspace
	e:Emit(n)
	task.delay(life, function() p:Destroy() end)
end
local function dust(at: Vector3)
	burst(at, {
		Texture = "rbxasset://textures/particles/smoke_main.dds",
		Color = ColorSequence.new(Color3.fromRGB(214, 202, 178)),
		Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.8), NumberSequenceKeypoint.new(1, 2.6) }),
		Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 1) }),
		Lifetime = NumberRange.new(0.45, 0.7), Speed = NumberRange.new(5, 9), SpreadAngle = Vector2.new(180, 25),
		Drag = 5, Acceleration = Vector3.new(0, 2, 0), LightInfluence = 0.6,
	}, 16, 1.2)
end
local function confetti(at: Vector3)
	burst(at, {
		Color = ColorSequence.new({
			ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 196, 61)), ColorSequenceKeypoint.new(0.25, Color3.fromRGB(236, 232, 224)),
			ColorSequenceKeypoint.new(0.5, Color3.fromRGB(128, 152, 106)), ColorSequenceKeypoint.new(0.75, Color3.fromRGB(150, 62, 58)),
			ColorSequenceKeypoint.new(1, Color3.fromRGB(58, 84, 140)) }),
		Size = NumberSequence.new(0.32), Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.8, 0), NumberSequenceKeypoint.new(1, 1) }),
		Lifetime = NumberRange.new(1.2, 1.8), Speed = NumberRange.new(22, 34), SpreadAngle = Vector2.new(28, 28),
		Acceleration = Vector3.new(0, -34, 0), Drag = 1.2, Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-260, 260),
		EmissionDirection = Enum.NormalId.Top, LightInfluence = 0.4,
	}, 70, 2.2)
end
-- the flash on a slapped dummy, and the Slapper's hand squashing on the smack
local function flash(model: Model)
	local h = Instance.new("Highlight")
	h.FillColor = Color3.new(1, 1, 1); h.OutlineTransparency = 1; h.FillTransparency = 0.35
	h.DepthMode = Enum.HighlightDepthMode.Occluded
	h.Parent = model
	TweenService:Create(h, TweenInfo.new(0.18, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { FillTransparency = 1 }):Play()
	task.delay(0.2, function() h:Destroy() end)
end
local function squash(ch: Model?)
	local prop = ch and ch:FindFirstChild("MiniSlapper")
	if not prop then return end
	for _, d in prop:GetDescendants() do
		if d:IsA("BasePart") and d.Name ~= "Root" and (string.find(string.lower(d.Name), "hand", 1, true) or string.find(string.lower(d.Name), "palm", 1, true)) then
			local s = d.Size
			local t1 = TweenService:Create(d, TweenInfo.new(0.06, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(s.X * 1.3, s.Y * 0.6, s.Z * 1.25) })
			t1:Play()
			t1.Completed:Connect(function()
				TweenService:Create(d, TweenInfo.new(0.22, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Size = s }):Play()
			end)
		end
	end
end

-- ------------------------------------------------------------------ the world (everyone)
function M.world(model: Model, api: any): ((number) -> ())?
	local root = model:WaitForChild("Root", 10) :: BasePart?
	if not root then return nil end
	local last: string? = nil
	local function sfx(name: string, at: Vector3?, vol: number?, pitch: number?) api.Sfx.play(name, at, vol, pitch) end
	model:GetAttributeChangedSignal("Ev"):Connect(function()
		local e = model:GetAttribute("Ev")
		if type(e) ~= "string" or e == last then return end
		last = e
		local _, kind, side, x = string.match(e, "^(%d+):(%a+):([^:]+):(.*)$")
		if not kind or not side then return end
		local torso = dummyTorso(model, side)
		local at = if torso then torso.Position else root.Position
		local mine = me:GetAttribute("MiniGameId") == model:GetAttribute("Id")
		if kind == "slap" then
			local power = tonumber(x) or 0.5
			local body = golferBody(model, side)
			if body then
				swings[body] = { t0 = os.clock(), from = WIND }
				winds[body] = nil
				squash(body)
			end
			sfx("slap_whoosh", at, 0.6)
			task.delay(0.07, function() sfx("slap_hit", at, 0.6 + 0.4 * power, 1.05 - 0.15 * power) end)
			local d = model:FindFirstChild("Dummy_" .. side)
			if d and d:IsA("Model") then flash(d) end
			dust(at - Vector3.new(0, 2, 0))
			if mine and side == me:GetAttribute("MiniSide") then api.shake(0.01 + 0.02 * power, 0.22) end
		elseif kind == "boing" then
			sfx("boing", at, 0.7)
		elseif kind == "bonk" then
			sfx("bonk", at, 0.45)
		elseif kind == "cup" then
			local i = model:GetAttribute("Hole") :: number? or 1
			local cup = holePart(model, i, "Cup")
			local c = if cup then cup.Position else at
			sfx("popper", c, 0.8)
			sfx("pop", c, 0.7)
			confetti(c + Vector3.new(0, 0.5, 0))
			local fl = holePart(model, i, "Flag")
			if fl then
				local cf = fl.CFrame
				local t = TweenService:Create(fl, TweenInfo.new(0.12, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, 3, true), { CFrame = cf * CFrame.Angles(0, 0, math.rad(14)) })
				t:Play()
				t.Completed:Connect(function() fl.CFrame = cf end)
			end
		elseif kind == "oob" then
			sfx("whoops", at, 0.6)
		elseif kind == "done" then
			sfx("loot_win_rare", root.Position + Vector3.new(0, 8, 0), 0.5)
		end
	end)
	-- the aim line: from the dummy whose shot it is, along the aim, on the lawn
	local line = Instance.new("Part")
	line.Name = "GolfAim"; line.Anchored = true; line.CanCollide = false; line.CanQuery = false; line.CanTouch = false
	line.CastShadow = false; line.Material = Enum.Material.SmoothPlastic; line.Color = Color3.fromRGB(240, 238, 232)
	line.Transparency = 1; line.Size = Vector3.new(0.35, 0.05, 4)
	local tip = line:Clone()
	tip.Name = "GolfAimTip"; tip.Size = Vector3.new(0.9, 0.05, 0.9)
	line.Parent = workspace; tip.Parent = workspace
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	model.Destroying:Connect(function() line:Destroy(); tip:Destroy() end)
	return function(_dt: number)
		local turn = model:GetAttribute("Turn")
		local show = model:GetAttribute("State") == "play" and model:GetAttribute("Phase") == "aim" and type(turn) == "string" and turn ~= ""
		local torso = show and dummyTorso(model, turn :: string)
		if not torso then line.Transparency = 1; tip.Transparency = 1; return end
		local mineTurn = me:GetAttribute("MiniGameId") == model:GetAttribute("Id") and me:GetAttribute("MiniSide") == turn
		local yaw = if mineTurn and M.aimYaw then M.aimYaw else (model:GetAttribute("Aim") :: number? or 0)
		local d = dirOf(yaw)
		params.FilterDescendantsInstances = { model:FindFirstChild("Course") :: Instance }
		local hit = workspace:Raycast(torso.Position + Vector3.new(0, 1, 0), Vector3.new(0, -10, 0), params)
		local y = if hit then hit.Position.Y + 0.06 else torso.Position.Y - 2.5
		local len = 3 + (if mineTurn then (M.charge or 0) * 7 else 0)
		local from = Vector3.new(torso.Position.X, y, torso.Position.Z) + d * 1.2
		line.Size = Vector3.new(0.35, 0.05, len)
		line.CFrame = CFrame.lookAt(from + d * len / 2, from + d * len)
		tip.CFrame = CFrame.lookAt(from + d * (len + 0.2), from + d * (len + 1)) * CFrame.Angles(0, math.rad(45), 0)
		line.Transparency = 0.25; tip.Transparency = 0.25
	end
end

-- ------------------------------------------------------------------ your screen
local S: { [string]: any } = {}
M.aimYaw = nil :: number?
M.charge = nil :: number?

local function send(api: any, d: any) api.send(d) end

local function myTurn(): boolean
	local m = S.model
	return m ~= nil and m:GetAttribute("State") == "play" and m:GetAttribute("Phase") == "aim" and m:GetAttribute("Turn") == S.side
end

local function charge(on: boolean)
	if on then
		if not myTurn() or S.charging then return end
		S.charging = true
		S.chargeT = os.clock()
		S.meter.Visible = true
		return
	end
	if not S.charging then return end
	S.charging = false
	S.meter.Visible = false
	local p = M.charge or 0
	M.charge = nil
	local body = me.Character
	if body then winds[body] = nil end
	if myTurn() then send(S.api, { op = "slap", yaw = M.aimYaw or 0, power = p }) end
end

-- the card: a row per golfer, a column per hole, the round against par
local function buildCard(T: any, parent: Instance): Frame
	local card = T.plate(parent, "Card", UDim2.fromScale(0.5, 0.5), UDim2.fromOffset(640, 60))
	card.AnchorPoint = Vector2.new(0.5, 0.5)
	return card
end
local function fillCard(api: any)
	local T = api.T
	local m = S.model
	local card = S.card :: Frame
	for _, c in card:GetChildren() do if c:IsA("GuiObject") and c.Name ~= "UICorner" and c.Name ~= "UIStroke" then c:Destroy() end end
	local cols = { 150 }
	for _ = 1, #GB.HOLES do table.insert(cols, 52) end
	table.insert(cols, 70); table.insert(cols, 56)
	local function row(y: number, cells: { string }, colors: { Color3? }?, bold: boolean?)
		local x = 16
		for k, txt in cells do
			local t = T.text(card, "C", txt, if bold then 15 else 14, (colors and colors[k]) or T.TEXT, if bold then T.FONT_TITLE else T.FONT_BOLD,
				if k == 1 then Enum.TextXAlignment.Left else Enum.TextXAlignment.Center)
			t.Position = UDim2.fromOffset(x, y); t.Size = UDim2.fromOffset(cols[k], 22)
			x += cols[k]
		end
	end
	local head = { "HOLE" }
	local pars = { "PAR" }
	local parTotal = 0
	for i, h in GB.HOLES do table.insert(head, tostring(i)); table.insert(pars, tostring(h.par)); parTotal += h.par end
	table.insert(head, "TOTAL"); table.insert(head, "")
	table.insert(pars, tostring(parTotal)); table.insert(pars, "")
	row(14, head, { T.MUTED, T.MUTED, T.MUTED, T.MUTED, T.MUTED, T.MUTED, T.MUTED, T.MUTED, T.MUTED }, true)
	row(38, pars, { T.MUTED, T.MUTED, T.MUTED, T.MUTED, T.MUTED, T.MUTED, T.MUTED, T.MUTED, T.MUTED })
	local y = 66
	local hole = (m:GetAttribute("Hole") :: number?) or 1
	for _, s in orderOf(m) do
		local c = cardOf(m, s)
		local cells = { string.upper(tostring(m:GetAttribute(s .. "Name") or s)) }
		local colors: { Color3? } = { if s == S.side then T.ACCENT else T.TEXT }
		for i = 1, #GB.HOLES do
			local n = c[i] or 0
			table.insert(cells, if n > 0 then tostring(n) else "·")
			table.insert(colors, if n > 0 and n < GB.HOLES[i].par then T.ACCENT elseif i == hole and m:GetAttribute("State") == "play" then T.SOFT else T.TEXT)
		end
		local strokes, d = vsPar(m, c)
		table.insert(cells, tostring(strokes)); table.insert(colors, T.TEXT)
		table.insert(cells, parText(d)); table.insert(colors, if d < 0 then T.ACCENT else T.MUTED)
		row(y, cells, colors)
		local dot = T.new("Frame", { Name = "Dot", BackgroundColor3 = GB.COLORS[s], BorderSizePixel = 0, Position = UDim2.fromOffset(4, y + 7), Size = UDim2.fromOffset(8, 8) }, card)
		T.corner(dot, 4)
		y += 26
	end
	card.Size = UDim2.fromOffset(640, y + 14)
end

local function layout()
	local api = S.api
	local T = api.T
	local m = S.model
	local st = m:GetAttribute("State")
	local host = m:GetAttribute("Host") == S.side
	for _, b in S.panel:GetChildren() do if b:IsA("GuiButton") then b.Visible = false end end
	S.card.Visible = st == "between" or st == "done"
	if S.card.Visible then fillCard(api) end
	S.lobby.Visible = st == "lobby"
	local first: GuiObject? = nil
	if st == "lobby" then
		local names = {}
		for _, s in orderOf(m) do table.insert(names, string.upper(tostring(m:GetAttribute(s .. "Name") or s))) end
		S.lobbyL.Text = table.concat(names, "   ·   ")
		S.lobbySub.Text = if #names < #GB.SIDES then "UP TO 4 GOLFERS" else ""
		if host then S.startB.Visible = true; S.startB.Text = "START"; first = S.startB
		else S.lobbySub.Text = "WAITING FOR " .. string.upper(tostring(m:GetAttribute(tostring(m:GetAttribute("Host")) .. "Name") or "THE HOST")) end
	elseif st == "done" then
		if host then S.startB.Visible = true; S.startB.Text = "AGAIN"; first = S.startB end
	end
	local y = 0
	for _, b in S.panel:GetChildren() do
		if b:IsA("GuiButton") and b.Visible then b.Position = UDim2.fromOffset(y, 0); y += 152 end
	end
	S.panel.Size = UDim2.fromOffset(math.max(0, y - 10), 42)
	api.nav(first ~= nil and api.padOn(), first)
end

-- the result of a shot, under the hole's line for a moment
local function say(text: string, color: Color3?)
	local T = S.api.T
	S.flash.Text = text
	S.flash.TextColor3 = color or T.TEXT
	S.flash.TextTransparency = 0
	local t0 = os.clock()
	S.flashT = t0
	task.delay(1.4, function()
		if S.flashT == t0 and S.flash then T.tween(S.flash, 0.5, { TextTransparency = 1 }, Enum.EasingStyle.Quad, Enum.EasingDirection.In) end
	end)
end

function M.open(api: any, model: Model, side: string)
	local T = api.T
	S = { api = api, model = model, side = side, conns = {}, charging = false }
	M.aimYaw = nil
	M.charge = nil
	local root = api.root
	-- the top: the hole, its par, and each golfer's strokes
	local top = T.plate(root, "Hole", UDim2.new(0.5, -330, 0, 16), UDim2.fromOffset(660, 58))
	S.holeL = T.text(top, "Hole", "", 22, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Left)
	S.holeL.Position = UDim2.fromOffset(18, 6); S.holeL.Size = UDim2.fromOffset(200, 26)
	S.parL = T.text(top, "Par", "", 13, T.MUTED, T.FONT_TITLE, Enum.TextXAlignment.Left)
	S.parL.Position = UDim2.fromOffset(18, 32); S.parL.Size = UDim2.fromOffset(200, 18)
	S.golfers = T.new("Frame", { Name = "Golfers", BackgroundTransparency = 1, Position = UDim2.fromOffset(200, 8), Size = UDim2.fromOffset(450, 42) }, top)
	-- the middle: whose shot, the result
	S.status = T.text(root, "Status", "", 26, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Center, true)
	S.status.AnchorPoint = Vector2.new(0.5, 0); S.status.Position = UDim2.new(0.5, 0, 0, 92); S.status.Size = UDim2.fromOffset(700, 32)
	S.sub = T.text(root, "Sub", "", 14, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Center, true)
	S.sub.AnchorPoint = Vector2.new(0.5, 0); S.sub.Position = UDim2.new(0.5, 0, 0, 124); S.sub.Size = UDim2.fromOffset(700, 18)
	S.flash = T.text(root, "Flash", "", 30, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Center, true)
	S.flash.AnchorPoint = Vector2.new(0.5, 0.5); S.flash.Position = UDim2.fromScale(0.5, 0.34); S.flash.Size = UDim2.fromOffset(700, 36)
	S.flash.TextTransparency = 1
	-- the power meter
	local meter = T.plate(root, "Meter", UDim2.new(0.5, -200, 1, -118), UDim2.fromOffset(400, 44))
	meter.Visible = false
	S.meter = meter
	local ml = T.text(meter, "Label", "POWER", 12, T.MUTED, T.FONT_TITLE, Enum.TextXAlignment.Left)
	ml.Position = UDim2.fromOffset(14, 4); ml.Size = UDim2.fromOffset(120, 14)
	local track = T.new("Frame", { Name = "Track", BackgroundColor3 = T.TRACK, BorderSizePixel = 0, Position = UDim2.fromOffset(14, 22), Size = UDim2.new(1, -28, 0, 12) }, meter)
	T.corner(track, 6)
	S.fill = T.new("Frame", { Name = "Fill", BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Size = UDim2.fromScale(0, 1) }, track)
	T.corner(S.fill, 6)
	-- the lobby, the card, the buttons
	S.lobby = T.new("Frame", { Name = "Lobby", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0.32, 0), Size = UDim2.fromOffset(700, 60) }, root)
	S.lobbyL = T.text(S.lobby, "Names", "", 22, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Center, true)
	S.lobbyL.Size = UDim2.fromOffset(700, 28)
	S.lobbySub = T.text(S.lobby, "Sub", "", 14, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Center, true)
	S.lobbySub.Position = UDim2.fromOffset(0, 32); S.lobbySub.Size = UDim2.fromOffset(700, 18)
	S.card = buildCard(T, root)
	S.card.Visible = false
	S.panel = T.new("Frame", { Name = "Panel", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0.32, 70), Size = UDim2.fromOffset(142, 42) }, root)
	S.startB = api.button(S.panel, "Start", "START", UDim2.new(), UDim2.fromOffset(142, 42), true)
	S.startB.Activated:Connect(function() send(api, { op = "start" }) end)
	S.keys = T.text(root, "Keys", "", 13, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center, true)
	S.keys.AnchorPoint = Vector2.new(0.5, 1); S.keys.Position = UDim2.new(0.5, 0, 1, -16); S.keys.Size = UDim2.fromOffset(900, 18)
	-- a phone: SLAP (hold), and dragging anywhere else turns the aim
	if api.isTouch() then
		local b = api.button(root, "Slap", "SLAP", UDim2.new(1, -80, 1, -130), UDim2.fromOffset(100, 100), true)
		b.AnchorPoint = Vector2.new(0.5, 0.5)
		T.corner(b, 50)
		b.MouseButton1Down:Connect(function() charge(true) end)
		b.MouseButton1Up:Connect(function() charge(false) end)
		b.MouseLeave:Connect(function() charge(false) end)
		table.insert(S.conns, UIS.TouchMoved:Connect(function(io: InputObject, gp: boolean)
			if gp or not myTurn() then return end
			M.aimYaw = (M.aimYaw or 0) - io.Delta.X * 0.008
		end))
	end
	-- keys
	table.insert(S.conns, UIS.InputBegan:Connect(function(io: InputObject, gp: boolean)
		if gp then return end
		local k, ut = io.KeyCode, io.UserInputType
		if ut == Enum.UserInputType.MouseButton1 or k == Enum.KeyCode.ButtonR2 then charge(true)
		elseif ut == Enum.UserInputType.MouseButton2 then S.rmb = true end
	end))
	table.insert(S.conns, UIS.InputEnded:Connect(function(io: InputObject)
		local k, ut = io.KeyCode, io.UserInputType
		if ut == Enum.UserInputType.MouseButton1 or k == Enum.KeyCode.ButtonR2 then charge(false)
		elseif ut == Enum.UserInputType.MouseButton2 then S.rmb = false end
	end))
	table.insert(S.conns, UIS.InputChanged:Connect(function(io: InputObject)
		if io.UserInputType == Enum.UserInputType.MouseMovement and S.rmb and myTurn() then
			M.aimYaw = (M.aimYaw or 0) - io.Delta.X * 0.006
		end
	end))
	for _, a in { "State", "Host", "Order", "Hole", "AName", "BName", "CName", "DName", "A_card", "B_card", "C_card", "D_card" } do
		table.insert(S.conns, model:GetAttributeChangedSignal(a):Connect(layout))
	end
	-- each shot's result, said once
	table.insert(S.conns, model:GetAttributeChangedSignal("Ev"):Connect(function()
		local e = model:GetAttribute("Ev")
		local _, kind, who, x = string.match(tostring(e), "^(%d+):(%a+):([^:]+):(.*)$")
		if not kind then return end
		local name = if who == side then "YOU" else string.upper(tostring(model:GetAttribute(tostring(who) .. "Name") or ""))
		local n = tonumber(x) or 0
		if kind == "cup" then
			local i = (model:GetAttribute("Hole") :: number?) or 1
			local par = GB.HOLES[i].par
			say((if n == 1 then "HOLE IN ONE" elseif n == par - 1 then "BIRDIE" elseif n == par then "PAR" elseif n < par then "UNDER PAR" else "IN THE CUP")
				.. "  ·  " .. name .. "  ·  " .. n, if n < par then T.ACCENT else T.TEXT)
		elseif kind == "oob" then say("OUT OF BOUNDS  ·  +1", T.DANGER)
		elseif kind == "pickup" then say("PICKED UP  ·  " .. name, T.SOFT)
		end
	end))
	-- your aim starts at the cup each time your shot comes round
	table.insert(S.conns, model:GetAttributeChangedSignal("TurnT"):Connect(function()
		if model:GetAttribute("Turn") == side then
			M.aimYaw = model:GetAttribute("Aim") :: number?
			api.Sfx.play("click", nil, 0.5)
		end
	end))
	if model:GetAttribute("Turn") == side then M.aimYaw = model:GetAttribute("Aim") :: number? end
	layout()
	-- the camera
	local c = L.cam
	api.camera = function(): CFrame?
		local st = model:GetAttribute("State")
		local cf = (model:FindFirstChild("Root") :: BasePart?)
		if not cf then return nil end
		local base = cf.CFrame
		if st == "play" then
			local turn = model:GetAttribute("Turn")
			local torso = type(turn) == "string" and dummyTorso(model, turn) or nil
			if torso then
				if model:GetAttribute("Phase") == "fly" then
					local v = flat(torso.AssemblyLinearVelocity)
					local d = if v.Magnitude > 3 then v.Unit else dirOf((model:GetAttribute("Aim") :: number?) or 0)
					return CFrame.lookAt(torso.Position - d * c.chase + Vector3.new(0, c.chaseUp, 0), torso.Position)
				end
				local yaw = if turn == side and M.aimYaw then M.aimYaw else ((model:GetAttribute("Aim") :: number?) or 0)
				local d = dirOf(yaw)
				local p = torso.Position
				return CFrame.lookAt(p - d * c.back + Vector3.new(0, c.up, 0), p + d * c.ahead + Vector3.new(0, 0.5, 0))
			end
		end
		-- the lobby, between holes, the end: over the course, looking down its length from the front
		local i = (model:GetAttribute("Hole") :: number?) or 1
		local tee = holePart(model, if st == "between" then math.min(#GB.HOLES, i + 1) else i, "Tee")
		local at = if tee then tee.Position else base.Position
		return CFrame.lookAt(at + base.LookVector * -16 + Vector3.new(0, 18, 0), at + base.LookVector * 14)
	end
	api.fov = c.fov
	-- every frame: the top line, whose shot, aiming with keys and stick, the meter
	S.step = RunService.RenderStepped:Connect(function(dt: number)
		local st = model:GetAttribute("State")
		local hole = (model:GetAttribute("Hole") :: number?) or 1
		local h = GB.HOLES[hole]
		S.holeL.Text = if st == "lobby" then "SLAP GOLF" else ("HOLE " .. hole .. " / " .. #GB.HOLES)
		S.parL.Text = if st == "lobby" then "6 HOLES" else ("PAR " .. h.par)
		-- the golfers on the top line: a dot, the name, this hole's strokes, the round against par
		local order = orderOf(model)
		local sig = table.concat(order, ",") .. (st or "")
		for _, s in order do sig ..= tostring(model:GetAttribute(s .. "_card")) .. tostring(model:GetAttribute(s .. "_done")) end
		sig ..= tostring(model:GetAttribute("Turn"))
		if S.topSig ~= sig then
			S.topSig = sig
			for _, ch in S.golfers:GetChildren() do ch:Destroy() end
			local x = 0
			for _, s in order do
				local c2 = cardOf(model, s)
				local _, d = vsPar(model, c2)
				local here = c2[hole] or 0
				local active = model:GetAttribute("Turn") == s and st == "play"
				local f = T.new("Frame", { Name = s, BackgroundColor3 = if active then T.CARD_HI else T.CARD, BorderSizePixel = 0, Position = UDim2.fromOffset(x, 0), Size = UDim2.fromOffset(108, 42) }, S.golfers)
				T.corner(f, 8)
				local dot = T.new("Frame", { BackgroundColor3 = GB.COLORS[s], BorderSizePixel = 0, Position = UDim2.fromOffset(8, 8), Size = UDim2.fromOffset(8, 8) }, f)
				T.corner(dot, 4)
				local nm = T.text(f, "Name", string.upper(tostring(model:GetAttribute(s .. "Name") or s)), 11, if s == side then T.ACCENT else T.SOFT, T.FONT_TITLE, Enum.TextXAlignment.Left)
				nm.Position = UDim2.fromOffset(20, 3); nm.Size = UDim2.fromOffset(84, 16); nm.TextTruncate = Enum.TextTruncate.AtEnd
				local sc = T.text(f, "Score", (if model:GetAttribute(s .. "_done") then "IN " else "") .. here .. "   " .. parText(d), 14, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Left)
				sc.Position = UDim2.fromOffset(8, 20); sc.Size = UDim2.fromOffset(96, 18)
				x += 114
			end
		end
		-- whose shot
		local turn = model:GetAttribute("Turn")
		if st == "play" and type(turn) == "string" and turn ~= "" then
			local left = math.max(0, GB.SHOT_TIME - (now() - ((model:GetAttribute("TurnT") :: number?) or now())))
			if turn == side then
				S.status.Text = if model:GetAttribute("Phase") == "fly" then "" else "YOUR SHOT"
				S.status.TextColor3 = T.ACCENT
				S.sub.Text = if model:GetAttribute("Phase") == "aim" and left < 10 then ("%d"):format(math.ceil(left)) else ""
			else
				S.status.Text = if model:GetAttribute("Phase") == "fly" then "" else string.upper(tostring(model:GetAttribute(turn .. "Name") or ""))
				S.status.TextColor3 = T.TEXT
				S.sub.Text = ""
			end
		elseif st == "between" then
			S.status.Text = "HOLE " .. hole .. " DONE"; S.status.TextColor3 = T.TEXT; S.sub.Text = ""
		elseif st == "done" then
			-- the round's best: the fewest strokes
			local best, who = math.huge, nil
			for _, s in order do
				local n = vsPar(model, cardOf(model, s))
				if n < best then best, who = n, s end
			end
			S.status.Text = if who == side then "YOU WIN" elseif who then string.upper(tostring(model:GetAttribute(who .. "Name") or "")) .. " WINS" else "ROUND OVER"
			S.status.TextColor3 = if who == side then T.ACCENT else T.TEXT
			S.sub.Text = if #order == 1 then "" else ""
		else
			S.status.Text = ""; S.sub.Text = ""
		end
		-- aiming: keys and the stick turn it, and tell everyone where you're looking (a few times a second)
		if myTurn() then
			M.aimYaw = M.aimYaw or ((model:GetAttribute("Aim") :: number?) or 0)
			local turnBy = 0
			if not UIS:GetFocusedTextBox() then
				if UIS:IsKeyDown(Enum.KeyCode.A) or UIS:IsKeyDown(Enum.KeyCode.Left) then turnBy += 1 end
				if UIS:IsKeyDown(Enum.KeyCode.D) or UIS:IsKeyDown(Enum.KeyCode.Right) then turnBy -= 1 end
			end
			if api.padOn() then
				local x = api.Pad.stick(1).X
				if math.abs(x) > 0.15 then turnBy -= x end
			end
			M.aimYaw = (M.aimYaw :: number) + turnBy * dt * 1.4
			if os.clock() - (S.aimSent or 0) > 0.12 and S.aimSentYaw ~= M.aimYaw then
				S.aimSent = os.clock(); S.aimSentYaw = M.aimYaw
				send(api, { op = "aim", yaw = M.aimYaw })
			end
		elseif S.charging then
			S.charging = false; S.meter.Visible = false; M.charge = nil
		end
		-- the meter: up to full in CHARGE s, back down, up again: let go where you want it
		if S.charging then
			local u = ((os.clock() - S.chargeT) / GB.CHARGE) % 2
			local p = if u <= 1 then u else 2 - u
			M.charge = p
			S.fill.Size = UDim2.fromScale(math.max(0.02, p), 1)
			local body = me.Character
			if body then winds[body] = p end
		end
		S.keys.Text = if not myTurn() then ""
			elseif api.isTouch() then ""
			elseif api.padOn() then "LS AIM · HOLD RT OR A TO SLAP · LET GO"
			else "A / D AIM · RIGHT DRAG AIM · HOLD CLICK OR SPACE TO SLAP · LET GO"
	end)
end

function M.close()
	if S.step then S.step:Disconnect() end
	for _, c in S.conns or {} do c:Disconnect() end
	if S.api then S.api.camera = nil; S.api.fov = nil; S.api.nav(false) end
	local body = me.Character
	if body then winds[body] = nil end
	M.aimYaw = nil
	M.charge = nil
	S = {}
end

function M.remote(_d: any) end

-- Space and a pad's A: hold to charge, let go to slap
function M.space(down: boolean, _io: any): boolean
	if not S.model then return false end
	if down then
		if myTurn() then charge(true); return true end
	else
		if S.charging then charge(false); return true end
	end
	local st = S.model:GetAttribute("State")
	return st == "play" or st == "between"
end

function M.back(): boolean return false end

function M.confirmLeave(): string?
	if not S.model then return nil end
	if S.model:GetAttribute("State") == "play" or S.model:GetAttribute("State") == "between" then return "PRESS AGAIN TO LEAVE THE ROUND" end
	return nil
end

-- Studio test: MiniTest "golf:start", "golf:slap:<power>" (at the cup), "golf:slapyaw:<degrees>:<power>" (degrees off
-- the line to the cup, + to the left), "golf:aim:<degrees>" (turn your aim by that much)
function M.test(v: string): string
	local m = S.model
	if not m then return "not open" end
	if v == "golf:start" then send(S.api, { op = "start" }); return "start" end
	local p = tonumber(string.match(v, "^golf:slap:([%d%.]+)$"))
	if p then send(S.api, { op = "slap", yaw = (m:GetAttribute("Aim") :: number?) or 0, power = p }); return "slap " .. p end
	local deg, p2 = string.match(v, "^golf:slapyaw:(%-?[%d%.]+):([%d%.]+)$")
	if deg then
		send(S.api, { op = "slap", yaw = ((m:GetAttribute("Aim") :: number?) or 0) + math.rad(tonumber(deg) or 0), power = tonumber(p2) or 0.5 })
		return "slapyaw " .. deg
	end
	local a = tonumber(string.match(v, "^golf:aim:(%-?[%d%.]+)$"))
	if a then M.aimYaw = (M.aimYaw or 0) + math.rad(a); return "aim " .. a end
	return game:GetService("HttpService"):JSONEncode({ state = m:GetAttribute("State"), turn = m:GetAttribute("Turn"), phase = m:GetAttribute("Phase") })
end

return M
