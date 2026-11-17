--!strict
-- GRAPPLE LOOKS: how each grapple skin's rope and head are drawn (17 Nov 2026; the owner, via the main session: "Let's
-- get custom grapples again, kill effects and grapples should be gacha too!!"). The eight are the web game's
-- (shared/cosmetics.js COSMETICS.grapple; Flair.luau has their names and rarities). Client side only, and look only:
-- the ropes are the game's own Beams (the server's for other players, Move.client's for yours) and nothing here
-- touches the swing. client/GrappleSkins.client.luau picks each rope's skin; the equip screen (FlairUI) calls preview.
--
-- THE HEADS: ReplicatedStorage.JankfireGrapples.<id>, one Model each (studio-tools/GrappleImport.luau builds them from
-- the uploads that tools/roblox/grapple_heads.py made). A head is in the HEAD FRAME: its pivot is the bite (the point
-- the rope hit), -Z points into the wall, +Y up, the head lies at z >= 0. Attribute Tail = studs from the bite back to
-- where the rope ties on (the rope ends there, so it never pokes through the head). Parts named "glow" pulse (laser),
-- parts named "star" run through the rainbow (rainbow). No head model yet: the rope head stands in; no rope head
-- either: just the rope.
-- THE ROPES: LOOKS[id]. Pictures tile along the rope (TextureMode Wrap, TextureLength = studs per picture); they are
-- tools/roblox/grapple_ropes.py's (uploaded 17 Nov, ids in roblox/docs/GRAPPLES.md). A rope's colour multiplies its
-- picture: the grey ones (twist, chain, glow, ribbon) take their colour from it.
--
-- One RenderStepped for every live rope (heads follow the swing, the rope ties on at the tail, the rainbow's colours
-- and the laser's pulse), connected only while there is one.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GrappleLook = {}

export type Look = {
	width: number, -- studs across at the head end
	width0: number?, -- at the hand end (leafy and glowing ropes start thinner, out of your face)
	color: ColorSequence,
	texture: string, -- "" = plain colour
	textureLength: number, -- studs one picture covers
	textureSpeed: number,
	segments: number,
	lightEmission: number,
	lightInfluence: number,
	brightness: number,
	transparency: number,
	tail: number, -- where the rope ties on when the head model has no Tail attribute
	spin: number?, -- rad/s round the rope (the rainbow's star)
	cycle: boolean?, -- the colours run through the rainbow
	pulse: boolean?, -- a soft glow pulse (the laser)
	stretch: boolean?, -- thinner the longer it stretches, with a wobble (the sticky hand's cord)
}

-- the rope pictures (IMAGE ids, not the Decal ids: see GRAPPLES.md)
local TEX = {
	twist = "rbxassetid://128729089001963", -- grey strands (Decal 73043694393156)
	chain = "rbxassetid://107278956523683", -- grey links (Decal 81833412743656)
	candy = "rbxassetid://127006434700551", -- red and cream stripes (Decal 118442793065578)
	vine = "rbxassetid://110014939268762", -- a stem with leaves (Decal 85015828496852)
	glow = "rbxassetid://81238473856499", -- a hot core in a halo (Decal 94671855236150)
	ribbon = "rbxassetid://117284904786521", -- a soft-edged ribbon (Decal 117030152790720)
}
GrappleLook.TEX = TEX

local function cs(r: number, g: number, b: number): ColorSequence
	return ColorSequence.new(Color3.fromRGB(r, g, b))
end

GrappleLook.IDS = { "rope", "chain", "candy", "plunger", "vine", "laser", "sticky", "rainbow" }

GrappleLook.LOOKS = {
	-- brown three-strand rope (the grey strands tinted)
	rope = {
		width = 0.22, color = cs(170, 132, 92), texture = TEX.twist, textureLength = 0.75, textureSpeed = 0,
		segments = 1, lightEmission = 0, lightInfluence = 1, brightness = 1, transparency = 0, tail = 1.5,
	},
	-- steel chain: face-on rings and edge-on links
	chain = {
		width = 0.36, color = cs(200, 205, 212), texture = TEX.chain, textureLength = 0.72, textureSpeed = 0,
		segments = 1, lightEmission = 0, lightInfluence = 1, brightness = 1, transparency = 0, tail = 1.28,
	},
	-- red and cream candy stripes
	candy = {
		width = 0.24, color = cs(255, 255, 255), texture = TEX.candy, textureLength = 0.48, textureSpeed = 0,
		segments = 1, lightEmission = 0, lightInfluence = 1, brightness = 1, transparency = 0, tail = 1.6,
	},
	-- a pale cotton cord
	plunger = {
		width = 0.18, color = cs(228, 216, 188), texture = TEX.twist, textureLength = 0.6, textureSpeed = 0,
		segments = 1, lightEmission = 0, lightInfluence = 1, brightness = 1, transparency = 0, tail = 1.7,
	},
	-- a green vine with leaves, thin at your hand and full at the hook
	vine = {
		width = 0.75, width0 = 0.32, color = cs(255, 255, 255), texture = TEX.vine, textureLength = 1.5, textureSpeed = 0,
		segments = 1, lightEmission = 0, lightInfluence = 1, brightness = 1, transparency = 0, tail = 1.44,
	},
	-- a cyan beam: a hot core in a halo, soft bands running down it, pulsing
	laser = {
		width = 0.32, width0 = 0.2, color = cs(102, 220, 240), texture = TEX.glow, textureLength = 3, textureSpeed = 1.2,
		segments = 1, lightEmission = 1, lightInfluence = 0, brightness = 2, transparency = 0.05, tail = 1.22,
		pulse = true,
	},
	-- a thin see-through green cord that thins as it stretches
	sticky = {
		width = 0.16, color = cs(116, 184, 111), texture = "", textureLength = 1, textureSpeed = 0,
		segments = 1, lightEmission = 0.1, lightInfluence = 1, brightness = 1, transparency = 0.25, tail = 0.42,
		stretch = true,
	},
	-- a ribbon whose colours run through the rainbow toward the star, which spins
	rainbow = {
		width = 0.34, width0 = 0.22, color = cs(255, 255, 255), texture = TEX.ribbon, textureLength = 1, textureSpeed = 0,
		segments = 1, lightEmission = 0.6, lightInfluence = 0.2, brightness = 1.5, transparency = 0, tail = 0.33,
		cycle = true, spin = 1.7,
	},
} :: { [string]: Look }

local function lookOf(id: string): Look
	return GrappleLook.LOOKS[id] or GrappleLook.LOOKS.rope
end
GrappleLook.look = lookOf

-- the skin's head model is in the place (the plain rope is always ready)
function GrappleLook.ready(id: string): boolean
	if id == "rope" then return true end
	local lib = ReplicatedStorage:FindFirstChild("JankfireGrapples")
	return lib ~= nil and lib:FindFirstChild(id) ~= nil
end

-- the rope's own look (width, colour, picture). marks the Beam GrappleLook = id (GrappleSkins leaves a marked Beam alone)
function GrappleLook.dress(beam: Beam, id: string)
	local L = lookOf(id)
	beam.Width0 = L.width0 or L.width
	beam.Width1 = L.width
	beam.Color = L.color
	beam.Texture = L.texture
	beam.TextureMode = Enum.TextureMode.Wrap
	beam.TextureLength = L.textureLength
	beam.TextureSpeed = L.textureSpeed
	beam.Segments = L.segments
	beam.LightEmission = L.lightEmission
	beam.LightInfluence = L.lightInfluence
	beam.Brightness = L.brightness
	beam.Transparency = NumberSequence.new(L.transparency)
	beam.FaceCamera = true
	beam.CurveSize0 = 0
	beam.CurveSize1 = 0
	beam:SetAttribute("GrappleLook", if GrappleLook.LOOKS[id] then id else "rope")
end

-- ------------------------------------------------------------------------------------------------ live ropes
type Rec = {
	beam: Beam,
	look: Look,
	bite: Vector3, -- where the rope hit (the head's pivot)
	anchor: Attachment, -- the rope's own end (put back on the Beam when the head comes off)
	tie: Attachment, -- the end the rope uses while the head is on: the bite moved back by the tail
	tail: number,
	head: Model?,
	parts: { BasePart },
	offs: { CFrame }, -- each part in the head frame
	glows: { BasePart },
	glowBase: { Color3 },
	stars: { BasePart },
	from: Vector3,
	dir: Vector3,
	up: Vector3,
	t0: number,
	lastCF: CFrame?,
	shown: boolean,
	dead: boolean,
}

local live: { [Rec]: boolean } = {}
local conn: RBXScriptConnection? = nil
local moveParts: { BasePart } = {}
local moveCFs: { CFrame } = {}
local WHITE = Color3.new(1, 1, 1)

local function headFolder(): Instance
	local f = workspace:FindFirstChild("GrappleHeads")
	if not f then
		f = Instance.new("Folder")
		f.Name = "GrappleHeads" -- (made by this client: client-side only)
		f.Parent = workspace
	end
	return f :: Instance
end

-- a head's up: world up, or (a rope straight up or down) the rope's own heading
local function upFor(dir: Vector3): Vector3
	if math.abs(dir.Y) < 0.95 then
		return (Vector3.yAxis - dir * dir.Y).Unit
	end
	local flat = Vector3.new(dir.X, 0, dir.Z)
	return if flat.Magnitude > 1e-3 then flat.Unit else Vector3.zAxis
end

local function drop(rec: Rec)
	if rec.dead then return end
	rec.dead = true
	live[rec] = nil
	if rec.head then rec.head:Destroy() end
	if rec.beam.Attachment1 == rec.tie and rec.anchor.Parent then rec.beam.Attachment1 = rec.anchor end
	rec.tie:Destroy()
	if next(live) == nil and conn then
		conn:Disconnect()
		conn = nil
	end
end

-- where everything goes this frame: the head on the bite pointing along the rope, the rope tied on at the tail.
-- returns the head's CFrame and the rope's length
local function aim(rec: Rec, now: number): (CFrame, number)
	local a0 = rec.beam.Attachment0
	if a0 and a0.Parent then rec.from = a0.WorldPosition end
	local d = rec.bite - rec.from
	local len = d.Magnitude
	if len > 1e-3 then rec.dir = d / len end
	local dir = rec.dir
	local up = rec.up - dir * rec.up:Dot(dir) -- (last frame's up, kept square to the rope: no sudden roll)
	up = if up.Magnitude > 1e-3 then up.Unit else upFor(dir)
	rec.up = up
	local cf = CFrame.lookAt(rec.bite, rec.bite + dir, up)
	local spin = rec.look.spin
	if spin then cf *= CFrame.Angles(0, 0, (now - rec.t0) * spin) end
	rec.tie.WorldPosition = rec.bite - dir * math.min(rec.tail, len * 0.5)
	return cf, len
end

local function step()
	local now = os.clock()
	table.clear(moveParts)
	table.clear(moveCFs)
	for rec in live do
		local beam = rec.beam
		if not beam.Parent or not rec.anchor.Parent then -- (the rope is over: its Beam or its own end has gone)
			drop(rec)
			continue
		end
		local cf, len = aim(rec, now)
		local L = rec.look
		local head = rec.head
		if head then
			local show = beam.Enabled
			if show ~= rec.shown then
				rec.shown = show
				head.Parent = if show then headFolder() else nil
				rec.lastCF = nil
			end
			if show and (L.spin or not rec.lastCF or not cf:FuzzyEq(rec.lastCF :: CFrame, 1e-4)) then
				rec.lastCF = cf
				for i, p in rec.parts do
					table.insert(moveParts, p)
					table.insert(moveCFs, cf * rec.offs[i])
				end
			end
		end
		local t = now - rec.t0
		if L.cycle then
			-- the spectrum along the rope (one round every 40 studs), flowing toward the head; the star wears the head end's
			local hue = t * 0.3
			local span = len / 40
			local n = math.clamp(math.ceil(span * 6) + 2, 2, 20)
			local kps: { ColorSequenceKeypoint } = table.create(n)
			for k = 0, n - 1 do
				local f = k / (n - 1)
				kps[k + 1] = ColorSequenceKeypoint.new(f, Color3.fromHSV((hue - f * span) % 1, 0.6, 1))
			end
			beam.Color = ColorSequence.new(kps)
			local c = Color3.fromHSV((hue - span) % 1, 0.55, 1)
			for _, s in rec.stars do s.Color = c end
		end
		if L.pulse then
			local k = 0.5 + 0.5 * math.sin(t * 6)
			beam.Transparency = NumberSequence.new(math.min(1, L.transparency + 0.18 * (1 - k)))
			beam.Width0 = (L.width0 or L.width) * (0.94 + 0.08 * k)
			beam.Width1 = L.width * (0.94 + 0.08 * k)
			for i, g in rec.glows do g.Color = rec.glowBase[i]:Lerp(WHITE, 0.35 * k) end
		end
		if L.stretch then
			local k = math.clamp(math.sqrt(15 / math.max(len, 1)), 0.45, 1.4) * (1 + math.sin(t * 9) * 0.06)
			beam.Width0 = (L.width0 or L.width) * k
			beam.Width1 = L.width * k
		end
	end
	if #moveParts > 0 then
		workspace:BulkMoveTo(moveParts, moveCFs, Enum.BulkMoveMode.FireCFrameChanged)
	end
end

-- put the skin's head on a rope (a Beam whose Attachment1 is the bite) and keep it there while the rope lives.
-- returns a cleanup (also run by itself when the Beam goes)
function GrappleLook.attach(beam: Beam, id: string): () -> ()
	local a1 = beam.Attachment1
	if not a1 then return function() end end
	local L = lookOf(id)
	local lib = ReplicatedStorage:FindFirstChild("JankfireGrapples")
	local tpl = lib and (lib:FindFirstChild(id) or lib:FindFirstChild("rope"))
	local bite = a1.WorldPosition
	local a0 = beam.Attachment0
	local from = if a0 then a0.WorldPosition else bite + Vector3.yAxis
	local d = bite - from
	local dir = if d.Magnitude > 1e-3 then d.Unit else -Vector3.yAxis
	local tie = Instance.new("Attachment")
	tie.Name = "GrappleTie"
	tie.WorldPosition = bite
	local rec: Rec = {
		beam = beam, look = L, bite = bite, anchor = a1, tie = tie, tail = 0, head = nil,
		parts = {}, offs = {}, glows = {}, glowBase = {}, stars = {},
		from = from, dir = dir, up = upFor(dir), t0 = os.clock(), lastCF = nil, shown = false, dead = false,
	}
	if tpl and tpl:IsA("Model") then
		local head = tpl:Clone()
		local pivot = head:GetPivot()
		for _, x in head:GetDescendants() do
			if x:IsA("BasePart") then
				x.Anchored = true
				x.CanCollide = false
				x.CanQuery = false
				x.CanTouch = false
				x.Massless = true
				table.insert(rec.parts, x)
				table.insert(rec.offs, pivot:ToObjectSpace(x.CFrame))
				if x.Name == "glow" then
					table.insert(rec.glows, x)
					table.insert(rec.glowBase, x.Color)
				elseif x.Name == "star" then
					table.insert(rec.stars, x)
				end
			elseif x:IsA("Script") or x:IsA("LocalScript") then
				x:Destroy()
			end
		end
		local tt = tpl:GetAttribute("Tail")
		rec.tail = if type(tt) == "number" then tt elseif tpl.Name == id then L.tail else lookOf("rope").tail
		rec.head = head
		local cf = aim(rec, os.clock())
		head:PivotTo(cf)
		rec.lastCF = cf
		rec.shown = beam.Enabled
		if rec.shown then head.Parent = headFolder() end
	end
	tie.WorldPosition = bite - dir * math.min(rec.tail, d.Magnitude * 0.5)
	tie.Parent = workspace.Terrain
	beam.Attachment1 = tie
	live[rec] = true
	if not conn then conn = RunService.RenderStepped:Connect(step) end
	return function() drop(rec) end
end

-- a rope from a0 to a point in the air with the skin on it, for the equip screen's client-only stand-in. returns a
-- cleanup that takes the lot away
function GrappleLook.preview(a0: Attachment, worldPoint: Vector3, id: string): () -> ()
	local a1 = Instance.new("Attachment")
	a1.Name = "GrapplePreviewPoint"
	a1.WorldPosition = worldPoint
	a1.Parent = workspace.Terrain
	local b = Instance.new("Beam")
	b.Name = "GrapplePreview"
	b.Attachment0 = a0
	b.Attachment1 = a1
	GrappleLook.dress(b, id) -- (marked, so GrappleSkins leaves it alone)
	b.Parent = a0.Parent or workspace.Terrain
	local stop = GrappleLook.attach(b, id)
	return function()
		stop()
		b:Destroy()
		a1:Destroy()
	end
end

return GrappleLook
