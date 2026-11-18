--!strict
-- THE ARCADE CABINET, your side (shared/MiniGames.luau; server/MiniArcade). MiniGames.client calls this.
--   world: each cabinet's screen (a SurfaceGui in your PlayerGui on the cabinet's Screen part) shows the server's high
--          scores, or who is playing, their score and wave; the marquee carries the game's name
--   your game: the camera goes into the screen and the screen takes over: a small top-down JANKFIRE. you against
--          waves of bots (grunts that keep their distance and shoot, rushers that charge, heavies that spray) in a
--          walled yard with cover; three of the game's own guns (Redline, Shotgun, Sniper) and a dash. a kill scores
--          more in a quick chain (x1 to x3), a cleared wave adds a bonus and a little health. the run ends when you
--          drop; the score goes to the server's board
--   keys: WASD / arrows move, the mouse aims, click fires, 1 2 3 or the wheel switch guns, R reloads, Space or Shift
--         dashes. a pad: left stick moves, right stick aims, RT fires, RB / Y next gun, X reloads, A dashes. a phone:
--         a stick on each side (the right one aims and fires), DASH and the gun button
-- the game is drawn in one 640 x 400 yard (16:10), every frame placed by scale so it fits any screen
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local HttpService = game:GetService("HttpService")
local MG = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("MiniGames")) :: any

local M = {}
local me = Players.LocalPlayer
local W, H = 640, 400
local INK = Color3.fromRGB(21, 24, 30)

local function boardOf(model: Model): { any }
	local f = model.Parent
	local raw = f and f:GetAttribute("ArcadeBoard")
	if type(raw) ~= "string" then return {} end
	local ok, t = pcall(HttpService.JSONDecode, HttpService, raw)
	return if ok and type(t) == "table" then t else {}
end
local function fmt(n: number): string
	local s = tostring(math.floor(n))
	local out = s:reverse():gsub("(%d%d%d)", "%1,"):reverse()
	if out:sub(1, 1) == "," then out = out:sub(2) end
	return out
end

-- ------------------------------------------------------------------ the cabinet's screen (everyone)
function M.world(model: Model, api: any): ((number) -> ())?
	local T = api.T
	local scr = model:WaitForChild("Screen", 10) :: BasePart?
	local mq = model:WaitForChild("Marquee", 10) :: BasePart?
	if not scr or not mq then return nil end
	local pg = me:WaitForChild("PlayerGui")
	local sg = T.new("SurfaceGui", { Name = "MiniArcadeScreen", Face = Enum.NormalId.Front, Adornee = scr, ResetOnSpawn = false,
		SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud, PixelsPerStud = 140, LightInfluence = 0, Brightness = 1.4,
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, pg)
	local bg = T.new("Frame", { Name = "Bg", BackgroundColor3 = INK, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1) }, sg)
	local head = T.text(bg, "Head", "JANKFIRE", 30, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Center)
	head.Position = UDim2.fromScale(0, 0.04); head.Size = UDim2.fromScale(1, 0.13)
	local sub = T.text(bg, "Sub", "HIGH SCORES", 15, T.ACCENT, T.FONT_TITLE, Enum.TextXAlignment.Center)
	sub.Position = UDim2.fromScale(0, 0.18); sub.Size = UDim2.fromScale(1, 0.08)
	local rows: { TextLabel } = {}
	for i = 1, 6 do
		local r = T.text(bg, "Row" .. i, "", 15, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Left)
		r.Position = UDim2.new(0.08, 0, 0.29 + (i - 1) * 0.1, 0); r.Size = UDim2.new(0.84, 0, 0.09, 0)
		r.RichText = true
		rows[i] = r
	end
	local foot = T.text(bg, "Foot", "", 13, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center)
	foot.Position = UDim2.fromScale(0, 0.9); foot.Size = UDim2.fromScale(1, 0.07)
	local msg = T.new("SurfaceGui", { Name = "MiniArcadeMarquee", Face = Enum.NormalId.Front, Adornee = mq, ResetOnSpawn = false,
		SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud, PixelsPerStud = 120, LightInfluence = 0 }, pg)
	local title = T.text(msg, "Title", "JANKFIRE", 52, Color3.fromRGB(58, 63, 72), T.FONT_SHOUT, Enum.TextXAlignment.Center)
	title.Size = UDim2.fromScale(1, 1)
	local function draw()
		local live = model:GetAttribute("Live")
		if type(live) == "number" then
			head.Text = "NOW PLAYING"
			head.TextSize = 22
			sub.Text = string.upper((model:GetAttribute("PName") or "") :: string)
			rows[1].Text = ""
			rows[2].Text = ("<font size=\"30\">%s</font>"):format(fmt(live))
			rows[2].TextXAlignment = Enum.TextXAlignment.Center
			rows[3].Text = ""
			rows[4].Text = "WAVE " .. tostring(model:GetAttribute("Wave") or 1)
			rows[4].TextXAlignment = Enum.TextXAlignment.Center
			for i = 5, 6 do rows[i].Text = "" end
			foot.Text = ""
		else
			head.Text = "JANKFIRE"
			head.TextSize = 30
			sub.Text = "HIGH SCORES"
			local b = boardOf(model)
			for i = 1, 6 do
				local e = b[i]
				rows[i].TextXAlignment = Enum.TextXAlignment.Left
				rows[i].Text = if e then ("%d   %s<font color=\"#9ca2ac\">  ·  </font>%s"):format(i, string.upper(tostring(e.n)):sub(1, 14), fmt(e.s)) else ""
			end
			foot.Text = if #b == 0 then "NO SCORES YET" else ""
		end
	end
	draw()
	model:GetAttributeChangedSignal("Live"):Connect(draw)
	model:GetAttributeChangedSignal("Wave"):Connect(draw)
	model:GetAttributeChangedSignal("PName"):Connect(draw)
	local f = model.Parent
	if f then f:GetAttributeChangedSignal("ArcadeBoard"):Connect(draw) end
	model.Destroying:Connect(function() sg:Destroy(); msg:Destroy() end)
	return nil
end

