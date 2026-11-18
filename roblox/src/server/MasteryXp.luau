--!strict
-- WEAPON MASTERY on the server (Shared.Mastery has the numbers and the camos; docs/MASTERY.md). each player's XP per
-- weapon lives in their stats save (Stats.luau, data.mx = { [weapon] = xp }: session-locked like the rest, "_studio"
-- stores in Studio). Stats decides what counts (real matches only: the same checks as its own numbers, never a ghost
-- or dev match, never a dummy) and calls in here; this module only adds, levels, grants and tells the client.
--   * a camo is granted for its gun alone through Loot.grant("mastery:<camo>@<gun>", "mastery:<userId>:<camo>@<gun>"):
--     once (the receipt, and ownership), and only once the camo is live (Mastery.live). sync() hands out every camo a
--     player has earned and lacks: on join, on a level up, and when a camo goes live while they're here
--   * the player attribute Mastery ("ar=5120;smg=40") carries the XP for the bars
--   * the remote event JankfireRemotes.MasteryPush tells the client: { k = "level", w, lv } a weapon levelled up,
--     { k = "camo", w, c } a camo was unlocked, { k = "match", gains = { [w] = xp }, xp = { [w] = total } } what the
--     match just over gave (client/MasteryClient.client.luau draws them)
-- Studio play tests: ServerStorage.JankMasteryTest (BindableFunction), see MasteryXp.test at the end.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local M = require(Shared:WaitForChild("Mastery"))
local Roster = require(Shared:WaitForChild("Roster")) :: any
local Loot = require(script.Parent:WaitForChild("Loot")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local Push = Remotes:FindFirstChild("MasteryPush") :: RemoteEvent?
if not Push then
	local e = Instance.new("RemoteEvent")
	e.Name = "MasteryPush"
	e.Parent = Remotes
	Push = e
end
local push = Push :: RemoteEvent

local MasteryXp = {}

type PS = { p: Player, d: any, dirty: () -> (), match: { [string]: number }?, again: boolean, busy: boolean }
local ps: { [Player]: PS } = {}
local CAP = M.total(M.MAX)

local function mx(d: any): { [string]: number }
	if type(d.mx) ~= "table" then d.mx = {} end
	return d.mx
end
local function send(p: Player, msg: any)
	if p.Parent then pcall(push.FireClient, push, p, msg) end
end
function MasteryXp.publish(p: Player)
	local s = ps[p]
	if not s or not p.Parent then return end
	local v = M.encode(mx(s.d))
	if p:GetAttribute("Mastery") ~= v then p:SetAttribute("Mastery", v) end
end

-- ------------------------------------------------------------------ the camos
local function key(id: string, wid: string): string return id .. "@" .. wid end
local function owned(p: Player, id: string, wid: string): boolean
	-- (what's really owned: Loot.owns says yes to anything under the owner's Studio "unlock")
	local o = Loot.ownedOf(p)
	return o.wrap ~= nil and o.wrap[key(id, wid)] == true
end
-- every camo this player has earned (and is live) but doesn't own yet: granted, one at a time (Loot.grant yields:
-- it saves). a second call while one runs makes the first go round again
local function sync(p: Player)
	local s = ps[p]
	if not s or not Loot.ready(p) then return end
	if s.busy then s.again = true; return end
	s.busy = true
	repeat
		s.again = false
		for wid, xp in table.clone(mx(s.d)) do
			if not M.levels(wid) then continue end
			for _, c in M.earned(M.levelOf(xp)) do
				if not M.live(c.id) or owned(p, c.id, wid) then continue end
				local ok, got = pcall(Loot.grant, p, "mastery:" .. key(c.id, wid), "mastery:" .. p.UserId .. ":" .. key(c.id, wid))
				if ok and got and owned(p, c.id, wid) then
					send(p, { k = "camo", w = wid, c = c.id })
				elseif not ok then
					warn("[jankfire] mastery: grant failed: " .. tostring(got))
				end
				if ps[p] ~= s then return end -- (they left while it saved)
			end
		end
	until not s.again
	s.busy = false
