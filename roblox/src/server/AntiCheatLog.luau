--!strict
-- the anti-cheat's review log (docs/ANTI-CHEAT.md): every catch (put back, kick, ban) and every aim flag the server
-- only writes down. this server's entries are kept in memory; every 30 s the new ones are appended to a DataStore list
-- the owner reads from the panel (/ac in chat), so flags from every server end up in one place. nothing leaves Roblox.
--   DataStore "JankAntiCheat_v1":  "log" = the newest MAX entries (a Studio play test writes "log_studio" instead, so
--   test catches never mix with real ones);  "u_<userId>" = one player's totals (points, kicks, flags by kind, last)
local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local STUDIO = RunService:IsStudio()
local LOG_KEY = if STUDIO then "log_studio" else "log"
local USER_PREFIX = if STUDIO then "su_" else "u_"
local MAX = 300
local FLUSH = 30

export type Entry = {
	t: number, -- os.time()
	uid: number,
	name: string,
	kind: string, -- teleport, noclip, inside, fly, stall, speed, rise, kick, ban, unban, head, snap, smoke, remote, admin
	act: string, -- "put back", "flag", "kick", "would kick" (Studio), "ban", "unban", "clear"
	info: string, -- the numbers behind it, for a person to read
	n: number?, -- how many times in a row (merged)
	srv: string?, -- which server (the first 8 of its JobId)
}

local Log = {}
local recent: { Entry } = {} -- this server's, oldest first
local queue: { Entry } = {}
local users: { [number]: { kicks: number, points: number, flags: { [string]: number } } } = {}
local last: { [string]: Entry } = {} -- uid..kind -> the entry a repeat merges into
local store: DataStore? = nil
pcall(function() store = DataStoreService:GetDataStore("JankAntiCheat_v1") end)
local SRV = if game.JobId ~= "" then string.sub(game.JobId, 1, 8) else "st" .. (os.time() % 100000)

-- one line for the log. a repeat of the same kind for the same player within 10 s adds to the last line (a flying
-- cheater is put back every second: that's one line with a count, not sixty)
function Log.add(p: Player | number, kind: string, act: string, info: string, points: number?)
	local uid = if typeof(p) == "Instance" then (p :: Player).UserId else p :: number
	local name = if typeof(p) == "Instance" then (p :: Player).Name else tostring(uid)
	local key = uid .. "|" .. kind .. "|" .. act
	local now = os.time()
	local prev = last[key]
	if prev and now - prev.t <= 10 then
		prev.n = (prev.n or 1) + 1
		prev.t = now
		prev.info = string.sub(info, 1, 200)
		if not table.find(queue, prev) then table.insert(queue, prev) end
	else
		local e: Entry = { t = now, uid = uid, name = name, kind = kind, act = act, info = string.sub(info, 1, 200), n = 1, srv = SRV }
		table.insert(recent, e)
		while #recent > MAX do table.remove(recent, 1) end
		table.insert(queue, e)
		last[key] = e
	end
	local u = users[uid] or { kicks = 0, points = 0, flags = {} }
	users[uid] = u
	u.flags[kind] = (u.flags[kind] or 0) + 1
	u.points += points or 0
	if act == "kick" then u.kicks += 1 end
	print(("[anticheat] %s %s: %s (%s)"):format(name, kind, act, info))
end

-- the cached copy of the stored list (the panel asks every few seconds; the DataStore is read at most every 20 s)
local stored: { Entry } = {}
local storedT = -math.huge
local function readStored()
	if not store or os.clock() - storedT < 20 then return end
	storedT = os.clock()
	local ok, v = pcall(function() return (store :: DataStore):GetAsync(LOG_KEY) end)
	if ok and type(v) == "table" then stored = v end
end

-- everything: the stored list plus this server's lines not stored yet, newest first, at most `max`
function Log.read(max: number?): { Entry }
	readStored()
	local out = {}
	for _, e in recent do table.insert(out, e) end
	-- (this server's own lines are all in `recent`; the stored list adds the other servers')
	for _, e in stored do
		if type(e) == "table" and e.srv ~= SRV then table.insert(out, e) end
	end
	table.sort(out, function(a, b) return (a.t or 0) > (b.t or 0) end)
	local n = max or 120
	while #out > n do table.remove(out) end
	return out
end

-- one player's stored totals (across servers), or nil
function Log.user(uid: number): any
	if not store then return nil end
	local ok, v = pcall(function() return (store :: DataStore):GetAsync(USER_PREFIX .. uid) end)
	return if ok then v else nil
end

-- the queue into the DataStore: one UpdateAsync for the list, one per player who got new lines
function Log.flush()
	if not store or #queue == 0 then return end
	local batch = queue
	queue = {}
	local ok, err = pcall(function()
		(store :: DataStore):UpdateAsync(LOG_KEY, function(old: any)
			local list = if type(old) == "table" then old else {}
			-- (a merged line goes in again: drop its older copy from this server)
			for _, e in batch do
				for i = #list, 1, -1 do
					local o = list[i]
					if type(o) == "table" and o.srv == e.srv and o.uid == e.uid and o.kind == e.kind and o.act == e.act and (e.t - (o.t or 0)) <= (e.n or 1) * 10 + 10 then table.remove(list, i); break end
				end
				table.insert(list, e)
			end
			while #list > MAX do table.remove(list, 1) end
			return list
		end)
	end)
	if not ok then
		warn("[anticheat] log not stored: " .. tostring(err))
		for _, e in batch do table.insert(queue, e) end -- (try again next time)
		return
	end
	storedT = -math.huge
	local per: { [number]: { [string]: number } } = {}
	for _, e in batch do
		per[e.uid] = per[e.uid] or {}
		per[e.uid][e.kind] = (per[e.uid][e.kind] or 0) + (e.n or 1)
	end
	for uid, kinds in per do
		local u = users[uid]
		pcall(function()
			(store :: DataStore):UpdateAsync(USER_PREFIX .. uid, function(old: any)
				local r = if type(old) == "table" then old else { kicks = 0, points = 0, flags = {}, kickTimes = {} }
				r.flags = if type(r.flags) == "table" then r.flags else {}
				for k, n in kinds do r.flags[k] = (tonumber(r.flags[k]) or 0) + n end
				if u then
					r.points = (tonumber(r.points) or 0) + u.points
					r.kicks = (tonumber(r.kicks) or 0) + u.kicks
					if u.kicks > 0 then
						r.kickTimes = if type(r.kickTimes) == "table" then r.kickTimes else {}
						for _ = 1, u.kicks do table.insert(r.kickTimes, os.time()) end
						while #r.kickTimes > 20 do table.remove(r.kickTimes, 1) end
					end
				end
				r.last = os.time()
				return r
			end)
		end)
		if u then u.points = 0; u.kicks = 0 end
	end
end

-- kicks a player has had in the last `days` days, stored ones included (the auto-ban asks this)
function Log.kicksWithin(uid: number, days: number): number
	local r = Log.user(uid)
	local n = 0
	local u = users[uid]
	if u then n += u.kicks end
	if type(r) == "table" and type(r.kickTimes) == "table" then
		for _, t in r.kickTimes do if type(t) == "number" and os.time() - t <= days * 86400 then n += 1 end end
	end
	return n
end

task.spawn(function()
	while true do
		task.wait(FLUSH)
		Log.flush()
	end
end)
game:BindToClose(function() Log.flush() end)
Players.PlayerRemoving:Connect(function(p)
	local pre = p.UserId .. "|"
	for k in last do if string.sub(k, 1, #pre) == pre then last[k] = nil end end
end)

return Log
