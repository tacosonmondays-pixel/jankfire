--!strict
-- ZOMBIES (the web game's co-op wave survival, server/zombies.js; the owner, 20 Nov 2026: "lets bring back zombies!!
-- We can used colored dummies for now!!"). A squad of up to 4 on a zombies map (the contract: roblox/docs/ZOMBIES.md).
-- Endless rounds of zombies climb in through the windows of whichever areas are open and walk the nav grid
-- (ZombieNav.luau) to the nearest of the squad. Hits and kills earn credits, spent with Q on shutters and wall guns (F on the web; F is the flashlight here since 27 Nov 2026, and E the grapple).
-- A downed player is revived by a friend holding F; when everyone's down it's over.
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
	hurtT: number, iframe: number, down: { at: CFrame, untilT: number, self: number? }?, dead: boolean, reviver: Member?, reviveT: number,
	field: { d: { [number]: number }, t: number, at: Vector3 }?, prompt: ProximityPrompt?,
	bot: Bot?, -- (a squad bot: its brain)
}
export type Bot = {
	i: number, gun: string, mag: number, reloadUntil: number, nextShot: number, th: Mob?, td: number, task: Member?,
	revT0: number, think: number, side: number, sideT: number, chk: number, chkPos: Vector3, stuck: number,
	spot: { d: { [number]: number }, t: number, at: Vector3 },
}
export type Mob = {
	id: number, f: Fighter, m: Model, hum: Humanoid, root: BasePart, kind: number, speed: number,
	ph: string, win: number, t: number, t0: number, dur: number,
	target: Member?, wish: Vector3, close: boolean, swingAt: number, nextSwing: number,
	hits: number, hitAt: { [Member]: number }, seen: number, chk: number, chkPos: Vector3, stuck: number,
	side: number, sideDir: number, lastHs: boolean, walk: AnimationTrack?,
	k: number?, -- (its size: ZombieSpecial scales the specials and bosses)
}
type Game = {
	map: ZM.Map, model: Model, nav: Nav.Nav, open: { boolean }, areas: { [string]: boolean },
	n: number, st: string, untilT: number, toSpawn: number, spawnAt: number, win: { [number]: number },
	members: { Member }, byF: { [Fighter]: Member }, mobs: { Mob }, byMob: { [Fighter]: Mob },
	fieldT: number, tick: number, lastT: number, templates: { [number]: Model }, prompts: { Instance }, mobId: number,
	overT: number?, conn: RBXScriptConnection?, id: string, players: { Player },
	cost: { n: number, sum: number, max: number }, -- (ms a tick: the server cost)
}
local G: Game? = nil
Zombies.game = function(): Game? return G end
local gameN = 0
-- (play-party's queue, 20 Nov 2026) one game per server: the queue asks before it forms a squad
local starting = 0 -- (a start still yielding: the map copy, the nav, the bodies, ~1.6 s on the school)
function Zombies.busy(): boolean return G ~= nil or starting > 0 end
-- the zombies maps ready to play: every Model in ServerStorage.ZMMaps with a ZM folder (the test block only while
-- there's nothing else). never in Arena.pool or the duel / MODES rotations: the queue draws from this
local function sources(): { Model }
	local out = {}
	local lib = ServerStorage:FindFirstChild("ZMMaps")
	if lib then for _, m in lib:GetChildren() do if m:IsA("Model") and m:FindFirstChild("ZM") then table.insert(out, m) end end end
	-- (the maps session's: workspace.Map.<name> with ZombiesMap = true, Enabled false, the school since v1155)
	local wm = workspace:FindFirstChild("Map")
	if wm then
		for _, m in wm:GetChildren() do
			if m:IsA("Model") and m:GetAttribute("ZombiesMap") == true and m:FindFirstChild("ZM") then table.insert(out, m) end
		end
	end
	return out
end
local function source(name: string): Model?
	for _, m in sources() do if m.Name == name then return m end end
	-- (a spare named outright, out of the rotation, ZombiesMap off: a test can still play it. maps() never lists it)
	local wm = workspace:FindFirstChild("Map")
	local spare = wm and wm:FindFirstChild(name)
	if spare and spare:IsA("Model") and spare:FindFirstChild("ZM") then return spare end
	return nil
end
function Zombies.maps(): { string }
	local out, test = {}, {}
	for _, m in sources() do
		if m.Name == "ZTest" then table.insert(test, m.Name) else table.insert(out, m.Name) end
	end
	table.sort(out)
	return if #out > 0 then out else test
end
-- set by the queue (play-party): called right after stop() has sent everyone home, so the parties go back to their rooms
Zombies.onEnd = nil :: ((string, { Player }) -> ())?
-- (stage 2 on: ZombieExtra.luau fills these, the web's zx* / zs* hooks: the power, colas, the Voider, the Cheat
-- Machine, drops, boards, the crate). each is optional
Zombies.ext = {} :: { [string]: any }
local function call(name: string, ...: any): any
	local fn = Zombies.ext[name]
	if fn then return fn(...) end
	return nil
end

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
	if d > 0 then
		local k = call("creditMul", G, m)
		if type(k) == "number" then d = math.floor(d * k + 0.5) end
	end
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
-- what a gun holds for you in all (mag + spares): the web's zxMaxAmmo (Deep Pockets, the Voider: ZombieExtra)
local function maxTotal(m: Member, wid: string): number?
	local total = ZM.ammo(wid)
	if not total then return nil end
	local k = call("ammoMul", G, m, wid)
	return math.floor(total * (if type(k) == "number" then k else 1) + 0.5)
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
	if p and hold then
		local eq = Remotes:FindFirstChild("Equip")
		task.delay(0.3, function()
			if p.Parent and f.forced and table.find(f.forced :: { string }, hold) and eq and eq:IsA("RemoteEvent") then eq:FireClient(p, hold) end
		end)
	end
end
-- a new weapon: a melee replaces your melee; a gun takes a free slot or replaces the gun in your hands
local function grant(m: Member, wid: string)
	local w = W[wid]
	if not w then return end
	if w.slot == "melee" then
		m.melee = wid
	elseif not table.find(m.guns, wid) then
		if #m.guns < (call("guns", G, m) or R.guns) then
			table.insert(m.guns, wid)
		else
			local i = table.find(m.guns, m.f.held) or #m.guns
			m.res[m.guns[i]] = nil
			if m.p then m.p:SetAttribute("ZmRes_" .. m.guns[i], nil) end
			call("dropGun", G, m, m.guns[i]) -- (its warranty goes with it)
			m.guns[i] = wid
		end
	end
	local total = maxTotal(m, wid)
	if total and w.mag then m.res[wid] = math.max(0, total - w.mag) end
	arm(m, wid)
end
local function freshKit(m: Member)
	call("fresh", G, m) -- (back to the start pistol: the Voider's work goes too)
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
Zombies.BOT_WALK = "rbxassetid://507777826" -- (the squad's bots: Roblox's plain R15 walk)
local anims: { [string]: Animation } = {}
local function walkTrack(hum: Humanoid, id: string?): AnimationTrack?
	local an = hum:FindFirstChildOfClass("Animator")
	if not an then an = Instance.new("Animator"); (an :: Animator).Parent = hum end
	local aid = id or Zombies.WALK
	local anim = anims[aid]
	if not anim then
		anim = Instance.new("Animation")
		anim.AnimationId = aid
		anims[aid] = anim
	end
	local ok, tr = pcall(function() return (an :: Animator):LoadAnimation(anim :: Animation) end)
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
	local pw = call("packWindow", g)
	local wi = if type(pw) == "number" and g.map.windows[pw] then pw else pickWindow(g, live)
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
	local okS, errS = pcall(call, "spawned", g, z) -- (a special, a boss: ZombieSpecial)
	if not okS then warn("[jankfire] zombies spawned: " .. tostring(errS)) end
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
	local sw = call("steer", g, z)
	if typeof(sw) == "Vector3" then z.wish = sw; z.close = false end
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
		local ru = call("reachUp", g, z)
		if hd > R.reachHit * (z.k or 1) or dv.Y < -3.9 or dv.Y > (if type(ru) == "number" then ru else R.reachUp) + 0.9 then return end -- dodged
		local from = z.root.Position + Vector3.new(0, 1.5, 0)
		local to = tr.Position
		if hd > 2.7 and workspace:Raycast(from, to - from, g.nav.params) then return end -- not through a wall
		if n < t.iframe then return end
		t.iframe = n + R.iframe
		local dir = if hd > 1e-3 then flat(dv) / hd else z.root.CFrame.LookVector
		local cm = call("clawMul", g, t)
		local zc = call("zClaw", g, z)
		Fight.hurt(t.f, ZM.claw(g.n) * (if type(cm) == "number" then cm else 1) * (if type(zc) == "number" then zc else 1), z.f, "claw", false, dir * 12 + Vector3.new(0, 6, 0), to)
		return
	end
	if not t or not t.f.alive or n < z.nextSwing then return end
	local tr = Fight.root(t.f)
	if not tr then return end
	local dv = feetOf(tr) - feetOf(z.root)
	local ru = call("reachUp", g, z)
	local reachUp = if type(ru) == "number" then ru else R.reachUp
	if flat(dv).Magnitude > R.reach * (z.k or 1) + (if z.kind > 0 then 0.75 else 0) or dv.Y < -3.6 or dv.Y > reachUp then return end
	local cd = call("zCd", g, z)
	z.swingAt = n + R.windup
	z.nextSwing = n + R.swipeCd * (if type(cd) == "number" then cd else 1)
	if dv.Y > 3 and call("canJump", g, z) ~= false then z.hum.Jump = true end
end
local function climb(g: Game, z: Mob)
	local w = g.map.windows[z.win]
	local n = now()
	if z.ph == "wait" then
		if call("tear", g, z) then return end -- (planks first)
		if g.st ~= "over" and n >= z.t and (g.win[z.win] or 0) <= n then
			z.ph = "climb"
			z.t0 = n
			z.dur = if z.kind > 0 then R.climbRun else R.climb
			g.win[z.win] = n + z.dur * 0.6
			-- over the sill (a tween on the anchored body: everyone sees it smooth), then down inside
			local k = z.k or 1
			local mid = w.at.Position - Vector3.new(0, 0.6, 0) + Vector3.new(0, Hitbox.ROOT_UP * k - 1.5, 0)
			local inAt = w.inn + Vector3.new(0, Hitbox.ROOT_UP * k, 0)
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
	local cap = z.speed
	if not over then
		local slow = call("zombieSpeed", g, z)
		local s = if z.close then 0 else z.speed * (if z.swingAt > 0 then 0.35 else 1) * (if type(slow) == "number" then slow else 1)
		cap = math.max(z.speed, s) -- (a boss's charge, a Screamer's hype: faster than its walk)
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
		z.hum.WalkSpeed = math.min(sp, cap * 1.3)
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
	task.spawn(function()
		-- (a live server streams: the far map copy reaches the client before the body lands on it)
		local g, p = G, m.p
		if g and p and workspace.StreamingEnabled then
			local at = spawnPoint(g, m)
			pcall(function() p:RequestStreamAroundAsync(at, 6) end)
		end
		Fight.spawn(f)
	end)
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
		if not m.p then pcall(function() (r :: BasePart):SetNetworkOwner(nil) end) end -- (a bot: the server moves it)
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
	local selfT = call("downed", g, m) -- (Get Up Juice: back up by yourself in a few seconds; the colas go)
	t.alive = false
	t.hp = 1 -- (the body stays up: HP shows 0, the HUD's down screen takes over)
	local p = m.p
	if p then p:SetAttribute("Hp", 0) end
	local anyUp = false
	for _, o in g.members do if o ~= m and o.f.alive then anyUp = true end end
	local r = Fight.root(t)
	if g.st == "over" or not (anyUp or selfT) or not r then
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
	m.down = { at = CFrame.lookAt(feet + Vector3.new(0, Hitbox.ROOT_UP, 0), feet + Vector3.new(0, Hitbox.ROOT_UP, 0) + look), untilT = now() + R.bleed,
		self = if type(selfT) == "number" then now() + selfT else nil }
	if p then
		p:SetAttribute("ZmDown", workspace:GetServerTimeNow() + R.bleed)
		p:SetAttribute("ACGrace", os.clock() + R.bleed + 5)
	end
	-- the revive: hold Q over them (27 Nov 2026: F is the flashlight now, and E the grapple)
	local pr = Instance.new("ProximityPrompt")
	pr.Name = "ZmRevive"
	pr.ActionText = "Revive"
	pr.ObjectText = m.name
	pr.KeyboardKeyCode = Enum.KeyCode.Q
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

-- ------------------------------------------------------------------ doors and wall guns (Q)
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
	-- (26 Nov 2026, the owner: "doors dont have animations the ones you buy") it rolls up into its housing, slat by slat,
	-- with a recorded rattle: every client plays the roll itself, smooth, from ZmOpenT (ZombiesClient.rollUp). the server
	-- only hides the shutter once the roll is done, so anyone who missed it still sees the door open
	sh:SetAttribute("ZmOpenT", workspace:GetServerTimeNow())
	task.delay(R.doorRoll + 0.4, function() if sh.Parent then sh.Transparency = 1 end end)
	sayAll({ k = "door", i = i, by = if by then by.name else nil, label = d.label, sh = sh })
end
local function prompt(parent: BasePart, action: string, object: string, hold: number): ProximityPrompt
	local pr = Instance.new("ProximityPrompt")
	pr.ActionText = action
	pr.ObjectText = object
	-- (Q since 27 Nov 2026, the owner: "f for flashlight". most games buy on E, but E is the grapple here; Q's other
	-- jobs, the katana's wave and the Scythe's form, aren't in ZOMBIES)
	pr.KeyboardKeyCode = Enum.KeyCode.Q
	pr.HoldDuration = hold
	pr.MaxActivationDistance = 9
	pr.RequiresLineOfSight = false
	pr.Parent = parent
	return pr
end
Zombies.lastRefusal = ""
local function buyerOf(g: Game, pl: Player): Member?
	local f = Fight.byPlayer[pl]
	local m = f and g.byF[f]
	if not m then Zombies.lastRefusal = pl.Name .. ": not in this game"; return nil end
	if not m.f.alive or g.st == "over" then Zombies.lastRefusal = pl.Name .. ": down or over"; return nil end
	if not inOpenArea(m) then -- (movement is the client's: walking through a shutter buys nothing)
		local r = Fight.root(m.f)
		Zombies.lastRefusal = pl.Name .. ": not in an open area (at " .. tostring(r and ZM.areaAt(g.map, feetOf(r))) .. ")"
		return nil
	end
	Zombies.lastRefusal = ""
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
				local total = maxTotal(m, b.w)
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

-- ------------------------------------------------------------------ the squad's bots (web server/zmbots.js)
-- a squad is always Zombies.SQUAD: bots take the empty slots. their bodies, spawns and credits are here; their brains
-- (revive, fight, shop, hold a window: ZombieBots.luau, since 26 Nov 2026) step through Zombies.ext.botStep. they go
-- down like anyone and are revived the same way (hold Q over them). their models live in the arena (not
-- workspace.Dummies: nobody's aim locks onto them) and nothing queries them (shots pass through)
Zombies.SQUAD = 4
local BOT_SHIRT = { Color3.fromRGB(70, 110, 170), Color3.fromRGB(150, 70, 60), Color3.fromRGB(90, 130, 80), Color3.fromRGB(170, 140, 70) }
local BOT_SKIN = { Color3.fromRGB(234, 184, 146), Color3.fromRGB(160, 110, 80), Color3.fromRGB(250, 214, 176), Color3.fromRGB(120, 82, 60) }
local BOT_GUNS = { "revolver", "pistol" }
local botWalk: { [Member]: AnimationTrack? } = {}
local function botBody(i: number): Model
	local shirt, skin = BOT_SHIRT[(i - 1) % 4 + 1], BOT_SKIN[(i - 1) % 4 + 1]
	local ok, m = pcall(function()
		local d = Instance.new("HumanoidDescription")
		d.HeadColor, d.LeftArmColor, d.RightArmColor = skin, skin, skin
		d.TorsoColor = shirt
		d.LeftLegColor, d.RightLegColor = Color3.fromRGB(52, 56, 66), Color3.fromRGB(52, 56, 66)
		return Players:CreateHumanoidModelFromDescription(d, Enum.HumanoidRigType.R15)
	end)
	local body: Model = if ok and m then m :: Model else Instance.new("Model")
	body.Name = "Bot " .. i
	for _, d in body:GetDescendants() do
		if d:IsA("BasePart") then d.CollisionGroup = GROUP; d.CanQuery = false; d.Material = Enum.Material.SmoothPlastic end
	end
	local hum = body:FindFirstChildOfClass("Humanoid")
	if hum then
		hum.DisplayName = "Bot " .. i
		hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.Viewer
		hum.NameDisplayDistance = 80
		hum.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
		hum.BreakJointsOnDeath = true
		hum.AutoJumpEnabled = false
	end
	local hs = body:FindFirstChild("Health")
	if hs then hs:Destroy() end
	body:SetAttribute("ZmBot", i)
	return body
end
-- a (new) body at a spawn, full HP, its kit in hand
local function botSpawn(g: Game, m: Member)
	local b = m.bot :: Bot
	local f = m.f
	local old = f.ref
	if typeof(old) == "Instance" then
		Fight.byModel[old :: any] = nil
		if (old :: Instance).Parent then (old :: Instance):Destroy() end
	end
	local body = botBody(b.i)
	local at, look = spawnPoint(g, m)
	local pos = at + Vector3.new(0, Hitbox.ROOT_UP + 0.2, 0)
	local lk = if look then Vector3.new(look.X, 0, look.Z) else Vector3.xAxis
	body:PivotTo(CFrame.lookAt(pos, pos + (if lk.Magnitude > 1e-3 then lk.Unit else Vector3.xAxis)))
	f.ref = body
	f.forced = kitList(m)
	Rules.spawn(f, now())
	f.held = b.gun
	body.Parent = g.model
	Fight.byModel[body] = f
	local r = body:FindFirstChild("HumanoidRootPart") :: BasePart?
	if r then pcall(function() (r :: BasePart):SetNetworkOwner(nil) end) end
	m.down, m.dead, m.reviver = nil, false, nil
	if m.prompt then m.prompt:Destroy(); m.prompt = nil end
	b.mag, b.reloadUntil, b.task, b.th = (W[b.gun].mag :: number?) or 6, 0, nil, nil
	Fight.syncHp(f)
	Fight.showWeapon(f)
	local hum = body:FindFirstChildOfClass("Humanoid")
	botWalk[m] = if hum then walkTrack(hum, Zombies.BOT_WALK) else nil
end
local function addBot(g: Game, i: number)
	local gun = BOT_GUNS[math.random(1, #BOT_GUNS)]
	local f = Rules.newFighter("zbot", "Bot " .. i, nil)
	local m: Member = {
		f = f, p = nil, name = "Bot " .. i, c = R.start, guns = { gun }, melee = R.startMelee, res = {},
		kills = 0, heads = 0, downs = 0, revives = 0, earned = 0, hurtT = 0, iframe = 0, down = nil, dead = false,
		reviver = nil, reviveT = 0, field = nil, prompt = nil,
		bot = {
			i = i, gun = gun, mag = 6, reloadUntil = 0, nextShot = 0, th = nil, td = math.huge, task = nil, revT0 = 0,
			think = 0, side = 1, sideT = 0, chk = now(), chkPos = Vector3.zero, stuck = 0,
			spot = { d = {}, t = -math.huge, at = Vector3.new(1e9, 0, 0) },
		},
	}
	table.insert(g.members, m)
	g.byF[f] = m
	table.insert(Fight.all, f)
	botSpawn(g, m)
end
local function removeBot(g: Game, m: Member)
	local fi = table.find(Fight.all, m.f)
	if fi then table.remove(Fight.all, fi) end
	g.byF[m.f] = nil
	m.f.alive = false
	local body = m.f.ref
	if typeof(body) == "Instance" then
		Fight.byModel[body :: any] = nil
		(body :: Instance):Destroy()
	end
	if m.prompt then m.prompt:Destroy() end
	botWalk[m] = nil
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
				local rm = call("regenMul", g, m)
				f.hp = math.min(f.maxHp or Weapons.HP, f.hp + R.regen * dt * (if type(rm) == "number" then rm else 1))
				Fight.syncHp(f)
			end
			continue
		end
		local d = m.down
		if not d then continue end
		if d.self and n >= d.self and g.st ~= "over" then standUp(m, nil); continue end -- (Get Up Juice)
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
	local okO, errO = pcall(call, "over", g) -- (ZombieExtract: the game over's XP)
	if not okO then warn("[jankfire] zombies over: " .. tostring(errO)) end
	publish()
end
local function nextRound(g: Game)
	call("round", g)
	g.n += 1
	g.st = "live"
	g.toSpawn = ZM.count(g.n, #g.members)
	g.spawnAt = now() + 1.5
	for _, m in g.members do
		if m.f.alive then continue end
		if m.bot then botSpawn(g, m) else if m.dead or not m.down then freshKit(m) end; respawn(m) end
	end
	sayAll({ k = "round", st = "start", n = g.n })
	publish()
end
local function cleared(g: Game)
	g.st = "break"
	g.untilT = now() + R.rest
	sayAll({ k = "round", st = "clear", n = g.n })
	local okC, errC = pcall(call, "cleared", g) -- (ZombieExtract: the extraction's offer, a longer break)
	if not okC then warn("[jankfire] zombies cleared: " .. tostring(errC)) end
	publish()
end
local function tick(g: Game, dt: number)
	g.tick += 1
	for _, z in table.clone(g.mobs) do
		if z.ph == "hunt" and z.f.alive and (now() - z.seen > 25 or z.stuck > 8) then call("lost", g, z); removeMob(g, z); g.toSpawn += 1 end -- lost or wedged: again from a window
	end
	if g.st == "over" then
		for _, z in g.mobs do step(g, z, dt) end
		if g.overT and now() - g.overT > 12 then Zombies.stop("over") end
		return
	end
	fields(g)
	squadTick(g, dt)
	local okX, errX = pcall(call, "tick", g, dt)
	if not okX then warn("[jankfire] zombies extra tick: " .. tostring(errX)) end
	if g.st == "over" or G ~= g then return end -- (27 Nov: an extraction ends the game in there; a stale break would start the next round)
	-- over when nobody's up: everyone down or out (someone on their way back in, a respawn loading, still counts as up)
	local anyUp = false
	for _, m in g.members do
		if m.f.alive or (not m.down and not m.dead) or (m.down and m.down.self) then anyUp = true end
	end
	if #g.members > 0 and not anyUp then
		for _, m in g.members do if m.down then bleedOut(m) end end -- (a downed player with nobody up: out at once)
		gameOver(g)
		return
	end
	for _, z in g.mobs do step(g, z, dt) end
	local bs = Zombies.ext.botStep -- (the bots' brains: ZombieBots.luau)
	if bs then
		for _, m in g.members do
			if m.bot then
				local okB, errB = pcall(bs, g, m, dt)
				if not okB then warn("[jankfire] zombies bot: " .. tostring(errB)) end
			end
		end
	end
	if g.st ~= "live" then
		if now() >= g.untilT then nextRound(g) end
		if g.tick % 5 == 0 then publish() end
		return
	end
	local alive = 0
	for _, z in g.mobs do if z.f.alive then alive += 1 end end
	local cap, gap = ZM.maxAlive(#g.members), ZM.gap(g.n, #g.members)
	local hv = call("heavy", g) -- (ZombieExtract's hold-out: more at once, faster)
	if type(hv) == "table" then cap = math.min(hv.cap or cap, math.floor(cap * (hv.alive or 1) + 0.5)); gap *= (hv.gap or 1) end
	if g.toSpawn > 0 and alive < cap and now() >= g.spawnAt then
		local live = {}
		for _, m in g.members do if m.f.alive then table.insert(live, m) end end
		g.spawnAt = now() + (if spawnOne(g, live) then gap else 0.5)
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
		if g and by ~= nil then -- (nobody behind it: a fall, the void. as for anyone)
			local tz, bz = t.kind == "zombie", by.kind == "zombie"
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
		local g = G
		local z = g and g.byMob[t]
		local a = by and member(by)
		if g and z and a and Weapons.base(wid) == "revolver" then
			amt *= R.revolverDmg / math.max(1, W.revolver.dmg :: number) -- (zombies keep the revolver's old 40)
		end
		if g and z and a then
			local x = call("hitZombie", g, z, amt, a, wid)
			if type(x) == "number" then amt = x end
		end
		return amt
	end
	Fight.lastStand = goDown
	-- (20 Nov 2026, the owner: "I loaded in but I cant move") a squad member spawns free to move, whatever else
	-- anchored the body on the way in (Party's lobby plinths anchor a party's bodies on spawn)
	Fight.onSpawn(function(f: Fighter)
		local m = member(f)
		if not m or not m.p then return end
		for _ = 1, 3 do
			task.wait(0.25)
			if member(f) ~= m or m.down then return end
			local r = Fight.root(f)
			if r and r.Anchored then r.Anchored = false end
		end
	end)
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
			local head = (z.lastHs or call("allHeads", g) == true) and not melee
			give(k, if melee or head then R.bonus else R.kill, if melee then "melee" elseif head then "head" else "kill")
			k.kills += 1
			if head then k.heads += 1 end
		end
		call("killed", g, z, k)
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
			return if f and member(f) then "match" else nil -- (a zombies game is a match to every menu: hub buttons hidden, loadouts locked)
		end
	end
end

-- ------------------------------------------------------------------ start / stop
-- start a game: (the game's id, a line about the map) or (nil, why). players: the real ones (1 to 4); the squad's bots
-- fill the empty slots. opts.queue: which queue it came from (kept for the results)
local startGame: (players: { Player }, mapName: string) -> (string?, string?)
function Zombies.start(players: { Player }, mapName: string, _opts: { queue: string }?): (string?, string?)
	if Zombies.busy() then return nil, "busy" end
	starting += 1 -- (busy from the moment a start begins, play-party's queue: not only once it's done)
	local ok, id, why = pcall(startGame, players, mapName)
	starting -= 1
	if not ok then warn("[jankfire] zombies start: " .. tostring(id)); return nil, "start failed" end
	return id, why
end
startGame = function(players: { Player }, mapName: string): (string?, string?)
	hook()
	local tpl = source(mapName)
	if not tpl then return nil, "no zombies map " .. mapName end
	local model = tpl:Clone()
	model:SetAttribute("Enabled", nil) -- (the source sits out of the PvP pool; this copy is the game)
	model:PivotTo(SITE)
	model.Parent = workspace
	local map, why = ZM.read(model)
	if not map then model:Destroy(); return nil, why end
	local shutters = {}
	for _, d in map.doors do table.insert(shutters, d.shutter) end
	local skip: { Instance } = { dummies() }
	for _, p in Players:GetPlayers() do if p.Character then table.insert(skip, p.Character) end end
	local hidden = {}
	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") and d.CanCollide and not d.CanQuery then d.CanQuery = true; table.insert(hidden, d) end
	end
	local nav = Nav.build(map.bounds, shutters, skip)
	for _, d in hidden do d.CanQuery = false end
	local g: Game = {
		map = map, model = model, nav = nav, open = {}, areas = {}, n = 0, st = "pre", untilT = now() + R.first,
		toSpawn = 0, spawnAt = 0, win = {}, members = {}, byF = {}, mobs = {}, byMob = {}, fieldT = now(), tick = 0, lastT = now(),
		templates = {}, prompts = {}, mobId = 0, overT = nil, conn = nil, id = "", players = {},
		cost = { n = 0, sum = 0, max = 0 },
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
		p:SetAttribute("Arena", mapName) -- (HubLife lights your screen by it: the school's own night look, HubLook.byArena)
		respawn(m)
	end
	for i = #g.members + 1, Zombies.SQUAD do addBot(g, i - #players) end
	wirePrompts(g)
	call("start", g)
	model:SetAttribute("Label", map.label)
	publish()
	local acc = 0
	g.conn = RunService.Heartbeat:Connect(function(dt: number)
		acc += dt
		if acc < 0.1 then return end
		local step = math.min(acc, 0.25)
		acc = 0
		if G ~= g then return end
		local t0 = os.clock()
		local ok, err = pcall(tick, g, step)
		if not ok then warn("[jankfire] zombies tick: " .. tostring(err)) end
		local c = (os.clock() - t0) * 1000
		local cost = g.cost
		cost.n += 1; cost.sum += c; cost.max = math.max(cost.max, c)
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
	for _, m in table.clone(g.members) do if m.bot then removeBot(g, m) end end
	for _, m in g.members do
		if m.bot then continue end
		local f, p = m.f, m.p
		if m.prompt then m.prompt:Destroy() end
		f.forced = nil
		local r = Fight.root(f)
		if r then r.Anchored = false end
		if p and p.Parent then
			p:SetAttribute("ZmOn", nil); p:SetAttribute("ZmC", nil); p:SetAttribute("ZmDown", nil); p:SetAttribute("ZmOut", nil)
			p:SetAttribute("ZmArena", nil)
			p:SetAttribute("Arena", nil)
			for wid in m.res do p:SetAttribute("ZmRes_" .. wid, nil) end
			p:SetAttribute("TeleportT", os.clock())
			f.alive = false
			task.spawn(function() Fight.spawn(f) end) -- (back to the hub with your own loadout)
		end
	end
	for _, t in g.templates do t:Destroy() end
	pcall(call, "stop", g)
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
	return { on = true, n = g.n, st = g.st, toSpawn = g.toSpawn, mobs = mobs, members = ms, open = g.open, cells = g.nav.cells, built = g.nav.built,
		refusal = Zombies.lastRefusal, areas = g.areas,
		tickMs = if g.cost.n > 0 then string.format("avg %.2f max %.2f over %d ticks", g.cost.sum / g.cost.n, g.cost.max, g.cost.n) else "",
		layers = g.nav.L, windows = #g.map.windows, doors = #g.map.doors }
end
function Zombies.round(n: number)
	local g = G
	if not g then return end
	for _, z in table.clone(g.mobs) do removeMob(g, z) end
	for _, k in { "BossName", "BossHp", "BossMax" } do g.model:SetAttribute(k, nil) end -- (a boss swept off with the rest: no stale bar)
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

-- (the mode's own parts, for ZombieExtra.luau)
Zombies.X = {
	give = give, pay = pay, say = say, sayAll = sayAll, member = member, inOpenArea = inOpenArea, arm = arm, grant = grant,
	pushRes = pushRes, removeMob = removeMob, standUp = standUp, feetOf = feetOf, flat = flat, publish = publish,
	kitList = kitList, prompt = prompt, buyerOf = buyerOf, maxTotal = maxTotal,
	openDoor = openDoor, botWalk = function(m: Member): AnimationTrack? return botWalk[m] end, -- (ZombieBots)
	fight = function(): any return Fight end,
	saveBest = function(g: Game) saveBest(g) end, gameOver = function(g: Game) gameOver(g) end, site = SITE, -- (ZombieExtract)
}

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
			elseif op == "door" then local g = G; if g and g.map.doors[tonumber(a) or 0] then openDoor(g, tonumber(a) :: number, nil) end; return true -- (one door: its roll)
			elseif op == "max" then R.maxAlive = tonumber(a); return true
			elseif op == "cost" then local g = G; if g then g.cost = { n = 0, sum = 0, max = 0 } end; return true
			elseif op == "maps" then return Zombies.maps()
			end
			local tx = Zombies.ext.test -- (stage 2's own: ZombieExtra)
			if tx then local r = tx(op, a, b); if r ~= nil then return r end end
			return "ops: start, stop, state, round, credits, open, door n, max, cost, maps (+ ZombieExtra's, ZombieSpecial's, ZombieBots' bots)"
		end
	end
end

return Zombies
