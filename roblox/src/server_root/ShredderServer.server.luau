-- the Shredder: a port of the web game's shredder (shared/weapons.js + server/room.js shredPull / shredHeat).
-- the client only says "trigger held, looking this way". the server does the rest from its own positions: who is in
-- the cone, line of sight, the pull toward the intake (harder the closer), holding them in the teeth, the damage and
-- the heat. 1 m = 3 studs.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Debris = game:GetService("Debris")
local PhysicsService = game:GetService("PhysicsService")

local S = 3
local W = {
	range = 14 * S, cone = 0.61 + 0.15, tick = 0.09, mouth = 1.3 * S, shredR = 2 * S, grabR = 3.5 * S,
	dps = 150, pull = 4 * S, pullMax = 22 * S, vmax = 10 * S, lift = 1.4 * S,
	fuel = 4, regen = 1, coolTo = 0.35, spawnSafe = 1.2, holdFor = 0.26,
}
local COS_CONE = math.cos(W.cone)
local remote = ReplicatedStorage:WaitForChild("ShredderRemote")
-- the weapons' fight system owns HP, kills, respawns and the feed: the Shredder's damage goes through it
local Fight = nil
do
	local ok, m = pcall(function() return require(game:GetService("ServerScriptService"):WaitForChild("Jankfire"):WaitForChild("Fight")) end)
	if ok then Fight = m end
end

-- anyone caught in a Shredder (and its chips) passes through players, so the body it drags in, holds in front of
-- you and spits out of the chute next to your head can't bounce you around. they still hit the map.
pcall(function() PhysicsService:RegisterCollisionGroup("JFPlayers") end)
pcall(function() PhysicsService:RegisterCollisionGroup("JFShredded") end)
PhysicsService:CollisionGroupSetCollidable("JFPlayers", "JFShredded", false)
local caught = {} -- [model] = last time a shredder had it
local function setGroup(model, group)
	for _, d in ipairs(model:GetDescendants()) do
		if d:IsA("BasePart") and not d:FindFirstAncestorOfClass("Tool") then d.CollisionGroup = group end
	end
end
local function catch(model)
	if not caught[model] then setGroup(model, "JFShredded") end
	caught[model] = os.clock()
end

local state = {} -- [player] = { on, look, aimT, heat, hot, tickT, tokens, tokT, attr }
local spawnT = {} -- [player] = when the current character spawned
local held = {} -- [humanoid] = { at, untilT } (npcs only: players hold themselves, told by "grab")
local pulledT = {} -- [humanoid] = last time the shredder touched it (npcs: when to let them get up)

local function newState() return { on = false, look = Vector3.zAxis, aimT = 0, heat = 0, hot = false, tickT = 0, tokens = 40, tokT = os.clock(), attr = {} } end
local function finite(n) return n == n and math.abs(n) < 1e6 end

local function setup(p)
	state[p] = newState()
	local function onChar(ch)
		spawnT[p] = os.clock(); state[p] = newState() -- a new life starts cold
		setGroup(ch, "JFPlayers")
		ch.DescendantAdded:Connect(function(d) -- accessories load in late
			if d:IsA("BasePart") and not d:FindFirstAncestorOfClass("Tool") then d.CollisionGroup = if caught[ch] then "JFShredded" else "JFPlayers" end
		end)
	end
	p.CharacterAdded:Connect(onChar)
	if p.Character then onChar(p.Character) end
end
Players.PlayerAdded:Connect(setup)
for _, p in ipairs(Players:GetPlayers()) do setup(p) end
Players.PlayerRemoving:Connect(function(p) state[p] = nil; spawnT[p] = nil end)

local function equipped(p)
	local ch = p.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	if not hum or hum.Health <= 0 then return nil end
	local tool = ch:FindFirstChild("Shredder")
	if tool and tool:IsA("Tool") then return tool, ch, hum end
	return nil
end

