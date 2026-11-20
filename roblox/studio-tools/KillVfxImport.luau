--!strict
-- KillVfxImport (studio tool, 20 Nov 2026, kill-effects-emotes): builds the kill effects' templates in
-- ReplicatedStorage.JankfireVfx from the bought Combat VFX pack (coldd Development; credited in Shared.Credits) for
-- VfxEmit to play (client/KillFx.luau PACK). Run in Edit:
--   require(this).build(source)   source: any Instance holding the pack's effects under their own names
--   require(this).check()         what's there, every template's biggest particle and longest life
-- The pack's own settings never go in git: this copies the effects that are already in the place and only changes
-- them by the rules below. Each template is cut down to a dead body's size (the kill effect rules: about 4 studs, 1.5 s,
-- no floor marks), recoloured to its kill effect's colour, and given VfxEmit's attributes (EmitCount / EmitDuration /
-- EmitDelay), so continuous emitters play as short bursts.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local M = {}

-- per template: the pack effect(s) it's made from, the biggest any particle may get (studs; a particle's Size is half its
-- width), the longest a particle may live (s), how long continuous emitters run (s) and at what share of their rate, the
-- use's one accent colour, and the part it rides (its size is where particles are born: the body's volume or a point).
-- The colour rule is the VFX session's (pack-effects-usage.md): white-hot cores stay white; saturated colours move to the
-- accent's hue with about 30% of their saturation taken out; Brightness at most 4; LightEmission within -1..1 (a negative
-- one only as the pack's own dark layer)
-- `skip` drops the emitters under the pack's attachments of those names
type Spec = { from: { string }, maxSize: number, kmax: number, life: number, run: number, rate: number?, accent: Color3,
	part: Vector3, skip: { string }? }
