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
--   ("pet", id)       -> wear a pet you have found ("" = none)
--   ("petseen", ids)  -> the picker showed these NEW pets (18 Nov); "state" also sends petsAt (the order found) and petsNew
-- PETS (18 Nov 2026): found only (server/PetSecrets.server.luau finds them), owned in THIS save (d.pets), never the loot
-- save, so the shop and the bags never see them. the worn one is the player attribute Pet (every client's Pets.client
-- draws it). script.PetOps (BindableFunction, for the server's own scripts):
--   ("grant", p, id)   -> "found" (the first time: saved, worn if you wore none, "NEW PET · <NAME>" and its sound for
--                         you alone), "owned", "loading" (the save isn't in yet: try again), "no such pet"
--   ("owns", p, id)    -> true / false
--   ("bump", p, key)   -> one more of a saved count (d.seen[key]: how many times the train passed you), the new count
--                         (nil while loading)
-- player attributes: KillFx (the worn effect), Grapple (the worn grapple skin), Emotes ("wave,salute,,,,,,"), Emote
-- (playing now, or nil), Pet (the worn pet, or nil), FlairSave.
-- Studio only: ServerStorage.JankFlairTest (BindableFunction):
--   ("fx", model, id)          an effect on any model, as a kill would (frozen + FlairKill)
--   ("kill", player, n|name)   you kill a training dummy, the n-th or the first whose name has it (the real path: Fight.hurt)
--   ("unlock", player, on)     wear anything this session (nothing saved), like Loot's dev unlock
--   ("state", player)          what the server has
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local InsertService = game:GetService("InsertService")
local HttpService = game:GetService("HttpService")

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
	return { v = 2, kill = Flair.DEFAULT.kill, grapple = Flair.DEFAULT.grapple, emotes = table.clone(Flair.DEFAULT.emotes), pet = "", pets = {}, seen = {},
		freeSeen = {} }
end)

type State = { prof: any, ready: boolean, emote: { id: string, t0: number, len: number, loop: boolean }?, last: number,
	budget: number, budgetT: number, devAll: boolean, rbx: { [string]: number }? }
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
-- pets: found ones are in the save (d.pets[id] = true); the dev unlock wears any
local function ownsPet(p: Player, id: string): boolean
	if not Flair.pet(id) then return false end
	local s = st[p]
	if s and s.devAll then return true end
	local d = dataOf(p)
	return d ~= nil and type(d.pets) == "table" and d.pets[id] == true
end
local function wornPet(p: Player): string?
	local d = dataOf(p)
	local id = d and d.pet
	return if type(id) == "string" and id ~= "" and ownsPet(p, id) then id else nil
end
local function publish(p: Player)
	local s = st[p]
	if not s or not p.Parent then return end
	p:SetAttribute("Pet", wornPet(p))
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
-- a catalog emote's body animation (InsertService:LoadAsset; Roblox's and creators' emotes both load), kept for everyone
local rbxAnim: { [number]: string | false } = {}
local function animOf(asset: number): string?
	local c = rbxAnim[asset]
	if c ~= nil then return if c then c else nil end
	local ok, m = pcall(InsertService.LoadAsset, InsertService, asset)
	local id: string? = nil
	if ok and m then
		local a = m:FindFirstChildWhichIsA("Animation", true)
		if a and a.AnimationId ~= "" then id = a.AnimationId end
		m:Destroy()
	end
	rbxAnim[asset] = id or false
	return id
end
local function startEmote(p: Player, id: any): (boolean, string?, number?, string?)
	local s = st[p]
	if not s then return false, "loading", nil end
	-- one of your own Roblox emotes (the wheel's second page): it has to be on your avatar, read by readRbx below
	local mine = if type(id) == "string" and string.sub(id, 1, 4) == "rbx:" and s.rbx then s.rbx[string.sub(id, 5)] else nil
	local e = if mine then nil else Flair.info("emote", id)
	if not mine then
		if not e or e.anim == "rbxassetid://0" then return false, "no such emote", nil end
		if not owns(p, "emote", id) then return false, "not owned", nil end
		if not table.find(slots(p), id) then return false, "not on your wheel", nil end
	end
	local f = Fight.byPlayer[p]
	if not f or not f.alive then return false, "dead", nil end
	local now = os.clock()
	if now - s.last < Flair.COOLDOWN then return false, "too soon", nil end
	s.last = now
	-- (your own: its animation is read out of the catalog emote the first time anyone plays it, then kept)
	local anim = if mine then animOf(mine) else nil
	if mine and not anim then return false, "can't play that one", nil end
	-- (your own: its length is the clip's, which the client reads off the track and says stop at; here only a cap)
	s.emote = if mine then { id = id, t0 = now, len = 30, loop = true } else { id = id, t0 = now, len = e.len, loop = e.loop }
	p:SetAttribute("Emote", id)
	holster(p)
	if mine then return true, nil, nil, anim end
	return true, nil, e.len
end

-- ------------------------------------------------------------------ your own Roblox emotes
-- the emotes on your Roblox avatar (the ones you bought, StarterPlayer.UserEmotesEnabled), read from the description
-- your character was built from once its look has loaded: the ones you have equipped on Roblox first (by their slot),
-- then the rest by name, up to MAX_RBX (the wheel shows them 8 to a page). published as the player's RbxEmotes
-- attribute: JSON [{ n = name, a = catalog asset id }] for the wheel's pictures and names. each one's animation is read
-- when it's first played (startEmote)
local MAX_RBX = 96
local function readRbx(p: Player)
	local s = st[p]
	local ch = p.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	if not s or not hum then return end
	local ok, desc = pcall(hum.GetAppliedDescription, hum)
	if not ok or not desc then return end
	local okE, emotes = pcall(desc.GetEmotes, desc)
	if not okE or type(emotes) ~= "table" then return end
	local okQ, equipped = pcall(desc.GetEquippedEmotes, desc)
	local order, seen = {}, {}
	if okQ and type(equipped) == "table" then
		table.sort(equipped, function(a: any, b: any) return (tonumber(a.Slot) or 99) < (tonumber(b.Slot) or 99) end)
		for _, q in equipped do
			if type(q.Name) == "string" and emotes[q.Name] and not seen[q.Name] then seen[q.Name] = true; table.insert(order, q.Name) end
		end
	end
	local rest = {}
	for name in emotes do if type(name) == "string" and not seen[name] then table.insert(rest, name) end end
	table.sort(rest, function(a: string, b: string) return string.lower(a) < string.lower(b) end)
	for _, n in rest do table.insert(order, n) end
	local list, map = {}, {}
	for _, name in order do
		if #list >= MAX_RBX then break end
		local ids = emotes[name]
		local asset = type(ids) == "table" and tonumber(ids[1]) or nil
		if asset then
			map[name] = asset
			table.insert(list, { n = name, a = asset })
		end
	end
	if st[p] ~= s or not p.Parent then return end
	s.rbx = map
	p:SetAttribute("RbxEmotes", HttpService:JSONEncode(list))
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
-- the new free emotes (Flair EMOTES' NEW column) this player has looked at: no NEW dot on those (19 Nov)
local function freeSeenList(p: Player): { string }
	local d = dataOf(p)
	local out = {}
	if d and type(d.freeSeen) == "table" then for id, v in d.freeSeen do if v == true then table.insert(out, id) end end end
	return out
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
		local pets, petsNew = {}, {}
		for _, id in Flair.PET_ORDER do if ownsPet(p, id) then table.insert(pets, id) end end
		if d and type(d.petsNew) == "table" then for id in d.petsNew do if ownsPet(p, id) then table.insert(petsNew, id) end end end
		return { ok = true, kill = worn(p), grapple = wornGrapple(p), emotes = slots(p), owned = ownedList(p),
			save = p:GetAttribute("FlairSave"), picked = d and d.kill or "none", pets = pets, pet = wornPet(p) or "",
			petsAt = if d and type(d.petsAt) == "table" then d.petsAt else {}, petsNew = petsNew, freeSeen = freeSeenList(p) }
	end
	if op == "freeseen" then
		-- (the picker showed these new free emotes: their NEW dots go. 19 Nov)
		local d = dataOf(p)
		if d and type(a) == "table" then
			if type(d.freeSeen) ~= "table" then d.freeSeen = {} end
			for i, id in ipairs(a) do
				if i > 40 then break end
				local e = type(id) == "string" and Flair.info("emote", id)
				if e and e.new then d.freeSeen[id] = true end
			end
			if s.prof then s.prof.dirty = true end
		end
		return { ok = true }
	end
	if op == "petseen" then
		-- (the picker showed these NEW pets: no NEW dot on them from now on. 18 Nov)
		local d = dataOf(p)
		if d and type(d.petsNew) == "table" and type(a) == "table" then
			for i, id in ipairs(a) do
				if i > 20 then break end
				if type(id) == "string" then d.petsNew[id] = nil end
			end
			if s.prof then s.prof.dirty = true end
		end
		return { ok = true }
	end
	if op == "emote" then
		local ok, why, len, anim = startEmote(p, a)
		return { ok = ok, why = why, len = len, anim = anim }
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
	elseif op == "pet" then
		if a ~= "" and not Flair.pet(a) then return { ok = false, why = "no such pet" } end
		if a ~= "" and not ownsPet(p, a) then return { ok = false, why = "not found yet" } end
		if d.pet ~= a then d.pet = a; changed(p) end
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
	-- (an emote or kill effect taken out of the game leaves its slot empty, not an error: 17 Nov, Groove, Fist Pump, Bow)
	for i = 1, Flair.SLOTS do if d.emotes[i] ~= "" and not Flair.info("emote", d.emotes[i]) then d.emotes[i] = "" end end
	if not Flair.info("kill", d.kill) then d.kill = Flair.DEFAULT.kill end
	if not Flair.info("grapple", d.grapple) then d.grapple = Flair.DEFAULT.grapple end
	if type(d.pet) ~= "string" then d.pet = "" end
	if type(d.pets) ~= "table" then d.pets = {} end
	if type(d.seen) ~= "table" then d.seen = {} end
	if type(d.freeSeen) ~= "table" then d.freeSeen = {} end
	-- (v2, 17 Nov: Roblox's free emotes are the starter set: a wheel saved before then gets them in its empty slots)
	if (tonumber(d.v) or 1) < 2 then
		for _, id in Flair.DEFAULT.emotes do
			if id ~= "" and not table.find(d.emotes, id) then
				local i = table.find(d.emotes, "")
				if i then d.emotes[i] = id end
			end
		end
		d.v = 2
	end
	s.prof = prof
	s.ready = true
	prof.onLost.Event:Connect(function() publish(p) end)
	publish(p)
end

for _, p in Players:GetPlayers() do task.spawn(added, p) end
Players.PlayerAdded:Connect(added)
-- your own Roblox emotes, read each time your character's look is in (and once for anyone already here)
local function watchLook(p: Player)
	local function soon()
		-- (once the character's look is in: before that its description has no emotes)
		local t0 = os.clock()
		while p.Parent and not p:HasAppearanceLoaded() and os.clock() - t0 < 15 do task.wait(0.25) end
		task.wait(0.5)
		readRbx(p)
	end
	p.CharacterAdded:Connect(function() task.spawn(soon) end)
	p.CharacterAppearanceLoaded:Connect(function() task.spawn(readRbx, p) end)
	if p.Character then task.spawn(soon) end
end
for _, p in Players:GetPlayers() do watchLook(p) end
Players.PlayerAdded:Connect(watchLook)
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

-- ------------------------------------------------------------------ pets: the finds (PetSecrets asks through PetOps)
local CalloutR = Remotes:WaitForChild("Callout", 10) :: RemoteEvent?
-- the find's recording, on the finder's screen only (a copy in their PlayerGui: nobody else hears it), like the hub egg's
local function foundSound(p: Player, id: string)
	local kit = ReplicatedStorage:FindFirstChild("JankfirePets")
	local m = kit and kit:FindFirstChild(id)
	local snd = m and m:FindFirstChild("Found")
	local pg = p:FindFirstChildOfClass("PlayerGui")
	if not (snd and snd:IsA("Sound") and pg) then return end
	local c = snd:Clone()
	c.Parent = pg
	c:Play()
	local len = if c.PlaybackRegionsEnabled then c.PlaybackRegion.Max - c.PlaybackRegion.Min else c.TimeLength
	task.delay(math.max(2, len + 0.5), function() c:Destroy() end)
end
local function grantPet(p: Player, id: string): string
	local info = Flair.pet(id)
	if not info then return "no such pet" end
	local s = st[p]
	local d = dataOf(p)
	if not s or not s.ready or not d then return "loading" end
	if type(d.pets) ~= "table" then d.pets = {} end
	if d.pets[id] == true then return "owned" end
	d.pets[id] = true
	-- (newest first and NEW in the picker, 18 Nov, shop-gui: the order pets were found in, and the ones the picker hasn't
	-- shown yet; "state" sends both, "petseen" clears)
	d.petsN = (tonumber(d.petsN) or 0) + 1
	d.petsAt = if type(d.petsAt) == "table" then d.petsAt else {}
	d.petsAt[id] = d.petsN
	d.petsNew = if type(d.petsNew) == "table" then d.petsNew else {}
	d.petsNew[id] = true
	if type(d.pet) ~= "string" or d.pet == "" then d.pet = id end -- (your first pet comes along at once)
	changed(p)
	if CalloutR then CalloutR:FireClient(p, "NEW PET · " .. string.upper(info.name), 2.8) end
	foundSound(p, id)
	return "found"
end
local PetOps = script:FindFirstChild("PetOps") :: BindableFunction?
if not PetOps then
	local b = Instance.new("BindableFunction")
	b.Name = "PetOps"
	b.Parent = script
	PetOps = b
end
(PetOps :: BindableFunction).OnInvoke = function(op: any, p: any, a: any): any
	if typeof(p) ~= "Instance" or not p:IsA("Player") then return nil end
	if op == "grant" then return grantPet(p, a)
	elseif op == "owns" then return ownsPet(p, a)
	elseif op == "bump" then
		local s = st[p]
		local d = dataOf(p)
		if not s or not s.ready or not d or type(a) ~= "string" then return nil end
		if type(d.seen) ~= "table" then d.seen = {} end
		d.seen[a] = (tonumber(d.seen[a]) or 0) + 1
		changed(p)
		return d.seen[a]
	elseif op == "count" then
		local d = dataOf(p)
		return d and type(d.seen) == "table" and tonumber(d.seen[a]) or 0
	elseif op == "forget" then -- (Studio tests only: lose a pet again, or every pet and count with "all")
		if not RunService:IsStudio() then return nil end
		local d = dataOf(p)
		if not d then return "loading" end
		if a == "all" then d.pets = {}; d.seen = {}; d.pet = "" elseif type(d.pets) == "table" then d.pets[a] = nil end
		if d.pet ~= "" and not (type(d.pets) == "table" and d.pets[d.pet]) then d.pet = "" end
		changed(p)
		return "forgot " .. tostring(a)
	end
	return nil
end

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
