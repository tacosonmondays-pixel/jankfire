--!strict
-- the training area's doors and gates as each player sees them (16 Nov 2026, from the owner's play test: "when you go
-- up to garage doors can they slide up", "when you go to the laser gate, when you get close you hear a click and the
-- laser gate turns off?", and the course's pit: "is that going to be something?"):
--   * the back lot's garage door (Hub.TrainingGround.Lot.Door): the server (TheLot) decides when it moves and sets the
--     Door's attributes From, Goal, Dur and Since (server time). this rolls the slats up smoothly, into the head one by
--     one. Rattle (server time): the door jumps a hand's width and drops (LOCKED). if you have found the egg (your
--     attribute LotKey, from your save: owner, 17 Nov, "once you find the golden dummies, the main garage is
--     permanently open for you") it is up on your screen whatever the server's door does, and its slats and DoorBlock
--     don't stop you (your own body is yours to move; the anti-cheat skips this door): straight up when you get there,
--     rolling up with the reveal when you earn it
--   * the panel over that door: your own hunt (owner, 17 Nov, from the friends' preview: "yellow dummies to enter
--     outside once shot by someone dont appear for others"). TheLot gives every player their own three gold Carls (the
--     Carls sort below keeps only yours in your world) and their own 90 s; your attributes LotGold (bits 1, 2, 4: the
--     ones you have found) and LotGoldBy (server time your clock runs out) say how far you are. one cardboard man lit
--     per gold Carl you found and your clock; all three and OPEN if you have the key or the door is up. a ding at the
--     panel and a chime where he stood when you find one, the door's whirr when you find the third, a buzz when your
--     time runs out: on your screen only
--   * roll-up shutters: a Model with the attribute Shutter (the muster's gate home), in the training area or anywhere
--     tagged "Shutter" (the hub's gate to here, GateKit: both sides are the same door). it rolls up while anyone is within
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
--     hub's style, holding what you hold the way everyone else sees you hold it (ThirdPerson's hold), a still statue.
--     the owner, 16 Nov: "it can be a hologram version of your avatar"; it stands on a plain round projector
--   * the gold dummies' door (a Model tagged EggDoor, TrainingLot's eggDoor; owner, 17 Nov: the dead end "should be the
--     locked door connected to the dummies", opening onto a portal to the playground): on a key holder's screen (LotKey)
--     it rolls up as they come within Near of it (and down once they are SHUTTER_SLACK past) onto the dark doorway, the
--     plate reads OPEN, and its slats and EggBlock don't stop them (the doorway's trigger, Doors.EggPortal, takes only
--     key holders: LaserDoors). for everyone else it stays down; walk up to it and it rattles, clatters, and
--     LOCKED flashes, on your screen only
--   * one-way doors (a Model tagged OneWayDoor: the basement's walk-out onto the range's far terrace, TrainingLot; owner,
--     17 Nov, "can you make the exit actually connect to an exit"): its leaf (parts with Shut) swings Swing radians
--     about its Hinge on your screen while you are in its Inside box, and stays open while you are within Near of its
--     Center after (through the doorway and away); its leaf and Block don't stop you while it is open. from the other
--     side it never opens: nobody in the hall gets down to the lot that way. a click when it opens and when it shuts
--   * the range's Carls: every runner has his own (RangeTest); this screen keeps only its own in its world. the back
--     lot's gold Carls the same way: everyone has their own (TheLot)
--   * the gun shop's keeper (ShopKeeper.server builds him): his idle (his attribute Idle: the owner's "cute sway waiting
--     at the cases"; one clip or a few, the first most of the time) loops here, crossfading at each end, and he waves
--     when WaveAt (server time) moves on. his gaze (owner, 17 Nov: "can my character look down I look high or at
--     least down and track the palyer"): a layer on his neck and waist joints, on this screen only (a Motor6D's C0, or
--     an AnimationConstraint's Attachment0, as HubNPCs.client does the regulars'), over whatever clip plays: his eyes
--     lowered to the counter while nobody is near, and turned to the nearest player within GAZE.range in front of him,
--     eased, with a short hold before he turns to someone else
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
local KEY_UP = 4.2 -- (seconds to roll up on your screen when you earn the key: the egg's reveal)
local keyU: number? = nil -- (how far up it is on a key holder's screen; nil = set it straight up when next in your world)
local keyShown: number? = nil
local function doorU(m: Instance, now: number): (number, boolean)
	local from, goal, dur, since = m:GetAttribute("From"), m:GetAttribute("Goal"), m:GetAttribute("Dur"), m:GetAttribute("Since")
	if type(from) ~= "number" or type(goal) ~= "number" or type(dur) ~= "number" or type(since) ~= "number" then return 0, false end
	if dur <= 0 then return goal, false end
	local a = (now - since) / dur
	return from + (goal - from) * ease(a), a < 1.05
end
local function shake(t: number): (Vector3, boolean)
	if t < 0 or t > 0.8 then return Vector3.zero, false end
	local y
	if t < 0.16 then y = 0.55 * math.sin(t / 0.16 * math.pi / 2)        -- up a hand's width
	elseif t < 0.28 then y = 0.55 * (1 - (t - 0.16) / 0.12) ^ 2         -- drops
	else y = 0.14 * math.abs(math.sin((t - 0.28) * 28)) * (1 - (t - 0.28) / 0.52) end -- and bounces
	local x = 0.07 * math.sin(t * 95) * (1 - t / 0.8)
	return Vector3.new(x, y, 0), true
end
local function rattleOff(m: Instance, now: number): (Vector3, boolean)
	local at = m:GetAttribute("Rattle")
	if type(at) ~= "number" then return Vector3.zero, false end
	return shake(now - at)
end

-- a key holder's door lets them through: its slats and block don't collide or stop rays on this screen
local function passDoor(r: Roller)
	for _, s in r.slats do
		if s.p.CanCollide then s.p.CanCollide = false end
		if s.p.CanQuery then s.p.CanQuery = false end
	end
	local blk = r.m.Parent and r.m.Parent:FindFirstChild("DoorBlock")
	if blk and blk:IsA("BasePart") then
		if blk.CanCollide then blk.CanCollide = false end
		if blk.CanQuery then blk.CanQuery = false end
	end
end
me:GetAttributeChangedSignal("LotKey"):Connect(function()
	local dr = door
	-- (earned with the door in front of you: it rolls up from where it is; anywhere else it is up when you get there)
	if me:GetAttribute("LotKey") == true and dr and dr.m:IsDescendantOf(workspace) then keyU = doorU(dr.m, workspace:GetServerTimeNow()) else keyU = nil end
end)

-- ---------------------------------------------------------------- the lot's panel: your own hunt (this screen's)
local lotPanelStep: (now: number) -> ()
do
	local GOLD, PIP_OFF = Color3.fromRGB(242, 184, 75), Color3.fromRGB(198, 192, 181) -- (TheLot's old pair)
	local pips: { { p: BasePart, n: number, lit: boolean? } } = {}
	local timerText: TextLabel? = nil
	local panelOf: Instance? = nil
	local lastBits, lastKey, lastBy = 0, me:GetAttribute("LotKey") == true, 0
	local function lotOf(): Instance?
		local tg = trainingGround()
		return tg and tg:FindFirstChild("Lot")
	end
	local function readPanel(panel: Instance?)
		panelOf = panel
		table.clear(pips)
		timerText = nil
		if not panel then return end
		for _, d in panel:GetDescendants() do
			local n = d:GetAttribute("Pip")
			if d:IsA("BasePart") and type(n) == "number" then table.insert(pips, { p = d, n = n, lit = nil }) end
		end
		local t = panel:FindFirstChild("Timer")
		local g = t and t:FindFirstChild("Gui")
		local l = g and g:FindFirstChild("Text")
		timerText = if l and l:IsA("TextLabel") then l else nil
	end
	-- one of the door's own sounds (in the panel's Timer: Ding, Open, Buzz), a copy on this screen alone
	local function panelSound(name: string)
		local lot = lotOf()
		local panel = lot and lot:FindFirstChild("Panel")
		local t = panel and panel:FindFirstChild("Timer")
		local s = t and t:FindFirstChild(name)
		if not s or not s:IsA("Sound") then return end
		local c = s:Clone()
		c.Parent = t
		c.Ended:Once(function() c:Destroy() end)
		c:Play()
		task.delay(8, function() if c.Parent then c:Destroy() end end)
	end
	local function chimeAt(i: number)
		local lot = lotOf()
		local spots = lot and lot:FindFirstChild("GoldSpots")
		local s = spots and spots:FindFirstChild("Gold" .. i)
		if s and s:IsA("BasePart") then Sfx.play("ting", s.Position) end
	end
	-- your hunt moved on: a find, the last find (the key), or out of time
	local function hunted()
		local b = me:GetAttribute("LotGold")
		local bits = if type(b) == "number" then b else 0
		local by = me:GetAttribute("LotGoldBy")
		if type(by) == "number" then lastBy = by end
		local key = me:GetAttribute("LotKey") == true
		local finished = key and not lastKey and lastBits ~= 0 -- (the third: the server takes your count away as the key comes)
		local got = if finished then 7 else bits
		for i = 1, 3 do
			local m = 2 ^ (i - 1)
			if bit32.btest(got, m) and not bit32.btest(lastBits, m) then panelSound("Ding"); chimeAt(i) end
		end
		if finished then panelSound("Open")
		elseif not key and bits == 0 and lastBits ~= 0 then panelSound("Buzz") end
		lastBits = if key then 0 else bits
		lastKey = key
	end
	-- (the key and the count come together: look once both are here)
	local function soon() task.delay(0.15, hunted) end
	me:GetAttributeChangedSignal("LotGold"):Connect(soon)
	me:GetAttributeChangedSignal("LotKey"):Connect(soon)
	local inWorld = false
	lotPanelStep = function(now: number)
		local dr = door
		if not dr or not dr.m:IsDescendantOf(workspace) then inWorld = false; return end
		local panel = dr.m.Parent and dr.m.Parent:FindFirstChild("Panel")
		if not inWorld or panel ~= panelOf then readPanel(panel) end -- (back in your world or rebuilt: paint it afresh)
		inWorld = true
		local key = me:GetAttribute("LotKey") == true
		local all = key or doorU(dr.m, now) > 0.02
		local b = me:GetAttribute("LotGold")
		local bits = if type(b) == "number" then b else 0
		for _, q in pips do
			local lit = all or bit32.btest(bits, 2 ^ (q.n - 1))
			if q.lit ~= lit and q.p.Parent then
				q.lit = lit
				q.p.Color = if lit then GOLD else PIP_OFF
				q.p.Material = if lit then Enum.Material.Neon else Enum.Material.SmoothPlastic
			end
		end
		local word = "1:30" -- (idle: the plate reads LOCKED, three men, the clock's rule and a hint)
		if all then
			word = "OPEN"
		else
			local by = me:GetAttribute("LotGoldBy")
			if bits ~= 0 and type(by) == "number" then
				local left = math.max(0, math.floor(by - now))
				word = ("%d:%02d"):format(left // 60, left % 60)
			end
		end
		local tl = timerText
		if tl and tl.Text ~= word then tl.Text = word end
	end
end

-- ---------------------------------------------------------------- shutters (on screen only)
type Shutter = { r: Roller, center: Vector3, near: number, lin: number, goal: number, lastNear: number, shown: boolean }
local shutters: { Shutter } = {}
local SHUTTER_UP, SHUTTER_DOWN, SHUTTER_SLACK, SHUTTER_LINGER = 1.1, 1.4, 2, 0.8 -- (seconds up, seconds down, studs, seconds)

-- ---------------------------------------------------------------- one-way doors (this screen's)
type OneWay = { m: Instance, leaf: { Slat }, hinge: CFrame, swing: number, inside: BasePart?, blk: BasePart?, center: Vector3,
	near: number, lin: number, goal: number, shown: boolean, pass: boolean? }
local oneWays: { OneWay } = {}
local ONEWAY_OPEN, ONEWAY_SHUT = 0.45, 0.6 -- (seconds)
local function oneWayOf(m: Instance): OneWay?
	local h, sw, c, n = m:GetAttribute("Hinge"), m:GetAttribute("Swing"), m:GetAttribute("Center"), m:GetAttribute("Near")
	if typeof(h) ~= "CFrame" or typeof(c) ~= "Vector3" then return nil end
	local leaf: { Slat } = {}
	for _, d in m:GetDescendants() do
		local shut = d:GetAttribute("Shut")
		if d:IsA("BasePart") and typeof(shut) == "CFrame" then table.insert(leaf, { p = d, shut = shut }) end
	end
	if #leaf == 0 then return nil end
	local inside, blk = m:FindFirstChild("Inside"), m:FindFirstChild("Block")
	return {
		m = m, leaf = leaf, hinge = h, swing = if type(sw) == "number" then sw else -math.pi / 2,
		inside = if inside and inside:IsA("BasePart") then inside else nil, blk = if blk and blk:IsA("BasePart") then blk else nil,
		center = c, near = if type(n) == "number" then n else 5.5, lin = 0, goal = 0, shown = false, pass = nil,
	}
end
local function inBox(b: BasePart, pos: Vector3): boolean
	local rel = b.CFrame:PointToObjectSpace(pos)
	local h = b.Size / 2
	return math.abs(rel.X) <= h.X and math.abs(rel.Y) <= h.Y and math.abs(rel.Z) <= h.Z
end
local function oneWayPass(o: OneWay, pass: boolean)
	if o.pass == pass then return end
	o.pass = pass
	for _, s in o.leaf do s.p.CanCollide = not pass; s.p.CanQuery = not pass end
	if o.blk then o.blk.CanCollide = not pass; o.blk.CanQuery = not pass end
end
local function oneWayStep(o: OneWay, dt: number, root: BasePart?)
	if not o.m:IsDescendantOf(workspace) then o.shown = false; o.pass = nil; return end -- (out of your world)
	local inn = root ~= nil and o.inside ~= nil and inBox(o.inside :: BasePart, root.Position)
	local near = root ~= nil and (root.Position - o.center).Magnitude <= o.near
	-- open while you are inside; once open, it stays open while you are near it (in the doorway, just through it)
	local goal = if inn or (o.goal == 1 and near) then 1 else 0
	local moved = false
	if not o.shown then
		o.shown, o.goal, o.lin, moved = true, goal, goal, true
	elseif goal ~= o.goal then
		o.goal = goal
		Sfx.play("click", o.center, 0.8, if goal == 1 then 1 else 0.85)
	end
	if o.lin ~= goal then
		local step = dt / (if goal == 1 then ONEWAY_OPEN else ONEWAY_SHUT)
		o.lin = if goal > o.lin then math.min(goal, o.lin + step) else math.max(goal, o.lin - step)
		moved = true
	end
	oneWayPass(o, o.lin > 0 or goal == 1)
	if moved then
		local turn = o.hinge * CFrame.Angles(0, o.swing * ease(o.lin), 0) * o.hinge:Inverse()
		for _, s in o.leaf do if s.p.Parent then s.p.CFrame = turn * s.shut end end
	end
end

-- ---------------------------------------------------------------- the gold dummies' door (this screen's)
type Egg = { r: Roller, center: Vector3, near: number, lin: number, goal: number, shown: boolean, pass: boolean?,
	blk: BasePart?, text: TextLabel?, bumpT: number, was: boolean }
local eggs: { Egg } = {}
local EGG_BUMP, EGG_EVERY = 4.6, 2.4 -- (studs from its middle that count as at it; seconds between rattles)
local LOCKED_GOLD, LOCKED_RED = Color3.fromRGB(242, 184, 75), Color3.fromRGB(255, 92, 72)
local function eggOf(m: Instance): Egg?
	local c, n = m:GetAttribute("Center"), m:GetAttribute("Near")
	local r = readRoller(m)
	if typeof(c) ~= "Vector3" or #r.slats == 0 then return nil end
	local blk = m:FindFirstChild("EggBlock")
	local plate = m:FindFirstChild("EggPlate")
	local text = plate and plate:FindFirstChild("Text", true)
	return {
		r = r, center = c, near = if type(n) == "number" then n else 11, lin = 0, goal = 0, shown = false, pass = nil,
		blk = if blk and blk:IsA("BasePart") then blk else nil,
		text = if text and text:IsA("TextLabel") then text else nil, bumpT = -math.huge, was = false,
	}
end
-- let a key holder's body through (or not): the slats and the block behind them, on this screen
local function eggPass(e: Egg, pass: boolean)
	if e.pass == pass then return end
	e.pass = pass
	for _, sl in e.r.slats do sl.p.CanCollide = not pass; sl.p.CanQuery = not pass end
	if e.blk then e.blk.CanCollide = not pass; e.blk.CanQuery = not pass end
end
local function eggStep(e: Egg, dt: number, clock: number, root: BasePart?)
	if not e.r.m:IsDescendantOf(workspace) then e.shown = false; e.pass = nil; return end -- (out of your world)
	local key = me:GetAttribute("LotKey") == true
	eggPass(e, key)
	local flat, dy = math.huge, math.huge
	if root then
		local d = root.Position - e.center
		flat, dy = Vector3.new(d.X, 0, d.Z).Magnitude, math.abs(d.Y)
	end
	local goal = if key and dy < 9 and flat <= (if e.goal == 1 then e.near + SHUTTER_SLACK else e.near) then 1 else 0
	local moved = false
	if not e.shown then
		e.shown, e.goal, e.lin, moved = true, goal, goal, true -- (back in your world: straight to where it should be)
	elseif goal ~= e.goal then
		e.goal = goal
		Sfx.play("whirr", e.center + Vector3.new(0, 5, 0), 0.9, if goal == 1 then 0.8 else 0.65)
	end
	if e.lin ~= goal then
		local step = dt / (if goal == 1 then SHUTTER_UP else SHUTTER_DOWN)
		e.lin = if goal > e.lin then math.min(goal, e.lin + step) else math.max(goal, e.lin - step)
		moved = true
	end
	-- locked: at it without the key, it rattles (a hand's width up and down), clatters, and LOCKED flashes
	if not key and dy < 9 and flat <= EGG_BUMP and clock - e.bumpT > EGG_EVERY then
		e.bumpT = clock
		Sfx.play("clatter", e.center + Vector3.new(0, 4, 0), 0.85)
	end
	local off, shaking = shake(clock - e.bumpT)
	if moved or shaking or e.was then place(e.r, ease(e.lin), off) end
	e.was = shaking
	if e.text then
		local word = if key then "OPEN" else "LOCKED"
		if e.text.Text ~= word then e.text.Text = word end
		local t = clock - e.bumpT
		local col = if not key and t < 0.78 and (t % 0.26) < 0.14 then LOCKED_RED else LOCKED_GOLD
		if e.text.TextColor3 ~= col then e.text.TextColor3 = col end
	end
end

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
-- (19 Nov, the owner: "Hologram in the training hub spawns in as you normalally then renders as hologram..": the copy
-- stood on the spot looking like you while ThirdPerson drew the gun into its hands, and the old statue went first. now
-- a new statue is made out of sight, HIDE_DOWN studs under its spot (under the floor; ThirdPerson still poses it, it is
-- well inside TP.T.far), and only when it is frozen with its gun does it come up onto the spot, put on the hologram's
-- look (every piece see-through until the build-in sweep's first paint brings them in) and take the old one's place,
-- all in one frame. nobody sees the plain copy; the old statue stays up until then)
local pending: Model? = nil
local HIDE_DOWN = 40
local function dropOne(m: Model?)
	if not m then return end
	if Holo then pcall(function() local h = Holo.of(m); if h then h:remove(0) end end) end
	m:Destroy()
end
local function dropHolo()
	dropOne(holo); holo = nil
	dropOne(pending); pending = nil
	holoSig = ""
end
-- (16 Nov evening, the owner's lag report, 12 fps in training: the mirror was a full 1.8x clone of your avatar with
-- its layered clothing, an Animator playing, scanline textures on every face and a new CFrame every frame. it is a
-- still statue now: a plain copy (no layered clothing), posed once and then anchored, its Humanoid and joints gone,
-- facing out of the bay; the hologram look without scanlines, glitch or flicker. nothing about it runs per frame)
-- (17 Nov, the owner: "the you hologram isnt holding a weapon properly": the copy carried ThirdPerson's own gun,
-- TPGun, welded to its chest while its arms hung in the idle. now, for a moment while it is made, it is a ThirdPerson
-- test rig (tag TPRig, TPWeapon = what you hold, its Skin, TPPlayer = you for your wrap and hat): ThirdPerson builds
-- the gun fresh and puts it in its hands exactly as everyone sees you hold it (the katana in its own stance), at the
-- hip, looking straight out. once the draw is over the body is anchored where it is, the gun copied in as still parts,
-- the tag taken off (ThirdPerson lets go and drops its own copy) and the joints and Humanoid destroyed. your utility:
-- when you use it, the statue holds that item as you do (its use pose, or a throw's wind-up) for ITEM_SHOW seconds,
-- then goes back to your weapon. it is made again only when what you hold changes (a swap, a skin, a wrap or a hat
-- gives you a new HeldWeapon), you respawn, or your look changes)
local ITEM_SHOW = 4
local TPmod: any = nil
local function thirdPerson(): any
	if TPmod == nil then
		local m = script.Parent:FindFirstChild("ThirdPerson")
		local ok, t = pcall(function() return if m then require(m) else nil end)
		TPmod = if ok and t then t else false
	end
	return if TPmod then TPmod else nil
end
local holoFor: Model? = nil
local holoBusy = false
local holoHeld: Instance? = nil -- (the HeldWeapon the statue was made with)
local holoItem: string? = nil -- (an item pose it shows: "laptop:use:0.55"), and until when
local itemUntil = 0
local itemSeen: any = nil
local function buildHolo(ch: Model, spot: BasePart)
	dropOne(pending); pending = nil -- (a half-made one is dropped; the standing statue stays until its successor is ready)
	holoFor = ch
	local hw = ch:FindFirstChild("HeldWeapon")
	holoHeld = hw
	local wid = hw and hw:GetAttribute("Weapon")
	local skin = hw and hw:GetAttribute("Skin")
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
		-- (what it holds, the copies ThirdPerson hung on you (TPGun, TPItem), and layered clothing: a WrapLayer deforms
		-- over the body every frame)
		if d:IsA("Tool") or d.Name == "HeldWeapon" or d.Name == "TPGun" or d.Name == "TPItem"
			or (d:IsA("Accessory") and d:FindFirstChildWhichIsA("WrapLayer", true)) then d:Destroy() end
	end
	-- (your own pose and aim stay with you: it stands at the hip, looking straight out)
	for _, a in { "TP", "Pose", "PoseW", "TPKatPose", "TPClipPose", "TPItemPose", "TPWeapon" } do m:SetAttribute(a, nil) end
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
	local onSpot = spot.CFrame * CFrame.new(0, up + 0.1, 0)
	pcall(function() m:PivotTo(onSpot * CFrame.new(0, -HIDE_DOWN, 0)) end) -- (out of sight before it is in the world)
	m.Parent = workspace
	pcall(function() m:ScaleTo(HOLO_SCALE) end)
	pcall(function() m:PivotTo(onSpot * CFrame.new(0, -HIDE_DOWN, 0)) end)
	pending = m
	-- the pose: Roblox's own idle for a moment, then frozen where it is
	local an = hum and hum:FindFirstChildOfClass("Animator")
	if an and hum then
		local a = Instance.new("Animation")
		a.AnimationId = if hum.RigType == Enum.HumanoidRigType.R6 then "rbxassetid://180435571" else "rbxassetid://507766388"
		pcall(function() an:LoadAnimation(a):Play(0) end)
	end
	-- the hold: ThirdPerson poses it as a test rig for a moment
	local TP = thirdPerson()
	local held = type(wid) == "string" and TP ~= nil
	if held then
		m:SetAttribute("TP", Vector3.zero)
		m:SetAttribute("TPWeapon", wid)
		m:SetAttribute("TPPlayer", me.UserId)
		if type(skin) == "string" then m:SetAttribute("Skin", skin) end
		if holoItem then m:SetAttribute("TPItemPose", holoItem) end
		CollectionService:AddTag(m, "TPRig")
	end
	holoBusy = true
	task.spawn(function()
		local t0 = os.clock()
		-- (until its gun is in its hands and the draw is done: at least 0.6 s, at most 3)
		while held and os.clock() - t0 < 3 do
			task.wait()
			if pending ~= m or not m.Parent then holoBusy = false; return end
			local r = TP.rigFor(m)
			if os.clock() - t0 > 0.6 and r and r.gun and r.clip == nil and r.kat == nil and (holoItem == nil or (r.item and r.item.model)) then break end
		end
		if not held then task.wait(0.35) end
		holoBusy = false
		if pending ~= m or not m.Parent then return end
		-- frozen where it is: the body anchored, ThirdPerson's gun (and item) copied in as still parts, then let go
		for _, d in m:GetDescendants() do if d:IsA("BasePart") then d.Anchored = true end end
		if held then
			local r = TP.rigFor(m)
			for _, src in { r and r.gun, r and r.item and r.item.model } do
				if src and src.Parent then
					local was2 = src.Archivable
					src.Archivable = true
					local okC, g = pcall(function() return src:Clone() end)
					src.Archivable = was2
					if okC and g then
						for _, d in g:GetDescendants() do
							if d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.CastShadow = false
							elseif d:IsA("JointInstance") or d:IsA("WeldConstraint") then d:Destroy() end
						end
						g.Name = if src == (r and r.gun) then "HoloGun" else "HoloItem"
						g.Parent = m
					end
				end
			end
			CollectionService:RemoveTag(m, "TPRig")
			for _, a in { "TPWeapon", "TPItemPose", "TP" } do m:SetAttribute(a, nil) end
			for _, d in m:GetChildren() do if d.Name == "TPGun" or d.Name == "TPItem" then d:Destroy() end end
		end
		for _, d in m:GetDescendants() do
			if d:IsA("JointInstance") or d:IsA("WeldConstraint") or d:IsA("Humanoid") or d:IsA("AnimationController") then d:Destroy() end
		end
		-- the swap, in one frame (no yield from here): up onto the spot, the hologram's look on and every piece see-through
		-- until the sweep's first paint, the old statue gone
		pending = nil
		pcall(function() m:PivotTo(onSpot) end)
		if Holo then
			pcall(function()
				local h = Holo.apply(m, { build = 1.5, lines = false, glitch = false, flicker = 0, see = 0.84 }) -- (see 0.84: with no scanlines the neon body bloomed white)
				for _, sv in (h and h.parts) or {} do sv.p.Transparency = 1 end
			end)
		end
		local old = holo
		holo = m
		if old ~= m then dropOne(old) end
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
	-- your utility: a use (or a throw) on your own body shows on the statue for ITEM_SHOW seconds
	local TP = thirdPerson()
	local r = TP and TP.rigFor(ch)
	local it = r and r.item
	if it and it ~= itemSeen then
		itemSeen = it
		local u = TP.T.use[it.id]
		holoItem = if it.kind == "throw" then ("%s:throw:0.14"):format(it.id) elseif u then ("%s:use:%.2f"):format(it.id, u.dur * 0.5) else nil
		if holoItem then itemUntil = os.clock() + ITEM_SHOW; holoFor = nil end
	elseif holoItem and os.clock() > itemUntil then
		holoItem = nil; holoFor = nil
	end
	if not holo or not holo.Parent or holoFor ~= ch or ch:FindFirstChild("HeldWeapon") ~= holoHeld then buildHolo(ch, spot) end
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

-- ---------------------------------------------------------------- the gun shop's keeper: his idles and wave
-- Idle is one clip id or several, comma-separated: the first is his idle; at each loop's end, after the first, he goes
-- on to one of the others now and then (SOMETIMES), and from any other back to the first. every clip has two tracks,
-- so one can fade in while the other fades out
local SOMETIMES = 0.35
-- his gaze: rest = how far his eyes go down while nobody is near; bias = down on top of the clip always (the mocap
-- holds his head a little high); range = studs in front of him; yaw / pitch = the most he turns; speed = how fast he
-- eases there (1/s); hold = s someone else must be nearest before he turns to them; neck / waist = their shares
local GAZE = { rest = math.rad(-10), bias = math.rad(-8), range = 16, yaw = math.rad(60), pitch = math.rad(25), speed = 5, hold = 0.6,
	neck = Vector2.new(0.7, 0.75), waist = Vector2.new(0.3, 0.25) }
type Joint = { set: (CFrame) -> (), c0: CFrame }
local function jointOf(m: Model, part: string, name: string): Joint?
	local p = m:FindFirstChild(part)
	local j = p and p:FindFirstChild(name)
	if j and j:IsA("Motor6D") then
		local m6 = j
		return { set = function(cf: CFrame) m6.C0 = cf end, c0 = m6.C0 }
	elseif j and j:IsA("AnimationConstraint") and j.Attachment0 then
		local at = j.Attachment0 :: Attachment
		return { set = function(cf: CFrame) at.CFrame = cf end, c0 = at.CFrame }
	end
	return nil
end
type Keeper = { m: Model, clips: { { AnimationTrack } }, ci: number, other: number, cur: AnimationTrack?, wave: AnimationTrack?, waveAt: number,
	neck: Joint?, waist: Joint?, head: BasePart?, root: BasePart?, gy: number, gp: number, target: Player?, cand: Player?, candSince: number }
local keeper: Keeper? = nil
local function keeperOf(m: Instance): Keeper?
	if not m:IsA("Model") then return nil end
	local hum = m:FindFirstChildOfClass("Humanoid")
	local an = hum and hum:FindFirstChildOfClass("Animator")
	local ids = m:GetAttribute("Idle")
	if not an or type(ids) ~= "string" or ids == "" then return nil end -- (not ready yet: the next look tries again)
	local clips = {}
	for id in string.gmatch(ids, "[^,%s]+") do
		local a = Instance.new("Animation"); a.AnimationId = id
		local ok1, t1 = pcall(function() return an:LoadAnimation(a) end)
		local ok2, t2 = pcall(function() return an:LoadAnimation(a) end)
		if ok1 and ok2 and t1 and t2 then
			for _, t in { t1, t2 } do t.Looped = false; t.Priority = Enum.AnimationPriority.Idle end
			table.insert(clips, { t1, t2 })
		end
	end
	if #clips == 0 then return nil end
	local wave: AnimationTrack? = nil
	local wid = m:GetAttribute("Wave")
	if type(wid) == "string" and wid ~= "" then
		local w = Instance.new("Animation"); w.AnimationId = wid
		local okW, tw = pcall(function() return an:LoadAnimation(w) end)
		if okW and tw then tw.Looped = false; tw.Priority = Enum.AnimationPriority.Action; wave = tw end
	end
	local at = m:GetAttribute("WaveAt")
	local head, root = m:FindFirstChild("Head"), m:FindFirstChild("HumanoidRootPart")
	return { m = m, clips = clips, ci = 1, other = 0, cur = nil, wave = wave, waveAt = if type(at) == "number" then at else 0,
		neck = jointOf(m, "Head", "Neck"), waist = jointOf(m, "UpperTorso", "Waist"),
		head = if head and head:IsA("BasePart") then head else nil, root = if root and root:IsA("BasePart") then root else nil,
		gy = 0, gp = GAZE.rest, target = nil, cand = nil, candSince = 0 }
end
-- where a player's head is in front of him, if near enough to look at
local function gazeAt(k: Keeper, p: Player?): Vector3?
	local ch = p and p.Character
	local h = ch and ch:FindFirstChild("Head")
	local root = k.root
	if not h or not h:IsA("BasePart") or not root then return nil end
	local rel = root.CFrame:PointToObjectSpace(h.Position)
	if rel.Z > -0.5 or rel.Magnitude > GAZE.range then return nil end
	return h.Position
end
local function gazeStep(k: Keeper, dt: number)
	local neck, head, root = k.neck, k.head, k.root
	if not neck or not head or not root then return end
	local now = os.clock()
	local best, bestD = nil, math.huge
	for _, p in Players:GetPlayers() do
		local at = gazeAt(k, p)
		if at then
			local d = (at - head.Position).Magnitude
			if d < bestD then best, bestD = p, d end
		end
	end
	-- (someone else nearest: he turns to them once that has held for GAZE.hold; the one he looks at gone: at once)
	if best ~= k.target then
		if gazeAt(k, k.target) == nil then k.target = best; k.cand = nil
		elseif best ~= k.cand then k.cand = best; k.candSince = now
		elseif now - k.candSince >= GAZE.hold then k.target = best; k.cand = nil end
	else
		k.cand = nil
	end
	local wy, wp = 0, GAZE.rest
	local at = gazeAt(k, k.target)
	if at then
		local d = root.CFrame:VectorToObjectSpace(at - head.Position)
		local flat = math.sqrt(d.X * d.X + d.Z * d.Z)
		wy = math.clamp(math.atan2(-d.X, -d.Z), -GAZE.yaw, GAZE.yaw)
		wp = math.clamp(math.atan2(d.Y, flat), -GAZE.pitch, GAZE.pitch)
	end
	local a = 1 - math.exp(-GAZE.speed * dt)
	k.gy += (wy - k.gy) * a
	k.gp += (wp - k.gp) * a
	local p = k.gp + GAZE.bias
	neck.set(neck.c0 * CFrame.Angles(p * GAZE.neck.Y, k.gy * GAZE.neck.X, 0))
	if k.waist then k.waist.set(k.waist.c0 * CFrame.Angles(p * GAZE.waist.Y, k.gy * GAZE.waist.X, 0)) end
end
local function keeperStep(dt: number)
	local k = keeper
	if not k then return end
	if not k.m:IsDescendantOf(workspace) then k.cur = nil; return end -- (out of your world: start afresh when he is back)
	gazeStep(k, dt)
	local cur = k.cur
	local playing = false
	for _, c in k.clips do if c[1].IsPlaying or c[2].IsPlaying then playing = true; break end end
	if not cur or not playing then
		for _, c in k.clips do c[1]:Stop(0); c[2]:Stop(0) end
		k.ci = 1; k.cur = k.clips[1][1]; k.clips[1][1]:Play(0.4)
	elseif cur.Length > 0 and cur.Length - cur.TimePosition < 0.75 then
		local nci = 1
		if k.ci == 1 and #k.clips > 1 and math.random() < SOMETIMES then
			k.other = (k.other % (#k.clips - 1)) + 1
			nci = 1 + k.other
		end
		local pair = k.clips[nci]
		local nxt = if pair[1] == cur then pair[2] else pair[1]
		nxt:Play(0.7); cur:Stop(0.7); k.cur = nxt; k.ci = nci
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
	-- shutters: the area's own (its Shutter models) and any tagged "Shutter" anywhere (the hub's side of the gate), one
	-- each by its model; a door that is gone (a rebuild) drops out, a new one is met straight at open or shut for who is
	-- near it now. (a nil area is one ZoneCull has taken out of your world for now: keep what we know, it comes back as
	-- it was)
	local have: { [Instance]: boolean } = {}
	for i = #shutters, 1, -1 do
		local sm = shutters[i].r.m
		if not sm.Parent then table.remove(shutters, i) else have[sm] = true end
	end
	local function addShutter(m: Instance)
		if have[m] then return end
		local c, n = m:GetAttribute("Center"), m:GetAttribute("Near")
		local r = readRoller(m)
		if typeof(c) == "Vector3" and #r.slats > 0 then
			local near = if type(n) == "number" then n else 12
			local up = if anyoneNear(c, near) then 1 else 0
			place(r, up, Vector3.zero)
			table.insert(shutters, { r = r, center = c, near = near, lin = up, goal = up, lastNear = if up == 1 then os.clock() else -math.huge, shown = true })
			have[m] = true
		end
	end
	for _, m in CollectionService:GetTagged("Shutter") do if m:GetAttribute("Shutter") == true then addShutter(m) end end
	-- one-way doors, the same way (tagged OneWayDoor)
	local haveOne: { [Instance]: boolean } = {}
	for i = #oneWays, 1, -1 do
		local om = oneWays[i].m
		if not om.Parent then table.remove(oneWays, i) else haveOne[om] = true end
	end
	for _, m in CollectionService:GetTagged("OneWayDoor") do
		if not haveOne[m] then
			local o = oneWayOf(m)
			if o then table.insert(oneWays, o); haveOne[m] = true end
		end
	end
	-- the gold dummies' doors, the same way (tagged EggDoor)
	local haveEgg: { [Instance]: boolean } = {}
	for i = #eggs, 1, -1 do
		local em = eggs[i].r.m
		if not em.Parent then table.remove(eggs, i) else haveEgg[em] = true end
	end
	for _, m in CollectionService:GetTagged("EggDoor") do
		if not haveEgg[m] then
			local e = eggOf(m)
			if e then table.insert(eggs, e); haveEgg[m] = true end
		end
	end
	if tg and tg ~= seen then
		seen = tg
		pit = nil
		mirrorSpot = nil
		if tg then
			for _, m in tg:GetDescendants() do
				if m:GetAttribute("Shutter") == true then
					addShutter(m)
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
		if me:GetAttribute("LotKey") == true then
			if not dr.m:IsDescendantOf(workspace) then
				keyU, keyShown = nil, nil -- (out of your world: straight up when it is back)
			else
				local k = math.min(1, (keyU or 1) + dt / KEY_UP)
				keyU = k
				local shown = math.max(u, k)
				if shown ~= keyShown then place(dr, shown, Vector3.zero); keyShown = shown end
				passDoor(dr)
			end
			doorMoving = true -- (if the key goes, back to the server's door at once)
		else
			local off, shaking = rattleOff(dr.m, now)
			if moving or shaking or doorMoving then place(dr, u, off) end
			doorMoving = moving or shaking
			keyShown = nil
		end
	end
	do -- the panel over it: your own hunt
		local okP, errP = pcall(lotPanelStep, now)
		if not okP then warn("[TrainingDoors] lot panel: " .. tostring(errP)) end
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
	-- the gold dummies' door
	do
		local mc = me.Character
		local myRoot = mc and mc:FindFirstChild("HumanoidRootPart") :: BasePart?
		for _, e in eggs do
			local okE, errE = pcall(eggStep, e, dt, clock, myRoot)
			if not okE then warn("[TrainingDoors] egg door: " .. tostring(errE)) end
		end
		for _, o in oneWays do
			local okO, errO = pcall(oneWayStep, o, dt, myRoot)
			if not okO then warn("[TrainingDoors] one-way door: " .. tostring(errO)) end
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
	local okM, errM = pcall(mirrorStep, dt) -- (the mirror going wrong never stops the doors)
	if not okM then warn("[TrainingDoors] mirror: " .. tostring(errM)) end
	keeperStep(dt)
end)
scan()
