--!strict
-- ANIME WEAPON EFFECTS (the VFX session, 26 Nov 2026; roblox/docs/VFX-PIPELINE.md "Anime weapon effects").
-- The owner: "better vfx in anime style, especially applied to weapons ... don't use too many meshes, you usually end up
-- making things look too geometric". So the shapes are Blender-rendered FLIPBOOKS (tools/roblox/vfx/anime/: slash_bl.py,
-- burst_bl.py), played by camera-facing particles; sparks, the twinkle and the impact frame are code. Since 27 Nov a
-- melee swing is a SWEEP instead: a ribbon laid on the blade's own path (below, "the blade sweep").
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

-- ---------------------------------------------------------------- the blade sweep
-- (27 Nov 2026, the owner: "make sure the effects follow the plane of the weapon and katana for example, are attached
-- along the side of the blade". The crescent above floated as a card facing the lens; this ribbon is laid on the
-- blade's own path.) Every frame of a swing the blade's Mid (45 % along it) and tip (Muzzle) are sampled: in camera
-- space for your own first-person blade, so the ribbon rides with your view as the old smear did, or in the world for
-- a body seen from outside (its TPGun). A chain of flat Beams (FaceCamera off) runs through the samples, so the ribbon
-- lies in the plane the blade swept, its outer edge on the tip's path: seen from the side it is the swing's arc, not a
-- card. Every weapon's own Mid and Muzzle set its size (the katana's stretch moves its Muzzle). Two layers share the
-- beams' attachments, so they can't slip apart: the body (tinted, its inner edge an ink line, both in sweep2d.py's
-- texture) and the white core along the outer edge. Older samples thin towards the tip's path and fade (the crescent's
-- tail). A glint runs from Mid to the tip along the blade while it sweeps.
AnimeFx.STYLE = "blade" -- ("card": the camera-facing crescent of 26 Nov; the attribute AnimeFxStyle flips it for tests)
workspace:GetAttributeChangedSignal("AnimeFxStyle"):Connect(function()
	local v = workspace:GetAttribute("AnimeFxStyle")
	if v == "blade" or v == "card" then AnimeFx.STYLE = v end
end)
local SWEEP_BODY = "rbxassetid://119546036895646"
local SWEEP_CORE = "rbxassetid://79027786277985"
local SWEEP_LIFE = 0.16 -- a sample's life on the ribbon (seconds on the effect clock)
local SWEEP_MAX = 32
-- (seen in Studio 27 Nov on a test beam between two attachments: a non-facing Beam's width runs along its attachments'
-- Y axis; its texture's ROWS run along its length and its COLUMNS across its width, the image's left column on the
-- +Y edge. So sweep2d.py's cross-section runs left to right, outer edge first, and +Y must point to the outer edge:
-- the flip, as our Y points from the tip in to Mid. The attributes AnimeFxBeamAxis "Y"/"Z" and AnimeFxBeamFlip test)
local BEAM_AXIS = "Y"
local BEAM_FLIP = true
workspace:GetAttributeChangedSignal("AnimeFxBeamAxis"):Connect(function()
	local v = workspace:GetAttribute("AnimeFxBeamAxis")
	if v == "Y" or v == "Z" then BEAM_AXIS = v end
end)
workspace:GetAttributeChangedSignal("AnimeFxBeamFlip"):Connect(function()
	BEAM_FLIP = workspace:GetAttribute("AnimeFxBeamFlip") ~= false
end)

type Sample = { m: Vector3, t: Vector3, age: number }
type Sweep = { mid: Attachment, tip: Attachment, cam: boolean, tint: Color3, left: number, dur: number, el: number,
	samples: { Sample }, part: Part, atts: { Attachment }, body: { Beam }, core: { Beam }, glint: BillboardGui?,
	gImg: ImageLabel?, gAt: Attachment?, band: number, brk: boolean, runL: number, run: number, stopEl: number? }
local sweeps: { Sweep } = {}
local swingDir: Vector3? = nil -- the latest sweep's swing direction in the world (its tip's motion) and when
local swingDirT = -99

local function sweepBeam(p: Part, tex: string, z: number, col: Color3): Beam
	local b = Instance.new("Beam")
	b.Texture = tex
	b.TextureMode = Enum.TextureMode.Stretch
	b.TextureLength = 1
	b.TextureSpeed = 0
	b.FaceCamera = false
	b.Segments = 1
	b.LightEmission = 0
	b.LightInfluence = 0
	b.Brightness = 1
	b.ZOffset = z
	b.Color = ColorSequence.new(col)
	b.Enabled = false
	b.Parent = p
	return b
end

