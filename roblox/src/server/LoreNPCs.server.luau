--!strict
-- THE HIDDEN NPCS, the server half (18 Nov 2026; the book: Shared.LoreData, the rigs: Shared.LoreRigs, the spots:
-- ServerStorage.PolishBackup.LoreSpots). The owner: "Perhaps the hidden NPCs including guy from hr can be rehidden
-- around hub areas? As well as the cast from [the JANKFIRE] story?"
-- workspace.Map.Lore holds one Model per NPC (attribute LoreId; a hidden "Root" part on the floor under them). They
-- stand still here: their idle, head turns and speech bubbles are drawn on each player's own screen (LoreLife.client).
-- FINDING ONE: your body within reach of their Root (the web's own reach, LoreData.REACH / UP / DOWN) counts, once per
-- player, saved in this script's own store (JankfireLore_v1, Profiles: Studio saves go to its _studio twin). The first
-- time, their gift (the web's: a container, or a cosmetic, or a container if you own that already) through Loot.grant
-- with one receipt per player and NPC, a small line on the HUD ("NEW GRAPPLE · PLUNGER", Hud's small kind), and the
-- remote tells your screen to have them say their gift line.
-- The player's attributes: LoreFound (how many), LoreList (their ids, comma separated), LoreTotal (how many there are):
-- the profile card shows "n / N" (ProfileUI); nothing else nags.
-- HIDDEN UNTIL ITS CODE (18 Nov 2026, the owner: "Can jankfire npc's be hidden unless you do a very specific thing",
-- then "there should be a control panel somewhere that you type in jank actually make codes and every code spawns in
-- an NPC, ill give the codes weekly by weekly at some point"): every NPC, and the hub egg's mannequin ("egg"), is gone
-- for you (LoreLife.client hides it) until you type its code at the code panel (workspace.Map.Lore.CodePanel, built by
-- PolishBackup.LoreSpots). The code is checked here against LoreCodeBook (salted hashes and opening days only; the
-- plain codes live in the owner's vault), wrong tries are rate-limited (CODE_TRIES, then CODE_WAIT seconds, saved), and
-- each redemption is logged (the save's `codes`, and the server log). A right code reveals it for you for good (saved:
-- `seen`; the player attribute LoreSeen lists them), spawns it in beside the panel on your screen alone, and counts as
-- finding it (its gift and title as before; the egg's OG title goes through HubEgg.server's ServerStorage.HubEggFind).
-- Then it lives at its own spot for you. (Only a code counts: `seen` keeps nothing the save's `codes` log doesn't back, onlyCoded. The first idea, a secret action per NPC at its
-- spot, is written and parked: LoreTriggers.luau, behind TRIGGERS_ON.)
-- REWARD CODES (18 Nov 2026, the owner: the old Ducky skin trio "via code"): a book row with kind = "reward" gives the
-- things in REWARDS (through Loot.grant, one receipt per player and item: once each) instead of revealing an NPC; the
-- save's `claims` remembers it, and a second try says it's claimed. Same checks (its day, near the panel, no match,
-- the wrong-try wait).
-- Remote JankfireRemotes.LoreCode (RemoteFunction, made here): ("try", text) -> { ok = true, id, again? } |
-- { ok = true, reward = id, items = { names }, again? } |
-- { ok = false, why = "wrong" | "wait" | "far" | "busy" | "loading", wait = seconds, left = tries }
-- NOT IN THE WORLD UNTIL ITS CODE (18 Nov 2026, the owner: "can you remove the jankfire npcs? when you type in the codes
-- you'll get a cutscene where an npc walks in and then they'll appear somewhere!"): every NPC's model (and the hub egg's
-- mannequin, "Lore_egg") lives in ServerStorage.JankfireLore, never in the map (migrate() moves any a builder left in
-- Map.Lore or Map.Hub.HubEgg). Each player is given a copy of only the ones THEY have revealed, in their own
-- PlayerGui.LoreDelivery (a hidden ScreenGui: a PlayerGui reaches only its player), and their LoreLife.client puts it
-- in their world at its spot. A right code delivers it first, then tells their screen to play the cutscene.
-- Remote JankfireRemotes.Lore (server -> client): ("found", id, firstTime), ("seen", id, how) the moment you reveal one
-- (how = "code": the cutscene; "again": a used code, the cutscene with their "again" line), ("hrtake", at) from
-- HrGuy.server.
-- ServerStorage.LoreFindEvent (BindableEvent): (player, id) counts a find that isn't a walk-up (the HR guy's).
-- ServerStorage.LoreRevealEvent (BindableEvent, fired here): (player, id) when someone reveals one (HrGuy.server: "hr"
-- means he comes for them).
-- Studio play tests: ServerStorage.LoreTest (BindableFunction, Studio only):
--   "state"           every NPC: where, the first player's distance, found or not; the save's state
--   "find", id        the first player finds them now, wherever they stand
--   "forget", id?     takes one (or every) find off the first player's save (Studio's _studio store only)
--   "near", id        moves the first player to stand in front of them (a TeleportT stamp first)
--   "zone", id        moves the first player into the NPC's trigger Zone, facing its Face (a TeleportT stamp first)
--   "hide", id?       un-reveals one (or every) NPC for the first player and takes its find off too (_studio only)
--   "reveal", id      reveals one for the first player now (photos; the real way is its trigger)
--   "wear", title     sets the first player's CardTitle attribute (what Stats publishes from the save), for title rules
--   "progress"        what the triggers are counting for the first player (TRIGGERS_ON only)
--   "code", text      the first player types this at the panel (the real check, nearness skipped)
--   "clock", days     the server's calendar runs this many days ahead for the codes' opening days (0 = today)
--   "codes"           each code's NPC, opening day and whether it's open by that calendar
--   "unlock"          clears the first player's wrong tries and wait
--   "redeliver"       takes the first player's NPC copies back and gives them again (what joining does)
--   "migrate"         what loading a save does to `seen` (only code-backed reveals stay), now
--   "unclaim", id     forgets the first player's claim of a reward code (the items stay in the loot save)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local LoreData = require(Shared:WaitForChild("LoreData")) :: any
local Profiles = require(script.Parent:WaitForChild("Profiles")) :: any
local Loot = require(script.Parent:WaitForChild("Loot")) :: any
local Book = require(script.Parent:WaitForChild("LoreCodeBook")) :: any
local Sha256 = require(script.Parent:WaitForChild("Sha256")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local CalloutR = Remotes:WaitForChild("Callout") :: RemoteEvent
local LoreR = Remotes:WaitForChild("Lore") :: RemoteEvent

local STUDIO = RunService:IsStudio()
local TICK = 0.4 -- s between reach checks
local GIFT_WORDS = { grapple = "GRAPPLE", kill = "KILL EFFECT", effect = "EFFECT", hat = "HAT", emote = "EMOTE" }
local CONTAINER_WORDS = { crate = "+1 CRATE", bag = "+1 DUFFEL BAG", spray = "+1 SPRAY CAN" }
local TRIGGERS_ON = false -- (the parked first idea: a secret action per NPC, LoreTriggers.luau. codes are the way now)
local CODE_TRIES, CODE_WAIT, CODE_GAP = 5, 60, 0.5 -- wrong tries before a wait, the wait (s), the least gap between tries
local PANEL_REACH = 24 -- studs from the panel a try may come from
-- revealed by a code but not one of LoreData's NPCs: the hub egg's mannequin (HubEgg.server's; not in the LORE count)
local EXTRA = { egg = true } :: { [string]: boolean }
-- what each reward code gives (shop-gui's gift offers: "gift:<kind>:<id>", any item, never on sale; a grant gives only
-- what's missing and is true then too; false = not written yet, try again). names: LootTable's, with the weapon
local REWARDS = {
	ducky_classic = { "gift:skin:lmg_ducky", "gift:skin:revolver_ducky", "gift:skin:katana_ducky" },
} :: { [string]: { string } }
local okLT, LootTable = pcall(function() return require(Shared:WaitForChild("LootTable")) :: any end)
local WEAPON_WORD = { lmg = "LMG", revolver = "REVOLVER", katana = "KATANA" } :: { [string]: string }
local function itemName(offer: string): string
	local kind, id = string.match(offer, "^gift:(%w+):([%w_]+)$")
	local name = id or offer
	if okLT and LootTable and LootTable.info and kind and id then
		local ok, info = pcall(LootTable.info, kind, id)
		if ok and type(info) == "table" and type(info.name) == "string" then name = info.name end
	end
	local w = id and WEAPON_WORD[string.match(id, "^([%w]+)_") or ""]
	return string.upper(name) .. (if w then " " .. w else "")
end
local function known(id: any): boolean return type(id) == "string" and (LoreData.counts(id) or EXTRA[id] == true) end

local store = Profiles.new("JankfireLore_v1", function()
	return { v = 1, found = {}, seen = {}, codes = {}, codeWait = 0, claims = {} }
end)

type State = { prof: any?, ready: boolean, busy: { [string]: boolean }, wrong: number, lastTry: number, trying: boolean }
local st: { [Player]: State } = {}

-- every NPC's model, out of the world (LoreSpots.build puts them here)
local function npcStore(): Folder
	local f = ServerStorage:FindFirstChild("JankfireLore")
	if not f then
		f = Instance.new("Folder")
		f.Name = "JankfireLore"
		f.Parent = ServerStorage
	end
	return f :: Folder
end
-- anything a builder left in the world goes into storage (the place's old Map.Lore NPCs; the egg's mannequin)
local function migrate()
	local map = workspace:FindFirstChild("Map")
	local ml = map and map:FindFirstChild("Lore")
	local sf = npcStore()
	if ml then
		for _, m in ml:GetChildren() do
			if m:IsA("Model") and type(m:GetAttribute("LoreId")) == "string" then
				local old = sf:FindFirstChild(m.Name)
				if old then old:Destroy() end
				m.Parent = sf
			end
		end
	end
	local hub = map and map:FindFirstChild("Hub")
	local egg = hub and hub:FindFirstChild("HubEgg")
	local mq = egg and egg:FindFirstChild("Mannequin")
	if mq and mq:IsA("Model") then
		local old = sf:FindFirstChild("Lore_egg")
		if old then old:Destroy() end
		mq.Name = "Lore_egg"
		mq:SetAttribute("LoreId", "egg")
		mq.Parent = sf
	end
end
migrate()
task.spawn(function() while true do task.wait(10); pcall(migrate) end end)
local function lore(): Instance?
	local map = workspace:FindFirstChild("Map")
	return map and map:FindFirstChild("Lore")
end
-- each NPC's find point: its Root part (the floor under them), by id
local function points(): { [string]: BasePart }
	local out = {}
	local f = npcStore()
	if not f then return out end
	for _, m in f:GetChildren() do
		local id = m:GetAttribute("LoreId")
		local r = m:FindFirstChild("Root")
		if type(id) == "string" and r and r:IsA("BasePart") and LoreData.counts(id) then out[id] = r end
	end
	return out
end
local function rootOf(p: Player): BasePart?
	local ch = p.Character
	local r = ch and ch:FindFirstChild("HumanoidRootPart")
	return if r and r:IsA("BasePart") then r else nil
end
-- the web's canReach: a cylinder round them, a bit up and down from your feet (the root is ~3 over the feet)
local function inReach(r: BasePart, at: BasePart): boolean
	local feet = r.Position - Vector3.new(0, 3, 0)
	local d = at.Position - feet
	local flat = Vector3.new(d.X, 0, d.Z).Magnitude
	local reach = (at:GetAttribute("Reach") :: number?) or LoreData.REACH
	local up = (at:GetAttribute("Up") :: number?) or LoreData.UP -- (a cat up on a fridge: findable from the floor)
	return flat < reach and d.Y < up and d.Y > -LoreData.DOWN
end

local function publish(p: Player)
	local s = st[p]
	local n, list, seen = 0, {}, {}
	if s and s.prof then
		for _, id in LoreData.ORDER do
			if s.prof.data.found[id] then n += 1; table.insert(list, id) end
			if s.prof.data.seen[id] then table.insert(seen, id) end
		end
		for id in EXTRA do if s.prof.data.seen[id] then table.insert(seen, id) end end
	end
	p:SetAttribute("LoreTotal", LoreData.total())
	p:SetAttribute("LoreFound", n)
	p:SetAttribute("LoreList", table.concat(list, ","))
	-- (the NPCs your screen may draw: LoreLife hides the rest. a client can't add to this: it's the server's attribute)
	p:SetAttribute("LoreSeen", table.concat(seen, ","))
end

-- the gift (and later, the flair session's title for each find: LoreData entries' title ids go through the same door)
local function give(p: Player, e: any): string?
	local g = e.gift
	if not g then return nil end
	local receipt = "lore-" .. e.id .. "-" .. p.UserId .. (if STUDIO then "-" .. os.time() else "")
	if g.container then
		if Loot.grant(p, g.container, receipt) then return CONTAINER_WORDS[g.container] end
		return nil
	end
	if g.kind and g.id then
		if Loot.owns(p, g.kind, g.id) then
			local c = g.orElse or "bag"
			if Loot.grant(p, c, receipt) then return CONTAINER_WORDS[c] end
			return nil
		end
		-- the shop's server-only gift pass first ("gift:<kind>:<id>", shop-gui, 18 Nov: any item, grapples included,
		-- never on sale), then the item's own single offer (kill effects and emotes have one)
		local words = GIFT_WORDS[g.kind] or string.upper(g.kind)
		if Loot.grant(p, "gift:" .. g.kind .. ":" .. g.id, receipt) or Loot.grant(p, g.kind .. ":" .. g.id, receipt) then
			return "NEW " .. words .. " · " .. string.upper(g.id)
		end
		-- (the cosmetic has no offer right now, e.g. not on sale yet: its container instead, so nobody goes without)
		local c = g.orElse or "bag"
		if Loot.grant(p, c, receipt .. "-c") then return CONTAINER_WORDS[c] end
	end
	return nil
end

-- the secret title for a find (CardStyles "lore_<id>", rarity secret: Loot.grant of "egg:title:<id>", one receipt each),
-- and OVERDUE once every one of them is found
local TITLES = { gary = "REGIONAL MANAGER", dale = "OUT OF ORDER", janitor = "HAS SEEN THINGS", smiles = "MANDATORY FUN",
	todd = "INTERN", hr = "HAD A QUICK CHAT" }
local function titleFor(p: Player, tid: string): string?
	local receipt = "lore-title-" .. tid .. "-" .. p.UserId .. (if STUDIO then "-" .. os.time() else "")
	if Loot.owns(p, "title", tid) then return nil end
	return if Loot.grant(p, "egg:title:" .. tid, receipt) then tid else nil
end
local function allFound(s: State): boolean
	for _, id in LoreData.ORDER do if not s.prof.data.found[id] then return false end end
	return true
end
local function allCats(s: State): boolean
	if not LoreData.CATS_ON then return false end -- (parked: BOARD MEMBER is never granted)
	for _, id in LoreData.CATS do if not s.prof.data.found[id] then return false end end
	return true
end

local function find(p: Player, id: string)
	local s = st[p]
	local e = LoreData.get(id)
	if not s or not s.ready or not s.prof or not e or s.busy[id] or not LoreData.counts(id) then return end
	local d = s.prof.data
	if d.found[id] then return end
	s.busy[id] = true
	d.found[id] = os.time()
	s.prof.dirty = true
	publish(p)
	LoreR:FireClient(p, "found", id, true)
	task.spawn(function()
		local note = give(p, e)
		if note then CalloutR:FireClient(p, note, 2.6) end
		if TITLES[id] and titleFor(p, "lore_" .. id) then
			task.wait(if note then 2.8 else 0)
			CalloutR:FireClient(p, "NEW TITLE · " .. TITLES[id], 2.6)
		end
		if LoreData.get(id).kind == "cat" and allCats(s) and titleFor(p, "lore_cats") then
			task.wait(2.8)
			CalloutR:FireClient(p, "NEW TITLE · BOARD MEMBER", 2.6)
		end
		if allFound(s) and titleFor(p, "lore_all") then
			task.wait(2.8)
			CalloutR:FireClient(p, "NEW TITLE · OVERDUE", 2.6)
		end
		s.busy[id] = nil
	end)
end

-- their copies: only what they've revealed, in their own PlayerGui (only they receive it)
local function box(p: Player): ScreenGui?
	local pg = p:FindFirstChildOfClass("PlayerGui")
	if not pg then return nil end
	local g = pg:FindFirstChild("LoreDelivery")
	if not g then
		local ng = Instance.new("ScreenGui")
		ng.Name = "LoreDelivery"; ng.ResetOnSpawn = false; ng.Enabled = false
		ng.Parent = pg
		g = ng
	end
	return g :: ScreenGui
end
local function deliver(p: Player, id: string)
	local g = box(p)
	local src = npcStore():FindFirstChild("Lore_" .. id)
	if not g or not src or g:FindFirstChild(src.Name) then return end
	src:Clone().Parent = g
end
local function undeliver(p: Player, id: string?)
	local g = box(p)
	if not g then return end
	for _, c in g:GetChildren() do
		if not id or c.Name == "Lore_" .. id then c:Destroy() end
	end
end

-- a code (or a trigger) done: revealed for this player, saved, their copy delivered, their screen told
local revealEv = ServerStorage:FindFirstChild("LoreRevealEvent") or Instance.new("BindableEvent")
revealEv.Name = "LoreRevealEvent"
revealEv.Parent = ServerStorage
local function reveal(p: Player, id: string, how: string?)
	local s = st[p]
	if not s or not s.ready or not s.prof or not known(id) then return end
	local d = s.prof.data
	if d.seen[id] then return end
	d.seen[id] = os.time()
	s.prof.dirty = true
	publish(p)
	deliver(p, id)
	LoreR:FireClient(p, "seen", id, how)
	;(revealEv :: BindableEvent):Fire(p, id)
end

-- (18 Nov 2026, main relaying the owner: NPCs were showing for players who never typed their code) a reveal counts only
-- if that player really entered its code: `seen` keeps nothing the save's `codes` log doesn't back. Reveals carried
-- over from the find-by-walking days, a test's reveal, anything else: dropped on load (finds, titles and gifts stay)
local function onlyCoded(d: any)
	for k in d.seen do
		if not known(k) or d.codes[k] == nil then d.seen[k] = nil end
	end
end

-- ------------------------------------------------------------------ players
local function added(p: Player)
	if st[p] then return end
	local s: State = { prof = nil, ready = false, busy = {}, wrong = 0, lastTry = -1e9, trying = false }
	st[p] = s
	publish(p)
	local prof = Profiles.load(store, "u" .. p.UserId, function() return p.Parent ~= nil and st[p] == s end)
	if not prof then return end
	if st[p] ~= s then Profiles.release(store, prof); return end
	if type(prof.data.found) ~= "table" then prof.data.found = {} end
	for k in prof.data.found do if not LoreData.get(k) then prof.data.found[k] = nil end end -- (one taken out of the game)
	if type(prof.data.codes) ~= "table" then prof.data.codes = {} end
	if type(prof.data.codeWait) ~= "number" then prof.data.codeWait = 0 end
	if type(prof.data.claims) ~= "table" then prof.data.claims = {} end
	if type(prof.data.seen) ~= "table" then prof.data.seen = {} end
	onlyCoded(prof.data)
	s.prof = prof
	s.ready = true
	publish(p)
	for id in prof.data.seen do deliver(p, id) end -- (what they've revealed is in their world, nothing else)
	-- (someone who found everything before OVERDUE existed, or whose grant didn't save: theirs now, quietly)
	task.delay(8, function()
		if st[p] ~= s or not s.ready then return end
		if allCats(s) then titleFor(p, "lore_cats") end
		if allFound(s) then titleFor(p, "lore_all") end
	end)
end
for _, p in Players:GetPlayers() do task.spawn(added, p) end
Players.PlayerAdded:Connect(added)
Players.PlayerRemoving:Connect(function(p)
	local s = st[p]
	st[p] = nil
	if s and s.prof then Profiles.release(store, s.prof) end
end)

-- finds that aren't a walk-up (the Tall Guy From HR finds you: HrGuy.server fires this when he has someone)
local findEv = ServerStorage:FindFirstChild("LoreFindEvent") or Instance.new("BindableEvent")
findEv.Name = "LoreFindEvent"
findEv.Parent = ServerStorage;
(findEv :: BindableEvent).Event:Connect(function(p: Player, id: string)
	if typeof(p) == "Instance" and p:IsA("Player") and type(id) == "string" then find(p, id) end
end)

-- ------------------------------------------------------------------ the reach check
task.spawn(function()
	while true do
		task.wait(TICK)
		local pts = points()
		if next(pts) == nil then continue end
		for p, s in st do
			if not s.ready then continue end
			local r = rootOf(p)
			if not r then continue end
			for id, at in pts do
				if not s.prof.data.found[id] and s.prof.data.seen[id] and inReach(r, at) then find(p, id) end
			end
		end
	end
end)

-- ------------------------------------------------------------------ the codes
-- the panel (LoreSpots builds it into Map.Lore; its place is data there: L.PANEL)
local function panel(): Model?
	local f = lore()
	local m = f and f:FindFirstChild("CodePanel")
	return if m and m:IsA("Model") then m else nil
end
-- each code's opening moment (UTC midnight of its day)
local opensAt: { [string]: number } = {}
for _, c in Book.CODES do
	local y, mo, d = string.match(c.opens, "^(%d+)-(%d+)-(%d+)$")
	opensAt[c.id] = if y then DateTime.fromUniversalTime(tonumber(y) :: number, tonumber(mo) :: number, tonumber(d) :: number).UnixTimestamp else math.huge
end
local clockShift = 0 -- (Studio: LoreTest "clock")
local function today(): number return os.time() + clockShift end
local function plain(text: string): string return (string.gsub(string.lower(text), "[^%w]", "")) end
local function hashOf(code: string): string
	local h = Sha256.hex(Book.SALT .. ":" .. code)
	for _ = 2, Book.ITER do h = Sha256.hex(h .. Book.SALT) end
	return h
end
-- the egg's find is HubEgg.server's (the OG title; PetSecrets gives the mini mannequin to whoever owns it)
local function findEgg(p: Player)
	local f = ServerStorage:FindFirstChild("HubEggFind")
	if f and f:IsA("BindableFunction") then
		local ok, res = pcall(function() return (f :: BindableFunction):Invoke(p) end)
		if not ok then warn("[jankfire] lore code: the egg's find: " .. tostring(res)) end
	end
end

local function tryCode(p: Player, text: unknown, test: boolean?): any
	local s = st[p]
	if not s or not s.ready or not s.prof then return { ok = false, why = "loading" } end
	if s.trying then return { ok = false, why = "busy" } end
	local z = p:GetAttribute("Zone")
	if z == "match" or z == "staging" then return { ok = false, why = "far" } end
	if not test then
		local m = panel()
		local r = rootOf(p)
		if not m or not r or (r.Position - m:GetPivot().Position).Magnitude > PANEL_REACH then return { ok = false, why = "far" } end
	end
	local d = s.prof.data
	local now = os.time()
	if d.codeWait > now then return { ok = false, why = "wait", wait = d.codeWait - now } end
	if os.clock() - s.lastTry < CODE_GAP then return { ok = false, why = "busy" } end
	s.lastTry = os.clock()
	if type(text) ~= "string" or #text > 48 then return { ok = false, why = "wrong", left = CODE_TRIES - s.wrong } end
	local code = plain(text)
	if code == "" then return { ok = false, why = "wrong", left = CODE_TRIES - s.wrong } end -- (an empty box costs nothing)
	s.trying = true
	local h = if #code <= 32 then hashOf(code) else ""
	local id: string? = nil
	local reward = false
	for _, c in Book.CODES do
		if c.hash == h and today() >= (opensAt[c.id] or math.huge) then
			if c.kind == "reward" and REWARDS[c.id] then id = c.id; reward = true; break end
			if c.kind == nil and known(c.id) then id = c.id; break end
		end
	end
	s.trying = false
	if not id then
		s.wrong += 1
		if s.wrong >= CODE_TRIES then
			s.wrong = 0
			d.codeWait = now + CODE_WAIT
			s.prof.dirty = true
			return { ok = false, why = "wait", wait = CODE_WAIT }
		end
		return { ok = false, why = "wrong", left = CODE_TRIES - s.wrong }
	end
	s.wrong = 0
	if reward then
		local rid = id :: string
		local names = {}
		for _, offer in REWARDS[rid] do table.insert(names, itemName(offer)) end
		if d.claims[rid] then return { ok = true, reward = rid, items = names, again = true } end
		local all = true
		for _, offer in REWARDS[rid] do
			local receipt = ("lorecode-%s-%s-%d"):format(rid, offer, p.UserId) .. (if STUDIO then "-" .. os.time() else "")
			local ok, res = pcall(Loot.grant, p, offer, receipt)
			if not ok or res ~= true then all = false end
		end
		if not all then return { ok = false, why = "later" } end -- (a save wasn't written: nothing marked, try again)
		d.claims[rid] = os.time()
		d.codes[rid] = d.codes[rid] or os.time()
		s.prof.dirty = true
		print(("[jankfire] lore code: %s (%d) -> reward %s"):format(p.Name, p.UserId, rid))
		return { ok = true, reward = rid, items = names }
	end
	local again = d.seen[id] ~= nil
	d.codes[id] = d.codes[id] or now
	s.prof.dirty = true
	print(("[jankfire] lore code: %s (%d) -> %s%s"):format(p.Name, p.UserId, id, if again then " (again)" else ""))
	if again then
		deliver(p, id)
		LoreR:FireClient(p, "seen", id, "again") -- (its cutscene again, with its "again" line; nothing new is given)
	else
		reveal(p, id, "code")
	end
	-- it counts as finding it (titles and gifts as before)
	if id == "egg" then task.spawn(findEgg, p) elseif not d.found[id] then find(p, id) end
	return { ok = true, id = id, again = again or nil }
end

local codeR = Remotes:FindFirstChild("LoreCode")
if not codeR then
	codeR = Instance.new("RemoteFunction")
	codeR.Name = "LoreCode"
	codeR.Parent = Remotes
end
;(codeR :: RemoteFunction).OnServerInvoke = function(p: Player, op: unknown, text: unknown): any
	if op ~= "try" then return { ok = false, why = "wrong" } end
	return tryCode(p, text, false)
end

-- the HR guy has no spot of his own to stand at: his look for the panel's spawn-in, where clients can reach it
task.spawn(function()
	local hr = ServerStorage:WaitForChild("LoreHR", 30)
	if hr and not ReplicatedStorage:FindFirstChild("LoreHRShow") then
		local c = hr:Clone()
		c.Name = "LoreHRShow"
		c.Parent = ReplicatedStorage
	end
end)

-- ------------------------------------------------------------------ the triggers (parked: LoreTriggers, the spoilers)
local Triggers: any = if TRIGGERS_ON then require(script.Parent:WaitForChild("LoreTriggers")) else nil
if Triggers then Triggers.start({
	ready = function(p: Player): boolean
		local s = st[p]
		return s ~= nil and s.ready and s.prof ~= nil
	end,
	revealed = function(p: Player, id: string): boolean
		local s = st[p]
		return s ~= nil and s.prof ~= nil and s.prof.data.seen[id] ~= nil
	end,
	reveal = reveal,
}) end

-- ------------------------------------------------------------------ Studio test hook
if STUDIO then
	local hook = ServerStorage:FindFirstChild("LoreTest") or Instance.new("BindableFunction")
	hook.Name = "LoreTest"
	hook.Parent = ServerStorage;
	(hook :: BindableFunction).OnInvoke = function(op: string, a: any): any
		local p = Players:GetPlayers()[1]
		local s = p and st[p]
		if op == "state" then
			local out = { ready = s and s.ready or false, save = s and s.prof and s.prof.state or "none", npcs = {} :: any }
			local r = p and rootOf(p)
			for id, at in points() do
				out.npcs[id] = { at = tostring(at.Position), dist = if r then math.floor((r.Position - at.Position).Magnitude * 10) / 10 else -1,
					found = s and s.prof and s.prof.data.found[id] ~= nil or false, seen = s and s.prof and s.prof.data.seen[id] ~= nil or false,
				reach = r ~= nil and inReach(r, at) }
			end
			out.attrs = p and { p:GetAttribute("LoreFound"), p:GetAttribute("LoreTotal"), p:GetAttribute("LoreList"), p:GetAttribute("LoreSeen") } or nil
			return out
		elseif op == "find" and p then
			find(p, tostring(a))
			return p:GetAttribute("LoreList")
		elseif op == "forget" and s and s.prof then
			if a then s.prof.data.found[tostring(a)] = nil else s.prof.data.found = {} end
			s.prof.dirty = true
			publish(p)
			return p:GetAttribute("LoreList")
		elseif op == "near" and p then
			local at = points()[tostring(a)]
			local r = rootOf(p)
			if not at or not r then return "no" end
			local m = at.Parent :: Model
			local visit = at:GetAttribute("Visit")
			local off = if typeof(visit) == "Vector3" then visit else m:GetPivot().LookVector * 7
			p:SetAttribute("TeleportT", os.clock())
			local spot = at.Position + off + Vector3.new(0, 3.2, 0)
			r.CFrame = CFrame.lookAt(spot, Vector3.new(at.Position.X, spot.Y, at.Position.Z))
			return tostring(spot)
		elseif op == "zone" and p then
			local at = points()[tostring(a)]
			local z = at and (at.Parent :: Model):FindFirstChild("Zone")
			local r = rootOf(p)
			if not z or not z:IsA("BasePart") or not r then return "no zone" end
			local f = z:GetAttribute("Face")
			local look = if typeof(f) == "Vector3" then f else z.CFrame.LookVector
			local spot = z.Position + Vector3.new(0, 3 - z.Size.Y / 2 + 0.2, 0)
			p:SetAttribute("TeleportT", os.clock())
			r.CFrame = CFrame.lookAt(spot, spot + Vector3.new(look.X, 0, look.Z))
			return tostring(spot) .. " facing " .. tostring(look)
		elseif op == "hide" and s and s.prof then
			if a then s.prof.data.seen[tostring(a)] = nil; s.prof.data.found[tostring(a)] = nil
			else s.prof.data.seen = {}; s.prof.data.found = {} end
			undeliver(p, if a then tostring(a) else nil)
			s.prof.dirty = true
			publish(p)
			return p:GetAttribute("LoreSeen")
		elseif op == "reveal" and p then
			reveal(p, tostring(a), "test")
			return p:GetAttribute("LoreSeen")
		elseif op == "wear" and p then
			p:SetAttribute("CardTitle", tostring(a))
			return p:GetAttribute("CardTitle")
		elseif op == "progress" and p then
			return if Triggers then Triggers.progress(p) else "triggers parked"
		elseif op == "code" and p then
			return tryCode(p, a, true)
		elseif op == "clock" then
			clockShift = math.floor((tonumber(a) or 0) * 86400)
			return ("calendar: %s UTC"):format(DateTime.fromUnixTimestamp(today()):FormatUniversalTime("YYYY-MM-DD HH:mm", "en-us"))
		elseif op == "codes" then
			local out = {}
			for _, c in Book.CODES do table.insert(out, ("%s %s %s"):format(c.id, c.opens, if today() >= (opensAt[c.id] or math.huge) then "OPEN" else "shut")) end
			return table.concat(out, " | ")
		elseif op == "migrate" and p and s and s.prof then -- (what loading the save does to `seen`, now)
			onlyCoded(s.prof.data)
			s.prof.dirty = true
			publish(p)
			undeliver(p, nil)
			for id in s.prof.data.seen do deliver(p, id) end
			return p:GetAttribute("LoreSeen")
		elseif op == "redeliver" and p and s and s.prof then -- (what a rejoin does: their copies taken back, then given again)
			undeliver(p, nil)
			task.wait(0.5)
			for id in s.prof.data.seen do deliver(p, id) end
			return p:GetAttribute("LoreSeen")
		elseif op == "unclaim" and s and s.prof then
			s.prof.data.claims[tostring(a)] = nil
			s.prof.dirty = true
			return "unclaimed " .. tostring(a)
		elseif op == "unlock" and s and s.prof then
			s.wrong = 0
			s.prof.data.codeWait = 0
			s.prof.dirty = true
			return "unlocked"
		end
		return "ops: state, find id, forget id?, near id, zone id, hide id?, reveal id, wear title, progress, code text, clock days, codes, unlock"
	end
end
