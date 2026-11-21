--!strict
-- FINISHER TOWNS (20 Nov 2026): a scene's kit town in place of its plan's own boxes, with blank cowboy onlookers. The
-- owner, on High Noon: "can you fix the scene scenery too? like sprucent up the buildings ... can you add blank npcs
-- that are blokey and have cowboy gear like hiding in windows and reacting in the backgorund maybe? make two versions
-- so I can see side by side". The towns are chunky Blender kits (tools/roblox/highnoon_town.py, A a timber main
-- street, B an adobe border town), uploaded once and kept in ReplicatedStorage.JankfireFinisherSets.HighNoonTown<A|B>
-- (a model pivoted on the scene's ORIGIN); their onlookers' spots are in FinisherTownData. The onlookers are copies of
-- JankfireFinisherSets.Onlooker (a plain blocky R15 body, no face, a hat, a bandana, a vest), posed from the scene's own
-- clips by the scene's clock (never posed by hand): idle and a peek through the build-up, ducking below the sill at
-- the draw (windows, doors, barrels) or flinching at the shot (balconies, porches), peeking out again after. Cheap: a
-- handful of bodies, anchored at the root, posed only while on screen; the town is a few big meshes.
-- (FinisherScene builds it: Town.REPLACED are the plan's set tags the kit stands in for; Town.build after the set,
-- Town.step every frame)
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Finishers = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Finishers")) :: any
local TownData = require(script.Parent:WaitForChild("FinisherTownData")) :: any

local Town = {}
-- the plan's set pieces a kit town stands in for (its ground and its footprints stay)
Town.REPLACED = { porch = true, window = true, bldg = true, prop = true, walk = true, sign = true, lamp = true, cactus = true,
	mesa = true } :: { [string]: boolean }

-- the onlookers' clips (Finishers.SCENE_ANIMS keys, all already the scene's) and how each kind of spot reacts, in the
-- scene's own seconds (High Noon: the reach at 10.22, the draw at 10.88, the shot at 11.3, the far shot from 11.55)
Town.MOVES = {
	idle = "id_06_dune_weight_shift", look = "victim_lookaround_t2", duck = "bx_28_knockdown_liver",
	flinch = "bx_18_block_high_center", cower = "bx_27_hit_stomach",
}
Town.TIMES = { peek0 = 2.4, peek1 = 7.2, duck = 10.2, duckFrom = 0.25, duckTo = 0.95, duckFor = 0.5, shot = 11.3,
	flinchFor = 0.45, back = 12.5 }
local COLOURS = { -- (muted: hats, vests, shirts and trousers per onlooker, in turn)
	{ hat = Color3.fromRGB(122, 98, 74), vest = Color3.fromRGB(86, 66, 48), shirt = Color3.fromRGB(176, 160, 136), legs = Color3.fromRGB(92, 84, 76) },
	{ hat = Color3.fromRGB(70, 62, 56), vest = Color3.fromRGB(120, 92, 62), shirt = Color3.fromRGB(150, 128, 104), legs = Color3.fromRGB(70, 68, 66) },
	{ hat = Color3.fromRGB(176, 158, 124), vest = Color3.fromRGB(64, 58, 52), shirt = Color3.fromRGB(184, 172, 150), legs = Color3.fromRGB(104, 90, 74) },
}

local function sets(): Instance?
	return ReplicatedStorage:FindFirstChild("JankfireFinisherSets")
end

local function ease(u: number): number u = math.clamp(u, 0, 1); return u * u * (3 - 2 * u) end

-- the town for a scene's EXTRA (ex.town = "A" | "B"), or nil
function Town.pick(sceneId: string, key: string?): any
	if not key then return nil end
	local d = TownData[sceneId]
	local t = d and d[key]
	local f = sets()
	if not t or not f or not f:FindFirstChild(t.set) then return nil end
	return t
end

type Npc = { model: Model, root: BasePart, kind: string, react: string?, tracks: { [string]: AnimationTrack }, phase: number, on: boolean }

