--!strict
-- WallGrid: the wall box shows itself where you meet it (18 Nov 2026; the owner: "if you get close to wall box, should
-- like a small like grid appear where you grapple? like almost a hologram shield type thing but not the entire box just
-- in the section youre grappling to"). A walled arena's walls (Mat "bound") and the step round its edge (Mat "ledge",
-- above the scenery behind it: the arena's EdgeSeen) are invisible (tools/roblox/wallbox.py). Where your rope bites one,
-- where you come within NEAR studs of one, and where a bullet hits one (Fx.impact asks WallGridHit), a small round hex
-- grid shows on it in the game's calm hologram ice-blue, soft at its rim, and fades a moment after you leave or let go.
-- No text. Client only and cheap: the patches are built once (a part each, a SurfaceGui with the grid's lines in a
-- CanvasGroup) and then only moved and faded (one CFrame and one GroupTransparency each); the wall search is a few
-- rays ten times a second, and only in a walled arena (Main.server puts its SkyY on you there).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local player = Players.LocalPlayer
local camera = workspace.CurrentCamera

local SIZE = 13           -- studs across
local PPS = 24            -- the grid's pixels per stud
local HEX = 1.35          -- a cell's corner radius (studs)
local LINE = 3            -- px
local TINT = Color3.fromRGB(176, 226, 242) -- (Hologram.luau's ice-blue)
local NEAR = 10           -- studs: a wall this close shows its patch
local FADE_IN, FADE_OUT = 0.12, 0.6

-- ---------------------------------------------------------------- what counts as the wall box
local function shield(part: Instance?, y: number): boolean
	if not part or not part:IsA("BasePart") then return false end
	local m = part:GetAttribute("Mat")
	if m == "bound" then return true end
	if m == "ledge" then -- (the step: only above the scenery behind it; below that its face is a building or a cliff)
		local arena = part.Parent and part.Parent.Parent
		local seen = arena and arena:GetAttribute("EdgeSeen")
		return type(seen) == "number" and y > seen + 1
	end
	return false
end

-- ---------------------------------------------------------------- the patch: built once
local holder = Instance.new("Folder")
holder.Name = "WallGrid"
holder.Parent = camera

-- the hex lattice's edges inside the patch's circle, each once, with how strongly it shows (soft toward the rim)
local edges: { { number } } = {}
do
	local R = SIZE / 2
	local seen: { [string]: boolean } = {}
	local w, h = math.sqrt(3) * HEX, 1.5 * HEX -- (pointy-top cells: columns sqrt(3) r apart, rows 1.5 r)
	local function corner(cx: number, cy: number, k: number): (number, number)
		local a = math.rad(60 * k - 30)
		return cx + HEX * math.cos(a), cy + HEX * math.sin(a)
	end
	for row = -6, 6 do
		for col = -6, 6 do
			local cx = col * w + (if row % 2 == 0 then 0 else w / 2)
			local cy = row * h
			if cx * cx + cy * cy > (R + HEX) * (R + HEX) then continue end
			for k = 0, 5 do
				local x0, y0 = corner(cx, cy, k)
				local x1, y1 = corner(cx, cy, k + 1)
				local mx, my = (x0 + x1) / 2, (y0 + y1) / 2
				local key = ("%d,%d"):format(math.floor(mx * 20 + 0.5), math.floor(my * 20 + 0.5))
				if seen[key] then continue end
				seen[key] = true
				local t = math.sqrt(mx * mx + my * my) / R
				local s = math.clamp((1 - t) / 0.5, 0, 1) -- full in the middle, gone at the rim
				s = s * s * (3 - 2 * s)
				if s > 0.04 then table.insert(edges, { x0, y0, x1, y1, s }) end
			end
		end
	end
end

type Patch = { part: Part, gui: SurfaceGui, group: CanvasGroup, ring: Frame, stroke: UIStroke, lines: { Frame }, thick: number, alpha: number, target: number, rate: number,
	pos: Vector3?, normal: Vector3?, follow: Vector3?, flashT: number? }

local function circle(parent: Instance, scale: number, see: number): Frame
	local f = Instance.new("Frame")
	f.AnchorPoint = Vector2.new(0.5, 0.5); f.Position = UDim2.fromScale(0.5, 0.5); f.Size = UDim2.fromScale(scale, scale)
	f.BackgroundColor3 = TINT; f.BackgroundTransparency = see; f.BorderSizePixel = 0
	local c = Instance.new("UICorner"); c.CornerRadius = UDim.new(0.5, 0); c.Parent = f
	f.Parent = parent
	return f
end

local function makePatch(i: number): Patch
	local p = Instance.new("Part")
	p.Name = "Patch" .. i
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Transparency = 1; p.Size = Vector3.new(SIZE, SIZE, 0.05)
	p.CFrame = CFrame.new(0, -1e5, 0)
	local g = Instance.new("SurfaceGui")
	g.Face = Enum.NormalId.Front; g.LightInfluence = 0; g.Brightness = 2
	-- (a fixed canvas: a patch drawn bigger, for a far hook, keeps its grid and thickens its lines with it)
	g.SizingMode = Enum.SurfaceGuiSizingMode.FixedSize; g.CanvasSize = Vector2.new(SIZE * PPS, SIZE * PPS)
	g.Enabled = false
	g.Parent = p
	local cg = Instance.new("CanvasGroup")
	cg.Size = UDim2.fromScale(1, 1); cg.BackgroundTransparency = 1; cg.GroupTransparency = 1
	cg.Parent = g
	-- a faint glow, thicker in the middle (three soft discs), then the lines
	circle(cg, 1, 0.965); circle(cg, 0.66, 0.955); circle(cg, 0.34, 0.95)
	local px = SIZE * PPS
	local lines = {}
	for _, e in edges do
		local x0, y0, x1, y1, s = e[1], e[2], e[3], e[4], e[5]
		local f = Instance.new("Frame")
		f.AnchorPoint = Vector2.new(0.5, 0.5)
		f.Position = UDim2.fromOffset((0.5 + (x0 + x1) / 2 / SIZE) * px, (0.5 - (y0 + y1) / 2 / SIZE) * px)
		f.Size = UDim2.fromOffset(math.sqrt((x1 - x0) ^ 2 + (y1 - y0) ^ 2) * PPS + LINE * 0.5, LINE)
		f.Rotation = -math.deg(math.atan2(y1 - y0, x1 - x0))
		f.BackgroundColor3 = TINT; f.BackgroundTransparency = 1 - 0.85 * s; f.BorderSizePixel = 0
		f.Parent = cg
		table.insert(lines, f)
	end
	-- the ring that runs out from where a rope bites
	local ring = circle(cg, 0.1, 1)
	local st = Instance.new("UIStroke"); st.Color = TINT; st.Thickness = 4; st.Transparency = 1; st.Parent = ring
	p.Parent = holder
	return { part = p, gui = g, group = cg, ring = ring, stroke = st, lines = lines, thick = LINE, alpha = 0, target = 0, rate = 1 / FADE_OUT, pos = nil, normal = nil }
end

local hookP = makePatch(1)
local nearP = makePatch(2)
local hitP = { makePatch(3), makePatch(4) }
local nextHit = 1
local all = { hookP, nearP, hitP[1], hitP[2] }

local function place(pt: Patch, at: Vector3, n: Vector3, size: number?)
	pt.pos, pt.normal = at, n
	local sz = size or SIZE
	if math.abs(pt.part.Size.X - sz) > 0.05 then pt.part.Size = Vector3.new(sz, sz, 0.05) end
	local up = if math.abs(n.Y) > 0.9 then Vector3.zAxis else Vector3.yAxis
	pt.part.CFrame = CFrame.lookAt(at + n * 0.08, at + n * 2, up)
end
-- far away the grid's lines get thicker (once per placing, not per frame), so a patch 200 studs off still reads
local function lineFor(dist: number): number
	return math.floor(math.clamp(LINE * dist / 60, LINE, 10) + 0.5)
end
local function thicken(pt: Patch, t: number)
	if pt.thick == t then return end
	pt.thick = t
	for _, f in pt.lines do f.Size = UDim2.fromOffset(f.Size.X.Offset, t) end
	pt.stroke.Thickness = t + 1
end
local function show(pt: Patch, a: number)
	pt.target = a; pt.rate = 1 / FADE_IN
end
local function hide(pt: Patch)
	pt.target = 0; pt.rate = 1 / FADE_OUT
end
local function ripple(pt: Patch)
	pt.ring.Size = UDim2.fromScale(0.1, 0.1); pt.stroke.Transparency = 0.1
	TweenService:Create(pt.ring, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = UDim2.fromScale(0.9, 0.9) }):Play()
	TweenService:Create(pt.stroke, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 }):Play()
