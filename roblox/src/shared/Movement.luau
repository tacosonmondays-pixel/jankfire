--!strict
-- JANKFIRE movement maths, ported from public/js/player.js and shared/hookphys.js (the classic grapple). Pure functions
-- on plain numbers (studs, seconds) so tests run them outside Roblox (roblox/tests, `lune run`). The client controller
-- (Move.client.luau) feeds them the character's real velocity every frame and puts the result back.
local Config = require(script.Parent.Config)

local Movement = {}

export type Hook = { ax: number, ay: number, az: number, len: number? }
export type State = {
	vx: number, vy: number, vz: number,
	onGround: boolean, groundTicks: number, combo: number,
	hook: Hook?, lift: number, -- lift: the rope's share of your weight, fading out after you let go
	sliding: boolean, crouching: boolean, sprinting: boolean,
	slip: number?, -- seconds of slipping left (marbles): no grip, no jumping, no steering (public/js/player.js)
	slideT: number, slideCd: number, slideArmed: boolean, slideAir: number, -- the slide's time left, its cooldown, crouch let go since, time off the ground
}
export type Input = {
	wx: number, wz: number, -- unit wish direction (world, flat), 0,0 = no keys
	forward: boolean, -- holding W (sprint and air steering need it)
	sprint: boolean, crouch: boolean,
	jump: boolean, -- jump held or buffered this tick
	jumpPressed: boolean, -- jump went down this tick (grapple jump)
	lookX: number, lookZ: number, -- flat look direction
}

function Movement.newState(): State
	return { vx = 0, vy = 0, vz = 0, onGround = false, groundTicks = 0, combo = 0, hook = nil, lift = 0, sliding = false, crouching = false, sprinting = false,
		slideT = 0, slideCd = 0, slideArmed = true, slideAir = 0 }
end

-- quake accelerate: add speed along the wish direction up to wishSpeed
function Movement.accelerate(vx: number, vz: number, wx: number, wz: number, wishSpeed: number, accel: number, dt: number): (number, number)
	local cur = vx * wx + vz * wz
	local add = wishSpeed - cur
	if add <= 0 then return vx, vz end
	local a = math.min(accel * wishSpeed * dt, add)
	return vx + a * wx, vz + a * wz
end

