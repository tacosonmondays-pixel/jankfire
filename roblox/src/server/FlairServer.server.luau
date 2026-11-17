--!strict
-- FLAIR on the server: kill effects and emotes (Shared.Flair; doc FLAIR.md).
--   * what you WEAR: one kill effect and the emote wheel's slots, saved in this script's own session-locked store
--     (JankfireFlair_v1, Profiles.luau). what you OWN is the loot save's (Loot.owns; the free ones everybody owns):
--     a saved pick you don't own stays saved but isn't worn.
--   * kill effects: on every kill in a match or the training hall (not the hub), the REAL killer's worn effect (the
--     server's own kill credit, Fight.onKill) plays on the victim's body for everyone: the body is frozen where it fell
--     (anchored, no collisions) in the same step as the death, and every client draws it (FlairKill -> KillFx.luau).
--     no effect for a fall into the void or the Shredder's own kill.
--   * emotes: checked here (alive, owned, on your wheel, not too soon), played by your own client (animations on your
--     own character replicate to everyone). anywhere: the hub, training, and matches (Rivals allows them mid-match;
--     the emoter's client hides enemies it can't see, so the third-person camera can't scout). your weapon is put away
--     while it plays; a shot, a death or a respawn ends it.
-- remote ReplicatedStorage.JankfireRemotes.Flair (RemoteFunction, made here if missing), always answers a table:
--   ("state")         -> { ok, kill, emotes = { 8 ids or "" }, owned = { kill = { ids }, emote = { ids } }, save }
--   ("kill", id)      -> wear a kill effect ("none" = the default)
--   ("grapple", id)   -> wear a grapple skin ("rope" = the default)
--   ("slot", i, id)   -> put an emote on wheel slot i (1..8; "" empties it; an emote may sit on several slots)
--   ("emote", id)     -> start one: { ok, len } / { ok = false, why }
--   ("stop")          -> end it
-- remote FlairKill (RemoteEvent, made here): { m = the body, fx = id, k = killer's UserId, from = where they stood } to
-- every client.
-- player attributes: KillFx (the worn effect), Grapple (the worn grapple skin), Emotes ("wave,salute,,,,,,"), Emote
-- (playing now, or nil), FlairSave.
-- Studio only: ServerStorage.JankFlairTest (BindableFunction):
--   ("fx", model, id)          an effect on any model, as a kill would (frozen + FlairKill)
--   ("kill", player, n|name)   you kill a training dummy, the n-th or the first whose name has it (the real path: Fight.hurt)
--   ("unlock", player, on)     wear anything this session (nothing saved), like Loot's dev unlock
--   ("state", player)          what the server has
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Jankfire = script.Parent
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Flair = require(Shared:WaitForChild("Flair")) :: any
local Fight = require(Jankfire:WaitForChild("Fight")) :: any
local Loot = require(Jankfire:WaitForChild("Loot")) :: any
local Profiles = require(Jankfire:WaitForChild("Profiles")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local function remote(name: string, class: string): any
	local r = Remotes:FindFirstChild(name)
	if not r then
		r = Instance.new(class)
		r.Name = name
		r.Parent = Remotes
	end
	return r
end
local Remote = remote("Flair", "RemoteFunction") :: RemoteFunction
local KillEvent = remote("FlairKill", "RemoteEvent") :: RemoteEvent

local store = Profiles.new("JankfireFlair_v1", function()
	return { v = 1, kill = Flair.DEFAULT.kill, grapple = Flair.DEFAULT.grapple, emotes = table.clone(Flair.DEFAULT.emotes) }
end)

type State = { prof: any, ready: boolean, emote: { id: string, t0: number, len: number, loop: boolean }?, last: number,
	budget: number, budgetT: number, devAll: boolean }
local st: { [Player]: State } = {}

-- ------------------------------------------------------------------ owning and wearing
local function owns(p: Player, t: string, id: string): boolean
	if Flair.isFree(t, id) then return true end
	if not Flair.info(t, id) then return false end
	local s = st[p]
	if s and s.devAll then return true end
	local ok, yes = pcall(Loot.owns, p, t, id)
	return ok and yes == true
end
local function dataOf(p: Player): any
	local s = st[p]
	return s and s.prof and s.prof.data
end
local function worn(p: Player): string
	local d = dataOf(p)
	local k = d and d.kill
	return if type(k) == "string" and Flair.info("kill", k) and owns(p, "kill", k) then k else "none"
end
-- the grapple skin worn (owned, else the plain rope): the player attribute Grapple, which every client's GrappleSkins reads
local function wornGrapple(p: Player): string
	local d = dataOf(p)
	local g = d and d.grapple
	return if type(g) == "string" and Flair.info("grapple", g) and owns(p, "grapple", g) then g else Flair.DEFAULT.grapple
end
local function slots(p: Player): { string }
	local d = dataOf(p)
	local out = {}
	for i = 1, Flair.SLOTS do
		local id = d and type(d.emotes) == "table" and d.emotes[i]
		if d == nil then id = Flair.DEFAULT.emotes[i] end
		out[i] = if type(id) == "string" and Flair.info("emote", id) and owns(p, "emote", id) then id else ""
	end
	return out
end
local function publish(p: Player)
	local s = st[p]
	if not s or not p.Parent then return end
	p:SetAttribute("KillFx", worn(p))
	p:SetAttribute("Grapple", wornGrapple(p))
	p:SetAttribute("Emotes", table.concat(slots(p), ","))
	p:SetAttribute("FlairSave", if not s.ready then "loading" elseif s.prof then s.prof.state else "off")
end
local function changed(p: Player)
	local s = st[p]
	if s and s.prof then s.prof.dirty = true end
	publish(p)
end

-- ------------------------------------------------------------------ emotes
local function holster(p: Player)
	local ch = p.Character
	if not ch then return end
	local hw = ch:FindFirstChild("HeldWeapon")
	if hw then hw:Destroy() end
	local hum = ch:FindFirstChildOfClass("Humanoid")
	if hum and ch:FindFirstChildOfClass("Tool") then hum:UnequipTools() end
end
local function endEmote(p: Player, reshow: boolean)
	local s = st[p]
	if not s or not s.emote then return end
	s.emote = nil
	if p.Parent then p:SetAttribute("Emote", nil) end
	if reshow then
		local f = Fight.byPlayer[p]
		if f and f.alive then Fight.showWeapon(f) end
	end
end
local function startEmote(p: Player, id: any): (boolean, string?, number?)
	local s = st[p]
	if not s then return false, "loading", nil end
	local e = Flair.info("emote", id)
	if not e or e.anim == "rbxassetid://0" then return false, "no such emote", nil end
	if not owns(p, "emote", id) then return false, "not owned", nil end
	if not table.find(slots(p), id) then return false, "not on your wheel", nil end
	local f = Fight.byPlayer[p]
	if not f or not f.alive then return false, "dead", nil end
	local now = os.clock()
	if now - s.last < Flair.COOLDOWN then return false, "too soon", nil end
	s.last = now
	s.emote = { id = id, t0 = now, len = e.len, loop = e.loop }
	p:SetAttribute("Emote", id)
	holster(p)
	return true, nil, e.len
end

-- ------------------------------------------------------------------ kill effects
-- the body freezes where it fell, in the same step as the death (before its joints break and it flies apart)
local function freeze(m: Model)
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = true
			d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
		end
	end
	m:SetAttribute("FlairFrozen", true)
end
local function playOn(m: Model, id: string, killer: number?, from: Vector3?)
	freeze(m)
	m:SetAttribute("KillFx", id)
	KillEvent:FireAllClients({ m = m, fx = id, k = killer, from = from })
end
local function onKill(info: any)
	local k, v = info.k, info.v
	if not k or k == v or k.kind ~= "player" then return end
	if info.w == "void" or info.w == "shredder" then return end
	local kp = k.ref :: Player
	if not kp.Parent or kp:GetAttribute("Zone") == "hub" then return end
	local id = worn(kp)
	if id == "none" then return end
	local m = Fight.model(v)
	if not m or not m.Parent then return end
	local kr = kp.Character and kp.Character:FindFirstChild("HumanoidRootPart") :: BasePart?
	playOn(m, id, kp.UserId, kr and kr.Position) -- (where the killer stood: Blast Zone throws the body away from them)
end

-- ------------------------------------------------------------------ the remote
local function spend(s: State): boolean
	local t = os.clock()
	s.budget = math.min(20, s.budget + (t - s.budgetT) * 5); s.budgetT = t
	if s.budget < 1 then return false end
	s.budget -= 1
	return true
end
local function ownedList(p: Player): any
	local out = { kill = {}, emote = {}, grapple = {} }
	for _, t in Flair.TYPES do
		for _, id in Flair.ORDER[t] do if owns(p, t, id) then table.insert(out[t], id) end end
	end
	return out
end

local function handle(p: Player, op: any, a: any, b: any): any
	local s = st[p]
	if not s then return { ok = false, why = "loading" } end
	-- (every request pays first, "state" too: nothing here answers for free)
	if not spend(s) then return { ok = false, why = "slow down" } end
	if op == "state" then
		local d = dataOf(p)
		return { ok = true, kill = worn(p), grapple = wornGrapple(p), emotes = slots(p), owned = ownedList(p),
			save = p:GetAttribute("FlairSave"), picked = d and d.kill or "none" }
	end
	if op == "emote" then
		local ok, why, len = startEmote(p, a)
		return { ok = ok, why = why, len = len }
	elseif op == "stop" then
		endEmote(p, true)
		return { ok = true }
	end
	local d = dataOf(p)
	if not s.ready or not d then return { ok = false, why = "loading" } end
	if op == "kill" then
		if type(a) ~= "string" or not Flair.info("kill", a) then return { ok = false, why = "no such kill effect" } end
		if not owns(p, "kill", a) then return { ok = false, why = "not owned" } end
		if d.kill ~= a then d.kill = a; changed(p) end
		return { ok = true }
	elseif op == "grapple" then
		if type(a) ~= "string" or not Flair.info("grapple", a) then return { ok = false, why = "no such grapple" } end
		if not owns(p, "grapple", a) then return { ok = false, why = "not owned" } end
		if d.grapple ~= a then d.grapple = a; changed(p) end
		return { ok = true }
	elseif op == "slot" then
		if type(a) ~= "number" or a ~= math.floor(a) or a < 1 or a > Flair.SLOTS then return { ok = false, why = "no such slot" } end
		if type(b) ~= "string" then return { ok = false, why = "nope" } end
		if b ~= "" then
			if not Flair.info("emote", b) then return { ok = false, why = "no such emote" } end
			if not owns(p, "emote", b) then return { ok = false, why = "not owned" } end
		end
		if type(d.emotes) ~= "table" then d.emotes = {} end
		for i = 1, Flair.SLOTS do if type(d.emotes[i]) ~= "string" then d.emotes[i] = "" end end
		if d.emotes[a] ~= b then d.emotes[a] = b; changed(p) end
		return { ok = true }
	end
	return { ok = false, why = "nope" }
end
Remote.OnServerInvoke = function(p: Player, op: any, a: any, b: any)
	local ok, res = pcall(handle, p, op, a, b)
	if not ok then warn("[jankfire] flair: " .. tostring(res)); return { ok = false, why = "error" } end
	return res
end

-- ------------------------------------------------------------------ players
local function added(p: Player)
	if st[p] then return end
	local s: State = { prof = nil, ready = false, emote = nil, last = -10, budget = 20, budgetT = os.clock(), devAll = false }
	st[p] = s
	publish(p)
	local prof = Profiles.load(store, "u" .. p.UserId, function() return p.Parent ~= nil and st[p] == s end)
	if not prof then return end
	if st[p] ~= s then Profiles.release(store, prof); return end
	-- (a save from before a new slot count or with junk in it: cleaned to the shape the server keeps)
	local d = prof.data
	if type(d.kill) ~= "string" then d.kill = Flair.DEFAULT.kill end
	if type(d.grapple) ~= "string" then d.grapple = Flair.DEFAULT.grapple end
	if type(d.emotes) ~= "table" then d.emotes = table.clone(Flair.DEFAULT.emotes) end
	for i = 1, Flair.SLOTS do if type(d.emotes[i]) ~= "string" then d.emotes[i] = "" end end
	s.prof = prof
	s.ready = true
	prof.onLost.Event:Connect(function() publish(p) end)
	publish(p)
end

for _, p in Players:GetPlayers() do task.spawn(added, p) end
Players.PlayerAdded:Connect(added)
Players.PlayerRemoving:Connect(function(p)
	local s = st[p]
	st[p] = nil
	if s and s.prof then Profiles.release(store, s.prof) end
end)
if Loot.changed then Loot.changed:Connect(function(p: Player) task.defer(publish, p) end) end

-- (a slip in here must never break a shot, a hit or a death: every hook runs in a pcall)
local function safe(fn: any): any
	return function(...)
		local ok, err = pcall(fn, ...)
		if not ok then warn("[jankfire] flair: " .. tostring(err)) end
	end
end
Fight.onKill(safe(function(info: any)
	if info.v and info.v.kind == "player" then endEmote(info.v.ref :: Player, false) end
	onKill(info)
end))
Fight.onShot(safe(function(f: any, _wid: string)
	if f.kind == "player" then endEmote(f.ref :: Player, false) end -- (the shot already has its weapon out)
end))
Fight.onSpawn(safe(function(f: any)
	if f.kind == "player" then endEmote(f.ref :: Player, false) end
end))

-- an emote ends on its own (one-shots after their length; a loop after 30 s), and the weapon stays away while it plays
local acc = 0
RunService.Heartbeat:Connect(function(dt: number)
	acc += dt
	if acc < 0.2 then return end
	acc = 0
	local now = os.clock()
	for p, s in st do
		local e = s.emote
		if e then
			if now - e.t0 > (if e.loop then 30 else e.len + 0.6) then endEmote(p, true)
			else holster(p) end
		end
	end
end)

-- ------------------------------------------------------------------ Studio test hook
if RunService:IsStudio() then
	local SS = game:GetService("ServerStorage")
	local old = SS:FindFirstChild("JankFlairTest")
	if old then old:Destroy() end
	local bf = Instance.new("BindableFunction")
	bf.Name = "JankFlairTest"
	bf.OnInvoke = function(op: string, a: any, b: any): any
		if op == "fx" then
			if typeof(a) ~= "Instance" or not a:IsA("Model") or not Flair.info("kill", b) then return "need a model and an effect id" end
			playOn(a, b, nil)
			return "played " .. b .. " on " .. a:GetFullName()
		elseif op == "kill" then
			local p = a :: Player
			local f = Fight.byPlayer[p]
			local list = {}
			for _, x in Fight.all do if x.kind == "dummy" and x.alive then table.insert(list, x) end end
			local t = list[tonumber(b) or 1]
			if type(b) == "string" and not tonumber(b) then
				t = nil
				for _, x in list do if string.find(x.name, b, 1, true) then t = x; break end end
			end
			if not f or not t then return "no fighter or no live dummy (" .. #list .. " live)" end
			local done = Fight.hurt(t, 99999, f, "ar", false)
			return ("hurt %s for %s; KillFx = %s"):format(t.name, tostring(done), worn(p))
		elseif op == "unlock" then
			local s = st[a]
			if not s then return "no player" end
			s.devAll = b ~= false
			publish(a)
			return "unlock " .. tostring(s.devAll)
		elseif op == "state" then
			local s = st[a]
			if not s then return "no player" end
			local d = dataOf(a)
			return ("ready=%s save=%s kill=%s worn=%s grapple=%s slots=%s emote=%s"):format(tostring(s.ready), tostring(a:GetAttribute("FlairSave")),
				tostring(d and d.kill), worn(a), wornGrapple(a), table.concat(slots(a), ","), tostring(s.emote and s.emote.id))
		end
		return "ops: fx, kill, unlock, state"
	end
	bf.Parent = SS
end
