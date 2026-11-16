--!strict
-- CARDBOARD CARL'S: the target lane in the training hall. stand on CHILL, NORMAL or SWEATY and 25 cardboard men pop
-- up one at a time down the lane; put each one down before he folds himself away. the board keeps count.
-- a Carl is a real fighter of kind "dummy" (so every weapon, hit check, hit marker and DINK works on him exactly as
-- on the dummies) with a cardboard body from ServerStorage.JankfireMeshes.bc_cutout. he never fights back.
-- since 16 Nov (the owner: "keep in mind there will be multiple people in these hubs") the lane is three lanes, one per
-- plate, and each has its own run at once: a Carl pops only on his lane's spots. a run stops early if the runner leaves
-- the hall or dies. while you run, the dummy yard's shooters leave you alone (the attribute RangeRun on the player).
-- the lanes are data in the map: Hub.TrainingGround.Range.Plates (parts Easy / Medium / Hard), .Spots (where a Carl
-- stands, facing his plate; attribute Lane = the plate's name), .Board (a part whose Gui has RowEasy, RowMedium,
-- RowHard and Line) and .BestBoard (Gui.Best: the best run per lane today)
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
local TOTAL = 25
local HP = 30 -- three rifle rounds, two to the head, one katana swing
local IDLE = "stand on a plate. 25 cardboard men. he won't shoot back."
-- up = seconds a Carl stays up, gap = seconds until the next one
local LEVELS: { [string]: { up: number, gap: number, name: string } } = {
	Easy = { up = 3.2, gap = 0.55, name = "CHILL" },
	Medium = { up = 1.9, gap = 0.4, name = "NORMAL" },
	Hard = { up = 1.1, gap = 0.25, name = "SWEATY" },
}
type Run = { p: Player, level: string, score: number, left: number, cur: Fighter?, curUntil: number, nextAt: number, lastSpot: BasePart? }
local runs: { [string]: Run } = {}          -- by plate (lane)
local best: { [string]: number } = {}       -- the best run per level since the server started
local mustStepOff: { [Player]: boolean } = {} -- after a run you step off the plates before the next one
local Fight: any
local range: Instance? = nil
local idleAt = 0
local NAMES = { Easy = "CHILL", Medium = "NORMAL", Hard = "SWEATY" }

local function setText(name: string, text: string)
	local b = range and range:FindFirstChild("Board")
	local g = b and b:FindFirstChild("Gui")
	local l = g and g:FindFirstChild(name)
	if l and l:IsA("TextLabel") and l.Text ~= text then l.Text = text end
end
local function show(line: string?)
	for lane in LEVELS do
		local r = runs[lane]
		setText("Row" .. lane, if r then ("%s · %02d down · %02d left"):format(r.p.DisplayName, r.score, r.left) else "free")
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

-- the next Carl: a random spot (never the same one twice running), up from flat on his back
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
	m:SetAttribute("Dummy", true); m:SetAttribute("Base", base)
	m.Parent = workspace:FindFirstChild("Dummies") or workspace
	local f = Rules.newFighter("dummy", "Cardboard Carl", m)
	Rules.spawn(f, os.clock())
	f.hp = HP
	Fight.byModel[m] = f
	table.insert(Fight.all, f)
	r.cur, r.curUntil = f, os.clock() + LEVELS[r.level].up
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
	runs[r.level] = nil
	idleAt = os.clock() + 8
	mustStepOff[r.p] = true
	if r.p.Parent then r.p:SetAttribute("RangeRun", nil) end
	if abandoned then
		show(("%s left %s. he saw that."):format(r.p.DisplayName, NAMES[r.level]))
		return
	end
	local lv = LEVELS[r.level]
	if not best[r.level] or r.score > best[r.level] then best[r.level] = r.score end
	local verdict = if r.score >= TOTAL then "FLAWLESS. THE CARDBOARD FEARS YOU"
		elseif r.score >= 20 then "CARL IS IMPRESSED"
		elseif r.score >= 12 then "CARL HAS SEEN BETTER"
		else "CARL IS LAUGHING. HE'S CARDBOARD"
	show(("%s · %d / %d on %s · best %d"):format(r.p.DisplayName, r.score, TOTAL, lv.name, best[r.level]))
	if r.p.Parent then CalloutR:FireClient(r.p, ("%d / %d · %s"):format(r.score, TOTAL, verdict), 3) end
	sound("End")
end

local function onKill(info: any)
	local r: Run? = nil
	for _, x in runs do if x.cur == info.v then r = x end end
	if not r or not r.cur then return end
	local f = r.cur :: Fighter
	r.score += 1; r.left -= 1
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

local acc = 0
local function tick(dt: number)
	acc += dt
	if acc < 0.05 then return end
	acc = 0
	local now = os.clock()
	for _, r in runs do
		local f = Fight.byPlayer[r.p]
		if not r.p.Parent or not f or not f.alive or r.p:GetAttribute("Zone") ~= "training" then finish(r, true); continue end
		if r.cur then
			if now >= r.curUntil then -- too slow: he folds himself away, one fewer to go
				local c = r.cur :: Fighter
				r.cur = nil; r.left -= 1; r.nextAt = now + LEVELS[r.level].gap
				remove(c, false)
				show(nil)
			end
		elseif r.left <= 0 then finish(r, false)
		elseif now >= r.nextAt then pop(r) end
	end
	if idleAt > 0 and now >= idleAt and next(runs) == nil then idleAt = 0; show(IDLE) end
	for _, p in Players:GetPlayers() do
		local f = Fight.byPlayer[p]
		local root = if f and f.alive then Fight.root(f) else nil
		if not root or p:GetAttribute("Zone") ~= "training" then mustStepOff[p] = nil; continue end
		local running = false
		for _, r in runs do if r.p == p then running = true end end
		if running then continue end
		local plate = onPlate(root.Position)
		if not plate then
			mustStepOff[p] = nil
		elseif not mustStepOff[p] and LEVELS[plate] and not runs[plate] then
			runs[plate] = { p = p, level = plate, score = 0, left = TOTAL, cur = nil, curUntil = 0, nextAt = now + 1.2, lastSpot = nil }
			idleAt = 0
			p:SetAttribute("RangeRun", true) -- the dummy yard's shooters leave a runner alone (Dummies.luau)
			show(("%s · %s · 25 cardboard men incoming"):format(p.DisplayName, LEVELS[plate].name))
			CalloutR:FireClient(p, "CARDBOARD CARL'S · " .. LEVELS[plate].name, 1.4)
			sound("Start")
		end
	end
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
end

return RangeTest