local addSample: (s: Sweep, m: Vector3, t: Vector3, dt: number?) -> () -- (below)
-- mid, tip: the blade's attachments; dur: how long the blade sweeps (its clip's trail window); cam: sample in camera
-- space (your own first-person blade); o.pre: the blade's Mid and tip a frame earlier, in the same space (at a low
-- frame rate the window is caught late); o.glint = false: no glint
function AnimeFx.sweep(mid: Attachment, tip: Attachment, tint: Color3, dur: number, cam: boolean, o: { glint: boolean?, pre: { m: Vector3, t: Vector3 }? }?)
	if not on() then return end
	local p = holder(CFrame.new())
	-- (it samples until the cut ends, up to half a second: the clip's window only says when to start looking)
	local s: Sweep = { mid = mid, tip = tip, cam = cam, tint = tint, left = math.max(dur, 0.5), dur = math.max(dur, 0.03),
		el = 0, samples = {}, part = p, atts = {}, body = {}, core = {}, glint = nil, gImg = nil, gAt = nil,
		band = if cam then 0.55 else 1, brk = false, runL = 0, run = 0, stopEl = nil } -- (first person: 55 % of Mid-to-tip, facing you)
	if o and o.pre then addSample(s, o.pre.m, o.pre.t) end
	if not (o and o.glint == false) then
		local at = Instance.new("Attachment")
		at.Parent = p
		local g = Instance.new("BillboardGui")
		g.LightInfluence = 0
		g.AlwaysOnTop = false
		g.Adornee = at
		g.Size = UDim2.fromScale(0, 0)
		local im = Instance.new("ImageLabel")
		im.BackgroundTransparency = 1
		im.Size = UDim2.fromScale(1, 1)
		im.Image = SPARKLE
		im.ImageColor3 = Color3.new(1, 1, 1):Lerp(tint, 0.15)
		im.Parent = g
		g.Parent = p
		s.glint, s.gImg, s.gAt = g, im, at
	end
	table.insert(sweeps, s)
end

-- a body's swing seen from outside (or yours in third person): the sweep on the blade it holds (ThirdPerson's TPGun
-- under the character). false when it holds none
function AnimeFx.bodySweep(ch: Instance?, tint: Color3, dur: number): boolean
	local g = ch and ch:FindFirstChild("TPGun")
	local root = g and g:IsA("Model") and g.PrimaryPart
	local mid = root and root:FindFirstChild("Mid")
	local tip = root and root:FindFirstChild("Muzzle")
	if not (mid and mid:IsA("Attachment") and tip and tip:IsA("Attachment")) then return false end
	AnimeFx.sweep(mid, tip, tint, dur, false)
	return true
end

local function perp(tg: Vector3): Vector3
	local alt = if math.abs(tg.Y) < 0.9 then Vector3.yAxis else Vector3.xAxis
	return tg:Cross(alt).Unit
end

