--!strict
-- THE PARKOUR ISLAND's rules (20 Nov 2026; studio-tools/ParkourIsland.luau builds it: Map.Hub.Parkour). Off the start
-- deck the clock runs (Parkour remote "go"); each checkpoint you reach is your restart and shows a split; a fall (under
-- the folder's FallY) puts you back on your last checkpoint (or the start) with the clock still running; the finish
-- stops it ("done": your time, your best today, the best of the server today). Back on the start deck the clock resets.
-- The start deck's board shows today's five best. Nothing is saved: today's bests live with the server.
-- Studio only: ServerStorage.JankParkourTest ("state"), ("cp", n, userId?) puts you on checkpoint n, ("finish", userId?)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local CalloutR = Remotes:WaitForChild("Callout") :: RemoteEvent
local PkR = Remotes:FindFirstChild("Parkour") :: RemoteEvent?
if not PkR then
	local r = Instance.new("RemoteEvent")
	r.Name = "Parkour"
	r.Parent = Remotes
	PkR = r
end
local R = PkR :: RemoteEvent

type Run = { t0: number?, cp: number, inStart: boolean, splits: { number } }
local runs: { [Player]: Run } = {}
local bestOf: { [Player]: number } = {}
local board: { { name: string, t: number } } = {} -- today's best, one row per player
local pk: Instance? = nil

local function inside(part: BasePart, pos: Vector3): boolean
	local rel = part.CFrame:PointToObjectSpace(pos)
	local h = part.Size / 2
	return math.abs(rel.X) <= h.X and math.abs(rel.Y) <= h.Y and math.abs(rel.Z) <= h.Z
end
local function game_(): Instance? return pk and pk:FindFirstChild("Game") end
local function zone(name: string): BasePart?
	local g = game_()
	local p = g and g:FindFirstChild(name)
	return if p and p:IsA("BasePart") then p else nil
end
local function paintBoard()
	local sc = pk and pk:FindFirstChild("Scenery")
	local b = sc and sc:FindFirstChild("Board")
	local g = b and b:FindFirstChild("Gui")
	local l = g and g:FindFirstChild("Text") :: TextLabel?
	if not l then return end
	local lines = { "PARKOUR" }
	for i = 1, math.min(5, #board) do table.insert(lines, ("%d  %s  %.1f S"):format(i, board[i].name, board[i].t)) end
	l.Text = table.concat(lines, "\n")
end
local function put(p: Player, part: BasePart)
	local ch = p.Character
	if not ch then return end
	p:SetAttribute("TeleportT", os.clock()) -- (the anti-cheat's teleport check starts afresh)
	local root = ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if root then root.AssemblyLinearVelocity = Vector3.zero end
	local at = part.Position + Vector3.new(0, -part.Size.Y / 2 + 3.2, 0)
	local lv = part.CFrame.LookVector
	ch:PivotTo(CFrame.lookAt(at, at + Vector3.new(lv.X, 0, lv.Z)))
end
local function cpPart(n: number): BasePart? return if n <= 0 then zone("Start") else zone("CP" .. n) end
local function finish(p: Player, r: Run)
	local t = os.clock() - (r.t0 :: number)
	r.t0 = nil
	local was = bestOf[p]
	local isBest = was == nil or t < was
	if isBest then bestOf[p] = t end
	-- today's board: one row per player, their best
	local row = nil
	for _, b in board do if b.name == p.DisplayName then row = b end end
	if not row then table.insert(board, { name = p.DisplayName, t = t })
	elseif t < row.t then row.t = t end
	table.sort(board, function(a, b) return a.t < b.t end)
	paintBoard()
	R:FireClient(p, "done", { time = t, best = bestOf[p], newBest = isBest, top = board[1] and board[1].t })
end

local acc, lookAt = 0, 0
RunService.Heartbeat:Connect(function(dt: number)
	acc += dt
	if acc < 0.1 then return end
	acc = 0
	local now = os.clock()
	if now - lookAt > 3 then
		lookAt = now
		local hub = workspace:FindFirstChild("Map") and workspace.Map:FindFirstChild("Hub")
		pk = hub and hub:FindFirstChild("Parkour")
	end
	if not pk then return end
	local fallY = pk:GetAttribute("FallY")
	local nCp = pk:GetAttribute("Checkpoints")
	local zp = (workspace.Map.Hub :: Instance):FindFirstChild("ParkourZone") :: BasePart?
	local start, fin = zone("Start"), zone("Finish")
	for _, p in Players:GetPlayers() do
		local ch = p.Character
		local hum = ch and ch:FindFirstChildOfClass("Humanoid")
		local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		local on = zp and root and hum and hum.Health > 0 and inside(zp, root.Position)
		local r = runs[p]
		if not on then
			if r then
				runs[p] = nil
				R:FireClient(p, "off")
			end
			continue
		end
		local pos = (root :: BasePart).Position
		if not r then
			r = { t0 = nil, cp = 0, inStart = true, splits = {} }
			runs[p] = r
			R:FireClient(p, "on", { best = bestOf[p] })
		end
		local run = r :: Run
		-- a fall: back on the last checkpoint
		if type(fallY) == "number" and pos.Y < fallY then
			local back = cpPart(run.cp)
			if back then put(p, back) end
			CalloutR:FireClient(p, if run.cp > 0 then "CHECKPOINT " .. run.cp else "AGAIN", 0.8)
			continue
		end
		-- the start deck: the clock is ready; off it, it runs
		local nowIn = start ~= nil and inside(start, pos)
		if nowIn and not run.inStart then
			run.t0, run.cp, run.splits = nil, 0, {}
			R:FireClient(p, "ready", { best = bestOf[p] })
		elseif not nowIn and run.inStart then
			run.t0 = now
			R:FireClient(p, "go", {})
		end
		run.inStart = nowIn
		if run.t0 then
			-- checkpoints, in any order past your last one
			if type(nCp) == "number" then
				for i = run.cp + 1, nCp do
					local c = zone("CP" .. i)
					if c and inside(c, pos) then
						run.cp = i
						local split = now - run.t0
						table.insert(run.splits, split)
						R:FireClient(p, "cp", { n = i, of = nCp, split = split })
						break
					end
				end
			end
			if fin and inside(fin, pos) then finish(p, run) end
		end
	end
end)

Players.PlayerRemoving:Connect(function(p: Player) runs[p] = nil; bestOf[p] = nil end)

if RunService:IsStudio() then
	local bf = Instance.new("BindableFunction")
	bf.Name = "JankParkourTest"
	local function who(uid: any): Player? return if type(uid) == "number" then Players:GetPlayerByUserId(uid) else Players:GetPlayers()[1] end
	bf.OnInvoke = function(op: string, a: any, b: any): any
		if op == "cp" then
			local p = who(b)
			local c = cpPart(a)
			if p and c then put(p, c); return "on " .. c.Name end
			return "no player or checkpoint"
		elseif op == "finish" then
			local p = who(a)
			local f = zone("Finish")
			if p and f then put(p, f); return "on the finish" end
			return "no finish"
		end
		local out = {}
		for p, r in runs do out[p.Name] = { running = r.t0 ~= nil, cp = r.cp, splits = r.splits, best = bestOf[p] } end
		return { runs = out, board = board, built = pk ~= nil }
	end
	bf.Parent = game:GetService("ServerStorage")
end
