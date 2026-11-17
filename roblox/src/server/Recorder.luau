--!strict
-- RECORDER: every match recorded as data, not video (roblox/docs/REPLAY.md; the web game's server/room.js recording,
-- its clip() and hlCandidate()). from a match's start to its end, about 12 times a second, a snapshot of everyone in
-- it (24 bytes each, packed in a buffer) and a log of what happened (shots with their ends, swings, hits, kills,
-- rounds). out of that:
--   * the KILLCAM: a player killed by another gets the last ~5 s, watched from over the killer's shoulder
--   * the PLAY OF THE MATCH: every kill is scored the web game's way; after the end screen everyone watches the best
--     one (Matches.afterHook holds the match on the end screen for it)
--   * REPORTS: Recorder.forReport(player) hands the current or last match's recording to the anti-cheat session as
--     plain strings, to keep with a report. nothing is stored by default: a finished match's recording stays in
--     memory KEEP_AFTER s, then it is gone
-- clips go to clients on JankfireRemotes.Replay (client/Replay.luau plays them).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Recorder = {}
Recorder.HZ = 12
Recorder.KEEP_AFTER = 600 -- s a finished match's recording waits for a report
Recorder.KILLCAM = { before = 5, after = 0.7 }
-- (Modes.luau) does this victim get a killcam? nil = always. a classic mode's respawn comes before the clip would end
Recorder.killcamFor = nil :: ((Player) -> boolean)?
Recorder.POTM = { before = 3.2, after = 1.3, max = 8, wait = 3.5, slowPerKill = 0.6 }
Recorder.REC = 24 -- bytes a fighter a frame

type Fighter = any
type Frame = { s: number, b: buffer }
type Best = { score: number, label: string, focus: number, name: string, t0: number, t1: number, kills: number }
type Session = {
	id: number, kind: string, match: any?, t0: number, t1: number?, started: number,
	fighters: { Fighter }, slot: { [Fighter]: number }, info: { [number]: any },
	frames: { Frame }, ev: { any }, weapons: { string }, wIndex: { [string]: number },
	killLog: { [Fighter]: { number } }, roundKills: { [Fighter]: { number } }, lastHs: { [Fighter]: boolean },
	best: Best?, bytes: number, mode: string?, arena: string?,
}

local Fight: any
local Matches: any
local remote: RemoteEvent
local live: { Session } = {}
local of: { [Fighter]: Session } = {} -- the live session each fighter is in
local lastOf: { [number]: { s: Session, expires: number } } = {} -- each player's last finished match by user id, for reports (a leaver's too)
local byMatch: { [number]: Session } = {}
local nextId = 0

local function now(): number return os.clock() end

-- ------------------------------------------------------------------ sessions
local function infoOf(f: Fighter, slot: number): any
	if f.kind == "player" then
		local p = f.ref :: Player
		return { id = p.UserId, name = p.DisplayName, user = p.Name, kind = "player", slot = slot,
			skins = p:GetAttribute("Skins"), wraps = p:GetAttribute("Wraps"), hats = p:GetAttribute("Hats") }
	end
	local m = Fight.model(f)
	return { id = -slot, name = f.name, kind = f.kind, slot = slot, model = m }
end

local function begin(kind: string, fighters: { Fighter }, match: any?): Session
	nextId += 1
	local s: Session = {
		id = nextId, kind = kind, match = match, t0 = now(), t1 = nil, started = os.time(),
		fighters = {}, slot = {}, info = {}, frames = {}, ev = {}, weapons = {}, wIndex = {},
		killLog = {}, roundKills = {}, lastHs = {}, best = nil, bytes = 0,
		mode = if match then match.mode else kind, arena = if match then match.arena else nil,
	}
	for _, f in fighters do
		if s.slot[f] == nil then
			table.insert(s.fighters, f)
			local i = #s.fighters
			s.slot[f] = i
			s.info[i] = infoOf(f, i)
			of[f] = s
		end
	end
	table.insert(live, s)
	if match then byMatch[match.id] = s end
	return s
end

local function finish(s: Session)
	if s.t1 then return end
	s.t1 = now()
	local i = table.find(live, s)
	if i then table.remove(live, i) end
	for _, f in s.fighters do
		if of[f] == s then of[f] = nil end
		if f.kind == "player" then lastOf[(f.ref :: Player).UserId] = { s = s, expires = now() + Recorder.KEEP_AFTER } end
	end
	if s.match then task.delay(Recorder.KEEP_AFTER, function() if byMatch[s.match.id] == s then byMatch[s.match.id] = nil end end) end
end