-- ------------------------------------------------------------------ the game
local GUNS = {
	{ id = "redline", name = "REDLINE", rate = 0.11, dmg = 16, speed = 720, spread = 0.05, pellets = 1, mag = 30, reload = 1.3, life = 0.9, sound = "gun_redline_k0", vol = 0.22 },
	{ id = "shotgun", name = "SHOTGUN", rate = 0.72, dmg = 12, speed = 640, spread = 0.34, pellets = 7, mag = 6, reload = 1.6, life = 0.42, sound = "gun_shotgun", vol = 0.3 },
	{ id = "sniper", name = "SNIPER", rate = 0.95, dmg = 130, speed = 1600, spread = 0, pellets = 1, mag = 5, reload = 1.9, life = 0.6, pierce = true, sound = "gun_sniper", vol = 0.3 },
}
local KINDS = {
	grunt = { r = 9, hp = 40, speed = 62, pts = 100, color = Color3.fromRGB(196, 88, 80), shoot = { every = { 1.6, 2.4 }, speed = 230, dmg = 9, n = 1, spread = 0 }, keep = { 150, 240 } },
	rusher = { r = 8, hp = 26, speed = 128, pts = 120, color = Color3.fromRGB(214, 142, 96), touch = 14 },
	heavy = { r = 13, hp = 150, speed = 40, pts = 300, color = Color3.fromRGB(150, 72, 78), shoot = { every = { 2.2, 3.0 }, speed = 200, dmg = 10, n = 3, spread = 0.28 }, keep = { 120, 200 } },
}
local COVER = { { 150, 110, 70, 26 }, { 420, 110, 70, 26 }, { 150, 264, 70, 26 }, { 420, 264, 70, 26 }, { 300, 180, 40, 40 } }
local P_SPEED, DASH_T, DASH_V, DASH_CD = 168, 0.16, 560, 1.0
local CHAIN_T = 2.5

local G: { [string]: any } = {}
local rng = Random.new()

local function frame(parent: Instance, color: Color3, round: boolean?, z: number?): Frame
	local f = Instance.new("Frame")
	f.BackgroundColor3 = color
	f.BorderSizePixel = 0
	f.AnchorPoint = Vector2.new(0.5, 0.5)
	f.ZIndex = z or 2
	if round then local c = Instance.new("UICorner"); c.CornerRadius = UDim.new(0.5, 0); c.Parent = f end
	f.Parent = parent
	return f
end
local function put(f: GuiObject, x: number, y: number, w: number, h: number)
	f.Position = UDim2.fromScale(x / W, y / H)
	f.Size = UDim2.fromScale(w / W, h / H)
end

local function inCover(x: number, y: number, pad: number): { number }?
	for _, c in COVER do
		if x > c[1] - pad and x < c[1] + c[3] + pad and y > c[2] - pad and y < c[2] + c[4] + pad then return c end
	end
	return nil
end
-- push a circle out of the walls and the cover
local function collide(e: any)
	e.x = math.clamp(e.x, 14 + e.r, W - 14 - e.r)
	e.y = math.clamp(e.y, 14 + e.r, H - 14 - e.r)
	for _, c in COVER do
		local cx = math.clamp(e.x, c[1], c[1] + c[3])
		local cy = math.clamp(e.y, c[2], c[2] + c[4])
		local dx, dy = e.x - cx, e.y - cy
		local d = math.sqrt(dx * dx + dy * dy)
		if d < e.r then
			if d < 0.01 then
				-- (inside: out the nearest side)
				local l, r, t, b = e.x - c[1], c[1] + c[3] - e.x, e.y - c[2], c[2] + c[4] - e.y
				local m = math.min(l, r, t, b)
				if m == l then e.x = c[1] - e.r elseif m == r then e.x = c[1] + c[3] + e.r elseif m == t then e.y = c[2] - e.r else e.y = c[2] + c[4] + e.r end
			else
				e.x = cx + dx / d * e.r
				e.y = cy + dy / d * e.r
			end
		end
	end
end

local function popup(text: string, x: number, y: number, color: Color3)
	local T = G.api.T
	local l = T.text(G.canvas, "Pop", text, 13, color, T.FONT_BOLD, Enum.TextXAlignment.Center)
	l.AnchorPoint = Vector2.new(0.5, 0.5); l.ZIndex = 6
	put(l, x, y, 80, 16)
	table.insert(G.fx, { f = l, t = 0, life = 0.7, x = x, y = y, vy = -40, kind = "pop" })
end
local function ringFx(x: number, y: number, r: number, color: Color3)
	local f = frame(G.canvas, color, true, 1)
	f.BackgroundTransparency = 1
	local s = Instance.new("UIStroke"); s.Color = color; s.Thickness = 2; s.Parent = f
	put(f, x, y, r * 2, r * 2)
	table.insert(G.fx, { f = f, s = s, t = 0, life = 0.35, x = x, y = y, r = r, kind = "ring" })
end
local function burst(x: number, y: number, color: Color3, n: number)
	for _ = 1, n do
		local f = frame(G.canvas, color, false, 1)
		local a = rng:NextNumber(0, math.pi * 2)
		local v = rng:NextNumber(60, 170)
		put(f, x, y, 4, 4)
		table.insert(G.fx, { f = f, t = 0, life = rng:NextNumber(0.25, 0.45), x = x, y = y, vx = math.cos(a) * v, vy = math.sin(a) * v, kind = "spark" })
	end
end

local function sfx(name: string, vol: number?)
	G.api.Sfx.play(name, nil, vol or 0.4)
end

-- ------------------------------------------------------------------ a run
local function clearWorld()
	for _, list in { G.enemies or {}, G.bullets or {}, G.pickups or {}, G.fx or {} } do
		for _, e in list do if e.f then e.f:Destroy() end end
	end
	G.enemies, G.bullets, G.pickups, G.fx, G.spawns = {}, {}, {}, {}, {}
end

local function newRun()
	clearWorld()
	local p = G.p
	p.x, p.y, p.vx, p.vy = W / 2, H / 2 + 60, 0, 0
	p.hp, p.gun, p.fireCd, p.reload, p.dashCd, p.dashT, p.inv = 100, 1, 0, 0, 0, 0, 0
	p.ammo = { GUNS[1].mag, GUNS[2].mag, GUNS[3].mag }
	G.score, G.kills, G.wave, G.mult, G.chain, G.chainT = 0, 0, 0, 1, 0, 0
	G.toSpawn, G.spawnCd, G.waveGap = 0, 0, 1.0
	G.liveT = 0
	G.waveDone = false
	G.over = false
	G.mode = "play"
	G.api.send({ op = "start" })
	G.attract.Visible = false
	G.overP.Visible = false
	G.hud.Visible = true
end

local function startWave()
	G.wave += 1
	G.toSpawn = 3 + 2 * G.wave
	G.spawnCd = 0.4
	G.banner.Text = "WAVE " .. G.wave
	G.banner.TextTransparency = 0
	G.bannerT = os.clock()
	sfx("round_start", 0.35)
end

local function spawnEnemy()
	local wave = G.wave
	local kind = "grunt"
	local r = rng:NextNumber()
	if wave >= 4 and r < 0.14 + wave * 0.01 then kind = "heavy" elseif wave >= 2 and r < 0.42 then kind = "rusher" end
	local K = KINDS[kind]
	-- an edge spot away from you
	local x, y = 0, 0
	for _ = 1, 12 do
		local side = rng:NextInteger(1, 4)
		x = if side == 1 then 30 elseif side == 2 then W - 30 else rng:NextNumber(40, W - 40)
		y = if side == 3 then 30 elseif side == 4 then H - 30 else rng:NextNumber(40, H - 40)
		if (x - G.p.x) ^ 2 + (y - G.p.y) ^ 2 > 180 ^ 2 and not inCover(x, y, 16) then break end
	end
	ringFx(x, y, K.r + 6, K.color)
	table.insert(G.spawns, { at = os.clock() + 0.55, x = x, y = y, kind = kind })
