--!strict
-- the hub's regulars, on your own screen.
-- a dot after a regular's name while something waits for you there. HubNPCs (server) tags the label's TextLabel
-- "RegularBadge" with Base (its text) and BadgeFlag (one of your player attributes: Dune's is QuestNews, which the
-- quests server sets when today's quests or a finished one are new to you and clears when you open the QUESTS screen).
-- while that attribute is true for you, the label shows an amber dot.
-- their clips, played here: the server only moves their bodies (tagged "HubRegular") and says what they are doing in
-- the body's attributes (HubNPCs.server's header). played by the server, a clip would be lost here once ZoneCull had
-- taken the Rotunda out of your world and brought it back; played here, everything starts again as it should when
-- the body is back under workspace. every change of clip fades (0.3 to 0.5 s); each idle loops with no pop (two copies
-- crossfading where it ends) at a speed of its own (0.9 to 1.1) from a start of its own; the walk at the rate the
-- server says (how fast they really go); standing up and sitting down over the time the server takes, picked up part
-- way if you come in part way.
-- a living layer over their clips (owner, 17 Nov: "also the animations seem really stiff.."): small eased turns added
-- to their joints (here only: the server never moves them, and whatever clip plays goes on top; a Motor6D's C0, or on
-- Roblox's newer avatar joints, an AnimationConstraint's, its Attachment0's CFrame):
-- breathing in the waist, the head drifting between things to look at every few seconds (now and then you, if you are
-- near), the shoulders swaying a little. less while they walk or get up; none when they are far or out of sight
local Players = game:GetService("Players")
local CollectionService = game:GetService("CollectionService")
local RunService = game:GetService("RunService")

local me = Players.LocalPlayer
local DOT = '  <font color="#ffc24a">●</font>'

local function watch(t: Instance)
	if not t:IsA("TextLabel") then return end
	local flag, base = t:GetAttribute("BadgeFlag"), t:GetAttribute("Base")
	if type(flag) ~= "string" or type(base) ~= "string" then return end
	local function apply()
		if not t.Parent then return end
		t.Text = if me:GetAttribute(flag) == true then base .. DOT else base
	end
	apply()
	me:GetAttributeChangedSignal(flag):Connect(apply)
end
CollectionService:GetInstanceAddedSignal("RegularBadge"):Connect(watch)
for _, t in CollectionService:GetTagged("RegularBadge") do watch(t) end

-- ---------------------------------------------------------------- their clips
local FADE = 0.4
type Loop = { a: AnimationTrack, b: AnimationTrack, cur: AnimationTrack?, on: boolean, speed: number, first: boolean }
type Clips = {
	idle: Loop?, stand: Loop?, walk: AnimationTrack?, rise: AnimationTrack?, settle: AnimationTrack?, extra: AnimationTrack?, extraStand: AnimationTrack?, extraOn: AnimationTrack?,
	move: AnimationTrack?, moveLen: number, moveAt: number, after: string?, rate: number, extraAt: number,
	phase: string?, phaseAt: number,
}
local function track(an: Animator, id: any, prio: Enum.AnimationPriority, looped: boolean): AnimationTrack?
	if type(id) ~= "string" or id == "" then return nil end
	local a = Instance.new("Animation"); a.AnimationId = id
	local ok, t = pcall(function() return an:LoadAnimation(a) end)
	if not ok or not t then return nil end
	t.Priority = prio; t.Looped = looped
	return t
end
local function loopOf(an: Animator, id: any, prio: Enum.AnimationPriority): Loop?
	local a, b = track(an, id, prio, false), track(an, id, prio, false)
	if not a or not b then return nil end
	return { a = a, b = b, cur = nil, on = false, speed = 0.9 + math.random() * 0.2, first = true }
end
local function loopOn(l: Loop?, f: number)
	if not l or l.on then return end
	l.on = true; l.cur = l.a
	l.a:Play(f, 1, l.speed)
	if l.first and l.a.Length > 2 then l.first = false; l.a.TimePosition = math.random() * (l.a.Length - 1.5) end -- (no two start together)
end
local function loopOff(l: Loop?, f: number)
	if not l or not l.on then return end
	l.on = false; l.a:Stop(f); l.b:Stop(f); l.cur = nil
end
local function loopStep(l: Loop?)
	if not l or not l.on then return end
	local cur = l.cur
	if not cur or not (l.a.IsPlaying or l.b.IsPlaying) then l.b:Stop(0); l.a:Play(0.3, 1, l.speed); l.cur = l.a; return end
	if l.first and cur.Length > 2 then l.first = false; cur.TimePosition = math.random() * (cur.Length - 1.5) end
	if cur.Length > 0 and (cur.Length - cur.TimePosition) / l.speed < 0.75 then
		local nxt = if cur == l.a then l.b else l.a
		nxt:Play(0.7, 1, l.speed); cur:Stop(0.7); l.cur = nxt
	end
end

type Joint = { set: (CFrame) -> (), c0: CFrame }
type Reg = {
	m: Model, an: Animator?, clips: Clips?, inWorld: boolean,
	head: BasePart?, chest: BasePart?, waist: Joint?, neck: Joint?, ls: Joint?, rs: Joint?,
	breath: number, phase0: number, from: Vector2, to: Vector2, t0: number, dur: number, nextAt: number, calm: number,
}
local regs: { [Model]: Reg } = {}

local function load(r: Reg): Clips?
	local m = r.m
	local hum = m:FindFirstChildOfClass("Humanoid")
	local an = hum and hum:FindFirstChildOfClass("Animator")
	if not an or m:GetAttribute("Idle") == nil then return nil end -- (not all there yet: the next frame tries again)
	r.an = an
	return {
		idle = loopOf(an, m:GetAttribute("Idle"), Enum.AnimationPriority.Idle),
		stand = if m:GetAttribute("Pose") == "sit" then loopOf(an, m:GetAttribute("StandIdle"), Enum.AnimationPriority.Idle) else nil,
		walk = track(an, m:GetAttribute("Walk"), Enum.AnimationPriority.Movement, true),
		rise = track(an, m:GetAttribute("Rise"), Enum.AnimationPriority.Action, false),
		settle = track(an, m:GetAttribute("Settle"), Enum.AnimationPriority.Action, false),
		extra = track(an, m:GetAttribute("Extra"), Enum.AnimationPriority.Action, false),
		extraStand = track(an, m:GetAttribute("ExtraStand"), Enum.AnimationPriority.Action, false), extraOn = nil,
		move = nil, moveLen = 0, moveAt = 0, after = nil, rate = 1, extraAt = 0, phase = nil, phaseAt = 0,
	}
end
-- what keeps going while they are in a phase: "idle" (seated, or a standing one standing), "stand" (a seated one
-- standing), "walk"
local function base(r: Reg, phase: string): string
	if phase == "walk" or phase == "turn" then return "walk" end
	if phase == "seated" then return "idle" end
	return if r.m:GetAttribute("Pose") == "sit" then "stand" else "idle"
end
local function only(c: Clips, keep: string?, f: number)
	if keep == "idle" then loopOn(c.idle, f) else loopOff(c.idle, f) end
	if keep == "stand" then loopOn(c.stand, f) else loopOff(c.stand, f) end
	if c.walk then
		if keep == "walk" then if not c.walk.IsPlaying then c.walk:Play(f, 1, c.rate) end elseif c.walk.IsPlaying then c.walk:Stop(f) end
	end
end
local function stopAll(c: Clips)
	only(c, nil, 0)
	for _, t in { c.rise, c.settle, c.extra, c.extraStand } do if t and t.IsPlaying then t:Stop(0) end end
	c.move = nil; c.after = nil; c.phase = nil
end
local function clipsStep(r: Reg)
	local c = r.clips
	if not c then return end
	local m = r.m
	local now = workspace:GetServerTimeNow()
	local phase = m:GetAttribute("Phase")
	local at = m:GetAttribute("PhaseAt")
	phase = if type(phase) == "string" then phase else "stood"
	at = if type(at) == "number" then at else 0
	local rate = m:GetAttribute("WalkRate")
	c.rate = if type(rate) == "number" and rate > 0 then rate else 1
	if phase ~= c.phase or at ~= c.phaseAt then
		c.phase, c.phaseAt = phase, at
		local len = m:GetAttribute("PhaseLen")
		len = if type(len) == "number" and len > 0 then len else 1.2
		local t = if phase == "rise" then c.rise elseif phase == "settle" then c.settle else nil
		if c.move and c.move ~= t then c.move:Stop(FADE) end
		c.move = nil
		if phase == "rise" or phase == "settle" then
			c.after = if phase == "rise" then (if m:GetAttribute("Pose") == "sit" then "stand" else "idle") else "idle"
			if now - at >= len - 0.3 then only(c, c.after, FADE) -- (came in at its end: straight to what follows)
			elseif t then
				only(c, nil, FADE)
				c.move, c.moveLen, c.moveAt = t, len, at
				t:Play(0.35, 1, 1)
			else only(c, c.after, math.min(len, 1.2)) end -- (no clip: a long crossfade)
		else
			only(c, base(r, phase), FADE)
		end
	end
	-- standing up or sitting down: at the speed that fits the server's time, then into what follows
	local mv = c.move
	if mv then
		if mv.Length > 0 then
			local k = (now - c.moveAt) / c.moveLen
			local sp = mv.Length / c.moveLen
			if math.abs(mv.Speed - sp) > 0.02 then mv:AdjustSpeed(sp) end
			if math.abs(mv.TimePosition - k * mv.Length) > 0.25 then mv.TimePosition = math.clamp(k * mv.Length, 0, mv.Length) end
			if k >= 1 - 0.4 / c.moveLen then mv:Stop(FADE); c.move = nil; only(c, c.after, FADE) end
		elseif now - c.moveAt > c.moveLen then mv:Stop(FADE); c.move = nil; only(c, c.after, FADE) end
	end
	-- the walk's rate
	if c.walk and c.walk.IsPlaying and math.abs(c.walk.Speed - c.rate) > 0.03 then c.walk:AdjustSpeed(c.rate) end
	loopStep(c.idle); loopStep(c.stand)
	-- a one-shot now and then (the server says when; a seated one standing somewhere plays its ExtraStand)
	local x = m:GetAttribute("ExtraAt")
	if type(x) == "number" and x > c.extraAt then
		c.extraAt = x
		local which = if m:GetAttribute("Pose") == "sit" and phase ~= "seated" then c.extraStand else c.extra
		if which and now - x < 1.5 then which:Play(0.6); c.extraOn = which end
	end
	local e = c.extraOn
	if e and e.IsPlaying and e.Length > 0 and e.Length - e.TimePosition < 0.7 then e:Stop(0.7); c.extraOn = nil end
	if e and phase ~= "seated" and phase ~= "stood" and e.IsPlaying then e:Stop(0.4); c.extraOn = nil end -- (they started moving)
end

-- ---------------------------------------------------------------- the living layer
local NEAR = 70 -- (studs from the camera: nearer than this they get it)
local BREATH = math.rad(1.4) -- (how far the chest leans with each breath)
local HEAD_YAW, HEAD_PITCH = math.rad(16), math.rad(6) -- (how far the head drifts each way)
local SWAY = math.rad(1.6) -- (the shoulders)
local function joint(m: Model, part: string, name: string): Joint?
	local p = m:FindFirstChild(part)
	local j = p and p:FindFirstChild(name)
	if j and j:IsA("Motor6D") then
		local m6 = j
		return { set = function(cf) m6.C0 = cf end, c0 = m6.C0 }
	elseif j and j:IsA("AnimationConstraint") and j.Attachment0 then
		local at = j.Attachment0
		return { set = function(cf) at.CFrame = cf end, c0 = at.CFrame }
	end
	return nil
end
local function ease(x: number): number x = math.clamp(x, 0, 1); return x * x * (3 - 2 * x) end
local function layer(r: Reg, now: number, dt: number, eye: Vector3, mine: BasePart?, cam: Camera)
	local m, head, chest = r.m, r.head, r.chest
	if not head or not chest or (head.Position - eye).Magnitude > NEAR then return end
	local _, onScreen = cam:WorldToViewportPoint(head.Position)
	if not onScreen then return end
	local phase = m:GetAttribute("Phase") -- (calmer while they walk, turn, get up or sit down: the clip moves them enough)
	local want = if phase == "walk" or phase == "rise" or phase == "settle" or phase == "turn" then 0.35 else 1
	r.calm += (want - r.calm) * math.min(1, dt * 3)
	local b = math.sin((now * r.breath + r.phase0) * 2 * math.pi)
	if r.waist then r.waist.set(r.waist.c0 * CFrame.new(0, 0.012 * b, 0) * CFrame.Angles(-BREATH * b * (0.5 + 0.5 * r.calm), 0, 0)) end
	-- the head: a new thing to look at every 2.5 to 6 s, turned to over 0.7 to 1.2 s; now and then you, if you are near
	if now >= r.nextAt then
		local look = Vector2.new((math.random() * 2 - 1) * HEAD_YAW, (math.random() * 1.6 - 1) * HEAD_PITCH)
		if mine and (mine.Position - head.Position).Magnitude < 14 and math.random() < 0.35 then
			local d = chest.CFrame:VectorToObjectSpace(mine.Position - head.Position)
			local flat = math.sqrt(d.X * d.X + d.Z * d.Z)
			look = Vector2.new(math.clamp(math.atan2(-d.X, -d.Z), -math.rad(40), math.rad(40)), math.clamp(math.atan2(d.Y, flat), -math.rad(12), math.rad(10)))
		end
		r.from = r.from:Lerp(r.to, ease((now - r.t0) / r.dur))
		r.to = look; r.t0 = now; r.dur = 0.7 + math.random() * 0.5
		r.nextAt = now + 2.5 + math.random() * 3.5
	end
	local h = r.from:Lerp(r.to, ease((now - r.t0) / r.dur)) * r.calm
	if r.neck then r.neck.set(r.neck.c0 * CFrame.Angles(h.Y + BREATH * b * 0.3, h.X, 0)) end
	-- the shoulders: a slow sway, each its own
	local s1 = math.sin((now * 0.31 + r.phase0 * 1.7) * 2 * math.pi)
	local s2 = math.sin((now * 0.27 + r.phase0 * 2.3) * 2 * math.pi)
	if r.ls then r.ls.set(r.ls.c0 * CFrame.Angles(SWAY * 0.4 * s1 * r.calm, 0, SWAY * (0.6 * s1 + 0.4 * b) * r.calm)) end
	if r.rs then r.rs.set(r.rs.c0 * CFrame.Angles(SWAY * 0.4 * s2 * r.calm, 0, -SWAY * (0.6 * s2 + 0.4 * b) * r.calm)) end
end

local function add(m: Instance)
	if not m:IsA("Model") or regs[m] then return end
	regs[m] = {
		m = m, an = nil, clips = nil, inWorld = false, head = nil, chest = nil, waist = nil, neck = nil, ls = nil, rs = nil,
		breath = 0.2 + math.random() * 0.06, phase0 = math.random() * 10, -- (a breath every 3.8 to 5 s, each their own)
		from = Vector2.zero, to = Vector2.zero, t0 = 0, dur = 1, nextAt = os.clock() + math.random() * 3, calm = 1,
	}
end
local function drop(m: Instance)
	local r = regs[m :: Model]
	if not r then return end
	for _, k in { r.waist, r.neck, r.ls, r.rs } do if k then pcall(k.set, k.c0) end end
	if r.clips then stopAll(r.clips) end
	regs[m :: Model] = nil
end
CollectionService:GetInstanceAddedSignal("HubRegular"):Connect(add)
CollectionService:GetInstanceRemovedSignal("HubRegular"):Connect(drop)
for _, m in CollectionService:GetTagged("HubRegular") do add(m) end

RunService.RenderStepped:Connect(function(dt)
	local cam = workspace.CurrentCamera
	local now = os.clock()
	local eye = if cam then cam.CFrame.Position else Vector3.zero
	local mine = if me.Character then me.Character:FindFirstChild("Head") :: BasePart? else nil
	for m, r in regs do
		if not m.Parent then continue end
		local inWorld = m:IsDescendantOf(workspace)
		if not inWorld then
			-- (out of your world: nothing to play; everything starts again when they are back)
			if r.inWorld and r.clips then stopAll(r.clips) end
			r.inWorld = false
			continue
		end
		if not r.inWorld then
			r.inWorld = true
			if r.clips then stopAll(r.clips) end
		end
		if not r.head then
			local head, chest = m:FindFirstChild("Head"), m:FindFirstChild("UpperTorso")
			if head and chest and head:IsA("BasePart") and chest:IsA("BasePart") then
				r.head, r.chest = head, chest
				r.waist, r.neck = joint(m, "UpperTorso", "Waist"), joint(m, "Head", "Neck")
				r.ls, r.rs = joint(m, "LeftUpperArm", "LeftShoulder"), joint(m, "RightUpperArm", "RightShoulder")
			end
		end
		if not r.clips then r.clips = load(r) end
		clipsStep(r)
		if cam then layer(r, now, dt, eye, mine, cam) end
	end
end)