local function weaponIndex(s: Session, wid: string?): number
	if type(wid) ~= "string" then return 0 end
	local i = s.wIndex[wid]
	if not i then
		if #s.weapons >= 250 then return 0 end
		table.insert(s.weapons, wid)
		i = #s.weapons
		s.wIndex[wid] = i
	end
	return i :: number
end

-- ------------------------------------------------------------------ snapshots
local POSE = { stand = 0, crouch = 1, slide = 2 }
local function snapshot(s: Session)
	local n = #s.fighters
	local b = buffer.create(n * Recorder.REC)
	for i, f in s.fighters do
		local o = (i - 1) * Recorder.REC
		local root = Fight.root(f)
		local m = Fight.model(f)
		local pos = if root then root.Position else Vector3.zero
		local look = if root then root.CFrame.LookVector else Vector3.new(0, 0, -1)
		local yaw = math.atan2(-look.X, -look.Z)
		local tp = m and m:GetAttribute("TP")
		local pitch, flags = 0, 0
		if typeof(tp) == "Vector3" then pitch, flags = tp.X, tp.Z end
		local pose = m and m:GetAttribute("Pose")
		buffer.writeu32(b, o, i)
		buffer.writef32(b, o + 4, pos.X); buffer.writef32(b, o + 8, pos.Y); buffer.writef32(b, o + 12, pos.Z)
		buffer.writei16(b, o + 16, math.clamp(math.floor(yaw * 100 + 0.5), -32000, 32000))
		buffer.writei8(b, o + 18, math.clamp(math.floor(pitch + 0.5), -90, 90))
		buffer.writeu8(b, o + 19, math.clamp(math.floor(flags), 0, 255))
		buffer.writeu8(b, o + 20, if type(pose) == "string" then (POSE[pose] or 0) else 0)
		buffer.writeu8(b, o + 21, weaponIndex(s, f.held))
		buffer.writeu8(b, o + 22, math.clamp(math.floor((f.hp or 0) + 0.5), 0, 255))
		buffer.writeu8(b, o + 23, if f.alive and root then 1 else 0)
	end
	table.insert(s.frames, { s = now(), b = b })
	s.bytes += n * Recorder.REC
end

-- ------------------------------------------------------------------ events
local function push(s: Session, e: any)
	e.s = now()
	table.insert(s.ev, e)
end
local function slotIn(s: Session, f: Fighter?): number?
	return if f then s.slot[f] else nil
end

-- the web game's play of the round score, for one kill (multikills, distance, a fall, a headshot), and its label
local function candidate(s: Session, k: Fighter, v: Fighter, w: string, hs: boolean)
	local t = now()
	local log = {}
	for _, x in s.killLog[k] or {} do if t - x < 8 then table.insert(log, x) end end
	table.insert(log, t)
	s.killLog[k] = log
	local multi = #log
	local kf, vf = Fight.feet(k), Fight.feet(v)
	local metres = if kf and vf then (kf - vf).Magnitude / 3 else 0
	local score = multi * 10 + math.min(6, metres / 15) + (if w == "void" then 5 else 0) + (if hs then 3 else 0) + math.random()
	local best = s.best
	if best and best.score >= score then return end
	local label = if multi >= 5 then "RAMPAGE" elseif multi == 4 then "QUAD KILL" elseif multi == 3 then "TRIPLE KILL"
		elseif multi == 2 then "DOUBLE KILL" elseif w == "void" then "INTO THE SMOG" elseif metres > 40 then ("%d M SHOT"):format(math.floor(metres))
		elseif hs then "HEADSHOT" else "KILL"
	s.best = { score = score, label = label, focus = s.slot[k], name = k.name, t0 = math.max(log[1] - Recorder.POTM.before, t - 8),
		t1 = t + Recorder.POTM.after, kills = multi }
end

-- ------------------------------------------------------------------ clips
-- a slice of the recording: the frames and events between t0 and t1, who's who, the weapon names
function Recorder.clip(s: Session, t0: number, t1: number): any
	local frames = {}
	for _, f in s.frames do if f.s >= t0 and f.s <= t1 then table.insert(frames, f) end end
	local ev = {}
	for _, e in s.ev do if e.s >= t0 and e.s <= t1 then table.insert(ev, e) end end
	local info = {}
	for slot, i in s.info do
		local c = table.clone(i)
		c.model = nil
		if i.kind ~= "player" and i.model then c.modelName = (i.model :: Instance).Name end
		info[slot] = c
	end
	return { t0 = t0, t1 = t1, frames = frames, ev = ev, info = info, weapons = s.weapons, rec = Recorder.REC }
