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
-- NOT IN THE WORLD UNTIL ITS CODE (18 Nov 2026, the owner: "can you remove the jankfire npcs? when you type in the codes
-- you'll get a cutscene where an npc walks in and then they'll appear somewhere!"). The server keeps every NPC's model
-- (and the hub egg's mannequin) in ServerStorage.JankfireLore and gives you a copy of each one YOU have revealed, in
-- PlayerGui.LoreDelivery (a hidden ScreenGui: only you get what's in your PlayerGui). Each is cloned here into
-- workspace.LoreLocal at its own spot (this screen only) and lives as before. Nothing else is in the map.
-- A right code at the panel (remote Lore "seen", how = "code") plays a short cutscene on your screen alone (startCut):
-- your controls and the HUD go, black bars, the camera cuts to the panel; the NPC walks in (its legs on a procedural
-- walk; the sitters stand up for it), turns to you, greets you and says its lines, then turns toward where it lives
-- and walks off as it fades (the hint: no text). SKIP (Space, B, or the button) after the first second. Never in a
-- match. Then it's at its own spot, for you to go and find.
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
local CUT_WALK, CUT_BEAT, CUT_LEAVE, CUT_SKIP = 3.2, 2.8, 1.5, 1.2 -- the cutscene's parts (s), and when SKIP shows
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
	temp: boolean, born: number, leaving: boolean, cut: boolean?, walk: number?,
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

-- ------------------------------------------------------------------ your NPCs: only the ones you've revealed exist here
local localFolder = Instance.new("Folder") -- (this screen's NPCs at their spots)
localFolder.Name = "LoreLocal"
localFolder.Parent = workspace
local cutFolder = Instance.new("Folder") -- (the cutscene's actor)
cutFolder.Name = "LoreCut"
cutFolder.Parent = workspace
local placed: { [string]: Model } = {}
local function place(src: Instance)
	if not src:IsA("Model") then return end
	local id = src:GetAttribute("LoreId")
	if type(id) ~= "string" or placed[id] then return end
	-- (its pieces may still be arriving)
	local rig = Rigs[id]
	if rig then for name in rig.pieces do src:WaitForChild(name, 5) end else task.wait(0.3) end
	if not src.Parent or placed[id] then return end
	src.Archivable = true
	if not Data.PLACE_IN_WORLD then
		-- (out of the world: only its cutscene uses it, cloned from this hidden copy)
		placed[id] = src :: Model
		src.Destroying:Connect(function() if placed[id] == src then placed[id] = nil end end)
		return
	end
	local m = src:Clone()
	for _, d in m:GetDescendants() do if d:IsA("BaseScript") then d:Destroy() end end
	m.Parent = localFolder
	placed[id] = m
	if rig then adopt(m) end
	src.Destroying:Connect(function()
		if placed[id] == m then placed[id] = nil end
		m:Destroy()
	end)
end
task.spawn(function()
	local pg = me:WaitForChild("PlayerGui")
	local box = pg:FindFirstChild("LoreDelivery")
	while not box do
		pg.ChildAdded:Wait()
		box = pg:FindFirstChild("LoreDelivery")
	end
	for _, c in (box :: Instance):GetChildren() do task.spawn(place, c) end
	;(box :: Instance).ChildAdded:Connect(function(c) task.spawn(place, c) end)
end)

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
-- a walk, on any rig's legs (every one has legL / legR / kneeL / kneeR): thighs swing, the back knee bends; the
-- story cast's arms swing against them. phase 0 = standing straight (the sitters stand up for it)
local function walkPose(n: Npc)
	local J, ph = n.J, n.walk or 0
	local s = math.sin(ph)
	if J.legL then J.legL.rot = { 0.42 * s, 0, 0 } end
	if J.legR then J.legR.rot = { -0.42 * s, 0, 0 } end
	if J.kneeL then J.kneeL.rot = { -0.6 * math.max(0, -s), 0, 0 } end
	if J.kneeR then J.kneeR.rot = { -0.6 * math.max(0, s), 0, 0 } end
	if J.spine and J.arm and J.armL then
		J.arm.rot[1] += 0.28 * s
		J.armL.rot[1] -= 0.28 * s
	end
end

-- ------------------------------------------------------------------ a right code's cutscene (your screen only)
local ContextActionService = game:GetService("ContextActionService")
local Th = require(script.Parent:WaitForChild("Theme")) :: any
local cut: any = nil
local cutUi: any = nil
local hiddenGuis: { [ScreenGui]: boolean } = {}
local hiddenBoards: { [BillboardGui]: boolean } = {} -- (nametags and titles over heads, off while it runs)
local hiddenNames: { [Humanoid]: Enum.HumanoidDisplayDistanceType } = {}
local rayP = RaycastParams.new()
rayP.FilterType = Enum.RaycastFilterType.Exclude
local endCut: () -> ()
local function controls(on: boolean)
	pcall(function()
		local c = require(me:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: any):GetControls()
		if on then c:Enable() else c:Disable() end
	end)
end
local function ui(): any
	if cutUi and cutUi.g.Parent then return cutUi end
	local g = Instance.new("ScreenGui")
	g.Name = "JankLoreCut"; g.ResetOnSpawn = false; g.IgnoreGuiInset = true; g.DisplayOrder = 80; g.Enabled = false
	g.Parent = me:WaitForChild("PlayerGui")
	local top = Instance.new("Frame")
	top.Name = "BarTop"; top.BackgroundColor3 = Color3.new(0, 0, 0); top.BorderSizePixel = 0; top.Size = UDim2.new(1, 0, 0, 0)
	top.Parent = g
	local bot = top:Clone()
	bot.Name = "BarBot"; bot.AnchorPoint = Vector2.new(0, 1); bot.Position = UDim2.fromScale(0, 1); bot.Parent = g
	local sc = Th.scaled(g)
	local skip = Th.new("TextButton", { Name = "Skip", AutoButtonColor = false, BackgroundColor3 = Th.BG, BackgroundTransparency = Th.BG_A, BorderSizePixel = 0,
		AnchorPoint = Vector2.new(1, 1), Position = UDim2.new(1, -28, 1, -14), Size = UDim2.fromOffset(132, 36), FontFace = Th.FONT_BOLD, TextSize = 13,
		Text = "SKIP", TextColor3 = Th.TEXT, TextXAlignment = Enum.TextXAlignment.Left, Visible = false, ZIndex = 4 }, sc)
	Th.corner(skip); Th.edge(skip)
	Th.new("UIPadding", { PaddingLeft = UDim.new(0, 66) }, skip)
	local key = Th.key(skip, "", UDim2.fromOffset(-58, 7))
	key.Size = UDim2.fromOffset(50, 22)
	local kt = key:FindFirstChild("Letter")
	if kt and kt:IsA("TextLabel") then kt.Text = "SPACE"; kt.TextSize = 10 end
	skip.Activated:Connect(function() if cut and os.clock() - cut.t0 > CUT_SKIP then endCut() end end)
	cutUi = { g = g, top = top, bot = bot, skip = skip }
	return cutUi
end
-- the code panel nearest you (the hubs' are tagged CodePanel; the ring's is Map.Lore.CodePanel)
local function panelModel(): Model?
	local list = {}
	for _, m in game:GetService("CollectionService"):GetTagged("CodePanel") do
		if m:IsA("Model") and m:IsDescendantOf(workspace) then table.insert(list, m) end
	end
	local map = workspace:FindFirstChild("Map")
	local l = map and map:FindFirstChild("Lore")
	local old = l and l:FindFirstChild("CodePanel")
	if old and old:IsA("Model") and not table.find(list, old) then table.insert(list, old) end
	local ch = me.Character
	local r = ch and ch:FindFirstChild("HumanoidRootPart")
	local best, bd = nil, math.huge
	for _, m in list do
		local d = if r and r:IsA("BasePart") then (m:GetPivot().Position - r.Position).Magnitude else 0
		if d < bd then best, bd = m, d end
	end
	return best
end
local function flat(v: Vector3, fallback: Vector3): Vector3
	local f = Vector3.new(v.X, 0, v.Z)
	return if f.Magnitude > 1e-3 then f.Unit else fallback
end

endCut = function()
	local c = cut
	if not c then return end
	cut = nil
	pcall(function() RunService:UnbindFromRenderStep("JankLoreCut") end)
	pcall(function() ContextActionService:UnbindAction("JankLoreSkip") end)
	if c.actor and c.actor.m then c.actor.m:Destroy() end
	for g in hiddenGuis do if g.Parent then g.Enabled = true end end
	table.clear(hiddenGuis)
	for b in hiddenBoards do if b.Parent then b.Enabled = true end end
	table.clear(hiddenBoards)
	for h, t in hiddenNames do if h.Parent then h.DisplayDistanceType = t end end
	table.clear(hiddenNames)
	if cutUi then cutUi.g.Enabled = false; cutUi.skip.Visible = false end
	local cam = workspace.CurrentCamera
	cam.CameraType = Enum.CameraType.Custom
	cam.FieldOfView = c.fov
	-- (always down, never the value saved at the start: the code screen was still closing then, so it read true. a
	-- menu that's really still up has MenuCursor put it straight back. 18 Nov: the owner's hub buttons stayed dead)
	me:SetAttribute("LoadoutOpen", false)
	if me:GetAttribute("Finishing") == "lore" then me:SetAttribute("Finishing", nil) end
	controls(true)
end

local function stepCut(dt: number)
	local c = cut
	if not c then return end
	local t = os.clock() - c.t0
	-- (Studio photos: the player attribute LoreCutHold = seconds holds the cutscene at that moment)
	local hold = me:GetAttribute("LoreCutHold")
	if type(hold) == "number" and RunService:IsStudio() then t = hold; c.t0 = os.clock() - hold end
	local T1, T2, T3 = CUT_WALK, CUT_WALK + CUT_BEAT, CUT_WALK + CUT_BEAT + CUT_LEAVE
	if t >= T3 then endCut(); return end
	local a = c.actor
	local head: Vector3
	if a.kind == "still" then
		-- the mannequin fades in where it stands; the HR guy is a step closer every time you blink (cut), and simply
		-- isn't there at the end
		local pos, look, vis
		if c.id == "hr" then
			local k = if t >= T1 then 1 else math.floor(t / (T1 / 3)) / 3
			pos = c.start:Lerp(c.finish, k); look = flat(c.finish - c.start, c.face)
			if t >= T1 then look = c.face end
			vis = if t < T2 then 1 else 0
		else
			pos = c.finish; look = c.face
			vis = if t < T2 then math.min(1, t / 1.2) else math.max(0, 1 - (t - T2) / CUT_LEAVE)
		end
		a.m:PivotTo(CFrame.lookAt(pos, pos + look) + Vector3.new(0, a.lift, 0))
		for _, pt in a.parts do pt.LocalTransparencyModifier = 1 - vis end
		head = pos + Vector3.new(0, a.lift + a.height * 0.82, 0)
	else
		local n = a.n
		local pos, look, vis, moving
		if t < T1 then
			local k = t / T1
			pos = c.start:Lerp(c.finish, 1 - (1 - k) * (1 - k)); look = flat(c.finish - c.start, c.face)
			moving = 1 - k * 0.6; vis = math.min(1, t / 0.6)
		elseif t < T2 then
			pos = c.finish; look = flat(c.camB - c.finish, c.face); moving = nil; vis = 1
		else
			local k = (t - T2) / CUT_LEAVE
			pos = c.finish + c.exit * (k * (c.exitRun or 5.5)); look = c.exit; moving = 1; vis = math.max(0, 1 - k * 1.25)
		end
		c.look = if c.look then flat(c.look:Lerp(look, math.min(1, dt * 7)), look) else look
		if moving then n.walk = (n.walk or 0) + dt * 8.5 * moving else n.walk = 0 end
		local bob = if moving then math.abs(math.sin(n.walk :: number)) * 0.14 else 0
		n.base = CFrame.lookAt(pos, pos + c.look) + Vector3.new(0, a.lift + bob, 0)
		n.yaw = math.atan2(-c.look.X, -c.look.Z)
		if n.vis ~= vis then n.vis = vis; apply(n) end
		head = if n.J.head then worldOf(n, n.J.head).Position + Vector3.new(0, 0.6, 0) else n.base.Position + Vector3.new(0, 4.5, 0)
		-- the beat: they've arrived, they greet you and say their piece
		if t >= T1 and not c.said then
			c.said = true
			local e = Data.get(c.id)
			if e then
				local lines = {}
				if e.beats[1] and e.beats[1][1] then table.insert(lines, e.beats[1][1]) end
				local more = if c.again then e.again else e.got
				if more and more[1] then table.insert(lines, more[1]) end
				say(n, lines)
				if e.greet then playClip(n, e.greet) end
			end
		end
	end
	-- the camera: three set-ups, cut between (the aim eases toward the head within a shot)
	local shot = if t < T1 then 1 elseif t < T2 then 2 else 3
	local at = if shot == 1 then c.camA elseif shot == 2 then c.camB else c.camC
	if shot ~= c.shot then c.shot = shot; c.aim = head end
	c.aim = (c.aim :: Vector3):Lerp(head, math.min(1, dt * 5))
	local cam = workspace.CurrentCamera
	cam.CameraType = Enum.CameraType.Scriptable
	cam.CFrame = CFrame.lookAt(at, c.aim)
	local u = cutUi
	if u then
		local bar = math.min(1, t / 0.35) * 0.11
		if t > T3 - 0.35 then bar = math.max(0, (T3 - t) / 0.35) * 0.11 end
		u.top.Size = UDim2.fromScale(1, bar); u.bot.Size = UDim2.fromScale(1, bar)
		if t > CUT_SKIP and not u.skip.Visible then u.skip.Visible = true end
	end
end

-- id: whose code it was; again: a code you'd used before (their "again" line)
local function startCut(id: string, again: boolean?)
	if cut then endCut() end
	local z = me:GetAttribute("Zone")
	if z == "match" or z == "staging" then return end
	local pm = panelModel()
	local sp = pm and pm:FindFirstChild("Show")
	if not pm or not sp or not sp:IsA("BasePart") then return end
	local finish = sp.Position
	local face = flat(sp.CFrame.LookVector, Vector3.zAxis) -- (toward where you stand at the panel)
	local pc = pm:GetPivot().Position
	local away = flat(finish - pc, -face) -- (the panel's far side: they come from there)
	rayP.FilterDescendantsInstances = { me.Character :: Instance, localFolder, cutFolder }
	-- the way in: the longest clear, floored run (up to 16 studs) among directions round the panel's far side, never
	-- from the camera's side
	-- (body-wide, and against every visible part's box near the panel: imported meshes with queries off, like the
	-- arcade's piers, are missed by rays. a body-sized box steps out along the way in half studs till it touches one)
	local boxes: { { Vector3 } } = {}
	local map = workspace:FindFirstChild("Map")
	-- (the panel's own hub: Map.Hub.<Square|Concourse|Atrium> for theirs, Map.Hub for the ring's)
	local hubF = map and map:FindFirstChild("Hub")
	local scanRoot: Instance? = hubF
	if hubF and pm:IsDescendantOf(hubF) then
		local a: Instance = pm
		while a.Parent and a.Parent ~= hubF do a = a.Parent :: Instance end
		scanRoot = a
	end
	for _, root in { scanRoot, pm } do
		if not root then continue end
		for _, p in (root :: Instance):GetDescendants() do
			if p:IsA("BasePart") and p.Transparency < 1 and (p.Position - finish).Magnitude < 40 then
				local cf, sz = p.CFrame, p.Size / 2
				local ex = Vector3.new(
					math.abs(cf.RightVector.X) * sz.X + math.abs(cf.UpVector.X) * sz.Y + math.abs(cf.LookVector.X) * sz.Z,
					math.abs(cf.RightVector.Y) * sz.X + math.abs(cf.UpVector.Y) * sz.Y + math.abs(cf.LookVector.Y) * sz.Z,
					math.abs(cf.RightVector.Z) * sz.X + math.abs(cf.UpVector.Z) * sz.Y + math.abs(cf.LookVector.Z) * sz.Z)
				if p.Position.Y + ex.Y > finish.Y + 0.3 then table.insert(boxes, { p.Position - ex, p.Position + ex }) end
			end
		end
	end
	local function bodyHits(at: Vector3): boolean
		local lo, hi = at + Vector3.new(-1.3, 0.3, -1.3), at + Vector3.new(1.3, 6, 1.3)
		for _, b in boxes do
			if b[1].X < hi.X and b[2].X > lo.X and b[1].Y < hi.Y and b[2].Y > lo.Y and b[1].Z < hi.Z and b[2].Z > lo.Z then return true end
		end
		return false
	end
	local function clearRun(dir: Vector3, maxRun: number): number
		local d = 0.5
		while d <= maxRun do
			if bodyHits(finish + dir * d) then return math.max(0, d - 1) end
			d += 0.5
		end
		return maxRun
	end
	local best, bestDir = 0, away
	for _, deg in { 0, 30, -30, 60, -60, 90, -90, 120, -120 } do
		local dir = (CFrame.Angles(0, math.rad(deg), 0) * away)
		if dir:Dot(face) > 0.55 then continue end
		local run = clearRun(dir, 16)
		-- (floor all the way: step back from the far end till there is)
		while run > 3 do
			local p = finish + dir * run
			local fl = workspace:Raycast(p + Vector3.new(0, 4, 0), Vector3.new(0, -8, 0), rayP)
			if fl and math.abs(fl.Position.Y - finish.Y) < 1.5 then break end
			run -= 2
		end
		if run > best + 0.5 then best, bestDir = run, dir end
	end
	local start = finish + bestDir * math.max(4, best)
	-- after: off toward where they live (the last shot's only hint)
	local home = placed[id]
	local exit = if home then flat(home:GetPivot().Position - finish, -face) else -face
	local actor: any
	if id == "egg" or id == "hr" then
		local src = if id == "egg" then placed.egg else ReplicatedStorage:FindFirstChild("LoreHRShow")
		if not src or not src:IsA("Model") then return end
		src.Archivable = true
		local m = src:Clone()
		looksOnly(m)
		m:PivotTo(CFrame.lookAt(finish, finish + face))
		local lo = lowest(m)
		local cf, size = m:GetBoundingBox()
		m.Parent = cutFolder
		local parts = {}
		for _, d in m:GetDescendants() do if d:IsA("BasePart") and d.Transparency < 1 then table.insert(parts, d) end end
		actor = { kind = "still", m = m, parts = parts, lift = if lo < math.huge then finish.Y - lo else 0, height = size.Y }
		local _ = cf
	else
		local src = placed[id]
		if not src then return end
		local m = src:Clone()
		-- (only the person walks in: their desk, chair, machine and the things on their spot stay home)
		for _, name in { "Desk", "MachineBlock", "Zone", "Target", id .. "_machine", id .. "_door", id .. "_npc", id .. "_turn" } do
			local x = m:FindFirstChild(name)
			if x then x:Destroy() end
		end
		looksOnly(m)
		m:PivotTo(CFrame.lookAt(start, finish))
		m.Parent = cutFolder
		adopt(m, true)
		local n = npcs[m]
		if not n then m:Destroy(); return end
		n.cut = true; n.walk = 0; n.vis = 0; n.nearSaid = true
		apply(n)
		-- feet on the floor in the walking pose (a sitter's root is at its seat)
		walkPose(n); solve(n)
		local lo = math.huge
		for _, pcc in n.pieces do
			local j = pcc.joint.name
			if j == "kneeL" or j == "kneeR" or j == "legL" or j == "legR" then
				local cf = pcc.joint.cf * pcc.off
				local sz = pcc.part.Size / 2
				local ext = math.abs(cf.UpVector.Y) * sz.Y + math.abs(cf.RightVector.Y) * sz.X + math.abs(cf.LookVector.Y) * sz.Z
				lo = math.min(lo, cf.Position.Y - ext)
			end
		end
		local lift = if lo < math.huge then -lo else 0
		local hh = if n.J.head then n.J.head.cf.Position.Y + lift else 5
		actor = { kind = "rig", m = m, n = n, lift = lift, height = hh }
	end
	local hgt = if actor.kind == "rig" then actor.height else actor.height * 0.82
	-- (a tight corner: a camera set-up behind a wall comes in to just this side of it)
	local tgt = finish + Vector3.new(0, math.max(3, hgt * 0.8), 0)
	local function clampCam(p: Vector3): Vector3
		local d = p - tgt
		local h = workspace:Raycast(tgt, d, rayP)
		return if h then h.Position - d.Unit * 0.8 else p
	end
	-- (each set-up: a spot with 3 studs of room round it from every visible part's box, and a clear line to each point
	-- it watches, found by turning round what it watches from the wanted spot; else the wanted spot pulled in)
	local function room(p: Vector3): number
		local best = math.huge
		for _, b in boxes do
			local dx = math.max(b[1].X - p.X, 0, p.X - b[2].X)
			local dy = math.max(b[1].Y - p.Y, 0, p.Y - b[2].Y)
			local dz = math.max(b[1].Z - p.Z, 0, p.Z - b[2].Z)
			best = math.min(best, dx * dx + dy * dy + dz * dz)
		end
		return math.sqrt(best)
	end
	local function lineClear(a: Vector3, b: Vector3): boolean
		local d = b - a
		local n = math.max(1, math.floor(d.Magnitude / 0.5))
		for i = 1, n - 1 do
			local p = a + d * (i / n)
			for _, bx in boxes do
				if p.X > bx[1].X - 0.3 and p.X < bx[2].X + 0.3 and p.Y > bx[1].Y - 0.3 and p.Y < bx[2].Y + 0.3
					and p.Z > bx[1].Z - 0.3 and p.Z < bx[2].Z + 0.3 then return false end
			end
		end
		return true
	end
	local function pickCam(want: Vector3, watch: { Vector3 }): Vector3
		local centre = watch[1]
		local fl = Vector3.new(want.X - centre.X, 0, want.Z - centre.Z)
		local dist0, up = fl.Magnitude, want.Y - centre.Y
		fl = if dist0 > 1e-3 then fl.Unit else face
		-- (the best by score: every line clear first, then room up to 3 studs; the first found wins a tie)
		local best, bestScore = nil, -1
		for _, deg in { 0, 20, -20, 40, -40, 60, -60, 80, -80, 100, -100, 130, -130 } do
			local dir = CFrame.Angles(0, math.rad(deg), 0) * fl
			for _, k in { 1, 0.85, 1.2, 0.7 } do
				local p = centre + dir * (dist0 * k) + Vector3.new(0, up, 0)
				local r = room(p)
				if r < 0.8 then continue end
				local clearN = 0
				for _, w in watch do if lineClear(p, w) then clearN += 1 end end
				local score = clearN * 10 + math.min(r, 3)
				if score > bestScore + 1e-3 then best, bestScore = p, score end
				if clearN == #watch and r >= 3 then return p end
			end
		end
		return best or clampCam(want)
	end
	local exitRun = clearRun(exit, 5.5)
	local headUp = Vector3.new(0, math.max(3, hgt * 0.6), 0) -- (chest height: clear of hanging lamps)
	local cam = workspace.CurrentCamera
	cut = {
		id = id, again = again, t0 = os.clock(), actor = actor, start = start, finish = finish, face = face, exit = exit,
		exitRun = exitRun,
		camA = pickCam(finish + face * 13 - away * 4 + Vector3.new(0, 5.5, 0), { (start + finish) / 2 + headUp, start + headUp, finish + headUp }),
		camB = pickCam(finish + face * 7.5 + away * 1.8 + Vector3.new(0, math.max(3, hgt * 0.9), 0), { finish + headUp }),
		camC = pickCam(finish + face * 10 - exit * 3 + Vector3.new(0, 6, 0), { finish + exit * (exitRun / 2) + headUp, finish + headUp }),
		fov = cam.FieldOfView, loadoutWas = me:GetAttribute("LoadoutOpen"), said = false, shot = 0, aim = nil, look = nil,
	}
	local okSetup, errSetup = pcall(function()
		local u = ui()
		for _, g in me:WaitForChild("PlayerGui"):GetChildren() do
			if g:IsA("ScreenGui") and g ~= u.g and g.Enabled and g.Name ~= "LoreDelivery" then hiddenGuis[g] = true; g.Enabled = false end
		end
		u.g.Enabled = true
		for _, root in { workspace, me:WaitForChild("PlayerGui") } do
			for _, d in (root :: Instance):GetDescendants() do
				if d:IsA("BillboardGui") and d.Enabled and d.Name ~= "LoreBubble" and not d:IsDescendantOf(cutFolder) then
					hiddenBoards[d] = true; d.Enabled = false
				end
			end
		end
		for _, pl in Players:GetPlayers() do
			local hum = pl.Character and pl.Character:FindFirstChildOfClass("Humanoid")
			if hum and hum.DisplayDistanceType ~= Enum.HumanoidDisplayDistanceType.None then
				hiddenNames[hum] = hum.DisplayDistanceType
				hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
			end
		end
		me:SetAttribute("LoadoutOpen", true) -- (hands and guns hold still, no menu opens, the shoulder camera lets go)
		me:SetAttribute("Finishing", "lore") -- (MenuCursor, PadLook and the death camera treat it like a finisher)
		controls(false)
		cam.FieldOfView = 50
		chime(finish + Vector3.new(0, 4, 0))
		ContextActionService:BindActionAtPriority("JankLoreSkip", function(_, state)
			if state == Enum.UserInputState.Begin and cut and os.clock() - cut.t0 > CUT_SKIP then endCut() end
			return Enum.ContextActionResult.Sink
		end, false, 3600, Enum.KeyCode.Space, Enum.KeyCode.ButtonB)
		RunService:BindToRenderStep("JankLoreCut", Enum.RenderPriority.Last.Value + 70, function(dt: number)
			local ok, err = pcall(stepCut, dt)
			if not ok then warn("[jankfire] lore cutscene: " .. tostring(err)); endCut() end
		end)
	end)
	if not okSetup then
		warn("[jankfire] lore cutscene setup: " .. tostring(errSetup))
		endCut()
	end
end
me.CharacterAdded:Connect(function() if cut then endCut() end end)
me:GetAttributeChangedSignal("Zone"):Connect(function()
	local z = me:GetAttribute("Zone")
	if cut and (z == "match" or z == "staging") then endCut() end
end)

-- ------------------------------------------------------------------ the hub egg's prompt and lamp: off until its code
-- and the nook's door: every part named EggNookDoor (the hub's own in Map.Hub, or LoreSpots' stand-in in Map.Lore) is a
-- solid finished panel over the nook's opening for everyone, and only opens (hidden, no collisions, on this screen
-- alone) for a player who has entered JANK, while the NPCs are placed in the world at all (LoreData.PLACE_IN_WORLD)
local eggHidden: boolean? = nil
local function doors(map: Instance?): { BasePart }
	local out = {}
	if not map then return out end
	for _, d in map:GetDescendants() do
		if d.Name == "EggNookDoor" then
			if d:IsA("BasePart") then table.insert(out, d) end
			for _, p in d:GetDescendants() do if p:IsA("BasePart") then table.insert(out, p) end end
		end
	end
	return out
end
local function eggApply()
	local map = workspace:FindFirstChild("Map")
	local hub = map and map:FindFirstChild("Hub")
	local e = hub and hub:FindFirstChild("HubEgg")
	local hide = not seen.egg or not Data.PLACE_IN_WORLD
	if hide == eggHidden then return end
	eggHidden = hide
	for _, p in doors(map) do
		if p:GetAttribute("DoorCollide") == nil then p:SetAttribute("DoorCollide", p.CanCollide) end
		p.LocalTransparencyModifier = if hide then 0 else 1
		p.CanCollide = if hide then p:GetAttribute("DoorCollide") == true else false
	end
	if not e then return end
	for _, d in e:GetDescendants() do
		if d:IsA("ProximityPrompt") then d.Enabled = not hide
		elseif d:IsA("Light") then d.Enabled = not hide
		elseif d:IsA("Highlight") then d.Enabled = not hide end
	end
end
task.spawn(function()
	while true do
		eggHidden = nil -- (look again: the hub may have been rebuilt)
		pcall(eggApply)
		-- (a cutscene's flag with no cutscene: put right, controls back)
		if not cut and me:GetAttribute("Finishing") == "lore" then
			me:SetAttribute("Finishing", nil)
			me:SetAttribute("LoadoutOpen", false)
			controls(true)
		end
		task.wait(3)
	end
end)

me:GetAttributeChangedSignal("LoreSeen"):Connect(function()
	readSeen()
	eggHidden = nil
	pcall(eggApply)
	for _, n in npcs do
		if n.cut then continue end
		local want = seen[n.id] == true
		if want ~= n.shown then
			n.shown = want
			if not want then n.vis = 0; n.nearSaid = false end
			apply(n)
		end
	end
end)

LoreR.OnClientEvent:Connect(function(op: string, id: string, first: any)
	if op == "seen" then
		-- a code at the panel: its cutscene (once its copy has reached you). otherwise a soft chime where they stand
		if first == "code" or first == "again" then
			task.spawn(function()
				local t0 = os.clock()
				while id ~= "hr" and not placed[id] and os.clock() - t0 < 4 do task.wait(0.1) end
				startCut(id, first == "again")
			end)
			return
		end
		for _, n in npcs do
			if n.id == id and not n.cut then chime(n.base.Position + Vector3.new(0, 4, 0)) end
		end
		return
	end
	if op ~= "found" then return end
	for _, n in npcs do
		if n.id == id and not n.cut then
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
	local myE = myEye()
	local now = os.clock()
	local parts, cfs = {}, {}
	for m, n in npcs do
		local rp = n.base.Position
		local dCam = (camPos - rp).Magnitude
		-- far: not drawn on this client (and drawn again when near), hidden in place
		if (dCam > HIDE) ~= n.out then
			n.out = dCam > HIDE
			apply(n)
		end
		if n.out or not m:IsDescendantOf(workspace) then continue end
		if not n.shown then continue end
		if not n.cut and n.vis < 1 then
			n.vis = math.min(1, n.vis + dt / FADE)
			apply(n)
		end
		-- (the cutscene's actor looks at the camera)
		local eye = if n.cut then camPos else myE
		local d = if eye then Vector3.new(eye.X - rp.X, 0, eye.Z - rp.Z).Magnitude else 1e9
		-- the opening beat, once per approach
		if not n.cut then
			if d < SAY_NEAR and not n.nearSaid then
				local e = Data.get(n.id)
				if e and e.beats[1] then
					say(n, e.beats[1]); n.nearSaid = true; n.heard = 0
					if e.greet then playClip(n, e.greet) end
				end
			elseif d > SAY_RESET and n.nearSaid then
				n.nearSaid = false
			end
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
		if n.walk then walkPose(n) end
		solve(n)
		for _, pc in n.pieces do
			table.insert(parts, pc.part)
			table.insert(cfs, n.base * pc.joint.cf * pc.off)
		end
	end
	if #parts > 0 then workspace:BulkMoveTo(parts, cfs, Enum.BulkMoveMode.FireCFrameChanged) end
end)
