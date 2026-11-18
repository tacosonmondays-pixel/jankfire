--!strict
-- THE HIDDEN NPCS' TRIGGERS (18 Nov 2026, the owner: "Can jankfire npc's be hidden unless you do a very specific
-- thing"). SPOILERS: what each NPC wants is written here and in roblox/docs/LORE.md, never anywhere a client can read.
-- Every lore NPC is gone for you (LoreLife.client: no body, no bubble, no prompt, no sound) until you do their own
-- thing at their spot. Then they're there for you for good (LoreNPCs' save, `seen`), and walking up to them finds them
-- as before. Each rule is judged here from what the server already knows; a client saying so is never enough:
--   emote    the Emote attribute FlairServer sets when it starts one of your emotes, while your body is in the NPC's
--            Zone (and faces the Zone's Face), held for secs
--   still    your body in the Zone, facing its Face, not drifting more than DRIFT studs, for secs
--   title    the title you wear (CardTitle: Stats sets it from your save), in the Zone, or anywhere on the back lot for
--            a rule with lot = true (TheLot's OnLot), for secs
--   shoot    shots Combat accepted (Fight.onShotFx runs after Rules.fire: ammo, rate, a clear line from your real head)
--            whose path from your eye to an end point crosses the Target box: n of them within `within` s
--   grapple  a hook on a point (the Grapple remote) that Main.server took: its rope (Rope_<id>) really ends there, on
--            the Target box: n of them within `within` s
-- Zones and targets are parts in each NPC's model, built with the clues by PolishBackup.LoreSpots: "Zone" (hidden, no
-- collisions or queries; attribute Face = a flat unit Vector3 to look along) and "Target" (hidden, queryable, so shots
-- and hooks land on it). A rule with lot = true needs neither (the Tall Guy From HR: no spot of his own).
--   T.start(api)  api.ready(p), api.revealed(p, id), api.reveal(p, id, kind)
--   T.progress(p) what's counting for p now ({ [id]: seconds or hits })
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Fight = require(script.Parent:WaitForChild("Fight")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local T = {}

T.RULES = {
	gary = { kind = "emote", emote = "salute", secs = 1 }, -- at his desk, facing it: salute the regional manager
	dale = { kind = "shoot", n = 3, within = 8 }, -- hit his machine three times ("she bites"; he hits her with a wrench)
	janitor = { kind = "still", secs = 8 }, -- stand on the wet floor by the boiler and don't move
	smiles = { kind = "emote", emote = "cheer", secs = 1 }, -- up on the Hook by his balloons: mandatory fun
	todd = { kind = "shoot", n = 5, within = 15 }, -- shoot the missing-texture cube on the far tower five times
	hr = { kind = "title", title = "lore_gary", secs = 8, lot = true }, -- wear REGIONAL MANAGER on the back lot: he wants a word
	auntie = { kind = "shoot", n = 3, within = 10 }, -- the empty tin on the watch steps, three times: you're a debit
	lumps = { kind = "still", secs = 10 }, -- on his block, facing the sunset, still
	gordo = { kind = "emote", emote = "point", secs = 1 }, -- on the chalk X behind the south-east containers: point
	mina = { kind = "still", secs = 12 }, -- wait at the roll-up door, facing it
	sharon = { kind = "grapple", n = 1, within = 1 }, -- hook the red pot
	dumpling = { kind = "emote", emote = "dance", secs = 5 }, -- dance by the tyres in the gym ("do it again!")
	pallet_jack = { kind = "grapple", n = 1, within = 1 }, -- hook his pallet stack ("go on. it's not heavy.")
	eotm = { kind = "title", title = "lore_todd", secs = 3 }, -- wear INTERN on top of the finish tower
	overtime = { kind = "still", secs = 60 }, -- face the clock in his corner for exactly a minute
} :: { [string]: any }

local STEP = 0.25 -- s between checks of the held rules
local DRIFT = 1.2 -- studs a "still" body may wander
local FACE_DOT = 0.8 -- how square to the Face you have to be (about 37 degrees either way)
local SHOOT_RANGE = 160 -- studs from your eye to the target
local PAD = 0.4 -- studs round a Target box that still count (a spinning cube, a bullet grazing)

type Api = { ready: (Player) -> boolean, revealed: (Player, string) -> boolean, reveal: (Player, string, string) -> () }
local api: Api? = nil

-- ------------------------------------------------------------------ the models
local cache: { [string]: Model } = {}
local cacheT = -1e9
local function models(): { [string]: Model }
	local now = os.clock()
	if now - cacheT < 2 then return cache end
	cacheT = now
	local out = {}
	local map = workspace:FindFirstChild("Map")
	local f = map and map:FindFirstChild("Lore")
	if f then
		for _, m in f:GetChildren() do
			local id = m:GetAttribute("LoreId")
			if m:IsA("Model") and type(id) == "string" and T.RULES[id] then out[id] = m end
		end
	end
	cache = out
	return out
end
local function part(m: Model, name: string): BasePart?
	local p = m:FindFirstChild(name)
	return if p and p:IsA("BasePart") then p else nil
end
local function rootOf(p: Player): BasePart?
	local ch = p.Character
	local r = ch and ch:FindFirstChild("HumanoidRootPart")
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	if not r or not r:IsA("BasePart") or not hum or hum.Health <= 0 then return nil end
	return r
end

-- ------------------------------------------------------------------ geometry
local function inBox(box: BasePart, pos: Vector3): boolean
	local l = box.CFrame:PointToObjectSpace(pos)
	local h = box.Size / 2
	return math.abs(l.X) <= h.X and math.abs(l.Y) <= h.Y and math.abs(l.Z) <= h.Z
end
local function distToBox(box: BasePart, pos: Vector3): number
	local l = box.CFrame:PointToObjectSpace(pos)
	local h = box.Size / 2
	return Vector3.new(math.max(math.abs(l.X) - h.X, 0), math.max(math.abs(l.Y) - h.Y, 0), math.max(math.abs(l.Z) - h.Z, 0)).Magnitude
end
-- does the segment a -> b pass through the box (grown by pad)? (the slab test, in the box's own frame)
local function crosses(box: BasePart, a: Vector3, b: Vector3, pad: number): boolean
	local la, lb = box.CFrame:PointToObjectSpace(a), box.CFrame:PointToObjectSpace(b)
	local h = box.Size / 2 + Vector3.one * pad
	local o = { la.X, la.Y, la.Z }
	local d = { lb.X - la.X, lb.Y - la.Y, lb.Z - la.Z }
	local e = { h.X, h.Y, h.Z }
	local t0, t1 = 0, 1
	for i = 1, 3 do
		if math.abs(d[i]) < 1e-9 then
			if o[i] < -e[i] or o[i] > e[i] then return false end
		else
			local ta, tb = (-e[i] - o[i]) / d[i], (e[i] - o[i]) / d[i]
			if ta > tb then ta, tb = tb, ta end
			t0, t1 = math.max(t0, ta), math.min(t1, tb)
			if t0 > t1 then return false end
		end
	end
	return true
end
local function facing(z: BasePart, r: BasePart): boolean
	local f = z:GetAttribute("Face")
	if typeof(f) ~= "Vector3" then return true end
	local lv = r.CFrame.LookVector
	local flat = Vector3.new(lv.X, 0, lv.Z)
	local want = Vector3.new((f :: Vector3).X, 0, (f :: Vector3).Z)
	if flat.Magnitude < 0.3 or want.Magnitude < 0.3 then return false end
	return flat.Unit:Dot(want.Unit) >= FACE_DOT
end

-- ------------------------------------------------------------------ held rules (emote, still, title)
type Held = { t: number, at: Vector3 }
local held: { [Player]: { [string]: Held } } = {}
local function holds(p: Player, r: BasePart, id: string, rule: any, m: Model?): boolean
	if rule.lot then
		return p:GetAttribute("OnLot") == true and p:GetAttribute("CardTitle") == rule.title
	end
	if not m then return false end
	local z = part(m, "Zone")
	if not z or not inBox(z, r.Position) or not facing(z, r) then return false end
	if rule.kind == "emote" then return p:GetAttribute("Emote") == rule.emote end
	if rule.kind == "title" then return p:GetAttribute("CardTitle") == rule.title end
	return rule.kind == "still"
end
local function step(dt: number)
	local a = api
	if not a then return end
	local ms = models()
	for _, p in Players:GetPlayers() do
		if not a.ready(p) then held[p] = nil; continue end
		local r = rootOf(p)
		local mine = held[p] or {}
		held[p] = mine
		for id, rule in T.RULES do
			if rule.kind == "shoot" or rule.kind == "grapple" then continue end
			if not r or a.revealed(p, id) or not holds(p, r, id, rule, ms[id]) then mine[id] = nil; continue end
			local h = mine[id]
			if not h then h = { t = 0, at = r.Position }; mine[id] = h end
			if rule.kind == "still" and (r.Position - h.at).Magnitude > DRIFT then h.t, h.at = 0, r.Position end
			h.t += dt
			if h.t >= rule.secs then
				mine[id] = nil
				a.reveal(p, id, rule.kind)
			end
		end
	end
end

-- ------------------------------------------------------------------ counted rules (shoot, grapple)
local counts: { [Player]: { [string]: { number } } } = {}
local function count(p: Player, id: string, rule: any)
	local a = api
	if not a then return end
	local now = os.clock()
	local mine = counts[p] or {}
	counts[p] = mine
	local list = mine[id] or {}
	mine[id] = list
	table.insert(list, now)
	while list[1] and now - list[1] > (rule.within or 10) do table.remove(list, 1) end
	if #list >= (rule.n or 1) then
		mine[id] = nil
		a.reveal(p, id, rule.kind)
	end
end

local function onShot(f: any, _wid: string, ends: any, kind: string?)
	local a = api
	if not a or kind ~= nil or type(ends) ~= "table" or f.kind ~= "player" then return end
	local p = f.ref
	if typeof(p) ~= "Instance" or not p:IsA("Player") or not a.ready(p) then return end
	local eye = Fight.eye(f)
	if not eye then return end
	for id, m in models() do
		local rule = T.RULES[id]
		if rule.kind ~= "shoot" or a.revealed(p, id) then continue end
		local tg = part(m, "Target")
		if not tg or (tg.Position - eye).Magnitude > SHOOT_RANGE then continue end
		for _, e in ends do
			if typeof(e) == "Vector3" and crosses(tg, eye, e, PAD) then
				count(p, id, rule)
				break
			end
		end
	end
end

local function onHook(p: Player, what: unknown, point: unknown, body: unknown)
	local a = api
	if not a or what ~= "hook" or typeof(point) ~= "Vector3" or typeof(body) == "Instance" or not a.ready(p) then return end
	local pt = point :: Vector3
	-- (only near a grapple target at all: most hooks end here)
	local near: { string } = {}
	for id, m in models() do
		local rule = T.RULES[id]
		local tg = rule.kind == "grapple" and part(m, "Target")
		if tg and distToBox(tg, pt) <= 1 + PAD and not a.revealed(p, id) then table.insert(near, id) end
	end
	if #near == 0 then return end
	-- Main.server judges the hook (range, sight, rate) and ties the rope at the point: only a rope that is really
	-- there, ending at this point, counts
	task.delay(0.15, function()
		local rope = workspace.Terrain:FindFirstChild("Rope_" .. p.UserId)
		local a1 = rope and rope:IsA("Beam") and rope.Attachment1
		if not a1 or (a1.WorldPosition - pt).Magnitude > 0.3 then return end
		for _, id in near do count(p, id, T.RULES[id]) end
	end)
end

-- ------------------------------------------------------------------ start
function T.start(given: Api)
	api = given
	Fight.onShotFx(onShot)
	local g = Remotes:WaitForChild("Grapple", 30)
	if g and g:IsA("RemoteEvent") then (g :: RemoteEvent).OnServerEvent:Connect(onHook) end
	local acc = 0
	RunService.Heartbeat:Connect(function(dt: number)
		acc += dt
		if acc < STEP then return end
		local d = acc
		acc = 0
		step(d)
	end)
	Players.PlayerRemoving:Connect(function(p) held[p] = nil; counts[p] = nil end)
end

-- what's counting for p right now (Studio tests)
function T.progress(p: Player): { [string]: number }
	local out = {}
	for id, h in held[p] or {} do out[id] = math.floor(h.t * 10) / 10 end
	for id, l in counts[p] or {} do out[id] = #l end
	return out
end

return T
