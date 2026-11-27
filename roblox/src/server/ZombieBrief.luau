--!strict
-- ZOMBIES: the BRIEFING (27 Nov 2026; roblox/docs/ZOMBIES.md 4.14). The owner: "Can the cutscene static into like a
-- green text pc code style menu? Thats where you select you weapons and passives and stuff? There will be a cool weapon
-- graphic that's like a green grid hologram thing? It's like debrief after the news".
-- Between the intro's static and its school shot (ZombieCine holds its clock there): one shared timer (ZM.BRIEF.secs)
-- from the moment it opens; when every human is READY it closes at once. Each human picks a starting sidearm
-- (ZM.BRIEF.sidearms) and one passive (ZM.BRIEF.passives); the bots pick a passive at random (their gun is
-- ZombieBots' own). The server checks and applies the picks: the sidearm through freshKit's m.startGun (what you get
-- back after being out too), the passives through the mode's hooks (creditMul, bleedMul, regenAfter, boardTimeMul,
-- boardPayMul, killed). Nobody can join a running game today; a member who picked nothing keeps the defaults (the
-- revolver, no passive). Installed after ZombieLight.
--   arena attributes: BriefT0 (server time it opens), BriefEnd (the timer's end), BriefT1 (it closed: the film's
--   school shot plays from then), BriefSquad (JSON rows: n name, w sidearm, p passive, r ready, bot, id UserId)
--   the Zm remote: { k = "bpick", w = <sidearm>?, p = <passive>? } while it's open, { k = "bready" }
-- Test ops (Studio's ServerStorage.JankZombies): "brief" (the state), "bpick" <player> "<sidearm>:<passive>",
-- "bready" <player>, "bclose", "bhooks" <player> (what each passive's hooks return for them)
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local HttpService = game:GetService("HttpService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local ZM = require(Shared:WaitForChild("ZM"))
local Weapons = require(Shared:WaitForChild("Weapons"))

local ZombieBrief = {}
local W = Weapons.list
local B = ZM.BRIEF
local XC = ZM.X
local now = os.clock
local function srv(): number return workspace:GetServerTimeNow() end

function ZombieBrief.install(Z: any)
	local ext, X = Z.ext, Z.X
	local zr = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Zm") :: RemoteEvent
	local AT = B.at -- (s into the film it opens)
	local TAIL = XC.intro - AT -- (the film after it: the school, the squad, your view)
	local SWITCH_OFF = 0.35 -- (the terminal's switch-off before the school shot)

	local function chain(name: string, fn: (...any) -> any)
		local prev = ext[name]
		ext[name] = function(...)
			local r = if prev then prev(...) else nil
			local mine = fn(r, ...)
			if mine ~= nil then return mine end
			return r
		end
	end
	local function humans(g: any): { any }
		local out = {}
		for _, m in g.members do if m.p then table.insert(out, m) end end
		return out
	end
	local function memberOf(g: any, p: Player): any
		for _, m in g.members do if m.p == p then return m end end
		return nil
	end
	local function pas(m: any): any
		return if m and m.passive then B.passives[m.passive] else nil
	end

	-- what every client draws the squad's column from
	local function squad(g: any)
		local b = g.brief
		local rows = {}
		for _, m in g.members do
			table.insert(rows, {
				n = m.name, w = m.startGun or (if m.bot then m.bot.gun else ZM.R.startGuns[1]), p = m.passive or "",
				r = m.p == nil or b.ready[m] == true, bot = m.p == nil, id = if m.p then m.p.UserId else 0,
			})
		end
		g.model:SetAttribute("BriefSquad", HttpService:JSONEncode(rows))
	end
	local function setTimes(g: any)
		local b = g.brief
		g.model:SetAttribute("BriefT0", b.t0)
		g.model:SetAttribute("BriefEnd", b.endT)
		-- round 1 waits for it, then the film's tail (+2.1 s: a client still loading holds its black lead, ZombieExtract)
		g.untilT = now() + math.max(0, b.endT - srv()) + TAIL + 2.1
	end
	local function close(g: any, why: string)
		local b = g.brief
		if not b or b.closed then return end
		b.closed = true
		b.why = why
		g.model:SetAttribute("BriefT1", srv() + SWITCH_OFF)
		g.untilT = now() + SWITCH_OFF + TAIL + 1.5
		if g.x and g.x.skips then table.clear(g.x.skips) end -- (a skip after it needs everyone again: ZombieExtract)
		squad(g)
	end
	local function allReady(g: any)
		local b = g.brief
		if not b or b.closed then return end
		local hs = humans(g)
		if #hs == 0 then return end
		for _, m in hs do if not b.ready[m] then return end end
		close(g, "ready")
	end
	-- a pick: the sidearm re-kits you (nothing's bought yet: it's before round 1), the passive is a name
	local function apply(g: any, m: any, w: string?, p: string?)
		local changed = false
		if w and table.find(B.sidearms, w) and W[w] and m.startGun ~= w then
			m.startGun = w
			X.freshKit(m)
			X.arm(m, w)
			changed = true
		end
		if p and B.passives[p] and m.passive ~= p then
			m.passive = p
			changed = true
		end
		if m.p then
			m.p:SetAttribute("ZmSidearm", m.startGun)
			m.p:SetAttribute("ZmPassive", m.passive)
		end
		if changed then squad(g) end
	end

	-- the game starts: ZombieExtract's own start hook set the film's IntroT0 (it runs first: installed before)
	chain("start", function(_r: any, g: any)
		local t0 = g.model:GetAttribute("IntroT0")
		if type(t0) ~= "number" then return nil end
		g.brief = { t0 = t0 + AT, endT = t0 + AT + B.secs, ready = {}, closed = false, last = {} }
		for _, m in g.members do
			if m.p then
				m.p:SetAttribute("ZmSidearm", nil)
				m.p:SetAttribute("ZmPassive", nil)
			else
				m.passive = B.order[math.random(1, #B.order)] -- (a bot picks at random)
			end
		end
		for _, k in { "BriefT1", "BriefSquad" } do g.model:SetAttribute(k, nil) end
		setTimes(g)
		squad(g)
		return nil
	end)
	-- every human skipped the news (ZombieExtract's xskip): the briefing opens now, not round 1
	ext.allSkipped = function(g: any): boolean?
		local b = g.brief
		if not b or b.closed then return nil end
		if srv() < b.t0 then
			b.t0 = srv()
			b.endT = b.t0 + B.secs
			setTimes(g)
		end
		return true
	end

	-- ---------------------------------------------------------------- the passives
	chain("creditMul", function(r: any, _g: any, m: any, why: string?)
		local ps = pas(m)
		if not ps then return nil end
		local k = if type(r) == "number" then r else 1
		if ps.credit then k *= ps.credit end
		if ps.head and why == "head" then k *= ps.head end
		return k
	end)
	chain("bleedMul", function(r: any, _g: any, m: any)
		local ps = pas(m)
		if not ps or not ps.bleed then return nil end
		return (tonumber(r) or 1) * ps.bleed
	end)
	chain("regenAfter", function(r: any, _g: any, m: any)
		local ps = pas(m)
		if not ps or not ps.regenAfter then return nil end
		return math.min(tonumber(r) or math.huge, ps.regenAfter)
	end)
	chain("boardTimeMul", function(r: any, _g: any, m: any)
		local ps = pas(m)
		if not ps or not ps.board then return nil end
		return (tonumber(r) or 1) * ps.board
	end)
	chain("boardPayMul", function(r: any, _g: any, m: any)
		local ps = pas(m)
		if not ps or not ps.pay then return nil end
		return (tonumber(r) or 1) * ps.pay
	end)
	local function scrounge(k: any)
		local ps = pas(k)
		if not ps or not ps.rounds or not k.f.alive then return end
		local wid = k.f.held
		local w = W[wid]
		local total = X.maxTotal(k, wid)
		if not w or not w.mag or not total then return end
		local cap = math.max(0, total - w.mag)
		local was = k.res[wid] or 0
		if was < cap then
			k.res[wid] = math.min(cap, was + ps.rounds)
			X.pushRes(k)
		end
	end
	chain("killed", function(_r: any, _g: any, _z: any, k: any)
		if k then scrounge(k) end
		return nil
	end)

	-- ---------------------------------------------------------------- the picks, READY
	zr.OnServerEvent:Connect(function(p: Player, msg: any)
		if type(msg) ~= "table" or (msg.k ~= "bpick" and msg.k ~= "bready") then return end
		local g = Z.game()
		local b = g and g.brief
		if not g or not b or b.closed or g.st ~= "pre" then return end
		local m = memberOf(g, p)
		if not m then return end
		local t = now()
		if t - (b.last[p] or -math.huge) < 0.08 then return end -- (a re-kit per pick: not every frame)
		b.last[p] = t
		if msg.k == "bpick" then
			apply(g, m, if type(msg.w) == "string" then msg.w else nil, if type(msg.p) == "string" then msg.p else nil)
		else
			b.ready[m] = true
			squad(g)
			allReady(g)
		end
	end)
	-- the timer, and a human leaving (the rest may all be ready)
	task.spawn(function()
		while true do
			task.wait(0.2)
			local g = Z.game()
			local b = g and g.brief
			if g and b and not b.closed then
				if g.st ~= "pre" then close(g, "gone")
				elseif srv() >= b.endT then close(g, "time")
				else allReady(g) end
			end
		end
	end)

	-- ---------------------------------------------------------------- Studio test ops
	chain("test", function(r: any, op: string, a: any, bArg: any)
		if r ~= nil then return nil end
		local g = Z.game()
		local b = g and g.brief
		if op == "brief" then
			if not b then return "no briefing" end
			local rows = {}
			for _, m in g.members do
				table.insert(rows, { m.name, m.startGun or "-", m.passive or "-", b.ready[m] == true, table.concat(m.guns, ",") })
			end
			return { open = not b.closed, why = b.why, t0 = b.t0 - srv(), endT = b.endT - srv(), st = g.st, rows = rows }
		end
		if not b then return nil end
		local m = if typeof(a) == "Instance" and a:IsA("Player") then memberOf(g, a) else nil
		if op == "bpick" and m and type(bArg) == "string" then
			local w, ps = string.match(bArg, "^([^:]*):?(.*)$")
			apply(g, m, if w ~= "" then w else nil, if ps ~= "" then ps else nil)
			return { m.startGun, m.passive }
		elseif op == "bready" and m then
			b.ready[m] = true; squad(g); allReady(g); return true
		elseif op == "bclose" then
			close(g, "test"); return true
		elseif op == "bhooks" and m then
			-- what each passive's hooks give for this member (the whole chain), then SCROUNGER on 5 spent spares
			local out, old = {}, m.passive
			for _, id in B.order do
				m.passive = id
				out[id] = string.format("credit %s head %s bleed %s regenAfter %s boardTime %s boardPay %s",
					tostring(ext.creditMul(g, m, "kill")), tostring(ext.creditMul(g, m, "head")), tostring(ext.bleedMul(g, m)),
					tostring(ext.regenAfter(g, m)), tostring(ext.boardTimeMul(g, m)), tostring(ext.boardPayMul(g, m)))
			end
			m.passive = "scrounger"
			local wid = m.f.held
			local before = m.res[wid]
			if before then m.res[wid] = math.max(0, before - 5) end
			local mid = m.res[wid]
			scrounge(m)
			out.scrounger_kill = string.format("%s spares %s -> %s -> %s", tostring(wid), tostring(before), tostring(mid), tostring(m.res[wid]))
			m.res[wid] = before
			X.pushRes(m)
			m.passive = old
			return out
		end
		return nil
	end)
end

return ZombieBrief
