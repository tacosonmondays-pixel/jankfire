--!strict
-- VfxEmit: plays one of the bought VFX pack effects in the game (20 Nov 2026; the owner: "Now we have proper vfx").
-- The packs (BuiltByBit: Combat VFX, 100+ Combat VFX, Crimson Slash, Heart & Butterfly; Standard EULA, credited in
-- shared/Credits.luau; the raw files never go in git) author every effect for their Studio emit plugins: each
-- ParticleEmitter carries attributes saying how to fire it, which nothing in a running game reads. This module reads
-- them itself (our own code):
--   EmitDelay      seconds to wait before this emitter fires
--   EmitCount      particles to Emit() at once (when EmitDuration is 0)
--   EmitDuration   > 0: the emitter runs (Enabled, its own Rate) for this many seconds instead of a burst
--   TimeScale_Start / TimeScale_End / TimeScale_Duration   the emitter's TimeScale eased from Start to End (slow-mo tails)
-- Beams and Trails in an effect are shown for the effect's life and faded out.
-- The effects live as templates in ReplicatedStorage.JankfireVfx (one Part or Attachment per effect, recoloured to our
-- palette, on textures re-uploaded under the owner). VfxEmit.play(name, cframe, opts) clones one from a small pool,
-- places it, fires it and parks it again when its last particle is gone. Particle counts follow the settings' particle
-- slider (Fx.density) and at most MAX_PER_FRAME particles are emitted a frame (the rest wait for the next frames), so a
-- burst of shots can't spike the frame (the 16 Nov lag lesson).
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local VfxEmit = {}

local MAX_PER_FRAME = 260 -- particles emitted in one frame across every effect
local POOL = 4 -- spare clones kept per effect
local PARK = CFrame.new(0, -6000, 0)

local Fx: any = nil
do
	local m = script.Parent:FindFirstChild("Fx")
	if m and m:IsA("ModuleScript") then
		local ok, F = pcall(require, m)
		if ok then Fx = F end
	end
end
local function density(): number
	local d = if Fx then Fx.density else nil
	return if type(d) == "number" then d else 1
end

local holder = Instance.new("Folder")
holder.Name = "VfxEmit"
holder.Parent = workspace

type Fire = { at: number, em: ParticleEmitter, n: number }
local queue: { Fire } = {} -- emits waiting for their time (or for room in a frame)
type Live = { inst: Instance, name: string, done: number, extras: { Instance } }
local live: { Live } = {}
local pools: { [string]: { Instance } } = {}
type Base = { size: NumberSequence, speed: NumberRange, accel: Vector3, color: ColorSequence }
local base: { [ParticleEmitter]: Base } = setmetatable({}, { __mode = "k" }) :: any

local function templates(): Instance?
	return ReplicatedStorage:FindFirstChild("JankfireVfx")
end
local function num(i: Instance, k: string, d: number): number
	local v = i:GetAttribute(k)
	return if type(v) == "number" then v else d
end
-- how long an effect lasts: its latest emitter's delay + duration + longest particle life
local function lifeOf(root: Instance): number
	local t = 0.3
	for _, d in root:GetDescendants() do
		if d:IsA("ParticleEmitter") then
			t = math.max(t, num(d, "EmitDelay", 0) + num(d, "EmitDuration", 0) + d.Lifetime.Max / math.max(d.TimeScale, 0.05))
		end
	end
	return t + 0.1
end

local function take(name: string): Instance?
	local p = pools[name]
	if p and #p > 0 then return table.remove(p) end
	local f = templates()
	local t = f and f:FindFirstChild(name)
	if not t then return nil end
	local c = t:Clone()
	for _, d in c:GetDescendants() do
		if d:IsA("ParticleEmitter") then d.Enabled = false; d:SetAttribute("BaseTimeScale", d.TimeScale)
		elseif d:IsA("Beam") or d:IsA("Trail") then (d :: any).Enabled = false end
	end
	if c:IsA("BasePart") then c.Anchored = true; c.CanCollide = false; c.CanQuery = false; c.CanTouch = false; c.Transparency = 1 end
	return c
end
local function place(c: Instance, cf: CFrame, parent: Instance?)
	if c:IsA("BasePart") then
		c.CFrame = cf
		c.Parent = parent or holder
	elseif c:IsA("Attachment") then
		c.Parent = parent or workspace.Terrain
		c.WorldCFrame = cf
	elseif c:IsA("Model") then
		c.Parent = parent or holder
		c:PivotTo(cf)
	end
end

