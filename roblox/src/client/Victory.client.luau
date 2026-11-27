--!strict
-- THE VICTORY SCENE's client (27 Nov 2026; shared/VictoryData.luau has the why). The server's message
-- (JankfireRemotes.Victory, server/VictoryServer.server.luau) comes at the match's end; then:
--   scene   the default scene plays (client/VictoryScene.luau), the stats card (client/VictoryCard.luau) slides in as
--           it settles, Space / B / the SKIP chip jump to it after V.SKIP_AFTER s
--   cine    a finisher's cinematic plays instead (client/Finisher.luau); when Matches' end screen comes (Round
--           "over"), the stage's held shot and the card
--   neither (a draw): the card alone over the arena
-- The card stays for the end screen's wait (Round "over": next / nextLabel), then the play of the match has the screen
-- (Replay), or the trip home ends it (Round "hub"). While it runs: LocalPlayer VictoryOn (Arsenal skips FightHud's old
-- end screen, MasteryClient its own match card), Finishing = "victory" (the death camera, PadLook, MenuCursor and the
-- replay treat it like a finisher), LoadoutOpen (the hands and the menus hold still), the other screens hidden.
-- The card's rewards are this match's: XP and coins (the Xp / Brass attributes against their value when the match
-- began), weapon mastery (MasteryPush "match"), quests that moved (the Quests remote's state, then and now).
-- Studio: LocalPlayer attribute VictoryTest = "win" | "lose" | "win:<mates>" | "lose:<mates>" | "cine" | "card" |
--   "draw" | "skip" | "stop" plays it here without a match (your own body as every body); with workspace attribute
--   VictorySpot = an arena's name (workspace.Map.<name>, e.g. "RooftopV3") it plays at that map's own spot; workspace
--   VictoryFreeze = seconds holds the lens at that moment of the scene (photos)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ContextActionService = game:GetService("ContextActionService")

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local V = require(Shared:WaitForChild("VictoryData")) :: any
local TeamColors = require(Shared:WaitForChild("TeamColors")) :: any
local Ranks = require(Shared:WaitForChild("Ranks")) :: any
local Mastery = require(Shared:WaitForChild("Mastery")) :: any
local Roster = require(Shared:WaitForChild("Roster")) :: any
local Arena = require(Shared:WaitForChild("Arena")) :: any
local ModeConfig = require(Shared:WaitForChild("ModeConfig")) :: any
local QuestData = require(Shared:WaitForChild("QuestData")) :: any
local Scene = require(script.Parent:WaitForChild("VictoryScene")) :: any
local Card = require(script.Parent:WaitForChild("VictoryCard")) :: any
local Replay = require(script.Parent:WaitForChild("Replay")) :: any

local R = Remotes:WaitForChild("Victory", 60) :: RemoteEvent?
local RoundR = Remotes:WaitForChild("Round") :: RemoteEvent

-- ------------------------------------------------------------------ what the match began with
type Snap = { xp: number, brass: number, quests: { [string]: any }?, at: number }
local snap: Snap? = nil
local masteryMsg: any = nil
local function questState(): any
	local r = Remotes:FindFirstChild("Quests")
	if not (r and r:IsA("RemoteFunction")) then return nil end
	local ok, res = pcall(function() return (r :: RemoteFunction):InvokeServer("state") end)
	if ok and type(res) == "table" and res.ok and type(res.list) == "table" then return res end
	return nil
end
local function questsById(res: any): { [string]: any }
	local out = {}
	for _, q in res.list do if type(q.id) == "string" then out[q.id .. "#" .. tostring(q.slot)] = q end end
	return out
end
local function takeSnap()
	local s: Snap = { xp = tonumber(me:GetAttribute("Xp")) or 0, brass = tonumber(me:GetAttribute("Brass")) or 0, quests = nil, at = os.clock() }
	snap = s
	masteryMsg = nil
	task.spawn(function()
		local res = questState()
		if res and snap == s then s.quests = questsById(res) end
	end)
end
me:GetAttributeChangedSignal("Arena"):Connect(function()
	if me:GetAttribute("Arena") ~= nil and me:GetAttribute("VictoryOn") == nil then takeSnap() end
end)
if me:GetAttribute("Arena") ~= nil then takeSnap() end
local push = Remotes:WaitForChild("MasteryPush", 30) :: RemoteEvent?
if push then
	push.OnClientEvent:Connect(function(msg: any)
		if type(msg) == "table" and msg.k == "match" and type(msg.gains) == "table" then masteryMsg = msg end
	end)
end

-- ------------------------------------------------------------------ the card's numbers
local COLS = { K = "KILLS", D = "DEATHS", A = "ASSISTS", DMG = "DAMAGE" }
local function ordinal(n: number): string
	local s = if n % 100 >= 11 and n % 100 <= 13 then "TH" elseif n % 10 == 1 then "ST" elseif n % 10 == 2 then "ND" elseif n % 10 == 3 then "RD" else "TH"
	return tostring(n) .. s
end
local function rewardsNow(): any
	local out: any = {}
	local s = snap
	local xpNow = tonumber(me:GetAttribute("Xp")) or 0
	if s then
		local lv = Ranks.levelOf(xpNow)
		local function frac(x: number, l: number): number
			local a, b = Ranks.xpForLevel(l), Ranks.xpForLevel(l + 1)
			return math.clamp((x - a) / math.max(1, b - a), 0, 1)
		end
		local before = if Ranks.levelOf(s.xp) < lv then 1.01 else frac(s.xp, lv) -- (> to: a level gained, the bar starts over)
		out.level = { lv = lv, from = if before > 1 then 1 else before, to = frac(xpNow, lv), gain = math.max(0, xpNow - s.xp),
			into = math.max(0, xpNow - Ranks.xpForLevel(lv)), need = Ranks.xpForLevel(lv + 1) - Ranks.xpForLevel(lv) }
		if before > 1 then out.level.from = 1; out.level.to = frac(xpNow, lv) end
		out.coins = (tonumber(me:GetAttribute("Brass")) or 0) - s.brass
	else
		out.level = { lv = Ranks.levelOf(xpNow), from = 0, to = 0, gain = 0 }
	end
	local mm = masteryMsg
	if mm then
		local list = {}
		for w, g in mm.gains do
			local gain = tonumber(g) or 0
			if gain > 0 and type(w) == "string" then
				local now = tonumber((mm.xp or {})[w]) or gain
				local lv, _, _, to = Mastery.progress(now)
				local bl, _, _, bf = Mastery.progress(math.max(0, now - gain))
				local e = Roster.byId[w]
				table.insert(list, { name = if e then e.name else w, lv = lv, from = if bl < lv then 1 else bf, to = to, gain = gain })
			end
		end
		table.sort(list, function(a, b) return a.gain > b.gain end)
		out.mastery = list
	end
	return out
end
local function questsMoved(res: any): { any }
	local out = {}
	local s = snap
	if not res or not s or not s.quests then return out end
	for key, q in questsById(res) do
		local was = s.quests[key]
		local n0 = if was then tonumber(was.n) or 0 else 0
		local n1 = tonumber(q.n) or 0
		if was and (n1 > n0 or (q.done and not was.done)) then
			local row = QuestData.byId and QuestData.byId[q.id]
			table.insert(out, { text = tostring(q.text or (row and row.text) or q.id), n = n1, goal = tonumber(q.goal) or 1, done = q.done == true,
				from = math.clamp(n0 / math.max(1, tonumber(q.goal) or 1), 0, 1) })
		end
	end
	table.sort(out, function(a, b) return (a.done and 1 or 0) > (b.done and 1 or 0) end)
	return out
end

-- the card's table from the server's message
local function cardOf(msg: any): any
	local d: any = {}
	local board = if type(msg.board) == "table" then msg.board else nil
	d.result = if msg.winner == nil then (if msg.classic then "NO WINNER" else "DRAW") elseif msg.youWon then "VICTORY" else "DEFEAT"
	local modeName = string.lower(tostring(msg.mode or "")) -- ("2v2", as players write it)
	local def = msg.classic and ModeConfig.byId and ModeConfig.byId[msg.mode]
	if def and type(def.name) == "string" then modeName = string.upper(def.name) end
	local parts = { modeName }
	local okT, title = pcall(Arena.title, if msg.arena ~= "" then msg.arena else nil)
	if okT and type(title) == "string" and title ~= "" then table.insert(parts, string.upper(title)) end
	if msg.ranked then table.insert(parts, "RANKED") end
	d.sub = table.concat(parts, "   ")
	-- the columns and my numbers (the Tab board's own counts)
	local cols = if board and type(board.cols) == "table" then board.cols else { "K", "D", "A", "DMG" }
	d.cols, d.boardCols, d.mine = {}, cols, {}
	for i, c in cols do d.cols[i] = COLS[c] or tostring(c) end
	local allRows = {}
	d.board = {}
	if board then
		for _, side in board.teams or {} do
			local rows = {}
			for _, r in side.rows or {} do
				if r.empty then continue end
				local mine = r.uid == me.UserId
				if mine then for i, v in r.v or {} do d.mine[i] = tonumber(v) or 0 end end
				table.insert(rows, { name = r.name, v = r.v, mine = mine })
				table.insert(allRows, { v1 = tonumber((r.v or {})[1]) or 0, mine = mine })
			end
			local t = tonumber(side.t) or 1
			table.insert(d.board, { color = TeamColors.color(((t - 1) % 4) + 1), rows = rows, t = t,
				name = if type(side.name) == "string" then side.name else TeamColors.name(((t - 1) % 4) + 1) })
		end
	end
	-- the score: one tile per side, yours first (a free-for-all: your place instead)
	d.tiles = {}
	if msg.ffa or (board and board.ffa) then
		table.sort(allRows, function(a, b) return a.v1 > b.v1 end)
		for i, r in allRows do if r.mine then d.place = ordinal(i) .. " OF " .. #allRows end end
		local one = { color = TeamColors.color(1), rows = {}, t = 0, name = "" }
		for _, side in d.board do for _, r in side.rows do table.insert(one.rows, r) end end
		table.sort(one.rows, function(a, b) return (tonumber((a.v or {})[1]) or 0) > (tonumber((b.v or {})[1]) or 0) end)
		d.board = { one }
	else
		local mineT = tonumber(msg.team)
		for _, side in d.board do
			local n = tonumber((msg.wins or {})[side.t])
			if msg.classic then
				n = 0
				for _, r in side.rows do n += tonumber((r.v or {})[1]) or 0 end
			end
			local tile = { n = n or 0, color = side.color, mine = side.t == mineT, won = msg.winner ~= nil and side.t == msg.winner, name = side.name }
			side.score = n or 0
			if tile.mine then table.insert(d.tiles, 1, tile) else table.insert(d.tiles, tile) end
		end
		-- (your side first on the board too)
		table.sort(d.board, function(a, b) return (a.t == mineT and 1 or 0) > (b.t == mineT and 1 or 0) end)
	end
	local rw = rewardsNow()
	d.level, d.mastery, d.coins = rw.level, rw.mastery, rw.coins
	d.wallet = tonumber(me:GetAttribute("Brass"))
	d.quests = {}
	return d
end

-- ------------------------------------------------------------------ the run
local hidden: { [ScreenGui]: boolean } = {}
local KEEP = { JankVictoryCard = true, JankPlayFade = true, JankFinisher = true }
local function hideScreens()
	for _, g in pg:GetChildren() do
		if g:IsA("ScreenGui") and not KEEP[g.Name] and g.Enabled then hidden[g] = true; g.Enabled = false end
	end
end
local function showScreens()
	for g in hidden do if g.Parent then g.Enabled = true end end
	table.clear(hidden)
end
local function controls(on: boolean)
	pcall(function()
		local c = require(me:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: any):GetControls()
		if on then c:Enable() else c:Disable() end
	end)
end

type Run = { msg: any, card: any?, t0: number, loadoutWas: any, skipOk: boolean, cardShown: boolean, over: boolean, tok: number,
	test: boolean }
local run: Run? = nil
local tok = 0

local function report(r: Run)
	if r.test or not R then return end
	pcall(function() (R :: RemoteEvent):FireServer({ t = "done" }) end)
end
local function unbindSkip()
	pcall(function() ContextActionService:UnbindAction("JankVictorySkip") end)
	Card.skip(false)
end

local function showCard(r: Run)
	if r.cardShown then return end
	r.cardShown = true
	local d = cardOf(r.msg)
	r.card = d
	Card.show(d)
	-- the rewards settle a moment after the match ends (Stats, Quests, MasteryXp write in their own end hooks)
	local my = r.tok
	task.spawn(function()
		for _ = 1, 4 do
			task.wait(0.9)
			if not run or run.tok ~= my then return end
			local rw = rewardsNow()
			local res = questState()
			rw.quests = questsMoved(res)
			Card.rewards(rw)
		end
	end)
end

local function finish(why: string)
	local r = run
	if not r then return end
	run = nil
	tok += 1
	unbindSkip()
	Scene.stop(why)
	Card.hide()
	showScreens()
	controls(true)
	me:SetAttribute("LoadoutOpen", r.loadoutWas == true)
	if me:GetAttribute("Finishing") == "victory" then me:SetAttribute("Finishing", nil) end
	me:SetAttribute("VictoryOn", nil)
end

local function skip()
	local r = run
	if not r or not r.skipOk then return end
	r.skipOk = false
	unbindSkip()
	Scene.hold()
	showCard(r)
	report(r)
end
local function bindSkip(r: Run)
	local my = r.tok
	task.delay(V.SKIP_AFTER, function()
		if not run or run.tok ~= my or r.cardShown then return end
		r.skipOk = true
		Card.skip(true)
		ContextActionService:BindActionAtPriority("JankVictorySkip", function(_, state)
			if state == Enum.UserInputState.Begin then skip() end
			return Enum.ContextActionResult.Sink
		end, false, 3600, Enum.KeyCode.Space, Enum.KeyCode.ButtonB)
	end)
end
Card.onSkip = skip

local function begin(msg: any, test: boolean?)
	finish("new")
	tok += 1
	local r: Run = { msg = msg, card = nil, t0 = os.clock(), loadoutWas = me:GetAttribute("LoadoutOpen"), skipOk = false, cardShown = false,
		over = false, tok = tok, test = test == true }
	run = r
	me:SetAttribute("VictoryOn", true)
	-- (the last kill's victim is often still in its killcam: the match is over, the scene has the screen. Finishing
	-- set below keeps new killcams out: ReplayClient)
	if msg.scene and Replay.mode and Replay.mode() == "killcam" then pcall(Replay.stop) end
	if msg.scene then
		me:SetAttribute("Finishing", "victory")
		me:SetAttribute("LoadoutOpen", true)
		controls(false)
		hideScreens()
		if not Scene.start(msg) then
			-- (no stage: straight to the card)
			showCard(r)
			report(r)
			return
		end
		bindSkip(r)
		-- the card slides in as the lens settles
		local my = r.tok
		task.delay(math.max(0, (tonumber(msg.len) or V.LEN) - 0.8), function()
			if not run or run.tok ~= my then return end
			showCard(r)
			unbindSkip()
		end)
		task.delay(tonumber(msg.len) or V.LEN, function()
			if run and run.tok == my then report(r) end
		end)
	end
	-- (cine or a draw: nothing until the end screen comes - Round "over")
end

-- the end screen's moment: the card (and the held shot after a cinematic), its wait bar
local function onOver(next: number, label: string?)
	local r = run
	if not r then return end
	r.over = true
	if not r.cardShown then
		if r.msg.cine and #(r.msg.stage or {}) > 0 then
			-- (after the cinematic: the winners on the stage, held, no intro and no sting)
			me:SetAttribute("Finishing", "victory")
			me:SetAttribute("LoadoutOpen", true)
			controls(false)
			hideScreens()
			Scene.start(r.msg, { hold = true, quiet = true })
		elseif not r.msg.scene then
			me:SetAttribute("LoadoutOpen", true)
			hideScreens()
		end
		showCard(r)
	end
	unbindSkip()
	Card.wait(next, label)
	-- the play of the match comes after the wait: let go of the screen just before it
	local my = r.tok
	if label and string.find(string.lower(label), "play of the match", 1, true) then
		task.delay(math.max(0, next - 0.15), function()
			if run and run.tok == my then finish("potm") end
		end)
	end
end

if R then
	R.OnClientEvent:Connect(function(msg: any)
		if type(msg) ~= "table" or msg.t ~= "scene" or not V.ON then return end
		begin(msg)
	end)
end
RoundR.OnClientEvent:Connect(function(r: any)
	if type(r) ~= "table" then return end
	if r.over then
		onOver(if type(r.next) == "number" then r.next else 7, if type(r.nextLabel) == "string" then r.nextLabel else nil)
	elseif r.hub or r.start then
		finish(if r.hub then "home" else "round")
	end
end)
-- (the play of the match took the screen some other way: let go)
RunService.Heartbeat:Connect(function()
	if run and Replay.mode and Replay.mode() == "potm" then finish("replay") end
end)

-- ------------------------------------------------------------------ Studio: a scene without a match
if RunService:IsStudio() then
	-- (a map's spot, read here as the server reads it: server/VictoryServer's spotIn)
	local function spotOf(name: any): any?
		local map = workspace:FindFirstChild("Map")
		local site = map and type(name) == "string" and map:FindFirstChild(name)
		local v = site and site:FindFirstChild("Victory", true)
		if not (v and v:IsA("Model")) then return nil end
		local function lens(n: string): any?
			local p = v:FindFirstChild(n)
			if not (p and p:IsA("BasePart")) then return nil end
			return { at = p.Position, look = p.Position + p.CFrame.LookVector * 30, fov = tonumber(p:GetAttribute("Fov")) or 40 }
		end
		local function floor(n: string): CFrame?
			local p = v:FindFirstChild(n)
			if not (p and p:IsA("BasePart")) then return nil end
			return p.CFrame * CFrame.new(0, -p.Size.Y / 2, 0)
		end
		local s: any = { hero = floor("Hero"), mates = {}, rise = { lens("RiseA"), lens("RiseB") }, wide = { lens("WideA"), lens("WideB") },
			hold = lens("Hold"), lose = { lens("LoseA"), lens("LoseB") }, lights = v:FindFirstChild("Lights") }
		if not s.hero or not (s.rise[1] and s.rise[2] and s.wide[1] and s.wide[2]) then return nil end
		for i = 1, 3 do local c = floor("Mate" .. i); if c then table.insert(s.mates, c) end end
		if not (s.lose[1] and s.lose[2]) then s.lose = nil end
		return s
	end
	local function fake(win: boolean, mates: number, how: string): any
		local stage = { { uid = me.UserId, name = me.DisplayName, front = true, emote = V.emoteOf(me:GetAttribute("Emotes")) } }
		for i = 1, mates do table.insert(stage, { uid = me.UserId, name = "" }) end
		-- (sample rows for the preview, a 5-3 match: each side's kills are the other side's deaths, and a side that took
		-- n rounds killed at least n x its size)
		local SAMPLE = {
			[0] = { win = { { 5, 3, 0, 917 } }, lose = { { 3, 5, 0, 704 } } },
			[1] = { win = { { 6, 2, 1, 1183 }, { 5, 4, 3, 946 } }, lose = { { 4, 6, 0, 823 }, { 2, 5, 2, 612 } } },
			[2] = { win = { { 7, 3, 2, 1437 }, { 6, 3, 5, 1176 }, { 3, 4, 7, 893 } }, lose = { { 5, 6, 1, 1052 }, { 3, 5, 4, 806 }, { 2, 5, 2, 641 } } },
			[3] = { win = { { 8, 3, 2, 1618 }, { 6, 4, 7, 1259 }, { 5, 4, 3, 1031 }, { 3, 3, 9, 764 } },
				lose = { { 5, 6, 1, 1193 }, { 4, 6, 6, 958 }, { 3, 5, 2, 726 }, { 2, 5, 3, 587 } } },
		}
		local NAMES = { "kopi_kat", "slapdash09", "Wickerfield", "ducktape_dan", "mossbyte", "frostlane", "pelican_pete" }
		local sm0 = SAMPLE[math.clamp(mates, 0, 3)]
		local sm = { us = if win then sm0.win else sm0.lose, them = if win then sm0.lose else sm0.win }
		local us, them = {}, {}
		for i, v in sm.us do table.insert(us, { name = if i == 1 then me.DisplayName else NAMES[i - 1], uid = if i == 1 then me.UserId else -i, v = v }) end
		for i, v in sm.them do table.insert(them, { name = NAMES[3 + i], uid = -10 - i, v = v }) end
		return {
			t = "scene", id = 0, scene = how == "scene", cine = how == "cine", len = V.LEN, winner = if how == "draw" then nil elseif win then 1 else 2,
			youWon = win and how ~= "draw", team = 1, mode = ("%dv%d"):format(mates + 1, mates + 1), classic = false, ranked = false,
			arena = "RooftopV3", wins = { if win then 5 else 3, if win then 3 else 5 },
			board = { mode = "", cols = { "K", "D", "A", "DMG" }, teams = { { t = 1, rows = us }, { t = 2, rows = them } } },
			stage = stage, front = me.UserId, spot = spotOf(workspace:GetAttribute("VictorySpot")),
		}
	end
	me:GetAttributeChangedSignal("VictoryTest"):Connect(function()
		local v = me:GetAttribute("VictoryTest")
		if type(v) ~= "string" or v == "" then return end
		me:SetAttribute("VictoryTest", nil)
		local kind, n = string.match(v, "^(%a+):?(%d*)$")
		-- (the preview's rewards: a sample of what a real match gives - 340 XP, 60 coins, a weapon's mastery)
		local lost = string.sub(v, 1, 4) == "lose"
		snap = { xp = (tonumber(me:GetAttribute("Xp")) or 0) - (if lost then 140 else 340), brass = (tonumber(me:GetAttribute("Brass")) or 0) - (if lost then 20 else 60), quests = nil, at = os.clock() }
		local w1 = (Mastery.weapons and Mastery.weapons() or {})[1]
		if w1 then masteryMsg = { gains = { [w1] = if lost then 100 else 250 }, xp = { [w1] = 2250 } } end
		local mates = tonumber(n) or 0
		if kind == "stop" then finish("test"); return end
		if kind == "skip" then if run then run.skipOk = true end; skip(); return end
		if kind == "win" or kind == "lose" then
			begin(fake(kind == "win", mates, "scene"), true)
			task.delay(V.LEN + 0.3, function() if run and run.test then onOver(7, "back to the hub in %d") end end)
		elseif kind == "cine" or kind == "card" or kind == "draw" then
			begin(fake(true, mates, if kind == "cine" then "cine" elseif kind == "draw" then "draw" else "card"), true)
			onOver(7, "back to the hub in %d")
		end
	end)
end
