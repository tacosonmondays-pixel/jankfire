--!nonstrict
-- the hub's regulars: the owner's friends about the hub in their own avatars (owner, 16 Nov: "Can you put these two as
-- NPCs somewhere?", "This one too"). every part tagged "HubNPC" is a regular's place (HubRotunda's B.npc leaves them;
-- any builder may): attributes Who (the name to show), User (their Roblox username), UserId (optional, else looked up),
-- Pose ("sit" on the Seat that is the place, or "stand" on its spot), Role (the word after their name over them), Badge
-- (a player attribute: HubNPCs.client puts a dot after their name while it is true for you).
-- at server start each one's avatar is built from their user id as R15 (one kind of animation fits all of them); if
-- that fails, the saved copy ServerStorage.JankfireNPCs.<Who>. they can't be pushed (always anchored), shot (no queries,
-- no touches) or killed. one label over them; any ProximityPrompt on their place (theirs, or one another script adds
-- later) is moved onto their body so it goes where they go.
-- what they do (owner, 17 Nov: "Can they have idle animations? ..." and "Can Trisangle sometimes stand up and then sit
-- back down on other seats? Maybe Looticus has a teleport ability but will always be in that room, Dune can walk around
-- the gym and Frisk can move to different spots on the railing?"):
--   this script only moves their bodies and says what they are doing; their clips are played on each player's own
--   screen (HubNPCs.client), from the body's attributes: Pose, Idle, StandIdle, Walk, Rise / Settle (with RiseLen /
--   SettleLen), Extra (ExtraLen), ExtraStand (ExtraStandLen), and as they go Phase ("seated", "stood", "rise", "settle", "walk", "turn"), PhaseAt
--   (the server's time it began), PhaseLen (how long a rise or settle takes), WalkRate (the walk's speed), ExtraAt (a
--   one-shot began). (a clip the server played would be lost on a screen once ZoneCull had taken the Rotunda out of
--   that player's world and brought it back)
--   Idle: their clip (Studio's prompt-to-animation tool, or motion capture); none: Roblox's own sit, or their avatar's
--   own idle. Extra: a one-shot now and then over it while they keep still (ExtraEvery = Vector2 seconds; a seated
--   one's while seated); ExtraStand: a seated one's while they stand somewhere
--   Walk: their own avatar's walk (its animation pack's, or Roblox's own: the Animate their avatar comes with), sped
--   to how fast they really go so the feet don't slide; Walk (attribute): only if the avatar has none
--   Rise / Settle: standing up from a seat and sitting down on one (made with the same tool, uploaded with their hips
--   kept still: the body itself goes along the hips' own path in the clip, RISE / SETTLE below)
--   Moves on the place: "seats" (stand, walk to another seat, sit: MoveEvery = Vector2 seconds between), "teleport" (a
--   soft puff, gone, a puff at another spot), "loop" (walk round the points in order, pausing at the stops), "pingpong"
--   (now and then walk to a neighbouring stop). their points are parts tagged "NPCPoint": Who, Index (1 = where they
--   start), Kind ("seat" / "spot" / "stop" / "via"), Pose ("sit" / "stand"), Pause (Vector2), facing = the part's own;
--   a seat's Stand (where they stand in front of it, clear of it), Approach and Aisle (Vector3s on the floor; the
--   place's Door joins the two aisles). they walk only along those, which the builder lays clear of walls and
--   furniture (HubRotunda's R.check sweeps a body-sized box along every one), and wait while a player stands in their
--   way. an anchored body's CFrame, no physics; each regular's own thread, awake only while they move
-- getting up and sitting down (owner, 17 Nov: "When they stand make sure they don't stand in their seats like clipped
-- into it! Idk how you would do it but make them leaving their seat natural?"): they stand up out of the seat onto its
-- Stand point (forward over the feet, then up), take a step out to the Approach before turning, and at the next seat
-- stop on its Stand point, turn their back to it and sit down (down, then back onto the seat). Looticus stands up
-- first, puffs away from in front of his seat, puffs in standing in front of the next one, and sits.
-- not stiff (owner, 17 Nov: "also the animations seem really stiff.."): walking eases in and out (no constant-speed
-- glide), turns on the spot before walking off, and the walk runs at the speed they really go; HubNPCs.client fades
-- every change of clip, varies each idle and lays a small living layer over every clip
local Players = game:GetService("Players")
local CollectionService = game:GetService("CollectionService")
local ServerStorage = game:GetService("ServerStorage")
local RunService = game:GetService("RunService")
local Debris = game:GetService("Debris")

local TAG, POINT = "HubNPC", "NPCPoint"
local WALK = 5 -- studs a second
local ACCEL, BRAKE = 9, 6 -- studs a second, a second: getting going, stopping
-- a walk clip's own speed: Roblox's Animate plays its walk at full speed at 6.4 studs a second on a body of the
-- standard height (HipHeight 2) and in proportion on taller or shorter ones; packs are made to the same
local WALK_NATURAL = 6.4
local STAND_OUT = 1.9 -- (a seat with no Stand: they stand this far in front of it)
-- where the body is through a transition, as parts of the way from one place to the other at each tenth of the clip:
-- h along the floor, v up or down. from the clips' own hips (their LowerTorso's travel, which the uploaded clips leave
-- out; the motion-capture clips' hips, 17 Nov): standing up, a lean first, then forward over the feet and up; sitting
-- down, back and down together through the middle of the clip
local RISE = { h = { 0, 0, 0, 0.01, 0.17, 0.36, 0.56, 0.76, 0.86, 0.94, 1 }, v = { 0, 0, 0, 0, 0.09, 0.48, 0.82, 0.94, 0.97, 0.98, 1 } }
local SETTLE = { h = { 0, 0.01, 0.07, 0.18, 0.42, 0.7, 0.9, 0.99, 1, 1, 1 }, v = { 0, 0, 0.01, 0.04, 0.16, 0.43, 0.76, 1, 1, 1, 1 } }
local DEF = { stand = "rbxassetid://507766388", sit = "rbxassetid://2506281703", walk = "rbxassetid://507777826" } -- (Roblox's own, R15)

local function userIdOf(spot: BasePart): number?
	-- (the zombies entrance's guide, 20 Nov 2026: a plain dummy, ServerStorage.JankfireNPCs.ZombieGuide, until the owner picks a
	-- friend: Map.Hub's attribute ZombieGuideUserId = their user id puts that avatar at every hub's zombies door)
	if spot:GetAttribute("Who") == "ZombieGuide" then
		local map = workspace:FindFirstChild("Map")
		local hub = map and map:FindFirstChild("Hub")
		local g = hub and hub:GetAttribute("ZombieGuideUserId")
		return if type(g) == "number" and g > 0 then g else nil
	end
	local id = spot:GetAttribute("UserId")
	if type(id) == "number" and id > 0 then return id end
	local name = spot:GetAttribute("User")
	if type(name) ~= "string" then return nil end
	for _ = 1, 3 do
		local ok, res = pcall(function() return Players:GetUserIdFromNameAsync(name) end)
		if ok and res then spot:SetAttribute("UserId", res); return res end
		task.wait(2)
	end
	return nil
end

local function avatar(spot: BasePart, who: string): Model?
	local id = userIdOf(spot)
	if id then
		for _ = 1, 2 do
			local ok, m = pcall(function()
				local desc = Players:GetHumanoidDescriptionFromUserId(id)
				return Players:CreateHumanoidModelFromDescription(desc, Enum.HumanoidRigType.R15)
			end)
			if ok and m then return m end
			task.wait(2)
		end
	end
	local lib = ServerStorage:FindFirstChild("JankfireNPCs")
	local saved = lib and lib:FindFirstChild(who)
	if saved and saved:IsA("Model") then return saved:Clone() end
	warn("[jankfire] no avatar for the hub's " .. who)
	return nil
end

local function label(m: Model, text: string, role: string?, head: BasePart?, badge: string?)
	local bb = Instance.new("BillboardGui")
	bb.Name = "NameLabel"; bb.Size = UDim2.new(if role then 8.5 else 5, 0, 0.9, 0); bb.StudsOffsetWorldSpace = Vector3.new(0, 1.9, 0)
	bb.LightInfluence = 0; bb.MaxDistance = 45; bb.AlwaysOnTop = false; bb.Adornee = head
	local t = Instance.new("TextLabel")
	t.BackgroundTransparency = 1; t.Size = UDim2.fromScale(1, 1); t.TextScaled = true; t.RichText = true
	-- ("DUNE · QUESTS": the name, then what they do for you in a quieter grey)
	t.Text = if role then ("%s  <font color=\"#98a2ac\">·  %s</font>"):format(string.upper(text), role) else text
	if badge then -- (HubNPCs.client adds a dot for each player whose own attribute named by badge is true: Dune's QuestNews)
		t:SetAttribute("Base", t.Text); t:SetAttribute("BadgeFlag", badge)
		CollectionService:AddTag(t, "RegularBadge")
	end
	t.TextColor3 = Color3.fromRGB(236, 240, 242); t.TextStrokeTransparency = 0.6
	t.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Bold)
	t.Parent = bb
	bb.Parent = head or m
end

-- a soft puff where Looticus leaves and where he lands
local function puff(at: Vector3)
	local p = Instance.new("Part")
	p.Name = "Poof"; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Transparency = 1
	p.Size = Vector3.new(2, 4, 2); p.CFrame = CFrame.new(at)
	local e = Instance.new("ParticleEmitter")
	e.Texture = "rbxasset://textures/particles/smoke_main.dds"
	e.Color = ColorSequence.new(Color3.fromRGB(230, 226, 216))
	e.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1.2), NumberSequenceKeypoint.new(1, 3.2) })
	e.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.45), NumberSequenceKeypoint.new(1, 1) })
	e.Lifetime = NumberRange.new(0.5, 0.8); e.Speed = NumberRange.new(2, 4); e.SpreadAngle = Vector2.new(180, 180)
	e.Drag = 4; e.LightEmission = 0.15; e.Rate = 0
	e.Parent = p
	p.Parent = workspace
	e:Emit(16)
	Debris:AddItem(p, 1.5)
end

-- the floor under a point (the places, the points and every regular left out; the hub's kit pieces don't take rays)
local function floorAt(at: Vector3, skip: { Instance }): number
	local rp = RaycastParams.new(); rp.FilterType = Enum.RaycastFilterType.Exclude; rp.FilterDescendantsInstances = skip; rp.RespectCanCollide = false
	local hit = workspace:Raycast(at + Vector3.new(0, 4, 0), Vector3.new(0, -9, 0), rp)
	return if hit then hit.Position.Y else at.Y
end
local function yawCF(pos: Vector3, yaw: number): CFrame return CFrame.new(pos) * CFrame.Angles(0, yaw, 0) end
local function yawOf(cf: CFrame): number local lv = cf.LookVector; return math.atan2(-lv.X, -lv.Z) end
local function turnBy(from: number, to: number): number return (to - from + math.pi) % (2 * math.pi) - math.pi end
local function ease(x: number): number x = math.clamp(x, 0, 1); return x * x * (3 - 2 * x) end
local function along(list: { number }, k: number): number -- (a tenths table read at k, 0..1)
	local x = math.clamp(k, 0, 1) * (#list - 1)
	local i = math.min(math.floor(x), #list - 2)
	return list[i + 1] + (list[i + 2] - list[i + 1]) * (x - i)
end
local function idOf(v: any): string? return if type(v) == "string" and v ~= "" then v else nil end

local npcs = {} -- the ones that move
-- seats players sit on too (19 Nov 2026, the owner: "seats in the lounge are sittable ... loot will wait until there is
-- a seat open if they're all being sat on", "seats in vip room work too"): the hub's builder tags the regulars' seat
-- points HubSeat, so HubSeats gives each one a Sit prompt. while a regular sits on one its NpcHere is true (HubSeats
-- hides its prompt then); a seat a player sits on (SeatTaken while NpcHere isn't) is passed by: the regular picks
-- another, or waits while every one is taken
local function npcHere(p: Instance?, on: boolean)
	if p and p:IsA("BasePart") and p:GetAttribute("NpcHere") ~= on then p:SetAttribute("NpcHere", on) end
end
local function takenByPlayer(p: BasePart): boolean return p:GetAttribute("SeatTaken") == true and p:GetAttribute("NpcHere") ~= true end

-- what they are doing now, for every screen (HubNPCs.client plays the clips from it)
local function setPhase(n, phase: string, len: number?)
	n.m:SetAttribute("PhaseLen", len or 0)
	n.m:SetAttribute("PhaseAt", workspace:GetServerTimeNow())
	n.m:SetAttribute("Phase", phase)
end

local function place(spot: BasePart)
	if spot:GetAttribute("Built") then return end
	spot:SetAttribute("Built", true)
	local who = spot:GetAttribute("Who") or spot.Name
	local m = avatar(spot, who)
	if not m then return end
	m.Name = "Regular_" .. who
	-- (their avatar's Animate, before the scripts go: its walk and idle, a pack's or Roblox's own)
	local function own(folder: string): string?
		local a = m:FindFirstChild("Animate")
		local f = a and a:FindFirstChild(folder)
		local x = f and f:FindFirstChildWhichIsA("Animation")
		return x and idOf(x.AnimationId)
	end
	local ownWalk, ownIdle = own("walk"), own("idle")
	local hum = m:FindFirstChildOfClass("Humanoid")
	local root = m:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not hum or not root then m:Destroy(); return end
	for _, d in m:GetDescendants() do
		if d:IsA("LuaSourceContainer") or d:IsA("Sound") then d:Destroy()
		elseif d:IsA("BasePart") then d.CanQuery = false; d.CanTouch = false; d.CastShadow = true end
	end
	hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	hum.BreakJointsOnDeath = false
	hum.MaxHealth = math.huge; hum.Health = math.huge
	hum:SetStateEnabled(Enum.HumanoidStateType.Dead, false)
	hum:SetStateEnabled(Enum.HumanoidStateType.Ragdoll, false)
	hum:SetStateEnabled(Enum.HumanoidStateType.FallingDown, false)
	if not hum:FindFirstChildOfClass("Animator") then Instance.new("Animator").Parent = hum end -- (each screen plays on it)
	m.PrimaryPart = root
	local pose = if spot:GetAttribute("Pose") == "sit" and spot:IsA("Seat") then "sit" else "stand"
	local skip = { m }
	for _, r in CollectionService:GetTagged(TAG) do table.insert(skip, r) end
	for _, r in CollectionService:GetTagged(POINT) do table.insert(skip, r) end
	-- their clips, for every screen
	m:SetAttribute("Who", who)
	m:SetAttribute("Pose", pose)
	m:SetAttribute("Idle", idOf(spot:GetAttribute("Idle")) or (if pose == "sit" then DEF.sit else ownIdle or DEF.stand))
	m:SetAttribute("StandIdle", ownIdle or DEF.stand)
	m:SetAttribute("Walk", ownWalk or idOf(spot:GetAttribute("Walk")) or DEF.walk)
	for _, k in { "Rise", "Settle", "RiseLen", "SettleLen", "Extra", "ExtraLen", "ExtraStand", "ExtraStandLen" } do
		local v = spot:GetAttribute(k)
		if v ~= nil then m:SetAttribute(k, v) end
	end
	m:SetAttribute("WalkRate", 1)
	m:SetAttribute("Phase", if pose == "sit" then "seated" else "stood")
	m.Parent = spot.Parent
	-- standing: the root's height over the floor (a scaled avatar's longer legs put on the floor). seated: how the root
	-- sits on a seat, measured once by sitting on this place's Seat, then kept with the body anchored
	local hip = hum.HipHeight + root.Size.Y / 2
	root.Anchored = true
	do
		local fy = floorAt(spot.Position, skip)
		m:PivotTo(yawCF(Vector3.new(spot.Position.X, fy + hip, spot.Position.Z), yawOf(spot.CFrame)))
		local low = math.huge
		for _, p in m:GetDescendants() do if p:IsA("BasePart") and p.Transparency < 1 then low = math.min(low, p.Position.Y - p.Size.Y / 2) end end
		if low < fy - 0.05 and low > fy - 3 then hip += fy - low; m:PivotTo(m:GetPivot() + Vector3.new(0, fy - low, 0)) end
	end
	local sitOffset: CFrame? = nil
	if pose == "sit" then
		local seat = spot :: Seat
		root.Anchored = false
		m:PivotTo(seat.CFrame * CFrame.new(0, 3, 0))
		seat.Disabled = false
		seat:Sit(hum)
		task.wait(0.3)
		sitOffset = seat.CFrame:ToObjectSpace(root.CFrame)
		local w = seat:FindFirstChild("SeatWeld"); if w then w:Destroy() end
		seat.Disabled = true
		hum.Sit = false
		root.Anchored = true
		m:PivotTo(seat.CFrame * sitOffset)
	end
	-- prompts go onto the body (and any added to the place later: the shop's VIP daily reward on Trisangle's)
	local at = Instance.new("Attachment"); at.Name = "PromptAt"; at.Position = Vector3.new(0, 1, 0); at.Parent = root
	local function adopt(d: Instance) if d:IsA("ProximityPrompt") then task.defer(function() d.Parent = at end) end end
	for _, d in spot:GetDescendants() do adopt(d) end
	spot.DescendantAdded:Connect(adopt)
	local n = {
		who = who, m = m, root = root, hip = hip, sitOffset = sitOffset, skip = skip, pose = pose, seated = pose == "sit",
		natural = WALK_NATURAL * math.max(hum.HipHeight, 0.5) / 2,
		mode = spot:GetAttribute("Moves"), points = {}, at = 1, busy = false, extraOn = false, speed = 1, kick = false, forceTo = nil,
		moveEvery = spot:GetAttribute("MoveEvery"), door = spot:GetAttribute("Door"),
	}
	setPhase(n, if pose == "sit" then "seated" else "stood")
	-- a one-shot now and then while they keep still: a seated one's Extra while seated, its ExtraStand while standing;
	-- a standing one's Extra (every screen plays the one that fits how they are: HubNPCs.client)
	local every = spot:GetAttribute("ExtraEvery")
	if idOf(spot:GetAttribute("Extra")) or idOf(spot:GetAttribute("ExtraStand")) then
		local range = if typeof(every) == "Vector2" then every else Vector2.new(15, 30)
		task.spawn(function()
			while m.Parent do
				task.wait(range.X + math.random() * math.max(range.Y - range.X, 0))
				if not m.Parent then break end
				if n.busy then continue end
				local standing = n.pose == "sit" and not n.seated
				if not idOf(m:GetAttribute(if standing then "ExtraStand" else "Extra")) then continue end
				local len = m:GetAttribute(if standing then "ExtraStandLen" else "ExtraLen")
				n.extraOn = true
				m:SetAttribute("ExtraAt", workspace:GetServerTimeNow())
				task.wait(if type(len) == "number" and len > 0 then len else 4)
				n.extraOn = false
			end
		end)
	end
	CollectionService:AddTag(m, "HubRegular") -- (HubNPCs.client: their clips and the living layer)
	local role, badge = spot:GetAttribute("Role"), spot:GetAttribute("Badge")
	if not spot:GetAttribute("NoLabel") then -- (NoLabel: no name text, the zombies guide's until the owner picks a friend)
		label(m, tostring(who), if type(role) == "string" then role else nil, m:FindFirstChild("Head") :: BasePart?, if type(badge) == "string" then badge else nil)
	end
	-- their points, if they move
	if type(n.mode) == "string" then
		local hub = spot:GetAttribute("Hub") -- (the three hubs, 20 Nov: each has its own copy of every regular; a place and its points share Hub, none = the ring)
		for _, p in CollectionService:GetTagged(POINT) do
			if p:IsA("BasePart") and p:GetAttribute("Who") == who and p:GetAttribute("Hub") == hub then table.insert(n.points, p) end
		end
		table.sort(n.points, function(a, b) return (a:GetAttribute("Index") or 0) < (b:GetAttribute("Index") or 0) end)
		if n.seated and n.points[1] and n.points[1]:GetAttribute("Pose") == "sit" then npcHere(n.points[1], true) end -- (they start on their first point)
		if #n.points > 1 then table.insert(npcs, n) end
	end
end

-- ---------------------------------------------------------------- moving
local function blocked(ahead: Vector3): boolean
	for _, pl in Players:GetPlayers() do
		local ch = pl.Character
		local r = ch and ch:FindFirstChild("HumanoidRootPart")
		if r then
			local d = r.Position - ahead
			if math.abs(d.Y) < 5 and Vector3.new(d.X, 0, d.Z).Magnitude < 2.6 then return true end
		end
	end
	return false
end
local function seatedAt(n, p: BasePart): CFrame return p.CFrame * n.sitOffset end
-- where they stand at a point, the root at standing height: in front of a seat (its Stand), facing the way it faces
local function standOf(n, p: BasePart): CFrame
	local s = p:GetAttribute("Stand")
	local at = if typeof(s) == "Vector3" then s elseif p:GetAttribute("Pose") == "sit" then p.CFrame * Vector3.new(0, 0, -STAND_OUT) else p.Position
	return yawCF(Vector3.new(at.X, floorAt(at, n.skip) + n.hip, at.Z), yawOf(p.CFrame))
end
local function isSeat(n, p: BasePart): boolean return p:GetAttribute("Pose") == "sit" and n.sitOffset ~= nil end
local function setRate(n, r: number) n.m:SetAttribute("WalkRate", math.floor(r * 100 + 0.5) / 100) end

-- a transition between seated and standing ("rise" / "settle"): every screen plays its clip over the time it takes
-- here while the body goes from one place to the other along the clip's own hips (w: RISE or SETTLE)
local function transition(n, kind: string, from: CFrame, to: CFrame, w)
	local own = n.m:GetAttribute(if kind == "rise" then "RiseLen" else "SettleLen")
	local len = (if type(own) == "number" and own > 0 then own else 1.2) / n.speed
	setPhase(n, kind, len)
	local ya, dy = yawOf(from), turnBy(yawOf(from), yawOf(to))
	local t = 0
	while t < len and n.m.Parent do
		t += RunService.Heartbeat:Wait()
		local k = t / len
		local h, v = along(w.h, k), along(w.v, k)
		n.root.CFrame = yawCF(Vector3.new(from.X + (to.X - from.X) * h, from.Y + (to.Y - from.Y) * v, from.Z + (to.Z - from.Z) * h), ya + dy * h)
	end
	n.root.CFrame = to
end
local function getUp(n, p: BasePart): boolean
	if not n.seated then return true end
	local to = standOf(n, p)
	if blocked(to.Position) then return false end -- (someone right in front of them: later)
	while n.extraOn do task.wait(0.2) end
	transition(n, "rise", n.root.CFrame, to, RISE)
	n.seated = false
	npcHere(p, false)
	setPhase(n, "stood")
	return true
end
local function sitDown(n, p: BasePart)
	transition(n, "settle", n.root.CFrame, seatedAt(n, p), SETTLE)
	n.seated = true
	npcHere(p, true)
	setPhase(n, "seated")
end
-- turn on the spot (stepping round: the walk at a slow step while they turn)
local function turnTo(n, yaw: number)
	local root = n.root
	local have = yawOf(root.CFrame)
	local dy = turnBy(have, yaw)
	if math.abs(dy) < 0.05 then return end
	local dur, pos, t = (0.3 + math.abs(dy) / math.pi * 0.6) / n.speed, root.Position, 0
	setRate(n, 0.55 * n.speed)
	setPhase(n, "turn", dur)
	while t < dur and n.m.Parent do
		t += RunService.Heartbeat:Wait()
		root.CFrame = yawCF(pos, have + dy * ease(t / dur))
	end
	setPhase(n, "stood")
end
-- walk along floor points (each on its own floor), easing in at the start and braking to stop at the end, turning
-- smoothly the way they go, the walk's speed told to every screen as it changes; they wait while a player stands in
-- their way
local function walkAlong(n, list: { Vector3 })
	local root = n.root
	local pts = { root.Position }
	for _, p in list do table.insert(pts, Vector3.new(p.X, floorAt(p, n.skip) + n.hip, p.Z)) end
	local total = 0
	for i = 1, #pts - 1 do total += (pts[i + 1] - pts[i]).Magnitude end
	if total < 0.05 then return end
	-- far round from the way they face: turn on the spot first
	for i = 2, #pts do
		local d = pts[i] - pts[1]
		if Vector3.new(d.X, 0, d.Z).Magnitude > 0.3 then
			local want = math.atan2(-d.X, -d.Z)
			if math.abs(turnBy(yawOf(root.CFrame), want)) > math.rad(35) then turnTo(n, want) end
			break
		end
	end
	local sp = n.speed
	local top, acc, brake = WALK * sp, ACCEL * sp * sp, BRAKE * sp * sp
	setRate(n, 0.1)
	setPhase(n, "walk")
	local i, gone, v, shown = 1, 0, 0, 0.1 -- (the leg, how far along it, the speed, the walk's rate last told)
	while i < #pts and n.m.Parent do
		local a, b = pts[i], pts[i + 1]
		local leg = (b - a).Magnitude
		if gone >= leg - 1e-3 then i += 1; gone = 0; continue end
		local dir = (b - a) / leg
		local flat = Vector3.new(dir.X, 0, dir.Z)
		local face = if flat.Magnitude > 0.05 then flat.Unit else root.CFrame.LookVector
		local pos = root.Position
		if blocked(pos + face * 1.8) then
			setPhase(n, "stood")
			repeat task.wait(0.25) until not n.m.Parent or not blocked(pos + face * 1.8)
			v = 0; shown = 0.1
			setRate(n, 0.1)
			setPhase(n, "walk")
			continue
		end
		local dt = RunService.Heartbeat:Wait()
		local left = leg - gone -- (what is left of the whole way: brake in time to stop at its end)
		for k = i + 1, #pts - 1 do left += (pts[k + 1] - pts[k]).Magnitude end
		v = math.min(v + acc * dt, top, math.sqrt(2 * brake * math.max(left, 0)) + 0.15 * sp)
		gone = math.min(gone + v * dt, leg)
		local have = yawOf(root.CFrame)
		root.CFrame = yawCF(a + dir * gone, have + turnBy(have, math.atan2(-face.X, -face.Z)) * math.min(1, dt * 7 * sp))
		local r = math.max(v / n.natural, 0.1) -- (the walk's rate: how fast they go over what the clip is made for)
		if math.abs(r - shown) > 0.05 then shown = r; setRate(n, r) end
	end
	setPhase(n, "stood")
end
-- at a point with nothing in between (after a fault): sat on a seat, or stood facing its way
local function rest(n, p: BasePart)
	if isSeat(n, p) and not takenByPlayer(p) then
		n.root.CFrame = seatedAt(n, p); n.seated = true; npcHere(p, true); setPhase(n, "seated")
	else
		n.root.CFrame = standOf(n, p); n.seated = false; npcHere(p, false); setPhase(n, "stood")
	end
end
local function pauseAt(n, p: BasePart): number
	local pause, every = p:GetAttribute("Pause"), n.moveEvery
	if typeof(pause) == "Vector2" then return pause.X + math.random() * (pause.Y - pause.X) end
	if typeof(every) == "Vector2" then return every.X + math.random() * (every.Y - every.X) end
	return 8
end
-- one move (blocking while it lasts); how long to wait before the next
local function move(n): number
	local pts, mode = n.points, n.mode
	local a = pts[n.at]
	local function pick(): number? -- (another of their points; never a seat a player sits on; nil: every one is taken)
		local f = n.forceTo
		if type(f) == "number" and f >= 1 and f <= #pts and f ~= n.at and not takenByPlayer(pts[f]) then return f end
		local free = {}
		for j, p in pts do if j ~= n.at and not takenByPlayer(p) then table.insert(free, j) end end
		if #free == 0 then return nil end
		return free[math.random(1, #free)]
	end
	if mode == "teleport" then
		local j = pick()
		if not j then return 6 end -- (every other place taken: wait for one to come free)
		local b = pts[j]
		local there = standOf(n, b)
		if blocked(there.Position) then return 5 end
		if not getUp(n, a) then return 5 end
		task.wait(0.5 / n.speed)
		puff(n.root.Position)
		n.root.CFrame = there; n.at = j
		setPhase(n, "stood")
		puff(there.Position)
		if isSeat(n, b) then
			task.wait(0.7 / n.speed)
			if takenByPlayer(b) then return 6 end -- (someone sat down on it as they came: they stand, and go on soon)
			sitDown(n, b)
		end
		return 60 + math.random() * 60
	elseif mode == "seats" then
		local j = pick()
		if not j then return 6 end -- (every other seat taken: wait for one to come free)
		local b = pts[j]
		-- out of the seat, a step out to the front of it, round by the aisles (the door joins the two sides), to the
		-- front of the other, onto its stand point; their back to it; down. (R.check sweeps a body along the same)
		local list = { a:GetAttribute("Approach") }
		if a:GetAttribute("Aisle") ~= b:GetAttribute("Aisle") then
			table.insert(list, a:GetAttribute("Aisle")); table.insert(list, n.door); table.insert(list, b:GetAttribute("Aisle"))
		end
		table.insert(list, b:GetAttribute("Approach"))
		for _, v in list do if typeof(v) ~= "Vector3" then return 30 end end
		table.insert(list, standOf(n, b).Position)
		if not getUp(n, a) then return 5 end
		task.wait(0.35 / n.speed)
		walkAlong(n, list)
		n.at = j
		turnTo(n, yawOf(b.CFrame))
		if isSeat(n, b) then
			if takenByPlayer(b) then return 4 end -- (someone sat down on it while they walked over: they stand, then try another)
			task.wait(0.2 / n.speed); sitDown(n, b)
		end
		return pauseAt(n, b)
	elseif mode == "loop" or mode == "pingpong" then
		-- the next stop (loop: onward round; pingpong: a neighbour either way), through the "via" points between
		local count, cur = #pts, n.at
		local dir = if mode == "loop" then 1 else (if math.random() < 0.5 then -1 else 1)
		if mode == "pingpong" and (cur + dir < 1 or cur + dir > count) then dir = -dir end
		local list, j = {}, cur
		for _ = 1, count do
			j += dir
			if mode == "loop" then j = (j - 1) % count + 1 end
			if j < 1 or j > count then return 10 end
			table.insert(list, pts[j].Position)
			if pts[j]:GetAttribute("Kind") ~= "via" then break end
		end
		if j == cur then return 10 end
		walkAlong(n, list)
		n.at = j
		turnTo(n, yawOf(pts[j].CFrame))
		return pauseAt(n, pts[j])
	end
	return 30
end
local function nap(n, secs: number) -- (cut short by the test hook)
	local t0 = os.clock()
	while os.clock() - t0 < secs and not n.kick do task.wait(0.2) end
	n.kick = false
end
local function life(n)
	nap(n, 5 + math.random() * 8)
	while n.m.Parent do
		n.busy = true
		n.m:SetAttribute("MoveCount", (n.m:GetAttribute("MoveCount") or 0) + 1)
		local ok, res = pcall(move, n)
		n.busy = false; n.speed = 1; n.forceTo = nil
		if not ok then
			warn("[jankfire] the hub's " .. n.who .. ": " .. tostring(res))
			pcall(rest, n, n.points[n.at])
			res = 20
		end
		nap(n, res)
	end
end
-- the test hook (Play tests; in ServerStorage, so only the server's own code reaches it):
--   JankNPCTest:Invoke("move", who, to?, speed?) -> "ok": who moves now (to = their point's index; speed < 1 slows the
--   whole move, 0.25 = a quarter, for photos). "where", who -> their point, phase, seated, the root's position
local hook = Instance.new("BindableFunction")
hook.Name = "JankNPCTest"
hook.OnInvoke = function(op, who, to, speed)
	for _, n in npcs do
		if n.who ~= who then continue end
		if op == "move" then
			if n.busy then return "busy" end
			n.forceTo = to; n.speed = math.clamp(tonumber(speed) or 1, 0.1, 2); n.kick = true
			return "ok"
		elseif op == "where" then
			local p = n.root.Position
			return ("%s: point %d, phase %s, seated %s, busy %s, moves %d, at (%.2f, %.2f, %.2f)"):format(n.who, n.at, tostring(n.m:GetAttribute("Phase")), tostring(n.seated), tostring(n.busy), n.m:GetAttribute("MoveCount") or 0, p.X, p.Y, p.Z)
		end
	end
	return "no regular called " .. tostring(who)
end
hook.Parent = ServerStorage

local started = {}
local function begin(s: Instance)
	if not s:IsA("BasePart") then return end
	place(s)
	for _, n in npcs do
		if not started[n] then started[n] = true; task.spawn(life, n) end
	end
end
CollectionService:GetInstanceAddedSignal(TAG):Connect(function(s) task.spawn(begin, s) end)
for _, s in CollectionService:GetTagged(TAG) do task.spawn(begin, s) end