-- every message is checked: kind, a finite unit-ish look, alive, holding the Shredder, at most 40 a second
remote.OnServerEvent:Connect(function(p, kind, look)
	local s = state[p]
	if not s then return end
	local now = os.clock()
	s.tokens = math.min(40, s.tokens + (now - s.tokT) * 40); s.tokT = now
	if s.tokens < 1 then return end
	s.tokens -= 1
	if kind == "stop" then s.on = false return end
	if kind == "sw" then -- the gun's swivel toward its target, for everyone else to see: a rotation of at most 40°
		if typeof(look) ~= "CFrame" then return end
		if now - (s.swT or 0) < 1 / 15 then return end -- (a replicated attribute: at most 15 a second, not 40)
		s.swT = now
		local tool = equipped(p)
		if not tool then return end
		local axis, ang = look:ToAxisAngle()
		if not (finite(axis.X) and finite(axis.Y) and finite(axis.Z) and finite(ang)) then return end
		if axis.Magnitude < 0.5 or math.abs(ang) < 1e-3 then tool:SetAttribute("Swivel", CFrame.identity) return end
		tool:SetAttribute("Swivel", CFrame.fromAxisAngle(axis.Unit, math.clamp(ang, -math.rad(40), math.rad(40))))
		return
	end
	if kind ~= "aim" or typeof(look) ~= "Vector3" then return end
	if not (finite(look.X) and finite(look.Y) and finite(look.Z)) then return end
	local m = look.Magnitude
	if m < 0.5 or m > 1.5 then return end
	if not equipped(p) then return end
	s.look = look / m; s.on = true; s.aimT = now
end)

-- everyone who can be shredded: other players and the practice dummies
local function targets(shooter)
	local list = {}
	for _, p in ipairs(Players:GetPlayers()) do
		if p ~= shooter and p.Character then table.insert(list, { model = p.Character, player = p }) end
	end
	local dummies = workspace:FindFirstChild("Dummies")
	if dummies then for _, m in ipairs(dummies:GetChildren()) do if m:IsA("Model") then table.insert(list, { model = m }) end end end
	return list
end

local function bodies()
	local list = {}
	for _, p in ipairs(Players:GetPlayers()) do if p.Character then table.insert(list, p.Character) end end
	local dummies = workspace:FindFirstChild("Dummies")
	if dummies then table.insert(list, dummies) end
	return list
end

local function ragdoll(hum, root)
	pulledT[hum] = os.clock()
	if not hum.PlatformStand then hum.PlatformStand = true end
	pcall(function() root:SetNetworkOwner(nil) end)
end

-- one chunk of someone, out of the chute
local function chip(from, dir, colour, base)
	local c = Instance.new("Part")
	c.Name = "Chip"
	local sz = 0.25 + math.random() * 0.4
	c.Size = Vector3.new(sz, sz * 0.6, sz * 0.8)
	c.Color = colour
	c.Material = Enum.Material.SmoothPlastic
	c.CanQuery = false; c.CanTouch = false
	c.CollisionGroup = "JFShredded"
	c.CFrame = CFrame.new(from + Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * 0.2) * CFrame.Angles(math.random() * 6, math.random() * 6, math.random() * 6)
	c.AssemblyLinearVelocity = dir * (18 + math.random() * 18) + Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * 9.6 + Vector3.new(0, 4.5, 0) + (base or Vector3.zero)
	c.AssemblyAngularVelocity = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * 32
	c.Parent = workspace
	Debris:AddItem(c, 2.2 + math.random() * 1.6)
end

-- where a shooter's intake and chute are right now, and which way the chute spits
local function portsOf(shooterCh)
	local tool = shooterCh and shooterCh.Parent and shooterCh:FindFirstChild("Shredder")
	local h = tool and tool:FindFirstChild("Handle")
	local mz = h and h:FindFirstChild("Muzzle")
	local chute = tool and tool:FindFirstChild("sh_bell2", true)
	local hub = tool and tool:FindFirstChild("sh_hub", true)
	if not (mz and chute and hub) then return nil end
	local dir = ((chute.Position - hub.Position).Unit + Vector3.new(0, 0.6, 0)).Unit
	local root = shooterCh:FindFirstChild("HumanoidRootPart")
	return mz.WorldPosition, chute.Position + dir * 0.4, dir, root and root.AssemblyLinearVelocity or Vector3.zero
end

