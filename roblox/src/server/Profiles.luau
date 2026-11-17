--!strict
-- one save per player that only ONE server may write at a time (a session lock), the job ProfileStore does, written
-- here so the game has no outside code in it. Loot.luau keeps everything you own in one of these.
--
-- why a lock: with a plain DataStore a player who hops servers can be saved by the old server AFTER the new one loaded
-- them, and whatever the new server gave them is lost (or two servers both hand out the same thing). here:
--   * loading writes a lock { sid, t } into the save itself (UpdateAsync). sid is new for every load.
--   * a save (autosave every AUTOSAVE s, on leave, on shutdown) only writes if the lock in the store is still ours;
--     every save renews the lock's time.
--   * a load that finds someone else's lock waits for it to be let go (the old server lets go when you leave it,
--     within a second or two). a lock not renewed for STALE s belongs to a dead server: we take it. after WAIT s we
--     take it anyway (Roblox has moved the player here; the old server's next save sees it lost the lock and stops).
--   * a server that finds its lock taken stops writing for good and tells its owner (onLost).
-- Studio without API access (Game Settings > Security): profiles run in memory and say so ("off"); nothing is saved.
local DataStoreService = game:GetService("DataStoreService")
local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")

local Profiles = {}

local AUTOSAVE = 60 -- s between saves of a profile that changed (and lock renewals)
local STALE = if RunService:IsStudio() then 20 else 240 -- s: a lock this old is a dead server's
local WAIT = if RunService:IsStudio() then 8 else 45 -- s of waiting for a live lock before taking it
local SERVER = HttpService:GenerateGUID(false) -- (JobId is "" in Studio)

export type Profile = {
	key: string, data: any, state: string, -- "cloud" | "off" (in memory) | "lost" | "released"
	sid: string, dirty: boolean, lastSave: number, busy: boolean,
	onLost: BindableEvent,
}
export type Store = { name: string, ds: DataStore?, template: () -> any, live: { [Profile]: boolean } }

local function deepCopy(t: any): any
	if type(t) ~= "table" then return t end
	local o = {}
	for k, v in t do o[k] = deepCopy(v) end
	return o
end

-- fill what a template has and an old save lacks (new fields added after the save was made)
local function fill(data: any, tpl: any)
	for k, v in tpl do
		if data[k] == nil then data[k] = deepCopy(v)
		elseif type(v) == "table" and type(data[k]) == "table" then fill(data[k], v) end
	end
end

local function retry(fn: () -> any, tries: number?): (boolean, any)
	local err: any = nil
	for i = 1, tries or 3 do
		local ok, res = pcall(fn)
		if ok then return true, res end
		err = res
		if i < (tries or 3) then task.wait(i) end
	end
	return false, err
end

local stores: { Store } = {}

function Profiles.new(name: string, template: () -> any): Store
	-- Studio saves into its own stores ("<name>_studio"), never the live game's (17 Nov 2026, after the first publish:
	-- a Studio play test loads the owner's save, takes its lock after WAIT s, and the live server that had the owner
	-- lost the lock and kicked them: "it keeps kicking me from my own game")
	if RunService:IsStudio() then name ..= "_studio" end
	local ds: DataStore? = nil
	local ok, s = pcall(function() return DataStoreService:GetDataStore(name) end)
	if ok then ds = s end
	local st: Store = { name = name, ds = ds, template = template, live = {} }
	table.insert(stores, st)
	return st
end

local function memory(st: Store, key: string, why: string): Profile
	warn(("[jankfire] %s: %s runs in memory this session (%s). in Studio: Game Settings > Security > Enable Studio Access to API Services"):format(st.name, key, why))
	local p: Profile = { key = key, data = st.template(), state = "off", sid = "", dirty = false, lastSave = os.clock(), busy = false, onLost = Instance.new("BindableEvent") }
	st.live[p] = true
	return p
end

