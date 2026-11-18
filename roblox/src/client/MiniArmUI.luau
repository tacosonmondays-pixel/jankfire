--!strict
-- ARM WRESTLING, your side (shared/MiniGames.luau; server/MiniArm). MiniGames.client calls this.
--   world: every client moves each arm table's clasp from the table's Bal (smoothed), so everyone sees the two hands
--          lean one way and the other; the sitters' arms follow through their IKControls. the slam: the clasp drops
--          onto the loser's pin pad, a recorded thud there, a ring of dust-grey off the pad, the sitters' cameras shake
--   your screen: the meter across the top (you on the left: winning moves the arms to your left, as you see them),
--          the check at the bottom (the needle, the zone; Space / pad A / a tap anywhere on the lower half), the
--          countdown and the result; alone: three bot buttons; after a bout: AGAIN
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local MG = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("MiniGames")) :: any

local M = {}
local me = Players.LocalPlayer
local L = MG.L.arm

local function now(): number return workspace:GetServerTimeNow() end

-- ------------------------------------------------------------------ the world
local function ring(at: CFrame)
	local p = Instance.new("Part")
	p.Name = "MiniSlamRing"; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
	p.Shape = Enum.PartType.Cylinder; p.Material = Enum.Material.SmoothPlastic; p.Color = Color3.fromRGB(214, 210, 202)
	p.Size = Vector3.new(0.05, 0.6, 0.6); p.Transparency = 0.25
	p.CFrame = at * CFrame.Angles(0, 0, math.pi / 2)
	p.Parent = workspace
	TweenService:Create(p, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(0.05, 2.4, 2.4), Transparency = 1 }):Play()
	task.delay(0.4, function() p:Destroy() end)
end

function M.world(model: Model, api: any): ((number) -> ())?
	local root = model:WaitForChild("Root", 10) :: BasePart?
	if not root then return nil end
	local clasp = root:WaitForChild("Clasp", 5) :: Attachment
	local hA = root:WaitForChild("HandA", 5) :: Attachment
	local hB = root:WaitForChild("HandB", 5) :: Attachment
	if not clasp or not hA or not hB then return nil end
	local shown, vel = 0, 0
	local slamFrom: number? = nil
	local slammed = false
	local SLAM_T = 0.13
	return function(dt: number)
		local st = model:GetAttribute("State")
		local bal = (model:GetAttribute("Bal") or 0) :: number
		local ang: number
		if st == "slam" then
			local w = model:GetAttribute("Winner")
			local dir = if w == "A" then 1 else -1
			local t = now() - ((model:GetAttribute("At") or now()) :: number)
			slamFrom = slamFrom or shown * L.swing
			local u = math.clamp(t / SLAM_T, 0, 1)
			ang = (slamFrom :: number) + (88 * dir - (slamFrom :: number)) * u * u
			if u >= 1 and not slammed then
				slammed = true
				local loser = if w == "A" then "B" else "A"
				local pinAt = root.CFrame * CFrame.new(L.pin[loser])
				-- (recordings already in the game: a big wooden gavel hit and a body-against-wall thud, together)
				if not api.playAny({ "mini_slam" }, pinAt.Position, 1) then
					api.Sfx.play("gavel_strike", pinAt.Position, 1)
					api.Sfx.play("lasso_slam", pinAt.Position, 0.55)
				end
				ring(pinAt)
				if me:GetAttribute("MiniGameId") == model:GetAttribute("Id") then api.shake(0.035, 0.35) end
			end
			shown = dir * 88 / L.swing
			vel = 0
		else
			slamFrom = nil
			slammed = false
			-- a stiff spring toward the server's meter, plus the straining tremble while a bout is on
			local w0 = 13
			local a = w0 * w0 * (bal - shown) - 2 * w0 * vel
			vel += a * dt
			shown += vel * dt
			ang = shown * L.swing
			if st == "bout" then ang += math.noise(os.clock() * 7, model:GetAttribute("Id") and 3 or 1) * 2.2 end
		end
		local th = math.rad(ang)
		local p = L.pivot + Vector3.new(-math.sin(th) * L.reach, math.cos(th) * L.reach, 0)
		clasp.Position = p
		hA.Position = p + Vector3.new(0, 0, 0.09)
		hB.Position = p - Vector3.new(0, 0, 0.09)
	end
end

-- ------------------------------------------------------------------ your screen
local S: { [string]: any } = {}

local function myBal(): number
	local b = (S.model:GetAttribute("Bal") or 0) :: number
	return if S.side == "A" then b else -b
end

