--!strict
-- THE BACK LOT (16 Nov 2026): the training area's secret outdoor grounds behind the big garage door at the end of the
-- dummy yard, and the little easter egg that opens it. three GOLD CARLS hide in the training rooms; shoot all three
-- within 90 seconds of the first and the garage door rolls up for 45 seconds. the panel over the door lights one
-- cardboard man per gold Carl down and counts the time left. out on the lot, cardboard Carls on the long lane and in
-- the blocks fold when shot and stand back up. you leave the lot by its side door (Doors.LotExit, LaserDoors) or the
-- garage while it is open. while you are on the lot (attribute OnLot) the Plinker in the yard leaves you alone.
-- a Carl here is a real fighter of kind "dummy", made like RangeTest's (so every weapon and hit check works on him).
-- the door (owner, 16 Nov: "when you go up to garage doors can they slide up"): it rolls up when someone walks up to
-- it. from the lot it always lets you back in; on the yard's side it rolls up for anyone who has opened it before
-- (the egg), and for everyone else it lifts a hand's width, rattles and drops while LOCKED flashes. the slats move on
-- each player's screen (TrainingDoors.client, from the Door's attributes From, Goal, Dur, Since and Rattle); here the
-- server only decides when, and whether the slats block. the map is data, made by ServerStorage.PolishBackup.
-- TrainingLot into Hub.TrainingGround.Lot:
--   Door       (Model) parts with the attribute Shut (their shut CFrame); its attributes Lift (studs it goes up) and
--              Top (a slat whose bottom is over this height is put away inside the wall)
--   Doorway    (Part, unseen) a body inside it holds the door open (nobody is shut in it)
--   Panel      parts with the attribute Pip (1, 2, 3: the cardboard men that light up) and a part Timer whose Gui has Text
--   Beacons    models tagged HubSpin (HubLife turns them while Spin > 0); parts in them with the attribute Lens glow
--   GoldSpots  parts Gold1..Gold3: where a gold Carl stands (its look = the way he faces)
--   Targets    parts: where a lot Carl stands (its look points at the shooters)
--   Area       (Part, unseen) inside it a player is on the lot
-- nothing happens while the training area is v1 (no Lot): it looks again every few seconds.
-- Studio play tests: ServerStorage.LotTest (a BindableFunction, Studio only) answers "state", "gold" (n: put gold Carl
-- n down as if the first player shot him), "lotcarl" (one lot Carl down), "open", "shut", "carls"
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Fight = require(script.Parent:WaitForChild("Fight")) :: any
local CalloutR = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Callout") :: RemoteEvent

local WINDOW = 90     -- seconds from the first gold Carl to get the other two
local OPEN_FOR = 45   -- seconds the door stays up
local MOVE_T = 4.2    -- seconds to roll up when the egg opens it (the reveal)
local MOVE_FAST = 1.5 -- seconds to roll up when someone walks up to it
local CLOSE_T = 2.0   -- seconds to roll down
local NEAR = 11       -- studs out from the doorway (either side) that count as walking up to it
local HOLD = 1.5      -- seconds it stays up after the last person near it has gone
local PASS_U = 0.42   -- over this the bottom slat is high enough to walk under: the slats stop blocking
local BACK_UP = 2.6   -- seconds a lot Carl lies down before he stands up again
local GOLD_BACK = 4   -- seconds after the door is down before the gold Carls are back in their places
local HP = 30         -- like Cardboard Carl's: three rifle rounds, two to the head
local GOLD = Color3.fromRGB(242, 184, 75)
local PIP_OFF = Color3.fromRGB(198, 192, 181) -- (pale: readable on the panel's inset from the yard's steps)

