--!strict
-- ANIME WEAPON EFFECTS (the VFX session, 26 Nov 2026; roblox/docs/VFX-PIPELINE.md "Anime weapon effects").
-- The owner: "better vfx in anime style, especially applied to weapons ... don't use too many meshes, you usually end up
-- making things look too geometric". So the shapes are Blender-rendered FLIPBOOKS (tools/roblox/vfx/anime/: slash_bl.py,
-- burst_bl.py), played by camera-facing particles; sparks, the twinkle and the impact frame are code.
-- Each flipbook comes in three layers rendered from the same timing, played together from one part:
--   body  greyscale, tinted per weapon: painted once underneath (LightEmission 0, so the colour survives on bright
--         floors) and added once on top
--   core  white-hot, added, untinted
--   ink   black accents, painted over (the two-tone anime look)
-- Slashes come in takes (arc length, tilt) and MIRRORED copies: a particle can't flip its texture, so the mirror is
-- what makes a right-to-left swing bulge the right way.
-- Nothing here is server-side or replicated: every client draws its own (as Fx does).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Lighting = game:GetService("Lighting")

local AnimeFx = {}
AnimeFx.ON = true -- the switch: false = the old katana smear and blast (on since the real swing test, 26 Nov 2026)
-- (tests: the workspace attribute AnimeFxOn = true / false flips the game's own copy; a require from the command bar
-- makes a second copy, so setting .ON there does nothing to the game's swings)
workspace:GetAttributeChangedSignal("AnimeFxOn"):Connect(function()
	local v = workspace:GetAttribute("AnimeFxOn")
	if type(v) == "boolean" then AnimeFx.ON = v end
end)
AnimeFx.LAB = false -- (the VFX lab sets this while it's open, so its effects play whatever ON says)
local function on(): boolean return AnimeFx.ON or AnimeFx.LAB end

-- the sheets (Open Cloud Image uploads; roblox/assets/vfx/anime.json). 4x4, 16 frames each
local SHEET: { [string]: { body: string, core: string, ink: string, painted: boolean? } } = {
	-- (26 Nov, round 2: the 2D slash, tools/roblox/vfx/anime/slash2d.py, PAINTED and coloured as drawn. In game the Blender
	-- slashes below read as "ghostly pale arcs" (critic 4/10 on a bright range): their additive layers washed out)
	slashp_a = { body = "rbxassetid://77470245818189", core = "rbxassetid://93851108583013", ink = "rbxassetid://81460246049124", painted = true },
	slashp_am = { body = "rbxassetid://75098402989510", core = "rbxassetid://71759742261612", ink = "rbxassetid://129004925303226", painted = true },
	slashp_b = { body = "rbxassetid://90217798948554", core = "rbxassetid://86605588801701", ink = "rbxassetid://106824240148137", painted = true },
	slashp_bm = { body = "rbxassetid://101404556384510", core = "rbxassetid://82610822665793", ink = "rbxassetid://73977337423245", painted = true },
	slashp_c = { body = "rbxassetid://72266209960048", core = "rbxassetid://81038759370416", ink = "rbxassetid://133033911652012", painted = true },
	slashp_cm = { body = "rbxassetid://118352474362616", core = "rbxassetid://75369352645691", ink = "rbxassetid://83743603576657", painted = true },
	slash_a = { body = "rbxassetid://131328627718726", core = "rbxassetid://105994308718339", ink = "rbxassetid://86693392108149" },
	slash_am = { body = "rbxassetid://138390481481344", core = "rbxassetid://74640920777631", ink = "rbxassetid://132308172645988" },
	slash_b = { body = "rbxassetid://134583722484506", core = "rbxassetid://123596133069102", ink = "rbxassetid://137331711989662" },
	slash_bm = { body = "rbxassetid://138610398019082", core = "rbxassetid://75508282178711", ink = "rbxassetid://121170316045394" },
	slash_c = { body = "rbxassetid://130800394321007", core = "rbxassetid://81831698484670", ink = "rbxassetid://139248969243044" },
	slash_cm = { body = "rbxassetid://124835024292822", core = "rbxassetid://91121143458818", ink = "rbxassetid://121155273304143" },
	burst_a = { body = "rbxassetid://82691384021546", core = "rbxassetid://72312195768018", ink = "rbxassetid://119992340179461" },
	-- (27 Nov: the 2D hit burst, tools/roblox/vfx/anime/burst2d.py, painted: the Blender burst_a above read 4/10 in game,
	-- "a soft, translucent swirl of white-blue arcs ... ghostly feathers")
	burstp_a = { body = "rbxassetid://113445278597671", core = "rbxassetid://124878193183318", ink = "rbxassetid://120220254753645", painted = true },
}
AnimeFx.SHEET = SHEET
local SPARKLE = "rbxassetid://118739981349944" -- four points (Fx's sparkle)
-- the sparks (tools/roblox/vfx/anime/spark2d.py, drawn vertically, the sharp head up): a tinted RIM shard and a white
-- CORE inside it, painted. (26 Nov round 2: the soft stadiums, 73042129135061, read as "white leaves, rice grains or
-- feathers"; round 2's additive comet, 82553508731703, as "thin, pale, see-through hairs ... scratches")
local SPARK_RIM = "rbxassetid://129820872226047"
local SPARK_CORE = "rbxassetid://70674633185085"

-- a OneShot flipbook plays over the particle's Lifetime (measured 26 Nov 2026, v1372; FlipbookFramerate is ignored):
-- the lifetime IS the speed. The slash in 0.42 s, the burst in 0.34 s (the critic's timing)
local FRAMES = 16
local FPS = 30
local LIFE = FRAMES / FPS
local LIFE_OF: { [string]: number } = { slash = 0.42, slashp = 0.42, burst = 0.34, burstp = 0.34 }

local me = Players.LocalPlayer
local folder = Instance.new("Folder")
folder.Name = "JankAnimeFx"
folder.Parent = workspace

-- slow motion and freeze for the lab and for photos: every emitter's TimeScale, and the code-driven bits' clock
local TS = 1
function AnimeFx.setTimeScale(k: number)
	TS = math.clamp(k, 0, 1)
	for _, d in folder:GetDescendants() do
		if d:IsA("ParticleEmitter") then d.TimeScale = TS end
	end
end
function AnimeFx.timeScale(): number return TS end
-- (photos and tests: the workspace attribute AnimeFxTimeScale reaches this copy from anywhere, as FxTimeScale does Fx)
workspace:GetAttributeChangedSignal("AnimeFxTimeScale"):Connect(function()
	local v = workspace:GetAttribute("AnimeFxTimeScale")
	AnimeFx.setTimeScale(if type(v) == "number" then v else 1)
end)

local function holder(cf: CFrame): Part
	local p = Instance.new("Part")
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Transparency = 1
	p.Size = Vector3.new(0.2, 0.2, 0.2)
	p.CFrame = cf
	-- (27 Nov 2026) the layers emit from one Attachment, a point: a part's emitter spawns each particle at a random spot
	-- inside the part, so the body, core and ink of one slash landed up to 0.1 stud apart (a 10-17 px gap in first person)
	local at = Instance.new("Attachment")
	at.Name = "At"
	at.Parent = p
	p.Parent = folder
	return p
end

-- a part lives until its longest particle is gone, on the effect clock (so a frozen lab effect stays)
local live: { { p: Instance, left: number, follow: ((Part) -> ())? } } = {}
local function keep(p: Part, life: number, follow: ((Part) -> ())?)
	table.insert(live, { p = p, left = life + 0.1, follow = follow })
end
RunService.RenderStepped:Connect(function(dt)
	for i = #live, 1, -1 do
		local e = live[i]
		e.left -= dt * TS
		if e.follow and e.p.Parent then e.follow(e.p :: Part) end
		if e.left <= 0 or not e.p.Parent then
			if e.p.Parent then e.p:Destroy() end
			table.remove(live, i)
		end
	end
end)

local function ns(...: number): NumberSequence
	local a = { ... }
	local k = {}
	for i = 1, #a, 2 do table.insert(k, NumberSequenceKeypoint.new(a[i], a[i + 1])) end
	return NumberSequence.new(k)
end

-- one flipbook layer: a camera-facing one-shot particle of the whole sheet. Every layer of one effect gets the same
-- size, rotation and life, so they play in step
local function layer(p: Part, tex: string, color: Color3, le: number, z: number, size: NumberSequence, rot: number, alpha: number, locked: boolean, life: number)
	local e = Instance.new("ParticleEmitter")
	e.Texture = tex
	e.Enabled = false
	-- (27 Nov 2026, turn 4: FlipbookBlendFrames is on by default and cross-fades each frame into the next, so a cel
	-- frame shows two drawings half see-through: the "soft, translucent" slash, its "feathered" inner edge and the
	-- doubled ink in the v1409 captures. Cel frames step)
	pcall(function() (e :: any).FlipbookBlendFrames = false end)
	e.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
	e.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
	e.FlipbookFramerate = NumberRange.new(FRAMES / life)
	e.FlipbookStartRandom = false
	e.Lifetime = NumberRange.new(life)
	e.Speed = NumberRange.new(0)
	e.Rotation = NumberRange.new(rot)
	e.RotSpeed = NumberRange.new(0)
	e.Size = size
	e.Transparency = NumberSequence.new(1 - alpha)
	e.Color = ColorSequence.new(color)
	e.LightEmission = le
	e.LightInfluence = 0
	e.Brightness = 1
	e.ZOffset = z
	e.Orientation = Enum.ParticleOrientation.FacingCamera
	e.LockedToPart = locked
	e.TimeScale = TS
	e.Parent = p:FindFirstChild("At") or p
	e:Emit(1)
end

-- the three layers of `sheet` at cf: size = the particle's Size (half its width in studs); rot in degrees
-- o.push: the effect grows from 92 % to full over its first quarter (a slash's hold pushes forward instead of sitting)
local function flipbook(sheet: string, cf: CFrame, size: number, rot: number, tint: Color3, o: { follow: ((Part) -> ())?, under: number?, push: boolean?, z: number? }?): Part?
	local s = SHEET[sheet]
	if not s then return nil end
	local p = holder(cf)
	local locked = o ~= nil and o.follow ~= nil
	local sz = if o and o.push then ns(0, size * 0.92, 0.31, size, 1, size) else NumberSequence.new(size) -- (0.13 s of 0.42)
	-- (a warm tint is added at 0.45: red clips first, so orange turned lemon on a grey floor; the painted pass carries the hue)
	local add = if tint.R > tint.B + 0.08 then 0.45 else 1
	local life = LIFE_OF[string.match(sheet, "^(%a+)_") or ""] or LIFE
	local z0 = (o and o.z) or 0
	if s.painted then
		-- (a white body that takes the weapon's tint, the white core and the ink, all painted: one opaque cel shape)
		layer(p, s.body, tint, 0, z0, sz, rot, 1, locked, life)
		layer(p, s.core, Color3.new(1, 1, 1), 0, z0 + 0.05, sz, rot, 1, locked, life)
		layer(p, s.ink, Color3.new(0, 0, 0), 0, z0 + 0.1, sz, rot, 1, locked, life)
	else
		layer(p, s.body, tint, 0, 0, sz, rot, (o and o.under) or 0.7, locked, life) -- painted under: the colour on bright floors
		layer(p, s.body, tint, 1, 0.05, sz, rot, add, locked, life)
		layer(p, s.core, Color3.new(1, 1, 1), 1, 0.1, sz, rot, 1, locked, life)
		layer(p, s.ink, Color3.new(0, 0, 0), 0, 0.15, sz, rot, 0.95, locked, life)
	end
	keep(p, life, o and o.follow)
	return p
end
AnimeFx.flipbook = flipbook

-- ---------------------------------------------------------------- the slash
-- The sheets are drawn with the swing running up the right side of the cell (from the bottom, bulging to the right).
-- dir2 is the swing's direction ON SCREEN (x right, y up); bulgeRight says which side of that direction the arc
-- bulges to (the mirrored sheet bulges left). ROT_SIGN turns maths angles (anticlockwise) into a particle's Rotation:
-- +1, because a particle's positive Rotation turns it ANTICLOCKWISE on screen (seen 26 Nov 2026 in two Studio captures:
-- the v1372 stage slashes bulged up instead of down, and a side-wall bullet pop opened the wrong way; it was -1)
local ROT_SIGN = 1
AnimeFx.TAKES = { "slashp_a", "slashp_b", "slashp_c" } -- (the Blender takes: slash_a, slash_b, slash_c)
local takeN = 0
function AnimeFx.slash(cf: CFrame, dir2: Vector2, bulgeRight: boolean, size: number, tint: Color3, o: { take: string?, follow: ((Part) -> ())? }?)
	if not on() then return end
	local take = o and o.take
	if not take then
		takeN = takeN % #AnimeFx.TAKES + 1
		take = AnimeFx.TAKES[takeN]
	end
	local sheet = (take :: string) .. (if bulgeRight then "" else "m")
	local ang = math.deg(math.atan2(dir2.Y, dir2.X)) - 90 -- the sheet's own swing runs straight up
	flipbook(sheet, cf, size, ROT_SIGN * ang, tint, { follow = o and o.follow, push = true })
end

-- ---------------------------------------------------------------- the hit
-- how far to draw a hit's effects towards the camera (ZOffset, studs): 2, or less when the hit is close to the lens
function AnimeFx.nearZ(at: Vector3): number
	local cam = workspace.CurrentCamera
	if not cam then return 0 end
	return math.clamp((cam.CFrame.Position - at).Magnitude - 0.6, 0, 2)
end
function AnimeFx.burst(at: Vector3, size: number, tint: Color3, rot: number?, sheet: string?)
	if not on() then return end
	-- (turn 4: drawn up to 2 studs nearer the camera (ZOffset keeps its size on screen). Inside a body it faded where it
	-- met the body and read pale and see-through on the dummy; never past 0.6 studs from the lens)
	flipbook(sheet or "burstp_a", CFrame.new(at), size, rot or math.random(0, 359), tint, { under = 0.6, z = AnimeFx.nearZ(at) })
end

-- sparks: velocity-stretched streaks off the hit, white-hot heads into the tint, with a little gravity
-- (SPARK_ROT: the turn that puts the comet's head forward along its flight under VelocityParallel; the workspace
-- attribute AnimeFxSparkRot overrides it for tests)
local SPARK_ROT = 0
workspace:GetAttributeChangedSignal("AnimeFxSparkRot"):Connect(function()
	local v = workspace:GetAttribute("AnimeFxSparkRot")
	SPARK_ROT = if type(v) == "number" then v else 0
end)
local sparkRng = Random.new()
function AnimeFx.sparks(at: Vector3, dir: Vector3, n: number, tint: Color3, speed: number?)
	if not on() or n <= 0 then return end
	local d = if dir.Magnitude > 1e-3 then dir.Unit else Vector3.yAxis
	local p = holder(CFrame.new(at))
	local att = p:FindFirstChild("At") :: Attachment
	-- (27 Nov, round 3: two painted emitters, the tinted rim shard and the white core inside it, fed ONE spark at a
	-- time with the same direction, speed and life, so each core rides inside its rim; they shrink out, never fade)
	local function em(tex: string, col: Color3, z: number): ParticleEmitter
		local e = Instance.new("ParticleEmitter")
		e.Texture = tex
		e.Enabled = false
		e.Orientation = Enum.ParticleOrientation.VelocityParallel
		e.Rotation = NumberRange.new(SPARK_ROT)
		e.EmissionDirection = Enum.NormalId.Front
		e.SpreadAngle = Vector2.zero
		e.Drag = 4
		e.Acceleration = Vector3.new(0, -20, 0)
		e.Size = ns(0, 0.54, 0.55, 0.45, 1, 0) -- (v1423's critic: 1.5x, they were too small to read past the burst)
		e.Transparency = NumberSequence.new(0)
		e.Color = ColorSequence.new(col)
		e.LightEmission = 0
		e.LightInfluence = 0
		e.ZOffset = z
		e.TimeScale = TS
		e.Parent = att
		return e
	end
	local z0 = AnimeFx.nearZ(at) -- (turn 4: as the burst, nearer the camera, or they fade into the body they leave)
	local rim, core = em(SPARK_RIM, tint, z0), em(SPARK_CORE, Color3.new(1, 1, 1), z0 + 0.05)
	-- (round 2: they flew ~8 studs and past the camera; now under 3: v / drag x (1 - e^(-drag t)))
	local sp = speed or 12
	local base = CFrame.lookAt(Vector3.zero, d)
	for _ = 1, n do
		-- a direction in a 35 degree cone round d (the attachment's front), a speed and a life, the same for both
		local spin, tilt = sparkRng:NextNumber(0, math.pi * 2), math.rad(35) * math.sqrt(sparkRng:NextNumber())
		att.CFrame = base * CFrame.Angles(0, 0, spin) * CFrame.Angles(tilt, 0, 0)
		local s = NumberRange.new(sp * sparkRng:NextNumber(0.75, 1.15))
		local l = NumberRange.new(sparkRng:NextNumber(0.18, 0.28))
		rim.Speed, core.Speed = s, s
		rim.Lifetime, core.Lifetime = l, l
		rim:Emit(1)
		core:Emit(1)
	end
	keep(p, 0.35)
end

-- the twinkle: a four-point star that pops and shrinks, turning a little
function AnimeFx.twinkle(at: Vector3, size: number, tint: Color3?)
	if not on() then return end
	local p = holder(CFrame.new(at))
	local e = Instance.new("ParticleEmitter")
	e.Texture = SPARKLE
	e.Enabled = false
	e.Speed = NumberRange.new(0)
	e.Lifetime = NumberRange.new(0.22)
	e.Size = ns(0, size * 0.4, 0.15, size, 1, 0)
	e.Rotation = NumberRange.new(math.random(-12, 12))
	e.RotSpeed = NumberRange.new(90)
	e.Transparency = ns(0, 0, 0.7, 0, 1, 1)
	e.Color = ColorSequence.new(Color3.new(1, 1, 1):Lerp(tint or Color3.new(1, 1, 1), 0.25))
	e.LightEmission = 1
	e.LightInfluence = 0
	e.ZOffset = 0.3
	e.TimeScale = TS
	e.Parent = p
	e:Emit(1)
	keep(p, 0.3)
end

-- the impact frame: two frames of high-contrast black and white on YOUR OWN heavy hits and kills only (Settings >
-- SCREEN SHAKE off turns it off too). ~0.07 s in all
local cc: ColorCorrectionEffect? = nil
local ccUntil = 0
function AnimeFx.impactFrame(allowed: boolean?)
	if not on() or allowed == false then return end
	if not cc or not cc.Parent then
		local c = Instance.new("ColorCorrectionEffect")
		c.Name = "AnimeImpactFrame"
		c.Enabled = false
		c.Parent = Lighting
		cc = c
	end
	local c = cc :: ColorCorrectionEffect
	c.Saturation = -1
	c.Contrast = 0.9
	c.Brightness = 0.08
	c.TintColor = Color3.new(1, 1, 1)
	c.Enabled = true
	ccUntil = os.clock() + 0.07
	task.delay(0.035, function() if c.Parent then c.Contrast = 0.45; c.Brightness = 0.02 end end)
	task.delay(0.075, function() if os.clock() >= ccUntil and c.Parent then c.Enabled = false end end)
end

-- ---------------------------------------------------------------- placing a slash for a swing
-- where a swing is on screen: the camera's view of a world direction (x right, y up)
function AnimeFx.screenDir(world: Vector3): Vector2
	local cam = workspace.CurrentCamera
	if not cam then return Vector2.new(1, 0) end
	local cf = cam.CFrame
	local v = Vector2.new(world:Dot(cf.RightVector), world:Dot(cf.UpVector))
	return if v.Magnitude > 1e-4 then v.Unit else Vector2.new(1, 0)
end

-- your own swing in first person: the blade tip's path sampled in camera space (the viewmodel's smear window) gives
-- the direction and which way the path curves; the slash then rides with the camera for its life
function AnimeFx.ownSlash(pts: { Vector3 }, tint: Color3, size: number?)
	if not on() or #pts < 3 then return end
	local cam = workspace.CurrentCamera
	if not cam then return end
	local p0, p1, p2 = pts[1], pts[math.ceil(#pts / 2)], pts[#pts]
	local function scr(v: Vector3): Vector2 return Vector2.new(v.X / -math.min(v.Z, -0.6), v.Y / -math.min(v.Z, -0.6)) end
	local s0, s1, s2 = scr(p0), scr(p1), scr(p2)
	local d = s2 - s0
	if d.Magnitude < 1e-3 then return end
	local a, b = s1 - s0, s2 - s1
	local turnLeft = a.X * b.Y - a.Y * b.X > 0 -- an anticlockwise path bulges to the right of its direction
	local depth = 3.2
	local mid = (s0 + s2) / 2 + (s1 - (s0 + s2) / 2) * 0.6
	-- (the real swing, 26 Nov: the katana's tip starts low and close to the lens, so its path's middle projected off the
	-- bottom-left of the screen; the slash stays near the middle of the view, leaning towards the path)
	mid = Vector2.new(math.clamp(mid.X * 0.5, -0.3, 0.3), math.clamp(mid.Y * 0.5, -0.22, 0.22))
	local off = CFrame.new(mid.X * depth, mid.Y * depth, -depth)
	AnimeFx.slash(cam.CFrame * off, d.Unit, turnLeft, size or 1.7, tint, {
		follow = function(part: Part)
			local c = workspace.CurrentCamera
			if c then part.CFrame = c.CFrame * off end
		end,
	})
end

-- someone else's swing (or yours in third person): in front of their body, along their right (alt = back the other way)
function AnimeFx.bodySlash(root: BasePart, look: Vector3, alt: boolean, reach: number, tint: Color3)
	if not on() then return end
	local flat = Vector3.new(look.X, 0, look.Z)
	flat = if flat.Magnitude > 1e-3 then flat.Unit else root.CFrame.LookVector
	local right = flat:Cross(Vector3.yAxis)
	local swing = (if alt then -right else right) + Vector3.new(0, -0.25, 0)
	local at = root.Position + flat * reach * 0.45 + Vector3.new(0, 0.6, 0)
	local d2 = AnimeFx.screenDir(swing)
	-- the arc bulges away from the body: towards `flat` on screen
	local away = AnimeFx.screenDir(flat + Vector3.new(0, 0.3, 0))
	local bulgeRight = (d2.X * away.Y - d2.Y * away.X) < 0
	AnimeFx.slash(CFrame.new(at), d2, bulgeRight, reach * 0.42, tint)
end

-- ---------------------------------------------------------------- the library (game-vfx, CC0)
-- Six of the twelve CC0 flipbooks from the game-vfx library (github.com/rehan/game-vfx; its art is CC0, the clone stays
-- in the vault), repacked to 4x4 at 1024 by tools/roblox/vfx/anime/repack.py. Painted-realistic, NOT anime: here for
-- the lab, to compare and to pick from for later effects (a rocket's blast, the taser's arc). Coloured as drawn, one layer
local LIB: { [string]: { tex: string, life: number, glow: boolean } } = {
	gvfx_fire = { tex = "rbxassetid://110525931857378", life = 0.7, glow = true },
	gvfx_smoke = { tex = "rbxassetid://84631229333766", life = 1.2, glow = false },
	gvfx_lightning = { tex = "rbxassetid://139625511854822", life = 0.5, glow = true },
	gvfx_explosion = { tex = "rbxassetid://96414523197432", life = 1.0, glow = true },
	gvfx_frost = { tex = "rbxassetid://113478574429570", life = 0.8, glow = true },
	gvfx_arcane = { tex = "rbxassetid://128306984837395", life = 0.9, glow = true },
}
AnimeFx.LIB = LIB
function AnimeFx.lib(id: string, at: Vector3, size: number)
	local l = LIB[id]
	if not l then return end
	local p = holder(CFrame.new(at))
	layer(p, l.tex, Color3.new(1, 1, 1), if l.glow then 1 else 0, 0, NumberSequence.new(size), 0, 1, false, l.life)
	keep(p, l.life)
end

-- ---------------------------------------------------------------- the lab's list (VfxLab.client)
AnimeFx.LIST = {
	{ id = "slashp_a", label = "SLASH A (150)", kind = "slash" },
	{ id = "slashp_b", label = "SLASH B (125, thick)", kind = "slash" },
	{ id = "slashp_c", label = "SLASH C (185, thin)", kind = "slash" },
	{ id = "slash_a", label = "OLD BLENDER SLASH (additive)", kind = "slash" },
	{ id = "burstp_a", label = "HIT BURST", kind = "burst" },
	{ id = "burst_a", label = "OLD BLENDER BURST (additive)", kind = "burst" },
	{ id = "sparks", label = "SPARKS", kind = "sparks" },
	{ id = "twinkle", label = "TWINKLE", kind = "twinkle" },
	{ id = "hit", label = "FULL HIT (burst + sparks + twinkle)", kind = "hit" },
	{ id = "impact", label = "IMPACT FRAME", kind = "impact" },
	-- (the gun's anime flash and puff live in Fx; the lab fires Fx.muzzle at the spot, side-on or facing you)
	{ id = "muzzle_side", label = "MUZZLE FLASH + PUFF (side)", kind = "muzzle" },
	{ id = "muzzle_front", label = "MUZZLE FLASH (facing you)", kind = "muzzle" },
	{ id = "pop_floor", label = "BULLET HIT (floor, seen side-on)", kind = "bullet" },
	{ id = "pop_wall", label = "BULLET HIT (wall to the right)", kind = "bullet" },
	{ id = "gvfx_fire", label = "LIBRARY: FIRE BURST", kind = "lib" },
	{ id = "gvfx_explosion", label = "LIBRARY: BIG EXPLOSION", kind = "lib" },
	{ id = "gvfx_smoke", label = "LIBRARY: SMOKE BURST", kind = "lib" },
	{ id = "gvfx_lightning", label = "LIBRARY: LIGHTNING", kind = "lib" },
	{ id = "gvfx_frost", label = "LIBRARY: FROST", kind = "lib" },
	{ id = "gvfx_arcane", label = "LIBRARY: ARCANE", kind = "lib" },
}

-- each melee weapon's colour and how big its slash is drawn (a Size: half the width in studs; first person / bodies)
local TINT: { [string]: Color3 } = {
	-- (round 2: the katana saturated; its pale 150, 200, 255 washed out in game)
	katana = Color3.fromRGB(70, 160, 255), knife = Color3.fromRGB(200, 208, 222), scythe = Color3.fromRGB(62, 230, 200),
	claw = Color3.fromRGB(235, 70, 60), bread = Color3.fromRGB(240, 205, 150), slapper = Color3.fromRGB(255, 140, 190),
	slipper = Color3.fromRGB(255, 154, 213), scales = Color3.fromRGB(255, 200, 58),
}
local FP_SIZE: { [string]: number } = { katana = 1.7, knife = 1.35, scythe = 2.1, claw = 1.4, bread = 1.5, slapper = 1.3, scales = 1.8 }
local REACH: { [string]: number } = { katana = 9, knife = 8, scythe = 11, claw = 8, bread = 8, slapper = 7, scales = 10 }
function AnimeFx.tintFor(wid: string?, glow: Color3?): Color3
	return glow or (wid and TINT[wid]) or Color3.fromRGB(220, 225, 235)
end
function AnimeFx.fpSize(wid: string?): number return (wid and FP_SIZE[wid]) or 1.6 end
function AnimeFx.reach(wid: string?): number return (wid and REACH[wid]) or 8 end

-- the full melee hit, as Arsenal plays it: the burst and sparks; a heavy hit adds the twinkle, and your own heavy hit
-- the impact frame (frame = false: Settings > SCREEN SHAKE is off)
function AnimeFx.hit(at: Vector3, from: Vector3, tint: Color3, heavy: boolean, own: boolean, frame: boolean?)
	if not on() then return end
	local dir = at - from
	-- (the real swing, 26 Nov: the hit point is inside the body, which hid the burst: draw it on the side facing the camera)
	local cam = workspace.CurrentCamera
	if cam then
		local toCam = cam.CFrame.Position - at
		if toCam.Magnitude > 2.5 then at += toCam.Unit * 1.4 end
	end
	AnimeFx.burst(at, if heavy then 3.25 else 2.4, tint) -- (the sheet draws it at 80 %: its margins)
	-- (round 2: away from the camera and up, 5-7 of them; they flew back past the camera before)
	AnimeFx.sparks(at, (if dir.Magnitude > 1e-3 then dir.Unit else Vector3.zAxis) * 0.7 + Vector3.new(0, 0.7, 0), if heavy then 7 else 5, tint)
	if heavy then AnimeFx.twinkle(at + Vector3.new(0, 0.4, 0), 1.6, tint) end
	if own and heavy then AnimeFx.impactFrame(frame) end
end

function AnimeFx.clear()
	for _, e in live do if e.p.Parent then e.p:Destroy() end end
	table.clear(live)
end

return AnimeFx
