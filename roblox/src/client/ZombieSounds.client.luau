--!strict
-- ZOMBIES sounds (27 Nov 2026, the owner: "Can we also have zombie sounds start of round sound effects that's like
-- imposing like what cod has, find what needs sound effects in gameplay and add it no generated stuff"). Every one a
-- recording: Roblox's licensed library (Pro Sound Effects) or the CC0 takes already in JankfireSounds; the picks and
-- their levels: roblox/assets/sounds/store.json (zm_*), docs/ZOMBIES.md 4.12. The zombies' voices are the owner's
-- exception to the no-voice rule (ZOMBIES only): creature groans, snarls, shrieks and death gurgles, never words.
--   * the round: our own sting (a deep boom with a double bell strike; a boss round, the boom, a deep metal boom and a
--     gong), a quiet gong as a round is cleared
--   * the zombies (workspace.Dummies, near this camera): a groan now and then, a snarl as one closes on you, a gurgle
--     as one dies, a boss's roar; at most three voices in any 1.6 s and a pitch jitter, so a full round never turns
--     into a wall of noise
--   * you: a claw's swipe and hit when a zombie is on you and your Hp drops; the body fall when someone goes down
--   * the windows' boards: the clatter as one is torn off, the knock as one is nailed back (zm_planks, zm_board)
--   * the economy and the world: credits (a soft coin, capped), a buy (the coin in the slot; a gun's ammo the magazine
--     too), a refusal (a dry click), the power's breaker and the tubes' buzz, a power-up's bell, a boss on the way
--   * the extraction: a gong as it's called, a clock's tick through the last ten seconds to lift-off
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local me = Players.LocalPlayer
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local ZM = require(Shared:WaitForChild("ZM"))
local okSfx, Sfx = pcall(require, script.Parent:WaitForChild("Sfx"))
local zr = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Zm") :: RemoteEvent

local rng = Random.new()
local BOSS: { [string]: boolean } = {}
for _, b in ZM.BOSSES do BOSS[b] = true end

local function play(name: string, at: Vector3?, vol: number?)
	if okSfx and Sfx then pcall((Sfx :: any).play, name, at, vol) end
end
local function inGame(): boolean return me:GetAttribute("ZmOn") == true end
local function srv(): number return workspace:GetServerTimeNow() end
local function arena(): Model?
	local n = me:GetAttribute("ZmArena")
	local a = if type(n) == "string" then workspace:FindFirstChild(n) else nil
	return if a and a:IsA("Model") then a else nil
end
local function myRoot(): BasePart?
	local ch = me.Character
	local r = ch and ch:FindFirstChild("HumanoidRootPart")
	return if r and r:IsA("BasePart") then r else nil
end

-- ------------------------------------------------------------ the voices' cap
local recent: { number } = {}
local function voice(name: string, at: Vector3?, vol: number?): boolean
	local t = os.clock()
	for i = #recent, 1, -1 do if t - recent[i] > 1.6 then table.remove(recent, i) end end
	if #recent >= 3 then return false end
	table.insert(recent, t)
	play(name, at, vol)
	return true
end

-- ------------------------------------------------------------ what the server says
local lastCredit = 0
zr.OnClientEvent:Connect(function(x: any)
	if type(x) ~= "table" or not inGame() then return end
	local k = x.k
	if k == "round" then
		if x.st == "start" then
			local n = tonumber(x.n) or 0
			play("zm_round")
			-- (a boss round: the metal boom with the boom, the gong half a second on; 27 Nov check: all at once clipped)
			if n > 0 and n % ZM.BOSS.every == 0 then play("zm_roundboss"); task.delay(0.5, function() play("zm_gong") end) else play("zm_roundbell") end
		else
			play("zm_roundend")
		end
	elseif k == "boss" then
		if x.st == "warn" then task.delay(1.6, function() play("zm_bossroar", nil, 0.85) end) end -- (after the round's sting)
	elseif k == "buy" then
		if x.ok == true then
			play("zm_buy")
			if type(x.m) == "string" and string.find(x.m, " ammo$") then play("zm_gunbuy") end
		else
			play("empty")
		end
	elseif k == "c" then
		local t = os.clock()
		if type(x.d) == "number" and x.d > 0 and x.why ~= "test" and t - lastCredit > 0.12 then lastCredit = t; play("zm_credit") end
	elseif k == "down" then
		if x.st == "down" then play("zm_downed", nil, if x.who == me.DisplayName then 1 else 0.55)
		elseif x.st == "up" then play("heal", nil, 0.7) end
	elseif k == "power" then
		play("zm_power")
		task.delay(0.35, function() play("zm_flicker") end)
	elseif k == "drop" then
		play("zm_roundbell", nil, 0.45)
	elseif k == "xcall" then
		play("zm_gong", nil, 0.8)
	end
end)

-- ------------------------------------------------------------ the zombies' voices
type Z = { m: Model, head: BasePart?, hum: Humanoid?, nextG: number, near: boolean, boss: boolean, dead: boolean }
local zs: { [Model]: Z } = {}
local function headOf(m: Model): BasePart?
	local h = m:FindFirstChild("Head")
	return if h and h:IsA("BasePart") then h else nil
end
local function died(z: Z)
	if z.dead then return end
	z.dead = true
	local h = z.head
	local cam = workspace.CurrentCamera
	if h and cam and (h.Position - cam.CFrame.Position).Magnitude < 70 and (z.boss or rng:NextNumber() < 0.7) then
		voice(if z.boss then "zm_bossroar" else "zm_zdie", h.Position)
	end
end
local function watchDummies(dm: Instance)
	dm.ChildRemoved:Connect(function(c: Instance)
		local z = zs[c :: any]
		if z then
			if inGame() then died(z) end
			zs[c :: any] = nil
		end
	end)
end
local dmSeen: Instance? = nil
task.spawn(function()
	while true do
		task.wait(0.2)
		local dm = workspace:FindFirstChild("Dummies")
		if dm and dm ~= dmSeen then dmSeen = dm; watchDummies(dm) end
		if not inGame() or not dm then
			if next(zs) then table.clear(zs) end
			continue
		end
		local cam = workspace.CurrentCamera
		if not cam then continue end
		local ear = cam.CFrame.Position
		local root = myRoot()
		local t = os.clock()
		local near = 0
		for _, z in zs do
			local h = z.head
			if h and (h.Position - ear).Magnitude < 45 then near += 1 end
		end
		for _, c in dm:GetChildren() do
			if not c:IsA("Model") then continue end
			local ty = c:GetAttribute("ZmType")
			if c.Name ~= "Zombie" and ty == nil then continue end
			local z = zs[c]
			if not z then
				local hum = c:FindFirstChildOfClass("Humanoid")
				local nz: Z = { m = c, head = headOf(c), hum = hum, nextG = t + rng:NextNumber(1.5, 7), near = false,
					boss = type(ty) == "string" and BOSS[ty] == true, dead = false }
				zs[c] = nz
				if hum then hum.Died:Connect(function() died(nz) end) end
				z = nz
			end
			local zz = z :: Z
			if zz.dead then continue end
			if zz.boss == false and type(ty) == "string" and BOSS[ty] then zz.boss = true end
			local h = zz.head or headOf(c)
			zz.head = h
			if not h then continue end
			local d = (h.Position - ear).Magnitude
			-- a snarl as it closes on you (once, till it's backed off)
			if root then
				local dr = (h.Position - root.Position).Magnitude
				if not zz.near and dr < 11 then
					zz.near = true
					if rng:NextNumber() < 0.7 then voice(if zz.boss then "zm_bossroar" else "zm_snarl", h.Position) end
				elseif zz.near and dr > 18 then
					zz.near = false
				end
			end
			-- a groan now and then (rarer, each, the more there are)
			if t >= zz.nextG and d < 55 then
				if voice(if zz.boss then "zm_bossroar" else "zm_groan", h.Position, if zz.boss then 0.7 else nil) then
					zz.nextG = t + rng:NextNumber(5, 12) * (1 + near / 8) * (if zz.boss then 1.6 else 1)
				else
					zz.nextG = t + rng:NextNumber(0.6, 2)
				end
			end
		end
	end
end)

-- ------------------------------------------------------------ the claws on you
local lastHp: number? = nil
me:GetAttributeChangedSignal("Hp"):Connect(function()
	local hp = tonumber(me:GetAttribute("Hp"))
	local was = lastHp
	lastHp = hp
	if not inGame() or not hp or not was or hp >= was then return end
	local root = myRoot()
	if not root then return end
	local best: Z? = nil
	local bd = 6
	for _, z in zs do
		local h = z.head
		if h and not z.dead then
			local d = (h.Position - root.Position).Magnitude
			if d < bd then bd, best = d, z end
		end
	end
	if not best then return end
	play("zm_swipe")
	task.delay(0.06, function() play("zm_claw") end)
	local bh = (best :: Z).head
	if bh and rng:NextNumber() < 0.35 then voice(if (best :: Z).boss then "zm_bossroar" else "zm_shriek", bh.Position) end
end)

-- ------------------------------------------------------------ the windows' boards
local planksOf: { [Instance]: boolean } = {}
local quietUntil = 0
local lastBoard = 0
local function watchPlank(p: BasePart)
	if planksOf[p] then return end
	planksOf[p] = true
	local was = p.Transparency
	p:GetPropertyChangedSignal("Transparency"):Connect(function()
		local now = p.Transparency
		local t = os.clock()
		if t < quietUntil or t - lastBoard < 0.2 then was = now; return end
		if was < 0.5 and now >= 0.5 then lastBoard = t; play("zm_planks", p.Position) -- (torn off)
		elseif was >= 0.5 and now < 0.5 then lastBoard = t; play("zm_board", p.Position) end -- (nailed back)
		was = now
	end)
	p.Destroying:Connect(function() planksOf[p] = nil end)
end
task.spawn(function()
	local seen: Instance? = nil
	while true do
		task.wait(1)
		local a = if inGame() then arena() else nil
		local ex = a and a:FindFirstChild("ZMExtra")
		if ex and ex ~= seen then
			seen = ex
			quietUntil = os.clock() + 3 -- (the game's first showing of the boards)
		end
		if ex then
			for _, p in ex:GetChildren() do
				if p.Name == "Plank" and p:IsA("BasePart") then watchPlank(p) end
			end
		end
	end
end)

-- ------------------------------------------------------------ the extraction's last ten seconds
local XC = ZM.X
local lastTick = -1
RunService.Heartbeat:Connect(function()
	if not inGame() then return end
	local a = arena()
	if not a or a:GetAttribute("XSt") ~= "hold" then lastTick = -1; return end
	local t0 = a:GetAttribute("XT0")
	if type(t0) ~= "number" or type(XC) ~= "table" or type(XC.hold) ~= "number" then return end
	local left = XC.hold - (srv() - t0)
	if left > 0 and left <= 10 then
		local s = math.ceil(left)
		if s ~= lastTick then lastTick = s; play("zm_tick") end
	end
end)
