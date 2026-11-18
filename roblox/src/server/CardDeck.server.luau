--!strict
-- weapons batch E: the Card Deck (WEAPONS.md "Card Deck"; traced spec weapons-batchE-spec.md, web room.js playCard).
-- the server owns the deck (52 + 2 jokers, shuffled), your hand of 5, which card you play and everything it does; the
-- client sends only which slot ("play", i, eye, aim), a redraw ("redraw") or asks for the hand ("hand").
--   ace (any suit): a teleport along your aim, 16 m or short of the first wall (only ever up, never down; the server
--     checks the landing is clear)
--   spades: a fan of 6 cards (0.16 rad); J Q K: 24 over 0.9 rad. a card: 11 + 0.6 x rank
--   hearts: heal 3 x rank (to 100); J Q K: 150 HP, the extra fading 2 a second
--   clubs: a blast in front of you (9 m, 53 deg): 12 + 2 x rank and a shove; J Q K: all round (12 m): 30 and a big shove
--   diamonds: a dash along your aim, 3.5 x rank m/s; J Q K: 55
--   joker: a random suit's J Q K
--   every card but spades and aces also flicks 2 cards straight ahead
-- R redraws a new 5 (every 2.5 s); an empty hand is dealt again 1.5 s after its last card; a new hand each life, the
-- deck lasts the whole time you're here
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Fight = require(script.Parent:WaitForChild("Fight"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local FxR = Remotes:WaitForChild("Fx") :: RemoteEvent
local CardsR = Remotes:FindFirstChild("Cards") :: RemoteEvent?
if not CardsR then
	local r = Instance.new("RemoteEvent")
	r.Name = "Cards"
	r.Parent = Remotes
	CardsR = r
end
local Volley = ServerStorage:WaitForChild("JankCardVolley") :: BindableEvent -- (WeaponProj.server flies the cards)

local S = Weapons.S
local now = os.clock
type Fighter = Rules.Fighter

type Deck = { deck: { string }, hand: { string }, redrawT: number, dealAt: number? }
local decks: { [Player]: Deck } = {}

local SUITS = { "h", "s", "c", "d" }
local function newDeck(): { string }
	local d = {}
	for _, s in SUITS do for r = 1, 13 do table.insert(d, s .. r) end end
	table.insert(d, "j0"); table.insert(d, "j0")
	for i = #d, 2, -1 do local j = math.random(i); d[i], d[j] = d[j], d[i] end
	return d
end
local function stateOf(p: Player): Deck
	local st = decks[p]
	if not st then st = { deck = newDeck(), hand = {}, redrawT = -math.huge }; decks[p] = st end
	return st
end
local function send(p: Player)
	local st = stateOf(p)
	local r = CardsR :: RemoteEvent
	r:FireClient(p, "hand", st.hand, #st.deck)
end
-- a new 5 (fewer than 5 left in the deck: a fresh deck, the rest thrown away)
local function deal(p: Player)
	local st = stateOf(p)
	if #st.deck < 5 then st.deck = newDeck() end
	st.hand = {}
	for _ = 1, 5 do table.insert(st.hand, table.remove(st.deck) :: string) end
	st.dealAt = nil
	send(p)
end

Fight.onSpawn(function(f: Fighter)
	if f.kind == "player" then deal(f.ref :: Player) end
end)

-- ------------------------------------------------------------------ the effects
local function card(id: string): (string, number) return string.sub(id, 1, 1), tonumber(string.sub(id, 2)) or 0 end
local function centre(t: Fighter): Vector3? local ft = Fight.feet(t); return ft and ft + Vector3.new(0, 0.9 * S, 0) end
local function rotY(d: Vector3, a: number): Vector3 return (CFrame.fromAxisAngle(Vector3.yAxis, a) * d) end
-- a volley: n cards spread over `spread` rad round the aim (the pitch kept), each `dmg`
local function fan(p: Player, eye: Vector3, d: Vector3, n: number, spread: number, dmg: number, suit: string)
	local dirs = {}
	for k = 0, n - 1 do
		local a = if n > 1 then (k / (n - 1) - 0.5) * spread else 0
		table.insert(dirs, rotY(d, a))
	end
	Volley:Fire(p, eye, dirs, dmg, suit)
end
local mapParams = RaycastParams.new()
mapParams.FilterType = Enum.RaycastFilterType.Include
local function mapRay(o: Vector3, d: Vector3): RaycastResult?
	local map = workspace:FindFirstChild("Map")
	if not map then return nil end
	mapParams.FilterDescendantsInstances = { map }
	return workspace:Raycast(o, d, mapParams)
end
-- a body-sized box at a spot: any map part in it?
local function clearAt(feet: Vector3): boolean
	local map = workspace:FindFirstChild("Map")
	if not map then return true end
	local op = OverlapParams.new()
	op.FilterType = Enum.RaycastFilterType.Include
	op.FilterDescendantsInstances = { map }
	local box = CFrame.new(feet + Vector3.new(0, 1.05 * S, 0))
	for _, part in workspace:GetPartBoundsInBox(box, Vector3.new(0.6 * S, 1.6 * S, 0.6 * S), op) do
		if part:IsA("BasePart") and part.CanCollide then return false end
	end
	return true
end
local function teleport(p: Player, f: Fighter, eye: Vector3, d: Vector3)
	local feet, root = Fight.feet(f), Fight.root(f)
	local m = Fight.model(f)
	if not feet or not root or not m then return end
	local hit = mapRay(eye, d * 16 * S)
	local dist = if hit then math.max(0, hit.Distance - 1 * S) else 16 * S
	local to = feet + Vector3.new(d.X * dist, math.max(0, d.Y * dist), d.Z * dist)
	-- (the web had no landing check: aimed at a ledge you could land inside it. here it comes back toward you till clear)
	local tries = 0
	while not clearAt(to) and tries < 8 do
		tries += 1
		to = feet:Lerp(to, 0.75)
	end
	if not clearAt(to) then return end
	local from = root.Position
	p:SetAttribute("TeleportT", now()) -- (a server move: the anti-cheat starts afresh from here)
	p:SetAttribute("ACGrace", now() + 1)
	m:PivotTo(root.CFrame + (to - feet))
	FxR:FireAllClients({ k = "cardtp", model = m, a = from, b = root.Position })
end
local function heal(p: Player, f: Fighter, amt: number, cap: number)
	local before = f.hp
	f.hp = math.max(f.hp, math.min(cap, f.hp + amt))
	Fight.syncHp(f)
	if f.hp > before then FxR:FireAllClients({ k = "cardheal", model = Fight.model(f), big = cap > (f.maxHp or Weapons.HP) or nil }) end
end
local function blast(f: Fighter, ult: boolean, rank: number)
	local me = Fight.feet(f)
	local mc = centre(f)
	local root = Fight.root(f)
	if not me or not mc or not root then return end
	local look = Vector3.new(root.CFrame.LookVector.X, 0, root.CFrame.LookVector.Z).Unit
	local R = (if ult then 12 else 9) * S
	FxR:FireAllClients({ k = "cardblast", p = me, r = R, ult = ult or nil, look = look })
	for _, t in Fight.all do
		if t == f or not t.alive or not Fight.allow(f, t) then continue end
		if t.onlyFor ~= nil and t.onlyFor ~= f.ref then continue end
		local tf, tc = Fight.feet(t), centre(t)
		if not tf or not tc then continue end
		local to = tf - me
		local dist = to.Magnitude
		if dist > R or dist < 1e-3 then continue end
		local dir = to.Unit
		if not ult and Vector3.new(dir.X, 0, dir.Z).Unit:Dot(look) < 0.6 then continue end
		-- (not through walls: the web's blast was)
		local sight = tc - mc
		if sight.Magnitude > 1e-3 and Fight.castMap(mc, sight.Unit, sight.Magnitude) then continue end
		local dmg = if ult then 30 else 12 + 2 * rank
		local k = (if ult then 55 else 10 + 4 * rank) * S
		Fight.hurt(t, dmg, f, "cards", false, dir * k + Vector3.new(0, (if ult then 14 else 6) * S, 0), tc)
	end
end

local function play(p: Player, i: unknown, eye: unknown, aim: unknown)
	if p:GetAttribute("Zone") == "hub" then return end
	local f = Fight.byPlayer[p]
	if not f or not f.alive or f.held ~= "cards" or not table.find(Rules.loadoutOf(f), "cards") then return end
	if typeof(eye) ~= "Vector3" or typeof(aim) ~= "Vector3" or type(i) ~= "number" then return end
	local n = now()
	if n < f.staggerUntil then return end
	local seye = Fight.eye(f)
	if not seye then return end
	local o = if ((eye :: Vector3) - seye).Magnitude > 4 * S then seye else eye :: Vector3
	local d = aim :: Vector3
	if d.Magnitude < 0.5 or d.Magnitude > 1.5 then return end
	d = d.Unit
	local st = stateOf(p)
	local idx = math.clamp(math.floor(i :: number), 1, 5)
	local id = st.hand[idx]
	if not id then return end
	local w = Weapons.list.cards :: any
	if not Rules.gate(f, "cards", n, w.cd / 0.9 * 0.75) then return end
	table.remove(st.hand, idx)
	local suit, rank = card(id)
	local joker = suit == "j"
	if joker then suit, rank = SUITS[math.random(4)], 13 end
	local ult = rank >= 11
	local dmg = w.dmg + w.perRank * math.clamp(rank, 2, 13)
	Fight.shot(f, "cards")
	FxR:FireAllClients({ k = "cardplay", model = Fight.model(f), by = p.UserId, card = id, suit = suit, rank = rank, ult = ult or nil, joker = joker or nil })
	if rank == 1 then teleport(p, f, o, d)
	elseif suit == "s" then fan(p, o, d, if ult then w.ultN else w.fanN, if ult then w.ultSpread else w.fanSpread, dmg, suit)
	elseif suit == "h" then heal(p, f, if ult then 150 else 3 * rank, if ult then 150 else (f.maxHp or Weapons.HP))
	elseif suit == "c" then blast(f, ult, rank)
	elseif suit == "d" then
		local k = (if ult then 55 else 3.5 * rank) * S
		Fight.knock(f, d * k + Vector3.new(0, (if ult then 6 else 2) * S, 0), "cards")
		p:SetAttribute("ACGrace", n + 1.2)
		FxR:FireAllClients({ k = "carddash", model = Fight.model(f), look = d, ult = ult or nil })
	end
	-- every card but spades and aces still throws 2 straight ahead
	if suit ~= "s" and rank ~= 1 then fan(p, o, d, w.flick, 0.05, dmg, suit) end
	if #st.hand == 0 then st.dealAt = n + 1.5 end
	send(p)
end

;(CardsR :: RemoteEvent).OnServerEvent:Connect(function(p: Player, op: unknown, a: unknown, b: unknown, c: unknown)
	if op == "play" then play(p, a, b, c)
	elseif op == "redraw" then
		local f = Fight.byPlayer[p]
		local st = stateOf(p)
		if not f or not f.alive or now() - st.redrawT < 2.5 then return end
		st.redrawT = now()
		deal(p)
	elseif op == "hand" then
		local st = stateOf(p)
		if #st.hand == 0 and not st.dealAt then deal(p) else send(p) end
	end
end)

-- an empty hand dealt again; overheal above your max fading 2 HP a second
local acc = 0
RunService.Heartbeat:Connect(function(dt: number)
	local n = now()
	for p, st in decks do
		if st.dealAt and n >= st.dealAt then deal(p) end
	end
	acc += dt
	if acc < 0.25 then return end
	local step = acc
	acc = 0
	for _, f in Fight.all do
		local cap = f.maxHp or Weapons.HP
		if f.alive and f.hp > cap then
			f.hp = math.max(cap, f.hp - 2 * step)
			Fight.syncHp(f)
		end
	end
end)
Players.PlayerRemoving:Connect(function(p) decks[p] = nil end)
