--!strict
-- your settings (the page on P), kept per player in their own save (JankfireSettings_v1, Profiles.luau: session-locked
-- like the loot, flair and stats saves) and handed to your client when you join. the client (Settings.luau) holds the
-- values and applies them; this script only keeps them. what's stored: the settings that differ from the defaults, as
-- key -> number / boolean / short string. nothing here changes a fight: sensitivity, crosshair, sound, graphics and
-- HUD are yours alone.
--   remote JankfireRemotes.Settings (RemoteFunction):
--     ("load")         -> { ok, state = "cloud" | "off", data = { key = value } }  (waits for the save, up to 20 s)
--     ("save", data)   -> { ok }  (the whole table of changed settings; checked: at most MAX keys, short keys, plain values)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Jankfire = script.Parent
local Profiles = require(Jankfire:WaitForChild("Profiles")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local MAX = 200 -- keys in one save (there are about 90 settings and binds)
local MAX_STR = 64
local MIN_GAP = 0.5 -- s between two saves from one player

local Remote = Remotes:FindFirstChild("Settings")
if not Remote then
	Remote = Instance.new("RemoteFunction")
	Remote.Name = "Settings"
	Remote.Parent = Remotes
end

local store = Profiles.new("JankfireSettings_v1", function()
	return { v = 1, s = {} }
end)

type State = { prof: any, ready: boolean, lastSave: number }
local st: { [Player]: State } = {}

-- a client's table, cleaned: only short keys and plain values
local function clean(t: any): { [string]: any }?
	if type(t) ~= "table" then return nil end
	local out = {}
	local n = 0
	for k, v in t do
		if type(k) ~= "string" or #k > 40 or not string.match(k, "^[%w%._]+$") then return nil end
		local tv = type(v)
		if tv == "number" then
			if v ~= v or v == math.huge or v == -math.huge then return nil end
		elseif tv == "string" then
			if #v > MAX_STR then return nil end
		elseif tv ~= "boolean" then
			return nil
		end
		n += 1
		if n > MAX then return nil end
		out[k] = v
	end
	return out
end

local function handle(p: Player, op: any, a: any): any
	local s = st[p]
	if not s then return { ok = false, why = "not here" } end
	if op == "load" then
		local t0 = os.clock()
		while not s.ready and st[p] == s and os.clock() - t0 < 20 do task.wait(0.2) end
		if not s.ready or not s.prof then return { ok = false, why = "not loaded" } end
		return { ok = true, state = s.prof.state, data = table.clone(s.prof.data.s) }
	elseif op == "save" then
		if not s.ready or not s.prof then return { ok = false, why = "not loaded" } end
		local now = os.clock()
		if now - s.lastSave < MIN_GAP then return { ok = false, why = "too fast" } end
		local d = clean(a)
		if not d then return { ok = false, why = "bad settings" } end
		s.lastSave = now
		s.prof.data.s = d
		s.prof.dirty = true
		return { ok = true }
	end
	return { ok = false, why = "nope" }
end
(Remote :: RemoteFunction).OnServerInvoke = function(p: Player, op: any, a: any)
	local ok, res = pcall(handle, p, op, a)
	if not ok then warn("[jankfire] settings: " .. tostring(res)); return { ok = false, why = "error" } end
	return res
end

local function added(p: Player)
	if st[p] then return end
	local s: State = { prof = nil, ready = false, lastSave = 0 }
	st[p] = s
	local prof = Profiles.load(store, "u" .. p.UserId, function() return p.Parent ~= nil and st[p] == s end)
	if not prof then return end
	if st[p] ~= s then Profiles.release(store, prof); return end
	if type(prof.data.s) ~= "table" then prof.data.s = {} end
	prof.data.s = clean(prof.data.s) or {}
	s.prof = prof
	s.ready = true
end

for _, p in Players:GetPlayers() do task.spawn(added, p) end
Players.PlayerAdded:Connect(added)
Players.PlayerRemoving:Connect(function(p)
	local s = st[p]
	st[p] = nil
	if s and s.prof then Profiles.release(store, s.prof) end
end)
