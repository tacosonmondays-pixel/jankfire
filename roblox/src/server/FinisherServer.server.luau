--!strict
-- FINISHERS on the server (shared/Finishers.luau; roblox/docs/FINISHERS.md). It watches the kills and the rounds:
--   * a round won within Finishers.FRESH s of its last kill, by the killer's team, the killer still standing, the victim
--     a player, the killer's skin on the weapon that killed owning a finisher -> the WORLD finisher on the victim's body
--     for everyone in the match (no camera: client/FinisherWorld.luau); when that round wins the match -> the full cut
--     (or its scene) to everyone in the match, the end screen waiting for it. (The short cut between rounds is retired,
--     20 Nov: "finisher cutscene should only play when you get the final hit on the game winning round")
--   * a classic mode's end (Matches.finish) right after its last kill -> the full cut to everyone in it
--   * a round that leaves a team one win from the match, or a classic mode's start -> { kind = "warm", scenes } to
--     everyone in it: the scenes its end could bring, their sets built ahead on the clients (no hitch at the start)
-- What it sends (JankfireRemotes.Finisher, made here if missing): the last Finishers.LEAD s of the match recording
-- (Recorder.recent), cut down to the killer and the victim, plus who's who. The camera, the bodies and the effects are
-- the client's (client/Finisher.luau). Nothing here holds a round or a match: the cuts fit the windows that are already
-- there (the 3 s between rounds, the end screen), and the client ends one early when a round starts.
-- Studio only: ServerStorage.JankFinisherTest (BindableFunction):
--   ("arm", player, skinId?, kind?, all?)  the player's next kill plays that skin's finisher ("full" | "short"), to the
--                                         player (all = true: to everyone in the server), whatever they wear
--   ("kill", player, n|name, weapon?)      kill a live training dummy now through Fight.hurt (with that weapon, default ar)
--   ("decide", table)                      Finishers.decide on a table
--   ("world", player, skin, n|name)        a WORLD finisher of that skin on a live training dummy's body, to the player
--                                         (the dummy stands frozen as it is; photos and checks)
--   ("state")                              what is armed, the last kill of each live match
--   ("round", player, "full"|"short", skin, ends) the MATCH PATH with one tester: the real round handler (the function
--                                         Matches.onRound calls) on the player's real match (JankMatchTest "ghost"
--                                         with the player on team 1) and the player's real last kill in it (a training
--                                         dummy, counted as a player for this test only); "full" = that round wins the
--                                         match, "short" = it doesn't. Only Matches' own call is left out: a round
--                                         ends on a kill of a real second player, which one tester can't make.
--                                         ends = true: a "full" one then ends the match as Matches' round handler does
--                                         (Matches.finish 1.2 s on: the end screen and the trip home after the scene)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Jankfire = script.Parent
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Finishers = require(Shared:WaitForChild("Finishers")) :: any
local GunSkins = require(Shared:WaitForChild("GunSkins")) :: any
local Weapons = require(Shared:WaitForChild("Weapons")) :: any
local Fight = require(Jankfire:WaitForChild("Fight")) :: any
local Matches = require(Jankfire:WaitForChild("Matches")) :: any
local Recorder = require(Jankfire:WaitForChild("Recorder")) :: any
-- (27 Nov: the cutscene as the match's victory scene - its best winner's finisher against the enemy best, asked for by
-- the victory scene; filled in below)
local FV = require(Jankfire:WaitForChild("FinisherVictory")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local remote = Remotes:FindFirstChild("Finisher") :: RemoteEvent?
if not remote then
	local r = Instance.new("RemoteEvent")
	r.Name = "Finisher"
	r.Parent = Remotes
	remote = r
end
local R = remote :: RemoteEvent

type Kill = { k: any, v: any, w: string, t: number, skin: string?, fid: string? }
local lastKill: { [any]: Kill } = {} -- each live match's last kill by a player
-- each match's kills per player per weapon (which equipped finisher a player brings to the victory scene)
local killsBy: { [any]: { [Player]: { [string]: number } } } = setmetatable({}, { __mode = "k" }) :: any
local played: { [any]: boolean } = {} -- matches whose last round already played the full cut
-- the viewers of a match's full cut who haven't reported their scene done yet (Matches.endMatch holds the end screen
-- on m.finisherUntil: the scene's length + HOLD_SLACK s at most, brought in when this set empties)
local watching: { [any]: { [Player]: boolean } } = {}
-- (the cap: the scene's length + HOLD_SLACK s. A client starts its scene a little after the server sends it - the clip
-- over the network, the ghosts built - so the cap leaves room for that; it is only reached if a viewer never reports)
local HOLD_SLACK = 4
local function holdFor(m: any, fid: string, viewers: { Player })
	local len = Finishers.length("full", false, Finishers.LIST[fid])
	local t0 = os.clock()
	m.finisherUntil = t0 + len + HOLD_SLACK
	m.finisherFrom = t0
	local set = {}
	for _, p in viewers do set[p] = true end
	watching[m] = set
	-- (the live cut-off hunt, 20 Nov: the server's console says how the hold ended)
	task.delay(len + HOLD_SLACK + 0.1, function()
		local left = watching[m]
		if left and next(left) then
			local names = {}
			for p in left do table.insert(names, p.Name) end
			print(("[jankfire] FinisherHold: the cap ended it after %.1f s, still playing for %s"):format(os.clock() - t0, table.concat(names, ", ")))
		end
	end)
end
local armed: { [Player]: { skin: string?, kind: string, all: boolean } } = {} -- (Studio tests)

-- the weapon a kill counts as (a parry is the katana's)
local function weaponOf(w: string): string
	return if w == "parry" then "katana" else w
end
local function isMelee(w: string): boolean
	local row = Weapons.list[w]
	return row ~= nil and row.kind == "melee"
end

-- the clip cut down to two fighters: every frame keeps only their records
local function onlyTwo(clip: any, a: number, b: number): any
	local REC = clip.rec or 24
	local frames = {}
	for _, f in clip.frames do
		local src = f.b
		local n = buffer.len(src) // REC
		local keep = {}
		for k = 0, n - 1 do
			local slot = buffer.readu32(src, k * REC)
			if slot == a or slot == b then table.insert(keep, k) end
		end
		local out = buffer.create(#keep * REC)
		for i, k in keep do buffer.copy(out, (i - 1) * REC, src, k * REC, REC) end
		table.insert(frames, { s = f.s, b = out })
	end
	local ev = {}
	for _, e in clip.ev do
		local who = e.id or e.k
		if (e.t == "shot" or e.t == "swing") and (who == a) then table.insert(ev, e)
		elseif e.t == "kill" and e.v == b then table.insert(ev, e) end
	end
	-- (string keys: a sparse number-keyed table would not survive the remote whole)
	local info = {}
	for slot, i in clip.info do if slot == a or slot == b then info[tostring(slot)] = i end end
	return { t0 = clip.t0, t1 = clip.t1, frames = frames, ev = ev, info = info, weapons = clip.weapons, rec = REC }
end

-- send a finisher of kill `x` to `viewers`
local function play(x: Kill, kind: string, viewers: { Player }, fid: string, skin: string)
	local clip, slots = Recorder.recent(x.k, Finishers.LEAD + 0.25)
	if not clip or not slots then return false, "not recorded" end
	local ks, vs = slots[x.k], slots[x.v]
	if not ks or not vs then return false, "not both in the recording" end
	local c = onlyTwo(clip, ks, vs)
	if #c.frames < 4 then return false, "too short" end
	-- (the killer's look in the clip wears the finisher's skin on the weapon that killed: a test arms one they don't wear)
	local w = weaponOf(x.w)
	local ki = c.info[tostring(ks)]
	if ki then
		ki = table.clone(ki)
		local skins = if type(ki.skins) == "string" then ki.skins else ""
		local list = {}
		for wid, sk in string.gmatch(skins, "([%w_]+)=([%w_]+)") do if wid ~= w then table.insert(list, wid .. "=" .. sk) end end
		table.insert(list, w .. "=" .. skin)
		ki.skins = table.concat(list, ";")
		c.info[tostring(ks)] = ki
	end
	local msg = { t = "finisher", id = fid, kind = kind, clip = c, focus = ks, victim = vs, w = w, skin = skin, melee = isMelee(w),
		by = x.k.name, byId = if x.k.kind == "player" then (x.k.ref :: Player).UserId else nil, kill = x.t,
		vid = if x.v.kind == "player" then (x.v.ref :: Player).UserId else nil }
	for _, p in viewers do
		if p.Parent then
			local m = table.clone(msg)
			m.role = if x.k.ref == p then "killer" elseif x.v.ref == p then "victim" else "watch"
			R:FireClient(p, m)
		end
	end
	return true, ("%s %s to %d"):format(fid, kind, #viewers)
end

-- a WORLD finisher (a round won, not the match): no recording, no camera - every client in the match draws the theme on
-- the victim's body where it lies (client/FinisherWorld.luau). The body is frozen there first, as a kill effect does
local function playWorld(x: Kill, viewers: { Player }, fid: string, skin: string): (boolean, string)
	local vm = Fight.model(x.v)
	if not vm or not vm.Parent then return false, "no body" end
	for _, d in vm:GetDescendants() do
		if d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false end
	end
	local km = Fight.model(x.k)
	local kr = km and km:FindFirstChild("HumanoidRootPart") :: BasePart?
	-- (the VFX session's interface: FinisherWorld.play(id, victim, { from, killer }))
	local msg = { t = "finisher", kind = "world", id = fid, skin = skin, victim = vm, killer = km, from = if kr then kr.Position else nil,
		by = x.k.name, byId = if x.k.kind == "player" then (x.k.ref :: Player).UserId else nil }
	for _, p in viewers do
		if p.Parent then
			local m = table.clone(msg)
			m.role = if x.k.ref == p then "killer" elseif x.v.ref == p then "victim" else "watch"
			R:FireClient(p, m)
		end
	end
	return true, ("%s world to %d"):format(fid, #viewers)
end

-- the finisher a killer's skin on that weapon owns
local function ownedFor(k: any, w: string): (string?, string?)
	if k.kind ~= "player" then return nil, nil end
	local skin = GunSkins.skinFor(k.ref :: Player, w)
	local fid = Finishers.forSkin(skin)
	return fid, skin
end

local function everyone(m: any): { Player }
	local out = {}
	for _, list in m.teams do for _, p in list do if p.Parent then table.insert(out, p) end end end
	return out
end

local function teamOf(m: any, p: Player): number?
	for t, list in m.teams do if table.find(list, p) then return t end end
	return nil
end

-- ------------------------------------------------------------------ the hooks
Fight.onKill(function(info: any)
	local k, v = info.k, info.v
	if not k or k == v or k.kind ~= "player" then return end
	local kp = k.ref :: Player
	local w = weaponOf(info.w)
	local t = os.clock()
	local a = armed[kp]
	if a then -- (a Studio test: this kill plays it, match or not)
		armed[kp] = nil
		local skin = a.skin or select(2, ownedFor(k, w))
		local fid = Finishers.forSkin(skin)
		if not fid or not skin then return end
		task.defer(function() -- (after the recorder has logged the kill)
			local ok, why = play({ k = k, v = v, w = info.w, t = t }, a.kind, if a.all then Players:GetPlayers() else { kp }, fid, skin)
			kp:SetAttribute("FinisherTestResult", ("%s: %s"):format(tostring(ok), tostring(why)))
		end)
		return
	end
	local m = Matches.raw(kp)
	if not m then return end
	local fid, skin = ownedFor(k, w)
	lastKill[m] = { k = k, v = v, w = info.w, t = t, fid = fid, skin = skin }
	local byP = killsBy[m] or {}
	killsBy[m] = byP
	local c = byP[kp] or {}
	byP[kp] = c
	c[w] = (c[w] or 0) + 1
end)

local function onRound(m: any, winner: number): (string?, any)
	local x = lastKill[m]
	if not x then return nil, "no kill" end
	local kp = x.k.ref :: Player
	local kind = Finishers.decide({ since = os.clock() - x.t, owned = x.fid ~= nil, weapon = x.w, killerAlive = x.k.alive == true,
		victimPlayer = x.v.kind == "player" or x.testVictim == true, sameTeam = teamOf(m, kp) == winner, event = "round",
		wins = m.wins[winner], need = Matches.WIN, classic = m.rules ~= nil })
	if not kind or not x.fid or not x.skin then return nil, "decided none" end
	-- (the victory scene live: the match-winning round's cut is its now - the best winner against the enemy best)
	if kind == "full" and FV.ON then return nil, "the victory scene's" end
	if kind == "full" then
		played[m] = true
		-- (a scene runs longer than the old cut: the end screen, the trip home and the play of the match wait for it)
		local all = everyone(m)
		holdFor(m, x.fid, all)
		return kind, table.pack(play(x, "full", all, x.fid, x.skin))
	elseif kind == "world" then
		return kind, table.pack(playWorld(x, everyone(m), x.fid, x.skin))
	else -- ("short": retired - Finishers.decide no longer picks it; kept for the "arm" test's short cut)
		local viewers = { kp }
		if x.v.kind == "player" and (x.v.ref :: Player).Parent then table.insert(viewers, x.v.ref) end
		return kind, table.pack(play(x, "short", viewers, x.fid, x.skin))
	end
end
-- (built ahead - main, 20 Nov: a scene's first frame built its whole set, a 97-99 ms hitch. Everyone in the match is
-- told which scenes its end could bring - the ones the skins its players wear own - in the gap after a round that
-- leaves a team one win from the match, and at a classic mode's start (its end is its only cut); the clients build those
-- sets then, a chunk a frame, parked off the map: client/FinisherScene.luau's Scene.warm)
local function scenesOf(m: any): { string }
	local out, seen = {}, {}
	for _, p in everyone(m) do
		local s = p:GetAttribute("Skins")
		if type(s) ~= "string" then continue end
		for wid in string.gmatch(s, "([%w_]+)=[%w_]+") do
			local _, row = Finishers.forSkin(GunSkins.skinFor(p, wid))
			local sid = row and (row :: any).scene
			if type(sid) == "string" and not seen[sid] then
				seen[sid] = true
				table.insert(out, sid)
			end
		end
	end
	return out
end
local function warm(m: any)
	local list = scenesOf(m)
	if #list == 0 then return end
	for _, p in everyone(m) do R:FireClient(p, { t = "finisher", kind = "warm", scenes = list }) end
end

-- ------------------------------------------------------------------ the victory scene's (server/FinisherVictory.luau)
function FV.finisherOf(p: Player, m: any): any?
	local s = p:GetAttribute("Skins")
	if type(s) ~= "string" then return nil end
	local counts = (m and killsBy[m] and killsBy[m][p]) or {}
	local best, bestN = nil, -1
	for wid in string.gmatch(s, "([%w_]+)=[%w_]+") do
		local skin = GunSkins.skinFor(p, wid)
		local fid, row = Finishers.forSkin(skin)
		local sid = row and (row :: any).scene
		if fid and skin and type(sid) == "string" then
			local n = counts[wid] or 0
			if n > bestN then
				best, bestN = { fid = fid, skin = skin, w = wid, scene = sid, len = Finishers.length("full", isMelee(wid), row) }, n
			end
		end
	end
	return best
end
function FV.play(m: any, kp: Player, vp: Player): (boolean, string, number?)
	if type(m) ~= "table" or typeof(kp) ~= "Instance" or typeof(vp) ~= "Instance" or not kp.Parent or not vp.Parent then
		return false, "a player left", nil
	end
	local c = FV.finisherOf(kp, m)
	if not c then return false, "no scene finisher equipped", nil end
	local k, v = Fight.of(kp), Fight.of(vp)
	if not k or not v then return false, "not fighters", nil end
	local all = everyone(m)
	holdFor(m, c.fid, all)
	local ok, why = play({ k = k, v = v, w = c.w, t = os.clock() }, "full", all, c.fid, c.skin)
	if not ok then
		watching[m] = nil
		m.finisherUntil = nil
		return false, why, nil
	end
	played[m] = true
	return true, why, c.len
end

Matches.onRound(function(m: any, winner: number)
	onRound(m, winner)
	local top = 0
	for _, n in m.wins or {} do top = math.max(top, n) end
	if top == Matches.WIN - 1 then warm(m) end -- (one win from the match: the next round may end it)
end)
Matches.onStart(function(m: any)
	if m.rules then warm(m) end
end)

Matches.onEnd(function(m: any, winner: number?)
	local x = lastKill[m]
	local done = played[m]
	lastKill[m] = nil
	played[m] = nil
	if done or not x or not winner or FV.ON then return end
	local kp = x.k.ref :: Player
	local kind = Finishers.decide({ since = os.clock() - x.t, owned = x.fid ~= nil, weapon = x.w, killerAlive = x.k.alive == true,
		victimPlayer = x.v.kind == "player", sameTeam = teamOf(m, kp) == winner, event = "end", classic = m.rules ~= nil })
	if kind and x.fid and x.skin then
		local all = everyone(m)
		if kind == "full" then holdFor(m, x.fid, all) end
		play(x, kind, all, x.fid, x.skin)
	end
end)

Players.PlayerRemoving:Connect(function(p)
	armed[p] = nil
	for m, set in watching do
		set[p] = nil
		if next(set) == nil then watching[m] = nil; if type(m.finisherUntil) == "number" then m.finisherUntil = math.min(m.finisherUntil, os.clock() + 0.3) end end
	end
end)
-- a viewer's full cut is over (played to its end, skipped, or never played): once all of a match's are, the end
-- screen comes on
R.OnServerEvent:Connect(function(p: Player, msg: any)
	if type(msg) ~= "table" or msg.t ~= "done" then return end
	for m, set in watching do
		if set[p] then
			set[p] = nil
			if next(set) == nil then
				watching[m] = nil
				if type(m.finisherUntil) == "number" then m.finisherUntil = math.min(m.finisherUntil, os.clock() + 0.3) end
				print(("[jankfire] FinisherHold: every viewer done %.1f s after it was sent"):format(os.clock() - (m.finisherFrom or os.clock())))
			end
		end
	end
end)

-- ------------------------------------------------------------------ Studio tests (ServerStorage.JankFinisherTest)
if RunService:IsStudio() then
	local old = ServerStorage:FindFirstChild("JankFinisherTest")
	if old then old:Destroy() end
	local fn = Instance.new("BindableFunction")
	fn.Name = "JankFinisherTest"
	fn.OnInvoke = function(op: string, a: any, b: any, c: any, d: any): any
		if op == "arm" and typeof(a) == "Instance" and a:IsA("Player") then
			if b ~= nil and not Finishers.forSkin(b) then return "no finisher on " .. tostring(b) end
			armed[a] = { skin = b, kind = if c == "short" then "short" else "full", all = d == true }
			a:SetAttribute("FinisherTestResult", nil)
			return "armed"
		elseif op == "kill" and typeof(a) == "Instance" and a:IsA("Player") then
			local f = Fight.byPlayer[a]
			local list = {}
			for _, x in Fight.all do if x.kind == "dummy" and x.alive then table.insert(list, x) end end
			local t = list[tonumber(b) or 1]
			if type(b) == "string" and not tonumber(b) then
				t = nil
				for _, x in list do if string.find(x.name, b, 1, true) then t = x; break end end
			end
			if not f or not t then return "no fighter or no live dummy (" .. #list .. " live)" end
			local w = if type(c) == "string" and Weapons.list[c] then c else "ar"
			local done = Fight.hurt(t, 99999, f, w, false)
			return ("hurt %s for %s with %s"):format(t.name, tostring(done), w)
		elseif op == "decide" then
			return Finishers.decide(a)
		elseif op == "world" and typeof(a) == "Instance" and a:IsA("Player") then
			local fid = Finishers.forSkin(b)
			if not fid then return "no finisher on " .. tostring(b) end
			local list = {}
			for _, x in Fight.all do if x.kind == "dummy" and x.alive then table.insert(list, x) end end
			local t = list[tonumber(c) or 1]
			if type(c) == "string" and not tonumber(c) then
				-- (an exact name first: "Armour1" mustn't pick "Armour10")
				t = nil
				for _, x in list do if x.name == c then t = x; break end end
				if not t then for _, x in list do if string.find(x.name, c, 1, true) then t = x; break end end end
			end
			local f = Fight.byPlayer[a]
			if not f or not t then return "no fighter or no live dummy (" .. #list .. " live)" end
			return table.pack(playWorld({ k = f, v = t, w = "test", t = os.clock() }, { a }, fid, b :: string))
		elseif op == "round" and typeof(a) == "Instance" and a:IsA("Player") then
			local m = Matches.raw(a)
			if not m then return "not in a match: JankMatchTest(\"ghost\", pad, nil, secs, player) first" end
			local x = lastKill[m]
			if not x then return "no kill in this match yet" end
			local skin = if type(c) == "string" then c else x.skin
			x.fid, x.skin = Finishers.forSkin(skin), skin
			x.testVictim = true
			x.t = os.clock()
			local team = teamOf(m, a) or 1
			local was = m.wins[team]
			m.wins[team] = if b == "short" then 1 else Matches.WIN
			local kind, res = onRound(m, team)
			m.wins[team] = was
			if d == true and kind == "full" then
				local t0 = os.clock()
				task.delay(1.2, function()
					a:SetAttribute("FinisherTestEnd", ("finish at %.1f s, hold to %.1f s"):format(os.clock() - t0, (m.finisherUntil or t0) - t0))
					Matches.finish(m, team)
				end)
			end
			return { kind = kind, sent = res, viewers = #everyone(m), match = m.id, hold = if m.finisherUntil then m.finisherUntil - os.clock() else nil }
		elseif op == "victory" and typeof(a) == "Instance" and a:IsA("Player") then
			-- ("victory", player, n|name, skin?): the victory scene's call with one tester - the player against a live
			-- training dummy (a player in a real match), to the player only; skin: wear-free (the arm test's way)
			local list = {}
			for _, x in Fight.all do if x.kind == "dummy" and x.alive then table.insert(list, x) end end
			local t = list[tonumber(b) or 1]
			if type(b) == "string" and not tonumber(b) then
				t = nil
				for _, x in list do if x.name == b then t = x; break end end
			end
			local f = Fight.byPlayer[a]
			if not f or not t then return "no fighter or no live dummy (" .. #list .. " live)" end
			local cand = FV.finisherOf(a, Matches.raw(a))
			if type(c) == "string" then
				local fid, row = Finishers.forSkin(c)
				local wid = nil
				for w in Weapons.list do
					if string.sub(c, 1, #w + 1) == w .. "_" and (not wid or #w > #wid) then wid = w end
				end
				cand = if fid and row and (row :: any).scene and wid then { fid = fid, skin = c, w = wid, scene = (row :: any).scene } else nil
			end
			if not cand then return "no scene finisher for " .. a.Name .. " (" .. tostring(c) .. ")" end
			return table.pack(play({ k = f, v = t, w = cand.w, t = os.clock() }, "full", { a }, cand.fid, cand.skin))
		elseif op == "state" then
			local out = { armed = {}, matches = {} }
			for p, x in armed do out.armed[p.Name] = x end
			for m, x in lastKill do table.insert(out.matches, { id = m.id, by = x.k.name, w = x.w, fid = x.fid, ago = os.clock() - x.t }) end
			return out
		end
		return nil
	end
	fn.Parent = ServerStorage
end
