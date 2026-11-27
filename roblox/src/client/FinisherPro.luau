--!strict
-- FINISHER PRO SCENES (26 Nov 2026; roblox/docs/FINISHERS.md): a finisher scene made by a professional animator, played
-- as he delivered it - his two R15 KeyframeSequences (uploaded under the owner's account) on the two real avatars, the
-- katana and its sheath on their own tracks, his per-frame camera - with our own on top: the time ramps (slow-motion on
-- the draw, the pass, the cut), the lens moves, the letterbox, the set, the effects. The original file stays in the
-- vault (Exports\Tidecrest cutscene (pro animator)); the numbers it carries are in FinisherProData_<scene id>
-- (tools/roblox/tide_pro_data.py), this plays them.
-- FinisherScene hands a scene here when FinisherProData_<id> exists (Pro.has): the same calls, can / warm / unwarm /
-- start / step / hitNow / grade / barsIn / stop.
-- How the animator's take is laid out (his README): everything is relative to the killer's root at frame 0, 3 studs
-- over the floor on his stock rig; the victim's root at (0, 0.22, -36) turned round; the travel is baked into the Root
-- joints, so both roots hold still; camera = origin * cam[f]; no blending across the cuts; the blade's length per frame.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local CollectionService = game:GetService("CollectionService")
local ContentProvider = game:GetService("ContentProvider")
local RunService = game:GetService("RunService")

local Pro = {}
-- (the ink and petals: client/FinisherProFx.luau; the sounds: the game's own recorded library)
local Fx: any = nil
do
	local m = script.Parent:FindFirstChild("FinisherProFx")
	if m then
		local ok, F = pcall(require, m)
		if ok then Fx = F else warn("[jankfire] finisher pro fx: " .. tostring(F)) end
	end
end
local Sfx: any = nil
do
	local m = script.Parent:FindFirstChild("Sfx")
	if m then
		local ok, S = pcall(require, m)
		if ok then Sfx = S end
	end
end

-- the set's spot (FinisherScene's: far off every map, client-only parts): the floor under the killer's start
local ORIGIN = CFrame.new(0, 600, -24000)
local STOCK_HIP = 3.0 -- (the animator's rig: its root 3 over the floor)
local GZ = -0.62 -- (the katana package's guard face along the Katana part's -z; the blade runs on from it)
local BLADE = { kat_blade_blade = true, kat_blade_gold = true, kat_blade_paleedge = true, kat_blade_steel = true,
	kat_blade_edge = true, kat_blade_spine = true }
-- (the package rig's joints for the two props, as he keyed them: off the right hand's middle, off the hips' middle)
local KAT_C0 = CFrame.new(0, -0.12, 0)
local SHEATH_C0 = CFrame.new(-1.12, 0.1, -0.75, 0.99903, 0.021968, 0.038158, 0, -0.86664, 0.498934, 0.04403, -0.49845, -0.8658)
local STOCK_LT = Vector3.new(2, 0.4, 1) -- (the stock LowerTorso the sheath's joint was set on)

-- our own on top of each take: its clips (uploads of his two KeyframeSequences), the shots' names, the set and the
-- props kit (ReplicatedStorage.JankfireFinisherSets), the time ramps, the lens moves, the look
local TUNE: { [string]: any } = {
	inkfall = {
		anims = { k = "79972501972288", v = "130332889571388" },
		-- (27 Nov: k is his take with the run replaced by a coil and a dash, then smoothed - tools/roblox/tide_run_splice.py;
		-- the first splice was 107553046720755; his own
		-- killer, untouched, was 131612410895094)
		set = "TideWaterfall", kit = "TidecrestKit",
		short = 207, -- (a round win's short version: from THE CUT LANDS)
		vZ = -36, -- (where his README stands the victim's root)
		barsIn = 0.4,
		-- the sounds on his frames (the game's recorded library, Sfx names; no voices): the thumb's pop, the draw, the tip
		-- coming free, the whirl, the tip's stop at his nose, the rush of the charge, the whoosh into the cut, the hit, the
		-- click home and the bowl ringing over it, the cut landing, the body on the ground
		cues = { { 7, "loot_pop", 0.3 }, { 17, "swing", 0.55 }, { 55, "loot_pop", 0.6 }, { 57, "swing", 1 },
			{ 57, "skin_katana_sakura_swing", 0.7 }, { 86, "whoops", 0.5 }, { 119, "skin_katana_sakura_hit", 0.6 }, { 120, "zone_playground", 0.8 }, { 120, "swing", 0.9 },
			{ 130, "swing", 1 },
			{ 131, "skin_katana_sakura_swing", 0.85 }, { 139, "round_end", 0.9 }, { 204, "loot_pop", 0.9 }, { 205, "zone_vip", 0.8 },
			{ 207, "skin_katana_sakura_hit", 0.85 }, { 219, "death", 0.55 } },
		-- (the falls under it all: Pro Sound Effects' distant waterfall, a steady stream, from Roblox's licensed library;
		-- under the EFFECTS slider)
		bed = { id = "9120552671", vol = 0.42 },
		-- (a cool light on each fighter from the moon's side: dark avatars against the dark cliffs read by their edges -
		-- the set's judge, round 1: "the charcoal attacker merges into the cliffs because there is no rim light")
		rim = { dir = Vector3.new(-0.068, 0.208, 0.976), dist = 4.5, color = Color3.fromRGB(176, 196, 255), bright = 0.85, range = 9 },
		-- (per-shot exposure trims: the extreme close-ups fill the frame with a face or an outfit - a white one blew out
		-- in v1401's grip and face shots)
		expTrim = { ["THE GRIP"] = -0.55, ["THE TIP"] = -0.3, STILLNESS = -0.35, ["THE DRAW"] = -0.2, ["THE SHEATHE"] = -0.2,
			["THE COIL"] = -0.2 },
		-- the night (the set's SceneLook adds its Sky, Atmosphere, Bloom and grade): a cool moonlit key, blue fill, the
		-- moon's own light low behind the falls
		-- (v1393: exposure 1.3 blew white outfits and pale masks out in every close-up; 0.55 with less fill still glowed)
		-- (round 2, the judge: "lift the world off black" - more fill; the white outfits are held by the per-shot trims)
		look = { lighting = { ClockTime = 0.3, GeographicLatitude = 23, Brightness = 2.0, Ambient = Color3.fromRGB(46, 52, 80),
			OutdoorAmbient = Color3.fromRGB(86, 98, 140), ColorShift_Top = Color3.fromRGB(150, 170, 232), ColorShift_Bottom = Color3.fromRGB(24, 28, 46),
			EnvironmentDiffuseScale = 0.45, EnvironmentSpecularScale = 0.7, ShadowSoftness = 0.3, ExposureCompensation = 0.15, GlobalShadows = true } },
	},
}

local cache: { [string]: any } = {}
local function dataOf(sid: string?): any
	if type(sid) ~= "string" then return nil end
	local c = cache[sid]
	if c ~= nil then return c or nil end
	local d: any = false
	local m = script.Parent and script.Parent:FindFirstChild("FinisherProData_" .. sid)
	if m and m:IsA("ModuleScript") and TUNE[sid] then
		local ok, t = pcall(require, m)
		if ok and type(t) == "table" and type((t :: any)[sid]) == "table" then
			d = (t :: any)[sid]
			for k, v in TUNE[sid] do d[k] = v end
		end
	end
	cache[sid] = d
	return d or nil
end

function Pro.has(sid: string?): boolean
	return dataOf(sid) ~= nil
end

function Pro.can(sid: string, kind: string, kg: any, vg: any): boolean
	if not dataOf(sid) then return false end
	if kind ~= "full" and kind ~= "short" then return false end
	for _, g in { kg, vg } do
		if not g or not g.model or not g.model:FindFirstChild("LowerTorso") or not g.model:FindFirstChild("RightHand") or not g.hum then return false end
		if not (g.hum :: Humanoid):FindFirstChildOfClass("Animator") then return false end
	end
	return true
end

-- ------------------------------------------------------------------ the time ramps
-- d.ramp = { { frame, speed }, ... }: the take's speed (1 = as delivered) at those frames, eased between; a shot can
-- crawl through its key moment and catch up after. Built once per start into each frame's start time (s)
local function rampAt(d: any, f: number): number
	local r = d.ramp
	if not r or #r == 0 then return 1 end
	if f <= r[1][1] then return r[1][2] end
	for i = 1, #r - 1 do
		local a, b = r[i], r[i + 1]
		if f < b[1] then
			-- (a cut between them is a hard change: the next speed from the cut on)
			if b[3] == "cut" then return a[2] end
			local u = (f - a[1]) / math.max(1e-3, b[1] - a[1])
			u = u * u * (3 - 2 * u)
			return a[2] + (b[2] - a[2]) * u
		end
	end
	return r[#r][2]
end
local function buildClock(sc: any)
	local d = sc.d
	local cum = {}
	local t = 0
	for f = sc.f0, d.frames - 1 do
		cum[f] = t
		-- (each frame's span: a frame at speed k lasts 1 / (24 k); sampled at its middle)
		t += (1 / d.fps) / math.max(0.05, rampAt(d, f + 0.5) * sc.speed)
	end
	cum[d.frames] = t
	sc.cum = cum
	sc.total = t
end
-- (real seconds into the scene -> the take's frame and how far through it)
local function frameAt(sc: any, w: number): (number, number)
	local lo, hi = sc.f0, sc.d.frames - 1
	if w <= 0 then return lo, 0 end
	while lo < hi do
		local mid = (lo + hi + 1) // 2
		if sc.cum[mid] <= w then lo = mid else hi = mid - 1 end
	end
	local span = sc.cum[lo + 1] - sc.cum[lo]
	return lo, if span > 0 then math.clamp((w - sc.cum[lo]) / span, 0, 1) else 0
end

-- ------------------------------------------------------------------ the set, built ahead (FinisherScene's warm-up)
local warm: { [string]: any } = {}
local playing: string? = nil

local function setTemplate(d: any): Instance?
	local sets = ReplicatedStorage:FindFirstChild("JankfireFinisherSets")
	return sets and d.set and sets:FindFirstChild(d.set) or nil
end

-- the set's model, pivoted on the floor under the killer's start; `step` waits a frame between chunks
local SET_CHUNK = 150
local function buildSet(d: any, folder: Instance, step: (() -> boolean)?): Instance?
	local tpl = setTemplate(d)
	if not tpl then return nil end
	local m = tpl:Clone()
	if m:IsA("Model") then m:PivotTo(ORIGIN) end
	-- (parented a chunk at a time: one big parent write is one long frame)
	local kids = m:GetChildren()
	local holder = Instance.new("Model")
	holder.Name = "Set"
	holder.Parent = folder
	for i, c in kids do
		c.Parent = holder
		if step and i % SET_CHUNK == 0 and not step() then return nil end
	end
	m:Destroy()
	return holder
end

function Pro.unwarm(sid: string?)
	for id, w in warm do
		if sid == nil or id == sid then
			w.dead = true
			w.folder:Destroy()
			warm[id] = nil
		end
	end
end

function Pro.warm(sid: string): boolean
	local d = dataOf(sid)
	if not d or playing == sid then return false end
	local w = warm[sid]
	if w and not w.dead then return true end
	local folder = Instance.new("Folder")
	folder.Name = "JankFinisherStage"
	folder.Parent = workspace
	local nw: any = { folder = folder, ready = false, dead = false }
	warm[sid] = nw
	local t0 = os.clock()
	task.spawn(function()
		local frames = 0
		local function step(): boolean
			task.wait()
			frames += 1
			return not nw.dead and folder.Parent ~= nil
		end
		local set = buildSet(d, folder, step)
		if nw.dead then return end
		nw.set, nw.ready = set, true
		if RunService:IsStudio() then
			workspace:SetAttribute("FinisherWarm", ("%s pro ready: %d frames, %.1f s"):format(sid, frames, os.clock() - t0))
		end
		local list = {}
		for _, id in d.anims or {} do
			local a = Instance.new("Animation")
			a.AnimationId = "rbxassetid://" .. id
			table.insert(list, a)
		end
		pcall(function() ContentProvider:PreloadAsync(list) end)
	end)
	return true
end

-- ------------------------------------------------------------------ the bodies and the props
local function takeBody(g: any)
	g.model:SetAttribute("TPWeapon", nil)
	if g.run then pcall(function() g.run:Stop(0) end) end
	if g.idle then pcall(function() g.idle:Stop(0) end) end
	task.delay(0.05, function() if g.model.Parent then CollectionService:RemoveTag(g.model, "TPRig") end end)
	local an = (g.hum :: Humanoid):FindFirstChildOfClass("Animator") :: Animator
	for _, tr in an:GetPlayingAnimationTracks() do tr:Stop(0) end
	g.root.Anchored = true
	for _, d in g.model:GetDescendants() do
		if d:IsA("BasePart") and d.Name ~= "HumanoidRootPart" and d.Transparency < 0.9 then d.CastShadow = true end
	end
end

-- an invisible part the take's own prop track moves (a Motor6D the Animator finds by its parts' names); the props we
-- show follow it, so any body and any skin can wear them
local function proxy(sc: any, g: any, name: string, part0: BasePart, c0: CFrame): BasePart
	local old = g.model:FindFirstChild("JankPro" .. name)
	if old then old:Destroy() end
	local p = Instance.new("Part")
	p.Name = name
	p.Size = Vector3.new(0.1, 0.1, 0.1)
	p.Transparency = 1
	p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Massless = true; p.CastShadow = false
	p.CFrame = part0.CFrame * c0
	local holder = Instance.new("Model")
	holder.Name = "JankPro" .. name
	p.Parent = holder
	local m = Instance.new("Motor6D")
	m.Name = name
	m.Part0 = part0
	m.Part1 = p
	m.C0 = c0
	m.Parent = part0
	holder.Parent = g.model
	table.insert(sc.made, holder)
	table.insert(sc.made, m)
	return p
end

-- the shown katana and sheath: the kit's pieces, anchored, placed each frame off the proxies (the blade stretched)
local function propKit(sc: any, d: any)
	local sets = ReplicatedStorage:FindFirstChild("JankfireFinisherSets")
	local kit = sets and d.kit and sets:FindFirstChild(d.kit)
	sc.katParts, sc.sheathParts = {}, {}
	if not kit then return end
	for _, pair in { { "KatanaModel", "Katana", sc.katParts }, { "SheathModel", "Sheath", sc.sheathParts } } do
		local src = kit:FindFirstChild(pair[1])
		local root = src and src:FindFirstChild(pair[2])
		if src and root and root:IsA("BasePart") then
			local m = src:Clone()
			local r = m:FindFirstChild(pair[2]) :: BasePart
			for _, p in m:GetDescendants() do
				if p:IsA("BasePart") then
					p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
					p.CastShadow = p ~= r
					if p == r then p.Transparency = 1 end
					table.insert(pair[3], { p = p, rel = r.CFrame:ToObjectSpace(p.CFrame), size = p.Size, blade = BLADE[p.Name] == true })
				elseif p:IsA("JointInstance") or p:IsA("Constraint") or p:IsA("BaseScript") then
					p:Destroy()
				end
			end
			m.Parent = sc.folder
			if pair[2] == "Katana" then sc.katModel = m else sc.sheathModel = m end
			local mouth = r:FindFirstChild("SheathMouth")
			if mouth and mouth:IsA("Attachment") then sc.mouthA = mouth.CFrame end
		end
	end
end

-- (a piece's place this frame: the blade's pieces grow along -z from the guard face, the rest ride the root)
local function placeProps(sc: any, katCF: CFrame, sheathCF: CFrame, L: number)
	local parts, cfs = sc.moveP, sc.moveC
	table.clear(parts); table.clear(cfs)
	for _, e in sc.katParts do
		if e.blade then
			local p = e.rel.Position
			table.insert(cfs, katCF * CFrame.new(p.X, p.Y, GZ + (p.Z - GZ) * L) * e.rel.Rotation)
			if e.L ~= L then
				e.L = L
				-- (the mesh's own axis along the katana's z; the long blade broadens too - at 10x its own breadth is a
				-- hairline in the wide shots, the review found: up to 2.6x as broad at full length)
				local lz = e.rel:VectorToObjectSpace(Vector3.zAxis)
				local s = e.size
				local b = 1 + 1.6 * math.clamp((L - 1.5) / 8.5, 0, 1)
				e.p.Size = if math.abs(lz.X) > 0.9 then Vector3.new(s.X * L, s.Y * b, s.Z * b) elseif math.abs(lz.Y) > 0.9 then Vector3.new(s.X * b, s.Y * L, s.Z * b) else Vector3.new(s.X * b, s.Y * b, s.Z * L)
			end
		else
			table.insert(cfs, katCF * e.rel)
		end
		table.insert(parts, e.p)
	end
	for _, e in sc.sheathParts do
		table.insert(parts, e.p)
		table.insert(cfs, sheathCF * e.rel)
	end
	workspace:BulkMoveTo(parts, cfs, Enum.BulkMoveMode.FireCFrameChanged)
end

-- ------------------------------------------------------------------ the look (the scene's own night; the place's put back)
local LOOK_KEYS = { "ClockTime", "GeographicLatitude", "Brightness", "OutdoorAmbient", "Ambient", "ColorShift_Top",
	"ColorShift_Bottom", "EnvironmentDiffuseScale", "EnvironmentSpecularScale", "ShadowSoftness", "ExposureCompensation", "GlobalShadows" }
local function applyLook(sc: any, lk: any)
	local L = game:GetService("Lighting")
	local was: any = { props = {}, added = {}, off = {} }
	for _, key in LOOK_KEYS do was.props[key] = (L :: any)[key] end
	sc.lookWas = was
	pcall(function()
		for key, v in lk.lighting or {} do (L :: any)[key] = v end
		-- (the arena's own post effects off for the scene - one grade in every shot - and its skies parked)
		for _, e in L:GetChildren() do
			if (e:IsA("ColorCorrectionEffect") or e:IsA("SunRaysEffect") or e:IsA("DepthOfFieldEffect") or e:IsA("BlurEffect")
				or e:IsA("BloomEffect") or e:IsA("Atmosphere") or e:IsA("Sky") or e:IsA("Clouds")) and string.sub(e.Name, 1, 4) ~= "Jank" then
				table.insert(was.off, { e, e.Parent })
			end
		end
		local park = Instance.new("Folder")
		park.Name = "JankSceneSkyPark"
		park.Parent = L
		was.park = park
		for _, x in was.off do x[1].Parent = park end
		-- the scene's own: its Sky, Atmosphere, Bloom, ColorCorrection, kept with its set's template (SceneLook folder)
		local tpl = setTemplate(sc.d)
		local own = tpl and tpl:FindFirstChild("SceneLook")
		if own then
			for _, c in own:GetChildren() do
				local k = c:Clone()
				k.Parent = L
				table.insert(was.added, k)
			end
		end
	end)
end
local function restoreLook(sc: any)
	local was = sc.lookWas
	if not was then return end
	local L = game:GetService("Lighting")
	pcall(function() for key, v in was.props do (L :: any)[key] = v end end)
	for _, inst in was.added do pcall(function() inst:Destroy() end) end
	for _, x in was.off do pcall(function() x[1].Parent = x[2] end) end
	if was.park then was.park:Destroy() end
	sc.lookWas = nil
end

-- ------------------------------------------------------------------ the scene
function Pro.start(s: any, kind: string, sid: string): any
	local d = dataOf(sid)
	local sc: any = { d = d, pro = true, kind = kind, speed = 1, made = {}, tracks = {}, moveP = {}, moveC = {}, hip = {},
		f0 = 0, shotNow = nil }
	if kind == "short" and d.short then sc.f0 = d.short end
	buildClock(sc)
	-- the set: built ahead when it could be
	local c0 = os.clock()
	local w = warm[sid]
	warm[sid] = nil
	if w and w.ready and not w.dead and w.folder.Parent then
		sc.folder, sc.set, sc.warm = w.folder, w.set, true
	else
		if w then w.dead = true; w.folder:Destroy() end
		local folder = Instance.new("Folder")
		folder.Name = "JankFinisherStage"
		folder.Parent = workspace
		sc.folder = folder
		sc.set = buildSet(d, folder, nil)
	end
	local c1 = os.clock()
	applyLook(sc, d.look or {})
	-- the two of them, the take on each, the props' tracks
	takeBody(s.kg)
	takeBody(s.vg)
	-- (each root's height over its own feet, as Finisher.luau read it off the copy before anything moved it; the
	-- Humanoid's HipHeight is only a fallback - a scaled avatar's can be far off)
	for who, g in { k = s.kg, v = s.vg } do
		local hum = g.hum :: Humanoid
		sc.hip[who] = hum.HipHeight + (g.root :: BasePart).Size.Y / 2
	end
	if type(s.kFloor) == "number" and typeof(s.K0) == "Vector3" then sc.hip.k = math.clamp(s.K0.Y - s.kFloor, 1.5, 5) end
	if type(s.hipV) == "number" then sc.hip.v = math.clamp(s.hipV, 1.5, 5) end
	local kgm = s.kg.model
	local hand = kgm:FindFirstChild("RightHand") :: BasePart
	local lt = kgm:FindFirstChild("LowerTorso") :: BasePart
	local ls = lt.Size
	local sh0 = SHEATH_C0.Position
	local shC0 = CFrame.new(sh0.X * ls.X / STOCK_LT.X, sh0.Y * ls.Y / STOCK_LT.Y, sh0.Z * ls.Z / STOCK_LT.Z) * SHEATH_C0.Rotation
	sc.pk = proxy(sc, s.kg, "Katana", hand, KAT_C0)
	sc.ps = proxy(sc, s.kg, "Sheath", lt, shC0)
	propKit(sc, d)
	for who, g in { k = s.kg, v = s.vg } do
		local an = (g.hum :: Humanoid):FindFirstChildOfClass("Animator") :: Animator
		local a = Instance.new("Animation")
		a.AnimationId = "rbxassetid://" .. d.anims[who]
		local ok, tr = pcall(function() return an:LoadAnimation(a) end)
		if ok and tr then
			tr.Looped = false
			tr.Priority = Enum.AnimationPriority.Action4
			tr:Play(0, 1, 0)
			sc.tracks[who] = tr
		end
	end
	-- (the roots hold still where the take starts them, each at its own body's hip height; Pro.step grounds each on its
	-- own feet from the first frames on - his rig stood 0.22 off our floor)
	sc.rootCF = { k = ORIGIN, v = ORIGIN * CFrame.new(0, 0, d.vZ or -36) * CFrame.Angles(0, math.pi, 0) }
	sc.gnd = { k = { off = 0, n = 0, sum = 0 }, v = { off = 0, n = 0, sum = 0 } }
	s.kg.root.CFrame = sc.rootCF.k + Vector3.new(0, sc.hip.k, 0)
	s.vg.root.CFrame = sc.rootCF.v + Vector3.new(0, sc.hip.v, 0)
	sc.take = ORIGIN * CFrame.new(0, d.floor or STOCK_HIP, 0) -- (the take's space: its origin, the killer's root at frame 0)
	sc.floorY = ORIGIN.Y
	sc.cued = {}
	if d.rim then
		sc.rims = {}
		for _, g in { s.kg, s.vg } do
			local ut = g.model:FindFirstChild("UpperTorso")
			if ut and ut:IsA("BasePart") then
				local a = Instance.new("Attachment")
				a.Name = "JankProRim"
				a.Parent = ut
				local l = Instance.new("PointLight")
				l.Color = d.rim.color; l.Brightness = d.rim.bright; l.Range = d.rim.range; l.Shadows = false
				l.Parent = a
				table.insert(sc.made, a)
				table.insert(sc.rims, a)
			end
		end
	end
	if d.bed then
		local snd = Instance.new("Sound")
		snd.Name = "FinisherSound"
		snd.SoundId = "rbxassetid://" .. d.bed.id
		snd.Looped = true
		snd.Volume = 0
		local m = game:GetService("SoundService"):FindFirstChild("JankMaster")
		local grp = m and m:FindFirstChild("Effects")
		if grp and grp:IsA("SoundGroup") then snd.SoundGroup = grp end
		snd.Parent = game:GetService("SoundService")
		snd:Play()
		game:GetService("TweenService"):Create(snd, TweenInfo.new(0.6), { Volume = d.bed.vol }):Play()
		sc.bed = snd
	end
	playing = sid
	sc.prof = ("set %.1f%s, rest %.1f"):format(1000 * (c1 - c0), if sc.warm then " (built ahead)" else "", 1000 * (os.clock() - c1))
	return sc
end

-- (Catmull-Rom between the take's frames within one shot)
local function crv(p0: Vector3, p1: Vector3, p2: Vector3, p3: Vector3, t: number): Vector3
	local t2, t3 = t * t, t * t * t
	return 0.5 * ((2 * p1) + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (3 * p1 - p0 - 3 * p2 + p3) * t3)
end
local function camOf(c: { number }): CFrame
	return CFrame.new(c[1], c[2], c[3], c[4], c[5], c[6], c[7], c[8], c[9], c[10], c[11], c[12])
end

-- the lens at frame i + a (the animator's, eased through his frames, never across a cut), in the take's space
local function baseLens(sc: any, i: number, a: number): (CFrame, number)
	local d = sc.d
	local n = d.frames
	local shot = d.shot
	local function at(f: number): CFrame return camOf(d.cam[f + 1]) end
	local cA = at(i)
	local fovA = d.cam[i + 1][13]
	local j = math.min(i + 1, n - 1)
	if j == i or shot[j + 1] ~= shot[i + 1] or a <= 0 then return cA, fovA end
	local cB = at(j)
	local cP = if i - 1 >= 0 and shot[i] == shot[i + 1] then at(i - 1) else cA
	local cN = if j + 1 < n and shot[j + 2] == shot[i + 1] then at(j + 1) else cB
	local pos = crv(cP.Position, cA.Position, cB.Position, cN.Position, a)
	local lk = crv(cP.LookVector, cA.LookVector, cB.LookVector, cN.LookVector, a)
	local up = crv(cP.UpVector, cA.UpVector, cB.UpVector, cN.UpVector, a)
	local c = if lk.Magnitude > 1e-4 and up.Magnitude > 1e-4 then CFrame.lookAt(pos, pos + lk.Unit, up.Unit) else cA:Lerp(cB, a)
	return c, fovA + (d.cam[j + 1][13] - fovA) * a
end

-- ------------------------------------------------------------------ the bodies' points (the lens holds to them)
local PT = { kH = { "k", "Head" }, kUT = { "k", "UpperTorso" }, kLT = { "k", "LowerTorso" }, kRH = { "k", "RightHand" },
	vH = { "v", "Head" }, vUT = { "v", "UpperTorso" }, vLT = { "v", "LowerTorso" } }
local function realPt(sc: any, s: any, key: string): Vector3?
	if key == "mouth" then return sc.mouthW end
	local a = PT[key]
	if not a then return nil end
	local g = if a[1] == "k" then s.kg else s.vg
	local p = g.model:FindFirstChild(a[2])
	return if p and p:IsA("BasePart") then p.Position else nil
end
-- the stock rig's point at frame i + a (the scan, the take's space)
local function stockPt(d: any, key: string, i: number, a: number): Vector3?
	local arr = d.stock and d.stock[key]
	if not arr then return nil end
	local j = math.min(i + 1, d.frames - 1)
	local p0 = Vector3.new(arr[i * 3 + 1], arr[i * 3 + 2], arr[i * 3 + 3])
	local p1 = Vector3.new(arr[j * 3 + 1], arr[j * 3 + 2], arr[j * 3 + 3])
	return p0:Lerp(p1, a)
end

-- (a body's lowest point, world Y: its feet, or every body part once it lies on the floor)
local function lowest(g: any, all: boolean): number
	local y = math.huge
	for _, p in g.model:GetChildren() do
		if p:IsA("BasePart") and p.Name ~= "HumanoidRootPart" and p.Transparency < 1 and (all or p.Name == "LeftFoot" or p.Name == "RightFoot") then
			local cf, hs = p.CFrame, p.Size / 2
			local ext = math.abs(cf.RightVector.Y) * hs.X + math.abs(cf.UpVector.Y) * hs.Y + math.abs(cf.LookVector.Y) * hs.Z
			y = math.min(y, cf.Position.Y - ext)
		end
	end
	return y
end

-- each body on its own feet: the first frames measure how high the take stands this body (his rig's floor was 0.22
-- under ours), then a foot never goes through the floor (the dash's plant), and a body lying down lies on it
local FALL_FROM = 214 -- (the victim's fall: from here the whole body is grounded, up or down)
local function ground(sc: any, who: string, g: any, fi: number, dt: number)
	local gs = sc.gnd[who]
	-- (the root goes where the take stands it every frame, measured or not: Finisher.luau posed the ghosts at the
	-- preview's or the kill's own spot once after the start, and a frame skipped here left them there - the first
	-- in-game test, v1373: an empty set, the bodies back in the hub)
	local function place() g.root.CFrame = sc.rootCF[who] + Vector3.new(0, sc.hip[who] + gs.off, 0) end
	local tr = sc.tracks[who]
	if not tr or tr.Length <= 0 then place(); return end
	local all = who == "v" and fi >= FALL_FROM
	-- (measured only once the body stands at the scene: Finisher.luau posed it at its own spot after the start)
	local here = g.root.Position - sc.rootCF[who].Position
	if Vector2.new(here.X, here.Z).Magnitude > 2 then place(); return end
	local low = lowest(g, all) - ORIGIN.Y -- (the floor is ORIGIN's height)
	if low > 40 or low < -40 then place(); return end
	local natural = low - (gs.off - (gs.base or 0)) -- (where it would stand on the base offset)
	if not gs.base then
		-- (calibrating: the take's first frames, the body at rest)
		gs.sum += gs.off - low
		gs.n += 1
		if gs.n >= 3 then gs.base = gs.sum / gs.n end
		gs.off = gs.off - low
	else
		local target = gs.base + math.max(0, -natural)
		if all and natural > -1.5 and natural < 1.5 then target = gs.base - natural end
		gs.off += (target - gs.off) * math.min(1, dt * 14)
	end
	place()
end

-- the long blade's tip laid on the victim's face: his take holds it a stud over the head at THE TIP; the stretch's
-- payoff is the tip a hair from the nose, on any face
local AIM_A, AIM_B, AIM_END = 70, 77, 94
local propsAt: (sc: any, d: any, fi: number, katP: CFrame, shP: CFrame) -> (CFrame, CFrame)
local function aimed(sc: any, s: any, katCF: CFrame, L: number, fi: number): CFrame
	if fi < AIM_A or fi >= AIM_END then return katCF end
	local wgt = math.clamp((fi - AIM_A) / (AIM_B - AIM_A), 0, 1)
	local head = s.vg.model:FindFirstChild("Head") :: BasePart?
	if not head then return katCF end
	local ffa = head:FindFirstChild("FaceFrontAttachment")
	local face = if ffa and ffa:IsA("Attachment") then ffa.WorldPosition else (head.CFrame * Vector3.new(0, 0, -head.Size.Z / 2))
	face += head.CFrame.LookVector * 0.12
	local grip = katCF.Position
	-- (27 Nov: the stretched blade keeps its curve's height - its mesh broadens up to 2.6x but only stretches along its
	-- length - so its tip is 0.181 x that breadth over the line, not 0.181 x the length: the old point put the real tip
	-- 1.3 studs under the face and THE TIP's tight lens never saw the blade)
	local tip = katCF * Vector3.new(0, 0.181 * (1 + 1.6 * math.clamp((L - 1.5) / 8.5, 0, 1)), GZ + (-3.84 - GZ) * L)
	local v1, v2 = (tip - grip), (face - grip)
	if v1.Magnitude < 1e-3 or v2.Magnitude < 1e-3 then return katCF end
	v1, v2 = v1.Unit, v2.Unit
	local ang = math.acos(math.clamp(v1:Dot(v2), -1, 1))
	if ang < 1e-4 or ang > math.rad(25) then return katCF end
	local axis = v1:Cross(v2)
	if axis.Magnitude < 1e-6 then return katCF end
	return CFrame.fromAxisAngle(axis.Unit, ang * wgt) * (katCF - grip) + grip
end

-- the camera's life: a handheld shake on the dash, a kick on the hits, the coil's impact frame and the launch's plant
-- (frames; decays in ~0.15 s; the coil itself held dead still)
local SHAKE = { ["THE LAUNCH"] = 1.6 }
local BUMPS = { { 11, 0.7 }, { 57, 1 }, { 119, 1.4 }, { 120, 1.2 }, { 139, 1.3 }, { 204, 0.6 }, { 207, 1 } }

-- the katana and its sheath on any body. 27 Nov, the owner: "it also just suddenly appears on her hip.. instead of
-- grabbing the katana it like snaps in front her legs then back in her hands ... she doesn't really unsheathe it". The
-- props ride proxies his take moves (the katana off the right hand, the sheath off the hips); on a body built unlike
-- his rig the hand and the hip don't keep his spacing, so a blade pinned to the sheath and a blade in the hand were two
-- places, and the switch between them was a jump. Now:
--   * sheathed: the blade in the sheath, the sheath on the hip (as before);
--   * drawing and sheathing (the data's slides): the sheath rides the BLADE as his take has it - the blade leaves the
--     mouth, or goes back in, on any body - and the blade the hand; the difference between where the sheathed blade
--     was and where the hand holds it eases out over the first frames, so nothing jumps;
--   * the draw ends on a cut (the sheath back on the hip there, out of sight); after the sheathe the sheath settles
--     back from where the blade went in onto the hip over a few frames, the blade home in it.
local function rowCF(r: any): CFrame
	return CFrame.new(r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12])
end
local function relAt(rows: any, fi: number): CFrame?
	if not rows then return nil end
	local f = math.floor(fi)
	local a, b = rows[f], rows[f + 1]
	if type(a) ~= "table" then return nil end
	if type(b) ~= "table" then return rowCF(a) end
	return rowCF(a):Lerp(rowCF(b), fi - f)
end
local function smooth01(u: number): number u = math.clamp(u, 0, 1); return u * u * (3 - 2 * u) end
local SETTLE = 8 -- (frames the sheath takes back onto the hip after the sheathe)
function propsAt(sc: any, d: any, fi: number, katP: CFrame, shP: CFrame): (CFrame, CFrame)
	local f = math.floor(fi)
	local home = d.inSheath and d.inSheath[f + 1] or 0
	local relRow = d.relS and d.relS[f + 1]
	local relS = if type(relRow) == "table" then rowCF(relRow) else nil
	for _, w in d.slides or {} do
		local a, b, kind, easeN = w[1], w[2], w[3], w[4]
		if fi >= a and fi < b then
			local rk = relAt(d.relKS, fi)
			if not rk then break end
			local u = smooth01((fi - a) / easeN)
			if kind == "draw" then
				if not sc.drawC then
					local ra = d.relS and d.relS[a + 1]
					sc.drawC = katP:Inverse() * (shP * (if type(ra) == "table" then rowCF(ra) else CFrame.identity))
				end
				local kat = katP * sc.drawC:Lerp(CFrame.identity, u)
				return kat, kat * rk
			else
				local shK = katP * rk
				if not sc.sheC then sc.sheC = shK:Inverse() * shP end
				local sh = shK * sc.sheC:Lerp(CFrame.identity, u)
				sc.sheLast, sc.sheEnd = sh, b
				return katP, sh
			end
		end
	end
	if sc.sheLast and sc.sheEnd and fi >= sc.sheEnd and fi < sc.sheEnd + SETTLE then
		local sh = sc.sheLast:Lerp(shP, smooth01((fi - sc.sheEnd) / SETTLE))
		return (if relS then sh * relS else katP), sh
	end
	if home > 0 and relS then return katP:Lerp(shP * relS, home), shP end
	return katP, shP
end

function Pro.step(s: any, w: number): (string, number, boolean)
	local sc = s.scene
	local d = sc.d
	local dt = math.clamp(w - (sc.lastW or w), 0, 0.1)
	sc.lastW = w
	local i, a = frameAt(sc, w)
	local T = (i + a) / d.fps
	-- (what is on screen this frame is the pose set last frame: the Animator applies a TimePosition at its next step.
	-- So the lens, the props and the grounding all follow the previous moment, and the bodies get this one)
	local pi_, pa = sc.prevI or i, sc.prevA or a
	sc.prevI, sc.prevA = i, a
	local fi = pi_ + pa
	local shotN = d.shot[pi_ + 1]
	local names = d.names or {}
	sc.shotNow = names[shotN] or tostring(shotN)
	sc.T = T
	sc.fi = fi
	for _, tr in sc.tracks do
		local L = tr.Length
		tr.TimePosition = if L > 0 then math.clamp(T, 0, L - 1 / 60) else T
	end
	ground(sc, "k", s.kg, fi, dt)
	ground(sc, "v", s.vg, fi, dt)
	for _, a in sc.rims or {} do
		local ut = a.Parent :: BasePart
		a.WorldPosition = ut.Position + d.rim.dir.Unit * d.rim.dist + Vector3.new(0, 1.5, 0)
	end
	-- the props: off their proxies; a blade home in its sheath stays home on any body
	local j = math.min(pi_ + 1, d.frames - 1)
	local L = d.blade[pi_ + 1] + (d.blade[j + 1] - d.blade[pi_ + 1]) * pa
	if d.shot[j + 1] ~= shotN then L = d.blade[pi_ + 1] end
	local katCF, shCF = propsAt(sc, d, fi, sc.pk.CFrame, sc.ps.CFrame)
	katCF = aimed(sc, s, katCF, L, fi)
	-- (27 Nov, the owner: "Katana blade is missing in the shot where it's pointed at enemy face" - the long blade lay
	-- with its flat up, edge-on to THE TIP's eye-level lens: a hairline in the dark. For that shot it turns on its own
	-- length so its flat faces the lens; the hand holding it is far out of the shot)
	if sc.shotNow == "THE TIP" then
		local cam = (workspace.CurrentCamera :: Camera).CFrame.Position
		local grip = katCF.Position
		local axis = katCF.LookVector
		local mid = grip + axis * (1.6 * L)
		local to = cam - mid
		to -= axis * to:Dot(axis)
		if to.Magnitude > 1e-3 then
			local r = katCF.RightVector
			local want = if r:Dot(to) >= 0 then to.Unit else -to.Unit
			local ang = math.atan2(r:Cross(want):Dot(axis), r:Dot(want))
			katCF = CFrame.fromAxisAngle(axis, ang) * (katCF - grip) + grip
		end
	end
	placeProps(sc, katCF, shCF, L)
	if sc.mouthA then sc.mouthW = (shCF * sc.mouthA).Position end
	-- the lens: ours over his, held to the real bodies' points (the stock rig's in the data), with the run's shake and
	-- the hits' kick
	local c, fov = baseLens(sc, pi_, pa)
	local an = d.anchor and d.anchor[shotN]
	local off = Vector3.zero
	if an then
		local sp, rp = stockPt(d, an[1], pi_, pa), realPt(sc, s, an[1])
		if sp and rp then
			off = (sc.take:PointToObjectSpace(rp) - sp) * an[2]
			if off.Magnitude > 6 then off = Vector3.zero end
		end
	end
	if sc.anShot ~= shotN then sc.anShot = shotN; sc.anOff = off else sc.anOff = sc.anOff:Lerp(off, math.min(1, dt * 10)) end
	local cw = sc.take * (c + sc.anOff)
	local shk = SHAKE[sc.shotNow]
	if shk then
		local t = w * 7
		cw *= CFrame.new(math.noise(t, 1.3) * 0.05 * shk, math.noise(t, 2.7) * 0.05 * shk, 0)
			* CFrame.Angles(math.rad(math.noise(t, 4.1) * 0.5 * shk), math.rad(math.noise(t, 5.9) * 0.5 * shk), 0)
	end
	for _, b in BUMPS do
		local age = (fi - b[1]) / d.fps
		if age >= 0 and age < 0.3 then
			local k = b[2] * math.exp(-age * 16) * math.sin(age * 55)
			cw *= CFrame.new(0, 0.05 * k, 0) * CFrame.Angles(0, 0, math.rad(1.1 * k))
		end
	end
	local cam = workspace.CurrentCamera :: Camera
	cam.CameraType = Enum.CameraType.Scriptable
	-- (his field of view is vertical, Roblox's default: held so for the scene in case anything left the camera otherwise)
	if not sc.fovModeWas then sc.fovModeWas = cam.FieldOfViewMode end
	if cam.FieldOfViewMode ~= Enum.FieldOfViewMode.Vertical then cam.FieldOfViewMode = Enum.FieldOfViewMode.Vertical end
	cam.CFrame = cw
	cam.FieldOfView = fov
	-- (the shot's exposure)
	local lk = d.look and d.look.lighting
	if lk and lk.ExposureCompensation then
		local want = lk.ExposureCompensation + ((d.expTrim and d.expTrim[sc.shotNow]) or 0)
		local L = game:GetService("Lighting")
		if math.abs(L.ExposureCompensation - want) > 1e-3 then L.ExposureCompensation = want end
	end
	-- the ink and petals (after the lens: the glints turn to it), the sounds on their frames
	if Fx then
		local ok, err = pcall(Fx.step, sc, s, fi, w, dt, katCF, L)
		if not ok and not sc.fxWarned then sc.fxWarned = true; warn("[jankfire] finisher pro fx: " .. tostring(err)) end
	end
	if Sfx then
		for _, q in d.cues or {} do
			if not sc.cued[q] and fi >= q[1] and q[1] >= sc.f0 then
				sc.cued[q] = true
				pcall(Sfx.play, q[2], nil, q[3])
			end
		end
	end
	if RunService:IsStudio() then
		local function rel(p: BasePart?): string
			if not p then return "-" end
			local q = sc.take:PointToObjectSpace(p.Position)
			return ("%.1f,%.1f,%.1f"):format(q.X, q.Y, q.Z)
		end
		local kl, vl = s.kg.model:FindFirstChild("LowerTorso") :: BasePart?, s.vg.model:FindFirstChild("LowerTorso") :: BasePart?
		local cq = sc.take:PointToObjectSpace(cw.Position)
		local skl = stockPt(d, "kLT", pi_, pa)
		workspace:SetAttribute("ProDebug", ("f%.1f %s | kRoot %s %s kLT %s (stock %s) | vRoot %s %s vLT %s | cam %.1f,%.1f,%.1f off %.1f,%.1f,%.1f | gnd %.2f %.2f | fov set %.1f now %.1f %s vp %dx%d"):format(
			fi, tostring(sc.shotNow), s.kg.root.Name, rel(s.kg.root), rel(kl), if skl then ("%.1f,%.1f,%.1f"):format(skl.X, skl.Y, skl.Z) else "-",
			s.vg.root.Name, rel(s.vg.root), rel(vl), cq.X, cq.Y, cq.Z, sc.anOff.X, sc.anOff.Y, sc.anOff.Z, sc.gnd.k.off, sc.gnd.v.off,
			fov, cam.FieldOfView, tostring(cam.FieldOfViewMode), cam.ViewportSize.X, cam.ViewportSize.Y))
	end
	-- (the shot's name and how far through it, for Finisher.luau's overlay: the last shot carries the name card)
	local s0, s1 = pi_, pi_
	while s0 > 0 and d.shot[s0] == shotN do s0 -= 1 end
	while s1 < d.frames - 1 and d.shot[s1 + 2] == shotN do s1 += 1 end
	local u = math.clamp((fi - s0) / math.max(1, s1 - s0), 0, 1)
	return sc.shotNow, u, shotN == d.shot[d.frames]
end

function Pro.hitNow(s: any): boolean
	return s.scene ~= nil and s.scene.hitOn == true
end

-- (the scene's own grade: the set's SceneLook carries the night's colour, so this stays neutral - until the very end,
-- where the brief greys it out as he comes apart)
local GREY_FROM, GREY_OVER = 236, 18
function Pro.grade(s: any): any
	local sc = s.scene
	if not sc then return nil end
	local k = math.clamp(((sc.fi or 0) - GREY_FROM) / GREY_OVER, 0, 1)
	k = k * k * (3 - 2 * k)
	return { tint = Color3.new(1, 1, 1), sat = -0.55 * k, con = 0.04 + 0.08 * k, bright = -0.02 * k }
end

function Pro.barsIn(s: any): number?
	local sc = s.scene
	return sc and sc.d.barsIn or nil
end

function Pro.stop(s: any)
	local sc = s.scene
	if not sc then return end
	s.scene = nil
	playing = nil
	for _, tr in sc.tracks do pcall(function() tr:Stop(0) end) end
	if sc.fovModeWas then pcall(function() (workspace.CurrentCamera :: Camera).FieldOfViewMode = sc.fovModeWas end) end
	local bed = sc.bed
	if bed and bed.Parent then
		game:GetService("TweenService"):Create(bed, TweenInfo.new(0.3), { Volume = 0 }):Play()
		task.delay(0.35, function() bed:Destroy() end)
	end
	restoreLook(sc)
	for _, inst in sc.made do pcall(function() inst:Destroy() end) end
	for _, gh in sc.ghosts or {} do pcall(function() gh.model:Destroy() end) end
	for _, g in { s.kg, s.vg } do
		local h = g and g.model and g.model:FindFirstChild("JankProInk")
		if h then h:Destroy() end
	end
	if sc.folder then sc.folder:Destroy() end
end

return Pro