local function track(n: Npc, key: string): AnimationTrack?
	local have = n.tracks[key]
	if have then return have end
	local id = Finishers.SCENE_ANIMS[Town.MOVES[key]]
	local hum = n.model:FindFirstChildOfClass("Humanoid")
	local an = hum and hum:FindFirstChildOfClass("Animator")
	if not id or not an then return nil end
	local a = Instance.new("Animation")
	a.AnimationId = "rbxassetid://" .. id
	local ok, tr = pcall(function() return (an :: Animator):LoadAnimation(a) end)
	if not ok or not tr then return nil end
	tr.Looped = false
	tr.Priority = Enum.AnimationPriority.Action4
	n.tracks[key] = tr
	return tr
end

-- builds the town and its onlookers under `parent`, the town pivoted on `origin`; returns its state (for Town.step).
-- `step` (built ahead of the scene, FinisherScene's Scene.warm): the town comes a few pieces at a time and the onlookers
-- one at a time, `step` called between (it waits a frame); false from it stops the build (nil back)
local TOWN_CHUNK = 40
function Town.build(sceneId: string, key: string, parent: Instance, origin: CFrame, step: (() -> boolean)?): any
	local t = Town.pick(sceneId, key)
	if not t then return nil end
	local f = sets() :: Instance
	local src = f:FindFirstChild(t.set) :: Model
	local m: Model
	if step then
		-- (each piece moved by the shift that pivots the whole town on `origin`)
		local shift = origin * src:GetPivot():Inverse()
		m = Instance.new("Model")
		m.Name = src.Name
		m.Parent = parent
		for n, c in src:GetChildren() do
			local k = c:Clone()
			if k:IsA("PVInstance") then
				k:PivotTo(shift * k:GetPivot())
			else
				for _, d in k:GetDescendants() do if d:IsA("BasePart") then d.CFrame = shift * d.CFrame end end
			end
			k.Parent = m
			if n % TOWN_CHUNK == 0 and not step() then return nil end
		end
	else
		m = src:Clone()
		m:PivotTo(origin)
		m.Parent = parent
	end
	local st = { model = m, npcs = {} :: { Npc } }
	local proto = f:FindFirstChild("Onlooker") :: Model?
	if not proto then return st end
	for i, sp in t.spots do
		if step and not step() then return nil end
		local n = proto:Clone()
		local root = n:FindFirstChild("HumanoidRootPart") :: BasePart?
		local hum = n:FindFirstChildOfClass("Humanoid")
		if not root or not hum then n:Destroy(); continue end
		-- (feet on the spot: the root stands HipHeight + half its height over them)
		local feet = origin * Vector3.new(sp[1], sp[2], sp[3])
		local look = origin:VectorToWorldSpace(Vector3.new(sp[4], 0, sp[5]))
		local up = hum.HipHeight + root.Size.Y / 2
		root.Anchored = true
		n:PivotTo(CFrame.lookAt(feet + Vector3.new(0, up, 0), feet + Vector3.new(0, up, 0) + look))
		-- their colours, in turn
		local c = COLOURS[(i - 1) % #COLOURS + 1]
		for _, p in n:GetDescendants() do
			if p:IsA("BasePart") then
				p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
				local g = p:GetAttribute("Gear")
				if g == "hat" then p.Color = c.hat
				elseif g == "vest" then p.Color = c.vest
				elseif g == nil then
					-- (a plain body: shirt, trousers, a muted skin; no face)
					local nm = p.Name
					if string.find(nm, "Torso") or string.find(nm, "Arm") then p.Color = c.shirt
					elseif string.find(nm, "Leg") or string.find(nm, "Foot") then p.Color = c.legs
					elseif nm == "Head" or string.find(nm, "Hand") then p.Color = Color3.fromRGB(196, 170, 140) end
				end
			end
		end
		n.Parent = parent
		-- (sp[8], when there: the spot's own reaction - "duck" | "cower" at the draw, "flinch" at the shot - the one that
		-- fits its opening without passing through the town, as the clip check measured)
		table.insert(st.npcs, { model = n, root = root, kind = sp[6], react = sp[8], tracks = {}, phase = (i * 0.37) % 1, on = true })
	end
	return st
end

-- (built ahead: every onlooker's clips loaded now, so none loads on the scene's frames)
function Town.warm(st: any)
	if not st then return end
	for _, n in st.npcs do
		for key in Town.MOVES do track(n, key) end
	end
end

-- one clip at a moment, another faded in over it
local function pose(n: Npc, a: string, ta: number, b: string?, tb: number?, wb: number?)
	local want = { [a] = if b then 1 - (wb or 0) else 1 }
	if b then want[b] = math.max(wb or 0, 0.001) end
	for key, w in want do
		local tr = track(n, key)
		if tr then
			if not tr.IsPlaying then tr:Play(0, math.max(w, 0.001), 0) else tr:AdjustWeight(math.max(w, 0.001), 0) end
			local L = tr.Length
			local t = if key == a then ta else (tb or 0)
			if L > 0 then t = if key == "idle" or key == "look" then t % L else math.clamp(t, 0, L - 1 / 60) end
			tr.TimePosition = t
		end
	end
	for key, tr in n.tracks do
		if not want[key] and tr.IsPlaying then tr:Stop(0) end
	end
end

-- every frame: each onlooker on screen takes its pose for the scene's clock T (s)
function Town.step(st: any, T: number)
	if not st then return end
	local cam = workspace.CurrentCamera
	local X = Town.TIMES
	for _, n in st.npcs do
		if not n.root.Parent then continue end
		if cam then
			local v, onScreen = cam:WorldToViewportPoint(n.root.Position)
			if not onScreen or v.Z < 0 then continue end
		end
		local ph = n.phase
		local idleT = T * 0.9 + ph * 3
		local ducker = n.kind == "window" or n.kind == "door" or n.kind == "barrel"
		local react = n.react or (if ducker then "duck" else "flinch")
		local early = react ~= "flinch" -- (a duck or a cower comes at the draw; a flinch at the shot)
		local tDuck = X.duck + ph * 0.25
		local tShot = X.shot + 0.05 + ph * 0.15
		local function held(): number
			local tr = n.tracks[react]
			local L = if tr and tr.Length > 0 then tr.Length else 1
			return if react == "duck" then X.duckTo elseif react == "cower" then L * 0.6 else L * 0.55
		end
		if early and T >= tDuck and T < X.back + ph * 0.3 then
			local u = math.clamp((T - tDuck) / X.duckFor, 0, 1)
			if react == "duck" then
				-- down below the sill: the knockdown's fall, held at its lowest
				pose(n, "duck", X.duckFrom + (X.duckTo - X.duckFrom) * ease(u), "idle", idleT, 1 - ease(u * 3))
			else
				-- doubled over, held (a shallow room: the knockdown would carry them through its walls)
				pose(n, "cower", held() * ease(u), "idle", idleT, 1 - ease(u * 2.5))
			end
		elseif not early and T >= tShot and T < X.back + ph * 0.3 then
			-- a flinch at the shot: the guard thrown up, held
			local u = math.clamp((T - tShot) / X.flinchFor, 0, 1)
			pose(n, "flinch", held() * ease(u), "idle", idleT, 1 - ease(u * 2.5))
		elseif T >= X.back then
			-- peeking out again after: up into the look-round
			local u = math.clamp((T - X.back - ph * 0.3) / 0.6, 0, 1)
			pose(n, "look", (T - X.back) * 0.8, react, held(), 1 - ease(u))
		else
			-- the build-up: idle, a peek round for some
			local p0, p1 = X.peek0 + ph * 2, X.peek1 + ph
			local w = if (n.kind == "window" or n.kind == "balcony") and T >= p0 and T <= p1 then ease((T - p0) / 0.5) * ease((p1 - T) / 0.5) else 0
			pose(n, "idle", idleT, "look", (T - p0) * 0.7, w)
		end
	end
end

return Town