end

-- ---------------------------------------------------------------- where the rope bites
local params = RaycastParams.new()
params.FilterType = Enum.RaycastFilterType.Exclude
local function body(): (Model?, BasePart?)
	local ch = player.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	return ch, root
end

player:GetAttributeChangedSignal("HookAt"):Connect(function()
	local at = player:GetAttribute("HookAt")
	local ch, root = body()
	if typeof(at) ~= "Vector3" or not ch or not root then hide(hookP); return end
	local from = root.Position + Vector3.new(0, 1.5, 0)
	local d = at - from
	if d.Magnitude < 0.5 then hide(hookP); return end
	params.FilterDescendantsInstances = { ch, holder }
	local hit = workspace:Raycast(from, d.Unit * (d.Magnitude + 2), params)
	if hit and (hit.Position - at).Magnitude < 1.5 and shield(hit.Instance, at.Y) then
		place(hookP, at, hit.Normal, math.clamp(d.Magnitude * 0.1, SIZE, 30)) -- (a far one drawn bigger, so it still reads)
		thicken(hookP, lineFor(d.Magnitude))
		show(hookP, 1)
		ripple(hookP)
	else
		hide(hookP)
	end
end)

-- ---------------------------------------------------------------- bullets on the wall box (Fx.impact asks)
local hitFn = Instance.new("BindableFunction")
hitFn.Name = "WallGridHit"
hitFn.OnInvoke = function(at: Vector3, n: Vector3, part: Instance?): boolean
	if not shield(part, at.Y) then return false end
	local pt = hitP[nextHit]
	nextHit = nextHit % #hitP + 1
	local dist = (camera.CFrame.Position - at).Magnitude
	place(pt, at, n, math.clamp(dist * 0.07, SIZE * 0.7, 24))
	thicken(pt, lineFor(dist))
	pt.alpha = 0.9; pt.target = 0; pt.rate = 1 / 0.5
	return true