M.SPEC = {
	-- STATIC: electric bolts crawl over the body (played three times while it flickers)
	KillStaticArc = { from = { "Shock Aura", "Blue Lightning" }, maxSize = 2.8, kmax = 0.8, life = 0.3, run = 0.18, rate = 1.6,
		accent = Color3.fromRGB(150, 226, 255), part = Vector3.new(1.4, 4.2, 1) },
	-- STATIC: the snap out to a point
	KillStaticPop = { from = { "Eletricity", "Golden Eletricity" }, maxSize = 2.2, kmax = 0.8, life = 0.3, run = 0.12,
		accent = Color3.fromRGB(150, 226, 255), part = Vector3.new(0.6, 0.6, 0.6) },
	-- SHATTER: the ice burst at the break, frost flakes falling (its "smokes" layer out: a 20-stud white fog, 20 Nov photo)
	KillIceBurst = { from = { "Frigid Blast" }, maxSize = 3.6, kmax = 0.28, life = 0.9, run = 0.1,
		accent = Color3.fromRGB(176, 214, 236), part = Vector3.new(0.8, 1.2, 0.8), skip = { "smokes" } },
	-- ASCEND: rays and a soft core as the body glows and lifts
	KillRays = { from = { "Treasure" }, maxSize = 3.4, kmax = 0.6, life = 0.6, run = 0.8, rate = 1.5,
		accent = Color3.fromRGB(255, 232, 186), part = Vector3.new(0.5, 0.5, 0.5) },
	-- (BLAST ZONE waits for a ring from the 100+ pack: Guard break and Slam are parry and landing's)
} :: { [string]: Spec }

local function maxOf(ns: NumberSequence): number
	local m = 0
	for _, kp in ns.Keypoints do m = math.max(m, kp.Value + kp.Envelope) end
	return m
end
local function scaleNS(ns: NumberSequence, k: number): NumberSequence
	local out = {}
	for _, kp in ns.Keypoints do table.insert(out, NumberSequenceKeypoint.new(kp.Time, kp.Value * k, kp.Envelope * k)) end
	return NumberSequence.new(out)
end
local function recolour(cs: ColorSequence, s: Spec): ColorSequence
	local ah = s.accent:ToHSV()
	local out = {}
	for _, kp in cs.Keypoints do
		local _, sat, val = kp.Value:ToHSV()
		local v = kp.Value
		if sat >= 0.15 then v = Color3.fromHSV(ah, sat * 0.7, val) end -- (whites and greys stay as they are)
		table.insert(out, ColorSequenceKeypoint.new(kp.Time, v))
	end
	return ColorSequence.new(out)
end

local function find(source: Instance, name: string): Instance?
	for _, d in source:GetDescendants() do
		if d.Name == name and (d:IsA("BasePart") or d:IsA("Attachment") or d:IsA("Model")) then
			for _, x in d:GetDescendants() do if x:IsA("ParticleEmitter") then return d end end
		end
	end
	return nil
end

-- one emitter made to fit the spec
local function fit(e: ParticleEmitter, s: Spec)
	local big = maxOf(e.Size)
	local k = math.min(s.kmax, if big > 0 then s.maxSize / big else 1)
	e.Size = scaleNS(e.Size, k)
	e.Speed = NumberRange.new(e.Speed.Min * k, e.Speed.Max * k)
	e.Acceleration *= k
	e.Lifetime = NumberRange.new(math.min(e.Lifetime.Min, s.life), math.min(e.Lifetime.Max, s.life))
	e.Color = recolour(e.Color, s)
	e.LightInfluence = 0
	e.LightEmission = math.clamp(e.LightEmission, -1, 1)
	e.Brightness = math.min(e.Brightness, 4)
	e.Enabled = false
	-- an emitter the pack fires by hand keeps its count; a continuous one runs for `run` seconds at its own rate
	local n = e:GetAttribute("EmitCount")
	local dur = e:GetAttribute("EmitDuration")
	if (type(n) ~= "number" or n <= 0) and (type(dur) ~= "number" or dur <= 0) then
		e:SetAttribute("EmitCount", nil)
		e:SetAttribute("EmitDuration", s.run)
		e.Rate = e.Rate * (s.rate or 1)
	elseif type(dur) == "number" and dur > 0 then
		e:SetAttribute("EmitDuration", math.min(dur, s.run))
	end
	e:SetAttribute("PackFit", string.format("x%.3f", k))
end

function M.build(source: Instance): string
	local folder = ReplicatedStorage:FindFirstChild("JankfireVfx")
	if not folder then
		folder = Instance.new("Folder")
		folder.Name = "JankfireVfx"
		folder.Parent = ReplicatedStorage
	end
	local out = {}
	for name, s in M.SPEC do
		local p = Instance.new("Part")
		p.Name = name
		p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
		p.Transparency = 1; p.Size = s.part
		local got = {}
		for _, src in s.from do
			local fx = find(source, src)
			if not fx then table.insert(out, name .. ": missing " .. src); continue end
			-- every emitter (and the attachments holding them, at the middle: a body-sized burst, not the pack's layout)
			for _, d in fx:GetDescendants() do
				if d:IsA("ParticleEmitter") and not (s.skip and d.Parent and table.find(s.skip, d.Parent.Name)) then
					local e = d:Clone()
					fit(e, s)
					local at = d.Parent
					if at and at:IsA("Attachment") then
						local a = p:FindFirstChild(at.Name)
						if not a then
							a = Instance.new("Attachment")
							a.Name = at.Name
							a.Parent = p
						end
						e.Parent = a
					else
						e.Parent = p
					end
					table.insert(got, src)
				end
			end
		end
		p:SetAttribute("KillFx", true)
		p:SetAttribute("From", table.concat(s.from, " + ") .. " (Combat VFX Asset Pack, coldd Development)")
		local old = folder:FindFirstChild(name)
		if old then old:Destroy() end
		p.Parent = folder
		table.insert(out, string.format("%s: %d emitters", name, #got))
	end
	table.sort(out)
	return table.concat(out, "; ")
end

function M.check(): string
	local folder = ReplicatedStorage:FindFirstChild("JankfireVfx")
	if not folder then return "no JankfireVfx" end
	local out = {}
	for name in M.SPEC do
		local t = folder:FindFirstChild(name)
		if not t then table.insert(out, name .. ": MISSING"); continue end
		local n, big, life = 0, 0, 0
		for _, d in t:GetDescendants() do
			if d:IsA("ParticleEmitter") then
				n += 1
				big = math.max(big, maxOf(d.Size))
				life = math.max(life, d.Lifetime.Max + (tonumber(d:GetAttribute("EmitDelay")) or 0) + (tonumber(d:GetAttribute("EmitDuration")) or 0))
			end
		end
		table.insert(out, string.format("%s: %d em, biggest %.1f studs, done by %.2f s", name, n, big, life))
	end
	table.sort(out)
	return table.concat(out, "; ")
end

return M
