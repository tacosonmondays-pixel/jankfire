--!strict
-- REPORTS (17 Nov 2026; the owner: "Can we have a built in report that saves public chat?"; docs/ANTI-CHEAT.md,
-- "Reports"). a player reports another from their card, the end-of-match board or a party row (client/ReportUI.luau),
-- with a reason: cheating, abusive chat, griefing, other. the report keeps, for the owner's panel:
--   * the last CHAT_SECS of PUBLIC chat in this server, filtered for everyone like Roblox's own chat does (whispers,
--     team chat and chat commands are never kept)
--   * the reported player's anti-cheat state (points, recent catches, totals across servers)
--   * the match's recording when they're in one or just left one (Recorder.forReport: kept only for reported matches)
-- only user ids are stored, never names (the panel looks names up when it shows them). it all lives in the DataStore
-- "JankReports_v1" (a Studio test writes "s_" keys) and goes after KEEP_DAYS. Roblox's right-to-erasure requests:
-- Reports.erase(userId), the panel's ERASE (docs/ANTI-CHEAT.md says how). players can still use Roblox's own Report
-- (Esc menu); ours is extra evidence for the owner.
-- the owner's actions (server/AntiCheat.server.luau answers the panel): dismiss, kick, ban (the ban switch), and
-- CONFIRM CHEATER: the owner's "give back any ranked stuff or stats" (Stats / RankedData / Quests .restoreFor), never
-- from an automatic flag. UNCONFIRM (a wrong catch) gives the cheater's own numbers back (.undoRestore)
local Players = game:GetService("Players")
local DataStoreService = game:GetService("DataStoreService")
local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")
local TextService = game:GetService("TextService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Reports = {}
local STUDIO = RunService:IsStudio()
local K = if STUDIO then "s_" else "" -- (Studio's reports never mix with real ones)

Reports.REASONS = { cheating = "Cheating", chat = "Abusive chat", griefing = "Griefing", other = "Other" }
local CTX = { card = true, board = true, party = true, other = true }
Reports.KEEP_DAYS = 30
Reports.CHAT_SECS = 180 -- s of public chat a report keeps
Reports.LEFT_SECS = 600 -- s after leaving that someone can still be reported (the end-of-match board)
Reports.PER_10MIN = 3 -- reports one player can send in 10 minutes
Reports.PER_DAY = 10 -- and in a day (every server)
Reports.DEDUP_HOURS = 24 -- the same reporter reporting the same player again inside this: kept once
local MAX_INDEX = 500
local MAX_REC = 3500000 -- characters of JSON: a DataStore key holds 4 MB

local store: DataStore? = nil
pcall(function() store = DataStoreService:GetDataStore("JankReports_v1") end)
local SRV = if game.JobId ~= "" then string.sub(game.JobId, 1, 8) else "st" .. (os.time() % 100000)

local deps: any = {}

-- ------------------------------------------------------------------ public chat, the last few minutes, filtered
type Line = { t: number, c: number, u: number, x: string }
local chat: { Line } = {}
local function trimChat()
	local c0 = os.clock() - Reports.CHAT_SECS
	while #chat > 0 and chat[1].c < c0 do table.remove(chat, 1) end
	while #chat > 400 do table.remove(chat, 1) end
end
-- two ways a public line reaches the server: Player.Chatted (a recipient = a whisper; "/" = a command, "/w" a whisper,
-- "/t" or "%" team chat: none of them are public), and the legacy chat's own server, its "All" channel (this place
-- uses the legacy chat). a line both report is kept once
local heardCount = { chatted = 0, channel = 0, say = 0, kept = 0 }
local recentLines: { [string]: number } = {}
local function heard(p: Player, msg: unknown, recipient: Player?, via: string)
	if recipient or type(msg) ~= "string" or msg == "" then return end
	local first = string.sub(msg, 1, 1)
	if first == "/" or first == "%" then return end
	heardCount[via] += 1
	local text = string.sub(msg, 1, 200)
	local key = p.UserId .. "|" .. text
	if recentLines[key] and os.clock() - recentLines[key] < 2 then return end
	recentLines[key] = os.clock()
	heardCount.kept += 1
	local t, c, uid = os.time(), os.clock(), p.UserId
	task.spawn(function()
		local ok, out = pcall(function()
			return TextService:FilterStringAsync(text, uid, Enum.TextFilterContext.PublicChat):GetNonChatStringForBroadcastAsync()
		end)
		-- (never the raw words: what everyone else could see, or nothing)
		table.insert(chat, { t = t, c = c, u = uid, x = if ok and type(out) == "string" then out else "(not kept: the filter didn't answer)" })
		table.sort(chat, function(a, b) return a.c < b.c end)
		trimChat()
		for k, at in recentLines do if os.clock() - at > 5 then recentLines[k] = nil end end
	end)
end
-- the legacy chat's server (ChatServiceRunner, put in ServerScriptService when a server starts): its "All" channel is
-- the public one (whispers and team chat have their own channels)
local function hookLegacyChat()
	-- (the legacy chat's own remote: what a client says, and to which channel. "All" is public; whispers go to
	-- "To <name>", team chat to "Team". tested 17 Nov: this is the one that hears the legacy chat here)
	task.spawn(function()
		local ev = ReplicatedStorage:WaitForChild("DefaultChatSystemChatEvents", 60)
		local say = ev and ev:WaitForChild("SayMessageRequest", 20)
		if say and say:IsA("RemoteEvent") then
			say.OnServerEvent:Connect(function(p: Player, msg: unknown, channel: unknown)
				if channel == "All" then heard(p, msg, nil, "say") end
			end)
		end
	end)
	local runner = game:GetService("ServerScriptService"):WaitForChild("ChatServiceRunner", 60)
	local mod = runner and runner:WaitForChild("ChatService", 20)
	if not mod or not mod:IsA("ModuleScript") then return end
	local ok, CS = pcall(require, mod)
	if not ok or type(CS) ~= "table" then return end
	local hooked = false
	local function onChannel(name: string)
		if name ~= "All" or hooked then return end
		local ch = CS:GetChannel("All")
		if not ch or not ch.MessagePosted then return end
		hooked = true
		ch.MessagePosted:Connect(function(m: any)
			if type(m) ~= "table" or (m.MessageType ~= nil and m.MessageType ~= "Message") then return end
			local p = (if type(m.SpeakerUserId) == "number" then Players:GetPlayerByUserId(m.SpeakerUserId) else nil)
				or (if type(m.FromSpeaker) == "string" then Players:FindFirstChild(m.FromSpeaker) else nil)
			if p and p:IsA("Player") then heard(p, m.Message, nil, "channel") end
		end)
	end
	pcall(onChannel, "All")
	if CS.ChannelAdded then CS.ChannelAdded:Connect(function(name: string) pcall(onChannel, name) end) end
end

-- ------------------------------------------------------------------ who's here, who just left
local left: { [number]: { t: number, p: Player } } = {}
local sent: { [Player]: { number } } = {}
local dedup: { [string]: number } = {}

local function validUid(v: unknown): number?
	if type(v) ~= "number" or v ~= v or v ~= math.floor(v) or math.abs(v) > 2 ^ 53 or v == 0 then return nil end
	if v < 0 and not STUDIO then return nil end -- (Studio's local test players have negative ids)
	return v
end
Reports.validUid = validUid

local names: { [number]: string } = {}
-- a name to SHOW (looked up, never stored)
function Reports.nameOf(uid: number): string
	if uid == 0 then return "(erased)" end
	local p = Players:GetPlayerByUserId(uid)
	if p then return p.Name end
	if names[uid] then return names[uid] end
	local ok, n = pcall(function() return Players:GetNameFromUserIdAsync(uid) end)
	names[uid] = if ok and type(n) == "string" then n else ("user " .. uid)
	return names[uid]
end

local function recorder(): any
	local m = script.Parent:FindFirstChild("Recorder")
	if not m then return nil end
	local ok, R = pcall(require, m)
	return if ok then R else nil
end

-- ------------------------------------------------------------------ storing
local idxT0 = 0 -- (bumped on every write: Reports.list's cache starts again)
local function upd(key: string, fn: (any) -> any): boolean
	if not store then return false end
	idxT0 += 1
	local ok, err = pcall(function() (store :: DataStore):UpdateAsync(key, fn) end)
	if not ok then warn("[reports] " .. key .. ": " .. tostring(err)) end
	return ok
end
local function get(key: string): any
	if not store then return nil end
	local ok, v = pcall(function() return (store :: DataStore):GetAsync(key) end)
	return if ok then v else nil
end
local function del(key: string)
	if store then pcall(function() (store :: DataStore):RemoveAsync(key) end) end
end

-- who appears in a report (its chat, its recording): "inv_<userId>" lists those reports, so an erasure finds them
local function noteIn(uid: number, id: string)
	upd(K .. "inv_" .. uid, function(old: any)
		local l = if type(old) == "table" then old else {}
		if table.find(l, id) then return nil end
		table.insert(l, id)
		while #l > 300 do table.remove(l, 1) end
		return l
	end)
end

local function save(r: any, rec: any?)
	if not store then return end
	local dup = false
	-- the recording first (its own key: up to 4 MB), then the report, then the index that points at both
	if rec then
		local okJ, js = pcall(function() return HttpService:JSONEncode(rec) end)
		if okJ and #js <= MAX_REC then
			r.rec = pcall(function() (store :: DataStore):SetAsync(K .. "rec_" .. r.id, rec) end)
			r.recBytes = #js
		end
	end
	local okR = pcall(function() (store :: DataStore):SetAsync(K .. "r_" .. r.id, r) end)
	if not okR then warn("[reports] report " .. r.id .. " not stored"); return end
	upd(K .. "index", function(old: any)
		dup = false
		local l = if type(old) == "table" then old else {}
		for _, e in l do
			if type(e) == "table" and e.by == r.by and e.who == r.who and r.t - (e.t or 0) < Reports.DEDUP_HOURS * 3600 then dup = true; return nil end
		end
		table.insert(l, { id = r.id, t = r.t, by = r.by, who = r.who, why = r.why, ctx = r.ctx, match = r.match, lines = #r.chat, rec = r.rec == true, state = "open" })
		while #l > MAX_INDEX do table.remove(l, 1) end
		return l
	end)
	if dup then
		-- (another server already has this one: drop the copy)
		del(K .. "r_" .. r.id); del(K .. "rec_" .. r.id)
		return
	end
	local seen: { [number]: boolean } = { [r.by] = true, [r.who] = true }
	for _, l in r.chat do seen[l.u] = true end
	if rec and type(rec.players) == "table" then for _, pl in rec.players do if type(pl) == "table" and type(pl.id) == "number" then seen[pl.id] = true end end end
	for uid in seen do noteIn(uid, r.id) end
	if deps.Log then deps.Log.add(r.who, "report", "report", ("%s, from the %s; %d chat lines%s"):format(Reports.REASONS[r.why] or r.why, r.ctx, #r.chat, if r.rec then ", with the match" else "")) end
end

-- ------------------------------------------------------------------ a player reports someone
local function send(p: Player, who: unknown, why: unknown, ctx: unknown): any
	local uid = validUid(who)
	if not uid then return { ok = false, why = "who?" } end
	if type(why) ~= "string" or not Reports.REASONS[why] then return { ok = false, why = "pick a reason" } end
	local c = if type(ctx) == "string" and CTX[ctx] then ctx else "other"
	if uid == p.UserId then return { ok = false, why = "that's you" } end
	local target = Players:GetPlayerByUserId(uid)
	local gone = left[uid]
	if not target and not (gone and os.clock() - gone.t < Reports.LEFT_SECS) then return { ok = false, why = "they're not in this server any more" } end
	local mine = sent[p] or {}
	sent[p] = mine
	while #mine > 0 and os.clock() - mine[1] > 600 do table.remove(mine, 1) end
	if #mine >= Reports.PER_10MIN then return { ok = false, why = "you've sent a few already: try again in a while" } end
	local dk = p.UserId .. ":" .. uid
	if dedup[dk] and os.time() - dedup[dk] < Reports.DEDUP_HOURS * 3600 then return { ok = true, again = true } end
	-- (a day's limit across servers: the index knows)
	local idx = get(K .. "index")
	if type(idx) == "table" then
		local n = 0
		for _, e in idx do if type(e) == "table" and e.by == p.UserId and os.time() - (e.t or 0) < 86400 then n += 1 end end
		if n >= Reports.PER_DAY then return { ok = false, why = "that's enough reports for today" } end
	end
	table.insert(mine, os.clock())
	dedup[dk] = os.time()
	local lines = {}
	for _, l in chat do
		if os.clock() - l.c <= Reports.CHAT_SECS then table.insert(lines, { t = l.t, u = l.u, x = l.x }) end
	end
	local flags = nil
	if deps.flagsOf then
		local okF, f = pcall(deps.flagsOf, uid)
		if okF then flags = f end
	end
	local rec = nil
	local R = recorder()
	local mp = target or (gone and gone.p)
	if R and mp and type(R.forReport) == "function" then
		local okR, r = pcall(R.forReport, mp)
		if okR and type(r) == "table" then
			rec = r
			-- (user ids only: the names come off)
			if type(r.players) == "table" then for _, pl in r.players do if type(pl) == "table" then pl.name = nil; pl.user = nil end end end
		end
	end
	local id = string.sub(string.gsub(HttpService:GenerateGUID(false), "-", ""), 1, 12)
	local report = {
		id = id, t = os.time(), by = p.UserId, who = uid, why = why, ctx = c, chat = lines, flags = flags,
		match = if rec then rec.id else nil, mode = if rec then rec.mode else nil, srv = SRV, rec = false,
	}
	task.spawn(save, report, rec)
	return { ok = true }
end

-- ------------------------------------------------------------------ the owner's side
-- every report, newest first, with names to show (the index is read at most every 8 s: an open panel asks every 3)
local idxCache: any, idxT, idxSeen = nil, -math.huge, -1
function Reports.list(): { any }
	if os.clock() - idxT > 8 or idxSeen ~= idxT0 then idxCache, idxT, idxSeen = get(K .. "index"), os.clock(), idxT0 end
	local idx = idxCache
	local out = {}
	if type(idx) == "table" then
		for i = #idx, 1, -1 do
			local e = idx[i]
			if type(e) == "table" then
				local row = table.clone(e)
				row.whoName, row.byName = Reports.nameOf(e.who), Reports.nameOf(e.by)
				table.insert(out, row)
			end
		end
	end
	return out
end

-- one report, its chat with names, the size of its recording (the recording itself stays on the server)
function Reports.get(id: string): any
	local r = get(K .. "r_" .. id)
	if type(r) ~= "table" then return nil end
	local lines = {}
	for _, l in r.chat or {} do table.insert(lines, { t = l.t, u = l.u, name = Reports.nameOf(l.u), x = l.x, who = l.u == r.who }) end
	r.chat = lines
	r.whoName, r.byName = Reports.nameOf(r.who), Reports.nameOf(r.by)
	r.here = Players:GetPlayerByUserId(r.who) ~= nil
	return r
end

-- open / dismissed / actioned (kicked, banned, confirmed), and by whom
function Reports.setState(id: string, state: string, by: number): boolean
	local found = false
	upd(K .. "index", function(old: any)
		found = false
		if type(old) ~= "table" then return nil end
		for _, e in old do
			if type(e) == "table" and e.id == id then e.state = state; e.at = os.time(); e.by2 = by; found = true end
		end
		return if found then old else nil
	end)
	return found
end

-- the earliest evidence about a player: their first anti-cheat catch or the first report about them (both kept 30
-- days), a day before it. 0 = nothing on record (everything the restores still have)
function Reports.evidenceSince(uid: number): number
	local t = math.huge
	local idx = get(K .. "index")
	if type(idx) == "table" then for _, e in idx do if type(e) == "table" and e.who == uid then t = math.min(t, e.t or math.huge) end end end
	if deps.Log then
		local r = deps.Log.user(uid)
		if type(r) == "table" and type(r.first) == "number" then t = math.min(t, r.first) end
	end
	return if t == math.huge then 0 else math.max(0, t - 86400)
end

-- the restores: each module's restoreFor / undoRestore, in its own thread, behind a FindFirstChild and a pcall; a
-- "try again" answer is tried again twice
local RESTORES = { { "Stats", "stats" }, { "RankedData", "ranked" }, { "Quests", "quests" } }
local function call(modName: string, fn: string, ...: any): any
	local m = script.Parent:FindFirstChild(modName)
	if not m then return { ok = false, why = modName .. " isn't in this place" } end
	local okM, mod = pcall(require, m)
	if not okM or type(mod) ~= "table" or type(mod[fn]) ~= "function" then return { ok = false, why = modName .. "." .. fn .. " missing" } end
	local args = table.pack(...)
	local res: any = nil
	for i = 1, 3 do
		local ok, r = pcall(function() return mod[fn](table.unpack(args, 1, args.n)) end)
		res = if ok then r else { ok = false, why = tostring(r) }
		if type(res) == "table" and res.ok ~= false then break end
		if i < 3 then task.wait(10) end
	end
	return res
end
local function brief(res: any): string
	if type(res) ~= "table" then return "?" end
	if res.ok == false then return "failed (" .. tostring(res.why) .. ")" end
	local bits = {}
	for _, k in { "matches", "victims", "now", "queued" } do
		if res[k] ~= nil then table.insert(bits, k .. " " .. tostring(res[k])) end
	end
	return if #bits > 0 then table.concat(bits, ", ") else "ok"
end

-- CONFIRM CHEATER: the restores, from `since` (os.time; nil = the earliest evidence, 0 = everything). safe to press
-- twice: every restore is once per match on its own side, and the record here says who confirmed and when
function Reports.confirm(uid: number, since: number?, by: number): number
	local from = if since == nil then Reports.evidenceSince(uid) else math.max(0, math.floor(since))
	upd(K .. "c_" .. uid, function(old: any)
		local r = if type(old) == "table" then old else { list = {} }
		r.list = if type(r.list) == "table" then r.list else {}
		table.insert(r.list, { t = os.time(), by = by, since = from, op = "confirm" })
		r.confirmed = true
		return r
	end)
	if deps.Log then deps.Log.add(uid, "confirm", "confirm", ("confirmed a cheater by the owner (user %d); restores since %s"):format(by, if from > 0 then os.date("!%d %b %Y", from) :: string else "the start")) end
	for _, m in RESTORES do
		task.spawn(function()
			local res = call(m[1], "restoreFor", uid, from)
			if deps.Log then deps.Log.add(uid, "confirm", "restore " .. m[2], brief(res)) end
		end)
	end
	return from
end

-- UNCONFIRM: a wrong catch. the cheater's own numbers come back (Stats and Quests keep a copy; ranked has an
-- undo only if its module offers one); the victims keep their refunds
function Reports.unconfirm(uid: number, by: number)
	upd(K .. "c_" .. uid, function(old: any)
		local r = if type(old) == "table" then old else { list = {} }
		r.list = if type(r.list) == "table" then r.list else {}
		table.insert(r.list, { t = os.time(), by = by, op = "unconfirm" })
		r.confirmed = false
		return r
	end)
	if deps.Log then deps.Log.add(uid, "confirm", "unconfirm", ("unconfirmed by the owner (user %d)"):format(by)) end
	for _, m in RESTORES do
		task.spawn(function()
			local res = call(m[1], "undoRestore", uid)
			if deps.Log then deps.Log.add(uid, "confirm", "undo " .. m[2], brief(res)) end
		end)
	end
end

-- ERASE (Roblox's right-to-erasure): every report by or about them goes, their lines in other reports become
-- "(erased)", a recording they're in goes, their confirm record and their anti-cheat records go. returns the counts
function Reports.erase(uid: number): any
	local gone, scrubbed = {}, 0
	upd(K .. "index", function(old: any)
		table.clear(gone)
		if type(old) ~= "table" then return nil end
		local keep = {}
		for _, e in old do
			if type(e) == "table" and (e.by == uid or e.who == uid) then table.insert(gone, e.id) else table.insert(keep, e) end
		end
		return if #gone > 0 then keep else nil
	end)
	for _, id in gone do del(K .. "r_" .. id); del(K .. "rec_" .. id) end
	local inv = get(K .. "inv_" .. uid)
	if type(inv) == "table" then
		for _, id in inv do
			if table.find(gone, id) then continue end
			local touched = false
			upd(K .. "r_" .. id, function(r: any)
				touched = false
				if type(r) ~= "table" then return nil end
				for _, l in r.chat or {} do
					if l.u == uid then l.u = 0; l.x = "(erased)"; touched = true end
				end
				if r.by == uid then r.by = 0; touched = true end
				if r.rec then r.rec = false; touched = true end -- (the recording had them in it: it goes)
				return if touched then r else nil
			end)
			del(K .. "rec_" .. id)
			if touched then scrubbed += 1 end
		end
	end
	del(K .. "inv_" .. uid)
	del(K .. "c_" .. uid)
	for i = #chat, 1, -1 do if chat[i].u == uid then table.remove(chat, i) end end
	local logLines = if deps.Log and deps.Log.erase then deps.Log.erase(uid) else 0
	names[uid] = nil
	return { reports = #gone, scrubbed = scrubbed, logLines = logLines }
end

-- reports older than KEEP_DAYS go (every 6 hours, from any server)
local function sweep()
	local old = {}
	upd(K .. "index", function(list: any)
		table.clear(old)
		if type(list) ~= "table" then return nil end
		local keep = {}
		for _, e in list do
			if type(e) == "table" and os.time() - (e.t or 0) > Reports.KEEP_DAYS * 86400 then table.insert(old, e.id) else table.insert(keep, e) end
		end
		return if #old > 0 then keep else nil
	end)
	for _, id in old do del(K .. "r_" .. id); del(K .. "rec_" .. id) end
end

-- ------------------------------------------------------------------ wiring (AntiCheat.server.luau calls this)
-- d = { Log = AntiCheatLog, flagsOf = (userId) -> anti-cheat state }
function Reports.init(d: any)
	deps = d
	local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
	local fn = Remotes:FindFirstChild("Report") :: RemoteFunction?
	if not fn then
		local r = Instance.new("RemoteFunction")
		r.Name = "Report"
		r.Parent = Remotes
		fn = r
	end
	local calls: { [Player]: { n: number, t: number } } = {}
	;(fn :: RemoteFunction).OnServerInvoke = function(p: Player, op: unknown, a: unknown, b: unknown, c: unknown): any
		local bt = calls[p]
		local t = os.clock()
		if not bt then bt = { n = 4, t = t }; calls[p] = bt end
		bt.n = math.min(4, bt.n + (t - bt.t) * 0.5); bt.t = t
		if bt.n < 1 then return { ok = false, why = "slow down" } end
		bt.n -= 1
		if op == "send" then
			local ok, res = pcall(send, p, a, b, c)
			return if ok then res else { ok = false, why = "something broke: try again" }
		elseif op == "reasons" then
			return Reports.REASONS
		end
		return nil
	end
	local function hook(p: Player)
		p.Chatted:Connect(function(msg: string, recipient: Player?) heard(p, msg, recipient, "chatted") end)
	end
	for _, p in Players:GetPlayers() do hook(p) end
	Players.PlayerAdded:Connect(hook)
	task.spawn(hookLegacyChat)
	Players.PlayerRemoving:Connect(function(p)
		left[p.UserId] = { t = os.clock(), p = p }
		sent[p] = nil; calls[p] = nil
	end)
	task.spawn(function()
		while true do
			for uid, l in left do if os.clock() - l.t > Reports.LEFT_SECS then left[uid] = nil end end
			task.wait(60)
		end
	end)
	task.spawn(function()
		task.wait(60)
		while true do
			pcall(sweep)
			task.wait(6 * 3600)
		end
	end)
end

-- (Studio tests, through ServerStorage.JankAC: somebody who "just left", so a solo test has someone to report)
function Reports.testLeft(uid: number)
	if STUDIO then left[uid] = { t = os.clock(), p = nil :: any } end
end
-- (Studio tests: what's in the chat buffer now, and how lines arrived)
function Reports.chatNow(): any
	local out = {}
	for _, l in chat do table.insert(out, { u = l.u, x = l.x, ago = math.floor(os.clock() - l.c) }) end
	return { lines = out, counts = table.clone(heardCount) }
end

return Reports