end
hitFn.Parent = script.Parent

-- ---------------------------------------------------------------- coming near a wall (ten times a second)
local DIRS: { Vector3 } = {}
for k = 0, 7 do
	local a = math.rad(45 * k)
	table.insert(DIRS, Vector3.new(math.cos(a), 0, math.sin(a)))
end
table.insert(DIRS, Vector3.new(0, -1, 0)) -- (the step's top under you)
local nearAt: Vector3? = nil
task.spawn(function()
	while true do
		task.wait(0.1)
		local ch, root = body()
		local hum = ch and ch:FindFirstChildOfClass("Humanoid")
		if not hum or hum.Health <= 0 then hide(hookP) end -- (a rope doesn't outlive you)
		if not ch or not root or type(player:GetAttribute("SkyY")) ~= "number" then nearAt = nil; hide(nearP); continue end
		params.FilterDescendantsInstances = { ch, holder }
		local chest = root.Position + Vector3.new(0, 1, 0)
		local best: RaycastResult?, bestD = nil, math.huge
		for _, dir in DIRS do
			local r = workspace:Raycast(chest, dir * (NEAR + 2), params)
			if r and shield(r.Instance, r.Position.Y) then
				-- (how far the face's plane really is: a ray at 45 degrees to a wall reads long)
				local dd = math.abs((chest - r.Position):Dot(r.Normal))
				if dd < bestD then best, bestD = r, dd end
			end
		end
		if not best or bestD > NEAR then nearAt = nil; hide(nearP); continue end
		local n = best.Normal
		local foot = chest - n * (chest - best.Position):Dot(n)
		local part = best.Instance :: BasePart
		if math.abs(n.Y) < 0.5 then -- (on a wall: keep the patch on the face, under its top)
			local top = part.Position.Y + part.Size.Y / 2
			foot = Vector3.new(foot.X, math.min(foot.Y, top - SIZE * 0.3), foot.Z)
		end
		if not shield(part, foot.Y) then nearAt = nil; hide(nearP); continue end
		if nearP.normal == nil or (nearP.normal :: Vector3):Dot(n) < 0.99 or nearP.alpha < 0.05 then place(nearP, foot, n) end
		nearP.normal = n
		nearAt = foot
		show(nearP, math.clamp(1 - (bestD - 2) / (NEAR - 2), 0.15, 1) * 0.8)
	end
end)

-- ---------------------------------------------------------------- each frame: fades, and the near patch following you
RunService.RenderStepped:Connect(function(dt: number)
	for _, pt in all do
		if pt.alpha ~= pt.target then
			local step = dt * pt.rate
			pt.alpha = if pt.alpha < pt.target then math.min(pt.target, pt.alpha + step) else math.max(pt.target, pt.alpha - step)
			pt.group.GroupTransparency = 1 - pt.alpha
			local on = pt.alpha > 0.01
			if pt.gui.Enabled ~= on then pt.gui.Enabled = on end
		end
	end
	if nearAt and nearP.pos and nearP.normal then
		local to = nearP.pos:Lerp(nearAt :: Vector3, math.min(1, dt * 12))
		if (to - (nearP.pos :: Vector3)).Magnitude > 0.01 then place(nearP, to, nearP.normal :: Vector3) end
	end
end)