end

local function addEnemy(s: any)
	local K = KINDS[s.kind]
	local f = frame(G.canvas, K.color, true, 3)
	local scale = 1 + (G.wave - 1) * 0.03
	local e = { kind = s.kind, K = K, x = s.x, y = s.y, vx = 0, vy = 0, r = K.r, hp = K.hp * (1 + (G.wave - 1) * 0.05), f = f,
		speed = K.speed * math.min(1.6, scale), shootCd = if K.shoot then rng:NextNumber(K.shoot.every[1], K.shoot.every[2]) else 0,
		strafe = if rng:NextNumber() < 0.5 then 1 else -1, flash = 0 }
	put(f, e.x, e.y, e.r * 2, e.r * 2)
	table.insert(G.enemies, e)
end

local function fire()
	local p = G.p
	local g = GUNS[p.gun]
	if p.reload > 0 or p.fireCd > 0 then return end
	if p.ammo[p.gun] <= 0 then
		p.reload = g.reload
		sfx("reload", 0.25)
		return
	end
	p.ammo[p.gun] -= 1
	p.fireCd = g.rate
	local a = math.atan2(G.aim.Y, G.aim.X)
	for _ = 1, g.pellets do
		local aa = a + rng:NextNumber(-g.spread, g.spread) * (if g.pellets > 1 then 1 else 0.5)
		local f = frame(G.canvas, Color3.fromRGB(244, 228, 186), false, 4)
		local b = { x = p.x + math.cos(a) * 12, y = p.y + math.sin(a) * 12, vx = math.cos(aa) * g.speed, vy = math.sin(aa) * g.speed,
			dmg = g.dmg, mine = true, life = g.life, pierce = g.pierce, hit = {}, f = f, len = if g.id == "sniper" then 22 else 9 }
		f.Rotation = math.deg(aa)
		table.insert(G.bullets, b)
	end
	sfx(g.sound, g.vol)
	G.kick = 2.5
	if p.ammo[p.gun] <= 0 then p.reload = g.reload; sfx("reload", 0.22) end
end

local function enemyShot(e: any)
	local S = e.K.shoot
	local a = math.atan2(G.p.y - e.y, G.p.x - e.x)
	for i = 1, S.n do
		local aa = a + (if S.n > 1 then (i - (S.n + 1) / 2) * S.spread / math.max(1, S.n - 1) * 2 else 0) + rng:NextNumber(-0.05, 0.05)
		local f = frame(G.canvas, Color3.fromRGB(226, 98, 90), true, 4)
		table.insert(G.bullets, { x = e.x + math.cos(aa) * (e.r + 3), y = e.y + math.sin(aa) * (e.r + 3), vx = math.cos(aa) * S.speed * (1 + G.wave * 0.02),
			vy = math.sin(aa) * S.speed * (1 + G.wave * 0.02), dmg = S.dmg, mine = false, life = 3, hit = {}, f = f, len = 6 })
	end
end

local function hurt(dmg: number)
	local p = G.p
	if p.inv > 0 or p.dashT > 0 or G.mode ~= "play" then return end
	p.hp -= dmg
	p.inv = 0.45
	G.shake = 6
	sfx("hurt", 0.35)
	G.hurtF.BackgroundTransparency = 0.6
	G.api.T.tween(G.hurtF, 0.35, { BackgroundTransparency = 1 })
	if p.hp <= 0 then
		p.hp = 0
		G.mode = "over"
		sfx("round_end", 0.45)
		burst(p.x, p.y, G.api.T.ACCENT, 14)
		G.api.send({ op = "over", score = G.score, wave = G.wave, kills = G.kills })
		G.overT = os.clock()
		G.overScore.Text = fmt(G.score)
		G.overSub.Text = ("WAVE %d  ·  %d KILLS"):format(G.wave, G.kills)
		G.overRank.Text = ""
		task.delay(0.9, function() if G.mode == "over" then G.overP.Visible = true; G.api.nav(G.api.padOn(), G.againB) end end)
	end
end

local function kill(e: any, i: number)
	table.remove(G.enemies, i)
	e.f:Destroy()
	G.kills += 1
	if os.clock() - G.chainT < CHAIN_T then G.chain += 1 else G.chain = 1 end
	G.chainT = os.clock()
	G.mult = math.min(3, 1 + 0.5 * (G.chain - 1))
	local pts = math.floor(e.K.pts * G.mult)
	G.score += pts
	popup("+" .. pts, e.x, e.y - e.r - 6, if G.mult > 1 then G.api.T.ACCENT else G.api.T.SOFT)
	burst(e.x, e.y, e.K.color, 7)
	ringFx(e.x, e.y, e.r + 4, e.K.color)
	sfx("kill", 0.3)
	if rng:NextNumber() < 0.1 then
		local f = frame(G.canvas, Color3.fromRGB(143, 209, 138), false, 2)
		local c = Instance.new("UICorner"); c.CornerRadius = UDim.new(0.25, 0); c.Parent = f
		put(f, e.x, e.y, 12, 12)
		table.insert(G.pickups, { x = e.x, y = e.y, f = f, t = 0 })
	end
end

