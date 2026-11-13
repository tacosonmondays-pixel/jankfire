-- JANKFIRE Roblox: tests that run outside Studio, with Lune (https://lune-org.github.io). from roblox/:
--   lune run tests/run
-- the game's modules use Roblox-style requires (script.Parent.Config); here they're loaded with a stand-in for that
local fs = require("@lune/fs")
local luau = require("@lune/luau")
local serde = require("@lune/serde")
local process = require("@lune/process")
local roblox = require("@lune/roblox")

local fails, passes = 0, 0
local function check(ok: boolean, what: string)
	if ok then passes += 1 else fails += 1; print("FAIL: " .. what) end
end
local function near(a: number, b: number, tol: number): boolean return math.abs(a - b) <= tol end

-- selene: allow(global_usage)
local function load(path: string, provides: { [string]: any }): any
	local env = setmetatable({
		CFrame = roblox.CFrame, Vector3 = roblox.Vector3, Color3 = roblox.Color3, Instance = roblox.Instance,
		script = { Parent = setmetatable({}, { __index = function(_, k) return { __mod = k } end }) },
		game = { GetService = function() return { WaitForChild = function(_, k) return { __mod = k, WaitForChild = function(_, k2) return { __mod = k2 } end } end } end },
		require = function(m) return provides[m.__mod] end,
	}, { __index = _G })
	return luau.load(fs.readFile(path), { debugName = path, environment = env })()
end

local Config = load("src/shared/Config.luau", {})
local Movement = load("src/shared/Movement.luau", { Config = Config })
local HookCheck = load("src/server/HookCheck.luau", { Config = Config })
-- MeshSwap gets Lune's real Roblox datatypes (CFrame, Vector3, Instance)
local MeshSwap = load("src/server/MeshSwap.luau", {})
local S = Config.S

-- ---------------------------------------------------------------- movement
local function input(o: { [string]: any }?): any
	local i = { wx = 0, wz = 0, forward = false, sprint = false, crouch = false, jump = false, jumpPressed = false, lookX = 0, lookZ = 1 }
	for k, v in o or {} do i[k] = v end
	return i
end
local dt = 1 / 60
do -- run from standing: up to 10 m/s, sprint to 14.5
	local st = Movement.newState(); st.onGround = true
	for _ = 1, 120 do st.groundTicks += 1; Movement.step(st, input({ wz = 1, forward = true, lookZ = 1 }), dt, Config.grav, 0, 0, 0) end
	check(near(st.vz, 10 * S, 0.5), ("runs at 10 m/s (got %.2f studs/s)"):format(st.vz))
	for _ = 1, 120 do st.groundTicks += 1; Movement.step(st, input({ wz = 1, forward = true, sprint = true }), dt, Config.grav, 0, 0, 0) end
	check(near(st.vz, 14.5 * S, 0.7), ("sprints at 14.5 m/s (got %.2f)"):format(st.vz))
	check(st.sprinting, "sprinting flag")
	-- let go: friction stops you in well under a second
	for _ = 1, 40 do st.groundTicks += 1; Movement.step(st, input(), dt, Config.grav, 0, 0, 0) end
	check(math.abs(st.vz) < 0.5, ("stops when you let go (%.2f)"):format(st.vz))
end
do -- slide: crouch at sprint speed keeps most of it for a second, then it ends below slideMin
	local st = Movement.newState(); st.onGround = true; st.groundTicks = 10; st.vz = 14.5 * S
	Movement.step(st, input({ crouch = true }), dt, Config.grav, 0, 0, 0)
	check(st.sliding, "crouch while fast = slide")
	for _ = 1, 59 do st.groundTicks += 1; Movement.step(st, input({ crouch = true }), dt, Config.grav, 0, 0, 0) end
	check(st.vz > 10.5 * S and st.vz < 12 * S, ("a 1 s slide keeps ~78%% (got %.1f m/s)"):format(st.vz / S))
	for _ = 1, 600 do st.groundTicks += 1; Movement.step(st, input({ crouch = true }), dt, Config.grav, 0, 0, 0) end
	check(not st.sliding and st.crouching, "slow slide turns into a crouch")
	check(st.vz < Config.slideMin, "slide ends under slideMin")
end
do -- bhop: jumping on the landing tick skips friction (momentum is forever) and counts the combo
	local st = Movement.newState(); st.onGround = true; st.groundTicks = 1; st.vz = 20 * S; st.combo = 1
	Movement.step(st, input({ jump = true }), dt, Config.grav, 0, 0, 0)
	check(st.vz == 20 * S, "a bhop keeps every bit of speed")
	check(st.combo == 2, "bhop combo counts")
	local st2 = Movement.newState(); st2.onGround = true; st2.groundTicks = 10; st2.vz = 20 * S
	Movement.step(st2, input(), dt, Config.grav, 0, 0, 0)
	check(st2.vz < 20 * S, "standing on the ground: friction")
end
do -- air: holding W turns momentum toward the look and keeps all of it; strafing caps small but adds
	local st = Movement.newState(); st.vz = 15 * S
	for _ = 1, 30 do Movement.step(st, input({ wx = 1, forward = true, lookX = 1, lookZ = 0 }), dt, Config.grav, 0, 0, 0) end
	local hs = math.sqrt(st.vx * st.vx + st.vz * st.vz)
	check(st.vx > 0 and hs >= 15 * S - 0.01, ("air steer turns, keeps speed (%.2f m/s, vx %.1f)"):format(hs / S, st.vx))
	local a = Movement.newState()
	for _ = 1, 60 do Movement.step(a, input({ wx = 1 }), dt, Config.grav, 0, 0, 0) end
	check(near(a.vx, Config.airCap, 0.01), "air accel caps at airCap from standing")
end
-- ---------------------------------------------------------------- the grapple against the web game's own (metres x 3)
do
	local trace = serde.decode("json", fs.readFile("tests/rope-trace.json"))
	for _, c in trace.cases do
		local p = { c.p[1] * S, c.p[2] * S, c.p[3] * S }
		local v = { c.v[1] * S, c.v[2] * S, c.v[3] * S }
		local h = { ax = c.a[1] * S, ay = c.a[2] * S, az = c.a[3] * S, len = nil }
		local grav, tdt = trace.grav * S, trace.dt
		local worst = 0
		local k = 0
		for i = 1, c.steps do
			v[2] -= grav * tdt
			-- the web game pulls from p.y + 1 m (the chest): same here
			v[1], v[2], v[3] = Movement.ropeStep(h, p[1], p[2] + S, p[3], v[1], v[2], v[3], tdt, grav)
			for j = 1, 3 do p[j] += v[j] * tdt end
			if i % 30 == 0 then
				k += 1
				local e = c.pts[k]
				for j = 1, 3 do worst = math.max(worst, math.abs(p[j] / S - e[j]), math.abs(v[j] / S - e[j + 3])) end
			end
		end
		check(worst < 1e-6, ("grapple '%s' matches the web game (worst diff %.2e m)"):format(c.name, worst))
		local jx, jy, jz = Movement.ropeJump(v[1], v[2], v[3])
		check(near(jx / S, c.jump[1], 1e-6) and near(jy / S, c.jump[2], 1e-6) and near(jz / S, c.jump[3], 1e-6), "grapple jump matches: " .. c.name)
	end
	-- through Movement.step: hooked, grapple jump releases and flings up
	local st = Movement.newState(); st.vx = 30
	st.hook = { ax = 0, ay = 100, az = 0 }
	Movement.step(st, input(), dt, Config.grav, 0, 0, 0)
	check(st.vy > 0, "the rope pulls you up toward the point")
	local ev = Movement.step(st, input({ jumpPressed = true }), dt, Config.grav, 0, 0, 0)
	check(ev == "grappleJump" and st.hook == nil and st.vy >= Config.hook.jumpUp, "space on the rope = grapple jump")
	check(st.lift == 1, "the rope's lift fades instead of dropping you")
end
-- ---------------------------------------------------------------- the server's hook checks
do
	check(HookCheck.point(1, 2, 3) == nil, "a real point")
	check(HookCheck.point(0 / 0, 2, 3) ~= nil and HookCheck.point(math.huge, 0, 0) ~= nil and HookCheck.point("1", 2, 3) ~= nil, "NaN / inf / strings refused")
	check(HookCheck.reach(100, 100, 100.5) == nil, "in range, in sight")
	check(HookCheck.reach(Config.hook.range + 50, 300, 300) ~= nil, "out of range refused")
	check(HookCheck.reach(100, 100, 40) ~= nil, "a wall in the way refused")
	check(HookCheck.reach(100, 100, nil) ~= nil, "a point in thin air refused")
	local t = {}
	local ok = 0
	for i = 1, 20 do if HookCheck.rate(t, i * 0.01) then ok += 1 end end
	check(ok == Config.check.hookRate, ("hook spam capped at %d/s (got %d)"):format(Config.check.hookRate, ok))
	check(HookCheck.rate(t, 5), "allowed again a second later")
end
-- ---------------------------------------------------------------- MeshSwap: a model lands where the web game draws it
do
	local V3, CF = roblox.Vector3, roblox.CFrame
	-- a two-piece model in the file (metres): a body box [-1,0,-0.7]..[1,1.5,0.7] and a fan on top (centre 0.5,1.6,0)
	local fileLo, fileHi = V3.new(-1, 0, -0.7), V3.new(1, 1.7, 0.7)
	local fileCentre, fileSize = (fileLo + fileHi) / 2, fileHi - fileLo
	local pieces = { { name = "ac_metal", c = V3.new(0, 0.75, 0), s = V3.new(2, 1.5, 1.4) }, { name = "fan", c = V3.new(0.5, 1.6, 0), s = V3.new(0.6, 0.2, 0.6) } }
	-- imported into Studio at some odd scale and spot (the importer's choice): 3.7 studs per metre, somewhere else
	local imp, at = 3.7, V3.new(500, 20, -80)
	local tmpl = roblox.Instance.new("Model")
	for _, p in pieces do
		local part = roblox.Instance.new("Part")
		part.Name = p.name; part.Size = p.s * imp; part.CFrame = CF.new(at + (p.c - fileCentre) * imp); part.Parent = tmpl
	end
	-- the web game's placement: fitted per axis (K studs per file metre) and turned 90 degrees, its box centre at `place`
	local K = V3.new(3, 4.5, 2.4)
	local place = CF.new(30, 6, -12) * CF.Angles(0, math.pi / 2, 0)
	MeshSwap.fitParts(tmpl, CF.new(at), fileSize * imp, { K = K, FileSize = fileSize }, place)
	local worst = 0
	for _, p in pieces do
		local part = tmpl:FindFirstChild(p.name)
		local want = place:PointToWorldSpace((p.c - fileCentre) * K)
		local wantSize = p.s * K
		worst = math.max(worst, (part.CFrame.Position - want).Magnitude, (part.Size - wantSize).Magnitude)
	end
	check(worst < 1e-4, ("MeshSwap puts every piece where the web game draws it (worst %.1e studs)"):format(worst))
	-- variants: only the placement's v-piece stays
	local m2 = roblox.Instance.new("Model")
	for _, n in { "v0_band", "v1_band", "v2_band", "lr_wall" } do local p = roblox.Instance.new("Part"); p.Name = n; p.Parent = m2 end
	MeshSwap.fitParts(m2, CF.new(), V3.new(1, 1, 1), { K = V3.new(3, 3, 3), FileSize = V3.new(1, 1, 1), Variant = "v1" }, CF.new())
	check(m2:FindFirstChild("v1_band") ~= nil and m2:FindFirstChild("v0_band") == nil and m2:FindFirstChild("v2_band") == nil and m2:FindFirstChild("lr_wall") ~= nil, "a placement keeps only its own variant's pieces")
end
-- ---------------------------------------------------------------- the built place file
do
	local file = "build/JANKFIRE-Rooftop.rbxl"
	if fs.isFile(file) then
		local game = roblox.deserializePlace(fs.readFile(file))
		local ws = game:GetService("Workspace")
		local mapm = ws:FindFirstChild("Map") and ws.Map:FindFirstChild("Rooftop")
		check(mapm ~= nil, "place has Workspace.Map.Rooftop")
		local parts = serde.decode("json", fs.readFile("build/rooftop.parts.json"))
		local n, pads, spawns, markers = 0, 0, 0, 0
		for _, d in mapm:GetDescendants() do
			if d.ClassName == "Part" and d.Parent.Name ~= "ModelMarkers" and d.Parent.Name ~= "TeamSpawns" then
				n += 1
				if d:GetAttribute("Pad") then pads += 1 end
			elseif d.ClassName == "SpawnLocation" then spawns += 1
			elseif d.Parent and d.Parent.Name == "ModelMarkers" then markers += 1 end
		end
		check(n == #parts.parts, ("every map box is a Part (%d of %d)"):format(n, #parts.parts))
		check(pads == 6, "6 jump pads with their launch velocity")
		check(spawns == #parts.spawns, "spawns")
		check(markers > 0, "Blender model markers")
		check(mapm:GetAttribute("KillY") ~= nil, "kill height on the map")
		check(ws.Gravity == Config.grav, "Workspace.Gravity = JANKFIRE's")
		local sss = game:GetService("ServerScriptService")
		check(sss:FindFirstChild("Jankfire") and sss.Jankfire:FindFirstChild("Main") and sss.Jankfire.Main.ClassName == "Script", "server script")
		local sp = game:GetService("StarterPlayer")
		local cl = sp.StarterPlayerScripts:FindFirstChild("Jankfire")
		check(cl and cl:FindFirstChild("Move") and cl.Move.ClassName == "LocalScript", "client movement script")
		local rs = game:GetService("ReplicatedStorage")
		check(rs:FindFirstChild("JankfireRemotes") and rs.JankfireRemotes:FindFirstChild("Grapple") ~= nil, "remotes")
	else
		print("(no built place yet: node tools/roblox/build.mjs)")
	end
end

print(("%d passed, %d failed"):format(passes, fails))
process.exit(if fails > 0 then 1 else 0)
