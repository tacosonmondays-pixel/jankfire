--!strict
-- SLAP GOLF, the server's half (shared/MiniGames.luau: MG.GOLF has every number and the six holes, MG.L.golf the
-- footprint). the owner, 19 Nov 2026: "mini game where you toss dummies with the hand slapper, almost like mini golf".
-- MiniGames.server calls this like the other games' halves, plus build (the course, once, on the hub's "golf" spot),
-- pickSide (a free golfer's place, A-D) and refresh (the PLAY / JOIN prompt and the names).
-- the course: one raised bed of six cells (two rows of three, each hole playing toward the spot's look), the lawn in
-- rolled stripes, round rails, a cup with a flag, and each hole's own pieces (a log, a planter, a ramp up to a raised
-- green, a turning bar, bouncy posts, a jump over a pit). all plain parts in the hub's quiet colours, the flag the one
-- accent. the dummies: the training room's cardboard dummy as a ragdoll (ball-socket joints, no Humanoid), owned by
-- the server so everyone sees the same flight, in their own collision group (they touch the course, never people or
-- each other). each golfer holds the Hand Slapper (a welded prop) while they play.
-- what everyone sees is in the course model's attributes (MiniGolfUI draws it):
--   State "lobby" | "play" | "between" | "done", Host (a side), Order ("A,B,..": who plays, in turn order), Hole, Par,
--   Turn (the side to play, or ""), Phase "aim" | "fly", TurnT (server time the shot began), Aim (the player's yaw as
--   they aim, radians), <S>_card ("2,3,0,0,0,0": strokes per hole, 0 = not played), <S>_done (this hole: in or picked
--   up), Ev = "<n>:<kind>:<side>:<x>" (slap (power), cup, oob, pickup, rest, hole (n), done, boing, bonk)
-- from the client: { op = "start" } (the host, in the lobby or after a round), { op = "aim", yaw },
-- { op = "slap", yaw, power } (your turn, aiming)
local Players = game:GetService("Players")
local PhysicsService = game:GetService("PhysicsService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Golf = {}
Golf.SIDES = { "A", "B", "C", "D" }

local rng = Random.new()
local DGROUP = "MiniGolfDummy"
local function groups()
	pcall(function() PhysicsService:RegisterCollisionGroup(DGROUP) end)
	pcall(function() PhysicsService:CollisionGroupSetCollidable(DGROUP, DGROUP, false) end)
	for _, g in { "JFPlayers", "JFShredded", "VipGuest", "JFRayBlind" } do
		pcall(function() PhysicsService:CollisionGroupSetCollidable(DGROUP, g, false) end)
	end
end
groups()

local WeaponModels: any = nil
pcall(function() WeaponModels = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("WeaponModels")) end)

-- the hub's quiet palette: a sage lawn in two rolled tones, cream bed and stone, warm wood rails, slate, one amber flag
local C = {
	lawnA = Color3.fromRGB(128, 152, 106), lawnB = Color3.fromRGB(117, 141, 97), bed = Color3.fromRGB(214, 206, 190),
	stone = Color3.fromRGB(198, 190, 174), rail = Color3.fromRGB(176, 138, 94), slate = Color3.fromRGB(98, 102, 111),
	rim = Color3.fromRGB(236, 232, 224), hole = Color3.fromRGB(32, 35, 42), flag = Color3.fromRGB(255, 196, 61),
	pit = Color3.fromRGB(64, 68, 76), post = Color3.fromRGB(232, 226, 214), band = Color3.fromRGB(62, 66, 74),
	planter = Color3.fromRGB(150, 112, 76), bush = Color3.fromRGB(88, 112, 80), log = Color3.fromRGB(104, 128, 88),
	tan = Color3.fromRGB(180, 154, 122), legs = Color3.fromRGB(74, 78, 87), pale = Color3.fromRGB(236, 234, 228), -- (Dummies')
}

local function set(T: any, k: string, v: any) if T.model:GetAttribute(k) ~= v then T.model:SetAttribute(k, v) end end
local function ev(T: any, kind: string, side: string, x: any?)
	T.g.evN += 1
	set(T, "Ev", ("%d:%s:%s:%s"):format(T.g.evN, kind, side, tostring(x or "-")))
end

-- ------------------------------------------------------------------ the course
local function mk(parent: Instance, name: string, cf: CFrame, size: Vector3, color: Color3, props: { [string]: any }?): Part
	local p = Instance.new("Part")
	p.Name = name; p.Anchored = true; p.Size = size; p.CFrame = cf; p.Color = color
	p.Material = Enum.Material.SmoothPlastic
	p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	p.CanCollide = true; p.CanQuery = true; p.CanTouch = false
	if props then for k, v in props do (p :: any)[k] = v end end
	p.Parent = parent
	return p
end
-- a round rod from a to b (a Cylinder's length is its X)
local function rod(parent: Instance, name: string, a: Vector3, b: Vector3, r: number, color: Color3, props: { [string]: any }?): Part
	local len = (b - a).Magnitude
	local p = mk(parent, name, CFrame.lookAt((a + b) / 2, b) * CFrame.Angles(0, math.pi / 2, 0), Vector3.new(len, r * 2, r * 2), color, props)
	p.Shape = Enum.PartType.Cylinder
	return p
end
-- a standing round post (its middle at `at`)
local function post(parent: Instance, name: string, at: CFrame, r: number, h: number, color: Color3, props: { [string]: any }?): Part
	local p = mk(parent, name, at * CFrame.Angles(0, 0, math.pi / 2), Vector3.new(h, r * 2, r * 2), color, props)
	p.Shape = Enum.PartType.Cylinder
	return p
end

-- the lawn's top at (x, z) in a hole's cell (nil: a pit, or off the lawn)
local FULL = { { -6, 6, -18, 18, 0 } }
local function topAt(h: any, x: number, z: number): number?
	if h.pit and z <= h.pit[1] and z >= h.pit[2] then return nil end
	for _, r in h.ramps or {} do
		local z0, z1 = math.min(r[3], r[4]), math.max(r[3], r[4])
		if x >= r[1] - 1 and x <= r[2] + 1 and z >= z0 and z <= z1 then
			return r[5] + (r[6] - r[5]) * ((z - r[3]) / (r[4] - r[3]))
		end
	end
	for _, r in h.lawn or FULL do
		if x >= r[1] - 1 and x <= r[2] + 1 and z >= math.min(r[3], r[4]) and z <= math.max(r[3], r[4]) then return r[5] end
	end
	return nil
end

-- each hole's cell frame: its middle on the lawn's level (y = 0 on the lawn), -Z along the play
local function cellCF(T: any, i: number): CFrame
	local L = T.L
	local col = if i <= 3 then i else 7 - i -- (row two runs back the other way: 4 under 3)
	local row = if i <= 3 then 1 else 2
	return T.cf * CFrame.new(L.cols[col], L.H, L.rows[row])
end
Golf.cellCF = cellCF

local function buildHole(T: any, i: number, h: any, parent: Instance)
	local L = T.L
	local cf = cellCF(T, i)
	local H = L.H
	local f = Instance.new("Model")
	f.Name = "Hole" .. i
	f.Parent = parent
	local function at(x: number, y: number, z: number): CFrame return cf * CFrame.new(x, y, z) end
	-- the bed: the cell's full width from the floor to the lawn's level, split round a pit
	local spans = { { 19, -19 } }
	if h.pit then spans = { { 19, h.pit[1] }, { h.pit[2], -19 } } end
	for _, s in spans do
		local z0, z1 = s[1], s[2]
		mk(f, "Bed", at(0, -H / 2 - 0.1, (z0 + z1) / 2), Vector3.new(14, H - 0.2, math.abs(z0 - z1)), C.bed)
	end
	if h.pit then
		mk(f, "PitFloor", at(0, -H + 0.05, (h.pit[1] + h.pit[2]) / 2), Vector3.new(14, 0.1, math.abs(h.pit[1] - h.pit[2])), C.pit)
	end
	-- the lawn: rolled stripes 3 studs deep, on raised blocks where the lawn is higher
	for _, r in h.lawn or FULL do
		local x0, x1, z0, z1, top = r[1], r[2], math.max(r[3], r[4]), math.min(r[3], r[4]), r[5]
		if top > 0 then
			mk(f, "Raised", at(0, (top - 0.2) / 2 - 0.1, (z0 + z1) / 2), Vector3.new(14, top + 0.0, z0 - z1), C.bed)
		end
		local z = z0
		local n = 0
		while z > z1 + 0.01 do
			local z2 = math.max(z1, z - 3)
			-- (the stripes' tone by their place along the cell, so neighbouring rects keep the rhythm)
			local band = math.floor((19 - z) / 3 + 0.001)
			mk(f, "Lawn", at((x0 + x1) / 2, top - 0.1, (z + z2) / 2), Vector3.new(x1 - x0, 0.2, z - z2), if band % 2 == 0 then C.lawnA else C.lawnB)
			z = z2
			n += 1
		end
	end
	-- the ramps: a block up to the low end, a wedge on it (turned so its tall end is where the ramp is high: checked
	-- with a ray, so the wedge's own way round doesn't matter)
	for _, r in h.ramps or {} do
		local zA, zB, yA, yB = r[3], r[4], r[5], r[6]
		local lo = math.min(yA, yB)
		local hi = math.max(yA, yB)
		local zm = (zA + zB) / 2
		local len = math.abs(zA - zB)
		if lo > 0 then mk(f, "RampBase", at(0, lo / 2 - 0.1, zm), Vector3.new(14, lo, len), C.bed) end
		local zHigh = if yA > yB then zA else zB
		local w = Instance.new("WedgePart")
		w.Name = "Ramp"; w.Anchored = true; w.Material = Enum.Material.SmoothPlastic; w.Color = C.lawnA
		w.Size = Vector3.new(14, hi - lo, len)
		w.CFrame = at(0, lo + (hi - lo) / 2, zm) * (if zHigh > zm then CFrame.identity else CFrame.Angles(0, math.pi, 0))
		w.Parent = f
		local params = RaycastParams.new()
		params.FilterType = Enum.RaycastFilterType.Include
		params.FilterDescendantsInstances = { w }
		local function heightAt(z: number): number
			local o = at(0, hi + 5, z).Position
			local hit = workspace:Raycast(o, Vector3.new(0, -(hi + 10), 0), params)
			return if hit then hit.Position.Y else -math.huge
		end
		if heightAt(zHigh + (if zHigh > zm then -0.3 else 0.3)) < heightAt(zm + (zm - zHigh) * 0.9) then
			w.CFrame *= CFrame.Angles(0, math.pi, 0)
		end
	end
	-- the rails: round wood bumpers round the cell, following the lawn's height (over a pit they bridge at the
	-- lawn's level), each with a taller see-through box that does the bumping
	local function railSeg(a: Vector3, b: Vector3)
		rod(f, "Rail", a, b, 0.6, C.rail)
		local mid = (a + b) / 2
		local box = mk(f, "RailBox", CFrame.lookAt(mid, b) * CFrame.new(0, 0.6, 0), Vector3.new(1.1, 2.8, (b - a).Magnitude + 1.1), C.rail,
			{ Transparency = 1, CanQuery = false, CanTouch = true, CastShadow = false })
		box:SetAttribute("GolfRail", true)
	end
	local zs: { number } = { 18.5, -18.5 }
	for _, r in h.lawn or {} do table.insert(zs, r[3]); table.insert(zs, r[4]) end
	for _, r in h.ramps or {} do table.insert(zs, r[3]); table.insert(zs, r[4]) end
	if h.pit then table.insert(zs, h.pit[1]); table.insert(zs, h.pit[2]) end
	table.sort(zs, function(a, b) return a > b end)
	-- (the rod's middle 0.4 over the lawn: it sits on the bed's edge; the raised green and the ramps are full width, so
	-- a rail up there sits on them too)
	local function railY(x: number, z: number): number
		local t = topAt(h, x, math.clamp(z, -18, 18))
		return (t or 0) + 0.4
	end
	for _, sx in { -6.5, 6.5 } do
		for k = 1, #zs - 1 do
			local za, zb = zs[k], zs[k + 1]
			if za - zb < 0.05 then continue end
			local ya = railY(sx - math.sign(sx) * 0.6, za - 0.01)
			local yb = railY(sx - math.sign(sx) * 0.6, zb + 0.01)
			railSeg(cf * Vector3.new(sx, ya, za), cf * Vector3.new(sx, yb, zb))
		end
	end
	for _, sz in { 18.5, -18.5 } do
		local y = railY(0, sz)
		railSeg(cf * Vector3.new(-6.5, y, sz), cf * Vector3.new(6.5, y, sz))
		for _, sx in { -6.5, 6.5 } do
			local cap = mk(f, "RailCap", at(sx, y, sz), Vector3.new(1.3, 1.3, 1.3), C.rail)
			cap.Shape = Enum.PartType.Ball
		end
	end
	-- the tee mat and the cup (a cream rim, the dark hole, a flag on a pole with the hole's number)
	local teeY = topAt(h, h.tee.X, h.tee.Y) or 0
	post(f, "Tee", at(h.tee.X, teeY + 0.03, h.tee.Y), 1.6, 0.06, C.slate, { CanCollide = false, CanQuery = false })
	local cupY = topAt(h, h.cup.X, h.cup.Y) or 0
	post(f, "CupRim", at(h.cup.X, cupY + 0.03, h.cup.Y), 3.0, 0.06, C.rim, { CanCollide = false, CanQuery = false })
	post(f, "Cup", at(h.cup.X, cupY + 0.04, h.cup.Y), 2.6, 0.08, C.hole, { CanCollide = false, CanQuery = false })
	post(f, "FlagPole", at(h.cup.X, cupY + 3.2, h.cup.Y), 0.12, 6.4, C.rim, { CanCollide = false, CanQuery = false })
	local flag = mk(f, "Flag", at(h.cup.X + 0.95, cupY + 5.8, h.cup.Y), Vector3.new(1.8, 1.15, 0.08), C.flag, { CanCollide = false, CanQuery = false })
	for _, face in { Enum.NormalId.Front, Enum.NormalId.Back } do
		local g = Instance.new("SurfaceGui")
		g.Face = face; g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud; g.PixelsPerStud = 60; g.LightInfluence = 0
		local t = Instance.new("TextLabel")
		t.BackgroundTransparency = 1; t.Size = UDim2.fromScale(1, 1); t.Text = tostring(i); t.TextScaled = true
		t.Font = Enum.Font.GothamBlack; t.TextColor3 = C.hole
		t.Parent = g
		g.Parent = flag
	end
	-- the hole's pieces
	if h.hump then
		local hp = h.hump
		local log = rod(f, "Hump", cf * Vector3.new(-6, hp.top - hp.r, hp.z), cf * Vector3.new(6, hp.top - hp.r, hp.z), hp.r, C.log)
		log.Material = Enum.Material.SmoothPlastic
	end
	if h.planter then
		local p = h.planter
		local x0, x1, z0, z1, ph = p[1], p[2], p[3], p[4], p[5]
		mk(f, "Planter", at((x0 + x1) / 2, ph / 2, (z0 + z1) / 2), Vector3.new(x1 - x0, ph, z1 - z0), C.planter)
		local n = math.max(2, math.floor((z1 - z0) / 5.5))
		for k = 0, n - 1 do
			local z = z0 + 2.4 + k * ((z1 - z0 - 4.8) / math.max(1, n - 1))
			local b = mk(f, "Bush", at((x0 + x1) / 2, ph + 0.9, z), Vector3.new(2.6, 2.6, 2.6), C.bush)
			b.Shape = Enum.PartType.Ball
		end
	end
	for k, p in h.posts or {} do
		local y = topAt(h, p[1], p[2]) or 0
		local pp = post(f, "Bouncer" .. k, at(p[1], y + 1.2, p[2]), p[3], 2.4, C.post,
			{ CustomPhysicalProperties = PhysicalProperties.new(0.7, 0.2, 1, 1, 100), CanTouch = true })
		pp:SetAttribute("GolfBouncer", true)
		post(f, "Band", at(p[1], y + 1.6, p[2]), p[3] + 0.06, 0.32, C.band, { CanCollide = false, CanQuery = false })
	end
	if h.spinner then
		local s = h.spinner
		local y = topAt(h, s[1], s[2]) or 0
		post(f, "SpinPost", at(s[1], y + 1.5, s[2]), 0.7, 3, C.post)
		local bar = mk(f, "SpinBar", at(s[1], y + 1.0, s[2]), Vector3.new(s[3], 0.8, 0.8), C.rail,
			{ CustomPhysicalProperties = PhysicalProperties.new(1, 0.3, 0.6, 1, 10) })
		T.g.spin = { bar = bar, at = at(s[1], y + 1.0, s[2]), a = 0 }
	end
end

-- the strips of stone between the cells and round the footprint's edge, at the lawn's level
local function buildBorders(T: any, parent: Instance)
	local L = T.L
	local W, D = L.size.X, L.size.Y
	local H = L.H
	local function strip(x0: number, x1: number, z0: number, z1: number)
		if x1 - x0 < 0.05 or z1 - z0 < 0.05 then return end
		mk(parent, "Stone", T.cf * CFrame.new((x0 + x1) / 2, H / 2 - 0.1, (z0 + z1) / 2), Vector3.new(x1 - x0, H - 0.2 + 0.2, z1 - z0), C.stone)
	end
	-- between the rows, and the two ends
	local rowEdge = L.rows[1] - L.cell.Y / 2
	strip(-W / 2, W / 2, -rowEdge, rowEdge)
	strip(-W / 2, W / 2, L.rows[1] + L.cell.Y / 2, D / 2)
	strip(-W / 2, W / 2, -D / 2, L.rows[2] - L.cell.Y / 2)
	-- between the columns (and the sides, if the footprint is wider than the cells)
	local xs = { -W / 2 }
	for _, c in L.cols do table.insert(xs, c - L.cell.X / 2); table.insert(xs, c + L.cell.X / 2) end
	table.insert(xs, W / 2)
	for _, row in L.rows do
		for k = 1, #xs - 1, 2 do strip(xs[k], xs[k + 1], row - L.cell.Y / 2, row + L.cell.Y / 2) end
	end
end

function Golf.build(T: any, ctx: any)
	T.L = ctx.MG.L.golf
	T.g = T.g or {}
	T.g.evN = 0
	local course = Instance.new("Model")
	course.Name = "Course"
	course.Parent = T.model
	for i, h in ctx.MG.GOLF.HOLES do buildHole(T, i, h, course) end
	buildBorders(T, course)
	-- the PLAY / JOIN prompt, at the front of the course (the first hole's end)
	local a = Instance.new("Attachment")
	a.Name = "PromptAt"
	a.CFrame = CFrame.new(T.L.prompt)
	a.Parent = T.model.PrimaryPart
	local pr = Instance.new("ProximityPrompt")
	pr.ObjectText = ctx.MG.TITLE.golf; pr.ActionText = "Play"
	pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX; pr.HoldDuration = 0
	pr.MaxActivationDistance = 12; pr.RequiresLineOfSight = false; pr.ClickablePrompt = true
	pr.Exclusivity = Enum.ProximityPromptExclusivity.OnePerButton
	pr:SetAttribute("MiniSide", "*")
	pr.Parent = a
	T.prompts["*"] = pr
	-- the bumps you hear: a dummy on a bouncy post, a dummy on a rail (once in a moment)
	local lastT = 0
	for _, d in course:GetDescendants() do
		if d:IsA("BasePart") and (d:GetAttribute("GolfBouncer") or d:GetAttribute("GolfRail")) then
			local kind = if d:GetAttribute("GolfBouncer") then "boing" else "bonk"
			d.Touched:Connect(function(o: BasePart)
				if o.CollisionGroup ~= DGROUP or os.clock() - lastT < 0.2 then return end
				if o.AssemblyLinearVelocity.Magnitude < 6 then return end
				lastT = os.clock()
				local side = o:GetAttribute("GolfSide")
				if type(side) == "string" then ev(T, kind, side, "-") end
			end)
		end
	end
end

-- ------------------------------------------------------------------ the dummies (a ragdoll each)
local LIMITS = {
	Neck = { 30, 25 }, Waist = { 25, 20 }, Root = { 20, 10 },
	LeftShoulder = { 75, 45 }, RightShoulder = { 75, 45 }, LeftElbow = { 70, 10 }, RightElbow = { 70, 10 },
	LeftWrist = { 25, 15 }, RightWrist = { 25, 15 }, LeftHip = { 55, 25 }, RightHip = { 55, 25 },
	LeftKnee = { 70, 10 }, RightKnee = { 70, 10 }, LeftAnkle = { 25, 15 }, RightAnkle = { 25, 15 },
}
local desc: HumanoidDescription? = nil
local function dummyDesc(): HumanoidDescription
	if desc then return desc end
	local d = Instance.new("HumanoidDescription")
	d.HeadColor = C.tan; d.TorsoColor = C.tan; d.LeftArmColor = C.tan; d.RightArmColor = C.tan
	d.LeftLegColor = C.legs; d.RightLegColor = C.legs
	desc = d
	return d
end

type Dummy = { model: Model, root: BasePart, torso: BasePart, parts: { BasePart }, rel: { [BasePart]: CFrame }, standH: number }

local function makeDummy(T: any, side: string, color: Color3): Dummy?
	local ok, m = pcall(function() return Players:CreateHumanoidModelFromDescription(dummyDesc(), Enum.HumanoidRigType.R15) end)
	if not ok or not m then warn("[MiniGolf] no dummy body: " .. tostring(m)); return nil end
	local rig = m :: Model
	rig.Name = "Dummy_" .. side
	rig:SetAttribute("MiniSide", side)
	local root = rig:FindFirstChild("HumanoidRootPart") :: BasePart
	local torso = rig:FindFirstChild("UpperTorso") :: BasePart
	local lower = rig:FindFirstChild("LowerTorso") :: BasePart
	if not root or not torso or not lower then rig:Destroy(); return nil end
	local head = rig:FindFirstChild("Head")
	local face = head and head:FindFirstChildOfClass("Decal")
	if face then face:Destroy() end
	-- standing, at the origin: each part's place against the root (to stand it up again), and how high the root is
	rig:PivotTo(CFrame.new(0, 100, 0))
	local rel: { [BasePart]: CFrame } = {}
	local parts: { BasePart } = {}
	local low = math.huge
	for _, d in rig:GetDescendants() do
		if d:IsA("BasePart") then
			rel[d] = root.CFrame:ToObjectSpace(d.CFrame)
			table.insert(parts, d)
			if d ~= root then low = math.min(low, d.Position.Y - d.Size.Y / 2) end
		end
	end
	local standH = root.Position.Y - low + 0.05
	-- the joints: every one a ball and socket within limits, except the root's (welded to the lower torso)
	for _, j in rig:GetDescendants() do
		local a0: Attachment?, a1: Attachment? = nil, nil
		if j:IsA("Motor6D") then
			local p0, p1 = j.Part0, j.Part1
			if p0 and p1 then
				a0 = Instance.new("Attachment"); (a0 :: Attachment).CFrame = j.C0; (a0 :: Attachment).Parent = p0
				a1 = Instance.new("Attachment"); (a1 :: Attachment).CFrame = j.C1; (a1 :: Attachment).Parent = p1
			end
		elseif j:IsA("AnimationConstraint") then
			a0, a1 = j.Attachment0, j.Attachment1
		else
			continue
		end
		local name = j.Name
		local isRoot = name == "Root" or name == "RootJoint"
		if isRoot then
			local w = Instance.new("WeldConstraint"); w.Part0 = root; w.Part1 = lower; w.Parent = root
		elseif a0 and a1 then
			local bs = Instance.new("BallSocketConstraint")
			bs.Attachment0 = a0; bs.Attachment1 = a1
			local lim = LIMITS[name] or { 40, 20 }
			bs.LimitsEnabled = true; bs.UpperAngle = lim[1]
			bs.TwistLimitsEnabled = true; bs.TwistLowerAngle = -lim[2]; bs.TwistUpperAngle = lim[2]
			bs.Parent = j.Parent
		end
		j:Destroy()
	end
	local hum = rig:FindFirstChildOfClass("Humanoid")
	if hum then hum:Destroy() end
	for _, p in parts do
		p.CollisionGroup = DGROUP
		p.CanCollide = p ~= root
		p.CanQuery = false; p.CanTouch = true; p.Massless = p == root
		p.CustomPhysicalProperties = PhysicalProperties.new(0.6, 0.55, 0.25, 1, 1)
		p:SetAttribute("GolfSide", side)
	end
	-- the training dummy's target ring on its chest, its middle in the golfer's colour
	for k, r in { { 1.7, C.pale }, { 0.8, color } } do
		local d = Instance.new("Part")
		d.Name = "Ring"; d.Shape = Enum.PartType.Cylinder; d.Material = Enum.Material.SmoothPlastic; d.Color = r[2]
		d.Size = Vector3.new(0.12, r[1], r[1])
		d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.Massless = true; d.CastShadow = false
		d.CollisionGroup = DGROUP
		d.CFrame = torso.CFrame * CFrame.new(0, 0.15, -(torso.Size.Z / 2 + 0.04 + 0.05 * k)) * CFrame.Angles(0, math.pi / 2, 0)
		local w = Instance.new("WeldConstraint"); w.Part0 = torso; w.Part1 = d; w.Parent = d
		d.Parent = rig
	end
	for _, p in parts do p.Anchored = true end
	rig.Parent = T.model
	return { model = rig, root = root, torso = torso, parts = parts, rel = rel, standH = standH }
end

-- the ground under (x, z) in hole i's cell: the course only (not the dummies, not people)
local function groundAt(T: any, i: number, pos: Vector3): number
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = { T.model:FindFirstChild("Course") :: Instance }
	local lawn = cellCF(T, i).Position.Y
	local hit = workspace:Raycast(Vector3.new(pos.X, lawn + 12, pos.Z), Vector3.new(0, -30, 0), params)
	if hit then return hit.Position.Y end
	return lawn
end

-- stand a dummy up at (x, z) world, facing `dir`, held still (anchored) until it's slapped
local function stand(T: any, D: Dummy, pos: Vector3, dir: Vector3)
	local i = T.g.hole
	local y = groundAt(T, i, pos)
	local p = Vector3.new(pos.X, y + D.standH, pos.Z)
	local cf = CFrame.lookAt(p, p + Vector3.new(dir.X, 0, dir.Z))
	for _, part in D.parts do
		part.Anchored = true
		part.AssemblyLinearVelocity = Vector3.zero
		part.AssemblyAngularVelocity = Vector3.zero
		part.CFrame = cf * D.rel[part] -- (the ring, welded to the torso, comes along)
	end
end

local function hide(D: Dummy)
	for _, part in D.parts do part.Anchored = true; part.AssemblyLinearVelocity = Vector3.zero end
	D.model:PivotTo(CFrame.new(D.root.Position.X, D.root.Position.Y - 40, D.root.Position.Z))
end

-- ------------------------------------------------------------------ golfers
local function bodyOf(who: any): Model?
	if typeof(who) == "Instance" and who:IsA("Player") then return who.Character end
	if type(who) == "table" and who.Character then return who.Character end
	return nil
end

-- the Hand Slapper in a golfer's right hand while they play (the server's own weld, as Fight.showWeapon holds weapons)
local SLAP_K = 6.5
local function slapper(T: any, side: string, on: boolean, who: any?)
	local ch = bodyOf(if who ~= nil then who else T.who[side])
	if not ch then return end
	for _, c in ch:GetChildren() do if c.Name == "MiniSlapper" then c:Destroy() end end
	if not on or not WeaponModels then return end
	local hand = ch:FindFirstChild("RightHand") :: BasePart? or ch:FindFirstChild("Right Arm") :: BasePart?
	if not hand then return end
	local ok, w = pcall(WeaponModels.build, "slapper", SLAP_K)
	if not ok or not w or not w.PrimaryPart then return end
	w.Name = "MiniSlapper"
	local grip = w.PrimaryPart:FindFirstChild("Grip") :: Attachment?
	local off = if grip then grip.Position else Vector3.zero
	for _, d in w:GetDescendants() do
		if d:IsA("BasePart") then d.Anchored = false; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.Massless = true end
	end
	w:PivotTo(hand.CFrame * CFrame.new(0, -hand.Size.Y * 0.35, 0) * CFrame.Angles(-math.pi / 2, 0, 0) * CFrame.new(-off))
	local weld = Instance.new("WeldConstraint")
	weld.Part0 = hand; weld.Part1 = w.PrimaryPart; weld.Parent = w.PrimaryPart
	w.Parent = ch
end

-- a golfer onto their spot: beside their dummy (GOLF.SIDE to its left, GOLF.BACK behind), facing along `dir` (TeleportT first)
local function placeGolfer(T: any, side: string, D: Dummy, dir: Vector3)
	local who = T.who[side]
	local ch = bodyOf(who)
	if not ch then return end
	local hum = ch:FindFirstChildOfClass("Humanoid")
	local root = ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not hum or not root then return end
	local GB = T.ctx.MG.GOLF
	local flat = Vector3.new(dir.X, 0, dir.Z)
	if flat.Magnitude < 0.01 then flat = Vector3.new(0, 0, -1) end
	flat = flat.Unit
	local base = D.torso.Position - flat * GB.BACK - flat:Cross(Vector3.yAxis) * GB.SIDE -- (to its left: your right hand swings into it)
	local y = groundAt(T, T.g.hole, base)
	local up = root.Size.Y / 2 + (if hum.RigType == Enum.HumanoidRigType.R15 then hum.HipHeight else 2) + 0.1
	local pos = Vector3.new(base.X, y + up, base.Z)
	if typeof(who) == "Instance" and who:IsA("Player") then who:SetAttribute("TeleportT", os.clock()) end
	root.AssemblyLinearVelocity = Vector3.zero
	ch:PivotTo(CFrame.lookAt(pos, pos + flat))
end

-- ------------------------------------------------------------------ the round
local function GB(T: any): any return T.ctx.MG.GOLF end
local function holeOf(T: any): any return GB(T).HOLES[T.g.hole] end
local function cupPos(T: any, i: number): Vector3
	local h = GB(T).HOLES[i]
	return cellCF(T, i) * Vector3.new(h.cup.X, topAt(h, h.cup.X, h.cup.Y) or 0, h.cup.Y)
end
local function teePos(T: any, i: number, k: number): Vector3
	local h = GB(T).HOLES[i]
	-- (side by side on the tee, half a stud... 1.6 apart, across the lane)
	local x = math.clamp(h.tee.X + (k - 1) * 1.6 - 1.2, -5, 5)
	return cellCF(T, i) * Vector3.new(x, 0, h.tee.Y)
end
local function toCup(T: any, from: Vector3): Vector3
	local v = cupPos(T, T.g.hole) - from
	v = Vector3.new(v.X, 0, v.Z)
	return if v.Magnitude > 0.01 then v.Unit else (cellCF(T, T.g.hole).LookVector)
end

local function pubCard(T: any, side: string)
	local G = T.g
	local c = G.card[side]
	if not c then set(T, side .. "_card", nil); set(T, side .. "_done", nil); return end
	set(T, side .. "_card", table.concat(c, ","))
	set(T, side .. "_done", G.done[side] == true)
end
local function pubOrder(T: any)
	set(T, "Order", table.concat(T.g.order, ","))
end
local function state(T: any, s: string)
	T.g.state = s
	T.g.at = T.ctx.now()
	set(T, "State", s)
end

local function present(T: any): { string }
	local o = {}
	for _, s in Golf.SIDES do if T.who[s] ~= nil then table.insert(o, s) end end
	return o
end

local nextTurn: (T: any) -> ()
local function startTurn(T: any, side: string)
	local G = T.g
	local D: Dummy? = G.dummy[side]
	if not D then -- (no body could be made for this golfer: they sit the hole out rather than stall it)
		G.done[side] = true
		G.turn = side
		nextTurn(T)
		return
	end
	G.turn = side
	G.phase = "aim"
	G.turnT = T.ctx.now()
	local dir = toCup(T, D.torso.Position)
	stand(T, D, Vector3.new(D.torso.Position.X, 0, D.torso.Position.Z), dir)
	G.from[side] = D.root.Position
	-- (the aim first: a client reads it when TurnT changes)
	set(T, "Aim", math.floor(math.atan2(-dir.X, -dir.Z) * 1000 + 0.5) / 1000)
	set(T, "Turn", side); set(T, "Phase", "aim"); set(T, "TurnT", G.turnT)
	placeGolfer(T, side, D, dir)
end

-- whose shot is next: round the order from the last one, the first not yet in (none: the hole's over)
function nextTurn(T: any)
	local G = T.g
	local n = #G.order
	if n == 0 then return end
	local k0 = table.find(G.order, G.turn or "") or 0
	for k = 1, n do
		local s = G.order[((k0 + k - 1) % n) + 1]
		if not G.done[s] then startTurn(T, s); return end
	end
	-- everyone's in: the card, then the next hole
	G.turn = nil
	set(T, "Turn", "")
	ev(T, "hole", "-", G.hole)
	state(T, "between")
end

local function startHole(T: any, i: number)
	local G = T.g
	G.hole = i
	set(T, "Hole", i); set(T, "Par", GB(T).HOLES[i].par)
	G.done = {}
	for k, s in G.order do
		pubCard(T, s)
		local D: Dummy? = G.dummy[s]
		if D then stand(T, D, teePos(T, i, k), toCup(T, teePos(T, i, k))) end
	end
	state(T, "play")
	G.turn = nil
	nextTurn(T)
end

local function begin(T: any)
	local G = T.g
	G.order = present(T)
	pubOrder(T)
	G.card = {}
	for _, s in G.order do
		G.card[s] = { 0, 0, 0, 0, 0, 0 }
		if not G.dummy[s] then G.dummy[s] = makeDummy(T, s, GB(T).COLORS[s]) end
	end
	startHole(T, 1)
end

local function finishShot(T: any, side: string, how: string)
	local G = T.g
	local D: Dummy = G.dummy[side]
	local h = holeOf(T)
	local card = G.card[side]
	if how == "cup" then
		G.done[side] = true
		ev(T, "cup", side, card[G.hole])
		hide(D)
	elseif how == "oob" then
		card[G.hole] += 1 -- (the penalty)
		ev(T, "oob", side, card[G.hole])
		local back = G.from[side] or teePos(T, G.hole, 1)
		stand(T, D, back, toCup(T, back))
	else
		ev(T, "rest", side, card[G.hole])
	end
	if not G.done[side] and card[G.hole] >= h.par + GB(T).MAX_OVER then
		G.done[side] = true
		ev(T, "pickup", side, card[G.hole])
		hide(D)
	end
	pubCard(T, side)
	G.phase = "aim"
	nextTurn(T)
end

local function slap(T: any, side: string, yaw: number, power: number)
	local G = T.g
	local B = GB(T)
	local D: Dummy = G.dummy[side]
	if not D then return end
	power = math.clamp(power, 0, 1)
	local dir = Vector3.new(-math.sin(yaw), 0, -math.cos(yaw))
	G.from[side] = Vector3.new(D.torso.Position.X, 0, D.torso.Position.Z)
	placeGolfer(T, side, D, dir) -- (behind it on the line you chose: the swing points where the dummy goes)
	local speed = B.POWER.min + (B.POWER.max - B.POWER.min) * power
	local v = dir * speed + Vector3.new(0, speed * B.POWER.loft, 0)
	local spin = Vector3.yAxis:Cross(dir) * (4 + 8 * power) + Vector3.new(0, rng:NextNumber(-2, 2), 0)
	for _, p in D.parts do p.Anchored = false end
	for _, p in D.parts do
		pcall(function() p:SetNetworkOwner(nil) end)
		p.AssemblyLinearVelocity = v
	end
	D.torso.AssemblyAngularVelocity = spin
	G.card[side][G.hole] += 1
	pubCard(T, side)
	G.phase = "fly"
	G.flyT = T.ctx.now()
	G.restT = nil
	set(T, "Phase", "fly")
	ev(T, "slap", side, ("%.2f"):format(power))
end

-- ------------------------------------------------------------------ the module's hooks (MiniGames.server)
function Golf.setup(T: any, ctx: any)
	T.ctx = ctx
	local ev0 = T.g.evN or 0
	local spin = T.g.spin
	T.g = { state = "lobby", evN = ev0, order = {}, card = {}, done = {}, dummy = {}, from = {}, hole = 1, spin = spin, host = nil }
	state(T, "lobby")
	set(T, "Turn", ""); set(T, "Hole", 1); set(T, "Par", ctx.MG.GOLF.HOLES[1].par)
	groups()
end

function Golf.canReplaceBot(_T: any): boolean return false end

function Golf.pickSide(T: any): string?
	if T.g.state ~= "lobby" and T.g.state ~= "done" then return nil end
	for _, s in Golf.SIDES do if T.who[s] == nil then return s end end
	return nil
end

function Golf.refresh(T: any, ctx: any)
	local m = T.model
	local n = 0
	for _, s in Golf.SIDES do
		local who = T.who[s]
		if who ~= nil then n += 1 end
		m:SetAttribute(s .. "Name", if who then ctx.nameOf(who) else nil)
		m:SetAttribute(s .. "Id", if who then ctx.idOf(who) else nil)
	end
	local pr = T.prompts["*"]
	if pr then
		local open = (T.g.state == "lobby" or T.g.state == "done") and n < #Golf.SIDES
		pr.Enabled = open
		pr.ActionText = if n == 0 then "Play" else "Join"
	end
end

function Golf.joined(T: any, side: string, _p: Player, ctx: any)
	local G = T.g
	slapper(T, side, true)
	if not G.host or T.who[G.host] == nil then G.host = side; set(T, "Host", side) end
	if G.state == "done" then state(T, "lobby") end
	if not table.find(G.order, side) then table.insert(G.order, side); pubOrder(T) end
	ctx.refresh(T)
end

function Golf.left(T: any, side: string, who: any, ctx: any)
	local G = T.g
	slapper(T, side, false, who)
	local D: Dummy? = G.dummy[side]
	if D then D.model:Destroy(); G.dummy[side] = nil end
	local k = table.find(G.order, side)
	if k then table.remove(G.order, k); pubOrder(T) end
	G.card[side] = nil
	G.done[side] = nil
	pubCard(T, side)
	if G.host == side then
		G.host = G.order[1]
		set(T, "Host", G.host)
	end
	if #G.order == 0 then
		for _, d in G.dummy do d.model:Destroy() end
		G.dummy = {}
		state(T, "lobby")
		set(T, "Turn", "")
	elseif G.state == "play" and G.turn == side then
		G.phase = "aim"
		nextTurn(T)
	end
	ctx.refresh(T)
end

function Golf.msg(T: any, p: Player, side: string, d: any, ctx: any)
	local G = T.g
	if d.op == "start" then
		if (G.state ~= "lobby" and G.state ~= "done") or G.host ~= side then return end
		begin(T)
		ctx.refresh(T)
	elseif d.op == "aim" then
		if G.state ~= "play" or G.turn ~= side or G.phase ~= "aim" then return end
		if type(d.yaw) == "number" and d.yaw == d.yaw then set(T, "Aim", math.floor(d.yaw * 1000 + 0.5) / 1000) end
	elseif d.op == "slap" then
		if G.state ~= "play" or G.turn ~= side or G.phase ~= "aim" then return end
		if type(d.yaw) ~= "number" or d.yaw ~= d.yaw or type(d.power) ~= "number" or d.power ~= d.power then return end
		slap(T, side, d.yaw, d.power)
	end
end

local function partsSpeed(D: Dummy): number
	local v = 0
	for _, p in D.parts do
		if p ~= D.root then v = math.max(v, p.AssemblyLinearVelocity.Magnitude) end
	end
	return v
end

function Golf.step(T: any, dt: number, ctx: any)
	local G = T.g
	-- the turning bar (its contact speed set too, so it shoves a dummy rather than passing through it)
	local sp = G.spin
	if sp and sp.bar.Parent then
		sp.a = (sp.a + dt * ctx.MG.GOLF.SPIN) % (math.pi * 2)
		sp.bar.CFrame = sp.at * CFrame.Angles(0, sp.a, 0)
		sp.bar.AssemblyAngularVelocity = Vector3.new(0, ctx.MG.GOLF.SPIN, 0)
	end
	local now = ctx.now()
	if G.state == "between" then
		if now - G.at >= ctx.MG.GOLF.BETWEEN then
			if G.hole >= #ctx.MG.GOLF.HOLES then
				state(T, "done")
				ev(T, "done", "-", "-")
				for _, D in G.dummy do hide(D) end
				ctx.refresh(T)
			else
				startHole(T, G.hole + 1)
			end
		end
		return
	end
	if G.state ~= "play" or not G.turn then return end
	local side = G.turn :: string
	local D: Dummy? = G.dummy[side]
	if not D then nextTurn(T); return end
	if G.phase == "aim" then
		-- (a shot not taken in time is taken for you: soft, at the cup)
		if now - G.turnT >= ctx.MG.GOLF.SHOT_TIME then
			local dir = toCup(T, D.torso.Position)
			slap(T, side, math.atan2(-dir.X, -dir.Z), 0.4)
		end
		return
	end
	-- in flight: in the cup, out of bounds, or at rest
	local B = ctx.MG.GOLF
	local h = holeOf(T)
	local cf = cellCF(T, G.hole)
	local l = cf:PointToObjectSpace(D.torso.Position)
	local cup = cupPos(T, G.hole)
	local flatV = Vector3.new(D.torso.AssemblyLinearVelocity.X, 0, D.torso.AssemblyLinearVelocity.Z).Magnitude
	local dCup = Vector3.new(D.torso.Position.X - cup.X, 0, D.torso.Position.Z - cup.Z).Magnitude
	if dCup < B.CUP_R and D.torso.Position.Y < cup.Y + B.CUP_H and flatV < B.CUP_V then
		finishShot(T, side, "cup")
		return
	end
	local inPit = h.pit ~= nil and l.Z <= h.pit[1] + 0.5 and l.Z >= h.pit[2] - 0.5 and l.Y < -0.2
	if math.abs(l.X) > 6.9 or math.abs(l.Z) > 18.9 or l.Y < -1.0 or inPit then
		finishShot(T, side, "oob")
		return
	end
	local v = partsSpeed(D)
	if v < B.REST_V then
		G.restT = G.restT or now
		if now - (G.restT :: number) >= B.REST_T then finishShot(T, side, "rest") end
	else
		G.restT = nil
	end
	if now - (G.flyT or now) > B.FLY_MAX then finishShot(T, side, "rest") end
end

return Golf