-- ------------------------------------------------------------------ one step (1/60 s)
local function step(dt: number)
	local p = G.p
	-- input: where to go, where to aim
	local mv = Vector2.zero
	if G.touchMove then mv = G.touchMove
	elseif G.api.padOn() then
		local s = G.api.Pad.stick(1)
		if s.Magnitude > 0.2 then mv = Vector2.new(s.X, -s.Y) end
	else
		local x = (if UIS:IsKeyDown(Enum.KeyCode.D) or UIS:IsKeyDown(Enum.KeyCode.Right) then 1 else 0) - (if UIS:IsKeyDown(Enum.KeyCode.A) or UIS:IsKeyDown(Enum.KeyCode.Left) then 1 else 0)
		local y = (if UIS:IsKeyDown(Enum.KeyCode.S) or UIS:IsKeyDown(Enum.KeyCode.Down) then 1 else 0) - (if UIS:IsKeyDown(Enum.KeyCode.W) or UIS:IsKeyDown(Enum.KeyCode.Up) then 1 else 0)
		mv = Vector2.new(x, y)
	end
	if G.testAuto then
		local near, nd = nil, math.huge
		for _, e in G.enemies do
			local d = (e.x - p.x) ^ 2 + (e.y - p.y) ^ 2
			if d < nd then near, nd = e, d end
		end
		if near then
			local d = Vector2.new(near.x - p.x, near.y - p.y)
			G.testAim = d.Unit
			mv = if d.Magnitude < 130 then -d.Unit else Vector2.new(-d.Unit.Y, d.Unit.X) * 0.6
		end
	end
	if mv.Magnitude > 1 then mv = mv.Unit end
	local firing = false
	if G.touchAim then
		G.aim = G.touchAim.Unit
		firing = true
	elseif G.api.padOn() then
		local s = G.api.Pad.stick(2)
		if s.Magnitude > 0.3 then
			local want = Vector2.new(s.X, -s.Y).Unit
			-- a little help on a pad: an enemy within 14 degrees of the stick gets the aim
			local best, bestD = nil, math.cos(math.rad(14))
			for _, e in G.enemies do
				local d = Vector2.new(e.x - p.x, e.y - p.y)
				if d.Magnitude > 1 then
					local dot = d.Unit:Dot(want)
					if dot > bestD then best, bestD = d.Unit, dot end
				end
			end
			G.aim = best or want
		elseif mv.Magnitude > 0.2 then
			G.aim = mv.Unit
		end
		firing = G.api.Pad.trigger("ButtonR2") > 0.3
	else
		local c = G.canvas
		local m = UIS:GetMouseLocation()
		local lx = (m.X - c.AbsolutePosition.X) / math.max(1, c.AbsoluteSize.X) * W
		local ly = (m.Y - c.AbsolutePosition.Y) / math.max(1, c.AbsoluteSize.Y) * H
		local d = Vector2.new(lx - p.x, ly - p.y)
		if d.Magnitude > 2 then G.aim = d.Unit end
		G.mouse = Vector2.new(lx, ly)
		firing = UIS:IsMouseButtonPressed(Enum.UserInputType.MouseButton1)
	end
	-- you
	p.fireCd = math.max(0, p.fireCd - dt)
	p.dashCd = math.max(0, p.dashCd - dt)
	p.inv = math.max(0, p.inv - dt)
	if p.reload > 0 then
		p.reload -= dt
		if p.reload <= 0 then p.reload = 0; p.ammo[p.gun] = GUNS[p.gun].mag end
	end
	if p.dashT > 0 then
		p.dashT -= dt
		p.x += p.dvx * dt; p.y += p.dvy * dt
		G.ghostT = (G.ghostT or 0) - dt
		if G.ghostT <= 0 then
			G.ghostT = 0.03
			local f = frame(G.canvas, G.api.T.ACCENT, true, 2)
			f.BackgroundTransparency = 0.55
			put(f, p.x, p.y, p.r * 2, p.r * 2)
			table.insert(G.fx, { f = f, t = 0, life = 0.18, x = p.x, y = p.y, kind = "ghost" })
		end
	else
		local k = 1 - math.exp(-dt * 14)
		p.vx += (mv.X * P_SPEED - p.vx) * k
		p.vy += (mv.Y * P_SPEED - p.vy) * k
		p.x += p.vx * dt; p.y += p.vy * dt
	end
	collide(p)
	if G.testAuto then
		if G.testAim then G.aim = G.testAim end
		firing = #G.enemies > 0
	end
	if firing and G.mode == "play" then fire() end
	-- waves
	if G.mode == "play" and #G.enemies == 0 and #G.spawns == 0 and G.toSpawn == 0 then
		if G.wave > 0 and not G.waveDone then
			G.waveDone = true
			local bonus = MG.ARCADE.WAVE_BONUS * G.wave
			G.score += bonus
			popup("WAVE BONUS +" .. bonus, W / 2, 60, G.api.T.ACCENT)
			p.hp = math.min(100, p.hp + 25)
			G.waveGap = 1.6
		end
		G.waveGap -= dt
		if G.waveGap <= 0 then G.waveDone = false; startWave() end
	end
	if G.toSpawn > 0 then
		G.spawnCd -= dt
		if G.spawnCd <= 0 and #G.enemies + #G.spawns < 9 + G.wave then
			G.spawnCd = math.max(0.25, 0.75 - G.wave * 0.04)
			G.toSpawn -= 1
			spawnEnemy()
		end
	end
	for i = #G.spawns, 1, -1 do
		if os.clock() >= G.spawns[i].at then addEnemy(G.spawns[i]); table.remove(G.spawns, i) end
	end
	-- the bots
	for i, e in G.enemies do
		local dx, dy = p.x - e.x, p.y - e.y
		local d = math.max(1, math.sqrt(dx * dx + dy * dy))
		local ux, uy = dx / d, dy / d
		local wx, wy = 0, 0
		local K = e.K
		if K.keep then
			if d > K.keep[2] then wx, wy = ux, uy
			elseif d < K.keep[1] then wx, wy = -ux, -uy
			else wx, wy = -uy * e.strafe * 0.8, ux * e.strafe * 0.8 end
			if rng:NextNumber() < dt * 0.4 then e.strafe = -e.strafe end
		else
			wx, wy = ux, uy
		end
		-- (keep apart)
		for j, o in G.enemies do
			if j ~= i then
				local ox, oy = e.x - o.x, e.y - o.y
				local od = ox * ox + oy * oy
				local min = e.r + o.r + 4
				if od < min * min and od > 0.01 then
					local q = math.sqrt(od)
					wx += ox / q * 0.8; wy += oy / q * 0.8
				end
			end
		end
		local wl = math.sqrt(wx * wx + wy * wy)
		if wl > 1 then wx, wy = wx / wl, wy / wl end
		local k = 1 - math.exp(-dt * 6)
		e.vx += (wx * e.speed - e.vx) * k
		e.vy += (wy * e.speed - e.vy) * k
		e.x += e.vx * dt; e.y += e.vy * dt
		collide(e)
		if K.shoot and G.mode == "play" then
			e.shootCd -= dt * (1 + G.wave * 0.04)
			if e.shootCd <= 0 then
				e.shootCd = rng:NextNumber(K.shoot.every[1], K.shoot.every[2])
				enemyShot(e)
			end
		end
		if K.touch and d < e.r + p.r + 1 then
			hurt(K.touch)
			e.vx -= ux * 260; e.vy -= uy * 260
			p.vx += ux * 220; p.vy += uy * 220
		end
		e.flash = math.max(0, e.flash - dt)
	end
	-- bullets
	for i = #G.bullets, 1, -1 do
		local b = G.bullets[i]
		b.life -= dt
		b.x += b.vx * dt; b.y += b.vy * dt
		local dead = b.life <= 0 or b.x < 8 or b.x > W - 8 or b.y < 8 or b.y > H - 8 or inCover(b.x, b.y, 0) ~= nil
		if not dead then
			if b.mine then
				for j = #G.enemies, 1, -1 do
					local e = G.enemies[j]
					if not b.hit[e] and (e.x - b.x) ^ 2 + (e.y - b.y) ^ 2 < (e.r + 3) ^ 2 then
						b.hit[e] = true
						e.hp -= b.dmg
						e.flash = 0.06
						e.vx += b.vx * 0.05; e.vy += b.vy * 0.05
						if e.hp <= 0 then kill(e, j) else
							if os.clock() - (G.hitSnd or 0) > 0.05 then G.hitSnd = os.clock(); sfx("hit", 0.18) end
						end
						if not b.pierce then dead = true; break end
					end
				end
			elseif (p.x - b.x) ^ 2 + (p.y - b.y) ^ 2 < (p.r + 2) ^ 2 then
				hurt(b.dmg)
				dead = true
			end
		end
		if dead then
			if inCover(b.x, b.y, 0) then burst(b.x, b.y, Color3.fromRGB(120, 126, 136), 2) end
			b.f:Destroy()
			table.remove(G.bullets, i)
		end
	end
	-- pickups
	for i = #G.pickups, 1, -1 do
		local k = G.pickups[i]
		k.t += dt
		if (k.x - p.x) ^ 2 + (k.y - p.y) ^ 2 < (p.r + 8) ^ 2 then
			p.hp = math.min(100, p.hp + 30)
			popup("+30", k.x, k.y - 12, Color3.fromRGB(143, 209, 138))
			sfx("heal", 0.35)
			k.f:Destroy(); table.remove(G.pickups, i)
		elseif k.t > 12 then
			k.f:Destroy(); table.remove(G.pickups, i)
		end
	end
	if os.clock() - G.chainT > CHAIN_T then G.mult = 1 end
	-- the cabinet's screen, now and then
	G.liveT += dt
	if G.liveT >= MG.ARCADE.LIVE_EVERY and G.mode == "play" then
		G.liveT = 0
		G.api.send({ op = "live", score = G.score, wave = G.wave })
	end
