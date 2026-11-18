--!strict
-- your own Roblox avatar's hands and forearms in first person: the hand and lower-arm meshes cloned off your character
-- (so it is always YOUR body: blocky, slim, anything), scaled to the weapon and put on it by the hold table
-- (Holds.luau, written from tools/roblox/holds.json). used by the weapons' Viewmodel and the Shredder's viewmodel.
--
-- how an arm is placed, every frame (AvatarArms.aim):
--   * the hand grips at its own GRIP ATTACHMENT, the spot and the turn Roblox itself uses for a held Tool, so the
--     grip is right for any avatar's hand shape: what it holds (a pistol grip, the katana's hilt, a handguard, a
--     magazine) runs through the fist, thumb side up the handle or toward the muzzle
--   * the hand turns about that handle until its wrist faces your elbow, a spot fixed in camera space
--   * the forearm is NOT glued to the weapon: it runs from the wrist to that elbow, so an arm never sweeps across the
--     screen when the weapon rolls, swings or twirls
--   * limbs are lined up by their rig attachments (grip, wrist, elbow), not by their boxes: on many bodies the arm
--     meshes lie slanted inside their parts, and a box-aligned forearm showed as a wedge
--   * a thing too big to grip (the Shredder's body, a reload prop's foot) is held from UNDER: the hand's palm side up
--     against it, the arm on its line to the elbow
--
-- THE LOOK is a switch (the module's "Look" attribute, if set, wins over LOOK):
--   "kit" (default): your arm shapes in the game's glove and sleeve colours, so the hands look the same whatever the
--     avatar wears (a pale or untextured arm blew out to a plain white shape under the lamps)
--   "avatar": your skin tone and your shirt's sleeves, as on your body
-- (a modelled four-finger glove was tried on 2026-11-15 and taken out the same day: the owner wants Roblox's own hands)
local Players = game:GetService("Players")
local Holds = require(script.Parent:WaitForChild("Holds")) :: any

local AvatarArms = {}

AvatarArms.LOOK = "kit" -- "kit" | "avatar"
function AvatarArms.look(): string
	local a = script:GetAttribute("Look")
	return if a == "kit" or a == "avatar" then a else AvatarArms.LOOK
end
-- one charcoal family. the glove is clearly LIGHTER than the guns (a glove of a dark gun's own value vanished into
-- it: the Revolver looked unheld) and the sleeve clearly DARKER than the glove: the lamps hit the top of a forearm
-- full on, and anything lighter showed as a pale cone propping up the gun. (judge rounds, 2026-11-15)
AvatarArms.KIT = {
	-- (judge rounds on the hold: 46,48,54 merged into dark guns; 54,56,63 read as grey clay; a 20,21,24 sleeve was a
	-- flat black cut-out and 22,23,27 on a long arm caught a glossy stripe. this pair sits between them)
	glove = Color3.fromRGB(50, 52, 58),
	sleeve = Color3.fromRGB(36, 38, 43), -- (judge 3: 26,28,32 vanished against the black guns)
	-- tried in the hall, this close to the eye: Plastic and Rubber speckle, Fabric crumples, Leather turns a hand into
	-- a rock, and an unlit sleeve (Neon in a dark colour) is a flat black bar once the forearm crosses the screen.
	-- both are SmoothPlastic: clean, and the lamps still model the arm's faces
	material = Enum.Material.SmoothPlastic,
	sleeveMaterial = Enum.Material.SmoothPlastic,
}

-- a zombie's hands (Infection: the player attribute ModeZombie, Modes.luau): this green, the Zombie Claw's own since
-- 17 Nov. the owner, 18 Nov 2026: "Blood cross and zombie hand can just be our normal hand!! Zombie will just turn it
-- green!!": the claw is your own hand (no model on it), and a zombie's hands go green whatever they hold, back the
-- moment ModeZombie goes (zombieSync, below). everyone else sees the body's own ZombieTint highlight
AvatarArms.ZOMBIE = Color3.fromRGB(111, 154, 58)
local function zombie(): boolean
	local lp = Players.LocalPlayer
	return lp ~= nil and lp:GetAttribute("ModeZombie") == true
end

AvatarArms.STUDS = 3 -- studs per metre (the game's scale: Weapons.S)
AvatarArms.HAND = 0.115 -- the hand across, metres, at a hold's size 1 (the hold table sizes it to each weapon)
AvatarArms.FORE_L = 0.62 -- forearm length, metres: long enough to leave the screen, so no elbow end ever shows
AvatarArms.SLEEVE = 1.6 -- the forearm's thickness against the hand's own scale (0.9 and 1.1 read as a pole under a ball; 1.35 still a thin pole once the guns sat further off in the Rivals layout)
AvatarArms.SINK = 0.12 -- held from under: the thing sinks this far (of the hand's thickness) into the palm
AvatarArms.PAST = 0.18 -- ... and the fingers reach this far (of the hand's length) past it

local UNDER = { palm = true } -- (the hold table's poses that hold from under; every other pose is a grip)
local WHOLE = { hand = true } -- (... and the one where the hand IS the weapon, the Zombie Claw: placed whole, no grip)

type Arm = {
	side: string, root: BasePart, rel: CFrame, under: boolean, whole: boolean, elbow: Vector3, turn: number,
	hand: BasePart, fore: BasePart,
	gripInv: CFrame, -- the hand's grip attachment, inverted (part space, sized)
	wrist: Vector3, -- the hand's wrist joint (part space, sized)
	mid: CFrame, -- under holds: a frame at the hand's middle, its Y to the wrist
	foreInv: CFrame, -- the forearm's own frame at its wrist joint (Y to the elbow), inverted
	thick: number, long: number, ang: number,
	over: CFrame?, mix: number, overUnder: boolean,
	elbowTo: Vector3?, elbowMix: number, -- (AvatarArms.elbowAt: the elbow spot moved for a pose, the Bow's draw)
	away: boolean, idle: boolean?, -- (a hand that waits off screen: hidden while nothing calls it)
	base: { color: Color3, material: Enum.Material, name: string }?, -- (the hand as dressed, for zombieSync)
}
-- (a plain table, cleared when the arms are destroyed. NOT a weak one: an Instance's Luau handle can be collected
-- while the Instance lives on, and a weak key went with it: the forearms froze a moment after every swap)
local live: { [Instance]: { Arm } } = {}

local KEEP = { SurfaceAppearance = true, SpecialMesh = true }
local function limb(src: BasePart): BasePart
	local c = src:Clone()
	for _, d in c:GetChildren() do if not KEEP[d.ClassName] then d:Destroy() end end
	c.Anchored = true; c.CanCollide = false; c.CanQuery = false; c.CanTouch = false; c.CastShadow = false
	c.Massless = true; c.Transparency = 0
	return c
end

-- a piece of the kit: the limb's own shape in one flat colour (its skin picture and surface come off)
local function dress(p: BasePart, color: Color3, material: Enum.Material)
	for _, d in p:GetChildren() do if d:IsA("SurfaceAppearance") then d:Destroy() end end
	if p:IsA("MeshPart") then p.TextureID = "" end
	p.Color = color; p.Material = material; p.Reflectance = 0
end

local function spot(part: BasePart, name: string): Vector3?
	local a = part:FindFirstChild(name)
	return if a and a:IsA("Attachment") then a.Position else nil
end

-- (the hold session, 18 Nov 2026; the owner: "your hand r6 or r15") a blocky R6 body has one part per arm, no hand or
-- forearm: its hand and forearm are cut from that arm (its colour and surface), a hand a third of the arm long and a
-- forearm of the rest, with the joints an R15 limb carries, so everything below holds them like any other
local function r6Parts(arm: BasePart, side: string): (BasePart, BasePart)
	local function piece(size: Vector3): Part
		local p = Instance.new("Part")
		p.Size = size; p.Color = arm.Color; p.Material = arm.Material; p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
		return p
	end
	local s = arm.Size
	local hand = piece(Vector3.new(s.X, s.Y * 0.3, s.Z))
	hand.Name = side .. "Hand"
	local w = Instance.new("Attachment"); w.Name = side .. "WristRigAttachment"; w.Position = Vector3.new(0, hand.Size.Y / 2, 0); w.Parent = hand
	local g = Instance.new("Attachment"); g.Name = side .. "GripAttachment"; g.CFrame = CFrame.Angles(-math.pi / 2, 0, 0); g.Parent = hand
	local fore = piece(Vector3.new(s.X * 0.95, s.Y * 0.6, s.Z * 0.95))
	fore.Name = side .. "LowerArm"
	local fw = Instance.new("Attachment"); fw.Name = side .. "WristRigAttachment"; fw.Position = Vector3.new(0, -fore.Size.Y / 2, 0); fw.Parent = fore
	local fe = Instance.new("Attachment"); fe.Name = side .. "ElbowRigAttachment"; fe.Position = Vector3.new(0, fore.Size.Y / 2, 0); fe.Parent = fore
	return hand, fore
end
-- a body's hand and forearm for a side: its own (R15), or cut from its arm (R6)
local function srcOf(ch: Model, side: string): (BasePart?, BasePart?)
	local h, f = ch:FindFirstChild(side .. "Hand"), ch:FindFirstChild(side .. "LowerArm")
	if h and f and h:IsA("BasePart") and f:IsA("BasePart") then return h, f end
	local arm = ch:FindFirstChild(side .. " Arm")
	if arm and arm:IsA("BasePart") then return r6Parts(arm, side) end
	return nil, nil
end

-- a limb's own frame at a joint: its Y along the limb toward the elbow end, its X the part's X squared to that
local function basisAt(joint: Vector3, toElbow: Vector3): CFrame
	local y = if toElbow.Magnitude > 1e-4 then toElbow.Unit else Vector3.yAxis
	local x = Vector3.xAxis - y * y.X
	x = if x.Magnitude > 1e-3 then x.Unit else Vector3.zAxis
	return CFrame.fromMatrix(joint, x, y, x:Cross(y))
end

-- ---- the hand that IS the weapon (pose "hand": the Zombie Claw). its model is only what goes on a hand: the nails
-- (pieces named nail_*) and the cuff (cuff_*), built round a reference hand (REF, file metres: its middle at the
-- hold's spot, palm down, fingers forward, thumb to the left). every body's hand is another shape (a blocky hand is a
-- slab a third as long as it is wide), so the nails go onto THIS hand's fingertip end and the cuff onto its wrist,
-- spread to its width and thickness (the nails grow with its width only; the cuff stretches round it). handRel =
-- the hand part's frame against the weapon's root, size = the hand part's size, wrist = its wrist joint (part
-- space), all in studs. the hand's own axes: x through it (palm to back), y to the wrist, z across. the pieces
-- remember how they were built (attributes FitRel / FitSize), so fitting again starts from there. first and third
-- person both use it
AvatarArms.REF = { wide = 0.115, thick = 0.06, long = 0.10 }
local FIT = { nail = "tips", cuff = "wrist" }
function AvatarArms.fitOver(root: BasePart, k: number, handRel: CFrame, size: Vector3, wrist: Vector3?)
	local m = root.Parent
	if not m then return end
	local R = AvatarArms.REF
	local sw = size.Z / (R.wide * k) -- (across)
	local st = size.X / (R.thick * k) -- (through: most avatars' hands are far thicker than the reference)
	local s3 = Vector3.new(st, sw, sw) -- (per hand axis: spots spread with the hand; the cuff stretches with it)
	local spots = {
		tips = { from = Vector3.new(0, -R.long / 2 * k, 0), to = Vector3.new(0, -size.Y / 2, 0), stretch = false },
		wrist = { from = Vector3.new(0, R.long / 2 * k, 0), to = wrist or Vector3.new(0, size.Y * 0.42, 0), stretch = true },
	}
	-- (a piece's size along one of its own axes, v in the hand's axes: the hand's stretch along it)
	local function along(v: Vector3): number return math.sqrt((v.X * st) ^ 2 + (v.Y * sw) ^ 2 + (v.Z * sw) ^ 2) end
	for _, d in m:GetDescendants() do
		if not d:IsA("BasePart") or d == root or d:FindFirstAncestor("AvatarArms") then continue end
		local n = string.lower(d.Name)
		local g = nil
		for pre, grp in FIT do
			if string.sub(n, 1, #pre) == pre then g = spots[grp]; break end
		end
		if not g then continue end
		local rel0, size0 = d:GetAttribute("FitRel"), d:GetAttribute("FitSize")
		if typeof(rel0) ~= "CFrame" or typeof(size0) ~= "Vector3" then
			rel0, size0 = root.CFrame:ToObjectSpace(d.CFrame), d.Size
			d:SetAttribute("FitRel", rel0); d:SetAttribute("FitSize", size0)
		end
		local inH = handRel:ToObjectSpace(rel0 :: CFrame) -- (the piece against the hand's middle, the hand's axes)
		local wc = d:FindFirstChildOfClass("WeldConstraint")
		if wc then wc.Enabled = false end -- (moved alone, then welded where it now is)
		-- the nails keep their shape (grown with the hand's width); the cuff stretches round this hand
		local Rr = inH.Rotation
		d.Size = (size0 :: Vector3) * (if g.stretch then Vector3.new(along(Rr.XVector), along(Rr.YVector), along(Rr.ZVector)) else Vector3.one * sw)
		d.CFrame = root.CFrame * handRel * CFrame.new(g.to + (inH.Position - g.from) * s3) * Rr
		if wc then wc.Enabled = true end
	end
end

-- (the hold session, 18 Nov 2026) the Blood Cross's hat spot, agreed with weapon-hats: an Attachment "HatSpot" on the
-- hand part (tag GunHatSpot; attributes Weapon, Owner = the UserId, K = studs per metre of the weapon in that view),
-- and GunHats welds the player's hat for that weapon there. on top of the hand in its finger-gun pose: the thumb side,
-- just behind the knuckles, +Y out of the top, -Z toward the fingertips (the hand's own axes: x palm to back, y to the
-- wrist, z across, the thumb at -z). first person puts it on the AvatarArms hand, third person on the body's own right
-- hand; on = false takes it off
local CollectionService = game:GetService("CollectionService")
function AvatarArms.hatSpot(hand: BasePart, wid: string, owner: number, k: number, on: boolean)
	local a = hand:FindFirstChild("HatSpot")
	if not on then
		if a then a:Destroy() end
		return
	end
	if a then return end
	local s = hand.Size
	local at = Instance.new("Attachment")
	at.Name = "HatSpot"
	at.CFrame = CFrame.fromMatrix(Vector3.new(s.X * 0.15, -s.Y * 0.2, -s.Z / 2), Vector3.xAxis, -Vector3.zAxis)
	at:SetAttribute("Weapon", wid); at:SetAttribute("Owner", owner); at:SetAttribute("K", k)
	at.Parent = hand
	CollectionService:AddTag(at, "GunHatSpot")
end

-- a weapon's hand rows, a skin's own where it has them (the knife's spoon look holds its handle further back)
function AvatarArms.rows(wid: string, skin: string?): any
	local rows = Holds.holds[wid]
	local sk = rows and skin and rows.skins and rows.skins[skin]
	return sk or rows
end

-- the arms for a weapon, under `parent`, held as the hold table says. root = the weapon's root (its frame the
-- weapon's own: -Z forward, +Y up), k = studs per metre of the weapon's file, frame = the weapon's frame against root
-- if root is not it (the Shredder's handle), scale = the viewmodel's size (the hands grow with the weapon). false if
-- your character isn't ready or the weapon has no row
function AvatarArms.hold(parent: Instance, root: BasePart, wid: string, k: number, frame: CFrame?, scale: number?, skin: string?): boolean
	local ch = Players.LocalPlayer and Players.LocalPlayer.Character
	local rows = AvatarArms.rows(wid, skin)
	if not ch or not rows or not ch:FindFirstChildOfClass("Humanoid") then return false end
	local src: { [string]: { BasePart } } = {}
	for _, side in { "Right", "Left" } do
		if not rows[side] then continue end
		local h, f = srcOf(ch, side)
		if not h or not f then return false end
		src[side] = { h, f }
	end
	local kit = AvatarArms.look() == "kit"
	local arms = Instance.new("Model")
	arms.Name = "AvatarArms"
	if not kit then
		-- (a Humanoid in the model makes the Shirt and BodyColors show on the limbs, as they do on your body)
		local hum = Instance.new("Humanoid")
		hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
		hum.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
		hum.RigType = Enum.HumanoidRigType.R15
		hum.RequiresNeck = false; hum.BreakJointsOnDeath = false
		pcall(function() (hum :: any).EvaluateStateMachine = false end)
		hum.Parent = arms
		for _, c in ch:GetChildren() do
			if c:IsA("Shirt") or c:IsA("BodyColors") then c:Clone().Parent = arms end
		end
	end
	local S = AvatarArms.STUDS
	local list: { Arm } = {}
	for _, side in { "Right", "Left" } do
		local row = rows[side]
		if not row then continue end
		local srcHand, srcFore = src[side][1], src[side][2]
		local hand, fore = limb(srcHand), limb(srcFore)
		-- the hand keeps its shape; the forearm keeps its section (a little slimmer) and is drawn out to leave the screen
		local f = AvatarArms.HAND * S * row.size * (scale or 1) / math.max(srcHand.Size.X, srcHand.Size.Z)
		local fy = AvatarArms.FORE_L * S / srcFore.Size.Y
		local fs = Vector3.new(f * AvatarArms.SLEEVE, fy, f * AvatarArms.SLEEVE)
		hand.Size = srcHand.Size * f
		fore.Size = srcFore.Size * fs
		-- the joints, from the rig (a blocky body's are on its middle line; many others' are not)
		local hw = (spot(srcHand, side .. "WristRigAttachment") or Vector3.new(0, srcHand.Size.Y * 0.42, 0)) * f
		local fw = (spot(srcFore, side .. "WristRigAttachment") or Vector3.new(0, -srcFore.Size.Y / 2, 0)) * fs
		local fe = (spot(srcFore, side .. "ElbowRigAttachment") or Vector3.new(0, srcFore.Size.Y / 2, 0)) * fs
		-- the grip: where a Tool's handle sits in this hand, and how it is turned (its Y runs up the handle)
		local ga = srcHand:FindFirstChild(side .. "GripAttachment")
		local grip = if ga and ga:IsA("Attachment") then ga.CFrame.Rotation + ga.Position * f
			else CFrame.Angles(-math.pi / 2, 0, 0) + Vector3.new(0, -srcHand.Size.Y * 0.2, 0) * f
		-- (along the handle the hand sits on its own middle: some rigs put the attachment at the fist's edge)
		local along = grip.YVector
		grip -= along * grip.Position:Dot(along)
		if kit then
			local K = AvatarArms.KIT
			dress(hand, K.glove, K.material)
			dress(fore, K.sleeve, K.sleeveMaterial)
		end
		-- a tinted hand (a row's own tint; a zombie's green) in either look; named apart so your body colours never
		-- repaint it. what it was dressed as stays on its Arm, for zombieSync
		if row.tint then dress(hand, row.tint, AvatarArms.KIT.material) end
		hand.Name = side .. (if row.tint then "HandTint" else "Hand"); fore.Name = side .. "LowerArm"
		local base = { color = hand.Color, material = hand.Material, name = hand.Name }
		if zombie() then dress(hand, AvatarArms.ZOMBIE, AvatarArms.KIT.material); hand.Name = side .. "HandTint" end
		hand.Parent = arms; fore.Parent = arms
		local whole = WHOLE[row.pose] == true
		if whole then
			-- the weapon is only what goes on this hand (nails, a cuff): fitted to its shape now, before it is placed
			AvatarArms.fitOver(root, k, (frame or CFrame.identity) * CFrame.new(row.at * k) * CFrame.fromEulerAnglesXYZ(row.rot.X, row.rot.Y, row.rot.Z), hand.Size, hw)
		end
		table.insert(list, {
			side = side, root = root, under = UNDER[row.pose] == true, whole = whole,
			elbow = row.elbow or Holds.elbow[side], turn = row.turn or 0,
			rel = (frame or CFrame.identity) * CFrame.new(row.at * k) * CFrame.fromEulerAnglesXYZ(row.rot.X, row.rot.Y, row.rot.Z),
			hand = hand, fore = fore,
			gripInv = grip:Inverse(), wrist = hw, mid = basisAt(Vector3.zero, hw), foreInv = basisAt(fw, fe - fw):Inverse(),
			thick = hand.Size.X, long = hand.Size.Y, ang = 0, mix = 0, overUnder = false, elbowMix = 0, away = row.away == true,
			base = base,
		})
	end
	if #list == 0 then return false end
	local old = parent:FindFirstChild("AvatarArms")
	if old then old:Destroy() end
	live[arms] = list
	arms.Destroying:Connect(function() live[arms] = nil end)
	arms.Parent = parent
	AvatarArms.aim(parent, (workspace.CurrentCamera :: Camera).CFrame)
	return true
end

-- where a hand's hold sits against the weapon's root, and what kind it is (for a caller that sends the hand elsewhere)
function AvatarArms.holdFrame(wid: string, side: string, k: number, frame: CFrame?, skin: string?): CFrame?
	local rows = AvatarArms.rows(wid, skin)
	local row = rows and rows[side]
	if not row then return nil end
	return (frame or CFrame.identity) * CFrame.new(row.at * k) * CFrame.fromEulerAnglesXYZ(row.rot.X, row.rot.Y, row.rot.Z)
end
function AvatarArms.poseOf(wid: string, side: string, skin: string?): string?
	local rows = AvatarArms.rows(wid, skin)
	return if rows and rows[side] then rows[side].pose else nil
end

-- send a hand somewhere other than its hold: `to` = a frame in the world (nil = back on the weapon), mix = how far the
-- hand has gone there (0 to 1). a grip: the frame's Y runs up the thing, through the fist. under = true: its position
-- is the thing's underside and its Y points up into it. set it every frame it applies, before AvatarArms.aim
function AvatarArms.override(parent: Instance, side: string, to: CFrame?, mix: number, under: boolean?)
	local arms = parent:FindFirstChild("AvatarArms")
	local list = arms and live[arms]
	if not list then return end
	for _, a in list do
		if a.side == side then
			a.over = to; a.mix = if to then math.clamp(mix, 0, 1) else 0; a.overUnder = under == true
		end
	end
end

-- move an arm's elbow spot (camera space, metres; nil = its row's own) part of the way (mix 0 to 1): the Bow's draw
-- puts the bow arm's elbow out along the straight arm and the drawing arm's behind you. set it every frame it applies
function AvatarArms.elbowAt(parent: Instance, side: string, to: Vector3?, mix: number)
	local arms = parent:FindFirstChild("AvatarArms")
	local list = arms and live[arms]
	if not list then return end
	for _, a in list do
		if a.side == side then a.elbowTo = to; a.elbowMix = if to then math.clamp(mix, 0, 1) else 0 end
	end
end

-- every frame, after the weapon (and whatever the off hand is on) is placed
function AvatarArms.aim(parent: Instance, cam: CFrame)
	local arms = parent:FindFirstChild("AvatarArms")
	local list = arms and live[arms]
	if not list then return end
	local S = AvatarArms.STUDS
	for _, a in list do
		local F = a.root.CFrame * a.rel -- the hold's frame, in the world
		local under = a.under
		if a.over and a.mix > 0 then
			F = F:Lerp(a.over, a.mix)
			if a.mix > 0.5 then under = a.overUnder end
		end
		local eSpot = if a.elbowTo and a.elbowMix > 0 then a.elbow:Lerp(a.elbowTo, a.elbowMix) else a.elbow
		local elbow = cam:PointToWorldSpace(eSpot * S)
		local hand: CFrame
		if under then
			-- the arm on its line to the elbow, the palm side up into the thing as far as that line allows
			local to = elbow - F.Position
			local Y = if to.Magnitude > 1e-3 then to.Unit else -cam.LookVector
			local n = F.YVector
			local P = n - Y * n:Dot(Y)
			P = if P.Magnitude > 1e-3 then P.Unit else cam.UpVector
			local X = if a.side == "Right" then -P else P
			local at = F.Position - P * a.thick * (0.5 - AvatarArms.SINK) - Y * a.long * AvatarArms.PAST
			hand = CFrame.fromMatrix(at, X, Y, X:Cross(Y)) * a.mid:Inverse()
		elseif a.whole then
			hand = F -- (the hand's own frame: the row's turn already lines its axes up)
		else
			-- the grip on the handle, turned about it until the wrist faces the elbow
			local w = a.gripInv * a.wrist -- (the wrist, seen from the grip)
			local e = F:PointToObjectSpace(elbow)
			if w.X * w.X + w.Z * w.Z > 1e-6 and e.X * e.X + e.Z * e.Z > 1e-6 then
				a.ang = math.atan2(e.X, e.Z) - math.atan2(w.X, w.Z)
			end
			hand = F * CFrame.Angles(0, a.ang + a.turn, 0) * a.gripInv
		end
		a.hand.CFrame = hand
		-- the forearm from the wrist to the elbow, its faces carrying on from the hand's
		local wrist = hand:PointToWorldSpace(a.wrist)
		local to = elbow - wrist
		local Y = if to.Magnitude > 1e-3 then to.Unit else hand.YVector
		local X = hand.XVector - Y * hand.XVector:Dot(Y)
		X = if X.Magnitude > 1e-3 then X.Unit else hand.ZVector:Cross(Y).Unit
		a.fore.CFrame = CFrame.fromMatrix(wrist, X, Y, X:Cross(Y)) * a.foreInv
		-- a hand that waits off screen (a one-handed gun's left: away) is hidden until something calls it. the weapon's
		-- own code hides any piece with the Hide attribute every frame (Arsenal), so it is set only when it changes
		if a.away then
			local idle = not (a.over ~= nil and a.mix > 0.001)
			if idle ~= a.idle then
				a.idle = idle
				a.hand:SetAttribute("Hide", if idle then true else nil)
				a.fore:SetAttribute("Hide", if idle then true else nil)
			end
		end
	end
end

-- zombieSync: ModeZombie on or off while arms are out: their hands go green, or back to how they were dressed
if Players.LocalPlayer then
	Players.LocalPlayer:GetAttributeChangedSignal("ModeZombie"):Connect(function()
		local on = zombie()
		for _, list in live do
			for _, a in list do
				local b = a.base
				if not b or not a.hand.Parent then continue end
				if on then
					dress(a.hand, AvatarArms.ZOMBIE, AvatarArms.KIT.material); a.hand.Name = a.side .. "HandTint"
				else
					a.hand.Color, a.hand.Material, a.hand.Name = b.color, b.material, b.name
				end
			end
		end
	end)
end

return AvatarArms
