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
	slideFric = 0.25, -- a slide barely slows you: it carries your momentum
	slideMin = 7 * S, -- crouch while faster than this = slide
	slideTime = 0.8, -- s: a slide lasts this long at most (or till you let go of crouch / slow right down)
	slideBoost = 3 * S, -- a slide starts with this shove...
	slideCap = 17 * S, -- ...up to this speed (already faster: you keep what you have)
	slideEnd = 4 * S, -- slower than this, the slide's over
	slideCd = 0.45, -- s before the next slide (and crouch has to be let go first)
	slideJumpAdd = 3 * S, -- jump before the slide ends: this much more speed...
	slideJumpCap = 20 * S, -- ...up to this
	slideJumpUp = 1.2, -- and 20% more jump
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
		-- hooked to a person (18 Nov 2026, the web's tryHook / hookPoint): the rope ties on this far over their root (their
		-- chest), lets go this close to them (the web's 3.2 m: your momentum carries you into them) and drops when they've
		-- been out of your sight this long (the server allows a little more, for lag)
		bodyUp = 1, bodyLet = 3.2 * S, bodyBlind = 0.4,
		-- the yank (18 Nov 2026, the owner: "maybe you can press a button to like pull them towards you"): with the rope on
		-- a person, the YANK key pulls them toward you once and the rope drops. aimed so they'd fly about yankAir s and
		-- land short of you, at most yankSpeed sideways (a point-blank frag shoves 34 m/s) and yankUp up (off their feet;
		-- more when you're above them, up to yankClimb more). someone you can't hurt (a teammate) gets yankMate of it, a
		-- rescue. one every yankCool s (the server's say-so). not in the hub
		yankSpeed = 30 * S, yankUp = 9 * S, yankClimb = 10 * S, yankAir = 0.7, yankMate = 0.45, yankCool = 3,
		-- the reel (19 Nov 2026, the owner: "the same way how you press F to push people in, I want a button that reels you
		-- in"): with your rope on anything (a wall or a person), the REEL key pulls YOU along it to the hook point at
		-- reelSpeed, the yank's mirror. it ends when you get there (reelArrive off a wall point, bodyLet off a person),
		-- when you let go, or after reelMax s; reelKeep of the speed carries on. one every reelCool s (the server's say-so)
		reelSpeed = 55 * S, reelArrive = 1.5 * S, reelMax = 2, reelKeep = 0.45, reelCool = 3,
		-- the tie (19 Nov 2026, the owner: "tie, then choose"): a rope on a PERSON doesn't pull you in any more. it ties and
		-- holds taut: no pull, no lift, its length only ever shortens (never under tieMin), and when they get further than
		-- that you're dragged after them, tieK x the slack a second, at most tieDrag. then you choose: F yanks them to you,
		-- X reels you to them, or let go. ropes on walls, ledges and points pull you in as before
		tieMin = 3.2 * S, tieK = 8, tieDrag = 20 * S,
	},
	-- loot (server/Loot.luau, shared/LootTable.luau): LOOT_FREE = containers cost nothing and open even with none in
	-- stock (while we test); LOOT_ROBUX = sell them through developer products (Shop.luau's product ids; receipts:
	-- ShopReceipts.server.luau -> Loot.grant). off until the owner turns it on
	LOOT_FREE = false, -- (real money on, 18 Nov 2026, the owner: "Lets get the shop going!". docs/MONEY.md)
	LOOT_ROBUX = true,
	-- server checks (generous: movement is the client's, the server only catches teleports)
	check = {
		maxSpeed = 140 * S, -- studs/s, well past any bhop/grapple speed the web game sees
		slack = 30, -- studs of lag allowance per check
		hookSlack = 12, -- studs: a hook point can be this far past the range (lag)
		hookRate = 6, -- hook requests per second
	},
}

return Config
