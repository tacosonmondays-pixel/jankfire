--!strict
-- THE WEAPON TUTORIAL ROOMS (20 Nov 2026; the owner: "a room with a course that teraches you how to use each gun and the
-- course changed in like a hologram effect with a button you press it, it pulls up a menu with all the weapons select
-- one, and itll place a small course or shooting thingyu dpeending on what you picked to teach you how to use it").
-- Four private rooms off the training wing's corridor (TrainingRedo builds them: TrainingGround.Tutorial.Room<n>).
--   * walk into a free room and it is yours: its lamp turns amber, the room's folder gets User = your UserId (every
--     other client makes the mouth solid for itself: TutorialUI), and you get a note to use the console
--   * the console (E) opens the menu on your screen (TutorialUI); a pick comes back here as ("pick", id): the room's old
--     course goes, the new one is built in the room's Course model (TutorialUI dresses it as a hologram with the
--     build-in sweep) and its targets pop up: cardboard Carls that are yours alone (Owner + onlyFor, as the range's)
--   * your hits and kills on them count toward the entry's goal (TutorialData); met, you get the time and your best
--     this visit; the Carls keep coming back until then
--   * leave the room (or die, or leave the game) and it clears for the next one
-- The weapon itself comes from the training try layer: TutorialUI asks the Loadout remote for it, as the loadout screen
-- does (in training any weapon, owned or not, never saved).
-- Studio only: ServerStorage.JankTutorialTest (a BindableFunction): ("state"), ("open", userId?) the console's menu,
-- ("claim", roomIndex, userId?) puts the
-- first player (or that one) in the room as its user, ("pick", wid, userId?), ("hit", userId?) puts down one of their Carls as if
-- they shot it, ("release", roomIndex)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Roster = require(Shared:WaitForChild("Roster")) :: any
local TD = require(Shared:WaitForChild("TutorialData")) :: any
local Rules = require(script.Parent:WaitForChild("Rules"))
local Dummies = require(script.Parent:WaitForChild("Dummies")) :: any -- (the practice turret's burst: Dummies.burst)
local Fight = require(script.Parent:WaitForChild("Fight")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local CalloutR = Remotes:WaitForChild("Callout") :: RemoteEvent
local TutR = Remotes:FindFirstChild("Tutorial") :: RemoteEvent?
if not TutR then
	local r = Instance.new("RemoteEvent")
	r.Name = "Tutorial"
	r.Parent = Remotes
	TutR = r
end
local R = TutR :: RemoteEvent

type Fighter = Rules.Fighter
type Target = { f: Fighter?, spec: any, home: CFrame, phase: number, backAt: number, fireAt: number? }
type Room = {
	i: number, folder: Instance, zone: BasePart, origin: CFrame, lamp: BasePart?, board: BasePart?,
	user: Player?, outAt: number, wid: string?, entry: any, course: Model?, targets: { Target },
	gates: { { part: BasePart, passed: boolean } }, goalZones: { BasePart }, pits: { BasePart },
	got: { [string]: any }, t0: number, done: boolean,
}

local FREE = Color3.fromHex("8fd8cf") -- (TrainingRedo's WING.ACCENT)
local TAKEN = Color3.fromHex("f0a53a")
local PIECE = Color3.fromHex("cfe9e5") -- the course's pieces before the client's hologram look
local REBIRTH = 1.2 -- s until a downed Carl is back
local OUT_GRACE = 1.0 -- s outside the room before it clears
local rooms: { Room } = {}
local best: { [Player]: { [string]: number } } = {}
local tut: Instance? = nil

local function inside(part: BasePart, pos: Vector3, pad: number): boolean
	local rel = part.CFrame:PointToObjectSpace(pos)
	local h = part.Size / 2
	return math.abs(rel.X) <= h.X + pad and math.abs(rel.Y) <= h.Y + pad and math.abs(rel.Z) <= h.Z + pad
end
local function rootOf(p: Player): BasePart?
	local ch = p.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	if not ch or not hum or hum.Health <= 0 then return nil end
	return ch:FindFirstChild("HumanoidRootPart") :: BasePart?
end
local function roomOf(p: Player): Room?
	for _, r in rooms do if r.user == p then return r end end
	return nil
end
local function nameOf(wid: string): string
	if string.sub(wid, 1, 5) == "move:" then
		for _, m in TD.MOVES do if m.id == wid then return m.name end end
		return string.upper(string.sub(wid, 6))
	end
	local e = Roster.byId[wid]
	return if e then string.upper(e.name) else string.upper(wid)
end

-- ------------------------------------------------------------------ the board on the back wall
local function board(r: Room, a: string, b: string?)
	local bd = r.board
	local g = bd and bd:FindFirstChild("Gui")
	local l = g and g:FindFirstChild("Line1") :: TextLabel?
	if l then
		l.RichText = true
		l.Text = if b then ("%s\n<font size=\"60\">%s</font>"):format(a, b) else a
	end
end

-- ------------------------------------------------------------------ the Carls (the range's kind: RangeTest)
local function dropCarl(t: Target, shot: boolean)
	local f = t.f
	t.f = nil
	if not f then return end
	f.alive = false
	local i = table.find(Fight.all, f)
	if i then table.remove(Fight.all, i) end
	local m = f.ref :: Model?
	if not m then return end
	Fight.byModel[m] = nil
	local body = m:FindFirstChild("Body") :: Model?
	if shot and body then
		local b0 = body:GetPivot()
		task.spawn(function()
			local t0 = os.clock()
			while os.clock() - t0 < 0.22 and body.Parent do
				local u = (os.clock() - t0) / 0.22
				body:PivotTo(b0 * CFrame.new(0, -1.2 * u, 0) * CFrame.Angles(-1.3 * u * u, 0, 0))
				RunService.Heartbeat:Wait()
			end
			task.wait(0.3)
			m:Destroy()
		end)
	else
		m:Destroy()
	end
end

local function popCarl(r: Room, t: Target)
	local user = r.user
	if not user then return end
	local sp = t.spec
	local feet = (r.origin * CFrame.new(sp[1], sp[3] or 0, -sp[2])).Position
	local toUser = Vector3.new(r.origin.Position.X - feet.X, 0, r.origin.Position.Z - feet.Z)
	if toUser.Magnitude < 0.01 then toUser = -r.origin.LookVector end
	toUser = toUser.Unit
	-- (+Z of this frame faces the model's front: toward you, or away for a backstab)
	local base = if sp.back then CFrame.lookAt(feet, feet + toUser) else CFrame.lookAt(feet, feet - toUser)
	t.home = base
	local m = Instance.new("Model")
	m.Name = "Carl"
	local root = Instance.new("Part")
	root.Name = "HumanoidRootPart"; root.Size = Vector3.new(2, 2, 1); root.Transparency = 1
	root.Anchored = true; root.CanCollide = false; root.CanQuery = false; root.CanTouch = false
	root.CFrame = base + Vector3.new(0, Hitbox.ROOT_UP, 0)
	root.Parent = m
	m.PrimaryPart = root
	local lib = ServerStorage:FindFirstChild("JankfireMeshes")
	local tmpl = lib and lib:FindFirstChild("bc_cutout")
	if tmpl and tmpl:IsA("Model") then
		local b = tmpl:Clone()
		b.Name = "Body"
		for _, d in b:GetDescendants() do
			if d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false end
		end
		local cf, sz = b:GetBoundingBox()
		local rel = CFrame.new(0, sz.Y / 2, 0) * (cf:Inverse() * b:GetPivot()).Rotation
		b:PivotTo(base * rel)
		b.Parent = m
	end
	local hum = Instance.new("Humanoid")
	hum.RequiresNeck = false; hum.BreakJointsOnDeath = false
	hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	hum.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
	hum.MaxHealth = 100; hum.Health = 100
	hum.Parent = m
	m:SetAttribute("Dummy", true); m:SetAttribute("Owner", user.UserId); m:SetAttribute("Tutorial", r.i)
	m:SetAttribute("HitNeck", Hitbox.CUTOUT.neck); m:SetAttribute("HitTop", Hitbox.CUTOUT.top)
	m.Parent = workspace:FindFirstChild("Dummies") or workspace
	local f = Rules.newFighter("dummy", "Cardboard Carl", m)
	f.onlyFor = user
	Rules.spawn(f, os.clock())
	local g = r.entry and r.entry.goal or {}
	f.hp = sp.hp or (if g.kills then 100 else 1000)
	Fight.byModel[m] = f
	table.insert(Fight.all, f)
	t.f = f
end

-- ------------------------------------------------------------------ the course's pieces
local function piece(r: Room, cm: Model, name: string, cf: CFrame, size: Vector3, shape: Enum.PartType?): Part
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true; p.CanTouch = false
	p.Size = size
	if shape then p.Shape = shape end
	p.CFrame = r.origin * cf
	p.Color = PIECE; p.Material = Enum.Material.SmoothPlastic
	p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	p.Parent = cm
	return p
end
local function zonePart(r: Room, name: string, cf: CFrame, size: Vector3): Part
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Transparency = 1
	p.Size = size
	p.CFrame = r.origin * cf
	p.Parent = r.course
	return p
end
-- build a piece from its row (TutorialData): local x across, z into the room, y up
local function build(r: Room, row: any)
	local cm = r.course :: Model
	local k, x, z = row[1], row[2], row[3]
	if k == "box" then
		local w, h, d, y = row[4], row[5], row[6], row[7] or 0
		piece(r, cm, "Block", CFrame.new(x, y + h / 2, -z), Vector3.new(w, h, d))
	elseif k == "post" then
		local h = row[4]
		piece(r, cm, "Post", CFrame.new(x, h / 2, -z) * CFrame.Angles(0, 0, math.pi / 2), Vector3.new(h, 2.6, 2.6), Enum.PartType.Cylinder)
		piece(r, cm, "PostTop", CFrame.new(x, h - 0.2, -z), Vector3.new(3.6, 0.4, 3.6))
	elseif k == "bar" then
		local w, y = row[4], row[5]
		piece(r, cm, "Bar", CFrame.new(x, y + 0.6, -z), Vector3.new(w, 1.2, 1.2), Enum.PartType.Cylinder)
		for _, s in { -1, 1 } do piece(r, cm, "BarPost", CFrame.new(x + s * (w / 2 + 0.6), (y + 1.2) / 2, -z), Vector3.new(1.2, y + 1.2, 1.2)) end
	elseif k == "gate" then
		local w, h = row[4], row[5] or 9
		for _, s in { -1, 1 } do piece(r, cm, "GatePost", CFrame.new(x + s * (w / 2 + 0.6), h / 2, -z), Vector3.new(1.2, h, 1.2)) end
		piece(r, cm, "GateHead", CFrame.new(x, h + 0.6, -z), Vector3.new(w + 2.4, 1.2, 1.2))
		local trig = zonePart(r, "GateZone", CFrame.new(x, h / 2, -z), Vector3.new(w, h, 3))
		table.insert(r.gates, { part = trig, passed = false })
	elseif k == "ledge" then
		local w, h, d = row[4], row[5], row[6]
		piece(r, cm, "Ledge", CFrame.new(x, h / 2, -z), Vector3.new(w, h, d))
		table.insert(r.goalZones, zonePart(r, "GoalZone", CFrame.new(x, h + 3, -z), Vector3.new(w, 6, d)))
	elseif k == "pit" then
		local w, d = row[4], row[5]
		local p = piece(r, cm, "Pit", CFrame.new(x, 0.1, -z), Vector3.new(w, 0.2, d))
		p.Color = Color3.fromHex("3a3f47")
		p:SetAttribute("Pit", true)
		table.insert(r.pits, zonePart(r, "PitZone", CFrame.new(x, 2.4, -z), Vector3.new(w, 4.6, d)))
	end
end

local function clearCourse(r: Room)
	for _, t in r.targets do dropCarl(t, false) end
	r.targets = {}
	r.gates, r.goalZones, r.pits = {}, {}, {}
	if r.course then r.course:Destroy() end
	r.course = nil
	r.wid, r.entry, r.done = nil, nil, false
	r.got = {}
end

local function userFighter(p: Player): Fighter? return Fight.byPlayer[p] end

local function start(r: Room, wid: string)
	local user = r.user
	if not user then return end
	clearCourse(r)
	local en = TD.W[wid]
	if not en then return end
	r.wid, r.entry = wid, en
	local cm = Instance.new("Model")
	cm.Name = "Course"
	cm:SetAttribute("Weapon", wid)
	cm:SetAttribute("Stamp", os.clock())
	r.course = cm
	local pieces, targets = TD.course(wid)
	for _, row in pieces do build(r, row) end
	cm.Parent = r.folder -- (all its pieces in it before it is in the world: the client dresses it in one go)
	cm:SetAttribute("Ready", true)
	for _, sp in targets do
		local t: Target = { f = nil, spec = sp, home = CFrame.identity, phase = math.random() * 6, backAt = 0 }
		table.insert(r.targets, t)
		popCarl(r, t)
	end
	-- (the medkit, the Redline: the room starts you low)
	local st = en.start
	if st and st.hp then
		local f = userFighter(user)
		if f and f.alive and f.hp > st.hp then Fight.hurt(f, f.hp - st.hp, nil, "tutorial", false, nil, nil, nil, true) end
	end
	r.t0 = os.clock()
	r.got = {}
	user:SetAttribute("TutorialWeapon", wid)
	board(r, nameOf(wid), TD.goalText(en.goal, r.got))
	R:FireClient(user, "course", { room = r.i, wid = wid, name = nameOf(wid), moves = en.moves, goal = en.goal, best = (best[user] or {})[wid] })
end

local function release(r: Room)
	local u = r.user
	clearCourse(r)
	r.user = nil
	r.folder:SetAttribute("User", nil)
	if r.lamp then r.lamp.Color = FREE end
	board(r, "")
	if u and u.Parent then
		u:SetAttribute("TutorialWeapon", nil)
		u:SetAttribute("TutorialRoom", nil)
		R:FireClient(u, "left", { room = r.i })
	end
end

local function claim(r: Room, p: Player)
	r.user = p
	r.outAt = 0
	r.folder:SetAttribute("User", p.UserId)
	if r.lamp then r.lamp.Color = TAKEN end
	p:SetAttribute("TutorialRoom", r.i)
	board(r, "ROOM " .. r.i, "USE THE CONSOLE")
	R:FireClient(p, "claimed", { room = r.i })
end

local function progress(r: Room)
	local u = r.user
	if not u or not r.entry or r.done then return end
	board(r, nameOf(r.wid :: string), TD.goalText(r.entry.goal, r.got))
	R:FireClient(u, "prog", { room = r.i, got = r.got })
	if TD.met(r.entry.goal, r.got) then
		r.done = true
		local secs = os.clock() - r.t0
		local mine = best[u] or {}
		best[u] = mine
		local wid = r.wid :: string
		local isBest = mine[wid] == nil or secs < mine[wid]
		if isBest then mine[wid] = secs end
		board(r, nameOf(wid), ("DONE  ·  %.1f S"):format(secs))
		R:FireClient(u, "done", { room = r.i, wid = wid, time = secs, best = mine[wid], newBest = isBest, got = r.got })
	end
end

local function bump(r: Room, key: string, n: number?)
	r.got[key] = (r.got[key] or 0) + (n or 1)
	progress(r)
end

-- ------------------------------------------------------------------ hits and kills on the room's Carls
local function targetOf(f: Fighter): (Room?, Target?)
	for _, r in rooms do
		for _, t in r.targets do if t.f == f then return r, t end end
	end
	return nil, nil
end
Fight.onHurt(function(t: Fighter, done: number, by: Fighter?, _wid: string, hs: boolean?)
	if t.kind ~= "dummy" or not by or done <= 0 then return end
	local r, tg = targetOf(t)
	if not r or not r.user or by.ref ~= r.user or r.done then return end
	if tg and tg.spec.turret then
		r.got.turret = (r.got.turret or 0) + 1 -- (sent back into it: a crit return, a reverse card)
	else
		r.got.hits = (r.got.hits or 0) + 1
		if hs then r.got.heads = (r.got.heads or 0) + 1 end
	end
	progress(r)
end)
Fight.onKill(function(info: any)
	local v = info.v
	if not v or v.kind ~= "dummy" then return end
	local r, t = targetOf(v)
	if not r or not t then return end
	local k = info.k
	if r.user and k and k.ref == r.user and not r.done then bump(r, "kills") end
	dropCarl(t, true)
	t.backAt = os.clock() + REBIRTH
end)

-- ------------------------------------------------------------------ the rooms in the map
local function wire(folder: Instance, i: number): Room?
	local zone = folder:FindFirstChild("Zone") :: BasePart?
	local origin = folder:FindFirstChild("Origin") :: BasePart?
	if not zone or not origin then return nil end
	local r: Room = {
		i = i, folder = folder, zone = zone, origin = origin.CFrame, lamp = folder:FindFirstChild("DoorLamp") :: BasePart?,
		board = folder:FindFirstChild("Board") :: BasePart?, user = nil, outAt = 0, wid = nil, entry = nil, course = nil,
		targets = {}, gates = {}, goalZones = {}, pits = {}, got = {}, t0 = 0, done = false,
	}
	if r.lamp then r.lamp.Color = FREE end
	folder:SetAttribute("User", nil)
	local old = folder:FindFirstChild("Course")
	if old then old:Destroy() end
	local btn = folder:FindFirstChild("Console")
	local pp = btn and btn:FindFirstChild("Prompt") :: ProximityPrompt?
	if pp then
		pp.Triggered:Connect(function(p: Player)
			if r.folder.Parent == nil then return end
			if r.user == p then
				R:FireClient(p, "open", { room = r.i, wid = r.wid })
			else
				CalloutR:FireClient(p, "THIS ROOM IS IN USE", 1.2)
			end
		end)
	end
	board(r, "")
	return r
end
local function find()
	local hub = workspace:FindFirstChild("Map") and workspace.Map:FindFirstChild("Hub")
	local tg = hub and hub:FindFirstChild("TrainingGround")
	local f = tg and tg:FindFirstChild("Tutorial")
	-- (Studio: before v4 is live, a staging copy's rooms: TrainingV2.build("stage"), Map.TrainingStage)
	if not f and RunService:IsStudio() then
		local st = workspace:FindFirstChild("Map") and workspace.Map:FindFirstChild("TrainingStage")
		local stg = st and st:FindFirstChild("TrainingGround")
		f = stg and stg:FindFirstChild("Tutorial")
	end
	if f == tut then return end
	for _, r in rooms do release(r) end
	rooms = {}
	tut = f
	if not f then return end
	for i = 1, 8 do
		local rf = f:FindFirstChild("Room" .. i)
		if not rf then break end
		local r = wire(rf, i)
		if r then table.insert(rooms, r) end
	end
end

R.OnServerEvent:Connect(function(p: Player, op: unknown, a: unknown)
	local r = roomOf(p)
	if not r then return end
	if op == "pick" and type(a) == "string" then
		local en = TD.W[a]
		if not en then return end
		if string.sub(a, 1, 5) ~= "move:" then
			local re = Roster.byId[a]
			if not re or not re.live then return end
		end
		start(r, a)
	elseif op == "clear" then
		clearCourse(r)
		board(r, "ROOM " .. r.i, "USE THE CONSOLE")
	end
end)

-- ------------------------------------------------------------------ every frame: rails, hops; every 0.1 s: who's where
local acc, lookAt = 0, 0
RunService.Heartbeat:Connect(function(dt: number)
	local now = os.clock()
	for _, r in rooms do
		for _, t in r.targets do
			local f = t.f
			local sp = t.spec
			if f and f.alive and (sp.rail or sp.hop) then
				local m = f.ref :: Model?
				if m and m.Parent then
					local off = Vector3.zero
					if sp.rail then
						local span, speed = sp.rail[1], sp.rail[2]
						off += r.origin.RightVector * span * math.sin((now + t.phase) * speed / span)
					end
					if sp.hop then off += Vector3.new(0, 3 * math.abs(math.sin((now + t.phase) * 2.4)), 0) end
					local root = m.PrimaryPart
					if root then
						local want = t.home + off + Vector3.new(0, Hitbox.ROOT_UP, 0)
						local delta = want.Position - root.Position
						if delta.Magnitude > 0.01 then m:PivotTo(m:GetPivot() + delta) end
					end
				end
			end
		end
	end
	acc += dt
	if acc < 0.1 then return end
	acc = 0
	if now - lookAt > 2 then lookAt = now; find() end
	for _, r in rooms do
		local u = r.user
		if u then
			local root = if u.Parent then rootOf(u) else nil
			if not root or not inside(r.zone, root.Position, 2) then
				if r.outAt == 0 then r.outAt = now end
				if not root or not u.Parent or now - r.outAt > OUT_GRACE then release(r) end
				continue
			end
			r.outAt = 0
			-- Carls back up; the practice turret's burst every 3 s (not once the goal is met)
			if r.entry and not r.done then
				local uf = userFighter(u)
				for _, t in r.targets do
					if not t.f and t.backAt > 0 and now >= t.backAt then t.backAt = 0; popCarl(r, t) end
					local f = t.f
					if t.spec.turret and f and f.alive and uf and uf.alive and now >= (t.fireAt or 0) then
						t.fireAt = now + 3
						if (t.fireAt :: number) > 0 and Dummies.burst then Dummies.burst(f, uf, 3) end
					end
				end
			end
			-- gates, the goal ledge, the pit, the HP goal
			if r.entry and not r.done then
				local changed = false
				for _, g in r.gates do
					if not g.passed and inside(g.part, root.Position, 0.5) then g.passed = true; r.got.gates = (r.got.gates or 0) + 1; changed = true end
				end
				for _, gz in r.goalZones do
					if not r.got.reach and inside(gz, root.Position, 0.5) then r.got.reach = true; changed = true end
				end
				for _, pz in r.pits do
					if inside(pz, root.Position, 0) then
						u:SetAttribute("TeleportT", os.clock())
						local ch = u.Character
						local at = r.origin.Position + Vector3.new(0, 3, 0)
						if ch then ch:PivotTo(CFrame.lookAt(at, at + r.origin.LookVector)) end
						CalloutR:FireClient(u, "AGAIN", 0.8)
					end
				end
				if r.entry.goal.hp then
					local f = userFighter(u)
					local hp = if f then f.hp else 0
					if hp ~= r.got.hp then r.got.hp = hp; changed = true end
				end
				if changed then progress(r) end
			end
		else
			-- a free room: the first one in (who has no other room) takes it
			for _, p in Players:GetPlayers() do
				if roomOf(p) then continue end
				local root = rootOf(p)
				if root and inside(r.zone, root.Position, 0) then claim(r, p); break end
			end
		end
	end
end)

Players.PlayerRemoving:Connect(function(p: Player)
	local r = roomOf(p)
	if r then release(r) end
	best[p] = nil
end)

-- ------------------------------------------------------------------ Studio tests
if RunService:IsStudio() then
	local bf = Instance.new("BindableFunction")
	bf.Name = "JankTutorialTest"
	local function who(uid: any): Player?
		if type(uid) == "number" then return Players:GetPlayerByUserId(uid) end
		return Players:GetPlayers()[1]
	end
	bf.OnInvoke = function(op: string, a: any, b: any): any
		find()
		if op == "claim" then
			local r, p = rooms[a], who(b)
			if not r or not p then return "no room or player" end
			local cur = roomOf(p)
			if cur and cur ~= r then release(cur) end
			if r.user and r.user ~= p then release(r) end
			if r.user ~= p then claim(r, p) end
			return "claimed room " .. r.i
		elseif op == "pick" then
			local p = who(b)
			local r = p and roomOf(p)
			if not r then return "no room" end
			if not TD.W[a] then return "no entry " .. tostring(a) end
			start(r, a)
			return "started " .. a .. " in room " .. r.i .. " with " .. #r.targets .. " targets"
		elseif op == "hit" then
			local p = who(a)
			local r = p and roomOf(p)
			if not r or not p then return "no room" end
			for _, t in r.targets do
				local f = t.f
				if f and f.alive and not t.spec.turret then
					Fight.hurt(f, f.hp, userFighter(p), "ar", true)
					return "hit one"
				end
			end
			return "no Carl up"
		elseif op == "open" then -- (the console's E, as if pressed)
			local p = who(a)
			local r = p and roomOf(p)
			if not r or not p then return "no room" end
			R:FireClient(p, "open", { room = r.i, wid = r.wid })
			return "opened"
		elseif op == "release" then
			local r = rooms[a]
			if r then release(r) end
			return "released"
		end
		local out = {}
		for _, r in rooms do
			local up = 0
			for _, t in r.targets do if t.f and t.f.alive then up += 1 end end
			table.insert(out, { room = r.i, user = r.user and r.user.Name, wid = r.wid, targets = #r.targets, up = up, got = r.got, done = r.done,
				pieces = r.course and #r.course:GetChildren() or 0 })
		end
		return out
	end
	bf.Parent = ServerStorage
end
