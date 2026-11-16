--!strict
-- the training area's doors and gates as each player sees them (16 Nov 2026, from the owner's play test: "when you go
-- up to garage doors can they slide up", "when you go to the laser gate, when you get close you hear a click and the
-- laser gate turns off?", and the course's pit: "is that going to be something?"):
--   * the back lot's garage door (Hub.TrainingGround.Lot.Door): the server (TheLot) decides when it moves and sets the
--     Door's attributes From, Goal, Dur and Since (server time). this rolls the slats up smoothly, into the head one by
--     one. Rattle (server time): the door jumps a hand's width and drops (LOCKED)
--   * roll-up shutters: a Model with the attribute Shutter (the muster's gate home). it rolls up while anyone is within
--     Near studs of its Center and rolls down after them. only on screen: its slats never block (walk in and the gate's
--     trigger takes you home)
--   * laser gates: anything tagged LaserGate (CollectionService). its parts named LaserBar and LaserField (or marked with
--     the attribute Laser: the playground's gate home, StructurePass) switch off with
--     a click while anyone is within Near (an attribute, default 9) of it, and back on with a click once they are gone.
--     a gate's own builder only has to tag it
--   * the course's long-jump pit (a part LongJumpPit with the attribute Edge, the take-off line's z): slide down the
--     lane, jump at the line, and how far you got shows when you land
--   * the mirror (the muster's bay; a part MirrorSpot): while you are in training you stand there as a hologram in the
--     hub's style (see-through, a soft fill and outline, turning slowly over its lens), holding what you hold. the owner,
--     16 Nov: "it can be a hologram version of your avatar"; its podium shows your name, rank and numbers
--   * the range's Carls: every runner has his own (RangeTest); this screen keeps only its own in its world
-- the slats' shut places are their attribute Shut (a CFrame); a Model's Lift is how far up they go and Top the height
-- over which a slat is inside the wall (hidden)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local CollectionService = game:GetService("CollectionService")

local Hud = require(script.Parent:WaitForChild("Hud"))
local Sfx = require(script.Parent:WaitForChild("Sfx"))
local me = Players.LocalPlayer

type Slat = { p: BasePart, shut: CFrame }
type Roller = { m: Instance, slats: { Slat }, lift: number, top: number }
local function ease(a: number): number
	a = math.clamp(a, 0, 1)
	return a * a * (3 - 2 * a)
end
local function readRoller(m: Instance): Roller
	local r: Roller = { m = m, slats = {}, lift = 0, top = math.huge }
	local lf, tp = m:GetAttribute("Lift"), m:GetAttribute("Top")
	r.lift = if type(lf) == "number" then lf else 10
	r.top = if type(tp) == "number" then tp else math.huge
	for _, d in m:GetDescendants() do
		local shut = d:GetAttribute("Shut")
		if d:IsA("BasePart") and typeof(shut) == "CFrame" then table.insert(r.slats, { p = d, shut = shut }) end
	end
	return r
end
-- put the slats u of the way up (0 shut .. 1 up), shifted by off (the rattle)
local function place(r: Roller, u: number, off: Vector3)
	for _, s in r.slats do
		if not s.p.Parent then continue end
		local cf = s.shut + Vector3.new(0, u * r.lift, 0) + off
		s.p.CFrame = cf
		local away = cf.Y - s.p.Size.Y / 2 > r.top
		local tr = if away then 1 else 0
		if s.p.Transparency ~= tr then s.p.Transparency = tr end
	end
end
-- is anyone (any player's character) within near studs of at, flat, and not far above or below it?
local function anyoneNear(at: Vector3, near: number): boolean
	for _, p in Players:GetPlayers() do
		local ch = p.Character
		local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		if root then
			local d = root.Position - at
			if math.abs(d.Y) < 9 and Vector3.new(d.X, 0, d.Z).Magnitude <= near then return true end
		end
	end
	return false
end

local function trainingGround(): Instance?
	local map = workspace:FindFirstChild("Map")
	local hub = map and map:FindFirstChild("Hub")
	return hub and hub:FindFirstChild("TrainingGround")
end

-- ---------------------------------------------------------------- the back lot's door (the server's)
local door: Roller? = nil
local function doorU(m: Instance, now: number): (number, boolean)
	local from, goal, dur, since = m:GetAttribute("From"), m:GetAttribute("Goal"), m:GetAttribute("Dur"), m:GetAttribute("Since")
	if type(from) ~= "number" or type(goal) ~= "number" or type(dur) ~= "number" or type(since) ~= "number" then return 0, false end
	if dur <= 0 then return goal, false end
	local a = (now - since) / dur
	return from + (goal - from) * ease(a), a < 1.05
end
local function rattleOff(m: Instance, now: number): (Vector3, boolean)
	local at = m:GetAttribute("Rattle")
	if type(at) ~= "number" then return Vector3.zero, false end
	local t = now - at
	if t < 0 or t > 0.8 then return Vector3.zero, false end
	local y
	if t < 0.16 then y = 0.55 * math.sin(t / 0.16 * math.pi / 2)        -- up a hand's width
	elseif t < 0.28 then y = 0.55 * (1 - (t - 0.16) / 0.12) ^ 2         -- drops
	else y = 0.14 * math.abs(math.sin((t - 0.28) * 28)) * (1 - (t - 0.28) / 0.52) end -- and bounces
	local x = 0.07 * math.sin(t * 95) * (1 - t / 0.8)
	return Vector3.new(x, y, 0), true
end

-- ---------------------------------------------------------------- shutters (on screen only)
type Shutter = { r: Roller, center: Vector3, near: number, u: number, from: number, goal: number, since: number, dur: number, lastNear: number }
local shutters: { Shutter } = {}

-- ---------------------------------------------------------------- laser gates
type Gate = { m: Instance, parts: { { p: BasePart, tr: number } }, center: Vector3, near: number, off: boolean, lastNear: number }
local gates: { [Instance]: Gate } = {}
local function gateOf(m: Instance): Gate
	local parts = {}
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") and (d.Name == "LaserBar" or d.Name == "LaserField" or d:GetAttribute("Laser") == true) then table.insert(parts, { p = d, tr = d.Transparency }) end
	end
	local center: Vector3
	local c = m:GetAttribute("Center")
	if typeof(c) == "Vector3" then center = c
	elseif m:IsA("Model") then center = m:GetBoundingBox().Position
	elseif m:IsA("BasePart") then center = m.Position
	elseif #parts > 0 then center = parts[1].p.Position
	else center = Vector3.zero end
	local n = m:GetAttribute("Near")
	return { m = m, parts = parts, center = center, near = if type(n) == "number" then n else 9, off = false, lastNear = 0 }
end
local function setLasers(g: Gate, off: boolean)
	g.off = off
	Sfx.play("click", g.center, 1, if off then 1 else 0.8)
	task.spawn(function()
		-- (a short flicker as the power goes, or comes back)
		for k = 1, 3 do
			local show = if off then k % 2 == 0 else k % 2 == 1
			for _, e in g.parts do if e.p.Parent then e.p.Transparency = if show then e.tr else 1 end end
			task.wait(0.05)
		end
		for _, e in g.parts do if e.p.Parent then e.p.Transparency = if g.off then 1 else e.tr end end
	end)
end
CollectionService:GetInstanceAddedSignal("LaserGate"):Connect(function(m) gates[m] = gateOf(m) end)
CollectionService:GetInstanceRemovedSignal("LaserGate"):Connect(function(m) gates[m] = nil end)
for _, m in CollectionService:GetTagged("LaserGate") do gates[m] = gateOf(m) end

-- ---------------------------------------------------------------- the long-jump pit
local pit: BasePart? = nil
local best = 0
local takeoff: Vector3? = nil
local wasAir = false
local function jumpWatch(root: BasePart, hum: Humanoid)
	local p = pit
	if not p or not p.Parent then return end
	local edge = p:GetAttribute("Edge")
	if type(edge) ~= "number" then return end
	local air = hum.FloorMaterial == Enum.Material.Air
	local pos = root.Position
	local rel = p.CFrame:PointToObjectSpace(pos)
	local h = p.Size / 2
	local inLane = math.abs(rel.X) <= h.X + 0.5
	if air and not wasAir then
		-- (a take-off counts from the lane, up to 40 studs before the line; a foot over the line is a foul)
		takeoff = if inLane and pos.Z < edge + 40 and pos.Z > edge - 3 then pos else nil
	elseif wasAir and not air and takeoff then
		local from = takeoff
		takeoff = nil
		if inLane and pos.Z < edge and pos.Z > edge - 60 then
			if from.Z < edge - 0.5 then
				Hud.callout("LONG JUMP · FOUL. JUMP FROM THE LINE", 1.8)
				Sfx.play("whoops", nil, 0.6)
			else
				local dist = edge - pos.Z
				local text = ("LONG JUMP · %.1f"):format(dist)
				if dist > best then
					if best > 0 then text ..= " · BEST" end
					best = dist
				end
				Hud.callout(text, 2.2)
				Sfx.play("ting", nil, 0.8, 0.9 + math.min(dist, 30) / 60)
			end
		end
	end
	wasAir = air
end

-- ---------------------------------------------------------------- the mirror
local mirrorSpot: BasePart? = nil
local holo: Model? = nil
local holoSig, spin = "", 0
local HOLO = Color3.fromRGB(143, 216, 255)
local HOLO_SCALE = 1.8 -- (the owner, 16 Nov: "can hologram you be larger?": nearly twice you, still under the bay's ceiling)
local function dropHolo()
	if holo then holo:Destroy(); holo = nil end
	holoSig = ""
end
-- what you are holding, as a string (the hologram is made again when it changes)
local function holding(ch: Model): string
	local t = {}
	for _, c in ch:GetChildren() do if c:IsA("Model") or c:IsA("Tool") then table.insert(t, c.Name) end end
	table.sort(t)
	return table.concat(t, ",")
end
local function buildHolo(ch: Model)
	dropHolo()
	local was = ch.Archivable
	ch.Archivable = true
	local ok, c = pcall(function() return ch:Clone() end)
	ch.Archivable = was
	if not ok or not c then return end
	local m = c :: Model
	m.Name = "MirrorHolo"
	for _, d in m:GetDescendants() do
		if d:IsA("BaseScript") or d:IsA("Sound") or d:IsA("ParticleEmitter") or d:IsA("Light") or d:IsA("BillboardGui")
			or d:IsA("ProximityPrompt") or d:IsA("Highlight") or d:IsA("Beam") or d:IsA("Trail") then
			d:Destroy()
		elseif d:IsA("BasePart") then
			d.Anchored = d.Name == "HumanoidRootPart"; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
			d.CastShadow = false; d.Massless = true; d.LocalTransparencyModifier = 0
			if d.Transparency < 1 then d.Transparency = math.max(d.Transparency, 0.3) end
		elseif d:IsA("Decal") then
			d.Transparency = math.max(d.Transparency, 0.4)
		end
	end
	local hum = m:FindFirstChildOfClass("Humanoid")
	if hum then
		hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
		hum.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
		hum.PlatformStand = true
	end
	local hl = Instance.new("Highlight")
	hl.FillColor = HOLO; hl.OutlineColor = HOLO; hl.FillTransparency = 0.8; hl.OutlineTransparency = 0.4
	hl.DepthMode = Enum.HighlightDepthMode.Occluded
	hl.Parent = m
	m.Parent = workspace
	pcall(function() m:ScaleTo(HOLO_SCALE) end)
	-- the pose: whatever you are playing now (so it holds your gun the way you do)
	local an = hum and hum:FindFirstChildOfClass("Animator")
	local real = ch:FindFirstChildOfClass("Humanoid")
	local ran = real and real:FindFirstChildOfClass("Animator")
	if an and ran then
		for _, tr in ran:GetPlayingAnimationTracks() do
			pcall(function()
				local t = an:LoadAnimation(tr.Animation)
				t.Looped = true
				t:Play(0, math.max(tr.WeightTarget, 0.01), 1)
			end)
		end
	end
	holo = m
	holoSig = holding(ch)
end
local function mirrorStep(dt: number)
	local spot = mirrorSpot
	local ch = me.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	if not spot or not spot.Parent or not ch or not root or not hum or hum.Health <= 0 then dropHolo(); return end
	-- (always there while you are in training: the owner, 16 Nov: "can your big hologram just be active always?")
	if me:GetAttribute("Zone") ~= "training" then dropHolo(); return end
	if not holo or not holo.Parent or holding(ch) ~= holoSig then buildHolo(ch) end
	local h = holo
	local hr = h and h:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not h or not hr then return end
	spin += dt * 0.32
	local up = (hum.HipHeight + root.Size.Y / 2) * HOLO_SCALE
	hr.CFrame = spot.CFrame * CFrame.new(0, up + 0.1, 0) * CFrame.Angles(0, spin, 0)
end

-- ---------------------------------------------------------------- the mirror's podium
-- the hologram stands on a two-step podium: the upper step's front shows your rank's badge, your name, @handle and
-- level; the lower step's front a strip of tiles with your numbers, from your own card (Stats' Profile remote, "card").
-- on your screen only: everyone sees their own (the owner, 16 Nov: "maybe at a plate with your username and a display
-- of stats??", then "I was thinking more of like a podium thing"). filled while you are in training, again every 30 s
-- and when your XP moves
local RS = game:GetService("ReplicatedStorage")
local SharedM = RS:WaitForChild("Jankfire")
local Ranks = require(SharedM:WaitForChild("Ranks"))
local Roster = require(SharedM:WaitForChild("Roster"))
local MFONT = "rbxasset://fonts/families/Montserrat.json"
local PALE, GREY, AMBER, DEEP = Color3.fromHex("eceae4"), Color3.fromHex("9aa0a8"), Color3.fromHex("f0a53a"), Color3.fromHex("2e3238")
local boards: { [string]: BasePart } = {}
local filledAt, filledXp: any = -math.huge, false
local myCard: any = nil
local asking = false
local function label(parent: Instance, name: string, text: string, x: number, y: number, w: number, h: number, color: Color3, weight: Enum.FontWeight, align: Enum.TextXAlignment?): TextLabel
	local t = Instance.new("TextLabel")
	t.Name = name; t.BackgroundTransparency = 1; t.TextScaled = true; t.Text = text; t.TextColor3 = color
	t.FontFace = Font.new(MFONT, weight); t.TextXAlignment = align or Enum.TextXAlignment.Center
	t.Position = UDim2.fromScale(x, y); t.Size = UDim2.fromScale(w, h)
	t.Parent = parent
	return t
end
-- this screen's own layer on a board's Gui (made again each time)
local function layer(name: string): (Frame?, Vector2)
	local part = boards[name]
	local g = part and part.Parent and part:FindFirstChild("Gui")
	if not part or not g or not g:IsA("SurfaceGui") then return nil, Vector2.zero end
	local old = g:FindFirstChild("Mine")
	if old then old:Destroy() end
	local f = Instance.new("Frame")
	f.Name = "Mine"; f.BackgroundTransparency = 1; f.Size = UDim2.fromScale(1, 1)
	f.Parent = g
	-- (its size in pixels: the face's size in studs times the Gui's pixels per stud)
	local face = g.Face
	local sz = part.Size
	local w, h = sz.X, sz.Y
	if face == Enum.NormalId.Left or face == Enum.NormalId.Right then w, h = sz.Z, sz.Y
	elseif face == Enum.NormalId.Top or face == Enum.NormalId.Bottom then w, h = sz.X, sz.Z end
	return f, Vector2.new(w, h) * g.PixelsPerStud
end
local function comma(n: number?): string
	local s = tostring(math.floor(tonumber(n) or 0))
	local out = s:reverse():gsub("(%d%d%d)", "%1,"):reverse()
	return (out:gsub("^,", ""))
end
local function pct(a: number?, b: number?): string
	local x, y = tonumber(a) or 0, tonumber(b) or 0
	return if y > 0 then ("%d%%"):format(math.floor(x / y * 100 + 0.5)) else "—"
end
-- the upper step: your rank's badge, your name, @handle, level
local function fillName()
	local f, px = layer("MirrorPodiumName")
	if not f then return end
	local r = Ranks.of(me:GetAttribute("Xp") :: any)
	local bs = math.floor(px.Y * 0.84)
	local ok, b = pcall(Ranks.badge, f, bs, r)
	if ok and b then b.AnchorPoint = Vector2.new(0, 0.5); b.Position = UDim2.new(0, math.floor(px.Y * 0.12), 0.5, 0) end
	local x0 = (px.Y * 1.1) / math.max(px.X, 1)
	label(f, "Name", string.upper(me.DisplayName), x0, 0.06, 0.66 - x0, 0.58, PALE, Enum.FontWeight.Heavy, Enum.TextXAlignment.Left)
	label(f, "Handle", "@" .. me.Name, x0, 0.66, 0.66 - x0, 0.28, GREY, Enum.FontWeight.SemiBold, Enum.TextXAlignment.Left)
	label(f, "Rank", string.upper(r.name), 0.66, 0.1, 0.31, 0.42, AMBER, Enum.FontWeight.Heavy, Enum.TextXAlignment.Right)
	label(f, "Level", ("LEVEL %d"):format(r.level), 0.66, 0.56, 0.31, 0.32, GREY, Enum.FontWeight.Bold, Enum.TextXAlignment.Right)
end
-- the lower step: five tiles of your numbers
local function fillStats()
	local f = layer("MirrorPodiumStats")
	if not f then return end
	local s = myCard and myCard.stats
	local ok = type(s) == "table"
	local k, d = if ok then tonumber(s.k) or 0 else 0, if ok then tonumber(s.d) or 0 else 0
	local w = myCard and type(myCard.weapons) == "table" and myCard.weapons[1]
	local e = type(w) == "table" and type(w.id) == "string" and Roster.byId[w.id]
	local tiles = {
		{ "KILLS", if ok then comma(k) else "—" },
		{ "K/D", if not ok then "—" elseif d > 0 then ("%.2f"):format(k / d) elseif k > 0 then ("%.2f"):format(k) else "—" },
		{ "WINS", if ok then comma(s.w) else "—" },
		{ "HEADSHOT %", if ok then pct(s.hs, s.hc) else "—" },
		{ "BEST STREAK", if ok then tostring(tonumber(s.best) or 0) else "—" },
		{ "MOST HELD", if e then string.upper(e.name) elseif type(w) == "table" then string.upper(tostring(w.id)) else "—" },
	}
	local n = #tiles
	for i, t in tiles do
		local x = (i - 1) / n
		label(f, "K" .. i, t[1], x + 0.012, 0.1, 1 / n - 0.024, 0.24, GREY, Enum.FontWeight.Bold)
		label(f, "V" .. i, t[2], x + 0.012, 0.38, 1 / n - 0.024, 0.5, if i == n then AMBER else PALE, Enum.FontWeight.Heavy)
		if i > 1 then
			local line = Instance.new("Frame")
			line.Name = "Rule"; line.BackgroundColor3 = DEEP; line.BorderSizePixel = 0
			line.Position = UDim2.fromScale(x, 0.14); line.Size = UDim2.new(0, 2, 0.72, 0)
			line.Parent = f
		end
	end
end
local function askCard()
	if asking then return end
	asking = true
	task.spawn(function()
		local rem = RS:FindFirstChild("JankfireRemotes")
		local pr = rem and rem:FindFirstChild("Profile")
		if pr and pr:IsA("RemoteFunction") then
			local ok, res = pcall(function() return pr:InvokeServer("card", me.UserId) end)
			if ok and type(res) == "table" and res.ok and type(res.card) == "table" then myCard = res.card end
		end
		asking = false
		fillStats()
	end)
end
local function boardsStep()
	local spot = mirrorSpot
	local ch = me.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not spot or not root or not next(boards) then return end
	if me:GetAttribute("Zone") ~= "training" then return end
	local now = os.clock()
	local xp = me:GetAttribute("Xp")
	if now - filledAt > 30 or xp ~= filledXp then
		filledAt, filledXp = now, xp
		fillName(); fillStats(); askCard()
	end
end

-- ---------------------------------------------------------------- somebody else's range Carls
-- (RangeTest: every runner has his own Carls, each with the attribute Owner = his UserId.) this screen keeps only its
-- own in its world; the rest go into a folder outside it, so they are not drawn, aimed at or outlined, and no blood
-- flies off them (Arsenal). the local player's attribute ViewAs (a UserId: Studio's photo of what another runner
-- sees) shows that runner's instead
local away = Instance.new("Folder")
away.Name = "OthersCarls"
local function viewer(): number
	local v = me:GetAttribute("ViewAs")
	return if type(v) == "number" then v else me.UserId
end
local function sortCarl(m: Instance)
	if not m:IsA("Model") then return end
	local o = m:GetAttribute("Owner")
	if type(o) ~= "number" then return end
	if o ~= viewer() then
		if m.Parent and m.Parent ~= away then m.Parent = away end
	elseif m.Parent == away then
		local dm = workspace:FindFirstChild("Dummies")
		if dm then m.Parent = dm end
	end
end
local function resort()
	local dm = workspace:FindFirstChild("Dummies")
	if dm then for _, m in dm:GetChildren() do sortCarl(m) end end
	for _, m in away:GetChildren() do sortCarl(m) end
end
task.spawn(function()
	local dm = workspace:WaitForChild("Dummies", 120)
	if not dm then return end
	dm.ChildAdded:Connect(function(m: Instance) task.defer(sortCarl, m) end)
	resort()
end)
me:GetAttributeChangedSignal("ViewAs"):Connect(resort)

-- ---------------------------------------------------------------- find the training area's pieces (it can be rebuilt)
local seen: Instance? = nil
local look, doorMoving = 0, true
local function scan()
	local tg = trainingGround()
	local lot = tg and tg:FindFirstChild("Lot")
	local d = lot and lot:FindFirstChild("Door")
	if d and (not door or door.m ~= d or #door.slats == 0) then door = readRoller(d); doorMoving = true
	elseif not d then door = nil end
	if tg ~= seen then
		seen = tg
		table.clear(shutters)
		pit = nil
		mirrorSpot = nil
		table.clear(boards); filledAt = -math.huge
		if tg then
			for _, m in tg:GetDescendants() do
				if m:GetAttribute("Shutter") == true then
					local c, n = m:GetAttribute("Center"), m:GetAttribute("Near")
					local r = readRoller(m)
					if typeof(c) == "Vector3" and #r.slats > 0 then
						table.insert(shutters, { r = r, center = c, near = if type(n) == "number" then n else 12, u = 0, from = 0, goal = 0, since = 0, dur = 1, lastNear = -math.huge })
					end
				elseif m.Name == "LongJumpPit" and m:IsA("BasePart") then
					pit = m
				elseif m.Name == "MirrorSpot" and m:IsA("BasePart") then
					mirrorSpot = m
				elseif (m.Name == "MirrorPodiumName" or m.Name == "MirrorPodiumStats") and m:IsA("BasePart") then
					boards[m.Name] = m
				end
			end
		end
	end
end

RunService.RenderStepped:Connect(function(dt: number)
	look += dt
	if look > 2 then look = 0; scan() end
	local now = workspace:GetServerTimeNow()
	local clock = os.clock()
	-- the lot's door
	local dr = door
	if dr and dr.m.Parent then
		local u, moving = doorU(dr.m, now)
		local off, shaking = rattleOff(dr.m, now)
		if moving or shaking or doorMoving then place(dr, u, off) end
		doorMoving = moving or shaking
	end
	-- shutters
	for _, s in shutters do
		local near = anyoneNear(s.center, s.near)
		if near then s.lastNear = clock end
		local goal = if near or clock - s.lastNear < 0.8 then 1 else 0
		if goal ~= s.goal then
			s.from, s.goal, s.since = s.u, goal, clock
			s.dur = if goal == 1 then 1.1 else 1.4
			Sfx.play("whirr", s.center + Vector3.new(0, 5, 0), 0.9, if goal == 1 then 0.8 else 0.65)
		end
		local a = (clock - s.since) / s.dur
		if a <= 1.05 then
			s.u = s.from + (s.goal - s.from) * ease(a)
			place(s.r, s.u, Vector3.zero)
			if a >= 1 and s.goal == 0 and s.u ~= 0 then s.u = 0 end
		end
	end
	-- laser gates
	for _, g in gates do
		local near = anyoneNear(g.center, g.near)
		if near then g.lastNear = clock end
		if near and not g.off then setLasers(g, true)
		elseif not near and g.off and clock - g.lastNear > 0.6 then setLasers(g, false) end
	end
	-- the long jump
	local ch = me.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	if root and hum then jumpWatch(root, hum) end
	mirrorStep(dt)
	boardsStep()
end)
scan()
