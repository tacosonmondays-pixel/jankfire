--!strict
-- THE HIDDEN NPCS, on your screen (18 Nov 2026; the server half: LoreNPCs.server, the book: Shared.LoreData, the rigs:
-- Shared.LoreRigs). Their bodies on the server stand still in the web's build pose; here each one lives the way it did
-- on the web: the web's own update() maths (public/js/lorenpcs.js), line for line, on the same joints, moved with one
-- BulkMoveTo a frame. Gary slumps at his screen and sighs, then spins his chair round to you; Dale hits his machine
-- with the wrench and turns when you come; the Janitor mops a figure eight and stares at the wall every 14 s; Mr.
-- Smiles kicks his legs over the drop, his balloons bobbing, and waves when you're close; Todd types and strokes his
-- beard at the glitching cube. Heads turn to you (the web's headLook).
-- SPEECH: a bubble over the head (in the world, not the HUD), the web's lines typed out one at a time: the opening
-- beat when you first come near, the next beat each time you use TALK (their prompt), the gift line when the server
-- says you found them (remote Lore "found"), the "again" line once you've heard everything.
-- Cheap: only NPCs within LIVE studs of your camera move (the rest keep their last pose); past HIDE they are put aside
-- on this client (ZoneCull also takes the whole Map.Lore away when you're far from the hub).
-- HIDDEN UNTIL ITS CODE (18 Nov 2026, the owner's code panel; the server half: LoreNPCs.server): an NPC your LoreSeen
-- (the server's attribute) doesn't list isn't there for you: no body, no bubble, no TALK, no movement (pieces marked
-- Clue would stay: none are now). The hub egg's mannequin too (Map.Hub.HubEgg: its body, outline and prompt, its
-- collisions off on your screen). A right code at the panel (remote Lore "seen", how = "code") spawns a copy in beside
-- the panel (CodePanel.Show): it fades in with a soft chime, greets you and says its lines, then after SHOW_LIFE s
-- (or when you walk off) it fades away, and from then on it's at its own spot for you.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local me = Players.LocalPlayer
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Rigs = require(Shared:WaitForChild("LoreRigs")) :: any
local Data = require(Shared:WaitForChild("LoreData")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local LoreR = Remotes:WaitForChild("Lore") :: RemoteEvent

local LIVE = 110 -- studs: closer than this they move
local HIDE = 260 -- studs: further than this they're put aside here
local SAY_NEAR = 22 -- studs: the opening beat when you first come this close
local SAY_RESET = 60 -- studs: walk this far away and the opening plays again next time
local TYPE_CPS = 38 -- characters a second
local FADE = 0.9 -- s a revealed NPC takes to fade in
local SHOW_LIFE = 18 -- s a spawned-in NPC stays by the code panel
local SHOW_FAR = 60 -- studs: walk this far from it and it goes
local showFolder = Instance.new("Folder") -- (the panel's spawn-ins: on this screen only, never in Map.Lore)
showFolder.Name = "LoreShowLocal"
showFolder.Parent = workspace
local aside = Instance.new("Folder")
aside.Name = "LoreAside"

-- ------------------------------------------------------------------ the web's helpers
local function lerp(a: number, b: number, k: number): number return a + (b - a) * k end
local function bump(k: number): number return if k <= 0 or k >= 1 then 0 else math.sin(k * math.pi) end
local function wrapA(a: number): number return math.atan2(math.sin(a), math.cos(a)) end
local function yawTo(ax: number, az: number, bx: number, bz: number): number return math.atan2(-(bx - ax), -(bz - az)) end
local function clamp(v: number, a: number, b: number): number return math.max(a, math.min(b, v)) end

type Joint = { name: string, parent: Joint?, pre: CFrame, pos: { number }, rot: { number }, k: number, cf: CFrame }
type Piece = { part: BasePart, joint: Joint, off: CFrame }
type Npc = {
	id: string, model: Model, root: BasePart, base: CFrame, yaw: number, J: { [string]: Joint }, order: { Joint },
	pieces: { Piece }, parts: { BasePart }, cfs: { CFrame }, st: any, t0: number, out: boolean, home: Instance,
	bubble: any, heard: number, nearSaid: boolean, live: boolean,
	clues: { BasePart }, shown: boolean, vis: number, prompt: ProximityPrompt?,
	temp: boolean, born: number, leaving: boolean,
}
local npcs: { [Model]: Npc } = {}

-- ------------------------------------------------------------------ who you've revealed (the server's LoreSeen)
local seen: { [string]: boolean } = {}
local function readSeen()
	table.clear(seen)
	local s = me:GetAttribute("LoreSeen")
	if type(s) == "string" then for _, id in string.split(s, ",") do if id ~= "" then seen[id] = true end end end
end
readSeen()
-- body pieces: hidden when far or not revealed (faded in by vis); clue pieces: only when far
local function apply(n: Npc)
	local body = if n.out then 1 else 1 - n.vis
	for _, p in n.parts do p.LocalTransparencyModifier = body end
	for _, p in n.clues do p.LocalTransparencyModifier = if n.out then 1 else 0 end
	for _, d in n.model:GetDescendants() do if d:IsA("Beam") then d.Enabled = not n.out end end
	if n.prompt then n.prompt.Enabled = n.shown and not n.out end
	if not n.shown and n.bubble then n.bubble.queue = {}; n.bubble.line = nil; n.bubble.gui.Enabled = false end
end

-- ------------------------------------------------------------------ rigs
local function eulerXYZ(r: { number }): CFrame return CFrame.fromEulerAnglesXYZ(r[1], r[2], r[3]) end
local function local_(j: Joint): CFrame
	return CFrame.new(j.pos[1] * j.k, j.pos[2] * j.k, j.pos[3] * j.k) * eulerXYZ(j.rot)
end
local function solve(n: Npc)
	for _, j in n.order do
		local l = j.pre * local_(j)
		j.cf = if j.parent then j.parent.cf * l else l
	end
end
-- the head's world position and the joints' world yaw (for headLook): from last frame's solve
local function worldOf(n: Npc, j: Joint): CFrame return n.base * j.cf end

-- ------------------------------------------------------------------ speech bubbles
local function makeBubble(n: Npc)
	local head = n.model:FindFirstChild(n.id .. "_head") :: BasePart?
	local gui = Instance.new("BillboardGui")
	gui.Name = "LoreBubble"
	gui.Adornee = head or n.root
	gui.Size = UDim2.fromOffset(300, 120)
	gui.StudsOffsetWorldSpace = Vector3.new(0, if head then 2.6 else 8, 0)
	gui.LightInfluence = 0
	gui.MaxDistance = 70
	gui.AlwaysOnTop = false
	gui.ResetOnSpawn = false
	gui.Enabled = false
	local holder = Instance.new("Frame")
	holder.BackgroundTransparency = 1
	holder.Size = UDim2.fromScale(1, 1)
	holder.Parent = gui
	local box = Instance.new("Frame")
	box.Name = "Box"
	box.AnchorPoint = Vector2.new(0.5, 1)
	box.Position = UDim2.new(0.5, 0, 1, -10)
	box.AutomaticSize = Enum.AutomaticSize.XY
	box.Size = UDim2.fromOffset(0, 0)
	box.BackgroundColor3 = Color3.fromRGB(22, 22, 26)
	box.BackgroundTransparency = 0.12
	box.Parent = holder
	local c = Instance.new("UICorner"); c.CornerRadius = UDim.new(0, 10); c.Parent = box
	local pad = Instance.new("UIPadding")
	pad.PaddingLeft = UDim.new(0, 12); pad.PaddingRight = UDim.new(0, 12); pad.PaddingTop = UDim.new(0, 8); pad.PaddingBottom = UDim.new(0, 8)
	pad.Parent = box
	local lim = Instance.new("UISizeConstraint"); lim.MaxSize = Vector2.new(276, 400); lim.Parent = box
	local tl = Instance.new("TextLabel")
	tl.Name = "Text"
	tl.BackgroundTransparency = 1
	tl.AutomaticSize = Enum.AutomaticSize.XY
	tl.Size = UDim2.fromOffset(0, 0)
	tl.FontFace = Font.new("rbxasset://fonts/families/BuilderSans.json", Enum.FontWeight.Medium)
	tl.TextSize = 17
	tl.TextColor3 = Color3.fromRGB(238, 236, 230)
	tl.TextWrapped = true
	tl.TextXAlignment = Enum.TextXAlignment.Left
	tl.Text = ""
	tl.Parent = box
	local wrapLim = Instance.new("UISizeConstraint"); wrapLim.MaxSize = Vector2.new(252, 400); wrapLim.Parent = tl
	local tail = Instance.new("Frame")
	tail.Name = "Tail"
	tail.AnchorPoint = Vector2.new(0.5, 0.5)
	tail.Position = UDim2.new(0.5, 0, 1, -10)
	tail.Size = UDim2.fromOffset(12, 12)
	tail.Rotation = 45
	tail.BackgroundColor3 = box.BackgroundColor3
	tail.BackgroundTransparency = box.BackgroundTransparency
	tail.BorderSizePixel = 0
	tail.Parent = holder
	gui.Parent = me:WaitForChild("PlayerGui")
	n.bubble = { gui = gui, text = tl, queue = {} :: { string }, line = nil :: string?, shown = 0, holdUntil = 0, typing = false }
end
-- say these lines (they replace whatever was queued)
local function say(n: Npc, lines: { string })
	if not n.bubble then makeBubble(n) end
	local b = n.bubble
	b.queue = table.clone(lines)
	b.line = nil
end
local function stepBubble(n: Npc, dt: number, now: number)
	local b = n.bubble
	if not b then return end
	if not b.line then
		if #b.queue == 0 then
			if b.gui.Enabled and now > b.holdUntil then b.gui.Enabled = false end
			b.typing = false
			return
		end
		b.line = table.remove(b.queue, 1)
		b.shown = 0
		b.gui.Enabled = true
	end
	local line = b.line :: string
	local len = utf8.len(line) or #line
	if b.shown < len then
		b.typing = true
		b.shown = math.min(len, b.shown + dt * TYPE_CPS)
		local cut = utf8.offset(line, math.floor(b.shown) + 1)
		b.text.Text = if cut then string.sub(line, 1, cut - 1) else line
		b.holdUntil = now + 1.4 + len * 0.035
	else
		b.typing = false
		b.text.Text = line
		if now > b.holdUntil then b.line = nil end
	end
end

-- ------------------------------------------------------------------ the web's update(), one per NPC
-- ctx: eye (world, studs), k (the web's near, 0..1), say (a line is being typed), rp (the root's world position), yaw
local function headLook(n: Npc, st: any, ctx: any, rootYaw: number, k: number, dt: number, maxY: number)
	local h = n.J.head
	local ty, tx = 0, 0
	if ctx.eye and k > 0 then
		local p = worldOf(n, h).Position
		ty = clamp(wrapA(yawTo(p.X, p.Z, ctx.eye.X, ctx.eye.Z) - rootYaw), -maxY, maxY) * k
		tx = clamp(math.atan2(ctx.eye.Y - p.Y, math.sqrt((ctx.eye.X - p.X) ^ 2 + (ctx.eye.Z - p.Z) ^ 2)), -0.5, 0.5) * k
	end
	st.hy = lerp(st.hy or 0, ty + (st.oy or 0), math.min(1, dt * 4))
	st.hx = lerp(st.hx or 0, tx + (st.ox or 0), math.min(1, dt * 4))
	h.rot[2] = st.hy
	h.rot[1] = st.hx
end
local function faceYou(n: Npc, body: Joint, ctx: any, k: number, dt: number, speed: number)
	local want = if k > 0.5 and ctx.eye then wrapA(yawTo(ctx.rp.X, ctx.rp.Z, ctx.eye.X, ctx.eye.Z) - ctx.yaw) else 0
	body.rot[2] += wrapA(want - body.rot[2]) * math.min(1, dt * speed)
end
local function speak(n: Npc, t: number, sayOn: boolean, k: number): number
	if not sayOn then return 0 end
	local h = n.J.head
	h.rot[1] += math.sin(t * 13) * 0.04 * k + math.sin(t * 5.3) * 0.03 * k
	return math.sin(t * 3.1) * 0.5 + 0.5
end

local UPDATE: { [string]: (Npc, number, number, any) -> () } = {}

UPDATE.gary = function(n, dt, t, ctx)
	local J, st, k = n.J, n.st, ctx.k
	local want = if k > 0.4 and ctx.eye then wrapA(yawTo(ctx.rp.X, ctx.rp.Z, ctx.eye.X, ctx.eye.Z) - ctx.yaw) else math.sin(t * 0.4) * 0.08
	st.turn = lerp(st.turn or 0, want, math.min(1, dt * (if k > 0.4 then 3 else 1.2)))
	J.turn.rot[2] = st.turn
	local sigh = bump(((t % 7) - 5) / 1.6)
	local atDesk = 1 - math.min(1, math.abs(st.turn) * 1.5)
	J.body.rot[1] = 0.16 * atDesk - sigh * 0.06
	J.arm.rot[1] = lerp(-0.95, -0.25, atDesk) + math.sin(t * 9) * 0.03 * atDesk
	J.armL.rot[1] = lerp(-1.1, -0.35, atDesk) + math.sin(t * 7.3 + 1) * 0.02 * atDesk
	st.ox = -0.25 * atDesk - sigh * 0.12
	headLook(n, st, ctx, ctx.yaw + J.turn.rot[2], k, dt, 0.8)
	local g = speak(n, t, ctx.say, 1)
	if g > 0 then J.armL.rot[1] += g * 0.4 end
end

UPDATE.dale = function(n, dt, t, ctx)
	local J, st, k = n.J, n.st, ctx.k
	faceYou(n, J.turn, ctx, k, dt, 2.2)
	local busy = math.max(0, 1 - math.abs(J.turn.rot[2]) * 1.2)
	st.hitAt = st.hitAt or (t + 1.2)
	st.shake = st.shake or 0
	if t > st.hitAt then
		st.hitAt = t + 1.8 + math.random() * 1.6
		if busy > 0.8 then st.shake = 1 end
	end
	local sw = math.max(0, 1 - (st.hitAt - t) / 0.35)
	st.shake = math.max(0, st.shake - dt * 4)
	J.machine.rot[3] = math.sin(t * 60) * 0.012 * st.shake
	J.machine.pos[1] = -0.25 + math.sin(t * 47) * 0.01 * st.shake
	J.door.rot[2] = 1.95 + math.sin(t * 40) * 0.05 * st.shake
	J.arm.rot[1] = lerp(1.1, lerp(1.6, -0.1, sw), busy)
	J.arm.rot[2] = 0.2 * busy
	J.armL.rot[1] = lerp(-1.3, 0.2, busy)
	J.body.rot[1] = 0.12 * busy
	st.ox = busy * (0.05 + math.sin(t * 0.7) * 0.06)
	st.oy = busy * math.sin(t * 0.5) * 0.2
	headLook(n, st, ctx, ctx.yaw + J.turn.rot[2], k, dt, 0.9)
	local g = speak(n, t, ctx.say, 1)
	if g > 0 then J.armL.rot[1] = lerp(J.armL.rot[1], -0.4, g) end
end

UPDATE.janitor = function(n, dt, t, ctx)
	local J, st, k = n.J, n.st, ctx.k
	faceYou(n, J.turn, ctx, k, dt, 1.0)
	local cyc = t % 14
	local stare = if cyc > 10 then bump((cyc - 10) / 4) else 0
	local work = (1 - stare) * (1 - math.min(1, k * 1.4))
	local sw = math.sin(t * 1.6)
	J.mop.rot[2] = sw * 0.45 * work
	J.mop.rot[1] = -0.95 + math.sin(t * 3.2) * 0.06 * work
	J.body.rot[2] = sw * 0.12 * work
	J.arm.rot[1] = -0.55 + math.sin(t * 3.2) * 0.05 * work
	J.arm.rot[2] = sw * 0.2 * work
	J.armL.rot[1] = -0.45
	J.armL.rot[2] = 0.35 + sw * 0.15 * work
	st.oy = stare * 1.1
	st.ox = -0.05 * work - 0.02
	headLook(n, st, ctx, ctx.yaw + J.turn.rot[2], k, dt, 1.2)
	speak(n, t, ctx.say, 0.5)
end

local BALLOONS = { { -0.25, 0.1, 1.6 }, { 0.05, 0.3, 1.85 }, { 0.3, 0.05, 1.5 } }
UPDATE.smiles = function(n, dt, t, ctx)
	local J, st, k = n.J, n.st, ctx.k
	J.kneeL.rot[1] = -1.4 + math.sin(t * 1.3) * 0.3
	J.kneeR.rot[1] = -1.4 + math.sin(t * 1.3 + 2.2) * 0.3
	J.body.rot[3] = math.sin(t * 0.6) * 0.04
	local wave = if k > 0.5 then 1 else 0
	J.arm.rot[1] = lerp(-1.3, 2.6, wave)
	J.arm.rot[3] = lerp(0.25, -0.2 + math.sin(t * 9) * 0.35, wave)
	J.armL.rot[1] = 0.25 + math.sin(t * 0.8) * 0.05
	st.oy = math.sin(t * 0.35) * 0.35 * (1 - k)
	st.ox = -0.25 * (1 - k) + math.sin(t * 0.9) * 0.05
	headLook(n, st, ctx, ctx.yaw, k, dt, 1.0)
	J.head.rot[3] = math.sin(t * 0.7) * 0.12
	speak(n, t, ctx.say, 1.5)
	-- the balloons follow his left glove (solve the arm first: they hang off where it is this frame)
	solve(n)
	local armL = J.armL
	local hand = (armL.cf * CFrame.new(0.38 * armL.k, -0.05 * armL.k, -0.53 * armL.k)).Position / 3
	st.ph = st.ph or { math.random() * 6, math.random() * 6, math.random() * 6 }
	for i, b in BALLOONS do
		local j = J["balloon" .. i]
		if j then
			local ph = st.ph[i]
			j.pos[1] = hand.X + b[1] + math.sin(t * 0.9 + ph) * 0.12
			j.pos[2] = hand.Y + b[3] + math.sin(t * 1.3 + ph) * 0.06
			j.pos[3] = hand.Z + b[2] + math.cos(t * 0.7 + ph) * 0.12
			j.rot[3] = math.sin(t + ph) * 0.15
		end
	end
end

UPDATE.todd = function(n, dt, t, ctx)
	local J, st, k = n.J, n.st, ctx.k
	J.bug.rot[1] = t * 0.7
	J.bug.rot[2] = t * 1.1
	J.bug.pos[2] = 1.25 + math.sin(t * 1.7) * 0.05 + (if math.random() < 0.04 then 0.03 else 0) -- (the glitch)
	local cyc = t % 9
	local think = if cyc > 6.5 then bump((cyc - 6.5) / 2.5) else 0
	local typ = (1 - think) * (1 - math.min(1, k * 1.5))
	J.arm.rot[1] = lerp(-0.6, -0.35 + math.sin(t * 22) * 0.06, typ)
	J.armL.rot[1] = lerp(-0.6, -0.4 + math.sin(t * 19 + 1) * 0.06, typ)
	J.armL.rot[1] = lerp(J.armL.rot[1], 1.2, think)
	J.body.rot[1] = 0.2 * typ
	st.ox = -0.3 * typ + 0.1 * think
	st.oy = think * 0.8
	local wv = if k > 0.5 then 1 else 0
	J.arm.rot[1] = lerp(J.arm.rot[1], 2.5, wv)
	J.arm.rot[3] = lerp(0, math.sin(t * 10) * 0.4, wv)
	headLook(n, st, ctx, ctx.yaw, k, dt, 1.0)
	speak(n, t, ctx.say, 1.2)
end

-- ------------------------------------------------------------------ the story cast (the web's actors.js, standing)
-- the gesture clips (public/js/story/actors.js CLIPS, the same numbers): f(J, t, k) adds onto the pose. len in s
local function ss(t: number): number return if t <= 0 then 0 elseif t >= 1 then 1 else t * t * (3 - 2 * t) end
local CLIPS: { [string]: { len: number, f: (any, number, number) -> () } } = {
	wave = { len = 1.8, f = function(J, t, k) J.arm.rot[1] += 2.6 * k; J.arm.rot[3] += (0.5 + math.sin(t * 12) * 0.35) * k; J.foreR.rot[1] += 0.5 * k end },
	nod = { len = 0.9, f = function(J, t, k) J.head.rot[1] -= math.abs(math.sin(t * 9)) * 0.25 * k end },
	shake = { len = 1.0, f = function(J, t, k) J.head.rot[2] += math.sin(t * 16) * 0.35 * k end },
	shrug = { len = 1.2, f = function(J, t, k)
		local b = bump(t / 1.2) * k
		J.arm.rot[3] += 0.45 * b; J.armL.rot[3] -= 0.45 * b; J.foreR.rot[1] += 1.3 * b; J.foreL.rot[1] += 1.3 * b
		J.foreR.rot[3] += 0.6 * b; J.foreL.rot[3] -= 0.6 * b; J.head.rot[3] += 0.2 * b; J.spine.pos[2] += 0.03 * b
	end },
	point = { len = 1.6, f = function(J, t, k) J.arm.rot[1] += 1.5 * k; J.foreR.rot[1] -= 0.2 * k end },
	cry = { len = 3, f = function(J, t, k)
		J.armL.rot[1] += 2.3 * k; J.foreL.rot[1] += 1.7 * k; J.head.rot[1] -= (0.3 + math.sin(t * 9) * 0.06) * k; J.spine.rot[1] -= 0.12 * k
	end },
	flex = { len = 1.8, f = function(J, t, k)
		local b = ss(t / 0.3) * k
		J.arm.rot[3] += 1.45 * b; J.armL.rot[3] -= 1.45 * b; J.foreR.rot[3] += 1.9 * b; J.foreL.rot[3] -= 1.9 * b; J.spine.rot[1] += 0.08 * b
	end },
	bow = { len = 1.6, f = function(J, t, k) J.spine.rot[1] -= 0.7 * bump(t / 1.6) * k end },
	stomp = { len = 0.8, f = function(J, t, k)
		J.spine.pos[2] -= 0.06 * bump(t / 0.25) * k; J.arm.rot[3] += 0.4 * bump(t / 0.8) * k; J.armL.rot[3] -= 0.4 * bump(t / 0.8) * k
	end },
	think = { len = 2.5, f = function(J, t, k)
		J.arm.rot[1] += 1.0 * k; J.foreR.rot[1] += 2.2 * k; J.arm.rot[3] -= 0.3 * k; J.head.rot[3] += 0.15 * k; J.head.rot[1] += 0.12 * k
	end },
	write = { len = 9e9, f = function(J, t, k)
		J.armL.rot[1] += 0.9 * k; J.foreL.rot[1] += 1.0 * k; J.arm.rot[1] += 0.8 * k; J.foreR.rot[1] += (1.1 + math.sin(t * 18) * 0.12) * k
		J.arm.rot[3] -= 0.2 * k; J.head.rot[1] -= 0.4 * k
	end },
	hold = { len = 9e9, f = function(J, t, k)
		J.arm.rot[1] += 0.7 * k; J.armL.rot[1] += 0.7 * k; J.foreR.rot[1] += 0.9 * k; J.foreL.rot[1] += 0.9 * k; J.arm.rot[3] -= 0.1 * k; J.armL.rot[3] += 0.1 * k
	end },
	shock = { len = 1.2, f = function(J, t, k)
		local b = ss(t / 0.12) * k
		J.arm.rot[3] += 0.9 * b; J.armL.rot[3] -= 0.9 * b; J.foreR.rot[1] += 1.2 * b; J.foreL.rot[1] += 1.2 * b; J.spine.rot[1] += 0.15 * b; J.head.rot[1] += 0.1 * b
	end },
	-- "you're late." (mina): a slow look away, a beat, then the head comes round to you sharp, chin up, a tilt
	late = { len = 3.2, f = function(J, t, k)
		local away = ss(t / 0.5) * (1 - ss((t - 1.1) / 0.28))
		local back = ss((t - 1.1) / 0.28)
		local over = bump((t - 1.3) / 0.35) * 0.07
		local up = back * (1 - ss((t - 2.6) / 0.6))
		J.head.rot[2] += (-0.7 * away + over) * k; J.head.rot[1] += (-0.06 * away + 0.07 * up) * k; J.head.rot[3] += 0.08 * up * k
		J.spine.rot[1] += 0.035 * up * k; J.spine.pos[2] += 0.008 * up * k
	end },
}
-- (the spine's rest numbers, kept once per NPC: actors.js starts every frame from them)
local function castRest(n: Npc)
	if n.st.rest then return end
	local J = n.J
	n.st.rest = { spineX = J.spine.rot[1], spineY = J.spine.pos[2], tilt = (Rigs[n.id] and Rigs[n.id].tilt) or 0 }
end
local function playClip(n: Npc, name: string)
	if CLIPS[name] then n.st.clip = { name = name, t = 0 } end
end
local function castUpdate(n: Npc, dt: number, t: number, ctx: any)
	local J, st = n.J, n.st
	if not (J.arm and J.armL and J.foreR and J.foreL and J.spine and J.head) then return end
	castRest(n)
	local rest = st.rest
	local e = Data.get(n.id)
	-- the rest pose, every frame (actors.js pose(): arms down a touch forward, elbows a touch bent)
	J.arm.rot = { 0.05, 0, 0.1 }; J.armL.rot = { 0.05, 0, -0.1 }
	J.foreR.rot = { 0.22, 0, 0 }; J.foreL.rot = { 0.22, 0, 0 }
	J.spine.rot = { rest.spineX, 0, 0 }; J.spine.pos[2] = rest.spineY
	J.head.rot = { 0, 0, rest.tilt }
	-- breathing, and the idle style
	local br = math.sin(t * 1.9)
	J.spine.pos[2] += br * 0.006
	J.spine.rot[1] -= br * 0.012
	local idle = e and e.idle
	if idle == "sway" then J.spine.rot[3] = math.sin(t * 0.6) * 0.05; J.head.rot[3] = math.sin(t * 0.6 + 1) * 0.06 end
	if idle == "fidget" then
		local f = if math.sin(t * 0.9) > 0.6 then 1 else 0
		J.foreR.rot[1] += 1.2 * f + math.sin(t * 20) * 0.1 * f; J.arm.rot[1] += 0.4 * f; J.head.rot[2] += math.sin(t * 0.37) * 0.25
	end
	if idle == "write" and not ctx.say then CLIPS.write.f(J, t, 1) end
	if idle == "hold" then CLIPS.hold.f(J, t, 1) end
	-- talking: a hand moves with the words, little nods
	if ctx.say then J.foreR.rot[1] += 0.8; J.arm.rot[1] += 0.3; J.head.rot[1] += math.sin(t * 13) * 0.04 end
	-- a gesture now and then, blended in and out
	st.nextClip = st.nextClip or (t + 6 + math.random() * 8)
	if not st.clip and t > st.nextClip and e and e.clips and #e.clips > 0 then
		playClip(n, e.clips[math.random(1, #e.clips)])
		st.nextClip = t + 9 + math.random() * 10
	end
	if st.clip then
		local c = CLIPS[st.clip.name]
		st.clip.t += dt
		local k = math.min(ss(st.clip.t / 0.18), ss((c.len - st.clip.t) / 0.25))
		c.f(J, st.clip.t, k)
		if st.clip.t >= c.len then st.clip = nil end
	end
	-- turning round to you when you're close (the whole body on its spot), the head looking at you (clamped, eased)
	local want = 0
	if ctx.eye and ctx.k > 0.2 then want = clamp(wrapA(yawTo(ctx.rp.X, ctx.rp.Z, ctx.eye.X, ctx.eye.Z) - ctx.yaw), -1.3, 1.3) end
	st.turn = lerp(st.turn or 0, want, math.min(1, dt * 2.2))
	J.root.rot[2] = st.turn
	local ty, tx = 0, 0
	if ctx.eye then
		local hp = worldOf(n, J.head).Position
		ty = clamp(wrapA(yawTo(hp.X, hp.Z, ctx.eye.X, ctx.eye.Z) - ctx.yaw - st.turn), -1.0, 1.0)
		tx = clamp(math.atan2(ctx.eye.Y - hp.Y, math.sqrt((ctx.eye.X - hp.X) ^ 2 + (ctx.eye.Z - hp.Z) ^ 2)), -0.45, 0.45)
	end
	st.ly = lerp(st.ly or 0, ty, math.min(1, dt * (if ctx.eye then 5 else 3)))
	st.lx = lerp(st.lx or 0, tx, math.min(1, dt * (if ctx.eye then 5 else 3)))
	J.head.rot[2] += st.ly
	J.head.rot[1] += st.lx
end

-- ------------------------------------------------------------------ the board of directors (the web's updateCat)
-- one cohesive body, head and tail (lore_cat_meshes.py): breathing, a lazy look round (or at you, close), the tail's
-- slow curl and swish, a flick now and then. Pet (their prompt): a reaction, as on the web
local PET = { "squint", "squint", "blink", "headbutt", "stretch", "roll", "swat" }
local function catRest(n: Npc)
	if n.st.rest then return end
	local r = {}
	for name, j in n.J do r[name] = { pos = table.clone(j.pos), rot = table.clone(j.rot) } end
	n.st.rest = r
end
local function petCat(n: Npc, now: number)
	local pose = n.model:GetAttribute("Pose")
	local k = PET[math.random(1, #PET)]
	if k == "roll" and pose ~= "side" and pose ~= "lie" then k = "headbutt" end
	if k == "stretch" and (pose == "box" or pose == "sit") then k = "blink" end
	n.st.pet = { t = now, k = k, dur = if k == "stretch" then 2.4 elseif k == "roll" then 2.6 elseif k == "swat" then 1.2 else 2.0 }
	say(n, { if k == "swat" then "*swat*" elseif k == "blink" then "*slow blink*" elseif k == "stretch" then "*stretches*" elseif k == "headbutt" then "*headbutts your hand*" else "*purrs*" })
end
local function catUpdate(n: Npc, dt: number, t: number, ctx: any)
	local J, st = n.J, n.st
	if not (J.body and J.neck and J.tailBase) then return end
	catRest(n)
	local R = st.rest
	local now = os.clock()
	local pet = st.pet
	if pet and now - pet.t > pet.dur then pet = nil; st.pet = nil end
	local pk = if pet then (now - pet.t) / pet.dur else 0
	local K = if pet then pet.k else ""
	-- look at you when you're close (a lazy, clamped head turn), otherwise a slow look round
	local wy = math.sin(t * 0.23) * 0.35 + math.sin(t * 0.61) * 0.15
	local wx = math.sin(t * 0.37) * 0.08
	if ctx.eye then
		local np = worldOf(n, J.neck).Position
		local dx, dy, dz = ctx.eye.X - np.X, ctx.eye.Y - np.Y, ctx.eye.Z - np.Z
		local d = math.sqrt(dx * dx + dz * dz)
		if d < 7 * 3.5 then
			wy = clamp(wrapA(math.atan2(-dx, -dz) - ctx.yaw), -1.1, 1.1)
			wx = clamp(math.atan2(dy, d) * 0.8, -0.5, 0.6)
		end
	end
	st.ly = lerp(st.ly or 0, wy, math.min(1, dt * 3))
	st.lx = lerp(st.lx or 0, wx, math.min(1, dt * 3))
	-- body: breathing (a purr's rumble while petted)
	local purr = if pet and K ~= "swat" then (1 - pk) * 0.004 else 0
	J.body.pos[2] = R.body.pos[2] + math.sin(t * 2.6) * 0.003 + (if purr > 0 then (math.random() - 0.5) * purr else 0)
	J.body.rot = { R.body.rot[1], R.body.rot[2], R.body.rot[3] }
	J.neck.rot = { R.neck.rot[1] + st.lx, R.neck.rot[2] + st.ly, R.neck.rot[3] }
	local tailUp, lash = 0, 0
	if K == "squint" or K == "headbutt" then tailUp = bump(pk) end
	if K == "headbutt" then J.neck.rot[1] += bump(math.min(1, pk * 2)) * 0.5 end
	if K == "stretch" then
		local s2 = bump(math.min(1, pk * 1.25))
		J.body.rot[1] -= s2 * 0.38; J.body.pos[2] += s2 * 0.05; J.neck.rot[1] -= s2 * 0.55; tailUp = s2
	end
	if K == "roll" then J.body.rot[3] = lerp(R.body.rot[3], R.body.rot[3] + 1.45, bump(math.min(1, pk * 1.1))) end
	if K == "swat" then lash = bump(math.min(1, pk * 1.4)); J.neck.rot[1] += lash * 0.12 end
	-- the tail: a slow swish, up when happy, lashing when annoyed, a flick every few seconds
	st.flickAt = st.flickAt or (t + 2)
	if t > st.flickAt + 0.5 then st.flickAt = t + 2 + math.random() * 4 end
	local fl = bump((t - st.flickAt) / 0.5)
	J.tailBase.rot = { lerp(R.tailBase.rot[1], 0.35, tailUp) + fl * 0.15, R.tailBase.rot[2], R.tailBase.rot[3] + math.sin(t * (if lash > 0 then 9 else 1.4)) * (if lash > 0 then 0.3 else 0.09) }
end

-- ------------------------------------------------------------------ finding the models
local function adopt(m: Instance, temp: boolean?)
	if not m:IsA("Model") or npcs[m] then return end
	local id = m:GetAttribute("LoreId")
	local rig = type(id) == "string" and Rigs[id]
	if not rig then return end
	local root = if temp then m:FindFirstChild("Root") else m:WaitForChild("Root", 10)
	if not root or not root:IsA("BasePart") then return end
	local J: { [string]: Joint } = {}
	local order: { Joint } = {}
	for _, j in rig.joints do
		local c = j.cf
		local rest = CFrame.new(c[1], c[2], c[3], c[4], c[5], c[6], c[7])
		local jj: Joint = { name = j.name, parent = if j.parent then J[j.parent] else nil, pre = CFrame.identity,
			pos = { j.pos[1], j.pos[2], j.pos[3] }, rot = { j.rot[1], j.rot[2], j.rot[3] }, k = j.k, cf = CFrame.identity }
		jj.pre = if j.parent then rest * local_(jj):Inverse() else CFrame.identity
		J[j.name] = jj
		table.insert(order, jj)
	end
	local base = root.CFrame
	local look = base.LookVector
	local n: Npc = { id = id :: string, model = m, root = root, base = base, yaw = math.atan2(-look.X, -look.Z), J = J,
		order = order, pieces = {}, parts = {}, cfs = {}, st = {}, t0 = math.random() * 20, out = false, home = m.Parent :: Instance,
		bubble = nil, heard = 0, nearSaid = false, live = false,
		clues = {}, shown = temp == true or seen[id :: string] == true, vis = if seen[id :: string] and not temp then 1 else 0, prompt = nil,
		temp = temp == true, born = os.clock(), leaving = false }
	for name, pc in rig.pieces do
		local part = if temp then m:FindFirstChild(name) else m:WaitForChild(name, 10)
		if part and part:IsA("BasePart") and J[pc.joint] then
			table.insert(n.pieces, { part = part, joint = J[pc.joint], off = CFrame.new(pc.at[1], pc.at[2], pc.at[3]) })
			table.insert(if part:GetAttribute("Clue") then n.clues else n.parts, part)
		end
	end
	if temp then -- (a spawn-in's other things, Gary's desk, Dale's machine, fade with it)
		for _, d in m:GetDescendants() do
			if d:IsA("BasePart") and d ~= root and not table.find(n.parts, d) and not table.find(n.clues, d) then table.insert(n.parts, d) end
		end
	end
	local tk = root:FindFirstChild("Talk", true)
	n.prompt = if tk and tk:IsA("ProximityPrompt") then tk else nil
	apply(n)
	npcs[m] = n
	m.Destroying:Connect(function() npcs[m] = nil; if n.bubble then n.bubble.gui:Destroy() end end)
	-- TALK: the next beat
	local pr = root:FindFirstChild("Talk", true)
	if pr and pr:IsA("ProximityPrompt") then
		pr.Triggered:Connect(function()
			local e = Data.get(n.id)
			if not e then return end
			if e.kind == "cat" then petCat(n, os.clock()); return end
			n.heard += 1
			local beat = e.beats[n.heard + 1]
			if not beat then beat = e.again; n.heard = #e.beats end
			say(n, beat)
		end)
	end
end

local function watch(f: Instance)
	for _, m in f:GetChildren() do task.spawn(adopt, m) end
	f.ChildAdded:Connect(function(m) task.spawn(adopt, m) end)
end
task.spawn(function()
	local map = workspace:WaitForChild("Map")
	local f = map:FindFirstChild("Lore")
	while not f do
		map.ChildAdded:Wait()
		f = map:FindFirstChild("Lore")
	end
	watch(f :: Instance)
end)

-- ------------------------------------------------------------------ the code panel's spawn-ins
local function showAt(): CFrame?
	local map = workspace:FindFirstChild("Map")
	local l = map and map:FindFirstChild("Lore")
	local pnl = l and l:FindFirstChild("CodePanel")
	local sp = pnl and pnl:FindFirstChild("Show")
	return if sp and sp:IsA("BasePart") then sp.CFrame else nil
end
local function chime(at: Vector3)
	local ok, Sfx = pcall(require, script.Parent:FindFirstChild("Sfx") :: ModuleScript)
	if ok and Sfx and Sfx.play then pcall(Sfx.play, "card_heal", at, 0.7, 0.9) end
end
-- a model's lowest point (its parts' boxes, not counting a Root)
local function lowest(m: Model): number
	local lo = math.huge
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") and d.Name ~= "Root" and d.Transparency < 1 then
			local cf, sz = d.CFrame, d.Size / 2
			local ext = math.abs(cf.UpVector.Y) * sz.Y + math.abs(cf.RightVector.Y) * sz.X + math.abs(cf.LookVector.Y) * sz.Z
			lo = math.min(lo, d.Position.Y - ext)
		end
	end
	return lo
end
-- strip a copy down to its looks: no prompts, scripts, sounds, lights, collisions or queries
local function looksOnly(m: Model)
	for _, d in m:GetDescendants() do
		if d:IsA("ProximityPrompt") or d:IsA("BaseScript") or d:IsA("Sound") or d:IsA("Light") then d:Destroy()
		elseif d:IsA("BasePart") then d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.LocalTransparencyModifier = 1 end
	end
end
-- a lore NPC: a copy of its model, standing by the panel (sitters lifted so their feet are on the floor), alive like
-- the real one (adopted as a temp NPC: it fades in, greets, talks, and goes after SHOW_LIFE)
local function spawnLore(id: string, at: CFrame)
	local map = workspace:FindFirstChild("Map")
	local l = map and map:FindFirstChild("Lore")
	local src = l and l:FindFirstChild("Lore_" .. id)
	if not src or not src:IsA("Model") then return end
	src.Archivable = true
	local m = src:Clone()
	for _, name in { "MachineBlock", "Zone", "Target" } do -- (Gary keeps his desk, Dale his machine: their things come too)
		local x = m:FindFirstChild(name)
		if x then x:Destroy() end
	end
	looksOnly(m)
	m:SetAttribute("LoreShow", true)
	m:PivotTo(at)
	local lo = lowest(m)
	if lo < at.Y - 0.3 then m:PivotTo(at + Vector3.new(0, at.Y - lo, 0)) end
	m.Parent = showFolder
	adopt(m, true)
end
-- the mannequin and the HR guy: still figures (no rig life), faded in and out here
type Plain = { m: Model, parts: { BasePart }, born: number, vis: number, leaving: boolean, at: Vector3 }
local plains: { Plain } = {}
local function spawnPlain(src: Instance?, at: CFrame)
	if not src or not src:IsA("Model") then return end
	src.Archivable = true
	local m = src:Clone()
	looksOnly(m)
	m:PivotTo(at)
	local lo = lowest(m)
	if math.abs(lo - at.Y) > 0.05 and lo < math.huge then m:PivotTo(m:GetPivot() + Vector3.new(0, at.Y - lo, 0)) end
	m.Parent = showFolder
	local parts = {}
	for _, d in m:GetDescendants() do if d:IsA("BasePart") and d.Transparency < 1 then table.insert(parts, d) end end
	table.insert(plains, { m = m, parts = parts, born = os.clock(), vis = 0, leaving = false, at = at.Position })
end
local function spawnIn(id: string)
	local at = showAt()
	if not at then return end
	for _, n in npcs do if n.temp then n.leaving = true end end -- (one at a time: whoever's there goes)
	for _, pl in plains do pl.leaving = true end
	chime(at.Position + Vector3.new(0, 4, 0))
	if id == "egg" then
		local map = workspace:FindFirstChild("Map")
		local hub = map and map:FindFirstChild("Hub")
		local e = hub and hub:FindFirstChild("HubEgg")
		spawnPlain(e and e:FindFirstChild("Mannequin"), at)
	elseif id == "hr" then
		spawnPlain(game:GetService("ReplicatedStorage"):FindFirstChild("LoreHRShow"), at)
	else
		spawnLore(id, at)
	end
end

-- ------------------------------------------------------------------ the hub egg's mannequin: hidden until its code
local eggHidden: boolean? = nil
local eggModel: Instance? = nil
local function eggApply()
	local map = workspace:FindFirstChild("Map")
	local hub = map and map:FindFirstChild("Hub")
	local e = hub and hub:FindFirstChild("HubEgg")
	local m = e and e:FindFirstChild("Mannequin")
	local hide = not seen.egg
	if m == eggModel and hide == eggHidden then return end
	eggModel, eggHidden = m, hide
	if not e then return end
	for _, d in e:GetDescendants() do
		if d:IsA("BasePart") and m and d:IsDescendantOf(m) then
			d.LocalTransparencyModifier = if hide then 1 else 0
			-- (its collisions off on this screen while hidden: no invisible plinth to bump into)
			if d:GetAttribute("EggCollide") == nil then d:SetAttribute("EggCollide", d.CanCollide) end
			d.CanCollide = if hide then false else d:GetAttribute("EggCollide") == true
		elseif d:IsA("ProximityPrompt") then d.Enabled = not hide
		elseif d:IsA("Light") then d.Enabled = not hide
		elseif d:IsA("Highlight") then d.Enabled = not hide end
	end
end
task.spawn(function()
	while true do
		pcall(eggApply)
		task.wait(1)
	end
end)

me:GetAttributeChangedSignal("LoreSeen"):Connect(function()
	readSeen()
	pcall(eggApply)
	for _, n in npcs do
		if n.temp then continue end
		local want = seen[n.id] == true
		if want ~= n.shown then
			n.shown = want
			if not want then n.vis = 0; n.nearSaid = false end
			apply(n)
		end
	end
end)

LoreR.OnClientEvent:Connect(function(op: string, id: string, first: boolean)
	if op == "seen" then
		-- a code at the panel: it spawns in there. (otherwise: a soft chime where they stand as they fade in)
		if (first :: any) == "code" then spawnIn(id); return end
		for _, n in npcs do
			if n.id == id and not n.temp then chime(n.base.Position + Vector3.new(0, 4, 0)) end
		end
		return
	end
	if op ~= "found" then return end
	for _, n in npcs do
		if n.id == id then
			local e = Data.get(id)
			if e then
				-- the opening (if they haven't said it yet), then the gift line
				local lines = {}
				if not n.nearSaid and e.beats[1] then for _, l in e.beats[1] do table.insert(lines, l) end; n.nearSaid = true; n.heard = math.max(n.heard, 0) end
				for _, l in (if first then e.got else e.again) do table.insert(lines, l) end
				say(n, lines)
			end
		end
	end
end)

-- ------------------------------------------------------------------ every frame
local function myEye(): Vector3?
	local ch = me.Character
	local h = ch and ch:FindFirstChild("Head")
	if h and h:IsA("BasePart") then return h.Position + Vector3.new(0, 0.4, 0) end
	local cam = workspace.CurrentCamera
	return cam and cam.CFrame.Position
end

RunService.RenderStepped:Connect(function(dt)
	dt = math.min(dt, 0.1)
	local cam = workspace.CurrentCamera
	local camPos = cam and cam.CFrame.Position or Vector3.zero
	local eye = myEye()
	local now = os.clock()
	local parts, cfs = {}, {}
	for m, n in npcs do
		local rp = n.base.Position
		local dCam = (camPos - rp).Magnitude
		-- far: not drawn on this client (and drawn again when near). hidden in place, never moved out of Map.Lore: ZoneCull
		-- measures the folder by what's in it, and a folder that shrank to the nearby ones once counted as far away
		if (dCam > HIDE) ~= n.out then
			n.out = dCam > HIDE
			apply(n)
		end
		-- (a spawn-in you went far from before it left: gone)
		if n.temp and n.out and now - n.born > SHOW_LIFE then task.defer(function() m:Destroy() end); continue end
		if n.out or not m:IsDescendantOf(workspace) then continue end
		-- not revealed: only the clue is here (no bubble, no moves). revealed just now: fading in
		if not n.shown then continue end
		if n.temp and not n.leaving and (now - n.born > SHOW_LIFE or (eye and (eye - rp).Magnitude > SHOW_FAR)) then n.leaving = true end
		if n.leaving then
			n.vis = math.max(0, n.vis - dt / FADE)
			apply(n)
			if n.vis <= 0 then task.defer(function() m:Destroy() end); continue end
		elseif n.vis < 1 then
			n.vis = math.min(1, n.vis + dt / FADE)
			apply(n)
		end
		local d = if eye then Vector3.new(eye.X - rp.X, 0, eye.Z - rp.Z).Magnitude else 1e9
		-- the opening beat, once per approach
		if d < SAY_NEAR and not n.nearSaid then
			local e = Data.get(n.id)
			if e and e.beats[1] then
				say(n, e.beats[1]); n.nearSaid = true; n.heard = 0
				if e.greet then playClip(n, e.greet) end
			end
		elseif d > SAY_RESET and n.nearSaid then
			n.nearSaid = false
		end
		stepBubble(n, dt, now)
		if dCam > LIVE then continue end
		local dm = d / 3 -- the web's metres
		local ctx = {
			eye = if eye and dm < 12 then eye else nil,
			k = clamp(1 - (dm - 2.2) / 4, 0, 1),
			say = n.bubble ~= nil and n.bubble.typing,
			rp = rp, yaw = n.yaw,
		}
		local up = UPDATE[n.id]
		if up then up(n, dt, now + n.t0, ctx) elseif n.J.tailBase then catUpdate(n, dt, now + n.t0, ctx) elseif n.J.spine then castUpdate(n, dt, now + n.t0, ctx) end
		solve(n)
		for _, pc in n.pieces do
			table.insert(parts, pc.part)
			table.insert(cfs, n.base * pc.joint.cf * pc.off)
		end
	end
	if #parts > 0 then workspace:BulkMoveTo(parts, cfs, Enum.BulkMoveMode.FireCFrameChanged) end
	-- the still spawn-ins (the mannequin, the HR guy): in, a while, out
	for i = #plains, 1, -1 do
		local pl = plains[i]
		if not pl.leaving and (now - pl.born > SHOW_LIFE or (eye and (eye - pl.at).Magnitude > SHOW_FAR)) then pl.leaving = true end
		local was = pl.vis
		pl.vis = if pl.leaving then math.max(0, pl.vis - dt / FADE) else math.min(1, pl.vis + dt / FADE)
		if pl.vis ~= was then for _, p in pl.parts do p.LocalTransparencyModifier = 1 - pl.vis end end
		if pl.leaving and pl.vis <= 0 then pl.m:Destroy(); table.remove(plains, i) end
	end
end)
