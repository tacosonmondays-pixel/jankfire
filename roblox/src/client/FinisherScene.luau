--!strict
-- FINISHER SCENES (19 Nov 2026; roblox/docs/FINISHERS.md): the owner's "cinematic" finishers. A finisher with a scene
-- (Finishers row `scene`) plays a small story in a few shots instead of the recording-based cut: the killer's and the
-- victim's own avatars (the replay's ghost copies, with their skins) act it out with mocap clips (Finishers.SCENE_ANIMS,
-- uploaded from the vault's Mixamo clips and the MotionBricks takes made from them), on a small set of its own built
-- far off the map, under a lens that moves the way the storyboards and the video planned it.
-- The plan is the video's (tools/roblox/finisher_r15.py video:<v>, boiled down by finisher_scene_data.py into
-- FinisherSceneData): per frame (24 fps) the lens, each body's clip and moment and where its root stands, where the
-- katana is. This plays it at the screen's frame rate (the frames are blended) and adds what moves on its own: the
-- blade's ink trail, drifting petals, the ink stroke, the petal burst, the body coming apart, the two-tone hit frames.
-- Scene.can(row, kind, kg, vg) -> boolean     both bodies are R15 with an Animator and the scene's data is here
-- Scene.start(s, kind) -> sc                  builds the set and takes the two bodies (s = Finisher.luau's state)
-- Scene.step(s, w) -> (shot name, u, last)    one frame at w s into the scene
-- Scene.stop(s)                               everything it made goes; the bodies are Finisher.luau's to destroy
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local CollectionService = game:GetService("CollectionService")

local Data = require(script.Parent:WaitForChild("FinisherSceneData")) :: any
-- (a scene's kit town and its onlookers: client/FinisherTown.luau; missing, the plan's own boxes stand)
local Town: any = nil
do
	local m = script.Parent:FindFirstChild("FinisherTown")
	if m then
		local ok, T = pcall(require, m)
		if ok then Town = T end
	end
end
-- (a scene too big for one module comes in parts, FinisherSceneData_<id> and FinisherSceneData_<id>_set: merged into
-- Data by scene id the first time it's asked for - High Noon's town alone is 74 KB)
local merged: { [string]: boolean } = {}
local function dataOf(sid: string?): any
	if type(sid) ~= "string" then return nil end
	if not merged[sid] then
		merged[sid] = true
		for _, m in script.Parent:GetChildren() do
			local n = m.Name
			if m:IsA("ModuleScript") and (n == "FinisherSceneData_" .. sid or n == "FinisherSceneData_" .. sid .. "_set") then
				local ok, t = pcall(require, m)
				if ok and type(t) == "table" and type(t[sid]) == "table" then
					Data[sid] = Data[sid] or {}
					for k, v in t[sid] do Data[sid][k] = v end
				end
			end
		end
	end
	local d = Data[sid]
	return if type(d) == "table" and d.f and d.stage then d else nil
end
local Sfx = require(script.Parent:WaitForChild("Sfx")) :: any
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Finishers = require(Shared:WaitForChild("Finishers")) :: any

local Scene = {}

-- the set's spot: far from every map, nothing else is ever there (client-only parts)
local ORIGIN = CFrame.new(0, 600, -24000)
local RIG_HIP = 3.0 -- (the plan's root height over the floor: the stock R15's hip height + half its root)
local INK = Color3.new(0.05, 0.05, 0.07)
local SMEAR = Color3.new(1, 0.95, 0.97) -- (the blade's light trail: the cut flashes bright, never a dark fan)
local PAPER = Color3.new(0.97, 0.96, 0.94)
local SAKURA = Color3.new(0.95, 0.74, 0.82)
local SAKURA2 = Color3.new(0.98, 0.86, 0.9)
local LACQUER = Color3.new(0.1, 0.07, 0.09)
local GOLD = Color3.new(0.85, 0.68, 0.32)
local R15 = { "Head", "UpperTorso", "LowerTorso", "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm",
	"RightLowerArm", "RightHand", "LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "RightUpperLeg", "RightLowerLeg", "RightFoot" }

-- the per-scene extras: where the round win's short payoff starts (a frame), its speed, the sound cues (frame,
-- Sfx name, volume: recordings from the game's library), the shots that trail ink off the blade (trail life, s)
local EXTRA: { [string]: any } = {
	inkfall = {
		-- (Tidecrest v4.2, 20 Nov: rebuilt from the scene-by-scene review - the grip, the two-hand draw with the long blade,
		-- the whirl to his face, the sprint, the pass, the hit frame, the freeze, the sheathe's click, the cut lands, the
		-- winner close on the right as he falls behind. a round win plays the cut landing and the end)
		short = { shot = "THE CUT LANDS", speed = 1 },
		cues = { { 1, "zone_lot", 0.5 }, { 1, "zone_playground", 1 }, { 7, "loot_pop", 0.3 }, { 17, "swing", 0.6 },
			{ 53, "loot_pop", 0.6 }, { 57, "swing", 1 }, { 57, "skin_katana_sakura_swing", 0.7 }, { 86, "whoops", 0.6 },
			{ 95, "zone_playground", 0.8 }, { 130, "swing", 1 }, { 131, "skin_katana_sakura_swing", 0.8 },
			{ 140, "round_end", 0.9 }, { 198, "loot_pop", 0.9 }, { 198, "zone_vip", 0.9 },
			{ 208, "skin_katana_sakura_hit", 0.8 }, { 234, "death", 0.6 } },
		trail = { ["THE LENGTH"] = 0.15, CLOSING = 0.1, ["THE PASS"] = 0.35, ["CUT FRAME"] = 0.35 },
		dust = { ["THE CHARGE"] = true, CLOSING = true, ["THE PASS"] = true },
	},
	highnoon = {
		-- (20 Nov, the owner: "take out tidecrest put in revolver" - the High Noon Western they approved as video,
		-- western_town_v3: a standoff in a sunset town on the two real avatars, the holsters on their hips, the hands
		-- reaching onto the guns, one shot; a round win plays the draw, the shot and the far shot)
		kit = "revolver",
		short = { shot = "THE DRAW", speed = 1 },
		-- (the bars come in over the overhead's push-in, as the video: the owner, "it should start without bars and the
		-- come in as it zooms in overhead")
		barsIn = 2.2,
		-- (the video's retime: the suspense shots held longer, each frame shown this many times as long; the enemy's reach
		-- held a beat longer still - the owner: "the scene where the enemy goes for the gun last a tiny bit longer")
		stretch = { OVERHEAD = 1.5, ["KILLER'S EYES"] = 1.6, ["VICTIM'S EYES"] = 1.6, ["KILLER'S HAND"] = 1.5,
			["VICTIM'S HAND"] = 1.5, ["THE WIDE"] = 1.4, ["EYES AGAIN"] = 1.6, ["THEIR EYES"] = 1.6, ["ENEMY REACHES"] = 2.0,
			["FAR SHOT"] = 1.3 },
		zoom = { ["EYES AGAIN"] = 1.3, ["THEIR EYES"] = 1.3 },
		-- (20 Nov, the owner: "there also no sound effects for the scenes and could we find some western music": all
		-- recordings, no voices. A number is a Roblox library sound (Pro Sound Effects, licensed to every experience); a
		-- name is the game's own library (Sfx). The wind and the music drop out before the shot, so the bang lands in
		-- near silence, and come back after the fall)
		cues = { { 20, "9120839174", 0.35 }, -- a sign creaks over the street
			{ 75, "click", 0.4 }, -- the killer's thumb on the hammer
			{ 95, "9114704545", 0.25 }, -- leather: the enemy's hand by the holster
			{ 112, "9114518070", 0.45 }, { 128, "9114518070", 0.3 }, -- the tumbleweed rolling through
			{ 169, "9114701864", 0.8 }, -- the enemy draws: the gun out of the leather
			{ 174, "9114701864", 1 }, { 176, "click", 0.5 }, -- the killer draws, cocks
			{ 181, "gun_revolver", 1 }, { 181, "skin_revolver_dust_fire", 0.8 }, -- the shot (a ricochet's long tail on it)
			{ 182, "9113487557", 0.7 }, -- the bullet into the body
			{ 191, "9113469691", 0.9 }, { 193, "9114658419", 0.4 }, -- the fall, the dust settling
			{ 211, "9114704674", 0.6 } }, -- back in the holster
		audio = {
			-- (the music: APM's "Gunslingers", an atmospheric western scene-setter from Roblox's licensed library; under
			-- the MUSIC slider. the wind: Pro Sound Effects' desert wind, under EFFECTS)
			-- (the music stays at its level through the shot, the shot on top of it - the owner, 20 Nov: "also the music
			-- softens at the shot"; only the wind drops out)
			music = { id = "1841135337", vol = 0.5 },
			bed = { id = "9114057104", vol = 0.5, out = 166, outT = 0.6, back = 196, backVol = 0.22, backT = 1.0, looped = true },
		},
		-- (the enemy's hand closes on the holster's grip through VICTIM'S HAND and stays there until the draw - the owner,
		-- 20 Nov: "the enemies hand should be on their holster after the scene of them moving their hand to the position")
		holdReach = { v = { from = 95, to = 110 } },
		-- (the town - the owner, 20 Nov: "can you fix the scene scenery too? ... make two versions so I can see side by
		-- side": the kit town "A" (a timber main street, onlookers in the saloon's windows) or "B" (an adobe border town,
		-- balcony and porch onlookers) in place of the plan's boxes, FinisherTown; the wheel ruts gone ("long rectangle
		-- strips ... make those go bye bye") and the footprints faint ("the footsteps can they be more subtyle")). The
		-- owner picked A, 20 Nov: B's set is out of the place (tools/roblox/highnoon_town_import.luau brings it back)
		town = "A", noRuts = true, softPrints = true,
		-- (the grade - the owner, 20 Nov: "can it transistion into that desaturated filter after the shot, but keep it nice
		-- and glowey without filter ofr the rest of it or a slight orange like in western films?": warm and glowing to the
		-- shot, easing into the desaturated look over `over` s from the impact frame `at`, held to the end. The scene
		-- owns it (Finisher.luau's grade asks Scene.grade); cheap: ColorCorrection and a gentle Bloom, no blur)
		grade = { warm = { tint = Color3.fromRGB(255, 226, 192), sat = 0.06, con = 0.12, bright = 0.02 },
			-- (the owner, 20 Nov: "after the shot and the person falls then fade toe desaturated": the body lands at
			-- frames 199-201 and settles by 206 in the plan)
			cold = { tint = Color3.fromRGB(242, 238, 232), sat = -0.62, con = 0.16, bright = -0.02 }, at = 206, over = 0.7,
			bloom = { Intensity = 0.55, Size = 26, Threshold = 1.5 } },
		-- (high noon - the owner, 20 Nov: "can it be an actual sky with a sun its high noon after all": Roblox's own sky
		-- and sun in place of the set's painted sunset ring and the place's sky box, the sun up in the top of THE DRAW's
		-- low lens (clock 12.9 at latitude -28 puts it there), bright warm daylight, a light desert haze, no lamps lit;
		-- all put back after)
		look = { clock = 12.9, lat = -28, bright = 2.8, outdoor = Color3.fromRGB(150, 138, 124), ambient = Color3.fromRGB(96, 88, 80),
			shiftTop = Color3.fromRGB(255, 236, 206), exposure = -0.1, plainSky = true,
			atmo = { Density = 0.26, Offset = 0.1, Color = Color3.fromRGB(204, 214, 224), Decay = Color3.fromRGB(204, 172, 132),
				Glare = 0.4, Haze = 0.5 } },
	},
}

-- the plan is laid out in Blender's axes (z up, the victim at the origin facing -y): a Blender offset in the stage's
-- Roblox axes
local function B(x: number, y: number, z: number): Vector3 return Vector3.new(x, z, -y) end
local function cfOf(t: { number }): CFrame return CFrame.new(t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10], t[11], t[12]) end
local function ease(u: number): number u = math.clamp(u, 0, 1); return u * u * (3 - 2 * u) end

local function part(parent: Instance, size: Vector3, cf: CFrame, col: Color3, mat: Enum.Material?, shape: Enum.PartType?): Part
	local p = Instance.new("Part")
	if shape then p.Shape = shape end
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	p.Size = size; p.CFrame = cf; p.Color = col; p.Material = mat or Enum.Material.SmoothPlastic
	p.Parent = parent
	return p
end

-- a box from a to b (world), its length along Z, `up` turning its flat side
local function between(p: BasePart, a: Vector3, b: Vector3, w: number, h: number, up: Vector3)
	local d = b - a
	local L = d.Magnitude
	if L < 1e-3 then p.Size = Vector3.new(w, h, 0.01); return end
	local z = -d.Unit
	local x = up:Cross(z)
	if x.Magnitude < 1e-4 then x = Vector3.xAxis:Cross(z) end
	x = x.Unit
	local y = z:Cross(x)
	p.Size = Vector3.new(w, h, L)
	p.CFrame = CFrame.fromMatrix((a + b) / 2, x, y, z)
end

function Scene.can(row: any, kind: string, kg: any, vg: any): boolean
	if not row or type(row.scene) ~= "string" or not dataOf(row.scene) then return false end
	if kind ~= "full" and kind ~= "short" then return false end
	for _, g in { kg, vg } do
		if not g or not g.model or not g.model:FindFirstChild("LowerTorso") or not g.hum then return false end
		if not (g.hum :: Humanoid):FindFirstChildOfClass("Animator") then return false end
	end
	return true
end

-- ------------------------------------------------------------------ the bodies
local function takeBody(g: any)
	g.model:SetAttribute("TPWeapon", nil)
	if g.run then pcall(function() g.run:Stop(0) end) end
	if g.idle then pcall(function() g.idle:Stop(0) end) end
	-- (a beat later, as the victim's hand-off does: ThirdPerson drops the gun it drew when TPWeapon goes, then lets go)
	task.delay(0.05, function() if g.model.Parent then CollectionService:RemoveTag(g.model, "TPRig") end end)
	local an = (g.hum :: Humanoid):FindFirstChildOfClass("Animator") :: Animator
	for _, tr in an:GetPlayingAnimationTracks() do tr:Stop(0) end
	g.root.Anchored = true
end

local function trackFor(sc: any, who: string, g: any, ci: number): AnimationTrack?
	sc.tracks[who] = sc.tracks[who] or {}
	local have = sc.tracks[who][ci]
	if have then return have end
	local clip = sc.d.clips[ci]
	local id = Finishers.SCENE_ANIMS[clip]
	if not id then return nil end
	local an = (g.hum :: Humanoid):FindFirstChildOfClass("Animator")
	if not an then return nil end
	local a = Instance.new("Animation")
	a.AnimationId = "rbxassetid://" .. id
	local ok, tr = pcall(function() return (an :: Animator):LoadAnimation(a) end)
	if not ok or not tr then return nil end
	tr.Looped = false
	tr.Priority = Enum.AnimationPriority.Action4
	sc.tracks[who][ci] = tr
	return tr
end

-- this frame's pose: the clip at its moment (paused; the moment set each frame), the root where the plan stands it
local function poseBody(sc: any, who: string, g: any, ci: number, t: number, root: CFrame)
	local tr = trackFor(sc, who, g, ci)
	if sc.cur[who] ~= ci then
		local old = sc.cur[who] and sc.tracks[who] and sc.tracks[who][sc.cur[who]]
		if old then old:Stop(0) end
		if tr then tr:Play(0, 1, 0) end
		sc.cur[who] = ci
	end
	if tr then
		local L = tr.Length
		tr.TimePosition = if L > 0 then math.clamp(t, 0, L - 1 / 60) else t
	end
	g.root.CFrame = ORIGIN * root + Vector3.new(0, sc.hip[who] - RIG_HIP, 0)
end

-- the victim comes apart: anchored copies of their body parts drift off as the original (hidden) keeps its pose
local function piecesFor(sc: any, g: any)
	if sc.pieces then return sc.pieces end
	local out = {}
	local rnd = Random.new(11)
	for _, n in R15 do
		local p = g.model:FindFirstChild(n)
		if p and p:IsA("BasePart") then
			local c = p:Clone()
			for _, d in c:GetDescendants() do
				if d:IsA("JointInstance") or d:IsA("Constraint") or d:IsA("Attachment") or d:IsA("BaseScript") then d:Destroy() end
			end
			c.Anchored = true; c.CanCollide = false; c.CanQuery = false; c.CanTouch = false
			c.Parent = sc.folder
			local dir = Vector3.new(rnd:NextNumber(-1, 1), rnd:NextNumber(-0.2, 1), rnd:NextNumber(-1, 1)).Unit
			table.insert(out, { src = p, copy = c, dir = dir * rnd:NextNumber(0.4, 1), rot = Vector3.new(rnd:NextNumber(-40, 40), rnd:NextNumber(-40, 40), rnd:NextNumber(-40, 40)) })
		end
	end
	for _, d in g.model:GetDescendants() do
		if d:IsA("BasePart") or d:IsA("Decal") then d.LocalTransparencyModifier = 1 end
	end
	sc.pieces = out
	return out
end

-- ------------------------------------------------------------------ the katana, its sheath, the trail
local function katanaKit(sc: any, skin: string?)
	local skins = ReplicatedStorage:FindFirstChild("JankfireSkins")
	local tpl = skins and (skins:FindFirstChild(skin or "") or skins:FindFirstChild("katana_sakura"))
	sc.kat = {}
	if tpl then
		local k = tpl:Clone()
		-- (the skin's real blade tip, the front-most corner along -Z: the long-blade stretch lands THIS tip on the
		-- plan's -(0.6 + 2.3 L); taking every skin's tip as -2.9 left the sakura blade ~4 studs short at THE TIP)
		local tipZ = math.huge
		for _, p in k:GetDescendants() do
			if p:IsA("BasePart") then
				local oc = p.CFrame
				for _, sx in { -1, 1 } do for _, sy in { -1, 1 } do for _, sz in { -1, 1 } do
					local z = (oc * Vector3.new(sx * p.Size.X / 2, sy * p.Size.Y / 2, sz * p.Size.Z / 2)).Z * 3
					if z < tipZ then tipZ = z end
				end end end
				p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
				p.Size *= 3
				table.insert(sc.kat, { p = p, rel = CFrame.new(oc.Position * 3) * oc.Rotation, size = p.Size, L = 1 })
			elseif p:IsA("BaseScript") or p:IsA("JointInstance") or p:IsA("Constraint") then
				p:Destroy()
			end
		end
		k.Parent = sc.folder
		sc.katModel = k
		sc.katTip = if tipZ < -1 and tipZ > -10 then tipZ else -2.9
	end
	-- the blade's trail: off a carrier that rides the blade (guard to tip, local -Z)
	local carrier = part(sc.folder, Vector3.new(0.1, 0.1, 0.1), ORIGIN, INK)
	carrier.Transparency = 1
	local a0 = Instance.new("Attachment"); a0.Position = Vector3.new(0, 0, -0.6); a0.Parent = carrier
	local a1 = Instance.new("Attachment"); a1.Position = Vector3.new(0, 0, -2.9); a1.Parent = carrier
	local tr = Instance.new("Trail")
	tr.Attachment0 = a0; tr.Attachment1 = a1
	tr.Color = ColorSequence.new(SMEAR)
	tr.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.05), NumberSequenceKeypoint.new(0.7, 0.4), NumberSequenceKeypoint.new(1, 1) })
	tr.LightEmission = 0.6; tr.LightInfluence = 0; tr.FaceCamera = false; tr.MinLength = 0
	tr.Lifetime = 0.12; tr.Enabled = false
	tr.Parent = carrier
	sc.carrier, sc.trail, sc.tipA = carrier, tr, a1
	-- the scabbard at the left hip (the killer's LowerTorso: the mouth forward and up, running back and down)
	sc.sheath = { part(sc.folder, Vector3.one, ORIGIN, LACQUER), part(sc.folder, Vector3.one, ORIGIN, SAKURA), part(sc.folder, Vector3.one, ORIGIN, GOLD) }
end

local function placeKit(sc: any, f: any, kg: any)
	local lt = kg.model:FindFirstChild("LowerTorso") :: BasePart?
	local hand = kg.model:FindFirstChild("RightHand") :: BasePart?
	if lt then
		local a, b = lt.CFrame * Vector3.new(-0.95, 0.1, -0.75), lt.CFrame * Vector3.new(-1.25, -1.6, 2.2)
		local d = (b - a).Unit
		local up = lt.CFrame.YVector
		between(sc.sheath[1], a, b, 0.22, 0.34, up)
		between(sc.sheath[2], a + d * 0.3, a + d * 0.5, 0.26, 0.38, up)
		between(sc.sheath[3], b - d * 0.25, b, 0.26, 0.38, up)
	end
	local grip: CFrame? = nil
	local k = f.kat
	if k and k[1] == 1 and hand then grip = hand.CFrame * CFrame.new(0, -0.12, 0)
	elseif k and k[1] == 2 and lt then grip = lt.CFrame * cfOf(k[2]) end
	local L = f.L or 1
	for _, e in sc.kat do
		e.p.LocalTransparencyModifier = if grip then 0 else 1
		if grip then
			local rel = e.rel
			if L ~= 1 and rel.Position.Z < -0.6 then
				-- (the long-blade gag: the blade stretched out along the grip's -Z from the guard)
				rel = CFrame.new(rel.Position.X, rel.Position.Y, -0.44 + (rel.Position.Z + 0.44) * L) * rel.Rotation
				if e.L ~= L then
					local ax = { math.abs(rel.XVector.Z), math.abs(rel.YVector.Z), math.abs(rel.ZVector.Z) }
					local sz = e.size
					e.p.Size = if ax[1] >= ax[2] and ax[1] >= ax[3] then Vector3.new(sz.X * L, sz.Y, sz.Z)
						elseif ax[2] >= ax[3] then Vector3.new(sz.X, sz.Y * L, sz.Z) else Vector3.new(sz.X, sz.Y, sz.Z * L)
				end
			elseif e.L ~= L then
				e.p.Size = e.size
			end
			e.L = L
			e.p.CFrame = grip * rel
		end
	end
	if grip then
		sc.carrier.CFrame = grip
		sc.tipA.Position = Vector3.new(0, 0, -(0.6 + 2.3 * L))
	end
end

-- ------------------------------------------------------------------ effects that move on their own
local function petalPool(sc: any, key: string, n: number, neon: boolean?): { Part }
	sc.pools[key] = sc.pools[key] or {}
	local pool = sc.pools[key]
	while #pool < n do
		local i = #pool
		table.insert(pool, part(sc.folder, Vector3.new(0.32, 0.04, 0.22) * 1.3, ORIGIN, if i % 4 == 0 then SAKURA2 else SAKURA,
			if neon then Enum.Material.Neon else Enum.Material.SmoothPlastic))
	end
	return pool
end

-- loose petals drifting with the scene's clock (`t`), round a centre (stage-local)
local function drift(sc: any, key: string, center: Vector3, n: number, spread: number, t: number, vel: Vector3, seed: number)
	local pool = petalPool(sc, key, n)
	local rnd = Random.new(seed)
	for i = 1, n do
		local base = center + Vector3.new(rnd:NextNumber(-1, 1), rnd:NextNumber(-0.6, 1), rnd:NextNumber(-1, 1)) * spread
		local ph = rnd:NextNumber(0, 6.28)
		local ax, ay, az = rnd:NextNumber(0, 6.28), rnd:NextNumber(0, 6.28), rnd:NextNumber(0, 6.28)
		local p = base + vel * t + Vector3.new(math.sin(ph + t * 3) * 0.25, math.cos(ph + t * 2.3) * 0.12, 0)
		pool[i].CFrame = ORIGIN * CFrame.new(p) * CFrame.Angles(ax + 2.4 * t, ay + 1.7 * t, az)
	end
end

-- pieces thrown out from a point, fast at first, slowing, then falling (u 0..1); world centre
local function burst(sc: any, key: string, center: Vector3, n: number, reach: number, u: number, seed: number, splat: boolean?, size: number?)
	sc.pools[key] = sc.pools[key] or {}
	local pool = sc.pools[key]
	while #pool < n do
		if splat then
			table.insert(pool, part(sc.folder, Vector3.one * 0.2, ORIGIN, INK, Enum.Material.SmoothPlastic, Enum.PartType.Ball))
		else
			local i = #pool
			table.insert(pool, part(sc.folder, Vector3.new(0.32, 0.04, 0.22) * (size or 1.3), ORIGIN, if i % 4 == 0 then SAKURA2 else SAKURA, Enum.Material.Neon))
		end
	end
	local rnd = Random.new(seed)
	local k = 1 - (1 - math.clamp(u, 0, 1)) ^ 2.2
	for i = 1, n do
		local d = Vector3.new(rnd:NextNumber(-1, 1), rnd:NextNumber(-0.3, 1), rnd:NextNumber(-1, 1)).Unit
		local r = reach * rnd:NextNumber(0.35, 1)
		local p = center + d * r * k - Vector3.new(0, 0.8 * u * u, 0)
		if splat then
			local s = 0.18 * (size or 1) * rnd:NextNumber(0.6, 1.6) * (1 - 0.5 * u)
			pool[i].Size = Vector3.one * s
			pool[i].CFrame = CFrame.new(p)
		else
			pool[i].CFrame = CFrame.new(p) * CFrame.Angles(rnd:NextNumber(0, 6.28) + 5.2 * u, rnd:NextNumber(0, 6.28) + 3.5 * u, rnd:NextNumber(0, 6.28))
		end
	end
end

-- dust kicked up where a foot strikes the floor (the crouched sprint of the owner's reference): each puff grows, drifts
-- back along the run and thins out over half a second; T = the scene's clock
local DUSTO = { { 0, 0, 0.2, 0.55 }, { 0.35, -0.25, 0.15, 0.42 }, { -0.3, -0.35, 0.28, 0.36 } }
local function dust(sc: any, g: any, T: number, kick: boolean)
	sc.dustL = sc.dustL or {}
	sc.dustLast = sc.dustLast or {}
	if kick then
		for _, f in { "LeftFoot", "RightFoot" } do
			local p = g.model:FindFirstChild(f) :: BasePart?
			if p and ORIGIN:PointToObjectSpace(p.Position).Y < 0.6 and T - (sc.dustLast[f] or -9) > 0.16 then
				sc.dustLast[f] = T
				table.insert(sc.dustL, { T, p.Position })
			end
		end
	end
	sc.pools.dust = sc.pools.dust or {}
	local pool = sc.pools.dust
	local n = 0
	for _, e in sc.dustL do
		local age = T - e[1]
		if age >= 0 and age <= 0.5 then
			local k = age / 0.5
			for _, o in DUSTO do
				n += 1
				local p = pool[n]
				if not p then
					p = part(sc.folder, Vector3.one, ORIGIN, Color3.new(0.78, 0.76, 0.74), Enum.Material.SmoothPlastic, Enum.PartType.Ball)
					pool[n] = p
				end
				local r = o[4] * (1 + 1.7 * k)
				local q = e[2] + B(o[1], o[2] - 0.9 * k, o[3] + 0.45 * k)
				p.Size = Vector3.one * r
				p.CFrame = CFrame.new(q.X, math.max(q.Y, ORIGIN.Y + r * 0.3), q.Z)
				p.Transparency = 0.3 + 0.65 * k
			end
		end
	end
	for j = n + 1, #pool do pool[j].Transparency = 1 end
end

-- the ink stroke where the swing passed: a brush of boxes from a to b, bulging, thick in the middle (world points)
local function stroke(sc: any, key: string, a: Vector3, b: Vector3, bulge: number, width: number, facing: Vector3, col: Color3, seed: number): { Part }
	local n = 16
	local d = b - a
	local side = d:Cross(facing).Unit
	local rnd = Random.new(seed)
	local pts = {}
	for i = 0, n do table.insert(pts, a + d * (i / n) + side * (bulge * math.sin(math.pi * i / n))) end
	local out = {}
	for i = 1, n do
		local t = (i - 0.5) / n
		local w = width * (math.sin(math.pi * math.min(1, t * 1.1)) ^ 0.6) * rnd:NextNumber(0.75, 1) + 0.02
		local p = part(sc.folder, Vector3.one, ORIGIN, col, if col == INK then Enum.Material.Neon else Enum.Material.SmoothPlastic)
		between(p, pts[i], pts[i + 1], 0.06, w, side)
		table.insert(out, p)
	end
	sc.pools[key] = out
	return out
end

-- the two-tone hit frame: the bodies in ink on paper, the set gone, the accent (the trail, the stroke) in the skin's pink
local function setHit(sc: any, s: any, on: boolean, accent: { Part }?, inv: boolean?)
	if sc.hitOn == on and sc.hitInv == (inv == true) and not on then return end
	if sc.hitOn == on and sc.hitInv == (inv == true) and on then return end
	sc.hitOn = on
	sc.hitInv = inv == true
	local FG, BG = if inv then PAPER else INK, if inv then INK else PAPER
	for _, d in sc.stage:GetDescendants() do if d:IsA("BasePart") then d.LocalTransparencyModifier = if on then 1 else 0 end end
	for _, pool in sc.pools do
		for _, p in pool do if p:IsA("BasePart") then p.LocalTransparencyModifier = if on and not (accent and table.find(accent, p)) then 1 else 0 end end
	end
	local inked = { s.kg.model, s.vg.model, sc.katModel }
	for _, km in sc.revModels or {} do table.insert(inked, km) end -- (the holsters, belts and revolvers ink with the bodies)
	for _, m in inked do
		if m then
			local h = m:FindFirstChild("JankSceneHit") :: Highlight?
			if on then
				local hl = h or Instance.new("Highlight")
				hl.Name = "JankSceneHit"
				hl.FillColor = FG; hl.FillTransparency = 0
				hl.OutlineColor = BG; hl.OutlineTransparency = 0
				hl.DepthMode = Enum.HighlightDepthMode.Occluded
				hl.Parent = m
			elseif h then
				h:Destroy()
			end
		end
	end
	for _, p in sc.sheath or {} do p.LocalTransparencyModifier = if on then 1 else 0 end
	if on then
		if not sc.backdrop then
			local b = part(sc.folder, Vector3.new(3000, 3000, 1), ORIGIN, PAPER, Enum.Material.Neon)
			sc.backdrop = b
		end
		sc.backdrop.Color = BG
		sc.backdrop.LocalTransparencyModifier = 0
		if sc.trail then sc.trail.Color = ColorSequence.new(s.row.colour) end
		for _, p in accent or {} do
			sc.orig[p] = sc.orig[p] or { p.Color, p.Material }
			p.Color = s.row.colour; p.Material = Enum.Material.Neon
		end
	else
		if sc.backdrop then sc.backdrop.LocalTransparencyModifier = 1 end
		if sc.trail then sc.trail.Color = ColorSequence.new(SMEAR) end
		for p, o in sc.orig do p.Color = o[1]; p.Material = o[2] end
		table.clear(sc.orig)
	end
end

-- ------------------------------------------------------------------ v2 (Tidecrest v4.2, 20 Nov): the plan's semantic layer
-- the scabbard in the left hand or on the hip, the blade's mode (hand / the pack's own sword track / trailing / home /
-- through the mouth / streaming out / aimed), lenses and effects riding on the real bodies, two-clip blends, afterimages,
-- each body grounded by its lowest point (the stand-in's legs aren't the player's)

local PACK_C0 = CFrame.new(0, 0, 0, 1, 0, 0, 0, 0, 1, 0, -1, 0) -- (the pack's sword handle off the right hand)
local BODYP = { "Head", "UpperTorso", "LowerTorso", "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm",
	"RightLowerArm", "RightHand", "LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "RightUpperLeg", "RightLowerLeg", "RightFoot" }

local function gripR(m: Model): CFrame?
	local h = m:FindFirstChild("RightHand") :: BasePart?
	if not h then return nil end
	return h.CFrame * CFrame.new(0, -0.4 * h.Size.Y, 0)
end

-- the lowest point of a body's own parts (accessories don't count), world y
local function lowestOf(m: Model): number
	local y = math.huge
	for _, n in BODYP do
		local p = m:FindFirstChild(n) :: BasePart?
		if p then
			local cf, h = p.CFrame, p.Size / 2
			for _, sx in { -1, 1 } do for _, sy in { -1, 1 } do for _, sz in { -1, 1 } do
				y = math.min(y, (cf * Vector3.new(sx * h.X, sy * h.Y, sz * h.Z)).Y)
			end end end
		end
	end
	return y
end

-- a body's tracks: one per clip; this frame's clip at its moment, a second blended in at its weight, the rest stopped
local function trackOf(sc: any, who: string, g: any, ci: number): AnimationTrack?
	sc.tracks[who] = sc.tracks[who] or {}
	local have = sc.tracks[who][ci]
	if have then return have end
	local clip = sc.d.clips[ci]
	local id = Finishers.SCENE_ANIMS[clip]
	if not id then return nil end
	local an = (g.hum :: Humanoid):FindFirstChildOfClass("Animator")
	if not an then return nil end
	local a = Instance.new("Animation")
	a.AnimationId = "rbxassetid://" .. id
	local ok, tr = pcall(function() return (an :: Animator):LoadAnimation(a) end)
	if not ok or not tr then return nil end
	tr.Looped = false
	tr.Priority = Enum.AnimationPriority.Action4
	sc.tracks[who][ci] = tr
	return tr
end

local function setTime(tr: AnimationTrack, t: number)
	local L = tr.Length
	if L > 0 then
		-- (a clip the plan loops - the run, the idle - wraps; others hold their ends)
		t = if t > L then t % L else math.clamp(t, 0, L - 1 / 60)
	end
	tr.TimePosition = t
end

local function poseV2(sc: any, who: string, g: any, e: any, ground: number?)
	local ci, t, ci2, t2, w2 = e[1], e[2], e[5], e[6], e[7]
	local want = { [ci] = if ci2 then 1 - w2 else 1 }
	if ci2 then want[ci2] = w2 end
	for c, w in want do
		local tr = trackOf(sc, who, g, c)
		if tr then
			if not tr.IsPlaying then tr:Play(0, math.max(w, 0.001), 0) else tr:AdjustWeight(math.max(w, 0.001), 0) end
			setTime(tr, if c == ci then t else t2)
		end
	end
	for c, tr in sc.tracks[who] or {} do
		if not want[c] and tr.IsPlaying then tr:Stop(0) end
	end
	local root = ORIGIN * cfOf(e[3]) + Vector3.new(0, sc.hip[who] - RIG_HIP, 0)
	-- grounding: last frame's real lowest point against the stand-in's, carried as a running offset (the pose the
	-- Animator shows is a frame behind the moment set here)
	if ground and sc.lowWas[who] then
		sc.gOff[who] = (sc.gOff[who] or 0) + (ORIGIN.Y + ground) - sc.lowWas[who]
		sc.gOff[who] = math.clamp(sc.gOff[who], -3, 3)
	end
	g.root.CFrame = root + Vector3.new(0, sc.gOff[who] or 0, 0)
end

-- the afterimages: copies of the killer, posed a moment behind, see-through
local function ghosts(sc: any, s: any, list: any)
	sc.ghosts = sc.ghosts or {}
	for gi, e in list or {} do
		local gh = sc.ghosts[gi]
		if not gh then
			local ok, m = pcall(function() return (s.kg.model :: Model):Clone() end)
			if not ok or not m then return end
			m.Name = "JankSceneGhost" .. gi
			for _, d in m:GetDescendants() do
				if d:IsA("BaseScript") then d:Destroy() elseif d:IsA("BasePart") then d.CanCollide = false; d.CanQuery = false; d.CanTouch = false end
			end
			m.Parent = sc.folder
			local hum = m:FindFirstChildOfClass("Humanoid")
			local hrp = m:FindFirstChild("HumanoidRootPart") :: BasePart?
			if not hum or not hrp then m:Destroy(); return end
			hrp.Anchored = true
			gh = { model = m, hum = hum, root = hrp }
			sc.ghosts[gi] = gh
			sc.hip["g" .. gi] = sc.hip.k
		end
		poseV2(sc, "g" .. gi, gh, e, nil)
		for _, d in gh.model:GetDescendants() do
			if d:IsA("BasePart") and d.Name ~= "HumanoidRootPart" then d.LocalTransparencyModifier = e[4]
			elseif d:IsA("Decal") then d.LocalTransparencyModifier = e[4] end
		end
		gh.model.Parent = sc.folder
	end
	for gi = #(list or {}) + 1, #sc.ghosts do sc.ghosts[gi].model.Parent = nil end
end

-- (the eyes' height on this head, in the head's own space, or nil: a dynamic head's eye bones, else a face accessory
-- that sits on the eyes (glasses, a visor). The owner, on High Noon: the eye shots missed the eyes - their avatar's
-- eyes sit ~0.4 lower than the stand-in's (its glasses at -0.15 against the stand-in's eyes at +0.24))
local function eyeY(p: BasePart, k: number): number?
	local sum, n = 0, 0
	for _, b in p:GetDescendants() do
		if b:IsA("Bone") then
			local nm = string.lower(b.Name)
			if (nm == "lefteye" or nm == "righteye") then
				sum += p.CFrame:PointToObjectSpace(b.WorldPosition).Y
				n += 1
			end
		end
	end
	if n > 0 then return sum / n end
	local m = p.Parent
	if not m then return nil end
	for _, acc in m:GetChildren() do
		if acc:IsA("Accessory") and acc.AccessoryType == Enum.AccessoryType.Face then
			local h = acc:FindFirstChild("Handle") :: BasePart?
			local at = h and h:FindFirstChildOfClass("Attachment")
			if h and at and (at.Name == "FaceFrontAttachment" or at.Name == "FaceCenterAttachment") then
				local rel = p.CFrame:PointToObjectSpace(h.Position)
				-- (in front of the face, centred, near the middle of the head: a beard or a collar sits lower)
				if math.abs(rel.X) < 0.3 * k and rel.Z < 0 and math.abs(rel.Y) < 0.35 * k then return rel.Y end
			end
		end
	end
	return nil
end
-- the real body point an anchor names (this frame), and the stand-in's (from the data); offsets scale by the part
local ANCH = { kH = { "k", "Head" }, kU = { "k", "UpperTorso" }, kL = { "k", "LowerTorso" }, vH = { "v", "Head" },
	vU = { "v", "UpperTorso" }, vL = { "v", "LowerTorso" }, kR = { "k", "RightHand" }, vR = { "v", "RightHand" } }
local function realAnchor(sc: any, s: any, key: string): (CFrame?, number)
	if key == "mouth" then return sc.mouthCF, 1 end
	local a = ANCH[key]
	if not a then return nil, 1 end
	local g = if a[1] == "k" then s.kg else s.vg
	local p = g.model:FindFirstChild(a[2]) :: BasePart?
	if not p then return nil, 1 end
	local sz = sc.d.sizes and sc.d.sizes[a[2]]
	local k = if sz then p.Size.Y / sz[2] else 1
	if a[2] == "Head" then
		-- (the real face, not the head part's middle - the owner, on High Noon: "the next scene isn't really at the eyes":
		-- an anime head, a big hat or hair puts the eyes elsewhere. The stand-in's face front, (0, 0, -0.6) on its 1.2
		-- head, lands on this head's own FaceFrontAttachment)
		local ffa = p:FindFirstChild("FaceFrontAttachment")
		if ffa and ffa:IsA("Attachment") then
			local off = ffa.Position - Vector3.new(0, 0, -0.6) * k
			-- (and at the eyes' own height when this head says where they are: the stand-in's eyes are at +0.24)
			local ey = eyeY(p, k)
			if ey then off = Vector3.new(off.X, ey - 0.24 * k, off.Z) end
			return p.CFrame * CFrame.new(off), k
		end
	end
	return p.CFrame, k
end
-- (the scene's own colour grade this frame, when it has one: Finisher.luau's grade asks; nil = the finisher's own)
function Scene.grade(s: any): { tint: Color3, sat: number, con: number, bright: number }?
	local sc = s.scene
	local g = sc and sc.ex and sc.ex.grade
	if not g then return nil end
	local k = if sc.gradeAt then math.clamp((s.w - sc.gradeAt) / g.over, 0, 1) else 0
	k = k * k * (3 - 2 * k)
	local a, b = g.warm, g.cold
	return { tint = a.tint:Lerp(b.tint, k), sat = a.sat + (b.sat - a.sat) * k, con = a.con + (b.con - a.con) * k,
		bright = a.bright + (b.bright - a.bright) * k }
end
-- (how long the letterbox bars take to come in, when a scene says: Finisher.luau's overlay asks)
function Scene.barsIn(s: any): number?
	local sc = s.scene
	return sc and sc.ex and sc.ex.barsIn or nil
end
local function rehang(sc: any, s: any, f: any, key: string?, cfW: CFrame, fb: any?, a: number?): CFrame
	if not key or key == "" or not f.an or not f.an[key] then return cfW end
	local real, k = realAnchor(sc, s, key)
	if not real then return cfW end
	-- (between two plan frames the stand-in's point moves on as smoothly as the real body does: blend it the same way.
	-- Held at frame A, a moving hip jolted the lens back at every plan frame - the owner, 20 Nov: "after the second zoom
	-- in of the eyes the camera gets really shakey")
	local pa = cfOf(f.an[key])
	if fb and a and a > 0 and fb.an and fb.an[key] then pa = pa:Lerp(cfOf(fb.an[key]), a) end
	local rel = (ORIGIN * pa):Inverse() * cfW
	return real * (CFrame.new(rel.Position * k) * rel.Rotation)
end

-- the scabbard and the blade from the killer's own hands (v2 plans: f.sh / f.kat modes)
local function placeKitV2(sc: any, s: any, f: any)
	local m = s.kg.model :: Model
	local lt = m:FindFirstChild("LowerTorso") :: BasePart?
	local lh = m:FindFirstChild("LeftHand") :: BasePart?
	local rh = m:FindFirstChild("RightHand") :: BasePart?
	local g0 = gripR(m)
	sc.mouthCF = nil
	local mouth: Vector3?, d: Vector3? = nil, nil
	local sh = f.sh
	if sh and lt then
		if sh[1] == 1 and lh and g0 then
			local rp, lp = g0.Position, lh.Position
			d = (lp - rp).Unit
			mouth = lp - (d :: Vector3) * (sc.m0 or sh[2])
			if sh[3] and sh[3] ~= 0 then mouth = (mouth :: Vector3) + lt.CFrame.LookVector * sh[3] end
		else
			mouth = lt.CFrame * Vector3.new(-0.95, 0.1, -0.75)
			d = ((lt.CFrame * Vector3.new(-1.25, -1.6, 2.2)) - (mouth :: Vector3)).Unit
		end
		sc.mouthCF = CFrame.lookAt(mouth :: Vector3, (mouth :: Vector3) + (d :: Vector3))
		local up = lt.CFrame.YVector
		local a = mouth :: Vector3
		local dd = d :: Vector3
		between(sc.sheath[1], a, a + dd * 3.3, 0.22, 0.4, up)
		between(sc.sheath[2], a + dd * 0.3, a + dd * 0.5, 0.26, 0.44, up)
		between(sc.sheath[3], a + dd * 3.05, a + dd * 3.3, 0.26, 0.44, up)
		for _, p in sc.sheath do p.LocalTransparencyModifier = 0 end
	else
		for _, p in sc.sheath do p.LocalTransparencyModifier = 1 end
	end
	local k = f.kat
	local L = f.L or 1
	local grip: CFrame? = nil
	if k and g0 then
		local mode = k[1]
		if mode == 1 then
			grip = g0
		elseif (mode == 3 or mode == 8) and rh then
			grip = rh.CFrame * PACK_C0 * cfOf(k[2]) * CFrame.Angles(math.rad(90), 0, 0)
			if mode == 8 then
				-- (turned toward the victim's face, its tip a hair short of it)
				local vh = s.vg.model:FindFirstChild("Head") :: BasePart?
				local w = k[4] or 1
				if vh and grip then
					local gp = (grip :: CFrame).Position
					-- (the blade runs along the grip's -Z, i.e. its LookVector, so the look goes AT the face: the
					-- first in-game try looked away and THE TIP showed no blade)
					local want = (vh.Position - gp).Unit
					local turned = CFrame.lookAt(gp, gp + want, Vector3.yAxis)
					grip = (grip :: CFrame):Lerp(turned, w)
					L = L * (1 - w) + math.max(1, ((vh.Position - gp).Magnitude - 0.95 - 0.6) / 2.3) * w
				end
			end
		elseif mode == 4 and lt then
			local lk = lt.CFrame.LookVector
			lk = Vector3.new(lk.X, 0, lk.Z).Unit
			local dirv = (-lk * 0.93 + Vector3.new(0, -0.36, 0)).Unit
			grip = CFrame.lookAt(g0.Position, g0.Position + dirv)
		elseif mode == 5 and mouth and d then
			local gp = (mouth :: Vector3) - (d :: Vector3) * ((k[2] or 0) + 0.44)
			grip = CFrame.lookAt(gp, gp + (d :: Vector3))
			L = 1
		elseif mode == 6 and mouth and d then
			local v = (mouth :: Vector3) - g0.Position
			if v.Magnitude < 0.5 then
				local gp = (mouth :: Vector3) - (d :: Vector3) * 0.44
				grip = CFrame.lookAt(gp, gp + (d :: Vector3)); L = 1
			else
				grip = CFrame.lookAt(g0.Position, g0.Position + v.Unit)
				L = math.max(1, (v.Magnitude + 2.4) / 2.3)
			end
		elseif mode == 7 and mouth and d then
			local gp = (mouth :: Vector3) - (d :: Vector3) * (k[2] + 0.44)
			grip = CFrame.lookAt(gp, gp + (d :: Vector3))
		end
	end
	-- (a grown blade lands the skin's own tip, sc.katTip, on the plan's -(0.6 + 2.3 L); a normal one keeps the skin's
	-- length - blended over L 1..2 so the growth has no jump)
	local den = 2.46 + ((-(sc.katTip or -2.9) - 0.44) - 2.46) * math.clamp(L - 1, 0, 1)
	local Ls = (0.16 + 2.3 * L) / den
	for _, e in sc.kat do
		e.p.LocalTransparencyModifier = if grip then 0 else 1
		if grip then
			local rel = e.rel
			if Ls ~= 1 and rel.Position.Z < -0.6 then
				rel = CFrame.new(rel.Position.X, rel.Position.Y, -0.44 + (rel.Position.Z + 0.44) * Ls) * rel.Rotation
				if e.L ~= Ls then
					local ax = { math.abs(rel.XVector.Z), math.abs(rel.YVector.Z), math.abs(rel.ZVector.Z) }
					local sz = e.size
					e.p.Size = if ax[1] >= ax[2] and ax[1] >= ax[3] then Vector3.new(sz.X * Ls, sz.Y, sz.Z)
						elseif ax[2] >= ax[3] then Vector3.new(sz.X, sz.Y * Ls, sz.Z) else Vector3.new(sz.X, sz.Y, sz.Z * Ls)
				end
			elseif e.L ~= Ls then
				e.p.Size = e.size
			end
			e.L = Ls
			e.p.CFrame = (grip :: CFrame) * rel
		end
	end
	if grip then
		sc.carrier.CFrame = grip
		sc.tipA.Position = Vector3.new(0, 0, -(0.6 + 2.3 * L))
	end
end

-- ------------------------------------------------------------------ High Noon: the revolvers (20 Nov)
-- each body's own holster on its hip (a belt and a leather pouch sized to its hips), its revolver in the holster or in
-- its hand (grip in the palm), the right arm reaching onto the gun through the draw (an IKControl: the hand hovers over
-- the grip, closes on it, carries it out - the owner: "make the hand reach closer to the gun and pull the gun!"), and
-- the killer's gun's last moments kept for the smear and the afterimage guns
local LEATHER = Color3.fromRGB(107, 69, 41)
local function revolverKit(sc: any, s: any)
	sc.rev, sc.revModels, sc.gunHist = {}, {}, {}
	sc.sheath = {}
	local skins = ReplicatedStorage:FindFirstChild("JankfireSkins")
	for _, who in { "k", "v" } do
		local g = if who == "k" then s.kg else s.vg
		local m = g.model :: Model
		local lt = m:FindFirstChild("LowerTorso") :: BasePart?
		if lt then
			local hw, hd = lt.Size.X / 2, lt.Size.Z / 2
			local lh = lt:FindFirstChild("LeftHipRigAttachment")
			if lh and lh:IsA("Attachment") then hw = math.max(hw, math.abs(lh.Position.X) + 0.45) end
			for _, d in m:GetDescendants() do if d:IsA("WrapLayer") then hw *= 1.12; hd *= 1.18; break end end
			local km = Instance.new("Model")
			km.Name = "JankRev" .. who
			km.Parent = sc.folder
			table.insert(sc.revModels, km)
			local kit: any = { hw = hw, hd = hd, leg = (g.hum :: Humanoid).HipHeight / 2, km = km }
			kit.holster = part(km, Vector3.new(0.32, 0.95, 0.55), ORIGIN, LEATHER, Enum.Material.Leather)
			kit.belt = part(km, Vector3.new(2 * hw * 1.06, 0.28, 2 * hd * 1.1), ORIGIN, LEATHER, Enum.Material.Leather)
			local want = if who == "k" and type(s.msg.skin) == "string" then s.msg.skin else "revolver_dust"
			local tpl = skins and (skins:FindFirstChild(want) or skins:FindFirstChild("revolver_dust"))
			local function build(tr: number): { any }
				local out = {}
				if not tpl then return out end
				local c = tpl:Clone()
				for _, p in c:GetDescendants() do
					if p:IsA("BasePart") then
						local oc = p.CFrame
						p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
						p.Size *= 3
						p.Transparency = math.max(p.Transparency, tr)
						table.insert(out, { p, CFrame.new(oc.Position * 3) * oc.Rotation })
					elseif p:IsA("BaseScript") or p:IsA("JointInstance") or p:IsA("Constraint") then
						p:Destroy()
					end
				end
				c.Parent = km
				return out
			end
			kit.parts = build(0)
			if who == "k" then kit.ghosts = { build(0.55), build(0.78) } end
			-- (the grip and the muzzle in the skin's own frame, x3: its attachments, or - the Dust revolver has none -
			-- the grip the runner used and the front-most corner of its parts, the barrel running along -Z)
			local ga = tpl and tpl:FindFirstChild("Grip", true)
			kit.grip = if ga and ga:IsA("Attachment") then ga.WorldPosition * 3 else Vector3.new(0, -0.55, 0.25)
			local ma = tpl and tpl:FindFirstChild("Muzzle", true)
			if ma and ma:IsA("Attachment") then
				kit.muzzle = ma.WorldPosition * 3
			else
				local minZ, at = math.huge, Vector3.zero
				for _, bp in (if tpl then tpl:GetDescendants() else {}) :: { Instance } do
					if bp:IsA("BasePart") then
						for _, sx in { -1, 1 } do for _, sy in { -1, 1 } do for _, sz in { -1, 1 } do
							local w = bp.CFrame * Vector3.new(sx * bp.Size.X / 2, sy * bp.Size.Y / 2, sz * bp.Size.Z / 2)
							if w.Z < minZ then minZ, at = w.Z, w end
						end end end
					end
				end
				kit.muzzle = at * 3
			end
			-- the reach: an IKControl on the right arm, aimed at an attachment on a hidden anchor
			local ua = m:FindFirstChild("RightUpperArm")
			local hand = m:FindFirstChild("RightHand")
			if ua and hand and ua:IsA("BasePart") and hand:IsA("BasePart") then
				local holder = part(sc.folder, Vector3.one * 0.1, ORIGIN, LEATHER)
				holder.Transparency = 1
				local att = Instance.new("Attachment")
				att.Parent = holder
				local ik = Instance.new("IKControl")
				ik.Type = Enum.IKControlType.Transform
				ik.ChainRoot = ua; ik.EndEffector = hand; ik.Target = att
				ik.Weight = 0
				pcall(function() (ik :: any).SmoothTime = 0 end)
				ik.Parent = g.hum
				kit.ik, kit.att = ik, att
			end
			sc.rev[who] = kit
		end
	end
end
local function placeRevolvers(sc: any, s: any, A: any, T: number)
	for _, who in { "k", "v" } do
		local g = if who == "k" then s.kg else s.vg
		local kit = sc.rev[who]
		local m = g.model :: Model
		local lt = m:FindFirstChild("LowerTorso") :: BasePart?
		local hand = m:FindFirstChild("RightHand") :: BasePart?
		if kit and lt and hand then
			local hcf = lt.CFrame * CFrame.new(kit.hw * 1.12, -0.45 * kit.leg, -0.05)
			kit.holster.CFrame = hcf
			kit.belt.CFrame = lt.CFrame * CFrame.new(0, 0.05, 0)
			local inH = hcf * CFrame.new(0, 0.15, 0) * CFrame.Angles(math.rad(-90), 0, 0) * CFrame.new(0, 0, -0.1)
			local onGrip = inH * CFrame.new(kit.grip) * CFrame.Angles(math.rad(90), 0, 0) * CFrame.new(0, 0.4 * hand.Size.Y, 0)
			-- the reach, by the draw's clock: hover over the grip, close on it, carry it out (the re-holster plays the draw
			-- backwards, so the hand goes home the same way)
			local e = A[who]
			local w, target = 0, nil
			if e and not e[5] and sc.d.clips[e[1]] == "quick_draw_t1" then
				local t = e[2]
				local hr = sc.ex.holdReach and sc.ex.holdReach[who]
				local fi = T * sc.d.fps + 1
				-- (a held reach: from its shot on, the hand closes on the grip by the shot's end and rests there - whatever the
				-- clip does - until the draw itself carries it on, past the moment the plain reach is on the grip anyway)
				local held = hr ~= nil and fi >= hr.from and t < 0.28
				local u = if held then math.clamp((fi - hr.from) / math.max(hr.to - hr.from, 1), 0, 1) else 0
				-- (held: most of the way on the hand from the shot's first frame, so the shake shows as it starts to move -
				-- the owner: "can it be shakey from the moment the shot happens")
				w = if held then 0.6 + 0.4 * ease(u / 0.5) else ease(t / 0.12) * (1 - ease((t - 0.34) / 0.2))
				if w > 0.002 then
					local ua = m:FindFirstChild("RightUpperArm") :: BasePart?
					local up = if ua then (ua.Position - onGrip.Position) * 0.2 else Vector3.zero
					local hover = CFrame.new(up + lt.CFrame:VectorToWorldSpace(Vector3.new(0.12, 0, -0.04))) * onGrip
					target = hover:Lerp(onGrip, if held then ease((u - 0.35) / 0.65) else ease((t - 0.14) / 0.14))
					-- (the nervous hand - the owner, 20 Nov: "also the enemy hand shaking was removed!": the plan shakes it by
					-- jittering the clip's time round the moment, 0.012 s * sin(frame * 2.3), which swung the old reach's
					-- weight and so the hand. Held on the grip, the same jitter now lifts it off the grip toward the hover and
					-- back, up to 0.12 studs, until the draw's own reach takes over)
					if held and target then
						local calm = 1 - ease((t - 0.1) / 0.12)
						local lift = hover.Position - onGrip.Position
						local dirUp = if lift.Magnitude > 1e-3 then lift.Unit else Vector3.yAxis
						target = target + dirUp * (0.06 + 0.06 * math.sin(fi * 2.3)) * calm
					end
				end
			end
			if kit.ik then
				kit.ik.Weight = w
				if target then kit.att.WorldCFrame = target end
			end
			-- (the gun goes in the hand where the hand IS: the IK already moved it. blending toward the target again pulled
			-- the gun off the hand - the owner: "after the enemy goes for the gun their hands aren't on the gun")
			local H = hand.CFrame
			local gcf: CFrame? = nil
			if A.gn and A.gn[who] == 1 then
				local pc = H * CFrame.new(0, -0.4 * hand.Size.Y, 0)
				gcf = CFrame.new(pc.Position) * pc.Rotation * CFrame.Angles(math.rad(-90), 0, 0) * CFrame.new(-kit.grip)
			elseif A.hol and A.hol[who] == 1 then
				gcf = inH
			end
			for _, q in kit.parts do
				if gcf then q[1].CFrame = (gcf :: CFrame) * q[2]; q[1].LocalTransparencyModifier = 0 else q[1].LocalTransparencyModifier = 1 end
			end
			kit.gcf = gcf
			for _, gl in kit.ghosts or {} do for _, q in gl do q[1].LocalTransparencyModifier = 1 end end
			if who == "k" and gcf then
				table.insert(sc.gunHist, { T, gcf })
				while #sc.gunHist > 1 and T - sc.gunHist[1][1] > 0.35 do table.remove(sc.gunHist, 1) end
			end
		end
	end
end
-- the killer's gun as it was dt ago (the nearest kept moment)
local function gunAt(sc: any, T: number): CFrame?
	local best = nil
	for _, h in sc.gunHist do if not best or math.abs(h[1] - T) < math.abs(best[1] - T) then best = h end end
	return best and best[2]
end

-- effects (the plan's fx list): each drawn this frame from pooled parts; what isn't drawn this frame hides
local function fxPart(sc: any, key: string, n: number, make: () -> Part): Part
	sc.pools[key] = sc.pools[key] or {}
	local pool = sc.pools[key]
	while #pool < n do table.insert(pool, make()) end
	sc.used[key] = math.max(sc.used[key] or 0, n)
	return pool[n]
end
local function P3(sc: any, s: any, f: any, an: string?, x: number, y: number, z: number): Vector3
	return rehang(sc, s, f, an, ORIGIN * CFrame.new(x, y, z)).Position
end
local function drawFx(sc: any, s: any, f: any, T: number)
	table.clear(sc.used)
	for idx, e in f.fx or {} do
		local an, kind = e[1], e[2]
		if kind == "ring" then
			local c = P3(sc, s, f, an, e[3], e[4], e[5])
			local fw = (P3(sc, s, f, an, e[11], e[12], e[13]) - c).Unit
			local ux = fw:Cross(Vector3.yAxis)
			ux = if ux.Magnitude > 1e-3 then ux.Unit else Vector3.xAxis
			local uy = ux:Cross(fw).Unit
			local rnd = Random.new(e[10])
			for j = 1, e[8] do
				local a = 2 * math.pi * (j - 1) / e[8] + rnd:NextNumber(-0.12, 0.12)
				local dv = ux * math.cos(a) + uy * math.sin(a)
				local p = fxPart(sc, "ring" .. idx, j, function() return part(sc.folder, Vector3.one, ORIGIN, SMEAR, Enum.Material.Neon) end)
				between(p, c + dv * e[6] * rnd:NextNumber(0.9, 1.2), c + dv * e[7] * rnd:NextNumber(0.8, 1.15), 0.02, 0.035, fw)
				p.LocalTransparencyModifier = 0
				table.insert(sc.accent, p)
			end
		elseif kind == "stroke" then
			local a = P3(sc, s, f, an, e[3], e[4], e[5])
			local b = P3(sc, s, f, an, e[6], e[7], e[8])
			local fc = (P3(sc, s, f, an, e[11], e[12], e[13]) - a).Unit
			local key = "stroke" .. idx
			local col = if e[14] == 0 then INK else s.row.colour
			local n = 16
			local dd = b - a
			local side = dd:Cross(fc).Unit
			local rnd = Random.new(e[15])
			for i = 1, n do
				local p0 = a + dd * ((i - 1) / n) + side * (e[9] * math.sin(math.pi * (i - 1) / n))
				local p1 = a + dd * (i / n) + side * (e[9] * math.sin(math.pi * i / n))
				local t = (i - 0.5) / n
				local w = e[10] * (math.sin(math.pi * math.min(1, t * 1.1)) ^ 0.6) * rnd:NextNumber(0.75, 1) + 0.02
				local p = fxPart(sc, key, i, function() return part(sc.folder, Vector3.one, ORIGIN, col, if col == INK then Enum.Material.Neon else Enum.Material.SmoothPlastic) end)
				p.Color = col
				between(p, p0, p1, 0.06, w, side)
				p.LocalTransparencyModifier = 0
				p.Transparency = e[16] or 0
				table.insert(sc.accent, p)
			end
		elseif kind == "burst" then
			local c = P3(sc, s, f, an, e[3], e[4], e[5])
			burst(sc, "burst" .. idx, c, e[6], e[7], e[8], e[9], e[10] == 1, e[11])
			for i = 1, e[6] do sc.pools["burst" .. idx][i].LocalTransparencyModifier = 0 end
			sc.used["burst" .. idx] = e[6]
		elseif kind == "drift" then
			local key = "drift" .. idx
			local pool = petalPool(sc, key, e[6])
			local rnd = Random.new(e[9])
			local base0 = P3(sc, s, f, an, e[3], e[4], e[5])
			local vel = Vector3.new(e[11], e[12], e[13])
			local t = e[8]
			for i = 1, e[6] do
				local bp = base0 + Vector3.new(rnd:NextNumber(-1, 1), rnd:NextNumber(-0.6, 1), rnd:NextNumber(-1, 1)) * e[7]
				local ph = rnd:NextNumber(0, 6.28)
				local ax, ay, az = rnd:NextNumber(0, 6.28), rnd:NextNumber(0, 6.28), rnd:NextNumber(0, 6.28)
				local q = bp + vel * t + Vector3.new(math.sin(ph + t * 3) * 0.25, math.cos(ph + t * 2.3) * 0.12, 0)
				pool[i].CFrame = CFrame.new(q) * CFrame.Angles(ax + 2.4 * t, ay + 1.7 * t, az)
				pool[i].LocalTransparencyModifier = 0
			end
			sc.used[key] = e[6]
		elseif kind == "splats" then
			local c = P3(sc, s, f, an, e[3], e[4], e[5])
			local rnd = Random.new(e[8])
			for i = 1, e[6] do
				local p = fxPart(sc, "splats" .. idx, i, function() return part(sc.folder, Vector3.one * 0.2, ORIGIN, INK, Enum.Material.SmoothPlastic, Enum.PartType.Ball) end)
				local q = c + Vector3.new(rnd:NextNumber(-1, 1), rnd:NextNumber(-1, 1), rnd:NextNumber(-1, 1)) * e[7]
				local sz = 0.18 * e[9] * rnd:NextNumber(0.6, 1.6)
				p.Size = Vector3.one * sz
				p.CFrame = CFrame.new(q)
				p.LocalTransparencyModifier = 0
				table.insert(sc.accent, p)
			end
		elseif kind == "glint" then
			local c = P3(sc, s, f, an, e[3], e[4], e[5])
			local sz = math.max(0.3, e[6])
			local a1 = fxPart(sc, "glint" .. idx, 1, function() return part(sc.folder, Vector3.one, ORIGIN, PAPER, Enum.Material.Neon) end)
			local a2 = fxPart(sc, "glint" .. idx, 2, function() return part(sc.folder, Vector3.one, ORIGIN, PAPER, Enum.Material.Neon) end)
			local cam = (workspace.CurrentCamera :: Camera).CFrame
			a1.Size = Vector3.new(0.04, sz, 0.04); a1.CFrame = CFrame.lookAt(c, c + cam.LookVector)
			a2.Size = Vector3.new(sz, 0.04, 0.04); a2.CFrame = CFrame.lookAt(c, c + cam.LookVector)
			a1.LocalTransparencyModifier = 0; a2.LocalTransparencyModifier = 0
		elseif kind == "sweat" then
			local c = P3(sc, s, f, an, e[3], e[4], e[5])
			local p = fxPart(sc, "sweat" .. idx, 1, function()
				local q = part(sc.folder, Vector3.new(0.16, 0.22, 0.16), ORIGIN, Color3.new(0.85, 0.93, 1), Enum.Material.Glass, Enum.PartType.Ball)
				q.Transparency = 0.15
				return q
			end)
			p.CFrame = CFrame.new(c)
			p.LocalTransparencyModifier = 0
		elseif kind == "tumble" then
			-- (High Noon) a tumbleweed: 44 twigs round its centre, the same twigs every frame, turned as it rolls
			local c = P3(sc, s, f, an, e[3], e[4], e[5])
			local ax = Vector3.new(e[8], e[9], e[10])
			local R = CFrame.fromAxisAngle(if ax.Magnitude > 1e-3 then ax.Unit else Vector3.xAxis, e[7])
			sc.twigs = sc.twigs or {}
			local tw = sc.twigs[e[11]]
			if not tw then
				tw = {}
				local rnd = Random.new(e[11])
				local function dir(): Vector3
					local v = Vector3.new(rnd:NextNumber(-1, 1), rnd:NextNumber(-1, 1), rnd:NextNumber(-1, 1))
					return if v.Magnitude > 1e-3 then v.Unit else Vector3.yAxis
				end
				for _ = 1, 44 do table.insert(tw, { dir() * rnd:NextNumber(0.6, 1), dir() * rnd:NextNumber(0.6, 1) }) end
				sc.twigs[e[11]] = tw
			end
			for j, q in tw do
				local p = fxPart(sc, "tumble" .. idx, j, function()
					return part(sc.folder, Vector3.one, ORIGIN, if j % 3 == 0 then Color3.new(0.5, 0.38, 0.24) else Color3.new(0.6, 0.46, 0.3))
				end)
				between(p, c + R:VectorToWorldSpace(q[1] * e[6]), c + R:VectorToWorldSpace(q[2] * e[6]), 0.07, 0.07, Vector3.yAxis)
				p.LocalTransparencyModifier = 0
			end
		elseif kind == "flash" or kind == "shock" then
			-- (High Noon) a muzzle flash at the killer's real muzzle; the shock where the shot lands, on the real chest
			local kit = sc.rev and sc.rev.k
			local c: Vector3, fw: Vector3
			if kind == "flash" and kit and kit.gcf then
				c = ((kit.gcf :: CFrame) * CFrame.new(kit.muzzle)).Position
				fw = (kit.gcf :: CFrame).LookVector
			else
				c = P3(sc, s, f, an, e[3], e[4], e[5])
				local v = Vector3.new(e[7], e[8], e[9])
				fw = if v.Magnitude > 1e-3 then v.Unit else Vector3.zAxis
			end
			local size, rays = e[6], e[10]
			local ux = fw:Cross(Vector3.yAxis)
			ux = if ux.Magnitude > 1e-3 then ux.Unit else Vector3.xAxis
			local uy = fw:Cross(ux).Unit
			local rnd = Random.new(e[11])
			local col = if kind == "flash" then Color3.new(1, 0.93, 0.62) else Color3.new(1, 0.95, 0.85)
			for j = 1, rays do
				local a = 2 * math.pi * (j - 1) / rays + rnd:NextNumber() * 0.4
				local dv = ux * math.cos(a) + uy * math.sin(a)
				local p = fxPart(sc, kind .. idx, j, function() return part(sc.folder, Vector3.one, ORIGIN, col, Enum.Material.Neon) end)
				between(p, c, c + dv * size * rnd:NextNumber(0.7, 1.3), size * 0.14, size * 0.05, fw)
				p.LocalTransparencyModifier = 0
				if kind == "shock" then table.insert(sc.accent, p) end
			end
			local b = fxPart(sc, kind .. idx, rays + 1, function() return part(sc.folder, Vector3.one, ORIGIN, col, Enum.Material.Neon, Enum.PartType.Ball) end)
			b.Size = Vector3.one * size * 0.5
			b.CFrame = CFrame.new(c)
			b.LocalTransparencyModifier = 0
			if kind == "shock" then table.insert(sc.accent, b) end
		elseif kind == "smoke" then
			local c = P3(sc, s, f, an, e[3], e[4], e[5])
			local p = fxPart(sc, "smoke" .. idx, 1, function()
				local q = part(sc.folder, Vector3.one, ORIGIN, Color3.new(0.78, 0.76, 0.74), Enum.Material.SmoothPlastic, Enum.PartType.Ball)
				q.Transparency = 0.35
				return q
			end)
			p.Size = Vector3.one * e[3 + 3]
			p.CFrame = CFrame.new(c)
			p.LocalTransparencyModifier = 0
		elseif kind == "gsmear" then
			-- (High Noon) the gun's swing out of the holster: its muzzle's path over the last 0.16 s, bright and thinning,
			-- and two fading copies of the gun behind it - from the real gun's own last moments
			local kit = sc.rev and sc.rev.k
			if kit and #sc.gunHist >= 2 then
				local pts = {}
				for j = 0, 6 do
					local gj = gunAt(sc, T - 0.16 * j / 6)
					if gj then table.insert(pts, (gj * CFrame.new(kit.muzzle * 0.8)).Position) end
				end
				for j = 1, #pts - 1 do
					local p = fxPart(sc, "gsmear" .. idx, j, function() return part(sc.folder, Vector3.one, ORIGIN, Color3.new(1, 0.92, 0.7), Enum.Material.Neon) end)
					if (pts[j] - pts[j + 1]).Magnitude > 0.02 then
						between(p, pts[j + 1], pts[j], 0.08, 0.32 * (1 - (j - 1) / 7), Vector3.yAxis)
						p.Transparency = 0.15 + 0.12 * (j - 1)
						p.LocalTransparencyModifier = 0
					else
						p.LocalTransparencyModifier = 1
					end
				end
				for j, dt in { 0.05, 0.1 } do
					local gj = gunAt(sc, T - dt)
					local gl = kit.ghosts and kit.ghosts[j]
					if gj and gl then for _, q in gl do q[1].CFrame = gj * q[2]; q[1].LocalTransparencyModifier = 0 end end
				end
			end
		elseif kind == "dustc" then
			-- (High Noon) the dust round the fallen one: 16 puffs spreading and fading
			local c0 = P3(sc, s, f, an, e[3], e[4], e[5])
			local k, u = e[6], e[7]
			local rnd = Random.new(91)
			for j = 1, 16 do
				local a0, r0, d0 = rnd:NextNumber(0, 6.28), rnd:NextNumber(0.8, 2.2), rnd:NextNumber(0.3, 1.8)
				local spread = d0 * (0.3 + 0.9 * k + 0.6 * u)
				local q = c0 + Vector3.new(math.cos(a0) * spread, -0.7 + 0.6 * u + rnd:NextNumber(0, 0.7), -math.sin(a0) * spread)
				local rr = r0 * (0.5 + 0.7 * k + 0.5 * u)
				local p = fxPart(sc, "dustc" .. idx, j, function()
					return part(sc.folder, Vector3.one, ORIGIN, if j % 2 == 0 then Color3.new(0.84, 0.72, 0.52) else Color3.new(0.95, 0.84, 0.62), Enum.Material.Sand, Enum.PartType.Ball)
				end)
				p.Size = Vector3.one * rr
				p.CFrame = CFrame.new(q.X, math.max(q.Y, ORIGIN.Y + rr * 0.25), q.Z)
				p.Transparency = math.min(0.97, 0.3 + 0.67 * u)
				p.LocalTransparencyModifier = 0
			end
		elseif kind == "btrail" then
			-- (High Noon, the owner: "bullet trail doesn't come out of gun for the impact frame") from the real muzzle
			local kit = sc.rev and sc.rev.k
			if kit and kit.gcf then
				local a0 = ((kit.gcf :: CFrame) * CFrame.new(kit.muzzle)).Position
				local p = fxPart(sc, "btrail" .. idx, 1, function() return part(sc.folder, Vector3.one, ORIGIN, Color3.new(1, 0.95, 0.85), Enum.Material.Neon) end)
				between(p, a0, P3(sc, s, f, an, e[3], e[4], e[5]), 0.09, 0.09, Vector3.yAxis)
				p.LocalTransparencyModifier = 0
				table.insert(sc.accent, p)
			end
		end
	end
	-- (pools not drawn this frame hide; the petals of the air and the dust keep their own)
	for key, pool in sc.pools do
		if key ~= "dust" and key ~= "air" then
			local n = sc.used[key] or 0
			for j = n + 1, #pool do pool[j].LocalTransparencyModifier = 1 end
		end
	end
end

-- the scene's sounds on their frames (the short payoff only hears its own). a cue that is all digits is a Roblox library
-- sound by id (EFFECTS); any other is the game's library by name (Sfx). a scene's audio beds (High Noon: the music under
-- MUSIC, the wind under EFFECTS) start with it, fade out on their `out` frame and come back on `back`
local SoundService = game:GetService("SoundService")
local TweenService = game:GetService("TweenService")
local function groupOf(name: string): SoundGroup?
	local m = SoundService:FindFirstChild("JankMaster")
	local g = m and m:FindFirstChild(name)
	return if g and g:IsA("SoundGroup") then g else nil
end
local function ownSound(sc: any, id: string, vol: number, group: string, looped: boolean?): Sound
	local snd = Instance.new("Sound")
	snd.Name = "FinisherSound"
	snd.SoundId = "rbxassetid://" .. id
	snd.Volume = vol
	snd.Looped = looped == true
	snd.SoundGroup = groupOf(group)
	snd.Parent = SoundService
	table.insert(sc.sounds, snd)
	if not looped then snd.Ended:Once(function() snd:Destroy() end) end
	snd:Play()
	return snd
end
local function fadeTo(snd: Sound?, to: number, t: number)
	if snd and snd.Parent then TweenService:Create(snd, TweenInfo.new(t, Enum.EasingStyle.Sine), { Volume = to }):Play() end
end
local function sounds(sc: any, i: number)
	sc.sounds = sc.sounds or {}
	for _, q in sc.ex.cues or {} do
		if not sc.cued[q] and i >= q[1] and q[1] >= sc.i0 then
			sc.cued[q] = true
			if string.match(q[2], "^%d+$") then pcall(ownSound, sc, q[2], q[3], "Effects") else pcall(Sfx.play, q[2], nil, q[3]) end
		end
	end
	local au = sc.ex.audio
	if not au then return end
	sc.beds = sc.beds or {}
	for key, b in au do
		local st = sc.beds[key]
		if not st then
			st = {}
			sc.beds[key] = st
			-- (no beds under a payoff that starts after they'd have gone quiet: the short one starts at the draw)
			if not b.out or sc.i0 < b.out then
				local ok, snd = pcall(ownSound, sc, b.id, b.vol, if key == "music" then "Music" else "Effects", b.looped)
				if ok then st.snd = snd end
			end
		end
		if st.snd then
			if not st.out and b.out and i >= b.out then st.out = true; fadeTo(st.snd, 0, b.outT) end
			if not st.back and b.back and i >= b.back then st.back = true; fadeTo(st.snd, b.backVol, b.backT) end
		end
	end
end

-- ------------------------------------------------------------------ the set, built now or ahead
-- (Studio tests: the workspace attribute FinisherTown = "A" | "B" picks a town over the scene's own)
local function townKeyOf(ex: any): string?
	local tk = workspace:GetAttribute("FinisherTown")
	if type(tk) == "string" and game:GetService("RunService"):IsStudio() then return tk end
	return ex.town
end

-- the plan's boxes (less what a kit town stands in for) and the kit town with its onlookers, under `stage`. Built
-- ahead, `step` waits a frame every SET_CHUNK pieces and says whether to go on; false from it stops the build (nil back)
local SET_CHUNK = 120
local function buildSet(sid: string, d: any, ex: any, townKey: string?, stage: Instance, step: (() -> boolean)?): ({ any }?, any)
	local setParts = {}
	local town = if Town and townKey then Town.pick(sid, townKey) else nil
	for n, q in d.stage do
		if step and n % SET_CHUNK == 0 and not step() then return nil, nil end
		-- (the pieces a kit town stands in for, and the ruts, aren't built at all: a false keeps the hide lists' count)
		if (town and Town.REPLACED[q[10]]) or (ex.noRuts and q[10] == "rut") or (q[10] == "sky" and ex.look and ex.look.plainSky) then
			table.insert(setParts, false)
			continue
		end
		local okm, mat = pcall(function() return (Enum.Material :: any)[q[9]] end)
		local shape = if q[1] == "Ball" then Enum.PartType.Ball elseif q[1] == "Cylinder" then Enum.PartType.Cylinder else nil
		-- (the painted sky ring is plain paint: Neon blows out white in the game's light)
		local p = part(stage, Vector3.new(q[2], q[3], q[4]), ORIGIN * cfOf(q[5]), Color3.new(q[6], q[7], q[8]), if q[10] == "sky" then Enum.Material.SmoothPlastic elseif okm then mat else nil, shape)
		p.CastShadow = q[10] ~= "floor" and q[10] ~= "sky" -- (the painted sky ring and its lid never shade the court)
		p.Name = q[10]
		-- (a scene under the engine's own sky leaves the painted ring out: built but unseen, so the plan's hide lists
		-- still count the set's parts the same way)
		if q[10] == "sky" and ex.look and ex.look.plainSky then p.Transparency = 1 end
		if q[10] == "print" and ex.softPrints then
			-- (a faint print: smaller, nearly the street's own colour, half see-through)
			p.Size = Vector3.new(p.Size.X * 0.75, p.Size.Y, p.Size.Z * 0.75)
			p.Color = p.Color:Lerp(Color3.fromRGB(196, 158, 112), 0.6)
			p.Transparency = 0.55
			p.CastShadow = false
		end
		table.insert(setParts, p)
		if ex.lamps and q[10] == "lamp" then
			local pl = Instance.new("PointLight")
			pl.Range = 10; pl.Brightness = 1.6; pl.Shadows = true; pl.Color = Color3.fromRGB(255, 190, 120)
			pl.Parent = p
		end
	end
	local st: any = nil
	if town then
		local ok, r = pcall(Town.build, sid, townKey :: string, stage, ORIGIN, step)
		if ok then st = r else warn("[jankfire] finisher town: " .. tostring(r)) end
		if step and not step() then return nil, nil end
	end
	return setParts, st
end

-- (the opening hitch - main, 20 Nov: the cutscene's first frame took 97-99 ms in both towns, its set, its kit town and
-- the onlookers all built in that one frame. The server now says when a scene may come - the gap after a round that
-- leaves a team one win from the match, a classic mode's start - and the set is built then, a chunk a frame, parked
-- where it plays: ORIGIN, far off every map, where nothing else ever is. The clips and the sounds are fetched with it.
-- Scene.start takes the parked set as it stands; Scene.unwarm drops it (home, or a new warm for the other town))
local ContentProvider = game:GetService("ContentProvider")
local warm: { [string]: any } = {}
local playing: string? = nil -- (the scene on screen now: no second set of it is built meanwhile)

function Scene.unwarm(sid: string?)
	for id, w in warm do
		if sid == nil or id == sid then
			w.dead = true
			w.folder:Destroy()
			warm[id] = nil
		end
	end
end

-- Scene.warm(sceneId) -> boolean   builds that scene's set ahead (true: built, on its way, or already there)
function Scene.warm(sid: string): boolean
	local d = dataOf(sid)
	if not d or playing == sid then return false end
	local ex = EXTRA[sid] or {}
	local key = townKeyOf(ex)
	local w = warm[sid]
	if w and not w.dead and w.key == key then return true end
	if w then Scene.unwarm(sid) end
	local folder = Instance.new("Folder")
	folder.Name = "JankFinisherStage"
	folder.Parent = workspace
	local stage = Instance.new("Folder")
	stage.Name = "Set"
	stage.Parent = folder
	local nw: any = { key = key, folder = folder, stage = stage, ready = false, dead = false }
	warm[sid] = nw
	local t0 = os.clock()
	task.spawn(function()
		local frames = 0
		local function step(): boolean
			task.wait()
			frames += 1
			return not nw.dead and folder.Parent ~= nil
		end
		local parts, town = buildSet(sid, d, ex, key, stage, step)
		if not parts or nw.dead then return end
		if town and Town.warm then pcall(Town.warm, town) end
		nw.setParts, nw.town, nw.ready = parts, town, true
		if game:GetService("RunService"):IsStudio() then
			workspace:SetAttribute("FinisherWarm", ("%s %s ready: %d frames, %.1f s"):format(sid, tostring(key), frames, os.clock() - t0))
		end
		-- (the clips and the sounds fetched now, not on their frames)
		local list = {}
		for _, clip in d.clips or {} do
			local id = Finishers.SCENE_ANIMS[clip]
			if id then
				local a = Instance.new("Animation")
				a.AnimationId = "rbxassetid://" .. id
				table.insert(list, a)
			end
		end
		local function snd(id: string)
			local x = Instance.new("Sound")
			x.SoundId = "rbxassetid://" .. id
			table.insert(list, x)
		end
		for _, q in ex.cues or {} do if string.match(q[2], "^%d+$") then snd(q[2]) end end
		for _, b in ex.audio or {} do snd(b.id) end
		pcall(function() ContentProvider:PreloadAsync(list) end)
	end)
	return true
end

-- ------------------------------------------------------------------ the scene
function Scene.start(s: any, kind: string): any
	local d = dataOf(s.row.scene)
	local ex = EXTRA[s.row.scene] or {}
	local sc: any = { d = d, ex = ex, kind = kind, i0 = 1, i1 = #d.f, speed = 1, tracks = {}, cur = {}, hip = {}, pools = {}, cued = {}, orig = {},
		shotOf = {}, shotStart = {}, lastShot = d.shots[#d.shots][1], v2 = d.sizes ~= nil, lowWas = {}, gOff = {}, used = {}, accent = {} }
	if kind == "short" and ex.short then
		local from = ex.short.from
		if ex.short.shot then
			local k0 = 0
			for _, sh in d.shots do
				if sh[1] == ex.short.shot then from = k0 + 1; break end
				k0 += sh[2]
			end
		end
		sc.i0, sc.speed = from or 1, ex.short.speed or 1
	end
	sc.total = (sc.i1 - sc.i0 + 1) / d.fps / sc.speed
	local k = 0
	for _, sh in d.shots do
		for j = 1, sh[2] do sc.shotOf[k + j] = sh[1]; sc.shotStart[k + j] = k + 1 end
		k += sh[2]
	end
	-- (a plan whose video held some shots longer - High Noon's suspense: each frame's start, in s from i0)
	if ex.stretch then
		sc.cum = {}
		local t = 0
		for i = sc.i0, sc.i1 do
			sc.cum[i] = t
			t += (ex.stretch[sc.shotOf[i]] or 1) / d.fps / sc.speed
		end
		sc.cum[sc.i1 + 1] = t
		sc.total = t
	end
	-- the set: the one built ahead when there is one (Scene.warm), else built now
	local c0 = os.clock()
	local townKey = townKeyOf(ex)
	local w = warm[s.row.scene]
	warm[s.row.scene] = nil
	if w and w.ready and not w.dead and w.key == townKey and w.folder.Parent then
		sc.folder, sc.stage, sc.setParts, sc.town, sc.warm = w.folder, w.stage, w.setParts, w.town, true
	else
		-- (one half built, or for the other town: dropped)
		if w then w.dead = true; w.folder:Destroy() end
		local folder = Instance.new("Folder")
		folder.Name = "JankFinisherStage"
		folder.Parent = workspace
		local stage = Instance.new("Folder")
		stage.Name = "Set"
		stage.Parent = folder
		sc.folder, sc.stage = folder, stage
		sc.setParts, sc.town = buildSet(s.row.scene, d, ex, townKey, stage, nil)
		sc.setParts = sc.setParts or {}
	end
	local c1 = os.clock()
	-- (the scene's own light, as its video: the place's Lighting saved first and put back by Scene.stop)
	if ex.look then
		local L = game:GetService("Lighting")
		local lk = ex.look
		local was: any = { props = {}, added = {} }
		for _, key in { "ClockTime", "GeographicLatitude", "Brightness", "OutdoorAmbient", "Ambient", "ColorShift_Top",
			"ColorShift_Bottom", "EnvironmentDiffuseScale", "EnvironmentSpecularScale", "ShadowSoftness", "ExposureCompensation",
			"GlobalShadows" } do
			was.props[key] = (L :: any)[key]
		end
		local atmo = L:FindFirstChildOfClass("Atmosphere")
		if atmo then was.atmo = { atmo, atmo.Density, atmo.Offset, atmo.Color, atmo.Decay, atmo.Glare, atmo.Haze } end
		sc.lookWas = was
		pcall(function()
			L.ClockTime = lk.clock; L.GeographicLatitude = lk.lat; L.Brightness = lk.bright
			L.OutdoorAmbient = lk.outdoor; L.Ambient = lk.ambient; L.ColorShift_Top = lk.shiftTop
			L.ColorShift_Bottom = Color3.new(0, 0, 0); L.EnvironmentDiffuseScale = 0.45; L.EnvironmentSpecularScale = 0.4
			L.ShadowSoftness = 0.15; L.ExposureCompensation = lk.exposure; L.GlobalShadows = true
			local a = atmo
			if not a then a = Instance.new("Atmosphere"); a.Name = "JankSceneAtmo"; a.Parent = L; table.insert(was.added, a) end
			a.Density = 0.3; a.Offset = 0.12; a.Color = Color3.fromRGB(222, 176, 134); a.Decay = Color3.fromRGB(176, 118, 92)
			a.Glare = 0.35; a.Haze = 1.4
			for key, v in lk.atmo or {} do (a :: any)[key] = v end
			-- (a gentle bloom on the sun and the highlights: the place's own Bloom, as the settings leave it on or off)
			local gb = ex.grade and ex.grade.bloom
			if gb then
				for _, e in L:GetChildren() do
					if e:IsA("BloomEffect") and string.sub(e.Name, 1, 4) ~= "Jank" then
						was.bloom = was.bloom or {}
						table.insert(was.bloom, { e, e.Intensity, e.Size, e.Threshold })
						e.Intensity, e.Size, e.Threshold = gb.Intensity, gb.Size, gb.Threshold
					end
				end
				-- (an arena whose look has no Bloom gets the scene's own for it; not "Jank"-named, so the settings' BLOOM
				-- switch holds it off as it does the looks' own - SettingsApply)
				if not was.bloom then
					local b = Instance.new("BloomEffect")
					b.Name = "SceneBloom"; b.Intensity = gb.Intensity; b.Size = gb.Size; b.Threshold = gb.Threshold
					b.Parent = L
					table.insert(was.added, b)
				end
			end
			-- (one grade in every shot, whatever arena the match was on - main, 20 Nov, the owner on live: "the color
			-- grading on the dust drover revolver ultimate changes throughout no?": the arena look's own colour
			-- correction stayed on under the scene's, and its sun rays came and went as the lens turned to the sun and
			-- away. Those are off for the scene and back on after)
			if ex.grade then
				was.post = {}
				for _, e in L:GetChildren() do
					if (e:IsA("ColorCorrectionEffect") or e:IsA("SunRaysEffect") or e:IsA("DepthOfFieldEffect") or e:IsA("BlurEffect"))
						and string.sub(e.Name, 1, 4) ~= "Jank" and e.Enabled then
						table.insert(was.post, e)
						e.Enabled = false
					end
				end
			end
			-- (the engine's own sky and sun: the place's Skies are parked under Lighting for the scene, put back after)
			if lk.plainSky then
				was.skies = {}
				local park = Instance.new("Folder")
				park.Name = "JankSceneSkyPark"; park.Parent = L
				for _, c in L:GetChildren() do
					if c:IsA("Sky") then table.insert(was.skies, { c, c.Parent }); c.Parent = park end
				end
				was.park = park
			end
			local cc = Instance.new("ColorCorrectionEffect")
			cc.Name = "JankSceneGrade"; cc.TintColor = Color3.fromRGB(255, 238, 220); cc.Contrast = 0.08; cc.Saturation = 0.04
			cc.Parent = L
			table.insert(was.added, cc)
		end)
	end
	local c2 = os.clock()
	-- the two of them
	takeBody(s.kg)
	takeBody(s.vg)
	for who, g in { k = s.kg, v = s.vg } do
		local hum = g.hum :: Humanoid
		sc.hip[who] = hum.HipHeight + (g.root :: BasePart).Size.Y / 2
	end
	if ex.kit == "revolver" then revolverKit(sc, s) else katanaKit(sc, s.msg.skin) end
	-- (Studio: where the start's time went, ms - Finisher.luau adds it to the FinisherProf readout)
	playing = s.row.scene
	sc.prof = ("set %.1f%s look %.1f bodies %.1f"):format(1000 * (c1 - c0), if sc.warm then " (built ahead)" else "", 1000 * (c2 - c1), 1000 * (os.clock() - c2))
	return sc
end

local function frameAt(sc: any, w: number): (number, number)
	if sc.cum then
		-- (stretched shots: the frame whose span holds w, and how far through it)
		local lo, hi = sc.i0, sc.i1
		while lo < hi do
			local mid = (lo + hi + 1) // 2
			if sc.cum[mid] <= w then lo = mid else hi = mid - 1 end
		end
		local span = sc.cum[lo + 1] - sc.cum[lo]
		return lo, if span > 0 then math.clamp((w - sc.cum[lo]) / span, 0, 1) else 0
	end
	local fi = sc.i0 + w * sc.d.fps * sc.speed
	local i = math.clamp(math.floor(fi), sc.i0, sc.i1)
	return i, math.clamp(fi - i, 0, 1)
end

-- (Catmull-Rom through the plan's frames: no step in speed at each plan frame. The owner, 20 Nov: "can teh cowboy thing
-- be a consistent framerate? ... that smae shot idk why but it feels like its smoother": straight lines between plan
-- frames read as judder wherever a move eases; the hand shot's lens drifts at one speed, so it looked smooth)
local function crv(p0: Vector3, p1: Vector3, p2: Vector3, p3: Vector3, t: number): Vector3
	local t2 = t * t
	return 0.5 * ((2 * p1) + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (3 * p1 - p0 - 3 * p2 + p3) * t2 * t)
end
local function crn(p0: number, p1: number, p2: number, p3: number, t: number): number
	local t2 = t * t
	return 0.5 * ((2 * p1) + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (3 * p1 - p0 - 3 * p2 + p3) * t2 * t)
end
-- the plan's effects between two of its frames: each one in both frames blended number by number (a tumbleweed rolls,
-- dust drifts), so they move on every render frame, not 16 times a second
local function fxBetween(fa: any, fb: any, a: number): any
	if not fa or not fb or a <= 0 then return fa end
	local out = table.create(#fa)
	for k, ea in fa do
		local eb = fb[k]
		if eb and eb[1] == ea[1] and eb[2] == ea[2] and #eb == #ea then
			local e = table.clone(ea)
			for n = 3, #ea do
				local x, y = ea[n], eb[n]
				if type(x) == "number" and type(y) == "number" and x ~= y then e[n] = x + (y - x) * a end
			end
			out[k] = e
		else
			out[k] = ea
		end
	end
	return out
end

function Scene.step(s: any, w: number): (string, number, boolean)
	local sc = s.scene
	local d = sc.d
	local i, a = frameAt(sc, w)
	local j = math.min(i + 1, sc.i1)
	local A, Bf = d.f[i], d.f[j]
	local same = j ~= i and sc.shotOf[i] == sc.shotOf[j]
	if not same then a = 0 end
	local shot = sc.shotOf[i]
	local s0 = sc.shotStart[i]
	local nIn = 0
	for _, sh in d.shots do if sh[1] == shot then nIn = sh[2] end end
	local li = i - s0 -- (the frame in its shot, from 0)
	local u = if nIn > 1 then math.clamp((li + a) / (nIn - 1), 0, 1) else 0
	local T = (i - 1 + a) / d.fps -- (the scene's own clock, s)
	-- the lens
	local cA = cfOf(A.c)
	local c = cA
	-- (the neighbours either side, when they're in the same shot)
	local Pf = if i - 1 >= sc.i0 and sc.shotOf[i - 1] == shot then d.f[i - 1] else nil
	local Nf = if j + 1 <= sc.i1 and sc.shotOf[j + 1] == shot then d.f[j + 1] else nil
	if same then
		local cB = cfOf(Bf.c)
		local cP = if Pf then cfOf(Pf.c) else cA
		local cN = if Nf then cfOf(Nf.c) else cB
		local pos = crv(cP.Position, cA.Position, cB.Position, cN.Position, a)
		local lk = crv(cP.LookVector, cA.LookVector, cB.LookVector, cN.LookVector, a)
		local upv = crv(cP.UpVector, cA.UpVector, cB.UpVector, cN.UpVector, a)
		c = if lk.Magnitude > 1e-4 and upv.Magnitude > 1e-4 then CFrame.lookAt(pos, pos + lk.Unit, upv.Unit) else cA:Lerp(cB, a)
	end
	local cam = workspace.CurrentCamera :: Camera
	cam.CameraType = Enum.CameraType.Scriptable
	cam.CFrame = ORIGIN * c
	cam.FieldOfView = if same then A.fov + (Bf.fov - A.fov) * a else A.fov
	-- (a shot the video cropped in on: the same push, by the lens)
	local zf = sc.ex.zoom and sc.ex.zoom[shot]
	if zf then cam.FieldOfView = math.deg(2 * math.atan(math.tan(math.rad(cam.FieldOfView) / 2) / zf)) end
	cam.Focus = cam.CFrame * CFrame.new(0, 0, -10)
	if sc.v2 then
		-- the bodies (two clips blended where the plan blends, grounded), the afterimages
		for who, g in { k = s.kg, v = s.vg } do
			local fa, fb = A[who], Bf[who]
			if fa then
				local e = table.clone(fa)
				local fp = Pf and Pf[who]
				local fn = Nf and Nf[who]
				if fp and fp[1] ~= fa[1] then fp = nil end
				if same and fb and fb[1] == fa[1] then
					local fn2 = if fn and fn[1] == fa[1] then fn else fb
					e[2] = crn((fp or fa)[2], fa[2], fb[2], fn2[2], a)
					e[3] = fa[3]
				end
				poseV2(sc, who, g, e, A["g" .. who])
				if same and fb and fb[1] == fa[1] then
					local ra, rb = ORIGIN * cfOf(fa[3]), ORIGIN * cfOf(fb[3])
					local rp = if fp then ORIGIN * cfOf(fp[3]) else ra
					local rn = if fn and fn[1] == fa[1] then ORIGIN * cfOf(fn[3]) else rb
					g.root.CFrame = ra:Lerp(rb, a).Rotation + crv(rp.Position, ra.Position, rb.Position, rn.Position, a)
						+ Vector3.new(0, sc.hip[who] - RIG_HIP + (sc.gOff[who] or 0), 0)
				end
				sc.lowWas[who] = lowestOf(g.model)
			end
		end
		-- the lens, riding on its body point (after the bodies are placed this frame, so it rides where they are now).
		-- the body's own small moves - a hip sway, the quick draw - shook it frame to frame where the plan's lens holds
		-- still (measured: 3 degrees back and forth through THE DRAW), so the lens takes the body's offset smoothed
		-- (0.25 s), set fresh on every cut
		if A.la then
			local planCam = cam.CFrame
			local off = planCam:Inverse() * rehang(sc, s, A, A.la, planCam, if same and Bf.la == A.la then Bf else nil, a)
			local now = os.clock()
			if sc.lensShot ~= shot or not sc.lensOff then
				sc.lensOff = off
			else
				sc.lensOff = (sc.lensOff :: CFrame):Lerp(off, 1 - math.exp(-math.max(now - (sc.lensT or now), 0) / 0.25))
			end
			sc.lensShot, sc.lensT = shot, now
			cam.CFrame = planCam * sc.lensOff
		end
		ghosts(sc, s, A.g)
		-- the scabbard's mouth sits where this body's own left hand holds it (measured once the grab's pose shows)
		if not sc.m0 and A.kat and A.kat[1] == 5 and A.sh and A.sh[1] == 1 and i >= sc.i0 + 2 then
			local lh = s.kg.model:FindFirstChild("LeftHand") :: BasePart?
			local g0 = gripR(s.kg.model)
			if lh and g0 then sc.m0 = math.max(0.2, (lh.Position - g0.Position).Magnitude - 0.44) end
		end
		if sc.rev then placeRevolvers(sc, s, A, T) else placeKitV2(sc, s, A) end
		local life = sc.ex.trail and sc.ex.trail[shot]
		if sc.trail then
			sc.trail.Enabled = life ~= nil
			if life then sc.trail.Lifetime = life end
		end
		-- (the faces the plan sets: a squint, wide eyes - on a head with FaceControls)
		for who, fv in A.fc or {} do
			local g = if who == "k" then s.kg else s.vg
			local hd = g.model:FindFirstChild("Head")
			local fcs = hd and hd:FindFirstChildOfClass("FaceControls")
			if fcs then for prop, val in fv do pcall(function() (fcs :: any)[prop] = val end) end end
		end
		dust(sc, s.kg, T, sc.ex.dust ~= nil and sc.ex.dust[shot] == true)
		table.clear(sc.accent)
		if same and A.fx and Bf.fx then
			local F2 = table.clone(A)
			F2.fx = fxBetween(A.fx, Bf.fx, a)
			drawFx(sc, s, F2, T)
		else
			drawFx(sc, s, A, T)
		end
		-- the cut one coming apart (the plan's scatter)
		local scat = A.v and A.v[4] or 0
		if scat > 0 then
			for _, pc in piecesFor(sc, s.vg) do
				local r = pc.rot * scat
				pc.copy.CFrame = CFrame.new(pc.dir * scat) * pc.src.CFrame * CFrame.Angles(math.rad(r.X), math.rad(r.Y), math.rad(r.Z))
				pc.copy.Transparency = math.clamp((scat - 0.25) / 0.25, 0, 1)
			end
		end
		local hit = A.hit ~= nil
		setHit(sc, s, hit, if hit then sc.accent else nil, A.hit == 2)
		-- (the plan clears the pillars standing in a wide lens's way - THE LENGTH's gag shot - so this frame hides the
		-- set's pieces it lists; the next frame without them shows them again)
		local hide = if hit then nil else A.hide
		if sc.hidWas ~= hide then
			for _, ix in sc.hidWas or {} do local p = sc.setParts[ix]; if p and not hit then p.LocalTransparencyModifier = 0 end end
			for _, ix in hide or {} do local p = sc.setParts[ix]; if p then p.LocalTransparencyModifier = 1 end end
			sc.hidWas = hide
		end
		if hit then
			-- (every hit frame: only the accents show - the blade's trail, the rings, the stroke - in the skin's colour)
			if sc.backdrop then sc.backdrop.CFrame = cam.CFrame * CFrame.new(0, 0, -180) end
			for _, pool in sc.pools do
				for _, p in pool do
					if table.find(sc.accent, p) then
						sc.orig[p] = sc.orig[p] or { p.Color, p.Material }
						p.Color = s.row.colour; p.Material = Enum.Material.Neon
						p.LocalTransparencyModifier = 0
					else
						p.LocalTransparencyModifier = 1
					end
				end
			end
		end
		sounds(sc, i)
		if sc.ex.grade and not sc.gradeAt and i >= sc.ex.grade.at then sc.gradeAt = s.w end
		if sc.town then pcall(Town.step, sc.town, s.w) end
		return shot, u, shot == sc.lastShot
	end
	-- the bodies
	for who, g in { k = s.kg, v = s.vg } do
		local fa, fb = A[who], Bf[who]
		if fa then
			local t = fa[2]
			local root = cfOf(fa[3])
			if same and fb and fb[1] == fa[1] then
				t += (fb[2] - fa[2]) * a
				root = root:Lerp(cfOf(fb[3]), a)
			end
			poseBody(sc, who, g, fa[1], t, root)
		end
	end
	placeKit(sc, A, s.kg)
	-- the blade's ink trail
	local life = sc.ex.trail and sc.ex.trail[shot]
	sc.trail.Enabled = life ~= nil
	if life then sc.trail.Lifetime = life end
	-- dust off the runner's feet
	dust(sc, s.kg, T, sc.ex.dust ~= nil and sc.ex.dust[shot] == true)
	-- petals on the air all through
	drift(sc, "air", B(-5, 9, 3), 10, 4, T, B(0.6, -0.3, -0.35), 401)
	local vg = s.vg
	local vHead = vg.model:FindFirstChild("Head") :: BasePart?
	local vUT = vg.model:FindFirstChild("UpperTorso") :: BasePart?
	if shot == "THE END" and vUT then
		local click = sc.ex.clickAt or 16
		if li >= click then
			if not sc.strokeAt then
				-- the cut shows across the victim's belly where the blade went through: ink with a pink edge
				local cc = vUT.Position + B(0, 0, -0.6)
				sc.strokeAt = cc
				local ink = stroke(sc, "stroke", cc + B(-2.2, -0.8, 0.55), cc + B(2.2, -0.8, -0.3), 0.25, 0.5, B(0, -1, 0), INK, 61)
				local edge = stroke(sc, "edge", cc + B(-1.9, -0.86, 0.4), cc + B(1.9, -0.86, -0.2), 0.22, 0.15, B(0, -1, 0), s.row.colour, 62)
				sc.strokeParts = table.move(edge, 1, #edge, #ink + 1, table.clone(ink))
			end
			accent = sc.strokeParts
			local fade = if li < click + 5 then 0 else math.min(0.9, (li - click - 5 + a) * 0.09)
			for _, p in sc.strokeParts do p.Transparency = fade end
			if li >= click + 2 then burst(sc, "splat", sc.strokeAt + B(0.4, -0.9, 0), 10, 2.0, (li - click - 2 + a) / 10, 71, true, 0.7) end
		end
		if li >= click + 10 then
			-- down on the ground, coming apart into petals
			if not sc.vc then sc.vc = vUT.Position end
			local uu = math.clamp((li - click - 10 + a) / math.max(1, nIn - click - 11), 0, 1)
			burst(sc, "burst", vUT.Position + B(0, 0, 0.3), 60, 2.6, uu, 421, false, 1.2)
			local scat = (A.v and A.v[4] or 0)
			if same and Bf.v then scat += ((Bf.v[4] or 0) - scat) * a end
			if scat > 0 then
				for _, pc in piecesFor(sc, vg) do
					local r = pc.rot * scat
					pc.copy.CFrame = CFrame.new(pc.dir * scat) * pc.src.CFrame * CFrame.Angles(math.rad(r.X), math.rad(r.Y), math.rad(r.Z))
					pc.copy.Transparency = math.clamp((uu - 0.6) / 0.4, 0, 1)
				end
			end
		end
	end
	-- the hit frames
	local hit = A.hit == true
	if hit and shot == "CUT FRAME" then accent = {} end
	setHit(sc, s, hit, accent)
	if hit and sc.backdrop then sc.backdrop.CFrame = cam.CFrame * CFrame.new(0, 0, -180) end
	-- the sounds, on their frames (the short payoff only hears its own)
	sounds(sc, i)
	if sc.ex.grade and not sc.gradeAt and i >= sc.ex.grade.at then sc.gradeAt = s.w end
	return shot, u, shot == sc.lastShot
end

function Scene.hitNow(s: any): boolean
	return s.scene ~= nil and s.scene.hitOn == true
end

function Scene.stop(s: any)
	local sc = s.scene
	if not sc then return end
	s.scene = nil
	playing = nil
	for _, set in sc.tracks do for _, tr in set do pcall(function() tr:Stop(0) end) end end
	for _, kit in sc.rev or {} do if kit.ik then kit.ik:Destroy() end end
	-- (its sounds go with it: a quick fade, so a skip doesn't click)
	for _, snd in sc.sounds or {} do
		if snd.Parent then fadeTo(snd, 0, 0.3); task.delay(0.35, function() snd:Destroy() end) end
	end
	-- (the place's own light back, as it was before the scene)
	local was = sc.lookWas
	if was then
		local L = game:GetService("Lighting")
		pcall(function()
			for key, v in was.props do (L :: any)[key] = v end
			if was.atmo then
				local a = was.atmo[1]
				a.Density, a.Offset, a.Color, a.Decay, a.Glare, a.Haze = was.atmo[2], was.atmo[3], was.atmo[4], was.atmo[5], was.atmo[6], was.atmo[7]
			end
		end)
		for _, sk in was.skies or {} do pcall(function() sk[1].Parent = sk[2] end) end
		for _, b in was.bloom or {} do pcall(function() b[1].Intensity, b[1].Size, b[1].Threshold = b[2], b[3], b[4] end) end
		for _, e in was.post or {} do pcall(function() if e.Parent then e.Enabled = true end end) end
		if was.park then was.park:Destroy() end
		for _, inst in was.added do inst:Destroy() end
	end
	if sc.folder then sc.folder:Destroy() end
	for _, g in { s.kg, s.vg } do
		if g and g.model then
			local h = g.model:FindFirstChild("JankSceneHit")
			if h then h:Destroy() end
		end
	end
end

return Scene