end

-- ------------------------------------------------------------------ drawing
local function draw(dt: number)
	local T = G.api.T
	local p = G.p
	-- the shake
	G.shake = math.max(0, (G.shake or 0) - dt * 30)
	G.kick = math.max(0, (G.kick or 0) - dt * 30)
	local sx = (rng:NextNumber() - 0.5) * (G.shake + G.kick * 0.3)
	local sy = (rng:NextNumber() - 0.5) * (G.shake + G.kick * 0.3)
	G.canvas.Position = UDim2.new(0.5, sx, 0.5, sy)
	-- you
	local alive = G.mode == "play" or G.mode == "attract"
	G.pf.Visible = alive
	G.gunF.Visible = alive
	put(G.pf, p.x, p.y, p.r * 2, p.r * 2)
	G.pf.BackgroundTransparency = if p.inv > 0 and math.floor(os.clock() * 20) % 2 == 0 then 0.6 else 0
	local a = math.atan2(G.aim.Y, G.aim.X)
	local back = (G.kick or 0)
	put(G.gunF, p.x + math.cos(a) * (13 - back), p.y + math.sin(a) * (13 - back), 14, 5)
	G.gunF.Rotation = math.deg(a)
	-- the aim line (the sniper)
	G.aimF.Visible = alive and p.gun == 3 and p.reload <= 0 and G.mode == "play"
	if G.aimF.Visible then
		local L = 150
		put(G.aimF, p.x + math.cos(a) * (L / 2 + 16), p.y + math.sin(a) * (L / 2 + 16), L, 1.5)
		G.aimF.Rotation = math.deg(a)
	end
	-- the crosshair (mouse)
	G.cross.Visible = G.mode == "play" and not G.api.padOn() and not G.touchOn
	if G.cross.Visible and G.mouse then put(G.cross, G.mouse.X, G.mouse.Y, 12, 12) end
	for _, e in G.enemies do
		put(e.f, e.x, e.y, e.r * 2, e.r * 2)
		e.f.BackgroundColor3 = if e.flash > 0 then T.TEXT else e.K.color
	end
	for _, b in G.bullets do
		if b.mine then put(b.f, b.x, b.y, b.len, 3) else put(b.f, b.x, b.y, b.len, b.len) end
	end
	for _, k in G.pickups do
		local s = 12 + math.sin(k.t * 6) * 1.5
		put(k.f, k.x, k.y, s, s)
		k.f.BackgroundTransparency = if k.t > 9 and math.floor(k.t * 8) % 2 == 0 then 0.6 else 0
	end
	for i = #G.fx, 1, -1 do
		local f = G.fx[i]
		f.t += dt
		local u = f.t / f.life
		if u >= 1 then f.f:Destroy(); table.remove(G.fx, i); continue end
		if f.kind == "pop" then
			f.y += f.vy * dt
			put(f.f, f.x, f.y, 140, 16)
			f.f.TextTransparency = u * u
		elseif f.kind == "ring" then
			local r = f.r * (1 + u * 0.9)
			put(f.f, f.x, f.y, r * 2, r * 2)
			f.s.Transparency = u
		elseif f.kind == "spark" then
			f.x += f.vx * dt; f.y += f.vy * dt
			f.vx *= 0.9; f.vy *= 0.9
			put(f.f, f.x, f.y, 4, 4)
			f.f.BackgroundTransparency = u
		elseif f.kind == "ghost" then
			f.f.BackgroundTransparency = 0.55 + 0.45 * u
		end
	end
	-- the HUD
	G.scoreL.Text = fmt(G.score)
	G.multL.Text = if G.mult > 1 then ("x%.1f"):format(G.mult) else ""
	G.waveL.Text = if G.wave > 0 then "WAVE " .. G.wave else ""
	G.bestL.Text = "BEST " .. fmt(math.max(G.best or 0, G.score))
	G.hpFill.Size = UDim2.fromScale(math.clamp(p.hp / 100, 0, 1), 1)
	G.hpFill.BackgroundColor3 = if p.hp < 30 then T.DANGER else T.TEXT
	G.dashFill.Size = UDim2.fromScale(1 - p.dashCd / DASH_CD, 1)
	for i, chip in G.chips do
		local g = GUNS[i]
		local on = i == p.gun
		chip.BackgroundColor3 = if on then T.CARD_HI else T.CARD
		chip.BackgroundTransparency = if on then 0.05 else 0.35
		local nm = chip:FindFirstChild("Name") :: TextLabel
		nm.TextColor3 = if on then T.ACCENT else T.MUTED
		local am = chip:FindFirstChild("Ammo") :: TextLabel
		am.Text = if on and p.reload > 0 then "RELOAD" else ("%d/%d"):format(p.ammo[i], g.mag)
		local rl = chip:FindFirstChild("Reload") :: Frame
		rl.Visible = on and p.reload > 0
		if rl.Visible then rl.Size = UDim2.new(1 - p.reload / g.reload, 0, 0, 2) end
	end
	if G.bannerT then
		local u = (os.clock() - G.bannerT - 1.2) / 0.5
		G.banner.TextTransparency = math.clamp(u, 0, 1)
	end
end

