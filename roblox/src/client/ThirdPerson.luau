--!strict
-- THIRD PERSON (16 Nov 2026, the owner: "can the character aim down gun outside of scopes in like in 3rd person
-- animations for weapons"). every character holding a weapon handles it with its own Roblox body: yours in third
-- person (V), and everyone's as other players see them. all of it is animated on each client, every frame, after the
-- walk / run animation and the crouch poses (CrouchPoses.client calls TP.step at the end of its own pass):
--   * THE GUN: each client builds its own copy of the gun a character holds (the same model, skin, wrap and hat as the
--     server's HeldWeapon, which is hidden here), sized to that avatar's arms (TP.T.scale: the server's 4.5 studs a
--     metre made a rifle longer than a slim avatar is tall, and no arm could reach its handguard), and welds it to the
--     chest where the stance puts it: at the hip, or up at the eye with the head down the sights (ADS: every gun,
--     scoped or not), pointing where the player looks
--   * THE BODY: the waist turns the chest into the stance (bladed for a rifle, the gun arm forward for a pistol) and
--     takes part of the look pitch; the neck takes the rest, so the head looks where the gun points (cheek down on the
--     stock while aiming). the walk animation's sway is taken out of the upper body, so the gun stays steady
--   * THE HANDS: the avatar's own hands (never a custom model), put on the hold table's grip spots (Holds.luau, the
--     same spots first person uses) by a two-bone IK solved from that avatar's own rig points (shoulder, elbow, wrist
--     and the hand's grip spot), so a wide, a slim or a tall body all grip the same gun. (Roblox's IKControl solves
--     during the animation step, before the crouch poses and this pass bend the spine, so its hands slid off the gun
--     whenever the chest moved; this solve runs after them, in the chest's own space, and lands exactly)
--   * FIRE: a kick per shot from the gun's own recoil row (TP.T.kick of first person's), the slide / cylinder /
--     hammer move; RELOAD: the gun goes through its first-person reload clip, its moving pieces move (GunParts) and the
--     off hand goes to the magazine, the pump, the cylinder or the shells; the pump / bolt / lever after a shot;
--     SPRINT: the gun comes down across the body; the KATANA has its own stance, two slashes, the guard and the draw;
--     ITEMS: the left hand throws (frag, smoke, duck, calculator) or holds the item up (the rest)
--   * THE NETWORK: your client sends where you look (pitch, a yaw offset) and two flags (aiming, reloading), at most
--     about 12 times a second; ThirdPersonRelay (server) checks it and puts it on your character as the "TP"
--     attribute (Vector3: pitch, yaw, flags). shots ("Shot"), swings and guards ("Fx") and items ("ItemFx") already
--     reach every client
-- tuning lives in TP.T; a Play test can change any of it live through this module's "Tune" attribute (JSON, merged
-- into TP.T). test rigs: any model tagged "TPRig" with a "TPWeapon" attribute is posed like a player (docs:
-- roblox/docs/THIRD-PERSON.md)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local CollectionService = game:GetService("CollectionService")
local HttpService = game:GetService("HttpService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local WeaponModels = require(Shared:WaitForChild("WeaponModels"))
local GunHats = require(Shared:WaitForChild("GunHats"))
local Holds = require(Shared:WaitForChild("Holds")) :: any
local AvatarArms = require(Shared:WaitForChild("AvatarArms")) -- (the claw's nails and cuff fitted onto a real hand)
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Anims = require(Shared:WaitForChild("Anims")) :: any
for name, a in require(Shared:WaitForChild("Reloads")) :: any do
	if not Anims[name] then Anims[name] = a end
end
local GunParts = require(script.Parent:WaitForChild("GunParts"))
local Binds = require(script.Parent:WaitForChild("Binds")) :: any -- (the crouch, held or toggled: Settings)
local Keys = require(script.Parent:WaitForChild("Keys")) -- (C held: a keyboard, or the phone's SLIDE)
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
-- (the sounds, for someone else's reload: found when first needed, so this module never waits on them)
local SfxM: any = nil
local function sfx(): any
	if SfxM == nil then
		local m = script.Parent:FindFirstChild("Sfx")
		if m and m:IsA("ModuleScript") then
			local ok, M = pcall(require, m)
			SfxM = if ok then M else false
		end
	end
	return SfxM or nil
end

local TP = {}
local me = Players.LocalPlayer
local camera = workspace.CurrentCamera
local W = Weapons.list :: any
local V = Vector3.new
local CF = CFrame.new
local ANG = CFrame.Angles
local ID = CFrame.identity

-- ------------------------------------------------------------------ tuning (distances in the avatar's arm lengths, u)
TP.T = {
	scale = 1.95, kMin = 2, kMax = 4.5, -- the gun: studs per metre of its file = scale x u, clamped
	size = { katana = 1.3, remote = 1.4 }, -- a weapon's own size on top (a sword read short at the guns' scale; the TV Remote hid in the fist: gun-models, 18 Nov)
	swig = { mouth = V(0, -0.08, -0.85), tip = -2.75, more = 0.8 }, -- the Hot Sauce's swig (owner, 18 Nov: "turned and poured into your mouth", "reach up and over to your mouth"): the cap a little above and in front of the mouth (head sizes from the head's middle; SaucePour.client draws the sauce falling into it), the bottle's tip at the start (radians: the cap back toward the mouth, the base up and out; reached the long way round, up and over) and how much more it tips up over the 3 s swig
	-- (the hold session, 18 Nov 2026) weapons-port's Lasso and cart, from the player's attributes. spin: the coil's fist
	-- over the head from the right shoulder (chest space, u), going round `circle` u, `rev` turns a second, the loop
	-- `loop` u round; pull: that fist on the rope (aim space from the shoulder, u), `lead` u to the other fist along it;
	-- flailR / flailL: a caught one's hands from the shoulders (chest space, u), waving `wave` u at `waveHz`; ride: a
	-- cart rider's free left hand out for balance (aim space from the shoulder, u), leant in `lean` radians
	lasso = { spin = V(0.1, 0.92, -0.05), circle = 0.22, rev = 2.2, loop = 0.75, pull = V(0.12, -0.55, -0.5), lead = 0.3,
		flailR = V(0.4, 0.75, -0.1), flailL = V(-0.4, 0.75, -0.1), wave = 0.28, waveHz = 3, ride = V(-0.9, -0.3, -0.2), lean = 0.18 },
	-- (the hold session, 18 Nov 2026) the Bow's draw (the owner: "the bow draw animtion looks bad!"): the chest turns side
	-- on (twist, radians), the bow goes out on a straight left arm (the arrow's rest `reach` of the arm's reach from the
	-- shoulder, along the aim from the anchor) nearly upright (roll radians: its top away from the face), and the string,
	-- the arrow and the right hand come back to the anchor (aim space from the right eye, u) under the cheek; the right
	-- elbow out behind (poleR, chest space, u). held full it shakes (shake u, over shakeIn s); let go: the string snaps,
	-- the bow kicks (kick u) and rocks (rock rad), the hand stays a moment (follow u), and it comes down after `hold` s.
	-- arrowScale: the nocked arrow's size against the bow's
	bow = { twist = -0.85, anchor = V(-0.02, -0.17, 0.08), reach = 0.96, roll = 0.2, poleR = V(1.1, 0.35, 0.9), poleL = V(-0.5, -1.2, 0.1),
		shake = 0.006, shakeIn = 0.5, kick = 0.05, rock = 0.14, follow = 0.05, hold = 0.22, arrowScale = 0.8 },
	far = 140, -- beyond this many studs from the camera a body is posed every 3rd frame
	kick = 0.55, -- first person's recoil row x this
	clipK = 1.1, -- a first-person clip's camera-space metres x the gun's k
	eye = V(0.15, 0.08, -0.3), -- the right eye against the head's middle, in head sizes
	lowSpeed = 33, -- studs/s on the ground (not aiming, not just fired) that read as a sprint: the gun comes down
	-- per stance. twist / twistAds: the chest's turn (radians, + = to the left); waist: the share of the look pitch
	-- the waist takes; ads: where the rear sight sits from the right eye while aiming (aim space, u); hip: the gun's
	-- move from there at the hip (aim space, u) and hipRot its turn there; cheek: the head's tilt while aiming
	-- (x down, z toward the stock); poleR / poleL: where each elbow points, from its shoulder (chest space, u)
	rifle = { twist = -0.38, twistAds = -0.5, waist = 0.45, ads = V(0.01, -0.05, -0.3), hip = V(0.14, -0.36, 0.12), hipRot = V(-0.04, 0.06, 0.08),
		cheek = V(-0.12, 0, -0.2), poleR = V(0.9, -0.9, 0.7), poleL = V(-0.6, -1.2, -0.2) },
	heavy = { twist = -0.42, twistAds = -0.5, waist = 0.4, ads = V(0.01, -0.06, -0.32), hip = V(0.2, -0.62, 0.2), hipRot = V(-0.02, 0.08, 0.12),
		cheek = V(-0.12, 0, -0.2), poleR = V(1, -0.8, 0.8), poleL = V(-0.5, -1.3, -0.2) },
	pistol = { twist = 0.22, twistAds = 0.38, waist = 0.4, ads = V(0.02, -0.06, -0.62), hip = V(0.08, -0.44, 0.04), hipRot = V(-0.05, 0.1, 0),
		cheek = V(-0.06, 0, -0.12), poleR = V(0.9, -1, 0.3), poleL = V(-0.6, -1.2, -0.2) },
	-- (the hold session, 18 Nov 2026) Lefty & Righty: square on, a pistol out in each hand (the left one the right's
	-- mirror across the chest), elbows out both sides
	akimbo = { twist = 0, twistAds = 0, waist = 0.4, ads = V(0.02, -0.06, -0.62), hip = V(0.12, -0.44, 0.02), hipRot = V(-0.05, 0.08, 0),
		cheek = V(0, 0, 0), poleR = V(0.9, -1, 0.3), poleL = V(-0.9, -1, 0.3) },
	-- (the hold session, 17 Nov 2026) the one-handed melee weapons: low at the right hip, blade forward; never aimed
	melee = { twist = 0.18, twistAds = 0.18, waist = 0.4, ads = V(0.02, -0.06, -0.62), hip = V(0.12, -0.5, 0.1), hipRot = V(-0.1, 0.12, 0),
		cheek = V(0, 0, 0), poleR = V(0.9, -1, 0.3), poleL = V(-0.6, -1.2, -0.2) },
	shredder = { twist = -0.4, twistAds = -0.45, waist = 0.4, ads = V(0.18, -0.5, -0.5), hip = V(0.32, -0.85, -0.3), hipRot = V(0, 0, 0),
		cheek = V(-0.05, 0, -0.08), poleR = V(1, -0.8, 0.8), poleL = V(-0.5, -1.3, -0.2) },
	-- the katana: its hilt's pose against the chest (pos in u from the chest's front, rot = x y z radians), per key
	katana = { twist = -0.15, waist = 0.35, pitchShare = 0.5, poleR = V(0.9, -1, 0.4), poleL = V(-0.8, -1, 0.1), chest = V(0, 0.05, -0.2) },
	-- sprinting: the gun comes down and across, turned about the grip (x down, y left, z roll)
	low = V(-0.62, 0.42, 0.25),
	-- the throw (left hand, from its shoulder in aim space, u) and the item poses (left hand, "S" = from the left
	-- shoulder, "E" = from the eye; aim space, u)
	throw = {
		{ t = 0, p = V(0.15, -0.35, -0.6) }, { t = 0.14, p = V(-0.12, 0.55, 0.4) }, { t = 0.26, p = V(0.15, 0.4, -0.95) },
		{ t = 0.46, p = V(0.35, -0.2, -0.7) }, { t = 0.7, p = V(0.35, -0.3, -0.65) },
	},
	release = 0.24,
	use = {
		medkit = { from = "S", p = V(0.42, -0.32, -0.5), dur = 1.0 }, nvg = { from = "E", p = V(-0.12, 0.12, -0.12), dur = 0.7 },
		camera = { from = "E", p = V(-0.08, -0.06, -0.42), dur = 0.9 }, radar = { from = "S", p = V(0.3, 0.15, -0.95), dur = 1.0 },
		laptop = { from = "S", p = V(0.5, -0.32, -0.62), dur = 1.1 }, popper = { from = "S", p = V(0.25, 0.85, -0.45), dur = 0.8 },
		reverse = { from = "S", p = V(0.35, 0.3, -0.85), dur = 0.9 }, bubble = { from = "S", p = V(0.35, -0.15, -0.85), dur = 0.8 },
		wand = { from = "E", p = V(-0.05, -0.12, -0.42), dur = 0.9 },
	},
}

-- the katana's moves (the hilt's pose against the chest: p in u, r = x y z radians, e = ease into the key)
local KAT_REST = { p = V(0.3, -0.32, -0.42), r = V(0.62, 0.22, -0.08) }
local KAT = {
	swing = { dur = 0.5, keys = {
		{ t = 0, p = KAT_REST.p, r = KAT_REST.r },
		{ t = 0.07, p = V(0.42, 0.3, -0.1), r = V(1.95, -0.35, 0.55), e = "smooth" },
		{ t = 0.12, p = V(0.12, 0.02, -0.62), r = V(0.25, 0.55, -0.85), e = "linear" },
		{ t = 0.17, p = V(-0.18, -0.34, -0.44), r = V(-0.55, 1.05, -1.25), e = "snap" },
		{ t = 0.28, p = V(-0.2, -0.38, -0.42), r = V(-0.62, 1.12, -1.3), e = "smooth" },
		{ t = 0.5, p = KAT_REST.p, r = KAT_REST.r, e = "smooth" },
	} },
	swing2 = { dur = 0.5, keys = {
		{ t = 0, p = KAT_REST.p, r = KAT_REST.r },
		{ t = 0.07, p = V(-0.28, 0.3, -0.15), r = V(1.95, 0.45, -0.6), e = "smooth" },
		{ t = 0.12, p = V(0.02, 0.02, -0.65), r = V(0.25, -0.45, 0.85), e = "linear" },
		{ t = 0.17, p = V(0.38, -0.34, -0.42), r = V(-0.55, -0.95, 1.25), e = "snap" },
		{ t = 0.28, p = V(0.4, -0.38, -0.4), r = V(-0.62, -1.0, 1.3), e = "smooth" },
		{ t = 0.5, p = KAT_REST.p, r = KAT_REST.r, e = "smooth" },
	} },
	guard = { dur = 0.56, keys = {
		{ t = 0, p = KAT_REST.p, r = KAT_REST.r },
		{ t = 0.05, p = V(0.08, 0.42, -0.55), r = V(0.12, 1.5, 0.05), e = "snap" },
		{ t = 0.34, p = V(0.08, 0.4, -0.55), r = V(0.12, 1.48, 0.05), e = "linear" },
		{ t = 0.56, p = KAT_REST.p, r = KAT_REST.r, e = "smooth" },
	} },
	draw = { dur = 0.45, keys = {
		{ t = 0, p = V(-0.35, -0.55, 0.05), r = V(-1.1, 2.7, 0) },
		{ t = 0.18, p = V(0.05, -0.12, -0.45), r = V(0.25, 0.95, 0.35), e = "smooth" },
		{ t = 0.45, p = KAT_REST.p, r = KAT_REST.r, e = "smooth" },
	} },
	stagger = { dur = 0.62, keys = {
		{ t = 0, p = KAT_REST.p, r = KAT_REST.r },
		{ t = 0.07, p = V(0.45, 0.3, -0.15), r = V(1.45, -0.3, 0.55), e = "snap" },
		{ t = 0.32, p = V(0.4, 0.22, -0.2), r = V(1.2, -0.2, 0.45), e = "smooth" },
		{ t = 0.62, p = KAT_REST.p, r = KAT_REST.r, e = "smooth" },
	} },
}
TP.KAT, TP.KAT_REST = KAT, KAT_REST

local ONE_HAND = { pistol = true, revolver = true, sawnoff = true, taser = true, cig = true, remote = true, slipper = true, cards = true, lasso = true, akimbo = true, bloodcross = true } -- (Taser, Hot Sauce, TV Remote, Slipper, Card Deck, Lasso, Lefty & Righty, the Blood Cross's finger-gun hand: 18 Nov)
-- a weapon held in another class's stance (its moves still its own class's: the Scythe swings as a melee weapon, held low
-- with both hands like the LMG: 18 Nov 2026)
local STANCE: { [string]: string } = { scythe = "heavy", akimbo = "akimbo" }
local function classOf(wid: string): string
	if wid == "katana" then return "katana" end
	-- (the hold session, 17 Nov 2026) every other melee weapon is one-handed: the Knife (its Spoon skin), the Zombie
	-- Claw. their slashes and the stab are the first-person clips (swing_<id>, swing_<id>2, stab_<id>), round the grip
	if W[wid] and W[wid].kind == "melee" then return "melee" end
	if wid == "shredder" then return "shredder" end
	if ONE_HAND[wid] then return "pistol" end
	if wid == "lmg" or wid == "minigun" or wid == "blower" then return "heavy" end -- (the Minigun, the Leaf Blower: held low, 18 Nov 2026)
	return "rifle"
end
TP.classOf = classOf

-- "Tune" (JSON) merged into TP.T: numbers, and {x,y,z} arrays where TP.T has a Vector3
local function merge(dst: any, src: any)
	for key, v in src do
		local cur = dst[key]
		if typeof(cur) == "Vector3" and type(v) == "table" then dst[key] = V(v[1] or 0, v[2] or 0, v[3] or 0)
		elseif type(cur) == "table" and type(v) == "table" then merge(cur, v)
		elseif type(v) == "number" or type(v) == "string" or type(v) == "boolean" then dst[key] = v end
	end
end
local function retune()
	local s = script:GetAttribute("Tune")
	if type(s) ~= "string" or s == "" then return end
	local ok, t = pcall(function() return HttpService:JSONDecode(s) end)
	if ok and type(t) == "table" then merge(TP.T, t) end
end
script:GetAttributeChangedSignal("Tune"):Connect(retune)
retune()

-- ------------------------------------------------------------------ small maths
local EASE = {
	linear = function(u: number) return u end,
	smooth = function(u: number) return u * u * (3 - 2 * u) end,
	snap = function(u: number) return 1 - (1 - u) ^ 3 end,
	["in"] = function(u: number) return u * u * u end,
	back = function(u: number) local c = 1.9; return 1 + (c + 1) * (u - 1) ^ 3 + c * (u - 1) ^ 2 end,
}
local function smoothstep(u: number): number u = math.clamp(u, 0, 1); return u * u * (3 - 2 * u) end
local function v3(a: { number }): Vector3 return V(a[1], a[2], a[3]) end
local function eul(v: Vector3): CFrame return CFrame.fromEulerAnglesXYZ(v.X, v.Y, v.Z) end
-- a frame seen in a mirror across the chest's middle (x -> -x): Lefty & Righty's left gun from the right one
local function mirrorX(cf: CFrame): CFrame
	local x, y, z, r00, r01, r02, r10, r11, r12, r20, r21, r22 = cf:GetComponents()
	return CFrame.new(-x, y, z, r00, -r01, -r02, -r10, r11, r12, -r20, r21, r22)
end
local function wrapAng(a: number): number
	a = (a + math.pi) % (2 * math.pi) - math.pi
	return a
end
-- a frame whose Y is y exactly and whose X is x squared to it
local function basis(x: Vector3, y: Vector3): CFrame
	local xx = x - y * x:Dot(y)
	if xx.Magnitude < 1e-4 then xx = (if math.abs(y.Z) < 0.9 then Vector3.zAxis else Vector3.xAxis):Cross(y) end
	xx = xx.Unit
	return CFrame.fromMatrix(Vector3.zero, xx, y, xx:Cross(y))
end

-- a first-person clip at t (Anims / Reloads): the offset (metres, camera space) and the turn
local function sampleClip(name: string, t: number): (Vector3, CFrame)
	local a = Anims[name]
	local keys = a.keys
	local k0, k1 = keys[1], keys[#keys]
	if t <= keys[1].t then k1 = keys[1] end
	for i = 1, #keys - 1 do
		if t >= keys[i].t and t < keys[i + 1].t then k0, k1 = keys[i], keys[i + 1]; break end
	end
	local span = k1.t - k0.t
	local u = if span > 0 then math.clamp((t - k0.t) / span, 0, 1) else 1
	local e = (EASE :: any)[k1.e or "smooth"](u)
	local p = v3(k0.p):Lerp(v3(k1.p), e)
	local r = v3(k0.r):Lerp(v3(k1.r), e)
	return p, eul(r)
end
-- one of our own key lists (the katana, the throw)
local function sampleKeys(keys: { any }, t: number): (Vector3, Vector3?)
	local k0, k1 = keys[1], keys[#keys]
	if t <= keys[1].t then return keys[1].p, keys[1].r end
	if t >= k1.t then return k1.p, k1.r end
	for i = 1, #keys - 1 do
		if t >= keys[i].t and t < keys[i + 1].t then k0, k1 = keys[i], keys[i + 1]; break end
	end
	local span = k1.t - k0.t
	local u = if span > 0 then math.clamp((t - k0.t) / span, 0, 1) else 1
	local e = (EASE :: any)[k1.e or "smooth"](u)
	local r = if k0.r and k1.r then (k0.r :: Vector3):Lerp(k1.r, e) else nil
	return (k0.p :: Vector3):Lerp(k1.p, e), r
end
-- a channel of a first-person clip (GunParts' sampleCh): when its pieces start and stop moving
local function chWindow(name: string?, ch: string): (number?, number?)
	local a = name and Anims[name]
	local k = a and a.ch and a.ch[ch]
	if not k or #k < 3 then return nil, nil end
	return k[2][1], k[#k][1]
end

-- ------------------------------------------------------------------ the rig: joints and arms of one body
type Joint = { j: any, c0: CFrame, c1: CFrame }
type Arm = {
	side: string, S: Vector3, as: Vector3, ae: Vector3, L1: number, B1inv: CFrame,
	el: Vector3, wl: Vector3, L2: number, B2inv: CFrame, wh: Vector3,
	grip: CFrame, gripInv: CFrame, mid: CFrame, thick: number, long: number, reach: number,
	sh: Joint, elb: Joint, wr: Joint,
}
type Grab = { node: string, piece: any, rel: CFrame, ch: string }
type Rig = {
	ch: Model, hum: Humanoid, root: BasePart, ut: BasePart, head: BasePart?, isMe: boolean, player: Player?,
	J: { [string]: Joint }, arms: { [string]: Arm }, u: number, Hs: number, nk: Vector3, headC1: CFrame, geomT: number, dirty: boolean,
	src: Instance?, wid: string, cls: string, k: number,
	gun: Model?, groot: BasePart?, weld: Weld?, parts: any, sight: Vector3, gripPt: Vector3, muzzle: Attachment?,
	holdR: CFrame?, holdL: CFrame?, poseR: string?, poseL: string?, turnR: number, turnL: number, ride: Grab?, grab: { [string]: Grab },
	hidden: { [BasePart]: number }, shown: { [BasePart]: number },
	pitch: number, yaw: number, aim: number, low: number, on: number, lastFire: number, flags: number,
	clip: { name: string, t: number, rate: number }?, follow: { name: string, at: number }?,
	kat: { name: string, t: number }?, katAlt: boolean, lastSwing: number,
	rec: { p: Vector3, pv: Vector3, r: Vector3, rv: Vector3 },
	item: { id: string, kind: string, t: number, model: Model? }?,
	leftW: number, frame: number, tool: Tool?, toolFrame: CFrame?, kKat: number,
}
local rigs: { [Model]: Rig } = {}
TP.rigs = rigs

local function isJoint(d: Instance): boolean return d:IsA("Motor6D") or d:IsA("AnimationConstraint") end
local function jointOf(ch: Model, part: string, name: string): Joint?
	local p = ch:FindFirstChild(part)
	local j = p and p:FindFirstChild(name)
	if not j or not isJoint(j) then return nil end
	if j:IsA("Motor6D") then
		local m = j :: Motor6D
		return { j = m, c0 = m.C0, c1 = m.C1 }
	end
	local a = j :: AnimationConstraint
	local a0, a1 = a.Attachment0, a.Attachment1
	if not a0 or not a1 then return nil end
	return { j = a, c0 = a0.CFrame, c1 = a1.CFrame }
end

local function spot(part: BasePart?, name: string): Vector3?
	local a = part and part:FindFirstChild(name)
	return if a and a:IsA("Attachment") then a.Position else nil
end

-- (the hold session, 18 Nov 2026; the owner: "Keep R6 allowed") a blocky R6 body: the Torso is the chest (no waist to
-- turn), the Neck and the RootJoint, and each arm one block on its shoulder. its Arm rows carry what the rest reads
-- (the shoulder, a grip at the arm's end, a reach) with the arm split in two for elbowAt's turn of the hand; the arm
-- itself is aimed by solveArmR6. r.u is an R15 arm's (so the stances' sizes read the same)
local function readBodyR6(r: Rig): boolean
	local ch = r.ch
	local torso = ch:FindFirstChild("Torso") :: BasePart?
	local head = ch:FindFirstChild("Head") :: BasePart?
	local neck = jointOf(ch, "Torso", "Neck")
	local root = jointOf(ch, "HumanoidRootPart", "RootJoint")
	if not torso or not head or not neck or not root then return false end
	local J: { [string]: Joint } = { Root = root, Neck = neck }
	local arms: { [string]: Arm } = {}
	for _, side in { "Right", "Left" } do
		local sh = jointOf(ch, "Torso", side .. " Shoulder")
		local arm = ch:FindFirstChild(side .. " Arm") :: BasePart?
		if not sh or not arm then return false end
		J[side .. "Shoulder"] = sh
		local ga = arm:FindFirstChild(side .. "GripAttachment")
		local grip = if ga and ga:IsA("Attachment") then ga.CFrame else ANG(-math.pi / 2, 0, 0) + V(0, -arm.Size.Y / 2, 0)
		local as = sh.c1.Position -- (the shoulder, in the arm's own space)
		local len = (grip.Position - as).Magnitude
		arms[side] = {
			side = side, S = sh.c0.Position, as = as, ae = as, L1 = len * 0.55, B1inv = ID,
			el = Vector3.zero, wl = Vector3.zero, L2 = len * 0.45, B2inv = ID,
			wh = grip.Position + V(0, arm.Size.Y * 0.25, 0), -- (no wrist: a spot up the arm from the grip, for handOn's turn)
			grip = grip, gripInv = grip:Inverse(), mid = basis(Vector3.xAxis, Vector3.yAxis), thick = arm.Size.X, long = arm.Size.Y * 0.3,
			reach = len, sh = sh, elb = sh, wr = sh,
		}
	end
	r.J = J
	r.ut, r.head = torso, head
	r.Hs = head.Size.Y
	r.nk = neck.c0.Position
	r.headC1 = neck.c1
	r.arms = arms
	r.u = 1.9
	;(r :: any).r6 = true
	r.geomT = os.clock()
	r.dirty = false
	return true
end

-- read a body's joints and limbs (again whenever its joints change, and every half second: avatars rescale after a spawn)
local function readBody(r: Rig): boolean
	local ch = r.ch
	if not ch:FindFirstChild("UpperTorso") and ch:FindFirstChild("Torso") then return readBodyR6(r) end
	local J: { [string]: Joint } = {}
	for _, n in { { "LowerTorso", "Root" }, { "UpperTorso", "Waist" }, { "Head", "Neck" },
		{ "RightUpperArm", "RightShoulder" }, { "RightLowerArm", "RightElbow" }, { "RightHand", "RightWrist" },
		{ "LeftUpperArm", "LeftShoulder" }, { "LeftLowerArm", "LeftElbow" }, { "LeftHand", "LeftWrist" } } do
		local j = jointOf(ch, n[1], n[2])
		if not j then return false end
		J[n[2]] = j
	end
	r.J = J
	local ut = ch:FindFirstChild("UpperTorso") :: BasePart?
	local head = ch:FindFirstChild("Head") :: BasePart?
	if not ut or not head then return false end
	r.ut, r.head = ut, head
	r.Hs = head.Size.Y
	r.nk = J.Neck.c0.Position
	r.headC1 = J.Neck.c1
	local arms: { [string]: Arm } = {}
	for _, side in { "Right", "Left" } do
		local sh, elb, wr = J[side .. "Shoulder"], J[side .. "Elbow"], J[side .. "Wrist"]
		local hand = ch:FindFirstChild(side .. "Hand") :: BasePart?
		if not hand then return false end
		local as, ae = sh.c1.Position, elb.c0.Position
		local el, wl = elb.c1.Position, wr.c0.Position
		local L1, L2 = (ae - as).Magnitude, (wl - el).Magnitude
		if L1 < 0.05 or L2 < 0.05 then return false end
		local wh = wr.c1.Position
		-- the grip: where a Tool's handle sits in this hand (its Y up the handle), on the hand's own middle along it
		local ga = hand:FindFirstChild(side .. "GripAttachment")
		local grip = if ga and ga:IsA("Attachment") then ga.CFrame.Rotation + ga.Position
			else ANG(-math.pi / 2, 0, 0) + V(0, -hand.Size.Y * 0.2, 0)
		local along = grip.YVector
		grip -= along * grip.Position:Dot(along)
		local y = if wh.Magnitude > 1e-4 then wh.Unit else Vector3.yAxis
		arms[side] = {
			side = side, S = sh.c0.Position, as = as, ae = ae, L1 = L1, B1inv = basis(Vector3.xAxis, (ae - as).Unit):Inverse(),
			el = el, wl = wl, L2 = L2, B2inv = basis(Vector3.xAxis, (wl - el).Unit):Inverse(), wh = wh,
			grip = grip, gripInv = grip:Inverse(), mid = basis(Vector3.xAxis, y), thick = hand.Size.X, long = hand.Size.Y,
			reach = L1 + L2 + (wh - grip.Position).Magnitude * 0.85,
			sh = sh, elb = elb, wr = wr,
		}
	end
	r.arms = arms
	r.u = arms.Right.L1 + arms.Right.L2
	r.geomT = os.clock()
	r.dirty = false
	return true
end

-- ------------------------------------------------------------------ IK
-- where the elbow goes for a wrist at Wp (chest space), bent toward the pole
local function elbowAt(a: Arm, Wp: Vector3, pole: Vector3): (Vector3, Vector3, Vector3)
	local S = a.S
	local d = Wp - S
	local L = d.Magnitude
	local dir = if L > 1e-4 then d / L else V(0, -1, 0)
	local Lc = math.clamp(L, math.abs(a.L1 - a.L2) + 0.01, (a.L1 + a.L2) * 0.999)
	local pv = pole - S
	local up = pv - dir * pv:Dot(dir)
	if up.Magnitude < 1e-4 then up = V(0, 0, 1) - dir * dir.Z end
	if up.Magnitude < 1e-4 then up = Vector3.xAxis end
	up = up.Unit
	local x = (a.L1 * a.L1 - a.L2 * a.L2 + Lc * Lc) / (2 * Lc)
	local h = math.sqrt(math.max(0, a.L1 * a.L1 - x * x))
	return S + dir * x + up * h, S + dir * Lc, up:Cross(dir)
end
-- put the arm's hand at H (chest space): the three joints' Transforms. weight blends from what the animation put there
local function solveArm(a: Arm, H: CFrame, pole: Vector3, weight: number)
	local Wp = H * a.wh
	local E, Wc, nAlt = elbowAt(a, Wp, pole)
	local Hc = H + (Wc - Wp)
	local d1 = (E - a.S).Unit
	local d2 = (Wc - E).Unit
	local n = d1:Cross(d2)
	n = if n.Magnitude > 1e-4 then n.Unit else nAlt.Unit
	local UA = CF(a.S) * (basis(n, d1) * a.B1inv) * CF(-a.as)
	local LA = CF(E) * (basis(n, d2) * a.B2inv) * CF(-a.el)
	local T1 = (a.sh.c0:Inverse() * UA * a.sh.c1).Rotation
	local T2 = (a.elb.c0:Inverse() * UA:Inverse() * LA * a.elb.c1).Rotation
	local T3 = (a.wr.c0:Inverse() * LA:Inverse() * Hc * a.wr.c1).Rotation
	if weight >= 0.999 then
		a.sh.j.Transform = T1; a.elb.j.Transform = T2; a.wr.j.Transform = T3
	else
		a.sh.j.Transform = a.sh.j.Transform:Lerp(T1, weight)
		a.elb.j.Transform = a.elb.j.Transform:Lerp(T2, weight)
		a.wr.j.Transform = a.wr.j.Transform:Lerp(T3, weight)
	end
end
-- (R6) the arm is one block: turned on its shoulder (the least turn from hanging) so the line from the shoulder to its
-- grip points at where the hand should hold (H * grip); it reaches as far as the arm does. whole (a hand that IS the
-- weapon: H is the hand's own frame): the arm's last 0.6 studs are the hand, their middle aimed at H
local function solveArmR6(a: Arm, H: CFrame, weight: number, whole: boolean?)
	local sh = a.sh
	local A0 = sh.c0 * sh.c1:Inverse() -- (the arm hanging, chest space)
	local pt = if whole then a.grip.Position + V(0, 0.3, 0) else a.grip.Position
	local v0 = A0:VectorToWorldSpace(pt - a.as)
	local v1 = (if whole then H.Position else (H * a.grip).Position) - a.S
	if v0.Magnitude < 1e-3 or v1.Magnitude < 1e-3 then return end
	v0, v1 = v0.Unit, v1.Unit
	local axis = v0:Cross(v1)
	local ang = math.acos(math.clamp(v0:Dot(v1), -1, 1))
	local R = if axis.Magnitude > 1e-5 then CFrame.fromAxisAngle(axis.Unit, ang) elseif v0:Dot(v1) < 0 then CFrame.fromAxisAngle(Vector3.xAxis, math.pi) else ID
	local A = CF(a.S) * R * CF(-a.S) * A0
	local T = (sh.c0:Inverse() * A * sh.c1).Rotation
	sh.j.Transform = if weight >= 0.999 then T else sh.j.Transform:Lerp(T, weight)
end
-- the hand on a hold frame F (chest space; its Y along the thing held, through the fist), turned about it until the
-- wrist faces the elbow (AvatarArms' rule); "palm": held from under, the palm up into it
local function handOn(a: Arm, F: CFrame, pose: string?, turn: number, pole: Vector3): CFrame
	if pose == "hand" then return F end -- (the hold session: the hand IS the weapon, the claw; F is the hand's own frame)
	local elbow = elbowAt(a, F.Position, pole)
	if pose == "palm" then
		local to = elbow - F.Position
		local Y = if to.Magnitude > 1e-3 then to.Unit else -F.ZVector
		local nrm = F.YVector
		local P = nrm - Y * nrm:Dot(Y)
		P = if P.Magnitude > 1e-3 then P.Unit else Vector3.yAxis
		local X = if a.side == "Right" then -P else P
		local at = F.Position - P * a.thick * 0.38 - Y * a.long * 0.18
		return CFrame.fromMatrix(at, X, Y, X:Cross(Y)) * a.mid:Inverse()
	end
	local w = a.gripInv * a.wh
	local e = F:PointToObjectSpace(elbow)
	local ang = 0
	if w.X * w.X + w.Z * w.Z > 1e-6 and e.X * e.X + e.Z * e.Z > 1e-6 then ang = math.atan2(e.X, e.Z) - math.atan2(w.X, w.Z) end
	return F * ANG(0, ang + turn, 0) * a.gripInv
end
-- a hold too far for this arm: slide it back along the gun (toward the grip, v) until the hand can reach it
local function within(a: Arm, F: CFrame, v: Vector3, maxSlide: number): CFrame
	local D = F.Position - a.S
	local R = a.reach * 0.97
	if D.Magnitude <= R then return F end
	local b = v:Dot(D)
	local disc = b * b - D:Dot(D) + R * R
	local s = if disc >= 0 then -b - math.sqrt(disc) else -b
	if s < 0 then s = if disc >= 0 then -b + math.sqrt(disc) else 0 end
	return F + v * math.clamp(s, 0, maxSlide)
end

-- ------------------------------------------------------------------ the gun each client builds for a body
local function hideServerGun(r: Rig, src: Instance?)
	if not src or not src:IsA("Model") or src:IsA("Tool") or (r :: any).hiddenSrc == src then return end
	(r :: any).hiddenSrc = src
	local function hide(d: Instance)
		if d:IsA("BasePart") and r.hidden[d] == nil then
			r.hidden[d] = d.Transparency
			d.Transparency = 1
		end
	end
	for _, d in src:GetDescendants() do hide(d) end
	-- (a hat or a piece arriving late)
	local c = src.DescendantAdded:Connect(hide)
	src.Destroying:Connect(function() c:Disconnect() end)
end
local function showServerGun(r: Rig)
	for p, t in r.hidden do if p.Parent then p.Transparency = t end end
	table.clear(r.hidden);
	(r :: any).hiddenSrc = nil
end

local function dropGun(r: Rig)
	if r.gun then r.gun:Destroy() end
	-- (the hold session) the claw's green comes off this body's own hand
	local tint = (r :: any).tint
	if tint then
		(r :: any).tint = nil
		if tint.part.Parent then
			tint.part.Color = tint.color
			if tint.tex and tint.part:IsA("MeshPart") then (tint.part :: MeshPart).TextureID = tint.tex end
		end
	end
	r.gun, r.groot, r.weld, r.parts, r.muzzle = nil, nil, nil, nil, nil
	;(r :: any).gun2 = nil -- (Lefty & Righty's left gun: inside r.gun, gone with it)
	r.holdR, r.holdL, r.ride = nil, nil, nil
	r.grab = {}
	r.clip, r.follow, r.kat = nil, nil, nil
	table.clear(r.shown)
end

local function katOf(r: Rig): number
	local v = if r.player then r.player:GetAttribute("Kat") else r.ch:GetAttribute("TPKat")
	return if type(v) == "number" then v else 0
end

-- the off hand's grabs on the gun's moving pieces: round the lower end of a piece's node (a magazine from below),
-- and the pump (the hand rides it). in the gun's own space, against the piece
local function grabsFor(r: Rig)
	r.ride, r.grab = nil, {}
	local st = r.parts
	if not st then return end
	local function biggest(list: { any }?): any
		local best = nil
		for _, p in list or {} do
			if not best or p.part.Size.Magnitude > best.part.Size.Magnitude then best = p end
		end
		return best
	end
	local pump = biggest(st.nodes.pump)
	if pump and r.holdL then r.ride = { node = "pump", piece = pump, rel = pump.rest:Inverse() * r.holdL, ch = "pump" } end
	for node, ch in { mag = "mag", cylinder = "cyl", hinge = "hinge" } do
		local list = st.nodes[node]
		local main = biggest(list)
		if main and list then
			local lo, hi = Vector3.one * math.huge, -Vector3.one * math.huge
			for _, p in list do
				local h = p.part.Size / 2
				for _, c in { V(h.X, h.Y, h.Z), V(-h.X, h.Y, h.Z), V(h.X, -h.Y, h.Z), V(h.X, h.Y, -h.Z), V(-h.X, -h.Y, h.Z), V(-h.X, h.Y, -h.Z), V(h.X, -h.Y, -h.Z), V(-h.X, -h.Y, -h.Z) } do
					local q = p.rest:PointToWorldSpace(c)
					lo = lo:Min(q); hi = hi:Max(q)
				end
			end
			local at = CF((lo.X + hi.X) / 2, lo.Y + math.min(0.04 * r.k, (hi.Y - lo.Y) * 0.35), (lo.Z + hi.Z) / 2)
			r.grab[node] = { node = node, piece = main, rel = main.rest:Inverse() * at, ch = ch }
		end
	end
end

local function holdFrame(wid: string, side: string, k: number, frame: CFrame?, skin: string?): (CFrame?, string?, number)
	local rows = AvatarArms.rows(wid, skin) -- (the hold session: a skin's own hands, the knife's spoon)
	local row = rows and rows[side]
	if not row then return nil, nil, 0 end
	return (frame or ID) * CF(row.at * k) * eul(row.rot), row.pose, row.turn or 0
end

local function buildGun(r: Rig, wid: string, src: Instance?)
	dropGun(r)
	r.wid, r.cls = wid, classOf(wid)
	if wid == "shredder" then
		-- a Tool: Roblox's own grip weld holds it in the right hand; the hands are placed so it ends up in the stance
		local tool = src :: Tool
		r.tool = tool
		local h = tool:FindFirstChild("Handle") :: BasePart?
		local mz = h and h:FindFirstChild("Muzzle") :: Attachment?
		local hub = tool:FindFirstChild("sh_hub", true) :: BasePart?
		local bell = tool:FindFirstChild("sh_bell2", true) :: BasePart?
		-- (a skin, the Wood Chipper, may not have the hub and the chute: then from the handle to the muzzle, handle's up)
		if h and mz then
			local from = if hub then hub.Position else h.Position
			local axis = (mz.WorldPosition - from).Unit
			local upW = if bell then bell.Position - from else h.CFrame.UpVector
			upW -= axis * axis:Dot(upW)
			if upW.Magnitude < 1e-3 then upW = Vector3.yAxis - axis * axis.Y end
			upW = upW.Unit
			r.toolFrame = CFrame.lookAt(Vector3.zero, h.CFrame:VectorToObjectSpace(axis), h.CFrame:VectorToObjectSpace(upW))
			r.k = 3
			r.holdL, r.poseL, r.turnL = holdFrame("shredder", "Left", 3, r.toolFrame.Rotation)
			r.muzzle = mz
		end
		r.on = 0
		return
	end
	r.tool, r.toolFrame = nil, nil
	local T = TP.T
	r.k = math.clamp(T.scale * r.u * (T.size[wid] or 1), T.kMin, T.kMax * (T.size[wid] or 1))
	local skin = src and src:GetAttribute("Skin")
	local m = WeaponModels.build(wid, r.k, if type(skin) == "string" then skin else nil)
	if not m or not m.PrimaryPart then return end
	m.Name = "TPGun"
	local root = m.PrimaryPart
	if r.player then
		local wrId, wrMode = WeaponModels.wrapFor(r.player, wid)
		if wrId then WeaponModels.wrap(m, wrId, wrMode) end
	end
	local w = W[wid]
	r.parts = GunParts.attach(m, root, r.k, w and w.mdl and w.mdl.parts)
	if r.player then pcall(GunHats.attach, m, wid, GunHats.hatFor(r.player, wid), r.k, nil, GunHats.THIRD) end
	if wid == "katana" then WeaponModels.setKatana(m, katOf(r), r.k); r.kKat = katOf(r) end
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then d.CastShadow = false; d.CanQuery = false; d.CanTouch = false; d.CanCollide = false; d.Massless = true end
	end
	local sa = root:FindFirstChild("Sight") :: Attachment?
	local ga = root:FindFirstChild("Grip") :: Attachment?
	r.gripPt = if ga then ga.Position else Vector3.zero
	r.sight = if sa then sa.Position else r.gripPt + V(0, 0.12 * r.k, 0.02 * r.k)
	r.muzzle = root:FindFirstChild("Muzzle") :: Attachment?
	local sk = if type(skin) == "string" then skin else nil
	r.holdR, r.poseR, r.turnR = holdFrame(wid, "Right", r.k, nil, sk)
	r.holdL, r.poseL, r.turnL = holdFrame(wid, "Left", r.k, nil, sk)
	-- (the hold session) a one-handed gun's left hand waits off screen in first person (away): here the arm keeps its
	-- own pose and only comes to the gun for the reload's grabs below
	local rowL = (AvatarArms.rows(wid, sk) or {}).Left
	if rowL and rowL.away then r.holdL, r.poseL = nil, nil end
	-- (the hold session, 17 Nov 2026) the Zombie Claw: this body's own right hand is the claw. the nails and the cuff
	-- go onto its real shape, and on this client the hand takes the claw's green while it is out (dropGun undoes it)
	if r.poseR == "hand" and r.holdR then
		local hand = (r.ch:FindFirstChild("RightHand") or r.ch:FindFirstChild("Right Arm")) :: BasePart? -- (R6: the arm block)
		if hand then
			local wa = hand:FindFirstChild("RightWristRigAttachment") :: Attachment?
			if hand.Name == "Right Arm" then -- (R6: the arm's last 0.6 studs are the hand: solveArmR6's whole)
				AvatarArms.fitOver(root, r.k, r.holdR, V(hand.Size.X, 0.6, hand.Size.Z), V(0, 0.3, 0))
			else
				AvatarArms.fitOver(root, r.k, r.holdR, hand.Size, if wa then wa.Position else nil)
			end
			local tint = AvatarArms.rows(wid, sk).Right.tint
			if typeof(tint) == "Color3" then
				(r :: any).tint = { part = hand, color = hand.Color, tex = if hand:IsA("MeshPart") then (hand :: MeshPart).TextureID else nil }
				hand.Color = tint
				if hand:IsA("MeshPart") then (hand :: MeshPart).TextureID = "" end
			end
		end
	end
	-- (put at the chest before it goes in: the WeldConstraints holding its pieces and its hat keep whatever offset they
	-- find when they go live, and the chest weld moved only the root: every piece stayed back at the world's origin)
	m:PivotTo(r.ut.CFrame * CF(0, -0.5, -1))
	local wd = Instance.new("Weld")
	wd.Name = "TPWeld"; wd.Part0 = r.ut; wd.Part1 = root; wd.C0 = CF(0, -0.5, -1); wd.Parent = root
	r.gun, r.groot, r.weld = m, root, wd
	-- (the hold session, 18 Nov 2026) Lefty & Righty: a second gun for the left hand, posed as the first one's mirror
	-- across the chest's middle (stepRig); inside the first, so it hides and goes with it
	if w and w.hands == 2 then
		local m2 = WeaponModels.build(wid, r.k, if type(skin) == "string" then skin else nil)
		if m2 and m2.PrimaryPart then
			m2.Name = "TPGun2"
			local root2 = m2.PrimaryPart
			if r.player then
				local wrId, wrMode = WeaponModels.wrapFor(r.player, wid)
				if wrId then WeaponModels.wrap(m2, wrId, wrMode) end
			end
			local parts2 = GunParts.attach(m2, root2, r.k, w.mdl and w.mdl.parts)
			for _, d in m2:GetDescendants() do
				if d:IsA("BasePart") then d.CastShadow = false; d.CanQuery = false; d.CanTouch = false; d.CanCollide = false; d.Massless = true end
			end
			m2:PivotTo(r.ut.CFrame * CF(0, -0.5, -1))
			local wd2 = Instance.new("Weld")
			wd2.Name = "TPWeld2"; wd2.Part0 = r.ut; wd2.Part1 = root2; wd2.C0 = CF(0, -0.5, -1); wd2.Parent = root2
			m2.Parent = m
			;(r :: any).gun2 = { model = m2, weld = wd2, parts = parts2, muzzle = root2:FindFirstChild("Muzzle") }
		end
	end
	local list = {}
	for _, d in m:GetDescendants() do if d:IsA("BasePart") then table.insert(list, d) end end;
	(r :: any).gunParts = list
	grabsFor(r)
	if (r :: any).gun2 then r.grab = {} end -- (Lefty & Righty: the left hand keeps its own gun through a reload)
	m.Parent = r.ch
	r.on = 0
	-- the draw: the gun comes up (the katana from the hip)
	if wid == "katana" then r.kat = { name = "draw", t = 0 }
	else
		local dname = if w and w.draw and Anims[w.draw] then w.draw else "draw_gun"
		r.clip = { name = dname, t = 0, rate = 1 }
	end
end

-- ------------------------------------------------------------------ bodies we pose
local function newRig(ch: Model): Rig?
	local hum = ch:FindFirstChildOfClass("Humanoid")
	local root = ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local ut = ch:FindFirstChild("UpperTorso") or ch:FindFirstChild("Torso") -- (an R6 body's chest is its Torso: readBodyR6)
	if not hum or not root or not ut or not ut:IsA("BasePart") then return nil end
	local r: Rig = {
		ch = ch, hum = hum, root = root, ut = ut :: BasePart, head = nil, isMe = ch == me.Character,
		-- (a test rig or a replay ghost may name its player in TPPlayer: its gun then gets that player's wrap and hat)
		player = Players:GetPlayerFromCharacter(ch) or (if type(ch:GetAttribute("TPPlayer")) == "number" then Players:GetPlayerByUserId(ch:GetAttribute("TPPlayer") :: number) else nil),
		J = {}, arms = {}, u = 1.5, Hs = 1, nk = Vector3.zero, headC1 = ID, geomT = 0, dirty = true,
		src = nil, wid = "", cls = "", k = 3,
		gun = nil, groot = nil, weld = nil, parts = nil, sight = Vector3.zero, gripPt = Vector3.zero, muzzle = nil,
		holdR = nil, holdL = nil, poseR = nil, poseL = nil, turnR = 0, turnL = 0, ride = nil, grab = {}, hidden = {}, shown = {},
		pitch = 0, yaw = 0, aim = 0, low = 0, on = 0, lastFire = -10, flags = 0,
		clip = nil, follow = nil, kat = nil, katAlt = false, lastSwing = -10,
		rec = { p = Vector3.zero, pv = Vector3.zero, r = Vector3.zero, rv = Vector3.zero },
		item = nil, leftW = 0, frame = 0, tool = nil, toolFrame = nil, kKat = 0,
	}
	local function mark(d: Instance) if isJoint(d) then r.dirty = true end end
	ch.DescendantAdded:Connect(mark)
	ch.DescendantRemoving:Connect(mark)
	return r
end

local function release(r: Rig)
	dropGun(r)
	showServerGun(r)
	if r.item and r.item.model then r.item.model:Destroy() end
	r.item = nil
	r.src, r.wid, r.tool = nil, "", nil
	if r.isMe and r.hum.Parent and r.hum:GetAttribute("TPTurned") then r.hum.AutoRotate = true; r.hum:SetAttribute("TPTurned", nil) end
	local rh = r.ch:FindFirstChild("RightHand") or r.ch:FindFirstChild("Right Arm") -- (the Blood Cross's hat spot goes with the weapon: AvatarArms.hatSpot; R6: on the arm)
	local hs = rh and rh:FindFirstChild("HatSpot")
	if hs then hs:Destroy() end
end

-- what a body is holding: the Shredder (a Tool), the server's HeldWeapon, or (a test rig) its TPWeapon attribute
local function sourceOf(ch: Model): (Instance?, string?)
	-- (the owner gone invisible, OwnerDev.server: nobody else draws their gun)
	local owner = Players:GetPlayerFromCharacter(ch)
	if owner and owner ~= Players.LocalPlayer and owner:GetAttribute("DevInvisible") == true then return nil, nil end
	local tool = ch:FindFirstChildOfClass("Tool")
	if tool and tool.Name == "Shredder" then return tool, "shredder" end
	local hw = ch:FindFirstChild("HeldWeapon")
	if hw then
		local wid = hw:GetAttribute("Weapon")
		if type(wid) == "string" and W[wid] then return hw, wid end
	end
	local tw = ch:GetAttribute("TPWeapon")
	if type(tw) == "string" and (W[tw] or tw == "shredder") then return ch, tw end
	return nil, nil
end

local function candidates(): { Model }
	local out = {}
	for _, p in Players:GetPlayers() do
		if p.Character then table.insert(out, p.Character) end
	end
	local d = workspace:FindFirstChild("Dummies")
	if d then for _, m in d:GetChildren() do if m:IsA("Model") then table.insert(out, m) end end end
	for _, m in CollectionService:GetTagged("TPRig") do if m:IsA("Model") then table.insert(out, m) end end
	return out
end

local function rigFor(m: Instance?): Rig?
	if not m or not m:IsA("Model") then return nil end
	return rigs[m]
end
TP.rigFor = rigFor

-- the muzzle of the gun a body holds as everyone sees it (Arsenal's tracers and flashes start here)
function TP.muzzle(m: Instance?, hand: number?): Vector3?
	local r = rigFor(m)
	local g2 = r and (r :: any).gun2
	if hand == 1 and g2 and g2.muzzle and g2.muzzle.Parent then return g2.muzzle.WorldPosition end -- (Lefty's)
	if r and r.muzzle and r.muzzle.Parent and (r.gun or r.tool) then return r.muzzle.WorldPosition end
	return nil
end

-- ------------------------------------------------------------------ events: shots, reloads, swings, items
local function rnd(): number return (if math.random() < 0.5 then -1 else 1) * (0.5 + math.random() * 0.5) end
local function kickRig(r: Rig, wid: string?, fan: boolean?)
	local w = W[wid or r.wid]
	if not w then return end
	local row = w.recoilVM or { back = 0.8, up = 2.5, roll = 1, side = 0.2, punch = 0.01 }
	local m = TP.T.kick * (if fan and w.fan then w.fan.kick else 1) * (1 - 0.4 * r.aim)
	r.rec.pv += V(row.side * rnd(), 0, row.back) * m * r.k / 3
	r.rec.rv += V(row.up, 0, row.roll * rnd()) * m
	r.lastFire = os.clock()
	if r.parts then GunParts.shot(r.parts, w) end
	-- the pump / bolt / lever after the shot, not over a reload
	if w.cycle and Anims[w.cycle.clip] then r.follow = { name = w.cycle.clip, at = os.clock() + w.cycle.at } end
end
local function reloadRig(r: Rig, secs: number?, empty: boolean?)
	local w = W[r.wid]
	if not w or not w.mag then return end
	local name = if Anims["reload_" .. r.wid] then "reload_" .. r.wid else "reload_ar"
	if empty and Anims[name .. "_empty"] then name ..= "_empty" end
	local a = Anims[name]
	if not a then return end
	local s = secs or w.reload or a.dur
	r.follow = nil
	local clip = { name = name, t = 0, rate = if s > 0 then a.dur / s else 1 }
	r.clip = clip
	if not r.isMe then
		-- (the sound session, 17 Nov 2026: "gun fire audio should be proportional to where players are") someone else's
		-- reload is heard at their gun: the mag out now, the mag in 60% through, only a few strides far (Sfx's ROLL)
		local function at(): Vector3 return if r.muzzle and r.muzzle.Parent then r.muzzle.WorldPosition else r.root.Position end
		local Sfx = sfx()
		if Sfx then
			Sfx.play("click", at(), 0.9, 0.8)
			task.delay(s * 0.6, function()
				if r.clip == clip and r.ch.Parent then Sfx.play("reload", at()) end
			end)
		end
	end
end
local function katRig(r: Rig, name: string)
	if r.wid ~= "katana" then return end
	r.kat = { name = name, t = 0 }
end
local function swingRig(r: Rig, alt: boolean?, name: string?)
	local now = os.clock()
	local a = if alt == nil then (now - r.lastSwing < 0.75 and not r.katAlt) else alt
	r.katAlt = a
	r.lastSwing = now
	-- (the hold session) a melee weapon plays its own first-person clip: the slash (every other one the backhand) or
	-- the one named (the knife's stab)
	if r.cls == "melee" then
		local n = name or ("swing_" .. r.wid .. (if a then "2" else ""))
		if not Anims[n] then n = "swing_" .. r.wid end
		if Anims[n] then r.clip = { name = n, t = 0, rate = 1 } end
		return
	end
	katRig(r, if a then "swing2" else "swing")
end
local function itemRig(r: Rig, id: string, kind: string)
	if r.item and r.item.model then r.item.model:Destroy() end
	r.item = { id = id, kind = kind, t = 0, model = nil }
end

-- your own weapon code (Arsenal) tells us what you do the moment you do it
local mine = { aim = 0, sprint = false, reloadT = -10, reloadDur = 0, empty = false, ammo = nil :: number?, draw = nil :: number? }
function TP.mine(aim: number, sprint: boolean?, ammo: number?, draw: number?)
	mine.aim = aim
	mine.sprint = sprint == true
	mine.ammo = ammo
	mine.draw = draw -- (the Bow drawn, 0..1, while you draw it: Arsenal's minigun.bowDraw())
end
function TP.aiming(): number return mine.aim end -- (how far you're aimed in, 0 to 1: the shoulder camera comes in with it)
local function myRig(): Rig? return rigFor(me.Character) end
function TP.fired(wid: string, fan: boolean?)
	local r = myRig()
	if r then kickRig(r, wid, fan) end
end
function TP.reload(wid: string, secs: number, empty: boolean?)
	mine.reloadT, mine.reloadDur, mine.empty = os.clock(), secs, empty == true
	local r = myRig()
	if r and r.wid == wid then reloadRig(r, secs, empty) end
end
function TP.cancelReload()
	mine.reloadT = -10
	local r = myRig()
	if r and r.clip and string.sub(r.clip.name, 1, 7) == "reload_" then r.clip = nil end
end
function TP.swing(alt: boolean, name: string?) local r = myRig(); if r then swingRig(r, alt, name) end end -- (name: a melee clip, the knife's stab)
function TP.parry() local r = myRig(); if r then katRig(r, "guard") end end
-- (the katana's held guard, 18 Nov 2026) a body's katana clip kept at time t while it's `name`: the guard stays up
-- while its right click is held (Arsenal for yours, Katana.client for everyone else's, every frame)
function TP.holdKat(m: Instance?, name: string, t: number)
	local r = rigFor(m)
	if r and r.kat and r.kat.name == name and r.kat.t > t then r.kat.t = t end
end

local function rigOfUid(uid: any): Rig?
	if type(uid) ~= "number" then return nil end
	local p = Players:GetPlayerByUserId(uid)
	return if p and p.Character then rigFor(p.Character) else nil
end

Remotes:WaitForChild("Shot").OnClientEvent:Connect(function(s: any)
	if type(s) ~= "table" or s.by == me.UserId then return end
	local r = rigFor(if typeof(s.model) == "Instance" then s.model else nil)
	if r then kickRig(r, if type(s.w) == "string" then s.w else nil, false) end
end)
Remotes:WaitForChild("Fx").OnClientEvent:Connect(function(f: any)
	if type(f) ~= "table" then return end
	local r = rigFor(if typeof(f.model) == "Instance" then f.model else nil)
	if f.k == "swing" and f.by ~= me.UserId and r then swingRig(r, nil, if type(f.clip) == "string" then f.clip else nil)
	elseif f.k == "guard" and f.by ~= me.UserId and r then katRig(r, "guard")
	elseif f.k == "parry" and f.kind == "melee" then
		local a = rigOfUid(f.att) -- (the swing that got parried: its owner staggers)
		if a then katRig(a, "stagger") end
	end
end)
-- items, as the server announces them (ItemFx): o = who used it
local THROWN = { frag = "frag", duck = "duck", smokegren = "smoke", calc = "quiz" }
local USED = { ["bub+"] = "bubble", popper = "popper", reverse = "reverse", adsfx = "laptop", nvflash = "nvg", radar = "radar", snap = "camera", medkit = "medkit" }
Remotes:WaitForChild("ItemFx").OnClientEvent:Connect(function(f: any)
	if type(f) ~= "table" then return end
	local r = rigOfUid(f.o)
	if not r then return end
	if f.k == "ps" then
		local w = if type(f.w) == "string" then f.w else ""
		if THROWN[w] then
			itemRig(r, THROWN[w], "throw")
			-- (this arrives as the item leaves the hand: the arm starts from the top of its wind-up and swings through)
			if r.item then r.item.t = TP.T.throw[2].t end
		elseif w == "soap" then itemRig(r, "wand", "use") end
	elseif f.k == "cook" then -- (a grenade held up with its pin out, until it's thrown, goes off or drops: Utility's cooking)
		itemRig(r, if f.w == "smoke" then "smoke" else "frag", "cook")
	elseif f.k == "cookx" then
		if r.item and r.item.kind == "cook" then
			if r.item.model then r.item.model:Destroy() end
			r.item = nil
		end
	elseif USED[f.k] then
		itemRig(r, USED[f.k], "use")
	end
end)

-- an item model in the left hand while it's used (ReplicatedStorage.JankfireItems, the first-person ones: x_<id>,
-- GripPos / GripRot = where the fist goes, its Y up through the fist)
local ITEM_MODEL = { frag = "x_frag", smoke = "x_smoke", medkit = "x_medkit", bubble = "x_bubble", popper = "x_popper", reverse = "x_reverse",
	duck = "x_duck", quiz = "x_calc", laptop = "x_laptop", nvg = "x_nvg", radar = "x_radar", camera = "x_camera", wand = "x_wand" }
local NO_MODEL = { nvg = true } -- (the goggles already show on the head: the items client draws them from the NV attribute)
local function itemModel(r: Rig, id: string): Model?
	if NO_MODEL[id] then return nil end
	local lib = ReplicatedStorage:FindFirstChild("JankfireItems")
	local t = lib and lib:FindFirstChild(ITEM_MODEL[id] or ("x_" .. id))
	-- (the player's own skin for this gadget: a Model in JankfireSkins with Weapon = the gadget id and Item set)
	if r.player then
		local GS = require(Shared:WaitForChild("GunSkins")) :: any
		local sk = GS.template(id, GS.skinFor(r.player, id))
		if sk and sk:GetAttribute("Item") then t = sk end
	end
	local hand = (r.ch:FindFirstChild("LeftHand") or r.ch:FindFirstChild("Left Arm")) :: BasePart? -- (R6: the arm block)
	if not t or not t:IsA("Model") or not hand then return nil end
	local m = t:Clone()
	-- (and their wrap on it, as on their guns: gadgets take wraps since 18 Nov 2026)
	if r.player then
		local wrId, wrMode = WeaponModels.wrapFor(r.player, id)
		if wrId then pcall(WeaponModels.wrap, m, wrId, wrMode) end
	end
	pcall(function() m:ScaleTo(m:GetScale() * r.k / 3) end)
	local gp, gr = m:GetAttribute("GripPos"), m:GetAttribute("GripRot")
	local grip = CF((if typeof(gp) == "Vector3" then gp else Vector3.zero) * m:GetScale()) * eul(if typeof(gr) == "Vector3" then gr else Vector3.zero)
	-- (held as in first person: the calculator turned round, the laptop by its other edge, both facing the holder)
	if id == "quiz" then grip *= ANG(0, -math.pi, 0) end
	if id == "laptop" then local q = grip.Position; grip = CF(-q.X, q.Y, q.Z) * ANG(0, -math.pi, 0) end
	local pv = m:GetPivot()
	local a = r.arms.Left
	local handGrip = if a then a.grip else ID
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = false; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.CastShadow = false; d.Massless = true
			local wd = Instance.new("Weld")
			wd.Part0 = hand; wd.Part1 = d
			wd.C0 = handGrip * grip:Inverse() * pv:ToObjectSpace(d.CFrame)
			wd.Parent = d
		end
	end
	m.Name = "TPItem"
	m.Parent = r.ch
	return m
end

-- ------------------------------------------------------------------ the pose, every frame
local function thirdPerson(): boolean
	local ch = me.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	-- (third person is on: the shoulder camera can come in closer than that in a tight corner)
	return me:GetAttribute("ThirdPerson") == true or (root ~= nil and (camera.CFrame.Position - root.Position).Magnitude > 4.5)
end
TP.thirdPerson = thirdPerson

-- what's under the crosshair in third person: the camera's ray, started level with your head (nothing between the
-- camera and you counts), against the map and everyone's hit boxes (the boxes the shots use). Your shots (Arsenal)
-- and your gun go from your eye to this point, so with the camera over your shoulder they still land on the
-- crosshair up close
local mapRay = RaycastParams.new()
mapRay.FilterType = Enum.RaycastFilterType.Include
function TP.crosshair(eye: Vector3): Vector3
	local cam = camera.CFrame
	local look = cam.LookVector
	local o = cam.Position + look * math.max(0, (eye - cam.Position):Dot(look))
	local far = 900
	local map = workspace:FindFirstChild("Map")
	if map then
		mapRay.FilterDescendantsInstances = { map }
		local hit = workspace:Raycast(o, look * far, mapRay)
		if hit then far = (hit.Position - o).Magnitude end
	end
	local best = far
	local function body(m: Model)
		local hum = m:FindFirstChildOfClass("Humanoid")
		local root = m:FindFirstChild("HumanoidRootPart") :: BasePart?
		if not hum or not root or hum.Health <= 0 then return end
		local feet = Hitbox.feet(root.Position)
		local t = Hitbox.ray(o, look, feet, Hitbox.distScale((feet - eye).Magnitude))
		if t and t < best then best = t end
	end
	for _, p in Players:GetPlayers() do
		if p ~= me and p.Character then body(p.Character) end
	end
	local dm = workspace:FindFirstChild("Dummies")
	if dm then for _, m in dm:GetChildren() do if m:IsA("Model") then body(m) end end end
	if best < far then best += 0.3 end -- (a little into the box: the line from your eye surely goes in)
	return o + look * best
end

-- where you look, for your own body: from your eye toward what the crosshair is on (so in third person the gun points
-- at what the camera's centre sees, not along the camera)
local myAim = { pitch = 0, yaw = 0 }
local function myLook(r: Rig)
	local cam = camera.CFrame
	local eye = r.root.Position + V(0, Hitbox.EYE_UP - Hitbox.ROOT_UP, 0)
	local dir = cam.LookVector
	if thirdPerson() then
		local to = TP.crosshair(eye) - eye
		if to.Magnitude > 1 then dir = to.Unit end
	end
	local rel = r.root.CFrame:VectorToObjectSpace(dir)
	myAim.pitch = math.asin(math.clamp(dir.Y, -1, 1))
	myAim.yaw = math.clamp(math.atan2(-rel.X, -rel.Z), -1.2, 1.2)
end

local FLAG_AIM, FLAG_RELOAD, FLAG_EMPTY = 1, 2, 4

-- the state of another body: the "TP" attribute its owner's client sent (pitch, yaw in degrees; flags)
local function readState(r: Rig, dt: number)
	local v = r.ch:GetAttribute("TP")
	local p, y, f = 0, 0, 0
	if typeof(v) == "Vector3" then p, y, f = math.rad(v.X), math.rad(v.Y), math.floor(v.Z + 0.5) end
	local a = math.min(1, dt * 14)
	r.pitch += (p - r.pitch) * a
	r.yaw += (y - r.yaw) * a
	local was = r.flags
	r.flags = f
	r.aim = math.clamp(r.aim + (if bit32.band(f, FLAG_AIM) ~= 0 then 7 else -8) * dt, 0, 1)
	local rl = bit32.band(f, FLAG_RELOAD) ~= 0
	if rl and bit32.band(was, FLAG_RELOAD) == 0 then reloadRig(r, nil, bit32.band(f, FLAG_EMPTY) ~= 0)
	elseif not rl and bit32.band(was, FLAG_RELOAD) ~= 0 and r.clip and string.sub(r.clip.name, 1, 7) == "reload_" then
		-- (it ended on their side: let ours run out unless it was cut short, a swap or a death)
		if r.clip.t < (Anims[r.clip.name].dur * 0.8) then r.clip = nil end
	end
	-- test rigs: a fire / swing / guard / item is a number that changes
	if CollectionService:HasTag(r.ch, "TPRig") then
		for _, ev in { "TPFire", "TPSwing", "TPGuard", "TPStagger", "TPItem" } do
			local n = r.ch:GetAttribute(ev)
			local key = ev .. "_seen"
			if n ~= nil and n ~= (r :: any)[key] then
				(r :: any)[key] = n
				if ev == "TPFire" then kickRig(r, nil, false)
				elseif ev == "TPSwing" then swingRig(r, nil)
				elseif ev == "TPGuard" then katRig(r, "guard")
				elseif ev == "TPStagger" then katRig(r, "stagger")
				elseif ev == "TPItem" and type(n) == "string" then
					local id, kind = string.match(n, "^(%a+):(%a+)")
					if id and kind then itemRig(r, id, kind) end
				end
			end
		end
		-- frozen poses for photos: "TPKatPose" = "swing:0.15", "TPClipPose" = "reload_ar:0.6", "TPItemPose" = "frag:throw:0.12"
		local kp = r.ch:GetAttribute("TPKatPose")
		if type(kp) == "string" then
			local n, t = string.match(kp, "^(%w+):([%d%.]+)$")
			if n and KAT[n] then r.kat = { name = n, t = tonumber(t) or 0 } end
		end
		local cp = r.ch:GetAttribute("TPClipPose")
		if type(cp) == "string" then
			local n, t = string.match(cp, "^([%w_]+):([%d%.]+)$")
			if n and Anims[n] then r.clip = { name = n, t = tonumber(t) or 0, rate = 0 }; r.follow = nil end
		end
		local ip = r.ch:GetAttribute("TPItemPose")
		if type(ip) == "string" then
			local id, kind, t = string.match(ip, "^(%a+):(%a+):([%d%.]+)$")
			if id and kind then
				if not (r.item and r.item.id == id and r.item.kind == kind) then itemRig(r, id, kind) end
				if r.item then r.item.t = (tonumber(t) or 0) - dt end
			end
		end
	end
end

-- the gun's pose in chest space (before the clip, the kick and the sprint), for a stance. Q = the look against the
-- chest; eye = the right eye (chest space)
local function gunPose(r: Rig, st: any, Q: CFrame, eye: Vector3, e: number): CFrame
	local u = r.u
	local ads = CF(eye) * Q * CF(st.ads * u) * CF(-r.sight)
	if e >= 0.999 then return ads end
	local hip = CF(eye) * Q * CF(st.hip * u) * eul(st.hipRot) * CF(st.ads * u) * CF(-r.sight)
	if e <= 0.001 then return hip end
	return hip:Lerp(ads, e)
end

-- (the hold session, 18 Nov 2026) a body's Bow draw this frame: d = how far it's drawn (0..1), nil when it isn't. pull:
-- the string, a share of the full draw (its spring overshoots past 0 after the let-go); hand: the right hand's (the
-- same while drawing; it stays at the cheek a moment after); up: how far the bow is raised to the draw (0..1)
type BowS = { up: number, pull: number, pv: number, hand: number, relT: number, relPull: number, was: boolean, fullT: number? }
local function bowStep(r: Rig, d: number?, dt: number, now: number): BowS
	local rx = r :: any
	if not rx.bowS then rx.bowS = { up = 0, pull = 0, pv = 0, hand = 0, relT = -10, relPull = 0, was = false } end
	local B = rx.bowS :: BowS
	local T = TP.T.bow
	local drawing = d ~= nil
	if B.was and not drawing then B.relT = now; B.relPull = B.pull; B.fullT = nil end
	B.was = drawing
	local rt = now - B.relT
	if drawing then
		local dd = math.clamp(d :: number, 0, 1)
		B.pull += ((1 - (1 - dd) ^ 1.6) - B.pull) * math.min(1, dt * 20); B.pv = 0
		if dd >= 0.999 then B.fullT = B.fullT or now else B.fullT = nil end
		B.hand = B.pull
	else
		local n = math.clamp(math.ceil(dt * 240), 1, 40)
		local h = dt / n
		for _ = 1, n do B.pv += (-3600 * B.pull - 80 * B.pv) * h; B.pull += B.pv * h end -- (the snap: past its rest and back)
		local tgt = if rt < T.hold then B.relPull else 0
		B.hand += (tgt - B.hand) * math.min(1, dt * (if rt < T.hold then 30 else 7))
	end
	local upNow = drawing or rt < T.hold
	B.up += ((if upNow then 1 else 0) - B.up) * math.min(1, dt * (if upNow then 12 else 5))
	return B
end
-- ... and its string (two halves from the limbs to the nock) and the arrow on it, welded into the gun (so they move with
-- it on the same step): made while the bow is up or the string still moving, the kit's straight string hidden then
local BOW_NOCK, BOW_LEAVE = 0.1132, { V(0, 0.36, 0.1132), V(0, -0.36, 0.1132) } -- (the kit bow's export meta.bow, file metres)
local BOW_ARROW_NOCK = V(-0.0023, 0, 0.4002) -- (w_pj_arrow's nock)
local BOW_STUDIO = game:GetService("RunService"):IsStudio() -- (Studio photos: your BowDrawHold attribute holds your draw)
local function bowString(r: Rig, B: BowS, on: boolean, cd: number, now: number)
	local rx = r :: any
	local s = rx.bowStr
	if s and (s.gun ~= r.gun or not on) then
		for _, p in s.halves do p:Destroy() end
		if s.arrow then s.arrow:Destroy() end
		for _, p in s.kit do if p.Parent then p:SetAttribute("Hide", nil) end end
		rx.bowStr = nil; s = nil
	end
	if not on or not r.gun or not r.groot then return end
	local root = r.groot :: BasePart
	if not s then
		local kit, col = {}, Color3.fromRGB(60, 52, 44)
		for _, d in (r.gun :: Model):GetDescendants() do
			if d:IsA("BasePart") and string.sub(string.lower(d.Name), 1, 6) == "string" then
				if string.find(string.lower(d.Name), "cord", 1, true) then col = d.Color end
				d:SetAttribute("Hide", true) -- (the gun's own hide pass: LocalTransparencyModifier)
				table.insert(kit, d)
			end
		end
		local halves = {}
		for i = 1, 2 do
			local p = Instance.new("Part")
			p.Name = "TPBowString" .. i
			p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false; p.Massless = true
			p.Material = Enum.Material.SmoothPlastic; p.Color = col
			p.Size = V(0.012 * r.k, 0.012 * r.k, 0.1)
			p.CFrame = root.CFrame
			p.Parent = r.gun
			local wd = Instance.new("Weld")
			wd.Part0 = root; wd.Part1 = p; wd.Parent = p
			halves[i] = { part = p, weld = wd }
		end
		local arrow, aw, arel = nil, nil, CFrame.identity
		local lib = game:GetService("ReplicatedStorage"):FindFirstChild("JankfireWeapons")
		local t = lib and lib:FindFirstChild("w_pj_arrow")
		if t and t:IsA("Model") then
			local a = t:Clone()
			a.Name = "TPBowArrow"
			a:ScaleTo(a:GetScale() * r.k * TP.T.bow.arrowScale)
			a:PivotTo(root.CFrame)
			local main = a.PrimaryPart or a:FindFirstChildWhichIsA("BasePart", true)
			if main then
				for _, d in a:GetDescendants() do
					if d:IsA("BasePart") then
						d.Anchored = false; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.CastShadow = false; d.Massless = true
						if d ~= main then local wc = Instance.new("WeldConstraint"); wc.Part0 = main; wc.Part1 = d; wc.Parent = d end
					end
				end
				arel = a:GetPivot():ToObjectSpace(main.CFrame)
				a.Parent = r.gun
				aw = Instance.new("Weld")
				aw.Part0 = root; aw.Part1 = main; aw.C0 = arel; aw.Parent = main
				arrow = a
			else
				a:Destroy()
			end
		end
		s = { gun = r.gun, halves = halves, kit = kit, arrow = arrow, aweld = aw, arel = arel, shown = true }
		rx.bowStr = s
	end
	local rt = now - B.relT
	local buzz = if not B.was and rt < 0.4 then math.sin(rt * 2 * math.pi * 24) * 0.005 * r.k * math.exp(-rt / 0.08) else 0
	local nock = V(buzz, 0, BOW_NOCK * r.k + B.pull * (rx.bowFull or 0))
	for i, hv in s.halves do
		local a = BOW_LEAVE[i] * r.k
		hv.part.Size = V(hv.part.Size.X, hv.part.Size.Y, math.max(0.01, (nock - a).Magnitude))
		hv.weld.C0 = CFrame.lookAt((a + nock) / 2, nock)
	end
	if s.arrow and s.aweld then
		local ready = B.was or rt > cd
		s.aweld.C0 = CF(nock - BOW_ARROW_NOCK * r.k * TP.T.bow.arrowScale) * s.arel
		if ready ~= s.shown then
			s.shown = ready
			for _, d in s.arrow:GetDescendants() do if d:IsA("BasePart") then d.LocalTransparencyModifier = if ready then 0 else 1 end end
		end
	end
end

local function katanaPose(r: Rig, Q: CFrame): CFrame
	local st = TP.T.katana
	local u = r.u
	local p, rot = KAT_REST.p, KAT_REST.r
	local kc = r.kat
	if kc then
		local K = KAT[kc.name]
		if K then
			local pp, rr = sampleKeys(K.keys, kc.t)
			p, rot = pp, rr or rot
		end
	end
	local chest = st.chest * u
	-- the stance looks part of the way up and down with you
	local q = ID:Lerp(Q, st.pitchShare)
	return CF(chest) * q * CF(p * u) * eul(rot)
end

local function stepRig(r: Rig, dt: number, now: number)
	local hum = r.hum
	if hum.Health <= 0 or not r.root.Parent then release(r); return end
	local src, wid = sourceOf(r.ch)
	if not src or not wid then
		if r.src then release(r) end
		return
	end
	if r.dirty or now - r.geomT > 0.5 then
		if not readBody(r) then return end
	end
	if src ~= r.src or wid ~= r.wid or (not r.gun and not r.tool) then
		if r.src and r.src ~= src then showServerGun(r) end
		r.src = src
		buildGun(r, wid, src)
	end
	if not r.gun and not r.tool then return end
	if src.Name == "HeldWeapon" then hideServerGun(r, src) end
	r.isMe = r.ch == me.Character
	-- how far off: far bodies are posed every 3rd frame
	r.frame += 1
	local dist = (camera.CFrame.Position - r.root.Position).Magnitude
	local acc = dt
	if dist > TP.T.far then
		(r :: any).acc = ((r :: any).acc or 0) + dt
		if r.frame % 3 ~= 0 then return end
		acc = (r :: any).acc; (r :: any).acc = 0
	end
	dt = acc
	-- ---- the state: yours from your own game, everyone else's from the network
	if r.isMe then
		myLook(r)
		r.pitch, r.yaw, r.aim = myAim.pitch, myAim.yaw, mine.aim
	else
		readState(r, dt)
	end
	local st = TP.T[STANCE[r.wid] or r.cls] or TP.T.rifle
	local w = W[r.wid]
	r.on = math.min(1, r.on + dt * 6)
	-- the clip (reload / draw / pump), the follow-up after a shot, the katana's move
	local clip = r.clip
	if clip then
		clip.t += dt * clip.rate
		if clip.t >= Anims[clip.name].dur then r.clip = nil; clip = nil end
	end
	if r.follow and now >= r.follow.at then
		if not (clip and string.sub(clip.name, 1, 7) == "reload_") then r.clip = { name = r.follow.name, t = 0, rate = 1 }; clip = r.clip end
		r.follow = nil
	end
	if r.kat then
		r.kat.t += dt
		local K = KAT[r.kat.name]
		if not K or r.kat.t >= K.dur then r.kat = nil end
	end
	if r.wid == "katana" and r.gun then
		local n = katOf(r)
		if n ~= r.kKat then r.kKat = n; WeaponModels.setKatana(r.gun, n, r.k) end
	end
	local reloading = clip ~= nil and string.sub(clip.name, 1, 7) == "reload_"
	-- the recoil springs (240 Hz sub-steps, like first person)
	local rec = r.rec
	local nSub = math.clamp(math.ceil(dt * 240), 1, 40)
	local h = dt / nSub
	for _ = 1, nSub do
		rec.pv += (-220 * rec.p - 20 * rec.pv) * h; rec.p += rec.pv * h
		rec.rv += (-200 * rec.r - 18 * rec.rv) * h; rec.r += rec.rv * h
	end
	-- (the hold session, 18 Nov 2026) the Lasso spun / held, caught on one, riding a cart: the player's attributes, eased
	local plr = Players:GetPlayerFromCharacter(r.ch)
	local rx = r :: any
	local function eased(key: string, on: boolean, rate: number): number
		local v = (rx[key] or 0) + ((if on then 1 else 0) - (rx[key] or 0)) * math.min(1, dt * rate)
		rx[key] = v
		return v
	end
	local ride = eased("cartRide", plr ~= nil and plr:GetAttribute("RidingCart") ~= nil, 6) -- (not "ride": r.ride is the pump hand's)
	local lspin = eased("lspin", r.wid == "lasso" and plr ~= nil and plr:GetAttribute("LassoSpin") == true, 9)
	local lhold = eased("lhold", r.wid == "lasso" and plr ~= nil and plr:GetAttribute("LassoHolding") == true, 9)
	local flail = eased("flail", plr ~= nil and plr:GetAttribute("LassoHeld") == true, 8)
	-- the Bow's draw: yours from Arsenal (TP.mine), anyone else's from their BowDrawT (the server clock when their draw
	-- began: weapons-port's), a TPRig test body's from its own BowDraw (0..1)
	local bowS: BowS? = nil
	if r.wid == "bow" then
		local bd: number? = nil
		if r.isMe then
			bd = mine.draw
			local hd = if BOW_STUDIO then me:GetAttribute("BowDrawHold") else nil
			if type(hd) == "number" then bd = math.clamp(hd, 0, 1) end
		else
			local holder: Instance = plr or r.ch
			local dd, t0 = holder:GetAttribute("BowDraw"), holder:GetAttribute("BowDrawT")
			if type(dd) == "number" then bd = math.clamp(dd, 0, 1)
			elseif type(t0) == "number" then bd = math.clamp((workspace:GetServerTimeNow() - t0) / (if w and w.drawT then w.drawT else 0.7), 0, 1) end
		end
		bowS = bowStep(r, bd, dt, now)
	end
	local bowUp = if bowS then smoothstep(bowS.up) else 0
	local spinAt: Vector3?, ropeL: CFrame? = nil, nil -- (the spinning fist, chest space; the left fist on the rope)
	-- sprinting (on the ground, fast, not aiming, not just fired): the gun comes down across the body (riding a cart too)
	local vel = r.root.AssemblyLinearVelocity
	local spd = V(vel.X, 0, vel.Z).Magnitude
	local sprint = if r.isMe then mine.sprint and spd > 12 else spd > TP.T.lowSpeed
	local wantLow = (sprint and hum.FloorMaterial ~= Enum.Material.Air or ride > 0.5) and r.aim < 0.2 and now - r.lastFire > 0.6 and not reloading
		and r.cls ~= "katana"
	r.low += ((if wantLow then 1 else 0) - r.low) * math.min(1, dt * 8)
	-- ---- the chest: turned into the stance, part of the look pitch, the walk's sway taken out
	local J = r.J
	local e = smoothstep(r.aim)
	local twist = if r.cls == "katana" then st.twist else st.twist + (st.twistAds - st.twist) * e
	if bowUp > 0 then twist += (TP.T.bow.twist - twist) * bowUp end -- (the Bow drawn: side on, the left shoulder to it)
	local pitch = math.clamp(r.pitch, -1.45, 1.45)
	local yaw = math.clamp(r.yaw, -1.2, 1.2)
	local crouchW = 0
	local pose = r.ch:GetAttribute("Pose")
	if r.isMe then
		local ui = game:GetService("UserInputService")
		if not ui:GetFocusedTextBox() and Binds.on("crouch") then crouchW = 1 end -- (held or toggled: Binds)
	elseif pose == "crouch" then crouchW = 1 end
	local waistPitch = pitch * st.waist - 0.12 * crouchW - TP.T.lasso.lean * ride
	local Rut = ANG(0, yaw + twist, 0) * ANG(waistPitch, 0, 0)
	local Raim = ANG(0, yaw, 0) * ANG(pitch, 0, 0)
	local on = r.on
	local LT = (J.Root.c0 * J.Root.j.Transform * J.Root.c1:Inverse()).Rotation
	if J.Waist then
		local Tw = (J.Waist.c0.Rotation:Inverse() * LT:Inverse() * Rut * J.Waist.c1.Rotation)
		J.Waist.j.Transform = if on >= 0.999 then Tw else J.Waist.j.Transform:Lerp(Tw, on)
	else
		Rut = LT -- (R6: no waist, the chest stays where the body has it; the aim is all in the arms and the head)
	end
	local Q = (Rut:Inverse() * Raim).Rotation
	-- ---- the head: where the gun points; the cheek down on the stock while aiming
	local cheek = st.cheek or Vector3.zero
	local Hq = Q * eul(cheek * e)
	if r.cls == "katana" then Hq = Q end
	local Tn = J.Neck.c0.Rotation:Inverse() * Hq * J.Neck.c1.Rotation
	J.Neck.j.Transform = if on >= 0.999 then Tn else J.Neck.j.Transform:Lerp(Tn, on)
	local headCF = CF(r.nk) * Hq * CF(-r.headC1.Position)
	local eye = headCF * (TP.T.eye * r.Hs)
	-- ---- the gun
	local G: CFrame
	if r.cls == "katana" then
		G = katanaPose(r, Q)
	else
		G = gunPose(r, st, Q, eye, e)
		if clip then
			local p, crot = sampleClip(clip.name, clip.t)
			G = G * CF(p * r.k * TP.T.clipK) * crot
		end
		-- the kick about the grip, then the sprint's lowering about the grip
		local gp = r.gripPt
		G = G * CF(gp) * ANG(rec.r.X, 0, rec.r.Z) * CF(-gp) * CF(rec.p.X, 0, rec.p.Z)
		if r.low > 0.001 then G = G * CF(gp) * eul(TP.T.low * r.low) * CF(-gp) end
		-- the Hot Sauce's swig (18 Nov 2026: the player attribute Swig, set by the server while its trigger is held):
		-- the bottle up in front of the mouth, its cap tipped toward it (TP.T.swig: rot about the head, mouth in head
		-- sizes from its middle), eased in and out
		if r.wid == "cig" then
			local who = Players:GetPlayerFromCharacter(r.ch)
			local holder: Instance = who or r.ch -- (a TPRig test body: its own Swig attribute)
			local on = holder:GetAttribute("Swig") == true
			local want = if on then 1 else 0
			local ra = r :: any
			if on and not ra.swigT then ra.swigT = os.clock() elseif not on then ra.swigT = nil end -- (when this swig began)
			ra.swig = (ra.swig or 0) + (want - (ra.swig or 0)) * math.min(1, dt * 5) -- (the up-and-over, ~0.45 s)
			if ra.swig > 0.001 then
				local sw = TP.T.swig
				local k = if ra.swigT then math.clamp((os.clock() - ra.swigT) / 3, 0, 1) else 1 -- (3 s: the swig's maxCharge)
				-- (up and over: the tip eased by angle the long way round (+2 pi), so the hand comes up to the head and the
				-- cap rises and turns over to the mouth; a Lerp of the whole turn went down and away, as if dumping it)
				local e = smoothstep(ra.swig)
				local M = CF(headCF * (sw.mouth * r.Hs)) * Hq * ANG((sw.tip + sw.more * smoothstep(k) + 2 * math.pi) * e, 0, 0) * CF(0, 0, 0.118 * r.k)
				G = G:Lerp(M, e)
			end
		end
		-- (the hold session, 18 Nov 2026) weapons-port's Lasso (TP.T.lasso): spinning, the coil's fist goes round over
		-- the head; holding someone, it's low and ahead on the rope; caught (whatever they hold), the gun's hand is up
		-- and waving
		if r.holdR and (lspin > 0.001 or lhold > 0.001 or flail > 0.001) then
			local T = TP.T.lasso
			local RS, inv = r.arms.Right.S, (r.holdR :: CFrame):Inverse()
			if lhold > 0.001 then
				local p = RS + Q * (T.pull * r.u)
				G = G:Lerp(CF(p) * Q * ANG(-math.pi / 2, 0, 0) * inv, smoothstep(lhold))
				ropeL = CF(p + Q.LookVector * T.lead * r.u) * Q * ANG(-math.pi / 2, 0, 0)
			end
			if lspin > 0.001 then
				local ph = now * 2 * math.pi * T.rev
				spinAt = RS + (T.spin + V(math.cos(ph), 0, math.sin(ph)) * T.circle) * r.u
				G = G:Lerp(CF(spinAt :: Vector3) * Q * inv, smoothstep(lspin))
			end
			if flail > 0.001 then
				local wv = now * 2 * math.pi * T.waveHz
				local p = RS + (T.flailR + V(math.sin(wv), math.cos(wv * 1.3), 0) * T.wave) * r.u
				G = G:Lerp(CF(p) * Q * inv, smoothstep(flail))
			end
		end
		-- the Bow drawn (TP.T.bow): out on the straight left arm, the arrow's line along the aim through the anchor under
		-- the right cheek; how far out the arm's reach decides, and the string comes back that far less the nock's own
		if bowS and bowUp > 0.001 then
			local T = TP.T.bow
			local f = Q.LookVector
			local A = eye + Q * (T.anchor * r.u)
			local La = r.arms.Left
			local dv = A - La.S
			local b = f:Dot(dv)
			local disc = b * b - (dv:Dot(dv) - (La.reach * T.reach) ^ 2)
			local D = math.max(if disc > 0 then -b + math.sqrt(disc) else 0.9 * r.u, 0.4 * r.u)
			local rest = A + f * D
			rx.bowFull = math.max(0, D - BOW_NOCK * r.k)
			local rt = now - bowS.relT
			local sh = if bowS.fullT then math.min(1, (now - bowS.fullT) / T.shakeIn) else 0
			local tremor = V(math.sin(now * 71) * 0.6 + math.sin(now * 113 + 1) * 0.4, math.sin(now * 83 + 2) * 0.6 + math.sin(now * 127) * 0.4, 0) * (T.shake * r.u * sh)
			local kk = if bowS.was then 0 else (1 - math.exp(-rt / 0.02)) * math.exp(-rt / 0.09) * 1.6
			local Bf = CF(f * (T.kick * r.u * kk) + Q * tremor) * CFrame.lookAt(rest, rest + f, Q.UpVector) * ANG(-T.rock * kk, 0, T.roll)
			G = G:Lerp(Bf, bowUp)
		end
		-- a breath and the stride, small
		local bob = if hum.FloorMaterial ~= Enum.Material.Air then math.min(1, spd / 20) else 0
		local ph = now * (if spd > 20 then 11 else 8)
		G = CF(math.sin(ph * 0.5) * 0.015 * r.u * bob, (math.abs(math.sin(ph * 0.5)) * -0.03 * bob + math.sin(now * 1.7) * 0.006) * r.u, 0) * G
	end
	-- ---- the Shredder: a Tool in Roblox's own grip, so the right hand goes where the tool lands in the stance
	local arms = r.arms
	local R, L = arms.Right, arms.Left
	local poleR = R.S + st.poleR * r.u
	local poleL = L.S + st.poleL * r.u
	if bowUp > 0.001 then -- (the Bow drawn: the right elbow out behind, the bow arm's nearly straight)
		poleR = poleR:Lerp(R.S + TP.T.bow.poleR * r.u, bowUp)
		poleL = poleL:Lerp(L.S + TP.T.bow.poleL * r.u, bowUp)
	end
	local handR: CFrame?, handL: CFrame?
	if r.tool then
		local tool = r.tool
		local hand = (r.ch:FindFirstChild("RightHand") or r.ch:FindFirstChild("Right Arm")) :: BasePart? -- (R6: the Tool's grip is on the arm)
		local grip = hand and hand:FindFirstChild("RightGrip") :: Weld?
		if grip and r.toolFrame and grip.Part1 then
			-- G is where the gun's own frame (muzzle -Z, chute up) goes: aim it from the eye like a heavy gun
			local Gs = CF(eye) * Q * CF(st.hip * r.u * (1 - e) + st.ads * r.u * e)
			Gs = Gs * CF(rec.p.X, 0, rec.p.Z)
			local handle = Gs * r.toolFrame:Inverse()
			handR = handle * (tool.Grip :: CFrame) * grip.C0:Inverse()
			if r.holdL then handL = handOn(L, handle * r.holdL, r.poseL, r.turnL, poleL) end
		end
	else
		if r.weld then r.weld.C0 = G end
		local g2 = (r :: any).gun2 -- (Lefty & Righty: the left gun, the right one's mirror)
		local G2 = if g2 then mirrorX(G) else nil
		if g2 and G2 then
			g2.weld.C0 = G2
			if g2.parts and w and dist < TP.T.far then
				GunParts.step(g2.parts, dt, { clip = nil, t = 0, anims = Anims, ammo = w.mag or 0, mag = w.mag or 0, reloading = false, now = now, firedT = r.lastFire }, w)
			end
		end
		-- the moving pieces (near bodies only)
		if r.parts and w and dist < TP.T.far then
			GunParts.step(r.parts, dt, {
				clip = if clip then clip.name else nil, t = if clip then clip.t else 0, anims = Anims,
				ammo = (if r.isMe and mine.ammo then mine.ammo else w.mag) or 0, mag = w.mag or 0, reloading = reloading, now = now, firedT = r.lastFire,
			}, w)
		end
		-- the pieces a reload takes out (a dropped mag) and your own gun in first person: hidden (and scoped in from
		-- third person, TPScope: ShoulderCam took the camera into your head)
		local hideAll = r.isMe and (not thirdPerson() or me:GetAttribute("TPScope") == true)
		for _, d in (r :: any).gunParts or {} do
			local want = if hideAll or d:GetAttribute("Hide") then 1 else 0
			if r.shown[d] ~= want then r.shown[d] = want; d.LocalTransparencyModifier = want end
		end
		if r.holdR then
			local Fr = G * r.holdR
			if bowS and bowS.hand > 1e-3 then -- (the Bow: the hand on the string wherever the draw has it; at the cheek a moment after)
				local rt = now - bowS.relT
				local fol = if not bowS.was and rt < TP.T.bow.hold then TP.T.bow.follow * r.u * math.min(1, rt / 0.08) else 0
				Fr = G * CF(0, 0, bowS.hand * ((r :: any).bowFull or 0) + fol) * r.holdR
			end
			handR = handOn(R, Fr, if r.poseR == "hand" then "hand" else "grip", r.turnR, poleR)
		end
		if r.holdL then
			local F = (G2 or G) * r.holdL -- (Lefty & Righty: on the left gun's grip)
			local gunBack = G:VectorToWorldSpace(Vector3.zAxis)
			-- the off hand: on the handguard (riding the pump), or at the reload's moving piece
			if r.ride then
				local p = r.ride.piece
				F = G * ((p.last or p.rest) * r.ride.rel)
			end
			if r.cls ~= "katana" and not G2 then F = within(L, F, gunBack, 0.18 * r.k) end
			handL = handOn(L, F, r.poseL, r.turnL, poleL)
		end
		-- reloads: the off hand takes the magazine / the cylinder / the shells down and back
		r.leftW = 0
		if clip and reloading then
			for _, g in r.grab do
				local t0, t1 = chWindow(clip.name, g.ch)
				if t0 and t1 then
					local mix = smoothstep((clip.t - (t0 - 0.2)) / 0.18) * (1 - smoothstep((clip.t - t1) / 0.22))
					if mix > 0 then
						local p = g.piece
						local F = G * ((p.last or p.rest) * g.rel)
						local hand = handOn(L, F, "grip", 0, poleL)
						handL = if handL then handL:Lerp(hand, mix) else hand
						r.leftW = mix
						break
					end
				end
			end
		end
		-- the Yeehaw's spin and the Revolver's twirl: the off hand stands clear
		if clip then
			local a = Anims[clip.name]
			local tw = a and a.ch and a.ch.twirl
			if tw and handL then
				local t0, t1 = tw[1][1], tw[#tw][1]
				for i = 1, #tw do if tw[i][2] ~= 0 then t0 = tw[math.max(1, i - 1)][1]; break end end
				local mix = smoothstep((clip.t - (t0 - 0.16)) / 0.16) * (1 - smoothstep((clip.t - t1) / 0.2))
				if mix > 0 then handL = handL:Lerp(handL + V(-0.15, -0.45, 0.2) * r.u, mix) end
			end
		end
		-- (the hold session, 18 Nov 2026) the other fist on the Lasso's rope; a caught one's other hand up and waving;
		-- a cart rider's free left hand out for balance (TP.T.lasso)
		local T = TP.T.lasso
		if ropeL and lhold > 0.001 then
			local hand = handOn(L, ropeL :: CFrame, "grip", 0, poleL)
			handL = if handL then handL:Lerp(hand, lhold) else hand
			r.leftW = math.max(r.leftW, lhold)
		end
		if flail > 0.001 then
			local wv = now * 2 * math.pi * T.waveHz + 2
			local hand = CF(L.S + (T.flailL + V(math.sin(wv * 1.1), math.cos(wv), 0) * T.wave) * r.u) * Q * L.gripInv
			handL = if handL then handL:Lerp(hand, flail) else hand
			r.leftW = math.max(r.leftW, flail)
		elseif ride > 0.001 and not r.holdL then
			local hand = CF(L.S) * Q * CF(T.ride * r.u) * L.gripInv
			handL = if handL then handL:Lerp(hand, ride) else hand
			r.leftW = math.max(r.leftW, ride)
		end
	end
	-- ---- items: the left hand throws or holds one up, then goes back
	local it = r.item
	local itemMix = 0
	if it then
		it.t += dt
		local T = TP.T
		if it.kind == "throw" then
			local last = T.throw[#T.throw].t
			if it.t >= last then
				if it.model then it.model:Destroy() end
				r.item = nil
			else
				local p = sampleKeys(T.throw, it.t)
				local F = CF(L.S) * Q * CF(p * r.u)
				local hand = F * L.gripInv
				itemMix = smoothstep(it.t / 0.08) * (1 - smoothstep((it.t - (last - 0.2)) / 0.2))
				handL = if handL then handL:Lerp(hand, itemMix) else hand
				if it.model then it.model:Destroy(); it.model = nil end -- (the thrown item is drawn in flight by the items client)
			end
		elseif it.kind == "cook" then
			-- a grenade being cooked: up at the top of the throw's wind-up with its pin out, held there until it's thrown
			-- (the throw's "ps" takes over from that key), goes off or drops ("cookx"); never longer than 4 s
			if it.t >= 4 then
				if it.model then it.model:Destroy() end
				r.item = nil
			else
				local F = CF(L.S) * Q * CF(T.throw[2].p * r.u)
				local hand = F * L.gripInv
				itemMix = smoothstep(it.t / 0.14)
				handL = if handL then handL:Lerp(hand, itemMix) else hand
				if not it.model then
					it.model = itemModel(r, it.id)
					if it.model then
						for _, d in it.model:GetDescendants() do
							if d:IsA("BasePart") and (string.match(d.Name, "^pin") or string.match(d.Name, "^ring")) then d.Transparency = 1 end
						end
					end
				end
			end
		else
			local u = T.use[it.id] or T.use.medkit
			if it.t >= u.dur then
				if it.model then it.model:Destroy() end
				r.item = nil
			else
				local base = if u.from == "E" then CF(eye) * Q else CF(L.S) * Q
				local F = base * CF(u.p * r.u) * ANG(0.2, 0, 0)
				local hand = F * L.gripInv
				itemMix = smoothstep(it.t / 0.14) * (1 - smoothstep((it.t - (u.dur - 0.2)) / 0.2))
				handL = if handL then handL:Lerp(hand, itemMix) else hand
				if not it.model then it.model = itemModel(r, it.id) end
			end
		end
	end
	-- ---- the arms: IK onto the hands. a free left hand (a pistol) goes back to the animation's own swing
	local r6 = (r :: any).r6 == true -- (an R6 body: each arm one block, aimed on its shoulder)
	if handR then if r6 then solveArmR6(R, handR, on, r.poseR == "hand") else solveArm(R, handR, poleR, on) end end
	local leftOn = handL ~= nil and (r.holdL ~= nil or r.tool ~= nil or itemMix > 0 or r.leftW > 0)
	if handL and leftOn then
		local wgt = on
		if not r.holdL and not r.tool then wgt = math.max(itemMix, r.leftW) * on end
		if r6 then solveArmR6(L, handL, wgt, r.poseL == "hand") else solveArm(L, handL, poleL, wgt) end
	end
	-- (the hold session, 18 Nov 2026) the Lasso's loop over the head while it spins, the fist driving it round its
	-- edge: everyone's, and yours in third person (first person draws its own)
	local loop = rx.loop :: { BasePart }?
	if loop and (loop :: { BasePart })[1].Parent ~= r.gun then rx.loop = nil; loop = nil end -- (the gun was rebuilt)
	if spinAt and lspin > 0.05 and r.gun and not (r.isMe and not thirdPerson()) then
		if not loop then
			local list = {}
			for i = 1, 18 do
				local p = Instance.new("Part")
				p.Name = "LassoLoop"; p.Shape = Enum.PartType.Cylinder
				p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
				p.Material = Enum.Material.SmoothPlastic; p.Color = Color3.fromRGB(214, 178, 118)
				p.Parent = r.gun
				list[i] = p
			end
			rx.loop = list
			loop = list
		end
		local T = TP.T.lasso
		local ph = now * 2 * math.pi * T.rev
		local hand = r.ut.CFrame:PointToWorldSpace(spinAt :: Vector3)
		local way = r.ut.CFrame:VectorToWorldSpace(V(math.cos(ph), 0, math.sin(ph)))
		local rad = T.loop * r.u
		local thick = 0.035 * r.u
		local mid = CF(hand + V(way.X, 0, way.Z) * rad * 0.85)
		local seg = 2 * math.pi * rad / 18 + 0.05
		for i, p in loop :: { BasePart } do
			local th = (i - 1) / 18 * 2 * math.pi - ph
			p.Size = V(seg, thick, thick)
			p.CFrame = mid * ANG(0, th, 0) * CF(rad, 0, 0) * ANG(0, math.pi / 2, 0)
		end
	elseif loop then
		for _, p in loop :: { BasePart } do p:Destroy() end
		rx.loop = nil
	end
	-- (the hold session, 18 Nov 2026) the Bow's string and arrow: everyone's, and yours in third person
	if bowS then
		local hideMine = r.isMe and (not thirdPerson() or me:GetAttribute("TPScope") == true)
		local on = r.gun ~= nil and dist < TP.T.far and not hideMine and (bowS.up > 0.002 or math.abs(bowS.pull) > 1e-3)
		bowString(r, bowS, on, if w and w.cd then w.cd else 0.35, now)
	elseif rx.bowStr then
		bowString(r, rx.bowS or { up = 0, pull = 0, pv = 0, hand = 0, relT = -10, relPull = 0, was = false }, false, 0, now)
	end
	-- (the hold session, 18 Nov 2026) the Blood Cross's hat spot on this body's own right hand (AvatarArms.hatSpot;
	-- GunHats seats the Googly Eyes there): while it's out, not on yours while you're in first person
	local rhand = r.ch:FindFirstChild("RightHand") or r.ch:FindFirstChild("Right Arm") -- (R6: on the arm, AvatarArms.hatSpot)
	if rhand and rhand:IsA("BasePart") then
		-- (yours: only once the camera is really out and your body shows: right after V the camera is still at your head and
		-- your body hidden, weapon-hats found the eyes floating there)
		local want = r.wid == "bloodcross" and not (r.isMe and (not thirdPerson() or me:GetAttribute("TPScope") == true or rhand.LocalTransparencyModifier > 0.5))
		if want ~= (rhand:FindFirstChild("HatSpot") ~= nil) then
			AvatarArms.hatSpot(rhand, "bloodcross", if r.player then r.player.UserId else 0, r.k, want)
		end
	end
	-- (debug / tests: where each hand was sent, chest space, to check the IK landed it there)
	if r.gun and r.ch:GetAttribute("TPDebug") then
		r.gun:SetAttribute("HandR", handR)
		r.gun:SetAttribute("HandL", handL)
	end
end

-- ------------------------------------------------------------------ every frame
local lastHook = 0
local function stepAll(dt: number)
	dt = if type(dt) == "number" and dt > 0 then math.min(dt, 0.1) else 1 / 60
	local now = os.clock()
	local seen: { [Model]: boolean } = {}
	for _, ch in candidates() do
		seen[ch] = true
		local r = rigs[ch]
		if not r then
			local src = sourceOf(ch)
			if not src then continue end
			local nr = newRig(ch)
			if not nr then continue end
			rigs[ch] = nr
			r = nr
		end
		local ok, err = pcall(stepRig, r :: Rig, dt, now)
		if not ok then
			warn("[ThirdPerson] " .. ch.Name .. ": " .. tostring(err))
			pcall(release, r :: Rig)
			rigs[ch] = nil
		end
	end
	for ch, r in rigs do
		if not seen[ch] or not ch.Parent then pcall(release, r); rigs[ch] = nil end
	end
end
-- CrouchPoses calls this at the end of its own pass (after the animation and the crouch / slide bends), so this always
-- has the last word on the upper body
function TP.step(dt: number)
	lastHook = os.clock()
	stepAll(dt)
end
-- (if the crouch poses aren't there to call it, our own pass after the animation)
RunService.Stepped:Connect(function(_, dt)
	if os.clock() - lastHook > 0.25 then stepAll(dt) end
end)

-- ------------------------------------------------------------------ yours: face where you aim in third person, and
-- tell everyone else where you look
local Send: RemoteEvent? = nil -- (ThirdPersonRelay makes it when the server starts)
local sent = { p = 999, y = 999, f = -1, t = 0 }
RunService:BindToRenderStep("JankfireThirdPerson", Enum.RenderPriority.Camera.Value + 4, function(dt: number)
	local ch = me.Character
	local r = rigFor(ch)
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not ch or not hum or not root then return end
	local armed = r ~= nil and (r.gun ~= nil or r.tool ~= nil) and hum.Health > 0
	-- third person with a weapon out: your body turns to where you aim (first person already does)
	local face = armed and thirdPerson() and not hum.PlatformStand and not hum.Sit and me:GetAttribute("LoadoutOpen") ~= true
	if face then
		if hum.AutoRotate then hum.AutoRotate = false; hum:SetAttribute("TPTurned", true) end
		local look = camera.CFrame.LookVector
		local want = math.atan2(-look.X, -look.Z)
		local _, cy = root.CFrame:ToOrientation()
		local d = wrapAng(want - cy)
		if math.abs(d) > 1e-3 then
			root.CFrame = CF(root.Position) * CFrame.fromOrientation(0, cy + d * math.min(1, dt * 20), 0)
		end
	elseif hum:GetAttribute("TPTurned") then
		hum.AutoRotate = true; hum:SetAttribute("TPTurned", nil)
	end
	-- the network: pitch / yaw in degrees and the flags, when they change (at most ~12 a second, flags at once)
	if not Send then Send = Remotes:FindFirstChild("TPState") :: RemoteEvent? end
	if not armed or not Send or not r then return end
	myLook(r)
	local now = os.clock()
	local p = math.floor(math.deg(myAim.pitch) + 0.5)
	local y = math.floor(math.deg(myAim.yaw) + 0.5)
	local f = 0
	if mine.aim > 0.5 then f += FLAG_AIM end
	if now - mine.reloadT < mine.reloadDur then f += FLAG_RELOAD; if mine.empty then f += FLAG_EMPTY end end
	local gap = now - sent.t
	local moved = math.abs(p - sent.p) >= 2 or math.abs(y - sent.y) >= 3
	if (f ~= sent.f and gap > 0.04) or (moved and gap >= 1 / 12) or ((p ~= sent.p or y ~= sent.y) and gap > 0.3) then
		sent.p, sent.y, sent.f, sent.t = p, y, f, now;
		(Send :: RemoteEvent):FireServer(p, y, f)
	end
end)

-- your gun reached the server (a swap): a reload in your hands was cut by it
me.CharacterAdded:Connect(function() mine.reloadT = -10 end)

return TP