end
-- (FinisherServer) the last `before` s of the recording a fighter is in, up to now: the clip and every fighter's slot in
-- it. their live match, else (a player) the one that just ended. nil when nobody is recording them
function Recorder.recent(f: Fighter, before: number): (any?, { [Fighter]: number }?)
	local s = of[f]
	if not s and f.kind == "player" then
		local l = lastOf[(f.ref :: Player).UserId]
		if l and now() < l.expires then s = l.s end
	end
	if not s then return nil, nil end
	return Recorder.clip(s, now() - before, now()), s.slot
end
local function clipLen(b: Best): number
	return math.min(Recorder.POTM.max, b.t1 - b.t0) + b.kills * Recorder.POTM.slowPerKill
end

-- ------------------------------------------------------------------ the hooks
local function onShotFx(f: Fighter, wid: string, ends: { Vector3 }?, kind: string?)
	local s = of[f]
	if not s then return end
	local e: any = { t = kind or "shot", id = s.slot[f], w = wid }
	if ends then
		local out = {}
		for i, v in ends do if i <= 12 and typeof(v) == "Vector3" then out[i] = v end end
		e.e = out
	end
	push(s, e)
end

local function onHurt(t: Fighter, done: number, by: Fighter?, wid: string, hs: boolean?)
	local s = of[t]
	if not s then return end
	s.lastHs[t] = hs == true
	push(s, { t = "hurt", v = s.slot[t], k = slotIn(s, by), a = math.floor(done + 0.5), hs = hs == true, w = wid })
end

