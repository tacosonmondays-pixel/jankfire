--!strict
-- HOLDOUT's start-up on the server (26 Nov 2026; roblox/docs/HUNT.md): the remote, the house's props, who's in it, and
-- the Studio test hook.
--   JankfireRemotes.Hunt (RemoteEvent): the client's "go" / "back" (HuntTravel) and the moves (HuntMoves)
--   ServerStorage.JankHuntTest (Studio only, BindableFunction):
--     ("go", p) / ("back", p)          to the house and back
--     ("at", p, x, y, z [, yaw])       stand at a spot in the house (its local studs)
--     ("move", p, op, look)            a move as if the client asked ("jab", "push", "super" after "hold"...)
--     ("round", p, opts) / ("stop")    a round now with p and stand-ins / end it
--     ("rstate")                       the round's phase, gun, members
--     ("hurt", p, who, dmg, head)      a round member takes a hit from p (the break-up test)
--     ("state")                        who is in the house, the props wired
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

-- (the remote first: HuntRound waits for it as it loads)
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local remote = Remotes:FindFirstChild("Hunt") :: RemoteEvent?
if not remote then
	local r = Instance.new("RemoteEvent"); r.Name = "Hunt"; r.Parent = Remotes
	remote = r
end

local HC = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("HuntConfig")) :: any
local Hunt = require(script.Parent:WaitForChild("Hunt")) :: any
local HuntTravel = require(script.Parent:WaitForChild("HuntTravel")) :: any
local HuntMoves = require(script.Parent:WaitForChild("HuntMoves")) :: any
local HuntProps = require(script.Parent:WaitForChild("HuntProps")) :: any
local HuntItems = require(script.Parent:WaitForChild("HuntItems")) :: any
local rate: { [Player]: { t: number, n: number } } = {}
;(remote :: RemoteEvent).OnServerEvent:Connect(function(p: Player, op: any, a: any, b: any)
	if type(op) ~= "string" then return end
	-- (at most 30 a second from anyone)
	local r = rate[p]
	local now = os.clock()
	if not r or now - r.t > 1 then r = { t = now, n = 0 }; rate[p] = r end
	r.n += 1
	if r.n > 30 then return end
	if op == "go" then HuntTravel.go(p)
	elseif op == "back" then HuntTravel.back(p)
	elseif HuntItems.handle(p, op, a, b) then return
	else HuntMoves.handle(p, op, a, b) end
end)
Players.PlayerRemoving:Connect(function(p) rate[p] = nil end)

Hunt.start()
-- the house's props: wired once it's in the place (it is built in Edit, so at once in a live server)
task.spawn(function()
	local map = workspace:WaitForChild("Map")
	local house = map:WaitForChild(HC.HOUSE, 60)
	if house then print("[hunt] " .. HuntProps.wire(house)) end
end)

