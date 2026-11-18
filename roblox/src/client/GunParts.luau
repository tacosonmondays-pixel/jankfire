--!strict
-- the pieces of a gun that move in your hands (batch 3): mags that drop and come back, charging handles, the pump,
-- the bolt, the Yeehaw's lever and hammer, the Belt Sander's feed cover, belt and glowing barrel, Plan B's slide, the
-- Revolver's cylinder and hammer, Half a Shotgun breaking open, and the whole-gun twirls (lever spin-cock, the
-- Revolver round your finger). the web game moves named nodes of the Blender model (public/js/rifles.js, sidearms.js,
-- reloads.js, glbkit.js); here every piece of the viewmodel hangs off the root on a Weld this module drives, and a
-- piece knows its node by its name ("mag_wzB__ar_mag" hangs off "mag"). where a node turns and how far it goes is in
-- the gun's row (Weapons mdl.parts); the timings are the clips' `ch` channels (Reloads.luau, generated).
local GunParts = {}

type Piece = { part: BasePart, weld: Weld, rest: CFrame, node: string, last: CFrame?, hidden: boolean }
export type State = {
	root: BasePart, k: number, parts: { [string]: any }, all: { Piece }, nodes: { [string]: { Piece } },
	cylA: number, cylTo: number, hamT: number, kickT: number, heat: number, heatPiece: BasePart?, heatShown: number,
	jarShow: number?, jarBob: number?,
	-- (weapons batch A) the Minigun's barrels: their turn and how fast; whose gun (nil = your viewmodel); the Water
	-- Pistol's tank as shown (0..1, eased) and each tank piece's full size
	barA: number?, spinV: number?, owner: Player?, waterShow: number?, waterSize: { [BasePart]: Vector3 }?,
	-- (the Scythe's two forms) each moving node's offset to where it sits in the other form (root space), the switch's
	-- length; and whether whose gun this is has been looked up (a third-person copy is parented after attach)
	form: { [string]: CFrame }?, formTime: number?, ownerSeen: boolean?,
	shotT: number?, -- (weapons batch C) when it last fired: the round in the muzzle is gone till it's refilled
}
-- your own last form switch (os.clock: Arsenal sets it); anyone else's is their FormT attribute (server time, Combat)
GunParts.myFormT = -math.huge
-- your own Minigun's spin, 0..1 (Arsenal sets it every frame); anyone else's comes from their Spin attribute
GunParts.mySpin = 0
export type Ctx = { clip: string?, t: number, anims: any, ammo: number, mag: number, reloading: boolean, now: number, firedT: number }

local function nodeOf(name: string): string
	local base = string.match(name, "^(.-)__") or name
	return (string.gsub(base, "_wz%a+$", ""))
end

-- every piece of the gun onto a Weld (call it before the hands go on: they stay glued to the root and never twirl)
function GunParts.attach(m: Model, root: BasePart, k: number, parts: { [string]: any }?): State?
	if not parts then return nil end
	local st: State = {
		root = root, k = k, parts = parts, all = {}, nodes = {},
		cylA = 0, cylTo = 0, hamT = 1, kickT = 1, heat = 0, heatPiece = nil, heatShown = -1,
	}
	for _, c in m:GetChildren() do
		if not c:IsA("BasePart") or c == root then continue end
		local wc = c:FindFirstChildOfClass("WeldConstraint")
		if wc then wc:Destroy() end
		local rest = root.CFrame:ToObjectSpace(c.CFrame)
		local wd = Instance.new("Weld")
		wd.Part0 = root; wd.Part1 = c; wd.C0 = rest; wd.Parent = c
		local piece: Piece = { part = c, weld = wd, rest = rest, node = nodeOf(c.Name), last = nil, hidden = false }
		table.insert(st.all, piece)
		local list = st.nodes[piece.node] or {}
		st.nodes[piece.node] = list
		table.insert(list, piece)
		if parts.heat and string.find(c.Name, parts.heat.piece, 1, true) then st.heatPiece = c end
	end
	st.owner = game:GetService("Players"):GetPlayerFromCharacter(m.Parent)
	-- (a two-form weapon, the Scythe: build the other form's model once and measure where each moving node sits in it.
	-- the switch eases from there to here, so the code stand-in and the kit model both just work if the pieces share
	-- their node names in the two models)
	local F = parts.form
	if F and type(F.to) == "string" and type(F.nodes) == "table" then
		local ok, WM = pcall(require, game:GetService("ReplicatedStorage"):WaitForChild("Jankfire"):WaitForChild("WeaponModels"))
		local other = if ok then (WM :: any).build(F.to, k) else nil
		if other and other.PrimaryPart then
			local offs: { [string]: CFrame } = {}
			for _, node in F.nodes do
				local mine = st.nodes[node]
				if not mine or not mine[1] then continue end
				for _, c in other:GetChildren() do
					if c:IsA("BasePart") and c ~= other.PrimaryPart and nodeOf(c.Name) == node then
						offs[node] = other.PrimaryPart.CFrame:ToObjectSpace(c.CFrame) * mine[1].rest:Inverse()
						break
					end
				end
			end
			st.form, st.formTime = offs, tonumber(F.time) or 0.45
		end
		if other then other:Destroy() end
	end
	return st
end

-- a shot: the cylinder turns a chamber, the hammer falls, the slide kicks, the barrel warms
function GunParts.shot(st: State, w: any)
	local cyl = st.parts.cylinder
	if cyl then st.cylTo += cyl.step or math.pi / 3 end
	st.hamT, st.kickT = 0, 0
	st.shotT = os.clock()
	if w.heatUp then st.heat = math.min(1, st.heat + w.heatUp / (w.rate or 1)) end
end

-- a channel of the clip that's playing, the web game's sampleCh: smooth between its keys, held outside them
local function sample(c: Ctx, ch: string): { number }?
	local a = c.clip and c.anims[c.clip]
	local k = a and a.ch and a.ch[ch]
	if not k then return nil end
	local t = c.t
	local n = #k
	local function vals(row: { number }): { number }
		local out = table.create(#row - 1)
		for i = 2, #row do out[i - 1] = row[i] end
		return out
	end
	if t <= k[1][1] then return vals(k[1]) end
	if t >= k[n][1] then return vals(k[n]) end
	local i = 1
	while i < n - 1 and t >= k[i + 1][1] do i += 1 end
	local k0, k1 = k[i], k[i + 1]
	local u = math.clamp((t - k0[1]) / math.max(1e-6, k1[1] - k0[1]), 0, 1)
	u = u * u * (3 - 2 * u)
	local out = table.create(#k0 - 1)
	for j = 2, #k0 do out[j - 1] = k0[j] + ((k1[j] or k0[j]) - k0[j]) * u end
	return out
end

local function about(pivot: Vector3, rot: CFrame): CFrame
	return CFrame.new(pivot) * rot * CFrame.new(-pivot)
end
local function rx(a: number): CFrame return CFrame.Angles(a, 0, 0) end
local function rz(a: number): CFrame return CFrame.Angles(0, 0, a) end

-- the Belt Sander's barrel: dark -> red -> orange -> white-hot (public/js/rifles.js heatColor)
local C_DARK, C_RED, C_OR, C_HOT = Color3.fromRGB(42, 42, 44), Color3.fromRGB(154, 26, 6), Color3.fromRGB(255, 106, 16), Color3.fromRGB(255, 240, 176)
local function heatColor(h: number): Color3
	if h < 0.45 then return C_DARK:Lerp(C_RED, h / 0.45) end
	if h < 0.8 then return C_RED:Lerp(C_OR, (h - 0.45) / 0.35) end
	return C_OR:Lerp(C_HOT, (h - 0.8) / 0.2)
end

function GunParts.step(st: State, dt: number, c: Ctx, w: any)
	local k, P = st.k, st.parts
	local move: { [string]: CFrame } = {}
	local hide: { [string]: boolean } = {}
	st.hamT = math.min(1, st.hamT + dt); st.kickT = math.min(1, st.kickT + dt)
	local empty = c.ammo <= 0 and not c.reloading

	if P.mag then
		local v = sample(c, "mag")
		if v then
			if P.mag.dir then -- Plan B: the mag slides out along the grip's rake
				move.mag = CFrame.new(P.mag.dir * (v[1] * k))
				hide.mag = v[1] >= 0.18
			else -- [down, back, tip]
				move.mag = CFrame.new(0, v[1] * k, (v[2] or 0) * k) * about((P.mag.at or Vector3.zero) * k, rx(v[3] or 0))
				hide.mag = v[1] < -0.3
			end
		end
	end
	if P.charge then
		local v = sample(c, "charge")
		if v then move.charge = CFrame.new(0, 0, v[1] * k) end
	end
	if P.pump then
		local v = sample(c, "pump")
		if v then move.pump = CFrame.new(0, 0, v[1] * P.pump.travel * k) end
	end
	if P.bolt then
		local v = sample(c, "bolt")
		if v then move.bolt = CFrame.new(0, 0, (v[2] or 0) * P.bolt.travel * k) * about(P.bolt.at * k, rz(v[1] * P.bolt.lift)) end
	end
	if P.lever then
		local v = sample(c, "lever")
		if v then move.lever = about(P.lever.at * k, rx(v[1])) end
	end
	if P.lhammer then -- the model rests with the hammer down; between shots it sits cocked
		local v = sample(c, "lhammer")
		move.lhammer = about(P.lhammer.at * k, rx(if v then v[1] else 0.75))
	end
	if P.cover then
		local v = sample(c, "cover")
		if v then move.cover = about(P.cover.at * k, rx(v[1])) end
	end
	if P.slide then -- back fast and home a bit slower on every shot; locked back on an empty mag
		local v = sample(c, "slide")
		local t = st.kickT
		local kick = if t < 0.022 then t / 0.022 elseif t < 0.075 then 1 - (t - 0.022) / 0.053 else 0
		local s = if v then v[1] elseif empty or (c.reloading and c.clip == "reload_pistol_empty" and c.t < 1.04) then 1 else kick
		if s ~= 0 then move.slide = CFrame.new(0, 0, s * P.slide.travel * k) end
	end
	if P.hammer then
		local t = st.hamT
		local a: number
		if P.hammer.kind == "pistol" then
			local down = if empty then 0 elseif t < 0.02 then t / 0.02 elseif t < 0.06 then 1 - (t - 0.02) / 0.04 else 0
			a = -down * 0.75
		else
			a = if t < 0.05 then (t / 0.05) * 0.55 else math.max(0, 0.55 * (1 - (t - 0.05) / 0.05))
		end
		if a ~= 0 then move.hammer = about(P.hammer.at * k, rx(a)) end
	end
	if P.cylinder then -- a chamber a shot (eased), out on its crane and spun in the reload
		st.cylA += (st.cylTo - st.cylA) * math.min(1, dt * 24)
		local v = sample(c, "cyl")
		local th = if v then v[1] * 1.2 else 0
		local R = 0.034 * k
		local swing = CFrame.new(-R * math.sin(th), R * math.cos(th) - R, if v then v[1] * 0.004 * k else 0)
		move.cylinder = swing * about(P.cylinder.at * k, rz(-st.cylA - (if v then v[2] or 0 else 0)))
	end
	if P.hinge then -- Half a Shotgun: the barrels (and what rides on them) break down round the pin
		local v = sample(c, "hinge")
		local open = if v then v[1] else 0
		local hingeCF = about(P.hinge.at * k, rx(-open * P.hinge.open))
		local sh = sample(c, "shells")
		for _, node in P.hinge.nodes do
			local cf = hingeCF
			local i = if P.shells then table.find(P.shells, node) else nil
			if i and sh then
				local d = sh[i] or 0
				cf = hingeCF * CFrame.new(0, 0, d * k)
				hide[node] = d >= 0.15
			end
			if open ~= 0 or i then move[node] = cf end
		end
	end
	if P.hammers then -- one falls per barrel fired; the reload's last beat cocks them again
		local ck = sample(c, "cock")
		local fired = c.mag - c.ammo
		for i, h in P.hammers do
			local down = if i <= fired then (if ck then 1 - ck[1] else 1) else 0
			if down ~= 0 then move[h.node] = about(h.at * k, rx(-down * 0.75)) end
		end
	end
	if P.belt then -- a link per round left; the reload takes them off and lays a fresh belt
		local v = sample(c, "belt")
		local show = if v then (if v[1] > 0.5 then P.belt.n else 0) elseif c.reloading then 0 else math.min(P.belt.n, c.ammo)
		for i = 0, P.belt.n - 1 do hide[("belt_%02d"):format(i)] = i >= show end
	end
	if P.jar then -- the Marble Shotgun's jar: its balls show the ammo (fuller for longer), the reload pours them back
		local n = P.jar.n
		local full = math.clamp(c.ammo / math.max(1, c.mag), 0, 1)
		local frac = if full <= 0 then 0 else full ^ (P.jar.curve or 1)
		if c.reloading and c.clip == "reload_marbles" and P.jar.pour then
			local u = math.clamp((c.t - P.jar.pour[1]) / (P.jar.pour[2] - P.jar.pour[1]), 0, 1)
			frac += (1 - frac) * u
		end
		local show = math.clamp(math.floor(frac * n + 0.5), 0, n)
		if show < (st.jarShow or n) then st.jarBob = 1 end -- a shot took some: the rest settle with a small bob
		st.jarShow = show
		st.jarBob = math.max(0, (st.jarBob or 0) - dt * 5)
		local jb = st.jarBob or 0
		local bob = if jb > 0 then CFrame.new(0, -0.004 * k * math.sin(jb * math.pi), 0) else nil
		for i = 0, n - 1 do
			local node = ("marble_%02d"):format(i)
			hide[node] = i >= show
			if bob and i < show then move[node] = bob end
		end
	end
	if P.lid and c.reloading and c.clip == "reload_marbles" then -- flips open on its front hinge for the pour, snaps shut
		local o0, o1, s0, s1 = P.lid.times[1], P.lid.times[2], P.lid.times[3], P.lid.times[4]
		local t = c.t
		local open = if t < o0 then 0 elseif t < o1 then (function(u) return u * u * (3 - 2 * u) end)((t - o0) / (o1 - o0))
			elseif t < s0 then 1 elseif t < s1 then 1 - ((t - s0) / (s1 - s0)) ^ 2 else 0
		if open ~= 0 then move.lid = about(P.lid.at * k, rx(open * P.lid.open)) end
	end
	if P.crank and c.reloading and c.clip == "reload_marbles" then -- one full turn as the lid shuts (no jump at the end)
		local u = math.clamp((c.t - P.crank.times[1]) / (P.crank.times[2] - P.crank.times[1]), 0, 1)
		if u > 0 and u < 1 then move.crank = about(P.crank.at * k, rx(-u * u * (3 - 2 * u) * 2 * math.pi)) end
	end
	-- (weapons batch A) the Minigun's barrels turn round the gun's own axis, 40 rad/s at full spin (web weapons.js 1721).
	-- yours from GunParts.mySpin; someone else's eases up and down from their Spin attribute
	if P.barrels then
		local owner = st.owner
		local mine = owner == nil or owner == game:GetService("Players").LocalPlayer
		local want = if mine then GunParts.mySpin elseif owner and owner:GetAttribute("Spin") == true then 1 else 0
		local v = st.spinV or 0
		v = if mine then want elseif want > v then math.min(want, v + dt / 0.6) else math.max(want, v - dt / 0.9)
		st.spinV = v
		st.barA = ((st.barA or 0) + v * dt * 40) % (math.pi * 2)
		if v > 0 or (st.barA or 0) ~= 0 then move.barrels = about(P.barrels.at * k, rz(st.barA :: number)) end
	end
	-- the Water Pistol's tank (web secondaries.js 672): the water inside drains with the ammo and fills on the reload
	if P.water then
		local list = st.nodes.water
		if list then
			local full = if c.reloading then 1 else math.clamp(c.ammo / math.max(1, c.mag), 0, 1)
			local shown = st.waterShow or full
			shown += (full - shown) * math.min(1, dt * 10)
			st.waterShow = shown
			local sizes = st.waterSize or {}
			st.waterSize = sizes
			local f = math.max(0.04, shown)
			for _, pc in list do
				local rest = sizes[pc.part] or pc.part.Size
				sizes[pc.part] = rest
				local want = Vector3.new(rest.X, rest.Y * f, rest.Z)
				if (pc.part.Size - want).Magnitude > 1e-4 then pc.part.Size = want end
				move.water = CFrame.new(0, -(1 - f) * rest.Y / 2, 0)
			end
		end
	end
	-- (weapons batch C) the round sitting in the muzzle (the rubber chicken's head, the tennis ball in the bore) is gone
	-- from the shot till `back` s later, when the next one is in (parts.refill = { node, back })
	if P.refill and os.clock() - (st.shotT or -math.huge) < P.refill.back then hide[P.refill.node] = true end
	-- (the Scythe) a form switch just now: the moving pieces come across from where they sat in the other form
	if not st.owner and not st.ownerSeen then
		local m = st.root.Parent
		if m and m.Parent then st.ownerSeen = true; st.owner = game:GetService("Players"):GetPlayerFromCharacter(m.Parent) end
	end
	if st.form then
		local owner = st.owner
		local e: number
		if owner and owner ~= game:GetService("Players").LocalPlayer then
			local ft = owner:GetAttribute("FormT")
			e = if type(ft) == "number" then (workspace:GetServerTimeNow() - ft) / (st.formTime :: number) else 1
		else
			e = (os.clock() - GunParts.myFormT) / (st.formTime :: number)
		end
		if e < 1 then
			e = math.max(0, e)
			local s = 1 - e * e * (3 - 2 * e)
			for node, off in st.form :: { [string]: CFrame } do move[node] = CFrame.identity:Lerp(off, s) end
		end
	end
	-- the whole gun round the hand (the lever's spin-cock, the Revolver's twirl): every piece, never the hands
	local tw = sample(c, "twirl")
	local twirl: CFrame? = if tw and P.twirl and tw[1] ~= 0 then about(P.twirl.at * k, rx(tw[1])) else nil

	for _, p in st.all do
		local cf = move[p.node]
		local want = if cf then cf * p.rest else p.rest
		if twirl then want = twirl * want end
		if p.last ~= want then p.weld.C0 = want; p.last = want end
		local h = hide[p.node] == true
		if h ~= p.hidden then p.hidden = h; p.part:SetAttribute("Hide", if h then true else nil) end
	end

	-- heat: cools once you've let go for a moment; the barrel piece shows it
	if w.heatUp then
		if c.now - c.firedT > 0.25 then st.heat = math.max(0, st.heat - (w.heatDown or 0.4) * dt) end
		local hp = st.heatPiece
		if hp then
			local flick = if c.now - c.firedT < 0.12 then math.random() * 0.05 else 0
			local h = math.min(1, st.heat + flick)
			if math.abs(h - st.heatShown) > 0.004 then
				st.heatShown = h
				hp.Color = heatColor(h)
				hp.Material = if h > 0.2 then Enum.Material.Neon else Enum.Material.Metal
			end
		end
	end
end

return GunParts
