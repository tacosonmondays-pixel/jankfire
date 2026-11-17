--!strict
-- MODES: JANKFIRE's classic modes, played from the Play screen's MODES tab (roblox/docs/MODES.md has the web rules
-- traced to the web code, and "Roblox adaptations" for what had to change; the numbers are in Shared.ModeConfig).
-- four so far, all free for all, every player their own side:
--   GUN GAME            a 19-rung ladder, one weapon at a time. a kill with your rung's weapon moves you up, a death to a
--                       melee weapon knocks you down one; the first kill on the last rung wins (10 min: highest rung)
--   ONE IN THE CHAMBER  a Revolver with one bullet (any hit kills) and a melee weapon. a kill gives a bullet (3 at most),
--                       no reloads, no items. 3 lives; the last one standing wins (6 min: lives, then kills)
--   DUCK RAIN           deathmatch, first to 20 (6 min), while sky ducks fall and open black holes that belong to nobody
--                       (their pull and blast are the duck item's own code: Utility.skyHole)
--   RANDOMIZER          deathmatch, first to 20 (6 min), a random weapon in every slot every life
-- and two team modes (two sides, PINK and CYAN, parties kept on one side):
--   TEAM DEATHMATCH     every kill on the other side scores for yours, first to 40 (6 min: the higher score, or a draw)
--   TAGS                a kill drops a tag; grab the other side's to score, your own to deny it; first to 25
-- a mode's match runs through Matches (Matches.startMode): its site, who's in it, who may hurt whom (everyone: their
-- own side each), the end screen, home, and every hook on it (Stats, RankedData, the Recorder). Matches hands this
-- module the match (m.rules = this module's rules): the spawns, the respawns, the clock, the HUD, the board and the
-- end. the mode's own state is m.ms
-- what the result says (for Party Ranked, RankedData's ffa rating), set before Matches.onEnd runs: m.ffa = true,
-- m.modeId, m.places[team] = finishing place (ties share one), m.results = { { player, id, team, place, score, kills,
-- deaths } } best first; the winner Matches.onEnd gets is the first place's team (nil: nobody won)
-- what the clients see (player attributes, ModeHud.client): ModeId, ModeMatch, MatchHud and RoundEnds (the scoreboard),
-- ModeRung / ModeLadder / ModeLead (gun game), ModeLives / ModeBullets / ModeOut / ModeLeft (one in the chamber),
-- ModeLead (deathmatch), ModeTeam / ModeScore (team modes); sky ducks arrive on ItemFx as { k = "skyduck", ... }; tags
-- are Models in workspace.JankModeTags (attributes Team, At)
-- Studio play tests: ServerStorage.JankModeTest (ModesServer), see Modes.test at the end
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local ModeConfig = require(Shared:WaitForChild("ModeConfig"))
local PlayConfig = require(Shared:WaitForChild("PlayConfig"))
local Weapons = require(Shared:WaitForChild("Weapons"))
local Roster = require(Shared:WaitForChild("Roster"))
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Arena = require(Shared:WaitForChild("Arena"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local RoundR = Remotes:WaitForChild("Round") :: RemoteEvent
local CalloutR = Remotes:WaitForChild("Callout") :: RemoteEvent
local AmmoR = Remotes:WaitForChild("Ammo") :: RemoteEvent
local ItemFx = Remotes:WaitForChild("ItemFx") :: RemoteEvent

local Modes = {}
local Fight: any, Matches: any, Utility: any
local W = Weapons.list
local S = Weapons.S
local now = os.clock
local ACC = "#ffc43d" -- (the HUD's one accent, Theme.ACCENT: the number that's yours)
local function stamp(t: number): number return workspace:GetServerTimeNow() + (t - now()) end
local function lerp(a: number, b: number, k: number): number return a + (b - a) * k end

type Seat = {
	p: Player?, f: any?, name: string, uid: number, team: number, ghost: boolean,
	kills: number, deaths: number, rung: number, lives: number, out: boolean, outAt: number, gone: boolean,
	own: { string }?, -- (the player's own picks: back on their keys after the match)
}
type MS = {
	def: any, seats: { Seat }, byP: { [Player]: Seat }, byF: { [any]: Seat }, ladder: { string }, orig: { string },
	target: number, time: number, liveAt: number, nextDrop: number, ducks: number, size: number, tops: { Vector3 }?,
	rayTop: number, spawns: { CFrame }?, over: boolean, winner: Seat?, lead: string, n0: number,
	teams: boolean, score: { number }, winTeam: number?, tags: { Tag }, sideSpawns: { [number]: { CFrame } },
}
-- a dog tag on the floor (tags): its side, where it floats, its model, when it goes
type Tag = { team: number, p: Vector3, model: Model, dies: number }
local liveTags: { [any]: boolean } = {} -- (the tags matches being played: the pickups run every frame)
local SIDES = ModeConfig.SIDES

-- ------------------------------------------------------------------ helpers
local function msOf(m: any): MS? return if m and m.rules and m.ms then m.ms :: MS else nil end
local function present(s: Seat): boolean
	if s.gone then return false end
	if s.ghost then return true end
	local p = s.p :: Player
	return p.Parent ~= nil and Matches.raw(p) ~= nil
end
local function callTo(s: Seat, text: string, dur: number)
	if s.p and (s.p :: Player).Parent then CalloutR:FireClient(s.p, text, dur) end
end
local function callAll(ms: MS, text: string, dur: number, but: Seat?)
	for _, s in ms.seats do if s ~= but then callTo(s, text, dur) end end
end
local function wname(id: string?): string
	local w = id and W[id]
	return if w then string.upper(w.name) else string.upper(tostring(id))
end
local function shuffle(t: { any })
	for i = #t, 2, -1 do
		local j = math.random(i)
		t[i], t[j] = t[j], t[i]
	end
end

-- ------------------------------------------------------------------ weapons per mode
-- a weapon this mode may hand out mid-life: on Roblox (Roster live, Weapons.list) and not the Shredder (a Tool only a
-- spawn hands out)
local function usable(id: string): boolean
	local e = Roster.byId[id]
	return e ~= nil and e.live and W[id] ~= nil and id ~= "shredder"
end
-- the weapon a ladder pick plays as: itself if it's here, else its nearest that is (one not on the ladder yet if it can)
local function resolve(id: string, have: { string }): string
	if usable(id) then return id end
	local list = ModeConfig.NEAREST[id] or { "ar" }
	for _, c in list do if usable(c) and not table.find(have, c) then return c end end
	for _, c in list do if usable(c) then return c end end
	return "ar"
end
-- web rollLadder: 10 guns, 5 silly, 3 melee, then the knife; each group shuffled, the weapons that sat out the last
-- match first. returns the rungs (what you hold) and the web weapon each one stands for
local lastLadder: { [string]: boolean } = {}
local function rollLadder(): ({ string }, { string })
	local G = ModeConfig.GUN
	local out, orig = {}, {}
	local function take(pool: { string }, n: number)
		local c = table.clone(pool)
		shuffle(c)
		local fresh, stale = {}, {}
		for _, id in c do table.insert(if lastLadder[id] then stale else fresh, id) end
		for _, id in stale do table.insert(fresh, id) end
		for i = 1, math.min(n, #fresh) do
			table.insert(out, resolve(fresh[i], out))
			table.insert(orig, fresh[i])
		end
	end
	take(G.guns, G.take.guns)
	take(G.silly, G.take.silly)
	take(G.melee, G.take.melee)
	table.insert(out, resolve(G.last, out))
	table.insert(orig, G.last)
	table.clear(lastLadder)
	for _, id in orig do lastLadder[id] = true end
	return out, orig
end
-- web randomLoadout: a random weapon in each slot from every weapon on Roblox in that slot (the Shredder too: a spawn
-- hands it out)
local function roll(): { string }
	local out = {}
	for _, slot in { "primary", "secondary", "melee" } do
		local c = {}
		for _, e in Roster.list do if e.slot == slot and e.live and W[e.id] then table.insert(c, e.id) end end
		table.insert(out, if #c > 0 then c[math.random(#c)] else Weapons.loadout[#out + 1])
	end
	return out
end
-- what a seat carries this life (nil: their own loadout)
local function kitFor(ms: MS, s: Seat): { string }?
	local k = ms.def.kind
	if k == "gun" then return { ms.ladder[s.rung] } end
	if k == "oitc" then
		local kit = {}
		for _, id in ModeConfig.OITC.kit do table.insert(kit, resolve(id, kit)) end
		return kit
	end
	if ms.def.id == "rand" then return roll() end
	return nil
end
-- the server armed a seat mid-life (a new rung): its keys, its gun in hand, everyone sees it
local function rearm(s: Seat)
	local f, p = s.f, s.p
	if not f or not p or not f.alive then return end
	Rules.arm(f, now())
	Fight.showWeapon(f)
	p:SetAttribute("Loadout", table.concat(Rules.loadoutOf(f), ","))
	p:SetAttribute("ArmT", (tonumber(p:GetAttribute("ArmT")) or 0) + 1)
end
-- one in the chamber: the Revolver's mag is your bullets (the server's count; your client is told)
local function setBullets(s: Seat, n: number)
	local f, p = s.f, s.p
	if not f or not p then return end
	local gun = ModeConfig.OITC.gun
	local a = f.ammo[gun]
	if a then a.mag = n; a.reloadUntil = 0 end
	p:SetAttribute("ModeBullets", n)
	AmmoR:FireClient(p, gun, n, 0)
	-- (again in a moment: a respawn's own reset on the client may land after this)
	task.delay(0.5, function()
		local a2 = f.ammo[gun]
		if p.Parent and a2 then AmmoR:FireClient(p, gun, a2.mag, 0) end
	end)
end
local function bulletsOf(s: Seat): number
	local a = s.f and s.f.ammo[ModeConfig.OITC.gun]
	return if a then a.mag else 0
end

-- ------------------------------------------------------------------ order, places, the HUD
-- best first: gun game by rung then kills; one in the chamber by lives then kills; deathmatch by kills then fewer
-- deaths. the winner of a won match goes first; a leaver goes last
local function better(ms: MS, a: Seat, b: Seat): boolean
	if a.gone ~= b.gone then return not a.gone end
	if ms.winner and (a == ms.winner) ~= (b == ms.winner) then return a == ms.winner end
	if ms.winTeam and a.team ~= b.team and (a.team == ms.winTeam or b.team == ms.winTeam) then return a.team == ms.winTeam end
	local k = ms.def.kind
	if k == "gun" and a.rung ~= b.rung then return a.rung > b.rung end
	if k == "oitc" and a.lives ~= b.lives then return a.lives > b.lives end
	if a.kills ~= b.kills then return a.kills > b.kills end
	if k ~= "gun" and k ~= "oitc" and a.deaths ~= b.deaths then return a.deaths < b.deaths end
	return a.team < b.team
end
-- two seats that finish level share a place (the team number only breaks the tie for the order)
local function tied(ms: MS, a: Seat, b: Seat): boolean
	if a.gone ~= b.gone or a == ms.winner or b == ms.winner then return false end
	if ms.teams then return a.team == b.team or ms.winTeam == nil end -- (a team mode: places are the sides')
	local k = ms.def.kind
	if k == "gun" then return a.rung == b.rung and a.kills == b.kills end
	if k == "oitc" then return a.lives == b.lives and a.kills == b.kills end
	return a.kills == b.kills and a.deaths == b.deaths
end
local function ordered(ms: MS): { Seat }
	local list = table.clone(ms.seats)
	table.sort(list, function(a, b) return better(ms, a, b) end)
	return list
end
local function leftIn(ms: MS): { Seat }
	local out = {}
	for _, s in ms.seats do if present(s) and not s.out then table.insert(out, s) end end
	return out
end

local function hudLine(m: any, ms: MS, s: Seat): string
	local k = ms.def.kind
	if k == "gun" then
		return ('GUN GAME · RUNG · <font color="%s">%d</font>/%d'):format(ACC, s.rung, #ms.ladder)
	elseif k == "oitc" then
		return ('ONE IN THE CHAMBER ·  · <font color="%s">%d</font> LEFT'):format(ACC, #leftIn(ms))
	elseif ms.teams then
		return ('%s ·  · <font color="%s">%d</font> – <font color="%s">%d</font>'):format(ms.def.name, SIDES[1].hex, ms.score[1], SIDES[2].hex, ms.score[2])
	end
	return ('%s · KILLS · <font color="%s">%d</font>/%d'):format(ms.def.name, ACC, s.kills, ms.target)
end
-- everyone's scoreboard line, clock and mode numbers
local function publish(m: any)
	local ms = msOf(m)
	if not ms then return end
	local list = ordered(ms)
	local top = list[1]
	-- the leader (deathmatch: kills, gun game: rung)
	local lead = ""
	if top then
		if ms.teams then lead = ""
		elseif ms.def.kind == "gun" then lead = ("%s|%d"):format(top.name, top.rung)
		elseif ms.def.kind == "oitc" then lead = ("%s|%d"):format(top.name, top.lives)
		else lead = ("%s|%d"):format(top.name, top.kills) end
	end
	local left = #leftIn(ms)
	for i, s in list do
		local p = s.p
		if not p or not p.Parent or s.gone then continue end
		p:SetAttribute("MatchHud", hudLine(m, ms, s))
		p:SetAttribute("RoundEnds", if m.phase == "live" then stamp(m.roundEnds) else nil)
		p:SetAttribute("ModeLead", lead)
		p:SetAttribute("ModePlace", i)
		if ms.teams then
			p:SetAttribute("ModeTeam", s.team)
			p:SetAttribute("ModeScore", ("%d|%d"):format(ms.score[1], ms.score[2]))
		elseif ms.def.kind == "gun" then p:SetAttribute("ModeRung", s.rung)
		elseif ms.def.kind == "oitc" then
			p:SetAttribute("ModeLives", s.lives)
			p:SetAttribute("ModeLeft", left)
			p:SetAttribute("ModeOut", s.out or nil)
		end
	end
end

-- ------------------------------------------------------------------ the end
local function clearTags(ms: MS)
	for _, t in ms.tags do t.model:Destroy() end
	table.clear(ms.tags)
end
-- the end: win = the seat that takes it (free for all), team = the side that takes it (team modes; nil: a draw)
local function finish(m: any, win: Seat?, team: number?)
	local ms = msOf(m)
	if not ms or ms.over then return end
	ms.over = true
	ms.winner = if ms.teams then nil else win
	ms.winTeam = if ms.teams then team else nil
	liveTags[m] = nil
	clearTags(ms)
	-- the result (RankedData's Party Ranked rating reads it in Matches.onEnd): a free-for-all's places are each player's;
	-- a team mode's are the sides' (1 and 2, or 1 and 1 for a draw)
	local list = ordered(ms)
	m.ffa = if ms.teams then nil else true
	m.modeId = ms.def.id
	m.places, m.results = {}, {}
	local place = 0
	for i, s in list do
		if ms.teams then place = if ms.winTeam == nil or s.team == ms.winTeam then 1 else 2
		elseif i == 1 or not tied(ms, s, list[i - 1]) then place = i end
		m.places[s.team] = place
		local score = if ms.teams then ms.score[s.team] elseif ms.def.kind == "gun" then s.rung elseif ms.def.kind == "oitc" then s.lives else s.kills
		table.insert(m.results, { player = s.p, id = s.uid, team = s.team, place = place, score = score, kills = s.kills, deaths = s.deaths, ghost = s.ghost or nil })
	end
	-- everyone's own loadout back for their next spawn (home), no more mode rules on them
	for _, s in ms.seats do
		local f = s.f
		if f then
			f.forced = nil
			f.noReload = nil
			if not f.nextLoadout and s.own then f.nextLoadout = s.own end
		end
		if s.p then (s.p :: Player):SetAttribute("NoReload", nil) end
	end
	publish(m)
	Matches.finish(m, if ms.teams then ms.winTeam elseif win then win.team else nil)
end

-- the end of the clock: deathmatch most kills, gun game highest rung, one in the chamber most lives. the top player
-- takes it if they got a kill (web endRound), else nobody does
local function timeUp(m: any, ms: MS)
	if ms.teams then
		-- the higher score takes it; level is a draw (web endRound: no winner, no roll)
		local a, b = ms.score[1], ms.score[2]
		finish(m, nil, if a > b then 1 elseif b > a then 2 else nil)
		return
	end
	local list = ordered(ms)
	local top = list[1]
	if top and not top.gone and top.kills >= 1 then finish(m, top) else finish(m, nil) end
end

-- ------------------------------------------------------------------ tags
local tagFolder: Folder? = nil
local function tagModel(team: number, at: Vector3): Model
	if not tagFolder or not tagFolder.Parent then
		local f = Instance.new("Folder")
		f.Name = "JankModeTags"
		f.Parent = workspace
		tagFolder = f
	end
	local mdl = Instance.new("Model")
	mdl.Name = "Tag"
	local function part(name: string, size: Vector3, color: Color3, mat: Enum.Material): Part
		local q = Instance.new("Part")
		q.Name = name; q.Size = size; q.Color = color; q.Material = mat
		q.Anchored = true; q.CanCollide = false; q.CanQuery = false; q.CanTouch = false; q.CastShadow = false
		q.CFrame = CFrame.new(at)
		q.Parent = mdl
		return q
	end
	-- a plate in the side's colour (0.34 x 0.5 x 0.05 m) in a white frame (web objective.js)
	local frame = part("Frame", Vector3.new(0.4, 0.56, 0.04) * S, Color3.fromRGB(236, 234, 228), Enum.Material.SmoothPlastic)
	part("Plate", Vector3.new(0.34, 0.5, 0.05) * S, Color3.fromHex(string.sub(SIDES[team].hex, 2)), Enum.Material.Neon)
	mdl.PrimaryPart = frame
	mdl:SetAttribute("Team", team)
	mdl:SetAttribute("At", at)
	mdl.Parent = tagFolder
	return mdl
end
-- web dropTag: a kill on the other side during a live round drops the victim's tag on the floor under them (a ray 60 m
-- down from 1 m over their feet), 0.9 m over it; over the void, under the killer
local function dropTag(m: any, ms: MS, vs: Seat, ks: Seat)
	local T = ModeConfig.TAGS
	local function under(from: Vector3?): Vector3?
		if not from then return nil end
		local hit = Fight.castMap(from + Vector3.new(0, 1 * S, 0), Vector3.new(0, -1, 0), T.drop)
		return if hit then hit.Position + Vector3.new(0, T.up, 0) else nil
	end
	local at = under(if vs.f then Fight.feet(vs.f) else nil)
	if not at and ks.f then
		-- (a ghost has no body: a Studio test drops its tag a few steps from its killer)
		local ft = Fight.feet(ks.f)
		local off = if vs.ghost then Vector3.new(math.random(-12, 12), 0, math.random(-12, 12)) else Vector3.zero
		at = under(if ft then ft + off else nil) or under(ft)
	end
	if not at then return end
	table.insert(ms.tags, { team = vs.team, p = at, model = tagModel(vs.team, at), dies = now() + T.life })
end
-- a seat reached a tag: the other side's is a confirm (+1 to theirs, while live), their own side's a deny
local function grabTag(m: any, ms: MS, s: Seat, tag: Tag)
	local i = table.find(ms.tags, tag)
	if not i then return end
	table.remove(ms.tags, i)
	tag.model:Destroy()
	if tag.team ~= s.team then
		if m.phase ~= "live" then return end
		ms.score[s.team] += 1
		callTo(s, "KILL CONFIRMED +1", 1.1)
		if ms.score[s.team] >= ms.target then publish(m); finish(m, nil, s.team); return end
	else
		callTo(s, "KILL DENIED", 1.1)
	end
	publish(m)
end
-- every frame in a live tags match: tags that ran out go, anyone alive within 1.9 m of one (from their middle) takes it
local function tagTick(m: any)
	local ms = msOf(m)
	if not ms or ms.over then liveTags[m] = nil; return end
	local t = now()
	for _, tag in table.clone(ms.tags) do
		if t >= tag.dies then
			local i = table.find(ms.tags, tag)
			if i then table.remove(ms.tags, i) end
			tag.model:Destroy()
			continue
		end
		for _, s in ms.seats do
			local f = s.f
			if not f or not f.alive or not present(s) then continue end
			local ft = Fight.feet(f)
			if ft and (ft + Vector3.new(0, ModeConfig.TAGS.up, 0) - tag.p).Magnitude <= ModeConfig.TAGS.grab then grabTag(m, ms, s, tag); break end
		end
		if ms.over then return end
	end
end

-- ------------------------------------------------------------------ kills
local function gunUp(m: any, ms: MS, ks: Seat)
	if ks.rung >= #ms.ladder then finish(m, ks); return end
	ks.rung += 1
	local f = ks.f
	if f then f.forced = { ms.ladder[ks.rung] } end
	rearm(ks)
	if ks.rung == #ms.ladder then
		callTo(ks, "LAST RUNG · ONE KILL WINS", 1.8)
		callAll(ms, ks.name .. " IS ON THE LAST RUNG", 1.6, ks)
	else
		callTo(ks, ("%s · %d/%d"):format(wname(ms.ladder[ks.rung]), ks.rung, #ms.ladder), 1.2)
	end
end

-- one death in a mode's match. ks = the killer's seat (nil: a fall nobody gets, or a sky duck nobody earned), vs the
-- victim's, w / via as Fight's kill (via = what a credited fall was last hit with). the real kills (Fight.onKill) and a
-- Studio test's ghost kills both come through here
local function scoreKill(m: any, ks: Seat?, vs: Seat, w: string, via: string?)
	local ms = msOf(m)
	if not ms or ms.over or m.phase ~= "live" then return end
	vs.deaths += 1
	local real = ks ~= nil and ks ~= vs
	if real then (ks :: Seat).kills += 1 end
	local k = ms.def.kind
	if k == "gun" then
		-- up: a kill with your rung's weapon (a fall counts with what knocked them off). down: dying to a melee weapon
		local kw = via or w
		if real and kw == ms.ladder[(ks :: Seat).rung] then
			gunUp(m, ms, ks :: Seat)
			if ms.over then return end
		end
		if real and W[w] and W[w].kind == "melee" and vs.rung > 1 then
			vs.rung -= 1
			callTo(vs, "HUMILIATED", 1.4)
		end
		if vs.f then vs.f.forced = { ms.ladder[vs.rung] } end
	elseif k == "oitc" then
		-- a life gone (any death), the bullets with it; the killer gets one (3 at most)
		vs.lives = math.max(0, vs.lives - 1)
		if real and ks and not ks.ghost then
			local n = math.min(ModeConfig.OITC.maxBullets, bulletsOf(ks) + 1)
			setBullets(ks, n)
			callTo(ks, ("+1 BULLET · %d IN THE CHAMBER"):format(n), 1.2)
		end
		if vs.lives <= 0 then
			vs.out = true
			vs.outAt = now()
			callTo(vs, "OUT OF LIVES", 2)
			callAll(ms, vs.name .. " IS OUT OF LIVES", 1.4, vs)
		end
		local left = leftIn(ms)
		if ms.n0 >= 2 and #left <= 1 then publish(m); finish(m, left[1]); return end
	elseif k == "tdm" then
		-- every kill on the other side is a point for yours (web room.js: score[killer.team]++)
		if real and (ks :: Seat).team ~= vs.team then
			local t = (ks :: Seat).team
			ms.score[t] += 1
			if ms.score[t] >= ms.target then publish(m); finish(m, nil, t); return end
		end
	elseif k == "tags" then
		-- kills alone score nothing: a kill on the other side drops the victim's tag
		if real and (ks :: Seat).team ~= vs.team then dropTag(m, ms, vs, ks :: Seat) end
	else
		if real and (ks :: Seat).kills >= ms.target then publish(m); finish(m, ks); return end
	end
	publish(m)
end

-- ------------------------------------------------------------------ spawns
-- the site's spawn markers (Spawns, then TeamSpawns), each facing the middle
local function spawnList(m: any): { CFrame }
	local ms = m.ms :: MS
	if ms.spawns then return ms.spawns end
	local site = m.site.model :: Model
	local mid = site:GetPivot().Position
	local out = {}
	for _, fname in { "Spawns", "TeamSpawns" } do
		local f = site:FindFirstChild(fname)
		if f then
			for _, s in f:GetChildren() do
				if s:IsA("BasePart") then
					local pos = s.Position + Vector3.new(0, 0.1, 0)
					local toward = Vector3.new(mid.X, pos.Y, mid.Z)
					table.insert(out, if (toward - pos).Magnitude > 0.5 then CFrame.lookAt(pos, toward) else CFrame.new(pos))
				end
			end
		end
	end
	if #out == 0 then table.insert(out, CFrame.new(mid + Vector3.new(0, 5, 0))) end
	ms.spawns = out
	return out
end
-- a team mode's side's spawns (web pickSpawn: team 1 the arena's "att" team spawns, team 2 its "def"), each facing the
-- middle; none: every spawn
local function sideSpawns(m: any, team: number): { CFrame }
	local ms = m.ms :: MS
	local have = ms.sideSpawns[team]
	if have then return have end
	local site = m.site.model :: Model
	local mid = site:GetPivot().Position
	local want = if team == 1 then "att" else "def"
	local out = {}
	local ts = site:FindFirstChild("TeamSpawns")
	if ts then
		for _, sp in ts:GetChildren() do
			if sp:IsA("BasePart") and sp.Name == want then
				local pos = sp.Position + Vector3.new(0, 0.1, 0)
				local toward = Vector3.new(mid.X, pos.Y, mid.Z)
				table.insert(out, if (toward - pos).Magnitude > 0.5 then CFrame.lookAt(pos, toward) else CFrame.new(pos))
			end
		end
	end
	if #out == 0 then out = spawnList(m) end
	ms.sideSpawns[team] = out
	return out
end
-- web pickSpawn: the spawn farthest from the nearest living enemy, plus a random 0-15 m
local function spawnAt(m: any, p: Player): (Vector3, Vector3?)
	local ms = m.ms :: MS
	local me = ms.byP[p]
	local best, bestScore = nil, -math.huge
	for _, cf in (if ms.teams and me then sideSpawns(m, me.team) else spawnList(m)) do
		local near = 1e6
		for _, s in ms.seats do
			if s ~= me and s.f and s.f.alive and not (ms.teams and me and s.team == me.team) then
				local ft = Fight.feet(s.f)
				if ft then near = math.min(near, (ft - cf.Position).Magnitude) end
			end
		end
		local score = near + math.random() * 15 * S
		if score > bestScore then best, bestScore = cf, score end
	end
	local cf = best :: CFrame
	return cf.Position, cf.LookVector
end

-- ------------------------------------------------------------------ duck rain: sky ducks
local skyId = 0
local function playersOf(ms: MS): { Player }
	local out = {}
	for _, s in ms.seats do if s.p and (s.p :: Player).Parent and not s.gone then table.insert(out, s.p :: Player) end end
	return out
end
-- the arena's exposed tops: a grid of rays straight down over where the spawns are (+25 m around), each hit facing up
-- and above the fall line. every point is 2.5 x 2.5 m of floor (web lava.js surfaces). kept per arena, relative to its
-- pivot (a copy has the same tops)
local topsCache: { [string]: { pts: { Vector3 }, top: number } } = {}
local function tops(m: any): ({ Vector3 }, number)
	local site = m.site.model :: Model
	local pivot = site:GetPivot().Position
	local c = topsCache[m.arena]
	if not c then
		local D = ModeConfig.DUCKRAIN
		local lo, hi = Vector3.new(math.huge, math.huge, math.huge), Vector3.new(-math.huge, -math.huge, -math.huge)
		for _, cf in spawnList(m) do lo = lo:Min(cf.Position); hi = hi:Max(cf.Position) end
		if lo.X == math.huge then lo, hi = pivot - Vector3.new(150, 30, 150), pivot + Vector3.new(150, 30, 150) end
		local pad = 25 * S
		local params = RaycastParams.new()
		params.FilterType = Enum.RaycastFilterType.Include
		params.FilterDescendantsInstances = { site }
		params.RespectCanCollide = true
		local killY = Arena.killY(site)
		local y0 = hi.Y + 120 * S
		local pts, best = {}, -math.huge
		local n = 0
		for x = lo.X - pad, hi.X + pad, D.grid do
			for z = lo.Z - pad, hi.Z + pad, D.grid do
				local r = workspace:Raycast(Vector3.new(x, y0, z), Vector3.new(0, -(y0 - killY), 0), params)
				if r and r.Normal.Y > 0.6 and r.Position.Y > killY + 3 then
					table.insert(pts, r.Position - pivot)
					best = math.max(best, r.Position.Y - pivot.Y)
				end
				n += 1
				if n % 400 == 0 then task.wait() end
			end
		end
		c = { pts = pts, top = if best > -math.huge then best else 0 }
		topsCache[m.arena] = c
	end
	local cc = c :: { pts: { Vector3 }, top: number }
	local out = table.create(#cc.pts)
	for _, p in cc.pts do table.insert(out, p + pivot) end
	return out, pivot.Y + cc.top
end
local function castDown(m: any, x: number, z: number, from: number): Vector3?
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = { m.site.model }
	params.RespectCanCollide = true
	local killY = Arena.killY(m.site.model)
	local r = workspace:Raycast(Vector3.new(x, from, z), Vector3.new(0, -(from - killY), 0), params)
	if r and r.Position.Y > killY + 3 then return r.Position end
	return nil
end
local function skyDuck(m: any, ms: MS)
	local D = ModeConfig.DUCKRAIN
	local pts = ms.tops
	if not pts or #pts == 0 then return end
	local from = ms.rayTop
	local land: Vector3? = nil
	-- half of them land 2-14 m from someone alive in the match, the rest on a random exposed top (weighted by area:
	-- every grid point is the same area)
	if math.random() < D.near then
		local alive = {}
		for _, s in ms.seats do if s.f and s.f.alive and present(s) then table.insert(alive, s.f) end end
		if #alive > 0 then
			local ft = Fight.feet(alive[math.random(#alive)])
			if ft then
				for _ = 1, 4 do
					local a, d = math.random() * math.pi * 2, lerp(D.nearMin, D.nearMax, math.random())
					land = castDown(m, ft.X + math.cos(a) * d, ft.Z + math.sin(a) * d, from)
					if land then break end
				end
			end
		end
	end
	if not land then
		local p = pts[math.random(#pts)]
		local j = D.grid / 2
		land = castDown(m, p.X + (math.random() * 2 - 1) * j, p.Z + (math.random() * 2 - 1) * j, from) or p
	end
	local at = land :: Vector3
	-- the fall: from 46 m above where it lands (under the ray's start), straight down from 6 m/s at 22 m/s2
	local top = math.min(at.Y + D.drop, from - 1)
	local h = math.max(0, top - at.Y)
	local eta = math.min(D.maxFall, (-D.v0 + math.sqrt(D.v0 * D.v0 + 2 * D.g * h)) / D.g)
	skyId += 1
	local id = skyId
	ms.ducks += 1
	for _, p in playersOf(ms) do ItemFx:FireClient(p, { k = "skyduck", id = id, p = at, top = top, ms = math.floor(eta * 1000), v0 = D.v0, g = D.g }) end
	task.delay(eta, function()
		if not m.on or ms.over then return end
		-- it landed on someone: it sticks to them and the hole rides them
		local on: any = nil
		for _, s in ms.seats do
			local f = s.f
			if not f or not f.alive or not present(s) then continue end
			local ft = Fight.feet(f)
			if ft and Vector3.new(ft.X - at.X, 0, ft.Z - at.Z).Magnitude <= 0.7 * S and ft.Y > at.Y - 1 * S and ft.Y < at.Y + 2.2 * S then on = f; break end
		end
		Utility.skyHole(at + Vector3.new(0, 0.9 * S, 0), on, D.hole)
	end)
end
local function rainTick(m: any, ms: MS)
	if ms.def.id ~= "duckrain" or m.phase ~= "live" or ms.over or not ms.tops then return end
	local t = now()
	if t < ms.nextDrop then return end
	local D = ModeConfig.DUCKRAIN
	local top = 0
	for _, s in ms.seats do top = math.max(top, s.kills) end
	local k = math.clamp(math.max((t - ms.liveAt) / ms.time, top / ms.target), 0, 1)
	ms.nextDrop = t + lerp(D.everyFrom, D.everyTo, k)
	local n = math.max(1, math.floor(lerp(D.countFrom, D.countTo, k) * ms.size + (math.random() - 0.5) + 0.5))
	for _ = 1, n do skyDuck(m, ms) end
end

-- ------------------------------------------------------------------ the rules Matches calls (m.rules)
local RULES: any = {}
local pending: any = nil -- (Modes.start -> begin: the ghosts that come with it)

function RULES.begin(m: any)
	local def = ModeConfig.byId[m.mode]
	local kind = def.kind
	local teamMode = def.sides == 2
	local ms: MS = {
		def = def, seats = {}, byP = {}, byF = {}, ladder = {}, orig = {},
		target = if kind == "tdm" then ModeConfig.TDM.target elseif kind == "tags" then ModeConfig.TAGS.target else ModeConfig.DM.target,
		time = if kind == "gun" then ModeConfig.GUN.time elseif kind == "oitc" then ModeConfig.OITC.time
			elseif kind == "tdm" then ModeConfig.TDM.time elseif kind == "tags" then ModeConfig.TAGS.time else ModeConfig.DM.time,
		liveAt = 0, nextDrop = math.huge, ducks = 0, size = 1, tops = nil, rayTop = 0, spawns = nil, over = false, winner = nil, lead = "", n0 = 0,
		teams = teamMode, score = { 0, 0 }, winTeam = nil, tags = {}, sideSpawns = {},
	}
	m.ms = ms
	if kind == "gun" then ms.ladder, ms.orig = rollLadder() end
	local ghosts = pending or {}
	pending = nil
	local function playerSeat(p: Player, t: number): Seat
		local f = Fight.byPlayer[p]
		local s: Seat = { p = p, f = f, name = p.DisplayName, uid = p.UserId, team = t, ghost = false, kills = 0, deaths = 0, rung = 1,
			lives = ModeConfig.OITC.lives, out = false, outAt = 0, gone = false,
			own = if f then (f.nextLoadout or (f.loadout and table.clone(f.loadout))) else nil }
		ms.byP[p] = s
		if f then ms.byF[f] = s end
		return s
	end
	local function ghostSeat(g: any, i: number, t: number): Seat
		return { p = nil, f = nil, name = tostring(g.name or ("STAND-IN " .. i)), uid = tonumber(g.id) or -i, team = t, ghost = true,
			kills = 0, deaths = 0, rung = 1, lives = ModeConfig.OITC.lives, out = false, outAt = 0, gone = false, own = nil }
	end
	if teamMode then
		-- two sides: everyone on theirs, then the ghosts (each on the side it came with, else filling the smaller one)
		for t, list in m.teams do for _, p in list do table.insert(ms.seats, playerSeat(p, t)) end end
		for i, g in ghosts do
			local n1, n2 = 0, 0
			for _, s in ms.seats do if s.team == 1 then n1 += 1 else n2 += 1 end end
			local t = if g.team == 1 or g.team == 2 then g.team elseif n2 < n1 then 2 else 1
			table.insert(ms.seats, ghostSeat(g, i, t))
		end
	else
		local gi = 0
		for t, list in m.teams do
			local p = list[1]
			if p then
				table.insert(ms.seats, playerSeat(p, t))
			else
				gi += 1
				table.insert(ms.seats, ghostSeat(ghosts[gi] or {}, gi, t))
			end
		end
	end
	ms.n0 = #ms.seats
	-- (Studio tests: a gun game can start further up the ladder, web JF_GG_START)
	local gs = script:GetAttribute("TestGunStart")
	if kind == "gun" and type(gs) == "number" then for _, s in ms.seats do s.rung = math.clamp(math.floor(gs), 1, #ms.ladder) end end
	m.round = 1
	m.phase = "ready"
	-- the mode's kit on everyone, then a fresh body for each at the spawn farthest from the others
	for _, s in ms.seats do
		local p, f = s.p, s.f
		if not p or not f then continue end
		f.forced = kitFor(ms, s)
		f.noReload = if kind == "oitc" then true else nil
		p:SetAttribute("NoReload", if kind == "oitc" then true else nil)
		p:SetAttribute("ModeId", def.id)
		p:SetAttribute("ModeMatch", m.id)
		p:SetAttribute("ModeLadder", if kind == "gun" then table.concat(ms.ladder, ",") else nil)
		p:SetAttribute("ModeTarget", if kind == "dm" then ms.target else nil)
		p:SetAttribute("ModeOut", nil)
		f.alive = false
		task.spawn(Fight.spawn, f)
	end
	publish(m)
	-- the arena's name, the mode's name, its rules line; then the clock runs
	task.delay(0.4, function() if m.on then callAll(ms, Arena.title(m.arena), 1.0) end end)
	task.delay(1.5, function() if m.on then callAll(ms, def.name, 1.2) end end)
	task.delay(2.8, function()
		if not m.on then return end
		if teamMode then
			for _, s in ms.seats do callTo(s, ("YOU ARE %s · %s"):format(SIDES[s.team].name, def.rule), 1.1) end
		else
			callAll(ms, def.rule, 1.1)
		end
	end)
	if def.id == "duckrain" then
		task.spawn(function()
			local pts, top = tops(m)
			ms.tops = pts
			ms.rayTop = top + ModeConfig.DUCKRAIN.above
			local D = ModeConfig.DUCKRAIN
			local area = #pts * (D.grid / S) ^ 2
			ms.size = math.clamp(math.sqrt(area / D.areaPer), D.sizeMin, D.sizeMax)
		end)
	end
	task.delay(ModeConfig.READY, function()
		if not m.on or m.phase ~= "ready" or ms.over then return end
		m.phase = "live"
		ms.liveAt = now()
		local tt = script:GetAttribute("TestTime") -- (test knob: a shorter clock in a playtest)
		m.roundEnds = now() + (if type(tt) == "number" then tt else ms.time)
		ms.nextDrop = now() + ModeConfig.DUCKRAIN.first
		if kind == "tags" then liveTags[m] = true end
		publish(m)
		for _, p in playersOf(ms) do RoundR:FireClient(p, { start = true, mode = def.id }) end
	end)
end

function RULES.spawnAt(m: any, p: Player): (Vector3, Vector3?)
	return spawnAt(m, p)
end

-- Fight asks 2.5 s after a death: true = no respawn (the match is over, or you're out of lives). a randomizer life
-- gets its roll here, just before the spawn arms it
function RULES.holdRespawn(m: any, f: any): boolean
	local ms = msOf(m)
	if not ms or ms.over or m.phase == "over" or not m.on then return true end
	local s = ms.byF[f]
	if not s or s.out then return true end
	if ms.def.id == "rand" then f.forced = roll() end
	return false
end

-- every Matches tick (0.15 s): the clock, leavers, the sky ducks
function RULES.check(m: any)
	local ms = msOf(m)
	if not ms or ms.over then return end
	-- who left
	local changed = false
	for _, s in ms.seats do
		if not s.gone and not s.ghost and not present(s) then s.gone = true; changed = true end
	end
	local real, inn = 0, {}
	for _, s in ms.seats do
		if present(s) then
			table.insert(inn, s)
			if not s.ghost then real += 1 end
		end
	end
	if real == 0 then finish(m, nil); return end
	if ms.teams then
		-- everyone on one side left: the other takes it
		local has = { false, false }
		for _, s in inn do has[s.team] = true end
		if not has[1] or not has[2] then finish(m, nil, if has[1] then 1 elseif has[2] then 2 else nil); return end
	elseif #inn <= 1 and ms.n0 >= 2 then finish(m, inn[1]); return end
	if ms.def.kind == "oitc" then
		local left = leftIn(ms)
		if m.phase == "live" and #left <= 1 and ms.n0 >= 2 then finish(m, left[1]); return end
	end
	if changed then publish(m) end
	if m.phase ~= "live" then return end
	if now() >= m.roundEnds then timeUp(m, ms); return end
	rainTick(m, ms)
end

function RULES.setHud(m: any) publish(m) end

-- the end screen's board: { name, col, col, userId }, with the two columns' names (nil: KILLS, DEATHS)
function RULES.board(m: any): { { any } }
	local ms = m.ms :: MS
	local out = {}
	for _, s in ordered(ms) do
		local k = ms.def.kind
		if k == "gun" then
			local rung = if s == ms.winner then "WON" else ("%d/%d"):format(s.rung, #ms.ladder)
			table.insert(out, { s.name, rung, s.kills, s.uid })
		elseif k == "oitc" then
			table.insert(out, { s.name, s.lives, s.kills, s.uid })
		else
			table.insert(out, { s.name, s.kills, s.deaths, s.uid })
		end
	end
	return out
end
function RULES.cols(m: any): { string }?
	local k = (m.ms :: MS).def.kind
	if k == "gun" then return { "RUNG", "KILLS" } end
	if k == "oitc" then return { "LIVES", "KILLS" } end
	return nil
end
function RULES.label(m: any, team: number): string?
	if (m.ms :: MS).teams then return SIDES[team] and SIDES[team].name end
	for _, s in (m.ms :: MS).seats do if s.team == team then return s.name end end
	return nil
end
-- (Matches.backToHub) the players are going home: the mode's marks off them
function RULES.home(m: any)
	local ms = msOf(m)
	if not ms then return end
	liveTags[m] = nil
	clearTags(ms)
	for _, s in ms.seats do
		local p = s.p
		if p and p.Parent then
			for _, a in { "ModeId", "ModeMatch", "ModeLadder", "ModeTarget", "ModeRung", "ModeLead", "ModePlace", "ModeLives", "ModeLeft", "ModeOut", "ModeBullets", "NoReload", "ModeTeam", "ModeScore" } do
				p:SetAttribute(a, nil)
			end
		end
		local f = s.f
		if f then f.forced = nil; f.noReload = nil end
	end
end

-- ------------------------------------------------------------------ starting one (PlayConfig's start, from Party)
-- sides as Party.start found them (one list per queue entry: a whole party), opts as Matches.startQueued's. everyone
-- becomes their own side (a party's members fight each other too: it's a free-for-all). a Studio test's stand-ins
-- (negative ids in opts.rated) come along as ghosts: seats with no body, moved by JankModeTest
function Modes.start(id: string, sides: { { Player } }, opts: any, ghosts: { any }?): (any?, string?)
	local def = ModeConfig.byId[id]
	if not def then return nil, "no such mode" end
	local teamMode = def.sides == 2
	local solo = {}
	if teamMode then
		-- (a team mode keeps the queue's two sides as they are: parties together)
		for t = 1, 2 do solo[t] = table.clone(sides[t] or {}) end
	else
		for _, list in sides do for _, p in list do table.insert(solo, { p }) end end
	end
	local gs = ghosts or {}
	if not ghosts and RunService:IsStudio() and type(opts) == "table" and type(opts.rated) == "table" and type(opts.rated.teams) == "table" then
		local n = 0
		for t, list in opts.rated.teams do
			for _, x in list do
				if type(x.id) == "number" and x.id < 0 then n += 1; table.insert(gs, { id = x.id, name = "STAND-IN " .. n, team = t }) end
			end
		end
	end
	if not teamMode then for _ in gs do table.insert(solo, {}) end end
	if #solo < 1 or (teamMode and #solo[1] + #solo[2] < 1) then return nil, "nobody" end
	local o = if type(opts) == "table" then table.clone(opts) else {}
	o.rules, o.mode = RULES, id
	o.hold, o.holdWin = nil, nil -- (a mode with stand-ins isn't held: the ghosts play it)
	pending = gs
	local m, why = Matches.startMode(solo, o)
	pending = nil
	return m, why
end

-- ------------------------------------------------------------------ wiring
function Modes.init(fight: any, matches: any, utility: any, recorder: any?)
	Fight, Matches, Utility = fight, matches, utility
	-- tags: the pickups every frame (a running player covers more than a tag's reach in a Matches tick)
	RunService.Heartbeat:Connect(function()
		for m in liveTags do tagTick(m) end
	end)
	-- the cards' start (Party.start calls it when the queue forms a match of this mode)
	for _, def in ModeConfig.LIST do
		local entry = PlayConfig.byId[def.id]
		if entry then entry.start = function(sides: { { Player } }, opts: any) return Modes.start(def.id, sides, opts) end end
	end
	Fight.onKill(function(info: any)
		local v = info.v
		if v.kind ~= "player" then return end
		local m = Matches.raw(v.ref :: Player)
		local ms = msOf(m)
		if not ms then return end
		local vs = ms.byF[v]
		if not vs then return end
		local ks = if info.k then ms.byF[info.k] else nil
		scoreKill(m, ks, vs, info.w, info.via)
	end)
	-- a fresh life in one in the chamber: one bullet (the spawn filled the mag)
	Fight.onSpawn(function(f: any)
		if f.kind ~= "player" then return end
		local ms = msOf(Matches.raw(f.ref :: Player))
		if not ms or ms.over then return end
		local s = ms.byF[f]
		if s and ms.def.kind == "oitc" then setBullets(s, ModeConfig.OITC.bullets) end
	end)
	-- one in the chamber: every Revolver shot the server took is a bullet gone (the HUD's pips)
	Fight.onShot(function(f: any, wid: string)
		if f.kind ~= "player" or wid ~= ModeConfig.OITC.gun then return end
		local ms = msOf(Matches.raw(f.ref :: Player))
		if not ms or ms.def.kind ~= "oitc" then return end
		local a = f.ammo[wid];
		(f.ref :: Player):SetAttribute("ModeBullets", if a then a.mag else 0)
	end)
	-- one in the chamber: a Revolver hit always kills (web room.js oitcHit: 999)
	Fight.modDamage = function(t: any, amt: number, by: any, wid: string): number
		if wid ~= ModeConfig.OITC.gun or not by or by.kind ~= "player" or by == t then return amt end
		local ms = msOf(Matches.raw(by.ref :: Player))
		if ms and ms.def.kind == "oitc" then return ModeConfig.OITC.hit end
		return amt
	end
	-- no items in one in the chamber and gun game (web noItem)
	Fight.noItems = function(f: any): boolean
		if f.kind ~= "player" then return false end
		local ms = msOf(Matches.raw(f.ref :: Player))
		return ms ~= nil and (ms.def.kind == "oitc" or ms.def.kind == "gun")
	end
	-- the killcam only for a player who won't be back this match (out of lives): a 2.5 s respawn would cut it off
	if recorder then
		recorder.killcamFor = function(p: Player): boolean
			local ms = msOf(Matches.raw(p))
			if not ms then return true end
			local s = ms.byP[p]
			return s ~= nil and s.out
		end
	end
end

-- ------------------------------------------------------------------ Studio tests (ServerStorage.JankModeTest)
--   ("start", mode, player, ghostNames)   the player and ghosts (by name) straight into a match of that mode
--   ("kill", player, killerName|nil, victimName, weapon?)   a death in that player's match: a ghost's, or the player's
--     own (a real death through Fight: by a ghost it counts as theirs). names are seat names (DisplayName, or the
--     player's Name). weapon nil = the killer's rung weapon (gun game) / the Revolver (one in the chamber) / "ar"
--   ("state", player)   the player's match: phase, clock, seats, ladder, ducks
--   ("time", secs) the clock of every match started from now on (nil: the mode's own); ("gunstart", rung) likewise
--   ("end", player)    the clock runs out now
--   ("grab", player, seatName)   that seat takes the nearest tag (tags);  ("tags", player) where the tags are
function Modes.test(op: string, a: any, b: any, c: any, d: any): any
	if not RunService:IsStudio() then return nil end
	if op == "start" then
		local p = b :: Player
		local gs = {}
		for i, n in (if type(c) == "table" then c else {}) do table.insert(gs, { id = -i, name = n, team = if i % 2 == 1 then 2 else 1 }) end
		local m, why = Modes.start(tostring(a), { { p } }, { queue = "test:" .. tostring(a) }, gs)
		return if m then { id = m.id, arena = m.arena, site = m.site.model.Name } else { why = why }
	elseif op == "time" then script:SetAttribute("TestTime", a); return true
	elseif op == "gunstart" then script:SetAttribute("TestGunStart", a); return true
	end
	local p = if typeof(a) == "Instance" and a:IsA("Player") then a else nil
	local mm = nil
	for _, pl in Players:GetPlayers() do
		local x = Matches.raw(pl)
		if x and x.ms and (p == nil or pl == p) then mm = x; break end
	end
	local ms = msOf(mm)
	if not ms then return { why = "no mode match" } end
	local m = mm :: any
	if op == "state" then
		local seats = {}
		for _, s in ms.seats do
			table.insert(seats, { name = s.name, team = s.team, ghost = s.ghost, kills = s.kills, deaths = s.deaths, rung = s.rung, lives = s.lives, out = s.out,
				gone = s.gone, alive = if s.f then s.f.alive else nil, loadout = if s.f then table.concat(Rules.loadoutOf(s.f), ",") else nil,
				bullets = if s.f then bulletsOf(s) else nil })
		end
		return { mode = ms.def.id, phase = m.phase, left = m.roundEnds - now(), seats = seats, ladder = ms.ladder, orig = ms.orig,
			ducks = ms.ducks, size = ms.size, tops = if ms.tops then #ms.tops else nil, over = ms.over, arena = m.arena,
			score = ms.score, tags = #ms.tags, team = if ms.teams then true else nil }
	elseif op == "kill" then
		local function seatNamed(n: any): Seat?
			for _, s in ms.seats do if s.name == n or (s.p and (s.p :: Player).Name == n) then return s end end
			return nil
		end
		local ks, vs = seatNamed(b), seatNamed(c)
		if not vs then return { why = "no victim " .. tostring(c) } end
		local w = if type(d) == "string" then d
			elseif ms.def.kind == "gun" and ks then ms.ladder[ks.rung]
			elseif ms.def.kind == "oitc" then ModeConfig.OITC.gun else "ar"
		if vs.ghost then
			scoreKill(m, ks, vs, w, nil)
		else
			-- the real player dies through Fight (its respawn, the HUD, the feed); a ghost killer is credited here
			local f = vs.f
			if not f or not f.alive then return { why = "not alive" } end
			if ks and ks.ghost then
				-- (Fight's hooks see a death nobody got and this module skips it; the ghost's kill is scored here)
				local info = Rules.kill(f, nil, w, now())
				local saved = ms.byF[f]
				ms.byF[f] = nil
				Fight.died(info, Vector3.new(0, 20, 0))
				ms.byF[f] = saved
				scoreKill(m, ks, vs, w, nil)
			else
				Fight.hurt(f, 999, ks and ks.f or nil, w, false)
			end
		end
		return Modes.test("state", p)
	elseif op == "end" then
		m.roundEnds = now()
		return true
	elseif op == "grab" then -- (player, seatName) that seat takes the nearest tag (a ghost has no feet: the newest)
		local s: Seat? = nil
		for _, x in ms.seats do if x.name == b or (x.p and (x.p :: Player).Name == b) then s = x end end
		if not s or #ms.tags == 0 then return { why = "no seat or no tag" } end
		local ft = if s.f then Fight.feet(s.f) else nil
		local pick = ms.tags[#ms.tags]
		if ft then for _, t in ms.tags do if (t.p - ft).Magnitude < (pick.p - ft).Magnitude then pick = t end end end
		grabTag(m, ms, s, pick)
		return { score = ms.score, tags = #ms.tags }
	elseif op == "tags" then -- (player) where the tags are
		local out = {}
		for _, t in ms.tags do table.insert(out, { team = t.team, p = t.p, left = t.dies - now() }) end
		return out
	end
	return nil
end

return Modes