local function onKill(info: any)
	local v, k = info.v, info.k
	local s = of[v]
	if not s then return end
	local hs = s.lastHs[v] == true
	push(s, { t = "kill", v = s.slot[v], k = slotIn(s, k), w = info.w, hs = hs })
	-- the play of the match: a match counts kills on players; a test session counts its dummies too
	if k and k ~= v and s.slot[k] and (v.kind == "player" or s.kind == "test") then
		candidate(s, k, v, info.w, hs)
		local rk = s.roundKills[k] or {}
		table.insert(rk, now())
		s.roundKills[k] = rk
	end
	-- the killcam: the victim, a beat later, the last few seconds from over the killer's shoulder
	if v.kind == "player" and k and k ~= v and s.slot[k] then
		local vp = v.ref :: Player
		local t = now()
		task.delay(Recorder.KILLCAM.after, function()
			if not vp.Parent then return end
			if Recorder.killcamFor and not Recorder.killcamFor(vp) then return end -- (a classic mode: you're back in 2.5 s)
			local c = Recorder.clip(s, t - Recorder.KILLCAM.before, now())
			if #c.frames < 6 then return end
			remote:FireClient(vp, { t = "killcam", clip = c, focus = s.slot[k], victim = s.slot[v], w = info.w, by = k.name })
		end)
	end
end

-- a round won by a team with one player left who took two or more in it: a clutch (CLUTCH · 1V2) for the pick
local function onRound(m: any, winner: number)
	local s = byMatch[m.id]
	if not s or s.t1 then return end
	push(s, { t = "round", n = m.round, w = winner })
	local team = m.teams[winner]
	if team and #team >= 2 then
		local alive = {}
		for _, p in team do local f = Fight.byPlayer[p]; if f and f.alive then table.insert(alive, f) end end
		if #alive == 1 then
			local f = alive[1]
			local rk = s.roundKills[f] or {}
			if #rk >= 2 then
				local score = #rk * 10 + 6 + math.random()
				if not s.best or score > (s.best :: Best).score then
					s.best = { score = score, label = ("CLUTCH · 1V%d"):format(#rk), focus = s.slot[f], name = f.name,
						t0 = math.max(rk[1] - Recorder.POTM.before, rk[#rk] - Recorder.POTM.max + Recorder.POTM.after), t1 = rk[#rk] + Recorder.POTM.after, kills = #rk }
				end
			end
		end
	end
	s.roundKills = {}
end

-- Matches asks at the end: hold the end screen for the play of the match? { wait, total, label } or nil
local function afterHook(m: any): any?
	local s = byMatch[m.id]
	local b = s and s.best
	if not b then return nil end
	return { wait = Recorder.POTM.wait, total = Recorder.POTM.wait + clipLen(b) + 1.2, label = "play of the match in %d" }
end

local function onStart(m: any)
	local fs = {}
	for _, list in m.teams do for _, p in list do local f = Fight.byPlayer[p]; if f then table.insert(fs, f) end end end
	if #fs == 0 then return end
	begin("match", fs, m)
end

local function onEnd(m: any, _winner: number?)
	local s = byMatch[m.id]
	if not s then return end
	local b = s.best
	if b then
		local c = Recorder.clip(s, b.t0, math.min(b.t1, b.t0 + Recorder.POTM.max, now()))
		local msg = { t = "potm", clip = c, focus = b.focus, label = b.label, name = b.name, at = workspace:GetServerTimeNow() + Recorder.POTM.wait,
			slowKills = true }
		for _, list in m.teams do for _, p in list do if p.Parent then remote:FireClient(p, msg) end end end
	end
	finish(s)
end

-- ------------------------------------------------------------------ reports (the anti-cheat session's REPORT)
local B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
local function base64(b: buffer): string
	local n = buffer.len(b)
	local out = table.create(math.ceil(n / 3))
	local i = 0
	while i < n do
		local a0 = buffer.readu8(b, i)
		local a1 = if i + 1 < n then buffer.readu8(b, i + 1) else 0
		local a2 = if i + 2 < n then buffer.readu8(b, i + 2) else 0
		local v = a0 * 65536 + a1 * 256 + a2
		local c1, c2 = v // 262144 % 64 + 1, v // 4096 % 64 + 1
		local c3, c4 = v // 64 % 64 + 1, v % 64 + 1
		table.insert(out, string.sub(B64, c1, c1) .. string.sub(B64, c2, c2)
			.. (if i + 1 < n then string.sub(B64, c3, c3) else "=") .. (if i + 2 < n then string.sub(B64, c4, c4) else "="))
		i += 3
	end
	return table.concat(out)
end

-- a recording as plain strings, for a report: frames = base64 of [f32 seconds since start, u16 count, records...]
-- each frame; events = JSON (Vector3s as [x, y, z]); players = who's who. returns nil if there is nothing
function Recorder.export(s: Session): any
	local total = 0
	for _, f in s.frames do total += 6 + buffer.len(f.b) end
	local all = buffer.create(total)
	local o = 0
	for _, f in s.frames do
		buffer.writef32(all, o, f.s - s.t0)
		buffer.writeu16(all, o + 4, buffer.len(f.b) // Recorder.REC)
		buffer.copy(all, o + 6, f.b)
		o += 6 + buffer.len(f.b)
	end
	local ev = {}
	for _, e in s.ev do
		local c = {}
		for k, v in e do
			if typeof(v) == "Vector3" then c[k] = { math.floor(v.X * 100) / 100, math.floor(v.Y * 100) / 100, math.floor(v.Z * 100) / 100 }
			elseif type(v) == "table" then
				local arr = {}
				for i, x in v do arr[i] = if typeof(x) == "Vector3" then { math.floor(x.X * 100) / 100, math.floor(x.Y * 100) / 100, math.floor(x.Z * 100) / 100 } else x end
				c[k] = arr
			elseif k == "s" then c.s = math.floor((v - s.t0) * 1000) / 1000
			else c[k] = v end
		end
		table.insert(ev, c)
	end
	local players = {}
	for slot, i in s.info do players[tostring(slot)] = { id = i.id, name = i.name, user = i.user, kind = i.kind } end
	local framesB64 = base64(all)
	local evJson = HttpService:JSONEncode(ev)
	return {
		v = 1, id = s.id, kind = s.kind, mode = s.mode, arena = s.arena, started = s.started,
		secs = math.floor(((s.t1 or now()) - s.t0) * 10) / 10, hz = Recorder.HZ, rec = Recorder.REC, weapons = table.clone(s.weapons),
		players = players, frames = framesB64, events = evJson, bytes = #framesB64 + #evJson,
	}
end

-- the recording a report about this player should keep: the match they are in now, else their last one (kept
-- KEEP_AFTER s after it ended). nil when there is none. the anti-cheat session saves it in its own store.
-- who = the Player, or their user id (a player who left: a match still running that recorded them, or their last one)
function Recorder.forReport(who: Player | number): any?
	local uid = if typeof(who) == "Instance" then (who :: Player).UserId else tonumber(who)
	if not uid then return nil end
	local p = if typeof(who) == "Instance" then who :: Player else Players:GetPlayerByUserId(uid)
	local f = if p then Fight.byPlayer[p] else nil
	local s = if f then of[f] else nil
	if not s then
		for _, x in live do
			for _, i in x.info do if i.kind == "player" and i.id == uid then s = x; break end end
			if s then break end
		end
	end
	if not s then
		local l = lastOf[uid]
		if l and now() < l.expires then s = l.s end
	end
	return if s then Recorder.export(s) else nil
end

-- what the recorder holds now: sessions, frames, bytes, and the rate per minute of the live ones
function Recorder.stats(): any
	local out = { live = #live, sessions = {} }
	for _, s in live do
		local secs = math.max(0.1, now() - s.t0)
		table.insert(out.sessions, { id = s.id, kind = s.kind, fighters = #s.fighters, frames = #s.frames, events = #s.ev, frameBytes = s.bytes,
			secs = math.floor(secs * 10) / 10, perMinute = math.floor(s.bytes / secs * 60) })
	end
	return out
end

-- ------------------------------------------------------------------ wiring
function Recorder.init(fight: any, matches: any)
	Fight, Matches = fight, matches
	local remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
	local r = remotes:FindFirstChild("Replay")
	if not r then
		r = Instance.new("RemoteEvent")
		r.Name = "Replay"
		r.Parent = remotes
	end
	remote = r :: RemoteEvent
	Fight.onShotFx(onShotFx)
	Fight.onHurt(onHurt)
	Fight.onKill(onKill)
	Matches.onStart(onStart)
	Matches.onRound(onRound)
	Matches.onEnd(onEnd)
	Matches.afterHook = afterHook
	local acc = 0
	RunService.Heartbeat:Connect(function(dt)
		acc += dt
		if acc < 1 / Recorder.HZ then return end
		acc = 0
		for _, s in live do
			local ok, err = pcall(snapshot, s)
			if not ok then warn("[jankfire] recorder: " .. tostring(err)) end
		end
		local t = now()
		for id, l in lastOf do if t > l.expires then lastOf[id] = nil end end -- (a leaver's stays until KEEP_AFTER runs out)
	end)
	if RunService:IsStudio() then
		local old = ServerStorage:FindFirstChild("JankReplayTest")
		if old then old:Destroy() end
		local fn = Instance.new("BindableFunction")
		fn.Name = "JankReplayTest"
		fn.OnInvoke = function(op: string, a: any, b: any): any return Recorder.test(op, a, b) end
		fn.Parent = ServerStorage
	end
end

-- ------------------------------------------------------------------ Studio tests (ServerStorage.JankReplayTest)
-- ("record", player)   record the player and every dummy (a test session outside a match: the training hall)
-- ("stop", player)     end it (it becomes the player's last recording)
-- ("potm", player)     send the player the test session's play of the match now (its best kill run)
-- ("killcam", player, name)   send the player a killcam of the last 5 s from over `name`'s shoulder
-- ("stats")            what is recorded and its size;  ("export", player or user id) Recorder.forReport's size and shape
function Recorder.test(op: string, a: any, b: any): any
	if not RunService:IsStudio() then return nil end
	local p = if typeof(a) == "Instance" and a:IsA("Player") then a else nil
	local f = p and Fight.byPlayer[p]
	if op == "record" and f then
		if of[f] then finish(of[f] :: Session) end
		local fs = { f }
		for _, x in Fight.all do if x.kind ~= "player" then table.insert(fs, x) end end
		local s = begin("test", fs, nil)
		return { id = s.id, fighters = #s.fighters }
	elseif op == "stop" and f then
		local s = of[f]
		if s then finish(s) end
		return s ~= nil
	elseif op == "potm" and p then
		local s = (f and of[f]) or (lastOf[p.UserId] and lastOf[p.UserId].s)
		local bst = s and s.best
		if not s or not bst then return "no kills recorded" end
		local c = Recorder.clip(s, bst.t0, math.min(bst.t1, bst.t0 + Recorder.POTM.max, now()))
		remote:FireClient(p, { t = "potm", clip = c, focus = bst.focus, label = bst.label, name = bst.name, at = workspace:GetServerTimeNow() + 0.3, slowKills = true })
		return { label = bst.label, frames = #c.frames, events = #c.ev, secs = c.t1 - c.t0 }
	elseif op == "killcam" and p then
		local s = (f and of[f]) or (lastOf[p.UserId] and lastOf[p.UserId].s)
		if not s then return "not recording" end
		local focus = nil
		for slot, i in s.info do if i.name == b then focus = slot end end
		local c = Recorder.clip(s, now() - Recorder.KILLCAM.before, now())
		remote:FireClient(p, { t = "killcam", clip = c, focus = focus or 1, victim = f and s.slot[f], w = "ar", by = tostring(b) })
		return { frames = #c.frames, focus = focus }
	elseif op == "stats" then
		return Recorder.stats()
	elseif op == "export" and (p or type(a) == "number") then
		local x = Recorder.forReport(p or a)
		if not x then return "nothing" end
		return { bytes = x.bytes, frameChars = #x.frames, eventChars = #x.events, secs = x.secs, players = x.players, weapons = x.weapons }
	end
	return nil
end

return Recorder
