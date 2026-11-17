--!strict
-- SMALL LOOPING PREVIEWS of kill effects and emotes on cards (the owner, 17 Nov 2026: "for kill effects in shop can they
-- be small previews? same with in inv?"). the shop's cards, its inventory and its inspect panel use it; anyone may.
--   FlairAnim.attach(frame, kind, id) -> handle | nil: draws over `frame` (a square tile; it keeps the frame's own
--   still picture underneath for when nothing can play)
--     kill:  the effect's flipbook (Shared.FlairSheets, the VFX session's sheets), stepped frame by frame. no sheet yet:
--            nil (the still tile stays)
--     emote: a copy of your own avatar in a ViewportFrame inside a WorldModel (so it animates) doing the emote, looped
--   handle.stop() / FlairAnim.detach(frame) take it away (the frame going away does too)
-- cheap on purpose: one stepper for all; only a preview that's on screen plays (its ScreenGui enabled, every ancestor
-- visible, inside its scrolling frame's view and the screen), at most MAX at once, flipbooks at their own fps; the rest
-- hold their frame (emotes pause)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local me = Players.LocalPlayer

local A = {}
local MAX = 8
local BG = Color3.fromRGB(22, 24, 30) -- (the flair tile's dark)

type Handle = { frame: GuiObject, kind: string, root: GuiObject, step: (number, boolean) -> (), stop: () -> (), dead: boolean }
local live: { Handle } = {}

local function sheets(): any
	local m = Shared:FindFirstChild("FlairSheets")
	if not (m and m:IsA("ModuleScript")) then return nil end
	local ok, S = pcall(require, m)
	return if ok and type(S) == "table" then S else nil
end
local function flair(): any
	local m = Shared:FindFirstChild("Flair")
	if not (m and m:IsA("ModuleScript")) then return nil end
	local ok, F = pcall(require, m)
	return if ok and type(F) == "table" then F else nil
end

local function new(class: string, props: { [string]: any }, parent: Instance?): any
	local o = Instance.new(class)
	for k, v in props do (o :: any)[k] = v end
	if parent then o.Parent = parent end
	return o
end
local function round(o: Instance, r: number) new("UICorner", { CornerRadius = UDim.new(0, r) }, o) end

-- is it on screen? its ScreenGui on, every GuiObject above it visible, and its box inside every scrolling frame's view
local function shown(g: GuiObject): boolean
	if not g:IsDescendantOf(game) then return false end
	local a, s = g.AbsolutePosition, g.AbsoluteSize
	if s.X < 2 or s.Y < 2 then return false end
	local x0, y0, x1, y1 = a.X, a.Y, a.X + s.X, a.Y + s.Y
	local p: Instance? = g
	while p do
		if p:IsA("GuiObject") then
			if not p.Visible then return false end
			if p:IsA("ScrollingFrame") or p.ClipsDescendants then
				local pa, ps = p.AbsolutePosition, p.AbsoluteSize
				if x1 < pa.X or y1 < pa.Y or x0 > pa.X + ps.X or y0 > pa.Y + ps.Y then return false end
			end
		elseif p:IsA("LayerCollector") then
			if not (p :: any).Enabled then return false end
			break
		end
		p = p.Parent
	end
	local cam = workspace.CurrentCamera
	if cam then
		local v = cam.ViewportSize
		if x1 < 0 or y1 < -60 or x0 > v.X or y0 > v.Y then return false end
	end
	return true
end

-- ---------------------------------------------------------------- kill effects: the flipbook
local function flipbook(frame: GuiObject, id: string): Handle?
	local S = sheets()
	local sh = S and S.kill and S.kill[id]
	if type(sh) ~= "table" or type(sh.image) ~= "string" then return nil end
	local cols, px = tonumber(sh.cols) or 4, tonumber(sh.px) or 256
	local n = math.max(1, tonumber(sh.n) or 16)
	local fps = tonumber(sh.fps) or 10
	local hold = tonumber(sh.hold) or 0
	local z = frame.ZIndex + 3
	-- (any shape of frame: the backdrop fills it, the frame's picture sits in a square in the middle, and the words are
	-- placed in that square, so they land on the sheet's panel whatever the card's shape)
	local back = new("Frame", { Name = "FlairAnim", BackgroundColor3 = BG, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = z }, frame)
	round(back, 6)
	local img = new("ImageLabel", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromScale(1, 1), Image = sh.image, ImageRectSize = Vector2.new(px, px), ImageRectOffset = Vector2.zero,
		ScaleType = Enum.ScaleType.Stretch, ZIndex = z }, back)
	new("UIAspectRatioConstraint", { AspectRatio = 1 }, img)
	local words: TextLabel? = nil
	local w = sh.words
	if type(w) == "table" and type(w.text) == "string" then
		words = new("TextLabel", { BackgroundTransparency = 1, Position = UDim2.fromScale(w.x or 0, w.y or 0), Size = UDim2.fromScale(w.w or 1, w.h or 0.2),
			Text = w.text, TextScaled = true, TextColor3 = w.color or Color3.fromRGB(236, 240, 246), Font = Enum.Font.Code, Visible = false, ZIndex = z + 1 }, img)
	end
	local t = math.random() * (n / fps) -- (cards next to each other don't all play in step)
	local last = -1
	local h: Handle
	h = {
		frame = frame, kind = "kill", root = back, dead = false,
		step = function(dt: number, on: boolean)
			if on then t += dt end
			local f = math.floor(t * fps) % (n + hold)
			if f >= n then f = n - 1 end
			if f == last then return end
			last = f
			img.ImageRectOffset = Vector2.new((f % cols) * px, math.floor(f / cols) * px)
			if words and w then (words :: TextLabel).Visible = f + 1 >= (w.from or 1) and f + 1 <= (w.to or n) end
		end,
		stop = function()
			h.dead = true
			back:Destroy()
		end,
	}
	h.step(0, true)
	return h
end

-- ---------------------------------------------------------------- you, on a little set
-- (the owner, 17 Nov: "kill effects should display your character over surrounds, and the preview should be your
-- avatar". a copy of your own avatar stands on a small set inside the card: a floor disc with a thin ring in the
-- item's rarity colour, a dark backdrop behind; the game's quiet palette)
local tpl: Model? = nil
local tplFor: Model? = nil
local function avatar(): Model?
	local ch = me.Character
	if not ch then return tpl end
	if tpl and tplFor == ch then return tpl end
	local was = ch.Archivable
	ch.Archivable = true
	local ok, c = pcall(function() return ch:Clone() end)
	ch.Archivable = was
	if not ok or not c then return tpl end
	local m = c :: Model
	for _, d in m:GetDescendants() do
		if d:IsA("LuaSourceContainer") or d:IsA("Sound") or d:IsA("Tool") or d:IsA("ForceField") or d:IsA("BillboardGui")
			or d:IsA("ParticleEmitter") or d:IsA("Trail") or d:IsA("Beam") then
			d:Destroy()
		elseif d:IsA("BasePart") then
			d.Anchored = false; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
		end
	end
	local hum = m:FindFirstChildOfClass("Humanoid")
	if hum then hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None end
	local root = m:FindFirstChild("HumanoidRootPart") :: BasePart?
	if root then root.Anchored = true end
	if tpl then tpl:Destroy() end
	tpl, tplFor = m, ch
	return m
end

-- the body's own height (its parts, not its accessories: a big hat or a staff would shrink it)
local function bodySpan(m: Model): (number, number)
	local lo, hi = math.huge, -math.huge
	for _, p in m:GetChildren() do
		if p:IsA("BasePart") and p.Name ~= "HumanoidRootPart" then
			lo = math.min(lo, p.Position.Y - p.Size.Y / 2)
			hi = math.max(hi, p.Position.Y + p.Size.Y / 2)
		end
	end
	if lo == math.huge then
		local cf, size = m:GetBoundingBox()
		lo, hi = cf.Position.Y - size.Y / 2, cf.Position.Y + size.Y / 2
	end
	return lo, hi
end

local SET_FLOOR = Color3.fromRGB(52, 56, 66)
local SET_WALL = Color3.fromRGB(32, 35, 42)
local SET_SEAM = Color3.fromRGB(62, 66, 76)
-- the set's pieces round a body standing at the origin, its feet at `lo`, facing -Z (the camera is in front, on -Z)
local function buildSet(parent: Instance, lo: number, ring: Color3?, big: boolean?)
	local function p(size: Vector3, cf: CFrame, c: Color3, shape: Enum.PartType?, mat: Enum.Material?): Part
		local x = Instance.new("Part")
		x.Anchored = true; x.CanCollide = big == true; x.CanQuery = false; x.CanTouch = false; x.CastShadow = big == true
		x.Shape = shape or Enum.PartType.Block
		x.Size = size; x.CFrame = cf; x.Color = c; x.Material = mat or Enum.Material.SmoothPlastic
		x.TopSurface = Enum.SurfaceType.Smooth; x.BottomSurface = Enum.SurfaceType.Smooth
		x.Parent = parent
		return x
	end
	local k = if big then 1.6 else 1
	local up = CFrame.Angles(0, 0, math.pi / 2)
	-- the floor disc, and its thin ring in the rarity's colour
	p(Vector3.new(0.4, 9 * k, 9 * k), CFrame.new(0, lo - 0.2, 0) * up, SET_FLOOR, Enum.PartType.Cylinder)
	-- (a thin line, not a glow: on the big set it's plain and a little dimmed, the quiet palette's one accent)
	if ring then
		local rc = if big then ring:Lerp(SET_FLOOR, 0.3) else ring
		p(Vector3.new(0.38, 9.16 * k, 9.16 * k), CFrame.new(0, lo - 0.22, 0) * up, rc, Enum.PartType.Cylinder, if big then Enum.Material.SmoothPlastic else Enum.Material.Neon)
	end
	-- the ground round it, a step darker, and the backdrop behind with a lighter seam where they meet
	local wall = if big then Color3.fromRGB(44, 48, 57) else SET_WALL
	p(Vector3.new(90, 0.4, 90), CFrame.new(0, lo - 0.45, 0), wall)
	p(Vector3.new(90, 50, 0.6), CFrame.new(0, lo + 24.5, 6 * k), wall)
	p(Vector3.new(90, 0.3, 0.7), CFrame.new(0, lo - 0.1, 6 * k - 0.1), SET_SEAM)
	-- (the big set: two side walls turned in, so no sky shows past the backdrop's ends whatever the screen's width)
	if big then
		for _, sx in { -1, 1 } do
			p(Vector3.new(0.6, 50, 40), CFrame.new(sx * 16, lo + 24.5, -4) * CFrame.Angles(0, sx * 0.5, 0), wall)
		end
	end
end

-- a card's scene: the frame's holder, a ViewportFrame with a WorldModel (so things animate), the set, a copy of you
-- framed on your body (feet just above the bottom edge, a fifth over the head for raised arms), from the front a
-- little to the side. returns nil with no avatar to copy
type Scene = { holder: Frame, vp: ViewportFrame, world: WorldModel, cam: Camera, m: Model, lo: number, hi: number }
local function scene(frame: GuiObject, ring: Color3?, spread: number?): Scene?
	local src = avatar()
	if not src then return nil end
	local z = frame.ZIndex + 3
	local holder = new("Frame", { Name = "FlairAnim", BackgroundColor3 = SET_WALL, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = z, ClipsDescendants = true }, frame)
	round(holder, 6)
	-- (the shop's own 3D light, V.show's, so the pastel colours read as they do on the guns and in the inspect panel)
	local vp = new("ViewportFrame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = z + 1,
		Ambient = Color3.fromRGB(150, 153, 162), LightColor = Color3.fromRGB(255, 248, 240), LightDirection = Vector3.new(-0.5, -1, -0.7) }, holder)
	local world = new("WorldModel", {}, vp)
	local m = src:Clone()
	m:PivotTo(CFrame.identity)
	m.Parent = world
	local lo, hi = bodySpan(m)
	buildSet(world, lo, ring, false)
	local cam = new("Camera", { FieldOfView = 30 }, vp)
	vp.CurrentCamera = cam
	local r = (hi - lo) * (spread or 0.64) -- (half the height the frame shows: a kill effect's card a little wider)
	local d = r / math.tan(math.rad(cam.FieldOfView / 2))
	local look = Vector3.new(0, lo + r * 0.93, 0)
	local face = Vector3.new(0, 0, -1)
	cam.CFrame = CFrame.lookAt(look + (face * d) + face:Cross(Vector3.yAxis) * (d * 0.2), look)
	return { holder = holder, vp = vp, world = world, cam = cam, m = m, lo = lo, hi = hi }
end

local function animator(m: Model): Animator?
	local hum = m:FindFirstChildOfClass("Humanoid")
	if not hum then return nil end
	return hum:FindFirstChildOfClass("Animator") or new("Animator", {}, hum)
end
-- Roblox's own idle, so a copy doesn't stand in its rig's T pose
local IDLE = { [Enum.HumanoidRigType.R15] = "rbxassetid://507766388", [Enum.HumanoidRigType.R6] = "rbxassetid://180435571" }
local function idle(m: Model): AnimationTrack?
	local hum = m:FindFirstChildOfClass("Humanoid")
	local an = animator(m)
	if not hum or not an then return nil end
	local a = new("Animation", { AnimationId = IDLE[hum.RigType] or IDLE[Enum.HumanoidRigType.R15] })
	local ok, tr = pcall(function() return (an :: Animator):LoadAnimation(a) end)
	if not ok or not tr then return nil end
	tr.Looped = true
	tr.Priority = Enum.AnimationPriority.Idle
	tr:Play(0)
	return tr
end

local function rarityColor(kind: string, id: string): Color3?
	local F = flair()
	local i = F and F.info(kind, id)
	return i and F.RARITY_COLOR and F.RARITY_COLOR[i.rarity] or nil
end

-- ---------------------------------------------------------------- emotes: you, doing it
local function emote(frame: GuiObject, id: string): Handle?
	local F = flair()
	local e = F and F.info("emote", id)
	if not e or type(e.anim) ~= "string" or e.anim == "rbxassetid://0" then return nil end
	local sc = scene(frame, rarityColor("emote", id))
	if not sc then return nil end
	local an = animator(sc.m)
	-- (the flair session's way, FlairUI's stand-in: priority Action4, in over 0.3 s; a one-shot is let go 0.35 s before
	-- its end, rests about 0.7 s, and starts again, so it never snaps back at a loop's seam. a looping emote just loops.
	-- the clip, its length and whether it loops are read from Flair now: the ids change when the emotes are remade)
	local track: AnimationTrack? = nil
	local loops = e.loop == true
	local len = math.max(0.8, tonumber(e.len) or 3)
	if an then
		local anim = new("Animation", { AnimationId = e.anim })
		local ok, tr = pcall(function() return (an :: Animator):LoadAnimation(anim) end)
		if ok and tr then
			track = tr
			tr.Looped = loops
			tr.Priority = Enum.AnimationPriority.Action4
		end
	end
	local REST = 0.7
	local t = 0 -- (time in this round of the cycle, only counted while it's on screen)
	local going, playing = false, false
	local h: Handle
	h = {
		frame = frame, kind = "emote", root = sc.holder, dead = false,
		step = function(dt: number, on: boolean)
			local tr = track
			if not tr then return end
			if on ~= playing then
				playing = on
				if going then tr:AdjustSpeed(if on then 1 else 0) end
			end
			if not on then return end
			if not going and t == 0 then tr:Play(0.3); going = true end
			t += dt
			if loops then return end
			if going and t >= len - 0.35 then tr:Stop(0.35); going = false end
			if not going and t >= len + REST then t = 0 end
		end,
		stop = function()
			h.dead = true
			if track then pcall(function() (track :: AnimationTrack):Stop(0) end) end
			sc.holder:Destroy()
		end,
	}
	return h
end

-- ---------------------------------------------------------------- kill effects: you, taking it
-- the flair session's own KillFx run on the copy inside the card. a ViewportFrame draws parts and the body's fades and
-- moves, not particles or Highlights; KillFx parents its pieces where it's told (opts.parent) and faces the camera it's
-- given (opts.camera) since it set K.VIEWPORT. before that: you on the set, still (PREVIEW ON YOU shows the real one)
local function killfx(): any
	local m = script.Parent:FindFirstChild("KillFx")
	if not (m and m:IsA("ModuleScript")) then return nil end
	local ok, K = pcall(require, m)
	return if ok and type(K) == "table" then K else nil
end

-- Gibs (the default, "none"): the body falls apart. a WorldModel doesn't simulate, so the pieces are thrown by hand
local function gibs(m: Model, floorY: number): () -> ()
	local bits = {}
	for _, d in m:GetDescendants() do
		if d:IsA("Motor6D") then d.Enabled = false end
	end
	for _, p in m:GetDescendants() do
		if p:IsA("BasePart") and p.Name ~= "HumanoidRootPart" then
			table.insert(bits, { p = p, cf = p.CFrame, v = Vector3.new(math.random() * 6 - 3, math.random() * 5 + 1, math.random() * 6 - 3),
				w = Vector3.new(math.random() * 6 - 3, math.random() * 6 - 3, math.random() * 6 - 3) })
		end
	end
	local t0 = os.clock()
	local con: RBXScriptConnection? = nil
	con = RunService.RenderStepped:Connect(function(dt)
		if os.clock() - t0 > 1.4 then if con then con:Disconnect() end return end
		for _, b in bits do
			if b.p.Parent then
				b.v -= Vector3.new(0, 30 * dt, 0)
				local pos = b.p.Position + b.v * dt
				local half = b.p.Size.Magnitude * 0.25
				if pos.Y < floorY + half then pos = Vector3.new(pos.X, floorY + half, pos.Z); b.v = Vector3.new(b.v.X * 0.5, 0, b.v.Z * 0.5); b.w *= 0.5 end
				b.p.CFrame = CFrame.new(pos) * (b.p.CFrame - b.p.CFrame.Position) * CFrame.Angles(b.w.X * dt, b.w.Y * dt, b.w.Z * dt)
			end
		end
	end)
	return function()
		if con then con:Disconnect() end
		for _, b in bits do if b.p.Parent then b.p.CFrame = b.cf end end
		for _, d in m:GetDescendants() do if d:IsA("Motor6D") then d.Enabled = true end end
	end
end

local function kill(frame: GuiObject, id: string): Handle?
	local F = flair()
	local info = F and F.info("kill", id)
	if not info then return nil end
	local sc = scene(frame, rarityColor("kill", id), 0.74)
	if not sc then return nil end
	local stand = idle(sc.m)
	local K = killfx()
	local live3d = K ~= nil and K.VIEWPORT == true
	local dur = math.max(0.8, tonumber(info.dur) or 1.2)
	-- (each loop: you stand a moment, the effect plays, a short beat, you're back. cards side by side start apart so a row
	-- never goes blank at once, and the camera follows the body while it rises or flies, so it never leaves the tile)
	local START, REST = 0.7, 0.3
	local t, running = -math.random() * 1.6, false
	local undo: (() -> ())? = nil
	local cam0 = sc.cam.CFrame
	local body = {}
	local function collect()
		table.clear(body)
		for _, p in sc.m:GetChildren() do if p:IsA("BasePart") and p.Name ~= "HumanoidRootPart" then table.insert(body, p) end end
	end
	collect()
	local function centre(): Vector3?
		local sum, n = Vector3.zero, 0
		for _, p in body do
			if p.Transparency < 0.95 and p.LocalTransparencyModifier < 0.95 then sum += p.Position; n += 1 end
		end
		return if n > 0 then sum / n else nil
	end
	local c0 = centre() or Vector3.zero
	local follow = Vector3.zero
	-- (what the run adds to the card, KillFx parenting its pieces here: a duck, chickens, wedges. once nothing of the
	-- body or those is in view for a moment, the loop ends early, so the card is never long empty)
	local props: { Instance } = {}
	local addCon = sc.world.ChildAdded:Connect(function(c) if running then table.insert(props, c) end end)
	local tanHalf = math.tan(math.rad(sc.cam.FieldOfView / 2)) * 1.05
	local function inView(pos: Vector3): boolean
		local rel = sc.cam.CFrame:PointToObjectSpace(pos)
		if rel.Z > -0.1 then return false end
		return math.abs(rel.Y) / -rel.Z < tanHalf and math.abs(rel.X) / -rel.Z < tanHalf
	end
	local function seen(): boolean
		for _, p in body do
			if p.Transparency < 0.95 and p.LocalTransparencyModifier < 0.95 and inView(p.Position) then return true end
		end
		for _, x in props do
			if x.Parent then
				if x:IsA("BasePart") then
					if x.Transparency < 0.95 and inView(x.Position) then return true end
				else
					for _, q in x:GetDescendants() do
						if q:IsA("BasePart") and q.Transparency < 0.95 and inView(q.Position) then return true end
					end
				end
			end
		end
		return false
	end
	local emptyFor = 0
	local h: Handle
	local function reset()
		if undo then pcall(undo); undo = nil end
		if live3d and K and id ~= "none" then
			pcall(K.reset, sc.m)
			-- (a run that ended on its own leaves the body hidden for good, as a dead body should: a fresh copy of you each
			-- loop, like the equip screen's stand-in)
			local src = avatar()
			if src then
				local fresh = src:Clone()
				fresh:PivotTo(CFrame.identity)
				fresh.Parent = sc.world
				sc.m:Destroy()
				sc.m = fresh
				collect()
				if stand then pcall(function() (stand :: AnimationTrack):Stop(0) end) end
				stand = idle(fresh)
			end
		end
		running = false
		follow = Vector3.zero
		sc.cam.CFrame = cam0
		table.clear(props)
		emptyFor = 0
	end
	h = {
		frame = frame, kind = "kill", root = sc.holder, dead = false,
		step = function(dt: number, on: boolean)
			if stand then stand:AdjustSpeed(if on then 1 else 0) end
			if not on or not (live3d or id == "none") then return end
			t += dt
			if not running and t >= START then
				running = true
				if id == "none" then undo = gibs(sc.m, sc.lo)
				elseif K then pcall(K.play, sc.m, id, { preview = true, parent = sc.world, camera = sc.cam }) end
			end
			if running then
				-- (follow up and sideways, never down: a body sinking into its grave stays framed with its stone)
				local c = centre()
				if c then
					local d = (c - c0) * Vector3.new(0.6, 0.9, 0.6)
					follow = follow:Lerp(Vector3.new(d.X, math.max(0, d.Y), d.Z), math.min(1, dt * 8))
				end
				sc.cam.CFrame = cam0 + follow
				if t > START + 0.2 then
					emptyFor = if seen() then 0 else emptyFor + dt
					if emptyFor >= 0.25 then reset(); t = 0; return end
				end
			end
			if running and t >= START + dur + REST then reset(); t = 0 end
		end,
		stop = function()
			h.dead = true
			addCon:Disconnect()
			reset()
			sc.holder:Destroy()
		end,
	}
	return h
end

-- ---------------------------------------------------------------- PREVIEW ON YOU: the real thing, full screen
-- a kill effect played for real (particles, light and all) on a copy of you standing on a set off the map, with the
-- camera on it: the shop's inspect panel's PREVIEW ON YOU. every ScreenGui steps aside and comes back after; SPACE or
-- a click ends it early. returns once it's over
local STAGE = CFrame.new(0, 1800, 0) -- (well above everything: nothing else is up here)
local showing = false
function A.isShowing(): boolean return showing end
function A.showcase(id: string): boolean
	if showing then return false end
	local F = flair()
	local info = F and F.info("kill", id)
	local K = killfx()
	local src = avatar()
	if not info or not K or not src then return false end
	showing = true
	local cam = workspace.CurrentCamera
	local pg = me:FindFirstChildOfClass("PlayerGui")
	local hidden = {}
	if pg then
		for _, g in pg:GetChildren() do
			if g:IsA("ScreenGui") and g.Enabled then g.Enabled = false; table.insert(hidden, g) end
		end
	end
	local set = new("Model", { Name = "JankShowcase" }, workspace)
	local m = src:Clone()
	m:PivotTo(CFrame.identity)
	local lo, hi = bodySpan(m)
	-- (the set is built round the origin, then the whole lot moved up to the stage)
	buildSet(set, lo, rarityColor("kill", id), true)
	m.Parent = set
	for _, d in m:GetDescendants() do if d:IsA("BasePart") then d.CanCollide = true end end
	set.WorldPivot = CFrame.identity -- (it moves by its own origin, where the body stands)
	set:PivotTo(STAGE)
	-- light from the front: a warm key high on the left and a cool fill on the right (the sun up here is behind the wall)
	for _, l in { { -6, 9, -9, 2.2, Color3.fromRGB(255, 240, 224) }, { 7, 5, -8, 1.2, Color3.fromRGB(214, 226, 255) } } do
		local lamp = new("Part", { Anchored = true, CanCollide = false, CanQuery = false, Transparency = 1, Size = Vector3.one,
			CFrame = STAGE * CFrame.new(l[1], lo + l[2], l[3]) }, set)
		new("PointLight", { Brightness = l[4], Range = 30, Color = l[5], Shadows = false }, lamp)
	end
	local stand = idle(m)
	-- the camera: in front, a little to the side, easing in while it plays
	local h = hi - lo
	local look = STAGE * Vector3.new(0, lo + h * 0.55, 0)
	local from = STAGE * Vector3.new(h * 0.55, lo + h * 0.75, -h * 2.4)
	local to = STAGE * Vector3.new(h * 0.35, lo + h * 0.65, -h * 1.9)
	local oldType, oldFov, oldSubject = cam.CameraType, cam.FieldOfView, cam.CameraSubject
	cam.CameraType = Enum.CameraType.Scriptable
	cam.FieldOfView = 40
	cam.CFrame = CFrame.lookAt(from, look)
	-- SKIP, the only words on screen
	local skipGui = new("ScreenGui", { Name = "JankShowcaseSkip", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 60 }, pg)
	local skip = new("TextLabel", { BackgroundColor3 = Color3.fromRGB(16, 18, 22), BackgroundTransparency = 0.25, BorderSizePixel = 0,
		AnchorPoint = Vector2.new(1, 1), Position = UDim2.new(1, -24, 1, -24), Size = UDim2.fromOffset(150, 40),
		Text = "SKIP  [SPACE]", TextColor3 = Color3.fromRGB(240, 242, 245), TextSize = 14, Font = Enum.Font.GothamBold }, skipGui)
	round(skip, 6)
	local over = false
	local UIS = game:GetService("UserInputService")
	local inp = UIS.InputBegan:Connect(function(io)
		if io.KeyCode == Enum.KeyCode.Space or io.KeyCode == Enum.KeyCode.Escape or io.UserInputType == Enum.UserInputType.MouseButton1
			or io.UserInputType == Enum.UserInputType.Touch or io.KeyCode == Enum.KeyCode.ButtonB then over = true end
	end)
	local total = 0.6 + (tonumber(info.dur) or 1.2) + 1.1
	local t0 = os.clock()
	local fired = false
	while not over and os.clock() - t0 < total do
		local a = math.clamp((os.clock() - t0) / total, 0, 1)
		local e = 1 - (1 - a) * (1 - a)
		cam.CFrame = CFrame.lookAt(from:Lerp(to, e), look)
		if not fired and os.clock() - t0 >= 0.6 then
			fired = true
			if id == "none" then
				for _, d in m:GetDescendants() do
					if d:IsA("Motor6D") then d:Destroy()
					elseif d:IsA("BasePart") then
						d.Anchored = false
						d.AssemblyLinearVelocity = Vector3.new(math.random() * 8 - 4, math.random() * 6, math.random() * 8 - 4)
					end
				end
			else
				pcall(K.play, m, id, { preview = true })
			end
		end
		RunService.RenderStepped:Wait()
	end
	inp:Disconnect()
	pcall(K.reset, m)
	if stand then pcall(function() (stand :: AnimationTrack):Stop(0) end) end
	skipGui:Destroy()
	set:Destroy()
	cam.CameraType = oldType
	cam.FieldOfView = oldFov
	if oldSubject then cam.CameraSubject = oldSubject end
	for _, g in hidden do if g.Parent then g.Enabled = true end end
	showing = false
	return true
end

-- ---------------------------------------------------------------- the stepper
function A.attach(frame: GuiObject, kind: string, id: string): any
	local h = if kind == "kill" then (kill(frame, id) or flipbook(frame, id)) elseif kind == "emote" then emote(frame, id) else nil
	if not h then return nil end
	table.insert(live, h)
	return h
end
function A.detach(frame: GuiObject)
	for _, h in live do if h.frame == frame and not h.dead then h.stop() end end
end
-- (how many play right now: a test reads it)
A.playing = 0

RunService.RenderStepped:Connect(function(dt)
	if #live == 0 then A.playing = 0; return end
	local n = 0
	for i = #live, 1, -1 do
		local h = live[i]
		if h.dead or not h.root:IsDescendantOf(game) then
			if not h.dead then h.dead = true end
			table.remove(live, i)
		else
			local on = n < MAX and shown(h.frame)
			if on then n += 1 end
			h.step(dt, on)
		end
	end
	A.playing = n
end)

return A
