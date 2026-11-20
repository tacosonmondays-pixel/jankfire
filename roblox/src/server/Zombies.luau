--!strict
-- ZOMBIES (the web game's co-op wave survival, server/zombies.js; the owner, 20 Nov 2026: "lets bring back zombies!!
-- We can used colored dummies for now!!"). A squad of up to 4 on a zombies map (the contract: roblox/docs/ZOMBIES.md).
-- Endless rounds of zombies climb in through the windows of whichever areas are open and walk the nav grid
-- (ZombieNav.luau) to the nearest of the squad. Hits and kills earn credits, spent with E on shutters and wall guns.
-- A downed player is revived by a friend holding E; when everyone's down it's over.
--
-- Zombies are Fighters of kind "zombie": coloured R15 dummies in workspace.Dummies, so every weapon we have hits them
-- (the clients aim at that folder, Combat and WeaponProj check Fight.byModel). Their hits and deaths stay in here
-- (Fight.zombieHurt / zombieDied): no feed, no quests, no finishers. Squad members are Fighters as ever; the mode
-- hooks Fight (allow, holdRespawn, spawnAt, lastStand, quiet), Rules (onArm, onRes: spare rounds) and Matches.zoneOf
-- (Zone "zombies").
--
-- one game per server for now. ServerStorage.JankZombies (Studio) and Zombies.start / Zombies.stop run it
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local PhysicsService = game:GetService("PhysicsService")
local TweenService = game:GetService("TweenService")
local DataStoreService = game:GetService("DataStoreService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local ZM = require(Shared:WaitForChild("ZM"))
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Nav = require(script.Parent:WaitForChild("ZombieNav"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

type Fighter = Rules.Fighter
local Zombies = {}
local W = Weapons.list
local R = ZM.R
local S = Weapons.S
local now = os.clock
local Fight: any = nil
local Matches: any = nil
local ZmR: RemoteEvent? = nil
local STUDIO = RunService:IsStudio()
-- where a zombies map goes while it's played (far from everything else)
local SITE = CFrame.new(0, 600, 24000)
local GROUP = "JFZombies"

export type Member = {
	f: Fighter, p: Player?, name: string, c: number, guns: { string }, melee: string, res: { [string]: number },
	kills: number, heads: number, downs: number, revives: number, earned: number,
	hurtT: number, iframe: number, down: { at: CFrame, untilT: number }?, dead: boolean, reviver: Member?, reviveT: number,
	field: { d: { [number]: number }, t: number, at: Vector3 }?, prompt: ProximityPrompt?,
}
export type Mob = {
	id: number, f: Fighter, m: Model, hum: Humanoid, root: BasePart, kind: number, speed: number,
	ph: string, win: number, t: number, t0: number, dur: number,
	target: Member?, wish: Vector3, close: boolean, swingAt: number, nextSwing: number,
	hits: number, hitAt: { [Member]: number }, seen: number, chk: number, chkPos: Vector3, stuck: number,
	side: number, sideDir: number, lastHs: boolean, walk: AnimationTrack?,
}
type Game = {
	map: ZM.Map, model: Model, nav: Nav.Nav, open: { boolean }, areas: { [string]: boolean },
	n: number, st: string, untilT: number, toSpawn: number, spawnAt: number, win: { [number]: number },
	members: { Member }, byF: { [Fighter]: Member }, mobs: { Mob }, byMob: { [Fighter]: Mob },
	fieldT: number, tick: number, lastT: number, templates: { [number]: Model }, prompts: { Instance }, mobId: number,
	overT: number?, conn: RBXScriptConnection?, id: string, players: { Player },
}
local G: Game? = nil
Zombies.game = function(): Game? return G end
local gameN = 0
-- (play-party's queue, 20 Nov 2026) one game per server: the queue asks before it forms a squad
function Zombies.busy(): boolean return G ~= nil end
-- the zombies maps ready to play: every Model in ServerStorage.ZMMaps with a ZM folder (the test block only while
-- there's nothing else). never in Arena.pool or the duel / MODES rotations: the queue draws from this
function Zombies.maps(): { string }
	local out, test = {}, {}
	local lib = ServerStorage:FindFirstChild("ZMMaps")
	if lib then
		for _, m in lib:GetChildren() do
			if m:IsA("Model") and m:FindFirstChild("ZM") then
				if m.Name == "ZTest" then table.insert(test, m.Name) else table.insert(out, m.Name) end
			end
		end
	end
	table.sort(out)
	return if #out > 0 then out else test
end
-- set by the queue (play-party): called right after stop() has sent everyone home, so the parties go back to their rooms
Zombies.onEnd = nil :: ((string, { Player }) -> ())?

-- ------------------------------------------------------------------ helpers
local function feetOf(r: BasePart): Vector3 return Hitbox.feet(r.Position) end
local function floorOf(p: BasePart): Vector3 return p.Position - Vector3.new(0, p.Size.Y / 2, 0) end
local function flat(v: Vector3): Vector3 return Vector3.new(v.X, 0, v.Z) end
local function say(m: Member, x: { [string]: any })
	local r = ZmR
	if r and m.p and m.p.Parent then r:FireClient(m.p, x) end
end
local function sayAll(x: { [string]: any })
	local g, r = G, ZmR
	if not g or not r then return end
	for _, m in g.members do if m.p and m.p.Parent then r:FireClient(m.p, x) end end
end
-- everything the HUD shows that isn't yours: on the arena folder (everyone in it reads it)
local function publish()
	local g = G
	if not g then return end
	local alive = 0
	for _, z in g.mobs do if z.f.alive then alive += 1 end end
	local a = g.model
	a:SetAttribute("Round", g.n)
	a:SetAttribute("St", g.st)
	a:SetAttribute("Left", g.toSpawn + alive)
	a:SetAttribute("BreakUntil", if g.st == "pre" or g.st == "break" then workspace:GetServerTimeNow() + math.max(0, g.untilT - now()) else nil)
end
local function give(m: Member, d: number, why: string)
	m.c += d
	if d > 0 then m.earned += d end
	if m.p then m.p:SetAttribute("ZmC", m.c) end
	say(m, { k = "c", c = m.c, d = d, why = why })
end
local function pay(m: Member, price: number): boolean
	if m.c < price then say(m, { k = "buy", ok = false, m = "need " .. price }); return false end
	give(m, -price, "buy")
	return true
end
-- the player's spare rounds, for their HUD and their client's reloads (Arsenal reads ZmRes_<weapon>)
local function pushRes(m: Member)
	local p = m.p
	if not p then return end
	for wid, n in m.res do p:SetAttribute("ZmRes_" .. wid, n) end
end
local function inOpenArea(m: Member): boolean
	local g = G
	local r = Fight.root(m.f)
	if not g or not r then return false end
	local a = ZM.areaAt(g.map, feetOf(r))
	return a ~= nil and g.areas[a] == true
end

-- ------------------------------------------------------------------ the kit: your guns, your melee, your spare rounds
local function kitList(m: Member): { string }
	local out = table.clone(m.guns)
	table.insert(out, m.melee)
	return out
end
-- put the kit in your hands (full mags; the spares are the mode's), and tell your client
local function arm(m: Member, hold: string?)
	local f = m.f
	f.forced = kitList(m)
	Rules.arm(f, now())
	if hold and table.find(f.forced :: { string }, hold) then f.held = hold end
	local p = m.p
	if p then
		p:SetAttribute("Loadout", table.concat(f.forced :: { string }, ","))
		p:SetAttribute("ArmT", (tonumber(p:GetAttribute("ArmT")) or 0) + 1)
	end
	pushRes(m)
	if f.alive then Fight.showWeapon(f) end
end
-- a new weapon: a melee replaces your melee; a gun takes a free slot or replaces the gun in your hands
local function grant(m: Member, wid: string)
	local w = W[wid]
	if not w then return end
	if w.slot == "melee" then
		m.melee = wid
	elseif not table.find(m.guns, wid) then
		if #m.guns < R.guns then
			table.insert(m.guns, wid)
		else
			local i = table.find(m.guns, m.f.held) or #m.guns
			m.res[m.guns[i]] = nil
			if m.p then m.p:SetAttribute("ZmRes_" .. m.guns[i], nil) end
			m.guns[i] = wid
		end
	end
	local total = ZM.ammo(wid)
	if total and w.mag then m.res[wid] = math.max(0, total - w.mag) end
	arm(m, wid)
end
local function freshKit(m: Member)
	if m.p then for wid in m.res do m.p:SetAttribute("ZmRes_" .. wid, nil) end end
	m.guns = table.clone(R.startGuns)
	m.melee = R.startMelee
	m.res = {}
	for _, wid in m.guns do
		local total, w = ZM.ammo(wid), W[wid]
		if total and w and w.mag then m.res[wid] = math.max(0, total - w.mag) end
	end
	m.f.forced = kitList(m)
end

-- ------------------------------------------------------------------ the zombies' bodies
local function setupGroup()
	pcall(function() PhysicsService:RegisterCollisionGroup(GROUP) end)
	pcall(function() PhysicsService:CollisionGroupSetCollidable(GROUP, GROUP, false) end)
	pcall(function() PhysicsService:CollisionGroupSetCollidable(GROUP, "JFPlayers", false) end)
	pcall(function() PhysicsService:CollisionGroupSetCollidable(GROUP, "JFShredded", false) end)
end
-- one body per gait (the owner: coloured dummies): head, torso and arms in its colour, the legs darker. no face
local function template(kind: number): Model
	local col = ZM.GAIT_COLOR[kind]
	local legs = Color3.new(col.R * 0.45, col.G * 0.45, col.B * 0.45)
	local ok, m = pcall(function()
		local d = Instance.new("HumanoidDescription")
		d.HeadColor, d.TorsoColor, d.LeftArmColor, d.RightArmColor = col, col, col, col
		d.LeftLegColor, d.RightLegColor = legs, legs
		return Players:CreateHumanoidModelFromDescription(d, Enum.HumanoidRigType.R15)
	end)
	local body: Model = if ok and m then m :: Model else Instance.new("Model")
	body.Name = "Zombie"
	for _, d in body:GetDescendants() do
		if d:IsA("Decal") then d:Destroy()
		elseif d:IsA("BasePart") then d.CollisionGroup = GROUP; d.Material = Enum.Material.SmoothPlastic
		end
	end
	local hum = body:FindFirstChildOfClass("Humanoid")
	if hum then
		hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
		hum.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
		hum.BreakJointsOnDeath = true
		hum.AutoJumpEnabled = false
		hum:SetStateEnabled(Enum.HumanoidStateType.Climbing, false)
		hum:SetStateEnabled(Enum.HumanoidStateType.Swimming, false)
	end
	local hs = body:FindFirstChild("Health")
	if hs then hs:Destroy() end
	body:SetAttribute("Zombie", kind)
	return body
end
-- the walk: Roblox's own zombie walk (an animation cycle, never hand-posed). Zombies.WALK can be swapped in a test
Zombies.WALK = "rbxassetid://616168032"
local walkAnim: Animation? = nil
local function walkTrack(hum: Humanoid): AnimationTrack?
	local an = hum:FindFirstChildOfClass("Animator")
	if not an then an = Instance.new("Animator"); (an :: Animator).Parent = hum end
	if not walkAnim or walkAnim.AnimationId ~= Zombies.WALK then
		local a = Instance.new("Animation")
		a.AnimationId = Zombies.WALK
		walkAnim = a
	end
	local ok, tr = pcall(function() return (an :: Animator):LoadAnimation(walkAnim :: Animation) end)
	if not ok or not tr then return nil end
	tr.Looped = true
	tr.Priority = Enum.AnimationPriority.Movement
	return tr
end

local function dummies(): Folder
	local f = workspace:FindFirstChild("Dummies")
	if not f then f = Instance.new("Folder"); f.Name = "Dummies"; f.Parent = workspace end
	return f :: Folder
end

-- ------------------------------------------------------------------ spawning one through a window
local function pickWindow(g: Game, live: { Member }): number?
	local wins = {}
	for i, w in g.map.windows do if g.areas[w.area] then table.insert(wins, i) end end
	if #wins == 0 or #live == 0 then return nil end
	local function near(i: number): number
		local best = math.huge
		for _, m in live do
			local r = Fight.root(m.f)
			if r then best = math.min(best, (g.map.windows[i].inn - r.Position).Magnitude) end
		end
		return best
	end
	table.sort(wins, function(a, b) return near(a) < near(b) end)
	return wins[math.random(1, math.min(3, #wins))]
end
local function spawnOne(g: Game, live: { Member }): boolean
	local wi = pickWindow(g, live)
	if not wi then return false end
	local w = g.map.windows[wi]
	local speed, kind = ZM.gait(g.n, math.random(), math.random())
	local tpl = g.templates[kind]
	if not tpl then return false end
	local m = tpl:Clone()
	local hum = m:FindFirstChildOfClass("Humanoid")
	local root = m:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not hum or not root then m:Destroy(); return false end
	local side = w.n:Cross(Vector3.yAxis)
	local feet = w.out + side * ((math.random() - 0.5) * 6.6) - w.n * (math.random() * 2.4)
	local at = feet + Vector3.new(0, Hitbox.ROOT_UP, 0)
	root.Anchored = true
	m:PivotTo(CFrame.lookAt(at, at + w.n))
	g.mobId += 1
	local f = Rules.newFighter("zombie", ZM.GAIT_NAME[kind], m)
	f.maxHp = ZM.hp(g.n)
	f.forced = { "claw" }
	Rules.spawn(f, now())
	hum.MaxHealth, hum.Health = f.maxHp :: number, f.maxHp :: number
	hum.WalkSpeed = speed
	m.Parent = dummies()
	Fight.byModel[m] = f
	table.insert(Fight.all, f)
	local z: Mob = {
		id = g.mobId, f = f, m = m, hum = hum, root = root, kind = kind, speed = speed,
		ph = "wait", win = wi, t = now() + 0.3 + math.random() * 1.5, t0 = 0, dur = 0,
		target = nil, wish = Vector3.zero, close = false, swingAt = 0, nextSwing = 0,
		hits = 0, hitAt = {}, seen = now(), chk = now(), chkPos = at, stuck = 0, side = 0, sideDir = 1, lastHs = false,
		walk = walkTrack(hum),
	}
	table.insert(g.mobs, z)
	g.byMob[f] = z
	g.toSpawn -= 1
	return true
end
local function removeMob(g: Game, z: Mob, keep: boolean?)
	local i = table.find(g.mobs, z)
	if i then table.remove(g.mobs, i) end
	g.byMob[z.f] = nil
	local fi = table.find(Fight.all, z.f)
	if fi then table.remove(Fight.all, fi) end
	Fight.byModel[z.m] = nil
	z.f.alive = false
	if keep then
		task.delay(2.5, function() if z.m.Parent then z.m:Destroy() end end) -- (the pieces lie there a moment)
	else
		z.m:Destroy()
	end
end

-- ------------------------------------------------------------------ one zombie, one tick
local function headY(_z: Mob): number return 4.6 end
local function clearLine(g: Game, a: Vector3, b: Vector3): boolean
	local d = flat(b - a)
	for _, up in { 1.4, 3.9 } do
		if workspace:Raycast(a + Vector3.new(0, up, 0), d, g.nav.params) then return false end
	end
	return true
end
local function think(g: Game, z: Mob)
	local pos = feetOf(z.root)
	local best, bd, bf = nil :: Member?, math.huge, nil :: { [number]: number }?
	for _, m in g.members do
		if not m.f.alive then continue end
		local r = Fight.root(m.f)
		if not r then continue end
		local fl = m.field
		local d = if fl then Nav.dist(g.nav, g.open, fl.d, pos) else math.huge
		local reach = d < math.huge
		if not reach then d = 3000 + (r.Position - z.root.Position).Magnitude end
		if d < bd then bd = d; best = m; bf = if reach and fl then fl.d else nil end
	end
	z.target = best
	if not best then z.wish = Vector3.zero; z.close = false; return end
	local tr = Fight.root(best.f) :: BasePart
	local tp = feetOf(tr)
	local dv = tp - pos
	local hd = flat(dv).Magnitude
	if hd < 66 then z.seen = now() end
	z.close = hd < 2.55 and math.abs(dv.Y) < 6
	local wish = if hd > 1e-3 then flat(dv) / hd else Vector3.zero
	if not (hd < 27 and math.abs(dv.Y) < 4.2 and clearLine(g, pos, tp)) and bf then
		local p = Nav.downhill(g.nav, g.open, bf, pos)
		if p then
			local e = flat(p - pos)
			if e.Magnitude > 1e-3 then wish = e.Unit end
		end
	end
	if now() < z.side then
		local a = z.sideDir * 1.3
		local ca, sa = math.cos(a), math.sin(a)
		wish = Vector3.new(wish.X * ca - wish.Z * sa, 0, wish.X * sa + wish.Z * ca)
	end
	z.wish = wish
end
local function swipe(g: Game, z: Mob)
	local t = z.target
	local n = now()
	if z.swingAt > 0 then
		if n < z.swingAt then return end
		z.swingAt = 0
		if not t or not t.f.alive then return end
		local tr = Fight.root(t.f)
		if not tr then return end
		local dv = feetOf(tr) - feetOf(z.root)
		local hd = flat(dv).Magnitude
		if hd > R.reachHit or dv.Y < -3.9 or dv.Y > R.reachUp + 0.9 then return end -- dodged
		local from = z.root.Position + Vector3.new(0, 1.5, 0)
		local to = tr.Position
		if hd > 2.7 and workspace:Raycast(from, to - from, g.nav.params) then return end -- not through a wall
		if n < t.iframe then return end
		t.iframe = n + R.iframe
		local dir = if hd > 1e-3 then flat(dv) / hd else z.root.CFrame.LookVector
		Fight.hurt(t.f, ZM.claw(g.n), z.f, "claw", false, dir * 12 + Vector3.new(0, 6, 0), to)
		return
	end
	if not t or not t.f.alive or n < z.nextSwing then return end
	local tr = Fight.root(t.f)
	if not tr then return end
	local dv = feetOf(tr) - feetOf(z.root)
	if flat(dv).Magnitude > R.reach + (if z.kind > 0 then 0.75 else 0) or dv.Y < -3.6 or dv.Y > R.reachUp then return end
	z.swingAt = n + R.windup
	z.nextSwing = n + R.swipeCd
	if dv.Y > 3 then z.hum.Jump = true end
end
local function climb(g: Game, z: Mob)
	local w = g.map.windows[z.win]
	local n = now()
	if z.ph == "wait" then
		if g.st ~= "over" and n >= z.t and (g.win[z.win] or 0) <= n then
			z.ph = "climb"
			z.t0 = n
			z.dur = if z.kind > 0 then R.climbRun else R.climb
			g.win[z.win] = n + z.dur * 0.6
			-- over the sill (a tween on the anchored body: everyone sees it smooth), then down inside
			local mid = w.at.Position - Vector3.new(0, 0.6, 0) + Vector3.new(0, Hitbox.ROOT_UP - 1.5, 0)
			local inAt = w.inn + Vector3.new(0, Hitbox.ROOT_UP, 0)
			local look = w.n
			local t1 = TweenService:Create(z.root, TweenInfo.new(z.dur * 0.5, Enum.EasingStyle.Linear), { CFrame = CFrame.lookAt(mid, mid + look) })
			local t2 = TweenService:Create(z.root, TweenInfo.new(z.dur * 0.5, Enum.EasingStyle.Linear), { CFrame = CFrame.lookAt(inAt, inAt + look) })
			t1.Completed:Once(function() if z.root.Parent then t2:Play() end end)
			t1:Play()
			if z.walk then z.walk:Play(0.2, 1, 0.8) end
		end
		return
	end
	if n >= z.t0 + z.dur + 0.05 then
		z.ph = "hunt"
		z.root.Anchored = false
		pcall(function() z.root:SetNetworkOwner(nil) end)
		z.chk, z.chkPos, z.seen = n, z.root.Position, n
	end
end
local function step(g: Game, z: Mob, dt: number)
	if not z.f.alive then return end
	if z.ph ~= "hunt" then climb(g, z); return end
	local n = now()
	local over = g.st == "over"
	if not over and (g.tick + z.id) % 3 == 0 then think(g, z) end
	local tx = Vector3.zero
	if not over then
		local s = if z.close then 0 else z.speed * (if z.swingAt > 0 then 0.35 else 1)
		tx = z.wish * s
		local me = z.root.Position
		for _, o in g.mobs do -- (don't stack up on each other)
			if o == z or o.ph ~= "hunt" then continue end
			local d = flat(me - o.root.Position)
			local d2 = d.X * d.X + d.Z * d.Z
			if d2 > 7.2 or d2 < 1e-4 or math.abs(me.Y - o.root.Position.Y) > 4.5 then continue end
			local dl = math.sqrt(d2)
			tx += d * ((2.7 - dl) * 7 / dl)
		end
		for _, m in g.members do -- (and don't walk into the people they're clawing at: nobody collides)
			local r = m.f.alive and Fight.root(m.f)
			if not r then continue end
			local d = flat(me - r.Position)
			local d2 = d.X * d.X + d.Z * d.Z
			if d2 > 5.8 or d2 < 1e-4 or math.abs(me.Y - r.Position.Y) > 4.8 then continue end
			local dl = math.sqrt(d2)
			tx += d * ((2.4 - dl) * 10 / dl)
		end
	end
	local sp = tx.Magnitude
	if sp > 0.05 then
		z.hum.WalkSpeed = math.min(sp, z.speed * 1.3)
		z.hum:Move(tx / sp, false)
	else
		z.hum:Move(Vector3.zero, false)
		-- (stood at someone: face them)
		local t = z.target
		local tr = t and t.f.alive and Fight.root(t.f)
		if tr and z.close then
			local d = flat(tr.Position - z.root.Position)
			if d.Magnitude > 0.1 then z.hum:Move(d.Unit * 0.01, false); z.hum.WalkSpeed = 0.5 end
		end
	end
	local wk = z.walk
	if wk then
		local v = flat(z.root.AssemblyLinearVelocity).Magnitude
		if v > 1 then
			if not wk.IsPlaying then wk:Play(0.2) end
			wk:AdjustSpeed(math.clamp(v / 9, 0.6, 2.2))
		elseif wk.IsPlaying then
			wk:Stop(0.3)
		end
	end
	if over then return end
	swipe(g, z)
	if n - z.chk > 1.2 then -- wedged on something: hop and sidestep
		local moved = flat(z.root.Position - z.chkPos).Magnitude
		if not z.close and z.swingAt == 0 and moved < 1.8 then
			z.stuck += 1; z.hum.Jump = true; z.side = n + 0.7; z.sideDir = if math.random() < 0.5 then 1 else -1
		else
			z.stuck = 0
		end
		z.chk, z.chkPos = n, z.root.Position
	end
	if z.root.Position.Y < g.map.bounds.Position.Y - g.map.bounds.Size.Y / 2 - 60 then
		removeMob(g, z); g.toSpawn += 1 -- (fell out of the world: it comes back through a window)
	end
	local _ = dt
end

-- ------------------------------------------------------------------ the squad
local function member(f: Fighter): Member?
	local g = G
	return if g then g.byF[f] else nil
end
Zombies.member = member
local function spawnPoint(g: Game, m: Member): (Vector3, Vector3?)
	local sp = g.map.spawns
	if #sp == 0 then return floorOf(g.map.bounds) + Vector3.new(0, 1, 0), nil end
	local i = (table.find(g.members, m) or 1)
	local cf = sp[((i - 1) % #sp) + 1]
	return cf.Position, cf.LookVector
end
local function respawn(m: Member)
	local f = m.f
	m.down, m.dead, m.reviver = nil, false, nil
	if m.prompt then m.prompt:Destroy(); m.prompt = nil end
	if m.p then m.p:SetAttribute("ZmDown", nil); m.p:SetAttribute("ZmOut", nil) end
	f.alive = false
	f.forced = kitList(m)
	task.spawn(function() Fight.spawn(f) end)
end
-- back up where you went down (a revive), with your kit
local function standUp(m: Member, by: Member?)
	local f = m.f
	local down = m.down
	m.down, m.reviver = nil, nil
	if m.prompt then m.prompt:Destroy(); m.prompt = nil end
	local r = Fight.root(f)
	if r then
		r.Anchored = false
		if down then r.CFrame = down.at end
	end
	f.alive, f.hp, f.spawnT = true, f.maxHp or Weapons.HP, now()
	m.hurtT = 0
	Fight.syncHp(f)
	local p = m.p
	if p then
		p:SetAttribute("ZmDown", nil)
		p:SetAttribute("TeleportT", os.clock())
		p:SetAttribute("ACGrace", os.clock() + 2)
	end
	Fight.showWeapon(f)
	if by then by.revives += 1 end
	sayAll({ k = "down", who = m.name, st = "up", by = if by then by.name else nil })
end
local function bleedOut(m: Member)
	m.down, m.reviver = nil, nil
	m.dead = true
	if m.prompt then m.prompt:Destroy(); m.prompt = nil end
	local hum = Fight.hum(m.f)
	local r = Fight.root(m.f)
	if r then r.Anchored = false end
	if hum then hum.Health = 0 end -- (f.alive is already false: Fight's Died hook leaves it)
	if m.p then m.p:SetAttribute("ZmDown", nil); m.p:SetAttribute("ZmOut", true) end
	sayAll({ k = "down", who = m.name, st = "out" })
end
-- the killing hit: down (a friend can revive you for R.bleed s) or, with nobody else up, out
local function goDown(t: Fighter, _amt: number, _by: Fighter?, _wid: string): boolean
	local g = G
	local m = g and g.byF[t]
	if not g or not m then return false end
	m.downs += 1
	t.alive = false
	t.hp = 1 -- (the body stays up: HP shows 0, the HUD's down screen takes over)
	local p = m.p
	if p then p:SetAttribute("Hp", 0) end
	local anyUp = false
	for _, o in g.members do if o ~= m and o.f.alive then anyUp = true end end
	local r = Fight.root(t)
	if g.st == "over" or not anyUp or not r then
		bleedOut(m)
		return true
	end
	-- on the floor where you fell
	local feet = feetOf(r)
	local look = flat(r.CFrame.LookVector)
	look = if look.Magnitude > 1e-3 then look.Unit else Vector3.zAxis
	local lie = CFrame.lookAt(feet + Vector3.new(0, 1.1, 0), feet + Vector3.new(0, 1.1, 0) + look) * CFrame.Angles(math.rad(-80), 0, 0)
	r.Anchored = true
	r.CFrame = lie
	m.down = { at = CFrame.lookAt(feet + Vector3.new(0, Hitbox.ROOT_UP, 0), feet + Vector3.new(0, Hitbox.ROOT_UP, 0) + look), untilT = now() + R.bleed }
	if p then
		p:SetAttribute("ZmDown", workspace:GetServerTimeNow() + R.bleed)
		p:SetAttribute("ACGrace", os.clock() + R.bleed + 5)
	end
	-- the revive: hold E over them
	local pr = Instance.new("ProximityPrompt")
	pr.Name = "ZmRevive"
	pr.ActionText = "Revive"
	pr.ObjectText = m.name
	pr.KeyboardKeyCode = Enum.KeyCode.E
	pr.HoldDuration = R.revive
	pr.MaxActivationDistance = 9
	pr.RequiresLineOfSight = false
	pr:SetAttribute("Downed", if p then p.UserId else 0)
	pr.Parent = r
	m.prompt = pr
	pr.PromptButtonHoldBegan:Connect(function(pl: Player)
		local rv = Fight.byPlayer[pl] and g.byF[Fight.byPlayer[pl]]
		if rv and rv ~= m and rv.f.alive then m.reviver = rv; m.reviveT = now() end
	end)
	pr.PromptButtonHoldEnded:Connect(function(pl: Player)
		local rv = Fight.byPlayer[pl] and g.byF[Fight.byPlayer[pl]]
		if rv and m.reviver == rv then m.reviver = nil end
	end)
	pr.Triggered:Connect(function(pl: Player)
		local rv = Fight.byPlayer[pl] and g.byF[Fight.byPlayer[pl]]
		if G ~= g or not rv or rv == m or not rv.f.alive or not m.down then return end
		standUp(m, rv)
	end)
	sayAll({ k = "down", who = m.name, st = "down" })
	return true
end

-- ------------------------------------------------------------------ doors and wall guns (E)
local function openDoor(g: Game, i: number, by: Member?)
	if g.open[i] then return end
	g.open[i] = true
	g.areas = ZM.openAreas(g.map, g.open)
	g.fieldT = now()
	local d = g.map.doors[i]
	local sh = d.shutter
	sh.CanCollide = false
	sh.CanQuery = false
	local pr = sh:FindFirstChildOfClass("ProximityPrompt")
	if pr then pr:Destroy() end
	-- it rolls up into its housing
	TweenService:Create(sh, TweenInfo.new(0.9, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
		CFrame = sh.CFrame + Vector3.new(0, sh.Size.Y * 0.95, 0), Transparency = 1,
	}):Play()
	sayAll({ k = "door", i = i, by = if by then by.name else nil, label = d.label })
end
local function prompt(parent: BasePart, action: string, object: string, hold: number): ProximityPrompt
	local pr = Instance.new("ProximityPrompt")
	pr.ActionText = action
	pr.ObjectText = object
	pr.KeyboardKeyCode = Enum.KeyCode.E
	pr.HoldDuration = hold
	pr.MaxActivationDistance = 9
	pr.RequiresLineOfSight = false
	pr.Parent = parent
	return pr
end
local function buyerOf(g: Game, pl: Player): Member?
	local f = Fight.byPlayer[pl]
	local m = f and g.byF[f]
	if not m or not m.f.alive or g.st == "over" then return nil end
	if not inOpenArea(m) then return nil end -- (movement is the client's: walking through a shutter buys nothing)
	return m
end
local function wirePrompts(g: Game)
	for i, d in g.map.doors do
		local pr = prompt(d.shutter, "Open  " .. d.price, d.label, R.hold)
		pr.Name = "ZmDoor"
		table.insert(g.prompts, pr)
		pr.Triggered:Connect(function(pl: Player)
			local m = buyerOf(g, pl)
			if not m or g.open[i] then return end
			if pay(m, d.price) then openDoor(g, i, m) end
		end)
	end
	for _, b in g.map.buys do
		local w = W[b.w]
		local refill = ZM.ammoPrice(b.price)
		local pr = prompt(b.part, "Buy  " .. b.price, (w.name or b.w) .. if ZM.ammo(b.w) then "   (ammo " .. refill .. ")" else "", R.hold)
		pr.Name = "ZmBuy"
		table.insert(g.prompts, pr)
		pr.Triggered:Connect(function(pl: Player)
			local m = buyerOf(g, pl)
			if not m then return end
			if b.w == m.melee or table.find(m.guns, b.w) then -- already yours: a refill
				local total = ZM.ammo(b.w)
				if not total or not w.mag then say(m, { k = "buy", ok = false, m = "you already have it" }); return end
				local full = math.max(0, total - (w.mag :: number))
				if (m.res[b.w] or 0) >= full then say(m, { k = "buy", ok = false, m = "ammo full" }); return end
				if not pay(m, refill) then return end
				m.res[b.w] = full
				local a = m.f.ammo[b.w]
				if a then a.res = full end
				pushRes(m)
				say(m, { k = "buy", ok = true, m = (w.name or b.w) .. " ammo" })
				return
			end
			if pay(m, b.price) then grant(m, b.w); say(m, { k = "buy", ok = true, m = w.name or b.w }) end
		end)
	end
end

-- ------------------------------------------------------------------ the round loop
local function fields(g: Game)
	local n = now()
	for _, m in g.members do
		if not m.f.alive then continue end
		local r = Fight.root(m.f)
		if not r then continue end
		local at = feetOf(r)
		local fl = m.field
		if not fl then fl = { d = {}, t = -math.huge, at = Vector3.new(1e9, 0, 0) }; m.field = fl end
		local fd = fl :: { d: { [number]: number }, t: number, at: Vector3 }
		local moved = flat(at - fd.at).Magnitude + (if g.nav.L > 1 then math.abs(at.Y - fd.at.Y) else 0)
		if fd.t > g.fieldT and n - fd.t < 1.5 and (n - fd.t < 0.3 or moved < 2.25) then continue end
		Nav.flow(g.nav, g.open, at, fd.d)
		fd.t, fd.at = n, at
	end
end
local function squadTick(g: Game, dt: number)
	local n = now()
	for _, m in g.members do
		local f = m.f
		if f.alive then
			if f.hp < (f.maxHp or Weapons.HP) and n - m.hurtT > R.regenAfter then
				f.hp = math.min(f.maxHp or Weapons.HP, f.hp + R.regen * dt)
				Fight.syncHp(f)
			end
			continue
		end
		local d = m.down
		if not d then continue end
		if m.reviver and m.reviver.f.alive then d.untilT += dt -- (paused while someone's reviving you)
		elseif n >= d.untilT then bleedOut(m) end
	end
end
local function saveBest(g: Game)
	if not ServerStorage:FindFirstChild("ZMNoSave") then
		local ok, ds = pcall(function() return DataStoreService:GetDataStore(if STUDIO then "JankZombies_v1_studio" else "JankZombies_v1") end)
		if not ok or not ds then return end
		for _, m in g.members do
			local p = m.p
			if not p then continue end
			task.spawn(function()
				pcall(function()
					(ds :: DataStore):UpdateAsync("u" .. p.UserId, function(old: any)
						local t = if type(old) == "table" then old else {}
						t.best = math.max(tonumber(t.best) or 0, g.n)
						t.kills = (tonumber(t.kills) or 0) + m.kills
						t.games = (tonumber(t.games) or 0) + 1
						return t
					end)
				end)
			end)
			p:SetAttribute("ZmBest", math.max(tonumber(p:GetAttribute("ZmBest")) or 0, g.n))
		end
	end
end
local function gameOver(g: Game)
	g.st = "over"
	g.overT = now()
	local rows = {}
	for _, m in g.members do
		table.insert(rows, { m.name, m.kills, m.heads, m.downs, m.revives, m.earned })
	end
	table.sort(rows, function(a, b) return a[2] > b[2] end)
	sayAll({ k = "over", n = g.n, rows = rows })
	saveBest(g)
	publish()
end
local function nextRound(g: Game)
	g.n += 1
	g.st = "live"
	g.toSpawn = ZM.count(g.n, #g.members)
	g.spawnAt = now() + 1.5
	for _, m in g.members do if not m.f.alive then if m.dead or not m.down then freshKit(m) end; respawn(m) end end
	sayAll({ k = "round", st = "start", n = g.n })
	publish()
end
local function cleared(g: Game)
	g.st = "break"
	g.untilT = now() + R.rest
	sayAll({ k = "round", st = "clear", n = g.n })
	publish()
end
local function tick(g: Game, dt: number)
	g.tick += 1
	for _, z in table.clone(g.mobs) do
		if z.ph == "hunt" and z.f.alive and (now() - z.seen > 25 or z.stuck > 8) then removeMob(g, z); g.toSpawn += 1 end -- lost or wedged: again from a window
	end
	if g.st == "over" then
		for _, z in g.mobs do step(g, z, dt) end
		if g.overT and now() - g.overT > 12 then Zombies.stop("over") end
		return
	end
	fields(g)
	squadTick(g, dt)
	-- over when nobody's up: everyone down or out (someone on their way back in, a respawn loading, still counts as up)
	local anyUp = false
	for _, m in g.members do
		if m.f.alive or (not m.down and not m.dead) then anyUp = true end
	end
	if #g.members > 0 and not anyUp then
		for _, m in g.members do if m.down then bleedOut(m) end end -- (a downed player with nobody up: out at once)
		gameOver(g)
		return
	end
	for _, z in g.mobs do step(g, z, dt) end
	if g.st ~= "live" then
		if now() >= g.untilT then nextRound(g) end
		if g.tick % 5 == 0 then publish() end
		return
	end
	local alive = 0
	for _, z in g.mobs do if z.f.alive then alive += 1 end end
	if g.toSpawn > 0 and alive < ZM.maxAlive(#g.members) and now() >= g.spawnAt then
		local live = {}
		for _, m in g.members do if m.f.alive then table.insert(live, m) end end
		g.spawnAt = now() + (if spawnOne(g, live) then ZM.gap(g.n, #g.members) else 0.5)
	end
	if g.toSpawn <= 0 and alive == 0 then cleared(g) end
	if g.tick % 5 == 0 then publish() end
end

-- ------------------------------------------------------------------ the Fight hooks
local hooked = false
local function hook()
	if hooked then return end
	hooked = true
	setupGroup()
	local prevAllow = Fight.allow
	Fight.allow = function(by: Fighter?, t: Fighter): boolean
		local g = G
		if g then
			local tz, bz = t.kind == "zombie", by ~= nil and by.kind == "zombie"
			if tz or bz then
				if tz and bz then return false end -- (zombies don't hurt zombies)
				local other = if tz then by else t
				return other == nil or g.byF[other :: Fighter] ~= nil
			end
			local a, b = by and g.byF[by], g.byF[t]
			if a and b then return by == t end -- (no friendly fire; your own blast still shoves you)
			if a or b then return false end
		end
		return prevAllow(by, t)
	end
	local prevHold = Fight.holdRespawn
	Fight.holdRespawn = function(f: Fighter): boolean
		if member(f) then return true end -- (the dead come back with the next round)
		return prevHold(f)
	end
	local prevAt = Fight.spawnAt
	Fight.spawnAt = function(f: Fighter): (Vector3, Vector3?)
		local g = G
		local m = member(f)
		if g and m then return spawnPoint(g, m) end
		if prevAt then return prevAt(f) end
		return Fight.pickSpawn(f), nil
	end
	local prevMod = Fight.modDamage
	Fight.modDamage = function(t: Fighter, amt: number, by: Fighter?, wid: string): number
		if prevMod then amt = prevMod(t, amt, by, wid) end
		local m = member(t)
		if m then m.hurtT = now() end
		return amt
	end
	Fight.lastStand = goDown
	Fight.quiet = function(f: Fighter): boolean return member(f) ~= nil end
	Fight.zombieHurt = function(t: Fighter, _done: number, by: Fighter?, _wid: string, hs: boolean?)
		local g = G
		local z = g and g.byMob[t]
		local m = by and member(by)
		if not g or not z then return end
		z.lastHs = hs == true
		if m and z.hits < R.hitCap and now() - (z.hitAt[m] or -math.huge) >= R.hitGap then
			z.hitAt[m] = now(); z.hits += 1
			give(m, R.hit, "hit")
		end
	end
	Fight.zombieDied = function(info: any)
		local g = G
		local z = g and g.byMob[info.v]
		if not g or not z then return end
		local k = info.k and member(info.k)
		if k then
			local w = W[info.w]
			local melee = (w and w.kind == "melee") or info.w == "slipper"
			local head = z.lastHs and not melee
			give(k, if melee or head then R.bonus else R.kill, if melee then "melee" elseif head then "head" else "kill")
			k.kills += 1
			if head then k.heads += 1 end
		end
		removeMob(g, z, true)
	end
	Rules.onArm = function(f: any)
		local m = member(f)
		if not m then return end
		for wid, n in m.res do
			local a = f.ammo[wid]
			if a then a.res = n end
		end
		pushRes(m)
	end
	Rules.onRes = function(f: any, wid: string)
		local m = member(f)
		local a = f.ammo[wid]
		if m and a and a.res then m.res[wid] = a.res; pushRes(m) end
	end
	if Matches then
		Matches.zoneHook = function(p: Player): string?
			local f = Fight.byPlayer[p]
			return if f and member(f) then "zombies" else nil
		end
	end
end

-- ------------------------------------------------------------------ start / stop
-- start a game: (the game's id, a line about the map) or (nil, why). players: the real ones (1 to 4); the squad's bots
-- fill the empty slots. opts.queue: which queue it came from (kept for the results)
function Zombies.start(players: { Player }, mapName: string, _opts: { queue: string }?): (string?, string?)
	if G then return nil, "busy" end
	hook()
	local lib = ServerStorage:FindFirstChild("ZMMaps")
	local tpl = lib and lib:FindFirstChild(mapName)
	if not tpl or not tpl:IsA("Model") then return nil, "no map " .. mapName .. " in ServerStorage.ZMMaps" end
	local model = tpl:Clone()
	model:PivotTo(SITE)
	model.Parent = workspace
	local map, why = ZM.read(model)
	if not map then model:Destroy(); return nil, why end
	local shutters = {}
	for _, d in map.doors do table.insert(shutters, d.shutter) end
	local skip: { Instance } = { dummies() }
	for _, p in Players:GetPlayers() do if p.Character then table.insert(skip, p.Character) end end
	local nav = Nav.build(map.bounds, shutters, skip)
	local g: Game = {
		map = map, model = model, nav = nav, open = {}, areas = {}, n = 0, st = "pre", untilT = now() + R.first,
		toSpawn = 0, spawnAt = 0, win = {}, members = {}, byF = {}, mobs = {}, byMob = {}, fieldT = now(), tick = 0, lastT = now(),
		templates = {}, prompts = {}, mobId = 0, overT = nil, conn = nil, id = "", players = {},
	}
	gameN += 1
	g.id = "zm:" .. gameN
	for i = 1, #map.doors do g.open[i] = false end
	g.areas = ZM.openAreas(map, g.open)
	for k = 0, 2 do g.templates[k] = template(k) end
	G = g
	for _, p in players do
		local f = Fight.byPlayer[p]
		if not f then continue end
		local m: Member = {
			f = f, p = p, name = p.DisplayName, c = R.start, guns = {}, melee = R.startMelee, res = {},
			kills = 0, heads = 0, downs = 0, revives = 0, earned = 0, hurtT = 0, iframe = 0, down = nil, dead = false,
			reviver = nil, reviveT = 0, field = nil, prompt = nil,
		}
		freshKit(m)
		table.insert(g.members, m)
		g.byF[f] = m
		table.insert(g.players, p)
		p:SetAttribute("ZmOn", true)
		p:SetAttribute("ZmC", m.c)
		p:SetAttribute("ZmArena", model.Name)
		respawn(m)
	end
	wirePrompts(g)
	model:SetAttribute("Label", map.label)
	publish()
	local acc = 0
	g.conn = RunService.Heartbeat:Connect(function(dt: number)
		acc += dt
		if acc < 0.1 then return end
		local step = math.min(acc, 0.25)
		acc = 0
		if G ~= g then return end
		local ok, err = pcall(tick, g, step)
		if not ok then warn("[jankfire] zombies tick: " .. tostring(err)) end
	end)
	return g.id, string.format("zombies on %s: %d areas, %d doors, %d windows, %d wall buys; nav %dx%d x%d floors, %d cells in %.2f s",
		map.label, (function() local c = 0; for _ in map.areas do c += 1 end; return c end)(), #map.doors, #map.windows, #map.buys,
		nav.W, nav.D, nav.L, nav.cells, nav.built)
end

function Zombies.stop(_why: string?)
	local g = G
	if not g then return end
	G = nil
	if g.conn then g.conn:Disconnect() end
	for _, z in table.clone(g.mobs) do removeMob(g, z) end
	for _, m in g.members do
		local f, p = m.f, m.p
		if m.prompt then m.prompt:Destroy() end
		f.forced = nil
		local r = Fight.root(f)
		if r then r.Anchored = false end
		if p and p.Parent then
			p:SetAttribute("ZmOn", nil); p:SetAttribute("ZmC", nil); p:SetAttribute("ZmDown", nil); p:SetAttribute("ZmOut", nil)
			p:SetAttribute("ZmArena", nil)
			for wid in m.res do p:SetAttribute("ZmRes_" .. wid, nil) end
			p:SetAttribute("TeleportT", os.clock())
			f.alive = false
			task.spawn(function() Fight.spawn(f) end) -- (back to the hub with your own loadout)
		end
	end
	for _, t in g.templates do t:Destroy() end
	g.model:Destroy()
	local home = {}
	for _, p in g.players do if p.Parent then table.insert(home, p) end end
	local cb = Zombies.onEnd
	if cb then task.spawn(cb, g.id, home) end
end

-- someone left mid-game
Players.PlayerRemoving:Connect(function(p: Player)
	local g = G
	if not g then return end
	for i, m in g.members do
		if m.p == p then
			if m.prompt then m.prompt:Destroy() end
			g.byF[m.f] = nil
			table.remove(g.members, i)
			break
		end
	end
	if #g.members == 0 then Zombies.stop("empty") end
end)

-- ------------------------------------------------------------------ test knobs (Studio's ServerStorage.JankZombies)
function Zombies.state(): { [string]: any }
	local g = G
	if not g then return { on = false } end
	local mobs = {}
	for _, z in g.mobs do table.insert(mobs, { z.id, z.ph, z.kind, math.floor(z.f.hp), z.f.alive }) end
	local ms = {}
	for _, m in g.members do
		table.insert(ms, { m.name, m.c, m.f.alive, m.down ~= nil, m.dead, table.concat(kitList(m), ","), m.kills })
	end
	return { on = true, n = g.n, st = g.st, toSpawn = g.toSpawn, mobs = mobs, members = ms, open = g.open, cells = g.nav.cells, built = g.nav.built }
end
function Zombies.round(n: number)
	local g = G
	if not g then return end
	for _, z in table.clone(g.mobs) do removeMob(g, z) end
	g.n = math.max(0, n - 1)
	g.st = "break"
	g.untilT = now()
end
function Zombies.credits(p: Player, c: number)
	local g = G
	local f = Fight.byPlayer[p]
	local m = g and f and g.byF[f]
	if m then give(m, c - m.c, "test") end
end
function Zombies.openAll()
	local g = G
	if not g then return end
	for i = 1, #g.map.doors do openDoor(g, i, nil) end
end

function Zombies.init(fight: any, matches: any?)
	Fight = fight
	Matches = matches
	ZmR = Remotes:FindFirstChild("Zm") :: RemoteEvent?
	if not ZmR then
		local r = Instance.new("RemoteEvent")
		r.Name = "Zm"
		r.Parent = Remotes
		ZmR = r
	end
	if STUDIO then
		local hookF = ServerStorage:FindFirstChild("JankZombies") or Instance.new("BindableFunction")
		hookF.Name = "JankZombies"
		hookF.Parent = ServerStorage
		;(hookF :: BindableFunction).OnInvoke = function(op: string, a: any, b: any): any
			if op == "start" then
				local list = if type(a) == "table" then a else Players:GetPlayers()
				return Zombies.start(list, if type(b) == "string" then b else "ZTest")
			elseif op == "stop" then Zombies.stop("test"); return true
			elseif op == "state" then return Zombies.state()
			elseif op == "round" then Zombies.round(tonumber(a) or 1); return true
			elseif op == "credits" then Zombies.credits(a, tonumber(b) or 0); return true
			elseif op == "open" then Zombies.openAll(); return true
			elseif op == "max" then R.maxAlive = tonumber(a); return true
			end
			return "ops: start, stop, state, round, credits, open, max"
		end
	end
end

return Zombies