end
local function syncSoon(p: Player) task.spawn(sync, p) end

-- ------------------------------------------------------------------ XP (Stats calls these)
-- n XP with this weapon. why is for the log only. returns the XP it has now
function MasteryXp.add(p: Player, wid: any, n: number, _why: string?): number?
	local s = ps[p]
	if not s or type(wid) ~= "string" or n <= 0 then return nil end
	local w = Roster.formOf and Roster.formOf[wid] or wid -- (the Scythe's rifle form is the Scythe)
	if not M.levels(w) then return nil end
	local t = mx(s.d)
	local before = math.floor(tonumber(t[w]) or 0)
	if before >= CAP then return before end
	local after = math.min(CAP, before + math.floor(n))
	t[w] = after
	s.dirty()
	if s.match then s.match[w] = (s.match[w] or 0) + (after - before) end
	MasteryXp.publish(p)
	local l0, l1 = M.levelOf(before), M.levelOf(after)
	if l1 > l0 then
		send(p, { k = "level", w = w, lv = l1, from = l0 })
		syncSoon(p)
	end
	return after
end
-- the weapon held longest in a { [weapon] = seconds } table (nil if none)
function MasteryXp.top(times: { [string]: number }?): string?
	local best, top = 0, nil
	for wid, t in times or {} do if t > best then best, top = t, wid end end
	return top
end
-- a match (or a Stats test match) begins / ends for this player. counted = it was real: its gains go to the client
function MasteryXp.matchStart(p: Player)
	local s = ps[p]
	if s then s.match = {} end
end
function MasteryXp.matchEnd(p: Player, counted: boolean)
	local s = ps[p]
	if not s then return end
	local g = s.match
	s.match = nil
	if not counted or not g or next(g) == nil then return end
	local now = {}
	for w in g do now[w] = math.floor(tonumber(mx(s.d)[w]) or 0) end
	send(p, { k = "match", gains = g, xp = now })
end

-- ------------------------------------------------------------------ players (Stats binds its save's data here)
-- (again after a test puts a whole save back: the data table changed)
function MasteryXp.bind(p: Player, data: any, dirty: () -> ())
	local old = ps[p]
	ps[p] = { p = p, d = data, dirty = dirty, match = if old then old.match else nil, again = false, busy = if old then old.busy else false }
	mx(data)
	MasteryXp.publish(p)
	syncSoon(p)
end
function MasteryXp.unbind(p: Player)
	ps[p] = nil
end

local started = false
function MasteryXp.init()
	if started then return end
	started = true
	-- (the loot save loaded, or what they own changed: anything earned and missing)
	if Loot.changed then Loot.changed:Connect(function(p: Player) if ps[p] then syncSoon(p) end end) end
	-- a camo's picture lands in the place (the wraps session's WrapBook), or a test switches them all on
	local function all() for p in ps do syncSoon(p) end end
	local function watchLib(lib: Instance) lib.ChildAdded:Connect(function(c) if M.isCamo(c.Name) then all() end end) end
	local lib = ReplicatedStorage:FindFirstChild("JankfireWraps")
	if lib then watchLib(lib) end
	ReplicatedStorage.ChildAdded:Connect(function(c) if c.Name == "JankfireWraps" then watchLib(c); all() end end)
	ReplicatedStorage:GetAttributeChangedSignal("MasteryLive"):Connect(all)
	Players.PlayerRemoving:Connect(function(p) ps[p] = nil end)
	if RunService:IsStudio() then
		local old = ServerStorage:FindFirstChild("JankMasteryTest")
		if old then old:Destroy() end
		local fn = Instance.new("BindableFunction")
		fn.Name = "JankMasteryTest"
		fn.OnInvoke = function(op: string, a: any, b: any, c: any): any return MasteryXp.test(op, a, b, c) end
		fn.Parent = ServerStorage
	end
end

-- ------------------------------------------------------------------ Studio tests (ServerStorage.JankMasteryTest)
--   ("read", player)              { mx = { [w] = xp }, levels = { [w] = level }, camos = { "mastery_gold@ar", ... } owned,
--                                   live = { [camo] = bool }, attr = the Mastery attribute }
--   ("add", player, weapon, n)    n XP with it, as a kill would give (no match needed): its new XP
--   ("set", player, weapon, lv)   its XP to the start of that level (a level up shows if it went up): its new XP
--   ("put", player, map)          the whole XP map back as it was ({ [w] = xp }: a test's backup from "read")
--   ("live", on)                  every camo live (ReplicatedStorage attribute MasteryLive) or back to "picture in place"
--   ("drop", player)              every mastery camo off their loot save, with its receipts (a test's grants undone)
--   ("sync", player)              hand out what's earned now (waits for it)
--   ("toast", player, kind, ...)  send a push without changing anything: ("toast", p, "level", "ar", 12),
--                                 ("toast", p, "camo", "ar", "mastery_gold"), ("toast", p, "match", { ar = 450 })
function MasteryXp.test(op: string, a: any, b: any, c: any): any
	if not RunService:IsStudio() then return nil end
	if op == "live" then
		ReplicatedStorage:SetAttribute("MasteryLive", if a == true then true else nil)
		return ReplicatedStorage:GetAttribute("MasteryLive") == true
	end
	local p = a :: Player
	local s = ps[p]
	if not s then return "no such player (or their stats are still loading)" end
	if op == "read" then
		local levels, camos, live = {}, {}, {}
		for w, x in mx(s.d) do levels[w] = M.levelOf(x) end
		for k in Loot.ownedOf(p).wrap or {} do
			local id = string.match(k, "^([%w_]+)@")
			if id and M.isCamo(id) then table.insert(camos, k) end
		end
		table.sort(camos)
		for _, cm in M.CAMOS do live[cm.id] = M.live(cm.id) end
		return { mx = table.clone(mx(s.d)), levels = levels, camos = camos, live = live, attr = p:GetAttribute("Mastery") }
	elseif op == "add" then
		return MasteryXp.add(p, b, tonumber(c) or 0, "test")
	elseif op == "set" then
		local w = tostring(b)
		if not M.levels(w) then return "not a live weapon" end
		local before = math.floor(tonumber(mx(s.d)[w]) or 0)
		local want = M.total(math.clamp(math.floor(tonumber(c) or 1), 1, M.MAX))
		if want > before then return MasteryXp.add(p, w, want - before, "test") end
		mx(s.d)[w] = if want > 0 then want else nil
		s.dirty(); MasteryXp.publish(p)
		return want
	elseif op == "put" then
		if type(b) ~= "table" then return false end
		local t = {}
		for w, x in b do if type(w) == "string" and (tonumber(x) or 0) > 0 then t[w] = math.floor(tonumber(x) :: number) end end
		s.d.mx = t
		s.dirty(); MasteryXp.publish(p)
		return true
	elseif op == "drop" then
		if type(Loot.testDrop) ~= "function" then return "Loot.testDrop missing" end
		return Loot.testDrop(p, function(t: string, k: string): boolean
			local id = string.match(k, "^([%w_]+)@")
			return t == "wrap" and id ~= nil and M.isCamo(id)
		end, function(r: string): boolean return string.sub(r, 1, 8) == "mastery:" end)
	elseif op == "sync" then
		sync(p)
		return true
	elseif op == "toast" then
		if b == "level" then send(p, { k = "level", w = c, lv = 12, from = 11 })
		elseif b == "camo" then send(p, { k = "camo", w = c, c = "mastery_gold" })
		elseif b == "match" then
			local now = {}
			for w in (if type(c) == "table" then c else {}) do now[w] = math.floor(tonumber(mx(s.d)[w]) or 0) end
			send(p, { k = "match", gains = c, xp = now })
		end
		return true
	end
	return nil
end

return MasteryXp