-- ------------------------------------------------------------------ your screen
local function swap(dir: number?, to: number?)
	local p = G.p
	local n = to or ((p.gun - 1 + (dir or 1)) % #GUNS + 1)
	if n == p.gun or G.mode ~= "play" then return end
	p.gun = n
	p.reload = if p.ammo[n] <= 0 then GUNS[n].reload else 0
	p.fireCd = math.max(p.fireCd, 0.15)
	sfx("click", 0.3)
end
local function dash()
	local p = G.p
	if G.mode ~= "play" or p.dashCd > 0 then return end
	local mv = Vector2.new(p.vx, p.vy)
	local dir = if mv.Magnitude > 20 then mv.Unit else G.aim
	p.dvx, p.dvy = dir.X * DASH_V, dir.Y * DASH_V
	p.dashT = DASH_T
	p.dashCd = DASH_CD
	sfx("scythe_dash", 0.3)
end
local function reload()
	local p = G.p
	local g = GUNS[p.gun]
	if G.mode ~= "play" or p.reload > 0 or p.ammo[p.gun] >= g.mag then return end
	p.reload = g.reload
	sfx("reload", 0.25)
end

function M.open(api: any, model: Model, side: string)
	local T = api.T
	G = { api = api, model = model, conns = {}, mode = "attract", aim = Vector2.new(1, 0), p = { r = 9 }, chips = {} }
	G.p.x, G.p.y, G.p.vx, G.p.vy, G.p.hp, G.p.gun, G.p.inv, G.p.dashCd, G.p.reload = W / 2, H / 2 + 60, 0, 0, 100, 1, 0, 0, 0
	G.p.ammo = { GUNS[1].mag, GUNS[2].mag, GUNS[3].mag }
	G.score, G.kills, G.wave, G.mult, G.chainT = 0, 0, 0, 1, 0
	clearWorld()
	G.touchOn = api.isTouch()
	local root = api.root
	-- the cabinet round the screen
	local back = T.new("Frame", { Name = "Cab", BackgroundColor3 = Color3.fromRGB(26, 29, 35), BackgroundTransparency = 1, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 0 }, root)
	T.tween(back, 0.45, { BackgroundTransparency = 0 })
	G.back = back
	local bezel = T.new("Frame", { Name = "Bezel", BackgroundColor3 = Color3.fromRGB(44, 48, 56), BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.49), Size = UDim2.fromScale(0.9, 0.84), ZIndex = 0 }, back)
	T.new("UIAspectRatioConstraint", { AspectRatio = (W + 24) / (H + 24) }, bezel)
	T.corner(bezel, 18)
	local holder = T.new("Frame", { Name = "Holder", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.new(1, -24, 1, -24) }, bezel)
	local canvas = T.new("Frame", { Name = "Canvas", BackgroundColor3 = INK, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromScale(1, 1), ClipsDescendants = true, ZIndex = 1 }, holder)
	T.corner(canvas, 10)
	G.canvas = canvas
	-- the yard: a faint grid, the walls, the cover
	for x = 40, W - 40, 40 do local f = frame(canvas, Color3.fromRGB(31, 35, 43), false, 1); put(f, x, H / 2, 1, H - 20) end
	for y = 40, H - 40, 40 do local f = frame(canvas, Color3.fromRGB(31, 35, 43), false, 1); put(f, W / 2, y, W - 20, 1) end
	local wall = frame(canvas, INK, false, 1)
	wall.BackgroundTransparency = 1
	put(wall, W / 2, H / 2, W - 20, H - 20)
	local ws = Instance.new("UIStroke"); ws.Color = Color3.fromRGB(64, 70, 82); ws.Thickness = 2; ws.Parent = wall
	for _, c in COVER do
		local f = frame(canvas, Color3.fromRGB(47, 53, 63), false, 2)
		local cc = Instance.new("UICorner"); cc.CornerRadius = UDim.new(0, 4); cc.Parent = f
		local s = Instance.new("UIStroke"); s.Color = Color3.fromRGB(70, 77, 90); s.Thickness = 1; s.Parent = f
		put(f, c[1] + c[3] / 2, c[2] + c[4] / 2, c[3], c[4])
	end
	-- you
	G.pf = frame(canvas, T.ACCENT, true, 5)
	G.gunF = frame(canvas, Color3.fromRGB(58, 63, 72), false, 6)
	G.aimF = frame(canvas, T.ACCENT, false, 3)
	G.aimF.BackgroundTransparency = 0.6
	G.cross = frame(canvas, INK, true, 7)
	G.cross.BackgroundTransparency = 1
	local cs = Instance.new("UIStroke"); cs.Color = T.TEXT; cs.Thickness = 1.5; cs.Parent = G.cross
	G.hurtF = T.new("Frame", { Name = "Hurt", BackgroundColor3 = T.DANGER, BackgroundTransparency = 1, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 8 }, canvas)
	-- the HUD
	local hud = T.new("Frame", { Name = "Hud", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = 9, Visible = false }, canvas)
	G.hud = hud
	G.scoreL = T.text(hud, "Score", "0", 22, T.TEXT, T.FONT_TITLE)
	G.scoreL.Position = UDim2.new(0, 16, 0, 10); G.scoreL.Size = UDim2.fromOffset(200, 26); G.scoreL.ZIndex = 9
	G.multL = T.text(hud, "Mult", "", 15, T.ACCENT, T.FONT_BOLD)
	G.multL.Position = UDim2.new(0, 16, 0, 36); G.multL.Size = UDim2.fromOffset(100, 18); G.multL.ZIndex = 9
	G.waveL = T.text(hud, "Wave", "", 15, T.SOFT, T.FONT_TITLE, Enum.TextXAlignment.Center)
	G.waveL.AnchorPoint = Vector2.new(0.5, 0); G.waveL.Position = UDim2.new(0.5, 0, 0, 14); G.waveL.Size = UDim2.fromOffset(200, 20); G.waveL.ZIndex = 9
	G.bestL = T.text(hud, "Best", "", 13, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Right)
	G.bestL.AnchorPoint = Vector2.new(1, 0); G.bestL.Position = UDim2.new(1, -16, 0, 14); G.bestL.Size = UDim2.fromOffset(200, 18); G.bestL.ZIndex = 9
	local hp = T.new("Frame", { Name = "Hp", BackgroundColor3 = T.TRACK, BorderSizePixel = 0, AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(0, 16, 1, -26), Size = UDim2.fromOffset(170, 10), ZIndex = 9 }, hud)
	T.corner(hp, 5)
	G.hpFill = T.new("Frame", { Name = "Fill", BackgroundColor3 = T.TEXT, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 9 }, hp)
	T.corner(G.hpFill, 5)
	local dashB = T.new("Frame", { Name = "Dash", BackgroundColor3 = T.TRACK, BorderSizePixel = 0, AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(0, 16, 1, -14), Size = UDim2.fromOffset(70, 5), ZIndex = 9 }, hud)
	T.corner(dashB, 3)
	G.dashFill = T.new("Frame", { Name = "Fill", BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 9 }, dashB)
	T.corner(G.dashFill, 3)
	for i, g in GUNS do
		local chip = T.new("Frame", { Name = "Gun" .. i, BackgroundColor3 = T.CARD, BorderSizePixel = 0, AnchorPoint = Vector2.new(1, 1),
			Position = UDim2.new(1, -16 - (3 - i) * 116, 1, -12), Size = UDim2.fromOffset(110, 40), ZIndex = 9 }, hud)
		T.corner(chip)
		local kc = T.key(chip, tostring(i), UDim2.fromOffset(6, 9))
		kc.ZIndex = 10
		local nm = T.text(chip, "Name", g.name, 12, T.MUTED, T.FONT_BOLD)
		nm.Position = UDim2.fromOffset(34, 4); nm.Size = UDim2.fromOffset(74, 16); nm.ZIndex = 10
		local am = T.text(chip, "Ammo", "", 12, T.SOFT, T.FONT)
		am.Position = UDim2.fromOffset(34, 20); am.Size = UDim2.fromOffset(74, 16); am.ZIndex = 10
		local rl = T.new("Frame", { Name = "Reload", BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Position = UDim2.new(0, 0, 1, -2), Size = UDim2.new(0, 0, 0, 2), ZIndex = 10, Visible = false }, chip)
		G.chips[i] = chip
	end
	G.banner = T.text(canvas, "Banner", "", 30, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Center, true)
	G.banner.AnchorPoint = Vector2.new(0.5, 0.5); G.banner.Position = UDim2.fromScale(0.5, 0.3); G.banner.Size = UDim2.fromOffset(400, 40); G.banner.ZIndex = 9
	G.banner.TextTransparency = 1
	-- the attract screen: the name, the board, how to start
	local at = T.new("Frame", { Name = "Attract", BackgroundColor3 = INK, BackgroundTransparency = 0.08, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 10 }, canvas)
	G.attract = at
	local t1 = T.text(at, "Title", "JANKFIRE", 46, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Center)
	t1.Position = UDim2.fromScale(0, 0.08); t1.Size = UDim2.fromScale(1, 0.14); t1.ZIndex = 11
	local t2 = T.text(at, "Sub", "HIGH SCORES", 14, T.ACCENT, T.FONT_TITLE, Enum.TextXAlignment.Center)
	t2.Position = UDim2.fromScale(0, 0.25); t2.Size = UDim2.fromScale(1, 0.06); t2.ZIndex = 11
	G.boardRows = {}
	for i = 1, 5 do
		local r = T.text(at, "Row" .. i, "", 15, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Center)
		r.Position = UDim2.fromScale(0, 0.33 + (i - 1) * 0.065); r.Size = UDim2.fromScale(1, 0.06); r.ZIndex = 11
		G.boardRows[i] = r
	end
	G.startB = api.button(at, "Start", "START", UDim2.fromScale(0.5, 0.72), UDim2.fromOffset(170, 42), true)
	G.startB.AnchorPoint = Vector2.new(0.5, 0); G.startB.ZIndex = 11
	G.startB.Activated:Connect(function() if G.mode == "attract" then newRun() end end)
	G.howL = T.text(at, "How", "", 12, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center)
	G.howL.Position = UDim2.fromScale(0, 0.87); G.howL.Size = UDim2.fromScale(1, 0.06); G.howL.ZIndex = 11
	-- the end of a run
	local ov = T.new("Frame", { Name = "Over", BackgroundColor3 = INK, BackgroundTransparency = 0.15, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 12, Visible = false }, canvas)
	G.overP = ov
	local o1 = T.text(ov, "Title", "GAME OVER", 30, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Center)
	o1.Position = UDim2.fromScale(0, 0.18); o1.Size = UDim2.fromScale(1, 0.1); o1.ZIndex = 13
	G.overScore = T.text(ov, "Score", "", 40, T.ACCENT, T.FONT_SHOUT, Enum.TextXAlignment.Center)
	G.overScore.Position = UDim2.fromScale(0, 0.32); G.overScore.Size = UDim2.fromScale(1, 0.13); G.overScore.ZIndex = 13
	G.overSub = T.text(ov, "Sub", "", 15, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Center)
	G.overSub.Position = UDim2.fromScale(0, 0.47); G.overSub.Size = UDim2.fromScale(1, 0.06); G.overSub.ZIndex = 13
	G.overRank = T.text(ov, "Rank", "", 15, T.ACCENT, T.FONT_TITLE, Enum.TextXAlignment.Center)
	G.overRank.Position = UDim2.fromScale(0, 0.55); G.overRank.Size = UDim2.fromScale(1, 0.06); G.overRank.ZIndex = 13
	G.againB = api.button(ov, "Again", "PLAY AGAIN", UDim2.fromScale(0.5, 0.7), UDim2.fromOffset(190, 42), true)
	G.againB.AnchorPoint = Vector2.new(0.5, 0); G.againB.ZIndex = 13
	G.againB.Activated:Connect(function() if G.mode == "over" then newRun() end end)
	-- the hint under the screen
	G.keysL = T.text(back, "Keys", "", 13, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center)
	G.keysL.AnchorPoint = Vector2.new(0.5, 1); G.keysL.Position = UDim2.new(0.5, 0, 1, -14); G.keysL.Size = UDim2.fromOffset(900, 18)
	-- a phone's sticks and buttons
	if G.touchOn then
		local function stick(name: string, x: number): (Frame, Frame)
			local base = T.new("Frame", { Name = name, BackgroundColor3 = T.BG, BackgroundTransparency = 0.5, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
				Position = UDim2.new(x, 0, 1, -110), Size = UDim2.fromOffset(120, 120), Visible = false, ZIndex = 20 }, back)
			T.corner(base, 60)
			T.edge(base)
			local knob = T.new("Frame", { Name = "Knob", BackgroundColor3 = T.TEXT, BackgroundTransparency = 0.3, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
				Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(50, 50), ZIndex = 21 }, base)
			T.corner(knob, 25)
			return base, knob
		end
		G.lBase, G.lKnob = stick("MoveStick", 0.16)
		G.rBase, G.rKnob = stick("AimStick", 0.84)
		local dashT = api.button(back, "DashT", "DASH", UDim2.new(1, -40, 1, -250), UDim2.fromOffset(92, 92), false)
		dashT.AnchorPoint = Vector2.new(1, 1); dashT.ZIndex = 22
		T.corner(dashT, 46)
		dashT.MouseButton1Down:Connect(dash)
		local gunT = api.button(back, "GunT", "GUN", UDim2.new(1, -150, 1, -210), UDim2.fromOffset(70, 70), false)
		gunT.AnchorPoint = Vector2.new(1, 1); gunT.ZIndex = 22
		T.corner(gunT, 35)
		gunT.MouseButton1Down:Connect(function() swap(1) end)
		local touches: { [InputObject]: { side: string, at: Vector2 } } = {}
		local function set(side: string, v: Vector2?)
			local base, knob = if side == "l" then G.lBase else G.rBase, if side == "l" then G.lKnob else G.rKnob
			if v then knob.Position = UDim2.new(0.5, v.X * 40, 0.5, v.Y * 40) else knob.Position = UDim2.fromScale(0.5, 0.5) end
			if side == "l" then G.touchMove = v else G.touchAim = if v and v.Magnitude > 0.2 then v else nil end
			base.Visible = v ~= nil
		end
		table.insert(G.conns, UIS.TouchStarted:Connect(function(io: InputObject, gp: boolean)
			if gp then return end
			if G.mode ~= "play" then if G.mode == "attract" then newRun() end; return end
			local vs = workspace.CurrentCamera.ViewportSize
			local side = if io.Position.X < vs.X * 0.45 then "l" else "r"
			touches[io] = { side = side, at = Vector2.new(io.Position.X, io.Position.Y) }
			local base = if side == "l" then G.lBase else G.rBase
			-- (the stick appears where the thumb lands)
			local sc = (root.Parent and root.Parent:FindFirstChildOfClass("UIScale")) :: UIScale?
			local s = if sc then sc.Scale else 1
			local inset = game:GetService("GuiService"):GetGuiInset()
			base.Position = UDim2.fromOffset(io.Position.X / s, (io.Position.Y + inset.Y) / s)
			set(side, Vector2.zero)
		end))
		table.insert(G.conns, UIS.TouchMoved:Connect(function(io: InputObject)
			local t = touches[io]
			if not t then return end
			local d = Vector2.new(io.Position.X, io.Position.Y) - t.at
			local v = if d.Magnitude > 1 then d.Unit * math.min(1, d.Magnitude / 60) else Vector2.zero
			set(t.side, v)
		end))
		table.insert(G.conns, UIS.TouchEnded:Connect(function(io: InputObject)
			local t = touches[io]
			if not t then return end
			touches[io] = nil
			set(t.side, nil)
		end))
	end
	-- keys
	table.insert(G.conns, UIS.InputBegan:Connect(function(io: InputObject, gp: boolean)
		if gp then return end
		local k = io.KeyCode
		if k == Enum.KeyCode.One then swap(nil, 1) elseif k == Enum.KeyCode.Two then swap(nil, 2) elseif k == Enum.KeyCode.Three then swap(nil, 3)
		elseif k == Enum.KeyCode.Q or k == Enum.KeyCode.ButtonL1 then swap(-1)
		elseif k == Enum.KeyCode.E or k == Enum.KeyCode.ButtonR1 or k == Enum.KeyCode.ButtonY then swap(1)
		elseif k == Enum.KeyCode.R or k == Enum.KeyCode.ButtonX then reload()
		elseif k == Enum.KeyCode.LeftShift or k == Enum.KeyCode.RightShift then dash()
		elseif io.UserInputType == Enum.UserInputType.MouseButton1 and G.mode == "attract" then newRun() end
	end))
	table.insert(G.conns, UIS.InputChanged:Connect(function(io: InputObject, gp: boolean)
		if io.UserInputType == Enum.UserInputType.MouseWheel and G.mode == "play" then swap(if io.Position.Z > 0 then -1 else 1) end
	end))
	-- the attract screen's board and the keys line
	local function drawBoard()
		local b = boardOf(model)
		G.best = if b[1] then b[1].s else 0
		for i = 1, 5 do
			local e = b[i]
			G.boardRows[i].Text = if e then ("%d.  %s   %s   W%d"):format(i, string.upper(tostring(e.n)):sub(1, 16), fmt(e.s), e.w) elseif i == 1 then "NO SCORES YET" else ""
		end
	end
	drawBoard()
	if model.Parent then table.insert(G.conns, model.Parent:GetAttributeChangedSignal("ArcadeBoard"):Connect(drawBoard)) end
	-- the camera goes into the screen
	api.camera = function(): CFrame?
		local s = model:FindFirstChild("Screen") :: BasePart?
		if not s then return nil end
		return CFrame.lookAt(s.Position + s.CFrame.LookVector * 1.55, s.Position, s.CFrame.UpVector)
	end
	api.fov = 70
	pcall(function() UIS.MouseIcon = "rbxasset://SystemCursors/Cross" end)
	local acc = 0
	G.step = RunService.RenderStepped:Connect(function(dt: number)
		dt = math.min(dt, 0.1)
		G.keysL.Text = if G.touchOn then "" elseif api.padOn() then "LEFT STICK MOVE · RIGHT STICK AIM · RT FIRE · RB GUN · X RELOAD · " .. api.Pad.short("ButtonA") .. " DASH"
			else "WASD MOVE · MOUSE AIM · CLICK FIRE · 1 2 3 GUNS · R RELOAD · SPACE DASH"
		G.howL.Text = if G.touchOn then "TAP TO START" elseif api.padOn() then "PRESS " .. api.Pad.short("ButtonA") .. " TO START" else "PRESS SPACE TO START"
		if G.mode == "play" or G.mode == "over" then
			acc += dt
			while acc >= 1 / 60 do
				acc -= 1 / 60
				step(1 / 60)
			end
		end
		draw(dt)
	end)
	api.nav(false)
