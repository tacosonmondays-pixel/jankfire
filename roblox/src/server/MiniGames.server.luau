--!strict
-- THE HUB'S MINI-GAMES, the server (shared/MiniGames.luau says what they are). this script builds each game on its spot,
-- seats and stands players, keeps them in the hub, and hands everything else to the game's module (MiniArm, MiniBoard,
-- MiniArcade in this folder). one RemoteEvent, JankfireRemotes.MiniGame:
--   client -> server  ("leave")  |  (kind, data)  data = { op = ..., ... } for the game you're in
--   server -> client  (kind, data)  your own things: a skill check, a refused move, your arcade rank
-- what everyone sees (the meter, the board, the cabinet's screen) is in the game model's attributes
-- a player in a game has the attributes MiniGame (the kind), MiniGameId (the table) and MiniSide ("A" / "B" / "P");
-- the client (MiniGames.client) opens the game's screen from those
-- the anti-cheat: a seated body is "seat"-supported (AntiCheat support()); every server move of a body here stamps
-- TeleportT first; the furniture never moves
-- test hook (Studio): ServerStorage.JankMiniTest (BindableFunction): ("state") JSON of every table; ("sit", player,
-- tableId, side); ("leave", player); ("op", player, data) as if the client sent it; ("spots") where they stand
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local CollectionService = game:GetService("CollectionService")
local HttpService = game:GetService("HttpService")
local ServerStorage = game:GetService("ServerStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local MG = require(Shared:WaitForChild("MiniGames")) :: any
local Zones = require(script.Parent:WaitForChild("Zones")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local remote = Remotes:FindFirstChild("MiniGame") :: RemoteEvent?
if not remote then
	local r = Instance.new("RemoteEvent")
	r.Name = "MiniGame"
	r.Parent = Remotes
	remote = r
end
local Remote = remote :: RemoteEvent

local GAMES = {
	arm = require(script.Parent:WaitForChild("MiniArm")) :: any,
	board = require(script.Parent:WaitForChild("MiniBoard")) :: any,
	arcade = require(script.Parent:WaitForChild("MiniArcade")) :: any,
	box = require(script.Parent:WaitForChild("MiniBox")) :: any,
	golf = require(script.Parent:WaitForChild("MiniGolf")) :: any,
}

export type Table = { id: string, kind: string, model: Model, cf: CFrame, seats: { [string]: Seat }, who: { [string]: any }, prompts: { [string]: ProximityPrompt }, bots: { [string]: Model }, g: any }
local tables: { [string]: Table } = {}
local inGame: { [Player]: { t: Table, side: string } } = {}

-- ------------------------------------------------------------------ helpers the game modules use
local ctx = {}
ctx.MG = MG
ctx.tables = tables
function ctx.send(p: any, kind: string, data: any)
	if typeof(p) == "Instance" and p:IsA("Player") and p.Parent then Remote:FireClient(p, kind, data) end
end
function ctx.now(): number return workspace:GetServerTimeNow() end
function ctx.isBot(who: any): boolean return type(who) == "table" and who.bot == true end
function ctx.nameOf(who: any): string
	if typeof(who) == "Instance" and who:IsA("Player") then return who.DisplayName end
	if ctx.isBot(who) then return "BOT · " .. (MG.LEVEL_NAME[who.level] or "") end
	if type(who) == "table" and who.standIn then return who.DisplayName end -- (a Studio test's second player)
	return ""
end
function ctx.idOf(who: any): number
	if typeof(who) == "Instance" and who:IsA("Player") then return who.UserId end
	if ctx.isBot(who) then return -1 end
	if type(who) == "table" and who.standIn then return who.UserId end
	return 0
end

-- ------------------------------------------------------------------ building
local kit: Instance? = nil
local function kitModel(name: string): Model?
	kit = kit or (ReplicatedStorage:FindFirstChild("JankfireMiniGames") and (ReplicatedStorage :: any).JankfireMiniGames:FindFirstChild("Kit"))
	local m = kit and kit:FindFirstChild(name)
	return if m and m:IsA("Model") then m:Clone() else nil
end
local function place(parent: Instance, name: string, cf: CFrame, newName: string?): Model?
	local m = kitModel(name)
	if not m then warn("[MiniGames] the kit has no " .. name); return nil end
	m:PivotTo(cf)
	m.Name = newName or name
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then d.Anchored = true; d.CanTouch = false end
	end
	m.Parent = parent
	return m
end
local function part(parent: Instance, name: string, cf: CFrame, size: Vector3, props: { [string]: any }?): BasePart
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
	p.Transparency = 1; p.Size = size; p.CFrame = cf
	p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	if props then for k, v in props do (p :: any)[k] = v end end
	p.Parent = parent
	return p
end
local function att(parent: Instance, name: string, cf: CFrame): Attachment
	local a = Instance.new("Attachment")
	a.Name = name
	a.CFrame = cf
	a.Parent = parent
	return a
end
local function prompt(parent: Instance, object: string, action: string, dist: number): ProximityPrompt
	local pr = Instance.new("ProximityPrompt")
	pr.ObjectText = object; pr.ActionText = action
	pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX; pr.HoldDuration = 0
	pr.MaxActivationDistance = dist; pr.RequiresLineOfSight = false; pr.ClickablePrompt = true
	pr.Exclusivity = Enum.ProximityPromptExclusivity.OnePerButton
	pr.Parent = parent
	return pr
end
local FACE = { A = CFrame.identity, B = CFrame.Angles(0, math.pi, 0) } -- (A faces -Z, B faces +Z)

local folder: Folder
-- (parent: the hub's own MiniGames folder, else the first hub's; suffix: "_<hub>" for a hub's markers that name it)
local function newTable(kind: string, cf: CFrame, n: number, parent: Instance?, suffix: string?): Table?
	local id = kind .. n .. (suffix or "")
	local model = Instance.new("Model")
	model.Name = "Mini_" .. id
	model:SetAttribute("Kind", kind)
	model:SetAttribute("Id", id)
	local root = part(model, "Root", cf, Vector3.new(1, 1, 1))
	model.PrimaryPart = root
	local T: Table = { id = id, kind = kind, model = model, cf = cf, seats = {}, who = {}, prompts = {}, bots = {}, g = {} }
	local L = MG.L[kind]
	local seatY = MG.SEAT_TOP - 0.1 - MG.SEAT_SINK
	if kind == "arm" then
		place(model, "mg_armtable", cf, "Table")
		for _, side in { "A", "B" } do
			place(model, "mg_stool", cf * CFrame.new(L.seat[side]), "Stool" .. side)
		end
		-- the clasp and the free hands' pegs (the IKControls aim at these; each client moves the clasp: MiniArm.client)
		att(root, "Clasp", CFrame.new(L.pivot + Vector3.new(0, L.reach, 0)))
		for _, side in { "A", "B" } do
			att(root, "Hand" .. side, CFrame.new(L.pivot + Vector3.new(0, L.reach, 0)))
			att(root, "Peg" .. side, CFrame.new(L.peg[side]))
			-- the elbow's pole: below and out to the sitter's right of the elbow pad, so the arm bends the right way
			local e = L.elbow[side]
			att(root, "Pole" .. side, CFrame.new(e + Vector3.new(if side == "A" then 1.5 else -1.5, -1.4, if side == "A" then 1.2 else -1.2)))
			att(root, "PolePeg" .. side, CFrame.new(L.peg[side] + Vector3.new(if side == "A" then -1.6 else 1.6, -1.2, if side == "A" then 1.0 else -1.0)))
			att(root, "Pin" .. side, CFrame.new(L.pin[side]))
		end
	elseif kind == "board" then
		place(model, "mg_boardtable", cf, "Table")
		place(model, "mg_chair", cf * CFrame.new(L.seat.A) * FACE.B, "ChairA") -- (the chair's mesh faces +Z: A's turns)
		place(model, "mg_chair", cf * CFrame.new(L.seat.B), "ChairB")
		att(root, "BoardCentre", CFrame.new(0, L.surface, 0))
	elseif kind == "arcade" then
		place(model, "mg_cabinet", cf * FACE.B, "Cabinet") -- (its front, +Z in the mesh, turned to -Z: the spot's look)
		local s = L.screen
		-- (its front face looks at you, tipped up by the tilt; the client's SurfaceGui draws on Front)
		part(model, "Screen", cf * CFrame.new(s.at) * CFrame.Angles(math.rad(s.tilt), 0, 0),
			Vector3.new(s.size.X, s.size.Y, 0.03), { Transparency = 0, Color = Color3.fromRGB(24, 27, 33), Material = Enum.Material.SmoothPlastic })
		local mq = L.marquee
		part(model, "Marquee", cf * CFrame.new(mq.at), Vector3.new(mq.size.X, mq.size.Y, 0.05))
		local box = part(model, "Box", cf * CFrame.new(0, 3.8, 0), Vector3.new(3.4, 7.6, 2.8), { CanCollide = true, CanQuery = true })
		box.Name = "Collision"
		CollectionService:AddTag(model, "MiniArcade")
		-- the two seats on the lid (HubSeats gives each a Sit prompt; you face out over the screen)
		for k, at in L.topSeats or {} do
			local s = part(model, "TopSeat" .. k, cf * CFrame.new(at), Vector3.new(1.2, 0.2, 1.2))
			CollectionService:AddTag(s, "HubSeat")
		end
	elseif kind == "box" then
		-- the gym's ring: nothing built, the ring is the hub's. two marks on the mat, where each boxer stands
		for _, side in { "A", "B" } do
			att(root, "Stand" .. side, CFrame.new(0, 0, if side == "A" then L.gap else -L.gap) * FACE[side])
		end
	elseif kind == "golf" then
		-- slap golf: the whole course is the game's own (MiniGolf.build: the bed, six holes, its PLAY / JOIN prompt)
		GAMES.golf.build(T, ctx)
	end
	if kind == "box" then
		for _, side in { "A", "B" } do
			local a = att(root, "PromptAt" .. side, CFrame.new(0, 3, if side == "A" then L.mark else -L.mark))
			local pr = prompt(a, MG.TITLE.box, "Box", 8)
			pr:SetAttribute("MiniSide", side)
			T.prompts[side] = pr
		end
	elseif kind == "golf" then
		-- (its one prompt, side "*": up to four golfers, the first free place each; made by MiniGolf.build above)
	elseif kind == "arm" or kind == "board" then
		for _, side in { "A", "B" } do
			local seat = Instance.new("Seat")
			seat.Name = "Seat" .. side
			seat.Anchored = true; seat.CanCollide = false; seat.CanTouch = false; seat.CanQuery = false
			seat.Transparency = 1; seat.Size = Vector3.new(1.6, 0.2, 1.6)
			seat.CFrame = cf * CFrame.new(L.seat[side] + Vector3.new(0, seatY, 0)) * FACE[side]
			seat.Parent = model
			T.seats[side] = seat
			local a = att(seat, "PromptAt", CFrame.new(0, 1.6, 0))
			local pr = prompt(a, MG.TITLE[kind], "Sit", 7)
			pr:SetAttribute("MiniSide", side)
			T.prompts[side] = pr
		end
		-- the table and the seats are solid (people walk round them, not through). the table's box carries ACPass: a
		-- sitter leaning in has the root within a stud of its edge, which the anti-cheat's "inside" test would count
		-- (the AC session's rule, 18 Nov)
		local top = (L.top :: number)
		local tb = part(model, "Collision", cf * CFrame.new(0, top / 2, 0), Vector3.new(if kind == "arm" then 2.6 else 4.4, top, if kind == "arm" then 2.4 else 4.4), { CanCollide = true, CanQuery = true })
		tb:SetAttribute("ACPass", true)
		for _, side in { "A", "B" } do
			part(model, "Collision", cf * CFrame.new(L.seat[side] + Vector3.new(0, 1, 0)), Vector3.new(1.7, 2, 1.7), { CanCollide = true })
		end
	else
		local a = att(root, "PromptAt", CFrame.new(0, 3.6, -1.6))
		local pr = prompt(a, MG.TITLE.arcade, "Play", 7)
		pr:SetAttribute("MiniSide", "P")
		T.prompts.P = pr
	end
	CollectionService:AddTag(model, "MiniGame")
	model.Parent = parent or folder
	tables[id] = T
	for side, pr in T.prompts do
		pr.Triggered:Connect(function(p: Player) ctx.join(p, T, side) end)
	end
	GAMES[kind].setup(T, ctx)
	return T
end

-- ------------------------------------------------------------------ bots' bodies (a plain mannequin in the seat)
local botDesc = Instance.new("HumanoidDescription")
do
	local skin, limb = Color3.fromRGB(200, 196, 188), Color3.fromRGB(150, 154, 162)
	botDesc.HeadColor = skin; botDesc.TorsoColor = limb; botDesc.LeftArmColor = skin; botDesc.RightArmColor = skin
	botDesc.LeftLegColor = limb; botDesc.RightLegColor = limb
end
local function makeBot(): Model?
	local ok, m = pcall(function() return Players:CreateHumanoidModelFromDescription(botDesc, Enum.HumanoidRigType.R15) end)
	if not ok or not m then warn("[MiniGames] no bot body: " .. tostring(m)); return nil end
	local rig = m :: Model
	rig.Name = "MiniBot"
	local hum = rig:FindFirstChildOfClass("Humanoid")
	if hum then
		hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
		hum.BreakJointsOnDeath = false
		hum:SetStateEnabled(Enum.HumanoidStateType.Dead, false)
	end
	for _, d in rig:GetDescendants() do
		if d:IsA("BasePart") then d.CanCollide = false; d.CanTouch = false; d.CanQuery = false; d.Massless = true end
	end
	CollectionService:AddTag(rig, "MiniBot")
	return rig
end
local spareBots: { Model } = {}
task.spawn(function() -- (two ready before anyone asks: making one takes a moment)
	for _ = 1, 2 do
		local b = makeBot()
		if b then table.insert(spareBots, b); b.Parent = ServerStorage end
	end
end)

local function leanOf(T: Table): number return if T.kind == "arm" then MG.L.arm.lean else 0 end
local function afterSit(T: Table, side: string, hum: Humanoid)
	local seat = T.seats[side]
	local lean = leanOf(T)
	for _ = 1, 30 do
		local w = seat:FindFirstChild("SeatWeld") :: Weld?
		if w then
			if lean ~= 0 and not w:GetAttribute("Leaned") then
				w.C0 = w.C0 * CFrame.Angles(math.rad(-lean), 0, 0)
				w:SetAttribute("Leaned", true)
			end
			return
		end
		task.wait(0.05)
	end
end

-- where a boxer stands (the ring: no seats), its root's CFrame for a body of this humanoid
local function standCF(T: Table, side: string, hum: Humanoid?, root: BasePart?): CFrame
	local L = MG.L.box
	local at = T.cf * CFrame.new(0, 0, if side == "A" then L.gap else -L.gap) * FACE[side]
	local up = (if root then root.Size.Y / 2 else 1) + (if hum and hum.RigType == Enum.HumanoidRigType.R15 then hum.HipHeight else 2) + 0.05
	return at + Vector3.new(0, up, 0)
end

-- boxing gloves on a boxer's hands for the bout (on = false: off again). the kit's mg_glove (its origin is the middle of
-- a hand, the cuff up the forearm), sized to the hand, welded; a corner's colour each (A muted red, B muted blue)
local GLOVE_COLOUR = { A = Color3.fromRGB(150, 62, 58), B = Color3.fromRGB(58, 84, 140) }
-- (`whom`: the one leaving, whom ctx.leave has already taken out of T.who: without it a leaver kept the gloves on)
function ctx.gloves(T: Table, side: string, on: boolean, whom: any?)
	local who = if whom ~= nil then whom else T.who[side]
	local ch: Model? = if typeof(who) == "Instance" and who:IsA("Player") then who.Character
		elseif type(who) == "table" and who.Character then who.Character else T.bots[side]
	if not ch then return end
	for _, c in ch:GetChildren() do if c.Name == "MiniGlove" then c:Destroy() end end
	if not on then return end
	local hum = ch:FindFirstChildOfClass("Humanoid")
	local r6 = hum ~= nil and hum.RigType == Enum.HumanoidRigType.R6
	for _, hand in { "Right", "Left" } do
		local h = ch:FindFirstChild(if r6 then hand .. " Arm" else hand .. "Hand") :: BasePart?
		local src = kitModel("mg_glove")
		if not h or not src then if src then src:Destroy() end; continue end
		-- (an R15 hand ~0.3 across gets a glove about twice its size; an R6 arm is a stud wide: the glove at its end)
		local k = if r6 then 1.15 else math.clamp(math.max(h.Size.X, h.Size.Z) / 0.36, 0.7, 1.5)
		local at = if r6 then h.CFrame * CFrame.new(0, -h.Size.Y / 2 + 0.15, 0) else h.CFrame * CFrame.new(0, -0.05 * k, 0)
		src.Name = "MiniGlove"
		for _, p in src:GetDescendants() do
			if not p:IsA("BasePart") then continue end
			local rel = p.CFrame -- (the kit's own frame: relative to the hand's middle)
			p.Size *= k
			p.CFrame = at * (rel - rel.Position + rel.Position * k)
			p.Anchored = false; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Massless = true
			if string.find(p.Name, "a3a3a3", 1, true) then p.Color = GLOVE_COLOUR[side] end
			local w = Instance.new("WeldConstraint")
			w.Part0 = h; w.Part1 = p
			w.Parent = p
		end
		src.Parent = ch
	end
end

-- a boxer back onto their mark, facing the other one (each round's start: in between they walk where they like). for a
-- person it's the server moving them, so TeleportT first (the anti-cheat)
function ctx.toMark(T: Table, side: string)
	local who = T.who[side]
	local ch: Model? = if typeof(who) == "Instance" and who:IsA("Player") then who.Character
		elseif type(who) == "table" and who.Character then who.Character else T.bots[side]
	if not ch then return end
	local hum = ch:FindFirstChildOfClass("Humanoid")
	local root = ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not hum or not root then return end
	if typeof(who) == "Instance" and who:IsA("Player") then who:SetAttribute("TeleportT", os.clock()) end
	root.AssemblyLinearVelocity = Vector3.zero
	ch:PivotTo(standCF(T, side, hum, root))
end

-- a bot sits down at T's seat `side` (or gets up: on = false)
function ctx.botSeat(T: Table, side: string, level: string?)
	local old = T.bots[side]
	if old then
		T.bots[side] = nil
		local hum = old:FindFirstChildOfClass("Humanoid")
		if hum then hum.Sit = false end
		local w = T.seats[side] and T.seats[side]:FindFirstChild("SeatWeld")
		if w then w:Destroy() end
		for _, c in old:GetDescendants() do if c:IsA("IKControl") or c.Name == "MiniGlove" or c.Name == "MiniFace" then c:Destroy() end end
		-- (a boxer walked on its own feet: back to the still, see-through body a seat wants)
		if hum then hum.AutoRotate = true; hum:Move(Vector3.zero, false) end
		for _, d in old:GetDescendants() do if d:IsA("BasePart") then d.CanCollide = false end end
		old.Parent = ServerStorage
		table.insert(spareBots, old)
	end
	if not level then
		if ctx.isBot(T.who[side]) then T.who[side] = nil end
		ctx.refresh(T)
		return
	end
	local rig = table.remove(spareBots) or makeBot()
	if not rig then return end
	T.bots[side] = rig
	rig:SetAttribute("MiniSide", side) -- (the boxing client finds each corner's body by this)
	T.who[side] = { bot = true, level = level }
	local seat = T.seats[side]
	local hum = rig:FindFirstChildOfClass("Humanoid") :: Humanoid
	local root = rig:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not seat then
		-- (the ring: the bot walks on its own feet, the server's physics: MiniBox's botMove steers its Humanoid and turns
		-- its MiniFace to face the other boxer. its torso and head are solid so you bump into it, not through it. the
		-- boxing client plays its moves)
		if root then root.Anchored = false end
		local an = hum:FindFirstChildOfClass("Animator")
		if an then for _, tr in an:GetPlayingAnimationTracks() do tr:Stop(0) end end
		rig:SetAttribute("SitPlaying", nil)
		for _, n in { "UpperTorso", "LowerTorso", "Head" } do
			local p = rig:FindFirstChild(n)
			if p and p:IsA("BasePart") then p.CanCollide = true end
		end
		hum.AutoRotate = false
		hum.WalkSpeed = 0
		if root then
			local a0 = root:FindFirstChild("RootAttachment") :: Attachment?
			if not a0 then a0 = Instance.new("Attachment"); (a0 :: Attachment).Name = "RootAttachment"; (a0 :: Attachment).Parent = root end
			local ao = Instance.new("AlignOrientation")
			ao.Name = "MiniFace"
			ao.Mode = Enum.OrientationAlignmentMode.OneAttachment
			ao.Attachment0 = a0
			ao.RigidityEnabled = false
			ao.MaxTorque = 1e7
			ao.Responsiveness = 30
			ao.CFrame = CFrame.lookAt(Vector3.zero, (if side == "A" then 1 else -1) * T.cf.LookVector) -- (A faces -Z)
			ao.Parent = root
		end
		hum:SetStateEnabled(Enum.HumanoidStateType.FallingDown, false) -- (bumped, it stays on its feet)
		hum:SetStateEnabled(Enum.HumanoidStateType.Ragdoll, false)
		rig:PivotTo(standCF(T, side, hum, root))
		rig.Parent = T.model
		if root then pcall(function() root:SetNetworkOwner(nil) end) end
		ctx.refresh(T)
		return
	end
	if root then root.Anchored = false end
	rig:PivotTo(seat.CFrame * CFrame.new(0, 3, 0))
	rig.Parent = T.model
	if root then pcall(function() root:SetNetworkOwner(nil) end) end
	seat:Sit(hum)
	task.spawn(afterSit, T, side, hum)
	-- (a made body has no Animate script: Roblox's own sit pose, played here, reaches every client)
	local an = hum:FindFirstChildOfClass("Animator") or Instance.new("Animator", hum)
	if not rig:GetAttribute("SitPlaying") then
		local a = Instance.new("Animation")
		a.AnimationId = "rbxassetid://2506281703"
		local ok, tr = pcall(an.LoadAnimation, an, a)
		if ok and tr then tr.Looped = true; tr.Priority = Enum.AnimationPriority.Core; tr:Play(0); rig:SetAttribute("SitPlaying", true) end
	end
	ctx.refresh(T)
end

-- the prompts and the names on the table, from who sits where
function ctx.refresh(T: Table)
	if GAMES[T.kind].refresh then GAMES[T.kind].refresh(T, ctx); return end -- (golf: four places, one prompt)
	local m = T.model
	for _, side in { "A", "B", "P" } do
		if not T.prompts[side] then continue end
		local who = T.who[side]
		m:SetAttribute(side .. "Name", if who then ctx.nameOf(who) else nil)
		m:SetAttribute(side .. "Id", if who then ctx.idOf(who) else nil)
		local open = who == nil or (ctx.isBot(who) and GAMES[T.kind].canReplaceBot(T))
		T.prompts[side].Enabled = open
		T.prompts[side].ActionText = if who and ctx.isBot(who) then "Challenge" elseif side == "P" then "Play" elseif T.kind == "box" then "Box" else "Sit"
	end
end

-- ------------------------------------------------------------------ joining and leaving
local function bodyOf(p: Player): (Model?, Humanoid?, BasePart?)
	local ch = p.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not ch or not hum or not root or hum.Health <= 0 then return nil, nil, nil end
	return ch, hum, root
end
local function allowed(p: Player): boolean
	return MG.ZONES[Zones.of(p)] == true and p:GetAttribute("Zone") ~= "staging"
end

function ctx.join(p: Player, T: Table, side: string)
	if inGame[p] or not allowed(p) then return end
	local ch, hum, root = bodyOf(p)
	if not ch or not hum or not root then return end
	if (root.Position - T.cf.Position).Magnitude > (if T.kind == "golf" then 60 else 16) then return end
	-- (one prompt for several places, golf's: the game picks the first free one, none while a round's on)
	if side == "*" then
		local pick = GAMES[T.kind].pickSide and GAMES[T.kind].pickSide(T)
		if not pick then return end
		side = pick
	end
	local who = T.who[side]
	if who ~= nil and not (ctx.isBot(who) and GAMES[T.kind].canReplaceBot(T)) then return end
	if who ~= nil then ctx.botSeat(T, side, nil); GAMES[T.kind].left(T, side, who, ctx) end
	T.who[side] = p
	inGame[p] = { t = T, side = side }
	p:SetAttribute("TeleportT", os.clock())
	-- (sitting somewhere else, a hub seat, the cabinet's lid: up first, so the move below takes you)
	if hum.SeatPart then
		local w = hum.SeatPart:FindFirstChild("SeatWeld")
		if w then w:Destroy() end
		hum.Sit = false
	end
	root.AssemblyLinearVelocity = Vector3.zero
	if T.seats[side] then
		local seat = T.seats[side]
		if hum.SeatPart then local w = hum.SeatPart:FindFirstChild("SeatWeld"); if w then w:Destroy() end end
		ch:PivotTo(seat.CFrame * CFrame.new(0, 3, 0))
		seat:Sit(hum)
		task.spawn(afterSit, T, side, hum)
		-- (a sit that didn't take: out again, never "in a game" standing beside it)
		task.delay(1, function()
			local g = inGame[p]
			if g and g.t == T and g.side == side and hum.Parent and hum.SeatPart ~= seat then ctx.leave(p, "stood") end
		end)
	elseif T.kind == "box" then -- (the ring: onto your mark, facing the other one)
		ch:PivotTo(standCF(T, side, hum, root))
	elseif T.kind == "golf" then -- (the course: you stay where you are until your shot puts you by your dummy)
	else -- (the arcade: stand at the cabinet, facing the screen)
		local L = MG.L.arcade
		local at = T.cf * CFrame.new(L.stand)
		local up = root.Size.Y / 2 + (if hum.RigType == Enum.HumanoidRigType.R15 then hum.HipHeight else 2) + 0.1
		local pos = at.Position + Vector3.new(0, up, 0)
		ch:PivotTo(CFrame.lookAt(pos, pos - T.cf.LookVector)) -- (the screen faces the spot's look: you face back along it)
	end
	p:SetAttribute("MiniGameId", T.id)
	p:SetAttribute("MiniSide", side)
	p:SetAttribute("MiniGame", T.kind)
	ctx.refresh(T)
	GAMES[T.kind].joined(T, side, p, ctx)
end

function ctx.leave(p: Player, why: string?)
	local g = inGame[p]
	if not g then return end
	inGame[p] = nil
	local T, side = g.t, g.side
	if T.who[side] == p then T.who[side] = nil end
	p:SetAttribute("MiniGame", nil)
	p:SetAttribute("MiniGameId", nil)
	p:SetAttribute("MiniSide", nil)
	local ch, hum, root = bodyOf(p)
	if ch and hum and root then
		for _, c in hum:GetChildren() do if c:IsA("IKControl") and string.sub(c.Name, 1, 4) == "Mini" then c:Destroy() end end
		local L = MG.L[T.kind]
		if why ~= "gone" then
			local seated = hum.SeatPart ~= nil
			if seated then
				local w = (hum.SeatPart :: BasePart):FindFirstChild("SeatWeld")
				if w then w:Destroy() end
				hum.Sit = false
			end
			if seated or T.kind == "arcade" then
				local spot = if T.kind == "arcade" then L.leave else L.stand[side]
				local at = (T.cf * CFrame.new(spot)).Position
				local up = root.Size.Y / 2 + (if hum.RigType == Enum.HumanoidRigType.R15 then hum.HipHeight else 2) + 0.2
				local away = (at - T.cf.Position) * Vector3.new(1, 0, 1)
				p:SetAttribute("TeleportT", os.clock())
				root.AssemblyLinearVelocity = Vector3.zero
				local pos = at + Vector3.new(0, up, 0)
				ch:PivotTo(CFrame.lookAt(pos, pos + (if away.Magnitude > 0.1 then away.Unit else Vector3.zAxis)))
			end
		end
	end
	ctx.refresh(T)
	GAMES[T.kind].left(T, side, p, ctx)
end

-- ------------------------------------------------------------------ the remote
Remote.OnServerEvent:Connect(function(p: Player, kind: any, data: any)
	if kind == "leave" then ctx.leave(p, "asked"); return end
	local g = inGame[p]
	if not g or type(kind) ~= "string" or kind ~= g.t.kind or type(data) ~= "table" or type(data.op) ~= "string" then return end
	local ok, err = pcall(GAMES[kind].msg, g.t, p, g.side, data, ctx)
	if not ok then warn("[MiniGames] " .. kind .. " " .. tostring(data.op) .. ": " .. tostring(err)) end
end)

Players.PlayerRemoving:Connect(function(p: Player) ctx.leave(p, "gone") end)
local function watch(p: Player)
	p.CharacterRemoving:Connect(function() ctx.leave(p, "gone") end)
	p.CharacterAdded:Connect(function(ch: Model)
		local hum = ch:WaitForChild("Humanoid", 10) :: Humanoid?
		if hum then
			hum.Died:Connect(function() ctx.leave(p, "gone") end)
			-- got up by itself (a jump out of the seat): that's leaving
			hum:GetPropertyChangedSignal("SeatPart"):Connect(function()
				local g = inGame[p]
				if g and g.t.seats[g.side] and hum.SeatPart == nil then
					task.delay(0.3, function()
						local g2 = inGame[p]
						if g2 == g and hum.Parent and hum.SeatPart == nil then ctx.leave(p, "stood") end
					end)
				end
			end)
		end
	end)
end
for _, p in Players:GetPlayers() do watch(p) end
Players.PlayerAdded:Connect(watch)

-- out of the hub (a match, a map room) or wandered off the cabinet: out of the game
local acc = 0
RunService.Heartbeat:Connect(function(dt: number)
	for _, T in tables do
		local ok, err = pcall(GAMES[T.kind].step, T, dt, ctx)
		if not ok then warn("[MiniGames] step " .. T.id .. ": " .. tostring(err)) end
	end
	acc += dt
	if acc < 0.5 then return end
	acc = 0
	for p, g in inGame do
		local _, _, root = bodyOf(p)
		if not root or not allowed(p) then ctx.leave(p, "zone"); continue end
		if g.t.kind == "box" then
			-- (the ring: you walk all over it, so out means well past its ropes, or fallen off it)
			local l = g.t.cf:PointToObjectSpace(root.Position)
			local half = g.t.model:GetAttribute("Half")
			local b = (if type(half) == "number" then half - 1.75 else MG.L.box.bound) + 4
			if math.abs(l.X) > b or math.abs(l.Z) > b or l.Y < -6 or l.Y > 14 then ctx.leave(p, "away") end
		elseif g.t.kind == "golf" then
			-- (the course: anywhere on or by it)
			local l = g.t.cf:PointToObjectSpace(root.Position)
			local sz = MG.L.golf.size
			if math.abs(l.X) > sz.X / 2 + 10 or math.abs(l.Z) > sz.Y / 2 + 10 or l.Y < -6 or l.Y > 20 then ctx.leave(p, "away") end
		elseif (root.Position - g.t.cf.Position).Magnitude > 14 then ctx.leave(p, "away") end
	end
end)

-- ------------------------------------------------------------------ the spots
-- every hub's markers (20 Nov 2026: the owner wants all three hub concepts built, with travel between them; the hub
-- session's convention is side-session-notes/HUB-MARKERS.md). a marker is any BasePart under workspace.Map tagged
-- MiniGameSpot with Game = a kind (MG.L), the hub builders' own:
--   * a hub is a folder right under Map.Hub (Map.Hub.Square, .Concourse, .Atrium) and its markers carry Hub = its id
--     ("square"): their tables go into a MiniGames folder inside that hub folder, so they show and hide with it
--     (ZoneCull culls each child of Map.Hub per client), and their ids carry it: box1_square, arm1_square;
--   * the legacy ring's markers carry no Hub: their tables stay in Map.Hub.MiniGames as box1, arm1, board1, arcade1
--     (the tests and the docs use those);
--   * numbers count per hub and kind; a ring's own Ring (1..4) wins;
--   * anything under an ancestor with the attribute MiniGamesOff = true is skipped: a builder's staging copy;
--   * a marker that turns up later (a hub built while the server runs, a Studio test) is built when it appears. one
--     already built is never built twice
local built: { [Instance]: boolean } = {}
local folders: { [Instance]: Folder } = {}
local mapRef: Instance? = nil
local counts: { [string]: number } = {}
type Spot = { kind: string, cf: CFrame, half: number?, ring: number?, hub: string?, holder: Instance }
-- where a marker's tables live: its hub folder (the ancestor right under Map.Hub) when it names a hub, else Map.Hub
-- itself; a marker outside Map.Hub: its ancestor right under Map
local function hubOf(s: Instance): Instance
	local map = mapRef :: Instance
	local hubRoot = map:FindFirstChild("Hub")
	if hubRoot and s:IsDescendantOf(hubRoot) then
		if s:GetAttribute("Hub") == nil then return hubRoot end
		local top = s
		while top.Parent and top.Parent ~= hubRoot do top = top.Parent :: Instance end
		return top
	end
	local top = s
	while top.Parent and top.Parent ~= map and top.Parent ~= workspace do top = top.Parent :: Instance end
	return top
end
local function folderFor(holder: Instance): Folder
	local f = folders[holder]
	if f and f.Parent then return f end
	local nf = Instance.new("Folder")
	nf.Name = "MiniGames"
	nf.Parent = holder
	folders[holder] = nf
	return nf
end
local function switchedOff(s: Instance): boolean
	local a: Instance? = s
	while a and a ~= workspace do
		if a:GetAttribute("MiniGamesOff") == true then return true end
		a = a.Parent
	end
	return false
end
local function spotOf(s: Instance): Spot?
	if not s:IsA("BasePart") or built[s] or not mapRef or not s:IsDescendantOf(mapRef :: Instance) then return nil end
	local kind = s:GetAttribute("Game")
	if type(kind) ~= "string" or not MG.L[kind] or switchedOff(s) then return nil end
	built[s] = true
	local hub = s:GetAttribute("Hub")
	return { kind = kind, cf = s.CFrame, half = s:GetAttribute("Half"), ring = s:GetAttribute("Ring"),
		hub = if type(hub) == "string" and hub ~= "" then hub else nil, holder = hubOf(s) }
end
local function buildSpots(spots: { Spot })
	table.sort(spots, function(a, b) return a.cf.X + a.cf.Z * 0.001 < b.cf.X + b.cf.Z * 0.001 end)
	for _, s in spots do
		local key = (s.hub or "") .. "|" .. s.kind
		counts[key] = (counts[key] or 0) + 1
		-- (a marker's own number, the gym's Ring = 1..4, names its table: box1..box4 match the hub's rings)
		local num = if type(s.ring) == "number" then s.ring else counts[key]
		local suffix = if s.hub then "_" .. string.lower((string.gsub(s.hub :: string, "%W", ""))) else ""
		if tables[s.kind .. num .. suffix] then warn("[MiniGames] two markers for " .. s.kind .. num .. suffix .. ": the second is skipped"); continue end
		local ok, err = pcall(newTable, s.kind, CFrame.new(s.cf.Position) * s.cf.Rotation, num, folderFor(s.holder), suffix)
		-- (a ring's size: its marker's Half, the mat's middle to inside its ropes; MiniBox and MiniBoxUI fence to it)
		if ok and err and type(s.half) == "number" then (err :: any).model:SetAttribute("Half", s.half) end
		if not ok then warn("[MiniGames] building " .. s.kind .. ": " .. tostring(err)) end
	end
end
local function build()
	local map = workspace:WaitForChild("Map", 60)
	if not map then warn("[MiniGames] no Map"); return end
	mapRef = map
	local hub = map:WaitForChild("Hub", 30) -- (the first hub; the others are wherever their markers are)
	ReplicatedStorage:WaitForChild("JankfireMiniGames", 60)
	folder = folderFor(hub or map) -- (the first hub's folder: Studio's "place" test builds there)
	local spots: { Spot } = {}
	for _, s in CollectionService:GetTagged("MiniGameSpot") do
		local sp = spotOf(s)
		if sp then table.insert(spots, sp) end
	end
	-- the boxing ring when no hub has a "box" marker: the first hub's RingMat (its top's middle, the look along its right)
	local hasBox = false
	for _, sp in spots do if sp.kind == "box" then hasBox = true end end
	if not hasBox and hub then
		for _, d in hub:GetDescendants() do
			if d:IsA("BasePart") and d.Name == "RingMat" then
				local top = d.Position + d.CFrame.UpVector * (d.Size.Y / 2)
				table.insert(spots, { kind = "box", cf = CFrame.lookAt(top, top + d.CFrame.RightVector), half = math.min(d.Size.X, d.Size.Z) / 2, holder = hub })
				break
			end
		end
	end
	if #spots == 0 then
		for _, sp in MG.SPOTS do
			table.insert(spots, { kind = sp[1], cf = CFrame.new(sp[2], sp[3], sp[4]) * CFrame.Angles(0, math.rad(sp[5] or 0), 0), holder = hub or map })
		end
	end
	buildSpots(spots)
	for _, f in folders do f:SetAttribute("Ready", true) end
	-- (a marker that turns up later: its builder sets the attributes right after the tag, so a moment's wait)
	CollectionService:GetInstanceAddedSignal("MiniGameSpot"):Connect(function(s: Instance)
		task.wait(0.5)
		local sp = spotOf(s)
		if sp then
			buildSpots({ sp })
			folderFor(sp.holder):SetAttribute("Ready", true)
		end
	end)
end
task.spawn(build)

-- ------------------------------------------------------------------ the test hook (Studio only)
if RunService:IsStudio() then
	local bf = Instance.new("BindableFunction")
	bf.Name = "JankMiniTest"
	bf.OnInvoke = function(what: string, a: any, b: any, c: any, d: any): any
		if what == "state" then
			local out = {}
			for id, T in tables do
				local at = {}
				for k, v in T.model:GetAttributes() do at[k] = if typeof(v) == "Vector3" then tostring(v) else v end
				local who = {}
				for side, w in T.who do who[side] = ctx.nameOf(w) end
				out[id] = { at = at, who = who, pos = tostring(T.cf.Position) }
			end
			local ing = {}
			for p, g in inGame do ing[p.Name] = g.t.id .. ":" .. g.side end
			return HttpService:JSONEncode({ tables = out, players = ing })
		elseif what == "sit" then
			local T = tables[b]
			if not T then return "no table " .. tostring(b) end
			ctx.join(a, T, c)
			return if inGame[a] then "sat" else "refused"
		elseif what == "leave" then
			ctx.leave(a, "asked")
			return "left"
		elseif what == "op" then
			local g = inGame[a]
			if not g then return "not in a game" end
			local ok, err = pcall(GAMES[g.t.kind].msg, g.t, a, g.side, b, ctx)
			return if ok then "ok" else tostring(err)
		elseif what == "standin" then
			-- a second player for a two-player test: a body in the seat that the games treat as a person (not a bot);
			-- it acts only through ("as", tableId, side, data), exactly as a client's message would
			local T = tables[a]
			if not T or T.who[b] ~= nil then return "seat taken" end
			-- (d = "r6": an R6 body, for the boxing R6 check)
			local rig: Model? = nil
			if d == "r6" then
				local ok, m = pcall(function() return Players:CreateHumanoidModelFromDescription(botDesc, Enum.HumanoidRigType.R6) end)
				if ok then rig = m; for _, x in (m :: Model):GetDescendants() do if x:IsA("BasePart") then x.CanCollide = false; x.Massless = true end end end
			else
				rig = table.remove(spareBots) or makeBot()
			end
			if not rig then return "no body" end
			rig.Name = "StandIn"
			rig:SetAttribute("MiniSide", b)
			local fake = { standIn = true, UserId = -7, DisplayName = "STAND-IN", Name = "StandIn", Character = rig, Parent = Players,
				GetNetworkPing = function() return 0.05 end }
			T.bots[b] = rig
			local seat = T.seats[b]
			rig:PivotTo((if seat then seat.CFrame else T.cf * CFrame.new(MG.L.arcade.stand)) * CFrame.new(0, 3, 0))
			rig.Parent = T.model
			if seat then
				local hum = rig:FindFirstChildOfClass("Humanoid") :: Humanoid
				seat:Sit(hum)
				task.spawn(afterSit, T, b, hum)
			elseif T.kind == "box" then
				local hum = rig:FindFirstChildOfClass("Humanoid") :: Humanoid
				local rr = rig:FindFirstChild("HumanoidRootPart") :: BasePart?
				if rr then rr.Anchored = true end
				rig:PivotTo(standCF(T, b, hum, rr))
			elseif T.kind == "golf" then
				-- (held still by the first tee; its shot puts it by its dummy, like a golfer)
				local rr = rig:FindFirstChild("HumanoidRootPart") :: BasePart?
				if rr then rr.Anchored = true end
				rig:PivotTo(T.cf * CFrame.new(MG.L.golf.cols[1] + 4, MG.L.golf.H + 3, MG.L.golf.rows[1] + 17))
			end
			T.who[b] = fake
			ctx.refresh(T)
			GAMES[T.kind].joined(T, b, fake, ctx)
			return "stand-in at " .. a .. ":" .. b
		elseif what == "as" then
			local T = tables[a]
			local fake = T and T.who[b]
			if type(fake) ~= "table" or not fake.standIn then return "no stand-in there" end
			if T.kind == "arm" and c.op == "auto" then
				-- (the stand-in's hand: through the bout it presses each check, a hit at `rate`, else a late miss, as a
				-- client would: the needle's own position at the press)
				task.spawn(function()
					local rng = Random.new()
					local plan: { [number]: boolean } = {}
					while T.who[b] == fake and (T.g.state == "bout" or T.g.state == "count") do
						local chk = T.g.chk[b]
						if chk and ctx.now() >= chk.t0 then
							if plan[chk.id] == nil then plan[chk.id] = rng:NextNumber() < (c.rate or 0.7) end
							local good = plan[chk.id]
							local x = MG.needle(chk, ctx.now())
							if (good and math.abs(x - chk.c) < chk.w * 0.5) or (not good and math.abs(x - chk.c) > chk.w * 1.5) then
								task.wait(rng:NextNumber(0, 0.05))
								pcall(GAMES.arm.msg, T, fake, b, { op = "hit", id = chk.id, pos = MG.needle(chk, ctx.now()) }, ctx)
								task.wait(0.15)
							end
						end
						task.wait()
					end
				end)
				return "pressing"
			end
			local ok, err = pcall(GAMES[T.kind].msg, T, fake, b, c, ctx)
			return if ok then "ok" else tostring(err)
		elseif what == "standout" then
			local T = tables[a]
			local fake = T and T.who[b]
			if type(fake) ~= "table" or not fake.standIn then return "no stand-in there" end
			T.who[b] = nil
			local rig = T.bots[b]
			T.bots[b] = nil
			if rig then
				local w = T.seats[b] and T.seats[b]:FindFirstChild("SeatWeld")
				if w then w:Destroy() end
				rig:Destroy()
			end
			ctx.refresh(T)
			GAMES[T.kind].left(T, b, fake, ctx)
			return "stand-in gone"
		elseif what == "spots" then
			local out = {}
			for id, T in tables do table.insert(out, id .. " " .. tostring(T.cf.Position)) end
			return table.concat(out, "\n")
		elseif what == "place" then
			-- (a game built at any CFrame for a test, before the hub has a marker for it: ("place", kind, cf); n 9)
			if typeof(b) ~= "CFrame" or not MG.L[a] then return "no" end
			local ok, T = pcall(newTable, a, b, 9)
			return if ok and T then T.id else "failed " .. tostring(T)
		end
		return "?"
	end
	bf.Parent = ServerStorage
end