-- (27 Nov, the first real swings: the katana's first-person trail window is its WIND-UP, the tip going over your head
-- and behind the lens; the cut comes after it, the tip sweeping across the view. So the sweep keeps the CUT itself:)
-- a sample counts while the tip moves faster than CUT_SPEED blade-spans (Mid to tip) a second; slower before a run is
-- still the wind-up (skipped), slower after a run of over 1.5 spans is the cut ending (sampling stops). First person
-- drops a tip within NEAR studs of the lens or behind it (the wind-up round your head) and starts the next run afresh;
-- a turn over 60 degrees (a wind-up turning into the cut, a backswing) starts it afresh too. A blade that has not moved
-- adds nothing.
local NEAR = 1
local CUT_SPEED = 25
addSample = function(s: Sweep, m: Vector3, t: Vector3, dt: number?)
	if s.cam and (t.Z > -NEAR or m.Z > -0.3) then
		if #s.samples > 0 then s.brk = true end
		return
	end
	local n = #s.samples
	if n >= 1 and dt then
		local last = s.samples[n]
		local v1 = t - last.t
		if v1.Magnitude < 1e-3 then return end
		local span = math.max((m - t).Magnitude, 0.05)
		if v1.Magnitude / math.max(dt, 1e-3) < CUT_SPEED * span then
			if s.runL > 1.5 * span then
				s.left = 0 -- (the cut has ended)
			elseif n == 1 then
				s.samples[1] = { m = m, t = t, age = 0 } -- (still winding up: the run starts from here)
			end
			return
		end
		if s.brk then
			s.samples, s.runL, s.run, s.brk = {}, 0, 0, false
		elseif n >= 2 then
			local v0 = last.t - s.samples[n - 1].t
			if v0.Magnitude > 1e-3 and v1:Dot(v0) < 0.5 * v1.Magnitude * v0.Magnitude then -- (60 degrees: a third-person swing's wind-up turned 70 into the cut, a corner)
				s.samples, s.runL, s.run = { last }, 0, 0
			end
		end
		if #s.samples >= 1 then s.runL += (t - s.samples[#s.samples].t).Magnitude end
	end
	table.insert(s.samples, { m = m, t = t, age = 0 })
end

local function stepSweep(s: Sweep, dt: number): boolean
	local cam = workspace.CurrentCamera
	if not cam then return false end
	local cf = cam.CFrame
	local d = dt * TS
	for _, smp in s.samples do smp.age += d end
	s.el += d
	if s.left > 0 and s.mid.Parent and s.tip.Parent then
		s.left -= d
		s.run += d
		if d > 0 or #s.samples == 0 then
			local m, t = s.mid.WorldPosition, s.tip.WorldPosition
			if s.cam then m, t = cf:PointToObjectSpace(m), cf:PointToObjectSpace(t) end
			addSample(s, m, t, dt)
		end
	else
		s.left = 0
	end
	if s.left <= 0 and not s.stopEl then s.stopEl = s.el end
	while #s.samples > 0 and s.samples[1].age > SWEEP_LIFE do table.remove(s.samples, 1) end
	while #s.samples > SWEEP_MAX do table.remove(s.samples, 1) end
	local ns = #s.samples
	if ns < 2 and s.left <= 0 then return false end
	-- the samples in the world now, then rounded: Catmull-Rom points between two samples where the path turns (a
	-- low frame rate or a fast swing left a polygon with corners)
	local Pm: { Vector3 }, Pt: { Vector3 }, Pa: { number } = {}, {}, {}
	for i, smp in s.samples do
		local m, t = smp.m, smp.t
		if s.cam then m, t = cf:PointToWorldSpace(m), cf:PointToWorldSpace(t) end
		Pm[i], Pt[i], Pa[i] = m, t, smp.age
	end
	local Dm: { Vector3 }, Dt: { Vector3 }, Da: { number } = {}, {}, {}
	local function cr(p0: Vector3, p1: Vector3, p2: Vector3, p3: Vector3, u: number): Vector3
		local u2, u3 = u * u, u * u * u
		return 0.5 * ((2 * p1) + (p2 - p0) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u2 + (3 * p1 - p0 - 3 * p2 + p3) * u3)
	end
	-- (round 3, the critic on v1454: "both edges kink ... a joined polyline", seams fanning at a tight curl: now no piece
	-- turns more than about 8 degrees. A segment gets as many points as the sharper of the turns at its two ends needs)
	local function turnAt(i: number): number
		if i <= 1 or i >= ns then return 0 end
		local e0, e1 = Pt[i] - Pt[i - 1], Pt[i + 1] - Pt[i]
		if e0.Magnitude < 1e-4 or e1.Magnitude < 1e-4 then return 0 end
		return math.deg(math.acos(math.clamp(e0.Unit:Dot(e1.Unit), -1, 1)))
	end
	for i = 1, ns do
		table.insert(Dm, Pm[i]); table.insert(Dt, Pt[i]); table.insert(Da, Pa[i])
		if i < ns and #Dt < 96 then
			local a0, a3 = math.max(i - 1, 1), math.min(i + 2, ns)
			local sub = math.clamp(math.ceil(math.max(turnAt(i), turnAt(i + 1)) / 8) - 1, 0, 8)
			for k = 1, sub do
				local u = k / (sub + 1)
				table.insert(Dt, cr(Pt[a0], Pt[i], Pt[i + 1], Pt[a3], u))
				table.insert(Dm, cr(Pm[a0], Pm[i], Pm[i + 1], Pm[a3], u))
				table.insert(Da, Pa[i] + (Pa[i + 1] - Pa[i]) * u)
			end
		end
	end
	local n = #Dt
	-- (round 2, the critic on v1448: "a nearly straight stripe of even width that ends in a square diagonal cut ... tape
	-- or a ruler"; from the shoulder camera, the plane edge-on, "a dotted thread ending in a chevron".) So:
	-- the head: the ribbon runs on 5 % of its length past the tip and closes there to a point
	if n >= 2 then
		local L0 = 0
		for i = 2, n do L0 += (Dt[i] - Dt[i - 1]).Magnitude end
		local hd = Dt[n] - Dt[n - 1]
		if hd.Magnitude > 1e-5 and L0 > 1e-4 then
			local ext = hd.Unit * (0.05 * L0)
			table.insert(Dt, Dt[n] + ext); table.insert(Dm, Dm[n] + ext); table.insert(Da, Da[n])
			n += 1
		end
	end
	local L, acc = 0, { 0 }
	for i = 2, n do L += (Dt[i] - Dt[i - 1]).Magnitude; acc[i] = L end
	-- (a stud's size in pixels at 1 stud away: the ribbon is never under 7 px across where the crescent is fullest)
	local pxK = 2 * math.tan(math.rad(cam.FieldOfView) / 2) / math.max(cam.ViewportSize.Y, 1)
	local C: { Vector3 }, Wd: { number }, U: { Vector3 }, Tr: { number } = {}, {}, {}, {}
	for i = 1, n do
		local k = math.clamp(Da[i] / SWEEP_LIFE, 0, 1)
		local u = if L > 1e-4 then acc[i] / L else 1
		-- a crescent along the swing: nothing at the tail, fullest at 70 %, closing to the point past the tip; it thins
		-- a little more with age
		local prof = if u < 0.7 then (u / 0.7) ^ 1.1 else math.max(0, 1 - (u - 0.7) / 0.3) ^ 0.8
		local f = s.band * prof * (1 - 0.35 * k)
		local span = Dm[i] - Dt[i]
		local sl = span.Magnitude
		local tg = Dt[math.min(i + 1, n)] - Dt[math.max(i - 1, 1)]
		local toEye = Dt[i] - cf.Position
		local wv = tg:Cross(toEye)
		if wv.Magnitude > 1e-6 and sl > 1e-5 then
			-- turned towards the lens: always in first person (the swing passes by your eye); from outside by how
			-- edge-on the swing's plane is (open to the camera: the blade's own plane; edge-on: facing you)
			wv = wv.Unit * sl
			if wv:Dot(span) < 0 then wv = -wv end
			local a = 1
			if not s.cam then
				local nrm = tg:Cross(span)
				local open = if nrm.Magnitude > 1e-6 and toEye.Magnitude > 1e-6 then math.abs(nrm.Unit:Dot(toEye.Unit)) else 1
				a = 1 - math.clamp(open / 0.45, 0, 1)
				a = a * a * (3 - 2 * a)
			end
			local mix = span * (1 - a) + wv * a
			span = if mix.Magnitude > 1e-5 then mix.Unit * sl else wv
		end
		local t = Dt[i]
		if s.cam and L > 1e-4 then
			-- (first person: the path bowed out by 7 % of its length at the middle, so it reads as an arc)
			t -= span.Unit * (0.07 * L * math.sin(math.pi * u))
		end
		local w = math.max(sl * f, 7 * pxK * toEye.Magnitude * prof)
		C[i] = t + span.Unit * (w / 2)
		Wd[i] = w
		U[i] = if sl > 1e-4 then span.Unit else Vector3.yAxis
		Tr[i] = math.clamp((k - 0.45) / 0.55, 0, 1) ^ 1.3
	end
	if ns >= 2 then
		local a, b = Pt[ns - 1], Pt[ns]
		if (b - a).Magnitude > 1e-3 then swingDir = (b - a).Unit; swingDirT = os.clock() end
	end
	-- (each segment has its own attachments: the body's meet their neighbours' exactly, the core's reach 6 % into
	-- them. Overlapping bodies let the next segment's blue draw over this one's white, a line across the band at every
	-- joint; overlapping cores only ever cover a neighbour's white with white. A ZOffset fix moved the core off the body)
	local TG: { Vector3 }, WW: { Vector3 } = {}, {}
	for i = 1, n do
		local tg = C[math.min(i + 1, n)] - C[math.max(i - 1, 1)]
		tg = if tg.Magnitude > 1e-5 then tg.Unit else perp(U[i])
		local w = U[i] - tg * U[i]:Dot(tg)
		w = if w.Magnitude > 1e-4 then w.Unit else perp(tg)
		if BEAM_FLIP then w = -w end
		TG[i], WW[i] = tg, w
	end
	local function place(at: Attachment, pos: Vector3, i: number)
		local tg, w = TG[i], WW[i]
		at.WorldCFrame = if BEAM_AXIS == "Y" then CFrame.fromMatrix(pos, tg, w) else CFrame.fromMatrix(pos, tg, w:Cross(tg))
	end
	for i = 1, n - 1 do
		for e = 1, 4 do
			local j = 4 * i - 4 + e
			if not s.atts[j] then
				local at = Instance.new("Attachment")
				at.Parent = s.part
				s.atts[j] = at
			end
		end
		local ov = (C[i + 1] - C[i]) * 0.025 -- (6 % left white ticks at the joints, seen from above)
		place(s.atts[4 * i - 3], C[i], i)
		place(s.atts[4 * i - 2], C[i + 1], i + 1)
		place(s.atts[4 * i - 1], C[i] - ov, i)
		place(s.atts[4 * i], C[i + 1] + ov, i + 1)
	end
	for i = 1, math.max(n - 1, #s.body) do
		local live = i <= n - 1 and (C[i + 1] - C[i]).Magnitude > 1e-4
		for li = 1, 2 do
			local list = if li == 1 then s.body else s.core
			local b = list[i]
			if not b and live then
				b = sweepBeam(s.part, if li == 1 then SWEEP_BODY else SWEEP_CORE, if li == 1 then 0 else 0.02, if li == 1 then s.tint else Color3.new(1, 1, 1))
				if li == 2 then b.Brightness = 1.25 end -- (the white band read light grey under the colour grading)
				list[i] = b
			end
			if b then
				if live then
					b.Attachment0, b.Attachment1 = if li == 1 then s.atts[4 * i - 3] else s.atts[4 * i - 1], if li == 1 then s.atts[4 * i - 2] else s.atts[4 * i]
					b.Width0, b.Width1 = Wd[i], Wd[i + 1]
					b.Transparency = NumberSequence.new(Tr[i], Tr[i + 1])
					b.Enabled = true
				else
					b.Enabled = false
				end
			end
		end
	end
	-- the glint: up the band to the tip while the blade sweeps, then a pop at the tip that shrinks away in 0.1 s
	if s.glint and s.gAt and s.gImg and ns >= 1 then
		local m, t = Pm[ns], Pt[ns]
		local g = math.clamp(s.run / 0.1, 0, 1)
		local after = if s.stopEl then math.max(0, s.el - s.stopEl) else 0
		local pos = t + (m - t) * (s.band * (1 - g))
		local sz = (t - m).Magnitude * s.band * (0.9 + 0.5 * g) * math.max(0, 1 - after / 0.1)
		local toCam = cf.Position - pos
		if toCam.Magnitude > 1e-3 then pos += toCam.Unit * (sz * 0.3) end -- (in front of the blade, not inside it)
		s.gAt.WorldPosition = pos
		s.glint.Size = UDim2.new(sz, 0, sz, 0)
		s.gImg.Rotation = s.el * 260
		s.glint.Enabled = sz > 0.01
	end
	return true
end

-- after the camera and the viewmodel (Arsenal's step is Camera + 2): the blade is where it is drawn this frame
RunService:BindToRenderStep("JankAnimeSweep", Enum.RenderPriority.Camera.Value + 3, function(dt: number)
	for i = #sweeps, 1, -1 do
		local s = sweeps[i]
		local ok, alive = pcall(stepSweep, s, dt)
		if not ok or not alive or not s.part.Parent then
			if s.part.Parent then s.part:Destroy() end
			table.remove(sweeps, i)
		end
	end
end)
-- the latest swing's direction in the world, if it is under `within` seconds old (the hit points its burst along it)
function AnimeFx.swingDir(within: number?): Vector3?
	return if os.clock() - swingDirT < (within or 0.4) then swingDir else nil
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
	-- (27 Nov: along the swing. The burst's longest needle (the sheet's 10 degrees clockwise from up) points the way the
	-- blade was moving on screen and the sparks fly on along it; with no sweep in the last 0.4 s, as before: away from
	-- the camera and up)
	local sd = AnimeFx.swingDir(0.4)
	local rot: number? = nil
	if sd then
		local d2 = AnimeFx.screenDir(sd)
		rot = math.deg(math.atan2(d2.Y, d2.X)) - 80 + math.random(-8, 8)
	end
	AnimeFx.burst(at, if heavy then 3.25 else 2.4, tint, rot) -- (the sheet draws it at 80 %: its margins)
	local away = if dir.Magnitude > 1e-3 then dir.Unit else Vector3.zAxis
	local sdir = if sd then sd * 0.85 + away * 0.25 + Vector3.new(0, 0.3, 0) else away * 0.7 + Vector3.new(0, 0.7, 0)
	AnimeFx.sparks(at, sdir, if heavy then 7 else 5, tint)
	if heavy then AnimeFx.twinkle(at + Vector3.new(0, 0.4, 0), 1.6, tint) end
	if own and heavy then AnimeFx.impactFrame(frame) end
end

function AnimeFx.clear()
	for _, e in live do if e.p.Parent then e.p:Destroy() end end
	table.clear(live)
	for _, sw in sweeps do if sw.part.Parent then sw.part:Destroy() end end
	table.clear(sweeps)
end

return AnimeFx