-- play an effect. opts.scale: a size factor (sizes, speeds, accelerations); opts.parent: ride a part (a gun, a body)
-- instead of standing in the world; opts.tint: a Color3 multiplied into every emitter's colour (for a skin's own
-- colour without a separate template)
function VfxEmit.play(name: string, cf: CFrame, opts: { scale: number?, parent: Instance?, tint: Color3? }?): boolean
	local c = take(name)
	if not c then return false end
	local o = opts or {}
	local sc = o.scale or 1
	place(c, cf, o.parent)
	local now = os.clock()
	local dens = density()
	for _, d in c:GetDescendants() do
		if d:IsA("ParticleEmitter") then
			-- (scale and tint always start from the template's own values: a pooled clone is reused with other options)
			local b = base[d]
			if not b then
				b = { size = d.Size, speed = d.Speed, accel = d.Acceleration, color = d.Color }
				base[d] = b
			end
			local B = b :: Base
			if sc ~= 1 then
				local k = {}
				for _, kp in B.size.Keypoints do table.insert(k, NumberSequenceKeypoint.new(kp.Time, kp.Value * sc, kp.Envelope * sc)) end
				d.Size = NumberSequence.new(k)
				d.Speed = NumberRange.new(B.speed.Min * sc, B.speed.Max * sc)
				d.Acceleration = B.accel * sc
			else
				d.Size = B.size; d.Speed = B.speed; d.Acceleration = B.accel
			end
			if o.tint then
				local tint = o.tint :: Color3
				local k = {}
				for _, kp in B.color.Keypoints do
					local v = kp.Value
					table.insert(k, ColorSequenceKeypoint.new(kp.Time, Color3.new(v.R * tint.R, v.G * tint.G, v.B * tint.B)))
				end
				d.Color = ColorSequence.new(k)
			else
				d.Color = B.color
			end
			d.TimeScale = num(d, "BaseTimeScale", 1)
			local delay = num(d, "EmitDelay", 0)
			local dur = num(d, "EmitDuration", 0)
			if dur > 0 then
				task.delay(delay, function()
					if d.Parent then d.Enabled = true end
					task.delay(dur, function() d.Enabled = false end)
				end)
			else
				local n = math.max(1, math.floor(num(d, "EmitCount", 1) * dens + 0.5))
				table.insert(queue, { at = now + delay, em = d, n = n })
			end
			local tsd = num(d, "TimeScale_Duration", 0)
			if tsd > 0 then
				local t0 = num(d, "TimeScale_Start", d.TimeScale)
				d.TimeScale = t0
				task.delay(delay, function()
					if d.Parent then
						TweenService:Create(d, TweenInfo.new(tsd, Enum.EasingStyle.Sine, Enum.EasingDirection.Out), { TimeScale = num(d, "TimeScale_End", t0) }):Play()
					end
				end)
			end
		elseif d:IsA("Beam") or d:IsA("Trail") then
			(d :: any).Enabled = true
		end
	end
	table.insert(live, { inst = c, name = name, done = now + lifeOf(c), extras = {} })
	return true
end

-- park a finished effect (its emitters off and cleared) for the next play
local function park(L: Live)
	local c = L.inst
	for _, d in c:GetDescendants() do
		if d:IsA("ParticleEmitter") then d.Enabled = false; d:Clear()
		elseif d:IsA("Beam") or d:IsA("Trail") then (d :: any).Enabled = false end
	end
	local p = pools[L.name]
	if not p then p = {}; pools[L.name] = p end
	if #p < POOL then
		place(c, PARK, nil)
		table.insert(p, c)
	else
		c:Destroy()
	end
end

RunService.Heartbeat:Connect(function()
	local now = os.clock()
	local budget = MAX_PER_FRAME
	local i = 1
	while i <= #queue do
		local f = queue[i]
		if f.at <= now and budget > 0 then
			if f.em.Parent then
				local n = math.min(f.n, budget)
				f.em:Emit(n)
				budget -= n
				f.n -= n
			else
				f.n = 0
			end
			if f.n <= 0 then table.remove(queue, i) else i += 1 end
		else
			i += 1
		end
	end
	for j = #live, 1, -1 do
		local L = live[j]
		if now >= L.done or not L.inst.Parent then
			table.remove(live, j)
			if L.inst.Parent then park(L) end
		end
	end
end)

-- the effects VfxEmit can play (the templates' names)
function VfxEmit.names(): { string }
	local out = {}
	local f = templates()
	if f then for _, c in f:GetChildren() do table.insert(out, c.Name) end end
	table.sort(out)
	return out
end

return VfxEmit
