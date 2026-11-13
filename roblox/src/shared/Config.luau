--!strict
-- JANKFIRE's movement numbers, copied from the web game (metres and seconds there) and scaled to studs here.
-- 1 m = 3 studs: a 1.8 m JANKFIRE player is 5.4 studs, about a Roblox R15 character. speeds and accelerations scale
-- by 3, rates (friction, air steering) don't.
local S = 3

local Config = {
	S = S,
	-- public/js/player.js C
	grav = 26 * S, -- Workspace.Gravity (Roblox's default is 196.2)
	jump = 9.2 * S, -- Humanoid.JumpPower: about 1.6 m (4.9 studs) high
	gSpeed = 10 * S, -- run
	gAccel = 11,
	fric = 6,
	stop = 3 * S,
	airCap = 1.4 * S, -- air strafing: a small cap, a huge accel = quake-style strafe turns
	airAccel = 90,
	airCtl = 2.6, -- rad/s: holding W turns your momentum toward where you look and keeps all of it
	slideFric = 0.25,
	slideMin = 7 * S, -- crouch while faster than this = slide
	sprintMul = 1.45,
	crouchMul = 0.45,
	standEye = 1.6 * S,
	crouchEye = 1.05 * S,
	slideEye = 0.95 * S,
	bhopTicks = 3, -- jump within this many ground ticks of landing: no friction, the combo goes up
	-- shared/weapons.js HOOK + shared/hookphys.js classic grapple (what players use)
	hook = {
		range = 90 * S,
		pull = 42 * S, -- steady pull toward the point
		near = 2 * S, -- the pull switches off this close
		lift = 0.35, -- share of gravity the rope takes
		letGo = 0.15, -- s: that share fades out over this after you let go
		jumpMul = 1.12, -- grapple jump: keep your momentum, +12% sideways
		jumpUp = 11 * S, -- and get launched up
		chest = 1 * S, -- the rope pulls from your chest, 1 m over your feet
	},
	-- server checks (generous: movement is the client's, the server only catches teleports)
	check = {
		maxSpeed = 140 * S, -- studs/s, well past any bhop/grapple speed the web game sees
		slack = 30, -- studs of lag allowance per check
		hookSlack = 12, -- studs: a hook point can be this far past the range (lag)
		hookRate = 6, -- hook requests per second
	},
}

return Config
