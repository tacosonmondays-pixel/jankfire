--!strict
-- the training area's doors and gates as each player sees them (16 Nov 2026, from the owner's play test: "when you go
-- up to garage doors can they slide up", "when you go to the laser gate, when you get close you hear a click and the
-- laser gate turns off?", and the course's pit: "is that going to be something?"):
--   * the back lot's garage door (Hub.TrainingGround.Lot.Door): the server (TheLot) decides when it moves and sets the
--     Door's attributes From, Goal, Dur and Since (server time). this rolls the slats up smoothly, into the head one by
--     one. Rattle (server time): the door jumps a hand's width and drops (LOCKED)
--   * roll-up shutters: a Model with the attribute Shutter (the muster's gate home). it rolls up while anyone is within
--     Near studs of its Center and rolls down once they are 2 studs past that (so it can't flip-flop at the edge). only
--     on screen: its slats never block (walk in and the gate's trigger takes you home). each one is a state, how far up
--     it is, that moves toward open or shut every frame, so a reversal midway carries on from where it is. (17 Nov, the
--     owner: "sometimes when you go through the door to the training hub, the door is stuck halfway open until you get
--     near it, it then resets and opens up and closes": going home, ZoneCull takes the training area out of your world
--     mid-close, and the area's rescan forgot the shutter, then met it again as shut with its slats left halfway. now
--     the shutters outlive the area leaving your world, and one that comes back, or is met for the first time, is set
--     straight to where it should be for who is near it, with no replay)
--   * laser gates: anything tagged LaserGate (CollectionService). its parts named LaserBar and LaserField (or marked with
--     the attribute Laser: the playground's gate home, StructurePass) switch off with
--     a click while anyone is within Near (an attribute, default 9) of it, and back on with a click once they are gone.
--     a gate's own builder only has to tag it
--   * the course's long-jump pit (a part LongJumpPit with the attribute Edge, the take-off line's z): slide down the
--     lane, jump at the line, and how far you got shows when you land
--   * the mirror (the muster's bay; a part MirrorSpot): while you are in training you stand there as a hologram in the
--     hub's style (see-through, a soft fill and outline, turning slowly over its lens), holding what you hold. the owner,
--     16 Nov: "it can be a hologram version of your avatar"; it stands on a plain round projector
--   * the range's Carls: every runner has his own (RangeTest); this screen keeps only its own in its world
--   * the gun shop's keeper (ShopKeeper.server builds him): his idle (his attribute Idle: the owner's "cute sway waiting
--     at the cases") loops here as two copies crossfading at each end, and he waves when WaveAt (server time) moves on.
--     played here, not on the server: ZoneCull takes the training area out of your world while you are away, and the
--     server's tracks don't come back with it. it starts again whenever he is back in your world
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
type Shutter = { r: Roller, center: Vector3, near: number, lin: number, goal: number, lastNear: number, shown: boolean }
local shutters: { Shutter } = {}
local SHUTTER_UP, SHUTTER_DOWN, SHUTTER_SLACK, SHUTTER_LINGER = 1.1, 1.4, 2, 0.8 -- (seconds up, seconds down, studs, seconds)

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
local holoSig = ""
local HOLO = Color3.fromRGB(143, 216, 255)
local HOLO_SCALE = 1.8 -- (the owner, 16 Nov: "can hologram you be larger?": nearly twice you, still under the bay's ceiling)
-- the look: the game's one hologram (ReplicatedStorage.Jankfire.Hologram, the VFX session's: ice-blue, an outline,
-- scanlines, a sweep as it builds in), as the hub's holograms; this script's own plain tint if it is not there
local holoMod = game:GetService("ReplicatedStorage"):WaitForChild("Jankfire"):FindFirstChild("Hologram")
local Holo: any = nil
if holoMod and holoMod:IsA("ModuleScript") then
	local ok, h = pcall(require, holoMod)
	if ok then Holo = h end
end
local function dropHolo()
	if holo then
		if Holo then pcall(function() local h = Holo.of(holo); if h then h:remove(0) end end) end
		holo:Destroy(); holo = nil
	end
	holoSig = ""
end
-- (16 Nov evening, the owner's lag report, 12 fps in training: the mirror was a full 1.8x clone of your avatar with
-- its layered clothing, an Animator playing, scanline textures on every face and a new CFrame every frame. it is a
-- still statue now: a plain copy (no layered clothing, nothing in its hands), posed once in Roblox's idle and then
-- anchored, its Humanoid and joints gone, facing out of the bay; the hologram look without scanlines, glitch or
-- flicker; made only when your character is (a spawn, a new look). nothing about it runs per frame)
local holoFor: Model? = nil
local holoBusy = false
local function buildHolo(ch: Model, spot: BasePart)
	dropHolo()
	holoFor = ch
	local realHum = ch:FindFirstChildOfClass("Humanoid")
	local realRoot = ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not realHum or not realRoot then return end
	local up = (realHum.HipHeight + realRoot.Size.Y / 2) * HOLO_SCALE
	local was = ch.Archivable
	ch.Archivable = true
	local ok, c = pcall(function() return ch:Clone() end)
	ch.Archivable = was
	if not ok or not c then return end
	local m = c :: Model
	m.Name = "MirrorHolo"
	for _, d in m:GetChildren() do
		-- (what it holds, and layered clothing: a WrapLayer deforms over the body every frame)
		if d:IsA("Tool") or d.Name == "HeldWeapon" or (d:IsA("Accessory") and d:FindFirstChildWhichIsA("WrapLayer", true)) then d:Destroy() end
	end
	for _, d in m:GetDescendants() do
		if d:IsA("BaseScript") or d:IsA("Sound") or d:IsA("ParticleEmitter") or d:IsA("Light") or d:IsA("BillboardGui")
			or d:IsA("ProximityPrompt") or d:IsA("Highlight") or d:IsA("Beam") or d:IsA("Trail") or d:IsA("WrapTarget") or d:IsA("WrapLayer") then
			d:Destroy()
		elseif d:IsA("BasePart") then
			d.Anchored = d.Name == "HumanoidRootPart"; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
			d.CastShadow = false; d.Massless = true; d.LocalTransparencyModifier = 0
			if not Holo and d.Transparency < 1 then d.Transparency = math.max(d.Transparency, 0.3) end
		elseif d:IsA("Decal") and not Holo then
			d.Transparency = math.max(d.Transparency, 0.4)
		end
	end
	local hum = m:FindFirstChildOfClass("Humanoid")
	if hum then
		hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
		hum.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
		hum.PlatformStand = true
	end
	if not Holo then
		local hl = Instance.new("Highlight")
		hl.FillColor = HOLO; hl.OutlineColor = HOLO; hl.FillTransparency = 0.8; hl.OutlineTransparency = 0.4
		hl.DepthMode = Enum.HighlightDepthMode.Occluded
		hl.Parent = m
	end
	m.Parent = workspace
	pcall(function() m:ScaleTo(HOLO_SCALE) end)
	pcall(function() m:PivotTo(spot.CFrame * CFrame.new(0, up + 0.1, 0)) end)
	holo = m
	-- the pose: Roblox's own idle for a moment, then frozen where it is
	local an = hum and hum:FindFirstChildOfClass("Animator")
	if an and hum then
		local a = Instance.new("Animation")
		a.AnimationId = if hum.RigType == Enum.HumanoidRigType.R6 then "rbxassetid://180435571" else "rbxassetid://507766388"
		pcall(function() an:LoadAnimation(a):Play(0) end)
	end
	holoBusy = true
	task.delay(0.35, function()
		holoBusy = false
		if holo ~= m or not m.Parent then return end
		for _, d in m:GetDescendants() do if d:IsA("BasePart") then d.Anchored = true end end
		for _, d in m:GetDescendants() do
			if d:IsA("JointInstance") or d:IsA("WeldConstraint") or d:IsA("Humanoid") or d:IsA("AnimationController") then d:Destroy() end
		end
		if Holo then pcall(function() Holo.apply(m, { build = 1.5, lines = false, glitch = false, flicker = 0, see = 0.84 }) end) end -- (see 0.84: with no scanlines the neon body bloomed white)
	end)
end
local function mirrorStep(_dt: number)
	local spot = mirrorSpot
	local ch = me.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	if not spot or not spot.Parent or not ch or not hum then dropHolo(); holoFor = nil; return end
	-- (always there while you are in training: the owner, 16 Nov: "can your big hologram just be active always?")
	if me:GetAttribute("Zone") ~= "training" then dropHolo(); holoFor = nil; return end
	if holoBusy then return end
	if not holo or not holo.Parent or holoFor ~= ch then buildHolo(ch, spot) end
end
-- a new look (the avatar editor, a respawn's appearance arriving late): the statue is made again
me.CharacterAppearanceLoaded:Connect(function() holoFor = nil end)

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

-- ---------------------------------------------------------------- the gun shop's keeper: his sway and wave
type Keeper = { m: Model, t1: AnimationTrack, t2: AnimationTrack, cur: AnimationTrack?, wave: AnimationTrack?, waveAt: number }
local keeper: Keeper? = nil
local function keeperOf(m: Instance): Keeper?
	if not m:IsA("Model") then return nil end
	local hum = m:FindFirstChildOfClass("Humanoid")
	local an = hum and hum:FindFirstChildOfClass("Animator")
	local id = m:GetAttribute("Idle")
	if not an or type(id) ~= "string" or id == "" then return nil end -- (not ready yet: the next look tries again)
	local a = Instance.new("Animation"); a.AnimationId = id
	local ok1, t1 = pcall(function() return an:LoadAnimation(a) end)
	local ok2, t2 = pcall(function() return an:LoadAnimation(a) end)
	if not ok1 or not ok2 or not t1 or not t2 then return nil end
	for _, t in { t1, t2 } do t.Looped = false; t.Priority = Enum.AnimationPriority.Idle end
	local wave: AnimationTrack? = nil
	local wid = m:GetAttribute("Wave")
	if type(wid) == "string" and wid ~= "" then
		local w = Instance.new("Animation"); w.AnimationId = wid
		local okW, tw = pcall(function() return an:LoadAnimation(w) end)
		if okW and tw then tw.Looped = false; tw.Priority = Enum.AnimationPriority.Action; wave = tw end
	end
	local at = m:GetAttribute("WaveAt")
	return { m = m, t1 = t1, t2 = t2, cur = nil, wave = wave, waveAt = if type(at) == "number" then at else 0 }
end
local function keeperStep()
	local k = keeper
	if not k then return end
	if not k.m:IsDescendantOf(workspace) then k.cur = nil; return end -- (out of your world: start afresh when he is back)
	local cur = k.cur
	if not cur or not (k.t1.IsPlaying or k.t2.IsPlaying) then
		k.t2:Stop(0); k.t1:Play(0.4); k.cur = k.t1
	elseif cur.Length > 0 and cur.Length - cur.TimePosition < 0.75 then
		local nxt = if cur == k.t1 then k.t2 else k.t1
		nxt:Play(0.7); cur:Stop(0.7); k.cur = nxt
	end
	local at = k.m:GetAttribute("WaveAt")
	if type(at) == "number" and at > k.waveAt then
		k.waveAt = at
		if k.wave and workspace:GetServerTimeNow() - at < 2 then k.wave:Play(0.15) end
	end
end

-- ---------------------------------------------------------------- find the training area's pieces (it can be rebuilt)
local seen: Instance? = nil
local look, doorMoving = 0, true
local function scan()
	local tg = trainingGround()
	local lot = tg and tg:FindFirstChild("Lot")
	local d = lot and lot:FindFirstChild("Door")
	if d and (not door or door.m ~= d or #door.slats == 0) then door = readRoller(d); doorMoving = true
	elseif not d then door = nil end
	-- (the shop's keeper: Range.Shop.Stock.ShopKeeper, made at server start)
	local range = tg and tg:FindFirstChild("Range")
	local shop = range and range:FindFirstChild("Shop")
	local stock = shop and shop:FindFirstChild("Stock")
	local km = stock and stock:FindFirstChild("ShopKeeper")
	if km and (not keeper or keeper.m ~= km) then keeper = keeperOf(km)
	elseif tg and not km then keeper = nil end
	-- (a nil area is one ZoneCull has taken out of your world for now: keep what we know, it comes back as it was)
	if tg and tg ~= seen then
		seen = tg
		table.clear(shutters)
		pit = nil
		mirrorSpot = nil
		if tg then
			for _, m in tg:GetDescendants() do
				if m:GetAttribute("Shutter") == true then
					local c, n = m:GetAttribute("Center"), m:GetAttribute("Near")
					local r = readRoller(m)
					if typeof(c) == "Vector3" and #r.slats > 0 then
						local near = if type(n) == "number" then n else 12
						-- (met for the first time: straight to open or shut, for who is near it now)
						local up = if anyoneNear(c, near) then 1 else 0
						place(r, up, Vector3.zero)
						table.insert(shutters, { r = r, center = c, near = near, lin = up, goal = up, lastNear = if up == 1 then os.clock() else -math.huge, shown = true })
					end
				elseif m.Name == "LongJumpPit" and m:IsA("BasePart") then
					pit = m
				elseif m.Name == "MirrorSpot" and m:IsA("BasePart") then
					mirrorSpot = m
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
	-- shutters: open inside Near, shut once everyone is SHUTTER_SLACK past it (and SHUTTER_LINGER after); how far up it
	-- is moves toward that every frame
	for _, s in shutters do
		local near = anyoneNear(s.center, if s.goal == 1 then s.near + SHUTTER_SLACK else s.near)
		if near then s.lastNear = clock end
		local goal = if near or clock - s.lastNear < SHUTTER_LINGER then 1 else 0
		if not s.r.m:IsDescendantOf(workspace) then s.shown = false; continue end -- (out of your world: nothing to move)
		if not s.shown then
			-- (back in your world: straight to where it should be, no replay and no sound)
			s.shown, s.goal, s.lin = true, goal, goal
			place(s.r, goal, Vector3.zero)
			continue
		end
		if goal ~= s.goal then
			s.goal = goal
			Sfx.play("whirr", s.center + Vector3.new(0, 5, 0), 0.9, if goal == 1 then 0.8 else 0.65)
		end
		if s.lin ~= goal then
			local step = dt / (if goal == 1 then SHUTTER_UP else SHUTTER_DOWN)
			s.lin = if goal > s.lin then math.min(goal, s.lin + step) else math.max(goal, s.lin - step)
			place(s.r, ease(s.lin), Vector3.zero)
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
	keeperStep()
end)
scan()