local function setPanel(api: any)
	local T = api.T
	local st = S.model:GetAttribute("State")
	local o = if S.side == "A" then "B" else "A"
	local oppName = S.model:GetAttribute(o .. "Name")
	local oppIsBot = (S.model:GetAttribute(o .. "Id") or 0) == -1
	S.oppL.Text = if oppName then string.upper(oppName :: string) else ""
	local panel = S.panel
	for _, c in panel:GetChildren() do if c:IsA("GuiButton") then c.Visible = false end end
	local first: GuiObject? = nil
	if st == "open" and not oppName then
		S.status.Text = "WAITING FOR A CHALLENGER"
		S.sub.Text = "OR PLAY A BOT"
		for _, b in S.botB do b.Visible = true end
		first = S.botB[2]
	elseif st == "done" then
		local won = S.model:GetAttribute("Winner") == S.side
		S.status.Text = if won then "YOU WIN" else "YOU LOSE"
		S.status.TextColor3 = if won then T.ACCENT else T.TEXT
		local mine = S.model:GetAttribute("Again" .. S.side)
		local theirs = S.model:GetAttribute("Again" .. o)
		S.sub.Text = if mine and not theirs then "WAITING FOR " .. (if oppName then string.upper(oppName :: string) else "THEM")
			elseif theirs and not oppIsBot then "THEY WANT A REMATCH" else ""
		S.againB.Visible = not mine
		first = S.againB
	else
		S.sub.Text = ""
	end
	api.nav(first ~= nil and api.padOn(), first)
end

