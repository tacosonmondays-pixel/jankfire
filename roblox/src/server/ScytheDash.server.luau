--!strict
-- the Scythe's dash (the owner, 18 Nov 2026: "Bring scythe in as a weapon, balance it especially its dash"; WEAPONS.md
-- "Scythe"). right click with the scythe out: the server checks it (yours, out, alive, not stunned or mid-swing, one
-- charge on its cooldown), finds the path (flat along your look, dash.dist studs, stopped short of a wall), hands it to
-- your client to run (DashV / DashUntil on you; ACGrace so the anti-cheat lets the burst through) and cuts the first
-- enemy within dash.width of that path: dash.dmg and a shove along it. a katana guard facing the dash parries it: no
-- damage, you're staggered instead. no invulnerability; after it, dash.recover s with no swing, guard or dash
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Fight = require(script.Parent:WaitForChild("Fight"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local FxR = Remotes:WaitForChild("Fx") :: RemoteEvent
local CalloutR = Remotes:WaitForChild("Callout") :: RemoteEvent
local DashR = Remotes:FindFirstChild("Dash") :: RemoteEvent?
if not DashR then
	local r = Instance.new("RemoteEvent")
	r.Name = "Dash"
	r.Parent = Remotes
	DashR = r
end
local W = Weapons.list
local now = os.clock
local _ = Players

;(DashR :: RemoteEvent).OnServerEvent:Connect(function(p: Player, look: unknown)
	if p:GetAttribute("Zone") == "hub" or typeof(look) ~= "Vector3" then return end
	local f = Fight.byPlayer[p]
	if not f or not f.alive then return end
	local wid = f.held
	local w = W[wid] :: any
	local D = w and w.dash
	if not D then return end
	local n = now()
	if n < f.staggerUntil or (f.castUntil and n < f.castUntil) or Rules.parryOpen(f, n) or Rules.transforming(f, n) then return end
	if not Rules.gate(f, "dash", n, D.cd / 0.9) then return end -- (one charge: the next only after cd s)
	local root = Fight.root(f)
	if not root then return end
	local flat = Vector3.new((look :: Vector3).X, 0, (look :: Vector3).Z)
	if flat.Magnitude < 0.2 then flat = Vector3.new(root.CFrame.LookVector.X, 0, root.CFrame.LookVector.Z) end
	flat = flat.Unit
	-- the path: from the chest along the look, short of any wall in the way (a body's width back from it)
	local from = root.Position
	local len = D.dist
	local hit = Fight.castMap(from, flat, len + 2)
	if hit then len = math.max(0, (hit.Position - from).Magnitude - 2) end
	local to = from + flat * len
	f.castUntil = n + D.time + D.recover -- (no swing or guard through the dash and its recovery)
	p:SetAttribute("ACGrace", n + D.time + 0.4) -- (the anti-cheat: this burst is the server's say)
	p:SetAttribute("DashV", flat * (len / D.time))
	p:SetAttribute("DashUntil", workspace:GetServerTimeNow() + D.time)
	FxR:FireAllClients({ k = "dash", model = Fight.model(f), a = from, b = to })
	-- the first enemy on the path
	local best, bt = nil, math.huge
	for _, t in Fight.all do
		if t == f or not t.alive or not Fight.allow(f, t) then continue end
		if t.onlyFor ~= nil and t.onlyFor ~= p then continue end
		local tr = Fight.root(t)
		if not tr then continue end
		local rel = tr.Position - from
		local along = rel:Dot(flat)
		if along < -1 or along > len + D.width then continue end
		local side = (rel - flat * along)
		if Vector3.new(side.X, 0, side.Z).Magnitude > D.width or math.abs(side.Y) > 4 then continue end
		if along < bt then best, bt = t, along end
	end
	if not best then return end
	local t = best :: Rules.Fighter
	local tr = Fight.root(t) :: BasePart
	-- a katana guard facing the dash stops it: you're staggered and shoved back off it (the melee parry)
	local pr = Rules.parryAt(t, from - tr.Position, Fight.facing(t), n)
	if pr > 0 then
		local shove = Rules.stagger(f, from - tr.Position, pr == 2, n)
		Fight.knock(f, shove, "parry")
		Rules.tagged(f, t, "parry", n)
		FxR:FireAllClients({ k = "parry", model = Fight.model(t), by = if t.kind == "player" then (t.ref :: Player).UserId else nil, att = p.UserId, pf = pr == 2, kind = "melee", st = f.staggerUntil - n, from = tr.Position })
		if t.kind == "player" then CalloutR:FireClient(t.ref :: Player, if pr == 2 then "PERFECT PARRY!" else "PARRY!", 0.9) end
		CalloutR:FireClient(p, "PARRIED", 0.8)
		return
	end
	task.delay(math.clamp(bt / math.max(1, len) * D.time, 0, D.time), function()
		if t.alive and f.alive then
			Fight.hurt(t, D.dmg, f, wid, false, flat * D.kb + Vector3.new(0, D.kbUp, 0), tr.Position)
		end
	end)
end)