if RunService:IsStudio() then
	local f = ServerStorage:FindFirstChild("JankHuntTest") :: BindableFunction?
	if f then f:Destroy() end
	local hook = Instance.new("BindableFunction")
	hook.Name = "JankHuntTest"
	hook.OnInvoke = function(op: string, p: any, ...: any): any
		local args = { ... }
		if op == "go" then return { HuntTravel.go(p) } end
		if op == "back" then return { HuntTravel.back(p) } end
		if op == "at" then
			local map = workspace:FindFirstChild("Map")
			local house = map and map:FindFirstChild(HC.HOUSE)
			local ch = p.Character
			if not (house and ch) then return "no house or body" end
			local O = house:GetPivot().Position
			local at = O + Vector3.new(args[1], args[2], args[3])
			p:SetAttribute("TeleportT", os.clock())
			ch:PivotTo(CFrame.new(at) * CFrame.Angles(0, math.rad(args[4] or 0), 0) + Vector3.new(0, 3, 0))
			return "ok"
		end
		if op == "move" then HuntMoves.handle(p, args[1], args[2]); return "sent" end
		-- ("round", p, opts): a round now with p (opts: role "gunman" | "hider", standins n, gun, hide s, hunt s)
		if op == "round" then
			local HuntRound = require(script.Parent:WaitForChild("HuntRound")) :: any
			local o = args[1] or {}
			local gm: any = if o.role == "gunman" then p elseif o.role == "hider" then false else nil
			return { HuntRound.start({ p }, { gunman = gm, standins = o.standins or 0, standinRole = if o.role == "hider" then "gunman" else "hider",
				gun = o.gun, hide = o.hide, hunt = o.hunt, fightBack = o.fightBack, passives = o.passives, map = o.map, introSet = o.introSet }) }
		end
		if op == "stop" then return require(script.Parent:WaitForChild("HuntRound")).stop() end
		-- (27 Nov, the item tables and the ragdoll) ("pick", p, id) take from the tables; ("use", p, slot, look) use a slot;
		-- ("rag", p, who, dur, min) down the round member named who (nil = p) as a shove would; ("getup", p)
		if op == "pick" then return HuntItems.pick(p, args[1]) end
		if op == "use" then HuntItems.handle(p, "use", args[1], args[2]); return p:GetAttribute("HuntItems") end
		if op == "cash" then HuntItems.score(p, tonumber(args[1]) or 0); return p:GetAttribute("HuntPoints") end
		if op == "getup" then require(script.Parent:WaitForChild("HuntRagdoll")).ask(p); return "asked" end
		if op == "rag" then
			local Fight = require(script.Parent:WaitForChild("Fight")) :: any
			local HR = require(script.Parent:WaitForChild("HuntRagdoll")) :: any
			local g = require(script.Parent:WaitForChild("HuntRound")).G
			local f = Fight.byPlayer[p]
			if args[1] and g then for _, m in g.members do if (m.p and m.p.Name or m.f.name) == args[1] then f = m.f end end end
			return HR.down(f, Vector3.new(0, 20, 25), tonumber(args[2]) or 2, tonumber(args[3]) or 1)
		end
		if op == "win" then require(script.Parent:WaitForChild("HuntRound")).forceWin(args[1] or "gunman"); return "won " .. tostring(args[1]) end -- (the win films)
		-- ("hurt", p, who?, dmg?, head?): the round's member named who (a stand-in's or a player's name; nil = the first
		-- living hider) takes dmg from p as if shot (head = a headshot). Fight.allow still decides (the hunt phase only)
		if op == "hurt" then
			local g = require(script.Parent:WaitForChild("HuntRound")).G
			if not g then return "no round" end
			local Fight = require(script.Parent:WaitForChild("Fight")) :: any
			local by = Fight.byPlayer[p]
			for _, m in g.members do
				local nm = if m.p then m.p.Name else m.f.name
				if nm == args[1] or (args[1] == nil and m.role == "hider" and m.alive) then
					return { nm, Fight.hurt(m.f, tonumber(args[2]) or 30, by, tostring(g.gun or "test"), args[3] == true, nil) }
				end
			end
			return "no such member"
		end
		if op == "rstate" then
			local g = require(script.Parent:WaitForChild("HuntRound")).G
			if not g then return "no round" end
			local ms = {}
			for _, m in g.members do table.insert(ms, { name = if m.p then m.p.Name else m.f.name, role = m.role, alive = m.alive, hp = m.f.hp, forced = m.f.forced }) end
			return { phase = g.phase, gun = g.gun, passives = g.passives, map = g.def.id, members = ms, kills = g.kills }
		end
		if op == "state" then
			local inn = {}
			for q in Hunt.inHouse do table.insert(inn, q.Name) end
			return { inHouse = inn, players = ReplicatedStorage:GetAttribute("HuntPlayers") }
		end
		return "unknown op " .. tostring(op)
	end
	hook.Parent = ServerStorage
end