-- load and lock. returns the profile, or nil if `still()` turned false while it waited (the player left).
-- a store that can't be reached gives an in-memory profile (state "off")
function Profiles.load(st: Store, key: string, still: () -> boolean): Profile?
	if not st.ds then return memory(st, key, "no DataStoreService") end
	local ds = st.ds :: DataStore
	local sid = SERVER .. ":" .. HttpService:GenerateGUID(false)
	local t0 = os.clock()
	while true do
		if not still() then return nil end
		local got: any = nil
		local held = false
		local ok, err = retry(function()
			return ds:UpdateAsync(key, function(old: any)
				got, held = nil, false
				local d = if type(old) == "table" then old else {}
				local lock = d.lock
				local now = os.time()
				if type(lock) == "table" and type(lock.sid) == "string" and lock.sid ~= sid and type(lock.t) == "number"
					and now - lock.t < STALE and os.clock() - t0 < WAIT then
					held = true
					return nil -- (someone else's: leave it as it is)
				end
				d.lock = { sid = sid, t = now }
				got = d
				return d
			end)
		end)
		if not ok then return memory(st, key, tostring(err)) end
		if got then
			local data = got
			data.lock = nil
			fill(data, st.template())
			local p: Profile = { key = key, data = data, state = "cloud", sid = sid, dirty = false, lastSave = os.clock(), busy = false, onLost = Instance.new("BindableEvent") }
			if not still() then
				-- (they left while it loaded: let go of the lock at once)
				st.live[p] = true
				Profiles.release(st, p)
				return nil
			end
			st.live[p] = true
			return p
		end
		if held then task.wait(if RunService:IsStudio() then 1 else 4) end
	end
end

-- write the profile if it is still ours. release = let go of the lock too. returns whether it was written
function Profiles.save(st: Store, p: Profile, release: boolean?): boolean
	if p.state ~= "cloud" or not st.ds then
		if release and p.state == "off" then p.state = "released"; st.live[p] = nil end
		return p.state == "off"
	end
	local ds = st.ds :: DataStore
	-- one write at a time per profile (two in flight could land out of order): wait for the one going
	local w0 = os.clock()
	while p.busy and os.clock() - w0 < 30 do task.wait(0.1) end
	if p.state ~= "cloud" then return false end
	p.busy = true
	local lost = false
	local payload = deepCopy(p.data)
	p.dirty = false
	local ok, err = retry(function()
		return ds:UpdateAsync(p.key, function(old: any)
			lost = false
			local lock = if type(old) == "table" then old.lock else nil
			if type(lock) ~= "table" or lock.sid ~= p.sid then
				lost = true
				return nil -- not ours any more: write nothing
			end
			payload.lock = if release then nil else { sid = p.sid, t = os.time() }
			return payload
		end)
	end)
	p.busy = false
	if not ok then
		p.dirty = true
		warn(("[jankfire] %s: couldn't save %s: %s"):format(st.name, p.key, tostring(err)))
		return false
	end
	p.lastSave = os.clock()
	if lost then
		p.state = "lost"
		st.live[p] = nil
		warn(("[jankfire] %s: %s was opened by another server; this one stops writing it"):format(st.name, p.key))
		p.onLost:Fire()
		return false
	end
	if release then p.state = "released"; st.live[p] = nil end
	return true
end

function Profiles.release(st: Store, p: Profile)
	if p.state == "cloud" or p.state == "off" then Profiles.save(st, p, true) end
end

-- autosave: a changed profile every AUTOSAVE s; an unchanged one renews its lock every AUTOSAVE * 2 s
local acc = 0
RunService.Heartbeat:Connect(function(dt)
	acc += dt
	if acc < 2 then return end
	acc = 0
	local now = os.clock()
	for _, st in stores do
		for p in st.live do
			if p.state == "cloud" and ((p.dirty and now - p.lastSave >= AUTOSAVE) or now - p.lastSave >= AUTOSAVE * 2) then
				p.lastSave = now
				task.spawn(Profiles.save, st, p)
			end
		end
	end
end)

-- shutting down: every live profile is saved and let go
game:BindToClose(function()
	local left = 0
	for _, st in stores do
		for p in st.live do
			left += 1
			task.spawn(function() Profiles.release(st, p); left -= 1 end)
		end
	end
	local t0 = os.clock()
	while left > 0 and os.clock() - t0 < 25 do task.wait(0.1) end
end)

return Profiles