type Entry = { spot: BasePart, gold: number? }
local lot: Instance? = nil
local carls: { [any]: Entry } = {}          -- fighter -> where he stands
local found = { false, false, false }
local firstAt = 0                            -- os.clock() of the first gold Carl down this try (0 = none yet)
local finders: { [Player]: boolean } = {}
local known: { [Player]: boolean } = {}      -- who has opened it this server: it rolls up for them on their own
local greeted: { [Player]: boolean } = {}    -- told "THE GARAGE REMEMBERS YOU" once
local state = "shut"                          -- shut | opening | open | closing
local eggOpen = false                         -- the egg opened it: up for OPEN_FOR, then the egg resets
local moveT = MOVE_FAST
local holdUntil, rattleAt = 0, 0
local u = 0                                   -- how far up the door is: 0 shut .. 1 open
local openUntil = 0
local slats: { { p: BasePart, shut: CFrame, solid: boolean, query: boolean } } = {}
local lift, top = 20.6, math.huge

local function lib(): Instance? return ServerStorage:FindFirstChild("JankfireMeshes") end
local function dummyFolder(): Instance return workspace:FindFirstChild("Dummies") or workspace end

-- the lot's sounds play from the panel over the door, for everyone near it
local function sound(name: string)
	local panel = lot and lot:FindFirstChild("Panel")
	local s = panel and panel:FindFirstChild(name, true)
	if s and s:IsA("Sound") then s:Play() end
end

local function say(p: Player, text: string, dur: number) CalloutR:FireClient(p, text, dur) end
-- a chime where a gold Carl stood (the shooter hears it, wherever the panel is)
local function chime(at: BasePart?)
	local lib = ReplicatedStorage:FindFirstChild("JankfireSounds")
	local src = lib and lib:FindFirstChild("ting")
	if not at or not src or not src:IsA("Sound") then return end
	local s = src:Clone(); s.RollOffMaxDistance = 300; s.Parent = at; s:Play()
	task.delay(3, function() s:Destroy() end)
end
local function sayTraining(text: string, dur: number)
	for _, p in Players:GetPlayers() do
		if p:GetAttribute("Zone") == "training" then say(p, text, dur) end
	end
end

-- ---------------------------------------------------------------- the Carls
-- a gold Carl is the cardboard man painted gold (light parts brighter, dark parts deeper)
local function gild(c: Color3): Color3
	local l = 0.3 * c.R + 0.59 * c.G + 0.11 * c.B
	return Color3.fromRGB(150, 98, 28):Lerp(Color3.fromRGB(255, 220, 120), math.clamp(l * 1.25, 0, 1))
end