local function flash(api: any, res: string)
	local T = api.T
	local col = if res == "perfect" then T.TEXT elseif res == "hit" then T.ACCENT else T.DANGER
	S.flashF.BackgroundColor3 = col
	S.flashF.BackgroundTransparency = 0.35
	T.tween(S.flashF, 0.3, { BackgroundTransparency = 1 })
	S.resL.Text = string.upper(res)
	S.resL.TextColor3 = col
	S.resL.TextTransparency = 0
	T.tween(S.resL, 0.6, { TextTransparency = 1 }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
	api.Sfx.play(if res == "miss" then "empty" elseif res == "perfect" then "parry_perfect" else "tink", nil, 0.45)
	if res ~= "miss" then api.shake(0.006, 0.12) end
end

local function press(api: any)
	local chk = S.chk
	if not chk or S.pressed[chk.id] or S.model:GetAttribute("State") ~= "bout" then return end
	local t = now()
	if t < chk.t0 then return end
	S.pressed[chk.id] = true
	local pos = MG.needle(chk, t)
	api.send({ op = "hit", id = chk.id, pos = pos })
	local d = math.abs(pos - chk.c)
	local res = if d <= chk.w * MG.ARM.PERFECT_K then "perfect" elseif d <= chk.w then "hit" else "miss"
	S.guess[chk.id] = res
	flash(api, res)
	S.needleHold = { pos = pos, t = os.clock() }
end

function M.open(api: any, model: Model, side: string)
	local T = api.T
	S = { api = api, model = model, side = side, chk = nil, pressed = {}, guess = {}, conns = {}, botB = {} }
	local root = api.root
	-- the meter
	local meter = T.plate(root, "Meter", UDim2.new(0.5, 0, 0, 18), UDim2.fromOffset(520, 58))
	meter.AnchorPoint = Vector2.new(0.5, 0)
	local you = T.text(meter, "You", "YOU", 13, T.ACCENT, T.FONT_TITLE)
	you.Position = UDim2.fromOffset(16, 6); you.Size = UDim2.new(0.5, -16, 0, 18)
	S.oppL = T.text(meter, "Opp", "", 13, T.SOFT, T.FONT_TITLE, Enum.TextXAlignment.Right)
	S.oppL.Position = UDim2.new(0.5, 0, 0, 6); S.oppL.Size = UDim2.new(0.5, -16, 0, 18)
	local track = T.new("Frame", { Name = "Track", BackgroundColor3 = T.TRACK, BorderSizePixel = 0, Position = UDim2.fromOffset(16, 32), Size = UDim2.new(1, -32, 0, 10) }, meter)
	T.corner(track, 5)
	local mid = T.new("Frame", { Name = "Mid", BackgroundColor3 = T.MUTED, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.new(0, 2, 1, 6) }, track)
	S.fill = T.new("Frame", { Name = "Fill", BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Position = UDim2.fromScale(0.5, 0), Size = UDim2.fromScale(0, 1) }, track)
	T.corner(S.fill, 5)
	S.knob = T.new("Frame", { Name = "Knob", BackgroundColor3 = T.TEXT, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(16, 16), ZIndex = 3 }, track)
	T.corner(S.knob, 8)
	mid.ZIndex = 2
	-- the status in the middle
	S.status = T.text(root, "Status", "", 34, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Center, true)
	S.status.AnchorPoint = Vector2.new(0.5, 0.5); S.status.Position = UDim2.fromScale(0.5, 0.36); S.status.Size = UDim2.fromOffset(600, 44)
	S.sub = T.text(root, "Sub", "", 15, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Center, true)
	S.sub.AnchorPoint = Vector2.new(0.5, 0); S.sub.Position = UDim2.new(0.5, 0, 0.36, 28); S.sub.Size = UDim2.fromOffset(600, 20)
	-- the buttons under it
	S.panel = T.new("Frame", { Name = "Panel", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0.36, 60), Size = UDim2.fromOffset(420, 44) }, root)
	for i, lv in MG.LEVELS do
		local b = api.button(S.panel, "Bot_" .. lv, MG.LEVEL_NAME[lv], UDim2.fromOffset((i - 1) * 142, 0), UDim2.fromOffset(132, 40), i == 2)
		b.Activated:Connect(function() api.send({ op = "bot", level = lv }) end)
		S.botB[i] = b
	end
	S.againB = api.button(S.panel, "Again", "AGAIN", UDim2.fromOffset(144, 0), UDim2.fromOffset(132, 40), true)
	S.againB.Activated:Connect(function() api.send({ op = "again" }) end)
	-- the check
	local chkP = T.plate(root, "Check", UDim2.new(0.5, 0, 1, -118), UDim2.fromOffset(560, 84))
	chkP.AnchorPoint = Vector2.new(0.5, 0)
	S.chkP = chkP
	local bar = T.new("Frame", { Name = "Bar", BackgroundColor3 = T.TRACK, BorderSizePixel = 0, Position = UDim2.fromOffset(20, 18), Size = UDim2.new(1, -40, 0, 26), ClipsDescendants = true }, chkP)
	T.corner(bar, 6)
	S.bar = bar
	S.zone = T.new("Frame", { Name = "Zone", BackgroundColor3 = T.ACCENT, BackgroundTransparency = 0.15, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0), Size = UDim2.fromScale(0.2, 1) }, bar)
	S.core = T.new("Frame", { Name = "Core", BackgroundColor3 = T.TEXT, BackgroundTransparency = 0.35, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromScale(0.5, 0), Size = UDim2.fromScale(MG.ARM.PERFECT_K, 1) }, S.zone)
	S.needle = T.new("Frame", { Name = "Needle", BackgroundColor3 = T.TEXT, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0, 0.5), Size = UDim2.new(0, 4, 1, 8), ZIndex = 3 }, bar)
	S.flashF = T.new("Frame", { Name = "Flash", BackgroundColor3 = T.TEXT, BackgroundTransparency = 1, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 4 }, bar)
	S.resL = T.text(chkP, "Result", "", 13, T.TEXT, T.FONT_TITLE, Enum.TextXAlignment.Center)
	S.resL.Position = UDim2.fromOffset(0, -1); S.resL.Size = UDim2.new(1, 0, 0, 18)
	local hint = T.text(chkP, "Hint", "", 13, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center)
	hint.Position = UDim2.new(0, 0, 1, -32); hint.Size = UDim2.new(1, 0, 0, 22)
	S.hint = hint
	-- (on a phone the whole lower half is the button)
	local tap = T.new("TextButton", { Name = "Tap", BackgroundTransparency = 1, Text = "", AutoButtonColor = false, Position = UDim2.fromScale(0, 0.5), Size = UDim2.fromScale(1, 0.5), Selectable = false, Visible = api.isTouch() }, root)
	tap.MouseButton1Down:Connect(function() press(api) end)
	S.tap = tap
	local function refresh() setPanel(api) end
	for _, a in { "State", "Winner", "AName", "BName", "AgainA", "AgainB" } do
		table.insert(S.conns, model:GetAttributeChangedSignal(a):Connect(refresh))
	end
	table.insert(S.conns, model:GetAttributeChangedSignal("State"):Connect(function()
		local st = model:GetAttribute("State")
		if st == "count" then api.Sfx.play("round_start", nil, 0.5)
		elseif st ~= "bout" then S.chk = nil end
	end))
	refresh()
	-- the camera: behind your left shoulder, on the clasp
	local mirror = if side == "A" then 1 else -1
	local c = L.cam
	api.camera = function(): CFrame?
		local r = model:FindFirstChild("Root") :: BasePart?
		if not r then return nil end
		local eye = r.CFrame * Vector3.new(c.side * mirror, L.top + c.up, (L.seat[side].Z) + c.back * mirror - 2.3 * mirror)
		local at = r.CFrame * (L.pivot + Vector3.new(0, L.reach * 0.75, 0))
		return CFrame.lookAt(eye, at)
	end
	-- what the camera must see: the clasped hands, both pin pads, the table's middle
	api.viewPoints = function(): { Vector3 }
		local r = model:FindFirstChild("Root") :: BasePart?
		local cl = r and r:FindFirstChild("Clasp") :: Attachment?
		if not r or not cl then return {} end
		return { cl.WorldPosition, r.CFrame * (L.pin.A + Vector3.new(0, 0.2, 0)), r.CFrame * (L.pin.B + Vector3.new(0, 0.2, 0)), r.CFrame * Vector3.new(0, L.top + 0.2, 0) }
	end
	api.fov = 62
	S.step = game:GetService("RunService").RenderStepped:Connect(function(dt: number)
		local st = model:GetAttribute("State")
		-- the meter: your share, eased
		local b = myBal()
		S.shownB = (S.shownB or 0) + (b - (S.shownB or 0)) * math.min(1, dt * 12)
		local x = 0.5 - S.shownB * 0.5
		S.knob.Position = UDim2.fromScale(x, 0.5)
		if x < 0.5 then S.fill.Position = UDim2.fromScale(x, 0); S.fill.Size = UDim2.fromScale(0.5 - x, 1); S.fill.BackgroundColor3 = T.ACCENT
		else S.fill.Position = UDim2.fromScale(0.5, 0); S.fill.Size = UDim2.fromScale(x - 0.5, 1); S.fill.BackgroundColor3 = T.DANGER end
		-- the middle
		if st == "count" then
			local left = MG.ARM.COUNT - (now() - ((model:GetAttribute("At") or now()) :: number))
			S.status.Text = if left > 0 then tostring(math.ceil(left)) else "GO"
			S.status.TextColor3 = T.TEXT
			S.sub.Text = ""
		elseif st == "bout" then
			local left = now() - ((model:GetAttribute("At") or now()) :: number)
			S.status.Text = if left < 0.6 then "GO" else ""
		elseif st == "slam" then
			local won = model:GetAttribute("Winner") == side
			S.status.Text = if won then "YOU WIN" else "YOU LOSE"
			S.status.TextColor3 = if won then T.ACCENT else T.TEXT
		end
		-- the check
		local chk = S.chk
		S.chkP.Visible = st == "bout" or st == "count"
		S.tap.Visible = api.isTouch() and st == "bout"
		S.hint.Text = if api.isTouch() then "TAP" elseif api.padOn() then "PRESS " .. api.Pad.short("ButtonA") else "PRESS SPACE"
		if chk and st == "bout" and S.auto and not S.pressed[chk.id] and now() >= chk.t0 and math.abs(MG.needle(chk, now()) - chk.c) < chk.w * 0.3 then
			press(api) -- (a Studio test's autopilot: MiniTest "arm:auto")
		end
		if chk and st == "bout" then
			S.zone.Visible = true
			S.zone.Position = UDim2.fromScale(chk.c, 0)
			S.zone.Size = UDim2.fromScale(chk.w * 2, 1)
			local hold = S.needleHold
			local pos = if hold and os.clock() - hold.t < 0.18 then hold.pos else MG.needle(chk, now())
			S.needle.Position = UDim2.fromScale(pos, 0.5)
			S.needle.BackgroundTransparency = if now() < chk.t0 then 0.6 else 0
		else
			S.zone.Visible = false
			S.needle.Position = UDim2.fromScale(0, 0.5)
		end
	end)
end

function M.close()
	if S.step then S.step:Disconnect() end
	for _, c in S.conns or {} do c:Disconnect() end
	if S.api then S.api.camera = nil; S.api.fov = nil; S.api.nav(false) end
	S = {}
end

function M.remote(d: any)
	if d.op == "check" then
		S.chk = d.chk
	elseif d.op == "result" then
		if S.guess and S.guess[d.id] and S.guess[d.id] ~= d.res and S.api then flash(S.api, d.res) end
	end
end

function M.space(down: boolean, _io: any): boolean
	if not S.model then return false end
	local st = S.model:GetAttribute("State")
	if st == "bout" then
		if down then press(S.api) end
		return true
	end
	return st == "count" or st == "slam"
end

function M.back(): boolean return false end

function M.confirmLeave(): string?
	if not S.model then return nil end
	local st = S.model:GetAttribute("State")
	if st == "bout" or st == "count" then return "PRESS AGAIN TO LEAVE: YOU FORFEIT" end
	return nil
end

function M.test(v: string): string
	if v == "arm:press" then press(S.api); return "pressed" end
	if v == "arm:auto" then S.auto = not S.auto; return "auto " .. tostring(S.auto) end
	if v == "arm:perfect" then
		-- (a test's press right on the zone: wait for the needle to reach it)
		local chk = S.chk
		if not chk then return "no check" end
		task.spawn(function()
			for _ = 1, 400 do
				local p = MG.needle(chk, now())
				if now() >= chk.t0 and math.abs(p - chk.c) < chk.w * 0.25 then press(S.api); return end
				task.wait()
			end
		end)
		return "aiming"
	end
	return game:GetService("HttpService"):JSONEncode({ chk = S.chk, bal = S.model and S.model:GetAttribute("Bal"), state = S.model and S.model:GetAttribute("State") })
end

return M
