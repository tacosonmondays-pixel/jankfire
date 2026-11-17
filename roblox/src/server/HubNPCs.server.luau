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
--   Idle: an animation (Studio's prompt-to-animation tool) looped with no pop (two copies crossfading at each end); none:
--   Roblox's own idle or sit. Extra: a one-shot now and then over it (ExtraEvery = Vector2 seconds), while seated
--   Walk: the walk played while they move (none: Roblox's own)
--   Moves on the place: "seats" (stand, walk to another seat, sit: MoveEvery = Vector2 seconds between), "teleport" (a
--   soft puff, gone, a puff at another spot), "loop" (walk round the points in order, pausing at the stops), "pingpong"
--   (now and then walk to a neighbouring stop). their points are parts tagged "NPCPoint": Who, Index (1 = where they
--   start), Kind ("seat" / "spot" / "stop" / "via"), Pose ("sit" / "stand"), Pause (Vector2), facing = the part's own;
--   a seat's Approach and Aisle (Vector3s on the floor; the place's Door joins the two aisles). they walk only along
--   those, which the builder lays clear of walls and furniture, and wait while a player stands in their way. all of it
--   in one Heartbeat loop: an anchored body's CFrame, no physics
local Players = game:GetService("Players")
local CollectionService = game:GetService("CollectionService")
local ServerStorage = game:GetService("ServerStorage")
local RunService = game:GetService("RunService")
local Debris = game:GetService("Debris")

local TAG, POINT = "HubNPC", "NPCPoint"
local WALK = 5 -- studs a second
local ANIM = { -- Roblox's own default animations
	[Enum.HumanoidRigType.R15] = { stand = "rbxassetid://507766388", sit = "rbxassetid://2506281703", walk = "rbxassetid://507777826" },
	[Enum.HumanoidRigType.R6] = { stand = "rbxassetid://180435571", sit = "rbxassetid://178130996", walk = "rbxassetid://180426354" },
}

local function userIdOf(spot: BasePart): number?
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

-- an animation that can be started and stopped: a generated clip loops with no pop where it ends (two tracks, the next
-- fading in as the last runs out); a default one simply loops
type Ctl = { start: (number?) -> (), stop: (number?) -> () }
local function anim(animator: Animator, id: string, priority: Enum.AnimationPriority, speed: number, seamless: boolean): Ctl?
	local a = Instance.new("Animation"); a.AnimationId = id
	local ok1, t1 = pcall(function() return animator:LoadAnimation(a) end)
	if not ok1 or not t1 then return nil end
	if not seamless then
		t1.Looped = true; t1.Priority = priority
		return { start = function(f) if not t1.IsPlaying then t1:Play(f or 0.4, 1, speed) end end, stop = function(f) t1:Stop(f or 0.4) end }
	end
	local ok2, t2 = pcall(function() return animator:LoadAnimation(a) end)
	if not ok2 or not t2 then return nil end
	for _, t in { t1, t2 } do t.Looped = false; t.Priority = priority end
	local on, cur = false, t1
	task.spawn(function()
		while animator.Parent do
			if not on or cur.Length <= 0 then task.wait(0.2); continue end
			local left = (cur.Length - cur.TimePosition) / speed
			if left > 0.8 then task.wait(math.min(left - 0.75, 1)); continue end
			if not on then continue end
			local nxt = if cur == t1 then t2 else t1
			nxt:Play(0.7, 1, speed); cur:Stop(0.7)
			cur = nxt
			task.wait(0.9)
		end
	end)
	return {
		start = function(f) if on then return end; on = true; cur = t1; t1:Play(f or 0.4, 1, speed) end,
		stop = function(f) on = false; t1:Stop(f or 0.4); t2:Stop(f or 0.4) end,
	}
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

local npcs = {} -- the ones that move

local function place(spot: BasePart)
	if spot:GetAttribute("Built") then return end
	spot:SetAttribute("Built", true)
	local who = spot:GetAttribute("Who") or spot.Name
	local m = avatar(spot, who)
	if not m then return end
	m.Name = "Regular_" .. who
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
	m.PrimaryPart = root
	local pose = if spot:GetAttribute("Pose") == "sit" and spot:IsA("Seat") then "sit" else "stand"
	local skip = { m }
	for _, r in CollectionService:GetTagged(TAG) do table.insert(skip, r) end
	for _, r in CollectionService:GetTagged(POINT) do table.insert(skip, r) end
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
	-- animations
	local animator = hum:FindFirstChildOfClass("Animator") or Instance.new("Animator")
	animator.Parent = hum
	local def = ANIM[hum.RigType] or ANIM[Enum.HumanoidRigType.R15]
	local function ctlFor(attr: string, fallback: string, priority: Enum.AnimationPriority, speed: number): Ctl?
		local id = spot:GetAttribute(attr)
		local c = if type(id) == "string" and id ~= "" then anim(animator, id, priority, 1, true) else nil
		return c or anim(animator, fallback, priority, speed, false)
	end
	local idle = ctlFor("Idle", def[pose], Enum.AnimationPriority.Idle, if pose == "stand" then 0.8 else 1)
	local standIdle = if pose == "sit" then anim(animator, def.stand, Enum.AnimationPriority.Idle, 0.8, false) else nil
	local walk = ctlFor("Walk", def.walk, Enum.AnimationPriority.Movement, 0.9)
	if idle then idle.start(0.3) end
	local n = {
		who = who, m = m, root = root, hip = hip, sitOffset = sitOffset, skip = skip,
		pose = pose, seated = pose == "sit", idle = idle, standIdle = standIdle, walk = walk,
		mode = spot:GetAttribute("Moves"), points = {}, at = 1, path = nil, i = 0, final = nil, waitUntil = 0, blockedSince = nil,
		moveEvery = spot:GetAttribute("MoveEvery"), door = spot:GetAttribute("Door"),
	}
	local extra, every = spot:GetAttribute("Extra"), spot:GetAttribute("ExtraEvery")
	if type(extra) == "string" and extra ~= "" then
		local a = Instance.new("Animation"); a.AnimationId = extra
		local ok, t = pcall(function() return animator:LoadAnimation(a) end)
		if ok and t then
			t.Looped = false; t.Priority = Enum.AnimationPriority.Action
			local range = if typeof(every) == "Vector2" then every else Vector2.new(15, 30)
			task.spawn(function()
				while m.Parent do
					task.wait(range.X + math.random() * math.max(range.Y - range.X, 0))
					if not m.Parent then break end
					if not n.seated or n.path then continue end -- (a seated one-shot, while sitting still)
					t:Play(0.6)
					local t0 = os.clock()
					while t.Length <= 0 and os.clock() - t0 < 5 do task.wait(0.1) end
					task.wait(math.max(t.Length - 0.7, 0.2))
					t:Stop(0.7)
				end
			end)
		end
	end
	local role, badge = spot:GetAttribute("Role"), spot:GetAttribute("Badge")
	label(m, tostring(who), if type(role) == "string" then role else nil, m:FindFirstChild("Head") :: BasePart?, if type(badge) == "string" then badge else nil)
	-- their points, if they move
	if type(n.mode) == "string" then
		for _, p in CollectionService:GetTagged(POINT) do
			if p:IsA("BasePart") and p:GetAttribute("Who") == who then table.insert(n.points, p) end
		end
		table.sort(n.points, function(a, b) return (a:GetAttribute("Index") or 0) < (b:GetAttribute("Index") or 0) end)
		if #n.points > 1 then
			n.waitUntil = os.clock() + 5 + math.random() * 8
			table.insert(npcs, n)
		end
	end
end

-- ---------------------------------------------------------------- moving
local function rest(n, p: BasePart)
	-- at a point: sit on a seat, or stand facing the way the point faces
	if p:GetAttribute("Pose") == "sit" and n.sitOffset then
		n.root.CFrame = p.CFrame * n.sitOffset
		n.seated = true
		if n.standIdle then n.standIdle.stop(0.4) end
		if n.idle then n.idle.start(0.5) end
	else
		n.root.CFrame = yawCF(Vector3.new(p.Position.X, floorAt(p.Position, n.skip) + n.hip, p.Position.Z), yawOf(p.CFrame))
		n.seated = false
		if n.pose == "sit" then
			if n.idle then n.idle.stop(0.4) end
			if n.standIdle then n.standIdle.start(0.4) end
		elseif n.idle then n.idle.start(0.5) end
	end
end
local function walkTo(n, list: { Vector3 }, final: BasePart)
	-- off along a path of floor points (heights put right as they go), ending at a point
	n.path = list; n.i = 1; n.final = final
	if n.idle then n.idle.stop(0.3) end
	if n.standIdle then n.standIdle.stop(0.3) end
	n.seated = false
	if n.walk then n.walk.start(0.3) end
end
local function choose(n): number?
	local pts, mode = n.points, n.mode
	if mode == "teleport" then
		local j = n.at
		while j == n.at do j = math.random(1, #pts) end
		puff(n.root.Position)
		rest(n, pts[j]); n.at = j
		puff(n.root.Position)
		return 60 + math.random() * 60
	elseif mode == "seats" then
		local j = n.at
		while j == n.at do j = math.random(1, #pts) end
		local a, b = pts[n.at], pts[j]
		local list = { a:GetAttribute("Approach"), a:GetAttribute("Aisle") }
		if a:GetAttribute("Aisle") ~= b:GetAttribute("Aisle") then table.insert(list, n.door); table.insert(list, b:GetAttribute("Aisle")) end
		table.insert(list, b:GetAttribute("Approach"))
		for _, v in list do if typeof(v) ~= "Vector3" then return 30 end end
		walkTo(n, list, b); n.at = j
		return nil
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
			if pts[j]:GetAttribute("Kind") ~= "via" then break end
			table.insert(list, pts[j].Position)
		end
		if j == cur then return 10 end
		walkTo(n, list, pts[j]); n.at = j
		return nil
	end
	return 30
end

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

RunService.Heartbeat:Connect(function(dt)
	local now = os.clock()
	for _, n in npcs do
		if not n.m.Parent then continue end
		if not n.path then
			if now >= n.waitUntil then
				local wait = choose(n)
				if wait then n.waitUntil = now + wait end
			end
			continue
		end
		-- walking: along the path's floor points, then onto the final point (a seat: straight into the seated place)
		local root = n.root
		local pos = root.Position
		local lastLeg = n.i > #n.path
		local f = n.final
		local target = if not lastLeg then n.path[n.i] elseif f:GetAttribute("Pose") == "sit" and n.sitOffset then (f.CFrame * n.sitOffset).Position else f.Position
		if not (lastLeg and f:GetAttribute("Pose") == "sit" and n.sitOffset) then target = Vector3.new(target.X, floorAt(target, n.skip) + n.hip, target.Z) end
		local d = target - pos
		local dist = d.Magnitude
		if dist < 0.15 then
			if lastLeg then
				if n.walk then n.walk.stop(0.4) end
				n.path = nil
				rest(n, f)
				local pause, every = f:GetAttribute("Pause"), n.moveEvery
				n.waitUntil = now + (if typeof(pause) == "Vector2" then pause.X + math.random() * (pause.Y - pause.X)
					elseif typeof(every) == "Vector2" then every.X + math.random() * (every.Y - every.X) else 8)
			else
				n.i += 1
			end
			continue
		end
		local flat = Vector3.new(d.X, 0, d.Z)
		local face = if flat.Magnitude > 0.05 then flat.Unit else root.CFrame.LookVector
		if blocked(pos + face * 1.8) then
			if not n.blockedSince then
				n.blockedSince = now
				if n.walk then n.walk.stop(0.3) end
				if n.pose == "stand" and n.idle then n.idle.start(0.3) elseif n.standIdle then n.standIdle.start(0.3) end
			end
			continue
		elseif n.blockedSince then
			n.blockedSince = nil
			if n.pose == "stand" and n.idle then n.idle.stop(0.3) elseif n.standIdle then n.standIdle.stop(0.3) end
			if n.walk then n.walk.start(0.3) end
		end
		local npos = pos + d.Unit * math.min(WALK * dt, dist)
		-- turn smoothly toward the way they walk; at the end of the last leg, toward the point's own facing
		local want = math.atan2(-face.X, -face.Z)
		if lastLeg and dist < 1.2 then want = yawOf(f.CFrame) end
		local have = yawOf(root.CFrame)
		local dy = (want - have + math.pi) % (2 * math.pi) - math.pi
		root.CFrame = yawCF(npos, have + dy * math.min(1, dt * 8))
	end
end)

CollectionService:GetInstanceAddedSignal(TAG):Connect(function(s) if s:IsA("BasePart") then task.spawn(place, s) end end)
for _, s in CollectionService:GetTagged(TAG) do if s:IsA("BasePart") then task.spawn(place, s) end end