local function makeCarl(e: Entry): any
	local spot = e.spot
	local feet = spot.Position
	local lv = spot.CFrame.LookVector
	local look = Vector3.new(lv.X, 0, lv.Z)
	look = if look.Magnitude > 0.01 then look.Unit else Vector3.zAxis
	local base = CFrame.lookAt(feet, feet - look) -- (+Z of this frame = the way he faces: the model's front)
	local m = Instance.new("Model")
	m.Name = if e.gold then "GoldCarl" else "Carl"
	local root = Instance.new("Part")
	root.Name = "HumanoidRootPart"; root.Size = Vector3.new(2, 2, 1); root.Transparency = 1
	root.Anchored = true; root.CanCollide = false; root.CanQuery = false; root.CanTouch = false
	root.CFrame = base + Vector3.new(0, Hitbox.ROOT_UP, 0)
	root.Parent = m
	m.PrimaryPart = root
	local l = lib()
	local tmpl = l and l:FindFirstChild("bc_cutout")
	local body: Model? = nil
	local rel = CFrame.identity
	if tmpl and tmpl:IsA("Model") then
		local b = tmpl:Clone()
		b.Name = "Body"
		for _, d in b:GetDescendants() do
			if d:IsA("BasePart") then
				d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
				if e.gold then d.Color = gild(d.Color) end
			end
		end
		local cf, sz = b:GetBoundingBox()
		rel = CFrame.new(0, sz.Y / 2, 0) * (cf:Inverse() * b:GetPivot()).Rotation
		b:PivotTo(base * CFrame.Angles(-1.45, 0, 0) * rel)
		b.Parent = m
		body = b
	end
	local hum = Instance.new("Humanoid")
	hum.RequiresNeck = false; hum.BreakJointsOnDeath = false
	hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	hum.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
	hum.MaxHealth = 100; hum.Health = 100
	hum.Parent = m
	m:SetAttribute("Dummy", true); m:SetAttribute("Base", base)
	if e.gold then m:SetAttribute("GoldCarl", e.gold) end
	m.Parent = dummyFolder()
	local f = Rules.newFighter("dummy", if e.gold then "Gold Carl" else "Cardboard Carl", m)
	Rules.spawn(f, os.clock())
	f.hp = HP
	Fight.byModel[m] = f
	table.insert(Fight.all, f)
	carls[f] = e
	if body then -- up from flat on his back
		local b = body
		task.spawn(function()
			local t0 = os.clock()
			while os.clock() - t0 < 0.3 and b.Parent and f.alive do
				local k = (os.clock() - t0) / 0.3
				b:PivotTo(base * CFrame.Angles(-1.45 * (1 - k) * (1 - k), 0, 0) * rel)
				RunService.Heartbeat:Wait()
			end
			if b.Parent and f.alive then b:PivotTo(base * rel) end
		end)
	end
	return f
end

-- off the fighter lists at once (nothing hits him twice, Fight never respawns him), then the cardboard tips over
local function fold(f: any)
	carls[f] = nil
	f.alive = false
	local i = table.find(Fight.all, f)
	if i then table.remove(Fight.all, i) end
	local m = f.ref :: Model?
	if not m then return end
	Fight.byModel[m] = nil
	local body = m:FindFirstChild("Body") :: Model?
	local base = m:GetAttribute("Base")
	task.spawn(function()
		if body and typeof(base) == "CFrame" then
			local b = base :: CFrame
			local rel = b:ToObjectSpace(body:GetPivot())
			local t0 = os.clock()
			while os.clock() - t0 < 0.22 and body.Parent do
				local k = (os.clock() - t0) / 0.22
				body:PivotTo(b * CFrame.Angles(-1.45 * k * k, 0, 0) * rel)
				RunService.Heartbeat:Wait()
			end
		end
		task.wait(0.6)
		m:Destroy()
	end)
end

local function goldStanding(i: number): boolean
	for _, e in carls do if e.gold == i then return true end end
	return false
end

-- every gold Carl who is down stands up again in his place
local function goldBack()
	local spots = lot and lot:FindFirstChild("GoldSpots")
	if not spots then return end
	for i = 1, 3 do
		local s = spots:FindFirstChild("Gold" .. i)
		if s and s:IsA("BasePart") and not goldStanding(i) then makeCarl({ spot = s, gold = i }) end
	end
end

-- ---------------------------------------------------------------- the panel and the door
local function setPips()
	local panel = lot and lot:FindFirstChild("Panel")
	if not panel then return end
	for _, d in panel:GetDescendants() do
		local n = d:GetAttribute("Pip")
		if d:IsA("BasePart") and type(n) == "number" then
			local lit = found[n] == true or state ~= "shut"
			d.Color = if lit then GOLD else PIP_OFF
			d.Material = if lit then Enum.Material.Neon else Enum.Material.SmoothPlastic
		end
	end
end

local shownText = ""
local function setTimer(text: string)
	if text == "" then text = "1:30" end -- (idle: the plate always reads LOCKED, three men, the clock's rule and a hint)
	if text == shownText then return end
	shownText = text
	local panel = lot and lot:FindFirstChild("Panel")
	local t = panel and panel:FindFirstChild("Timer")
	local g = t and t:FindFirstChild("Gui")
	local l = g and g:FindFirstChild("Text")
	if l and l:IsA("TextLabel") then l.Text = text end
end

local function setBeacons(on: boolean)
	local b = lot and lot:FindFirstChild("Beacons")
	if not b then return end
	for _, m in b:GetChildren() do
		m:SetAttribute("Spin", if on then 5 else 0)
		for _, d in m:GetDescendants() do
			if d:IsA("BasePart") and d:GetAttribute("Lens") then
				d.Material = if on then Enum.Material.Neon else Enum.Material.SmoothPlastic
				d.Color = if on then Color3.fromRGB(255, 170, 60) else Color3.fromRGB(150, 112, 62)
			elseif d:IsA("Light") then
				d.Enabled = on
			end
		end
	end
end

local passable: boolean? = nil
local function placeDoor()
	-- (the slats stay at their shut places here; whether they block follows how far up the door is)
	local up = u >= PASS_U
	if up == passable then return end
	passable = up
	for _, s in slats do
		s.p.CanCollide = s.solid and not up
		s.p.CanQuery = s.query and not up
	end
	local blk = lot and lot:FindFirstChild("DoorBlock") :: BasePart?
	if blk then blk.CanCollide = not up; blk.CanQuery = not up end
end
-- tell every screen to roll the door from where it is now to goal (0 shut, 1 up) over dur seconds
local function publish(goal: number, dur: number)
	local door = lot and lot:FindFirstChild("Door")
	if not door then return end
	door:SetAttribute("From", u); door:SetAttribute("Goal", goal); door:SetAttribute("Dur", dur)
	door:SetAttribute("Since", workspace:GetServerTimeNow())
end
local function goUp(dur: number)
	state = "opening"; moveT = dur
	publish(1, dur)
end
-- locked: the door jumps a hand's width and drops (every screen), it clatters, and LOCKED over the panel flashes
local function rattle()
	local door = lot and lot:FindFirstChild("Door")
	if door then door:SetAttribute("Rattle", workspace:GetServerTimeNow()) end
	sound("Rattle")
	local panel = lot and lot:FindFirstChild("Panel")
	local head = panel and panel:FindFirstChild("PanelHead")
	local g = head and head:FindFirstChild("Gui")
	local l = g and g:FindFirstChild("Line1")
	if l and l:IsA("TextLabel") then
		task.spawn(function()
			local was = l.TextColor3
			for _ = 1, 3 do
				l.TextColor3 = Color3.fromRGB(255, 92, 72); task.wait(0.14)
				l.TextColor3 = was; task.wait(0.12)
			end
		end)
	end
end
-- who is near the doorway, on the yard's side and on the lot's
local function nearDoor(): ({ Player }, { Player })
	local yard, back = {}, {}
	local dw = lot and lot:FindFirstChild("Doorway") :: BasePart?
	if not dw then return yard, back end
	for _, p in Players:GetPlayers() do
		local ch = p.Character
		local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		local hum = ch and ch:FindFirstChildOfClass("Humanoid")
		if root and hum and hum.Health > 0 then
			local rel = dw.CFrame:PointToObjectSpace(root.Position)
			local h = dw.Size / 2
			if math.abs(rel.X) <= h.X + 1 and math.abs(rel.Y) <= h.Y + 4 and math.abs(rel.Z) <= h.Z + NEAR then
				if root.Position.Z > dw.Position.Z then table.insert(yard, p) else table.insert(back, p) end
			end
		end
	end
	return yard, back
end

local function someoneIn(part: BasePart, grow: number): boolean
	for _, p in Players:GetPlayers() do
		local ch = p.Character
		local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		if root then
			local rel = part.CFrame:PointToObjectSpace(root.Position)
			local h = part.Size / 2
			if math.abs(rel.X) <= h.X + grow and math.abs(rel.Y) <= h.Y + grow and math.abs(rel.Z) <= h.Z + grow then return true end
		end
	end
	return false
end

local function count(): number
	local n = 0
	for i = 1, 3 do if found[i] then n += 1 end end
	return n
end

-- the egg is done: the slow reveal, up for OPEN_FOR (if someone already had it up, it just stays up that long)
local function open(by: Player?)
	if eggOpen then return end
	eggOpen = true
	setPips(); setBeacons(true); setTimer("OPEN")
	sayTraining("THE GARAGE IS OPEN", 2.2)
	if by then known[by] = true; greeted[by] = true end
	for p in finders do known[p] = true; greeted[p] = true end
	if state == "shut" or state == "closing" then goUp(MOVE_T); sound("Open")
	elseif state == "open" then openUntil = os.clock() + OPEN_FOR end
end

local function resetEgg()
	found = { false, false, false }
	firstAt = 0
	table.clear(finders)
	setPips()
	setTimer("")
end

local function goldDown(i: number, k: any, spot: BasePart?)
	if found[i] or eggOpen then return end
	found[i] = true
	if firstAt == 0 then firstAt = os.clock() end
	local n = count()
	setPips()
	sound("Ding")
	chime(spot)
	local p = if k and k.kind == "player" then k.ref :: Player else nil
	if p then
		finders[p] = true
		if n < 3 then -- (every gold hit says how long is left: the clock runs from the first)
			local left = math.max(0, WINDOW - (os.clock() - firstAt))
			say(p, ("GOLD %d OF 3 · %d:%02d"):format(n, math.floor(left / 60), math.floor(left % 60)), 1.8)
		end
	end
	if n == 3 then open(p) end
end

-- ---------------------------------------------------------------- the lot coming and going (v1 has none)
local function setup(l: Instance)
	lot = l
	table.clear(slats)
	local door = l:FindFirstChild("Door")
	if door then
		local lf, tp = door:GetAttribute("Lift"), door:GetAttribute("Top")
		lift = if type(lf) == "number" then lf else 20.6
		top = if type(tp) == "number" then tp else math.huge
		for _, d in door:GetDescendants() do
			local shut = d:GetAttribute("Shut")
			if d:IsA("BasePart") and typeof(shut) == "CFrame" then
				d.CFrame = shut; d.Transparency = 0
				table.insert(slats, { p = d, shut = shut, solid = d.CanCollide, query = d.CanQuery })
			end
		end
	end
	state, u, eggOpen, passable = "shut", 0, false, nil
	placeDoor()
	publish(0, 0)
	resetEgg()
	setBeacons(false)
	local targets = l:FindFirstChild("Targets")
	if targets then
		for _, s in targets:GetChildren() do if s:IsA("BasePart") then makeCarl({ spot = s }) end end
	end
	goldBack()
end

local function teardown()
	for f in carls do fold(f) end
	lot = nil
	table.clear(slats)
	for _, p in Players:GetPlayers() do if p:GetAttribute("OnLot") then p:SetAttribute("OnLot", nil) end end
end

Fight.onKill(function(info: any)
	local v = info.v
	local e = carls[v]
	if not e then return end
	fold(v)
	if e.gold then
		goldDown(e.gold, info.k, e.spot)
	else
		task.delay(BACK_UP, function()
			if lot and e.spot.Parent then makeCarl(e) end
		end)
	end
end)

local acc, look = 0, 0
RunService.Heartbeat:Connect(function(dt: number)
	local now = os.clock()
	look += dt
	if look > 3 then
		look = 0
		local tg = workspace:FindFirstChild("Map") and workspace.Map:FindFirstChild("Hub") and workspace.Map.Hub:FindFirstChild("TrainingGround")
		local l = tg and tg:FindFirstChild("Lot")
		if l ~= lot then
			if lot then teardown() end
			if l then setup(l) end
		end
	end
	if not lot then return end
	-- the door
	if state == "opening" then
		u = math.min(1, u + dt / moveT)
		placeDoor()
		if u >= 1 then state = "open"; openUntil = if eggOpen then now + OPEN_FOR else now end
	elseif state == "closing" then
		local dw = lot:FindFirstChild("Doorway") :: BasePart?
		if dw and someoneIn(dw, 0.5) then
			goUp(MOVE_FAST); sound("Open") -- (the safety eye: back up)
		else
			u = math.max(0, u - dt / CLOSE_T)
			placeDoor()
			if u <= 0 then
				state = "shut"
				setBeacons(false)
				setPips()
				if eggOpen then
					eggOpen = false
					resetEgg()
					task.delay(GOLD_BACK, function() if lot and state == "shut" then goldBack() end end)
				elseif firstAt == 0 then
					setTimer("")
				end
			end
		end
	end
	acc += dt
	if acc < 0.2 then return end
	acc = 0
	-- who is at the door: from the lot it always lets you back in; on the yard's side it rolls up for anyone who has
	-- opened it before, and for everyone else it rattles (LOCKED)
	local yard, back = nearDoor()
	local let: Player? = nil
	for _, p in yard do if known[p] then let = p; break end end
	if #back > 0 or let then
		holdUntil = now + HOLD
		if state == "shut" or state == "closing" then
			if let and not greeted[let] then greeted[let] = true end
			goUp(MOVE_FAST)
			sound("Open")
			setBeacons(true); setPips()
			if not eggOpen then setTimer("OPEN") end
		end
	elseif #yard > 0 and state == "shut" and now >= rattleAt then
		rattleAt = now + 2.4
		rattle()
	end
	if state == "open" then
		local left = math.ceil(openUntil - now)
		if eggOpen then setTimer(if left > 0 then ("OPEN · %d"):format(left) else "OPEN") end
		if now >= openUntil and now >= holdUntil then
			local dw = lot:FindFirstChild("Doorway") :: BasePart?
			if dw and someoneIn(dw, 0.5) then
				holdUntil = now + 1
			else
				state = "closing"; publish(0, CLOSE_T); sound("Close")
				if eggOpen then setTimer("") end
			end
		end
	end
	-- the hunt's clock runs whatever the door is doing (it shows while the door is down)
	if not eggOpen and firstAt > 0 then
		local left = WINDOW - (now - firstAt)
		if left <= 0 then
			for p in finders do say(p, "TOO SLOW. THE GOLD ONES ARE BACK", 2) end
			sound("Buzz")
			resetEgg()
			goldBack()
		elseif state == "shut" then
			setTimer(("%d:%02d"):format(math.floor(left / 60), math.floor(left % 60)))
		end
	end
	-- who is on the lot
	local area = lot:FindFirstChild("Area") :: BasePart?
	for _, p in Players:GetPlayers() do
		local ch = p.Character
		local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		local on = false
		if area and root then
			local rel = area.CFrame:PointToObjectSpace(root.Position)
			local h = area.Size / 2
			on = math.abs(rel.X) <= h.X and math.abs(rel.Y) <= h.Y and math.abs(rel.Z) <= h.Z
		end
		if (p:GetAttribute("OnLot") == true) ~= on then p:SetAttribute("OnLot", if on then true else nil) end
	end
end)

-- ---------------------------------------------------------------- Studio play tests only
if RunService:IsStudio() then
	local bf = Instance.new("BindableFunction")
	bf.Name = "LotTest"
	bf.OnInvoke = function(op: string, a: any): any
		if op == "state" then
			return { state = state, u = u, egg = eggOpen, found = table.clone(found), firstAt = firstAt, lot = lot ~= nil, slats = #slats, timer = shownText }
		elseif op == "gold" then
			for f, e in carls do
				if e.gold == a then
					local p = Players:GetPlayers()[1]
					local k = p and Fight.byPlayer[p]
					local info = Rules.kill(f, k, "redline", os.clock())
					Fight.died(info, nil)
					return true
				end
			end
			return false
		elseif op == "lotcarl" then -- put one lot Carl down (he stands up again after BACK_UP)
			for f, e in carls do
				if not e.gold then
					local info = Rules.kill(f, nil, "redline", os.clock())
					Fight.died(info, nil)
					return e.spot.Position
				end
			end
			return nil
		elseif op == "open" then open(Players:GetPlayers()[1]); return true
		elseif op == "shut" then if state == "open" then openUntil = 0; holdUntil = 0 end; return true
		elseif op == "know" then local p = Players:GetPlayers()[1]; if p then known[p] = a ~= false end; return true
		elseif op == "carls" then
			local out = {}
			for f, e in carls do
				local r = Fight.root(f)
				table.insert(out, { name = f.name, gold = e.gold, alive = f.alive, pos = if r then r.Position else nil })
			end
			return out
		end
		return nil
	end
	bf.Parent = ServerStorage
end
