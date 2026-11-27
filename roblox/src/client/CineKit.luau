--!strict
-- CineKit (27 Nov 2026): the shared piece for a scripted camera on the client. Written for HOUSE HUNT's gunman intro
-- (client/HuntIntro.client.luau); the finishers and the victory scene asked for it (theirs are woven into their own
-- scenes) and move to it with their next scenes. Nothing in it knows a scene. Its numbers match the finishers' (their
-- notes, 27 Nov) so every cinematic in the game reads as one: bars 0.105 of the screen, the handheld shake, the hit kick.
--   CineKit.bars(on, dur?)             the letterbox in or out (smoothstep, default 0.2 s; Tidecrest uses 0.4 in)
--   CineKit.play(shots, opts?) -> run  steps the camera every frame until run.stop(handBack?)
--     a shot: { name, t0, t1, ease = "inout" | "out" | "linear", roll = degrees?, shake = k | (u) -> k,
--               cam = (u) -> CFrame                     (any camera you like), or
--               from = { at, look, fov }, to = { at, look, fov } | "gameplay"   (Vector3s, or functions giving them) }
--       (u = 0..1 through the shot; a cut is the next shot, never blended across; "gameplay" = where the game's own
--       camera will be, so the hand-back doesn't pop)
--     opts: clock = () -> s (default: os.clock since play; a server clock keeps a phone or a slow load on time),
--           flag = string for the player's Finishing attribute while it plays (HubLife keeps its zone look off;
--           DeathCam, PadLook, MenuCursor and ReplayClient stand back); hold = studs/s drift back after the last shot;
--           warm = s before the last shot's end when the game's own camera takes the camera type back while this still
--           places it every frame (it then carries on from the last frame, no stale pop, and hides your own body itself)
--     run.kick(amp)   a hit kick from now (0.3 s)        run.shot   the current shot's name
--     run.stop(handBack?)  ends it; with handBack the camera lands on the gameplay camera, CameraType Custom
--   CineKit.prewarm(shots, opts?) -> warm   YIELDS (at most opts.timeout, default 4 s). Run it BEFORE the film: under an
--     open, a sting, a countdown, a loading moment; never as a frozen screen mid-film (the owner, 27 Nov: "Things pop
--     in because it renders as the clip plays"). It
--       1. asks ZoneCull (through CullKeep) to keep every map piece the shots see: each shot's camera spot and the point
--          it looks at, at u = 0, 0.5 and 1 (cam(u), or from/to; "gameplay" = where your body is), plus opts.points;
--       2. waits two frames for ZoneCull to bring them back, then preloads (ContentProvider:PreloadAsync) everything
--          those pieces and opts.sets use: meshes, textures, SurfaceAppearances, decals, clothes, sounds, animations,
--          particles, beams, images (one instance per asset id);
--       3. returns when it's all in, or at the timeout.
--     opts: key = string (the keep's name), points = { Vector3 }, names = { piece names }, sets = { Instance } (the
--           film's cast, props, kit, sound library; Sound and Animation objects too), anims = { ids }, sounds = { ids },
--           timeout = s, keepFor = s (the keep's safety net, default 120)
--     warm: { ok (all in before the timeout), waited (s), assets (n instances preloaded), pieces ({ Instance }),
--             release() (the keep ends) }
--     Hand it to play as opts.pre and play releases it at stop.
--     Mesh detail: a game script can't change a MeshPart's RenderFidelity ("Cannot change SolidModel RenderFidelity
--     during Run-Time"), so a film's hero meshes are set Precise in Edit, on the kit (the zombies helicopters are).
--   CineKit.gameplay(look?) -> (CFrame, fov)   where the game's camera will sit: first person at the head; third person
--     (ThirdPerson) at ShoulderCam's hip offset (right 2.5, up 0.6, back 8)
--   CineKit.handheld(cf, k, w), CineKit.kickCF(cf, amp, age), CineKit.ease(u), CineKit.lerp(a, b, u)
-- While a scene runs: CameraType Scriptable, FieldOfViewMode Vertical, and LocalPlayer LoadoutOpen = true (ShoulderCam
-- and its watchdog let go of the camera, the hands and guns hold still, no menu opens); all put back after.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ContentProvider = game:GetService("ContentProvider")
local okKeep, CullKeep = pcall(function() return require(script.Parent:WaitForChild("CullKeep", 5) :: ModuleScript) end)
if not okKeep then CullKeep = nil end

local me = Players.LocalPlayer
local K = {}
K.BAR = 0.105
K.ORDER = 45 -- (under the finishers' 46)

function K.ease(u: number): number
	u = math.clamp(u, 0, 1)
	return u * u * (3 - 2 * u)
end
local function easeOut(u: number): number u = math.clamp(u, 0, 1); return 1 - (1 - u) * (1 - u) end
function K.lerp(a: number, b: number, u: number): number return a + (b - a) * u end

-- the finishers' handheld: t = w * 7
function K.handheld(cf: CFrame, k: number, w: number): CFrame
	if k <= 0 then return cf end
	local t = w * 7
	local n = math.noise
	return cf * CFrame.new(n(t, 1.3) * 0.05 * k, n(t, 2.7) * 0.05 * k, 0) * CFrame.Angles(math.rad(n(t, 4.1) * 0.5 * k), math.rad(n(t, 5.9) * 0.5 * k), 0)
end
-- the finishers' hit kick, for 0.3 s after a hit
function K.kickCF(cf: CFrame, amp: number, age: number): CFrame
	if age < 0 or age > 0.3 then return cf end
	local a = amp * math.exp(-age * 16) * math.sin(age * 55)
	return cf * CFrame.new(0, 0.05 * a, 0) * CFrame.Angles(0, 0, math.rad(1.1 * a))
end

-- the bars: one ScreenGui, driven every frame (smoothstep between where they are and where they're going)
local gui: ScreenGui? = nil
local top: Frame?, bottom: Frame? = nil, nil
local bk, bFrom, bTo, bT0, bDur = 0, 0, 0, 0, 0.2
local function ensure()
	if gui and gui.Parent then return end
	local g = Instance.new("ScreenGui")
	g.Name = "CineBars"; g.IgnoreGuiInset = true; g.ResetOnSpawn = false; g.DisplayOrder = K.ORDER
	local function bar(name: string, y: number, ay: number): Frame
		local f = Instance.new("Frame")
		f.Name = name; f.BackgroundColor3 = Color3.new(0, 0, 0); f.BorderSizePixel = 0
		f.AnchorPoint = Vector2.new(0, ay); f.Position = UDim2.fromScale(0, y); f.Size = UDim2.fromScale(1, 0)
		f.Parent = g
		return f
	end
	top = bar("Top", 0, 0); bottom = bar("Bottom", 1, 1)
	g.Parent = me:WaitForChild("PlayerGui")
	gui = g
	RunService.RenderStepped:Connect(function()
		local u = if bDur <= 0 then 1 else math.clamp((os.clock() - bT0) / bDur, 0, 1)
		bk = bFrom + (bTo - bFrom) * K.ease(u)
		local h = K.BAR * bk
		if top then top.Size = UDim2.fromScale(1, h) end
		if bottom then bottom.Size = UDim2.fromScale(1, h) end
		if gui then gui.Enabled = bk > 0.001 end
	end)
end
function K.bars(on: boolean, dur: number?)
	ensure()
	bFrom, bTo, bT0, bDur = bk, if on then 1 else 0, os.clock(), dur or 0.2
end

local fov0 = 70 -- (the gameplay FOV, read when a scene starts)
function K.gameplay(look: Vector3?): (CFrame, number)
	local cam = workspace.CurrentCamera
	local ch = me.Character
	local head = ch and (ch:FindFirstChild("Head") or ch:FindFirstChild("HumanoidRootPart")) :: BasePart?
	if not head then return cam.CFrame, fov0 end
	local l = look or cam.CFrame.LookVector
	if l.Magnitude < 1e-3 then l = Vector3.new(0, 0, -1) end
	local cf = CFrame.lookAt(head.Position, head.Position + l.Unit)
	if me:GetAttribute("ThirdPerson") == true then cf = cf * CFrame.new(2.5, 0.6, 8) end -- (ShoulderCam's hip)
	return cf, fov0
end

local function val(v: any): any
	if type(v) == "function" then return v() end
	return v
end
local function easeOf(name: string?, u: number): number
	if name == "out" then return easeOut(u) elseif name == "linear" then return math.clamp(u, 0, 1) end
	return K.ease(u)
end

-- ------------------------------------------------------------------ prewarm
-- the properties that name content, per class (read in a pcall: some can't be read by a script; such an instance goes
-- on the list whole)
local CONTENT: { [string]: { string } } = {
	MeshPart = { "MeshId", "TextureID" }, SpecialMesh = { "MeshId", "TextureId" }, FileMesh = { "MeshId", "TextureId" },
	SurfaceAppearance = { "ColorMap", "NormalMap", "RoughnessMap", "MetalnessMap" },
	Decal = { "Texture" }, Texture = { "Texture" }, Sound = { "SoundId" }, Animation = { "AnimationId" },
	ParticleEmitter = { "Texture" }, Beam = { "Texture" }, Trail = { "Texture" },
	ImageLabel = { "Image" }, ImageButton = { "Image" },
	Shirt = { "ShirtTemplate" }, Pants = { "PantsTemplate" }, ShirtGraphic = { "Graphic" },
}
local function gather(roots: { Instance }): { Instance }
	local seen: { [string]: boolean } = {}
	local list: { Instance } = {}
	local function one(d: Instance)
		local props = CONTENT[d.ClassName]
		if not props then return end
		local fresh, unread = false, false
		for _, pn in props do
			local ok, v = pcall(function() return (d :: any)[pn] end)
			if not ok then unread = true
			elseif type(v) == "string" and v ~= "" and not seen[v] then seen[v] = true; fresh = true end
		end
		if fresh or unread then table.insert(list, d) end
	end
	for _, r in roots do
		one(r)
		for _, d in r:GetDescendants() do one(d) end
	end
	return list
end
-- where a shot's camera is and what it looks at, at u
local function spots(s: any, u: number, out: { Vector3 })
	local ok, cf = pcall(function(): CFrame?
		if s.cam then return s.cam(u) end
		local a, b = s.from, s.to
		if not a then return nil end
		local fa, la = val(a.at), val(a.look)
		if b == "gameplay" then
			local g = K.gameplay()
			return CFrame.lookAt(fa:Lerp(g.Position, u), la:Lerp(g.Position + g.LookVector * 10, u))
		end
		return CFrame.lookAt(fa:Lerp(val(b.at), u), la:Lerp(val(b.look), u))
	end)
	if ok and typeof(cf) == "CFrame" then
		table.insert(out, cf.Position)
		table.insert(out, cf.Position + cf.LookVector * 80) -- (a long lens sees past the margin round the lens itself)
	end
end
local warmN = 0
function K.prewarm(shots: { any }?, opts: any?): any
	opts = opts or {}
	warmN += 1
	local key = opts.key or ("CineKitWarm" .. warmN)
	local t0 = os.clock()
	local pts: { Vector3 } = table.clone(opts.points or {})
	for _, s in shots or {} do for _, u in { 0, 0.5, 1 } do spots(s, u, pts) end end
	local warm: any = { ok = false, waited = 0, assets = 0, pieces = {}, key = key }
	if CullKeep then
		(CullKeep :: any).keep(key, { names = opts.names, points = pts, seconds = opts.keepFor or 120 })
		RunService.PreRender:Wait(); RunService.PreRender:Wait() -- (ZoneCull steps in PreRender: the pieces are back)
		warm.pieces = (CullKeep :: any).pieces(pts, opts.names)
	end
	local roots: { Instance } = table.clone(warm.pieces)
	for _, x in opts.sets or {} do table.insert(roots, x) end
	for _, id in opts.anims or {} do local a = Instance.new("Animation"); a.AnimationId = id; table.insert(roots, a) end
	for _, id in opts.sounds or {} do local a = Instance.new("Sound"); a.SoundId = id; table.insert(roots, a) end
	local list = gather(roots)
	warm.assets = #list
	local done = false
	task.spawn(function()
		pcall(function() ContentProvider:PreloadAsync(list) end)
		done = true
	end)
	local timeout = opts.timeout or 4
	while not done and os.clock() - t0 < timeout do RunService.Heartbeat:Wait() end
	warm.ok = done
	warm.waited = os.clock() - t0
	warm.release = function()
		if CullKeep then (CullKeep :: any).release(key) end
	end
	return warm
end

export type Run = { stop: (boolean?) -> (), kick: (number) -> (), shot: string?, done: boolean }
-- the game's camera follows your current body (27 Nov: a round re-made the body while the scene played, and the camera
-- went on following the old one for half a second after the hand-back, until ShoulderCam's watchdog put it right)
local function subject(cam: Camera)
	local ch = me.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	if hum and cam.CameraSubject ~= hum then cam.CameraSubject = hum end
end

local n = 0
function K.play(shots: { any }, opts: any?): Run
	opts = opts or {}
	n += 1
	local key = "CineKit" .. n
	local cam = workspace.CurrentCamera
	local start = os.clock()
	local clock: () -> number = opts.clock or function() return os.clock() - start end
	local was = { mode = cam.FieldOfViewMode, fov = cam.FieldOfView, open = me:GetAttribute("LoadoutOpen"), flag = me:GetAttribute("Finishing") }
	fov0 = cam.FieldOfView
	me:SetAttribute("LoadoutOpen", true)
	if opts.flag then me:SetAttribute("Finishing", opts.flag) end
	cam.FieldOfViewMode = Enum.FieldOfViewMode.Vertical
	cam.CameraType = Enum.CameraType.Scriptable
	local run: Run = { stop = function() end, kick = function() end, shot = nil, done = false }
	local kickAt, kickAmp = -1e9, 0
	run.kick = function(amp: number) kickAt, kickAmp = clock(), amp end
	local function frame(t: number): (CFrame, number?)
		local s: any = nil
		for _, x in shots do if t >= x.t0 and t < x.t1 then s = x; break end end
		local past = 0
		if not s then
			local last = shots[#shots]
			if t >= last.t1 then s = last; past = t - last.t1 else s = shots[1] end
		end
		local u = math.clamp((t - s.t0) / math.max(1e-3, s.t1 - s.t0), 0, 1)
		run.shot = s.name
		local cf: CFrame, fov: number?
		if s.cam then
			cf = s.cam(u)
			fov = if type(s.fov) == "function" then s.fov(u) else s.fov
		else
			local e = easeOf(s.ease, u)
			local a = s.from
			local fa, la = val(a.at), val(a.look)
			local fb: Vector3, lb: Vector3, vb: number?
			if s.to == "gameplay" then
				local g, gf = K.gameplay(if s.look then val(s.look) else nil)
				fb, lb, vb = g.Position, g.Position + g.LookVector * 10, gf
			else
				fb, lb, vb = val(s.to.at), val(s.to.look), s.to.fov
			end
			cf = CFrame.lookAt(fa:Lerp(fb, e), la:Lerp(lb, e))
			if a.fov or vb then fov = K.lerp(a.fov or vb, vb or a.fov, e) end
		end
		if s.roll then cf = cf * CFrame.Angles(0, 0, math.rad(s.roll)) end
		local k = if type(s.shake) == "function" then s.shake(u) elseif type(s.shake) == "number" then s.shake else 0
		cf = K.handheld(cf, k, t)
		if past > 0 and opts.hold then cf = cf * CFrame.new(0, 0, past * opts.hold) end
		return K.kickCF(cf, kickAmp, t - kickAt), fov
	end
	local endT = shots[#shots].t1
	RunService:BindToRenderStep(key, Enum.RenderPriority.Last.Value + 80, function()
		if run.done then return end
		local t = clock()
		local cf, fov = frame(t)
		-- (the 27 Nov test: Custom straight after Scriptable showed a stale frame of where you'd been for half a second)
		local warm = opts.warm and t >= endT - opts.warm
		if warm then subject(cam) end
		cam.CameraType = if warm then Enum.CameraType.Custom else Enum.CameraType.Scriptable
		cam.CFrame = cf
		if fov then cam.FieldOfView = fov end
	end)
	run.stop = function(handBack: boolean?)
		if run.done then return end
		run.done = true
		pcall(function() RunService:UnbindFromRenderStep(key) end)
		local g, gf = K.gameplay(cam.CFrame.LookVector)
		cam.FieldOfViewMode = was.mode
		cam.FieldOfView = if handBack then gf else was.fov
		subject(cam)
		cam.CameraType = Enum.CameraType.Custom
		if handBack then cam.CFrame = g end
		me:SetAttribute("LoadoutOpen", was.open)
		if opts.flag and me:GetAttribute("Finishing") == opts.flag then me:SetAttribute("Finishing", was.flag) end
		if opts.pre and opts.pre.release then opts.pre.release() end
	end
	return run
end

return K
