--!strict
-- your weapon in first person: the web game's pose stack (public/js/weapons.js, vmbob.js, anim.js), every frame, in
-- camera space: rest pose -> swap drop -> footstep bob -> breathing -> look sway -> run tilt -> aim (ADS) -> the clip
-- (draw / swing / parry / reload / staggered) -> recoil springs. plus the Redline's needle + vents, the katana's
-- length, two chunky hands. metres from the web game x3 = studs
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local WeaponModels = require(Shared:WaitForChild("WeaponModels"))
local Anims = require(Shared:WaitForChild("Anims")) :: any
local Fx = require(script.Parent:WaitForChild("Fx"))
local GunParts = require(script.Parent:WaitForChild("GunParts")) -- batch 3: the pieces that move (mags, pump, bolt, lever...)
local GunHats = require(Shared:WaitForChild("GunHats")) -- the hat on the gun (the loadout's Hats)
local GunSkins = require(Shared:WaitForChild("GunSkins")) -- the gun's skin (the loadout's Skins: another body)
-- the plain guns' reloads (Reloads.luau, generated from the web game's reloads.js) join the hand-keyed clips
for name, a in require(Shared:WaitForChild("Reloads")) :: any do
	if not Anims[name] then Anims[name] = a end
end

local S = Weapons.S
local VM = {}
VM.onEvent = nil :: ((string) -> ())?
VM.wid = ""
VM.skin = nil :: string? -- (the held weapon's skin, if any)
VM.model = nil :: Model?
VM.hitStop = 0
VM.parts = nil :: GunParts.State?
-- the utility slot (Utility.client.luau) borrows the off hand while an item is used: a frame in the world for the
-- fist (Y up through it), how far the hand has gone there (0 to 1), and whether it's held from under. nil = no item
VM.offHook = nil :: (() -> (CFrame?, number, boolean))?

local camera = workspace.CurrentCamera
local clip: { name: string, t: number, fired: { [number]: boolean }, rate: number? }? = nil
local swap = 0
local follow: { name: string, at: number }? = nil -- the clip a shot queued (the pump, the bolt, the lever)
local offGone = false -- the off hand has let go (a plain gun's reload)
local rec = { p = Vector3.zero, pv = Vector3.zero, r = Vector3.zero, rv = Vector3.zero }
local punch = { x = Vector3.zero, v = Vector3.zero }
local kick = 0
local kickUp = 0 -- (kick's upward tilt, scaled by VM.feel: the rearward push keeps kick whole)
local bobPh, breathT = 0, 0
local sway = Vector2.zero
local runK = 0
local feel = { ground = 0, slide = 0, slip = 0, speed = 0 } -- (the body's state, eased: VM.update)
local lastLook: Vector3? = nil
local needles: { Weld } = {}
local needleAng = -2.3
local hubCF = CFrame.identity
local vents: { BasePart } = {}
local k = 3

local EASE = {
	linear = function(u: number) return u end,
	smooth = function(u: number) return u * u * (3 - 2 * u) end,
	snap = function(u: number) return 1 - (1 - u) ^ 3 end,
	["in"] = function(u: number) return u * u * u end,
	back = function(u: number) local c = 1.9; return 1 + (c + 1) * (u - 1) ^ 3 + c * (u - 1) ^ 2 end,
}

local function v3(a: { number }): Vector3 return Vector3.new(a[1], a[2], a[3]) end

-- a clip's pose at time t: position offset (studs) and the rotation (base euler + offset; quaternion blend for slerp)
function VM.sample(name: string, t: number, base: Vector3): (Vector3, CFrame)
	local a = Anims[name]
	local keys = a.keys
	local k0, k1 = keys[1], keys[#keys]
	if t <= keys[1].t then k1 = keys[1] end
	for i = 1, #keys - 1 do
		if t >= keys[i].t and t < keys[i + 1].t then k0, k1 = keys[i], keys[i + 1]; break end
	end
	local span = k1.t - k0.t
	local u = if span > 0 then math.clamp((t - k0.t) / span, 0, 1) else 1
	local e = (EASE :: any)[k1.e](u)
	local p = v3(k0.p):Lerp(v3(k1.p), e) * S
	if a.slerp then
		local sb = v3(a.slerp)
		local c0 = CFrame.fromEulerAnglesXYZ((sb + v3(k0.r)).X, (sb + v3(k0.r)).Y, (sb + v3(k0.r)).Z)
		local c1 = CFrame.fromEulerAnglesXYZ((sb + v3(k1.r)).X, (sb + v3(k1.r)).Y, (sb + v3(k1.r)).Z)
		return p, c0:Lerp(c1, e)
	end
	local r = base + v3(k0.r):Lerp(v3(k1.r), e)
	return p, CFrame.fromEulerAnglesXYZ(r.X, r.Y, r.Z)
end

local prop: Model? = nil
local function dropProp() if prop then prop:Destroy(); prop = nil end end
function VM.play(name: string)
	if not Anims[name] then return end
	dropProp()
	clip = { name = name, t = 0, fired = {} }
end
-- a gun's reload: its own clip, or (a plain gun with none yet) the Assault Rifle's, played faster or slower so it
-- ends when the reload does. empty = the mag ran dry (Plan B has a reload of its own for that: the slide is dropped)
function VM.reload(wid: string, secs: number, empty: boolean?)
	local name = if Anims["reload_" .. wid] then "reload_" .. wid else "reload_ar"
	if empty and Anims[name .. "_empty"] then name ..= "_empty" end
	local a = Anims[name]
	if not a then return end
	dropProp()
	follow = nil
	clip = { name = name, t = 0, fired = {}, rate = if secs > 0 then a.dur / secs else 1 }
end
-- the clip that follows a shot, `delay` s after it (the Shotgun's pump, the Sniper's bolt, the Yeehaw's lever). a
-- reload that starts first drops it, like the web game
function VM.follow(name: string, delay: number)
	if Anims[name] then follow = { name = name, at = os.clock() + delay } end
end
-- a shot went off: the cylinder turns, the hammer falls, the slide kicks, the barrel warms (GunParts)
function VM.shot(w: any)
	if VM.parts then GunParts.shot(VM.parts, w) end
end
function VM.heat(): number return if VM.parts then VM.parts.heat else 0 end
function VM.playing(): string? return clip and clip.name end
function VM.clipT(): number? return clip and clip.t end
function VM.stop() clip = nil; dropProp() end
-- (the katana's held guard, 18 Nov 2026) keep the playing clip at time t while it's `name`: the parry pose stays up
function VM.holdAt(name: string, t: number) if clip and clip.name == name and clip.t > t then clip.t = t end end

-- how hard a gun kicks, by its kind (the owner, 17 Nov 2026: "can the gun not shoot up when you shoot or at least
-- not as aggressively?"). the web game's rows stay; on top: up = the gun's upward pitch, punch = the view punch's,
-- climb = the camera's own climb (Arsenal) with hold = the pause after a shot before the camera eases back to where
-- you aimed, pull = a steady ease back (per second) even inside the hold, so a spray faster than the hold (the
-- Redline at low HP: 22 shots a second) can't pile the climb up. the rearward punch is kept whole. the automatics
-- least, the snipers and shotguns a little more
local HEAVY = { sniper = true, shotgun = true, sawnoff = true, marbles = true, autoshot = true }
local FEEL = {
	auto = { up = 0.35, punch = 0.5, climb = 0.4, hold = 0.05, pull = 6 },
	semi = { up = 0.4, punch = 0.6, climb = 0.5, hold = 0.06, pull = 3 },
	heavy = { up = 0.5, punch = 0.7, climb = 0.6, hold = 0.09, pull = 0 },
}
VM.FEEL = FEEL
function VM.feel(wid: string, w: any): { up: number, punch: number, climb: number, hold: number, pull: number }
	if HEAVY[wid] then return FEEL.heavy end
	if w and w.auto and (w.rate or 0) >= 6 then return FEEL.auto end
	return FEEL.semi
end

-- a shot: the gun's recoil row on the springs + a camera view punch (public/js/weapons.js kickVM). up / pm scale the
-- upward pitch and the view punch (VM.feel, and Settings' visual recoil: gfx.recoil, nil = 1)
local function rnd(): number return (if math.random() < 0.5 then -1 else 1) * (0.5 + math.random() * 0.5) end
function VM.kick(row: { back: number, up: number, roll: number, side: number, punch: number }?, mul: number, fast: boolean, up: number?, pm: number?)
	local r = row or { back = 0.8, up = 2.5, roll = 1, side = 0.2, punch = 0.01 }
	local u, p = up or 1, pm or 1
	rec.pv += Vector3.new(r.side * rnd(), 0, r.back) * mul
	rec.rv += Vector3.new(r.up * u, 0, r.roll * rnd()) * mul
	punch.v += Vector3.new(r.punch * p, r.punch * 0.35 * rnd(), r.punch * 0.5 * rnd()) * mul * 21
	kick += if fast then 0.25 else 1
	kickUp += (if fast then 0.25 else 1) * u
end
-- a landed parry / hit: a jolt on the blade
function VM.jolt(up: number) rec.rv += Vector3.new(up, 0, 0); rec.pv += Vector3.new(0, 0, up * 0.3) end

-- the camera's view punch (visual only): applied after the camera module each frame
function VM.punch(): CFrame return CFrame.fromEulerAnglesXYZ(punch.x.X, punch.x.Y, punch.x.Z) end

local AvatarArms = require(game:GetService("ReplicatedStorage"):WaitForChild("Jankfire"):WaitForChild("AvatarArms"))
local Holds = require(Shared:WaitForChild("Holds")) :: any
-- every weapon in first person is drawn this much larger than the web game's scale, the hands with it (the owner,
-- 16 Nov 2026: "Can the weapons be a little larger, that way the arms dont look so long and lanky"). one number, in
-- tools/roblox/holds.json (_size); the third-person guns and the loadout previews are not touched
local SIZE: number = Holds.size or 1
-- (a weapon's own scale on top: the one-handed guns are drawn smaller, their hand came too close to the camera)
-- which look a weapon is held in: holds.json keeps three per weapon (before / after / combined) and "use" picks one;
-- a Play test can show one look on every weapon at once through the player's HoldLook attribute
local LookPlayer = game:GetService("Players").LocalPlayer
local function look(wid: string): any
	local row = Holds.holds[wid]
	if not row then return nil end
	local want = LookPlayer:GetAttribute("HoldLook")
	return (row.looks and ((type(want) == "string" and row.looks[want]) or row.looks[row.use])) or row
end
VM.look = look
local function sizeOf(wid: string): number
	local row = look(wid)
	return SIZE * (if row and row.scale then row.scale else 1)
end
-- the aimed view (Holds ads): the weapon's row and the held skin's own part of it (a skin's aimZ / sight / pieces hidden)
local function adsOf(wid: string): (any, any)
	local h = Holds.holds[wid] :: any
	local a = h and h.ads
	local sk = a and a.skins and wid == VM.wid and VM.skin and a.skins[VM.skin]
	return a, sk or nil
end
local adsHide: { BasePart } = {} -- (this skin's wings, horns and crowns: faded out while you aim)

-- the katana's rest and parry poses (Holds.katana, from tools/roblox/holds.json): a turn and a shift laid over the web
-- game's clips, so the flat of the blade, the guard and the wrapped handle face you. the cut itself is the web game's:
-- the fix eases out as a swing winds up and back in as it recovers
local function katanaFix(name: string?, t: number): (CFrame, Vector3)
	local K = Holds.katana
	local want = LookPlayer:GetAttribute("HoldLook")
	local kl = K.looks and ((type(want) == "string" and K.looks[want]) or K.looks[K.use])
	local rest = if kl then kl.rest else K.fixes.rest
	local keys = if name then K.clips[name] else nil
	if not keys then return rest.rot, rest.pos end
	local a, b = keys[1], keys[#keys]
	if t <= keys[1].t then b = keys[1] end
	for i = 1, #keys - 1 do
		if t >= keys[i].t and t < keys[i + 1].t then a, b = keys[i], keys[i + 1]; break end
	end
	local span = b.t - a.t
	local u = if span > 0 then math.clamp((t - a.t) / span, 0, 1) else 1
	u = u * u * (3 - 2 * u)
	local fa = if a.fix == "rest" then rest else K.fixes[a.fix]
	local fb = if b.fix == "rest" then rest else K.fixes[b.fix]
	return fa.rot:Lerp(fb.rot, u), fa.pos:Lerp(fb.pos, u)
end

-- ---- the off hand. it is not glued to the gun (AvatarArms places it every frame), so it can do its own part of a
-- reload instead of leaving the picture: it goes with the magazine out of the gun and back, rides the Shotgun's pump,
-- holds the Redline's can and the marble bag, and stands clear while the Yeehaw spins. (a Grab = a piece it can be
-- on, and the grip's frame against that piece: where the fist is, its +Y along the piece toward the thumb)
type Grab = { part: BasePart, rel: CFrame }
local armsOn = false -- (your arms are on the weapon: not the stand-in boxes)
local ride: Grab? = nil -- the pump: the hand's own hold moves with it
local magGrab: Grab? = nil -- the magazine, from below
local crankGrab: Grab? = nil -- a skin's crank (the Marble Shotgun's gumball machine): the hand rides it as it turns
local lidTop: Vector3? = nil -- the top of the Marble Shotgun's lid, shut (the weapon's root frame, studs)
-- a one-handed gun's left hand (its hold row says away): off screen and hidden, it comes in only for the reload's
-- off-hand track (Reloads lh: { t, k 0 away..1 there, f what it follows }, the web game's timings): 1 the magazine,
-- 5 the cylinder (from under, as it swings out), 6 / 7 the thumb behind shell 1 / 2 (Half a Shotgun)
local awayL = false
local lhGrab: { [number]: { grab: Grab, under: boolean } } = {}
-- the Revolver's speedloader (below): its spots in file metres, its times in s; the cylinder's back face it seats on
local LOADER = { face = Vector3.new(0, 0.009, 0.004), knob = 0.031, show = { 0.45, 1.32 }, drop = 0.95 }
local cylRear: { part: BasePart, rel: CFrame }? = nil -- (the cylinder's back face on its axis, against the cylinder piece)
local function smoothstep(u: number): number u = math.clamp(u, 0, 1); return u * u * (3 - 2 * u) end
-- a set of pieces' box in the weapon's root frame (studs, at rest)
local function boxOf(list: { any }, root: BasePart): (Vector3, Vector3)
	local lo, hi = Vector3.one * math.huge, -Vector3.one * math.huge
	for _, p in list do
		local part = p.part :: BasePart
		local rel = root.CFrame:ToObjectSpace(part.CFrame)
		local h = part.Size / 2
		for _, sx in { -1, 1 } do for _, sy in { -1, 1 } do for _, sz in { -1, 1 } do
			local q = rel:PointToWorldSpace(Vector3.new(sx * h.X, sy * h.Y, sz * h.Z))
			lo = lo:Min(q); hi = hi:Max(q)
		end end end
	end
	return lo, hi
end

local function offHandSetup(m: Model, root: BasePart)
	ride, magGrab, crankGrab, lidTop = nil, nil, nil, nil
	lhGrab = {}
	cylRear = nil
	local rowL = (AvatarArms.rows(VM.wid, VM.skin) or {}).Left
	awayL = rowL ~= nil and rowL.away == true
	local hold = AvatarArms.holdFrame(VM.wid, "Left", k, nil, VM.skin)
	local st = VM.parts
	if not armsOn or not hold or not st then return end
	-- (the away hand's pieces: the cylinder from under, palm up; the thumb behind each shell, pushing it home)
	if awayL then
		local cyl = st.nodes.cylinder
		if cyl and #cyl > 0 then
			local lo, hi = boxOf(cyl, root)
			local main = cyl[1].part :: BasePart
			lhGrab[5] = { grab = { part = main, rel = main.CFrame:ToObjectSpace(root.CFrame * CFrame.new((lo.X + hi.X) / 2, lo.Y, (lo.Z + hi.Z) / 2)) }, under = true }
			-- (the Revolver loads it with a speedloader: its back face, on its axis, the gun's own turn)
			if VM.wid == "revolver" then cylRear = { part = main, rel = main.CFrame:ToObjectSpace(root.CFrame * CFrame.new(LOADER.face * k)) } end
		end
		for i, node in { "shell1", "shell2" } do
			local sh = st.nodes[node]
			if sh and #sh > 0 then
				local lo, hi = boxOf(sh, root)
				local main = sh[1].part :: BasePart
				local at = CFrame.new((lo.X + hi.X) / 2 - 0.012 * k, (lo.Y + hi.Y) / 2 - 0.018 * k, hi.Z + 0.02 * k) * CFrame.Angles(-math.pi / 2, 0, 0)
				lhGrab[5 + i] = { grab = { part = main, rel = main.CFrame:ToObjectSpace(root.CFrame * at) }, under = false }
			end
		end
	end
	local function biggest(list: { any }?): BasePart?
		local best: BasePart? = nil
		for _, p in list or {} do
			local part = p.part :: BasePart
			if not best or part.Size.Magnitude > best.Size.Magnitude then best = part end
		end
		return best
	end
	local pump = biggest(st.nodes.pump)
	if pump then ride = { part = pump, rel = pump.CFrame:ToObjectSpace(root.CFrame * hold) } end
	-- the crank: its handle (low at the back of its axle at rest, the gun-models session), the fist's +Y out to the left
	local crank = biggest(st.nodes.crank)
	if crank then
		local at = root.CFrame * CFrame.new(Vector3.new(-0.05, -0.026, -0.07) * k) * CFrame.Angles(0, 0, math.pi / 2)
		crankGrab = { part = crank, rel = crank.CFrame:ToObjectSpace(at) }
	end
	-- the lid's top, shut: the highest point of its pieces over their middle
	local lids = st.nodes.lid
	if lids and #lids > 0 then
		local lo, hi = Vector3.one * math.huge, -Vector3.one * math.huge
		for _, p in lids do
			local part = p.part :: BasePart
			local rel = root.CFrame:ToObjectSpace(part.CFrame)
			local h = part.Size / 2
			for _, sx in { -1, 1 } do for _, sy in { -1, 1 } do for _, sz in { -1, 1 } do
				local q = rel:PointToWorldSpace(Vector3.new(sx * h.X, sy * h.Y, sz * h.Z))
				lo = lo:Min(q); hi = hi:Max(q)
			end end end
		end
		lidTop = Vector3.new((lo.X + hi.X) / 2, hi.Y, (lo.Z + hi.Z) / 2)
	end
	local mags = st.nodes.mag
	local mag = biggest(mags)
	if mag and mags then
		-- round the magazine's lower end, the thumb up toward the gun
		local lo, hi = Vector3.one * math.huge, -Vector3.one * math.huge
		for _, p in mags do
			local part = p.part :: BasePart
			local rel = root.CFrame:ToObjectSpace(part.CFrame)
			local h = part.Size / 2
			for _, c in { Vector3.new(h.X, h.Y, h.Z), Vector3.new(-h.X, h.Y, h.Z), Vector3.new(h.X, -h.Y, h.Z), Vector3.new(h.X, h.Y, -h.Z), Vector3.new(-h.X, -h.Y, h.Z), Vector3.new(-h.X, h.Y, -h.Z), Vector3.new(h.X, -h.Y, -h.Z), Vector3.new(-h.X, -h.Y, -h.Z) } do
				local q = rel:PointToWorldSpace(c)
				lo = lo:Min(q); hi = hi:Max(q)
			end
		end
		local at = CFrame.new((lo.X + hi.X) / 2, lo.Y + math.min(0.04 * k, (hi.Y - lo.Y) * 0.35), (lo.Z + hi.Z) / 2)
		magGrab = { part = mag, rel = mag.CFrame:ToObjectSpace(root.CFrame * at) }
		lhGrab[1] = { grab = magGrab :: Grab, under = false }
	end
end

-- ---- the Revolver's speedloader (the web game's reloads.js p_speedloader, 17 Nov): the off hand brings it in behind
-- the swung-out cylinder (0.32-0.76 s), seats it (0.92), the rounds drop into the chambers (0.95), a twist (1.1-1.2),
-- it pulls away (1.24) and is gone (1.32). it rides in the hand, its knob in the fist; seated, it sits on the cylinder's
-- back face, on its axis. built here in the kit's flat colours, sized to the gun (file metres x k). our hand is far
-- bigger than the web game's fist and, holding the knob from behind, hid the whole loader: so it lets go once the
-- loader is seated (0.8-0.92), the rounds drop in plain sight, and it comes back for the twist and the pull (1.0-1.12)
local function buildLoader(): Model
	local m = Instance.new("Model")
	m.Name = "p_speedloader"
	local function cyl(name: string, d: number, len: number, at: Vector3, color: Color3): BasePart
		local p = Instance.new("Part")
		p.Name = name; p.Shape = Enum.PartType.Cylinder
		p.Size = Vector3.new(len, d, d) * k; p.Color = color; p.Material = Enum.Material.SmoothPlastic
		p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
		p:SetAttribute("At", at * k) -- (its spot in the loader's frame: z back from the cylinder's face)
		p.Parent = m
		return p
	end
	cyl("Body", 0.074, 0.02, Vector3.new(0, 0, 0.012), Color3.fromRGB(46, 48, 54))
	cyl("Knob", 0.026, 0.018, Vector3.new(0, 0, LOADER.knob), Color3.fromRGB(74, 76, 84))
	for i = 0, 5 do
		local a = i * math.pi / 3
		cyl("Round" .. i, 0.014, 0.034, Vector3.new(math.cos(a) * 0.026, math.sin(a) * 0.026, -0.012), Color3.fromRGB(214, 170, 80))
	end
	m.Parent = camera
	return m
end
-- the loader's frame (world), seated or on its way, from its distance behind the face and its twist at t
local function loaderSeat(t: number): CFrame?
	local cr = cylRear
	if not cr then return nil end
	local d = if t < 0.76 then 0.03 + 0.09 * (1 - smoothstep((t - 0.5) / 0.26)) elseif t < 0.92 then 0.03 * (1 - smoothstep((t - 0.76) / 0.16))
		elseif t < 1.2 then 0 else 0.09 * smoothstep((t - 1.2) / 0.1)
	local tw = 1.2 * smoothstep((t - 1.1) / 0.1)
	return cr.part.CFrame * cr.rel * CFrame.new(0, 0, d * k) * CFrame.Angles(0, 0, tw)
end
local function knobGrip(): CFrame return CFrame.new(0, 0, LOADER.knob * k) * CFrame.Angles(-math.pi / 2, 0, 0) end
-- how far the hand is on the loader at t (0 away, hidden .. 1 on the knob)
local function loaderHand(t: number): number
	if t < 0.32 or (t >= 0.92 and t < 1) or t >= 1.42 then return 0 end
	if t < 0.6 then return smoothstep((t - 0.32) / 0.28) end
	if t < 0.8 then return 1 end
	if t < 0.92 then return 1 - smoothstep((t - 0.8) / 0.12) end
	if t < 1.12 then return smoothstep((t - 1) / 0.12) end
	if t < 1.32 then return 1 end
	return 1 - smoothstep((t - 1.32) / 0.1)
end
-- every frame (after offHand): the loader in the hand, where the hand is this frame
local function placeLoader(root: BasePart, to: CFrame?, mix: number, hidden: boolean?)
	local t = clip and clip.name == "reload_revolver" and clip.t
	-- (in the hand on its way in and on its way out; on the cylinder by itself in between)
	local inHand = t and (t < 0.8 or t > 1.22)
	if hidden or not t or not cylRear or t < LOADER.show[1] or t > LOADER.show[2] or (inHand and (not to or mix < 0.05)) then
		if prop and prop.Name == "p_speedloader" then dropProp() end
		return
	end
	local L: CFrame
	if inHand and to then
		local holdL = AvatarArms.holdFrame(VM.wid, "Left", k, nil, VM.skin)
		if not holdL then return end
		local F = (root.CFrame * holdL):Lerp(to, mix) -- (the fist's frame, as AvatarArms places it)
		L = F * knobGrip():Inverse()
	else
		local seat = loaderSeat(t)
		if not seat then return end
		L = seat
	end
	local lp = prop or buildLoader()
	prop = lp
	for _, p in lp:GetChildren() do
		if not p:IsA("BasePart") then continue end
		local at = p:GetAttribute("At")
		-- (a Part cylinder's axis is its X: turned onto the loader's Z)
		if typeof(at) == "Vector3" then p.CFrame = L * CFrame.new(at) * CFrame.Angles(0, math.pi / 2, 0) end
		if string.sub(p.Name, 1, 5) == "Round" then p.Transparency = if t >= LOADER.drop then 1 else 0 end
	end
end

-- what the away hand follows (the track's f) and whether it holds it from under: the Revolver's cylinder is its
-- speedloader's knob while it loads, else the piece's grab
local function lhFrame(f: number, t: number): (CFrame?, boolean)
	if f == 5 and cylRear then
		local seat = loaderSeat(t)
		if seat then return seat * knobGrip(), false end
	end
	local g = lhGrab[f]
	if not g then return nil, false end
	return g.grab.part.CFrame * g.grab.rel, g.under
end

-- the reload's off-hand track at t: how far the hand is in (0 to 1) and what it follows (a fraction blends two)
local function sampleLh(keys: { { number } }, t: number): (number, number)
	if t <= keys[1][1] then return keys[1][2], keys[1][3] end
	for i = 1, #keys - 1 do
		local a, b = keys[i], keys[i + 1]
		if t < b[1] then
			local u = (t - a[1]) / math.max(b[1] - a[1], 1e-4)
			return a[2] + (b[2] - a[2]) * u, a[3] + (b[3] - a[3]) * u
		end
	end
	local z = keys[#keys]
	return z[2], z[3]
end

-- where the off hand is this frame: (a frame in the world or nil for its hold, how far it has gone there, whether
-- that frame is something held from under: AvatarArms.override)
local function offHand(m: Model, root: BasePart): (CFrame?, number, boolean)
	-- a one-handed gun: the left hand only comes in for its reload's off-hand track, then goes again
	if awayL then
		local lh = clip and Anims[clip.name].lh
		if not lh then return nil, 0, false end
		local kIn, f = sampleLh(lh, clip.t)
		if cylRear and clip.name == "reload_revolver" then kIn, f = loaderHand(clip.t), 5 end
		local f0, f1 = math.floor(f), math.ceil(f)
		if kIn <= 0.001 then return nil, 0, false end
		local FA, uA = lhFrame(f0, clip.t)
		local FB, uB = lhFrame(f1, clip.t)
		if not (FA or FB) then return nil, 0, false end
		local to = if FA and FB then FA:Lerp(FB, f - f0) elseif FA then FA else FB
		return to, smoothstep(kIn), uA or uB
	end
	local base: CFrame? = if ride then ride.part.CFrame * ride.rel else nil
	if not clip then return base, if base then 1 else 0, false end
	local a = Anims[clip.name]
	local t = clip.t
	local ch = a.ch
	-- the whole gun turns round the other hand (the Yeehaw's spin-cock): clear of it, down out of the picture
	local tw = ch and ch.twirl
	if tw then
		local t0, t1 = tw[1][1], tw[#tw][1]
		for i = 1, #tw do if tw[i][2] ~= 0 then t0 = tw[math.max(1, i - 1)][1]; break end end
		local mix = smoothstep((t - (t0 - 0.16)) / 0.16) * (1 - smoothstep((t - t1) / 0.2))
		if mix > 0 then
			local hold = root.CFrame * (AvatarArms.holdFrame(VM.wid, "Left", k, nil, VM.skin) :: CFrame)
			local away = CFrame.new(camera.CFrame:VectorToWorldSpace(Vector3.new(-0.1, -0.42, 0.12) * S)) * hold
			return away, mix, false
		end
	end
	-- the magazine: there before it leaves, down and back with it, off it once it is home
	local mk = ch and ch.mag
	if mk and magGrab and #mk >= 3 then
		local t0, t1 = mk[2][1], mk[#mk][1]
		local mix = smoothstep((t - (t0 - 0.2)) / 0.18) * (1 - smoothstep((t - t1) / 0.22))
		if mix > 0 then return magGrab.part.CFrame * magGrab.rel, mix, false end
	end
	-- the reload props: the can and the bag sit in the hand (under their foot) from when they come up to when they go
	if prop then
		-- (when each is out, and how tall it is: VM.props below)
		local win = if clip.name == "reload_redline" then { 0.2, 1.26, 0.11 } elseif clip.name == "reload_marbles" then { 0.4, 1.35, 0.12 } else nil
		local hold = AvatarArms.holdFrame(VM.wid, "Left", k, nil, VM.skin)
		if win and hold then
			local mix = math.min(smoothstep((t - win[1]) / 0.12), 1 - smoothstep((t - (win[2] - 0.2)) / 0.2))
			return prop:GetPivot() * CFrame.new(0, -win[3] * S * SIZE / 2, 0), mix, true -- (under its foot, as it tips)
		end
	end
	-- the Marble Shotgun, after the bag: up to the jar's lid and the palm down on it as it snaps shut (1.42-1.50,
	-- the gun-models session's lid), then back; a skin with a crank: the hand rides the crank while it turns
	if clip.name == "reload_marbles" and t > 1.33 then
		local come = smoothstep((t - 1.35) / 0.1) -- (in from above)
		local press = smoothstep((t - 1.42) / 0.08) -- (down with the lid)
		local top = lidTop or Vector3.new(0, 0.17, -0.06) * k
		local at = top + Vector3.new(0, (0.05 * (1 - come) + 0.01 * (1 - press)) * k, 0)
		local lidF = root.CFrame * CFrame.new(at) * CFrame.Angles(math.pi, 0, 0) -- (palm down: held from above)
		-- (it lets go right after the thwack, before the gun swings back up to the middle: 17 Nov, the crosshair kept clear)
		local mix = smoothstep((t - 1.33) / 0.1) * (1 - smoothstep((t - 1.53) / 0.1))
		if crankGrab then
			-- (from the lid straight down to the crank, then it rides the crank while it turns, 1.55-1.75)
			local u = smoothstep((t - 1.5) / 0.07)
			if u > 0 then
				return lidF:Lerp(crankGrab.part.CFrame * crankGrab.rel, u), 1 - smoothstep((t - 1.75) / 0.13), u < 0.5
			end
		end
		if mix > 0 then return lidF, mix, true end
	end
	return base, if base then 1 else 0, false
end

local function hands(m: Model, root: BasePart)
	-- your own avatar's hands and forearms, held the way the hold table says (AvatarArms.hold)
	armsOn = AvatarArms.hold(m, root, VM.wid, k, nil, sizeOf(VM.wid), VM.skin)
	offHandSetup(m, root)
	if armsOn then return end
	-- your body may not be built yet (a spawn): plain boxes for now
	local kit = AvatarArms.look() ~= "avatar"
	local skin = if kit then AvatarArms.KIT.glove else Color3.fromRGB(255, 206, 160)
	local sleeve = if kit then AvatarArms.KIT.sleeve else Color3.fromRGB(255, 79, 216)
	for _, spot in { "Grip", "Fore" } do
		local a = root:FindFirstChild(spot) :: Attachment?
		if not a then continue end
		local fist = Instance.new("Part")
		fist.Name = "Hand" .. spot; fist.Size = Vector3.new(0.09, 0.1, 0.11) * k; fist.Color = skin
		fist.Material = Enum.Material.SmoothPlastic; fist.CanCollide = false; fist.CanQuery = false; fist.CanTouch = false; fist.CastShadow = false
		fist.CFrame = root.CFrame * CFrame.new(a.Position) * CFrame.new(if spot == "Fore" then -0.01 * k else 0.01 * k, -0.02 * k, 0)
		local cuff = Instance.new("Part")
		cuff.Name = "Sleeve" .. spot; cuff.Size = Vector3.new(0.1, 0.1, 0.5) * k; cuff.Color = sleeve
		cuff.Material = Enum.Material.SmoothPlastic; cuff.CanCollide = false; cuff.CanQuery = false; cuff.CanTouch = false; cuff.CastShadow = false
		-- the forearm runs back and down to a shoulder off screen, so the hands never float
		cuff.CFrame = fist.CFrame * CFrame.Angles(0.5, if spot == "Fore" then -0.35 else 0.25, 0) * CFrame.new(0, -0.03 * k, 0.28 * k)
		for _, p in { fist, cuff } do
			local w = Instance.new("WeldConstraint"); w.Part0 = root; w.Part1 = p; w.Parent = p
			p.Parent = m
		end
	end
	-- ... then keep trying for a few seconds, and swap the boxes for your arms
	task.spawn(function()
		for _ = 1, 24 do
			task.wait(0.25)
			if VM.model ~= m or not m.Parent then return end
			if AvatarArms.hold(m, root, VM.wid, k, nil, sizeOf(VM.wid), VM.skin) then
				armsOn = true
				offHandSetup(m, root)
				for _, n in { "HandGrip", "SleeveGrip", "HandFore", "SleeveFore" } do
					local p = m:FindFirstChild(n)
					if p then p:Destroy() end
				end
				return
			end
		end
	end)
end

-- ---- a soft fill light that rides with the gun (16 Nov 2026). three judges in a row found every gun near-black in
-- first person: the side you see (its top and its left) faces away from the hall's lamps, and painting the guns
-- lighter moved those pixels 0 to 6 levels. so a dim SpotLight sits up and to the left of the gun's middle, a little
-- toward you (in camera space, so it stays put while the gun sways, kicks and turns in a reload), aimed at that
-- middle. nothing of it shows; its reach ends just past the gun's far side, so it does not get to the floor; up
-- against a wall, cover or another player its reach is cut to the first thing in its cone (five rays a frame), so
-- nothing but the gun gets it; it goes out whenever the viewmodel is hidden (third person, the scope, a menu). it
-- lights your hands too
local FILL = {
	dir = Vector3.new(-0.62, 0.62, 0.48).Unit, -- from the gun's middle toward the light, camera space
	away = 1.4, -- how far the light sits from the middle, in the gun's half-lengths (+ 0.5 studs)
	reach = 1.2, -- where its light ends: this many half-lengths past the middle
	brightness = 1.2, -- (tried 1 and 1.6 in the hall: 1.6 turns the Revolver's steel cylinder near-white)
	color = Color3.fromRGB(255, 247, 238), -- plain white, a touch warm like the hall's lamps
	angle = 80,
}
local fill: { at: Attachment, light: SpotLight, mid: Vector3, away: number, full: number, reach: number }? = nil
-- the rays that look for something in the light's way (light space, -Z = where it points): its middle and four at 30°
local FILL_RAYS = { Vector3.new(0, 0, -1) }
for _, d in { Vector3.new(1, 0, 0), Vector3.new(-1, 0, 0), Vector3.new(0, 1, 0), Vector3.new(0, -1, 0) } do
	table.insert(FILL_RAYS, (d * math.sin(math.rad(30)) + Vector3.new(0, 0, -math.cos(math.rad(30)))).Unit)
end
local fillRay = RaycastParams.new()
fillRay.FilterType = Enum.RaycastFilterType.Exclude
local fillSkip: { Instance } = {}
local localPlayer = game:GetService("Players").LocalPlayer
-- how far the light can reach from `from` before it would land on something you can see (not your own body or gun)
local function fillReach(from: Vector3, aim: CFrame, full: number): number
	local me = localPlayer.Character
	if fillSkip[1] ~= camera or fillSkip[2] ~= me then
		fillSkip = if me then { camera, me } else { camera }
		fillRay.FilterDescendantsInstances = fillSkip
	end
	local best = full
	for _, d in FILL_RAYS do
		local dir = aim:VectorToWorldSpace(d)
		local o, left = from, best
		for _ = 1, 4 do -- (through invisible blockers: they catch no light)
			local hit = workspace:Raycast(o, dir * left, fillRay)
			if not hit then break end
			local part = hit.Instance
			if not (part:IsA("BasePart") and part.Transparency >= 0.95) then
				best = math.min(best, (hit.Position - from).Magnitude)
				break
			end
			left -= hit.Distance + 0.02
			if left <= 0 then break end
			o = hit.Position + dir * 0.02
		end
	end
	return best
end

local function fillOn(m: Model, root: BasePart)
	local box, size = m:GetBoundingBox() -- (the gun alone: the hands are not on yet)
	local half = math.max(size.X, size.Y, size.Z) / 2
	local away = FILL.away * half + 0.5
	local at = Instance.new("Attachment")
	at.Name = "FillLight"
	local light = Instance.new("SpotLight")
	light.Name = "Fill"; light.Face = Enum.NormalId.Front; light.Angle = FILL.angle; light.Shadows = false
	light.Brightness = FILL.brightness; light.Color = FILL.color; light.Range = away + FILL.reach * half
	light.Parent = at
	at.Parent = root
	fill = { at = at, light = light, mid = root.CFrame:PointToObjectSpace(box.Position), away = away, full = light.Range, reach = light.Range }
end

-- swap to a weapon: build its viewmodel, play its draw
function VM.set(wid: string, kat: number)
	if VM.model then VM.model:Destroy(); VM.model = nil end
	dropProp()
	fill = nil
	VM.parts = nil
	offGone = false
	VM.wid = wid
	needles, vents = {}, {}
	adsHide = {}
	local w = Weapons.list[wid]
	if not w or not w.vm then return end
	k = S * w.vm.s * sizeOf(wid)
	VM.skin = GunSkins.skinFor(game:GetService("Players").LocalPlayer, wid)
	local m = WeaponModels.build(wid, k, VM.skin)
	if not m or not m.PrimaryPart then return end
	-- what the HUD draws while you aim this one (FightHud: sights take the crosshair's place, a dot sight shows a dot)
	local ads, adsSkin = adsOf(wid)
	LookPlayer:SetAttribute("AimSight", if ads then ads.kind elseif w.mdl and w.mdl.sight then "iron" else "none")
	-- a skin's wings, horns and crowns (its pieces whose names start with these) fade out while you aim
	if adsSkin and adsSkin.hide then
		for _, d in m:GetDescendants() do
			if not d:IsA("BasePart") then continue end
			local n = string.lower(d.Name)
			for _, pre in adsSkin.hide do
				if string.sub(n, 1, #pre) == pre and (#n == #pre or string.sub(n, #pre + 1, #pre + 1) == "_") then table.insert(adsHide, d); break end
			end
		end
	end
	local root = m.PrimaryPart
	root.Anchored = true
	-- a skin's big pieces by the stock (an angel's wings, right at the lens) drawn smaller in your own view only,
	-- about the spot where they meet the gun (Holds ads.skins[id].near: pieces, scale, pivot in file metres);
	-- everyone else sees them full size
	local near = adsSkin and adsSkin.near
	if near then
		local piv = root.CFrame * CFrame.new(near.pivot * k)
		for _, d in m:GetDescendants() do
			if not d:IsA("BasePart") or d == root then continue end
			local n = string.lower(d.Name)
			for _, pre in near.pieces do
				if string.sub(n, 1, #pre) == pre and (#n == #pre or string.sub(n, #pre + 1, #pre + 1) == "_") then
					local wc = d:FindFirstChildOfClass("WeldConstraint")
					if wc then wc.Enabled = false end -- (moved alone, then welded where it now is)
					local rel = piv:ToObjectSpace(d.CFrame)
					d.Size *= near.scale
					d.CFrame = piv * CFrame.new(rel.Position * near.scale) * rel.Rotation
					if wc then wc.Enabled = true end
					break
				end
			end
		end
	end
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then d.CastShadow = false; d.CanQuery = false; d.CanTouch = false end
	end
	-- your wrap from the loadout screen (before the hands go on, so it never paints your arms)
	local wrId, wrMode = WeaponModels.wrapFor(game:GetService("Players").LocalPlayer, wid)
	if wrId then WeaponModels.wrap(m, wrId, wrMode) end
	-- the moving pieces go onto their own welds before the hands exist (the hands never ride a twirl)
	VM.parts = GunParts.attach(m, root, k, w.mdl and w.mdl.parts)
	fillOn(m, root)
	-- your hat on it, riding the piece under it (after the moving pieces are on their welds; never painted by a wrap)
	GunHats.attach(m, wid, GunHats.hatFor(game:GetService("Players").LocalPlayer, wid), k)
	hands(m, root)
	if wid == "katana" then WeaponModels.setKatana(m, kat, k) end
	-- the needle turns round its pivot (Welds we drive) instead of being glued
	for _, n in m:GetChildren() do
		if not n:IsA("BasePart") or n.Name ~= "needle" then continue end
		local pv = n:GetAttribute("Pivot")
		local pivot = if typeof(pv) == "Vector3" then pv * k else Vector3.new(-0.041, 0.03, -0.05) * k
		local wc = n:FindFirstChildOfClass("WeldConstraint")
		if wc then wc:Destroy() end
		hubCF = CFrame.new(pivot)
		local rel = hubCF:ToObjectSpace(root.CFrame:ToObjectSpace(n.CFrame))
		local wd = Instance.new("Weld")
		wd.Part0 = root; wd.Part1 = n; wd.C0 = hubCF; wd.C1 = rel:Inverse(); wd.Parent = n
		table.insert(needles, wd)
	end
	for _, d in m:GetChildren() do if d:IsA("BasePart") and (d.Name == "vent" or string.find(string.lower(d.Name), "vents", 1, true)) then table.insert(vents, d) end end
	m.Parent = camera
	VM.model = m
	swap = 0.2
	follow = nil
	VM.play(if wid == "katana" then "draw_katana" elseif w.draw and Anims[w.draw] then w.draw else "draw_gun")
end

function VM.attachment(name: string): Vector3?
	local m = VM.model
	local a = m and m.PrimaryPart and m.PrimaryPart:FindFirstChild(name) :: Attachment?
	return a and a.WorldPosition
end

export type Ctx = {
	aim: number, speed: number, sprint: boolean, slide: boolean, grounded: boolean, hp: number, firedT: number, slipping: boolean, now: number, sight: Vector3?,
	ammo: number?, reloading: boolean?, -- (for the moving pieces: the belt, a locked-back slide, fallen hammers)
	hidden: boolean?, -- (the viewmodel is hidden this frame: the fill light goes out)
}

function VM.update(dt: number, c: Ctx)
	local m = VM.model
	local w = Weapons.list[VM.wid]
	if not m or not m.PrimaryPart or not w or not w.vm then return end
	-- hit-stop: the clip's clock stops (melee hits and parries)
	local adt = dt
	if VM.hitStop > 0 then VM.hitStop -= dt; adt = 0 end
	if clip then
		clip.t += adt * (clip.rate or 1)
		local a = Anims[clip.name]
		for i, ev in a.events do
			if not clip.fired[i] and clip.t >= ev[1] then
				clip.fired[i] = true
				if VM.onEvent then VM.onEvent(ev[2]) end
			end
		end
		if clip.t >= a.dur then clip = nil; dropProp() end
	end
	-- the off hand lets go for a plain gun's reload. (the web game animates it fetching the mag; that hand isn't
	-- ported, and a forearm glued to a gun that rolls onto its side sweeps right across the screen. so it leaves the
	-- picture and comes back when the gun is loaded)
	-- (your arms keep it: the off hand does the reload, see offHand above. only the stand-in boxes still hide)
	local off = not armsOn and clip ~= nil and w.mdl ~= nil and string.sub(clip.name, 1, 7) == "reload_"
	if off ~= offGone then
		offGone = off
		local arms = m:FindFirstChild("AvatarArms")
		for _, n in { "LeftHand", "LeftCuff", "LeftSleeve", "LeftLowerArm", "HandFore", "SleeveFore" } do
			local p = (arms and arms:FindFirstChild(n)) or m:FindFirstChild(n)
			if p then p:SetAttribute("Hide", if off then true else nil) end
		end
	end
	-- the pump / bolt / lever a shot queued (not over a reload)
	if follow and c.now >= follow.at then
		local f = follow
		follow = nil
		if not (clip and string.sub(clip.name, 1, 7) == "reload_") then VM.play(f.name) end
	end
	-- springs (240 Hz sub-steps)
	local nSub = math.clamp(math.ceil(dt * 240), 1, 40)
	local h = dt / nSub
	for _ = 1, nSub do
		rec.pv += (-220 * rec.p - 20 * rec.pv) * h; rec.p += rec.pv * h
		rec.rv += (-200 * rec.r - 18 * rec.rv) * h; rec.r += rec.rv * h
		punch.v += (-160 * punch.x - 18 * punch.v) * h; punch.x += punch.v * h
	end
	kick = math.max(0, kick - 6 * dt)
	kickUp = math.max(0, kickUp - 6 * dt)
	swap = math.max(0, swap - 5 * dt)
	local base, rot = w.vm.p, w.vm.r
	local row = look(VM.wid)
	if row and row.shift then base += row.shift * S end -- (where it sits: the Rivals-class layout, holds.json)
	if row and row.tilt then rot += row.tilt end -- (the one-handed guns turned to show their side)
	local px, py, pz = base.X, base.Y - 0.3 * swap * S, base.Z
	local rx, ry, rz = 0, 0, 0
	-- what the gun reads off your body eases in and out (the owner, 18 Nov 2026: "sometimes the weapons vibrate during
	-- match"): on the ground or not flips frame to frame on stairs, kerbs and bumps (a step up, an edge read as air),
	-- sliding and slipping can flick on and off, and the body's speed jolts against walls and other bodies. the bob,
	-- the slide roll and the slip took each flip whole, a jump of the gun every frame
	local e10 = math.min(1, dt * 10)
	feel.ground += ((if c.grounded then 1 else 0) - feel.ground) * math.min(1, dt * 12)
	feel.slide += ((if c.slide then 1 else 0) - feel.slide) * e10
	feel.slip += ((if c.slipping then 1 else 0) - feel.slip) * e10
	feel.speed += (c.speed - feel.speed) * e10
	-- footstep bob: one dip per foot strike
	local spd = feel.speed / S
	local stride = math.min(4.3, 1.2 + 0.29 * spd)
	bobPh += spd * dt / stride * math.pi * feel.ground
	local run = math.clamp((spd - 6) / 4, 0, 1)
	local sprint = math.clamp((spd - 11.5) / 2.5, 0, 1)
	local amp = (0.011 + 0.008 * run + 0.01 * sprint) * feel.ground * math.min(1, spd / 3)
	local dip = -math.abs(math.sin(bobPh))
	px += math.sin(bobPh) * amp * 1.1 * S; py += dip * amp * 1.6 * S; rx += dip * amp * 2.5; rz += math.sin(bobPh) * amp * 3.5
	-- breathing
	breathT += dt
	px += math.sin(breathT * 1.3) * 0.0025 * S; py += math.sin(breathT * 2.1) * 0.0018 * S; rz += math.sin(breathT * 1.1) * 0.008
	-- look sway: the gun trails the mouse
	local look = camera.CFrame.LookVector
	if lastLook then
		local dyaw = math.atan2(-look.X, -look.Z) - math.atan2(-lastLook.X, -lastLook.Z)
		if dyaw > math.pi then dyaw -= 2 * math.pi elseif dyaw < -math.pi then dyaw += 2 * math.pi end
		local dpitch = math.asin(math.clamp(look.Y, -1, 1)) - math.asin(math.clamp(lastLook.Y, -1, 1))
		local tgt = Vector2.new(math.clamp(dyaw * 0.6, -0.07, 0.07), math.clamp(dpitch * 0.6, -0.07, 0.07))
		sway = sway:Lerp(tgt, math.min(1, dt * 9))
	end
	lastLook = look
	px += 0.2 * sway.X * S; py -= 0.12 * sway.Y * S; rx -= 0.8 * sway.Y; ry += 1.3 * sway.X; rz += 0.6 * sway.X
	-- run tilt / slide roll
	runK += ((if c.sprint and feel.ground > 0.5 and c.aim < 0.1 then 1 else 0) - runK) * math.min(1, dt * 8)
	py -= 0.03 * runK * S; rx -= 0.25 * runK; ry += 0.35 * runK; rz += 0.2 * runK
	rz += 0.3 * feel.slide
	-- slipping on marbles: the gun flung up, then wobbling
	if feel.slip > 0.001 then
		rx += (0.85 * 0.5 + math.sin(breathT * 9 * 2 * math.pi) * 0.12) * feel.slip
		rz += (0.5 * 0.5 + math.sin(breathT * 14 * 2 * math.pi) * 0.1) * feel.slip
	end
	-- the clip (draw / swing / parry / reload / stagger)
	local cp, crot: CFrame? = Vector3.zero, nil
	if clip then
		cp, crot = VM.sample(clip.name, clip.t, rot)
	end
	-- aim down sights: blend to the sight on the screen's centre, rotation to none
	local ra = 1 - c.aim * 0.6
	local pos = Vector3.new(px, py, pz) + cp
	local ads = c.sight
	if ads and c.aim > 0 then
		local e = c.aim * c.aim * (3 - 2 * c.aim)
		pos = pos:Lerp(ads, e)
		rx, ry, rz = rx * (1 - e), ry * (1 - e), rz * (1 - e)
	end
	pos += Vector3.new(rec.p.X * ra, rec.p.Y * (1 - c.aim * 0.3), (kick * 0.04 * S + rec.p.Z) * ra)
	local baseRot = crot or CFrame.fromEulerAnglesXYZ(rot.X, rot.Y, rot.Z)
	if ads and c.aim > 0 and not crot then baseRot = CFrame.fromEulerAnglesXYZ(rot.X, rot.Y, rot.Z):Lerp(CFrame.identity, c.aim) end
	if VM.wid == "katana" then
		local fr, fp = katanaFix(if clip then clip.name else nil, if clip then clip.t else 0)
		baseRot *= fr
		pos += fp * S
	end
	local jig = CFrame.fromEulerAnglesXYZ(rx + (kickUp * 0.12 + rec.r.X) * ra, ry, rz + rec.r.Z * ra)
	m.PrimaryPart.CFrame = camera.CFrame * CFrame.new(pos) * jig * baseRot
	-- the reload props are models of their own, not part of this gun: with the gun hidden (third person, a menu, the
	-- scope) they go too, or the jerry can / marble bag hung where the hidden gun is, at the camera, behind you
	if c.hidden then dropProp() else VM.props(m.PrimaryPart.CFrame) end
	GunHats.aim(m, c.aim, clip and clip.name) -- (the hat steps out of the sight picture while you aim, like the web game)
	-- so do a skin's wings, horns and crowns (after Arsenal has set each part's hidden-or-not for this frame)
	if #adsHide > 0 then
		local f = c.aim * c.aim * (3 - 2 * c.aim)
		for _, d in adsHide do d.LocalTransparencyModifier = math.max(d.LocalTransparencyModifier, f) end
	end
	-- the fill light: up and left of the gun's middle in camera space, aimed at it, stopping short of the world
	if fill then
		fill.light.Enabled = not c.hidden
		if not c.hidden then
			local mid = m.PrimaryPart.CFrame:PointToWorldSpace(fill.mid)
			local aim = CFrame.lookAt(mid + camera.CFrame:VectorToWorldSpace(FILL.dir * fill.away), mid)
			fill.at.WorldCFrame = aim
			local want = fillReach(aim.Position, aim, fill.full)
			-- (pulled in at once, let out over a moment: no flicker along a wall's edge)
			fill.reach = if want < fill.reach then want else fill.reach + (want - fill.reach) * math.min(1, dt * 10)
			fill.light.Range = math.max(fill.reach, 0.05)
		end
	end
	if VM.parts then
		GunParts.step(VM.parts, dt, {
			clip = if clip then clip.name else nil, t = if clip then clip.t else 0, anims = Anims,
			ammo = c.ammo or (w.mag or 0), mag = w.mag or 0, reloading = c.reloading == true, now = c.now, firedT = c.firedT,
		}, w)
	end
	-- your arms, last: they read where the magazine, the pump and the props are this frame
	if armsOn then
		local to, mix, under = offHand(m, m.PrimaryPart)
		local hook = VM.offHook
		if hook then
			local f2, m2, u2 = hook()
			if f2 and m2 > 0 then
				if to and mix > 0 then to, mix = to:Lerp(f2, m2), 1 else to, mix = f2, m2 end
				if m2 > 0.5 then under = u2 end
			end
		end
		placeLoader(m.PrimaryPart, to, mix, c.hidden)
		AvatarArms.override(m, "Left", to, mix, under)
		AvatarArms.aim(m, camera.CFrame)
	end
	-- the Redline's tachometer + vents (from your HP; it bangs off the limiter when it's in the red and firing)
	if VM.wid == "redline" then
		local tk = Weapons.tacho(c.hp)
		local tgt = -2.3 + 4.6 * tk
		if tk > 0.85 and c.now - c.firedT < 0.2 then tgt += math.sin(c.now * 1000 * 0.08) * 0.12 end
		if clip and clip.name == "reload_redline" then -- the rev: forced into the red, wobbles, back
			local t = clip.t
			local f = if t < 1.3 then 0 elseif t < 1.42 then (t - 1.3) / 0.12 elseif t < 1.56 then 1 elseif t < 1.76 then 1 - (t - 1.56) / 0.2 else 0
			tgt += (2.3 - tgt) * f + (if t > 1.46 and t < 1.56 then math.sin(t * 90) * 0.15 else 0)
		end
		needleAng += (tgt - needleAng) * math.min(1, dt * 12)
		for _, nw in needles do nw.C0 = hubCF * CFrame.Angles(needleAng, 0, 0) end
		local col = Color3.new(0.25 + 0.75 * tk, 0.04 + 0.3 * tk * tk, 0.02 + (if c.now - c.firedT < 0.2 then 0.15 * tk else 0))
		for _, v in vents do v.Color = col end
	end
end

-- the reload props, held by your off hand (timings from roblox/docs/WEAPONS.md, reloads.js): the Redline's red jerry
-- can rises at 0.2 s, tips into the gun 0.36-1.0 s (three glugs), goes by 1.26 s; the marble bag comes over the jar,
-- pours 0.66-1.18 s, then goes
local function smooth(u: number): number u = math.clamp(u, 0, 1); return u * u * (3 - 2 * u) end
function VM.props(gun: CFrame)
	if not clip then return end
	local t = clip.t
	if clip.name == "reload_redline" then
		if t < 0.2 or t > 1.26 then if prop then prop:Destroy(); prop = nil end return end
		if not prop then prop = Fx.prop("p_jerrycan", Vector3.new(0.035, 0.11, 0.09) * S * SIZE, Color3.fromRGB(200, 20, 15)) end
		local inn = smooth((t - 0.2) / 0.16) * (1 - smooth((t - 1.0) / 0.26))
		local tip = if t < 0.36 then 0 elseif t < 1.0 then smooth((t - 0.36) / 0.2) else 1 - smooth((t - 1.0) / 0.2)
		local wob = if t > 0.45 and t < 1.0 then math.sin(t * 30) * 0.05 else 0
		local at = gun * CFrame.new(Vector3.new(-0.05, 0.03 + 0.09 * inn, -0.06) * k) * CFrame.new(0, -0.25 * S * (1 - inn), 0)
		prop:PivotTo(at * CFrame.Angles(0, 0, -1.6 * tip + wob))
	elseif clip.name == "reload_marbles" then
		if t < 0.4 or t > 1.35 then if prop then prop:Destroy(); prop = nil end return end
		if not prop then prop = Fx.prop("p_marblebag", Vector3.new(0.09, 0.12, 0.09) * S * SIZE, Color3.fromRGB(230, 90, 25)) end
		local inn = smooth((t - 0.4) / 0.2) * (1 - smooth((t - 1.2) / 0.15))
		local pour = if t > 0.6 and t < 1.2 then 1 else 0
		local jig = if pour > 0 then math.abs(math.sin((t - 0.66) / 0.12 * math.pi)) * 0.25 else 0
		local at = gun * CFrame.new(Vector3.new(0, 0.2, -0.045) * k) * CFrame.new(0, -0.3 * S * (1 - inn), 0) -- (a touch behind the jar: its lid opens forward)
		prop:PivotTo(at * CFrame.Angles(0, 0, 2.6 * smooth((t - 0.55) / 0.12) * (1 - smooth((t - 1.18) / 0.1)) + jig))
	end
end

-- a new hat (the loadout screen): rebuild what's in your hands with it, as a new wrap does (Arsenal, "Wraps")
local function rebuildHeld()
	if VM.model and VM.wid ~= "" and VM.wid ~= "shredder" then
		local kat = localPlayer:GetAttribute("Kat")
		VM.set(VM.wid, if type(kat) == "number" then kat else 0)
	end
end
-- a new skin: the same (another body in your hands)
localPlayer:GetAttributeChangedSignal("Skins"):Connect(rebuildHeld)
localPlayer:GetAttributeChangedSignal("Hats"):Connect(function()
	if VM.model and VM.wid ~= "" and VM.wid ~= "shredder" then
		local kat = localPlayer:GetAttribute("Kat")
		VM.set(VM.wid, if type(kat) == "number" then kat else 0)
	end
end)

-- the katana grew (or reset): restretch
function VM.setKatana(n: number)
	if VM.wid == "katana" and VM.model then WeaponModels.setKatana(VM.model, n, k) end
end

-- the aim's zoom narrows the camera; the gun is pushed back by as much, so zooming in never makes it bigger (Rivals and
-- Valorant draw the gun with a view of its own: aimed, it stays small and low, most of the screen clear)
local function unzoom(): number
	local b = LookPlayer:GetAttribute("BaseFov")
	local base = if type(b) == "number" then b else 70
	local cur = camera.FieldOfView
	if cur >= base - 0.01 or cur < 1 then return 1 end
	return math.tan(math.rad(base) / 2) / math.tan(math.rad(cur) / 2)
end

-- where the sight sits while aiming (camera space, studs): on the screen's centre line (public/js/weapons.js adsPose),
-- 0.17 m + the weapon's aimZ from your eye (fitted to Rivals' aimed sizes, tools/roblox/hold_screen.py --ads) and the
-- zoom's push on top. the aim line: the skin's own, else the weapon's (Holds ads.sight: where the gun's Sight spot is
-- blocked, the Redline's deck, Half a Shotgun's hinge), else the Sight spot
function VM.adsPos(wid: string): Vector3?
	local w = Weapons.list[wid]
	if not w or not w.vm or not w.ads then return nil end
	local s = w.vm.s * sizeOf(wid)
	local a, sk = adsOf(wid)
	local az = (sk and sk.aimZ) or (a and a.aimZ) or 0
	local back = (0.17 + az) * unzoom() -- (the sight's distance from your eye, metres)
	local sight = (sk and sk.sight) or (a and a.sight) or (w.mdl and w.mdl.sight)
	if sight then return Vector3.new(0, -sight.Y * s, -back - sight.Z * s) * S end
	return Vector3.new(0.06, math.min(-0.1, -0.03 - 0.1479 * s), -back - 0.13) * S -- no sights: under and right of the middle
end

return VM