local function spitChunks(shooterCh, colour, last)
	local _, chute, dir, base = portsOf(shooterCh)
	if not chute then return end
	for _ = 1, (if last then 10 else 2 + (if math.random() < 0.5 then 1 else 0)) do chip(chute, dir, colour, base) end
	if last then for _ = 1, 8 do chip(chute, dir, Color3.fromRGB(150, 15, 15), base) end end -- the big finish
end

-- the kill (public/js/shredder.js shredKill): they come apart, every piece drifts off the body for a moment, then
-- gets sucked into the killer's intake (nearest first, speeding up, corkscrewing, shrinking down the throat) and
-- comes out of the chute as chunks in its colour. done here on copies of their parts, so everyone sees the same thing.
local pieces = {}
local KEEP = { Decal = true, SpecialMesh = true, SurfaceAppearance = true, Texture = true }
local function shredBody(t, shooterCh)
	local intake = portsOf(shooterCh)
	if not intake then return end
	local parts = {}
	for _, d in ipairs(t.model:GetDescendants()) do
		if d:IsA("BasePart") and d.Transparency < 1 and not d:FindFirstAncestorOfClass("Tool") then table.insert(parts, d) end
	end
	table.sort(parts, function(x, y) return (x.Position - intake).Magnitude < (y.Position - intake).Magnitude end) -- nearest bits go in first
	local function r(n) return (math.random() - 0.5) * 2 * n end
	for i, part in ipairs(parts) do
		local c = part:Clone()
		for _, k in ipairs(c:GetChildren()) do if not KEEP[k.ClassName] then k:Destroy() end end
		c.Name = "ShredBit"
		c.Anchored = true; c.CanCollide = false; c.CanQuery = false; c.CanTouch = false
		c.CollisionGroup = "JFShredded"
		c.CFrame = part.CFrame
		c.Parent = workspace
		part.Transparency = 1 -- the real one stays behind, hidden
		for _, k in ipairs(part:GetChildren()) do if k:IsA("Decal") then k.Transparency = 1 end end
		local mesh = c:FindFirstChildOfClass("SpecialMesh")
		table.insert(pieces, {
			part = c, shooter = shooterCh, size0 = c.Size, mesh = mesh, meshScale0 = mesh and mesh.Scale,
			rot = c.CFrame - c.CFrame.Position, t = 0, delay = 0.06 + (i / #parts) * 0.35 + math.random() * 0.06,
			pop = Vector3.new(r(0.9), 0.2 + math.random() * 0.8, r(0.9)) * S, av = Vector3.new(r(8), r(8), r(8)),
			wob = math.random() * 6, colour = part.Color, last = i == #parts,
		})
	end
end

local function stepPieces(dt)
	for i = #pieces, 1, -1 do
		local p = pieces[i]
		local c = p.part
		p.t += dt
		if not c.Parent then
			table.remove(pieces, i)
		elseif p.t < p.delay then -- coming apart: everything drifts off the body for a moment first
			p.rot = p.rot * CFrame.Angles(p.av.X * dt * 0.3, 0, p.av.Z * dt * 0.3)
			c.CFrame = CFrame.new(c.Position + p.pop * dt) * p.rot
		else
			local intake = portsOf(p.shooter)
			if not intake then -- the shooter's gone (died, put it away): it just drops
				c.Anchored = false; c.CanCollide = true
				Debris:AddItem(c, 3)
				table.remove(pieces, i)
			else
				if not p.from then p.from = c.Position; p.dur = math.clamp((p.from - intake).Magnitude / (11 * S), 0.16, 0.5) end
				local u = math.min(1, (p.t - p.delay) / p.dur)
				local e = u * u -- speeds up as it gets sucked in
				local wob = (1 - u) * 0.18 * S * math.sin(u * 14 + p.wob) -- a little corkscrew on the way
				local spin = 1 + u * 4
				p.rot = p.rot * CFrame.Angles(p.av.X * dt * spin, p.av.Y * dt * spin, p.av.Z * dt * spin)
				local k = 1 - 0.8 * u -- shrinks all the way in, so it fits down the throat
				c.Size = p.size0 * k
				if p.mesh then p.mesh.Scale = p.meshScale0 * k end
				c.CFrame = CFrame.new(p.from:Lerp(intake, e) + Vector3.new(wob, wob * 0.6, -wob)) * p.rot
				if u >= 1 then
					c:Destroy()
					table.remove(pieces, i)
					local shooter, colour, last = p.shooter, p.colour, p.last
					task.delay(0.11 + math.random() * 0.2, function() spitChunks(shooter, colour, last) end)
				end
			end
		end
	end
end

-- the hub's rule (Fight.allow): no pulling or grabbing people you couldn't hurt (the hub, the training room, your team)
local function allowed(p, t)
	if not Fight then return true end
	local me, them = Fight.of(p), Fight.of(t.player or t.model)
	if not me or not them then return t.player == nil end -- (a player the fight system doesn't know yet: hands off)
	return Fight.allow(me, them)
end

local function suckTick(p, s, el)
	local tool, ch, myHum = equipped(p)
	if not tool then return end
	local head = ch:FindFirstChild("Head")
	local myRoot = ch:FindFirstChild("HumanoidRootPart")
	if not head or not myRoot then return end
	local now = os.clock()
	local eye, L = head.Position, s.look
	local mouth = eye + L * W.mouth + Vector3.new(0, -0.25 * S, 0)
	local right = L:Cross(Vector3.yAxis)
	right = if right.Magnitude > 1e-3 then right.Unit else Vector3.xAxis
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = bodies()
	for _, t in ipairs(targets(p)) do
		local hum = t.model:FindFirstChildOfClass("Humanoid")
		local root = t.model:FindFirstChild("HumanoidRootPart")
		if hum and root and hum.Health > 0 and allowed(p, t) then
			-- in front of you (loosely: positions lag a bit) and not through a wall
			local fe = root.Position - eye
			local de = fe.Magnitude
			local inCone = de <= 3 * S or fe.Unit:Dot(L) >= COS_CONE
			local clear = inCone and de > 1.5 and not workspace:Raycast(eye, fe.Unit * (de - 1.5), params) or (inCone and de <= 1.5)
			if inCone and clear then
				-- intake to the nearest bit of their body
				local feet = root.Position - Vector3.new(0, hum.HipHeight + root.Size.Y / 2, 0)
				local by = math.clamp(mouth.Y, feet.Y + 0.2 * S, feet.Y + 1.7 * S)
				local to = Vector3.new(mouth.X - feet.X, mouth.Y - by, mouth.Z - feet.Z)
				local d = math.max(to.Magnitude, 1e-3)
				local safe = t.player ~= nil and now - (spawnT[t.player] or 0) < W.spawnSafe
				if d <= W.range and not safe then
					if d <= W.grabR then
						-- the last few metres it just yanks them in: hang them in the stream just past the mouth, a bit
						-- to the right where the gun is, low enough that you can still see past them (that's their feet)
						local at = mouth + L * 0.75 * S + right * 0.3 * S + Vector3.new(0, -1.0 * S, 0)
						local rootAt = at + Vector3.new(0, hum.HipHeight + root.Size.Y / 2, 0)
						catch(t.model)
						if t.player then remote:FireClient(t.player, "grab", rootAt)
						else ragdoll(hum, root); held[hum] = { at = rootAt, untilT = now + W.holdFor, root = root } end
						if d <= W.shredR then
							local tag = hum:FindFirstChild("creator") or Instance.new("ObjectValue")
							tag.Name = "creator"; tag.Value = p; tag.Parent = hum
							Debris:AddItem(tag, 2)
							local fv = Fight and Fight.of(t.player or t.model)
							if fv then Fight.hurt(fv, W.dps * el, Fight.of(p), "shredder", false, nil, root.Position)
							else hum:TakeDamage(W.dps * el) end
							if (fv and not fv.alive) or (not fv and hum.Health <= 0) then
								held[hum] = nil
								shredBody(t, ch)
								if t.player then remote:FireClient(t.player, "fx", "SHREDDED") end
								remote:FireClient(p, "fx", "SHREDDED")
							end
						end
					else
						-- speed-capped so they don't arrive like a bullet
						local k = 1 - d / W.range
						local dir = to / d
						local along = (root.AssemblyLinearVelocity - myRoot.AssemblyLinearVelocity):Dot(dir)
						local dv = math.max(0, math.min((W.pull + (W.pullMax - W.pull) * k * k) * (el / W.tick), W.vmax + d * 0.3 - along))
						local imp = dir * dv + Vector3.new(0, W.lift * (0.4 + 0.6 * k), 0)
						catch(t.model)
						if t.player then remote:FireClient(t.player, "pull", imp)
						else ragdoll(hum, root); root.AssemblyLinearVelocity += imp end
					end
				end
			end
		end
	end
end

local function setAttr(s, tool, k, v)
	if s.attr[k] ~= v or s.attr.tool ~= tool then s.attr[k] = v; tool:SetAttribute(k, v) end
end

RunService.Heartbeat:Connect(function(dt)
	local now = os.clock()
	stepPieces(dt)
	for p, s in pairs(state) do
		local tool = equipped(p)
		local on = s.on and tool ~= nil and now - s.aimT < 0.3
		-- ~4 s of sucking overheats it, then it has to cool to 35% before it runs again
		if s.hot then
			s.heat = math.max(0, s.heat - dt * W.regen)
			if s.heat <= W.fuel * W.coolTo then s.hot = false end
		elseif on then
			s.heat += dt
			if s.heat > W.fuel then s.hot = true end
		else
			s.heat = math.max(0, s.heat - dt * W.regen)
		end
		local sucking = on and not s.hot
		if tool then
			setAttr(s, tool, "Heat", math.floor(s.heat / W.fuel * 50 + 0.5) / 50)
			setAttr(s, tool, "Hot", s.hot)
			setAttr(s, tool, "Sucking", sucking)
			s.attr.tool = tool
			local fx = tool:FindFirstChild("Suction", true)
			if fx and fx.Enabled ~= sucking then fx.Enabled = sucking end
		end
		if sucking and now - s.tickT >= W.tick then
			local el = if now - s.tickT < 0.3 then now - s.tickT else W.tick
			s.tickT = now
			suckTick(p, s, el)
		end
	end
	-- npcs in the teeth chase their hold point; npcs nobody is pulling get back up
	for hum, h in pairs(held) do
		if now < h.untilT and hum.Health > 0 and h.root.Parent then
			local v = (h.at - h.root.Position) * 9
			if v.Magnitude > 90 then v = v.Unit * 90 end
			h.root.AssemblyLinearVelocity = v
		else
			held[hum] = nil
		end
	end
	for model, t in pairs(caught) do
		if not model.Parent then caught[model] = nil
		elseif now - t > 0.8 then
			local hum = model:FindFirstChildOfClass("Humanoid")
			if hum and hum.Health > 0 then
				setGroup(model, if Players:GetPlayerFromCharacter(model) then "JFPlayers" else "Default")
				caught[model] = nil
			end
		end
	end
	for hum, t in pairs(pulledT) do
		if not hum.Parent then pulledT[hum] = nil
		elseif now - t > 0.6 and not held[hum] then
			if hum.Health > 0 then hum.PlatformStand = false end
			pulledT[hum] = nil
		end
	end
end)

-- while the Shredder is out, the gun the weapons system put in your hand goes (others would see two); back when it's put away
local function watchTool(tool, plr)
	if not tool:IsA("Tool") or tool.Name ~= "Shredder" or tool:GetAttribute("JFHooked") then return end
	tool:SetAttribute("JFHooked", true)
	tool.Equipped:Connect(function()
		local ch = plr.Character
		local hw = ch and ch:FindFirstChild("HeldWeapon")
		if hw then hw:Destroy() end
	end)
	tool.Unequipped:Connect(function()
		local f = Fight and Fight.of(plr)
		if f and f.alive then Fight.showWeapon(f) end
	end)
end
local function hookPlayer(plr)
	local function hookBag(bag)
		for _, c in ipairs(bag:GetChildren()) do watchTool(c, plr) end
		bag.ChildAdded:Connect(function(c) watchTool(c, plr) end)
	end
	plr.ChildAdded:Connect(function(c) if c:IsA("Backpack") then hookBag(c) end end)
	local bag = plr:FindFirstChildOfClass("Backpack")
	if bag then hookBag(bag) end
end
for _, plr in ipairs(Players:GetPlayers()) do hookPlayer(plr) end
Players.PlayerAdded:Connect(hookPlayer)
