--!strict
-- CARDBOARD CARL'S: the target lane in the training hall. stand on CHILL, NORMAL or SWEATY and 25 cardboard men pop
-- up one at a time down the lane; put each one down before he folds himself away. the board keeps count.
-- a Carl is a real fighter of kind "dummy" (so every weapon, hit check, hit marker and DINK works on him exactly as
-- on the dummies) with a cardboard body from ServerStorage.JankfireMeshes.bc_cutout. he never fights back.
-- since 16 Nov (the owner: "can we make it so every player that starts the session sees their own targets that way
-- multiple people can use the shooting range?") every runner has his own Carls: any number of people can stand on one
-- plate and each gets his own 25. a Carl carries the attribute Owner (the runner's UserId) and f.onlyFor (the runner):
-- only his runner can hurt him (Fight.hurt), and every other client takes him out of its world (TrainingDoors.client),
-- so you never see, aim at, outline or bleed on somebody else's cardboard. the server counts each run on its own, and a
-- kill only counts from the runner, at least 0.12 s after his Carl started up (nobody reacts faster: the board stays
-- honest). a run stops early if the runner leaves the hall or dies. while you run, the dummy yard's shooters leave you
-- alone (the attribute RangeRun on the player).
-- the lanes are data in the map: Hub.TrainingGround.Range.Plates (parts Easy / Medium / Hard), .Spots (where a Carl
-- stands, facing his plate; attribute Lane = the plate's name), .Board (a part whose Gui has RowEasy, RowMedium,
-- RowHard and Line) and .BestBoard (Gui.Best: the best run per lane today)
-- in Studio only, ServerStorage.RangeHook (a BindableFunction) runs a ghost runner beside you for two-player tests:
-- ("ghost", lane | "off") starts or ends one, ("ghosthit") puts his Carl down, ("hit", userId) puts yours down as if
-- you shot him, ("cross", userId) has you shoot the ghost's Carl (it must do nothing), ("hold", on) keeps every Carl
-- up, ("state") lists the runs and the board's rows
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local CalloutR = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Callout") :: RemoteEvent

type Fighter = Rules.Fighter
local RangeTest = {}
-- (Quests.luau: a finished run's score, for the range quests) fn(player, plate "Easy"|"Medium"|"Hard", score, total)
local runHooks: { (Player, string, number, number) -> () } = {}
function RangeTest.onRun(fn: (Player, string, number, number) -> ()) table.insert(runHooks, fn) end
local TOTAL = 25
local HP = 30 -- three rifle rounds, two to the head, one katana swing
local QUICKEST = 0.12 -- a kill sooner than this after a Carl starts up doesn't count
local IDLE = "stand on a plate to start · 25 targets each"
-- up = seconds a Carl stays up, gap = seconds until the next one
local LEVELS: { [string]: { up: number, gap: number, name: string } } = {
	Easy = { up = 3.2, gap = 0.55, name = "CHILL" },
	Medium = { up = 1.9, gap = 0.4, name = "NORMAL" },
	Hard = { up = 1.1, gap = 0.25, name = "SWEATY" },
}
local LANES = { "Easy", "Medium", "Hard" }
-- p = the runner (nil for Studio's ghost), uid = his UserId (-1 for the ghost), who = his name on the board
type Run = {
	p: Player?, uid: number, who: string, level: string, score: number, left: number,
	cur: Fighter?, curAt: number, curUntil: number, nextAt: number, lastSpot: BasePart?,
}
local runs: { Run } = {}
local best: { [string]: number } = {}       -- the best run per level since the server started
local mustStepOff: { [Player]: boolean } = {} -- after a run you step off the plates before the next one
local Fight: any
local range: Instance? = nil
local idleAt = 0
local holdUp = false -- (Studio's hook: every Carl stays up)

local function runOf(p: Player): Run?
	for _, r in runs do if r.p == p then return r end end
	return nil
end

local function setText(name: string, text: string)
	local b = range and range:FindFirstChild("Board")
	local g = b and b:FindFirstChild("Gui")
	local l = g and g:FindFirstChild(name)
	if l and l:IsA("TextLabel") and l.Text ~= text then l.Text = text end
end
local function short(s: string): string return if #s > 14 then s:sub(1, 13) .. "…" else s end
local function show(line: string?)
	for _, lane in LANES do
		local on = {}
		for _, r in runs do if r.level == lane then table.insert(on, r) end end
		local t = "free"
		if #on == 1 then
			local r = on[1]
			t = ("%s · %02d down · %02d left"):format(short(r.who), r.score, r.left)
		elseif #on > 1 then
			local bits = {}
			for i, r in on do
				if i > 4 then table.insert(bits, ("+%d"):format(#on - 4)); break end
				table.insert(bits, ("%s %02d"):format(short(r.who), r.score))
			end
			t = table.concat(bits, "  ·  ")
		end
		setText("Row" .. lane, t)
	end
	if line then setText("Line", line) end
	local bb = range and range:FindFirstChild("BestBoard")
	local g = bb and bb:FindFirstChild("Gui")
	local l = g and g:FindFirstChild("Best")
	if l and l:IsA("TextLabel") then
		local function b(k: string): string return if best[k] then tostring(best[k]) else "—" end
		local t = ("BEST TODAY\nCHILL %s   NORMAL %s   SWEATY %s"):format(b("Easy"), b("Medium"), b("Hard"))
		if l.Text ~= t then l.Text = t end
	end
end
local function sound(name: string)
	local b = range and range:FindFirstChild("Board")
	local s = b and b:FindFirstChild(name)
	if s and s:IsA("Sound") then s:Play() end
end

-- fold a Carl away: off the fighter lists at once (nothing can hit him twice, and he never respawns), then the
-- cardboard tips over backwards (shot) or sinks into the floor (too slow) and goes
local function remove(f: Fighter, shot: boolean)
	local m = f.ref :: Model?
	f.alive = false
	local i = table.find(Fight.all, f)
	if i then table.remove(Fight.all, i) end
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
				local u = (os.clock() - t0) / 0.22
				if shot then body:PivotTo(b * CFrame.Angles(-1.45 * u * u, 0, 0) * rel)
				else body:PivotTo(b * CFrame.new(0, -7.2 * u, 0) * rel) end
				RunService.Heartbeat:Wait()
			end
		end
		task.wait(if shot then 0.5 else 0)
		m:Destroy()
	end)
end

-- the next Carl: a random spot on the runner's lane (never the same one twice running), up from flat on his back.
-- he is the runner's alone: Owner on the model (every other client takes him out of its world), onlyFor on the fighter
-- (nobody else can hurt him)
local function pop(r: Run)
	local spots = range and range:FindFirstChild("Spots")
	if not spots then return end
	local list = {}
	for _, s in spots:GetChildren() do
		if s:IsA("BasePart") and s ~= r.lastSpot and (s:GetAttribute("Lane") == nil or s:GetAttribute("Lane") == r.level) then table.insert(list, s) end
	end
	if #list == 0 then return end
	local spot = list[math.random(#list)] :: BasePart
	r.lastSpot = spot
	local feet = spot.Position
	local lv = spot.CFrame.LookVector
	local look = Vector3.new(lv.X, 0, lv.Z).Unit
	local base = CFrame.lookAt(feet, feet - look) -- (+Z of this frame = toward the shooters: the model's front)
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
	local body: Model? = nil
	local rel = CFrame.identity
	if tmpl and tmpl:IsA("Model") then
		local b = tmpl:Clone()
		b.Name = "Body"
		for _, d in b:GetDescendants() do
			if d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false end
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
	m:SetAttribute("Dummy", true); m:SetAttribute("Base", base); m:SetAttribute("Owner", r.uid)
	m:SetAttribute("HitNeck", Hitbox.CUTOUT.neck); m:SetAttribute("HitTop", Hitbox.CUTOUT.top) -- (his painted head is the head box: Hitbox.profile)
	m.Parent = workspace:FindFirstChild("Dummies") or workspace
	local f = Rules.newFighter("dummy", "Cardboard Carl", m)
	f.onlyFor = if r.p then r.p else "ghost"
	Rules.spawn(f, os.clock())
	f.hp = HP
	Fight.byModel[m] = f
	table.insert(Fight.all, f)
	r.cur, r.curAt, r.curUntil = f, os.clock(), os.clock() + LEVELS[r.level].up
	if body then
		local b = body
		task.spawn(function()
			local t0 = os.clock()
			while os.clock() - t0 < 0.14 and b.Parent and f.alive do
				local u = (os.clock() - t0) / 0.14
				b:PivotTo(base * CFrame.Angles(-1.45 * (1 - u), 0, 0) * rel)
				RunService.Heartbeat:Wait()
			end
			if b.Parent and f.alive then b:PivotTo(base * rel) end
		end)
	end
end

local function finish(r: Run, abandoned: boolean)
	if r.cur then remove(r.cur, false); r.cur = nil end
	local i = table.find(runs, r)
	if i then table.remove(runs, i) end
	idleAt = os.clock() + 8
	local p = r.p
	if p then
		mustStepOff[p] = true
		if p.Parent then p:SetAttribute("RangeRun", nil) end
	end
	if abandoned then
		show(("%s left %s"):format(r.who, LEVELS[r.level].name))
		return
	end
	local lv = LEVELS[r.level]
	if not best[r.level] or r.score > best[r.level] then best[r.level] = r.score end
	show(("%s · %d / %d on %s · best %d"):format(r.who, r.score, TOTAL, lv.name, best[r.level]))
	if p and p.Parent then CalloutR:FireClient(p, ("%d / %d"):format(r.score, TOTAL), 3) end
	if p then for _, fn in runHooks do task.spawn(fn, p, r.level, r.score, TOTAL) end end
	sound("End")
end

-- a Carl down. it counts only if his own runner did it (the ghost's die with nobody behind them) and not
-- impossibly soon after he started up; otherwise he just folds away, one fewer to go
local function onKill(info: any)
	local r: Run? = nil
	for _, x in runs do if x.cur == info.v then r = x end end
	if not r or not r.cur then return end
	local f = r.cur :: Fighter
	local k = info.k
	local fair = if r.p then (k ~= nil and k.ref == r.p) else k == nil
	if os.clock() - r.curAt < QUICKEST then fair = false end
	if fair then r.score += 1 end
	r.left -= 1
	r.cur = nil; r.nextAt = os.clock() + LEVELS[r.level].gap
	remove(f, true)
	show(nil)
end

-- which plate is this spot standing on (feet on or just above it)
local function onPlate(pos: Vector3): string?
	local plates = range and range:FindFirstChild("Plates")
	if not plates then return nil end
	for _, p in plates:GetChildren() do
		if p:IsA("BasePart") then
			local rel = p.CFrame:PointToObjectSpace(pos)
			if math.abs(rel.X) <= p.Size.X / 2 and math.abs(rel.Z) <= p.Size.Z / 2 and rel.Y > 0 and rel.Y < 7 then return p.Name end
		end
	end
	return nil
end

local function start(p: Player?, uid: number, who: string, plate: string)
	local now = os.clock()
	table.insert(runs, { p = p, uid = uid, who = who, level = plate, score = 0, left = TOTAL, cur = nil, curAt = 0, curUntil = 0, nextAt = now + 1.2, lastSpot = nil })
	idleAt = 0
	if p then
		p:SetAttribute("RangeRun", true) -- the dummy yard's shooters leave a runner alone (Dummies.luau)
		CalloutR:FireClient(p, "CARDBOARD CARL'S · " .. LEVELS[plate].name, 1.4)
	end
	show(("%s · %s"):format(who, LEVELS[plate].name))
	sound("Start")
end

local acc = 0
local function tick(dt: number)
	acc += dt
	if acc < 0.05 then return end
	acc = 0
	local now = os.clock()
	for _, r in table.clone(runs) do
		local p = r.p
		if p then
			local f = Fight.byPlayer[p]
			if not p.Parent or not f or not f.alive or p:GetAttribute("Zone") ~= "training" then finish(r, true); continue end
		end
		if r.cur then
			if holdUp then r.curUntil = now + LEVELS[r.level].up end
			if now >= r.curUntil then -- too slow: he folds himself away, one fewer to go
				local c = r.cur :: Fighter
				r.cur = nil; r.left -= 1; r.nextAt = now + LEVELS[r.level].gap
				remove(c, false)
				show(nil)
			end
		elseif r.left <= 0 then finish(r, false)
		elseif now >= r.nextAt then pop(r) end
	end
	if idleAt > 0 and now >= idleAt and #runs == 0 then idleAt = 0; show(IDLE) end
	for _, p in Players:GetPlayers() do
		local f = Fight.byPlayer[p]
		local root = if f and f.alive then Fight.root(f) else nil
		if not root or p:GetAttribute("Zone") ~= "training" then mustStepOff[p] = nil; continue end
		if runOf(p) then continue end
		local plate = onPlate(root.Position)
		if not plate then
			mustStepOff[p] = nil
		elseif not mustStepOff[p] and LEVELS[plate] then
			start(p, p.UserId, p.DisplayName, plate)
		end
	end
end

-- Studio only: a ghost runner beside you, for testing two people on one lane with one Play test
local function hook()
	if not RunService:IsStudio() or ServerStorage:FindFirstChild("RangeHook") then return end
	local h = Instance.new("BindableFunction")
	h.Name = "RangeHook"
	local function ghost(): Run?
		for _, r in runs do if r.p == nil then return r end end
		return nil
	end
	h.OnInvoke = function(op: string, a: any): any
		if op == "ghost" then
			local g = ghost()
			if g then finish(g, true) end
			if a ~= "off" then start(nil, -1, "Ghost", if LEVELS[a] then a else "Medium") end
			return "ghost " .. tostring(a)
		elseif op == "hold" then
			holdUp = a == true
			return "hold " .. tostring(holdUp)
		elseif op == "ghosthit" then
			local g = ghost()
			if not g or not g.cur then return "no ghost Carl up" end
			local c = g.cur :: Fighter
			if os.clock() - g.curAt < QUICKEST then task.wait(QUICKEST) end
			c.hp = 0
			Fight.died(Rules.kill(c, nil, "redline", os.clock()), Vector3.new(0, 20, 0))
			return ("ghost %d down, %d left"):format(g.score, g.left)
		elseif op == "hit" or op == "cross" then
			local p = Players:GetPlayerByUserId(tonumber(a) or 0)
			local f = if p then Fight.byPlayer[p] else nil
			if not p or not f then return "no fighter for " .. tostring(a) end
			local r, g = runOf(p), ghost()
			local target = if op == "hit" then (if r then r.cur else nil) else (if g then g.cur else nil)
			if not target then return "no Carl up" end
			local at = if op == "hit" and r then r.curAt elseif g then g.curAt else 0
			if os.clock() - at < QUICKEST then task.wait(QUICKEST) end
			local done = Fight.hurt(target, 999, f, "redline", false)
			return ("%s: %s dealt, yours %s, ghost %s"):format(op, tostring(done), if r then tostring(r.score) else "-", if g then tostring(g.score) else "-")
		elseif op == "state" then
			local out = {}
			for _, r in runs do
				table.insert(out, ("%s on %s: %d down, %d left, Carl %s (owner %d)"):format(r.who, r.level, r.score, r.left, if r.cur then "up" else "-", r.uid))
			end
			local b = range and range:FindFirstChild("Board")
			local g = b and b:FindFirstChild("Gui")
			for _, lane in LANES do
				local l = g and g:FindFirstChild("Row" .. lane)
				if l and l:IsA("TextLabel") then table.insert(out, lane .. " row: " .. l.Text) end
			end
			return table.concat(out, "\n")
		end
		return "ops: ghost <lane|off>, hold <bool>, ghosthit, hit <userId>, cross <userId>, state"
	end
	h.Parent = ServerStorage
end

function RangeTest.init(fight: any)
	Fight = fight
	local hub = workspace:WaitForChild("Map"):WaitForChild("Hub")
	local tg = hub:FindFirstChild("TrainingGround")
	range = tg and tg:FindFirstChild("Range")
	if not range then return end
	-- the lane's own sounds play from the board, for everyone in the hall
	local board = range:FindFirstChild("Board")
	local lib = ReplicatedStorage:FindFirstChild("JankfireSounds")
	if board and lib then
		for name, src in { Start = "round_start", End = "round_end" } do
			local s = lib:FindFirstChild(src)
			if s and s:IsA("Sound") and not board:FindFirstChild(name) then
				local c = s:Clone()
				c.Name = name; c.RollOffMinDistance = 30; c.RollOffMaxDistance = 400
				c.Parent = board
			end
		end
	end
	show(IDLE)
	Fight.onKill(onKill)
	RunService.Heartbeat:Connect(tick)
	Players.PlayerRemoving:Connect(function(p: Player) mustStepOff[p] = nil end)
	hook()
end

return RangeTest