-- ground friction (stop = the speed friction works from when you're nearly stopped, so you stop crisply)
function Movement.friction(vx: number, vz: number, fr: number, dt: number): (number, number)
	local hs = math.sqrt(vx * vx + vz * vz)
	if hs <= 0 then return vx, vz end
	local ns = math.max(0, hs - math.max(hs, Config.stop) * fr * dt) / hs
	return vx * ns, vz * ns
end

-- W-only air steering: turn your momentum toward where you look, keep ALL the speed
function Movement.airSteer(vx: number, vz: number, wx: number, wz: number, dt: number): (number, number)
	local hs = math.sqrt(vx * vx + vz * vz)
	if hs <= 2 * Config.S then return vx, vz end
	local cur, tgt = math.atan2(vx, vz), math.atan2(wx, wz)
	local da = tgt - cur
	while da > math.pi do da -= 2 * math.pi end
	while da < -math.pi do da += 2 * math.pi end
	if math.abs(da) >= math.pi / 2 then return vx, vz end
	local m = Config.airCtl * dt
	local na = cur + math.clamp(da, -m, m)
	return math.sin(na) * hs, math.cos(na) * hs
end

-- the classic grapple (hookphys.js classicRopeStep): a flat pull toward the point (off when close), the rope takes a
-- share of your weight, and it never lets you drift further away (the length only ever shrinks). p = your chest
function Movement.ropeStep(h: Hook, px: number, py: number, pz: number, vx: number, vy: number, vz: number, dt: number, grav: number): (number, number, number)
	local H = Config.hook
	local dx, dy, dz = h.ax - px, h.ay - py, h.az - pz
	local dist = math.sqrt(dx * dx + dy * dy + dz * dz)
	if dist < 0.03 then return vx, vy, vz end
	local nx, ny, nz = dx / dist, dy / dist, dz / dist
	local pull = if dist > H.near then H.pull else 0
	vx += nx * pull * dt; vy += ny * pull * dt; vz += nz * pull * dt
	vy += grav * H.lift * dt
	h.len = math.min(h.len or dist, dist)
	local radial = vx * nx + vy * ny + vz * nz
	if dist >= (h.len :: number) - 0.15 and radial < 0 then
		vx -= nx * radial; vy -= ny * radial; vz -= nz * radial
	end
	return vx, vy, vz
end

-- grapple jump (classicRopeJump): let go, keep your momentum +12% sideways, launch up
function Movement.ropeJump(vx: number, vy: number, vz: number): (number, number, number)
	local H = Config.hook
	return vx * H.jumpMul, math.max(vy, 0) * H.jumpMul + H.jumpUp, vz * H.jumpMul
end

-- the slide: crouch while fast on the ground. it lasts Config.slideTime at most (or till you let go of crouch, slow
-- right down or leave the ground), starts with a little shove and barely slows you, so your momentum carries. then a
-- short cooldown, and crouch has to be let go before the next. returns "slide" when one starts
function Movement.slideStep(st: State, inp: Input, dt: number, hs: number, slipping: boolean): (string?, number)
	st.slideCd = math.max(0, st.slideCd - dt)
	if not inp.crouch then st.slideArmed = true end
	local event: string? = nil
	if st.slideT > 0 then
		st.slideT -= dt
		st.slideAir = if st.onGround then 0 else st.slideAir + dt
		if st.slideT <= 0 or not inp.crouch or slipping or hs < Config.slideEnd or st.slideAir > 0.15 then
			st.slideT = 0
			st.slideCd = Config.slideCd
		end
	elseif inp.crouch and st.onGround and st.slideArmed and st.slideCd <= 0 and hs > Config.slideMin and not slipping and not inp.jump then
		st.slideT, st.slideArmed, st.slideAir = Config.slideTime, false, 0
		local ns = math.max(hs, math.min(hs + Config.slideBoost, Config.slideCap))
		st.vx, st.vz = st.vx / hs * ns, st.vz / hs * ns
		hs = ns
		event = "slide"
	end
	st.sliding = st.slideT > 0
	return event, hs
end

-- one tick of horizontal movement + the rope. gravity itself is the engine's (Workspace.Gravity): this only adds the
-- rope's lift. returns what happened this tick: "grappleJump" | "slideJump" | "slide" | "bhop" | nil
function Movement.step(st: State, inp: Input, dt: number, grav: number, chestX: number, chestY: number, chestZ: number): string?
	local event: string? = nil
	if inp.jumpPressed and st.hook then -- grapple jump
		st.hook = nil
		st.vx, st.vy, st.vz = Movement.ropeJump(st.vx, st.vy, st.vz)
		st.onGround = false
		st.lift = 1
		return "grappleJump"
	end
	local slipping = (st.slip or 0) > 0
	if slipping then st.slip = math.max(0, (st.slip :: number) - dt) end
	local hs = math.sqrt(st.vx * st.vx + st.vz * st.vz)
	event, hs = Movement.slideStep(st, inp, dt, hs, slipping)
	st.crouching = inp.crouch and not st.sliding
	st.sprinting = inp.sprint and not inp.crouch and inp.forward and st.onGround
	local moveMul = if st.sprinting then Config.sprintMul elseif st.crouching then Config.crouchMul else 1
	local wl = math.sqrt(inp.wx * inp.wx + inp.wz * inp.wz)
	if slipping then -- feet gone: next to no friction, no control, no jumping until you're up again
		if st.onGround then st.vx, st.vz = Movement.friction(st.vx, st.vz, 0.02, dt) end
	elseif st.onGround and not st.hook then
		if inp.jump then
			-- jumping on the first ticks of landing skips friction entirely = momentum is forever
			st.combo = if st.groundTicks <= Config.bhopTicks then st.combo + 1 else 1
			if st.combo >= 2 then event = "bhop" end
			if st.sliding then -- a slide jump: jump before the slide ends = more speed (and more height: Move.client)
				local ns = math.max(hs, math.min(hs + Config.slideJumpAdd, Config.slideJumpCap))
				if hs > 1e-3 then st.vx, st.vz = st.vx / hs * ns, st.vz / hs * ns end
				st.slideT, st.sliding, st.slideCd = 0, false, Config.slideCd
				event = "slideJump"
			end
		else
			st.vx, st.vz = Movement.friction(st.vx, st.vz, if st.sliding then Config.slideFric else Config.fric, dt)
			if not st.sliding and wl > 0 then
				st.vx, st.vz = Movement.accelerate(st.vx, st.vz, inp.wx, inp.wz, Config.gSpeed * moveMul, Config.gAccel * math.max(1, moveMul), dt)
			end
			if st.groundTicks > Config.bhopTicks and not st.sliding then st.combo = 0 end
		end
	elseif wl > 0 then
		st.vx, st.vz = Movement.accelerate(st.vx, st.vz, inp.wx, inp.wz, Config.airCap, Config.airAccel, dt)
		if inp.forward then
			local lw = math.sqrt(inp.lookX * inp.lookX + inp.lookZ * inp.lookZ)
			if lw > 0 then st.vx, st.vz = Movement.airSteer(st.vx, st.vz, inp.lookX / lw, inp.lookZ / lw, dt) end
		end
	end
	if st.hook then
		st.vx, st.vy, st.vz = Movement.ropeStep(st.hook, chestX, chestY, chestZ, st.vx, st.vy, st.vz, dt, grav)
		st.lift = 1
	elseif st.lift > 0 then -- letting go: the rope's share of your weight fades out instead of dropping you
		st.lift = math.max(0, st.lift - dt / Config.hook.letGo)
		st.vy += grav * Config.hook.lift * st.lift * dt
	end
	return event
end

-- slipped (marbles): 1.7 s, +6 m/s along your look, at least 6.5 m/s up, off the rope (public/js/player.js slip)
function Movement.slip(st: State, lookX: number, lookZ: number, time: number, fwd: number, up: number)
	st.slip = time
	local l = math.sqrt(lookX * lookX + lookZ * lookZ)
	if l > 0 then st.vx += lookX / l * fwd; st.vz += lookZ / l * fwd end
	st.vy = math.max(st.vy, up)
	st.onGround = false
	st.hook = nil
end

-- the eye height (camera) you ease toward
function Movement.eyeTarget(st: State): number
	return if st.sliding then Config.slideEye elseif st.crouching then Config.crouchEye else Config.standEye
end

return Movement