end

-- leaving mid-run: the run ends here and counts (sent before the core's leave, so the server still has the run)
function M.beforeLeave()
	if G.mode == "play" and G.api then
		G.mode = "over"
		G.api.send({ op = "over", score = G.score, wave = G.wave, kills = G.kills })
	end
end

function M.close()
	pcall(function() UIS.MouseIcon = "" end)
	if G.step then G.step:Disconnect() end
	for _, c in G.conns or {} do c:Disconnect() end
	if G.api then G.api.camera = nil; G.api.fov = nil; G.api.nav(false) end
	G = {}
end

function M.remote(d: any)
	if d.op == "rank" and G.overRank then
		G.overRank.Text = if d.rank == 1 then "BEST IN THE SERVER" elseif d.rank then ("#%d IN THE SERVER"):format(d.rank) else ""
	end
end

function M.space(down: boolean, _io: any): boolean
	if not G.mode then return false end
	if not down then return true end
	if G.mode == "attract" then newRun()
	elseif G.mode == "over" then if G.overP.Visible then newRun() end
	else dash() end
	return true
end

function M.back(): boolean return false end

function M.confirmLeave(): string?
	if G.mode == "play" then return "PRESS AGAIN TO LEAVE: THE RUN ENDS" end
	return nil
end

function M.test(v: string): string
	if v == "arcade:start" then if G.mode ~= "play" then newRun() end; return "started" end
	if v == "arcade:die" then if G.p then G.p.inv = 0; G.p.dashT = 0; hurt(999) end; return "dead" end
	if v == "arcade:auto" then G.testAuto = not G.testAuto; return "auto " .. tostring(G.testAuto) end
	return HttpService:JSONEncode({ mode = G.mode, score = G.score, wave = G.wave, kills = G.kills, hp = G.p and G.p.hp, enemies = G.enemies and #G.enemies })
end

return M
