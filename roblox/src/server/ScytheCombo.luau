--!strict
-- the Scythe's combo finisher (the owner, 18 Nov 2026: "if you get e + f + swing + dash, it auto shoots to do a
-- finisher! ... that final shot should reward an insta kill basically"; WEAPONS.md "Scythe"). the server keeps one
-- chain per attacker, on one target, from steps it has already confirmed elsewhere (nothing is judged again here):
--   grapple   your rope tied onto them (Main's hook on a body)            starts the chain (the scythe in your hands)
--   yank      the full pull (Main's yank, an enemy)                         next, within GAP s
--   swing     a scythe swing's hit on them (Combat, its latch list)  } either order, each within GAP s of the last,
--   dash      the scythe dash's contact on them (ScytheDash)         } the whole chain within WHOLE s
-- a scythe swing or dash that touches nobody while a chain is up, swapping weapons, either one dying, or a gap too long
-- ends it. it counts on a living enemy player; a training dummy counts only in Studio or the training zone (tests).
-- the 4th step fires the finisher (Combo.fire): the scythe snaps to its rifle (the server holds it, everyone's copy
-- moves across, FormT), and SNAP s later one shot at their head kills them whatever their HP or shield, credited to
-- the Scythe's rifle as a headshot. it fizzles (no shot) out of sight, past REACH or if they're already gone. then it
-- snaps back. everyone draws it from Fx "scyfin" (ScytheDash.client): a heavy teal tracer, a ring and a burst at the
-- head; the killer gets a hit-stop and a punch-in (FOV only, never the camera). a kill that ends a round or a match
-- plays the finishers' own cut as usual (Fight.onKill). no text anywhere
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Weapons = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Weapons"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Fight = require(script.Parent:WaitForChild("Fight"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local FxR = Remotes:WaitForChild("Fx") :: RemoteEvent
local EquipR = Remotes:WaitForChild("Equip") :: RemoteEvent

local S = Weapons.S
local Combo = {}
Combo.GAP = 2.0 -- s between one step and the next
Combo.WHOLE = 6.0 -- s for the whole chain
Combo.REACH = 40 * S -- studs: the shot's reach
Combo.SNAP = 0.2 -- s: the scythe to its rifle, then the shot
Combo.BACK = 0.35 -- s after the shot: back to the scythe

type Chain = { t: Rules.Fighter, start: number, last: number, yank: number?, swing: number?, dash: number?, swungAt: number? }
local chains: { [any]: Chain } = setmetatable({}, { __mode = "k" }) :: any

-- (Studio play tests: JankScytheTest "combo") what happened, newest last
Combo.log = {} :: { any }
local function note(e: any)
	e.t = os.clock()
	table.insert(Combo.log, e)
	if #Combo.log > 30 then table.remove(Combo.log, 1) end
end

local function holdsScythe(f: Rules.Fighter): boolean return f.held == "scythe" or f.held == "scythe_rifle" end
-- a step on t counts: a living enemy player; a training dummy only in Studio or the training zone
local function counts(f: Rules.Fighter, t: Rules.Fighter): boolean
	if t == f or not t.alive or not f.alive or f.kind ~= "player" then return false end
	if not Fight.allow(f, t) then return false end
	if t.kind == "player" then return true end
	if t.kind == "dummy" then return RunService:IsStudio() or (f.ref :: Player):GetAttribute("Zone") == "training" end
	return false
end

function Combo.reset(f: Rules.Fighter, why: string)
	if chains[f] then
		chains[f] = nil
		note({ k = "reset", by = f.name, why = why })
	end
end

-- the state, for the test hook
function Combo.state(f: Rules.Fighter): any
	local c = chains[f]
	if not c then return nil end
	local n = os.clock()
	return { target = c.t.name, age = n - c.start, since = n - c.last, yank = c.yank ~= nil, swing = c.swing ~= nil, dash = c.dash ~= nil }
end

-- ------------------------------------------------------------------ the shot
local function headOf(t: Rules.Fighter): Vector3?
	local m = Fight.model(t)
	local h = m and m:FindFirstChild("Head")
	if h and h:IsA("BasePart") then return h.Position end
	local r = Fight.root(t)
	return r and r.Position + Vector3.new(0, 1.5, 0)
end
local function clear(f: Rules.Fighter, t: Rules.Fighter): (Vector3?, Vector3?, string?)
	if not t.alive then return nil, nil, "gone" end
	local eye, head = Fight.eye(f), headOf(t)
	if not eye or not head then return nil, nil, "gone" end
	local d = head - eye
	if d.Magnitude > Combo.REACH then return nil, nil, "too far" end
	if d.Magnitude > 0.5 and Fight.castMap(eye, d.Unit, d.Magnitude - 0.4) then return nil, nil, "out of sight" end
	return eye, head, nil
end
-- the server holds this form now and everyone's copy moves across (Combat's own switch does the same)
local function hold(f: Rules.Fighter, wid: string)
	local p = f.ref :: Player
	f.held = wid
	p:SetAttribute("FormT", workspace:GetServerTimeNow())
	Fight.showWeapon(f)
	EquipR:FireClient(p, wid)
end

function Combo.fire(f: Rules.Fighter, t: Rules.Fighter)
	local p = f.ref :: Player
	local _, _, why = clear(f, t)
	if why then note({ k = "fizzle", by = f.name, v = t.name, why = why }); return end
	note({ k = "finisher", by = f.name, v = t.name })
	hold(f, "scythe_rifle")
	task.delay(Combo.SNAP, function()
		if not f.alive then return end
		local eye, head, why2 = clear(f, t)
		if eye and head then
			local dir = (head - eye).Unit
			FxR:FireAllClients({ k = "scyfin", model = Fight.model(f), victim = Fight.model(t), by = p.UserId, a = eye, b = head })
			local kb = dir * (30 * S) + Vector3.new(0, 10 * S, 0)
			local hp0 = t.hp
			-- whatever their HP: more than all of it, straight to HP (plain: no dome or card asked); a shield or a bubble
			-- that still kept them up is gone round with a kill of its own: the owner's "insta kill"
			Fight.hurt(t, t.hp + 1000, f, "scythe_rifle", true, kb, head, nil, true)
			local forced = false
			if t.alive then
				forced = true
				local info = Rules.kill(t, f, "scythe_rifle", os.clock())
				Fight.died(info, kb)
			end
			note({ k = "shot", by = f.name, v = t.name, hp = hp0, dist = (head - eye).Magnitude, forced = forced, dead = not t.alive })
		else
			note({ k = "fizzle", by = f.name, v = t.name, why = why2 })
		end
		task.delay(Combo.BACK, function()
			if f.alive and f.held == "scythe_rifle" then hold(f, "scythe") end
		end)
	end)
end

-- ------------------------------------------------------------------ the steps (each where the server already said so)
function Combo.step(f: Rules.Fighter, t: Rules.Fighter, kind: string)
	if not counts(f, t) then return end
	local n = os.clock()
	local c = chains[f]
	if c and (n - c.last > Combo.GAP or n - c.start > Combo.WHOLE or not c.t.alive) then
		Combo.reset(f, "too slow")
		c = nil
	end
	if kind == "grapple" then
		if not holdsScythe(f) then return end
		chains[f] = { t = t, start = n, last = n }
		note({ k = "grapple", by = f.name, v = t.name })
		return
	end
	if not c or c.t ~= t then return end -- (no chain on them: a step out of order is nothing)
	if not holdsScythe(f) then Combo.reset(f, "weapon"); return end
	if kind == "yank" then
		if c.yank then return end
		c.yank, c.last = n, n
		note({ k = "yank", by = f.name, v = t.name })
		return
	end
	if not c.yank then return end -- (a hit before the pull isn't part of it)
	if kind == "swing" then c.swing = c.swing or n elseif kind == "dash" then c.dash = c.dash or n else return end
	c.last = n
	note({ k = kind, by = f.name, v = t.name })
	if c.swing and c.dash then
		chains[f] = nil
		Combo.fire(f, t)
	end
end

-- a scythe swing was taken (Combat): if it lands on the chain's target nothing happens; if it touches nobody (or only
-- someone else) by its hit time, the chain is over
function Combo.swung(f: Rules.Fighter, hitT: number)
	local c = chains[f]
	if not c then return end
	local at = os.clock()
	c.swungAt = at
	task.delay(hitT + 0.45, function()
		local c2 = chains[f]
		if c2 ~= c or c2.swungAt ~= at then return end
		if not (c2.swing and c2.swing >= at) and c2.last < at then Combo.reset(f, "swing missed") end
	end)
end
-- a scythe dash that touched nobody
function Combo.miss(f: Rules.Fighter, kind: string) if chains[f] then Combo.reset(f, kind .. " missed") end end
-- a weapon swap: off the scythe ends it
function Combo.equipped(f: Rules.Fighter) if chains[f] and not holdsScythe(f) then Combo.reset(f, "weapon") end end

-- either one dying ends it
Fight.onKill(function(info: Rules.KillInfo)
	for f, c in chains do
		if f == info.v or c.t == info.v then Combo.reset(f, "a death") end
	end
end)

return Combo
